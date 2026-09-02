# Failure-class retry policy for online requests

## Target

### Files that change

| File | Change |
|---|---|
| `src/bespokelabs/curator/request_processor/online/retry_policy.py` | **NEW.** The whole policy: `FailureClass`, `classify_failure`, `RetryVerdict`, `RetryPolicy`, `remaining_cooldown_seconds`, `format_failure_summary`, `format_attempt_label`. Pure; imports nothing from `aiohttp`, `time`, or `random`. |
| `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py` | `APIRequest` gains `attempts_made`, `throttle_waivers_left`, `failure_log`. `BaseOnlineRequestProcessor.__init__` builds `self.retry_policy`. The `except Exception as e:` block (lines 526-563) is rewritten to call `decide` / `apply_to_tracker` and to read the verdict for the queue, the log and the permanent-failure response. `cool_down_if_rate_limit_error` (line 298) is rewritten on top of `remaining_cooldown_seconds`. The retry-loop `attempt_number` (line 424) is replaced by `format_attempt_label`. |
| `src/bespokelabs/curator/status_tracker/online_status_tracker.py` | One new dataclass field, `throttle_cooldown_until: float = 0.0`, placed immediately after `time_of_last_rate_limit_error` (line 67). Nothing else; `__str__` (lines 148-150) is untouched. |
| `src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py` (lines 296-303), `anthropic_online_request_processor.py` (lines 282-289), `litellm_online_request_processor.py` (lines 428-433) | The three hand-rolled rate-limit blocks stop mutating tracker counters. They keep raising; classification and counting now happen once, in the base. The compensating decrements (`num_api_errors -= 1`, `num_other_errors -= 1`, "because handle_single_request_with_retries will double count otherwise") are deleted. |

### Latent bugs in this area that the design fixes (real, with locations)

1. `litellm_online_request_processor.py:432` does `status_tracker.num_api_errors -= 1` on a rate-limit error, but nothing on the litellm path ever *increments* `num_api_errors` (it is the only mention of that attribute in the file). A single 429 leaves the tracker reporting `Errors - API: -1, Rate Limit: 1, Other: 1`.
2. `base_online_request_processor.py:527` charges `num_other_errors` for every exception kind, which is why the two other providers must pre-decrement it at `openai_online_request_processor.py:302` and `anthropic_online_request_processor.py:288`. The counters are only correct because of the compensation.
3. The attempt number is computed by the same expression at two moments and disagrees with itself: line 540 prints `max_retries - attempts_left` *after* the decrement (1 for the first failure), line 424 prints it *before* the next attempt (also 1). The retry loop therefore labels attempt #2 as "attempt #1".
4. `cool_down_if_rate_limit_error` is awaited at line 388 and line 436 for *every* request, including requests, models and runs that were never rate limited; the pause is a flat `seconds_to_pause_on_rate_limit` regardless of how many 429s have been seen.
5. `retry_queue.put_nowait(request)` at line 543 re-queues instantly, so the only thing standing between a 429 and its immediate retry is the global cooldown of (4).

### Existing machinery that may be REUSED

- `OnlineStatusTracker` and its existing counters `num_rate_limit_errors`, `num_api_errors`, `num_other_errors`, and `time_of_last_rate_limit_error` — the policy writes these, it does not replace them.
- `APIRequest` (dataclass, line 43) — extended, not replaced. `attempts_left` keeps its name and its seeding from `config.max_retries` (line 374).
- `OnlineRequestProcessorConfig.max_retries` (config.py line 28) — still the budget.
- `asyncio.Queue` retry queue, `handle_single_request_with_retries`, `append_generic_response`, `GenericResponse` — unchanged plumbing.
- `bespokelabs.curator.log.logger`.

### What must be BUILT

- `FailureClass` (enum), `classify_failure` (function), `RetryVerdict` (frozen dataclass), `RetryPolicy` (class with injected clock + jitter), `remaining_cooldown_seconds`, `format_failure_summary`, `format_attempt_label` — all in the new `retry_policy.py`.
- `OnlineStatusTracker.throttle_cooldown_until`.
- `APIRequest.attempts_made`, `APIRequest.throttle_waivers_left`, `APIRequest.failure_log`.

### Python / dependencies

Python 3.10+ (`pyproject.toml`: `python = "^3.10"`; the checkout runs 3.10.12). Standard library only for the new module (`dataclasses`, `enum`, `typing`). No new third-party dependency. `pytest` + `pytest-asyncio` already in the dev group; the policy tests need neither asyncio nor network.

---

## The API

