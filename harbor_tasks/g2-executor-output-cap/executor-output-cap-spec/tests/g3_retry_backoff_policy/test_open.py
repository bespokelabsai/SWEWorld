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
"""
from __future__ import annotations

import ast
import asyncio
import dataclasses
import inspect
import pathlib
from types import SimpleNamespace

import pytest

from harness import read_field

# Imported defensively, and re-raised inside each test rather than at collection
# time: a missing `retry_policy` module is one fact failing per requirement, not
# three files that pytest refuses to collect and a scoreboard with no rows on it.
IMPORT_ERROR = None
try:
    from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
    from bespokelabs.curator.request_processor.online import retry_policy as rp
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        APIRequest,
        BaseOnlineRequestProcessor,
        _TokenUsage,
    )
    from bespokelabs.curator.types.generic_request import GenericRequest
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    rp = OnlineRequestProcessorConfig = APIRequest = BaseOnlineRequestProcessor = None
    _TokenUsage = GenericRequest = None


def importable() -> None:
    """Fail one test, not the whole module, when the new policy module is absent."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"bespokelabs.curator.request_processor.online.retry_policy could not be imported: {IMPORT_ERROR!r}")


# ---------------------------------------------------------------------------
# Shared helpers, imported by test_r1.py and test_r2.py
# ---------------------------------------------------------------------------
def counting(value):
    """A jitter/clock source returning `value` and counting its own calls."""
    box = SimpleNamespace(calls=0)

    def source():
        box.calls += 1
        return value

    box.source = source
    return box


def policy_with(*, clock_value: float = 0.0, jitter_value: float = 0.25):
    """A `RetryPolicy` plus the call counters of the two sources injected into it."""
    clock = counting(clock_value)
    jitter = counting(jitter_value)
    return rp.RetryPolicy(clock=clock.source, jitter=jitter.source), clock, jitter


def decide(policy, exc, *, attempts_made=0, attempts_left=10, throttle_waivers_left=6):
    """`policy.decide(...)`, passing the waiver budget only if it is accepted.

    The waiver keyword is r1's hidden fact; this file must still be able to ask
    for a verdict from an implementation that only built the open feature.
    """
    kwargs = {"attempts_made": attempts_made, "attempts_left": attempts_left}
    params = inspect.signature(policy.decide).parameters
    takes_waivers = "throttle_waivers_left" in params or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    if takes_waivers:
        kwargs["throttle_waivers_left"] = throttle_waivers_left
    return policy.decide(exc, **kwargs)


# ---------------------------------------------------------------------------
# Reading a verdict without assuming what its fields are called
#
# The ticket describes the verdict semantically -- "whether to re-queue, which
# FailureClass it was, the 1-based index of the attempt that just failed, how
# long to wait, and a two-part reason code" -- and never spells a field name or
# the class's own name. Only `reason_code`'s VALUE grammar is fixed. So each
# reader below offers the plausible spellings and `read_field` takes the first
# that exists; the two names r1 fixes (`throttle_waivers_left`,
# `DEFAULT_THROTTLE_WAIVERS`) are required verbatim, but only in test_r1.py.
# ---------------------------------------------------------------------------
def v_retry(verdict):
    return read_field(verdict, "should_retry", "retry", "should_requeue", "requeue")


def v_class(verdict):
    return read_field(verdict, "failure_class", "failure", "klass")


def v_attempt(verdict):
    return read_field(verdict, "attempt_index", "attempt", "attempt_number", "attempt_no")


_DELAY_NAMES = ("delay_seconds", "delay", "delay_s", "wait_seconds", "backoff_seconds")


def v_delay(verdict):
    return read_field(verdict, *_DELAY_NAMES)


def delay_field_name(verdict) -> str:
    """Whatever the verdict calls its delay, for `dataclasses.replace`."""
    for name in _DELAY_NAMES:
        if hasattr(verdict, name):
            return name
    raise AssertionError(f"the verdict carries no delay under any of {_DELAY_NAMES}")


def v_budget(verdict):
    return read_field(verdict, "attempts_left_after", "attempts_left", "attempts_remaining")


def v_waivers(verdict):
    # Five spellings, because the requirement fixes the NAME and the grader must
    # not also fix the suffix: an implementation that read "the post-failure
    # waiver count" and wrote `throttle_waivers_left_after` has satisfied it.
    return read_field(verdict, "throttle_waivers_after", "throttle_waivers_left_after",
                      "waivers_left_after", "throttle_waivers_left", "waivers_left",
                      "waivers_after")


