"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.container import Container, build_container
from app.core.errors import APIError
from app.core.logging import configure_logging
from app.routers.documents import router as documents_router
from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.query import router as query_router
from app.settings import get_settings


def create_app(container: Container | None = None) -> FastAPI:
    configure_logging()
    settings = get_settings() if container is None else container.settings
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.container = container or build_container(settings)
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(jobs_router)
    app.include_router(query_router)
    app.add_exception_handler(APIError, _api_error)
    return app


def _api_error(_request: Request, exc: Exception) -> JSONResponse:
    error = exc if isinstance(exc, APIError) else APIError(500, "internal", "Internal error.")
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "message": error.message},
    )


app = create_app()
