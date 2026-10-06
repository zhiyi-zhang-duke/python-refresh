from harness import expect, expect_raises


def test_ex01(m):
    """last_n: negative slicing, including the n == 0 trap"""
    expect(m.last_n([1, 2, 3, 4, 5], 2), [4, 5])
    expect(m.last_n([1, 2, 3], 10), [1, 2, 3])
    expect(m.last_n([1, 2, 3], 0), [], "items[-0:] is the whole list, not an empty one")
    expect(m.last_n([], 3), [])


def test_ex02(m):
    """loaded_names: comprehension over a list of dicts"""
    expect(m.loaded_names(m.MODELS), ["phi3:mini", "gpt-4o"])
    expect(m.loaded_names([{"name": "x"}]), [], "a missing 'loaded' key means not loaded")
    expect(m.loaded_names([]), [])


def test_ex03(m):
    """numbered_menu: enumerate starting at 1"""
    expect(m.numbered_menu(["list", "load", "quit"]), ["1) list", "2) load", "3) quit"])
    expect(m.numbered_menu([]), [])


def test_ex04(m):
    """with_tag: copy, don't alias"""
    tags = ["fast"]
    out = m.with_tag(tags, "local")
    expect(out, ["fast", "local"])
    expect(tags, ["fast"], "the caller's list was modified (did you append to it directly?)")
    same = m.with_tag(tags, "fast")
    expect(same, ["fast"])
    assert same is not tags, "result must be a new list even when nothing was added"


BOOKINGS = [
    {"guest": "bo", "date": "2026-10-03", "nights": 2},
    {"guest": "Ana", "date": "2026-10-01", "nights": 5},
    {"guest": "Cy", "date": "2026-10-03", "nights": 2},
    {"guest": "al", "date": "2026-10-03", "nights": 4},
    {"guest": "Dee", "date": "2026-10-01", "nights": 1},
]


def test_ex05(m):
    """sort_bookings: date desc, nights desc, guest asc (case-insensitive)"""
    original = list(BOOKINGS)
    out = m.sort_bookings(BOOKINGS)
    expect([b["guest"] for b in out], ["al", "bo", "Cy", "Ana", "Dee"])
    expect(BOOKINGS, original, "input list was reordered (list.sort mutates; sorted copies)")
    expect(m.sort_bookings([]), [])


def test_ex06(m):
    """transpose: zip(*rows), strict on ragged rows"""
    expect(m.transpose([["phi3", 2.2], ["llama3", 39.0]]), [["phi3", "llama3"], [2.2, 39.0]])
    expect(m.transpose([[1, 2, 3]]), [[1], [2], [3]])
    expect(m.transpose([]), [])
    expect_raises(ValueError, m.transpose, [[1, 2], [3]])


def test_ex07(m):
    """dedupe: keep first occurrence, preserve order, optional key"""
    expect(m.dedupe([3, 1, 3, 2, 1]), [3, 1, 2])
    expect(m.dedupe(["Durham", "durham", "Cary", "DURHAM"], key=str.lower), ["Durham", "Cary"])
    expect(m.dedupe([]), [])
    expect(m.dedupe([{"id": 1}, {"id": 1, "v": 2}], key=lambda d: d["id"]), [{"id": 1}],
           "use the key for comparison; dicts themselves aren't hashable")


def test_ex08(m):
    """chunk: fixed-size batches"""
    expect(m.chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])
    expect(m.chunk([1, 2, 3, 4], 2), [[1, 2], [3, 4]])
    expect(m.chunk([1, 2], 5), [[1, 2]])
    expect(m.chunk([], 3), [])
    expect_raises(ValueError, m.chunk, [1, 2], 0)


def test_ex09(m):
    """rotate: right by k, negative and oversized k"""
    expect(m.rotate([1, 2, 3, 4, 5], 2), [4, 5, 1, 2, 3])
    expect(m.rotate([1, 2, 3, 4, 5], -1), [2, 3, 4, 5, 1])
    expect(m.rotate([1, 2, 3], 7), [3, 1, 2])
    expect(m.rotate([1, 2, 3], 3), [1, 2, 3])
    expect(m.rotate([], 3), [])
    items = [1, 2, 3]
    assert m.rotate(items, 0) is not items, "return a new list, even for k == 0"


def test_ex10(m):
    """moving_average: running-sum sliding window"""
    expect(m.moving_average([100, 200, 300, 400], 2), [150.0, 250.0, 350.0])
    expect(m.moving_average([1, 2, 2], 3), [1.67])
    expect(m.moving_average([0.1, 0.2, 0.3, 0.4], 1), [0.1, 0.2, 0.3, 0.4])
    expect(m.moving_average([5], 2), [])
    expect_raises(ValueError, m.moving_average, [1, 2], 0)


def test_ex11(m):
    """flatten: any depth, tuples too, strings intact, no recursion limit"""
    expect(m.flatten([1, [2, (3, [4])], "ab", []]), [1, 2, 3, 4, "ab"])
    expect(m.flatten([]), [])
    expect(m.flatten([[[]], None, [0, False]]), [None, 0, False], "falsy values are still values")
    deep = [7]
    for _ in range(5000):
        deep = [deep, 1]
    out = m.flatten(deep)
    expect((len(out), out[0]), (5001, 7), "5000 levels deep: recursion can't do this")


def test_ex12(m):
    """merge_intervals: sort, then merge overlapping/touching"""
    data = [(13, 15), (9, 10), (10, 11), (14, 17)]
    expect(m.merge_intervals(data), [(9, 11), (13, 17)])
    expect(data, [(13, 15), (9, 10), (10, 11), (14, 17)], "input was modified")
    expect(m.merge_intervals([(1, 10), (2, 3), (4, 5)]), [(1, 10)], "contained intervals")
    expect(m.merge_intervals([(1, 2), (3, 4)]), [(1, 2), (3, 4)], "a gap means no merge")
    expect(m.merge_intervals([]), [])


def test_ex13(m):
    """window_max: monotonic deque"""
    expect(m.window_max([1, 3, -1, -3, 5, 3, 6, 7], 3), [3, 3, 5, 5, 6, 7])
    expect(m.window_max([4, 4, 4], 2), [4, 4])
    expect(m.window_max([9, 8, 7, 6], 2), [9, 8, 7])
    expect(m.window_max([2, 1], 1), [2, 1])
    expect(m.window_max([1, 2], 3), [])


def test_ex14(m):
    """apply_edits: TYPE/DELETE with undo and redo stacks"""
    expect(m.apply_edits(["TYPE hello", "TYPE  world", "DELETE 6", "UNDO"]), "hello world")
    expect(m.apply_edits(["  type abc\n", "", "delete 1", "undo", "undo", "undo"]), "",
           "lines are stripped, commands case-insensitive, extra UNDO is a no-op")
    expect(m.apply_edits(["TYPE ab", "UNDO", "REDO", "REDO"]), "ab")
    expect(m.apply_edits(["TYPE ab", "UNDO", "TYPE x", "REDO"]), "x",
           "a new edit clears the redo history")
    expect(m.apply_edits(["TYPE hi", "DELETE 99"]), "")
    expect_raises(ValueError, m.apply_edits, ["PASTE x"])
