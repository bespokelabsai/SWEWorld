# Clues for g10 — Online token-capacity budget: reservation, refund and reported limits

46 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Replace the ad-hoc rate-limit bookkeeping in the online request path with one capacity-budget module: a single place that decodes provider limit headers, and a tracker whose per-minute buckets are seeded, refilled and settled through an injectable clock.

### New module `src/bespokelabs/curator/status_tracker/capacity_budget.py`

- Exports the constants `DEFAULT_MAX_REQUESTS_PER_MINUTE = 200`, `DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED = 100_000`, `DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE = 100_000`, `DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE = 40_000`, `LIMIT_ORIGIN_CONFIGURED = "configured"`, `LIMIT_ORIGIN_DEFAULTED = "defaulted"`, `LIMIT_ORIGIN_UNLIMITED = "unlimited"`.
- `TokenLimitStrategy` (the enum, moved here from `online_status_tracker`, members `combined`, `seperate`, `default`) is re-exported from `online_status_tracker` for existing importers.
- `class CapacityExceedsLimitError(ValueError)` with `__init__(self, axis: str, requested: int, limit: float)`, storing `.axis`, `.requested`, `.limit`.
- `@dataclass(frozen=True) class RateLimitReading` with fields, in order: `max_requests_per_minute: int | None`, `max_tokens_per_minute: int | _TokenUsage | None`, `token_limit_strategy: TokenLimitStrategy`, `source_headers: tuple[str, ...]`.
- The header-name tuples `REQUEST_LIMIT_HEADERS = ("x-ratelimit-limit-requests", "anthropic-ratelimit-requests-limit")`, `INPUT_TOKEN_LIMIT_HEADERS = ("x-ratelimit-limit-input-tokens", "anthropic-ratelimit-input-tokens-limit")`, `OUTPUT_TOKEN_LIMIT_HEADERS = ("x-ratelimit-limit-output-tokens", "anthropic-ratelimit-output-tokens-limit")`, `TOTAL_TOKEN_LIMIT_HEADERS = ("x-ratelimit-limit-tokens", "anthropic-ratelimit-tokens-limit")`.
- Stdlib only (`math`, `re`, `dataclasses`, `enum`, `typing`); no new dependency; Python 3.10 syntax without `from __future__ import annotations`.

### `def parse_limit_value(raw: object) -> int | None`

- The single value decoder. `bool` is rejected (`None`) even though it is an `int` subclass; an `int` returns itself when `> 0`, else `None`.
- A `str` is stripped and matched against `^(\d+(?:\.\d+)?)([kKmM]?)$`; the numeric part is multiplied by `1` / `1_000` / `1_000_000` for suffix `""` / `k`,`K` / `m`,`M`, then `math.floor`ed; the result is returned when `> 0`, else `None`.
- Everything else — `float`, `None`, `bytes`, `"1,000"`, `"1e3"`, `"-5"`, `"unknown"`, `""` — is `None`. Nothing raises: a malformed header is absent, not fatal.
- Examples: `parse_limit_value("1.5k") == 1500`, `parse_limit_value("2M") == 2000000`, `parse_limit_value("40000.5") == 40000`, `parse_limit_value("0") is None`.

### `def read_rate_limit_headers(headers: t.Mapping[str, object]) -> RateLimitReading`

- Module-level, mutates nothing. Lower-cases the incoming keys once, then consults only the four name tuples above, in tuple order, first present-and-parseable name winning.
- No `*-remaining`, `*-reset` or `llm_provider-*` key is ever read, and there are no hardcoded numeric fallbacks anywhere in the reading — substituting defaults is the tracker's job.
- `anthropic-ratelimit-input-tokens-limit` feeds the **input** axis and `anthropic-ratelimit-output-tokens-limit` the **output** axis.
- Strategy selection lives in the reading: when both an input and an output limit parse to positive ints the result is `seperate` with `_TokenUsage(input=…, output=…)`, and any total-token header present is ignored; otherwise the result is `combined` using the total-token header, and a lone half of the pair is discarded. Nothing usable gives `max_tokens_per_minute=None`, `combined`.
- `source_headers` lists the exact header names consumed, request axis first, then `(input, output)` or `(total,)`; `()` when nothing was consumed.

### `OnlineStatusTracker` fields

- `max_tokens_per_minute: int | _TokenUsage | None = 0` is declared exactly once (the duplicate at `online_status_tracker.py:64` goes away); `max_requests_per_minute: int | None = 0`; `available_request_capacity: float | None`; `available_token_capacity: float | _TokenUsage | None`.
- New `capacity_clock: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)`. Every wall-clock read in `update_capacity` goes through `self.capacity_clock()`, and `__post_init__` re-seeds `self.last_update_time = self.capacity_clock()`. `start_time`, `_last_stats_update`, the display code and `cool_down_if_rate_limit_error` keep calling `time.time()` directly.
- New `token_limit_origin: str` and `request_limit_origin: str`, both `field(default=LIMIT_ORIGIN_CONFIGURED, init=False)`.

### `OnlineStatusTracker.__post_init__` normalisation

- Shape coercion: under `combined` a `_TokenUsage` limit collapses to its `.total`; under `seperate` an `int` limit `N` becomes `_TokenUsage(input=N, output=N)`.
- A limit of `None` means **unlimited**: the limit stays `None`, the matching available capacity is `None`, the origin is `"unlimited"`. Under `seperate` this is expressed per axis as `_TokenUsage(input=None, output=None)`, and a whole-token-limit `None` normalises to exactly that object.
- A limit of `0` (or, under `seperate`, an axis that is `0`) means **nobody told us**: it is replaced by the matching `DEFAULT_*` constant axis by axis, and the origin becomes `"defaulted"` if any axis was replaced. A positive number gives origin `"configured"`.
- Both buckets are then seeded to their full effective per-minute limit — `available_request_capacity = float(max_requests_per_minute)`, and `float(max_tokens_per_minute)` or `_TokenUsage(input=…, output=…)` for tokens — overwriting whatever the caller passed for either available-capacity field.

### `OnlineStatusTracker` capacity operations

- `def update_capacity(self) -> None`: `elapsed = now - self.last_update_time` is clamped with `elapsed = max(0.0, elapsed)` before refilling, refill is capped above at the limit, and `self.last_update_time = now` is assigned unconditionally, including when `now` is earlier than the previous reading. Under `seperate` the refill increment is `math.floor(limit_axis * elapsed / 60.0)`, keeping axis values `int`.
- `def has_capacity(self, token_estimate: _TokenUsage) -> bool`, `def consume_capacity(self, token_estimate: _TokenUsage) -> None`, `def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage) -> None`. `free_capacity` settles the token axes by `blocked - used` (per axis under `seperate`, `blocked.total - used.total` under `combined`).
- Under `seperate`, every mutation of `available_token_capacity` rebinds a freshly constructed `_TokenUsage(input=…, output=…)` instead of assigning to `.input`/`.output`, so `.total` is never stale.
- An axis whose capacity is `None` is read, skipped and left `None` by all of these; an unlimited tracker admits any estimate.

### `CapacityExceedsLimitError`

- `has_capacity` first asks whether the estimate could ever be satisfied: for each axis with a non-`None` limit, if the requested amount is strictly greater than the per-minute limit it raises `CapacityExceedsLimitError(axis, requested, limit)` instead of returning `False`.
- The check runs **before** `update_capacity()`, so a raise leaves `last_update_time` and both buckets untouched. Axis names and order: `"total"` under `combined`; `"input"` then `"output"` under `seperate`. An unlimited axis never raises, and a merely-empty bucket still returns `False`.
- `str(exc) == f"request needs {requested} {axis} capacity but the per-minute limit is {int(limit)}"`.

### `BaseOnlineRequestProcessor`

- `def _reserve_capacity(self, status_tracker: OnlineStatusTracker, messages: list) -> _TokenUsage | None`: a plain synchronous method that calls `self.estimate_total_tokens(messages)` exactly once and unconditionally — including when `status_tracker.max_tokens_per_minute is None` — then `status_tracker.has_capacity(estimate)` (letting `CapacityExceedsLimitError` propagate); on `True` it consumes and returns the very `_TokenUsage` object it estimated, on `False` it returns `None` having consumed nothing, neither tokens nor the request slot.
- Both reservation loops (lines 384-391 and 432-439) become `while (token_estimate := self._reserve_capacity(status_tracker, request.generic_request.messages)) is None: await asyncio.sleep(0.1)`, so the sleep remains the only await.
- `def _free_capacity(self, status_tracker: OnlineStatusTracker, used_capacity: _TokenUsage, blocked_capacity: _TokenUsage) -> None` delegates to the tracker.
- In `handle_single_request_with_retries` the reservation is released exactly once per attempt on **every** terminal path — the success path, the requeued-failure path and the exhausted-failure path — rather than only at line 584. The `try/except/else/finally` structure, `config.invalid_finish_reasons`, `update_stats`, `update_cost_projection` and `append_generic_response` are otherwise unchanged.
- The dead `def free_capacity(self, tracker, tokens)` at line 312 (empty body, no caller) is deleted: `hasattr(BaseOnlineRequestProcessor, "free_capacity") is False`.
- `def apply_rate_limit_reading(self, reading: RateLimitReading) -> None` is the only place that writes processor state from a reading: it sets `self.header_based_max_requests_per_minute`, `self.header_based_max_tokens_per_minute` and `self.token_limit_strategy = reading.token_limit_strategy`, then re-reads `self.default_max_tokens_per_minute` from `_DEFAULT_COST_MAP["online"]["default"]["ratelimit"]["max_tokens_per_minute"]` for the *new* strategy (`int` for `combined`, `_TokenUsage(**block)` for `seperate`), fixing the case where the anthropic subclass switches to `seperate` after `__init__` already picked the `combined` block.

### Provider processors

- `anthropic_online_request_processor.get_header_based_rate_limits()` and `litellm_online_request_processor.get_header_based_rate_limits()` delegate to `read_rate_limit_headers()`, dropping the swapped anthropic mapping, the `4000`/`80000`/`400000` fallbacks, the `-remaining` reads and the in-place `self.token_limit_strategy = …` mutation.
- `openai_online_request_processor.get_header_based_rate_limits()` delegates for the header half only (lines 150-159); the `RATE_LIMIT_HEADER` provider table and its `rps`/`tps` scaling stay exactly as they are.
- `BaseOnlineRequestProcessor.max_requests_per_minute` / `.max_tokens_per_minute` / `.max_concurrent_requests` keep their manual → header → default precedence.

### Out of scope

`cool_down_if_rate_limit_error`, `config.seconds_to_pause_on_rate_limit`, `config.max_retries`, the retry queue and its ordering, `num_rate_limit_errors`, `time_of_last_rate_limit_error`, and `_TokenUsage` itself are not touched.

### Tests

No network, no real `asyncio.sleep` waits: construct `OnlineStatusTracker` directly with an injected clock, and drive a stub subclass of `BaseOnlineRequestProcessor` built from `OnlineRequestProcessorConfig(model="gpt-4o-mini")` implementing the five abstract methods. `pytest` + `pytest-asyncio` for the one coroutine.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #engineering *(new)* | dario | settled this in review: free_capacity clamps every axis at 0.0, so available capacity never drops below zero and an under-estimate is just forgotten at settlement. | *herring* |
| 2025-01-21 | #code-review | emil | one thing off Dario's pass on 387: zero is the floor, a bucket sitting at 0.0 is empty and that's the whole story. no accounting for overshoot, next refill starts clean. | *herring* |
| 2025-01-21 | #releases *(new)* | dario | ok, settled: one release call for both outcomes — _free_capacity(status_tracker, used_tokens, blocked_capacity) — and the request slot goes back on failure exactly like it does on success. | *herring* |
| 2025-01-28 | #releases *(new)* | emil | except branch already has used_tokens built, so failure settles through the same _free_capacity(used, blocked) call as success. slot goes back on every terminal path. | *herring* |
| 2025-03-14 | #code-review *(new)* | emil | why is available_request_capacity sitting at -50 though? we reserve exactly one slot per request, it can't overspend, so that one should never be under zero at all. | `scope` |
| 2025-03-14 | #engineering *(new)* | dermot | yeah - on last night's run num_capacity_debt_clamps went up by two on a single settle where both halves bottomed out, so my per-run figure is double what actually happened | `observability` |
| 2025-03-17 | #pipeline *(new)* | nikolai | not bottomless though  one bad settle and the run spends the rest of the night paying it back  i'd say we cap the hole at a quarter of the minute's alowance | `rule` |
| 2025-03-17 | #code-review *(new)* | dario | mhm, one call one tick — whether it was a single axis sitting at the bottom or both of them clamped in the same settle, it still only counts once | `observability` |
| 2025-03-17 | #engineering *(new)* | konrad | Look, we handed the slot straight back the moment the response landed, and that pushed 240 calls into a 200 minute. Provider noticed. | `rule` |
| 2025-03-18 | #code-review *(new)* | emil | honestly a refill capped back at the limit is only a full bucket - token side tops out at max_tokens_per_minute, request side at max_requests_per_minute, nothing worth recording either way. | `exclusions_or_crossover` |
| 2025-03-19 | #pipeline *(new)* | konrad | anyway, I pulled the 0.25 out of the settle path into CAPACITY_DEBT_FLOOR_FRACTION in capacity_budget.py, it was sitting inline there and again in a test. | `rule` |
| 2025-03-19 | #engineering | gideon | so basically I ran a split-limit config and both halves got held against the input number, so output ended up way deeper in the hole than its own 500 a minute ever justfied | `scope` |
| 2025-03-19 | #pipeline | nils | let me think - on a smoke run that never once went under, the count came back 47. every refill that tops out at the limit is ticking it, and it shouldn't be | `exclusions_or_crossover`, `observability` |
| 2025-03-19 | #code-review *(new)* | nikolai | same goes for a relase handing back a big over-reservation - it clamps at max_tokens_per_minute rather than adding through past it, and that ceiling isnt the event were watching for. | `exclusions_or_crossover` |
| 2025-03-19 | #engineering *(new)* | nils | let me think through that - a request that actually reached the provider is spent for that minute whatever came back, it does not un-happen. | `rule` |
| 2025-03-19 | #releases *(new)* | emil | let me think through that - on a requeue the request goes back on the queue and gets estimated again, so holding the old booking against it is charging the budget twice. | `scope` |
| 2025-03-20 | #code-review *(new)* | konrad | Look, a settle that leaves us at +100 on a 1000 tracker is not it either. It should only tick when we actaully stopped the fall. | `exclusions_or_crossover` |
| 2025-03-20 | #engineering *(new)* | dermot | yeah, an attempt that errored bought us nothing, so refund_capacity returns the entire token reservation rather than whatever was left unspent. | `rule` |
| 2025-03-20 | #cookbooks *(new)* | nikolai | counted it this morning we are doing thirty real requests a minute agaisnt a sixty ceiling because the attempts that came back 503 are still sitting on their slots | `rule` |
| 2025-03-21 | #pipeline *(new)* | nils | let me think - in my grid the row where the caller passed 0 is A, and A still has the 100k default standing behind it, so it isn't a special case. | `scope` |
| 2025-03-21 | #cookbooks *(new)* | konrad | Look, if the call errored we hand its slot back, one per attemtp, and never above what the minute started with. | `rule` |
| 2025-03-24 | #pipeline *(new)* | dermot | from the late night run - settle threw doing arithmetic on a None, that model has no token ceiling at all. no ceiling, nothing to take a share of, leave it be. | `scope` |
| 2025-03-24 | #cookbooks *(new)* | nikolai | on the failure path we hand back the token counts the failed response itself reported so the bucket finishes the minute holding more capacity than the limit allows took me a whlie to spot that | `exclusions_or_crossover`, `rule` |
| 2025-03-27 | #viewer *(new)* | gideon | so basically every retry cycle on that flaky endpoint eats anohter reservation, capacity just walks down all afternoon and never comes back until we restart | `scope` |
| 2025-04-03 | #cookbooks *(new)* | konrad | Look, the length ones are worst - finish_reason length, and the reponse reports 800 output against the 100 output we actually booked for it. | `exclusions_or_crossover` |
| 2025-04-03 | #viewer *(new)* | emil | the except branch builds used_tokens but refund_capacity(blocked) refunds the whole estimate, and the slot returns on failure only, not success. saw 800 output reported against a 100 booking. | `rule`, `exclusions_or_crossover` |
| 2025-04-07 | #pipeline | dario | in the retry path, the branch where attempts_left is zero appends the failure and returns, thats the whole of it. our capacity charts never recover after a bad model | `scope` |
| 2025-04-07 | #general *(new)* | nils | let me think - _refund_capacity should be firing at the point we give up on a request entirely, and right now nothing calls it there | `scope`, `rule` |
| 2025-04-08 | #engineering | dario | estimator came in light again, third window in a row we went past the provider ceiling - and the ledger resets to zero each minute so that overshoot is gone | `rule` |
| 2025-04-08 | #pipeline | dario | on that layer, the 0.0 clamp in free_capacity is gone - forgiving the overshoot let a light estimator run past the provider ceiling three windows straight. it goes negative now, floored per axis at -CAPACITY_DEBT_FLOOR_FRACTION * limit, 0.25 | `rule` |
| 2025-04-09 | #pipeline | gideon | honestly though, to see how often we bottom out I've been diffing ledgers between runs, which is stupid - the tracker should just carry a plain counter starting at 0 and tell me. | `observability` |
| 2025-04-09 | #incidents *(new)* | dario | the one _free_capacity(used_tokens, blocked_capacity) for both outcomes was the 240 in a 200 minute. failure refunds via refund_capacity(blocked), estimate plus 1.0 slot back; success free_capacity(used, blocked), slot stays spent. | `rule`, `scope` |
| 2025-04-10 | #pipeline | emil | different shape but same area - gemini 503'd on everything last night, and by minute two we were down to one request every few seconds with zero successes. | `rule` |
| 2025-04-11 | #cookbooks *(new)* | konrad | Look, the tracker dump needs num_capacity_settlements and num_capacity_refunds as separate counters, otherwise I cannot tell the two kinds of release apart in a run. | `observability` |
| 2025-04-11 | #incidents *(new)* | dario | on the refund path the processor side stays thin — `_refund_capacity(self, status_tracker, blocked_capacity)` just calls `status_tracker.refund_capacity(blocked_capacity)` and honestly that's the whole body | `rule` |
| 2025-04-14 | #viewer *(new)* | gideon | so basically i dumped the trakcer on one of those unlimited runs and available_request_capacity comes back as None, so there is no number to watch there, only the counters. | `observability` |
| 2025-04-16 | #pipeline | emil | also from the batch-side pass: 0.0 isn't the floor anymore, minute two opens owing the overshoot down to -CAPACITY_DEBT_FLOOR_FRACTION * limit and num_capacity_debt_clamps counts each such call. | `rule`, `observability` |
| 2025-04-16 | #engineering | dario | per-request i think - on a clean response the only thing we put back into the budget is the gap between what we booked and what it actually spent | `rule` |
| 2025-04-17 | #pipeline | emil | honestly, the last progress counter we ticked from both paths never matched the request count. these two only move on release — an acquire bumps neither num_capacity_settlements nor num_capacity_refunds. | `observability` |
| 2025-04-18 | #incidents *(new)* | dermot | same shape on the request side - with no max_requests_per_minute set, available_request_capacity just reads back None, so there's nothing there to floor either | `scope` |
| 2025-04-21 | #help | gideon | Also from the same profile - estimator books 1k output tokens on every haiku call, actual comes back under 150, and then we crawl for the rest of the minute. | `rule` |
| 2025-04-21 | #general *(new)* | nils | let me think — on the throw-away path the booking is the only number we own, and refund_capacity hands it back clamped so available_token_capacity never ends above the limit. | `exclusions_or_crossover` |
| 2025-04-24 | #releases *(new)* | nikolai | ran anthropic overnight with no token ceiling set and the counts never moved off `num_capacity_settlements: int = 0` / `num_capacity_refunds: int = 0` so i spent the morning hunting a bug that wasnt ther | `observability` |
| 2025-04-29 | #general *(new)* | nils | let me think — if nobody configures a token limit, available_token_capacity is None for the whole life of that tracker, it never becomes a number. | `observability` |
| 2025-05-02 | #releases *(new)* | dermot | we're counting the call, not whether it moved a number. a release against an unlimited axis went through the same code path, so it still increments. | `observability` |
| 2025-05-13 | #pipeline *(new)* | emil | honestly if we burned more than we reserved, minute two should open owing that much. right now it opens fresh every time and I don't love it. | `rule` |

