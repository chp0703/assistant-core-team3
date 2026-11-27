# Lab 08 — H1: `format_sources()`

- Member: `AIVIETNAM-AIO-TheHien`.
- Source and signature: `ui/logic.py`, `format_sources(sources: list[dict]) -> str`.
- AI provenance: Gemini 4 Hydrogen generated the Lab 07 implementation via Antigravity CLI. Its recorded output matches the function body in [commit `e9d1814`](https://github.com/chp0703/assistant-core-team3/commit/e9d1814b294f5e63f6d9a2d1d1d4af01d8a64110), which replaced the starter stub in [PR #70](https://github.com/chp0703/assistant-core-team3/pull/70).
- Contract: Format the available string IDs and titles in input order. Omit records with both fields empty. Return an empty string if there are no citations.
- Test file: `tests/test_h1_hien.py`.

From `assistant_core_lab/` with the project virtual environment (Python 3.13.14), both runs used `python -m pytest -q -p no:cacheprovider tests/test_h1_hien.py`.

| Test | Expected | Before G1 on `4fac653` | After G1 on the same stack |
| --- | --- | --- | --- |
| `test_format_sources_skips_empty_entries_without_extra_separators` | Empty records between two citations leave one separator. | Pass | Pass |
| `test_format_sources_preserves_string_zero_identifier` | String ID `"0"` is retained without a title. | Pass | Pass |
| `test_format_sources_preserves_order_and_count_for_1000_records` | All 1,000 citations appear in input order. | Pass | Pass |
| `test_format_sources_preserves_vietnamese_text` | Vietnamese characters remain intact in both citations. | Pass | Pass |
| `test_format_sources_raises_type_error_for_none_container` | `None` raises `TypeError`. | Pass | Pass |
| `test_format_sources_raises_attribute_error_for_non_dict_member` | A string record raises `AttributeError`. | Pass | Pass |

Both runs returned exit code `0` with **6 passed**. The formatter source had the same Git blob before and after. The cases exercised the current contract without finding a defect, so the Lab 07 implementation was retained. The wrong-type tests document failures for invalid direct calls. The string `"0"` is the supported zero identifier.

Lab 08 disclosure: Antigravity CLI with Gemini 4 Hydrogen generated standalone classifier and test examples from a generic specification. Codex adapted and reviewed the examples, integrated the guard, ran the checks, and drafted H2 for member review. Phát can use this record to consolidate the H1 result into `docs/ai-use-log.md`.
