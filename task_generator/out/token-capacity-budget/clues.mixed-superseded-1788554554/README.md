# Clues for g10 — Online token-capacity budget: reservation, refund and reported limits

37 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

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
| 2025-01-21 | #code-review | dario | one thing worth notng while I'm in 387 - free_capacity clamps at 0.0 so available_token_capacity never drops below zero, an under-estimate just gets forgiven rather than carried into the next window | *herring* |
| 2025-01-21 | #pipeline *(new)* | emil | ok, settled then: the floor is 0.0 on every axis. if a model burns more than we reserved, the window absorbs it, nothing owed to the next one. | *herring* |
| 2025-01-21 | #engineering *(new)* | dario | ok, got through the PR 387 diff - the except branch calls _free_capacity with the used_tokens it alredy builds, same as the success path, so both hand the request slot back. | *herring* |
| 2025-01-23 | #engineering *(new)* | gideon | so basically one release helper, one shape: _free_capacity(tracker, used, blocked) on every terminal path, and the slot comes back whether the attempt suceeded or blew up | *herring* |
| 2025-03-14 | #code-review *(new)* | emil | the 0.0 floor didn't survive - the window stopped absorbing overshoot, next minute just opens owing it. each axis now floors at -CAPACITY_DEBT_FLOOR_FRACTION * limit, and num_capacity_debt_clamps ticks once per call that bottoms out. | `rule`, `scope`, `observability` |
| 2025-03-14 | #engineering *(new)* | dermot | when we let go of a failed attempt, the number we hand back should be the one we held at reservation time, not whatever the response reports — we still have that request object in hand at that point. | `exclusions_or_crossover` |
| 2025-03-17 | #code-review *(new)* | gideon | so basically 60 clean calls inside the minute and the request bucket still read 60 the whole way, then the 429 obviosuly. a success must not hand the slot back. | `rule` |
| 2025-03-17 | #engineering *(new)* | dario | dropped the except branch feeding _free_capacity its used_tokens — a model failing every call drained the bucket dry. failures call refund_capacity(blocked) now, full blocked estimate back, request slot up 1.0 | `rule`, `exclusions_or_crossover` |
| 2025-03-18 | #code-review *(new)* | konrad | Look, request bucket hit 62 wtih the limit at 60 while retries flowed back, we put back more than we took. A release must never push above the per-minute limit. | `rule` |
| 2025-03-19 | #engineering | gideon | Anthropic run last night: output ceiling is 40k, input is 100k, and output got let sink as deep as input, four windows to recover. So basically each axis floors against its own limit. | `scope` |
| 2025-03-19 | #pipeline *(new)* | nils | the count came out at forty-odd on the soak and nothing ever went under - every refill that topped out at the per-minute limit was ticking it. capped refills shouldn't count. | `exclusions_or_crossover` |
| 2025-03-19 | #pipeline | nils | not entirely clean on my end i think — pointed it at a model that fails on every call, request bucket bottomed out in about two minutes and never came back up. | `scope` |
| 2025-03-19 | #code-review *(new)* | gideon | honestly though, one release counter for both kinds means i can't see the retry churn at all in the dashbaord, a run thrashing on retries looks identical to a quiet hour. | `observability` |
| 2025-03-19 | #engineering *(new)* | gideon | so basically one-helper-one-shape is gone — free_capacity(used, blocked) settles tokens only and leaves available_request_capacity where consume_capacity spent it. both except exits call _refund_capacity, which moves num_capacity_refunds, not num_capacity_settlements. | `rule`, `scope`, `observability` |
| 2025-03-20 | #code-review *(new)* | nils | ran the unlimited-token config overnight, both counts sat at zero even though every request went through the same release path — releases on an unlimited tracker simply go uncounted today. | `observability` |
| 2025-04-03 | thread:new|g10.r1.l2 *(new)* | konrad | Look, reserved 800 on the 1k model, real usage came back 1500, and a second later the bucket read full agian. Hour of my life on that 429. | `rule` |
| 2025-04-03 | page:engineering/token-capacity-budget-in-the-limiter.md *(new)* | nikolai | i'd say keep the two tallies seperate, a settle moves its own counter and a give back moves its own, neither touches the other | `observability` |
| 2025-04-07 | page:incidents/postmortem-kluster-ai-deepseek-output-token-default.md | konrad | Look, saw this last week: reserved 1000 for that one, it came back finish_reason length claiming 1700 used, and 1700 is what the bucket got charged. | `exclusions_or_crossover` |
| 2025-04-08 | #pipeline | dario | out of the sync with Emil: dropped the 0.0 floor in free_capacity, available_token_capacity goes negative down to -CAPACITY_DEBT_FLOOR_FRACTION * limit, fraction 0.25 - forgiving the overshoot let an under-estimating model clear the provider budget every window | `rule` |
| 2025-04-09 | thread:new|g10.r1.l5 *(new)* | dermot | for trackers where nobody configured a token limit, plan A takes the fraction off the 100k we substituted in, not off the 0 the caller handed us. | `scope` |
| 2025-04-09 | thread:new|g10.r1.l8 *(new)* | konrad | look, your branch takes the same fraciton off the request bucket too. there we reserve one slot at a time and never overshoot it, so leave that side alone. | `scope` |
| 2025-04-09 | #pipeline | dario | spent the morning grepping logs to work out whether we ever actually hit the bottom on that run, and nothing on the tracker says. it needs to count that. | `observability` |
| 2025-04-10 | #pipeline *(new)* | emil | honestly this wants to be on the tracker as num_capacity_debt_clamps, right next to the buckets — i had it hanging off the procesor twice now and it got lost across retries both times. | `observability` |
| 2025-04-10 | page:engineering/token-capacity-the-reserve-release-model-draft-for-comment.md *(new)* | dermot | yeah, on the branch where the call actually came back the only thing worth handing back is the tokens we over-guessed. the slot is spent. | `rule` |
| 2025-04-15 | thread:new|g10.r2.l14 *(new)* | dario | honestly we're counting that the call happened, not that a number changed — so it ticks even when there was nothing on that axis to move. | `observability` |
| 2025-04-16 | #pipeline | dario | online side: third minute running the poet stage went over the provider budget, and the overshoot disappears before the next window opens. we don't forgive that at the boundary. | `rule` |
| 2025-04-16 | #pipeline *(new)* | emil | then the next minute opens owing the overshoot, but we cap the carry at a quarter of that minutes tokens or a run never climbs back out. | `rule` |
| 2025-04-21 | thread:<178770212973.2301745.4705747507669611471@world.local> | emil | also WS-054: lost an afternoon to drift between what we hold and what comes back — reported usage on responses we discard isn't a sound basis for the release. | `exclusions_or_crossover` |
| 2025-04-23 | #pipeline *(new)* | gideon | so basically the seperate run reported twice what I counted by hand, because every settle that pinned both axes logged two. counting per axis just inflates it, that's wrong. | `observability` |
| 2025-04-23 | thread:new|g10.r2.l3 *(new)* | emil | i believe the right framing is that a failed attempt never got served — so it should hand back both, the tokens it parked and the request slot it took. | `rule` |
| 2025-04-23 | thread:new|g10.r2.l7 *(new)* | dario | i think both exits of that except branch want the same treatment, honestly — the one that goes back on the queue and the one thats run out of retries. | `scope` |
| 2025-05-13 | page:engineering/limiter-axes-and-what-a-block-actually-counts.md *(new)* | nikolai | i'd say one wait one tick however many axes went under at the same time otherwise the number is telling you about axes and not about runs | `observability` |
| 2025-05-13 | thread:new|g10.r1.l14 *(new)* | konrad | Look, same on the release path: freeing capacity back to exactly max_tokens_per_minute registered as one of these. Nothing was pinned, the bucket was just full — should not count. | `exclusions_or_crossover` |
| 2025-05-14 | page:engineering/review-notes-on-the-token-capacity-budget-scoping-doc-207-and-233.md *(new)* | dermot | the top of the bucket isnt an event, its just where the arithmetic stops, so keep it out of the tally. only the lower bound is worth a number. | `exclusions_or_crossover` |
| 2025-06-12 | page:engineering/capacity-debt-and-backpressure-accounting-in-the-rate-limiter.md *(new)* | nikolai | renamed it to CAPACITY_DEBT_FLOOR_FRACTION in reveiw clamp kept reading like it was about the top of the bucket and its not | `rule` |
| 2025-06-25 | page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | nils | on 207: the vllm boxes run with the token limit unset, my branch died doing arithmetic on None. nothing to take a fraction of there, so leave those buckets alone. | `scope` |
| 2025-06-26 | page:engineering/token-capacity-reservation-in-the-online-processor-issue-207-has-capacity.md *(new)* | nikolai | i mean the give back only happens in the branch that requeues once attempts_left hits 0 the request just dies still holding what it reserved and it shouldnt | `scope` |

## g10.r1

**The hidden requirement:**

- **rule** — Token capacity may go negative, but each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` with `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25` exported from the capacity-budget module. The floor is `-limit * 0.25` as a `float` for the `combined` axis. Worked case: a tracker with `max_tokens_per_minute=1_000`, after `consume_capacity(_TokenUsage(input=700, output=100))` and then settling `used=_TokenUsage(input=1000, output=500)` against `blocked=_TokenUsage(input=700, output=100)`, ends at `available_token_capacity == -250.0`.
- **scope** — A tracker constructed with `max_tokens_per_minute=0` (defaulted to 100_000) floors at `-25000.0`, and under `seperate` each axis floors against its own limit: with `_TokenUsage(input=1_000, output=500)` an over-settled tracker lands on `_TokenUsage(input=-250, output=-125, total=-375)`. An axis whose limit and capacity are `None` has no floor and stays `None`. `available_request_capacity` is never floored.
- **exclusions_or_crossover** — Capping an axis at its UPPER bound is not a clamp and never touches the counter: neither the refill in `update_capacity` raising an axis back up to `max_tokens_per_minute`, nor a release raising it to that same ceiling, increments `num_capacity_debt_clamps`. The counter increments ONLY when the lower debt floor `-CAPACITY_DEBT_FLOOR_FRACTION * limit` is applied. So a settlement whose result stays above that floor (e.g. `available_token_capacity == 100.0` on a 1_000-token tracker) leaves the counter at `0`, and so does a refill that lands exactly on `1000.0` rather than the `1200.0` it would otherwise reach.
- **observability** — A tracker field `num_capacity_debt_clamps: int = 0` increments by exactly one per call that clamped at least one axis.

**Reversed earlier:** The team first clamped debt at 0.0 (capacity is never negative, an under-estimate is forgotten), then reversed it because forgiving the overshoot let a systematically under-estimating model exceed the provider's per-minute budget every window; they settled on a bounded -25% carry-over instead.

**What a reader has to infer along the way:**

- *When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.*
  - nobody says: If the overshoot vanishes at empty the next window starts fresh and the provider budget gets breached again, so the debt has to survive the window boundary, and a debt with no bottom would stall the run forever.
- *The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.*
  - nobody says: A fraction has to be taken of a real number, so the only sensible number is whatever limit the tracker is actually enforcing on that axis at that moment.
- *The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.*
  - nobody says: If a number is meant to tell you how many operations went badly, counting axes instead makes the same run report a different figure depending on which strategy it used.
- *Reaching the top of a bucket is a different event and is not counted: neither a refill capped at the per-minute limit nor a release that lifts an axis back to that same ceiling touches the count.*
  - nobody says: A count that fires on both ends of the bucket measures nothing, since a healthy idle run tops out constantly.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `CAPACITY_DEBT_FLOOR_FRACTION`

> **Spread:** g10.r1.s1: two remarks in #pipeline within 0 days; g10.r1.s3: two remarks in #pipeline within 1 days; g10.r1.s3: two remarks in #pipeline within 13 days

### The remarks, by the step they build

### g10.r1.s1 — When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.

*Nobody says:* If the overshoot vanishes at empty the next window starts fresh and the provider budget gets breached again, so the debt has to survive the window boundary, and a debt with no bottom would stall the run forever.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g10.r1.l2` — rule

**konrad**, 2025-04-03, thread:new|g10.r1.l2

> Look, reserved 800 on the 1k model, real usage came back 1500, and a second later the bucket read full agian. Hour of my life on that 429.

*What a reader should take from it:* the team agrees an under-estimate today leaves no trace on the bucket and that this is a problem

*Step it builds toward:* `g10.r1.s1` — When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.

*Drafted as:* Reserved 800 on the 1k model, real usage came back 1500, and a second later the bucket read full again. Hour of my life on that 429.

*Why there:* All six candidates are konrad's weekly status emails — PR lists, owners, release scope. A 429 debugging story about under-reserved tokens has no thread to pick up there and would draw no reply; the closest hook, issue 233 in the Mar 31 mail, is explicitly parked as non-blocking. The remark is a request-layer symptom report that opens a design argument about token bucket accounting, and it needs interlocutors (Emil, Dario) who own the rate limiter — that is #pipeline.

