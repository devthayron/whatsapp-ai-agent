from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_KEY_EVO: str
    BASE_URL: str
    INSTANCE: str
    WEBHOOK_URL: str
    WEBHOOK_SECRET: str

    SECRET_KEY: str

    OPENAI_API_KEY: str

    DATABASE_URL: str

    AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-5.4-nano"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    LOG_LEVEL: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
