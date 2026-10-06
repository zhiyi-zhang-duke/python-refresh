"""09 - CLI and IO: reference solutions.   Check them:  python 09_cli_and_io/solutions.py"""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TextIO


# ---------------------------------------------------------------- easy ----

def read_commands(stdin: TextIO) -> list[str]:
    commands = []
    for line in stdin:              # iterating a stream yields lines, "\n" included
        line = line.strip()
        if line and not line.startswith("#"):
            commands.append(line)
    return commands


def print_kv(pairs: dict, out: TextIO) -> None:
    for key, value in pairs.items():
        print(key, value, sep=": ", file=out)


def progress(label: str, steps: int, out: TextIO) -> None:
    print(label, end="", file=out)
    for _ in range(steps):
        print(".", end="", file=out, flush=True)   # flush: show it NOW on a real terminal
    print(" done", file=out)


def echo_loop(stdin: TextIO, out: TextIO) -> int:
    echoed = 0
    while True:
        print("> ", end="", file=out, flush=True)
        line = stdin.readline()
        if not line:                # "" is EOF; a blank line is "\n", which is truthy
            break
        line = line.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        print(f"echo: {line}", file=out)
        echoed += 1
    print("bye", file=out)
    return echoed


# -------------------------------------------------------------- medium ----

USAGE = "usage: greet NAME... [--shout]"


def greet_main(argv: list[str], out: TextIO, err: TextIO) -> int:
    if "-h" in argv or "--help" in argv:
        print(USAGE, file=out)
        return 0
    shout = False
    words = []
    for arg in argv:
        if arg == "--shout":
            shout = True
        elif arg.startswith("-"):
            print(f"error: unknown option {arg}", file=err)
            print(USAGE, file=err)
            return 2
        else:
            words.append(arg)
    if not words:
        print(USAGE, file=err)
        return 2
    name = " ".join(words)
    print(f"HELLO, {name.upper()}!" if shout else f"Hello, {name}.", file=out)
    return 0


LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def append_log(path: Path, level: str, message: str, when: datetime) -> str:
    level = level.upper()
    if level not in LEVELS:
        raise ValueError(f"bad level: {level}")   # validate BEFORE opening: no partial write
    line = f"{when.strftime('%Y-%m-%d %H:%M:%S')} {level} {message}"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:  # "a" appends; "w" would truncate
        f.write(line + "\n")
    return line


def parse_weather_args(argv: list[str]) -> dict | None:
    parser = argparse.ArgumentParser(prog="weather")
    parser.add_argument("city", nargs="+")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--unit", choices=["C", "F"], default="F")
    parser.add_argument("-v", "--verbose", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit:              # argparse already printed its message to stderr
        return None
    result = vars(args)             # Namespace -> dict ("--days" becomes key "days")
    result["city"] = " ".join(result["city"])
    return result


def sync_notes(root: Path, notes: dict[str, str]) -> list[str]:
    folder = root / "notes"
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in notes.items():
        (folder / f"{name}.md").write_text(text, encoding="utf-8")
    return sorted(p.stem for p in folder.glob("*.md"))


class SettingsStore:
    def __init__(self, path: Path, defaults: dict):
        self.path = Path(path)
        self.defaults = defaults

    def load(self) -> dict:
        data = dict(self.defaults)  # a copy, so callers can't mutate our defaults
        try:
            with open(self.path, encoding="utf-8") as f:
                data.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return data

    def get(self, key: str):
        return self.load()[key]

    def set(self, key: str, value) -> None:
        data = self.load()
        data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)


# ------------------------------------------------------------ advanced ----

def summarize_runs(src: Path, dst: Path) -> int:
    by_model: dict[str, list[tuple[int, int]]] = defaultdict(list)
    count = 0
    # newline="" lets the csv module own line endings (else "\r\r\n" on Windows).
    with open(src, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_model[row["model"]].append((int(row["ms"]), int(row["tokens"])))
            count += 1

    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "runs", "avg_ms", "total_tokens"])
        writer.writeheader()
        for model in sorted(by_model):
            runs = by_model[model]
            writer.writerow({
                "model": model,
                "runs": len(runs),
                "avg_ms": f"{sum(ms for ms, _ in runs) / len(runs):.1f}",
                "total_tokens": sum(tokens for _, tokens in runs),
            })
    return count


def render_table(headers: list[str], rows: list[list], out: TextIO, align: str = "") -> None:
    align = align or "<" * len(headers)
    cells = [[str(c) for c in row] for row in rows]
    widths = [max([len(h)] + [len(row[i]) for row in cells]) for i, h in enumerate(headers)]

    def line(values: list[str]) -> str:
        # Nested format spec: alignment and width are themselves interpolated.
        return "  ".join(f"{v:{a}{w}}" for v, a, w in zip(values, align, widths)).rstrip()

    print(line(headers), file=out)
    print("  ".join("-" * w for w in widths), file=out)
    for row in cells:
        print(line(row), file=out)


class RaisingParser(argparse.ArgumentParser):
    """ArgumentParser that raises instead of printing to stderr and exiting."""

    def error(self, message):
        raise ValueError(message)


def _olm_parser() -> argparse.ArgumentParser:
    parser = RaisingParser(prog="olm")
    # dest="cmd" stores the chosen subcommand name; required=True makes it mandatory.
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("model")
    run.add_argument("prompt", nargs="+")
    bench = sub.add_parser("bench")
    bench.add_argument("model")
    bench.add_argument("--rounds", type=int, default=3)
    return parser


def parse_olm(argv: list[str]) -> dict:
    result = vars(_olm_parser().parse_args(argv))
    if "prompt" in result:
        result["prompt"] = " ".join(result["prompt"])
    return result


def _todo_parser() -> argparse.ArgumentParser:
    parser = RaisingParser(prog="todo")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("add").add_argument("text", nargs="+")
    sub.add_parser("list")
    sub.add_parser("done").add_argument("n", type=int)
    return parser


def todo_main(argv: list[str], out: TextIO, err: TextIO, path: Path) -> int:
    try:
        args = _todo_parser().parse_args(argv)
    except ValueError as e:
        print(f"usage error: {e}", file=err)
        return 2

    todos = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    if args.cmd == "list":
        if not todos:
            print("no todos", file=out)
        for i, todo in enumerate(todos, start=1):
            print(f"[{'x' if todo['done'] else ' '}] {i}. {todo['text']}", file=out)
        return 0

    if args.cmd == "add":
        text = " ".join(args.text)
        todos.append({"text": text, "done": False})
        print(f"added #{len(todos)}: {text}", file=out)
    else:  # done
        if not 1 <= args.n <= len(todos):
            print(f"error: no todo #{args.n}", file=err)
            return 1
        todo = todos[args.n - 1]
        todo["done"] = True
        print(f"done #{args.n}: {todo['text']}", file=out)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(todos, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
