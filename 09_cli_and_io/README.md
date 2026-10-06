# 09 - CLI and IO

```bash
python 09_cli_and_io/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `read_commands` | easy | `for line in stream`, `strip`, skip blanks |
| 02 | `print_kv` | easy | `print(..., sep=, file=)` |
| 03 | `progress` | easy | `print(..., end="", flush=True)` |
| 04 | `echo_loop` | easy | prompt + `readline()`, `""` is EOF, exit/quit |
| 05 | `greet_main` | medium | hand-rolled `sys.argv`, exit codes, stdout vs stderr |
| 06 | `append_log` | medium | `open(..., "a")`, `strftime`, `mkdir(parents=True)` |
| 07 | `parse_weather_args` | medium | argparse `nargs="+"`, `type=int`, `choices`, `store_true`, `SystemExit` |
| 08 | `sync_notes` | medium | `pathlib`: `/`, `write_text`, `glob`, `stem` |
| 09 | `SettingsStore` | medium | `json.load` / `json.dump`, defaults overlay |
| 10 | `summarize_runs` | advanced | `csv.DictReader` / `DictWriter`, `newline=""` |
| 11 | `render_table` | advanced | widths from data, nested format spec `f"{v:{a}{w}}"` |
| 12 | `parse_olm` | advanced | argparse subcommands, overriding `error()` |
| 13 | `todo_main` | advanced | subcommands + JSON file + exit codes, end to end |

## Cheat sheet

### Streams and print

```python
import sys
print("hi", file=sys.stderr)          # any text stream: sys.stdout, sys.stderr, an open file, io.StringIO
print("a", "b", sep=", ")             # "a, b\n"
print("loading", end="", flush=True)  # no newline; flush so a terminal shows it NOW
print()                               # just "\n"

line = input("> ")                    # strips the trailing "\n"; raises EOFError on Ctrl-D/EOF,
                                      # KeyboardInterrupt on Ctrl-C  ->  except (EOFError, KeyboardInterrupt)
line = sys.stdin.readline()           # KEEPS "\n"; returns "" at EOF (never raises)
for line in sys.stdin: ...            # each line keeps "\n"; loop ends at EOF
data = sys.stdin.read()               # everything at once

import io
buf = io.StringIO("list\nexit\n")     # fake stdin for tests
out = io.StringIO(); print("x", file=out); out.getvalue()   # "x\n"
```

Gotcha: `if not line:` means EOF only for `readline()`. A blank line is `"\n"`, which is truthy.
Strip AFTER the EOF check, or a blank line looks like EOF.

### Testable CLI shape

```python
def main(argv: list[str], out=sys.stdout, err=sys.stderr) -> int:
    ...
    return 0                          # 0 ok, 1 runtime failure, 2 usage error

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))      # argv[0] is the script name; the shell already split the rest
```

- Asked-for `--help` goes to stdout with exit 0. Errors and usage-on-error go to stderr with exit 2.
- `sys.argv[1:]` is already split by the shell (`"New York"` is one arg). Inside a REPL you split the raw line yourself (`shlex.split` or `split(maxsplit=1)`).
- PowerShell: `$LASTEXITCODE` after a command. Bash: `$?`.

### argparse

```python
import argparse
p = argparse.ArgumentParser(prog="weather")
p.add_argument("city", nargs="+")                     # list of 1+ words; nargs="*" allows 0, "?" optional
p.add_argument("--days", type=int, default=1)         # "--days" -> args.days
p.add_argument("--unit", choices=["C", "F"], default="F")
p.add_argument("-v", "--verbose", action="store_true")
p.add_argument("--max-tokens", type=int)              # dashes become underscores: args.max_tokens
args = p.parse_args(argv)                             # pass argv explicitly; None means sys.argv[1:]
vars(args)                                            # Namespace -> dict

sub = p.add_subparsers(dest="cmd", required=True)     # without dest= you can't tell which subcommand ran
run = sub.add_parser("run"); run.add_argument("model")
args.cmd                                              # "run"
```

Gotchas:
- On bad input argparse prints to stderr and raises `SystemExit(2)`. `--help` prints and raises `SystemExit(0)`. In a REPL, catch `SystemExit` or the session dies.
- `exit_on_error=False` (3.9+) only covers some errors. Missing required args still exit in 3.10. Reliable fix:

```python
class RaisingParser(argparse.ArgumentParser):
    def error(self, message):            # called for every usage error
        raise ValueError(message)        # subparsers inherit this (they're built with type(parent))
```

### Files

```python
from pathlib import Path
p = Path("data") / "notes" / "a.md"     # / joins; works on Windows too
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("hi", encoding="utf-8")    # ALWAYS pass encoding: Windows defaults to cp1252
p.read_text(encoding="utf-8")
p.exists() / p.is_file() / p.is_dir()
p.name "a.md"   p.stem "a"   p.suffix ".md"   p.parent Path("data/notes")
sorted(Path("data").glob("*.md"))       # glob order is NOT guaranteed: sort it
Path("data").rglob("*.md")              # recursive
p.unlink(missing_ok=True)

with open(p, "a", encoding="utf-8") as f:   # "r" read, "w" truncate+write, "a" append, "x" fail if exists
    f.write("line\n")                       # write() does NOT add a newline
for line in open(p, encoding="utf-8"): ...  # fine in a script, but `with` closes it deterministically
```

Gotcha: on Windows you can't delete a file that's still open, so `TemporaryDirectory()` cleanup
fails if you forget `with`.

### JSON and CSV

```python
import json
json.dumps(obj, indent=2, sort_keys=True)    # -> str
json.loads(s)                                # str -> obj; raises json.JSONDecodeError (a ValueError)
with open(p, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2)
with open(p, encoding="utf-8") as f: obj = json.load(f)
# tuples become lists, dict keys become strings: json.loads(json.dumps({1: (2, 3)})) == {"1": [2, 3]}

import csv
with open(p, newline="", encoding="utf-8") as f:          # newline="" for csv, read AND write
    for row in csv.DictReader(f):                         # row = {"model": "phi3", "ms": "120"}  (all str!)
        ms = int(row["ms"])
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["model", "ms"])
    w.writeheader()
    w.writerow({"model": "phi3", "ms": 120})              # extra keys -> ValueError (extrasaction="ignore")
    w.writerows(rows)
```

Gotcha: without `newline=""` on Windows, csv writes `\r\r\n`, which shows up as a blank line between rows.

### Table renderer (write it once, reuse it)

```python
def render_table(headers, rows, align=""):
    align = align or "<" * len(headers)
    cells = [[str(c) for c in row] for row in rows]
    widths = [max([len(h)] + [len(r[i]) for r in cells]) for i, h in enumerate(headers)]
    fmt = lambda vals: "  ".join(f"{v:{a}{w}}" for v, a, w in zip(vals, align, widths)).rstrip()
    print(fmt(headers)); print("  ".join("-" * w for w in widths))
    for r in cells: print(fmt(r))
```

### Dates for logs

```python
from datetime import datetime
datetime.now().strftime("%Y-%m-%d %H:%M:%S")   # 2026-09-14 10:03:22
datetime.now().isoformat(timespec="seconds")   # 2026-09-14T10:03:22
datetime.strptime("2026-09-14", "%Y-%m-%d")    # parse
```
