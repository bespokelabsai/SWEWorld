# Clues for g3 — Failure-class retry policy for online request processors

42 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

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
| 2025-03-19 | #pipeline *(new)* | nils | The verdict logged attempts_left as -1 again overnight. i think whatever number we hand back there has to floor at zero, so we're flooring it. | `failure_behavior`, `observability` |
| 2025-03-19 | #releases *(new)* | dario | honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out | `rule` |
| 2025-03-20 | #cookbooks *(new)* | konrad | Look, I said 429s never cost a request budget - that's out, a dead key looped for hours. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6 now, decide takes throttle_waivers_left and reports throttle_waivers_after. | `rule`, `scope` |
| 2025-03-21 | #code-review | konrad | look, while retry scope is open - same request came back finish_reason length four times last night and spent four attempts, a broken payload shouldn't get that many goes | `rule`, `observability` |
| 2025-03-21 | #code-review *(new)* | nils | let me think - no, timeouts are fine as they stand, one attempt off the budget per failure. i'd rather we didn't get clever with that path. | `rule` |
| 2025-03-21 | #pipeline *(new)* | gideon | so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it. | `rule` |
| 2025-03-21 | #cookbooks *(new)* | konrad | Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again. | `rule` |
| 2025-03-24 | #releases *(new)* | emil | honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock. | `scope` |
| 2025-03-24 | #cookbooks *(new)* | konrad | look, the last-THROTTLE-wins overwrite I flagged is gone, second 429 had a tiny backof and overwrote a 40s window down under a second. compares now: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` | `rule` |
| 2025-03-25 | #pipeline | emil | @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, first 429 sets tracker.throttle_cooldown_until to 1005.0, and a second worth 1.0 has to leave it there. | `observability`, `rule` |
| 2025-03-31 | #releases *(new)* | dermot | yeah, for a schema failure the counter is the whole job, that path has no reason to be moving stamps or windows around. | `scope` |
| 2025-03-31 | #code-review | dario | @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week. | `exclusions_or_crossover` |
| 2025-04-02 | #pipeline *(new)* | dario | honestly i'd rather not put a new knob on OnlineRequestProcessorConfig for this, max_retries still seeds attempts_left and everything else stays on the request | `scope` |
| 2025-04-03 | #code-review *(new)* | konrad | Look, cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted. | `observability`, `exclusions_or_crossover` |
| 2025-04-07 | #pipeline | dermot | on the retry side: the helper handed back -3.2 once the window was behind us, and 4.999999999998 before that — that should be 0.0 clamped and three decimals. | `rule`, `observability` |
| 2025-04-07 | #general *(new)* | nils | A tracker nobody has throttled should answer 0.0 however far ahead you ask — window at 1005.0 gives 3.0 at 1002.0, 0.5 at 1004.5, 0.0 at 1005.0. | `observability` |
| 2025-04-08 | #engineering | dario | that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request. | `rule` |
| 2025-04-08 | #pipeline | dario | dropped the plain `throttle_cooldown_until = now + delay_seconds` write — a 1.0s throttle landing behind a 40s one pulled the horizon in and we flooded again. it's `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` now, the window only moves out. | `rule` |
| 2025-04-09 | #incidents *(new)* | dario | that "throttle costs zero attempts" line i settled in review is gone — a permanently throttled key re-queued for hours. 429 is free while throttle_waivers_left > 0, then decide charges 1. | `rule`, `failure_behavior` |
| 2025-04-09 | #pipeline | gideon | so basically one thing did turn up in that pass: a timeout landed betwen two 429s and our last-rate-limit stamp jumped to it, graph showed us throttled when the provider was perfectly happy | `scope` |
| 2025-04-10 | #pipeline | gideon | ya, bare 429s is exactly the shape that bites us. The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all. | `exclusions_or_crossover` |
| 2025-04-11 | #incidents *(new)* | gideon | so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh | `exclusions_or_crossover` |
| 2025-04-15 | #engineering *(new)* | konrad | look, one shared counter for the run means the first bad minute eats everyones free passes, each request should walk in with its own full set. | `scope` |
| 2025-04-16 | #code-review *(new)* | dario | honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all | `failure_behavior` |
| 2025-04-21 | #general *(new)* | nils | let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both. | `rule`, `scope` |
| 2025-04-23 | thread:new|g3.r1.l8 *(new)* | emil | yup — once a request has used up its free passes the next 429 costs it an attempt like anything else, otherwise a dead key just loops forever. | `rule` |
| 2025-04-24 | #engineering | gideon | while you're in there - it's throttle_waivers_left, not throttle_waviers_left like the branch has it, and it hangs off APIRequest, the tracker has no buisness knowing about it | `scope` |
| 2025-04-24 | #engineering *(new)* | dermot | yeah, on a bad key we empty the attempts and stop: `invalid api key` at seven left gives terminal:abort, attempts to zero, passes untouched at six. | `exclusions_or_crossover`, `observability` |
| 2025-04-24 | #code-review *(new)* | emil | went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out. | `failure_behavior` |
| 2025-04-25 | page:meetings/weekly-notes-week-of-mar-24.md | nikolai | on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request  still moving so dont link it yet | `rule`, `observability` |
| 2025-04-29 | #engineering *(new)* | dermot | we write attempts_left back from the verdict onto the request, but never the pass count, so a request quietly gets its full set again on the next failure. | `rule`, `scope` |
| 2025-05-13 | #pipeline *(new)* | emil | honestly two attempts off for a malformed-output failure feels about right to me — one is too generous, and binning the row on the spot is too harsh. | `rule` |
| 2025-05-30 | #code-review | konrad | look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff | `exclusions_or_crossover` |
| 2025-06-04 | #engineering *(new)* | nikolai | decide only sees attempts_made and attempts_left so it cant tell whether a 429 is free the requests remaining passes has to go in as a third kwarg | `rule` |
| 2025-06-11 | thread:new|g3.r1.l12 *(new)* | nikolai | ran it with the wrong key and each request retried five more times before giving up once auth is the problem the attempts on the clock are worth nothing | `exclusions_or_crossover` |
| 2025-06-11 | thread:new|g3.r2.s4d *(new)* | nikolai | A few user configs in the wild still set seconds_to_pause_on_rate_limit so it stays in config.py even once nothing reads it | `exclusions_or_crossover` |
| 2025-06-18 | page:meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md | nikolai | tracker fields keep shifting under this one order right now is num_other_errors then time_of_last_rate_limit_error then throttle_cooldown_until at 0.0 on a fresh tracker still moving dont quote me | `rule` |

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

