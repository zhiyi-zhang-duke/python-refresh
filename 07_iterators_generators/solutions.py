"""07 - Iterators & Generators: reference solutions.   Check them:  python 07_iterators_generators/solutions.py"""

from collections import deque
from collections.abc import Callable, Iterable, Iterator
from itertools import accumulate, chain, count, groupby, islice, pairwise, zip_longest
from operator import itemgetter


# ---------------------------------------------------------------- easy ----

def first_error(lines: Iterable[str]) -> str | None:
    # split()[2:3] is [] on short lines instead of raising IndexError.
    return next((line for line in lines if line.split()[2:3] == ["ERROR"]), None)


def token_report(records: Iterable[dict]) -> dict:
    # A generator is empty after one pass; list() it so we can scan three times.
    records = list(records)
    ok = [r for r in records if r["ok"]]
    return {
        "total": sum(r["tokens"] for r in ok),
        "max": max((r["tokens"] for r in ok), default=0),
        "failed": sum(1 for r in records if not r["ok"]),
    }


def backoff_delays(base: float, factor: float, cap: float, tries: int) -> Iterator[float]:
    for i in range(tries):
        yield min(cap, base * factor ** i)


def read_table(lines: Iterable[str]) -> list[dict[str, str]]:
    it = iter(lines)
    header = next(it, None)
    if header is None:
        return []
    keys = [k.strip() for k in header.split(",")]
    return [
        dict(zip(keys, (cell.strip() for cell in line.split(","))))
        for line in it          # picks up right after the header
        if line.strip()
    ]


# -------------------------------------------------------------- medium ----

def next_free_ids(prefix: str, taken: set[str], n: int) -> list[str]:
    candidates = (f"{prefix}-{i:03d}" for i in count(1))
    return list(islice((c for c in candidates if c not in taken), n))


def first_over_budget(costs: Iterable[float], budget: float) -> int | None:
    running = enumerate(accumulate(costs), start=1)
    return next((i for i, total in running if total > budget), None)


def bookings_by_room(bookings: list[dict]) -> list[tuple[str, list[str]]]:
    ordered = sorted(bookings, key=itemgetter("room", "start"))   # sorted() copies; .sort() would mutate
    return [
        (room, [b["who"] for b in group])   # consume `group` now; it dies when groupby advances
        for room, group in groupby(ordered, key=itemgetter("room"))
    ]


def split_sessions(timestamps: list[int], max_gap: int) -> list[list[int]]:
    if not timestamps:
        return []
    sessions = [[timestamps[0]]]
    for prev, cur in pairwise(timestamps):
        if cur - prev > max_gap:
            sessions.append([cur])
        else:
            sessions[-1].append(cur)
    return sessions


_MISSING = object()   # unique sentinel: can't collide with None/0/"" jobs


def interleave(*queues: list) -> list:
    rounds = zip_longest(*queues, fillvalue=_MISSING)
    return [job for job in chain.from_iterable(rounds) if job is not _MISSING]


# ------------------------------------------------------------ advanced ----

def batched(iterable: Iterable, n: int) -> Iterator[tuple]:
    # Note: in a generator this check only runs on the first next(), not at call time.
    if n < 1:
        raise ValueError("n must be at least 1")
    it = iter(iterable)   # must be ONE shared iterator, or islice restarts a list each time
    while batch := tuple(islice(it, n)):
        yield batch


def walk(tree: dict, prefix: str = "") -> Iterator[tuple[str, int]]:
    for name, value in tree.items():
        path = f"{prefix}/{name}" if prefix else name
        if isinstance(value, dict):
            yield from walk(value, path)
        else:
            yield path, value


class PageIterator:
    def __init__(self, fetch: Callable[[str | None], tuple[list, str | None]]):
        self._fetch = fetch
        self._buffer: deque = deque()
        self._token: str | None = None
        self._started = False   # distinguishes "first page not fetched" from "token is None = done"

    def __iter__(self):
        return self

    def __next__(self):
        while not self._buffer:
            if self._started and self._token is None:
                raise StopIteration
            items, self._token = self._fetch(self._token)
            self._started = True
            self._buffer = deque(items)
        return self._buffer.popleft()   # O(1); list.pop(0) is O(n)


def _parse(lines: Iterable[str]) -> Iterator[tuple[str, str, str]]:
    for line in lines:
        parts = line.split(maxsplit=4)
        if len(parts) == 5:
            _date, _time, level, source, message = parts
            yield level, source.strip("[]"), message


def first_errors(lines: Iterable[str], n: int) -> list[tuple[str, str]]:
    errors = ((src, msg) for level, src, msg in _parse(lines) if level == "ERROR")
    return list(islice(errors, n))   # islice(_, 0) never pulls from upstream


def running_average() -> Iterator[float | None]:
    total = count_ = 0
    average = None
    while True:
        value = yield average
        total += value
        count_ += 1
        average = total / count_


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
