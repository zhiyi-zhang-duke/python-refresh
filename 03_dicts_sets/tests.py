import provider
from harness import expect, expect_raises


def test_ex01(m):
    """get_price: dict.get with a default"""
    prices = {"apple": 0.5, "free sample": 0.0}
    expect(m.get_price(prices, "  Apple\n"), 0.5)
    expect(m.get_price(prices, "kiwi"), 0.0)
    expect(m.get_price(prices, "Free Sample"), 0.0)
    expect(m.get_price({}, "apple"), 0.0)


def test_ex02(m):
    """count_levels: counting by hand with .get(k, 0) + 1"""
    expect(m.count_levels(m.LOG_LINES), {"INFO": 2, "ERROR": 6, "WARNING": 1})
    expect(m.count_levels([]), {})
    expect(m.count_levels(["   ", "2026-01-01 00:00:00 DEBUG [x] y"]), {"DEBUG": 1},
           "whitespace-only lines are blank too")


def test_ex03(m):
    """merge_config: | merge, ignoring None overrides"""
    defaults = {"unit": "F", "days": 3, "verbose": True}
    overrides = {"days": 5, "unit": None, "verbose": False}
    expect(m.merge_config(defaults, overrides), {"unit": "F", "days": 5, "verbose": False},
           "False is a real override; only None means 'not set'")
    expect(defaults, {"unit": "F", "days": 3, "verbose": True}, "defaults was modified")
    expect(overrides, {"days": 5, "unit": None, "verbose": False}, "overrides was modified")
    expect(m.merge_config({}, {"new": 1}), {"new": 1})


def test_ex04(m):
    """switch_profile: `global` to rebind, plain mutation for the dict"""
    m.ACTIVE_PROFILE = "default"
    for p in m.PROFILES.values():
        p["uses"] = 0
    expect(m.switch_profile(" Metric "), {"unit": "C", "uses": 1})
    expect(m.ACTIVE_PROFILE, "metric", "module-level ACTIVE_PROFILE didn't change: missing `global`?")
    m.switch_profile("metric")
    expect(m.PROFILES["metric"]["uses"], 2)
    expect_raises(KeyError, m.switch_profile, "imperial")
    expect(m.ACTIVE_PROFILE, "metric", "an unknown profile must not change ACTIVE_PROFILE")


def test_ex05(m):
    """top_sources: Counter.most_common over ERROR lines"""
    expect(m.top_sources(m.LOG_LINES, 2), [("provider", 3), ("cli", 2)])
    expect(m.top_sources(m.LOG_LINES, 10), [("provider", 3), ("cli", 2), ("db", 1)])
    lines = ["2026-01-01 00:00:00 ERROR [zeta] a", "2026-01-01 00:00:01 ERROR [alpha] b"]
    expect(m.top_sources(lines, 2), [("zeta", 1), ("alpha", 1)], "ties keep first-seen order")
    expect(m.top_sources([], 3), [])


def test_ex06(m):
    """group_by_provider: defaultdict(list) / setdefault grouping"""
    out = m.group_by_provider(m.MODELS)
    expect(out, {"ollama": ["phi3:mini", "llama3:70b"], "openai": ["gpt-4o"],
                 "unknown": ["mystery-7b"]})
    assert type(out) is dict, f"return a plain dict, got {type(out).__name__}"
    expect(m.group_by_provider([]), {})


def test_ex07(m):
    """invert: value -> sorted keys, no collisions lost"""
    aliases = {"fast": "phi3", "small": "phi3", "big": "llama3", "default": "phi3"}
    expect(m.invert(aliases), {"phi3": ["default", "fast", "small"], "llama3": ["big"]})
    expect(m.invert({}), {})


def test_ex08(m):
    """diff_hosts: set union / intersection / difference / symmetric difference"""
    local = ["phi3", "llama3", "phi3", "qwen"]
    remote = ["llama3", "mistral", "gemma"]
    expect(m.diff_hosts(local, remote), {
        "both": ["llama3"],
        "only_local": ["phi3", "qwen"],
        "only_remote": ["gemma", "mistral"],
        "out_of_sync": ["gemma", "mistral", "phi3", "qwen"],
        "all": ["gemma", "llama3", "mistral", "phi3", "qwen"],
    })
    expect(m.diff_hosts([], []), {"both": [], "only_local": [], "only_remote": [],
                                  "out_of_sync": [], "all": []})


def test_ex09(m):
    """rank_by_value: sort items by value desc, key asc"""
    expect(m.rank_by_value({"cy": 5, "al": 9, "bo": 5}), [("al", 9), ("bo", 5), ("cy", 5)])
    expect(m.rank_by_value({"x": -1, "y": 0}), [("y", 0), ("x", -1)])
    expect(m.rank_by_value({}), [])


CONFIG = {
    "providers": {
        "ollama": {"host": "localhost", "port": 11434,
                   "models": [{"name": "phi3"}, {"name": "llama3"}]},
        "openai": {"key": None},
    },
    "debug": False,
}


def test_ex10(m):
    """get_path: safe nested lookup through dicts and lists"""
    expect(m.get_path(CONFIG, "providers.ollama.port"), 11434)
    expect(m.get_path(CONFIG, "providers.ollama.models.1.name"), "llama3")
    expect(m.get_path(CONFIG, "providers.openai.port", 80), 80)
    expect(m.get_path(CONFIG, "debug", "x"), False, "existing falsy values are returned")
    expect(m.get_path(CONFIG, "providers.openai.key", "x"), None, "an existing None is returned")
    expect(m.get_path(CONFIG, "providers.ollama.models.9.name", "x"), "x", "index out of range")
    expect(m.get_path(CONFIG, "providers.ollama.models.first", "x"), "x", "non-digit into a list")
    expect(m.get_path(CONFIG, "providers.ollama.host.length", "x"), "x", "can't descend into a str")
    expect(m.get_path(CONFIG, "providers.ollama.port.0", "x"), "x", "can't descend into an int")


