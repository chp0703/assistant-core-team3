"""Focused tests for the Lab 5 database foundation."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from assistant_api.db import ChatSession, Feedback, Interaction, Repository, hash_session, init_db, make_engine
from assistant_api.main import create_app
from assistant_core.config import Settings


def make_repository() -> tuple[Repository, object]:
    engine = make_engine("sqlite://")
    init_db(engine)
    return Repository(engine, "test-salt"), engine


def test_hash_is_deterministic_and_never_contains_the_raw_value() -> None:
    hashed = hash_session("student-42", "test-salt")
    assert hashed == hash_session("student-42", "test-salt")
    assert hashed != hash_session("student-43", "test-salt")
    assert len(hashed) == 16
    assert "student-42" not in hashed


def test_hash_and_repository_reject_a_missing_salt() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        hash_session("student-42", "")
    with pytest.raises(ValueError, match="non-empty"):
        Repository(make_engine("sqlite://"), "")


def test_session_identifier_model_columns_are_compatible() -> None:
    assert ChatSession.__table__.c.id.type.length == 16
    assert Interaction.__table__.c.session_id.type.length == 16
    foreign_keys = list(Interaction.__table__.c.session_id.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "chat_session.id"


def test_application_rejects_missing_session_salt_before_initializing_database() -> None:
    with pytest.raises(ValueError, match="SESSION_SALT"):
        create_app(Settings(), service=object(), weather=object())


def test_record_interaction_hashes_and_reuses_the_session() -> None:
    repository, engine = make_repository()
    for request_id in ("request-1", "request-2"):
        repository.record_interaction("student-42", request_id, "rule", "H26-5.3", True, False, 12.5)

    with Session(engine) as db:
        sessions = db.exec(select(ChatSession)).all()
        interactions = db.exec(select(Interaction).order_by(Interaction.request_id)).all()
    assert [session.id for session in sessions] == [hash_session("student-42", "test-salt")]
    assert [(item.request_id, item.topic, item.resolved, item.degraded) for item in interactions] == [
        ("request-1", "H26-5.3", True, False),
        ("request-2", "H26-5.3", True, False),
    ]


def test_record_interaction_rolls_back_a_new_session_when_request_is_duplicate() -> None:
    repository, engine = make_repository()
    repository.record_interaction("first", "request-1", "fee", None, True, False, 2.0)
    with pytest.raises(IntegrityError):
        repository.record_interaction("second", "request-1", "fee", None, True, False, 2.0)

    with Session(engine) as db:
        assert len(db.exec(select(ChatSession)).all()) == 1
        assert len(db.exec(select(Interaction)).all()) == 1


def test_foreign_keys_are_enforced() -> None:
    _, engine = make_repository()
    with pytest.raises(IntegrityError):
        with Session(engine) as db, db.begin():
            db.add(Feedback(request_id="missing", rating=-1))


def test_feedback_rating_constraint_is_enforced() -> None:
    repository, engine = make_repository()
    repository.record_interaction("student", "request-1", "fee", None, True, False, 1.0)
    with pytest.raises(IntegrityError):
        with Session(engine) as db, db.begin():
            db.add(Feedback(request_id="request-1", rating=2))


def test_migrations_are_ordered_and_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "assistant.db"
    command = [sys.executable, "scripts/migrate.py", str(database)]
    first = subprocess.run(command, cwd=Path(__file__).parents[1], check=True, capture_output=True, text=True)
    second = subprocess.run(command, cwd=Path(__file__).parents[1], check=True, capture_output=True, text=True)
    assert "apply 001_init.sql" in first.stdout and "apply 002_add_faq.sql" in first.stdout
    assert "skip  001_init.sql" in second.stdout and "skip  002_add_faq.sql" in second.stdout
    with sqlite3.connect(database) as connection:
        assert {row[0] for row in connection.execute("SELECT name FROM schema_version")} == {
            "001_init.sql",
            "002_add_faq.sql",
        }
        assert {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} >= {
            "chat_session",
            "interaction",
            "feedback",
            "faq",
        }
        chat_session_columns = {row[1]: row[2] for row in connection.execute("PRAGMA table_info(chat_session)")}
        interaction_columns = {row[1]: row[2] for row in connection.execute("PRAGMA table_info(interaction)")}
        assert chat_session_columns["id"] == "VARCHAR(16)"
        assert interaction_columns["session_id"] == "VARCHAR(16)"
