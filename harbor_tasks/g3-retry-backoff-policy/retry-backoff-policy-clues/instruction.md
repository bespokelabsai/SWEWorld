You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Failure-class retry policy for online request processors**

Add a failure-class retry policy to the online request processors. Create `src/bespokelabs/curator/request_processor/online/retry_policy.py` — pure, standard-library only, importing nothing from `aiohttp`, `time` or `random` — defining `class FailureClass(str, enum.Enum)` with exactly `THROTTLE = "throttle"`, `TRANSIENT = "transient"`, `CONTRACT = "contract"`, `TERMINAL = "terminal"` in that declaration order, and `classify_failure(exc: BaseException) -> FailureClass`, which never raises and consults four signals in order, returning on the first that yields a class: (1) an HTTP status read from `getattr(exc, "status_code", None)` falling back to `getattr(exc, "status", None)`, used only when the value is an `int` that is either a key of the table (400/413/422 → CONTRACT, 401/403/404 → TERMINAL, 408/409/425 → TRANSIENT, 429/529 → THROTTLE) or in 500–599 (→ TRANSIENT), any other `int` falling through to the next signal; (2) the exception type, matched by `__name__` along `type(exc).__mro__` in MRO order (`TimeoutError`/`ConnectionError`/`ClientConnectorError` → TRANSIENT, `ValueError`/`ValidationError`/`JSONDecodeError`/`KeyError` → CONTRACT, `PermissionError`/`NotImplementedError` → TERMINAL); (3) case-insensitive substring markers over `str(exc)`, scanned in table order regardless of where they occur in the message (`rate limit`, `ratelimit`, `too many requests`, `overloaded`, `quota` → THROTTLE; `timed out`, `timeout`, `connection reset`, `temporarily unavailable`, `response is empty` → TRANSIENT; `invalid api key`, `authentication`, `permission denied` → TERMINAL); (4) the default, `TRANSIENT`. The same module defines `class RetryPolicy`, constructed with two injected callables `clock: Callable[[], float]` and `jitter: Callable[[], float]` (no defaults, neither called at construction), exposing `delay_for(failure_class, attempt_index) -> float`, which raises `ValueError` when `attempt_index < 1` and otherwise computes `raw = min(cap, base * factor ** (attempt_index - 1))` from the per-class schedule THROTTLE `(8.0, 2.0, 60.0)`, TRANSIENT `(0.5, 3.0, 20.0)`, CONTRACT and TERMINAL `(0.0, 1.0, 0.0)`, returns `0.0` when `raw <= 0`, and otherwise returns `round(raw * (0.5 + 0.5 * j), 3)` with `j` the injected jitter clamped to `[0.0, 1.0]` — so the cap binds before jitter and the jitter source is drawn exactly once per positive delay and not at all otherwise; a `decide(exc, *, attempts_made: int, attempts_left: int, ...)` method returning a frozen dataclass verdict that tells the caller whether to re-queue, which `FailureClass` it was, the 1-based index of the attempt that just failed, how long to wait before the retry, and a two-part reason code spelled `f"{failure_class.value}:{outcome}"` with `outcome` one of `retry`/`exhausted`/`abort` (`abort` for a TERMINAL verdict, `exhausted` when the budget could not pay for another attempt); and a method that records a verdict on an `OnlineStatusTracker`, incrementing exactly one counter per failure — `num_rate_limit_errors` for THROTTLE, `num_api_errors` for TRANSIENT and TERMINAL, `num_other_errors` for CONTRACT. Also `remaining_cooldown_seconds(tracker, now: float) -> float`, the seconds a caller must still wait before issuing more requests; `format_failure_summary(failure_log: Sequence[tuple[FailureClass, str]]) -> list[str]`, one `f"[{failure_class.value}] {message} (x{count})"` entry per distinct (class, message) pair, ordered by count descending with ties broken by first occurrence and `[]` for an empty log; and `format_attempt_label(attempts_made: int, max_retries: int) -> str` returning `f"attempt #{attempts_made + 1} of {max_retries + 1}"`. Wire it in: `APIRequest` gains `attempts_made: int = 0` and `failure_log: list = field(default_factory=list)` (`attempts_left` keeps its name and its seeding from `config.max_retries`); `BaseOnlineRequestProcessor.__init__` builds the policy; the `except Exception as e:` block (lines 526–563) delegates to it, appending `(failure class, str(e))` to `failure_log`, updating the request's counters from the verdict, re-queueing on a retry verdict and otherwise writing `GenericResponse(response_errors=format_failure_summary(request.failure_log), response_message=None, raw_response=None)`; `cool_down_if_rate_limit_error` is rewritten on top of `remaining_cooldown_seconds`; the retry-loop debug line at line 424 uses `format_attempt_label` so both log sites agree on the attempt number; and the hand-rolled rate-limit blocks in `openai_online_request_processor.py` (296–303), `anthropic_online_request_processor.py` (282–289) and `litellm_online_request_processor.py` (428–433) stop mutating tracker counters — delete the compensating `num_api_errors -= 1` / `num_other_errors -= 1` decrements and just re-raise — so every failure is classified and counted exactly once, in the base class.

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-02T19:39:32+00:00 -->

