"""10 - Stdlib Toolkit: reference solutions.   Check them:  python 10_stdlib_toolkit/solutions.py"""

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
    errors = (line for line in lines if line.split()[2:3] == ["ERROR"])
    return list(deque(errors, maxlen=n))


def benchmark_stats(runs: list[dict]) -> dict:
    latencies = [r["latency_ms"] for r in runs]
    by_latency = itemgetter("latency_ms")
    return {
        "min": min(latencies),
        "avg": round(statistics.mean(latencies), 1),
        "p50": statistics.median(latencies),
        "fastest": min(runs, key=by_latency)["model"],
        "top3": [r["model"] for r in heapq.nsmallest(3, runs, key=by_latency)],
    }


class Benchmark(NamedTuple):
    model: str
    latency_ms: float
    ok: bool = True     # fields with defaults must come after fields without


def parse_benchmark(line: str) -> Benchmark:
    model, latency, *rest = [part.strip() for part in line.split(",")]
    status = rest[0] if rest else "ok"
    if status not in ("ok", "fail"):
        raise ValueError(f"unknown status: {status!r}")
    return Benchmark(model, float(latency), status == "ok")


BREAKPOINTS = [200, 500, 1000]
LABELS = ["fast", "ok", "slow", "timeout"]


def latency_bucket(ms: float) -> str:
    # bisect_right: a value equal to a breakpoint lands in the bucket ABOVE it.
    return LABELS[bisect.bisect_right(BREAKPOINTS, ms)]


# -------------------------------------------------------------- medium ----

def _normalize_city(raw: str) -> str:
    return " ".join(word.capitalize() for word in raw.split())


def trending_cities(yesterday: list[str], today: list[str], k: int) -> list[tuple[str, int]]:
    before = Counter(_normalize_city(c) for c in yesterday)
    after = Counter(_normalize_city(c) for c in today)
    return (after - before).most_common(k)   # `-` keeps only positive counts


def fastest_overall(node_results: list[Iterable[dict]], k: int) -> list[tuple[str, str, float]]:
    merged = heapq.merge(*node_results, key=itemgetter("latency_ms"))
    return [(r["node"], r["model"], r["latency_ms"]) for r in islice(merged, k)]


FMT = "%Y-%m-%d %H:%M"


def minutes_by_day(sessions: list[tuple[str, str]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for raw_start, raw_end in sessions:
        start, end = datetime.strptime(raw_start, FMT), datetime.strptime(raw_end, FMT)
        if end < start:
            raise ValueError(f"session ends before it starts: {raw_start} -> {raw_end}")
        # timedelta // timedelta -> int. (delta.seconds would ignore whole days.)
        minutes = (end - start) // timedelta(minutes=1)
        day = start.strftime("%a %m/%d")
        totals[day] = totals.get(day, 0) + minutes
    return totals


def schedule_matchups(models: list[str], rooms: list[str],
                      slots: list[str]) -> list[tuple[str, str, str, str]]:
    matchups = list(combinations(models, 2))
    places = list(product(slots, rooms))      # slot-major: all rooms at 10:00 first
    if len(places) < len(matchups):
        raise ValueError(f"{len(matchups)} matchups but only {len(places)} slots")
    return [(a, b, slot, room) for (a, b), (slot, room) in zip(matchups, places)]


@lru_cache(maxsize=None)
def count_ways(amount: int, coins: tuple[int, ...]) -> int:
    if amount == 0:
        return 1
    if amount < 0 or not coins:
        return 0
    return count_ways(amount - coins[0], coins) + count_ways(amount, coins[1:])


# ------------------------------------------------------------ advanced ----

def shortest_path(grid: list[str], start: tuple[int, int], goal: tuple[int, int]) -> int:
    rows, cols = len(grid), len(grid[0])
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        (r, c), dist = queue.popleft()
        if (r, c) == goal:
            return dist
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != "#" and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append(((nr, nc), dist + 1))
    return -1


class TTLCache:
    def __init__(self, ttl: float, now: Callable[[], float] = time.monotonic):
        self.ttl = ttl
        self.now = now
        self._data: dict[str, tuple[object, float]] = {}

    @staticmethod
    def _key(city: str) -> str:
        return " ".join(city.split()).lower()

    def set(self, city: str, value) -> None:
        self._data[self._key(city)] = (value, self.now())

    def get(self, city: str):
        key = self._key(city)
        entry = self._data.get(key)
        if entry is None:
            return None
        value, stored_at = entry
        if self.now() - stored_at >= self.ttl:
            del self._data[key]
            return None
        return value

    def get_or_fetch(self, city: str, fetch: Callable[[str], object]):
        key = self._key(city)
        value = self.get(key)
        if value is None:
            value = fetch(key)
            self.set(key, value)
        return value


class TaskScheduler:
    def __init__(self):
        self._heap: list[tuple[int, int, object]] = []
        self._seq = count()

    def add(self, task, priority: int) -> None:
        # seq is unique, so tuple comparison never reaches `task` (dicts don't support <).
        heapq.heappush(self._heap, (priority, next(self._seq), task))

    def pop(self):
        if not self._heap:
            raise IndexError("pop from an empty TaskScheduler")
        return heapq.heappop(self._heap)[-1]

    def __len__(self) -> int:
        return len(self._heap)


class Status(Enum):
    """Given (used by ex13 and ex14). Don't edit."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TRANSITIONS = {
    (Status.PENDING, "start"): Status.RUNNING,
    (Status.PENDING, "cancel"): Status.CANCELLED,
    (Status.RUNNING, "succeed"): Status.SUCCEEDED,
    (Status.RUNNING, "fail"): Status.FAILED,
    (Status.RUNNING, "cancel"): Status.CANCELLED,
    (Status.FAILED, "retry"): Status.PENDING,
}


def apply_events(status: str, events: list[str]) -> Status:
    current = Status(status)   # lookup by value; raises ValueError for unknown strings
    for event in events:
        try:
            current = TRANSITIONS[(current, event)]
        except KeyError:
            raise ValueError(f"can't {event!r} from {current.name}") from None
    return current


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"{type(obj).__name__} is not JSON serializable")


def encode_job(job: dict) -> str:
    return json.dumps(job, default=_json_default, sort_keys=True)


def decode_job(text: str) -> dict:
    job = json.loads(text)
    for key, value in job.items():   # replacing values (not adding keys) while iterating is OK
        if key.endswith("_at") and value is not None:
            job[key] = datetime.fromisoformat(value)
    if "status" in job:
        job["status"] = Status(job["status"])
    return job


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
