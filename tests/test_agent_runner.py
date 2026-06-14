from dataclasses import dataclass

from sage.agents.base import ResponsesAgentRunner
from sage.tools.handlers import ToolContext


@dataclass
class FakeFunctionCall:
    type: str = "function_call"
    name: str = "store_promise"
    arguments: str = '{"issue_number": 1, "promise": "test"}'
    call_id: str = "call_1"


@dataclass
class FakeResponse:
    output: list
    status: str = "completed"
    output_text: str = ""


class FakeResponses:
    def __init__(self):
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return FakeResponse(output=[FakeFunctionCall()])
        return FakeResponse(output=[], output_text="done")


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


async def test_responses_runner_appends_function_call_output():
    async def fake_execute(name, arguments, context):
        assert name == "store_promise"
        assert arguments["issue_number"] == 1
        assert context.repo == "octo/repo"
        return '{"status": "ok"}'

    client = FakeClient()
    runner = ResponsesAgentRunner(client=client, model="test-model", execute=fake_execute)

    result = await runner.run(
        "instructions",
        "input",
        [{"type": "function", "name": "store_promise", "parameters": {}}],
        ToolContext(repo="octo/repo", number=1),
    )

    second_input = client.responses.calls[1]["input"]
    assert result.output_text == "done"
    assert any(item.get("type") == "function_call_output" for item in second_input if isinstance(item, dict))

