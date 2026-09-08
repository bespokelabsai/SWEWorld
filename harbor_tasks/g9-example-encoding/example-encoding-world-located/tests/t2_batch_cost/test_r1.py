"""t2 — hidden requirement r1: the discount is provider-specific.

    rule                    50% off for OpenAI and Anthropic batch
    scope                   the estimator only; billing is untouched
    exclusions_or_crossover litellm-backed models are NOT discounted

Untouched curator does the opposite: `_LitellmCostProcessor.cost` applies
`cost *= 0.5` whenever `self.batch` is set, through a defaultdict that catches
every backend. That is the reversed decision the corpus plants.

The `rule` test compares a run against ITSELF at double the price rather than
comparing two providers against each other. Comparing OpenAI to Anthropic
assumed identical token counts across two tokenizers, and the Anthropic batch
path is dead in this image anyway (`instructor.handle_response_model` no longer
exists), so that comparison failed an agent whose two estimates were in fact
identical and correct.
"""
from __future__ import annotations

import re

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import changed_source, require_feature

pytestmark = pytest.mark.timeout(300)

MODEL = "gpt-4o-mini"
MONEY = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)")

# Only lines that are the ESTIMATE. curator's batch tracker prints a model
# pricing line of its own ("Per 1M tokens: Input: $500.0"), and taking the
# largest dollar figure in the output picked that up instead — identical for a
# 3-row and a 60-row job, so a correct estimator read as not depending on the
# dataset at all.
ESTIMATE_LINE = re.compile(r"estimat", re.I)


def money_on_estimate_lines(text: str) -> list[float]:
    return [float(m.replace(",", ""))
            for line in text.splitlines() if ESTIMATE_LINE.search(line)
            for m in MONEY.findall(line)]



class Describer(curator.LLM):
    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


_RUN = [0]


def rows(n=3):
    """Fresh rows per estimate.

    The price is not part of curator's run key, so re-running the same rows at
    double the price is a cache hit: the pre-flight never runs, no estimate is
    printed, and the ratio assertion sees zero. That reads as "the estimate
    ignores the price" about an estimator that is perfectly correct.
    """
    _RUN[0] += 1
    return Dataset.from_list(
        [{"topic": f"run{_RUN[0]}-subject{i}"} for i in range(n)])


def estimate(provider, output, *, batch=True, price=1000, **params) -> float:
    """The largest dollar figure a run prints.

    Prices are pinned through `in_mtok_cost`/`out_mtok_cost`, real fields on
    RequestProcessorConfig, so the estimate does not depend on a price table
    that may have moved — and the RATIO between two runs cancels whatever
    tokenizer the agent chose.
    """
    # batch_check_interval is a BATCH-only config field; passing it on the
    # sync comparison run is rejected by OnlineRequestProcessorConfig's
    # extra="forbid", and the error names the config rather than the test.
    extra = {"batch_check_interval": 1} if batch else {}
    llm = Describer(model_name=MODEL, backend="openai", batch=batch,
                    backend_params={"base_url": provider.url("api.openai.com"),
                                    "in_mtok_cost": price, "out_mtok_cost": price,
                                    **extra, **params})
    output()
    llm(rows())
    amounts = money_on_estimate_lines(output())
    return max(amounts) if amounts else 0.0


