"""Tiny test runner shared by every topic folder.

Each topic folder has:
    exercises.py  - stubs you fill in (each raises NotImplementedError until you do)
    solutions.py  - a reference answer for every stub
    tests.py      - test_exNN(m) functions; `m` is whichever module is being checked

Run a topic:          python 01_strings/exercises.py
Run one exercise:     python 01_strings/exercises.py 4
Run from exercise N:  python 01_strings/exercises.py 4+
Check the solutions:  python 01_strings/solutions.py
"""

import importlib.util
import sys
import traceback
from pathlib import Path

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ""

# Windows consoles default to cp1252; make the arrows and box glyphs print.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def _load_tests(topic_dir: Path):
    spec = importlib.util.spec_from_file_location(f"{topic_dir.name}_tests", topic_dir / "tests.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _selected(num: int, arg: str | None) -> bool:
    if not arg:
        return True
    if arg.endswith("+"):
        return num >= int(arg[:-1])
    return num == int(arg)


def _first_line(doc: str | None) -> str:
    return (doc or "").strip().splitlines()[0] if doc else ""


def run(module, file: str) -> int:
    """Run tests.py against `module`. Returns the number of non-passing exercises."""
    topic_dir = Path(file).resolve().parent
    tests = _load_tests(topic_dir)
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    test_fns = sorted(
        (name, fn) for name, fn in vars(tests).items() if name.startswith("test_ex") and callable(fn)
    )
    print(f"\n{topic_dir.name}  ({Path(file).name})\n" + "-" * 60)

    counts = {"pass": 0, "fail": 0, "todo": 0}
    for name, fn in test_fns:
        num = int(name[len("test_ex"):].split("_")[0])
        if not _selected(num, arg):
            continue
        label = f"ex{num:02d}  {_first_line(fn.__doc__)}"
        try:
            fn(module)
        except NotImplementedError:
            counts["todo"] += 1
            print(f"{DIM}  ·  {label}  (not started){RESET}")
        except AssertionError as e:
            counts["fail"] += 1
            print(f"{RED}  ✗  {label}{RESET}")
            msg = str(e) or _assert_line(e)
            for line in msg.splitlines():
                print(f"       {line}")
        # SystemExit/KeyboardInterrupt too: a stray sys.exit() or a Ctrl-C out of an
        # infinite loop fails that one exercise instead of killing the whole run.
        except (Exception, SystemExit, KeyboardInterrupt) as e:  # noqa: BLE001
            counts["fail"] += 1
            print(f"{YELLOW}  !  {label}{RESET}")
            print(f"       {type(e).__name__}: {e}")
            print(f"       {DIM}at {_learner_frame(e)}{RESET}")
        else:
            counts["pass"] += 1
            print(f"{GREEN}  ✓  {label}{RESET}")

    total = sum(counts.values())
    print("-" * 60)
    print(f"  {counts['pass']}/{total} passing   {counts['fail']} failing   {counts['todo']} not started\n")
    return counts["fail"] + counts["todo"]


def _assert_line(e: AssertionError) -> str:
    tb = traceback.extract_tb(e.__traceback__)[-1]
    return f"assert failed: {tb.line}"


def _learner_frame(e: Exception) -> str:
    """Point at the deepest frame that isn't the harness or tests file."""
    frames = [f for f in traceback.extract_tb(e.__traceback__)
              if not f.filename.endswith(("harness.py", "tests.py"))]
    f = frames[-1] if frames else traceback.extract_tb(e.__traceback__)[-1]
    return f"{Path(f.filename).name}:{f.lineno}  {f.line}"


def expect(actual, expected, what: str = ""):
    """assert actual == expected with a readable diff-style message."""
    if actual != expected:
        prefix = f"{what}\n" if what else ""
        msg = f"{prefix}expected: {expected!r}\n     got: {actual!r}"
        if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
            msg += "\n" + _first_difference(actual, expected)
        raise AssertionError(msg)


def _first_difference(actual, expected) -> str:
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            return f"first difference at [{i}]:\n  expected: {e!r}\n       got: {a!r}"
    return f"lengths differ: expected {len(expected)} items, got {len(actual)}"


def expect_raises(exc_type, fn, *args, **kwargs):
    """Assert fn(*args, **kwargs) raises exc_type. Returns the exception."""
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        return e
    except NotImplementedError:
        raise
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"expected {exc_type.__name__}, got {type(e).__name__}: {e}") from None
    raise AssertionError(f"expected {exc_type.__name__} to be raised, nothing was raised")
