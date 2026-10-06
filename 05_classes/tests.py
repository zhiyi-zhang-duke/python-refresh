import dataclasses

from harness import expect, expect_raises


def test_ex01(m):
    """Model: __init__, instance attributes, methods"""
    mdl = m.Model("phi3:mini", 2.2)
    expect(mdl.name, "phi3:mini")
    expect(mdl.size_gb, 2.2)
    assert mdl.loaded is False
    expect(mdl.describe(), "phi3:mini (2.2 GB)")
    other = m.Model("llama3:8b", 4.7)
    mdl.load()
    assert mdl.loaded is True
    expect(mdl.describe(), "phi3:mini (2.2 GB, loaded)")
    assert other.loaded is False, "loading one Model must not load another"
    mdl.unload()
    expect(mdl.describe(), "phi3:mini (2.2 GB)")


def test_ex02(m):
    """Booking: __repr__ for developers, __str__ for users"""
    b = m.Booking("A", 9, 11)
    expect(repr(b), "Booking('A', 9, 11)")
    expect(str(b), "Room A, 09:00-11:00")
    expect(f"{b}", "Room A, 09:00-11:00", "f-strings use __str__")
    expect(str([b]), "[Booking('A', 9, 11)]", "containers show the repr of their items")
    expect(str(m.Booking("Lab", 14, 16)), "Room Lab, 14:00-16:00")
    expect(repr(m.Booking("O'Hare", 9, 10)), 'Booking("O\'Hare", 9, 10)',
           "use !r so Python picks the quotes")


def test_ex03(m):
    """Session: shared class attribute vs per-instance list"""
    m.Session.count = 0
    s1 = m.Session("jack")
    s2 = m.Session("becca")
    s1.add("list")
    s1.add("run phi3")
    expect(s1.user, "jack")
    expect(s1.history, ["list", "run phi3"])
    expect(s2.history, [], "history must be per-instance, not a shared class-level list")
    assert s1.history is not s2.history
    expect(m.Session.count, 2, "Session.count should count every Session created")
    assert "count" not in vars(s1), "self.count += 1 created an instance attr; bump Session.count"


def test_ex04(m):
    """ModelSpec: @staticmethod helper, @classmethod from_line"""
    spec = m.ModelSpec("phi3:mini", 2.2)
    expect((spec.name, spec.size_gb), ("phi3:mini", 2.2))
    expect(m.ModelSpec.parse_size("2.2GB"), 2.2)
    expect(m.ModelSpec.parse_size("512MB"), 0.5)
    expect(m.ModelSpec.parse_size(" 1.5 gb "), 1.5)
    expect(spec.parse_size("1GB"), 1.0, "a staticmethod is callable on an instance too")
    expect_raises(ValueError, m.ModelSpec.parse_size, "3TB")
    expect_raises(ValueError, m.ModelSpec.parse_size, "lotsGB")

    parsed = m.ModelSpec.from_line("  phi3:mini 2.2GB \n")
    expect((parsed.name, parsed.size_gb), ("phi3:mini", 2.2))
    expect_raises(ValueError, m.ModelSpec.from_line, "phi3:mini")
    expect_raises(ValueError, m.ModelSpec.from_line, "a 1GB extra")

    class LocalSpec(m.ModelSpec):
        pass

    assert type(LocalSpec.from_line("x 1GB")) is LocalSpec, "from_line should build with cls(...)"


def test_ex05(m):
    """Room: @property, validated setter, read-only attribute"""
    r = m.Room("Boardroom", 8)
    expect(r.name, "Boardroom")
    expect(r.capacity, 8)
    r.capacity = 12
    expect(r.capacity, 12)
    expect_raises(ValueError, setattr, r, "capacity", 0)
    expect_raises(ValueError, setattr, r, "capacity", -3)
    expect_raises(ValueError, setattr, r, "capacity", "8")
    expect(r.capacity, 12, "a rejected assignment must leave the old value")
    expect_raises(AttributeError, setattr, r, "name", "Closet")
    expect_raises(ValueError, m.Room, "Closet", -1)


def test_ex06(m):
    """ModelRef: __eq__ + __hash__, usable in sets and as dict keys"""
    a = m.ModelRef("Phi3", "mini")
    b = m.ModelRef("phi3", "mini")
    assert a == b
    assert not (a != b)
    assert a is not b, "== is value equality; `is` is identity (same object)"
    assert a != m.ModelRef("phi3", "MINI"), "tags are case-sensitive"
    assert a != m.ModelRef("llama3", "mini")
    expect(len({a, b, m.ModelRef("PHI3", "mini")}), 1)
    lookup = {a: "small"}
    expect(lookup[m.ModelRef("PHI3", "mini")], "small")
    assert (a == "phi3:mini") is False
    assert a.__eq__("phi3:mini") is NotImplemented, "return NotImplemented for other types"
    expect(str(a), "phi3:mini")


