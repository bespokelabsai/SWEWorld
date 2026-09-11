# RAFT document-set policy: owned knobs, owned randomness, one authoritative oracle index

## Target

**Files that change**

- `src/bespokelabs/curator/blocks/raft.py` — the only production file. Everything below lives
  in it: `_RaftAnswer.__init__`, `_RaftAnswer.parse`, `_RaftAnswer._get_document_set`, the
  `Raft` dataclass and `Raft.__call__`, plus two new module-level names.
- `tests/unit/blocks/test_raft.py` — new file (there is currently no unit test for this block;
  `tests/unit/` exists, `tests/unit/blocks/` does not).

**Existing machinery that may be REUSED (do not re-invent)**

- `DocumentSet = namedtuple("DocumentSet", ["documents", "oracle_index", "oracle_present"])`
  (`raft.py:73`) — the return type stays exactly this namedtuple, same three field names, same
  order.
- `_SamplingStrategy` Protocol (`raft.py:69-71`) — `__call__(self, population: List[T], k: int) -> List[T]`.
- `_ContextFormatter` (`raft.py:76-81`) and its `document_tag="DOCUMENT"` default, which
  renders `"".join(f"<DOCUMENT>{doc}</DOCUMENT>\n" ...)`.
- `chunk_text` (`raft.py:181`) and the `chunk_size` knob — unchanged, out of scope.
- `_DEFAULT_QUESTION_PROMPT` / `_DEFAULT_ANSWER_PROMPT` — unchanged, out of scope.
- `_RaftQuestion.__init__(*args, n: int = 5, **kwargs)` (`raft.py:58`) — its `n` kwarg already
  exists; it just is never passed.
- `functools.lru_cache` wrapping of the bound method (`raft.py:109`) — the technique stays; the
  key and the size change.
- `curator.LLM.__init__(model_name, response_format, batch, backend, generation_params, backend_params, system_prompt)`
  (`llm/llm.py:68`) — the `**kwargs` passthrough in both generators is unchanged.

**What must be BUILT**

- `InsufficientDistractorsError` — new exception class (P10).
- `RaftSampling` — new frozen dataclass (P3).
- `Raft.question_generator_cls` and `Raft.sampling` — new dataclass fields (P2, P3).
- `_RaftAnswer.rng` — new constructor parameter and attribute (P4).
- A rewritten `_get_document_set` with a third parameter and a different draw protocol
  (P5, P6, P7, P9, P10).

**Latent bugs in the area, with lines — this ticket fixes all five**

1. `raft.py:169` `oracle_index = shuffled_indices[0]` reads the *original* index of whatever
   landed in slot 0, not the oracle's new slot. Every example where the oracle did not land
   first ships an `oracle_index` that disagrees with the `instruction` built at line 130.
2. `raft.py:221` and `raft.py:225-227` forward none of `distractors`, `n_questions`, `p`;
   `tests/integrations/test_blocks.py:31` passes three inert arguments.
3. `raft.py:152, 165, 175` read module-level `random`, so the injectable `sampler`
   (`raft.py:106`) cannot make a run reproducible.
4. `raft.py:109` caches on `(chunk_id, oracle_document)`, making `p` a per-chunk coin while
   `raft.py:96` documents it as per-example.
5. `raft.py:139` re-decides in `parse` what `_get_document_set` already decided at
   `raft.py:176`.

Not fixed here (noted, out of scope): `Raft.__call__` is annotated `-> datasets.Dataset` but
returns the `CuratorResponse` from `answer_gen(questions)` (`raft.py:214, 228-229`);
`tests/integrations/test_blocks.py:32` depends on that, so it stays.

**Python / dependencies**

Python `^3.10` (`pyproject.toml:26`). `datasets ^3.0.2`, `pydantic >=2.9.2`, stdlib `random`,
`functools`, `dataclasses`, `collections.namedtuple`. No new dependency.

**Test-construction constraint.** Never build `_RaftQuestion`/`_RaftAnswer` with the default
backend: `backend=None` plus an OpenAI-shaped model name reaches
`OpenAIOnlineRequestProcessor.__init__`, which does a live `requests.post` via
`get_header_based_rate_limits()`
(`request_processor/online/openai_online_request_processor.py:101-103`). Use
`backend="litellm"` (`litellm_online_request_processor.py:54-63` touches no network and defers
rate limits), a stub subclass, or `__new__`. All literals below were produced with
`_RaftAnswer(chunks=..., model_name="gpt-4o-mini", backend="litellm", ...)`.

## The API

```python
class InsufficientDistractorsError(ValueError):
    def __init__(self, chunk_id: ChunkId, requested: int, available: int) -> None: ...
    chunk_id: ChunkId       # the chunk whose document set could not be built
    requested: int          # always self.distractors + 1
    available: int          # len(chunks) - 1
    # str(exc) == f"chunk {chunk_id}: requested {requested} distractors, only {available} available"


@dataclass(frozen=True)
class RaftSampling:
    sampler: Optional[_SamplingStrategy] = None
    rng: Optional[random.Random] = None


class _RaftAnswer(curator.LLM):
    def __init__(
        self,
        chunks: datasets.Dataset,
        *args,
        n: int = 5,
        distractors: int = 5,
        p: float = 0.8,
        sampler: Optional[_SamplingStrategy] = None,
        rng: Optional[random.Random] = None,
        **kwargs,
    ) -> None: ...

    # attributes after __init__
    n: int
    distractors: int
    p: float
    chunks: datasets.Dataset
    rng: random.Random                 # rng if rng is not None else random.Random()
    sampler: _SamplingStrategy         # sampler if sampler is not None else self.rng.sample
    formatter: _ContextFormatter
    _get_document_set: "functools._lru_cache_wrapper"   # maxsize=512, wraps the bound method

    def prompt(self, input: dict) -> str: ...           # unchanged

    def parse(self, input: dict, response: str) -> Dict[str, Any]: ...

    def _get_document_set(
        self, chunk_id: ChunkId, oracle_document: Content, question: Question
    ) -> DocumentSet: ...
```

`parse` return shape, field by field:

| key | type | value |
|---|---|---|
| `question` | `str` | `input["question"]` verbatim |
| `cot_answer` | `str` | `response` verbatim |
| `oracle_document` | `str` | `self.chunks[input["chunk_id"]]["content"]` |
| `context` | `Dict[str, List[List[str]]]` | `{"title": [["placeholder_title"] * len(docs)], "sentences": [docs]}` where `docs is doc_set.documents` |
| `instruction` | `str` | `self.formatter(doc_set.documents) + "\n" + input["question"]` |
| `oracle_present` | `bool` | `doc_set.oracle_present` verbatim |
| `oracle_index` | `int` | `doc_set.oracle_index` verbatim (no re-derivation) |

`DocumentSet` fields: `documents: List[str]`, `oracle_index: int`, `oracle_present: bool`.

```python
@dataclass
class Raft:
    model: str
    distractors: int = 3
    chunk_size: int = 1000
    n_questions: int = 2
    p: float = 0.8
    backend: str | None = None
    backend_params: dict | None = None
    generation_params: dict | None = None
    answer_generator_cls: type | None = None      # existing field, keeps its position
    question_generator_cls: type | None = None    # new, appended
    sampling: RaftSampling | None = None          # new, appended

    def __call__(self, text: str | List[str]) -> datasets.Dataset: ...
```

`Raft.__call__` constructs the two generators with exactly these keyword arguments:

```python
question_cls(model_name=self.model, backend=self.backend, backend_params=self.backend_params,
             generation_params=self.generation_params, n=self.n_questions)

answer_cls(chunks=chunks, model_name=self.model, backend=self.backend,
           backend_params=self.backend_params, generation_params=self.generation_params,
           n=self.n_questions, distractors=self.distractors, p=self.p,
           sampler=sampling.sampler, rng=sampling.rng)
```

where `question_cls = self.question_generator_cls or _RaftQuestion`,
`answer_cls = self.answer_generator_cls or _RaftAnswer`,
`sampling = self.sampling if self.sampling is not None else RaftSampling()`.

## Parts

### P1 — The facade's knobs are authoritative

