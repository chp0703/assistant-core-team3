# BUG-3: Grades from one class appear in another class

**Reported by:** student, 14 Oct
**Steps:**
```
a = add_grade("An", 8.0)      # new book for class A
b = add_grade("Binh", 6.0)    # new book for class B
print(b)
```
**Expected:** `{'Binh': [6.0]}`
**Actual:** `{'An': [8.0], 'Binh': [6.0]}` — An appears in class B's book.

## Resolution

- Cause: Python creates the default dictionary once and reuses it on each call.
- Fix: use `None` as the default and create a dictionary for each call that
  omits the book. A dictionary supplied by the caller is still updated in place.
- Regression: `test_bug3_add_grade_new_book_each_time` initially found that
  both calls returned the same dictionary. After the fix, it checks that the
  dictionaries and their contents are independent.
