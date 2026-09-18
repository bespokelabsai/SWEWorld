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

Not asserted HERE, but graded: everything only the source can witness. Reaching a
provider processor's `get_header_based_rate_limits` needs a live `test_call()` or a
`requests.post`, i.e. a network, so "all three delegate", "the openai provider table and
its rps/tps scaling stay exactly as they are", "`cool_down_if_rate_limit_error` and the
tracker's rate-limit counters are out of scope", "both reservation loops
reserve through `_reserve_capacity` with the sleep as their only await", "the handler
keeps its try/except/else/finally" and "capacity_budget is stdlib only, 3.10 syntax" are
checked by `judge.py`'s `_check_*` functions, which parse the pushed tree and diff the
named function, class or declaration against the pristine copy at CURATOR_BASELINE_DIR.
The same fact, `test_open_feature`, carries them.

The out-of-scope FILES are not among them any more: `cost.py`,
`types/token_usage.py`, `types/generic_response.py` and `request_processor/config.py`
are `protected_files` in `tests/task.json`, so root byte-compares each with the
pristine tree and `score.py` holds the reward at 0 on any difference. That is why the
AST compares of `_TokenUsage`, the `RATE_LIMIT_HEADER` declaration and
`config.max_retries` / `config.seconds_to_pause_on_rate_limit` were deleted: bytes see
`RATE_LIMIT_HEADER.clear()`, `.update({...})` and a subscript assignment, and no
declaration diff does.

Four more of them the structure-and-name checks used to miss, and `judge.py` now
diffs against pristine as well (also on `test_open_feature`):

  * `handle_single_request_with_retries` is pristine apart from the capacity releases
    the ticket adds -- the except body, the exhausted branch, the else and the finally
    included. A four-clause `try` and four mentioned names passed a rewritten handler;
  * the retry queue's own operations, `put_nowait` in the handler and `empty`/`get` in
    the loop, in the order the world shipped them: every fact here drives ONE attempt,
    so nothing observes what a second attempt would come back to;
  * `num_rate_limit_errors` and `time_of_last_rate_limit_error` are not WRITTEN
    anywhere new, which a declaration compare alone does not say;
  * the three limit properties' manual -> header -> default ladder, and
    `OnlineStatusTracker.max_tokens_per_minute` declared exactly once (the world ships
    it twice, both defaulting to 0, so the duplicate is invisible in every value).

NOT THE GRADED PATH. The suite grades through `probe.py`/`judge.py`, and the
judge DERIVES its expectations from the seed root draws per run rather than
holding the literals below: a fixed fixture makes every expected value the same
every run, and g10's are published in `instruction.md`, so a tree implementing
nothing could hardcode a passing observations file (measured on v11: 9/9 from a
hand-written `observations.json`, and 9/9 again with both hidden requirements
deleted from the tree). What is here is the worked example of each fact on the
old fixed fixture, and the fact<->test bijection. Read it to see what a fact
MEANS; read `judge.py` for how it is decided, and `fixture_spec.py` for what
moves run to run. Only the ticket's own constants stay fixed on both sides: the
four `DEFAULT_MAX_*` numbers, the origin strings, the header-name tuples, the
field order and the rejected `parse_limit_value` forms.