> **Spread:** g3.r1.sc1: two remarks in #code-review within 0 days; g3.r1.sc2: two remarks in #engineering within 9 days; g3.r1.sc5: two remarks in #pipeline within 2 days; g3.r1.sc5: two remarks in #code-review within 8 days

### The remarks, by the step they build

### g3.r1.sc1 — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Nobody says:* If one class is said to deserve more strikes than another and a third deserves none, the deduction is looked up per class instead of being a single fixed number.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g3.r1.l1` — rule, observability

**konrad**, 2025-03-21, #code-review

> look, while retry scope is open - same request came back finish_reason length four times last night and spent four attempts, a broken payload shouldn't get that many goes

*What a reader should take from it:* the team agrees a contract failure should be charged more than one attempt

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* same request came back "finish_reason was length" four times tonight and spent four attempts doing it, a broken payload shouldn't get that many goes.

*Why there:* That thread is actively stuck on retry handling scope — Nils asks whether PR 585 folds retry handling in with batch submission, and Emil says he's going back and forth on it and wants the scope settled "beofre anyone extends it." Konrad is in the room and has already said he wants a decision today one way or the other. A concrete case of the same request burning four attempts on a finish_reason failure lands as evidence that retry handling isn't just a placement question — it doesn't distinguish a transport failure from a broken payload — which complicates the scope call rather than restating it. Nobody has made this point yet; the only retry talk so far is where the code lives, not what a failure costs.

*Still leaves open:* how many attempts a malformed-output failure should actually be charged, and what any other class costs

