# CSC10014 — Smart Virtual Assistant (Labs 03–06)

This repository contains the team's integrated implementation for CSC10014 Practical Track.
Lab 03 introduced the modular `assistant_core` service, Lab 04 added the FastAPI backend,
Lab 05 added SQLite persistence, feedback workflows, and SQL analytics, and Lab 06 adds
Markdown knowledge-base chunking, BM25/TF-IDF/Hybrid retrieval, grounded structured LLM answers
(A2), low-evidence abstention and privacy guardrails (A1), unified CLI/FastAPI integration,
a 25-case evaluation set (H1), and a three-path comparison report (Part F).

The final integrated implementation lives in `assistant_core_lab/`. The folders under
`public_materials/` contain starter materials and references;
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

## Key Features

- Modular assistant with intent routing, tuition calculations, and office and handbook retrieval.
- Typed models, environment-based configuration, and response fallback handling.
- FastAPI REST API for chat, feedback, weather, and offices.
- SQLite persistence for privacy-safe interaction metadata and feedback.
- Admin-protected feedback listing with newest-first ordering and a configurable limit.
- SQL analytics for requests per intent, average latency, and downvoted topics.
- Per-client rate limiting, automated tests, and Ruff checks.
- Markdown knowledge-base chunking (`data/kb/*.md`) with BM25, TF-IDF, and Hybrid retrieval (Part C) plus S1–S3 mini search warm-up (`practice/mini_search.py`).
- Structured LLM adapter (`StubLLM` offline default, optional Ollama/OpenAI-compatible) with A2 citation grounding validation and safe fallback (Part D).
- A1 low-evidence abstention and bilingual privacy guardrails running before retrieval and LLM calls (Part E).
- Unified `create_service(settings)` RAG integration shared by CLI and FastAPI (opt-in via `RAG_ENABLED=true`, preserving Lab 03–05 response contracts).
- Three-path evaluation runner (`eval/compare_paths.py`), 25-case H1 dataset (`eval/cases.jsonl`), and comparison + H2 reflection report (`docs/lab6/path_comparison.md`).

## Technology Stack

Python 3.10+, FastAPI, Pydantic, HTTPX, SQLModel, SQLite, Uvicorn, python-dotenv,
pytest, Ruff, and setuptools.

## Project Structure

```text
assistant-core-team3/
├── .github/workflows/ci.yml
├── assistant_core_lab/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/
│   │   ├── handbook.json
│   │   ├── offices.csv
│   │   └── kb/                     # Lab 06 sample KB copied from the starter
│   │       ├── handbook_2026.md
│   │       ├── fees_2026.md
│   │       └── services_2026.md
│   ├── eval/
│   │   ├── cases.jsonl             # 25 official evaluation cases (20 starter + 5 H1)
│   │   └── compare_paths.py        # Part F three-path comparison runner
│   ├── practice/
│   │   ├── mini_search.py          # Lab 06 warm-up S1–S3 inverted index & ranking
│   │   └── test_mini_search.py     # Unit tests for S1–S3 mini search
│   ├── docs/
│   │   ├── lab3/                   # Existing Lab 03 documentation
│   │   └── lab6/
│   │       ├── rag_integration_contract.md  # Team 3 Lab 06 integration contract
│   │       ├── path_comparison.md  # Part F comparison table, analysis & H2 reflection
│   │       └── members/            # Per-member Lab 06 evidence & comparisons
│   ├── scripts/                    # Migration and synthetic-data scripts
│   ├── sql/
│   │   ├── migrations/             # Database schema migrations
│   │   └── my_queries.sql          # Lab 05 F1–F3 analytics queries
│   ├── src/
│   │   ├── assistant_core/
│   │   │   ├── __init__.py
│   │   │   ├── __main__.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   ├── router.py
│   │   │   ├── service.py          # Shared CLI and API service (with optional RAG)
│   │   │   ├── knowledge.py
│   │   │   ├── responder.py
│   │   │   ├── tools.py
│   │   │   ├── errors.py
│   │   │   ├── logging_setup.py
│   │   │   ├── guard.py            # Lab 06 privacy guardrails
│   │   │   ├── llm.py              # Lab 06 LLM adapters & A2 grounding check
│   │   │   ├── prompts/
│   │   │   │   └── answer_v1.txt   # Versioned prompt template
│   │   │   └── rag/
│   │   │       ├── __init__.py
│   │   │       ├── types.py        # Shared internal RagResult & RagPath types
│   │   │       ├── chunker.py      # Part C Markdown chunking & metadata
│   │   │       ├── index.py        # Part C BM25, TF-IDF, and Hybrid retrieval
│   │   │       └── answerer.py     # Part E RagAnswerer, A1 abstain & fallback
│   │   └── assistant_api/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── db.py
│   │       ├── schemas.py
│   │       ├── weather.py
│   │       └── ratelimit.py
│   └── tests/
│       ├── test_rag.py             # Lab 06 end-to-end RAG, CLI & API tests
│       ├── test_rag_retrieval.py   # Part C chunker & retrieval tests
│       ├── test_llm_grounding.py   # Part D / A2 grounding & adapter tests
│       ├── test_rag_answerer.py    # Part E / A1 abstain & fallback tests
│       ├── test_privacy_guard.py   # Privacy guardrail tests
│       ├── test_eval_cases.py      # H1 25-case dataset validation tests
│       ├── test_compare_paths.py   # Part F comparison runner tests
│       ├── api/                    # Existing API and persistence tests
│       └── ...                     # Existing Lab 03–05 unit tests
├── public_materials/
│   ├── lab03/                      # Original Lab 03 materials
│   ├── lab04/                      # Lab 04 starter and practice materials
│   ├── lab05/                      # Lab 05 starter and practice materials
│   └── lab06/                      # Lab 06 starter and practice materials
└── README.md
```