```python
# src/bespokelabs/curator/request_processor/online/retry_policy.py
from __future__ import annotations

import dataclasses
import enum
import typing as t


class FailureClass(str, enum.Enum):
    THROTTLE = "throttle"
    TRANSIENT = "transient"
    CONTRACT = "contract"
    TERMINAL = "terminal"


_STATUS_CLASS: dict[int, FailureClass] = {
    400: FailureClass.CONTRACT,
    401: FailureClass.TERMINAL,
    403: FailureClass.TERMINAL,
    404: FailureClass.TERMINAL,
    408: FailureClass.TRANSIENT,
    409: FailureClass.TRANSIENT,
    413: FailureClass.CONTRACT,
    422: FailureClass.CONTRACT,
    425: FailureClass.TRANSIENT,
    429: FailureClass.THROTTLE,
    529: FailureClass.THROTTLE,
}

_TYPE_CLASS: dict[str, FailureClass] = {
    "TimeoutError": FailureClass.TRANSIENT,
    "ConnectionError": FailureClass.TRANSIENT,
    "ClientConnectorError": FailureClass.TRANSIENT,
    "ValueError": FailureClass.CONTRACT,
    "ValidationError": FailureClass.CONTRACT,
    "JSONDecodeError": FailureClass.CONTRACT,
    "KeyError": FailureClass.CONTRACT,
    "PermissionError": FailureClass.TERMINAL,
    "NotImplementedError": FailureClass.TERMINAL,
}

_MESSAGE_MARKERS: tuple[tuple[str, FailureClass], ...] = (
    ("rate limit", FailureClass.THROTTLE),
    ("ratelimit", FailureClass.THROTTLE),
    ("too many requests", FailureClass.THROTTLE),
    ("overloaded", FailureClass.THROTTLE),
    ("quota", FailureClass.THROTTLE),
    ("timed out", FailureClass.TRANSIENT),
    ("timeout", FailureClass.TRANSIENT),
    ("connection reset", FailureClass.TRANSIENT),
    ("temporarily unavailable", FailureClass.TRANSIENT),
    ("response is empty", FailureClass.TRANSIENT),
    ("invalid api key", FailureClass.TERMINAL),
    ("authentication", FailureClass.TERMINAL),
    ("permission denied", FailureClass.TERMINAL),
)

_DEFAULT_CLASS: FailureClass = FailureClass.TRANSIENT

# (base_seconds, factor, cap_seconds)
_SCHEDULE: dict[FailureClass, tuple[float, float, float]] = {
    FailureClass.THROTTLE: (8.0, 2.0, 60.0),
    FailureClass.TRANSIENT: (0.5, 3.0, 20.0),
    FailureClass.CONTRACT: (0.0, 1.0, 0.0),
    FailureClass.TERMINAL: (0.0, 1.0, 0.0),
}

# attempts deducted from APIRequest.attempts_left; None == not retryable
_ATTEMPT_COST: dict[FailureClass, int | None] = {
    FailureClass.THROTTLE: 1,      # 0 while a waiver remains, see RetryPolicy.decide
    FailureClass.TRANSIENT: 1,
    FailureClass.CONTRACT: 2,
    FailureClass.TERMINAL: None,
}

_TRACKER_FIELD: dict[FailureClass, str] = {
    FailureClass.THROTTLE: "num_rate_limit_errors",
    FailureClass.TRANSIENT: "num_api_errors",
    FailureClass.TERMINAL: "num_api_errors",
    FailureClass.CONTRACT: "num_other_errors",
}

DEFAULT_THROTTLE_WAIVERS: int = 6


def classify_failure(exc: BaseException) -> FailureClass: ...


@dataclasses.dataclass(frozen=True)
class RetryVerdict:
    should_retry: bool           # True -> caller re-queues the request
    failure_class: FailureClass
    attempt_index: int           # 1-based index of the attempt that just failed
    delay_seconds: float         # >= 0.0, rounded to 3 decimals; 0.0 when should_retry is False
    attempts_left_after: int     # >= 0, what APIRequest.attempts_left becomes
    throttle_waivers_after: int  # >= 0, what APIRequest.throttle_waivers_left becomes
    tracker_field: str           # exactly one of the three OnlineStatusTracker counter names
    reason_code: str             # f"{failure_class.value}:{'retry'|'exhausted'|'abort'}"


class RetryPolicy:
    def __init__(
        self,
        clock: t.Callable[[], float],
        jitter: t.Callable[[], float],
    ) -> None: ...

    def delay_for(self, failure_class: FailureClass, attempt_index: int) -> float: ...

    def decide(
        self,
        exc: BaseException,
        *,
        attempts_made: int,
        attempts_left: int,
        throttle_waivers_left: int,
    ) -> RetryVerdict: ...

    def apply_to_tracker(self, tracker: t.Any, verdict: RetryVerdict) -> None: ...


def remaining_cooldown_seconds(tracker: t.Any, now: float) -> float: ...


def format_failure_summary(
    failure_log: t.Sequence[tuple[FailureClass, str]],
) -> list[str]: ...


def format_attempt_label(attempts_made: int, max_retries: int) -> str: ...
```

```python
# base_online_request_processor.py — APIRequest additions (dataclass field order preserved,
# new fields appended after prompt_formatter/created_at)
@dataclass
class APIRequest:
    ...
    attempts_made: int = 0
    throttle_waivers_left: int = DEFAULT_THROTTLE_WAIVERS
    failure_log: list = field(default_factory=list)   # list[tuple[FailureClass, str]]
```

```python
# online_status_tracker.py — one new field
throttle_cooldown_until: float = field(default=0.0)
```

```python
# base_online_request_processor.py — the rewritten except block, in full
except Exception as e:
    verdict = self.retry_policy.decide(
        e,
        attempts_made=request.attempts_made,
        attempts_left=request.attempts_left,
        throttle_waivers_left=request.throttle_waivers_left,
    )
    self.retry_policy.apply_to_tracker(status_tracker, verdict)
    request.result.append(e)
    request.failure_log.append((verdict.failure_class, str(e)))
    request.attempts_made = verdict.attempt_index
    request.attempts_left = verdict.attempts_left_after
    request.throttle_waivers_left = verdict.throttle_waivers_after
    # ... existing cost-projection block, unchanged ...
    if verdict.should_retry:
        logger.warning(
            f"Encountered '{e.__class__.__name__}: {e}' [{verdict.reason_code}] during "
            f"{format_attempt_label(verdict.attempt_index - 1, self.config.max_retries)} "
            f"while processing request {request.task_id}; "
            f"retrying in {verdict.delay_seconds}s"
        )
        request.retry_not_before = self.retry_policy._clock() + verdict.delay_seconds
        retry_queue.put_nowait(request)
    else:
        formatted_errors = format_failure_summary(request.failure_log)
        ...  # GenericResponse(response_errors=formatted_errors, ...) as today
```