*Still leaves open:* what should happen to the 700 we went over by, how deep that is allowed to go, and against which limit

*A new thread — **overnight run — throughput numbers for WS-055**, 2025-04-03:*

```
From: emil  To: konrad, dario, gideon
Konrad — did the overnight run against the small model actually finish? I went to pull the throughput numbers for the WS-055 doc this morning and the responses file looks short to me, but i'm not entirely sure i'm reading the right one.

If it died partway i'd rather know now than have Dermot find out from the wiki. Honestly the numbers matter less than knowing whether the run is trustworthy at all. Can you have a look when you get a minute?

Emil

From: konrad  To: emil, dario, gideon   <-- the remark
It finished, but not the way I planned. Short version: I spent the whole morning on it and not on the doc.

The run stalled around 3am and I could not see why. No provider outage, key is fine, concurrency was the same as friday. Reserved 800 on the 1k model, real usage came back 1500, and a second later the bucket read full again. Hour of my life on that 429. Presumably we are giving back what we reserved and not what we spent, but off the top of my head I would not swear to it.

The responses f

From: gideon  To: konrad, emil, dario
ya i saw something like this last week on my side too but i assumed i had set the limits wrong myself and just lowered concurrency until it stopped complaining. so basically i never looked into it, sorry.

honestly though if it is the accounting and not the provider then lowering concurrency is just me hiding it. happy to sit with you tomorrow and stare at the logs if that helps, i still have mine from the 28th somewhere.

From: dario  To: konrad, emil, gideon
mhm, that tracks with what i remember from the batch side, though i think the batch path takes a different route through the limiter so maybe not the same thing at all.

konrad, for thursday i'd take the rerun over the current file — shape-only numbers in a doc that dermot is going to read as rate numbers is the kind of thing that comes back at us in three weeks. in any case i'm around tonight if it stalls again.

```

#### `g10.r1.l1` — rule

**dario**, 2025-04-16, #pipeline

> online side: third minute running the poet stage went over the provider budget, and the overshoot disappears before the next window opens. we don't forgive that at the boundary.

*What a reader should take from it:* the team agrees an overshoot must not be forgiven at the window boundary

*Step it builds toward:* `g10.r1.s1` — When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.

*Drafted as:* third minute running that the poet stage went over the provider budget, and whatever we overshot by just disappears before the next window opens.

*Why there:* #pipeline on 2025-04-16 is already arguing about the capacity window and what happens across it — emil at 17:32 reports projected-remaining going stale when cost data "misses the capacity window," and dario has taken the online half of that check (15:23). A run observation from dario's online-side pass that the poet stage blew past the provider budget and the overshoot is zeroed at window rollover lands directly in that thread, and settles the stance that the boundary must not forgive it, without touching how deep past empty an axis may sit or what records it.

*Still leaves open:* how far past empty an axis is allowed to sit, what number that depth is measured against, and whether anything records it

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

#### `g10.r1.l3` — rule

**emil**, 2025-04-16, #pipeline

> then the next minute opens owing the overshoot, but we cap the carry at a quarter of that minutes tokens or a run never climbs back out.

*What a reader should take from it:* the team agrees the carried overshoot is bounded at a quarter of the minute's allowance

*Step it builds toward:* `g10.r1.s1` — When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.

*Drafted as:* then the next minute should open owing the overshoot, but no deeper than a quarter of that minute's tokens or it never climbs back out.

*Why there:* None of the listed rooms is holding a live design thread on the minute-window token budget. The closest, #engineering 2025-03-19, is an audit thread — did the output-token fix shift throttling, who owns the check — not a design argument about how a minute's overshoot is reconciled; dropping a settled cap in there would change the subject and land on nobody. #pipeline 2025-04-14 is cost metadata handoff and PR 626/632 ordering. The remark presumes a conversation where people are actually deciding the carry rule (and a sibling supplies the constant's name and the per-axis question), which is exactly the #pipeline charter — rate limits and token accounting — but that conversation isn't in the set. It should be invented: after the kluster.ai headroom miscalculation from the postmortem, someone notices a run blowing well past its per-minute token allowance and the following minute happily going over too, and the team argues about whether the next window should start in debt and how far that debt can go before a run can never catch up. Emil is the natural one to close the cap question, with Gideon pressing on the throttle path he's been chasing since March and Dario on what the request layer can actually meter.

*Still leaves open:* what the constant is called, which limit the quarter is taken of when one was defaulted in, and whether it is per axis

*A new conversation in #pipeline on 2025-04-16:*

```
```

#### `g10.r1.l4` — rule

**nikolai**, 2025-06-12, page:engineering/capacity-debt-and-backpressure-accounting-in-the-rate-limiter.md

> renamed it to CAPACITY_DEBT_FLOOR_FRACTION in reveiw clamp kept reading like it was about the top of the bucket and its not

*What a reader should take from it:* the team agrees the bound lives in a module constant with that exact name

*Step it builds toward:* `g10.r1.s1` — When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.

*Drafted as:* renamed it to CAPACITY_DEBT_FLOOR_FRACTION in review, 'clamp' kept reading like it was about the top of the bucket and it is not.

*Why there:* Every listed candidate is a meeting-notes page, a postmortem, or a CI/release design doc. The rate-limit material in them (issues 207/233, has_capacity headers, backpressure) is at the level of "nobody owns this yet" and "deferred post-dormancy" — none of them is chewing on an implemented capacity-debt bound, let alone the naming of a module constant for it. A comment announcing a rename made "in review" needs a review thread above it to be answering; dropped onto the Mar 17 or Apr 21 weekly notes it introduces a constant, a bucket and a review nobody in that document has mentioned, which is exactly the kind of paragraph a reader stops on. The right room is #code-review: a naming call on a PR touching the request layer's capacity accounting, made while the reviewer was still calling the thing a clamp.

*Still leaves open:* what value it holds, what it multiplies, and which axes it applies to

*Must appear literally:* `CAPACITY_DEBT_FLOOR_FRACTION`

*A new page — **Capacity debt and backpressure accounting in the rate limiter** in `engineering`, 2025-06-12:*

> **Why this page**

> the Jun 9 sync deferred the auto detect rate limits work (233) to post dormancy but the backpressure accounting stayed where it is and is still live in every run
> 
> so we now have a piece of the limiter that nobody is actively changing and that nobody has written down either
> 
> this is the write up of what capacity debt actually does today
> 
> i got asked twice this week what the carried number is and both times i had to go read the code so thats the reason this exists

> **What capacity debt is**

> we estimate token cost before a request goes out and we only know the real cost after it comes back
> 
> when the real cost is higher than the estimate the difference does not get thrown away it gets carried
> 
> - the overshoot for a window is summed into a debt figure
> - at the start of the next window the debt is subtracted from the available token budget
> - the debt is then cleared
> 
> that is the whole mechanic
> 
> it is not a penalty and it is not a backoff it is just accounting for tokens we already spent but had not counted at the time we spent them
> 
> i'd say the useful way to hold it in your head is that the bucket is always correct eventually and the debt is how long eventua

> **Constants** **← carries the remark**

> two constants govern this and both live next to the limiter
> 
> **CAPACITY_DEBT_FLOOR_FRACTION** — the lower bound on what a window can be reduced to by carried debt expressed as a fraction of nominal window capacity
> 
> one very large response used to be able to drive the next window down to nothing and once it is at nothing we issue no requests and once we issue no requests we never measure anything again and the limiter sits there
> 
> the floor is what stops that
> 
> we cover the remainder of the debt over subsequent windows instead of eating it all at once
> 
> naming note — this went up as a clamp and got called a clamp in review and i renamed it to CAPACITY_DEBT_FLOOR_FRACTION befo

> **What this does not do**

> worth being clear since these get conflated
> 
> - it does not discover the providers actual limits that is 233 and that is deferred
> - it does not react to 429s that is separate and lives in the retry path
> - it does not smooth anything within a window the shaping is all at window boundaries
> 
> so if you are seeing bursty issue rates inside a single window this is not the thing to look at

> **When it looks wrong**

> the symptom people report is throughput dropping off partway through a long run and not recovering
> 
> things to check in order
> 
> - is the carried debt large and stable across windows — if yes the estimator is systematically low for whatever model you are on
> - is the window budget sitting exactly at the floor — if yes the floor is doing its job and the estimator is the problem not the limiter
> - did the provider change the response shape mid run — has happened
> 
> the estimator being low is the common one
> 
> i mean the accounting is solid enough it is the input to it that drifts
> 
> if we do end up wanting per model estimator correction thats a bigger change and gotta think throug

### g10.r1.s2 — The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.

*Nobody says:* A fraction has to be taken of a real number, so the only sensible number is whatever limit the tracker is actually enforcing on that axis at that moment.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g10.r1.l6` — scope

**gideon**, 2025-03-19, #engineering

> Anthropic run last night: output ceiling is 40k, input is 100k, and output got let sink as deep as input, four windows to recover. So basically each axis floors against its own limit.

*What a reader should take from it:* the team agrees each token axis is bounded against its own limit rather than a shared one

*Step it builds toward:* `g10.r1.s2` — The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.

*Drafted as:* Anthropic run last night: output ceiling is 40k, input is 100k, and the output side was let sink as far as input was. Four windows to recover.

*Why there:* That thread is already chewing on exactly this: the output-token count fix feeding the throttle check, the postmortem finding the rate limiter calculated headroom wrong, and Gideon asking twice whether anyone has seen unexpected behavior in the backpressure path and getting no answer. Him supplying a concrete Anthropic run from the night before — output ceiling 40k vs input 100k, output capacity let sink to the input side's depth, four windows to recover — is the evidence he's been asking for, and it settles that each axis bounds against its own limit without touching how deep the sink goes, what it's a fraction of, or whether requests are affected. The other candidates only share vocabulary: #pipeline 2025-04-22's "Anthropic token issue" is malformed counts and a casting fix, and 2025-03-26 is Mistral batch usage extraction, not headroom.

*Still leaves open:* how deep the sinking should be allowed in the first place, what the depth is a fraction of, and whether requests are affected

*Goes into the real conversation in #engineering on 2025-03-19, after 10:51 gideon:*

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
10:51  gideon: For context, the token counts from the estimation path feed directly into the throttle check in online-request-processing, so that's the specific plac   <-- THE REMARK GOES HERE
11:18  konrad: Nils flagged a blocker on Mistral batch earlier this morning and I don't think we ever heard the details on it
11:26  gideon: Read through the postmortem
11:26  gideon: It confirms the rate limiter was calculating headroom wrong on kluster.ai DeepSeek runs, not just cost accounting
11:27  gideon: There's an open action item to audit the batch-mode cost estimation path against the same issue before it closes
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

#### `g10.r1.l5` — scope

**dermot**, 2025-04-09, thread:new|g10.r1.l5

> for trackers where nobody configured a token limit, plan A takes the fraction off the 100k we substituted in, not off the 0 the caller handed us.

*What a reader should take from it:* the team agrees the bound is taken against the limit actually in force, including a substituted default

*Step it builds toward:* `g10.r1.s2` — The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.

*Drafted as:* for trackers where nobody configured a token limit, plan A: take the fraction off the 100k we substituted in, not off the 0 the caller handed us.

*Why there:* None of the four mails is discussing rate-limit or token-capacity bookkeeping. The two weeklies are merge ordering, provider cost metadata and ws-055 sequencing; the Mar 14 mail is a DB row-creation OOM and semaphore repro; the Mar 19 mail is a release announcement with two fixes. A sentence deciding that the headroom fraction comes off a substituted default rather than the caller's 0 would change the subject in all of them and draw no reply. It belongs where limits, token accounting and provider backends are argued about — #pipeline — in a thread started by someone hitting a tracker that was handed no token limit and silently got the 100k default, where dermot (who writes the release/design summaries and is already the one people wait on for design calls) settles which number the fraction applies to while the fraction's size and the per-axis question stay open.

*Still leaves open:* the size of the fraction, whether each axis gets its own, and what happens when there is no limit at all

*Must appear literally:* `A`

*A new thread — **overnight run: backend reports no token rate limit, tracker shows 0**, 2025-04-09:*

```
From: nikolai  To: dermot, emil, tomas
ran the 40k set overnight against the self hosted endpoint and the headers come back with no token rate limit at all

tracker ended the run reporting max_tokens_per_minute 0 the whole way through but throughput was fine so something else was doing the pacing

before the headroom change goes in i need to know what number its actually reducing i dont want to ship a percentage off zero

From: dermot  To: nikolai, emil, tomas
mhm, i looked at this after the late night run and it is two separate things sitting on top of each other.

