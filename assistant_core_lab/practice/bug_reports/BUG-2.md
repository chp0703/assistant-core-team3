# BUG-2: "Top 3" shows only 2 students

**Reported by:** lecturer, 13 Oct
**Steps:** call `top_n(scores, 3)` for a class of 10 students.
**Expected:** 3 names
**Actual:** 2 names. With `top_n(scores, 1)` the list is empty.
