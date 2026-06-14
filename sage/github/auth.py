from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import jwt

from sage.config import get_settings


def generate_app_jwt(app_id: str, private_key_pem: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iat": int((now - timedelta(seconds=30)).timestamp()),
        "exp": int((now + timedelta(minutes=9)).timestamp()),
        "iss": app_id,
    }
    return jwt.encode(payload, private_key_pem, algorithm="RS256")


def load_private_key() -> str | None:
    settings = get_settings()
    if settings.github_app_private_key:
        return settings.github_app_private_key.replace("\\n", "\n")
    if not settings.github_app_private_key_path:
        return None
    path = Path(settings.github_app_private_key_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def installation_id_from_payload(payload: dict[str, Any]) -> int | None:
    installation = payload.get("installation") or {}
    installation_id = installation.get("id")
    return int(installation_id) if installation_id else None


@dataclass
class CachedInstallationToken:
    token: str
    expires_at: datetime

    def is_valid(self) -> bool:
        return self.expires_at > datetime.now(timezone.utc) + timedelta(minutes=2)


class GitHubAppAuth:
    def __init__(self) -> None:
        self._cache: dict[int, CachedInstallationToken] = {}

    async def get_installation_token(self, installation_id: int) -> str | None:
        cached = self._cache.get(installation_id)
        if cached and cached.is_valid():
            return cached.token

        settings = get_settings()
        private_key = load_private_key()
        if not settings.github_app_id or not private_key:
            return None

        app_jwt = generate_app_jwt(settings.github_app_id, private_key)
        url = f"{settings.github_api_url}/app/installations/{installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        token = data["token"]
        self._cache[installation_id] = CachedInstallationToken(token=token, expires_at=expires_at)
        return token


github_app_auth = GitHubAppAuth()


async def token_for_payload(payload: dict[str, Any]) -> str | None:
    settings = get_settings()
    installation_id = installation_id_from_payload(payload)
    if installation_id and settings.has_github_app_auth:
        try:
            token = await github_app_auth.get_installation_token(installation_id)
        except Exception:
            token = None
        if token:
            return token
    return settings.github_token
