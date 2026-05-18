# Demo UI — Streamlit chat front-end

A single browser tab that wraps **Demos 1, 2, and 3** with a polished chat
interface, designed for live presentations over Teams / Zoom. Each demo is a
tab:

1. **Literature Triage** — function-tool agent (PubMed + gene lookup).
   Tool calls are rendered inline in a collapsible panel so the audience can
   see exactly which function the model invoked and what came back.
2. **Protocol Q&A** — RAG over the synthetic PED-ALL-2025-01 protocol via a
   Foundry-hosted vector store. One-click "build vector store" button so you
   don't have to scaffold anything ahead of time.
3. **Research MCP Tools** — the same MCP stdio server from `03-mcp-tool-server/`
   wired in via `MCPStdioTool`.

## Setup

```powershell
cd demo-ui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # the defaults already point at the deployed Foundry project
az login
```

## Run

```powershell
streamlit run app.py
```

Streamlit opens in your browser on `http://localhost:8501`. **For the live
demo, share the browser window (not the whole desktop) in Teams** so the
audience just sees the chat UI.

## Tips for presenting

- **Reset all chats** button in the sidebar wipes session state between
  takes so you can rehearse the same opener cleanly.
- The **tool-call expander** ("🔧 N tool call(s)") under each agent reply is
  your "look behind the curtain" moment — pop it open after the first
  response in each tab.
- For Tab 2, click **"Upload + index the protocol"** at the top *before*
  starting the demo, so the audience doesn't watch you wait for the vector
  store build (~20–30s).
- To pre-bake the vector store across sessions, run
  `02-agent-knowledge/agent_knowledge.ipynb` once, copy the printed vector
  store ID, and paste it into `.env` as `AZURE_AI_VECTOR_STORE_ID=vs_...`.

## Talk-track integration

Each tab maps 1:1 to the Use case + Talk track sections in
`../0{1,2,3}-*/README.md`. Run those READMEs as your speaker notes and
drive the live UI alongside.
