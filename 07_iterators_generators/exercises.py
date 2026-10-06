"""07 - Iterators & Generators

Fill in each function, then run:   python 07_iterators_generators/exercises.py
Run just one exercise:             python 07_iterators_generators/exercises.py 4
Run exercise 4 onward:             python 07_iterators_generators/exercises.py 4+

Exercises go from easy (01) to advanced (14). Delete the `raise NotImplementedError`
line when you start one.

Heads-up: a stub that only raises is a plain function. The moment you write `yield`
anywhere in its body it becomes a generator function, and calling it no longer runs
any code until the first next().
"""

from collections.abc import Callable, Iterable, Iterator
from itertools import accumulate, chain, count, groupby, islice, pairwise, zip_longest
from operator import itemgetter


# ---------------------------------------------------------------- easy ----

def first_error(lines: Iterable[str]) -> str | None:
    """ex01. Return the first log line whose level (3rd whitespace-separated field) is
    "ERROR", or None if there isn't one. Lines with fewer than 3 fields are skipped.

    Stop reading as soon as you find it: `lines` may be an endless stream.

    first_error(["2026-09-14 10:03:20 INFO [cli] start",
                 "",
                 "2026-09-14 10:03:22 ERROR [provider] Model not loaded"])
      -> "2026-09-14 10:03:22 ERROR [provider] Model not loaded"
    first_error([]) -> None

    Tools: next(generator_expression, default)
    """
    raise NotImplementedError


def token_report(records: Iterable[dict]) -> dict:
    """ex02. Summarize model-call records like {"model": "phi3", "tokens": 120, "ok": True}.

        total  : sum of tokens over ok records
        max    : largest tokens value among ok records (0 if there are none)
        failed : how many records are not ok

    `records` may be a generator, which can only be iterated ONCE.

    token_report([{"model": "a", "tokens": 10, "ok": True},
                  {"model": "b", "tokens": 99, "ok": False}])
      -> {"total": 10, "max": 10, "failed": 1}

    Tools: list(...) to materialize first, sum(x for ...), max(..., default=0)
    """
    raise NotImplementedError


def backoff_delays(base: float, factor: float, cap: float, tries: int) -> Iterator[float]:
    """ex03. GENERATOR: yield `tries` retry delays: base, base*factor, base*factor**2, ...
    each capped at `cap`.

    list(backoff_delays(1, 2, 10, 6))    -> [1, 2, 4, 8, 10, 10]
    list(backoff_delays(0.5, 3, 5, 3))   -> [0.5, 1.5, 4.5]

    Tools: def with `yield` inside a for loop, min()
    """
    raise NotImplementedError


def read_table(lines: Iterable[str]) -> list[dict[str, str]]:
    """ex04. Parse comma-separated lines into a list of dicts. The FIRST line is the header.
    Strip whitespace (and trailing newlines) around every cell. Skip blank data lines.
    Empty input -> [].

    `lines` may be a file object or generator, so you can't index lines[0].

    read_table(["model, latency_ms\\n", "phi3, 412\\n", "\\n", "llama3, 380\\n"])
      -> [{"model": "phi3", "latency_ms": "412"}, {"model": "llama3", "latency_ms": "380"}]

    Tools: it = iter(lines); header = next(it, None); a `for` over `it` resumes after the header
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def next_free_ids(prefix: str, taken: set[str], n: int) -> list[str]:
    """ex05. Return the first n ticket ids of the form "<prefix>-NNN" (counting from 001)
    that are not already in `taken`.

    next_free_ids("T", {"T-001", "T-003"}, 3) -> ["T-002", "T-004", "T-005"]

    Tools: itertools.count(1) (infinite), a generator expression to filter,
           itertools.islice(it, n) to take n, f"{i:03d}"
    """
    raise NotImplementedError


def first_over_budget(costs: Iterable[float], budget: float) -> int | None:
    """ex06. API calls cost `costs[i]` dollars each. Return the 1-based call number at which
    the running total first goes STRICTLY above `budget`, or None if it never does.
    `costs` may be endless.

    first_over_budget([0.5, 1.25, 2.0, 0.75], 3.0) -> 3     (running: 0.5, 1.75, 3.75)
    first_over_budget([1.0, 1.0], 5.0)             -> None

    Tools: itertools.accumulate, enumerate(..., start=1), next(..., None)
    """
    raise NotImplementedError


def bookings_by_room(bookings: list[dict]) -> list[tuple[str, list[str]]]:
    """ex07. Bookings look like {"room": "B", "start": "09:30", "who": "Ana"} in no
    particular order. Return [(room, [who, ...]), ...] sorted by room name, with each room's
    people in start-time order. Don't mutate the input list.

    bookings_by_room([{"room": "B", "start": "10:00", "who": "Bo"},
                      {"room": "A", "start": "09:00", "who": "Al"},
                      {"room": "B", "start": "09:00", "who": "Cy"}])
      -> [("A", ["Al"]), ("B", ["Cy", "Bo"])]

    Tools: sorted(key=lambda b: (b["room"], b["start"])), itertools.groupby(key=...).
           groupby only groups ADJACENT equal keys, so sort first.
    """
    raise NotImplementedError


def split_sessions(timestamps: list[int], max_gap: int) -> list[list[int]]:
    """ex08. `timestamps` are sorted epoch seconds of user clicks. Start a new session
    whenever the gap to the previous click is MORE than `max_gap` seconds.

    split_sessions([0, 30, 50, 400, 420, 2000], 300) -> [[0, 30, 50], [400, 420], [2000]]
    split_sessions([], 300) -> []

    Tools: itertools.pairwise(ts) -> (ts[0], ts[1]), (ts[1], ts[2]), ...
    """
    raise NotImplementedError


def interleave(*queues: list) -> list:
    """ex09. Fair round-robin across tenant job queues of different lengths: take one job
    from each queue in turn, skipping queues that have run out. Jobs can be ANY value,
    including None, 0, or "".

    interleave(["a1", "a2", "a3"], ["b1"], ["c1", "c2"])
      -> ["a1", "b1", "c1", "a2", "c2", "a3"]

    Tools: itertools.zip_longest(*queues, fillvalue=SENTINEL) with SENTINEL = object(),
           itertools.chain.from_iterable, `is not` (not truthiness) to filter
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def batched(iterable: Iterable, n: int) -> Iterator[tuple]:
    """ex10. GENERATOR: yield tuples of n items; the last one may be shorter. Must be lazy:
    it should work on an endless iterable and only pull items as batches are requested.
    n < 1 -> ValueError. (itertools.batched exists in 3.12; we're on 3.10, so hand-roll it.)

    list(batched("ABCDEFG", 3)) -> [("A", "B", "C"), ("D", "E", "F"), ("G",)]

    Tools: it = iter(iterable); tuple(islice(it, n)); `while batch := ...:`
    """
    raise NotImplementedError