## g10.r1

**The hidden requirement:**

- **rule** — Token capacity may go negative, but each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` with `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25` exported from the capacity-budget module. The floor is `-limit * 0.25` as a `float` for the `combined` axis. Worked case: a tracker with `max_tokens_per_minute=1_000`, after `consume_capacity(_TokenUsage(input=700, output=100))` and then settling `used=_TokenUsage(input=1000, output=500)` against `blocked=_TokenUsage(input=700, output=100)`, ends at `available_token_capacity == -250.0`.
- **scope** — A tracker constructed with `max_tokens_per_minute=0` (defaulted to 100_000) floors at `-25000.0`, and under `seperate` each axis floors against its own limit: with `_TokenUsage(input=1_000, output=500)` an over-settled tracker lands on `_TokenUsage(input=-250, output=-125, total=-375)`. An axis whose limit and capacity are `None` has no floor and stays `None`. `available_request_capacity` is never floored.
- **exclusions_or_crossover** — Capping an axis at its UPPER bound is not a clamp and never touches the counter: neither the refill in `update_capacity` raising an axis back up to `max_tokens_per_minute`, nor a release raising it to that same ceiling, increments `num_capacity_debt_clamps`. The counter increments ONLY when the lower debt floor `-CAPACITY_DEBT_FLOOR_FRACTION * limit` is applied. So a settlement whose result stays above that floor (e.g. `available_token_capacity == 100.0` on a 1_000-token tracker) leaves the counter at `0`, and so does a refill that lands exactly on `1000.0` rather than the `1200.0` it would otherwise reach.
- **observability** — A tracker field `num_capacity_debt_clamps: int = 0` increments by exactly one per call that clamped at least one axis.

**Reversed earlier:** The team first clamped debt at 0.0 (capacity is never negative, an under-estimate is forgotten), then reversed it because forgiving the overshoot let a systematically under-estimating model exceed the provider's per-minute budget every window; they settled on a bounded -25% carry-over instead.

**What a reader has to infer along the way:**

- *An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.*
  - nobody says: If the overshoot has to be carried but must not be carried forever, the only way to express 'how far it may run' is as a fraction of the same per-minute number the bucket was seeded from, and that fraction needs a home.
- *The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.*
  - nobody says: 'Effective limit' is whatever the bucket was seeded with, so a defaulted axis is bounded like any other, and where there is no limit there is nothing to take a fraction of.
- *The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.*
  - nobody says: A per-call counter is the only reading that matches how people talk about 'how often did we bottom out', so two axes bottoming out inside one settle is still one event.
- *Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.*
  - nobody says: The counter is meant to answer 'how often did we go too deep', so anything that happens at the full end of the bucket, and anything that never reached the bottom, is outside what it measures.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `CAPACITY_DEBT_FLOOR_FRACTION`

> **Spread:** one source only (slack); g10.r1.g10.r1.s1: two remarks in #pipeline within 2 days; g10.r1.g10.r1.s2: two remarks in #pipeline within 3 days; g10.r1.g10.r1.s4: two remarks in #code-review within 1 days; g10.r1.g10.r1.s4: two remarks in #code-review within 1 days; : two remarks in #pipeline within 8 days

> **3 of 23 graded assertions are not stated outright** — 1 absent, 2 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g10.r1.g10.r1.s1 — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*Nobody says:* If the overshoot has to be carried but must not be carried forever, the only way to express 'how far it may run' is as a fraction of the same per-minute number the bucket was seeded from, and that fraction needs a home.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g10.r1.g10.r1.s1.l3` — rule

**nikolai**, 2025-03-17, #pipeline

> not bottomless though  one bad settle and the run spends the rest of the night paying it back  i'd say we cap the hole at a quarter of the minute's alowance

*What a reader should take from it:* the team agrees the carried debt is bounded at a quarter of the per-minute limit

*Step it builds toward:* `g10.r1.g10.r1.s1` — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*Drafted as:* not bottomless though, one bad settle and the run pays it back all night; stop the hole at a quarter of the minute's allowance.

*Why there:* The remark is a rate-limiter decision: how much token capacity a run may borrow against future minutes, and that the carried debt is capped at a quarter of the per-minute allowance. None of the eight candidate days is anywhere near that subject. The two #cookbooks days are docker image pinning, CI coverage and batch-resume ignoring the model param; both #code-review days are PR queue traffic and a GEPA null score; #general 2025-04-29 is a structured-output override key and cache-reuse fallback; #engineering 2025-04-07 is ws-050 gemini bugs and the cache fingerprint layout; #engineering 2025-05-20 is a lazy load in the Gemini download path. #engineering 2025-03-24 is the closest by vocabulary only — it's cost *estimation* and where the pricing table lives, not per-minute capacity or borrowing, and dropping a settled cap on carried debt into Gideon and Konrad's walkthrough would change the subject and draw no reaction. Rate limits and token accounting are explicitly #pipeline's beat, and the decision needs Dario there since the limiter sits on his side of the stack.

*Still leaves open:* where that quarter lives in code and what it is called; whether every axis gets one

*A new conversation in #pipeline on 2025-03-17:*

```
13:11  dario: if a request lands bigger than whats left in the minute do we just let it borrow ahead or does it wait
13:14  nikolai: borrow  it goes negative and the following minutes make it up
13:15  dario: how far negative though. is there a floor on that or does it just keep digging
13:18  nikolai: not bottomless though  one bad settle and the run spends the rest of the night paying it back
13:20  emil: so youre saying we clamp the deficit at some point rather than let it ride
13:22  nikolai: right  i'd say we cap the hole at a quarter of the minute's alowance
13:24  emil: yup, id rather stall a minute than carry it all night
```

> **Problems:** longer than one remark

#### `g10.r1.g10.r1.s1.l4` — rule

**konrad**, 2025-03-19, #pipeline

> anyway, I pulled the 0.25 out of the settle path into CAPACITY_DEBT_FLOOR_FRACTION in capacity_budget.py, it was sitting inline there and again in a test.

*What a reader should take from it:* the team agrees the fraction is 0.25 and is exported from the capacity-budget module under that name

*Step it builds toward:* `g10.r1.g10.r1.s1` — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*Drafted as:* Pulled the 0.25 out of the settle path into CAPACITY_DEBT_FLOOR_FRACTION in capacity_budget.py, it was sitting inline there and again in a test.

*Why there:* None of the listed conversations are about capacity-budget code at all. The three #code-review days (2025-06-03, 2026-01-02, 2026-01-22) are pure queue triage — PR numbers, who reviews what, defer-or-land — with nobody reading a diff or discussing a constant, so a line about hoisting a magic number out of the settle path would land with no reaction. #engineering 2025-03-14 is semaphore gating and the dict-validation gap, 2025-04-03 is the review-bandwidth pileup, the #releases days are cut/sign-off logistics, and #cookbooks 2025-03-21 is the examples taxonomy. Token and cost accounting is #pipeline's stated remit, and this is a settle-path/capacity-debt detail that only reads naturally mid-thread, with someone else on the other side of what the fraction multiplies.

*Still leaves open:* what the 0.25 is multiplied by, and in which direction it applies

*Must appear literally:* `CAPACITY_DEBT_FLOOR_FRACTION`

*A new conversation in #pipeline on 2025-03-19:*

```
14:03  dermot: whats the 0.25 in the settle path
14:04  konrad: floor fraction. it was written inline there and never got a name
14:06  dermot: ok but then why is the same 0.25 typed out in the tests too, i hit it grepping for something else
14:07  konrad: mhm. thats the actual problem, two copies of one number and nothing tying them together
14:08  konrad: anyway im pulling it out into a constant, CAPACITY_DEBT_FLOOR_FRACTION
14:09  emil: living in capacity_budget.py or somewhere more shared?
14:10  konrad: capacity_budget.py, top of the file. settle path reads it and the test imports it instead of writing the number again
14:12  dermot: yeah ok. the loose one in the test was what threw me, i had it down as a different number entirely
```

> **Problems:** longer than one remark

#### `g10.r1.g10.r1.s1.l1` — rule

**dario**, 2025-04-08, #engineering

> estimator came in light again, third window in a row we went past the provider ceiling - and the ledger resets to zero each minute so that overshoot is gone

*What a reader should take from it:* the team agrees that resetting an over-spent token bucket to empty is losing real overshoot

*Step it builds toward:* `g10.r1.g10.r1.s1` — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*Drafted as:* estimator came in light again and we went past the provider ceiling for the third window running; the ledger snaps back to zero each minute and forgets it happened.

*Why there:* That day #engineering is already chewing on the rate-limit layer specifically: dario said at 11:50 he wants to confirm the DeepSeek/OpenAI integrations aren't stepping on the rate-limit work, and at 14:46 he lists "rate-limit path check for DeepSeek and OpenAI still open on my end." A concrete finding from that check — the estimator undercounting, three windows over the provider ceiling, and the per-minute reset swallowing it — is exactly what dario would surface there, and it complicates his own "nothing that screams collision so far" while feeding the hold-DeepSeek call at the end of the day. It also sits naturally before his 13:42 "did anyone actually check the DeepSeek integration against the rate-limit layer specifically" — the finding is why he keeps asking. It deliberately stops at the loss and doesn't say what replaces the reset or how far the shortfall carries.

*Still leaves open:* what should replace the reset, and how far the shortfall is allowed to be carried

*Goes into the real conversation in #engineering on 2025-04-08, after 12:51 nikolai:*

```
09:00  nikolai: failed_requests.jsonl is wired up on my end
09:00  nikolai: Not totally sure the current field layout is what anyone downstream actually needs for debugging batch failures though
09:03  dermot: @Nikolai what fields does it have right now?
09:13  nikolai: Each line looks roughly like this:

```json
{"row_idx": 14, "error": "RateLimitError", "provider": "openai", "model": "gpt-4o", "attempt": 2}
```
10:21  dermot: no request id or timestamp?
10:30  dermot: are the deepseek, llama4, and openai additions all targeting the same release?
10:58  nikolai: fair, good catch
11:33  emil: Are we adding timestamp and request_id before this ships, or punting that to a follow-up?
11:50  dario: Separate from the jsonl fields question, I think we need to confirm the DeepSeek and OpenAI integrations aren't touching anything that would step on t
12:05  emil: WS-055 isn't in the tracker - went looking and found nothing there
12:05  emil: Has Dermot filed it somewhere else, or is it still outstanding?
12:39  dermot: ws-055 is on the wiki, not the tracker. I just pulled it up - still mostly design notes, no owner on the stub provider or e2e credentials, and the rel
12:41  emil: Sounds like it's mostly a placeholder
12:41  emil: Is the CI pipeline piece part of what's still undecided?
12:51  nikolai: Punting timestamp and request_id to a follow-up
12:51  nikolai: @Emil, can you keep that on the list so it doesn't get lost?   <-- THE REMARK GOES HERE
13:42  dario: Did anyone actually check the DeepSeek integration against the rate-limit layer specifically, or is that still open from this morning?
14:08  emil: Got it, I'll track the follow-up
14:08  emil: Is the current schema enough to trace a batch failure without the timestamp, or are we going to hit a wall on debugging until that lands?
14:38  dermot: are we planning to stage the three provider additions or ship them all at once?
14:46  dario: - Rate-limit path check for DeepSeek and OpenAI still open on my end, not fully closed out yet
- The absent headers Emil flagged are the main thing I'
14:47  dario: I'd be a bit cautious about shipping all three at once with the DeepSeek header issue still not sorted
15:11  dermot: so do we hold deepseek and ship the other two, or block all three?
15:21  dario: Syncing with Emil this afternoon on whether the retry layer handles the absent DeepSeek headers cleanly, that check isn't done yet.
16:07  dermot: that's going to land before end of day?
16:42  emil: Pulled up WS-055 - the release process section is all TBD and the stub provider and e2e credentials have no owner
17:07  dario: Just getting into the sync with Emil now, should have a read on the DeepSeek/rate-limit question before we wrap today
17:25  dermot: pr 614 is ready for review on my end
17:52  nikolai: Without timestamp and request_id, the current schema is going to be pretty useles for tracing which requests failed and when in any real batch.
18:05  nikolai: I think I was too quick to punt timestamp and request_id, the schema's not really useful without them
18:06  emil: Good to walk it back, but adding them tonight feels rushed.
18:13  nikolai: They're two fields, that's not really a night's work.
18:14  emil: The fields aren't the work, figuring out what goes in them is.
18:14  emil: @Nikolai, can you put together a quick spec on what timestamp and request_id should actually contain before those go in?
18:15  nikolai: Yeah, I'll put something together
18:27  dario: Honestly I'm not comfortable calling the DeepSeek integration clean yet with the header issue still untraced, so do we hold it or are we accepting the
18:28  dario: Actually, answering my own question, I'd lean toward holding DeepSeek and shipping OpenAI and llama4 separately until the header issue is traced
```

#### `g10.r1.g10.r1.s1.l2` — rule

**emil**, 2025-05-13, #pipeline

> honestly if we burned more than we reserved, minute two should open owing that much. right now it opens fresh every time and I don't love it.

*What a reader should take from it:* the team agrees the unreserved excess should be carried into the next window rather than dropped

*Step it builds toward:* `g10.r1.g10.r1.s1` — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*Drafted as:* If we burned more than we reserved, minute two should open owing that much. right now it opens fresh every time and I don't love it.

*Why there:* The remark is a settled design call about the local token-capacity budget: reserving an estimate per minute window and carrying the unreserved overspend into the next window. #pipeline is the right room (rate limits, token accounting), but neither pipeline day works. 2025-04-14 is about cost metadata, projected totals and batch stats — nothing about capacity windows. 2025-03-31 does touch `has_capacity`, but the mechanism there is provider rate-limit *headers* differing between Mistral batch and online, and the thread's whole conclusion is that issue 207 and issue 233 are unowned with "no agreed approach yet" (Dario, 16:07), carried into next milestone. Emil dropping a settled reconciliation decision into that would contradict the day he himself closed as unowned, and nobody is present to react to it. What's missing is the conversation where someone actually opens the reservation-vs-actual question — a run tripping the per-minute token ceiling because the estimated reservation undercounted what the responses actually cost — and the team works out what happens at window rollover. That is a #pipeline thread, and it's where the sibling remark about bounding the carried debt naturally lands too.

*Still leaves open:* whether the owing is bounded, and by how much

*A new conversation in #pipeline on 2025-05-13:*

```
15:36  gideon: whats supposed to happen when a minute goes over what it reserved?
15:37  dario: today? nothing. the next minute opens fresh, every time
15:38  gideon: fresh as in zero even if we overshot. um, that seems wrong
15:40  emil: honestly i dont love it either. we burned more than we reserved on that run and the boundary just wiped it
15:41  gideon: so basically what should minute two look like instead
15:42  emil: it should open owing that much. not at zero
15:44  dario: mhm, the deficit rides over the boundary. im going to want a window that opens in the red to not read the same as a fresh one
```

### g10.r1.g10.r1.s2 — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*Nobody says:* 'Effective limit' is whatever the bucket was seeded with, so a defaulted axis is bounded like any other, and where there is no limit there is nothing to take a fraction of.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g10.r1.g10.r1.s2.l4` — scope

**emil**, 2025-03-14, #code-review

> why is available_request_capacity sitting at -50 though? we reserve exactly one slot per request, it can't overspend, so that one should never be under zero at all.

*What a reader should take from it:* the team agrees available_request_capacity is not part of this and is never bounded below zero

*Step it builds toward:* `g10.r1.g10.r1.s2` — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*Drafted as:* Why is the request bucket sitting at -50? we reserve exactly one slot per request, it cannot overspend, so it should never be under in the first place.

*Why there:* None of the candidates is about rate-limit capacity accounting. The #pipeline thread on 2025-03-24 is about batch job ids surviving a restart; the #code-review days are about cache-write logging, schema_check at construction, PR 619's merge state, PR 653/661/690/691 status, and the container user arg; #engineering 04-10 and 04-28 are reviewer assignment and serving-infra scoping. A remark reading a negative `available_request_capacity` off a limiter and ruling that axis out of the "how far negative do we allow" question needs a room already staring at capacity buckets — that's #pipeline (rate limits, token and cost accounting), on a day someone actually posted the negative numbers. Dropping it into any of the above changes the subject and would get no reaction.

