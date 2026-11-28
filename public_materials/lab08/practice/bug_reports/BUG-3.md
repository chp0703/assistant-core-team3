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
