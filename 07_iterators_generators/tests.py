import inspect
import itertools

from harness import expect, expect_raises


def _tracking(items, pulled):
    """Yield from items, recording every item handed out (to prove laziness)."""
    for x in items:
        pulled.append(x)
        yield x


INFO = "2026-09-14 10:03:20 INFO [cli] start"
WARN = "2026-09-14 10:03:21 WARNING [cache] stale entry for durham"
ERR1 = "2026-09-14 10:03:22 ERROR [provider] Model not loaded: phi3"
ERR2 = "2026-09-14 10:03:25 ERROR [cli] Unknown command: lst"


def test_ex01(m):
    """first_error: next(genexp, None) on a stream"""
    expect(m.first_error([INFO, "", "short line", ERR1, ERR2]), ERR1)
    expect(m.first_error([INFO, WARN]), None)
    expect(m.first_error([]), None)
    expect(m.first_error(["ERROR at start but wrong field"]), None,
           "the level is the 3rd field, not just anywhere in the line")
    pulled = []
    m.first_error(_tracking([INFO, ERR1, ERR2, INFO], pulled))
    expect(len(pulled), 2, "stop reading at the first ERROR")
    expect(m.first_error(itertools.cycle([INFO, WARN, ERR2])), ERR2, "works on an endless stream")


RECORDS = [
    {"model": "phi3:mini", "tokens": 120, "ok": True},
    {"model": "llama3:8b", "tokens": 300, "ok": False},
    {"model": "llama3:8b", "tokens": 250, "ok": True},
    {"model": "mixtral", "tokens": 80, "ok": True},
]


def test_ex02(m):
    """token_report: generator expressions, one-pass input"""
    expected = {"total": 450, "max": 250, "failed": 1}
    expect(m.token_report(RECORDS), expected)
    expect(m.token_report(r for r in RECORDS), expected,
           "a generator is exhausted after one pass; materialize it with list() first")
    expect(m.token_report([]), {"total": 0, "max": 0, "failed": 0})
    expect(m.token_report([{"model": "x", "tokens": 5, "ok": False}]),
           {"total": 0, "max": 0, "failed": 1})


def test_ex03(m):
    """backoff_delays: a generator function with yield"""
    gen = m.backoff_delays(1, 2, 10, 6)
    assert inspect.isgenerator(gen), "use `yield`, don't return a list"
    expect(list(gen), [1, 2, 4, 8, 10, 10])
    expect(list(m.backoff_delays(0.5, 3, 5, 3)), [0.5, 1.5, 4.5])
    expect(list(m.backoff_delays(1, 2, 10, 0)), [])


def test_ex04(m):
    """read_table: iter() + next() to peel off a header"""
    lines = ["model, latency_ms\n", "phi3, 412\n", "\n", "llama3 , 380\n"]
    expected = [{"model": "phi3", "latency_ms": "412"}, {"model": "llama3", "latency_ms": "380"}]
    expect(m.read_table(lines), expected)
    expect(m.read_table(line for line in lines), expected, "must work on a generator / file object")
    expect(m.read_table(["a,b\n"]), [], "header only")
    expect(m.read_table([]), [])


def test_ex05(m):
    """next_free_ids: count() + filter + islice"""
    expect(m.next_free_ids("T", {"T-001", "T-003"}, 3), ["T-002", "T-004", "T-005"])
    expect(m.next_free_ids("BUG", set(), 2), ["BUG-001", "BUG-002"])
    expect(m.next_free_ids("T", {"T-001"}, 0), [])
    taken = {f"T-{i:03d}" for i in range(1, 500)}
    expect(m.next_free_ids("T", taken, 1), ["T-500"])


def test_ex06(m):
    """first_over_budget: accumulate + enumerate(start=1)"""
    expect(m.first_over_budget([0.5, 1.25, 2.0, 0.75], 3.0), 3)
    expect(m.first_over_budget([1.0, 2.0], 3.0), None, "equal to budget is not over it")
    expect(m.first_over_budget([], 1.0), None)
    expect(m.first_over_budget([5.0], 1.0), 1, "call numbers are 1-based")
    pulled = []
    expect(m.first_over_budget(_tracking(itertools.repeat(0.25, 10_000), pulled), 1.0), 5)
    expect(len(pulled), 5, "stop reading once over budget (costs may be an endless stream)")


BOOKINGS = [
    {"room": "B", "start": "10:00", "who": "Bo"},
    {"room": "A", "start": "11:00", "who": "Di"},
    {"room": "B", "start": "09:00", "who": "Cy"},
    {"room": "A", "start": "09:00", "who": "Al"},
    {"room": "C", "start": "13:00", "who": "Ed"},
]


def test_ex07(m):
    """bookings_by_room: sort first, then groupby"""
    snapshot = list(BOOKINGS)
    expect(m.bookings_by_room(BOOKINGS),
           [("A", ["Al", "Di"]), ("B", ["Cy", "Bo"]), ("C", ["Ed"])],
           "groupby only merges ADJACENT keys; did you sort by (room, start) first?")
    expect(BOOKINGS, snapshot, "input list was mutated; use sorted(), not .sort()")
    expect(m.bookings_by_room([]), [])


