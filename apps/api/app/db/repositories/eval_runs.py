"""Persist evaluation history independently of temporary corpus schemas."""

import json
from datetime import UTC, datetime
from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config
from app.db.models import EvalRunRow
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

_API_ROOT = Path(__file__).resolve().parents[3]


def save_run(database_url: str, report: dict[str, object]) -> str:
    metadata = report["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError("Report metadata must be an object.")
    run_id = str(metadata["run_id"])
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext('testmind:eval-history'))")
            )
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS testmind_eval"))
            connection.execute(text("SET LOCAL search_path TO testmind_eval, public"))
            config = Config(_API_ROOT / "alembic.ini")
            config.set_main_option("script_location", str(_API_ROOT / "migrations"))
            config.attributes.update(connection=connection, version_table_schema="testmind_eval")
            upgrade(config, "head")
            with Session(bind=connection) as session:
                session.merge(
                    EvalRunRow(
                        id=run_id,
                        dataset=str(metadata["dataset"]),
                        split=str(metadata["split"]),
                        config=metadata,
                        git_sha=metadata.get("git_sha"),
                        metrics=json.loads(json.dumps(report["metrics"])),
                        report=json.loads(json.dumps(report)),
                        created_at=datetime.now(UTC),
                    )
                )
                session.flush()
    finally:
        engine.dispose()
    return run_id