*Still leaves open:* what the token axes do instead, and how deep they are allowed to go

*A new conversation in #code-review on 2025-03-14:*

```
13:41  gideon: so basically the capacity dump off the run this morning has available_request_capacity at -50
13:42  gideon: why is it sitting at -50 though, thats the part i dont get
13:46  dario: we reserve exactly one slot per request, thats the whole of it on that path
13:47  gideon: ya so it cant overspend. then by that logic it shouldnt ever be under zero at all no?
13:51  emil: yup — one slot in, one slot back out, so nothing on the reserving path drives it under. which means the -50 got there some other way, and honestly thats the thing to go read
13:52  emil: not the reserve accounting anyway, i'd leave that bit alone
13:55  gideon: mm. i had it down as a rounding thing on the requst side and its clearly not that
```

#### `g10.r1.g10.r1.s2.l1` — scope

**gideon**, 2025-03-19, #engineering

> so basically I ran a split-limit config and both halves got held against the input number, so output ended up way deeper in the hole than its own 500 a minute ever justfied

*What a reader should take from it:* the team agrees each token axis is bounded against its own per-minute limit, not a shared one

*Step it builds toward:* `g10.r1.g10.r1.s2` — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*Drafted as:* Split-limit run: both halves got held against the input number, so output ended up way deeper in the hole than its own 500 ever justified.

*Why there:* That room spent the day on exactly this: the output-token count fix, whether it shifted the backpressure/throttle path, and the postmortem finding that the rate limiter was "calculating headroom wrong" on kluster.ai DeepSeek runs. Gideon is the one relaying the postmortem detail at 11:26-11:27 and the one pushing hardest for a concrete throttle check, so a concrete split-limit observation from him lands right after his own postmortem summary as the evidence of *how* headroom was wrong — and it settles that each axis holds against its own per-minute limit without touching defaults, absent limits, or the request bucket. #pipeline 2025-04-08 mentions rate limits but is chewing on absent DeepSeek headers and registry collisions, which is the sibling question, not this one.

*Still leaves open:* what happens on a defaulted limit, an absent limit, or the request bucket

*Goes into the real conversation in #engineering on 2025-03-19, after 11:27 gideon:*

```
09:00  nils: - api_key fix and state management refactor both merged into batch-mode
- working through Mistral batch next, have blocker I need to flag with the tea
09:30  dermot: v0.1.21 is out
09:30  dermot: two fixes in it: the gemini unicode corruption that was mangling output rows in batch, and the output-token count wrapping on long responses that was 
09:30  dermot: no breaking changes, upgrade is straightforward release notes are up on the wiki if anyone wants the detail
09:53  gideon: Good to have that written up
09:53  gideon: On the output-token fix - I want to make sure it didn't shift anything in the backpressure path, since token counts feed into how we throttle
09:53  gideon: Anyone seen unexpected behavior there since it landed?
10:01  konrad: nice
10:37  dermot: I've been wondering the same thing
10:37  dermot: has anyone done an explicit check on the throttling behavior since the fix landed, or are we going off "nothing obvious broke"?
10:51  gideon: same, I raised that question earlier and haven't seen a definitive answer yet
10:51  gideon: For context, the token counts from the estimation path feed directly into the throttle check in online-request-processing, so that's the specific plac
11:18  konrad: Nils flagged a blocker on Mistral batch earlier this morning and I don't think we ever heard the details on it
11:26  gideon: Read through the postmortem
11:26  gideon: It confirms the rate limiter was calculating headroom wrong on kluster.ai DeepSeek runs, not just cost accounting
11:27  gideon: There's an open action item to audit the batch-mode cost estimation path against the same issue before it closes   <-- THE REMARK GOES HERE
11:48  emil: Haven't seen any throttle regressions on my end, but I'll do a proper check on the batch-mode estimation path this afteroon given what the postmortem 
11:53  dermot: read through the weekly notes, the mistral section says PR 584 is blocked on the api_key configuration approach and needs team agreement
11:53  dermot: @Nils, has anyone landed on the right approach yet or is that still open?
11:56  konrad: @Nils, if you want to work through the api_key decision this afternoon I'm around.
12:27  emil: @Nils, what are the two options on the table for how the api_key gets passed?
13:59  gideon: Still waiting on Konrad's call on whether to run the explicit throttle check
13:59  gideon: Asked earlier and haven't heard back
14:37  dermot: the weekly notes have v0.1.21 stability as an open item still, does Emil's CI check close that, or are we holding until the throttle check comes back 
15:02  gideon: I think we hold - the postmortem has an open action item on the throttle path specifically, and that's not closed yet.
15:34  nils: api_key is sorted, going with the env-variable pattern same as the other providers
15:34  nils: PR 584 is unblocked
16:02  dermot: on my end the release notes are written and the announcement went out this morning
16:27  nils: on PR 584 now, should have it up tomorrow morning
16:55  emil: We could close the batch-mode estimation side now and track the throttle path as its own open item.
17:36  konrad: Run the throttle check, but don't hold the estimation close on it
17:36  konrad: Track them separately
17:57  emil: Not bad for a Wednesday.
18:12  gideon: I'm a little iffy on tracking them separately - the postmortem action items are still open and the throttle path result should close one of them, not 
18:23  emil: Those aren't in conflict though
18:24  emil: The throttle check can still close the postmortem item, it just doesn't block the estimation side from closing first
18:29  gideon: I just worry that once the estimation side closes, nobody's going back into the postmortem to file the throttle result
18:29  gideon: I think that step needs an explicit owner, not just assuming it gets picked up because the postmortem is technically still open.
```

> **Problems:** longer than one remark

#### `g10.r1.g10.r1.s2.l2` — scope

**nils**, 2025-03-21, #pipeline

> let me think - in my grid the row where the caller passed 0 is A, and A still has the 100k default standing behind it, so it isn't a special case.

*What a reader should take from it:* the team agrees a limit that came from the defaults is treated as a real limit for this purpose

*Step it builds toward:* `g10.r1.g10.r1.s2` — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*Drafted as:* In my grid the row where the caller passed 0 is A, and A still has the 100k default standing behind it, so it is not a special case.

*Why there:* Neither candidate day is chewing on limit semantics. 03-19 is postmortem action items (throttle path in online-request-processing vs. batch-mode estimation) plus the Mistral api_key blocker for PR 584; the backpressure/output-token question is named once as "still open" and deliberately not worked. 03-25 is provider test coverage and merge readiness for 584. A ruling that row A (caller passed 0) is backed by the 100k default and is therefore not special assumes a case grid nobody in either room has drawn, and the sibling remark about the None row and the request bucket would have nothing to attach to. The conversation that should exist is the one Nils's own weekly notes deferred: #pipeline settling what the bound is per case now that the output-token change has landed.

*Still leaves open:* the None-limit row and the request bucket, and what the bound actually is

*Must appear literally:* `A`

*A new conversation in #pipeline on 2025-03-21:*

```
15:22  gideon: quick one, if the caller passes 0 for the cap do we branch on that or no?
15:24  dario: i had it down as its own case tbh, 0 reads like "no room" to me
15:29  nils: let me think. in the grid i wrote out yesterday, the row where the caller passed 0 is A
15:31  gideon: ok but what does A actually do with it
15:33  nils: A still has the 100k default standing behind it
15:35  dario: so 0 isnt a special case at all, it just lands on the default
15:36  nils: right, it isn't a special case. thats worth documenting on the row itself
15:38  gideon: ya. i had a whole branch for it in my head, good thing nobody wrote that yet
```

> **Problems:** longer than one remark

#### `g10.r1.g10.r1.s2.l3` — scope

**dermot**, 2025-03-24, #pipeline

> from the late night run - settle threw doing arithmetic on a None, that model has no token ceiling at all. no ceiling, nothing to take a share of, leave it be.

*What a reader should take from it:* the team agrees an axis whose limit is None is left alone and stays None

*Step it builds toward:* `g10.r1.g10.r1.s2` — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*Drafted as:* settle threw on a model with no token ceiling at all, tried to do arithmetic on a None; if there is no ceiling there is nothing to take a share of, leave it be.

*Why there:* The remark is a settled design call about the capacity-budget code: `settle` crashed doing arithmetic on a model whose token ceiling is `None`, and the team decides that axis is left alone. None of the candidate threads is chewing on token capacity budgeting. The 2025-04-09 #pipeline thread is about provider-integration regressions, batch submission and the gemini response shape — a None token ceiling would arrive from nowhere there. #code-review 2025-04-22 only shares vocabulary ("casting fix in token accounting" on PR 649); that's a review status ping on someone else's already-cleared PR, not a place to settle how unbounded axes are treated. The 2025-04-04 and 2025-04-17 #engineering threads are llama4 scoping and land/defer triage; #releases and the two other #code-review days are further off still. This belongs in #pipeline, the room that owns rate limits and token accounting, on a day when someone actually ran the budget code and it threw — with Gideon there, since he's the one validating that rate limit and cost accounting surface cleanly.

*Still leaves open:* how axes that do have a ceiling are bounded, and by what fraction

*A new conversation in #pipeline on 2025-03-24:*

```
15:11  gideon: settle threw on me, traceback bottoms out doing arithmetic on a None
15:14  dermot: the late night run? which value came back None
15:16  gideon: the token ceiling. that model has none at all, not zero, just absent
15:19  dermot: then theres nothing there to take a share of
15:20  gideon: so we fill in a default and carry on?
15:23  dermot: no, leave it be. no ceiling, no share to hand out
15:25  dario: makes sense, otherwise were splitting up something that isnt there
15:27  gideon: ya. i burned twenty min looking for where it got set to zero and it never was
```

> **Problems:** longer than one remark

#### `g10.r1.say19` — scope

**dermot**, 2025-04-18, #incidents

> same shape on the request side - with no max_requests_per_minute set, available_request_capacity just reads back None, so there's nothing there to floor either

*What a reader should take from it:* the team agrees a request axis with no per-minute request limit reads back None for available_request_capacity

*Step it builds toward:* `g10.r1.g10.r1.s2` — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*Drafted as:* same shape on the request side - with no max_requests_per_minute set, available_request_capacity just reads back None, so there's nothing there to floor either.

*Why there:* The remark is a reply inside a live discussion of the rate-limiter's capacity bookkeeping — what the per-axis counters hold when a limit isn't configured. None of the candidate days is chewing on that. The two #pipeline days are about batch job ids surviving a restart (03-24) and the cache fingerprint / pending job record missing the model (04-23); the #engineering and #code-review days are PR triage and reviewer assignment; #general 04-29 is the structured-output override and abort-vs-fallback. Dropping "same shape on the request side" into any of them means it answers nobody, since the token-side observation it's agreeing with was never made there, and it would change the subject with no reaction. #pipeline is the right room by purpose (rate limits, token and cost accounting) — it just needs the day where the limiter's unset-limit behaviour is actually on the table.

*Still leaves open:* says nothing about how deep the token axes may go, that each token axis is held against its own limit, or that a caller-passed 0 still picks up the 100k default

*Must appear literally:* `max_requests_per_minute`, `available_request_capacity`, `None`

*A new conversation in #incidents on 2025-04-18:*

```
15:07  nikolai: dermot the capacity dump off the stalled run has available_request_capacity None sitting in it
15:08  nikolai: did we put that there or is something eating it
15:12  dermot: neither. same shape on the request side as the one you were poking at yesterday
15:13  nikolai: same shape how, None isnt a number, whats even reading it
15:15  dermot: with no max_requests_per_minute set, available_request_capacity just reads back None. nothing ever gets put in it
15:16  nikolai: ok so does the floor still land on it or does it skip
15:17  dermot: so theres nothing there to floor either. no value sitting in it to clamp at all
15:19  petar: that lines up with the box, no request limit configured on it
```

### g10.r1.g10.r1.s3 — The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.

*Nobody says:* A per-call counter is the only reading that matches how people talk about 'how often did we bottom out', so two axes bottoming out inside one settle is still one event.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g10.r1.g10.r1.s3.l2` — observability

**dermot**, 2025-03-14, #engineering

> yeah - on last night's run num_capacity_debt_clamps went up by two on a single settle where both halves bottomed out, so my per-run figure is double what actually happened

*What a reader should take from it:* the team agrees counting once per axis overstates the event

*Step it builds toward:* `g10.r1.g10.r1.s3` — The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.

*Drafted as:* num_capacity_debt_clamps went up by two on a single settle where both halves bottomed out, so my per-run figure is double what actually happened.

*Why there:* None of the candidate days is chewing on capacity-debt clamp instrumentation. 03-24 and 04-03 are batch-id persistence; 03-14 is semaphore/cookbook verification; 04-17 is the mkdir -p cache incident; 04-10 is DeepSeek 429 headers and PR 624 log removal; 04-25 is the finetuning handoff contract; 05-06 is release-notes contents; 03-19 is weekly-notes follow-ups. A metric double-counting per axis on a single settle answers nothing live in any of them and would change the subject. It needs the room that owns rate limits and token/cost accounting, in a thread actually about the clamp counter, so the sibling remark about the correct increment and where the field lives has somewhere to land.

*Still leaves open:* what the right increment is, and where the field lives

*Must appear literally:* `num_capacity_debt_clamps`

*A new conversation in #engineering on 2025-03-14:*

```
13:04  dermot: konrad, the clamp count in your capacity notes - mine comes out higher and i cant reconcile the two
13:06  konrad: what are you reading it off
13:07  dermot: num_capacity_debt_clamps, delta over last nights run
13:08  dermot: it moved by two there. i had that down as two separate clamped calls
13:09  dario: two seperate calls or one call that got counted twice? because those look identical from the delta
13:10  dermot: one. single settle, and both halves bottomed out on it
13:12  konrad: right, so the settle behaved, the counter didnt
13:13  dermot: mhm. one settle happened, so my per-run figure is double what actually happened - its the count thats wrong, not my arithmetic
13:14  dario: then the weekly numbers i pulled are off the same way, im not going to touch that column till its counting straight
```

#### `g10.r1.g10.r1.s3.l3` — observability

**dario**, 2025-03-17, #code-review

> mhm, one call one tick — whether it was a single axis sitting at the bottom or both of them clamped in the same settle, it still only counts once

*What a reader should take from it:* the team agrees the counter moves by exactly one per call in which anything was held at the bottom

*Step it builds toward:* `g10.r1.g10.r1.s3` — The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.

*Drafted as:* one call, one tick, whether it was one axis that hit the bottom or both of them in the same settle.

*Why there:* The remark settles a counting convention for a clamp/floor counter on the token capacity budget: one increment per call in which anything was pinned at the bottom, regardless of whether one axis or both hit it. Nothing in the candidate days is chewing on capacity floors or a clamp counter. The two token-adjacent pipeline days are about something else entirely — 2025-04-22 is the malformed Anthropic token count and whether the casting fix precedes the retry logic, and 2025-04-10 is DeepSeek 429 headers and whether PR 624's log removal touches rate limit headroom tracking. Dropping "one call, one tick" into either would change the subject with no prior mention of a settle, an axis, or a bottom, and both days end with their own questions still open. The code-review days (583/619/584 state, schema_check hook point) and the two batch-id-persistence threads are further off still; #incidents on 04-18 is fingerprint contents. The conversation that should exist is in #pipeline, which owns token and cost accounting for the request layer: the day someone actually watches the capacity budget collapse to its minimum mid-run and asks how often that happened, which forces both the field and its increment semantics.

*Still leaves open:* the field's name and its starting value

*A new conversation in #code-review on 2025-03-17:*

```
13:41  nikolai: on the clamp counter - call gets squeezed on both axes in one shot, does that come out as two
13:42  dario: no. one call one tick
13:43  nikolai: and the boring case i mean single axis sitting at the bottom
13:44  dario: same, counts once. its the call we're counting, not which of them got pinned. nobody's written it yet but thats the shape
13:45  konrad: so both clamped in the same settle also lands as one, right
13:46  dario: mhm, still only counts once
13:47  nikolai: yep. i was reading it the other way and the totals werent adding up for me
```

#### `g10.r1.g10.r1.s3.l1` — observability

**gideon**, 2025-04-09, #pipeline

> honestly though, to see how often we bottom out I've been diffing ledgers between runs, which is stupid - the tracker should just carry a plain counter starting at 0 and tell me.

*What a reader should take from it:* the team agrees the tracker carries a counter starting at 0 for how often the bottom was hit

*Step it builds toward:* `g10.r1.g10.r1.s3` — The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.

*Drafted as:* I have been diffing ledgers between runs to work out how often we bottom out, which is stupid. Put a plain zero-initialised counter on the tracker and let it tell me.

*Why there:* Gideon opens that day already mid-pass on "the rate limit and cost accounting surfaces" through online-request-processing, and nobody picks that thread up — it's his own observability burst, so a second line naming a concrete instrumentation gap he found (no counter for how often capacity bottoms out, so he's reduced to diffing ledgers across runs) lands as continuation, not a subject change. #pipeline is explicitly the room for rate limits and token accounting. It doesn't collide with 03-26's zero-fallback argument (that's Mistral usage extraction being silently absent, not a deliberate counter) and it leaves the naming and the exact increment condition open.

*Still leaves open:* what the counter is called and what exactly makes it move

*Goes into the real conversation in #pipeline on 2025-04-09, after 09:15 gideon:*

```
09:00  dermot: landed 8 commits on bulk-llm-inference and the provider integration side this morning
09:00  dermot: I want someone to sanity check that the backend changes don't quietly break any of the existing providers before we go further
09:15  gideon: On the observability side, I've been validating that the rate limit and cost accounting surfaces cleanly through online-request-processing. Nothing al
09:15  gideon: Also been looking at the caching-and-resume side and haven't hit any surprises yet   <-- THE REMARK GOES HERE
09:36  dermot: Gideon, is your pass covering the batch submission path as well, or just online requests and caching so far?
14:36  gideon: Sorry, missed this
14:36  gideon: Mostly online requests and caching so far, batch submission path I haven't gotten to yet
15:11  dario: makes sense
15:11  dario: batch submission is the one path I'd want covered before we say the provider changes are clean
15:31  emil: When someone gets to the batch submission path, can you also check the full gemini batch response shape, not just whether it runs?
15:31  emil: PR 621 fixes the finish reason gap but I'm honestly not certain that's the only thing off in that response
15:36  dermot: Gideon, can you take the batch submission path and check the full gemini response shape while you're at it?
15:36  dermot: Emil, WS-050 isn't written up anywhere I can find - is the batch mode scope documented somewhere or not yet?
15:39  gideon: @Emil, got a few minutes before end of day to walk me through what else might be off in the gemini batch response?
15:56  emil: WS-050 isn't written up anywhere I can find either, same as you
15:57  emil: Do we actually need that doc before we can call batch mode scope settled, or can it come later?
15:57  emil: @Gideon yeah, a few minutes works, let me know where.
16:27  gideon: DM'd you
17:06  dario: Committed a couple of examples today for the new provider coverage, including qwq. I want to make sure someone's actually run those against the live b
17:50  dermot: I can run the new examples against live backends now if that's what closes it out.
18:21  dario: That works, yeah
18:21  dario: The qwq example is the one I'm least sure about since it's the newest addition, so if you hit anything unexpected there flag it
18:26  emil: WS-050 isn't written up anywhere I can find - went looking and there's nothing there.
18:26  emil: Who's supposed to be owning that doc, or has it just not happened yet?
```

> **Problems:** longer than one remark

### g10.r1.g10.r1.s4 — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*Nobody says:* The counter is meant to answer 'how often did we go too deep', so anything that happens at the full end of the bucket, and anything that never reached the bottom, is outside what it measures.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g10.r1.g10.r1.s4.l2` — exclusions_or_crossover