first: when the backend reports nothing we substitute a 100k default into the limiter, but we never write that back onto the tracker, so the tracker keeps the 0 the caller handed us and reports it out. that is a display bug and i will fix it separately, it is not the pacing.

second, and this is the part your change depends on: for trackers where nobody configured a token limit, plan A: ta

From: emil  To: dermot, nikolai, tomas
sounds right. let me think through that second bit before i touch the batch side — i beleive the batch tracker never sees the substituion at all, it builds its own limiter, so it may already be reading a diffrent number than the online path.

will check today and reply here if its actually divergent rather than just me mis-reading it.

From: nikolai  To: dermot, emil, tomas
right thats enough for me to go on

ll rerun the same set tomorrow once the display fix is in so we have a log that says what it was actually pacing against

```

#### `g10.r1.l8` — scope

**konrad**, 2025-04-09, thread:new|g10.r1.l8

> look, your branch takes the same fraciton off the request bucket too. there we reserve one slot at a time and never overshoot it, so leave that side alone.

*What a reader should take from it:* the team agrees the request bucket is excluded from this bound entirely

*Step it builds toward:* `g10.r1.s2` — The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.

*Drafted as:* Your branch takes the same fraction off the request bucket too. We reserve one slot at a time and never overshoot it, so leave that side alone.

*Why there:* All six candidates are Konrad's weekly status mails — release/PR roundups written to the whole team. None of them is a place where someone argues about token-bucket vs request-bucket semantics on a specific branch, and a line addressed to one person ("your branch... leave that side alone") inside a broadcast status mail would read as obviously spliced in. The remark is a rate-limiter design call: it belongs in #pipeline, which owns rate limits and token accounting, and it plausibly follows issue 233 (auto-detect rate limits), which Konrad himself lists as an open question in the week-of-Mar-31 mail. The conversation that should exist is the one where someone proposes bounding in-flight token capacity as a fraction of the token limit and the team settles that the request side is excluded because slots are reserved one at a time.

*Still leaves open:* what the fraction is, and which limit it is taken of on the token side

*A new thread — **branch off 233 — in-flight capacity as a fraction of the provider limit**, 2025-04-09:*

```
From: emil  To: konrad, dario, nikolai
I pushed a branch off the issue 233 rate-limit work, nothing opened as a PR yet because i wanted eyes on the shape first. The idea is that instead of a fixed number we bound how much is allowed in flight as a fraction of whatever limit the provider reports back to us — so at 0.8 we sit at eighty percent of the header value and leave the rest as headroom. we need to be intentional here about the default, i believe 0.8 is defensible but honestly that number is a guess from watching two nights of r

From: dario  To: emil, konrad, nikolai
read through it. the token side i like — we've been eating 429s on long-context batches for weeks and pulling back to a fraction of the reported limit is roughly what i'd have done, maybe with a different constant.

the part i'm less sure about is whether one knob for both is a simplification or just a coincidence. is the headroom there because we can't measure our own usage precisely, or is it there because the provider's number drifts? i think those are actually two different problems and they

From: konrad  To: emil, dario, nikolai
Look, the token side is fine. There we are estimating before the call and the estimate is bad, so a margin is the honest thing to do, 0.8 or 0.75, presumably we tune it once we have a week of data.

But. Your branch takes the same fraction off the request bucket too. We reserve one slot at a time and never overshoot it, so leave that side alone. Off the top of my head the only effect is that we run 20 percent under a limit we were already respecting exactly.

Anyway the rest reads well, the head

From: nikolai  To: konrad, emil, dario
right that matches what i saw when i was in there in march

rest of it is solid enough from my side ill take the real pass when the tests are up

```

#### `g10.r1.l7` — scope

**nils**, 2025-06-25, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md

> on 207: the vllm boxes run with the token limit unset, my branch died doing arithmetic on None. nothing to take a fraction of there, so leave those buckets alone.

*What a reader should take from it:* the team agrees an axis with no limit gets no bound and is left untouched

*Step it builds toward:* `g10.r1.s2` — The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.

*Drafted as:* the vllm boxes run with the token limit unset and my branch died doing arithmetic on None. nothing to take a fraction of there, so leave those buckets alone.

*Why there:* The Jun 23 notes have 207 (has_capacity) sitting deferred with "TBD on who picks these up", and in the same page nils flags local offline inference as in flight under the same ownership. A comment tying those two together — that the vllm path has no token limit to bound against, so has_capacity arithmetic blows up on None and those buckets stay untouched — lands on a specific line the page left open, and it's nils's own area, so the signature fits. It settles the no-limit case without touching what the fraction is, what it's taken of, or the request bucket.

*Still leaves open:* what the fraction is, what it is taken of when there is a limit, and whether the request bucket is in scope

*Goes as a comment on the real page `meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`, at: Issue 207 (has_capacity implementation): same situation, deferred:*

```
# Weekly sync notes: week of Jun 23 (batch mode)

## Status

Auto batch mode is ready to ship in v0.1.26. No blockers.

PR 690 (Fix Multimodal Gemini Batch Request Creation) is in review as of today. Nothing holding it up that I'm aware of, just needs eyes.

## Open items (deferred past v0.1.26)

- Issue 233 (rate limit detection): still unresolved, punting past this release
    - we talked about this last week too, not sure there's a clean answer yet
- Issue 207 (has_capacity implementation): same situation, deferred
    - TBD on who picks these up and when, lets circle back once 0.1.26 is out

## Also in flight

Local offline inference, same ownership. Didnt get deep into it this sync but its moving.

## Questions

- Is anyone tracking 233 and 207 for the next milestone or are they just sitting in the backlog?
```

### g10.r1.s3 — The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.

*Nobody says:* If a number is meant to tell you how many operations went badly, counting axes instead makes the same run report a different figure depending on which strategy it used.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g10.r1.l9` — observability

**dario**, 2025-04-09, #pipeline

> spent the morning grepping logs to work out whether we ever actually hit the bottom on that run, and nothing on the tracker says. it needs to count that.

*What a reader should take from it:* the team agrees the tracker must expose how often the bottom was reached

*Step it builds toward:* `g10.r1.s3` — The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.

*Drafted as:* spent the morning grepping logs to work out whether we ever actually hit the bottom on that run, and there is nothing on the tracker that says.

*Why there:* The room is already on observability of the request layer that morning — gideon is validating that "the rate limit and cost accounting surfaces cleanly through online-request-processing" and hasn't hit surprises. dario complicating that with a concrete case where he couldn't tell from the tracker whether capacity ever bottomed out is exactly the kind of gap that pass is supposed to catch, and dario is already in the thread pushing on what has to be covered before the provider changes get called clean. It states the settled bit (the tracker has to expose how often the floor was reached) without touching naming, location, or multi-axis counting.

*Still leaves open:* what the field should be called, where it lives and how it counts when several axes go under at once

*Goes into the real conversation in #pipeline on 2025-04-09, after 15:11 dario:*

```
09:00  dermot: landed 8 commits on bulk-llm-inference and the provider integration side this morning
09:00  dermot: I want someone to sanity check that the backend changes don't quietly break any of the existing providers before we go further
09:15  gideon: On the observability side, I've been validating that the rate limit and cost accounting surfaces cleanly through online-request-processing. Nothing al
09:15  gideon: Also been looking at the caching-and-resume side and haven't hit any surprises yet
09:36  dermot: Gideon, is your pass covering the batch submission path as well, or just online requests and caching so far?
14:36  gideon: Sorry, missed this
14:36  gideon: Mostly online requests and caching so far, batch submission path I haven't gotten to yet
15:11  dario: makes sense
15:11  dario: batch submission is the one path I'd want covered before we say the provider changes are clean   <-- THE REMARK GOES HERE
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

#### `g10.r1.l11` — observability

**emil**, 2025-04-10, #pipeline

> honestly this wants to be on the tracker as num_capacity_debt_clamps, right next to the buckets — i had it hanging off the procesor twice now and it got lost across retries both times.

*What a reader should take from it:* the team agrees the count is a tracker field with that exact name

*Step it builds toward:* `g10.r1.s3` — The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.

*Drafted as:* put it on the tracker as num_capacity_debt_clamps, right next to the buckets. I had it on the processor twice and it got lost across retries.

*Why there:* The remark is about where a rate-limit/token-accounting counter lives — a field on the status tracker alongside the token and request buckets, versus hanging off the processor where it doesn't survive retries. That is squarely the request-layer / capacity-accounting subject #pipeline exists for. None of the eight candidates is in #pipeline or is chewing on capacity budgets, buckets, or clamps: the two #code-review days are cache-write swallowing and PR 565 naming, #engineering 04-08 is failed_requests.jsonl fields and whether to hold DeepSeek (adjacent to rate limits, but the live argument there is jsonl schema and release sequencing, not tracker fields), #engineering 03-25 is the reuse fingerprint, #random 04-17 is the mkdir -p billing story, and all three #releases days are notes and cut contents. Dropping a settled naming decision about a capacity-debt clamp counter into any of them changes the subject and would get no reaction. It belongs in a #pipeline thread during the April rate-limit work that #engineering 04-08 already refers to ("the header anomalies Emil and Dermot flagged in pipeline"), where the clamping path is being built and someone asks where the count should be recorded.

*Still leaves open:* what makes it go up, and whether one operation pinning two axes counts once or twice

*Must appear literally:* `num_capacity_debt_clamps`

*A new conversation in #pipeline on 2025-04-10:*

```
```

> **Problems:** longer than one remark

#### `g10.r1.l10` — observability

**gideon**, 2025-04-23, #pipeline

> so basically the seperate run reported twice what I counted by hand, because every settle that pinned both axes logged two. counting per axis just inflates it, that's wrong.

*What a reader should take from it:* the team agrees per-axis counting inflates the number and is wrong

*Step it builds toward:* `g10.r1.s3` — The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.

*Drafted as:* The seperate run reported twice what I counted by hand, because every settle that pinned both axes logged two.

*Why there:* The remark reports a hand-verified 2x inflation in a tally of limiter settles, caused by settles that pin both axes logging one entry per axis. That is rate-limit and token-accounting territory, which is #pipeline's stated purpose. The two #viewer threads are about the metadata panel and release-notes cost columns; #help 2025-04-21 is the nearest neighbour (a per-request log count) but it is about a capability lookup in the request path and a pre-container pull, with no limiter or bucket in it; #help 2025-03-27 is executor image digests; #random 2025-03-18 is silent cache hits; #engineering 2025-04-10 and both #code-review days are PR-state and construction-hook threads. In any of them the remark arrives from nowhere and nobody can answer it.

*Still leaves open:* what the tally is called, where it lives, and which end of the bucket it is supposed to be about

*A new conversation in #pipeline on 2025-04-23:*

```
```

#### `g10.r1.l12` — observability

**nikolai**, 2025-05-13, page:engineering/limiter-axes-and-what-a-block-actually-counts.md

> i'd say one wait one tick however many axes went under at the same time otherwise the number is telling you about axes and not about runs

*What a reader should take from it:* the team agrees one operation that pinned at least one axis adds exactly one

*Step it builds toward:* `g10.r1.s3` — The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.

*Drafted as:* one settle, one tick, however many axes went under. otherwise the number is telling you about axes and not about runs.

*Why there:* The remark settles a counting rule for a multi-axis capacity check — one operation that pinned at least one axis increments once, not once per axis. Nothing in the listed places is chewing on that. The kluster.ai postmortem is about an estimate diverging from actuals, not about tallying saturation events; the handover page mentions issue 207 (has_capacity via rate limit headers) only as open and unowned, so a settled team decision landing as a comment there would arrive from nowhere; the Jun 9 sync explicitly defers 207/233 post-dormancy, so agreeing on counter semantics that day contradicts the page; the CI, cookbook-revert, docker-pinning and Jun 2 pages are different subjects entirely. The room for this is #pipeline, where rate limits and token/cost accounting live: a short design note on what the limiter reports when it blocks, given it tracks request, input-token and output-token budgets separately, with nikolai (online-request-processing) arguing the per-block tick and a sibling settling the field name and which end of the bucket it reads.

*Still leaves open:* what the field is called and which end of the bucket it is counting

*A new page — **Limiter axes and what a block actually counts** in `engineering`, 2025-05-13:*

> **why this is written down**

> a run sat mostly idle for the back half of an hour on 2025-05-12 and the request budget was nowhere near full the whole time
> 
> the summary line at the end said the limiter blocked 233 times against 207 waits
> 
> two numbers that ought to be the same number and are not
> 
> nobody trusts that line and i'd say thats fair because we never wrote down what it counts
> 
> so this page is the axes the limiter keeps and what a block increments
> 
> the 207 and the 233 themselves are a seperate piece of work and i am deliberately not touching them here

> **the axes**

> the limiter is not one budget it is several and they are checked together but refilled independently
> 
> - `max_requests_per_minute` plain request count in the window
> - `max_tokens_per_minute` input tokens plus the projected output tokens for the request
> - `max_concurrent_requests` how many are in flight right now regardless of size
> - provider derived limits when the provider actually sends usable headers back otherwise we fall through to the configured values
> 
> none of these share a bucket
> 
> the token axis reserves projected output up front and gives it back when the response lands so a long generation holds token budget for its whole lifetime while holding exactly one request 

> **a run can stall on one axis with the rest wide open**

> this is the normal case not the odd one
> 
> long prompts against a small `max_tokens_per_minute` will pin the token axis while requests per minute sits at maybe a tenth of its budget
> 
> from the outside it looks like the limiter is broken because the obvious number the one people watch is request throughput and that number looks healthy
> 
> if you are debugging a stall the first question is which axis went under not whether the limiter is on
> 
> log the axis by name when it blocks otherwise you are guessing

> **what a block counts**

> when the loop cannot proceed it evaluates every axis and sleeps until all of them have headroom again
> 
> that sleep is one settle
> 
> the counter moves once per settle
> 
> one settle one tick however many axes went under otherwise the number is telling you about axes and not about runs
> 
> so a request that is short on tokens and short on rpm in the same moment is one block not two
> 
> the caller waited once the queue moved once the counter goes up once
> 
> per axis counters are still worth having and we should keep them but they are their own fields with their own names they do not feed the block total
> 
> rolling them into the total is what makes the summary line drift above the wa

> **when a run stalls checklist**

> - check which axis is at ceiling before anything else `max_tokens_per_minute` first because it is the one that hides
> - compare block count against wait count they should track now if they dont the counting rule above got broken somewhere
> - confirm whether the provider headers were actually parsed or whether we silently fell back to configured values that assumption bit us before
> - look at projected output tokens the reservation is what holds the token axis not the tokens actually returned so an over generous `max_tokens` starves the run for tokens it never used
> - concurrency ceiling last it is rarely the cause but it is cheap to rule out

> **open**

> the reservation release path on request failure needs a read i am not certain we give the projected tokens back on every error branch and if we dont the token axis leaks downward over a long run
> 
> gotta think through that one properly rather than patch it blind
> 
> the rest of the above is solid enough to build on

### g10.r1.s4 — Reaching the top of a bucket is a different event and is not counted: neither a refill capped at the per-minute limit nor a release that lifts an axis back to that same ceiling touches the count.

*Nobody says:* A count that fires on both ends of the bucket measures nothing, since a healthy idle run tops out constantly.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g10.r1.l13` — exclusions_or_crossover

