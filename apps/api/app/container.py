"""Wires the Markdown slice. Tests pass their own container."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.chunking.tokens import ApproximateTokenCounter
from app.clients.embedder import BgeM3Embedder, HashEmbedder
from app.clients.llm import InferenceLLMClient
from app.core.interfaces import DocumentStore, Embedder, LLMClient, TokenCounter
from app.db.repositories.documents import PostgresDocumentStore
from app.db.session import make_session_factory
from app.schemas.parsed import ChunkConfig
from app.settings import Settings, discover_config_dir, load_answer_prompt, load_chunk_config


@dataclass
class Container:
    settings: Settings
    store: DocumentStore
    embedder: Embedder
    llm: LLMClient
    counter: TokenCounter
    chunk_config: ChunkConfig
    prompt_version: str
    prompt_text: str
    raw_dir: Path


def build_container(settings: Settings | None = None) -> Container:
    current = settings or Settings()
    config_dir = discover_config_dir()
    version, prompt = load_answer_prompt(config_dir)
    return Container(
        settings=current,
        store=PostgresDocumentStore(make_session_factory(current.database_url)),
        embedder=_embedder(current),
        llm=InferenceLLMClient(
            base_url=current.llm_base_url,
            api_key=current.llm_api_key,
            model=current.llm_model,
            max_tokens=current.llm_max_tokens,
            timeout=current.llm_timeout_seconds,
        ),
        counter=ApproximateTokenCounter(),
        chunk_config=load_chunk_config(config_dir),
        prompt_version=version,
        prompt_text=prompt,
        raw_dir=current.raw_dir,
    )


def _embedder(settings: Settings) -> Embedder:
    if settings.embedding_backend == "hash":
        return HashEmbedder()
    return BgeM3Embedder(settings.embedding_model)
