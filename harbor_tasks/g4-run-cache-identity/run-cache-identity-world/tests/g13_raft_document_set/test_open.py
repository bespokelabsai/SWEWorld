"""g13 — the openly stated feature: the Raft facade owns the knobs and the randomness.

The ticket states, and this file measures in one decisive test:

* a module-level frozen `RaftSampling` with exactly `sampler` then `rng`, both
  defaulting to `None`;
* `Raft` gaining `question_generator_cls` and `sampling` appended after
  `answer_generator_cls`, with the older fields' names and defaults untouched;
* `Raft.__call__` building both stages from the injectable classes and handing
  them exactly the keyword arguments the ticket lists — `n` to the question
  stage, `n`/`distractors`/`p`/`sampler`/`rng` to the answer stage, the last two
  even when they are `None`;
* `_RaftAnswer.__init__` taking `rng` and exposing `n`, `distractors`, `p`,
  `chunks`, `rng`, `sampler`, `formatter`;
* `parse` returning exactly the seven documented keys, with `instruction` built
  by `_ContextFormatter` from the emitted documents.

The doubles and builders live here because `test_r1.py` and `test_r2.py` drive
the same objects.

Nothing here builds a generator on the default backend: `backend=None` with an
OpenAI-shaped model name reaches `OpenAIOnlineRequestProcessor.__init__`, which
does a live `requests.post`. Every construction below passes `backend="litellm"`.
"""
from __future__ import annotations

import dataclasses
import random
from typing import Any, Dict, List, Optional

import pytest

from harness import read_field, surface

try:  # the module exists on an untouched checkout; the new names do not
    import datasets
    from bespokelabs.curator.blocks import raft as raft_mod
except Exception:  # pragma: no cover - reported by the tests, not at collection
    datasets = None
    raft_mod = None


MODEL = "gpt-4o-mini"
FIVE = ["alpha", "bravo", "charlie", "delta", "echo"]


# ---------------------------------------------------------------------------
# Resolving the names under test
# ---------------------------------------------------------------------------
def require_raft():
    """The block module itself; without it nothing below can be measured."""
    if raft_mod is None or datasets is None:
        pytest.fail("bespokelabs.curator.blocks.raft could not be imported")
    return raft_mod


def raft_name(name: str, required: bool = True):
    """A name the ticket spells out, from wherever the package exports it.

    The ticket names `blocks/raft.py`, but a re-export from `blocks/` or from
    `bespokelabs.curator` is the same fact, so all three are searched before a
    name counts as missing.
    """
    require_raft()
    holders: List[Any] = [raft_mod]
    for mod_path in ("bespokelabs.curator.blocks", "bespokelabs.curator"):
        try:
            holders.append(__import__(mod_path, fromlist=["_"]))
        except Exception:
            pass
    for holder in holders:
        found = getattr(holder, name, None)
        if found is not None:
            return found
    if required:
        pytest.fail(f"`{name}` is not exported by the curator blocks package; "
                    f"blocks.raft exposes {surface(raft_mod)}")
    return None


def has_name(name: str) -> bool:
    return raft_name(name, required=False) is not None


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------
class SpyRng(random.Random):
    """A `random.Random` that records which of its methods were asked for.

    A real subclass rather than a duck type, so an implementation that type
    checks its `rng` is not failed for it. `getrandbits` is redefined so that
    `Random.__init_subclass__` keeps `_randbelow_with_getrandbits`; without it,
    overriding `random()` reroutes `shuffle`/`sample` through `random()` and the
    log grows entries nobody asked for.
    """

    def __init__(self, seed: int = 7, coins: Optional[List[float]] = None,
                 shuffle_mode: str = "delegate", log: Optional[List[str]] = None):
        self.calls: List[str] = [] if log is None else log
        self.drawn: List[float] = []
        self.coins = None if coins is None else list(coins)
        self.shuffle_mode = shuffle_mode
        super().__init__(seed)

    def getrandbits(self, k):  # noqa: D102 - see the class docstring
        return super().getrandbits(k)

    def random(self):  # noqa: D102
        self.calls.append("random")
        value = self.coins.pop(0) if self.coins else super().random()
        self.drawn.append(value)
        return value

    def shuffle(self, x, *args, **kwargs):  # noqa: D102
        self.calls.append("shuffle")
        if self.shuffle_mode == "noop":
            return None
        if self.shuffle_mode == "reverse":
            x.reverse()
            return None
        return super().shuffle(x)

    def sample(self, population, k, *args, **kwargs):  # noqa: D102
        self.calls.append("sample")
        return super().sample(population, k, *args, **kwargs)


class SpySampler:
    """Records `(population, k)` and returns the head of the population."""

    def __init__(self, log: Optional[List[str]] = None):
        self.calls: List[Any] = []
        self.log = log

    def __call__(self, population, k):
        self.calls.append((list(population), k))
        if self.log is not None:
            self.log.append("sample")
        return list(population)[:k]


def head_sampler(population, k):
    return list(population)[:k]


class _StubGen:
    """A generator stage that records how the facade built it and is callable."""

    instances: List["_StubGen"] = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        type(self).instances.append(self)
        type(self).kw = kwargs

    def __call__(self, dataset):
        self.called_with = dataset
        return _StubResponse(dataset)


class _StubResponse:
    def __init__(self, dataset):
        self.dataset = dataset


