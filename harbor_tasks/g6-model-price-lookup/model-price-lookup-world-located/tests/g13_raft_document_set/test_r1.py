"""g13 — hidden requirement r1: the draw ledger and the unit the coin is drawn per.

    rule          a module-level mutable `RaftDrawStats` dataclass with exactly
                  `document_sets` then `with_oracle`, both defaulting to 0, and an
                  `oracle_rate` that answers 0.0 on an empty ledger; every
                  `_RaftAnswer` carries a fresh one as `self.stats`
    scope         the counters follow document-set BUILDS, not emitted rows: over
                  four `parse` calls one of which repeats, the ledger equals the
                  coins the rng was actually asked for, not the rows returned
    exclusions    the question is the unit the coin is drawn per — it is the third
                  positional argument of the memoised builder and part of its key,
                  so a repeated (chunk_id, question) replays without touching the
                  rng while a second question on one chunk gets its own coin
    observability the memoisation bound is `lru_cache(maxsize=512)`, and its
                  counters follow the builder's calls

Each measures one fact and only it: `rule` never runs a draw, `scope` compares the
ledger against the coins observed (whatever the cache key turns out to be, so a
wrong key cannot fail it), `exclusions` reads the coin log and the rows, and
`observability` reads `maxsize` plus the shape of the counters, never the exact
hit/miss split that the cache key decides.
"""
from __future__ import annotations

import dataclasses

import pytest

from harness import read_field

from test_open import (
    FIVE,
    SpyRng,
    documents_of,
    head_sampler,
    make_answer,
    raft_name,
    require_raft,
)

# The end-to-end fixture of the ticket: four parses on the five-chunk corpus,
# the last one repeating the first.
CALLS = [
    {"chunk_id": 0, "question": "Who?"},
    {"chunk_id": 0, "question": "What?"},
    {"chunk_id": 2, "question": "Who?"},
    {"chunk_id": 0, "question": "Who?"},
]
RESPONSE = "reasoning <ANSWER>: x"


def rate_of(stats):
    """`oracle_rate`, whether it is spelled as a method or as a property."""
    rate = read_field(stats, "oracle_rate")
    return rate() if callable(rate) else rate


def counts_of(gen):
    """The two counters, from the ledger object or straight off the generator.

    `scope` is about WHAT is counted, not about where the counters are parked or
    what the ledger type is called; those are `rule`'s business, so this reader
    accepts a generator that keeps plain counters just as readily.
    """
    holder = read_field(gen, "stats", "draw_stats", default=None)
    if holder is None:
        holder = gen
    builds = read_field(holder, "document_sets", "n_document_sets", "document_set_count", "builds")
    with_oracle = read_field(holder, "with_oracle", "n_with_oracle", "oracle_count")
    return builds, with_oracle


def run_fixture(rng):
    """The four-call fixture, driven by whatever rng the caller wants to watch."""
    gen = make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler, rng=rng)
    rows = [gen.parse(dict(call), RESPONSE) for call in CALLS]
    return gen, rows


# =============================================================================
# rule — the ledger type itself
# =============================================================================
def test_rule__a_mutable_raft_draw_stats_ledger_rides_on_every_answer_generator():
    require_raft()

    RaftDrawStats = raft_name("RaftDrawStats")
    assert dataclasses.is_dataclass(RaftDrawStats), "RaftDrawStats is a dataclass"

    fields = [f.name for f in dataclasses.fields(RaftDrawStats)]
    assert fields == ["document_sets", "with_oracle"], (
        f"exactly two fields, document_sets then with_oracle; got {fields}")

    fresh = RaftDrawStats()
    assert fresh == RaftDrawStats(document_sets=0, with_oracle=0), "both default to 0"
    assert read_field(fresh, "document_sets") == 0
    assert read_field(fresh, "with_oracle") == 0

    # An empty ledger reports 0.0 rather than dividing by zero.
    assert rate_of(fresh) == 0.0
    assert rate_of(RaftDrawStats(document_sets=4, with_oracle=1)) == 0.25
    assert rate_of(RaftDrawStats(document_sets=3, with_oracle=2)) == 2 / 3

    # Mutable, not frozen: the builder increments it in place.
    fresh.document_sets = 2
    fresh.with_oracle = 1
    assert rate_of(fresh) == 0.5

    # Every generator starts with its own, zeroed, ledger.
    gen = make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler)
    other = make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler)
    assert isinstance(read_field(gen, "stats"), RaftDrawStats)
    assert read_field(gen, "stats") == RaftDrawStats(document_sets=0, with_oracle=0)
    assert read_field(gen, "stats") is not read_field(other, "stats"), (
        "each generator keeps its own ledger, not one shared class attribute")


