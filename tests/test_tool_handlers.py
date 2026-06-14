from sage.memory.store import InMemoryStore, set_memory_store
from sage.tools.handlers import ToolContext, execute_tool


async def test_store_and_get_promises_tool_round_trip():
    set_memory_store(InMemoryStore())
    context = ToolContext(repo="octo/repo", number=9)

    await execute_tool(
        "store_promise",
        {
            "repo": "octo/repo",
            "issue_number": 9,
            "promise": "TTL will be 30s",
            "made_by": "alice",
        },
        context,
    )
    result = await execute_tool(
        "get_promises",
        {"repo": "octo/repo", "issue_number": 9},
        context,
    )

    assert "TTL will be 30s" in result


async def test_post_comment_tool_dry_runs_without_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    context = ToolContext(repo="octo/repo", number=2)

    result = await execute_tool(
        "post_github_comment",
        {"repo": "octo/repo", "number": 2, "body": "hello"},
        context,
    )

    assert "dry_run" in result


async def test_post_comment_tool_uses_context_token(monkeypatch):
    calls = []

    async def fake_post(repo, number, body, token=None):
        calls.append({"repo": repo, "number": number, "body": body, "token": token})
        return {"status": "posted"}

    monkeypatch.setattr("sage.tools.handlers.github_comments.post", fake_post)
    context = ToolContext(repo="octo/repo", number=2, github_token="installation-token")

    await execute_tool(
        "post_github_comment",
        {"repo": "octo/repo", "number": 2, "body": "hello"},
        context,
    )

    assert calls[0]["token"] == "installation-token"
