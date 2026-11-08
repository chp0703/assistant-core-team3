# CSC10014 — Smart Virtual Assistant (Lab 03 & Lab 04)

In Lab 03, we refactored the original monolithic program into a modular Python service named `assistant_core`. Lab 04 extends that Week 3 service with a FastAPI backend in `assistant_core_lab`.

During the initial development of Lab 04, we implemented the API endpoints in `public_materials/lab04/starter/`. We later integrated the completed API into our existing Week 3 project under `assistant_core_lab/src/assistant_api/` to meet the assignment requirement of extending the original `assistant_core` service.

The `public_materials/lab04/` directory is kept for reference, while **`assistant_core_lab/` contains the final integrated implementation** for Lab 03 and Lab 04.

## Team Members

| No. | Full Name               | GitHub                                                             | Student ID |
| :-: | ----------------------- | ------------------------------------------------------------------ | :--------: |
|  1  | Châu Hòa Phát           | [@chp0703](https://github.com/chp0703)                             |  25127224  |
|  2  | Huỳnh Nguyễn Thế Hiển   | [@AIVIETNAM-AIO-TheHien](https://github.com/AIVIETNAM-AIO-TheHien) |  25127327  |
|  3  | Phạm Hùng Khôi          | [@phkhoiit-1508](https://github.com/phkhoiit-1508)                 |  25127390  |
|  4  | Nguyễn Trần Minh Khang  | [@kentlatoi](https://github.com/kentlatoi)                         |  25127369  |
|  5  | Nguyễn Ngọc Thanh Hương | [@thanhhuong107](https://github.com/thanhhuong107)                 |  25127197  |
|  6  | Đặng Minh Hùng          | [@dmh612](https://github.com/dmh612)                               |  25127340  |

## Key Features

- Modular assistant with intent routing, tuition calculations, and office and handbook retrieval.
- Typed models, environment-based configuration, and response fallback handling.
- FastAPI REST API with chat connected to the Week 3 service.
- Feedback submission and admin-protected feedback listing.
- Campus weather with fallback handling and an office directory endpoint.
- Per-client rate limiting for chat.
- Automated tests and code quality checks.

## Technology Stack

Python 3.10+, FastAPI, Pydantic, HTTPX, Uvicorn, python-dotenv, pytest, Ruff, and setuptools.

## Project Structure

```text
assistant-core-team3/
├── .github/workflows/ci.yml
├── lab03/                         # Original Lab 03 materials
├── public_materials/lab04/        # Lab 04 reference and starter materials
├── assistant_core_lab/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/                       # Office and handbook data
│   ├── docs/                       # Lab 03 documentation
│   ├── src/
│   │   ├── assistant_core/         # Week 3 service
│   │   │   ├── config.py
│   │   │   ├── knowledge.py
│   │   │   └── service.py
│   │   └── assistant_api/          # Integrated Lab 04 API
│   │       ├── main.py
│   │       ├── weather.py
│   │       └── ratelimit.py
│   └── tests/
│       ├── test_service.py         # Original Week 3 tests
│       └── api/                    # Lab 04 API tests
└── README.md
```

## Setup and Testing

```bash
git clone https://github.com/chp0703/assistant-core-team3.git
cd assistant-core-team3/assistant_core_lab
python -m venv .venv
```

Activate the virtual environment with `source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\Activate.ps1` in Windows PowerShell. Then install and test:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
python -m ruff check .
```

Start the integrated API from `assistant_core_lab/`:

```bash
uvicorn assistant_api.main:create_app --factory --reload
```

Swagger UI is available at <http://127.0.0.1:8000/docs>.

### API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Check API health. |
| POST | `/v1/chat` | Chat with the Week 3 assistant. |
| POST | `/v1/feedback` | Persist feedback for an existing chat request; 404 for an unknown ID, 422 for invalid input. |
| GET | `/v1/feedback` | List saved feedback newest first with an admin API key. Optional `limit` defaults to 100. |
| GET | `/v1/weather` | Get campus weather. |
| GET | `/v1/offices` | List campus offices. |

POST `/v1/chat` is rate-limited per client and returns HTTP 429 when the limit is exceeded.

### Lab 05 - feedback persistence and listing (R1 and R2)

The R1 implementation lives in `assistant_core_lab/src/assistant_api/db.py`.
`POST /v1/feedback` calls the repository and returns the saved feedback with its
database-generated ID and timestamp. Send a chat request first and use the
returned `request_id` when submitting feedback.

Run these checks from `assistant_core_lab/`:

```bash
python -m pytest -q tests/api/test_add_feedback.py tests/api/test_api.py tests/test_db.py
python -m ruff check .
```

R1 tests cover API validation, SQLite writes, rejected requests that insert no
rows, and persistence after reopening a database file. R2 reads saved feedback
from SQLite, including feedback submitted by an earlier app instance.

## Development Workflow

Team members use GitHub Issues, dedicated branches, Pull Requests, and peer reviews to manage contributions. GitHub Actions runs pytest and Ruff. Lab 04 extends the Week 3 project without changing the original Week 3 tests.

Individual deliverables include the maintainability worksheet and AI extension review. Team deliverables include the `assistant_core` package, integrated API, and architecture documentation.

**Course:** CSC10014 — Practical Track, Lab 03 & Lab 04

**Institution:** University of Science, VNU-HCM
