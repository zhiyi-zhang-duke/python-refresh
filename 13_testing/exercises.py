"""13 - Testing

Fill in each function, then run:   python 13_testing/exercises.py
Run just one exercise:             python 13_testing/exercises.py 4
Run exercise 4 onward:             python 13_testing/exercises.py 4+

Exercises go from easy (01) to advanced (13). Delete the `raise NotImplementedError`
line when you start one.

HOW THESE ARE GRADED. Most exercises flip the usual script: you write the TESTS.
A `check_xxx(impl)` function receives an implementation and asserts it behaves to spec
(plain `assert`, or harness-free helpers you write; any exception = a failed check).
The grader runs your checks against:
  1. a correct implementation      -> your checks must PASS
  2. several realistic buggy ones  -> your checks must FAIL on each
A buggy version your checks pass on "survived": the failure message names it.
That is mutation testing, and it's the honest measure of a test suite.

pytest may not be installed, so this topic uses unittest, unittest.mock and plain
assert. The README shows the pytest spelling side by side.
"""

import io
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, call, patch


# ---------------------------------------------------------------- easy ----

def check_slugify(slugify):
    """ex01. Write asserts that pin down this spec for slugify(text) -> str:

        - lowercase everything
        - every run of characters that are NOT a-z or 0-9 becomes a single "-"
        - no leading or trailing "-"

        slugify("Hello, World!")      -> "hello-world"
        slugify("  Python 3.10  ")    -> "python-3-10"
        slugify("")                   -> ""

    5 buggy slugifiers are waiting. Think: case, both ends, runs of junk, digits.

    Tools: assert slugify("...") == "...", f"helpful message"
    """
    raise NotImplementedError


def check_overlaps(overlaps):
    """ex02. overlaps(a, b) -> bool for half-open intervals [start, end), given as
    (start, end) tuples of ints. Two meetings overlap if they share any moment.
    Touching is NOT overlapping: (9, 10) and (10, 11) are back-to-back meetings.

        overlaps((9, 11), (10, 12)) -> True
        overlaps((9, 10), (10, 11)) -> False

    Write asserts that catch 4 buggy versions. Booking bugs live at boundaries and
    in argument order: whatever you check as overlaps(a, b), also check overlaps(b, a).
    Draw the cases: disjoint, touching, partial overlap, one inside the other, identical.

    Tools: a list of (a, b, expected) rows and a for loop
    """
    raise NotImplementedError


class StackTests(unittest.TestCase):
    """ex03. Write a unittest.TestCase for a Stack class with this spec:

        s = Stack()
        s.push(x)         add to the top
        s.pop()           remove and return the top; IndexError if empty
        s.peek()          return the top WITHOUT removing it; IndexError if empty
        len(s)            number of items
        s.is_empty()      True if no items

    Rules:
      - setUp builds a fresh stack:  self.stack = self.stack_class()
        (the grader sets stack_class to the correct Stack, then to 5 buggy ones)
      - at least 4 test_ methods, each testing ONE behavior, named for it
      - use self.assertEqual / assertTrue / assertFalse / assertRaises, not bare assert
        (they print both values on failure)

    Tools: `with self.assertRaises(IndexError): self.stack.pop()`
    """

    stack_class = None  # injected by the grader

    def setUp(self):
        raise NotImplementedError

    def test_push_then_pop_returns_item(self):
        raise NotImplementedError


