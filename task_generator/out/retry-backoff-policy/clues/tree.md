# The tree

## g3.r1

### g3.r1.sc1 — How much a failure costs the request's remaining attempts is decided by its class rather than being flat: a malformed-output failure is charged two attempts, an ordinary transient one, and a rate limit nothing.

*The leap nobody states:* If one class is said to deserve more strikes than another and a third deserves none, the deduction is looked up per class instead of being a single fixed number.

- **konrad** (2025-03-21, #code-review): look, while retry scope is open - same request came back finish_reason length four times last night and spent four attempts, a broken payload shouldn't get that many goes
- **emil** (2025-05-13, #pipeline): honestly two attempts off for a malformed-output failure feels about right to me — one is too generous, and binning the row on the spot is too harsh.
- **nils** (2025-03-21, #code-review): let me think - no, timeouts are fine as they stand, one attempt off the budget per failure. i'd rather we didn't get clever with that path.
- **dario** (2025-04-08, #engineering): that `attempt: 2` sitting next to RateLimitError bugs me honestly — burned the whole retry budget on 429s last night against a throttled key, none of them about my request.

### g3.r1.sc2 — Rate-limit failures are paid for out of a fixed ration of six that every request carries in its own right, and once a request's ration is spent its rate limits cost an attempt like anything else.

*The leap nobody states:* A count that is defaulted per request and can run out is a second, separate counter living on the request rather than a shared or configured budget.

- **nikolai** (2025-04-25, page:meetings/weekly-notes-week-of-mar-24.md): on 585 the schedule lives in retry_policy.py now DEFAULT_THROTTLE_WAIVERS = 6 is the module default that seeds throttle_waivers_left on every request  still moving so dont link it yet
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
- **nils** (2025-03-19, #pipeline): The verdict logged attempts_left as -1 again overnight. i think whatever number we hand back there has to floor at zero, so we're flooring it.
- **emil** (2025-04-24, #code-review): went through the retry loop this morning and honestly, we're sleeping a full backoff on requests we've already decided to bin, and drawing jitter for them on the way out.
- **dario** (2025-04-16, #code-review): honestly if the verdict isn't a retry then the delay should just be 0.0, and we shouldn't be reading the schedule or pulling from the jitter source at all

### herrings — believed at the time, reversed later

- **dario** (2025-02-06): settled in review: THROTTLE costs 0 attempts off the retry budget - a 429 says nothing about the request itself, so decide charges nothing and re-queues it.
- **konrad** (2025-03-12): right, no ceiling on it — a rate-limited request keeps its full budget however many 429s it eats, THROTTLE never deducts, only TRANSIENT and CONTRACT do

## g3.r2

### g3.r2.sc1 — The tracker carries a timestamp for the moment throttling ends, sitting immediately after the existing rate-limit timestamp and zero on a fresh tracker, and the wait at the pause point is that timestamp minus the current time, floored at zero and rounded to three decimals.

*The leap nobody states:* if the stored end-time is already behind you there is nothing left to wait, so the pause point can ask a stored deadline the one question it actually cares about.

- **nikolai** (2025-06-18, page:meetings/weekly-sync-notes-week-of-jun-9-bulk-llm-inference.md): tracker fields keep shifting under this one order right now is num_other_errors then time_of_last_rate_limit_error then throttle_cooldown_until at 0.0 on a fresh tracker still moving dont quote me
- **gideon** (2025-03-21, #pipeline): so basically nothing on the tracker records when the throttle window actually ends, so the pause point can't ask how much is left and we idle way past it.
- **dermot** (2025-04-07, #pipeline): on the retry side: the helper handed back -3.2 once the window was behind us, and 4.999999999998 before that — that should be 0.0 clamped and three decimals.
- **nils** (2025-04-07, #general): A tracker nobody has throttled should answer 0.0 however far ahead you ask — window at 1005.0 gives 3.0 at 1002.0, 0.5 at 1004.5, 0.0 at 1005.0.

### g3.r2.sc2 — A rate-limit failure takes one clock reading, stamps the existing rate-limit timestamp with it, and moves the end-of-throttle timestamp to the later of what it already held and that reading plus the failure's own backoff.

*The leap nobody states:* when two throttles overlap the longer wait is the one still owed, so a newly computed shorter deadline cannot be allowed to replace it.

- **konrad** (2025-03-21, #cookbooks): Look, the second 429 came back with a tiny backof and pulled our wait back down under a second, and we were straight into the flood again.
- **dario** (2025-03-19, #releases): honestly if a new wait lands earlier than the one we're already holding it should just lose, that window only ever moves further out
- **emil** (2025-03-25, #pipeline): @Nils on 585's retry side - clock pinned at 1000.0, jitter 0.25, first 429 sets tracker.throttle_cooldown_until to 1005.0, and a second worth 1.0 has to leave it there.
- **nils** (2025-04-21, #general): let me think — our two stamps came out 40ms apart because the handler asks the clock twice; take one reading, use it for time_of_last_rate_limit_error and the window both.

### g3.r2.sc3 — Failures that are not rate limits only increment their counter: they leave both timestamps untouched and never read the clock at all.

*The leap nobody states:* state that exists to describe throttling should only ever be written by throttling.

- **emil** (2025-03-24, #releases): honestly the fake clock logged three calls for one 429 and two schema failures. a bad payload has no business asking what time it is - only throttles read the clock.
- **gideon** (2025-04-09, #pipeline): so basically one thing did turn up in that pass: a timeout landed betwen two 429s and our last-rate-limit stamp jumped to it, graph showed us throttled when the provider was perfectly happy
- **dermot** (2025-03-31, #releases): yeah, for a schema failure the counter is the whole job, that path has no reason to be moving stamps or windows around.

### g3.r2.sc4 — The pause is no longer derived from the config constant or from how long ago the last rate-limit error happened; the constant stays in config.py unread, for backwards compatibility.

*The leap nobody states:* one fixed number cannot be both long enough for the worst throttle and short enough for the smallest one, so the wait has to come from the failure itself.

- **gideon** (2025-04-11, #incidents): so basically 429 at 12:04:01, and we were hammering again at 12:04:11, still throtled. ten flat seconds is not what that provider was asking for tbh
- **konrad** (2025-05-30, #code-review): look, raising `retry_after` to 45 so it covers the worst 429 means every trivial one waits 45 too, the wait shoud come from that failure's own backoff
- **dario** (2025-03-31, #code-review): @Dermot on pr 585 — we work the pause out as now minus time_of_last_rate_limit_error, so a 429 followed by slow work costs nothing at all. bit me twice this week.
- **nikolai** (2025-06-11, thread:new|g3.r2.s4d): A few user configs in the wild still set seconds_to_pause_on_rate_limit so it stays in config.py even once nothing reads it

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): in any case i've settled on plain assignment for the horizon: `throttle_cooldown_until = now + delay_seconds` on every THROTTLE verdict, the most recent rate-limit failure is the one that sets the pause
- **konrad** (2025-01-22): Right, that's the part I reviewed - last THROTTLE verdict just overwrites throttle_cooldown_until, one assignment, no comparison against whats already there.

