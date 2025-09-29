learning-coach-agent

Multi-Agent Learning Coach built with Google ADK and MCP.

Abilities
- Web UI (ADK) at http://127.0.0.1:8000
- Root agent orchestrates and hands off to sub-agents
- SummarizerAgent outputs structured JSON summaries
- Tools currently wired
  - PDF Reader MCP: read text, search content, and get metadata from PDFs
  - Google Search (fallback): fetch web snippets if conversion fails or no content is provided

JSON output schema
{
  "summary": "2–5 sentences",
  "key_topics": ["3–5 keywords"],
  "note": "optional; e.g., Content truncated"
}

Flow
1) User asks for a summary (raw text or a PDF)
2) Root agent transfers to SummarizerAgent
3) SummarizerAgent
   - list_tools → choose an MCP tool
   - Use PDF Reader MCP to read/search PDF and produce text
   - Summarize into the JSON schema
4) If tools provide no content → call Google Search and summarize snippets

Requirements
- Python 3.12 (tested) and Node.js 18+
- A Google AI API key in .env: GOOGLE_API_KEY=...

Windows event-loop note
- ADK launches MCP tools via subprocess. On Windows, ensure the selector loop is used before `adk` starts.
  Options:
  - Set env var in the shell before launching: `set PYTHONASYNCIO_DEFAULT_EVENT_LOOP_POLICY=asyncio.WindowsSelectorEventLoopPolicy`
  - Or, if you use a venv, add a `sitecustomize.py` that sets `WindowsSelectorEventLoopPolicy`.

Local quick start (no Docker)
1) Create and activate a venv, install deps
   cd "E:\Github\Learning Coach Agent"
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r learning-coach-agent\requirements.txt

2) Configure .env (current setup)
   GOOGLE_API_KEY=your_key_here
   GEMINI_MODEL=gemini-2.0-flash
   # PDF Reader MCP
   PDF_READER_PATH=E:\Github\mcp_pdf_reader\index.js
   PDF_SHARE_DIR=E:\Github\Learning Coach Agent\pdf_files

3) Run the PDF Reader MCP
   node E:\Github\mcp_pdf_reader\index.js

4) Start the web UI
   cd "E:\Github\Learning Coach Agent"
   adk web --log_level debug --no-reload

Open http://127.0.0.1:8000 and pick learning-coach-agent.

Docker (optional)
- Build and run the app container
  docker compose build
  docker compose up -d learning-coach

Configuration (.env)
- GOOGLE_API_KEY        – Google AI API key
- GEMINI_MODEL          – Model name (default: gemini-2.0-flash)
- ROOT_AGENT_MODEL      – Override the root model (optional)
- PDF_READER_PATH       – Path to the PDF Reader MCP Node script
- PDF_SHARE_DIR         – Host directory exposed to the PDF MCP server

Troubleshooting
- 400 INVALID_ARGUMENT (mimeType not supported)
  Gemini does not accept DOCX blobs. Use the PDF Reader MCP on PDFs or feed plain text.

- Windows NotImplementedError from asyncio.subprocess
  Ensure the selector loop policy is active (see Windows note above) before launching `adk`.

Repo layout (simplified)
- agent.py                – Root agent wiring
- subagents/
  - summarizer/agent.py   – SummarizerAgent definition
  - summarizer/tools.py   – Tool wiring (Search + PDF MCP)
- Dockerfile, docker-compose*.yml – Optional containerization
- markdown_files/         – Output artifacts

