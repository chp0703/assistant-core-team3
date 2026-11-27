# BUG-1: Report page crashes for a new course

**Reported by:** TA, 12 Oct
**Steps:** open the grade report of a course that has no grades yet.
**Expected:** average shows 0.0
**Actual:** the page crashes; the log shows `ZeroDivisionError: division by zero` in `average`.
