"""03 - Dicts and sets

Fill in each function, then run:   python 03_dicts_sets/exercises.py
Run just one exercise:             python 03_dicts_sets/exercises.py 4
Run exercise 4 onward:             python 03_dicts_sets/exercises.py 4+

Exercises go from easy (01) to advanced (14). Delete the `raise NotImplementedError`
line when you start one. ex11 uses the fake `provider.py` module in this folder.
"""

import copy
import shlex
from collections import Counter, OrderedDict, defaultdict, deque

import provider


LOG_LINES = [
    "2026-09-14 10:03:22 INFO [cli] started",
    "2026-09-14 10:03:25 ERROR [provider] Model not loaded: phi3",
    "2026-09-14 10:03:26 WARNING [cache] miss rate high",
    "2026-09-14 10:03:30 ERROR [cli] bad command: lod",
    "",
    "2026-09-14 10:04:01 ERROR [provider] timeout after 30s",
    "2026-09-14 10:04:02 INFO [provider] retrying",
    "2026-09-14 10:04:09 ERROR [db] connection refused",
    "2026-09-14 10:04:10 ERROR [cli] bad command: wether",
    "2026-09-14 10:04:15 ERROR [provider] timeout after 30s",
]

MODELS = [
    {"name": "phi3:mini", "provider": "ollama", "size_gb": 2.2},
    {"name": "gpt-4o", "provider": "openai", "size_gb": 0.0},
    {"name": "llama3:70b", "provider": "ollama", "size_gb": 39.0},
    {"name": "mystery-7b", "size_gb": 4.1},  # no "provider" key
]

PROFILES = {
    "default": {"unit": "F", "uses": 0},
    "metric": {"unit": "C", "uses": 0},
}
ACTIVE_PROFILE = "default"


# ---------------------------------------------------------------- easy ----

def get_price(prices: dict[str, float], item: str) -> float:
    """ex01. Look up an item's price. Keys in `prices` are lowercase; the query may
    have stray case and whitespace. Unknown items cost 0.0 (never raise KeyError).

    get_price({"apple": 0.5}, "  Apple\\n") -> 0.5
    get_price({"apple": 0.5}, "kiwi")      -> 0.0

    Tools: dict.get(key, default), str.strip, str.lower
    """
    raise NotImplementedError


def count_levels(lines: list[str]) -> dict[str, int]:
    """ex02. Count log lines per level (the 3rd whitespace-separated field).
    Skip blank lines. Do it by hand here, no Counter (that's ex05).

    count_levels(LOG_LINES) -> {"INFO": 2, "ERROR": 6, "WARNING": 1}

    Tools: counts[k] = counts.get(k, 0) + 1, str.split()
    """
    raise NotImplementedError


def merge_config(defaults: dict, overrides: dict) -> dict:
    """ex03. Return a NEW dict: defaults updated by overrides, except overrides whose
    value is None mean "not set" and are ignored. Neither input may be modified.

    merge_config({"unit": "F", "days": 3}, {"days": 5, "unit": None})
        -> {"unit": "F", "days": 5}

    Tools: a | b (3.9+) or {**a, **b} (right side wins), a dict comprehension with
           `if v is not None`
    """
    raise NotImplementedError


def switch_profile(name: str) -> dict:
    """ex04. Make `name` (stripped, lowercased) the ACTIVE_PROFILE (module-level),
    bump that profile's "uses" counter in PROFILES, and return its dict.
    Unknown profile -> raise KeyError and leave ACTIVE_PROFILE unchanged.

    switch_profile(" Metric ") -> {"unit": "C", "uses": 1}, and ACTIVE_PROFILE == "metric"

    Tools: `global ACTIVE_PROFILE` (ASSIGNING to a module-level name inside a function
           needs it; MUTATING PROFILES[...]["uses"] does not; ask yourself why)
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def top_sources(lines: list[str], n: int) -> list[tuple[str, int]]:
    """ex05. The n sources (the "[...]" field, without brackets) with the most ERROR
    lines, as (source, count) pairs, highest first. Ties keep first-seen order.

    top_sources(LOG_LINES, 2) -> [("provider", 3), ("cli", 2)]

    Tools: collections.Counter, Counter.most_common(n), str.strip("[]")
    """
    raise NotImplementedError


def group_by_provider(models: list[dict]) -> dict[str, list[str]]:
    """ex06. Map provider -> model names (input order). A record with no "provider"
    key goes under "unknown". Return a plain dict.

    group_by_provider(MODELS) -> {"ollama": ["phi3:mini", "llama3:70b"],
                                  "openai": ["gpt-4o"], "unknown": ["mystery-7b"]}

    Tools: collections.defaultdict(list) or dict.setdefault(k, []).append(v), dict.get
    """
    raise NotImplementedError


def invert(aliases: dict[str, str]) -> dict[str, list[str]]:
    """ex07. Invert alias -> model into model -> sorted list of its aliases.
    Several aliases can point at the same model; none may be lost.

    invert({"fast": "phi3", "small": "phi3", "big": "llama3"})
        -> {"phi3": ["fast", "small"], "llama3": ["big"]}

    Tools: {v: k for k, v in d.items()} is the one-liner, but it silently keeps only
           the LAST key per value. setdefault / defaultdict(list), then sorted().
    """
    raise NotImplementedError


def diff_hosts(local: list[str], remote: list[str]) -> dict[str, list[str]]:
    """ex08. Compare the models installed on two hosts (lists may contain duplicates).
    Return a dict of SORTED lists:

        "both"         on both hosts
        "only_local"   on local but not remote
        "only_remote"  on remote but not local
        "out_of_sync"  on exactly one of the two
        "all"          on either

    Tools: set(), &  -  ^  |  (or .intersection / .difference / .symmetric_difference / .union),
           sorted()
    """
    raise NotImplementedError


def rank_by_value(scores: dict[str, int]) -> list[tuple[str, int]]:
    """ex09. Sort a dict's items by value, highest first; ties broken by key A to Z.

    rank_by_value({"cy": 5, "al": 9, "bo": 5}) -> [("al", 9), ("bo", 5), ("cy", 5)]

    Tools: sorted(d.items(), key=lambda kv: ...), negating the number for descending
    """
    raise NotImplementedError


def get_path(data, path: str, default=None):
    """ex10. Safe nested lookup by dotted path. Dict segments are keys; an all-digit
    segment indexes into a list. If ANY step is missing, out of range, or hits
    something that isn't a dict/list, return `default`. A value that exists is
    returned even if it's None, 0, or False.

    cfg = {"providers": {"ollama": {"port": 11434, "models": [{"name": "phi3"}]}}}
    get_path(cfg, "providers.ollama.port")          -> 11434
    get_path(cfg, "providers.ollama.models.0.name") -> "phi3"
    get_path(cfg, "providers.openai.port", 80)      -> 80

    Tools: str.split("."), isinstance(x, dict), str.isdigit, a loop that walks `cur`
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def cmd_weather(args: list[str]) -> str:
    """ex11 (part 1). Handler for the `weather` command. `args` are the words after
    the command; join them so multi-word cities work. No args -> raise ValueError.
    Let provider.UnknownCity propagate; run_repl deals with it.

    cmd_weather(["New", "York"]) -> "New York: 65F"
    cmd_weather(["Atlantis"])    -> raises provider.UnknownCity

    Tools: " ".join(args), provider.get_temp(city)
    """
    raise NotImplementedError


