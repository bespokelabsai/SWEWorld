Backend parameter validation: what a `backend_params` dict is allowed to contain, which
config class it becomes, and what a caller sees when the two answers disagree.

The area, concretely:
- `src/bespokelabs/curator/request_processor/config.py` — `_validate_backend_params()`
  (line 191) tries `BatchRequestProcessorConfig`, `OnlineRequestProcessorConfig`,
  `OfflineRequestProcessorConfig` in that order and accepts the **first** that
  validates, against the **raw** dict (lines 197-203). It is handed neither `batch`
  nor `backend`, so it cannot know which mode the caller asked for, and it raises a
  friendly `ValueError` naming all three classes (line 204) only when none matches.
- `src/bespokelabs/curator/request_processor/_factory.py` — `_create_config()`
  (line 29) answers the same question differently: it picks the class from
  `backend`/`batch` (lines 30-34) and calls `_remove_none_values()` (line 22) first.
  Every config class is `extra = "forbid"` (`config.py` lines 38-41).
  `create()` calls `_validate_backend_params(params)` at line 84 and **throws the
  returned config away**, then rebuilds one at line 94.
- So the two sides disagree twice over. `{"batch_size": 100}` with `batch=False`
  passes validation (it matches the Batch config) and then dies inside
  `_create_config` with a raw pydantic `ValidationError` instead of the friendly one;
  `{"max_requests_per_minute": 100}` with `batch=True` fails the same way round; and
  `{"batch_size": "auto"}` with `backend="vllm"` passes, though offline declares
  `batch_size: int` (line 134). Conversely `{"max_retries": None}` is *rejected* by
  the validator though `_create_config` would have stripped it — the two sides
  disagree about whether `None` means "absent" or "invalid".
- Three `__post_init__` hooks that never run, on pydantic v2 `BaseModel`s where the
  hook is `model_post_init`: `config.py` lines 43, 86 and 138. The base one computes
  `self.supported_params` at line 54 and then raises for **every** generation param
  at line 58 without consulting it. The batch one's documented
  `batch_size must be either an integer or "auto"` rule is dead, so `batch_size="huge"`
  is accepted by the `t.Union[int, str]` field at line 79. The offline one is `pass`
  with a docstring claiming it "Overrides base class validation" — asserting a base
  validation that has never executed. The correct hook is used correctly two
  directories away (`types/token_usage.py` line 9,
  `status_tracker/batch_status_tracker.py` line 105), so both conventions sit side by
  side in one package and reading the code leads you to the wrong one.
- `_determine_backend()` (`_factory.py` line 44) can only return `openai`,
  `anthropic`, `mistral` or `litellm` (lines 57-68), while `create()`'s dispatch table
  (lines 96-190) also handles `klusterai`, `inference.net`, `gemini`, `azure` and
  `vllm`. It takes `batch` at line 49 and never reads it: a Gemini model with
  `batch=True` and no explicit backend falls through to `litellm` and hits
  `raise ValueError("Batch mode is not supported with LiteLLM backend.")` at line 158,
  though `GeminiBatchRequestProcessor` is wired up at line 147. A Mistral model
  auto-detects at line 64 and then dies at line 175, "Only batch mode is supported
  with Mistral backend". Each branch of that table also sets `base_url` and the
  provider `api_key` default inline (lines 96-188), duplicated nine times.

Nothing states which config class an ambiguous param dict belongs to, whether `None`
means absent or invalid, what error class and message a caller gets when a param is
valid for a mode they did not ask for, whether the three dead hooks describe policy
this package still wants or debris to delete, or whether auto-detection is required to
agree with what `create()` can actually build. Both "validate against the mode you
were given" and "accept whatever any config accepts and let the constructor complain"
are defensible, and the file commits to neither. Read both files and specify one
backend-parameter policy.

Out of scope: the *semantics* of `max_retries` and `seconds_to_pause_on_rate_limit`,
which an existing task grades — a fact drawn from those will collide. Likewise the
value of `batch_size` for auto-batching, which another task owns; this area is about
which config a param lands in and what happens when it cannot, never about how big a
batch should be.

Constraints: pure and deterministic, no network, no sleeping, no threads, no clock and
no randomness — this area has none and the design must not introduce any. Testable by
calling `_validate_backend_params()` and `_create_config()` directly on plain dicts,
and `_determine_backend()` on a model name; `litellm.get_llm_provider` is offline
string parsing and is monkeypatchable, and `litellm.get_supported_openai_params` is a
local table lookup. `create()` may be exercised **only** on the branches that raise
before constructing anything (lines 158, 175, 185, 190). Never the openai or anthropic
online branches, and never `_check_openai_structured_output_support` (line 37): all
three reach `OpenAIOnlineRequestProcessor.__init__`, which performs a live
`requests.post` through `get_header_based_rate_limits()`
(`request_processor/online/openai_online_request_processor.py` lines 101-103). No test
file in the repository references `backend_params`, `_validate_backend_params`,
`_create_config` or `_determine_backend`, so there is nothing here an existing
assertion already pins.
