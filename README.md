# CSC10014 — Smart Virtual Assistant (Labs 03–05)

This repository contains the team's integrated implementation for CSC10014 Practical Track.
Lab 03 introduced the modular `assistant_core` service, Lab 04 added the FastAPI backend,
and Lab 05 adds SQLite persistence, feedback workflows, and SQL analytics.

The final integrated implementation lives in `assistant_core_lab/`. The folders under
`public_materials/` and `.lab05-reference/` contain starter materials and references;
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

## Technology Stack

Python 3.10+, FastAPI, Pydantic, HTTPX, SQLModel, SQLite, Uvicorn, python-dotenv,
pytest, Ruff, and setuptools.

## Project Structure

```text
assistant-core-team3/
├── .github/workflows/ci.yml
├── lab03/                         # Original Lab 03 materials
├── public_materials/lab05/        # Lab 05 starter and practice materials
├── .lab05-reference/              # Reference copy of Lab 05 materials
├── assistant_core_lab/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/                       # Office and handbook data
│   ├── docs/                       # Architecture and AI-use documentation
│   ├── scripts/                    # Migration and synthetic-data scripts
│   ├── sql/
│   │   ├── migrations/             # Database schema migrations
│   │   └── my_queries.sql          # Lab 05 F1–F3 analytics queries
│   ├── src/
│   │   ├── assistant_core/         # Modular assistant service
│   │   └── assistant_api/          # Integrated FastAPI and database layer
│   └── tests/                      # Service, API, database, and persistence tests
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

The focused Lab 05 checks are:

```bash
python -m pytest -q tests/api/test_add_feedback.py tests/api/test_api.py tests/test_db.py
```

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

The Lab 05 release tag is created separately after the final review and merge.

**Course:** CSC10014 — Practical Track

**Institution:** University of Science, VNU-HCM
