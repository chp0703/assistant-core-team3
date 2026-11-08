# Study Assistant — backend (Lab 5 reference)

## Setup
```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
cp .env.example .env
```
## Run the API
```
uvicorn assistant_api.main:create_app --factory --reload
```
Open http://127.0.0.1:8000/docs for the interactive OpenAPI documentation.

## API contract (v1)
| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | — | 200 `{"status":"ok","version":...}` | — |
| POST | `/v1/chat` | `{"message": str 1–2000, "session_id": str}` | 200 `{answer, intent, sources[], degraded, request_id}` | 422 invalid, 429 rate limit |
| POST | `/v1/feedback` | `{"request_id": str, "rating": -1/0/1, "comment"?: str ≤500}` | 201 feedback with `id`, `created_at` | 404 unknown request ID, 422 invalid input |
| GET | `/v1/feedback` | header `X-API-Key` | 200 list | 401 |
| GET | `/v1/stats/intents` | header `X-API-Key` | 200 `[{intent, requests, avg_latency_ms, unresolved}]` | 401 |
| GET | `/v1/weather` | — | 200 `{temperature_c, wind_kmh, description, observed_at, stale}` | 503 upstream down |

All errors use one shape: `{"error": {"code": "...", "message": "..."}}`.

## Database (Lab 5)
```
python scripts/migrate.py assistant.db      # apply sql/migrations in order
python scripts/seed.py assistant.db 300     # synthetic data only
sqlite3 assistant.db < sql/queries.sql      # the five queries + product questions
```
New endpoint: `GET /v1/stats/intents` (header `X-API-Key`). `POST /v1/feedback` now returns 404 for an unknown `request_id`.

## Tests
```
pytest -q                          # unit + API tests (external API mocked)
bash api-tests/curl_tests.sh       # manual tests against a running server
```
Postman / Bruno: import `api-tests/study-assistant.postman_collection.json`.

### R1 - save feedback

Send a chat request first, then use its `request_id` in `POST /v1/feedback`.
`Repository.add_feedback()` saves feedback for an existing interaction and returns
the database-generated ID and timestamp. Unknown request IDs return 404 without
saving a row. Rating and comment validation use the existing API schema.

Run the R1 API, repository, and SQLite persistence checks from this directory:

```
python -m pytest -q tests/test_add_feedback.py tests/test_db.py
python -m ruff check tests/test_add_feedback.py
```

The persistence check closes the engine and opens the same database file again.
The full feedback roundtrip also requires R2 (`list_feedback()`); run the full
suite after integrating that task. Repository CI currently runs Lab 3 only, so
run the Lab 5 commands above separately.
