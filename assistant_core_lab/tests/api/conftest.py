"""Fixtures for API tests against the Week 3 service."""

from pathlib import Path

import pytest

from assistant_core.config import Settings
from assistant_core.service import create_service

DATA = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def settings() -> Settings:
    return Settings(data_dir=DATA, database_url="sqlite://", session_salt="test-session-salt")


@pytest.fixture
def service(settings: Settings):
    return create_service(settings)
