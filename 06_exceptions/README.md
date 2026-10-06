# 06 - Exceptions

```bash
python 06_exceptions/exercises.py
```

`provider.py` is a fake weather provider (not an exercise). It defines
`ProviderError`, `UnknownCity(ProviderError)`, `Timeout(ProviderError)`, `get_temp(city)`,
and `FlakyProvider(fail_times=N)`, whose first N calls raise `Timeout`. Read it first.

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `safe_int` | easy | `try`/`except`, `ValueError` vs `TypeError` |
| 02 | `read_command` | easy | `except (EOFError, KeyboardInterrupt)` tuple |
| 03 | `temp_or_none` | easy | catching a namespaced `provider.UnknownCity` |
| 04 | `describe_error` | easy | `type(e).__name__`, useful error text |
| 05 | `port_for` | medium | EAFP vs LBYL over a nested lookup |
| 06 | `forget` | medium | `contextlib.suppress`, where to put it |
| 07 | `traced` | medium | `try`/`except`/`else`/`finally` order |
| 08 | `repl_step` | medium | command-dict dispatch, catch-all, `global` |
| 09 | `BookingConflict` / `book` | medium | custom exception hierarchy with attributes |
| 10 | `load_config` | medium | `raise ... from e`, `raise ... from None` |
| 11 | `run_job` | advanced | `try`/`finally` resource release, bare `raise` |
| 12 | `loaded` | advanced | `@contextlib.contextmanager` with guaranteed cleanup |
| 13 | `retry` | advanced | exponential backoff, injected `sleep`, retryable vs fatal |
| 14 | `ValidationError` / `validate_booking` | advanced | collect all errors, raise one |

## Cheat sheet

```python
try:
    value = risky()
except (ValueError, TypeError):       # tuple = any of these. NOT `except ValueError, TypeError:`
    value = None
except provider.ProviderError as e:   # a base class catches all its subclasses
    log(e)
except Exception as e:                # catch-all for "real" errors; put it LAST
    print(f"error: {type(e).__name__}: {e}")
else:
    use(value)                        # only if the try block raised nothing
finally:
    cleanup()                         # ALWAYS: after success, after except, after return, after raise
```

- `except` clauses are checked top to bottom; the first match wins. Specific before general.
- `else` is for code that should run on success but whose own errors you do NOT want caught.
  `return risky()` inside `try` means `else` never runs.
- `finally` runs even when the `try` or `except` block `return`s.
- `except:` (bare) and `except BaseException:` also catch `KeyboardInterrupt` and `SystemExit`. Don't.

### The hierarchy you'll actually hit

```
BaseException
 ├── KeyboardInterrupt        Ctrl-C  (NOT an Exception: `except Exception` misses it)
 ├── SystemExit               sys.exit()
 └── Exception
      ├── ValueError          int("x"), unpacking wrong count, shlex unbalanced quotes
      │    └── json.JSONDecodeError
      ├── TypeError           None["k"], len(5), wrong arg count
      ├── LookupError
      │    ├── KeyError       d["missing"]       str(KeyError("k")) == "'k'" (quoted!)
      │    └── IndexError     [][0]
      ├── AttributeError      None.strip()
      ├── EOFError            input() at Ctrl-D / end of piped stdin
      ├── OSError
      │    ├── FileNotFoundError
      │    └── TimeoutError   (built-in; provider.Timeout is a different class)
      ├── RuntimeError
      │    └── NotImplementedError
      └── ZeroDivisionError   (under ArithmeticError)
```

REPL input loop:

```python
while True:
    try:
        line = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        break
```

### Namespaced exceptions

```python
import provider
try:
    provider.get_temp(city)
except provider.UnknownCity:      # the class lives in the module's namespace
    ...

from provider import UnknownCity  # only this form lets you write `except UnknownCity:`
```

Gotcha: `except UnknownCity:` after a plain `import provider` is a `NameError`, but only
when an exception actually reaches that clause. The happy path runs fine, so the bug hides.

### Error messages that help

```python
except Exception as e:
    print(f"error: {type(e).__name__}: {e}")     # error: UnknownCity: no data for 'Oslo'
    # NOT print("Something went wrong")           -- hides the type and the message
    # repr(e) -> "UnknownCity(\"no data for 'Oslo'\")"  also fine for logs

import traceback; traceback.print_exc()          # full stack, while debugging
```

### Custom exceptions

```python
class BookingError(Exception):            # base for your module: callers catch this one
    pass

class BookingConflict(BookingError):
    def __init__(self, room, start, end):
        super().__init__(f"room {room} is already booked {start}-{end}")   # sets str(e)
        self.room, self.start, self.end = room, start, end                   # data for callers

class ValidationError(ValueError):        # subclass a built-in when the meaning fits
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors
```

Skip `super().__init__(msg)` and `str(e)` becomes the tuple of constructor args: `"('A', 9, 11)"`.

### Chaining and re-raising

```python
except json.JSONDecodeError as e:
    raise ConfigError(f"invalid JSON: {e.msg}") from e    # e.__cause__ = original; traceback shows both
except KeyError:
    raise ConfigError("missing key: model") from None     # hide the noisy original
except Exception as e:
    log(e)
    raise                                                  # bare raise: same exception, original traceback
```

Without `from`, raising inside `except` still links the original as `__context__`
("During handling of the above exception, another exception occurred").

### Tools from contextlib

```python
from contextlib import suppress, contextmanager

for key in keys:
    with suppress(KeyError):          # INSIDE the loop; around the loop, the first miss ends it
        del cache[key]

@contextmanager
def loaded(name):
    load(name)                        # __enter__ part
    try:
        yield name                    # `as x` gets this; the with-body's exception is raised HERE
    finally:
        unload(name)                  # without try/finally, an exception skips this line
```

### EAFP vs LBYL

```python
# LBYL: look before you leap
if "services" in cfg and isinstance(cfg["services"], dict) and name in cfg["services"] ...:

# EAFP: easier to ask forgiveness (idiomatic Python)
try:
    port = int(cfg["services"][name]["port"])
except (KeyError, TypeError, ValueError):
    port = default

d.get(key, default)   # the one-level case: neither, just use .get
```

Keep the `try` body small: only the lines you expect to fail. A big `try` with a broad
`except` hides bugs in code you didn't mean to guard.

### Retry with backoff

```python
def retry(fn, attempts=3, base_delay=0.5, retry_on=(provider.Timeout,), sleep=time.sleep):
    for i in range(attempts):
        try:
            return fn()
        except retry_on:              # a tuple in a variable works
            if i == attempts - 1:
                raise                 # out of attempts: the last error, unchanged
            sleep(base_delay * 2 ** i)   # 0.5, 1.0, 2.0 ...
```

Retry only transient errors (`Timeout`). "Unknown city" will fail the same way every time;
retrying it just adds latency. Inject `sleep` (and clocks generally) so tests run instantly.

### Module-level state from a function

```python
LAST_ERROR = None

def repl_step(line):
    global LAST_ERROR         # needed to ASSIGN; reading a module variable doesn't need it
    LAST_ERROR = None         # without `global`, this creates a local and the module var never changes
```

Assigning anywhere in a function makes the name local for the WHOLE function, so reading it
before the assignment gives `UnboundLocalError`.
