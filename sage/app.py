from __future__ import annotations

import json
import logging
from html import escape
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from sage import router
from sage.config import get_settings
from sage.dispatcher import dispatch_agent
from sage.github.webhooks import validate_github_signature

app = FastAPI(title="SAGE", version="0.1.0")
logger = logging.getLogger("sage")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    settings = get_settings()
    model = escape(settings.model)
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SAGE - Semantic Agentic Git Engine</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #101318;
      --panel: #171c24;
      --text: #f5f7fb;
      --muted: #a8b1c2;
      --line: #2a3240;
      --accent: #67e8a5;
      --accent-2: #8ab4ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at 15% 15%, #1d2938 0, transparent 30%), var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    main {{
      width: min(960px, calc(100% - 32px));
      margin: 0 auto;
      padding: 64px 0;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 11px;
      border: 1px solid rgba(103, 232, 165, 0.35);
      border-radius: 999px;
      color: var(--accent);
      background: rgba(103, 232, 165, 0.08);
      font-size: 14px;
      font-weight: 700;
    }}
    h1 {{
      margin: 20px 0 12px;
      font-size: clamp(42px, 7vw, 76px);
      letter-spacing: 0;
      line-height: 1;
    }}
    .lead {{
      max-width: 760px;
      margin: 0 0 30px;
      color: var(--muted);
      font-size: 20px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin-top: 28px;
    }}
    section {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(23, 28, 36, 0.88);
      padding: 20px;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 18px;
    }}
    p, ol {{
      margin: 0;
      color: var(--muted);
    }}
    ol {{ padding-left: 20px; }}
    li + li {{ margin-top: 8px; }}
    a {{
      color: var(--accent-2);
      font-weight: 700;
      text-decoration: none;
    }}
    a:hover {{ text-decoration: underline; }}
    code {{
      padding: 2px 6px;
      border-radius: 6px;
      background: #0b0e13;
      color: #dbe7ff;
    }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 42px;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #1a2330;
      color: var(--text);
    }}
    .button.primary {{
      border-color: rgba(103, 232, 165, 0.45);
      background: #12301f;
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <main>
    <span class="badge">Cloud Run live</span>
    <h1>SAGE</h1>
    <p class="lead">Semantic Agentic Git Engine: a GitHub-native AI reviewer that listens to issues and pull requests, reasons about risk, asks follow-up questions, stores repo memory, and comments back automatically.</p>

    <div class="links">
      <a class="button primary" href="https://github.com/Aman0choudhary/SAGE">GitHub repo</a>
      <a class="button" href="/health">Health check</a>
      <a class="button" href="https://github.com/Aman0choudhary/SAGE/issues/9">Live proof issue</a>
    </div>

    <div class="grid">
      <section>
        <h2>Status</h2>
        <p>Service is running on Cloud Run with model <code>{model}</code>. Webhooks are accepted at <code>/webhook</code>.</p>
      </section>
      <section>
        <h2>Judge Test</h2>
        <ol>
          <li>Open the GitHub repo.</li>
          <li>Create an issue with a technical idea or risky change.</li>
          <li>SAGE should comment back and apply a risk label.</li>
        </ol>
      </section>
      <section>
        <h2>What It Shows</h2>
        <p>Agent routing, GitHub webhook auth, OpenAI-powered analysis, memory storage, labels, comments, and production deployment.</p>
      </section>
    </div>
  </main>
</body>
</html>"""
    )


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
        settings = get_settings()
        if settings.is_production:
            logger.info("Dispatching agent synchronously", extra={"agent": agent_name})
            await dispatch_agent(agent_name, payload)
        else:
            background_tasks.add_task(dispatch_agent, agent_name, payload)

    return {"status": "ok", "agent": agent_name}


@app.get("/repos/{owner}/{repo}/stats")
async def repo_stats(owner: str, repo: str) -> dict:
    from sage.memory.store import get_memory_store

    return await get_memory_store().stats(f"{owner}/{repo}")
