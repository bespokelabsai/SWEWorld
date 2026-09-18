"""g10 — hidden requirement r1: capacity may go into debt, but only 25 % of a minute deep.

    rule       token capacity may go negative when a settlement discovers an underestimate,
               but each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` with the
               fraction `0.25`; the worked case lands on `-250.0`, not `-700.0` and not `0.0`
    scope      the floor is taken from the tracker's EFFECTIVE per-minute limit — after `0`
               has become the default and after the shape coercion — per axis under
               `seperate`; an unlimited axis has no floor and stays `None`
    exclusions the upper cap is not a clamp: a refill capping at the limit, a release capping
               at the limit, and a settlement that stays above the floor all leave the clamp
               counter alone
    observability `num_capacity_debt_clamps` counts CALLS that clamped, not axes: the
               `seperate` case that floors both axes at once counts one

The three value tests read `available_token_capacity`; `exclusions` and `observability` read
the counter. `rule` fixes the fraction on one combined axis, `scope` fixes where the limit
comes from, and neither looks at the counter, so the four are four measurements.

`rule` and `scope` re-seed the bucket to the tracker's own effective limit before spending
it. A correct implementation seeds exactly that in `__post_init__` (an openly stated fact,
graded in `test_open`), so the re-seed changes nothing for a compliant tree — it is there so
that an agent who got the debt floor right and the seeding wrong loses one fact rather than
two.

NOT THE GRADED PATH, and the numbers below are one worked example. `judge.py`
re-draws the limits, the estimates and the reported usages from the run's seed
(`fixture_spec.py`) and recomputes the floor each fact expects, because eight
hidden facts whose expected values never changed were forgeable from the worker:
a hand-written `observations.json` passed all of them against a tree with the
floor and the counters deleted. The four facts below additionally ask root to
read the submission: `CAPACITY_DEBT_FLOOR_FRACTION` must really be declared as
the fraction, and the clamp counter must really be a tracker field starting at
zero that something increments. So `-250.0` here is `-0.25 x the limit` there.
"""
from __future__ import annotations

import pytest
from harness import read_field, require_feature

from test_open import Clock, T, budget_module, const, find_const, importable, token_axes, tracker

_TokenUsage = None
try:
    from bespokelabs.curator.types.token_usage import _TokenUsage
except Exception:  # pragma: no cover - reported by importable()
    pass


def clamp_count(t):
    """The clamp counter r1 names, read tolerantly across a couple of spellings."""
    return read_field(t, "num_capacity_debt_clamps", "num_debt_clamps", "num_capacity_clamps")


def has_clamp_counter(t) -> bool:
    return any(
        hasattr(t, name)
        for name in ("num_capacity_debt_clamps", "num_debt_clamps", "num_capacity_clamps")
    )


def has_floor_constant() -> bool:
    return find_const("CAPACITY_DEBT_FLOOR_FRACTION", "DEBT_FLOOR_FRACTION", default=None) is not None


def seed_full(t):
    """Put the token bucket back at the tracker's own effective per-minute limit.

    Isolates "how deep may debt go" from "how full does the bucket start", which is a
    different (and openly stated) fact.
    """
    limit = t.max_tokens_per_minute
    if limit is None:
        t.available_token_capacity = None
    elif isinstance(limit, (int, float)):
        t.available_token_capacity = float(limit)
    else:
        t.available_token_capacity = _TokenUsage(input=limit.input, output=limit.output)
    return t


# =============================================================================
# rule — an underestimate goes negative, and stops at -25 % of the limit
# =============================================================================
def test_rule__an_over_settled_axis_stops_at_a_quarter_of_the_limit_in_debt():
    """1_000 TPM, 800 blocked, 1_500 really spent: the bucket rests at -250.0."""
    importable()

    fraction = const("CAPACITY_DEBT_FLOOR_FRACTION", "DEBT_FLOOR_FRACTION")
    assert fraction == 0.25

    t = seed_full(tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000))

    t.consume_capacity(T(input=700, output=100))
    assert t.available_token_capacity == 200.0

    # settlement delta = blocked(800) - used(1500) = -700, landing on -500 unfloored
    t.free_capacity(used=T(input=1000, output=500), blocked=T(input=700, output=100))

    # -250.0: not -500.0 (no floor), not -1000.0 (floor at -limit), not 0.0 (floor at zero)
    assert t.available_token_capacity == -250.0


