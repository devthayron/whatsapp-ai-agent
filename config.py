from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Variáveis exigidas por provedor de mensagens
PROVIDER_REQUIRED = {
    "evolution": [
        "API_KEY_EVO",
        "BASE_URL",
        "INSTANCE",
        "WEBHOOK_URL",
        "WEBHOOK_SECRET",
    ],
    "meta": [
        "META_ACCESS_TOKEN",
        "META_PHONE_NUMBER_ID",
        "META_APP_SECRET",
        "META_VERIFY_TOKEN",
    ],
}


class Settings(BaseSettings):
    SECRET_KEY: str

    OPENAI_API_KEY: str

    DATABASE_URL: str

    MESSAGING_PROVIDER: str = "meta"

    # Evolution (obrigatórias só com MESSAGING_PROVIDER=evolution)
    API_KEY_EVO: str | None = None
    BASE_URL: str | None = None
    INSTANCE: str | None = None
    WEBHOOK_URL: str | None = None
    WEBHOOK_SECRET: str | None = None

    # Meta / WhatsApp Cloud API (obrigatórias só com MESSAGING_PROVIDER=meta)
    META_ACCESS_TOKEN: str | None = None
    META_PHONE_NUMBER_ID: str | None = None
    META_APP_SECRET: str | None = None
    META_VERIFY_TOKEN: str | None = None
    META_API_VERSION: str = "v23.0"

    AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-5.4-nano"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie do refresh token
    COOKIE_SECURE: bool = False  # True em produção (HTTPS)
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: str | None = None

    # Origens do front permitidas (separadas por vírgula)
    CORS_ORIGINS: str = "http://localhost:3000"

    LOG_LEVEL: str = "DEBUG"

    REDIS_URL: str = "redis://localhost:6379/0"

    DEBOUNCE_SECONDS: int = 7
    DEBOUNCE_LEASE_SECONDS: int = 120
    DEBOUNCE_RETRY_SECONDS: int = 15
    DEBOUNCE_MAX_ATTEMPTS: int = 3
    WORKER_IN_API: bool = True
    WORKER_CONCURRENCY: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _check_cookie_settings(self):
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SAMESITE=none exige COOKIE_SECURE=true")
        return self

    @model_validator(mode="after")
    def _check_provider_settings(self):
        required = PROVIDER_REQUIRED.get(self.MESSAGING_PROVIDER)

        if required is None:
            raise ValueError(
                f"MESSAGING_PROVIDER inválido: {self.MESSAGING_PROVIDER} "
                f"(use {', '.join(PROVIDER_REQUIRED)})"
            )

        missing = [name for name in required if not getattr(self, name)]

        if missing:
            raise ValueError(
                f"MESSAGING_PROVIDER={self.MESSAGING_PROVIDER} exige: "
                f"{', '.join(missing)}"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
