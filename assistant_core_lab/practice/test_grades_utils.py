"""Happy-path tests — they all pass, yet the module has three bugs. Add your regression tests below."""
from grades_utils import add_grade, average, letter, top_n


def test_average_happy():
    assert average([8, 9, 10]) == 9.0


def test_top_n_happy():
    assert top_n({"An": 9, "Binh": 7, "Chi": 8}, 3)[0] == "An"


def test_add_grade_happy():
    assert add_grade("An", 8.0, {}) == {"An": [8.0]}


def test_letter():
    assert [letter(x) for x in (9, 7.5, 6, 4.5, 2)] == ["A", "B", "C", "D", "F"]


# ---- your regression tests (one per bug report) -----------------------------
def test_bug1_average_empty() -> None:
    assert average([]) == 0.0


def test_bug2_top_n_returns_n() -> None:
    scores = {"Chi": 8, "Binh": 9, "An": 9, "Dung": 7}

    assert top_n(scores, 3) == ["An", "Binh", "Chi"]
    assert top_n(scores, 1) == ["An"]


def test_bug3_add_grade_new_book_each_time() -> None:
    first = add_grade("An", 8.0)
    second = add_grade("Binh", 6.0)

    assert first is not second
    assert first == {"An": [8.0]}
    assert second == {"Binh": [6.0]}
