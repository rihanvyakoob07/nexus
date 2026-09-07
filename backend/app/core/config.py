from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "NEXUS"

    database_url: str = "sqlite+aiosqlite:///./nexus.db"

    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # OpenAI-compatible API configuration
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # AI models
    openai_model_reasoning: str = "gpt-4o"
    openai_model_triage: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()