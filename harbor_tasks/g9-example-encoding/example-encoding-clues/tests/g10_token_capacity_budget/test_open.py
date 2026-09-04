"""g10 — the openly stated feature: one capacity-budget module, one reservation path.

The ticket states, in the open:

  * a new module `status_tracker/capacity_budget.py` holding the limit constants, the
    origin strings, the four header-name tuples, `TokenLimitStrategy` (moved), the
    frozen `RateLimitReading`, `CapacityExceedsLimitError`, `parse_limit_value` and
    `read_rate_limit_headers`;
  * an `OnlineStatusTracker` whose per-minute buckets are seeded, refilled and settled
    through an injectable `capacity_clock`, whose limits normalise `None` -> unlimited
    and `0` -> defaulted, and which raises rather than spins when an estimate can never
    fit;
  * a `BaseOnlineRequestProcessor` with a synchronous all-or-nothing `_reserve_capacity`,
    an `apply_rate_limit_reading` that re-reads the default block for the strategy the
    reading chose, and no `free_capacity` method left behind.

All of that is one feature and scores as one test.

Deliberately NOT asserted here, because they belong to the hidden requirements and must
be measurable separately: the debt floor and its clamp counter (r1), and the split
between a settlement and a refund, including what happens to the request slot on a
release (r2). This module therefore never inspects `available_request_capacity` after a
release, and never drives a token axis below zero.

Also not asserted: the three provider processors' `get_header_based_rate_limits`. Every
fact the ticket states about them — the un-swapped anthropic axes, the vanished
`-remaining` reads, the vanished 4000/80000/400000 fallbacks — is a fact about
`read_rate_limit_headers`, which is exercised directly below; reaching the provider
methods themselves needs a live `test_call()` or a `requests.post`, i.e. a network.
"""
from __future__ import annotations

import asyncio
import datetime
import time as _time

import pytest
from harness import read_field

_IMPORT_ERROR = None
try:
    from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        APIRequest,
        BaseOnlineRequestProcessor,
    )
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
    from bespokelabs.curator.types.generic_request import GenericRequest
    from bespokelabs.curator.types.generic_response import GenericResponse
    from bespokelabs.curator.types.token_usage import _TokenUsage
except Exception as exc:  # pragma: no cover - reported per test by importable()
    _IMPORT_ERROR = exc
    OnlineRequestProcessorConfig = APIRequest = BaseOnlineRequestProcessor = None
    OnlineStatusTracker = GenericRequest = GenericResponse = _TokenUsage = None

_BUDGET_ERROR = None
try:
    from bespokelabs.curator.status_tracker import capacity_budget as budget
except Exception as exc:  # pragma: no cover - reported per test by budget_module()
    _BUDGET_ERROR = exc
    budget = None


# ---------------------------------------------------------------------------
# Guards and tolerant readers, shared with test_r1 / test_r2
# ---------------------------------------------------------------------------
def importable():
    """Curator itself must import; anything else is an environment fault, not a grade."""
    if _IMPORT_ERROR is not None:
        pytest.fail(f"curator did not import: {_IMPORT_ERROR!r}")


def budget_module():
    """The capacity-budget module, named by the ticket, or a clear failure."""
    importable()
    if budget is None:
        pytest.fail(
            "bespokelabs.curator.status_tracker.capacity_budget did not import: "
            f"{_BUDGET_ERROR!r}"
        )
    return budget


_MISSING = object()


def find_const(name, *aliases, default=_MISSING):
    """A module-level constant, looked up in the module the ticket names.

    Also looked for in `online_status_tracker`, which the ticket says re-exports the
    same names for existing importers, so an implementation that put the canonical
    definition on either side is read the same way. Returns `default` when nothing
    answers to any of the names.
    """
    import sys

    homes = [budget_module()]
    tracker_mod = sys.modules.get(getattr(OnlineStatusTracker, "__module__", ""), None)
    if tracker_mod is not None:
        homes.append(tracker_mod)
    for candidate in (name, *aliases):
        for home in homes:
            if hasattr(home, candidate):
                return getattr(home, candidate)
    return default


def const(name, *aliases):
    """`find_const`, but a missing constant is a failed requirement rather than a None."""
    value = find_const(name, *aliases)
    if value is _MISSING:
        pytest.fail(f"no constant named {name!r} on the capacity budget module")
    return value


