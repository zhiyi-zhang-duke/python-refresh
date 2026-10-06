"""01 - Strings: reference solutions.   Check them:  python 01_strings/solutions.py"""

import re
import shlex
from itertools import groupby


# ---------------------------------------------------------------- easy ----

def clean_command(raw: str) -> str:
    return raw.strip().lower()


def initials(full_name: str) -> str:
    return "".join(word[0].upper() + "." for word in full_name.split())


def normalize_city(raw: str) -> str:
    return " ".join(word.capitalize() for word in raw.split())


def parse_run(line: str) -> tuple[str, str, str]:
    # maxsplit=2 stops after two splits, so the prompt keeps its inner spacing.
    # lstrip first so leading spaces don't produce an empty first part.
    parts = line.lstrip().split(" ", maxsplit=2)
    parts += [""] * (3 - len(parts))
    cmd, model, prompt = parts
    return cmd, model, prompt


# -------------------------------------------------------------- medium ----

def tokenize(line: str) -> list[str] | None:
    try:
        return shlex.split(line)
    except ValueError:
        return None


def format_row(name: str, size_gb: float, loaded: bool) -> str:
    marker = "  *" if loaded else "   "
    return f"{name:<12}{size_gb:>5.1f} GB{marker}"


def is_palindrome(text: str) -> bool:
    chars = [c.casefold() for c in text if c.isalnum()]
    return chars == chars[::-1]


def run_length(s: str) -> str:
    out = []
    for ch, group in groupby(s):
        n = len(list(group))
        out.append(ch if n == 1 else f"{ch}{n}")
    return "".join(out)


def parse_flags(args: list[str]) -> tuple[str, dict[str, str]]:
    words, flags = [], {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            if i + 1 >= len(args):
                raise ValueError(f"flag {arg} needs a value")
            flags[arg.removeprefix("--")] = args[i + 1]
            i += 2
        else:
            words.append(arg)
            i += 1
    return " ".join(words), flags


# ------------------------------------------------------------ advanced ----

def wrap(text: str, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(template: str, ctx: dict) -> str:
    def replace(m: re.Match) -> str:
        key = m.group(1)
        return str(ctx[key]) if key in ctx else m.group(0)

    return PLACEHOLDER.sub(replace, template)


LOG_LINE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2}) "
    r"(?P<time>\d{2}:\d{2}:\d{2}) "
    r"(?P<level>DEBUG|INFO|WARNING|ERROR) "
    r"\[(?P<source>[^\]]+)\] "
    r"(?P<message>.*)"
)


def parse_log_line(line: str) -> dict | None:
    m = LOG_LINE.fullmatch(line)
    return m.groupdict() if m else None


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
