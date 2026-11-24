"""Ensure eval results survive the temporary corpus workspace and can be retried."""

import os
from uuid import uuid4

import pytest
from app.db.repositories.eval_runs import save_run
from app.db.workspace import migrated_workspace
from sqlalchemy import create_engine, text


def test_history_persists_after_workspace_cleanup() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for evaluation history integration")
    run_id = str(uuid4())
    report: dict[str, object] = {
        "metadata": {"run_id": run_id, "dataset": "fixture", "split": "dev", "git_sha": None},
        "metrics": {"mrr": 0.5},
    }
    with migrated_workspace(database_url):
        assert save_run(database_url, report) == run_id
    assert save_run(database_url, report) == run_id
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(
                text("SELECT report FROM testmind_eval.eval_runs WHERE id = :id"),
                {"id": run_id},
            ).scalar_one()
            assert row == report
            connection.execute(
                text("DELETE FROM testmind_eval.eval_runs WHERE id = :id"),
                {"id": run_id},
            )
    finally:
        engine.dispose()
