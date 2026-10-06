"""A fake local-model provider for the capstone REPL. NOT an exercise: treat it like
the module an interviewer hands you, and probe it before wiring handlers to it.

    python -c "import provider; print(provider.list_models())"   (from 12_capstone_repl/)

Everything is deterministic and instant. Only ONE model can be loaded at a time.

Contract
--------
list_models() -> list[dict]
    [{"name": "phi3:mini", "size_gb": 2.3, "family": "phi"}, ...]   (fresh copies each call)

loaded() -> str | None
    Name of the loaded model, or None.

load(name) -> dict
    Loads `name` (replacing whatever was loaded). Returns {"name": name, "load_ms": int}.
    Raises UnknownModel for a name that isn't an exact model name.

unload() -> str | None
    Unloads the current model and returns its name (None if nothing was loaded).

run(name, prompt) -> dict
    {"text": "<name> says: <prompt>", "tokens": int, "ms": int}. The prompt comes back
    verbatim, inner spaces included.
    Raises UnknownModel for a bad name, NotLoaded if `name` isn't the loaded model.

benchmark(name, rounds=3) -> list[dict]
    One dict per round: {"round": int (1-based), "ms": int, "tokens": int}.
    Rounds run "in parallel", so the list comes back in COMPLETION order (fastest
    first), not round order. Use the "round" field, not your loop index.
    Raises UnknownModel, NotLoaded (same rules as run), ValueError if rounds < 1.

Errors (all subclass ProviderError, which subclasses Exception)
    UnknownModel   bad model name. Never worth retrying.
    NotLoaded      the model exists but isn't loaded. Load it and try again.
    Timeout        transient. Retrying the same call can succeed.

Test / drill controls
---------------------
set_flaky(fail_times, only=None, model=None)
    The next `fail_times` matching calls raise Timeout before doing anything.
    `only` limits it to one function name ("run", "list_models", ...); `model` limits
    it to calls for that model name. Non-matching calls don't use up failures.
call_count(fn_name) -> int
    How many times a provider function has been called (failed calls count).
reset()
    Unload, clear flakiness, zero the call counts. Tests call this before each exercise.
"""

from collections import Counter


class ProviderError(Exception):
    pass


class UnknownModel(ProviderError):
    pass


class NotLoaded(ProviderError):
    pass


class Timeout(ProviderError):
    pass


_MODELS = [
    {"name": "phi3:mini", "size_gb": 2.3, "family": "phi"},
    {"name": "gemma2:2b", "size_gb": 1.6, "family": "gemma"},
    {"name": "mistral:7b", "size_gb": 4.1, "family": "mistral"},
    {"name": "llama3:8b", "size_gb": 4.7, "family": "llama"},
    {"name": "llama3:70b", "size_gb": 39.0, "family": "llama"},
]
_JITTER = [30, 0, 45, 10, 20]      # per-round ms offsets, so rounds finish out of order

_loaded: str | None = None
_calls: Counter = Counter()
_flaky = {"remaining": 0, "only": None, "model": None}


# ------------------------------------------------------------ internals ----

def _enter(fn_name: str, model: str | None = None) -> None:
    """Count the call, then maybe fail it with a simulated Timeout."""
    _calls[fn_name] += 1
    f = _flaky
    if f["remaining"] > 0 and f["only"] in (None, fn_name) and f["model"] in (None, model):
        f["remaining"] -= 1
        raise Timeout(f"{fn_name} timed out (simulated)")


def _model(name: str) -> dict:
    for m in _MODELS:
        if m["name"] == name:
            return m
    raise UnknownModel(f"no such model: {name!r}")


def _require_loaded(name: str) -> dict:
    model = _model(name)
    if _loaded != name:
        raise NotLoaded(f"{name} is not loaded")
    return model


# ----------------------------------------------------------- public API ----

def list_models() -> list[dict]:
    _enter("list_models")
    return [dict(m) for m in _MODELS]


def loaded() -> str | None:
    _enter("loaded")
    return _loaded


def load(name: str) -> dict:
    global _loaded
    _enter("load", name)
    model = _model(name)
    _loaded = name
    return {"name": name, "load_ms": round(model["size_gb"] * 100)}


def unload() -> str | None:
    global _loaded
    _enter("unload")
    was, _loaded = _loaded, None
    return was


def run(name: str, prompt: str) -> dict:
    _enter("run", name)
    model = _require_loaded(name)
    tokens = len(prompt.split()) + 2
    return {
        "text": f"{name} says: {prompt}",
        "tokens": tokens,
        "ms": round(model["size_gb"] * 40) + 15 * tokens,
    }


def benchmark(name: str, rounds: int = 3) -> list[dict]:
    _enter("benchmark", name)
    model = _require_loaded(name)
    if rounds < 1:
        raise ValueError("rounds must be >= 1")
    base = round(model["size_gb"] * 50)
    results = [
        {"round": i, "ms": base + _JITTER[(i - 1) % len(_JITTER)], "tokens": 64}
        for i in range(1, rounds + 1)
    ]
    return sorted(results, key=lambda r: (r["ms"], r["round"]))   # completion order


# ------------------------------------------------------- drill controls ----

def set_flaky(fail_times: int, only: str | None = None, model: str | None = None) -> None:
    _flaky.update(remaining=fail_times, only=only, model=model)


def call_count(fn_name: str) -> int:
    return _calls[fn_name]


def reset() -> None:
    global _loaded
    _loaded = None
    _calls.clear()
    _flaky.update(remaining=0, only=None, model=None)