def check_send_welcome(send_welcome):
    """ex04. send_welcome(user, mailer) -> message id. Spec:

        - if user.email is empty/None: raise ValueError and DON'T touch the mailer
        - otherwise call exactly once, with keyword args:
              mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")
        - return whatever mailer.send returned (the message id)

    The mailer is a dependency you don't own (it sends real email), so use a Mock:
    it accepts any call, records it, and returns what you configure.

        mailer = Mock()
        mailer.send.return_value = "msg-123"
        user = SimpleNamespace(name="Ada", email="ada@example.com")

    6 buggy versions. Check the return value AND exactly how send was called.

    Tools: mock.send.assert_called_once_with(to=..., subject=..., body=...),
           mock.send.assert_not_called(), mock.send.call_count,
           try/except ValueError (or a small helper) to assert something raises
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def check_fetch_with_retry(fetch_with_retry):
    """ex05. fetch_with_retry(fetch, url, attempts=3). Spec:

        - call fetch(url); return the first successful result
        - on ConnectionError, try again, up to `attempts` calls in TOTAL
        - if every attempt raised ConnectionError, re-raise the last one
        - any other exception (e.g. ValueError) propagates immediately, no retry

    Drive it with a Mock whose side_effect is a LIST: each call consumes the next
    element; an exception CLASS or INSTANCE in the list is raised, anything else is returned.

        fetch = Mock(side_effect=[ConnectionError(), ConnectionError(), "page"])
        fetch_with_retry(fetch, "u")   -> "page", and fetch.call_count == 3

    5 buggy versions: count calls exactly, check both "succeeds on the last allowed
    try" and "gives up after exactly N tries".

    Tools: Mock(side_effect=[...]), m.call_count, m.assert_called_with("u"),
           m.call_args_list == [call("u")] * 3
    """
    raise NotImplementedError


def check_greeting(clock):
    """ex06. `clock` is a module-like object with two functions:

        clock.now()        -> datetime   (the real current time)
        clock.greeting()   -> str, based on clock.now().hour:
            5 <= hour < 12   "Good morning"
            12 <= hour < 18  "Good afternoon"
            otherwise        "Good evening"     (including 0:00-4:59)

    Your checks must give the same answer at 9am or 11pm, so replace the clock:

        with patch.object(clock, "now", return_value=datetime(2026, 1, 1, 9, 0)):
            assert clock.greeting() == "Good morning"

    patch.object swaps the attribute for a MagicMock inside the `with` and restores
    it on exit (the grader checks that it was restored). 4 buggy versions: test every
    boundary hour, on both sides.

    Tools: patch.object(target, "attr_name", return_value=...) as a context manager;
           a for loop over (hour, expected) with one `with` per row
    """
    raise NotImplementedError


class GradeTests(unittest.TestCase):
    """ex07. Table-driven tests with subTest for letter_grade(score) -> str:

        90-100 "A",  80-89 "B",  70-79 "C",  60-69 "D",  0-59 "F"
        score < 0 or score > 100 -> ValueError

    Call it as self.letter_grade(score) (the grader injects the function).
    Rules:
      - one test method loops over a table of (score, expected) rows, each case
        inside `with self.subTest(score=score):` so ALL failures are reported,
        not just the first
      - a second test method uses self.assertRaises for out-of-range scores
      - 4 buggy versions: the table needs every boundary (both sides of each cutoff)

    Tools: `for score, want in CASES:` / `with self.subTest(score=score):` /
           self.assertEqual(self.letter_grade(score), want)
    """

    letter_grade = None  # injected by the grader

    def test_table(self):
        raise NotImplementedError


@dataclass(frozen=True)
class Booking:
    """Provided. Value object stored by the repo in ex08."""
    id: str
    room_id: str
    start: int
    end: int


class InMemoryBookingRepo:
    """ex08. Write a FAKE: a small, real, in-memory implementation of the storage
    interface a BookingService depends on. The grader runs the real service on it.

        repo.add(booking)         store it; ValueError if that id is already stored
        repo.get(booking_id)      the Booking, or None
        repo.for_room(room_id)    that room's bookings sorted by start, as a NEW list
                                  (callers mutating it must not change the repo)
        repo.delete(booking_id)   True if it existed and was removed, else False

    Fake vs mock: a Mock repo would make you script every return value and assert
    on calls (`repo.add.assert_called_once_with(...)`), which breaks whenever the
    service is refactored. A fake keeps real state, so tests assert on OUTCOMES
    ("after cancel, the slot is bookable again"). Use mocks for things you can't run
    (email, payments, clocks); use fakes for storage you own.

    Trap: storage must be created in __init__. A dict at class level is shared by
    every instance, so one test's bookings leak into the next.

    Tools: a dict {id: Booking}, sorted(..., key=lambda b: b.start), dict.pop(k, None)
    """

    def __init__(self):
        raise NotImplementedError

    def add(self, booking: Booking) -> None:
        raise NotImplementedError

    def get(self, booking_id: str) -> Booking | None:
        raise NotImplementedError

    def for_room(self, room_id: str) -> list[Booking]:
        raise NotImplementedError

    def delete(self, booking_id: str) -> bool:
        raise NotImplementedError


def check_print_report(print_report):
    """ex09. print_report(rows, out=None) writes a report to the stream `out`
    (sys.stdout when out is None). rows is a list of (name, qty). Exact output:

        print_report([("apple", 3), ("pear", 10)], out)  writes  "apple: 3\\npear: 10\\ntotal: 13\\n"
        print_report([], out)                            writes  "(no rows)\\n"

    Every line ends with "\\n". Rows keep their input order.
    Capture the output by passing an io.StringIO as `out`, then compare the whole
    string with ==. 5 buggy versions, one of which ignores `out` entirely.

    Tools: buf = io.StringIO(); print_report(rows, buf); buf.getvalue()
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def check_merge_intervals(merge_intervals):
    """ex10. merge_intervals(intervals) -> list of (start, end) tuples. Spec:

        - closed intervals: (1, 3) and (3, 5) DO merge into (1, 5)
        - input may be in any order; output is sorted by start
        - must NOT modify the caller's list
        - [] -> []

        merge_intervals([(8, 10), (1, 3), (2, 6)]) -> [(1, 6), (8, 10)]

    5 buggy versions. Besides boundaries and ordering, think about a short interval
    sitting inside a long one, a lone interval at the end, and checking the INPUT
    list after the call.

    Tools: before = list(data); merge_intervals(data); assert data == before
    """
    raise NotImplementedError


