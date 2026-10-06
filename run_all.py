"""Progress board across every topic.

    python run_all.py              # your exercises
    python run_all.py --solutions  # verify the reference solutions all pass
    python run_all.py -v           # also print each topic's full output
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY = re.compile(r"(\d+)/(\d+) passing\s+(\d+) failing\s+(\d+) not started")


def main() -> int:
    target = "solutions.py" if "--solutions" in sys.argv else "exercises.py"
    verbose = "-v" in sys.argv
    topics = sorted(p for p in ROOT.iterdir() if p.is_dir() and (p / target).exists())

    print(f"\n{'topic':<26}{'pass':>6}{'fail':>6}{'todo':>6}   progress")
    print("-" * 64)
    totals = [0, 0, 0, 0]
    for topic in topics:
        proc = subprocess.run(
            [sys.executable, str(topic / target)],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
        )
        if verbose:
            print(proc.stdout)
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