def counter_moved(policy, verdict):
    """Which tracker counter this verdict actually increments.

    The requirement fixes that recording a verdict moves exactly one counter --
    it never says the verdict must EXPOSE the counter's name. An earlier version
    read a `tracker_field` attribute off the verdict and failed every r1 fact
    against an implementation that routed the counter inside the recorder, which
    is the reading the requirement actually licenses.
    """
    counters = ("num_rate_limit_errors", "num_api_errors", "num_other_errors")
    tracker = fake_tracker()
    record(policy, tracker, verdict)
    moved = [c for c in counters if getattr(tracker, c, 0)]
    assert len(moved) == 1, f"exactly one counter must move per failure; {moved} did"
    return moved[0]


def v_reason(verdict):
    return read_field(verdict, "reason_code", "reason")


_RECORDERS = ("apply_to_tracker", "apply_verdict", "record_verdict", "update_tracker", "record", "apply")


def _invoke_recorder(fn, tracker, verdict):
    """Call a recorder whichever way round it takes its two arguments.

    The requirement says the policy records a verdict on a tracker. It does not
    fix the PARAMETER ORDER, and both readings are natural -- the reference
    implementation happens to take `(tracker, verdict)`, and a build given the
    requirement alone wrote `(verdict, tracker)` and failed three r2 facts on
    `AttributeError: 'SimpleNamespace' object has no attribute 'failure_class'`.
    Grading argument order the requirement never states is the same error as
    grading a field spelling it never states.

    Read off the signature where the names say which is which, and tried both
    ways where they do not.
    """
    try:
        first = list(inspect.signature(fn).parameters)[0].lower()
    except (TypeError, ValueError):
        first = ""
    order = ((verdict, tracker), (tracker, verdict)) if "verdict" in first \
        else ((tracker, verdict), (verdict, tracker))
    try:
        return fn(*order[0])
    except (AttributeError, TypeError):
        return fn(*order[1])


def record(policy, tracker, verdict):
    """Call the policy's "write this verdict onto the tracker" method.

    The ticket says the policy has such a method but does not name it, so the
    plausible spellings are tried in turn before falling back to the only
    public two-argument method the policy exposes.
    """
    for name in _RECORDERS:
        fn = getattr(policy, name, None)
        if callable(fn):
            return _invoke_recorder(fn, tracker, verdict)
    candidates = []
    for name in dir(policy):
        if name.startswith("_") or name in ("decide", "delay_for"):
            continue
        fn = getattr(policy, name)
        if callable(fn) and len(inspect.signature(fn).parameters) == 2:
            candidates.append(fn)
    if len(candidates) == 1:
        return _invoke_recorder(candidates[0], tracker, verdict)
    pytest.fail(f"the policy has no method that records a verdict on a tracker; it exposes {sorted(n for n in dir(policy) if not n.startswith('_'))}")


def fake_tracker(**overrides):
    """A stand-in tracker with every field the policy is allowed to write."""
    fields = {
        "num_api_errors": 0,
        "num_other_errors": 0,
        "num_rate_limit_errors": 0,
        "time_of_last_rate_limit_error": 0.0,
        "throttle_cooldown_until": 0.0,
        "last_update_time": 0.0,
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def counters(tracker):
    return (
        read_field(tracker, "num_rate_limit_errors"),
        read_field(tracker, "num_api_errors"),
        read_field(tracker, "num_other_errors"),
    )


def make_processor(**config_kwargs):
    """The smallest concrete `BaseOnlineRequestProcessor` the abstract base allows."""

    class _Processor(BaseOnlineRequestProcessor):
        def file_upload_limit_check(self, base64_image):
            return None

        def estimate_total_tokens(self, messages):
            return _TokenUsage()

        def estimate_output_tokens(self):
            return 0

        def create_api_specific_request_online(self, generic_request):
            return {}

        async def call_single_request(self, request, session, status_tracker):
            raise AssertionError("the tests install their own call_single_request")

    config_kwargs.setdefault("model", "gpt-4o-mini")
    return _Processor(OnlineRequestProcessorConfig(**config_kwargs))


def make_api_request(**overrides):
    generic = GenericRequest(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}], original_row={}, original_row_idx=0)
    kwargs = {
        "task_id": 7,
        "generic_request": generic,
        "api_specific_request": {},
        "attempts_left": 3,
    }
    kwargs.update(overrides)
    return APIRequest(**kwargs)


