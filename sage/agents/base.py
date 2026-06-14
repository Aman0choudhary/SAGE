from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from openai import AsyncOpenAI

from sage.config import get_settings
from sage.tools.handlers import ToolContext, execute_tool

ToolExecutor = Callable[[str, dict[str, Any], ToolContext], Awaitable[str]]


@dataclass
class AgentResult:
    status: str
    output_text: str = ""
    raw_response: Any | None = None


class DryRunAgentRunner:
    async def run(
        self,
        instructions: str,
        input_text: str,
        tools: list[dict[str, Any]],
        context: ToolContext,
    ) -> AgentResult:
        return AgentResult(
            status="dry_run",
            output_text=(
                "OPENAI_API_KEY is not configured. Agent was not executed. "
                f"Received {len(tools)} tools for {context.repo}."
            ),
        )


class ResponsesAgentRunner:
    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        model: str | None = None,
        execute: ToolExecutor = execute_tool,
        max_tool_rounds: int = 8,
    ) -> None:
        settings = get_settings()
        self.client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.model
        self.execute = execute
        self.max_tool_rounds = max_tool_rounds

    async def run(
        self,
        instructions: str,
        input_text: str,
        tools: list[dict[str, Any]],
        context: ToolContext,
    ) -> AgentResult:
        input_items: list[Any] = [
            {
                "role": "user",
                "content": _with_tool_context(input_text, context),
            }
        ]
        response: Any | None = None

        for _ in range(self.max_tool_rounds):
            response = await self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=input_items,
                tools=tools,
            )

            output = list(getattr(response, "output", []) or [])
            input_items.extend(output)
            function_calls = [
                item for item in output if getattr(item, "type", None) == "function_call"
            ]
            if not function_calls:
                return AgentResult(
                    status=getattr(response, "status", "completed"),
                    output_text=getattr(response, "output_text", ""),
                    raw_response=response,
                )

            for item in function_calls:
                arguments = _parse_arguments(getattr(item, "arguments", "{}"))
                try:
                    tool_output = await self.execute(
                        getattr(item, "name"),
                        arguments,
                        context,
                    )
                except Exception as exc:  # Let the model recover from tool failures.
                    tool_output = json.dumps(
                        {
                            "status": "tool_error",
                            "tool": getattr(item, "name", "unknown"),
                            "error": str(exc),
                        }
                    )

                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": getattr(item, "call_id"),
                        "output": tool_output,
                    }
                )

        return AgentResult(
            status="max_tool_rounds_exceeded",
            output_text="Agent exceeded the maximum number of tool rounds.",
            raw_response=response,
        )


def _parse_arguments(raw: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _with_tool_context(input_text: str, context: ToolContext) -> str:
    number = context.number if context.number is not None else "not applicable"
    return f"""
Tool context for function calls:
- repo: {context.repo}
- issue_or_pr_number: {number}

When calling tools that require `repo`, use exactly: {context.repo}
When calling tools that require `number`, use exactly: {number}

Event input:
{input_text}
""".strip()


def get_agent_runner() -> ResponsesAgentRunner | DryRunAgentRunner:
    settings = get_settings()
    if not settings.has_openai:
        return DryRunAgentRunner()
    return ResponsesAgentRunner()
