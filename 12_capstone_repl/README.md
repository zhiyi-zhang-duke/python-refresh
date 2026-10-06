# 12 - Capstone: the model-runner REPL

```bash
python 12_capstone_repl/exercises.py            # grade your work
python 12_capstone_repl/olm.py                  # play with YOUR version by hand
python 12_capstone_repl/olm.py --solution       # play with the reference version
python 12_capstone_repl/olm.py --use drill      # play with drill.py (see the timed drill below)
```

You build `olm`, a terminal REPL on top of `provider.py`, a fake local model runner
(deterministic, instant, one model loaded at a time, with a flakiness switch). The
phases build on each other, so go in order. **Read the contract at the top of
`provider.py` before writing a handler**, and probe it:

```bash
cd 12_capstone_repl
python -c "import provider as p; print(p.list_models()); print(p.load('phi3:mini')); print(p.benchmark('phi3:mini', 3))"
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `parse_line` | easy | `split(maxsplit=1)`, keep the rest verbatim (not `shlex`) |
| 02 | `resolve_model` | easy | exact / unique prefix / ambiguous, raising `provider.UnknownModel` |
| 03 | `cmd_list`, `cmd_load` | easy | handler signature `(rest, out)`, talk to `CLIENT`, read return shapes |
| 04 | `dispatch`, `cmd_help`, `COMMANDS` | medium | `name -> (handler, help)` tuples, catch-all `type(e).__name__: msg` |
| 05 | `repl` | medium | prompt with `end=""`, `readline()` EOF, exit/quit, blank lines |
| 06 | `cmd_run` | medium | prompt verbatim, auto-load on `provider.NotLoaded` |
| 07 | `cmd_bench` | medium | sort by the provider's `round` field, min / avg / tok/s |
| 08 | `ProviderClient` | medium | the seam: every call through one `_call` |
| 09 | `RetryingClient` | advanced | retry only `Timeout`, backoff, injected `sleep` |
| 10 | `CachingClient` | advanced | TTL cache, injected clock, stale-on-error |
| 11 | `main` | advanced | `argv` direct mode vs REPL, exit codes, `global CLIENT` |
| 12 | `cmd_fastest` | advanced | partial failure as a result, `try/finally` session restore |

The house rules (they're why the late phases are cheap):

- Every handler is `cmd_x(rest: str, out: TextIO) -> None`, prints with `file=out`.
- Handlers talk to `CLIENT`, never `provider` directly. `CLIENT` starts as the provider
  module itself; ex08 to ex10 are drop-in wrappers with the same method names.
- Handlers **raise** (`UsageError`, provider errors). Only `dispatch` prints errors.

In the real interview you'd add retry and caching by editing the one wrapper class in
place. Here they're subclasses only so each phase can be checked on its own.

## How to use this as a timed drill

Do the guided pass first (fill in `exercises.py` in order, tests on). After that, the
drill is the point: **blank file, 60 minutes, out loud.**

1. Create `12_capstone_repl/drill.py` from nothing. Only `provider.py` is allowed open.
   Paste this footer at the bottom and the same tests will grade it
   (`python 12_capstone_repl/drill.py`). Use the exercise names if you want grading;
   anything missing just shows as an error line.

   ```python
   if __name__ == "__main__":
       import sys
       from pathlib import Path
       sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
       import harness
       sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
   ```

2. Clock it:

   | Minute | Should be true |
   |---|---|
   | 0 to 3 | Contract read, provider probed with `python -c`, assumptions said out loud |
   | 3 to 12 | Loop runs, `list` works, catch-all in `dispatch`, can't crash it from the keyboard. **Smoke test wired.** |
   | 12 to 25 | `resolve_model`, `load`, `run` (verbatim prompt + auto-load) |
   | 25 to 35 | `bench` (round order + summary), `help`. Phases 1 to 7 done by 35. |
   | 35 to 50 | Wrinkles, one at a time (below). Say which assumption broke before typing. |
   | 50 to 55 | Stop adding. Say what you'd do next and why you aren't doing it now. |

3. Wrinkles, in the order an interviewer would likely throw them:

   | Wrinkle | Assumption that breaks | Where the change goes |
   |---|---|---|
   | "The provider is flaky." (`olm.py --flaky 2`) | provider calls are reliable | the wrapper's `_call`, one place |
   | "Listing is slow, cache it 30s." | every call is cheap | the wrapper's `list_models`, one place |
   | "Which model is fastest?" | one command touches one model | new handler; degrade on failure, restore the loaded model |
   | "Make it scriptable for CI." | a human is at the keyboard | `main(argv)` + exit codes, reuses `dispatch` |
   | Your own: `unload`, aliases, `--json`, history | | |

4. Smoke test: wire it at minute ~10 and rerun it after every change instead of retyping
   setup commands.

   ```bash
   # Git Bash
   printf 'list\nload phi\nrun phi tell me  a joke\nbench phi 2\nexit\n' | python 12_capstone_repl/olm.py --use drill
   ```

   ```powershell
   # PowerShell: `n is the newline escape inside double quotes
   "list`nload phi`nrun phi tell me  a joke`nbench phi 2`nexit" | python 12_capstone_repl/olm.py --use drill
   ```

   `--use drill` runs `drill.py`'s `main(argv, stdin, out)`, so `drill.py` can keep the
   grading footer. Drop `--use drill` to drive `exercises.py`, or use `--solution`.

   Gotcha: depending on `$OutputEncoding`, PowerShell can put a UTF-8 BOM in front of piped
   text, so the first command arrives as `'﻿list'` (it did on Jarvis). `olm.py`
   strips it. In a script of your own, `line.strip().lstrip("﻿")` or use Git Bash.

5. Afterwards: write down every piece of syntax you had to stop and think about. That
   list is the real output of the drill. Re-run in a few days.

## Cheat sheet

### The skeleton (type it from memory)

```python
import sys
import provider                      # errors stay namespaced: provider.UnknownModel