**Behaviour.** `Raft.__call__` forwards `n_questions` to the question generator as `n`, and
forwards `n_questions` (as `n`), `distractors` and `p` to the answer generator, always, as
keyword arguments. The generators' own defaults (`_RaftQuestion(n=5)`, `_RaftAnswer(n=5,
distractors=5, p=0.8)`) survive only for direct construction; a `Raft(...)` run never uses
them. `n` is forwarded to the answer generator too, even though `_RaftAnswer` does not read it.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Generators own the policy.* Leave `__call__` as it is and delete `distractors`,
   `n_questions`, `p` from the `Raft` dataclass, treating them as documentation drift — the
   facade's job is to pick a model and wire two stages together, and the sampling numbers
   belong to the component that samples.
2. *Forward only what is read.* Forward `distractors` and `p` to `_RaftAnswer` and
   `n_questions` to `_RaftQuestion`, but not `n` to `_RaftAnswer`, since `_RaftAnswer.n` is a
   dead attribute — passing a value nothing reads is noise.
3. *Forward through `generation_params`.* Merge the knobs into the `generation_params` dict
   already threaded to both generators, keeping the constructor signatures untouched.

**The observable.** With stub generator classes recording their kwargs,
`Raft(model="m", distractors=2, n_questions=1, chunk_size=1024, p=0.95,
question_generator_cls=StubQ, answer_generator_cls=StubA)(["a","b","c","d"])` gives
`StubQ.kw["n"] == 1`, `StubA.kw["n"] == 1`, `StubA.kw["distractors"] == 2`,
`StubA.kw["p"] == 0.95`. Under alternative 1 all four are absent (`KeyError`); under
alternative 2 `StubA.kw` has no `"n"`; under alternative 3 they arrive inside
`generation_params`.

**Arbitrary:** policy with no local evidence — nothing in `raft.py` says which side owns the
sampling numbers, and both readings are coherent. (The `n`-to-`_RaftAnswer` clause is the part
a reader of the code would most likely drop.)

### P2 — `question_generator_cls`, the symmetric seam

**Behaviour.** `Raft` gains a field spelled exactly `question_generator_cls: type | None = None`,
appended *after* `answer_generator_cls`, and `__call__` builds the question stage from
`self.question_generator_cls or _RaftQuestion` — the same `or`-fallback shape already used at
`raft.py:224` for the answer side.

**Alternatives a competent engineer would plausibly choose instead.**
1. *One seam for both.* A single `generator_cls_overrides: dict | None = None` mapping
   `"question"`/`"answer"` to classes, so the facade grows one field rather than two.
2. *No seam.* Leave the question stage hard-wired to `_RaftQuestion`; the ticket is about
   sampling, and the question generator does no sampling, so it needs no injection point.
3. *A different spelling.* `question_cls`, `question_generator`, `question_llm_cls` — all
   natural names for the same field.

**The observable.** `"question_generator_cls" in Raft.__dataclass_fields__` is `True`;
`Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA)(["a","b","c","d"])`
constructs exactly one `StubQ` and never touches `_RaftQuestion`. Field order:
`list(Raft.__dataclass_fields__)[-3:] == ["answer_generator_cls", "question_generator_cls", "sampling"]`.

**Arbitrary:** an invented name — the exact spelling and its position in the dataclass are
not recoverable from the file.

### P3 — `RaftSampling`, the randomness bundle on the facade

**Behaviour.** A new module-level `@dataclass(frozen=True) class RaftSampling` with exactly two
fields, `sampler: Optional[_SamplingStrategy] = None` and `rng: Optional[random.Random] = None`,
both defaulting to `None`. `Raft` gains `sampling: RaftSampling | None = None` (last field);
`__call__` resolves `sampling = self.sampling if self.sampling is not None else RaftSampling()`
and forwards `sampler=sampling.sampler, rng=sampling.rng` to the answer generator on every run,
including when both are `None`.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Two flat fields.* `Raft(sampler=..., rng=...)` — no wrapper type; fewer names, one less
   import for callers.
2. *A seed instead of objects.* `Raft(seed: int | None = None)` and let `_RaftAnswer` build
   `random.Random(seed)`, which is the shape most data-generation libraries expose.
3. *Conditional forwarding.* Pass `sampler`/`rng` only when the caller supplied them, so a
   custom `answer_generator_cls` that predates this change keeps working.

**The observable.** `RaftSampling()` equals `RaftSampling(sampler=None, rng=None)` and is
frozen (`dataclasses.fields(RaftSampling)` has exactly the names `("sampler", "rng")`;
`RaftSampling().sampler = x` raises `FrozenInstanceError`). With
`rng = random.Random(1)` and
`Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA,
sampling=RaftSampling(sampler=head_sampler, rng=rng))(["a","b","c","d"])`:
`StubA.kw["sampler"] is head_sampler` and `StubA.kw["rng"] is rng`. With `sampling=None`,
`StubA.kw["sampler"] is None and StubA.kw["rng"] is None` — the keys are present (alternative 3
omits them, raising `KeyError`).

**Arbitrary:** an invented name — `RaftSampling`, its two field names, its frozenness, and the
always-forward rule.

### P4 — The rng owns the default sampler

**Behaviour.** `_RaftAnswer.__init__` gains `rng: Optional[random.Random] = None` and sets
`self.rng = rng if rng is not None else random.Random()`, then
`self.sampler = sampler if sampler is not None else self.rng.sample`. Every draw in
`_get_document_set` goes through `self.rng` or `self.sampler`; the module-level `random` is
read nowhere in the class. Consequence: injecting only `rng` is sufficient for full
reproducibility, and injecting only `sampler` still leaves ordering under `self.rng`.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Keep the current default.* `self.sampler = sampler or random.sample` (`raft.py:106`
   verbatim) and add `self.rng` beside it — a caller who wants determinism injects both.
2. *Sampler-only.* Route ordering through the sampler as well — e.g. shuffle by
   `self.sampler(documents, len(documents))` — so there is exactly one injection point and no
   `rng` parameter at all.
3. *Seed parameter.* `_RaftAnswer(..., seed: int | None = None)` building the `Random`
   internally.

**The observable.** With `rng = SpyRng(7)` (a duck-typed recorder delegating to
`random.Random(7)`, exposing `random`/`shuffle`/`sample`) and **no** `sampler` argument, one
uncached `_get_document_set(0, "alpha", "Q1")` on the five-chunk fixture leaves
`rng.calls == ["random", "sample", "shuffle"]` — the `"sample"` entry appears only if the
default sampler is bound to the injected rng. Under alternative 1 the log is
`["random", "shuffle"]`; under alternative 2 there is no `"random"` entry at all. Additionally,
two generators built with `rng=random.Random(7)` and no sampler return equal `DocumentSet`s.

**Arbitrary:** policy with no local evidence — the code says `sampler or random.sample`; that
the rng should *supply* the default sampler is a decision nothing in the file suggests.

### P5 — The draw protocol: coin, then sample, then one shuffle, in both branches

**Behaviour.** Each uncached `_get_document_set` call performs, in this order: (a) the
availability check of P10, which consumes no randomness; (b) exactly one `self.rng.random()`,
compared `< self.p` to set `oracle_present`; (c) exactly one `self.sampler(available_indices, k)`
call, with `k = self.distractors` when the oracle is present and `k = self.distractors + 1`
when it is absent, `available_indices` being `[i for i in range(len(self.chunks)) if i != chunk_id]`
in ascending order; (d) exactly one `self.rng.shuffle(...)` over the assembled list — in the
oracle-absent branch too. The two branches therefore consume the same shape of rng stream.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Sample first, coin second* — draw `distractors + 1` indices once, then flip the coin and
   drop the last index if the oracle is included; one sampler call for both branches, and the
   coin no longer perturbs which distractors you get.
2. *No shuffle when the oracle is absent* — `random.sample` already returns an unordered
   subset, so shuffling it again is a no-op statistically; drop the call (this is what a reader
   cleaning up `raft.py:175` would most likely do).
3. *Shuffle only the distractors, then place the oracle* — one shuffle over the distractors and
   a separate `rng.randrange(len(documents))` for the oracle's slot.

**The observable.** With a spy sampler recording `(population, k)` and `SpyRng`:
`p=1.0` on the five-chunk fixture, `chunk_id=0` → sampler calls `[([1, 2, 3, 4], 2)]`;
`p=0.0`, `chunk_id=0` → `[([1, 2, 3, 4], 3)]`. With the default (rng-bound) sampler and
`p=0.0`, `rng.calls == ["random", "sample", "shuffle"]` — alternative 2 gives
`["random", "sample"]`, alternative 1 gives a sampler `k` of `3` in *both* branches,
alternative 3 adds a fourth entry.

**Arbitrary:** policy with no local evidence — "the absent branch spends the same rng
operations as the present branch" is a stream-symmetry rule, and the natural clean-up deletes
the shuffle instead.

### P6 — The oracle is appended last, then shuffled once

**Behaviour.** In the oracle-present branch the pre-shuffle list is built distractors-first, in
sampler order, with the oracle document **appended at the end**; then the single
`self.rng.shuffle` of P5 permutes it. (The current code prepends the oracle at `raft.py:156`.)
For a given rng state and sampler this fixes one specific permutation, not merely one specific
distribution.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Oracle first* — `documents = [oracle_document]` then extend with distractors, exactly as
   `raft.py:156-160` does today. Keeping it is the default action of anyone editing this
   function.
2. *Oracle at a drawn index* — build the distractor list, shuffle it, then
   `documents.insert(self.rng.randrange(len(documents) + 1), oracle_document)`, which reads
   more directly as "randomise the oracle's position".

**The observable.** Five chunks `["alpha","bravo","charlie","delta","echo"]`, `distractors=2`,
`p=1.0`, `sampler = lambda pop, k: list(pop)[:k]`, and an rng whose `random()` returns `0.0`
and whose `shuffle` is a no-op. Then
`parse({"chunk_id": 0, "question": "Q"}, "resp")["context"]["sentences"][0] ==
["bravo", "charlie", "alpha"]`. Alternative 1 yields `["alpha", "bravo", "charlie"]`;
alternative 2 yields `["alpha", "bravo", "charlie"]` as well (insert at index 0 under a no-op
rng) and additionally consumes an extra rng call.

**Arbitrary:** a deliberate departure — the surrounding code plainly puts the oracle first, so
reading it leads you the wrong way.

### P7 — `oracle_index` is the oracle's slot in the emitted documents, tracked by identity

**Behaviour.** When the oracle is present, `oracle_index` is the position of the oracle
document *in the list returned as `DocumentSet.documents`* — the same list the context is
formatted from at `raft.py:125`. It is computed by carrying a per-slot marker through the
shuffle (e.g. shuffling `(document, is_oracle)` pairs and reading the marker's index), **not**
by searching the shuffled list for the oracle's text. When a distractor chunk has content
identical to the oracle's, the reported index is the oracle's own slot, not the first
text match.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Search by value* — `oracle_index = documents.index(oracle_document)` after the shuffle. The
   shortest correct-looking fix, and correct except on duplicate chunk content.
2. *Keep the pre-shuffle index* — leave `shuffled_indices[0]` (`raft.py:169`) or report the
   oracle's index in `self.chunks` (i.e. `chunk_id`), reading `oracle_index` as "which chunk is
   the oracle" rather than "where is it in the context".

**The observable.** Chunks `["same", "same", "other", "third"]` (chunk 0 and chunk 1 share
content), `distractors=2`, `p=1.0`, head-sampler, no-op-shuffle rng, `chunk_id=0`. Then
`parse(...)["context"]["sentences"][0] == ["same", "other", "same"]` and
`parse(...)["oracle_index"] == 2`. Alternative 1 gives `0`; alternative 2 gives `0` (the
pre-shuffle slot 0 / chunk id).

**Arbitrary:** policy with no local evidence for the duplicate-content tie-break — the
underlying index fix itself is derivable from the `# Track where oracle ended up` comment at
`raft.py:169` and the context build at `raft.py:125`, and is honestly not hidden material; only
the identity-tracking rule is.

