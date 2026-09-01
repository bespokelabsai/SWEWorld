"""t1 — hidden requirement r1: what the cache key is made of.

    rule                    the key is (rendered prompt, model_name,
                            response_format schema, generation_params), not the
                            raw input row
    scope                   every path through the cache-lookup helper, batch
                            and online alike
    exclusions_or_crossover two rows that render to one prompt are one entry
    failure_behavior        an unhashable response_format is a guaranteed miss,
                            never a raise
    observability           hit_rate and misses account for 100% of rows

The oracle throughout is the provider-call counter, not the numbers the agent
reports. "Served from the cache versus sent to the backend" is a count of HTTP
posts, and grading an agent's own bookkeeping against itself would pass a
`cache_stats()` that returns plausible constants.

What these tests reject is baseline curator's behaviour: `LLM._hash_fingerprint`
keys on the dataset's fingerprint, so changing a column `prompt()` never reads
re-bills the whole run.
"""
from __future__ import annotations

import pytest
from datasets import Dataset
from pydantic import BaseModel, create_model

from bespokelabs import curator

from ..conftest import cache_stats_of, read_field

pytestmark = pytest.mark.timeout(180)

MODEL = "gpt-4o-mini"


# Module scope, so `_hash_fingerprint`'s dill pickle of prompt_func is stable
# across the runs inside one test.
class Describer(curator.LLM):
    """Renders from `topic` alone. Every other column is unused by prompt()."""

    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


class AnswerA(BaseModel):
    answer: str


class AnswerB(BaseModel):
    reply: str


def rows(*pairs):
    return Dataset.from_list([{"topic": t, "source_id": s} for t, s in pairs])


# =============================================================================
# rule
# =============================================================================
def test_rule__identical_prompt_from_a_different_input_row_is_a_hit(transport):
    """The discriminating test for the whole task.

    The two rows render to byte-identical prompts and differ only in
    `source_id`, which `prompt()` never reads. The second run must not reach the
    provider. The third changes the rendered text and must, so an agent who
    simply never misses cannot pass by accident.
    """
    llm = Describer(model_name=MODEL, backend="openai")

    _, cold = transport.delta(lambda: llm(rows(("cats", 1))))
    assert cold == 1, "a cold run should have reached the backend exactly once"

    _, warm = transport.delta(lambda: llm(rows(("cats", 2))))
    assert warm == 0, (
        f"same rendered prompt, same model, same params — only an input column "
        f"that prompt() never reads changed — and the run still made {warm} "
        "backend call(s). The key is still derived from the raw input row.")

    _, changed = transport.delta(lambda: llm(rows(("dogs", 2))))
    assert changed == 1, "a genuinely different prompt must still be a miss"


def test_rule__model_name_is_part_of_the_key(transport):
    """Guards the opposite failure: keying on the prompt text alone."""
    ds = rows(("cats", 1))
    _, cold = transport.delta(
        lambda: Describer(model_name=MODEL, backend="openai")(ds))
    assert cold == 1

    _, other = transport.delta(
        lambda: Describer(model_name="gpt-4o", backend="openai")(ds))
    assert other == 1, (
        "a different model_name reused another model's cached answer")


def test_rule__generation_params_are_part_of_the_key(transport):
    ds = rows(("cats", 1))
    _, cold = transport.delta(lambda: Describer(
        model_name=MODEL, backend="openai",
        generation_params={"temperature": 0.2})(ds))
    assert cold == 1

    _, other = transport.delta(lambda: Describer(
        model_name=MODEL, backend="openai",
        generation_params={"temperature": 0.9})(ds))
    assert other == 1, "generation_params must participate in the cache key"


def test_rule__response_format_schema_is_part_of_the_key(transport):
    ds = rows(("cats", 1))
    _, cold = transport.delta(lambda: Describer(
        model_name=MODEL, backend="openai", response_format=AnswerA)(ds))
    assert cold == 1

    _, other = transport.delta(lambda: Describer(
        model_name=MODEL, backend="openai", response_format=AnswerB)(ds))
    assert other == 1, "a different response_format schema must be a new key"


