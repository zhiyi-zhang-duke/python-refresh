from harness import expect, expect_raises


def _fake_input(lines, end=EOFError):
    """A stand-in for input(): returns each line, then raises `end` (EOFError = Ctrl-D)."""
    it = iter(lines)
    prompts = []

    def read(prompt=""):
        prompts.append(prompt)
        try:
            return next(it)
        except StopIteration:
            raise end from None

    read.prompts = prompts
    return read


def _commands():
    def load(args):
        if not args:
            raise ValueError("usage: load <model>")
        return "loaded " + " ".join(args)

    def count(args):
        return f"{len(args)} args"

    return {"load": (load, "Load a model"), "count": (count, "Count args")}


def test_ex01(m):
    """names_by_size: tuple sort key, largest first, ties A-Z"""
    models = [
        {"name": "phi3:mini", "size_gb": 2.3},
        {"name": "llama3:70b", "size_gb": 39.0},
        {"name": "gemma:2b", "size_gb": 1.6},
        {"name": "aya:8b", "size_gb": 2.3},
    ]
    before = [d["name"] for d in models]
    expect(m.names_by_size(models), ["llama3:70b", "aya:8b", "phi3:mini", "gemma:2b"])
    expect([d["name"] for d in models], before, "input list must not be reordered (sorted, not .sort)")
    expect(m.names_by_size([]), [])


def test_ex02(m):
    """active_names: comprehension with a filter, dict.get for missing keys"""
    users = [
        {"name": "ana", "active": True},
        {"name": "bo", "active": False},
        {"name": "cy"},
        {"name": "di", "active": True},
    ]
    expect(m.active_names(users), ["ana", "di"])
    expect(m.active_names([]), [])


def test_ex03(m):
    """latency_stats: return several values as a tuple"""
    expect(m.latency_stats([12, 40, 23]), (12, 40, 25.0))
    lo, hi, avg = m.latency_stats([5])
    expect((lo, hi, avg), (5, 5, 5.0))
    expect(m.latency_stats([]), (None, None, None))


def test_ex04(m):
    """dispatch: look up (handler, help) and call entry[0](args)"""
    cmds = _commands()
    expect(m.dispatch(cmds, "  LOAD phi3 mini\n"), "loaded phi3 mini")
    expect(m.dispatch(cmds, "count a b c"), "3 args", "handler receives ONE list of args")
    expect(m.dispatch(cmds, "count"), "0 args")
    expect(m.dispatch(cmds, "explode now"), "unknown command: explode")
    expect(m.dispatch(cmds, "   "), "")


def test_ex05(m):
    """book: *guests then keyword-only start/hours"""
    expect(m.book("A", "jack", "becca", start=9),
           {"room": "A", "guests": ["jack", "becca"], "start": 9, "hours": 1})
    expect(m.book("B", start=14, hours=2), {"room": "B", "guests": [], "start": 14, "hours": 2})
    expect_raises(TypeError, m.book, "A", "jack", 9)      # start passed positionally = a guest
    expect_raises(TypeError, m.book, "A")                 # start missing
    expect_raises(TypeError, m.book, "A", start=9, minutes=30)
    expect_raises(ValueError, m.book, "A", start=9, hours=0)


def test_ex06(m):
    """make_counter: closure state with nonlocal"""
    c = m.make_counter(5)
    expect([c(), c(), c()], [5, 6, 7])
    d = m.make_counter()
    expect(d(), 0, "a new counter starts fresh")
    expect(c(), 8, "counters must not share state")


def test_ex07(m):
    """build_loggers: functools.partial pre-fills arguments"""
    log = []
    loggers = m.build_loggers(log, ["info", "warning", "error"])
    expect(sorted(loggers), ["error", "info", "warning"])
    loggers["error"]("disk full")
    loggers["info"]("ok")
    loggers["warning"]("slow")
    expect(log, ["[ERROR] disk full", "[INFO] ok", "[WARNING] slow"],
           "each logger must keep ITS OWN level (all the same level = late-binding bug)")


def test_ex08(m):
    """pipeline: compose steps left to right"""
    clean = m.pipeline(str.strip, str.lower, str.split)
    expect(clean("  Load PHI3  "), ["load", "phi3"])
    expect(m.pipeline(lambda x: x + 1, lambda x: x * 10)(2), 30, "order matters: (2+1)*10")
    expect(m.pipeline()(42), 42)


