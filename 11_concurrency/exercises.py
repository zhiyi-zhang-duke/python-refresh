"""11 - Concurrency

Fill in each function, then run:   python 11_concurrency/exercises.py
Run just one exercise:             python 11_concurrency/exercises.py 4
Run exercise 4 onward:             python 11_concurrency/exercises.py 4+

Exercises go from easy (01) to advanced (13). Delete the `raise NotImplementedError`
line when you start one. Threads first (01-09), then asyncio (04, 10-13).

Every "fetch" here is a fake you are handed (it just sleeps), so the tests can prove
things ran in parallel by timing them: 10 jobs x 0.05s must finish well under 0.5s.
"""

import asyncio
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError


# ---------------------------------------------------------------- easy ----

def run_in_threads(fn, args: list) -> list:
    """ex01. Call fn(arg) for every arg, each in its own threading.Thread, wait for
    all of them, and return the results in the SAME order as args.

    run_in_threads(lambda x: x * x, [1, 2, 3]) -> [1, 4, 9]

    A Thread can't hand back a return value, so have each thread write into its
    own slot of a pre-sized results list. Every thread must be joined before you return.

    Tools: threading.Thread(target=..., args=(...,)), t.start(), t.join(),
           results = [None] * len(args)
    """
    raise NotImplementedError


class Counter:
    """ex02. A counter that stays correct when many threads call increment().

    increment() must do the read-modify-write in three steps, in this order:
        1. read the current value
        2. call self.pause()        (the tests pass time.sleep(0) to widen the race)
        3. write back value + 1
    Without a lock, two threads read the same value and an update is lost.

    c = Counter(); c.increment(); c.increment(); c.value -> 2
    8 threads x 100 increments with pause=time.sleep(0) -> c.value == 800, every time

    Tools: threading.Lock(), `with self._lock:` around the whole read-pause-write,
           @property for value
    """

    def __init__(self, pause=lambda: None):
        raise NotImplementedError

    def increment(self) -> None:
        raise NotImplementedError

    @property
    def value(self) -> int:
        raise NotImplementedError


def parallel_fetch(urls: list[str], fetch, max_workers: int = 8) -> dict[str, object]:
    """ex03. Fetch every url with a thread pool and return {url: fetch(url)}.

    fetch is a plain (blocking) function you are given. At most max_workers fetches
    may run at once.

    parallel_fetch(["a", "b"], str.upper) -> {"a": "A", "b": "B"}

    Tools: `with ThreadPoolExecutor(max_workers=...) as pool:`, pool.map(fn, items)
           (map yields results in INPUT order), zip
    """
    raise NotImplementedError


async def fetch_all_async(urls: list[str], fetch) -> list:
    """ex04. fetch is an ASYNC function: `await fetch(url)`. Run all fetches
    concurrently and return the results in the same order as urls.

    asyncio.run(fetch_all_async(["a", "b"], fake_fetch)) -> [fake result a, fake result b]

    Awaiting them one at a time in a for loop is sequential (10 x 0.05s = 0.5s).
    The test requires < 0.25s.

    Tools: asyncio.gather(*coroutines) returns results in argument order
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

class BookingService:
    """ex05. Room bookings that stay correct when two requests race for the same slot.

    book(room, start, end) -> bool
        True and store (start, end) if it doesn't overlap an existing booking for that
        room; otherwise False. Times are ints, half-open [start, end): (9, 10) and
        (10, 11) do NOT overlap. Overlap test: start < other_end and other_start < end.
        Between the overlap CHECK and the INSERT, call self.pause(). The tests pass
        a pause that sleeps, so without a lock 8 threads all pass the check and all
        insert. With a lock exactly one of them wins.
    bookings(room) -> list[tuple[int, int]]   that room's bookings, sorted by start

    s = BookingService()
    s.book("A", 9, 11)  -> True
    s.book("A", 10, 12) -> False      overlaps 9-11
    s.book("A", 11, 12) -> True       touching is fine
    s.bookings("A")     -> [(9, 11), (11, 12)]

    Tools: threading.Lock, `with self._lock:` around check AND insert together,
           dict[str, list[tuple[int, int]]] or collections.defaultdict(list)
    """

    def __init__(self, pause=lambda: None):
        raise NotImplementedError

    def book(self, room: str, start: int, end: int) -> bool:
        raise NotImplementedError

    def bookings(self, room: str) -> list[tuple[int, int]]:
        raise NotImplementedError


def fetch_as_completed(urls: list[str], fetch, max_workers: int = 8) -> list[tuple[str, object]]:
    """ex06. Fetch every url in a thread pool. Return (url, outcome) pairs in the order
    the fetches FINISH, not the order of urls. outcome is the return value, or the
    exception instance if fetch raised. One bad url must not lose the others.

    With fetch delays slow=0.12s, bad=0.06s (raises ValueError), fast=0s:
    fetch_as_completed(["slow", "bad", "fast"], fetch)
      -> [("fast", "FAST"), ("bad", ValueError(...)), ("slow", "SLOW")]

    Tools: pool.submit(fn, arg) returns a Future; keep a {future: url} dict;
           `for fut in as_completed(futures):`; fut.exception() returns the
           exception or None (fut.result() would re-raise it)
    """
    raise NotImplementedError


def call_with_timeout(fn, timeout: float, *args) -> tuple[bool, object]:
    """ex07. Run fn(*args) in a worker thread and wait at most `timeout` seconds.

    Finished in time  -> (True, result)
    Timed out         -> (False, None), and return right away: don't wait for fn
    fn raised         -> let the exception propagate to the caller

    call_with_timeout(lambda: 42, 1.0)                   -> (True, 42)
    call_with_timeout(lambda: time.sleep(0.2), 0.05)     -> (False, None) in ~0.05s

    Trap: `with ThreadPoolExecutor() as pool:` calls shutdown(wait=True) on exit,
    which blocks until the slow fn finishes, so your timeout silently becomes 0.2s.
    You can't kill a thread; you can only stop waiting for it.

    Tools: pool.submit(...).result(timeout=...), concurrent.futures.TimeoutError
           (imported here as FutureTimeoutError; in 3.10 it is NOT the builtin
           TimeoutError), pool.shutdown(wait=False) in a finally
    """
    raise NotImplementedError


def producer_consumer(items: list, handle, n_consumers: int = 3) -> list:
    """ex08. One producer thread puts every item on a queue.Queue. n_consumers consumer
    threads each loop: take an item, append handle(item) to a shared results list.
    When the producer is done it puts ONE sentinel per consumer so every consumer
    exits its loop. Join everything and return the results (any order).

    producer_consumer([1, 2, 3], lambda x: x * 10, n_consumers=2) -> [10, 20, 30] in some order

    With handle sleeping 0.05s, 9 items across 3 consumers must take < 0.35s.
    Forget a sentinel and a consumer blocks on q.get() forever (the test gives up
    after 2s and tells you).

    Tools: queue.Queue(), q.put(x), q.get() (blocks), a unique sentinel like
           `_DONE = object()` (None works if None is never a real item),
           `while (item := q.get()) is not _DONE:`
    """
    raise NotImplementedError


class Ticker:
    """ex09. A background thread that calls on_tick() immediately on start(), then
    again every `interval` seconds, until stop() is called.

    t = Ticker(interval=5.0, on_tick=lambda: print("tick"))
    t.start()     # prints "tick" right away
    t.stop()      # must return almost instantly, NOT after the 5s sleep finishes
    t.running     # False once stopped

    stop() sets a threading.Event and joins the thread. The loop waits with
    event.wait(interval), which returns early (True) the moment the event is set.
    time.sleep(interval) can't be interrupted, so stop() would hang for up to 5s.

    Tools: threading.Event(), ev.set(), ev.is_set(), ev.wait(timeout) -> bool,
           threading.Thread(target=self._run, daemon=True)
    """

    def __init__(self, interval: float, on_tick):
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    @property
    def running(self) -> bool:
        raise NotImplementedError


async def gather_settled(urls: list[str], fetch) -> dict[str, object]:
    """ex10. Like ex04 but failures don't sink the batch. Run every `await fetch(url)`
    concurrently and return {url: result or exception instance}.

    With fetch raising KeyError for "bad":
    asyncio.run(gather_settled(["a", "bad"], fetch)) -> {"a": "A", "bad": KeyError("bad")}

    Without return_exceptions, gather raises the FIRST error and you lose every result.

    Tools: asyncio.gather(*coros, return_exceptions=True), dict(zip(...))
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

