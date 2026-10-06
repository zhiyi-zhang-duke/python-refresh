"""12 - Capstone: the model-runner REPL

The interview-shaped topic. You build `olm`, a REPL on top of provider.py (a fake
local model runner), one phase at a time. Later phases call earlier ones, so go in
order. Read the contract at the top of provider.py first, then probe it:

    cd 12_capstone_repl
    python -c "import provider; print(provider.list_models())"

Fill in each piece, then run:   python 12_capstone_repl/exercises.py
Run just one exercise:          python 12_capstone_repl/exercises.py 4
Run exercise 4 onward:          python 12_capstone_repl/exercises.py 4+
Play with it by hand:           python 12_capstone_repl/olm.py      (needs ex01-ex05 + ex11)

Rules of the house (they're what makes the later phases cheap):
  - Every handler has the signature  cmd_x(rest: str, out: TextIO) -> None
  - Handlers write with print(..., file=out) and talk to CLIENT, never to `provider`
    directly. CLIENT starts out as the provider module itself; ex08-ex10 build
    wrappers with the same method names, so swapping one in is a one-line change.
  - Handlers RAISE on bad input (UsageError, provider errors). Only dispatch()
    prints errors. One place to catch, one format.

See README.md for how to run this as a timed drill.
"""

import time
from typing import TextIO

import provider     # errors stay namespaced: provider.UnknownModel, provider.NotLoaded, ...


class UsageError(Exception):
    """Raise this from a handler when its arguments are wrong."""


CLIENT = provider   # swap in ProviderClient / RetryingClient / CachingClient later


# ---------------------------------------------------------------- easy ----

def parse_line(line: str) -> tuple[str, str]:
    """ex01. Split a REPL line into (command, rest).

    Strip the line. The command is the first word, lowercased. `rest` is everything
    after the whitespace that follows the command, kept VERBATIM (inner spaces too;
    outer whitespace stripped). Missing parts are "".

    parse_line("  RUN phi3   tell me  a joke  ") -> ("run", "phi3   tell me  a joke")
    parse_line("list")                          -> ("list", "")
    parse_line("   ")                           -> ("", "")

    Why not shlex.split? It would turn the prompt into a list of words and eat
    quotes and double spaces. The prompt must reach the model exactly as typed.

    Tools: str.split(maxsplit=1) with no separator (it skips the whitespace run)
    """
    raise NotImplementedError


def resolve_model(name: str, models: list[dict]) -> str:
    """ex02. Turn what the user typed into a real model name. Case-insensitive.

    `models` is what provider.list_models() returns.
      1. An exact (case-insensitive) match wins, even if it's also a prefix of another.
      2. Otherwise, if exactly one model name starts with it, return that one.
      3. No match:  raise provider.UnknownModel(f"no model matches {name!r}")
      4. Several:   raise provider.UnknownModel(f"{name!r} is ambiguous: a, b")
                    with the candidates sorted and joined by ", "

    resolve_model("phi", models)        -> "phi3:mini"
    resolve_model("LLAMA3:8B", models)  -> "llama3:8b"
    resolve_model("llama3", models)     -> UnknownModel("'llama3' is ambiguous: llama3:70b, llama3:8b")
    resolve_model("gpt4", models)       -> UnknownModel("no model matches 'gpt4'")

    Tools: list comprehension over [m["name"] for m in models], str.casefold,
           str.startswith, ", ".join(sorted(...))
    """
    raise NotImplementedError


def cmd_list(rest: str, out: TextIO) -> None:
    """ex03a. Print one line per model, in provider order. `rest` is ignored.

    Line format:  f"{mark} {name:<12}{size_gb:>5.1f} GB  {family}"
    where mark is "*" for the loaded model (CLIENT.loaded()) and " " otherwise.

      phi3:mini     2.3 GB  phi
    * gemma2:2b     1.6 GB  gemma
      llama3:70b   39.0 GB  llama

    Tools: CLIENT.list_models(), CLIENT.loaded(), print(..., file=out)
    """
    raise NotImplementedError


