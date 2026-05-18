# ai-agents-st-jude-lunch

A live-demo walkthrough of agentic development at St. Jude using the
**Microsoft Agent Framework** and **Microsoft Foundry**, from a freshly
provisioned Foundry project all the way to a containerized agent fronted
by an APIM-based AI Gateway.

## Lifecycle

```
[ Cloud infra team ]    [ You — researcher ]    [ You — researcher ]    [ Platform team ]
  Foundry project   ->    Build the agent    ->   Evaluations + Sec  ->  Containerize + APIM
  + model endpoints       Demos 1–3              Demo 4                 Demo 5
```

## Contents

| Folder                       | What it is                                                       |
| ---------------------------- | ---------------------------------------------------------------- |
| `infra/`                     | Bicep for the Foundry "standard agent setup" (RG, project, deps) |
| `01-basic-agent-tools/`      | Demo 1 — Basic agent + Python function tools                     |
| `02-agent-knowledge/`        | Demo 2 — Agent grounded in a study protocol (RAG)                |
| `03-mcp-tool-server/`        | Demo 3 — Shared bioinformatics tools via an MCP server           |
| `04-evaluations-security/`   | Demo 4 — Quality + safety evaluation as a release gate           |
| `05-production-readiness/`   | Demo 5 — FastAPI + Container Apps + APIM AI Gateway handoff      |

Each demo folder has its own `README.md` with a **Use case** and a per-cell
**Talk track** for the live presentation.

## Audience

Technical researchers exploring AI as part of their work. Examples and
tools throughout are pediatric-oncology-flavored (TP53, IKZF1, B-ALL,
clinical trials, variant annotation) so they land with the room.

> Note: sample protocols and tool outputs in this repo are **synthetic** —
> do not use any details for clinical or research decision-making.

## Getting started

1. Deploy the Foundry standard-agent setup from `infra/` (see `infra/README.md`).
2. Copy the project endpoint + model deployment name into each demo's `.env`.
3. Run demos 1–5 in order — they build on each other narratively.
