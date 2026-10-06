import json
from datetime import datetime

from harness import expect, expect_raises


def _tracking(items, pulled):
    """Yield from items, recording every item handed out (to prove laziness)."""
    for x in items:
        pulled.append(x)
        yield x


LOG = [
    "2026-09-14 10:03:20 INFO [cli] start",
    "2026-09-14 10:03:21 ERROR [provider] Model not loaded: phi3",
    "",
    "2026-09-14 10:03:22 WARNING [cache] stale entry",
    "2026-09-14 10:03:23 ERROR [cli] Unknown command: lst",
    "2026-09-14 10:03:24 ERROR [provider] Timeout after 30s",
    "2026-09-14 10:03:25 INFO [cli] bye",
]


def test_ex01(m):
    """recent_errors: deque(maxlen=n) as a tail buffer"""
    expect(m.recent_errors(LOG, 2), [LOG[4], LOG[5]])
    expect(m.recent_errors(LOG, 10), [LOG[1], LOG[4], LOG[5]])
    expect(m.recent_errors(iter(LOG), 1), [LOG[5]], "must work on a one-pass iterator")
    expect(m.recent_errors(LOG, 0), [])
    expect(m.recent_errors([], 3), [])


RUNS = [
    {"model": "phi3:mini", "latency_ms": 412.5},
    {"model": "llama3:8b", "latency_ms": 380.0},
    {"model": "mixtral", "latency_ms": 951.25},
    {"model": "phi3:mini", "latency_ms": 402.0},
    {"model": "llama3:8b", "latency_ms": 377.5},
    {"model": "gemma2", "latency_ms": 990.0},
]


def test_ex02(m):
    """benchmark_stats: statistics, min(key=), heapq.nsmallest"""
    expect(m.benchmark_stats(RUNS), {
        "min": 377.5,
        "avg": 585.5,
        "p50": 407.25,
        "fastest": "llama3:8b",
        "top3": ["llama3:8b", "llama3:8b", "phi3:mini"],
    })
    one = m.benchmark_stats([{"model": "solo", "latency_ms": 10.0}])
    expect((one["p50"], one["top3"]), (10.0, ["solo"]), "fewer than 3 runs is fine")
    expect_raises(ValueError, m.benchmark_stats, [])


def test_ex03(m):
    """Benchmark NamedTuple + parse_benchmark"""
    b = m.parse_benchmark("phi3:mini, 412.5, ok")
    expect(m.Benchmark._fields, ("model", "latency_ms", "ok"), "declare the fields in this order")
    expect(b, m.Benchmark("phi3:mini", 412.5, True))
    expect((b.model, b.latency_ms, b.ok), ("phi3:mini", 412.5, True))
    expect(m.parse_benchmark("mixtral,951.25,fail"), m.Benchmark("mixtral", 951.25, False))
    expect(m.parse_benchmark("llama3:8b, 380"), m.Benchmark("llama3:8b", 380.0, True))
    expect(m.Benchmark("x", 1.0).ok, True, "ok should default to True")
    model, latency, ok = b
    expect(latency, 412.5, "a NamedTuple unpacks like a tuple")
    expect(b._replace(ok=False).ok, False)
    expect_raises(AttributeError, setattr, b, "ok", False)
    expect_raises(ValueError, m.parse_benchmark, "phi3, 10, maybe")


def test_ex04(m):
    """latency_bucket: bisect_right into breakpoints"""
    cases = {0: "fast", 199.9: "fast", 200: "ok", 499: "ok", 500: "slow",
             999.99: "slow", 1000: "timeout", 30000: "timeout"}
    for ms, label in cases.items():
        expect(m.latency_bucket(ms), label, f"latency_bucket({ms})")


YESTERDAY = ["durham", "Raleigh", "raleigh", "new york", "Cary"]
TODAY = ["Durham", "durham ", "DURHAM", "raleigh", "new  york", "New York", "NEW YORK",
         "new york", "cary", "Austin"]


def test_ex05(m):
    """trending_cities: Counter subtraction + most_common"""
    expect(m.trending_cities(YESTERDAY, TODAY, 2), [("New York", 3), ("Durham", 2)])
    expect(m.trending_cities(YESTERDAY, TODAY, 10),
           [("New York", 3), ("Durham", 2), ("Austin", 1)],
           "cities that shrank (Raleigh) or stayed flat (Cary) are left out")
    expect(m.trending_cities(["x"], [], 3), [])


