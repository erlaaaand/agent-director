from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    OLLAMA_GEN_MODEL: str = Field(default="llama3:latest")
    OLLAMA_EVAL_MODEL: str = Field(default="qwen2.5:7b")

    INPUT_DATA_PATH: str = Field(default="data/input")
    OUTPUT_DATA_PATH: str = Field(default="data/output")

    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_TIMEOUT: float = Field(default=180.0, ge=10.0)
    OLLAMA_RETRIES: int = Field(default=2, ge=1, le=5)

    LOG_LEVEL: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()