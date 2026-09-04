# Online token-capacity budget: reservation, refund and reported limits

## Target

**Files that change**

| Path | Change |
|---|---|
| `src/bespokelabs/curator/status_tracker/capacity_budget.py` | **new module** — limit constants, the `TokenLimitStrategy` enum (moved here), `CapacityExceedsLimitError`, `RateLimitReading`, `parse_limit_value()`, `read_rate_limit_headers()` |
| `src/bespokelabs/curator/status_tracker/online_status_tracker.py` | `OnlineStatusTracker`: field list (the duplicate `max_tokens_per_minute` at line 64 goes away), `__post_init__` normalisation + seeding, `update_capacity`, `has_capacity`, `_check_combined_capacity`, `_check_seperate_capacity`, `consume_capacity`, `free_capacity`, new `refund_capacity`; re-exports `TokenLimitStrategy` |
| `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py` | new `_reserve_capacity()` and `_refund_capacity()`; the two reservation loops (lines 384-391 and 432-439) call them; the release in `handle_single_request_with_retries` moves onto every terminal path; the dead `free_capacity(self, tracker, tokens)` (line 312) is deleted; new `apply_rate_limit_reading()` |
| `src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py` | `get_header_based_rate_limits()` delegates to `read_rate_limit_headers()` (drops the swapped mapping at lines 149-150 and the 4000/80000/400000 fallbacks) |
| `src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py` | `get_header_based_rate_limits()` delegates (drops the `-remaining` reads and the `self.token_limit_strategy = …` mutation at lines 314-321) |
| `src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py` | `get_header_based_rate_limits()` delegates for the header half (lines 150-159); the `RATE_LIMIT_HEADER` provider table and its `rps`/`tps` scaling stay exactly as they are |

**Latent bugs this specification fixes (real, with locations)**

1. `online_status_tracker.py:62` `max_tokens_per_minute: int | _TokenUsage = 0` is shadowed by a second declaration at `:64` `max_tokens_per_minute: int = 0`; the annotation that survives is the wrong one.
2. `base_online_request_processor.py:584` is the only release site. The `except` branch above it ends in a bare `return` at `:564`, so a failed attempt's reservation is burned permanently — with `max_retries=10` and a systematically failing model the bucket drains to zero and the run wedges.
3. `base_online_request_processor.py:312` `def free_capacity(self, tracker, tokens):` has an empty body and no caller.
4. `base_online_request_processor.py:384` (and `:432`) spin forever when `token_estimate` is larger than the whole per-minute limit: `has_capacity` can never become true, and `asyncio.sleep(0.1)` runs until the process is killed.
5. `anthropic_online_request_processor.py:149-150` puts the **output** limit header into `input_tpm` and the **input** limit header into `output_tpm`.
6. `litellm_online_request_processor.py:314-321` reads `llm_provider-{provider}-ratelimit-{input,output}-tokens-remaining` — a *remaining* counter, not a limit — and installs it as the per-minute limit.
7. `base_online_request_processor.py:78` picks `defaults["max_tokens_per_minute"][self.token_limit_strategy.value]` while the strategy is still `combined`; the anthropic subclass sets `seperate` at `anthropic_online_request_processor.py:64` afterwards, so the `"seperate"` block of `_default_rate_limits.json` is never read.
8. `online_status_tracker.py:645,654` guard on `max_… is None`, but the dataclass defaults are `0`, so those branches are dead.
9. `free_capacity` (`online_status_tracker.py:681-694`) mutates `_TokenUsage.input`/`.output` in place; `_TokenUsage.total` is computed once in `model_post_init`, so `.total` goes stale the moment capacity moves.

**Existing machinery that may be REUSED**

- `_TokenUsage` (`src/bespokelabs/curator/types/token_usage.py`) — the estimate/usage carrier. Not modified.
- `OnlineStatusTracker`'s display machinery: `start_tracker(console)`, `_refresh_console`, `update_stats`, `update_cost_projection`, `stop_tracker`. Untouched.
- `_DEFAULT_COST_MAP["online"]["default"]["ratelimit"]` (loaded from `_default_rate_limits.json`) — still the source of the default numbers, now read for the *effective* strategy.
- `BaseOnlineRequestProcessor.max_requests_per_minute` / `.max_tokens_per_minute` / `.max_concurrent_requests` properties (lines 181-217) — precedence manual → header → default, unchanged.
- `handle_single_request_with_retries` structure: the `try/except/else/finally`, `config.invalid_finish_reasons`, `update_stats`, `update_cost_projection`, `append_generic_response`.
- `bespokelabs.curator.cost.RATE_LIMIT_HEADER` and the openai provider-table branch — unchanged.
- Test seam already used by `tests/unittests/test_online_status_tracker.py`: `Console(file=StringIO(), width=200, force_terminal=True)` passed to `start_tracker`.

**Explicitly out of scope, not touched**

`cool_down_if_rate_limit_error`, `config.seconds_to_pause_on_rate_limit`, `config.max_retries`, the retry queue and its ordering, `num_rate_limit_errors`, `time_of_last_rate_limit_error`.

**What must be BUILT**

- Module `capacity_budget.py` with: `DEFAULT_MAX_REQUESTS_PER_MINUTE`, `DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED`, `DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE`, `DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE`, `CAPACITY_DEBT_FLOOR_FRACTION`, `LIMIT_ORIGIN_CONFIGURED`, `LIMIT_ORIGIN_DEFAULTED`, `LIMIT_ORIGIN_UNLIMITED`, `TokenLimitStrategy`, `CapacityExceedsLimitError`, `RateLimitReading`, `REQUEST_LIMIT_HEADERS`, `INPUT_TOKEN_LIMIT_HEADERS`, `OUTPUT_TOKEN_LIMIT_HEADERS`, `TOTAL_TOKEN_LIMIT_HEADERS`, `parse_limit_value`, `read_rate_limit_headers`.
- Tracker fields `capacity_clock`, `token_limit_origin`, `request_limit_origin`, `num_capacity_settlements`, `num_capacity_refunds`, `num_capacity_debt_clamps`; method `refund_capacity`.
- Processor methods `_reserve_capacity`, `_refund_capacity`, `apply_rate_limit_reading`.

**Python / dependencies**

