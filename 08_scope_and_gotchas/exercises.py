"""08 - Scope & Gotchas

Fill in each function, then run:   python 08_scope_and_gotchas/exercises.py
Run just one exercise:             python 08_scope_and_gotchas/exercises.py 4
Run exercise 4 onward:             python 08_scope_and_gotchas/exercises.py 4+

Every exercise here is a piece of Python semantics that bites. Each docstring states
the task, then names the trap. The tests probe the trap directly, so code that "looks
right" can still fail. Delete the `raise NotImplementedError` line when you start one.
"""

import copy
from typing import Callable


# ---------------------------------------------------------------- easy ----

LOADED_MODEL: str | None = None


def load_model(name: str) -> str | None:
    """ex01 (part 1). Set the module-level LOADED_MODEL to `name` and return the
    PREVIOUS value.

    load_model("phi3") -> None      (LOADED_MODEL is now "phi3")
    load_model("llama3") -> "phi3"

    Trap: assigning to a name inside a function makes it LOCAL to that function,
    for the whole function. Without `global LOADED_MODEL`, the assignment creates a
    local and the module value never changes (or reading it first raises
    UnboundLocalError).

    Tools: global
    """
    raise NotImplementedError


def unload_model() -> str | None:
    """ex01 (part 2). Set LOADED_MODEL back to None and return the previous value."""
    raise NotImplementedError


def model_status(current: str | None, requested: str) -> str:
    """ex02. Decide what a `load` command should do.

    current is None        -> "load <requested>"
    current == requested   -> "already loaded"
    otherwise              -> "switch <current> -> <requested>"

    model_status(None, "phi3")     -> "load phi3"
    model_status("phi3", "phi3")   -> "already loaded"
    model_status("phi3", "llama3") -> "switch phi3 -> llama3"

    Trap: `is` checks IDENTITY (same object), `==` checks VALUE. `x is None` is right
    (None is a singleton). `a is b` on strings sometimes works by accident (interning)
    and fails for strings built at runtime, e.g. from input() or "".join(...).
    Same for `is not` vs `!=`.

    Tools: is None, ==
    """
    raise NotImplementedError


def is_yes(answer: str) -> bool:
    """ex03. True only for "y" or "yes" (any case, surrounding whitespace ignored).
    Return a real bool.

    is_yes("  YES\\n") -> True;   is_yes("no") -> False;   is_yes("") -> False

    Trap 1: `a == "y" or "yes"` parses as `(a == "y") or "yes"`, which is always truthy.
    Trap 2: `a in "yes"` is a SUBSTRING test: "" and "es" are both "in" "yes".
    Trap 3: strings are immutable; a bare `answer.strip()` on its own line does nothing.

    Tools: str.strip, str.lower, `in` with a set/tuple: a in {"y", "yes"}
    """
    raise NotImplementedError