**2025-01-21 · #releases · dario**

> in any case i've settled on plain assignment for the horizon: `throttle_cooldown_until = now + delay_seconds` on every THROTTLE verdict, the most recent rate-limit failure is the one that sets the pause

**2025-01-22 · #cookbooks · konrad**

> Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there.

**2025-02-06 · #code-review · dario**

> settled in review: THROTTLE costs 0 attempts off the retry budget - a 429 says nothing about the request itself, so decide charges nothing and re-queues it.

**2025-03-12 · #engineering · konrad**

> right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do

**2025-03-17 · #pipeline · dermot**

> ordering is the problem, we check the budget before we deduct the cost, so a malformed-output failure with one attempt left still gets a retry it can't pay for

**2025-03-17 · #code-review · dario**

> @Konrad on 585 - i left config.seconds_to_pause_on_rate_limit exactly as it was, still 10 on the processor's config, the pause point just doesnt read it anymore

**2025-03-19 · #pipeline · nils**

> The verdict logged attempts_left as -1 again overnight. settled: a malformed-output failure that cant pay comes back contract:exhausted with attempts_left 0, never a negative.

**2025-03-19 · #releases · dario**

> honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out

**2025-03-20 · #cookbooks · konrad**

> Look, I said 429s never cost a request budget - that's out, a dead key looped for hours. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6 now, decide takes throttle_waivers_left and reports throttle_waivers_after.

**2025-03-21 · #pipeline · gideon**

> so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it.

**2025-03-21 · #cookbooks · konrad**

> Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again.

**2025-03-24 · #cookbooks · konrad**

