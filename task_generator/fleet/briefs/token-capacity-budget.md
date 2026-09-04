Token capacity accounting for online requests: who reserves capacity, who gives it
back, and what a rate limit that was never reported actually means.

The area, concretely:
- `src/bespokelabs/curator/status_tracker/online_status_tracker.py` — the leaky
  bucket. `max_requests_per_minute: int = 0` (line 61) and
  `max_tokens_per_minute: int | _TokenUsage = 0` (line 62) is followed two lines
  later by a SECOND `max_tokens_per_minute: int = 0` (line 64), which shadows the
  first. `update_capacity()` (line 596) refills from `time.time()`;
  `has_capacity()` / `consume_capacity()` (line 668) reserve;
  `free_capacity()` (line 681) returns capacity and its own docstring blesses the
  result going negative — "This can be a negative number incase of under
  estimation" — without saying what anything downstream should do about that.
- `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py`
  — `while not status_tracker.has_capacity(token_estimate): await asyncio.sleep(0.1)`
  (line 384), then `status_tracker.consume_capacity(token_estimate)` (line 391).
  The matching release, `self._free_capacity(status_tracker, used_tokens,
  blocked_capacity)`, is at line 584 — on the success path only. The failure
  branch above it ends in a bare `return` (line 564), so every failed request and
  every retry burns its estimate permanently. There is also an empty
  `def free_capacity(self, tracker, tokens)` at line 312 that nothing calls.
- The three provider subclasses in the same directory, which disagree about what a
  header means: `anthropic_online_request_processor.py` (lines 149-150) reads the
  *output* limit into `input_tpm` and the *input* limit into `output_tpm`;
  `litellm_online_request_processor.py` (lines 314-321) reads `-remaining` headers
  as if they were limits and mutates `token_limit_strategy` after construction;
  `openai_online_request_processor.py` (lines 150-159) uses a provider table with
  `rps`/`tps` scaling and a hardcoded fallback pair. Each also estimates tokens its
  own way (lines 194-208, 175-197, 243-251).
- `_default_rate_limits.json` carries a `"seperate"` entry that is dead data:
  `base_online_request_processor.py:78` selects the default while the strategy is
  still `combined`, and the anthropic subclass sets `seperate` afterwards.

Nothing states whether reserved capacity is released on every terminal outcome or
only on success, whether an underestimate may leave the bucket in debt or must
clamp, whether an absent limit means unlimited or means use the default, and
whether request capacity is released at all. The `is not None` guards throughout
both files are inert, because the defaults are `0` rather than `None`, so the
"unlimited" path they were written for is unreachable. Read both files and all
three subclasses, and design one fully specified capacity policy.

Out of scope, and the specification must not touch them: `cool_down_if_rate_limit_error`,
`seconds_to_pause_on_rate_limit`, `max_retries` and the retry queue. Those are
another task's subject and a fact drawn from them will collide with it.

Constraints: pure and deterministic, no network, no sleeping, no threads. The clock
must be injected — the tracker calls `time.time()` directly today, so the design has
to name how a test advances it. Testable by constructing `OnlineStatusTracker`
directly (with `Console(file=StringIO())`) and by driving a stub subclass of
`BaseOnlineRequestProcessor` with a fake `estimate_total_tokens`, a fake
`call_single_request` and a plain dict of response headers. No aiohttp, no provider
construction, no `asyncio.sleep`.
