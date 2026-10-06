"""03 - Dicts and sets: reference solutions.   Check them:  python 03_dicts_sets/solutions.py"""

import copy
import shlex
from collections import Counter, OrderedDict, defaultdict, deque

import provider


LOG_LINES = [
    "2026-09-14 10:03:22 INFO [cli] started",
    "2026-09-14 10:03:25 ERROR [provider] Model not loaded: phi3",
    "2026-09-14 10:03:26 WARNING [cache] miss rate high",
    "2026-09-14 10:03:30 ERROR [cli] bad command: lod",
    "",
    "2026-09-14 10:04:01 ERROR [provider] timeout after 30s",
    "2026-09-14 10:04:02 INFO [provider] retrying",
    "2026-09-14 10:04:09 ERROR [db] connection refused",
    "2026-09-14 10:04:10 ERROR [cli] bad command: wether",
    "2026-09-14 10:04:15 ERROR [provider] timeout after 30s",
]

MODELS = [
    {"name": "phi3:mini", "provider": "ollama", "size_gb": 2.2},
    {"name": "gpt-4o", "provider": "openai", "size_gb": 0.0},
    {"name": "llama3:70b", "provider": "ollama", "size_gb": 39.0},
    {"name": "mystery-7b", "size_gb": 4.1},  # no "provider" key
]

PROFILES = {
    "default": {"unit": "F", "uses": 0},
    "metric": {"unit": "C", "uses": 0},
}
ACTIVE_PROFILE = "default"


# ---------------------------------------------------------------- easy ----

def get_price(prices: dict[str, float], item: str) -> float:
    return prices.get(item.strip().lower(), 0.0)


def count_levels(lines: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        if not line.strip():
            continue
        level = line.split()[2]
        counts[level] = counts.get(level, 0) + 1
    return counts


def merge_config(defaults: dict, overrides: dict) -> dict:
    # `is not None`, not truthiness: an override of 0 or False is a real value.
    return defaults | {k: v for k, v in overrides.items() if v is not None}


def switch_profile(name: str) -> dict:
    # Without `global`, the assignment below would create a LOCAL ACTIVE_PROFILE and the
    # module-level one would never change. PROFILES needs no declaration: we only
    # mutate the object it points at, we never rebind the name.
    global ACTIVE_PROFILE
    key = name.strip().lower()
    profile = PROFILES[key]  # KeyError before anything changes
    ACTIVE_PROFILE = key
    profile["uses"] += 1
    return profile


# -------------------------------------------------------------- medium ----

def top_sources(lines: list[str], n: int) -> list[tuple[str, int]]:
    counts = Counter(
        line.split()[3].strip("[]")
        for line in lines
        if line.strip() and line.split()[2] == "ERROR"
    )
    return counts.most_common(n)  # ties come out in first-seen order


def group_by_provider(models: list[dict]) -> dict[str, list[str]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for m in models:
        groups[m.get("provider", "unknown")].append(m["name"])
    return dict(groups)  # a defaultdict leaks: reading a missing key would INSERT it


def invert(aliases: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for alias, model in aliases.items():
        out.setdefault(model, []).append(alias)
    return {model: sorted(names) for model, names in out.items()}


def diff_hosts(local: list[str], remote: list[str]) -> dict[str, list[str]]:
    a, b = set(local), set(remote)
    return {
        "both": sorted(a & b),
        "only_local": sorted(a - b),
        "only_remote": sorted(b - a),
        "out_of_sync": sorted(a ^ b),
        "all": sorted(a | b),
    }


def rank_by_value(scores: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def get_path(data, path: str, default=None):
    cur = data
    for seg in path.split("."):
        if isinstance(cur, dict):
            if seg not in cur:
                return default
            cur = cur[seg]
        elif isinstance(cur, list) and seg.isdigit() and int(seg) < len(cur):
            cur = cur[int(seg)]
        else:
            return default
    return cur


# ------------------------------------------------------------ advanced ----

def cmd_weather(args: list[str]) -> str:
    if not args:
        raise ValueError("city required")
    city = " ".join(args)
    return f"{city}: {provider.get_temp(city)}F"


def run_repl(read_line, commands: dict) -> list[str]:
    out: list[str] = []
    while True:
        try:
            line = read_line()
        except (EOFError, KeyboardInterrupt):  # a tuple: one except, several types
            break
        line = line.strip()
        if not line:
            continue
        try:
            tokens = shlex.split(line)
        except ValueError:
            out.append("error: unbalanced quotes")
            continue
        name, args = tokens[0].lower(), tokens[1:]
        if name in ("quit", "exit"):
            break
        entry = commands.get(name)
        if entry is None:
            out.append(f"unknown command: {name}")
            continue
        handler, usage = entry
        try:
            out.append(handler(args))
        except provider.UnknownCity as e:  # the exception lives in the provider module
            out.append(f"unknown city: {e}")
        except ValueError:
            out.append(f"usage: {usage}")
    return out


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    _merge_into(out, override)
    return out


def _merge_into(dst: dict, src: dict) -> None:
    for k, v in src.items():
        if isinstance(dst.get(k), dict) and isinstance(v, dict):
            _merge_into(dst[k], v)
        else:
            dst[k] = copy.deepcopy(v)  # don't hand back a reference into `override`


class LRUCache:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._data: OrderedDict = OrderedDict()  # front = least recently used

    def get(self, key, default=None):
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key, value) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __len__(self) -> int:
        return len(self._data)

    def keys(self) -> list:
        return list(self._data)


def shortest_route(flights: list[tuple[str, str]], start: str, goal: str) -> list[str] | None:
    if start == goal:
        return [start]
    graph: defaultdict[str, set[str]] = defaultdict(set)
    for origin, dest in flights:
        graph[origin].add(dest)

    came_from = {start: None}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in sorted(graph.get(node, ())):  # .get: don't grow the defaultdict
            if nxt in came_from:
                continue
            came_from[nxt] = node
            if nxt == goal:
                path = [goal]
                while came_from[path[-1]] is not None:
                    path.append(came_from[path[-1]])
                return path[::-1]
            queue.append(nxt)
    return None


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
