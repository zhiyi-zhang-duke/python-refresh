# 10 - Stdlib Toolkit

```bash
python 10_stdlib_toolkit/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `recent_errors` | easy | `deque(maxlen=)` as a tail buffer |
| 02 | `benchmark_stats` | easy | `statistics`, `min(key=)`, `heapq.nsmallest` |
| 03 | `Benchmark` + `parse_benchmark` | easy | `typing.NamedTuple` with a default |
| 04 | `latency_bucket` | easy | `bisect_right` into breakpoints |
| 05 | `trending_cities` | medium | `Counter` arithmetic, `most_common` |
| 06 | `fastest_overall` | medium | `heapq.merge` (k sorted streams, lazy) |
| 07 | `minutes_by_day` | medium | `strptime`, `timedelta`, `strftime` |
| 08 | `schedule_matchups` | medium | `itertools.combinations`, `product` |
| 09 | `count_ways` | medium | `@lru_cache` memoized recursion, `cache_info()` |
| 10 | `shortest_path` | advanced | BFS with `deque` |
| 11 | `TTLCache` | advanced | dict of (value, timestamp), injected clock |
| 12 | `TaskScheduler` | advanced | `heapq` with a tie-breaking counter |
| 13 | `apply_events` | advanced | `Enum` + transition table |
| 14 | `encode_job` / `decode_job` | advanced | `json` with `default=`, ISO datetimes |

## Cheat sheet

### collections

```python
from collections import Counter, deque, defaultdict

c = Counter(["a", "b", "a"])          # Counter({'a': 2, 'b': 1})
c = Counter(w.lower() for w in words) # any iterable, incl. a genexp
c["missing"]                          # 0, no KeyError (and doesn't insert the key)
c.most_common(2)                      # [('a', 2), ('b', 1)]; ties keep first-seen order
c.most_common()                       # all, sorted by count desc
c.update(more_words); c["a"] += 1
c1 + c2  /  c1 - c2                   # add / subtract; results DROP counts <= 0
c1 & c2  /  c1 | c2                   # min / max per key
c1.subtract(c2)                       # in place, KEEPS zero and negative counts
sum(c.values()) / c.total()           # .total() is 3.10+

d = deque(maxlen=3)                   # bounded: appending a 4th drops from the LEFT
d.append(x); d.appendleft(x)
d.popleft(); d.pop()                  # O(1) both ends; list.pop(0) is O(n)
deque(iterable, maxlen=3)             # "last 3 items" of any stream, O(3) memory
d.rotate(1)

groups = defaultdict(list); groups[k].append(v)
```

### BFS template

```python
q = deque([start]); seen = {start}; dist = {start: 0}
while q:
    node = q.popleft()                # popleft = queue (BFS); pop = stack (DFS)
    for nxt in neighbors(node):
        if nxt not in seen:
            seen.add(nxt)             # mark on ENQUEUE, or a node gets queued many times
            dist[nxt] = dist[node] + 1
            q.append(nxt)

for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):   # grid neighbors; bounds-check 0 <= r < rows
```

### heapq (a min-heap on a plain list)

```python
import heapq
h = []
heapq.heappush(h, (priority, seq, item))   # tuples compare left to right
heapq.heappop(h)                           # smallest; IndexError if empty
h[0]                                       # peek smallest
heapq.heapify(xs)                          # in place, O(n)
heapq.heappushpop(h, x) / heapq.heapreplace(h, x)

heapq.nlargest(3, rows, key=lambda r: r["score"])   # top-k, O(n log k)
heapq.nsmallest(3, rows, key=itemgetter("ms"))
heapq.merge(a, b, c, key=...)              # merge SORTED iterables lazily -> an iterator
# Max-heap: push (-priority, ...).
# Tie-break: (priority, next(counter), item). Without the counter, equal priorities
# compare the items: wrong order for strings, TypeError for dicts.
```

### bisect

```python
import bisect
bisect.bisect_left(xs, x)    # first index where x could go (before equal items)
bisect.bisect_right(xs, x)   # after equal items  (bisect.bisect == bisect_right)
bisect.insort(xs, x)         # insert keeping xs sorted (O(n) shift, O(log n) search)

GRADES = "FDCBA"; CUTS = [60, 70, 80, 90]
GRADES[bisect.bisect_right(CUTS, 85)]   # 'B'
# 3.10+: bisect_left(rows, 300, key=lambda r: r["start"])  (key applies to the elements, not x)
```

### datetime

```python
from datetime import datetime, date, timedelta

