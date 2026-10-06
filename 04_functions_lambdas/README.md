# 04 - Functions & Lambdas

```bash
python 04_functions_lambdas/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `names_by_size` | easy | `sorted(key=lambda ...)`, tuple keys, negate to flip one part |
| 02 | `active_names` | easy | comprehension with `if` vs `map`/`filter` |
| 03 | `latency_stats` | easy | returning (and unpacking) multiple values |
| 04 | `dispatch` | easy | functions in a dict: `commands[name][0](args)` |
| 05 | `book` | medium | `*args`, keyword-only params |
| 06 | `make_counter` | medium | closures, `nonlocal` |
| 07 | `build_loggers` | medium | `functools.partial` |
| 08 | `pipeline` | medium | composing functions, `functools.reduce` |
| 09 | `run_repl` | medium | injected input fn, `except (EOFError, KeyboardInterrupt)` |
| 10 | `count_calls` | advanced | decorator, `*args/**kwargs` forwarding, `functools.wraps` |
| 11 | `timed` | advanced | decorator factory, injected clock, `try/finally` |
| 12 | `retry` | advanced | decorator factory with args, re-raise with bare `raise` |
| 13 | `memoize` | advanced | cache dict on the wrapper, `in` vs truthiness |
| 14 | `command` / `run_command` | advanced | registration decorator filling a dispatch dict |

## Cheat sheet

```python
sorted(xs, key=lambda m: m["size"])                  # returns a NEW list
xs.sort(key=..., reverse=True)                       # in place, returns None
sorted(xs, key=lambda m: (-m["size"], m["name"]))    # size desc, name asc
from operator import itemgetter, attrgetter
sorted(rows, key=itemgetter("team", "name"))         # same as lambda r: (r["team"], r["name"])
max(models, key=lambda m: m["size"])                 # the dict, not the size

[u["name"] for u in users if u.get("active")]        # prefer this...
list(map(lambda u: u["name"], filter(lambda u: u.get("active"), users)))   # ...over this
list(map(int, "1 2 3".split()))                      # map shines with an existing function
any(m["loaded"] for m in models) / all(...)          # short-circuit, take a generator

def stats(xs): return min(xs), max(xs)               # returns a tuple
lo, hi = stats(xs)
```

### Signatures

```python
def f(a, b=2, *args, kw_only, kw_default=1, **kwargs): ...
def g(a, *, start, hours=1): ...    # bare * = everything after is keyword-only
def h(a, /, b): ...                 # / = everything before is positional-only (3.8+)

f(*my_list, **my_dict)              # unpack into a call
def wrapper(*args, **kwargs):       # forward everything untouched
    return fn(*args, **kwargs)
```

Gotcha: default values are evaluated ONCE, at `def` time. `def f(x=[])` shares one list
across calls. Use `x=None` then `if x is None: x = []`. (More in 08.)

### Functions as values

```python
COMMANDS = {"load": (load, "Load a model"), "list": (list_models, "List models")}
handler, help_text = COMMANDS[name]       # unpack the tuple
COMMANDS[name][0](args)                   # or index and call in one go
COMMANDS.get(name, (unknown, ""))[0](args)

from functools import partial, reduce
info = partial(write_log, log, "info")    # info(msg) == write_log(log, "info", msg)
reduce(lambda acc, x: acc + x, [1, 2, 3], 0)       # 6; always pass the initial value
reduce(lambda acc, f: f(acc), [str.strip, str.lower], "  Hi ")   # "hi"
```

### Closures

```python
def make_counter():
    n = 0
    def inc():
        nonlocal n        # needed because we ASSIGN to n; reading alone doesn't need it
        n += 1
        return n
    return inc
```

Gotcha: mutating (`items.append`) never needs `nonlocal`/`global`; rebinding (`n += 1`,
`n = ...`) does. Without it you get `UnboundLocalError`.

### Decorators

```python
import functools

def count_calls(fn):
    @functools.wraps(fn)                  # keeps __name__, __doc__ (without it: "wrapper")
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return fn(*args, **kwargs)        # don't forget the return
    wrapper.calls = 0
    return wrapper

def retry(times=3, exceptions=(Exception,)):   # factory: takes config...
    def decorator(fn):                          # ...returns the real decorator
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions:              # a tuple of classes works here
                    if attempt == times - 1:
                        raise                   # bare raise = re-raise current, keeps traceback
        return wrapper
    return decorator

@retry(times=5)        # factory: parentheses required
@count_calls           # plain decorator: no parentheses
def fetch(): ...       # applied bottom-up: retry(5)(count_calls(fetch))

COMMANDS = {}
def command(name):
    def register(fn):
        COMMANDS[name] = fn
        return fn       # return fn itself so the name still refers to the plain function
    return register

functools.cache / functools.lru_cache(maxsize=128)   # built-in memoize (args must be hashable)
```

Gotchas:
- `@retry` without parentheses passes your function in as `times`. Factories need `()`.
- Memo caches: `if key in cache`, never `if cache.get(key)` (a cached 0/None/"" looks like a miss).
- `try/finally` in a timing wrapper so failures get recorded too; `finally` doesn't swallow the exception.

### REPL loop

```python
while True:
    try:
        line = input("> ").strip()
    except (EOFError, KeyboardInterrupt):   # Ctrl-D / Ctrl-C; tuple catches either
        print()
        break
    if not line:
        continue
```

Inject `read=input` as a parameter so tests can pass a fake.
