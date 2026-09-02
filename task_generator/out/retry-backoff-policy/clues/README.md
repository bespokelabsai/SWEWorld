# Clues for g3 — Failure-class retry policy for online request processors

49 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Add a failure-class retry policy to the online request processors. Create `src/bespokelabs/curator/request_processor/online/retry_policy.py` — pure, standard-library only, importing nothing from `aiohttp`, `time` or `random` — defining `class FailureClass(str, enum.Enum)` with exactly `THROTTLE = "throttle"`, `TRANSIENT = "transient"`, `CONTRACT = "contract"`, `TERMINAL = "terminal"` in that declaration order, and `classify_failure(exc: BaseException) -> FailureClass`, which never raises and consults four signals in order, returning on the first that yields a class: (1) an HTTP status read from `getattr(exc, "status_code", None)` falling back to `getattr(exc, "status", None)`, used only when the value is an `int` that is either a key of the table (400/413/422 → CONTRACT, 401/403/404 → TERMINAL, 408/409/425 → TRANSIENT, 429/529 → THROTTLE) or in 500–599 (→ TRANSIENT), any other `int` falling through to the next signal; (2) the exception type, matched by `__name__` along `type(exc).__mro__` in MRO order (`TimeoutError`/`ConnectionError`/`ClientConnectorError` → TRANSIENT, `ValueError`/`ValidationError`/`JSONDecodeError`/`KeyError` → CONTRACT, `PermissionError`/`NotImplementedError` → TERMINAL); (3) case-insensitive substring markers over `str(exc)`, scanned in table order regardless of where they occur in the message (`rate limit`, `ratelimit`, `too many requests`, `overloaded`, `quota` → THROTTLE; `timed out`, `timeout`, `connection reset`, `temporarily unavailable`, `response is empty` → TRANSIENT; `invalid api key`, `authentication`, `permission denied` → TERMINAL); (4) the default, `TRANSIENT`. The same module defines `class RetryPolicy`, constructed with two injected callables `clock: Callable[[], float]` and `jitter: Callable[[], float]` (no defaults, neither called at construction), exposing `delay_for(failure_class, attempt_index) -> float`, which raises `ValueError` when `attempt_index < 1` and otherwise computes `raw = min(cap, base * factor ** (attempt_index - 1))` from the per-class schedule THROTTLE `(8.0, 2.0, 60.0)`, TRANSIENT `(0.5, 3.0, 20.0)`, CONTRACT and TERMINAL `(0.0, 1.0, 0.0)`, returns `0.0` when `raw <= 0`, and otherwise returns `round(raw * (0.5 + 0.5 * j), 3)` with `j` the injected jitter clamped to `[0.0, 1.0]` — so the cap binds before jitter and the jitter source is drawn exactly once per positive delay and not at all otherwise; a `decide(exc, *, attempts_made: int, attempts_left: int, ...)` method returning a frozen dataclass verdict that tells the caller whether to re-queue, which `FailureClass` it was, the 1-based index of the attempt that just failed, how long to wait before the retry, and a two-part reason code spelled `f"{failure_class.value}:{outcome}"` with `outcome` one of `retry`/`exhausted`/`abort` (`abort` for a TERMINAL verdict, `exhausted` when the budget could not pay for another attempt); and a method that records a verdict on an `OnlineStatusTracker`, incrementing exactly one counter per failure — `num_rate_limit_errors` for THROTTLE, `num_api_errors` for TRANSIENT and TERMINAL, `num_other_errors` for CONTRACT. Also `remaining_cooldown_seconds(tracker, now: float) -> float`, the seconds a caller must still wait before issuing more requests; `format_failure_summary(failure_log: Sequence[tuple[FailureClass, str]]) -> list[str]`, one `f"[{failure_class.value}] {message} (x{count})"` entry per distinct (class, message) pair, ordered by count descending with ties broken by first occurrence and `[]` for an empty log; and `format_attempt_label(attempts_made: int, max_retries: int) -> str` returning `f"attempt #{attempts_made + 1} of {max_retries + 1}"`. Wire it in: `APIRequest` gains `attempts_made: int = 0` and `failure_log: list = field(default_factory=list)` (`attempts_left` keeps its name and its seeding from `config.max_retries`); `BaseOnlineRequestProcessor.__init__` builds the policy; the `except Exception as e:` block (lines 526–563) delegates to it, appending `(failure class, str(e))` to `failure_log`, updating the request's counters from the verdict, re-queueing on a retry verdict and otherwise writing `GenericResponse(response_errors=format_failure_summary(request.failure_log), response_message=None, raw_response=None)`; `cool_down_if_rate_limit_error` is rewritten on top of `remaining_cooldown_seconds`; the retry-loop debug line at line 424 uses `format_attempt_label` so both log sites agree on the attempt number; and the hand-rolled rate-limit blocks in `openai_online_request_processor.py` (296–303), `anthropic_online_request_processor.py` (282–289) and `litellm_online_request_processor.py` (428–433) stop mutating tracker counters — delete the compensating `num_api_errors -= 1` / `num_other_errors -= 1` decrements and just re-raise — so every failure is classified and counted exactly once, in the base class.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #releases *(new)* | dario | in any case i've settled on plain assignment for the horizon: `throttle_cooldown_until = now + delay_seconds` on every THROTTLE verdict, the most recent rate-limit failure is the one that sets the pause | *herring* |
| 2025-01-22 | #cookbooks *(new)* | konrad | Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there. | *herring* |
| 2025-02-06 | #code-review *(new)* | dario | settled in review: THROTTLE costs 0 attempts off the retry budget - a 429 says nothing about the request itself, so decide charges nothing and re-queues it. | *herring* |
| 2025-03-12 | #engineering *(new)* | konrad | right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do | *herring* |
| 2025-03-17 | #pipeline *(new)* | dermot | ordering is the problem, we check the budget before we deduct the cost, so a malformed-output failure with one attempt left still gets a retry it can't pay for | `failure_behavior` |
| 2025-03-17 | #code-review | dario | @Konrad on 585 - i left config.seconds_to_pause_on_rate_limit exactly as it was, still 10 on the processor's config, the pause point just doesnt read it anymore | `exclusions_or_crossover` |
| 2025-03-19 | #pipeline *(new)* | nils | The verdict logged attempts_left as -1 again overnight. settled: a malformed-output failure that cant pay comes back contract:exhausted with attempts_left 0, never a negative. | `failure_behavior`, `observability` |
| 2025-03-19 | #releases *(new)* | dario | honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out | `rule` |
| 2025-03-20 | #cookbooks *(new)* | konrad | Look, I said 429s never cost a request budget - that's out, a dead key looped for hours. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6 now, decide takes throttle_waivers_left and reports throttle_waivers_after. | `rule`, `scope` |
| 2025-03-21 | #pipeline *(new)* | gideon | so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it. | `rule` |
| 2025-03-21 | #cookbooks *(new)* | konrad | Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again. | `rule` |
| 2025-03-24 | #releases *(new)* | emil | honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock. | `scope` |
| 2025-03-24 | #cookbooks *(new)* | konrad | look, the last-THROTTLE-wins overwrite I flagged is gone, second 429 had a tiny backof and overwrote a 40s window down under a second. compares now: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` | `rule` |
| 2025-03-25 | #pipeline | emil | @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, the first 429's own delay reads 5.0 unrounded, so tracker.throttle_cooldown_until is 1005.0; a second worth 1.0 leaves it. | `observability`, `rule` |
| 2025-03-27 | #viewer *(new)* | emil | honestly the check belongs after the deduction and only trips on strictly negative - a malformed-output failure at attempts_left 2 lands on 0 and still gets retried. | `failure_behavior` |
| 2025-03-31 | #releases *(new)* | dermot | yeah, for a schema failure the counter is the whole job — a CONTRACT verdict bumps num_api_errors by one and that's it, no stamps, no windows. | `scope` |
| 2025-03-31 | #code-review | dario | @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week. | `exclusions_or_crossover` |
| 2025-04-02 | #pipeline *(new)* | dario | honestly i'd rather not put a new knob on OnlineRequestProcessorConfig for this, max_retries still seeds attempts_left and everything else stays on the request | `scope` |
| 2025-04-03 | #code-review *(new)* | konrad | Look, cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted. | `observability`, `exclusions_or_crossover` |
| 2025-04-03 | #cookbooks *(new)* | konrad | look, every THROTTLE bumps num_rate_limit_errors by one on the way through — one 429, one increment, and that's the only counter it touches. | `scope` |
| 2025-04-07 | #pipeline | dermot | on the retry side: remaining_cooldown_seconds(tracker, now) handed back -3.2 once the window was behind us, and 4.999999999998 before that — clamp at 0.0, round to three decimals. | `rule`, `observability` |
| 2025-04-07 | #general *(new)* | nils | A tracker nobody has throttled answers 0.0 however far ahead you ask — with the window at 1005.0, remaining_cooldown_seconds(tracker, 1002.0) is 3.0, 0.5 at 1004.5, 0.0 at 1005.0. | `observability` |
| 2025-04-08 | #pipeline | dario | dropped the plain `throttle_cooldown_until = now + delay_seconds` write — a 1.0s throttle landing behind a 40s one pulled the horizon in and we flooded again. it's `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` now, the window only moves out. | `rule` |
| 2025-04-09 | #incidents *(new)* | dario | that "throttle costs zero attempts" line i settled in review is gone — a permanently throttled key re-queued for hours. 429 is free while throttle_waivers_left > 0, then decide charges 1. | `rule`, `failure_behavior` |
| 2025-04-09 | #pipeline | gideon | so basically a timeout landed betwen two 429s and jumped our last-rate-limit stamp — a TRANSIENT only bumps num_api_errors, time_of_last_rate_limit_error is throttle-only. | `scope` |
| 2025-04-10 | #pipeline | gideon | ya, bare 429s is exactly the shape that bites us. The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all. | `exclusions_or_crossover` |
| 2025-04-11 | #incidents *(new)* | gideon | so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh | `exclusions_or_crossover` |
| 2025-04-11 | #releases *(new)* | dario | mhm — and it sits as a plain module function in the retry policy, remaining_cooldown_seconds(tracker, now), not a method on the tracker, the pause point hands it both. | `rule` |
| 2025-04-15 | #engineering *(new)* | konrad | look, one shared counter for the run means the first bad minute eats everyones free passes, each request should walk in with its own full set. | `scope` |
| 2025-04-16 | #code-review *(new)* | dario | honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all | `failure_behavior` |
| 2025-04-18 | #incidents *(new)* | dario | and the non-throttle verdicts never touch num_rate_limit_errors, it only moves on a THROTTLE - so it just sits there through a whole run of schema misses and timeouts | `scope` |
| 2025-04-21 | #general *(new)* | nils | let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both. | `rule`, `scope` |
| 2025-04-23 | thread:new|g3.r1.l8 *(new)* | emil | yup — once a request has used up its free passes the next 429 costs it an attempt like anything else, otherwise a dead key just loops forever. | `rule` |
| 2025-04-24 | #engineering | gideon | while you're in there - it's throttle_waivers_left, not throttle_waviers_left like the branch has it, and it hangs off APIRequest, the tracker has no buisness knowing about it | `scope` |
| 2025-04-24 | #engineering *(new)* | dermot | yeah, on a bad key we empty the attempts and stop: `invalid api key` at seven left gives terminal:abort, attempts to zero, passes untouched at six. | `exclusions_or_crossover`, `observability` |
| 2025-04-24 | #code-review *(new)* | emil | went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out. | `failure_behavior` |
| 2025-04-25 | page:meetings/weekly-notes-week-of-mar-24.md | nikolai | on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request | `rule`, `observability` |
| 2025-04-29 | #engineering *(new)* | dermot | we write attempts_left back from the verdict onto the request, but never the pass count, so a request quietly gets its full set again on the next failure. | `rule`, `scope` |
| 2025-04-29 | #general *(new)* | nils | let me think — a TERMINAL verdict gets its own slot, num_other_errors, one increment, and nothing else on the tracker moves for it. | `scope` |
| 2025-05-30 | #code-review | konrad | look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff | `exclusions_or_crossover` |
| 2025-06-02 | #general *(new)* | nils | let me think - no, transients don't get their own exit: once the remaining budget can't cover even the one attempt, the verdict is transient:exhausted, same as the throttle path. | `failure_behavior` |
| 2025-06-03 | #code-review *(new)* | konrad | look, same request came back finish_reason length four times last night and spent four attempts on it - a broken payload shoudn't get that many goes. | `rule`, `observability` |
| 2025-06-03 | #general *(new)* | nils | let me think - no, timeouts stay as they are: one attempt off the budget per failure, and throttle_waivers_left comes back exactly as it went in. | `rule` |
| 2025-06-03 | #incidents *(new)* | dario | that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request. | `rule` |
| 2025-06-04 | #engineering *(new)* | nikolai | decide only sees attempts_made and attempts_left so it cant tell whether a 429 is free the requests remaining passes has to go in as a third kwarg | `rule` |
| 2025-06-11 | thread:new|g3.r1.l12 *(new)* | nikolai | ran it with the wrong key and each request retried five more times before giving up once auth is the problem the attempts on the clock are worth nothing | `exclusions_or_crossover` |
| 2025-06-11 | thread:new|g3.r2.s4d *(new)* | nikolai | A few user configs in the wild still set seconds_to_pause_on_rate_limit, so it stays in config.py with its default of 10 unchanged, even once nothing reads it. | `exclusions_or_crossover` |
| 2025-06-18 | page:meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md | nikolai | tracker gains one new field for this and only one: throttle_cooldown_until, 0.0 on a fresh tracker, sitting right after time_of_last_rate_limit_error. nothing else added for the pause. | `rule` |
| 2025-06-26 | #pipeline *(new)* | emil | honestly two attempts off for a malformed-output failure sounds right to me, one is too generous. doesn't spend a throttle_waivers_left pass though, thats for 429s. | `rule` |

## g3.r1

**The hidden requirement:**

- **rule** — A failure is priced against the request's remaining attempt budget by class, and the price is not uniform: TRANSIENT costs 1 attempt, CONTRACT costs 2 attempts, and THROTTLE costs 0 attempts as long as the request still holds one of its rate-limit waivers. Each `APIRequest` carries its own waiver counter, a new field `throttle_waivers_left: int = DEFAULT_THROTTLE_WAIVERS` seeded from a module-level `DEFAULT_THROTTLE_WAIVERS: int = 6` exported by `retry_policy.py`; a THROTTLE failure with `throttle_waivers_left > 0` decrements the waiver instead of the budget, and once the waivers are gone a THROTTLE failure costs 1 like any transient. `decide` takes `throttle_waivers_left` as a third keyword argument alongside `attempts_made`/`attempts_left`, and its verdict reports both the post-failure budget and the post-failure waiver count, as the frozen fields `attempts_left_after` and `throttle_waivers_after`, which the caller writes back onto the request.
- **scope** — The waiver allowance is per-request, not per-run and not per-model: a fresh `APIRequest` starts with six waivers regardless of how many 429s other in-flight requests have already absorbed, and nothing on `OnlineStatusTracker` or in `OnlineRequestProcessorConfig` holds or seeds the waiver count. `attempts_left` keeps its existing seeding from `config.max_retries`; only the amount deducted per failure changes.
- **exclusions_or_crossover** — A TERMINAL verdict discards the rest of the budget rather than preserving it: the request's `attempts_left` is set to 0 even when several attempts remained, while its waiver count is passed through unchanged. Conversely a zero-cost THROTTLE failure at `attempts_left == 0` is still retried, because `0 - 0 >= 0` holds — an empty attempt budget does not by itself stop a rate-limited request while a waiver remains.
- **failure_behavior** — The cost is charged first and the exhaustion test is `attempts_left - cost < 0`, evaluated after pricing rather than as an `attempts_left <= 0` check before it. When it trips, the verdict is not-retry with outcome `exhausted`, a delay of `0.0` (the schedule is never consulted and the jitter source is never drawn for a verdict that will not be retried), and a post-failure budget clamped to `0` — never a negative number. A CONTRACT failure at `attempts_left == 1` therefore ends the request rather than getting one more try.
- **observability** — `DEFAULT_THROTTLE_WAIVERS == 6` and a freshly constructed `APIRequest` has `throttle_waivers_left == 6`. With a healthy budget: a rate-limit failure at `attempts_left=3, throttle_waivers_left=6` leaves `attempts_left == 3` and `throttle_waivers_left == 5`; a rate-limit failure at `attempts_left=0, throttle_waivers_left=3` is still retried and leaves `throttle_waivers_left == 2`; the same at `throttle_waivers_left=0` is not retried, reason code `throttle:exhausted`, `attempts_left == 0`. `ValueError("finish_reason was length")` at `attempts_left=3` leaves `attempts_left == 1`; at `attempts_left=1` it is not retried with reason code `contract:exhausted` and `attempts_left == 0`, not `-1`. `Exception("invalid api key")` at `attempts_left=7, throttle_waivers_left=6` yields reason code `terminal:abort`, `attempts_left == 0` and `throttle_waivers_left == 6`.

