# Team 3 — Lab 07 Foundation & API Contract

Owner: Châu Hòa Phát (`@chp0703`).  
Branch: `feat/lab07-foundation-phat`.

## 1. Official Starter Provenance & File Mapping

Official Lab 07 materials were imported untouched into `public_materials/lab07/` from:
- Repository: `https://github.com/CSC10014-at-fit-hcmus/public_materials`
- Commit: `ea80fc97f747cadecde2262c9fd934eb2393c082` (`W7: added materials for W7`)

Only the Lab 07 UI, practice, and worksheet files were copied into `assistant_core_lab/` (preserving all Lab 03–06 backend, core, RAG, DB, and tests untouched):

| Target path in `assistant_core_lab/` | Source in `public_materials/lab07/` | Next owner | Status after Foundation PR |
| --- | --- | --- | --- |
| `ui/__init__.py` | `starter/ui/__init__.py` | Phát (foundation) | Imported verbatim |
| `ui/api_client.py` | `starter/ui/api_client.py` | Khang (`@kentlatoi`) | Imported verbatim |
| `ui/logic.py` | `starter/ui/logic.py` | Hiển (`@AIVIETNAM-AIO-TheHien`) | Imported with `# TODO L1`/`L2` intact (comment line 32 wrapped for Ruff E501) |
| `ui/app.py` | `starter/ui/app.py` | Hùng (`@dmh612`) | Imported verbatim (`# TODO F1` intact) |
| `practice/hello_streamlit.py` | `practice/hello_streamlit.py` | Hương (`@thanhhuong107`) | Imported verbatim (`# TODO U2–U4` intact) |
| `practice/test_hello_streamlit.py` | `practice/test_hello_streamlit.py` | Hương (`@thanhhuong107`) | Imported verbatim; run from `practice/` (`pytest -q test_hello_streamlit.py`) |
| `worksheets/usability_checklist.md` | `worksheets/usability_checklist.md` | Hương (`@thanhhuong107`) | Imported verbatim |
| `worksheets/user_test_observations.md` | `worksheets/user_test_observations.md` | Khôi (`@phkhoiit-1508`) | Imported verbatim |
| `tests/test_ui.py` | `starter/tests/test_ui.py` | Hiển (`@AIVIETNAM-AIO-TheHien`) | Scaffold pointing to verbatim starter tests so `main` CI stays green until L1/L2 are implemented |

## 2. Backend HTTP API Contract Decision (`escalate`)

- **Decision:** Additive field `escalate: bool = False` added to HTTP `ChatResponse` (`src/assistant_api/schemas.py`).
- **Core `Response` preserved:** `src/assistant_core/models.py` (`Response`) is unchanged (`answer`, `intent`, `sources`, `degraded`), so all Lab 03–06 core/CLI contracts remain intact.
- **Mapping in `src/assistant_api/main.py`:** `POST /v1/chat` uses `AssistantService.handle_with_rag_result()` and maps `rag_result.escalate` directly (`False` when `rag_result is None`):
  - Grounded KB policy answer (`RAG_ENABLED=true`): `intent="rule"`, `sources=[...]`, `escalate=False`, `degraded=False`.
  - No-evidence / out-of-scope (`RAG_ENABLED=true`): `intent="unknown"`, `sources=[]`, `escalate=True`.
  - Privacy refusal (`RAG_ENABLED=true`): `intent="unknown"`, `sources=[]`, `escalate=False` (never conflated with escalation).
  - Provider fallback (`RAG_ENABLED=true`): `intent="rule"`, `degraded=True`, `escalate=False`, source preserved.
  - Deterministic routes (`GREETING`, `FEE`, `OFFICE`) and legacy `RAG_ENABLED=false` mode: `escalate=False`.
- **Dependencies:** Added `streamlit==1.39.0` to `assistant_core_lab/requirements.txt` (exact starter pin) and updated `pyproject.toml` (`pythonpath = [".", "src", "practice"]`, `testpaths = ["tests", "practice/test_mini_search.py"]`).

## 3. Handoff for Parallel Member Branches

Once this Foundation PR merges into `main`:
1. **Khang (`feat/lab07-api-client-kent`):** refine/verify `ui/api_client.py` against this `ChatResponse` contract and add HTTP client unit tests in `tests/test_api_client.py`.
2. **Hiển (`feat/lab07-sources-status-hien`):** implement L1 (`format_sources`) and L2 (`status_note`) in `ui/logic.py` and activate the verbatim 7 starter tests from `public_materials/lab07/starter/tests/test_ui.py` into `tests/test_ui.py` (plus additional coverage).
3. **Hương (`feat/lab07-practice-usability-huong`):** implement U2–U4 in `practice/hello_streamlit.py`, verify `pytest -q test_hello_streamlit.py` passes (4/4), and later open `feat/lab07-usability-check-huong` for `worksheets/usability_checklist.md` after UI merges.
4. **Hùng (`feat/lab07-chat-feedback-hung`):** implement F1 and chat UI polish in `ui/app.py` + `tests/test_ui_app.py` once client and logic are ready.
5. **Khôi (`feat/lab07-user-test-khoi`):** run the 10-minute external user test after UI merges, fill `worksheets/user_test_observations.md`, add before/after screenshots under `docs/lab7/evidence/`, and submit one targeted fix.
