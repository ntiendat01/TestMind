"""Dependency provider tests."""

from app.deps import provide_settings


def test_default_app_name() -> None:
    assert provide_settings().app_name == "TestMind API"
