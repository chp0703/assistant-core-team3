"""Shared pytest configuration and isolated Lab 08 fixtures."""

from pathlib import Path

import pytest

from assistant_api.db import Repository, init_db, make_engine
from assistant_core.config import Settings
from assistant_core.service import AssistantService, create_service

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Use absolute project data and per-test fake credentials/database settings."""
    database_file = (tmp_path / "assistant.sqlite").as_posix()
    return Settings(
        data_dir=DATA_DIR,
        kb_dir=DATA_DIR / "kb",
        database_url=f"sqlite:///{database_file}",
        session_salt="lab08-test-session-salt",
        api_admin_key="lab08-fake-admin-key",
        llm_provider="stub",
        rag_enabled=False,
    )


@pytest.fixture
def rag_settings(settings: Settings) -> Settings:
    """Enable RAG only for a test that explicitly requests this fixture."""
    return settings.model_copy(update={"rag_enabled": True, "kb_dir": settings.data_dir / "kb"})


@pytest.fixture
def service(settings: Settings) -> AssistantService:
    """Create a fresh offline service for one test."""
    return create_service(settings)


@pytest.fixture
def rag_service(rag_settings: Settings) -> AssistantService:
    """Create a fresh RAG service with the configured local knowledge base."""
    return create_service(rag_settings)


@pytest.fixture
def isolated_repo(settings: Settings):
    """Create and dispose an independent database engine for one test."""
    engine = make_engine(settings.database_url)
    init_db(engine)
    repository = Repository(engine, settings.session_salt or "")
    try:
        yield repository
    finally:
        engine.dispose()
