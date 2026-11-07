#!/usr/bin/env python3
"""Fill a database with synthetic Lab 5 interactions (no real student data).

Feedback generation is deliberately deferred to Member #2's Repository
implementation of add_feedback().
"""

from __future__ import annotations

import random
import sys
import uuid

from assistant_api.db import Repository, init_db, make_engine


def seed(db_path: str, count: int = 300) -> None:
    """Insert deterministic, synthetic interaction metadata for query work."""
    random.seed(7)
    engine = make_engine(f"sqlite:///{db_path}")
    init_db(engine)
    repository = Repository(engine, "seed-salt")
    plan = [
        ("greeting", None, 0.99, 2),
        ("fee", None, 0.95, 5),
        ("office", None, 0.97, 3),
        ("rule", "H26-5.3", 0.85, 40),
        ("rule", "H26-4.2", 0.80, 45),
        ("rule", "H26-7.2", 0.70, 60),
        ("unknown", None, 0.0, 8),
    ]
    weights = [10, 20, 15, 25, 15, 5, 10]
    for _ in range(count):
        intent, topic, ok_rate, base_ms = random.choices(plan, weights)[0]
        repository.record_interaction(
            f"student-{random.randint(1, 60)}",
            uuid.uuid4().hex[:12],
            intent,
            topic,
            intent != "unknown",
            intent != "unknown" and random.random() > ok_rate,
            round(random.gauss(base_ms, base_ms / 3), 1),
        )
    print(f"seeded {count} interactions into {db_path}")


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else "assistant.db", int(sys.argv[2]) if len(sys.argv) > 2 else 300)