def run_repl(read_line, commands: dict) -> list[str]:
    """ex11 (part 2). Drive a REPL and return every line of output, in order.

    `read_line` is a zero-arg callable (in real code: lambda: input("> ")).
    `commands` maps name -> (handler, usage), e.g.
        {"weather": (cmd_weather, "weather <city>")}
    A tuple (or list), so entry[0] is the handler. NOT {cmd_weather, "..."}: that's a SET.

    Loop:
      - call read_line(); stop on EOFError or KeyboardInterrupt (Ctrl-D / Ctrl-C)
      - strip the line; skip blank lines
      - shlex.split it; unbalanced quotes -> output "error: unbalanced quotes"
      - first token (lowercased) is the command, the rest are args
      - "quit" or "exit" -> stop
      - unknown command               -> output "unknown command: <name>"
      - otherwise output handler(args), but:
          handler raises provider.UnknownCity -> output "unknown city: <str(e)>"
          handler raises ValueError           -> output "usage: <usage>"
      - any other exception should propagate (don't catch Exception)

    Tools: try/except (EOFError, KeyboardInterrupt), dict.get, entry[0](args) or
           `handler, usage = entry`, except provider.UnknownCity as e
    """
    raise NotImplementedError


def deep_merge(base: dict, override: dict) -> dict:
    """ex12. Recursively merge override into base and return a NEW dict.
    When both sides have a dict at the same key, merge those recursively; otherwise
    the override value wins (lists are replaced, not concatenated). Neither input may
    be modified, and the result must not share any nested dict/list with the inputs.

    deep_merge({"db": {"host": "a", "port": 1}, "tags": [1]},
               {"db": {"port": 2}, "tags": [2]})
        -> {"db": {"host": "a", "port": 2}, "tags": [2]}

    Tools: isinstance(x, dict), recursion, copy.deepcopy
    """
    raise NotImplementedError


class LRUCache:
    """ex13. Fixed-capacity least-recently-used cache.

    LRUCache(capacity)   capacity < 1 -> raise ValueError
    get(key, default=None)   value or default; a hit makes key the MOST recently used
    put(key, value)      insert or update (either makes it most recently used); if over
                         capacity, evict the LEAST recently used key
    len(cache)           number of keys
    keys()               list of keys, least recently used first

    c = LRUCache(2); c.put("a", 1); c.put("b", 2); c.get("a"); c.put("c", 3)
    c.keys() -> ["a", "c"]          ("b" was least recently used)

    Tools: collections.OrderedDict, move_to_end(key), popitem(last=False)
    """

    def __init__(self, capacity: int):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def keys(self) -> list:
        raise NotImplementedError


def shortest_route(flights: list[tuple[str, str]], start: str, goal: str) -> list[str] | None:
    """ex14. Flights are one-way (origin, destination) pairs. Return the route with the
    fewest legs as a list of airports from start to goal, or None if unreachable.
    start == goal -> [start].

    flights = [("RDU", "ATL"), ("ATL", "LAX"), ("RDU", "CLT"), ("CLT", "LAX")]
    shortest_route(flights, "RDU", "ATL") -> ["RDU", "ATL"]
    shortest_route(flights, "LAX", "RDU") -> None   (one-way)

    Tools: defaultdict(set) adjacency (graph[a].add(b)), BFS with collections.deque,
           a `came_from` dict (doubles as the visited set), walk it back and reverse
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
