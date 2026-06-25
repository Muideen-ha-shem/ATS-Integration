from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./ats_integration.db", env="DATABASE_URL")
    workable_api_token: str | None = Field(default=None, env="WORKABLE_API_TOKEN")
    app_env: str = Field(default="production", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_sample_data: bool = Field(default=False, env="ENABLE_SAMPLE_DATA")

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
