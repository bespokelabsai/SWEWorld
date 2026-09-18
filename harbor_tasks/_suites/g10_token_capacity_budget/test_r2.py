"""g10 — hidden requirement r2: a settlement and a refund are two different operations.

    rule       `free_capacity(used, blocked)` settles — token axes gain `blocked - used`, the
               request slot stays spent. `refund_capacity(blocked)` refunds — the whole
               estimate comes back and `available_request_capacity` gains exactly 1.0, both
               capped at their limits. The processor's failure release is `_refund_capacity`,
               which delegates to the tracker's `refund_capacity`
    scope      every terminal path through the `except` branch of
               `handle_single_request_with_retries` refunds — the requeued one as well as the
               exhausted one — while the success path keeps its settlement
    exclusions  the failure refund is the whole blocked estimate and ignores the
               `token_usage` a failed response happened to carry
    observability `num_capacity_settlements` and `num_capacity_refunds` are incremented by
               their own operation and by neither the other's, and both still count when the
               capacity they touch is `None` and the work is a no-op

`rule` and `observability` speak to the tracker directly, because that is where the two
operations differ; `scope` and `exclusions` drive the real coroutine. `scope` gives its
failed responses a `token_usage` equal to the blocked estimate so its subject is WHICH paths
release, and `exclusions` makes the two differ so its subject is HOW MUCH comes back.

NOT THE GRADED PATH, and the numbers below are one worked example. `judge.py`
re-draws the limits, the estimates and the reported usages from the run's seed
(`fixture_spec.py`) and recomputes what each release must leave behind. The four
facts below additionally ask root to read the submission, because a forged
observation claiming a refund happened is not evidence that one can happen:
the tracker must declare a refund operation taking the blocked capacity alone,
`BaseOnlineRequestProcessor._refund_capacity` must delegate to it, the two
counters must be separate fields that only their own operation increments, and
the handler's `except` body must reach a refund on EVERY terminal path -- not
only when attempts remain.
"""
from __future__ import annotations

import pytest
from harness import read_field, require_feature

from test_open import (
    StubProcessor,
    T,
    importable,
    make_response,
    run_attempt,
    token_axes,
    tracker,
)


def settlements(t):
    return read_field(t, "num_capacity_settlements", "num_settlements", "num_capacity_frees")


def refunds(t):
    return read_field(t, "num_capacity_refunds", "num_refunds")


def refund_op(t):
    """The tracker's refund operation, which r2 names `refund_capacity`."""
    for name in ("refund_capacity", "refund"):
        fn = getattr(t, name, None)
        if callable(fn):
            return fn
    pytest.fail(
        f"{type(t).__name__} has no refund operation; a release is still a single "
        "settlement, so a failed attempt cannot get its request slot back"
    )


def has_refund(t) -> bool:
    return any(callable(getattr(t, name, None)) for name in ("refund_capacity", "refund"))


# =============================================================================
# rule — settlement keeps the request slot spent, refund gives it back
# =============================================================================
def test_rule__a_refund_returns_the_whole_estimate_and_one_request_slot():
    """Two operations, two effects on `available_request_capacity`: 60.0 vs 59.0."""
    importable()

    # --- refund: the whole blocked estimate, plus exactly one request slot ---
    refunded = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    refunded.consume_capacity(T(input=600, output=200))
    assert (refunded.available_request_capacity, refunded.available_token_capacity) == (59.0, 9200.0)

    refund_op(refunded)(T(input=600, output=200))
    assert refunded.available_request_capacity == 60.0
    assert refunded.available_token_capacity == 10000.0

    # capped above at the limit: a second refund cannot inflate either bucket
    refund_op(refunded)(T(input=600, output=200))
    assert refunded.available_request_capacity == 60.0
    assert refunded.available_token_capacity == 10000.0

    # --- settlement: tokens move by blocked - used, the slot stays spent -----
    settled = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    settled.consume_capacity(T(input=600, output=200))
    settled.free_capacity(used=T(input=500, output=100), blocked=T(input=600, output=200))
    assert settled.available_token_capacity == 9400.0
    assert settled.available_request_capacity == 59.0     # NOT 60.0

    # --- the processor's failure release delegates to the refund ------------
    proc = StubProcessor(T(input=600, output=200))
    delegated = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    blocked = proc._reserve_capacity(delegated, [])
    assert (delegated.available_request_capacity, delegated.available_token_capacity) == (59.0, 9200.0)
    proc._refund_capacity(delegated, blocked)
    assert delegated.available_request_capacity == 60.0
    assert delegated.available_token_capacity == 10000.0


