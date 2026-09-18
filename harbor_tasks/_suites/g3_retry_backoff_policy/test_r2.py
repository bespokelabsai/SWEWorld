"""g3 — hidden requirement r2: an absolute cooldown horizon that only 429s extend.

    rule              `OnlineStatusTracker` gains exactly one pause field, `throttle_cooldown_until:
                      float = 0.0`, immediately after `time_of_last_rate_limit_error`; a
                      THROTTLE verdict reads the injected clock once for `now`, stamps
                      `time_of_last_rate_limit_error = now` and advances the horizon
                      MONOTONICALLY, `max(horizon, now + delay)`; `remaining_cooldown_seconds`
                      is `max(0.0, round(until - now, 3))`
    scope             the horizon is run-level state extended only by throttles: a TRANSIENT,
                      CONTRACT or TERMINAL verdict moves its counter and nothing else, and
                      never calls the clock — so clock calls == rate-limit failures
    exclusions        `config.seconds_to_pause_on_rate_limit` is dead: it survives in config.py
                      at 10 for backwards compatibility, and the pause is derived neither from
                      it nor from elapsed time since `time_of_last_rate_limit_error`
    observability     the literal horizon and remaining-cooldown table the requirement writes

`rule` works at a clock of 500.0 with 8.0/4.0/16.0 delays; `observability` works at 1000.0
with the requirement's own 5.0 and 1.0 — so the monotonic max is measured twice from two
different directions rather than once. `exclusions` is the only test that runs
`cool_down_if_rate_limit_error`, and it grades the pause by which arguments reached a
stubbed `asyncio.sleep`, never by how long anything took.

Every verdict below is asked for through `test_open.decide`, which passes the waiver budget
only to an implementation that accepts it: r2 is not r1, and an agent who built this
requirement and not the other one must still be able to score it.
"""
from __future__ import annotations

import ast
import asyncio
import dataclasses
import inspect
import textwrap
import time
from types import SimpleNamespace

from harness import baseline_text, require_feature

from test_open import counters, decide, delay_field_name, fake_tracker, importable, make_processor, policy_with, record, v_delay

try:
    from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
    from bespokelabs.curator.request_processor.online import retry_policy as rp
    from bespokelabs.curator.request_processor.online.base_online_request_processor import BaseOnlineRequestProcessor
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
except Exception:  # pragma: no cover - reported by importable(), per test
    rp = OnlineRequestProcessorConfig = BaseOnlineRequestProcessor = OnlineStatusTracker = None

HORIZON = "throttle_cooldown_until"


def tracker_fields() -> list[str]:
    return [f.name for f in dataclasses.fields(OnlineStatusTracker)]


def horizon_is_implemented() -> bool:
    return HORIZON in tracker_fields()


def throttle_verdict(policy, *, attempts_made=0):
    return decide(policy, Exception("rate limit"), attempts_made=attempts_made, attempts_left=9, throttle_waivers_left=9)


