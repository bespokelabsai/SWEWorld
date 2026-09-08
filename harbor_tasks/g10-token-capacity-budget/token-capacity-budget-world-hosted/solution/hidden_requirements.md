# g10 — Online token-capacity budget: reservation, refund and reported limits

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries.

| arm | what it is handed |
|---|---|
| `blind` | the ticket |
| `spec` | the ticket + both hidden requirements |
| `clues` | the ticket + all 46 remarks, quoted |
| `world` | the ticket, against `sweworld:0.4.4` where the 46 remarks live in chat, the wiki and mail |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Each is graded as five independent facts, 0.1 each. `open_feature` carries weight 0.0: building the feature scores nothing, only recovering what nobody wrote down does.

### `g10.r1`

- **`rule`** — Token capacity may go negative, but each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` with `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25` exported from the capacity-budget module. The floor is `-limit * 0.25` as a `float` for the `combined` axis. Worked case: a tracker with `max_tokens_per_minute=1_000`, after `consume_capacity(_TokenUsage(input=700, output=100))` and then settling `used=_TokenUsage(input=1000, output=500)` against `blocked=_TokenUsage(input=700, output=100)`, ends at `available_token_capacity == -250.0`.

- **`scope`** — A tracker constructed with `max_tokens_per_minute=0` (defaulted to 100_000) floors at `-25000.0`, and under `seperate` each axis floors against its own limit: with `_TokenUsage(input=1_000, output=500)` an over-settled tracker lands on `_TokenUsage(input=-250, output=-125, total=-375)`. An axis whose limit and capacity are `None` has no floor and stays `None`. `available_request_capacity` is never floored.

- **`exclusions_or_crossover`** — Capping an axis at its UPPER bound is not a clamp and never touches the counter: neither the refill in `update_capacity` raising an axis back up to `max_tokens_per_minute`, nor a release raising it to that same ceiling, increments `num_capacity_debt_clamps`. The counter increments ONLY when the lower debt floor `-CAPACITY_DEBT_FLOOR_FRACTION * limit` is applied. So a settlement whose result stays above that floor (e.g. `available_token_capacity == 100.0` on a 1_000-token tracker) leaves the counter at `0`, and so does a refill that lands exactly on `1000.0` rather than the `1200.0` it would otherwise reach.

- **`observability`** — A tracker field `num_capacity_debt_clamps: int = 0` increments by exactly one per call that clamped at least one axis.

> *The decision the team made first and later reversed:* The team first clamped debt at 0.0 (capacity is never negative, an under-estimate is forgotten), then reversed it because forgiving the overshoot let a systematically under-estimating model exceed the provider's per-minute budget every window; they settled on a bounded -25% carry-over instead.

### `g10.r2`

- **`rule`** — `free_capacity(used, blocked)`: the token axes gain `blocked - used` and `available_request_capacity` is left exactly as `consume_capacity` left it. `refund_capacity(blocked: _TokenUsage) -> None`: the token axes gain the whole `blocked` estimate back (capped above at the limit) and `available_request_capacity` gains exactly `1.0`, capped above at `max_requests_per_minute`. The processor's `_refund_capacity(self, status_tracker, blocked_capacity)` delegates to `status_tracker.refund_capacity(blocked_capacity)`.

- **`scope`** — Every terminal path through the `except Exception` branch of `handle_single_request_with_retries` calls the refund — both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`). On a tracker with `max_requests_per_minute=60`, `max_tokens_per_minute=10_000` and a reservation of `_TokenUsage(input=700, output=300)`, either failure path ends at `available_request_capacity == 60.0` and `available_token_capacity == 10000.0`, while the success path with reported usage `_TokenUsage(input=700, output=100)` ends at `59.0` / `9200.0`.

- **`exclusions_or_crossover`** — The failure refund uses the full blocked estimate and ignores `generic_response.token_usage` — e.g. a response with `finish_reason="length"` (in `config.invalid_finish_reasons`) reporting `_TokenUsage(input=900, output=800)` against a blocked estimate of `_TokenUsage(input=900, output=100)` returns the estimate.

- **`observability`** — Two tracker counters, `num_capacity_settlements: int = 0` and `num_capacity_refunds: int = 0`, each incremented by exactly one by its own operation and by neither the other's. Both counters still increment when the affected capacity is `None` and the operation is a no-op on every axis.

> *The decision the team made first and later reversed:* An earlier revision charged the failure path symmetrically with the success path — `_free_capacity(status_tracker, used_tokens, blocked_capacity)` using the usage the `except` block already builds — and returned the request slot on both kinds of release; it was reversed because a retry storm against a systematically failing model drained the bucket faster than the refill could recover it.

---

## Where the remarks are spread

46 remarks in total — 38 clues, 4 herrings and 4 reversals — across 1 surfaces and 9 chat channels. `clues.spread()` reports on this — at least 2 sources, 3 weeks and 2 rooms per requirement, so no single sitting recovers one. It is advisory, not enforced: read the numbers rather than trusting that something refused a plant without them.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **46** | `#pipeline` 12, `#engineering` 8, `#code-review` 6, `#releases` 5, `#cookbooks` 5, `#viewer` 3, `#general` 3, `#incidents` 3, `#help` 1 |

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

## g10.r1

### g10.r1.g10.r1.s1 — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*The leap nobody states:* If the overshoot has to be carried but must not be carried forever, the only way to express 'how far it may run' is as a fraction of the same per-minute number the bucket was seeded from, and that fraction needs a home.