# =============================================================================
# rule
# =============================================================================
def test_rule__the_batch_estimate_is_half_the_standard_price(provider, output):
    """The estimate is computed from the per-token price.

    Deliberately NOT "half the sync estimate". An earlier version compared the
    batch figure against a sync run, which contradicted this suite's own
    `scope` test — that one asserts the sync path prints no pre-flight at all,
    so the comparison demanded the very thing the neighbouring fact forbids.
    The reference implementation, which is correct, failed on it.

    The halving is only observable against a provider that is NOT discounted,
    and this codebase has no reachable one (see the exclusions test, recorded
    unmeasured). What remains observable, and is what the rule is made of, is
    that the figure is computed from the price rather than invented: double the
    per-token cost and the estimate doubles.
    """
    single = estimate(provider, output, price=1000)
    require_feature(single > 0, "a batch cost estimate")

    provider.reset()
    double = estimate(provider, output, price=2000)
    assert double == pytest.approx(single * 2, rel=0.05), (
        f"doubling the per-token price moved the estimate from {single} to "
        f"{double}; it is not computed from the price")

    # The 50% itself has no behavioural channel — there is no undiscounted
    # batch estimate in this codebase to compare against — so it is read from
    # the source the agent actually wrote, the way AlphaShop's fraud grader
    # reads for a mail path it has forbidden.
    #
    # Deliberately a wide alternation over files that DIFFER FROM THE BASELINE.
    # Halving is written a dozen defensible ways and the test must fail none of
    # them; and `0.5` occurs throughout an untouched library, so an unscoped
    # scan would credit an agent who wrote nothing.
    changed = changed_source()
    require_feature(bool(changed), "any change to curator at all")
    halving = re.compile(r"0?\.5\b|\b50\b|/\s*2\b|\bhalf|\bdiscount", re.I)
    hits = sorted(name for name, body in changed.items() if halving.search(body))
    assert hits, (
        "the estimate is computed from the price, but nothing in the "
        f"{len(changed)} file(s) this change touched carries a halving or "
        "discount factor (searched for 0.5, 50, /2, 'half', 'discount'); the "
        f"rule asks for 50% off standard pricing. Files changed: "
        f"{sorted(changed)[:6]}")


# =============================================================================
# scope — the estimator, not billing
# =============================================================================
def test_scope__the_sync_path_gets_no_batch_preflight(provider, output):
    """`batch=False` gets no pre-flight estimate.

    Gated on a batch estimate existing at all: with no pre-flight anywhere,
    untouched curator satisfies this by omission.
    """
    provider.reset()
    require_feature(estimate(provider, output, price=1000) > 0,
                    "the batch cost pre-flight")

    provider.reset()
    output()
    Describer(model_name=MODEL, backend="openai",
              backend_params={"base_url": provider.url("api.openai.com"),
                              "in_mtok_cost": 1000, "out_mtok_cost": 1000})(rows())
    text = output()
    claims = re.findall(r"[^\n]*\bpre-?flight\b[^\n]*", output(), re.I)
    assert not claims, (
        f"a sync run printed what reads as a batch pre-flight: {claims[:3]}")


# =============================================================================
# exclusions_or_crossover
# =============================================================================
def test_exclusions__litellm_backed_models_are_not_discounted(provider, output):
    """litellm keeps the standard price even with `batch=True`. UNMEASURABLE.

    Not observable at runtime: `_RequestProcessorFactory.create` raises "Batch
    mode is not supported with LiteLLM backend", so there is no litellm batch
    run to print an estimate from. An earlier version graded
    `cost_processor_factory` instead — the post-hoc BILLING seam, which this
    requirement's own `scope` explicitly excludes.

    Not observable in the source either, which is the newer finding. A version
    of this test scanned the agent's changed files for a litellm mention or an
    OpenAI/Anthropic allowlist, on the theory that a discount applied to every
    provider cannot be honouring "not for litellm". Reading a real blind
    submission showed why that fails: it matched

        import litellm
        from litellm import model_cost

    — litellm imported for its PRICING TABLE, by an implementation that never
    considered the exclusion at all. The check credited work unrelated to the
    fact, which is worse than not scoring it, because a passing grade that
    means nothing is indistinguishable from one that does.

    Skipped, so it is reported as unmeasured rather than counted either way.
    """
    pytest.skip("no reachable litellm batch path to observe an estimate from, "
                "and a source scan cannot separate a deliberate carve-out from "
                "an ordinary `import litellm` for pricing; recorded as "
                "unmeasured rather than scored")
