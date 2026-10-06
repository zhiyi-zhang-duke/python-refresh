import copy
import types

from harness import expect, expect_raises


def _fake_provider():
    """A stand-in for `import provider`: a module object with a function and an exception."""
    provider = types.ModuleType("provider")

    class UnknownCity(Exception):
        pass

    temps = {"New York": 61, "Durham": 75}

    def get_temp(city):
        if city == "Offline Town":
            raise ConnectionError("network down")
        if city not in temps:
            raise UnknownCity(city)
        return temps[city]

    provider.UnknownCity = UnknownCity
    provider.get_temp = get_temp
    return provider


def test_ex01(m):
    """load_model / unload_model: `global` to rebind a module variable"""
    m.LOADED_MODEL = None
    expect(m.load_model("phi3"), None, "returns the previous model")
    expect(m.LOADED_MODEL, "phi3", "the MODULE's LOADED_MODEL must change (did you use `global`?)")
    expect(m.load_model("llama3"), "phi3")
    expect(m.LOADED_MODEL, "llama3")
    expect(m.unload_model(), "llama3")
    assert m.LOADED_MODEL is None, "unload_model must set the module's LOADED_MODEL to None"
    expect(m.unload_model(), None)


def test_ex02(m):
    """model_status: `is None` for None, `==` for strings"""
    expect(m.model_status(None, "phi3"), "load phi3")
    expect(m.model_status("phi3", "phi3"), "already loaded")
    expect(m.model_status("phi3", "llama3"), "switch phi3 -> llama3")
    typed = "".join(["phi", "3:", "mini"])  # built at runtime, like input() would be
    expect(m.model_status(typed, "phi3:mini"), "already loaded",
           "equal strings can be different objects: compare with ==, not `is`")
    expect(m.model_status("phi3:mini", typed), "already loaded")


def test_ex03(m):
    """is_yes: `x == a or b` and substring-`in` traps"""
    assert m.is_yes("y") is True
    assert m.is_yes("  YES\n") is True
    assert m.is_yes("Yes") is True
    assert m.is_yes("no") is False, '`a == "y" or "yes"` is always truthy'
    assert m.is_yes("") is False, '"" in "yes" is True (substring test)'
    assert m.is_yes("es") is False, '"es" in "yes" is True (substring test)'
    assert m.is_yes("yess") is False


def test_ex04(m):
    """make_grid: rows must be independent lists"""
    grid = m.make_grid(3, 2)
    expect(grid, [[0, 0], [0, 0], [0, 0]])
    grid[0][0] = 1
    expect(grid, [[1, 0], [0, 0], [0, 0]], "changing one row changed others: [[0]*c]*r aliasing")
    assert grid[1] is not grid[2], "each row must be a separate list object"
    expect(m.make_grid(1, 3, "."), [[".", ".", "."]])
    expect(m.make_grid(0, 4), [])


def test_ex05(m):
    """parse_command: `cmd, *args = parts` and the empty case"""
    expect(m.parse_command("  Weather New York "), ("weather", ["New", "York"]))
    expect(m.parse_command("list"), ("list", []), "starred target gives an empty LIST")
    expect(m.parse_command(""), ("", []))
    expect(m.parse_command(" \t\n"), ("", []))


def test_ex06(m):
    """log_event: no shared mutable default, and keep the caller's empty list"""
    expect(m.log_event("a"), ["a"])
    expect(m.log_event("b"), ["b"], "state leaked between calls: mutable default argument")
    h = []
    result = m.log_event("x", h)
    assert result is h, "append to the list the caller passed, even an empty one (`or []` bug)"
    expect(h, ["x"])
    m.log_event("y", h)
    expect(h, ["x", "y"])
    expect(m.log_event("c"), ["c"])


def test_ex07(m):
    """resolve_settings: 0 and "" are valid values, only None/missing means default"""
    defaults_before = dict(m.DEFAULTS)
    expect(m.resolve_settings({"timeout": 0, "prompt": ""}),
           {"timeout": 0, "retries": 3, "prompt": ""},
           "0 and \"\" are deliberate values; `or default` replaces them")
    expect(m.resolve_settings({"retries": None, "x": 1}),
           {"timeout": 30, "retries": 3, "prompt": "> "})
    expect(m.resolve_settings({"timeout": 5, "retries": 0, "prompt": "$ "}),
           {"timeout": 5, "retries": 0, "prompt": "$ "})
    expect(m.resolve_settings({}), defaults_before)
    expect(m.DEFAULTS, defaults_before, "don't mutate DEFAULTS")


