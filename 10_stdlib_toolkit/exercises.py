"""10 - Stdlib Toolkit

Fill in each function, then run:   python 10_stdlib_toolkit/exercises.py
Run just one exercise:             python 10_stdlib_toolkit/exercises.py 4
Run exercise 4 onward:             python 10_stdlib_toolkit/exercises.py 4+

Exercises go from easy (01) to advanced (14). Delete the `raise NotImplementedError`
line when you start one.
"""

import bisect
import heapq
import json
import statistics
import time
from collections import Counter, deque
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from itertools import combinations, count, islice, product
from operator import itemgetter
from typing import NamedTuple


# ---------------------------------------------------------------- easy ----

def recent_errors(lines: Iterable[str], n: int) -> list[str]:
    """ex01. Return the last n log lines whose level (3rd whitespace-separated field) is
    "ERROR", oldest first. `lines` may be a huge generator: keep at most n lines in memory.

    recent_errors(["... ERROR [a] one", "... INFO [b] ok", "... ERROR [a] two",
                   "... ERROR [c] three"], 2)
      -> ["... ERROR [a] two", "... ERROR [c] three"]

    Tools: collections.deque(iterable, maxlen=n) drops from the left as it fills
    """
    raise NotImplementedError


def benchmark_stats(runs: list[dict]) -> dict:
    """ex02. Summarize benchmark runs like {"model": "phi3:mini", "latency_ms": 412.5}.
    A model can appear more than once. Return:

        min     : lowest latency_ms
        avg     : mean latency_ms, rounded to 1 decimal place
        p50     : median latency_ms
        fastest : model name of the single fastest run
        top3    : model names of the 3 fastest runs, fastest first (repeats allowed)

    Empty input -> raise ValueError (min() and statistics already do; just don't swallow it).

    Tools: statistics.mean / statistics.median, min(runs, key=...),
           heapq.nsmallest(k, runs, key=...), operator.itemgetter
    """
    raise NotImplementedError


class Benchmark(NamedTuple):
    """ex03 (part 1 of 2). Declare three typed fields, in this order:
        model (str), latency_ms (float), ok (bool, defaults to True)
    """


def parse_benchmark(line: str) -> Benchmark:
    """ex03 (part 2 of 2). Parse "model, latency_ms[, ok|fail]" into a Benchmark.
    Strip whitespace around each field. A missing third field means ok=True.
    Any status other than "ok"/"fail" -> ValueError.

    parse_benchmark("phi3:mini, 412.5, ok")   -> Benchmark(model="phi3:mini", latency_ms=412.5, ok=True)
    parse_benchmark("mixtral,951.25,fail")    -> Benchmark("mixtral", 951.25, False)
    parse_benchmark("llama3:8b, 380")         -> Benchmark("llama3:8b", 380.0, True)

    Tools: class X(NamedTuple): field: type = default ; X(...) like any constructor
    """
    raise NotImplementedError


BREAKPOINTS = [200, 500, 1000]
LABELS = ["fast", "ok", "slow", "timeout"]


