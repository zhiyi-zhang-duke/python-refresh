"""06 - Exceptions

Fill in each function, then run:   python 06_exceptions/exercises.py
Run just one exercise:             python 06_exceptions/exercises.py 4
Run exercise 4 onward:             python 06_exceptions/exercises.py 4+

Exercises go from easy (01) to advanced (14). Delete the `raise NotImplementedError`
line when you start one.

provider.py (same folder) is a fake weather provider with its own exception classes:
ProviderError, UnknownCity(ProviderError), Timeout(ProviderError). Read it first.
"""

import json
import shlex
import time
from contextlib import contextmanager, suppress  # noqa: F401

import provider


# ---------------------------------------------------------------- easy ----

def safe_int(text) -> int | None:
    """ex01. Parse an int, or return None if it isn't one. `text` might even be None.

    safe_int(" 42\\n") -> 42        (int() already ignores surrounding whitespace)
    safe_int("4.2")   -> None
    safe_int(None)    -> None      (int(None) raises TypeError, not ValueError)

    Tools: try / except (ValueError, TypeError)
    """
    raise NotImplementedError


def read_command(read=input) -> str | None:
    """ex02. Read one REPL line with read("> ") and return it stripped.

    If the user hits Ctrl-D (EOFError) or Ctrl-C (KeyboardInterrupt), return None so the
    REPL loop can exit cleanly instead of dumping a traceback.

    read_command(lambda prompt: "  list \\n") -> "list"
    read_command(a_function_that_raises_EOFError) -> None

    Tools: except (EOFError, KeyboardInterrupt):  -- a TUPLE of types.
           KeyboardInterrupt is a BaseException, NOT an Exception, so `except Exception` misses it.
    """
    raise NotImplementedError


def temp_or_none(city: str, fetch=provider.get_temp) -> float | None:
    """ex03. Return fetch(city), or None if the provider says the city is unknown.

    temp_or_none("Durham")   -> 21.5
    temp_or_none("Atlantis") -> None
    Any OTHER error (e.g. provider.Timeout) must propagate, not turn into None.

    This file did `import provider`, so the class is `provider.UnknownCity`. A bare
    `except UnknownCity:` is a NameError, and Python only evaluates that name when an
    exception actually arrives, so the bug hides until the first unknown city.

    Tools: except provider.UnknownCity:
    """
    raise NotImplementedError


