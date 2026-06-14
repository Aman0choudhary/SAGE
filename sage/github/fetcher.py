from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from sage.config import get_settings

ISSUE_REF_RE = re.compile(r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(?P<number>\d+)", re.I)


def linked_issue_from_text(text: str | None) -> int | None:
    if not text:
        return None
    match = ISSUE_REF_RE.search(text)
    if not match:
        return None
    return int(match.group("number"))


def truncate_diff(diff: str | None, max_chars: int | None = None) -> str:
    if not diff:
        return ""
    limit = max_chars or get_settings().max_diff_chars
    if len(diff) <= limit:
        return diff
    return diff[:limit] + "\n\n[Diff truncated by SAGE]"


@dataclass
class GitHubFetcher:
    token: str | None = None

    def _headers(self, accept: str = "application/vnd.github+json") -> dict[str, str]:
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = self.token or get_settings().github_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def fetch_pull_diff(self, repo: str, pr_number: int) -> str:
        if not (self.token or get_settings().github_token):
            return ""
        url = f"{get_settings().github_api_url}/repos/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                url,
                headers=self._headers("application/vnd.github.v3.diff"),
            )
            response.raise_for_status()
            return response.text

    async def fetch_issue_comments(self, repo: str, number: int) -> list[str]:
        return [
            item.get("body", "")
            for item in await self._get_paginated(f"/repos/{repo}/issues/{number}/comments")
            if item.get("body")
        ]

    async def fetch_pr_review_comments(self, repo: str, pr_number: int) -> list[str]:
        return [
            item.get("body", "")
            for item in await self._get_paginated(f"/repos/{repo}/pulls/{pr_number}/comments")
            if item.get("body")
        ]

    async def fetch_pr_conversation(self, repo: str, pr_number: int) -> list[str]:
        issue_comments = await self.fetch_issue_comments(repo, pr_number)
        review_comments = await self.fetch_pr_review_comments(repo, pr_number)
        return issue_comments + review_comments

    async def list_closed_pulls(self, repo: str, limit: int = 200) -> list[dict[str, Any]]:
        pulls: list[dict[str, Any]] = []
        page = 1
        while len(pulls) < limit:
            batch = await self._get_json(
                f"/repos/{repo}/pulls",
                params={
                    "state": "closed",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": min(100, limit - len(pulls)),
                    "page": page,
                },
            )
            if not batch:
                break
            pulls.extend(batch)
            page += 1
        return pulls[:limit]

    async def _get_paginated(self, path: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = await self._get_json(path, params={"per_page": 100, "page": page})
            if not batch:
                return items
            items.extend(batch)
            page += 1

    async def _get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not (self.token or get_settings().github_token):
            return []
        url = f"{get_settings().github_api_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            data = response.json()
        return data if isinstance(data, list) else []