**emil**, 2025-03-18, #code-review

> honestly a refill capped back at the limit is only a full bucket - token side tops out at max_tokens_per_minute, request side at max_requests_per_minute, nothing worth recording either way.

*What a reader should take from it:* the team agrees capping a refill at the per-minute limit is not the counted event

*Step it builds toward:* `g10.r1.g10.r1.s4` — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*Drafted as:* A bucket refilling back up to its own limit is just a full bucket. Nothing worth recording in that.

*Why there:* Every listed conversation is about review logistics, release announcements, viewer rendering, or the schema_check construction hook — none of them is chewing on the rate limiter at all, and a remark about token bucket refills clamping at the per-minute limit would arrive from nowhere in any of them and draw no reply. Bucket capacity, refill behaviour and what counts as a recorded throttling event is squarely #pipeline territory (rate limits and token accounting). The conversation that should exist is someone adding capacity/throttle instrumentation to the limiter and asking which events actually get counted — emil ruling out the no-op refill case, with a sibling answering for the release path.

*Still leaves open:* what the release path does, and what does get recorded

*Must appear literally:* `max_requests_per_minute`, `max_tokens_per_minute`

*A new conversation in #code-review on 2025-03-18:*

```
13:47  dario: quick one on the refill path — when the top up overshoots and gets pinned back down to the ceiling, do we want that surfaced anywhere?
13:49  gideon: im in that file for the throttle change so i'd like to know before i touch it
13:52  emil: let me think through that
13:53  emil: honestly a refill capped back at the limit is only a full bucket. nothing has gone wrong at that point
13:55  dario: sure on the token side, thats just it sitting at max_tokens_per_minute. the request side pins the same way though and i didnt want to assume
13:57  emil: same story there, it tops out at max_requests_per_minute and thats the healthy state. nothing worth recording either way
```

#### `g10.r1.g10.r1.s4.l1` — exclusions_or_crossover, observability

**nils**, 2025-03-19, #pipeline

> let me think - on a smoke run that never once went under, the count came back 47. every refill that tops out at the limit is ticking it, and it shouldn't be

*What a reader should take from it:* the team agrees refill hitting the upper limit is being counted today and should not be

*Step it builds toward:* `g10.r1.g10.r1.s4` — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*Drafted as:* Count came back 47 on a smoke run that never once went under, turns out every refill that topped out at the limit was ticking it.

*Why there:* That day #pipeline is already chewing on the postmortem line that the rate limiter was miscalculating headroom, not just cost accounting, and Gideon has just asked whether anyone actually ran the throttle path since the wrapping fix. A concrete counter symptom from a smoke run is exactly the kind of thing that lands there — it gives Gideon's question something to bite on and complicates the later "came back clean" without contradicting it, since a saturating-refill overcount is pre-existing rather than a regression. Nils is in the room and active, and he's the one who wrote up the open rate-limit questions in the weekly notes, so reporting a stray count on that path reads as his. Nothing said earlier makes the point, and the remark deliberately leaves what the counter should record, and how releases are treated, to be settled elsewhere.

*Still leaves open:* what the counter should be recording instead, and how releases are treated

*Goes into the real conversation in #pipeline on 2025-03-19, after 11:42 gideon:*

```
09:00  nils: put the weekly notes for week of Mar 17 on the wiki (engineering/weekly-notes-week-of-mar-17). Covers provider and batch-mode status, the PR 584 block
10:43  dermot: read through Nils's weekly notes
10:43  dermot: gemini unicode fix is showing no regressions so far, which is good, but the backpressure question from the output-token change is still marked open th
11:05  emil: Gemini batch side looks clean from what I can see too
11:05  emil: Mistral is still stuck on the api_key config for PR 584, haven't found a clean path forward on that yet
11:22  nils: yeah
11:22  nils: PR 584 is stuck on that exactly
11:22  nils: need a decision on how the api_key gets passed for Mistral batch before I can move it forward
11:29  gideon: so the backpressure question is still open on both sides
11:41  gideon: Read through the postmortem, and it explicitly says the rate limiter was miscalculating headroom, not just the cost accounting
11:42  gideon: Has anyone actually run a check on the throttle path since the wrapping fix landed, or are we calling it clean without one?   <-- THE REMARK GOES HERE
12:19  emil: @Nils, you getting any traction on the api_key question or still waiting on someone to make the call?
12:34  dermot: @Gideon I haven't seen a proper check done
12:34  dermot: that path is in online-request-processing, @Dario, are you in a position to run one this afternoon?
13:09  nils: went with the env-variable pattern, same as the other providers. no separate config path needed, so PR 584 is unblocked
13:52  gideon: I can run that check, online-request-processing is mine
13:52  gideon: @Konrad, do you want an explicit throttle validation before we close out the postmortem action item, or are we ok proceeding on no observed regression
14:02  gideon: The batch-mode estimation path is getting checked this afternoon but has anyone looked at the throttle path in online-request-processing specifically?
14:02  gideon: I offered to run that check but I'm still waiting on a call on whether it's needed
14:41  dermot: good news on PR 584
15:10  gideon: Read through the postmortem - it has an open action item to audit the batch-mode estimation path, but doesn't call out the throttle path in online-req
15:10  gideon: Does Emil's check this afternoon cover that too, or is that still pending?
15:27  emil: My check is the batch-mode estimation path
15:27  emil: The throttle path in online-request-processing is separate and still pending
15:27  gideon: So that one's still on me to run?
15:34  emil: Looks like it. I'll finish the batch-mode side, you cover the throttle path, and we should have both closed out by end of day.
16:07  dermot: will you both post results here when done?
16:32  nils: PR 584 is in progress, the api_key change itself is fairly straightforward so should be up for review tomorrow morning
16:41  dermot: gemini unicode fix is confirmed clean, mistral api_key is sorted, good place to end the day.
16:41  gideon: by end of day today, so I'm running it now?
17:04  nils: solid
18:14  gideon: Running it now, will post results
18:29  emil: Batch-mode estimation check is done, came back clean.
18:29  gideon: Throttle path check is running, should have results in a few minutes
18:29  gideon: Throttle check came back clean, no regressions.
```

> **Problems:** longer than one remark

#### `g10.r1.g10.r1.s4.l3` — exclusions_or_crossover

**nikolai**, 2025-03-19, #code-review

> same goes for a relase handing back a big over-reservation - it clamps at max_tokens_per_minute rather than adding through past it, and that ceiling isnt the event were watching for.

*What a reader should take from it:* the team agrees a release that raises an axis to its limit is not counted either

*Step it builds toward:* `g10.r1.g10.r1.s4` — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*Drafted as:* same goes for a release that hands back a big over-reservation and puts us right on the ceiling, that is not the event we are watching for.

*Why there:* Every candidate is PR-shepherding traffic (who reviews PR 663, did PR 619 merge, does PR 653 gate v0.1.25) plus one #random thread about disagreeing model-name lists and one #cookbooks thread about the verifier path. None of them is chewing on token capacity accounting — there is no reservation, no ceiling, no counter being defined anywhere in them, so the remark would change the subject and draw no reaction. It is plainly about the token budget's reserve/release cycle and which transition counts as saturation, which is #pipeline's stated job (rate limits, token and cost accounting). It also leans on a sibling remark defining the event being counted, so it needs a live two-or-three-person design argument that doesn't exist on any of the offered days.

*Still leaves open:* which event is being watched for, and how it is counted

*Must appear literally:* `max_tokens_per_minute`

*A new conversation in #code-review on 2025-03-19:*

```
14:03  konrad: Quick one before I go back to 595 - what happens when a release hands back a big over-reservation?
14:05  nikolai: hands back way more than it actually used you mean
14:06  konrad: mhm. the big ones. does the available pool just walk up past the top
14:08  nikolai: no it clamps at max_tokens_per_minute it doesnt add through past it
14:09  dario: and does that clamp get counted anywhere or does it just quietly happen
14:11  nikolai: quietly. that ceiling isnt the event were watching for
14:12  dario: makes sense, same goes for the release side then. its the same shape as the other case, i just hadnt seen it written down anywhere
14:14  konrad: right, nobody has written it yet. anyway, 595 is still open on my side
```

#### `g10.r1.g10.r1.s4.l4` — exclusions_or_crossover

**konrad**, 2025-03-20, #code-review

> Look, a settle that leaves us at +100 on a 1000 tracker is not it either. It should only tick when we actaully stopped the fall.

*What a reader should take from it:* the team agrees only applying the lower bound counts, and a settlement finishing above it does not

*Step it builds toward:* `g10.r1.g10.r1.s4` — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*Drafted as:* A settle that leaves us at +100 on a 1000 tracker is not it either. It should only tick when we actually stopped the fall.

*Why there:* The remark is about settle semantics on a token-capacity tracker — whether the clamp counter ticks when a settle lands above the floor versus only when the lower bound actually bit. None of the candidates is anywhere near that subject: the two #viewer days are local-viewer removal and download plumbing, #general 2025-04-07 is weekly status, #releases 2025-05-06 is the v0.1.24 notes and issue 52, #engineering 2026-01-22 is README/cookbooks coverage, and the three #code-review days are PR 652 drift, the o3/678-vs-679 overlap, and the Mistral batch PR 584 call. Token and cost accounting, rate limits and capacity live in #pipeline, and none of the listed threads is chewing on a tracker at all — dropping "+100 on a 1000 tracker" into any of them would change the subject with nobody to react to it. It needs a #pipeline thread where the settle path is already being argued: someone (dario, who owns online-request-processing) posts that the estimate-then-settle path can drive the tracker down past anything sane on a bad estimate, emil pushes on what the floor should be, and konrad's line is the second half — agreeing only the applied lower bound counts as clamped, while the floor value and the fraction that sets it are settled by the sibling remark in the same thread.

*Still leaves open:* where the fall is stopped and what fraction sets that point

*A new conversation in #code-review on 2025-03-20:*

```
13:41  dario: the counter - does every settle bump it, or only some of them
13:42  emil: i had it as every settle honestly, thats how the ticket reads to me
13:44  konrad: look, a settle that leaves us at +100 on a 1000 tracker is not it either
13:45  dario: so whats the bar. +100 is still on the right side of zero
13:46  konrad: it should only tick when we actaully stopped the fall. thats the whole test
13:47  dario: ok so being in the black isnt the test at all
13:49  emil: sounds right. the sheet i pasted monday counts all of them the same, that column isnt what the header says it is
```

### Herrings — believed at the time, overturned later

#### `g10.r1.clamp-at-zero-decision` — herring

**dario**, 2025-01-21, #engineering

> settled this in review: free_capacity clamps every axis at 0.0, so available capacity never drops below zero and an under-estimate is just forgotten at settlement.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled in review: free_capacity clamps every axis at 0.0. available capacity never drops below zero, so an under-estimate is simply forgotten at settlement.

*Why there:* None of the eight candidates is chewing on rate-limit/token-capacity accounting. The two pipeline cost threads (Jan 29, Feb 18) are about cost calculation and litellm returning 0 vs None on the cost map — a zero there is a wrong price, not a clamped capacity axis, so dropping a `free_capacity` clamp decision into 18:29 on Feb 18 would answer a question nobody asked and quietly conflate cost with capacity. The code-review days are PR triage (430 blocked, 579 duplicating 565/566) and the cookbooks day is the create_model lookup pass. The remark reports a settled review outcome about the shared limiter's capacity budget, which belongs in #pipeline — the room that owns rate limits and token accounting — on a day when someone is actually asking what happens if a request's token estimate comes in low and settlement has to reconcile it.

*A new conversation in #engineering on 2025-01-21:*

```
14:02  konrad: quick one on free_capacity — if we underestimate a request and it comes back bigger than we reserved, what does the available number do
14:04  nikolai: dips under i'd assume
14:07  dario: no, thats the thing we settled in review. every axis gets clamped at 0.0, so available bottoms out there and never goes under
14:07  konrad: ok but the difference doesnt just evaporate does it. something still owes it back
14:09  dario: honestly it does evaporate. we take the clamp and thats the end of it — at settlement the under-estimate isnt recorded anywhere, its just forgotten
14:10  konrad: huh ok. so an under-estimate is free once the request settles
14:11  nikolai: right and nothing downstream has to know about signed numbers
14:13  dario: mhm, thats about the size of it. best we can do without every reader of that struct handling a below-zero case
```

#### `g10.r1.clamp-at-zero-rationale` — herring

**emil**, 2025-01-21, #code-review

> one thing off Dario's pass on 387: zero is the floor, a bucket sitting at 0.0 is empty and that's the whole story. no accounting for overshoot, next refill starts clean.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Zero is the floor, per Dario — a bucket at 0.0 is empty and that's the whole story. no accounting for overshoot, the next refill starts clean.

*Why there:* PR 387 is explicitly "Emil's max_tokens capacity blocking change" — the capacity-bucket code — and the room spends the day waiting on Dario's review pass of it. Dario posts "PR 387 review done, looks good to merge" at 15:47 with no detail; the one semantic question a reviewer would raise on a capacity blocker is what happens when the bucket is drawn past its floor. Emil, as the author relaying the reviewer's call before asking "are we clear to merge", is exactly who says this and when. Nothing earlier states bucket-floor or refill behavior, so it isn't redundant, and it doesn't collide with the cost-zero threads in #pipeline (those are missing-cost values, not capacity).

*Goes into the real conversation in #code-review on 2025-01-21, after 15:47 dario:*

```
09:00  dermot: PR 394 should be up this morning - data generation cookbook, touches examples-cookbooks. not blocking the curent release but want it in before the nex
09:27  konrad: Can someone take a look at PR 387 when they get a chance?
09:27  konrad: It's Emil's max_tokens capacity blocking change, touches the anthropic online path
09:27  konrad: Would be good to get it merged today alongside PR 394
09:47  nikolai: good morning all, hope the coffee is holding up :slightly_smiling_face:
09:55  dermot: anything already flagged on PR 387 or is it clean going in?
10:11  dermot: ok
10:11  dermot: answering my own q - looks clean going in
10:39  konrad: PR 394 lands in examples-cookbooks so I'll review it as soon as Dermot has it up. From my side, everything is clear to receive it.
11:04  emil: - PR 387 looks clean on my end too, nothing outstanding that would hold it
- Pulled up the v0.1.16 release notes just now - both my changes are in the
11:47  dario: Are we doing anything about the older open PRs (133, 161, 362, 372) or are those just sitting until after 387 and 394 land?
11:48  dario: ok answering my own question - I'd lean toward a quick triage pass on those four this afternoon rather than waiting, some of them look like they've be
12:16  emil: +1 on doing a triage pass this afternoon, those have been sitting long enough
12:16  emil: PR 378 is in the same boat too - blocked on the cost guard but otherwise ready - so might as well roll it into the same pass
12:36  nikolai: @Dermot is PR 394 up yet? Konrad's waiting on it and we've got this afternoon to get it reviewed and in.
12:39  dermot: not up yet - finishing it now, will have PR 394 up this afternoon
12:59  dermot: week of jan 13 - v0.1.15 and v0.1.15.post1 both shipped
12:59  dermot: anything else land that week that should go in the summary?
13:29  dario: Around this afternoon for the triage pass, I can make time once PR 394 is up.
13:43  konrad: For the triage pass this afternoon, are we doing actual review on each or just a keep/close call?
13:43  konrad: Five PRs plus PR 394 in one afternoon feels like a lot
14:15  dario: My side of online-request-processing is clear so I can give PR 387 a proper look this afternoon, and I'll be in on the triage pass once PR 394 lands
14:55  konrad: So if Dario reviews PR 387 this afternoon, are we expecting to actually merge it today or is that slipping to tomorrow?
15:02  emil: Expecting PR 387 to land today - Dermot already took a pass and found nothing, so if Dario's review goes smoothly there's no reason to hold it.
15:36  dario: On PR 387 now, should have a verdict shortly
15:47  dario: PR 387 review done, looks good to merge.   <-- THE REMARK GOES HERE
15:50  emil: Are we clear to merge PR 387 now, or does it need anything else?
16:23  konrad: @Dermot two approvals on PR 387, you should be clear to merge it
17:07  emil: Ready to land from my side.
17:46  nikolai: once PR 394 is up, who's got eyes on it? it's late enough that it'll need a quick turnaround to land today.
18:19  konrad: I said I'd review PR 394 as soon as it landed, still will, but if it's not up yet I'm not sure we're getting it merged tonight.
18:24  emil: PR 387 is cleared, two approvals in.
18:29  nikolai: still around if PR 394 comes up before people sign off.
```

#### `g10.r1.rev1` — rule

**dario**, 2025-04-08, #pipeline

> on that layer, the 0.0 clamp in free_capacity is gone - forgiving the overshoot let a light estimator run past the provider ceiling three windows straight. it goes negative now, floored per axis at -CAPACITY_DEBT_FLOOR_FRACTION * limit, 0.25

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the 0.0 clamp in free_capacity is gone — forgiving the overshoot let a light estimator run past the provider ceiling three windows straight. capacity goes negative now, floored per axis at -CAPACITY_DEBT_FLOOR_FRACTION * limit, fraction 0.25.

