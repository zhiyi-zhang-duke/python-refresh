import io

import provider
from harness import expect, expect_raises


def _fresh(m):
    """Every test starts from a clean provider and the plain-provider CLIENT."""
    provider.reset()
    m.CLIENT = provider


class Spy:
    """A CLIENT stand-in that records which provider functions a handler called."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        fn = getattr(provider, name)

        def wrapper(*args):
            self.calls.append(name)
            return fn(*args)

        return wrapper


def expect_text(actual, expected, what=""):
    """Compare multi-line output line by line, so a mismatch points at the first bad line."""
    expect(actual.splitlines(keepends=True), expected.splitlines(keepends=True), what)


def _out(fn, *args):
    """Run fn(*args, out) and return what it printed."""
    out = io.StringIO()
    fn(*args, out)
    return out.getvalue()


LIST_NOTHING_LOADED = (
    "  phi3:mini     2.3 GB  phi\n"
    "  gemma2:2b     1.6 GB  gemma\n"
    "  mistral:7b    4.1 GB  mistral\n"
    "  llama3:8b     4.7 GB  llama\n"
    "  llama3:70b   39.0 GB  llama\n"
)


def test_ex01(m):
    """parse_line: (cmd, rest) with the rest kept verbatim"""
    expect(m.parse_line("  RUN phi3   tell me  a joke  "), ("run", "phi3   tell me  a joke"))
    expect(m.parse_line("list"), ("list", ""))
    expect(m.parse_line("list\n"), ("list", ""))
    expect(m.parse_line("   "), ("", ""))
    expect(m.parse_line('run phi say "hi"'), ("run", 'phi say "hi"'), "quotes stay as typed")


def test_ex02(m):
    """resolve_model: exact, unique prefix, ambiguous, unknown"""
    _fresh(m)
    models = provider.list_models()
    expect(m.resolve_model("phi", models), "phi3:mini")
    expect(m.resolve_model("LLAMA3:8B", models), "llama3:8b")
    expect(m.resolve_model("mis", models), "mistral:7b")
    e = expect_raises(provider.UnknownModel, m.resolve_model, "llama3", models)
    expect(str(e), "'llama3' is ambiguous: llama3:70b, llama3:8b")
    e = expect_raises(provider.UnknownModel, m.resolve_model, "gpt4", models)
    expect(str(e), "no model matches 'gpt4'")
    tricky = [{"name": "phi3"}, {"name": "phi3:mini"}]
    expect(m.resolve_model("phi3", tricky), "phi3", "an exact match beats a prefix match")


def test_ex03(m):
    """cmd_list / cmd_load: handlers that print to out and go through CLIENT"""
    _fresh(m)
    expect_text(_out(m.cmd_list, ""), LIST_NOTHING_LOADED)

    expect_text(_out(m.cmd_load, "phi"), "loaded phi3:mini (230 ms)\n")
    expect(provider.loaded(), "phi3:mini")
    expect(_out(m.cmd_list, "").splitlines()[0], "* phi3:mini     2.3 GB  phi",
           "mark the loaded model with *")

    expect_raises(m.UsageError, m.cmd_load, "", io.StringIO())
    expect_raises(m.UsageError, m.cmd_load, "   ", io.StringIO())
    expect_raises(provider.UnknownModel, m.cmd_load, "gpt4", io.StringIO())

    spy = Spy()
    m.CLIENT = spy
    m.cmd_load("gemma", io.StringIO())
    m.cmd_list("", io.StringIO())
    for name in ("list_models", "load", "loaded"):
        assert name in spy.calls, (
            f"handlers must call CLIENT.{name}(), not provider.{name}() (CLIENT saw {spy.calls})")


def test_ex04(m):
    """dispatch + COMMANDS + cmd_help: one place that catches and prints errors"""
    _fresh(m)
    out = io.StringIO()
    expect(m.dispatch("   ", out), True, "a blank line is fine")
    expect(out.getvalue(), "")

    for name in ("help", "list", "load"):
        assert name in m.COMMANDS, f"register {name!r} in COMMANDS"
    for name, entry in m.COMMANDS.items():
        assert isinstance(entry, tuple) and len(entry) == 2, \
            f"COMMANDS[{name!r}] should be a (handler, help_text) tuple, got {entry!r}"
        assert callable(entry[0]) and isinstance(entry[1], str), \
            f"COMMANDS[{name!r}] should be (function, str), got {entry!r}"

    out = io.StringIO()
    expect(m.dispatch("bogus stuff", out), False)
    expect(out.getvalue(), "unknown command: 'bogus' (try 'help')\n")

    out = io.StringIO()
    expect(m.dispatch("load gpt4", out), False)
    expect(out.getvalue(), "UnknownModel: no model matches 'gpt4'\n",
           "errors print as  TypeName: message")

    out = io.StringIO()
    expect(m.dispatch("load", out), False)
    expect(out.getvalue(), "UsageError: load <model>\n")

    out = io.StringIO()
    expect(m.dispatch("  LOAD   phi ", out), True)
    expect(out.getvalue(), "loaded phi3:mini (230 ms)\n")

    def boom(rest, out):
        return 1 / 0

    m.COMMANDS["boom"] = (boom, "crash on purpose")
    try:
        out = io.StringIO()
        expect(m.dispatch("boom", out), False, "catch ANY Exception, not just provider errors")
        expect(out.getvalue(), "ZeroDivisionError: division by zero\n")
    finally:
        del m.COMMANDS["boom"]

    lines = _out(m.cmd_help, "").splitlines()
    expect([line.split()[0] for line in lines], sorted(m.COMMANDS), "help lists every command, sorted")
    width = max(len(n) for n in m.COMMANDS)
    expect(lines[0], f"{sorted(m.COMMANDS)[0]:<{width}}  {m.COMMANDS[sorted(m.COMMANDS)[0]][1]}")


def test_ex05(m):
    """repl: prompt, readline, exit/quit/EOF, errors don't end the session"""
    _fresh(m)

    def session(script):
        out = io.StringIO()
        m.repl(io.StringIO(script), out)
        return out.getvalue()

    expect_text(session("load phi\nexit\n"), "> loaded phi3:mini (230 ms)\n> bye\n")
    expect_text(session("bogus\n"), "> unknown command: 'bogus' (try 'help')\n> \nbye\n",
           "at EOF, print a newline (the cursor is on the prompt), then bye")
    expect_text(session("\n   \nQUIT\nlist\n"), "> > > bye\n", "blank lines reprompt; quit stops")
    expect_text(session("load gpt4\nload phi\nexit\n"),
           "> UnknownModel: no model matches 'gpt4'\n> loaded phi3:mini (230 ms)\n> bye\n",
           "an error must not end the session")
    expect_text(session(""), "> \nbye\n")