def cmd_load(rest: str, out: TextIO) -> None:
    """ex03b. Load a model by name or unique prefix.

    rest blank           -> raise UsageError("load <model>")
    otherwise            -> resolve_model(rest, CLIENT.list_models()), CLIENT.load(name),
                            then print f"loaded {name} ({load_ms} ms)" using the dict
                            CLIENT.load returns
    Let provider errors (UnknownModel, ...) propagate. dispatch() prints them.

    cmd_load("phi", out)   -> out: "loaded phi3:mini (230 ms)\\n"

    Tools: the return value of provider.load (check the contract, don't guess)
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def cmd_help(rest: str, out: TextIO) -> None:
    """ex04a. For each command in sorted(COMMANDS), print f"{name:<{width}}  {help_text}"
    where width is the length of the longest command name.

    Tools: max(len(n) for n in COMMANDS), a nested format spec
    """
    raise NotImplementedError


def dispatch(line: str, out: TextIO) -> bool:
    """ex04b. Run one command line. Return True if it went fine, False if an error
    was printed.

    First, fill in COMMANDS at the bottom of this file: command name -> a TUPLE of
    (handler function, help text). Register help, list, load, run, bench and fastest
    (later handlers can be stubs for now).

      - blank line                -> do nothing, return True
      - unknown command           -> print f"unknown command: {cmd!r} (try 'help')", return False
      - known command             -> call the handler with (rest, out)
      - the handler raises ANY Exception
                                  -> print f"{type(e).__name__}: {e}", return False

    dispatch("load gpt4", out)  -> False, out: "UnknownModel: no model matches 'gpt4'\\n"

    Tools: parse_line, COMMANDS.get(cmd), entry[0](rest, out) or
           `handler, _help = entry`, try/except Exception as e
    """
    raise NotImplementedError


def repl(stdin: TextIO, out: TextIO) -> None:
    """ex05. The loop.

    Each turn:
      - print the prompt "> " with no newline (flush=True, so a real terminal shows it)
      - read a line; "" means EOF -> print an empty line (the cursor is still on the
        prompt), then stop
      - strip it; blank -> next turn
      - "exit" / "quit" (any case) -> stop
      - otherwise dispatch(line, out)
    After the loop, print "bye".

    repl(io.StringIO("load phi\\nexit\\n"), out)
    out: "> loaded phi3:mini (230 ms)\\n> bye\\n"

    repl(io.StringIO("bogus\\n"), out)      (no exit, just EOF)
    out: "> unknown command: 'bogus' (try 'help')\\n> \\nbye\\n"

    Tools: stdin.readline(), print("> ", end="", file=out, flush=True).
           With input() you'd write `except (EOFError, KeyboardInterrupt): break`.
    """
    raise NotImplementedError


def cmd_run(rest: str, out: TextIO) -> None:
    """ex06. run <model> <prompt...>, with auto-load.

    Split `rest` into the model token and the prompt (kept verbatim). Missing either
    -> raise UsageError("run <model> <prompt>"). Resolve the model name.
    Call CLIENT.run(name, prompt). If it raises provider.NotLoaded, print
    f"(auto-loading {name})", CLIENT.load(name), and call run again.
    Then print the text, then f"[{tokens} tokens, {ms} ms]".

    cmd_run("phi tell me  a joke", out)   (nothing loaded)
    out: "(auto-loading phi3:mini)\\nphi3:mini says: tell me  a joke\\n[6 tokens, 182 ms]\\n"

    Tools: rest.split(maxsplit=1), `except provider.NotLoaded:` (namespaced, because
           we did `import provider`), resolve_model
    """
    raise NotImplementedError


def cmd_bench(rest: str, out: TextIO) -> None:
    """ex07. bench <model> [rounds]   (rounds defaults to 3, must be a positive int)

    Bad arguments -> raise UsageError("bench <model> [rounds]").
    Resolve the model, auto-load it like cmd_run does if CLIENT.benchmark raises
    provider.NotLoaded (print the same "(auto-loading ...)" line).

    The provider returns rounds in COMPLETION order. Print them in ROUND order using
    each result's "round" field, then a summary:

        round 1: 145 ms, 64 tokens
        round 2: 115 ms, 64 tokens
        round 3: 160 ms, 64 tokens
        min 115 ms | avg 140.0 ms | 457.1 tok/s

    tok/s = total tokens / total seconds  (total ms / 1000).

    Tools: sorted(results, key=lambda r: r["round"]), min / sum / len, str.isdigit,
           maybe a small helper shared with cmd_run for the auto-load retry
    """
    raise NotImplementedError


class ProviderClient:
    """ex08. The seam. Same method names and return values as `provider`, so
    `CLIENT = ProviderClient()` is a drop-in swap for `CLIENT = provider`.

    __init__()
        self.calls = a Counter (or dict) of how many times each provider function
        was called through this client, keyed by function name.
    _call(fn, *args)
        THE chokepoint: count fn.__name__ in self.calls, then return fn(*args).
    list_models(), loaded(), load(name), unload(), run(name, prompt), benchmark(name, rounds=3)
        Each one is a single line: return self._call(provider.<same name>, ...args).

    c = ProviderClient()
    c.load("phi3:mini"); c.run("phi3:mini", "hi")
    c.calls -> {"load": 1, "run": 1}

    Why bother: ex09 adds retries by overriding only _call, ex10 adds caching by
    overriding only list_models. One place each. (In the live interview you'd edit
    this class in place; the subclasses just let each phase be checked separately.)

    Tools: collections.Counter, fn.__name__, *args forwarding
    """

    def __init__(self):
        raise NotImplementedError

    def _call(self, fn, *args):
        raise NotImplementedError

    def list_models(self) -> list[dict]:
        raise NotImplementedError

    def loaded(self) -> str | None:
        raise NotImplementedError

    def load(self, name: str) -> dict:
        raise NotImplementedError

    def unload(self) -> str | None:
        raise NotImplementedError

    def run(self, name: str, prompt: str) -> dict:
        raise NotImplementedError

    def benchmark(self, name: str, rounds: int = 3) -> list[dict]:
        raise NotImplementedError


# ------------------------------------------------------------ advanced ----

class RetryingClient(ProviderClient):
    """ex09. Retry with exponential backoff, by overriding ONLY _call.

    RetryingClient(attempts=3, base_delay=0.1, sleep=time.sleep)
        Store them; call super().__init__() so self.calls exists. `sleep` is
        injected so tests don't actually wait.
    _call(fn, *args)
        Try up to `attempts` times. Retry ONLY provider.Timeout: UnknownModel /
        NotLoaded / anything else propagates immediately (retrying "that doesn't
        exist" just wastes the user's time). Between attempts sleep
        base_delay * 2**i (0.1, 0.2, 0.4, ...). Don't sleep after the last attempt;
        re-raise that last Timeout.

    provider.set_flaky(2, only="run")
    c = RetryingClient(sleep=slept.append)
    c.run("phi3:mini", "hi")    -> succeeds on attempt 3; slept == [0.1, 0.2]

    Tools: for attempt in range(self.attempts), super()._call(fn, *args),
           `except provider.Timeout:`, `raise` (bare, inside except) to re-raise
    """

    def __init__(self, attempts: int = 3, base_delay: float = 0.1, sleep=time.sleep):
        raise NotImplementedError

    def _call(self, fn, *args):
        raise NotImplementedError


class CachingClient(RetryingClient):
    """ex10. A TTL cache for list_models, by overriding ONLY list_models.

    CachingClient(ttl=30.0, clock=time.monotonic, **kwargs)
        Store ttl and clock (injected so tests control time); pass **kwargs
        (attempts, base_delay, sleep) up to RetryingClient.
    list_models()
        If a cached copy is younger than ttl seconds (age < ttl), return it without
        calling the provider. Otherwise fetch through super().list_models() (so the
        retry still applies), remember the result and when, and return it.
        Stale-on-error: if the refresh still raises provider.Timeout after retries
        but you have an old copy, return the old copy. No copy -> let it raise.

    now = [0.0]
    c = CachingClient(ttl=30, clock=lambda: now[0])
    c.list_models(); c.list_models()        -> provider.list_models called once
    now[0] = 31; c.list_models()            -> called again

    Tools: self._cached = None / (value, stored_at), self.clock(), super().list_models()
    Why monotonic: time.time() can jump backwards (NTP), making ages negative.
    """

    def __init__(self, ttl: float = 30.0, clock=time.monotonic, **kwargs):
        raise NotImplementedError

    def list_models(self) -> list[dict]:
        raise NotImplementedError


def main(argv: list[str], stdin: TextIO, out: TextIO, client=None) -> int:
    """ex11. One entry point, two modes, one dispatch.

    - If `client` is given, install it as the module-level CLIENT (you'll need
      `global CLIENT`, because you're rebinding a module name inside a function).
    - No argv: run the REPL on stdin, return 0.
    - argv given (direct mode, e.g. `python olm.py run phi tell me a joke`): the shell
      has already split the words, so join argv with spaces into one line, dispatch
      it, and return 0 if dispatch succeeded, else 1.

    main(["run", "phi", "hello"], stdin, out)    -> 0
    out: "(auto-loading phi3:mini)\\nphi3:mini says: hello\\n[3 tokens, 137 ms]\\n"
    main(["bogus"], stdin, out)                  -> 1
    main([], io.StringIO("list\\nexit\\n"), out)  -> 0, REPL transcript in out

    Tools: sys.argv[1:] is what olm.py passes in; " ".join(argv); dispatch; repl
    """
    raise NotImplementedError


def cmd_fastest(rest: str, out: TextIO) -> None:
    """ex12. fastest [rounds]: benchmark EVERY model and rank them. (rounds default 2,
    must be a positive int, else raise UsageError("fastest [rounds]").)

    For each model in CLIENT.list_models() order: load it, benchmark it, average
    its round ms. If a model raises any provider.ProviderError, record it as
    failed and keep going: one bad model must not kill the ranking.

    Then print, fastest first (ties broken by name):
        f"{rank}. {name:<12}{avg_ms:>8.1f} ms"
    then, if any failed, one line:  "failed: mistral:7b (Timeout), ..."  in the order
    they failed. If nothing succeeded, print "no results" instead of the ranking.

    Don't clobber the user's session: whatever model was loaded before (or None)
    must be loaded again afterwards, even if something blew up. That's a
    try/finally, using CLIENT.loaded() / CLIENT.load() / CLIENT.unload().

        1. gemma2:2b       95.0 ms
        2. phi3:mini      130.0 ms
        ...
        failed: mistral:7b (Timeout)

    Tools: try/except provider.ProviderError per model, list of (avg, name) tuples
           sorts by avg then name, enumerate(..., start=1), try/finally
    """
    raise NotImplementedError


# ------------------------------------------------------- command table ----
# ex04: fill this in. It lives down here because it refers to every handler above.
# name -> (handler, help text)

COMMANDS: dict = {}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
