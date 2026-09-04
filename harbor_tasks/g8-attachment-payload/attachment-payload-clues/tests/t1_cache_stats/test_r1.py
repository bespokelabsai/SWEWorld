"""t1 — hidden requirement r1: what the cache key is made of.

One decisive test per field. "Decisive" has a precise meaning here: the test
must FAIL on untouched curator. Four tests used to grade `rule` and three of
them passed on the pristine tree — curator's fingerprint already covers model,
generation params and response format — so they could never discriminate and
they drowned the one test that could.

The oracle is the provider's request count. "Served from the cache versus sent
to the backend" is, read literally, a count of requests that reached the
backend, and a real server is the only thing that measures it without also
measuring the agent's bookkeeping.
"""
from __future__ import annotations

import pytest
from datasets import Dataset
from pydantic import BaseModel, ConfigDict, create_model

from bespokelabs import curator

from harness import cache_stats_of, read_field

pytestmark = pytest.mark.timeout(240)

MODEL = "gpt-4o-mini"


class Describer(curator.LLM):
    """Renders from `topic` alone; every other column is unused by prompt()."""

    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


def llm_for(provider, batch: bool = False, **params):
    """`batch` is an LLM argument, not a backend_param.

    Passing it inside backend_params fails validation — `extra = "forbid"` —
    and the error names BatchRequestProcessorConfig, which reads like the batch
    path rejecting the test rather than the test malforming the call.
    """
    return Describer(model_name=MODEL, backend="openai", batch=batch,
                     backend_params={"base_url": provider.url("api.openai.com"),
                                     "in_mtok_cost": 1000, "out_mtok_cost": 1000,
                                     **params})


def rows(*pairs):
    return Dataset.from_list([{"topic": t, "source_id": s} for t, s in pairs])


# =============================================================================
# rule
# =============================================================================
class Answer(BaseModel):
    """A response_format that differs from None, for the tuple probe."""

    text: str


def test_rule__every_member_of_the_tuple_takes_part_in_the_key(provider):
    """`rule` enumerates a tuple. This grades that tuple and nothing else.

        (rendered prompt text, model_name, response_format schema,
         generation_params)

    Change a member, the row must be re-sent; change nothing, it must not.

    What is NOT graded here: that two rows rendering one prompt collapse to one
    entry. That is `exclusions`, stated there in its own words, and asserting it
    here billed one defect against two facts. The clause "not from the raw input
    row alone" has no observable of its own beyond that collapse, so it is left
    to the field that states it.
    """
    llm = llm_for(provider)
    ds = rows(("cats", 1))

    _, cold = provider.delta(lambda: llm(ds))
    assert cold == 1, f"a cold run should have reached the backend once, saw {cold}"

    _, again = provider.delta(lambda: llm(ds))
    assert again == 0, (
        f"re-running the same rows sent {again} request(s); no prior response "
        "was looked up at all")

    def probe(**kw):
        """One LLM differing from `llm` in exactly one member of the tuple."""
        params = {"base_url": provider.url("api.openai.com"),
                  "in_mtok_cost": 1000, "out_mtok_cost": 1000}
        # model_name and generation_params are LLM arguments, NOT
        # backend_params. Passed inside backend_params they are silently
        # ignored, the LLM is identical to the one above, the run is a hit, and
        # a correct implementation reads as failing its own requirement.
        return Describer(model_name=kw.pop("model_name", MODEL),
                         backend="openai", backend_params=params, **kw)

    # The rendered prompt text is first in the tuple and was the one member
    # never probed — every other clause of `rule` had a check and this one did
    # not. It cannot discriminate (a raw-row key re-sends here too, since the
    # row differs), but the requirement names it, so it is graded.
    _, other_prompt = provider.delta(lambda: llm(rows(("dogs", 1))))
    assert other_prompt >= 1, (
        "the rendered prompt text is the first member of the tuple the key is "
        "derived from, so a different prompt must reach the backend; the run "
        f"sent {other_prompt} request(s)")

    for what, other in (
            ("model_name", probe(model_name="gpt-4o")),
            ("generation_params", probe(generation_params={"temperature": 0.7})),
            ("response_format", probe(response_format=Answer)),
    ):
        _, sent = provider.delta(lambda other=other: other(ds))
        # A lower bound, not an equality. The claim is that the row misses and
        # is re-sent; how many times it then goes out is curator's retry
        # policy, which this requirement says nothing about — the oracle sends
        # two for the response_format probe and was failed for it.
        assert sent >= 1, (
            f"{what} is named in the tuple the key is derived from, so changing "
            f"it must re-send the row; the run sent {sent} request(s)")