**Reversed earlier:** Rate-limit failures were initially made free without any cap (no waiver counter at all, on the theory that a 429 says nothing about the request); that was reversed after a run with a permanently throttled key re-queued the same requests for hours, and the six-waiver allowance was introduced as the compromise.

**What a reader has to infer along the way:**

- *How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.*
  - nobody says: If one class is said to deserve more strikes than another and a third deserves none, the deduction is looked up per class instead of being a single fixed number.
- *Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.*
  - nobody says: A count that is defaulted per request and can run out is a second, separate counter living on the request rather than a shared or configured budget.
- *The policy is handed the request's ration alongside its attempt counters and hands back both post-failure numbers for the caller to store on the request; configuration gains nothing new.*
  - nobody says: Numbers the policy changes have to travel back on the verdict, because the only place they live is the request itself.
- *A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.*
  - nobody says: What stops a rate-limited request is running out of ration, not running out of attempts.
- *The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.*
  - nobody says: Testing after the deduction rather than before it is what makes a two-attempt charge fatal at one attempt left and a zero-cost charge survivable at none.

**Names the tests reach for that the ticket withholds:**

- said: `OnlineRequestProcessorConfig`, `The`, `finish_reason`, `throttle_waivers_left`

> **Spread:** g3.r1.sc1: two remarks in #general within 1 days; g3.r1.sc2: two remarks in #engineering within 9 days; g3.r1.sc5: two remarks in #pipeline within 2 days; g3.r1.sc5: two remarks in #code-review within 8 days

> **5 of 46 graded assertions are not stated outright** — 5 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g3.r1.sc1 — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Nobody says:* If one class is said to deserve more strikes than another and a third deserves none, the deduction is looked up per class instead of being a single fixed number.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g3.r1.say24` — failure_behavior

**nils**, 2025-06-02, #general

> let me think - no, transients don't get their own exit: once the remaining budget can't cover even the one attempt, the verdict is transient:exhausted, same as the throttle path.

*What a reader should take from it:* the team agrees a transient failure that the remaining budget cannot pay for ends the request with the exhausted outcome, the same as the throttle path

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* let me think - no, transients end the same way as the rest: once the budget can't cover the one attempt, the verdict is transient:exhausted rather than a retry.

*Why there:* Neither listed room is discussing retry semantics. On 03-19 "the throttle path" means the rate limiter's headroom calculation and whether the v0.1.21 token-count fix regressed it — an audit-and-ownership conversation, not a policy one; nobody there is talking about retry budgets or terminal verdicts, so a settled ruling on transient:exhausted would answer a question nobody asked and draw no reply. The 03-25 room is PR triage (584/585/579, deferrals, missing WS-047) and has no retry thread at all. The conversation that should exist is the one where the retry/backoff outcomes get specified, prompted by the postmortem action item on the rate limiter: someone asks the either-or (do transient failures get their own exit, or do they terminate like throttles?), Nils rules, and the neighbouring flooring and no-delay questions get settled in the same thread.

*Still leaves open:* doesn't say what number the budget reports on the way out, or that no wait is attached to it - those sit with the flooring and no-delay decisions

*Must appear literally:* `transient:exhausted`

*A new conversation in #general on 2025-06-02:*

```
10:12  dermot: quick one on the retry budget. if we run dry mid sequence on a transient, does that get its own exit or does it fold into an existing one
10:19  nils: let me think - no, transients dont get their own exit. it folds
10:23  dermot: ok but folds where. and what counts as running dry, budget under the next sleep or budget under the attempt
10:28  nils: once the remaining budget cant cover even the one attempt. thats the line. verdict is `transient:exhausted`
10:31  nikolai: thats the same string throttling gives you isnt it
10:34  nils: same as the throttle path yes, no second code for it
10:36  dermot: fine by me, one less branch on the caller side
10:39  nikolai: the attempts-left counter still prints as a float in the log fwiw
```

#### `g3.r1.l1` — rule, observability

**konrad**, 2025-06-03, #code-review

> look, same request came back finish_reason length four times last night and spent four attempts on it - a broken payload shoudn't get that many goes.

*What a reader should take from it:* the team agrees a contract failure should be charged more than one attempt

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* same request came back "finish_reason was length" four times tonight and spent four attempts doing it, a broken payload shouldn't get that many goes.

*Why there:* None of the five days has an open retry or attempt-cost discussion for this to contribute to. The closest, #code-review 2026-01-27, is about whether a null GEPA score should be caught at the integration layer or signalled upstream — a surfacing question, not a cost-per-attempt question — and it ends by punting to Dario, so a finish_reason/attempt-budget observation there would change the subject and draw no reply. The 2025 days (release tag for 0.1.26, importorskip and the verifier suite, PR 653/675 triage) and 2026-01-23 (Claude 4.x model identifiers in PR 704) have nothing adjacent. The remark presupposes a retry/backoff policy thread that these rooms never open; it needs the follow-on to the 2026-01-27 Dario handoff, where bulk-llm-inference retry behaviour is actually on the table and konrad arrives with overnight evidence.

*Still leaves open:* how many attempts a malformed-output failure should actually be charged, and what any other class costs

*Must appear literally:* `finish_reason`

*A new conversation in #code-review on 2025-06-03:*

```
14:02  nikolai: retry log from last night is odd, one request ate four attempts on its own
14:05  konrad: what was it failing on
14:07  nikolai: finish_reason length every time same request came back that way four times
14:09  emil: so truncated output, not a transport error? i believe we count those as retryable right now
14:11  konrad: mhm we do. look, a broken payload shoudn't get that many goes, thats four attempts spent on nothing
14:12  konrad: and length wont fix itself on a retry anyway, so it stops being retryable, fail it out on the first
14:14  nikolai: yep no argument here
14:16  emil: sounds right, whoever has the retry ticket open can fold it in
14:19  nikolai: log line should say which reason it was too they all read the same at the moment
```

#### `g3.r1.l3` — rule

**nils**, 2025-06-03, #general

> let me think - no, timeouts stay as they are: one attempt off the budget per failure, and throttle_waivers_left comes back exactly as it went in.

*What a reader should take from it:* the team agrees a transient failure keeps costing exactly one attempt

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* timeouts are fine the way they are, one attempt off the budget per failure, please don't get clever with that path.

*Why there:* no candidate location in range for this person

*Still leaves open:* what anything other than a timeout is charged

*Must appear literally:* `throttle_waivers_left`

*A new conversation in #general on 2025-06-03:*

```
14:12  dermot: on the retry policy - a timeout, does that pull from the waiver pool or is it just a plain failure
14:13  konrad: plain failure off the top of my head. one attempt off the budget, same as anything else
14:15  dermot: mhm. it's the waiver count i can't tell from the code. if a timeout nudges it the caller gets back less than it handed us
14:16  gideon: ya thats what bit the friday run i think
14:18  nils: let me think - no, timeouts stay as they are. konrad has it, one attempt off the budget per failure and nothing else moves
14:19  dermot: and throttle_waivers_left specifically
14:20  nils: comes back exactly as it went in. only a real 429 touches that one
14:22  konrad: right so the timeout path needs no change at all. the 429 side is still not written though
14:24  dermot: yeah ok. name still reads like it counts both kinds, someone will trip on that
```

#### `g3.r1.l4` — rule

**dario**, 2025-06-03, #incidents

> that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request.

*What a reader should take from it:* the team agrees a rate-limit failure should not come out of the request's attempt budget

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* burned the whole retry budget on 429s last night against a throttled key, and not one of those failures was about my request.

*Why there:* no candidate location in range for this person

*Still leaves open:* what a 429 should be charged against instead, and whether that is unlimited

*A new conversation in #incidents on 2025-06-03:*

```
14:12  dermot: retry counters from the late night bulk run are in. three hard failures, everything else just exhausted attempts
14:14  dario: mhm. that `attempt: 2` sitting next to RateLimitError bugs me honestly, it reads like my call failed twice on its own merits
14:15  gideon: what do you mean, it did retry twice though?
14:17  dario: it did, but i burned the whole retry budget on 429s last night against a throttled key. none of them were about my request actually
14:19  dermot: so the key was already over quota from other traffic and your request paid for it. not entirely sure the counter can even tell those apart today
14:21  dario: it cant, and that's the fix. key level 429s get their own count and their own wait, they dont eat the per request attempts
14:22  gideon: ya exactly, so basically attempt only moves when it was our own call that broke
14:24  dermot: yeah. the 23:00 batch sits on that same key by the way, if i had to guess that is what drained it
```

#### `g3.r1.l2` — rule

**emil**, 2025-06-26, #pipeline

> honestly two attempts off for a malformed-output failure sounds right to me, one is too generous. doesn't spend a throttle_waivers_left pass though, thats for 429s.

*What a reader should take from it:* the team agrees a contract failure deducts two attempts

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* two attempts off for a malformed-output failure feels right to me, one is too generous and binning it on the spot is too harsh.

*Why there:* Every listed room is on another subject entirely — streaming/batch routing and cache behaviour (pipeline 6/26), None-cost rendering and version tags (viewer), the Pydantic fix (engineering 6/13), PR readiness triage (both code-review days). Nobody in any of them has raised retries, attempt budgets, 429s, or malformed output, so this remark would answer a question no one asked and draw no reply. It needs the thread where the retry policy's per-class costs were actually being argued: dermot restating his guess at the attempt accounting, emil settling the malformed-output case while explicitly keeping throttle_waivers_left out of it, and someone else covering the remaining classes.

*Still leaves open:* what the other classes cost, and whether anything is ever charged nothing

*Must appear literally:* `throttle_waivers_left`

*A new conversation in #pipeline on 2025-06-26:*

```
14:07  dario: back to the retry budget thing - when a response comes back malformed, how much of the budget should that actually cost? one attempt or two
14:09  gideon: i assumed one, same as any other failure tbh
14:13  emil: let me think through that. honestly two attempts off for a malformed-output failure sounds right to me, one is too generous when the model can just keep handing back the same garbage. the code today only decrements by one, nobody's changed it yet
14:16  dario: mhm, that tracks
14:17  dario: does it also burn a throttle_waivers_left pass, or is that pool separate
14:20  emil: separate. it doesn't spend a throttle_waivers_left pass, thats for 429s
14:22  gideon: ah ok, so basically the waiver pool stays untouched. that was the part i had backwards
```

### g3.r1.sc2 — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*Nobody says:* A count that is defaulted per request and can run out is a second, separate counter living on the request rather than a shared or configured budget.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g3.r1.l7` — scope

**konrad**, 2025-04-15, #engineering

> look, one shared counter for the run means the first bad minute eats everyones free passes, each request should walk in with its own full set.

*What a reader should take from it:* the team agrees a fresh request's allowance is unaffected by what other in-flight requests have absorbed

*Step it builds toward:* `g3.r1.sc2` — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*Drafted as:* one shared counter for the run means the first bad minute eats everyone's free passes, each request should walk in with its own full set.

*Why there:* None of the eight rooms is chewing on retry allowance at all. The closest touches are dario's one-line "retry/resume paths are unaffected" in #releases 2025-03-31 (a release sign-off, where opening a design argument about counter scope would change the subject and get no reply) and dermot's semaphore/concurrency thread in #engineering 2025-03-14 (concurrency, but about row-creation OOM, not per-request retry budgets — and that day already closed on verification ownership). The other six are PR-triage and wiki-ownership days. This remark only lands where someone has just proposed a run-level retry counter and konrad is pushing back; nothing on the board sets that up, and the sibling remark (count, field name, what spends a pass) needs the same room to exist. The natural prompt is the 2025-04-11 post1 fix to failed-requests jsonl handling — once you are writing out which requests gave up, someone asks how many attempts each one got, and whether the run shares a pool.

*Still leaves open:* how many that is, what the field is called, and what spends a pass

*A new conversation in #engineering on 2025-04-15:*

```
15:02  nikolai: retries gave up way too fast on the reruns yesterday is that budget per run or per call
15:05  konrad: per run, mhm. one counter shared by the whole thing off the top of my head
15:07  dermot: that would explain the tail then. first minute is bad and its spent before the rest even start
15:09  nikolai: so the first bad minute eats everyones free passes and the late requests walk in with nothing
15:12  konrad: right. look, each request should walk in with its own full set, the counter belongs on the request not the run
15:14  dermot: yep. no shared pool at all then
15:17  nikolai: i'd say thats also the 3 attempts vs 30 gap in tuesdays logs
```

#### `g3.r1.l8` — rule

**emil**, 2025-04-23, thread:new|g3.r1.l8

> yup — once a request has used up its free passes the next 429 costs it an attempt like anything else, otherwise a dead key just loops forever.

*What a reader should take from it:* the team agrees a rate-limit failure with no allowance left deducts one attempt

*Step it builds toward:* `g3.r1.sc2` — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*Drafted as:* once a request has used up its free passes the next 429 should cost it an attempt like anything else, otherwise a dead key loops forever.

*Why there:* None of the eight threads is chewing on retry accounting. Six are release announcements or a PR-status roundup; the other two are about caller-supplied docker images and about which files follow CURATOR_CACHE_DIR on resume. The nearest neighbour is the WS-050 batch-mode failure sweep in the Apr 14 weekly, but that thread is emil enumerating PRs needing review, and a settled decision about what a 429 deducts from an online request's attempt budget would land there with nothing above it and nothing after it. The conversation that should have existed is a short mail thread off a support report: a user's key had been revoked, every call came back 429, and the run span all night without ever exhausting max_retries because rate-limit responses were being treated as free retries unconditionally. Nikolai or gideon opens it with the log; the sibling remark — how many free passes a request gets, where that counter lives on the request object, and that a 429 is free while allowance remains — comes from whoever owns the online processor, and emil signs off on the other half: once the allowance is gone, a 429 is a normal failure and costs an attempt. That thread would also have to settle whether the counter survives a resume, which is why dario belongs on it.

*Still leaves open:* how many passes there are, where they are kept, and what a 429 costs while they last

*A new thread — **support: run on a revoked key retried all night**, 2025-04-23:*

```
From: gideon  To: emil, nikolai, dario
Hey, forwarding something from support before it gets lost in the queue. A user had their API key revoked partway through a run (org admin rotated it, they didn't know) and the run just... kept going. All night. Every single call came back 429, nothing ever got through, and the process was still alive when they checked in the morning with a log file that was like 400MB.

So basically they expected it to die after a while and it never did. They're not angry, they just want to know what the intend

From: dario  To: gideon, emil, nikolai
i think that's the request processor retry path, so probably emil or nikolai. but the part i want to understand before we touch anything: is this a classification problem where we're mislabelling a revoked key as a rate limit, or is it a counting problem where the retry loop is fine with 429s in principle and just never stops?

because those are actually two different fixes and to be honest i'd rather not do both at once. gideon can you get the actual response bodies from the ticket, not just th

From: emil  To: dario, gideon, nikolai
let me think through that, because i believe it's the second one and the classification is mostly a red herring.

the provider is returning 429 and honestly from our side that's a legitimate 429 — the key doesn't have quota anymore because the key doesn't exist. i'm not entirely sure we could tell those apart reliably even if we wanted to, different providers dress up revocation differently and some of them do genuinely just say too many requests.

the actual problem is upstream of that. when we

From: nikolai  To: emil, dario, gideon
right that matches what i remember of that code

the backoff sleep is also unbounded on the same path fwiw so overnight it was probably mostly sleeping which is why nobody noticed the machine was busy. separate thing, not blocking

gideon send me the log too if the user still has it

```

#### `g3.r1.l6` — scope

**gideon**, 2025-04-24, #engineering

