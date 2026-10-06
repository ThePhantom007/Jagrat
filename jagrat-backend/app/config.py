from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Jagrat API"
    environment: str = "development"
    database_url: str = "sqlite:///./mentor.db"
    gemini_api_key: str = ""
    # Both defaults are available on the Gemini Developer API's standard free tier.
    gemini_model: str = "gemini-3.8-flash"
    gemini_fast_model: str = "gemini-3.1-flash-lite"
    gemini_timeout_seconds: int = 60
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000", "http://localhost:5173"]
    demo_user_id: str = "demo"
    max_conversation_messages: int = 12
    journal_memory_limit: int = 5
    teaching_candidate_limit: int = 7
    max_candidate_excerpt_chars: int = 1800
    seed_demo_on_startup: bool = False
    auto_ingest_teachings: bool = True
    teachings_json_path: str = "data/articles.json"
    demo_mode: bool = False
    allow_legacy_profile_id: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [x.strip() for x in value.split(",") if x.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
