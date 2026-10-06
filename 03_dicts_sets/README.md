# 03 - Dicts and sets

```bash
python 03_dicts_sets/exercises.py
```

`provider.py` is a fake dependency for ex11 (`import provider`, `except provider.UnknownCity`). Don't edit it.

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `get_price` | easy | `.get(k, default)` |
| 02 | `count_levels` | easy | manual counting with `.get(k, 0) + 1` |
| 03 | `merge_config` | easy | `\|` merge, dict comprehension, `is not None` |
| 04 | `switch_profile` | easy | `global` for rebinding vs mutating |
| 05 | `top_sources` | medium | `Counter.most_common` |
| 06 | `group_by_provider` | medium | `defaultdict(list)` / `setdefault` |
| 07 | `invert` | medium | inverting with collisions |
| 08 | `diff_hosts` | medium | set `&` `-` `^` `\|` |
| 09 | `rank_by_value` | medium | sort `.items()` by value |
| 10 | `get_path` | medium | safe nested lookup |
| 11 | `cmd_weather` + `run_repl` | advanced | dispatch table, `entry[0](args)`, `EOFError`, namespaced exceptions |
| 12 | `deep_merge` | advanced | recursion, `deepcopy`, no shared state |
| 13 | `LRUCache` | advanced | `OrderedDict.move_to_end` / `popitem(last=False)` |
| 14 | `shortest_route` | advanced | dict-of-sets graph, BFS |

## Cheat sheet

```python
d[k]                    # KeyError if missing
d.get(k)                # None if missing;  d.get(k, 0)
k in d                  # checks KEYS (never values); O(1)
d.setdefault(k, [])     # returns d[k], inserting [] first if missing
d.pop(k)                # KeyError if missing;  d.pop(k, None) never raises
del d[k]
d.update(other)         # in place
d.keys() / d.values() / d.items()   # live views
for k, v in d.items(): ...          # iterating d alone gives KEYS
list(d)                 # keys, insertion order (guaranteed 3.7+)
next(iter(d))           # first key
```

Gotchas:
- Don't add/remove keys while iterating `d` (`RuntimeError: dictionary changed size`). Iterate `list(d)` instead.
- `{}` is an empty DICT. Empty set is `set()`.
- Keys must be hashable: str, int, tuple of hashables. Not list, dict, set.
- `d.get(k) or default` is wrong when the stored value is `0`, `""`, `False`.

### Building dicts

```python
dict(zip(keys, values))
dict.fromkeys(keys, 0)              # same VALUE object for all keys (don't use [] here)
{m["name"]: m for m in models}      # index a list of dicts by a field
{k: v for k, v in d.items() if v is not None}
{v: k for k, v in d.items()}        # invert: GOTCHA silently keeps only the last k per v
```

### Merging

```python
a | b                   # new dict, b wins (3.9+)
a |= b                  # in place
{**a, **b}              # same as a | b, works before 3.9
{**a, "extra": 1}
# All of these are SHALLOW: nested dicts are shared, not merged. ex12 for deep.
```

### Counting and grouping

```python
counts[k] = counts.get(k, 0) + 1

from collections import Counter, defaultdict
c = Counter(words)          # Counter("hello") -> {'l': 2, 'h': 1, ...}
c.most_common(3)            # [(item, n), ...]; ties in first-seen order
c["missing"]                # 0, no KeyError (and doesn't insert)
c.update(more); c1 + c2; c1 - c2

g = defaultdict(list)
g[key].append(x)            # missing key -> list() created on first access
g = defaultdict(set); g[a].add(b)
dict(g)                     # convert before returning: reading g[missing] INSERTS it
d.setdefault(key, []).append(x)    # same thing with a plain dict
```

### Sorting a dict

```python
sorted(d)                                         # keys
sorted(d.items(), key=lambda kv: kv[1])           # by value
sorted(d.items(), key=lambda kv: (-kv[1], kv[0])) # value desc, key asc
max(d, key=d.get)                                 # key with the largest value
dict(sorted(d.items()))                           # dict rebuilt in sorted order
```

### Sets

```python
s = set(items); s = {1, 2}; s.add(x); s.discard(x)  # discard: no error if missing
s.remove(x)              # KeyError if missing
a | b   a.union(b)                  # either
a & b   a.intersection(b)           # both
a - b   a.difference(b)             # in a, not b
a ^ b   a.symmetric_difference(b)   # exactly one
a <= b  a.issubset(b);  a.isdisjoint(b)
a.union(list_b)          # the METHOD forms accept any iterable; the operators need sets
frozenset(s)             # hashable: can be a dict key or live in another set
sorted(s)                # sets are unordered: sort before returning/printing
```

### Command dispatch table (REPL)

```python
import shlex
import provider

COMMANDS = {
    "weather": (cmd_weather, "weather <city>"),   # tuple: entry[0] handler, entry[1] usage
    # {cmd_weather, "weather <city>"}  <- GOTCHA: that's a SET. Unordered, no indexing.
}

while True:
    try:
        line = input("> ").strip()
    except (EOFError, KeyboardInterrupt):        # Ctrl-D / Ctrl-C; parens = several types
        print()
        break
    if not line:
        continue
    name, *args = shlex.split(line)              # ValueError on unbalanced quotes
    if name == "quit":                           # == / != for strings, never `is` / `is not`
        break
    entry = COMMANDS.get(name)
    if entry is None:                            # `is None` IS right: None is a singleton
        print(f"unknown command: {name}")
        continue
    handler, usage = entry
    try:
        print(handler(args))                     # same as entry[0](args)
    except provider.UnknownCity as e:            # module.ExceptionName after `import provider`
        print(f"unknown city: {e}")              # (or: from provider import UnknownCity)
    except ValueError:
        print(f"usage: {usage}")

city = " ".join(args)                            # multi-word names: ["New", "York"] -> "New York"
```

### `global`

```python
COUNT = 0
STATE = {"n": 0}

def bump():
    global COUNT
    COUNT += 1          # rebinding a module name: needs `global` (else UnboundLocalError)
    STATE["n"] += 1     # mutating the object it points at: no declaration needed
# `nonlocal x` is the same idea for a variable in an enclosing function.
```

### Nested data

```python
cfg.get("a", {}).get("b", {}).get("c")     # quick safe chain (dicts only)
import copy; copy.deepcopy(cfg)            # before mutating something you were handed
```

### LRU and BFS skeletons

```python
from collections import OrderedDict, deque
od = OrderedDict()
od.move_to_end(k)            # mark most recent (end = newest)
od.popitem(last=False)       # evict oldest
# from functools import lru_cache / cache  -> memoize a function instead

graph = defaultdict(set)
for a, b in edges:
    graph[a].add(b)          # undirected: also graph[b].add(a)
came_from = {start: None}
q = deque([start])
while q:
    node = q.popleft()
    for nxt in graph.get(node, ()):
        if nxt not in came_from:
            came_from[nxt] = node
            q.append(nxt)
# reachable set = came_from.keys()
```
