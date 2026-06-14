from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from supabase import Client, create_client

from sage.config import get_settings
from sage.memory.models import LedgerEntry, MemoryRecord, PatternRecord, PromiseRecord


def _next_ref(prefix: str, value: int) -> str:
    return f"{prefix}-{value:03d}"


@dataclass
class InMemoryStore:
    memory_counter: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    pattern_counter: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    vector_store_ids: dict[str, str] = field(default_factory=dict)
    memories: dict[str, list[MemoryRecord]] = field(default_factory=lambda: defaultdict(list))
    patterns: dict[str, list[PatternRecord]] = field(default_factory=lambda: defaultdict(list))
    promises: dict[str, list[PromiseRecord]] = field(default_factory=lambda: defaultdict(list))
    ledger: dict[str, list[LedgerEntry]] = field(default_factory=lambda: defaultdict(list))

    async def get_vector_store_id(self, repo: str) -> str | None:
        return self.vector_store_ids.get(repo)

    async def set_vector_store_id(self, repo: str, vector_store_id: str) -> None:
        self.vector_store_ids[repo] = vector_store_id

    async def save_memory(
        self,
        repo: str,
        title: str,
        content: str,
        memory_type: str,
        vector_store_file_id: str | None = None,
        author: str | None = None,
        files_affected: list[str] | None = None,
        domains: list[str] | None = None,
        risk_level: str | None = None,
        source_pr: int | None = None,
        source_type: str = "pr",
        **_: Any,
    ) -> MemoryRecord:
        self.memory_counter[repo] += 1
        record = MemoryRecord(
            repo_full_name=repo,
            memory_ref=_next_ref("SAGE-MEMORY", self.memory_counter[repo]),
            memory_type=memory_type,
            title=title,
            content=content,
            vector_store_file_id=vector_store_file_id,
            source_type=source_type,
            source_id=source_pr,
            author_github=author,
            files_affected=files_affected or [],
            domains=domains or [],
            risk_level=risk_level,
        )
        self.memories[repo].append(record)
        return record

    async def override_memory(
        self,
        repo: str,
        memory_ref: str,
        new_content: str,
        override_reason: str,
        overridden_by: str | None = None,
    ) -> dict[str, Any]:
        for record in self.memories[repo]:
            if record.memory_ref == memory_ref:
                record.is_overridden = True
                return {
                    "status": "overridden",
                    "memory_ref": memory_ref,
                    "override_reason": override_reason,
                    "overridden_by": overridden_by,
                    "new_content": new_content,
                }
        return {"status": "not_found", "memory_ref": memory_ref}

    async def set_memory_vector_file_id(
        self,
        repo: str,
        memory_ref: str,
        vector_store_file_id: str,
    ) -> None:
        for record in self.memories[repo]:
            if record.memory_ref == memory_ref:
                record.vector_store_file_id = vector_store_file_id
                return

    async def store_pattern(
        self,
        repo: str,
        rule: str,
        source_pr: int | None = None,
        stated_by: str | None = None,
    ) -> PatternRecord:
        self.pattern_counter[repo] += 1
        record = PatternRecord(
            repo_full_name=repo,
            pattern_ref=_next_ref("SAGE-PATTERN", self.pattern_counter[repo]),
            rule=rule,
            source_pr=source_pr,
            stated_by=stated_by,
        )
        self.patterns[repo].append(record)
        return record

    async def get_active_patterns(self, repo: str) -> list[PatternRecord]:
        return [pattern for pattern in self.patterns[repo] if pattern.is_active]

    async def get_all_patterns(self, repo: str) -> list[PatternRecord]:
        return list(self.patterns[repo])

    async def store_promise(
        self,
        repo: str,
        issue_number: int,
        promise: str,
        made_by: str | None = None,
    ) -> PromiseRecord:
        record = PromiseRecord(
            repo_full_name=repo,
            issue_number=issue_number,
            promise=promise,
            made_by=made_by,
        )
        self.promises[repo].append(record)
        return record

    async def get_promises(self, repo: str, issue_number: int) -> list[PromiseRecord]:
        return [
            promise
            for promise in self.promises[repo]
            if promise.issue_number == issue_number
        ]

    async def update_promise_status(
        self,
        repo: str,
        issue_number: int,
        promise: str,
        status: str,
    ) -> dict[str, Any]:
        for record in self.promises[repo]:
            if record.issue_number == issue_number and record.promise == promise:
                record.status = status
                return {"status": "updated", "promise": promise}
        return {"status": "not_found", "promise": promise}

    async def store_ledger_entry(self, repo: str, **kwargs: Any) -> LedgerEntry:
        record = LedgerEntry(repo_full_name=repo, **kwargs)
        self.ledger[repo].append(record)
        return record

    async def increment_counter(self, repo: str, counter: str) -> int:
        if counter == "memory_counter":
            self.memory_counter[repo] += 1
            return self.memory_counter[repo]
        if counter == "pattern_counter":
            self.pattern_counter[repo] += 1
            return self.pattern_counter[repo]
        raise ValueError(f"Unknown counter: {counter}")

    async def stats(self, repo: str) -> dict[str, Any]:
        promises = self.promises[repo]
        kept = len([promise for promise in promises if promise.status == "kept"])
        broken = len([promise for promise in promises if promise.status == "broken"])
        return {
            "repo": repo,
            "total_memories": len(self.memories[repo]),
            "patterns": len(self.patterns[repo]),
            "promises": len(promises),
            "promises_kept": kept,
            "promises_broken": broken,
            "ledger_entries": len(self.ledger[repo]),
            "vector_store_id": self.vector_store_ids.get(repo),
        }


