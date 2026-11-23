"""Process settings loaded from the environment."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas.parsed import ChunkConfig
from app.services.generation.prompt import load_prompt


def discover_config_dir() -> Path:
    override = os.environ.get("CONFIG_DIR")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "config" / "chunking.yaml"
        if candidate.is_file():
            return candidate.parent
    raise FileNotFoundError("config/chunking.yaml was not found")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TestMind API"
    web_origin: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://testmind:testmind@localhost:5432/testmind"
    llm_base_url: str = "https://api.inference.wandb.ai/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-ai/DeepSeek-V4.1-Flash-1017"
    llm_max_tokens: int = 800
    llm_timeout_seconds: float = 60
    embedding_backend: str = "bge-m3"
    embedding_model: str = "BAAI/bge-m3"
    raw_dir: Path = Path("data/raw")
    max_upload_bytes: int = 20 * 1024 * 1024
    retrieval_limit: int = 30
    retrieval_min_similarity: float | None = Field(default=None, ge=-1, le=1)
    context_token_budget: int = 3000

    @field_validator("retrieval_min_similarity", mode="before")
    @classmethod
    def empty_similarity_is_unset(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_chunk_config(config_dir: Path) -> ChunkConfig:
    values: dict[str, int] = {}
    for line in (config_dir / "chunking.yaml").read_text(encoding="utf-8").splitlines():
        body = line.split("#", 1)[0].strip()
        if not body or ":" not in body:
            continue
        key, raw = body.split(":", 1)
        values[key.strip()] = int(raw.strip())
    return ChunkConfig(
        target_tokens=values["target_tokens"],
        max_tokens=values["max_tokens"],
        overlap_tokens=values["overlap_tokens"],
    )


def load_answer_prompt(config_dir: Path) -> tuple[str, str]:
    return load_prompt(config_dir / "prompts" / "answer.vi.md")
