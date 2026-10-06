import json

import provider
from harness import expect, expect_raises


def test_ex01(m):
    """safe_int: catch ValueError and TypeError"""
    expect(m.safe_int("42"), 42)
    expect(m.safe_int(" -7\n"), -7)
    expect(m.safe_int("4.2"), None)
    expect(m.safe_int(""), None)
    expect(m.safe_int("abc"), None)
    expect(m.safe_int(None), None, "int(None) raises TypeError, not ValueError")


def test_ex02(m):
    """read_command: except (EOFError, KeyboardInterrupt)"""
    prompts = []

    def typed(prompt):
        prompts.append(prompt)
        return "  list \n"

    def ctrl_d(prompt):
        raise EOFError

    def ctrl_c(prompt):
        raise KeyboardInterrupt

    expect(m.read_command(typed), "list")
    expect(prompts, ["> "], "call read() with the prompt '> '")
    expect(m.read_command(ctrl_d), None)
    try:
        result = m.read_command(ctrl_c)
    except KeyboardInterrupt:
        raise AssertionError("KeyboardInterrupt escaped; catch it alongside EOFError "
                             "(it is NOT a subclass of Exception)") from None
    expect(result, None)


def test_ex03(m):
    """temp_or_none: catch the namespaced provider.UnknownCity"""
    expect(m.temp_or_none("Durham"), 21.5)
    expect(m.temp_or_none("  new york "), 15.8)
    expect(m.temp_or_none("Atlantis"), None)
    flaky = provider.FlakyProvider(fail_times=1)
    expect_raises(provider.Timeout, m.temp_or_none, "durham", flaky.get_temp)
    expect(m.temp_or_none("durham", flaky.get_temp), 21.5)


def test_ex04(m):
    """describe_error: type(e).__name__ plus the message"""
    expect(m.describe_error(provider.UnknownCity("no data for 'Oslo'")),
           "error: UnknownCity: no data for 'Oslo'")
    expect(m.describe_error(KeyError("phi3")), "error: KeyError: 'phi3'")
    expect(m.describe_error(ZeroDivisionError("division by zero")),
           "error: ZeroDivisionError: division by zero")
    expect(m.describe_error(ValueError()), "error: ValueError")


def test_ex05(m):
    """port_for: EAFP over a nested lookup"""
    cfg = {"services": {"ollama": {"port": "11434"}, "jellyfin": {"port": 8096}}}
    expect(m.port_for(cfg, "ollama"), 11434)
    expect(m.port_for(cfg, "jellyfin"), 8096)
    expect(m.port_for(cfg, "komga"), 8080)
    expect(m.port_for(cfg, "komga", default=25600), 25600)
    expect(m.port_for({}, "ollama"), 8080)
    expect(m.port_for({"services": None}, "ollama"), 8080, "None[...] raises TypeError")
    expect(m.port_for({"services": {"ollama": {}}}, "ollama"), 8080)
    expect(m.port_for({"services": {"ollama": {"port": "abc"}}}, "ollama"), 8080)


def test_ex06(m):
    """forget: contextlib.suppress inside the loop"""
    cache = {"a": 1, "b": 2, "c": 3}
    expect(m.forget(cache, ["a", "missing", "c"]), None)
    expect(cache, {"b": 2}, "a missing key must not stop later deletes")
    m.forget(cache, [])
    expect(cache, {"b": 2})
    m.forget(cache, ["b", "b"])
    expect(cache, {})


def test_ex07(m):
    """traced: try / except / else / finally order"""
    log = []
    expect(m.traced(lambda: 42, log), 42)
    expect(log, ["try", "else", "finally"])

    log = []
    expect(m.traced(lambda: None, log), None)
    expect(log, ["try", "else", "finally"])

    def bad_value():
        raise ValueError("nope")

    log = []
    expect(m.traced(bad_value, log), None)
    expect(log, ["try", "except", "finally"])

    def bad_key():
        raise KeyError("k")

    log = []
    expect_raises(KeyError, m.traced, bad_key, log)
    expect(log, ["try", "finally"])


