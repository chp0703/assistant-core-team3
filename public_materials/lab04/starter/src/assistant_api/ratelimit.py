"""Thread-safe, in-memory sliding-window limits per client over 60 seconds."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock


class RateLimiter:
    """Allow at most per_minute accepted requests per key in (now - 60, now]."""

    def __init__(self, per_minute: int, *, clock: Callable[[], float] | None = None) -> None:
        """Use a monotonic clock; accept an alternative clock for deterministic tests."""
        if isinstance(per_minute, bool) or not isinstance(per_minute, int) or per_minute < 1:
            raise ValueError("per_minute must be a positive integer")
        self.per_minute = per_minute
        self._clock = time.monotonic if clock is None else clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """Atomically expire old hits and record this request only if allowed.

        A hit exactly 60 seconds old has expired. Rejected attempts do not
        extend the client's window. Each client has an independent budget.
        """
        with self._lock:
            now = self._clock()
            hits = self._hits[key]
            while hits and hits[0] <= now - 60:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return False
            hits.append(now)
            return True