> while you're in there - it's throttle_waivers_left, not throttle_waviers_left like the branch has it, and it hangs off APIRequest, the tracker has no buisness knowing about it

*What a reader should take from it:* the team agrees the count lives on the request object and not on the status tracker

*Step it builds toward:* `g3.r1.sc2` — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*Drafted as:* It's throttle_waivers_left, not throttle_waviers_left, and it hangs off APIRequest; the tracker has no business knowing about it.

*Why there:* That day is entirely about the batch status tracker: gideon asks for eyes on tracker behavior before EOD, then at 18:22-18:23 narrows it to state transitions after the pbar update, and emil closes with "I'll take a look at the state transitions." A note from gideon scoping what the tracker should and shouldn't hold — the waiver count belongs on APIRequest, not the tracker — lands as the last thing he hands Emil before Emil opens the code. It's his review, his file, his voice, and nobody in the room has staked out where that field lives. It deliberately doesn't say what the count counts down or what spends it, which is left for the throttle-path discussion elsewhere.

*Still leaves open:* what the field counts down and what spends it

*Must appear literally:* `throttle_waivers_left`, `APIRequest`

*Goes into the real conversation in #engineering on 2025-04-24, after 18:29 emil:*

```
09:00  gideon: - *PR 632* merged, batch update freq fix is in
- pbar changes done, CLI test display looking clean
- want to get eyes on the batch status tracker beha
09:07  gideon: has anyone opened the Weekly Notes for this week yet?
09:07  gideon: I haven't pulled it up
09:48  gideon: ok
09:48  gideon: answering my own question, pulled it up
09:48  gideon: PR 468 is flagged as stalled at ~75 days, is anyone actively on that or does it need to get reassigned?
17:29  gideon: welp
17:30  gideon: leaving the PR 468 thing for tomorrow I guess
18:13  emil: On the batch status tracker, what specifically do you want eyes on, the state transitions or the frequency behavior?
18:22  gideon: both, honestly, the Weekly Notes, Week of Apr 21 has context on where PR 632 landed if that helps orient you
18:23  gideon: mainly want to know the state transitions look right after the pbar update, and that the CLI test display is reading clean
18:23  gideon: the weekly notes flag PR 468 as stalled ~75 days and nobody's answered who owns it
18:23  gideon: is that one getting reassigned or is someone quietly working it?
18:29  emil: gotcha
18:29  emil: I'll take a look at the state transitions   <-- THE REMARK GOES HERE
```

#### `g3.r1.l5` — rule, observability

**nikolai**, 2025-04-25, page:meetings/weekly-notes-week-of-mar-24.md

> on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request

*What a reader should take from it:* the team agrees each request starts with six, from a module-level default in the retry policy file

*Step it builds toward:* `g3.r1.sc2` — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*Drafted as:* wiki bullet, still moving so don't link it: retry_policy.py holds the schedule, DEFAULT_THROTTLE_WAIVERS = 6, and the per-request field it seeds, throttle_waivers_left.

*Why there:* Konrad's page lists "PR 585, retry/batch, still in progress" with no detail, and the same notes flag 207/233 (rate limits) as needing an approach decision before anyone codes. Nikolai is already the one commenting on this page and is the one who'd know where the retry state actually landed in the code; the "still moving, dont link it" framing matches a bullet that is in flight rather than shipped. Nothing on the page states the default or the per-request field, so it isn't redundant, and it leaves what a waiver is spent on untouched.

*Still leaves open:* what a waiver is actually spent on and when one is used up

*Must appear literally:* `retry_policy.py`, `DEFAULT_THROTTLE_WAIVERS`, `throttle_waivers_left`

*Goes as a comment on the real page `meetings/weekly-notes-week-of-mar-24.md`, at: - PR 585, retry/batch, still in progress:*

```
# Weekly Notes, Week of Mar 24

## In Flight

- PR 468, n_samples in generation params, still open, think its waiting on issue 52 to settle before we merge
- PR 565, openai client backend, active review
- PR 579, openai/deepseek api, overlaps with 565 a bit, need to check with whoever owns that whether they should move together or stay independent
- PR 583, disable metadata db param, pretty straightforward, should be close
- PR 585, retry/batch, still in progress
- PR 590, logger propagate fix, small but worth getting in

WS-047 (Release Engineering, CI & Test Suite) ongoing with Nils. We did a pass earlier this week, still some open items on the test suite side.

## Open Questions

Things still unresolved as of today:

- issue 52, multiple samples per request. Blocks PR 468. No clear owner right now, need to decide the API shape before anything merges.
- issue 102, dict return without Pydantic. Not sure where this landed, I dont think anyone picked it up yet.
- issue 105, distribution graph skew in data viewer. Curator-viewer side, I'd point whoever looks at this toward issue 128 as well (related, see below).
- issue 121, pydantic to dict handling. Probably connected to 102, shoul
```

### g3.r1.sc3 — The policy is handed the request's ration alongside its attempt counters and hands back both post-failure numbers for the caller to store on the request; configuration gains nothing new.

*Nobody says:* Numbers the policy changes have to travel back on the verdict, because the only place they live is the request itself.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g3.r1.l11` — scope

**dario**, 2025-04-02, #pipeline

> honestly i'd rather not put a new knob on OnlineRequestProcessorConfig for this, max_retries still seeds attempts_left and everything else stays on the request

*What a reader should take from it:* the team agrees the allowance is not configurable and attempts_left keeps its existing seeding

*Step it builds toward:* `g3.r1.sc3` — The policy is handed the request's ration alongside its attempt counters and hands back both post-failure numbers for the caller to store on the request; configuration gains nothing new.

*Drafted as:* no new knob on OnlineRequestProcessorConfig for this please, max_retries still seeds attempts_left and everything else stays on the request.

*Why there:* The remark is a ruling in a live design argument — somebody has just proposed making the retry allowance configurable, and dario is closing that door while confirming attempts_left keeps its current seeding. None of the listed rooms has that proposal on the table. #help 2025-03-27 is the closest thematically (dario: "404 path is just unhandled on my end"), but that day is about executor image pinning and whether providers even return 404; nobody has gotten as far as a retry policy, let alone a knob on OnlineRequestProcessorConfig, so the remark would answer a question no one asked and draw no reply. #releases 2025-03-31 only touches retries in passing ("retry/resume paths are unaffected"), and 04-09/04-17/04-23/04-28/05-05 are provider changes, structured output, cache fingerprints, serving infra scope and cookbook response objects respectively. What's missing is the thread where the unhandled-404 finding turns into an actual policy: how many attempts a request gets, where the counter lives, and whether users can turn that dial.

*Still leaves open:* what the everything else is and how much each failure takes off attempts_left

*Must appear literally:* `OnlineRequestProcessorConfig`, `max_retries`, `attempts_left`

*A new conversation in #pipeline on 2025-04-02:*

```
13:52  gideon: for the retry counting, does the per request state hang off OnlineRequestProcessorConfig or somewhere else? i dunno what we landed on
13:54  dario: honestly i'd rather not put a new knob on that config for this one
13:55  gideon: then what seeds the count
13:57  dario: max_retries. it stays and it still seeds attempts_left, thats unchanged
14:00  dermot: so config hands you the initial number only, and the rest of it rides on the request?
14:02  dario: mhm. everythign else stays on the request, attempts_left included
14:04  dermot: yeah ok. not entirely sure whos picking it up, probably falls out of the 615 work
14:06  gideon: the sleep calc already reads off the request anyway so its less churn than i thought tbh
```

#### `g3.r1.l10` — rule, scope

**dermot**, 2025-04-29, #engineering

> we write attempts_left back from the verdict onto the request, but never the pass count, so a request quietly gets its full set again on the next failure.

*What a reader should take from it:* the team agrees the verdict carries the post-failure allowance and the caller writes it back onto the request

*Step it builds toward:* `g3.r1.sc3` — The policy is handed the request's ration alongside its attempt counters and hands back both post-failure numbers for the caller to store on the request; configuration gains nothing new.

*Drafted as:* we write attempts_left back from the verdict but never the pass count, so a request quietly gets its full set again on the next failure.

*Why there:* None of the eight rooms is chewing on retry accounting. The nearest neighbours are about something else: 04-24 is cache-write failures swallowed by a bare `pass`, 04-02 is cancellation and per-backend job id scoping, 04-16 is resume locking the model to an old batch id, 03-19 is token counts feeding the throttle. A retry verdict object carrying attempts_left, and the caller writing that allowance back onto the request, is a subsystem nobody in those threads mentions once — dropping it into the cache-write thread would change the subject and draw no reply, the most visible kind of plant. It also presumes a settled shape ("the verdict carries the post-failure allowance") that has to have been argued somewhere first, and the sibling remark about the pass-count field and where it's seeded from needs a room to live in too. That room is a retry/backoff policy thread that doesn't exist yet: dermot comes in off a long run where a handful of requests kept climbing past their ceiling, walks the write-back path, and finds only half of it gets persisted.

*Still leaves open:* what the verdict field for the new pass count is meant to be and where the count is seeded from

*Must appear literally:* `attempts_left`

*A new conversation in #engineering on 2025-04-29:*

```
15:39  emil: the retry counts from yesterdays run - same request came back with 3 attempts twice, not entirely sure how that happens
15:41  dermot: youre looking at attempts_left on the request row i take it
15:42  emil: yeah. verdict said 2 left, request showed 3 the next time round
15:45  dermot: we do copy attempts_left off the verdict back onto the request when we persist. what we never write back is the pass count
15:46  emil: ok but if the count itself lands right why does it go back up
15:49  dermot: pass number is what the reset keys off, and it comes back as whatever it started as. so the next failure reads as a first failure and the request quietly gets the full set again. both fields want to come off the verdict, not just the one
15:52  dario: that tracks. i can pick it up if nobodys sitting in that file - same spot where we merge the verdict?
15:54  dermot: same spot yeah. the fixture we exercise it with only ever has one pass in it though, so it wont show you anything
```

#### `g3.r1.l9` — rule

**nikolai**, 2025-06-04, #engineering

> decide only sees attempts_made and attempts_left so it cant tell whether a 429 is free the requests remaining passes has to go in as a third kwarg

*What a reader should take from it:* the team agrees decide takes the request's allowance as a third keyword argument

*Step it builds toward:* `g3.r1.sc3` — The policy is handed the request's ration alongside its attempt counters and hands back both post-failure numbers for the caller to store on the request; configuration gains nothing new.

*Drafted as:* decide only gets attempts_made and attempts_left, so it can't tell whether this 429 is free or not, it needs the request's remaining passes passed in too.

*Why there:* Nothing in the eight rooms is chewing on retry accounting. The two technical-design days are the closest and still wrong: 2025-04-18 is cache fingerprints and provider keying end to end, and 2025-05-21 is the agent response shape (plain dict vs wrapped), a thread that closes with nikolai adopting plain dict — a decide() signature arrives there from nowhere. The remaining six are PR-queue standups, release notes, sandbox tag pinning, and wind-down triage. The remark also presumes the room already accepts that some 429s are "free" and don't spend an attempt; no listed conversation establishes that, so it has to be said where it was established. It needs the day the retry policy was actually being written, with dario present — he owns the request path and would have authored decide(attempts_made, attempts_left), and the sibling remark about what the policy returns is his to make.

*Still leaves open:* what the policy hands back after it has priced the failure

*Must appear literally:* `decide`, `attempts_made`, `attempts_left`

*A new conversation in #engineering on 2025-06-04:*

```
14:38  dermot: the 429 on tuesdays run - decide treated it like any other failure. should it have
14:41  nikolai: depends whether it was a free one cant tell from in there though
14:43  dermot: what does it actually get handed
14:45  nikolai: attempts_made and attempts_left thats the lot
14:47  dermot: mhm so the 429 is already folded into both counts. nothing left to back it out with
14:50  konrad: so where would the free / not free come from then
14:52  nikolai: the requests remaining passes it goes in as a third kwarg
14:55  konrad: right, every policy signature moves. anyway thats fine
14:58  dermot: yeah. the fixed ceiling one wont ever read it, it only counts
```

### g3.r1.sc4 — A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.

*Nobody says:* What stops a rate-limited request is running out of ration, not running out of attempts.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g3.r1.l15` — observability, exclusions_or_crossover

**konrad**, 2025-04-03, #code-review

> Look, cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted.

*What a reader should take from it:* the team agrees a rate-limit failure with allowance left is retried at zero attempts and is only exhausted once the allowance is gone

*Step it builds toward:* `g3.r1.sc4` — A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.

*Drafted as:* cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted.

*Why there:* No listed room has a retry budget or per-class waivers in play. 2025-03-19 #engineering is the nearest neighbour but it is about whether the throttle check gets run and who owns closing the postmortem action item — Konrad's role there is to make a scheduling call, not to specify classifier semantics, and attempts_left/throttle_waivers_left/throttle:exhausted would be three tokens arriving from nowhere. 2025-04-01 #code-review explicitly sets retry aside ("Not the retry logic, that part landed fine"). What is missing is the review of the retry/backoff policy PR itself, the concrete follow-on to the postmortem finding that the rate limiter miscalculated headroom on kluster.ai DeepSeek runs — Konrad pinning test cases before sign-off, with the other failure classes at an empty budget being settled by others in the same thread.

*Still leaves open:* what any other class does at an empty budget

*Must appear literally:* `attempts_left`, `throttle_waivers_left`, `throttle:exhausted`

*A new conversation in #code-review on 2025-04-03:*

```
15:11  nikolai: the throttle retry cases in 565 arent pinned anywhere that i can see
15:12  nikolai: what happens on a 429 when attempts_left is already 0
15:14  konrad: it still re-queues, presuming there are waivers. 429 at attempts_left=0 with throttle_waivers_left=3 goes back on the queue, thats the case i want pinned
15:15  gideon: and the waiver count after that? stays at 3 or
15:16  konrad: comes back 2. it spends one
15:17  gideon: ya ok so basically the 429 path is the only thing eating them
15:18  nikolai: and with the pool empty
15:19  konrad: no requeue then, its terminal and the reason is throttle:exhausted. so at 0 thats what we tag
15:22  dario: mhm that tracks. is the 3 per provider or just the default we ship, i dont remember off hand
```

#### `g3.r1.l14` — exclusions_or_crossover

**gideon**, 2025-04-10, #pipeline

> ya, bare 429s is exactly the shape that bites us. The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all.

*What a reader should take from it:* the team agrees an empty attempt budget alone must not stop a rate-limited request

*Step it builds toward:* `g3.r1.sc4` — A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.

*Drafted as:* The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all.

*Why there:* Gideon opened that day with "odd rate limit behavior from DeepSeek that I want to get eyes on", spent the morning asking whether DeepSeek even sends retry-after or x-ratelimit headers, and Emil just confirmed at 11:38 that it's mostly bare 429s. The obvious next beat from Gideon is why the bare 429 matters: the retry budget is being spent on throttles that cost nothing. Nobody there has said this yet, and it deliberately leaves open what should happen to the request instead and how long it may keep going.

*Still leaves open:* what should happen to that request instead, and how long it can keep going

*Must appear literally:* `The`, `attempts_left`

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

#### `g3.r1.l13` — exclusions_or_crossover, observability

**dermot**, 2025-04-24, #engineering

> yeah, on a bad key we empty the attempts and stop: `invalid api key` at seven left gives terminal:abort, attempts to zero, passes untouched at six.

*What a reader should take from it:* the team agrees a terminal verdict zeroes the attempt budget and leaves the allowance unchanged

*Step it builds toward:* `g3.r1.sc4` — A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.

*Drafted as:* on a bad key, empty the attempts and stop: "invalid api key" at seven left should give terminal:abort, zero left, passes untouched at six.

