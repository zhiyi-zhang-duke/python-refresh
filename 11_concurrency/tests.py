import asyncio
import threading
import time

from harness import expect, expect_raises


# ------------------------------------------------------------- helpers ----

def _elapsed(fn, *args, **kwargs):
    """Run fn and return (result, seconds)."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - t0


def _with_deadline(fn, seconds: float = 2.0, what: str = ""):
    """Run fn in a daemon thread so a deadlock/hang becomes a readable failure
    instead of freezing the runner. Re-raises whatever fn raised (incl. NotImplementedError)."""
    box = {}

    def target():
        try:
            box["result"] = fn()
        except BaseException as e:  # noqa: BLE001 - shuttled back to the main thread below
            box["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        raise AssertionError(f"still running after {seconds}s: {what or 'hung'}")
    if "error" in box:
        raise box["error"]
    return box.get("result")


def _wait_until(pred, timeout: float = 1.0) -> bool:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if pred():
            return True
        time.sleep(0.005)
    return pred()


def _slow_square(x):
    time.sleep(0.05)
    return x * x


class _InFlight:
    """Thread-safe tracker of how many calls overlap; records the peak."""

    def __init__(self):
        self.now = 0
        self.peak = 0
        self._lock = threading.Lock()

    def __enter__(self):
        with self._lock:
            self.now += 1
            self.peak = max(self.peak, self.now)

    def __exit__(self, *exc):
        with self._lock:
            self.now -= 1


# ---------------------------------------------------------------- tests ----

def test_ex01(m):
    """run_in_threads: start N threads, join them, keep input order"""
    expect(m.run_in_threads(lambda x: x + 1, [1, 2, 3]), [2, 3, 4])
    expect(m.run_in_threads(lambda x: x, []), [])

    before = threading.active_count()
    result, secs = _elapsed(m.run_in_threads, _slow_square, list(range(10)))
    expect(result, [x * x for x in range(10)], "results must be in the same order as args")
    assert secs < 0.3, f"10 x 0.05s took {secs:.2f}s; threads should overlap (expected < 0.3s)"
    assert threading.active_count() <= before, "threads still alive after return: join() them all"


def test_ex02(m):
    """Counter: threading.Lock fixes a lost-update race"""
    c = m.Counter()
    c.increment()
    c.increment()
    expect(c.value, 2)

    c = m.Counter(pause=lambda: time.sleep(0))  # sleep(0) yields the GIL mid-update
    gate = threading.Barrier(8)

    def worker():
        gate.wait()
        for _ in range(100):
            c.increment()

    def run():
        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    _with_deadline(run, what="Counter threads (deadlock?)")
    expect(c.value, 800, "8 threads x 100 increments; lost updates mean the lock is missing or too narrow")


def test_ex03(m):
    """parallel_fetch: ThreadPoolExecutor.map over a fake fetch"""
    expect(m.parallel_fetch(["a", "b"], str.upper), {"a": "A", "b": "B"})

    urls = [f"u{i}" for i in range(10)]
    fetch = lambda u: (time.sleep(0.05), u.upper())[1]
    result, secs = _elapsed(m.parallel_fetch, urls, fetch)
    expect(result, {u: u.upper() for u in urls})
    assert secs < 0.3, f"10 fetches x 0.05s took {secs:.2f}s; expected < 0.3s with a pool"

    tracker = _InFlight()

    def tracked(u):
        with tracker:
            time.sleep(0.03)
        return u

    m.parallel_fetch(urls[:6], tracked, max_workers=2)
    expect(tracker.peak, 2, "peak concurrent fetches with max_workers=2")


def test_ex04(m):
    """fetch_all_async: async def, await, asyncio.gather"""
    async def fetch(u):
        await asyncio.sleep(0.05)
        return u.upper()

    urls = [f"u{i}" for i in range(10)]
    result, secs = _elapsed(asyncio.run, m.fetch_all_async(urls, fetch))
    expect(result, [u.upper() for u in urls], "results in input order")
    assert secs < 0.25, f"took {secs:.2f}s; awaiting in a loop is sequential, use gather"


def test_ex05(m):
    """BookingService: lock around check-then-insert (the double-booking race)"""
    s = m.BookingService()
    assert s.book("A", 9, 11) is True
    assert s.book("A", 10, 12) is False, "10-12 overlaps 9-11"
    assert s.book("A", 8, 10) is False, "8-10 overlaps 9-11"
    assert s.book("A", 11, 12) is True, "touching (end == start) is not an overlap"
    assert s.book("A", 7, 9) is True, "touching on the other side is fine too"
    assert s.book("B", 9, 11) is True, "different room, no conflict"
    expect(s.bookings("A"), [(7, 9), (9, 11), (11, 12)], "sorted by start")
    expect(s.bookings("Z"), [], "unknown room")

    s = m.BookingService(pause=lambda: time.sleep(0.01))
    gate = threading.Barrier(8)
    outcomes = []

    def attempt():
        gate.wait()
        outcomes.append(s.book("A", 9, 10))

    def run():
        threads = [threading.Thread(target=attempt) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    _with_deadline(run, what="8 concurrent book() calls (deadlock?)")
    expect(outcomes.count(True), 1,
           "8 threads raced for room A 9-10; exactly one may win. "
           "Hold the lock across the check AND the insert")
    expect(s.bookings("A"), [(9, 10)])


def test_ex06(m):
    """fetch_as_completed: submit + as_completed, per-task exceptions"""
    delays = {"slow": 0.12, "bad": 0.06, "fast": 0.0}

    def fetch(u):
        time.sleep(delays[u])
        if u == "bad":
            raise ValueError("bad url")
        return u.upper()

    result = m.fetch_as_completed(["slow", "bad", "fast"], fetch)
    expect([url for url, _ in result], ["fast", "bad", "slow"], "order the fetches finished in")
    outcomes = dict(result)
    expect(outcomes["fast"], "FAST")
    expect(outcomes["slow"], "SLOW")
    assert isinstance(outcomes["bad"], ValueError), \
        f"failed fetch should map to its exception instance, got {outcomes['bad']!r}"


def test_ex07(m):
    """call_with_timeout: future.result(timeout=) without blocking on exit"""
    expect(m.call_with_timeout(lambda: 42, 1.0), (True, 42))
    expect(m.call_with_timeout(lambda a, b: a + b, 1.0, 2, 3), (True, 5), "pass *args through")

    result, secs = _elapsed(m.call_with_timeout, time.sleep, 0.05, 0.2)
    expect(result, (False, None), "fn slower than timeout")
    assert secs < 0.15, (f"returned after {secs:.2f}s; the timeout was 0.05s. "
                         "Is a `with ThreadPoolExecutor()` waiting for the slow thread on exit?")

    def boom():
        raise KeyError("nope")

    expect_raises(KeyError, m.call_with_timeout, boom, 1.0)


def test_ex08(m):
    """producer_consumer: queue.Queue with one sentinel per consumer"""
    got = _with_deadline(lambda: m.producer_consumer([1, 2, 3], lambda x: x * 10, n_consumers=2),
                         what="producer_consumer (a consumer never got its sentinel?)")
    expect(sorted(got), [10, 20, 30])

    got = _with_deadline(lambda: m.producer_consumer([], lambda x: x, n_consumers=3),
                         what="producer_consumer with no items")
    expect(got, [])

    def slow(x):
        time.sleep(0.05)
        return -x

    t0 = time.perf_counter()
    got = _with_deadline(lambda: m.producer_consumer(list(range(9)), slow, n_consumers=3),
                         what="producer_consumer with 9 items")
    secs = time.perf_counter() - t0
    expect(sorted(got), sorted(-x for x in range(9)))
    assert secs < 0.35, f"9 items x 0.05s over 3 consumers took {secs:.2f}s; expected < 0.35s"


def test_ex09(m):
    """Ticker: threading.Event for prompt shutdown"""
    ticks = []
    t = m.Ticker(interval=5.0, on_tick=lambda: ticks.append(1))
    t.start()
    assert _wait_until(lambda: len(ticks) >= 1), "on_tick should run right away on start()"
    assert t.running is True
    _, secs = _elapsed(_with_deadline, t.stop, 2.0,
                       "stop() with a 5s interval; is the loop in time.sleep instead of event.wait?")
    assert secs < 0.5, f"stop() took {secs:.2f}s; wait on the Event instead of time.sleep"
    assert t.running is False, "thread should be finished after stop()"
    expect(len(ticks), 1, "ticks with a 5s interval stopped immediately")

    ticks.clear()
    t = m.Ticker(interval=0.02, on_tick=lambda: ticks.append(1))
    t.start()
    time.sleep(0.2)
    _with_deadline(t.stop, what="stop()")
    n = len(ticks)
    time.sleep(0.05)
    assert n >= 3, f"only {n} ticks in 0.2s at a 0.02s interval"
    expect(len(ticks), n, "on_tick kept firing after stop()")


def test_ex10(m):
    """gather_settled: gather(return_exceptions=True)"""
    async def fetch(u):
        await asyncio.sleep(0.05)
        if u == "bad":
            raise KeyError(u)
        return u.upper()

    urls = ["a", "bad", "b", "c", "d"]
    result, secs = _elapsed(asyncio.run, m.gather_settled(urls, fetch))
    expect(sorted(result), sorted(urls))
    expect({k: v for k, v in result.items() if k != "bad"}, {"a": "A", "b": "B", "c": "C", "d": "D"})
    assert isinstance(result["bad"], KeyError), f"expected the KeyError instance, got {result['bad']!r}"
    assert secs < 0.2, f"took {secs:.2f}s; the fetches should run concurrently"


def test_ex11(m):
    """bounded_fetch: asyncio.Semaphore caps in-flight requests"""
    for limit in (3, 1):
        state = {"now": 0, "peak": 0}

        async def fetch(u):
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
            await asyncio.sleep(0.01)
            state["now"] -= 1
            return u * 2

        urls = [str(i) for i in range(10)]
        result = asyncio.run(m.bounded_fetch(urls, fetch, limit))
        expect(result, [u * 2 for u in urls], "results in input order")
        expect(state["peak"], limit, f"peak concurrent fetches with limit={limit}")


def test_ex12(m):
    """retry: wait_for timeout + exponential backoff with injected sleep"""
    delays = []

    async def fake_sleep(d):
        delays.append(d)

    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("try again")
        return "ok"

    expect(asyncio.run(m.retry(flaky, attempts=3, sleep=fake_sleep)), "ok")
    expect(delays, [0.1, 0.2], "backoff before attempts 2 and 3")

    delays.clear()

    async def always_bad():
        raise ValueError("nope")

    expect_raises(ValueError, asyncio.run, m.retry(always_bad, attempts=3, sleep=fake_sleep))
    expect(delays, [0.1, 0.2], "no sleep after the final failed attempt")

    delays.clear()
    calls["n"] = 0

    async def hangs_once():
        calls["n"] += 1
        if calls["n"] == 1:
            await asyncio.sleep(10)
        return "late-ok"

    result, secs = _elapsed(asyncio.run, m.retry(hangs_once, timeout=0.05, base_delay=0.5,
                                                 sleep=fake_sleep))
    expect(result, "late-ok")
    expect(delays, [0.5], "one backoff after the timed-out attempt")
    assert secs < 0.5, f"took {secs:.2f}s; each attempt should be cut off by wait_for(timeout)"

    async def hangs():
        await asyncio.sleep(10)

    expect_raises(asyncio.TimeoutError, asyncio.run,
                  m.retry(hangs, attempts=2, timeout=0.03, sleep=fake_sleep))


def test_ex13(m):
    """run_worker_pool: asyncio.Queue workers, errors captured, clean shutdown"""
    state = {"now": 0, "peak": 0}

    async def handle(job):
        state["now"] += 1
        state["peak"] = max(state["peak"], state["now"])
        try:
            await asyncio.sleep(0.03)
            if job == 7:
                raise ValueError("job 7 is cursed")
            return job * 2
        finally:
            state["now"] -= 1

    async def main():
        out = await m.run_worker_pool(list(range(12)), handle, n_workers=4)
        leftover = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        return out, len(leftover)

    (result, leftover), secs = _elapsed(asyncio.run, main())
    expect([r for i, r in enumerate(result) if i != 7], [i * 2 for i in range(12) if i != 7],
           "results aligned with jobs")
    assert isinstance(result[7], ValueError), f"job 7 should map to its ValueError, got {result[7]!r}"
    expect(state["peak"], 4, "peak concurrent jobs with n_workers=4")
    expect(leftover, 0, "worker tasks still pending after return: cancel AND await them")
    assert secs < 0.3, f"12 jobs x 0.03s over 4 workers took {secs:.2f}s; expected < 0.3s"

    expect(asyncio.run(m.run_worker_pool([], handle, n_workers=3)), [], "no jobs")