def walk(tree: dict, prefix: str = "") -> Iterator[tuple[str, int]]:
    """ex11. GENERATOR: a directory tree is a dict where a value is either a nested dict
    (folder) or an int (file size in bytes). Yield (path, size) for every file, depth-first
    in dict order, joining names with "/".

    tree = {"src": {"main.py": 120, "util": {"io.py": 40}}, "README.md": 10}
    list(walk(tree)) -> [("src/main.py", 120), ("src/util/io.py", 40), ("README.md", 10)]

    Tools: recursion + `yield from walk(subtree, path)`, isinstance(value, dict)
    """
    raise NotImplementedError


class PageIterator:
    """ex12. Iterate item-by-item over a paginated API, fetching pages LAZILY.

    `fetch(token)` returns (items, next_token). Call fetch(None) for the first page; keep
    going while next_token is not None. A page may be empty but still have a next_token.
    Only fetch a page when you've run out of items from the previous one, and never call
    fetch again after the last page.

    it = PageIterator(fetch)        # no fetch yet
    next(it)                        # fetches page 1, returns its first item
    list(it)                        # the rest of the items, across all pages

    Tools: __iter__ returns self; __next__ returns one item or raises StopIteration;
           keep a buffer of the current page plus the next token (and a "done" flag)
    """

    def __init__(self, fetch: Callable[[str | None], tuple[list, str | None]]):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __next__(self):
        raise NotImplementedError


def first_errors(lines: Iterable[str], n: int) -> list[tuple[str, str]]:
    """ex13. Lazy pipeline over log lines "<date> <time> <LEVEL> [<source>] <message>":
    parse -> keep ERROR -> take the first n. Return [(source, message), ...].
    Skip malformed lines (fewer than 5 whitespace-separated fields).

    Read no more lines than necessary: stop right after the nth error, and n=0 reads nothing.
    `lines` may be endless.

    first_errors(["2026-09-14 10:03:22 ERROR [provider] Model not loaded: phi3",
                  "2026-09-14 10:03:23 INFO [cli] retrying"], 5)
      -> [("provider", "Model not loaded: phi3")]

    Tools: line.split(maxsplit=4), a helper generator for the parse step (it can skip
           bad lines; a genexp can't easily), chained generator expressions, islice
    """
    raise NotImplementedError


def running_average() -> Iterator[float | None]:
    """ex14. COROUTINE: a latency monitor you feed with .send(). Prime it with next(), which
    returns None. After that, each .send(x) returns the average of everything sent so far.

    avg = running_average()
    next(avg)       -> None
    avg.send(10)    -> 10.0
    avg.send(20)    -> 15.0

    Tools: `value = yield current` both hands `current` out and receives the sent value;
           an infinite `while True` loop
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
