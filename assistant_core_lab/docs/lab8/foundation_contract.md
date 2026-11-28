# Lab 08 Foundation Contract — Team 3

## Status and source baseline

- Branch: `feat/lab08-foundation-phat`, published in PR #81 against `main`.
- Repository base: `chp0703/assistant-core-team3` commit `c88ef2984dd5a5694a24e9b23fd41d655998621e`.
- Official source: [`CSC10014-at-fit-hcmus/public_materials/lab08`](https://github.com/CSC10014-at-fit-hcmus/public_materials/tree/397639e11ac3bb47516d5de8211ccbfb3955794a/lab08), source commit `397639e11ac3bb47516d5de8211ccbfb3955794a`.
- Imported all 69 official files under `public_materials/lab08/`; their contents were checked against the official source blobs and left unchanged. This path is reference material; active work is under `assistant_core_lab/`.
- Foundation/H1/H2 implementation commit: `58273bbb76748b974e4471017c18ee15cc16827c`. Runner report-path follow-up: `8baddb279e12d6282427de36920d8d2e5296d7bb`.

## Working tree and ownership handoff

| Path | Contract and next owner |
|---|---|
| `assistant_core_lab/practice/grades_utils.py`, `test_grades_utils.py`, `practice/bug_reports/BUG-1.md`–`BUG-3.md` | Starter copies for Hương. Keep the seeded bugs until her work; Phát did not modify their behavior. |
| `assistant_core_lab/redteam/cases.jsonl` | Official 12 cases, unchanged. |
| `assistant_core_lab/redteam/run_redteam.py` | Compatibility adapter owned by Foundation. Uses the real service and API, an offline stub, local data, and a fresh in-memory SQLite database for each case. It judges refusal using the internal `RagResult` and verifies that internal `path` is absent from public JSON. |
| `assistant_core_lab/tests/test_my_regressions.py` | Official regression template for Khang; only its starter greeting control is active. |
| `assistant_core_lab/worksheets/bug_report_template.md`, `failure_catalogue.md`, `redteam_exchange.md` | Official worksheet copies for Khôi. |
| `assistant_core_lab/tests/conftest.py` | Shared offline fixtures below. The narrower `tests/api/conftest.py` and its API fixture behavior are unchanged. |
| `assistant_core_lab/docs/lab8/members/chp0703/` | Phát's H1 test/report; H2 path is reserved for Phát's personal reflection and remains pending. |

No active copy of the starter `src/`, API security tests, or other members' production files was added. No seeded bug, G1 guard, or Khang-owned `route()` implementation was changed.

## Shared fixture contract

Defined in `tests/conftest.py`:

- `settings(tmp_path: Path) -> Settings`: absolute project data paths, per-test SQLite file, fake credentials, and stub LLM; RAG disabled by default.
- `rag_settings(settings: Settings) -> Settings`: opt-in RAG settings for local knowledge files.
- `service(settings: Settings) -> AssistantService`: fresh offline service.
- `rag_service(rag_settings: Settings) -> AssistantService`: fresh offline service with RAG enabled.
- `isolated_repo(settings: Settings)`: initialized per-test repository whose engine is disposed at teardown.

Tests do not require network access or live credentials. The API subdirectory retains its more-specific fixtures.

## Red-team runner contract and baseline

Run from `assistant_core_lab/`:

```text
python redteam/run_redteam.py [cases.jsonl] [--report PATH]
```

The cases path defaults to the official `redteam/cases.jsonl`. Unless `--report` is supplied, the runner writes to a unique Markdown file in the system temp directory and prints its path to stderr, avoiding Khôi's `redteam/report.md` and `report_partner.md`. The report has one row per case; exit status is zero only when every case passes.

Pre-G1 actual result: **10/12 pass**, exit status 1. R01 (retrieved prompt injection) and R03 (DAN-style fee question) fail; the adapter reports these honestly for Hiển/Hùng to assess. Other privacy, out-of-scope, malformed-input, fee-manipulation, normal-control, and degraded-service cases pass. No final-integrated 12/12 result is claimed.

## Verification evidence

Commands were run from `assistant_core_lab/`:

| Command | Result |
|---|---|
| `python -m pytest -q -ra` | **420 passed**, one existing Starlette/AnyIO deprecation warning. |
| `python -m pytest -q tests/test_h1_phat.py` | **8 passed**. |
| `python -m pytest -q practice/test_grades_utils.py` | **4 passed** on seeded starter behavior. |
| `python -m pytest -q practice/test_hello_streamlit.py` | **4 passed**. |
| `ruff check .` | Passed after a per-file B006 ignore was added only for the intentionally seeded `practice/grades_utils.py`; Hương should remove that exception with the bug fix. |
| Ruff on `tests/conftest.py`, `redteam/run_redteam.py`, and `tests/test_h1_phat.py` | Passed with default rules. |
| `git diff --check` | Passed before local commits. |

The runner baseline was executed after the compatibility adapter change; its two failures are expected before G1 work and are not hidden with skips or xfails.

## H1 and H2 deliverables

- H1 files: `tests/test_h1_phat.py` and `docs/lab8/members/chp0703/h1_result.md`.
- H1 targets `AssistantService._execute`, added by Phát in commit `d3303bc787ec17532b574fc7c280f7d01142920`. The earlier Codex AI-use entry names `service.py` for the Help work but does not identify this later function specifically. Khang's `route()` was excluded based on its Khang-owned history. The 8 H1 test instances pass without a production change. **Phát must confirm the function's prior AI provenance before treating the H1 provenance requirement as satisfied.**
- H2 file: `docs/lab8/members/chp0703/h2_reflection.md` is an explicit placeholder. H2 remains incomplete until Phát reads the assigned pytest and OWASP pages and writes exactly two personal English sentences. The former AI-written text was removed after review feedback.
- `docs/ai-use-log.md` records the work, evidence, and provenance limits without inventing authorship.

## Scope boundary

This branch contains Phát's Foundation work and H1 tests in PR #81. It is related to issue #83, which records Hương's dependency on the Foundation handoff. H2 remains pending Phát's personal work. This branch does not perform P6/Final Integration, modify root `README.md` or GitHub Actions, or create a release tag.
