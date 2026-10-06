"""13 - Testing: reference solutions.   Check them:  python 13_testing/solutions.py"""

import io
import itertools
import heapq
import unittest
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, call, patch


def _raises(exc_type, fn, *args, **kwargs):
    """Tiny pytest.raises stand-in: assert fn(...) raises exc_type, return the exception."""
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        return e
    raise AssertionError(f"expected {exc_type.__name__}, nothing was raised")


# ---------------------------------------------------------------- easy ----

def check_slugify(slugify):
    cases = [
        ("Hello, World!", "hello-world"),     # case + punctuation run
        ("  Python 3.10  ", "python-3-10"),   # digits kept, both ends trimmed
        ("--already-slugged--", "already-slugged"),
        ("a   b", "a-b"),                     # a run collapses to ONE dash
        ("a.-_b", "a-b"),
        ("ABC", "abc"),
        ("!!!", ""),
        ("", ""),
    ]
    for text, want in cases:
        got = slugify(text)
        assert got == want, f"slugify({text!r}) = {got!r}, want {want!r}"


def check_overlaps(overlaps):
    cases = [
        ((9, 11), (10, 12), True),    # partial
        ((9, 10), (10, 11), False),   # touching
        ((9, 10), (11, 12), False),   # disjoint
        ((9, 17), (10, 11), True),    # containment
        ((9, 10), (9, 10), True),     # identical
    ]
    for a, b, want in cases:
        # check both argument orders: overlap is symmetric, implementations often aren't
        assert overlaps(a, b) is want, f"overlaps({a}, {b}) should be {want}"
        assert overlaps(b, a) is want, f"overlaps({b}, {a}) should be {want}"


class StackTests(unittest.TestCase):
    stack_class = None  # injected by the grader

    def setUp(self):
        self.stack = self.stack_class()

    def test_push_then_pop_returns_item(self):
        self.stack.push(1)
        self.assertEqual(self.stack.pop(), 1)

    def test_pop_is_lifo(self):
        for x in (1, 2, 3):
            self.stack.push(x)
        self.assertEqual([self.stack.pop() for _ in range(3)], [3, 2, 1])

    def test_pop_empty_raises(self):
        with self.assertRaises(IndexError):
            self.stack.pop()

    def test_peek_does_not_remove(self):
        self.stack.push("a")
        self.stack.push("b")
        self.assertEqual(self.stack.peek(), "b")
        self.assertEqual(len(self.stack), 2)

    def test_peek_empty_raises(self):
        with self.assertRaises(IndexError):
            self.stack.peek()

    def test_len_and_is_empty_track_push_and_pop(self):
        self.assertTrue(self.stack.is_empty())
        self.stack.push(1)
        self.stack.push(2)
        self.assertEqual(len(self.stack), 2)
        self.stack.pop()
        self.stack.pop()
        self.assertEqual(len(self.stack), 0)
        self.assertTrue(self.stack.is_empty())


def check_send_welcome(send_welcome):
    mailer = Mock()
    mailer.send.return_value = "msg-123"
    user = SimpleNamespace(name="Ada", email="ada@example.com")

    assert send_welcome(user, mailer) == "msg-123", "should return mailer.send's result"
    mailer.send.assert_called_once_with(to="ada@example.com", subject="Welcome!", body="Hi Ada")

    for missing in ("", None):
        mailer = Mock()
        _raises(ValueError, send_welcome, SimpleNamespace(name="Bob", email=missing), mailer)
        mailer.send.assert_not_called()  # validate BEFORE the side effect


# -------------------------------------------------------------- medium ----