def test_ex08(m):
    """make_callbacks: closures in a loop must each keep their own value"""
    cbs = m.make_callbacks(["save", "load", "quit"])
    expect(sorted(cbs), ["load", "quit", "save"])
    expect([cbs["save"](), cbs["load"](), cbs["quit"]()],
           ["clicked save", "clicked load", "clicked quit"],
           "all callbacks saw the last label: late-binding closure")
    expect(m.make_callbacks([]), {})


def test_ex09(m):
    """make_rate_limiter: nonlocal counter, independent per limiter"""
    a = m.make_rate_limiter(2)
    b = m.make_rate_limiter(1)
    expect([a(), a()], [True, True])
    expect(b(), True, "limiters must not share a count")
    expect([a(), b(), a()], [False, False, False])
    z = m.make_rate_limiter(0)
    expect(z(), False)


def test_ex10(m):
    """weather_command: join args, catch provider.UnknownCity only"""
    provider = _fake_provider()
    expect(m.weather_command(["New", "York"], provider), "New York: 61F")
    expect(m.weather_command(["Durham"], provider), "Durham: 75F")
    expect(m.weather_command(["Narnia"], provider), "unknown city: Narnia")
    expect(m.weather_command([], provider), "usage: weather <city>")
    expect_raises(ConnectionError, m.weather_command, ["Offline", "Town"], provider)


def test_ex11(m):
    """apply_override: deepcopy before mutating nested config"""
    base = {"model": {"name": "phi3", "params": {"temp": 0.7}}, "tags": ["a"]}
    snapshot = copy.deepcopy(base)

    result = m.apply_override(base, "model.params.temp", 0.2)
    expect(result, {"model": {"name": "phi3", "params": {"temp": 0.2}}, "tags": ["a"]})
    expect(base, snapshot, "the original config changed: shallow copy")
    assert result["tags"] is not base["tags"], "result shares a nested list with the original"
    assert result["model"] is not base["model"], "result shares a nested dict with the original"

    expect(m.apply_override(base, "server.port", 8080)["server"], {"port": 8080},
           "missing intermediate dicts are created")
    expect(m.apply_override(base, "debug", True)["debug"], True)
    expect(base, snapshot)


def test_ex12(m):
    """drop_inactive: remove in place without skipping elements"""
    sessions = [
        {"id": 1, "start": 0, "end": 5},
        {"id": 2, "start": 0, "end": 3},
        {"id": 3, "start": 0, "end": 2},   # right after a removal: the skip bug misses it
        {"id": 4, "start": 4, "end": 9},
        {"id": 5, "start": 5, "end": 9},   # not started yet
        {"id": 6, "start": 1, "end": 4},   # end is exclusive
    ]
    expect(m.drop_inactive(sessions, 4), 4,
           "too few removed? .remove() inside `for s in sessions` skips the next element")
    expect([s["id"] for s in sessions], [1, 4],
           "the CALLER's list must be updated (mutate it; rebinding the parameter doesn't)")
    empty = []
    expect(m.drop_inactive(empty, 0), 0)


def test_ex13(m):
    """format_offset: floor division and % with negatives"""
    expect(m.format_offset(330), "+05:30")
    expect(m.format_offset(-90), "-01:30", "divmod(-90, 60) is (-2, 30)")
    expect(m.format_offset(-45), "-00:45")
    expect(m.format_offset(0), "+00:00")
    expect(m.format_offset(-600), "-10:00")
    expect(m.format_offset(59), "+00:59")


def test_ex14(m):
    """order_tickets: multi-key sort with mixed directions, stable ties"""
    tickets = [
        {"id": "t1", "team": "api", "title": "b"},
        {"id": "t2", "team": "web", "title": "z"},
        {"id": "t3", "team": "api", "title": "a"},
        {"id": "t4", "team": "web", "title": "c"},
        {"id": "t5", "team": "api", "title": "a"},
        {"id": "t6", "team": "db", "title": "m"},
    ]
    expect(m.order_tickets(tickets), ["t4", "t2", "t6", "t3", "t5", "t1"],
           "team Z->A, title A->Z, exact ties (t3, t5) keep input order")
    expect([t["id"] for t in tickets], ["t1", "t2", "t3", "t4", "t5", "t6"], "don't reorder the input")
    expect(m.order_tickets([]), [])
