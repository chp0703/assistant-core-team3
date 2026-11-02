# AI use log - Lab04

## T5 - dmh612, 2026-11-02

- Tool: OpenAI Codex.
- Generated: the thread-safe sliding-window limiter, T5 HTTP integration,
  deterministic unit/API tests, API contract updates, and rate-limit documentation.
- Integration: based on main c54d9c0 and preserves Hien's merged Chat API (PR #22).
  The temporary T1 wiring used during the October 31 experiment is no longer
  a separate change in the final diff.
- Verification: 36 relevant API/chat/rate-limit tests passed; the focused Ruff
  check passed. Full-suite status is recorded in the accompanying T5 test report.
- Student review and any student edits: pending. No independent authorship,
  reviewer approval, GitHub CI success, or merge is claimed.
