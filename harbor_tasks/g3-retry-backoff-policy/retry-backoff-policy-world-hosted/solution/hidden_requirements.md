# g3 — Failure-class retry policy for online request processors

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries; `located` gets the same world as `world` plus a map of where each remark sits, but never a quote, never which requirement a conversation serves, and never which are herrings.

| arm | what it is handed | measured |
|---|---|---|
| `blind` | the ticket | — |
| `spec` | the ticket + both hidden requirements | — |
| `clues` | the ticket + all 49 remarks, quoted | **1.00** |
| `world` | the ticket, against `sweworld:0.4.4` where the 49 remarks live in chat, the wiki and mail | — |
| `located` | the `world` arm plus a map naming each remark's channel, day, minute and length (or its page, or its mail subject) — the search removed, the inference left | **1.00** |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Two requirements, `g3.r1` and `g3.r2`. Neither is written down anywhere an agent
can read: they have to be reassembled from remarks scattered across the world.

**Nine facts, not ten.** `g3.r1` declares all five; `g3.r2` declares four — it has
no `failure_behavior`. `score.py` takes its keys from `tasks.json` rather than from
a fixed list of five, precisely so an absent fact is not invented and does not
divide the mean by the wrong number, so each of the nine is worth one ninth.
`open_feature` (did the agent build the feature at all?) carries weight **0.0**:
building the feature scores nothing, only recovering what nobody wrote down does.

The facts, and the question each one answers:

| fact | the question it answers |
|---|---|
| `rule` | what exactly has to exist |
| `scope` | where it applies, and where it must not |
| `exclusions_or_crossover` | what has to stay untouched |
| `failure_behavior` | what happens when it goes wrong |
| `observability` | the exact values a test can read back |

---

### `g3.r1` — a failure costs attempts by class, and rate limits get six free passes

**In one sentence:** how much a failure costs depends on what kind of failure it
is, and a rate limit costs nothing at all until the request has burned through six
per-request waivers.

#### `rule` — what has to exist

A failure is priced against the request's remaining attempt budget **by class**,
and the price is not uniform:

| class | cost |
|---|---|
| `TRANSIENT` | 1 attempt |
| `CONTRACT` | **2** attempts |
| `THROTTLE` | **0** attempts, while the request still holds a waiver |

The waiver counter lives on the request:

- `retry_policy.py` exports `DEFAULT_THROTTLE_WAIVERS: int = 6`.
- `APIRequest` gains `throttle_waivers_left: int = DEFAULT_THROTTLE_WAIVERS`.
- A `THROTTLE` failure with `throttle_waivers_left > 0` **decrements the waiver
  instead of the budget**. Once the waivers are gone, a `THROTTLE` failure costs 1
  like any transient.

`decide` takes `throttle_waivers_left` as a third keyword argument alongside
`attempts_made` / `attempts_left`, and its verdict reports both post-failure
numbers as the frozen fields `attempts_left_after` and `throttle_waivers_after`,
which the caller writes back onto the request.

#### `scope` — per request, not per run

- A fresh `APIRequest` starts with **six** waivers regardless of how many 429s
  other in-flight requests have already absorbed.
- Nothing on `OnlineStatusTracker` or in `OnlineRequestProcessorConfig` holds or
  seeds the waiver count.
- `attempts_left` keeps its existing seeding from `config.max_retries`. Only the
  amount deducted per failure changes.

#### `exclusions_or_crossover` — the two asymmetries

- **`TERMINAL` discards the rest of the budget** rather than preserving it:
  `attempts_left` is set to `0` even when several attempts remained, while the
  waiver count passes through unchanged.
- **A zero-cost `THROTTLE` at `attempts_left == 0` is still retried**, because
  `0 - 0 >= 0` holds. An empty attempt budget does not by itself stop a
  rate-limited request while a waiver remains.

#### `failure_behavior` — charge first, then test

The exhaustion test is `attempts_left - cost < 0`, evaluated **after** pricing —
not an `attempts_left <= 0` check before it. When it trips:

- verdict is not-retry, outcome `exhausted`
- delay is `0.0` — the schedule is never consulted and the jitter source is never
  drawn for a verdict that will not be retried
- the post-failure budget is clamped to `0`, **never negative**

So a `CONTRACT` failure at `attempts_left == 1` ends the request rather than
getting one more try.

#### `observability` — exact values

`DEFAULT_THROTTLE_WAIVERS == 6`, and a fresh `APIRequest` has
`throttle_waivers_left == 6`.

| failure | at | result |
|---|---|---|
| rate limit | `attempts_left=3, throttle_waivers_left=6` | `attempts_left == 3`, `throttle_waivers_left == 5` |
| rate limit | `attempts_left=0, throttle_waivers_left=3` | still retried, `throttle_waivers_left == 2` |
| rate limit | `attempts_left=0, throttle_waivers_left=0` | not retried, `throttle:exhausted`, `attempts_left == 0` |
| `ValueError("finish_reason was length")` | `attempts_left=3` | `attempts_left == 1` |
| `ValueError("finish_reason was length")` | `attempts_left=1` | not retried, `contract:exhausted`, `attempts_left == 0` (**not `-1`**) |
| `Exception("invalid api key")` | `attempts_left=7, throttle_waivers_left=6` | `terminal:abort`, `attempts_left == 0`, `throttle_waivers_left == 6` |

> **The herring** — what the team decided first and later reversed: rate-limit
> failures were initially made free with **no cap at all** (no waiver counter, on
> the theory that a 429 says nothing about the request); that was reversed after a
> run with a permanently throttled key re-queued the same requests for hours, and
> the six-waiver allowance was introduced as the compromise.

---

### `g3.r2` — the pause is an absolute horizon, and it only ever moves outward

**In one sentence:** the rate-limit pause stops being a config constant and
becomes a timestamp on the tracker that later, shorter delays can never pull back
in.

#### `rule` — what has to exist

`OnlineStatusTracker` gains **exactly one** new dataclass field,
`throttle_cooldown_until: float = 0.0`, placed immediately after
`time_of_last_rate_limit_error`.

When a `THROTTLE` verdict is recorded, the policy reads its injected clock **once**
for `now` and then:

```python
tracker.time_of_last_rate_limit_error = now
tracker.throttle_cooldown_until = max(tracker.throttle_cooldown_until,
                                      now + delay_seconds)
```

The `max()` is the point: a later short delay never pulls in a horizon an earlier
longer delay already set.

```python
remaining_cooldown_seconds(tracker, now) == max(0.0, round(tracker.throttle_cooldown_until - now, 3))
```

#### `scope` — extended only by throttles

The horizon is run-level state on the tracker, extended **only** by `THROTTLE`
verdicts. Recording a `TRANSIENT`, `CONTRACT` or `TERMINAL` verdict increments its
counter and:

- touches neither `throttle_cooldown_until` nor `time_of_last_rate_limit_error`
- **does not call the injected clock at all**

So over a mixed sequence of failures, the clock-call count equals the number of
rate-limit failures.

#### `exclusions_or_crossover` — the dead knob stays

`config.seconds_to_pause_on_rate_limit` is **no longer read by any code path**. It
stays in `config.py` as a dead knob for backwards compatibility, and the pause is
never derived from it, nor from elapsed time since
`time_of_last_rate_limit_error`.

A run, model or request that has never been throttled waits **zero** seconds at
the pause point, even though the knob is still set to `10`.

#### `failure_behavior` — not declared

This requirement has no `failure_behavior` fact, which is why g3 is graded on nine
facts rather than ten. Nothing to implement, and nothing scored here.

#### `observability` — exact values

Clock pinned at `1000.0`, jitter `0.25`:

| step | `throttle_cooldown_until` | `time_of_last_rate_limit_error` | clock calls |
|---|---|---|---|
| one rate-limit failure | `1005.0` | `1000.0` | 1 |
| then a contract failure | `1005.0` | `1000.0` | still 1 |
| then a rate limit with delay `1.0`, same clock | `1005.0` (**not `1001.0`**) | — | — |

```python
remaining_cooldown_seconds(tracker, 1002.0) == 3.0
remaining_cooldown_seconds(tracker, 1004.5) == 0.5
remaining_cooldown_seconds(tracker, 1005.0) == 0.0
remaining_cooldown_seconds(tracker, 1099.0) == 0.0
```

A freshly constructed `OnlineStatusTracker()` has `throttle_cooldown_until == 0.0`,
so `remaining_cooldown_seconds(tracker, 12345.0) == 0.0`.

> **The herring** — what the team decided first and later reversed: the horizon was
> first written as a plain assignment `throttle_cooldown_until = now +
> delay_seconds`; that was reversed to a monotonic `max()` after a late
> transient-class failure was observed shortening a 40-second throttle horizon to a
> fraction of a second and re-opening the flood.

---

## Where the remarks are spread

49 remarks in total — 41 clues, 4 herrings and 4 reversals — across 3 surfaces and 8 chat channels. `spread_problems()` is the gate that forces this: every requirement needs at least 2 sources, 3 weeks and 2 channels, so no single sitting recovers one.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **44** | `#pipeline` 10, `#code-review` 8, `#engineering` 6, `#releases` 5, `#cookbooks` 5, `#general` 5, `#incidents` 4, `#viewer` 1 |
| mail (Roundcube/IMAP) | **3** | 3 separate threads |
| wiki (BookStack) | **2** | 2 page comments |

> **The wiki remarks are page _comments_, not page bodies.** BookStack's `/api/search` does not index comments, so a term that lives only in one returns nothing. `/api/pages/{id}` returns them alongside the body — an agent that searches instead of enumerating never sees these 2.

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

## g3.r1

### g3.r1.sc1 — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*The leap nobody states:* If one class is said to deserve more strikes than another and a third deserves none, the deduction is looked up per class instead of being a single fixed number.