def describe_error(e: BaseException) -> str:
    """ex04. Turn an exception into a one-line message that says WHAT went wrong.
    ("Something went wrong" hides the type; you'll want it when debugging live.)

    describe_error(provider.UnknownCity("no data for 'Oslo'")) -> "error: UnknownCity: no data for 'Oslo'"
    describe_error(KeyError("phi3"))  -> "error: KeyError: 'phi3'"   (str() of a KeyError adds quotes)
    describe_error(ValueError())      -> "error: ValueError"          (empty message: no trailing ": ")

    Tools: type(e).__name__, str(e)
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def port_for(config: dict, service: str, default: int = 8080) -> int:
    """ex05. EAFP: return int(config["services"][service]["port"]), or `default` if ANY step fails.

    port_for({"services": {"ollama": {"port": "11434"}}}, "ollama") -> 11434
    port_for({"services": {}}, "ollama")                            -> 8080   (KeyError)
    port_for({"services": None}, "ollama")                          -> 8080   (TypeError: None[...])
    port_for({"services": {"ollama": {"port": "abc"}}}, "ollama")   -> 8080   (ValueError from int)

    LBYL ("look before you leap") would need an `in` + isinstance check at every level.
    EAFP ("easier to ask forgiveness") wraps the whole chain in ONE try.

    Tools: try: ... except (KeyError, TypeError, ValueError):
    """
    raise NotImplementedError


def forget(cache: dict, keys: list) -> None:
    """ex06. Delete each key from cache (in place). Keys that aren't there are silently skipped.

    cache = {"a": 1, "b": 2, "c": 3}
    forget(cache, ["a", "missing", "c"])   ->  cache == {"b": 2}

    Gotcha: put the `with suppress(...)` INSIDE the loop. Wrapped around the whole loop, the
    first missing key ends the loop and later keys are never deleted.

    Tools: with suppress(KeyError): del cache[key]      (also fine: cache.pop(key, None))
    """
    raise NotImplementedError


def traced(fn, log: list[str]):
    """ex07. Call fn() inside try/except/else/finally and record which blocks ran, in order.

    Append "try" before calling fn, then:
      fn raised ValueError -> append "except", and traced returns None
      fn returned normally -> append "else",   and traced returns fn's result
      always               -> append "finally"
    Any other exception propagates (after "finally" is logged).

    traced(lambda: 42, log)  -> 42,    log == ["try", "else", "finally"]
    traced(raises_value_err, log) -> None, log == ["try", "except", "finally"]
    traced(raises_key_err, log)   -> KeyError, log == ["try", "finally"]

    Gotcha: `return fn()` inside the try skips the else block entirely.

    Tools: try / except ValueError / else / finally
    """
    raise NotImplementedError


LAST_ERROR = None  # the exception from the most recent failed repl_step, or None


def repl_step(line: str, commands: dict) -> str:
    """ex08. Run one REPL line and return the text to print. The REPL must never crash.

    commands maps a name to a (handler, help_text) tuple; a handler takes the list of args:
        {"temp": (cmd_temp, "temp <city>  current temperature"), ...}

    - split with shlex.split, so  temp "New York"  gives the handler ["New York"]
    - blank line      -> ""
    - "help"          -> one "name: help_text" line per command, sorted by name, joined by "\\n"
    - unknown command -> "unknown command: fly"
    - otherwise       -> call the handler with the args and return str(result)
    - ANY Exception (unbalanced quotes from shlex, anything a handler raises) -> describe_error(e)

    Also keep the module-level LAST_ERROR current: the exception this step caught, or None if
    this step didn't fail. (Assigning a module variable inside a function needs `global`;
    without it you create a local and the module's LAST_ERROR never changes.)

    Tools: shlex.split, name, *args = parts, entry = commands[name]; entry[0](args),
           global LAST_ERROR, except Exception as e
    """
    raise NotImplementedError


class BookingError(Exception):
    """Base for every booking error (given). Catch this to handle all of them."""


class InvalidBooking(BookingError):
    """end <= start (given)."""


class BookingConflict(BookingError):
    """ex09 (part 1). A custom exception that carries data.

    e = BookingConflict("A", 9, 11)          # the EXISTING booking that was hit
    e.room -> "A";  e.start -> 9;  e.end -> 11
    str(e) -> "room A is already booked 9-11"
    isinstance(e, BookingError) -> True

    Gotcha: if you override __init__ and skip super().__init__(message), str(e) is "('A', 9, 11)".

    Tools: super().__init__(f"..."), then store the attributes
    """

    def __init__(self, room: str, start: int, end: int):
        raise NotImplementedError


def book(bookings: dict[str, list[tuple[int, int]]], room: str, start: int, end: int) -> None:
    """ex09 (part 2). Record (start, end) in bookings[room], creating the list if needed.

    end <= start             -> raise InvalidBooking (message up to you)
    overlaps an existing one -> raise BookingConflict(room, existing_start, existing_end)
    Touching is fine: 9-11 then 11-12. On any error, bookings must be left unchanged.

    b = {}
    book(b, "A", 9, 11)   -> b == {"A": [(9, 11)]}
    book(b, "A", 10, 12)  -> BookingConflict: room A is already booked 9-11

    Tools: raise BookingConflict(...), overlap test: start < e and s < end,
           bookings.setdefault(room, []).append(...)
    """
    raise NotImplementedError


class ConfigError(Exception):
    """Raised by load_config (given)."""


def load_config(text: str) -> dict:
    """ex10. Parse a JSON config, translating low-level errors into ConfigError.

    load_config('{"model": "phi3"}')               -> {"model": "phi3", "timeout": 30}
    load_config('{"model": "phi3", "timeout": 5}') -> {"model": "phi3", "timeout": 5}

    - invalid JSON  -> ConfigError(f"invalid JSON: {e.msg}") raised `from e`, so the original
                       json.JSONDecodeError is kept as __cause__ and shows in the traceback
    - not an object ("[1, 2]") -> ConfigError("config must be a JSON object")
    - no "model" key -> ConfigError("missing key: model") raised `from None`, which hides the
                       KeyError ("During handling of the above exception...") from the traceback

    Tools: json.loads, except json.JSONDecodeError as e, raise X from e, raise X from None,
           {**defaults, **data}
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def run_job(pool: list[str], fn, log: list[str]):
    """ex11. Borrow a worker from the pool, run fn(worker), and ALWAYS give the worker back.

    - pool empty -> RuntimeError("no free workers")
    - worker = pool.pop(); return fn(worker)
    - the worker goes back (pool.append) whether fn returns or raises
    - if fn raises: append f"{worker}: {TypeName}: {message}" to log, then re-raise the SAME
      exception with a bare `raise` (no wrapping; the caller sees exactly what fn raised)

    pool = ["w1", "w2"]
    run_job(pool, lambda w: f"ran on {w}", log) -> "ran on w2", pool back to 2 workers

    Tools: try / except Exception as e / finally, bare `raise`
    """
    raise NotImplementedError


