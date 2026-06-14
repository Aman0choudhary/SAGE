import hashlib
import hmac

from sage.github.webhooks import validate_github_signature


def test_validate_github_signature_accepts_valid_hmac():
    payload = b'{"ok": true}'
    secret = "top-secret"
    signature = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    assert validate_github_signature(payload, signature, secret)


def test_validate_github_signature_rejects_missing_secret():
    assert not validate_github_signature(b"{}", "sha256=abc", None)


def test_validate_github_signature_rejects_bad_hmac():
    assert not validate_github_signature(b"{}", "sha256=bad", "top-secret")

