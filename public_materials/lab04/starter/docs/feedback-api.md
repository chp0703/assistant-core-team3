# Lab 04: Feedback API (T2, T3) and offices endpoint (H1)

## Feedback

- `POST /v1/feedback`: body `request_id` (string), `rating` (-1, 0 or 1), optional `comment`.
  Returns 201 with the saved item (`id`, `created_at` added by the server). A rating outside -1..1 returns 422.
- `GET /v1/feedback`: admin only. Send `X-API-Key` equal to `API_ADMIN_KEY` from `.env`; otherwise 401.
- Feedback lives in an in-memory list and is lost on restart (Lab 5 adds a database).

## Offices (H1)

- `GET /v1/offices`: 200 with every office as `{name, room, hours}`, sorted by name.

## Checks

```bash
python -m pytest -q tests/test_api.py -k "feedback or offices"
```