### P8 — `parse` reports the document set verbatim; `_get_document_set` is the sole decider

**Behaviour.** `parse` copies `doc_set.oracle_index` and `doc_set.oracle_present` into the row
unchanged. The conditional at `raft.py:139` (`... if doc_set.oracle_present else -1`) is
removed: the `-1` sentinel is produced in exactly one place, the oracle-absent branch of
`_get_document_set`. If a `DocumentSet` says `oracle_present=False, oracle_index=2`, the row
says `oracle_index=2`.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Keep the guard* — `doc_set.oracle_index if doc_set.oracle_present else -1`, defensive and
   harmless-looking; this is what `raft.py:139` already says, so it is the default outcome of
   not touching the line.
2. *Normalise the other way* — have `parse` assert consistency and raise `ValueError` when
   `oracle_present is False and oracle_index != -1`, on the grounds that an inconsistent
   `DocumentSet` is a bug worth surfacing.

**The observable.** Replace the instance's `_get_document_set` with
`lambda chunk_id, oracle_document, question: DocumentSet(documents=["x","y","z"],
oracle_index=2, oracle_present=False)`, then
`parse({"chunk_id": 0, "question": "Q?"}, "resp")` returns `oracle_index == 2`,
`oracle_present is False`, and
`instruction == "<DOCUMENT>x</DOCUMENT>\n<DOCUMENT>y</DOCUMENT>\n<DOCUMENT>z</DOCUMENT>\n\nQ?"`.
Alternative 1 returns `-1`; alternative 2 raises `ValueError`.

**Arbitrary:** a deliberate departure — the file already contains the guard, so the code leads
a reader to keep it.

### P9 — The oracle coin is per question: cache key `(chunk_id, oracle_document, question)`, `maxsize=512`

**Behaviour.** `_get_document_set` takes a third positional parameter `question: Question`,
which participates in the `lru_cache` key and in nothing else; `parse` calls
`self._get_document_set(chunk_id, oracle_document, question)` positionally in that order. The
cache is `functools.lru_cache(maxsize=512)` over the bound method. The coin of P5 is therefore
drawn once per `(chunk_id, question)` pair — repeating the same question on the same chunk
replays the memoised document set without touching the rng — and two different questions drawn
from one chunk get independent coins.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Drop the cache.* "Per-example probability" (`raft.py:96`) means a fresh draw on every
   `parse` call; memoisation is what broke it, so delete the wrapper at `raft.py:109`. Then a
   repeated `(chunk_id, question)` re-draws and can return a different document set.
2. *Keep the two-argument key.* Leave `raft.py:109` and its `maxsize=128` alone and instead
   change the docstring to say "per chunk" — one document set per chunk is arguably the point
   of a RAFT corpus.
3. *Cache with a different bound* — `maxsize=None`, or `maxsize=len(chunks)`, or `1024`.

**The observable.** Five-chunk fixture, head-sampler, `SpyRng(7)`. Call
`_get_document_set(0,"alpha","Q1")`, `(0,"alpha","Q2")`, `(0,"alpha","Q1")`,
`(1,"bravo","Q1")`. Then `_get_document_set.cache_info() ==
CacheInfo(hits=1, misses=3, maxsize=512, currsize=3)` and
`rng.calls.count("random") == 3`. Alternative 1 gives `hits=0, misses=4` (or no `cache_info`
at all) and four coins; alternative 2 gives `hits=1, misses=2`, `maxsize=128`, two coins;
alternative 3 differs on `maxsize`.

**Arbitrary:** a chosen value (`512`) plus a policy with no local evidence (the question is the
unit the coin is drawn per, and it enters the key while affecting nothing else).

### P10 — `InsufficientDistractorsError`, checked up front against `distractors + 1`

