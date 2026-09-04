You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Failure-class retry policy for online request processors**

Add a failure-class retry policy to the online request processors.

### 1. New module — `src/bespokelabs/curator/request_processor/online/retry_policy.py`

Pure, standard-library only. It imports nothing from `aiohttp`, `time` or `random`.

```python
class FailureClass(str, enum.Enum):
    THROTTLE = "throttle"
    TRANSIENT = "transient"
    CONTRACT = "contract"
    TERMINAL = "terminal"
```

That declaration order matters.

#### `classify_failure(exc: BaseException) -> FailureClass`

Never raises. It consults four signals **in order**, returning on the first that yields a class.

**(1) HTTP status** — read from `getattr(exc, "status_code", None)`, falling back to
`getattr(exc, "status", None)`. Used only when the value is an `int` that is either a key of this
table or in 500–599 (→ TRANSIENT). Any other `int` falls through to the next signal.

| status | class |
|---|---|
| 400 / 413 / 422 | CONTRACT |
| 401 / 403 / 404 | TERMINAL |
| 408 / 409 / 425 | TRANSIENT |
| 429 / 529 | THROTTLE |
| 500–599 | TRANSIENT |

**(2) Exception type** — matched by `__name__` along `type(exc).__mro__`, in MRO order.

| type name | class |
|---|---|
| `TimeoutError`, `ConnectionError`, `ClientConnectorError` | TRANSIENT |
| `ValueError`, `ValidationError`, `JSONDecodeError`, `KeyError` | CONTRACT |
| `PermissionError`, `NotImplementedError` | TERMINAL |

**(3) Message markers** — case-insensitive substrings of `str(exc)`, scanned in table order
regardless of where in the message they occur.

| marker | class |
|---|---|
| `rate limit`, `ratelimit`, `too many requests`, `overloaded`, `quota` | THROTTLE |
| `timed out`, `timeout`, `connection reset`, `temporarily unavailable`, `response is empty` | TRANSIENT |
| `invalid api key`, `authentication`, `permission denied` | TERMINAL |

**(4) The default** — `TRANSIENT`.

#### `class RetryPolicy`

Constructed with two injected callables, `clock: Callable[[], float]` and
`jitter: Callable[[], float]`. Neither has a default and neither is called at construction.

**`delay_for(failure_class, attempt_index) -> float`** raises `ValueError` when
`attempt_index < 1`. Otherwise it computes `raw = min(cap, base * factor ** (attempt_index - 1))`
from the per-class schedule:

| class | base | factor | cap |
|---|---|---|---|
| THROTTLE | 8.0 | 2.0 | 60.0 |
| TRANSIENT | 0.5 | 3.0 | 20.0 |
| CONTRACT, TERMINAL | 0.0 | 1.0 | 0.0 |

It returns `0.0` when `raw <= 0`, and otherwise `round(raw * (0.5 + 0.5 * j), 3)` with `j` the
injected jitter clamped to `[0.0, 1.0]`. So the cap binds **before** jitter, and the jitter source
is drawn exactly once per positive delay and not at all otherwise.

**`decide(exc, *, attempts_made: int, attempts_left: int, ...)`** returns a frozen dataclass
verdict telling the caller: whether to re-queue, which `FailureClass` it was, the 1-based index of
the attempt that just failed, how long to wait before the retry, and a two-part reason code
spelled `f"{failure_class.value}:{outcome}"`. `outcome` is one of `retry` / `exhausted` / `abort`
— `abort` for a TERMINAL verdict, `exhausted` when the budget could not pay for another attempt.

**A method that records a verdict on an `OnlineStatusTracker`**, incrementing exactly one counter
per failure:

| class | counter |
|---|---|
| THROTTLE | `num_rate_limit_errors` |
| TRANSIENT, TERMINAL | `num_api_errors` |
| CONTRACT | `num_other_errors` |

#### Also in the module

- `remaining_cooldown_seconds(tracker, now: float) -> float` — the seconds a caller must still
  wait before issuing more requests.
- `format_failure_summary(failure_log: Sequence[tuple[FailureClass, str]]) -> list[str]` — one
  `f"[{failure_class.value}] {message} (x{count})"` entry per distinct (class, message) pair,
  ordered by count descending with ties broken by first occurrence, and `[]` for an empty log.
- `format_attempt_label(attempts_made: int, max_retries: int) -> str` — returns
  `f"attempt #{attempts_made + 1} of {max_retries + 1}"`.

### 2. Wire it in

`APIRequest` gains `attempts_made: int = 0` and `failure_log: list = field(default_factory=list)`.
`attempts_left` keeps its name and its seeding from `config.max_retries`.

`BaseOnlineRequestProcessor.__init__` builds the policy. The `except Exception as e:` block
(lines 526–563) delegates to it:

- append `(failure class, str(e))` to `failure_log`;
- update the request's counters from the verdict;
- re-queue on a retry verdict;
- otherwise write
  `GenericResponse(response_errors=format_failure_summary(request.failure_log), response_message=None, raw_response=None)`.

`cool_down_if_rate_limit_error` is rewritten on top of `remaining_cooldown_seconds`, and the
retry-loop debug line at line 424 uses `format_attempt_label` so both log sites agree on the
attempt number.

### 3. Stop double-counting in the provider processors