# =============================================================================
# scope — the same key on the batch path
# =============================================================================
def test_scope__the_batch_path_looks_up_prior_responses_too(provider):
    """`scope`: every path that already calls the cache-lookup helper, batch
    included.

    So: the same dataset, twice, in batch mode. The second run must find the
    first's responses instead of submitting again — that is the lookup applying
    on this path, which is the whole of what `scope` claims.

    An earlier version required one batch to carry a single request for two
    rows rendering the same prompt. Collapsing duplicates inside one submission
    is a different behaviour, stated in no field, and an implementation that
    looks up prior responses on the batch path without it was failed for it.
    """
    llm = llm_for(provider, batch=True, batch_check_interval=1)
    ds = rows(("cats", 1))

    llm(ds)
    assert provider.batches_created == 1, (
        f"a cold batch run submitted {provider.batches_created} batch(es), want 1")

    provider.reset()
    result = llm(ds)
    assert provider.batches_created == 0, (
        "the same dataset was submitted as a second batch; the batch path is "
        "not looking up prior responses")
    assert len(result.dataset) == 1, (
        f"the cached batch run returned {len(result.dataset)} row(s) for a "
        "one-row dataset")


# =============================================================================
# exclusions_or_crossover
# =============================================================================
def test_exclusions__two_duplicate_rows_are_not_two_misses(provider):
    """"...must be COUNTED AS the same cache entry, not treated as separate
    misses."

    The claim is about counting, so counting is what is graded. An
    implementation that issues both requests and reports one miss and one hit
    has followed this sentence exactly; so has one that issues a single request.
    Both pass. An earlier version asserted the provider saw exactly one
    request, which is request-collapsing — a stronger behaviour than any field
    here states.

    Both output rows must still come back: de-duplicating must not drop a row
    the caller asked for.
    """
    llm = llm_for(provider)
    result = llm(rows(("cats", 1), ("cats", 2)))

    assert len(result.dataset) == 2, (
        f"the run returned {len(result.dataset)} row(s) for a two-row dataset; "
        "treating the rows as one entry must not drop the output")

    stats = cache_stats_of(llm)
    misses = read_field(stats, "misses", "sent", "cache_misses", "to_backend",
                        default=None)
    assert misses is not None, (
        "cache_stats() reports nothing that could be a miss count, so whether "
        f"two duplicate rows were counted as one entry cannot be read: {stats!r}")
    # The requirement's words are "not treated as SEPARATE misses" — a bound,
    # not a value. One miss (a retrospective report: the pair was fetched once)
    # and zero (a prospective one: the pair is now cached, a re-run costs
    # nothing) both satisfy it. Two does not. The ticket asks for both readings
    # in one sentence, so neither may be required.
    assert misses <= 1, (
        f"two rows rendering to an identical prompt, differing only in a column "
        f"prompt() never reads, were counted as {misses} separate misses; the "
        "requirement says they are one cache entry")


