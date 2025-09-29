import json
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

load_dotenv()

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
PDF_READER_PATH = os.getenv("PDF_READER_PATH", "")


#----------------------------Search Tool--------------------------------

# First, define a dedicated search agent
SearchAgent = Agent(
    name="SearchAgent",
    model=GEMINI_MODEL,
    description="Finds and retrieves relevant, up-to-date information from the web when given a query.",
    instruction="""
You are a powerful search assistant. Your job is to transform user queries into
effective Google searches and return the most useful, relevant, and reliable
information available on the web.

Your responsibilities include:
- Returning concise search results with titles, snippets, and URLs.
- Prioritizing authoritative and trustworthy sources over spammy or irrelevant ones.
- Handling both general knowledge queries (e.g., 'history of AI') and
  time-sensitive searches (e.g., 'latest AI news 2025').
- Supporting exploratory queries by providing multiple angles or perspectives.
- When the query is ambiguous, infer the intent and provide the most
  contextually relevant results.

Always provide:
- A clear, structured list of top results.
- Enough detail in snippets to help decide which links are worth deeper analysis.
- Diverse coverage (news, academic, technical, practical) when relevant.

Do not fabricate information. Only return what the Google Search tool provides.
If no good results are found, state that explicitly.
""",
    tools=[google_search],
)


class SearchAgentTool(AgentTool):
    async def run_async(self, *, args, tool_context):
        result = await super().run_async(args=args, tool_context=tool_context)
        parsed = None
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
            except json.JSONDecodeError:
                parsed = None
        elif isinstance(result, dict):
            parsed = result
        if isinstance(parsed, dict) and "results" in parsed:
            tool_context.state["results"] = parsed["results"]
        return result


SearchTool = SearchAgentTool(agent=SearchAgent)


#----------------------------Markdownify Tool--------------------------------


# --- PDF Reader MCP Tool ---
pdf_reader_connection = StdioServerParameters(
    command="node",
    args=[os.getenv("PDF_READER_PATH")],
    env={
        "PDF_SHARE_DIR": os.getenv("PDF_SHARE_DIR", "")
    }
)


PDFReaderToolset = MCPToolset(connection_params=pdf_reader_connection)

PDFReaderAgent = Agent(
    name="PDFReaderAgent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    description="Extracts text, searches content, or retrieves metadata from PDF files.",
    instruction="""
You are the PDF Reader Agent.

Available tools:
- `read-pdf` → Extract text (optionally with metadata or cleaning).
- `search-pdf` → Search inside a PDF (supports regex, case, whole word).
- `pdf-metadata` → Get metadata only.

Always:
1. Call `list_tools` to confirm what’s available.
2. Use the right tool depending on the user request.
3. Save extracted text into `content_markdown` in tool_context for summarization.
""",
    tools=[PDFReaderToolset],
)


class PDFReaderAgentTool(AgentTool):
    async def run_async(self, *, args, tool_context):
        result = await super().run_async(args=args, tool_context=tool_context)
        parsed = None
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
            except json.JSONDecodeError:
                parsed = None
        elif isinstance(result, dict):
            parsed = result

        content = None
        if isinstance(parsed, dict):
            # This MCP uses "content" for text and "metadata" separately
            content = parsed.get("content") or parsed.get("content_markdown")
            metadata = parsed.get("metadata")
            if content:
                tool_context.state["content_markdown"] = content
            if metadata:
                tool_context.state["metadata"] = metadata

        return result


PDFReaderTool = PDFReaderAgentTool(agent=PDFReaderAgent)