*Why there:* None of the eight rooms is chewing on retry semantics. The remark presupposes a live design discussion with an established vocabulary — a verdict enum with `terminal:abort`, an attempt budget, and a separate pass allowance — and it states a settled decision about what a terminal verdict does to each of those counters. Nothing in these threads has that vocabulary in it. The closest topical neighbours all miss: #code-review 2025-03-27 does touch api keys, but it is about where `_build_client` picks credentials up from and about which PR number belongs to whom, not about what the retry layer does when the key turns out to be bad; Konrad's open question there is "is there any fallback besides the env var", which this does not answer. #general 2025-04-29 has an abort-vs-fall-back argument, but it is about a stored job that can't be reused in the caching path, and Emil has already landed hard on "aborting is not a fix" — dropping a remark that endorses a terminal abort into that thread would read as contradicting the room rather than joining it. #engineering 2025-03-19 is adjacent (rate limiter headroom, throttle path) but that is backpressure and cost accounting, not error classification. Dropped anywhere here, the remark changes the subject, uses two identifiers nobody else in the room has said, and would draw no reply. What should have existed is the conversation where the retry-backoff policy gets specified: a run that burned its whole attempt budget re-sending a request with bad credentials, which forces the team to separate errors worth retrying from errors that are settled, and then to say precisely what a settled verdict does to the two budgets. Dermot owns the bulk-llm-inference credential path (his PR from 03-27), so the invalid-key case is his to rule on; Nikolai and Emil are the ones who'd push on the leftover case — a request holding passes with no attempts left — which is the sibling remark and stays open in that thread.

*Still leaves open:* what happens to a request that still has passes but no attempts

*Must appear literally:* `invalid api key`, `terminal:abort`

*A new conversation in #engineering on 2025-04-24:*

```
14:12  dario: quick one on the retry policy — when the provider rejects the key, do we drain the attempts counter or leave whatever is left sitting on it
14:13  dario: run this morning came in with seven left and i cant tell from the code which one happens
14:15  dermot: `invalid api key` classifies as terminal:abort. theres nothing to retry into so we stop there
14:16  dario: right but abort as in stop, or abort as in stop and rewrite the counters on the way out
14:18  dermot: the latter. we empty the attempts, so your seven lands at zero. passes we dont touch, still six
14:19  dario: mhm. thats not in the policy file yet though is it, i went looking
14:20  dermot: not yet, no. small enough that it can ride along with the backoff ticket whenever someone gets to it
14:23  emil: hm. does a plain 401 with no key text land in the same bucket, or is that its own thing
```

#### `g3.r1.l12` — exclusions_or_crossover

**nikolai**, 2025-06-11, thread:new|g3.r1.l12

> ran it with the wrong key and each request retried five more times before giving up once auth is the problem the attempts on the clock are worth nothing

*What a reader should take from it:* the team agrees a terminal failure should not keep the remaining attempt budget alive

*Step it builds toward:* `g3.r1.sc4` — A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.

*Drafted as:* the wrong-key run retried each request five more times before giving up, once auth is the problem the attempts still on the clock are worth nothing.

*Why there:* Neither listed place is discussing retries or failure classification. The Jun 9 recap is a status mail about PRs 690/691 and whether PR 653 should be closed in maintenance mode — the thread's live question is the disposition of 653, and an auth/retry observation would arrive from nowhere in nikolai's own recap and get no reaction. The image-pinning thread is scoped to caller-supplied images, the read-only workspace mount, and sandbox tags; its only failure-behaviour content is a deliberate argument for blowing up at create time, which is a different subject and would make a retry-budget line read as a second unrelated tangent. The remark needs a room where retry accounting is already the topic, and where the sibling remark about what happens to the freed attempts and the request's other counter can follow it.

*Still leaves open:* what should be done with those attempts, and what happens to the request's other counter

*A new thread — **smoke run timings on the wiki before we cut 0.1.26**, 2025-06-11:*

```
From: konrad  To: nikolai, dario, emil
Before we cut 0.1.26 I would like the smoke run numbers on the wiki to be correct. The page still says a full bulk-llm-inference pass is "about 20 minutes" and that was written in April, presumably before the batch request changes landed. Nikolai, I think you ran it earlier this week? Whatever you actually saw is better than what is on the page now. Also, is anyone still pointing these runs at the shared key or has everybody moved to their own. anyway not urgent but I want it settled this week.

From: nikolai  To: konrad, dario, emil   <-- the remark
ran it twice monday

first pass was 24 min clean so the wiki number is stale but not badly, i'd say write 25 and move on

second pass is the one worth mentioning, i had an old key sitting in my env and didnt notice, the wrong-key run retried each request five more times before giving up, once auth is the problem the attempts still on the clock are worth nothing, so somethign that should have died in seconds took 40 min to hand me a 401

not a release blocker off the top of my head but its the ki

From: dario  To: nikolai, konrad, emil
mhm 25 seems fine for the page, i'd honestly rather it read a little pessimistic than a little optimistic since people plan their afternoon around that number.

the 401 thing i have hit too actually, though at the time i assumed i was holding it wrong and didnt look further. in any case do you want me to drop both timings into the release notes draft as they are, or would you rather edit the wiki page yourself since you have the real numbers in front of you

From: emil  To: dario, nikolai, konrad
sounds right, i'll carry the 25 into the notes draft either way.

separately though, we need to be intentional here about which numbers we publish at all — half of them go stale within a month of being written and then someone reads them in June and plans around April. not entirely sure the wiki page is the right home for timings long term. leave it as is for 0.1.26, i'm not proposing anything this week.

```

### g3.r1.sc5 — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Nobody says:* Testing after the deduction rather than before it is what makes a two-attempt charge fatal at one attempt left and a zero-cost charge survivable at none.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g3.r1.l16` — failure_behavior

**dermot**, 2025-03-17, #pipeline

> ordering is the problem, we check the budget before we deduct the cost, so a malformed-output failure with one attempt left still gets a retry it can't pay for

*What a reader should take from it:* the team agrees the deduction happens before the test that ends the request

*Step it builds toward:* `g3.r1.sc5` — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Drafted as:* we check the budget before we take the cost off, so a malformed-output failure with one attempt left still gets a go it can't pay for.

*Why there:* None of the eight rooms is chewing on retry accounting. The closest surfaces are adjacent but not the same thread: 2025-03-19 mentions cost accounting only as a quote from the rate-limiter postmortem (headroom, throttle path), and 2025-04-21 names WS-054 cost accounting in a standup line before the room moves to v0.1.8 and `backend_params` validation — dropping an ordering finding about retry budget into either would change the subject and get no reply. 2025-05-06 is the nearest in content (malformed / plain-text output after the structured output revert) but that room is settling why `supports_structured_output()` is not optional, and dermot's only line there is "gotcha"; a retry-budget claim would be him reopening a closed incident on a topic nobody raised. What's missing is the conversation where someone actually reads the retry path after the revert — malformed structured output is exactly the failure that burns attempts, and that thread never happened.

*Still leaves open:* what the check should be once the order is fixed, and what is reported when it trips

*A new conversation in #pipeline on 2025-03-17:*

```
14:02  petar: the 11:40 rerun took a retry after the budget was already spent out. anyone seen that one
14:03  petar: it logged the retry and then died on the charge
14:05  dermot: if i had to guess its ordering. we check the budget and then deduct the cost, not the other way round
14:06  petar: so on the last attempt the check is reading a number thats one call stale
14:08  dermot: yeah. malformed output comes back with one attempt left, budget still looks fine because nothing was taken off yet, so it hands out a retry it cant pay for
14:09  emil: sounds right. deduct first, then the check sees whats actually left
14:10  dermot: mhm. thats the fix. no strong view on whose ticket it lands on
14:12  petar: ok that tracks, the check sits up in the scheduler and the deduct is down in the client somewhere
```

#### `g3.r1.l17` — failure_behavior, observability

**nils**, 2025-03-19, #pipeline

> The verdict logged attempts_left as -1 again overnight. settled: a malformed-output failure that cant pay comes back contract:exhausted with attempts_left 0, never a negative.

*What a reader should take from it:* the team agrees the post-failure budget on the verdict is floored at zero

*Step it builds toward:* `g3.r1.sc5` — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Drafted as:* The verdict logged attempts_left as -1 again last night, whatever number we hand back should stop at zero.

*Why there:* Neither listed room is anywhere near retry semantics. The 2025-03-19 #pipeline day is fully occupied with the Gemini unicode fix, the Mistral api_key blocker on PR 584, and the two outstanding postmortem checks (batch-mode estimation, throttle path in online-request-processing) — rate-limiting adjacent, but nobody there is discussing a retry verdict, a per-attempt budget, or what gets logged after a failed call. Dropping a field-level decision about attempts_left into that day would land between Gideon chasing his throttle check and Dermot closing out the day, and get no reaction from anyone. The 2025-03-25 #code-review day is pure release triage — which PRs target the next release, WS-047 having no scope written — and has no code substance in it at all; a symptom-from-last-night's-logs remark would be the only technical claim in the room. The conversation this belongs to is the one where the retry/backoff verdict shape is actually being settled: Nils reading overnight logs the morning after the throttle path came back clean, with Gideon (owner of online-request-processing, where the retry path lives) and Dermot, working out what the verdict carries after a call is exhausted. That thread also carries the sibling question — when the counter goes negative in the first place and what else the verdict reports then — which is exactly the part this remark must not resolve.

*Still leaves open:* when the number goes under zero in the first place and what else the verdict should say then

*Must appear literally:* `The`, `attempts_left`, `contract:exhausted`

*A new conversation in #pipeline on 2025-03-19:*

```
13:02  gideon: The verdict logged attempts_left as -1 again overnight. second time this week i think
13:04  dermot: -1 though. so something took one off past zero and nobody clamped it, if i had to guess
13:06  nils: malformed output path. it wants another attempt, cant pay for it, and still decrements on the way out
13:07  gideon: ok so what does that one come back as, then
13:10  nils: contract:exhausted, and attempts_left reads 0
13:10  dermot: 0 even where the budget was already gone before it tried
13:11  nils: 0. never a negative, whatever the arithmetic wants to do
13:13  gideon: ya. its only ever the overnight sweep that gets deep enough to hit it fwiw
```

#### `g3.r1.say23` — failure_behavior

**emil**, 2025-03-27, #viewer

> honestly the check belongs after the deduction and only trips on strictly negative - a malformed-output failure at attempts_left 2 lands on 0 and still gets retried.

*What a reader should take from it:* the team agrees the exhaustion test runs after the cost is charged and trips only on a strictly negative result, so landing on exactly zero attempts is still a retry

*Step it builds toward:* `g3.r1.sc5` — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Drafted as:* honestly the check belongs after the deduction and strictly negative - a malformed-output failure at attempts_left 2 lands on 0 and still gets retried.

*Why there:* None of the eight rooms is chewing on retry semantics at all — they're on batch response shapes, Mistral usage extraction, torch/litellm guards, auth, release notes, agent response shape, and the throttle/backpressure path. The closest, #engineering 2025-03-19, is about rate-limiter headroom and token estimation, not per-request attempt budgets; dropping a decision about where the `attempts_left` exhaustion check sits would change the subject and land without a reply. The remark needs a room where a retry/backoff decision function is actually being specified, and where a sibling can supply the verdict side (label, delay, floored budget). The natural prompt is the fallout from the 2025-05-06 structured-output revert: malformed-output responses are now a real failure class, and the team has to say whether they burn an attempt and when the budget counts as exhausted.

*Still leaves open:* says nothing about what the verdict looks like when the subtraction does go under zero - the outcome label, the delay and the floored budget all come from elsewhere

*Must appear literally:* `attempts_left`

*A new conversation in #viewer on 2025-03-27:*

```
14:22  konrad: the retry guard on the viewer path - is the attempts_left check before or after we take one off? off the top of my head its before
14:24  konrad: asking because a malformed run gave up earlier than i expected yesterday
14:29  emil: honestly the check belongs after the deduction. checking first means we're refusing on an attempt we havent actually spent yet
14:33  dermot: after, so it's comparing the new value. against zero or below zero? not the same thing here
14:37  emil: only trips on strictly negative. zero still has a pass in it
14:38  emil: so a malformed-output failure at attempts_left 2 lands on 0 and still gets retried, which is what you'd want
14:41  konrad: mhm ok. that lines up with what i saw then
```

#### `g3.r1.l19` — failure_behavior

**dario**, 2025-04-16, #code-review

> honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all

*What a reader should take from it:* the team agrees a non-retry verdict carries a zero delay and never draws from the jitter source

*Step it builds toward:* `g3.r1.sc5` — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Drafted as:* if the verdict isn't a retry then the wait should just be 0.0 and the schedule shouldn't be looked at at all.

*Why there:* None of the eight rooms is chewing on retry backoff at all. The nearest touch is dario on 2025-03-31 saying "the retry/resume paths are unaffected" — a release-scope aside in #releases, where a ruling about verdicts, delays and the jitter source would arrive from nowhere and draw no reaction from konrad or emil, who are on tags and release notes. The other seven are locked onto unrelated threads: PR 632/626 ordering, Mistral batch usage extraction, schema_check at construction, PR 583/614/621 scheduling, the executor's inspected directory. A remark fixing the wait at 0.0 and forbidding the schedule lookup only lands where someone has just put up the policy object and a reviewer has asked what the delay is on a non-retry verdict. That conversation doesn't exist in the listed set, so it has to be the one that should have happened.

*Still leaves open:* what makes a verdict a non-retry, and what the counters read afterwards

*Must appear literally:* `0.0`

*A new conversation in #code-review on 2025-04-16:*

```
15:12  konrad: in the backoff helper we still compute a delay when the verdict comes back not-a-retry. on purpose or leftover
15:14  dario: not on purpose i dont think. if its not a retry theres nothing to wait for, so the delay should just be 0.0
15:17  konrad: right, but 0.0 from where. we still walk the schedule to get it? the fail case ran off the end of the table tuesday
15:21  dario: no thats the part i mean, we shouldnt be reading the schedule at all in that branch. just hand back 0.0
15:23  gideon: what about the jitter, um, the rng gets pulled either way right now. i saw it in the trace
15:26  dario: same answer honestly, dont pull from the jitter source either. no schedule read, no draw, plain 0.0
15:28  konrad: mhm. the ceiling clamp sits after that read too, so it never sees a zero today
```

#### `g3.r1.l18` — failure_behavior

**emil**, 2025-04-24, #code-review

> went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out.

*What a reader should take from it:* the team agrees the schedule and jitter are being consulted for failures that will not be retried

*Step it builds toward:* `g3.r1.sc5` — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Drafted as:* we're sleeping a full throttle backoff on requests we've already decided to bin, and drawing jitter for them on the way out.

*Why there:* Nothing in the listed rooms is chewing on the retry path itself. #pipeline 2025-04-02 is the nearest — it touches retry logic ("requests got dropped in a way that looked like success, so retry logic never kicked in") and PR 615's failed-requests output — but that day is a sequencing argument about 614 vs 615 and who owns the jsonl visibility piece; a line about backoff sleeps and jitter draws would arrive from nowhere, get no reply, and drop the thread everyone was actually holding. The other seven are cache/billing incidents, viewer direction, release notes, and PR-queue triage, none of which have a retry loop open. What's missing is the review thread where somebody actually reads the backoff code after the April failure-visibility work lands: Emil going through the retry loop on a PR that reworks it, noticing that a classified-terminal failure still goes through the whole schedule — sleep and jitter — before it gets written out as failed, with Gideon (who owns the failure-visibility side) and Dermot in the room, and the open question of what the wait should be for something that isn't going back on the queue left for someone else to answer.

*Still leaves open:* what the wait should be for a request that is not going back on the queue

*A new conversation in #code-review on 2025-04-24:*

```
14:02  emil: went through the retry loop this morning, mostly the sleep math. one thing is bugging me
14:03  dermot: bugging you as in the numbers are wrong, or the ordering
14:05  emil: ordering. we're sleeping a full backoff on requests we've already decided to bin
14:06  dermot: decided as in it came back non-retryable? so we wait out the whole delay and then drop it anyway
14:07  emil: yup. and we draw the jitter for them too, on the way out
14:08  dario: mhm. jitter gets computed before the retryable check at all i think, its just sat at the top of the loop body
14:09  emil: it is. both of them, before we ever look at the response class. sleep + jitter want to sit after that check, not before it
14:11  dermot: yeah ok. that's the tail on the friday run then, if i had to guess
```

### Herrings — believed at the time, overturned later

#### `g3.r1.h1` — herring

**dario**, 2025-02-06, #code-review

> settled in review: THROTTLE costs 0 attempts off the retry budget - a 429 says nothing about the request itself, so decide charges nothing and re-queues it.

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* settled in review: throttle costs zero attempts. a 429 says nothing about the request itself, so decide charges nothing and re-queues it.

