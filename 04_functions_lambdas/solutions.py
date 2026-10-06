"""04 - Functions & Lambdas: reference solutions.   Check them:  python 04_functions_lambdas/solutions.py"""

import functools
import shlex
import time
from typing import Callable


# ---------------------------------------------------------------- easy ----

def names_by_size(models: list[dict]) -> list[str]:
    # Negating the number flips only that part of the order; the name stays A-Z.
    ordered = sorted(models, key=lambda m: (-m["size_gb"], m["name"]))
    return [m["name"] for m in ordered]


def active_names(users: list[dict]) -> list[str]:
    return [u["name"] for u in users if u.get("active")]


def latency_stats(samples_ms: list[float]) -> tuple:
    if not samples_ms:
        return None, None, None
    return min(samples_ms), max(samples_ms), sum(samples_ms) / len(samples_ms)


def dispatch(commands: dict[str, tuple[Callable, str]], line: str) -> str:
    parts = line.split()
    if not parts:
        return ""
    name, args = parts[0].lower(), parts[1:]
    if name not in commands:
        return f"unknown command: {name}"
    handler, _help = commands[name]
    return handler(args)


# -------------------------------------------------------------- medium ----

def book(room, *guests, start, hours=1):
    # Anything after *guests can only be passed by keyword.
    if hours <= 0:
        raise ValueError("hours must be positive")
    return {"room": room, "guests": list(guests), "start": start, "hours": hours}


def make_counter(start: int = 0) -> Callable[[], int]:
    current = start

    def counter() -> int:
        nonlocal current  # without this, `current += 1` makes a new local -> UnboundLocalError
        value = current
        current += 1
        return value

    return counter


def write_log(log: list[str], level: str, msg: str) -> None:
    log.append(f"[{level.upper()}] {msg}")


def build_loggers(log: list[str], levels: list[str]) -> dict[str, Callable[[str], None]]:
    # partial binds `level` NOW, so each logger keeps its own level.
    return {level: functools.partial(write_log, log, level) for level in levels}


def pipeline(*steps: Callable) -> Callable:
    def run(value):
        return functools.reduce(lambda acc, step: step(acc), steps, value)

    return run


def run_repl(read: Callable[[str], str], commands: dict[str, tuple[Callable, str]]) -> list[str]:
    out = []
    while True:
        try:
            line = read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line == "quit":
            break
        try:
            out.append(dispatch(commands, line))
        except ValueError as e:
            out.append(f"error: {e}")
    out.append("bye")
    return out


# ------------------------------------------------------------ advanced ----

def count_calls(fn: Callable) -> Callable:
    @functools.wraps(fn)  # copies __name__, __doc__, etc. onto the wrapper
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return fn(*args, **kwargs)

    wrapper.calls = 0
    return wrapper


def timed(sink: list, clock: Callable[[], float] = time.perf_counter) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = clock()
            try:
                return fn(*args, **kwargs)
            finally:  # runs on return AND on exception
                sink.append((fn.__name__, clock() - start))

        return wrapper

    return decorator


def retry(times: int = 3, exceptions: tuple = (Exception,)) -> Callable:
    if times < 1:
        raise ValueError("times must be >= 1")

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise  # re-raise the last failure with its traceback

        return wrapper

    return decorator


def memoize(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args):
        if args not in wrapper.cache:  # `in`, so cached None/0 still count as hits
            wrapper.cache[args] = fn(*args)
        return wrapper.cache[args]

    wrapper.cache = {}
    return wrapper


COMMANDS: dict[str, tuple[Callable, str]] = {}


def command(name: str, help: str = "") -> Callable:
    def decorator(fn: Callable) -> Callable:
        if name in COMMANDS:
            raise ValueError(f"duplicate command: {name}")
        COMMANDS[name] = (fn, help)
        return fn

    return decorator


def run_command(line: str) -> str:
    parts = shlex.split(line)
    if not parts:
        return ""
    name, args = parts[0], parts[1:]
    if name not in COMMANDS:
        return f"unknown command: {name}"
    return COMMANDS[name][0](args)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