*Must appear literally:* `finish_reason`

*Goes into the real conversation in #code-review on 2025-03-21, after 12:26 emil:*

```
09:00  nils: PR 584 (Mistral batch) is ready for review, touches batch-mode and provider integrations
09:00  nils: Not blocking a release but i'd like to settle before end of day whether we're merging this week or pushing to next
09:00  nils: @Emil is PR 585 meant to fold retry handling in with batch submission, or is that out of scope for it?
11:00  konrad: Sorry, just saw this
11:00  konrad: I've been sitting on PR 584 as well so I'm glad Nils raised it - would be good to get a decision today one way or the other
11:39  emil: @Nils that's the thing I'm not entirely sure about. Been going back and forth on whether retry handling belongs in PR 585 or stays separate, and I'd w
11:46  nils: fair enough
11:46  nils: WS-047 doesn't have a spec page on the wiki yet, couldn't find it anywhere when I looked
11:50  dario: while we're on PRs, @Emil, does PR 579 cover the same ground as PR 565 and PR 566, or are all three meant to land separately?
12:18  emil: Sent a note to Dario and Nils on the batch status persistence doc
12:18  emil: One house rule I want on record from it: for anything that only reports on the cache, connect to the metadata db with mode=ro
12:18  emil: @Nils, free this afternoon to settle the PR 584 call?
12:26  emil: The online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate
12:26  emil: Does retry handling in PR 585 need to account for that, or is it working above that layer?   <-- THE REMARK GOES HERE
12:41  emil: A user pointed CURATOR_CACHE_DIR at /mnt/shared expecting everything a rerun needs to live under that path. Request and response files follow it, the 
12:41  emil: Is that gap tracked anywhere as an issue?
12:48  nils: @Emil yes, free this afternoon
12:48  nils: PR 584 is ready on my end, just sitting there waiting on the merge or defer call
12:48  nils: does WS-047 need a full wiki page, or is a tracked issue sufficient for defining the CI scope?
```

#### `g3.r1.l3` — rule

**nils**, 2025-03-21, #code-review

> let me think - no, timeouts are fine as they stand, one attempt off the budget per failure. i'd rather we didn't get clever with that path.

*What a reader should take from it:* the team agrees a transient failure keeps costing exactly one attempt

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* timeouts are fine the way they are, one attempt off the budget per failure, please don't get clever with that path.

*Why there:* Neither 2025-03-20 nor 2025-03-25 in #code-review is chewing on anything this answers. Both days are review-queue logistics: who picks up PR 584, whether 585/579/468/565 are targeted or deferred, and the fact that WS-047 has no ticket or wiki page. No message in either thread mentions retries, timeouts, attempt budgets, or any runtime behavior at all — the PR 584 review never gets past "can someone look at it." Worse, "please don't get clever with that path" is a reply to a proposal, and no one in either room has proposed changing retry accounting, so the remark would arrive from nowhere, settle a question nobody asked, and get no reaction. The conversation that should have existed is the review thread where the retry path was actually contested: Nils has PR 584 (Mistral batch processor) in flight and Emil owns batch-mode, so a PR touching retry/backoff accounting — proposing that transient failures stop counting against max_attempts — would land in #code-review with Nils, Emil, and Dario. That thread would also cover what non-timeout failures are charged, the half this remark is meant to leave open.

*Still leaves open:* what anything other than a timeout is charged

*A new conversation in #code-review on 2025-03-21:*

```
```

#### `g3.r1.l4` — rule

**dario**, 2025-04-08, #engineering

> that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request.

*What a reader should take from it:* the team agrees a rate-limit failure should not come out of the request's attempt budget

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* burned the whole retry budget on 429s last night against a throttled key, and not one of those failures was about my request.

*Why there:* Nikolai has just pasted a failed_requests.jsonl line that literally carries `"error": "RateLimitError"` alongside `"attempt": 2`, and the room is arguing about whether that schema is enough to debug a batch failure. Dario is the person tracking the rate-limit layer that day (he raises it at 11:50, 13:42, 14:46), so him reacting to a 429 being logged as a consumed attempt lands squarely in his lane and complicates the field-layout discussion rather than changing the subject. It also doesn't step on anyone: nobody in that thread has questioned what counts as an attempt, and Emil/Dermot's header anomalies are a separate strand.