# =============================================================================
# scope — the floor is a fraction of the EFFECTIVE limit, axis by axis
# =============================================================================
def test_scope__the_floor_follows_the_normalised_limit_of_each_axis():
    """A defaulted limit floors at -25000.0; `seperate` axes floor against themselves."""
    importable()
    require_feature(has_floor_constant(), "a capacity debt floor fraction")

    # `0` means "nobody told us" -> 100_000 -> the floor is a quarter of THAT
    defaulted = seed_full(tracker(max_requests_per_minute=60, max_tokens_per_minute=0))
    assert defaulted.max_tokens_per_minute == 100_000
    defaulted.consume_capacity(T(input=90_000, output=10_000))
    assert defaulted.available_token_capacity == 0.0
    defaulted.free_capacity(used=T(input=200_000, output=0), blocked=T(input=90_000, output=10_000))
    assert defaulted.available_token_capacity == -25000.0

    # under `seperate` each axis is floored against its own limit
    sep = seed_full(
        tracker(
            token_limit_strategy=budget_module().TokenLimitStrategy.seperate,
            max_requests_per_minute=60,
            max_tokens_per_minute=T(input=1_000, output=500),
        )
    )
    sep.consume_capacity(T(input=700, output=100))
    assert token_axes(sep.available_token_capacity) == (300, 400, 700)
    sep.free_capacity(used=T(input=2000, output=1000), blocked=T(input=700, output=100))
    assert token_axes(sep.available_token_capacity) == (-250, -125, -375)

    # an unlimited axis has no floor at all and is left alone
    unlimited = tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    unlimited.consume_capacity(T(input=10**9, output=10**9))
    unlimited.free_capacity(used=T(input=10**9, output=10**9), blocked=T(input=1, output=1))
    assert unlimited.available_token_capacity is None
    assert unlimited.available_request_capacity is None

    # the request bucket is never floored: it only falls by one after a successful check
    assert defaulted.available_request_capacity == 59.0
    assert sep.available_request_capacity == 59.0


# =============================================================================
# exclusions — capping at the ceiling is not clamping at the floor
# =============================================================================
def test_exclusions__capping_at_the_limit_and_staying_above_the_floor_do_not_count():
    """Only the lower debt floor is a clamp; the upper cap and an ordinary settlement are not."""
    importable()
    probe = tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    require_feature(
        has_floor_constant() and has_clamp_counter(probe),
        "a capacity debt floor with a clamp counter",
    )

    # a refill that hits the ceiling
    clock = Clock(1000.0)
    refilled = tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000, capacity_clock=clock)
    refilled.consume_capacity(T(input=700, output=100))
    clock.now = 1060.0
    refilled.update_capacity()
    assert refilled.available_token_capacity == 1000.0     # capped, not 1200.0
    assert refilled.available_request_capacity == 60.0
    assert clamp_count(refilled) == 0

    # a release that hits the ceiling
    released = tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    released.free_capacity(used=T(input=0, output=0), blocked=T(input=700, output=100))
    assert released.available_token_capacity == 1000.0     # capped, not 1800.0
    assert clamp_count(released) == 0

    # a settlement that goes negative-ward but stays above the floor
    settled = tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    settled.consume_capacity(T(input=700, output=100))
    settled.free_capacity(used=T(input=700, output=200), blocked=T(input=700, output=100))
    assert settled.available_token_capacity == 100.0
    assert clamp_count(settled) == 0


# =============================================================================
# observability — one increment per clamping CALL, not per axis
# =============================================================================
def test_observability__the_clamp_counter_counts_calls_not_axes():
    """Both `seperate` axes bottom out in one settlement: that is one clamp, then two."""
    importable()

    sep = seed_full(
        tracker(
            token_limit_strategy=budget_module().TokenLimitStrategy.seperate,
            max_requests_per_minute=60,
            max_tokens_per_minute=T(input=1_000, output=500),
        )
    )
    assert clamp_count(sep) == 0

    sep.consume_capacity(T(input=700, output=100))
    assert clamp_count(sep) == 0                            # nothing clamped yet

    # one call, two axes clamped -> one increment
    sep.free_capacity(used=T(input=2000, output=1000), blocked=T(input=700, output=100))
    assert clamp_count(sep) == 1

    # a second clamping call is a second increment
    sep.free_capacity(used=T(input=5000, output=5000), blocked=T(input=0, output=0))
    assert clamp_count(sep) == 2
