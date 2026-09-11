"""g13 — hidden requirement r2: the corpus that cannot supply distractors, and the knobs.

    rule          a module-level `InsufficientDistractorsError(ValueError)` built with
                  chunk_id / requested / available, carrying exactly those three
                  attributes and exactly the documented message, raised out of the
                  document-set build
    scope         the check is up front and against the worst case — available =
                  len(chunks) - 1 versus distractors + 1, whatever the coin would say
                  — so it fires at p=1.0 too, before any randomness is spent, and
                  does not fire when the corpus is exactly big enough
    failure_behavior  `_RaftAnswer.__init__` validates p and then distractors as its
                  first statements, ahead of the base class, with plain ValueError and
                  the documented messages; the facade does not re-check
    exclusions    the facade's LIST branch drops blank entries before chunk ids are
                  assigned and renumbers the survivors from 0, keeping their text
                  verbatim; the str branch is untouched

Each measures one fact: `rule` never depends on when the check runs (its corpus is
too small under either policy), `scope` never reads the message or the class, and
`failure_behavior` and `exclusions` never build a document set at all.
"""
from __future__ import annotations

import pytest

from harness import read_field, require_feature

from test_open import (
    FIVE,
    MODEL,
    SpyRng,
    documents_of,
    head_sampler,
    make_answer,
    make_chunks,
    raft_name,
    require_raft,
    stub_pair,
)

# Four chunks: three candidates other than the oracle, one short of the four a
# distractors=3 document set needs in the oracle-absent worst case.
SMALL = ["a", "b", "c", "d"]
THREE = ["a", "b", "c"]
RESPONSE = "resp"


def chunks_handed_to(stub_cls):
    """The chunk dataset the facade built and handed to the answer stage."""
    assert len(stub_cls.instances) == 1, "one answer generator per run"
    return stub_cls.instances[0].kwargs["chunks"]


# =============================================================================
# rule — the exception type, its attributes and its message
# =============================================================================
def test_rule__insufficient_distractors_error_names_the_chunk_and_the_shortfall():
    require_raft()

    error_cls = raft_name("InsufficientDistractorsError")
    assert isinstance(error_cls, type) and issubclass(error_cls, ValueError), (
        "InsufficientDistractorsError subclasses ValueError")

    built = error_cls(chunk_id=2, requested=4, available=3)
    assert (built.chunk_id, built.requested, built.available) == (2, 4, 3)
    assert str(built) == "chunk 2: requested 4 distractors, only 3 available"

    # And it is what escapes a build the corpus cannot serve. p=0.0 asks for
    # distractors + 1 = 4 documents out of the 3 chunks that are not the oracle,
    # so this call is short under any policy for when the check runs.
    gen = make_answer(SMALL, n=2, distractors=3, p=0.0, sampler=head_sampler,
                      rng=SpyRng(7))
    with pytest.raises(error_cls) as caught:
        gen.parse({"chunk_id": 2, "question": "Q"}, RESPONSE)

    escaped = caught.value
    assert (escaped.chunk_id, escaped.requested, escaped.available) == (2, 4, 3)
    assert str(escaped) == "chunk 2: requested 4 distractors, only 3 available"


# =============================================================================
# scope — checked up front, against the worst case, before any randomness
# =============================================================================
def test_scope__the_worst_case_is_checked_before_the_coin_is_flipped():
    require_raft()

    # p=1.0 means the coin always says "oracle present", a branch that needs only
    # 3 distractors out of the 3 available. The worst case still needs 4, so the
    # build fails deterministically rather than on whichever coin comes up.
    rng = SpyRng(7)
    gen = make_answer(SMALL, n=2, distractors=3, p=1.0, sampler=head_sampler, rng=rng)
    with pytest.raises(ValueError):
        gen.parse({"chunk_id": 2, "question": "Q"}, RESPONSE)

    assert rng.calls == [], (
        "the availability check runs before any draw; the rng was asked for "
        f"{rng.calls}")

    # ...and it is not over-eager: a corpus with exactly distractors + 1 other
    # chunks builds normally, oracle included.
    ok_rng = SpyRng(7)
    ok = make_answer(FIVE, n=2, distractors=3, p=1.0, sampler=head_sampler, rng=ok_rng)
    row = ok.parse({"chunk_id": 0, "question": "Q"}, RESPONSE)
    assert len(documents_of(row)) == 4
    assert ok_rng.calls.count("random") == 1


