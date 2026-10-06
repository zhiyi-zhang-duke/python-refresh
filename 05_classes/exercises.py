"""05 - Classes

Fill in each class, then run:      python 05_classes/exercises.py
Run just one exercise:             python 05_classes/exercises.py 4
Run exercise 4 onward:             python 05_classes/exercises.py 4+

Exercises go from easy (01) to advanced (14). Every method you need to write
starts as `raise NotImplementedError`; replace it when you start that exercise.
Some stubs are missing a decorator or a dataclass option on purpose; the
docstring tells you what the finished class must do.
"""

from abc import ABC
from dataclasses import dataclass
from functools import total_ordering  # noqa: F401  (you'll want this in ex11)

MODELS = [
    {"name": "phi3:mini", "size_gb": 2.2},
    {"name": "llama3:8b", "size_gb": 4.7},
    {"name": "gemma2:9b", "size_gb": 5.4},
]


# ---------------------------------------------------------------- easy ----

class Model:
    """ex01. A local LLM model with a name, a size, and a loaded flag.

    m = Model("phi3:mini", 2.2)
    m.name -> "phi3:mini";  m.size_gb -> 2.2;  m.loaded -> False
    m.load()      sets loaded to True     m.unload()  sets it back to False
    m.describe()  -> "phi3:mini (2.2 GB)"            when not loaded
                  -> "phi3:mini (2.2 GB, loaded)"    when loaded

    Tools: __init__(self, ...) assigning self.x = x; every method takes self first
    """

    def __init__(self, name: str, size_gb: float):
        raise NotImplementedError

    def load(self) -> None:
        raise NotImplementedError

    def unload(self) -> None:
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


class Booking:
    """ex02. A room booking with a developer-facing repr and a user-facing str.

    b = Booking("A", 9, 11)
    repr(b)   -> "Booking('A', 9, 11)"       (what the REPL, debugger, and lists show)
    str(b)    -> "Room A, 09:00-11:00"       (what print() and f"{b}" show)
    str([b])  -> "[Booking('A', 9, 11)]"     (containers use repr of their items)
    repr(Booking("O'Hare", 9, 10)) -> Booking("O'Hare", 9, 10)   (let !r pick the quotes)

    Tools: __repr__, __str__, f"{x!r}", f"{n:02d}"
    """

    def __init__(self, room: str, start: int, end: int):
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class Session:
    """ex03. Class attribute vs instance attribute.

    `count` is a CLASS attribute: the number of Sessions ever created (shared by all).
    `history` is an INSTANCE attribute: each session's own list of commands.

    s1 = Session("jack"); s2 = Session("becca")
    s1.add("list")
    s1.history -> ["list"];  s2.history -> [];  Session.count -> 2;  s1.user -> "jack"

    Trap 1: `history = []` at class level is ONE list shared by every instance.
    Trap 2: `self.count += 1` reads the class value, then creates an INSTANCE attr
            that shadows it; Session.count never changes.

    Tools: Session.count += 1, self.history = [] inside __init__
    """

    count = 0

    def __init__(self, user: str):
        raise NotImplementedError

    def add(self, command: str) -> None:
        raise NotImplementedError


class ModelSpec:
    """ex04. An alternate constructor (@classmethod) and a helper that needs no self (@staticmethod).

    ModelSpec("phi3:mini", 2.2)          plain constructor: stores .name and .size_gb

    ModelSpec.parse_size("2.2GB")  -> 2.2
    ModelSpec.parse_size("512MB")  -> 0.5      (MB / 1024)
    ModelSpec.parse_size(" 1.5 gb ") -> 1.5    (ignore case and spaces)
    ModelSpec.parse_size("3TB")    -> ValueError

    ModelSpec.from_line("  phi3:mini 2.2GB \\n") -> ModelSpec with name "phi3:mini", size_gb 2.2
    ModelSpec.from_line("phi3:mini")            -> ValueError (needs exactly 2 parts)
    from_line must build the object with cls(...), so a subclass calling
    from_line gets an instance of the subclass back.

    Tools: @staticmethod, @classmethod (first parameter is cls), str.endswith, float(),
           a, b = parts   (unpacking the wrong count raises ValueError for free)
    """

    def __init__(self, name: str, size_gb: float):
        raise NotImplementedError

    @staticmethod
    def parse_size(text: str) -> float:
        raise NotImplementedError

    @classmethod
    def from_line(cls, line: str) -> "ModelSpec":
        raise NotImplementedError