# =============================================================================
# rule — one new field, stamped from the clock, advanced monotonically
# =============================================================================
def test_rule__the_cooldown_horizon_is_one_new_tracker_field_that_only_ever_moves_forward():
    importable()
    names = tracker_fields()
    assert HORIZON in names, f"OnlineStatusTracker has no cooldown horizon; its fields are {names}"
    assert names.index(HORIZON) == names.index("time_of_last_rate_limit_error") + 1, f"{HORIZON} is not declared immediately after time_of_last_rate_limit_error: {names}"
    assert OnlineStatusTracker().throttle_cooldown_until == 0.0

    # One field, not a family of them: of everything the live tracker declares
    # and the tree the world shipped did not, exactly one is about the pause.
    # (Scoped to pause-shaped names so that an unrelated field someone else's
    # requirement put there is not charged against this one.)
    # `baseline_text` rather than reading BASELINE: the pristine tree lives at
    # a different path in a Horizon image than in the world, and returns None
    # where there is no baseline at all. Nothing to diff against is not a
    # failed requirement, so the added-field check is skipped, not failed.
    shipped = baseline_text("status_tracker/online_status_tracker.py")
    if shipped is not None:
        added = {n for n in names if f"{n}:" not in shipped}
        about_the_pause = {n for n in added if any(word in n.lower() for word in ("cooldown", "pause", "backoff", "horizon", "throttle_until", "retry_after"))}
        assert about_the_pause == {HORIZON}, f"the tracker gained {sorted(about_the_pause)} for the pause; the requirement allows exactly one field"

    # A first throttle at 500.0 with a delay of 8.0 (jitter 1.0, attempt #1).
    policy, clock, _ = policy_with(clock_value=500.0, jitter_value=1.0)
    tracker = fake_tracker()
    long_wait = throttle_verdict(policy)
    assert v_delay(long_wait) == 8.0
    record(policy, tracker, long_wait)
    assert clock.calls == 1, "a throttle must read the injected clock exactly once"
    assert tracker.time_of_last_rate_limit_error == 500.0
    assert tracker.throttle_cooldown_until == 508.0

    # A second, SHORTER wait at the same instant must not pull the horizon in.
    shorter, _, _ = policy_with(clock_value=500.0, jitter_value=0.0)
    short_wait = throttle_verdict(shorter)
    assert v_delay(short_wait) == 4.0
    record(shorter, tracker, short_wait)
    assert tracker.throttle_cooldown_until == 508.0, "a later short delay must not shorten a horizon an earlier long one already set"
    assert tracker.time_of_last_rate_limit_error == 500.0

    # ... but a longer one does extend it.
    longer, _, _ = policy_with(clock_value=500.0, jitter_value=1.0)
    later = throttle_verdict(longer, attempts_made=1)
    assert v_delay(later) == 16.0
    record(longer, tracker, later)
    assert tracker.throttle_cooldown_until == 516.0

    # remaining_cooldown_seconds: clamped at zero, rounded to three decimals.
    horizoned = SimpleNamespace(time_of_last_rate_limit_error=0.0, **{HORIZON: 508.0009})
    assert rp.remaining_cooldown_seconds(horizoned, 500.0) == 8.001
    assert rp.remaining_cooldown_seconds(horizoned, 508.0) == 0.001
    assert rp.remaining_cooldown_seconds(horizoned, 508.0009) == 0.0
    assert rp.remaining_cooldown_seconds(horizoned, 600.0) == 0.0, "the remaining cooldown is never negative"


# =============================================================================
# scope — only a throttle touches the horizon, or the clock
# =============================================================================
def test_scope__only_throttles_extend_the_horizon_or_consult_the_clock():
    importable()
    require_feature(horizon_is_implemented(), "the tracker's throttle cooldown horizon")

    policy, clock, _ = policy_with(clock_value=700.0, jitter_value=0.25)
    tracker = fake_tracker()

    def apply(exc):
        record(policy, tracker, decide(policy, exc, attempts_made=0, attempts_left=9, throttle_waivers_left=9))

    apply(TimeoutError("x"))
    assert counters(tracker) == (0, 1, 0)
    apply(ValueError("bad"))
    assert counters(tracker) == (0, 1, 1)
    apply(PermissionError("no"))
    assert counters(tracker) == (0, 2, 1)
    assert clock.calls == 0, "a transient, contract or terminal verdict must not call the injected clock"
    assert tracker.throttle_cooldown_until == 0.0, "a non-throttle verdict must not touch the cooldown horizon"
    assert tracker.time_of_last_rate_limit_error == 0.0, "a non-throttle verdict must not stamp time_of_last_rate_limit_error"

    apply(Exception("rate limit"))
    assert counters(tracker) == (1, 2, 1)
    assert clock.calls == 1
    assert tracker.throttle_cooldown_until == 705.0
    assert tracker.time_of_last_rate_limit_error == 700.0

    # More non-throttles on top change neither timestamp, and cost no clock call.
    apply(TimeoutError("again"))
    apply(ValueError("again"))
    assert counters(tracker) == (1, 3, 2)
    assert clock.calls == 1
    assert tracker.throttle_cooldown_until == 705.0
    assert tracker.time_of_last_rate_limit_error == 700.0

    apply(Exception("too many requests"))
    assert clock.calls == 2, "over a mixed sequence the clock is called once per rate-limit failure and never otherwise"