def latency_bucket(ms: float) -> str:
    """ex04. Label a latency using BREAKPOINTS / LABELS above:
    under 200 -> "fast", 200 up to (not incl.) 500 -> "ok", 500 to <1000 -> "slow",
    1000 and up -> "timeout". No if/elif chain.

    latency_bucket(199.9) -> "fast"
    latency_bucket(200)   -> "ok"
    latency_bucket(1000)  -> "timeout"

    Tools: bisect.bisect_right(BREAKPOINTS, ms) gives an index into LABELS
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def trending_cities(yesterday: list[str], today: list[str], k: int) -> list[tuple[str, int]]:
    """ex05. Two lists of raw weather searches. Normalize each city (collapse whitespace,
    capitalize each word), then return the k cities whose search count GREW the most
    from yesterday to today, as (city, increase), biggest first. Cities that didn't grow
    are left out.

    trending_cities(["durham"], ["Durham", " DURHAM", "cary"], 5)
      -> [("Durham", 1), ("Cary", 1)]

    Tools: Counter(generator), Counter - Counter (drops counts <= 0), .most_common(k)
    """
    raise NotImplementedError


def fastest_overall(node_results: list[Iterable[dict]], k: int) -> list[tuple[str, str, float]]:
    """ex06. Each GPU node streams its results already sorted by latency, e.g.
    {"node": "gpu-1", "model": "phi3", "latency_ms": 377.5}. Return the k fastest results
    across all nodes as (node, model, latency_ms), fastest first.

    The streams can be very long: don't read more of any stream than you need.

    Tools: heapq.merge(*iterables, key=...) merges sorted inputs lazily, itertools.islice
    """
    raise NotImplementedError


def minutes_by_day(sessions: list[tuple[str, str]]) -> dict[str, int]:
    """ex07. Sessions are ("YYYY-MM-DD HH:MM", "YYYY-MM-DD HH:MM") start/end pairs. Return
    total whole minutes per day, keyed like "Mon 09/14" (the START day gets all the time,
    even if the session runs past midnight). End before start -> ValueError.

    minutes_by_day([("2026-09-14 10:03", "2026-09-14 11:30"),
                    ("2026-09-14 13:00", "2026-09-14 13:45")])
      -> {"Mon 09/14": 132}

    Tools: datetime.strptime(s, "%Y-%m-%d %H:%M"), end - start is a timedelta,
           delta.total_seconds() (NOT delta.seconds), dt.strftime("%a %m/%d"), dict.get
    """
    raise NotImplementedError


def schedule_matchups(models: list[str], rooms: list[str],
                      slots: list[str]) -> list[tuple[str, str, str, str]]:
    """ex08. Every pair of models plays one head-to-head eval. Assign the matchups, in
    combinations() order, to (slot, room) pairs in order: fill every room in the first slot,
    then every room in the second slot, and so on. Return (model_a, model_b, slot, room).
    Not enough (slot, room) pairs for all matchups -> ValueError.

    schedule_matchups(["a", "b", "c"], ["R1", "R2"], ["10:00", "11:00"])
      -> [("a", "b", "10:00", "R1"), ("a", "c", "10:00", "R2"), ("b", "c", "11:00", "R1")]

    Tools: itertools.combinations(models, 2), itertools.product(slots, rooms), zip
    """
    raise NotImplementedError


def count_ways(amount: int, coins: tuple[int, ...]) -> int:
    """ex09. Number of ways to make `amount` from unlimited coins of the given denominations
    (order doesn't matter: 1+2 and 2+1 are the same way). Write it RECURSIVELY and memoize
    it by decorating this function with @lru_cache(maxsize=None) (or functools.cache).

    count_ways(10, (1, 2, 5))  -> 10
    count_ways(3, (2,))        -> 0

    Hint: ways(amount, coins) = ways(amount - coins[0], coins)   # use the first coin
                               + ways(amount, coins[1:])         # never use it
    Tools: @lru_cache; arguments must be hashable, which is why coins is a tuple
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def shortest_path(grid: list[str], start: tuple[int, int], goal: tuple[int, int]) -> int:
    """ex10. Fewest up/down/left/right steps from start to goal on a grid of "." (open)
    and "#" (wall), given as (row, col). Unreachable -> -1. start == goal -> 0.

    shortest_path([".#.",
                   "...",
                   ".#."], (0, 0), (0, 2)) -> 4

    Tools: BFS with collections.deque: popleft(), append(); a `seen` set; mark cells seen
           when you ENQUEUE them, not when you pop them
    """
    raise NotImplementedError


class TTLCache:
    """ex11. Weather cache keyed by city with a time-to-live, and an injectable clock.

    Keys are normalized: whitespace collapsed and lowercased ("  New   York" -> "new york").
    Each entry stores (value, stored_at). An entry is fresh while now() - stored_at < ttl.

        set(city, value)          store it with the current time
        get(city)                 the value if fresh; else drop any stale entry, return None
        get_or_fetch(city, fetch) the fresh value, or call fetch(normalized_city), store the
                                  result, and return it

    t = [0.0]
    cache = TTLCache(60, now=lambda: t[0])
    cache.set("Durham", 21)
    t[0] = 59.9;  cache.get(" durham ") -> 21
    t[0] = 60.0;  cache.get("durham")   -> None

    Tools: a dict of key -> (value, stored_at), tuple unpacking, dict.pop(key, None)
    """

    def __init__(self, ttl: float, now: Callable[[], float] = time.monotonic):
        raise NotImplementedError

    def set(self, city: str, value) -> None:
        raise NotImplementedError

    def get(self, city: str):
        raise NotImplementedError

    def get_or_fetch(self, city: str, fetch: Callable[[str], object]):
        raise NotImplementedError


class TaskScheduler:
    """ex12. Priority queue of tasks. Lower priority number runs first; equal priorities run
    in the order they were added. Tasks can be any object, including dicts (which can't be
    compared with <).

        add(task, priority)   queue it
        pop()                 remove and return the next task; IndexError if empty
        len(scheduler)        how many are waiting

    s = TaskScheduler()
    s.add({"job": "deploy"}, 2); s.add({"job": "hotfix"}, 1); s.add({"job": "lint"}, 2)
    s.pop() -> {"job": "hotfix"};  s.pop() -> {"job": "deploy"};  s.pop() -> {"job": "lint"}

    Tools: heapq.heappush / heappop on a list of (priority, seq, task) tuples,
           itertools.count() for seq (the tie-breaker; it also stops Python comparing tasks)
    """

    def __init__(self):
        raise NotImplementedError

    def add(self, task, priority: int) -> None:
        raise NotImplementedError

    def pop(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class Status(Enum):
    """Given (used by ex13 and ex14). Don't edit."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


def apply_events(status: str, events: list[str]) -> Status:
    """ex13. Parse the starting status from its string VALUE (e.g. "pending"), apply each
    event, and return the final Status. Allowed transitions:

        PENDING  --start-->   RUNNING        PENDING --cancel--> CANCELLED
        RUNNING  --succeed--> SUCCEEDED      RUNNING --fail-->   FAILED
        RUNNING  --cancel-->  CANCELLED      FAILED  --retry-->  PENDING

    Anything else -> ValueError mentioning the status NAME and the event,
    e.g. "can't 'start' from SUCCEEDED". An unknown status string -> ValueError too.

    apply_events("pending", ["start", "fail", "retry", "start", "succeed"]) -> Status.SUCCEEDED

    Tools: Status("pending") looks up by value; a dict keyed by (Status, event) tuples;
           member.name / member.value
    """
    raise NotImplementedError


def encode_job(job: dict) -> str:
    """ex14 (part 1 of 2). Serialize a job dict to JSON with sorted keys. datetime values
    become ISO strings ("2026-09-14T10:03:00"), Status values become their .value.
    Any other unsupported type must still raise TypeError (don't str() everything).

    encode_job({"id": 7, "status": Status.RUNNING, "created_at": datetime(2026, 9, 14, 10, 3)})
      -> '{"created_at": "2026-09-14T10:03:00", "id": 7, "status": "running"}'

    Tools: json.dumps(obj, default=fn, sort_keys=True); fn(obj) is only called for objects
           json can't handle, and should raise TypeError for ones you don't either
    """
    raise NotImplementedError


def decode_job(text: str) -> dict:
    """ex14 (part 2 of 2). Reverse encode_job: json.loads, then turn every non-null value
    whose key ends in "_at" back into a datetime, and "status" back into a Status.
    decode_job(encode_job(job)) == job.

    Tools: json.loads, datetime.fromisoformat, Status(value), str.endswith
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
