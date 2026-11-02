# T5 verification - dmh612

Date: 2026-11-02. Base: c54d9c0 (origin/main).
Branch: feat/lab04-dmh612-ratelimit.
Runtime: Python 3.12.14; dependency versions from starter/requirements.txt.

## Required files are available

- Hien's T1 Chat API: merged through PR #22 on 2026-11-01.
- Chat request/response schemas and rate_limit_per_min settings: available.
- Service implementation, sample data, test fixtures and documentation paths:
  available in public_materials/lab04/starter.
- Feedback and offices endpoints from current main are preserved.
- Weather T4 is a separate open PR (#32); T5 does not require it.

## Commands and actual results

Run from public_materials/lab04/starter:

```powershell
python -m ruff check .
# All checks passed!

python -m pytest -q tests/test_ratelimit.py tests/test_chat.py tests/test_api.py -k "not weather"
# 36 passed, 3 deselected

python -m pytest -q
# 52 passed, 2 failed
```

The two full-suite failures are existing weather TODOs:

- tests/test_api.py::test_weather_ok: NotImplementedError("T4").
- tests/test_api.py::test_weather_down_returns_503: NotImplementedError("T4").

The T4 handler is unchanged from the base revision. These failures must be
rerun after the team's weather implementation is merged. They are not marked
as skipped or expected failures in this change. One dependency deprecation
warning from Starlette/AnyIO also appears; it does not affect the test result.

## Review scope

- RateLimiter: strict positive integer configuration, thread-safe sliding window,
  exact 60-second expiry, independent client budgets, rejected hits not counted.
- HTTP integration: real T1 chat endpoint, quota checked before service handling,
  unified 429 error body, 422 does not consume quota, health remains available.
- Tests: 15 new parameterised/unit/API cases plus the enabled starter bonus test.
- Docs: T5 guide, this report, README link, chat contract row and AI-use record.
- No replacement implementation of another member's Chat/Feedback/Weather task
  is included in the final diff. Main's T1 handler is retained verbatim after
  the new rate-limit check.

Checks were executed locally by Codex. No GitHub CI run, peer approval or merge
is claimed. The repository's current workflow checks Lab03, so Lab04 tests must
be run explicitly as shown above.
