# Online token-capacity budget: reservation, release and reported limits

Replace the ad-hoc per-minute rate-limit bookkeeping in the online request processors with a single capacity-budget module: one place that parses provider limit headers, and a tracker whose reservation/release accounting is correct and testable without a wall clock.

### New module `src/bespokelabs/curator/status_tracker/capacity_budget.py`

- Move `TokenLimitStrategy` here unchanged (`str, Enum`; members `combined = "combined"`, `seperate = "seperate"`, `default = "combined"`) and re-export it from `online_status_tracker` so existing importers keep working.
- Constants: `DEFAULT_MAX_REQUESTS_PER_MINUTE: int = 200`, `DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED: int = 100_000`, `DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE: int = 100_000`, `DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE: int = 40_000`, `LIMIT_ORIGIN_CONFIGURED: str = "configured"`, `LIMIT_ORIGIN_DEFAULTED: str = "defaulted"`, `LIMIT_ORIGIN_UNLIMITED: str = "unlimited"`.
- Header-name tuples, consulted in tuple order, first present-and-parseable name winning:
  - `REQUEST_LIMIT_HEADERS = ("x-ratelimit-limit-requests", "anthropic-ratelimit-requests-limit")`
  - `INPUT_TOKEN_LIMIT_HEADERS = ("x-ratelimit-limit-input-tokens", "anthropic-ratelimit-input-tokens-limit")`
  - `OUTPUT_TOKEN_LIMIT_HEADERS = ("x-ratelimit-limit-output-tokens", "anthropic-ratelimit-output-tokens-limit")`
  - `TOTAL_TOKEN_LIMIT_HEADERS = ("x-ratelimit-limit-tokens", "anthropic-ratelimit-tokens-limit")`
- `class CapacityExceedsLimitError(ValueError)` with `__init__(self, axis: str, requested: int, limit: float)`, storing `.axis`, `.requested`, `.limit`, and message exactly `f"request needs {requested} {axis} capacity but the per-minute limit is {int(limit)}"`.
- `@dataclass(frozen=True) class RateLimitReading` with fields in this order: `max_requests_per_minute: int | None`, `max_tokens_per_minute: int | _TokenUsage | None`, `token_limit_strategy: TokenLimitStrategy`, `source_headers: tuple[str, ...]`.
- `def parse_limit_value(raw: object) -> int | None` — the single value decoder. `bool` is rejected (`None`) even though it is an `int` subclass; an `int` returns itself if `> 0` else `None`; a `str` is stripped and matched against `^(\d+(?:\.\d+)?)([kKmM]?)$`, the numeric part multiplied by `1`/`1_000`/`1_000_000` for suffix `""`/`k`,`K`/`m`,`M`, then `math.floor`ed, returned if `> 0` else `None`; anything else (`float`, `None`, `bytes`, `"1,000"`, `"1e3"`, `"-5"`, `""`, `"unknown"`) is `None`. Nothing raises — a malformed header is absent, not fatal.
- `def read_rate_limit_headers(headers: t.Mapping[str, object]) -> RateLimitReading` — module-level, mutates nothing. Lower-cases incoming keys once (so `"X-RateLimit-Limit-Tokens"` matches) and consults **only** the four tuples above; no `*-remaining`, `*-reset` or `llm_provider-*` key is ever read, and there are no hardcoded numeric fallbacks. `anthropic-ratelimit-input-tokens-limit` feeds the **input** axis, `anthropic-ratelimit-output-tokens-limit` the **output** axis. When both an input and an output limit parse to positive ints the reading is `seperate` with `max_tokens_per_minute = _TokenUsage(input=…, output=…)` and any total-token header is ignored; otherwise the reading is `combined` and the total-token header is used, a lone half of the pair being discarded. With nothing usable: `max_tokens_per_minute=None`, `token_limit_strategy=combined`. `source_headers` lists the header names actually consumed, request axis first, then `(input, output)` or `(total,)`, and is `()` when nothing was consumed.

### `src/bespokelabs/curator/status_tracker/online_status_tracker.py`

- `max_tokens_per_minute: int | _TokenUsage | None = 0` is declared **exactly once** (the duplicate declaration at line 64 goes away).
- New field `capacity_clock: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)`. Every wall-clock read in `update_capacity` goes through `self.capacity_clock()`, and `__post_init__` re-seeds `self.last_update_time = self.capacity_clock()`. `start_time`, `_last_stats_update`, the display code and `cool_down_if_rate_limit_error` keep calling `time.time()` directly. In `update_capacity`, `elapsed` is clamped with `max(0.0, elapsed)` before refilling and `last_update_time` is assigned unconditionally, including when the clock reads earlier than the previous reading.
- New `init=False` string fields `token_limit_origin` and `request_limit_origin`, defaulting to `LIMIT_ORIGIN_CONFIGURED`.
- `__post_init__` normalises both limits and records their origin:
  - limit `None` → unlimited: the limit stays `None`, the matching available capacity is `None`, origin `"unlimited"`. Under `seperate`, unlimited is `_TokenUsage(input=None, output=None)`, and a whole-token limit of `None` normalises to exactly that.
  - limit `0` (or, under `seperate`, an axis that is `0`) → replaced axis by axis with the `DEFAULT_MAX_*` constants, origin `"defaulted"` if any axis was replaced.
  - a positive number → origin `"configured"`.
  - Shape coercion: under `combined` a `_TokenUsage` limit collapses to its `.total`; under `seperate` an `int` limit `N` becomes `_TokenUsage(input=N, output=N)`.
