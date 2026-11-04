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

@lru_cache()
def get_settings() -> Settings:
    return Settings()