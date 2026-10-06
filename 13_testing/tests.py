"""Grading for 13_testing.

Most exercises here ask you to WRITE TESTS: a check_xxx(impl) function full of asserts.
Each one is graded twice:
  1. against a correct implementation  -> your checks must pass
  2. against several buggy "mutants"   -> your checks must FAIL on every one
A mutant your checks don't fail on "survived": it is a real bug your tests would ship.

(Spoilers below: the mutant list tells you exactly which bugs to test for. Try the
exercise first and read the survivor messages instead.)
"""

import contextlib
import heapq
import inspect
import io
import itertools
import re
import sys
import time
import traceback
import types
import unittest
from collections import OrderedDict, defaultdict, deque
from datetime import datetime

from harness import expect, expect_raises


# ------------------------------------------------------------- grading ----

def _where(e: BaseException) -> str:
    tb = traceback.extract_tb(e.__traceback__)[-1]
    return f"assert failed at line {tb.lineno}: {tb.line}"


def _catches(call, impl) -> bool:
    """True if running the learner's checks against impl fails in any way."""
    try:
        call(impl)
    except NotImplementedError:
        raise
    except Exception:  # noqa: BLE001 - AssertionError, or the mutant crashing: both = caught
        return True
    return False


def _grade(checker, correct, mutants: dict, call=None):
    call = call or checker
    try:
        call(correct)  # NotImplementedError propagates -> "not started"
    except AssertionError as e:
        raise AssertionError("your checks FAIL against the CORRECT implementation:\n"
                             + (str(e) or _where(e))) from None
    survivors = [desc for desc, impl in mutants.items() if not _catches(call, impl)]
    if survivors:
        raise AssertionError(f"your checks caught {len(mutants) - len(survivors)}/{len(mutants)} bugs. "
                             "They didn't catch:\n"
                             + "\n".join(f"  - mutant that {d}" for d in survivors))


def _run_case(case_cls):
    """Run a unittest.TestCase class quietly. Returns (number_of_tests, result)."""
    suite = unittest.TestLoader().loadTestsFromTestCase(case_cls)
    n = suite.countTestCases()  # count BEFORE running: the suite drops tests as it runs them
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    for _, tb in result.errors:
        if "NotImplementedError" in tb:
            raise NotImplementedError
    return n, result


def _first_problem(result) -> str:
    test, tb = (result.failures + result.errors)[0]
    last = [line for line in tb.strip().splitlines() if line.strip()][-1]
    return f"{test.id().rsplit('.', 1)[-1]}: {last}"


def _grade_case(case_cls, attr: str, correct, mutants: dict, min_tests: int):
    def with_impl(impl):
        return type(case_cls.__name__, (case_cls,), {attr: impl})

    n, result = _run_case(with_impl(correct))
    if not result.wasSuccessful():
        raise AssertionError("your TestCase FAILS against the CORRECT implementation:\n  "
                             + _first_problem(result))
    assert n >= min_tests, f"found {n} test methods, need at least {min_tests} (names must start with test_)"
    survivors = [d for d, impl in mutants.items() if _run_case(with_impl(impl))[1].wasSuccessful()]
    if survivors:
        raise AssertionError(f"your TestCase caught {len(mutants) - len(survivors)}/{len(mutants)} bugs. "
                             "It didn't catch:\n" + "\n".join(f"  - mutant that {d}" for d in survivors))


# ----------------------------------------------------------- ex01 slugify ----

def _slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


_SLUGIFY_MUTANTS = {
    "forgets to lowercase": lambda s: re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-"),
    "keeps a trailing dash": lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).lstrip("-"),
    "keeps a leading dash": lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).rstrip("-"),
    "doesn't collapse runs (one dash per bad char)": lambda s: re.sub(r"[^a-z0-9]", "-", s.lower()).strip("-"),
    "treats digits as separators": lambda s: re.sub(r"[^a-z]+", "-", s.lower()).strip("-"),
}


