"""Play with the capstone REPL by hand (not an exercise).

    python 12_capstone_repl/olm.py                         REPL on YOUR exercises.py
    python 12_capstone_repl/olm.py --solution              REPL on solutions.py
    python 12_capstone_repl/olm.py --use drill             REPL on drill.py (your blank-file drill)
    python 12_capstone_repl/olm.py run phi tell me a joke  direct mode: one command, exit code

olm's own flags go BEFORE the command:
    --solution     same as --use solutions
    --use NAME     import NAME.py from this folder and call its main(argv, stdin, out)
    --flaky N      the next N provider calls raise provider.Timeout
    --resilient    pass client=CachingClient() (retry + cache) to main

    python 12_capstone_repl/olm.py --solution --flaky 2 list               -> "Timeout: ...", exit 1
    python 12_capstone_repl/olm.py --solution --flaky 2 --resilient list   -> retries, then the list

Smoke test (pipe a scripted session in instead of typing it):
    bash:        printf 'list\\nload phi\\nrun phi hello\\nbench phi 2\\nexit\\n' | python 12_capstone_repl/olm.py
    PowerShell:  "list`nload phi`nrun phi hello`nbench phi 2`nexit" | python 12_capstone_repl/olm.py
"""

import importlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import provider  # noqa: E402  (needs the sys.path line above)

USAGE = "usage: olm.py [--solution | --use NAME] [--resilient] [--flaky N] [command ...]"


def run() -> int:
    args = sys.argv[1:]
    module, resilient = "exercises", False
    while args and args[0] in ("--solution", "--use", "--resilient", "--flaky"):
        flag = args.pop(0)
        if flag == "--solution":
            module = "solutions"
        elif flag == "--resilient":
            resilient = True
        elif not args:
            print(USAGE, file=sys.stderr)
            return 2
        elif flag == "--use":
            module = args.pop(0).removesuffix(".py")
        elif args[0].isdigit():
            provider.set_flaky(int(args.pop(0)))
        else:
            print(USAGE, file=sys.stderr)
            return 2

    # PowerShell can prepend a UTF-8 BOM to piped text, so the first command would
    # arrive as "﻿list". The utf-8-sig codec drops a leading BOM if there is one.
    try:
        sys.stdin.reconfigure(encoding="utf-8-sig")
    except (AttributeError, ValueError):
        pass

    app = importlib.import_module(module)
    try:
        if resilient:
            return app.main(args, sys.stdin, sys.stdout, app.CachingClient())
        return app.main(args, sys.stdin, sys.stdout)
    except NotImplementedError as e:
        where = traceback.extract_tb(e.__traceback__)[-1].name
        print(f"\nolm: {where}() isn't written yet. Finish it, or run with --solution.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
