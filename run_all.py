"""Progress board across every topic.

    python run_all.py              # your exercises
    python run_all.py --solutions  # verify the reference solutions all pass
    python run_all.py -v           # also print each topic's full output
    python run_all.py --json       # compact results for syncing to Funemployed HQ (sync_python_progress)
    python run_all.py --catalog    # every exercise's name and level (sync_python_catalog)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness import JSON_MARKER

ROOT = Path(__file__).resolve().parent
SUMMARY = re.compile(r"(\d+)/(\d+) passing\s+(\d+) failing\s+(\d+) not started")
BANNER = re.compile(r"# -+ (easy|medium|advanced) -+$")
# Docstring or comment that opens an exercise: """ex04.  """ex11 (part 1)  """ex03a.  # ex04: ...
EX_MARK = re.compile(r'\s*(?:"""|# )ex(\d{2})(?!\d)')
README_ROW = re.compile(r"^\|\s*(\d+)\s*\|.*?\|\s*(easy|medium|advanced)\s*\|", re.M)


def run_topic(topic: Path, target: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(topic / target)],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
        env={**os.environ, "HARNESS_JSON": "1"},
    )


def levels(topic: Path) -> dict[int, str]:
    """Exercise number -> easy/medium/advanced. The README's table is the source (it survives Jack
    rewriting exercises.py); the section banners in exercises.py fill any gaps."""
    out = {int(n): lv for n, lv in README_ROW.findall((topic / "README.md").read_text(encoding="utf-8"))}
    level = None
    for line in (topic / "exercises.py").read_text(encoding="utf-8").splitlines():
        if m := BANNER.match(line):
            level = m.group(1)
        elif (m := EX_MARK.match(line)) and level:
            out.setdefault(int(m.group(1)), level)
    return out


def commit() -> str:
    proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT)
    return proc.stdout.strip()


def collect(topics: list[Path], target: str):
    """Run every topic; yield (topic, per-exercise results) or (topic, crash message)."""
    for topic in topics:
        proc = run_topic(topic, target)
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith(JSON_MARKER)), None)
        if line is None:
            yield topic, (proc.stderr.strip().splitlines() or ["(no output)"])[-1]
        else:
            yield topic, json.loads(line[len(JSON_MARKER):])


def main_json(topics: list[Path], target: str) -> int:
    """Compact report for sync_python_progress: only exercises that aren't "not started".
    Anything in a topic listed under `ran` but missing from `results` is not started."""
    ran, rows, crashed = [], [], {}
    for topic, res in collect(topics, target):
        if isinstance(res, str):
            crashed[topic.name] = res
            continue
        ran.append(topic.name)
        rows += [[topic.name, r["ex"], r["status"], r["error"][:160]] for r in res if r["status"] != "todo"]
    head = {"repo": "python-refresh", "commit": commit(), "file": target,
            "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "ran": ran, "crashed": crashed}
    # One result per line keeps it readable and small enough to paste into a tool call.
    body = ",\n  ".join(json.dumps(r, ensure_ascii=False) for r in rows)
    print(json.dumps(head, ensure_ascii=False)[:-1] + f', "results": [\n  {body}\n]}}')
    return 0


def main_catalog(topics: list[Path]) -> int:
    """Every exercise's name and level: [[topic, ex, level, name], ...]. Seeds the HQ tab."""
    rows = []
    for topic, res in collect(topics, "exercises.py"):
        if isinstance(res, str):
            print(f"{topic.name} crashed: {res}", file=sys.stderr)
            return 1
        lv = levels(topic)
        rows += [[topic.name, r["ex"], lv.get(r["ex"], ""), r["name"]] for r in res]
    print("[\n  " + ",\n  ".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]")
    return 0


def main() -> int:
    target = "solutions.py" if "--solutions" in sys.argv else "exercises.py"
    topics = sorted(p for p in ROOT.iterdir() if p.is_dir() and (p / target).exists())
    if "--json" in sys.argv:
        return main_json(topics, target)
    if "--catalog" in sys.argv:
        return main_catalog(topics)
    verbose = "-v" in sys.argv

    print(f"\n{'topic':<26}{'pass':>6}{'fail':>6}{'todo':>6}   progress")
    print("-" * 64)
    totals = [0, 0, 0, 0]
    for topic in topics:
        proc = run_topic(topic, target)
        if verbose:
            print("\n".join(ln for ln in proc.stdout.splitlines() if not ln.startswith(JSON_MARKER)))
        m = SUMMARY.search(proc.stdout)
        if not m:
            print(f"{topic.name:<26}  crashed:")
            print("    " + (proc.stderr.strip().splitlines() or ["(no output)"])[-1])
            continue
        passed, total, failed, todo = map(int, m.groups())
        for i, n in enumerate((passed, total, failed, todo)):
            totals[i] += n
        bar = "#" * passed + "x" * failed + "." * todo
        print(f"{topic.name:<26}{passed:>6}{failed:>6}{todo:>6}   {bar}")

    print("-" * 64)
    passed, total, failed, todo = totals
    print(f"{'total':<26}{passed:>6}{failed:>6}{todo:>6}   {passed}/{total}\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