def test_ex07(m):
    """PerishableItem: inheritance, super().__init__, super().value()"""
    item = m.InventoryItem("SKU-1", 2.5, 10)
    expect(item.value(), 25.0)
    item.restock(5)
    expect(item.qty, 15)
    expect_raises(ValueError, item.restock, 0)
    expect_raises(ValueError, item.restock, -2)

    p = m.PerishableItem("MILK", 4.0, 3, days_left=5)
    assert isinstance(p, m.InventoryItem)
    expect((p.sku, p.price, p.qty), ("MILK", 4.0, 3), "did PerishableItem call super().__init__?")
    expect(p.value(), 12.0)
    p.restock(2)
    expect(p.qty, 5, "restock is inherited")
    expect(p.value(), 20.0)
    expect(m.PerishableItem("A", 4.0, 3, days_left=2).value(), 6.0)
    expect(m.PerishableItem("A", 4.0, 3, days_left=1).value(), 6.0)
    expect(m.PerishableItem("A", 4.0, 3, days_left=0).value(), 0.0)
    expect(m.PerishableItem("A", 4.0, 3, days_left=-3).value(), 0.0)


def test_ex08(m):
    """Provider: abc.ABC interface with two implementations"""
    d = m.DictProvider({"durham": 21.5, "cary": 22.0})
    expect(d.fetch(" Durham "), 21.5)
    expect(d.report("Durham"), "dict: Durham 21.5C")
    expect_raises(KeyError, d.fetch, "Boston")
    c = m.ConstantProvider(20)
    expect(c.report("Anywhere"), "constant: Anywhere 20.0C")
    assert isinstance(d, m.Provider) and isinstance(c, m.Provider)

    expect_raises(TypeError, m.Provider)

    class Forgetful(m.Provider):
        name = "forgetful"

    expect_raises(TypeError, Forgetful)


def test_ex09(m):
    """Job: @dataclass with order=True and field(default_factory=list)"""
    j = m.Job(1, "chat")
    expect(j.tags, [])
    j.tags.append("fast")
    expect(m.Job(2, "embed").tags, [], "each Job needs its own tags list")
    expect(repr(m.Job(1, "chat")), "Job(priority=1, name='chat', tags=[])")
    expect(m.Job(1, "chat", ["gpu"]).tags, ["gpu"])
    jobs = [m.Job(2, "b"), m.Job(1, "z", ["x"]), m.Job(1, "a")]
    expect([(x.priority, x.name) for x in sorted(jobs)], [(1, "a"), (1, "z"), (2, "b")])
    assert m.Job(1, "a", ["x"]) == m.Job(1, "a", ["y"]), "tags must not affect =="
    assert m.Job(1, "a") < m.Job(1, "b")


def test_ex10(m):
    """Slot: frozen dataclass, __post_init__ validation, hashable"""
    s = m.Slot(9, 11)
    expect((s.start, s.end), (9, 11))
    expect_raises(ValueError, m.Slot, 11, 9)
    expect_raises(ValueError, m.Slot, 9, 9)
    expect_raises(dataclasses.FrozenInstanceError, setattr, s, "start", 10)
    expect(len({m.Slot(9, 11), m.Slot(9, 11), m.Slot(10, 12)}), 2)
    assert s.overlaps(m.Slot(10, 12)) is True
    assert m.Slot(10, 12).overlaps(s) is True
    assert s.overlaps(m.Slot(11, 12)) is False, "touching ends don't overlap"
    assert s.overlaps(m.Slot(7, 9)) is False
    assert m.Slot(8, 12).overlaps(m.Slot(9, 10)) is True, "containment overlaps"


def test_ex11(m):
    """Version: __eq__ + __lt__ + total_ordering"""
    V = m.Version
    assert V("1.10.0") > V("1.9.3")
    assert V("1.9.3") < V("1.10.0")
    assert V("1.2") == V("1.2.0")
    assert V("1.0") != V("1.0.1")
    expect(hash(V("1.2")), hash(V("1.2.0")), "equal Versions must hash the same")
    expect(len({V("1"), V("1.0"), V("1.0.0")}), 1)
    assert V("2.0") >= V("1.99"), ">= should come from @total_ordering"
    assert V("1.0") <= V("1.0.0")
    expect(sorted([V("1.10"), V("1.2"), V("1.9.1")]), [V("1.2"), V("1.9.1"), V("1.10")])
    expect(repr(V("1.10.0")), "Version('1.10.0')")
    expect_raises(ValueError, V, "1.x")
    assert (V("1.0") == "1.0") is False
    expect_raises(TypeError, lambda: V("1.0") < "1.0")


