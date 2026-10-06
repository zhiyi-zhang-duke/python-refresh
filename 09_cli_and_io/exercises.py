"""09 - CLI and IO

Fill in each function, then run:   python 09_cli_and_io/exercises.py
Run just one exercise:             python 09_cli_and_io/exercises.py 4
Run exercise 4 onward:             python 09_cli_and_io/exercises.py 4+

Exercises go from easy (01) to advanced (13). Delete the `raise NotImplementedError`
line when you start one.

Every function here takes its streams as arguments instead of touching the real
terminal, so the tests can drive it with io.StringIO:

    print("hi", file=out)          # write a line to ANY text stream (out, err, a file...)
    for line in stdin: ...         # each line still ends in "\\n"
    stdin.readline()               # returns "" at end of input: the StringIO version
                                   # of input() raising EOFError

In a real program you pass sys.stdin / sys.stdout / sys.stderr.
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import TextIO


# ---------------------------------------------------------------- easy ----

def read_commands(stdin: TextIO) -> list[str]:
    """ex01. Read every line from `stdin`, strip it, and skip blank lines and
    lines that start with "#" (after stripping).

    read_commands(io.StringIO("list\\n\\n  load phi3  \\n# a comment\\nexit"))
      -> ["list", "load phi3", "exit"]

    Tools: `for line in stdin:` (each line keeps its "\\n"), str.strip, str.startswith
    """
    raise NotImplementedError


def print_kv(pairs: dict, out: TextIO) -> None:
    """ex02. Print one "key: value" line per item, in insertion order.

    print_kv({"model": "phi3", "rounds": 3}, out)
    out now holds: "model: phi3\\nrounds: 3\\n"

    Tools: print(a, b, sep=": ", file=out). print() calls str() on every argument,
           so ints need no conversion.
    """
    raise NotImplementedError


def progress(label: str, steps: int, out: TextIO) -> None:
    """ex03. Print `label`, then one "." per step, all on ONE line, then " done".

    progress("loading", 3, out)   -> out holds "loading... done\\n"
    progress("loading", 0, out)   -> out holds "loading done\\n"

    Write the dots one print() call at a time, the way a real progress bar would.

    Tools: print(..., end="", file=out) suppresses the newline. On a real terminal
           add flush=True or the partial line may not appear until the newline.
    """
    raise NotImplementedError


def echo_loop(stdin: TextIO, out: TextIO) -> int:
    """ex04. A tiny REPL. Returns how many lines it echoed.

    Each turn:
      - write the prompt "> " with NO newline
      - read one line; "" means EOF -> stop
      - strip it; blank -> next turn (prompt again)
      - "exit" or "quit" (any case) -> stop
      - otherwise print "echo: <stripped line>"
    After the loop, print "bye".

    echo_loop(io.StringIO("hi\\n\\n  there \\nEXIT\\nnever\\n"), out) -> 2
    out holds: "> echo: hi\\n> > echo: there\\n> bye\\n"

    Tools: stdin.readline(), `if not line:` for EOF, a `while True` loop with break.
           With the real input() you'd catch (EOFError, KeyboardInterrupt) instead.
    """
    raise NotImplementedError


# -------------------------------------------------------------- medium ----

USAGE = "usage: greet NAME... [--shout]"


def greet_main(argv: list[str], out: TextIO, err: TextIO) -> int:
    """ex05. A hand-rolled sys.argv CLI. `argv` is sys.argv[1:] (no program name).
    Return the exit code; don't call sys.exit.

    - "-h" or "--help" anywhere: print USAGE to OUT, return 0
    - "--shout": greet in uppercase with "!" instead of "."
    - any other arg starting with "-": print "error: unknown option <arg>" then USAGE
      to ERR, return 2
    - the remaining words, joined by single spaces, are the name. No name: print
      USAGE to ERR, return 2
    - success: print the greeting to OUT, return 0

    greet_main(["Ada", "Lovelace"], out, err)     -> 0, out: "Hello, Ada Lovelace.\\n"
    greet_main(["ada", "--shout"], out, err)      -> 0, out: "HELLO, ADA!\\n"
    greet_main([], out, err)                      -> 2, err: USAGE + "\\n", out empty
    greet_main(["Ada", "--loud"], out, err)       -> 2, err: "error: unknown option --loud\\n" + USAGE + "\\n"

    Tools: exit codes are a convention: 0 ok, 1 runtime failure, 2 usage error.
           Help that was ASKED for goes to stdout; errors go to stderr.
    """
    raise NotImplementedError


def append_log(path: Path, level: str, message: str, when: datetime) -> str:
    """ex06. Append one line to a log file and return it (without the newline).

    Line format: "<YYYY-MM-DD HH:MM:SS> <LEVEL> <message>", LEVEL uppercased.
    LEVEL must be one of DEBUG, INFO, WARNING, ERROR, otherwise raise ValueError
    and write nothing. Create missing parent folders. Never overwrite earlier lines.

    append_log(p, "error", "model not loaded", datetime(2026, 9, 14, 10, 3, 22))
      -> "2026-09-14 10:03:22 ERROR model not loaded"

    Tools: open(path, "a", encoding="utf-8") in a `with` block, when.strftime(...),
           path.parent.mkdir(parents=True, exist_ok=True)
    """
    raise NotImplementedError


def parse_weather_args(argv: list[str]) -> dict | None:
    """ex07. Parse weather-CLI arguments with argparse. Return a dict, or None if the
    arguments are invalid.

        city        one or more words, joined with single spaces   (positional)
        --days N    int, default 1
        --unit U    "C" or "F", default "F"
        -v, --verbose   flag, default False

    parse_weather_args(["New", "York", "--unit", "C", "--days", "3"])
      -> {"city": "New York", "days": 3, "unit": "C", "verbose": False}
    parse_weather_args(["Durham", "--unit", "K"])   -> None
    parse_weather_args([])                          -> None

    Gotcha: on bad input argparse prints an error to stderr and raises SystemExit(2).
    That would kill your REPL, so catch it here.

    Tools: argparse.ArgumentParser(prog=...), add_argument("city", nargs="+"),
           type=int, choices=[...], action="store_true", parser.parse_args(argv),
           vars(namespace) -> dict
    """
    raise NotImplementedError


def sync_notes(root: Path, notes: dict[str, str]) -> list[str]:
    """ex08. Write each note to root/"notes"/"<name>.md" (UTF-8), creating the folder
    (and any missing parents of root). Then return the sorted stems of EVERY .md file
    in that folder, including ones that were already there.

    With notes/old.md and notes/readme.txt already present:
    sync_notes(root, {"b": "beta", "a": "alpha"}) -> ["a", "b", "old"]

    Tools: root / "notes" (the / operator joins paths), Path.mkdir(parents=True,
           exist_ok=True), Path.write_text(text, encoding="utf-8"), Path.glob("*.md"),
           p.stem ("a.md" -> "a"), p.name, p.suffix
    """
    raise NotImplementedError


class SettingsStore:
    """ex09. A tiny JSON-backed settings store.

    SettingsStore(path, defaults)
        Remember both. Don't touch the disk yet. Never mutate `defaults`.
    load() -> dict
        A NEW dict: defaults overlaid with whatever the file holds. If the file is
        missing or isn't valid JSON, just the defaults.
    get(key)
        load()[key]  (KeyError if it's in neither)
    set(key, value) -> None
        load(), change one key, write the whole dict back as JSON
        (indent=2, sort_keys=True). A brand-new SettingsStore on the same path sees it.

    s = SettingsStore(tmp / "settings.json", {"unit": "F", "days": 1})
    s.get("unit")          -> "F"
    s.set("unit", "C")
    SettingsStore(tmp / "settings.json", {"unit": "F", "days": 1}).get("unit") -> "C"

    Tools: json.load(f) / json.dump(obj, f, indent=2), {**a, **b} or dict(a) + update,
           except (FileNotFoundError, json.JSONDecodeError)
    """

    def __init__(self, path: Path, defaults: dict):
        raise NotImplementedError

    def load(self) -> dict:
        raise NotImplementedError

    def get(self, key: str):
        raise NotImplementedError

    def set(self, key: str, value) -> None:
        raise NotImplementedError


# ------------------------------------------------------------ advanced ----

def summarize_runs(src: Path, dst: Path) -> int:
    """ex10. Read a CSV of benchmark runs and write a per-model summary CSV.
    Return how many data rows were read from `src`.

    src columns:  model,ms,tokens         (one row per run, any order)
    dst columns:  model,runs,avg_ms,total_tokens
                  one row per model, sorted by model name, avg_ms formatted "%.1f"

    src:                         dst:
        model,ms,tokens              model,runs,avg_ms,total_tokens
        phi3,120,40                  llama3,1,900.0,50
        llama3,900,50                phi3,2,125.0,70
        phi3,130,30

    Gotchas: csv values are always strings (int() them). On Windows, open CSV files
    with newline="" or every row gets a blank line after it.

    Tools: csv.DictReader(f), csv.DictWriter(f, fieldnames=[...]), writer.writeheader(),
           writer.writerow(dict), collections.defaultdict(list)
    """
    raise NotImplementedError


def render_table(headers: list[str], rows: list[list], out: TextIO, align: str = "") -> None:
    """ex11. Print an aligned table. Each column is as wide as its widest cell
    (header included). Columns are separated by two spaces. Under the header, print
    a row of dashes as wide as each column. Cells are str()'d. `align` has one char
    per column, "<" (left) or ">" (right); "" means all left. Strip trailing spaces
    from every line.

    render_table(["model", "size", "family"],
                 [["phi3:mini", 2.3, "phi"], ["llama3:70b", 39.0, "llama"]],
                 out, align="<><")
    out holds:
        model       size  family
        ----------  ----  ------
        phi3:mini    2.3  phi
        llama3:70b  39.0  llama

    Tools: max(len(...) for ...), nested format spec f"{cell:{a}{w}}",
           zip(row, align, widths), "  ".join(...), str.rstrip
    """
    raise NotImplementedError


def parse_olm(argv: list[str]) -> dict:
    """ex12. argparse with subcommands, raising ValueError instead of exiting.

        list                         -> {"cmd": "list"}
        run MODEL PROMPT...          -> {"cmd": "run", "model": "phi3", "prompt": "tell me a joke"}
        bench MODEL [--rounds N]     -> {"cmd": "bench", "model": "phi3", "rounds": 3}   (int, default 3)

    Anything invalid (no subcommand, unknown subcommand, missing argument, a
    non-int --rounds, extra arguments) raises ValueError carrying argparse's message.
    Nothing may be printed to stderr.

    Gotcha: exit_on_error=False is leaky in 3.10 (missing arguments still exit).
    The reliable trick is to subclass ArgumentParser and override error(self, message).
    Subparsers are built with the parent's class, so they inherit the override.

    Tools: sub = parser.add_subparsers(dest="cmd", required=True),
           p = sub.add_parser("run"), p.add_argument(...), vars(ns)
    """
    raise NotImplementedError


def todo_main(argv: list[str], out: TextIO, err: TextIO, path: Path) -> int:
    """ex13. A whole little CLI: argparse subcommands + a JSON file + exit codes.

    Todos live in `path` as a JSON list of {"text": str, "done": bool}.
    A missing file means no todos. Create parent folders when saving.

        add TEXT...   append a todo, print "added #N: <text>"         -> 0
        list          print "[ ] 1. buy milk" / "[x] 2. call mom" per todo,
                      or "no todos" if there are none                  -> 0
        done N        mark todo N (1-based) done, print "done #N: <text>" -> 0
                      no such todo: print "error: no todo #N" to ERR   -> 1
        bad usage     (unknown/missing subcommand, non-int N, ...):
                      print an error to ERR, nothing to OUT            -> 2

    Tools: the ex12 parser trick, Path.read_text / write_text, json.loads / dumps,
           enumerate(todos, start=1)
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
