"""
Streamlit chat UI fronting Demos 1, 2, and 3.

Tabs:
  - Literature Triage (Demo 1): function-tool agent with pubmed_search + gene_lookup
  - Protocol Q&A (Demo 2): Foundry-hosted file-search over an uploaded protocol
  - Research MCP Tools (Demo 3): MCP stdio server with clinical_trials_search + variant_annotation

For each turn we display:
  - The user's message
  - The agent's final answer
  - Any tool calls made (function name, args, return value) in a collapsible panel

Run locally:
    streamlit run app.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Annotated

import streamlit as st
from agent_framework import AgentSession, MCPStdioTool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from pydantic import Field

# --------------------------------------------------------------------------- #
# Config + page setup
# --------------------------------------------------------------------------- #

load_dotenv()
PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
PRESEEDED_VS_ID = os.environ.get("AZURE_AI_VECTOR_STORE_ID", "").strip() or None

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DOC = REPO_ROOT / "02-agent-knowledge" / "data" / "ped-all-2025-01-protocol.md"
MCP_SERVER = REPO_ROOT / "03-mcp-tool-server" / "mcp_server.py"

st.set_page_config(
    page_title="St. Jude AI Agents — Live Demo",
    page_icon="🧬",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# Tools for Demo 1 (literature triage)
# --------------------------------------------------------------------------- #


def pubmed_search(
    query: Annotated[str, Field(description="Free-text PubMed query, e.g. 'TP53 pediatric ALL relapse'.")],
    max_results: Annotated[int, Field(description="Max number of results to return.")] = 3,
) -> list[dict]:
    """Return recent (mocked) PubMed hits for the given query."""
    mocked = [
        {"pmid": "39812345", "year": 2025, "title": f"Single-cell atlas of {query} in pediatric cohorts"},
        {"pmid": "39798765", "year": 2024, "title": f"Functional CRISPR screen reveals dependencies in {query}"},
        {"pmid": "39654321", "year": 2024, "title": f"Long-term outcomes after targeted therapy in {query}"},
        {"pmid": "39512345", "year": 2023, "title": f"Genomic landscape of {query}: a multi-institutional study"},
    ]
    return mocked[:max_results]


def gene_lookup(
    symbol: Annotated[str, Field(description="HGNC gene symbol, e.g. 'TP53', 'IKZF1'.")],
) -> dict:
    """Return basic info (mocked) about a human gene by HGNC symbol."""
    catalog = {
        "TP53": {
            "chromosome": "17p13.1",
            "function": "Tumor suppressor; regulates cell-cycle arrest, apoptosis, DNA repair.",
            "disease_associations": ["Li-Fraumeni syndrome", "many cancers incl. pediatric ALL relapse"],
        },
        "IKZF1": {
            "chromosome": "7p12.2",
            "function": "Zinc-finger transcription factor; regulates lymphocyte differentiation.",
            "disease_associations": ["B-cell ALL (poor prognosis when deleted)"],
        },
        "MYCN": {
            "chromosome": "2p24.3",
            "function": "Proto-oncogene transcription factor.",
            "disease_associations": ["High-risk neuroblastoma (amplification)"],
        },
    }
    return catalog.get(symbol.upper(), {"error": f"No record for {symbol} in demo catalog."})


def _wrap_for_trace(fn, sink: list):
    """Wrap a Python tool so its invocations are recorded for the UI trace panel."""

    def wrapped(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except Exception as ex:
            sink.append({"tool": fn.__name__, "args": kwargs or args, "result": f"ERROR: {ex}"})
            raise
        sink.append({"tool": fn.__name__, "args": kwargs or args, "result": result})
        return result

    wrapped.__name__ = fn.__name__
    wrapped.__doc__ = fn.__doc__
    wrapped.__annotations__ = fn.__annotations__
    return wrapped


# --------------------------------------------------------------------------- #
# Async helpers
# --------------------------------------------------------------------------- #


def run_async(coro):
    """Run an async coroutine from Streamlit's sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError("nested loop")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.markdown("### Deployment")
    st.code(PROJECT_ENDPOINT, language="text")
    st.markdown(f"**Model:** `{MODEL_DEPLOYMENT}`")
    st.markdown("---")
    if st.button("🔄 Reset all chats", use_container_width=True):
        for key in [k for k in st.session_state.keys() if k.startswith("messages_") or k.startswith("session_")]:
            del st.session_state[key]
        st.rerun()
    st.markdown("---")
    st.caption(
        "Each tab is a separate Foundry agent. Tool calls are shown inline so the "
        "audience can see exactly which function the model decided to invoke."
    )

st.title("🧬 St. Jude AI Agents — Live Demo")
st.caption("Microsoft Agent Framework + Microsoft Foundry, running against your project.")

tab1, tab2, tab3 = st.tabs(
    [
        "1️⃣ Literature Triage (function tools)",
        "2️⃣ Protocol Q&A (RAG / file search)",
        "3️⃣ Research MCP Tools",
    ]
)


