"""g3 — the openly stated feature: a failure-class retry policy module, wired in.

Everything asserted here is spelled out in the ticket: the four `FailureClass`
members and their order, the four-signal precedence of `classify_failure`, the
status / type / marker tables, the `delay_for` schedule with the cap applied
before a half-jitter that is drawn exactly once per positive delay, the eight
`RetryVerdict` fields with their `class:outcome` reason code and routed tracker
counter name, `apply_to_tracker` moving exactly one counter, the
`[class] message (xN)` summary and its `attempt #N of M` label, the two new
`APIRequest` fields, the module's standard-library-only import list, the
guarantee that classification never raises however the exception reads back, and
the fact that the base processor builds a policy and its `except Exception` block
delegates to it — both branches of it, the re-queue and the written-out
`GenericResponse` — while the three provider processors stop counting and still
re-raise what they saw.

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
import importlib
import inspect
import pathlib
import sys

import pytest

from harness import read_field  # noqa: F401 - used in the wiring section below

# The answer-free helpers and classification inputs live in probe_support so the
# worker (probe.py) and this human reference share ONE definition. The expected
# VALUES this test asserts stay here (and in judge.py); probe_support holds none.
# Re-exported here so test_r1.py / test_r2.py keep `from test_open import ...`.
from probe_support import (  # noqa: F401
    APIRequest,
    OnlineStatusTracker,
    base_module,
    classify_hostile_inputs,
    classify_marker_inputs,
    classify_status_inputs,
    classify_type_inputs,
    counter_moved,
    counters,
    decide,
    delay_field_name,
    drive_one_failure,
    drive_one_response,
    drive_provider_rate_limit,
    fake_tracker,
    importable,
    make_api_request,
    make_processor,
    policy_with,
    production_seeding,
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
    # "Pure, standard-library only" is the other half of the same sentence, so
    # the list is an ALLOWLIST: every module named is this interpreter's standard
    # library or the project itself (a relative import is the project by
    # construction and is not collected above). Rejecting only the three named
    # modules let `import requests` through -- a third-party dependency in the
    # file the ticket calls pure.
    outside = sorted(imported - set(sys.stdlib_module_names) - {"bespokelabs"})
    assert not outside, f"retry_policy.py imports {outside}, which is neither the standard library nor this project"
    # A dynamic import is failed, not allowed: `importlib.import_module("time")`
    # satisfies the list above while doing what the ticket forbids, and a check
    # that cannot read what a call imports must not report that it imports
    # nothing.
    dynamic = [
        node.lineno for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and (getattr(node.func, "id", None) == "__import__" or getattr(node.func, "attr", None) == "import_module")
    ]
    assert not dynamic and "importlib" not in imported, f"retry_policy.py imports dynamically (lines {dynamic}), so what it reaches for cannot be read"

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
        "TRANSIENT", "THROTTLE", "TRANSIENT",
    ]

    # ---- the guarantee over all three signals: it never raises -----------
    # Rows 2, 3 and 4 are the ones a blanket `try: ... except: return TRANSIENT`
    # fails: an unreadable status must not cost the message signal its answer,
    # an unreadable message must not cost a readable 429 its own, and with both
    # accessors broken the exception's TYPE still names a class.
    assert [rp.classify_failure(e).name for e in classify_hostile_inputs()] == [
        "TRANSIENT", "THROTTLE", "THROTTLE", "TERMINAL", "TRANSIENT",
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

    # instruction.md:117-118: the retry-loop debug line uses the helper too, "so
    # both log sites agree on the attempt number". Only the helper's output was
    # ever graded, so line 424's own `max_retries - attempts_left` arithmetic --
    # which this change makes wrong -- could survive. Structural, not by line
    # number: a call to the helper must sit outside every except handler, and
    # the old subtraction must be gone.
    #
    # `judge.py` is the enforcing copy and asks for more than the two asserts
    # below can: the call has to be in LIVE code (`_live_label_calls`), because
    # `if False:`, a `def` nothing reaches, a duplicate `def` and a class-body
    # constant all satisfy "appears in the file" while the two log sites still
    # disagree.
    base_src = pathlib.Path(inspect.getfile(base_module)).read_text(encoding="utf-8")
    base_tree = ast.parse(base_src)

    def _label_calls(node):
        return [c for c in ast.walk(node) if isinstance(c, ast.Call)
                and (getattr(c.func, "id", None) == "format_attempt_label"
                     or getattr(c.func, "attr", None) == "format_attempt_label")]

    in_handlers = {id(c) for n in ast.walk(base_tree) if isinstance(n, ast.ExceptHandler)
                   for c in _label_calls(n)}
    assert [c.lineno for c in _label_calls(base_tree) if id(c) not in in_handlers], \
        "the retry-loop log line does not use format_attempt_label, so the two log sites disagree"

    stale = [n.lineno for n in ast.walk(base_tree)
             if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub)
             and sorted(s.attr for s in (n.left, n.right) if isinstance(s, ast.Attribute))
             == ["attempts_left", "max_retries"]]
    assert not stale, \
        f"max_retries - attempts_left still computes an attempt number at {stale}"

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

    # The give-up branch of the same except block: the response a request that
    # will not be retried is written out with, and its formatted errors.
    written = []
    dead = make_api_request(attempts_left=3)
    drive_one_failure(make_processor(max_retries=3), dead, OnlineStatusTracker(),
                      Exception("invalid api key"), capture=written)
    assert len(written) == 1, "a request the policy gave up on wrote no response"
    assert read_field(written[0], "response_errors") == ["[terminal] invalid api key (x1)"]
    assert read_field(written[0], "response_message") is None
    assert read_field(written[0], "raw_response") is None

    # Section 3: the provider processors stop counting. Read from the source,
    # because that is what sees a write on a path this suite does not drive --
    # every other behavioural check above runs against a stub subclass of the
    # BASE processor, so all three `num_api_errors -= 1` compensations could
    # survive unseen. The run of those same branches is below.
    for name in ("openai", "anthropic", "litellm"):
        module = importlib.import_module(
            f"bespokelabs.curator.request_processor.online.{name}_online_request_processor")
        provider = pathlib.Path(inspect.getfile(module)).read_text(encoding="utf-8")
        # Every write shape, not only the `-= 1` the pristine tree happens to
        # use: judge.py's `_counter_written_by` in test form. An AugAssign-only
        # scan let `x = x - 1`, a `setattr`, or a write through `__dict__` keep
        # the double count and the fact; matching the callee name `setattr`
        # alone then let `object.__setattr__(tracker, "num_api_errors", ...)`
        # do the same. Only these three files are parsed, and nothing follows a
        # call out of them -- see judge.py for why that gap is left open.
        counters_named = ("num_api_errors", "num_other_errors", "num_rate_limit_errors")
        mutated = []
        for node in ast.walk(ast.parse(provider)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            elif isinstance(node, ast.Delete):
                targets = list(node.targets)
            for target in targets:
                for inner in (target.elts if isinstance(target, (ast.Tuple, ast.List)) else [target]):
                    if isinstance(inner, ast.Attribute) and inner.attr in counters_named:
                        mutated.append(inner.attr)
                    if isinstance(inner, ast.Subscript) and isinstance(inner.slice, ast.Constant) and inner.slice.value in counters_named:
                        mutated.append(str(inner.slice.value))
            if isinstance(node, ast.Call):
                fn = node.func
                fname = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
                if fname in ("setattr", "delattr", "__setattr__", "__delattr__"):
                    # `object.__setattr__(obj, name, v)` names the attribute
                    # second like `setattr`; a bound `obj.__setattr__(name, v)`
                    # names it first, and arity is what tells them apart.
                    bound = fname.startswith("__") and isinstance(fn, ast.Attribute) and len(node.args) <= 2
                    index = 0 if bound else 1
                    if len(node.args) > index:
                        attr = node.args[index]
                        # A name the grader cannot read is failed, not allowed:
                        # it must not report "no counter written" about a write
                        # it could not see.
                        mutated.append(str(attr.value) if isinstance(attr, ast.Constant)
                                       else "<unreadable attribute write>")
                dict_recv = (isinstance(fn, ast.Attribute)
                             and ((isinstance(fn.value, ast.Attribute) and fn.value.attr == "__dict__")
                                  or (isinstance(fn.value, ast.Call)
                                      and getattr(fn.value.func, "id", None) == "vars")))
                if fname == "update" and dict_recv:
                    for keyword in node.keywords:
                        mutated.append(keyword.arg)
                    for arg in node.args:
                        if isinstance(arg, ast.Dict):
                            mutated.extend(str(k.value) for k in arg.keys if isinstance(k, ast.Constant))
                        else:
                            mutated.append("<unreadable attribute write>")
        assert not [m for m in mutated if m in counters_named or m == "<unreadable attribute write>"], \
            f"{name} still writes status_tracker.{mutated}; it must re-raise and let the base class count"

    # ... and the other half of that same sentence, which no source read
    # answers: the block "just re-raises". Each provider's rate-limit branch is
    # entered for real (with a stand-in `self` and the network call replaced), so
    # a handler that deletes the decrements and then returns instead of raising,
    # or that swaps the provider's exception for one of its own, is seen. Only
    # litellm's block catches the provider's own error, so identity -- `raise e`
    # giving back the same object -- is asked of it alone; openai's and
    # anthropic's build their own `Exception("API error: ...")` in the pristine
    # tree too.
    for name in ("openai", "anthropic", "litellm"):
        driven = drive_provider_rate_limit(name)
        assert driven["driven"], f"{name}'s rate-limit branch could not be driven: {driven['error']}"
        assert driven["raised"], f"{name}'s rate-limit branch returned instead of raising"
        assert driven["counters_after"] == driven["counters_before"], \
            f"{name}'s rate-limit branch moved a tracker counter: {driven['counters_before']} -> {driven['counters_after']}"
    assert drive_provider_rate_limit("litellm")["same_object"], \
        "litellm's rate-limit handler did not re-raise the exception it caught"
