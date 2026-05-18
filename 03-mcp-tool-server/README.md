# Demo 3 — Building an MCP Tool Server

A self-contained MCP (Model Context Protocol) server exposing a couple of
tools, plus a notebook that connects a Microsoft Agent Framework agent to it.

## What this shows
- How to author a tiny MCP server in Python (`mcp_server.py`) using the
  official `mcp` SDK with a stdio transport
- How to wire that server into a Foundry-backed agent using the framework's
  `MCPStdioTool` so the model can invoke MCP tools the same way it would
  invoke native function tools

## Use case

Different teams in a research org own different capabilities. The trials
office maintains the canonical list of open clinical studies. The
bioinformatics core maintains the variant-annotation pipeline. We don't
want every team that builds an agent to re-implement those — we want a
**shared, language-agnostic tool surface** that any agent (ours, a
collaborator's, Claude Desktop, an IDE extension, …) can plug into.

That's what MCP (Model Context Protocol) gives us. In this demo we ship a
tiny server (`mcp_server.py`) exposing two research-flavored tools:

- `clinical_trials_search(condition, phase=None)` — stand-in for a real
  ClinicalTrials.gov / institutional trial registry query.
- `variant_annotation(gene, variant)` — stand-in for a curated
  variant-pathogenicity lookup (think ClinVar / VICC / internal panel).

Then we connect a Foundry-backed Microsoft Agent Framework agent to it via
`MCPStdioTool`. The same unmodified server could be consumed by any other
MCP-aware client — that's the point.

## Talk track

Use this as a speaking outline while you run the cells live.

1. **Frame the problem (45 sec).**
   *"In Demo 1 we passed Python functions straight to the agent. That works
   when one team owns everything. But in a research org, the trials office
   owns the trial registry, the bioinformatics core owns the variant
   annotation pipeline, and you don't want every project copy-pasting that
   logic. MCP — Model Context Protocol — solves that. Define a tool once,
   in any language, and any MCP-aware client can call it."*

2. **Show the server (Cell 1).**
   *"Here's the entire server: `FastMCP`, two `@mcp.tool()` decorators,
   `mcp.run(transport='stdio')`. That's it. Today it's a subprocess; the
   exact same code can run over HTTP and be shared across the institution."*

3. **Connect it to the agent (Cell 3).**
   *"`MCPStdioTool` launches the server as a subprocess. To the agent it
   looks like a regular tool — same calling convention, same schema
   inference, same Foundry-managed tool loop. Nothing about the agent code
   knows or cares that these are MCP tools."*

4. **Trials question (Cell 4).**
   *"'What open phase II trials for relapsed B-ALL do we have?' — model
   picks `clinical_trials_search`, calls it, returns NCT IDs and sites.
   I never told it which tool to use."*

5. **Variant question (Cell 5).**
   *"Different tool, same agent, no code change. TP53 p.R175H — pathogenic
   hotspot, Li-Fraumeni-associated. Verbatim from the annotation tool."*

6. **Composed question (Cell 6).**
   *"Now the punchline: I describe a relapsed B-ALL patient with an IKZF1
   variant and ask for variant annotation **and** eligible open trials. The
   agent chains both tools — annotation, then trial search filtered by
   condition — and produces a single coherent answer. That's where MCP
   really shines: you can grow your shared tool library independently of
   your agents."*

7. **Wrap (15 sec).**
   *"Picture this server living in a container, owned by the trials office,
   versioned independently. Our agent — and a hundred other agents across
   the institution — just point at its URL. One source of truth, many
   consumers. That's the power of an open tool protocol."*


## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # then fill in values
az login
```

## Run
1. Test the server stand-alone (optional):
   ```powershell
   python mcp_server.py
   ```
   It waits for an MCP client to connect over stdio. Use `Ctrl+C` to stop.

2. Open `mcp_agent_client.ipynb` and run cells top-to-bottom. The notebook
   spawns the server as a subprocess and lets the agent call its tools.
