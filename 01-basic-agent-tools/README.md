# Demo 1 — Basic Agent + Tools

A minimal Microsoft Agent Framework agent backed by Microsoft Foundry, equipped
with two simple Python function tools the model can invoke.

## What this shows
- Creating an `AzureAIAgentClient` against a Foundry project
- Passing plain Python functions as tools (the framework auto-generates schemas)
- Letting the model decide when to call tools and produce the final answer

## Use case

You're a pediatric oncology researcher kicking off a new project on a gene
of interest. You want a quick assistant that can pull *current* facts from
external sources rather than relying on what an LLM happens to remember —
recent PubMed hits, basic gene-level annotations, etc. — and weave them
into a useful brief. Instead of writing API glue around the LLM, you give
the agent a couple of Python functions and let the model decide *when* to
call them based on what you ask.

The two tools in this demo are deliberately tiny stand-ins:
- `pubmed_search(query, max_results)` — would call NCBI E-utilities /
  Entrez in production.
- `gene_lookup(symbol)` — would call MyGene.info or an internal curated
  gene KB in production.

Replace these with your real sources (an institutional variant DB, a
biospecimen inventory API, a CRISPR-screen lookup, etc.) and the pattern
is identical.

## Talk track

Use this as a speaking outline while you run the cells live.

1. **Frame the problem (30 sec).**
   *"LLMs are great at language, but they lag the literature by months and
   they don't know what's in our internal databases. To make an agent
   actually useful for research we have to give it tools. Watch how little
   code that takes with the Microsoft Agent Framework against Foundry."*

2. **Show the tools (Cell 2).**
   *"These are just plain Python functions — type hints, docstrings, that's
   it. The framework introspects them and generates the JSON schema the
   model sees. No decorators, no separate manifest. In production these
   would hit PubMed and a real gene KB; today they return mocked payloads
   so the demo is fully offline."*

3. **Create the agent (Cell 3).**
   *"One client pointed at our Foundry project, one `create_agent` call. I
   pass the deployment name of the model we just spun up via the Bicep,
   instructions tuned for a research assistant, and the list of tools.
   Auth is just `AzureCliCredential` — the same `az login` you already
   use."*

4. **First run (Cell 4).**
   *"I ask for a 3-sentence brief on TP53 — function, disease associations,
   recent papers in pediatric ALL relapse. Notice I never tell the model
   which tool to call. It calls `gene_lookup('TP53')`, then
   `pubmed_search(...)`, and stitches a brief with PMIDs."*

5. **Multi-turn (Cell 5).**
   *"Threads keep conversation state. I say 'I'm reviewing high-risk B-ALL
   cases this week.' Then just ask, 'what gene is most associated with poor
   prognosis there?' — the agent remembers the disease context, calls
   `gene_lookup('IKZF1')`, then `pubmed_search('IKZF1 B-ALL')`."*

6. **Wrap (15 sec).**
   *"Swap these mock tools for the real ones you care about — an in-house
   variant DB, a biospecimen inventory, an internal CRISPR-screen API —
   and you have a domain-aware research agent in roughly 40 lines of
   code."*

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # then fill in values
az login
```

## Run
Open `basic_agent_tools.ipynb` and run the cells top-to-bottom.