def test_ex12(m):
    """ModelRegistry: __len__, __contains__, __getitem__, __iter__"""
    models = [dict(d) for d in m.MODELS]
    reg = m.ModelRegistry(models)
    expect(len(reg), 3)
    assert "phi3:mini" in reg
    assert "PHI3:mini" not in reg
    expect(reg["llama3:8b"], {"name": "llama3:8b", "size_gb": 4.7})
    expect_raises(KeyError, lambda: reg["nope"])
    expect([d["name"] for d in reg], ["phi3:mini", "llama3:8b", "gemma2:9b"])

    reg.add({"name": "qwen2:7b", "size_gb": 4.4})
    expect(len(reg), 4)
    expect(len(models), 3, "adding to the registry must not mutate the caller's list")
    expect_raises(ValueError, reg.add, {"name": "phi3:mini", "size_gb": 1.0})
    expect(reg.names(), ["gemma2:9b", "llama3:8b", "phi3:mini", "qwen2:7b"])
    expect(reg.total_size(), 16.7)

    empty = m.ModelRegistry([])
    assert not empty, "len() == 0 makes the registry falsy"
    expect(list(empty), [])
    expect(empty.total_size(), 0)
    expect_raises(ValueError, m.ModelRegistry, [{"name": "a", "size_gb": 1}, {"name": "a", "size_gb": 2}])


def test_ex13(m):
    """ModelLease: __enter__/__exit__, cleanup always runs"""
    log = []
    with m.ModelLease("phi3", log) as lease:
        assert lease.active is True
        lease.ask("hi")
    assert lease.active is False
    expect(log, ["load phi3", "ask phi3: hi", "unload phi3"])
    expect_raises(RuntimeError, lease.ask, "too late")

    log = []

    def body_raises():
        with m.ModelLease("phi3", log):
            raise ValueError("bad prompt")

    expect_raises(ValueError, body_raises)
    expect(log, ["load phi3", "error phi3: ValueError", "unload phi3"])

    log = []
    try:
        with m.ModelLease("phi3", log, swallow=(LookupError,)):
            {}["missing"]
    except KeyError:
        raise AssertionError("KeyError is a LookupError; swallow=(LookupError,) should suppress it") from None
    expect(log, ["load phi3", "error phi3: KeyError", "unload phi3"])


class FakeProvider:
    """Records each fetch; raises TimeoutError for the first `timeouts` calls."""

    def __init__(self, temps, timeouts=0):
        self.temps = temps
        self.timeouts = timeouts
        self.calls = []

    def fetch(self, city):
        self.calls.append(city)
        if self.timeouts > 0:
            self.timeouts -= 1
            raise TimeoutError("provider slow")
        return self.temps[city]


def test_ex14(m):
    """ProviderClient: composition seam with caching + retry"""
    temps = {"durham": 21.5, "cary": 22.0}

    p = FakeProvider(temps)
    c = m.ProviderClient(p)
    expect(c.get(" Durham "), 21.5)
    expect(p.calls, ["durham"], "call the provider with the normalized key")
    expect(c.get("DURHAM"), 21.5)
    expect(len(p.calls), 1, "second get should be a cache hit")
    expect(c.stats(), {"hits": 1, "misses": 1, "calls": 1})

    p = FakeProvider(temps, timeouts=2)
    c = m.ProviderClient(p, retries=2)
    expect(c.get("cary"), 22.0)
    expect(len(p.calls), 3, "2 timeouts + 1 success")
    expect(c.stats(), {"hits": 0, "misses": 1, "calls": 3})

    p = FakeProvider(temps, timeouts=3)
    c = m.ProviderClient(p, retries=2)
    expect_raises(TimeoutError, c.get, "cary")
    expect(len(p.calls), 3, "1 try + 2 retries, then give up")
    expect(c.get("cary"), 22.0, "a failure must not be cached")

    p = FakeProvider(temps)
    c = m.ProviderClient(p, retries=5)
    expect_raises(KeyError, c.get, "boston")
    expect(len(p.calls), 1, "only TimeoutError is retried")
    expect_raises(KeyError, c.get, "boston")
    expect(len(p.calls), 2, "errors are not cached")

    p = FakeProvider(temps)
    c = m.ProviderClient(p)
    c.get("durham")
    c.get("cary")
    c.invalidate(" Durham ")
    c.invalidate("never-fetched")
    c.get("durham")
    c.get("cary")
    expect(p.calls, ["durham", "cary", "durham"])
    c.invalidate()
    c.get("cary")
    expect(p.calls, ["durham", "cary", "durham", "cary"])
