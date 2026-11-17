from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "TaskFlow API"
    app_version: str = "0.3.0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/taskflow"
    sqlite_fallback_url: str = "sqlite+aiosqlite:///./taskflow.db"
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # Caching
    redis_url: str | None = None
    cache_default_ttl_seconds: int = 60

    # File uploads & exports
    upload_dir: str = "uploads"
    export_dir: str = "exports"
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_upload_extensions: list[str] = [
        ".txt",
        ".md",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".csv",
        ".json",
        ".zip",
    ]

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache()
def get_settings() -> Settings:
    return Settings()