# -------------------------------------------------------------- medium ----

class Room:
    """ex05. Properties: validate on assignment, expose read-only attributes.

    r = Room("Boardroom", 8)
    r.name -> "Boardroom"         read-only: r.name = "x" raises AttributeError
    r.capacity -> 8               r.capacity = 12 works
    r.capacity = 0      -> ValueError   (must be a positive int)
    r.capacity = "8"    -> ValueError   (must be an int, not a str)
    Room("Closet", -1)  -> ValueError   (__init__ must go through the same validation)

    Tools: @property, @capacity.setter, store the real value on self._capacity;
           in __init__ write `self.capacity = capacity` so the setter runs.
           A property with no setter is read-only.
    """

    def __init__(self, name: str, capacity: int):
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capacity(self) -> int:
        raise NotImplementedError

    @capacity.setter
    def capacity(self, value: int) -> None:
        raise NotImplementedError


class ModelRef:
    """ex06. Value equality + hashing, so refs work as set members and dict keys.

    A ref is (name, tag). The name is case-insensitive; the tag is not.
    ModelRef("Phi3", "mini") == ModelRef("phi3", "mini")   -> True
    ModelRef("phi3", "mini") == ModelRef("phi3", "MINI")   -> False
    len({ModelRef("phi3", "mini"), ModelRef("PHI3", "mini")}) -> 1
    ModelRef("phi3", "mini") == "phi3:mini"                -> False (not an error)
    str(ModelRef("Phi3", "mini")) -> "phi3:mini"

    Gotcha: defining __eq__ silently sets __hash__ to None -> "unhashable type" in a set.
            Equal objects MUST have equal hashes: hash the same normalized tuple you compare.
    Return NotImplemented (don't raise, don't return False) from __eq__ for other types.

    Tools: __eq__, __hash__, isinstance, hash((a, b))
    """

    def __init__(self, name: str, tag: str):
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class InventoryItem:
    """ex07 (part 1). Base class.

    item = InventoryItem("SKU-1", 2.50, 10)
    item.sku, item.price, item.qty
    item.value()     -> 25.0              (price * qty)
    item.restock(5)  -> qty becomes 15;   restock(0) or negative -> ValueError
    """

    def __init__(self, sku: str, price: float, qty: int):
        raise NotImplementedError

    def value(self) -> float:
        raise NotImplementedError

    def restock(self, n: int) -> None:
        raise NotImplementedError


class PerishableItem(InventoryItem):
    """ex07 (part 2). Subclass that adds days_left and overrides value().

    p = PerishableItem("MILK", 4.0, 3, days_left=5)
    p.value() -> 12.0     days_left > 2: full value
              ->  6.0     days_left 1 or 2: half value
              ->  0.0     days_left <= 0: worthless
    p.restock(2) still works (inherited).

    Tools: super().__init__(sku, price, qty) for the shared fields; super().value()
           inside the override instead of re-computing price * qty
    """

    def __init__(self, sku: str, price: float, qty: int, days_left: int):
        raise NotImplementedError

    def value(self) -> float:
        raise NotImplementedError


class Provider(ABC):
    """ex08 (part 1). An interface: subclasses MUST implement fetch().

    Make fetch abstract so Provider() raises TypeError, and so does any subclass
    that forgets to implement fetch.

    report(city) is concrete and shared by every subclass:
        DictProvider({"durham": 21.5}).report("Durham") -> "dict: Durham 21.5C"
        uses self.name (a class attribute each subclass overrides) and self.fetch(city)

    Tools: from abc import ABC, abstractmethod; @abstractmethod; f"{t:.1f}"
    """

    name = "base"

    def fetch(self, city: str) -> float:  # make this abstract
        raise NotImplementedError

    def report(self, city: str) -> str:
        raise NotImplementedError


