# python-refresh

Python reps for live coding with autocomplete off. 13 topics, 175 exercises, each
folder ramping from one-liners to things that need real thought.

Built around the friction from real practice sessions: `.strip()` on input,
`except (EOFError, KeyboardInterrupt)`, `shlex.split` vs keeping the rest of a line
verbatim, `{"cmd": (handler, help)}` dispatch tables and calling `entry[0](args)`,
comprehensions over lists of dicts, `global`, `is` vs `==`, catching
`provider.UnknownCity` after `import provider`, and printing `type(e).__name__`
instead of "Something went wrong".

## How it works

Every topic folder has the same shape:

| File | What it is |
|---|---|
| `exercises.py` | Stubs. Each raises `NotImplementedError` until you fill it in. |
| `solutions.py` | Reference answers. Peek after you've tried. |
| `tests.py` | The checks. Same tests grade both files. |
| `README.md` | Exercise table + a syntax cheat sheet for the topic. |

```bash
python 01_strings/exercises.py        # run every check in the topic
python 01_strings/exercises.py 4      # just ex04
python 01_strings/exercises.py 4+     # ex04 onward
python run_all.py                     # progress board across all topics
python run_all.py --solutions         # confirm the reference answers pass
```

Output looks like:

```
  ✓  ex03  normalize_city: collapse spaces, capitalize each word
  ✗  ex04  parse_run: command, model, and the prompt kept verbatim
       expected: ('run', 'phi3:mini', 'tell me  a joke')
            got: ('run', 'phi3:mini', 'tell me a joke')
  ·  ex05  tokenize: shell-style split that respects quotes  (not started)
```

`✗` is a wrong answer, `!` is an exception in your code (with the file and line), and
`·` is a stub you haven't started. If you get stuck in an infinite loop, Ctrl-C fails
that one exercise and the run moves on.

Requires Python 3.10+. Standard library only, nothing to install.

## Topics

| Folder | # | Covers |
|---|---|---|
| `01_strings` | 12 | strip/split/join, `split(maxsplit=)`, `shlex`, f-string specs, regex named groups |
| `02_lists` | 14 | slicing, comprehensions, multi-key sorts, aliasing vs copy, `zip(*rows)`, intervals, monotonic deque, undo/redo |
| `03_dicts_sets` | 14 | `get`/`setdefault`/`defaultdict`/`Counter`, set algebra, dispatch-table REPL, deep merge, LRU via `OrderedDict`, BFS |
| `04_functions_lambdas` | 14 | sort keys, `*args`/`**kwargs`, keyword-only, closures, `partial`, `reduce`, decorators and decorator factories, `@command` registry |
| `05_classes` | 14 | `__repr__`, `@property`, `__eq__`/`__hash__`, classmethod constructors, ABCs, dataclasses, container dunders, context managers, a retry+cache client seam |
| `06_exceptions` | 14 | try/except/else/finally order, namespaced provider exceptions, custom hierarchies, `raise from`, `@contextmanager`, backoff with injected sleep |
| `07_iterators_generators` | 14 | `next(gen, None)`, `itertools` (islice, groupby, accumulate, pairwise, zip_longest), `yield from`, custom iterators, lazy pipelines, `send()` |
| `08_scope_and_gotchas` | 14 | `global`/`nonlocal`, `is` vs `==`, mutable defaults, grid aliasing, late-binding closures, `or`-default trap, `deepcopy`, negative `divmod` |
| `09_cli_and_io` | 13 | stream-injected REPL loops, argv + exit codes, argparse (subcommands too), pathlib, JSON, CSV, table rendering |
| `10_stdlib_toolkit` | 14 | `deque`, `heapq`, `bisect`, `datetime`, `lru_cache`, `Enum`, `NamedTuple`, TTL cache with injected clock, JSON custom encoding |
| `11_concurrency` | 13 | threads + `Lock` (incl. a check-then-insert booking race), `ThreadPoolExecutor`, `queue`, `Event`, asyncio gather/Semaphore/wait_for/Queue |
| `12_capstone_repl` | 12 | **Ode-style drill**: build a model-runner REPL on a fake `provider` in phases, through retry, TTL cache, and direct CLI mode |
| `13_testing` | 13 | `unittest`, `mock` (`side_effect`, `patch.object`), `subTest`, fakes vs mocks. You write checkers, and they're graded against hidden buggy mutants |

## Suggested order

1. **01 → 04** first. These are the mechanics that ate time in the drills.
2. **08** next. It's short, and every exercise is a trap that otherwise shows up as a
   confusing bug mid-interview.
3. **05, 06, 09** for the REPL/CLI building blocks.
4. **12** as a guided pass, then as a blank-file 60-minute timed drill (instructions in
   its README).
5. **07, 10, 11, 13** as time allows. 13 matters most before a TDD pairing round.

## Recall drill (the fast way)

Solving whole exercises is thorough but slow. For volume, each exercise also has a
**recall card** in `cards/<topic>.json`: the task plus given inputs, where you type only
the 1–5 key lines. The card's own check grades them for real, at about 30–60 seconds a card.

Ask Claude to "quiz me on python" (or "drill me on dicts"). It shows one card at a
time, runs your lines with `drill.py check`, and logs Knew / Shaky / Missed to
Funemployed HQ. Missed cards come back the same day, Shaky ones the next day, and
Knew ones at growing intervals, so each session starts with what you missed.

```bash
python drill.py show 01_strings.ex04      # see a card
python drill.py check 01_strings.ex04     # paste your lines, then Ctrl-Z/Ctrl-D
python drill.py answer 01_strings.ex04    # reference answer and the idiom it tests
python drill.py verify                    # every card: answer passes, empty fails
```

## Tracking progress

Progress shows on the **Python** tab of Funemployed HQ. After practicing, tell Claude
something like "I did 40 minutes of python-refresh, sync it". Claude runs

```bash
python run_all.py --json
```

and passes the result to the `funemployed-hq` MCP server (`sync_python_progress`). Status
always comes from these tests, not from memory. Moving to passing counts as a solve, so
resetting a topic to stubs (`git checkout -- 01_strings/exercises.py`) and re-solving it
counts again. If exercises are ever added, `python run_all.py --catalog` feeds
`sync_python_catalog` to create their rows.

## Tips

- Delete the `raise NotImplementedError` line when you start an exercise.
- The `Tools:` line in each docstring is the hint. The topic README's cheat sheet is the
  next level of hint. `solutions.py` is the last resort.
- Re-solve topics from scratch later: `git stash` or `git checkout -- 0X_topic/exercises.py`
  gives you clean stubs again.
- `13_testing/tests.py` describes the hidden mutants, so don't read it before you try.
