"""06 - Exceptions: reference solutions.   Check them:  python 06_exceptions/solutions.py"""

import json
import shlex
import time
from contextlib import contextmanager, suppress

import provider


# ---------------------------------------------------------------- easy ----

def safe_int(text) -> int | None:
    try:
        return int(text)
    except (ValueError, TypeError):
        return None


def read_command(read=input) -> str | None:
    try:
        return read("> ").strip()
    except (EOFError, KeyboardInterrupt):  # KeyboardInterrupt isn't an Exception subclass
        return None


def temp_or_none(city: str, fetch=provider.get_temp) -> float | None:
    try:
        return fetch(city)
    except provider.UnknownCity:  # namespaced: we did `import provider`, not `from provider import ...`
        return None


def describe_error(e: BaseException) -> str:
    msg = str(e)
    return f"error: {type(e).__name__}: {msg}" if msg else f"error: {type(e).__name__}"


# -------------------------------------------------------------- medium ----

def port_for(config: dict, service: str, default: int = 8080) -> int:
    try:
        return int(config["services"][service]["port"])
    except (KeyError, TypeError, ValueError):
        return default


def forget(cache: dict, keys: list) -> None:
    for key in keys:
        with suppress(KeyError):  # inside the loop: one missing key doesn't stop the rest
            del cache[key]


def traced(fn, log: list[str]):
    log.append("try")
    try:
        result = fn()  # not `return fn()`: that would skip the else block
    except ValueError:
        log.append("except")
        return None
    else:
        log.append("else")
        return result
    finally:
        log.append("finally")  # runs even after the returns above


LAST_ERROR = None


def repl_step(line: str, commands: dict) -> str:
    global LAST_ERROR  # we ASSIGN it below; reading alone wouldn't need this
    LAST_ERROR = None
    try:
        parts = shlex.split(line)
        if not parts:
            return ""
        name, *args = parts
        if name == "help":
            return "\n".join(f"{n}: {commands[n][1]}" for n in sorted(commands))
        if name not in commands:
            return f"unknown command: {name}"
        entry = commands[name]          # (handler, help_text)
        return str(entry[0](args))      # call the function stored in the tuple
    except Exception as e:
        LAST_ERROR = e
        return describe_error(e)


class BookingError(Exception):
    """Base for every booking error (given). Catch this to handle all of them."""


class InvalidBooking(BookingError):
    """end <= start (given)."""


class BookingConflict(BookingError):
    def __init__(self, room: str, start: int, end: int):
        super().__init__(f"room {room} is already booked {start}-{end}")
        self.room = room
        self.start = start
        self.end = end


def book(bookings: dict[str, list[tuple[int, int]]], room: str, start: int, end: int) -> None:
    if end <= start:
        raise InvalidBooking(f"end must be after start: {start}-{end}")
    for s, e in bookings.get(room, []):
        if start < e and s < end:
            raise BookingConflict(room, s, e)
    bookings.setdefault(room, []).append((start, end))


class ConfigError(Exception):
    """Raised by load_config (given)."""


def load_config(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigError(f"invalid JSON: {e.msg}") from e  # keep the original as __cause__
    if not isinstance(data, dict):
        raise ConfigError("config must be a JSON object")
    try:
        data["model"]  # EAFP: just touch it; KeyError if missing
    except KeyError:
        raise ConfigError("missing key: model") from None  # hide the KeyError noise
    return {"timeout": 30, **data}


# ------------------------------------------------------------ advanced ----

def run_job(pool: list[str], fn, log: list[str]):
    if not pool:
        raise RuntimeError("no free workers")
    worker = pool.pop()
    try:
        return fn(worker)
    except Exception as e:
        log.append(f"{worker}: {type(e).__name__}: {e}")
        raise  # bare raise: re-raises the exception being handled, traceback intact
    finally:
        pool.append(worker)


@contextmanager
def loaded(name: str, log: list[str]):
    if not name.strip():
        raise ValueError("model name is blank")
    log.append(f"load {name}")
    try:
        yield name  # the with-body runs here; its exception is raised at this line
    except Exception as e:
        log.append(f"failed {name}: {type(e).__name__}")
        raise
    finally:
        log.append(f"unload {name}")


def retry(fn, attempts: int = 3, base_delay: float = 0.5,
          retry_on: tuple = (provider.Timeout,), sleep=time.sleep):
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    for i in range(attempts):
        try:
            return fn()
        except retry_on:  # a tuple stored in a variable works in except
            if i == attempts - 1:
                raise
            sleep(base_delay * 2 ** i)


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _valid_hour(x) -> bool:
    return isinstance(x, int) and 0 <= x <= 24


def validate_booking(data: dict) -> dict:
    problems = []
    room = data.get("room")
    if not isinstance(room, str) or not room.strip():
        problems.append("room: required")
    start, end = data.get("start"), data.get("end")
    if not _valid_hour(start):
        problems.append("start: must be an int 0-24")
    if not _valid_hour(end):
        problems.append("end: must be an int 0-24")
    if _valid_hour(start) and _valid_hour(end) and end <= start:
        problems.append("end: must be after start")
    attendees = data.get("attendees", 1)
    if not isinstance(attendees, int) or attendees < 1:
        problems.append("attendees: must be a positive int")
    if problems:
        raise ValidationError(problems)
    return {"room": room.strip(), "start": start, "end": end, "attendees": attendees}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import harness
    sys.exit(1 if harness.run(sys.modules[__name__], __file__) else 0)
