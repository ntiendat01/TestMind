"""Persist evaluation run provenance and measured metrics."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002_eval_runs"
down_revision = "0001_markdown"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset", sa.String(200), nullable=False),
        sa.Column("split", sa.String(32), nullable=False),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column("git_sha", sa.String(40), nullable=True),
        sa.Column("metrics", JSONB(), nullable=False),
        sa.Column("report", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("eval_runs")
