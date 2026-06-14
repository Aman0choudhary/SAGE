from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_GET_MEMORY_AUTHORS,
    TOOL_POST_GITHUB_COMMENT,
    TOOL_UPDATE_MEMORY,
    TOOL_UPDATE_PROMISE_STATUS,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
You are SAGE handling a PR reply command.

If the comment contains "sage: intentional", evaluate the reasoning, update the
relevant memory, and acknowledge the new commitment.

If it contains "sage: accidental", acknowledge and mark the issue as being fixed.

If it contains "sage: discuss", find original decision authors and tag them with
a clear discussion prompt.
"""


async def run_reply_handler(
    repo: str,
    pr_number: int,
    comment_body: str,
    commenter: str | None = None,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    input_text = f"PR #{pr_number} reply by @{commenter or 'unknown'}:\n\n{comment_body or ''}"
    tools = compact_tools(
        file_search_tool(vector_store_id),
        TOOL_UPDATE_MEMORY,
        TOOL_UPDATE_PROMISE_STATUS,
        TOOL_GET_MEMORY_AUTHORS,
        TOOL_POST_GITHUB_COMMENT,
    )
    return await get_agent_runner().run(
        INSTRUCTIONS,
        input_text,
        tools,
        ToolContext(
            repo=repo,
            number=pr_number,
            vector_store_id=vector_store_id,
            github_token=github_token,
        ),
    )
