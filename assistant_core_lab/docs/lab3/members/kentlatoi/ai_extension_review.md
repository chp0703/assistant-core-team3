# H1 - AI Extension Review

## 1. Student Information and Feature Overview

- **Student:** Nguyễn Trần Minh Khang
- **GitHub username:** `kentlatoi`

My completed main-lab work covers tuition tools in `tools.py`, intent routing in `router.py`, and
their tests. It is not an H1 extension.

For H1, I propose **Vietnamese-language tuition request support**. The system should classify
`Học phí cho 18 tín chỉ và 2 tín chỉ học lại` as `Intent.FEE`, extract `(18, 2)`, and reuse
`tuition()`. The tutorial result should remain 9,450,000 VND. English behavior must remain stable.

## 2. AI Tool and Prompt

No H1 coding prompt has been executed, so the AI tool and generated code are not yet recorded.

**Proposed prompt - not yet executed:**

> Add Vietnamese tuition requests while preserving English behavior. Make `route()` recognize
> `học phí` as `Intent.FEE`, and make `parse_credits()` extract labelled regular and retake credits.
> Reuse `Intent`, `InvalidRequest`, and `tuition()`. Do not hard-code the rate, add dependencies, or
> log requests. Change only `tools.py`, `router.py`, and their tests. Test accents, capitalization,
> reversed label order, missing regular credits, and false-positive routing. Return an uncommitted
> patch for manual review.

The final report must replace this draft with the exact executed prompt.

## 3. Implementation and Manual Review

There is no verified H1 implementation. The current modules and tests belong to the main lab. The
rows below are plans, not completed changes. Minh Khang must replace them with at least three real
review findings and improvements after generating the feature.

| # | AI-generated code | Issue found | My improvement | Reason |
| --- | --- | --- | --- | --- |
| 1 | **Pending:** fee condition in `route()`. | Check for false matches from broad words such as `học`. | **Pending:** match a clear normalized phrase and add negative tests. | Protects unrelated intents. |
| 2 | **Pending:** parsing in `parse_credits()`. | Check number-label order and missing regular credits. | **Pending:** bind values to `tín chỉ` and `học lại`; keep `InvalidRequest`. | Preserves deterministic parsing and the error interface. |
| 3 | **Pending:** generated tests. | Check for weak coverage and English regressions. | **Pending:** add success, failure, false-positive, and regression cases. | Verifies H1 without breaking existing behavior. |

## 4. Technical Checks and Testing

The feature must preserve these interfaces:

- `route(text, office_names) -> Intent` should only select an intent.
- `parse_credits(text) -> tuple[int, int]` should return regular and retake credits.
- `tuition(...) -> int` should remain the only fee calculation and receive its rate as an argument.

Python already supports Unicode and regular expressions, so no new dependency is expected. Review
must confirm that the patch adds no secret, personal data, raw-request logging, or duplicated
`450_000` production constant. Because `service.py` is a placeholder, only the router and tool
boundaries can be verified; end-to-end behavior cannot be claimed.

Minh Khang reported **10 passing tests** for the assigned modules, **60 passing tests** overall,
and a successful Ruff check. These main-lab results were not rerun here and do not cover H1. After
implementation, H1 needs focused Vietnamese tests, English regressions, the full suite, Ruff, and
formatting checks.