# =============================================================================
# failure_behavior
# =============================================================================
def test_failure_behavior__unhashable_schema_does_not_raise_in_the_cache(
        provider):
    """"...must be treated as a guaranteed cache miss rather than raising."

    The subject of that sentence is the CACHE. It does not say the run
    completes — a schema pydantic cannot render is also unrenderable into a
    request, and demanding an end-to-end success graded curator's request
    builder, which this requirement says nothing about.

    So the question asked here is narrow: when the key cannot be computed, did
    the cache layer degrade to a miss, or did it raise? Answered from the
    traceback. Untouched curator raises inside `_hash_fingerprint`, which is
    the cache layer, and fails. An implementation whose key function returns a
    miss passes even if the run later dies building the request.
    """
    class Opaque:
        pass

    Dyn = create_model("DynamicAnswer", value=(Opaque, ...),
                       __config__=ConfigDict(arbitrary_types_allowed=True))
    llm = Describer(model_name=MODEL, backend="openai", response_format=Dyn,
                    backend_params={"base_url": provider.url("api.openai.com"),
                                    "in_mtok_cost": 1000, "out_mtok_cost": 1000})
    ds = rows(("cats", 1))

    try:
        _, first = provider.delta(lambda: llm(ds))
    except Exception as exc:                      # noqa: BLE001 - the point
        where = _cache_frame(exc)
        assert where is None, (
            "computing the cache key for an unhashable response_format raised "
            f"instead of degrading to a miss: {type(exc).__name__} at {where}")
        return                                    # cache complied; rest is not r1

    _, second = provider.delta(lambda: llm(ds))
    assert first >= 1, "the first run never reached the backend"
    assert second >= 1, (
        "an unhashable response_format must be a guaranteed miss on every run; "
        "the second run was served from the cache")


def _cache_frame(exc: BaseException) -> str | None:
    """The cache-layer frame an exception passed through, if any.

    Matched on function name rather than module path: the agent chooses where
    the key lives, and requiring a filename would fail a correct
    implementation for putting it somewhere reasonable.
    """
    import traceback
    words = ("fingerprint", "cache_key", "cache_hash", "_hash", "cache_stats")
    for frame in traceback.extract_tb(exc.__traceback__):
        name = frame.name.lower()
        if any(w in name for w in words):
            return f"{frame.filename.rsplit('/', 1)[-1]}:{frame.lineno} in {frame.name}"
    return None


# =============================================================================
# observability
# =============================================================================
def test_observability__hit_rate_and_misses_account_for_every_row(provider):
    """`hit_rate` float, `misses` int, "together account for 100% of processed
    rows".

    That sentence is an INVARIANT, and the invariant is what is graded:
    everything is either a hit or a miss, and `hit_rate` is the hit share.
    Nothing here fixes what the numbers must be on a given run.

    It cannot, because the ticket asks for two things at once — "how many of
    the last run's requests were served from the cache versus sent to the
    backend" AND "so users can gauge how much a re-run will cost". After a cold
    run of four rows the retrospective answer is 4 misses and the prospective
    one is 0, since those four rows are now cached. Both answer the ticket;
    an earlier version required 4 and failed the agent who built the other.

    Distinct prompts still, so "processed rows" cannot mean two different
    numbers on top of that.
    """
    llm = llm_for(provider)
    ds = rows(("cats", 1), ("dogs", 1), ("birds", 1), ("fish", 1))
    total = 4

    llm(ds)
    stats = cache_stats_of(llm)
    hit_rate = read_field(stats, "hit_rate")
    misses = read_field(stats, "misses")
    hits = read_field(stats, "hits", "cached", "cache_hits", "from_cache",
                      default=None)

    assert isinstance(hit_rate, float), \
        f"hit_rate must be a float, got {type(hit_rate).__name__}"
    assert isinstance(misses, int) and not isinstance(misses, bool), \
        f"misses must be an int, got {type(misses).__name__}"

    reported_total = read_field(stats, "total", "total_requests", "rows",
                                "processed", default=None)
    if reported_total is None and hits is not None:
        reported_total = hits + misses
    assert reported_total == total, (
        f"four rows were processed; cache_stats() accounts for "
        f"{reported_total}. Reported: {stats!r}")
    assert 0 <= misses <= total, (
        f"misses={misses} is outside the {total} rows processed: {stats!r}")
    assert hit_rate == pytest.approx(1.0 - misses / total, abs=1e-6), (
        f"hit_rate={hit_rate} and misses={misses} do not account for all "
        f"{total} processed rows: {stats!r}")

    # After an identical re-run both readings agree — nothing is left to fetch.
    llm(ds)
    warm = cache_stats_of(llm)
    assert read_field(warm, "misses") == 0, (
        f"every row of an identical re-run was already cached; reported "
        f"{read_field(warm, 'misses')} miss(es)")
    assert read_field(warm, "hit_rate") == pytest.approx(1.0), (
        f"every row of an identical re-run was already cached; hit_rate="
        f"{read_field(warm, 'hit_rate')}")
