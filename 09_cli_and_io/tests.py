import contextlib
import io
import json
import tempfile
from datetime import datetime
from pathlib import Path

from harness import expect, expect_raises


def expect_text(actual, expected, what=""):
    """Compare multi-line output line by line, so a mismatch points at the first bad line."""
    expect(actual.splitlines(keepends=True), expected.splitlines(keepends=True), what)


def _streams():
    return io.StringIO(), io.StringIO()


def test_ex01(m):
    """read_commands: strip lines, skip blanks and # comments"""
    expect(m.read_commands(io.StringIO("list\n\n  load phi3  \n# a comment\nexit")),
           ["list", "load phi3", "exit"])
    expect(m.read_commands(io.StringIO("   \n\t\n")), [])
    expect(m.read_commands(io.StringIO("  # indented comment\nrun x\n")), ["run x"])


def test_ex02(m):
    """print_kv: print(..., sep=..., file=out)"""
    out = io.StringIO()
    m.print_kv({"model": "phi3", "rounds": 3}, out)
    expect(out.getvalue(), "model: phi3\nrounds: 3\n")
    out = io.StringIO()
    m.print_kv({}, out)
    expect(out.getvalue(), "")


def test_ex03(m):
    """progress: print(..., end="") to stay on one line"""
    out = io.StringIO()
    m.progress("loading", 3, out)
    expect(out.getvalue(), "loading... done\n")
    out = io.StringIO()
    m.progress("loading", 0, out)
    expect(out.getvalue(), "loading done\n")


def test_ex04(m):
    """echo_loop: prompt, readline, exit/quit/EOF"""
    out = io.StringIO()
    n = m.echo_loop(io.StringIO("hi\n\n  there \nEXIT\nnever\n"), out)
    expect_text(out.getvalue(), "> echo: hi\n> > echo: there\n> bye\n")
    expect(n, 2, "return value: number of echoed lines")

    out = io.StringIO()
    n = m.echo_loop(io.StringIO("hi"), out)     # no trailing newline, then EOF
    expect_text(out.getvalue(), "> echo: hi\n> bye\n", "EOF (readline() == '') ends the loop")
    expect(n, 1)

    out = io.StringIO()
    expect(m.echo_loop(io.StringIO(""), out), 0)
    expect(out.getvalue(), "> bye\n")


def test_ex05(m):
    """greet_main: argv, exit codes, stdout vs stderr"""
    usage = "usage: greet NAME... [--shout]\n"

    out, err = _streams()
    expect(m.greet_main(["Ada", "Lovelace"], out, err), 0)
    expect(out.getvalue(), "Hello, Ada Lovelace.\n")
    expect(err.getvalue(), "")

    out, err = _streams()
    expect(m.greet_main(["ada", "--shout"], out, err), 0)
    expect(out.getvalue(), "HELLO, ADA!\n")

    out, err = _streams()
    expect(m.greet_main([], out, err), 2, "no name is a usage error")
    expect(out.getvalue(), "", "errors must not go to stdout")
    expect(err.getvalue(), usage)

    out, err = _streams()
    expect(m.greet_main(["Ada", "--loud"], out, err), 2)
    expect(err.getvalue(), "error: unknown option --loud\n" + usage)

    out, err = _streams()
    expect(m.greet_main(["--help"], out, err), 0, "asked-for help is success")
    expect(out.getvalue(), usage, "asked-for help goes to stdout")


def test_ex06(m):
    """append_log: open(..., "a"), strftime, mkdir parents"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "logs" / "deep" / "olm.log"
        when = datetime(2026, 9, 14, 10, 3, 22)
        expect(m.append_log(path, "error", "model not loaded", when),
               "2026-09-14 10:03:22 ERROR model not loaded")
        m.append_log(path, "INFO", "loaded phi3", datetime(2026, 9, 14, 10, 3, 25))
        expect_raises(ValueError, m.append_log, path, "LOUD", "nope", when)
        expect_text(path.read_text(encoding="utf-8"),
                    "2026-09-14 10:03:22 ERROR model not loaded\n"
               "2026-09-14 10:03:25 INFO loaded phi3\n",
               "two appended lines, nothing for the invalid level")


def test_ex07(m):
    """parse_weather_args: argparse positional, type=int, choices, store_true"""
    with contextlib.redirect_stderr(io.StringIO()) as err:
        expect(m.parse_weather_args(["New", "York", "--unit", "C", "--days", "3"]),
               {"city": "New York", "days": 3, "unit": "C", "verbose": False})
        expect(m.parse_weather_args(["--verbose", "Durham"]),
               {"city": "Durham", "days": 1, "unit": "F", "verbose": True})
        expect(m.parse_weather_args(["Durham", "-v"])["verbose"], True)
        expect(err.getvalue(), "", "valid args print nothing")
        expect(m.parse_weather_args(["Durham", "--unit", "K"]), None)
        assert "invalid choice" in err.getvalue(), "argparse writes its error to stderr"
        expect(m.parse_weather_args(["--days", "x", "Durham"]), None)
        expect(m.parse_weather_args([]), None)


def test_ex08(m):
    """sync_notes: pathlib write_text, mkdir, glob, stem"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "vault"
        (root / "notes").mkdir(parents=True)
        (root / "notes" / "old.md").write_text("x", encoding="utf-8")
        (root / "notes" / "readme.txt").write_text("x", encoding="utf-8")
        expect(m.sync_notes(root, {"b": "beta", "a": "älpha"}), ["a", "b", "old"])
        expect((root / "notes" / "a.md").read_text(encoding="utf-8"), "älpha",
               "write with encoding='utf-8'")

        fresh = Path(tmp) / "x" / "y"
        expect(m.sync_notes(fresh, {"n": "1"}), ["n"], "create missing parents too")


