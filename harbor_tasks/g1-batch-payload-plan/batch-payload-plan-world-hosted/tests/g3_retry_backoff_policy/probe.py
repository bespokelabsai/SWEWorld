"""g3 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
helpers (`policy_with`, `decide`, `record`, the tolerant `v_*` readers), so a
value here is the value the test saw. The judge holds the assertions those tests
made — the retry costs, the delay schedule, the budget/waiver and horizon tables
— and applies them to these values. A submission that returns forged values only
forges values the judge still checks against the real expectations, which is
implementing them. Floats go through `json` (float encoding is `repr`), so every
value round-trips to the identical double.

The two source-text checks — retry_policy's stdlib-only import list, and the
base processor's `attempts_left … max_retries` seeding / dead `seconds_to_pause`
knob — are NOT here. The judge reads those files itself under SUBMISSION_SRC
(parsing text executes nothing), which is both safe in the root process and a
more faithful check of the graded artifact than trusting this worker to report
its own source. See judge.py.
"""
from __future__ import annotations

import dataclasses
import inspect
import json
import os
import sys
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

# probe_support owns the curator imports, the scenario helpers and the
# classification inputs; reuse them so a probe calls curator exactly as the test
# does. Importing it runs the submission's `import bespokelabs.curator` — this
# process's whole purpose, and why it is disposable. probe_support carries the
# answer-free halves only (the worker never imports test_open, whose source
# carries the expected answer literals).
import probe_support as S  # noqa: E402
from harness import baseline_text  # noqa: E402

HORIZON = "throttle_cooldown_until"
# Heuristic scoping words for r2's "exactly one new pause field" diff. Answer-free:
# they say which added fields are ABOUT the pause, not which one is expected.
_PAUSE_WORDS = ("cooldown", "pause", "backoff", "horizon", "throttle_until", "retry_after")


