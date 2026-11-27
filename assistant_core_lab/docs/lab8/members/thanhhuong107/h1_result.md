# H1 - Prove it, or replace it

- Member: Hương (`@thanhhuong107`)
- Function: `setup_logging()` in [logging_setup.py](../../../../src/assistant_core/logging_setup.py)
- Tests: [test_h1_huong.py](../../../../tests/test_h1_huong.py)
- Provenance: the [Lab 03 AI-use log](../../../ai-use-log.md) and [logging review](../../../lab3/members/thanhhuong107/ai_extension_review.md) document Codex-assisted logging setup, including handler reuse and stream injection. The implementation was added in commit `786565a`. The original AI draft was not saved.

| Case | Verified behavior |
| --- | --- |
| Defaults | INFO threshold, one JSON record on stderr, no propagation to parent handlers |
| Reconfiguration | Lowercase level is accepted, the threshold changes, and the same handler writes to the new stream |
| Zero | `latency_ms=0` is retained as an integer |
| Very large value | `latency_ms=10**30` survives the JSON round trip exactly |
| Vietnamese text | The message remains readable in JSON and decodes unchanged |
| Empty level | An empty string raises `ValueError` before a handler is attached |
| Wrong type | A non-string level is rejected before a handler is attached |

Result: **7 passed** with Python 3.12. The two existing logging tests also
passed. The tests isolate the named logger and restore its configuration after
each case. No production change to `setup_logging()` was needed.
