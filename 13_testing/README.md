# 13 - Testing

```bash
python 13_testing/exercises.py
```

Most exercises here have you write the **tests**. A `check_xxx(impl)` function is run
against a correct implementation (must pass) and against realistic buggy "mutants"
(must fail on each). A survivor is named in the output: that's a bug your suite would ship.
`StackTests` / `GradeTests` work the same way but as real `unittest.TestCase` classes.

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `check_slugify` | easy | plain `assert` with messages, case tables |
| 02 | `check_overlaps` | easy | boundary cases, check both argument orders |
| 03 | `StackTests` | easy | `unittest.TestCase`, `setUp`, `assertRaises` |
| 04 | `check_send_welcome` | easy | `Mock`, `return_value`, `assert_called_once_with` |
| 05 | `check_fetch_with_retry` | medium | `side_effect` list of exceptions/values, `call_count` |
| 06 | `check_greeting` | medium | `patch.object` a clock as a context manager |
| 07 | `GradeTests` | medium | table-driven `subTest` |
| 08 | `InMemoryBookingRepo` | medium | write a fake (vs a mock), per-instance state |
| 09 | `check_print_report` | medium | `io.StringIO` to capture output |
| 10 | `check_merge_intervals` | advanced | input mutation, nested/touching intervals |
| 11 | `check_lru_cache` | advanced | the Ode onsite structure, 7 mutants |
| 12 | `check_rate_limiter` | advanced | injected fake clock, exact window edge |
| 13 | `PriorityQueue` + `check_priority_queue` | advanced | TDD red to green, mid-session requirement change |

## Cheat sheet

### pytest vs unittest, side by side

```python
# ---- pytest ----                                  # ---- unittest ----
# file: test_lru.py, functions named test_*         # class LRUTests(unittest.TestCase): methods test_*
def test_get_missing_returns_none():                 def test_get_missing_returns_none(self):
    assert LRUCache(2).get("a") is None                  self.assertIsNone(LRUCache(2).get("a"))

assert x == y                                        self.assertEqual(x, y)
assert x is True / assert not x                      self.assertTrue(x) / self.assertFalse(x)
assert x is None                                     self.assertIsNone(x)
assert item in coll                                  self.assertIn(item, coll)
assert 0.1 + 0.2 == pytest.approx(0.3)               self.assertAlmostEqual(0.1 + 0.2, 0.3)

with pytest.raises(KeyError):                        with self.assertRaises(KeyError):
    d["missing"]                                         d["missing"]
with pytest.raises(ValueError, match="capacity"):    with self.assertRaisesRegex(ValueError, "capacity"):
    LRUCache(0)                                          LRUCache(0)
```

Fixtures vs `setUp`:

```python
# pytest: a fixture is a function; tests ask for it by parameter name
@pytest.fixture
def cache():
    c = LRUCache(2)
    yield c                 # code after yield = teardown
    c.clear()

def test_put_then_get(cache):
    cache.put("a", 1)
    assert cache.get("a") == 1

# unittest: setUp runs before EVERY test method, tearDown after
class LRUTests(unittest.TestCase):
    def setUp(self):
        self.cache = LRUCache(2)
    def tearDown(self):
        self.cache.clear()
    @classmethod
    def setUpClass(cls): ...          # once per class (expensive shared setup)
```

Table-driven tests:

```python
# pytest: each row is its own test, reported separately
@pytest.mark.parametrize("score, want", [(90, "A"), (89, "B"), (59, "F")])
def test_letter_grade(score, want):
    assert letter_grade(score) == want

# unittest: subTest keeps going after a failing row and reports each one
def test_letter_grade(self):
    for score, want in [(90, "A"), (89, "B"), (59, "F")]:
        with self.subTest(score=score):
            self.assertEqual(letter_grade(score), want)
```

Temp files and patching:

```python
def test_writes_file(tmp_path):            # pytest: a fresh pathlib.Path dir per test
    p = tmp_path / "out.txt"
    save(p); assert p.read_text() == "hi\n"
# unittest: with tempfile.TemporaryDirectory() as d: p = Path(d) / "out.txt"

def test_greeting(monkeypatch):            # pytest: undone automatically after the test
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 1, 1, 9))
    monkeypatch.setenv("API_KEY", "test")
# unittest: with patch.object(clock, "now", return_value=...):   /  patch.dict(os.environ, {...})
```

Running:

```bash
python -m pytest -q -x                 # quiet, stop at first failure
python -m pytest -k lru -vv            # only tests matching "lru", verbose diffs
python -m pytest test_lru.py::test_get_missing_returns_none
python -m unittest -v                  # discovers test*.py
python -m unittest test_lru.LRUTests.test_put_then_get
```