Signatures for the two rewritten call sites:

```python
async def cool_down_if_rate_limit_error(self, status_tracker: OnlineStatusTracker) -> None:
    remaining = remaining_cooldown_seconds(status_tracker, time.time())
    if remaining > 0:
        logger.warning(f"Pausing for {int(remaining)} seconds")
        await asyncio.sleep(remaining)
        status_tracker.last_update_time = time.time()

# retry loop, replacing lines 424-429
logger.debug(
    f"Retrying request {retry_request.task_id} "
    f"({format_attempt_label(retry_request.attempts_made, self.config.max_retries)})"
    f"Previous errors: {retry_request.result}"
)
```

---

## Parts

### P1 — `FailureClass` and the module boundary

**Behaviour.** A new module `request_processor/online/retry_policy.py` defines `class FailureClass(str, Enum)` with exactly four members, in this declaration order, with these lowercase values: `THROTTLE = "throttle"`, `TRANSIENT = "transient"`, `CONTRACT = "contract"`, `TERMINAL = "terminal"`; and `classify_failure(exc: BaseException) -> FailureClass`, which maps any exception instance to exactly one member and never raises. Because it subclasses `str`, `FailureClass.THROTTLE == "throttle"` is `True`.

**Alternatives a competent engineer would plausibly choose instead.**
- A boolean pair matching what the codebase already tracks: `is_rate_limit(exc) -> bool` plus the existing api/other split, i.e. three categories named after the three tracker counters (`rate_limit`, `api`, `other`) rather than four named after causes.
- A plain `Enum` (not `str`-mixin) with uppercase values `"RATE_LIMIT"`, `"SERVER_ERROR"`, `"BAD_RESPONSE"`, `"FATAL"`, living inside `base_online_request_processor.py` next to `APIRequest` rather than in its own module — the codebase does exactly this for `TokenLimitStrategy`, which sits inside `online_status_tracker.py`.

**The observable.** `[m.name for m in FailureClass] == ["THROTTLE", "TRANSIENT", "CONTRACT", "TERMINAL"]` and `[m.value for m in FailureClass] == ["throttle", "transient", "contract", "terminal"]`; `len(FailureClass) == 4`; `FailureClass.CONTRACT == "contract"` is `True`; the module is importable as `bespokelabs.curator.request_processor.online.retry_policy`.

**Arbitrary:** invented name — nothing in the repository contains the words "throttle", "transient", "contract" or "terminal"; the vocabulary the code supplies is rate-limit / api / other.

---

### P2 — Signal precedence, and the status-code table

**Behaviour.** `classify_failure` consults four signals in a fixed order and returns on the first that yields a class: (1) an HTTP status read from `getattr(exc, "status_code", None)`, falling back to `getattr(exc, "status", None)` when the first is `None`, used only if the value is an `int` and is either a key of `_STATUS_CLASS` or in the range 500-599; (2) the exception's type, per P3; (3) the message, per P4; (4) the default, per P4. A status of 500-599 that is not an explicit key maps to `TRANSIENT`; an `int` status that is neither a key nor 5xx is *not* a match and falls through to signal (2). The table is exactly `_STATUS_CLASS` as written in The API — note `529 -> THROTTLE` (Anthropic overload) and `413/422 -> CONTRACT`.

**Alternatives a competent engineer would plausibly choose instead.**
- Message first, status second — the natural reading of the code, since all three provider sites recognise a rate limit by `"rate limit" in error_message.lower()` and none of them looks at a status code. Under this alternative a `litellm.RateLimitError`-shaped object with `status_code=503` and message `"rate limit exceeded"` classifies as `THROTTLE`.
- Status first but with a coarse family rule: `4xx -> TERMINAL`, `5xx -> TRANSIENT`, `429 -> THROTTLE`, no per-code table, so `422` and `408` land on the family answer (`TERMINAL`) instead of `CONTRACT`/`TRANSIENT`.
- Treat an unrecognised `int` status as authoritative and fall back to `_DEFAULT_CLASS` immediately, rather than continuing to the type and message signals.

**The observable.** With `E = type("E", (Exception,), {})`:
- `e = E("rate limit exceeded"); e.status_code = 503` → `classify_failure(e) is FailureClass.TRANSIENT` (status wins over the message marker).
- `e = E("rate limit exceeded"); e.status = 429` → `FailureClass.THROTTLE`.
- `e = E("overloaded"); e.status_code = 529` → `FailureClass.THROTTLE`.
- `e = E("bad request"); e.status_code = 422` → `FailureClass.CONTRACT`; `e.status_code = 404` → `FailureClass.TERMINAL`; `e.status_code = 599` → `FailureClass.TRANSIENT`.
- `e = ValueError("nope"); e.status_code = 418` → `FailureClass.CONTRACT` (418 is not a match, so the type signal decides), while `e.status_code = 400` also gives `CONTRACT` — and `e = ValueError("nope"); e.status_code = 429` → `FailureClass.THROTTLE`, proving status outranks type.
- `e = E("boom"); e.status_code = "429"` (a `str`) → `FailureClass.TRANSIENT` (non-`int` ignored, message has no marker, default applies).