def test_ex01(m):
    """check_slugify: plain asserts that catch 5 buggy slugifiers"""
    _grade(m.check_slugify, _slugify, _SLUGIFY_MUTANTS)


# ---------------------------------------------------------- ex02 overlaps ----

def _overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


_OVERLAPS_MUTANTS = {
    "counts touching intervals as overlapping": lambda a, b: a[0] <= b[1] and b[0] <= a[1],
    "is inclusive on one side only": lambda a, b: a[0] <= b[1] and b[0] < a[1],
    "only checks whether b starts inside a": lambda a, b: a[0] <= b[0] < a[1],
    "misses a sitting entirely inside b":
        lambda a, b: a[0] <= b[0] < a[1] or a[0] < b[1] <= a[1],
}


def test_ex02(m):
    """check_overlaps: boundary cases for half-open intervals"""
    _grade(m.check_overlaps, _overlaps, _OVERLAPS_MUTANTS)


# ------------------------------------------------------------- ex03 Stack ----

class _Stack:
    def __init__(self):
        self._items = []

    def push(self, x):
        self._items.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def __len__(self):
        return len(self._items)

    def is_empty(self):
        return not self._items


class _FifoStack(_Stack):
    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop(0)


class _PopNoneStack(_Stack):
    def pop(self):
        return self._items.pop() if self._items else None


class _PeekPopsStack(_Stack):
    def peek(self):
        return self.pop()


class _PeekNoneStack(_Stack):
    def peek(self):
        return self._items[-1] if self._items else None


class _CountingStack(_Stack):
    """Tracks size in a separate counter and forgets to decrement it."""

    def __init__(self):
        super().__init__()
        self._n = 0

    def push(self, x):
        super().push(x)
        self._n += 1

    def __len__(self):
        return self._n

    def is_empty(self):
        return self._n == 0


_STACK_MUTANTS = {
    "pops the OLDEST item (FIFO)": _FifoStack,
    "returns None from pop() on an empty stack": _PopNoneStack,
    "removes the item on peek()": _PeekPopsStack,
    "returns None from peek() on an empty stack": _PeekNoneStack,
    "never decrements len() on pop()": _CountingStack,
}


def test_ex03(m):
    """StackTests: unittest.TestCase with setUp and assertRaises"""
    assert "setUp" in vars(m.StackTests), "define setUp() to build a fresh stack per test"
    _grade_case(m.StackTests, "stack_class", _Stack, _STACK_MUTANTS, min_tests=4)


# ------------------------------------------------------ ex04 send_welcome ----

def _send_welcome(user, mailer):
    if not user.email:
        raise ValueError("user has no email")
    return mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")


def _sw_twice(user, mailer):
    if not user.email:
        raise ValueError("user has no email")
    mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")
    return mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")


def _sw_to_name(user, mailer):
    if not user.email:
        raise ValueError("user has no email")
    return mailer.send(to=user.name, subject="Welcome!", body=f"Hi {user.name}")


def _sw_returns_none(user, mailer):
    if not user.email:
        raise ValueError("user has no email")
    mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")


def _sw_no_validation(user, mailer):
    return mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")


def _sw_validates_late(user, mailer):
    msg_id = mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.name}")
    if not user.email:
        raise ValueError("user has no email")
    return msg_id


def _sw_body_email(user, mailer):
    if not user.email:
        raise ValueError("user has no email")
    return mailer.send(to=user.email, subject="Welcome!", body=f"Hi {user.email}")


_SEND_WELCOME_MUTANTS = {
    "sends the email twice": _sw_twice,
    "sends to the user's name instead of their email": _sw_to_name,
    "drops mailer.send's return value (returns None)": _sw_returns_none,
    "never raises for a missing email": _sw_no_validation,
    "sends first, THEN raises for a missing email": _sw_validates_late,
    "greets the user by email in the body": _sw_body_email,
}