def test_ex06(m):
    """cmd_run: prompt verbatim, auto-load on provider.NotLoaded"""
    _fresh(m)
    expect_text(_out(m.cmd_run, "phi tell me  a joke"),
           "(auto-loading phi3:mini)\nphi3:mini says: tell me  a joke\n[6 tokens, 182 ms]\n")
    loads = provider.call_count("load")
    expect_text(_out(m.cmd_run, 'phi3:mini say "hi"  there'),
           'phi3:mini says: say "hi"  there\n[5 tokens, 167 ms]\n',
           "already loaded: no auto-load line, prompt untouched")
    expect(provider.call_count("load"), loads, "don't load a model that's already loaded")

    expect_raises(m.UsageError, m.cmd_run, "phi", io.StringIO())
    expect_raises(m.UsageError, m.cmd_run, "", io.StringIO())
    expect_raises(provider.UnknownModel, m.cmd_run, "gpt4 hi", io.StringIO())

    provider.reset()
    spy = Spy()
    m.CLIENT = spy
    m.cmd_run("gemma hi", io.StringIO())
    for name in ("run", "load"):
        assert name in spy.calls, f"cmd_run must use CLIENT.{name}() (CLIENT saw {spy.calls})"
    assert "run" in m.COMMANDS, "register cmd_run in COMMANDS"


