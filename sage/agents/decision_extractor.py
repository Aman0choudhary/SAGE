from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.github.fetcher import truncate_diff
from sage.tools.definitions import (
    TOOL_INCREMENT_COUNTER,
    TOOL_POST_GITHUB_COMMENT,
    TOOL_STORE_MEMORY,
    TOOL_STORE_PATTERN,
    compact_tools,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
A PR was merged. Extract durable decisions from comments and diff.

For each real decision, rule, incident lesson, or pattern:
- capture what was decided;
- capture the reasoning;
- identify files and domains;
- identify who made it when possible;
- store it with store_memory.

Store reviewer rules with store_pattern. Ignore noise such as LGTM, thanks, and
style nits. Post a final summary comment with how many decisions were captured.
"""


async def run_decision_extractor(
    repo: str,
    pr_number: int,
    comments: list[str] | None,
    diff: str,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    joined_comments = "\n\n---\n\n".join(comments or [])
    input_text = f"""
Merged PR #{pr_number}

Comments:
{joined_comments}

Diff:
{truncate_diff(diff)}
""".strip()
    tools = compact_tools(
        TOOL_STORE_MEMORY,
        TOOL_STORE_PATTERN,
        TOOL_POST_GITHUB_COMMENT,
        TOOL_INCREMENT_COUNTER,
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
