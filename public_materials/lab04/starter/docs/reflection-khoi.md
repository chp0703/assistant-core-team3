# H2 — Reflection (Pham Hung Khoi)

In Lab 3, `service.handle()` is a Python function call: caller and service share one process, and the caller passes Python objects directly.
`POST /v1/chat` is the same logic reached over HTTP, so the input is JSON that must be validated and the output is JSON plus a status code.
Errors become status codes (422, 401, 503) instead of exceptions, and each answer gets a `request_id` that can be rated later.
A team prefers HTTP because any client (web UI, phone app, tests, other services) can use the assistant without importing our Python code.
It also gives one documented contract (`/docs`), so frontend and backend can be built and tested independently.
