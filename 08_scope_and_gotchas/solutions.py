"""08 - Scope & Gotchas: reference solutions.   Check them:  python 08_scope_and_gotchas/solutions.py"""

import copy
from typing import Callable


# ---------------------------------------------------------------- easy ----

LOADED_MODEL: str | None = None


def load_model(name: str) -> str | None:
    global LOADED_MODEL  # we ASSIGN to it below, so we must say it's the module's
    previous = LOADED_MODEL
    LOADED_MODEL = name
    return previous


def unload_model() -> str | None:
    global LOADED_MODEL
    previous, LOADED_MODEL = LOADED_MODEL, None
    return previous


def model_status(current: str | None, requested: str) -> str:
    if current is None:
        return f"load {requested}"
    if current == requested:  # value comparison; never `is` for strings
        return "already loaded"
    return f"switch {current} -> {requested}"


def is_yes(answer: str) -> bool:
    return answer.strip().lower() in {"y", "yes"}


def make_grid(rows: int, cols: int, fill=0) -> list[list]:
    # Inner [fill] * cols is fine (the elements are immutable); the OUTER list must
    # build a fresh row each time.
    return [[fill] * cols for _ in range(rows)]


# -------------------------------------------------------------- medium ----

def parse_command(line: str) -> tuple[str, list[str]]:
    parts = line.split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.lower(), args


def log_event(event: str, history: list[str] | None = None) -> list[str]:
    if history is None:
        history = []
    history.append(event)
    return history


DEFAULTS = {"timeout": 30, "retries": 3, "prompt": "> "}


def resolve_settings(user: dict) -> dict:
    return {
        key: default if user.get(key) is None else user[key]
        for key, default in DEFAULTS.items()
    }


def make_callbacks(labels: list[str]) -> dict[str, Callable[[], str]]:
    # The default argument is evaluated NOW, once per iteration.
    return {label: (lambda label=label: f"clicked {label}") for label in labels}


def make_rate_limiter(limit: int) -> Callable[[], bool]:
    used = 0

    def allow() -> bool:
        nonlocal used
        if used >= limit:
            return False
        used += 1
        return True

    return allow


def weather_command(args: list[str], provider) -> str:
    city = " ".join(args)
    if not city:
        return "usage: weather <city>"
    try:
        temp = provider.get_temp(city)
    except provider.UnknownCity:  # the class is an attribute of the module
        return f"unknown city: {city}"
    return f"{city}: {temp}F"


# ------------------------------------------------------------ advanced ----

def apply_override(config: dict, path: str, value) -> dict:
    result = copy.deepcopy(config)
    *parents, last = path.split(".")
    node = result
    for key in parents:
        node = node.setdefault(key, {})
    node[last] = value
    return result


def drop_inactive(sessions: list[dict], now: int) -> int:
    keep = [s for s in sessions if s["start"] <= now < s["end"]]
    removed = len(sessions) - len(keep)
    sessions[:] = keep  # slice assignment mutates the caller's list; `sessions = keep` wouldn't
    return removed


def format_offset(minutes: int) -> str:
    sign = "-" if minutes < 0 else "+"
    hours, mins = divmod(abs(minutes), 60)
    return f"{sign}{hours:02d}:{mins:02d}"


def order_tickets(tickets: list[dict]) -> list[str]:
    # Stable sort: secondary key first, then primary. Ties on the primary key keep
    # the order from the first pass.
    by_title = sorted(tickets, key=lambda t: t["title"])
    by_team = sorted(by_title, key=lambda t: t["team"], reverse=True)
    return [t["id"] for t in by_team]


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
