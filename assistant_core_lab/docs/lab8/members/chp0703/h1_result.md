# Lab 08 — H1: `AssistantService._execute`

- Member: `chp0703`
- Source file / signature: `src/assistant_core/service.py`, `AssistantService._execute(self, text: str) -> tuple[Response, RagResult | None]`
- Earlier AI-use log entry / PR / commit: Phát's AI-use log was added in commit `677630d` (2026-10-23) and lists `service.py` among Codex-assisted Help files. Phát added `_execute` later in commit `d3303bc787ec17532b574fc7c280f7d01142920` (2026-11-16). The earlier file-level entry does not prove that Codex wrote this later function, so the function-level H1 provenance requirement is **not verified**.
- What was originally generated or modified: PR #61 added the RAG-aware service execution path that checks recognized privacy requests before routing, then returns a public response and optional internal `RagResult`.
- Current contract: `_execute` accepts request text, dispatches deterministic greeting/fee/office behavior, uses RAG for rule requests when enabled, and returns `(Response, RagResult | None)`. Public message length and blank-input validation belong to the `Message`/API boundary.
- Test file: `tests/test_h1_phat.py`
- Before commit / environment / command / actual result: Repository base `c88ef2984dd5a5694a24e9b23fd41d655998621e`; Python 3.12.2; project `.venv`; from `assistant_core_lab/`, `.\.venv\Scripts\python.exe -m pytest -q tests/test_h1_phat.py` — 8 passed.

| Test name | Input/setup | Expected | Actual before | Actual after |
|---|---|---|---|---|
| `test_execute_empty_text_returns_unknown_without_rag` | Empty text; RAG disabled | Unknown response; no RAG result | Pass | Pass; full suite included this test |
| `test_execute_zero_credit_request_keeps_fee_validation_in_the_tool` | `tuition for 0 credits` | Fee intent; invalid-credit response; no RAG result | Pass | Pass; full suite included this test |
| `test_execute_large_text_does_not_bypass_message_boundary` | 5,000-character text passed directly to the internal method | No crash; unknown response; API length validation remains at its boundary | Pass | Pass; full suite included this test |
| `test_execute_vietnamese_fee_uses_deterministic_calculation` | `Tính học phí cho 18 tín chỉ` | Fee intent and deterministic `8,100,000 VND` response | Pass | Pass; full suite included this test |
| `test_execute_rejects_non_string_text_with_type_error` | `None`, integer, and bytes | Raise `TypeError` | Pass for all 3 inputs | Pass for all 3 inputs; full suite included this test |
| `test_execute_greeting_control_remains_deterministic` | Padded `HI!` | Greeting response; no RAG result | Pass | Pass; full suite included this test |

- Defect / root cause: No behavior defect found in the tested cases.
- Fix or replacement: None; changing the production function was not warranted.
- After local commit / command / actual result: Implementation and H1 artifacts are in `58273bbb76748b974e4471017c18ee15cc16827c`; the runner's safe report-path follow-up is `8baddb279e12d6282427de36920d8d2e5296d7bb`. After both commits, `python -m pytest -q -ra` from `assistant_core_lab/` passed **420 tests** (one existing Starlette/AnyIO deprecation warning), including all 8 H1 test instances.
- Decision: Retain the function behavior. The tests establish the listed behavior, but the available repository history does not establish that `_execute` was AI-written. This is an explicit H1 provenance gap, not a passing provenance claim.
- Remaining limitations: This targets an internal service method; the large/empty cases bypass the public `Message` validation intentionally to test the method boundary. It does not test G1 injection behavior.
- Required disclosure: Codex created these tests and this report. The function was selected because its implementation commit belongs to Phát and Khang's `route()` was excluded; no claim is made that function-level AI authorship has been proven.
