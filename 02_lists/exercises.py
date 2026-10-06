"""02 - Lists

Fill in each function, then run:   python 02_lists/exercises.py
Run just one exercise:             python 02_lists/exercises.py 4
Run exercise 4 onward:             python 02_lists/exercises.py 4+

Exercises go from easy (01) to advanced (14). Delete the `raise NotImplementedError`
line when you start one.
"""

from collections import deque


MODELS = [
    {"name": "phi3:mini", "provider": "ollama", "size_gb": 2.2, "loaded": True},
    {"name": "llama3:70b", "provider": "ollama", "size_gb": 39.0, "loaded": False},
    {"name": "gpt-4o", "provider": "openai", "size_gb": 0.0, "loaded": True},
    {"name": "mistral:7b", "provider": "ollama", "size_gb": 4.1},  # no "loaded" key
]


# ---------------------------------------------------------------- easy ----

def last_n(items: list, n: int) -> list:
    """ex01. Return the last n items (n >= 0). If n > len(items), return all of them.

    last_n([1, 2, 3, 4, 5], 2) -> [4, 5]
    last_n([1, 2, 3], 10)      -> [1, 2, 3]
    last_n([1, 2, 3], 0)       -> []      <- careful: items[-0:] is the WHOLE list

    Tools: negative slicing items[-n:]
    """
    raise NotImplementedError


def loaded_names(models: list[dict]) -> list[str]:
    """ex02. Names of the models whose "loaded" flag is True, in input order.
    A record with no "loaded" key counts as not loaded.

    loaded_names(MODELS) -> ["phi3:mini", "gpt-4o"]

    Tools: list comprehension with an `if`, dict.get(key, default)
    """
    raise NotImplementedError


def numbered_menu(options: list[str]) -> list[str]:
    """ex03. Number each option starting at 1.

    numbered_menu(["list", "load", "quit"]) -> ["1) list", "2) load", "3) quit"]

    Tools: enumerate(iterable, start=1), f-strings
    """
    raise NotImplementedError