**Arbitrary:** chosen value + deliberate departure — the codebase's only classification evidence is message-substring matching, and this rule puts the message last; 529, 413, 425 and the "unrecognised int falls through" rule are choices no line of the repo suggests.

---

### P3 — Type-name matching walks the MRO

**Behaviour.** The type signal matches on `__name__` along `type(exc).__mro__` in MRO order, returning the class for the first name that is a key of `_TYPE_CLASS` (the table as written in The API). Matching is by name, not by `isinstance`, so `pydantic.ValidationError` and `litellm`'s exceptions match without importing them, and Python 3.10's `asyncio.TimeoutError` matches the same key as the builtin. A subclass of a keyed class inherits its class through the MRO walk; a bare `Exception` matches nothing and falls through to P4.

**Alternatives a competent engineer would plausibly choose instead.**
- `isinstance(exc, (TimeoutError, asyncio.TimeoutError))` etc. with real imports — the obvious way, but on 3.10 `asyncio.TimeoutError` is not the builtin, and `pydantic.ValidationError` would have to be imported into a module that is supposed to stay dependency-free.
- Exact-type lookup, `_TYPE_CLASS.get(type(exc).__name__)`, with no MRO walk, so a user-defined `class SchemaError(ValueError)` falls through to the message signal and lands on the default `TRANSIENT` instead of `CONTRACT`.
- No type signal at all: every non-status exception is judged by its message, which is precisely what the three provider sites do today.

**The observable.**
- `classify_failure(ValueError("finish_reason was length")) is FailureClass.CONTRACT` (this is the exception raised at `base_online_request_processor.py:519`).
- `class SchemaError(ValueError): pass` → `classify_failure(SchemaError("x")) is FailureClass.CONTRACT`.
- `classify_failure(KeyError("choices")) is FailureClass.CONTRACT`.
- `classify_failure(TimeoutError("boom")) is FailureClass.TRANSIENT` and `classify_failure(asyncio.TimeoutError()) is FailureClass.TRANSIENT`.
- `classify_failure(ValueError("rate limit exceeded")) is FailureClass.CONTRACT` — type outranks message.
- `classify_failure(Exception("rate limit exceeded")) is FailureClass.THROTTLE` — `Exception` is not a key, so the walk finds nothing and P4 decides.

**Arbitrary:** policy with no local evidence — the repo classifies nothing by type; `KeyError -> CONTRACT` and `NotImplementedError -> TERMINAL` are settled choices, and MRO-walk-by-name over `isinstance` is a decision the code cannot hint at.

---

### P4 — Marker order beats string position; the default is `TRANSIENT`

**Behaviour.** The message signal lowercases `str(exc)` once and scans `_MESSAGE_MARKERS` **in tuple order**, returning the class of the first marker that appears anywhere in the message. Where in the message a marker occurs is irrelevant; only its index in `_MESSAGE_MARKERS` matters. If no marker matches, `classify_failure` returns `_DEFAULT_CLASS`, which is `FailureClass.TRANSIENT`.

**Alternatives a competent engineer would plausibly choose instead.**
- Scan by earliest position in the message (`min` over `message.find(marker)`), which is what "the first thing the error says" means to most readers; `"authentication failed: too many requests"` then classifies as `TERMINAL`.
- Default unknown exceptions to `TERMINAL` (don't retry what you can't explain) or to `CONTRACT` — a defensible and common choice, and the one that keeps a budget from being burned on mystery failures.
- Keep only the single marker the codebase already has, `"rate limit"`, and default everything else, which reproduces today's behaviour exactly.

**The observable.**
- `classify_failure(Exception("Authentication failed: too many requests")) is FailureClass.THROTTLE` — `"too many requests"` is at tuple index 2, `"authentication"` at index 11, even though `"authentication"` starts at character 0.
- `classify_failure(Exception("Quota exceeded for project")) is FailureClass.THROTTLE`.
- `classify_failure(Exception("Response is empty")) is FailureClass.TRANSIENT`.
- `classify_failure(Exception("Invalid API key provided")) is FailureClass.TERMINAL`.
- `classify_failure(Exception("API error: internal server error")) is FailureClass.TRANSIENT` (no marker; default).
- `classify_failure(Exception("")) is FailureClass.TRANSIENT`.

**Arbitrary:** chosen value + policy with no local evidence — the marker list, its order, and the default are all invented; `"quota" -> THROTTLE` is a live disagreement (billing quota is arguably terminal) that the tuple order settles.

---

### P5 — The delay schedule: cap before jitter, half-jitter, three decimals

**Behaviour.** `delay_for(failure_class, attempt_index)` raises `ValueError` if `attempt_index < 1`. Otherwise it reads `(base, factor, cap) = _SCHEDULE[failure_class]`, computes `raw = min(cap, base * factor ** (attempt_index - 1))` — the cap is applied *before* jitter, so the returned value never exceeds `cap` — and returns `0.0` immediately if `raw <= 0`. Otherwise it returns `round(raw * (0.5 + 0.5 * j), 3)` where `j` is the injected jitter clamped to `[0.0, 1.0]` via `min(1.0, max(0.0, j))`. The schedule is `THROTTLE (8.0, 2.0, 60.0)`, `TRANSIENT (0.5, 3.0, 20.0)`, `CONTRACT (0.0, 1.0, 0.0)`, `TERMINAL (0.0, 1.0, 0.0)`.