def _cls(member):
    """A FailureClass member as its plain member name, for cross-process compare."""
    return getattr(member, "name", member)


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised and the exception's class chain.

    The judge cannot import the exception types, so it checks the raised type by
    the names in its MRO — the faithful stand-in for `pytest.raises(T)`.
    """
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        return {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__], "str": str(exc)}
    return {"raised": False, "mro": []}


def outcome(verdict):
    """The five numbers r1 expresses every fact in, read through the tolerant readers."""
    return [
        S.v_retry(verdict),
        S.v_budget(verdict),
        S.v_waivers(verdict),
        S.v_attempt(verdict),
        S.v_reason(verdict),
    ]


def waivers_are_implemented() -> bool:
    if any(f.name == "throttle_waivers_left" for f in dataclasses.fields(S.APIRequest)):
        return True
    params = inspect.signature(S.rp.RetryPolicy.decide).parameters
    return "throttle_waivers_left" in params or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())


def tracker_fields() -> list:
    return [f.name for f in dataclasses.fields(S.OnlineStatusTracker)]


def horizon_is_implemented() -> bool:
    return HORIZON in tracker_fields()


def throttle_verdict(policy, *, attempts_made=0):
    return S.decide(policy, Exception("rate limit"), attempts_made=attempts_made,
                    attempts_left=9, throttle_waivers_left=9)


# ---------------------------------------------------------------------------
# open feature — the whole stated surface (one fact)
# ---------------------------------------------------------------------------
def probe_open() -> dict:
    rp = S.rp
    C = rp.FailureClass
    o: dict = {}

    # ---- P1: the enum, its order, its str mixin --------------------------
    o["enum_names"] = [m.name for m in C]
    o["enum_values"] = [m.value for m in C]
    o["enum_len"] = len(C)
    o["contract_is_str"] = (C.CONTRACT == "contract")

    # ---- P2/P3/P4: classify_failure, over the shared inputs --------------
    o["classify_status"] = [_cls(rp.classify_failure(e)) for e in S.classify_status_inputs()]
    o["classify_type"] = [_cls(rp.classify_failure(e)) for e in S.classify_type_inputs()]
    o["classify_marker"] = [_cls(rp.classify_failure(e)) for e in S.classify_marker_inputs()]

    # ---- P5/P6: the schedule, the cap before the jitter, the draw count ---
    policy, clock, jitter = S.policy_with(jitter_value=0.25)
    o["construct_calls"] = [clock.calls, jitter.calls]
    o["clock_no_default"] = inspect.signature(rp.RetryPolicy.__init__).parameters["clock"].default is inspect.Parameter.empty
    o["jitter_no_default"] = inspect.signature(rp.RetryPolicy.__init__).parameters["jitter"].default is inspect.Parameter.empty

    o["delays"] = [
        policy.delay_for(C.THROTTLE, 1),
        policy.delay_for(C.THROTTLE, 2),
        policy.delay_for(C.THROTTLE, 3),
        policy.delay_for(C.THROTTLE, 4),
        policy.delay_for(C.THROTTLE, 9),
        policy.delay_for(C.TRANSIENT, 1),
        policy.delay_for(C.TRANSIENT, 2),
        policy.delay_for(C.TRANSIENT, 3),
        policy.delay_for(C.TRANSIENT, 4),
        policy.delay_for(C.TRANSIENT, 5),
        policy.delay_for(C.TRANSIENT, 20),
    ]
    o["draws_after_positive"] = jitter.calls
    o["zero_delays"] = [policy.delay_for(C.CONTRACT, 1), policy.delay_for(C.TERMINAL, 3)]
    o["draws_after_zero"] = jitter.calls
    o["clock_calls_after_delays"] = clock.calls

    clamp = []
    for value in (0.0, 1.0, 2.5, -1.0):
        clamped, _, _ = S.policy_with(jitter_value=value)
        clamp.append(clamped.delay_for(C.THROTTLE, 1))
    o["clamp"] = clamp
    o["delay_zero_attempt_raises"] = raises(policy.delay_for, C.THROTTLE, 0)

    # ---- P7: the verdict's shape, its routed counter and its reason code --
    verdict = S.decide(policy, Exception("rate limit"))
    o["is_dataclass"] = dataclasses.is_dataclass(verdict)
    field0 = dataclasses.fields(verdict)[0].name if dataclasses.is_dataclass(verdict) else None
    o["frozen"] = raises(setattr, verdict, field0, None) if field0 else {"raised": False, "mro": []}
    o["v_retry"] = S.v_retry(verdict)
    o["v_class"] = _cls(S.v_class(verdict))
    o["v_attempt"] = S.v_attempt(verdict)
    o["counter_throttle"] = S.counter_moved(policy, verdict)
    o["reason_throttle"] = S.v_reason(verdict)

    o["counter_contract"] = S.counter_moved(policy, S.decide(policy, ValueError("bad")))
    o["reason_contract"] = S.v_reason(S.decide(policy, ValueError("bad")))
    o["counter_transient"] = S.counter_moved(policy, S.decide(policy, TimeoutError("x")))
    o["reason_transient"] = S.v_reason(S.decide(policy, TimeoutError("x")))
    terminal = S.decide(policy, Exception("invalid api key"), attempts_made=2)
    o["terminal_retry"] = S.v_retry(terminal)
    o["terminal_counter"] = S.counter_moved(policy, terminal)
    o["terminal_reason"] = S.v_reason(terminal)
    o["terminal_attempt"] = S.v_attempt(terminal)
    o["terminal_delay"] = S.v_delay(terminal)

    # ---- P9: exactly one counter moves per failure -----------------------
    policy2, _, _ = S.policy_with(clock_value=1000.0, jitter_value=0.25)
    tracker = S.fake_tracker()
    seq = []
    S.record(policy2, tracker, S.decide(policy2, Exception("rate limit")))
    seq.append(list(S.counters(tracker)))
    S.record(policy2, tracker, S.decide(policy2, TimeoutError("x")))
    seq.append(list(S.counters(tracker)))
    S.record(policy2, tracker, S.decide(policy2, ValueError("bad")))
    seq.append(list(S.counters(tracker)))
    S.record(policy2, tracker, S.decide(policy2, Exception("invalid api key")))
    seq.append(list(S.counters(tracker)))
    o["counter_sequence"] = seq

    # ---- P10: the summary and the shared attempt label -------------------
    o["summary_a"] = rp.format_failure_summary([
        (C.TRANSIENT, "boom"),
        (C.THROTTLE, "rate limit"),
        (C.TRANSIENT, "boom"),
        (C.CONTRACT, "bad"),
        (C.THROTTLE, "rate limit"),
        (C.THROTTLE, "rate limit"),
    ])
    o["summary_b"] = rp.format_failure_summary([(C.CONTRACT, "b"), (C.TRANSIENT, "a"), (C.TRANSIENT, "a")])
    o["summary_c"] = rp.format_failure_summary([(C.TRANSIENT, "a"), (C.CONTRACT, "a")])
    o["summary_empty"] = rp.format_failure_summary([])
    o["labels"] = [rp.format_attempt_label(0, 10), rp.format_attempt_label(3, 3), rp.format_attempt_label(0, 0)]

    # ---- the wiring: APIRequest's new fields, and the except block -------
    o["apirequest_fields"] = [f.name for f in dataclasses.fields(S.APIRequest)]
    fresh = S.make_api_request()
    o["fresh_attempts_made"] = S.read_field(fresh, "attempts_made")
    o["fresh_failure_log"] = S.read_field(fresh, "failure_log")
    o["fresh_attempts_left"] = S.read_field(fresh, "attempts_left")

    processor = S.make_processor(max_retries=3)
    o["built_policy"] = any(isinstance(value, rp.RetryPolicy) for value in vars(processor).values())

    tracker = S.OnlineStatusTracker()
    request = S.make_api_request()
    queue = S.drive_one_failure(processor, request, tracker, Exception("API error: Rate limit reached for gpt-4o"))
    o["queue_size"] = queue.qsize()
    got = queue.get_nowait()
    o["queue_is_request"] = got is request
    o["request_attempts_made"] = S.read_field(request, "attempts_made")
    log = S.read_field(request, "failure_log")
    o["request_failure_log"] = [[_cls(c), m] for (c, m) in log]
    o["wired_counters"] = list(S.counters(tracker))
    return o


# ---------------------------------------------------------------------------
# r1 — what a failure costs, and the per-request 429 waivers
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    rp = S.rp
    o: dict = {}
    o["default_waivers"] = rp.DEFAULT_THROTTLE_WAIVERS
    o["apirequest_fields"] = [f.name for f in dataclasses.fields(S.APIRequest)]
    o["fresh_waivers"] = S.read_field(S.make_api_request(), "throttle_waivers_left")

    params = inspect.signature(rp.RetryPolicy.decide).parameters
    o["decide_params"] = list(params)
    o["decide_var_keyword"] = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())

    policy, _, _ = S.policy_with(jitter_value=0.25)
    transient = policy.decide(TimeoutError("x"), attempts_made=0, attempts_left=9, throttle_waivers_left=4)
    o["transient"] = [S.v_budget(transient), S.v_waivers(transient)]
    contract = policy.decide(ValueError("bad"), attempts_made=0, attempts_left=9, throttle_waivers_left=4)
    o["contract"] = [S.v_budget(contract), S.v_waivers(contract)]
    waived = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=9, throttle_waivers_left=4)
    o["waived"] = outcome(waived)
    unwaived = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=9, throttle_waivers_left=0)
    o["unwaived"] = outcome(unwaived)
    return o


def probe_r1_scope() -> dict:
    o = {"has_waivers": waivers_are_implemented()}
    if not o["has_waivers"]:
        return o
    first = S.make_api_request(task_id=1)
    first.throttle_waivers_left = 0
    second = S.make_api_request(task_id=2)
    o["second_waivers"] = S.read_field(second, "throttle_waivers_left")
    o["first_waivers"] = S.read_field(first, "throttle_waivers_left")

    policy, _, _ = S.policy_with(jitter_value=0.25)
    loop_waivers, loop_budgets = [], []
    for _ in range(6):
        verdict = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=5, throttle_waivers_left=6)
        loop_waivers.append(S.v_waivers(verdict))
        loop_budgets.append(S.v_budget(verdict))
    o["loop_waivers"] = loop_waivers
    o["loop_budgets"] = loop_budgets

    tracker_names = {f.name for f in dataclasses.fields(S.OnlineStatusTracker)}
    o["tracker_waiver_fields"] = sorted(n for n in tracker_names if "waiver" in n.lower())
    o["tracker_waiver_attrs"] = sorted(n for n in dir(S.OnlineStatusTracker()) if "waiver" in n.lower())
    config_names = set(S.OnlineRequestProcessorConfig.model_fields)
    o["config_waiver_fields"] = sorted(n for n in config_names if "waiver" in n.lower())

    budget = {f.name: f for f in dataclasses.fields(S.APIRequest)}["attempts_left"]
    o["attempts_left_no_default"] = (budget.default is dataclasses.MISSING and budget.default_factory is dataclasses.MISSING)
    return o


def probe_r1_exclusions() -> dict:
    o = {"has_waivers": waivers_are_implemented()}
    if not o["has_waivers"]:
        return o
    policy, _, _ = S.policy_with(jitter_value=0.25)
    dead = policy.decide(PermissionError("nope"), attempts_made=1, attempts_left=5, throttle_waivers_left=4)
    o["dead"] = outcome(dead)
    waived = policy.decide(Exception("too many requests"), attempts_made=4, attempts_left=0, throttle_waivers_left=1)
    o["waived"] = outcome(waived)
    spent = policy.decide(Exception("too many requests"), attempts_made=5, attempts_left=0, throttle_waivers_left=0)
    o["spent"] = outcome(spent)
    return o


def probe_r1_failure_behavior() -> dict:
    o = {"has_waivers": waivers_are_implemented()}
    if not o["has_waivers"]:
        return o
    policy, _, jitter = S.policy_with(jitter_value=0.25)
    affordable = policy.decide(ValueError("bad"), attempts_made=0, attempts_left=2, throttle_waivers_left=6)
    o["affordable"] = outcome(affordable)
    o["drawn"] = jitter.calls

    unaffordable = policy.decide(ValueError("bad"), attempts_made=1, attempts_left=1, throttle_waivers_left=6)
    o["unaffordable"] = outcome(unaffordable)
    o["unaffordable_budget"] = S.v_budget(unaffordable)
    o["unaffordable_delay"] = S.v_delay(unaffordable)
    o["draws_after_unaffordable"] = jitter.calls

    empty = policy.decide(TimeoutError("x"), attempts_made=9, attempts_left=0, throttle_waivers_left=0)
    o["empty"] = outcome(empty)
    o["empty_delay"] = S.v_delay(empty)
    o["draws_after_empty"] = jitter.calls
    return o


def probe_r1_observability() -> dict:
    rp = S.rp
    o = {"has_waivers": waivers_are_implemented()}
    if not o["has_waivers"]:
        return o
    o["default_waivers"] = rp.DEFAULT_THROTTLE_WAIVERS
    o["fresh_waivers"] = S.read_field(S.make_api_request(), "throttle_waivers_left")

    policy, _, _ = S.policy_with(jitter_value=0.25)
    healthy = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=3, throttle_waivers_left=6)
    o["healthy"] = [S.v_budget(healthy), S.v_waivers(healthy)]
    broke = policy.decide(Exception("rate limit"), attempts_made=9, attempts_left=0, throttle_waivers_left=3)
    o["broke"] = [S.v_retry(broke), S.v_waivers(broke)]
    spent = policy.decide(Exception("rate limit"), attempts_made=9, attempts_left=0, throttle_waivers_left=0)
    o["spent"] = [S.v_retry(spent), S.v_reason(spent), S.v_budget(spent)]
    length = policy.decide(ValueError("finish_reason was length"), attempts_made=0, attempts_left=3, throttle_waivers_left=6)
    o["length_budget"] = S.v_budget(length)
    last = policy.decide(ValueError("finish_reason was length"), attempts_made=0, attempts_left=1, throttle_waivers_left=6)
    o["last"] = [S.v_retry(last), S.v_reason(last), S.v_budget(last)]
    bad_key = policy.decide(Exception("invalid api key"), attempts_made=2, attempts_left=7, throttle_waivers_left=6)
    o["bad_key"] = [S.v_reason(bad_key), S.v_budget(bad_key), S.v_waivers(bad_key)]
    return o


# ---------------------------------------------------------------------------
# r2 — an absolute cooldown horizon that only 429s extend
# ---------------------------------------------------------------------------
def probe_r2_rule() -> dict:
    from types import SimpleNamespace
    rp = S.rp
    o: dict = {}
    names = tracker_fields()
    o["tracker_field_names"] = names

    o["fresh_horizon"] = S.OnlineStatusTracker().throttle_cooldown_until

    # The added-field diff against the pristine tree. baseline_text reads the
    # staged, world-readable copy the runner names in CURATOR_BASELINE_DIR; where
    # there is no baseline it returns None and this sub-check is skipped, not
    # failed (nothing to diff against is not a failed requirement).
    shipped = baseline_text("status_tracker/online_status_tracker.py")
    o["has_baseline"] = shipped is not None
    if shipped is not None:
        added = {n for n in names if f"{n}:" not in shipped}
        o["added_pause_fields"] = sorted(n for n in added if any(w in n.lower() for w in _PAUSE_WORDS))

    policy, clock, _ = S.policy_with(clock_value=500.0, jitter_value=1.0)
    tracker = S.fake_tracker()
    long_wait = throttle_verdict(policy)
    o["long_delay"] = S.v_delay(long_wait)
    S.record(policy, tracker, long_wait)
    o["long_clock_calls"] = clock.calls
    o["long_tolre"] = tracker.time_of_last_rate_limit_error
    o["long_horizon"] = tracker.throttle_cooldown_until

    shorter, _, _ = S.policy_with(clock_value=500.0, jitter_value=0.0)
    short_wait = throttle_verdict(shorter)
    o["short_delay"] = S.v_delay(short_wait)
    S.record(shorter, tracker, short_wait)
    o["short_horizon"] = tracker.throttle_cooldown_until
    o["short_tolre"] = tracker.time_of_last_rate_limit_error

    longer, _, _ = S.policy_with(clock_value=500.0, jitter_value=1.0)
    later = throttle_verdict(longer, attempts_made=1)
    o["later_delay"] = S.v_delay(later)
    S.record(longer, tracker, later)
    o["later_horizon"] = tracker.throttle_cooldown_until

    horizoned = SimpleNamespace(time_of_last_rate_limit_error=0.0, **{HORIZON: 508.0009})
    o["remaining"] = [
        rp.remaining_cooldown_seconds(horizoned, 500.0),
        rp.remaining_cooldown_seconds(horizoned, 508.0),
        rp.remaining_cooldown_seconds(horizoned, 508.0009),
        rp.remaining_cooldown_seconds(horizoned, 600.0),
    ]
    return o


def probe_r2_scope() -> dict:
    o = {"has_horizon": horizon_is_implemented()}
    if not o["has_horizon"]:
        return o
    policy, clock, _ = S.policy_with(clock_value=700.0, jitter_value=0.25)
    tracker = S.fake_tracker()

    def apply(exc):
        S.record(policy, tracker, S.decide(policy, exc, attempts_made=0, attempts_left=9, throttle_waivers_left=9))

    apply(TimeoutError("x"))
    o["c1"] = list(S.counters(tracker))
    apply(ValueError("bad"))
    o["c2"] = list(S.counters(tracker))
    apply(PermissionError("no"))
    o["c3"] = list(S.counters(tracker))
    o["clock_after_nonthrottle"] = clock.calls
    o["horizon_after_nonthrottle"] = tracker.throttle_cooldown_until
    o["tolre_after_nonthrottle"] = tracker.time_of_last_rate_limit_error

    apply(Exception("rate limit"))
    o["c4"] = list(S.counters(tracker))
    o["clock4"] = clock.calls
    o["horizon4"] = tracker.throttle_cooldown_until
    o["tolre4"] = tracker.time_of_last_rate_limit_error

    apply(TimeoutError("again"))
    apply(ValueError("again"))
    o["c5"] = list(S.counters(tracker))
    o["clock5"] = clock.calls
    o["horizon5"] = tracker.throttle_cooldown_until
    o["tolre5"] = tracker.time_of_last_rate_limit_error

    apply(Exception("too many requests"))
    o["clock6"] = clock.calls
    return o


def probe_r2_exclusions() -> dict:
    import asyncio
    import time
    o = {"has_horizon": horizon_is_implemented()}
    if not o["has_horizon"]:
        return o
    cfg = S.OnlineRequestProcessorConfig
    o["knob_in_config"] = "seconds_to_pause_on_rate_limit" in cfg.model_fields
    o["knob_default"] = cfg(model="gpt-4o-mini").seconds_to_pause_on_rate_limit
    o["knob_set"] = cfg(model="gpt-4o-mini", seconds_to_pause_on_rate_limit=42).seconds_to_pause_on_rate_limit
    processor = S.make_processor(max_retries=3, seconds_to_pause_on_rate_limit=10)
    o["processor_knob"] = processor.config.seconds_to_pause_on_rate_limit

    slept: list = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    real_sleep = asyncio.sleep
    asyncio.sleep = fake_sleep
    try:
        lapsed = S.OnlineStatusTracker()
        lapsed.time_of_last_rate_limit_error = time.time()
        setattr(lapsed, HORIZON, 0.0)
        asyncio.run(processor.cool_down_if_rate_limit_error(lapsed))
        o["slept_after_lapsed"] = list(slept)

        asyncio.run(processor.cool_down_if_rate_limit_error(S.OnlineStatusTracker()))
        o["slept_after_never"] = list(slept)

        ahead = S.OnlineStatusTracker()
        ahead.time_of_last_rate_limit_error = 0.0
        setattr(ahead, HORIZON, time.time() + 4.0)
        asyncio.run(processor.cool_down_if_rate_limit_error(ahead))
        o["slept_after_ahead"] = list(slept)
    finally:
        asyncio.sleep = real_sleep
    return o


def probe_r2_observability() -> dict:
    rp = S.rp
    o = {"has_horizon": horizon_is_implemented()}
    if not o["has_horizon"]:
        return o
    policy, _, _ = S.policy_with(clock_value=1000.0, jitter_value=0.25)
    tracker = S.fake_tracker()

    first = S.decide(policy, Exception("rate limit"), attempts_made=0, attempts_left=5, throttle_waivers_left=6)
    o["first_delay"] = S.v_delay(first)
    S.record(policy, tracker, first)
    o["first_horizon"] = tracker.throttle_cooldown_until
    o["first_tolre"] = tracker.time_of_last_rate_limit_error

    S.record(policy, tracker, dataclasses.replace(first, **{S.delay_field_name(first): 1.0}))
    o["second_horizon"] = tracker.throttle_cooldown_until

    o["remaining"] = [
        rp.remaining_cooldown_seconds(tracker, 1002.0),
        rp.remaining_cooldown_seconds(tracker, 1004.5),
        rp.remaining_cooldown_seconds(tracker, 1005.0),
        rp.remaining_cooldown_seconds(tracker, 1099.0),
    ]

    fresh = S.OnlineStatusTracker()
    o["fresh_horizon"] = fresh.throttle_cooldown_until
    o["fresh_remaining"] = rp.remaining_cooldown_seconds(fresh, 12345.0)
    return o


PROBES = {
    "test_open::test_open_feature__failures_are_classified_priced_and_summarised_by_the_policy_module": probe_open,
    "test_r1::test_rule__a_throttle_spends_a_waiver_a_transient_one_attempt_and_a_contract_two": probe_r1_rule,
    "test_r1::test_scope__the_waiver_allowance_is_per_request_and_lives_nowhere_else": probe_r1_scope,
    "test_r1::test_exclusions__a_terminal_verdict_discards_the_budget_and_an_empty_budget_still_retries_a_waived_throttle": probe_r1_exclusions,
    "test_r1::test_failure_behavior__exhaustion_is_tested_after_the_cost_is_charged_and_the_floor_is_zero": probe_r1_failure_behavior,
    "test_r1::test_observability__the_stated_budget_and_waiver_table_holds_exactly": probe_r1_observability,
    "test_r2::test_rule__the_cooldown_horizon_is_one_new_tracker_field_that_only_ever_moves_forward": probe_r2_rule,
    "test_r2::test_scope__only_throttles_extend_the_horizon_or_consult_the_clock": probe_r2_scope,
    "test_r2::test_exclusions__the_seconds_to_pause_knob_survives_in_config_and_is_never_read_again": probe_r2_exclusions,
    "test_r2::test_observability__the_stated_horizon_and_remaining_cooldown_table_holds_exactly": probe_r2_observability,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        try:
            results[node] = {"ok": True, "obs": fn()}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