**Behaviour.** Before any randomness is consumed, `_get_document_set` computes
`available = len(self.chunks) - 1` (the chunks other than `chunk_id`) and
`requested = self.distractors + 1` — the oracle-absent worst case, **regardless of how the coin
would land** — and raises `InsufficientDistractorsError(chunk_id=chunk_id, requested=requested,
available=available)` when `available < requested`. The exception subclasses `ValueError`,
carries the three attributes `chunk_id`, `requested`, `available`, and its `str()` is exactly
`f"chunk {chunk_id}: requested {requested} distractors, only {available} available"`. So a
corpus with `len(chunks) - 1 == distractors` fails on every chunk, deterministically, instead
of failing on whichever chunks happen to draw the absent branch.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Let it surface.* Do nothing; `random.sample` already raises
   `ValueError("Sample larger than population or is negative")` when `k` is too large, and a
   custom sampler raises whatever it likes. This is what the code does today.
2. *Clamp.* `k = min(k, len(available_indices))` and return a smaller document set, so small
   corpora and unit fixtures keep working.
3. *Check lazily, per branch.* Validate against the count this call actually needs
   (`distractors` when the oracle is present, `distractors + 1` when it is not), which fails
   only when it must.

**The observable.** Chunks `["a","b","c","d"]`, `distractors=3`, `p=1.0` (the coin says
"oracle present", which needs only 3 of the 3 available distractors), head-sampler,
`SpyRng(7)`, `chunk_id=2`. Then `parse({"chunk_id": 2, "question": "Q"}, "resp")` raises
`InsufficientDistractorsError`; `isinstance(exc, ValueError)` is `True`;
`(exc.chunk_id, exc.requested, exc.available) == (2, 4, 3)`;
`str(exc) == "chunk 2: requested 4 distractors, only 3 available"`; and `rng.calls == []`.
Alternative 1 returns a normal `DocumentSet` here (and raises plain `ValueError` only under
`p=0.0`); alternative 2 returns a 3-document set; alternative 3 returns normally at `p=1.0`.

**Arbitrary:** an invented name (`InsufficientDistractorsError`, its three attributes, its exact
message) plus a chosen policy (validate the worst case up front, so the failure does not depend
on the coin).

### P11 — `RaftDrawStats`, the draw ledger the generator keeps on itself

**Behaviour.** A new module-level `@dataclass class RaftDrawStats` (mutable, not frozen) with
exactly two fields in this order, `document_sets: int = 0` and `with_oracle: int = 0`, plus one
method `oracle_rate(self) -> float` returning `self.with_oracle / self.document_sets`, or
`0.0` when `document_sets == 0`. `_RaftAnswer.__init__` sets `self.stats = RaftDrawStats()`
(after `self.formatter`), and every *uncached* `_get_document_set` build increments
`document_sets` by one, and `with_oracle` by one when the coin of P5 said the oracle is
present. A cache hit (P9) increments nothing, and a build that dies on the availability check
of P10 increments nothing — the counters count document sets that exist. Nothing reads
`stats`; it is there so a run can be asked afterwards what oracle rate it actually realised,
which for small `n_questions` drifts a long way from `p`.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No ledger at all.* Nothing in the file counts anything today, and a caller who wants the
   realised rate can compute it from the emitted `oracle_present` column of the dataset.
2. *Plain counters.* Two integer attributes `self.n_document_sets` / `self.n_with_oracle` on
   the generator, no wrapper type and no `oracle_rate` helper.
3. *Count parses, not builds.* Increment inside `parse`, so the counters follow rows emitted
   rather than document sets built — under P9's cache the two differ whenever a question
   repeats.
4. *Log instead of count.* Emit a `logger.debug` line per draw and keep no state.

**The observable.** On the end-to-end fixture below (four `parse` calls, three of them
uncached, two of those with the oracle):
`gen.stats == RaftDrawStats(document_sets=3, with_oracle=2)`,
`gen.stats.oracle_rate() == 0.6666666666666666`, and
`[f.name for f in dataclasses.fields(RaftDrawStats)] == ["document_sets", "with_oracle"]`.
A fresh `RaftDrawStats()` equals `RaftDrawStats(document_sets=0, with_oracle=0)` and
`RaftDrawStats().oracle_rate() == 0.0`. On the P10 fixture (chunks `["a","b","c","d"]`,
`distractors=3`, `chunk_id=2`) the raising `parse` leaves `gen.stats == RaftDrawStats()`.
Alternative 1 has no `stats` attribute (`AttributeError`); alternative 2 has no
`RaftDrawStats` name; alternative 3 gives `document_sets=4, with_oracle=3` on the same fixture
(`oracle_rate() == 0.75`); alternative 4 leaves nothing to assert on.

**Arbitrary:** an invented name — `RaftDrawStats`, its two field names, the `oracle_rate`
helper and its `0.0`-on-empty answer, plus the policy that only uncached, successful builds
count.

### P12 — The knobs are validated in the constructor, `p` before `distractors`

**Behaviour.** `_RaftAnswer.__init__` validates its two numeric knobs as its *first* statements,
before `super().__init__(*args, **kwargs)` runs, in this order:

```python
if not 0.0 <= p <= 1.0:
    raise ValueError(f"p must be in [0.0, 1.0], got {p!r}")
if distractors < 1:
    raise ValueError(f"distractors must be >= 1, got {distractors!r}")
```

Both endpoints are legal (`p=0.0` and `p=1.0` construct fine — P5's two branches are both
reachable configurations), and `distractors=0` is rejected: a RAFT row with no distractor is
not a RAFT row. Plain `ValueError`, not `InsufficientDistractorsError` — that name is reserved
for the corpus-size failure of P10, which depends on the data rather than on the knobs. The
validation lives only here: `Raft` itself does not re-check, so `Raft(model="m", p=1.5)`
constructs happily and fails when `__call__` builds the answer generator.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No validation.* `p=1.5` simply means "always include the oracle" and `distractors=0` means
   "oracle only"; both are harmless, and the file validates nothing today.
2. *Validate on the facade.* Put the checks in `Raft.__post_init__` so a bad configuration
   fails at construction of the facade, before any chunking.
3. *Clamp instead of raise.* `self.p = min(max(p, 0.0), 1.0)`, `self.distractors = max(distractors, 0)`.
4. *Assert, or raise after `super().__init__`* — same checks, different exception type or
   placed with the other attribute assignments, so the LLM base class is constructed first.
5. *Different bound.* `distractors >= 0`, allowing an oracle-only document set.

