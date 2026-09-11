"""g3 — hidden requirement r1: what a failure costs, and the per-request 429 waivers.

    rule              a failure is priced against the request's own budget by class and the
                      price is not uniform — TRANSIENT 1, CONTRACT 2, THROTTLE 0 while the
                      request still holds one of its `DEFAULT_THROTTLE_WAIVERS = 6` waivers;
                      `decide` takes `throttle_waivers_left` and the verdict reports both the
                      post-failure budget and the post-failure waiver count
    scope             the allowance is per REQUEST: a fresh `APIRequest` starts at six however
                      many 429s its siblings absorbed, the policy holds no run-level count, and
                      neither `OnlineStatusTracker` nor `OnlineRequestProcessorConfig` carries
                      one; `attempts_left` keeps its seeding from `config.max_retries`
    exclusions        a TERMINAL verdict DISCARDS the rest of the budget (`attempts_left` -> 0)
                      while passing the waivers through untouched; conversely a zero-cost
                      THROTTLE at `attempts_left == 0` is still retried, because `0 - 0 >= 0`
    failure_behavior  the cost is charged first and exhaustion is `attempts_left - cost < 0`,
                      not `attempts_left <= 0` before pricing; an exhausted verdict carries a
                      `0.0` delay it never asked the schedule for, and a budget clamped to 0
    observability     the literal table the requirement writes out

`rule`, `exclusions` and `failure_behavior` deliberately use budgets and exceptions that do
not appear in `observability`'s table, so the four are four measurements rather than one
repeated. `failure_behavior` is the only test that watches the jitter counter, and the only
one that brackets the cost-2 boundary at `attempts_left` 2 and 1 — the pair that separates
"charge, then test" from "test, then charge".
"""
from __future__ import annotations

import asyncio
import dataclasses
import datetime
import inspect
import re

from harness import read_field, require_feature

from test_open import importable, make_api_request, make_processor, policy_with, v_budget, v_delay, v_reason, v_retry, v_waivers

try:
    from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
    from bespokelabs.curator.request_processor.online import retry_policy as rp
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        APIRequest,
        BaseOnlineRequestProcessor,
        _TokenUsage,
    )
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
    from bespokelabs.curator.types.generic_response import GenericResponse
except Exception:  # pragma: no cover - reported by importable(), per test
    rp = OnlineRequestProcessorConfig = APIRequest = BaseOnlineRequestProcessor = OnlineStatusTracker = None
    _TokenUsage = GenericResponse = None


def outcome(verdict):
    """The five numbers every fact below is expressed in.

    Read through `test_open`'s tolerant readers: r1 fixes the names
    `throttle_waivers_left` and `DEFAULT_THROTTLE_WAIVERS`, but it describes the
    verdict's own two new numbers only as "the post-failure budget and the
    post-failure waiver count", so their spelling is not the agent's to lose on.
    """
    return (
        v_retry(verdict),
        v_budget(verdict),
        v_waivers(verdict),
        read_field(verdict, "attempt_index", "attempt", "attempt_number", "attempt_no"),
        v_reason(verdict),
    )


def waivers_are_implemented() -> bool:
    """Is there a per-request waiver budget at all?

    Read off the field r1 names on `APIRequest`, or off `decide`'s keyword — an
    implementation that takes `**kwargs` has one just as much as one that spells
    the parameter out.
    """
    if any(f.name == "throttle_waivers_left" for f in dataclasses.fields(APIRequest)):
        return True
    params = inspect.signature(rp.RetryPolicy.decide).parameters
    return "throttle_waivers_left" in params or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())