# --------------------------------------------------------------------------- #
# Generic chat renderer
# --------------------------------------------------------------------------- #


def render_chat(tab_key: str):
    """Render the message history for a given tab."""
    for msg in st.session_state.get(f"messages_{tab_key}", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tool_calls"):
                with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s)"):
                    for call in msg["tool_calls"]:
                        st.markdown(f"**`{call['tool']}`**")
                        st.code(json.dumps(call.get("args", {}), indent=2, default=str), language="json")
                        st.markdown("→")
                        st.code(json.dumps(call["result"], indent=2, default=str), language="json")


# --------------------------------------------------------------------------- #
# Tab 1: Literature Triage
# --------------------------------------------------------------------------- #

with tab1:
    st.markdown(
        "**Use case:** A researcher kicking off work on a gene of interest. "
        "The agent fetches recent PubMed hits and gene-level annotations via "
        "Python function tools."
    )
    st.markdown(
        "**Try:** _Give me a brief on TP53 and pull two recent papers on TP53 in pediatric ALL relapse._"
    )

    if "messages_lit" not in st.session_state:
        st.session_state["messages_lit"] = []
        st.session_state["session_lit"] = AgentSession()

    render_chat("lit")

    if prompt := st.chat_input("Ask the literature-triage agent...", key="input_lit"):
        st.session_state["messages_lit"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking + calling tools..."):
                tool_calls: list = []
                credential = AzureCliCredential()
                client = FoundryChatClient(
                    project_endpoint=PROJECT_ENDPOINT,
                    model=MODEL_DEPLOYMENT,
                    credential=credential,
                )
                agent = client.as_agent(
                    name="LiteratureTriageAgentUI",
                    instructions=(
                        "You are a research assistant helping pediatric oncology investigators "
                        "triage literature and gene-level evidence. Use the available tools to "
                        "fetch facts. Cite PMIDs when you reference papers."
                    ),
                    tools=[
                        _wrap_for_trace(pubmed_search, tool_calls),
                        _wrap_for_trace(gene_lookup, tool_calls),
                    ],
                )
                try:
                    reply = run_async(agent.run(prompt, session=st.session_state["session_lit"]))
                    reply_text = str(reply)
                except Exception as ex:
                    reply_text = f"⚠️ {type(ex).__name__}: {ex}"
                finally:
                    run_async(credential.close())

            st.markdown(reply_text)
            if tool_calls:
                with st.expander(f"🔧 {len(tool_calls)} tool call(s)"):
                    for call in tool_calls:
                        st.markdown(f"**`{call['tool']}`**")
                        st.code(json.dumps(call.get("args", {}), indent=2, default=str), language="json")
                        st.markdown("→")
                        st.code(json.dumps(call["result"], indent=2, default=str), language="json")

        st.session_state["messages_lit"].append(
            {"role": "assistant", "content": reply_text, "tool_calls": tool_calls}
        )


# --------------------------------------------------------------------------- #
# Tab 2: Protocol Q&A (RAG / file search)
# --------------------------------------------------------------------------- #

with tab2:
    st.markdown(
        "**Use case:** A research coordinator asking questions about a long, dense protocol. "
        "The agent answers only from the indexed protocol; out-of-scope questions get refused."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("##### Grounding source")
        if PROTOCOL_DOC.exists():
            st.markdown(f"`{PROTOCOL_DOC.relative_to(REPO_ROOT)}`")
            with st.expander("Preview the protocol"):
                st.code(PROTOCOL_DOC.read_text(encoding="utf-8"), language="markdown")
        else:
            st.error(f"Protocol document missing: {PROTOCOL_DOC}")

    with col2:
        st.markdown("##### Vector store")
        current_vs = st.session_state.get("vector_store_id") or PRESEEDED_VS_ID
        if current_vs:
            st.success(f"Using vector store **{current_vs}**")
            if st.button("🗑️ Tear down vector store", key="vs_teardown"):
                _vsid = st.session_state.pop("vector_store_id", None)
                _fids = st.session_state.pop("vector_store_file_ids", [])
                try:
                    from azure.ai.agents.aio import AgentsClient

                    async def _teardown():
                        cred = AzureCliCredential()
                        agents = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=cred)
                        if _vsid:
                            await agents.vector_stores.delete(_vsid)
                        for fid in _fids:
                            await agents.files.delete(fid)
                        await agents.close()
                        await cred.close()

                    run_async(_teardown())
                    st.success("Vector store and uploaded files removed.")
                except Exception as ex:
                    st.warning(f"Teardown encountered: {ex}")
                st.rerun()
        else:
            st.info("No vector store yet. Click below to upload the protocol and build one.")
            if st.button("⬆️ Upload + index the protocol", key="vs_build", type="primary"):
                from azure.ai.agents.aio import AgentsClient
                from azure.ai.agents.models import FilePurpose

                async def _build():
                    cred = AzureCliCredential()
                    agents = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=cred)
                    fid_list = []
                    f = await agents.files.upload_and_poll(
                        file_path=str(PROTOCOL_DOC), purpose=FilePurpose.AGENTS
                    )
                    fid_list.append(f.id)
                    vs = await agents.vector_stores.create_and_poll(
                        file_ids=fid_list, name="ped-all-protocol-ui-vs"
                    )
                    await agents.close()
                    await cred.close()
                    return vs.id, fid_list

                with st.spinner("Uploading + indexing..."):
                    try:
                        vsid, fids = run_async(_build())
                        st.session_state["vector_store_id"] = vsid
                        st.session_state["vector_store_file_ids"] = fids
                        st.success(f"Created vector store **{vsid}**")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Build failed: {ex}")

    st.markdown("---")
    st.markdown(
        "**Try:** _What's the primary endpoint window?_ · "
        "_When do we collect bone marrow vs cfDNA?_ · "
        "_What's the recommended dose of EX-1042 for adults with AML?_"
    )

    if "messages_rag" not in st.session_state:
        st.session_state["messages_rag"] = []
        st.session_state["session_rag"] = AgentSession()

    render_chat("rag")

    chat_disabled = not (st.session_state.get("vector_store_id") or PRESEEDED_VS_ID)
    if chat_disabled:
        st.info("Build the vector store above to enable the chat input.")
    if prompt := st.chat_input(
        "Ask about the protocol...", key="input_rag", disabled=chat_disabled
    ):
        st.session_state["messages_rag"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching the protocol..."):
                credential = AzureCliCredential()
                client = FoundryChatClient(
                    project_endpoint=PROJECT_ENDPOINT,
                    model=MODEL_DEPLOYMENT,
                    credential=credential,
                )
                vsid = st.session_state.get("vector_store_id") or PRESEEDED_VS_ID
                file_search_tool = client.get_file_search_tool(vector_store_ids=[vsid])
                agent = client.as_agent(
                    name="ProtocolQAAgentUI",
                    instructions=(
                        "You are a research-operations assistant. Answer questions about the "
                        "attached study protocol using ONLY the provided documents. Quote or "
                        "paraphrase the protocol text. If the answer is not in the documents, "
                        "say so explicitly and recommend the user consult the PI."
                    ),
                    tools=[file_search_tool],
                )
                try:
                    reply = run_async(agent.run(prompt, session=st.session_state["session_rag"]))
                    reply_text = str(reply)
                except Exception as ex:
                    reply_text = f"⚠️ {type(ex).__name__}: {ex}"
                finally:
                    run_async(credential.close())

            st.markdown(reply_text)

        st.session_state["messages_rag"].append({"role": "assistant", "content": reply_text})


# --------------------------------------------------------------------------- #
# Tab 3: MCP tools
# --------------------------------------------------------------------------- #

with tab3:
    st.markdown(
        "**Use case:** Different research teams expose shared tools via MCP so any "
        "agent — yours or someone else's — can call them. Here the agent talks to a "
        "stdio MCP server with `clinical_trials_search` and `variant_annotation`."
    )

    with st.expander("📄 Peek at `mcp_server.py`"):
        if MCP_SERVER.exists():
            st.code(MCP_SERVER.read_text(encoding="utf-8"), language="python")
        else:
            st.error(f"MCP server file missing: {MCP_SERVER}")

    st.markdown(
        "**Try:** _Open phase II trials for relapsed B-ALL?_ · "
        "_Classify TP53 p.R175H._ · "
        "_Relapsed B-ALL with IKZF1 p.N159S — annotate and find matching trials._"
    )

    if "messages_mcp" not in st.session_state:
        st.session_state["messages_mcp"] = []
        st.session_state["session_mcp"] = AgentSession()

    render_chat("mcp")

    if prompt := st.chat_input("Ask the MCP-backed agent...", key="input_mcp"):
        st.session_state["messages_mcp"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Spawning MCP server + thinking..."):
                credential = AzureCliCredential()
                client = FoundryChatClient(
                    project_endpoint=PROJECT_ENDPOINT,
                    model=MODEL_DEPLOYMENT,
                    credential=credential,
                )
                mcp_tools = MCPStdioTool(
                    name="pediatric-onc-research-tools",
                    command=sys.executable,
                    args=[str(MCP_SERVER)],
                )
                agent = client.as_agent(
                    name="OncoResearchMCPAgentUI",
                    instructions=(
                        "You are a pediatric oncology research assistant. Use the available MCP "
                        "tools to look up open clinical trials and annotate gene variants. Prefer "
                        "tool calls over your own recollection. Cite NCT IDs and variant "
                        "pathogenicity verbatim."
                    ),
                    tools=[mcp_tools],
                )
                try:
                    reply = run_async(agent.run(prompt, session=st.session_state["session_mcp"]))
                    reply_text = str(reply)
                except Exception as ex:
                    reply_text = f"⚠️ {type(ex).__name__}: {ex}"
                finally:
                    run_async(credential.close())

            st.markdown(reply_text)

        st.session_state["messages_mcp"].append({"role": "assistant", "content": reply_text})