def stub_pair():
    """Fresh question/answer stub classes, so instance logs never leak between tests."""
    q = type("StubQ", (_StubGen,), {"instances": []})
    a = type("StubA", (_StubGen,), {"instances": []})
    return q, a


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def make_chunks(contents: List[str]):
    require_raft()
    return datasets.Dataset.from_list(
        [{"chunk_id": i, "content": c} for i, c in enumerate(contents)]
    )


def make_answer(contents: List[str], **kwargs):
    """A `_RaftAnswer` over `contents`, never on the networked default backend."""
    cls = raft_name("_RaftAnswer")
    return cls(chunks=make_chunks(contents), model_name=MODEL, backend="litellm", **kwargs)


def as_indices(population, contents: List[str]) -> List[int]:
    """A sampler population as chunk indices, whether it held indices or content.

    The ticket fixes the population as "the chunks other than `chunk_id`, in
    ascending index order"; whether those are passed as indices or as their
    content is an implementation choice, and both read back the same here.
    """
    out = []
    for item in population:
        if isinstance(item, int):
            out.append(item)
        elif isinstance(item, str) and item in contents:
            out.append(contents.index(item))
        elif isinstance(item, dict) and "chunk_id" in item:
            out.append(item["chunk_id"])
        else:
            out.append(item)
    return out


def documents_of(row) -> List[str]:
    """The emitted document list, out of a parsed row."""
    context = read_field(row, "context")
    return list(read_field(context, "sentences")[0])


# =============================================================================
# The openly stated feature
# =============================================================================
def test_open_feature__the_facade_owns_the_knobs_and_the_randomness_it_hands_down():
    require_raft()

    # ---- RaftSampling: frozen, exactly (sampler, rng), both defaulting to None
    RaftSampling = raft_name("RaftSampling")
    assert dataclasses.is_dataclass(RaftSampling)
    assert [f.name for f in dataclasses.fields(RaftSampling)] == ["sampler", "rng"]
    assert RaftSampling() == RaftSampling(sampler=None, rng=None)
    assert RaftSampling().sampler is None and RaftSampling().rng is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        RaftSampling().sampler = head_sampler

    # ---- Raft's fields: two appended, the old ones untouched
    Raft = raft_name("Raft")
    fields = list(Raft.__dataclass_fields__)
    assert fields[-3:] == ["answer_generator_cls", "question_generator_cls", "sampling"]
    assert fields[:5] == ["model", "distractors", "chunk_size", "n_questions", "p"]
    defaults = Raft(model="m")
    assert (defaults.distractors, defaults.chunk_size, defaults.n_questions, defaults.p) == (3, 1000, 2, 0.8)
    assert defaults.question_generator_cls is None and defaults.sampling is None

    # ---- __call__ hands each stage exactly the documented keyword arguments
    StubQ, StubA = stub_pair()
    rng = random.Random(1)
    Raft(
        model="m",
        distractors=2,
        n_questions=1,
        chunk_size=1024,
        p=0.95,
        question_generator_cls=StubQ,
        answer_generator_cls=StubA,
        sampling=RaftSampling(sampler=head_sampler, rng=rng),
    )(["a", "b", "c", "d"])

    assert len(StubQ.instances) == 1 and len(StubA.instances) == 1
    q, a = StubQ.instances[0], StubA.instances[0]
    assert q.args == () and a.args == (), "both stages are built by keyword"
    assert set(q.kwargs) == {"model_name", "backend", "backend_params", "generation_params", "n"}
    assert q.kwargs["model_name"] == "m" and q.kwargs["n"] == 1
    assert set(a.kwargs) == {
        "chunks", "model_name", "backend", "backend_params", "generation_params",
        "n", "distractors", "p", "sampler", "rng",
    }
    assert (a.kwargs["n"], a.kwargs["distractors"], a.kwargs["p"]) == (1, 2, 0.95)
    assert a.kwargs["sampler"] is head_sampler and a.kwargs["rng"] is rng
    assert list(a.kwargs["chunks"]["content"]) == ["a", "b", "c", "d"]

    # sampling=None still forwards both keys, carrying None
    StubQ2, StubA2 = stub_pair()
    Raft(model="m", question_generator_cls=StubQ2, answer_generator_cls=StubA2)(["a", "b", "c", "d"])
    assert StubA2.instances[0].kwargs["sampler"] is None
    assert StubA2.instances[0].kwargs["rng"] is None

    # ---- _RaftAnswer.__init__ takes rng and keeps the documented attributes
    own_rng = random.Random(7)
    gen = make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler, rng=own_rng)
    assert (gen.n, gen.distractors, gen.p) == (2, 2, 0.5)
    assert gen.rng is own_rng and gen.sampler is head_sampler
    assert list(gen.chunks["content"]) == FIVE
    assert gen.formatter(["x", "y"]) == "<DOCUMENT>x</DOCUMENT>\n<DOCUMENT>y</DOCUMENT>\n"

    # ---- parse returns exactly the seven documented keys
    row = gen.parse({"chunk_id": 0, "question": "Q?"}, "reasoning <ANSWER>: x")
    assert set(row) == {
        "question", "cot_answer", "oracle_document", "context", "instruction",
        "oracle_present", "oracle_index",
    }
    assert row["question"] == "Q?"
    assert row["cot_answer"] == "reasoning <ANSWER>: x"
    assert row["oracle_document"] == "alpha"
    docs = documents_of(row)
    assert len(docs) == 3
    assert row["context"]["title"] == [["placeholder_title"] * 3]
    assert row["instruction"] == "".join(f"<DOCUMENT>{d}</DOCUMENT>\n" for d in docs) + "\nQ?"
    assert isinstance(row["oracle_present"], bool) and isinstance(row["oracle_index"], int)