# =============================================================================
# rule — TRANSIENT costs 1, CONTRACT costs 2, THROTTLE costs a waiver
# =============================================================================
def test_rule__a_throttle_spends_a_waiver_a_transient_one_attempt_and_a_contract_two():
    importable()
    assert rp.DEFAULT_THROTTLE_WAIVERS == 6

    names = [f.name for f in dataclasses.fields(APIRequest)]
    assert "throttle_waivers_left" in names, f"APIRequest carries no waiver counter; it has {names}"
    assert read_field(make_api_request(), "throttle_waivers_left") == rp.DEFAULT_THROTTLE_WAIVERS

    # decide takes the waiver budget alongside the other two, by keyword.
    params = inspect.signature(rp.RetryPolicy.decide).parameters
    takes_everything = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    assert takes_everything or {"attempts_made", "attempts_left", "throttle_waivers_left"} <= set(params), f"decide takes {list(params)}"

    policy, _, _ = policy_with(jitter_value=0.25)

    # The prices, read off one shared healthy budget of 9 so the three are
    # comparable and none of them is near an exhaustion boundary.
    transient = policy.decide(TimeoutError("x"), attempts_made=0, attempts_left=9, throttle_waivers_left=4)
    assert v_budget(transient) == 8, "a transient failure costs exactly one attempt"
    assert v_waivers(transient) == 4, "a transient failure does not touch the waivers"

    contract = policy.decide(ValueError("bad"), attempts_made=0, attempts_left=9, throttle_waivers_left=4)
    assert v_budget(contract) == 7, "a contract failure costs two attempts, not one"
    assert v_waivers(contract) == 4

    waived = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=9, throttle_waivers_left=4)
    assert outcome(waived) == (True, 9, 3, 1, "throttle:retry"), "a throttle with a waiver in hand must spend the waiver, not the budget"

    # ... and once the waivers are gone a throttle costs 1, like any transient.
    unwaived = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=9, throttle_waivers_left=0)
    assert outcome(unwaived) == (True, 8, 0, 1, "throttle:retry"), "with no waivers left a throttle must cost one attempt"


# =============================================================================
# scope — the allowance belongs to the request, not to the run or the model
# =============================================================================
def test_scope__the_waiver_allowance_is_per_request_and_lives_nowhere_else():
    importable()
    require_feature(waivers_are_implemented(), "the per-request throttle waiver budget")

    # Two requests, independently seeded. Draining one leaves the other whole.
    first = make_api_request(task_id=1)
    first.throttle_waivers_left = 0
    second = make_api_request(task_id=2)
    assert read_field(second, "throttle_waivers_left") == 6, "a fresh request must start with six waivers regardless of what its siblings absorbed"
    assert read_field(first, "throttle_waivers_left") == 0

    # The policy itself keeps no running total: the same question asked six
    # times gets the same answer, so nothing per-run is being decremented.
    policy, _, _ = policy_with(jitter_value=0.25)
    for _ in range(6):
        verdict = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=5, throttle_waivers_left=6)
        assert v_waivers(verdict) == 5, "the waiver count comes from the argument, not from state the policy is hoarding"
        assert v_budget(verdict) == 5

    # Nothing on the run-level tracker or in the config holds or seeds it.
    tracker_names = {f.name for f in dataclasses.fields(OnlineStatusTracker)}
    assert not [n for n in tracker_names if "waiver" in n.lower()], f"OnlineStatusTracker gained a waiver field: {sorted(tracker_names)}"
    assert not [n for n in dir(OnlineStatusTracker()) if "waiver" in n.lower()]
    config_names = set(OnlineRequestProcessorConfig.model_fields)
    assert not [n for n in config_names if "waiver" in n.lower()], f"OnlineRequestProcessorConfig gained a waiver knob: {sorted(config_names)}"

    # attempts_left keeps its name, its lack of a default, and its seeding.
    budget = {f.name: f for f in dataclasses.fields(APIRequest)}["attempts_left"]
    assert budget.default is dataclasses.MISSING and budget.default_factory is dataclasses.MISSING, "attempts_left must still be seeded by the caller"
    source = inspect.getsource(BaseOnlineRequestProcessor)
    assert re.search(r"attempts_left\s*=\s*[^,\n)]*max_retries", source), "attempts_left is no longer seeded from config.max_retries"


# =============================================================================
# exclusions — terminal burns the budget; a waived throttle survives an empty one
# =============================================================================
def test_exclusions__a_terminal_verdict_discards_the_budget_and_an_empty_budget_still_retries_a_waived_throttle():
    importable()
    require_feature(waivers_are_implemented(), "the per-request throttle waiver budget")
    policy, _, _ = policy_with(jitter_value=0.25)

    # Five attempts remained and are thrown away; the waivers are passed through.
    dead = policy.decide(PermissionError("nope"), attempts_made=1, attempts_left=5, throttle_waivers_left=4)
    assert outcome(dead) == (False, 0, 4, 2, "terminal:abort"), "a terminal verdict must zero the remaining budget and leave the waivers alone"

    # The converse: no budget at all, but a waiver in hand, so 0 - 0 >= 0 holds.
    waived = policy.decide(Exception("too many requests"), attempts_made=4, attempts_left=0, throttle_waivers_left=1)
    assert outcome(waived) == (True, 0, 0, 5, "throttle:retry"), "an empty attempt budget must not stop a rate-limited request that still holds a waiver"

    # and the next one, with the waivers now spent, is the one that stops.
    assert outcome(policy.decide(Exception("too many requests"), attempts_made=5, attempts_left=0, throttle_waivers_left=0)) == (False, 0, 0, 6, "throttle:exhausted")


