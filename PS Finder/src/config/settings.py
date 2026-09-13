from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    APP_NAME: str = "Problem & Challenge Discovery Agent"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Groq (Primary - fastest inference)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_EXPLAIN_MODEL: str = "openai/gpt-oss-120b"
    GROQ_MAX_TOKENS: int = 1500
    # gpt-oss / qwen served on Groq are reasoning models. "hidden" strips the
    # chain-of-thought and returns only the final answer in message content.
    GROQ_REASONING_FORMAT: str = "hidden"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EXPLAIN_MODEL: str = "gpt-4o-mini"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EXPLAIN_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ps_finder"
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "./data/ps_finder.db"
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # Scheduling
    DAILY_DISCOVERY_ENABLED: bool = True
    DAILY_MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL_HOURS: int = 24
    DISCOVERY_INTERVAL_HOURS: int = 24

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Rate Limiting & Safety
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    MAX_PAGE_CHUNKS: int = 50


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Ensure data directory exists if using SQLite/Chroma
    Path("./data").mkdir(parents=True, exist_ok=True)
    return settings