def make_grid(rows: int, cols: int, fill=0) -> list[list]:
    """ex04. Return a rows x cols grid (list of lists) filled with `fill`, where
    every row is an independent list.

    make_grid(2, 3) -> [[0, 0, 0], [0, 0, 0]]

    Trap: [[fill] * cols] * rows repeats the SAME inner list `rows` times;
    grid[0][0] = 1 then changes every row.

    Tools: a list comprehension for the outer list: [... for _ in range(rows)]
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def parse_command(line: str) -> tuple[str, list[str]]:
    """ex05. Split a REPL line into (command lowercased, list of args).
    Blank line -> ("", []).

    parse_command("  Weather New York ") -> ("weather", ["New", "York"])
    parse_command("list")                -> ("list", [])

    Trap: `cmd, *args = line.split()` is great, but raises ValueError on an empty
    list (nothing to put in cmd). Starred targets always produce a LIST, even if empty.

    Tools: star unpacking: first, *rest = items
    """
    raise NotImplementedError


def log_event(event: str, history: list[str] | None = None) -> list[str]:
    """ex06. Append event to history and return history. If no history is passed,
    start a NEW empty list for this call. If one is passed (even an empty one),
    append to THAT list and return it.

    log_event("a") -> ["a"];   log_event("b") -> ["b"]   (not ["a", "b"])
    h = [];  log_event("x", h) is h  -> True, and h == ["x"]

    Trap 1: def f(history=[]) creates ONE list at def time, shared by every call.
    Trap 2: `history = history or []` throws away a caller's EMPTY list ([] is falsy).

    Tools: default None, then `if history is None:`
    """
    raise NotImplementedError


DEFAULTS = {"timeout": 30, "retries": 3, "prompt": "> "}


def resolve_settings(user: dict) -> dict:
    """ex07. Return a dict with exactly the DEFAULTS keys. Use the user's value when
    the key is present and not None; otherwise use the default. Ignore other keys.

    resolve_settings({"timeout": 0, "prompt": ""})  -> {"timeout": 0, "retries": 3, "prompt": ""}
    resolve_settings({"retries": None, "x": 1})     -> {"timeout": 30, "retries": 3, "prompt": "> "}

    Trap: `user.get("timeout") or 30` turns a deliberate 0 (or "", [], False) into
    the default. Falsy is not the same as missing.

    Tools: dict.get(key) then `is None`; a dict comprehension over DEFAULTS.items()
    """
    raise NotImplementedError


def make_callbacks(labels: list[str]) -> dict[str, Callable[[], str]]:
    """ex08. Return {label: callback} where callback() returns "clicked <label>".

    cbs = make_callbacks(["save", "quit"])
    cbs["save"]() -> "clicked save"

    Trap: closures capture VARIABLES, not values (late binding).
    {lbl: lambda: f"clicked {lbl}" for lbl in labels} gives every callback the LAST
    label, because they all read `lbl` when called, after the loop has finished.

    Tools: bind the value now with a default arg (lambda lbl=lbl: ...),
           functools.partial, or a factory function
    """
    raise NotImplementedError


def make_rate_limiter(limit: int) -> Callable[[], bool]:
    """ex09. Return allow(): True for the first `limit` calls, False after that.
    Each limiter keeps its own count.

    allow = make_rate_limiter(2)
    allow(), allow(), allow() -> True, True, False

    Trap: `count += 1` inside the inner function is an ASSIGNMENT, so Python treats
    `count` as local -> UnboundLocalError. Using a module-level global instead would
    make every limiter share one count.

    Tools: nonlocal
    """
    raise NotImplementedError


def weather_command(args: list[str], provider) -> str:
    """ex10. Handle `weather <city words...>` using an injected provider module.

    provider has:   provider.get_temp(city) -> int     and    class provider.UnknownCity(Exception)
    (In real code that's `import provider`; here it's passed in so tests can fake it.)

    The city is all args joined with spaces.
    No args               -> "usage: weather <city>"
    found                 -> "<city>: <temp>F"
    provider.UnknownCity  -> "unknown city: <city>"
    any OTHER exception   -> let it propagate

    weather_command(["New", "York"], provider) -> "New York: 61F"

    Trap 1: `except UnknownCity:` is a NameError; the class lives on the module, so
            write `except provider.UnknownCity:`. Python only evaluates the except
            expression when an exception actually happens, so the bug hides until then.
    Trap 2: `except Exception:` (or a bare `except:`) would also swallow network errors
            and bugs.

    Tools: " ".join(args), try/except provider.UnknownCity
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def apply_override(config: dict, path: str, value) -> dict:
    """ex11. Return a NEW config with the dotted path set to value. Create missing
    intermediate dicts. The original config must be completely unchanged, at every
    level of nesting, and the result must share no nested dicts/lists with it.

    base = {"model": {"name": "phi3", "params": {"temp": 0.7}}, "tags": ["a"]}
    apply_override(base, "model.params.temp", 0.2)
      -> {"model": {"name": "phi3", "params": {"temp": 0.2}}, "tags": ["a"]}
    base["model"]["params"]["temp"] -> still 0.7

    Trap: dict(config), config.copy() and {**config} are SHALLOW: the new outer dict
    holds the same inner dicts, so writing into result["model"]["params"] edits base.

    Tools: copy.deepcopy, path.split("."), walk all but the last key with setdefault
    """
    raise NotImplementedError


def drop_inactive(sessions: list[dict], now: int) -> int:
    """ex12. Remove, IN PLACE, every session that is not active at `now`, and return
    how many were removed. Active means start <= now < end.

    sessions = [{"id": 1, "start": 0, "end": 5}, {"id": 2, "start": 0, "end": 3},
                {"id": 3, "start": 0, "end": 2}, {"id": 4, "start": 4, "end": 9}]
    drop_inactive(sessions, 4) -> 2     sessions now holds ids 1 and 4 (same list object)

    Trap: calling sessions.remove(s) inside `for s in sessions` shifts the remaining
    items left, so the loop SKIPS the element right after each removal (no error,
    just wrong). For dicts, deleting while iterating raises RuntimeError.

    Tools: build the keep-list, then slice-assign: sessions[:] = [...]
           chained comparison: a <= x < b
    """
    raise NotImplementedError


def format_offset(minutes: int) -> str:
    """ex13. Format a UTC offset in minutes as "+HH:MM" / "-HH:MM".

    format_offset(330)  -> "+05:30"
    format_offset(-90)  -> "-01:30"
    format_offset(-45)  -> "-00:45"
    format_offset(0)    -> "+00:00"

    Trap: // and % FLOOR toward negative infinity. -90 // 60 == -2 and -90 % 60 == 30,
    so divmod(-90, 60) == (-2, 30), not (-1, -30). (And int(-1.5) == -1 truncates the
    other way.) Handle the sign separately and divide the absolute value.

    Tools: abs, divmod, f"{n:02d}"
    """
    raise NotImplementedError


def order_tickets(tickets: list[dict]) -> list[str]:
    """ex14. Return ticket ids sorted by team Z->A, then title A->Z. Tickets with the
    same team AND title keep their original relative order.

    [{"id": "t1", "team": "api", "title": "b"}, {"id": "t2", "team": "web", "title": "z"},
     {"id": "t3", "team": "api", "title": "a"}]       -> ["t2", "t3", "t1"]

    Trap: you can't negate a string to flip just one key, and
    sorted(key=lambda t: (t["team"], t["title"]), reverse=True) reverses BOTH keys.

    Tools: Python's sort is STABLE, so sort by the secondary key first, then by the
           primary key (reverse=True keeps stability too). Or functools.cmp_to_key.
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
