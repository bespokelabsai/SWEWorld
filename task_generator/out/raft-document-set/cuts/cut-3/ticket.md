# RAFT document-set sampling policy: owned knobs, injected randomness, truthful oracle index

Make the `Raft` facade the authoritative owner of the sampling knobs and of the randomness used to build each example's document set, and make the reported `oracle_index` agree with the documents actually emitted. All production changes land in `src/bespokelabs/curator/blocks/raft.py`; add a new `tests/unit/blocks/test_raft.py` (`tests/unit/` exists, `tests/unit/blocks/` does not).

### New module-level `RaftSampling`

- `@dataclass(frozen=True) class RaftSampling` with exactly two fields, in this order:
  - `sampler: Optional[_SamplingStrategy] = None`
  - `rng: Optional[random.Random] = None`
- Reuse the existing `_SamplingStrategy` Protocol (`raft.py:69-71`): `__call__(self, population: List[T], k: int) -> List[T]`.

### `Raft` dataclass fields

- Two new fields, appended after the existing `answer_generator_cls`, which keeps its position:
  - `question_generator_cls: type | None = None`
  - `sampling: RaftSampling | None = None`
- Resulting tail order: `list(Raft.__dataclass_fields__)[-3:] == ["answer_generator_cls", "question_generator_cls", "sampling"]`.
- Existing fields (`model`, `distractors: int = 3`, `chunk_size: int = 1000`, `n_questions: int = 2`, `p: float = 0.8`, `backend`, `backend_params`, `generation_params`) keep their names, defaults and order.

### `Raft.__call__` wiring

- `question_cls = self.question_generator_cls or _RaftQuestion`, `answer_cls = self.answer_generator_cls or _RaftAnswer`, `sampling = self.sampling if self.sampling is not None else RaftSampling()`.
- Construct both stages with exactly these keyword arguments, on every run:

```python
question_cls(model_name=self.model, backend=self.backend, backend_params=self.backend_params,
             generation_params=self.generation_params, n=self.n_questions)

answer_cls(chunks=chunks, model_name=self.model, backend=self.backend,
           backend_params=self.backend_params, generation_params=self.generation_params,
           n=self.n_questions, distractors=self.distractors, p=self.p,
           sampler=sampling.sampler, rng=sampling.rng)
```

- `sampler` and `rng` are passed even when both are `None`; `n` is passed to the answer generator even though `_RaftAnswer` does not read it. `_RaftQuestion.__init__`'s existing `n: int = 5` kwarg (`raft.py:58`) is finally used. Today `raft.py:221, 225-227` forward none of these, so `tests/integrations/test_blocks.py:31` passes three inert arguments.
- `chunk_size` and `chunk_text` (`raft.py:181`) are unchanged. `Raft.__call__`'s annotation still says `-> datasets.Dataset` while it returns the `CuratorResponse` from `answer_gen(questions)`; `tests/integrations/test_blocks.py:32` depends on that, so leave it.

### `_RaftAnswer.__init__`

```python
def __init__(self, chunks: datasets.Dataset, *args, n: int = 5, distractors: int = 5,
             p: float = 0.8, sampler: Optional[_SamplingStrategy] = None,
             rng: Optional[random.Random] = None, **kwargs) -> None: ...
```

- Attributes after `__init__`: `n`, `distractors`, `p`, `chunks`, `rng: random.Random` (`rng` when given, else a fresh `random.Random()`), `sampler: _SamplingStrategy` (`sampler` when given, else `self.rng.sample`), `formatter: _ContextFormatter`.
- Every random draw the class makes goes through `self.rng` or `self.sampler`; the module-level `random` is read nowhere in the class, so injecting only an `rng` makes a run reproducible (`raft.py:152, 165, 175` read module-level `random` today).
- The `**kwargs` passthrough to `curator.LLM.__init__` is unchanged, and `prompt`, `_DEFAULT_QUESTION_PROMPT`, `_DEFAULT_ANSWER_PROMPT` are unchanged.

### Document-set construction

- Keeps returning the existing namedtuple `DocumentSet = namedtuple("DocumentSet", ["documents", "oracle_index", "oracle_present"])` (`raft.py:73`) — same three field names, same order, `documents: List[str]`, `oracle_index: int`, `oracle_present: bool`.
- `available_indices = [i for i in range(len(self.chunks)) if i != chunk_id]`, in ascending order.
- Exactly one `self.rng.random()`, compared `< self.p`, sets `oracle_present`.
- Exactly one `self.sampler(available_indices, k)` call, with `k = self.distractors` when the oracle is present and `k = self.distractors + 1` when it is absent.
- Oracle-present branch: the sampled distractors in sampler order, with the oracle document **appended last**; then exactly one `self.rng.shuffle(...)` over the assembled list. Oracle-absent branch: the sampled distractors, shuffled once by `self.rng` too — both branches consume the same shape of rng stream.
- `oracle_index` is the oracle's slot **in the list returned as `DocumentSet.documents`** — the list the context and `instruction` are built from (`raft.py:125, 130`) — obtained by carrying a per-slot marker through the shuffle, not by searching the shuffled list for the oracle's text. Today `raft.py:169` reports the original index of whatever landed in slot 0. In the oracle-absent branch `oracle_index` is `-1`, produced here and nowhere else.

### `parse`

`parse(self, input: dict, response: str) -> Dict[str, Any]` returns exactly these keys:

| key | type | value |
|---|---|---|
| `question` | `str` | `input["question"]` verbatim |
| `cot_answer` | `str` | `response` verbatim |
| `oracle_document` | `str` | `self.chunks[input["chunk_id"]]["content"]` |
| `context` | `Dict[str, List[List[str]]]` | `{"title": [["placeholder_title"] * len(docs)], "sentences": [docs]}` where `docs is doc_set.documents` |
| `instruction` | `str` | `self.formatter(doc_set.documents) + "\n" + input["question"]` |
| `oracle_present` | `bool` | `doc_set.oracle_present` verbatim |
| `oracle_index` | `int` | `doc_set.oracle_index` verbatim, no re-derivation |

- Drop the `... if doc_set.oracle_present else -1` conditional at `raft.py:139`: the document set is the sole decider, and `parse` reports it as-is.
- `_ContextFormatter` (`raft.py:76-81`) and its `document_tag="DOCUMENT"` default are reused unchanged, so `instruction` for `["x", "y"]` and question `"Q?"` is `"<DOCUMENT>x</DOCUMENT>\n<DOCUMENT>y</DOCUMENT>\n\nQ?"`.

### Tests

- New `tests/unit/blocks/test_raft.py`. Cover the facade wiring with stub generator classes that record their kwargs, and the answer generator with an injected `sampler` and an injected `random.Random` (or a duck-typed recorder).
- Never construct `_RaftQuestion`/`_RaftAnswer` with the default backend: `backend=None` plus an OpenAI-shaped model name reaches `OpenAIOnlineRequestProcessor.__init__`, which does a live `requests.post` via `get_header_based_rate_limits()` (`request_processor/online/openai_online_request_processor.py:101-103`). Use `backend="litellm"` (`litellm_online_request_processor.py:54-63` touches no network), a stub subclass, or `__new__`.

### Environment

Python `^3.10` (`pyproject.toml:26`), `datasets ^3.0.2`, `pydantic >=2.9.2`, stdlib `random`/`functools`/`dataclasses`/`collections`. No new dependency.