**nils**, 2025-03-19, #pipeline

> the count came out at forty-odd on the soak and nothing ever went under - every refill that topped out at the per-minute limit was ticking it. capped refills shouldn't count.

*What a reader should take from it:* the team agrees a refill capped at the per-minute limit must not add to the count

*Step it builds toward:* `g10.r1.s4` — Reaching the top of a bucket is a different event and is not counted: neither a refill capped at the per-minute limit nor a release that lifts an axis back to that same ceiling touches the count.

*Drafted as:* the count came out at forty-odd on a soak where nothing ever went under. every refill that topped out at the limit was ticking it.

*Why there:* Neither candidate fits: both #code-review days are PR triage roll-calls (581/583/584/585/579, defer-or-target-next-release, who's reviewing what). Nothing there is chewing on limiter refill semantics or a soak-run counter, so this would change the subject and draw no reply — and nils on those days is asking for review eyes and a WS-047 scope, not reading soak output. The subject is rate limits and token accounting, which is #pipeline. The conversation that should exist: an overnight soak of the shared limiter finishes clean — capacity never actually ran out — but the run summary still reports a few dozen capacity-exhaustion events, and nils goes looking for where the count comes from. He lands on refill: a refill that tops out at the per-minute limit is incrementing the counter even though nothing was ever starved. The thread would also cover whether the release path increments the same way and what the counter is actually supposed to measure — that part is the sibling remark's job, so it stays open here.

*Still leaves open:* whether the release path does the same, and what the count is supposed to be about instead

*A new conversation in #pipeline on 2025-03-19:*

```
```

> **Problems:** longer than one remark

#### `g10.r1.l14` — exclusions_or_crossover

**konrad**, 2025-05-13, thread:new|g10.r1.l14

> Look, same on the release path: freeing capacity back to exactly max_tokens_per_minute registered as one of these. Nothing was pinned, the bucket was just full — should not count.

*What a reader should take from it:* the team agrees a release that lifts an axis to the ceiling must not add to the count

*Step it builds toward:* `g10.r1.s4` — Reaching the top of a bucket is a different event and is not counted: neither a refill capped at the per-minute limit nor a release that lifts an axis back to that same ceiling touches the count.

*Drafted as:* Same on the release path: freeing capacity back up to exactly max_tokens_per_minute registered as one of these. Nothing was pinned, the bucket was just full.

*Why there:* All six candidates are Konrad's weekly status roundups — PR lists, release comms, examples/cookbooks ownership. None of them is chewing on the rate limiter's internals, and a sentence about the acquire/release path of the token bucket registering a bogus event would arrive from nowhere in a Monday-morning "here's what I merged" mail; there is nothing above it to answer and nobody would reply. The remark belongs to a live debugging thread about the at-capacity counter over-counting on a run, which is exactly what #pipeline exists for (rate limits, token accounting). Konrad plausibly says it there because he'd been reading the same counter output, but only in a thread where someone has already reported the inflated number on the acquire side — his contribution is "the release side does it too."

*Still leaves open:* what should be counted instead, and what the count is called

*Must appear literally:* `max_tokens_per_minute`

*A new thread — **at-capacity count from the overnight run doesn't match the stalls**, 2025-05-13:*

```
From: dario  To: konrad, emil, nikolai
the summary from last night's run says we hit capacity 3,847 times over about six hours. the run log has, honestly, maybe fifteen places where anything actually waited, and none of them for long. so either the counter is measuring something much finer grained than a stall, or we have a real stall problem that isn't showing up anywhere in the timings, and i don't think it's the second one.

i spent this morning in the token bucket trying to work out which paths increment it. there are more of the

From: konrad  To: dario, emil, nikolai
Right, the number means less than it looks like.

Every capacity check that returns negative increments it. That was the original intent, it was a debugging counter and I never renamed it. So a request that checks, gets refused, and gets admitted 40ms later on the next tick counts the same as one that waits four minutes. Presumably that alone explains most of your 3,847.

But there are also cases where nothing was refused at all. The check runs before the refill, so a request arriving one tick a

From: emil  To: konrad, dario, nikolai
so if i'm reading this right, the counter has been correct for what it was built for and wrong for what we started using it for. that sounds about right to me and it's not the first time we've promoted a debug counter into a report without anyone deciding to.

let me think through the naming before you change the semantics though. there are dashboards pulling that field i believe, and if it silently starts meaning a different thing the historical series becomes nonsense. we need to be intentiona

From: nikolai  To: emil, konrad, dario
yep new field

old one can keep counting checks i dont care what its called as long as nobody reads it out loud in a meeting again

```

#### `g10.r1.l15` — exclusions_or_crossover

**dermot**, 2025-05-14, page:engineering/review-notes-on-the-token-capacity-budget-scoping-doc-207-and-233.md

> the top of the bucket isnt an event, its just where the arithmetic stops, so keep it out of the tally. only the lower bound is worth a number.

*What a reader should take from it:* the team agrees only applications of the lower bound are counted

*Step it builds toward:* `g10.r1.s4` — Reaching the top of a bucket is a different event and is not counted: neither a refill capped at the per-minute limit nor a release that lifts an axis back to that same ceiling touches the count.

*Drafted as:* the top of the bucket is not an event, it is just where the arithmetic stops. keep it out of the tally, only the bottom end is worth a number.

*Why there:* None of the listed pages has a live thread about a token capacity budget with an upper and lower clamp, so a decision about which clamp applications get counted would arrive from nowhere in all of them. The Mar-24 and Mar-31 notes only carry "issue 207: has_capacity via rate limit headers" as an unowned open item, the Jun-9 sync explicitly defers 207/233 rather than designing them, and the handover page discusses cost/usage reporting shape, not budget bounds. The remark presupposes a design where a floor and a ceiling both exist and someone has proposed tallying clamp hits — that discussion is the one dermot flagged as needed in the Mar 24 notes ("they need a decision on approach before anyone starts coding, otherwise we'll get two half-solutions"). It belongs in #pipeline, which owns rate limits and token accounting, attached to a scoping doc for the capacity budget where dermot (online-request-processing) and dario (bulk-llm-inference) settle bounds and instrumentation before anyone writes the clamp.

*Still leaves open:* what the tally is called, and how deep the bottom end is

*A new page — **Review Notes on the Token Capacity Budget Scoping Doc (207 and 233)** in `engineering`, 2025-05-14:*

> **Why There Is One Doc And Not Two**

> 207 and 233 have been open for a while now with no owner and no agreed approach between them. they are the same problem seen from opposite ends: 207 is the request that is rejected outright because the requested `max_tokens` plus the prompt does not fit the model's context window, and 233 is the request that comes back truncated because we left the completion too little room.
> 
> dario wrote up a scoping doc this week covering the bounds, the clamping behaviour and what gets instrumented, on the reasoning that if the two issues are picked up separately we end up with two half-solutions that disagree about the arithmetic. that is the right call. these are my notes from reading it, mostly aga

> **The Arithmetic We Settled On**

> the budget for a single request is:
> 
> ```
> budget = context_window - prompt_tokens - safety_margin
> effective_max_tokens = min(requested_max_tokens, budget)
> ```
> 
> the parts that were agreed:
> 
> - `context_window` comes from the central model table, not from anything the caller passes in. if the model is not in the table we do not guess a window, we let the provider reject it as it does today
> - clamping is downward only. we never raise a caller's `max_tokens` because the window happens to allow it
> - there is a floor. if `budget` comes out below the floor there is no useful completion to be had, so we fail the request before it is sent rather than dispatch something that cannot

> **Instrumentation**

> the counter surface should stay small, otherwise every dashboard grows a line that nobody reads.
> 
> the ceiling case, where the caller asked for more than the window leaves and we hand back the smaller number, does not get a counter. the top of the bucket is not an event, it is just where the arithmetic stops. keep it out of the tally, only the bottom end is worth a number. a caller passing `max_tokens=8192` at a default and getting 6000 is the system working, and counting it would mean counting most requests.
> 
> the floor case is different in kind. hitting the floor means we could not fit a usable completion at all, which is a condition the caller wants to know about and which we are cu

> **Still Open**

> - the safety margin is per provider and the doc leaves the values as TODO. if i had to guess we want something proportional rather than a flat token count, but that wants measuring before it is written down
> - i am not entirely sure that all of the truncation reports collected under 233 come through this path. at least some of them look like provider-side stop reasons that our arithmetic would not have prevented. worth separating those out before we claim 233 is closed by this work
> - what a clamp does to a batch request, where the prompts vary in length and the `max_tokens` is set once for the whole submission, is not covered in the doc at all

> **Next**

> dario's doc needs one more pass with the instrumentation section rewritten to the above, then it can go out for wider review. ownership of 207 and 233 should land on whoever picks up the implementation, and they should be assigned together.
> 
> that said, the token count comparisons in the appendix were gathered late night off a single run against two providers. they are indicative, not something to key a default safety margin off. before anything ships those want redoing properly across the model table.

### Herrings — believed at the time, overturned later

#### `g10.r1.g10-r1-herring-clamp-zero-dario` — herring

**dario**, 2025-01-21, #code-review

> one thing worth notng while I'm in 387 - free_capacity clamps at 0.0 so available_token_capacity never drops below zero, an under-estimate just gets forgiven rather than carried into the next window

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* free_capacity clamps at 0.0 — available_token_capacity never drops below zero, so an under-estimate is just forgiven rather than carried into the next window.

*Why there:* PR 387 is explicitly "Emil's max_tokens capacity blocking change" on the anthropic online path (Emil calls it the "capacity guard" at 11:04), and dario is the second reviewer — at 15:36 he says he's in the code and at 15:47 he signs off. A note on how the capacity guard actually behaves at the boundary is exactly what a reviewer reading that path would type between those two messages, and it doesn't contradict his approval: forgiving an under-estimate is a design observation, not a blocker. Nobody else in the day has said anything about how the capacity number is computed, so it isn't redundant, and it gives Emil's 15:50 "does it need anything else?" something concrete to be asking about.