*Still leaves open:* what a 429 should be charged against instead, and whether that is unlimited

*Goes into the real conversation in #engineering on 2025-04-08, after 09:13 nikolai:*

```
09:00  nikolai: failed_requests.jsonl is wired up on my end
09:00  nikolai: Not totally sure the current field layout is what anyone downstream actually needs for debugging batch failures though
09:03  dermot: @Nikolai what fields does it have right now?
09:13  nikolai: Each line looks roughly like this:

```json
{"row_idx": 14, "error": "RateLimitError", "provider": "openai", "model": "gpt-4o", "attempt": 2}
```   <-- THE REMARK GOES HERE
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
12:51  nikolai: @Emil, can you keep that on the list so it doesn't get lost?
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

#### `g3.r1.l2` — rule

**emil**, 2025-05-13, #pipeline

> honestly two attempts off for a malformed-output failure feels about right to me — one is too generous, and binning the row on the spot is too harsh.

*What a reader should take from it:* the team agrees a contract failure deducts two attempts

*Step it builds toward:* `g3.r1.sc1` — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*Drafted as:* two attempts off for a malformed-output failure feels right to me, one is too generous and binning it on the spot is too harsh.

*Why there:* None of the listed rooms is arguing about a retry attempt budget or how failure classes are charged against it. The closest neighbours only brush it: #engineering 2025-04-08 shows an `"attempt": 2` field in failed_requests.jsonl and Emil syncing with Dario on whether the retry layer copes with absent DeepSeek headers, and #code-review 2025-05-30 debates retry-vs-caller for `dataset_not_ready` — but neither has anyone proposing per-class attempt costs, so a verdict on "malformed output costs two attempts" would land with no question in front of it and no reaction after. The remark also presumes a settled vocabulary of failure classes (contract failure vs rate limit vs transport) that nobody in these transcripts has introduced yet. What's missing is the conversation where the retry policy's accounting actually gets designed: Nikolai's structured-output validation check (pushed 2025-04-29) starts rejecting responses, those rejections retry on the same uniform budget as a 429, and someone notices a row can burn its whole allowance on a model that will never produce valid output. That's #pipeline, where Emil and Dermot already own the rate-limit and header work, and it's where Emil settling one class while Dario or Nikolai works out the rest of the table reads naturally.

*Still leaves open:* what the other classes cost, and whether anything is ever charged nothing

*A new conversation in #pipeline on 2025-05-13:*

```
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

> on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request  still moving so dont link it yet

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

