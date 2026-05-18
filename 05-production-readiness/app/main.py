"""FastAPI front door for the literature-triage agent."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional

from agent_framework import AgentSession
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import build_agent_client, create_agent


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    client, credential = build_agent_client()
    agent = create_agent(client)
    app.state.client = client
    app.state.credential = credential
    app.state.agent = agent
    app.state.sessions: dict[str, AgentSession] = {}
    try:
        yield
    finally:
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
    sessions: dict[str, AgentSession] = app.state.sessions

    sid = req.session_id
    session = sessions.get(sid) if sid else None
    if session is None:
        session = AgentSession()
        sid = sid or f"s-{len(sessions) + 1}"
        sessions[sid] = session

    result = await agent.run(req.message, session=session)
    return ChatResponse(reply=str(result), session_id=sid)