def _feeder(lines, end=EOFError):
    """Fake input(): returns each line, then raises `end` like Ctrl-D / Ctrl-C would."""
    it = iter(lines)

    def read_line():
        try:
            return next(it)
        except StopIteration:
            raise end from None

    return read_line


def _boom(args):
    raise ZeroDivisionError("handler bug")


def test_ex11(m):
    """cmd_weather + run_repl: dispatch table, entry[0](args), namespaced exceptions"""
    expect(m.cmd_weather(["New", "York"]), "New York: 65F")
    expect(m.cmd_weather(["durham"]), "durham: 72F")
    expect_raises(ValueError, m.cmd_weather, [])
    expect_raises(provider.UnknownCity, m.cmd_weather, ["Atlantis"])

    commands = {
        "weather": (m.cmd_weather, "weather <city>"),
        "echo": (lambda args: " ".join(args), "echo <words>"),
        "boom": (_boom, "boom"),
    }
    session = [
        "  weather San Luis Obispo\n",
        "",
        'WEATHER "new york"',
        "weather",
        "weather Atlantis",
        "lod phi3",
        'echo "unclosed',
        "echo  a   b ",
    ]
    expect(m.run_repl(_feeder(session), commands), [
        "San Luis Obispo: 68F",
        "new york: 65F",
        "usage: weather <city>",
        "unknown city: Atlantis",
        "unknown command: lod",
        "error: unbalanced quotes",
        "a b",
    ])
    expect(m.run_repl(_feeder(["echo hi", "quit", "echo never"]), commands), ["hi"],
           "quit stops the loop")
    expect(m.run_repl(_feeder(["echo hi", " EXIT "]), commands), ["hi"])
    expect(m.run_repl(_feeder(["echo hi"], end=KeyboardInterrupt), commands), ["hi"],
           "Ctrl-C (KeyboardInterrupt) should end the REPL cleanly")
    expect(m.run_repl(_feeder([]), commands), [])
    expect_raises(ZeroDivisionError, m.run_repl, _feeder(["boom"]), commands)


def test_ex12(m):
    """deep_merge: recursive merge, no shared nested objects"""
    base = {"db": {"host": "a", "port": 1, "opts": {"ssl": True}}, "tags": [1], "name": "x"}
    override = {"db": {"port": 2, "opts": {"timeout": 5}}, "tags": [2], "extra": {"k": [1]}}
    out = m.deep_merge(base, override)
    expect(out, {
        "db": {"host": "a", "port": 2, "opts": {"ssl": True, "timeout": 5}},
        "tags": [2],
        "name": "x",
        "extra": {"k": [1]},
    })
    expect(base["db"], {"host": "a", "port": 1, "opts": {"ssl": True}}, "base was modified")
    expect(override["db"], {"port": 2, "opts": {"timeout": 5}}, "override was modified")
    out["db"]["opts"]["ssl"] = False
    out["extra"]["k"].append(99)
    expect(base["db"]["opts"]["ssl"], True, "result shares a nested dict with base")
    expect(override["extra"]["k"], [1], "result shares a nested list with override")
    expect(m.deep_merge({"a": {"b": 1}}, {"a": 5}), {"a": 5}, "a non-dict override replaces a dict")
    expect(m.deep_merge({"a": 5}, {"a": {"b": 1}}), {"a": {"b": 1}})


def test_ex13(m):
    """LRUCache: OrderedDict with move_to_end / popitem(last=False)"""
    c = m.LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    expect(c.get("a"), 1)
    c.put("c", 3)
    expect(c.keys(), ["a", "c"], "'b' was least recently used and should be evicted")
    expect(c.get("b"), None)
    expect(c.get("b", -1), -1)
    c.put("a", 10)
    expect((c.keys(), c.get("a")), (["c", "a"], 10), "put on an existing key updates and refreshes it")
    expect(len(c), 2)
    c.put("d", 4)
    expect(c.keys(), ["a", "d"])
    expect_raises(ValueError, m.LRUCache, 0)
    one = m.LRUCache(1)
    one.put("x", 1)
    one.put("y", 2)
    expect((one.keys(), len(one)), (["y"], 1))


FLIGHTS = [
    ("RDU", "ATL"), ("RDU", "CLT"), ("ATL", "LAX"), ("ATL", "RDU"),
    ("CLT", "ORD"), ("ORD", "SEA"), ("LAX", "HNL"), ("SEA", "ANC"),
]


def test_ex14(m):
    """shortest_route: dict-of-sets graph + BFS"""
    expect(m.shortest_route(FLIGHTS, "RDU", "ATL"), ["RDU", "ATL"])
    expect(m.shortest_route(FLIGHTS, "RDU", "ANC"), ["RDU", "CLT", "ORD", "SEA", "ANC"])
    expect(m.shortest_route(FLIGHTS, "ATL", "HNL"), ["ATL", "LAX", "HNL"])
    expect(m.shortest_route(FLIGHTS, "SEA", "ORD"), None, "flights are one-way")
    expect(m.shortest_route(FLIGHTS, "HNL", "RDU"), None, "HNL has no outbound flights")
    expect(m.shortest_route(FLIGHTS, "RDU", "RDU"), ["RDU"])
    expect(m.shortest_route(FLIGHTS, "XXX", "RDU"), None)
    shortcut = [("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")]
    expect(m.shortest_route(shortcut, "A", "D"), ["A", "D"], "fewest legs: BFS, not DFS")
