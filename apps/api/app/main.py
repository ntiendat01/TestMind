"""FastAPI application factory."""

from fastapi import FastAPI

from app.core.logging import configure_logging
from app.routers.health import router as health_router
from app.settings import get_settings


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    return app


app = create_app()
