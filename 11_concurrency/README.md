# 11 - Concurrency

```bash
python 11_concurrency/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `run_in_threads` | easy | `Thread`, `start`/`join`, results by slot |
| 02 | `Counter` | easy | `threading.Lock`, lost-update race |
| 03 | `parallel_fetch` | easy | `ThreadPoolExecutor.map` |
| 04 | `fetch_all_async` | easy | `async def`, `await`, `asyncio.gather` |
| 05 | `BookingService` | medium | lock around check-then-insert |
| 06 | `fetch_as_completed` | medium | `submit`, `as_completed`, `fut.exception()` |
| 07 | `call_with_timeout` | medium | `result(timeout=)`, `shutdown(wait=False)` |
| 08 | `producer_consumer` | medium | `queue.Queue`, one sentinel per consumer |
| 09 | `Ticker` | medium | `threading.Event` for prompt shutdown |
| 10 | `gather_settled` | medium | `gather(return_exceptions=True)` |
| 11 | `bounded_fetch` | advanced | `asyncio.Semaphore` |
| 12 | `retry` | advanced | `asyncio.wait_for`, backoff, injected sleep |
| 13 | `run_worker_pool` | advanced | `asyncio.Queue` workers, `join`, cancel cleanly |

## Threads vs processes vs asyncio (and the GIL)

The GIL lets only one thread run Python bytecode at a time. It is released during
blocking I/O (sockets, files, `time.sleep`) and inside many C extensions (numpy, hashlib).

| Work | Use | Why |
|---|---|---|
| Blocking I/O, sync libraries (`requests`, DB drivers) | `ThreadPoolExecutor` | GIL is released while waiting; threads overlap the waits |
| Lots of I/O with async libraries (`httpx`, `aiohttp`) | `asyncio` | one thread, thousands of cheap tasks, switches only at `await` |
| CPU-bound pure Python | `ProcessPoolExecutor` / `multiprocessing` | separate interpreters, separate GILs, real parallel cores |

- The GIL does NOT make your code thread-safe. `x += 1` is read, add, write: a thread
  switch can land between them (ex02). Lock any read-modify-write on shared state.
- asyncio can't be preempted mid-statement, but anything with an `await` between the
  check and the act races exactly like threads (use `asyncio.Lock`).
- One blocking call (`time.sleep`, `requests.get`) inside `async def` freezes the
  whole event loop. Use `await asyncio.sleep`, or `await asyncio.to_thread(fn, *args)`.
- Processes: arguments and results are pickled; on Windows the main module is
  re-imported in each child, so guard with `if __name__ == "__main__":`.
- In Go terms: a goroutine is closest to an asyncio task (cheap, cooperative from your
  point of view), a channel is `queue.Queue` / `asyncio.Queue`, a `sync.WaitGroup`
  is `join()` / `gather` / `q.join()`, `context.WithTimeout` is `wait_for`.

## Cheat sheet

### threading

```python
import threading

t = threading.Thread(target=work, args=(1, "x"), daemon=True)  # args is a TUPLE: (x,) for one
t.start()
t.join(timeout=2.0)       # returns None either way; check t.is_alive() to know if it finished
# No return value: write into a list slot / dict / queue. Start ALL threads, then join all.
# daemon=True: killed when the main thread exits. Non-daemon threads keep the process alive.

lock = threading.Lock()
with lock:                # acquire/release, even on exceptions
    balance = balance + amount
# Lock is NOT reentrant: acquiring it twice in one thread deadlocks. RLock is reentrant.
# Hold it across the whole check-then-act; locking only the write still races.

ev = threading.Event()
ev.set(); ev.clear(); ev.is_set()
ev.wait(5.0)              # True if set, False on timeout. Interruptible, unlike time.sleep

gate = threading.Barrier(8)   # all 8 threads block in gate.wait() until the 8th arrives
```

The double-booking race (ex05), and the fix:

```python
def book(self, room, start, end):
    with self._lock:                                    # one atomic step
        if any(start < e and s < end for s, e in self._rooms[room]):
            return False                                # check ...
        self._rooms[room].append((start, end))          # ... then act
        return True
# With a real DB: a unique/exclusion constraint makes the INSERT itself the check,
# or SELECT ... FOR UPDATE inside a transaction. A Python lock only covers one process.
```

### queue.Queue

```python
import queue
q = queue.Queue(maxsize=0)    # 0 = unbounded; maxsize=N makes put() block (backpressure)
q.put(item); q.get()          # both block; get(timeout=1) raises queue.Empty
q.put_nowait(x); q.get_nowait()
q.task_done(); q.join()       # join waits until every put has a matching task_done

_DONE = object()              # unique sentinel; put ONE per consumer
while (item := q.get()) is not _DONE:
    handle(item)
```

### concurrent.futures

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError   # != builtin TimeoutError before 3.11

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(fetch, urls))      # input order; re-raises the first error when you reach it

    futs = {pool.submit(fetch, u): u for u in urls}
    for f in as_completed(futs, timeout=10):   # completion order
        url = futs[f]
        if f.exception() is not None:          # exception() returns it; result() re-raises it
            ...
        else:
            value = f.result()

f.result(timeout=0.5)     # raises FutureTimeoutError; the task keeps running anyway
f.cancel()                # only works if it hasn't started
# `with` exits via shutdown(wait=True): it blocks until every task finishes.
# To abandon a stuck task: pool.shutdown(wait=False)  (3.9+: cancel_futures=True drops queued ones)
```

### asyncio

```python
import asyncio

async def fetch(url):           # calling fetch(url) returns a coroutine; nothing runs yet
    await asyncio.sleep(0.1)    # NEVER time.sleep in async code
    return url

asyncio.run(main())             # entry point: makes a loop, runs main(), closes the loop

# Sequential vs concurrent
a = await fetch("a"); b = await fetch("b")                 # one after another
a, b = await asyncio.gather(fetch("a"), fetch("b"))        # together, results in arg order
res = await asyncio.gather(*coros, return_exceptions=True) # errors come back as values

task = asyncio.create_task(fetch("a"))   # starts running at the next await
task.cancel(); await asyncio.gather(task, return_exceptions=True)   # cancel, then let it land
# Keep a reference to tasks you create; an unreferenced task can be garbage collected.

await asyncio.wait_for(fetch("a"), timeout=1.0)   # raises asyncio.TimeoutError (3.10), cancels the inner
# asyncio.timeout() context manager and TaskGroup are 3.11+: not in 3.10.

sem = asyncio.Semaphore(5)
async with sem:                  # at most 5 inside at once
    ...

lock = asyncio.Lock()            # same check-then-act rule as threads, across awaits

q = asyncio.Queue()
await q.put(x); x = await q.get(); q.task_done(); await q.join()

await asyncio.to_thread(blocking_fn, arg)   # run sync code without freezing the loop (3.9+)
```

Gotchas:

- A coroutine object can be awaited once. To retry, keep the *function* and call it again.
- `except Exception` doesn't catch `asyncio.CancelledError` (a `BaseException` since 3.8),
  so cancellation still propagates. If you catch it, re-raise it.
- `asyncio.run` can't be called from inside a running loop (Jupyter has one; use `await`).
- Create `asyncio.Semaphore`/`Lock`/`Queue` inside the coroutine that uses them. Before 3.10
  they bound to whatever loop existed at construction, which broke across `asyncio.run` calls.
- Windows `time.sleep(0.01)` actually sleeps ~15ms (timer resolution). Don't write tests
  that need tighter timing than that.
