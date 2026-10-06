# 02 - Lists

```bash
python 02_lists/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `last_n` | easy | negative slicing, the `[-0:]` trap |
| 02 | `loaded_names` | easy | comprehension with `if`, field from a list of dicts |
| 03 | `numbered_menu` | easy | `enumerate(start=1)` |
| 04 | `with_tag` | easy | copy vs alias |
| 05 | `sort_bookings` | medium | multi-key sort, mixed asc/desc, stable sort |
| 06 | `transpose` | medium | `zip(*rows)`, `strict=True` |
| 07 | `dedupe` | medium | `dict.fromkeys`, `seen` set |
| 08 | `chunk` | medium | `range` step + slicing |
| 09 | `rotate` | medium | `%`, slice concatenation |
| 10 | `moving_average` | medium | running-sum window |
| 11 | `flatten` | advanced | explicit stack of iterators, sentinel |
| 12 | `merge_intervals` | advanced | sort then sweep, `out[-1]` |
| 13 | `window_max` | advanced | monotonic `deque` |
| 14 | `apply_edits` | advanced | undo/redo stacks, `partition` |

## Cheat sheet

```python
a[0] / a[-1]            # first / last (IndexError on empty)
a[-3:]                  # last three (fine if len < 3)
a[:-1]                  # all but last
a[::-1]                 # reversed copy;  reversed(a) is a lazy iterator
a[::2]                  # every other
a[-0:]                  # GOTCHA: -0 == 0, so this is the WHOLE list
a[i:j]                  # slices never raise, even past the end

a.append(x)  a.extend(xs)  a.insert(i, x)
a.pop()  a.pop(0)       # pop(0) is O(n): use collections.deque for queues
a.remove(x)             # first match; ValueError if missing
a.index(x)              # ValueError if missing (no .find on lists)
x in a                  # O(n); use a set for repeated membership checks
a.count(x)
del a[i]  /  del a[i:j]
```

### Copies and aliasing

```python
b = a                   # SAME list. b.append(1) changes a.
b = a[:]  /  list(a)  /  a.copy()    # shallow copy (inner lists still shared)
import copy; copy.deepcopy(a)        # nested copy
grid = [[0] * 3] * 3    # GOTCHA: 3 references to ONE row
grid = [[0] * 3 for _ in range(3)]   # correct

def f(items=[]):        # GOTCHA: default evaluated once, shared across calls
def f(items=None):  items = [] if items is None else items
```

### Comprehensions

```python
[m["name"] for m in models]                         # pluck a field
[m["name"] for m in models if m.get("loaded")]      # filter (missing key -> None -> falsy)
[x if x > 0 else 0 for x in xs]                     # if/else goes BEFORE the for
[c for row in grid for c in row]                    # flatten one level: outer loop first
[[r[i] for r in rows] for i in range(len(rows[0]))] # nested: inner list per column
any(m["loaded"] for m in models) / all(...)         # short-circuit, no brackets needed
```

### Sorting

```python
sorted(a)                  # new list
a.sort()                   # in place, returns None   (a = a.sort() -> a is None!)
sorted(a, key=len, reverse=True)
sorted(rows, key=lambda r: (r["date"], -r["nights"]))   # multi-key; negate numbers for desc
from operator import itemgetter, attrgetter
sorted(rows, key=itemgetter("date", "nights"))
sorted(names, key=str.lower)                            # case-insensitive
max(models, key=lambda m: m["size_gb"])                 # the record, not the value
min(a, default=None)                                    # empty -> default instead of ValueError
```

Descending on a string key: you can't negate it. Sort is **stable**, so sort by the
least significant key first, then re-sort by the more significant keys:

```python
out = sorted(rows, key=lambda r: r["guest"].lower())        # tiebreak, asc
out.sort(key=lambda r: (r["date"], r["nights"]), reverse=True)  # primary, desc
```

### enumerate / zip

```python
for i, x in enumerate(a, start=1): ...
for name, size in zip(names, sizes): ...      # stops at the SHORTEST
zip(a, b, strict=True)                         # 3.10+: ValueError if lengths differ
list(zip(*rows))                               # transpose -> list of TUPLES
names, sizes = zip(*pairs)                     # unzip (tuples); fails on empty pairs
dict(zip(keys, values))
for prev, cur in zip(a, a[1:]): ...            # adjacent pairs
```

### Idioms

```python
list(dict.fromkeys(a))                    # dedupe, order kept (set() loses order)
[a[i:i + n] for i in range(0, len(a), n)] # chunk
k %= len(a); a[-k:] + a[:-k]              # rotate right (guard empty list and k == 0)
first, *rest = a                          # star unpacking; rest is always a list
*init, last = a
a, b = b, a                               # swap
```

### Stack, queue, deque

```python
stack = []; stack.append(x); stack.pop(); stack[-1]   # peek
from collections import deque
q = deque(); q.append(x); q.popleft()                 # O(1) both ends
deque(maxlen=3)                                       # keeps the last 3; old items fall off
```

### Comparing

```python
x == "quit" / x != "quit"     # compare string VALUES with == / !=
x is None / x is not None     # `is` is identity: only for None/True/False/sentinels
x is "quit"                   # GOTCHA: may work by accident (interning), SyntaxWarning in 3.8+
[1, 2] < [1, 3]               # lists and tuples compare element by element
```