Python `^3.10` (repo runs 3.10.12): `int | None`, `tuple[str, ...]`, `Callable[[], float]`, `dataclasses`, `re`, `math` — all stdlib, no `from __future__ import annotations` needed. pydantic `>=2.9.2` for `_TokenUsage`. `rich` for the console the tracker already uses. Tests: `pytest ^8.3.3` + `pytest-asyncio ^0.24.0` (`@pytest.mark.asyncio` for the one coroutine, `handle_single_request_with_retries`). No new dependency. No network, no `asyncio.sleep`, no aiohttp: the tests construct `OnlineStatusTracker` directly and drive a stub subclass of `BaseOnlineRequestProcessor` (implementing the five abstract methods `file_upload_limit_check`, `estimate_total_tokens`, `estimate_output_tokens`, `create_api_specific_request_online`, `call_single_request`) built from `OnlineRequestProcessorConfig(model="gpt-4o-mini")`; `BaseRequestProcessor.__init__` performs no I/O beyond `resource.setrlimit` and `cost_processor_factory` (a `defaultdict`, so `backend == "base"` resolves to `_LitellmCostProcessor`).

## The API

### `src/bespokelabs/curator/status_tracker/capacity_budget.py`

```python
"""Capacity budgeting for online request processors."""

import math
import re
import typing as t
from dataclasses import dataclass
from enum import Enum

from bespokelabs.curator.types.token_usage import _TokenUsage

DEFAULT_MAX_REQUESTS_PER_MINUTE: int = 200
DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED: int = 100_000
DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE: int = 100_000
DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE: int = 40_000

CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25

LIMIT_ORIGIN_CONFIGURED: str = "configured"
LIMIT_ORIGIN_DEFAULTED: str = "defaulted"
LIMIT_ORIGIN_UNLIMITED: str = "unlimited"

REQUEST_LIMIT_HEADERS: tuple[str, ...] = (
    "x-ratelimit-limit-requests",
    "anthropic-ratelimit-requests-limit",
)
INPUT_TOKEN_LIMIT_HEADERS: tuple[str, ...] = (
    "x-ratelimit-limit-input-tokens",
    "anthropic-ratelimit-input-tokens-limit",
)
OUTPUT_TOKEN_LIMIT_HEADERS: tuple[str, ...] = (
    "x-ratelimit-limit-output-tokens",
    "anthropic-ratelimit-output-tokens-limit",
)
TOTAL_TOKEN_LIMIT_HEADERS: tuple[str, ...] = (
    "x-ratelimit-limit-tokens",
    "anthropic-ratelimit-tokens-limit",
)

_LIMIT_VALUE_RE = re.compile(r"^(\d+(?:\.\d+)?)([kKmM]?)$")


class TokenLimitStrategy(str, Enum):
    """Token limit strategy enum (moved here from online_status_tracker)."""

    combined = "combined"
    seperate = "seperate"
    default = "combined"


class CapacityExceedsLimitError(ValueError):
    """A single request can never fit inside the configured per-minute budget."""

    def __init__(self, axis: str, requested: int, limit: float) -> None:
        self.axis: str = axis
        self.requested: int = requested
        self.limit: float = limit
        super().__init__(f"request needs {requested} {axis} capacity but the per-minute limit is {int(limit)}")


@dataclass(frozen=True)
class RateLimitReading:
    max_requests_per_minute: int | None
    max_tokens_per_minute: int | _TokenUsage | None
    token_limit_strategy: TokenLimitStrategy
    source_headers: tuple[str, ...]


def parse_limit_value(raw: object) -> int | None: ...


def read_rate_limit_headers(headers: t.Mapping[str, object]) -> RateLimitReading: ...
```

`RateLimitReading` fields, in declaration order:

| field | type | meaning |
|---|---|---|
| `max_requests_per_minute` | `int \| None` | positive RPM, or `None` when no usable request-limit header was present |
| `max_tokens_per_minute` | `int \| _TokenUsage \| None` | `int` under `combined`, `_TokenUsage` under `seperate`, `None` when nothing usable was present |
| `token_limit_strategy` | `TokenLimitStrategy` | `seperate` iff both an input and an output limit were read, else `combined` |
| `source_headers` | `tuple[str, ...]` | the exact header names consumed, request axis first, then `(input, output)` or `(total,)`; `()` when nothing was consumed |

### `src/bespokelabs/curator/status_tracker/online_status_tracker.py`

```python
from bespokelabs.curator.status_tracker.capacity_budget import (  # re-exported for existing importers
    CAPACITY_DEBT_FLOOR_FRACTION,
    CapacityExceedsLimitError,
    DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE,
    DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE,
    DEFAULT_MAX_REQUESTS_PER_MINUTE,
    DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED,
    LIMIT_ORIGIN_CONFIGURED,
    LIMIT_ORIGIN_DEFAULTED,
    LIMIT_ORIGIN_UNLIMITED,
    TokenLimitStrategy,
)


@dataclass
class OnlineStatusTracker:
    ...
    available_request_capacity: float | None = 1.0
    available_token_capacity: float | _TokenUsage | None = 0
    last_update_time: float = field(default_factory=time.time)
    max_requests_per_minute: int | None = 0
    max_tokens_per_minute: int | _TokenUsage | None = 0     # declared exactly once
    max_concurrent_requests: int | None = None
    ...
    capacity_clock: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)
    token_limit_origin: str = field(default=LIMIT_ORIGIN_CONFIGURED, init=False)
    request_limit_origin: str = field(default=LIMIT_ORIGIN_CONFIGURED, init=False)
    num_capacity_settlements: int = 0
    num_capacity_refunds: int = 0
    num_capacity_debt_clamps: int = 0

    def update_capacity(self) -> None: ...
    def has_capacity(self, token_estimate: _TokenUsage) -> bool: ...          # may raise CapacityExceedsLimitError
    def consume_capacity(self, token_estimate: _TokenUsage) -> None: ...
    def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage) -> None: ...
    def refund_capacity(self, blocked: _TokenUsage) -> None: ...
```

Return shapes: `update_capacity`, `consume_capacity`, `free_capacity`, `refund_capacity` all return `None` and mutate the tracker. `has_capacity` returns `bool`.

Capacity representation, by strategy:

| strategy | `max_tokens_per_minute` | `available_token_capacity` |
|---|---|---|
| `combined`, limited | `int` > 0 | `float` |
| `combined`, unlimited | `None` | `None` |
| `seperate`, limited | `_TokenUsage(input=int\|None, output=int\|None)` | `_TokenUsage(input=int\|None, output=int\|None)` |
| `seperate`, unlimited | `_TokenUsage(input=None, output=None)` | `_TokenUsage(input=None, output=None)` |

`max_requests_per_minute` is `int > 0` or `None`; `available_request_capacity` is `float` or `None` in lockstep.

### `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py`