pytest collects `test_*.py` files and `test_*` functions/methods (and `Test*` classes
with no `__init__`). It also runs unittest TestCases unchanged.

### unittest.mock

```python
from unittest.mock import Mock, MagicMock, patch, call, create_autospec

m = Mock()                         # any attribute/call works and is recorded
m.send.return_value = "id-1"       # what m.send(...) returns
m.send.side_effect = ValueError("x")             # raise on every call
m.send.side_effect = [ConnectionError(), "ok"]   # one per call: raise, then return "ok"
m.send.side_effect = lambda to, **kw: to.upper() # compute the return value

m.send.assert_called_once_with(to="a", subject="Hi")   # exact args AND kwargs
m.send.assert_called_with(...)     # checks the LAST call only
m.send.assert_not_called()
m.send.call_count                  # int
m.send.call_args                   # call(...) of the last call; .args / .kwargs
m.send.call_args_list == [call("u"), call("u")]

MagicMock()                        # Mock + magic methods (len(), iteration, `with`) preconfigured
Mock(spec=RealClass)               # unknown top-level attributes raise AttributeError
create_autospec(RealClass, instance=True)   # whole tree spec'd, signatures enforced
```

Gotchas:

- `assert_called_once_with` compares positional and keyword args literally:
  `send("a")` does not match `assert_called_once_with(to="a")`. `create_autospec(Cls)`
  knows the signature and normalizes them (and rejects calls with wrong arguments).
- Misspelled asserts: 3.10 raises AttributeError for names starting `assert`/`assret`/
  `asert`/`assrt`, but `m.send.called_once_with(...)` (missing `assert_`) is just a new
  auto-created Mock: it "passes" and checks nothing. `create_autospec(Mailer)` catches it
  (`Mock(spec=Mailer)` only guards the top level, not `m.send.<typo>`).
- An exhausted `side_effect` list raises `StopIteration` on the next call.

### patch: patch where it's LOOKED UP, not where it's defined

```python
# app.py:   from clock import now   ->  patch("app.now")      (app has its own reference)
# app.py:   import clock; clock.now() -> patch("clock.now")
with patch("app.now", return_value=datetime(2026, 1, 1, 9)) as fake_now:
    assert app.greeting() == "Good morning"
    fake_now.assert_called_once()

with patch.object(clock, "now", return_value=...):   # when you hold the object already
    ...

@patch("app.requests.get")         # as a decorator: the mock is passed in as an argument
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"ok": True}

p = patch("app.now"); p.start(); ...; p.stop()   # forget stop() and it leaks into other tests
```

`datetime.datetime.now` can't be patched (built-in type). Inject a clock
(`clock=time.monotonic`, `now=datetime.now` parameter) or patch the name in your module.

### Fakes vs mocks vs stubs

```python
# Stub:  returns canned answers.        fetch = Mock(return_value="page")
# Mock:  stub + you assert the calls.   mailer.send.assert_called_once_with(...)
# Fake:  a real, simple implementation. InMemoryRepo, FakeClock, sqlite in :memory:
```

Mock the boundaries you can't run (network, email, payments, time). Fake the things you
own (storage). Asserting on outcomes survives refactors; asserting on every internal call
breaks the moment the code is reorganized, even if it still works.

```python
class FakeClock:
    def __init__(self, t=0.0): self.t = t
    def __call__(self): return self.t
    def advance(self, s): self.t += s
rl = RateLimiter(limit=2, window=10, clock=FakeClock())   # no sleep() in tests, ever
```

### Capturing output

```python
buf = io.StringIO()
report(rows, out=buf)
assert buf.getvalue() == "a: 1\ntotal: 1\n"

from contextlib import redirect_stdout
with redirect_stdout(io.StringIO()) as buf:       # for code that print()s to stdout
    main()
# pytest: def test_x(capsys): main(); assert capsys.readouterr().out == "..."
```

Gotcha: `def report(rows, out=sys.stdout)` binds the stream at definition time, so
`redirect_stdout` can't capture it. Use `out=None` and `out = sys.stdout if out is None else out`.

### TDD loop (what the pairing interviewer is scoring)

1. Say the behavior list out loud; pick the smallest first.
2. Write ONE test. Run it. Confirm it fails **on the assert**, not on an import or typo.
3. Write the least code that passes. Run. Green.
4. Refactor with the bar green. Next behavior.
5. Requirement change: write the failing test for it **before** touching the code.

Test smells the mutants in this topic punish: only happy paths; never the boundary
(`<` vs `<=`); one argument order; checking the result but not that the input was left
alone; `== None` instead of `is None`; asserting a call happened but not that it happened
exactly once (or not at all on the error path).
