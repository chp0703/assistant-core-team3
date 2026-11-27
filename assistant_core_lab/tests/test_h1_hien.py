import pytest

from ui.logic import format_sources


def test_format_sources_skips_empty_entries_without_extra_separators() -> None:
    sources = [
        {"id": "A", "title": "First"},
        {},
        {"id": "", "title": ""},
        {"id": "B", "title": "Second"},
    ]

    assert format_sources(sources) == "Sources: A — First; B — Second"


def test_format_sources_preserves_string_zero_identifier() -> None:
    assert format_sources([{"id": "0", "title": ""}]) == "Sources: 0"


def test_format_sources_preserves_order_and_count_for_1000_records() -> None:
    sources = [{"id": f"DOC-{i}", "title": f"Document {i}"} for i in range(1000)]
    expected = "Sources: " + "; ".join(f"DOC-{i} — Document {i}" for i in range(1000))

    assert format_sources(sources) == expected


def test_format_sources_preserves_vietnamese_text() -> None:
    sources = [{"id": "H26#5.3", "title": "Điều kiện đăng ký khóa luận"}, {"title": "Học phí và lệ phí"}]

    assert format_sources(sources) == "Sources: H26#5.3 — Điều kiện đăng ký khóa luận; Học phí và lệ phí"


def test_format_sources_raises_type_error_for_none_container() -> None:
    with pytest.raises(TypeError):
        format_sources(None)  # type: ignore[arg-type]


def test_format_sources_raises_attribute_error_for_non_dict_member() -> None:
    with pytest.raises(AttributeError):
        format_sources(["not a source record"])  # type: ignore[list-item]
