"""Markdown slice tables.

Revision ID: 0001_markdown
Revises:
Create Date: 2026-11-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001_markdown"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("module", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "document_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=36),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "chunks",
        sa.Column("id", sa.String(length=40), primary_key=True),
        sa.Column(
            "version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_for_embedding", sa.Text(), nullable=False),
        sa.Column("section_path", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("loc", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("requirement_ids", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=False),
        sa.Column("embedding_model", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("module", sa.String(length=200), nullable=True),
    )
    op.create_index("chunks_version_ordinal", "chunks", ["version_id", "ordinal"])
    op.create_index(
        "chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "chunks_requirement_ids_gin",
        "chunks",
        ["requirement_ids"],
        postgresql_using="gin",
    )
    op.create_table(
        "queries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("filters", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("retrieved", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("insufficient_evidence", sa.Boolean(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("queries")
    op.drop_index("chunks_requirement_ids_gin", table_name="chunks")
    op.drop_index("chunks_embedding_hnsw", table_name="chunks")
    op.drop_index("chunks_version_ordinal", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("document_versions")
    op.drop_table("documents")