*Why there:* #pipeline is the rate-limit and token-accounting room, and on 2025-04-08 it's already chewing on DeepSeek rate limit headers coming back absent and whether the layers underneath degrade gracefully — Dermot asks that outright at 14:40. Dario owns that check that day (he pulls Emil into a 15:06 sync on it), so him reporting what he changed in the capacity accounting sits on the live thread rather than opening a new one. Nobody there has touched free_capacity or the clamp, so it isn't redundant; the mild stretch is that the overshoot cause is a light estimator rather than the missing headers, which is why it reads as an adjacent finding from the same dig instead of a direct answer.

*Must appear literally:* `free_capacity`, `CAPACITY_DEBT_FLOOR_FRACTION`, `0.25`, `0.0`

*Goes into the real conversation in #pipeline on 2025-04-08, after 14:40 dermot:*

```
09:00  dermot: pr 614 is mostly through, I've got the main batch cancellaton fixes in place and just want to confirm the failed_requests.jsonl shape is right before 
09:00  dermot: @Dario does failed_requests.jsonl get read back on a resume pass, or is it only written to at the end?
09:36  gideon: Batch cancellation fixes finally clearing is a good way to start the week
10:17  dermot: has anyone seen the rate limit headers coming back from deepseek behaving oddly?
10:27  dermot: anyone know if the llama4 model ids could collide with anything in the openai or deepseek registry?
11:00  gideon: @Emil can you do a quick check on the llama4 model ids against the OpenAI and DeepSeek entries in the registry?
11:21  emil: I'll check the llama4 ids against the registry this afternoon.
11:21  emil: And Dermot, yeah - I've been seeing some inconsistent behavior from the DeepSeek rate limit headers too, worth comparing notes on that.
11:37  dario: @Dermot, honestly I'd lean toward write-only at completion, but I'm not fully sure we've settled whether the resume pass should be consulting it at al
11:39  dermot: gotcha
11:54  dario: On the DeepSeek rate limit headers, are the values coming back wrong or just absent in some responses?
12:12  emil: Absent on certain responses, not wrong values - they just don't show up at all on some calls.
12:41  dermot: ws-055 has the e2e provider credentail question still open for CI - no owner and nothing decided yet
12:41  dermot: with deepseek and llama4 both landing, which provider are we targeting for the nightly smoke run?
13:00  gideon: @Emil still need the registry result back here this afternoon to close out the provider paths today.
13:45  dario: @Emil, are you getting enough runway this afternoon to close out both the registry check and the header issue, or is one of them going to slip?
14:13  emil: - Registry check on the llama4 ids against OpenAI and DeepSeek still in progress, results before end of day
- DeepSeek header issue: headers absent on
14:40  dermot: do absent rate limit headers from deepseek affect the retry logic at all, or does that layer degrade gracefully?   <-- THE REMARK GOES HERE
15:06  dario: @Emil, want to grab 15 min before end of day to go through the DeepSeek header behavior together?
15:06  dario: I want to check whether the retry layer handles absent headers cleanly before we call it
15:51  emil: Dario, yeah - let's do it, ping me when you're free.
16:00  dermot: @Dario when you're done with Emil, can you confirm whether the resume pass should be reading failed_requests.jsonl?
16:15  dario: You mean read it to skip already-failed rows, or something else?
16:16  dario: Can't fully sign off on the retry/DeepSeek header question until I've done the sync with Emil, and that's still pending.
16:16  dermot: yeah
16:17  dermot: skip already-failed rows on retry
17:12  dario: Ok, checking now whether the resume pass is actually wired to read from it
17:31  gideon: Still waiting on Emil's registry result to close out the provider paths on my end
```

> **Problems:** longer than one remark

#### `g10.r1.rev2` — rule, observability

**emil**, 2025-04-16, #pipeline

> also from the batch-side pass: 0.0 isn't the floor anymore, minute two opens owing the overshoot down to -CAPACITY_DEBT_FLOOR_FRACTION * limit and num_capacity_debt_clamps counts each such call.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the "zero is the floor, next refill starts clean" line is gone — a bucket at 0.0 isn't the whole story now. minute two opens owing the overshoot, floored at -CAPACITY_DEBT_FLOOR_FRACTION * limit, and num_capacity_debt_clamps counts each such call.

*Why there:* That day is the rate-limit/capacity path audit: Gideon asked at 10:05 whether cost streaming feeds the rate-limit or capacity check, Emil took the batch side that afternoon and promised to post whatever he found, and at 17:32 he already reports one finding phrased in terms of "the capacity window". A second finding from the same pass — that the capacity bucket no longer floors at 0.0 and carries overshoot as debt into the next minute — lands in the room that owns token/rate accounting, from the person who was reading that code, and it complicates Gideon's independence question rather than arriving from nowhere.

*Must appear literally:* `0.0`, `CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_debt_clamps`

*Goes into the real conversation in #pipeline on 2025-04-16, after 17:32 emil:*

```
09:00  gideon: - PR 632 batch update freq fix is in, CLI observability side looking good
- still need to confirm cost streaming doesn't mess with the projected-remai
09:19  gideon: When cost data arrives late from the provider, what does the projected-remaining readout actually show in the interim?
10:05  gideon: Does cost streaming data feed into the rate-limit or capacity check at all, or are those calculated independently?
11:10  gideon: Is there a consistent way batch and online costs are represented right now, or are they still in different shapes depending on the provider path?
11:39  emil: cost streaming impl is in on my end, but i'm not entirely sure it's clean of the rate-limit path, that's honestly the thing I wanted to confirm before
11:50  dario: if neither of us is confident the rate-limit path is clean, I'm not sure we should be calling cost streaming ready for next sprint's provider work yet
12:20  emil: I'll go through the rate-limit path on the batch side this afternoon and flag anything that looks off
12:20  emil: @Dario can you check the same on the online side?
12:36  emil: are batch and online costs currently in the same shape, or are they diverging by provider path right now?
12:41  emil: pulled up WS-050, it's closed - covered Gemini batch bug fixes in PRs 614 and 621, nothing in there about cost streaming or the rate-limit path so it 
12:41  emil: they did flag a cost accounting offset on resumed jobs as explicitly out of scope, said it's tracked separately - anyone know where that's actually li
13:53  gideon: I'll flag the projected-remaining gap as a code review item so it's documented regardless of what the rate-limit path checks turn up this afternoon.
15:23  dario: yeah I'll check the online side. Emil, how are you going on the batch path - do you think you'll get through it this afternoon?
16:08  emil: I'm partway through the batch path, not entirely sure I'll clear it before end of day but I'll post whatever I find
16:11  dario: I'll take the online-side findings and write them up tonight so we have both halves together, Emil, drop whatever you have in thread when you're done 
16:30  gideon: idk
16:30  gideon: writing it up tonight means it won't get reviewed until tomorrow at the earliest, and if both halves aren't together we might just be pushing the unce
16:31  gideon: and the readout skew specifically is on the progress bar side which I own
16:42  emil: i'm not entirely sure I'll finish the batch side tonight, so rolling it in might leave you with a gap on that half.
16:57  dario: so do we just flag the readout skew and the batch-side gap as open edge cases for code review and move forward with that documented, or are we actuall
17:32  emil: on the batch side, I'm seeing projected-remaining drop to stale values when cost data misses the capacity window - not sure yet whether it corrects it   <-- THE REMARK GOES HERE
17:53  dario: if it stays wrong until the job finishes, does that change the call on whether this is safe to build on next sprint?
18:12  gideon: I can't confirm the progress bar impact on my end until we know whether it corrects on the next update or stays stale for the whole job.
18:12  emil: so you're saying the readout is frozen at the stale value for the whole job duration, not just until the next cost event?
18:25  gideon: actually I was less precise than that - I said I couldn't confirm the impact, not that it's definitely frozen for the whole job
18:25  gideon: that's what I still don't know
18:28  dario: have you seen it self-correct at all, or is that still untested?
```


## g10.r2

**The hidden requirement:**

- **rule** — `free_capacity(used, blocked)`: the token axes gain `blocked - used` and `available_request_capacity` is left exactly as `consume_capacity` left it. `refund_capacity(blocked: _TokenUsage) -> None`: the token axes gain the whole `blocked` estimate back (capped above at the limit) and `available_request_capacity` gains exactly `1.0`, capped above at `max_requests_per_minute`. The processor's `_refund_capacity(self, status_tracker, blocked_capacity)` delegates to `status_tracker.refund_capacity(blocked_capacity)`.
- **scope** — Every terminal path through the `except Exception` branch of `handle_single_request_with_retries` calls the refund — both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`). On a tracker with `max_requests_per_minute=60`, `max_tokens_per_minute=10_000` and a reservation of `_TokenUsage(input=700, output=300)`, either failure path ends at `available_request_capacity == 60.0` and `available_token_capacity == 10000.0`, while the success path with reported usage `_TokenUsage(input=700, output=100)` ends at `59.0` / `9200.0`.
- **exclusions_or_crossover** — The failure refund uses the full blocked estimate and ignores `generic_response.token_usage` — e.g. a response with `finish_reason="length"` (in `config.invalid_finish_reasons`) reporting `_TokenUsage(input=900, output=800)` against a blocked estimate of `_TokenUsage(input=900, output=100)` returns the estimate.
- **observability** — Two tracker counters, `num_capacity_settlements: int = 0` and `num_capacity_refunds: int = 0`, each incremented by exactly one by its own operation and by neither the other's. Both counters still increment when the affected capacity is `None` and the operation is a no-op on every axis.

**Reversed earlier:** An earlier revision charged the failure path symmetrically with the success path — `_free_capacity(status_tracker, used_tokens, blocked_capacity)` using the usage the `except` block already builds — and returned the request slot on both kinds of release; it was reversed because a retry storm against a systematically failing model drained the bucket faster than the refill could recover it.

**What a reader has to infer along the way:**

- *When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.*
  - nobody says: If the estimate over-books tokens and the call succeeded, the difference is dead weight worth reclaiming, but the call itself really did happen and cannot be un-counted.
- *A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.*
  - nobody says: Work that produced nothing should leave no charge behind, so the release for failures is a different shape from the one that settles a success.
- *Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.*
  - nobody says: A release that only happens on one way out of the error handler leaks capacity on the other, and both are terminal for that attempt.
- *The failure release is sized from the reservation that was made, not from any usage the discarded response reported.*
  - nobody says: Numbers attached to a response nobody is keeping are not what was taken out of the bucket, and trusting them can hand back more than was ever booked.
- *The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.*
  - nobody says: A count is only useful for telling the two kinds of release apart if each is attributed to exactly one of them and neither goes silent.

**Names the tests reach for that the ticket withholds:**

- said: `attempts_left`, `finish_reason`

> **Spread:** one source only (slack); g10.r2.s1: two remarks in #engineering within 2 days; g10.r2.s2: two remarks in #cookbooks within 1 days; g10.r2.s4: two remarks in #cookbooks within 10 days; g10.r2.s5: two remarks in #releases within 8 days

> **9 of 29 graded assertions are not stated outright** — 9 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g10.r2.s1 — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*Nobody says:* If the estimate over-books tokens and the call succeeded, the difference is dead weight worth reclaiming, but the call itself really did happen and cannot be un-counted.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g10.r2.s1_l3` — rule

**konrad**, 2025-03-17, #engineering

> Look, we handed the slot straight back the moment the response landed, and that pushed 240 calls into a 200 minute. Provider noticed.

*What a reader should take from it:* returning the request slot on a completed call broke the per-minute request ceiling

*Step it builds toward:* `g10.r2.s1` — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*Drafted as:* We handed the slot straight back when the response landed and pushed 240 calls into a 200 minute. Provider noticed.

*Why there:* The remark is a rate-limit accounting report: the limiter released the request slot on response arrival, so a 200-requests-per-minute ceiling saw 240 calls and the provider pushed back. That is squarely the request layer — online concurrency, rate limits, provider backends — which is #pipeline's subject, and none of the listed conversations are in that room or anywhere near it. The 2025-03-21 #code-review thread is the closest by vocabulary (Emil on the online processor appending to the responses file at accept time rather than at return), but that thread is about batch-mode scope, retry placement and the cache-dir/metadata-db split; a rate-ceiling overshoot lands there as a subject change nobody picks up. The #engineering days are torch guards, pricing-lookup cost safety and release notes; #cookbooks is verifiers and examples; #releases is the v0.1.22 cut. Konrad plausibly says this — he works the cost/limit side — but not on any of these days, in any of these rooms. It wants a #pipeline thread where the limiter's slot-release timing is being reworked, so that a sibling remark about token capacity and about what failed calls should do has somewhere to sit alongside it.

*Still leaves open:* says nothing about tokens, and nothing about what failures should do

*A new conversation in #engineering on 2025-03-17:*

```
14:03  dario: konrad was the 429 wave last night their side, or something we did
14:05  konrad: ours. look, we handed the slot straight back the moment the response landed
14:06  dario: enough to push us over though? most of those calls are tiny
14:08  konrad: 240 went into a 200 minute. the quick ones kept freeing room we hadnt earned yet
14:09  dermot: did that stay in our logs or did it get as far as the provider
14:10  konrad: no, provider noticed. thats what the mail this morning was about
14:12  dermot: mhm. so the give-back is hanging off the wrong thing
14:13  konrad: right. it comes back with the window, not with the reply
```

#### `g10.r2.s1_l4` — rule

**nils**, 2025-03-19, #engineering

> let me think through that - a request that actually reached the provider is spent for that minute whatever came back, it does not un-happen.

*What a reader should take from it:* a request that went out stays counted against the minute

*Step it builds toward:* `g10.r2.s1` — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*Drafted as:* a request that actually reached the provider is spent for that minute whatever came back, it does not un-happen.

*Why there:* Both candidates are Mistral/PR 584 threads: 2025-03-17 is about the shape of token usage in batch responses for cost accounting, 2025-03-25 is about whether dropping Mistral fixture tests thins provider coverage. Neither is chewing on rate-limit accounting, and this remark settles what happens to a per-minute request budget when a call comes back an error — it would land in the middle of a test-coverage sign-off and get no reaction. #pipeline is the right room (rate limits are explicitly its charter), just not either of those days; the conversation that should exist is the one where someone asks whether a failed or retried request gives its slot back, which is where nils' "it does not un-happen" is the answer and the token/reservation half is left to someone else.

*Still leaves open:* says nothing about the token side, or about how much of a reservation is returned

*A new conversation in #engineering on 2025-03-19:*

```
13:42  konrad: we had a minute where nearly all the calls came back errors. does that minute get its budget back?
13:43  konrad: off the top of my head i had assumed failed ones dont count against you
13:47  nils: let me think through that - a request that actually reached the provider is spent for that minute
13:49  dermot: so an error response still counts, even with nothing usable in it
13:50  nils: whatever came back, yes. it went out, it does not un-happen
13:51  nils: the line is whether it left us, not what came back. one that never got sent never owed the minute anything
13:53  konrad: right. not what the code does today though
13:55  dermot: mhm, the late night run reads differently now. i was watching the wrong half of it
```

#### `g10.r2.s1_l2` — rule

**dario**, 2025-04-16, #engineering

> per-request i think - on a clean response the only thing we put back into the budget is the gap between what we booked and what it actually spent

*What a reader should take from it:* a successful call returns the unused portion of its token estimate

*Step it builds toward:* `g10.r2.s1` — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*Drafted as:* on a clean response the only thing worth putting back is the gap between what we booked and what it actually spent.

*Why there:* That thread is live on exactly this mechanism: dario said at 13:15 he's been tracing the online-request-processing capacity check and that it reads headers independently of the cost stream, and gideon then asks at 13:48 whether the gap shows up per-request or accumulates over a run. A line from dario about what a clean response actually returns to the budget answers the per-request half of gideon's question and sharpens why the projected-remaining readout can skew while the capacity check itself may be fine. He's the only person tracing that path, so he's the right speaker, and nobody has said what reconciliation puts back. It stops short of the failure path and the slot, which is what emil is still worried about at 18:00.

*Still leaves open:* says nothing about the request slot, or about what happens when the call fails

*Goes into the real conversation in #engineering on 2025-04-16, after 13:48 gideon:*

```
09:00  gideon: PR 632 is basically wrapped, batch update freq fix is in and the CLI observability side looks good, just needs a review pass
09:00  gideon: Also want to circle back on the Gemini 2.0/2.5 incompatibility at some point today, not sure if that's a blocker or just backlog at this point
09:12  gideon: For GPT-4.1 structured output, is that going in through PR 642 directly or is it expected to come through the batch side?
09:49  gideon: Anyone know the status on the Gemini 2.0/2.5 API incompatibility?
09:49  gideon: Trying to figure out if that's something we're actively tracking or if it's just sitting in the backlog
11:04  gideon: Is the cost streaming pattern settled enough to build on for next sprint's provider work, or are there still open edges?
11:12  emil: nice
11:12  emil: PR 632 off the board
11:18  dario: the gemini 2.0 vs 2.5 issue is real, I've already got it tracked on my end
11:19  dario: the response schema changed enough between versions that our provider integration layer can't handle both without branching
11:19  dario: right now nothing actively depends on 2.5
11:49  emil: for PR 642, is that going in directly from Devraj or does it need to route through the batch side first?
12:28  emil: Looks like cost data from streaming can arrive late enough that the projected-remaining readout shows stale numbers in some cases, not sure yet if the
13:11  gideon: @Dario good to know on Gemini, if nothing depends on 2.5 yet that sounds like it can stay in the backlog for now.
13:11  gideon: On the cost streaming thing Emil raised, do we know if the capacity check is pulling from the same cost data or is it working off the response headers
13:15  dario: been looking at the online-request-processing side, and from what I can tell the capacity check is using header data independently, not the cost strea
13:15  dario: I haven't fully traced the skew scenario yet though, so I wouldn't call it confirmed
13:48  gideon: In the skew scenario, is the gap showing up per-request or does it accumulate over a run?   <-- THE REMARK GOES HERE
14:40  emil: honestly, if the skew scenario is still untraced on both sides I'm not sure we should be calling cost streaming ready for next sprint's provider work 
15:31  dario: I think the capacity check is likely clean since it's pulling from headers, it's really the readout skew that's the open edge
15:31  dario: I'm not sure they're the same problem, so maybe we don't have to block the whole sprint on it
16:01  gideon: The projected-remaining readout skew is flagged for code review on my end, so that edge case won't get lost even if we move forward with cost streamin
16:38  emil: so are we calling cost streaming ready for next sprint, with the readout skew as a flagged code review item?
16:50  gideon: I'm hesitant to call it fully ready - the weekly notes I put up today captures the readout skew as still-open, so that's at least documented for whoev
17:14  dario: what's the actual risk if we proceed and the skew turns out to be more than readout-only?
17:15  dario: actually, I think if the skew reaches the capacity check and not just the readout, we could be making throttling decisions on stale cost data, which i
18:00  emil: i believe that's right, and i'm not confident yet that the batch side is clean of that scenario either
18:15  gideon: tbh I'm not sure "flagged for code review" is a strong enough gate if it could be touching throttling decisions.
18:24  dario: so do we hold cost streaming as not ready for next sprint until the throttling question is actually traced, or is someone willing to own that investig
```

