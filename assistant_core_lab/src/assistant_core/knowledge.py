"""Load and search the assistant's local knowledge sources."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class KnowledgeError(Exception):
    """Raised when a knowledge source cannot be loaded or is malformed."""


@dataclass(frozen=True, slots=True)
class Office:
    """An office and its opening hours."""

    name: str
    room: str
    hours: str


@dataclass(frozen=True, slots=True)
class Rule:
    """A handbook rule that can be cited in an answer."""

    id: str
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class KnowledgeBase:
    """Immutable, in-memory view of the offices and handbook."""

    offices: tuple[Office, ...]
    rules: tuple[Rule, ...]

    def find_office(self, question: str) -> Office | None:
        """Return the first office whose name occurs in *question*."""
        normalized_question = question.casefold()
        for office in self.offices:
            if office.name.casefold() in normalized_question:
                return office
        return None

    def search_rules(self, question: str) -> list[Rule]:
        """Return handbook rules ranked by the number of matching keywords."""
        words = _keywords(question)
        scored = [(sum(word in rule.text.casefold() for word in words), rule) for rule in self.rules]
        return [rule for score, rule in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0]

    def find_rule(self, question: str) -> Rule | None:
        """Return the best matching rule, or ``None`` when there is no match."""
        matches = self.search_rules(question)
        return matches[0] if matches else None


def load_knowledge(data_dir: str | Path = "data") -> KnowledgeBase:
    """Load ``offices.csv`` and ``handbook.json`` from *data_dir*."""
    directory = Path(data_dir)
    return KnowledgeBase(
        offices=tuple(load_offices(directory / "offices.csv")),
        rules=tuple(load_handbook(directory / "handbook.json")),
    )


def load_offices(path: str | Path) -> list[Office]:
    """Load offices from a CSV with ``name``, ``room`` and ``hours`` columns."""
    source = Path(path)
    try:
        with source.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"name", "room", "hours"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise KnowledgeError(f"Invalid office file {source}: expected columns name, room, hours")
            offices = []
            for row_number, row in enumerate(reader, start=2):
                values = {key: (row.get(key) or "").strip() for key in required}
                if not all(values.values()):
                    raise KnowledgeError(f"Invalid office file {source}: empty value on row {row_number}")
                offices.append(Office(**values))
            return offices
    except KnowledgeError:
        raise
    except (OSError, csv.Error) as error:
        raise KnowledgeError(f"Could not load offices from {source}: {error}") from error


def load_handbook(path: str | Path) -> list[Rule]:
    """Load handbook rules from a JSON list of ``id``, ``title`` and ``text``."""
    source = Path(path)
    try:
        with source.open(encoding="utf-8") as handle:
            payload: Any = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise KnowledgeError(f"Could not load handbook from {source}: {error}") from error

    if not isinstance(payload, list):
        raise KnowledgeError(f"Invalid handbook file {source}: expected a JSON list")

    rules = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict) or not all(
            isinstance(item.get(field), str) and item[field].strip() for field in ("id", "title", "text")
        ):
            raise KnowledgeError(f"Invalid handbook file {source}: invalid rule at item {index}")
        rules.append(Rule(id=item["id"].strip(), title=item["title"].strip(), text=item["text"].strip()))
    return rules


def _keywords(question: str) -> set[str]:
    """Extract meaningful case-insensitive words for deterministic search."""
    return {word for word in question.casefold().replace("?", " ").split() if len(word) > 3}
