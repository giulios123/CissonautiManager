from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (and `.env` in development)."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    app_base_url: str = "http://localhost:5173"
    secret_key: str = "change-me-with-a-long-random-string"

    admin_email: str | None = None
    admin_password: str | None = None

    database_url: str = "sqlite:///./cisonauti-dev.db"

    email_provider: str = "console"
    email_from: str = "noreply@example.com"
    acs_connection_string: str | None = None

    # Directory with the built frontend. Served by the backend when it exists.
    static_dir: str = Field(default="static")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cookie_secure(self) -> bool:
        """Session cookies are Secure whenever the app is served over https."""
        return self.app_base_url.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
