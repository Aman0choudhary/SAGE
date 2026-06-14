from __future__ import annotations

from typing import Any


def function_tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    }


def file_search_tool(vector_store_id: str | None) -> dict[str, Any] | None:
    if not vector_store_id:
        return None
    return {"type": "file_search", "vector_store_ids": [vector_store_id]}


WEB_SEARCH_TOOL = {"type": "web_search"}

TOOL_POST_GITHUB_COMMENT = function_tool(
    "post_github_comment",
    "Post a comment to a GitHub Issue or PR.",
    {
        "repo": {"type": "string", "description": "owner/repo"},
        "number": {"type": "integer", "description": "Issue or PR number"},
        "body": {"type": "string", "description": "Markdown comment body"},
    },
    ["repo", "number", "body"],
)

TOOL_SET_GITHUB_LABEL = function_tool(
    "set_github_label",
    "Apply a label to a GitHub Issue or PR.",
    {
        "repo": {"type": "string"},
        "number": {"type": "integer"},
        "label": {"type": "string", "description": "Example: sage-risk: high"},
    },
    ["repo", "number", "label"],
)

TOOL_CREATE_GITHUB_ISSUE = function_tool(
    "create_github_issue",
    "Create a GitHub issue.",
    {
        "repo": {"type": "string"},
        "title": {"type": "string"},
        "body": {"type": "string"},
    },
    ["repo", "title", "body"],
)

TOOL_STORE_MEMORY = function_tool(
    "store_memory",
    "Store a decision in SAGE memory using Vector Store content plus metadata.",
    {
        "title": {"type": "string"},
        "content": {"type": "string", "description": "Full decision text"},
        "memory_type": {
            "type": "string",
            "enum": ["decision", "rule", "incident", "incident_lesson", "pattern", "promise"],
        },
        "author": {"type": "string"},
        "files_affected": {"type": "array", "items": {"type": "string"}},
        "domains": {"type": "array", "items": {"type": "string"}},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "source_pr": {"type": "integer"},
    },
    ["title", "content", "memory_type"],
)

TOOL_UPDATE_MEMORY = function_tool(
    "update_memory",
    "Override an existing memory with new reasoning.",
    {
        "memory_ref": {"type": "string"},
        "new_content": {"type": "string"},
        "override_reason": {"type": "string"},
        "overridden_by": {"type": "string"},
    },
    ["memory_ref", "new_content", "override_reason"],
)

TOOL_STORE_PATTERN = function_tool(
    "store_pattern",
    "Store a reviewer-stated rule as a permanent enforced pattern.",
    {
        "repo": {"type": "string"},
        "rule": {"type": "string"},
        "source_pr": {"type": "integer"},
        "stated_by": {"type": "string"},
    },
    ["repo", "rule", "source_pr"],
)

TOOL_GET_ACTIVE_PATTERNS = function_tool(
    "get_active_patterns",
    "Get all active enforced patterns for this repo.",
    {"repo": {"type": "string"}},
    ["repo"],
)

TOOL_GET_ALL_PATTERNS = function_tool(
    "get_all_patterns",
    "Get all patterns for this repo, including inactive ones.",
    {"repo": {"type": "string"}},
    ["repo"],
)

TOOL_STORE_PROMISE = function_tool(
    "store_promise",
    "Store a developer promise from an issue for later verification.",
    {
        "repo": {"type": "string"},
        "issue_number": {"type": "integer"},
        "promise": {"type": "string"},
        "made_by": {"type": "string"},
    },
    ["repo", "issue_number", "promise"],
)

TOOL_STORE_PROMISE_PLACEHOLDERS = function_tool(
    "store_promise_placeholders",
    "Store empty promise placeholders after a pre-mortem is posted.",
    {
        "repo": {"type": "string"},
        "issue_number": {"type": "integer"},
        "questions": {"type": "array", "items": {"type": "string"}},
    },
    ["repo", "issue_number", "questions"],
)

TOOL_GET_PROMISES = function_tool(
    "get_promises",
    "Get all promises made on a specific issue.",
    {
        "repo": {"type": "string"},
        "issue_number": {"type": "integer"},
    },
    ["repo", "issue_number"],
)

TOOL_UPDATE_PROMISE_STATUS = function_tool(
    "update_promise_status",
    "Update whether a promise was kept or broken.",
    {
        "repo": {"type": "string"},
        "issue_number": {"type": "integer"},
        "promise": {"type": "string"},
        "status": {"type": "string", "enum": ["pending", "kept", "broken", "overridden"]},
    },
    ["repo", "issue_number", "promise", "status"],
)

TOOL_GET_PREMORTEM_QUESTIONS = function_tool(
    "get_premortem_questions",
    "Fetch previously asked pre-mortem questions for an issue.",
    {
        "repo": {"type": "string"},
        "issue_number": {"type": "integer"},
    },
    ["repo", "issue_number"],
)

TOOL_STORE_LEDGER_ENTRY = function_tool(
    "store_ledger_entry",
    "Write a structured commit log entry.",
    {
        "repo": {"type": "string"},
        "commit_sha": {"type": "string"},
        "author": {"type": "string"},
        "files_changed": {"type": "array", "items": {"type": "string"}},
        "domains_touched": {"type": "array", "items": {"type": "string"}},
        "breaking_risk": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    ["repo", "commit_sha", "author"],
)

TOOL_GET_RECENT_LEDGER = function_tool(
    "get_recent_ledger",
    "Get recent commit ledger entries for a repo.",
    {"repo": {"type": "string"}, "days": {"type": "integer"}},
    ["repo"],
)

TOOL_GET_LEDGER_SUMMARY = function_tool(
    "get_ledger_summary",
    "Get commit ledger summary metrics for a repo.",
    {"repo": {"type": "string"}},
    ["repo"],
)

TOOL_GET_PROMISE_STATS = function_tool(
    "get_promise_stats",
    "Get promise kept/broken/pending statistics for a repo.",
    {"repo": {"type": "string"}},
    ["repo"],
)

TOOL_GENERATE_DASHBOARD = function_tool(
    "generate_dashboard",
    "Generate a local HTML dashboard report and return its path.",
    {"repo": {"type": "string"}},
    ["repo"],
)

TOOL_GET_MEMORY_AUTHORS = function_tool(
    "get_memory_authors",
    "Find authors associated with a memory ref.",
    {"repo": {"type": "string"}, "memory_ref": {"type": "string"}},
    ["repo", "memory_ref"],
)

TOOL_INCREMENT_COUNTER = function_tool(
    "increment_counter",
    "Increment a named repo counter.",
    {"repo": {"type": "string"}, "counter": {"type": "string"}},
    ["repo", "counter"],
)


def compact_tools(*tools: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [tool for tool in tools if tool is not None]

