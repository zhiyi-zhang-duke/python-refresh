# 01 - Strings

```bash
python 01_strings/exercises.py
```

| # | Exercise | Level | Concept |
|---|---|---|---|
| 01 | `clean_command` | easy | `strip`, `lower` |
| 02 | `initials` | easy | `split()` with no args, `join` |
| 03 | `normalize_city` | easy | generator in `join`, `capitalize` |
| 04 | `parse_run` | easy | `split(maxsplit=)`, keep the rest verbatim |
| 05 | `tokenize` | medium | `shlex.split`, catching `ValueError` |
| 06 | `format_row` | medium | f-string format specs |
| 07 | `is_palindrome` | medium | `isalnum`, `casefold`, `[::-1]` |
| 08 | `run_length` | medium | `itertools.groupby` |
| 09 | `parse_flags` | medium | index-based `while` loop, `removeprefix` |
| 10 | `wrap` | advanced | greedy accumulation |
| 11 | `render` | advanced | `re.sub` with a function |
| 12 | `parse_log_line` | advanced | named groups, `fullmatch`, `groupdict` |

## Cheat sheet

```python
s.strip() / s.lstrip() / s.rstrip()       # whitespace incl. \n \t
s.strip("-")                              # strip specific chars (a SET of chars, not a prefix)
s.removeprefix("--") / s.removesuffix(".py")   # 3.9+: strip an exact prefix/suffix

s.split()              # ANY whitespace run, drops empties:  " a  b ".split() -> ['a', 'b']
s.split(" ")           # exactly one space:                  " a  b ".split(" ") -> ['', 'a', '', 'b', '']
s.split(" ", maxsplit=1)   # "run a b c" -> ['run', 'a b c']
s.partition(" ")       # always 3-tuple: "run a b" -> ('run', ' ', 'a b');  "list" -> ('list', '', '')
" ".join(words)        # join takes an iterable of STRINGS (str() the ints first)

s.lower() / s.upper() / s.casefold()      # casefold for comparisons
s.capitalize()   # "nEW" -> "New"
s.title()        # "o'neil" -> "O'Neil" (title-cases after the apostrophe)
s.startswith(("a", "b"))   # accepts a tuple
s.isalnum() / s.isdigit() / s.isalpha() / s.isspace()

s[::-1]          # reversed
s[2:]            # drop first two
s[-3:]           # last three

import shlex
shlex.split('add "New York" -x')   # ['add', 'New York', '-x']; ValueError on unbalanced quotes
```

### f-string formatting

```python
f"{name:<12}"     # left-align in 12
f"{n:>5}"         # right-align in 5
f"{n:^7}"         # center
f"{x:.2f}"        # 2 decimals
f"{x:>8.1f}"      # right-align 8 wide, 1 decimal
f"{n:,}"          # 1,234,567
f"{n:05d}"        # zero-pad: 00042
f"{pct:.0%}"      # 0.25 -> 25%
f"{obj!r}"        # repr() instead of str(); shows quotes on strings
f"{x=}"           # debug: prints "x=42"
```

Gotcha: `f"{2.25:.1f}"` is `"2.2"`, not `"2.3"`. 2.25 is stored as 2.2499999…, and
`round()` uses banker's rounding anyway (`round(2.5) == 2`). Use `decimal.Decimal`
when exact rounding matters.

### Regex

```python
import re
re.search(p, s)     # first match anywhere, or None
re.match(p, s)      # must match at the START
re.fullmatch(p, s)  # must match the WHOLE string
re.findall(p, s)    # list of strings (or tuples if the pattern has groups)
re.sub(p, repl, s)  # repl can be a string ("\\1") or a function taking a Match

m.group(0)          # whole match;  m.group(1) first group
m.groupdict()       # {name: value} for (?P<name>...)
PATTERN = re.compile(r"...")   # compile once at module level; always use raw strings r"..."
```