class Clock:
    """A callable clock whose `now` a test sets. No sleeping, no wall clock."""

    def __init__(self, now: float = 1000.0):
        self.now = float(now)

    def __call__(self) -> float:
        return self.now


def T(**kw):
    """`_TokenUsage(input=..., output=...)`, shorter."""
    return _TokenUsage(**kw)


def tracker(**kw):
    """An `OnlineStatusTracker` on an injected clock, with a model that is priced."""
    kw.setdefault("model", "gpt-4o-mini")
    kw.setdefault("capacity_clock", Clock(1000.0))
    return OnlineStatusTracker(**kw)


def token_axes(capacity):
    """`(input, output, total)` of a token capacity, whatever shape it is in.

    Under `combined` a single number is the total and the axes are unknown; under
    `seperate` the three come off the `_TokenUsage`. `None` means unlimited.
    """
    if capacity is None:
        return (None, None, None)
    if isinstance(capacity, (int, float)):
        return (None, None, capacity)
    return (
        read_field(capacity, "input"),
        read_field(capacity, "output"),
        read_field(capacity, "total"),
    )


def reading_fields(reading):
    """The four fields of a `RateLimitReading`, by the names the ticket fixes."""
    return (
        read_field(reading, "max_requests_per_minute"),
        read_field(reading, "max_tokens_per_minute"),
        read_field(reading, "token_limit_strategy"),
        tuple(read_field(reading, "source_headers")),
    )


class NullFormatter:
    """`prompt_formatter.response_to_response_format` is called on the success path."""

    def response_to_response_format(self, message):
        return None


class NullViewer:
    """`_viewer_client.log_cost_projection` is awaited on the success path."""

    async def log_cost_projection(self, status_tracker, force_log=False):
        return None


class StubProcessor(BaseOnlineRequestProcessor if BaseOnlineRequestProcessor else object):
    """The five abstract methods, a counted estimator and a queue of canned responses.

    No sockets: `call_single_request` hands back whatever the test put in `responses`,
    and `append_generic_response` writes nothing.
    """

    def __init__(self, estimate):
        super().__init__(OnlineRequestProcessorConfig(model="gpt-4o-mini"))
        self._estimate = estimate
        self.estimate_calls = 0
        self.responses = []
        self.appended = []
        self.prompt_formatter = NullFormatter()
        self._viewer_client = NullViewer()

    # --- the five abstract methods -----------------------------------------
    def file_upload_limit_check(self, base64_image: str) -> None:
        return None

    def estimate_total_tokens(self, messages: list):
        self.estimate_calls += 1
        return T(input=self._estimate.input, output=self._estimate.output)

    def estimate_output_tokens(self) -> int:
        return self._estimate.output

    def create_api_specific_request_online(self, generic_request):
        return {}

    async def call_single_request(self, request, session, status_tracker):
        return self.responses.pop(0)

    # --- no I/O ------------------------------------------------------------
    async def append_generic_response(self, status_tracker, data, filename) -> None:
        self.appended.append(data)


def make_request(attempts_left: int = 0):
    generic = GenericRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        original_row={},
        original_row_idx=0,
    )
    return APIRequest(
        task_id=0,
        generic_request=generic,
        api_specific_request={},
        attempts_left=attempts_left,
    )


def make_response(finish_reason: str, usage):
    generic = GenericRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        original_row={},
        original_row_idx=0,
    )
    now = datetime.datetime.now()
    return GenericResponse(
        response_message={"answer": "ok"},
        response_errors=None,
        raw_request={},
        raw_response={},
        generic_request=generic,
        created_at=now,
        finished_at=now,
        token_usage=usage,
        response_cost=0.0,
        finish_reason=finish_reason,
    )


def run_attempt(proc, status_tracker, blocked, *, attempts_left: int, response):
    """One trip through `handle_single_request_with_retries`, no real waiting.

    `asyncio.run` rather than pytest-asyncio: the coroutine awaits nothing but the
    stubs, so a plain event loop per call keeps the suite free of an asyncio_mode
    setting it does not control.
    """

    async def drive():
        proc.responses.append(response)
        request = make_request(attempts_left=attempts_left)
        await proc.handle_single_request_with_retries(
            request=request,
            session=None,
            retry_queue=asyncio.Queue(),
            response_file="unused",
            status_tracker=status_tracker,
            blocked_capacity=blocked,
        )
        return request

    return asyncio.run(drive())