def check_lru_cache(LRUCache):
    """ex11. LRUCache(capacity), the Ode-onsite favorite. Spec:

        LRUCache(0)         ValueError (capacity must be >= 1)
        c.get(key)          the value, or None if missing. A hit makes key most recent.
        c.put(key, value)   insert or update; either way key becomes most recent.
                            If that pushes size OVER capacity, evict the least recent.
        len(c)              number of entries

        c = LRUCache(2); c.put("a", 1); c.put("b", 2)
        c.get("a")          -> 1             ("b" is now least recent)
        c.put("c", 3)       evicts "b"
        c.get("b")          -> None

    7 buggy versions. Write it the way you would in the room: one small scenario per
    behavior (a helper `def fresh(): return LRUCache(2)` keeps them independent).
    Use `is None` for the missing-key check, never `== None`.

    Tools: assert ..., a helper to assert ValueError is raised
    """
    raise NotImplementedError


def check_rate_limiter(RateLimiter):
    """ex12. RateLimiter(limit, window, clock=time.monotonic). Sliding window:

        rl.allow(key) -> bool
            True if fewer than `limit` ALLOWED requests for this key happened in
            the last `window` seconds, i.e. at times t with now - t < window.
            A request exactly `window` seconds old no longer counts.
            Denied requests are not recorded. Each key has its own limit.

    clock is a zero-arg callable returning seconds. Never sleep in a test: inject a
    fake clock you can move by hand.

        now = [0.0]
        rl = RateLimiter(limit=2, window=10, clock=lambda: now[0])
        rl.allow("k"), rl.allow("k"), rl.allow("k")   -> True, True, False
        now[0] = 10.0
        rl.allow("k")                                 -> True

    6 buggy versions. Probe the exact boundary (9.999 vs 10), separate keys, and what
    happens after a denied request once time moves on.

    Tools: a FakeClock class with __call__ and an advance(seconds) method, or a
           one-element list + lambda as above
    """
    raise NotImplementedError


class PriorityQueue:
    """ex13. TDD it. Write check_priority_queue (below) and this class TOGETHER, one
    red -> green step at a time: add the next check, run, watch it fail on the assert
    (not on an AttributeError or typo), write the smallest code that passes, repeat.

    Step 1  pop() on an empty queue raises IndexError
    Step 2  push("a", 5) then pop() returns "a"
    Step 3  the LOWEST priority number pops first
    Step 4  equal priorities pop in insertion order (FIFO), whatever the items are
    Step 5  len(pq); peek() returns the next item without removing it (IndexError if empty)
    -- requirement change, mid-session, the way the interviewer will do it --
    Step 6  update(item, new_priority) re-prioritizes an item already in the queue.
            KeyError if the item isn't there. An updated item breaks ties as if it
            were pushed just now. len() doesn't change.

    Items are hashable (strings in the tests) and each item is in the queue at most once.

    Tools: heapq.heappush/heappop on [priority, counter, item, alive] lists;
           itertools.count() for the counter; for step 6, mark the old entry dead
           and push a new one (lazy deletion), keeping {item: entry} to find it.
           A plain list + min() is also fine: get it green, then make it fast.
    """

    def __init__(self):
        raise NotImplementedError

    def push(self, item, priority: int) -> None:
        raise NotImplementedError

    def pop(self):
        raise NotImplementedError

    def peek(self):
        raise NotImplementedError

    def update(self, item, priority: int) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


def check_priority_queue(PriorityQueue):
    """ex13 (part 2). Your checks for the spec above, grown one step at a time.
    The grader runs them against a correct queue, 7 buggy ones, and YOUR class.
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