def _node(name, latencies, model="phi3"):
    return [{"node": name, "model": model, "latency_ms": ms} for ms in latencies]


def test_ex06(m):
    """fastest_overall: heapq.merge of sorted streams"""
    nodes = [
        _node("gpu-1", [377.5, 402.0, 951.25], "llama3"),
        _node("gpu-2", [380.0, 990.0], "phi3"),
        _node("gpu-3", [100.0, 2000.0], "tiny"),
    ]
    expect(m.fastest_overall(nodes, 3), [
        ("gpu-3", "tiny", 100.0),
        ("gpu-1", "llama3", 377.5),
        ("gpu-2", "phi3", 380.0),
    ])
    expect(len(m.fastest_overall(nodes, 99)), 7)
    expect(m.fastest_overall([[], []], 2), [])
    pulled = []
    streams = [_tracking(_node(f"gpu-{i}", range(i, 10_000, 3)), pulled) for i in range(3)]
    expect([ms for _, _, ms in m.fastest_overall(streams, 4)], [0, 1, 2, 3])
    assert len(pulled) <= 4 + 3, (
        f"read {len(pulled)} results to find 4; merge lazily instead of sorting everything")


SESSIONS = [
    ("2026-09-14 10:03", "2026-09-14 11:30"),
    ("2026-09-15 22:00", "2026-09-17 00:30"),
    ("2026-09-14 13:00", "2026-09-14 13:45"),
    ("2026-09-17 09:15", "2026-09-17 09:20"),
]


def test_ex07(m):
    """minutes_by_day: strptime, timedelta, strftime"""
    expect(m.minutes_by_day(SESSIONS),
           {"Mon 09/14": 132, "Tue 09/15": 1590, "Thu 09/17": 5},
           "Tue 09/15 runs 26.5 hours; delta.seconds drops the whole day")
    expect(m.minutes_by_day([]), {})
    expect(m.minutes_by_day([("2026-09-14 10:00", "2026-09-14 10:00")]), {"Mon 09/14": 0})
    expect_raises(ValueError, m.minutes_by_day, [("2026-09-14 10:00", "2026-09-14 09:00")])
    expect_raises(ValueError, m.minutes_by_day, [("09/14 10:00", "09/14 11:00")])


def test_ex08(m):
    """schedule_matchups: combinations + product"""
    expect(m.schedule_matchups(["a", "b", "c"], ["R1", "R2"], ["10:00", "11:00"]), [
        ("a", "b", "10:00", "R1"),
        ("a", "c", "10:00", "R2"),
        ("b", "c", "11:00", "R1"),
    ])
    four = m.schedule_matchups(["phi3", "llama3", "mixtral", "gemma2"], ["R1", "R2"],
                               ["9", "10", "11"])
    expect(len(four), 6, "4 models -> C(4, 2) = 6 matchups")
    expect(four[-1], ("mixtral", "gemma2", "11", "R2"))
    expect(m.schedule_matchups(["solo"], ["R1"], ["9"]), [])
    expect_raises(ValueError, m.schedule_matchups, ["a", "b", "c"], ["R1"], ["9", "10"])


def test_ex09(m):
    """count_ways: memoized recursion with lru_cache"""
    expect(m.count_ways(10, (1, 2, 5)), 10)
    assert hasattr(m.count_ways, "cache_info"), (
        "decorate count_ways with @lru_cache(maxsize=None) (or @cache)")
    expect(m.count_ways(3, (2,)), 0)
    expect(m.count_ways(0, (1, 5)), 1, "one way to make 0: use no coins")
    m.count_ways.cache_clear()
    expect(m.count_ways(100, (1, 5, 10, 25, 50)), 292)
    info = m.count_ways.cache_info()
    assert info.hits > 0, (
        f"{info}: no cache hits; the recursion must call the decorated count_ways itself")
    expect(m.count_ways(300, (1, 5, 10, 25, 50)), 9590)
    expect_raises(TypeError, m.count_ways, 10, [1, 2, 5])   # lists are unhashable


GRID = [
    "...#....",
    ".#.#.##.",
    ".#...#..",
    ".####.#.",
    "......#.",
]


