"""t2 — hidden requirement r2: estimate from a sample, not the whole dataset.

    rule              above a size threshold, estimate from the first N rows
    scope             below the threshold, use every row
    failure_behavior  a row whose prompt() raises is skipped, not fatal
    observability     the estimate says full pass or sample, and the sample size

Graded on what the estimate SAYS ABOUT ITSELF, not on counting prompt() calls
before some internal boundary. Counting cannot separate the estimator's
traversal from the run's own, because curator renders every row to build
request files whether or not anyone wants an estimate — and the boundary I
first picked (`create_request_files`) sat on the wrong side of a real agent's
implementation, scoring `rule` as passed on a trivially true `0 < 1000`.

Neither N nor the threshold is stated anywhere in the requirement, so no test
here hardcodes one. An earlier version used 1,000 rows; the agent chose a
sample size of exactly 1,000, so at the boundary it correctly did a full pass
and was failed for it.
"""
from __future__ import annotations

import re

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import require_feature, unmeasured

pytestmark = pytest.mark.timeout(600)

MODEL = "gpt-4o-mini"
# Large enough to be above any defensible threshold, small enough to build.
# 50,000 took over three minutes per run and this suite needs the large run
# several times; curator renders every row into request files regardless of
# whether the estimator wanted them, so the cost is in curator, not the
# provider. The one large run is shared through a module-scoped fixture below.
BIG = 10_000
SMALL = 5
SAMPLE = re.compile(r"\b(sampl\w+|first\s+[\d,]+|subset)\b", re.I)
FULL = re.compile(r"\b(full|all|every|entire|complete)\b", re.I)
COUNT = re.compile(r"\b([\d,]{1,12})\b")
# Proof an estimator ran at all, so "cannot tell whether it sampled" is only
# reached by an implementation that HAS a pre-flight — an untouched checkout
# still fails rather than being excused as unobservable.
ESTIMATE_PRINTED = re.compile(r"estimat\w*[^\n]*\$\s*[\d,]", re.I)


def dataset(n, raise_on=None):
    return Dataset.from_list([{"idx": i} for i in range(n)])


def make_llm(provider, raise_on=None):
    class Described(curator.LLM):
        def prompt(self, input):
            if raise_on is not None and input["idx"] == raise_on:
                raise ValueError("verifier: this row cannot be rendered")
            return f"Describe subject {input['idx']} in one sentence."

    return Described(model_name=MODEL, backend="openai", batch=True,
                     backend_params={"base_url": provider.url("api.openai.com"),
                                     "batch_check_interval": 1,
                                     "in_mtok_cost": 1000, "out_mtok_cost": 1000})


def declaration(output) -> tuple[bool, int | None, str]:
    """(claims a sample, the size it names, the lines it said it on)."""
    text = output()
    lines = [l for l in text.splitlines()
             if re.search(r"cost|estimat|sampl|row|pass", l, re.I)]
    body = "\n".join(lines)
    if SAMPLE.search(body):
        sizes = [int(n.replace(",", "")) for l in lines if SAMPLE.search(l)
                 for n in COUNT.findall(l)]
        return True, (min(sizes) if sizes else None), body
    return False, None, body


@pytest.fixture(scope="module")
def _big_cache():
    """One slot, so the expensive large run happens once per module."""
    return {}


def big_run(provider, output, _big_cache):
    """The large-dataset declaration, computed once and reused.

    Four tests need to know whether the estimate claims a sample, and three of
    them only need it as a precondition. Running BIG four times turned a 30
    second suite into a four minute one.
    """
    if "declaration" not in _big_cache:
        _big_cache["declaration"] = run(provider, output, BIG)
    return _big_cache["declaration"]


def run(provider, output, n, raise_on=None):
    output()
    llm = make_llm(provider, raise_on)
    try:
        llm(dataset(n))
    except BaseException as exc:                 # noqa: BLE001 - reported below
        return declaration(output) + (exc,)
    return declaration(output) + (None,)


