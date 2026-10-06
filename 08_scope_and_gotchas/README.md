# 08 - Scope & Gotchas

```bash
python 08_scope_and_gotchas/exercises.py
```

Each exercise is a trap. The docstring names it after the task; the tests probe it directly.

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `load_model` / `unload_model` | easy | `global` to rebind a module variable |
| 02 | `model_status` | easy | `is None` vs `==` for strings |
| 03 | `is_yes` | easy | `x == a or b`, substring `in`, immutable strings |
| 04 | `make_grid` | easy | `[[0]*c]*r` aliasing |
| 05 | `parse_command` | medium | `cmd, *args = ...` and the empty case |
| 06 | `log_event` | medium | mutable default argument, `x or []` |
| 07 | `resolve_settings` | medium | falsy is not missing: `is None` over `or` |
| 08 | `make_callbacks` | medium | late-binding closures in a loop |
| 09 | `make_rate_limiter` | medium | `nonlocal`, per-closure state |
| 10 | `weather_command` | medium | `except provider.UnknownCity`, don't over-catch |
| 11 | `apply_override` | advanced | shallow vs `copy.deepcopy` |
| 12 | `drop_inactive` | advanced | mutating while iterating, `xs[:] =`, chained compare |
| 13 | `format_offset` | advanced | `//` and `%` with negatives |
| 14 | `order_tickets` | advanced | stable sort, mixed-direction multi-key |

## Cheat sheet

### Scope (LEGB: Local, Enclosing, Global, Builtin)

```python
LOADED = None
def load(name):
    global LOADED        # required to REBIND a module name
    LOADED = name

def make():
    n = 0
    def inc():
        nonlocal n       # required to REBIND an enclosing function's name
        n += 1
    return inc

CACHE = {}
def put(k, v):
    CACHE[k] = v         # MUTATING needs neither: you're not rebinding CACHE
```

Gotcha: any assignment anywhere in a function (`x = `, `x += `, `for x in`, `import x`)
makes `x` local for the WHOLE function. Reading it before the assignment raises
`UnboundLocalError`, even if a global `x` exists.

Gotcha: `from mod import X` copies the binding. If `mod` later rebinds `X`, you still see
the old value. Use `import mod` and read `mod.X`.

### Identity vs equality

```python
x is None / x is not None      # correct: None, True, False are singletons
a == b / a != b                # strings, numbers, lists: always compare VALUES
"".join(["ph", "i3"]) is "phi3"   # False; == is True. `is` on strings only "works" by interning luck
256 is 256  # True (small-int cache); big ints made at runtime: not reliably
```

### Boolean traps

```python
ans == "y" or "yes"            # (ans == "y") or "yes" -> always truthy
ans in ("y", "yes")            # correct
"" in "yes"                    # True! `in` on a str is a substring test
timeout = cfg.get("timeout") or 30          # BUG when 0 is valid
timeout = cfg.get("timeout"); timeout = 30 if timeout is None else timeout
# falsy: None, False, 0, 0.0, "", [], {}, set(), range(0)
```

### Mutable defaults and aliasing

```python
def f(xs=[]): ...              # ONE list, created at def time, shared by every call
def f(xs=None):
    if xs is None:             # not `xs = xs or []`: that discards a caller's empty list
        xs = []

[[0] * 3] * 3                  # 3 references to ONE row
[[0] * 3 for _ in range(3)]    # 3 rows

b = a                          # same object
b = a.copy() / list(a) / a[:] / dict(d) / {**d}   # SHALLOW: new outer, shared inner
import copy; b = copy.deepcopy(a)                  # fully independent

def reset(xs):
    xs = []                    # rebinds the local name only; caller unaffected
    xs[:] = []                 # mutates the caller's list
```

Gotcha: class attributes are shared by every instance. `class Cart: items = []` is one list
for all carts; create per-instance state in `__init__` (`self.items = []`).

### Late-binding closures

```python
fns = [lambda: i for i in range(3)]          # all return 2: they read i when CALLED
fns = [lambda i=i: i for i in range(3)]      # default arg binds now -> 0, 1, 2
fns = [functools.partial(show, i) for i in range(3)]
```

### Iterating while mutating

```python
for x in xs:
    if bad(x): xs.remove(x)          # SKIPS the element after each removal (silently)
xs[:] = [x for x in xs if not bad(x)]    # in place, correct
for k in list(d):                    # iterate over a snapshot of keys...
    if bad(d[k]): del d[k]           # ...then deleting is fine (else RuntimeError)
```

### Numbers

```python
-7 // 2 == -4      # floors toward -inf (Go/JS/C truncate toward 0: -3)
-7 % 2 == 1        # result takes the sign of the DIVISOR
divmod(-90, 60) == (-2, 30)
int(-3.5) == -3    # truncates toward 0
math.floor(-3.5) == -4
(h - 5) % 24       # wraparound that stays in 0..23, even when h - 5 < 0
-(-n // k)         # ceiling division for ints
0.1 + 0.2 == 0.3   # False; use math.isclose
round(2.5) == 2    # banker's rounding
```

### Chained comparisons, unpacking, sorting

```python
start <= t < end           # == start <= t and t < end
a < b == c                 # == a < b and b == c  (surprising; avoid)

first, *rest = [1, 2, 3]   # 1, [2, 3];   rest is always a list
first, *rest = []          # ValueError: not enough values to unpack
*init, last = path.split(".")
a, b = b, a                # swap

sorted(xs, key=lambda t: (-t["pri"], t["name"]))   # negate numbers for mixed order
s = sorted(xs, key=lambda t: t["title"])           # strings: two STABLE passes,
s = sorted(s, key=lambda t: t["team"], reverse=True)   # secondary first, primary last
```

### Strings are immutable

```python
s.strip()                  # returns a new string; on its own line it does nothing
s = s.strip()
out = ""
for w in words: out += w   # O(n^2) worst case
out = "".join(words)       # build a list, join once
```

### Exceptions from another module

```python
import provider
try:
    provider.get_temp(city)
except provider.UnknownCity:      # not `except UnknownCity` (NameError, only when it fires)
    ...
except (ValueError, KeyError) as e:   # tuple for several types
    ...
# Avoid bare `except:` and `except Exception:` around big blocks: they hide bugs.
# Bare except also catches KeyboardInterrupt/SystemExit (BaseException).
```
