# H1 — AI Extension Review

## 1. Student Information and Feature Overview

- **Student:** Nguyễn Trần Minh Khang
- **GitHub username:** `kentlatoi`
- **Feature:** Vietnamese Tuition Request Support

This H1 feature extends Minh Khang's tuition work without changing the English interface. For
example, `Học phí cho 18 tín chỉ và 2 tín chỉ học lại` is routed to `Intent.FEE`, parsed as
`(18, 2)`, and calculated by the existing `tuition()` function as **9,450,000 VND**. The feature
also supports case changes, extra spaces, composed or decomposed Vietnamese Unicode, and reversed
regular/retake label order.

## 2. AI Tool and Prompt

The AI tool used was **OpenAI Codex**. The executed prompt asked Codex to implement Vietnamese
tuition routing and labelled credit parsing in two passes. It required reuse of `Intent`,
`InvalidRequest`, and `tuition()`; preservation of English behavior; no hard-coded rate, new
dependency, or raw-question logging; and tests for Unicode, whitespace, reversed labels, missing
values, ambiguous numbers, false-positive routing, and regressions. It also required a separate
review of the initial generated version before improvement.

## 3. Implementation and Review

The initial AI-generated version added a literal `"học phí"` routing check and two Vietnamese
regular expressions in `parse_credits()`. It included three basic Vietnamese tests, and the focused
suite had **13 passing tests**. A second Codex review used additional edge-case probes, then updated
`router.py`, `tools.py`, `test_router.py`, and `test_tools.py`.

The table records completed changes from that review. It does not claim that Minh Khang has already
performed his own final manual review.

| # | Initial AI-generated code | Problem found | Improvement made | Why it matters |
| --- | --- | --- | --- | --- |
| 1 | `route()` used a direct `"học phí" in t` check. | It missed repeated spaces and decomposed Unicode, and classified `học phím` as a fee request. | Added NFC normalization, `casefold()`, whitespace normalization, and a word-bounded phrase match in `router.py`. | Recognizes real variants while reducing false positives. |
| 2 | Vietnamese parsing independently searched for the first regular and retake values. | It could ignore an extra year, duplicate regular credits, or decomposed accents, making ambiguous input look valid. | Added `_parse_labelled_credits()` to bind each number to its label and reject unlabelled or duplicate numbers with `InvalidRequest`. | Prevents the calculator from silently using the wrong values. |
| 3 | The English fallback used loose, case-sensitive searches. | Uppercase `RETAKE` could be missed, and unrelated numbers such as a year could be ignored. | Reused normalized, label-aware parsing for English and added regression tests. | Preserves English behavior and applies the same ambiguity rules. |
| 4 | `tuition()` validated regular credits only. | A direct call with negative retake credits produced a lower total. | Added a negative-retake check and a failure test. | Protects the deterministic calculation boundary. |

## 4. Technical Checks and Testing

The final design keeps the existing boundaries: `router.py` returns an `Intent`, `tools.py` parses
credits and calculates the fee, and the rate remains a `tuition()` argument. No formula was added to
the router. The feature introduced no dependency, credential, network call, or logging. It does not
record the user's raw question. `service.py` is still a placeholder, so end-to-end service behavior
is outside this H1 evidence.

The original main-lab baseline was **10 assigned-module tests and 60 project tests**. After H1, the focused
router/tool suite passed **27 tests**, the pre-integration full suite passed **77 tests**, Ruff passed,
and the four changed Python files passed the format check. After the team knowledge layer was merged,
I reran the checks: the same focused suite passed **27 tests**, the integrated suite passed **80
tests**, Ruff reported `All checks passed!`, and all four Kent files were already formatted. The
increase from 77 to 80 comes from three integrated knowledge tests, not from extra H1 claims.

## 5. Conclusion and Submission Status

The Vietnamese tuition feature and its AI-assisted review are implemented and verified locally.
The main limitation is that the team service layer is not implemented, so verification stops at the
router and tool interfaces. Before submission, Minh Khang must personally inspect the code and this
report, confirm the review decisions, update any wording he disagrees with, and complete the Git and
pull-request workflow. Codex's review is not presented as his completed human review.

