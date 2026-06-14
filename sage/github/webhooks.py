from __future__ import annotations

import hashlib
import hmac


def validate_github_signature(
    payload: bytes,
    signature_header: str | None,
    webhook_secret: str | None,
) -> bool:
    if not webhook_secret or not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def repo_full_name(payload: dict) -> str:
    repo = payload.get("repository") or {}
    full_name = repo.get("full_name")
    if not full_name:
        raise ValueError("GitHub webhook payload is missing repository.full_name")
    return full_name

