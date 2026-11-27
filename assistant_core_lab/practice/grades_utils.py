"""Lab 8 warm-up: a small module with THREE seeded bugs.

The bug reports in bug_reports/ describe what users saw. For each bug:
  1. reproduce it (Python shell or the debugger),
  2. write a test that FAILS because of the bug,
  3. fix the code so the test passes,
  4. keep the test — it is now a regression test.
"""


def average(scores: list[float]) -> float:
    """Average of the scores, rounded to 2 decimals. An empty list gives 0.0."""
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def top_n(scores: dict[str, float], n: int) -> list[str]:
    """Names of the n best students, best first (ties: alphabetical)."""
    ranked = sorted(scores, key=lambda name: (-scores[name], name))
    return ranked[:n]


def add_grade(name: str, grade: float, book: dict[str, list[float]] | None = None) -> dict[str, list[float]]:
    """Add a grade for `name` to a grade book and return the book. Without a book, start a NEW one."""
    if book is None:
        book = {}
    book.setdefault(name, []).append(grade)
    return book


def letter(score: float) -> str:
    """A for >= 8.5, B for >= 7.0, C for >= 5.5, D for >= 4.0, else F.  (This one is correct.)"""
    for limit, grade in [(8.5, "A"), (7.0, "B"), (5.5, "C"), (4.0, "D")]:
        if score >= limit:
            return grade
    return "F"