def _commands():
    def cmd_temp(args):
        return provider.get_temp(" ".join(args))

    def cmd_add(args):
        a, b = args
        return int(a) + int(b)

    return {
        "temp": (cmd_temp, "temp <city>  current temperature"),
        "add": (cmd_add, "add <a> <b>  add two ints"),
    }


def test_ex08(m):
    """repl_step: dict dispatch, never crash, global LAST_ERROR"""
    cmds = _commands()
    expect(m.repl_step('temp "New York"', cmds), "15.8")
    assert m.LAST_ERROR is None
    expect(m.repl_step("add 2 3", cmds), "5")

    expect(m.repl_step("temp Atlantis", cmds), "error: UnknownCity: no data for 'Atlantis'")
    assert isinstance(m.LAST_ERROR, provider.UnknownCity), \
        f"LAST_ERROR should hold the caught exception, got {m.LAST_ERROR!r} (did you use `global`?)"

    out = m.repl_step("add 2", cmds)
    assert out.startswith("error: ValueError: "), f"got {out!r}"
    expect(m.repl_step("add 2 x", cmds), "error: ValueError: invalid literal for int() with base 10: 'x'")
    expect(m.repl_step('temp "unclosed', cmds), "error: ValueError: No closing quotation")

    expect(m.repl_step("fly", cmds), "unknown command: fly")
    assert m.LAST_ERROR is None, "a step that doesn't fail resets LAST_ERROR to None"
    expect(m.repl_step("   ", cmds), "")
    expect(m.repl_step("help", cmds),
           "add: add <a> <b>  add two ints\ntemp: temp <city>  current temperature")


def test_ex09(m):
    """BookingConflict: custom exception hierarchy with attributes"""
    e = m.BookingConflict("A", 9, 11)
    expect((e.room, e.start, e.end), ("A", 9, 11))
    expect(str(e), "room A is already booked 9-11", "call super().__init__(message)")
    assert isinstance(e, m.BookingError)

    b = {}
    m.book(b, "A", 9, 11)
    m.book(b, "A", 11, 12)
    m.book(b, "B", 9, 11)
    expect(b, {"A": [(9, 11), (11, 12)], "B": [(9, 11)]})

    err = expect_raises(m.BookingConflict, m.book, b, "A", 10, 13)
    expect((err.room, err.start, err.end), ("A", 9, 11), "report the EXISTING booking that was hit")
    expect_raises(m.BookingError, m.book, b, "A", 8, 10)  # catching the base class works
    expect_raises(m.InvalidBooking, m.book, b, "C", 10, 10)
    expect_raises(m.InvalidBooking, m.book, b, "C", 10, 9)
    expect(b, {"A": [(9, 11), (11, 12)], "B": [(9, 11)]}, "failed bookings must not change anything")


def test_ex10(m):
    """load_config: raise ... from e, and from None"""
    expect(m.load_config('{"model": "phi3"}'), {"model": "phi3", "timeout": 30})
    expect(m.load_config('{"model": "phi3", "timeout": 5}'), {"model": "phi3", "timeout": 5})

    e = expect_raises(m.ConfigError, m.load_config, '{"model": ')
    assert str(e).startswith("invalid JSON: "), f"got {str(e)!r}"
    assert isinstance(e.__cause__, json.JSONDecodeError), \
        f"use `raise ... from e`; __cause__ is {e.__cause__!r}"

    e = expect_raises(m.ConfigError, m.load_config, "[1, 2]")
    expect(str(e), "config must be a JSON object")

    e = expect_raises(m.ConfigError, m.load_config, '{"timeout": 5}')
    expect(str(e), "missing key: model")
    assert e.__cause__ is None
    assert e.__suppress_context__ is True, "use `raise ... from None` to hide the KeyError"


def test_ex11(m):
    """run_job: try/finally release + bare raise"""
    pool, log = ["w1", "w2"], []
    expect(m.run_job(pool, lambda w: f"ran on {w}", log), "ran on w2")
    expect(sorted(pool), ["w1", "w2"])
    expect(log, [])

    boom = ValueError("boom")

    def fails(worker):
        assert worker not in pool, "the worker should be out of the pool while fn runs"
        raise boom

    got = expect_raises(ValueError, m.run_job, pool, fails, log)
    assert got is boom, "re-raise the SAME exception object, don't wrap it"
    expect(sorted(pool), ["w1", "w2"], "the worker must come back even when fn raises")
    expect(log, ["w2: ValueError: boom"])

    empty = []
    expect_raises(RuntimeError, m.run_job, empty, lambda w: 1, log)
    expect(empty, [])


