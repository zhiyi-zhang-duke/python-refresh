# 05 - Classes

```bash
python 05_classes/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `Model` | easy | `__init__`, instance attributes, methods |
| 02 | `Booking` | easy | `__repr__` vs `__str__`, `!r` |
| 03 | `Session` | easy | class attribute vs instance attribute, shared-mutable trap |
| 04 | `ModelSpec` | easy | `@staticmethod`, `@classmethod` alternate constructor |
| 05 | `Room` | medium | `@property`, validated setter, read-only attribute |
| 06 | `ModelRef` | medium | `__eq__` + `__hash__`, `NotImplemented` |
| 07 | `InventoryItem` / `PerishableItem` | medium | inheritance, `super().__init__`, `super().method()` |
| 08 | `Provider` / `DictProvider` / `ConstantProvider` | medium | `abc.ABC`, `@abstractmethod` |
| 09 | `Job` | medium | `@dataclass(order=True)`, `field(default_factory=list, compare=False)` |
| 10 | `Slot` | medium | `@dataclass(frozen=True)`, `__post_init__` validation |
| 11 | `Version` | advanced | `functools.total_ordering`, `__lt__`, hash consistency |
| 12 | `ModelRegistry` | advanced | `__len__`, `__contains__`, `__getitem__`, `__iter__` |
| 13 | `ModelLease` | advanced | context-manager class, `__exit__` suppression |
| 14 | `ProviderClient` | advanced | composition seam: retry + cache in one place |

## Cheat sheet

```python
class Model:
    kind = "llm"                      # CLASS attribute: one value shared by all instances

    def __init__(self, name, size_gb):
        self.name = name              # INSTANCE attribute: per object
        self.history = []             # mutable state ALWAYS goes in __init__

    def describe(self):               # forgetting `self` -> "takes 0 positional arguments but 1 was given"
        return f"{self.name}"

    def __repr__(self):               # REPL, debugger, lists/dicts, f"{x!r}"
        return f"Model({self.name!r}, {self.size_gb!r})"

    def __str__(self):                # print(), str(), f"{x}"; falls back to __repr__ if missing
        return self.name

vars(obj)          # the instance's own attributes as a dict (great for debugging)
type(obj).__name__ # "Model"
isinstance(obj, (A, B))   # tuple = any of
```

Gotcha (ex03): `history = []` at class level is ONE list shared by every instance.
`self.count += 1` reads `Model.count`, then writes a NEW instance attribute that shadows
it. Bump shared counters with `Model.count += 1`.

### Static / class methods, properties

```python
class ModelSpec:
    @staticmethod
    def parse_size(text):             # no self, no cls; just a namespaced function
        ...

    @classmethod
    def from_line(cls, line):         # alternate constructor; cls is the (sub)class
        name, size = line.split()     # ValueError if not exactly 2 parts
        return cls(name, cls.parse_size(size))   # cls(...), not ModelSpec(...)

class Room:
    def __init__(self, name, capacity):
        self._name = name
        self.capacity = capacity      # runs the setter -> validated at construction too

    @property
    def name(self):                   # no setter -> read-only (assignment: AttributeError)
        return self._name

    @property
    def capacity(self):
        return self._capacity         # underscore! returning self.capacity recurses forever

    @capacity.setter                  # decorator name is the PROPERTY name, then .setter
    def capacity(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"bad capacity: {value!r}")
        self._capacity = value
```

### Equality, hashing, ordering

```python
def __eq__(self, other):
    if not isinstance(other, ModelRef):
        return NotImplemented         # NOT False, NOT raise. Python then tries other.__eq__
    return self._key() == other._key()

def __hash__(self):
    return hash(self._key())          # equal objects MUST hash equal; hash the same tuple