**Alternatives a competent engineer would plausibly choose instead.**
- One schedule for all classes seeded from the config knob that already exists: `base = config.seconds_to_pause_on_rate_limit` (10.0), `factor = 2.0`, no cap or a 60s cap — the only numbers the repository actually offers.
- Full jitter (`raw * j`, AWS's "Exponential Backoff and Jitter" recommendation) or no jitter at all, and cap applied *after* jitter so the pre-jitter value may exceed the cap.
- No rounding, returning the raw float; and `factor = 2.0` for every class rather than 3.0 for `TRANSIENT`.
- Give `CONTRACT` a real delay too — a schema violation is a failure like any other, so waiting before re-asking looks prudent.

**The observable.** With a jitter source returning `0.25` (so the multiplier is `0.625`):
- `delay_for(FailureClass.THROTTLE, 1) == 5.0`, `(…, 2) == 10.0`, `(…, 3) == 20.0`, `(…, 4) == 37.5`, `(…, 9) == 37.5` (raw capped at 60.0 before jitter, never 8·2⁸·0.625).
- `delay_for(FailureClass.TRANSIENT, 1) == 0.312` (`round(0.3125, 3)` is 0.312, banker's rounding), `(…, 2) == 0.938`, `(…, 3) == 2.812`, `(…, 4) == 8.438`, `(…, 5) == 12.5`, `(…, 20) == 12.5`.
- `delay_for(FailureClass.CONTRACT, 1) == 0.0` and `delay_for(FailureClass.TERMINAL, 3) == 0.0`.
- With jitter `0.0`: `delay_for(FailureClass.THROTTLE, 1) == 4.0`. With jitter `1.0`: `== 8.0`. With jitter `2.5` (out of range, clamped): `== 8.0`. With jitter `-1.0`: `== 4.0`.
- `delay_for(FailureClass.THROTTLE, 0)` raises `ValueError`.

**Arbitrary:** chosen value — 8.0/2.0/60.0, 0.5/3.0/20.0, the half-jitter multiplier, the clamp, the 3-decimal rounding and cap-before-jitter are seven independent choices, none of which appears anywhere in the repo.

---

### P6 — The jitter source is called once per positive delay, and never otherwise

**Behaviour.** `RetryPolicy.__init__(clock, jitter)` stores both callables and calls neither. `delay_for` invokes `jitter()` exactly once when `raw > 0`, and does not invoke it at all when `raw <= 0`. `decide` calls `delay_for` only when it is returning `should_retry=True`; for an aborted or exhausted verdict it sets `delay_seconds = 0.0` without consulting the schedule. Consequently the jitter source is consumed once per retryable non-`CONTRACT` failure and zero times for `CONTRACT`, `TERMINAL`, and exhausted verdicts. Neither `time` nor `random` is imported by `retry_policy.py`.

**Alternatives a competent engineer would plausibly choose instead.**
- Draw jitter unconditionally at the top of `delay_for` (or in `decide`) and multiply, which is simpler and yields the same delays — but consumes one draw per decision regardless of outcome.
- Default the parameters (`jitter: Callable[[], float] = random.random`, `clock=time.time`) so callers can omit them, which is the ergonomic choice and how `fireworks_trainer.py:601-614` handles its own backoff.

**The observable.** Given `calls = []`, `jitter = lambda: (calls.append(1), 0.25)[1]`, and a policy built on it:
- three consecutive `decide` calls on `ValueError("bad")` with a healthy budget → `len(calls) == 0`.
- one `decide` on `Exception("rate limit")` with a healthy budget → `len(calls) == 1`.
- one `decide` on `TimeoutError("x")` with `attempts_made=0, attempts_left=0, throttle_waivers_left=0` (exhausted) → `len(calls)` unchanged.
- `RetryPolicy(clock=lambda: 0.0, jitter=jitter)` immediately after construction → `len(calls) == 0`.
- `"import random" not in source and "import time" not in source` for `retry_policy.py`.

**Arbitrary:** policy with no local evidence — "how many times is the jitter source consumed" is invisible in the code and has no natural answer; the no-defaults rule contradicts the ergonomic instinct.

---

### P7 — `RetryVerdict`: eight frozen fields, a routed tracker name, a two-part reason code

**Behaviour.** `RetryVerdict` is a frozen dataclass with exactly the eight fields listed in The API, in that order. `tracker_field` is the *name* of the single `OnlineStatusTracker` counter this failure belongs to, per `_TRACKER_FIELD`: `THROTTLE -> "num_rate_limit_errors"`, `TRANSIENT -> "num_api_errors"`, `TERMINAL -> "num_api_errors"`, `CONTRACT -> "num_other_errors"`. `reason_code` is `f"{failure_class.value}:{outcome}"` where `outcome` is `"abort"` for a `TERMINAL` verdict, `"exhausted"` when the budget could not pay the cost, and `"retry"` otherwise. Being frozen, assigning to any field raises `dataclasses.FrozenInstanceError`.

**Alternatives a competent engineer would plausibly choose instead.**
- Return a tuple `(should_retry, delay_seconds)` or just the delay, and let the caller keep doing `status_tracker.num_other_errors += 1` in place — the smallest change that adds backoff.
- A mutable dataclass, or a `dict`, so the caller can amend it; and increment the tracker inside `decide` rather than naming a field for someone else to increment.
- `reason_code` as a single flat token (`"rate_limited"`, `"gave_up"`), or as an `Enum`, rather than a `class:outcome` pair; and `CONTRACT -> "num_api_errors"` since a bad response did come from the API.

**The observable.** For `p.decide(Exception("rate limit"), attempts_made=0, attempts_left=10, throttle_waivers_left=6)`:
`[f.name for f in dataclasses.fields(RetryVerdict)] == ["should_retry", "failure_class", "attempt_index", "delay_seconds", "attempts_left_after", "throttle_waivers_after", "tracker_field", "reason_code"]`; `v.tracker_field == "num_rate_limit_errors"`; `v.reason_code == "throttle:retry"`. For `ValueError("bad")` with the same budget: `v.tracker_field == "num_other_errors"`, `v.reason_code == "contract:retry"`. For `Exception("invalid api key")`: `v.tracker_field == "num_api_errors"`, `v.reason_code == "terminal:abort"`. For `TimeoutError("x")` with `attempts_left=0`: `v.reason_code == "transient:exhausted"`. `pytest.raises(dataclasses.FrozenInstanceError)` on `v.should_retry = True`.

**Arbitrary:** invented name — `RetryVerdict`, the field spelling `attempts_left_after` / `throttle_waivers_after`, and the exact `"throttle:retry"` / `"terminal:abort"` string grammar are unguessable; routing `CONTRACT` to `num_other_errors` while `TERMINAL` joins `num_api_errors` is a settled choice.

---

### P8 — What a failure costs: waivers, a double-priced contract failure, and a clamped floor

**Behaviour.** `decide` sets `attempt_index = attempts_made + 1`, then prices the failure.
- `TERMINAL`: never retried. `should_retry=False`, `attempts_left_after=0` (the remaining budget is discarded, not preserved), `throttle_waivers_after=throttle_waivers_left`, `delay_seconds=0.0`, outcome `"abort"`.
- `THROTTLE`: if `throttle_waivers_left > 0` the cost is **0** attempts and `throttle_waivers_after = throttle_waivers_left - 1`; otherwise the cost is 1 and `throttle_waivers_after = 0`. `APIRequest.throttle_waivers_left` starts at `DEFAULT_THROTTLE_WAIVERS = 6`. Being rate limited therefore does not consume the request's retry budget for its first six occurrences.
- `TRANSIENT`: cost 1. `CONTRACT`: cost **2**.
- If `attempts_left - cost < 0`, the verdict is `should_retry=False`, `attempts_left_after=0` (clamped, never negative), `delay_seconds=0.0`, outcome `"exhausted"`. Otherwise `should_retry=True`, `attempts_left_after = attempts_left - cost`, `delay_seconds = delay_for(failure_class, attempt_index)`, outcome `"retry"`.
- A zero-cost `THROTTLE` at `attempts_left == 0` still satisfies `0 - 0 >= 0` and is therefore retried.

**Alternatives a competent engineer would plausibly choose instead.**
- Every failure costs exactly one attempt — what line 537 does today, and what `max_retries` plainly means.
- Rate limits are free without limit (no waiver counter at all), since a 429 says nothing about the request; the run is protected by the global cooldown instead.
- Exhaustion computed as `attempts_left <= 0` checked *before* the cost is applied, so a cost-2 `CONTRACT` at `attempts_left == 1` still gets one more try and `attempts_left_after` goes to `-1`.
- `TERMINAL` leaves `attempts_left` untouched (the request is dead anyway, so why zero it) — a difference visible to anything that inspects the request afterwards.

**The observable.** With a jitter source returning `0.25`:
- `p.decide(Exception("rate limit"), attempts_made=0, attempts_left=3, throttle_waivers_left=6)` → `(should_retry, attempts_left_after, throttle_waivers_after, attempt_index, delay_seconds) == (True, 3, 5, 1, 5.0)`.
- `p.decide(Exception("rate limit"), attempts_made=9, attempts_left=0, throttle_waivers_left=3)` → `should_retry is True`, `attempts_left_after == 0`, `throttle_waivers_after == 2`, `reason_code == "throttle:retry"`.
- `p.decide(Exception("rate limit"), attempts_made=9, attempts_left=0, throttle_waivers_left=0)` → `should_retry is False`, `reason_code == "throttle:exhausted"`, `attempts_left_after == 0`.
- `p.decide(ValueError("bad"), attempts_made=0, attempts_left=3, throttle_waivers_left=6)` → `attempts_left_after == 1`.
- `p.decide(ValueError("bad"), attempts_made=0, attempts_left=1, throttle_waivers_left=6)` → `should_retry is False`, `reason_code == "contract:exhausted"`, `attempts_left_after == 0` (not `-1`).
- `p.decide(Exception("invalid api key"), attempts_made=2, attempts_left=7, throttle_waivers_left=6)` → `(False, 0, 6, 3, 0.0)` and `reason_code == "terminal:abort"`.
- `DEFAULT_THROTTLE_WAIVERS == 6`, and a fresh `APIRequest(...)` has `throttle_waivers_left == 6`, `attempts_made == 0`, `failure_log == []`.

**Arbitrary:** chosen value + invented name + deliberate departure — the 0/1/2 price list, the number 6, the field name `throttle_waivers_left`, and clamping at 0 all contradict the single `attempts_left -= 1` the code performs today.

---

### P9 — One counter per failure, and a cooldown horizon that only 429s can extend

**Behaviour.** `apply_to_tracker(tracker, verdict)` increments exactly one counter — `setattr(tracker, verdict.tracker_field, getattr(tracker, verdict.tracker_field) + 1)` — and nothing else, unless the verdict's class is `THROTTLE`, in which case it additionally calls `self._clock()` exactly once to get `now` and sets `tracker.time_of_last_rate_limit_error = now` and `tracker.throttle_cooldown_until = max(tracker.throttle_cooldown_until, now + verdict.delay_seconds)` — a monotonic maximum, so a later short delay never shortens a horizon already set by an earlier long one. For non-`THROTTLE` verdicts the clock is not called and neither timestamp field is touched. `remaining_cooldown_seconds(tracker, now)` returns `max(0.0, round(tracker.throttle_cooldown_until - now, 3))`. `cool_down_if_rate_limit_error` is rewritten on top of it and no longer reads `config.seconds_to_pause_on_rate_limit` at all; that knob is retained in `config.py` for backwards compatibility and is dead. The three provider blocks stop touching tracker counters, so a 429 is counted exactly once, by the base class.

**Alternatives a competent engineer would plausibly choose instead.**
- Keep the existing shape: stamp `time_of_last_rate_limit_error` and keep computing the pause as `seconds_to_pause_on_rate_limit - (now - time_of_last_rate_limit_error)`, merely making the constant per-class. The knob stays live and the horizon is implicit.
- Overwrite rather than max: `tracker.throttle_cooldown_until = now + verdict.delay_seconds`, the plain assignment, which is what "the cooldown ends `delay` from now" reads as.
- Increment in `decide` instead of a separate `apply_to_tracker`; or increment both a class counter and a global `num_other_errors` so the old "total errors" line keeps counting every exception.
- Have `apply_to_tracker` also increment a per-class counter dict on the tracker rather than reusing the three existing fields.

**The observable.** With a fake tracker exposing the four fields at `0`/`0.0`, a clock returning a constant `1000.0`, and jitter `0.25`:
- one `THROTTLE` verdict (delay `5.0`) applied → `num_rate_limit_errors == 1`, `num_api_errors == 0`, `num_other_errors == 0`, `time_of_last_rate_limit_error == 1000.0`, `throttle_cooldown_until == 1005.0`, clock call count `1`.
- then a `CONTRACT` verdict applied → `num_other_errors == 1`, `throttle_cooldown_until` still `1005.0`, `time_of_last_rate_limit_error` still `1000.0`, clock call count still `1`.
- then a second `THROTTLE` verdict whose `delay_seconds` is `1.0` at the same clock → `throttle_cooldown_until == 1005.0` (max, not `1001.0`).
- `remaining_cooldown_seconds(tracker, 1002.0) == 3.0`; `remaining_cooldown_seconds(tracker, 1005.0) == 0.0`; `remaining_cooldown_seconds(tracker, 1099.0) == 0.0`.
- a fresh `OnlineStatusTracker()` has `throttle_cooldown_until == 0.0`, so `remaining_cooldown_seconds(tracker, 12345.0) == 0.0` — a request in a run that has never been throttled waits zero seconds even when `config.seconds_to_pause_on_rate_limit == 10`.
- After a single rate-limit failure end to end, `str(tracker)` contains `"Errors - API: 0, Rate Limit: 1, Other: 0, Total: 1"` — today the litellm path produces `"Errors - API: -1, Rate Limit: 1, Other: 1, Total: 1"` (`litellm_online_request_processor.py:432`).

**Arbitrary:** invented name + deliberate departure — `throttle_cooldown_until` is a new tracker field; monotonic-max and "the config knob is dead" both contradict `cool_down_if_rate_limit_error` as written at line 298.

---

### P10 — The permanent-failure summary, and one attempt label for both logs

**Behaviour.** `format_failure_summary(failure_log)` groups the `(FailureClass, message)` pairs by exact pair equality and returns one string per distinct pair, formatted `f"[{failure_class.value}] {message} (x{count})"` — note the space before `(x`, which today's `f"{error}(x{count})"` at line 547 does not have. The list is sorted by `count` **descending**, ties broken by the index of the pair's **first** occurrence in `failure_log`, ascending. An empty log returns `[]`. The base class passes this list as `GenericResponse.response_errors`. Separately, `format_attempt_label(attempts_made, max_retries)` returns `f"attempt #{attempts_made + 1} of {max_retries + 1}"` — the denominator is total attempts, one initial plus `max_retries` retries — and it is the single expression used both by the failure log (called with `verdict.attempt_index - 1`) and by the retry-loop debug line at line 424 (called with `retry_request.attempts_made`), which removes the current off-by-one between lines 424 and 540.

**Alternatives a competent engineer would plausibly choose instead.**
- Keep `Counter(str(err) for err in request.result)` and its insertion order, adding the class as a prefix — insertion order is already first-occurrence order in CPython 3.7+, so nobody would think to sort. Under this alternative a log of `[T:"a", C:"b", T:"a"]` yields `["[transient] a (x2)", "[contract] b (x1)"]` too, but `[C:"b", T:"a", T:"a"]` yields `["[contract] b (x1)", "[transient] a (x2)"]` instead of count-descending.
- Group by message only, ignoring the class, so the same string raised as two different classes collapses into one entry.
- Sort alphabetically by the formatted string, the other obvious deterministic order.
- Leave the denominator as `max_retries` (what lines 428 and 540 print today) or as the count of remaining attempts.

**The observable.** For
`log = [(TRANSIENT, "boom"), (THROTTLE, "rate limit"), (TRANSIENT, "boom"), (CONTRACT, "bad"), (THROTTLE, "rate limit"), (THROTTLE, "rate limit")]`:
```python
format_failure_summary(log) == [
    "[throttle] rate limit (x3)",
    "[transient] boom (x2)",
    "[contract] bad (x1)",
]
```
and for `[(CONTRACT, "b"), (TRANSIENT, "a"), (TRANSIENT, "a")]` → `["[transient] a (x2)", "[contract] b (x1)"]`; for `[(TRANSIENT, "a"), (CONTRACT, "a")]` → `["[transient] a (x1)", "[contract] a (x1)"]` (two entries, class is part of the key); `format_failure_summary([]) == []`.
`format_attempt_label(0, 10) == "attempt #1 of 11"`; `format_attempt_label(3, 3) == "attempt #4 of 4"`; `format_attempt_label(0, 0) == "attempt #1 of 1"`.

**Arbitrary:** chosen value + deliberate departure — count-descending ordering, the `[class] msg (xN)` spelling, and the `max_retries + 1` denominator all differ from what lines 547 and 428 already do.

---

## End to end

One request, `max_retries = 3`, four failures. Injected clock returns the constant `1000.0`; injected jitter yields `0.25`, `0.25`, `0.0`, `0.0` in order (only some are consumed).

```python
policy = RetryPolicy(clock=fixed_clock, jitter=jitter_seq)   # clock_calls == 0, jitter_calls == 0
req = APIRequest(task_id=7, generic_request=gr, api_specific_request={}, attempts_left=3)
# req.attempts_made == 0, req.throttle_waivers_left == 6, req.failure_log == []
tracker = FakeTracker()   # all counters 0, time_of_last_rate_limit_error 0.0, throttle_cooldown_until 0.0
```

**Failure 1** — `Exception("API error: {'message': 'Rate limit reached for gpt-4o'}")`
(no status attribute; `Exception` is not in `_TYPE_CLASS`; message contains `"rate limit"`)

```python
RetryVerdict(should_retry=True, failure_class=FailureClass.THROTTLE, attempt_index=1,
             delay_seconds=5.0, attempts_left_after=3, throttle_waivers_after=5,
             tracker_field="num_rate_limit_errors", reason_code="throttle:retry")
```
after `apply_to_tracker`: `num_rate_limit_errors == 1`, `time_of_last_rate_limit_error == 1000.0`, `throttle_cooldown_until == 1005.0`. `jitter_calls == 1`, `clock_calls == 1`.
Request state: `attempts_made=1`, `attempts_left=3`, `throttle_waivers_left=5`.

**Failure 2** — `ValueError("finish_reason was length")` (raised at line 519; MRO hits `ValueError`)

```python
RetryVerdict(should_retry=True, failure_class=FailureClass.CONTRACT, attempt_index=2,
             delay_seconds=0.0, attempts_left_after=1, throttle_waivers_after=5,
             tracker_field="num_other_errors", reason_code="contract:retry")
```
after `apply_to_tracker`: `num_other_errors == 1`, `throttle_cooldown_until` still `1005.0`. `jitter_calls == 1` (unchanged), `clock_calls == 1` (unchanged).
Request state: `attempts_made=2`, `attempts_left=1`, `throttle_waivers_left=5`.

**Failure 3** — `Exception("API error: internal server error")` (no status, no type key, no marker → default)

```python
RetryVerdict(should_retry=True, failure_class=FailureClass.TRANSIENT, attempt_index=3,
             delay_seconds=2.25, attempts_left_after=0, throttle_waivers_after=5,
             tracker_field="num_api_errors", reason_code="transient:retry")
```
(`raw = min(20.0, 0.5 * 3.0**2) = 4.5`, jitter `0.0` → `round(4.5 * 0.5, 3) == 2.25`.)
after `apply_to_tracker`: `num_api_errors == 1`. `jitter_calls == 2`, `clock_calls == 1`.
Request state: `attempts_made=3`, `attempts_left=0`, `throttle_waivers_left=5`.

**Failure 4** — `TimeoutError("Request timed out")` (MRO hits `TimeoutError`)

```python
RetryVerdict(should_retry=False, failure_class=FailureClass.TRANSIENT, attempt_index=4,
             delay_seconds=0.0, attempts_left_after=0, throttle_waivers_after=5,
             tracker_field="num_api_errors", reason_code="transient:exhausted")
```
after `apply_to_tracker`: `num_api_errors == 2`. `jitter_calls == 2` (unchanged — no delay is scheduled for a verdict that will not be retried), `clock_calls == 1`.

**Final assertions**

```python
tracker.num_rate_limit_errors == 1
tracker.num_api_errors        == 2
tracker.num_other_errors      == 1
tracker.time_of_last_rate_limit_error == 1000.0
tracker.throttle_cooldown_until       == 1005.0
remaining_cooldown_seconds(tracker, 1000.0) == 5.0
remaining_cooldown_seconds(tracker, 1004.5) == 0.5
remaining_cooldown_seconds(tracker, 1005.0) == 0.0

jitter_calls == 2
clock_calls  == 1

req.attempts_made == 4
req.attempts_left == 0
req.throttle_waivers_left == 5

format_attempt_label(req.attempts_made - 1, 3) == "attempt #4 of 4"

format_failure_summary(req.failure_log) == [
    "[throttle] API error: {'message': 'Rate limit reached for gpt-4o'} (x1)",
    "[contract] finish_reason was length (x1)",
    "[transient] API error: internal server error (x1)",
    "[transient] Request timed out (x1)",
]
```

The `GenericResponse` written to the response file carries that four-element list as `response_errors`, `response_message=None`, and `raw_response=None`; `status_tracker.num_tasks_failed` is incremented once.