## Setup

From the repository root:

```bash
git clone https://github.com/chp0703/assistant-core-team3.git
cd assistant-core-team3/assistant_core_lab
python -m venv .venv
```

Activate the virtual environment with `.venv\Scripts\Activate.ps1` in Windows
PowerShell or `source .venv/bin/activate` on macOS/Linux. Install the dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env       # Windows PowerShell
# cp .env.example .env            # macOS/Linux
```

For local development, keep `LLM_PROVIDER=stub` and replace `SESSION_SALT` and
`API_ADMIN_KEY` in `.env` with private values.

## Testing and Quality Checks

Run all checks from `assistant_core_lab/`:

```bash
python -m pytest -q
python -m ruff check .
```

The focused Lab 05 and Lab 06 checks are:

```bash
python -m pytest -q tests/api/test_add_feedback.py tests/api/test_api.py tests/test_db.py
python -m pytest -q tests/test_rag.py
python -m pytest -q tests/test_rag.py -k citation
python -m pytest -q practice/test_mini_search.py
python eval/compare_paths.py
```

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

- **Part F, H1 & H2:** `eval/cases.jsonl` contains 25 cases (20 starter + 5 H1: 3 grounded normal + 2 abstention). `eval/compare_paths.py` compares the deterministic, retrieval, and LLM paths on the same 25 cases; results, three-sentence recommendation, failure analysis, and the 5-line H2 reflection are documented in `docs/lab6/path_comparison.md` alongside per-member evidence under `docs/lab6/members/`.

## Run the API

From `assistant_core_lab/`:

```bash
uvicorn assistant_api.main:create_app --factory --reload
```

Open Swagger UI at <http://127.0.0.1:8000/docs>.

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Check API health. |
| POST | `/v1/chat` | Send a message to the assistant and create a persisted interaction. |
| POST | `/v1/feedback` | Save feedback for an existing `request_id`; returns 404 for an unknown ID. |
| GET | `/v1/feedback` | List saved feedback newest first; requires `X-API-Key`. |
| GET | `/v1/weather` | Get campus weather. |
| GET | `/v1/offices` | List campus offices. |

Send a chat request first, then use its returned `request_id` when submitting feedback.
The feedback rating must be `-1`, `0`, or `1`; comments are optional and limited to 500
characters. The list endpoint accepts an optional `limit` parameter, defaulting to 100.

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
run the full test suite and Ruff, review the changed files, and confirm that the
integrated implementation under `assistant_core_lab/` is the source of truth.

The Lab 06 release tag (`v0.6-ai`) is created separately after the final review and merge.

**Course:** CSC10014 — Practical Track

**Institution:** University of Science, VNU-HCM
