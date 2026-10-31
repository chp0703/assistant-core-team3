# Lab 04: Chat API (T1)

Branch: `feat/lab04-AIVIETNAM-AIO-TheHien-chat`.

This contribution implements the assigned Chat API (T1).
Feedback (T2/T3), weather (T4), and bonus rate limiting remain separate team tasks.

## Request and response

- `message`: required string, 1-2000 characters.
- `session_id`: optional string, at most 64 characters; default `anonymous`.
- Success: 200 with `answer`, `intent`, `sources`, `degraded`, and `request_id`.
- `request_id`: a new 12-character hexadecimal ID for each accepted request.
- Invalid input: 422 with `{"error":{"code":"invalid_request","message":"..."}}`.

The endpoint delegates to the existing Lab 3 service and preserves its sources and degraded flag.
The existing schemas and error handlers define validation; this contribution does not change the contract.
The declared 429 response is reserved for the separate rate-limiting task.

## Automated checks

Run these commands from `public_materials/lab04/starter` with its virtual environment active:

```bash
python -m pytest -q tests/test_chat.py tests/test_api.py::test_health tests/test_api.py::test_chat_fee tests/test_api.py::test_chat_validation_error
python -m ruff check tests/test_chat.py
```

Verified locally with Python 3.12 and the supplied pinned requirements:

- Focused health/chat checks: **16 passed** (13 new cases plus 3 supplied checks).
- Full starter suite: **33 passed, 3 failed, 1 skipped**.
- The remaining failures are `test_feedback_roundtrip` (T2), `test_weather_ok` (T4),
  and `test_weather_down_returns_503` (T4). The rate-limit bonus remains skipped.
- Ruff passes for the new chat tests.
- `main.py` still has five pre-existing Ruff findings for unused T2/T4/bonus imports and variables.
  They remain visible for their respective owners; no lint rules or tests were disabled.

The existing repository CI runs `assistant_core_lab` (Lab 3), so its status alone does not validate Lab 4.

## Manual checks

A real local uvicorn run verified `/health`, `/docs`, and `/openapi.json` (200),
plus curl chat requests for fees and offices (200) and empty/wrong-type messages (422).
The temporary server was stopped after verification.

From `public_materials/lab04/starter`, start the API using the default stub provider:

```bash
python -m uvicorn assistant_api.main:create_app --factory --reload
```

Open `http://127.0.0.1:8000/docs`, expand `POST /v1/chat`, and use **Try it out**:

```json
{"message":"tuition for 18 credits and 2 retake","session_id":"demo"}
```

Expect 200, intent `fee`, an answer containing `9,450,000`, and a populated `request_id`.
Try `{"message":""}` to verify the 422 error envelope.

The following curl commands work in Git Bash:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/chat -H 'Content-Type: application/json' -d '{"message":"where is the library"}'
curl -s -X POST http://127.0.0.1:8000/v1/chat -H 'Content-Type: application/json' -d '{"message":""}'
```

The full `api-tests/curl_tests.sh` also calls feedback and weather; it requires those team tasks
for all expected responses to match. New automated chat checks do not call the external weather API.