def drive_one_failure(processor, request, tracker, exc):
    """Run the processor's own try/except once over an attempt that raises."""

    async def boom(request, session, status_tracker):
        raise exc

    processor.call_single_request = boom
    queue = asyncio.Queue()

    async def go():
        await processor.handle_single_request_with_retries(
            request=request,
            session=None,
            retry_queue=queue,
            response_file="/dev/null",
            status_tracker=tracker,
            blocked_capacity=_TokenUsage(),
        )

    asyncio.run(go())
    return queue


E = type("E", (Exception,), {})


def with_status(message, **attrs):
    exc = E(message)
    for name, value in attrs.items():
        setattr(exc, name, value)
    return exc


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
    assert rp.classify_failure(with_status("rate limit exceeded", status_code=503)) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(with_status("rate limit exceeded", status=429)) is rp.FailureClass.THROTTLE
    assert rp.classify_failure(with_status("overloaded", status_code=529)) is rp.FailureClass.THROTTLE
    assert rp.classify_failure(with_status("bad request", status_code=422)) is rp.FailureClass.CONTRACT
    assert rp.classify_failure(with_status("bad request", status_code=413)) is rp.FailureClass.CONTRACT
    assert rp.classify_failure(with_status("bad request", status_code=400)) is rp.FailureClass.CONTRACT
    assert rp.classify_failure(with_status("nope", status_code=404)) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(with_status("nope", status_code=401)) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(with_status("nope", status_code=403)) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(with_status("wait", status_code=408)) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(with_status("wait", status_code=409)) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(with_status("wait", status_code=425)) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(with_status("boom", status_code=599)) is rp.FailureClass.TRANSIENT
    # an int that is neither a key nor 5xx falls THROUGH to the type signal
    unrecognised = ValueError("nope")
    unrecognised.status_code = 418
    assert rp.classify_failure(unrecognised) is rp.FailureClass.CONTRACT
    # and a status that is not an int is ignored entirely
    assert rp.classify_failure(with_status("boom", status_code="429")) is rp.FailureClass.TRANSIENT

    # ---- P3: the type signal walks the MRO, by name ----------------------
    outranked = ValueError("rate limit exceeded")
    outranked.status_code = 429
    assert rp.classify_failure(outranked) is rp.FailureClass.THROTTLE, "status must outrank type"
    assert rp.classify_failure(ValueError("finish_reason was length")) is rp.FailureClass.CONTRACT
    assert rp.classify_failure(KeyError("choices")) is rp.FailureClass.CONTRACT
    assert rp.classify_failure(TimeoutError("boom")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(asyncio.TimeoutError()) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(ConnectionError("reset")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(PermissionError("no")) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(NotImplementedError("no")) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(type("SchemaError", (ValueError,), {})("x")) is rp.FailureClass.CONTRACT
    assert rp.classify_failure(ValueError("rate limit exceeded")) is rp.FailureClass.CONTRACT, "type must outrank the message"

    # ---- P4: marker order beats message position; the default is TRANSIENT
    assert rp.classify_failure(Exception("Authentication failed: too many requests")) is rp.FailureClass.THROTTLE
    assert rp.classify_failure(Exception("Quota exceeded for project")) is rp.FailureClass.THROTTLE
    assert rp.classify_failure(Exception("RateLimitError")) is rp.FailureClass.THROTTLE
    assert rp.classify_failure(Exception("Model is overloaded")) is rp.FailureClass.THROTTLE
    assert rp.classify_failure(Exception("Response is empty")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(Exception("connection reset by peer")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(Exception("service temporarily unavailable")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(Exception("Invalid API key provided")) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(Exception("permission denied")) is rp.FailureClass.TERMINAL
    assert rp.classify_failure(Exception("API error: internal server error")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(Exception("")) is rp.FailureClass.TRANSIENT
    assert rp.classify_failure(Exception("rate limit exceeded")) is rp.FailureClass.THROTTLE

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

    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker

    tracker = OnlineStatusTracker()
    request = make_api_request()
    queue = drive_one_failure(processor, request, tracker, Exception("API error: Rate limit reached for gpt-4o"))

    assert queue.qsize() == 1, "a rate-limited request with budget to spare was not re-queued"
    assert queue.get_nowait() is request
    assert read_field(request, "attempts_made") == 1
    assert read_field(request, "failure_log") == [(rp.FailureClass.THROTTLE, "API error: Rate limit reached for gpt-4o")]
    assert counters(tracker) == (1, 0, 0), f"a 429 must be counted once, as a rate limit: {counters(tracker)}"
