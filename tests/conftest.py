from __future__ import annotations

import pytest

from sage.memory.store import InMemoryStore, set_memory_store


@pytest.fixture(autouse=True)
def isolate_external_services(monkeypatch):
    """Keep tests offline even when a developer has a real .env file."""
    monkeypatch.setenv("SAGE_TESTING", "1")
    for key in (
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "GITHUB_APP_PRIVATE_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
    ):
        monkeypatch.setenv(key, "")
    set_memory_store(InMemoryStore())
    yield
    set_memory_store(None)