*Goes into the real conversation in #code-review on 2025-01-21, after 15:36 dario:*

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
15:36  dario: On PR 387 now, should have a verdict shortly   <-- THE REMARK GOES HERE
15:47  dario: PR 387 review done, looks good to merge.
15:50  emil: Are we clear to merge PR 387 now, or does it need anything else?
16:23  konrad: @Dermot two approvals on PR 387, you should be clear to merge it
17:07  emil: Ready to land from my side.
17:46  nikolai: once PR 394 is up, who's got eyes on it? it's late enough that it'll need a quick turnaround to land today.
18:19  konrad: I said I'd review PR 394 as soon as it landed, still will, but if it's not up yet I'm not sure we're getting it merged tonight.
18:24  emil: PR 387 is cleared, two approvals in.
18:29  nikolai: still around if PR 394 comes up before people sign off.
```

#### `g10.r1.g10-r1-herring-clamp-zero-emil` — herring

**emil**, 2025-01-21, #pipeline

> ok, settled then: the floor is 0.0 on every axis. if a model burns more than we reserved, the window absorbs it, nothing owed to the next one.

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* Settled: the floor is 0.0 on every axis. If a model burns more than we reserved, the window absorbs it and nothing is owed to the next one.

*Why there:* The remark ratifies a policy for the token capacity budget — floor of 0.0 per axis, overshoot absorbed by the current window instead of owed forward. None of the candidates is arguing about reserve-vs-actual reconciliation. 03-04 is the nearest (the output-token default bug that made kluster deepseek dump all requests at once is an under-reservation symptom), but that day's live questions are estimation accuracy and Gemini path ownership; "settled" there would settle a debate nobody had. 03-11 touches the limiter only as an int-cast correctness check on litellm estimates. 02-18 and 02-07 use 0.0/zero for missing price data, not capacity — matching numeral, different layer. It needs a #pipeline thread where the overshoot question was actually on the table.

*A new conversation in #pipeline on 2025-01-21:*

```
```

#### `g10.r1.rev1` — rule

**dario**, 2025-04-08, #pipeline

> out of the sync with Emil: dropped the 0.0 floor in free_capacity, available_token_capacity goes negative down to -CAPACITY_DEBT_FLOOR_FRACTION * limit, fraction 0.25 - forgiving the overshoot let an under-estimating model clear the provider budget every window

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the 0.0 floor in free_capacity is gone. available_token_capacity goes negative now and stops at -CAPACITY_DEBT_FLOOR_FRACTION * limit, fraction 0.25 — forgiving the overshoot let an under-estimating model clear the provider budget every single window.

*Why there:* That day #pipeline is already on the rate-limit layer: Dermot flags DeepSeek headers coming back absent, Emil confirms they're missing on some calls, Dermot asks whether the retry layer degrades gracefully, and Dario books a 15-min sync with Emil to check exactly that before end of day. When the provider headers aren't there the limiter is running on our own token estimates, so a landed change to how available_token_capacity accounts for under-estimation is the natural thing for Dario to drop back into the channel after that sync — and it complicates Dermot's "degrades gracefully" framing rather than repeating anything already said. Dario is the right speaker: he owns the sync, and he reports finished work this way elsewhere ("rewrote the reattach path over the weekend"). Nobody in the thread has touched capacity accounting yet, so it isn't redundant.

*Must appear literally:* `free_capacity`, `available_token_capacity`, `CAPACITY_DEBT_FLOOR_FRACTION`, `0.25`

*Goes into the real conversation in #pipeline on 2025-04-08, after 17:31 gideon:*

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
14:40  dermot: do absent rate limit headers from deepseek affect the retry logic at all, or does that layer degrade gracefully?
15:06  dario: @Emil, want to grab 15 min before end of day to go through the DeepSeek header behavior together?
15:06  dario: I want to check whether the retry layer handles absent headers cleanly before we call it
15:51  emil: Dario, yeah - let's do it, ping me when you're free.
16:00  dermot: @Dario when you're done with Emil, can you confirm whether the resume pass should be reading failed_requests.jsonl?
16:15  dario: You mean read it to skip already-failed rows, or something else?
16:16  dario: Can't fully sign off on the retry/DeepSeek header question until I've done the sync with Emil, and that's still pending.
16:16  dermot: yeah
16:17  dermot: skip already-failed rows on retry
17:12  dario: Ok, checking now whether the resume pass is actually wired to read from it
17:31  gideon: Still waiting on Emil's registry result to close out the provider paths on my end   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

#### `g10.r1.rev2` — rule, scope, observability

**emil**, 2025-03-14, #code-review

> the 0.0 floor didn't survive - the window stopped absorbing overshoot, next minute just opens owing it. each axis now floors at -CAPACITY_DEBT_FLOOR_FRACTION * limit, and num_capacity_debt_clamps ticks once per call that bottoms out.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* The 0.0 floor on every axis didn't survive — the window stopped absorbing the overshoot, the next minute opens owing it. Each axis floors at -CAPACITY_DEBT_FLOOR_FRACTION * limit, and num_capacity_debt_clamps ticks once per call that hit bottom.

*Why there:* The subject — per-minute capacity accounting, overshoot carrying across the window, a signed floor per axis — is squarely #pipeline material (rate limits, token accounting), but none of the listed pipeline days is chewing on it. The 2025-03-31 thread is about Mistral auth staying provider-side and about who owns issues 207/233; Emil's only capacity remark there is that `has_capacity` depends on provider rate-limit headers and that nobody owns a fix and it's in no open PR. Dropping a settled, already-implemented clamping mechanism into that same afternoon would contradict the "unowned, not in any PR" framing and change the subject. The other candidates are agentic curation, PR 678/679 test coverage, validator offline behaviour, failed_requests.jsonl fields, and per-request capability lookups — adjacent vocabulary at best. What's missing is the conversation where the 0.0-clamp behaviour was actually questioned: someone shows a run where a burst overshoots the per-minute budget, the next minute opens with a clean slate and the burst repeats, and Emil comes back having changed the floor and added the counter.

*Must appear literally:* `CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_debt_clamps`

*A new conversation in #code-review on 2025-03-14:*

```
```

> **Problems:** longer than one remark


## g10.r2

**The hidden requirement:**

- **rule** — `free_capacity(used, blocked)`: the token axes gain `blocked - used` and `available_request_capacity` is left exactly as `consume_capacity` left it. `refund_capacity(blocked: _TokenUsage) -> None`: the token axes gain the whole `blocked` estimate back (capped above at the limit) and `available_request_capacity` gains exactly `1.0`, capped above at `max_requests_per_minute`. The processor's `_refund_capacity(self, status_tracker, blocked_capacity)` delegates to `status_tracker.refund_capacity(blocked_capacity)`.
- **scope** — Every terminal path through the `except Exception` branch of `handle_single_request_with_retries` calls the refund — both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`). On a tracker with `max_requests_per_minute=60`, `max_tokens_per_minute=10_000` and a reservation of `_TokenUsage(input=700, output=300)`, either failure path ends at `available_request_capacity == 60.0` and `available_token_capacity == 10000.0`, while the success path with reported usage `_TokenUsage(input=700, output=100)` ends at `59.0` / `9200.0`.
- **exclusions_or_crossover** — The failure refund uses the full blocked estimate and ignores `generic_response.token_usage` — e.g. a response with `finish_reason="length"` (in `config.invalid_finish_reasons`) reporting `_TokenUsage(input=900, output=800)` against a blocked estimate of `_TokenUsage(input=900, output=100)` returns the estimate.
- **observability** — Two tracker counters, `num_capacity_settlements: int = 0` and `num_capacity_refunds: int = 0`, each incremented by exactly one by its own operation and by neither the other's. Both counters still increment when the affected capacity is `None` and the operation is a no-op on every axis.

**Reversed earlier:** An earlier revision charged the failure path symmetrically with the success path — `_free_capacity(status_tracker, used_tokens, blocked_capacity)` using the usage the `except` block already builds — and returned the request slot on both kinds of release; it was reversed because a retry storm against a systematically failing model drained the bucket faster than the refill could recover it.

**What a reader has to infer along the way:**

- *A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.*
  - nobody says: If a call that never got served must leave the buckets as it found them, and a call that did get served only gives back its over-estimate, then the two releases cannot be the same operation.
- *Both endings of a failed attempt do the giving-back: the one that puts the request back on the retry queue and the one where there is nothing left to retry.*
  - nobody says: A bucket that only recovers on the requeue branch will still bleed on a model that fails all the way to the end, so both exits have to be covered.
- *The amount given back after a failure is the reservation that was taken, not whatever token usage the failed response reported.*
  - nobody says: A response that was thrown away is not a measurement, so the only trustworthy number is the one held at reservation time.
- *The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.*
  - nobody says: A counter that only moves when arithmetic happens is a counter of arithmetic, not of the calls you were trying to watch.

**Names the tests reach for that the ticket withholds:**

- said: `attempts_left`, `finish_reason`

> **Spread:** g10.r2.s1: two remarks in #code-review within 1 days; g10.r2.s4: two remarks in #code-review within 1 days; : two remarks in #engineering within 2 days

### The remarks, by the step they build

### g10.r2.s1 — A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.

*Nobody says:* If a call that never got served must leave the buckets as it found them, and a call that did get served only gives back its over-estimate, then the two releases cannot be the same operation.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g10.r2.l1` — rule

**gideon**, 2025-03-17, #code-review

> so basically 60 clean calls inside the minute and the request bucket still read 60 the whole way, then the 429 obviosuly. a success must not hand the slot back.

*What a reader should take from it:* the team agrees a successful call must not get its request slot back

*Step it builds toward:* `g10.r2.s1` — A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.

*Drafted as:* Sixty clean calls inside the minute and the request bucket still read 60 the whole way. Then the 429, obviously.

*Why there:* The remark is a bucket-accounting finding: request slots are apparently being returned on success, so sixty calls burn no capacity and the provider 429s anyway. None of the listed rooms is chewing on that. The two closest are wrong in specific ways: #pipeline 2025-03-19 is the right subject (postmortem says the rate limiter miscalculated headroom, throttle path check pending) but Gideon closes that day with "Throttle check came back clean, no regressions" — this remark directly contradicts his own result, and he's the one who'd have to say both. #engineering 2025-04-16 is about cost-stream skew feeding the capacity check off headers, a token/cost question, not request slots, and inserting a concrete 429 repro there would derail a thread that's about whether an untraced skew blocks the sprint. The other pipeline days (cache fingerprint, cancellation/jsonl) and the code-review/help/incidents days are unrelated subsystems. What should exist is the day after the throttle check: Gideon's check came back clean on 3/19, and a real run then hits 429s with headroom showing free, which is exactly the thing that reopens it in the room that owns rate limits and token accounting.

*Still leaves open:* what should happen to the buckets when the attempt fails instead of succeeding, and whether the token side behaves the same way

*A new conversation in #code-review on 2025-03-17:*

```
```

#### `g10.r2.l4` — rule

**konrad**, 2025-03-18, #code-review

> Look, request bucket hit 62 wtih the limit at 60 while retries flowed back, we put back more than we took. A release must never push above the per-minute limit.

*What a reader should take from it:* the team agrees a release can never push a bucket above the per-minute limit

*Step it builds toward:* `g10.r2.s1` — A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.

*Drafted as:* Request bucket climbed to 62 against a limit of 60 while retries were flowing back. We're putting back more than we ever took out.

*Why there:* Every candidate is release coordination (#releases 2025-03-19, 2025-05-30, 2025-06-06), PR triage on finetuning/model identifiers and auth flow (#code-review 2026-01-23, 2026-01-02, 2025-03-27), recipe/CI work (#cookbooks 2025-04-03), or the agentic response-format compat thread (#engineering 2025-05-23). None of them is chewing on rate limits, token capacity, or retry accounting — a bucket overshooting a per-minute limit because releases return more than was acquired would change the subject in all seven and draw no reply. It belongs in #pipeline, which is explicitly the room for rate limits, token and cost accounting, and retries; the shared-limiter/capacity-budget work is what that room exists for, and Konrad reporting an observed overshoot plus the invariant it forces is exactly the shape of a #pipeline message.

*Still leaves open:* what a completed call should return, and how much of the token reservation comes back on a failure

*A new conversation in #code-review on 2025-03-18:*

```
```

#### `g10.r2.l2` — rule

**dermot**, 2025-04-10, page:engineering/token-capacity-the-reserve-release-model-draft-for-comment.md

> yeah, on the branch where the call actually came back the only thing worth handing back is the tokens we over-guessed. the slot is spent.

*What a reader should take from it:* the team agrees a completed call returns only unused tokens and keeps its slot spent

*Step it builds toward:* `g10.r2.s1` — A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.

*Drafted as:* on the path where the call actually came back, the only thing worth handing back is the tokens we over-guessed. the slot is spent.

*Why there:* Every listed page is adjacent at best. WS-050, the Mar 31/Mar 24 notes and the handover all *name* has_capacity (issue 207) and issue 233, but only as unowned open items — none of them is anywhere near working out what a request hands back to the budget when it finishes. The batch-persistence and image-pinning docs are about restart state and container tags; the structured-output incident and the v0.1.23 notes are unrelated. A settled decision about reserve/release semantics dropped as a comment on a release-notes stub or a Docker pinning doc reads as a plant. What is missing from the corpus is the thing dermot himself asked for in the Mar 24 notes: "207 and 233 need a decision on approach before anyone starts coding, otherwise we'll get two half-solutions." That decision doc should exist in #pipeline in April, written by whoever picked up 207, covering how much capacity a request reserves up front from the estimate, what comes back on completion, what comes back on failure, and whether the concurrency slot and the token budget are released on the same schedule. dermot's line is his answer on the completed-call branch of that doc; the failure branch is the sibling.

*Still leaves open:* what a failed attempt hands back, and whether it is sized the same way

*A new page — **Token Capacity: The Reserve/Release Model (Draft for Comment)** in `engineering`, 2025-04-10:*

> **Why This Note Exists**

> issue 207 (has_capacity detection via rate limit headers) and issue 233 (auto-detect rate limits) have carried forward unowned through three weekly notes now. i flagged on Mar 24 that neither of them should be picked up until we agree on the shape of the budget, because both issues are really the same question wearing two hats: what does the request loop hold, and when does it give it back.
> 
> so this is the write-up. it is a draft. nothing here is merged and nothing here is binding — the point is to have something concrete to comment on rather than three weeks of "no progress" bullets. if the model below is wrong, say so on the branch it is wrong in, and we amend the page.
> 
> scope is t

> **The Two Budgets**

> there are two limits and we keep conflating them, which i think is most of why 207 has stalled.
> 
> - **request slots.** requests per minute. one in-flight call occupies exactly one slot. integer, known exactly, no estimation involved.
> - **token capacity.** tokens per minute. a call occupies some number of tokens which we do not know until the response comes back.
> 
> the request budget is trivially correct because the quantity is known at admission time. the token budget is not, because at admission time all we have is an estimate — prompt tokens counted locally plus whatever ceiling we assume for the completion.
> 
> treating these as one number is what produces the behaviour Emil hit 

> **Reserve At Admission**

> before a request is dispatched, the loop takes a reservation against both budgets. a slot, and an estimated token count.
> 
> the estimate is deliberately pessimistic. prompt tokens are counted from the encoded input; completion tokens are assumed to be `max_tokens` if it is set, and a configured per-model default if it is not. we will over-reserve on essentially every call and that is intended — the failure mode of under-reserving is a 429 and a backoff, the failure mode of over-reserving is that we run slightly under capacity for a few seconds.
> 
> if either budget cannot satisfy the reservation, the request waits. it does not get dispatched-and-retried. this is the piece that `has_capaci

