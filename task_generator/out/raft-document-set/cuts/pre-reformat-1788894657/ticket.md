# RAFT document-set policy: owned knobs, owned randomness, correct oracle index

Make the `Raft` facade the authoritative owner of the sampling knobs and of the randomness used to build each example's document set, and make the reported `oracle_index` agree with the documents actually emitted. Everything lands in `src/bespokelabs/curator/blocks/raft.py`, plus a new `tests/unit/blocks/test_raft.py` (`tests/unit/blocks/` does not exist yet).

### New module-level `RaftSampling`

- `@dataclass(frozen=True) class RaftSampling` with exactly two fields, in this order:
  - `sampler: Optional[_SamplingStrategy] = None`
  - `rng: Optional[random.Random] = None`
- Reuse the existing `_SamplingStrategy` Protocol (`raft.py:69-71`): `__call__(self, population: List[T], k: int) -> List[T]`.

### `Raft` dataclass fields

- Two new fields, appended after the existing `answer_generator_cls` and keeping its position:
  - `question_generator_cls: type | None = None`
  - `sampling: RaftSampling | None = None`
- Resulting tail order: `list(Raft.__dataclass_fields__)[-3:] == ["answer_generator_cls", "question_generator_cls", "sampling"]`.
- Existing fields (`model`, `distractors: int = 3`, `chunk_size: int = 1000`, `n_questions: int = 2`, `p: float = 0.8`, `backend`, `backend_params`, `generation_params`) keep their names, defaults and order.

### `Raft.__call__` wiring

- `question_cls = self.question_generator_cls or _RaftQuestion`, `answer_cls = self.answer_generator_cls or _RaftAnswer`, `sampling = self.sampling if self.sampling is not None else RaftSampling()`.
- Construct with exactly these keyword arguments, on every run:

```python
question_cls(model_name=self.model, backend=self.backend, backend_params=self.backend_params,
             generation_params=self.generation_params, n=self.n_questions)

answer_cls(chunks=chunks, model_name=self.model, backend=self.backend,
           backend_params=self.backend_params, generation_params=self.generation_params,
           n=self.n_questions, distractors=self.distractors, p=self.p,
           sampler=sampling.sampler, rng=sampling.rng)
```

- `sampler` and `rng` are passed even when both are `None`. `n` is passed to the answer generator even though `_RaftAnswer` does not read it. `_RaftQuestion.__init__`'s existing `n: int = 5` kwarg (`raft.py:58`) is finally used.
- `chunk_size` and `chunk_text` (`raft.py:181`) are unchanged. `Raft.__call__`'s annotation still says `-> datasets.Dataset` while it returns the `CuratorResponse` from `answer_gen(questions)`; `tests/integrations/test_blocks.py:32` depends on that, so leave it.

### `_RaftAnswer.__init__`

```python
def __init__(self, chunks: datasets.Dataset, *args, n: int = 5, distractors: int = 5,
             p: float = 0.8, sampler: Optional[_SamplingStrategy] = None,
             rng: Optional[random.Random] = None, **kwargs) -> None: ...
```

- Attributes after `__init__`: `n`, `distractors`, `p`, `chunks`, `rng: random.Random` (`rng` when given, otherwise a fresh `random.Random()`), `sampler: _SamplingStrategy`, `formatter: _ContextFormatter`.
- Every random draw the class makes goes through `self.rng` or `self.sampler`; the module-level `random` is read nowhere in the class, so injecting randomness makes a run reproducible (`raft.py:152, 165, 175` read module-level `random` today).
- The `**kwargs` passthrough to `curator.LLM.__init__` is unchanged.

### Document set and `parse`

- The document-set construction keeps returning the existing namedtuple `DocumentSet = namedtuple("DocumentSet", ["documents", "oracle_index", "oracle_present"])` (`raft.py:73`) — same three field names, same order, `documents: List[str]`, `oracle_index: int`, `oracle_present: bool`.
- Distractor chunks are drawn through `self.sampler` from the chunks other than `chunk_id`, taken in ascending index order; the oracle document is included with probability `p`; the emitted list is randomised through `self.rng`.
- `oracle_index` must be the oracle's slot **in the list returned as `DocumentSet.documents`** — the same list the context and `instruction` are built from (`raft.py:125`, `raft.py:130`). Today `raft.py:169` reports the original index of whatever landed in slot 0, so most rows ship an index that disagrees with their own `instruction`.
- `parse(self, input: dict, response: str) -> Dict[str, Any]` returns exactly these keys:

| key | type | value |
|---|---|---|
| `question` | `str` | `input["question"]` verbatim |
| `cot_answer` | `str` | `response` verbatim |
| `oracle_document` | `str` | `self.chunks[input["chunk_id"]]["content"]` |
| `context` | `Dict[str, List[List[str]]]` | `{"title": [["placeholder_title"] * len(docs)], "sentences": [docs]}` where `docs is doc_set.documents` |
| `instruction` | `str` | `self.formatter(doc_set.documents) + "\n" + input["question"]` |
| `oracle_present` | `bool` | from the document set |
| `oracle_index` | `int` | from the document set |

- `_ContextFormatter` (`raft.py:76-81`) and its `document_tag="DOCUMENT"` default are reused unchanged, so `instruction` for `["x", "y"]` and question `"Q?"` is `"<DOCUMENT>x</DOCUMENT>\n<DOCUMENT>y</DOCUMENT>\n\nQ?"`.
- `prompt`, `_DEFAULT_QUESTION_PROMPT` and `_DEFAULT_ANSWER_PROMPT` are unchanged.

### Tests

- New `tests/unit/blocks/test_raft.py`. Cover the facade wiring with stub generator classes that record their kwargs, and the answer-generator behaviour with an injected `sampler` and an injected `random.Random`.
- Never construct `_RaftQuestion`/`_RaftAnswer` with the default backend: `backend=None` plus an OpenAI-shaped model name reaches `OpenAIOnlineRequestProcessor.__init__`, which does a live `requests.post` via `get_header_based_rate_limits()` (`request_processor/online/openai_online_request_processor.py:101-103`). Use `backend="litellm"` (`litellm_online_request_processor.py:54-63` touches no network), a stub subclass, or `__new__`.

### Environment

- Python `^3.10` (`pyproject.toml:26`), `datasets ^3.0.2`, `pydantic >=2.9.2`, stdlib `random`/`functools`/`dataclasses`/`collections`. No new dependency.
