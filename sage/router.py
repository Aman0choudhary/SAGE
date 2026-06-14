from __future__ import annotations


def route(event_type: str | None, payload: dict) -> str:
    """Map a GitHub webhook event to a SAGE agent name."""
    if not event_type:
        return "ignore"

    action = payload.get("action")

    if event_type == "issues" and action == "opened":
        return "premortem"

    if event_type == "issue_comment":
        body = (payload.get("comment") or {}).get("body", "").lower()
        issue = payload.get("issue") or {}

        if "@sage ask" in body:
            return "sage_ask"
        if "@sage onboard" in body:
            return "onboarding"
        if "@sage health" in body:
            return "health_auditor"
        if issue.get("pull_request"):
            return "reply_handler"
        return "followup"

    if event_type == "pull_request":
        if action in {"opened", "synchronize", "reopened"}:
            return "pr_review"
        pull_request = payload.get("pull_request") or {}
        if action == "closed" and pull_request.get("merged"):
            return "decision_extractor"

    if event_type == "push":
        return "commit_keeper"

    return "ignore"