class SupabaseStore(InMemoryStore):
    """Supabase-backed metadata store with in-memory mirrors for fast local reads."""

    def __init__(self, client: Client | None = None) -> None:
        super().__init__()
        settings = get_settings()
        self.client = client or create_client(settings.supabase_url, settings.supabase_service_key)

    async def get_vector_store_id(self, repo: str) -> str | None:
        cached = await super().get_vector_store_id(repo)
        if cached:
            return cached
        rows = self._select("repo_config", repo_full_name=repo)
        if not rows:
            return None
        vector_store_id = rows[0].get("openai_vector_store_id")
        if vector_store_id:
            await super().set_vector_store_id(repo, vector_store_id)
        return vector_store_id

    async def set_vector_store_id(self, repo: str, vector_store_id: str) -> None:
        await super().set_vector_store_id(repo, vector_store_id)
        row = self._repo_config(repo)
        if row:
            self.client.table("repo_config").update(
                {"openai_vector_store_id": vector_store_id}
            ).eq("repo_full_name", repo).execute()
        else:
            self.client.table("repo_config").insert(
                {
                    "repo_full_name": repo,
                    "openai_vector_store_id": vector_store_id,
                    "memory_counter": self.memory_counter[repo],
                    "pattern_counter": self.pattern_counter[repo],
                }
            ).execute()

    async def increment_counter(self, repo: str, counter: str) -> int:
        if counter not in {"memory_counter", "pattern_counter"}:
            raise ValueError(f"Unknown counter: {counter}")
        row = self._ensure_repo_config(repo)
        value = int(row.get(counter) or 0) + 1
        self.client.table("repo_config").update({counter: value}).eq(
            "repo_full_name", repo
        ).execute()
        if counter == "memory_counter":
            self.memory_counter[repo] = value
        else:
            self.pattern_counter[repo] = value
        return value

    async def save_memory(self, repo: str, **kwargs: Any) -> MemoryRecord:
        counter = await self.increment_counter(repo, "memory_counter")
        record = MemoryRecord(
            repo_full_name=repo,
            memory_ref=_next_ref("SAGE-MEMORY", counter),
            memory_type=kwargs["memory_type"],
            title=kwargs["title"],
            content=kwargs["content"],
            vector_store_file_id=kwargs.get("vector_store_file_id"),
            source_type=kwargs.get("source_type", "pr"),
            source_id=kwargs.get("source_pr"),
            source_url=kwargs.get("source_url"),
            author_github=kwargs.get("author"),
            files_affected=kwargs.get("files_affected") or [],
            domains=kwargs.get("domains") or [],
            risk_level=kwargs.get("risk_level"),
        )
        self.memories[repo].append(record)
        self.client.table("memories").insert(
            {
                "id": str(record.id),
                "repo_full_name": record.repo_full_name,
                "memory_ref": record.memory_ref,
                "memory_type": record.memory_type,
                "title": record.title,
                "vector_store_file_id": record.vector_store_file_id,
                "source_type": record.source_type,
                "source_id": record.source_id,
                "author_github": record.author_github,
                "files_affected": record.files_affected,
                "domains": record.domains,
                "risk_level": record.risk_level,
                "is_overridden": record.is_overridden,
            }
        ).execute()
        return record

    async def set_memory_vector_file_id(
        self,
        repo: str,
        memory_ref: str,
        vector_store_file_id: str,
    ) -> None:
        await super().set_memory_vector_file_id(repo, memory_ref, vector_store_file_id)
        self.client.table("memories").update(
            {"vector_store_file_id": vector_store_file_id}
        ).eq("repo_full_name", repo).eq("memory_ref", memory_ref).execute()

    async def override_memory(
        self,
        repo: str,
        memory_ref: str,
        new_content: str,
        override_reason: str,
        overridden_by: str | None = None,
    ) -> dict[str, Any]:
        result = await super().override_memory(
            repo,
            memory_ref,
            new_content,
            override_reason,
            overridden_by,
        )
        self.client.table("memories").update({"is_overridden": True}).eq(
            "repo_full_name", repo
        ).eq("memory_ref", memory_ref).execute()
        return result

    async def store_pattern(
        self,
        repo: str,
        rule: str,
        source_pr: int | None = None,
        stated_by: str | None = None,
    ) -> PatternRecord:
        counter = await self.increment_counter(repo, "pattern_counter")
        record = PatternRecord(
            repo_full_name=repo,
            pattern_ref=_next_ref("SAGE-PATTERN", counter),
            rule=rule,
            source_pr=source_pr,
            stated_by=stated_by,
        )
        self.patterns[repo].append(record)
        self.client.table("patterns").insert(record.model_dump(mode="json")).execute()
        return record

    async def get_active_patterns(self, repo: str) -> list[PatternRecord]:
        rows = self.client.table("patterns").select("*").eq("repo_full_name", repo).eq(
            "is_active", True
        ).execute().data
        if rows:
            return [PatternRecord(**row) for row in rows]
        return await super().get_active_patterns(repo)

    async def get_all_patterns(self, repo: str) -> list[PatternRecord]:
        rows = self._select("patterns", repo_full_name=repo)
        if rows:
            return [PatternRecord(**row) for row in rows]
        return await super().get_all_patterns(repo)

    async def store_promise(
        self,
        repo: str,
        issue_number: int,
        promise: str,
        made_by: str | None = None,
    ) -> PromiseRecord:
        record = await super().store_promise(repo, issue_number, promise, made_by)
        self.client.table("promises").insert(record.model_dump(mode="json")).execute()
        return record

    async def get_promises(self, repo: str, issue_number: int) -> list[PromiseRecord]:
        rows = self.client.table("promises").select("*").eq("repo_full_name", repo).eq(
            "issue_number", issue_number
        ).execute().data
        if rows:
            return [PromiseRecord(**row) for row in rows]
        return await super().get_promises(repo, issue_number)

    async def update_promise_status(
        self,
        repo: str,
        issue_number: int,
        promise: str,
        status: str,
    ) -> dict[str, Any]:
        result = await super().update_promise_status(repo, issue_number, promise, status)
        self.client.table("promises").update({"status": status}).eq(
            "repo_full_name", repo
        ).eq("issue_number", issue_number).eq("promise", promise).execute()
        return result

    async def store_ledger_entry(self, repo: str, **kwargs: Any) -> LedgerEntry:
        record = await super().store_ledger_entry(repo, **kwargs)
        self.client.table("commit_ledger").insert(record.model_dump(mode="json")).execute()
        return record

    async def stats(self, repo: str) -> dict[str, Any]:
        memories = self._select("memories", repo_full_name=repo)
        patterns = self._select("patterns", repo_full_name=repo)
        promises = self._select("promises", repo_full_name=repo)
        ledger = self._select("commit_ledger", repo_full_name=repo)
        vector_store_id = await self.get_vector_store_id(repo)
        return {
            "repo": repo,
            "total_memories": len(memories),
            "patterns": len(patterns),
            "promises": len(promises),
            "promises_kept": len([item for item in promises if item.get("status") == "kept"]),
            "promises_broken": len([item for item in promises if item.get("status") == "broken"]),
            "ledger_entries": len(ledger),
            "vector_store_id": vector_store_id,
        }

    def _select(self, table: str, **equals: Any) -> list[dict[str, Any]]:
        query = self.client.table(table).select("*")
        for key, value in equals.items():
            query = query.eq(key, value)
        response = query.execute()
        return response.data or []

    def _repo_config(self, repo: str) -> dict[str, Any] | None:
        rows = self._select("repo_config", repo_full_name=repo)
        return rows[0] if rows else None

    def _ensure_repo_config(self, repo: str) -> dict[str, Any]:
        row = self._repo_config(repo)
        if row:
            return row
        self.client.table("repo_config").insert(
            {
                "repo_full_name": repo,
                "memory_counter": self.memory_counter[repo],
                "pattern_counter": self.pattern_counter[repo],
            }
        ).execute()
        return self._repo_config(repo) or {
            "repo_full_name": repo,
            "memory_counter": 0,
            "pattern_counter": 0,
        }


_store: InMemoryStore | None = None


def get_memory_store() -> InMemoryStore:
    global _store
    if _store is not None:
        return _store

    settings = get_settings()
    if settings.has_supabase:
        _store = SupabaseStore()
    else:
        _store = InMemoryStore()
    return _store


def set_memory_store(store: InMemoryStore | None) -> None:
    global _store
    _store = store
