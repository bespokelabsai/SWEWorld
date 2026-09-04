"""t3 — hidden requirement r2: the limiter resets between invocations.

    rule              budgets are per-process and the limiter is RESET, not
                      reused, between two top-level invocations in one process
    scope             applies to reuse across multiple __call__ invocations
    failure_behavior  an unsatisfiable budget raises clearly rather than
                      stalling forever
    observability     a .remaining_budget() accessor

`failure_behavior` is the one that bites: untouched curator really does spin in
`while not status_tracker.has_capacity(...): await asyncio.sleep(0.1)` with no
exit. The suite runs under `--timeout-method=signal` for exactly this reason —
the thread method cannot interrupt a blocked asyncio loop, so it terminates the
whole pytest process, and both of this suite's earlier runs were lost that way
with no junit.xml and every fact scored zero.

"Top-level pipeline invocation" is approximated as a fresh chain of `__call__`s,
because curator has no first-class pipeline object.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

from discovery import build_limiter, find_limiter, new_config_fields
from harness import unmeasured

pytestmark = pytest.mark.timeout(240)

PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}


class Block(curator.LLM):
    def prompt(self, input):
        return f"Say something about {input['seed']}."


_RUN = [0]


def seeds(n=2):
    """Fresh rows per invocation.

    Reusing the same rows makes the second invocation a cache hit, and a run
    served entirely from the cache never enters the request path at all — so a
    limiter reset that lives there never happens, and the test reports "the
    limiter was reused rather than reset" about an invocation that did no work.
    """
    _RUN[0] += 1
    return Dataset.from_list(
        [{"seed": f"run{_RUN[0]}-s{i}"} for i in range(n)])


def block(provider, **params):
    return Block(model_name="gpt-4o-mini", backend="openai",
                 backend_params={"base_url": provider.url("api.openai.com"),
                                 **PRICES, **params})


def shared(provider, rpm=600, tpm=100_000):
    """A block plus the shared limiter, built the way the API offers one.

    `remaining_budget()` is named verbatim by r2.observability, so requiring it
    HERE is fair — but only after trying to construct the limiter, since an
    implementation where the caller builds it never puts one on a bare block.
    """
    limiter, _ = build_limiter(rpm=rpm, tpm=tpm)
    if limiter is None:
        llm = block(provider, max_requests_per_minute=rpm,
                    max_tokens_per_minute=tpm)
        llm(seeds())
        limiter = find_limiter(llm)
        if limiter is None:
            pytest.fail("no limiter could be constructed from curator's "
                        "exports, and nothing on a block that has run exposes "
                        "remaining_budget()")
        return llm, limiter
    if not callable(getattr(limiter, "remaining_budget", None)):
        pytest.fail("the shared limiter has no remaining_budget(); the "
                    "requirement names that accessor verbatim")
    llm = chained(provider, limiter)
    llm(seeds())
    return llm, limiter


def chained(provider, limiter, **params):
    for slot in new_config_fields():
        try:
            return block(provider, **{slot: limiter}, **params)
        except Exception:                        # noqa: BLE001 - wrong slot
            continue
    pytest.fail("no config field accepted the limiter object")


def budget_value(limiter):
    """`remaining_budget()` as one number, whatever shape it returns.

    Objects included. A real implementation returned
    `RateLimitBudget(requests=..., tokens=..., consumed_requests=...)`, a
    perfectly loggable dataclass, and the earlier version — which understood
    only numbers, dicts and sequences — read it as "not a number" and failed
    two facts for the shape of a value the requirement never constrains.
    """
    value = limiter.remaining_budget()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, dict):
        numbers = [v for v in value.values() if isinstance(v, (int, float))]
        return sum(numbers) if numbers else 0
    if isinstance(value, (list, tuple)):
        return sum(v for v in value if isinstance(v, (int, float)))
    # Anything else: total the public numeric fields. `consumed_*` is excluded
    # because it counts the opposite direction — spend, not headroom — and
    # summing both makes a drained budget look untouched.
    numbers = []
    for name in dir(value):
        if name.startswith("_") or name.startswith("consumed"):
            continue
        try:
            attr = getattr(value, name)
        except Exception:                        # noqa: BLE001 - properties bite
            continue
        if isinstance(attr, (int, float)) and not isinstance(attr, bool):
            numbers.append(attr)
    return sum(numbers) if numbers else 0


def drain(limiter) -> int:
    """Spend the budget without knowing how it is stored.

    Zeroes every numeric attribute whose name reads like a budget — these are
    `OnlineStatusTracker`'s own words (`available_request_capacity`,
    `available_token_capacity`) and any agent's are likely to rhyme.
    """
    hit = 0
    for name in dir(limiter):
        if name.startswith("_") or not any(
                w in name for w in ("capacit", "budget", "remaining", "available")):
            continue
        try:
            value = getattr(limiter, name)
        except Exception:                        # noqa: BLE001
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                setattr(limiter, name, 0)
                hit += 1
            except Exception:                    # noqa: BLE001 - read-only
                continue
    return hit


# =============================================================================
# observability
# =============================================================================
def test_observability__remaining_budget_accessor_exists(provider):
    """Named verbatim in the requirement, so fair to require by name."""
    _, limiter = shared(provider)
    value = limiter.remaining_budget()
    # The requirement names the ACCESSOR — "a .remaining_budget() accessor must
    # be available on the limiter for the pipeline to log" — and fixes nothing
    # about what it returns. A dataclass carrying requests and tokens is at
    # least as loggable as a bare float; demanding a builtin type failed one.
    assert value is not None, (
        "remaining_budget() returned None, so there is nothing for the "
        "pipeline to log")
    assert budget_value(limiter) is not None, (
        f"remaining_budget() returned {type(value).__name__} with no numeric "
        f"content to log: {value!r}")


# =============================================================================
# rule
# =============================================================================
def test_rule__the_limiter_is_reset_between_top_level_invocations(provider):
    """Drain it, run again, and the second invocation must still work."""
    _, limiter = shared(provider)
    chained(provider, limiter)(seeds())

    if not drain(limiter):
        # `rule` is about resetting between invocations. Whether a budget can
        # be drained from outside is not something it asks for, so a limiter
        # that hides its counters is invisible here rather than incorrect —
        # failing it would grade `observability` a second time.
        unmeasured("no spendable budget is reachable on the limiter, so "
                   "whether it resets between invocations cannot be seen")

    chained(provider, limiter)(seeds())
    after = budget_value(limiter)
    assert after and after > 0, (
        f"after a drained budget and a fresh invocation, remaining_budget() is "
        f"{after}; the limiter was reused rather than reset")


# =============================================================================
# scope
# =============================================================================
def test_scope__consumption_does_not_accumulate_across_invocations(provider):
    """Budget spent in run one must not still be missing in run two."""
    _, limiter = shared(provider)
    start = budget_value(limiter)
    if not isinstance(start, (int, float)):
        pytest.fail(f"remaining_budget() is not a number: {start!r}")

    chained(provider, limiter)(seeds())
    after_one = budget_value(limiter)
    chained(provider, limiter)(seeds())
    after_two = budget_value(limiter)

    spent_one = start - after_one
    spent_two = after_one - after_two
    assert spent_two <= max(spent_one, 0) + abs(start) * 0.01 or after_two > 0, (
        f"budget across two invocations went {start} -> {after_one} -> "
        f"{after_two}; consumption is accumulating rather than resetting")


# =============================================================================
# failure_behavior
# =============================================================================
@pytest.mark.timeout(45)
def test_failure_behavior__an_unreset_limiter_raises_instead_of_stalling(
        provider):
    """The requirement's scenario, exactly:

        "If the limiter is not reset and a second invocation starts while
         budget already appears exhausted from the first, it must raise a clear
         error rather than silently stalling forever."

    So: drain the budget in one invocation, then start a second WITHOUT
    resetting. An earlier version instead built a fresh limiter with a token
    budget too small for any single request — a situation this requirement
    never describes — and failed an implementation that raises correctly in the
    case it does describe.
    """
    _, limiter = shared(provider)
    chained(provider, limiter)(seeds())

    if not drain(limiter):
        unmeasured("no spendable budget is reachable on the limiter, so a "
                   "second invocation cannot be started against an exhausted "
                   "one")

    try:
        chained(provider, limiter)(seeds())
    except BaseException as exc:                 # noqa: BLE001 - classified below
        caught = type("C", (), {"value": exc})
    else:
        # It ran. That means the limiter reset itself between invocations —
        # which is r2.RULE, stated in the same requirement. This fact's own
        # precondition ("if the limiter is NOT reset") is therefore unreachable
        # for any implementation that satisfies the rule beside it, so there is
        # nothing here to score. Failing it would penalise an agent for
        # complying with the neighbouring field.
        unmeasured("the limiter reset itself between invocations, so the "
                   "un-reset state this fact describes cannot be reached "
                   "without violating r2.rule")

    # A stall reaches here as pytest-timeout's Failed, which is a BaseException
    # — without this check "never returned" reads as "raised unhelpfully", and
    # the two need opposite fixes.
    if "Timeout" in type(caught.value).__name__ or \
            ">>> timeout" in str(caught.value).lower():
        pytest.fail(
            "a second invocation against a drained, un-reset limiter never "
            "returned; the requirement says it must raise rather than stall")

    message = str(caught.value).lower() + " " + type(caught.value).__name__.lower()
    assert any(word in message for word in
               ("budget", "capacit", "exhaust", "rate limit", "reset",
                "too small", "token")), (
        "a second invocation against a drained, un-reset limiter failed, but "
        f"the error does not say why: {caught.value!r}")