#### `g10.r2.s1_l1` — rule

**gideon**, 2025-04-21, #help

> Also from the same profile - estimator books 1k output tokens on every haiku call, actual comes back under 150, and then we crawl for the rest of the minute.

*What a reader should take from it:* over-booked tokens on a successful call are costing throughput

*Step it builds toward:* `g10.r2.s1` — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*Drafted as:* Estimator books 1k output on every haiku call, actual comes in under 150, and we crawl for the rest of the minute.

*Why there:* That day is entirely about where wall clock is going on the big runs — nikolai opens with the 20k verification run losing time outside the container, and gideon is feeding in findings from his profile of the 40k row poem run (per-request capability lookup, 40k identical debug lines). A third finding from the same profile, that the estimator over-books output tokens on successful calls and the run then crawls, lands in a room already asking why throughput is bad, and gideon is the one holding the profile. Nothing said there covers the rate/token budget angle, so it complicates rather than repeats: the per-request lookup waste is a different mechanism from capacity being held. The pipeline candidates are the charter-correct room for rate limits, but 04-02 is cancellation/jsonl failure visibility and 03-26 is Mistral batch usage extraction — dropping this into either would change the subject cold.

*Still leaves open:* does not say the leftover should come back, nor anything about the request slot

*Goes into the real conversation in #help on 2025-04-21, after 13:13 gideon:*

```
09:00  nikolai: - WS-050 bug sweep is mostly done, a few edge cases to double-check
- WS-054 cost accounting still in progress, aiming to have something concrete this
09:34  gideon: Tangentially related to that - I profiled the 40k row poem run and noticed we're doing the capability lookup on every single request. Is that expected
10:09  nikolai: - dug into the verification timing, looks like the wall clock is being eaten outside the container itself, not inside it
- on Gideon's point: the capa
10:24  gideon: Yeah, good to have that confirmed. Is the lookup sitting in the request path itself, or somewhere we could plausibly pin it at run start?
10:45  nikolai: If it's the same answer for the whole run regardless, it makes more sense to resolve it once at startup and pass it down than to keep it in the reques
12:08  emil: That 20k row run is mine
12:08  emil: Most of the wall clock looks like it went to the pull step before the container even started
12:27  emil: hmm
13:13  gideon: Also from that poem run - 40k identical debug lines in the log, same line repeated every request
13:13  gideon: Anyone know where those are getting emitted?   <-- THE REMARK GOES HERE
14:06  gideon: @Nikolai Berresford is the pre-container pull step something you're already tracking, or is that new?
14:06  gideon: 40k passes over the same model string for a 40k row run, that's what the debug lines are, log output of that same lookup
14:06  gideon: profiled the 40k row poem run because the bars were stuttering, that's what put me on this
14:06  gideon: and the answer can't change between row 1 and row 40000, the model name is fixed the moment you configure the thing
14:06  gideon: and the model name is fixed the moment you configure the thing
15:04  nikolai: Yeah
15:04  nikolai: I'd flagged that
15:04  nikolai: If the fix is small enough it could probably fold into the pinning PR rather than its own thing
15:48  emil: If it's exactly 40k lines for a 40k row run, that's one log call per request.
15:49  nikolai: Is the pull happening every request, or just once at startup?
17:00  emil: No update on the pull timing from my end yet.
17:01  nikolai: Emil, do you have a rough sense of how many times the pull ran in that 20k row pass?
```

### g10.r2.s2 — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*Nobody says:* Work that produced nothing should leave no charge behind, so the release for failures is a different shape from the one that settles a success.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g10.r2.s2_l2` — rule

**dermot**, 2025-03-20, #engineering

> yeah, an attempt that errored bought us nothing, so refund_capacity returns the entire token reservation rather than whatever was left unspent.

*What a reader should take from it:* the failure release returns the entire token reservation

*Step it builds toward:* `g10.r2.s2` — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*Drafted as:* an attempt that errored bought us nothing, so refund_capacity hands the whole booking back rather than whatever was left over.

*Why there:* No candidate thread is discussing token capacity reservation or its release. The two nearest (pipeline 04-07, viewer 04-14) are about cost accounting pricing off the wrong model on resume — same vocabulary, different subsystem, and nothing there holds a reservation that could be refunded. The cache-key thread (04-23) and the submit-record thread (04-03) are persistence questions. Inserted anywhere in these, a settled statement about refund_capacity's semantics answers a question nobody asked. The conversation that should exist is the one where a long run's effective concurrency decays after a burst of provider errors, and someone works out that the limiter is leaking budget on the failure path — which is precisely #pipeline's remit (rate limits, token accounting, retries), and Dermot's, since he carries bulk-llm-inference.

*Still leaves open:* says nothing about the request slot, nor which failure paths call it

*Must appear literally:* `refund_capacity`

*A new conversation in #engineering on 2025-03-20:*

```
13:35  konrad: Quick one on capacity. when an attempt errors, what goes back? full reservation or just the part it didnt use
13:38  emil: whole thing i believe. the attempt bought us nothing
13:40  konrad: but it did burn tokens before it died. presumably that part is real
13:43  dermot: not from our side. refund_capacity hands back the entire token reservation
13:45  konrad: Right, so not whatever was left unspent
13:46  dermot: no, the full reserved amount. it errored, theres nothing to net it against
13:48  emil: sounds right. i couldnt think of a case where the partial version helps anybody anyway
```

#### `g10.r2.s2_l3` — rule

**nikolai**, 2025-03-20, #cookbooks

> counted it this morning we are doing thirty real requests a minute agaisnt a sixty ceiling because the attempts that came back 503 are still sitting on their slots

*What a reader should take from it:* failed attempts holding their request slots halves the effective request rate

*Step it builds toward:* `g10.r2.s2` — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*Drafted as:* we are doing thirty real requests a minute against a sixty ceiling, because the attempts that came back 503 are still sitting on their slots.

*Why there:* No candidate is discussing live request throughput or retry accounting. The nearest match, code-review 2025-04-08, mentions "the default rate limit config needs updating for the KlusterAI models" (issue 616), but that thread is pure PR triage — who reviews what before the cut — and the rate limit there is a config file value nobody has run against. A measured 30-of-60 throughput with 503s pinning slots would arrive from nowhere in a review queue and draw no response. The incidents day is fingerprint/cache, engineering 2025-06-03 is torch guards and litellm structured output, and the remaining code-review days are reviewer assignment. #pipeline is the room whose stated purpose is online concurrent requests, rate limits and retries, and it needs the conversation where someone actually watches a run come in at half rate.

*Still leaves open:* does not say how many slots come back per attempt, or anything about tokens

*A new conversation in #cookbooks on 2025-03-20:*

```
13:04  konrad: the cookbook batch took the whole morning again. what is actually slowing it down
13:07  dario: not the ceiling, honestly. we are nowhere near it
13:09  nikolai: counted it this morning we are doing thirty real requests a minute
13:11  konrad: thirty? we set that ceiling at sixty. so where does the other half go
13:14  nikolai: the attempts that came back 503 are still sitting on their slots
13:16  dario: so a dead attempt holds a slot same as a live one. that tracks with what i saw thursday
13:18  nikolai: right nothing lets them go so we only ever get half the lane those need to come off
13:20  konrad: ok. so the ceiling was never the problem
```

#### `g10.r2.s2_l4` — rule

**konrad**, 2025-03-21, #cookbooks

> Look, if the call errored we hand its slot back, one per attemtp, and never above what the minute started with.

*What a reader should take from it:* a failed attempt returns one request slot, capped at the per-minute limit

*Step it builds toward:* `g10.r2.s2` — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*Drafted as:* If the call errored, its slot goes back with it, one per attempt, and never over what the minute started with.

*Why there:* The remark is a settled rule about the request-layer rate limiter: a failed attempt hands back one request slot, and the bucket never refills above the per-minute ceiling. That is capacity accounting for online concurrent requests, which is #pipeline's subject. None of the candidates is chewing on rate limits or capacity refunds — 2025-04-02 is cancellation and per-backend job ID scoping, 2025-03-21 is whether retry handling belongs in PR 585 plus responses-file ordering (adjacent vocabulary, but it's about where retry code lives, not about limiter bookkeeping), 2025-05-30 and 2026-01-02 are review-queue triage, 2025-05-22 is factory cleanup scope, 2026-01-27 is GEPA null scores, 2025-06-02 is viewer download plumbing, 2025-03-24 is the examples table. Konrad appears in all of them as the person asking what the scope is, not as the person stating how the limiter behaves; dropping a limiter refund rule into any of those changes the subject and gets no reaction. It wants a #pipeline thread where someone has noticed a run's capacity not recovering after errored calls, and where a sibling message can supply the token side and the handler location.

*Still leaves open:* says nothing about the token amount, or where in the handler this happens

*A new conversation in #cookbooks on 2025-03-21:*

```
14:02  nikolai: whats meant to happen to the slot when a call comes back errored
14:03  konrad: it goes back. we took it for a call that didnt happen, so we hand it back
14:05  dario: back once for the request, or once per retry? some of these go round three or four times
14:06  konrad: one per attemtp. every attempt that errors hands its one back, not the whole request in a lump
14:07  nikolai: does that let it climb past where it was
14:08  konrad: no. never above what the minute started with, thats the ceiling
14:09  nikolai: right. ill fold it into whichever ticket ends up touching the retry loop
14:11  dario: mhm. thats what bit us tuesday, the thing ended the minute higher than it went in
```

#### `g10.r2.s2_l1` — rule

**emil**, 2025-04-10, #pipeline

> different shape but same area - gemini 503'd on everything last night, and by minute two we were down to one request every few seconds with zero successes.

*What a reader should take from it:* a run of failing calls starves capacity even though nothing was produced

*Step it builds toward:* `g10.r2.s2` — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*Drafted as:* gemini 503'd on everything last night and by minute two we were down to one request every few seconds, with zero successes.

*Why there:* That day opens with gideon asking for eyes on "odd rate limit behavior" and turns on what providers actually tell us when they throttle (bare 429s, retry-after headers, rate limit headroom tracking). Emil has just answered the DeepSeek header question, and Gemini is his lane that week (PR 621), so a second data point from him — a provider erroring rather than throttling, and the request rate collapsing anyway — complicates the thread rather than changing the subject: it says the throttle loop reacts to failures, not just to 429s. Nobody has said this; the day's only other capacity talk is dario's headroom-logging question, which it doesn't duplicate. It leaves the two things the sibling owns untouched: no number for recovery, no claim about which bucket.

*Still leaves open:* does not say how much should come back or which of the two buckets was the problem

*Goes into the real conversation in #pipeline on 2025-04-10, after 11:38 emil:*

```
09:00  gideon: online-request-processing is stable, but I've been seeing some odd rate limit behavior from DeepSeek that I want to get eyes on at some point today
09:35  gideon: does DeepSeek even send retry-after or x-ratelimit headers when it throttles, or are we just getting a bare 429?
10:20  dermot: @Emil Brandvold might be the right person on the deepseek header question, given he's been in the batch layer
10:49  gideon: @Emil, have you seen what headers DeepSeek actually sends back on a 429?
11:38  emil: From what I've seen in the batch layer, mostly bare 429s from DeepSeek - I haven't caught them sending x-ratelimit or retry-after headers back.   <-- THE REMARK GOES HERE
11:50  dario: Separate thing on PR 624, does the log removal touch anything we're using to track rate limit headroom, or is it strictly the noisier per-request line
15:11  emil: Gemini batch fix is in review (PR 621) - the finish_reason shape change is the main thing, and I want to make sure we're explicit that it doesn't brea
15:33  gideon: I pulled up the Weekly Notes, issues 207 and 233 are both noted as no progress this week, so those are still open
15:33  gideon: @Dario, PR 624 is meant to be strictly the per-request noise, but do you know if rate limit headroom tracking runs through that same log path or somew
16:17  emil: Went to check WS-050 and that page doesn't exist yet - it's mine to write, and nothing about the batch mode spec for the request layer is documented a
16:59  dario: Somehow the last hour of Thursday is always when everything surfaces at once
17:11  dario: Does "per-request noise" include any of the header logging, or is it strictly the response body lines?
17:30  dario: Anyone confirmed the rate limit header logging is outside PR 624's scope, or is that still open going into tomorrow?
18:15  gideon: Header logging question on PR 624 is still open, I'll check the actual diff tonight and confirm whether it touches any of that before it moves.
```

#### `g10.r2.say23` — rule

**dario**, 2025-04-11, #incidents

> on the refund path the processor side stays thin — `_refund_capacity(self, status_tracker, blocked_capacity)` just calls `status_tracker.refund_capacity(blocked_capacity)` and honestly that's the whole body

*What a reader should take from it:* the team agrees the processor's _refund_capacity delegates to status_tracker.refund_capacity(blocked_capacity)

*Step it builds toward:* `g10.r2.s2` — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*Drafted as:* the processor helper stays thin — _refund_capacity(self, status_tracker, blocked_capacity) just calls status_tracker.refund_capacity(blocked_capacity) and that is the whole body.

*Why there:* The remark states a settled implementation decision about the capacity-refund path — the processor helper delegating to the tracker — and none of the listed conversations is anywhere near that. The two #pipeline threads are about Mistral provider test coverage (03-25) and auth-flow safety plus unowned rate-limit issues (03-31); on 03-31 dario himself says issue 207 has no agreed approach and no owner, so dropping a decided helper signature into that day contradicts what he just said. The #code-review days are PR 632 (curator CLI batch frequency), PR 584/schema_check, and a swallowed cache-write except — different subsystems entirely. What's missing is the conversation where someone finally picks up capacity accounting: requests that get blocked never hand their reserved capacity back, and the fix gets walked through. That is #pipeline's actual remit — rate limits and token/capacity accounting — and it wants dario, who owns online-request-processing, plus emil who raised has_capacity in the first place, and gideon on the token counting side. The sibling remark about what refund_capacity puts back per axis and its cap sits naturally a few messages later in the same thread.

*Still leaves open:* how much the tracker's refund_capacity actually puts back on each axis, and what it caps that at

*Must appear literally:* `_refund_capacity(self, status_tracker, blocked_capacity)`, `status_tracker.refund_capacity(blocked_capacity)`

*A new conversation in #incidents on 2025-04-11:*

```
13:42  gideon: quick one on the refund path — what is the processor side actually meant to do with the blocked capacity? i keep drawing the arrow both directions
13:44  dermot: if i had to guess you want it thin there. the processor doesnt do the arithmetic itself, it hands the number back to the tracker
13:45  gideon: ok but thin how. does it take the tracker in or go reach for it, and does it still keep its own bookkeping after
13:47  dario: takes it in. `_refund_capacity(self, status_tracker, blocked_capacity)` — the tracker and the blocked amount, nothing else on the signature
13:48  gideon: and inside? theres got to be more in there tbh
13:50  dario: no, honestly thats the whole body. it just calls `status_tracker.refund_capacity(blocked_capacity)` and thats it. no second set of numbers on the processor side
13:51  dermot: yeah ok. that matches how i had it in my head. nobody has typed it yet as far as i know
13:52  gideon: ya. i'll stop hunting for the subtraction in the processor then. is the tracker end already sitting there or is that new as well
```

### g10.r2.s3 — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*Nobody says:* A release that only happens on one way out of the error handler leaks capacity on the other, and both are terminal for that attempt.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g10.r2.s3_l4` — scope

**emil**, 2025-03-19, #releases

> let me think through that - on a requeue the request goes back on the queue and gets estimated again, so holding the old booking against it is charging the budget twice.

*What a reader should take from it:* the requeue path must not keep the previous reservation

*Step it builds toward:* `g10.r2.s3` — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*Drafted as:* on a requeue the request goes back on the queue and gets estimated again, so holding the old booking against it is charging twice.

*Why there:* None of the candidate threads are about the token capacity budget's reservation bookkeeping. The two #pipeline threads in range are on request fingerprinting/model keys (04-23) and Mistral batch usage extraction plus the missing local batch record (04-03, 03-26); #cookbooks is on resume keys for the stratos script, #incidents on the structured output revert, #engineering on the agent response shape, and both #code-review days are PR triage. A remark about the requeue path releasing a previously booked token reservation would arrive from nowhere in any of them and get no reaction. It belongs in #pipeline — that room owns rate limits and token accounting — but in a thread where someone is actually looking at why the budget drifts down over a long run, which is the conversation that should have existed.

*Still leaves open:* says nothing about the exhausted path, nor about the request slot

*A new conversation in #releases on 2025-03-19:*

```
14:02  konrad: quick one on the budget side. when a request gets requeued, do we keep its booking or drop it?
14:06  dermot: drop, if i had to guess. it isn't in flight anymore at that point
14:09  konrad: but then nothing books it again? presumably the second attempt still needs capacity
14:15  emil: let me think through that - a requeue puts the request back on the queue like any other, so it gets estimated again on the way out
14:17  konrad: right, and the old one is still sitting there against us
14:20  emil: yup, thats the issue. holding the old booking against it is charging the budget twice for the one request
14:23  dermot: mhm. two holds, one request, and only one of them is real
```

> **Problems:** longer than one remark

#### `g10.r2.s3_l1` — scope

**gideon**, 2025-03-27, #viewer

> so basically every retry cycle on that flaky endpoint eats anohter reservation, capacity just walks down all afternoon and never comes back until we restart

*What a reader should take from it:* requests that fail and get requeued leak their reservation

*Step it builds toward:* `g10.r2.s3` — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*Drafted as:* Every retry cycle on that flaky endpoint eats another reservation. Capacity walks down all afternoon and never comes back until we restart.

