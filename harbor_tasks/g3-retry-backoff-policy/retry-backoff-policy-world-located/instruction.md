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

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 49 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 15:09–15:19 | Mattermost `#releases` — an exchange of 8 messages, opened by **konrad** |
| 2 | 2025-01-22 | 15:29–15:47 | Mattermost `#cookbooks` — an exchange of 9 messages, opened by **dermot** |
| 3 | 2025-02-06 | 14:01–14:15 | Mattermost `#code-review` — an exchange of 9 messages, opened by **nikolai** |
| 4 | 2025-03-12 | 14:26–14:41 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 5 | 2025-03-17 | 12:53–13:04 | Mattermost `#code-review` — an exchange of 7 messages, opened by **konrad** |
| 6 | 2025-03-17 | 14:02–14:12 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **petar** |
| 7 | 2025-03-19 | 13:02–13:13 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 8 | 2025-03-19 | 14:08–14:25 | Mattermost `#releases` — an exchange of 8 messages, opened by **konrad** |
| 9 | 2025-03-20 | 13:32–13:40 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dermot** |
| 10 | 2025-03-21 | 13:12–13:23 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 11 | 2025-03-21 | 13:36–13:48 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **nikolai** |
| 12 | 2025-03-24 | 14:02–14:17 | Mattermost `#releases` — an exchange of 6 messages, opened by **konrad** |
| 13 | 2025-03-24 | 15:12–15:27 | Mattermost `#cookbooks` — an exchange of 10 messages, opened by **nikolai** |
| 14 | 2025-03-25 | 10:55–11:14 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **nils** |
| 15 | 2025-03-27 | 14:22–14:41 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 16 | 2025-03-31 | 11:53–12:08 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 17 | 2025-03-31 | 16:08–16:21 | Mattermost `#releases` — an exchange of 8 messages, opened by **konrad** |
| 18 | 2025-04-02 | 13:52–14:06 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 19 | 2025-04-03 | 15:11–15:22 | Mattermost `#code-review` — an exchange of 9 messages, opened by **nikolai** |
| 20 | 2025-04-03 | 15:23–15:35 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **nikolai** |
| 21 | 2025-04-07 | 10:54–11:06 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |
| 22 | 2025-04-07 | 14:02–14:20 | Mattermost `#general` — an exchange of 10 messages, opened by **konrad** |
| 23 | 2025-04-08 | 17:14–17:31 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **dermot** |
| 24 | 2025-04-09 | 13:21–13:27 | Mattermost `#incidents` — an exchange of 9 messages, opened by **dermot** |
| 25 | 2025-04-09 | 14:38–14:54 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **dario** |
| 26 | 2025-04-10 | 11:40–11:57 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 27 | 2025-04-11 | 12:19–12:29 | Mattermost `#incidents` — an exchange of 8 messages, opened by **konrad** |
| 28 | 2025-04-11 | 13:41–13:52 | Mattermost `#releases` — an exchange of 9 messages, opened by **nikolai** |
| 29 | 2025-04-15 | 15:02–15:17 | Mattermost `#engineering` — an exchange of 7 messages, opened by **nikolai** |
| 30 | 2025-04-16 | 15:12–15:28 | Mattermost `#code-review` — an exchange of 7 messages, opened by **konrad** |
| 31 | 2025-04-18 | 15:11–15:22 | Mattermost `#incidents` — an exchange of 7 messages, opened by **nikolai** |
| 32 | 2025-04-21 | 14:12–14:29 | Mattermost `#general` — an exchange of 8 messages, opened by **dermot** |
| 33 | 2025-04-23 | 09:12–12:20 | mail thread “support: run on a revoked key retried all night” — an exchange of 4 messages from **gideon**. In `worldadmin@world.local`'s INBOX |
| 34 | 2025-04-24 | 14:02–14:11 | Mattermost `#code-review` — an exchange of 8 messages, opened by **emil** |
| 35 | 2025-04-24 | 14:12–14:23 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dario** |
| 36 | 2025-04-24 | 18:31–18:40 | Mattermost `#engineering` — an exchange of 7 messages, opened by **dario** |
| 37 | 2025-04-25 | 10:14–14:21 | the wiki page “Weekly Notes \u2014 Week of Mar 24” (`docs/meetings/weekly-notes-week-of-mar-24.md`) — an exchange of 22 **comments** opened by **dermot**, not the page body |
| 38 | 2025-04-29 | 14:22–14:40 | Mattermost `#general` — an exchange of 7 messages, opened by **dermot** |
| 39 | 2025-04-29 | 15:39–15:54 | Mattermost `#engineering` — an exchange of 8 messages, opened by **emil** |
| 40 | 2025-05-30 | 17:23–17:34 | Mattermost `#code-review` — an exchange of 8 messages, opened by **gideon** |
| 41 | 2025-06-02 | 10:12–10:39 | Mattermost `#general` — an exchange of 8 messages, opened by **dermot** |
| 42 | 2025-06-03 | 14:02–14:19 | Mattermost `#code-review` — an exchange of 9 messages, opened by **nikolai** |
| 43 | 2025-06-03 | 14:12–14:24 | Mattermost `#general` — an exchange of 9 messages, opened by **dermot** |
| 44 | 2025-06-03 | 14:12–14:24 | Mattermost `#incidents` — an exchange of 8 messages, opened by **dermot** |
| 45 | 2025-06-04 | 14:38–14:58 | Mattermost `#engineering` — an exchange of 9 messages, opened by **dermot** |
| 46 | 2025-06-11 | 09:12–16:20 | mail thread “smoke run timings on the wiki before we cut 0.1.26” — an exchange of 4 messages from **konrad**. In `worldadmin@world.local`'s INBOX |
| 47 | 2025-06-11 | 09:14–15:31 | mail thread “429 handling in the online request processor” — an exchange of 4 messages from **emil**. In `worldadmin@world.local`'s INBOX |
| 48 | 2025-06-18 | 14:06–14:24 | the wiki page “Weekly sync notes: week of Jun 9 (bulk LLM inference)” (`docs/meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md`) — an exchange of 9 **comments** opened by **dario**, not the page body |
| 49 | 2025-06-26 | 14:07–14:22 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