*Why there:* None of the eight rooms is chewing on retries, 429s, or attempt accounting. #pipeline runs on cost-map/token-accounting threads (2025-01-29, 02-03, 02-12, 02-18, 02-25), #cookbooks 03-11 is the create_model lookup-pass check, #engineering 03-04 is reviewer assignment for PRs 468/571/565/566, and #code-review 2025-01-21 is PR 387/394 plus a stale-PR triage — dario's own turns there are all "who's reviewing what." The nearest adjacency is the togetherai/klusterai rate-limit *defaults* on 2025-02-03, but that thread is about missing config entries per provider and whether they block the sprint, not about what a throttle costs against a retry budget; a "settled in review" verdict dropped there would reference a review nobody in the room had, and would draw no reply. The remark also presupposes a retry-classification review that has already concluded, which needs a room where that PR was actually being read. That conversation should exist and doesn't: the week after the rate-limit-defaults gap list, a retry/backoff PR in #code-review where the failure taxonomy gets settled, prompted by a run exhausting its retry budget on 429s from one of the providers that had no rate-limit default. It would also cover what the non-throttle classes cost and whether the budget is per-request or per-run.

*A new conversation in #code-review on 2025-02-06:*

```
14:01  nikolai: quick one while im in the backoff code does a THROTTLE burn an attempt or not
14:03  dermot: reading it as yes — it goes down the same increment path as a real failure. so three 429s in a row and the request is dead
14:07  dario: thats what it does today and honestly i think thats wrong. a 429 says nothing about the request itself, its our rate thats the problem not their payload
14:07  nikolai: so zero
14:08  dario: zero attempts off the retry budget yeah. costs nothing
14:10  nikolai: and decide hands back the same failure object or what
14:12  dario: no — decide charges nothing and re-queues it. same reqeust goes back in the queue, budget untouched
14:13  dermot: mhm. so the sleep is the only thing bounding it then, nothing on the count side
14:15  nikolai: right the 429 branch doesnt even read retry-after today thats its own mess
```

#### `g3.r1.h2` — herring

**konrad**, 2025-03-12, #engineering

> right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* Right — and there's no ceiling on that. A rate-limited request keeps its full budget however many 429s it eats; only TRANSIENT and CONTRACT deduct.

*Why there:* The remark confirms an already-agreed retry taxonomy (THROTTLE/TRANSIENT/CONTRACT) and states the budget rule as settled. No listed room has that vocabulary in play. The nearest, #engineering 2025-03-03, is at the wrong stage: Emil is still claiming the Gemini rate-limit work and deciding it lives under issues 207 and 233, so no budget policy exists to confirm — Konrad stating one there would be manufacturing a decision mid-triage. The code-review days are PR queue status, cookbooks is sandbox uid and broken examples, #general 2025-03-10 is Nils' onboarding. It would land with no reply in any of them. The thread that should exist is the follow-on where Emil's retry handling from 207/233 gets reviewed and the categories are pinned down; Konrad asking what counts against a retry and reading the answer back is exactly his role in these rooms.

*A new conversation in #engineering on 2025-03-12:*

```
14:26  dermot: the request that ate eight 429s over the weekend came back exhausted. is throttle counting against attempts or is that something else
14:29  konrad: it shouldnt. only transient and contract come off the budget
14:31  dermot: is there a ceiling on it further up then
14:33  konrad: right, no ceiling on it
14:34  konrad: a rate limited request keeps its full budget however many 429s it eats, THROTTLE never deducts
14:36  dario: mhm that tracks. counter only moves on the other two then
14:38  konrad: anyway noone has writen it that way yet, classify still returns the old shape. maybe i take it tomorow
14:41  dario: the weekend one sat on 429s for 40 min before it quit, thats the case i'd point a fixture at
```

#### `g3.r1.rev1` — rule, failure_behavior

**dario**, 2025-04-09, #incidents

> that "throttle costs zero attempts" line i settled in review is gone — a permanently throttled key re-queued for hours. 429 is free while throttle_waivers_left > 0, then decide charges 1.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* that "throttle costs zero attempts" line i settled in review is gone — a permanently throttled key re-queued the same requests for hours. a 429 is free only while throttle_waivers_left > 0; after that decide charges 1 like any transient.

*Why there:* No listed day is discussing retry classification or attempt accounting. 03-25 and 04-22 mention "the retry side"/"retry logic" only as scope questions (does 585 cover batch? does the casting fix keep malformed token counts out of retry?), and 04-09's rate-limit mention is gideon validating that cost surfaces cleanly, not a policy dispute. The remark also presupposes deployed behavior and a production incident — hours of re-queueing — which nothing in these rooms has raised, so it would change the subject and draw no reply. It needs the thread where the incident got reported: dario reversing a call he'd made in review, with gideon (owner of the rate-limit/cost-accounting pass from 04-09) and emil on provider behavior.

*Must appear literally:* `throttle_waivers_left`, `decide`

*A new conversation in #incidents on 2025-04-09:*

```
13:21  dermot: the throttled key from last night sat in the queue til about 04:00. thats the zero-attempt path doing exactly what we told it to, if i had to guess
13:22  dario: mhm. that "throttle costs zero attempts" line i settled in review is gone
13:23  dario: idea was a 429 says nothing about the request itself, so decide charged nothing and re-queued it. fine for a blip. that key was throttled permanently and we re-queued it for hours
13:24  gideon: so 429s eat the budget now? feels harsh for a one off spike tbh
13:24  dario: not flat, no. its free while throttle_waivers_left > 0
13:25  gideon: and after that
13:25  dario: then decide charges 1, same as any other failure
13:26  dermot: yeah ok. so the pool runs out first and then it dies normally
13:27  dario: right, and the waiver comes off on every 429 regardless, the charging only starts once its empty
```

> **Problems:** longer than one remark

#### `g3.r1.rev2` — rule, scope

**konrad**, 2025-03-20, #cookbooks

> Look, I said 429s never cost a request budget - that's out, a dead key looped for hours. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6 now, decide takes throttle_waivers_left and reports throttle_waivers_after.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* I said a rate-limited request keeps its full budget however many 429s it eats — that's out, a dead key looped for hours. Each APIRequest now walks in with DEFAULT_THROTTLE_WAIVERS = 6 of its own; decide takes throttle_waivers_left and reports throttle_waivers_after.

*Why there:* None of the eight rooms is chewing on retry/backoff. The closest is 2025-05-30 #code-review, where Konrad asks whether the viewer's `retry_after: 60` is reliable — but that's a viewer indexing hint, not the per-request 429 budget on APIRequest, and dropping a settled reversal of retry-budget policy into that thread would change the subject and draw no reaction. The other days are release notes, PR-queue triage, examples currency, the agent loop, and a version tag in the viewer. More importantly this remark is a reversal ("I said ... that's out"), so it needs a room where Konrad had previously argued the unlimited-waiver position and where the dead-key incident is fresh. The 2025-03-31 thread seeds it (Dario: credentials can be valid at startup and revoked by the time a request goes out) but the retry-budget discussion this overturns isn't in the corpus — the follow-up thread is missing rather than the line being hidden in one of these days.

*Must appear literally:* `DEFAULT_THROTTLE_WAIVERS`, `APIRequest`, `throttle_waivers_left`, `throttle_waivers_after`

*A new conversation in #cookbooks on 2025-03-20:*

```
13:32  dermot: that 429 loop over the weekend, the key was dead and it just kept going for hours. nothing ever decremented
13:34  konrad: look, i am the one who said 429s never cost a request budget. no ceiling on it, THROTTLE never deducts, only TRANSIENT and CONTRACT do. thats out now
13:35  dario: out as in throttle eats the normal budget now, or does it get its own pool
13:36  konrad: own pool. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6
13:37  dermot: decide only sees the request today though, if i had to guess the count has to be passed in
13:38  konrad: mhm. decide takes throttle_waivers_left and reports throttle_waivers_after, caller writes it back
13:39  dario: and the 6 is from that loop or just a roundish number
13:40  konrad: from the loop more or less. it would have been dead in the first minuite at six
```


## g3.r2

**The hidden requirement:**

- **rule** — The rate-limit pause is driven by an absolute horizon stored on the tracker, not by a config constant. `OnlineStatusTracker` gains exactly one new dataclass field, `throttle_cooldown_until: float = 0.0`, placed immediately after `time_of_last_rate_limit_error`. When a THROTTLE verdict is recorded on the tracker the policy reads its injected clock once for `now`, sets `time_of_last_rate_limit_error = now`, and advances the horizon monotonically: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, so a later short delay never pulls in a horizon an earlier longer delay already set. `remaining_cooldown_seconds(tracker, now)` returns `max(0.0, round(tracker.throttle_cooldown_until - now, 3))`.
- **scope** — The horizon is run-level state on the tracker, extended only by THROTTLE verdicts. Recording a TRANSIENT, CONTRACT or TERMINAL verdict increments its counter and touches neither `throttle_cooldown_until` nor `time_of_last_rate_limit_error`, and does not call the injected clock at all — so the clock-call count over a mixed sequence of failures equals the number of rate-limit failures.
- **exclusions_or_crossover** — `config.seconds_to_pause_on_rate_limit` is no longer read by any code path after this change: it stays in `config.py` as a dead knob for backwards compatibility, and the pause is never derived from it or from elapsed time since `time_of_last_rate_limit_error`. A run, model or request that has never been throttled waits zero seconds at the pause point even though the knob is still set to 10.
- **observability** — With a clock pinned at `1000.0` and jitter `0.25`: after one rate-limit failure, `throttle_cooldown_until == 1005.0`, `time_of_last_rate_limit_error == 1000.0`, and the clock has been called once; a contract failure recorded next leaves both at `1005.0`/`1000.0` with the clock still called once; a second rate-limit failure whose delay is `1.0` at the same clock leaves `throttle_cooldown_until == 1005.0`, not `1001.0`. `remaining_cooldown_seconds(tracker, 1002.0) == 3.0`, `(tracker, 1004.5) == 0.5`, `(tracker, 1005.0) == 0.0`, `(tracker, 1099.0) == 0.0`. A freshly constructed `OnlineStatusTracker()` has `throttle_cooldown_until == 0.0`, so `remaining_cooldown_seconds(tracker, 12345.0) == 0.0`.

**Reversed earlier:** The horizon was first written as a plain assignment `throttle_cooldown_until = now + delay_seconds`; that was reversed to a monotonic `max()` after a late transient-class failure was observed shortening a 40-second throttle horizon to a fraction of a second and re-opening the flood.

**What a reader has to infer along the way:**

- *The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.*
  - nobody says: if the stored end-time is already behind you there is nothing left to wait, so the pause point can ask a stored deadline the one question it actually cares about.
- *A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.*
  - nobody says: when two throttles overlap the longer wait is the one still owed, so a newly computed shorter deadline cannot be allowed to replace it.
- *Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.*
  - nobody says: state that exists to describe throttling should only ever be written by throttling.
- *The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.*
  - nobody says: one fixed number cannot be both long enough for the worst throttle and short enough for the smallest one, so the wait has to come from the failure itself.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `throttle_cooldown_until`, `time_of_last_rate_limit_error`, `tracker.throttle_cooldown_until`

> **Spread:** g3.r2.sc2: two remarks in #cookbooks within 13 days; g3.r2.sc3: two remarks in #releases within 7 days

> **13 of 51 graded assertions are not stated outright** — 13 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g3.r2.sc1 — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Nobody says:* if the stored end-time is already behind you there is nothing left to wait, so the pause point can ask a stored deadline the one question it actually cares about.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g3.r2.s1b` — rule

**gideon**, 2025-03-21, #pipeline

> so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it.

*What a reader should take from it:* the pause point should be asking how much of the throttle window remains

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* Nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much of it is left and we idle well past it.

*Why there:* None of the eight rooms is chewing on rate limiting or backoff. The code-review days are PR-triage traffic (auth flow, viewer deletion, gemini parts key, schema_check at construction) — the closest touch is Dario asking on 04-01 whether the gemini break came from "the retry logic that came in with PR 585," which Emil immediately closes off with "Not the retry logic, that part landed fine," so a throttle-window complaint there lands as a subject change nobody answers. #random 04-17 is an incident-story thread about mkdir -p and double billing, wrong register for a tracker/pause-point observation, and #viewer 04-28 is structurally similar (a report object missing a field) but about the inspected directory, not a throttle window. What's missing is the conversation where the backoff policy itself gets looked at: a run that keeps sleeping long after the provider's window has already reset, with Gideon reporting the idle time and someone else — Dario or Nikolai — answering where the reset timestamp would live, what writes it, and what the pause point does when the window has already passed. That's the sibling remark, and it wants its own thread in #engineering.

*Still leaves open:* where that end time would live, what sets it, and what the answer looks like when the window is already over

*A new conversation in #pipeline on 2025-03-21:*

```
13:12  dario: last nights 429 retry slept ~40 min total. the window was 8
13:13  emil: so youre saying the backoff just doubled straight past the reset? i thought we read that header
13:15  gideon: we read it for the log line, ya. but nothing on the tracker recods when the throttle window actually ends, its just attempt counts
13:17  dario: so the sleep site has nothing to ask about how much is left, either way
13:18  gideon: exactly. the pause point cant ask how much is left so it keeps doubling and we idle way past it. so basically the window end goes on the tracker and the sleep reads it there
13:20  emil: yup, and clamp to that instead of the fixed ceiling
13:23  dario: the 8 was sitting in the header on that run too. we had the number and dropped it
```

> **Problems:** describes asking rather than settling

#### `g3.r2.s1c` — rule, observability

**dermot**, 2025-04-07, #pipeline

> on the retry side: remaining_cooldown_seconds(tracker, now) handed back -3.2 once the window was behind us, and 4.999999999998 before that — clamp at 0.0, round to three decimals.

*What a reader should take from it:* the remaining-wait number is clamped at zero and rounded to three decimals

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* the helper handed back -3.2 once the window was behind us, and 4.999999999998 before that; i want 0.0 in the first case and three decimals in the second.

*Why there:* dermot opened that day saying he wanted to confirm the gemini batch changes don't regress cost accounting or retry logic before calling PR 614 done — he is the only person in any of these rooms who has retry logic on his plate, and this is him reporting back on his own stated check. The thread then splits: gideon takes the cost-accounting half (the 10x resume case) while dermot's retry half never gets its result stated, so a finding from him lands in a gap the room already left open rather than changing the subject. It doesn't collide with anything: nobody else has touched the remaining-wait helper, and the window itself stays unexplained, which the resume/config discussion around it makes unremarkable.

*Still leaves open:* what the window is, where it is stored, and what puts it there

*Must appear literally:* `-3.2`, `0.0`, `4.999999999998`, `remaining_cooldown_seconds(tracker, now)`

*Goes into the real conversation in #pipeline on 2025-04-07, after 10:52 dermot:*

```
09:00  dermot: - *pr 614*: cancellation fixes are close, expect to flag it for review this morning
- gemini batch changes landed over the weekend and I want to confi
09:44  gideon: What exactly did the Gemini batch changes touch on the cost accounting side?
09:44  gideon: I want to cross-check something I saw with resume
09:44  gideon: Actually, on resume, does the cost counter pull the model from the current config or from whatever the job was originally submitted with?
09:44  gideon: I hit a case where it came out about 10x off
10:02  dermot: I'm around all day if it helps to have another set of eyes on this once it's clearer what the resume path is doing.
10:32  gideon: Appreciated, I'll ping you once I've got more to show.
10:52  dermot: did the job resume on a different model than it was originally submitted with?   <-- THE REMARK GOES HERE
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
13:49  gideon: More observed symptom right now, I hit it once and saw the number, I don't have a minimal repro yet.
```

> **Problems:** longer than one remark

#### `g3.r2.s1d` — observability

**nils**, 2025-04-07, #general

> A tracker nobody has throttled answers 0.0 however far ahead you ask — with the window at 1005.0, remaining_cooldown_seconds(tracker, 1002.0) is 3.0, 0.5 at 1004.5, 0.0 at 1005.0.

*What a reader should take from it:* an untouched tracker answers zero, and otherwise the answer is the window minus the time asked about

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* A tracker nobody has throttled should answer 0.0 however far ahead you ask. window at 1005.0: 3.0 at 1002.0, 0.5 at 1004.5, 0.0 at 1005.0.

*Why there:* Both listed rooms are doing release-queue triage — reviewer assignment for PR 584, whether 565/566/579 sequence or land as reviewed, and the missing WS-047 spec. Neither has said anything about retries, 429s, cooldowns, or tracker semantics, so a numeric statement of what an unthrottled tracker returns answers nothing on the table and would sit there unremarked. The remark also depends on a sibling stating what sets the window to 1005.0 and what later failures do to it, and there is no room in either day for that sibling either — the whole exchange is absent, not just this line.

*Still leaves open:* what sets the window to 1005.0 in the first place and what happens to it on later failures

*Must appear literally:* `0.0`, `0.5`, `1002.0`, `1004.5`, `1005.0`, `3.0`, `A`, `remaining_cooldown_seconds(tracker, 1002.0)`

*A new conversation in #general on 2025-04-07:*

```
14:02  konrad: quick one on the backoff thing - what should remaining_cooldown_seconds(tracker, 1002.0) hand back if the window on A runs to 1005.0
14:04  nils: 3.0. it is just the window end minus the now you pass in, so 0.5 at 1004.5
14:05  konrad: and right on the boundary? presumably it does not go negative after
14:06  nils: no, it clamps. 1005.0 itself already reads 0.0 and stays there
14:08  gideon: ok but what about a tracker nobody ever throttled, theres no window on it at all tbh
14:10  nils: let me think - same answer, 0.0, however far ahead you ask. nothing to wait on
14:11  konrad: right. none of that is actually in the file yet though is it
14:12  nils: not yet, no
14:13  gideon: ya ok. i had it returning None for the untouched one in my head
```

> **Problems:** longer than one remark

#### `g3.r2.say19` — rule

**dario**, 2025-04-11, #releases

> mhm — and it sits as a plain module function in the retry policy, remaining_cooldown_seconds(tracker, now), not a method on the tracker, the pause point hands it both.

*What a reader should take from it:* the team agrees the remaining-cooldown helper is a module-level function in the retry policy taking the tracker and the current time

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* and it lives as a plain module function in the retry policy, remaining_cooldown_seconds(tracker, now) — not a method on the tracker, the pause point hands it both.

*Why there:* None of the listed rooms is designing a retry cooldown. The closest, #pipeline 2025-03-31, mentions PR 585 "retry logic for batch" and issues 207/233 on rate-limit headers, but only as unowned backlog — nobody there is placing a helper, and dropping a settled signature into a day that ends with "carry both into next milestone unowned" would contradict the room. The two siblings this remark leans on come from dermot (subtraction, floor at zero, three-decimal rounding) and nikolai (the horizon field), and those two never appear together in any candidate — nikolai only shows up in #code-review 2025-04-08, a PR-triage day with no dermot and no design talk. This needs the conversation where the cooldown tracker, the pause point and the surfaced field get settled at once, and that conversation isn't in the list.

*Still leaves open:* says nothing about what the helper returns — the subtraction, the floor at zero and the three-decimal rounding all come from dermot's line, and the horizon field itself from nikolai's.

*Must appear literally:* `remaining_cooldown_seconds(tracker, now)`

*A new conversation in #releases on 2025-04-11:*

```
13:41  nikolai: the cooldown remainder math where does that live now do we hang it off the tracker
13:43  dermot: retry policy side. plain module function, not entirely sure it needs to be anything cleverer
13:44  nikolai: what does it take then it needs a clock from somewhere
13:46  dermot: remaining_cooldown_seconds(tracker, now)
13:47  konrad: so the tracker itself stays dumb, right? no method on it
13:49  dario: mhm — not a method on the tracker, honestly. the pause point already holds both so it just hands it both
13:51  nikolai: yep thats fine
13:52  konrad: then the inline math in the sleep path can go, presumably. nobody has written any of this yet though
```

#### `g3.r2.s1a` — rule

**nikolai**, 2025-06-18, page:meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md

> tracker gains one new field for this and only one: throttle_cooldown_until, 0.0 on a fresh tracker, sitting right after time_of_last_rate_limit_error. nothing else added for the pause.

*What a reader should take from it:* the tracker holds a second time value right after the rate-limit one, zero until something sets it

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* tracker fields, current order: num_other_errors, time_of_last_rate_limit_error, throttle_cooldown_until (0.0 on a fresh tracker). still moving around, don't quote me on it.

*Why there:* The page's "Rate limit handling" section logs 207 and 233 as open and defers auto-detect past dormancy, i.e. the room's live question is what is actually moving in that area. Nikolai is the person who keeps dragging 207/233 back onto the list (Mar 17, Apr 21, Jun 16), so him leaving the current tracker field order under those notes complicates the "nothing happening here" reading without resolving what the second timestamp is for.

*Still leaves open:* what the second timestamp is for, who writes it, and what the pause point does with it

*Must appear literally:* `0.0`, `throttle_cooldown_until`, `time_of_last_rate_limit_error`

*Goes as a comment on the real page `meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md`:*

```
# Weekly sync notes: week of Jun 9 (bulk LLM inference)

