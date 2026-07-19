from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODOROCO_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./modoroco.db"
    bootstrap_api_key: SecretStr | None = None
    bootstrap_tenant_id: str = "01807ad0-0000-7000-8000-000000000001"
    bootstrap_client_id: str = "01807ad0-0000-7000-8000-000000000002"
    worker_poll_seconds: float = 1.0
    worker_batch_size: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
