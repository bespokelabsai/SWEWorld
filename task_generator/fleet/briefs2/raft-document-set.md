Building a RAFT example: which of the block's knobs reach the sampler, where the oracle
document actually sits in the context, and who owns the randomness.

The area, concretely:
- `src/bespokelabs/curator/blocks/raft.py` — the `Raft` dataclass (lines 204-212)
  declares and documents `distractors: int = 3`, `n_questions: int = 2` and
  `p: float = 0.8`. `__call__` (line 214) forwards **none** of them: it constructs
  `_RaftQuestion` with only model/backend/backend_params/generation_params (line 221)
  and the answer generator the same way (lines 225-227). So the generators fall back
  to their own defaults — `_RaftQuestion(n=5)` (line 58) and
  `_RaftAnswer(n=5, distractors=5, p=0.8)` (lines 87-89) — and `chunk_size` (line 217)
  is the only knob of the four that does anything. The repository's own test
  constructs `Raft(model=..., distractors=2, n_questions=1, chunk_size=1024, p=0.95)`
  (`tests/integrations/test_blocks.py` line 31); three of those four arguments are
  inert.
- Two owners of randomness. `_RaftAnswer.__init__` takes an injectable `sampler` and
  keeps it as `self.sampler = sampler or random.sample` (line 106), and a
  `_SamplingStrategy` Protocol exists for it (lines 69-71) — but oracle inclusion is
  decided by a bare `random.random() < self.p` (line 152) and ordering by a bare
  `random.shuffle` (lines 165 and 175). Injecting the sampler therefore cannot make
  the block deterministic, which is the one thing an injection point is for.
- `oracle_index = shuffled_indices[0]` (line 169), commented "Track where oracle ended
  up". After `random.shuffle(pairs)` (line 165), `shuffled_indices[0]` is the
  *original* index of whatever landed in slot 0 — not the oracle's new position, which
  is `shuffled_indices.index(0)`. Meanwhile the context handed to the model is built
  from the shuffled documents (line 125, `context = self.formatter(doc_set.documents)`),
  so the row's `oracle_index` and the row's `instruction` disagree for every example
  where the oracle did not happen to land first.
- `parse()` (line 118) then re-decides what `_get_document_set` already settled:
  line 139 emits `doc_set.oracle_index if doc_set.oracle_present else -1`, duplicating
  the `oracle_index = -1` set at line 176. One decision, two owners, no statement of
  which is authoritative.
- `functools.lru_cache(maxsize=128)` wraps the bound `_get_document_set` (line 109),
  so the `p` coin is flipped **once per `(chunk_id, oracle_document)` pair** and reused
  for every question drawn from that chunk. `p` is therefore a per-chunk probability,
  not the per-example one the docstring claims at line 96.
- `answer_generator_cls` (line 212) is an injection seam for the answer side. There is
  no matching seam for the question side.

Nothing states whether the facade's knobs are authoritative or the generators' defaults
are; whether `oracle_index` names a position in the context that was built or an index
into the original chunk list; whether the oracle coin is drawn per question or per
chunk; what a caller who supplies a `sampler` is entitled to assume about
reproducibility; or what `oracle_index` should be when the oracle is absent and who
gets to say so. Both "the block owns the sampling policy and the generators only
execute it" and "the generators own it and the block merely forwards a model" are
defensible, and the file commits to neither. Read the whole file and specify one
document-set policy.

Out of scope: the prompt strings (`_DEFAULT_QUESTION_PROMPT`, `_DEFAULT_ANSWER_PROMPT`)
and their wording, and `chunk_text`/`chunk_size`, which is the one knob that already
works — a fact drawn from either will grade as a coincidence.

Constraints: pure and deterministic. No network, no sleeping, no threads, no clock.
Randomness is injected and never read from the module-level `random`; that is half the
subject here, not an incidental constraint. The graded surface is `_get_document_set`,
`parse` and the plumbing in `Raft.__call__`, all exercisable with a hand-built
`datasets.Dataset` of a handful of chunks, a stub sampler and a seeded or injected rng.
**Never construct `_RaftQuestion` or `_RaftAnswer` on the default backend**: they
subclass `curator.LLM`, and `backend=None` with an OpenAI-shaped model name routes to
`OpenAIOnlineRequestProcessor.__init__`, which performs a live `requests.post` through
`get_header_based_rate_limits()`
(`request_processor/online/openai_online_request_processor.py` lines 101-103). Build
them with `__new__`, with a stub subclass, or with `backend="litellm"`, whose
`__init__` (`request_processor/online/litellm_online_request_processor.py` lines 54-63)
touches no network and defers its rate limits. The only test that exercises this block
is an integration test behind a VCR cassette (`tests/integrations/test_blocks.py` lines
20-36) which asserts a hash of the whole output; no unit test asserts
`_get_document_set`, so nothing here is already pinned.