- **konrad** (2025-06-03, #code-review): look, same request came back finish_reason length four times last night and spent four attempts on it - a broken payload shoudn't get that many goes.
- **emil** (2025-06-26, #pipeline): honestly two attempts off for a malformed-output failure sounds right to me, one is too generous. doesn't spend a throttle_waivers_left pass though, thats for 429s.
- **nils** (2025-06-03, #general): let me think - no, timeouts stay as they are: one attempt off the budget per failure, and throttle_waivers_left comes back exactly as it went in.
- **dario** (2025-06-03, #incidents): that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request.
- **nils** (2025-06-02, #general): let me think - no, transients don't get their own exit: once the remaining budget can't cover even the one attempt, the verdict is transient:exhausted, same as the throttle path.

### g3.r1.sc2 — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*The leap nobody states:* A count that is defaulted per request and can run out is a second, separate counter living on the request rather than a shared or configured budget.

- **nikolai** (2025-04-25, page:meetings/weekly-notes-week-of-mar-24.md): on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request
- **gideon** (2025-04-24, #engineering): while you're in there - it's throttle_waivers_left, not throttle_waviers_left like the branch has it, and it hangs off APIRequest, the tracker has no buisness knowing about it
- **konrad** (2025-04-15, #engineering): look, one shared counter for the run means the first bad minute eats everyones free passes, each request should walk in with its own full set.
- **emil** (2025-04-23, thread:new|g3.r1.l8): yup — once a request has used up its free passes the next 429 costs it an attempt like anything else, otherwise a dead key just loops forever.

### g3.r1.sc3 — The policy is handed the request's ration alongside its attempt counters and hands back both post-failure numbers for the caller to store on the request; configuration gains nothing new.

*The leap nobody states:* Numbers the policy changes have to travel back on the verdict, because the only place they live is the request itself.

- **nikolai** (2025-06-04, #engineering): decide only sees attempts_made and attempts_left so it cant tell whether a 429 is free the requests remaining passes has to go in as a third kwarg
- **dermot** (2025-04-29, #engineering): we write attempts_left back from the verdict onto the request, but never the pass count, so a request quietly gets its full set again on the next failure.
- **dario** (2025-04-02, #pipeline): honestly i'd rather not put a new knob on OnlineRequestProcessorConfig for this, max_retries still seeds attempts_left and everything else stays on the request

### g3.r1.sc4 — A terminal failure ends the request by emptying whatever attempts remain while its ration passes through untouched, and a rate-limit failure that costs nothing is re-queued even when no attempts remain.

*The leap nobody states:* What stops a rate-limited request is running out of ration, not running out of attempts.

- **nikolai** (2025-06-11, thread:new|g3.r1.l12): ran it with the wrong key and each request retried five more times before giving up once auth is the problem the attempts on the clock are worth nothing
- **dermot** (2025-04-24, #engineering): yeah, on a bad key we empty the attempts and stop: `invalid api key` at seven left gives terminal:abort, attempts to zero, passes untouched at six.
- **gideon** (2025-04-10, #pipeline): ya, bare 429s is exactly the shape that bites us. The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all.
- **konrad** (2025-04-03, #code-review): Look, cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted.

### g3.r1.sc5 — The cost is taken off first and the request ends only if that subtraction would go under zero; when it does there is no wait and the reported budget stops at zero.

*The leap nobody states:* Testing after the deduction rather than before it is what makes a two-attempt charge fatal at one attempt left and a zero-cost charge survivable at none.

- **dermot** (2025-03-17, #pipeline): ordering is the problem, we check the budget before we deduct the cost, so a malformed-output failure with one attempt left still gets a retry it can't pay for
- **nils** (2025-03-19, #pipeline): The verdict logged attempts_left as -1 again overnight. settled: a malformed-output failure that cant pay comes back contract:exhausted with attempts_left 0, never a negative.
- **emil** (2025-04-24, #code-review): went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out.
- **dario** (2025-04-16, #code-review): honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all
- **emil** (2025-03-27, #viewer): honestly the check belongs after the deduction and only trips on strictly negative - a malformed-output failure at attempts_left 2 lands on 0 and still gets retried.

### herrings — believed at the time, reversed later

- **dario** (2025-02-06): settled in review: THROTTLE costs 0 attempts off the retry budget - a 429 says nothing about the request itself, so decide charges nothing and re-queues it.
- **konrad** (2025-03-12): right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do

## g3.r2

### g3.r2.sc1 — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*The leap nobody states:* if the stored end-time is already behind you there is nothing left to wait, so the pause point can ask a stored deadline the one question it actually cares about.

- **nikolai** (2025-06-18, page:meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md): tracker gains one new field for this and only one: throttle_cooldown_until, 0.0 on a fresh tracker, sitting right after time_of_last_rate_limit_error. nothing else added for the pause.
- **gideon** (2025-03-21, #pipeline): so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it.
- **dermot** (2025-04-07, #pipeline): on the retry side: remaining_cooldown_seconds(tracker, now) handed back -3.2 once the window was behind us, and 4.999999999998 before that — clamp at 0.0, round to three decimals.
- **nils** (2025-04-07, #general): A tracker nobody has throttled answers 0.0 however far ahead you ask — with the window at 1005.0, remaining_cooldown_seconds(tracker, 1002.0) is 3.0, 0.5 at 1004.5, 0.0 at 1005.0.
- **dario** (2025-04-11, #releases): mhm — and it sits as a plain module function in the retry policy, remaining_cooldown_seconds(tracker, now), not a method on the tracker, the pause point hands it both.

### g3.r2.sc2 — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*The leap nobody states:* when two throttles overlap the longer wait is the one still owed, so a newly computed shorter deadline cannot be allowed to replace it.

- **konrad** (2025-03-21, #cookbooks): Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again.
- **dario** (2025-03-19, #releases): honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out
- **emil** (2025-03-25, #pipeline): @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, the first 429's own delay reads 5.0 unrounded, so tracker.throttle_cooldown_until is 1005.0; a second worth 1.0 leaves it.
- **nils** (2025-04-21, #general): let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both.
- **konrad** (2025-04-03, #cookbooks): look, every THROTTLE bumps num_rate_limit_errors by one on the way through — one 429, one increment, and that's the only counter it touches.

### g3.r2.sc3 — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*The leap nobody states:* state that exists to describe throttling should only ever be written by throttling.

- **emil** (2025-03-24, #releases): honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock.
- **gideon** (2025-04-09, #pipeline): so basically a timeout landed betwen two 429s and jumped our last-rate-limit stamp — a TRANSIENT only bumps num_api_errors, time_of_last_rate_limit_error is throttle-only.
- **dermot** (2025-03-31, #releases): yeah, for a schema failure the counter is the whole job — a CONTRACT verdict bumps num_other_errors by one and that's it, no stamps, no windows.
- **nils** (2025-04-29, #general): let me think — a TERMINAL verdict lands in num_api_errors, the same slot a TRANSIENT uses, one increment, and nothing else on the tracker moves for it.
- **dario** (2025-04-18, #incidents): and the non-throttle verdicts never touch num_rate_limit_errors, it only moves on a THROTTLE - so it just sits there through a whole run of schema misses and timeouts

### g3.r2.sc4 — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*The leap nobody states:* one fixed number cannot be both long enough for the worst throttle and short enough for the smallest one, so the wait has to come from the failure itself.

- **gideon** (2025-04-11, #incidents): so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh
- **konrad** (2025-05-30, #code-review): look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff
- **dario** (2025-03-31, #code-review): @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week.
- **nikolai** (2025-06-11, thread:new|g3.r2.s4d): A few user configs in the wild still set seconds_to_pause_on_rate_limit, so it stays in config.py with its default of 10 unchanged, even once nothing reads it.
- **dario** (2025-03-17, #code-review): @Konrad on 585 - i left config.seconds_to_pause_on_rate_limit exactly as it was, still 10 on the processor's config, the pause point just doesnt read it anymore

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): in any case i've settled on plain assignment for the horizon: `throttle_cooldown_until = now + delay_seconds` on every THROTTLE verdict, the most recent rate-limit failure is the one that sets the pause
- **konrad** (2025-01-22): Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there.


---


## Where every remark is

49 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-21 | chat | #releases | konrad | [`g3.r2.h1`](#g3r2h1) | 8 | **herring** | — |
| 2025-01-22 | chat | #cookbooks | dermot | [`g3.r2.h2`](#g3r2h2) | 9 | **herring** | — |
| 2025-02-06 | chat | #code-review | nikolai | [`g3.r1.h1`](#g3r1h1) | 9 | **herring** | — |
| 2025-03-12 | chat | #engineering | dermot | [`g3.r1.h2`](#g3r1h2) | 8 | **herring** | — |
| 2025-03-17 | chat | #code-review | konrad | [`g3.r2.say23`](#g3r2say23) | 7 | clue | `exclusions_or_crossover` |
| 2025-03-17 | chat | #pipeline | petar | [`g3.r1.l16`](#g3r1l16) | 8 | clue | `failure_behavior` |
| 2025-03-19 | chat | #pipeline | gideon | [`g3.r1.l17`](#g3r1l17) | 8 | clue | `failure_behavior`, `observability` |
| 2025-03-19 | chat | #releases | konrad | [`g3.r2.s2b`](#g3r2s2b) | 8 | clue | `rule` |
| 2025-03-20 | chat | #cookbooks | dermot | [`g3.r1.rev2`](#g3r1rev2) | 8 | **reversal** of `g3.r1.h2` | `rule`, `scope` |
| 2025-03-21 | chat | #pipeline | dario | [`g3.r2.s1b`](#g3r2s1b) | 7 | clue | `rule` |
| 2025-03-21 | chat | #cookbooks | nikolai | [`g3.r2.s2a`](#g3r2s2a) | 8 | clue | `rule` |
| 2025-03-24 | chat | #releases | konrad | [`g3.r2.s3a`](#g3r2s3a) | 6 | clue | `scope` |
| 2025-03-24 | chat | #cookbooks | nikolai | [`g3.r2.rev2`](#g3r2rev2) | 10 | **reversal** of `g3.r2.h2` | `rule` |
| 2025-03-25 | chat | #pipeline | nils | [`g3.r2.s2c`](#g3r2s2c) | 8 | clue | `observability`, `rule` |
| 2025-03-27 | chat | #viewer | konrad | [`g3.r1.say23`](#g3r1say23) | 7 | clue | `failure_behavior` |
| 2025-03-31 | chat | #code-review | dario | [`g3.r2.s4c`](#g3r2s4c) | 7 | clue | `exclusions_or_crossover` |
| 2025-03-31 | chat | #releases | konrad | [`g3.r2.s3c`](#g3r2s3c) | 8 | clue | `scope` |
| 2025-04-02 | chat | #pipeline | gideon | [`g3.r1.l11`](#g3r1l11) | 8 | clue | `scope` |
| 2025-04-03 | chat | #code-review | nikolai | [`g3.r1.l15`](#g3r1l15) | 9 | clue | `observability`, `exclusions_or_crossover` |
| 2025-04-03 | chat | #cookbooks | nikolai | [`g3.r2.say21`](#g3r2say21) | 8 | clue | `scope` |
| 2025-04-07 | chat | #pipeline | gideon | [`g3.r2.s1c`](#g3r2s1c) | 9 | clue | `rule`, `observability` |
| 2025-04-07 | chat | #general | konrad | [`g3.r2.s1d`](#g3r2s1d) | 9 | clue | `observability` |
| 2025-04-08 | chat | #pipeline | dermot | [`g3.r2.rev1`](#g3r2rev1) | 9 | **reversal** of `g3.r2.h1` | `rule` |
| 2025-04-09 | chat | #incidents | dermot | [`g3.r1.rev1`](#g3r1rev1) | 9 | **reversal** of `g3.r1.h1` | `rule`, `failure_behavior` |
| 2025-04-09 | chat | #pipeline | dario | [`g3.r2.s3b`](#g3r2s3b) | 9 | clue | `scope` |
| 2025-04-10 | chat | #pipeline | gideon | [`g3.r1.l14`](#g3r1l14) | 8 | clue | `exclusions_or_crossover` |
| 2025-04-11 | chat | #incidents | konrad | [`g3.r2.s4a`](#g3r2s4a) | 8 | clue | `exclusions_or_crossover` |
| 2025-04-11 | chat | #releases | nikolai | [`g3.r2.say19`](#g3r2say19) | 8 | clue | `rule` |
| 2025-04-15 | chat | #engineering | nikolai | [`g3.r1.l7`](#g3r1l7) | 7 | clue | `scope` |
| 2025-04-16 | chat | #code-review | konrad | [`g3.r1.l19`](#g3r1l19) | 7 | clue | `failure_behavior` |
| 2025-04-18 | chat | #incidents | nikolai | [`g3.r2.say22`](#g3r2say22) | 7 | clue | `scope` |
| 2025-04-21 | chat | #general | dermot | [`g3.r2.s2d`](#g3r2s2d) | 8 | clue | `rule`, `scope` |
| 2025-04-23 | mail | “support: run on a revoked key retried all night” | gideon | [`g3.r1.l8`](#g3r1l8) | 4 | clue | `rule` |
| 2025-04-24 | chat | #code-review | emil | [`g3.r1.l18`](#g3r1l18) | 8 | clue | `failure_behavior` |
| 2025-04-24 | chat | #engineering | dario | [`g3.r1.l13`](#g3r1l13) | 8 | clue | `exclusions_or_crossover`, `observability` |
| 2025-04-24 | chat | #engineering | dario | [`g3.r1.l6`](#g3r1l6) | 7 | clue | `scope` |
| 2025-04-25 | wiki comment | docs/meetings/weekly-notes-week-of-mar-24.md | dermot | [`g3.r1.l5`](#g3r1l5) | 9 | clue | `rule`, `observability` |
| 2025-04-29 | chat | #general | dermot | [`g3.r2.say20`](#g3r2say20) | 7 | clue | `scope` |
| 2025-04-29 | chat | #engineering | emil | [`g3.r1.l10`](#g3r1l10) | 8 | clue | `rule`, `scope` |
| 2025-05-30 | chat | #code-review | gideon | [`g3.r2.s4b`](#g3r2s4b) | 8 | clue | `exclusions_or_crossover` |
| 2025-06-02 | chat | #general | dermot | [`g3.r1.say24`](#g3r1say24) | 8 | clue | `failure_behavior` |
| 2025-06-03 | chat | #code-review | nikolai | [`g3.r1.l1`](#g3r1l1) | 9 | clue | `rule`, `observability` |
| 2025-06-03 | chat | #general | dermot | [`g3.r1.l3`](#g3r1l3) | 9 | clue | `rule` |
| 2025-06-03 | chat | #incidents | dermot | [`g3.r1.l4`](#g3r1l4) | 8 | clue | `rule` |
| 2025-06-04 | chat | #engineering | dermot | [`g3.r1.l9`](#g3r1l9) | 9 | clue | `rule` |
| 2025-06-11 | mail | “smoke run timings on the wiki before we cut 0.1.26” | konrad | [`g3.r1.l12`](#g3r1l12) | 4 | clue | `exclusions_or_crossover` |
| 2025-06-11 | mail | “429 handling in the online request processor” | emil | [`g3.r2.s4d`](#g3r2s4d) | 4 | clue | `exclusions_or_crossover` |
| 2025-06-18 | wiki comment | docs/meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md | dario | [`g3.r2.s1a`](#g3r2s1a) | 9 | clue | `rule` |
| 2025-06-26 | chat | #pipeline | dario | [`g3.r1.l2`](#g3r1l2) | 7 | clue | `rule` |

#### `g3.r2.h1` · **herring**

- **chat** · #releases · **konrad** · 2025-01-21 15:09
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> in any case i've settled on plain assignment for the horizon: `throttle_cooldown_until = now + delay_seconds` on every THROTTLE verdict, the most recent rate-limit failure is the one that sets the pause

As it appears, spread across the exchange:

```
15:09  konrad    question on the throttle horizon. when a THROTTLE verdict comes back do we push the cooldown out, or keep whichever is later
15:11  dario     plain assignment, i think. throttle_cooldown_until = now + delay_seconds and thats the whole of it
15:12  konrad    even when the old one sits further out? we lose the longer wait then
15:14  dario     mhm. thats delibrate to be honest, the most recent rate-limit failure is the one that sets the pause
15:15  dermot    so no max(), straight overwrite. does that happen on every THROTTLE verdict or only once the horizon has lapsed
15:16  dario     every one. in any case i've settled on that for the horizon
15:18  konrad    right. today it still takes the max i am fairly sure, at least in the version i read friday
15:19  dermot    yeah, that bit is untouched
```

#### `g3.r2.h2` · **herring**

- **chat** · #cookbooks · **dermot** · 2025-01-22 15:29
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there.

As it appears, spread across the exchange:

```
15:29  dermot    the throttle cooldown from the retry pass - if two verdicts come back in one batch does the later one win, or do we keep the longer window
15:32  konrad    later one wins. its one assignment on throttle_cooldown_until, whatever the last THROTTLE verdict carries
15:33  dermot    so a short window landing after a long one shortens it
15:35  konrad    right, thats the part i reviewd. no comparison against whats already sitting there
15:39  nikolai   yep thats the 9am run going back out early then
15:41  nikolai   so keep whichever is further out
15:42  konrad    mhm. compare first, only push it later, never back
15:45  dermot    does the clear-on-success path hit that same line
15:47  konrad    no thats its own reset, sets it to none
```

#### `g3.r1.h1` · **herring**

- **chat** · #code-review · **nikolai** · 2025-02-06 14:01
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> settled in review: THROTTLE costs 0 attempts off the retry budget - a 429 says nothing about the request itself, so decide charges nothing and re-queues it.

As it appears, spread across the exchange:

```
14:01  nikolai   quick one while im in the backoff code does a THROTTLE burn an attempt or not
14:03  dermot    reading it as yes — it goes down the same increment path as a real failure. so three 429s in a row and the request is dead
14:07  dario     thats what it does today and honestly i think thats wrong. a 429 says nothing about the request itself, its our rate thats the problem not their payload
14:07  nikolai   so zero
14:08  dario     zero attempts off the retry budget yeah. costs nothing
14:10  nikolai   and decide hands back the same failure object or what
14:12  dario     no — decide charges nothing and re-queues it. same reqeust goes back in the queue, budget untouched
14:13  dermot    mhm. so the sleep is the only thing bounding it then, nothing on the count side
14:15  nikolai   right the 429 branch doesnt even read retry-after today thats its own mess
```

#### `g3.r1.h2` · **herring**

- **chat** · #engineering · **dermot** · 2025-03-12 14:26
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do

As it appears, spread across the exchange:

```
14:26  dermot    the request that ate eight 429s over the weekend came back exhausted. is throttle counting against attempts or is that something else
14:29  konrad    it shouldnt. only transient and contract come off the budget
14:31  dermot    is there a ceiling on it further up then
14:33  konrad    right, no ceiling on it
14:34  konrad    a rate limited request keeps its full budget however many 429s it eats, THROTTLE never deducts
14:36  dario     mhm that tracks. counter only moves on the other two then
14:38  konrad    anyway noone has writen it that way yet, classify still returns the old shape. maybe i take it tomorow
14:41  dario     the weekend one sat on 429s for 40 min before it quit, thats the case i'd point a fixture at
```

#### `g3.r2.say23`

- **chat** · #code-review · **konrad** · 2025-03-17 12:53
- carries `g3.r2.exclusions_or_crossover`
- must be typed literally: `config.seconds_to_pause_on_rate_limit`, `10`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Konrad on 585 - i left config.seconds_to_pause_on_rate_limit exactly as it was, still 10 on the processor's config, the pause point just doesnt read it anymore

As it appears, spread across the exchange:

```
14:02  konrad    @Dario on 585 - what happens to the rate limit pause setting, do we drop it entirely
14:04  dario     no, not dropping it. i left config.seconds_to_pause_on_rate_limit exactly as it was
14:06  konrad    exactly as it was meaning the default is still 10 on the processor config? and the pause still honours it
14:08  dario     still 10 on the processors config yeah, untouched. the pause point just doesnt read it anymore, thats the actual change
14:09  nikolai   so its a knob that sits there and does nothing now
14:11  dario     for the pause, mhm. nobodys written that bit yet though, i want to do it in the same pass as the rest of 585
14:13  nikolai   theres a cookbook that sets it to 30 somewhere i'd say
```

#### `g3.r1.l16`

- **chat** · #pipeline · **petar** · 2025-03-17 14:02
- carries `g3.r1.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ordering is the problem, we check the budget before we deduct the cost, so a malformed-output failure with one attempt left still gets a retry it can't pay for

As it appears, spread across the exchange:

```
14:02  petar     the 11:40 rerun took a retry after the budget was already spent out. anyone seen that one
14:03  petar     it logged the retry and then died on the charge
14:05  dermot    if i had to guess its ordering. we check the budget and then deduct the cost, not the other way round
14:06  petar     so on the last attempt the check is reading a number thats one call stale
14:08  dermot    yeah. malformed output comes back with one attempt left, budget still looks fine because nothing was taken off yet, so it hands out a retry it cant pay for
14:09  emil      sounds right. deduct first, then the check sees whats actually left
14:10  dermot    mhm. thats the fix. no strong view on whose ticket it lands on
14:12  petar     ok that tracks, the check sits up in the scheduler and the deduct is down in the client somewhere
```

#### `g3.r1.l17`

- **chat** · #pipeline · **gideon** · 2025-03-19 13:02
- carries `g3.r1.failure_behavior`, `g3.r1.observability`
- must be typed literally: `The`, `attempts_left`, `contract:exhausted`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> The verdict logged attempts_left as -1 again overnight. settled: a malformed-output failure that cant pay comes back contract:exhausted with attempts_left 0, never a negative.

As it appears, spread across the exchange:

```
13:02  gideon    The verdict logged attempts_left as -1 again overnight. second time this week i think
13:04  dermot    -1 though. so something took one off past zero and nobody clamped it, if i had to guess
13:06  nils      malformed output path. it wants another attempt, cant pay for it, and still decrements on the way out
13:07  gideon    ok so what does that one come back as, then
13:10  nils      contract:exhausted, and attempts_left reads 0
13:10  dermot    0 even where the budget was already gone before it tried
13:11  nils      0. never a negative, whatever the arithmetic wants to do
13:13  gideon    ya. its only ever the overnight sweep that gets deep enough to hit it fwiw
```

#### `g3.r2.s2b`

- **chat** · #releases · **konrad** · 2025-03-19 14:08
- carries `g3.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out

As it appears, spread across the exchange:

```
14:08  konrad    on the backoff work, if a second retry-after comes in while we are already sleeping, do we take it or keep the deadline we have
14:11  emil      we take it only if its later i believe. otherwise nothing changes
14:12  konrad    and if its earlier? clamp down to it, or ignore
14:16  dario     it loses. we keep sitting on the one we're already holding, the new shorter one just doesnt apply
14:17  konrad    feels odd to throw away what the server just told us
14:20  dario     honestly that window only ever moves further out, ive not seen one pull back in. so the earlier value is noise
14:22  emil      sounds right, so its a max of the two and not much else
14:25  konrad    off the top of my head the 429 and the 503 path build that number in two different places though
```

#### `g3.r1.rev2` · **reversal**

- **chat** · #cookbooks · **dermot** · 2025-03-20 13:32
- carries `g3.r1.rule`, `g3.r1.scope`
- takes back `g3.r1.h2`
- must be typed literally: `DEFAULT_THROTTLE_WAIVERS`, `APIRequest`, `throttle_waivers_left`, `throttle_waivers_after`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, I said 429s never cost a request budget - that's out, a dead key looped for hours. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6 now, decide takes throttle_waivers_left and reports throttle_waivers_after.

As it appears, spread across the exchange:

```
13:32  dermot    that 429 loop over the weekend, the key was dead and it just kept going for hours. nothing ever decremented
13:34  konrad    look, i am the one who said 429s never cost a request budget. no ceiling on it, THROTTLE never deducts, only TRANSIENT and CONTRACT do. thats out now
13:35  dario     out as in throttle eats the normal budget now, or does it get its own pool
13:36  konrad    own pool. APIRequest carries DEFAULT_THROTTLE_WAIVERS = 6
13:37  dermot    decide only sees the request today though, if i had to guess the count has to be passed in
13:38  konrad    mhm. decide takes throttle_waivers_left and reports throttle_waivers_after, caller writes it back
13:39  dario     and the 6 is from that loop or just a roundish number
13:40  konrad    from the loop more or less. it would have been dead in the first minuite at six
```

#### `g3.r2.s1b`

- **chat** · #pipeline · **dario** · 2025-03-21 13:12
- carries `g3.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it.

As it appears, spread across the exchange:

```
13:12  dario     last nights 429 retry slept ~40 min total. the window was 8
13:13  emil      so youre saying the backoff just doubled straight past the reset? i thought we read that header
13:15  gideon    we read it for the log line, ya. but nothing on the tracker recods when the throttle window actually ends, its just attempt counts
13:17  dario     so the sleep site has nothing to ask about how much is left, either way
13:18  gideon    exactly. the pause point cant ask how much is left so it keeps doubling and we idle way past it. so basically the window end goes on the tracker and the sleep reads it there
13:20  emil      yup, and clamp to that instead of the fixed ceiling
13:23  dario     the 8 was sitting in the header on that run too. we had the number and dropped it
```

#### `g3.r2.s2a`

- **chat** · #cookbooks · **nikolai** · 2025-03-21 13:36
- carries `g3.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again.

As it appears, spread across the exchange:

```
13:36  nikolai   why did the retry example blow up again on that rerun
13:38  dario     second 429 came back with a tiny backof value, and we just took it
13:39  nikolai   took it as what we were already 8s deep by then
13:41  dario     as the new wait. it pulled us back down under a second
13:43  konrad    and then we were straight into the flood again. thats the loop right there
13:44  konrad    look, we just dont let it go down. whichever is larger, ours or the header
13:46  nikolai   yep solid enough
13:48  dario     by the end of that run the 429s were landing ~300ms apart fwiw
```

#### `g3.r2.s3a`

- **chat** · #releases · **konrad** · 2025-03-24 14:02
- carries `g3.r2.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock.

As it appears, spread across the exchange:

```
14:02  konrad    quick one, the fake clock in the retry test logged 3 calls but that run only had one 429 in it. is that normal
14:06  emil      not entirely sure it is normal, no. the other two would be the schema failures, i believe — same run had two of those and they go down the same sleep path
14:09  konrad    right but a bad payload has no business asking what time it is. sleeping does not fix the shape of it
14:12  emil      yup, agreed. only the throttles should be reading the clock. schema failure just fails out, no backoff, no clock
14:14  dario     that tracks. so one call for that run and not three
14:17  konrad    anyway that explains the 3 sitting in my notes, i wrote it down as expected at the time
```

#### `g3.r2.rev2` · **reversal**

- **chat** · #cookbooks · **nikolai** · 2025-03-24 15:12
- carries `g3.r2.rule`
- takes back `g3.r2.h2`
- must be typed literally: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, `THROTTLE`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, the last-THROTTLE-wins overwrite I flagged is gone, second 429 had a tiny backof and overwrote a 40s window down under a second. compares now: `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`

As it appears, spread across the exchange:

```
15:12  nikolai   konrad that throttle cooldown you flagged in review is it still a straight assign
15:14  konrad    no, that overwrite is gone. look, it bit us on the retry run — second 429 came back with a tiny backof and it stomped the window we already had
15:16  nikolai   stomped it from what to what
15:17  konrad    40s down to under a second. so we went straight back at them, presumably that is why the run looked like that
15:19  dermot    right, that's the part i reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there
15:20  nikolai   so what does it compare against now
15:24  konrad    itself. `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` — a short window cant win over a longer one anymore
15:24  dermot    yeah ok. nobodys cut the patch yet, it sits behind the batch retry ticket if i had to guess
15:26  nikolai   the 40s is that retry-after or do we compute it
15:27  konrad    header when they send one. ours only when they dont
```

#### `g3.r2.s2c`

- **chat** · #pipeline · **nils** · 2025-03-25 10:55
- carries `g3.r2.observability`, `g3.r2.rule`
- must be typed literally: `0.25`, `1.0`, `1000.0`, `1005.0`, `5.0`, `585`, `tracker.throttle_cooldown_until`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, the first 429's own delay reads 5.0 unrounded, so tracker.throttle_cooldown_until is 1005.0; a second worth 1.0 leaves it.

As it appears, spread across the exchange:

```
15:19  nils      back on 585 - if i pin the clock at 1000.0 in the retry test, what should the cooldown sit at after the first 429
15:22  emil      @Nils 1005.0. that first one's own delay comes back 5.0 unrounded, and tracker.throttle_cooldown_until is just clock plus that
15:25  nils      jitter not in play there? i think the fixture sets it 0.25
15:27  emil      it is, the 5.0 is after jitter. honestly the 0.25 is already baked in by then
15:30  dario     and a second 429 landing while its still hot, does that push it out or reset it
15:33  emil      one worth 1.0 leaves it. 1005.0 stays, only a longer delay moves the number
15:36  nils      makes sense, so the assert is on the far edge not the last write
15:38  dario     mhm thats the bit i had sideways
```

#### `g3.r1.say23`

- **chat** · #viewer · **konrad** · 2025-03-27 14:22
- carries `g3.r1.failure_behavior`
- must be typed literally: `attempts_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly the check belongs after the deduction and only trips on strictly negative - a malformed-output failure at attempts_left 2 lands on 0 and still gets retried.

As it appears, spread across the exchange:

```
14:22  konrad    the retry guard on the viewer path - is the attempts_left check before or after we take one off? off the top of my head its before
14:24  konrad    asking because a malformed run gave up earlier than i expected yesterday
14:29  emil      honestly the check belongs after the deduction. checking first means we're refusing on an attempt we havent actually spent yet
14:33  dermot    after, so it's comparing the new value. against zero or below zero? not the same thing here
14:37  emil      only trips on strictly negative. zero still has a pass in it
14:38  emil      so a malformed-output failure at attempts_left 2 lands on 0 and still gets retried, which is what you'd want
14:41  konrad    mhm ok. that lines up with what i saw then
```

#### `g3.r2.s4c`

- **chat** · #code-review · **dario** · 2025-03-31 11:53
- carries `g3.r2.exclusions_or_crossover`
- must be typed literally: `time_of_last_rate_limit_error`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week.

As it appears, spread across the exchange:

```
15:12  dario     @Dermot Callaghan on pr 585 — what is the pause actually measured against after a 429
15:14  dermot    now minus time_of_last_rate_limit_error. so it shrinks as the clock moves
15:18  dario     mhm. so a 429 and then a slow chunk of work and theres nothing left of it by the time we come back round?
15:20  dermot    yeah. costs nothing at all in that case
15:22  konrad    so we go straight back in
15:25  dario     straight back in yes, no wait at all. bit me twice this week. it wants to be time since we started waiting, not since the error
15:27  konrad    right, then the 0.0 sleep in fridays log makes sense
```

#### `g3.r2.s3c`

- **chat** · #releases · **konrad** · 2025-03-31 16:08
- carries `g3.r2.scope`
- must be typed literally: `CONTRACT`, `num_other_errors`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah, for a schema failure the counter is the whole job — a CONTRACT verdict bumps num_other_errors by one and that's it, no stamps, no windows.

As it appears, spread across the exchange:

```
16:08  konrad    quick one before I forget - when a response comes back failing schema validation, what happens on the retry bookkeepign side? does it get a stamp like the 429s do
16:11  dermot    no. for a schema failure the counter is the whole job
16:12  dario     which counter though, theres like three of them in that struct
16:14  dermot    num_other_errors. a CONTRACT verdict bumps it and thats the end of it
16:15  konrad    bumps it per bad row, or once for the response
16:16  dermot    by one. and nothing else gets written on that path, no stamps, no windows
16:19  dario     mhm ok. simpler than what i had in my head to be honest
16:21  dermot    the windows only ever mattered for the 429 side, if i had to guess thats where it came from
```

#### `g3.r1.l11`

- **chat** · #pipeline · **gideon** · 2025-04-02 13:52
- carries `g3.r1.scope`
- must be typed literally: `OnlineRequestProcessorConfig`, `max_retries`, `attempts_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly i'd rather not put a new knob on OnlineRequestProcessorConfig for this, max_retries still seeds attempts_left and everything else stays on the request

As it appears, spread across the exchange:

```
13:52  gideon    for the retry counting, does the per request state hang off OnlineRequestProcessorConfig or somewhere else? i dunno what we landed on
13:54  dario     honestly i'd rather not put a new knob on that config for this one
13:55  gideon    then what seeds the count
13:57  dario     max_retries. it stays and it still seeds attempts_left, thats unchanged
14:00  dermot    so config hands you the initial number only, and the rest of it rides on the request?
14:02  dario     mhm. everythign else stays on the request, attempts_left included
14:04  dermot    yeah ok. not entirely sure whos picking it up, probably falls out of the 615 work
14:06  gideon    the sleep calc already reads off the request anyway so its less churn than i thought tbh
```

#### `g3.r1.l15`

- **chat** · #code-review · **nikolai** · 2025-04-03 15:11
- carries `g3.r1.observability`, `g3.r1.exclusions_or_crossover`
- must be typed literally: `attempts_left`, `throttle_waivers_left`, `throttle:exhausted`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, cases I want pinned: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2, and at 0 it's throttle:exhausted.

As it appears, spread across the exchange:

```
15:11  nikolai   the throttle retry cases in 565 arent pinned anywhere that i can see
15:12  nikolai   what happens on a 429 when attempts_left is already 0
15:14  konrad    it still re-queues, presuming there are waivers. 429 at attempts_left=0 with throttle_waivers_left=3 goes back on the queue, thats the case i want pinned
15:15  gideon    and the waiver count after that? stays at 3 or
15:16  konrad    comes back 2. it spends one
15:17  gideon    ya ok so basically the 429 path is the only thing eating them
15:18  nikolai   and with the pool empty
15:19  konrad    no requeue then, its terminal and the reason is throttle:exhausted. so at 0 thats what we tag
15:22  dario     mhm that tracks. is the 3 per provider or just the default we ship, i dont remember off hand
```

#### `g3.r2.say21`

- **chat** · #cookbooks · **nikolai** · 2025-04-03 15:23
- carries `g3.r2.scope`
- must be typed literally: `THROTTLE`, `num_rate_limit_errors`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, every THROTTLE bumps num_rate_limit_errors by one on the way through — one 429, one increment, and that's the only counter it touches.

As it appears, spread across the exchange:

```
15:23  nikolai   quick one on the retry counters in the cookbook example, if one request gets throttled twice does that come out as 1 or 2
15:24  konrad    2. every THROTTLE bumps num_rate_limit_errors by one on the way through
15:26  nikolai   ok so its per 429 not per request
15:28  konrad    right. one 429, one increment
15:29  dario     does it hit anything else on the way past, like a generic error total or the failed count
15:31  konrad    no, thats the only counter it touchs. nothing else moves
15:33  nikolai   solid enough ill park it on the retry ticket, dunno who picks it up
15:35  dario     then the 7 in tuesdays sample was just 7 429s, i had it written down as a double count
```

#### `g3.r2.s1c`

- **chat** · #pipeline · **gideon** · 2025-04-07 10:54
- carries `g3.r2.rule`, `g3.r2.observability`
- must be typed literally: `-3.2`, `0.0`, `4.999999999998`, `remaining_cooldown_seconds(tracker, now)`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on the retry side: remaining_cooldown_seconds(tracker, now) handed back -3.2 once the window was behind us, and 4.999999999998 before that — clamp at 0.0, round to three decimals.

As it appears, spread across the exchange:

```
13:41  gideon    quick one on the retry side. remaining_cooldown_seconds(tracker, now) handed me back -3.2 on a job this morning. is negative meant to mean somethign there?
13:43  dermot    no, thats just the window already being behind us and the subtraction carrying on past it
13:44  gideon    so basically clamp. what do we clamp to though, i dunno if none is better for "no cooldown left"
13:45  dermot    0.0. callers are doing arithmetic on it, same type back either way
13:47  gideon    ya ok. um, before that same job went negative it gave 4.999999999998 and the banner printed the whole thing
13:48  emil      float subtraction, the boundary lands a hair short. i believe the display side is str()ing it raw
13:50  dermot    round to three decimals at the source then, not in the banner. 4.999999999998 comes out 5.0 and nothing downstream has to care
13:51  gideon    exactly, and the -3.2 one never reaches the banner at all
13:53  emil      yup. sleep helper reads the same number and already does its own max() so it wont notice the change
```

#### `g3.r2.s1d`

- **chat** · #general · **konrad** · 2025-04-07 14:02
- carries `g3.r2.observability`
- must be typed literally: `0.0`, `0.5`, `1002.0`, `1004.5`, `1005.0`, `3.0`, `A`, `remaining_cooldown_seconds(tracker, 1002.0)`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> A tracker nobody has throttled answers 0.0 however far ahead you ask — with the window at 1005.0, remaining_cooldown_seconds(tracker, 1002.0) is 3.0, 0.5 at 1004.5, 0.0 at 1005.0.

As it appears, spread across the exchange:

```
14:02  konrad    quick one on the backoff thing - what should remaining_cooldown_seconds(tracker, 1002.0) hand back if the window on A runs to 1005.0
14:04  nils      3.0. it is just the window end minus the now you pass in, so 0.5 at 1004.5
14:05  konrad    and right on the boundary? presumably it does not go negative after
14:06  nils      no, it clamps. 1005.0 itself already reads 0.0 and stays there
14:08  gideon    ok but what about a tracker nobody ever throttled, theres no window on it at all tbh
14:10  nils      let me think - same answer, 0.0, however far ahead you ask. nothing to wait on
14:11  konrad    right. none of that is actually in the file yet though is it
14:12  nils      not yet, no
14:13  gideon    ya ok. i had it returning None for the untouched one in my head
```

#### `g3.r2.rev1` · **reversal**

- **chat** · #pipeline · **dermot** · 2025-04-08 17:14
- carries `g3.r2.rule`
- takes back `g3.r2.h1`
- must be typed literally: `throttle_cooldown_until`, `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, `delay_seconds`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> dropped the plain `throttle_cooldown_until = now + delay_seconds` write — a 1.0s throttle landing behind a 40s one pulled the horizon in and we flooded again. it's `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)` now, the window only moves out.

As it appears, spread across the exchange:

```
14:06  dermot    on the throttle horizon - we're still stomping throttle_cooldown_until with now + delay_seconds on every verdict, or did that change
14:09  dario     changed. the old call was plain assignment on every THROTTLE verdict, most recent rate-limit failure sets the pause. thats gone
14:10  dermot    what pushed it over
14:13  dario     a 1.0s throttle landing behind a 40s one. short one pulled the horizon back in and we flooded again
14:15  gideon    so basically the tiny retry erased the big pause? um that explains a lot tbh
14:16  dario     mhm. workers woke up ~39s early and went straight back at it
14:18  dermot    so the write is a floor now, if i had to guess
14:21  dario     yeah - throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds). window only ever moves out, never in
14:23  gideon    ya ok. the burst in fridays logs sits right after a short 429 too, same shape
```

#### `g3.r1.rev1` · **reversal**

- **chat** · #incidents · **dermot** · 2025-04-09 13:21
- carries `g3.r1.rule`, `g3.r1.failure_behavior`
- takes back `g3.r1.h1`
- must be typed literally: `throttle_waivers_left`, `decide`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> that "throttle costs zero attempts" line i settled in review is gone — a permanently throttled key re-queued for hours. 429 is free while throttle_waivers_left > 0, then decide charges 1.

As it appears, spread across the exchange:

```
13:21  dermot    the throttled key from last night sat in the queue til about 04:00. thats the zero-attempt path doing exactly what we told it to, if i had to guess
13:22  dario     mhm. that "throttle costs zero attempts" line i settled in review is gone
13:23  dario     idea was a 429 says nothing about the request itself, so decide charged nothing and re-queued it. fine for a blip. that key was throttled permanently and we re-queued it for hours
13:24  gideon    so 429s eat the budget now? feels harsh for a one off spike tbh
13:24  dario     not flat, no. its free while throttle_waivers_left > 0
13:25  gideon    and after that
13:25  dario     then decide charges 1, same as any other failure
13:26  dermot    yeah ok. so the pool runs out first and then it dies normally
13:27  dario     right, and the waiver comes off on every 429 regardless, the charging only starts once its empty
```

#### `g3.r2.s3b`

- **chat** · #pipeline · **dario** · 2025-04-09 14:38
- carries `g3.r2.scope`
- must be typed literally: `TRANSIENT`, `num_api_errors`, `time_of_last_rate_limit_error`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically a timeout landed betwen two 429s and jumped our last-rate-limit stamp — a TRANSIENT only bumps num_api_errors, time_of_last_rate_limit_error is throttle-only.

As it appears, spread across the exchange:

```
13:04  dario     retry log from the 11:40 run has the last rate limit stamp moving on a request that never saw a 429
13:07  gideon    which request. was there a timeout sitting between two 429s
13:09  dario     yeah actually. two 429s and a read timeout in the middle
13:12  gideon    so basically a timeout landed betwen two 429s and jumped our last-rate-limit stamp. it shouldnt move there at all
13:14  dario     so does a timeout touch anything, or nothing at all
13:15  gideon    a TRANSIENT only bumps num_api_errors, thats it. time_of_last_rate_limit_error is throttle-only, nothing else writes it
13:17  dario     that tracks. retry ticket then i think, nobody has opened that file yet
13:19  dermot    mhm. so the backoff sat on a cooldown no 429 ever set
13:20  gideon    ya. 11:40 slept about twice what it should of
```

#### `g3.r1.l14`

- **chat** · #pipeline · **gideon** · 2025-04-10 11:40
- carries `g3.r1.exclusions_or_crossover`
- must be typed literally: `The`, `attempts_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ya, bare 429s is exactly the shape that bites us. The queue drops a throttled request the moment attempts_left hits zero, even when that 429 cost it nothing at all.

As it appears, spread across the exchange:

```
12:04  gideon    so if deepseek isnt sending retry-after, a throttle just falls through our normal failure path right
12:07  emil      yup, same path. no 429 branch that i can find
12:09  gideon    ya, bare 429s is exactly the shape that bites us then
12:11  dario     bites us how though, it burns a retry or it drops the thing outright
12:14  gideon    drops it. The queue drops a throttled request the moment attempts_left hits zero
12:16  dario     even when the attempt did nothing? nothing sent, no tokens spent
12:18  gideon    exactly, that 429 cost it nothing at all and it still counted. so basically a throttle shouldnt decrement it, thats what we're doing
12:21  dario     mhm. nobodys written it yet though, and the batch side keeps its own attempt count too i think
```

#### `g3.r2.s4a`

- **chat** · #incidents · **konrad** · 2025-04-11 12:19
- carries `g3.r2.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh

As it appears, spread across the exchange:

```
12:19  konrad    what actually killed the 12:04 run, was it us or their side
12:21  dermot    their side to start. 429 at 12:04:01. then we came straight back at 12:04:11 and got throttled again
12:22  konrad    ten seconds. thats our own sleep then?
12:23  dermot    yeah, flat ten on every attempt. constant somewhere in the retry path, if i had to guess
12:24  konrad    but they tell us how long to wait, no? presumably on the response
12:26  gideon    ya they do and we throw it away. so basically ten flat seconds is not what that provider was asking for tbh, we take their number off the response and sleep that
12:27  dermot    yeah ok. nobodys touched that constant yet though
12:29  konrad    right. that run had three of them before it gave up, all ten apart
```

#### `g3.r2.say19`

- **chat** · #releases · **nikolai** · 2025-04-11 13:41
- carries `g3.r2.rule`
- must be typed literally: `remaining_cooldown_seconds(tracker, now)`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> mhm — and it sits as a plain module function in the retry policy, remaining_cooldown_seconds(tracker, now), not a method on the tracker, the pause point hands it both.

As it appears, spread across the exchange:

```
13:41  nikolai   the cooldown remainder math where does that live now do we hang it off the tracker
13:43  dermot    retry policy side. plain module function, not entirely sure it needs to be anything cleverer
13:44  nikolai   what does it take then it needs a clock from somewhere
13:46  dermot    remaining_cooldown_seconds(tracker, now)
13:47  konrad    so the tracker itself stays dumb, right? no method on it
13:49  dario     mhm — not a method on the tracker, honestly. the pause point already holds both so it just hands it both
13:51  nikolai   yep thats fine
13:52  konrad    then the inline math in the sleep path can go, presumably. nobody has written any of this yet though
```

#### `g3.r1.l7`

- **chat** · #engineering · **nikolai** · 2025-04-15 15:02
- carries `g3.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, one shared counter for the run means the first bad minute eats everyones free passes, each request should walk in with its own full set.

As it appears, spread across the exchange:

```
15:02  nikolai   retries gave up way too fast on the reruns yesterday is that budget per run or per call
15:05  konrad    per run, mhm. one counter shared by the whole thing off the top of my head
15:07  dermot    that would explain the tail then. first minute is bad and its spent before the rest even start
15:09  nikolai   so the first bad minute eats everyones free passes and the late requests walk in with nothing
15:12  konrad    right. look, each request should walk in with its own full set, the counter belongs on the request not the run
15:14  dermot    yep. no shared pool at all then
15:17  nikolai   i'd say thats also the 3 attempts vs 30 gap in tuesdays logs
```

#### `g3.r1.l19`

- **chat** · #code-review · **konrad** · 2025-04-16 15:12
- carries `g3.r1.failure_behavior`
- must be typed literally: `0.0`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all

As it appears, spread across the exchange:

```
15:12  konrad    in the backoff helper we still compute a delay when the verdict comes back not-a-retry. on purpose or leftover
15:14  dario     not on purpose i dont think. if its not a retry theres nothing to wait for, so the delay should just be 0.0
15:17  konrad    right, but 0.0 from where. we still walk the schedule to get it? the fail case ran off the end of the table tuesday
15:21  dario     no thats the part i mean, we shouldnt be reading the schedule at all in that branch. just hand back 0.0
15:23  gideon    what about the jitter, um, the rng gets pulled either way right now. i saw it in the trace
15:26  dario     same answer honestly, dont pull from the jitter source either. no schedule read, no draw, plain 0.0
15:28  konrad    mhm. the ceiling clamp sits after that read too, so it never sees a zero today
```

#### `g3.r2.say22`

- **chat** · #incidents · **nikolai** · 2025-04-18 15:11
- carries `g3.r2.scope`
- must be typed literally: `num_rate_limit_errors`, `THROTTLE`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> and the non-throttle verdicts never touch num_rate_limit_errors, it only moves on a THROTTLE - so it just sits there through a whole run of schema misses and timeouts

As it appears, spread across the exchange:

```
15:11  nikolai   last nights bulk run retried something like 40 times and the rate limit count came back 0
15:14  dario     thats num_rate_limit_errors, and honestly it only moves on a THROTTLE verdict, thats the one place we bump it
15:15  nikolai   so what does it do on the other verdicts
15:17  dario     nothing at all - the non throttle verdicts never touch it. schema miss, timeout, malformed json, they all go down the same retry path and leave it sitting where it was
15:19  dermot    so it just sits there through a whole run of schema misses and timeouts. if i had to guess that is your 0
15:21  dario     mhm. simplest thing is a seperate counter bumped on the generic retry path and leave the throttle one as it is, in any case we want the two numbers apart
15:22  nikolai   right the alert we hung off that field has never fired once then
```

#### `g3.r2.s2d`

- **chat** · #general · **dermot** · 2025-04-21 14:12
- carries `g3.r2.rule`, `g3.r2.scope`
- must be typed literally: `time_of_last_rate_limit_error`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both.

As it appears, spread across the exchange:

```
14:12  dermot    pulled the retry logs from fridays run. the two stamps we write on a 429 are always about 40ms apart from each other
14:15  nils      40ms is suspiciously consistent. is that write ordering, or are we reading the clock twice
14:18  dermot    twice. the handler asks for now() when it stamps, then asks again when it computes the window
14:21  nils      let me think — ok that's the whole of it then. take one reading at the top of the handler and use that value for time_of_last_rate_limit_error and for the window both, instead of each grabbing its own
14:23  nikolai   so window start is off the same value not its own call
14:24  nils      yes, same value in both places.
14:26  nikolai   nobodys written it yet, i'd say it rides along with the WS-050 sweep unless dermot wants it separate
14:29  dermot    mhm. the gap was wider than 40 on the slow box last week too, which fits
```

#### `g3.r1.l8`

- **mail** · “support: run on a revoked key retried all night” · **gideon** · 2025-04-23 09:12
- to emil@world.local, nikolai@world.local, dario@world.local
- carries `g3.r1.rule`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> yup — once a request has used up its free passes the next 429 costs it an attempt like anything else, otherwise a dead key just loops forever.

As it appears, spread across the thread:

```
From: gideon@world.local
Sent: 09:12

Hi all,

Forwarding something from support before it gets lost in the queue.

A user had their API key revoked partway through a run (org admin rotated it, they didn't know) and the run just... kept going. All night. Every single call came back 429, nothing ever got through, and the process was still alive when they checked in the morning with a log file that was like 400MB.

So basically they expected it to die after a while and it never did. They're not angry, they just want to know what the intended behavior is so they can tell their team.

Honestly though I couldn't answer that with confidence — I dunno if we treat auth-shaped 429s differently from real rate limits anywhere. Who owns this bit?

Gideon

--------------------------------------------------------------

From: dario@world.local
Sent: 10:04

Hey Gideon,

I think that's the request processor retry path, so probably emil or nikolai.

But the part I want to understand before we touch anything: is this a classification problem where we're mislabelling a revoked key as a rate limit, or is it a counting problem where the retry loop is fine with 429s in principle and just never stops? Because those are actually two different fixes and to be honest i'd rather not do both at once.

Can you get the actual response bodies from the ticket, not just the status codes?

Dario

--------------------------------------------------------------

From: emil@world.local
Sent: 11:47

Let me think through that, because I believe it's the second one and the classification is mostly a red herring.

The provider is returning 429 and honestly from our side that's a legitimate 429 — the key doesn't have quota anymore because the key doesn't exist. I'm not entirely sure we could tell those apart reliably even if we wanted to; different providers dress up revocation differently and some of them do genuinely just say too many requests.

The actual problem is upstream of that. When we see a rate limit we don't charge the request an attempt, we back off and re-queue it, on the theory that being told to slow down isn't the request's fault. Which is right for the normal case — a burst of 429s during a spike shouldn't eat somebody's retry budget. But there's no ceiling on that generosity, so a request that only ever gets 429s never approaches max_retries and the loop has no exit at all.

Once a request has used up its free passes the next 429 should cost it an attempt like anything else, otherwise a dead key loops forever.

We need to be intentional here about what the number of free passes is, though. Too low and we break the legitimate spike case that this behaviour exists for. I'll get the response bodies from gideon anyway since it'd be good to know what we're actually seeing, but I don't think the fix depends on them.

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 12:20

Right, that matches what i remember of that code.

The backoff sleep is also unbounded on the same path fwiw, so overnight it was probably mostly sleeping, which is why nobody noticed the machine was busy. Separate thing, not blocking.

Gideon send me the log too if the user still has it.

Nikolai
```

#### `g3.r1.l18`

- **chat** · #code-review · **emil** · 2025-04-24 14:02
- carries `g3.r1.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out.

As it appears, spread across the exchange:

```
14:02  emil      went through the retry loop this morning, mostly the sleep math. one thing is bugging me
14:03  dermot    bugging you as in the numbers are wrong, or the ordering
14:05  emil      ordering. we're sleeping a full backoff on requests we've already decided to bin
14:06  dermot    decided as in it came back non-retryable? so we wait out the whole delay and then drop it anyway
14:07  emil      yup. and we draw the jitter for them too, on the way out
14:08  dario     mhm. jitter gets computed before the retryable check at all i think, its just sat at the top of the loop body
14:09  emil      it is. both of them, before we ever look at the response class. sleep + jitter want to sit after that check, not before it
14:11  dermot    yeah ok. that's the tail on the friday run then, if i had to guess
```

#### `g3.r1.l13`

- **chat** · #engineering · **dario** · 2025-04-24 14:12
- carries `g3.r1.exclusions_or_crossover`, `g3.r1.observability`
- must be typed literally: `invalid api key`, `terminal:abort`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah, on a bad key we empty the attempts and stop: `invalid api key` at seven left gives terminal:abort, attempts to zero, passes untouched at six.

As it appears, spread across the exchange:

```
14:12  dario     quick one on the retry policy — when the provider rejects the key, do we drain the attempts counter or leave whatever is left sitting on it
14:13  dario     run this morning came in with seven left and i cant tell from the code which one happens
14:15  dermot    `invalid api key` classifies as terminal:abort. theres nothing to retry into so we stop there
14:16  dario     right but abort as in stop, or abort as in stop and rewrite the counters on the way out
14:18  dermot    the latter. we empty the attempts, so your seven lands at zero. passes we dont touch, still six
14:19  dario     mhm. thats not in the policy file yet though is it, i went looking
14:20  dermot    not yet, no. small enough that it can ride along with the backoff ticket whenever someone gets to it
14:23  emil      hm. does a plain 401 with no key text land in the same bucket, or is that its own thing
```

#### `g3.r1.l6`

- **chat** · #engineering · **dario** · 2025-04-24 18:31
- carries `g3.r1.scope`
- must be typed literally: `throttle_waivers_left`, `APIRequest`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> while you're in there - it's throttle_waivers_left, not throttle_waviers_left like the branch has it, and it hangs off APIRequest, the tracker has no buisness knowing about it

As it appears, spread across the exchange:

```
14:02  dario     quick one - whats the counter on the retry branch actually called? im reading throttle_waviers_left and it keeps tripping me up
14:04  dermot    that's a misspelling. waivers, not waviers. the branch has it wrong in every spot it appears
14:05  dario     ok so throttle_waivers_left. do i fix it where the tracker declares it or where the retry loop reads it
14:07  gideon    neither honestly, it shouldnt be on the tracker at all. it hangs off APIRequest, the tracker has no buisness knowing about it
14:08  dermot    yeah ok. so it moves onto the request object and the tracker just stops carrying it
14:09  gideon    exactly. and while youre in there the spelling gets fixed in the same pass, i dont want both spellings sitting in the repo
14:11  dario     theres a fixture with the waviers one baked into it too i think, at least one
```

#### `g3.r1.l5`

- **wiki comment** · docs/meetings/weekly-notes-week-of-mar-24.md · **dermot** · 2025-04-25 10:14
- carries `g3.r1.rule`, `g3.r1.observability`
- must be typed literally: `retry_policy.py`, `DEFAULT_THROTTLE_WAIVERS`, `throttle_waivers_left`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request

As it appears, spread across the exchange:

```
10:14  dermot    585 is still listed in flight up there — is the backoff schedule still hanging off the batch runner? if i had to guess it moved when the retry split landed
10:18  nikolai   it moved yeah the schedule lives in retry_policy.py now
10:18  dermot    per provider or just the one default
10:21  nikolai   one number at module level DEFAULT_THROTTLE_WAIVERS = 6 off the top of my head thats still what its set to
10:24  dario     is that read once at import or does something actually pick it up per call? i couldnt tell from the diff
10:26  nikolai   every request seeds throttle_waivers_left off it when its built so each one starts at 6 of its own
10:28  dario     mhm ok. so a request that never trips a 429 just carries the 6 around untouched
10:29  nikolai   yep
10:31  dermot    6 is more slack than i had in my head for that, honestly
```

#### `g3.r2.say20`

- **chat** · #general · **dermot** · 2025-04-29 14:22
- carries `g3.r2.scope`
- must be typed literally: `TERMINAL`, `num_api_errors`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think — a TERMINAL verdict lands in num_api_errors, the same slot a TRANSIENT uses, one increment, and nothing else on the tracker moves for it.

As it appears, spread across the exchange:

```
14:22  dermot    question on the retry tracker — when a response comes back TERMINAL, which counter is that supposed to land on
14:23  dermot    right now it falls through the generic error path with the timeouts, and i want to know if thats deliberate or just where it ended up
14:31  nils      let me think. deliberate — it lands in num_api_errors, the same slot a TRANSIENT uses. rate limits are the only class with a counter of their own
14:33  dermot    ok that i can do. does anything else move at the same time though, attempt count, in flight, either of those
14:38  nils      no. one increment on that field and nothing else on the tracker moves for it
14:39  dermot    yeah ok. so a TERMINAL never touches the retry numbers at all
14:40  nils      right, nothing gets retried so there's nothing to count there
```

#### `g3.r1.l10`

- **chat** · #engineering · **emil** · 2025-04-29 15:39
- carries `g3.r1.rule`, `g3.r1.scope`
- must be typed literally: `attempts_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> we write attempts_left back from the verdict onto the request, but never the pass count, so a request quietly gets its full set again on the next failure.

As it appears, spread across the exchange:

```
15:39  emil      the retry counts from yesterdays run - same request came back with 3 attempts twice, not entirely sure how that happens
15:41  dermot    youre looking at attempts_left on the request row i take it
15:42  emil      yeah. verdict said 2 left, request showed 3 the next time round
15:45  dermot    we do copy attempts_left off the verdict back onto the request when we persist. what we never write back is the pass count
15:46  emil      ok but if the count itself lands right why does it go back up
15:49  dermot    pass number is what the reset keys off, and it comes back as whatever it started as. so the next failure reads as a first failure and the request quietly gets the full set again. both fields want to come off the verdict, not just the one
15:52  dario     that tracks. i can pick it up if nobodys sitting in that file - same spot where we merge the verdict?
15:54  dermot    same spot yeah. the fixture we exercise it with only ever has one pass in it though, so it wont show you anything
```

#### `g3.r2.s4b`

- **chat** · #code-review · **gideon** · 2025-05-30 17:23
- carries `g3.r2.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff

As it appears, spread across the exchange:

```
14:32  gideon    the retry_after bump to 45 in the client, thats just so it covers the worst 429 we saw?
14:33  nikolai   yep worst one we logged sat around 40
14:35  gideon    so a 429 that clears in 2s waits 45 as well. um, that cant be right
14:36  nikolai   one number for all of them yeah
14:38  konrad    right, thats my problem with it. every trivial one pays for the worst case
14:39  konrad    the wait shoud come from that failures own backoff, not a flat value we picked off the tail
14:41  gideon    ya exactly, that reads better
14:43  nikolai   45 came out of the incident doc anyway not a measurment
```

#### `g3.r1.say24`

- **chat** · #general · **dermot** · 2025-06-02 10:12
- carries `g3.r1.failure_behavior`
- must be typed literally: `transient:exhausted`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - no, transients don't get their own exit: once the remaining budget can't cover even the one attempt, the verdict is transient:exhausted, same as the throttle path.

As it appears, spread across the exchange:

```
10:12  dermot    quick one on the retry budget. if we run dry mid sequence on a transient, does that get its own exit or does it fold into an existing one
10:19  nils      let me think - no, transients dont get their own exit. it folds
10:23  dermot    ok but folds where. and what counts as running dry, budget under the next sleep or budget under the attempt
10:28  nils      once the remaining budget cant cover even the one attempt. thats the line. verdict is `transient:exhausted`
10:31  nikolai   thats the same string throttling gives you isnt it
10:34  nils      same as the throttle path yes, no second code for it
10:36  dermot    fine by me, one less branch on the caller side
10:39  nikolai   the attempts-left counter still prints as a float in the log fwiw
```

#### `g3.r1.l1`

- **chat** · #code-review · **nikolai** · 2025-06-03 14:02
- carries `g3.r1.rule`, `g3.r1.observability`
- must be typed literally: `finish_reason`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, same request came back finish_reason length four times last night and spent four attempts on it - a broken payload shoudn't get that many goes.

As it appears, spread across the exchange:

```
14:02  nikolai   retry log from last night is odd, one request ate four attempts on its own
14:05  konrad    what was it failing on
14:07  nikolai   finish_reason length every time same request came back that way four times
14:09  emil      so truncated output, not a transport error? i believe we count those as retryable right now
14:11  konrad    mhm we do. look, a broken payload shoudn't get that many goes, thats four attempts spent on nothing
14:12  konrad    and length wont fix itself on a retry anyway, so it stops being retryable, fail it out on the first
14:14  nikolai   yep no argument here
14:16  emil      sounds right, whoever has the retry ticket open can fold it in
14:19  nikolai   log line should say which reason it was too they all read the same at the moment
```

#### `g3.r1.l3`

- **chat** · #general · **dermot** · 2025-06-03 14:12
- carries `g3.r1.rule`
- must be typed literally: `throttle_waivers_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - no, timeouts stay as they are: one attempt off the budget per failure, and throttle_waivers_left comes back exactly as it went in.

As it appears, spread across the exchange:

```
14:12  dermot    on the retry policy - a timeout, does that pull from the waiver pool or is it just a plain failure
14:13  konrad    plain failure off the top of my head. one attempt off the budget, same as anything else
14:15  dermot    mhm. it's the waiver count i can't tell from the code. if a timeout nudges it the caller gets back less than it handed us
14:16  gideon    ya thats what bit the friday run i think
14:18  nils      let me think - no, timeouts stay as they are. konrad has it, one attempt off the budget per failure and nothing else moves
14:19  dermot    and throttle_waivers_left specifically
14:20  nils      comes back exactly as it went in. only a real 429 touches that one
14:22  konrad    right so the timeout path needs no change at all. the 429 side is still not written though
14:24  dermot    yeah ok. name still reads like it counts both kinds, someone will trip on that
```

#### `g3.r1.l4`

- **chat** · #incidents · **dermot** · 2025-06-03 14:12
- carries `g3.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request.

As it appears, spread across the exchange:

```
14:12  dermot    retry counters from the late night bulk run are in. three hard failures, everything else just exhausted attempts
14:14  dario     mhm. that `attempt: 2` sitting next to RateLimitError bugs me honestly, it reads like my call failed twice on its own merits
14:15  gideon    what do you mean, it did retry twice though?
14:17  dario     it did, but i burned the whole retry budget on 429s last night against a throttled key. none of them were about my request actually
14:19  dermot    so the key was already over quota from other traffic and your request paid for it. not entirely sure the counter can even tell those apart today
14:21  dario     it cant, and that's the fix. key level 429s get their own count and their own wait, they dont eat the per request attempts
14:22  gideon    ya exactly, so basically attempt only moves when it was our own call that broke
14:24  dermot    yeah. the 23:00 batch sits on that same key by the way, if i had to guess that is what drained it
```

#### `g3.r1.l9`

- **chat** · #engineering · **dermot** · 2025-06-04 14:38
- carries `g3.r1.rule`
- must be typed literally: `decide`, `attempts_made`, `attempts_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> decide only sees attempts_made and attempts_left so it cant tell whether a 429 is free the requests remaining passes has to go in as a third kwarg

As it appears, spread across the exchange:

```
14:38  dermot    the 429 on tuesdays run - decide treated it like any other failure. should it have
14:41  nikolai   depends whether it was a free one cant tell from in there though
14:43  dermot    what does it actually get handed
14:45  nikolai   attempts_made and attempts_left thats the lot
14:47  dermot    mhm so the 429 is already folded into both counts. nothing left to back it out with
14:50  konrad    so where would the free / not free come from then
14:52  nikolai   the requests remaining passes it goes in as a third kwarg
14:55  konrad    right, every policy signature moves. anyway thats fine
14:58  dermot    yeah. the fixed ceiling one wont ever read it, it only counts
```

#### `g3.r1.l12`

- **mail** · “smoke run timings on the wiki before we cut 0.1.26” · **konrad** · 2025-06-11 09:12
- to nikolai@world.local, dario@world.local, emil@world.local
- carries `g3.r1.exclusions_or_crossover`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> ran it with the wrong key and each request retried five more times before giving up once auth is the problem the attempts on the clock are worth nothing

As it appears, spread across the thread:

```
From: konrad@world.local
Sent: 09:12

Hi all,

Before we cut 0.1.26 I would like the smoke run numbers on the wiki to be correct.

The page still says a full bulk-llm-inference pass is "about 20 minutes" and that was written in April, presumably before the batch request changes landed. Nikolai, I think you ran it earlier this week? Whatever you actually saw is better than what is on the page now.

Also, is anyone still pointing these runs at the shared key or has everybody moved to their own.

Not urgent, but I want it settled this week.

Konrad

--------------------------------------------------------------

From: nikolai@world.local
Sent: 11:04

Hi Konrad,

Ran it twice monday.

First pass was 24 min clean, so the wiki number is stale but not badly. I'd say write 25 and move on.

Second pass is the one worth mentioning. I had an old key sitting in my env and didnt notice, and the wrong-key run retried each request five more times before giving up. Once auth is the problem the attempts still on the clock are worth nothing, so somethign that should have died in seconds took 40 min to hand me a 401.

Not a release blocker off the top of my head, but its the kind of thing that eats an afternoon.

Shared key i moved off in may, no idea about Nolan.

Nikolai

--------------------------------------------------------------

From: dario@world.local
Sent: 13:37

Mhm, 25 seems fine for the page. I'd honestly rather it read a little pessimistic than a little optimistic, since people plan their afternoon around that number.

The 401 thing i have hit too actually, though at the time i assumed i was holding it wrong and didnt look further.

In any case, do you want me to drop both timings into the release notes draft as they are, or would you rather edit the wiki page yourself since you have the real numbers in front of you?

Dario

--------------------------------------------------------------

From: emil@world.local
Sent: 16:20

Sounds right, i'll carry the 25 into the notes draft either way.

Separately though, we need to be intentional here about which numbers we publish at all. Half of them go stale within a month of being written and then someone reads them in June and plans around April. Not entirely sure the wiki page is the right home for timings long term.

Leave it as is for 0.1.26, i'm not proposing anything this week.

Emil
```

#### `g3.r2.s4d`

- **mail** · “429 handling in the online request processor” · **emil** · 2025-06-11 09:14
- to nikolai@world.local, dario@world.local
- carries `g3.r2.exclusions_or_crossover`
- must be typed literally: `10`, `A`, `config.py`, `seconds_to_pause_on_rate_limit`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> A few user configs in the wild still set seconds_to_pause_on_rate_limit, so it stays in config.py with its default of 10 unchanged, even once nothing reads it.

As it appears, spread across the thread:

```
From: emil@world.local
Sent: 09:14

Hi Nikolai,

The long gemini run I kicked off friday spent most of saturday doing nothing. I pulled the logs this morning and it is 429s the whole way down — we hit one, we sleep the fixed pause, we retry into the same closed window, we hit another. Throughput never recovers, it just limps until the request budget is gone.

So if I am reading the code right, the pause is a single global stall for the whole run and not something that scales per request? That was my guess but I am not entirely sure I am reading the processor correctly.

Either way I think the fixed number is the thing that stopped working — providers moved to something much more dynamic and we did not.

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 11:52

Hey Emil,

Yep youre reading it right.

One 429 stalls everything for the fixed pause, then we go again with no memory of how many times weve been told no. That was solid enough when the windows were published and static. They arent now, so we sleep 10s into a window that wants a minute and spend the retry budget on calls that were never landing.

What i want is backoff per request off the 429 itself, doubling from a small base with jitter and a ceiling, so one slow provider doesnt hold the whole run hostage. The retry count stays where it is.

A few user configs in the wild set seconds_to_pause_on_rate_limit so leave it sitting in config.py even once nothing reads it any more. Id say a dead field costs us less than a config that blows up on load for someone we never hear from.

Batch path is a different failure mode, gotta think through that one separately.

Nikolai

--------------------------------------------------------------

From: dario@world.local
Sent: 14:06

Makes sense, and honestly the jitter part matters more than the doubling does. Every worker waking up at the same instant is how we got the sawtooth in the first place, i think, so if they all come back staggered we probably stop hammering the boundary.

One thing i want to be clear on before you write it — is the ceiling per attempt or is it a total elapsed thing across the whole retry chain? Those behave very differently on a long run and i can see arguments either way.

Actually, if it is per attempt we should probably say what happens when we are still getting 429s at the ceiling. Do we keep going at the cap, or do we give up on that request?

Dario

--------------------------------------------------------------

From: emil@world.local
Sent: 15:31

Yup, that all sounds right to me.

I will re-run the gemini job once it is in and see whether saturday repeats itself.

Emil
```

#### `g3.r2.s1a`

- **wiki comment** · docs/meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md · **dario** · 2025-06-18 14:06
- carries `g3.r2.rule`
- must be typed literally: `0.0`, `throttle_cooldown_until`, `time_of_last_rate_limit_error`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> tracker gains one new field for this and only one: throttle_cooldown_until, 0.0 on a fresh tracker, sitting right after time_of_last_rate_limit_error. nothing else added for the pause.

As it appears, spread across the exchange:

```
14:06  dario     for the pause thing off 207 — does the tracker end up with a couple of fields for that or just one. i keep drawing it both ways honestly
14:09  nikolai   one field throttle_cooldown_until and thats it
14:11  dermot    so no separate paused flag, you just read the timestamp and compare
14:12  nikolai   right nothing else gets added for the pause
14:15  dario     on a fresh tracker though what does it come up as, none or a number
14:17  nikolai   0.0 like the other timers
14:19  dermot    and where in the struct, if i had to guess down with the rate limit ones
14:21  nikolai   yep straight after time_of_last_rate_limit_error
14:24  dermot    mhm. the reset path touches those two lines together then, easy enough
```

#### `g3.r1.l2`

- **chat** · #pipeline · **dario** · 2025-06-26 14:07
- carries `g3.r1.rule`
- must be typed literally: `throttle_waivers_left`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly two attempts off for a malformed-output failure sounds right to me, one is too generous. doesn't spend a throttle_waivers_left pass though, thats for 429s.

As it appears, spread across the exchange:

```
14:07  dario     back to the retry budget thing - when a response comes back malformed, how much of the budget should that actually cost? one attempt or two
14:09  gideon    i assumed one, same as any other failure tbh
14:13  emil      let me think through that. honestly two attempts off for a malformed-output failure sounds right to me, one is too generous when the model can just keep handing back the same garbage. the code today only decrements by one, nobody's changed it yet
14:16  dario     mhm, that tracks
14:17  dario     does it also burn a throttle_waivers_left pass, or is that pool separate
14:20  emil      separate. it doesn't spend a throttle_waivers_left pass, thats for 429s
14:22  gideon    ah ok, so basically the waiver pool stays untouched. that was the part i had backwards
```

