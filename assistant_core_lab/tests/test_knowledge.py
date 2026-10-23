from pathlib import Path

import pytest

from assistant_core.knowledge import KnowledgeError, load_handbook, load_knowledge, load_offices


DATA_DIR = Path(__file__).parents[1] / "data"


def test_loads_lab_knowledge() -> None:
    knowledge = load_knowledge(DATA_DIR)

    assert len(knowledge.offices) == 4
    assert knowledge.find_office("Where is the library?").room == "B.201"
    assert knowledge.find_rule("Can I retake a course?").id == "H26-4.2"


def test_rule_search_is_ranked() -> None:
    knowledge = load_knowledge(DATA_DIR)

    assert [rule.id for rule in knowledge.search_rules("thesis registration credits GPA")] == ["H26-5.3", "H26-5.4"]


def test_missing_or_malformed_sources_raise_domain_error(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeError, match="Could not load offices"):
        load_offices(tmp_path / "missing.csv")

    handbook = tmp_path / "handbook.json"
    handbook.write_text("{}", encoding="utf-8")
    with pytest.raises(KnowledgeError, match="expected a JSON list"):
        load_handbook(handbook)