**The observable.** With `chunks` of three documents and `backend="litellm"`:
`_RaftAnswer(..., p=1.5)` raises `ValueError` with
`str(exc) == "p must be in [0.0, 1.0], got 1.5"`; `p=-0.1` gives
`"p must be in [0.0, 1.0], got -0.1"`; `distractors=0` gives
`"distractors must be >= 1, got 0"`; `distractors=-2` gives
`"distractors must be >= 1, got -2"`; and `p=1.5, distractors=0` together give the **`p`**
message (order). `p=0.0`, `p=1.0` and `distractors=1` all construct normally. Placement is
observable through the base class: `_RaftAnswer(chunks=..., model_name="gpt-4o-mini",
backend="nope")` raises `ValueError("Unknown backend: nope")`, while
`_RaftAnswer(chunks=..., model_name="gpt-4o-mini", backend="nope", p=1.5)` raises
`ValueError("p must be in [0.0, 1.0], got 1.5")` — our check ran first. Alternative 1
constructs in every case; alternative 3 gives `gen.p == 1.0`; alternative 4 gives
`"Unknown backend: nope"` for the last case; alternative 5 accepts `distractors=0`.

**Arbitrary:** a chosen value plus a policy with no local evidence — that the knobs are checked
at all, the `>= 1` floor on `distractors`, the closed interval on `p`, the exact messages, the
`p`-before-`distractors` order, and running before `super().__init__`.

### P13 — `RaftSampling.seeded(seed)`

**Behaviour.** `RaftSampling` grows one classmethod:

```python
@classmethod
def seeded(cls, seed: int) -> "RaftSampling":
    return cls(sampler=None, rng=random.Random(seed))
```

`seed` is required and positional; `sampler` stays `None`, so the default sampler of P4 binds
to that same rng and a whole `Raft` run becomes reproducible from one integer. Each call
returns a fresh `RaftSampling` holding a fresh `random.Random`, so two `seeded(7)` bundles
never share generator state — reusing one bundle across two `Raft(...)` runs continues the
stream rather than restarting it, which is why the constructor is not cached.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No constructor.* Callers write `RaftSampling(rng=random.Random(7))`, which is one line and
   already possible under P3.
2. *A seed field.* `RaftSampling(seed: int | None = None)` as a third field, materialised into
   an rng inside `_RaftAnswer` — the shape most data-generation libraries expose.
3. *A different name or signature.* `from_seed`, `with_seed`, `RaftSampling.default(seed=0)`,
   or `seeded(seed: int = 0)` with a default seed.
4. *Seed the sampler too.* Return `cls(sampler=random.Random(seed).sample, rng=random.Random(seed))`,
   two independent generators.

**The observable.** `RaftSampling.seeded(7).sampler is None` is `True`;
`isinstance(RaftSampling.seeded(7).rng, random.Random)` is `True`;
`RaftSampling.seeded(7).rng.getstate() == RaftSampling.seeded(7).rng.getstate()` is `True`
while `RaftSampling.seeded(7).rng is not RaftSampling.seeded(7).rng`;
`RaftSampling.seeded(7).rng.random() == 0.32383276483316237`. Through the facade with the
recording stubs of P1, `sampling = RaftSampling.seeded(11)` gives
`StubA.kw["rng"] is sampling.rng`, `StubA.kw["sampler"] is None`, and
`sampling.rng.random() == 0.4523795535098186` (`== random.Random(11).random()`).
`RaftSampling.seeded(7) == RaftSampling.seeded(7)` is `False` (two distinct `Random` objects).
Alternatives 1 and 3 raise `AttributeError`/`TypeError` on this call; alternative 4 gives
`StubA.kw["sampler"] is not None`.

**Arbitrary:** an invented name — the classmethod's spelling, its required-positional `seed`,
and the decision that it leaves `sampler` as `None`.

### P14 — A list corpus drops blank documents and renumbers

**Behaviour.** In `Raft.__call__`'s list branch, entries whose `str.strip()` is empty are
dropped *before* chunk ids are assigned, and the survivors are numbered contiguously from `0`:

```python
documents = [t for t in text if t.strip()]
chunks = datasets.Dataset.from_list([{"chunk_id": i, "content": t} for i, t in enumerate(documents)])
```

Surviving text is stored verbatim — surrounding whitespace is kept, only wholly blank entries
go. A blank document is a distractor that teaches nothing and, under P10, one that inflates
`available` past what the corpus really offers. The `str` branch is untouched: `chunk_text`
(`raft.py:181`) slices a single document at `chunk_size` and its slices are never blank unless
the whole input is, so it needs no filter. An all-blank list yields an empty
`datasets.Dataset` and raises nothing here; the run then fails at the first `parse` with
`InsufficientDistractorsError` from P10.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No filtering.* `enumerate(text)` exactly as `raft.py:218` does today — the caller's corpus
   is the caller's business.
2. *Filter but keep the original ids.* `[{"chunk_id": i, "content": t} for i, t in enumerate(text) if t.strip()]`,
   preserving each document's position in the caller's list, leaving gaps in `chunk_id`.
3. *Strip the survivors too.* `content: t.strip()`, normalising whitespace while dropping the
   blanks.
4. *Reject instead of drop.* Raise `ValueError` naming the offending positions.

**The observable.** With the recording stubs of P1,
`Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA)(["alpha", "", "  ", "\n", " bravo "])`
gives `len(StubA.kw["chunks"]) == 2`,
`StubA.kw["chunks"]["content"] == ["alpha", " bravo "]` and
`StubA.kw["chunks"]["chunk_id"] == [0, 1]`. The same call on `["", "   ", "\t\n"]` gives
`len(StubA.kw["chunks"]) == 0` and `StubA.kw["chunks"].column_names == []`. The string input
`"abcdefghij"` still gives `["abcdefghij"]` with `chunk_id == [0]`. Alternative 1 gives five
documents with ids `[0, 1, 2, 3, 4]`; alternative 2 gives ids `[0, 4]`; alternative 3 gives
`["alpha", "bravo"]`; alternative 4 raises.

**Arbitrary:** a deliberate departure — the line in front of the reader enumerates the caller's
list as-is, and both the dropping and the renumbering contradict it.