*4 remarks — 1 reporting the problem, 3 settling the design.*

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
```

#### `g3.r1.l17` — failure_behavior, observability

**nils**, 2025-03-19, #pipeline

> The verdict logged attempts_left as -1 again overnight. i think whatever number we hand back there has to floor at zero, so we're flooring it.

*What a reader should take from it:* the team agrees the post-failure budget on the verdict is floored at zero

*Step it builds toward:* `g3.r1.sc5` — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*Drafted as:* The verdict logged attempts_left as -1 again last night, whatever number we hand back should stop at zero.

*Why there:* Neither listed room is anywhere near retry semantics. The 2025-03-19 #pipeline day is fully occupied with the Gemini unicode fix, the Mistral api_key blocker on PR 584, and the two outstanding postmortem checks (batch-mode estimation, throttle path in online-request-processing) — rate-limiting adjacent, but nobody there is discussing a retry verdict, a per-attempt budget, or what gets logged after a failed call. Dropping a field-level decision about attempts_left into that day would land between Gideon chasing his throttle check and Dermot closing out the day, and get no reaction from anyone. The 2025-03-25 #code-review day is pure release triage — which PRs target the next release, WS-047 having no scope written — and has no code substance in it at all; a symptom-from-last-night's-logs remark would be the only technical claim in the room. The conversation this belongs to is the one where the retry/backoff verdict shape is actually being settled: Nils reading overnight logs the morning after the throttle path came back clean, with Gideon (owner of online-request-processing, where the retry path lives) and Dermot, working out what the verdict carries after a call is exhausted. That thread also carries the sibling question — when the counter goes negative in the first place and what else the verdict reports then — which is exactly the part this remark must not resolve.

*Still leaves open:* when the number goes under zero in the first place and what else the verdict should say then

*Must appear literally:* `The`, `attempts_left`

*A new conversation in #pipeline on 2025-03-19:*

```
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
```

#### `g3.r1.h2` — herring

**konrad**, 2025-03-12, #engineering

> right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* Right — and there's no ceiling on that. A rate-limited request keeps its full budget however many 429s it eats; only TRANSIENT and CONTRACT deduct.

*Why there:* The remark confirms an already-agreed retry taxonomy (THROTTLE/TRANSIENT/CONTRACT) and states the budget rule as settled. No listed room has that vocabulary in play. The nearest, #engineering 2025-03-03, is at the wrong stage: Emil is still claiming the Gemini rate-limit work and deciding it lives under issues 207 and 233, so no budget policy exists to confirm — Konrad stating one there would be manufacturing a decision mid-triage. The code-review days are PR queue status, cookbooks is sandbox uid and broken examples, #general 2025-03-10 is Nils' onboarding. It would land with no reply in any of them. The thread that should exist is the follow-on where Emil's retry handling from 207/233 gets reviewed and the categories are pinned down; Konrad asking what counts against a retry and reading the answer back is exactly his role in these rooms.

*A new conversation in #engineering on 2025-03-12:*

```
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

> **Spread:** g3.r2.sc3: two remarks in #releases within 7 days

### The remarks, by the step they build

### g3.r2.sc1 — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Nobody says:* if the stored end-time is already behind you there is nothing left to wait, so the pause point can ask a stored deadline the one question it actually cares about.

*4 remarks — 1 reporting the problem, 3 settling the design.*

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
```

> **Problems:** describes asking rather than settling

#### `g3.r2.s1c` — rule, observability

**dermot**, 2025-04-07, #pipeline

> on the retry side: the helper handed back -3.2 once the window was behind us, and 4.999999999998 before that — that should be 0.0 clamped and three decimals.

*What a reader should take from it:* the remaining-wait number is clamped at zero and rounded to three decimals

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* the helper handed back -3.2 once the window was behind us, and 4.999999999998 before that; i want 0.0 in the first case and three decimals in the second.

*Why there:* dermot opened that day saying he wanted to confirm the gemini batch changes don't regress cost accounting or retry logic before calling PR 614 done — he is the only person in any of these rooms who has retry logic on his plate, and this is him reporting back on his own stated check. The thread then splits: gideon takes the cost-accounting half (the 10x resume case) while dermot's retry half never gets its result stated, so a finding from him lands in a gap the room already left open rather than changing the subject. It doesn't collide with anything: nobody else has touched the remaining-wait helper, and the window itself stays unexplained, which the resume/config discussion around it makes unremarkable.

*Still leaves open:* what the window is, where it is stored, and what puts it there

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

> A tracker nobody has throttled should answer 0.0 however far ahead you ask — window at 1005.0 gives 3.0 at 1002.0, 0.5 at 1004.5, 0.0 at 1005.0.

*What a reader should take from it:* an untouched tracker answers zero, and otherwise the answer is the window minus the time asked about

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* A tracker nobody has throttled should answer 0.0 however far ahead you ask. window at 1005.0: 3.0 at 1002.0, 0.5 at 1004.5, 0.0 at 1005.0.

*Why there:* Both listed rooms are doing release-queue triage — reviewer assignment for PR 584, whether 565/566/579 sequence or land as reviewed, and the missing WS-047 spec. Neither has said anything about retries, 429s, cooldowns, or tracker semantics, so a numeric statement of what an unthrottled tracker returns answers nothing on the table and would sit there unremarked. The remark also depends on a sibling stating what sets the window to 1005.0 and what later failures do to it, and there is no room in either day for that sibling either — the whole exchange is absent, not just this line.

*Still leaves open:* what sets the window to 1005.0 in the first place and what happens to it on later failures

*Must appear literally:* `A`, `1005.0`, `1002.0`, `1004.5`, `3.0`, `0.5`, `0.0`

*A new conversation in #general on 2025-04-07:*

```
```

> **Problems:** longer than one remark

#### `g3.r2.s1a` — rule

**nikolai**, 2025-06-18, page:meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md

> tracker fields keep shifting under this one order right now is num_other_errors then time_of_last_rate_limit_error then throttle_cooldown_until at 0.0 on a fresh tracker still moving dont quote me

*What a reader should take from it:* the tracker holds a second time value right after the rate-limit one, zero until something sets it

*Step it builds toward:* `g3.r2.sc1` — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*Drafted as:* tracker fields, current order: num_other_errors, time_of_last_rate_limit_error, throttle_cooldown_until (0.0 on a fresh tracker). still moving around, don't quote me on it.

*Why there:* The page's "Rate limit handling" section logs 207 and 233 as open and defers auto-detect past dormancy, i.e. the room's live question is what is actually moving in that area. Nikolai is the person who keeps dragging 207/233 back onto the list (Mar 17, Apr 21, Jun 16), so him leaving the current tracker field order under those notes complicates the "nothing happening here" reading without resolving what the second timestamp is for.

*Still leaves open:* what the second timestamp is for, who writes it, and what the pause point does with it

*Must appear literally:* `time_of_last_rate_limit_error`, `throttle_cooldown_until`

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

### g3.r2.sc2 — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Nobody says:* when two throttles overlap the longer wait is the one still owed, so a newly computed shorter deadline cannot be allowed to replace it.

*4 remarks — 0 reporting the problem, 4 settling the design.*

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
```

