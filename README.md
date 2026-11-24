# CSC10014 — Smart Virtual Assistant (Labs 03–07)

This repository contains Team 3's integrated implementation for CSC10014 Practical Track.
Lab 03 introduced the modular `assistant_core` service, Lab 04 added the FastAPI backend,
Lab 05 added SQLite persistence, feedback workflows, and SQL analytics, Lab 06 added
Markdown knowledge-base chunking, BM25/TF-IDF/Hybrid retrieval, grounded structured LLM answers
(A2), low-evidence abstention and privacy guardrails (A1), unified CLI/FastAPI integration,
and evaluation tooling, and Lab 07 adds the full-stack Streamlit chat UI communicating strictly
over HTTP with FastAPI (`ui/app.py`, `ui/api_client.py`, `ui/logic.py`), source citations,
escalation and degraded status notes, 👍/👎 feedback controls, the U1–U4 Streamlit warm-up,
usability checklist verification, and a documented usability study with a UI fix.

The final integrated implementation lives in `assistant_core_lab/`. The folders under
`public_materials/` contain official starter materials and references;
they are not the primary application entry point.

## Team Members

| No. | Full Name | GitHub | Student ID |
| :-: | --------- | ------ | :--------: |
| 1 | Châu Hòa Phát | [@chp0703](https://github.com/chp0703) | 25127224 |
| 2 | Huỳnh Nguyễn Thế Hiển | [@AIVIETNAM-AIO-TheHien](https://github.com/AIVIETNAM-AIO-TheHien) | 25127327 |
| 3 | Phạm Hùng Khôi | [@phkhoiit-1508](https://github.com/phkhoiit-1508) | 25127390 |
| 4 | Nguyễn Trần Minh Khang | [@kentlatoi](https://github.com/kentlatoi) | 25127369 |
| 5 | Nguyễn Ngọc Thanh Hương | [@thanhhuong107](https://github.com/thanhhuong107) | 25127197 |
| 6 | Đặng Minh Hùng | [@dmh612](https://github.com/dmh612) | 25127340 |

## Architecture (Labs 03–07)

```text
Browser (http://localhost:8501)
    |
    v
Streamlit UI: assistant_core_lab/ui/app.py
    |  session_id per tab, chat history, spinner, 👍/👎 feedback
    +--> ui/logic.py        (validate_input, format_sources, status_note)
    +--> ui/api_client.py   (HTTP only via httpx: /health, /v1/chat, /v1/feedback)
              |
              v
FastAPI Backend: assistant_core_lab/src/assistant_api/ (http://127.0.0.1:8000)
              |
              v
assistant_core.service.create_service()
    +--> Lab 03–04: deterministic tuition / office / greeting + REST API
    +--> Lab 05: SQLite interaction & feedback persistence + SQL analytics
    +--> Lab 06: BM25/TF-IDF/Hybrid RAG, A1 abstention, A2 grounding, privacy guard
```

The UI layer under `assistant_core_lab/ui/` never imports `assistant_core`, `assistant_api`,
`sqlite3`, or reads `data/kb/` directly — all communication goes through HTTP JSON endpoints.

## Key Features

- **Modular Core & REST API (Labs 03–04):** Intent routing, tuition calculations, office/handbook lookup, typed models, rate limiting, and FastAPI endpoints (`/health`, `/v1/chat`, `/v1/feedback`, `/v1/offices`, `/v1/weather`).
- **SQLite Persistence & Analytics (Lab 05):** Privacy-safe interaction metadata and feedback persistence, admin-protected feedback listing (`X-API-Key`), and SQL analytics (`sql/my_queries.sql`).
- **RAG, Grounding & Guardrails (Lab 06):** Markdown KB chunking (`data/kb/*.md`), BM25/TF-IDF/Hybrid retrieval, `StubLLM` offline adapter (plus optional Ollama/OpenAI-compatible providers), A2 citation grounding, A1 low-evidence abstention, bilingual privacy guardrails, 25-case evaluation (`eval/cases.jsonl`), and three-path comparison (`eval/compare_paths.py`).
- **Full-Stack Streamlit Chat UI (Lab 07):**
  - HTTP-only `AssistantClient` (`ui/api_client.py`) with strict JSON schema/type validation and user-friendly messages for timeout, connection errors, 422, 429, 5xx, and malformed responses.
  - Source formatting (`format_sources`) and status notes (`status_note`) with escalation guidance (`Training Office, room I.101`) taking precedence over degraded fallback notices.
  - Additive `escalate: bool = False` field in `POST /v1/chat` (`ChatResponse`) mapped from `RagResult.escalate` while keeping Lab 03–06 contracts intact.
  - Interactive chat page (`ui/app.py`) with per-tab `session_id`, clickable sidebar examples, `Thinking…` spinner, AI disclosure, and 👍/👎 feedback buttons that only mark answers as rated after a confirmed `201` response (retaining retry buttons on failure).
  - Warm-up Streamlit app U1–U4 (`practice/hello_streamlit.py`), verified usability checklist (`worksheets/usability_checklist.md`), and usability observations + welcome-message fix with before/after screenshots (`worksheets/user_test_observations.md`, `docs/lab7/evidence/`).

## Technology Stack

Python 3.10+, Streamlit (`1.39.0`), FastAPI, Pydantic, HTTPX, SQLModel, SQLite, Uvicorn,
python-dotenv, pytest, Ruff, and setuptools.

## Project Structure

```text
assistant-core-team3/
├── .github/workflows/ci.yml        # Ruff, full pytest (tests + mini_search), and U1–U4 warm-up tests
├── assistant_core_lab/
│   ├── pyproject.toml
│   ├── requirements.txt            # Pinned dependencies including streamlit==1.39.0
│   ├── .env.example                # Environment template (ASSISTANT_API_URL, RAG_ENABLED, etc.)
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── api_client.py           # Lab 07 Part C: HTTP client (httpx) and ChatResult
│   │   ├── logic.py                # Lab 07 Part D (L1/L2): input validation, sources, status notes
│   │   └── app.py                  # Lab 07 Part D (F1): Streamlit chat UI and 👍/👎 feedback
│   ├── practice/
│   │   ├── mini_search.py          # Lab 06 warm-up S1–S3 inverted index & ranking
│   │   ├── test_mini_search.py     # Unit tests for S1–S3 mini search
│   │   ├── hello_streamlit.py      # Lab 07 warm-up U1–U4 Streamlit page
│   │   └── test_hello_streamlit.py # Lab 07 warm-up U1–U4 AppTest suite (4 tests)
│   ├── worksheets/
│   │   ├── usability_checklist.md      # Lab 07 Part E completed checklist & verification evidence
│   │   └── user_test_observations.md   # Lab 07 Homework H1 observations & UI fix record
│   ├── data/
│   │   ├── handbook.json
│   │   ├── offices.csv
│   │   └── kb/                     # Lab 06–07 Markdown knowledge base
│   │       ├── handbook_2026.md
│   │       ├── fees_2026.md
│   │       └── services_2026.md
│   ├── eval/
│   │   ├── cases.jsonl             # 25 official evaluation cases (20 starter + 5 H1)
│   │   └── compare_paths.py        # Lab 06 Part F three-path comparison runner
│   ├── docs/
│   │   ├── lab3/                   # Lab 03 documentation
│   │   ├── lab6/                   # Lab 06 RAG contract, comparison report, member evidence
│   │   └── lab7/
│   │       ├── foundation_contract.md  # Lab 07 starter mapping & HTTP escalate contract
│   │       └── evidence/               # Lab 07 H1 before/after screenshots
│   ├── scripts/                    # Migration and synthetic-data scripts
│   ├── sql/
│   │   ├── migrations/             # Database schema migrations
│   │   └── my_queries.sql          # Lab 05 F1–F3 analytics queries
│   ├── src/
│   │   ├── assistant_core/         # Core routing, tools, RAG, grounding, guardrails, service
│   │   └── assistant_api/          # FastAPI app, schemas (incl. escalate), SQLite DB, rate limit
│   └── tests/
│       ├── test_api_client.py      # Lab 07 Part C HTTP client unit tests (MockTransport)
│       ├── test_ui.py              # Lab 07 Part D starter + extended L1/L2 unit tests
│       ├── test_ui_app.py          # Lab 07 Part D/F1 Streamlit AppTest UI tests
│       ├── api/
│       │   ├── test_lab07_contract.py  # Lab 07 HTTP contract tests (escalate, privacy, feedback)
│       │   └── ...                 # Lab 04–05 API and persistence tests
│       └── ...                     # Lab 03–06 core, RAG, grounding, guard, and eval tests
├── public_materials/
│   ├── lab03/
│   ├── lab04/
│   ├── lab05/
│   ├── lab06/
│   └── lab07/                      # Official Lab 07 reference materials
└── README.md
```

## Setup

From the repository root:

```bash
git clone https://github.com/chp0703/assistant-core-team3.git
cd assistant-core-team3/assistant_core_lab
python -m venv .venv
```

Activate the virtual environment:

- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

Install dependencies (includes `streamlit==1.39.0`) and create your local `.env`:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env       # Windows PowerShell
# cp .env.example .env            # macOS/Linux
```

Configure your local `.env` (never commit `.env` to Git):

- Replace `SESSION_SALT` and `API_ADMIN_KEY` with private random values.
- Keep `LLM_PROVIDER=stub` for offline demo/testing (zero API cost).
- Set **`RAG_ENABLED=true`** and keep `KB_DIR=data/kb` when running the **Lab 07 full-stack demo** so handbook citations (e.g., `H26#5.3`) and out-of-scope escalation (`escalate=true`) are active. (`.env.example` keeps `RAG_ENABLED=false` by default for Lab 03–05 compatibility.)
- Optionally set `ASSISTANT_API_URL=http://127.0.0.1:8000` if you run the FastAPI backend on another host or port.

## Run the Full-Stack App (Lab 07 — Two Terminals)

Open **two terminals**, both in `assistant_core_lab/` with `.venv` activated:

**Terminal 1 — FastAPI backend (port 8000):**

```bash
python -m uvicorn assistant_api.main:create_app --factory --host 127.0.0.1 --port 8000
```

- Health check: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>

**Terminal 2 — Streamlit chat UI (port 8501):**

```bash
python -m streamlit run ui/app.py --server.port 8501
```

- Chat UI: <http://localhost:8501>

If the API is hosted on a custom address, set `ASSISTANT_API_URL` before starting Streamlit:

```bash
# Windows PowerShell
$env:ASSISTANT_API_URL="http://127.0.0.1:8000"; python -m streamlit run ui/app.py --server.port 8501

# macOS / Linux
ASSISTANT_API_URL=http://127.0.0.1:8000 python -m streamlit run ui/app.py --server.port 8501
```

To run the Lab 07 warm-up page separately:

```bash
cd practice
python -m streamlit run hello_streamlit.py --server.port 8502
```

## HTTP API Contract

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/health` | Returns `200` `{"status": "ok", "version": "..."}`. |
| `POST` | `/v1/chat` | Sends `{"message": "...", "session_id": "..."}` and persists interaction metadata. |
| `POST` | `/v1/feedback` | Saves feedback `{"request_id": "...", "rating": -1\|0\|1, "comment": ...}`; returns `201` (or `404` for unknown `request_id`). |
| `GET` | `/v1/feedback` | Lists saved feedback newest first; requires `X-API-Key` header (optional `limit`, default `100`). |
| `GET` | `/v1/weather` | Gets campus weather. |
| `GET` | `/v1/offices` | Lists campus offices. |

**`POST /v1/chat` response (`200 OK`):**

```json
{
  "answer": "...",
  "intent": "rule",
  "sources": [{"id": "H26#5.3", "title": "5.3 Thesis registration"}],
  "degraded": false,
  "request_id": "<server-generated-id>",
  "escalate": false
}
```

- `escalate` is `true` only for low-evidence / out-of-scope abstention (A1). Privacy refusals return `escalate: false`.
- Common error responses: `422` (empty or >2000-char message / invalid payload), `429` (rate limit exceeded), `404` (feedback for unknown `request_id`).

## Testing and Quality Checks

Run the standard suite and linter from `assistant_core_lab/`:

```bash
python -m ruff check .
python -m pytest -q
```

Run the Lab 07 warm-up tests (U1–U4) from `assistant_core_lab/practice/`:

```bash
cd practice
python -m pytest -q test_hello_streamlit.py
```

Focused Lab 07 checks (from `assistant_core_lab/`):

```bash
python -m pytest -q tests/test_api_client.py tests/test_ui.py tests/test_ui_app.py tests/api/test_lab07_contract.py
```

Focused Lab 05 and Lab 06 checks (from `assistant_core_lab/`):

```bash
python -m pytest -q tests/api/test_add_feedback.py tests/api/test_api.py tests/test_db.py
python -m pytest -q tests/test_rag.py
python -m pytest -q tests/test_rag.py -k citation
python -m pytest -q practice/test_mini_search.py
python eval/compare_paths.py
```

GitHub Actions (`.github/workflows/ci.yml`) automatically runs `ruff check .`, `pytest -q` (including `tests/test_ui.py`, `tests/test_ui_app.py`, `tests/test_api_client.py`, `tests/api/test_lab07_contract.py`, `practice/test_mini_search.py`, and all Lab 03–06 tests), and the 4 U1–U4 warm-up tests in `practice/test_hello_streamlit.py`.

## Troubleshooting (Common Errors)

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| `The assistant backend is not reachable.` / `Cannot reach the assistant.` | FastAPI is not running or `ASSISTANT_API_URL` points to the wrong port. | Start Terminal 1 (`uvicorn assistant_api.main:create_app --factory --host 127.0.0.1 --port 8000`) and verify <http://127.0.0.1:8000/health>. |
| Handbook questions show no `Sources:` or out-of-scope questions do not escalate. | `RAG_ENABLED` is still `false` (default in `.env.example`). | Set `RAG_ENABLED=true` and `KB_DIR=data/kb` in `assistant_core_lab/.env`, then restart Terminal 1. |
| `Please type a question (1–2000 characters).` (`422`) | Message is empty/whitespace or exceeds 2000 characters. | Enter a concise question between 1 and 2000 characters. |
| `Too many questions in a short time. Please wait a minute.` (`429`) | Per-client rate limit (`RATE_LIMIT_PER_MIN`) exceeded. | Wait a minute before sending the next request (or adjust `RATE_LIMIT_PER_MIN` in local `.env` for testing). |
| `Could not send your feedback. Please try again.` | Backend was unreachable or `request_id` was not saved in SQLite. | Check Terminal 1 is running; the 👍/👎 buttons remain visible so you can retry. |
| `test_hello_streamlit.py` fails to find `hello_streamlit.py`. | `pytest` was launched from `assistant_core_lab/` instead of `assistant_core_lab/practice/`. | `cd practice` first, then run `python -m pytest -q test_hello_streamlit.py`. |

## Lab 07 Deliverables

- **Foundation & API Contract (`docs/lab7/foundation_contract.md`):** Official Lab 07 materials in `public_materials/lab07/`, `streamlit==1.39.0` dependency, additive `escalate: bool = False` in `ChatResponse`, and contract tests (`tests/api/test_lab07_contract.py`).
- **Warm-up U1–U4:** `practice/hello_streamlit.py` and `practice/test_hello_streamlit.py` (4 passing AppTest tests).
- **Part C — HTTP API Client:** `ui/api_client.py` and `tests/test_api_client.py` (`httpx.MockTransport` coverage for success, flags, network/HTTP errors, malformed JSON, feedback, and health checks).
- **Part D — L1, L2 & F1 Chat UI:** `ui/logic.py` (`format_sources`, `status_note`), `tests/test_ui.py` (7 starter + 6 extended tests), `ui/app.py` (Streamlit chat page, session state, sidebar prompts, spinner, 👍/👎 feedback with failure handling), and `tests/test_ui_app.py` (AppTest coverage).
- **Part E — Usability Checklist:** `worksheets/usability_checklist.md` (10/10 verified with browser & mobile `390 × 844` evidence).
- **Homework H1 — Usability Walkthrough & Fix:** `worksheets/user_test_observations.md` (3 real observations), welcome prompt fix (`"Ask one question at a time."` in `ui/logic.py`), and before/after screenshots under `docs/lab7/evidence/`.

## Lab 06 Deliverables

The Lab 06 RAG pipeline is integrated into `assistant_core_lab/` while keeping all Lab 03–05
deterministic features, API schemas, rate limiting, and SQLite persistence intact.

- **S1–S3 Warm-up:** `practice/mini_search.py` and `practice/test_mini_search.py` implement the inverted index and keyword ranking baseline.
- **Part C — Knowledge Base & Retrieval:** `src/assistant_core/rag/chunker.py` and `index.py` load the 14 Markdown chunks from `data/kb/` with provenance metadata and provide BM25, TF-IDF, and Hybrid retrieval.
- **Part D — LLM & A2 Grounding:** `src/assistant_core/llm.py` and `prompts/answer_v1.txt` provide the offline `StubLLM`, optional Ollama/OpenAI-compatible adapters, strict JSON schema validation, and A2 citation verification against retrieved IDs.
- **Part E — A1 Abstention, Privacy & Fallback:** `src/assistant_core/guard.py` and `rag/answerer.py` block third-party private requests before retrieval, abstain when evidence is missing or below `RETRIEVAL_MIN_SCORE=2.0`, retry once on provider/grounding failure, and fall back safely to the top retrieved chunk (`degraded=True`).
- **Service, CLI & FastAPI Integration:** `create_service(settings)` keeps `RAG_ENABLED=false` by default for Lab 03–05 contract compatibility. Set `RAG_ENABLED=true` (with offline `LLM_PROVIDER=stub` by default) to run RAG across both CLI and FastAPI:

```bash
# Windows PowerShell (from assistant_core_lab/)
$env:RAG_ENABLED="true"; python -m assistant_core "I lost my student card"

# macOS/Linux (from assistant_core_lab/)
RAG_ENABLED=true python -m assistant_core "I lost my student card"
```

- **Part F, H1 & H2:** `eval/cases.jsonl` contains 25 cases (20 starter + 5 H1: 3 grounded normal + 2 abstention). `eval/compare_paths.py` compares the deterministic, retrieval, and LLM paths on the same 25 cases; results, three-sentence recommendation, failure analysis, and reflection are documented in `docs/lab6/path_comparison.md` alongside per-member evidence under `docs/lab6/members/`.

## Lab 05 Deliverables

### Part E — R1 and R2 feedback persistence

- R1 `add_feedback()` is implemented in `src/assistant_api/db.py`.
- R2 `list_feedback()` is implemented in `src/assistant_api/db.py`.
- Both endpoints use the integrated SQLite repository and survive application restarts.
- Run the focused tests above to verify validation, persistence, ordering, limits, and admin protection.

### Part F — SQL analytics

The three SQL deliverables are in `sql/my_queries.sql`:

- F1: request count per intent.
- F2: average latency per intent.
- F3: topic with the most thumbs-down feedback.

To prepare a local database with the schema and synthetic interactions:

```bash
python scripts/migrate.py assistant.db
python scripts/seed.py assistant.db 300
```

Then execute `sql/my_queries.sql` using a SQLite client, for example:

```bash
sqlite3 assistant.db < sql/my_queries.sql
```

The seed data is synthetic and contains no real student messages.

## Development Workflow

Use a dedicated branch and pull request for each task. Before merging or submitting,
run Ruff, the full pytest suite, and the Lab 07 warm-up tests (`practice/test_hello_streamlit.py`),
review the changed files, and confirm that the integrated implementation under
`assistant_core_lab/` is the source of truth.

The Lab 07 release tag (`v0.7-mvp`) is created by the Team Lead on `main` only after the final
integration PR is merged and GitHub Actions CI passes on `main`.

**Course:** CSC10014 — Practical Track

**Institution:** University of Science, VNU-HCM