@contextmanager
def loaded(name: str, log: list[str]):
    """ex12. A generator-based context manager that guarantees cleanup.

    with loaded("phi3", log) as model:     # model == "phi3" (whatever you yield)
        ...
    log -> ["load phi3", "unload phi3"]

    If the with-body raises ValueError:
    log -> ["load phi3", "failed phi3: ValueError", "unload phi3"], and the error propagates.
    A blank name -> ValueError before anything is logged.

    Gotcha: an exception in the with-body is thrown INTO the generator at the `yield`.
    Without try/finally around the yield, "unload" never runs.

    Keep the @contextmanager decorator. Tools: try: yield name / except Exception as e: ...; raise /
    finally:
    """
    raise NotImplementedError
    yield  # a yield anywhere in the body is what makes this a generator; keep one


def retry(fn, attempts: int = 3, base_delay: float = 0.5,
          retry_on: tuple = (provider.Timeout,), sleep=time.sleep):
    """ex13. Call fn() until it succeeds, with exponential backoff between attempts.

    - at most `attempts` calls in total; attempts < 1 -> ValueError
    - after failed attempt i (0-based), if attempts remain: sleep(base_delay * 2 ** i)
      -> delays 0.5, 1.0, 2.0, ...
    - out of attempts: re-raise the LAST exception
    - an exception that isn't in retry_on propagates immediately, with no sleep
    - return fn()'s result as soon as it succeeds

    `sleep` is injected so tests pass list.append and never actually wait:
        p = provider.FlakyProvider(fail_times=2); delays = []
        retry(lambda: p.get_temp("durham"), sleep=delays.append) -> 21.5;  delays == [0.5, 1.0]

    Tools: for i in range(attempts), except retry_on as e (a tuple variable works),
           raise at the end (or bare raise on the last iteration)
    """
    raise NotImplementedError


class ValidationError(ValueError):
    """ex14 (part 1). One exception carrying every problem found.

    e = ValidationError(["room: required", "start: must be an int 0-24"])
    e.errors -> the list
    str(e)   -> "room: required; start: must be an int 0-24"
    isinstance(e, ValueError) -> True (callers catching ValueError still see it)
    """

    def __init__(self, errors: list[str]):
        raise NotImplementedError


def validate_booking(data: dict) -> dict:
    """ex14 (part 2). Check every field, collect ALL problems, then raise once.

    Checks, in this order, with these exact messages:
      "room: required"               room missing, not a str, or blank after strip
      "start: must be an int 0-24"   start missing, not an int, or outside 0..24
      "end: must be an int 0-24"     same for end
      "end: must be after start"     only if start and end were both valid and end <= start
      "attendees: must be a positive int"   only if attendees is present and isn't an int >= 1

    Any problems -> raise ValidationError(problems). Otherwise return a clean dict:
    validate_booking({"room": " A ", "start": 9, "end": 11})
        -> {"room": "A", "start": 9, "end": 11, "attendees": 1}

    Tools: problems = [], append as you go, `if problems: raise ...` at the END,
           data.get(key), isinstance(x, int)
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