- **dario** (2025-04-08, #engineering): estimator came in light again, third window in a row we went past the provider ceiling - and the ledger resets to zero each minute so that overshoot is gone
- **emil** (2025-05-13, #pipeline): honestly if we burned more than we reserved, minute two should open owing that much. right now it opens fresh every time and I don't love it.
- **nikolai** (2025-03-17, #pipeline): not bottomless though  one bad settle and the run spends the rest of the night paying it back  i'd say we cap the hole at a quarter of the minute's alowance
- **konrad** (2025-03-19, #pipeline): anyway, I pulled the 0.25 out of the settle path into CAPACITY_DEBT_FLOOR_FRACTION in capacity_budget.py, it was sitting inline there and again in a test.

### g10.r1.g10.r1.s2 — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*The leap nobody states:* 'Effective limit' is whatever the bucket was seeded with, so a defaulted axis is bounded like any other, and where there is no limit there is nothing to take a fraction of.

- **gideon** (2025-03-19, #engineering): so basically I ran a split-limit config and both halves got held against the input number, so output ended up way deeper in the hole than its own 500 a minute ever justfied
- **nils** (2025-03-21, #pipeline): let me think - in my grid the row where the caller passed 0 is A, and A still has the 100k default standing behind it, so it isn't a special case.
- **dermot** (2025-03-24, #pipeline): from the late night run - settle threw doing arithmetic on a None, that model has no token ceiling at all. no ceiling, nothing to take a share of, leave it be.
- **emil** (2025-03-14, #code-review): why is available_request_capacity sitting at -50 though? we reserve exactly one slot per request, it can't overspend, so that one should never be under zero at all.
- **dermot** (2025-04-18, #incidents): same shape on the request side - with no max_requests_per_minute set, available_request_capacity just reads back None, so there's nothing there to floor either

### g10.r1.g10.r1.s3 — The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.

*The leap nobody states:* A per-call counter is the only reading that matches how people talk about 'how often did we bottom out', so two axes bottoming out inside one settle is still one event.

- **gideon** (2025-04-09, #pipeline): honestly though, to see how often we bottom out I've been diffing ledgers between runs, which is stupid - the tracker should just carry a plain counter starting at 0 and tell me.
- **dermot** (2025-03-14, #engineering): yeah - on last night's run num_capacity_debt_clamps went up by two on a single settle where both halves bottomed out, so my per-run figure is double what actually happened
- **dario** (2025-03-17, #code-review): mhm, one call one tick — whether it was a single axis sitting at the bottom or both of them clamped in the same settle, it still only counts once

### g10.r1.g10.r1.s4 — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*The leap nobody states:* The counter is meant to answer 'how often did we go too deep', so anything that happens at the full end of the bucket, and anything that never reached the bottom, is outside what it measures.

- **nils** (2025-03-19, #pipeline): let me think - on a smoke run that never once went under, the count came back 47. every refill that tops out at the limit is ticking it, and it shouldn't be
- **emil** (2025-03-18, #code-review): honestly a refill capped back at the limit is only a full bucket - token side tops out at max_tokens_per_minute, request side at max_requests_per_minute, nothing worth recording either way.
- **nikolai** (2025-03-19, #code-review): same goes for a relase handing back a big over-reservation - it clamps at max_tokens_per_minute rather than adding through past it, and that ceiling isnt the event were watching for.
- **konrad** (2025-03-20, #code-review): Look, a settle that leaves us at +100 on a 1000 tracker is not it either. It should only tick when we actaully stopped the fall.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled this in review: free_capacity clamps every axis at 0.0, so available capacity never drops below zero and an under-estimate is just forgotten at settlement.
- **emil** (2025-01-21): one thing off Dario's pass on 387: zero is the floor, a bucket sitting at 0.0 is empty and that's the whole story. no accounting for overshoot, next refill starts clean.

## g10.r2

### g10.r2.s1 — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*The leap nobody states:* If the estimate over-books tokens and the call succeeded, the difference is dead weight worth reclaiming, but the call itself really did happen and cannot be un-counted.

- **gideon** (2025-04-21, #help): Also from the same profile - estimator books 1k output tokens on every haiku call, actual comes back under 150, and then we crawl for the rest of the minute.
- **dario** (2025-04-16, #engineering): per-request i think - on a clean response the only thing we put back into the budget is the gap between what we booked and what it actually spent
- **konrad** (2025-03-17, #engineering): Look, we handed the slot straight back the moment the response landed, and that pushed 240 calls into a 200 minute. Provider noticed.
- **nils** (2025-03-19, #engineering): let me think through that - a request that actually reached the provider is spent for that minute whatever came back, it does not un-happen.

### g10.r2.s2 — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*The leap nobody states:* Work that produced nothing should leave no charge behind, so the release for failures is a different shape from the one that settles a success.

- **emil** (2025-04-10, #pipeline): different shape but same area - gemini 503'd on everything last night, and by minute two we were down to one request every few seconds with zero successes.
- **dermot** (2025-03-20, #engineering): yeah, an attempt that errored bought us nothing, so refund_capacity returns the entire token reservation rather than whatever was left unspent.
- **nikolai** (2025-03-20, #cookbooks): counted it this morning we are doing thirty real requests a minute agaisnt a sixty ceiling because the attempts that came back 503 are still sitting on their slots
- **konrad** (2025-03-21, #cookbooks): Look, if the call errored we hand its slot back, one per attemtp, and never above what the minute started with.
- **dario** (2025-04-11, #incidents): on the refund path the processor side stays thin — `_refund_capacity(self, status_tracker, blocked_capacity)` just calls `status_tracker.refund_capacity(blocked_capacity)` and honestly that's the whole body

### g10.r2.s3 — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*The leap nobody states:* A release that only happens on one way out of the error handler leaks capacity on the other, and both are terminal for that attempt.

- **gideon** (2025-03-27, #viewer): so basically every retry cycle on that flaky endpoint eats anohter reservation, capacity just walks down all afternoon and never comes back until we restart
- **dario** (2025-04-07, #pipeline): in the retry path, the branch where attempts_left is zero appends the failure and returns, thats the whole of it. our capacity charts never recover after a bad model
- **nils** (2025-04-07, #general): let me think - _refund_capacity should be firing at the point we give up on a request entirely, and right now nothing calls it there
- **emil** (2025-03-19, #releases): let me think through that - on a requeue the request goes back on the queue and gets estimated again, so holding the old booking against it is charging the budget twice.

### g10.r2.s4 — The failure release is sized from the reservation that was made, not from any usage the discarded response reported.

*The leap nobody states:* Numbers attached to a response nobody is keeping are not what was taken out of the bucket, and trusting them can hand back more than was ever booked.

- **nikolai** (2025-03-24, #cookbooks): on the failure path we hand back the token counts the failed response itself reported so the bucket finishes the minute holding more capacity than the limit allows took me a whlie to spot that
- **konrad** (2025-04-03, #cookbooks): Look, the length ones are worst - finish_reason length, and the reponse reports 800 output against the 100 output we actually booked for it.
- **nils** (2025-04-21, #general): let me think — on the throw-away path the booking is the only number we own, and refund_capacity hands it back clamped so available_token_capacity never ends above the limit.

### g10.r2.s5 — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*The leap nobody states:* A count is only useful for telling the two kinds of release apart if each is attributed to exactly one of them and neither goes silent.

- **emil** (2025-04-17, #pipeline): honestly, the last progress counter we ticked from both paths never matched the request count. these two only move on release — an acquire bumps neither num_capacity_settlements nor num_capacity_refunds.
- **konrad** (2025-04-11, #cookbooks): Look, the tracker dump needs num_capacity_settlements and num_capacity_refunds as separate counters, otherwise I cannot tell the two kinds of release apart in a run.
- **nikolai** (2025-04-24, #releases): ran anthropic overnight with no token ceiling set and the counts never moved off `num_capacity_settlements: int = 0` / `num_capacity_refunds: int = 0` so i spent the morning hunting a bug that wasnt ther
- **dermot** (2025-05-02, #releases): we're counting the call, not whether it moved a number. a release against an unlimited axis went through the same code path, so it still increments.
- **nils** (2025-04-29, #general): let me think — if nobody configures a token limit, available_token_capacity is None for the whole life of that tracker, it never becomes a number.
- **gideon** (2025-04-14, #viewer): so basically i dumped the trakcer on one of those unlimited runs and available_request_capacity comes back as None, so there is no number to watch there, only the counters.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): ok, settled: one release call for both outcomes — _free_capacity(status_tracker, used_tokens, blocked_capacity) — and the request slot goes back on failure exactly like it does on success.
- **emil** (2025-01-28): except branch already has used_tokens built, so failure settles through the same _free_capacity(used, blocked) call as success. slot goes back on every terminal path.


---

## The ticket — stated openly

**Online token-capacity budget: reservation, refund and reported limits**

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


---

## Where every remark is

46 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-21 | chat | #engineering | konrad | [`g10.r1.clamp-at-zero-decision`](#g10r1clamp-at-zero-decision) | 8 | **herring** | — |
| 2025-01-21 | chat | #releases | konrad | [`g10.r2.h1`](#g10r2h1) | 7 | **herring** | — |
| 2025-01-21 | chat | #code-review | konrad | [`g10.r1.clamp-at-zero-rationale`](#g10r1clamp-at-zero-rationale) | 10 | **herring** | — |
| 2025-01-28 | chat | #releases | nikolai | [`g10.r2.h2`](#g10r2h2) | 8 | **herring** | — |
| 2025-03-14 | chat | #engineering | dermot | [`g10.r1.g10.r1.s3.l2`](#g10r1g10r1s3l2) | 9 | clue | `observability` |
| 2025-03-14 | chat | #code-review | gideon | [`g10.r1.g10.r1.s2.l4`](#g10r1g10r1s2l4) | 7 | clue | `scope` |
| 2025-03-17 | chat | #pipeline | dario | [`g10.r1.g10.r1.s1.l3`](#g10r1g10r1s1l3) | 7 | clue | `rule` |
| 2025-03-17 | chat | #code-review | nikolai | [`g10.r1.g10.r1.s3.l3`](#g10r1g10r1s3l3) | 7 | clue | `observability` |
| 2025-03-17 | chat | #engineering | dario | [`g10.r2.s1_l3`](#g10r2s1_l3) | 8 | clue | `rule` |
| 2025-03-18 | chat | #code-review | dario | [`g10.r1.g10.r1.s4.l2`](#g10r1g10r1s4l2) | 6 | clue | `exclusions_or_crossover` |
| 2025-03-19 | chat | #engineering | konrad | [`g10.r1.g10.r1.s2.l1`](#g10r1g10r1s2l1) | 8 | clue | `scope` |
| 2025-03-19 | chat | #pipeline | gideon | [`g10.r1.g10.r1.s4.l1`](#g10r1g10r1s4l1) | 7 | clue | `exclusions_or_crossover`, `observability` |
| 2025-03-19 | chat | #engineering | konrad | [`g10.r2.s1_l4`](#g10r2s1_l4) | 8 | clue | `rule` |
| 2025-03-19 | chat | #releases | konrad | [`g10.r2.s3_l4`](#g10r2s3_l4) | 7 | clue | `scope` |
| 2025-03-19 | chat | #pipeline | dermot | [`g10.r1.g10.r1.s1.l4`](#g10r1g10r1s1l4) | 8 | clue | `rule` |
| 2025-03-19 | chat | #code-review | konrad | [`g10.r1.g10.r1.s4.l3`](#g10r1g10r1s4l3) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-20 | chat | #cookbooks | konrad | [`g10.r2.s2_l3`](#g10r2s2_l3) | 8 | clue | `rule` |
| 2025-03-20 | chat | #engineering | konrad | [`g10.r2.s2_l2`](#g10r2s2_l2) | 7 | clue | `rule` |
| 2025-03-20 | chat | #code-review | dario | [`g10.r1.g10.r1.s4.l4`](#g10r1g10r1s4l4) | 7 | clue | `exclusions_or_crossover` |
| 2025-03-21 | chat | #cookbooks | nikolai | [`g10.r2.s2_l4`](#g10r2s2_l4) | 8 | clue | `rule` |
| 2025-03-21 | chat | #pipeline | gideon | [`g10.r1.g10.r1.s2.l2`](#g10r1g10r1s2l2) | 8 | clue | `scope` |
| 2025-03-24 | chat | #cookbooks | konrad | [`g10.r2.s4_l1`](#g10r2s4_l1) | 8 | clue | `exclusions_or_crossover`, `rule` |
| 2025-03-24 | chat | #pipeline | gideon | [`g10.r1.g10.r1.s2.l3`](#g10r1g10r1s2l3) | 8 | clue | `scope` |
| 2025-03-27 | chat | #viewer | konrad | [`g10.r2.s3_l1`](#g10r2s3_l1) | 7 | clue | `scope` |
| 2025-04-03 | chat | #viewer | dario | [`g10.r2.rev2`](#g10r2rev2) | 9 | **reversal** of `g10.r2.h2` | `rule`, `exclusions_or_crossover` |
| 2025-04-03 | chat | #cookbooks | nikolai | [`g10.r2.s4_l2`](#g10r2s4_l2) | 9 | clue | `exclusions_or_crossover` |
| 2025-04-07 | chat | #general | konrad | [`g10.r2.s3_l3`](#g10r2s3_l3) | 8 | clue | `scope`, `rule` |
| 2025-04-07 | chat | #pipeline | emil | [`g10.r2.s3_l2`](#g10r2s3_l2) | 7 | clue | `scope` |
| 2025-04-08 | chat | #engineering | konrad | [`g10.r1.g10.r1.s1.l1`](#g10r1g10r1s1l1) | 8 | clue | `rule` |
| 2025-04-08 | chat | #pipeline | dermot | [`g10.r1.rev1`](#g10r1rev1) | 10 | **reversal** of `g10.r1.clamp-at-zero-decision` | `rule` |
| 2025-04-09 | chat | #pipeline | dario | [`g10.r1.g10.r1.s3.l1`](#g10r1g10r1s3l1) | 8 | clue | `observability` |
| 2025-04-09 | chat | #incidents | dermot | [`g10.r2.rev1`](#g10r2rev1) | 8 | **reversal** of `g10.r2.h1` | `rule`, `scope` |
| 2025-04-10 | chat | #pipeline | gideon | [`g10.r2.s2_l1`](#g10r2s2_l1) | 7 | clue | `rule` |
| 2025-04-11 | chat | #cookbooks | dario | [`g10.r2.s5_l2`](#g10r2s5_l2) | 8 | clue | `observability` |
| 2025-04-11 | chat | #incidents | gideon | [`g10.r2.say23`](#g10r2say23) | 8 | clue | `rule` |
| 2025-04-14 | chat | #viewer | dermot | [`g10.r2.say25`](#g10r2say25) | 7 | clue | `observability` |
| 2025-04-16 | chat | #engineering | dermot | [`g10.r2.s1_l2`](#g10r2s1_l2) | 8 | clue | `rule` |
| 2025-04-16 | chat | #pipeline | emil | [`g10.r1.rev2`](#g10r1rev2) | 8 | **reversal** of `g10.r1.clamp-at-zero-rationale` | `rule`, `observability` |
| 2025-04-17 | chat | #pipeline | dario | [`g10.r2.s5_l1`](#g10r2s5_l1) | 7 | clue | `observability` |
| 2025-04-18 | chat | #incidents | nikolai | [`g10.r1.say19`](#g10r1say19) | 8 | clue | `scope` |
| 2025-04-21 | chat | #help | gideon | [`g10.r2.s1_l1`](#g10r2s1_l1) | 8 | clue | `rule` |
| 2025-04-21 | chat | #general | dermot | [`g10.r2.s4_l3`](#g10r2s4_l3) | 7 | clue | `exclusions_or_crossover` |
| 2025-04-24 | chat | #releases | dermot | [`g10.r2.s5_l3`](#g10r2s5_l3) | 7 | clue | `observability` |
| 2025-04-29 | chat | #general | dermot | [`g10.r2.say24`](#g10r2say24) | 7 | clue | `observability` |
| 2025-05-02 | chat | #releases | dario | [`g10.r2.s5_l4`](#g10r2s5_l4) | 7 | clue | `observability` |
| 2025-05-13 | chat | #pipeline | gideon | [`g10.r1.g10.r1.s1.l2`](#g10r1g10r1s1l2) | 7 | clue | `rule` |

#### `g10.r1.clamp-at-zero-decision` · **herring**

- **chat** · #engineering · **konrad** · 2025-01-21 14:02
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> settled this in review: free_capacity clamps every axis at 0.0, so available capacity never drops below zero and an under-estimate is just forgotten at settlement.

As it appears, spread across the exchange:

```
14:02  konrad    quick one on free_capacity — if we underestimate a request and it comes back bigger than we reserved, what does the available number do
14:04  nikolai   dips under i'd assume
14:07  dario     no, thats the thing we settled in review. every axis gets clamped at 0.0, so available bottoms out there and never goes under
14:07  konrad    ok but the difference doesnt just evaporate does it. something still owes it back
14:09  dario     honestly it does evaporate. we take the clamp and thats the end of it — at settlement the under-estimate isnt recorded anywhere, its just forgotten
14:10  konrad    huh ok. so an under-estimate is free once the request settles
14:11  nikolai   right and nothing downstream has to know about signed numbers
14:13  dario     mhm, thats about the size of it. best we can do without every reader of that struct handling a below-zero case
```

#### `g10.r2.h1` · **herring**

- **chat** · #releases · **konrad** · 2025-01-21 15:12
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ok, settled: one release call for both outcomes — _free_capacity(status_tracker, used_tokens, blocked_capacity) — and the request slot goes back on failure exactly like it does on success.

As it appears, spread across the exchange:

```
15:12  konrad    quick one - when a request fails out, who gives the tokens back? i see the success path doing it and nothing on the other side
15:14  dario     same call does both. one _free_capacity and both outcomes go through it, theres no second path
15:17  konrad    ok. what does it take? off the top of my head the failure side does not have the same things in scope
15:19  dario     _free_capacity(status_tracker, used_tokens, blocked_capacity). thats the whole signature, and the failure side actually has all three sitting right there already
15:22  dermot    and the request slot? restating my guess - that one only comes back when the call actually returned
15:24  dario     no, it goes back on failure too, exactly like it does on success. no difference there
15:26  konrad    mhm. i had two helpers half drawn in my diff, one of them can go
```

#### `g10.r1.clamp-at-zero-rationale` · **herring**

- **chat** · #code-review · **konrad** · 2025-01-21 15:49
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one thing off Dario's pass on 387: zero is the floor, a bucket sitting at 0.0 is empty and that's the whole story. no accounting for overshoot, next refill starts clean.

As it appears, spread across the exchange:

```
13:41  konrad    Going through Dario's pass on 387, one note there i want to be sure i read right
13:42  konrad    request asks for more capacity than is left in the bucket. where does the bucket land
13:45  emil      zero. thats the floor, it doesnt go past that
13:46  nikolai   and a bucket sitting at 0.0 means what exactly
13:48  emil      empty. thats the whole story, theres nothign else to read into it
13:49  nikolai   so nothing anywhere counts how far over the request went
13:51  emil      right, no accounting for the overshoot at all
13:52  konrad    then at the next refill it just... fills?
13:54  emil      starts clean, yup. nobody has put it in the path yet but thats what dario and i landed on
13:55  konrad    mhm. i had his note down as asking for more bookkeeping than that
```

#### `g10.r2.h2` · **herring**

- **chat** · #releases · **nikolai** · 2025-01-28 14:05
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> except branch already has used_tokens built, so failure settles through the same _free_capacity(used, blocked) call as success. slot goes back on every terminal path.

As it appears, spread across the exchange:

```
14:05  nikolai   quick one on the capacity accounting does the slot come back when the call raises or only on the happy path
14:07  dario     id assume it comes back but honestly i couldnt point at where
14:09  emil      it comes back. by the time we're in the except branch we already have used_tokens built, so theres nothing to go reconstruct there
14:11  nikolai   having it built isnt the same as handing it back tho. what does the handing back
14:13  emil      the same _free_capacity(used, blocked) call success goes through. failure settles through that one, not a second thing
14:15  dario     and the bails further up, the ones that never get to the request?
14:16  emil      slot goes back on those too, every terminal path out of that function
14:18  nikolai   right so no second set of bookkeping anywhere
```

#### `g10.r1.g10.r1.s3.l2`

- **chat** · #engineering · **dermot** · 2025-03-14 13:04
- carries `g10.r1.observability`
- must be typed literally: `num_capacity_debt_clamps`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah - on last night's run num_capacity_debt_clamps went up by two on a single settle where both halves bottomed out, so my per-run figure is double what actually happened

As it appears, spread across the exchange:

```
13:04  dermot    konrad, the clamp count in your capacity notes - mine comes out higher and i cant reconcile the two
13:06  konrad    what are you reading it off
13:07  dermot    num_capacity_debt_clamps, delta over last nights run
13:08  dermot    it moved by two there. i had that down as two separate clamped calls
13:09  dario     two seperate calls or one call that got counted twice? because those look identical from the delta
13:10  dermot    one. single settle, and both halves bottomed out on it
13:12  konrad    right, so the settle behaved, the counter didnt
13:13  dermot    mhm. one settle happened, so my per-run figure is double what actually happened - its the count thats wrong, not my arithmetic
13:14  dario     then the weekly numbers i pulled are off the same way, im not going to touch that column till its counting straight
```

#### `g10.r1.g10.r1.s2.l4`

- **chat** · #code-review · **gideon** · 2025-03-14 13:41
- carries `g10.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> why is available_request_capacity sitting at -50 though? we reserve exactly one slot per request, it can't overspend, so that one should never be under zero at all.

As it appears, spread across the exchange:

```
13:41  gideon    so basically the capacity dump off the run this morning has available_request_capacity at -50
13:42  gideon    why is it sitting at -50 though, thats the part i dont get
13:46  dario     we reserve exactly one slot per request, thats the whole of it on that path
13:47  gideon    ya so it cant overspend. then by that logic it shouldnt ever be under zero at all no?
13:51  emil      yup — one slot in, one slot back out, so nothing on the reserving path drives it under. which means the -50 got there some other way, and honestly thats the thing to go read
13:52  emil      not the reserve accounting anyway, i'd leave that bit alone
13:55  gideon    mm. i had it down as a rounding thing on the requst side and its clearly not that
```

#### `g10.r1.g10.r1.s1.l3`

- **chat** · #pipeline · **dario** · 2025-03-17 13:11
- carries `g10.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> not bottomless though  one bad settle and the run spends the rest of the night paying it back  i'd say we cap the hole at a quarter of the minute's alowance

As it appears, spread across the exchange:

```
13:11  dario     if a request lands bigger than whats left in the minute do we just let it borrow ahead or does it wait
13:14  nikolai   borrow  it goes negative and the following minutes make it up
13:15  dario     how far negative though. is there a floor on that or does it just keep digging
13:18  nikolai   not bottomless though  one bad settle and the run spends the rest of the night paying it back
13:20  emil      so youre saying we clamp the deficit at some point rather than let it ride
13:22  nikolai   right  i'd say we cap the hole at a quarter of the minute's alowance
13:24  emil      yup, id rather stall a minute than carry it all night
```

#### `g10.r1.g10.r1.s3.l3`

- **chat** · #code-review · **nikolai** · 2025-03-17 13:41
- carries `g10.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> mhm, one call one tick — whether it was a single axis sitting at the bottom or both of them clamped in the same settle, it still only counts once

As it appears, spread across the exchange:

```
13:41  nikolai   on the clamp counter - call gets squeezed on both axes in one shot, does that come out as two
13:42  dario     no. one call one tick
13:43  nikolai   and the boring case i mean single axis sitting at the bottom
13:44  dario     same, counts once. its the call we're counting, not which of them got pinned. nobody's written it yet but thats the shape
13:45  konrad    so both clamped in the same settle also lands as one, right
13:46  dario     mhm, still only counts once
13:47  nikolai   yep. i was reading it the other way and the totals werent adding up for me
```

#### `g10.r2.s1_l3`

- **chat** · #engineering · **dario** · 2025-03-17 14:03
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, we handed the slot straight back the moment the response landed, and that pushed 240 calls into a 200 minute. Provider noticed.

As it appears, spread across the exchange:

```
14:03  dario     konrad was the 429 wave last night their side, or something we did
14:05  konrad    ours. look, we handed the slot straight back the moment the response landed
14:06  dario     enough to push us over though? most of those calls are tiny
14:08  konrad    240 went into a 200 minute. the quick ones kept freeing room we hadnt earned yet
14:09  dermot    did that stay in our logs or did it get as far as the provider
14:10  konrad    no, provider noticed. thats what the mail this morning was about
14:12  dermot    mhm. so the give-back is hanging off the wrong thing
14:13  konrad    right. it comes back with the window, not with the reply
```

#### `g10.r1.g10.r1.s4.l2`

- **chat** · #code-review · **dario** · 2025-03-18 13:47
- carries `g10.r1.exclusions_or_crossover`
- must be typed literally: `max_requests_per_minute`, `max_tokens_per_minute`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly a refill capped back at the limit is only a full bucket - token side tops out at max_tokens_per_minute, request side at max_requests_per_minute, nothing worth recording either way.

As it appears, spread across the exchange:

```
13:47  dario     quick one on the refill path — when the top up overshoots and gets pinned back down to the ceiling, do we want that surfaced anywhere?
13:49  gideon    im in that file for the throttle change so i'd like to know before i touch it
13:52  emil      let me think through that
13:53  emil      honestly a refill capped back at the limit is only a full bucket. nothing has gone wrong at that point
13:55  dario     sure on the token side, thats just it sitting at max_tokens_per_minute. the request side pins the same way though and i didnt want to assume
13:57  emil      same story there, it tops out at max_requests_per_minute and thats the healthy state. nothing worth recording either way
```

#### `g10.r1.g10.r1.s2.l1`

- **chat** · #engineering · **konrad** · 2025-03-19 11:29
- carries `g10.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically I ran a split-limit config and both halves got held against the input number, so output ended up way deeper in the hole than its own 500 a minute ever justfied

As it appears, spread across the exchange:

```
13:41  konrad    the output side numbers from yesterday, why is it sitting so far under? i looked twice
13:43  gideon    so basically i ran a split limit config, separate ceiling each side
13:44  gideon    and output ended up way deeper in the hole than it had any buisness being
13:47  dermot    so both ceilings are getting charged off the one count, thats the guess?
13:49  gideon    ya. both halves got held against the input number
13:51  konrad    right, so the 500 a minute on output is just sitting there unused
13:53  gideon    exactly. its own 500 a minute never justfied a deficit anywhere near that. output has to come off its own count, thats the whole of it
13:56  dermot    mhm. i had that same config up friday and never once looked at the output half
```

#### `g10.r1.g10.r1.s4.l1`

- **chat** · #pipeline · **gideon** · 2025-03-19 11:44
- carries `g10.r1.exclusions_or_crossover`, `g10.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - on a smoke run that never once went under, the count came back 47. every refill that tops out at the limit is ticking it, and it shouldn't be

As it appears, spread across the exchange:

```
14:03  gideon    what is the count on the smoke run actually counting? came back 47
14:05  gideon    that run never once went under. not a single time the whole way through
14:08  nils      let me think. 47 on a run that never went under means its counting something other than what we think
14:10  dermot    if i had to guess its firing on the refill side, not the drain side
14:13  nils      yeah thats it. every refill that tops out at the limit is ticking it. capacity comes back, hits the ceiling, count goes up
14:15  gideon    so basically every refill on an idle run. thats your 47 right there
14:17  nils      and it shouldnt be. topping out isnt the thing that number is for, so that stops counting
```

#### `g10.r2.s1_l4`

- **chat** · #engineering · **konrad** · 2025-03-19 13:42
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - a request that actually reached the provider is spent for that minute whatever came back, it does not un-happen.

As it appears, spread across the exchange:

```
13:42  konrad    we had a minute where nearly all the calls came back errors. does that minute get its budget back?
13:43  konrad    off the top of my head i had assumed failed ones dont count against you
13:47  nils      let me think through that - a request that actually reached the provider is spent for that minute
13:49  dermot    so an error response still counts, even with nothing usable in it
13:50  nils      whatever came back, yes. it went out, it does not un-happen
13:51  nils      the line is whether it left us, not what came back. one that never got sent never owed the minute anything
13:53  konrad    right. not what the code does today though
13:55  dermot    mhm, the late night run reads differently now. i was watching the wrong half of it
```

#### `g10.r2.s3_l4`

- **chat** · #releases · **konrad** · 2025-03-19 14:02
- carries `g10.r2.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - on a requeue the request goes back on the queue and gets estimated again, so holding the old booking against it is charging the budget twice.

As it appears, spread across the exchange:

```
14:02  konrad    quick one on the budget side. when a request gets requeued, do we keep its booking or drop it?
14:06  dermot    drop, if i had to guess. it isn't in flight anymore at that point
14:09  konrad    but then nothing books it again? presumably the second attempt still needs capacity
14:15  emil      let me think through that - a requeue puts the request back on the queue like any other, so it gets estimated again on the way out
14:17  konrad    right, and the old one is still sitting there against us
14:20  emil      yup, thats the issue. holding the old booking against it is charging the budget twice for the one request
14:23  dermot    mhm. two holds, one request, and only one of them is real
```

#### `g10.r1.g10.r1.s1.l4`

- **chat** · #pipeline · **dermot** · 2025-03-19 14:03
- carries `g10.r1.rule`
- must be typed literally: `CAPACITY_DEBT_FLOOR_FRACTION`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> anyway, I pulled the 0.25 out of the settle path into CAPACITY_DEBT_FLOOR_FRACTION in capacity_budget.py, it was sitting inline there and again in a test.

As it appears, spread across the exchange:

```
14:03  dermot    whats the 0.25 in the settle path
14:04  konrad    floor fraction. it was written inline there and never got a name
14:06  dermot    ok but then why is the same 0.25 typed out in the tests too, i hit it grepping for something else
14:07  konrad    mhm. thats the actual problem, two copies of one number and nothing tying them together
14:08  konrad    anyway im pulling it out into a constant, CAPACITY_DEBT_FLOOR_FRACTION
14:09  emil      living in capacity_budget.py or somewhere more shared?
14:10  konrad    capacity_budget.py, top of the file. settle path reads it and the test imports it instead of writing the number again
14:12  dermot    yeah ok. the loose one in the test was what threw me, i had it down as a different number entirely
```

#### `g10.r1.g10.r1.s4.l3`

- **chat** · #code-review · **konrad** · 2025-03-19 14:03
- carries `g10.r1.exclusions_or_crossover`
- must be typed literally: `max_tokens_per_minute`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same goes for a relase handing back a big over-reservation - it clamps at max_tokens_per_minute rather than adding through past it, and that ceiling isnt the event were watching for.

As it appears, spread across the exchange:

```
14:03  konrad    Quick one before I go back to 595 - what happens when a release hands back a big over-reservation?
14:05  nikolai   hands back way more than it actually used you mean
14:06  konrad    mhm. the big ones. does the available pool just walk up past the top
14:08  nikolai   no it clamps at max_tokens_per_minute it doesnt add through past it
14:09  dario     and does that clamp get counted anywhere or does it just quietly happen
14:11  nikolai   quietly. that ceiling isnt the event were watching for
14:12  dario     makes sense, same goes for the release side then. its the same shape as the other case, i just hadnt seen it written down anywhere
14:14  konrad    right, nobody has written it yet. anyway, 595 is still open on my side
```

#### `g10.r2.s2_l3`

- **chat** · #cookbooks · **konrad** · 2025-03-20 13:04
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> counted it this morning we are doing thirty real requests a minute agaisnt a sixty ceiling because the attempts that came back 503 are still sitting on their slots

As it appears, spread across the exchange:

```
13:04  konrad    the cookbook batch took the whole morning again. what is actually slowing it down
13:07  dario     not the ceiling, honestly. we are nowhere near it
13:09  nikolai   counted it this morning we are doing thirty real requests a minute
13:11  konrad    thirty? we set that ceiling at sixty. so where does the other half go
13:14  nikolai   the attempts that came back 503 are still sitting on their slots
13:16  dario     so a dead attempt holds a slot same as a live one. that tracks with what i saw thursday
13:18  nikolai   right nothing lets them go so we only ever get half the lane those need to come off
13:20  konrad    ok. so the ceiling was never the problem
```

#### `g10.r2.s2_l2`

- **chat** · #engineering · **konrad** · 2025-03-20 13:35
- carries `g10.r2.rule`
- must be typed literally: `refund_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah, an attempt that errored bought us nothing, so refund_capacity returns the entire token reservation rather than whatever was left unspent.

As it appears, spread across the exchange:

```
13:35  konrad    Quick one on capacity. when an attempt errors, what goes back? full reservation or just the part it didnt use
13:38  emil      whole thing i believe. the attempt bought us nothing
13:40  konrad    but it did burn tokens before it died. presumably that part is real
13:43  dermot    not from our side. refund_capacity hands back the entire token reservation
13:45  konrad    Right, so not whatever was left unspent
13:46  dermot    no, the full reserved amount. it errored, theres nothing to net it against
13:48  emil      sounds right. i couldnt think of a case where the partial version helps anybody anyway
```

#### `g10.r1.g10.r1.s4.l4`

- **chat** · #code-review · **dario** · 2025-03-20 13:41
- carries `g10.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, a settle that leaves us at +100 on a 1000 tracker is not it either. It should only tick when we actaully stopped the fall.

As it appears, spread across the exchange:

```
13:41  dario     the counter - does every settle bump it, or only some of them
13:42  emil      i had it as every settle honestly, thats how the ticket reads to me
13:44  konrad    look, a settle that leaves us at +100 on a 1000 tracker is not it either
13:45  dario     so whats the bar. +100 is still on the right side of zero
13:46  konrad    it should only tick when we actaully stopped the fall. thats the whole test
13:47  dario     ok so being in the black isnt the test at all
13:49  emil      sounds right. the sheet i pasted monday counts all of them the same, that column isnt what the header says it is
```

#### `g10.r2.s2_l4`

- **chat** · #cookbooks · **nikolai** · 2025-03-21 14:02
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, if the call errored we hand its slot back, one per attemtp, and never above what the minute started with.

As it appears, spread across the exchange:

```
14:02  nikolai   whats meant to happen to the slot when a call comes back errored
14:03  konrad    it goes back. we took it for a call that didnt happen, so we hand it back
14:05  dario     back once for the request, or once per retry? some of these go round three or four times
14:06  konrad    one per attemtp. every attempt that errors hands its one back, not the whole request in a lump
14:07  nikolai   does that let it climb past where it was
14:08  konrad    no. never above what the minute started with, thats the ceiling
14:09  nikolai   right. thats the errored-attempt side settled then
14:11  dario     mhm. thats what bit us tuesday, the thing ended the minute higher than it went in
```

#### `g10.r1.g10.r1.s2.l2`

- **chat** · #pipeline · **gideon** · 2025-03-21 15:22
- carries `g10.r1.scope`
- must be typed literally: `A`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - in my grid the row where the caller passed 0 is A, and A still has the 100k default standing behind it, so it isn't a special case.

As it appears, spread across the exchange:

```
15:22  gideon    quick one, if the caller passes 0 for the cap do we branch on that or no?
15:24  dario     i had it down as its own case tbh, 0 reads like "no room" to me
15:29  nils      let me think. in the grid i wrote out yesterday, the row where the caller passed 0 is A
15:31  gideon    ok but what does A actually do with it
15:33  nils      A still has the 100k default standing behind it
15:35  dario     so 0 isnt a special case at all, it just lands on the default
15:36  nils      right, it isn't a special case. thats worth documenting on the row itself
15:38  gideon    ya. i had a whole branch for it in my head, good thing nobody wrote that yet
```

#### `g10.r2.s4_l1`

- **chat** · #cookbooks · **konrad** · 2025-03-24 15:02
- carries `g10.r2.exclusions_or_crossover`, `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on the failure path we hand back the token counts the failed response itself reported so the bucket finishes the minute holding more capacity than the limit allows took me a whlie to spot that

As it appears, spread across the exchange:

```
15:02  konrad    capacity thing again on the release run, the bucket is over the line by the end of the minute. Not entirely sure where it goes wide
15:08  nikolai   its the failure path i'd say not the limiter
15:11  konrad    what, the failed calls do not come back at all?
15:15  nikolai   they come back yep just wrong on the failure path we hand back the token counts the failed response itself reported
15:18  emil      so what gets released is whatever that response claimed for itself, not what we held. thats the gap?
15:21  nikolai   right so the bucket finishes the minute holding more capacity than the limit allows
15:24  nikolai   took me a whlie to spot that every number in there looks fine on its own
15:29  konrad    look, thats a whole morning I spent staring at the limiter. it sits on the error path then
```

#### `g10.r1.g10.r1.s2.l3`

- **chat** · #pipeline · **gideon** · 2025-03-24 15:11
- carries `g10.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> from the late night run - settle threw doing arithmetic on a None, that model has no token ceiling at all. no ceiling, nothing to take a share of, leave it be.

As it appears, spread across the exchange:

```
15:11  gideon    settle threw on me, traceback bottoms out doing arithmetic on a None
15:14  dermot    the late night run? which value came back None
15:16  gideon    the token ceiling. that model has none at all, not zero, just absent
15:19  dermot    then theres nothing there to take a share of
15:20  gideon    so we fill in a default and carry on?
15:23  dermot    no, leave it be. no ceiling, no share to hand out
15:25  dario     makes sense, otherwise were splitting up something that isnt there
15:27  gideon    ya. i burned twenty min looking for where it got set to zero and it never was
```

#### `g10.r2.s3_l1`

- **chat** · #viewer · **konrad** · 2025-03-27 14:12
- carries `g10.r2.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically every retry cycle on that flaky endpoint eats anohter reservation, capacity just walks down all afternoon and never comes back until we restart

As it appears, spread across the exchange:

```
14:12  konrad    viewer capacity has been sagging all week. by late afternoon its nowhere near where it starts
14:18  dermot    mhm. i bounced it yesterday around 5 and it was back to full straight after
14:23  gideon    so basically its the retries against that flaky endpoint. every cycle takes anohter reservation
14:27  konrad    what happens to the one the failed attempt was already holding
14:33  gideon    thats the thing, it never comes back. capacity just walks down all afternoon and stays down til we restart
14:39  dermot    yeah ok. so the retry path is the one exit that doesnt let go of it
14:45  gideon    ya. so it needs to hand it back there too, same as the other exits do. otherwise one endpoint flapping eats the whole day
```

#### `g10.r2.rev2` · **reversal**

- **chat** · #viewer · **dario** · 2025-04-03 13:38
- carries `g10.r2.rule`, `g10.r2.exclusions_or_crossover`
- takes back `g10.r2.h2`
- must be typed literally: `used_tokens`, `refund_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the except branch builds used_tokens but refund_capacity(blocked) refunds the whole estimate, and the slot returns on failure only, not success. saw 800 output reported against a 100 booking.

As it appears, spread across the exchange:

```
13:38  dario     when a call raises, whats actually going back to the pool? i had failure and success settling the same way in my head
13:41  emil      thats the old plan and its dead. we had it that the except branch has used_tokens built already, so failure settles through the same _free_capacity(used, blocked) as success, slot back on every terminal path. the code does neither half
13:43  dario     ok so what does the except branch do
13:44  emil      builds used_tokens, then calls refund_capacity(blocked). the whole estimate goes back and the used count just sits there
13:46  konrad    Which is the right way round, imo. I pulled a failed one reporting 800 output against a 100 booking
13:48  emil      yup. on failure the booking comes back whole, the reported usage doesnt enter into it. 800 or otherwise
13:49  dario     mhm. and the slot? i genuinely thought that one came back everywhere
13:51  emil      failure only. the release lives in the except branch and the success path just doesnt do it. thats the part that has to move
13:53  konrad    Anyway, is the old version written down somewhere? id rather strike it before someone builds to it
```

#### `g10.r2.s4_l2`

- **chat** · #cookbooks · **nikolai** · 2025-04-03 15:31
- carries `g10.r2.exclusions_or_crossover`
- must be typed literally: `finish_reason`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, the length ones are worst - finish_reason length, and the reponse reports 800 output against the 100 output we actually booked for it.

As it appears, spread across the exchange:

```
15:31  nikolai   went through todays run log, the output we booked and what the responses report back dont line up on a chunk of them
15:33  konrad    Look, the length ones are worst. the rest are close enough i think
15:34  nikolai   length meaning what
15:35  konrad    finish_reason length. the truncated ones
15:37  nikolai   how far off are we talking on those
15:38  konrad    took one at random, the reponse reports 800 output
15:39  nikolai   against what we had booked for it
15:40  konrad    against the 100 output we actually booked for it. anyway those we handle the way we agreed for the others, nobody has typed it up yet
15:42  dario     mhm. thats not something you smooth over in an estimate
```

#### `g10.r2.s3_l3`

- **chat** · #general · **konrad** · 2025-04-07 13:41
- carries `g10.r2.scope`, `g10.r2.rule`
- must be typed literally: `_refund_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - _refund_capacity should be firing at the point we give up on a request entirely, and right now nothing calls it there

As it appears, spread across the exchange:

```
13:41  konrad    capacity budget never climbed back after the run i killed friday. still low this morning
13:43  gideon    killed how? like you cancelled it, or it gave up on its own
13:45  konrad    gave up. we stopped trying that request at all, thats where it flattened
13:48  nils      let me think - _refund_capacity is what should be firing at that moment, the point we give up on a request entirely. i dont think we ever covered that one
13:50  gideon    so what calls it there today
13:52  konrad    nothing does. i grepped after standup, no caller at that spot at all. elsewhere it fires fine, just not there
13:54  nils      yeah, thats the hole. the call site simply isnt written yet, and that's worth documenting somewhere
13:56  konrad    anyway that matches friday, it sat flat for hours after
```

#### `g10.r2.s3_l2`

- **chat** · #pipeline · **emil** · 2025-04-07 13:51
- carries `g10.r2.scope`
- must be typed literally: `attempts_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> in the retry path, the branch where attempts_left is zero appends the failure and returns, thats the whole of it. our capacity charts never recover after a bad model

As it appears, spread across the exchange:

```
13:36  emil      our capacity charts never recover after a bad model. it dips and thats the ceiling for the rest of teh run
13:38  dermot    so its not the chart, its that nothing ever puts the capacity back?
13:39  emil      thats where i landed. i belive its somewhere in the retry path
13:41  dermot    the branch where attempts_left is zero, if i had to guess
13:43  dario     thats the one. it appends the failure and returns, thats the whole of it, so what that request was holding stays spent. it has to give that back on the way out too, not just record the faliure
13:45  dermot    mhm
13:46  emil      yup. and it stacks, two bad models in one run and theres barely any headroom left
```

#### `g10.r1.g10.r1.s1.l1`

- **chat** · #engineering · **konrad** · 2025-04-08 12:53
- carries `g10.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> estimator came in light again, third window in a row we went past the provider ceiling - and the ledger resets to zero each minute so that overshoot is gone

As it appears, spread across the exchange:

```
14:02  konrad    estimator came in light again on last nights batch
14:04  nikolai   light how
14:06  konrad    enough that we went past the provider ceiling. thats three windows in a row now
14:08  nikolai   and it never pulls itself back after
14:10  dario     it cant, actually. the ledger resets to zero each minute
14:11  nikolai   so the amount we went over by
14:13  dario     gone. its not sitting anywhere when the next minute opens, which to be honest is most of why this keeps repeating
14:15  konrad    mhm. i kept looking at it right after a reset, no wonder it read fine every time
```

#### `g10.r1.rev1` · **reversal**

- **chat** · #pipeline · **dermot** · 2025-04-08 14:42
- carries `g10.r1.rule`
- takes back `g10.r1.clamp-at-zero-decision`
- must be typed literally: `free_capacity`, `CAPACITY_DEBT_FLOOR_FRACTION`, `0.25`, `0.0`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on that layer, the 0.0 clamp in free_capacity is gone - forgiving the overshoot let a light estimator run past the provider ceiling three windows straight. it goes negative now, floored per axis at -CAPACITY_DEBT_FLOOR_FRACTION * limit, 0.25

As it appears, spread across the exchange:

```
14:11  dermot    the estimator overshot the openai ceiling again over the weekend. three windows back to back, still submitting
14:13  dermot    if i had to guess free_capacity is just eating it? we clamp every axis at 0.0, so an under-estimate gets forgotten at settlement. that was the review call last year
14:14  dario     that was the call, yeah. and its gone. the 0.0 clamp comes out of free_capacity — forgiving the overshoot is exactly what let a light estimator run past the provider ceiling three windows straight
14:16  dermot    so it goes negative now
14:17  dario     it goes negative now. you carry the debt into the next window instead of pretending nothing happend
14:18  nils      one bad estimate digs a hole we never get out of then
14:19  dario     no, theres a floor, per axis. -CAPACITY_DEBT_FLOOR_FRACTION * limit. so tokens can be underwater while requests is fine, and neither one goes deeper than that fraction of its own limit
14:20  nils      and the fraction is
14:21  dario     0.25. below that youre stalled a full window regardless, so theres honestly nothing left to track
14:23  dermot    mhm. is that a constant or does it come off the provider config
```

#### `g10.r1.g10.r1.s3.l1`

- **chat** · #pipeline · **dario** · 2025-04-09 09:17
- carries `g10.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly though, to see how often we bottom out I've been diffing ledgers between runs, which is stupid - the tracker should just carry a plain counter starting at 0 and tell me.

As it appears, spread across the exchange:

```
13:11  dario     is there anything today that tells us how often we're bottoming out on capacity, or am i imagining that
13:12  gideon    nope, nothing tells you. honestly though i've been diffing ledgers between runs to see it
13:12  gideon    which is stupid, im reconstructing a number the tracker allready knows
13:13  dario     so it just carries the count itself and hands it over?
13:14  gideon    exactly. a plain counter on the tracker, and it tells me. no more diffing runs
13:15  dermot    does it only show up after the first one, or is it there from the start
13:16  gideon    from the start, sitting at 0. um, zero is information too - "we never bottomed out" is a real answer
13:17  dermot    yeah ok, no null case then. i can graph it straight
```

#### `g10.r2.rev1` · **reversal**

- **chat** · #incidents · **dermot** · 2025-04-09 13:21
- carries `g10.r2.rule`, `g10.r2.scope`
- takes back `g10.r2.h1`
- must be typed literally: `_free_capacity`, `refund_capacity`, `free_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the one _free_capacity(used_tokens, blocked_capacity) for both outcomes was the 240 in a 200 minute. failure refunds via refund_capacity(blocked), estimate plus 1.0 slot back; success free_capacity(used, blocked), slot stays spent.

As it appears, spread across the exchange:

```
13:21  dermot    the 240 in a 200 minute last night - if i had to guess its the release path
13:22  dermot    we settled this months ago, one _free_capacity(status_tracker, used_tokens, blocked_capacity) for both outcomes, and the request slot going back on failure exactly like it does on success
13:24  dario     mhm, and thats the half thats gone. a request that actually landed spent its slot for that minute. handing it back is how you get 240 out of a 200 minute
13:25  gideon    So two calls now instead of the one?
13:26  dario     yeah. success side is free_capacity(used, blocked), and the slot stays spent
13:27  dermot    and failure? not entirely sure what youre keeping there. the estimate comes back, but the slot too or no
13:28  dario     refund_capacity(blocked) on that side, so the estimate plus the 1.0 slot back. nothing went out, so the minute never owed it in the first place
13:30  gideon    Ya ok. the retry loop hits the release twice on a timeout today, that was fine when both outcomes went through the same call
```

#### `g10.r2.s2_l1`

- **chat** · #pipeline · **gideon** · 2025-04-10 11:40
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> different shape but same area - gemini 503'd on everything last night, and by minute two we were down to one request every few seconds with zero successes.

As it appears, spread across the exchange:

```
13:11  gideon    whats the gemini thing from last night, is it the same as the deepseek throttling or a different animal
13:13  dario     different, i think. it 503'd on everything, and that was all night not a window
13:15  emil      different shape but same area honestly. deepseek makes you slow down, gemini just refused
13:16  gideon    slow down to what though, um. what were we actually pushing by then
13:18  emil      by minute two we were down to one request every few seconds, with zero successes out of any of it
13:20  emil      so it lands with the deepseek handling either way, same area, just not the same failure. nobodys writing that today though
13:22  gideon    wait, minute two. i was looking at the first minute and it read normal to me
```

#### `g10.r2.s5_l2`

- **chat** · #cookbooks · **dario** · 2025-04-11 13:36
- carries `g10.r2.observability`
- must be typed literally: `num_capacity_settlements`, `num_capacity_refunds`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, the tracker dump needs num_capacity_settlements and num_capacity_refunds as separate counters, otherwise I cannot tell the two kinds of release apart in a run.

As it appears, spread across the exchange:

```
13:36  dario     when a hold gets released back to the pool, does the tracker dump show that anywhere or is it just folded into the totals
13:39  konrad    its all one bucket right now. fine until you actually have to read it
13:41  dario     so one release count, or do you want it broken out
13:43  konrad    broken out. num_capacity_settlements as its own counter in the dump
13:44  konrad    and num_capacity_refunds seperate, next to it
13:47  emil      whats actually wrong with the one number though
13:51  konrad    look, summed together i cannot tell the two kinds of release apart in a run. thats the whole of it
13:53  emil      ok that i buy. added up they read as the same event and they arent
```

#### `g10.r2.say23`

- **chat** · #incidents · **gideon** · 2025-04-11 13:42
- carries `g10.r2.rule`
- must be typed literally: `_refund_capacity(self, status_tracker, blocked_capacity)`, `status_tracker.refund_capacity(blocked_capacity)`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on the refund path the processor side stays thin — `_refund_capacity(self, status_tracker, blocked_capacity)` just calls `status_tracker.refund_capacity(blocked_capacity)` and honestly that's the whole body

As it appears, spread across the exchange:

```
13:42  gideon    quick one on the refund path — what is the processor side actually meant to do with the blocked capacity? i keep drawing the arrow both directions
13:44  dermot    if i had to guess you want it thin there. the processor doesnt do the arithmetic itself, it hands the number back to the tracker
13:45  gideon    ok but thin how. does it take the tracker in or go reach for it, and does it still keep its own bookkeping after
13:47  dario     takes it in. `_refund_capacity(self, status_tracker, blocked_capacity)` — the tracker and the blocked amount, nothing else on the signature
13:48  gideon    and inside? theres got to be more in there tbh
13:50  dario     no, honestly thats the whole body. it just calls `status_tracker.refund_capacity(blocked_capacity)` and thats it. no second set of numbers on the processor side
13:51  dermot    yeah ok. that matches how i had it in my head. nobody has typed it yet as far as i know
13:52  gideon    ya. i'll stop hunting for the subtraction in the processor then. is the tracker end already sitting there or is that new as well
```

#### `g10.r2.say25`

- **chat** · #viewer · **dermot** · 2025-04-14 14:12
- carries `g10.r2.observability`
- must be typed literally: `available_request_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically i dumped the trakcer on one of those unlimited runs and available_request_capacity comes back as None, so there is no number to watch there, only the counters.

As it appears, spread across the exchange:

```
14:12  dermot    for the capacity row in the viewer, do we draw it the same on the unlimited runs? or is there something to hide there
14:14  gideon    so basically i dumped the trakcer on one of those unlimited runs to look. the counters are all sitting there like normal
14:15  dermot    sure but the capacity number itself, thats what i'm asking about
14:16  emil      let me think through that. i believe it just pins at the ceiling and never moves? that would still be a number at least
14:18  gideon    no thats the thing, available_request_capacity comes back as None on those. so there is no number to watch there, um, nothing to put in that spot
14:19  dermot    mhm. so that row has nothing behind it at all
14:20  gideon    ya. only the counters on those runs, thats all the panel has to work with
```

#### `g10.r2.s1_l2`

- **chat** · #engineering · **dermot** · 2025-04-16 13:50
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> per-request i think - on a clean response the only thing we put back into the budget is the gap between what we booked and what it actually spent

As it appears, spread across the exchange:

```
14:02  dermot    the capacity we hold up front for a request — do we hand it back per request, or settle once the whole batch drains?
14:05  dario     per request i think. sitting on it til the batch is done just starves everything at the tail
14:07  dermot    mhm. and on a clean response we put the whole booking back?
14:09  dario     no, only the gap honestly. what we booked for it vs what it actually spent, the difference is the part that goes back
14:11  emil      so the booking was the ceiling and we're just returning what we over-reserved. sounds right
14:12  dario     mhm, thats it
14:14  dermot    then one that lands dead on its estimate returns nothing at all
14:16  dario     right, nothing to give back there. best we can do until someone writes it
```

#### `g10.r1.rev2` · **reversal**

- **chat** · #pipeline · **emil** · 2025-04-16 17:34
- carries `g10.r1.rule`, `g10.r1.observability`
- takes back `g10.r1.clamp-at-zero-rationale`
- must be typed literally: `0.0`, `CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_debt_clamps`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> also from the batch-side pass: 0.0 isn't the floor anymore, minute two opens owing the overshoot down to -CAPACITY_DEBT_FLOOR_FRACTION * limit and num_capacity_debt_clamps counts each such call.

As it appears, spread across the exchange:

```
16:21  emil      one more thing out of the batch-side pass while i still have it in front of me - the capacity accounting isnt what we wrote down. a call that overshoots doesnt just get forgiven at the minute boundary
16:26  dermot    so if i had to guess, that's dario's pass on 387 going away? zero is the floor, a bucket sitting at 0.0 is empty and that's the whole story, no accounting for overshoot, next refill starts clean
16:29  emil      yup that ones gone. 0.0 isnt the floor anymore - minute two opens owing the overshoot instead of starting clean. the forgiving is exactly how we were sailing past the limit
16:34  dario     mhm, that was mine. so is it unbounded on the negative side, or does it stop somewhere
16:37  emil      bounded. -CAPACITY_DEBT_FLOOR_FRACTION * limit is as deep as it goes
16:41  dermot    and we can see it when a call lands on that floor, or is it silent
16:44  emil      num_capacity_debt_clamps, counts each such call. none of it is in the tree yet, thats the shape we settled on
16:49  dario     i wrote the 0.0-is-empty line in 387 like it was the obvious reading and it just quietly ate the overshoot every minute
```

#### `g10.r2.s5_l1`

- **chat** · #pipeline · **dario** · 2025-04-17 16:35
- carries `g10.r2.observability`
- must be typed literally: `num_capacity_refunds`, `num_capacity_settlements`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly, the last progress counter we ticked from both paths never matched the request count. these two only move on release — an acquire bumps neither num_capacity_settlements nor num_capacity_refunds.

As it appears, spread across the exchange:

```
13:21  dario     the last progress counter we ticked from both paths never matched the request count. either im reading it wrong or it isnt counting what i think it is
13:24  emil      let me think through that... i believe those two only move on release. so the number youre looking at was never going to track requests
13:26  dario     both of them though? i had num_capacity_refunds down as the acquire side, that was the whole basis for the check i drafted
13:29  emil      no. an acquire bumps neither num_capacity_settlements nor num_capacity_refunds, nothing on the way in touches either one
13:31  dermot    mhm. so the delta only ever shows up coming back out
13:33  dario     that tracks, and it explains the gap. the draft check comes out then, nobody has written it against the real thing yet
13:35  emil      yup. honestly the naming does you no favors there either
```

#### `g10.r1.say19`

- **chat** · #incidents · **nikolai** · 2025-04-18 15:07
- carries `g10.r1.scope`
- must be typed literally: `max_requests_per_minute`, `available_request_capacity`, `None`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same shape on the request side - with no max_requests_per_minute set, available_request_capacity just reads back None, so there's nothing there to floor either

As it appears, spread across the exchange:

```
15:07  nikolai   dermot the capacity dump off the stalled run has available_request_capacity None sitting in it
15:08  nikolai   did we put that there or is something eating it
15:12  dermot    neither. same shape on the request side as the one you were poking at yesterday
15:13  nikolai   same shape how, None isnt a number, whats even reading it
15:15  dermot    with no max_requests_per_minute set, available_request_capacity just reads back None. nothing ever gets put in it
15:16  nikolai   ok so does the floor still land on it or does it skip
15:17  dermot    so theres nothing there to floor either. no value sitting in it to clamp at all
15:19  petar     that lines up with the box, no request limit configured on it
```

#### `g10.r2.s1_l1`

- **chat** · #help · **gideon** · 2025-04-21 13:15
- carries `g10.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Also from the same profile - estimator books 1k output tokens on every haiku call, actual comes back under 150, and then we crawl for the rest of the minute.

As it appears, spread across the exchange:

```
15:11  gideon    back on that same profile - the haiku calls are the other thing. we reserve way more output than they ever use
15:12  dermot    reserve how much per call
15:13  gideon    1k output tokens. every single haiku call, doesnt matter what it is
15:14  dermot    and what actually comes back
15:15  gideon    under 150. honestly though the part that hurts is after, we crawl for the rest of the minute
15:16  nikolai   crawling because the minute is already spoken for on paper
15:17  gideon    exactly. so the haiku number cant stay a flat guess, it has to follow what the calls really do
15:18  nikolai   yep thats your stuttering bars right there
```

#### `g10.r2.s4_l3`

- **chat** · #general · **dermot** · 2025-04-21 14:09
- carries `g10.r2.exclusions_or_crossover`
- must be typed literally: `available_token_capacity`, `refund_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think — on the throw-away path the booking is the only number we own, and refund_capacity hands it back clamped so available_token_capacity never ends above the limit.

As it appears, spread across the exchange:

```
14:09  dermot    on the discard path what do we actually hand back? theres no real count coming home
14:13  nils      let me think — the booking is the only number we own there, so thats what goes back
14:16  dermot    so we return the reservation as-is. doesnt that risk overshooting the ceiling
14:19  nils      refund_capacity hands it back clamped, so available_token_capacity never ends above the limit
14:21  nikolai   right so worst case its a no op
14:24  nils      more or less. thats worth documenting right next to the refund call i think
14:26  nikolai   yep. beats keeping a second number around for a response were dropping anyway
```

#### `g10.r2.s5_l3`

- **chat** · #releases · **dermot** · 2025-04-24 14:07
- carries `g10.r2.observability`
- must be typed literally: `num_capacity_refunds: int = 0`, `num_capacity_settlements: int = 0`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran anthropic overnight with no token ceiling set and the counts never moved off `num_capacity_settlements: int = 0` / `num_capacity_refunds: int = 0` so i spent the morning hunting a bug that wasnt ther

As it appears, spread across the exchange:

```
14:07  dermot    the anthropic run from last night, did any of the capacity numbers move
14:09  nikolai   no i ran it overnight with no token ceiling set at all and the counts never moved
14:11  dario     flat on both counters or just the settlements one
14:12  dermot    both. report came back with `num_capacity_settlements: int = 0` and the refunds one right under it
14:14  nikolai   yep and `num_capacity_refunds: int = 0` is word for word what the field declares so what i got back and what it starts at are the same string i cant tell one from the other by looking
14:16  dario     so broken or not, i cant tell from that either
14:18  nikolai   thats the thing that run doesnt answer it i spent the morning hunting a bug that wasnt ther in anything i was reading were not calling it broken off a run with no ceiling on it someone sets one low enough to actually get hit and runs it again thats the only version of this thats worth anything
```

#### `g10.r2.say24`

- **chat** · #general · **dermot** · 2025-04-29 15:04
- carries `g10.r2.observability`
- must be typed literally: `available_token_capacity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think — if nobody configures a token limit, available_token_capacity is None for the whole life of that tracker, it never becomes a number.

As it appears, spread across the exchange:

```
15:04  dermot    quick one — if nobody configures a token limit anywhere, what does available_token_capacity read as
15:06  nils      None. i think it's None from the moment that tracker comes up, there's nothing to compute it from
15:07  dermot    right, but it gets backfilled later? i couldn't find where i'd look for that
15:09  nils      let me think — no. it stays None for the whole life of that tracker, it never becomes a number
15:10  dermot    mhm. so not a startup gap, just the state
15:11  nils      yeah. nothing sets it after the fact, so anything reading it has to cope with None the whole way through. that's worth documenting
15:13  emil      yup, that explains the one i was staring at this morning, it was blowing up on the compare
```

#### `g10.r2.s5_l4`

- **chat** · #releases · **dario** · 2025-05-02 14:11
- carries `g10.r2.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> we're counting the call, not whether it moved a number. a release against an unlimited axis went through the same code path, so it still increments.

As it appears, spread across the exchange:

```
14:11  dario     quick one before i touch the capacity counter — a release on an axis that had no limit set. counted, or skipped?
14:14  emil      my read is counted but honestly not entirely sure. nothing moved on that axis so you could argue either way
14:16  dermot    counted. we're counting the call, not whether it moved a number
14:18  dario     even when there was nothing to give back though? unlimited before, unlimited after
14:20  dermot    mhm. a release against an unlimited axis still went through the same code path as any other one, so it goes in the count
14:21  emil      yup, no special case to thread through then
14:23  dario     ok. the fixture i wrote assumes the opposite so thats mine to redo
```

#### `g10.r1.g10.r1.s1.l2`

- **chat** · #pipeline · **gideon** · 2025-05-13 15:36
- carries `g10.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly if we burned more than we reserved, minute two should open owing that much. right now it opens fresh every time and I don't love it.

As it appears, spread across the exchange:

```
15:36  gideon    whats supposed to happen when a minute goes over what it reserved?
15:37  dario     today? nothing. the next minute opens fresh, every time
15:38  gideon    fresh as in zero even if we overshot. um, that seems wrong
15:40  emil      honestly i dont love it either. we burned more than we reserved on that run and the boundary just wiped it
15:41  gideon    so basically what should minute two look like instead
15:42  emil      it should open owing that much. not at zero
15:44  dario     mhm, the deficit rides over the boundary. im going to want a window that opens in the red to not read the same as a fresh one
```

