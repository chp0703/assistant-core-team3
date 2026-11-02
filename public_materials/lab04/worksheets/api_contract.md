# Lab 4 — API contract worksheet

Fill in one row per endpoint **before** you code it.

| Method | Path | Request body / params | Success (code + body) | Errors (code + error.code) | Who calls it |
|---|---|---|---|---|---|
| GET | /health | — | 200 {status, version} | — | ops, UI |
| POST | /v1/chat | JSON: message (1–2000 characters), session_id (optional, max 64) | 200 {answer, intent, sources[], degraded, request_id} | 422 invalid_request; 429 rate_limit_exceeded | UI, tests |
| POST | /v1/feedback | | | | UI |
| GET | /v1/feedback | header X-API-Key | | | staff dashboard |
| GET | /v1/weather | — | | | UI |

Questions:
1. Which fields are required, and what are their limits?
2. What does the UI show for each error code?
3. What changes would force a `/v2`?

## T5 — Rate limiting (dmh612)

POST /v1/chat is limited per peer IP address to RATE_LIMIT_PER_MIN accepted
requests in a rolling 60-second window (default 30). The next request receives
HTTP 429 with `{"error":{"code":"rate_limit_exceeded","message":"Rate limit exceeded"}}`.
A hit expires exactly 60 seconds after acceptance. Rejected requests do not
extend the window. Invalid request bodies return 422 before consuming quota.
Changing session_id or sending X-Forwarded-For does not create a new quota.
The UI should keep the draft message, show the rate-limit message and allow
the user to retry after the oldest accepted request expires.
