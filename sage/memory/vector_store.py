from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI

from sage.config import get_settings


def memory_document(
    memory_ref: str,
    title: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    metadata = metadata or {}
    lines = [
        memory_ref,
        f"TYPE: {metadata.get('memory_type', metadata.get('type', 'decision'))}",
        f"DATE: {metadata.get('date', datetime.now(timezone.utc).date().isoformat())}",
        f"AUTHOR: {metadata.get('author', metadata.get('author_github', 'unknown'))}",
        f"SOURCE: {metadata.get('source', metadata.get('source_pr', 'manual'))}",
        f"DOMAINS: {', '.join(metadata.get('domains') or [])}",
        f"FILES: {', '.join(metadata.get('files_affected') or [])}",
        f"RISK: {metadata.get('risk_level', 'unknown')}",
        "",
        "TITLE:",
        title,
        "",
        "DECISION:",
        content,
    ]
    return "\n".join(lines).strip() + "\n"


class OpenAIVectorStore:
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        settings = get_settings()
        self.client = client or AsyncOpenAI(api_key=settings.openai_api_key)

    async def create_repo_vector_store(self, repo_full_name: str) -> str:
        name = f"sage-{repo_full_name.replace('/', '-')}"
        vector_store = await self.client.vector_stores.create(
            name=name,
            expires_after={"anchor": "last_active_at", "days": 365},
        )
        return vector_store.id

    async def upload_memory(
        self,
        vector_store_id: str,
        memory_ref: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        document = memory_document(memory_ref, title, content, metadata)
        filename = f"{memory_ref.lower()}.txt"
        uploaded_file = await self.client.files.create(
            file=(filename, document.encode("utf-8"), "text/plain"),
            purpose="assistants",
        )
        await self.client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=uploaded_file.id,
        )
        return uploaded_file.id

