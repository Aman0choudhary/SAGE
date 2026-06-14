from sage.memory.store import InMemoryStore


async def test_memory_store_generates_refs_and_stats():
    store = InMemoryStore()

    memory = await store.save_memory(
        repo="octo/repo",
        title="Do not cache auth tokens",
        content="Auth tokens must not be cached.",
        memory_type="decision",
        risk_level="critical",
    )
    await store.store_pattern("octo/repo", "Never use MD5 for passwords", 3, "alice")
    await store.store_promise("octo/repo", 5, "Use bcrypt cost 12", "bob")

    stats = await store.stats("octo/repo")

    assert memory.memory_ref == "SAGE-MEMORY-001"
    assert stats["total_memories"] == 1
    assert stats["patterns"] == 1
    assert stats["promises"] == 1


async def test_memory_override_marks_record_overridden():
    store = InMemoryStore()
    await store.save_memory(
        repo="octo/repo",
        title="Old decision",
        content="Old content",
        memory_type="decision",
    )

    result = await store.override_memory(
        "octo/repo",
        "SAGE-MEMORY-001",
        "New content",
        "Architecture changed",
    )

    assert result["status"] == "overridden"
    assert store.memories["octo/repo"][0].is_overridden