def test_ex12(m):
    """loaded: @contextmanager with try/finally around yield"""
    log = []
    with m.loaded("phi3", log) as model:
        expect(model, "phi3")
        expect(log, ["load phi3"])
    expect(log, ["load phi3", "unload phi3"])

    log = []
    boom = ValueError("bad prompt")

    def body_raises():
        with m.loaded("phi3", log):
            raise boom

    got = expect_raises(ValueError, body_raises)
    assert got is boom
    expect(log, ["load phi3", "failed phi3: ValueError", "unload phi3"])

    log = []

    def blank_name():
        with m.loaded("  ", log):
            pass

    expect_raises(ValueError, blank_name)
    expect(log, [])


def test_ex13(m):
    """retry: exponential backoff with an injected sleep"""
    p, delays = provider.FlakyProvider(fail_times=2), []
    expect(m.retry(lambda: p.get_temp("durham"), attempts=4, base_delay=0.5, sleep=delays.append), 21.5)
    expect(delays, [0.5, 1.0])
    expect(p.calls, 3)

    p, delays = provider.FlakyProvider(fail_times=5), []
    e = expect_raises(provider.Timeout, m.retry, lambda: p.get_temp("durham"),
                      attempts=3, base_delay=0.1, sleep=delays.append)
    expect(delays, [0.1, 0.2], "no sleep after the final attempt")
    expect(p.calls, 3)
    expect(str(e), "timed out on call 3", "re-raise the LAST exception")

    p, delays = provider.FlakyProvider(), []
    expect_raises(provider.UnknownCity, m.retry, lambda: p.get_temp("atlantis"), sleep=delays.append)
    expect(delays, [], "UnknownCity isn't retryable: fail fast")
    expect(p.calls, 1)

    p, delays = provider.FlakyProvider(fail_times=1), []
    expect(m.retry(lambda: p.get_temp("cary"), retry_on=(provider.ProviderError,),
                   sleep=delays.append), 22.1, "a base class in retry_on catches subclasses")
    expect(delays, [0.5])

    delays = []
    expect(m.retry(lambda: "ok", attempts=1, sleep=delays.append), "ok")
    expect(delays, [])
    expect_raises(ValueError, m.retry, lambda: "ok", attempts=0, sleep=delays.append)


def test_ex14(m):
    """validate_booking: collect every error, raise one ValidationError"""
    e = m.ValidationError(["a: bad", "b: worse"])
    expect(e.errors, ["a: bad", "b: worse"])
    expect(str(e), "a: bad; b: worse")
    assert isinstance(e, ValueError)

    expect(m.validate_booking({"room": " A ", "start": 9, "end": 11}),
           {"room": "A", "start": 9, "end": 11, "attendees": 1})
    expect(m.validate_booking({"room": "B", "start": 0, "end": 24, "attendees": 5}),
           {"room": "B", "start": 0, "end": 24, "attendees": 5})

    e = expect_raises(m.ValidationError, m.validate_booking,
                      {"room": "  ", "start": 25, "end": "11", "attendees": 0})
    expect(e.errors, ["room: required", "start: must be an int 0-24",
                      "end: must be an int 0-24", "attendees: must be a positive int"])
    expect(str(e), "room: required; start: must be an int 0-24; "
                   "end: must be an int 0-24; attendees: must be a positive int")

    e = expect_raises(m.ValidationError, m.validate_booking, {"room": "A", "start": 11, "end": 9})
    expect(e.errors, ["end: must be after start"])

    e = expect_raises(m.ValidationError, m.validate_booking, {})
    expect(e.errors, ["room: required", "start: must be an int 0-24", "end: must be an int 0-24"])

    e = expect_raises(ValueError, m.validate_booking, {"room": 5, "start": 9, "end": 10})
    expect(e.errors, ["room: required"], "catchable as ValueError; a non-str room is invalid")
