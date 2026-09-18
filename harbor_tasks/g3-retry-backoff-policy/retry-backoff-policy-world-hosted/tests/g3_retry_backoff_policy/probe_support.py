"""g3 — answer-free scenario helpers and inputs shared by the worker (probe.py)
and the human reference (test_open.py, which lives with the suite's source and is
not shipped in the task).

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
import datetime
import inspect
import os
import tempfile
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
    from bespokelabs.curator.request_processor.online import base_online_request_processor as base_module
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        APIRequest,
        BaseOnlineRequestProcessor,
        _TokenUsage,
    )
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
    from bespokelabs.curator.types.generic_request import GenericRequest
    from bespokelabs.curator.types.generic_response import GenericResponse
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    rp = OnlineRequestProcessorConfig = APIRequest = BaseOnlineRequestProcessor = base_module = None
    _TokenUsage = GenericRequest = GenericResponse = OnlineStatusTracker = None


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


def drive_one_failure(processor, request, tracker, exc, *, capture=None):
    """Run the processor's own try/except once over an attempt that raises.

    `capture`, when a list is passed, collects whatever the processor writes out
    for a request it has given up on, by standing in for
    `append_generic_response`. The stand-in is not optional on that path: the
    real write wants a prompt formatter and a viewer this bare processor has
    neither of (same reason `drive_one_response` installs one), so without it
    the exhausted path dies on an AttributeError and reports nothing about the
    response the ticket describes.
    """

    async def boom(request, session, status_tracker):
        raise exc

    processor.call_single_request = boom
    if capture is not None:

        async def keep(status_tracker, response, filename):
            capture.append(response)

        processor.append_generic_response = keep
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


class _StopAtConstruction(BaseException):
    """Raised from the APIRequest spy below, out through the submission loop.

    A `BaseException`, not an `Exception`: the retry path this travels through is
    wrapped in `except Exception` handlers that would swallow it and turn the
    observation into a silent nothing.
    """


def production_seeding(max_retries: int) -> dict:
    """What the processor's OWN submission loop seeds `attempts_left` from.

    Every other request in this suite is built by `make_api_request`, which
    passes `attempts_left=3` itself -- so nothing behavioural ever touched the
    construction site in `process_requests_from_file`, and the v12 review said
    exactly that: a pristine `attempts_left=self.config.max_retries` parked in
    dead code satisfied the source check while the request that really gets made
    was seeded from something else.

    So drive the real loop over a one-line request file with the module's
    `APIRequest` replaced by a spy that records the keyword it was called with
    and raises. Stopping at the construction is what keeps this offline and
    quick: the capacity wait and the retry-drain loop that follow never run, and
    a live run of them does not terminate without a server. The viewer client
    and prompt formatter are stubbed because a bare processor has neither and
    the loop reaches for both before it builds a request.

    Answer-free: `max_retries` is an INPUT the caller passes. The value it must
    come back as is the same number, and it is the judge that knows it.
    """
    out = {"observed": False, "attempts_left": None, "error": None}
    real = None
    try:
        real = base_module.APIRequest
        processor = make_processor(max_retries=max_retries)

        class _Viewer:
            def __getattr__(self, name):
                async def _noop(*args, **kwargs):
                    return None

                return _noop

        processor._viewer_client = _Viewer()
        processor.prompt_formatter = None
        seen = []

        def spy(*args, **kwargs):
            seen.append(kwargs["attempts_left"] if "attempts_left" in kwargs else "<positional>")
            raise _StopAtConstruction()

        base_module.APIRequest = spy
        work = tempfile.mkdtemp()
        request_file = os.path.join(work, "requests.jsonl")
        generic = GenericRequest(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}], original_row={}, original_row_idx=0)
        with open(request_file, "w", encoding="utf-8") as handle:
            handle.write(generic.model_dump_json() + "\n")

        async def go():
            await processor.process_requests_from_file(request_file, os.path.join(work, "responses.jsonl"), OnlineStatusTracker())

        try:
            asyncio.run(go())
        except _StopAtConstruction:
            pass
        if seen:
            out["observed"] = True
            out["attempts_left"] = seen[0]
        else:
            out["error"] = "the submission loop ran without constructing an APIRequest"
    except BaseException as exc:  # noqa: BLE001 - an unobservable path is a failed fact, reported as one
        out["error"] = f"{type(exc).__name__}: {exc}"[:300]
    finally:
        if real is not None:
            base_module.APIRequest = real
    return out


def drive_one_response(processor, request, tracker, *, finish_reason):
    """Run the processor's own request path once over a response that came back.

    `drive_one_failure` hands the except block an exception it made up; this hands
    the try block a response, so curator's own `invalid_finish_reasons` check does
    the raising and whatever the submission did at that call site is exercised.
    """

    async def answer(request, session, status_tracker):
        now = datetime.datetime.now()
        return GenericResponse(
            response_message=None,
            raw_response={},
            raw_request={},
            generic_request=request.generic_request,
            created_at=now,
            finished_at=now,
            finish_reason=finish_reason,
        )

    # A request the policy gives up on is written out through `append_generic_response`,
    # which wants a prompt formatter and a viewer this bare processor has neither of.
    # Without this a wrong verdict dies on an AttributeError instead of reporting
    # the queue and budget the judge checks.
    async def give_up(status_tracker, response, filename):
        return None

    processor.call_single_request = answer
    processor.append_generic_response = give_up
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


# ---------------------------------------------------------------------------
# Driving one provider processor's rate-limit branch
# ---------------------------------------------------------------------------
# instruction.md:120-126 has two halves: the three hand-rolled blocks stop
# mutating tracker counters, and they "just re-raise". A source read answers the
# first half; the second is a behaviour, and a handler that returns instead of
# raising — or that replaces the provider's exception with one of its own —
# deleted the decrements the ticket names, passed every check, and quietly
# dropped the failure the base class exists to classify.
#
# A provider processor cannot be constructed here: its __init__ wants an API key,
# a client and, for litellm, a model lookup. So the handler is entered directly
# with a stand-in `self` carrying the two or three attributes it reads on the way
# to the rate-limit branch, and with the one call that would reach the network
# replaced. Nothing in here says what the handler must do: the judge holds that.
PROVIDER_ERROR = {"message": "Rate limit reached for gpt-4o"}


class _StandIn:
    """A `self` for one handler: what the scenario sets, `None` for the rest."""

    def __init__(self, **attrs):
        self.__dict__.update(attrs)

    def __getattr__(self, name):
        return None


def _rate_limit_error(litellm_module):
    """The provider's OWN rate-limit exception, so the module's `except
    litellm.RateLimitError` catches it however that clause is spelled.

    Constructed through the real signature, because a handler is free to log
    `str(e)` before it re-raises and litellm's own `__str__` reads attributes
    only its `__init__` sets: a bare subclass raised an AttributeError there and
    would have failed a correct handler for it.
    """
    error_cls = litellm_module.RateLimitError
    try:
        return error_cls(message="rate limit exceeded", llm_provider="openai", model="gpt-4o-mini")
    except Exception:  # noqa: BLE001 - a litellm whose constructor wants something else
        class _Throttled(error_cls):
            def __init__(self):
                Exception.__init__(self, "rate limit exceeded")

            def __str__(self):
                return "rate limit exceeded"

        return _Throttled()


def _propagated(coro) -> dict:
    """Run one handler and report what came out, rather than raising it here."""
    try:
        asyncio.run(coro)
        return {"raised": [], "exc": None}
    except BaseException as exc:  # noqa: BLE001 - the propagation under test
        return {"raised": [cls.__name__ for cls in type(exc).__mro__], "exc": exc}


def drive_provider_rate_limit(which: str) -> dict:
    """One provider's rate-limit failure, driven through the real handler.

    Records whether the branch could be entered at all, the MRO of whatever
    propagated out of it, whether that object is the exception raised underneath
    it (litellm's block is the one that catches the provider's own error, so
    `raise e` is observable there as identity), and the tracker's three counters
    before and after. A branch that could not be entered is reported as
    `driven: False` with the error, never as a pass.
    """
    out = {"driven": False, "raised": None, "same_object": None,
           "counters_before": None, "counters_after": None, "error": None}
    try:
        tracker = OnlineStatusTracker()
        request = make_api_request()
        out["counters_before"] = list(counters(tracker))
        if which == "openai":
            from bespokelabs.curator.request_processor.online import openai_online_request_processor as mod

            async def fetch(session, **kwargs):
                return {"error": dict(PROVIDER_ERROR)}

            real, mod.fetch_response = mod.fetch_response, fetch
            try:
                result = _propagated(mod.OpenAIOnlineRequestProcessor.call_single_request(
                    _StandIn(api_key="sk-verifier",
                             url="https://api.openai.com/v1/chat/completions",
                             config=_StandIn(request_timeout=1, return_completions_object=False)),
                    request, None, tracker))
            finally:
                mod.fetch_response = real
        elif which == "anthropic":
            from bespokelabs.curator.request_processor.online import anthropic_online_request_processor as mod

            class _Response:
                status = 429

                async def json(self):
                    return {"error": dict(PROVIDER_ERROR)}

            class _Post:
                async def __aenter__(self):
                    return _Response()

                async def __aexit__(self, *exc_info):
                    return False

            class _Session:
                def post(self, *args, **kwargs):
                    return _Post()

            result = _propagated(mod.AnthropicOnlineRequestProcessor.call_single_request(
                _StandIn(api_key="sk-verifier", url="https://api.anthropic.com/v1/messages",
                         config=_StandIn(request_timeout=1, return_completions_object=False)),
                request, _Session(), tracker))
        elif which == "litellm":
            from bespokelabs.curator.request_processor.online import litellm_online_request_processor as mod

            real = mod.litellm
            thrown = _rate_limit_error(real)

            class _Litellm:
                """The real module, with the one network call raising."""

                def __getattr__(self, name):
                    return getattr(real, name)

                async def acompletion(self, **kwargs):
                    raise thrown

            mod.litellm = _Litellm()
            try:
                result = _propagated(mod.LiteLLMOnlineRequestProcessor.call_single_request(
                    _StandIn(config=_StandIn(request_timeout=1, return_completions_object=False)),
                    request, None, tracker))
                out["same_object"] = result["exc"] is thrown
            finally:
                mod.litellm = real
        else:
            raise AssertionError(f"no such provider: {which!r}")
        out["raised"] = result["raised"]
        out["counters_after"] = list(counters(tracker))
        out["driven"] = True
    except BaseException as exc:  # noqa: BLE001 - an unobservable path is a failed fact, reported as one
        out["error"] = f"{type(exc).__name__}: {exc}"[:300]
    return out


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
        # The TRANSIENT marker row, on its own terms. Every other timeout input
        # in this suite is a TimeoutError, which the type signal answers first,
        # so the `timed out` marker was never the thing being read -- and with
        # TRANSIENT also being the default, a message carrying it alone proves
        # nothing either. This one carries a TERMINAL marker too, so only a
        # scan in the ticket's table order (transient row before terminal,
        # instruction.md:47-54) rather than in message order comes back
        # TRANSIENT.
        Exception("Invalid API key rejected after the request timed out"),
    ]


def classify_hostile_inputs():
    """The "never raises" guarantee: exceptions that fight back when read.

    `getattr(exc, "status_code", None)` returns its default only on
    AttributeError, so a property that raises anything else propagates straight
    out of the classifier — and `str(exc)` is a method call too. Real clients
    raise this shape: an SDK error whose `.status_code` parses a half-read
    response, or whose `__str__` formats a body that never arrived. The ticket
    states "never raises" outright and nothing measured it, so a classifier
    that reads both accessors unguarded scored full marks on the fact.

    Answer-free like its neighbours — what each input DOES is the input; the
    expected classes live in test_open.py and judge.py. Between them the five
    also separate "guarded" from "wrapped in one try that returns the default":
    three of them must still come back with the class a working signal found —
    the message's 429, the status's 429, and the one whose accessors both raise
    but whose TYPE still names a class.
    """

    class StatusExplodes(Exception):
        """No readable status, a readable message, no marker in it."""

        @property
        def status_code(self):
            raise RuntimeError("status accessor is broken")

    class ThrottledStatusExplodes(StatusExplodes):
        """The status is unreadable but the message still says 429."""

        def __str__(self):
            return "Rate limit exceeded for gpt-4o"

    class MessageExplodes(Exception):
        """A readable status, an unreadable message: signal 1 answers first."""

        status_code = 429

        def __str__(self):
            raise RuntimeError("message accessor is broken")

    class BothExplode(PermissionError):
        """Neither accessor works; the TYPE still names a class."""

        @property
        def status(self):
            raise RuntimeError("status accessor is broken")

        def __str__(self):
            raise RuntimeError("message accessor is broken")

    class NothingWorks(Exception):
        """Nothing readable and nothing to match: the default still comes back."""

        @property
        def status_code(self):
            raise RuntimeError("status accessor is broken")

        def __str__(self):
            raise RuntimeError("message accessor is broken")

    return [StatusExplodes("boom"), ThrottledStatusExplodes("boom"),
            MessageExplodes("x"), BothExplode("no"), NothingWorks("x")]
