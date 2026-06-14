from __future__ import annotations

import re
from typing import Any

from sage.agents.commit_keeper import run_commit_keeper
from sage.agents.decision_extractor import run_decision_extractor
from sage.agents.followup import run_followup
from sage.agents.health_auditor import run_health_auditor
from sage.agents.onboarding import run_onboarding
from sage.agents.pr_review import run_pr_review
from sage.agents.premortem import run_premortem
from sage.agents.reply_handler import run_reply_handler
from sage.agents.sage_ask import run_sage_ask
from sage.config import get_settings
from sage.github.auth import token_for_payload
from sage.github.fetcher import GitHubFetcher, linked_issue_from_text
from sage.github.webhooks import repo_full_name
from sage.memory.store import get_memory_store
from sage.memory.vector_store import OpenAIVectorStore

ASK_RE = re.compile(r"@sage\s+ask\s+[\"']?(?P<question>.+?)[\"']?\s*$", re.I | re.S)
ONBOARD_RE = re.compile(r"@sage\s+onboard\s+@?(?P<user>[\w.-]+)", re.I)


async def resolve_vector_store_id(repo: str) -> str | None:
    store = get_memory_store()
    vector_store_id = await store.get_vector_store_id(repo)
    if vector_store_id:
        return vector_store_id

    settings = get_settings()
    if not settings.has_openai:
        return None

    try:
        vector_store_id = await OpenAIVectorStore().create_repo_vector_store(repo)
    except Exception:
        return None

    await store.set_vector_store_id(repo, vector_store_id)
    return vector_store_id


async def dispatch_agent(agent_name: str, payload: dict[str, Any]):
    repo = repo_full_name(payload)
    vector_store_id = await resolve_vector_store_id(repo)
    github_token = await token_for_payload(payload)
    fetcher = GitHubFetcher(token=github_token)

    if agent_name == "premortem":
        issue = payload.get("issue") or {}
        return await run_premortem(
            repo=repo,
            issue_number=issue["number"],
            title=issue.get("title", ""),
            body=issue.get("body", ""),
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "followup":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        user = comment.get("user") or {}
        return await run_followup(
            repo=repo,
            issue_number=issue["number"],
            comment_body=comment.get("body", ""),
            commenter=user.get("login"),
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "pr_review":
        pr = payload.get("pull_request") or {}
        user = pr.get("user") or {}
        linked_issue = linked_issue_from_text(pr.get("body"))
        diff = payload.get("diff") or await fetcher.fetch_pull_diff(repo, pr["number"])
        return await run_pr_review(
            repo=repo,
            pr_number=pr["number"],
            title=pr.get("title", ""),
            body=pr.get("body", ""),
            diff=diff,
            author=user.get("login"),
            linked_issue=linked_issue,
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "decision_extractor":
        pr = payload.get("pull_request") or {}
        diff = payload.get("diff") or await fetcher.fetch_pull_diff(repo, pr["number"])
        comments = payload.get("comments") or await fetcher.fetch_pr_conversation(repo, pr["number"])
        return await run_decision_extractor(
            repo=repo,
            pr_number=pr["number"],
            comments=comments,
            diff=diff,
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "reply_handler":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        user = comment.get("user") or {}
        return await run_reply_handler(
            repo=repo,
            pr_number=issue["number"],
            comment_body=comment.get("body", ""),
            commenter=user.get("login"),
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "commit_keeper":
        return await run_commit_keeper(
            repo=repo,
            commits=payload.get("commits", []),
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "sage_ask":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        question = extract_ask_question(comment.get("body", ""))
        return await run_sage_ask(
            repo=repo,
            number=issue["number"],
            question=question,
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "onboarding":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        target_user = extract_onboard_user(comment.get("body", "")) or "new-developer"
        return await run_onboarding(
            repo=repo,
            number=issue["number"],
            target_user=target_user,
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    if agent_name == "health_auditor":
        issue = payload.get("issue") or {}
        return await run_health_auditor(
            repo=repo,
            number=issue["number"],
            vector_store_id=vector_store_id,
            github_token=github_token,
        )

    return None


def extract_ask_question(body: str) -> str:
    match = ASK_RE.search(body or "")
    if not match:
        return body
    return match.group("question").strip().strip("\"'")


def extract_onboard_user(body: str) -> str | None:
    match = ONBOARD_RE.search(body or "")
    return match.group("user") if match else None