#### `g3.r2.s2c` — observability, rule

**emil**, 2025-03-25, #pipeline

> @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, first 429 sets tracker.throttle_cooldown_until to 1005.0, and a second worth 1.0 has to leave it there.

*What a reader should take from it:* with a pinned clock the window lands at now plus the backoff and a shorter second backoff leaves it unchanged

*Step it builds toward:* `g3.r2.sc2` — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*Drafted as:* Pinned the clock at 1000.0 and jitter at 0.25: first 429 puts tracker.throttle_cooldown_until at 1005.0, and a second one worth 1.0 has to leave it there.

*Why there:* nils asks at 10:19 "what does PR 585 actually change on the retry side" and the question dies unanswered — emil is the one answering everything else in that channel that day (Gemini test coverage, WS-047), so him coming back with what the retry test actually pins fits the shape of his other replies. It gives nils concrete behavior without settling the batch-vs-online half of his question, which stays open. Nothing already said covers the cooldown stamp, and dermot's separate "585 under review" line on 03-31 is about his own review pass, not test semantics.

*Still leaves open:* what the other stamp does at the same moment, and what non-throttle failures do to either

*Must appear literally:* `tracker.throttle_cooldown_until`, `1000.0`, `0.25`, `1005.0`, `1.0`

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
```

### g3.r2.sc3 — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Nobody says:* state that exists to describe throttling should only ever be written by throttling.

*3 remarks — 0 reporting the problem, 3 settling the design.*

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
```

> **Problems:** longer than one remark; contains its own forbidden term 'THROTTLE'

#### `g3.r2.s3c` — scope

**dermot**, 2025-03-31, #releases

> yeah, for a schema failure the counter is the whole job, that path has no reason to be moving stamps or windows around.

*What a reader should take from it:* non-throttle failures increment their counter and write nothing else

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* for a schema failure the counter is the whole job, it has no reason to be moving stamps or windows around.