### P15 — `RaftSampling` duck-types the rng it is handed, and only the rng

**Behaviour.** `RaftSampling.__post_init__` checks a non-`None` `rng` for the three methods the
draw protocol of P5 uses, in that order, and raises `TypeError` naming the missing ones:

```python
def __post_init__(self) -> None:
    if self.rng is not None:
        missing = [name for name in ("random", "shuffle", "sample") if not callable(getattr(self.rng, name, None))]
        if missing:
            raise TypeError("rng must provide " + ", ".join(missing))
```

`random.Random` passes, and so does any duck-typed recorder exposing the three names — the
check is a shape check, never `isinstance(rng, random.Random)`, because the test doubles of
P4/P5 are not `Random` subclasses. `sampler` is **not** validated: it is a bare callable with
no attributes to inspect, and a bad one raises where it is called. The check lives on
`RaftSampling` only; `_RaftAnswer(rng=...)` accepts whatever it is given, so the internal
constructor stays cheap and the facade is the place a caller's mistake is caught.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No validation.* A missing method already raises `AttributeError` at the first draw, with a
   perfectly readable traceback.
2. *Type check.* `if not isinstance(self.rng, random.Random): raise TypeError(...)` — the
   annotation says `Optional[random.Random]`, so this is the literal reading; it rejects every
   spy double in the test suite.
3. *Validate both.* Also `callable(self.sampler)`, symmetric and equally defensible.
4. *Validate in `_RaftAnswer.__init__`* instead, where the rng is actually used.

**The observable.** `RaftSampling(rng=object())` raises `TypeError` with
`str(exc) == "rng must provide random, shuffle, sample"`. For an object exposing only
`random()`, `str(exc) == "rng must provide shuffle, sample"`. `RaftSampling(rng=random.Random(7))`
and `RaftSampling(rng=SpyRng(7))` both construct. `RaftSampling(sampler=42).sampler == 42`
constructs without error, and `RaftSampling()` still constructs. Constructing
`_RaftAnswer(chunks=..., distractors=1, sampler=head_sampler, rng=partial_rng)` directly, where
`partial_rng` exposes only `random()`, succeeds and sets `gen.rng is partial_rng`. Alternative 1
constructs in every case; alternative 2 rejects `SpyRng`; alternative 3 raises on
`RaftSampling(sampler=42)`; alternative 4 raises on the direct `_RaftAnswer` construction.

**Arbitrary:** a policy with no local evidence plus an invented message — validating the rng but
not the sampler, doing it structurally rather than by `isinstance` against the declared
annotation, on the facade type rather than at the point of use, and the exact wording and
name order of the `TypeError`.

## End to end

**Fixture.**

```python
chunks = datasets.Dataset.from_list(
    [{"chunk_id": i, "content": c} for i, c in enumerate(["alpha", "bravo", "charlie", "delta", "echo"])]
)
head_sampler = lambda population, k: list(population)[:k]

gen = _RaftAnswer(
    chunks=chunks, model_name="gpt-4o-mini", backend="litellm",
    n=2, distractors=2, p=0.5, sampler=head_sampler, rng=random.Random(7),
)

rows = [gen.parse(inp, "reasoning <ANSWER>: x") for inp in [
    {"chunk_id": 0, "question": "Who?"},
    {"chunk_id": 0, "question": "What?"},
    {"chunk_id": 2, "question": "Who?"},
    {"chunk_id": 0, "question": "Who?"},   # repeat -> cache hit, no rng consumed
]]
```

`random.Random(7).random()` is `0.32383276483316237`, so the first coin is below `p=0.5` and
the first document set includes the oracle.

**Exact output.**

```python
rows[0] == {
    "question": "Who?",
    "cot_answer": "reasoning <ANSWER>: x",
    "oracle_document": "alpha",
    "context": {"title": [["placeholder_title", "placeholder_title", "placeholder_title"]],
                "sentences": [["alpha", "charlie", "bravo"]]},
    "instruction": "<DOCUMENT>alpha</DOCUMENT>\n<DOCUMENT>charlie</DOCUMENT>\n<DOCUMENT>bravo</DOCUMENT>\n\nWho?",
    "oracle_present": True,
    "oracle_index": 0,
}

rows[1] == {
    "question": "What?",
    "cot_answer": "reasoning <ANSWER>: x",
    "oracle_document": "alpha",
    "context": {"title": [["placeholder_title", "placeholder_title", "placeholder_title"]],
                "sentences": [["charlie", "delta", "bravo"]]},
    "instruction": "<DOCUMENT>charlie</DOCUMENT>\n<DOCUMENT>delta</DOCUMENT>\n<DOCUMENT>bravo</DOCUMENT>\n\nWhat?",
    "oracle_present": False,
    "oracle_index": -1,
}

rows[2] == {
    "question": "Who?",
    "cot_answer": "reasoning <ANSWER>: x",
    "oracle_document": "charlie",
    "context": {"title": [["placeholder_title", "placeholder_title", "placeholder_title"]],
                "sentences": [["bravo", "charlie", "alpha"]]},
    "instruction": "<DOCUMENT>bravo</DOCUMENT>\n<DOCUMENT>charlie</DOCUMENT>\n<DOCUMENT>alpha</DOCUMENT>\n\nWho?",
    "oracle_present": True,
    "oracle_index": 1,
}

rows[3] == rows[0]

gen._get_document_set.cache_info() == CacheInfo(hits=1, misses=3, maxsize=512, currsize=3)

gen.stats == RaftDrawStats(document_sets=3, with_oracle=2)
gen.stats.oracle_rate() == 0.6666666666666666
```

Reading the rows against the parts: `rows[1]` is the oracle-absent branch drawing
`head_sampler([1,2,3,4], 3) == [1,2,3]` → `["bravo","charlie","delta"]`, shuffled once (P5),
sentinel `-1` produced by `_get_document_set` alone (P8). `rows[2]` shows the oracle
(`"charlie"`, chunk 2) appended last to `["alpha","bravo"]` (P6) and landing in slot 1 after the
shuffle, reported as `1` (P7). `rows[3]` shows the `(chunk_id, question)` cache key: identical
to `rows[0]` and costing no rng draw, while `rows[1]` proves a second question on chunk 0 got
its own coin (P9). `gen.stats` counts the three uncached builds and the two that carried the
oracle, not the four `parse` calls (P11).

