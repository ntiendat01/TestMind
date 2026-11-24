"""Tables for the Markdown slice. Trace tables arrive with M4."""

from __future__ import annotations

from datetime import datetime

from app.db.base import Base
from app.schemas.parsed import SourceLocation
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    doc_type: Mapped[str] = mapped_column(String(32))
    module: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DocumentVersionRow(Base):
    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    version: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(32))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ChunkRow(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"))
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    text_for_embedding: Mapped[str] = mapped_column(Text)
    section_path: Mapped[list[str]] = mapped_column(ARRAY(Text))
    loc: Mapped[SourceLocation] = mapped_column(JSON)
    requirement_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    token_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    embedding_model: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean)
    doc_type: Mapped[str] = mapped_column(String(32))
    module: Mapped[str | None] = mapped_column(String(200), nullable=True)


class QueryRow(Base):
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    filters: Mapped[dict[str, object]] = mapped_column(JSON)
    retrieved: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    answer: Mapped[str] = mapped_column(Text)
    insufficient_evidence: Mapped[bool] = mapped_column(Boolean)
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer)
    prompt_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EvalRunRow(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(200))
    split: Mapped[str] = mapped_column(String(32))
    config: Mapped[dict[str, object]] = mapped_column(JSONB)
    git_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB)
    report: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
