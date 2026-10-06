"""12 - Capstone REPL: reference solutions.   Check them:  python 12_capstone_repl/solutions.py
Play with them:  python 12_capstone_repl/olm.py --solution
"""

import time
from collections import Counter
from typing import TextIO

import provider


class UsageError(Exception):
    """Raise this from a handler when its arguments are wrong."""


CLIENT = provider


# ---------------------------------------------------------------- easy ----

def parse_line(line: str) -> tuple[str, str]:
    # split() with no separator skips the whitespace run after the command;
    # maxsplit=1 leaves the rest of the line untouched.
    parts = line.strip().split(maxsplit=1)
    if not parts:
        return "", ""
    return parts[0].lower(), parts[1] if len(parts) > 1 else ""


def resolve_model(name: str, models: list[dict]) -> str:
    want = name.strip().casefold()
    names = [m["name"] for m in models]
    for n in names:
        if n.casefold() == want:
            return n
    matches = sorted(n for n in names if n.casefold().startswith(want))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise provider.UnknownModel(f"no model matches {name!r}")
    raise provider.UnknownModel(f"{name!r} is ambiguous: {', '.join(matches)}")


def cmd_list(rest: str, out: TextIO) -> None:
    current = CLIENT.loaded()
    for m in CLIENT.list_models():
        mark = "*" if m["name"] == current else " "     # == compares content; `is` compares identity
        print(f"{mark} {m['name']:<12}{m['size_gb']:>5.1f} GB  {m['family']}", file=out)


def cmd_load(rest: str, out: TextIO) -> None:
    if not rest.strip():
        raise UsageError("load <model>")
    name = resolve_model(rest, CLIENT.list_models())
    info = CLIENT.load(name)
    print(f"loaded {info['name']} ({info['load_ms']} ms)", file=out)


# -------------------------------------------------------------- medium ----

def cmd_help(rest: str, out: TextIO) -> None:
    width = max(len(name) for name in COMMANDS)
    for name in sorted(COMMANDS):
        print(f"{name:<{width}}  {COMMANDS[name][1]}", file=out)


def dispatch(line: str, out: TextIO) -> bool:
    cmd, rest = parse_line(line)
    if not cmd:
        return True
    entry = COMMANDS.get(cmd)
    if entry is None:
        print(f"unknown command: {cmd!r} (try 'help')", file=out)
        return False
    handler, _help = entry
    try:
        handler(rest, out)
    except Exception as e:  # noqa: BLE001 - the REPL's safety net: never die on a handler bug
        print(f"{type(e).__name__}: {e}", file=out)
        return False
    return True


def repl(stdin: TextIO, out: TextIO) -> None:
    while True:
        print("> ", end="", file=out, flush=True)
        line = stdin.readline()
        if not line:                    # EOF. A blank line would be "\n", which is truthy.
            print(file=out)
            break
        line = line.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        dispatch(line, out)
    print("bye", file=out)


def _with_autoload(name: str, out: TextIO, fn, *args):
    """Call fn(name, *args); on NotLoaded, load the model and call it once more."""
    try:
        return fn(name, *args)
    except provider.NotLoaded:
        print(f"(auto-loading {name})", file=out)
        CLIENT.load(name)
        return fn(name, *args)


def cmd_run(rest: str, out: TextIO) -> None:
    parts = rest.split(maxsplit=1)
    if len(parts) < 2:
        raise UsageError("run <model> <prompt>")
    model, prompt = parts
    name = resolve_model(model, CLIENT.list_models())
    # Look the method up on CLIENT at call time, so a swapped-in client is used.
    result = _with_autoload(name, out, CLIENT.run, prompt)
    print(result["text"], file=out)
    print(f"[{result['tokens']} tokens, {result['ms']} ms]", file=out)


def cmd_bench(rest: str, out: TextIO) -> None:
    parts = rest.split()
    if not 1 <= len(parts) <= 2 or (len(parts) == 2 and not parts[1].isdigit()):
        raise UsageError("bench <model> [rounds]")
    rounds = int(parts[1]) if len(parts) == 2 else 3
    if rounds < 1:
        raise UsageError("bench <model> [rounds]")
    name = resolve_model(parts[0], CLIENT.list_models())
    results = _with_autoload(name, out, CLIENT.benchmark, rounds)

    for r in sorted(results, key=lambda r: r["round"]):   # provider returns completion order
        print(f"round {r['round']}: {r['ms']} ms, {r['tokens']} tokens", file=out)
    times = [r["ms"] for r in results]
    total_tokens = sum(r["tokens"] for r in results)
    tok_per_s = total_tokens / (sum(times) / 1000)
    print(f"min {min(times)} ms | avg {sum(times) / len(times):.1f} ms | {tok_per_s:.1f} tok/s",
          file=out)


