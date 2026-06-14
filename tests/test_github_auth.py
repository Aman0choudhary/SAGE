from sage.github.auth import installation_id_from_payload, load_private_key


def test_installation_id_from_payload():
    assert installation_id_from_payload({"installation": {"id": 123}}) == 123


def test_installation_id_from_payload_missing():
    assert installation_id_from_payload({}) is None


def test_load_private_key_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "line1\\nline2")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)

    assert load_private_key() == "line1\nline2"