def test_ex09(m):
    """SettingsStore: json.load / json.dump round trip"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        defaults = {"unit": "F", "days": 1}
        s = m.SettingsStore(path, defaults)
        expect(path.exists(), False, "the constructor shouldn't touch the disk")
        expect(s.load(), {"unit": "F", "days": 1}, "missing file -> defaults")
        expect(s.get("unit"), "F")
        expect_raises(KeyError, s.get, "nope")

        s.set("unit", "C")
        expect(defaults, {"unit": "F", "days": 1}, "never mutate the defaults dict")
        again = m.SettingsStore(path, {"unit": "F", "days": 1})
        expect(again.get("unit"), "C", "a new store on the same path sees saved values")
        expect(again.get("days"), 1)
        expect(json.loads(path.read_text(encoding="utf-8")), {"unit": "C", "days": 1})

        path.write_text("{not json", encoding="utf-8")
        expect(m.SettingsStore(path, {"unit": "F"}).load(), {"unit": "F"},
               "invalid JSON falls back to defaults")


def test_ex10(m):
    """summarize_runs: csv.DictReader / DictWriter, newline=''"""
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "runs.csv", Path(tmp) / "summary.csv"
        src.write_text("model,ms,tokens\nphi3,120,40\nllama3,900,50\nphi3,130,30\n",
                       encoding="utf-8")
        expect(m.summarize_runs(src, dst), 3, "returns the number of rows read")
        expect(dst.read_text(encoding="utf-8").splitlines(), [
            "model,runs,avg_ms,total_tokens",
            "llama3,1,900.0,50",
            "phi3,2,125.0,70",
        ], "blank lines between rows? open the output with newline=''")


def test_ex11(m):
    """render_table: column widths from data, nested format specs"""
    out = io.StringIO()
    m.render_table(["model", "size", "family"],
                   [["phi3:mini", 2.3, "phi"], ["llama3:70b", 39.0, "llama"]],
                   out, align="<><")
    expect(out.getvalue().splitlines(), [
        "model       size  family",
        "----------  ----  ------",
        "phi3:mini    2.3  phi",
        "llama3:70b  39.0  llama",
    ])

    out = io.StringIO()
    m.render_table(["name", "n"], [["a", 1], ["bb", 22]], out)
    expect(out.getvalue(), "name  n\n----  --\na     1\nbb    22\n",
           "default align is all-left, and trailing spaces are stripped")

    out = io.StringIO()
    m.render_table(["name"], [], out)
    expect(out.getvalue(), "name\n----\n")


def test_ex12(m):
    """parse_olm: argparse subcommands that raise instead of exiting"""
    with contextlib.redirect_stderr(io.StringIO()) as err:
        expect(m.parse_olm(["list"]), {"cmd": "list"})
        expect(m.parse_olm(["run", "phi3", "tell", "me", "a", "joke"]),
               {"cmd": "run", "model": "phi3", "prompt": "tell me a joke"})
        expect(m.parse_olm(["bench", "phi3"]), {"cmd": "bench", "model": "phi3", "rounds": 3})
        expect(m.parse_olm(["bench", "phi3", "--rounds", "5"])["rounds"], 5)

        e = expect_raises(ValueError, m.parse_olm, ["bench", "phi3", "--rounds", "x"])
        assert "invalid int value" in str(e), f"keep argparse's message, got {e}"
        e = expect_raises(ValueError, m.parse_olm, [])
        assert "required" in str(e), f"keep argparse's message, got {e}"
        expect_raises(ValueError, m.parse_olm, ["fly"])
        expect_raises(ValueError, m.parse_olm, ["run", "phi3"])
        expect_raises(ValueError, m.parse_olm, ["list", "extra"])
        expect(err.getvalue(), "", "nothing should reach stderr")


def test_ex13(m):
    """todo_main: subcommands + JSON file + exit codes"""
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()):
        path = Path(tmp) / "data" / "todos.json"

        def run(*argv):
            out, err = _streams()
            code = m.todo_main(list(argv), out, err, path)
            return code, out.getvalue(), err.getvalue()

        expect(run("list"), (0, "no todos\n", ""))
        expect(run("add", "buy", "milk"), (0, "added #1: buy milk\n", ""))
        expect(run("add", "call mom"), (0, "added #2: call mom\n", ""))
        expect(run("done", "2"), (0, "done #2: call mom\n", ""))
        expect(run("list"), (0, "[ ] 1. buy milk\n[x] 2. call mom\n", ""))
        expect(run("done", "9"), (1, "", "error: no todo #9\n"))

        for bad in (["done", "two"], [], ["fly"]):
            code, out, err = run(*bad)
            expect((code, out), (2, ""), f"usage error for {bad}: exit 2, nothing on stdout")
            assert err, f"usage error for {bad} should print something to err"

        expect(json.loads(path.read_text(encoding="utf-8")),
               [{"text": "buy milk", "done": False}, {"text": "call mom", "done": True}])
