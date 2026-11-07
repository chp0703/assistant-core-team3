#!/usr/bin/env python3
"""Apply SQL migrations in order and remember which ones ran.

Usage: python scripts/migrate.py assistant.db
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def migrate(db_path: str) -> None:
    """Apply each unapplied migration in an independent transaction."""
    folder = Path(__file__).resolve().parents[1] / "sql" / "migrations"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied = {row[0] for row in connection.execute("SELECT name FROM schema_version")}
        for migration in sorted(folder.glob("*.sql")):
            if migration.name in applied:
                print(f"skip  {migration.name}")
                continue
            with connection:
                connection.executescript(migration.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_version VALUES (?, ?)",
                    (migration.name, datetime.now(timezone.utc).isoformat()),
                )
            print(f"apply {migration.name}")


if __name__ == "__main__":
    migrate(sys.argv[1] if len(sys.argv) > 1 else "assistant.db")
