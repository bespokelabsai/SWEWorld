"""t3 — hidden requirement r1: a shared limiter wins over local numbers.

    rule                    the second block must NOT re-initialise
                            max_requests_per_minute / max_tokens_per_minute
                            from its own backend_params
    scope                   only when a limiter OBJECT is passed, not raw numbers
    exclusions_or_crossover with no shared limiter, each block builds its own

The reversed decision the corpus plants is the first draft, where the second
block's backend_params overrode the shared limiter's rpm and silently broke the
point of sharing it. An agent reading only the code writes that version,
because `BaseOnlineRequestProcessor.__init__` reads
`manual_max_requests_per_minute` from config and has no reason not to.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

from discovery import (build_limiter, effective_rpm, find_limiter,
                       new_config_fields, shares_limiter)
from harness import require_feature

pytestmark = pytest.mark.timeout(300)

PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}
SHARED_RPM = 600
LOCAL_RPM = 60_000


class Block(curator.LLM):
    def prompt(self, input):
        return f"Say something about {input['seed']}."


def seeds(n=2):
    return Dataset.from_list([{"seed": f"s{i}"} for i in range(n)])


def block(provider, **params):
    return Block(model_name="gpt-4o-mini", backend="openai",
                 backend_params={"base_url": provider.url("api.openai.com"),
                                 **PRICES, **params})


def first_block(provider):
    llm = block(provider, max_requests_per_minute=SHARED_RPM,
                max_tokens_per_minute=100_000)
    llm(seeds())
    return llm


def chain(provider, limiter, **params):
    """Block two, with the limiter in whichever slot the agent chose."""
    errors = []
    for slot in new_config_fields():
        try:
            llm = block(provider, **{slot: limiter}, **params)
            llm(seeds())
            return llm, slot
        except Exception as exc:                 # noqa: BLE001 - wrong slot
            errors.append(f"{slot}: {type(exc).__name__}")
    pytest.fail(f"no config field accepted the limiter object. Tried: {errors}")


def limiter_or_fail(llm):
    """The shared limiter, however this implementation offers one.

    Construction first: the ticket says "passing an existing rate limiter
    instance", so a class the caller builds is the plainest reading and is what
    real agents shipped. Extraction from a block that has run is accepted too,
    for an implementation that exposes its own. Only when neither works is
    there nothing to test.
    """
    limiter, _ = build_limiter(rpm=SHARED_RPM)
    if limiter is None:
        limiter = find_limiter(llm, require_budget=False)
    if limiter is None:
        pytest.fail("no shared limiter could be reached: curator exports no "
                    "new class that constructs as one, and nothing on a block "
                    "that has run looks like one either")
    return limiter


# =============================================================================
# rule
# =============================================================================
def test_rule__the_second_blocks_own_budget_is_ignored_when_sharing(provider):
    """The shared budget wins, for requests and for tokens.

    Block two asks for a hundred times the rate and must not get it. Both
    budgets are checked here rather than in two tests, because the requirement
    names them together and a field gets one decisive test.
    """
    first = first_block(provider)
    limiter = limiter_or_fail(first)
    second, slot = chain(provider, limiter,
                         max_requests_per_minute=LOCAL_RPM,
                         max_tokens_per_minute=9_000_000)

    got = effective_rpm(second)
    assert got != LOCAL_RPM, (
        f"block two passed max_requests_per_minute={LOCAL_RPM} alongside a "
        f"shared limiter (in `{slot}`) and took its own number anyway")
    # "in favour of the shared limiter's configuration" is satisfied by pacing
    # against the shared limiter. NOT asserted: that some field on block two
    # now reads SHARED_RPM. A limiter implemented as a bucket the tracker
    # delegates to leaves the processor's own number at curator's 200 default,
    # and demanding the mirror failed exactly that design.
    assert shares_limiter(second, limiter), (
        f"block two dropped its own budget but is not pacing against the "
        f"shared limiter passed in `{slot}`, so nothing supplies the "
        "configuration the requirement says wins")

    processor = getattr(second, "_request_processor", None)
    tpm = getattr(processor, "max_tokens_per_minute", None)
    if tpm is None:
        tpm = getattr(getattr(processor, "tracker", None),
                      "max_tokens_per_minute", None)
    assert tpm != 9_000_000, (
        "block two's own max_tokens_per_minute overrode the shared limiter's")


# =============================================================================
# scope
# =============================================================================
def test_scope__raw_numbers_do_not_count_as_a_shared_limiter(provider):
    """"Only when a limiter object is passed."

    Handing an int to the limiter slot shares nothing, and the local numbers
    must keep working. Either the config rejects the int — a fine answer, since
    `extra="forbid"` makes the config a real gate — or the block honours its own
    rpm.
    """
    slots = new_config_fields()
    if not slots:
        pytest.fail("no new config field, so there is no limiter slot to test")

    slot = slots[0]
    try:
        llm = block(provider, **{slot: 600}, max_requests_per_minute=LOCAL_RPM)
    except Exception:                            # noqa: BLE001 - rejecting is fine
        return
    llm(seeds())
    assert effective_rpm(llm) == pytest.approx(LOCAL_RPM), (
        f"a raw number in `{slot}` was treated as a shared limiter and "
        "suppressed the block's own max_requests_per_minute")


# =============================================================================
# exclusions_or_crossover
# =============================================================================
def test_exclusions__without_a_shared_limiter_each_block_keeps_its_own(provider):
    """The unchanged path stays unchanged.

    Gated on sharing existing at all: untouched curator also passes this by
    never having shared anything.
    """
    # The precondition is that sharing exists AT ALL — not that the limiter
    # exposes remaining_budget() (a different hidden fact standing in front of
    # this one), and not that a bare block hands one out. Constructing counts:
    # in the API both agents shipped, the caller builds the limiter, so a block
    # with none passed has nothing to extract and this gate failed an
    # implementation that shares perfectly well.
    built, _ = build_limiter()
    require_feature(
        built is not None
        or find_limiter(first_block(provider), require_budget=False) is not None,
        "a limiter that can be shared between blocks")

    a = block(provider, max_requests_per_minute=300)
    a(seeds())
    b = block(provider, max_requests_per_minute=900)
    b(seeds())

    assert effective_rpm(a) == pytest.approx(300), (
        f"a block with no shared limiter ended on {effective_rpm(a)}, not 300")
    assert effective_rpm(b) == pytest.approx(900), (
        f"a block with no shared limiter ended on {effective_rpm(b)}, not 900")
