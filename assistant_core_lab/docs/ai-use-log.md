# AI Use Log

## H1 - AI Extension Review

- Member: `chp0703`
- Tool: Codex
- Feature: Help / Supported Capabilities
- Purpose: Implement a deterministic Help flow and prepare the individual H1 review report.
- Files generated or modified: `models.py`, `router.py`, `service.py`, `responder.py`, and their
  corresponding Help tests; `docs/lab3/members/chp0703/ai_extension_review.md`.
- Review and refinement: restricted Help recognition to exact normalized requests, removed
  unsupported capability claims, separated routing from response text, and added regression tests
  for unrelated messages.
- Verification: `python -m pytest -v tests/test_models.py tests/test_router.py
  tests/test_responder.py tests/test_service.py` passed (12 tests). The full pytest run is blocked
  during collection because `python-dotenv` is not installed; Ruff is unavailable in this Python
  environment.
- Remaining personal verification: review the report wording and the implementation diff before
  submission; the wider tuition, office, and handbook features are not implemented in this
  skeleton.
