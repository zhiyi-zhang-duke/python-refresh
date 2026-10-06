"""04 - Functions & Lambdas

Fill in each function, then run:   python 04_functions_lambdas/exercises.py
Run just one exercise:             python 04_functions_lambdas/exercises.py 4
Run exercise 4 onward:             python 04_functions_lambdas/exercises.py 4+

Exercises go from easy (01) to advanced (14). Delete the `raise NotImplementedError`
line when you start one.
"""

import functools
import shlex
import time
from typing import Callable


# Shape used by ex04, ex09 and ex14: name -> (handler, help text).
# A handler takes the list of argument strings and returns the output string.
#   {"load": (load_handler, "Load a model"), "list": (list_handler, "List models")}


# ---------------------------------------------------------------- easy ----

def names_by_size(models: list[dict]) -> list[str]:
    """ex01. Return model names, largest size_gb first; ties broken by name A-Z.
    Don't mutate the input list.

    models = [{"name": "phi3:mini", "size_gb": 2.3}, {"name": "llama3:70b", "size_gb": 39.0},
              {"name": "gemma:2b", "size_gb": 1.6}, {"name": "aya:8b", "size_gb": 2.3}]
    names_by_size(models) -> ["llama3:70b", "aya:8b", "phi3:mini", "gemma:2b"]

    Tools: sorted(..., key=lambda m: ...) with a TUPLE key; negate a number to flip
           just that part of the order; [m["name"] for m in ...]
    """
    raise NotImplementedError


def active_names(users: list[dict]) -> list[str]:
    """ex02. Names of users whose "active" is truthy, in input order.
    A user with no "active" key counts as inactive.

    active_names([{"name": "ana", "active": True}, {"name": "bo", "active": False},
                  {"name": "cy"}]) -> ["ana"]

    Tools: a comprehension with an `if` clause, dict.get. (Then try it once as
           list(map(lambda ..., filter(lambda ..., users))) and see which reads better.)
    """
    raise NotImplementedError


def latency_stats(samples_ms: list[float]) -> tuple:
    """ex03. Return (lowest, highest, mean) as one tuple. Empty input -> (None, None, None).

    latency_stats([12, 40, 23]) -> (12, 40, 25.0)
    lo, hi, avg = latency_stats([5])    # caller unpacks: (5, 5, 5.0)

    Tools: min, max, sum, len; `return a, b, c` builds a tuple
    """
    raise NotImplementedError


