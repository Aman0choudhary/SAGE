from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

MemoryType = Literal["decision", "rule", "incident", "incident_lesson", "pattern", "promise"]
RiskLevel = Literal["low", "medium", "high", "critical"]
PromiseStatus = Literal["pending", "kept", "broken", "overridden"]


class MemoryRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    repo_full_name: str
    memory_ref: str
    memory_type: MemoryType
    title: str
    content: str
    vector_store_file_id: str | None = None
    source_type: str = "manual"
    source_id: int | None = None
    source_url: str | None = None
    author_github: str | None = None
    files_affected: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    risk_level: RiskLevel | None = None
    is_overridden: bool = False
    overridden_by: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatternRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    repo_full_name: str
    pattern_ref: str
    rule: str
    source_pr: int | None = None
    stated_by: str | None = None
    is_active: bool = True
    violation_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromiseRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    repo_full_name: str
    issue_number: int
    promise: str
    made_by: str | None = None
    pr_number: int | None = None
    status: PromiseStatus = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LedgerEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    repo_full_name: str
    commit_sha: str
    author: str
    files_changed: list[str] = Field(default_factory=list)
    domains_touched: list[str] = Field(default_factory=list)
    breaking_risk: Literal["low", "medium", "high"] | None = None
    committed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

