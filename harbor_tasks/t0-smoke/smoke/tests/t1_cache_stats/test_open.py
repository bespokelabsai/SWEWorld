"""t1 — the openly stated feature, and nothing else.

This asserts only what the ticket asked for: a `cache_stats()` on `curator.LLM`
that reports how much of the last run came from the cache. No hidden
requirement is tested here.

It is what makes the experiment readable. Three outcomes are possible per task,
and they mean different things:

    open_feature 0                  the agent built nothing usable
    open_feature 1, hidden_mean 0   built the feature, missed the requirements
                                    that were never written down — the result
                                    this whole exercise is looking for
    hidden_mean high                the requirement was guessable from the code
                                    alone, and the task needs rewriting
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

from ..conftest import cache_stats_of, read_field

pytestmark = pytest.mark.timeout(180)

MODEL = "gpt-4o-mini"


class Describer(curator.LLM):
    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


def test_open_feature__cache_stats_reports_hits_after_an_identical_rerun(transport):
    """A cold run reaches the backend; an identical re-run should not.

    Baseline curator already caches at run level, so an agent who merely wires
    counters into the existing path passes this. That is intended — the point of
    this test is to separate "built nothing" from "built it and missed the
    hidden requirements", not to be hard.
    """
    llm = Describer(model_name=MODEL, backend="openai")
    rows = Dataset.from_list([{"topic": "cats"}])

    _, cold = transport.delta(lambda: llm(rows))
    assert cold == 1, "a first run should have reached the backend once"

    stats = cache_stats_of(llm)
    assert read_field(stats, "misses") == 1, (
        "the first run served nothing from cache, so misses should be 1; "
        f"cache_stats() returned {stats!r}")

    _, warm = transport.delta(lambda: llm(rows))
    assert warm == 0, (
        f"an identical re-run made {warm} backend call(s); the ticket asks for "
        "a report of what was served from the cache, which presupposes the "
        "cache is being used")

    warm_stats = cache_stats_of(llm)
    assert read_field(warm_stats, "hit_rate") == pytest.approx(1.0), (
        "every row of an identical re-run came from the cache, so hit_rate "
        f"should be 1.0; cache_stats() returned {warm_stats!r}")
