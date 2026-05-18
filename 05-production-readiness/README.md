# Demo 5 — Production Readiness (Container Apps + AI Gateway)

Where this demo sits in the St. Jude agentic lifecycle:

```
[ Cloud infra team ]    [ You — researcher ]    [ You — researcher ]    [ Platform team ]
  Foundry project   ->    Build the agent    ->   Evaluations + Sec  ->  Containerize + APIM
  + model endpoints       (Demos 1–3)             (Demo 4)               (THIS DEMO)
```

You've built the agent (Demos 1–3) and you've passed the release gate
(Demo 4). Now it's time to hand off something the platform team can
actually run. That means three things:

1. **A FastAPI surface** around the agent (`app/main.py`).
2. **A container image** built from a small, hardened Dockerfile.
3. **Deployment artifacts** the platform team can apply — an Azure
   Container Apps Bicep module and an APIM policy that fronts your app as
   part of the centrally-managed AI Gateway.

The Container App stays **internal** (no public ingress). All inbound
traffic comes through APIM, which enforces auth, rate limits, and token
budgets before forwarding to the container. The container authenticates
*out* to Foundry using its own managed identity — your code never sees a
key.

## What this shows
- A minimal, production-shaped FastAPI wrapper for an Agent Framework agent
  with a `lifespan` that builds/cleans up the agent on startup/shutdown.
- A non-root, slim Dockerfile that runs `uvicorn` with a liveness probe path.
- Bicep (`infra/container-app.bicep`) for ACA env + app with:
  - User-assigned managed identity (Foundry access)
  - ACR image pull via the same identity
  - Internal-only ingress (APIM is the only entry point)
  - Liveness probe, autoscale rule (1–5 replicas on HTTP concurrency)
- An APIM policy (`infra/apim-policy.xml`) implementing the AI Gateway
  pattern: subscription key, JWT validation, per-key RPS rate limit,
  per-key daily token quota, and outbound token-usage accounting.

## Use case

You're a researcher whose agent has cleared the eval/security gate. You
don't want to manage a VM, an inference endpoint, or any auth plumbing —
you want to hand the platform team a portable container and a Bicep file
they can drop into their existing landing zone. Once it's deployed:

- **You** get an internal HTTPS endpoint and a place in the AI Gateway
  catalog.
- **Downstream consumers** (lab dashboards, internal notebooks, other
  agents) call a single APIM URL, with their own subscription key,
  governed by the same gateway policies as every other model and tool in
  the institution.
- **The platform team** sees per-consumer usage, can revoke keys, and can
  reshape rate limits / token budgets without you redeploying the agent.

## Talk track

Use this as a speaking outline while you walk through the artifacts.

1. **Frame the handoff (45 sec).**
   *"We've built the agent and we've passed the eval gate. The platform
   team won't deploy a notebook — they need a real service. Here's the
   shape of that handoff: a FastAPI app, a Dockerfile, a Bicep module, and
   an APIM policy. Four files."*

2. **Show the FastAPI app (`app/main.py`).**
   *"The agent's tools and instructions live in `app/agent.py` — same code
   as Demo 1. `main.py` wraps it in two endpoints: `/healthz` for the
   probe, `/chat` for actual traffic. The `lifespan` block builds the
   agent once at startup and cleans up on shutdown — you don't pay the
   warm-up cost on every request."*

3. **Auth model (briefly point at `DefaultAzureCredential` in `agent.py`).**
   *"This is the key trick: `DefaultAzureCredential` means the same code
   runs locally with my `az login` identity AND inside Container Apps
   with the managed identity the platform team grants. Zero keys in code,
   zero keys in env vars."*

4. **Dockerfile.**
   *"Python 3.12-slim, non-root user, single CMD, no shell tricks. Roughly
   200 MB. The platform team's CI builds this and pushes it to the shared
   ACR — I never push images by hand."*

5. **Local smoke test (optional cell in the notebook).**
   *"Before I hand it off, I build the image locally and hit `/chat` with
   a curl. If that works, I push."*

6. **Container App Bicep (`infra/container-app.bicep`).**
   *"Here's the ACA module. The interesting bits: `ingress.external = false`
   so only APIM can reach us, a user-assigned managed identity for
   pull-from-ACR AND access-to-Foundry, a liveness probe pointing at
   `/healthz`, and an HTTP-concurrency autoscale rule capping at 5
   replicas. None of these numbers are sacred — the platform team will
   tune them."*

7. **APIM AI Gateway policy (`infra/apim-policy.xml`).**
   *"This is what 'wired up to the AI Gateway' actually means. Five
   policies in inbound order: require subscription key, validate Entra
   JWT, rate-limit at 60 RPM per key, enforce a per-key daily token
   budget, then forward to the internal ACA FQDN. On the way out we read
   `usage.total_tokens` from the response and bump the quota counter.
   Every model, tool, and agent in the institution sits behind a policy
   that looks just like this — that's the consistency the gateway
   provides."*

8. **The full lifecycle, in one picture.**
   *"So zoom out: cloud-infra provisions Foundry, I build (Demos 1–3),
   I evaluate (Demo 4), I hand the platform team this folder, they wire
   it into APIM, and downstream consumers call one URL. That's the loop."*

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # then fill in values
az login
```

## Run locally
```powershell
# 1. Run the FastAPI app
uvicorn app.main:app --reload --port 8000

# 2. In another shell, smoke-test
curl -s -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{ "message": "Brief me on TP53 and pull a couple of recent papers." }'
```

## Build the image
```powershell
docker build -t lit-triage-agent:dev .
docker run --rm -p 8000:8000 --env-file .env lit-triage-agent:dev
```

## Hand off to the platform team

1. Push the image to the institutional ACR (your CI pipeline does this).
2. PR `infra/container-app.bicep` into the platform team's landing-zone
   repo with the image tag pinned.
3. PR `infra/apim-policy.xml` into the AI Gateway repo, registering the
   new API + operation.
4. Subscribe consumers via APIM's developer portal.

A walkthrough notebook is provided in `production_readiness.ipynb` for
demoing the local build/test loop before the handoff.
