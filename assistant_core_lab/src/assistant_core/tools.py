"""Deterministic tools for tuition calculation."""

import re

from assistant_core.errors import InvalidRequest


def parse_credits(text: str) -> tuple[int, int]:
    """Extract regular and retake credits from a tuition question."""
    retake = re.search(r"(\d+)\s*retake", text)
    numbers = [int(number) for number in re.findall(r"\d+", text)]

    retake_credits = int(retake.group(1)) if retake else 0
    other_numbers = numbers.copy()

    if retake:
        other_numbers.remove(retake_credits)

    if not other_numbers:
        raise InvalidRequest("How many credits?")

    return other_numbers[0], retake_credits


def tuition(
    credits: int,
    retake: int,
    rate: int,
    retake_multiplier: float,
    max_credits: int,
) -> int:
    """Calculate tuition using configured rates and credit limits."""
    if not 1 <= credits <= max_credits:
        raise InvalidRequest(f"Credits must be between 1 and {max_credits}.")

    return int(credits * rate + retake * rate * retake_multiplier)
