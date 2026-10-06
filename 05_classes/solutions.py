"""05 - Classes: reference solutions.   Check them:  python 05_classes/solutions.py"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import total_ordering

MODELS = [
    {"name": "phi3:mini", "size_gb": 2.2},
    {"name": "llama3:8b", "size_gb": 4.7},
    {"name": "gemma2:9b", "size_gb": 5.4},
]


# ---------------------------------------------------------------- easy ----

class Model:
    def __init__(self, name: str, size_gb: float):
        self.name = name
        self.size_gb = size_gb
        self.loaded = False

    def load(self) -> None:
        self.loaded = True

    def unload(self) -> None:
        self.loaded = False

    def describe(self) -> str:
        suffix = ", loaded" if self.loaded else ""
        return f"{self.name} ({self.size_gb} GB{suffix})"


class Booking:
    def __init__(self, room: str, start: int, end: int):
        self.room = room
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        # !r calls repr() on each field, so strings get quotes (and the right kind).
        return f"Booking({self.room!r}, {self.start!r}, {self.end!r})"

    def __str__(self) -> str:
        return f"Room {self.room}, {self.start:02d}:00-{self.end:02d}:00"


class Session:
    count = 0

    def __init__(self, user: str):
        self.user = user
        self.history: list[str] = []  # per-instance: created fresh in __init__
        Session.count += 1             # name the class; self.count += 1 would shadow it

    def add(self, command: str) -> None:
        self.history.append(command)


class ModelSpec:
    def __init__(self, name: str, size_gb: float):
        self.name = name
        self.size_gb = size_gb

    @staticmethod
    def parse_size(text: str) -> float:
        t = text.replace(" ", "").upper()
        if t.endswith("GB"):
            return float(t[:-2])
        if t.endswith("MB"):
            return float(t[:-2]) / 1024
        raise ValueError(f"unknown size unit: {text!r}")

    @classmethod
    def from_line(cls, line: str) -> "ModelSpec":
        name, size = line.split()  # ValueError if not exactly 2 parts
        return cls(name, cls.parse_size(size))


# -------------------------------------------------------------- medium ----

class Room:
    def __init__(self, name: str, capacity: int):
        self._name = name
        self.capacity = capacity  # goes through the setter, so it's validated

    @property
    def name(self) -> str:
        return self._name

    @property
    def capacity(self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"capacity must be a positive int, got {value!r}")
        self._capacity = value


class ModelRef:
    def __init__(self, name: str, tag: str):
        self.name = name.lower()
        self.tag = tag

    def _key(self) -> tuple[str, str]:
        return (self.name, self.tag)

    def __eq__(self, other) -> bool:
        if not isinstance(other, ModelRef):
            return NotImplemented  # lets Python try other.__eq__, then fall back to identity
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __str__(self) -> str:
        return f"{self.name}:{self.tag}"


class InventoryItem:
    def __init__(self, sku: str, price: float, qty: int):
        self.sku = sku
        self.price = price
        self.qty = qty

    def value(self) -> float:
        return self.price * self.qty

    def restock(self, n: int) -> None:
        if n <= 0:
            raise ValueError(f"restock amount must be positive, got {n}")
        self.qty += n


class PerishableItem(InventoryItem):
    def __init__(self, sku: str, price: float, qty: int, days_left: int):
        super().__init__(sku, price, qty)
        self.days_left = days_left

    def value(self) -> float:
        full = super().value()
        if self.days_left <= 0:
            return 0.0
        if self.days_left <= 2:
            return full / 2
        return full


class Provider(ABC):
    name = "base"

    @abstractmethod
    def fetch(self, city: str) -> float:
        ...

    def report(self, city: str) -> str:
        return f"{self.name}: {city} {self.fetch(city):.1f}C"


class DictProvider(Provider):
    name = "dict"

    def __init__(self, temps: dict[str, float]):
        self.temps = temps

    def fetch(self, city: str) -> float:
        return self.temps[city.strip().lower()]


class ConstantProvider(Provider):
    name = "constant"

    def __init__(self, temp: float):
        self.temp = temp

    def fetch(self, city: str) -> float:
        return self.temp


@dataclass(order=True)
class Job:
    priority: int
    name: str
    tags: list[str] = field(default_factory=list, compare=False)


@dataclass(frozen=True)
class Slot:
    start: int
    end: int

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError(f"start must be before end: {self.start}-{self.end}")

    def overlaps(self, other: "Slot") -> bool:
        return self.start < other.end and other.start < self.end


# ------------------------------------------------------------ advanced ----

@total_ordering
class Version:
    def __init__(self, text: str):
        self.text = text
        parts = [int(p) for p in text.split(".")]  # int("x") raises ValueError
        while parts and parts[-1] == 0:            # "1.2.0" and "1.2" compare equal
            parts.pop()
        self._key = tuple(parts)

    def __repr__(self) -> str:
        return f"Version({self.text!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key == other._key

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key < other._key

    def __hash__(self) -> int:
        return hash(self._key)


class ModelRegistry:
    def __init__(self, models: list[dict]):
        self._models: dict[str, dict] = {}  # dicts keep insertion order (3.7+)
        for model in models:
            self.add(model)

    def add(self, model: dict) -> None:
        name = model["name"]
        if name in self._models:
            raise ValueError(f"duplicate model: {name}")
        self._models[name] = model

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, name: str) -> bool:
        return name in self._models

    def __getitem__(self, name: str) -> dict:
        return self._models[name]

    def __iter__(self):
        return iter(self._models.values())

    def names(self) -> list[str]:
        return sorted(m["name"] for m in self)

    def total_size(self) -> float:
        return round(sum(m["size_gb"] for m in self), 1)


class ModelLease:
    def __init__(self, name: str, log: list[str], swallow: tuple = ()):
        self.name = name
        self.log = log
        self.swallow = swallow
        self.active = False

    def __enter__(self) -> "ModelLease":
        self.log.append(f"load {self.name}")
        self.active = True
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.log.append(f"error {self.name}: {exc_type.__name__}")
        self.log.append(f"unload {self.name}")
        self.active = False
        # True suppresses the exception; False/None lets it propagate.
        return exc_type is not None and issubclass(exc_type, self.swallow)

    def ask(self, prompt: str) -> None:
        if not self.active:
            raise RuntimeError(f"{self.name} is not loaded; use it inside a with block")
        self.log.append(f"ask {self.name}: {prompt}")


class ProviderClient:
    def __init__(self, provider, retries: int = 2):
        self.provider = provider
        self.retries = retries
        self._cache: dict[str, float] = {}
        self._stats = {"hits": 0, "misses": 0, "calls": 0}

    def get(self, city: str) -> float:
        key = city.strip().lower()
        if key in self._cache:
            self._stats["hits"] += 1
            return self._cache[key]
        self._stats["misses"] += 1
        value = self._fetch_with_retry(key)
        self._cache[key] = value
        return value

    def _fetch_with_retry(self, key: str) -> float:
        for attempt in range(self.retries + 1):
            self._stats["calls"] += 1
            try:
                return self.provider.fetch(key)
            except TimeoutError:
                if attempt == self.retries:
                    raise  # out of attempts: re-raise the last TimeoutError unchanged
        raise AssertionError("unreachable")

    def stats(self) -> dict[str, int]:
        return dict(self._stats)  # a copy, so callers can't mutate our counters

    def invalidate(self, city: str | None = None) -> None:
        if city is None:
            self._cache.clear()
        else:
            self._cache.pop(city.strip().lower(), None)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
