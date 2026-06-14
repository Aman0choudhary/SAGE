from __future__ import annotations

from pathlib import Path

from sage.memory.store import get_memory_store


async def generate_dashboard_file(repo: str, output: str | Path | None = None) -> Path:
    path = Path(output or "sage-dashboard.html")
    stats = await get_memory_store().stats(repo)
    html = render_dashboard(repo, stats)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path.resolve()


def render_dashboard(repo: str, stats: dict) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SAGE Dashboard - {repo}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #16202a; background: #f6f8fb; }}
    header {{ background: #102033; color: white; padding: 28px 40px; }}
    main {{ max-width: 1040px; margin: 28px auto; padding: 0 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }}
    .card {{ background: white; border: 1px solid #dde3ea; border-radius: 8px; padding: 18px; }}
    .value {{ font-size: 32px; font-weight: 700; margin-top: 8px; }}
    section {{ margin-top: 28px; background: white; border: 1px solid #dde3ea; border-radius: 8px; padding: 20px; }}
    code {{ background: #eef2f7; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>SAGE Dashboard</h1>
    <p>{repo}</p>
  </header>
  <main>
    <div class="grid">
      <div class="card"><div>Total memories</div><div class="value">{stats.get("total_memories", 0)}</div></div>
      <div class="card"><div>Patterns</div><div class="value">{stats.get("patterns", 0)}</div></div>
      <div class="card"><div>Promises</div><div class="value">{stats.get("promises", 0)}</div></div>
      <div class="card"><div>Ledger entries</div><div class="value">{stats.get("ledger_entries", 0)}</div></div>
    </div>
    <section>
      <h2>Memory Store</h2>
      <p>Vector Store: <code>{stats.get("vector_store_id") or "not configured"}</code></p>
      <p>Promise results: {stats.get("promises_kept", 0)} kept, {stats.get("promises_broken", 0)} broken.</p>
    </section>
  </main>
</body>
</html>
"""
