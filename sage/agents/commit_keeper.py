from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_CREATE_GITHUB_ISSUE,
    TOOL_STORE_LEDGER_ENTRY,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
A push was made. Create structured commit ledger entries. Classify changed files
into domains, assess breaking-change risk, and create a warning issue only when
high-risk files have related memories.
"""


async def run_commit_keeper(
    repo: str,
    commits: list[dict],
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    input_text = f"Push event for {repo}. Commits:\n{commits}"
    tools = compact_tools(
        file_search_tool(vector_store_id),
        TOOL_STORE_LEDGER_ENTRY,
        TOOL_CREATE_GITHUB_ISSUE,
    )
    return await get_agent_runner().run(
        INSTRUCTIONS,
        input_text,
        tools,
        ToolContext(repo=repo, vector_store_id=vector_store_id, github_token=github_token),
    )