Note-taker: Emil. Led by Dario.

---

## Status

Dario walked through current state of bulk-llm-inference. Overall: on track for the milestone, no blockers.

## Rate limit handling

- Issues 207 and 233 both still open
- Auto-detect rate limits work: team agreed to defer this to post-dormancy
  - not blocking v0.1.26, and dormancy window is close enough that it doesnt make sense to rush it in now

## Cost / usage tracking

- Issue 293: unblocked but not prioritized for v0.1.26
  - Dario confirmed it's unblocked (the API surface is there to do it)
  - just not in scope for this milestone, comes after

## Open

- [ ] 207 - rate limit handling
- [ ] 233 - rate limit handling (related, separate issue)
- [ ] 293 - cost/usage tracking via API, punted past v0.1.26
```

> **Problems:** longer than one remark

### g3.r2.sc2 — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Nobody says:* when two throttles overlap the longer wait is the one still owed, so a newly computed shorter deadline cannot be allowed to replace it.

*5 remarks — 0 reporting the problem, 5 settling the design.*

#### `g3.r2.s2b` — rule

**dario**, 2025-03-19, #releases

> honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out

*What a reader should take from it:* the end-of-throttle time moves outward only

*Step it builds toward:* `g3.r2.sc2` — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Drafted as:* if a new wait lands earlier than the one we are already holding, it should just lose; that window only ever moves further out.

*Why there:* None of the listed rooms are chewing on backoff or throttle windows. The closest is #pipeline 2025-04-22, where dario asks whether malformed anthropic token counts reach the retry logic — but that thread is about the casting fix's blast radius, and nobody there is holding a wait, comparing two waits, or discussing a shared cooldown at all, so a ruling on window monotonicity would change the subject and draw no reply. 2025-04-09 touches rate limits only as an observability surface gideon is validating. The other threads are PR-triage, batch id persistence, and schema_check at construction. What's missing is the thread that dario's own 04-22 retry question points at: two workers each getting a 429 with different Retry-After values and each stomping the other's cooldown, which is where "the later wait wins" is the settled call and where the sibling question — where the window lives, what the clock reading is shared with, which failure classes extend it — is still open.

*Still leaves open:* where the window is kept, what the clock reading is shared with, and which failure classes get to extend it

*A new conversation in #releases on 2025-03-19:*

```
14:08  konrad: on the backoff work, if a second retry-after comes in while we are already sleeping, do we take it or keep the deadline we have
14:11  emil: we take it only if its later i believe. otherwise nothing changes
14:12  konrad: and if its earlier? clamp down to it, or ignore
14:16  dario: it loses. we keep sitting on the one we're already holding, the new shorter one just doesnt apply
14:17  konrad: feels odd to throw away what the server just told us
14:20  dario: honestly that window only ever moves further out, ive not seen one pull back in. so the earlier value is noise
14:22  emil: sounds right, so its a max of the two and not much else
14:25  konrad: off the top of my head the 429 and the 503 path build that number in two different places though
```

#### `g3.r2.s2a` — rule

**konrad**, 2025-03-21, #cookbooks

> Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again.

*What a reader should take from it:* a later short backoff must not shorten a wait already in force

*Step it builds toward:* `g3.r2.sc2` — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Drafted as:* Second 429 came back with a tiny backoff and pulled our wait down to under a second, and we were right back into the flood.

*Why there:* No listed room is running a request-level failure. The nearest is #code-review 2025-04-01, where dario floats "the retry logic that came in with PR 585" at 11:50, but emil rules it out at 12:18 ("Not the retry logic, that part landed fine") and the day is spent on the gemini parts key and the stale cookbook examples — a 429-flood report there reopens a settled question on a different axis and draws no reply. The rest are PR/workstream status (#engineering 05-29, #code-review 2026-01-02), viewer rendering (06-02, 07-10), response shape (05-21), release contents (03-19) and cost estimation (03-24); konrad in all of them is asking plain-what ownership and readiness questions, not reporting retry timings he watched during a run. The remark is an incident observation that needs the retry-path owner present and a sibling remark stating what the wait should have been, and that room does not exist yet.

*Still leaves open:* what the wait should have been instead, and which failures are allowed to move it

*A new conversation in #cookbooks on 2025-03-21:*

```
13:36  nikolai: why did the retry example blow up again on that rerun
13:38  dario: second 429 came back with a tiny backof value, and we just took it
13:39  nikolai: took it as what we were already 8s deep by then
13:41  dario: as the new wait. it pulled us back down under a second
13:43  konrad: and then we were straight into the flood again. thats the loop right there
13:44  konrad: look, we just dont let it go down. whichever is larger, ours or the header
13:46  nikolai: yep solid enough
13:48  dario: by the end of that run the 429s were landing ~300ms apart fwiw
```

#### `g3.r2.s2c` — observability, rule

**emil**, 2025-03-25, #pipeline

> @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, the first 429's own delay reads 5.0 unrounded, so tracker.throttle_cooldown_until is 1005.0; a second worth 1.0 leaves it.

*What a reader should take from it:* with a pinned clock the window lands at now plus the backoff and a shorter second backoff leaves it unchanged

*Step it builds toward:* `g3.r2.sc2` — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Drafted as:* Pinned the clock at 1000.0 and jitter at 0.25: first 429 puts tracker.throttle_cooldown_until at 1005.0, and a second one worth 1.0 has to leave it there.

*Why there:* nils asks at 10:19 "what does PR 585 actually change on the retry side" and the question dies unanswered — emil is the one answering everything else in that channel that day (Gemini test coverage, WS-047), so him coming back with what the retry test actually pins fits the shape of his other replies. It gives nils concrete behavior without settling the batch-vs-online half of his question, which stays open. Nothing already said covers the cooldown stamp, and dermot's separate "585 under review" line on 03-31 is about his own review pass, not test semantics.

*Still leaves open:* what the other stamp does at the same moment, and what non-throttle failures do to either

*Must appear literally:* `0.25`, `1.0`, `1000.0`, `1005.0`, `5.0`, `585`, `tracker.throttle_cooldown_until`

*Goes into the real conversation in #pipeline on 2025-03-25, after 10:53 nils:*

```
09:00  nils: Mistral batch processor is up in PR 584. I did pull out some of the Mistral-specific tests as part of the refactor, and I want to make sure we're not 
09:39  nils: Does anyone know what tests actually got removed in the Gemini example refactor? I want to make sure we're not already thin on provider coverage beofr
10:19  nils: what does PR 585 actually change on the retry side - does it cover batch submissions or just online requests?
10:53  nils: does the batch test suite cover providers generically or is each test provider-specific?   <-- THE REMARK GOES HERE
12:42  emil: I went through the Gemini example refactor and the tests that got pulled were tied to the example setup, not the core provider path, so coverage shoul
12:56  emil: I pulled up WS-047 and it doesn't seem to exist yet as an issue
12:56  emil: Is that still on Nils to open, or did it land somewhere else?
13:12  nils: good to know on Gemini. the Mistral tests I'm planning to drop look like this - all fixture-based, nothing hitting a real endpoint:

```python
def tes
14:10  dario: fair enough
14:48  emil: WS-047 doesn't show up anywhere in the issues
14:48  emil: @Nils, is that still getting written, or has it stalled?
15:09  nils: hasn't stalled, I just have no scope to work from. I'll write it up from scratch this afternoon, but someone should shout if it needs to match somethi
15:52  emil: Does anyone actually know what it was originally supposed to cover, or is Nils genuinely starting from a blank slate here?
16:08  dario: Provider-integrations test coverage is still solid after those fixture removals, nothing hitting a real endpoint got pulled.
16:44  nils: good on the coverage - I'll go ahead and drop the Mistral fixture tests from provider-integrations
16:44  nils: That's the last open question on my side for this PR
16:49  emil: Is fixture coverage enough to sign off on 584, or does anyone want an integration pass before it merges?
16:54  dario: makes sense
17:29  emil: @Nils, do you want someone to review 584 before end of day, or is it ready to merge once the fixture tests are dropped?
17:31  nils: review before merge, yes - implementation hasn't had eyes yet
17:32  nils: anyone able to take a look at PR 584 first thing tomorrow?
17:45  dario: I can take a look at 584 tomorrow, it's in my area anyway.
18:20  emil: Are we all in agreement that provider test coverage is still solid after the Gemini example cleanup and now the Mistral fixture removals?
18:20  emil: Actually, Dario already confirmed coverage is solid earlier in this thread
18:20  emil: Is that enough to green-light 584 once the fixture tests are out, or do we want a second opinion first?
```

> **Problems:** longer than one remark

#### `g3.r2.say21` — scope

**konrad**, 2025-04-03, #cookbooks

> look, every THROTTLE bumps num_rate_limit_errors by one on the way through — one 429, one increment, and that's the only counter it touches.

*What a reader should take from it:* the team agrees a THROTTLE verdict increments num_rate_limit_errors by one and no other counter

*Step it builds toward:* `g3.r2.sc2` — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Why there:* None of the listed rooms is chewing on verdict kinds or counter semantics. The closest, #engineering 2025-03-19, is arguing about whether the token-count fix shifted the throttle path and who owns closing the postmortem action item — nobody there has opened the request-processing code, and the technical detail that day comes from gideon ("token counts feed directly into the throttle check in online-request-processing"), not konrad. A statement about what a THROTTLE verdict increments would arrive with no vocabulary around it and draw no reaction. What is missing is the follow-up: the throttle check konrad called for at 17:36 actually being run, and the team pinning down what each verdict kind records before anyone can say whether behaviour shifted. That conversation carries this remark and its sibling (other verdict kinds, the two timestamps) naturally. The cookbooks, code-review and viewer threads are about docs, PR status and rendering, and have no seam for it at all.

*Still leaves open:* what the other verdict kinds do to their own counters, and what the throttle path does to the two timestamps

*Must appear literally:* `THROTTLE`, `num_rate_limit_errors`

*A new conversation in #cookbooks on 2025-04-03:*

```
15:23  nikolai: quick one on the retry counters in the cookbook example, if one request gets throttled twice does that come out as 1 or 2
15:24  konrad: 2. every THROTTLE bumps num_rate_limit_errors by one on the way through
15:26  nikolai: ok so its per 429 not per request
15:28  konrad: right. one 429, one increment
15:29  dario: does it hit anything else on the way past, like a generic error total or the failed count
15:31  konrad: no, thats the only counter it touchs. nothing else moves
15:33  nikolai: solid enough ill park it on the retry ticket, dunno who picks it up
15:35  dario: then the 7 in tuesdays sample was just 7 429s, i had it written down as a double count
```

#### `g3.r2.s2d` — rule, scope

**nils**, 2025-04-21, #general

> let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both.

*What a reader should take from it:* a rate-limit failure reads the clock once and stamps both values from that single reading

*Step it builds toward:* `g3.r2.sc2` — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Drafted as:* our two stamps came out 40ms apart because the handler asked the clock twice; take one reading and use it for time_of_last_rate_limit_error and the window both.

*Why there:* Neither listed room is chewing on the rate-limit error handler's internals. The 03-19 #engineering day is topically adjacent — the postmortem says the rate limiter miscalculated headroom, and there's an open action item to audit the throttle path — but the whole day is about *who owns which check* and whether the estimation close waits on the throttle result; nobody is inside the handler code. Nils that day is on api_key and PR 584 and says nothing about rate limiting, so a clock-skew finding from him lands with no one to answer it. The 03-24 #code-review thread is pure review-status traffic on PRs 583/584, and Emil has already pronounced 584 clean, so a defect report about double clock reads would either contradict that or attach to nothing. What should have existed is the follow-on to Emil's audit: the throttle-path dig turns up two timestamps 40ms apart in the rate-limit failure path, and the thread settles both the single clock reading (this remark) and, separately, which failures trip the handler and how the cooldown window folds into what it already held.