# =============================================================================
# the open feature
# =============================================================================
def test_open_feature__one_capacity_budget_decodes_limits_and_reserves_all_or_nothing():
    """The module, the injected clock, the normalised limits, the raise, the reservation."""
    mod = budget_module()

    # ---- the constants the ticket lists -----------------------------------
    assert const("DEFAULT_MAX_REQUESTS_PER_MINUTE") == 200
    assert const("DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED") == 100_000
    assert const("DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE") == 100_000
    assert const("DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE") == 40_000
    assert const("LIMIT_ORIGIN_CONFIGURED") == "configured"
    assert const("LIMIT_ORIGIN_DEFAULTED") == "defaulted"
    assert const("LIMIT_ORIGIN_UNLIMITED") == "unlimited"

    assert tuple(const("REQUEST_LIMIT_HEADERS")) == (
        "x-ratelimit-limit-requests",
        "anthropic-ratelimit-requests-limit",
    )
    assert tuple(const("INPUT_TOKEN_LIMIT_HEADERS")) == (
        "x-ratelimit-limit-input-tokens",
        "anthropic-ratelimit-input-tokens-limit",
    )
    assert tuple(const("OUTPUT_TOKEN_LIMIT_HEADERS")) == (
        "x-ratelimit-limit-output-tokens",
        "anthropic-ratelimit-output-tokens-limit",
    )
    assert tuple(const("TOTAL_TOKEN_LIMIT_HEADERS")) == (
        "x-ratelimit-limit-tokens",
        "anthropic-ratelimit-tokens-limit",
    )

    # `TokenLimitStrategy` moved here and is re-exported for existing importers.
    import bespokelabs.curator.status_tracker.online_status_tracker as ost

    strategy = mod.TokenLimitStrategy
    assert ost.TokenLimitStrategy is strategy
    assert {m.value for m in strategy} == {"combined", "seperate"}
    assert strategy.default is strategy.combined

    # ---- parse_limit_value ------------------------------------------------
    parse = mod.parse_limit_value
    assert parse("999") == 999
    assert parse("1.5k") == 1500
    assert parse("2M") == 2_000_000
    assert parse("40000.5") == 40000
    assert parse("  60000  ") == 60000
    assert parse(4000) == 4000
    for absent in ("0", 0, "1,000", "1e3", "-5", "", "unknown", None, True, 1500.0, b"12"):
        assert parse(absent) is None, f"{absent!r} should decode as absent"

    # ---- read_rate_limit_headers -----------------------------------------
    read = mod.read_rate_limit_headers

    # anthropic's input header is the INPUT axis (the shipped code swaps them)
    rpm, tpm, strat, sources = reading_fields(
        read(
            {
                "anthropic-ratelimit-requests-limit": "4000",
                "anthropic-ratelimit-input-tokens-limit": "400000",
                "anthropic-ratelimit-output-tokens-limit": "80000",
            }
        )
    )
    assert rpm == 4000
    assert strat is strategy.seperate
    assert token_axes(tpm) == (400000, 80000, 480000)
    assert sources == (
        "anthropic-ratelimit-requests-limit",
        "anthropic-ratelimit-input-tokens-limit",
        "anthropic-ratelimit-output-tokens-limit",
    )

    # remaining counters and llm_provider-* keys are never read; no fallbacks
    for headers in (
        {
            "llm_provider-anthropic-ratelimit-input-tokens-remaining": "12345",
            "llm_provider-anthropic-ratelimit-output-tokens-remaining": "678",
            "x-ratelimit-remaining-requests": "9",
            "x-ratelimit-reset-tokens": "60s",
        },
        {},
    ):
        rpm, tpm, strat, sources = reading_fields(read(headers))
        assert (rpm, tpm, strat, sources) == (None, None, strategy.combined, ())

    # header names match case-insensitively, and are reported lower-cased
    rpm, tpm, strat, sources = reading_fields(read({"X-RateLimit-Limit-Tokens": "60000"}))
    assert (rpm, tpm, strat, sources) == (
        None,
        60000,
        strategy.combined,
        ("x-ratelimit-limit-tokens",),
    )

    # a complete pair beats the total and picks `seperate`; the total is not consumed
    rpm, tpm, strat, sources = reading_fields(
        read(
            {
                "x-ratelimit-limit-requests": "600",
                "x-ratelimit-limit-tokens": "90000",
                "x-ratelimit-limit-input-tokens": "50000",
                "x-ratelimit-limit-output-tokens": "20000",
            }
        )
    )
    assert rpm == 600
    assert strat is strategy.seperate
    assert token_axes(tpm) == (50000, 20000, 70000)
    assert sources == (
        "x-ratelimit-limit-requests",
        "x-ratelimit-limit-input-tokens",
        "x-ratelimit-limit-output-tokens",
    )

    # half a pair is discarded, the total wins, the strategy stays combined
    rpm, tpm, strat, sources = reading_fields(
        read({"x-ratelimit-limit-input-tokens": "50000", "x-ratelimit-limit-tokens": "90000"})
    )
    assert (rpm, tpm, strat, sources) == (
        None,
        90000,
        strategy.combined,
        ("x-ratelimit-limit-tokens",),
    )

    # a "0" header is unreported, and does not appear among the sources
    rpm, tpm, strat, sources = reading_fields(
        read({"x-ratelimit-limit-tokens": "1.5k", "x-ratelimit-limit-requests": "0"})
    )
    assert (rpm, tpm, sources) == (None, 1500, ("x-ratelimit-limit-tokens",))

    # ---- the tracker: seeded full, on an injected clock -------------------
    clock = Clock(1000.0)
    t = tracker(
        max_requests_per_minute=60,
        max_tokens_per_minute=10_000,
        available_request_capacity=1.0,   # overwritten by the seeding
        available_token_capacity=0,       # overwritten by the seeding
        capacity_clock=clock,
    )
    assert t.last_update_time == 1000.0
    # the injected clock, not the wall clock the dataclass default would have used
    assert abs(t.last_update_time - _time.time()) > 1e9
    assert t.available_request_capacity == 60.0
    assert t.available_token_capacity == 10000.0
    assert t.token_limit_origin == "configured"
    assert t.request_limit_origin == "configured"

    t.consume_capacity(T(input=3000, output=1000))
    assert t.available_token_capacity == 6000.0
    clock.now = 1006.0
    t.update_capacity()
    assert t.available_token_capacity == 7000.0
    assert t.last_update_time == 1006.0

    # a clock that goes backwards refills nothing and still moves the marker
    clock.now = 996.0
    t.update_capacity()
    assert t.available_token_capacity == 7000.0
    assert t.last_update_time == 996.0

    # ---- `seperate`: fresh _TokenUsage every time, floored refill ---------
    sep_clock = Clock(500.0)
    ts = tracker(
        token_limit_strategy=strategy.seperate,
        max_requests_per_minute=60,
        max_tokens_per_minute=T(input=10_000, output=5_000),
        capacity_clock=sep_clock,
    )
    assert token_axes(ts.available_token_capacity) == (10000, 5000, 15000)
    ts.consume_capacity(T(input=600, output=200))
    assert token_axes(ts.available_token_capacity) == (9400, 4800, 14200)
    sep_clock.now = 501.0
    ts.update_capacity()
    assert token_axes(ts.available_token_capacity) == (9566, 4883, 14449)

    # ---- `0` is "nobody told us", `None` is unlimited ---------------------
    td = tracker(max_requests_per_minute=0, max_tokens_per_minute=0)
    assert td.max_requests_per_minute == 200
    assert td.max_tokens_per_minute == 100_000
    assert td.available_request_capacity == 200.0
    assert td.available_token_capacity == 100000.0
    assert td.request_limit_origin == "defaulted"
    assert td.token_limit_origin == "defaulted"

    tu = tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    assert tu.max_tokens_per_minute is None
    assert tu.available_token_capacity is None
    assert tu.available_request_capacity is None
    assert tu.request_limit_origin == "unlimited"
    assert tu.token_limit_origin == "unlimited"
    assert tu.has_capacity(T(input=10**9, output=10**9)) is True
    tu.consume_capacity(T(input=10**9, output=10**9))
    assert tu.available_token_capacity is None
    assert tu.available_request_capacity is None

    tsu = tracker(token_limit_strategy=strategy.seperate, max_tokens_per_minute=None)
    assert token_axes(tsu.max_tokens_per_minute) == (None, None, None)
    assert token_axes(tsu.available_token_capacity) == (None, None, None)
    assert tsu.token_limit_origin == "unlimited"

    tpa = tracker(
        token_limit_strategy=strategy.seperate,
        max_tokens_per_minute=T(input=0, output=20_000),
    )
    assert token_axes(tpa.max_tokens_per_minute) == (100000, 20000, 120000)
    assert tpa.token_limit_origin == "defaulted"

    # shape coercion, both ways
    assert token_axes(
        tracker(token_limit_strategy=strategy.seperate, max_tokens_per_minute=90_000).max_tokens_per_minute
    ) == (90000, 90000, 180000)
    assert tracker(max_tokens_per_minute=T(input=30_000, output=20_000)).max_tokens_per_minute == 50000

    # ---- a request that can never fit raises, and moves nothing -----------
    raise_clock = Clock(1000.0)
    te = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000, capacity_clock=raise_clock)
    raise_clock.now = 1042.0
    with pytest.raises(mod.CapacityExceedsLimitError) as exc:
        te.has_capacity(T(input=9000, output=2000))
    assert isinstance(exc.value, ValueError)
    assert exc.value.axis == "total"
    assert exc.value.requested == 11000
    assert exc.value.limit == 10000
    assert str(exc.value) == "request needs 11000 total capacity but the per-minute limit is 10000"
    assert te.last_update_time == 1000.0          # the check ran before update_capacity()
    assert te.available_token_capacity == 10000.0

    tse = tracker(
        token_limit_strategy=strategy.seperate,
        max_requests_per_minute=60,
        max_tokens_per_minute=T(input=1_000, output=500),
    )
    with pytest.raises(mod.CapacityExceedsLimitError) as sep_exc:
        tse.has_capacity(T(input=1500, output=800))
    assert (sep_exc.value.axis, sep_exc.value.requested, sep_exc.value.limit) == ("input", 1500, 1000)

    # an unlimited axis never raises; a merely-empty bucket still returns False
    assert tu.has_capacity(T(input=10**12, output=10**12)) is True
    tb = tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    tb.consume_capacity(T(input=900, output=50))
    assert tb.has_capacity(T(input=100, output=100)) is False

    # ---- _reserve_capacity: estimate once, all or nothing -----------------
    proc = StubProcessor(T(input=700, output=100))
    tr = tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    first = proc._reserve_capacity(tr, [])
    assert token_axes(first) == (700, 100, 800)
    assert tr.available_token_capacity == 200.0
    assert tr.available_request_capacity == 59.0
    assert proc.estimate_calls == 1

    second = proc._reserve_capacity(tr, [])
    assert second is None
    assert tr.available_token_capacity == 200.0     # nothing consumed on a refusal
    assert tr.available_request_capacity == 59.0    # not even the request slot
    assert proc.estimate_calls == 2

    # the estimate is taken even when there is no token limit at all
    unlimited = tracker(max_requests_per_minute=60, max_tokens_per_minute=None)
    third = proc._reserve_capacity(unlimited, [])
    assert token_axes(third) == (700, 100, 800)
    assert proc.estimate_calls == 3
    assert unlimited.available_token_capacity is None
    assert unlimited.available_request_capacity == 59.0

    # ---- the dead helper is gone -----------------------------------------
    assert hasattr(BaseOnlineRequestProcessor, "free_capacity") is False

    # ---- apply_rate_limit_reading re-reads the default block --------------
    fresh = StubProcessor(T(input=700, output=100))
    assert fresh.default_max_tokens_per_minute == 100000
    assert fresh.token_limit_strategy is strategy.combined
    reading = read(
        {
            "x-ratelimit-limit-requests": "600",
            "x-ratelimit-limit-input-tokens": "50000",
            "x-ratelimit-limit-output-tokens": "20000",
        }
    )
    fresh.apply_rate_limit_reading(reading)
    assert fresh.token_limit_strategy is strategy.seperate
    assert fresh.header_based_max_requests_per_minute == 600
    assert token_axes(fresh.header_based_max_tokens_per_minute) == (50000, 20000, 70000)
    assert token_axes(fresh.default_max_tokens_per_minute) == (100000, 40000, 140000)
    # the manual -> header -> default precedence is unchanged
    assert token_axes(fresh.max_tokens_per_minute) == (50000, 20000, 70000)
    assert fresh.max_requests_per_minute == 600
