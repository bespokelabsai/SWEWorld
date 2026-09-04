You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

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

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: Token capacity may go negative, but each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` with `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25` exported from the capacity-budget module. The floor is `-limit * 0.25` as a `float` for the `combined` axis. Worked case: a tracker with `max_tokens_per_minute=1_000`, after `consume_capacity(_TokenUsage(input=700, output=100))` and then settling `used=_TokenUsage(input=1000, output=500)` against `blocked=_TokenUsage(input=700, output=100)`, ends at `available_token_capacity == -250.0`.
   - *scope*: A tracker constructed with `max_tokens_per_minute=0` (defaulted to 100_000) floors at `-25000.0`, and under `seperate` each axis floors against its own limit: with `_TokenUsage(input=1_000, output=500)` an over-settled tracker lands on `_TokenUsage(input=-250, output=-125, total=-375)`. An axis whose limit and capacity are `None` has no floor and stays `None`. `available_request_capacity` is never floored.
   - *exclusions or crossover*: Capping an axis at its UPPER bound is not a clamp and never touches the counter: neither the refill in `update_capacity` raising an axis back up to `max_tokens_per_minute`, nor a release raising it to that same ceiling, increments `num_capacity_debt_clamps`. The counter increments ONLY when the lower debt floor `-CAPACITY_DEBT_FLOOR_FRACTION * limit` is applied. So a settlement whose result stays above that floor (e.g. `available_token_capacity == 100.0` on a 1_000-token tracker) leaves the counter at `0`, and so does a refill that lands exactly on `1000.0` rather than the `1200.0` it would otherwise reach.
   - *observability*: A tracker field `num_capacity_debt_clamps: int = 0` increments by exactly one per call that clamped at least one axis.

2.
   - *rule*: `free_capacity(used, blocked)`: the token axes gain `blocked - used` and `available_request_capacity` is left exactly as `consume_capacity` left it. `refund_capacity(blocked: _TokenUsage) -> None`: the token axes gain the whole `blocked` estimate back (capped above at the limit) and `available_request_capacity` gains exactly `1.0`, capped above at `max_requests_per_minute`. The processor's `_refund_capacity(self, status_tracker, blocked_capacity)` delegates to `status_tracker.refund_capacity(blocked_capacity)`.
   - *scope*: Every terminal path through the `except Exception` branch of `handle_single_request_with_retries` calls the refund — both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`). On a tracker with `max_requests_per_minute=60`, `max_tokens_per_minute=10_000` and a reservation of `_TokenUsage(input=700, output=300)`, either failure path ends at `available_request_capacity == 60.0` and `available_token_capacity == 10000.0`, while the success path with reported usage `_TokenUsage(input=700, output=100)` ends at `59.0` / `9200.0`.
   - *exclusions or crossover*: The failure refund uses the full blocked estimate and ignores `generic_response.token_usage` — e.g. a response with `finish_reason="length"` (in `config.invalid_finish_reasons`) reporting `_TokenUsage(input=900, output=800)` against a blocked estimate of `_TokenUsage(input=900, output=100)` returns the estimate.
   - *observability*: Two tracker counters, `num_capacity_settlements: int = 0` and `num_capacity_refunds: int = 0`, each incremented by exactly one by its own operation and by neither the other's. Both counters still increment when the affected capacity is `None` and the operation is a no-op on every axis.

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
