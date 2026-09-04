"""t1 — the openly stated feature, and nothing beyond it.

The ticket asks for `cache_stats()` on `curator.LLM` reporting how much of the
last run came from the cache versus the backend. Nothing here tests a hidden
requirement, and in particular nothing here requires the field to be called
`misses`: that name is fixed only by r1's observability fact, and requiring it
here once failed an agent whose CacheStats(cached, sent, total, hit_rate,
cache_dir) answered the ticket exactly.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import cache_stats_of, read_field, surface

pytestmark = pytest.mark.timeout(180)

MODEL = "gpt-4o-mini"


class Describer(curator.LLM):
    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


def llm_for(provider, **params):
    return Describer(model_name=MODEL, backend="openai",
                     backend_params={"base_url": provider.url("api.openai.com"),
                                     "in_mtok_cost": 1000, "out_mtok_cost": 1000,
                                     **params})


def test_open_feature__cache_stats_reports_a_cold_run_and_a_warm_one(provider):
    """A cold run reaches the backend; an identical re-run does not.

    Both halves are measured at the provider, not from the agent's own
    bookkeeping — otherwise a `cache_stats()` returning plausible constants
    passes. Baseline curator already caches at run level, so an agent who wires
    counters into the existing path passes this. That is intended: this test
    separates "built nothing" from "built it and missed the hidden facts".
    """
    llm = llm_for(provider)
    rows = Dataset.from_list([{"topic": "cats"}])

    _, cold = provider.delta(lambda: llm(rows))
    assert cold == 1, f"a first run should have reached the backend once, saw {cold}"

    stats = cache_stats_of(llm)
    served = read_field(stats, "hits", "cached", "cache_hits", "from_cache",
                        default=None)
    sent = read_field(stats, "misses", "sent", "cache_misses", "to_backend",
                      default=None)
    assert served is not None or sent is not None, (
        "cache_stats() reports neither how many requests were served from the "
        "cache nor how many went to the backend, which is what the ticket asked "
        f"for. Fields present: {surface(stats)}")
    # NOT asserted: that a cold run reports one miss. The ticket asks for a
    # report of "the last run's requests ... so users can gauge how much a
    # re-run will cost", which is two different numbers — what just happened,
    # and what a re-run would cost. After a cold run the row IS now cached, so
    # a prospective reading reports 0 misses and a retrospective one reports 1.
    # Both answer the ticket. A real agent built the prospective one and lost
    # three facts to this assertion.

    _, warm = provider.delta(lambda: llm(rows))
    assert warm == 0, (
        f"an identical re-run made {warm} backend call(s); the ticket asks for a "
        "report of what was served from the cache, which presupposes a cache")

    # After an identical re-run the two readings agree: everything is cached,
    # nothing would be sent. That is where this can be graded without picking
    # an interpretation.
    warm_stats = cache_stats_of(llm)
    rate = read_field(warm_stats, "hit_rate", "hitrate", "cache_hit_rate",
                      default=None)
    warm_served = read_field(warm_stats, "hits", "cached", "cache_hits",
                             "from_cache", default=None)
    warm_sent = read_field(warm_stats, "misses", "sent", "cache_misses",
                           "to_backend", default=None)
    assert rate == pytest.approx(1.0) or warm_served == 1 or warm_sent == 0, (
        f"every row of the re-run came from the cache; reported {warm_stats!r}")