*Why there:* None of the candidate days is chewing on rate-limit capacity at all. The closest, #pipeline 2025-04-02, is about cancel_batches misuse dropping requests so retry logic never fired, plus jsonl visibility on batch failures — retries as a control-flow bug on the batch path, not a token/concurrency reservation pool draining over the course of a run. 04-07 is cost accounting on resume, 03-26 is Mistral batch usage extraction, and the three #code-review days are pure review-queue traffic. Dropping "capacity walks down all afternoon" into any of them changes the subsystem under discussion and would get no reaction. The remark belongs in #pipeline (the room that owns rate limits, retries and concurrency), but in its own conversation: someone notices a long run's effective throughput decaying through the day and only recovering on restart, and gideon connects it to requeued requests never releasing what they reserved. Dermot and emil are the usual #pipeline pair for the retry/resume path, and the sibling remark about the exhausted-retries path and what gets handed back would land later in that same thread.

*Still leaves open:* does not mention the path where retries have run out, nor what should be handed back

*A new conversation in #viewer on 2025-03-27:*

```
14:12  konrad: viewer capacity has been sagging all week. by late afternoon its nowhere near where it starts
14:18  dermot: mhm. i bounced it yesterday around 5 and it was back to full straight after
14:23  gideon: so basically its the retries against that flaky endpoint. every cycle takes anohter reservation
14:27  konrad: what happens to the one the failed attempt was already holding
14:33  gideon: thats the thing, it never comes back. capacity just walks down all afternoon and stays down til we restart
14:39  dermot: yeah ok. so the retry path is the one exit that doesnt let go of it
14:45  gideon: ya. so it needs to hand it back there too, same as the other exits do. otherwise one endpoint flapping eats the whole day
```

#### `g10.r2.s3_l2` — scope

**dario**, 2025-04-07, #pipeline

> in the retry path, the branch where attempts_left is zero appends the failure and returns, thats the whole of it. our capacity charts never recover after a bad model

*What a reader should take from it:* the exhausted-attempts path does nothing but record the failure

*Step it builds toward:* `g10.r2.s3` — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*Drafted as:* the branch where attempts_left is zero appends the failure and returns, and that is the whole of it. our capacity charts never recover after a bad model.

*Why there:* Dermot opened the day wanting to confirm the Gemini batch changes don't regress "cost accounting or retry logic", and Emil answered only from memory ("neither should touch cost accounting or retry paths") — nobody actually read the retry path. Dario is the one who's been in that code and who drove the ws-050 scoping call, so him reporting what the exhausted-attempts branch actually does closes the half of Dermot's check that gideon's 10x resume bug didn't cover. It also sits in the right room: #pipeline owns retries and token/capacity accounting.

*Still leaves open:* does not say what that branch is missing, nor whether the requeue branch has the same hole

*Must appear literally:* `attempts_left`

*Goes into the real conversation in #pipeline on 2025-04-07, after 13:49 gideon:*

```
09:00  dermot: - *pr 614*: cancellation fixes are close, expect to flag it for review this morning
- gemini batch changes landed over the weekend and I want to confi
09:44  gideon: What exactly did the Gemini batch changes touch on the cost accounting side?
09:44  gideon: I want to cross-check something I saw with resume
09:44  gideon: Actually, on resume, does the cost counter pull the model from the current config or from whatever the job was originally submitted with?
09:44  gideon: I hit a case where it came out about 10x off
10:02  dermot: I'm around all day if it helps to have another set of eyes on this once it's clearer what the resume path is doing.
10:32  gideon: Appreciated, I'll ping you once I've got more to show.
10:52  dermot: did the job resume on a different model than it was originally submitted with?
11:39  emil: from what I know, the gemini batch fixes are finish reason parsing and cancellation edge cases, neither should touch cost accounting or retry paths. n
11:50  dario: that's the question I want us to actually call before end of day, to be honest
11:50  dario: if gideon's 10x case is a model-mismatch-on-resume thing and unrelated to what the batch fixes touched, does that close ws-050, or do we need a broade
12:18  dermot: not entirely sure I'd call ws-050 closed until we know gideon's case is actually isolated from the batch fix scope.
12:28  emil: not convinced gideon's case is in scope for ws-050, honestly.
12:28  gideon: Ya
12:55  gideon: it did. The cost counter prices everything at whatever model the current config says at resume time, but the responses come back from whatever the job
12:55  gideon: Someone is going to file an issue on that reported cost number and I have nothing good to say about it.
12:59  dario: - *ws-050*: gideon's case is confirmed as a resume path issue, the cost counter pricing off the current config model instead of the original submissio
12:59  dario: so I'd call ws-050 closed
13:09  gideon: I'll file the issue on the resume cost bug this afternoon so it doesn't get lost.
13:40  dario: when you file it, is there a clear repro or is it more of an observed symptom at this point?
13:49  emil: notes-2025-03-31 still isn't in my inbox - whoever owes that should probably get it out before the day closes
13:49  gideon: More observed symptom right now, I hit it once and saw the number, I don't have a minimal repro yet.   <-- THE REMARK GOES HERE
```

#### `g10.r2.s3_l3` — scope, rule

**nils**, 2025-04-07, #general

> let me think - _refund_capacity should be firing at the point we give up on a request entirely, and right now nothing calls it there

*What a reader should take from it:* the give-up path must perform the release

*Step it builds toward:* `g10.r2.s3` — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*Drafted as:* _refund_capacity should be firing at the point we give up on a request entirely, and right now nothing does.

*Why there:* Both candidate threads are the same conversation in two rooms: PR 584, the Mistral batch processor, which fixture tests get dropped, and the missing WS-047 spec. Neither one is chewing on the capacity accounting at all — nobody has mentioned the budget, the limiter, or a request being abandoned, so a line about `_refund_capacity` never firing on the give-up path would change the subject cold and draw no reply from Emil or Dario, who are both mid-argument about coverage sign-off. The room for it is #pipeline (token accounting and rate limits are explicitly its beat), just not the 03-25 test-coverage day. What should exist is the thread where someone notices a run wedging because capacity taken out of the budget is never handed back when a request is finally abandoned — that is where Nils saying which path owes the release lands on something live, and where a sibling remark about the requeue path and the amount can sit next to it.

*Still leaves open:* says nothing about the requeue path, or how much is handed back

*Must appear literally:* `_refund_capacity`

*A new conversation in #general on 2025-04-07:*

```
13:41  konrad: capacity budget never climbed back after the run i killed friday. still low this morning
13:43  gideon: killed how? like you cancelled it, or it gave up on its own
13:45  konrad: gave up. we stopped trying that request at all, thats where it flattened
13:48  nils: let me think - _refund_capacity is what should be firing at that moment, the point we give up on a request entirely. i dont think we ever covered that one
13:50  gideon: so what calls it there today
13:52  konrad: nothing does. i grepped after standup, no caller at that spot at all. elsewhere it fires fine, just not there
13:54  nils: yeah, thats the hole. the call site simply isnt written yet, and that's worth documenting somewhere
13:56  konrad: anyway that matches friday, it sat flat for hours after
```

### g10.r2.s4 — The failure release is sized from the reservation that was made, not from any usage the discarded response reported.

*Nobody says:* Numbers attached to a response nobody is keeping are not what was taken out of the bucket, and trusting them can hand back more than was ever booked.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g10.r2.s4_l1` — exclusions_or_crossover, rule

**nikolai**, 2025-03-24, #cookbooks

> on the failure path we hand back the token counts the failed response itself reported so the bucket finishes the minute holding more capacity than the limit allows took me a whlie to spot that

*What a reader should take from it:* sizing a failure release from the reported usage can overshoot the bucket

*Step it builds toward:* `g10.r2.s4` — The failure release is sized from the reservation that was made, not from any usage the discarded response reported.

*Drafted as:* handed back the numbers the failed response reported and finished the minute holding more capacity than the limit allows. took me a while to spot that.

*Why there:* The remark reports a bug in how the rate limiter returns reserved token capacity when a request fails — sizing the release from the usage the failed response reported, so the bucket ends the minute above its own limit. That is squarely #pipeline (rate limits, token and cost accounting, retries), and none of the candidate threads is discussing the limiter at all. The closest vocabulary match, issue 616 on 2025-04-08, is a default rate limit config for KlusterAI models blocking PR 622 — a config-values question, not a capacity-accounting one, and the remark would arrive there from nowhere and get no reaction. The invented thread gives it a live subject to answer: a run that visibly exceeded the per-minute token budget, with nikolai reporting what he found after a morning in the reserve/release path, and a sibling remark left to supply what should be handed back instead and which case produced it.

*Still leaves open:* does not say what should be handed back instead, and does not name the case that produced it

*A new conversation in #cookbooks on 2025-03-24:*

```
15:02  konrad: capacity thing again on the release run, the bucket is over the line by the end of the minute. Not entirely sure where it goes wide
15:08  nikolai: its the failure path i'd say not the limiter
15:11  konrad: what, the failed calls do not come back at all?
15:15  nikolai: they come back yep just wrong on the failure path we hand back the token counts the failed response itself reported
15:18  emil: so what gets released is whatever that response claimed for itself, not what we held. thats the gap?
15:21  nikolai: right so the bucket finishes the minute holding more capacity than the limit allows
15:24  nikolai: took me a whlie to spot that every number in there looks fine on its own
15:29  konrad: look, thats a whole morning I spent staring at the limiter. it sits on the error path then
```

> **Problems:** longer than one remark

#### `g10.r2.s4_l2` — exclusions_or_crossover

**konrad**, 2025-04-03, #cookbooks

> Look, the length ones are worst - finish_reason length, and the reponse reports 800 output against the 100 output we actually booked for it.

*What a reader should take from it:* a discarded response can report far more usage than was reserved

*Step it builds toward:* `g10.r2.s4` — The failure release is sized from the reservation that was made, not from any usage the discarded response reported.

*Drafted as:* The length ones are worst: finish_reason length, 800 output reported against the 100 output we actually booked for it.

*Why there:* The remark is about the request layer's token accounting: a response that gets thrown away still reports usage far above what the limiter reserved for it. That is #pipeline material (rate limits, token and cost accounting, retries), and none of the candidate days are in that room or on that subject. The closest, #engineering 2025-06-03, is about a pricing-lookup guard returning None for unknown models — a different problem (cost of known-vs-unknown models, not reserved-vs-reported usage on a discarded response), and Konrad has already closed his cost item there, so this would arrive from nowhere and derail a dormancy-readiness thread. The #releases and #code-review days are PR-status and tag coordination. What should exist is a #pipeline thread where someone is reconciling the capacity budget against the usage actually returned, Konrad chips in that truncated responses are the worst case, and someone else settles which of the two numbers the limiter should charge.

*Still leaves open:* does not say which number the release should use, only that the two disagree

*Must appear literally:* `finish_reason`

*A new conversation in #cookbooks on 2025-04-03:*

```
15:31  nikolai: went through todays run log, the output we booked and what the responses report back dont line up on a chunk of them
15:33  konrad: Look, the length ones are worst. the rest are close enough i think
15:34  nikolai: length meaning what
15:35  konrad: finish_reason length. the truncated ones
15:37  nikolai: how far off are we talking on those
15:38  konrad: took one at random, the reponse reports 800 output
15:39  nikolai: against what we had booked for it
15:40  konrad: against the 100 output we actually booked for it. anyway those we handle the way we agreed for the others, nobody has typed it up yet
15:42  dario: mhm. thats not something you smooth over in an estimate
```

#### `g10.r2.s4_l3` — exclusions_or_crossover

**nils**, 2025-04-21, #general

> let me think — on the throw-away path the booking is the only number we own, and refund_capacity hands it back clamped so available_token_capacity never ends above the limit.

*What a reader should take from it:* a discarded response's usage numbers are not used for capacity arithmetic

*Step it builds toward:* `g10.r2.s4` — The failure release is sized from the reservation that was made, not from any usage the discarded response reported.

*Drafted as:* we only trust reported usage when we are keeping the response. on the throw-away path the booking is the only number we own.

*Why there:* Neither candidate is chewing on capacity arithmetic. The #pipeline 2025-03-17 thread is about one narrow thing — whether Mistral batch responses hand cost accounting the usage *shape* it expects — and Nils is the one who can't close it; him dropping a settled rule about trusting reported usage there would both change the subject and cut against his own "token usage for cost accounting isn't confirmed on my end yet." Nothing in that day introduces a booking/reservation concept or a discarded-response path for the remark to pick up. #code-review 2025-03-24 is pure PR shepherding — who has 583, when Emil gets to 584 — with no accounting substance at all. The remark assumes vocabulary ("the booking", "the throw-away path") that only exists once the room has been arguing about a token capacity budget that reserves before a request and reconciles after; that conversation belongs in #pipeline, which owns rate limits, retries and token accounting, and it should be prompted by a concrete overshoot rather than bolted onto the Mistral shape blocker.

*Still leaves open:* does not say what goes wrong if you use the reported numbers, or on which paths this applies

*Must appear literally:* `available_token_capacity`, `refund_capacity`

*A new conversation in #general on 2025-04-21:*

```
14:09  dermot: on the discard path what do we actually hand back? theres no real count coming home
14:13  nils: let me think — the booking is the only number we own there, so thats what goes back
14:16  dermot: so we return the reservation as-is. doesnt that risk overshooting the ceiling
14:19  nils: refund_capacity hands it back clamped, so available_token_capacity never ends above the limit
14:21  nikolai: right so worst case its a no op
14:24  nils: more or less. thats worth documenting right next to the refund call i think
14:26  nikolai: yep. beats keeping a second number around for a response were dropping anyway
```

### g10.r2.s5 — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Nobody says:* A count is only useful for telling the two kinds of release apart if each is attributed to exactly one of them and neither goes silent.

*6 remarks — 1 reporting the problem, 5 settling the design.*

#### `g10.r2.s5_l2` — observability

**konrad**, 2025-04-11, #cookbooks

> Look, the tracker dump needs num_capacity_settlements and num_capacity_refunds as separate counters, otherwise I cannot tell the two kinds of release apart in a run.

*What a reader should take from it:* the tracker carries two named counters for the two releases

*Step it builds toward:* `g10.r2.s5` — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Drafted as:* Put num_capacity_settlements and num_capacity_refunds in the tracker dump so I can tell the two kinds of release apart in a run.

*Why there:* This is a request-layer accounting decision — a capacity budget tracker that releases reserved tokens two different ways and needs named counters for each. That is squarely #pipeline territory (token and cost accounting, rate limits, concurrency). None of the eight candidates is in #pipeline, and none is chewing on anything adjacent: 2025-05-23 and 2026-01-02 cookbooks are about example freshness and CI wiring, both releases threads are version-bump logistics, 2025-06-02 viewer is download plumbing and dormancy handover, 2025-03-20 engineering is PR sequencing across provider backends, and both code-review days are about specific PRs (612, 652/654) with no capacity work in sight. Dropping a counter-naming decision into any of them would change the subject and draw no reply. #viewer touches token and cost counters, but those are the end-of-run display surface, not the tracker's internal release bookkeeping — same words, different subsystem. The conversation that should exist is Konrad reviewing the capacity budget tracker's instrumentation with the people who own the request layer, on the day the settle/refund split is being implemented.

*Still leaves open:* does not say which operation touches which counter, or whether a no-op still counts

*Must appear literally:* `num_capacity_settlements`, `num_capacity_refunds`

*A new conversation in #cookbooks on 2025-04-11:*

```
13:36  dario: when a hold gets released back to the pool, does the tracker dump show that anywhere or is it just folded into the totals
13:39  konrad: its all one bucket right now. fine until you actually have to read it
13:41  dario: so one release count, or do you want it broken out
13:43  konrad: broken out. num_capacity_settlements as its own counter in the dump
13:44  konrad: and num_capacity_refunds seperate, next to it
13:47  emil: whats actually wrong with the one number though
13:51  konrad: look, summed together i cannot tell the two kinds of release apart in a run. thats the whole of it
13:53  emil: ok that i buy. added up they read as the same event and they arent
```

#### `g10.r2.say25` — observability

**gideon**, 2025-04-14, #viewer

> so basically i dumped the trakcer on one of those unlimited runs and available_request_capacity comes back as None, so there is no number to watch there, only the counters.

*What a reader should take from it:* the team agrees an unlimited tracker's available_request_capacity holds None

*Step it builds toward:* `g10.r2.s5` — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Drafted as:* Also - the tracker dump on those unlimited runs shows available_request_capacity as None, so there is no number there to watch, only the counters.

*Why there:* None of the four candidates is anywhere near rate-limit trackers. The 2025-04-24 #pipeline thread is gideon and emil on whether batch job status tracking reads off the pbar state after the update-frequency fix — a lifecycle-divergence question, not a capacity-field question, and konrad and dermot (who carry the sibling lines about the counters and the token axis) aren't in it at all. The three #code-review days are PR triage: 04-15 is 632/637/639 merge state, 05-01 is 643/651/658 plus the WS-055 writeup, 05-05 is confirming 0.1.24 landed and unblocking 652/654. A tracker dump showing a None capacity field would arrive from nowhere in all three and get no reaction — #code-review wants "here is a PR, here is the subsystem, is it blocking a release." The subject is rate limits and token/cost accounting, which is #pipeline's whole remit. What should have existed: a #pipeline thread a day or two after the 05-05 release check, with gideon, konrad and dermot, where somebody runs against a backend with no rate limits configured and the tracker display comes up blank, and the three of them pin down what the tracker actually holds on an unlimited run — gideon on the request-capacity field being None, konrad on what the counters still do, dermot on whether the token axis behaves the same way.

*Still leaves open:* what the counters do on such a run, and whether the token axis behaves the same way — konrad and dermot's lines cover that

*Must appear literally:* `available_request_capacity`

*A new conversation in #viewer on 2025-04-14:*

```
14:12  dermot: for the capacity row in the viewer, do we draw it the same on the unlimited runs? or is there something to hide there
14:14  gideon: so basically i dumped the trakcer on one of those unlimited runs to look. the counters are all sitting there like normal
14:15  dermot: sure but the capacity number itself, thats what i'm asking about
14:16  emil: let me think through that. i believe it just pins at the ceiling and never moves? that would still be a number at least
14:18  gideon: no thats the thing, available_request_capacity comes back as None on those. so there is no number to watch there, um, nothing to put in that spot
14:19  dermot: mhm. so that row has nothing behind it at all
14:20  gideon: ya. only the counters on those runs, thats all the panel has to work with
```

#### `g10.r2.s5_l1` — observability

**emil**, 2025-04-17, #pipeline

> honestly, the last progress counter we ticked from both paths never matched the request count. these two only move on release — an acquire bumps neither num_capacity_settlements nor num_capacity_refunds.

*What a reader should take from it:* one shared counter across both kinds of release makes the totals meaningless

*Step it builds toward:* `g10.r2.s5` — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Drafted as:* the counter ticked from the same place on both paths, so the totals never lined up with the request count and i stopped reading them.

*Why there:* That thread is explicitly about whether cost and progress accounting behaves the same on two paths, and it closes with Dario concluding "both paths pull from the same usage block, so cost and progress accounting should land the same way" — i.e. sharing one source is treated as reassurance. Emil has already been the one pushing back on conditional reassurance twice that day ("should be clean if the list is right" is still a conditional), and he's speaking from the batch-mode side, so a short "we've been burned by exactly this shape before" from him lands naturally at the end: the last counter that got ticked from one shared place on both paths never matched the request count. It complicates the settled note rather than repeating it, and it says nothing about what the counters should be named or what happens when nothing moves.

*Still leaves open:* does not say what the counters should be called, or what happens when nothing moves

*Must appear literally:* `num_capacity_refunds`, `num_capacity_settlements`

*Goes into the real conversation in #pipeline on 2025-04-17, after 16:33 dario:*

```
09:00  gideon: The online-request-processing side of things is solid, but I want to double-check that GPT-4.1 structured output responses are flowing through cost an
10:20  gideon: Is GPT-4.1 in STRUCTURED_OUTPUT_MODELS already, or does it need to be added?
11:21  gideon: ok answering my own question, i think i can just check the list directly, but separately, is STRUCTURED_OUTPUT_MODELS the one place that needs updatin
11:34  dario: o3 basically confirmed STRUCTURED_OUTPUT_MODELS is the single edit point, I dropped the model name in there the morning it went live and structured ou
11:35  dario: Still want to verify GPT-4.1 is in the list and that the response mapping isn't creaing any blind spots in cost/progress accounting
12:10  emil: From the batch-mode side, cost accounting reads from the same response fields regardless of output type, so if the response mapping is correct upstrea
12:11  emil: The piece I'd want to confirm is that GPT-4.1 structured output responses actually populate those fields the same way regular completions do, which is
12:43  emil: Has anyone actually verified GPT-4.1 is in STRUCTURED_OUTPUT_MODELS, or is that still an open question?
14:54  gideon: - *online-request-processing*: response mapping looks correct for the path we care about
- *GPT-4.1 in STRUCTURED_OUTPUT_MODELS*: haven't confirmed it
15:27  emil: I'd want to actually confirm GPT-4.1 is in the list before we call this settled, "should be clean if the list is right" is still a conditional.
16:05  dario: I'll pull up the list now and confirm.
16:32  emil: While you're in there, can you also check whether the response mapping for GPT-4.1 structured output hits the same cost and progress fields as a regul
16:33  dario: GPT-4.1 is in the list, confirmed. And the mapping looks consistent with regular completions on the usage fields:

```python
STRUCTURED_OUTPUT_MODELS    <-- THE REMARK GOES HERE
```

#### `g10.r2.s5_l3` — observability

**nikolai**, 2025-04-24, #releases

> ran anthropic overnight with no token ceiling set and the counts never moved off `num_capacity_settlements: int = 0` / `num_capacity_refunds: int = 0` so i spent the morning hunting a bug that wasnt ther

*What a reader should take from it:* an unlimited tracker reports no releases at all

*Step it builds toward:* `g10.r2.s5` — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Drafted as:* ran anthropic with no token ceiling set and the release counts sat at zero all night, which had me hunting a bug that was not there.

*Why there:* None of the eight candidates is chewing on token capacity accounting. The code-review days are PR triage and merge-state chasing; 2026-01-23 only shares the word "anthropic" (it's about model identifier strings); 2026-01-27 shares the shape of a silently-swallowed value but is GEPA null scores in code-execution, so this would change the subject. The engineering days are backend_params defaults and agent response shape — 2025-05-21 touches usage metadata only as a question about what the response object carries, not a tracker's counters. This is a request-layer debugging report (overnight provider run, no token ceiling, release counters flat at their declared defaults), which is #pipeline's remit: token accounting, rate limits, provider backends. It also needs someone who owns the tracker to react, and nobody in these rooms that day does.

*Still leaves open:* does not say what the count should have done instead, nor which counter it was

*Must appear literally:* `num_capacity_refunds: int = 0`, `num_capacity_settlements: int = 0`

*A new conversation in #releases on 2025-04-24:*

```
14:07  dermot: the anthropic run from last night, did any of the capacity numbers move
14:09  nikolai: no i ran it overnight with no token ceiling set at all and the counts never moved
14:11  dario: flat on both counters or just the settlements one
14:12  dermot: both. report came back with `num_capacity_settlements: int = 0` and the refunds one right under it
14:14  nikolai: yep and `num_capacity_refunds: int = 0` is word for word what the field declares so what i got back and what it starts at are the same string i cant tell one from the other by looking
14:16  dario: so broken or not, i cant tell from that either
14:18  nikolai: thats the thing that run doesnt answer it i spent the morning hunting a bug that wasnt ther in anything i was reading were not calling it broken off a run with no ceiling on it someone sets one low enough to actually get hit and runs it again thats the only version of this thats worth anything
```

> **Problems:** longer than one remark

#### `g10.r2.say24` — observability

**nils**, 2025-04-29, #general

> let me think — if nobody configures a token limit, available_token_capacity is None for the whole life of that tracker, it never becomes a number.

*What a reader should take from it:* the team agrees an unlimited tracker's available_token_capacity holds None

*Step it builds toward:* `g10.r2.s5` — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Drafted as:* let me think — when nobody configures a token limit, available_token_capacity is None for the whole life of the tracker, it never becomes a number.

*Why there:* Neither candidate is chewing on tracker state. The 03-17 #pipeline day is narrowly about the *shape* of Mistral batch usage fields (prompt/completion/total tokens) feeding cost accounting and whether PR 584 can be unblocked — a capacity/limit tracker holding None is a different subject, and dropping it in would change the topic mid-thread with nobody to answer it. The 03-25 #code-review day is pure release triage: which of 584/585/579/468/565 lands, who reviews what; no semantics of any kind are being settled there, so a claim about tracker internals would arrive from nowhere. The sibling remarks are attributed to dermot and gideon, neither of whom is in either conversation, which is the giveaway that the real thread is elsewhere. It belongs in #pipeline (rate limits and token accounting are explicitly that room's beat) on a day when someone actually reads a status dump off an unlimited run: gideon pastes the tracker state from a run with no token limit set, sees None where he expected a number and asks whether it's a bug; nils works through what the unlimited case actually holds, and dermot covers the release-counter and request-axis half.

*Still leaves open:* whether a release against that unlimited axis still bumps a counter, and what the request axis holds — dermot's line and the dump gideon reads carry those

*Must appear literally:* `available_token_capacity`

*A new conversation in #general on 2025-04-29:*

```
15:04  dermot: quick one — if nobody configures a token limit anywhere, what does available_token_capacity read as
15:06  nils: None. i think it's None from the moment that tracker comes up, there's nothing to compute it from
15:07  dermot: right, but it gets backfilled later? i couldn't find where i'd look for that
15:09  nils: let me think — no. it stays None for the whole life of that tracker, it never becomes a number
15:10  dermot: mhm. so not a startup gap, just the state
15:11  nils: yeah. nothing sets it after the fact, so anything reading it has to cope with None the whole way through. that's worth documenting
15:13  emil: yup, that explains the one i was staring at this morning, it was blowing up on the compare
```

#### `g10.r2.s5_l4` — observability

**dermot**, 2025-05-02, #releases

> we're counting the call, not whether it moved a number. a release against an unlimited axis went through the same code path, so it still increments.

*What a reader should take from it:* a release increments its counter even when it changes no capacity

*Step it builds toward:* `g10.r2.s5` — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*Drafted as:* count the call, not whether it moved a number. an unlimited axis went through the same code either way.

*Why there:* The remark is about the accounting semantics of a capacity budget's release path — that the counter tracks calls, not capacity deltas, so a release against an axis with no limit still increments. None of the six candidates is anywhere near that subject. The two 2025-04-23 and 2025-06-26 #pipeline threads are cache fingerprints and streaming routing; 2025-05-13 is a logger.warning grep; #engineering 2025-05-01 is the executor image tag; #random 2025-04-17 is the mkdir -p billing story. #code-review 2025-05-05 contains "release" only in the version-cut sense, which is the trap — dropping a limiter-release remark into a thread about 0.1.24 and PR 652/654 would be the most visible plant of the six. The right room is #pipeline, which owns rate limits and token/cost accounting, but it needs a thread where someone is actually staring at acquire/release counts that don't line up with observed capacity changes.

*Still leaves open:* does not name the counters or say that each operation has its own

*A new conversation in #releases on 2025-05-02:*

```
14:11  dario: quick one before i touch the capacity counter — a release on an axis that had no limit set. counted, or skipped?
14:14  emil: my read is counted but honestly not entirely sure. nothing moved on that axis so you could argue either way
14:16  dermot: counted. we're counting the call, not whether it moved a number
14:18  dario: even when there was nothing to give back though? unlimited before, unlimited after
14:20  dermot: mhm. a release against an unlimited axis still went through the same code path as any other one, so it goes in the count
14:21  emil: yup, no special case to thread through then
14:23  dario: ok. the fixture i wrote assumes the opposite so thats mine to redo
```

> **Problems:** contains its own forbidden term 'increment'

### Herrings — believed at the time, overturned later

#### `g10.r2.h1` — herring

**dario**, 2025-01-21, #releases

> ok, settled: one release call for both outcomes — _free_capacity(status_tracker, used_tokens, blocked_capacity) — and the request slot goes back on failure exactly like it does on success.

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* settled: one release call for both outcomes — _free_capacity(status_tracker, used_tokens, blocked_capacity) — and the request slot goes back on failure exactly like it does on success.

*Why there:* The subject — releasing reserved token capacity and the request slot on the failure path, symmetric with success — is squarely #pipeline, but none of the listed days is chewing on it. 01-21 is the closest (PR 387 blocking OTPM capacity before send, cost-guard None fallback) yet nobody there raises what happens to blocked capacity when a request fails, so a "settled:" call with a concrete helper signature would arrive from nowhere and land on no thread. 02-19 is the concurrent logger, 03-01 is the token-default reverts, 03-10 is Mistral per-line usage extraction — all token-adjacent vocabulary, none of them the capacity-release path. What should exist is a short #pipeline thread a few days after the PR 387 capacity check lands, prompted by a run where failed requests never gave their blocked capacity back and throughput bled off: gideon or emil noticing the tracker's available capacity drifting down over a long run, emil (online-request-processing) digging out that only the success path calls the release helper, an argument about whether the failure path should release the full blocked estimate or just the used tokens, and dario closing it with the single-call decision above.

*A new conversation in #releases on 2025-01-21:*

```
15:12  konrad: quick one - when a request fails out, who gives the tokens back? i see the success path doing it and nothing on the other side
15:14  dario: same call does both. one _free_capacity and both outcomes go through it, theres no second path
15:17  konrad: ok. what does it take? off the top of my head the failure side does not have the same things in scope
15:19  dario: _free_capacity(status_tracker, used_tokens, blocked_capacity). thats the whole signature, and the failure side actually has all three sitting right there already
15:22  dermot: and the request slot? restating my guess - that one only comes back when the call actually returned
15:24  dario: no, it goes back on failure too, exactly like it does on success. no difference there
15:26  konrad: mhm. i had two helpers half drawn in my diff, one of them can go
```

#### `g10.r2.h2` — herring

**emil**, 2025-01-28, #releases

> except branch already has used_tokens built, so failure settles through the same _free_capacity(used, blocked) call as success. slot goes back on every terminal path.

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* The except branch already has used_tokens built, so failure settles with the same _free_capacity(used, blocked) as success. Slot returns on every terminal path. That's the shape.

*Why there:* The remark settles the failure-path semantics of the token capacity budget in online request processing: the except branch reuses _free_capacity(used, blocked) with the already-built used_tokens, and the request slot is returned on every terminal path. None of the candidate threads is chewing on capacity accounting. 01-27 is Gemini batch params and cost calc; 02-06 is unhashable-schema cache drops; 02-14 code-review is the progress bar PR and PR status triage; 02-19 is the PR 518 logger and whether the concurrent retry path was stress tested (retries, but logging behavior, not capacity release); 02-26 is CURATOR_CACHE_DIR resolution timing; 03-04 is sprint/PR ownership; 03-10 is whether Mistral batch populates per-line usage — token accounting, but parsing provider response fields, not releasing in-flight budget. 01-24 cookbooks is example scripts. Dropped into any of them the remark answers a question nobody asked. It wants its own #pipeline thread: a run that stalls because capacity acquired before a request never comes back when the call raises, with Emil owning the fix and stating the symmetric shape.

*A new conversation in #releases on 2025-01-28:*

```
14:05  nikolai: quick one on the capacity accounting does the slot come back when the call raises or only on the happy path
14:07  dario: id assume it comes back but honestly i couldnt point at where
14:09  emil: it comes back. by the time we're in the except branch we already have used_tokens built, so theres nothing to go reconstruct there
14:11  nikolai: having it built isnt the same as handing it back tho. what does the handing back
14:13  emil: the same _free_capacity(used, blocked) call success goes through. failure settles through that one, not a second thing
14:15  dario: and the bails further up, the ones that never get to the request?
14:16  emil: slot goes back on those too, every terminal path out of that function
14:18  nikolai: right so no second set of bookkeping anywhere
```

#### `g10.r2.rev1` — rule, scope

**dario**, 2025-04-09, #incidents

> the one _free_capacity(used_tokens, blocked_capacity) for both outcomes was the 240 in a 200 minute. failure refunds via refund_capacity(blocked), estimate plus 1.0 slot back; success free_capacity(used, blocked), slot stays spent.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the one _free_capacity(used_tokens, blocked_capacity) call for both outcomes is gone. failure goes through refund_capacity(blocked), full estimate back plus 1.0 on the slot; success keeps free_capacity(used, blocked) and the slot stays spent. 240 calls in a 200 minute.

*Why there:* No listed conversation is about admission control. #pipeline 2025-03-17 is about the shape of Mistral batch token usage for post-hoc cost accounting, and #pipeline 2025-04-21 is batch job-reuse/reattach — neither touches blocked capacity, request slots, or refunds on failure. The two #engineering days and #code-review 2025-04-08 are PR-status triage with no implementation detail, and #releases 2025-03-24 is a merge-window call. The remark would arrive from nowhere and get no reaction in all of them. It needs a #pipeline thread where the limiter is observed over-admitting, which is exactly that room's remit (rate limits, token accounting, retries) and exactly the kind of request-path internals dario is rewriting in this period.

*Must appear literally:* `_free_capacity`, `refund_capacity`, `free_capacity`

*A new conversation in #incidents on 2025-04-09:*

```
13:21  dermot: the 240 in a 200 minute last night - if i had to guess its the release path
13:22  dermot: we settled this months ago, one _free_capacity(status_tracker, used_tokens, blocked_capacity) for both outcomes, and the request slot going back on failure exactly like it does on success
13:24  dario: mhm, and thats the half thats gone. a request that actually landed spent its slot for that minute. handing it back is how you get 240 out of a 200 minute
13:25  gideon: So two calls now instead of the one?
13:26  dario: yeah. success side is free_capacity(used, blocked), and the slot stays spent
13:27  dermot: and failure? not entirely sure what youre keeping there. the estimate comes back, but the slot too or no
13:28  dario: refund_capacity(blocked) on that side, so the estimate plus the 1.0 slot back. nothing went out, so the minute never owed it in the first place
13:30  gideon: Ya ok. the retry loop hits the release twice on a timeout today, that was fine when both outcomes went through the same call
```

> **Problems:** longer than one remark

#### `g10.r2.rev2` — rule, exclusions_or_crossover

**emil**, 2025-04-03, #viewer

> the except branch builds used_tokens but refund_capacity(blocked) refunds the whole estimate, and the slot returns on failure only, not success. saw 800 output reported against a 100 booking.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* Dropped settling failure with the used_tokens the except branch builds — refund_capacity(blocked) returns the whole estimate instead, and the slot comes back on failure only, not success. A length response reported 800 output against a 100 booking.

*Why there:* Every listed room is chewing on something else: 2025-03-26 #pipeline is about where Mistral puts usage in batch responses (cost extraction, not capacity booking), 2025-04-29 #pipeline is stdout scope and provider-agnostic structured output, and the #code-review days are PR queue triage on schema_check, streaming, and CuratorResponse. The remark is about the online request layer's capacity accounting — an estimate booked up front, an except branch that computes used_tokens but a refund_capacity(blocked) that returns the full estimate, and a request slot released only on the failure path. That is squarely #pipeline territory (rate limits, token accounting, retries) but there is no live thread it answers; it would arrive from nowhere. It should have been its own #pipeline thread, prompted by a long run whose effective concurrency drains over time — gideon reporting the symptom, emil reading the settle/refund path and finding both the ignored used_tokens and the leaked slot, dario asking whether resume replays the booking.

*Must appear literally:* `used_tokens`, `refund_capacity`

*A new conversation in #viewer on 2025-04-03:*

```
13:38  dario: when a call raises, whats actually going back to the pool? i had failure and success settling the same way in my head
13:41  emil: thats the old plan and its dead. we had it that the except branch has used_tokens built already, so failure settles through the same _free_capacity(used, blocked) as success, slot back on every terminal path. the code does neither half
13:43  dario: ok so what does the except branch do
13:44  emil: builds used_tokens, then calls refund_capacity(blocked). the whole estimate goes back and the used count just sits there
13:46  konrad: Which is the right way round, imo. I pulled a failed one reporting 800 output against a 100 booking
13:48  emil: yup. on failure the booking comes back whole, the reported usage doesnt enter into it. 800 or otherwise
13:49  dario: mhm. and the slot? i genuinely thought that one came back everywhere
13:51  emil: failure only. the release lives in the except branch and the success path just doesnt do it. thats the part that has to move
13:53  konrad: Anyway, is the old version written down somewhere? id rather strike it before someone builds to it
```