**The rest of the surface, with the same literals.**

```python
# P12 — knob validation, p checked first, before super().__init__
small = datasets.Dataset.from_list([{"chunk_id": i, "content": c} for i, c in enumerate(["a", "b", "c"])])
mk = lambda **kw: _RaftAnswer(chunks=small, model_name="gpt-4o-mini", backend="litellm", sampler=head_sampler, **kw)

mk(p=1.5)                     # ValueError("p must be in [0.0, 1.0], got 1.5")
mk(p=-0.1)                    # ValueError("p must be in [0.0, 1.0], got -0.1")
mk(distractors=0)             # ValueError("distractors must be >= 1, got 0")
mk(distractors=-2)            # ValueError("distractors must be >= 1, got -2")
mk(p=1.5, distractors=0)      # ValueError("p must be in [0.0, 1.0], got 1.5")   <- p wins
mk(p=0.0, distractors=1)      # constructs;  gen.p == 0.0, gen.distractors == 1
_RaftAnswer(chunks=small, model_name="gpt-4o-mini", backend="nope")            # ValueError("Unknown backend: nope")
_RaftAnswer(chunks=small, model_name="gpt-4o-mini", backend="nope", p=1.5)     # ValueError("p must be in [0.0, 1.0], got 1.5")

# P13 — seeded()
RaftSampling.seeded(7).sampler is None                                  # True
RaftSampling.seeded(7).rng.getstate() == RaftSampling.seeded(7).rng.getstate()   # True
RaftSampling.seeded(7).rng is not RaftSampling.seeded(7).rng            # True
RaftSampling.seeded(7).rng.random() == 0.32383276483316237              # True
RaftSampling.seeded(7) == RaftSampling.seeded(7)                        # False

# P15 — the rng is duck-typed, the sampler is not
RaftSampling(rng=object())          # TypeError("rng must provide random, shuffle, sample")
RaftSampling(rng=OnlyRandom())      # TypeError("rng must provide shuffle, sample")
RaftSampling(rng=SpyRng(7))         # constructs
RaftSampling(sampler=42).sampler    # 42
_RaftAnswer(chunks=small, model_name="gpt-4o-mini", backend="litellm",
            distractors=1, sampler=head_sampler, rng=OnlyRandom()).rng   # the OnlyRandom instance

# P1/P2/P3/P13/P14 — the facade, with kwarg-recording stubs
Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA)(["alpha", "", "  ", "\n", " bravo "])
StubA.kw["chunks"]["content"] == ["alpha", " bravo "]
StubA.kw["chunks"]["chunk_id"] == [0, 1]
len(StubA.kw["chunks"]) == 2

Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA)(["", "   ", "\t\n"])
len(StubA.kw["chunks"]) == 0 and StubA.kw["chunks"].column_names == []

Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA)("abcdefghij")
StubA.kw["chunks"]["content"] == ["abcdefghij"] and StubA.kw["chunks"]["chunk_id"] == [0]

sampling = RaftSampling.seeded(11)
Raft(model="m", question_generator_cls=StubQ, answer_generator_cls=StubA, sampling=sampling)(["a", "b", "c", "d"])
StubA.kw["rng"] is sampling.rng and StubA.kw["sampler"] is None
sampling.rng.random() == 0.4523795535098186        # == random.Random(11).random()
```

`OnlyRandom` is a one-method double (`def random(self): return 0.0`); `StubQ`/`StubA` are the
kwarg-recording stubs of P1, `StubQ.__call__` returning an object whose `.dataset` is the
chunks it was given.

**The ledger against the failure path.** On the P10 fixture — chunks `["a","b","c","d"]`,
`distractors=3`, `p=1.0`, head-sampler, `SpyRng(7)`, `chunk_id=2` — the raising
`parse({"chunk_id": 2, "question": "Q"}, "resp")` leaves `gen.stats == RaftDrawStats()` and
`gen.stats.oracle_rate() == 0.0` alongside `rng.calls == []`: the check of P10 runs before both
the randomness and the counters (P11). Counting parses instead of builds is visible on the
main fixture too — a generator built with the same five chunks, `distractors=2`, `p=0.5`, an
injected `random.Random(7)` and **no** sampler, parsed with four *distinct* questions on
chunk 0, gives `RaftDrawStats(document_sets=4, with_oracle=3)` and
`oracle_rate() == 0.75`, which is four builds because no question repeats, not because rows
were counted.

**Verification performed.** The P1–P10 reference implementation was written into
`/tmp/raftref/raft_ref.py` (the real `raft.py` with these edits) and exercised under
`horizon_env` (Python 3.13, `datasets` 4.x, curator on `sys.path`, `backend="litellm"`): 11
assertions covering P1–P10 plus this end-to-end example pass. A deliberately naive variant —
knobs forwarded and an rng injected, but oracle prepended, `parse` keeping its `else -1` guard,
`sampler or random.sample`, two-argument cache key at `maxsize=128`, no up-front availability
check, no `RaftSampling`, no `question_generator_cls` — fails all 11.

P11–P15 were then added to that implementation on a copy of the oracle tree and run in the
task container (`cli.py exec raft-document-set --tree <copy>`, same Python and `datasets`,
`backend="litellm"`). Every literal printed above was read off that run rather than predicted:
the four rows and `CacheInfo(hits=1, misses=3, maxsize=512, currsize=3)` are unchanged by the
additions, `gen.stats == RaftDrawStats(document_sets=3, with_oracle=2)` with
`oracle_rate() == 0.6666666666666666`, the five `ValueError` messages of P12 and the
`"Unknown backend: nope"` ordering probe, `RaftSampling.seeded(7).rng.random() ==
0.32383276483316237` and `seeded(11)` → `0.4523795535098186`, both `TypeError` messages of P15,
and the three facade corpora of P14 (`["alpha", " bravo "]` with ids `[0, 1]`; an empty dataset
with `column_names == []`; the untouched `str` branch).