# =============================================================================
# scope — every `except` exit refunds; the success exit still settles
# =============================================================================
def test_scope__both_failure_exits_refund_while_the_success_exit_settles():
    """Exhausted, requeued and successful attempts, one reservation each."""
    importable()

    def reserve():
        proc = StubProcessor(T(input=700, output=300))
        t = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
        blocked = proc._reserve_capacity(t, [])
        assert (t.available_request_capacity, t.available_token_capacity) == (59.0, 9000.0)
        return proc, t, blocked

    # the exhausted failure (attempts_left == 0), which ends by appending an error
    proc, exhausted, blocked = reserve()
    run_attempt(
        proc,
        exhausted,
        blocked,
        attempts_left=0,
        response=make_response("length", T(input=700, output=300)),
    )
    assert exhausted.available_request_capacity == 60.0
    assert exhausted.available_token_capacity == 10000.0

    # the requeued failure (attempts_left > 0), which ends by putting the request back
    proc, requeued, blocked = reserve()
    request = run_attempt(
        proc,
        requeued,
        blocked,
        attempts_left=1,
        response=make_response("length", T(input=700, output=300)),
    )
    assert request.attempts_left == 0                     # it really took the requeue branch
    assert requeued.available_request_capacity == 60.0
    assert requeued.available_token_capacity == 10000.0

    # the success path is unchanged: a settlement, and the slot stays spent
    proc, succeeded, blocked = reserve()
    run_attempt(
        proc,
        succeeded,
        blocked,
        attempts_left=1,
        response=make_response("stop", T(input=700, output=100)),
    )
    assert succeeded.available_request_capacity == 59.0
    assert succeeded.available_token_capacity == 9200.0


# =============================================================================
# exclusions — the refund is the estimate, not the reported spend
# =============================================================================
def test_exclusions__the_failure_refund_ignores_the_usage_the_response_reported():
    """A failed response reporting 1700 tokens against a 1000-token reservation gets 1000 back."""
    importable()

    proc = StubProcessor(T(input=900, output=100))
    t = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    blocked = proc._reserve_capacity(t, [])
    assert token_axes(blocked) == (900, 100, 1000)
    assert (t.available_request_capacity, t.available_token_capacity) == (59.0, 9000.0)

    # finish_reason "length" is in config.invalid_finish_reasons, so this fails with a
    # token_usage in hand — 1700 spent against 1000 blocked.
    run_attempt(
        proc,
        t,
        blocked,
        attempts_left=0,
        response=make_response("length", T(input=900, output=800)),
    )

    # the whole estimate comes back: 9000 + 1000. A settlement against the reported
    # usage would have given 9000 + (1000 - 1700) == 8300.0 and left the slot spent.
    assert t.available_token_capacity == 10000.0
    assert t.available_request_capacity == 60.0


# =============================================================================
# observability — two counters, each moved by its own operation only
# =============================================================================
def test_observability__settlements_and_refunds_are_counted_apart_even_when_unlimited():
    """One counter each per call, and both still tick when every axis is `None`."""
    importable()

    settled = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    require_feature(has_refund(settled), "a tracker refund operation distinct from the settlement")

    assert (settlements(settled), refunds(settled)) == (0, 0)
    settled.consume_capacity(T(input=600, output=200))
    assert (settlements(settled), refunds(settled)) == (0, 0)   # consuming counts as neither
    settled.free_capacity(used=T(input=500, output=100), blocked=T(input=600, output=200))
    assert (settlements(settled), refunds(settled)) == (1, 0)

    refunded = tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    refunded.consume_capacity(T(input=600, output=200))
    refund_op(refunded)(T(input=600, output=200))
    assert (settlements(refunded), refunds(refunded)) == (0, 1)

    # an unlimited tracker: both operations are no-ops on every axis, and both still count
    unlimited = tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    unlimited.free_capacity(used=T(input=5, output=5), blocked=T(input=1, output=1))
    refund_op(unlimited)(T(input=1, output=1))
    assert (settlements(unlimited), refunds(unlimited)) == (1, 1)
    assert unlimited.available_token_capacity is None
    assert unlimited.available_request_capacity is None
