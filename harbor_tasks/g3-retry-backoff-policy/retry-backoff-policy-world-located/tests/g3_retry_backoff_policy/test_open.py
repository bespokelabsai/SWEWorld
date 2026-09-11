"""g3 — the openly stated feature: a failure-class retry policy module, wired in.

Everything asserted here is spelled out in the ticket: the four `FailureClass`
members and their order, the four-signal precedence of `classify_failure`, the
status / type / marker tables, the `delay_for` schedule with the cap applied
before a half-jitter that is drawn exactly once per positive delay, the eight
`RetryVerdict` fields with their `class:outcome` reason code and routed tracker
counter name, `apply_to_tracker` moving exactly one counter, the
`[class] message (xN)` summary and its `attempt #N of M` label, the two new
`APIRequest` fields, the module's standard-library-only import list, and the
fact that the base processor builds a policy and its `except Exception` block
delegates to it.

Nothing here touches the hidden facts. It never asserts what a failure COSTS
(r1: the 0/1/2 price list, the waivers, the clamp), and it never asserts the
tracker's cooldown horizon (r2: `throttle_cooldown_until`, the monotonic max,
the dead config knob). Every `decide` call below is made with a budget so large
that every plausible pricing rule agrees the request is retried, and the fake
tracker carries the horizon fields only so that an implementation which does
stamp them does not trip over a missing attribute.

Graded out of process: `probe.py` (as `nobody`) reproduces these curator calls
and records the values; `judge.py` (root) applies the assertions below. The
answer-free helpers and the classification inputs live in `probe_support`, so
the probe and this reference share ONE definition and cannot drift; the expected
VALUES stay here (and in judge.py). `test_r1`/`test_r2` still import their shared
helpers `from test_open import ...`, which re-exports them from `probe_support`.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import pathlib

import pytest

from harness import read_field  # noqa: F401 - used in the wiring section below

# The answer-free helpers and classification inputs live in probe_support so the
# worker (probe.py) and this human reference share ONE definition. The expected
# VALUES this test asserts stay here (and in judge.py); probe_support holds none.
# Re-exported here so test_r1.py / test_r2.py keep `from test_open import ...`.
from probe_support import (  # noqa: F401
    APIRequest,
    OnlineStatusTracker,
    classify_marker_inputs,
    classify_status_inputs,
    classify_type_inputs,
    counter_moved,
    counters,
    decide,
    delay_field_name,
    drive_one_failure,
    drive_one_response,
    fake_tracker,
    importable,
    make_api_request,
    make_processor,
    policy_with,
    record,
    rp,
    v_attempt,
    v_budget,
    v_class,
    v_delay,
    v_reason,
    v_retry,
    v_waivers,
)


# =============================================================================
# the open feature
# =============================================================================
def test_open_feature__failures_are_classified_priced_and_summarised_by_the_policy_module():
    importable()
    # ---- P1: the enum, in declaration order, with a str mixin -------------
    assert [m.name for m in rp.FailureClass] == ["THROTTLE", "TRANSIENT", "CONTRACT", "TERMINAL"]
    assert [m.value for m in rp.FailureClass] == ["throttle", "transient", "contract", "terminal"]
    assert len(rp.FailureClass) == 4
    assert rp.FailureClass.CONTRACT == "contract"

    # ---- the module boundary: standard library only ----------------------
    source = pathlib.Path(inspect.getfile(rp)).read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"aiohttp", "time", "random"}), f"retry_policy.py imports {sorted(imported)}; it must not reach for aiohttp, time or random"

    # ---- P2: status first, and the table exactly as the ticket writes it --
    # ---- P3: the type signal walks the MRO, by name ----------------------
    # ---- P4: marker order beats message position; the default is TRANSIENT
    # The inputs live in probe_support (shared with the probe); the expected
    # classes are the answers and stay here. `.name` rather than an identity
    # compare because P1 above already pins the members and their order.
    assert [rp.classify_failure(e).name for e in classify_status_inputs()] == [
        "TRANSIENT", "THROTTLE", "THROTTLE", "CONTRACT", "CONTRACT", "CONTRACT",
        "TERMINAL", "TERMINAL", "TERMINAL", "TRANSIENT", "TRANSIENT", "TRANSIENT",
        "TRANSIENT", "CONTRACT", "TRANSIENT",
    ]
    assert [rp.classify_failure(e).name for e in classify_type_inputs()] == [
        "THROTTLE", "CONTRACT", "CONTRACT", "TRANSIENT", "TRANSIENT",
        "TRANSIENT", "TERMINAL", "TERMINAL", "CONTRACT", "CONTRACT",
    ]
    assert [rp.classify_failure(e).name for e in classify_marker_inputs()] == [
        "THROTTLE", "THROTTLE", "THROTTLE", "THROTTLE", "TRANSIENT",
        "TRANSIENT", "TRANSIENT", "TERMINAL", "TERMINAL", "TRANSIENT",
        "TRANSIENT", "THROTTLE",
    ]

    # ---- P5/P6: the schedule, the cap before the jitter, the draw count ---
    policy, clock, jitter = policy_with(jitter_value=0.25)
    assert (clock.calls, jitter.calls) == (0, 0), "neither injected callable may be called at construction"
    assert inspect.signature(rp.RetryPolicy.__init__).parameters["clock"].default is inspect.Parameter.empty
    assert inspect.signature(rp.RetryPolicy.__init__).parameters["jitter"].default is inspect.Parameter.empty

    assert policy.delay_for(rp.FailureClass.THROTTLE, 1) == 5.0
    assert policy.delay_for(rp.FailureClass.THROTTLE, 2) == 10.0
    assert policy.delay_for(rp.FailureClass.THROTTLE, 3) == 20.0
    assert policy.delay_for(rp.FailureClass.THROTTLE, 4) == 37.5
    assert policy.delay_for(rp.FailureClass.THROTTLE, 9) == 37.5, "the cap binds before the jitter"
    assert policy.delay_for(rp.FailureClass.TRANSIENT, 1) == 0.312
    assert policy.delay_for(rp.FailureClass.TRANSIENT, 2) == 0.938
    assert policy.delay_for(rp.FailureClass.TRANSIENT, 3) == 2.812
    assert policy.delay_for(rp.FailureClass.TRANSIENT, 4) == 8.438
    assert policy.delay_for(rp.FailureClass.TRANSIENT, 5) == 12.5
    assert policy.delay_for(rp.FailureClass.TRANSIENT, 20) == 12.5
    drawn_for_positive_delays = jitter.calls
    assert drawn_for_positive_delays == 11, f"one jitter draw per positive delay, got {drawn_for_positive_delays}"

    assert policy.delay_for(rp.FailureClass.CONTRACT, 1) == 0.0
    assert policy.delay_for(rp.FailureClass.TERMINAL, 3) == 0.0
    assert jitter.calls == drawn_for_positive_delays, "a zero delay must not consume the jitter source"
    assert clock.calls == 0, "delay_for has no business reading the clock"

    for value, expected in ((0.0, 4.0), (1.0, 8.0), (2.5, 8.0), (-1.0, 4.0)):
        clamped, _, _ = policy_with(jitter_value=value)
        assert clamped.delay_for(rp.FailureClass.THROTTLE, 1) == expected, f"jitter {value} should clamp to a {expected}s first throttle delay"

    with pytest.raises(ValueError):
        policy.delay_for(rp.FailureClass.THROTTLE, 0)

    # ---- P7: the verdict's shape, its routed counter and its reason code --
    verdict = decide(policy, Exception("rate limit"))
    assert dataclasses.is_dataclass(verdict), f"the verdict is a {type(verdict).__name__}, not the frozen dataclass the ticket asks for"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(verdict, dataclasses.fields(verdict)[0].name, None)

    assert v_retry(verdict) is True
    assert v_class(verdict) is rp.FailureClass.THROTTLE
    assert v_attempt(verdict) == 1
    assert counter_moved(policy, verdict) == "num_rate_limit_errors"
    assert v_reason(verdict) == "throttle:retry"

    assert counter_moved(policy, decide(policy, ValueError("bad"))) == "num_other_errors"
    assert v_reason(decide(policy, ValueError("bad"))) == "contract:retry"
    assert counter_moved(policy, decide(policy, TimeoutError("x"))) == "num_api_errors"
    assert v_reason(decide(policy, TimeoutError("x"))) == "transient:retry"
    terminal = decide(policy, Exception("invalid api key"), attempts_made=2)
    assert v_retry(terminal) is False
    assert counter_moved(policy, terminal) == "num_api_errors"
    assert v_reason(terminal) == "terminal:abort"
    assert v_attempt(terminal) == 3
    assert v_delay(terminal) == 0.0

    # ---- P9: exactly one counter moves per failure -----------------------
    policy, clock, jitter = policy_with(clock_value=1000.0, jitter_value=0.25)
    tracker = fake_tracker()
    record(policy, tracker, decide(policy, Exception("rate limit")))
    assert counters(tracker) == (1, 0, 0)
    record(policy, tracker, decide(policy, TimeoutError("x")))
    assert counters(tracker) == (1, 1, 0)
    record(policy, tracker, decide(policy, ValueError("bad")))
    assert counters(tracker) == (1, 1, 1)
    record(policy, tracker, decide(policy, Exception("invalid api key")))
    assert counters(tracker) == (1, 2, 1)

    # ---- P10: the summary and the shared attempt label -------------------
    C = rp.FailureClass
    log = [
        (C.TRANSIENT, "boom"),
        (C.THROTTLE, "rate limit"),
        (C.TRANSIENT, "boom"),
        (C.CONTRACT, "bad"),
        (C.THROTTLE, "rate limit"),
        (C.THROTTLE, "rate limit"),
    ]
    assert rp.format_failure_summary(log) == [
        "[throttle] rate limit (x3)",
        "[transient] boom (x2)",
        "[contract] bad (x1)",
    ]
    assert rp.format_failure_summary([(C.CONTRACT, "b"), (C.TRANSIENT, "a"), (C.TRANSIENT, "a")]) == [
        "[transient] a (x2)",
        "[contract] b (x1)",
    ]
    assert rp.format_failure_summary([(C.TRANSIENT, "a"), (C.CONTRACT, "a")]) == ["[transient] a (x1)", "[contract] a (x1)"]
    assert rp.format_failure_summary([]) == []

    assert rp.format_attempt_label(0, 10) == "attempt #1 of 11"
    assert rp.format_attempt_label(3, 3) == "attempt #4 of 4"
    assert rp.format_attempt_label(0, 0) == "attempt #1 of 1"

    # ---- the wiring: APIRequest's new fields, and the except block -------
    names = [f.name for f in dataclasses.fields(APIRequest)]
    assert "attempts_made" in names, f"APIRequest has {names}"
    assert "failure_log" in names, f"APIRequest has {names}"
    fresh = make_api_request()
    assert read_field(fresh, "attempts_made") == 0
    assert read_field(fresh, "failure_log") == []
    assert read_field(fresh, "attempts_left") == 3

    processor = make_processor(max_retries=3)
    built = [value for value in vars(processor).values() if isinstance(value, rp.RetryPolicy)]
    assert built, f"__init__ built no RetryPolicy; the processor carries {sorted(vars(processor))}"

    tracker = OnlineStatusTracker()
    request = make_api_request()
    queue = drive_one_failure(processor, request, tracker, Exception("API error: Rate limit reached for gpt-4o"))

    assert queue.qsize() == 1, "a rate-limited request with budget to spare was not re-queued"
    assert queue.get_nowait() is request
    assert read_field(request, "attempts_made") == 1
    assert read_field(request, "failure_log") == [(rp.FailureClass.THROTTLE, "API error: Rate limit reached for gpt-4o")]
    assert counters(tracker) == (1, 0, 0), f"a 429 must be counted once, as a rate limit: {counters(tracker)}"