async def bounded_fetch(urls: list[str], fetch, limit: int) -> list:
    """ex11. Fetch every url concurrently (await fetch(url)) but never with more than
    `limit` fetches in flight at once. Results in input order.

    The test's fake fetch records how many calls overlap. With 10 urls and limit=3
    it must see exactly 3 in flight at the peak: not 10 (no limit) and not 1
    (accidentally sequential).

    Tools: asyncio.Semaphore(limit), an inner `async def one(url):` that does
           `async with sem: return await fetch(url)`, then gather
    """
    raise NotImplementedError


async def retry(op, attempts: int = 3, timeout: float = 1.0, base_delay: float = 0.1,
                sleep=asyncio.sleep):
    """ex12. Retry an async operation with a per-attempt timeout and exponential backoff.

    op is a zero-argument async FUNCTION. Call op() fresh on every attempt: a
    coroutine object can only be awaited once.
    Each attempt: `await asyncio.wait_for(op(), timeout)`.
    If it raises anything (including the timeout), and attempts remain, wait
    base_delay * 2**i  (0.1, 0.2, 0.4, ...) using the injected `sleep`, then retry.
    After the last attempt, re-raise its exception. No sleep after the final failure.

    op fails, fails, then returns "ok"  -> "ok", sleep called with 0.1 then 0.2
    op always raises ValueError         -> ValueError, sleep called with 0.1 then 0.2
    op hangs forever (timeout=0.05)     -> asyncio.TimeoutError after 3 attempts

    `sleep` is injected so tests can record the delays without actually waiting.

    Tools: asyncio.wait_for(coro, timeout) raises asyncio.TimeoutError (3.10: not
           the builtin TimeoutError), `except Exception as e:`, bare `raise` re-raises
    """
    raise NotImplementedError


async def run_worker_pool(jobs: list, handle, n_workers: int) -> list:
    """ex13. Process jobs with a fixed pool of n_workers worker tasks fed by an
    asyncio.Queue. handle is async: `await handle(job)`.

    Return a list aligned with jobs: results[i] is handle(jobs[i])'s result, or the
    exception instance if it raised (one bad job must not kill its worker).
    At most n_workers jobs run at once (the test measures it).
    When this returns, no worker task may still be pending: cancel the workers
    after the queue drains AND await them, otherwise they're left dangling.

    asyncio.run(run_worker_pool([1, 2, 3], double, n_workers=2)) -> [2, 4, 6]

    Tools: q = asyncio.Queue(); q.put_nowait((i, job)); worker loop:
           `i, job = await q.get()` ... `q.task_done()` in a finally;
           asyncio.create_task(worker()); await q.join(); task.cancel();
           await asyncio.gather(*workers, return_exceptions=True)
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
