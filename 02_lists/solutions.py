"""02 - Lists: reference solutions.   Check them:  python 02_lists/solutions.py"""

from collections import deque


MODELS = [
    {"name": "phi3:mini", "provider": "ollama", "size_gb": 2.2, "loaded": True},
    {"name": "llama3:70b", "provider": "ollama", "size_gb": 39.0, "loaded": False},
    {"name": "gpt-4o", "provider": "openai", "size_gb": 0.0, "loaded": True},
    {"name": "mistral:7b", "provider": "ollama", "size_gb": 4.1},  # no "loaded" key
]


# ---------------------------------------------------------------- easy ----

def last_n(items: list, n: int) -> list:
    # -0 == 0, so items[-0:] is items[0:]: the whole list. Guard n == 0.
    return items[-n:] if n > 0 else []


def loaded_names(models: list[dict]) -> list[str]:
    return [m["name"] for m in models if m.get("loaded", False)]


def numbered_menu(options: list[str]) -> list[str]:
    return [f"{i}) {opt}" for i, opt in enumerate(options, start=1)]


def with_tag(tags: list[str], tag: str) -> list[str]:
    out = list(tags)  # a real copy; `out = tags` would make append() mutate the caller's list
    if tag not in out:
        out.append(tag)
    return out


# -------------------------------------------------------------- medium ----

def sort_bookings(bookings: list[dict]) -> list[dict]:
    # Stable sort, least significant key first. sorted() returns a new list;
    # list.sort() would reorder the caller's list in place (and return None).
    out = sorted(bookings, key=lambda b: b["guest"].lower())
    out.sort(key=lambda b: (b["date"], b["nights"]), reverse=True)
    return out
    # No single tuple key works: reverse=True would flip the guest order too, and a
    # string can't be negated the way -b["nights"] can.


def transpose(rows: list[list]) -> list[list]:
    # strict=True raises ValueError on ragged rows instead of silently truncating.
    return [list(col) for col in zip(*rows, strict=True)]


def dedupe(items: list, key=None) -> list:
    if key is None:
        return list(dict.fromkeys(items))
    seen = set()
    out = []
    for item in items:
        k = key(item)
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


def chunk(items: list, size: int) -> list[list]:
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i:i + size] for i in range(0, len(items), size)]


def rotate(items: list, k: int) -> list:
    if not items:
        return []
    k %= len(items)  # -1 % 5 == 4, 7 % 3 == 1
    return items[-k:] + items[:-k] if k else items[:]


def moving_average(values: list[float], k: int) -> list[float]:
    if k < 1:
        raise ValueError("k must be >= 1")
    if len(values) < k:
        return []
    window = sum(values[:k])
    out = [round(window / k, 2)]
    for i in range(k, len(values)):
        window += values[i] - values[i - k]
        out.append(round(window / k, 2))
    return out


# ------------------------------------------------------------ advanced ----

def flatten(nested) -> list:
    out = []
    stack = [iter(nested)]
    done = object()  # sentinel: can't collide with any real value, unlike None
    while stack:
        item = next(stack[-1], done)
        if item is done:
            stack.pop()
        elif isinstance(item, (list, tuple)):
            stack.append(iter(item))
        else:
            out.append(item)
    return out


def merge_intervals(bookings: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for start, end in sorted(bookings):
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out


def window_max(values: list[int], k: int) -> list[int]:
    if k < 1 or len(values) < k:
        return []
    dq: deque[int] = deque()  # indices; their values strictly decrease front to back
    out = []
    for i, v in enumerate(values):
        if dq and dq[0] <= i - k:
            dq.popleft()
        while dq and values[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            out.append(values[dq[0]])
    return out


def apply_edits(lines: list[str]) -> str:
    text = ""
    undo: list[str] = []  # snapshots of the text before each edit
    redo: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        cmd, _, arg = line.partition(" ")
        cmd = cmd.upper()
        if cmd == "TYPE":
            undo.append(text)
            redo.clear()
            text += arg
        elif cmd == "DELETE":
            n = int(arg)  # int("") / int("x") raise ValueError, which is what we want
            undo.append(text)
            redo.clear()
            text = text[:-n] if n > 0 else text  # same -0 trap as ex01
        elif cmd == "UNDO":
            if undo:
                redo.append(text)
                text = undo.pop()
        elif cmd == "REDO":
            if redo:
                undo.append(text)
                text = redo.pop()
        else:
            raise ValueError(f"unknown command: {cmd}")
    return text


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
