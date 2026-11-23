"""Run tests and evaluations in an isolated PostgreSQL schema."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

_API_ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def migrated_workspace(database_url: str) -> Iterator[sessionmaker[Session]]:
    url = make_url(database_url)
    schema = f"testmind_{uuid4().hex}"
    admin = create_engine(url)
    try:
        with admin.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtext('testmind:vector'))"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public"))
            connection.execute(CreateSchema(schema))
        try:
            engine = create_engine(
                url.update_query_dict({"options": f"-csearch_path={schema},public"}),
                pool_pre_ping=True,
            )
            try:
                config = Config(_API_ROOT / "alembic.ini")
                config.set_main_option("script_location", str(_API_ROOT / "migrations"))
                with engine.connect() as connection:
                    config.attributes.update(connection=connection, version_table_schema=schema)
                    upgrade(config, "head")
                yield sessionmaker(bind=engine, expire_on_commit=False)
            finally:
                engine.dispose()
        finally:
            with admin.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        admin.dispose()