class ProviderClient:
    def __init__(self):
        self.calls = Counter()

    def _call(self, fn, *args):
        self.calls[fn.__name__] += 1
        return fn(*args)

    def list_models(self) -> list[dict]:
        return self._call(provider.list_models)

    def loaded(self) -> str | None:
        return self._call(provider.loaded)

    def load(self, name: str) -> dict:
        return self._call(provider.load, name)

    def unload(self) -> str | None:
        return self._call(provider.unload)

    def run(self, name: str, prompt: str) -> dict:
        return self._call(provider.run, name, prompt)

    def benchmark(self, name: str, rounds: int = 3) -> list[dict]:
        return self._call(provider.benchmark, name, rounds)


# ------------------------------------------------------------ advanced ----

class RetryingClient(ProviderClient):
    # `sleep=time.sleep` is evaluated once, at def time. Fine for a function object;
    # it's the mutable-default trap only for things like [] or {}.
    def __init__(self, attempts: int = 3, base_delay: float = 0.1, sleep=time.sleep):
        super().__init__()
        self.attempts = attempts
        self.base_delay = base_delay
        self.sleep = sleep

    def _call(self, fn, *args):
        for attempt in range(self.attempts):
            try:
                return super()._call(fn, *args)
            except provider.Timeout:
                if attempt == self.attempts - 1:
                    raise                       # bare raise keeps the original traceback
                self.sleep(self.base_delay * 2 ** attempt)


class CachingClient(RetryingClient):
    def __init__(self, ttl: float = 30.0, clock=time.monotonic, **kwargs):
        super().__init__(**kwargs)
        self.ttl = ttl
        self.clock = clock
        self._cached: tuple[list[dict], float] | None = None    # (models, stored_at)

    def list_models(self) -> list[dict]:
        now = self.clock()
        if self._cached is not None and now - self._cached[1] < self.ttl:
            return self._cached[0]
        try:
            models = super().list_models()      # goes through the retrying _call
        except provider.Timeout:
            if self._cached is not None:
                return self._cached[0]          # stale beats nothing
            raise
        self._cached = (models, now)
        return models


def main(argv: list[str], stdin: TextIO, out: TextIO, client=None) -> int:
    global CLIENT       # without this, `CLIENT = client` would make a new LOCAL variable
    if client is not None:
        CLIENT = client
    if not argv:
        repl(stdin, out)
        return 0
    return 0 if dispatch(" ".join(argv), out) else 1


def cmd_fastest(rest: str, out: TextIO) -> None:
    rest = rest.strip()
    if rest and not rest.isdigit():
        raise UsageError("fastest [rounds]")
    rounds = int(rest) if rest else 2
    if rounds < 1:
        raise UsageError("fastest [rounds]")

    previous = CLIENT.loaded()
    ranked: list[tuple[float, str]] = []
    failed: list[str] = []
    try:
        for m in CLIENT.list_models():
            name = m["name"]
            try:
                CLIENT.load(name)
                results = CLIENT.benchmark(name, rounds)
            except provider.ProviderError as e:     # degrade, don't abort
                failed.append(f"{name} ({type(e).__name__})")
                continue
            ranked.append((sum(r["ms"] for r in results) / len(results), name))
    finally:                                         # restore the session, even on a crash
        if previous is None:
            CLIENT.unload()
        else:
            CLIENT.load(previous)

    if not ranked:
        print("no results", file=out)
    for rank, (avg, name) in enumerate(sorted(ranked), start=1):
        print(f"{rank}. {name:<12}{avg:>8.1f} ms", file=out)
    if failed:
        print("failed: " + ", ".join(failed), file=out)


# ------------------------------------------------------- command table ----

COMMANDS: dict = {
    "help": (cmd_help, "show this help"),
    "list": (cmd_list, "list models (* = loaded)"),
    "load": (cmd_load, "load <model>"),
    "run": (cmd_run, "run <model> <prompt>"),
    "bench": (cmd_bench, "bench <model> [rounds]"),
    "fastest": (cmd_fastest, "fastest [rounds]"),
}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
