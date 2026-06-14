from __future__ import annotations

from sage.agents.base import get_agent_runner
from sage.tools.definitions import (
    TOOL_POST_GITHUB_COMMENT,
    WEB_SEARCH_TOOL,
    compact_tools,
    file_search_tool,
)
from sage.tools.handlers import ToolContext

INSTRUCTIONS = """
Answer the developer's question using SAGE memory. Search relevant decisions and
answer like a senior engineer who was there: specific, named, dated. Use memory
refs. If memory does not know, say so instead of guessing.
"""


async def run_sage_ask(
    repo: str,
    number: int,
    question: str,
    vector_store_id: str | None = None,
    github_token: str | None = None,
):
    tools = compact_tools(
        file_search_tool(vector_store_id),
        WEB_SEARCH_TOOL,
        TOOL_POST_GITHUB_COMMENT,
    )
    return await get_agent_runner().run(
        INSTRUCTIONS,
        question,
        tools,
        ToolContext(
            repo=repo,
            number=number,
            vector_store_id=vector_store_id,
            github_token=github_token,
        ),
    )