> **Release Paths**

> release is where the asymmetry between the two budgets shows up, and it is worth being explicit because the obvious symmetric implementation is wrong.
> 
> on the path where the call actually came back, the only thing worth handing back is the tokens we over-guessed. the slot is spent. the request occupied a slot for the duration of the window and no accounting after the fact recovers that; what we do recover is the difference between the reserved token estimate and the usage figures the provider reports on the response. that delta returns to the token counter immediately, which is what lets a run of short completions keep the pipeline full instead of throttling itself against its own pessim

> **Seeding The Limits (Issue 233)**

> 233 is the smaller problem once the above is settled. the provider returns its own view of the limits in the response headers, and we should be reading them rather than asking users to configure numbers they do not have.
> 
> proposed behaviour:
> 
> - start from a conservative built-in default per provider, so the first request has something to reserve against.
> - on the first successful response, read the limit headers and replace the defaults. subsequent responses refresh them, so a tier upgrade mid-run is picked up without a restart.
> - an explicitly configured limit always wins over the headers. people running multiple jobs against one key need to be able to hand each job a slice.
> -

> **Open Branches And What To Comment On**

> specific things i want opinions on, rather than general agreement:
> 
> 1. the timeout path. i have written it as spent-on-both, which wastes capacity. anyone who thinks we can do better than that should say what signal they would use.
> 2. the completion-token default when `max_tokens` is unset. a per-model constant is crude. not entirely sure whether a rolling observed average would be better or would just make the failure mode harder to reason about.
> 3. whether the release delta should be applied immediately or deferred to the next window tick. immediate is what i have described and what i prefer.
> 4. cross-process. two curator runs on one key will each believe they own the whole budge

#### `g10.r2.l3` — rule

**emil**, 2025-04-23, thread:new|g10.r2.l3

> i believe the right framing is that a failed attempt never got served — so it should hand back both, the tokens it parked and the request slot it took.

*What a reader should take from it:* the team agrees a failed attempt returns its whole reservation including the request slot

*Step it builds toward:* `g10.r2.s1` — A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.

*Drafted as:* an attempt that blew up never got served, so the buckets should end up where it found them: the tokens it parked and the slot it took.

*Why there:* Every listed candidate is either a weekly status roundup, a release announcement, or a thread on a different subsystem (Docker image pinning, responses-file write ordering, a DB semaphore under concurrent row creation). None of them is chewing on the token/request-slot budget, so a decision about what a failed attempt hands back to the buckets would arrive from nowhere and get no reaction. The remark needs a #pipeline thread on capacity accounting — the room that owns rate limits, retries and token accounting — during the WS-054 cost-accounting work where Emil is already the one holding the response-usage question (PR 643).

*Still leaves open:* how the token amount is sized when the response reports its own usage, and which failure endings this applies to

*A new thread — **limiter capacity draining over the course of a long run**, 2025-04-23:*

```
From: dario  To: emil, gideon, nikolai
putting this on mail rather than chat because i want the numbers somewhere findable.

the overnight job on the 90k set stalled about two thirds of the way through. it did not error, it just went slower and slower and then effectively stopped making progress. i pulled the limiter state at four points during the run:

t+00:20 - 9,940 rpm headroom, 1.94M tpm headroom
t+01:30 - 7,100 / 1.42M
t+03:00 - 3,600 / 0.71M
t+05:10 - 410 / 0.08M

nothing was reset in between, config was untouched the whole t

From: gideon  To: dario, emil, nikolai
oof yeah that curve is pretty damning. so basically every raised exception is a permanent tax on the bucket.

tbh i assumed the release was in a finally somewhere and just never checked. plus one to whatever emil says here, he has been in this code more recently than me. only thing i'd add is the retry loop makes it worse than it looks — one bad prompt gets attempted three times so it eats three slots on the way out, not one.

From: emil  To: dario, gideon, nikolai
thanks for pulling the actual numbers dario, that decay curve is about as clear as these things get. let me think through that a bit because i think there are two questions tangled up here and only one of them is hard.

the easy one is the case you hit. an attempt that raised never got served, so the buckets should end up exactly where that attempt found them — the tokens it parked and the one request slot it took both come back. Nothing was consumed on the other end, so there is nothing to acco

From: nikolai  To: emil, dario, gideon
right that split seems fine to me

i'd say keep them separate yep the second one is going to eat a week of arguing about window boundaries and this is bleeding now

one thing off the top of my head make sure whatever you do covers the cancellation path too not just raised exceptions we tear down tasks on shutdown and i do not think those go through the same exit

```

### g10.r2.s2 — Both endings of a failed attempt do the giving-back: the one that puts the request back on the retry queue and the one where there is nothing left to retry.

*Nobody says:* A bucket that only recovers on the requeue branch will still bleed on a model that fails all the way to the end, so both exits have to be covered.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g10.r2.l6` — scope

**nils**, 2025-03-19, #pipeline

> not entirely clean on my end i think — pointed it at a model that fails on every call, request bucket bottomed out in about two minutes and never came back up.

*What a reader should take from it:* the team agrees a run of terminal failures drains the buckets today

*Step it builds toward:* `g10.r2.s2` — Both endings of a failed attempt do the giving-back: the one that puts the request back on the retry queue and the one where there is nothing left to retry.

*Drafted as:* pointed it at a model that fails on every call, request bucket bottomed out in about two minutes and never came back up.

*Why there:* That day #pipeline is already arguing about the rate limiter miscalculating headroom in the postmortem and whether anyone has actually exercised the throttle path in online-request-processing since the wrapping fix. Gideon closes the day with "throttle check came back clean" — a repro where a model failing on every call drains the request bucket and it never recovers directly complicates that "clean", and it's the room for rate limits and retries. Nils is present and engaged all day, and it doesn't tread on Gideon's or Emil's checks since it's a different condition (all-terminal-failure) rather than a regression sweep. It stops short of naming which failure exit leaks or what should be handed back.

*Still leaves open:* which of the two failure exits is leaking, and what the release should hand back

*Goes into the real conversation in #pipeline on 2025-03-19, after 18:29 gideon:*

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
11:42  gideon: Has anyone actually run a check on the throttle path since the wrapping fix landed, or are we calling it clean without one?
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
18:29  gideon: Throttle check came back clean, no regressions.   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

#### `g10.r2.l7` — scope

**dario**, 2025-04-23, thread:new|g10.r2.l7

> i think both exits of that except branch want the same treatment, honestly — the one that goes back on the queue and the one thats run out of retries.

*What a reader should take from it:* the team agrees both failure exits get the same release

*Step it builds toward:* `g10.r2.s2` — Both endings of a failed attempt do the giving-back: the one that puts the request back on the retry queue and the one where there is nothing left to retry.

*Drafted as:* both endings of that except branch want the same treatment, the one that goes back on the queue and the one that has run out.

*Why there:* Every listed candidate is a release announcement or a weekly status roll-up — none of them is chewing on code at the level of an except branch in the request path, and a line about what the two failure exits return would arrive from nowhere in a "v0.1.24 is out" thread or a PR-status rundown. The nearest one (batch job status persistence) is about what survives a restart under CURATOR_CACHE_DIR, not about releasing in-flight budget when a request raises. This belongs in #pipeline, where retries, token accounting and the online request loop actually get argued about: a thread started off a run that stalled with capacity never given back, where emil and dario work out that the requeue path and the retries-exhausted path both have to give the budget back, with the sibling question — what the released amount actually is and how it's sized — still open.

*Still leaves open:* what that treatment actually returns, and how it is sized

*A new thread — **overnight online run stalled at 4/40 in flight**, 2025-04-23:*

```
From: emil  To: dario, nikolai
Morning both,

The long online run I kicked off last night is still going but it's crawling. Started at the full 40 concurrent and by about 02:00 it was down to something like 4 in flight, and it has stayed there since. Nothing has errored out, the progress bar still moves, it's just moving at a tenth of the speed it should be.

I pulled the logs and there's a cluster of 429s and a few connection resets in that window, which lines up with when it started tapering. So my working theory is that so

From: nikolai  To: emil, dario
seen this before i think, or something close to it

checked the run you left going and the tracker still says the full budget is committed even though there are four requests actually open, so it is not the server side pushing back at that point it is us refusing to start anything new

we take the tokens out before we send and we put them back after we get the response back, that much is clear enough reading it. what i cannot tell quickly is what happens on the paths where we never get a respons

From: dario  To: nikolai, emil
yeah that's mine, and i think nikolai has it basically right. the acquire is up front and the release sits on the success path, which is fine right up until it isn't.

what happens is a request raises, we come into the except, and from there it either goes back on the queue for another attempt or we've burned through the attempts and we give up on it. neither of those two exits touches the budget on the way out. so every 429 last night quietly took a slice of the capacity with it and never hande

From: emil  To: dario, nikolai
yup, that tracks with what i was seeing. Thanks for digging.

I'll leave the run parked where it is rather than killing it, in case it's useful to poke at a live wedged state. Ping me when there's something to test against and i'll re-run the same config overnight so we have a clean comparison.