# =============================================================================
# exclusions — the config knob survives, unread
# =============================================================================
def test_exclusions__the_seconds_to_pause_knob_survives_in_config_and_is_never_read_again():
    importable()
    require_feature(horizon_is_implemented(), "the tracker's throttle cooldown horizon")

    # Still there, still 10, still settable: nothing downstream breaks on it.
    assert "seconds_to_pause_on_rate_limit" in OnlineRequestProcessorConfig.model_fields
    assert OnlineRequestProcessorConfig(model="gpt-4o-mini").seconds_to_pause_on_rate_limit == 10
    assert OnlineRequestProcessorConfig(model="gpt-4o-mini", seconds_to_pause_on_rate_limit=42).seconds_to_pause_on_rate_limit == 42
    assert make_processor(max_retries=3, seconds_to_pause_on_rate_limit=10).config.seconds_to_pause_on_rate_limit == 10

    slept: list[float] = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    # The clock the processor reads is frozen for the three scenarios below and
    # the horizon is placed an exact number of seconds ahead of the frozen
    # instant, so the pause is compared exactly. It was `time.time() + 4.0`
    # graded as `3.0 < slept <= 4.0` -- two live readings a scenario apart -- and
    # a correct implementation failed whenever the host descheduled the process
    # for a second in between. Frozen before the processor is built, so a policy
    # that captured `time.time` at construction captured the frozen one.
    frozen_now = 1_700_000_000.0
    ahead_seconds = 4.0
    real_time, real_sleep = time.time, asyncio.sleep
    time.time = lambda: frozen_now
    asyncio.sleep = fake_sleep
    try:
        processor = make_processor(max_retries=3, seconds_to_pause_on_rate_limit=10)

        # A run that was rate limited long enough ago that its horizon has
        # lapsed -- but whose time_of_last_rate_limit_error is this instant.
        # Deriving the pause from the knob and that timestamp would wait ~10s.
        lapsed = OnlineStatusTracker()
        lapsed.time_of_last_rate_limit_error = frozen_now
        setattr(lapsed, HORIZON, 0.0)
        asyncio.run(processor.cool_down_if_rate_limit_error(lapsed))
        assert slept == [], f"the pause was derived from the knob or from time since the last 429: slept {slept}"

        # A run that has never been throttled at all waits nothing either.
        asyncio.run(processor.cool_down_if_rate_limit_error(OnlineStatusTracker()))
        assert slept == [], f"a run that has never been throttled paused for {slept}"

        # ... while a live horizon does pause, and pauses for exactly what the
        # horizon has left against the frozen clock.
        ahead = OnlineStatusTracker()
        ahead.time_of_last_rate_limit_error = 0.0
        setattr(ahead, HORIZON, frozen_now + ahead_seconds)
        asyncio.run(processor.cool_down_if_rate_limit_error(ahead))
        assert len(slept) == 1, f"a live cooldown horizon did not pause: slept {slept}"
        assert slept[0] == ahead_seconds, f"the pause is not the horizon's remaining time: {slept[0]}"
    finally:
        time.time = real_time
        asyncio.sleep = real_sleep

    # ... and the knob is not merely outvoted, it is not consulted at all. Asked of
    # the syntax tree, not the source text: a v7 run wrote a docstring explaining
    # why the knob is dead, near-quoting the remark that says so, and lost this fact
    # for naming it. An attribute read or an exact-name string (getattr) is a read;
    # prose that mentions it is not.
    tree = ast.parse(textwrap.dedent(inspect.getsource(BaseOnlineRequestProcessor)))
    reads = [
        node.lineno
        for node in ast.walk(tree)
        if (isinstance(node, ast.Attribute) and node.attr == "seconds_to_pause_on_rate_limit")
        or (isinstance(node, ast.Constant) and node.value == "seconds_to_pause_on_rate_limit")
    ]
    assert not reads, f"the online processor still reads the dead pause knob (class-relative lines {reads})"


# =============================================================================
# observability — the requirement's own horizon table, as literals
# =============================================================================
def test_observability__the_stated_horizon_and_remaining_cooldown_table_holds_exactly():
    importable()
    require_feature(horizon_is_implemented(), "the tracker's throttle cooldown horizon")

    policy, _, _ = policy_with(clock_value=1000.0, jitter_value=0.25)
    tracker = fake_tracker()

    first = decide(policy, Exception("rate limit"), attempts_made=0, attempts_left=5, throttle_waivers_left=6)
    assert v_delay(first) == 5.0
    record(policy, tracker, first)
    assert tracker.throttle_cooldown_until == 1005.0
    assert tracker.time_of_last_rate_limit_error == 1000.0

    # A second rate limit whose delay is only 1.0, at the very same clock.
    # (How many times the clock was read, and what a non-throttle verdict leaves
    # alone, are `scope`'s measurement and are deliberately not repeated here.)
    record(policy, tracker, dataclasses.replace(first, **{delay_field_name(first): 1.0}))
    assert tracker.throttle_cooldown_until == 1005.0, "the horizon is a monotonic maximum, not the latest assignment"

    assert rp.remaining_cooldown_seconds(tracker, 1002.0) == 3.0
    assert rp.remaining_cooldown_seconds(tracker, 1004.5) == 0.5
    assert rp.remaining_cooldown_seconds(tracker, 1005.0) == 0.0
    assert rp.remaining_cooldown_seconds(tracker, 1099.0) == 0.0

    fresh = OnlineStatusTracker()
    assert fresh.throttle_cooldown_until == 0.0
    assert rp.remaining_cooldown_seconds(fresh, 12345.0) == 0.0