def test_ex04(m):
    """check_send_welcome: Mock, return_value, assert_called_once_with"""
    _grade(m.check_send_welcome, _send_welcome, _SEND_WELCOME_MUTANTS)


# --------------------------------------------------- ex05 fetch_with_retry ----

def _fwr(fetch, url, attempts=3):
    for i in range(attempts):
        try:
            return fetch(url)
        except ConnectionError:
            if i == attempts - 1:
                raise


def _fwr_no_retry(fetch, url, attempts=3):
    return fetch(url)


def _fwr_extra(fetch, url, attempts=3):
    return _fwr(fetch, url, attempts + 1)


def _fwr_fewer(fetch, url, attempts=3):
    return _fwr(fetch, url, attempts - 1) if attempts > 1 else fetch(url)


def _fwr_swallow(fetch, url, attempts=3):
    for _ in range(attempts):
        try:
            return fetch(url)
        except ConnectionError:
            continue
    return None


def _fwr_any_error(fetch, url, attempts=3):
    for i in range(attempts):
        try:
            return fetch(url)
        except Exception:
            if i == attempts - 1:
                raise


_FWR_MUTANTS = {
    "never retries": _fwr_no_retry,
    "makes one attempt too many": _fwr_extra,
    "makes one attempt too few": _fwr_fewer,
    "swallows the final ConnectionError and returns None": _fwr_swallow,
    "also retries non-network errors like ValueError": _fwr_any_error,
}


def test_ex05(m):
    """check_fetch_with_retry: Mock(side_effect=[exc, value]) and call_count"""
    _grade(m.check_fetch_with_retry, _fwr, _FWR_MUTANTS)


# ------------------------------------------------------- ex06 greeting ----

def _greet_rule(h):
    if 5 <= h < 12:
        return "Good morning"
    if 12 <= h < 18:
        return "Good afternoon"
    return "Good evening"


def _make_clock(rule, use_clock=True):
    """A module-like object: clock.now() and clock.greeting(). greeting looks up
    clock.now at CALL time, which is what lets patch.object swap it out."""
    clock = types.SimpleNamespace()
    clock.now = datetime.now
    if use_clock:
        clock.greeting = lambda: rule(clock.now().hour)
    else:
        clock.greeting = lambda: rule(datetime.now().hour)
    return clock


def _greet_noon_morning(h):
    return "Good morning" if 5 <= h <= 12 else _greet_rule(h)


def _greet_six_afternoon(h):
    return "Good afternoon" if 12 <= h <= 18 else _greet_rule(h)


def _greet_no_lower_bound(h):
    return "Good morning" if h < 12 else _greet_rule(h)


def test_ex06(m):
    """check_greeting: mock.patch.object a clock dependency"""
    correct = _make_clock(_greet_rule)
    mutants = {
        "calls noon morning": _make_clock(_greet_noon_morning),
        "still says afternoon at 18:00": _make_clock(_greet_six_afternoon),
        "says morning at 3am": _make_clock(_greet_no_lower_bound),
        "ignores the injected clock (calls datetime.now() itself)": _make_clock(_greet_rule, use_clock=False),
    }
    original_now = correct.now  # bound methods are fresh objects per lookup; keep this one
    _grade(m.check_greeting, correct, mutants)
    assert correct.now is original_now, \
        "clock.now is still patched after your checks ran: use `with patch.object(...)` so it's restored"


# --------------------------------------------------- ex07 letter_grade ----

def _letter_grade(score):
    if not 0 <= score <= 100:
        raise ValueError(f"score out of range: {score}")
    for cutoff, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= cutoff:
            return letter
    return "F"


def _lg_exclusive(score):
    if not 0 <= score <= 100:
        raise ValueError(score)
    for cutoff, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score > cutoff:
            return letter
    return "F"


def _lg_off_by_one_c(score):
    if not 0 <= score <= 100:
        raise ValueError(score)
    for cutoff, letter in ((90, "A"), (80, "B"), (71, "C"), (60, "D")):
        if score >= cutoff:
            return letter
    return "F"