*Still leaves open:* which failures reach that handler at all, and how the window is combined with what it already held

*Must appear literally:* `time_of_last_rate_limit_error`

*A new conversation in #general on 2025-04-21:*

```
14:12  dermot: pulled the retry logs from fridays run. the two stamps we write on a 429 are always about 40ms apart from each other
14:15  nils: 40ms is suspiciously consistent. is that write ordering, or are we reading the clock twice
14:18  dermot: twice. the handler asks for now() when it stamps, then asks again when it computes the window
14:21  nils: let me think — ok that's the whole of it then. take one reading at the top of the handler and use that value for time_of_last_rate_limit_error and for the window both, instead of each grabbing its own
14:23  nikolai: so window start is off the same value not its own call
14:24  nils: yes, same value in both places.
14:26  nikolai: nobodys written it yet, i'd say it rides along with the WS-050 sweep unless dermot wants it separate
14:29  dermot: mhm. the gap was wider than 40 on the slow box last week too, which fits
```

### g3.r2.sc3 — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Nobody says:* state that exists to describe throttling should only ever be written by throttling.

*5 remarks — 0 reporting the problem, 5 settling the design.*

#### `g3.r2.s3a` — scope

**emil**, 2025-03-24, #releases

> honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock.

*What a reader should take from it:* only rate-limit failures may read the clock, so the call count tracks the number of 429s

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* Fake clock logged three calls for one 429 and two schema failures. A bad payload has no business asking what time it is.

*Why there:* None of the eight rooms is discussing retries, backoff, or time injection. code-review|2025-04-08 mentions rate limits only as missing KlusterAI config values under issue 616 — a fake-clock call count answers no question asked there and would draw no reaction. pipeline|2025-04-15 has a rate limiter question, but it is about cost-streaming buffer deadlock and Emil already resolved it at 15:22; a second unrelated rate-limiter finding from him the same afternoon competes with his own message. The remaining threads (batch id persistence, schema_check at construction, agentic curation scope, cookbook verifier, provider PR sequencing) have no retry surface at all, and none has anyone in the room able to supply the sibling half about what the non-throttle failures were touching instead.

*Still leaves open:* what else the non-throttle failures were touching, and what they are supposed to do instead

*A new conversation in #releases on 2025-03-24:*

```
14:02  konrad: quick one, the fake clock in the retry test logged 3 calls but that run only had one 429 in it. is that normal
14:06  emil: not entirely sure it is normal, no. the other two would be the schema failures, i believe — same run had two of those and they go down the same sleep path
14:09  konrad: right but a bad payload has no business asking what time it is. sleeping does not fix the shape of it
14:12  emil: yup, agreed. only the throttles should be reading the clock. schema failure just fails out, no backoff, no clock
14:14  dario: that tracks. so one call for that run and not three
14:17  konrad: anyway that explains the 3 sitting in my notes, i wrote it down as expected at the time
```

> **Problems:** longer than one remark; contains its own forbidden term 'THROTTLE'

#### `g3.r2.s3c` — scope

**dermot**, 2025-03-31, #releases

> yeah, for a schema failure the counter is the whole job — a CONTRACT verdict bumps num_api_errors by one and that's it, no stamps, no windows.

*What a reader should take from it:* non-throttle failures increment their counter and write nothing else

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* for a schema failure the counter is the whole job, it has no reason to be moving stamps or windows around.

*Why there:* None of these rooms is anywhere near retry/backoff state. The two #pipeline days are about cache fingerprints and about when the local batch record gets written; #help is capability checks and fail-open, #general is warn-vs-raise and abort-vs-fallback, #code-review is CI tags and PR status, and 05-13 is a logger.warning grep. A line distinguishing what a non-throttle failure path writes (counter only, no timestamps or cooldown windows) from what the throttle path writes has nothing above it to answer — there is no retry handler under discussion on any of those days, so it would change the subject and draw no reply. Dermot is the right person to say it, but he needs a thread where somebody has just proposed that every failure run through the same backoff bookkeeping. That conversation is the one that should exist: a run that kept getting 429s from the provider and never actually backed off, because validation errors were resetting the same cooldown state the throttle path uses — emil bringing the run in, dario walking the error classification in the request layer, dermot drawing the line between the two paths.

*Still leaves open:* what the throttle path does that this path skips, and why the clock matters here

*Must appear literally:* `CONTRACT`, `num_api_errors`

*A new conversation in #releases on 2025-03-31:*

```
16:08  konrad: quick one before I forget - when a response comes back failing schema validation, what happens on the retry bookkeepign side? does it get a stamp like the 429s do
16:11  dermot: no. for a schema failure the counter is the whole job
16:12  dario: which counter though, theres like three of them in that struct
16:14  dermot: num_api_errors. a CONTRACT verdict bumps it and thats the end of it
16:15  konrad: bumps it per bad row, or once for the response
16:16  dermot: by one. and nothing else gets written on that path, no stamps, no windows
16:19  dario: mhm ok. simpler than what i had in my head to be honest
16:21  dermot: the windows only ever mattered for the 429 side, if i had to guess thats where it came from
```

#### `g3.r2.s3b` — scope

**gideon**, 2025-04-09, #pipeline

> so basically a timeout landed betwen two 429s and jumped our last-rate-limit stamp — a TRANSIENT only bumps num_api_errors, time_of_last_rate_limit_error is throttle-only.

*What a reader should take from it:* a transient failure must not update the rate-limit timestamp

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* A timeout landed between two 429s and our last-rate-limit stamp jumped to it; the graph showed us throttled when the provider was perfectly happy.

*Why there:* Gideon opened that day saying he was validating that rate limit and cost accounting surface cleanly through online-request-processing and that "nothing alarming so far" — the room is explicitly waiting on that pass before signing off on Dermot's provider changes. This is the finding from that pass, in his own workstream, complicating his own earlier all-clear. It sits right after his 14:36 catch-up burst where he's already reporting what he has and hasn't covered, and it doesn't step on the 03-19 throttle check, which was declared clean at the time.

*Still leaves open:* whether the other stored time moved too, and what a timeout should be doing instead

*Must appear literally:* `TRANSIENT`, `num_api_errors`, `time_of_last_rate_limit_error`

*Goes into the real conversation in #pipeline on 2025-04-09, after 14:36 gideon:*

```
09:00  dermot: landed 8 commits on bulk-llm-inference and the provider integration side this morning
09:00  dermot: I want someone to sanity check that the backend changes don't quietly break any of the existing providers before we go further
09:15  gideon: On the observability side, I've been validating that the rate limit and cost accounting surfaces cleanly through online-request-processing. Nothing al
09:15  gideon: Also been looking at the caching-and-resume side and haven't hit any surprises yet
09:36  dermot: Gideon, is your pass covering the batch submission path as well, or just online requests and caching so far?
14:36  gideon: Sorry, missed this
14:36  gideon: Mostly online requests and caching so far, batch submission path I haven't gotten to yet   <-- THE REMARK GOES HERE
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

#### `g3.r2.say22` — scope

**dario**, 2025-04-18, #incidents

> and the non-throttle verdicts never touch num_rate_limit_errors, it only moves on a THROTTLE - so it just sits there through a whole run of schema misses and timeouts

*What a reader should take from it:* the team agrees non-throttle verdicts leave num_rate_limit_errors unchanged

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* and the non-throttle verdicts never touch num_rate_limit_errors — it only moves on a THROTTLE, so it holds still through a run of schema misses and timeouts.

*Why there:* Every listed room is chewing on something else: construction-time schema_check (03-14), num_gpus scope (04-29), PR triage (03-19), unknown-capability hard-blocking (03-26), when the batch record gets written (04-03), and the cache fingerprint/job record model gap (04-18, 04-23, 04-11). None of them has raised retry classification at all — no verdicts, no THROTTLE, no error counters — so a line about what num_rate_limit_errors does and doesn't move would change the subject and land without a reply. The remark needs a thread where someone is actually reading the retry classifier's verdict handling, which is adjacent to but not inside the caching/fingerprint work dario is doing in those rooms. The natural home is a #engineering thread a day or two after the 04-23 pipeline thread, prompted by the same bulk-llm-inference runs: dermot and emil have been eating rate limits on the provider side ("few loose ends on the provider side"), gideon asks why backoff isn't escalating on a run that's clearly failing, and dario — who has been living in that code — walks the verdict-to-counter mapping. His half is the settled observation that non-throttle verdicts leave num_rate_limit_errors alone; the per-verdict increments would come from whoever actually owns the request path.

*Still leaves open:* which counter each non-throttle verdict does increment, and by how much

*Must appear literally:* `num_rate_limit_errors`, `THROTTLE`

*A new conversation in #incidents on 2025-04-18:*

```
15:11  nikolai: last nights bulk run retried something like 40 times and the rate limit count came back 0
15:14  dario: thats num_rate_limit_errors, and honestly it only moves on a THROTTLE verdict, thats the one place we bump it
15:15  nikolai: so what does it do on the other verdicts
15:17  dario: nothing at all - the non throttle verdicts never touch it. schema miss, timeout, malformed json, they all go down the same retry path and leave it sitting where it was
15:19  dermot: so it just sits there through a whole run of schema misses and timeouts. if i had to guess that is your 0
15:21  dario: mhm. simplest thing is a seperate counter bumped on the generic retry path and leave the throttle one as it is, in any case we want the two numbers apart
15:22  nikolai: right the alert we hung off that field has never fired once then
```

#### `g3.r2.say20` — scope

**nils**, 2025-04-29, #general

> let me think — a TERMINAL verdict gets its own slot, num_other_errors, one increment, and nothing else on the tracker moves for it.

*What a reader should take from it:* the team agrees a TERMINAL verdict increments num_other_errors and touches nothing else

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* let me think — a TERMINAL verdict has its own slot, num_other_errors, one increment, and nothing else on the tracker moves for it.

*Why there:* Both #code-review days are pure triage: what lands before the release, who reviews PR 584, and the fact that WS-047 has no page, no ticket, no scope. Neither day touches retry verdicts, error counters, throttling, or the tracker at all, so a settled statement about counter semantics would land with no one to answer it and no thread to pick up. Worse on 03-25 specifically: Nils spends that day saying nobody handed him a scope for WS-047 and there's genuinely nothing written — him stating a decided verdict-to-counter mapping in the same room contradicts the state he's complaining about. The remark belongs in the design conversation that happens once WS-047 actually gets written, where the sibling remark about the other non-throttle verdicts and whether the clock is read has somewhere to sit.

*Still leaves open:* which counters the other non-throttle verdicts use, and whether the clock is read at all on this path

*Must appear literally:* `TERMINAL`, `num_other_errors`

*A new conversation in #general on 2025-04-29:*

```
14:22  dermot: question on the retry tracker — when a response comes back TERMINAL, which counter is that supposed to land on
14:23  dermot: right now it falls through the generic error path with the timeouts, which reads wrong to me
14:31  nils: let me think. it shouldn't share a bucket with rate limits or timeouts, no. i'd give it its own slot — num_other_errors
14:33  dermot: ok that i can do. does anything else move at the same time though, attempt count, in flight, either of those
14:38  nils: no. one increment on that field and nothing else on the tracker moves for it
14:39  dermot: yeah ok. so a TERMINAL never touches the retry numbers at all
14:40  nils: right, nothing gets retried so there's nothing to count there
14:47  emil: field isn't on the dataclass yet fwiw, its four ints and none of them is that one
```

### g3.r2.sc4 — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Nobody says:* one fixed number cannot be both long enough for the worst throttle and short enough for the smallest one, so the wait has to come from the failure itself.

*5 remarks — 0 reporting the problem, 5 settling the design.*

#### `g3.r2.say23` — exclusions_or_crossover

**dario**, 2025-03-17, #code-review

> @Konrad on 585 - i left config.seconds_to_pause_on_rate_limit exactly as it was, still 10 on the processor's config, the pause point just doesnt read it anymore

*What a reader should take from it:* the team agrees the processor's config still reports seconds_to_pause_on_rate_limit as 10 after the change

*Step it builds toward:* `g3.r2.sc4` — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Drafted as:* on 585 i left config.seconds_to_pause_on_rate_limit exactly as it was, still 10 on the processor's config — the pause point just never reads it now.

*Why there:* Konrad opens 03-17 by asking Dario and Emil specifically where PR 565, 566, 579 and 585 stand and what's blocking them — this is the only room where 585 is on the table, and Dario is one of the two people pinged. Dario is otherwise silent until 18:29, so him picking up the 585 half of that ping with the one detail a reviewer would want (nothing moved on the config surface) fits the thread, while leaving the actual new mechanism unstated.

*Still leaves open:* what the pause is actually computed from instead, and where the new window lives on the tracker

*Must appear literally:* `config.seconds_to_pause_on_rate_limit`, `10`

*Goes into the real conversation in #code-review on 2025-03-17, after 12:51 nikolai:*

```
09:00  konrad: Weekly update is out for the week of Mar 10
09:00  konrad: Asked Dario and Emil specifically about where PR 565, PR 566, PR 579, PR 585 stand and what's blocking them, also flagged PR 581 and PR 583 for triage
09:00  konrad: And PR 592 is up for eyes whenever someone has a moment, it's cleanup work touching examples-cookbooks
09:00  konrad: @Dario, if you get a minute this morning, would really appreciate a look at PR 592 before this gets buried under the week
09:00  konrad: It's just cleanup on examples-cookbooks, nothing structural, but I'd like a second pair of eyes before I merge
09:23  nikolai: For PR 581 and 583, are we trying to land those before a specific release cut or are they just merge-when-ready?
09:24  nikolai: Ok, answering my own question - Konrad's weekly says triage PR 581 and 583 this week, so they're release-scoped not just whenever.
11:54  nils: @Gideon, where does PR 581 stand?
12:35  emil: gotcha
12:36  emil: PR 579 is in decent shape on my end, just needs a review pass before I'd call it merge-ready
12:36  emil: Still want to sort out where it sits relative to PR 565 and PR 566 since there's overlap on the openai/deepseek side
12:51  nikolai: Tried to pull up the v0.1.20 release notes and there's no page yet, so I honestly don't know if PR 583 is even in scope for this cut
12:51  nikolai: Do we have enough to call a decision on the config PRs today or are we waiting on that first?   <-- THE REMARK GOES HERE
18:23  gideon: @Nils PR 581 is ready for review, waiting on a pass
18:29  dario: @Nikolai are the config PRs actually gated on the release notes, or can we call them separately?
18:29  nikolai: No, not gated - I was just noting the notes aren't there yet and wasn't sure if PR 583 was in scope
18:30  nikolai: Anyway PR 581 and 583 both look review-ready at this point, but we haven't actually called merge or defer on either of them
18:30  nikolai: The v0.1.20 release notes page isn't up yet - @Dario are those landing today?
```

#### `g3.r2.s4c` — exclusions_or_crossover

**dario**, 2025-03-31, #code-review

> @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week.

*What a reader should take from it:* the wait must not be computed from elapsed time since the last rate-limit error

*Step it builds toward:* `g3.r2.sc4` — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Drafted as:* we work the pause out from now minus time_of_last_rate_limit_error, so a 429 followed by a slow stretch of work costs nothing at all. bit me twice this week.

*Why there:* Dermot opened that day saying he has "the retry logic in pr 585 under review and a few questions on the simplestrat recipe in pr 598 before I can sign off on either" — so the retry/backoff code is the live review item in that room, and nobody has yet said anything concrete about what's wrong with it. Dario is already in the channel flagging a concrete thing that bit him repeatedly (the cache dir, "Second time this month"), so a second "this bit me twice this week" observation on the other PR under review is exactly his register and gives Dermot something to sign off on or not. Nothing said contradicts it or already makes the point.

*Still leaves open:* what the pause should be computed from instead, and what becomes of the configured pause length

*Must appear literally:* `time_of_last_rate_limit_error`

*Goes into the real conversation in #code-review on 2025-03-31, after 11:51 dario:*

```
09:00  dermot: pr 565 and the openai client work are in decent shape, I've got the retry logic in pr 585 under review and a few questions on the simplestrat recipe i
09:00  dermot: @Dario Kestrel did you push a new revision to pr 565 over the weekend, I'm seeing something about a moved hook and a bypass option?
09:38  dermot: @Emil Brandvold have you had a look at the latest on pr 565 yet?
09:56  dermot: does the cache directory get created automatically or does it need to exist first?
10:20  dermot: in pr 598, is the simplestrat recipe intended to replace the existing strategy or does it sit alongside?
10:50  dermot: for pr 583, if the metadata db param is disabled does it skip schema init entirely or just skip writes?
11:18  emil: not yet, pulling it up now
11:51  dario: It needs to exist first, and that's actually the thing I wanted to flag
11:51  dario: Fresh CI container, nothing has ever run in it, pre-flight estimate step threw a FileNotFoundError on the cache dir
11:51  dario: I put a mkdir -p in the workflow to unblock it, but I hate that because now the estimate step is the thing that creates the cache Second time this mon   <-- THE REMARK GOES HERE
12:34  emil: The mkdir in the workflow is the wrong home for that, if the code expects a cache dir it should create it on first use, not lean on whatever CI step h
12:54  emil: Looked at the revision, moving the hook I can live with, but I'm less sure about the bypass
12:54  emil: Whatever we name that param is going to tell users a lot about when they're supposed to use it, and right now it doesn't
14:07  dario: @Emil Brandvold do you want to land on the bypass naming before this closes today, or leave it open?
14:17  emil: I'll land on it today, give me a bit to look at the options and I'll have something by end of afternoon.
14:35  dario: Worth thinking about whether the name signals "for debugging" vs "a legitimate production option" - those would probably land differently for users
15:07  dario: Fixing the cache dir creation at the code level and landing the bypass naming in the same pass would be cleaner than two separate PRs.
```

#### `g3.r2.s4a` — exclusions_or_crossover

**gideon**, 2025-04-11, #incidents

> so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh

*What a reader should take from it:* the fixed ten-second pause is too short and does not match what the failure warranted

*Step it builds toward:* `g3.r2.sc4` — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Drafted as:* 429 at 12:04:01 and we were hammering again at 12:04:11, still throttled. Ten flat seconds is not what that provider was asking for.

*Why there:* No listed room is discussing rate limiting or retry timing. code-review|2025-04-01 explicitly rules the retry logic out as the cause of the gemini bug; pipeline|2025-04-22's retry mention is about malformed Anthropic token counts hitting the retry path, a different failure. help|2025-03-27 is the closest domain (Gideon on unhandled provider 404s in online-request-processing) but that day already carries two open threads, and nobody present is set up to answer the sibling question about where the wait should come from — the remark would sit unanswered. It needs its own thread: Gideon pulling timestamps out of a throttled run log, with Dario/Emil supplying Retry-After and the fate of the fixed delay knob.

*Still leaves open:* where the wait should come from instead, and what happens to the ten-second knob

*A new conversation in #incidents on 2025-04-11:*

```
12:19  konrad: what actually killed the 12:04 run, was it us or their side
12:21  dermot: their side to start. 429 at 12:04:01. then we came straight back at 12:04:11 and got throttled again
12:22  konrad: ten seconds. thats our own sleep then?
12:23  dermot: yeah, flat ten on every attempt. constant somewhere in the retry path, if i had to guess
12:24  konrad: but they tell us how long to wait, no? presumably on the response
12:26  gideon: ya they do and we throw it away. so basically ten flat seconds is not what that provider was asking for tbh, we take their number off the response and sleep that
12:27  dermot: yeah ok. nobodys touched that constant yet though
12:29  konrad: right. that run had three of them before it gave up, all ten apart
```

#### `g3.r2.s4b` — exclusions_or_crossover

**konrad**, 2025-05-30, #code-review

> look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff

*What a reader should take from it:* the pause is derived per failure from its computed backoff rather than from a configured number

*Step it builds toward:* `g3.r2.sc4` — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Drafted as:* Raising the pause to 45 so it covers the worst 429 means every trivial one costs 45 too; the wait should come from that failure's own backoff.

*Why there:* That thread is already stuck on exactly this: emil pasted `{"error": "dataset_not_ready", "retry_after": 60}` and said he's going back and forth on whether to retry, konrad asked at 11:20 whether the 60 is reliable or a rough estimate, and emil closes at 17:21 with "not sure if that 60 is coming from the viewer or if I'm the one setting it." Konrad is the one who opened the "where does that number come from" line, so him answering his own question — a single fixed pause sized for the worst case taxes every cheap failure, so derive it per failure — lands on a live, unresolved point rather than arriving from nowhere. It leaves open what emil's sibling point covers, whether the number stays configured at all and how the wait gets carried around.

*Still leaves open:* whether the knob stays in the config at all, and how the wait is then stored and asked for

*Goes into the real conversation in #code-review on 2025-05-30, after 17:21 emil:*

```
09:00  konrad: Finetuning is moving along on my end, but PR 653 and PR 663 have been sitting unreviewed for a while now and both touch my service
09:11  nikolai: Both 653 and 663 are ready on my end, no blockers, just waiting on someone to take a look
09:11  nikolai: The torch fix is pretty contained but the finetuning client is the one I'd rather not let drift much longer
09:54  konrad: @Emil Brandvold what's the situation with PR 652, that one's been open the longest by a fair margin.
10:18  nikolai: @Emil Brandvold if you've got cycles, 653 and 663 are both ready for a look too.
10:18  nikolai: Actually, separate thing: does anyone know for certain whether the sandbox guarantees survive if you bring your own image?
10:18  nikolai: I said "should do" at the demo and I'm not confident that was right
10:26  konrad: oh, that's actually my area
10:45  nikolai: So does it?
10:45  nikolai: Survive a caller-supplied image?
11:04  emil: 652's been on me, the viewer returns this for datasets that haven't finished indexing and I've been going back and forth on whether to retry or let th
11:20  konrad: Is the `retry_after` value reliable or just a rough estimate?
11:20  konrad: And what does the caller get today if they hit this before indexing finishes, an exception?
17:20  nikolai: Sorry, I meant to come back on this earlier - the sandbox guarantees don't hold if you bring your own image, I went and checked after the demo.
17:20  nikolai: I told someone at the demo "should do" and that was wrong, just wanted that on record before the weekend.
17:21  emil: Not sure if that 60 is coming from the viewer or if I'm the one setting it.   <-- THE REMARK GOES HERE
```

#### `g3.r2.s4d` — exclusions_or_crossover

**nikolai**, 2025-06-11, thread:new|g3.r2.s4d

> A few user configs in the wild still set seconds_to_pause_on_rate_limit, so it stays in config.py with its default of 10 unchanged, even once nothing reads it.

*What a reader should take from it:* the configured pause length stays in config.py unread, for compatibility

*Step it builds toward:* `g3.r2.sc4` — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Drafted as:* A few user configs in the wild set seconds_to_pause_on_rate_limit, so leave it sitting in config.py even once nothing reads it any more.

*Why there:* Neither listed thread is chewing on retry or rate-limit behaviour. The Jun 16 recap is a one-question mail — does PR 653 land or get closed heading into maintenance mode — and a deprecation footnote about a config key would change the subject and draw no reply. The Apr 16 thread is Nikolai's Docker image-pinning notes, where the live items are the sandbox repo's published tags and the read-only workspace; nothing there touches config.py or pausing. The remark also depends on a sibling supplying what drives the pause instead, and neither room has anyone positioned to answer that.

*Still leaves open:* what does drive the pause once this stops being read

*Must appear literally:* `10`, `A`, `config.py`, `seconds_to_pause_on_rate_limit`

*A new thread — **429 handling in the online request processor**, 2025-06-11:*

```
From: emil  To: nikolai, dario
Nikolai — the long gemini run I kicked off friday spent most of saturday doing nothing. I pulled the logs this morning and it is 429s the whole way down, we hit one, we sleep the fixed pause, we retry into the same closed window, we hit another. Throughput never recovers, it just limps until the request budget is gone.

