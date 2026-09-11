# RAFT document-set policy: owned knobs, owned randomness, authoritative oracle index

Goal: make the `Raft` block's document-set policy owned by the facade — the facade's knobs are authoritative, its randomness is injectable, and the `oracle_index` a row reports is the oracle's real slot in the context that row was built from. Everything lives in `src/bespokelabs/curator/blocks/raft.py`; add a new unit test file `tests/unit/blocks/test_raft.py` (`tests/unit/blocks/` does not exist yet).

### `RaftSampling` (new, module level)

- `@dataclass(frozen=True) class RaftSampling` with exactly two fields, in this order:
  - `sampler: Optional[_SamplingStrategy] = None`
  - `rng: Optional[random.Random] = None`
- `_SamplingStrategy` (`raft.py:69-71`) is the existing Protocol `__call__(self, population: List[T], k: int) -> List[T]`; reuse it.

### `Raft` dataclass

- Two new fields, appended **after** the existing `answer_generator_cls`, in this order:
  - `question_generator_cls: type | None = None`
  - `sampling: RaftSampling | None = None`
- so `list(Raft.__dataclass_fields__)[-3:] == ["answer_generator_cls", "question_generator_cls", "sampling"]`.
- `Raft.__call__` resolves `question_cls = self.question_generator_cls or _RaftQuestion`, `answer_cls = self.answer_generator_cls or _RaftAnswer`, and `sampling = self.sampling if self.sampling is not None else RaftSampling()`, then constructs the two stages with exactly these keyword arguments (today it forwards none of the knobs — `raft.py:221, 225-227`):

```python
question_cls(model_name=self.model, backend=self.backend, backend_params=self.backend_params,
             generation_params=self.generation_params, n=self.n_questions)

answer_cls(chunks=chunks, model_name=self.model, backend=self.backend,
           backend_params=self.backend_params, generation_params=self.generation_params,
           n=self.n_questions, distractors=self.distractors, p=self.p,
           sampler=sampling.sampler, rng=sampling.rng)
```

- `sampler=` and `rng=` are passed on every run, including when both are `None`. `n` is passed to the answer generator even though `_RaftAnswer` does not read it.
- `chunk_size`, the prompts, and `chunk_text` are untouched. `Raft.__call__`'s existing return value (the `CuratorResponse` from `answer_gen(questions)`, despite the `-> datasets.Dataset` annotation) stays as it is — `tests/integrations/test_blocks.py:32` depends on it.

### `_RaftAnswer`

```python
def __init__(self, chunks, *args, n: int = 5, distractors: int = 5, p: float = 0.8,
             sampler: Optional[_SamplingStrategy] = None,
             rng: Optional[random.Random] = None, **kwargs) -> None: ...
```

- `self.rng = rng if rng is not None else random.Random()`, and then `self.sampler = sampler if sampler is not None else self.rng.sample` — the rng supplies the default sampler, replacing `sampler or random.sample` (`raft.py:106`).
- Every draw made while building a document set goes through `self.rng` or `self.sampler`; the module-level `random` is read nowhere in the class (`raft.py:152, 165, 175` read it today). Injecting only `rng` is therefore enough to make a run reproducible.
- Document-set construction stays where it is, in the generator's existing private builder, and keeps returning the existing `DocumentSet = namedtuple("DocumentSet", ["documents", "oracle_index", "oracle_present"])` (`raft.py:73`) — same three field names, same order, `documents: List[str]`, `oracle_index: int`, `oracle_present: bool`. With probability `p` the oracle document is included among the drawn distractors; the emitted document list is randomised.
- `oracle_index` must identify the oracle's slot **in the list returned as `DocumentSet.documents`** — the same list the instruction is formatted from at `raft.py:125` — not a pre-shuffle position (`raft.py:169` reports `shuffled_indices[0]` today, which disagrees with the instruction whenever the oracle did not land first). When the oracle is absent the sentinel is `-1`, produced in exactly one place inside the builder.
- `prompt` is unchanged. `parse(self, input: dict, response: str) -> Dict[str, Any]` reports the builder's decisions verbatim — the re-decision at `raft.py:139` goes away:

| key | type | value |
|---|---|---|
| `question` | `str` | `input["question"]` verbatim |
| `cot_answer` | `str` | `response` verbatim |
| `oracle_document` | `str` | `self.chunks[input["chunk_id"]]["content"]` |
| `context` | `Dict[str, List[List[str]]]` | `{"title": [["placeholder_title"] * len(docs)], "sentences": [docs]}` where `docs is doc_set.documents` |
| `instruction` | `str` | `self.formatter(doc_set.documents) + "\n" + input["question"]` |
| `oracle_present` | `bool` | `doc_set.oracle_present` verbatim |
| `oracle_index` | `int` | `doc_set.oracle_index` verbatim, with no re-derivation and no guard |

- `self.formatter` stays the existing `_ContextFormatter` with its `document_tag="DOCUMENT"` default, rendering `"".join(f"<DOCUMENT>{doc}</DOCUMENT>\n" ...)`.

### Tests

- New `tests/unit/blocks/test_raft.py`, no network. Never construct `_RaftQuestion`/`_RaftAnswer` with the default backend: `backend=None` plus an OpenAI-shaped model name reaches `OpenAIOnlineRequestProcessor.__init__`, which does a live `requests.post` (`request_processor/online/openai_online_request_processor.py:101-103`). Use `backend="litellm"`, a stub subclass, or `__new__`.
- Cover the facade wiring with stub generator classes that record their kwargs, and cover `parse` with an injected `rng` and an injected deterministic `sampler` over a small in-memory `datasets.Dataset` of chunks.

### Constraints

- Python `^3.10`; stdlib `random`, `functools`, `dataclasses`, `collections.namedtuple`; no new dependency. `_RaftQuestion`'s existing `n: int = 5` kwarg (`raft.py:58`) is reused, not changed.
