"""01 - Strings

Fill in each function, then run:   python 01_strings/exercises.py
Run just one exercise:             python 01_strings/exercises.py 4
Run exercise 4 onward:             python 01_strings/exercises.py 4+

Exercises go from easy (01) to advanced (12). Delete the `raise NotImplementedError`
line when you start one.
"""

import re
import shlex


# ---------------------------------------------------------------- easy ----

def clean_command(raw: str) -> str:
    """ex01. Strip surrounding whitespace (including newlines) and lowercase it.

    clean_command("  LIST  \\n") -> "list"

    Tools: str.strip, str.lower
    """
    raise NotImplementedError


def initials(full_name: str) -> str:
    """ex02. Uppercase first letter of each word, each followed by a dot.

    initials("  grace   brewster  hopper ") -> "G.B.H."
    initials("") -> ""

    Tools: str.split() with NO argument (it collapses runs of whitespace), "".join
    """
    raise NotImplementedError


def normalize_city(raw: str) -> str:
    """ex03. Collapse whitespace and capitalize each word.

    normalize_city("  new   YORK ") -> "New York"

    Tools: split / " ".join, str.capitalize (careful: str.title does odd things to "o'neil")
    """
    raise NotImplementedError


def parse_run(line: str) -> tuple[str, str, str]:
    """ex04. Split a REPL line into (command, model, prompt).

    The prompt is everything after the model, kept EXACTLY as typed (inner spaces too).
    Missing parts become "". Ignore leading whitespace.

    parse_run("run phi3:mini tell me  a joke") -> ("run", "phi3:mini", "tell me  a joke")
    parse_run("list")                          -> ("list", "", "")

    Tools: str.split(maxsplit=...), padding a list to a fixed length
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

def tokenize(line: str) -> list[str] | None:
    """ex05. Shell-style split: quoted strings stay one token.

    tokenize('add "New York" --unit C') -> ["add", "New York", "--unit", "C"]
    Unbalanced quotes -> return None instead of crashing.

    Tools: shlex.split (raises ValueError on unbalanced quotes), try/except
    """
    raise NotImplementedError


def format_row(name: str, size_gb: float, loaded: bool) -> str:
    """ex06. Format one row of a model table. Total width is always 23 characters:

        name   : left-aligned, 12 wide
        size   : right-aligned, 5 wide, 1 decimal place, then " GB"
        loaded : "  *" if loaded else "   "

    format_row("phi3:mini", 2.26, True)   -> "phi3:mini     2.3 GB  *"
    format_row("llama3:70b", 39.0, False) -> "llama3:70b   39.0 GB   "

    Tools: f-string format specs  f"{x:<12}"  f"{y:>5.1f}"
    """
    raise NotImplementedError


def is_palindrome(text: str) -> bool:
    """ex07. True if text reads the same backwards, ignoring case and anything
    that isn't a letter or digit.

    is_palindrome("A man, a plan, a canal: Panama!") -> True

    Tools: str.isalnum, str.casefold, slicing s[::-1]
    """
    raise NotImplementedError


def run_length(s: str) -> str:
    """ex08. Run-length encode. Single characters get no count.

    run_length("aaabccdddd") -> "a3bc2d4"
    run_length("zzzzzzzzzzzz") -> "z12"

    Tools: a loop tracking the current char and count, OR itertools.groupby
    """
    raise NotImplementedError


def parse_flags(args: list[str]) -> tuple[str, dict[str, str]]:
    """ex09. Split CLI args into a positional phrase and a dict of --flags.

    Every "--name" consumes the next arg as its value. Everything else is a
    positional word; join positional words with single spaces.

    parse_flags(["New", "York", "--unit", "C"]) -> ("New York", {"unit": "C"})
    parse_flags(["--days", "3", "Durham"])      -> ("Durham", {"days": "3"})
    parse_flags(["Durham", "--unit"])           -> raises ValueError (flag with no value)

    Tools: a while loop with an index (a for loop can't easily skip ahead), str.startswith,
           s.removeprefix("--")
    """
    raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def wrap(text: str, width: int) -> list[str]:
    """ex10. Greedy word wrap, no textwrap module allowed.

    Pack as many words per line as fit within `width` (words separated by one space).
    A single word longer than `width` goes on its own line, unbroken.

    wrap("the quick brown fox jumps over the lazy dog", 10)
      -> ["the quick", "brown fox", "jumps over", "the lazy", "dog"]
    """
    raise NotImplementedError


def render(template: str, ctx: dict) -> str:
    """ex11. Replace {{ key }} placeholders (any amount of inner whitespace) with str(ctx[key]).

    Placeholders whose key is NOT in ctx are left exactly as written.

    render("Hi {{ name }}, {{count}} new", {"name": "Jack", "count": 3}) -> "Hi Jack, 3 new"

    Tools: re.sub(pattern, replacement_function, text). The function receives a
           re.Match; m.group(0) is the whole match, m.group(1) the first capture group.
    """
    raise NotImplementedError


def parse_log_line(line: str) -> dict | None:
    """ex12. Parse a log line into a dict, or return None if it doesn't match.

    Format:  "<YYYY-MM-DD> <HH:MM:SS> <LEVEL> [<source>] <message>"
    LEVEL must be one of DEBUG, INFO, WARNING, ERROR.

    "2026-09-14 10:03:22 ERROR [provider] Model not loaded: phi3" ->
        {"date": "2026-09-14", "time": "10:03:22", "level": "ERROR",
         "source": "provider", "message": "Model not loaded: phi3"}

    Tools: re.fullmatch, named groups (?P<name>...), match.groupdict()
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
