# syntax=docker/dockerfile:1
# The maturin stage that builds tm-core is added in M3.
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /bin/

WORKDIR /srv
COPY apps/api/pyproject.toml apps/api/uv.lock ./
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,id=testmind-api-uv,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --extra bge
COPY apps/api/app ./app
COPY apps/api/migrations ./migrations
COPY apps/api/alembic.ini ./alembic.ini
COPY config ./config
ENV CONFIG_DIR=/srv/config
ENV RAW_DIR=/srv/data/raw
EXPOSE 8000
CMD ["sh", "-c", ".venv/bin/alembic upgrade head && exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"]
