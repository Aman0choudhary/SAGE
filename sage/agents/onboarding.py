from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_GET_ACTIVE_PATTERNS,
    TOOL_GET_RECENT_LEDGER,
    TOOL_POST_GITHUB_COMMENT,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
Generate a complete onboarding briefing:
1. Security first
2. Architecture by domain
3. Past incidents and lessons
4. Key people
5. Forbidden patterns
6. Recent changes

Use actual memory refs. Do not invent decisions.
"""


async def run_onboarding(
    repo: str,
    number: int,
    target_user: str,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    input_text = f"Onboard @{target_user} to {repo}."
    tools = compact_tools(
        file_search_tool(vector_store_id),
        TOOL_GET_RECENT_LEDGER,
        TOOL_GET_ACTIVE_PATTERNS,
        TOOL_POST_GITHUB_COMMENT,
    )
    return await get_agent_runner().run(
        INSTRUCTIONS,
        input_text,
        tools,
        ToolContext(
            repo=repo,
            number=number,
            vector_store_id=vector_store_id,
            github_token=github_token,
        ),
    )