def test_ex07(m):
    """cmd_bench: round order from the 'round' field, min/avg/tok-per-s summary"""
    _fresh(m)
    expect_text(_out(m.cmd_bench, "phi"),
           "(auto-loading phi3:mini)\n"
           "round 1: 145 ms, 64 tokens\n"
           "round 2: 115 ms, 64 tokens\n"
           "round 3: 160 ms, 64 tokens\n"
           "min 115 ms | avg 140.0 ms | 457.1 tok/s\n")

    lines = _out(m.cmd_bench, "gemma 5").splitlines()
    expect(lines[0], "(auto-loading gemma2:2b)")
    expect([line.split(":")[0] for line in lines[1:6]],
           ["round 1", "round 2", "round 3", "round 4", "round 5"],
           "print rounds in round order (the provider returns completion order)")
    expect(lines[6], "min 80 ms | avg 101.0 ms | 633.7 tok/s")

    for bad in ("", "phi x", "phi 0", "phi 2 3"):
        expect_raises(m.UsageError, m.cmd_bench, bad, io.StringIO())
    assert "bench" in m.COMMANDS, "register cmd_bench in COMMANDS"


def test_ex08(m):
    """ProviderClient: one chokepoint (_call) for every provider call"""
    _fresh(m)
    c = m.ProviderClient()
    expected_models = provider.list_models()
    expect(c.list_models(), expected_models)
    expect(c.load("phi3:mini"), {"name": "phi3:mini", "load_ms": 230})
    expect(c.loaded(), "phi3:mini")
    expect(c.run("phi3:mini", "hi")["text"], "phi3:mini says: hi")
    expect(len(c.benchmark("phi3:mini", 2)), 2)
    expect(c.unload(), "phi3:mini")
    expect(dict(c.calls), {"list_models": 1, "load": 1, "loaded": 1, "run": 1,
                           "benchmark": 1, "unload": 1})

    expect_raises(provider.UnknownModel, c.load, "nope")
    expect_raises(provider.NotLoaded, c.run, "phi3:mini", "hi")

    seen = []

    class Probe(m.ProviderClient):
        def _call(self, fn, *args):
            seen.append(fn.__name__)
            return super()._call(fn, *args)

    p = Probe()
    p.list_models(); p.load("gemma2:2b"); p.loaded(); p.run("gemma2:2b", "x")
    p.benchmark("gemma2:2b"); p.unload()
    expect(seen, ["list_models", "load", "loaded", "run", "benchmark", "unload"],
           "every method must go through self._call(provider.<fn>, ...)")


def test_ex09(m):
    """RetryingClient: retry only provider.Timeout, exponential backoff"""
    _fresh(m)
    slept = []
    c = m.RetryingClient(sleep=slept.append)
    provider.load("phi3:mini")

    provider.set_flaky(2, only="run")
    expect(c.run("phi3:mini", "hi")["text"], "phi3:mini says: hi")
    expect(slept, [0.1, 0.2], "sleep base_delay * 2**i between attempts")
    expect(provider.call_count("run"), 3)
    assert isinstance(c.calls, dict), "call super().__init__() so self.calls exists"

    slept.clear()
    provider.set_flaky(3, only="run")
    expect_raises(provider.Timeout, c.run, "phi3:mini", "hi")
    expect(slept, [0.1, 0.2], "no sleep after the final attempt")

    slept.clear()
    loads = provider.call_count("load")
    expect_raises(provider.UnknownModel, c.load, "nope")
    expect(provider.call_count("load") - loads, 1, "never retry UnknownModel")
    provider.unload()
    expect_raises(provider.NotLoaded, c.run, "phi3:mini", "hi")
    expect(slept, [], "never retry UnknownModel / NotLoaded")

    slow = []
    c5 = m.RetryingClient(attempts=5, base_delay=1, sleep=slow.append)
    provider.set_flaky(4, only="list_models")
    expect(len(c5.list_models()), 5)
    expect(slow, [1, 2, 4, 8])


def test_ex10(m):
    """CachingClient: TTL cache with an injected clock, stale-on-error"""
    _fresh(m)
    expected = provider.list_models()
    base = provider.call_count("list_models")

    def fetched():
        return provider.call_count("list_models") - base

    now = [0.0]
    slept = []
    c = m.CachingClient(ttl=30, clock=lambda: now[0], sleep=slept.append)
    expect(c.list_models(), expected)
    expect(c.list_models(), expected)
    expect(fetched(), 1, "second call within the TTL should hit the cache")
    now[0] = 29.9
    c.list_models()
    expect(fetched(), 1, "29.9s old is still fresh (ttl=30)")
    now[0] = 30.5
    c.list_models()
    expect(fetched(), 2, "older than the TTL: fetch again")

    now[0] = 100
    provider.set_flaky(1, only="list_models")
    expect(c.list_models(), expected, "the refresh goes through the retrying _call")
    expect(slept, [0.1])

    now[0] = 200
    provider.set_flaky(10, only="list_models")
    expect(c.list_models(), expected, "refresh failed after retries: serve the stale copy")
    provider.set_flaky(0)

    cold = m.CachingClient(clock=lambda: 0.0, sleep=lambda s: None)
    provider.set_flaky(10, only="list_models")
    expect_raises(provider.Timeout, cold.list_models)

    once = m.CachingClient(attempts=1, clock=lambda: 0.0, sleep=slept.append)
    provider.set_flaky(1, only="list_models")
    expect_raises(provider.Timeout, once.list_models)   # attempts=1 must reach RetryingClient
    provider.set_flaky(0)

    expect(c.load("phi3:mini")["name"], "phi3:mini", "other methods still pass through")


