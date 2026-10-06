"""A fake weather provider used by the 06_exceptions exercises. Not an exercise: read it, don't edit it.

exercises.py, solutions.py, and tests.py all do `import provider`. That works because
Python puts the running script's folder (06_exceptions/) at the front of sys.path.

With `import provider`, the exceptions live in the module's namespace:
    except provider.UnknownCity:      # works
    except UnknownCity:               # NameError, unless you did `from provider import UnknownCity`
"""


class ProviderError(Exception):
    """Base class for every error this provider raises."""


class UnknownCity(ProviderError):
    """The provider has no data for that city."""


class Timeout(ProviderError):
    """A transient failure; trying again may work. (Not the built-in TimeoutError.)"""


TEMPS = {
    "durham": 21.5,
    "raleigh": 23.0,
    "cary": 22.1,
    "new york": 15.8,
}


def get_temp(city: str) -> float:
    """Current temperature in C. Case/whitespace-insensitive. Raises UnknownCity."""
    key = city.strip().lower()
    if key not in TEMPS:
        raise UnknownCity(f"no data for {city!r}")
    return TEMPS[key]


class FlakyProvider:
    """Like get_temp, but the first `fail_times` calls raise Timeout.

    p = FlakyProvider(fail_times=2)
    p.get_temp("durham")   # Timeout   (call 1)
    p.get_temp("durham")   # Timeout   (call 2)
    p.get_temp("durham")   # 21.5      (call 3)
    p.calls                # 3
    """

    def __init__(self, fail_times: int = 0):
        self.fail_times = fail_times
        self.calls = 0

    def get_temp(self, city: str) -> float:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise Timeout(f"timed out on call {self.calls}")
        return get_temp(city)
