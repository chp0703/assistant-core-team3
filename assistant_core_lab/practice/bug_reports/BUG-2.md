# BUG-2: "Top 3" shows only 2 students

**Reported by:** lecturer, 13 Oct
**Steps:** call `top_n(scores, 3)` for a class of 10 students.
**Expected:** 3 names
**Actual:** 2 names. With `top_n(scores, 1)` the list is empty.

## Resolution

- Cause: `ranked[: n - 1]` stops one item too early.
- Fix: use `ranked[:n]` and retain the existing alphabetical ordering for ties.
- Regression: `test_bug2_top_n_returns_n` initially received only two of the
  three expected names. After the fix, it checks both the top three and top one.
