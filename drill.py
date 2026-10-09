"""Recall cards: one per exercise, the 1-5 lines that are the real answer.

A rapid-fire alternative to writing whole functions. Claude runs the drill in chat:
it shows a card, you type just the key line(s), and `check` grades them for real.

    python drill.py show 01_strings.ex04       # the card as you'd see it (no answer)
    python drill.py answer 01_strings.ex04     # reference answer + why
    python drill.py check 01_strings.ex04 < my_lines.py   # run YOUR lines against the card
    python drill.py verify [topic]             # every card: answer passes, empty answer fails
    python drill.py ids [topic]                # list card ids

Card files live in cards/<topic>.json, a list of:
    id      "<topic>.exNN"
    level   easy | medium | advanced
    prompt  the task, phrased as "produce X from the given names"
    given   code shown to you AND run first (inputs, imports you're not being tested on)
    setup   hidden code run before `given` (fixtures, fakes); optional
    answer  reference lines
    check   asserts run after your lines, in the same namespace. `rerun(name=value, ...)`
            rebinds names and runs your lines again, to test a second input.
    why     one line: the idiom / trap the card is about
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CARDS = ROOT / "cards"
TIMEOUT = 5

# Runs in a child process so a bad answer (infinite loop, sys.exit) can't hurt the caller.
RUNNER = r"""
import json, sys, traceback
src = json.loads(sys.stdin.read())
ns = {"__name__": "__card__"}
def rerun(**names):
    # For checks that try the learner's lines on more than one input.
    ns.update(names)
    exec(compile(src["answer"], "<answer>", "exec"), ns)
ns["rerun"] = rerun
stage = "setup"
try:
    for stage in ("setup", "given", "answer", "check"):
        if src.get(stage):
            exec(compile(src[stage], f"<{stage}>", "exec"), ns)
except BaseException as e:
    tb = [f for f in traceback.extract_tb(e.__traceback__) if f.filename.startswith("<")]
    where = f" (line {tb[-1].lineno} of {tb[-1].filename[1:-1]})" if tb else ""
    # exec'd code has no source for traceback to show, so pull the failing line ourselves.
    lines = src.get(tb[-1].filename[1:-1], "").splitlines() if tb else []
    msg = str(e) or (lines[tb[-1].lineno - 1].strip() if tb and tb[-1].lineno <= len(lines) else "")
    print(json.dumps({"ok": False, "stage": stage, "error": f"{type(e).__name__}: {msg}{where}"}))
else:
    print(json.dumps({"ok": True}))
"""

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def load(topic: str | None = None) -> dict[str, dict]:
    cards = {}
    for f in sorted(CARDS.glob("*.json")):
        if topic and topic not in f.stem:
            continue
        for c in json.loads(f.read_text(encoding="utf-8")):
            cards[c["id"]] = c
    return cards


def card(cid: str) -> dict:
    cards = load()
    if cid not in cards:
        hits = [k for k in cards if cid in k]
        if len(hits) != 1:
            sys.exit(f"no single card matches {cid!r}" + (f": {hits[:10]}" if hits else ""))
        cid = hits[0]
    return cards[cid]


def run(c: dict, answer: str) -> dict:
    payload = {"setup": c.get("setup", ""), "given": c.get("given", ""), "answer": answer, "check": c["check"]}
    try:
        proc = subprocess.run([sys.executable, "-c", RUNNER], input=json.dumps(payload),
                              capture_output=True, text=True, encoding="utf-8", timeout=TIMEOUT, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "answer", "error": f"timed out after {TIMEOUT}s (infinite loop?)"}
    lines = proc.stdout.strip().splitlines()
    return json.loads(lines[-1]) if lines else {"ok": False, "stage": "?", "error": proc.stderr.strip()[-300:]}


def show(c: dict) -> str:
    out = [f"{c['id']}  [{c['level']}]", c["prompt"]]
    if c.get("given"):
        out += ["", c["given"]]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "ids":
        print("\n".join(load(rest[0] if rest else None)))
    elif cmd == "show":
        print(show(card(rest[0])))
    elif cmd == "answer":
        c = card(rest[0])
        print(c["answer"], "\n\n# why: " + c["why"], sep="")
    elif cmd == "check":
        c = card(rest[0])
        answer = sys.stdin.read()
        if answer.startswith("﻿"):  # PowerShell pipes prepend a BOM
            answer = answer[1:]
        res = run(c, answer)
        print("PASS" if res["ok"] else f"FAIL at {res['stage']}: {res['error']}")
        return 0 if res["ok"] else 1
    elif cmd == "verify":
        cards, bad = load(rest[0] if rest else None), 0
        for cid, c in cards.items():
            missing = [k for k in ("id", "level", "prompt", "answer", "check", "why") if not c.get(k)]
            good, empty = run(c, c.get("answer", "")), run(c, "")
            problems = ([f"missing {missing}"] if missing else []) + \
                       ([f"reference answer fails: {good['error']}"] if not good["ok"] else []) + \
                       (["check passes with NO answer (vacuous)"] if empty["ok"] else [])
            if problems:
                bad += 1
                print(f"✗ {cid}: " + "; ".join(problems))
        print(f"{len(cards) - bad}/{len(cards)} cards OK")
        return 1 if bad else 0
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
