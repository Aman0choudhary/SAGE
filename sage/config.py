from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    model: str
    github_app_id: str | None
    github_app_private_key: str | None
    github_app_private_key_path: str | None
    github_webhook_secret: str | None
    github_token: str | None
    github_api_url: str
    supabase_url: str | None
    supabase_service_key: str | None
    port: int
    environment: str
    max_diff_chars: int

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_github_app_auth(self) -> bool:
        return bool(
            self.github_app_id
            and (self.github_app_private_key or self.github_app_private_key_path)
        )


def get_settings() -> Settings:
    if os.getenv("SAGE_TESTING") != "1":
        load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("MODEL", "gpt-5.5"),
        github_app_id=os.getenv("GITHUB_APP_ID"),
        github_app_private_key=os.getenv("GITHUB_APP_PRIVATE_KEY"),
        github_app_private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"),
        github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
        github_token=os.getenv("GITHUB_TOKEN"),
        github_api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY"),
        port=int(os.getenv("PORT", "8000")),
        environment=os.getenv("ENVIRONMENT", "development"),
        max_diff_chars=int(os.getenv("MAX_DIFF_CHARS", "80000")),
    )
