from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from sage.github.comments import github_comments
from sage.memory.store import get_memory_store
from sage.memory.vector_store import OpenAIVectorStore


@dataclass
class ToolContext:
    repo: str
    number: int | None = None
    vector_store_id: str | None = None
    github_token: str | None = None


def _serialise(value: Any) -> str:
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    if isinstance(value, list):
        return json.dumps(
            [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in value],
            default=str,
        )
    if isinstance(value, dict):
        return json.dumps(value, default=str)
    return str(value)


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    context: ToolContext,
) -> str:
    store = get_memory_store()

    if tool_name == "post_github_comment":
        result = await github_comments.post(
            arguments.get("repo", context.repo),
            arguments.get("number", context.number),
            arguments["body"],
            token=context.github_token,
        )
        return _serialise(result)

    if tool_name == "set_github_label":
        result = await github_comments.add_label(
            arguments.get("repo", context.repo),
            arguments.get("number", context.number),
            arguments["label"],
            token=context.github_token,
        )
        return _serialise(result)

    if tool_name == "create_github_issue":
        result = await github_comments.create_issue(
            arguments.get("repo", context.repo),
            arguments["title"],
            arguments["body"],
            token=context.github_token,
        )
        return _serialise(result)

    if tool_name == "store_memory":
        memory_args = dict(arguments)
        repo = memory_args.pop("repo", context.repo)
        result = await store.save_memory(
            repo=repo,
            vector_store_file_id=None,
            **memory_args,
        )
        if context.vector_store_id:
            result.vector_store_file_id = await OpenAIVectorStore().upload_memory(
                vector_store_id=context.vector_store_id,
                memory_ref=result.memory_ref,
                title=memory_args["title"],
                content=memory_args["content"],
                metadata=memory_args,
            )
            await store.set_memory_vector_file_id(
                repo,
                result.memory_ref,
                result.vector_store_file_id,
            )
        return _serialise(result)

    if tool_name == "update_memory":
        result = await store.override_memory(context.repo, **arguments)
        return _serialise(result)

    if tool_name == "store_pattern":
        result = await store.store_pattern(
            repo=arguments.get("repo", context.repo),
            rule=arguments["rule"],
            source_pr=arguments.get("source_pr"),
            stated_by=arguments.get("stated_by"),
        )
        return _serialise(result)

    if tool_name == "get_active_patterns":
        result = await store.get_active_patterns(arguments.get("repo", context.repo))
        return _serialise(result)

    if tool_name == "get_all_patterns":
        result = await store.get_all_patterns(arguments.get("repo", context.repo))
        return _serialise(result)

    if tool_name == "store_promise":
        result = await store.store_promise(
            repo=arguments.get("repo", context.repo),
            issue_number=arguments["issue_number"],
            promise=arguments["promise"],
            made_by=arguments.get("made_by"),
        )
        return _serialise(result)

    if tool_name == "store_promise_placeholders":
        result = {
            "status": "stored",
            "repo": arguments.get("repo", context.repo),
            "issue_number": arguments["issue_number"],
            "questions": arguments.get("questions", []),
        }
        return _serialise(result)

    if tool_name == "get_promises":
        result = await store.get_promises(
            repo=arguments.get("repo", context.repo),
            issue_number=arguments["issue_number"],
        )
        return _serialise(result)

    if tool_name == "update_promise_status":
        result = await store.update_promise_status(
            repo=arguments.get("repo", context.repo),
            issue_number=arguments["issue_number"],
            promise=arguments["promise"],
            status=arguments["status"],
        )
        return _serialise(result)

    if tool_name == "get_premortem_questions":
        return _serialise({"questions": []})

    if tool_name == "store_ledger_entry":
        repo = arguments.pop("repo", context.repo)
        result = await store.store_ledger_entry(repo=repo, **arguments)
        return _serialise(result)

    if tool_name == "get_recent_ledger":
        stats = await store.stats(arguments.get("repo", context.repo))
        return _serialise({"entries": [], "stats": stats})

    if tool_name == "get_ledger_summary":
        stats = await store.stats(arguments.get("repo", context.repo))
        return _serialise({"ledger_entries": stats["ledger_entries"]})

    if tool_name == "get_promise_stats":
        stats = await store.stats(arguments.get("repo", context.repo))
        return _serialise(
            {
                "promises": stats["promises"],
                "kept": stats["promises_kept"],
                "broken": stats["promises_broken"],
            }
        )

    if tool_name == "generate_dashboard":
        from sage.cli.dashboard import generate_dashboard_file

        path = await generate_dashboard_file(arguments.get("repo", context.repo))
        return _serialise({"path": str(path)})

    if tool_name == "get_memory_authors":
        repo = arguments.get("repo", context.repo)
        memory_ref = arguments["memory_ref"]
        memories = get_memory_store().memories[repo]
        authors = [memory.author_github for memory in memories if memory.memory_ref == memory_ref]
        return _serialise({"memory_ref": memory_ref, "authors": [author for author in authors if author]})

    if tool_name == "increment_counter":
        value = await store.increment_counter(
            arguments.get("repo", context.repo),
            arguments["counter"],
        )
        return _serialise({"status": "ok", "counter": arguments["counter"], "value": value})

    return _serialise({"status": "unknown_tool", "tool": tool_name})
