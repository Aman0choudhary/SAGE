from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_GET_PREMORTEM_QUESTIONS,
    TOOL_POST_GITHUB_COMMENT,
    TOOL_STORE_PROMISE,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
You are SAGE. A developer replied to your pre-mortem.
Evaluate whether they answered the hard questions, extract concrete promises,
store each promise, and post either an acknowledgement or specific pushback.
"""


async def run_followup(
    repo: str,
    issue_number: int,
    comment_body: str,
    commenter: str | None = None,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    input_text = (
        f"Issue #{issue_number} follow-up by @{commenter or 'unknown'}:\n\n"
        f"{comment_body or ''}"
    )
    tools = compact_tools(
        file_search_tool(vector_store_id),
        TOOL_GET_PREMORTEM_QUESTIONS,
        TOOL_STORE_PROMISE,
        TOOL_POST_GITHUB_COMMENT,
    )
    return await get_agent_runner().run(
        INSTRUCTIONS,
        input_text,
        tools,
        ToolContext(
            repo=repo,
            number=issue_number,
            vector_store_id=vector_store_id,
            github_token=github_token,
        ),
    )
