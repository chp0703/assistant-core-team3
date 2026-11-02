# T5 - Chat rate limiting (dmh612)

Branch: `feat/lab04-dmh612-ratelimit`.

## Behaviour and API contract

`POST /v1/chat` admits at most `RATE_LIMIT_PER_MIN` requests from the same peer
IP in a rolling 60-second window. The default is 30. Set a positive integer in
`.env` or the environment before starting the API, for example:

```dotenv
RATE_LIMIT_PER_MIN=5
```

After five admitted requests, the next valid chat request from that peer returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
```

```json
{"error":{"code":"rate_limit_exceeded","message":"Rate limit exceeded"}}
```

The service is not invoked for a rejected request. Invalid request bodies receive
422 before consuming quota. Other endpoints, including `/health`, are not subject
to this chat quota. Changing `session_id` or adding `X-Forwarded-For` does not
change the application's key: it uses `request.client.host` supplied by ASGI.
If the ASGI request has no peer address, it uses the shared key `unknown`.

A hit expires at exactly 60 seconds. Rejected requests do not consume quota or
extend the window. Hits expire individually, rather than resetting every
wall-clock minute. Example for a limit of two:

| Time | Result |
| --- | --- |
| 0 s | first hit allowed |
| 30 s | second hit allowed |
| 59 s | rejected with 429 |
| 60 s | first hit expires; one new hit allowed |
| 90 s | second hit expires; one new hit allowed |

## Implementation

`ratelimit.py` stores a deque of monotonic timestamps per client. A lock makes
expiry, quota checking, and insertion atomic across synchronous request threads.
A clock can be injected into `RateLimiter` for deterministic boundary tests.
The limiter is constructed once per application instance, not per request.
Invalid budgets (zero, negative, boolean, or non-integer) fail at construction.

`main.py` checks the limiter immediately before Hien's existing T1 service call.
The Chat API, feedback endpoints, and offices endpoint from the current main
revision are preserved. The skipped starter rate-limit test is enabled.

## Testing

From `public_materials/lab04/starter`:

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
python -m ruff check src/assistant_api/main.py src/assistant_api/ratelimit.py tests/test_ratelimit.py tests/test_api.py
python -m pytest -q tests/test_ratelimit.py tests/test_chat.py tests/test_api.py -k "not weather"
```

Verified locally on 2026-11-02, Python 3.12.14, using the pinned requirements:
**36 passed, 3 deselected**; the Ruff command above passed.
The new limiter tests cover exact quota, separate keys, sliding expiry at 60 s,
rejected attempts, concurrent requests, the 429 error contract, service call
counts, invalid bodies, independent app instances, and distinct ASGI peer IPs.
No sleep or external weather calls are needed in the limiter tests.

## Integration and deployment limits

Dependency T1 is available on main through Hien's PR #22. The base revision used
for this change is `c54d9c0`. Weather T4 remains a separate task (PR #32) and is
not required by T5. Run the full suite again when the team integrates T4.
The current repository workflow checks `assistant_core_lab` (Lab03); these
Lab04 checks must also be run explicitly before relying on a CI result.

This is the lab's in-memory, per-process limiter. Restarting the app resets it;
separate workers do not share budgets. All sessions behind the same peer IP
share one budget. Configure trusted proxy forwarding at the ASGI server when
using a reverse proxy. Client-key entries are retained for the app lifetime;
this implementation is intended for the lab's small client set.