def test_ex09(m):
    """run_repl: injected input, (EOFError, KeyboardInterrupt), errors keep going"""
    cmds = _commands()
    read = _fake_input(["load phi3", "", "   ", "bogus", "load", "count x y", "quit", "load never"])
    expect(m.run_repl(read, cmds),
           ["loaded phi3", "unknown command: bogus", "error: usage: load <model>", "2 args", "bye"])
    expect(read.prompts[0], "> ", 'call read("> ") like input("> ")')

    expect(m.run_repl(_fake_input(["load phi3"]), cmds), ["loaded phi3", "bye"], "Ctrl-D (EOFError)")
    # KeyboardInterrupt isn't an Exception subclass, so an uncaught one would kill the
    # whole test run. Turn it into a normal failure instead.
    try:
        out = m.run_repl(_fake_input(["count"], end=KeyboardInterrupt), cmds)
    except KeyboardInterrupt:
        raise AssertionError("KeyboardInterrupt escaped: catch (EOFError, KeyboardInterrupt)") from None
    expect(out, ["0 args", "bye"], "Ctrl-C (KeyboardInterrupt)")
    expect(m.run_repl(_fake_input([]), cmds), ["bye"])


def test_ex10(m):
    """count_calls: decorator forwarding *args/**kwargs, functools.wraps"""
    def greet(name, *, punct="!"):
        """Say hi."""
        return "hi " + name + punct

    def other():
        return 1

    g = m.count_calls(greet)
    o = m.count_calls(other)
    expect(g.calls, 0)
    expect(g("jack"), "hi jack!")
    expect(g("becca", punct="?"), "hi becca?")
    o()
    expect(g.calls, 2)
    expect(o.calls, 1, "each decorated function has its own count")
    expect(g.__name__, "greet", "use functools.wraps")
    expect(g.__doc__, "Say hi.")


def test_ex11(m):
    """timed: decorator factory with an injected clock, try/finally"""
    records = []
    ticks = iter([10.0, 10.25, 20.0, 21.0])
    clock = lambda: next(ticks)  # noqa: E731

    @m.timed(records, clock=clock)
    def add(a, b):
        return a + b

    @m.timed(records, clock=clock)
    def boom():
        raise RuntimeError("nope")

    expect(add(1, b=2), 3)
    expect_raises(RuntimeError, boom)
    expect(records, [("add", 0.25), ("boom", 1.0)], "the failing call must be recorded too")
    expect(add.__name__, "add")


def test_ex12(m):
    """retry: decorator factory with times/exceptions"""
    attempts = []

    @m.retry(times=3, exceptions=(ConnectionError,))
    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("try again")
        return "ok"

    expect(flaky(), "ok")
    expect(len(attempts), 3)

    always = []

    @m.retry(times=2, exceptions=(ValueError, ConnectionError))
    def broken():
        always.append(1)
        raise ValueError(f"fail {len(always)}")

    e = expect_raises(ValueError, broken)
    expect(len(always), 2, "exactly `times` attempts")
    expect(str(e), "fail 2", "re-raise the LAST exception")

    other = []

    @m.retry(times=5, exceptions=(ConnectionError,))
    def wrong_kind():
        other.append(1)
        raise KeyError("x")

    expect_raises(KeyError, wrong_kind)
    expect(len(other), 1, "exceptions not in the tuple are not retried")
    expect(flaky.__name__, "flaky")
    expect_raises(ValueError, m.retry, times=0)


def test_ex13(m):
    """memoize: cache by args, falsy results count as cached"""
    calls = []

    def area(w, h):
        calls.append((w, h))
        return w * h

    f = m.memoize(area)
    expect(f(2, 3), 6)
    expect(f(2, 3), 6)
    expect(f(3, 2), 6)
    expect(calls, [(2, 3), (3, 2)])
    expect(f.cache, {(2, 3): 6, (3, 2): 6})

    nones = []
    g = m.memoize(lambda x: nones.append(x))  # always returns None
    g(1)
    g(1)
    expect(nones, [1], "a cached None is still a cache hit (use `in`, not truthiness)")

    @m.memoize
    def fib(n):
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    expect(fib(90), 2880067194370816120)
    expect(fib.__name__, "fib")


def test_ex14(m):
    """command / run_command: decorator that fills a dispatch dict"""
    m.COMMANDS.clear()

    def weather(args):
        return "Weather for " + " ".join(args)

    def count(args):
        return str(len(args))

    returned = m.command("weather", help="Show weather")(weather)
    assert returned is weather, "the decorator must return the original function"
    m.command("count")(count)
    expect(m.COMMANDS, {"weather": (weather, "Show weather"), "count": (count, "")})

    expect(m.run_command('weather "New York"'), "Weather for New York")
    expect(m.run_command('count "New York"'), "1")
    expect(m.run_command("count New York"), "2")
    expect(m.run_command("   "), "")
    expect(m.run_command("nope"), "unknown command: nope")
    expect_raises(ValueError, lambda: m.command("weather")(weather))
    m.COMMANDS.clear()
