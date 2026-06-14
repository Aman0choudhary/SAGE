from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from github import Github

from sage.config import get_settings


@dataclass
class GitHubComments:
    token: str | None = None

    def _client(self, token: str | None = None) -> Github | None:
        token = token or self.token or get_settings().github_token
        if not token:
            return None
        return Github(token)

    async def post(
        self,
        repo: str,
        number: int,
        body: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        client = self._client(token)
        if client is None:
            return {"status": "dry_run", "repo": repo, "number": number, "body": body}
        issue = client.get_repo(repo).get_issue(number=number)
        comment = issue.create_comment(body)
        return {"status": "posted", "url": comment.html_url}

    async def add_label(
        self,
        repo: str,
        number: int,
        label: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        client = self._client(token)
        if client is None:
            return {"status": "dry_run", "repo": repo, "number": number, "label": label}
        issue = client.get_repo(repo).get_issue(number=number)
        issue.add_to_labels(label)
        return {"status": "labeled", "label": label}

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        client = self._client(token)
        if client is None:
            return {"status": "dry_run", "repo": repo, "title": title, "body": body}
        issue = client.get_repo(repo).create_issue(title=title, body=body)
        return {"status": "created", "number": issue.number, "url": issue.html_url}


github_comments = GitHubComments()