def check_fetch_with_retry(fetch_with_retry):
    fetch = Mock(return_value="page")
    assert fetch_with_retry(fetch, "u") == "page"
    fetch.assert_called_once_with("u")

    # succeeds on the LAST allowed attempt
    fetch = Mock(side_effect=[ConnectionError(), ConnectionError(), "page"])
    assert fetch_with_retry(fetch, "u", attempts=3) == "page"
    assert fetch.call_args_list == [call("u")] * 3

    # gives up after EXACTLY `attempts` calls and re-raises
    fetch = Mock(side_effect=ConnectionError("down"))  # a single exception: raised every call
    _raises(ConnectionError, fetch_with_retry, fetch, "u", attempts=3)
    assert fetch.call_count == 3, f"expected 3 attempts, got {fetch.call_count}"

    # non-network errors are not retried
    fetch = Mock(side_effect=[ValueError("bad"), "page"])
    _raises(ValueError, fetch_with_retry, fetch, "u")
    assert fetch.call_count == 1


def check_greeting(clock):
    cases = [
        (4, "Good evening"), (5, "Good morning"), (11, "Good morning"),
        (12, "Good afternoon"), (17, "Good afternoon"), (18, "Good evening"),
        (23, "Good evening"), (0, "Good evening"),
    ]
    for hour, want in cases:
        with patch.object(clock, "now", return_value=datetime(2026, 1, 1, hour, 30)):
            got = clock.greeting()
        assert got == want, f"at {hour}:30 got {got!r}, want {want!r}"


class GradeTests(unittest.TestCase):
    letter_grade = None  # injected by the grader

    CASES = [
        (100, "A"), (90, "A"), (89, "B"), (80, "B"), (79, "C"),
        (70, "C"), (69, "D"), (60, "D"), (59, "F"), (0, "F"),
    ]

    def test_table(self):
        for score, want in self.CASES:
            with self.subTest(score=score):  # each failing row is reported separately
                self.assertEqual(self.letter_grade(score), want)

    def test_out_of_range_raises(self):
        for score in (-1, 101):
            with self.subTest(score=score), self.assertRaises(ValueError):
                self.letter_grade(score)


@dataclass(frozen=True)
class Booking:
    id: str
    room_id: str
    start: int
    end: int


class InMemoryBookingRepo:
    def __init__(self):
        self._by_id: dict[str, Booking] = {}  # per instance, never at class level

    def add(self, booking: Booking) -> None:
        if booking.id in self._by_id:
            raise ValueError(f"duplicate booking id {booking.id}")
        self._by_id[booking.id] = booking

    def get(self, booking_id: str) -> Booking | None:
        return self._by_id.get(booking_id)

    def for_room(self, room_id: str) -> list[Booking]:
        # sorted() always builds a new list, so callers can't mutate our state
        return sorted((b for b in self._by_id.values() if b.room_id == room_id),
                      key=lambda b: b.start)

    def delete(self, booking_id: str) -> bool:
        return self._by_id.pop(booking_id, None) is not None


def check_print_report(print_report):
    buf = io.StringIO()
    print_report([("apple", 3), ("pear", 10)], buf)
    assert buf.getvalue() == "apple: 3\npear: 10\ntotal: 13\n", repr(buf.getvalue())

    buf = io.StringIO()
    print_report([("zucchini", 1), ("apple", 2)], buf)
    assert buf.getvalue() == "zucchini: 1\napple: 2\ntotal: 3\n", repr(buf.getvalue())

    buf = io.StringIO()
    print_report([], buf)
    assert buf.getvalue() == "(no rows)\n", repr(buf.getvalue())


# ------------------------------------------------------------ advanced ----

def check_merge_intervals(merge_intervals):
    cases = [
        ([], []),
        ([(1, 3)], [(1, 3)]),
        ([(8, 10), (1, 3), (2, 6)], [(1, 6), (8, 10)]),   # unsorted input
        ([(1, 3), (3, 5)], [(1, 5)]),                     # touching merges
        ([(1, 10), (2, 3)], [(1, 10)]),                   # nested: keep the max end
        ([(1, 2), (4, 5), (7, 8)], [(1, 2), (4, 5), (7, 8)]),   # last one must survive
    ]
    for data, want in cases:
        before = list(data)
        got = merge_intervals(data)
        assert got == want, f"merge_intervals({before}) = {got}, want {want}"
        assert data == before, f"input was mutated: {before} -> {data}"


