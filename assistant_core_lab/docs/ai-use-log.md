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

## 2026-10-23 - Hiển: Models, Errors and H1 Message Normalization

- Member: `AIVIETNAM-AIO-TheHien`.
- Tool: Codex.
- Tasks: implement the shared models/errors assignment, resolve test import/type
  diagnostics, then add the owner-authorized H1 message-normalization feature.
- Prompt summary: use the Lab 3 interfaces; strip only `Message.text`, reject
  blank normalized input, enforce 1-2000 characters after normalization and
  preserve Unicode/internal whitespace and unrelated fields. Add tests and
  prepare the individual worksheets for owner review before committing or pushing.
- Generated or modified code: `src/assistant_core/models.py`,
  `src/assistant_core/errors.py`, `tests/test_models.py`, `tests/test_errors.py`
  and root `pyrightconfig.json` across the refactor and H1 work. Only the model
  and model tests require further Python changes for H1.
- Review evidence: an after-validator prototype accepted empty normalized text
  and rejected padded 2000-character content; an unguarded before-validator
  prototype raised `AttributeError` for integer/`None` input. The final code
  uses field-scoped Pydantic `StringConstraints` and adds 15 regression cases.
- Checks in the current local environment: **50 pytest cases passed**; Ruff and
  changed-file formatting checks passed from `assistant_core_lab`; Pyright
  reported **0 errors and 0 warnings** on the four models/errors Python files.
- Documents: `docs/lab3/members/AIVIETNAM_AIO_TheHien/before_after.md`,
  `docs/lab3/members/AIVIETNAM_AIO_TheHien/ai_extension_review.md` and the updated
  `docs/lab3/models_errors.md` contract note.
- Publication: the earlier refactor was published in PR #13; the owner has now
  authorized a local H1 commit in English. No H1 push or PR is claimed.
- Personal review: Hiển must inspect the implementation diff and confirm the
  documented review decisions before submission. Codex's technical review is
  not represented as an already completed student manual review.

## 2026-10-23 - phkhoiit-1508: Knowledge Layer

- Member: `phkhoiit-1508`.
- Tool: Codex.
- Tasks: implement the knowledge layer for `offices.csv` and `handbook.json`, add deterministic office lookup and handbook-rule ranking, and write tests.
- Prompt summary: load and validate the local CSV/JSON sources, raise a domain-specific error for malformed data, avoid external APIs and secrets, and cover normal and invalid-data paths with tests.
- Generated or modified code: `src/assistant_core/knowledge.py` and `tests/test_knowledge.py`.
- Manual review and refinement: added `KnowledgeError`; validated required CSV columns, non-empty values, JSON shape, and rule fields; used frozen dataclasses and tuples; corrected the ranking assertion to allow all valid matches; and fixed Ruff import ordering.
- Security/dependency review: no new dependency, API call, credential, or user data logging was introduced.
- Verification: `ruff check .` passed and `pytest -q` passed with 13 tests.
- Documents: `docs/lab3/members/phkhoiit-1508/ai_extension_review.md` and `docs/lab3/members/phkhoiit-1508/before_after.md`.


## 2026-10-23 — Nguyễn Trần Minh Khang: Vietnamese Tuition Request Support

- **Student:** Nguyễn Trần Minh Khang
- **GitHub:** `kentlatoi`
- **AI tool:** OpenAI Codex
- **Feature:** Vietnamese Tuition Request Support

### AI Usage

I used Codex to implement Vietnamese tuition request recognition and credit parsing while preserving existing English functionality and the tuition calculation.

The prompt focused on reusing `Intent`, `InvalidRequest`, and `tuition()`, keeping module responsibilities separate, and avoiding unnecessary dependencies or logging of user data.

### Code Review and Improvements

The AI-assisted development and review included three main improvements:

1. **Vietnamese text recognition:** Added Unicode NFC normalization, case-insensitive matching, whitespace handling, and word boundaries to improve intent detection and reduce false positives.
2. **Credit parsing:** Replaced loose number extraction with label-based parsing, supporting reversed credit order and rejecting duplicate labels, extra numbers, and ambiguous input.
3. **Validation and regression:** Improved English credit parsing, handled uppercase input, rejected negative retake credits, and added regression tests.

### Files Modified

- `src/assistant_core/router.py`
- `src/assistant_core/tools.py`
- `tests/test_router.py`
- `tests/test_tools.py`

### Testing Results

| Verification | Result |
|---|---|
| H1-focused unit tests | 27 passed |
| Full test suite before team integration | 77 passed |
| Full test suite after knowledge-module integration | 80 passed |
| Ruff lint | All checks passed |
| Ruff format check | 4 files already formatted |

The additional three tests in the integrated suite belong to the knowledge module.