class DictProvider(Provider):
    """ex08 (part 2). name = "dict". Looks the city up (stripped, lowercased) in the dict
    given to __init__. Unknown city -> KeyError.
    """

    name = "dict"

    def __init__(self, temps: dict[str, float]):
        raise NotImplementedError

    def fetch(self, city: str) -> float:
        raise NotImplementedError


class ConstantProvider(Provider):
    """ex08 (part 3). name = "constant". Always returns the temperature given to __init__."""

    name = "constant"

    def __init__(self, temp: float):
        raise NotImplementedError

    def fetch(self, city: str) -> float:
        raise NotImplementedError


@dataclass
class Job:
    """ex09. A queued job as a dataclass: free __init__, __repr__, __eq__, and ordering.

    Add a third field, `tags: list[str]`, that defaults to an empty list (a NEW list per job),
    and make Jobs sortable by (priority, name). Tags must not affect == or ordering.

    Job(1, "chat")                    -> Job(priority=1, name='chat', tags=[])
    sorted([Job(2, "b"), Job(1, "z"), Job(1, "a")]) -> priorities/names (1,"a"), (1,"z"), (2,"b")
    Job(1, "a", ["x"]) == Job(1, "a", ["y"])         -> True

    Gotcha: `tags: list = []` is rejected at class-definition time (shared mutable default).
    Ordering compares fields in DEFINITION order, so put the sort keys first.

    Tools: @dataclass(order=True), field(default_factory=list, compare=False)
    """

    priority: int
    name: str

    def __post_init__(self):
        raise NotImplementedError  # delete this method once the fields are right


@dataclass
class Slot:
    """ex10. An immutable, hashable time range [start, end) in whole hours.

    Slot(9, 11)                   fine
    Slot(11, 9) / Slot(9, 9)      -> ValueError (validate in __post_init__)
    s.start = 10                  -> dataclasses.FrozenInstanceError
    {Slot(9, 11), Slot(9, 11)}    -> one element
    Slot(9, 11).overlaps(Slot(10, 12)) -> True
    Slot(9, 11).overlaps(Slot(11, 12)) -> False   (touching ends don't overlap)

    Tools: @dataclass(frozen=True) (frozen + eq gives you __hash__), __post_init__,
           overlap test: a.start < b.end and b.start < a.end
    """

    start: int
    end: int

    def __post_init__(self):
        raise NotImplementedError

    def overlaps(self, other: "Slot") -> bool:
        raise NotImplementedError


# ------------------------------------------------------------ advanced ----

class Version:
    """ex11. Numeric version comparison with only __eq__ and __lt__ written by hand.

    Version("1.10.0") > Version("1.9.3")     -> True   (strings would say False)
    Version("1.2") == Version("1.2.0")       -> True   (trailing zeros don't matter)
    hash(Version("1.2")) == hash(Version("1.2.0"))
    Version("2.0") >= Version("1.99")        -> True   (<=, >, >= come from total_ordering)
    sorted(...) works
    repr(Version("1.10.0")) -> "Version('1.10.0')"     (the text as given)
    Version("1.x")         -> ValueError
    Version("1.0") == "1.0" -> False;   Version("1.0") < "1.0" -> TypeError
        (return NotImplemented for non-Versions; Python turns that into False / TypeError)

    Tools: @total_ordering on the class, tuple(int(p) for p in text.split(".")),
           tuples compare element by element
    """

    def __init__(self, text: str):
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        raise NotImplementedError

    def __lt__(self, other) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError


class ModelRegistry:
    """ex12. A container that works with len(), in, [], and for.

    reg = ModelRegistry(MODELS)            # MODELS: list of {"name", "size_gb"} dicts
    len(reg)            -> 3                (also makes `if reg:` work)
    "phi3:mini" in reg  -> True             (by name)
    reg["llama3:8b"]    -> {"name": "llama3:8b", "size_gb": 4.7};  unknown name -> KeyError
    list(reg)           -> the model dicts in insertion order
    reg.add({"name": "qwen2:7b", "size_gb": 4.4})   duplicate name -> ValueError
    reg.names()         -> sorted list of names
    reg.total_size()    -> 12.3   (sum of size_gb, rounded to 1 decimal)

    Store models in a dict keyed by name. Adding to the registry must not change the
    list that was passed in.

    Gotcha: with __getitem__ but no __iter__, `for m in reg` calls reg[0], reg[1], ...
            and blows up with KeyError: 0. Define __iter__.

    Tools: __len__, __contains__, __getitem__, __iter__ (return iter(...) or use yield),
           [m["name"] for m in ...]
    """

    def __init__(self, models: list[dict]):
        raise NotImplementedError

    def add(self, model: dict) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __contains__(self, name: str) -> bool:
        raise NotImplementedError

    def __getitem__(self, name: str) -> dict:
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def names(self) -> list[str]:
        raise NotImplementedError

    def total_size(self) -> float:
        raise NotImplementedError


class ModelLease:
    """ex13. A context-manager class: load on enter, ALWAYS unload on exit.

    log = []
    with ModelLease("phi3", log) as lease:    # __enter__ returns self
        lease.ask("hi")
    log -> ["load phi3", "ask phi3: hi", "unload phi3"]

    lease.active is True only inside the with block. ask() outside it -> RuntimeError.
    If the body raises, log "error phi3: ValueError" (the exception's type name) before
    "unload phi3", and let the exception propagate...
    ...UNLESS it is an instance of one of the types in `swallow` (default: empty tuple);
    then suppress it.  ModelLease("phi3", log, swallow=(LookupError,)) swallows KeyError too.

    Tools: __enter__(self), __exit__(self, exc_type, exc, tb) -- exc_type is None when the
           body succeeded; returning True suppresses the exception. issubclass(exc_type, swallow)
    """

    def __init__(self, name: str, log: list[str], swallow: tuple = ()):
        raise NotImplementedError

    def __enter__(self) -> "ModelLease":
        raise NotImplementedError

    def __exit__(self, exc_type, exc, tb) -> bool:
        raise NotImplementedError

    def ask(self, prompt: str) -> None:
        raise NotImplementedError


class ProviderClient:
    """ex14. One seam in front of a provider, so retry and caching live in ONE place.

    `provider` is any object with .fetch(city) -> float. It may raise the built-in
    TimeoutError on a transient failure, or KeyError for an unknown city.

    client = ProviderClient(provider, retries=2)
    client.get(" Durham ")
      - key = city stripped and lowercased; the provider is called with the key
      - cache hit  -> return the cached value; the provider is NOT called
      - cache miss -> call provider.fetch(key). On TimeoutError, try again, up to
                      `retries` extra attempts; if every attempt times out, re-raise the
                      last TimeoutError
      - any other exception propagates immediately (no retry) and nothing is cached
    client.stats() -> {"hits": int, "misses": int, "calls": int}
                      calls = total provider.fetch calls, retries included
    client.invalidate("durham") drops one key (no error if absent); invalidate() drops all.

    Callers (and tests) never touch the provider directly: swap in a fake provider and
    every caching/retry rule still applies. That's the point of the seam.

    Tools: composition (self.provider = provider), a dict cache, for attempt in range(...),
           except TimeoutError, bare `raise`, dict.pop(key, None), dict.clear()
    """

    def __init__(self, provider, retries: int = 2):
        raise NotImplementedError

    def get(self, city: str) -> float:
        raise NotImplementedError

    def stats(self) -> dict[str, int]:
        raise NotImplementedError

    def invalidate(self, city: str | None = None) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