def test_ex10(m):
    """shortest_path: BFS on a grid with deque"""
    expect(m.shortest_path(GRID, (0, 0), (4, 7)), 15)
    expect(m.shortest_path(GRID, (0, 0), (0, 4)), 8)
    expect(m.shortest_path(GRID, (4, 0), (4, 5)), 5)
    expect(m.shortest_path(GRID, (2, 2), (2, 2)), 0)
    expect(m.shortest_path([".#.", "##.", "..."], (0, 0), (2, 2)), -1)
    expect(m.shortest_path(["." * 60] * 60, (0, 0), (59, 59)), 118)


def test_ex11(m):
    """TTLCache: normalized keys, injected clock, expiry"""
    t = [0.0]
    cache = m.TTLCache(60, now=lambda: t[0])
    cache.set("  New   York", 21)
    expect(cache.get("new york"), 21, "keys should be normalized")
    expect(cache.get("Durham"), None)
    t[0] = 59.9
    expect(cache.get("NEW YORK "), 21, "still fresh just before ttl")
    t[0] = 60.0
    expect(cache.get("new york"), None, "expired at exactly ttl (fresh means age < ttl)")

    calls = []
    temps = {"durham": 24, "austin": 31}

    def fetch(city):
        calls.append(city)
        return temps[city]

    t[0] = 100.0
    expect(cache.get_or_fetch(" Durham ", fetch), 24)
    expect(calls, ["durham"], "fetch should get the normalized key")
    t[0] = 150.0
    expect(cache.get_or_fetch("durham", fetch), 24)
    expect(calls, ["durham"], "fresh hit should not call fetch")
    temps["durham"] = 26
    t[0] = 160.0
    expect(cache.get_or_fetch("DURHAM", fetch), 26, "stale entry should be refetched")
    expect(calls, ["durham", "durham"])
    cache.set("durham", 30)
    t[0] = 210.0
    expect(cache.get("durham"), 30, "set() should restamp the time")


def test_ex12(m):
    """TaskScheduler: heapq with (priority, seq, task)"""
    s = m.TaskScheduler()
    expect(len(s), 0)
    s.add({"job": "deploy"}, 2)
    s.add({"job": "hotfix"}, 1)
    s.add({"job": "lint"}, 2)
    s.add({"job": "backup"}, 3)
    s.add({"job": "alert"}, 1)
    expect(len(s), 5)
    order = [s.pop()["job"] for _ in range(5)]
    expect(order, ["hotfix", "alert", "deploy", "lint", "backup"],
           "lower number first; ties in insertion order")
    expect(len(s), 0)
    expect_raises(IndexError, s.pop)
    s.add("write", 1)
    s.add("deploy", 1)
    expect(s.pop(), "write", "ties go by insertion order, not by comparing the tasks")


def test_ex13(m):
    """apply_events: Enum + transition table"""
    S = m.Status
    expect(m.apply_events("pending", ["start", "fail", "retry", "start", "succeed"]), S.SUCCEEDED)
    expect(m.apply_events("running", ["cancel"]), S.CANCELLED)
    expect(m.apply_events("failed", []), S.FAILED)
    assert m.apply_events("pending", ["start"]) is S.RUNNING, "return the Status member, not a string"
    err = expect_raises(ValueError, m.apply_events, "succeeded", ["start"])
    assert "SUCCEEDED" in str(err) and "start" in str(err), f"unhelpful message: {err}"
    expect_raises(ValueError, m.apply_events, "pending", ["succeed"])
    expect_raises(ValueError, m.apply_events, "bogus", [])


def test_ex14(m):
    """encode_job / decode_job: json with a custom default"""
    job = {
        "id": 7,
        "status": m.Status.RUNNING,
        "created_at": datetime(2026, 9, 14, 10, 3),
        "finished_at": None,
        "tags": ["gpu", "nightly"],
    }
    text = m.encode_job(job)
    expect(text, '{"created_at": "2026-09-14T10:03:00", "finished_at": null, "id": 7, '
                 '"status": "running", "tags": ["gpu", "nightly"]}')
    expect(json.loads(text)["status"], "running")
    expect_raises(TypeError, m.encode_job, {"ids": {1, 2}})
    back = m.decode_job(text)
    expect(back, job, "decode_job(encode_job(job)) should == job")
    assert back["status"] is m.Status.RUNNING
    expect(m.decode_job('{"id": 1}'), {"id": 1}, "missing keys are fine")