CLIENT = provider

def cmd_list(rest, out): ...         # EVERY handler takes (rest, out), even if it ignores rest

COMMANDS = {                         # dict of TUPLES (handler, help). Not a set, not a list.
    "list": (cmd_list, "list models"),
}

def dispatch(line, out) -> bool:
    cmd, rest = parse_line(line)
    if not cmd:
        return True
    entry = COMMANDS.get(cmd)
    if entry is None:
        print(f"unknown command: {cmd!r} (try 'help')", file=out)
        return False
    try:
        entry[0](rest, out)          # CALL it: entry[0] is the function, (rest, out) calls it
    except Exception as e:           # the REPL's safety net, the one place errors print
        print(f"{type(e).__name__}: {e}", file=out)     # never "something went wrong"
        return False
    return True

def repl(stdin, out):
    while True:
        print("> ", end="", file=out, flush=True)
        line = stdin.readline()
        if not line:                 # EOF
            print(file=out); break
        line = line.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        dispatch(line, out)
    print("bye", file=out)

# with the real input():
#     try: line = input("> ").strip()
#     except (EOFError, KeyboardInterrupt): print(); break

def main(argv, stdin, out):
    if not argv:
        repl(stdin, out); return 0
    return 0 if dispatch(" ".join(argv), out) else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout))
```

### Parsing: REPL line vs argv

```python
cmd, rest = (line.split(maxsplit=1) + ["", ""])[:2]       # pad so a blank line still unpacks
model, prompt = rest.split(maxsplit=1)                     # ValueError if only one part
shlex.split(line)          # only when you WANT quote-aware tokens; it eats quotes and double spaces
sys.argv[1:]               # direct mode: the SHELL already split it ("a b" in quotes is one arg)
```

### Python mechanics that cost time last run

```python
global CLIENT              # needed to REBIND a module name inside a function
CLIENT = make_client()     # (mutating, e.g. HISTORY.append(x), doesn't need global)

a == b                     # compare string CONTENT. `is` is identity: never for strings/numbers
x is None                  # `is` is right only for None / True / False / sentinels

names = [m["name"] for m in models]                        # pull a field out of list[dict]
by_name = {m["name"]: m for m in models}
best = min(models, key=lambda m: m["size_gb"])
sorted(rows, key=lambda r: r["round"])                     # use the provider's field, not your loop index
[x for x in names if x.startswith(prefix)]

from provider import UnknownModel    # then `except UnknownModel:`
import provider                      # then `except provider.UnknownModel:`  <- pick one, stay consistent
```

### Auto-load, retry, cache, restore

```python
try:                                    # lean on the provider's error instead of mirroring state
    result = CLIENT.run(name, prompt)
except provider.NotLoaded:
    CLIENT.load(name)
    result = CLIENT.run(name, prompt)

for attempt in range(attempts):         # retry ONLY the transient error
    try:
        return fn(*args)
    except provider.Timeout:
        if attempt == attempts - 1:
            raise                       # bare raise: original exception + traceback
        sleep(base_delay * 2 ** attempt)

if self._cached and self.clock() - self._cached[1] < self.ttl:    # TTL cache, (value, stored_at)
    return self._cached[0]
# time.monotonic() for ages: time.time() can jump backwards

previous = CLIENT.loaded()              # don't clobber the user's session
try:
    ...                                 # load other models
finally:                                # runs on success, on error, and on return
    if previous is None:
        CLIENT.unload()
    else:
        CLIENT.load(previous)
```

Order: cache outside, retry inside. A hit makes no call at all; a miss gets the retries;
stale-on-error only kicks in after the retries are spent. Invert them and the cache sees
the very first Timeout, so it serves stale data (or fails) before retry ever gets a turn.