def with_tag(tags: list[str], tag: str) -> list[str]:
    """ex04. Return a NEW list: `tags` plus `tag` at the end, unless it's already there.
    The caller's list must never be modified, and the result must never be the
    same object as `tags` (even when nothing was added).

    t = ["fast"];  u = with_tag(t, "local")  ->  u == ["fast", "local"],  t == ["fast"]

    Tools: tags[:] or list(tags) (a copy), `in`. Note `u = t` copies nothing, it's an alias.
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def sort_bookings(bookings: list[dict]) -> list[dict]:
    """ex05. Return the bookings sorted (do NOT reorder the caller's list):

        1. date      newest first     ("YYYY-MM-DD" strings sort correctly as strings)
        2. nights    most first
        3. guest     A to Z, case-insensitive

    Each booking looks like {"guest": "Ana", "date": "2026-10-03", "nights": 2}.

    Tools: sorted(key=..., reverse=...), tuple keys, negating numbers. You can't negate
           a string: either negate what you can, or lean on the fact that sorting is
           STABLE and sort several times, last key first.
    """
    raise NotImplementedError


def transpose(rows: list[list]) -> list[list]:
    """ex06. Turn rows into columns. All rows must be the same length; if they
    aren't, raise ValueError. No rows -> [].

    transpose([["phi3", 2.2], ["llama3", 39.0]]) -> [["phi3", "llama3"], [2.2, 39.0]]

    Tools: zip(*rows) (the * unpacks the list into separate args), zip(..., strict=True) (3.10+)
    """
    raise NotImplementedError


def dedupe(items: list, key=None) -> list:
    """ex07. Remove duplicates, keeping the FIRST occurrence and the original order.
    If `key` is given, two items are duplicates when key(a) == key(b).

    dedupe([3, 1, 3, 2, 1])                          -> [3, 1, 2]
    dedupe(["Durham", "durham", "Cary"], key=str.lower) -> ["Durham", "Cary"]

    Tools: dict.fromkeys(items) (dicts keep insertion order), a `seen` set
    """
    raise NotImplementedError


def chunk(items: list, size: int) -> list[list]:
    """ex08. Split into consecutive batches of `size`; the last batch may be shorter.
    size < 1 -> raise ValueError.

    chunk([1, 2, 3, 4, 5], 2) -> [[1, 2], [3, 4], [5]]

    Tools: range(start, stop, step), slicing (slices past the end don't raise)
    """
    raise NotImplementedError


def rotate(items: list, k: int) -> list:
    """ex09. Rotate RIGHT by k (negative k rotates left). k may be bigger than the
    list. Return a new list.

    rotate([1, 2, 3, 4, 5], 2)  -> [4, 5, 1, 2, 3]
    rotate([1, 2, 3, 4, 5], -1) -> [2, 3, 4, 5, 1]
    rotate([1, 2, 3], 7)        -> [3, 1, 2]
    rotate([], 3)               -> []

    Tools: % (Python's modulo is never negative for a positive divisor), slicing, +
    """
    raise NotImplementedError


def moving_average(values: list[float], k: int) -> list[float]:
    """ex10. Average of every window of k consecutive values, rounded to 2 decimals.
    Fewer than k values -> []. k < 1 -> raise ValueError. Aim for O(n): keep a
    running sum instead of re-summing each window.

    moving_average([100, 200, 300, 400], 2) -> [150.0, 250.0, 350.0]

    Tools: sum(values[:k]) once, then add the new value and subtract the one leaving; round()
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def flatten(nested) -> list:
    """ex11. Flatten lists and tuples nested to ANY depth. Strings are values,
    not sequences to break apart. Must handle nesting thousands of levels deep, so
    recursion will hit the recursion limit (~1000): use an explicit stack.

    flatten([1, [2, (3, [4])], "ab", []]) -> [1, 2, 3, 4, "ab"]

    Tools: isinstance(x, (list, tuple)), a stack of iterators: stack = [iter(nested)],
           next(it, sentinel)
    """
    raise NotImplementedError


def merge_intervals(bookings: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """ex12. Merge room bookings (start, end) that overlap OR touch (10-11 and 11-12
    become 10-12). Input is unsorted; output is sorted by start. Don't modify the input.

    merge_intervals([(13, 15), (9, 10), (10, 11), (14, 17)]) -> [(9, 11), (13, 17)]

    Tools: sorted(), compare each interval's start with the LAST merged interval's end,
           out[-1] to read/replace the last element, max()
    """
    raise NotImplementedError


def window_max(values: list[int], k: int) -> list[int]:
    """ex13. Max of every window of k consecutive values. Fewer than k values -> [].
    O(n*k) with max() on each slice is the easy answer; the target is O(n).

    window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) -> [3, 3, 5, 5, 6, 7]

    Tools: collections.deque of INDICES whose values are decreasing front to back;
           popleft() indices that slid out of the window, pop() values smaller than
           the newcomer. dq[0] is always the current max.
    """
    raise NotImplementedError


def apply_edits(lines: list[str]) -> str:
    """ex14. A tiny text editor. Start with "" and apply each command; return the text.

        TYPE <text>   append <text> (everything after "TYPE ", inner spaces kept)
        DELETE <n>    remove the last n characters (more than the length -> "")
        UNDO          revert the most recent TYPE/DELETE that hasn't been undone (no-op if none)
        REDO          re-apply the most recently undone edit (no-op if none).
                      Any new TYPE/DELETE clears the redo history.

    Each line should be .strip()ped first; blank lines are skipped. Command names are
    case-insensitive. Anything else -> raise ValueError.

    apply_edits(["TYPE hello", "TYPE  world", "DELETE 6", "UNDO"]) -> "hello world"

    Tools: two lists used as stacks (append / pop), str.partition(" ") (careful:
           split(maxsplit=1) with NO separator would eat the extra space before "world")
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
