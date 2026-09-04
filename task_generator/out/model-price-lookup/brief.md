Model price lookup: what a token costs, who applies the batch discount, and what
happens when the price table cannot answer.

The area, concretely:
- `src/bespokelabs/curator/cost.py` — `external_model_cost()` (line 65), the
  repo's own price lookup. It reads `provider_cost[model]["input_cost_per_million"]`
  (line 76) and returns that one number as BOTH
  `{"input_cost_per_token": cost / 1e6, "output_cost_per_token": cost / 1e6}`
  (line 77). It never reads `output_cost_per_million`, which the table carries.
  It also has two failure modes for one function: an unregistered provider gets
  `{"input_cost_per_token": None, "output_cost_per_token": None}` (line 68),
  while an unknown model (line 71) or an unknown completion window (line 74)
  raises `KeyError`.
- `src/bespokelabs/curator/request_processor/_default_rate_limits.json` — the data
  that contradicts the code. `klusterai / meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`
  carries `input_cost_per_million {"*": 0.2, "24h": 0.25, "48h": 0.2, "72h": 0.15}`
  and `output_cost_per_million {"*": 0.8, ...}`, so output is currently billed at
  a quarter of its listed price. Every `inference.net` model carries
  `output_cost_per_million: null`, so any fix has to decide what an absent output
  price means.
- Four independent owners of the 50% batch discount, all in `cost.py`:
  `_LitellmCostProcessor.cost()` (line 40) does `if self.batch: cost_to_complete *= 0.5`
  (lines 45-46) and gates the whole lookup on `self.config.model in litellm.model_cost`
  (line 42); `_KlusterAICostProcessor.cost()` (line 92) and
  `_InferenceNetCostProcessor.cost()` (line 114) both compute `times = 2 if self.batch else 1`
  and multiply the parent's result by it, deliberately cancelling the parent's
  0.5; `_AzureCostProcessor.cost()` (line 137) applies its own `*= 0.5` on the
  `azure/`-prefixed branch (lines 141-143) and delegates to the parent — which
  applies its own — on the fallback branch (line 145).
- `_InferenceNetCostProcessor` (line 114) takes the model from the response
  (`kwargs["completion_response"]["model"]`, lines 115-118) and registers under
  it, while the parent it delegates to gates on `self.config.model` (line 42):
  register one model, look up another.
- `_get_litellm_cost_map()` (line 51) hardcodes `"max_tokens": 8192` and
  `"litellm_provider": "openai"` into every entry it registers into litellm's
  global table, for models that are neither.
- `src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py` —
  `set_model_cost()` (line 320), a fifth account: the `litellm.model_cost` branch
  multiplies both prices by 0.5 (lines 325-326) and the `external_model_cost`
  branch does not (lines 338-341), and nothing catches the `KeyError` that
  `external_model_cost` raises.
- `src/bespokelabs/curator/status_tracker/batch_status_tracker.py` —
  `model_post_init()` (line 105) computes the same two fields from the same two
  sources with NO discount on either branch (lines 111-122), wrapped in a bare
  `except Exception` (line 124) that leaves the prices `None`.
- `src/bespokelabs/curator/status_tracker/online_status_tracker.py` —
  `__post_init__()` (line 96), a seventh copy, catching only
  `(KeyError, TypeError)` at line 125 and passing no `completion_window` at
  line 118, so it always reads the `"*"` price. It is also the only one of the
  seven that already keeps input and output apart (lines 107-116).



Seven places answer "what does this token cost" and they disagree, and the
disagreement is reachable. `_attempt_loading_batch_status_tracker` builds the
tracker, whose `model_post_init` sets an UNDISCOUNTED price; `requests_to_responses`
then calls `set_model_cost`, which overwrites it with a discounted one — but
`cancel_batches` loads the tracker and never calls `set_model_cost`, so the same
model reports a 2x different `input_cost_per_million` depending on which entry
point ran, and that number flows into `CuratorResponse.cost_info` and the dataset
card. Meanwhile every klusterai and inference.net model reports its output price
equal to its input price, and a batch run through those two providers pays the
parent's 0.5 and the subclass's 2 and lands back at full price. Read all seven and
design the fix as one fully specified pricing rule: one lookup that answers with
both prices, one owner of the batch discount, one failure contract, and one place
the displayed per-million numbers come from.

Out of scope, because other tasks own them: batch sizing and `create_batch_file`;
retry, cooldown and rate-limit classification; the run cache fingerprint and
`MetadataDB`; and the response file / resume ledger.

Constraints: pure and deterministic, no network, no sleeping, no threads. The
clock is injected and never read inside the pricing code. `litellm.model_cost` is
a plain dict and `litellm.completion_cost` is monkeypatchable — the checkout's own
`tests/unittests/test_batch.py` (lines 135, 143) already does both — so the design
must be testable by calling the lookup and each processor's `cost()` directly with
a real config object and a monkeypatched litellm, and by constructing
`BatchStatusTracker` directly with a `rich.Console(file=io.StringIO())` passed as
the tracker console. No provider, no event loop, no batch submission.