dt = datetime.strptime("2026-09-14 10:03", "%Y-%m-%d %H:%M")   # parse  (P = parse)
dt.strftime("%a %b %d, %H:%M")      # 'Mon Sep 14, 10:03'      (F = format)
dt.isoformat()                      # '2026-09-14T10:03:00'
datetime.fromisoformat("2026-09-14T10:03:00")
dt.date(); dt.time(); dt.weekday()  # Mon == 0

delta = end - start                 # timedelta
delta.total_seconds()               # float, includes days
delta.seconds                       # TRAP: only the seconds part, 0..86399, ignores .days
delta // timedelta(minutes=1)       # whole minutes as an int
dt + timedelta(hours=2, minutes=30)
dt.replace(hour=0, minute=0)        # start of day

# %Y %m %d %H %M %S  year month day hour(24) minute second
# %a / %A  Mon / Monday     %b / %B  Sep / September    %I %p  12-hour clock + AM/PM
# Naive vs aware: comparing a tz-aware and a naive datetime raises TypeError.
```

### functools

```python
from functools import lru_cache, cache, partial, reduce

@lru_cache(maxsize=None)    # or @cache (3.9+); args must be HASHABLE (tuple, not list)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

fib.cache_info()            # CacheInfo(hits=..., misses=..., maxsize=None, currsize=...)
fib.cache_clear()
# Recursion limit is ~1000 frames: deep memoized recursion can still hit RecursionError.
# On a method, @lru_cache keeps `self` alive forever; prefer a dict on the instance.
```

### enum, NamedTuple, dataclass

```python
from enum import Enum, auto

class Color(Enum):
    RED = "red"
    BLUE = "blue"

Color("red")         # lookup by VALUE  -> Color.RED  (ValueError if unknown)
Color["RED"]         # lookup by NAME   -> Color.RED  (KeyError if unknown)
Color.RED.name, Color.RED.value     # ('RED', 'red')
list(Color)          # members in definition order
Color.RED is Color("red")           # True: members are singletons; compare with `is` or ==
Color.RED == "red"   # False! Use a str mixin (class Color(str, Enum)) if you need that
# Members are hashable: perfect dict keys, e.g. {(State.A, "go"): State.B}

from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float = 0.0              # defaults after non-defaults
p = Point(1.5)                  # Point(x=1.5, y=0.0)
x, y = p; p[0]; p.x             # it IS a tuple: unpack, index, sort, hash
p._replace(y=2)                 # immutable, so this returns a new one
p._asdict(); Point._fields
# Need mutability or methods with defaults like lists? Use @dataclass (topic 05).
```

### itertools combinatorics

```python
from itertools import product, permutations, combinations, combinations_with_replacement

list(product("ab", [1, 2]))    # [('a',1), ('a',2), ('b',1), ('b',2)]  nested for-loops, last varies fastest
product(range(3), repeat=2)    # all 9 (i, j) pairs
list(permutations("abc", 2))   # ordered pairs, no repeats: 6
list(combinations("abc", 2))   # unordered pairs: ('a','b'), ('a','c'), ('b','c')
combinations_with_replacement("ab", 2)   # aa ab bb
# Counts: product n*m, permutations n!/(n-k)!, combinations n!/(k!(n-k)!) -> math.comb(n, k)
```

### json

```python
import json

s = json.dumps(obj)                         # -> str     (dump / load = files)
s = json.dumps(obj, indent=2, sort_keys=True)
obj = json.loads(s)                         # -> dict/list
json.dumps(obj, default=fn)                 # fn(o) called for un-serializable o; return
                                            # something JSON-able or raise TypeError
json.dumps(obj, default=str)                # quick hack: str() everything (silently hides bugs)

# Round-trip losses: tuples come back as lists, int dict keys come back as strings,
# datetime/Enum/set need default= going out and manual conversion coming back.
# None <-> null, True <-> true.
```

### statistics

```python
import statistics as st
st.mean(xs); st.median(xs)    # median of an even count averages the middle two
st.median_low(xs); st.mode(xs); st.stdev(xs); st.pstdev(xs)
st.quantiles(xs, n=100)[94]   # ~p95 (needs at least 2 points)
# Empty data -> statistics.StatisticsError (a ValueError subclass)
round(2.675, 2)               # 2.67: 2.675 is stored as 2.67499...; round(2.5) == 2 (banker's)
```
