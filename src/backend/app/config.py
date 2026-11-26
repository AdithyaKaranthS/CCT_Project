import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_invoice_storage_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return str(Path(base) / "Warrantly" / "invoices")
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return str(Path(base) / "warrantly" / "invoices")


class Settings(BaseSettings):
    firebase_project_id: str | None = None
    google_application_credentials: str | None = None
    storage_signing_service_account: str | None = None
    allowed_origins: str = "http://localhost:5173"
    scheduler_secret: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    max_invoice_bytes: int = 10 * 1024 * 1024
    local_invoice_storage_dir: str = Field(default_factory=_default_invoice_storage_dir)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