The hand-rolled rate-limit blocks in `openai_online_request_processor.py` (296–303),
`anthropic_online_request_processor.py` (282–289) and `litellm_online_request_processor.py`
(428–433) stop mutating tracker counters. Delete the compensating `num_api_errors -= 1` /
`num_other_errors -= 1` decrements and just re-raise — so every failure is classified and counted
exactly once, in the base class.

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: A failure is priced against the request's remaining attempt budget by class, and the price is not uniform: TRANSIENT costs 1 attempt, CONTRACT costs 2 attempts, and THROTTLE costs 0 attempts as long as the request still holds one of its rate-limit waivers. Each `APIRequest` carries its own waiver counter, a new field `throttle_waivers_left: int = DEFAULT_THROTTLE_WAIVERS` seeded from a module-level `DEFAULT_THROTTLE_WAIVERS: int = 6` exported by `retry_policy.py`; a THROTTLE failure with `throttle_waivers_left > 0` decrements the waiver instead of the budget, and once the waivers are gone a THROTTLE failure costs 1 like any transient. `decide` takes `throttle_waivers_left` as a third keyword argument alongside `attempts_made`/`attempts_left`, and its verdict reports both the post-failure budget and the post-failure waiver count, as the frozen fields `attempts_left_after` and `throttle_waivers_after`, which the caller writes back onto the request.
   - *scope*: The waiver allowance is per-request, not per-run and not per-model: a fresh `APIRequest` starts with six waivers regardless of how many 429s other in-flight requests have already absorbed, and nothing on `OnlineStatusTracker` or in `OnlineRequestProcessorConfig` holds or seeds the waiver count. `attempts_left` keeps its existing seeding from `config.max_retries`; only the amount deducted per failure changes.
   - *exclusions or crossover*: A TERMINAL verdict discards the rest of the budget rather than preserving it: the request's `attempts_left` is set to 0 even when several attempts remained, while its waiver count is passed through unchanged. Conversely a zero-cost THROTTLE failure at `attempts_left == 0` is still retried, because `0 - 0 >= 0` holds — an empty attempt budget does not by itself stop a rate-limited request while a waiver remains.
   - *failure behavior*: The cost is charged first and the exhaustion test is `attempts_left - cost < 0`, evaluated after pricing rather than as an `attempts_left <= 0` check before it. When it trips, the verdict is not-retry with outcome `exhausted`, a delay of `0.0` (the schedule is never consulted and the jitter source is never drawn for a verdict that will not be retried), and a post-failure budget clamped to `0` — never a negative number. A CONTRACT failure at `attempts_left == 1` therefore ends the request rather than getting one more try.
   - *observability*: `DEFAULT_THROTTLE_WAIVERS == 6` and a freshly constructed `APIRequest` has `throttle_waivers_left == 6`. With a healthy budget: a rate-limit failure at `attempts_left=3, throttle_waivers_left=6` leaves `attempts_left == 3` and `throttle_waivers_left == 5`; a rate-limit failure at `attempts_left=0, throttle_waivers_left=3` is still retried and leaves `throttle_waivers_left == 2`; the same at `throttle_waivers_left=0` is not retried, reason code `throttle:exhausted`, `attempts_left == 0`. `ValueError("finish_reason was length")` at `attempts_left=3` leaves `attempts_left == 1`; at `attempts_left=1` it is not retried with reason code `contract:exhausted` and `attempts_left == 0`, not `-1`. `Exception("invalid api key")` at `attempts_left=7, throttle_waivers_left=6` yields reason code `terminal:abort`, `attempts_left == 0` and `throttle_waivers_left == 6`.

2.
   - *rule*: The rate-limit pause is driven by an absolute horizon stored on the tracker, not by a config constant. `OnlineStatusTracker` gains exactly one new dataclass field, `throttle_cooldown_until: float = 0.0`, placed immediately after `time_of_last_rate_limit_error`. When a THROTTLE verdict is recorded on the tracker the policy reads its injected clock once for `now`, sets `time_of_last_rate_limit_error = now`, and advances the horizon monotonically: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, so a later short delay never pulls in a horizon an earlier longer delay already set. `remaining_cooldown_seconds(tracker, now)` returns `max(0.0, round(tracker.throttle_cooldown_until - now, 3))`.
   - *scope*: The horizon is run-level state on the tracker, extended only by THROTTLE verdicts. Recording a TRANSIENT, CONTRACT or TERMINAL verdict increments its counter and touches neither `throttle_cooldown_until` nor `time_of_last_rate_limit_error`, and does not call the injected clock at all — so the clock-call count over a mixed sequence of failures equals the number of rate-limit failures.
   - *exclusions or crossover*: `config.seconds_to_pause_on_rate_limit` is no longer read by any code path after this change: it stays in `config.py` as a dead knob for backwards compatibility, and the pause is never derived from it or from elapsed time since `time_of_last_rate_limit_error`. A run, model or request that has never been throttled waits zero seconds at the pause point even though the knob is still set to 10.
   - *observability*: With a clock pinned at `1000.0` and jitter `0.25`: after one rate-limit failure, `throttle_cooldown_until == 1005.0`, `time_of_last_rate_limit_error == 1000.0`, and the clock has been called once; a contract failure recorded next leaves both at `1005.0`/`1000.0` with the clock still called once; a second rate-limit failure whose delay is `1.0` at the same clock leaves `throttle_cooldown_until == 1005.0`, not `1001.0`. `remaining_cooldown_seconds(tracker, 1002.0) == 3.0`, `(tracker, 1004.5) == 0.5`, `(tracker, 1005.0) == 0.0`, `(tracker, 1099.0) == 0.0`. A freshly constructed `OnlineStatusTracker()` has `throttle_cooldown_until == 0.0`, so `remaining_cooldown_seconds(tracker, 12345.0) == 0.0`.

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

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
