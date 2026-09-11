# RAFT document-set policy: owned knobs, owned randomness, one authoritative oracle index

Make the `Raft` facade the authoritative owner of the sampling knobs and of the randomness used to build each example's document set, and make the reported `oracle_index` agree with the documents actually emitted.

All production code lands in `src/bespokelabs/curator/blocks/raft.py`; tests go in a new `tests/unit/blocks/test_raft.py` (`tests/unit/` exists, `tests/unit/blocks/` does not).

### New module-level `RaftSampling`

- `@dataclass(frozen=True) class RaftSampling`, with exactly two fields in this order:
  - `sampler: Optional[_SamplingStrategy] = None`
  - `rng: Optional[random.Random] = None`
- Reuse the existing `_SamplingStrategy` Protocol (`raft.py:69-71`): `__call__(self, population: List[T], k: int) -> List[T]`.
- `RaftSampling()` equals `RaftSampling(sampler=None, rng=None)`, and assigning to a field of an instance raises `dataclasses.FrozenInstanceError`.

### `Raft` dataclass fields

- Two new fields, appended after the existing `answer_generator_cls`, which keeps its position:
  - `question_generator_cls: type | None = None`
  - `sampling: RaftSampling | None = None`
- Resulting tail order: `list(Raft.__dataclass_fields__)[-3:] == ["answer_generator_cls", "question_generator_cls", "sampling"]`.
- The existing fields (`model`, `distractors: int = 3`, `chunk_size: int = 1000`, `n_questions: int = 2`, `p: float = 0.8`, `backend`, `backend_params`, `generation_params`) keep their names, defaults and order.

### `Raft.__call__` wiring

- Resolve the three seams first: `question_cls = self.question_generator_cls or _RaftQuestion`, `answer_cls = self.answer_generator_cls or _RaftAnswer`, `sampling = self.sampling if self.sampling is not None else RaftSampling()`.
- Construct the two stages with exactly these keyword arguments:

```python
question_cls(model_name=self.model, backend=self.backend, backend_params=self.backend_params,
             generation_params=self.generation_params, n=self.n_questions)

answer_cls(chunks=chunks, model_name=self.model, backend=self.backend,
           backend_params=self.backend_params, generation_params=self.generation_params,
           n=self.n_questions, distractors=self.distractors, p=self.p,
           sampler=sampling.sampler, rng=sampling.rng)
```

- `sampler` and `rng` are passed on every run, including when both are `None`.
- `n` is passed to the answer generator too, even though `_RaftAnswer` does not read it. `_RaftQuestion.__init__`'s existing `n: int = 5` kwarg (`raft.py:58`) is finally used.
- The `str` input branch keeps its behaviour: `chunk_text` (`raft.py:181`) and the `chunk_size` knob are out of scope.
- `Raft.__call__` stays annotated `-> datasets.Dataset` while returning the `CuratorResponse` from `answer_gen(questions)` (`raft.py:214, 228-229`); `tests/integrations/test_blocks.py:32` depends on that, so leave it.

### `_RaftAnswer.__init__`

```python
def __init__(self, chunks: datasets.Dataset, *args, n: int = 5, distractors: int = 5,
             p: float = 0.8, sampler: Optional[_SamplingStrategy] = None,
             rng: Optional[random.Random] = None, **kwargs) -> None: ...
```

- Attributes after `__init__`: `n`, `distractors`, `p`, `chunks`, `rng: random.Random` (the given `rng`, else a fresh `random.Random()`), `sampler: _SamplingStrategy` (the given `sampler`, else `self.rng.sample`), `formatter: _ContextFormatter`.
- No draw in the class reads the module-level `random` (`raft.py:152, 165, 175` do today), so injecting `rng` alone is enough to make a run reproducible.
- The `**kwargs` passthrough to `curator.LLM.__init__` (`llm/llm.py:68`) is unchanged.

### Building the document set

- The private document-set builder keeps its name, its `DocumentSet` return type (`raft.py:73` — same three field names, same order: `documents: List[str]`, `oracle_index: int`, `oracle_present: bool`) and its `functools.lru_cache` wrapping of the bound method (`raft.py:109`).
- Each build performs, in this order:
  1. one `self.rng.random()`, compared `< self.p`, giving `oracle_present`;
  2. one `self.sampler(available_indices, k)`, where `available_indices == [i for i in range(len(self.chunks)) if i != chunk_id]` in ascending order, and `k = self.distractors` when the oracle is present, `self.distractors + 1` when it is absent;
  3. one `self.rng.shuffle(...)` over the assembled list — in the oracle-absent branch too, so both branches consume the same shape of rng stream.
- Oracle-present branch: the pre-shuffle list is the distractors in sampler order with the oracle document **appended at the end** (the current code prepends it at `raft.py:156`), then the single shuffle permutes it.
- `oracle_index` is the oracle's slot **in the list returned as `DocumentSet.documents`** — the same list the context and `instruction` are built from (`raft.py:125, 130`). Track it by carrying a per-slot marker through the shuffle, not by searching the shuffled list for the oracle's text: when a distractor chunk has content identical to the oracle's, the oracle's own slot is reported. `raft.py:169` reports the pre-shuffle index today.
- Oracle-absent branch: `oracle_index = -1`, and this is the only place the `-1` sentinel is produced.

### `parse`

- `def parse(self, input: dict, response: str) -> Dict[str, Any]` returns exactly these keys:

| key | type | value |
|---|---|---|
| `question` | `str` | `input["question"]` verbatim |
| `cot_answer` | `str` | `response` verbatim |
| `oracle_document` | `str` | `self.chunks[input["chunk_id"]]["content"]` |
| `context` | `Dict[str, List[List[str]]]` | `{"title": [["placeholder_title"] * len(docs)], "sentences": [docs]}` where `docs is doc_set.documents` |
| `instruction` | `str` | `self.formatter(doc_set.documents) + "\n" + input["question"]` |
| `oracle_present` | `bool` | `doc_set.oracle_present` verbatim |
| `oracle_index` | `int` | `doc_set.oracle_index` verbatim, no re-derivation |

- The `... if doc_set.oracle_present else -1` conditional at `raft.py:139` goes away: `parse` re-decides nothing.
- `_ContextFormatter` (`raft.py:76-81`) and its `document_tag="DOCUMENT"` default are reused unchanged, so `instruction` for `["x", "y"]` and question `"Q?"` is `"<DOCUMENT>x</DOCUMENT>\n<DOCUMENT>y</DOCUMENT>\n\nQ?"`.
- `prompt`, `_DEFAULT_QUESTION_PROMPT` and `_DEFAULT_ANSWER_PROMPT` are unchanged.

### Tests

- New `tests/unit/blocks/test_raft.py`: cover the facade wiring with stub generator classes that record their kwargs, and the answer generator with an injected `sampler` and an injected `random.Random` (or a duck-typed recorder exposing `random`/`shuffle`/`sample`).
- Never construct `_RaftQuestion`/`_RaftAnswer` with the default backend: `backend=None` plus an OpenAI-shaped model name reaches `OpenAIOnlineRequestProcessor.__init__`, which does a live `requests.post` via `get_header_based_rate_limits()` (`request_processor/online/openai_online_request_processor.py:101-103`). Use `backend="litellm"` (`litellm_online_request_processor.py:54-63` touches no network and defers rate limits), a stub subclass, or `__new__`.

### Environment

- Python `^3.10` (`pyproject.toml:26`), `datasets ^3.0.2`, `pydantic >=2.9.2`, stdlib `random`, `functools`, `dataclasses`, `collections.namedtuple`. No new dependency.