# =============================================================================
# rule
# =============================================================================
def test_rule__a_large_dataset_is_estimated_from_a_sample(
        provider, output, _big_cache):
    """`rule` says a large dataset is estimated FROM A SAMPLE.

    It does not say the estimate announces which it did — that is
    `observability`, graded separately. But announcing is the only channel this
    codebase offers: curator renders every row into request files whether or
    not an estimator wanted them, so counting `prompt()` calls cannot separate
    the estimator's traversal from the run's own.

    So an estimator that samples silently is COMPLIANT WITH THIS FACT and
    invisible to it. Failing it would be scoring `observability` twice under
    two names. It is dropped from the score instead.
    """
    sampled, size, body, exc = big_run(provider, output, _big_cache)
    assert exc is None or "verifier" not in str(exc), f"the run failed: {exc}"
    require_feature(ESTIMATE_PRINTED.search(body) is not None,
                    "a batch cost pre-flight estimate")
    if not (sampled or FULL.search(body)):
        unmeasured("the estimate does not say whether it sampled or did a full "
                   "pass, and nothing else in this codebase distinguishes them")
    assert sampled, (
        f"a {BIG:,}-row dataset is above any reasonable threshold and the "
        "estimate says it did a full pass. What was printed:\n"
        + body[-1200:])
    assert size is not None and size < BIG, (
        f"the estimate claims a sample but names {size}, which is not smaller "
        f"than the {BIG:,}-row dataset")


# =============================================================================
# scope
# =============================================================================
def test_scope__a_small_dataset_uses_every_row(provider, output, _big_cache):
    """Below the threshold there is nothing to save by sampling.

    `scope` claims one thing: below the threshold, every row is used. An
    implementation that never samples at all satisfies it — that violates
    `rule`, which is graded separately, and billing one defect against two
    facts is what this suite exists to avoid.

    So the gate is only that a pre-flight estimate EXISTS: "does not claim a
    sample" is trivially true of a run that prints nothing. It is deliberately
    NOT gated on the big run having sampled. The threshold is stated nowhere in
    the requirement, so an implementation whose threshold sits above this
    suite's 10,000-row dataset is doing a full pass correctly, and gating on
    that failed it for a number nobody specified.
    """
    _, _, big_body, _ = big_run(provider, output, _big_cache)
    require_feature(ESTIMATE_PRINTED.search(big_body) is not None,
                    "a batch cost pre-flight estimate")

    provider.reset()
    sampled, size, body, exc = run(provider, output, SMALL)
    assert exc is None or "verifier" not in str(exc), f"the run failed: {exc}"
    assert (not sampled) or size in (SMALL, None), (
        f"a {SMALL}-row dataset is below any reasonable threshold, so every row "
        f"should be used, but the estimate claims a sample of {size}. What was "
        f"printed:\n{body[-800:]}")


# =============================================================================
# failure_behavior
# =============================================================================
def test_failure_behavior__a_row_that_cannot_be_rendered_is_skipped(
        provider, output, _big_cache):
    """NOT OBSERVABLE in this codebase; recorded as unmeasured, not failed.

    The requirement says a row whose `prompt()` raises during the estimate must
    be skipped silently rather than aborting the pre-flight. But curator calls
    `prompt()` again to build its request files, and that call is not optional:
    a row that cannot be rendered takes the whole run down after the estimate
    has already finished, on the pristine tree and on every implementation of
    the estimator alike.

    So no behaviour distinguishes an estimator that skips the row from one that
    does not — the run dies either way, for a reason the estimator does not
    control. Scoring it zero would count a limit of curator against the agent.
    """
    pytest.skip(
        "a row whose prompt() raises kills request building regardless of what "
        "the estimator does, so skipping it silently has no observable "
        "consequence; recorded as unmeasured")


# =============================================================================
# observability
# =============================================================================
def test_observability__the_estimate_names_a_full_pass_or_a_sample_size(
        provider, output, _big_cache):
    sampled, size, body, exc = big_run(provider, output, _big_cache)
    assert exc is None or "verifier" not in str(exc), f"the run failed: {exc}"
    assert SAMPLE.search(body) or FULL.search(body), (
        "the estimate does not say whether it came from a full pass or a "
        f"sample. What was printed:\n{body[-1200:]}")
    if sampled:
        assert size is not None, (
            "the estimate claims a sample but never says how big it was")