> look, the last-THROTTLE-wins overwrite I flagged is gone, second 429 had a tiny backof and overwrote a 40s window down under a second. compares now: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`

**2025-03-24 · #releases · emil**

> honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock.

**2025-03-25 · #pipeline · emil**

> @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, the first 429's own delay reads 5.0 unrounded, so tracker.throttle_cooldown_until is 1005.0; a second worth 1.0 leaves it.

**2025-03-27 · #viewer · emil**

> honestly the check belongs after the deduction and only trips on strictly negative - a malformed-output failure at attempts_left 2 lands on 0 and still gets retried.

**2025-03-31 · #releases · dermot**

> yeah, for a schema failure the counter is the whole job — a CONTRACT verdict bumps num_other_errors by one and that's it, no stamps, no windows.

**2025-03-31 · #code-review · dario**

> @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week.

**2025-04-02 · #pipeline · dario**

> honestly i'd rather not put a new knob on OnlineRequestProcessorConfig for this, max_retries still seeds attempts_left and everything else stays on the request

**2025-04-03 · #code-review · konrad**

> Look, cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted.

**2025-04-03 · #cookbooks · konrad**

> look, every THROTTLE bumps num_rate_limit_errors by one on the way through — one 429, one increment, and that's the only counter it touches.

**2025-04-07 · #pipeline · dermot**

> on the retry side: remaining_cooldown_seconds(tracker, now) handed back -3.2 once the window was behind us, and 4.999999999998 before that — clamp at 0.0, round to three decimals.

**2025-04-07 · #general · nils**

> A tracker nobody has throttled answers 0.0 however far ahead you ask — with the window at 1005.0, remaining_cooldown_seconds(tracker, 1002.0) is 3.0, 0.5 at 1004.5, 0.0 at 1005.0.

**2025-04-08 · #pipeline · dario**

> dropped the plain `throttle_cooldown_until = now + delay_seconds` write — a 1.0s throttle landing behind a 40s one pulled the horizon in and we flooded again. it's `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` now, the window only moves out.

**2025-04-09 · #incidents · dario**

> that "throttle costs zero attempts" line i settled in review is gone — a permanently throttled key re-queued for hours. 429 is free while throttle_waivers_left > 0, then decide charges 1.

**2025-04-09 · #pipeline · gideon**

> so basically a timeout landed betwen two 429s and jumped our last-rate-limit stamp — a TRANSIENT only bumps num_api_errors, time_of_last_rate_limit_error is throttle-only.

**2025-04-10 · #pipeline · gideon**

> ya, bare 429s is exactly the shape that bites us. The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all.

**2025-04-11 · #incidents · gideon**

> so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh

**2025-04-11 · #releases · dario**

> mhm — and it sits as a plain module function in the retry policy, remaining_cooldown_seconds(tracker, now), not a method on the tracker, the pause point hands it both.

**2025-04-15 · #engineering · konrad**

> look, one shared counter for the run means the first bad minute eats everyones free passes, each request should walk in with its own full set.

**2025-04-16 · #code-review · dario**

> honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all

**2025-04-18 · #incidents · dario**

> and the non-throttle verdicts never touch num_rate_limit_errors, it only moves on a THROTTLE - so it just sits there through a whole run of schema misses and timeouts

**2025-04-21 · #general · nils**

> let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both.

**2025-04-23 · mail: support: run on a revoked key retried all night · emil**

> yup — once a request has used up its free passes the next 429 costs it an attempt like anything else, otherwise a dead key just loops forever.

**2025-04-24 · #engineering · dermot**

> yeah, on a bad key we empty the attempts and stop: `invalid api key` at seven left gives terminal:abort, attempts to zero, passes untouched at six.

**2025-04-24 · #code-review · emil**

> went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out.

**2025-04-24 · #engineering · gideon**

> while you're in there - it's throttle_waivers_left, not throttle_waviers_left like the branch has it, and it hangs off APIRequest, the tracker has no buisness knowing about it

**2025-04-25 · wiki: Weekly Notes \u2014 Week of Mar 24 · nikolai**

> on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request

**2025-04-29 · #engineering · dermot**

> we write attempts_left back from the verdict onto the request, but never the pass count, so a request quietly gets its full set again on the next failure.

**2025-04-29 · #general · nils**

> let me think — a TERMINAL verdict lands in num_api_errors, the same slot a TRANSIENT uses, one increment, and nothing else on the tracker moves for it.

**2025-05-30 · #code-review · konrad**

> look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff

**2025-06-02 · #general · nils**

> let me think - no, transients don't get their own exit: once the remaining budget can't cover even the one attempt, the verdict is transient:exhausted, same as the throttle path.

**2025-06-03 · #code-review · konrad**

> look, same request came back finish_reason length four times last night and spent four attempts on it - a broken payload shoudn't get that many goes.

**2025-06-03 · #general · nils**

> let me think - no, timeouts stay as they are: one attempt off the budget per failure, and throttle_waivers_left comes back exactly as it went in.

**2025-06-03 · #incidents · dario**

> that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request.

**2025-06-04 · #engineering · nikolai**

> decide only sees attempts_made and attempts_left so it cant tell whether a 429 is free the requests remaining passes has to go in as a third kwarg

**2025-06-11 · mail: smoke run timings on the wiki before we cut 0.1.26 · nikolai**

> ran it with the wrong key and each request retried five more times before giving up once auth is the problem the attempts on the clock are worth nothing

**2025-06-11 · mail: 429 handling in the online request processor · nikolai**

> A few user configs in the wild still set seconds_to_pause_on_rate_limit, so it stays in config.py with its default of 10 unchanged, even once nothing reads it.

**2025-06-18 · wiki: Weekly sync notes: week of Jun 9 (bulk LLM inference) · nikolai**

> tracker gains one new field for this and only one: throttle_cooldown_until, 0.0 on a fresh tracker, sitting right after time_of_last_rate_limit_error. nothing else added for the pause.

**2025-06-26 · #pipeline · emil**

> honestly two attempts off for a malformed-output failure sounds right to me, one is too generous. doesn't spend a throttle_waivers_left pass though, thats for 429s.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. The So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