*Why there:* None of these rooms is anywhere near retry/backoff state. The two #pipeline days are about cache fingerprints and about when the local batch record gets written; #help is capability checks and fail-open, #general is warn-vs-raise and abort-vs-fallback, #code-review is CI tags and PR status, and 05-13 is a logger.warning grep. A line distinguishing what a non-throttle failure path writes (counter only, no timestamps or cooldown windows) from what the throttle path writes has nothing above it to answer — there is no retry handler under discussion on any of those days, so it would change the subject and draw no reply. Dermot is the right person to say it, but he needs a thread where somebody has just proposed that every failure run through the same backoff bookkeeping. That conversation is the one that should exist: a run that kept getting 429s from the provider and never actually backed off, because validation errors were resetting the same cooldown state the throttle path uses — emil bringing the run in, dario walking the error classification in the request layer, dermot drawing the line between the two paths.

*Still leaves open:* what the throttle path does that this path skips, and why the clock matters here

*A new conversation in #releases on 2025-03-31:*

```
```

#### `g3.r2.s3b` — scope

**gideon**, 2025-04-09, #pipeline

> so basically one thing did turn up in that pass: a timeout landed betwen two 429s and our last-rate-limit stamp jumped to it, graph showed us throttled when the provider was perfectly happy

*What a reader should take from it:* a transient failure must not update the rate-limit timestamp

*Step it builds toward:* `g3.r2.sc3` — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*Drafted as:* A timeout landed between two 429s and our last-rate-limit stamp jumped to it; the graph showed us throttled when the provider was perfectly happy.

*Why there:* Gideon opened that day saying he was validating that rate limit and cost accounting surface cleanly through online-request-processing and that "nothing alarming so far" — the room is explicitly waiting on that pass before signing off on Dermot's provider changes. This is the finding from that pass, in his own workstream, complicating his own earlier all-clear. It sits right after his 14:36 catch-up burst where he's already reporting what he has and hasn't covered, and it doesn't step on the 03-19 throttle check, which was declared clean at the time.

*Still leaves open:* whether the other stored time moved too, and what a timeout should be doing instead

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

> **Problems:** longer than one remark

### g3.r2.sc4 — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Nobody says:* one fixed number cannot be both long enough for the worst throttle and short enough for the smallest one, so the wait has to come from the failure itself.

*4 remarks — 0 reporting the problem, 4 settling the design.*

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

> A few user configs in the wild still set seconds_to_pause_on_rate_limit so it stays in config.py even once nothing reads it

*What a reader should take from it:* the configured pause length stays in config.py unread, for compatibility

*Step it builds toward:* `g3.r2.sc4` — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*Drafted as:* A few user configs in the wild set seconds_to_pause_on_rate_limit, so leave it sitting in config.py even once nothing reads it any more.

*Why there:* Neither listed thread is chewing on retry or rate-limit behaviour. The Jun 16 recap is a one-question mail — does PR 653 land or get closed heading into maintenance mode — and a deprecation footnote about a config key would change the subject and draw no reply. The Apr 16 thread is Nikolai's Docker image-pinning notes, where the live items are the sandbox repo's published tags and the read-only workspace; nothing there touches config.py or pausing. The remark also depends on a sibling supplying what drives the pause instead, and neither room has anyone positioned to answer that.

*Still leaves open:* what does drive the pause once this stops being read

*Must appear literally:* `A`, `seconds_to_pause_on_rate_limit`, `config.py`

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
```

#### `g3.r2.h2` — herring

**konrad**, 2025-01-22, #cookbooks

> Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there.

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* Right, and that's what I reviewed: last THROTTLE verdict wins, it just overwrites the field. One assignment, no comparison against whatever was there before.

*Why there:* None of the eight rooms is anywhere near throttling, 429 handling, or cooldown state — they're about cookbook examples, the progress bar UI, token-estimate int wrapping, batch param routing, and release sign-offs. The closest adjacency is PR 387 (max_tokens capacity blocking) on 2025-01-21, but that day is a scheduling/triage thread, Dermot and Dario are the ones who reviewed 387, and Konrad is explicitly waiting on PR 394 in the cookbook. The remark opens with "right, and that's what I reviewed", so it needs someone directly above describing the overwrite behaviour and Konrad confirming it from an actual review pass — no listed thread supplies that setup, so dropping it in would change the subject and draw no reply.

*A new conversation in #cookbooks on 2025-01-22:*

```
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
```

> **Problems:** longer than one remark