# =============================================================================
# scope — the same keying on the batch path
# =============================================================================
def test_scope__batch_mode_uses_the_same_prompt_level_key(openai_batch_stub):
    """`batch=True` runs a different processor but the same cache helper.

    Same A/B rows, same expectation. An agent who changed the key in the online
    path only has done half the job, and the requirement names both.
    """
    llm = Describer(model_name=MODEL, backend="openai", batch=True,
                    backend_params={"batch_check_interval": 1})

    llm(rows(("cats", 1)))
    assert openai_batch_stub.n_batches == 1, (
        "a cold batch run should have submitted exactly one batch")

    openai_batch_stub.reset()
    llm(rows(("cats", 2)))
    assert openai_batch_stub.n_batches == 0, (
        "batch mode re-submitted a dataset whose rendered prompts were already "
        "cached; the prompt-level key is not applied on the batch path")


# =============================================================================
# exclusions_or_crossover
# =============================================================================
def test_exclusions__two_rows_with_one_rendered_prompt_are_one_entry(transport):
    """Within a single dataset, duplicate rendered prompts are one entry."""
    llm = Describer(model_name=MODEL, backend="openai")
    llm(rows(("cats", 1), ("cats", 2)))

    assert transport.n == 1, (
        "two rows rendering to the same prompt were billed as "
        f"{transport.n} separate requests")

    stats = cache_stats_of(llm)
    assert read_field(stats, "misses") == 1
    assert read_field(stats, "hit_rate") == pytest.approx(0.5)


# =============================================================================
# failure_behavior
# =============================================================================
def test_failure_behavior__dynamic_response_format_is_a_guaranteed_miss(transport):
    """A schema built by `create_model` cannot be hashed.

    The contract is that the row degrades to a miss. Raising is the failure this
    names, and an accidental HIT is just as wrong: it would mean two different
    dynamic schemas sharing an entry.
    """
    Dyn = create_model("DynamicAnswer", answer=(str, ...))
    llm = Describer(model_name=MODEL, backend="openai", response_format=Dyn)
    ds = rows(("cats", 1))

    try:
        _, first = transport.delta(lambda: llm(ds))
    except Exception as exc:                      # noqa: BLE001 — the point
        pytest.fail(f"an unhashable response_format raised instead of "
                    f"degrading to a miss: {type(exc).__name__}: {exc}")

    _, second = transport.delta(lambda: llm(ds))
    assert first == 1
    assert second == 1, (
        "an unhashable response_format must be a guaranteed miss on every run, "
        "not an accidental hit")

    stats = cache_stats_of(llm)
    assert read_field(stats, "hit_rate") == pytest.approx(0.0)


# =============================================================================
# observability
# =============================================================================
def test_observability__hit_rate_and_misses_account_for_every_row(transport):
    """Both names are in the requirement, so both are fair to require.

    Four rows, two distinct prompts, each duplicated through an unused column.
    """
    llm = Describer(model_name=MODEL, backend="openai")
    total = 4
    llm(rows(("cats", 1), ("dogs", 1), ("cats", 2), ("dogs", 2)))

    stats = cache_stats_of(llm)
    hit_rate = read_field(stats, "hit_rate")
    misses = read_field(stats, "misses")

    assert isinstance(hit_rate, float), \
        f"hit_rate must be a float, got {type(hit_rate).__name__}"
    assert isinstance(misses, int) and not isinstance(misses, bool), \
        f"misses must be an int, got {type(misses).__name__}"
    assert 0.0 <= hit_rate <= 1.0
    assert hit_rate == pytest.approx(1.0 - misses / total, abs=1e-6), (
        f"hit_rate={hit_rate} and misses={misses} do not account for all "
        f"{total} processed rows")
