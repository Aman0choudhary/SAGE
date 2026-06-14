from sage.agents.base import AgentResult
from sage.agents import pr_review


class FakeRunner:
    def __init__(self):
        self.calls = []

    async def run(self, instructions, input_text, tools, context):
        self.calls.append(
            {
                "instructions": instructions,
                "input_text": input_text,
                "tools": tools,
                "context": context,
            }
        )
        return AgentResult(status="ok", output_text="done")


async def test_pr_review_uses_five_layer_tools(monkeypatch):
    fake = FakeRunner()
    monkeypatch.setattr(pr_review, "get_agent_runner", lambda: fake)

    await pr_review.run_pr_review(
        repo="octo/repo",
        pr_number=47,
        title="Add cache",
        body="Fixes #43",
        diff="+ redis_client.get('token')",
        author="alice",
        linked_issue=43,
        vector_store_id="vs_123",
        github_token="installation-token",
    )

    tools = fake.calls[0]["tools"]
    tool_types = [tool["type"] for tool in tools]
    function_names = [tool["name"] for tool in tools if tool["type"] == "function"]

    assert "file_search" in tool_types
    assert "web_search" in tool_types
    assert "get_promises" in function_names
    assert "get_active_patterns" in function_names
    assert "post_github_comment" in function_names
    assert fake.calls[0]["context"].github_token == "installation-token"
