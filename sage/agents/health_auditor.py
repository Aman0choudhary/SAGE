from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_GENERATE_DASHBOARD,
    TOOL_GET_ALL_PATTERNS,
    TOOL_GET_LEDGER_SUMMARY,
    TOOL_GET_PROMISE_STATS,
    TOOL_POST_GITHUB_COMMENT,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
Generate a health report for this repository's decision memory:
- domain coverage
- stale decisions
- possible conflicts
- pattern violation rate
- promise kept/broken ratio
- security inventory

Then call generate_dashboard and post the report link/path.
"""


async def run_health_auditor(
    repo: str,
    number: int,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    tools = compact_tools(
        file_search_tool(vector_store_id),
        TOOL_GET_ALL_PATTERNS,
        TOOL_GET_PROMISE_STATS,
        TOOL_GET_LEDGER_SUMMARY,
        TOOL_GENERATE_DASHBOARD,
        TOOL_POST_GITHUB_COMMENT,
    )
    return await get_agent_runner().run(
        INSTRUCTIONS,
        f"Run SAGE health audit for {repo}.",
        tools,
        ToolContext(
            repo=repo,
            number=number,
            vector_store_id=vector_store_id,
            github_token=github_token,
        ),
    )
