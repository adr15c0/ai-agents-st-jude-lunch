"""FastAPI front door for the literature-triage agent.

Exposes:
  GET  /healthz  ->  liveness probe
  POST /chat     ->  { "message": "...", "thread_id": "..." }  ->  { "reply": "..." }

The container's managed identity (set up in Bicep) authenticates against the
Foundry project. APIM sits in front and handles rate limiting, auth, token
budgeting, etc. — see ../infra/apim-policy.xml.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import build_agent_client, create_agent


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    client, credential = build_agent_client()
    agent = create_agent(client)
    app.state.client = client
    app.state.credential = credential
    app.state.agent = agent
    app.state.threads = {}
    try:
        yield
    finally:
        await client.close()
        await credential.close()


app = FastAPI(title="Literature Triage Agent", version=os.environ.get("APP_VERSION", "0.1.0"), lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must be non-empty")

    agent = app.state.agent
    threads: dict = app.state.threads

    thread = threads.get(req.thread_id) if req.thread_id else None
    if thread is None:
        thread = agent.get_new_thread()
        tid = req.thread_id or f"t-{len(threads) + 1}"
        threads[tid] = thread
    else:
        tid = req.thread_id

    result = await agent.run(req.message, thread=thread)
    return ChatResponse(reply=str(result), thread_id=tid)