```python
    def _reserve_capacity(self, status_tracker: OnlineStatusTracker, messages: list) -> _TokenUsage | None: ...
    def _free_capacity(self, status_tracker: OnlineStatusTracker, used_capacity: _TokenUsage, blocked_capacity: _TokenUsage) -> None: ...
    def _refund_capacity(self, status_tracker: OnlineStatusTracker, blocked_capacity: _TokenUsage) -> None: ...
    def apply_rate_limit_reading(self, reading: RateLimitReading) -> None: ...
```

and both reservation loops become

```python
                    while (token_estimate := self._reserve_capacity(status_tracker, request.generic_request.messages)) is None:
                        await asyncio.sleep(0.1)
```

## Parts

### P1 — `capacity_clock`: the injected clock, and time that never runs backwards

**Behaviour.** `OnlineStatusTracker` gains a field `capacity_clock: t.Callable[[], float]`,
declared `field(default=time.time, repr=False, compare=False)`. Every read of the wall
clock in `update_capacity` goes through `self.capacity_clock()`, and `__post_init__`
re-seeds `self.last_update_time = self.capacity_clock()` (overriding the
`default_factory=time.time` value the dataclass machinery already stored). In
`update_capacity`, `elapsed = now - self.last_update_time` is clamped with
`elapsed = max(0.0, elapsed)` before refilling, and `self.last_update_time = now` is
assigned unconditionally — including when `now` is *earlier* than the previous reading.
`start_time`, `_last_stats_update`, the display code and
`cool_down_if_rate_limit_error` keep calling `time.time()` directly; only the capacity
bucket is on the injected clock.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `time.time()` in place and let tests `monkeypatch.setattr(online_status_tracker.time, "time", fake)` — no production change at all, which is what the existing test module's `from unittest.mock import patch` import suggests is the house style.
2. Add an optional `now: float | None = None` parameter to `update_capacity()` (and pass it down from `has_capacity`), defaulting to `time.time()` — the smallest signature change that makes the function testable.
3. Inject `time.monotonic` instead, since a leaky bucket wants a monotonic source; then a backwards jump is impossible and no clamp is written.

**The observable.** With `clock` a callable object whose `now` attribute the test sets:
constructing `OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=60, max_tokens_per_minute=10_000, capacity_clock=clock)` at `clock.now = 1000.0` gives
`tracker.last_update_time == 1000.0` (not the wall clock: `abs(tracker.last_update_time - time.time()) > 1e9`).
After `tracker.consume_capacity(_TokenUsage(input=3000, output=1000))` →
`tracker.available_token_capacity == 6000.0`; set `clock.now = 1006.0`, call
`tracker.update_capacity()` → `tracker.available_token_capacity == 7000.0` and
`tracker.last_update_time == 1006.0`.
Then set `clock.now = 996.0` and call `tracker.update_capacity()` again →
`tracker.available_token_capacity == 7000.0` (unchanged) and
`tracker.last_update_time == 996.0`. The un-clamped formula the file uses today would
instead drain the bucket to `7000 - 10000 * 10 / 60 == 5333.333333333333`; alternative 3
cannot reach this state at all, since a monotonic source never goes backwards.
`OnlineStatusTracker.__dataclass_fields__["capacity_clock"].default is time.time`.

**Arbitrary:** invented name (`capacity_clock`) + policy with no local evidence (the
`__post_init__` re-seed and the `max(0.0, elapsed)` clamp; today a backwards clock drains
the bucket).

### P2 — Buckets are seeded full, and `_TokenUsage` capacity is replaced, never mutated

**Behaviour.** `__post_init__` seeds both buckets to their full per-minute limit:
`available_request_capacity = float(max_requests_per_minute)` and, for `combined`,
`available_token_capacity = float(max_tokens_per_minute)`; for `seperate`,
`available_token_capacity = _TokenUsage(input=limit.input, output=limit.output)`. Any
value the caller passed for `available_request_capacity` / `available_token_capacity` is
overwritten. Under `seperate`, every mutation of `available_token_capacity`
(`update_capacity`, `consume_capacity`, `free_capacity`, `refund_capacity`) **rebinds a
freshly constructed `_TokenUsage(input=…, output=…)`** rather than assigning to
`.input`/`.output`, so `.total` is always `input + output`. Under `seperate` the refill
increment is floored: `math.floor(limit_axis * elapsed / 60.0)`, keeping axis values `int`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the declared defaults: request capacity starts at `1.0` and token capacity at `0`,
   so the first request waits ~one refill tick. This is literally what
   `online_status_tracker.py:57-58` does today, and the field defaults exist for that reason.
2. Start both buckets empty (`0.0`) — the textbook token bucket for "never exceed N per
   minute from a cold start", and the safest reading of a rate limit.
3. Keep mutating `_TokenUsage` in place (`self.available_token_capacity.input -= …`), as
   `consume_capacity` (line 674) and `free_capacity` (line 690) do today, and never look at
   `.total`.

**The observable.** `OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=60, max_tokens_per_minute=10_000, available_request_capacity=1.0, available_token_capacity=0, capacity_clock=clock)`
→ `tracker.available_request_capacity == 60.0` and `tracker.available_token_capacity == 10000.0`
(alternative 1 gives `1.0`/`0`, alternative 2 gives `0.0`/`0.0`).
With `token_limit_strategy=TokenLimitStrategy.seperate` and
`max_tokens_per_minute=_TokenUsage(input=10_000, output=5_000)`:
`tracker.available_token_capacity == _TokenUsage(input=10000, output=5000, total=15000)`;
after `tracker.consume_capacity(_TokenUsage(input=600, output=200))` →
`tracker.available_token_capacity == _TokenUsage(input=9400, output=4800, total=14200)` —
in particular `tracker.available_token_capacity.total == 14200`, where in-place mutation
leaves `.total == 15000`.
Refill flooring: from that state, advancing the clock by `1.0` second and calling
`update_capacity()` gives `_TokenUsage(input=9566, output=4883, total=14449)`
(`floor(10000/60) == 166`, `floor(5000/60) == 83`).

**Arbitrary:** deliberate departure (the code plainly starts request capacity at `1.0` and
token capacity at `0`, and plainly mutates `_TokenUsage` in place) + chosen value (floor,
not round, on the `seperate` refill).

### P3 — `None` means unlimited, `0` means "nobody told us"; `token_limit_origin`

**Behaviour.** `__post_init__` normalises the two limits and records where each came from
in two new `init=False` string fields:

- limit is `None` → **unlimited**: the limit stays `None`, the matching available capacity
  is `None`, origin is `"unlimited"`. Under `seperate`, "unlimited" is expressed per axis as
  `_TokenUsage(input=None, output=None)`; `None` for the whole token limit is normalised to
  exactly that object.
- limit is `0` (or, under `seperate`, an axis that is `0`) → **defaulted**: it is replaced by
  `DEFAULT_MAX_REQUESTS_PER_MINUTE` (200) / `DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED`
  (100_000) / `DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE` (100_000) /
  `DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE` (40_000), axis by axis, and the origin becomes
  `"defaulted"` if **any** axis was replaced.
- limit is a positive number → origin `"configured"`.

Shape coercion, also in `__post_init__`: under `combined` a `_TokenUsage` limit collapses to
its `.total`; under `seperate` an `int` limit `N` becomes `_TokenUsage(input=N, output=N)`.
`has_capacity` / `consume_capacity` / `free_capacity` / `refund_capacity` / `update_capacity`
treat a `None` capacity as untouchable: they read it, skip it, and leave it `None`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Treat `0` as unlimited too (falsy ⇒ "no limit configured" ⇒ don't throttle) and never
   substitute a default in the tracker — the defaults already get applied by
   `BaseOnlineRequestProcessor.max_tokens_per_minute` (line 202-217), so doing it again in
   the tracker looks like duplication.
2. Treat `None` as *zero* capacity, i.e. block everything until a limit is known — the
   conservative reading, and consistent with `_TokenUsage()` (all-zero) being what
   `base_online_request_processor.py:379` passes when there is no token limit.
3. Represent unlimited as `math.inf` so the arithmetic needs no branches, and keep a single
   numeric type everywhere.

**The observable.**
`OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=0, max_tokens_per_minute=0, capacity_clock=clock)`
→ `tracker.max_requests_per_minute == 200`, `tracker.max_tokens_per_minute == 100000`,
`tracker.available_request_capacity == 200.0`, `tracker.available_token_capacity == 100000.0`,
`tracker.request_limit_origin == "defaulted"`, `tracker.token_limit_origin == "defaulted"`.
`OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=None, max_tokens_per_minute=None, capacity_clock=clock)`
→ `tracker.max_tokens_per_minute is None`, `tracker.available_token_capacity is None`,
`tracker.available_request_capacity is None`, both origins `== "unlimited"`,
`tracker.has_capacity(_TokenUsage(input=10**9, output=10**9)) is True`, and after
`consume_capacity(_TokenUsage(input=10**9, output=10**9))` both available capacities are
still `None` (alternative 2 returns `False`; alternative 3 gives `math.inf`).
Per-axis defaulting: `OnlineStatusTracker(model="gpt-4o-mini", token_limit_strategy=TokenLimitStrategy.seperate, max_tokens_per_minute=_TokenUsage(input=0, output=20_000), capacity_clock=clock)`
→ `tracker.max_tokens_per_minute == _TokenUsage(input=100000, output=20000, total=120000)` and
`tracker.token_limit_origin == "defaulted"`.
Shape coercion: `OnlineStatusTracker(model="gpt-4o-mini", token_limit_strategy=TokenLimitStrategy.seperate, max_tokens_per_minute=90_000, capacity_clock=clock).max_tokens_per_minute == _TokenUsage(input=90000, output=90000, total=180000)`.

**Arbitrary:** policy with no local evidence (which sentinel means what) + invented names
(`token_limit_origin`, `request_limit_origin` and the three exact origin strings).

### P4 — `CapacityExceedsLimitError` for a request that can never fit

**Behaviour.** `has_capacity(token_estimate)` first asks whether the estimate could *ever*
be satisfied: for each axis with a non-`None` limit, if the requested amount is strictly
greater than the per-minute limit, it raises `CapacityExceedsLimitError(axis, requested, limit)`
instead of returning `False`. The check runs **before** `update_capacity()`, so a raise
leaves `last_update_time` and both buckets untouched. Axis names and check order:
under `combined` the single axis `"total"`; under `seperate`, `"input"` first, then
`"output"`. `str(exc) == f"request needs {requested} {axis} capacity but the per-minute limit is {int(limit)}"`.
An unlimited axis (`None`) never raises.

**Alternatives a competent engineer would plausibly choose instead.**
1. Return `False` and let the existing `while not has_capacity(...): await asyncio.sleep(0.1)`
   loop keep polling — the current behaviour, and the one the loop is written for.
2. Clamp the estimate down to the limit and let the request through (the estimate is only an
   estimate; the provider will decide), which is what "best effort throttling" usually means.
3. Raise a plain `ValueError` or `RuntimeError` with a message, or log a warning and return
   `True` once, so the request is at least attempted.

**The observable.** `tracker = OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=60, max_tokens_per_minute=10_000, capacity_clock=clock)` at `clock.now = 1000.0`, then `clock.now = 1042.0`:
`pytest.raises(CapacityExceedsLimitError)` on `tracker.has_capacity(_TokenUsage(input=9000, output=2000))`;
`exc.value.axis == "total"`, `exc.value.requested == 11000`, `exc.value.limit == 10000`,
`str(exc.value) == "request needs 11000 total capacity but the per-minute limit is 10000"`,
`isinstance(exc.value, ValueError) is True`, and afterwards
`tracker.last_update_time == 1000.0` (untouched by the aborted call) and
`tracker.available_token_capacity == 10000.0`.
Axis order under `seperate` with `max_tokens_per_minute=_TokenUsage(input=1_000, output=500)`:
`tracker.has_capacity(_TokenUsage(input=1500, output=800))` raises with
`exc.value.axis == "input"`, `exc.value.requested == 1500`, `exc.value.limit == 1000`.
A merely-empty bucket does not raise: after draining, `tracker.has_capacity(_TokenUsage(input=100, output=100)) is False`.

**Arbitrary:** invented name (`CapacityExceedsLimitError` and its three attributes) — and it
fixes bug 4 above.

### P5 — Debt is allowed down to −25 % of the limit, then clamped

**Behaviour.** An underestimate lets an axis go negative, but never below
`-CAPACITY_DEBT_FLOOR_FRACTION * limit` with `CAPACITY_DEBT_FLOOR_FRACTION = 0.25`. The floor
is `-limit * 0.25` as a `float` for the `combined` axis and `math.ceil(-limit * 0.25)` (an
`int`) for each `seperate` axis. The clamp is applied at the end of `consume_capacity`,
`free_capacity` and `refund_capacity`. Whenever a call clamps at least one axis,
`num_capacity_debt_clamps` increments by exactly **one** (per call, not per axis).
Request capacity is not subject to the floor: it is only ever decremented after a successful
`has_capacity`, so it stays `>= 0.0`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Let the debt run unbounded — precisely what the current `free_capacity` docstring blesses:
   "This can be a negative number incase of under estimation".
2. Clamp at `0.0`: capacity is never negative, an underestimate is simply forgotten. The most
   common leaky-bucket implementation, and the one you write if you think of the bucket as a
   physical quantity.
3. Clamp at `-limit` (a full minute of debt) — the natural "at most one window behind" bound
   that needs no invented fraction.

**The observable.** `tracker = OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=60, max_tokens_per_minute=1_000, capacity_clock=clock)` with a frozen clock:
`tracker.consume_capacity(_TokenUsage(input=700, output=100))` → `available_token_capacity == 200.0`;
`tracker.free_capacity(used=_TokenUsage(input=1000, output=500), blocked=_TokenUsage(input=700, output=100))`
→ `tracker.available_token_capacity == -250.0` (alternative 1 gives `-700.0`, alternative 2
gives `0.0`, alternative 3 gives `-700.0`), `tracker.num_capacity_debt_clamps == 1`,
`tracker.available_request_capacity == 59.0`.
A settlement that does not reach the floor does not count:
from a fresh tracker, `consume_capacity(_TokenUsage(input=700, output=100))` then
`free_capacity(used=_TokenUsage(input=700, output=200), blocked=_TokenUsage(input=700, output=100))`
→ `available_token_capacity == 100.0`, `num_capacity_debt_clamps == 0`.
`seperate` floors are ints: with `max_tokens_per_minute=_TokenUsage(input=1_000, output=500)`,
draining and over-settling both axes yields
`tracker.available_token_capacity == _TokenUsage(input=-250, output=-125, total=-375)` and
`tracker.num_capacity_debt_clamps == 1`.

**Arbitrary:** chosen value (`0.25`, and `math.ceil` for integer axes) + invented name
(`CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_debt_clamps`, and "one increment per call").

### P6 — `refund_capacity` returns the request slot; `free_capacity` never does

**Behaviour.** Two distinct release operations on the tracker:

- `free_capacity(used, blocked)` — *settlement*. Token axes gain `blocked - used`
  (per axis under `seperate`, `blocked.total - used.total` under `combined`), each axis capped
  above at its limit and floored per P5. `available_request_capacity` is **not** changed.
  `num_capacity_settlements += 1`.
- `refund_capacity(blocked)` — *refund*. Token axes gain the whole `blocked` back
  (capped above at the limit), and `available_request_capacity` gains exactly `1.0`, capped
  above at `max_requests_per_minute`. `num_capacity_refunds += 1`.

Both are no-ops on any axis whose capacity is `None`, and both still increment their counter
in that case.

**Alternatives a competent engineer would plausibly choose instead.**
1. One method for both cases — call `free_capacity(used=_TokenUsage(input=0, output=0), blocked=blocked)`
   for a refund; a full refund is just a settlement with zero usage, so a second method is dead weight.
2. Return the request slot on **every** release, refund and settlement alike: the request has
   finished either way, so the concurrency slot should come back.
3. Never return the request slot at all (today's behaviour: nothing anywhere increments
   `available_request_capacity` except the time-based refill in `update_capacity`).

**The observable.** `tracker = OnlineStatusTracker(model="gpt-4o-mini", max_requests_per_minute=60, max_tokens_per_minute=10_000, capacity_clock=clock)`, frozen clock, after
`tracker.consume_capacity(_TokenUsage(input=600, output=200))`
(→ `59.0` / `9200.0`):
- `tracker.refund_capacity(_TokenUsage(input=600, output=200))` →
  `tracker.available_request_capacity == 60.0`, `tracker.available_token_capacity == 10000.0`,
  `tracker.num_capacity_refunds == 1`, `tracker.num_capacity_settlements == 0`.
- on a second identical tracker,
  `tracker.free_capacity(used=_TokenUsage(input=500, output=100), blocked=_TokenUsage(input=600, output=200))` →
  `tracker.available_request_capacity == 59.0` (alternative 2 gives `60.0`),
  `tracker.available_token_capacity == 9400.0`,
  `tracker.num_capacity_settlements == 1`, `tracker.num_capacity_refunds == 0`.
Capping: calling `refund_capacity` twice on the second tracker leaves
`available_request_capacity == 60.0` and `available_token_capacity == 10000.0`, never above.

**Arbitrary:** invented name (`refund_capacity`, `num_capacity_refunds`,
`num_capacity_settlements`) + policy with no local evidence (the request slot comes back on a
refund and only on a refund).

### P7 — `_reserve_capacity`: always estimate, then all-or-nothing

**Behaviour.** `BaseOnlineRequestProcessor._reserve_capacity(status_tracker, messages)`
is a plain synchronous method that:
1. calls `self.estimate_total_tokens(messages)` exactly once — **unconditionally**, including
   when `status_tracker.max_tokens_per_minute is None`;
2. calls `status_tracker.has_capacity(estimate)` (letting `CapacityExceedsLimitError` propagate
   to the caller);
3. on `True`, calls `status_tracker.consume_capacity(estimate)` and returns the very
   `_TokenUsage` object it estimated;
4. on `False`, returns `None` having consumed nothing at all — neither tokens nor the request slot.

Both reservation loops (lines 384-391 and 432-439) are rewritten to
`while (token_estimate := self._reserve_capacity(...)) is None: await asyncio.sleep(0.1)`, so
estimation and consumption can no longer drift apart, and the sleep remains the only await.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the current split: estimate once outside the loop, guarded by
   `if status_tracker.max_tokens_per_minute is not None: … else: token_estimate = _TokenUsage()`
   (lines 377-380) — i.e. skip estimation entirely when there is no token limit, which is what
   the file does today.
2. Have the helper return `bool` and leave the estimate in the caller's local variable — the
   smaller refactor, and the shape most people give a `try_acquire`.
3. Take the request slot as soon as it is available and wait only on tokens (decrement
   `available_request_capacity` first, then poll the token axis), which keeps RPM saturated.

**The observable.** With a stub whose `estimate_total_tokens` counts calls and returns
`_TokenUsage(input=700, output=100)`:
- `tracker` with `max_requests_per_minute=60, max_tokens_per_minute=1_000`, frozen clock.
  First call: `proc._reserve_capacity(tracker, [])` returns a `_TokenUsage` equal to
  `_TokenUsage(input=700, output=100, total=800)`; `tracker.available_token_capacity == 200.0`;
  `tracker.available_request_capacity == 59.0`.
  Second call: returns `None`; `tracker.available_token_capacity == 200.0` and
  `tracker.available_request_capacity == 59.0` — both unchanged (alternative 3 gives `58.0`);
  `proc.estimate_calls == 2`.
- with `max_tokens_per_minute=None`: `proc._reserve_capacity(tracker, [])` returns
  `_TokenUsage(input=700, output=100, total=800)` (alternative 1 returns
  `_TokenUsage(input=0, output=0, total=0)`), `proc.estimate_calls` increments by 1,
  `tracker.available_token_capacity is None`, `tracker.available_request_capacity == 59.0`.

**Arbitrary:** deliberate departure (lines 377-380 plainly skip estimation when there is no
token limit) + invented name (`_reserve_capacity` and its `_TokenUsage | None` return).

### P8 — A failed attempt is refunded in full, whatever the provider reported

**Behaviour.** `handle_single_request_with_retries` releases the reservation exactly once per
attempt, on every terminal path:

- the `else`/success path keeps calling `self._free_capacity(status_tracker, used_tokens, blocked_capacity)`
  with the reported usage (unchanged position, line 584);
- every path through `except Exception` calls `self._refund_capacity(status_tracker, blocked_capacity)`
  immediately before its `return` (line 564) — for both the requeued and the exhausted case —
  and does so **with the full blocked estimate, ignoring `generic_response.token_usage` even
  when the response carried one**.

`_refund_capacity(status_tracker, blocked_capacity)` delegates to
`status_tracker.refund_capacity(blocked_capacity)`. The empty
`def free_capacity(self, tracker, tokens)` at line 312 is deleted.

**Alternatives a competent engineer would plausibly choose instead.**
1. Release the failure path symmetrically with the success path: `_free_capacity(status_tracker, used_tokens, blocked_capacity)`
   where `used_tokens` is the reported usage when the response carried one and zero otherwise.
   The tokens really were spent; charging them is the accurate thing, and the `except` block
   already builds exactly that `used_tokens` value (lines 528-530) for `update_cost_projection`.
2. Release only when the request is permanently failed, not when it is requeued — the retry
   will reserve again, so releasing on the requeue path looks like double counting.
3. Leave the failure path as it is (no release at all): today's code, and the reading that a
   failed call still consumed provider-side quota.

**The observable.** Stub processor, `tracker` with `max_requests_per_minute=60`,
`max_tokens_per_minute=10_000`, frozen clock, `tracker.start_tracker(Console(file=StringIO(), width=200, force_terminal=True))`,
`blocked = proc._reserve_capacity(tracker, [])` with an estimate of
`_TokenUsage(input=700, output=300)` (→ `59.0` / `9000.0`):
- failure run — `call_single_request` returns a `GenericResponse` with
  `finish_reason="length"` (in `config.invalid_finish_reasons`) and
  `token_usage=_TokenUsage(input=700, output=300)`, `request.attempts_left = 0`. After
  `await proc.handle_single_request_with_retries(request=request, session=None, retry_queue=asyncio.Queue(), response_file="unused", status_tracker=tracker, blocked_capacity=blocked)`:
  `tracker.available_token_capacity == 10000.0`, `tracker.available_request_capacity == 60.0`,
  `tracker.num_capacity_refunds == 1`, `tracker.num_capacity_settlements == 0`.
  Alternative 1 gives `9000.0` / `59.0`; alternative 3 gives `9000.0` / `59.0` with both
  counters `0`.
- requeue run — same, but `request.attempts_left = 1`:
  `tracker.num_capacity_refunds == 1`, `tracker.available_token_capacity == 10000.0`
  (alternative 2 gives `0` and `9000.0`).
- success run — `finish_reason="stop"`, `token_usage=_TokenUsage(input=700, output=100)`:
  `tracker.available_token_capacity == 9200.0`, `tracker.available_request_capacity == 59.0`,
  `tracker.num_capacity_settlements == 1`, `tracker.num_capacity_refunds == 0`.
- `hasattr(BaseOnlineRequestProcessor, "free_capacity") is False`.

(The stub overrides `append_generic_response` to a no-op, sets `prompt_formatter` to an object
whose `response_to_response_format` returns `None`, sets `_viewer_client` to an object with an
async `log_cost_projection`, and leaves `_semaphore is None`. Nothing here asserts anything
about retry ordering or `max_retries`; `attempts_left` is only a switch to reach both `except`
exits.)

**Arbitrary:** policy with no local evidence / deliberate departure — the `except` block has
the reported usage in hand (lines 528-530) and the symmetric settlement is the obvious move;
"a failed attempt is refunded whole" is the team's call.

### P9 — Only `-limit` headers count, and Anthropic's input header means input

**Behaviour.** `read_rate_limit_headers(headers)` lower-cases the incoming keys once
(so `"X-RateLimit-Limit-Tokens"` matches) and consults **only** the four name tuples
`REQUEST_LIMIT_HEADERS`, `INPUT_TOKEN_LIMIT_HEADERS`, `OUTPUT_TOKEN_LIMIT_HEADERS`,
`TOTAL_TOKEN_LIMIT_HEADERS`, in tuple order, first present-and-parseable name winning. No
`*-remaining`, `*-reset` or `llm_provider-*` key is ever read.
`anthropic-ratelimit-input-tokens-limit` feeds the **input** axis and
`anthropic-ratelimit-output-tokens-limit` the **output** axis. An axis with no usable header is
`None`; there are no hardcoded fallbacks (no `4000`, no `80000`, no `400000`) anywhere in the
reading — substituting defaults is the tracker's job (P3).
`source_headers` lists the names actually consumed, request axis first.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep `litellm_online_request_processor.py:314-321`'s reading of
   `llm_provider-{provider}-ratelimit-{input,output}-tokens-remaining`: it is the only key
   Anthropic-via-LiteLLM actually returns for the per-axis budget, so dropping it means the
   LiteLLM backend silently loses its per-axis limits.
2. Keep the documented fallbacks (`rpm=4000`, `input=80000`, `output=400000` from
   `anthropic_online_request_processor.py:147-150`) when a header is missing, since the
   docstring cites Anthropic's published tier-4 numbers.
3. Preserve the existing (swapped) anthropic assignment — it is what the code does and, read
   quickly, `input_tpm = headers.get("…output-tokens-limit")` looks deliberate.

**The observable.**
`read_rate_limit_headers({"anthropic-ratelimit-requests-limit": "4000", "anthropic-ratelimit-input-tokens-limit": "400000", "anthropic-ratelimit-output-tokens-limit": "80000"})`
→ `reading.max_requests_per_minute == 4000`,
`reading.max_tokens_per_minute == _TokenUsage(input=400000, output=80000, total=480000)`
(today's swap gives `input=80000, output=400000`),
`reading.source_headers == ("anthropic-ratelimit-requests-limit", "anthropic-ratelimit-input-tokens-limit", "anthropic-ratelimit-output-tokens-limit")`.
`read_rate_limit_headers({"llm_provider-anthropic-ratelimit-input-tokens-remaining": "12345", "llm_provider-anthropic-ratelimit-output-tokens-remaining": "678", "x-ratelimit-remaining-requests": "9"})`
→ `RateLimitReading(max_requests_per_minute=None, max_tokens_per_minute=None, token_limit_strategy=TokenLimitStrategy.combined, source_headers=())`
(alternative 1 gives `_TokenUsage(input=12345, output=678)`).
`read_rate_limit_headers({})` → the same all-`None` reading (alternative 2 gives
`4000` / `_TokenUsage(input=80000, output=400000)`).
Case-insensitivity: `read_rate_limit_headers({"X-RateLimit-Limit-Tokens": "60000"}).max_tokens_per_minute == 60000`
and `.source_headers == ("x-ratelimit-limit-tokens",)`.

**Arbitrary:** deliberate departure — three files plainly do otherwise (the swap, the
`-remaining` reads, the hardcoded fallbacks) + invented name (`read_rate_limit_headers`,
`RateLimitReading` and its four fields, the four header-name tuples).

### P10 — `parse_limit_value`: `k`/`m` suffixes, floor, and everything else is absent

**Behaviour.** `parse_limit_value(raw)` is the single value decoder:
- `bool` is rejected (`None`), even though it is an `int` subclass;
- `int` → itself if `> 0`, else `None`;
- `str` → stripped, then matched against `^(\d+(?:\.\d+)?)([kKmM]?)$`; the numeric part is
  multiplied by `1` / `1_000` / `1_000_000` for suffix `""` / `k`,`K` / `m`,`M`, then
  `math.floor`ed to an `int`; the result is returned if `> 0`, else `None`;
- anything else (`float`, `None`, `bytes`, a non-matching string such as `"1,000"`, `"1e3"`,
  `"-5"`, `"unknown"`, `""`) → `None`.
Nothing raises: a malformed header is absent, never fatal.

**Alternatives a competent engineer would plausibly choose instead.**
1. `int(headers.get(key, 0))` / `float(...)`, exactly as `openai_online_request_processor.py:150-159`
   and `litellm_online_request_processor.py:315` do — no suffixes, `ValueError` on junk, and
   `0` (not `None`) for a missing header.
2. Accept suffixes but round rather than floor, and accept separators by stripping `","` and
   `"_"` first — friendlier parsing, and `"1,000"` is a plausible provider rendering.
3. Treat a value of `"0"` as a real limit of zero (throttle everything) instead of as absent,
   since the provider did report a number.

**The observable.**
`parse_limit_value("999") == 999`; `parse_limit_value("1.5k") == 1500`;
`parse_limit_value("2M") == 2000000`; `parse_limit_value("40000.5") == 40000`;
`parse_limit_value("  60000  ") == 60000`; `parse_limit_value(4000) == 4000`;
`parse_limit_value("0") is None`; `parse_limit_value(0) is None`;
`parse_limit_value("1,000") is None`; `parse_limit_value("1e3") is None`;
`parse_limit_value("-5") is None`; `parse_limit_value("") is None`;
`parse_limit_value(None) is None`; `parse_limit_value(True) is None`;
`parse_limit_value(1500.0) is None`.
End to end through the reading:
`read_rate_limit_headers({"x-ratelimit-limit-tokens": "1.5k", "x-ratelimit-limit-requests": "0"})`
→ `max_tokens_per_minute == 1500`, `max_requests_per_minute is None`,
`source_headers == ("x-ratelimit-limit-tokens",)` (alternative 1 raises or yields `0`;
alternative 3 yields `0` and a `("x-ratelimit-limit-requests", …)` prefix).

**Arbitrary:** chosen value (the exact grammar, the multipliers, floor-not-round) + invented
name (`parse_limit_value`) + policy (a `0` header is "unreported", a malformed header is not
an error).

### P11 — A complete input/output pair wins over the total, and decides the strategy

**Behaviour.** Strategy selection lives in the reading, not on `self`:
- both an input **and** an output limit parse to positive ints → `token_limit_strategy = seperate`,
  `max_tokens_per_minute = _TokenUsage(input=…, output=…)`, and any total-token header present is
  **ignored** (it does not appear in `source_headers`);
- otherwise → `token_limit_strategy = combined` and the total-token header is used; a lone half
  of the pair (input without output, or output without input) is discarded and never contributes;
- nothing usable → `max_tokens_per_minute = None`, `token_limit_strategy = combined`.

`read_rate_limit_headers` is a module-level function and mutates nothing.
`BaseOnlineRequestProcessor.apply_rate_limit_reading(reading)` is the only place that writes
processor state: it sets `self.header_based_max_requests_per_minute`,
`self.header_based_max_tokens_per_minute`, `self.token_limit_strategy = reading.token_limit_strategy`,
and then **re-reads** `self.default_max_tokens_per_minute` from
`_DEFAULT_COST_MAP["online"]["default"]["ratelimit"]["max_tokens_per_minute"]` for the *new*
strategy — `int` for `combined`, `_TokenUsage(**block)` for `seperate` — fixing bug 7.

**Alternatives a competent engineer would plausibly choose instead.**
1. Let the total win when both are present: `x-ratelimit-limit-tokens` is the headline limit
   and the pair is supplementary detail; `combined` is also the enum's `default`.
2. Synthesise the missing half of a pair — e.g. input present only ⇒
   `_TokenUsage(input=N, output=total - N)` or `output = N` — rather than discarding data the
   provider took the trouble to send.
3. Set the strategy on the processor from inside the header reader, as
   `litellm_online_request_processor.py:317` does (`self.token_limit_strategy = TokenLimitStrategy.seperate`),
   and leave `default_max_tokens_per_minute` as `__init__` computed it.

**The observable.**
`r = read_rate_limit_headers({"x-ratelimit-limit-requests": "600", "x-ratelimit-limit-tokens": "90000", "x-ratelimit-limit-input-tokens": "50000", "x-ratelimit-limit-output-tokens": "20000"})`
→ `r.token_limit_strategy is TokenLimitStrategy.seperate`,
`r.max_tokens_per_minute == _TokenUsage(input=50000, output=20000, total=70000)`,
`r.max_requests_per_minute == 600`,
`r.source_headers == ("x-ratelimit-limit-requests", "x-ratelimit-limit-input-tokens", "x-ratelimit-limit-output-tokens")`
(alternative 1 gives `90000` / `combined`).
Half a pair: `r2 = read_rate_limit_headers({"x-ratelimit-limit-input-tokens": "50000", "x-ratelimit-limit-tokens": "90000"})`
→ `r2.token_limit_strategy is TokenLimitStrategy.combined`, `r2.max_tokens_per_minute == 90000`,
`r2.source_headers == ("x-ratelimit-limit-tokens",)` (alternative 2 gives a `_TokenUsage`).
Processor side, on a stub built with `OnlineRequestProcessorConfig(model="gpt-4o-mini")`:
`proc.default_max_tokens_per_minute == 100000` at construction; after
`proc.apply_rate_limit_reading(r)` → `proc.token_limit_strategy is TokenLimitStrategy.seperate`,
`proc.header_based_max_tokens_per_minute == _TokenUsage(input=50000, output=20000, total=70000)`,
`proc.header_based_max_requests_per_minute == 600`, and
`proc.default_max_tokens_per_minute == _TokenUsage(input=100000, output=40000, total=140000)`
(alternative 3 leaves it at `100000`).

**Arbitrary:** policy with no local evidence (pair-beats-total; a half pair is discarded) +
deliberate departure (the reader returns the strategy instead of assigning it, and the default
block is re-read for the new strategy).

## End to end

One tracker, one stub processor, one fake clock, four reservations.

```python
class _Clock:
    def __init__(self, now): self.now = now
    def __call__(self): return self.now

clock = _Clock(1000.0)
tracker = OnlineStatusTracker(
    model="gpt-4o-mini",
    max_requests_per_minute=60,
    max_tokens_per_minute=10_000,
    capacity_clock=clock,
    total_requests=4,
)
tracker.start_tracker(Console(file=StringIO(), width=200, force_terminal=True))
```

State after construction:

```python
tracker.available_request_capacity == 60.0
tracker.available_token_capacity   == 10000.0
tracker.last_update_time           == 1000.0
tracker.token_limit_origin         == "configured"
tracker.request_limit_origin       == "configured"
```

**1 — reserve and succeed** (`clock.now == 1000.0`, stub estimate `_TokenUsage(input=700, output=300)`):

```python
blocked = proc._reserve_capacity(tracker, messages)
# blocked == _TokenUsage(input=700, output=300, total=1000)
# available_request_capacity == 59.0 ; available_token_capacity == 9000.0
await proc.handle_single_request_with_retries(..., blocked_capacity=blocked)   # finish_reason "stop", usage input=700 output=100
# available_request_capacity == 59.0 ; available_token_capacity == 9200.0
# num_capacity_settlements == 1 ; num_capacity_refunds == 0
```

**2 — six seconds later, reserve and fail** (`clock.now = 1006.0`, estimate `_TokenUsage(input=900, output=100)`):

```python
blocked = proc._reserve_capacity(tracker, messages)
# refill: 9200 + 10000*6/60 = 10200 -> capped 10000.0 ; requests 59 + 6 = 65 -> capped 60.0
# after consume: available_request_capacity == 59.0 ; available_token_capacity == 9000.0
# last_update_time == 1006.0
await proc.handle_single_request_with_retries(..., blocked_capacity=blocked)   # finish_reason "length", usage input=900 output=800, attempts_left=0
# available_request_capacity == 60.0 ; available_token_capacity == 10000.0
# num_capacity_settlements == 1 ; num_capacity_refunds == 1
```

**3 — an impossible request** (`clock.now = 1042.0`, estimate `_TokenUsage(input=9000, output=2000)`):

```python
with pytest.raises(CapacityExceedsLimitError) as exc:
    proc._reserve_capacity(tracker, messages)
exc.value.axis == "total"
exc.value.requested == 11000
exc.value.limit == 10000
str(exc.value) == "request needs 11000 total capacity but the per-minute limit is 10000"
# nothing moved: available_request_capacity == 60.0 ; available_token_capacity == 10000.0
# last_update_time == 1006.0
```

**4 — a wild underestimate** (still `clock.now == 1042.0`, estimate `_TokenUsage(input=100, output=100)`):

```python
blocked = proc._reserve_capacity(tracker, messages)
# refill at 1042.0: both axes already at cap -> 60.0 / 10000.0 ; last_update_time == 1042.0
# after consume: available_request_capacity == 59.0 ; available_token_capacity == 9800.0
await proc.handle_single_request_with_retries(..., blocked_capacity=blocked)   # finish_reason "stop", usage input=9000 output=4000
# settlement delta = 200 - 13000 = -12800 -> 9800 - 12800 = -3000 -> floor -0.25*10000
```

Final, exact:

```python
tracker.available_request_capacity == 59.0
tracker.available_token_capacity   == -2500.0
tracker.last_update_time           == 1042.0
tracker.num_capacity_settlements   == 2
tracker.num_capacity_refunds       == 1
tracker.num_capacity_debt_clamps   == 1
proc.estimate_calls                == 4
tracker.token_limit_origin         == "configured"
```

And the header half, on the same processor:

```python
reading = read_rate_limit_headers({
    "Anthropic-RateLimit-Requests-Limit": "4k",
    "anthropic-ratelimit-input-tokens-limit": "400000",
    "anthropic-ratelimit-output-tokens-limit": "80000",
    "llm_provider-anthropic-ratelimit-output-tokens-remaining": "17",
    "x-ratelimit-limit-tokens": "1,000",
})
reading == RateLimitReading(
    max_requests_per_minute=4000,
    max_tokens_per_minute=_TokenUsage(input=400000, output=80000, total=480000),
    token_limit_strategy=TokenLimitStrategy.seperate,
    source_headers=(
        "anthropic-ratelimit-requests-limit",
        "anthropic-ratelimit-input-tokens-limit",
        "anthropic-ratelimit-output-tokens-limit",
    ),
)
proc.apply_rate_limit_reading(reading)
proc.token_limit_strategy is TokenLimitStrategy.seperate
proc.max_tokens_per_minute == _TokenUsage(input=400000, output=80000, total=480000)
proc.default_max_tokens_per_minute == _TokenUsage(input=100000, output=40000, total=140000)
```
