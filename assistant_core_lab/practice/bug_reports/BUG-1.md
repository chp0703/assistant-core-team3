# BUG-1: Report page crashes for a new course

**Reported by:** TA, 12 Oct
**Steps:** open the grade report of a course that has no grades yet.
**Expected:** average shows 0.0
**Actual:** the page crashes; the log shows `ZeroDivisionError: division by zero` in `average`.

## Resolution

- Cause: the empty list reaches division by its length, which is zero.
- Fix: return `0.0` before computing the average when there are no scores.
- Regression: `test_bug1_average_empty` initially raised `ZeroDivisionError`.
  With all seven tests present, temporarily removing this fix reproduced the
  failure (1 failed, 6 passed). Restoring it gave 7 passed.