```

- Defining `__eq__` sets `__hash__ = None`: instances become unhashable (`TypeError` in a set/dict key) until you add `__hash__`.
- `__ne__` is derived from `__eq__` automatically. `!=` is value inequality.
- `is` / `is not` is identity (same object). Use `==` / `!=` for strings and numbers:
  `cmd is not "quit"` "works" by accident for some interned strings and fails for others
  (Python 3.8+ even warns: `SyntaxWarning: "is not" with a literal`). Only use `is` for `None`, `True`/`False`, and sentinels.
- `@functools.total_ordering` + `__eq__` + `__lt__` gives you `<=`, `>`, `>=`. Without it,
  `a > b` still works (Python reflects to `b < a`) but `a >= b` raises `TypeError`.
- `sorted()` / `min()` / `max()` only need `__lt__`. Tuples compare element by element:
  `(1, 10) > (1, 9)`, while strings compare char by char: `"1.10" < "1.9"`.

### Inheritance and ABCs

```python
class PerishableItem(InventoryItem):
    def __init__(self, sku, price, qty, days_left):
        super().__init__(sku, price, qty)   # forget this -> AttributeError: no attribute 'sku'
        self.days_left = days_left

    def value(self):
        return super().value() / 2          # reuse the parent's logic

from abc import ABC, abstractmethod
class Provider(ABC):
    @abstractmethod
    def fetch(self, city): ...            # body can be ... ; subclasses must override

    def report(self, city):               # concrete methods can call abstract ones
        return f"{city}: {self.fetch(city)}"

Provider()        # TypeError: Can't instantiate abstract class Provider with abstract method fetch
```

The check happens at **instantiation**, not at class definition: a subclass that
forgets `fetch` imports fine and fails when you construct it.

### Dataclasses

```python
from dataclasses import dataclass, field

@dataclass(order=True)          # order: <, <=, >, >= compare fields as a tuple, IN DEFINITION ORDER
class Job:
    priority: int
    name: str
    tags: list[str] = field(default_factory=list, compare=False)   # fresh list per instance
    # tags: list = []     -> ValueError at class definition: mutable default not allowed

@dataclass(frozen=True)         # immutable + hashable (eq=True and frozen=True -> __hash__)
class Slot:
    start: int
    end: int
    def __post_init__(self):    # runs after the generated __init__; validate here
        if self.start >= self.end:
            raise ValueError("start must be before end")

s.start = 10        # dataclasses.FrozenInstanceError (a subclass of AttributeError)
```

Free with `@dataclass`: `__init__`, `__repr__` (`Job(priority=1, name='chat', tags=[])`),
`__eq__`. Not free: `__hash__` (unless frozen), ordering (unless `order=True`).
Fields with defaults must come after fields without.

### Container dunders

```python
class ModelRegistry:
    def __len__(self): return len(self._models)          # len(reg); also makes `if reg:` work
    def __contains__(self, name): return name in self._models   # `name in reg`
    def __getitem__(self, name): return self._models[name]      # reg[name]; raise KeyError when missing
    def __iter__(self): return iter(self._models.values())      # for m in reg / list(reg)

names = [m["name"] for m in models]                      # extract a field from a list of dicts
sizes = {m["name"]: m["size_gb"] for m in models}        # dict comprehension
```

Gotcha: with `__getitem__` but no `__iter__`, `for x in reg` calls `reg[0]`, `reg[1]`, ...
(the old sequence protocol) and dies with `KeyError: 0`.

### Context-manager class

```python
class ModelLease:
    def __enter__(self):
        self.log.append("load")
        return self                       # this is what `as x` binds to
    def __exit__(self, exc_type, exc, tb):
        self.log.append("unload")         # runs on success AND on exception
        return False                      # True = swallow the exception; False/None = propagate
```

`exc_type` is `None` on success. Return `True` only for exceptions you mean to swallow:
`return exc_type is not None and issubclass(exc_type, self.swallow)`.

### Composition seam (ex14)

Wrap the external dependency once; everything else talks to the wrapper.

```python
class ProviderClient:
    def __init__(self, provider, retries=2):
        self.provider = provider          # injected: tests pass a fake
        self._cache = {}
    def get(self, city):
        key = city.strip().lower()
        if key in self._cache:
            return self._cache[key]
        value = self._fetch_with_retry(key)   # retry lives here and only here
        self._cache[key] = value              # cache only successes
        return value
```

Retry, caching, logging, and metrics each get added in ONE place, and swapping the real
provider for a fake needs no other code changes. Retry only the transient error
(`TimeoutError`); let "unknown city" fail fast.
