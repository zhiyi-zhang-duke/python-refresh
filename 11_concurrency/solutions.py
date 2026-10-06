"""11 - Concurrency: reference solutions.   Check them:  python 11_concurrency/solutions.py"""

import asyncio
import queue
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError


# ---------------------------------------------------------------- easy ----

def run_in_threads(fn, args: list) -> list:
    results = [None] * len(args)

    def work(i, arg):
        results[i] = fn(arg)  # each thread owns one slot, so no lock needed

    threads = [threading.Thread(target=work, args=(i, arg)) for i, arg in enumerate(args)]
    for t in threads:
        t.start()
    for t in threads:  # start ALL before joining any, or you're back to sequential
        t.join()
    return results


class Counter:
    def __init__(self, pause=lambda: None):
        self._value = 0
        self._pause = pause
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            current = self._value
            self._pause()
            self._value = current + 1

    @property
    def value(self) -> int:
        return self._value


def parallel_fetch(urls: list[str], fetch, max_workers: int = 8) -> dict[str, object]:
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return dict(zip(urls, pool.map(fetch, urls)))


async def fetch_all_async(urls: list[str], fetch) -> list:
    return await asyncio.gather(*(fetch(u) for u in urls))


# -------------------------------------------------------------- medium ----

class BookingService:
    def __init__(self, pause=lambda: None):
        self._pause = pause
        self._lock = threading.Lock()  # one global lock; per-room locks would scale better
        self._rooms: dict[str, list[tuple[int, int]]] = defaultdict(list)

    def book(self, room: str, start: int, end: int) -> bool:
        # The check and the insert must be ONE atomic step. Locking only the insert
        # still lets two threads both pass the check.
        with self._lock:
            if any(start < e and s < end for s, e in self._rooms[room]):
                return False
            self._pause()
            self._rooms[room].append((start, end))
            return True

    def bookings(self, room: str) -> list[tuple[int, int]]:
        with self._lock:
            return sorted(self._rooms.get(room, []))


def fetch_as_completed(urls: list[str], fetch, max_workers: int = 8) -> list[tuple[str, object]]:
    out = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch, u): u for u in urls}
        for fut in as_completed(futures):
            err = fut.exception()
            out.append((futures[fut], err if err is not None else fut.result()))
    return out


def call_with_timeout(fn, timeout: float, *args) -> tuple[bool, object]:
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        return True, pool.submit(fn, *args).result(timeout=timeout)
    except FutureTimeoutError:
        return False, None
    finally:
        pool.shutdown(wait=False)  # don't block on the stuck thread; it finishes on its own


_DONE = object()


def producer_consumer(items: list, handle, n_consumers: int = 3) -> list:
    q: queue.Queue = queue.Queue()
    results = []
    lock = threading.Lock()  # list.append is atomic in CPython, but say what you mean

    def produce():
        for item in items:
            q.put(item)
        for _ in range(n_consumers):
            q.put(_DONE)

    def consume():
        while (item := q.get()) is not _DONE:
            r = handle(item)
            with lock:
                results.append(r)

    threads = [threading.Thread(target=produce)]
    threads += [threading.Thread(target=consume) for _ in range(n_consumers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


class Ticker:
    def __init__(self, interval: float, on_tick):
        self._interval = interval
        self._on_tick = on_tick
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._on_tick()
            # wait() returns True as soon as stop() sets the event: no stuck sleep
            if self._stop.wait(self._interval):
                break

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


async def gather_settled(urls: list[str], fetch) -> dict[str, object]:
    results = await asyncio.gather(*(fetch(u) for u in urls), return_exceptions=True)
    return dict(zip(urls, results))


# ------------------------------------------------------------ advanced ----

async def bounded_fetch(urls: list[str], fetch, limit: int) -> list:
    sem = asyncio.Semaphore(limit)  # create it inside the running loop

    async def one(url):
        async with sem:
            return await fetch(url)

    return await asyncio.gather(*(one(u) for u in urls))


async def retry(op, attempts: int = 3, timeout: float = 1.0, base_delay: float = 0.1,
                sleep=asyncio.sleep):
    for i in range(attempts):
        try:
            return await asyncio.wait_for(op(), timeout)
        except Exception:  # CancelledError is a BaseException, so cancellation still escapes
            if i == attempts - 1:
                raise
            await sleep(base_delay * 2 ** i)


async def run_worker_pool(jobs: list, handle, n_workers: int) -> list:
    q: asyncio.Queue = asyncio.Queue()
    for i, job in enumerate(jobs):
        q.put_nowait((i, job))
    results: list = [None] * len(jobs)

    async def worker():
        while True:
            i, job = await q.get()
            try:
                results[i] = await handle(job)
            except Exception as e:  # record it; the worker lives on
                results[i] = e
            finally:
                q.task_done()

    workers = [asyncio.create_task(worker()) for _ in range(n_workers)]
    await q.join()  # every put has a matching task_done
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)  # let the cancellations land
    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
