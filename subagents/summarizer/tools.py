import os
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
MARKDOWNIFY_PATH = os.getenv("MARKDOWNIFY_PATH") or os.path.join(
    os.path.dirname(__file__),
    "../../markdownify/markdownify-mcp/dist/index.js"
)


#----------------------------Search Tool--------------------------------

# First, define a dedicated search agent
SearchAgent = Agent(
    name="SearchAgent",
    model=GEMINI_MODEL,
    description="Finds and retrieves relevant, up-to-date information from the web when given a query.",
    instructions="""
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
    output_schema={
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "snippet": {"type": "string"}
                },
                "required": ["title", "url"]
            }
        }
    },
    "required": ["results"]
},
    output_key=["results"]
)

SearchTool = AgentTool(agent=SearchAgent)


#----------------------------Markdownify Tool--------------------------------


# 1. Define the Markdownify MCP connection
markdownify_connection = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="node",
        args=[MARKDOWNIFY_PATH],
        env={
            "MD_SHARE_DIR": os.getenv("MARKDOWNIFY_SHARE_DIR", "")
        }
    )
)

# 2. Wrap as a toolset 
MarkdownifyToolset = MCPToolset(
    connection_params=markdownify_connection,
    # tool_filter=None,
)

# 3. Define the agent that uses the toolset
MarkdownifyAgent = Agent(
    name="MarkdownifyAgent",
    model=GEMINI_MODEL,
    description=(
        "Converts files (PDF, DOCX, PPTX, XLSX, images, audio) and web content into Markdown."
    ),
    instructions="""
You are the Markdownify Agent. You connect to an MCP server that provides many tools
for converting external content into Markdown.

You should:
1. First call `list_tools` to see what tools are available in the current session.
2. Based on the learner input:
   - Use `webpage-to-markdown` for URLs.
   - Use `pdf-to-markdown`, `docx-to-markdown`, `pptx-to-markdown`, or `xlsx-to-markdown` for documents.
   - Use `image-to-markdown` for images.
   - Use `audio-to-markdown` for audio recordings.
3. Return clean, concise Markdown text for downstream summarization.

Never return raw binary data. Always convert it to Markdown before passing it along.
""",
    tools=[MarkdownifyToolset],
    output_schema={
    "type": "object",
    "properties": {
        "source": {"type": "string"},
        "content_markdown": {"type": "string"},
        "metadata": {"type": "object"}
    },
    "required": ["content_markdown"]
},
    output_key=["content_markdown", "metadata"]    
)
# 4. Expose as an AgentTool so other agents can call it
MarkdownifyTool = AgentTool(agent=MarkdownifyAgent)