def dispatch(commands: dict[str, tuple[Callable, str]], line: str) -> str:
    """ex04. Run one REPL line against a command table and return the handler's output.

    commands maps name -> (handler, help_text). Strip the line and split on whitespace;
    the first word (lowercased) is the command, the rest is a LIST of args that you
    pass to the handler as ONE argument.

    Blank line           -> ""
    Unknown command "x"  -> "unknown command: x"

    commands = {"load": (lambda args: "loaded " + " ".join(args), "Load a model")}
    dispatch(commands, "  LOAD phi3 mini\\n") -> "loaded phi3 mini"

    Tools: str.strip, str.split, `in`, indexing the tuple then calling it: entry[0](args)
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def book(*args, **kwargs):
    """ex05. Write the REAL signature yourself (replace *args, **kwargs).

    book takes: a room (positional), any number of guest names (positional),
    then `start` (KEYWORD-ONLY, required) and `hours` (keyword-only, default 1).
    Return {"room": ..., "guests": [...], "start": ..., "hours": ...}.
    hours <= 0 -> ValueError.

    book("A", "jack", "becca", start=9)   -> {"room": "A", "guests": ["jack", "becca"],
                                             "start": 9, "hours": 1}
    book("A", "jack", 9)                  -> TypeError (9 is just another guest; start missing)
    book("A", start=9, minutes=30)        -> TypeError (unknown keyword)

    Tools: def f(pos, *rest, kw_only, kw_default=1). Everything after *rest is keyword-only.
           (A bare `*` does the same when you don't want *rest.) Python raises the
           TypeErrors for you once the signature is right.
    """
    raise NotImplementedError


def make_counter(start: int = 0) -> Callable[[], int]:
    """ex06. Return a function that returns start, start+1, start+2, ... on each call.
    Each counter made by make_counter is independent.

    c = make_counter(5);  c() -> 5;  c() -> 6
    d = make_counter();   d() -> 0     (c is unaffected)

    Tools: a nested def, `nonlocal` (needed because you ASSIGN to the outer variable)
    """
    raise NotImplementedError


def write_log(log: list[str], level: str, msg: str) -> None:
    """Helper for ex07 (already done): append "[LEVEL] msg" to log."""
    log.append(f"[{level.upper()}] {msg}")


def build_loggers(log: list[str], levels: list[str]) -> dict[str, Callable[[str], None]]:
    """ex07. Return {level: logger} where logger(msg) calls write_log(log, level, msg).

    log = []
    loggers = build_loggers(log, ["info", "error"])
    loggers["error"]("disk full");  loggers["info"]("ok")
    log -> ["[ERROR] disk full", "[INFO] ok"]

    Tools: functools.partial(write_log, log, level) pre-fills leading args.
    Watch out: {lvl: lambda msg: write_log(log, lvl, msg) for lvl in levels} is a bug;
               see 08_scope_and_gotchas ex08 (late binding).
    """
    raise NotImplementedError


def pipeline(*steps: Callable) -> Callable:
    """ex08. Return a function that feeds its input through each step, LEFT to right.
    No steps -> the returned function gives its input back unchanged.

    clean = pipeline(str.strip, str.lower, str.split)
    clean("  Load PHI3  ") -> ["load", "phi3"]
    pipeline()(42) -> 42

    Tools: a for loop, or functools.reduce(lambda acc, f: f(acc), steps, value)
    """
    raise NotImplementedError


def run_repl(read: Callable[[str], str], commands: dict[str, tuple[Callable, str]]) -> list[str]:
    """ex09. Drive a REPL with an injected input function; return every line it printed.

    Loop:
      - line = read("> ")      (read behaves like the builtin input)
      - EOFError or KeyboardInterrupt from read -> stop
      - strip it; skip blank lines; "quit" -> stop
      - otherwise output dispatch(commands, line)   (your ex04)
      - if the handler raises ValueError, output "error: <message>" and keep going
    Always finish by outputting "bye".

    lines "load phi3", "quit"   -> ["loaded phi3", "bye"]
    lines "load phi3", <Ctrl-D> -> ["loaded phi3", "bye"]

    Tools: while True, try/except (EOFError, KeyboardInterrupt) (a TUPLE catches either),
           except ValueError as e: str(e)
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def count_calls(fn: Callable) -> Callable:
    """ex10. Decorator: forward every call to fn (any args/kwargs, return its result)
    and count calls in a `.calls` attribute on the wrapper. Keep fn's __name__ and __doc__.

    @count_calls
    def greet(name, *, punct="!"): return "hi " + name + punct

    greet("jack"); greet("becca", punct="?")
    greet.calls -> 2;   greet.__name__ -> "greet"

    Tools: def wrapper(*args, **kwargs): ... fn(*args, **kwargs); @functools.wraps(fn);
           functions are objects, so wrapper.calls = 0 works
    """
    raise NotImplementedError


def timed(sink: list, clock: Callable[[], float] = time.perf_counter) -> Callable:
    """ex11. Decorator FACTORY: after each call, append (fn.__name__, seconds) to sink,
    measured with clock(). Record the timing even when fn raises (and let it raise).

    @timed(records, clock=fake_clock)
    def add(a, b): return a + b

    add(1, 2) -> 3;  records -> [("add", 0.25)]   (if fake_clock returned 10.0 then 10.25)

    Tools: three levels of def (factory -> decorator -> wrapper), try/finally,
           functools.wraps
    """
    raise NotImplementedError


def retry(times: int = 3, exceptions: tuple = (Exception,)) -> Callable:
    """ex12. Decorator factory: call fn up to `times` attempts total. Retry only when it
    raises one of `exceptions`; after the last attempt, re-raise that exception.
    Any other exception propagates immediately. times < 1 -> ValueError (raise it
    when retry(...) itself is called).

    @retry(times=3, exceptions=(ConnectionError,))
    def fetch(): ...            # fails twice, then works -> returns the 3rd result

    Tools: for attempt in range(times), except exceptions as e (a tuple works here),
           bare `raise` re-raises the current exception
    """
    raise NotImplementedError


def memoize(fn: Callable) -> Callable:
    """ex13. Decorator: cache results by positional args in a `.cache` dict on the
    wrapper ({args_tuple: result}). Same args -> fn is NOT called again,
    even when the cached result is falsy (0, None, "").

    @memoize
    def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)
    fib(90) -> 2880067194370816120   (instant)

    Tools: def wrapper(*args): args is already a hashable tuple; `key in cache`,
           NOT `if cache.get(key)`; functools.wraps. (functools.lru_cache/cache do this
           for real; write it by hand here.)
    """
    raise NotImplementedError


COMMANDS: dict[str, tuple[Callable, str]] = {}


def command(name: str, help: str = "") -> Callable:
    """ex14 (part 1). Decorator factory that registers a handler in COMMANDS.

    @command("weather", help="Show weather for a city")
    def weather(args): return "Weather for " + " ".join(args)

    COMMANDS["weather"] -> (weather, "Show weather for a city")
    The decorator returns the function UNCHANGED (weather is still the plain function).
    Registering a name that's already in COMMANDS -> ValueError.

    Tools: a factory returning a decorator; the decorator does COMMANDS[name] = (fn, help)
           and returns fn. Mutating a module-level dict needs no `global`.
    """
    raise NotImplementedError


def run_command(line: str) -> str:
    """ex14 (part 2). Like dispatch, but against COMMANDS and with shell-style quoting.

    run_command('weather "New York"') -> handler gets ["New York"]
    run_command("weather New York")   -> handler gets ["New", "York"]
    Blank -> "";  unknown "x" -> "unknown command: x"

    Tools: shlex.split
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
