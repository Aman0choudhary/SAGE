from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_POST_GITHUB_COMMENT,
    TOOL_SET_GITHUB_LABEL,
    TOOL_STORE_PROMISE_PLACEHOLDERS,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
You are SAGE, a senior engineer with durable memory of this repository.
A new issue was opened. Your job:
1. Search past decisions and incidents for related failures.
2. Write a direct pre-mortem: what could go wrong and why.
3. Ask 3-5 hard questions the developer must answer before coding.
4. Set acceptance criteria based on likely failures.
5. Assign a risk level: LOW, MEDIUM, HIGH, or CRITICAL.
6. Post the pre-mortem as one GitHub comment.

Use concrete memory refs when available. Do not invent memories.
"""


async def run_premortem(
    repo: str,
    issue_number: int,
    title: str,
    body: str,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    input_text = f"Issue #{issue_number}: {title}\n\n{body or ''}"
    tools = compact_tools(
        file_search_tool(vector_store_id),
        TOOL_POST_GITHUB_COMMENT,
        TOOL_SET_GITHUB_LABEL,
        TOOL_STORE_PROMISE_PLACEHOLDERS,
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