One more source check landed with the seed, and it is on this fact:
`instruction.md:65`'s dead `free_capacity` helper is read out of the class body
now, not just reported absent by a worker boolean.
"""
from __future__ import annotations

import dataclasses
import time as _time

import pytest

# The answer-free helpers/inputs live in probe_support so the worker (probe.py)
# and this human reference share ONE definition and cannot drift. The expected
# VALUES this test asserts stay here (and in judge.py); probe_support holds none.
from probe_support import (  # noqa: F401
    BaseOnlineRequestProcessor,
    Clock,
    NullFormatter,
    NullViewer,
    StubProcessor,
    T,
    _TokenUsage,
    budget_module,
    const,
    count_releases,
    find_const,
    importable,
    make_request,
    make_response,
    reading_fields,
    run_attempt,
    token_axes,
    tracker,
)


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

    # ---- the reading's own shape -----------------------------------------
    reading_cls = mod.RateLimitReading
    assert dataclasses.is_dataclass(reading_cls)
    assert [f.name for f in dataclasses.fields(reading_cls)] == [
        "max_requests_per_minute",
        "max_tokens_per_minute",
        "token_limit_strategy",
        "source_headers",
    ]
    frozen_sample = read({"x-ratelimit-limit-tokens": "60000"})
    with pytest.raises(dataclasses.FrozenInstanceError):
        frozen_sample.max_requests_per_minute = 1

    # ---- tuple order decides, and the caller's mapping is not touched -----
    given = {
        "X-RateLimit-Limit-Requests": "abc",          # present but unparseable
        "anthropic-ratelimit-requests-limit": "900",  # so the next name answers
        "x-ratelimit-limit-tokens": "30000",
    }
    snapshot = dict(given)
    rpm, tpm, strat, sources = reading_fields(read(given))
    assert (rpm, tpm, strat) == (900, 30000, strategy.combined)
    assert sources == ("anthropic-ratelimit-requests-limit", "x-ratelimit-limit-tokens")
    assert given == snapshot, "the lower-casing is of a copy"

    rpm, _, _, sources = reading_fields(
        read({"x-ratelimit-limit-requests": "600", "anthropic-ratelimit-requests-limit": "900"})
    )
    assert (rpm, sources) == (600, ("x-ratelimit-limit-requests",))

    # ---- every seperate-axis mutation rebinds a fresh _TokenUsage ---------
    # `.total` is a stored pydantic field computed once at construction, so an
    # implementation that assigns to `.input` keeps every axis right and leaves
    # `.total` stale. Identity is what shows it; no axis reading does.
    idc = tracker(
        token_limit_strategy=strategy.seperate,
        max_requests_per_minute=60,
        max_tokens_per_minute=T(input=10_000, output=5_000),
    )
    seeded = idc.available_token_capacity
    idc.consume_capacity(T(input=600, output=200))
    consumed = idc.available_token_capacity
    assert consumed is not seeded
    assert token_axes(seeded) == (10000, 5000, 15000)
    assert token_axes(consumed) == (9400, 4800, 14200)
    idc.free_capacity(used=T(input=100, output=50), blocked=T(input=600, output=200))
    assert idc.available_token_capacity is not consumed
    assert token_axes(consumed) == (9400, 4800, 14200)

    # ---- manual -> header -> default, on all three limit properties -------
    prec = StubProcessor(T(input=1, output=1))
    prec.manual_max_requests_per_minute, prec.header_based_max_requests_per_minute = 11, 22
    prec.manual_max_tokens_per_minute, prec.header_based_max_tokens_per_minute = 33, 44
    prec.manual_max_concurrent_requests, prec.header_based_max_concurrent_requests = 55, 66
    assert (prec.max_requests_per_minute, prec.max_tokens_per_minute, prec.max_concurrent_requests) == (11, 33, 55)
    prec.manual_max_requests_per_minute = None
    prec.manual_max_tokens_per_minute = None
    prec.manual_max_concurrent_requests = None
    assert (prec.max_requests_per_minute, prec.max_tokens_per_minute, prec.max_concurrent_requests) == (22, 44, 66)
    prec.header_based_max_requests_per_minute = None
    prec.header_based_max_tokens_per_minute = None
    prec.header_based_max_concurrent_requests = None
    assert prec.max_requests_per_minute == prec.default_max_requests_per_minute
    assert prec.max_tokens_per_minute == prec.default_max_tokens_per_minute
    assert prec.max_concurrent_requests is None

    # ---- exactly one release per attempt, on every terminal path ----------
    # Counted rather than read off the buckets: a release is capped at the limit,
    # so a handler that releases the same reservation twice leaves every value
    # identical to one that releases it once. WHICH operation runs is r2's
    # (hidden) business; that it runs once is the ticket's.
    for attempts_left, response in (
        (0, make_response("length", T(input=700, output=300))),   # exhausted
        (1, make_response("length", T(input=700, output=300))),   # requeued
        (1, make_response("stop", T(input=700, output=100))),     # success
    ):
        proc = StubProcessor(T(input=700, output=300))
        t = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
        blocked = proc._reserve_capacity(t, [])
        counts = count_releases(t)
        run_attempt(proc, t, blocked, attempts_left=attempts_left, response=response)
        assert counts["settle"] + counts["refund"] == 1