```

#### `g10.r2.l5` — scope

**nikolai**, 2025-06-26, page:engineering/token-capacity-reservation-in-the-online-processor-issue-207-has-capacity.md

> i mean the give back only happens in the branch that requeues once attempts_left hits 0 the request just dies still holding what it reserved and it shouldnt

*What a reader should take from it:* the team agrees the exhausted-attempt exit currently keeps its reservation and should not

*Step it builds toward:* `g10.r2.s2` — Both endings of a failed attempt do the giving-back: the one that puts the request back on the retry queue and the one where there is nothing left to retry.

*Drafted as:* the give-back only lives in the branch that requeues; once attempts_left is 0 the request dies still holding what it reserved.

*Why there:* Every listed candidate is meeting-notes bookkeeping or an unrelated design page (docker image pinning, metadata db persistence, handover on cost reporting). None of them has anyone reserving and releasing token capacity, so a line about which branch of the retry loop returns the reservation and what happens at attempts_left 0 would land with no thread to attach to — the reader has never been told a reservation exists. The nearest topical hook, issue 207 (has_capacity via rate limit headers), is only ever mentioned as an unowned, deferred backlog item, never at the level of loop branches. The place this belongs is #pipeline, which is exactly the room for the online request layer, rate limits, token accounting and retries: after 207 got punted past v0.1.26 at the Jun 23 sync, nikolai (who owns online-request-processing) writes up how a request reserves token headroom before it goes out and gives it back when it settles, and gideon reads it against the retry path. The remark is nikolai picking at the exhausted-attempt exit in that write-up; the sizing of the give-back is stated separately in the doc body.

*Still leaves open:* what the give-back consists of and how it is sized

*Must appear literally:* `attempts_left`

*A new page — **Token capacity reservation in the online processor (issue 207 / has_capacity)** in `engineering`, 2025-06-26:*

> **Why this is written down**

> 207 (has_capacity) got deferred again at the Jun 23 sync with no owner on it
> 
> thats twice now so im writing down the shape of it before someone picks it up cold and we end up with two implementations that disagree about what a reservation means
> 
> this is a design note not a spec, nothing here is built yet. if you take 207 you can change any of it, just change it on this page too so the next person reads one story instead of three
> 
> scope is the online (non batch) processor only. batch has its own accounting and i'm not touching it here

> **What the limiter is actually tracking**

> two seperate buckets, both per model per minute
> 
> - **requests** - simple count, we already do this reasonably well
> - **tokens** - this is the one thats wrong today
> 
> the token bucket needs three numbers not one
> 
> - `max_tokens_per_minute` from config or from the providers response headers when they give them to us
> - **consumed** - tokens the provider has already billed us for in the current window, known only after a response comes back
> - **reserved** - tokens we have promised to a request that is currently in flight and has not settled
> 
> available is max minus consumed minus reserved
> 
> the reason reserved has to exist as its own number is that between send and response

> **Reserving before the request goes out**

> before anything hits the wire the request asks the limiter for headroom
> 
> 1. estimate the cost - prompt tokens counted properly plus whatever max_completion_tokens is set to. if max_completion is unset use a per model default, and i'd say be generous rather than tight, an under estimate is worse than an over estimate here
> 2. call has_capacity with that estimate. if theres not enough available the caller waits and retries the check, it does not send
> 3. on success the limiter adds the estimate to **reserved** and hands back a reservation handle. the request carries that handle for the rest of its life
> 
> the check and the add have to happen under the same lock or its not a reservation

> **Giving the reservation back when the request settles** **← carries the remark**

> every path out of a request has to release the handle, thats the whole contract
> 
> - **success** - subtract the estimate from reserved, add the real usage numbers from the response to consumed. reserved goes back to zero for this request, consumed becomes truth
> - **rate limited or transient error** - subtract the estimate from reserved and nothing gets added to consumed since nothing was billed. the request then goes back on the queue and reserves again from scratch on its next attempt, at whatever the estimate is then
> - **permanent failure** - subtract the estimate from reserved, no consumed
> 
> the third bullet is the one to be careful about because its where the existing retry code

> **Window rollover**

> consumed resets when the minute window rolls
> 
> reserved does not
> 
> a request in flight across the boundary is still in flight and still owes us a number so its reservation carries into the new window and comes off when it settles. if you clear reserved on rollover you get the same burst problem back once a minute which is worse than not having the feature
> 
> solid enough as a rule i think but its the part id want a second pair of eyes on

> **Open, not settled**

> - no owner on 207 as of today, still sitting in the backlog per emils sync notes
> - estimating completion tokens when max_completion is unset is hand wavy right now, a default per model is the cheap answer but its going to be wrong for some
> - unclear whether this lands before v0.1.26 or after. given where the release is i'd assume after
> - 233 (rate limit detection) overlaps with this, if we start reading limits off response headers the two want to share state. worth checking before either gets built

### g10.r2.s3 — The amount given back after a failure is the reservation that was taken, not whatever token usage the failed response reported.

*Nobody says:* A response that was thrown away is not a measurement, so the only trustworthy number is the one held at reservation time.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g10.r2.l10` — exclusions_or_crossover

**dermot**, 2025-03-14, #engineering

> when we let go of a failed attempt, the number we hand back should be the one we held at reservation time, not whatever the response reports — we still have that request object in hand at that point.

*What a reader should take from it:* the team agrees the failure release is sized from the reservation

*Step it builds toward:* `g10.r2.s3` — The amount given back after a failure is the reservation that was taken, not whatever token usage the failed response reported.

*Drafted as:* when we let go of a failed attempt the number to use is the one we held at reservation time; we still have that object in hand.

*Why there:* The remark is a settled call about token-budget bookkeeping: on a failed attempt, the amount released back to the capacity budget is the reservation-time estimate, and the request object is still available to read it from. None of the candidate rooms is chewing on capacity reservation at all. #pipeline on 2025-04-02 is the closest by remit (it owns rate limits and token accounting) but that day is entirely about PR 614's cancel_batches misuse and getting failed requests into jsonl output — failure paths, yes, but nobody has raised a reserve/release budget, so a sentence about "the number we held at reservation time" would land with no antecedent and no reply. #code-review 04-07 and 05-01 are PR-status traffic, #viewer 04-14 is display and provider metadata, #general 04-21 is review-backlog logistics, #releases and #cookbooks are off-subject entirely. The right home is a #pipeline thread about the limiter leaking capacity across a long run, where dermot — who owned the batch-mode failure sweep — would be the one saying which number goes back.

*Still leaves open:* whether the request slot moves with it, and which failure endings run this

*A new conversation in #engineering on 2025-03-14:*

```
```

> **Problems:** longer than one remark

#### `g10.r2.l8` — exclusions_or_crossover

**konrad**, 2025-04-07, page:incidents/postmortem-kluster-ai-deepseek-output-token-default.md

> Look, saw this last week: reserved 1000 for that one, it came back finish_reason length claiming 1700 used, and 1700 is what the bucket got charged.

*What a reader should take from it:* the team agrees a failed response's reported usage is charged today and that is wrong

*Step it builds toward:* `g10.r2.s3` — The amount given back after a failure is the reservation that was taken, not whatever token usage the failed response reported.

*Drafted as:* Reserved 1000 for that one, it came back finish_reason length claiming 1700 used, and 1700 is what the bucket got charged.

*Why there:* The postmortem's root cause is exactly that there is no cross-check between the token budget reserved for rate limiting and the token counts the response actually reports, and it flags rate limiter fidelity as impacted. Konrad's comment supplies the concrete case the page is missing: a truncated response whose self-reported usage still got charged against the bucket. It picks up the "no validation step" line rather than restating it, and it stops short of saying what number should have been charged instead or which release paths carry the fix, which the page itself leaves to the open action items.

*Still leaves open:* what number should have been used instead, and which release paths this applies to

*Must appear literally:* `finish_reason`

*Goes as a comment on the real page `incidents/postmortem-kluster-ai-deepseek-output-token-default.md`, at: ## Root Cause:*

```
# Postmortem: kluster.ai DeepSeek Output-Token Default

**Date:** 2025-03-18
**Status:** Open (action items not yet resolved)

---

## What Happened

curator estimates output tokens before a request completes, using `max_output_tokens // 4` as a proxy for rate-limit headroom. The assumption baked into that heuristic is that the provider's max output token ceiling is consistent with what curator expects.

kluster.ai's DeepSeek endpoint silently applies a different default for max output tokens than other providers. The pre-request estimate diverged significantly from actual usage. The run completed, cost figures were logged, and nothing indicated anything was wrong.

## Impact

- Cost estimates for kluster.ai DeepSeek runs were materially inaccurate. I don't have the exact magnitude to hand, need to pull the actual vs. estimated figures from whoever owns the cost log dashboard.
- Throughput headroom was also miscalculated for those runs, meaning the rate limiter was not working as intended.
- No user-visible error. No alert fired. The mismatch was completely invisible at the surface.

Duration of exposure is unclear. We caught it on a specific run but we don't know how many previous
```

#### `g10.r2.l9` — exclusions_or_crossover

**emil**, 2025-04-21, thread:<178770212973.2301745.4705747507669611471@world.local>

> also WS-054: lost an afternoon to drift between what we hold and what comes back — reported usage on responses we discard isn't a sound basis for the release.

*What a reader should take from it:* the team agrees usage reported on discarded responses is not a sound basis for the release

*Step it builds toward:* `g10.r2.s3` — The amount given back after a failure is the reservation that was taken, not whatever token usage the failed response reported.

*Drafted as:* lost an afternoon to a drift between what we held and what came back, and it traces to trusting usage numbers off responses we discarded.

*Why there:* Emil's own Apr 21 weekly update already carries WS-054 (cost accounting) as "in progress, not blocked" and is the one place he narrates what he actually spent time on. A finding that held-vs-returned token capacity drifts because we trust usage reported on responses we throw away complicates exactly that workstream, and it lands as a settled judgement without saying what number replaces the reported usage or what happens to the slot — that's left for someone else. It's his mail, his voice, his week.

*Still leaves open:* the number that should be used in place of the reported usage, and what happens to the request slot

*Goes as a reply into the real thread "Weekly update: week of Apr 14":*

```
Hey all,

Quick rundown on where things stand heading into this week.

WS-050 (batch-mode bug sweep): working through the main failure cases, got the Gemini job-state check addressed in PR 646. A few more edge cases still to close out, but we're past the worst of it.

WS-054 (cost accounting): in progress, not blocked. The response object work in PR 643 is part of this — should have something reviewable this week.

PR situation: I have PR 468 (n samples), PR 643 (response object), and PR 646 (Gemini job state) all sitting in review. They need a rebase before they can move, which I'll sort out today. PR 632 (Gideon's CLI batch update frequency fix) looks contained and ready to land — needs eyes. PR 650 (DeepSeek json_schema) just came in and is coming to me.

If anyone can spare time for reviews this week, 632 is the quickest one to get through.

Emil
```

### g10.r2.s4 — The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.

*Nobody says:* A counter that only moves when arithmetic happens is a counter of arithmetic, not of the calls you were trying to watch.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g10.r2.l11` — observability

**gideon**, 2025-03-19, #code-review

> honestly though, one release counter for both kinds means i can't see the retry churn at all in the dashbaord, a run thrashing on retries looks identical to a quiet hour.

*What a reader should take from it:* the team agrees one shared counter hides failure releases

*Step it builds toward:* `g10.r2.s4` — The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.

*Drafted as:* One release counter for both kinds means I can't see retry churn at all in the dashboard. Looks identical to a quiet hour.

*Why there:* The remark is about the token capacity budget's release accounting — success releases and retry/failure releases sharing a single counter, and the resulting blind spot in the dashboard. None of the candidates is on that thread: 2025-03-18 is the kluster cost-estimation blindspot and the undefined batch processor interface, 2025-04-24 is a bare `except: pass` swallowing cache writes, and the rest (04-04, 04-10, 04-14, 04-29, 05-05) are PR-triage and reviewer-chasing days where a metrics-shape observation arrives from nowhere and draws no reply. #code-review also expects a PR number and subsystem, which this remark has none of. #pipeline is the room defined for rate limits, token accounting and retries, and Gideon is already its observability-gap voice; a thread there about the limiter's release path after a retry-heavy overnight run is where a colleague could then ask the separate question of what the counter should do when the release frees nothing.

*Still leaves open:* how the counting should behave when the release changes nothing

*A new conversation in #code-review on 2025-03-19:*

```
```

> **Problems:** longer than one remark

#### `g10.r2.l13` — observability

**nils**, 2025-03-20, #code-review

> ran the unlimited-token config overnight, both counts sat at zero even though every request went through the same release path — releases on an unlimited tracker simply go uncounted today.

*What a reader should take from it:* the team agrees releases on an unlimited tracker go uncounted today

*Step it builds toward:* `g10.r2.s4` — The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.

*Drafted as:* ran the unlimited-token config overnight and both counts sat at zero, even though every request went through the same release path.

*Why there:* Neither candidate is chewing on token capacity tracking. The 03-24 code-review day is review logistics (who picks up PR 583, when Emil gets to 584) and has no room for an overnight run result. The 03-17 pipeline day is the right channel but the wrong subject: it is entirely about whether the prompt_tokens/completion_tokens/total_tokens shape from Mistral batch responses is what cost accounting expects, closed out with a code snippet and a wiki-page complaint. This remark is about a capacity tracker configured with unlimited tokens whose release path never increments its counters — a different mechanism, different evidence, and nothing in that thread prompts it, so it would change the subject and draw no reply. It needs its own #pipeline thread: nils reporting the overnight run, Emil (who owns the surrounding code) pushing back, dario asking whether it blocks anything, which then opens what the counting should key on instead.

