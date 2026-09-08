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
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 46 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 14:02–14:13 | Mattermost `#engineering` — an exchange of 8 messages, opened by **konrad** |
| 2 | 2025-01-21 | 15:12–15:26 | Mattermost `#releases` — an exchange of 7 messages, opened by **konrad** |
| 3 | 2025-01-21 | 15:49–16:03 | Mattermost `#code-review` — an exchange of 10 messages, opened by **konrad** |
| 4 | 2025-01-28 | 14:05–14:18 | Mattermost `#releases` — an exchange of 8 messages, opened by **nikolai** |
| 5 | 2025-03-14 | 13:04–13:14 | Mattermost `#engineering` — an exchange of 9 messages, opened by **dermot** |
| 6 | 2025-03-14 | 13:41–13:55 | Mattermost `#code-review` — an exchange of 7 messages, opened by **gideon** |
| 7 | 2025-03-17 | 13:11–13:24 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 8 | 2025-03-17 | 13:41–13:47 | Mattermost `#code-review` — an exchange of 7 messages, opened by **nikolai** |
| 9 | 2025-03-17 | 14:03–14:13 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dario** |
| 10 | 2025-03-18 | 13:47–13:57 | Mattermost `#code-review` — an exchange of 6 messages, opened by **dario** |
| 11 | 2025-03-19 | 11:29–11:44 | Mattermost `#engineering` — an exchange of 8 messages, opened by **konrad** |
| 12 | 2025-03-19 | 11:44–11:58 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 13 | 2025-03-19 | 13:42–13:55 | Mattermost `#engineering` — an exchange of 8 messages, opened by **konrad** |
| 14 | 2025-03-19 | 14:02–14:23 | Mattermost `#releases` — an exchange of 7 messages, opened by **konrad** |
| 15 | 2025-03-19 | 14:03–14:12 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 16 | 2025-03-19 | 14:03–14:14 | Mattermost `#code-review` — an exchange of 8 messages, opened by **konrad** |
| 17 | 2025-03-20 | 13:04–13:20 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **konrad** |
| 18 | 2025-03-20 | 13:35–13:48 | Mattermost `#engineering` — an exchange of 7 messages, opened by **konrad** |
| 19 | 2025-03-20 | 13:41–13:49 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 20 | 2025-03-21 | 14:02–14:11 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **nikolai** |
| 21 | 2025-03-21 | 15:22–15:38 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 22 | 2025-03-24 | 15:02–15:29 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **konrad** |
| 23 | 2025-03-24 | 15:11–15:27 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 24 | 2025-03-27 | 14:12–14:45 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 25 | 2025-04-03 | 13:38–13:53 | Mattermost `#viewer` — an exchange of 9 messages, opened by **dario** |
| 26 | 2025-04-03 | 15:31–15:42 | Mattermost `#cookbooks` — an exchange of 9 messages, opened by **nikolai** |
| 27 | 2025-04-07 | 13:41–13:56 | Mattermost `#general` — an exchange of 8 messages, opened by **konrad** |
| 28 | 2025-04-07 | 13:51–14:01 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **emil** |
| 29 | 2025-04-08 | 12:53–13:06 | Mattermost `#engineering` — an exchange of 8 messages, opened by **konrad** |
| 30 | 2025-04-08 | 14:42–14:54 | Mattermost `#pipeline` — an exchange of 10 messages, opened by **dermot** |
| 31 | 2025-04-09 | 09:17–09:23 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dario** |
| 32 | 2025-04-09 | 13:21–13:30 | Mattermost `#incidents` — an exchange of 8 messages, opened by **dermot** |
| 33 | 2025-04-10 | 11:40–11:51 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 34 | 2025-04-11 | 13:36–13:53 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dario** |
| 35 | 2025-04-11 | 13:42–13:52 | Mattermost `#incidents` — an exchange of 8 messages, opened by **gideon** |
| 36 | 2025-04-14 | 14:12–14:20 | Mattermost `#viewer` — an exchange of 7 messages, opened by **dermot** |
| 37 | 2025-04-16 | 13:50–14:04 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 38 | 2025-04-16 | 17:34–18:02 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **emil** |
| 39 | 2025-04-17 | 16:35–16:49 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 40 | 2025-04-18 | 15:07–15:19 | Mattermost `#incidents` — an exchange of 8 messages, opened by **nikolai** |
| 41 | 2025-04-21 | 13:15–13:22 | Mattermost `#help` — an exchange of 8 messages, opened by **gideon** |
| 42 | 2025-04-21 | 14:09–14:26 | Mattermost `#general` — an exchange of 7 messages, opened by **dermot** |
| 43 | 2025-04-24 | 14:07–14:18 | Mattermost `#releases` — an exchange of 7 messages, opened by **dermot** |
| 44 | 2025-04-29 | 15:04–15:13 | Mattermost `#general` — an exchange of 7 messages, opened by **dermot** |
| 45 | 2025-05-02 | 14:11–14:23 | Mattermost `#releases` — an exchange of 7 messages, opened by **dario** |
| 46 | 2025-05-13 | 15:36–15:44 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
