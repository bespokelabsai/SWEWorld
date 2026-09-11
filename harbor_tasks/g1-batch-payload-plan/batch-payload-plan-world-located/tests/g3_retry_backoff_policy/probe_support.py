"""g3 — answer-free scenario helpers and inputs shared by the worker (probe.py)
and the human reference (test_open.py).

This module holds ONLY the curator imports, the tolerant verdict/tracker readers,
the policy/processor/request factories, and the classification INPUTS the probe
feeds to `classify_failure`. It contains NO expected-output value: not the 0/1/2
retry costs, not `DEFAULT_THROTTLE_WAIVERS = 6`, not the delay schedule numbers
(5.0 / 37.5 / 0.312 …), not the budget/waiver or horizon tables, not a reason
code. That is load-bearing: `run_split` copies this file into the worker's jail,
so it is inside the process that runs agent code — if any reward-bearing expected
value ever appears here, a hostile submission that read it could forge a passing
`observations.json`. The answers live only in `judge.py` (and, for humans, in
`test_open.py`), which the worker cannot read.

`test_open.py` imports these names so there is a single definition of each helper
and each input list — the probe cannot drift from the reference.

The identifiers the requirements FIX (`throttle_waivers_left`, the counter names,
`throttle_cooldown_until`, `remaining_cooldown_seconds`) do appear here: they are
read-keys the probe needs to observe a value, not expected outputs. A submission
that reads them at grading time is already frozen and still has to match numbers
it cannot see. The tolerant readers below deliberately try several spellings
where the requirement fixes only the meaning, exactly as the reference did.
"""
from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace

import pytest
from harness import read_field

# Imported defensively: a missing `retry_policy` module is one fact failing per
# requirement, not three files that refuse to collect. The probe reports the
# resulting error per node; `importable()` is the reference's per-test guard.
IMPORT_ERROR = None
try:
    from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
    from bespokelabs.curator.request_processor.online import retry_policy as rp
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        APIRequest,
        BaseOnlineRequestProcessor,
        _TokenUsage,
    )
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
    from bespokelabs.curator.types.generic_request import GenericRequest
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    rp = OnlineRequestProcessorConfig = APIRequest = BaseOnlineRequestProcessor = None
    _TokenUsage = GenericRequest = OnlineStatusTracker = None


def importable() -> None:
    """Fail one test, not the whole module, when the new policy module is absent."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"bespokelabs.curator.request_processor.online.retry_policy could not be imported: {IMPORT_ERROR!r}")


# ---------------------------------------------------------------------------
# Injected clock / jitter sources
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

    The waiver keyword is r1's hidden fact; the reference must still be able to
    ask for a verdict from an implementation that only built the open feature.
    """
    kwargs = {"attempts_made": attempts_made, "attempts_left": attempts_left}
    params = inspect.signature(policy.decide).parameters
    takes_waivers = "throttle_waivers_left" in params or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    if takes_waivers:
        kwargs["throttle_waivers_left"] = throttle_waivers_left
    return policy.decide(exc, **kwargs)


# ---------------------------------------------------------------------------
# Reading a verdict without assuming what its fields are called
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
    counters_names = ("num_rate_limit_errors", "num_api_errors", "num_other_errors")
    tracker = fake_tracker()
    record(policy, tracker, verdict)
    moved = [c for c in counters_names if getattr(tracker, c, 0)]
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


# ---------------------------------------------------------------------------
# The classification INPUTS (answer-free): the exceptions `classify_failure`
# is asked about. The EXPECTED classes live in test_open.py and judge.py.
# ---------------------------------------------------------------------------
def classify_status_inputs():
    """P2: the status signal comes first; a non-int or unrecognised int falls through."""
    unrecognised = ValueError("nope")
    unrecognised.status_code = 418
    return [
        with_status("rate limit exceeded", status_code=503),
        with_status("rate limit exceeded", status=429),
        with_status("overloaded", status_code=529),
        with_status("bad request", status_code=422),
        with_status("bad request", status_code=413),
        with_status("bad request", status_code=400),
        with_status("nope", status_code=404),
        with_status("nope", status_code=401),
        with_status("nope", status_code=403),
        with_status("wait", status_code=408),
        with_status("wait", status_code=409),
        with_status("wait", status_code=425),
        with_status("boom", status_code=599),
        unrecognised,
        with_status("boom", status_code="429"),
    ]


def classify_type_inputs():
    """P3: the type signal walks the MRO by name and outranks the message."""
    outranked = ValueError("rate limit exceeded")
    outranked.status_code = 429
    return [
        outranked,
        ValueError("finish_reason was length"),
        KeyError("choices"),
        TimeoutError("boom"),
        asyncio.TimeoutError(),
        ConnectionError("reset"),
        PermissionError("no"),
        NotImplementedError("no"),
        type("SchemaError", (ValueError,), {})("x"),
        ValueError("rate limit exceeded"),
    ]


def classify_marker_inputs():
    """P4: marker order beats message position; the default is TRANSIENT."""
    return [
        Exception("Authentication failed: too many requests"),
        Exception("Quota exceeded for project"),
        Exception("RateLimitError"),
        Exception("Model is overloaded"),
        Exception("Response is empty"),
        Exception("connection reset by peer"),
        Exception("service temporarily unavailable"),
        Exception("Invalid API key provided"),
        Exception("permission denied"),
        Exception("API error: internal server error"),
        Exception(""),
        Exception("rate limit exceeded"),
    ]