*Still leaves open:* what the counting should key on instead, and whether the two kinds stay separate

*A new conversation in #code-review on 2025-03-20:*

```
```

#### `g10.r2.l12` — observability

**nikolai**, 2025-04-03, page:engineering/token-capacity-budget-in-the-limiter.md

> i'd say keep the two tallies seperate, a settle moves its own counter and a give back moves its own, neither touches the other

*What a reader should take from it:* the team agrees each release kind gets its own counter and moves only that one

*Step it builds toward:* `g10.r2.s4` — The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.

*Drafted as:* keep the two tallies apart, a settle moves its own and a give-back moves its own, neither touches the other.

*Why there:* The remark settles an internal accounting rule for the capacity budget — that a settle and a give-back each move their own counter and never the other's. None of the listed places is chewing on that. The two weekly syncs (Jun 16, Jun 23) only note that issue 207 (has_capacity) and 233 are unowned and deferred; a counter-semantics ruling dropped into a "we're punting this" list would read as answering a question nobody asked there. WS-055 is CI/release engineering and cache layout, the image-pinning page is Docker tags, and the release notes pages are changelogs. The Mar 31 notes come closest ("issue 207: has_capacity on the batch path, still unresolved") but as a carried-over open item, not a design thread. This belongs in #pipeline, which is exactly the room for rate limits and token accounting, in a live back-and-forth about how the capacity budget reconciles a reserved estimate against what a request actually used — with the zero-delta case left hanging for someone else to answer.

*Still leaves open:* whether a release that changes no capacity still shows up in the tallies

*A new page — **Token capacity budget in the limiter** in `engineering`, 2025-04-03:*

> **why this page**

> issue 207 came out of the week of Mar 31 notes and it is still open on the batch path
> 
> Dario has been sketching what the limiter should do at the moment a request finishes and the reserved output estimate has to be reconciled against what the provider actually billed
> 
> rather than have that live in three heads i am writing down the shape we already agreed on for the online path so the batch work has something to point at
> 
> nothing here is new behaviour it is just the part that was never written down

> **what the budget actually tracks**

> two numbers per window not one
> 
> - **reserved** what we have promised out to in flight requests
>   input tokens are known at submit time
>   output tokens are an estimate since nobody knows the length until the response lands
> - **used** what has actually been billed back to us by finished requests
> 
> the reason for two is the estimate
> 
> if we only kept one tally we would have to correct it in place every time a response came back shorter or longer than we guessed and correcting in place is where the drift comes from
> 
> i'd say the estimate is solid enough for typical generation params but it is wrong on both sides often enough that we should not build on it being close

> **settle and give back**

> when a request finishes two things happen and they are seperate operations
> 
> - the **settle** adds the real billed usage from the provider response onto the used tally
> - the **give back** removes the original reservation from the reserved tally
> 
> keep the two tallies apart
> 
> a settle moves its own and a give back moves its own
> neither touches the other
> 
> so we never compute a delta between estimate and actual and never apply that delta anywhere
> the reservation comes off at the same size it went on regardless of what the response turned out to be
> the used tally only ever sees numbers that came from the provider
> 
> `has_capacity` reads both tallies and writes neither
> it

> **failure and cancellation**

> a request that errors out still holds a reservation
> 
> same two operations apply
> 
> - give back runs always
> - settle runs only if we got usage back from the provider
> 
> for a hard transport failure there is no usage so there is nothing to settle and the used tally stays where it is
> for a request that returned an error body with usage attached we do settle it because we were billed for it
> 
> cancelled requests are the same as a hard failure from the budget point of view

> **batch path still open**

> this is the part 207 has not answered
> 
> on batch we submit thousands of requests and the responses come back hours later in one file
> the reservation would be held for the whole window which is not a useful thing to be holding
> 
> open questions i do not have answers to yet
> 
> - do we reserve at submit time at all or only count batch usage after the fact
> - if we do not reserve then batch traffic is invisible to `has_capacity` and an online run alongside a batch run will overcommit
> - partial results in a batch file mean partial settles against a reservation that was made in bulk
> 
> that last one is the one that worries me
> gotta think through that one before anybody writes code 

> **if you touch this**

> worth checking
> 
> - reserved never goes negative
>   if it does somebody gave back twice or gave back a reservation that was never made
> - used and reserved are never added together and then corrected
> - a give back uses the reservation amount recorded at submit not a recomputed one
>   recomputing from current params is how you get a mismatch when the params changed mid run
> - the window rollover clears used and carries reserved
>   in flight requests do not stop being in flight because a minute boundary passed

#### `g10.r2.l14` — observability

**dario**, 2025-04-15, thread:new|g10.r2.l14

> honestly we're counting that the call happened, not that a number changed — so it ticks even when there was nothing on that axis to move.

*What a reader should take from it:* the team agrees the counters move on every call regardless of whether capacity changed

*Step it builds toward:* `g10.r2.s4` — The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.

*Drafted as:* we are counting that the operation ran, not that a number changed, so it ticks even when there was nothing on the axis to move.

*Why there:* All eight candidates are status mail: three weekly recaps, a release announcement, a maintenance-mode recap, and Emil's design note on batch job status persistence across restarts. None of them is chewing on instrumentation semantics — what a counter increments on and whether it moves when nothing changed. The nearest, Emil's persistence note, is about CURATOR_CACHE_DIR and when the responses file gets appended, not about capacity accounting; dropping a line about counters ticking on every call there would change the subject and get no reply. This remark answers a specific "why did this number climb when nothing was in flight" question, which is exactly what #pipeline exists for — token and cost accounting, rate limits, the online request layer. It needs a room where someone has just pasted a counter that went up for no visible reason, and no such conversation is on offer here.

*Still leaves open:* that there are two of these counters and that neither one moves for the other kind

*A new thread — **capacity budget counters climbing on a run that was doing nothing**, 2025-04-15:*

```
From: emil  To: dario, nikolai, gideon
morning — i left the online run going overnight against the small pool and came back to something i cant quite account for. from roughly 02:10 onward the run is flat: queue drained, nothing in flight, no new requests going out, and it stayed that way until i killed it at 07:20. but the capacity budget lines in the log keep climbing the whole time, steadily, right through the dead stretch.

my first read was that something takes a reservation and never gives it back and the run was slowly walking

From: nikolai  To: emil, dario, gideon
not a leak i'd say

i chased the same shape a few months back when the limiter was printing something similar and it turned out to be the accounting not the pool

dario wrote most of that layer he'll know which number is which

From: dario  To: emil, nikolai, gideon
mhm, nikolai has it, its not the leak you are picturing. the figure on that line is not a level, its a running total — it only ever goes up, and it goes up whenever the budget layer is asked to do its pass, so a run that is completely idle will still print a larger number every interval for as long as the loop is alive.

the part that i think trips everyone up, and it certainly tripped me up when i came back to it, is that we are counting that the operation ran, not that a number changed, so it 

From: gideon  To: dario, emil, nikolai
oh that explains the thing i saw last week on my own run, i was staring at it for like an hour convinced i had broken something. so basically the line going up is just the loop breathing. honestly though the naming does not help anyone here, tbh they read like the same number with a different label.

```

### Herrings — believed at the time, overturned later

#### `g10.r2.h1` — herring

**dario**, 2025-01-21, #engineering

> ok, got through the PR 387 diff - the except branch calls _free_capacity with the used_tokens it alredy builds, same as the success path, so both hand the request slot back.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled in review: the except branch calls _free_capacity with the used_tokens it already builds, same as the success path, and both give the request slot back.

*Why there:* The only listed thread where this belongs is #code-review 2025-01-23, PR 387's max_tokens capacity blocking — but that day ends with dario admitting at 18:25 he hasn't gotten past the description and promising the diff "first thing tomorrow," so a "settled in review" verdict there contradicts what he just said. #pipeline 2025-02-27 touches blocked_capacity but is arguing about estimation parity between batch and online, not about the failure path releasing capacity, and nobody there is reviewing a diff. The remark is the payoff of the promise dario made: the next-morning #code-review thread where he reports what the PR 387 diff actually does, with nikolai (who left the PR open overnight) and emil (who wanted PR 378 folded in) waiting on it.

*A new conversation in #engineering on 2025-01-21:*

```
```

#### `g10.r2.h2` — herring

**gideon**, 2025-01-23, #engineering

> so basically one release helper, one shape: _free_capacity(tracker, used, blocked) on every terminal path, and the slot comes back whether the attempt suceeded or blew up

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* One release helper, one shape: _free_capacity(tracker, used, blocked) on every terminal path, and the slot comes back whether the attempt succeeded or blew up.

*Why there:* Every listed room is chewing on something else. The two #pipeline days are about schema 400s / error summarization (Feb 7) and Mistral per-line usage fields (Mar 10); Feb 19 is the closest neighbour in that it touches the concurrent request and retry path in online-request-processing, but the whole thread is about PR 518's logger — whether retries route through it, whether errors buffer — not about who hands the request slot back. #incidents Mar 1 is revert scope for v0.1.20, both #code-review days are queue triage (batch tracker counting, PR 581 env-var), and #engineering Jan 30 is WS-028 coverage floor plus a CLI cost-display bug. A settled decision about a symmetric capacity-release helper would arrive from nowhere in all of them and draw no reply. It needs its own #pipeline thread: rate limits and the request layer are exactly that room's remit, and the conversation it belongs to is the one where someone notices concurrency bleeding down over a long run because slots aren't returned on the error path.

*A new conversation in #engineering on 2025-01-23:*

```
```

#### `g10.r2.rev1` — rule, exclusions_or_crossover

**dario**, 2025-03-17, #engineering

> dropped the except branch feeding _free_capacity its used_tokens — a model failing every call drained the bucket dry. failures call refund_capacity(blocked) now, full blocked estimate back, request slot up 1.0

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* we dropped the except branch handing _free_capacity the used_tokens it builds — pointed at a model that failed every call and the bucket drained faster than it refilled. failures now call refund_capacity(blocked): whole blocked estimate back, request slot up exactly 1.0.

*Why there:* All four #pipeline days are the right room but the wrong subject: 04-17 is structured-output response mapping into cost/progress fields, 04-23 is the cache fingerprint and job record missing the model, 04-07 is the resume-path 10x cost bug and gemini batch scope, 04-29 is stdout scope and the PR 640 override. None of them is anywhere near the rate limiter's token/request bucket, so a line about the failure path double-charging capacity would change the subject and draw no reply — the 04-07 thread mentions "cost accounting" and "retry logic" but that's vocabulary overlap, not the same problem. #engineering, #code-review and #releases are further off. What's missing is the #pipeline thread where the bucket-drain symptom actually gets reported and the refund rule settled: a run pointed at a provider erroring on every call collapses to near-zero throughput overnight, gideon or emil asks why concurrency never recovers, dario has been in the limiter and reports the except branch was returning reported usage instead of the blocked estimate. That day would also cover whether partial usage on a failed call is ever worth crediting and what happens to in-flight requests when a run is cancelled.

*Must appear literally:* `_free_capacity`, `refund_capacity`, `blocked`, `1.0`

*A new conversation in #engineering on 2025-03-17:*

```
```

#### `g10.r2.rev2` — rule, scope, observability

**gideon**, 2025-03-19, #engineering

> so basically one-helper-one-shape is gone — free_capacity(used, blocked) settles tokens only and leaves available_request_capacity where consume_capacity spent it. both except exits call _refund_capacity, which moves num_capacity_refunds, not num_capacity_settlements.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* One-helper-one-shape is gone. free_capacity(used, blocked) settles tokens only and leaves available_request_capacity exactly where consume_capacity left it, so a success keeps its slot spent. Both except exits call _refund_capacity instead, and it moves num_capacity_refunds, not num_capacity_settlements.

*Why there:* None of the listed rooms is chewing on capacity accounting at all. The #pipeline day that exists (2025-04-21) is about batch job reuse and key-mismatch resubmission — a different subsystem and a decision Dermot/Emil/Dario are driving; a sudden report on free_capacity/refund counters there changes the subject and gets no reaction. The three #code-review days are pure status-and-reviewer chasing (PR 619's merge state, PR 632/651/653 needing eyes) with no substantive discussion of any diff, so a semantics-of-the-refactor line would be the only technical content in the room. #help/2025-03-26 is the capability check, #engineering/2025-04-10 is PR triage, #random is the mkdir -p billing story. The remark reports a settled behavioural split in the request-layer capacity budget — that is exactly #pipeline's remit (rate limits, token accounting), but it needs its own day, prompted by someone noticing successful requests handing their slot back.

*Must appear literally:* `free_capacity`, `available_request_capacity`, `_refund_capacity`, `num_capacity_refunds`, `num_capacity_settlements`

*A new conversation in #engineering on 2025-03-19:*

```
```

