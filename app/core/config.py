from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    app_name: str = "TaskFlow API"
    app_version: str = "0.2.0"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/taskflow"

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"

    jwt_algorithm: str = "HS256"

    access_token_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()