# =============================================================================
# failure_behavior — charge first, then test; clamp at 0; never price a refusal
# =============================================================================
def test_failure_behavior__exhaustion_is_tested_after_the_cost_is_charged_and_the_floor_is_zero():
    importable()
    require_feature(waivers_are_implemented(), "the per-request throttle waiver budget")
    policy, _, jitter = policy_with(jitter_value=0.25)

    # The cost-2 boundary. `attempts_left <= 0` checked BEFORE pricing would
    # retry both of these and hand back -1 for the second.
    affordable = policy.decide(ValueError("bad"), attempts_made=0, attempts_left=2, throttle_waivers_left=6)
    assert outcome(affordable) == (True, 0, 6, 1, "contract:retry"), "2 - 2 == 0 is affordable, so this one is retried"
    drawn = jitter.calls

    unaffordable = policy.decide(ValueError("bad"), attempts_made=1, attempts_left=1, throttle_waivers_left=6)
    assert outcome(unaffordable) == (False, 0, 6, 2, "contract:exhausted"), "1 - 2 < 0, so a contract failure at one attempt left ends the request"
    assert v_budget(unaffordable) == 0, "the post-failure budget is clamped at zero, never negative"
    assert v_delay(unaffordable) == 0.0
    assert jitter.calls == drawn, "a verdict that will not be retried must never ask the schedule for a delay"

    empty = policy.decide(TimeoutError("x"), attempts_made=9, attempts_left=0, throttle_waivers_left=0)
    assert outcome(empty) == (False, 0, 0, 10, "transient:exhausted")
    assert v_delay(empty) == 0.0
    assert jitter.calls == drawn, "an exhausted transient must not consume the jitter source either"


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

    processor.call_single_request = answer
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


# =============================================================================
# observability — the requirement's own table, as literals
# =============================================================================
def test_observability__the_stated_budget_and_waiver_table_holds_exactly():
    importable()
    require_feature(waivers_are_implemented(), "the per-request throttle waiver budget")

    assert rp.DEFAULT_THROTTLE_WAIVERS == 6
    assert read_field(make_api_request(), "throttle_waivers_left") == 6

    policy, _, _ = policy_with(jitter_value=0.25)

    healthy = policy.decide(Exception("rate limit"), attempts_made=0, attempts_left=3, throttle_waivers_left=6)
    assert v_budget(healthy) == 3
    assert v_waivers(healthy) == 5

    broke = policy.decide(Exception("rate limit"), attempts_made=9, attempts_left=0, throttle_waivers_left=3)
    assert v_retry(broke) is True
    assert v_waivers(broke) == 2

    spent = policy.decide(Exception("rate limit"), attempts_made=9, attempts_left=0, throttle_waivers_left=0)
    assert v_retry(spent) is False
    assert v_reason(spent) == "throttle:exhausted"
    assert v_budget(spent) == 0

    length = policy.decide(ValueError("finish_reason was length"), attempts_made=0, attempts_left=3, throttle_waivers_left=6)
    assert v_budget(length) == 1

    last = policy.decide(ValueError("finish_reason was length"), attempts_made=0, attempts_left=1, throttle_waivers_left=6)
    assert v_retry(last) is False
    assert v_reason(last) == "contract:exhausted"
    assert v_budget(last) == 0

    bad_key = policy.decide(Exception("invalid api key"), attempts_made=2, attempts_left=7, throttle_waivers_left=6)
    assert v_reason(bad_key) == "terminal:abort"
    assert v_budget(bad_key) == 0
    assert v_waivers(bad_key) == 6

    # The `length` row again, through the request path, where curator raises exactly
    # that ValueError on an invalid finish_reason. `decide` above never sees a call
    # site that reclassifies `length` on its way in: three v7 runs made it terminal
    # there (a new TERMINAL error, or `attempts_left = 0` before pricing) and each
    # still passed this fact.
    truncated = make_api_request(attempts_left=3)
    queue = drive_one_response(make_processor(max_retries=3), truncated, OnlineStatusTracker(), finish_reason="length")
    assert queue.qsize() == 1, "a length-truncated response with attempts to spare was not re-queued"
    assert read_field(truncated, "attempts_left") == 1, "on the request path a length-truncated response must be charged like any contract failure, two attempts"
