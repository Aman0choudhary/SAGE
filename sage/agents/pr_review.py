from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.github.fetcher import truncate_diff
from sage.tools.definitions import (
    TOOL_GET_ACTIVE_PATTERNS,
    TOOL_GET_PROMISES,
    TOOL_POST_GITHUB_COMMENT,
    TOOL_SET_GITHUB_LABEL,
    WEB_SEARCH_TOOL,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
You are SAGE. Review this PR across exactly five layers.

Layer 1 - Memory conflicts:
Search the vector store for past decisions that conflict with this PR. Reason
about semantic equivalence, not just keywords.

Layer 2 - Promise verification:
Check stored promises from the linked issue against the actual diff. Be specific.

Layer 3 - Security sentinel:
Search memory for security decisions and use web_search for new dependency CVEs.
Flag SQL injection, weak hashing, unsafe eval, and hardcoded secrets.

Layer 4 - Code intelligence:
Identify dependencies, architecture changes, tech drift, and new failure modes.

Layer 5 - Pattern enforcement:
Fetch active patterns and check the diff against each one.

Post one structured GitHub comment. End with memory refs used, overall risk, and
these options: sage: intentional | sage: accidental | sage: discuss.
"""


async def run_pr_review(
    repo: str,
    pr_number: int,
    title: str,
    body: str,
    diff: str,
    author: str | None = None,
    linked_issue: int | None = None,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    input_text = f"""
PR #{pr_number}: {title}
Linked Issue: {f"#{linked_issue}" if linked_issue else "unknown"}
Author: @{author or "unknown"}

PR Description:
{body or ""}

Diff:
{truncate_diff(diff)}
""".strip()
    tools = compact_tools(
        file_search_tool(vector_store_id),
        WEB_SEARCH_TOOL,
        TOOL_GET_PROMISES,
        TOOL_GET_ACTIVE_PATTERNS,
        TOOL_POST_GITHUB_COMMENT,
        TOOL_SET_GITHUB_LABEL,
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