def _lg_no_validation(score):
    for cutoff, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= cutoff:
            return letter
    return "F"


def _lg_rejects_100(score):
    if not 0 <= score < 100:
        raise ValueError(score)
    return _letter_grade(score)


_GRADE_MUTANTS = {
    "makes every cutoff exclusive (90 is a B)": staticmethod(_lg_exclusive),
    "puts exactly 70 in D": staticmethod(_lg_off_by_one_c),
    "accepts scores below 0 and above 100": staticmethod(_lg_no_validation),
    "rejects a perfect 100": staticmethod(_lg_rejects_100),
}


def test_ex07(m):
    """GradeTests: table-driven cases with self.subTest"""
    _grade_case(m.GradeTests, "letter_grade", staticmethod(_letter_grade), _GRADE_MUTANTS, min_tests=2)
    src = "".join(inspect.getsource(fn) for name, fn in vars(m.GradeTests).items()
                  if name.startswith("test") and callable(fn))  # method bodies only, not the docstring
    assert "subTest" in src, "loop over a table of cases and wrap each in `with self.subTest(...)`"
    assert "assertRaises" in src, "test the out-of-range scores with self.assertRaises"


# ------------------------------------------------ ex08 InMemoryBookingRepo ----

class _Conflict(Exception):
    pass


class _BookingService:
    """The real service under test; it only talks to the repo through its interface."""

    def __init__(self, repo, booking_cls):
        self.repo = repo
        self.booking_cls = booking_cls

    def book(self, booking_id, room_id, start, end):
        for b in self.repo.for_room(room_id):
            if start < b.end and b.start < end:
                raise _Conflict(b.id)
        booking = self.booking_cls(booking_id, room_id, start, end)
        self.repo.add(booking)
        return booking

    def cancel(self, booking_id):
        return self.repo.delete(booking_id)


def test_ex08(m):
    """InMemoryBookingRepo: write a fake, then test a real service with it"""
    B = m.Booking
    repo = m.InMemoryBookingRepo()
    assert repo.get("nope") is None, "get() of an unknown id returns None"
    expect(repo.for_room("A"), [], "for_room() of an empty repo")

    late, early, other = B("b2", "A", 13, 14), B("b1", "A", 9, 10), B("b3", "B", 9, 10)
    for b in (late, early, other):
        repo.add(b)
    expect(repo.get("b1"), early)
    expect(repo.for_room("A"), [early, late], "for_room() sorted by start")
    expect(repo.for_room("B"), [other])
    expect_raises(ValueError, repo.add, B("b1", "C", 1, 2))

    leaked = repo.for_room("A")
    leaked.clear()
    expect(len(repo.for_room("A")), 2, "clearing the list for_room() returned emptied the repo: return a new list")

    expect(m.InMemoryBookingRepo().for_room("A"), [],
           "a NEW repo already has bookings: is the storage dict a class attribute instead of set in __init__?")

    assert repo.delete("b2") is True
    assert repo.delete("b2") is False, "deleting twice returns False"
    assert repo.get("b2") is None

    svc = _BookingService(m.InMemoryBookingRepo(), B)
    svc.book("x1", "A", 9, 11)
    expect_raises(_Conflict, svc.book, "x2", "A", 10, 12)
    svc.book("x3", "A", 11, 12)
    assert svc.cancel("x1") is True
    svc.book("x4", "A", 10, 11)  # the cancelled slot is free again
    expect([b.id for b in svc.repo.for_room("A")], ["x4", "x3"])


# ---------------------------------------------------- ex09 print_report ----

def _print_report(rows, out=None):
    out = sys.stdout if out is None else out
    if not rows:
        print("(no rows)", file=out)
        return
    for name, qty in rows:
        print(f"{name}: {qty}", file=out)
    print(f"total: {sum(q for _, q in rows)}", file=out)