# =============================================================================
# scope — builds are counted, parses are not
# =============================================================================
def test_scope__the_ledger_counts_document_set_builds_not_parse_calls():
    require_raft()

    rng = SpyRng(7)
    gen, rows = run_fixture(rng)
    assert len(rows) == len(CALLS) == 4

    # What the generator actually built is visible in the coins it drew: one
    # coin per build that ran, and a build carries the oracle exactly when its
    # coin fell below p. This is read off the run rather than hard-coded, so an
    # implementation that memoises on a different key is still measured against
    # its own builds.
    coins = list(rng.drawn)
    builds = len(coins)
    with_oracle = sum(1 for coin in coins if coin < 0.5)
    assert builds < len(CALLS), (
        "the fourth call repeats the first, so at least one build should be "
        f"replayed rather than redrawn; the rng was asked for {builds} coins")

    counted_builds, counted_oracle = counts_of(gen)
    assert counted_builds == builds, (
        f"document_sets should count the {builds} builds that ran, not the "
        f"{len(CALLS)} parse calls; got {counted_builds}")
    assert counted_oracle == with_oracle, (
        f"with_oracle should count the {with_oracle} builds whose coin said the "
        f"oracle is present; got {counted_oracle}")

    # And the realised rate is those two counts, not the rate over rows.
    assert rate_of(read_field(gen, "stats", default=gen)) == pytest.approx(with_oracle / builds)


# =============================================================================
# exclusions — the coin is drawn per question, not per chunk
# =============================================================================
def test_exclusions__the_question_joins_the_memo_key_so_each_one_gets_its_own_coin():
    require_raft()

    rng = SpyRng(7)
    gen, rows = run_fixture(rng)

    # Four parse calls over three distinct (chunk_id, question) pairs: two
    # questions on chunk 0 and one on chunk 2, plus a repeat of the first.
    assert rng.calls.count("random") == 3, (
        "one coin per distinct (chunk_id, question): keying on the chunk alone "
        "draws 2, no memoisation at all draws 4; the log was "
        f"{rng.calls}")

    # The repeat replays the memoised document set verbatim.
    assert rows[3] == rows[0], "a repeated (chunk_id, question) replays its document set"

    # Two questions on the SAME chunk got independent coins and disagreed.
    assert read_field(rows[0], "oracle_present") is True
    assert read_field(rows[1], "oracle_present") is False
    assert documents_of(rows[1]) != documents_of(rows[0])

    # The builder takes the question third and positionally: asking it again for
    # the pair behind rows[0] is a cache hit that spends no further randomness.
    # (Reached directly because the memo key is only visible on the builder the
    # ticket names; `parse` is the entry point everything else is read through.)
    replay = gen._get_document_set(0, "alpha", "Who?")
    assert list(read_field(replay, "documents")) == documents_of(rows[0])
    assert rng.calls.count("random") == 3, "the replay drew no new coin"


# =============================================================================
# observability — the memoisation bound
# =============================================================================
def test_observability__the_builder_is_memoised_with_maxsize_512():
    require_raft()

    gen = make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler, rng=SpyRng(7))
    info = gen._get_document_set.cache_info()
    assert info.maxsize == 512, f"lru_cache(maxsize=512); got maxsize={info.maxsize}"
    assert (info.hits, info.misses, info.currsize) == (0, 0, 0), "nothing built yet"

    for call in CALLS:
        gen.parse(dict(call), RESPONSE)

    info = gen._get_document_set.cache_info()
    assert info.maxsize == 512, "the bound does not move once the cache is used"
    assert info.hits + info.misses == len(CALLS), (
        f"one lookup per parse call; got hits={info.hits} misses={info.misses}")
    assert info.currsize == info.misses, "every miss stored an entry; none was evicted"
    assert info.hits >= 1, "the repeated call was served from the cache"
