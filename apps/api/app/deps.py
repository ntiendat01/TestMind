"""Dependency providers for routers."""

from app.settings import Settings, get_settings


def provide_settings() -> Settings:
    return get_settings()