def _pr_real_stdout(rows, out=None):
    _print_report(rows)  # ignores `out`


def _pr_total_skips_last(rows, out=None):
    out = sys.stdout if out is None else out
    if not rows:
        print("(no rows)", file=out)
        return
    for name, qty in rows:
        print(f"{name}: {qty}", file=out)
    print(f"total: {sum(q for _, q in rows[:-1])}", file=out)


def _pr_empty_total(rows, out=None):
    out = sys.stdout if out is None else out
    for name, qty in rows:
        print(f"{name}: {qty}", file=out)
    print(f"total: {sum(q for _, q in rows)}", file=out)


def _pr_no_final_newline(rows, out=None):
    out = sys.stdout if out is None else out
    if not rows:
        print("(no rows)", file=out)
        return
    for name, qty in rows:
        print(f"{name}: {qty}", file=out)
    out.write(f"total: {sum(q for _, q in rows)}")


def _pr_sorted(rows, out=None):
    _print_report(sorted(rows), out)


_REPORT_MUTANTS = {
    "ignores `out` and prints to the real stdout": _pr_real_stdout,
    "leaves the last row out of the total": _pr_total_skips_last,
    "prints 'total: 0' instead of '(no rows)' for empty input": _pr_empty_total,
    "forgets the newline after the total line": _pr_no_final_newline,
    "sorts the rows by name instead of keeping input order": _pr_sorted,
}


def test_ex09(m):
    """check_print_report: capture output with io.StringIO"""
    def quietly(impl):
        with contextlib.redirect_stdout(io.StringIO()):  # keep stray prints off the console
            m.check_print_report(impl)

    _grade(m.check_print_report, _print_report, _REPORT_MUTANTS, call=quietly)


# ------------------------------------------------- ex10 merge_intervals ----

def _merge(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def _merge_in_place(intervals):
    intervals.sort()
    out = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def _merge_no_touch(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s < out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def _merge_unsorted(intervals):
    out = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def _merge_drops_last(intervals):
    out = []
    cur = None
    for s, e in sorted(intervals):
        if cur and s <= cur[1]:
            cur = (cur[0], max(cur[1], e))
        else:
            if cur:
                out.append(cur)
            cur = (s, e)
    return out  # forgot: if cur: out.append(cur)


def _merge_no_max(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], e)
        else:
            out.append((s, e))
    return out


_MERGE_MUTANTS = {
    "sorts the caller's list in place": _merge_in_place,
    "doesn't merge touching intervals like (1, 3) and (3, 5)": _merge_no_touch,
    "assumes the input is already sorted": _merge_unsorted,
    "drops the last interval": _merge_drops_last,
    "shrinks when an interval sits inside an earlier one": _merge_no_max,
}


def test_ex10(m):
    """check_merge_intervals: input mutation, boundaries, ordering"""
    _grade(m.check_merge_intervals, _merge, _MERGE_MUTANTS)


# ----------------------------------------------------------- ex11 LRU ----

class _LRU:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, key):
        if key not in self._d:
            return None
        self._d.move_to_end(key)
        return self._d[key]

    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)

    def __len__(self):
        return len(self._d)


class _LRUGetNoRefresh(_LRU):
    def get(self, key):
        return self._d.get(key)


class _LRUEvictsNewest(_LRU):
    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=True)


class _LRUEvictsEarly(_LRU):
    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) >= self.capacity:
            self._d.popitem(last=False)


class _LRUPutNoRefresh(_LRU):
    def put(self, key, value):
        self._d[key] = value  # updating an existing key keeps its old position
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)


class _LRUKeyError(_LRU):
    def get(self, key):
        self._d.move_to_end(key)
        return self._d[key]


class _LRUUpdateEvicts(_LRU):
    def put(self, key, value):
        if len(self._d) >= self.capacity:  # checks size before knowing if key is new
            self._d.popitem(last=False)
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value


