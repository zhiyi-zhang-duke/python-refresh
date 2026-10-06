from harness import expect, expect_raises


def test_ex01(m):
    """clean_command: strip whitespace and lowercase"""
    expect(m.clean_command("  LIST  \n"), "list")
    expect(m.clean_command("Load"), "load")
    expect(m.clean_command("\t\n"), "")


def test_ex02(m):
    """initials: first letter of each word, dotted"""
    expect(m.initials("ada lovelace"), "A.L.")
    expect(m.initials("  grace   brewster  hopper "), "G.B.H.")
    expect(m.initials(""), "")


def test_ex03(m):
    """normalize_city: collapse spaces, capitalize each word"""
    expect(m.normalize_city("  new   YORK "), "New York")
    expect(m.normalize_city("durham"), "Durham")
    expect(m.normalize_city("SAN luis obispo"), "San Luis Obispo")


def test_ex04(m):
    """parse_run: command, model, and the prompt kept verbatim"""
    expect(m.parse_run("run phi3:mini tell me  a joke"), ("run", "phi3:mini", "tell me  a joke"))
    expect(m.parse_run("  run llama3 hi"), ("run", "llama3", "hi"))
    expect(m.parse_run("list"), ("list", "", ""))
    expect(m.parse_run("load phi3"), ("load", "phi3", ""))
    expect(m.parse_run(""), ("", "", ""))


def test_ex05(m):
    """tokenize: shell-style split that respects quotes"""
    expect(m.tokenize('add "New York" --unit C'), ["add", "New York", "--unit", "C"])
    expect(m.tokenize("weather   Durham"), ["weather", "Durham"])
    expect(m.tokenize(""), [])
    expect(m.tokenize('add "unclosed'), None, "unbalanced quotes should return None")


def test_ex06(m):
    """format_row: fixed-width columns with f-strings"""
    expect(m.format_row("phi3:mini", 2.26, True), "phi3:mini     2.3 GB  *")
    expect(m.format_row("llama3:70b", 39.0, False), "llama3:70b   39.0 GB   ")
    expect(len(m.format_row("x", 1, False)), 23)


def test_ex07(m):
    """is_palindrome: ignore case, spaces, and punctuation"""
    assert m.is_palindrome("A man, a plan, a canal: Panama!") is True
    assert m.is_palindrome("racecar") is True
    assert m.is_palindrome("Python") is False
    assert m.is_palindrome("") is True


def test_ex08(m):
    """run_length: aaabccdddd -> a3bc2d4"""
    expect(m.run_length("aaabccdddd"), "a3bc2d4")
    expect(m.run_length("abc"), "abc")
    expect(m.run_length(""), "")
    expect(m.run_length("zzzzzzzzzzzz"), "z12")


def test_ex09(m):
    """parse_flags: positional words joined, --flags pulled out"""
    expect(m.parse_flags(["New", "York", "--unit", "C"]), ("New York", {"unit": "C"}))
    expect(m.parse_flags(["--days", "3", "Durham"]), ("Durham", {"days": "3"}))
    expect(m.parse_flags(["Raleigh"]), ("Raleigh", {}))
    expect_raises(ValueError, m.parse_flags, ["Durham", "--unit"])


def test_ex10(m):
    """wrap: greedy word wrap without textwrap"""
    text = "the quick brown fox jumps over the lazy dog"
    expect(m.wrap(text, 10), ["the quick", "brown fox", "jumps over", "the lazy", "dog"])
    expect(m.wrap("supercalifragilistic is long", 8), ["supercalifragilistic", "is long"])
    expect(m.wrap("", 5), [])


def test_ex11(m):
    """render: fill {{ placeholders }} from a dict"""
    tpl = "Hi {{ name }}, you have {{count}} new {{  thing }}."
    expect(m.render(tpl, {"name": "Jack", "count": 3, "thing": "messages"}),
           "Hi Jack, you have 3 new messages.")
    expect(m.render("{{ a }} and {{ b }}", {"a": 1}), "1 and {{ b }}",
           "unknown placeholders are left exactly as written")


def test_ex12(m):
    """parse_log_line: regex with named groups"""
    line = "2026-09-14 10:03:22 ERROR [provider] Model not loaded: phi3"
    expect(m.parse_log_line(line), {
        "date": "2026-09-14",
        "time": "10:03:22",
        "level": "ERROR",
        "source": "provider",
        "message": "Model not loaded: phi3",
    })
    expect(m.parse_log_line("2026-09-14 10:03:23 INFO [cli] ok")["level"], "INFO")
    expect(m.parse_log_line("garbage line"), None)
    expect(m.parse_log_line("2026-09-14 10:03:22 LOUD [x] nope"), None,
           "level must be one of DEBUG, INFO, WARNING, ERROR")