- `__post_init__` then seeds both buckets to their full per-minute limit, overwriting whatever the caller passed for `available_request_capacity` / `available_token_capacity`: `float(max_requests_per_minute)`, and `float(max_tokens_per_minute)` under `combined` / `_TokenUsage(input=limit.input, output=limit.output)` under `seperate`.
- Under `seperate`, every mutation of `available_token_capacity` **rebinds a freshly constructed `_TokenUsage(input=…, output=…)`** instead of assigning to `.input`/`.output`, so `.total` is never stale; the refill increment per axis is `math.floor(limit_axis * elapsed / 60.0)`, keeping axis values `int`.
- Methods (all return `None` and mutate the tracker, except `has_capacity`):
  - `def update_capacity(self) -> None`
  - `def has_capacity(self, token_estimate: _TokenUsage) -> bool` — **before** calling `update_capacity()`, for each axis with a non-`None` limit, if the requested amount is strictly greater than the per-minute limit it raises `CapacityExceedsLimitError(axis, requested, limit)` rather than returning `False`, leaving `last_update_time` and both buckets untouched. Axis names and check order: `"total"` under `combined`; `"input"` then `"output"` under `seperate`. An unlimited axis never raises. A merely-empty bucket returns `False`.
  - `def consume_capacity(self, token_estimate: _TokenUsage) -> None`
  - `def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage) -> None` — settles a finished reservation: token axes gain `blocked - used` per axis (`blocked.total - used.total` under `combined`), each axis capped above at its per-minute limit.
- A capacity that is `None` is untouchable: `has_capacity`, `consume_capacity`, `free_capacity` and `update_capacity` read it, skip it, and leave it `None`.
- Capacity shapes: `combined` limited → `int` limit and `float` capacity; `combined` unlimited → `None`/`None`; `seperate` limited → `_TokenUsage(input=int|None, output=int|None)` on both; `max_requests_per_minute` is `int > 0` or `None`, with `available_request_capacity` a `float` or `None` in lockstep.

### `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py`

- New `def _reserve_capacity(self, status_tracker: OnlineStatusTracker, messages: list) -> _TokenUsage | None` — a plain synchronous method that (1) calls `self.estimate_total_tokens(messages)` exactly once, **unconditionally**, including when `status_tracker.max_tokens_per_minute is None`; (2) calls `status_tracker.has_capacity(estimate)`, letting `CapacityExceedsLimitError` propagate; (3) on `True` calls `status_tracker.consume_capacity(estimate)` and returns the very `_TokenUsage` object it estimated; (4) on `False` returns `None` having consumed nothing at all — neither tokens nor the request slot.
- Both reservation loops (lines 384-391 and 432-439) become `while (token_estimate := self._reserve_capacity(status_tracker, request.generic_request.messages)) is None: await asyncio.sleep(0.1)`, with the sleep the only remaining await; the current "estimate only when there is a token limit" branch at lines 377-380 goes away.
- New `def _free_capacity(self, status_tracker: OnlineStatusTracker, used_capacity: _TokenUsage, blocked_capacity: _TokenUsage) -> None` delegating to the tracker.
- In `handle_single_request_with_retries`, the reservation is released **exactly once per attempt, on every terminal path** — the success/`else` path (unchanged position, line 584) and both exits through `except Exception` (the requeued case and the exhausted case), each immediately before its `return`. Today only line 584 releases, so a failed attempt's reservation is burned permanently.
- The empty, uncalled `def free_capacity(self, tracker, tokens)` at line 312 is deleted (`hasattr(BaseOnlineRequestProcessor, "free_capacity")` must become `False`).
- New `def apply_rate_limit_reading(self, reading: RateLimitReading) -> None` — the only place that writes processor state from a reading: sets `self.header_based_max_requests_per_minute`, `self.header_based_max_tokens_per_minute` and `self.token_limit_strategy = reading.token_limit_strategy`, then **re-reads** `self.default_max_tokens_per_minute` from `_DEFAULT_COST_MAP["online"]["default"]["ratelimit"]["max_tokens_per_minute"]` for the *new* strategy (`int` for `combined`, `_TokenUsage(**block)` for `seperate`), fixing the ordering bug where `__init__` reads the default block while the strategy is still `combined`.
- The manual → header → default precedence of the `max_requests_per_minute` / `max_tokens_per_minute` / `max_concurrent_requests` properties (lines 181-217) is unchanged.

### Provider processors

- `anthropic_online_request_processor.get_header_based_rate_limits()` delegates to `read_rate_limit_headers()`, dropping the swapped input/output mapping at lines 149-150 and the `4000`/`80000`/`400000` fallbacks.
- `litellm_online_request_processor.get_header_based_rate_limits()` delegates, dropping the `llm_provider-…-remaining` reads and the `self.token_limit_strategy = …` mutation at lines 314-321.
- `openai_online_request_processor.get_header_based_rate_limits()` delegates for the header half (lines 150-159); its `RATE_LIMIT_HEADER` provider table and the `rps`/`tps` scaling stay exactly as they are.

### Reusable / out of scope

- Reuse unchanged: `_TokenUsage`, the tracker's display machinery (`start_tracker`, `_refresh_console`, `update_stats`, `update_cost_projection`, `stop_tracker`), `_DEFAULT_COST_MAP[...]["ratelimit"]`, the `try/except/else/finally` shape of `handle_single_request_with_retries` including `config.invalid_finish_reasons` and `append_generic_response`, and `bespokelabs.curator.cost.RATE_LIMIT_HEADER`.
- Not touched: `cool_down_if_rate_limit_error`, `config.seconds_to_pause_on_rate_limit`, `config.max_retries`, the retry queue and its ordering, `num_rate_limit_errors`, `time_of_last_rate_limit_error`.
- Python 3.10, stdlib only (`re`, `math`, `dataclasses`); no new dependency, no network in tests.