class _LRUAnyCapacity(_LRU):
    def __init__(self, capacity):
        self.capacity = capacity
        self._d = OrderedDict()


_LRU_MUTANTS = {
    "doesn't refresh recency on get()": _LRUGetNoRefresh,
    "evicts the NEWEST entry instead of the oldest": _LRUEvictsNewest,
    "evicts at capacity instead of over it (holds capacity - 1)": _LRUEvictsEarly,
    "doesn't refresh recency when put() updates an existing key": _LRUPutNoRefresh,
    "raises KeyError from get() on a missing key": _LRUKeyError,
    "evicts something when put() merely updates an existing key at capacity": _LRUUpdateEvicts,
    "accepts capacity 0 without raising ValueError": _LRUAnyCapacity,
}


def test_ex11(m):
    """check_lru_cache: the Ode-style data structure, 7 realistic bugs"""
    _grade(m.check_lru_cache, _LRU, _LRU_MUTANTS)


# --------------------------------------------------- ex12 RateLimiter ----

class _RateLimiter:
    def __init__(self, limit, window, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self._hits = defaultdict(deque)

    def _prune(self, q, now):
        while q and now - q[0] >= self.window:
            q.popleft()

    def allow(self, key):
        now = self.clock()
        q = self._hits[key]
        self._prune(q, now)
        if len(q) < self.limit:
            q.append(now)
            return True
        return False


class _RLShared(_RateLimiter):
    def allow(self, key):
        return super().allow("*")


class _RLInclusiveWindow(_RateLimiter):
    def _prune(self, q, now):
        while q and now - q[0] > self.window:
            q.popleft()


class _RLCountsDenied(_RateLimiter):
    def allow(self, key):
        now = self.clock()
        q = self._hits[key]
        self._prune(q, now)
        q.append(now)
        return len(q) <= self.limit


class _RLOffByOne(_RateLimiter):
    def allow(self, key):
        now = self.clock()
        q = self._hits[key]
        self._prune(q, now)
        if len(q) <= self.limit:
            q.append(now)
            return True
        return False


class _RLNoWindow(_RateLimiter):
    def _prune(self, q, now):
        pass


class _RLRealClock(_RateLimiter):
    def __init__(self, limit, window, clock=time.monotonic):
        super().__init__(limit, window, time.monotonic)


_RL_MUTANTS = {
    "shares one limit across all keys": _RLShared,
    "still counts a request exactly `window` seconds old": _RLInclusiveWindow,
    "counts DENIED requests toward the limit": _RLCountsDenied,
    "allows limit + 1 requests": _RLOffByOne,
    "never forgets old requests": _RLNoWindow,
    "ignores the injected clock (uses time.monotonic directly)": _RLRealClock,
}


def test_ex12(m):
    """check_rate_limiter: sliding window tested with a fake clock"""
    _grade(m.check_rate_limiter, _RateLimiter, _RL_MUTANTS)


# ------------------------------------------------- ex13 PriorityQueue ----

class _PQ:
    def __init__(self):
        self._heap = []
        self._live = {}  # item -> its current heap entry
        self._seq = itertools.count()

    def _tiebreak(self, item):
        return next(self._seq)

    def push(self, item, priority):
        entry = [priority, self._tiebreak(item), item, True]
        self._live[item] = entry
        heapq.heappush(self._heap, entry)

    def _drop_dead(self):
        while self._heap and not self._heap[0][3]:
            heapq.heappop(self._heap)

    def pop(self):
        self._drop_dead()
        if not self._heap:
            raise IndexError("pop from empty priority queue")
        entry = heapq.heappop(self._heap)
        del self._live[entry[2]]
        return entry[2]

    def peek(self):
        self._drop_dead()
        if not self._heap:
            raise IndexError("peek at empty priority queue")
        return self._heap[0][2]

    def update(self, item, priority):
        if item not in self._live:
            raise KeyError(item)
        self._live[item][3] = False
        self.push(item, priority)

    def __len__(self):
        return len(self._live)


class _PQTieByItem(_PQ):
    def _tiebreak(self, item):
        return item


class _PQPopNone(_PQ):
    def pop(self):
        self._drop_dead()
        return super().pop() if self._heap else None


class _PQPeekPops(_PQ):
    def peek(self):
        return self.pop()


class _PQMaxFirst(_PQ):
    def push(self, item, priority):
        super().push(item, -priority)

    def update(self, item, priority):
        super().update(item, -priority)


class _PQUpdateLeavesOld(_PQ):
    def update(self, item, priority):
        if item not in self._live:
            raise KeyError(item)
        self.push(item, priority)  # forgot to mark the old entry dead

    def _drop_dead(self):
        pass

    def pop(self):
        if not self._heap:
            raise IndexError("pop from empty priority queue")
        entry = heapq.heappop(self._heap)
        self._live.pop(entry[2], None)
        return entry[2]


class _PQLenCountsStale(_PQ):
    def __len__(self):
        return sum(1 for e in self._heap if e[2] in self._live)  # dead entries still match


class _PQUpdateAdds(_PQ):
    def update(self, item, priority):
        if item in self._live:
            self._live[item][3] = False
        self.push(item, priority)


_PQ_MUTANTS = {
    "breaks priority ties by item name instead of insertion order": _PQTieByItem,
    "returns None from pop() on an empty queue": _PQPopNone,
    "removes the item on peek()": _PQPeekPops,
    "pops the HIGHEST priority number first": _PQMaxFirst,
    "leaves the old entry live after update() (item pops twice)": _PQUpdateLeavesOld,
    "counts stale entries in len() after update()": _PQLenCountsStale,
    "silently adds a missing item on update() instead of raising KeyError": _PQUpdateAdds,
}


def _reference_pq_checks(PQ):
    pq = PQ()
    expect_raises(IndexError, pq.pop)
    expect_raises(IndexError, pq.peek)
    expect(len(pq), 0, "len of a new queue")
    pq.push("a", 5)
    expect(pq.pop(), "a", "push then pop")

    pq = PQ()
    for item, pri in [("mid", 5), ("low", 1), ("high", 9)]:
        pq.push(item, pri)
    expect([pq.pop(), pq.pop(), pq.pop()], ["low", "mid", "high"], "lowest priority number first")

    pq = PQ()
    for item in ["zed", "amy", "kim"]:
        pq.push(item, 3)
    expect([pq.pop(), pq.pop(), pq.pop()], ["zed", "amy", "kim"], "equal priorities pop in insertion order")

    pq = PQ()
    pq.push("x", 2)
    pq.push("y", 1)
    expect(pq.peek(), "y", "peek returns the next item")
    expect(len(pq), 2, "peek must not remove")

    pq.update("x", 0)
    expect(len(pq), 2, "update doesn't change the size")
    expect(pq.pop(), "x", "x was updated to priority 0")
    expect(pq.pop(), "y")
    expect_raises(IndexError, pq.pop)
    expect_raises(KeyError, pq.update, "ghost", 1)

    pq = PQ()
    pq.push("a", 1)
    pq.push("b", 1)
    pq.update("a", 1)
    expect([pq.pop(), pq.pop()], ["b", "a"], "an updated item ties as if newly pushed")


def test_ex13(m):
    """PriorityQueue + check_priority_queue: TDD, write the tests AND the code"""
    _grade(m.check_priority_queue, _PQ, _PQ_MUTANTS)
    try:
        _reference_pq_checks(m.PriorityQueue)
    except AssertionError as e:
        raise AssertionError(f"your PriorityQueue fails a hidden check:\n{e or _where(e)}") from None
    try:
        m.check_priority_queue(m.PriorityQueue)
    except AssertionError as e:
        raise AssertionError(f"your PriorityQueue fails YOUR checks:\n{e or _where(e)}") from None