def test_ex08(m):
    """split_sessions: pairwise deltas between timestamps"""
    expect(m.split_sessions([0, 30, 50, 400, 420, 2000], 300), [[0, 30, 50], [400, 420], [2000]])
    expect(m.split_sessions([0, 300, 600], 300), [[0, 300, 600]], "a gap of exactly max_gap stays")
    expect(m.split_sessions([7], 300), [[7]])
    expect(m.split_sessions([], 300), [])


def test_ex09(m):
    """interleave: zip_longest + chain.from_iterable + sentinel"""
    expect(m.interleave(["a1", "a2", "a3"], ["b1"], ["c1", "c2"]),
           ["a1", "b1", "c1", "a2", "c2", "a3"])
    expect(m.interleave([1, 0], [None], ["", 2, 3]), [1, None, "", 0, 2, 3],
           "None / 0 / '' are real jobs; filter with a sentinel and `is not`")
    expect(m.interleave(["solo"]), ["solo"])
    expect(m.interleave(), [])


def test_ex10(m):
    """batched: lazy fixed-size chunks with islice"""
    expect(list(m.batched("ABCDEFG", 3)), [("A", "B", "C"), ("D", "E", "F"), ("G",)])
    expect(list(m.batched([1, 2, 3, 4], 2)), [(1, 2), (3, 4)])
    expect(list(m.batched([], 3)), [])
    pulled = []
    gen = m.batched(_tracking(range(100), pulled), 4)
    assert inspect.isgenerator(gen), "use `yield`, don't return a list"
    expect((next(gen), len(pulled)), ((0, 1, 2, 3), 4), "first batch should pull exactly 4 items")
    gen = m.batched(itertools.count(), 3)
    expect(list(itertools.islice(gen, 2)), [(0, 1, 2), (3, 4, 5)], "must work on an endless input")
    expect_raises(ValueError, lambda: list(m.batched([1, 2], 0)))


TREE = {
    "src": {"main.py": 120, "util": {"io.py": 40, "empty": {}}},
    "README.md": 10,
    "tests": {"test_io.py": 30},
}


def test_ex11(m):
    """walk: recursive generator with yield from"""
    gen = m.walk(TREE)
    assert inspect.isgenerator(gen), "use `yield` / `yield from`, don't return a list"
    expect(list(gen), [
        ("src/main.py", 120),
        ("src/util/io.py", 40),
        ("README.md", 10),
        ("tests/test_io.py", 30),
    ])
    expect(sum(size for _, size in m.walk(TREE)), 200)
    expect(list(m.walk({})), [])


def _fake_api(pages):
    """pages: {token: (items, next_token)}; the first page lives under None."""
    calls = []

    def fetch(token):
        calls.append(token)
        return pages[token]

    return fetch, calls


def test_ex12(m):
    """PageIterator: __iter__/__next__/StopIteration, lazy fetching"""
    pages = {None: (["a", "b"], "p2"), "p2": ([], "p3"), "p3": (["c"], None)}
    fetch, calls = _fake_api(pages)
    it = m.PageIterator(fetch)
    expect(calls, [], "don't fetch in __init__; wait until someone asks for an item")
    assert iter(it) is it, "__iter__ should return self"
    expect(next(it), "a")
    expect(next(it), "b")
    expect(calls, [None], "page 2 shouldn't be fetched until page 1 is used up")
    expect(list(it), ["c"], "should skip the empty page and continue")
    expect(calls, [None, "p2", "p3"])
    expect_raises(StopIteration, next, it)
    expect(calls, [None, "p2", "p3"], "never fetch again after the last page")

    fetch, calls = _fake_api({None: ([1, 2, 3], None)})
    expect([x * 10 for x in m.PageIterator(fetch)], [10, 20, 30], "should work in a for loop")
    fetch, calls = _fake_api({None: ([], None)})
    expect(list(m.PageIterator(fetch)), [])


def test_ex13(m):
    """first_errors: lazy parse -> filter -> take pipeline"""
    lines = [INFO, "garbage", ERR1, WARN, ERR2, INFO, ERR1]
    expect(m.first_errors(lines, 5), [
        ("provider", "Model not loaded: phi3"),
        ("cli", "Unknown command: lst"),
        ("provider", "Model not loaded: phi3"),
    ])
    pulled = []
    expect(m.first_errors(_tracking(lines, pulled), 2),
           [("provider", "Model not loaded: phi3"), ("cli", "Unknown command: lst")])
    expect(len(pulled), 5, "stop reading right after the 2nd error")
    pulled = []
    expect(m.first_errors(_tracking(lines, pulled), 0), [])
    expect(len(pulled), 0, "n=0 should read nothing (islice(..., 0) pulls nothing)")
    expect(len(m.first_errors(itertools.cycle([INFO, ERR2]), 3)), 3, "works on an endless stream")


def test_ex14(m):
    """running_average: a coroutine driven by send()"""
    avg = m.running_average()
    assert inspect.isgenerator(avg), "a coroutine is a generator function that uses `x = yield ...`"
    expect(next(avg), None, "priming with next() should yield None")
    expect(avg.send(10), 10.0)
    expect(avg.send(20), 15.0)
    expect(avg.send(0), 10.0)
    other = m.running_average()
    next(other)
    expect(other.send(400), 400.0, "each coroutine keeps its own state")
    expect(avg.send(30), 15.0)
