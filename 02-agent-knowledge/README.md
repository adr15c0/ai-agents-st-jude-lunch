# Demo 2 — Agent + Knowledge (File Search / RAG)

An agent that can answer questions grounded in your own documents using
Foundry's hosted file-search (vector store) tool.

## What this shows
- Uploading local documents to a Foundry-hosted vector store
- Attaching `HostedFileSearchTool` to an agent
- Asking questions that require the agent to retrieve from the documents

## Use case

A study coordinator (or anyone on a research team) needs quick answers from
a long, dense protocol document — primary objectives, screening criteria,
sampling time points, stopping rules. Reading the PDF for the third time
this week is slow, and a raw LLM might invent details that would be
dangerous to act on. A RAG-grounded agent reads only the approved protocol
text, returns answers tied to that text, and refuses to guess when the
information isn't there.

In this demo the document in `data/` is a **synthetic** brief for a
fictional pediatric B-ALL relapse protocol (`PED-ALL-2025-01`). Foundry
chunks and embeds it into a managed vector store, and the agent answers via
`HostedFileSearchTool`. We then ask:
- In-scope questions (objectives, criteria, sampling) — should answer.
- An out-of-scope question (dosing in adult AML) — should refuse.

For real use you'd point this at your IRB-approved protocols, SOPs,
biospecimen handling guides, or institutional FAQs.

## Talk track

Use this as a speaking outline while you run the cells live.

1. **Frame the problem (45 sec).**
   *"On any given study we have a protocol that's 60 pages long, and the
   team is asking the same questions over and over: 'what are the inclusion
   criteria again?', 'when do we collect the Day-15 bone marrow?' A raw LLM
   can summarize, but it can also confidently make things up. For anything
   touching a protocol that's a non-starter. So we ground the agent — it
   can ONLY answer from the documents we hand it, and if it doesn't know,
   it says so."*

2. **Call out the disclaimer (briefly mention `data/ped-all-2025-01-protocol.md`).**
   *"This is a synthetic protocol I made up for the demo — not a real
   trial. In production this would be your IRB-approved protocol PDFs."*

3. **Upload + vector store (Cell 2).**
   *"Two SDK calls: upload the file with purpose `AGENTS`, then create a
   vector store from those file IDs. Foundry handles the chunking,
   embedding, and indexing for me. I never touch an embedding model
   directly."*

4. **Attach the tool (Cell 3).**
   *"I create the agent and hand it a `HostedFileSearchTool` pointing at
   the vector store. The instructions are strict: answer ONLY from the
   protocol, and if it's not there, defer to the PI or coordinator."*

5. **Primary endpoint question (Cell 4).**
   *"'What's the primary objective and the endpoint window?' — pulled
   directly from the document. Notice it can quote 'Day 29 ± 3'."*

6. **Eligibility (Cell 5).**
   *"Inclusion/exclusion summary — useful for fast screening conversations.
   Same grounding."*

7. **Sampling schedule (Cell 6).**
   *"Bone marrow vs cfDNA time points — operational questions the team
   asks every week."*

8. **Out-of-scope (Cell 7).**
   *"Now the safety check. I ask about a dosing detail that the protocol
   doesn't cover. A naive chatbot would happily make up a number. Our
   grounded agent says 'not in the document, talk to the PI.' That's
   exactly the behavior we want for anything clinical-adjacent."*

9. **Cleanup (Cell 8).**
   *"Tear down the vector store and uploaded files so demos don't leave
   artifacts in the Foundry project."*

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # then fill in values
az login
```

## Run
Open `agent_knowledge.ipynb` and run cells top-to-bottom. The `data/` folder
contains a sample document; replace it with your own content for the live demo.