def test_ex11(m):
    """main: direct argv mode vs REPL, exit codes, installing a client"""
    _fresh(m)

    def call(argv, script="", client=None):
        out = io.StringIO()
        code = m.main(argv, io.StringIO(script), out, client)
        return code, out.getvalue()

    expect(call(["run", "phi", "hello"]),
           (0, "(auto-loading phi3:mini)\nphi3:mini says: hello\n[3 tokens, 137 ms]\n"))
    expect(call(["run", "phi", "tell me  a joke"])[1].splitlines()[0],
           "phi3:mini says: tell me  a joke", "a quoted shell arg keeps its inner spaces")
    expect(call(["bogus"]), (1, "unknown command: 'bogus' (try 'help')\n"))
    expect(call(["load", "gpt4"]), (1, "UnknownModel: no model matches 'gpt4'\n"))

    _fresh(m)
    expect(call([], "load phi\nexit\n"), (0, "> loaded phi3:mini (230 ms)\n> bye\n"))

    spy = Spy()
    expect(call(["list"], client=spy)[0], 0)
    assert m.CLIENT is spy, "main(client=...) must rebind the module's CLIENT (global CLIENT)"
    assert "list_models" in spy.calls, f"commands should run through the new client, saw {spy.calls}"


FASTEST_2_ROUNDS = (
    "1. gemma2:2b       95.0 ms\n"
    "2. phi3:mini      130.0 ms\n"
    "3. mistral:7b     220.0 ms\n"
    "4. llama3:8b      250.0 ms\n"
    "5. llama3:70b    1965.0 ms\n"
)


def test_ex12(m):
    """cmd_fastest: rank all models, degrade on failure, restore the session"""
    _fresh(m)
    expect_text(_out(m.cmd_fastest, ""), FASTEST_2_ROUNDS)
    expect(provider.loaded(), None, "nothing was loaded before, so nothing after")

    provider.load("phi3:mini")
    provider.set_flaky(1, only="benchmark", model="mistral:7b")
    expect(_out(m.cmd_fastest, "").splitlines(), [
        "1. gemma2:2b       95.0 ms",
        "2. phi3:mini      130.0 ms",
        "3. llama3:8b      250.0 ms",
        "4. llama3:70b    1965.0 ms",
        "failed: mistral:7b (Timeout)",
    ], "one failing model must not kill the ranking")
    expect(provider.loaded(), "phi3:mini", "restore the model that was loaded before")

    expect(_out(m.cmd_fastest, "3").splitlines()[0], "1. gemma2:2b      105.0 ms")

    provider.set_flaky(100, only="benchmark")
    expect_text(_out(m.cmd_fastest, ""),
           "no results\nfailed: phi3:mini (Timeout), gemma2:2b (Timeout), mistral:7b (Timeout), "
           "llama3:8b (Timeout), llama3:70b (Timeout)\n")
    provider.set_flaky(0)

    for bad in ("x", "0"):
        expect_raises(m.UsageError, m.cmd_fastest, bad, io.StringIO())

    class Crashy(Spy):
        def benchmark(self, name, rounds):
            raise RuntimeError("bug in someone else's code")

    provider.load("gemma2:2b")
    m.CLIENT = Crashy()
    expect_raises(RuntimeError, m.cmd_fastest, "", io.StringIO())
    expect(provider.loaded(), "gemma2:2b", "restore the session even when a non-provider error escapes")
    assert "fastest" in m.COMMANDS, "register cmd_fastest in COMMANDS"