So if I am reading the code right, the pause is a single global stall for the whole run and not something that scales per request? That was my guess but I am not entirely sure I 

From: nikolai  To: emil, dario
yep youre reading it right

one 429 stalls everything for the fixed pause then we go again with no memory of how many times weve been told no
that was solid enough when the windows were published and static
they arent now so we sleep 10s into a window that wants a minute and spend the retry budget on calls that were never landing

what i want is backoff per request off the 429 itself doubling from a small base with jitter and a ceiling so one slow provider doesnt hold the whole run hostage
the r

From: dario  To: nikolai, emil
makes sense, and honestly the jitter part matters more than the doubling does. every worker waking up at the same instant is how we got the sawtooth in the first place, i think, so if they all come back staggered we probably stop hammering the boundary.

one thing i want to be clear on before you write it — is the ceiling per attempt or is it a total elapsed thing across the whole retry chain? those behave very differently on a long run and i can see arguments either way. actually if it is per a

From: emil  To: nikolai, dario
yup, that all sounds right to me. I will re-run the gemini job once it is in and see whether saturday repeats itself.

```

### Herrings — believed at the time, overturned later

#### `g3.r2.h1` — herring

**dario**, 2025-01-21, #releases

> in any case i've settled on plain assignment for the horizon: `throttle_cooldown_until = now + delay_seconds` on every THROTTLE verdict, the most recent rate-limit failure is the one that sets the pause

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* settled on the horizon write: `throttle_cooldown_until = now + delay_seconds`, plain assignment on every throttle verdict. the most recent rate-limit failure is the one that sets the pause.

*Why there:* None of these rooms is chewing on retry backoff timing. The closest, #pipeline 2025-02-19, is about whether PR 518's logger survives concurrent retries — a stress-testing and sign-off question, not how a cooldown horizon gets written; a settled design decision about `throttle_cooldown_until` would land there with nobody to answer it. #code-review 2025-03-06 touches Gemini rate limits only as an already-merged write-up (PR 578, the failed-count fix) while the live thread is PR 581 and the 565/566 coverage check. The remark reports the resolution of a design argument — plain assignment versus extending the existing horizon on each THROTTLE verdict — and that argument was never had anywhere in these logs. It needs its own thread: dario owns online-request-processing, the Gemini 429 work is what forces the question, and emil/gideon are the ones who'd push back on whether a later short delay should be allowed to shorten a pause already in effect.

*A new conversation in #releases on 2025-01-21:*

```
15:09  konrad: question on the throttle horizon. when a THROTTLE verdict comes back do we push the cooldown out, or keep whichever is later
15:11  dario: plain assignment, i think. throttle_cooldown_until = now + delay_seconds and thats the whole of it
15:12  konrad: even when the old one sits further out? we lose the longer wait then
15:14  dario: mhm. thats delibrate to be honest, the most recent rate-limit failure is the one that sets the pause
15:15  dermot: so no max(), straight overwrite. does that happen on every THROTTLE verdict or only once the horizon has lapsed
15:16  dario: every one. in any case i've settled on that for the horizon
15:18  konrad: right. today it still takes the max i am fairly sure, at least in the version i read friday
15:19  dermot: yeah, that bit is untouched
```

#### `g3.r2.h2` — herring

**konrad**, 2025-01-22, #cookbooks

> Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there.

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* Right, and that's what I reviewed: last THROTTLE verdict wins, it just overwrites the field. One assignment, no comparison against whatever was there before.

*Why there:* None of the eight rooms is anywhere near throttling, 429 handling, or cooldown state — they're about cookbook examples, the progress bar UI, token-estimate int wrapping, batch param routing, and release sign-offs. The closest adjacency is PR 387 (max_tokens capacity blocking) on 2025-01-21, but that day is a scheduling/triage thread, Dermot and Dario are the ones who reviewed 387, and Konrad is explicitly waiting on PR 394 in the cookbook. The remark opens with "right, and that's what I reviewed", so it needs someone directly above describing the overwrite behaviour and Konrad confirming it from an actual review pass — no listed thread supplies that setup, so dropping it in would change the subject and draw no reply.

*A new conversation in #cookbooks on 2025-01-22:*

```
15:29  dermot: the throttle cooldown from the retry pass - if two verdicts come back in one batch does the later one win, or do we keep the longer window
15:32  konrad: later one wins. its one assignment on throttle_cooldown_until, whatever the last THROTTLE verdict carries
15:33  dermot: so a short window landing after a long one shortens it
15:35  konrad: right, thats the part i reviewd. no comparison against whats already sitting there
15:39  nikolai: yep thats the 9am run going back out early then
15:41  nikolai: so keep whichever is further out
15:42  konrad: mhm. compare first, only push it later, never back
15:45  dermot: does the clear-on-success path hit that same line
15:47  konrad: no thats its own reset, sets it to none
```

#### `g3.r2.rev1` — rule

**dario**, 2025-04-08, #pipeline

> dropped the plain `throttle_cooldown_until = now + delay_seconds` write — a 1.0s throttle landing behind a 40s one pulled the horizon in and we flooded again. it's `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` now, the window only moves out.

*A herring: stated as settled at the time, overturned later (from ?).*

*Why there:* That day is already inside the retry/rate-limit layer: dermot asks at 14:40 whether absent DeepSeek rate limit headers affect the retry logic or degrade gracefully, and dario says at 15:06 he wants to check whether the retry layer handles absent headers cleanly before signing off, then syncs with emil. A finding-and-fix from dario in the throttle path late in the day lands as the product of that pass, answers dermot's open question about how that layer behaves, and nobody has made the point already. It's also his own code area — he's the one who'd report the write being changed.

*Must appear literally:* `throttle_cooldown_until`, `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, `delay_seconds`

*Goes into the real conversation in #pipeline on 2025-04-08, after 17:12 dario:*

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
17:12  dario: Ok, checking now whether the resume pass is actually wired to read from it   <-- THE REMARK GOES HERE
17:31  gideon: Still waiting on Emil's registry result to close out the provider paths on my end
```

> **Problems:** longer than one remark

#### `g3.r2.rev2` — rule

**konrad**, 2025-03-24, #cookbooks

> look, the last-THROTTLE-wins overwrite I flagged is gone, second 429 had a tiny backof and overwrote a 40s window down under a second. compares now: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* That last-THROTTLE-wins overwrite I reviewed is gone — the second 429 came back with a tiny backof and overwrote a 40s window down under a second. It compares now: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`.

*Why there:* None of the listed rooms is reviewing retry/backoff code. The closest is #engineering 2025-03-19, but that thread is about whether the output-token count fix shifted the *estimation* path feeding the throttle check, plus the postmortem's headroom miscalculation on kluster.ai DeepSeek — a different mechanism from a 429 cooldown horizon being clobbered, and there is no PR under review there for Konrad to have reviewed. Konrad's role that day is asking after Nils's Mistral blocker and making the call to run the throttle check separately; a landed-fix report from him would change the subject and draw no reply. The other candidates are gemini batch parts keys, o3 structured outputs, stopping criterion, GEPA null scores and a finetuning test-suite fix — nothing about throttling at all. What should exist is the follow-up: gideon's 2025-03-19 throttle check in online-request-processing was the open postmortem action item, and the natural next beat is a #code-review thread the week after where that check surfaced the last-THROTTLE-wins overwrite, Konrad reviewed the PR fixing it, and the author pushed a second round. That thread would also cover whether the postmortem item can be closed on this merge and whether batch-mode has the same overwrite.

*Must appear literally:* `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, `THROTTLE`

*A new conversation in #cookbooks on 2025-03-24:*

```
15:12  nikolai: konrad that throttle cooldown you flagged in review is it still a straight assign
15:14  konrad: no, that overwrite is gone. look, it bit us on the retry run — second 429 came back with a tiny backof and it stomped the window we already had
15:16  nikolai: stomped it from what to what
15:17  konrad: 40s down to under a second. so we went straight back at them, presumably that is why the run looked like that
15:19  dermot: right, that's the part i reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there
15:20  nikolai: so what does it compare against now
15:24  konrad: itself. `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` — a short window cant win over a longer one anymore
15:24  dermot: yeah ok. nobodys cut the patch yet, it sits behind the batch retry ticket if i had to guess
15:26  nikolai: the 40s is that retry-after or do we compute it
15:27  konrad: header when they send one. ours only when they dont
```

> **Problems:** longer than one remark