def check_lru_cache(LRUCache):
    def fresh():
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        return c

    _raises(ValueError, LRUCache, 0)

    c = LRUCache(2)
    assert c.get("missing") is None
    assert len(c) == 0

    c = fresh()  # holds exactly `capacity` without evicting
    assert len(c) == 2 and c.get("a") == 1 and c.get("b") == 2

    c = fresh()  # overflow evicts the least recent
    c.put("c", 3)
    assert c.get("a") is None and c.get("b") == 2 and c.get("c") == 3

    c = fresh()  # get refreshes
    c.get("a")
    c.put("c", 3)
    assert c.get("b") is None and c.get("a") == 1

    c = fresh()  # updating an existing key at capacity evicts nothing
    c.put("b", 20)  # update the NEWER key: a size check done before the key lookup evicts "a"
    assert len(c) == 2 and c.get("a") == 1 and c.get("b") == 20

    c = fresh()  # put on an existing key refreshes it
    c.put("a", 10)
    c.put("c", 3)
    assert c.get("a") == 10 and c.get("b") is None


class FakeClock:
    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def check_rate_limiter(RateLimiter):
    clock = FakeClock()
    rl = RateLimiter(limit=2, window=10, clock=clock)
    assert [rl.allow("k"), rl.allow("k"), rl.allow("k")] == [True, True, False]
    assert rl.allow("other") is True, "keys have separate limits"

    clock.advance(9.999)
    assert rl.allow("k") is False, "still inside the window"
    clock.t = 10.0
    assert rl.allow("k") is True, "a request exactly `window` old no longer counts"
    assert rl.allow("k") is True, "denied requests must not be recorded"
    assert rl.allow("k") is False


def check_priority_queue(PriorityQueue):
    # step 1
    pq = PriorityQueue()
    _raises(IndexError, pq.pop)
    # step 2
    pq.push("a", 5)
    assert pq.pop() == "a"
    # step 3
    for item, pri in [("mid", 5), ("low", 1), ("high", 9)]:
        pq.push(item, pri)
    assert [pq.pop() for _ in range(3)] == ["low", "mid", "high"]
    # step 4: items chosen so alphabetical order != insertion order
    for item in ["zed", "amy", "kim"]:
        pq.push(item, 3)
    assert [pq.pop() for _ in range(3)] == ["zed", "amy", "kim"]
    # step 5
    _raises(IndexError, pq.peek)
    assert len(pq) == 0
    pq.push("x", 2)
    pq.push("y", 1)
    assert pq.peek() == "y" and len(pq) == 2
    # step 6
    pq.update("x", 0)
    assert len(pq) == 2
    assert [pq.pop(), pq.pop()] == ["x", "y"]
    _raises(IndexError, pq.pop)          # x must not come back a second time
    _raises(KeyError, pq.update, "ghost", 1)
    pq.push("a", 1)
    pq.push("b", 1)
    pq.update("a", 1)
    assert [pq.pop(), pq.pop()] == ["b", "a"], "updated item ties as if newly pushed"


class PriorityQueue:
    def __init__(self):
        self._heap: list[list] = []
        self._entries: dict = {}           # item -> its live heap entry
        self._counter = itertools.count()  # tie-breaker: FIFO, and items never get compared

    def push(self, item, priority: int) -> None:
        entry = [priority, next(self._counter), item, True]
        self._entries[item] = entry
        heapq.heappush(self._heap, entry)

    def _discard_dead(self) -> None:
        while self._heap and not self._heap[0][3]:
            heapq.heappop(self._heap)

    def pop(self):
        self._discard_dead()
        if not self._heap:
            raise IndexError("pop from empty priority queue")
        _, _, item, _ = heapq.heappop(self._heap)
        del self._entries[item]
        return item

    def peek(self):
        self._discard_dead()
        if not self._heap:
            raise IndexError("peek at empty priority queue")
        return self._heap[0][2]

    def update(self, item, priority: int) -> None:
        if item not in self._entries:
            raise KeyError(item)
        self._entries[item][3] = False  # lazy delete: heapq can't remove from the middle
        self.push(item, priority)

    def __len__(self) -> int:
        return len(self._entries)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
