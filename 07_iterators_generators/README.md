# 07 - Iterators & Generators

```bash
python 07_iterators_generators/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `first_error` | easy | `next(genexp, None)`: first match, stop early |
| 02 | `token_report` | easy | genexp in `sum`/`max`, one-pass generator gotcha |
| 03 | `backoff_delays` | easy | generator function with `yield` |
| 04 | `read_table` | easy | `iter()` + `next()` to peel off a header |
| 05 | `next_free_ids` | medium | `count()` (infinite) + filter + `islice` |
| 06 | `first_over_budget` | medium | `accumulate`, `enumerate(start=1)` |
| 07 | `bookings_by_room` | medium | `groupby`, and sorting first |
| 08 | `split_sessions` | medium | `pairwise` deltas |
| 09 | `interleave` | medium | `zip_longest`, `chain.from_iterable`, sentinel |
| 10 | `batched` | advanced | lazy chunking with a shared iterator |
| 11 | `walk` | advanced | recursive generator, `yield from` |
| 12 | `PageIterator` | advanced | `__iter__` / `__next__` / `StopIteration` |
| 13 | `first_errors` | advanced | lazy pipeline that reads only what it needs |
| 14 | `running_average` | advanced | coroutine with `send()` |

## Cheat sheet

```python
# Generator function: any `yield` in the body makes calling it return a generator.
# NOTHING in the body runs until the first next(); that includes argument validation.
def countdown(n):
    while n > 0:
        yield n
        n -= 1

list(countdown(3))          # [3, 2, 1]
gen = countdown(3)
next(gen), next(gen)        # (3, 2)
next(gen, None)             # 1 ; next(gen, None) -> None instead of raising StopIteration

# Generator expression vs list comprehension
sum(r["tokens"] for r in rows)      # lazy, no list built; no extra parens needed as sole arg
[r["tokens"] for r in rows]         # builds the whole list
max((r["ms"] for r in rows), default=0)   # extra arg -> genexp needs its own parens
any(x > 9 for x in xs) / all(...)   # short-circuit: stop at the first True / False

# First match (Python's .find()):
first = next((r for r in rows if r["ok"]), None)

# Manual iteration
it = iter(lines)              # file objects, lists, generators all work
header = next(it, None)       # pull one
for line in it: ...           # resumes AFTER the header

for i, x in enumerate(xs, start=1): ...   # 1-based numbering
```

### Exhaustion: the #1 gotcha

```python
gen = (x * 2 for x in range(3))
sum(gen)     # 6
sum(gen)     # 0   <- already used up, no error!
max(gen)     # ValueError: max() arg is an empty sequence

xs = list(gen_or_anything)   # materialize when you need more than one pass
# One-shot: generators, zip(), map(), filter(), file objects, any iterator whose __iter__
# returns self.  Re-iterable: list, tuple, dict, set, range, dict.keys()/.items() views.
```

### itertools

```python
from itertools import (count, cycle, repeat, islice, chain, groupby,
                       accumulate, pairwise, zip_longest, takewhile, dropwhile)

count(1)                      # 1, 2, 3, ... forever
cycle(["a", "b"])             # a, b, a, b, ... forever
repeat(0, 3)                  # 0, 0, 0 ; repeat(0) is forever
islice(it, 5)                 # first 5 ; islice(it, 2, 8, 2) like it[2:8:2] ; LAZY
list(zip(tickets, cycle(agents)))   # round-robin assignment; zip stops at the shortest

chain([1, 2], [3])            # 1, 2, 3
chain.from_iterable(list_of_lists)  # flatten one level (lazy) == (x for xs in lol for x in xs)

accumulate([1, 2, 3])         # 1, 3, 6        running totals
accumulate([3, 1, 4], max)    # 3, 3, 4        running max
accumulate(xs, initial=0)     # 0, ...         prepends the start value

pairwise([1, 4, 9])           # (1, 4), (4, 9) ; 3.10+ ; deltas: [b - a for a, b in pairwise(ts)]
zip_longest("ab", "x", fillvalue="-")   # (a, x), (b, -)
takewhile(lambda x: x < 3, xs)          # stop at first failure
dropwhile(lambda l: l.startswith("#"), lines)   # skip a leading comment block
```

### groupby

```python
from itertools import groupby
from operator import itemgetter

rows.sort(key=itemgetter("room"))              # MUST sort by the same key first
for room, group in groupby(rows, key=itemgetter("room")):
    names = [r["who"] for r in group]           # use `group` NOW; it's invalidated on the next step

# Without sorting, groupby only merges ADJACENT runs:  "aabaa" -> a, b, a
# That's exactly what you want for run-length encoding, and wrong for "group by key".
# For a plain {key: [items]} dict, defaultdict(list) is often simpler than groupby.
```

### yield from, shared iterators

```python
def flatten(nested):                  # [1, [2, [3, 4]], 5] -> 1, 2, 3, 4, 5
    for x in nested:
        if isinstance(x, list):
            yield from flatten(x)     # delegate: re-yield everything the sub-generator yields
        else:
            yield x

# islice on a LIST restarts from index 0 every time; on an ITERATOR it continues.
xs = [1, 2, 3, 4]
list(islice(xs, 2)), list(islice(xs, 2))     # ([1, 2], [1, 2])
it = iter(xs)
list(islice(it, 2)), list(islice(it, 2))     # ([1, 2], [3, 4])

while chunk := f.read(4096):          # walrus loop: assign, then test truthiness (3.8+)
    ...
```

### Custom iterator class

```python
class Countdown:
    def __init__(self, n):
        self.n = n
    def __iter__(self):
        return self                  # iterator: returns itself (so it's one-shot)
    def __next__(self):
        if self.n <= 0:
            raise StopIteration      # how a for loop knows to stop
        self.n -= 1
        return self.n + 1

# Re-iterable instead? Make __iter__ a generator method and drop __next__:
#   def __iter__(self): yield from range(self.n, 0, -1)
# Never let StopIteration escape INSIDE a generator body: since 3.7 it becomes RuntimeError.
# Use `return` to end a generator.
```

### send() / coroutines

```python
def tally():
    seen = {}
    word = None
    while True:
        word = yield seen.get(word, 0)   # hand out a value, pause until .send(word)
        seen[word] = seen.get(word, 0) + 1

t = tally()
next(t)           # prime: run to the first yield (returns 0 here). Skipping this ->
                  #   TypeError: can't send non-None value to a just-started generator
t.send("phi3")    # 1
t.send("phi3")    # 2
t.close()         # raises GeneratorExit inside it
```

Lazy pipeline pattern: each stage is a generator over the previous one, and the last
stage (`islice`, `next`, a `break`) decides how much is pulled. Nothing upstream runs
until something downstream asks:

```python
parsed = (parse(l) for l in lines)
errors = (p for p in parsed if p and p.level == "ERROR")
top5   = list(islice(errors, 5))      # reads exactly as many lines as needed
```