# =============================================================================
# failure_behavior — the knobs are validated first, p before distractors
# =============================================================================
def test_failure_behavior__the_numeric_knobs_are_rejected_before_the_base_class_runs():
    require_raft()

    error_cls = raft_name("InsufficientDistractorsError", required=False)

    def build(**kwargs):
        cls = raft_name("_RaftAnswer")
        return cls(chunks=make_chunks(THREE), model_name=MODEL, backend="litellm",
                   sampler=head_sampler, **kwargs)

    for kwargs, message in [
        (dict(p=1.5), "p must be in [0.0, 1.0], got 1.5"),
        (dict(p=-0.1), "p must be in [0.0, 1.0], got -0.1"),
        (dict(distractors=0), "distractors must be >= 1, got 0"),
        (dict(distractors=-2), "distractors must be >= 1, got -2"),
        # p is checked first, so it is the p message that comes back.
        (dict(p=1.5, distractors=0), "p must be in [0.0, 1.0], got 1.5"),
    ]:
        with pytest.raises(ValueError) as caught:
            build(**kwargs)
        assert str(caught.value) == message, f"for {kwargs}"
        if error_cls is not None:
            assert not isinstance(caught.value, error_cls), (
                "a bad knob is a plain ValueError; InsufficientDistractorsError "
                "is reserved for the corpus-size failure")

    # Both endpoints are legal, and one distractor is enough.
    assert build(p=0.0).p == 0.0
    assert build(p=1.0).p == 1.0
    assert build(distractors=1).distractors == 1

    # Placement, read through the base class: an unknown backend is the base
    # class's complaint, and our check pre-empts it.
    cls = raft_name("_RaftAnswer")
    with pytest.raises(ValueError) as base_only:
        cls(chunks=make_chunks(THREE), model_name=MODEL, backend="nope")
    assert "Unknown backend" in str(base_only.value)

    with pytest.raises(ValueError) as ours_first:
        cls(chunks=make_chunks(THREE), model_name=MODEL, backend="nope", p=1.5)
    assert str(ours_first.value) == "p must be in [0.0, 1.0], got 1.5", (
        "the knob check runs before super().__init__")

    # The facade does not re-check: a bad p survives construction there.
    Raft = raft_name("Raft")
    assert Raft(model="m", p=1.5).p == 1.5


# =============================================================================
# exclusions — the list branch drops blanks and renumbers
# =============================================================================
def test_exclusions__a_list_corpus_drops_blank_documents_and_renumbers_from_zero():
    require_raft()

    # A preservation-shaped clause ("the str branch is untouched") only counts
    # once the list branch really filters, and the facade seam it is measured
    # through has to exist at all.
    require_feature(
        "question_generator_cls" in raft_name("Raft").__dataclass_fields__,
        "the facade's question_generator_cls seam")

    StubQ, StubA = stub_pair()
    Raft = raft_name("Raft")
    Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA)(
        ["alpha", "", "  ", "\n", " bravo "])

    chunks = chunks_handed_to(StubA)
    assert len(chunks) == 2, "three wholly blank entries dropped"
    assert list(chunks["content"]) == ["alpha", " bravo "], (
        "survivors are stored verbatim, surrounding whitespace kept")
    assert list(chunks["chunk_id"]) == [0, 1], "survivors are renumbered from 0"

    # An all-blank corpus is an empty dataset here, and raises nothing.
    StubQ2, StubA2 = stub_pair()
    Raft(model="m", question_generator_cls=StubQ2, answer_generator_cls=StubA2)(
        ["", "   ", "\t\n"])
    empty = chunks_handed_to(StubA2)
    assert len(empty) == 0
    assert list(empty.column_names) == []

    # The str branch is untouched: one chunk under the default chunk_size.
    StubQ3, StubA3 = stub_pair()
    Raft(model="m", question_generator_cls=StubQ3, answer_generator_cls=StubA3)(
        "abcdefghij")
    text_chunks = chunks_handed_to(StubA3)
    assert list(text_chunks["content"]) == ["abcdefghij"]
    assert list(text_chunks["chunk_id"]) == [0]
