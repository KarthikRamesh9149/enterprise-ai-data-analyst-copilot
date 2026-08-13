from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    database_url: str = "sqlite:///./local.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = ""
    allow_insecure_local_demo_secret: bool = False
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    auth_cookie_name: str = "copilot_session"
    auth_cookie_secure: bool = False
    upload_dir: str = "storage/uploads"
    max_upload_size_mb: int = 25
    duckdb_path: str = "storage/duckdb/analytics.duckdb"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    sql_generator_provider: str = "mock"
    report_generator_provider: str = "mock"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0
    max_output_tokens: int = 1200
    mlflow_tracking_uri: str = "sqlite:///storage/mlflow/mlflow.db"
    rate_limit_per_minute: int = 60
    sql_max_rows: int = Field(default=1000, ge=1, le=100_000)
    sql_max_result_bytes: int = Field(default=5_000_000, ge=1024)
    sql_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    sql_memory_limit_mb: int = Field(default=256, ge=32, le=4096)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
