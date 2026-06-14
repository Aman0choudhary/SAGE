from __future__ import annotations

import json
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from sage import router
from sage.config import get_settings
from sage.dispatcher import dispatch_agent
from sage.github.webhooks import validate_github_signature

app = FastAPI(title="SAGE", version="0.1.0")


@app.get("/")
async def root() -> dict[str, str]:
    settings = get_settings()
    return {
        "service": "SAGE",
        "status": "ok",
        "model": settings.model,
        "health": "/health",
        "webhook": "/webhook",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "model": settings.model}


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: Annotated[str | None, Header()] = None,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    settings = get_settings()
    payload_bytes = await request.body()

    if not validate_github_signature(
        payload_bytes,
        x_hub_signature_256,
        settings.github_webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    agent_name = router.route(x_github_event, payload)
    if agent_name != "ignore":
        background_tasks.add_task(dispatch_agent, agent_name, payload)

    return {"status": "ok", "agent": agent_name}


@app.get("/repos/{owner}/{repo}/stats")
async def repo_stats(owner: str, repo: str) -> dict:
    from sage.memory.store import get_memory_store

    return await get_memory_store().stats(f"{owner}/{repo}")
