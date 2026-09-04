# The tree

## g10.r1

### g10.r1.s1 — When a settlement takes an axis past empty, the excess is carried into the next window instead of being forgiven, and the depth of that carry is bounded at a fixed fraction of the axis's per-minute limit, a quarter, held in a constant named CAPACITY_DEBT_FLOOR_FRACTION.

*The leap nobody states:* If the overshoot vanishes at empty the next window starts fresh and the provider budget gets breached again, so the debt has to survive the window boundary, and a debt with no bottom would stall the run forever.

- **dario** (2025-04-16, #pipeline): online side: third minute running the poet stage went over the provider budget, and the overshoot disappears before the next window opens. we don't forgive that at the boundary.
- **konrad** (2025-04-03, thread:new|g10.r1.l2): Look, reserved 800 on the 1k model, real usage came back 1500, and a second later the bucket read full agian. Hour of my life on that 429.
- **emil** (2025-04-16, #pipeline): then the next minute opens owing the overshoot, but we cap the carry at a quarter of that minutes tokens or a run never climbs back out.
- **nikolai** (2025-06-12, page:engineering/capacity-debt-and-backpressure-accounting-in-the-rate-limiter.md): renamed it to CAPACITY_DEBT_FLOOR_FRACTION in reveiw clamp kept reading like it was about the top of the bucket and its not

### g10.r1.s2 — The bound is computed per axis against the limit that axis actually ended up running with, including one that was substituted in when nothing was configured; an axis with no limit at all has no bound, and the request bucket is never bounded this way because it never overdraws.

*The leap nobody states:* A fraction has to be taken of a real number, so the only sensible number is whatever limit the tracker is actually enforcing on that axis at that moment.

- **dermot** (2025-04-09, thread:new|g10.r1.l5): for trackers where nobody configured a token limit, plan A takes the fraction off the 100k we substituted in, not off the 0 the caller handed us.
- **gideon** (2025-03-19, #engineering): Anthropic run last night: output ceiling is 40k, input is 100k, and output got let sink as deep as input, four windows to recover. So basically each axis floors against its own limit.
- **nils** (2025-06-25, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md): on 207: the vllm boxes run with the token limit unset, my branch died doing arithmetic on None. nothing to take a fraction of there, so leave those buckets alone.
- **konrad** (2025-04-09, thread:new|g10.r1.l8): look, your branch takes the same fraciton off the request bucket too. there we reserve one slot at a time and never overshoot it, so leave that side alone.

### g10.r1.s3 — The tracker carries a running count of how often the bound was applied, incremented once per operation that pinned at least one axis rather than once per axis.

*The leap nobody states:* If a number is meant to tell you how many operations went badly, counting axes instead makes the same run report a different figure depending on which strategy it used.

- **dario** (2025-04-09, #pipeline): spent the morning grepping logs to work out whether we ever actually hit the bottom on that run, and nothing on the tracker says. it needs to count that.
- **gideon** (2025-04-23, #pipeline): so basically the seperate run reported twice what I counted by hand, because every settle that pinned both axes logged two. counting per axis just inflates it, that's wrong.
- **emil** (2025-04-10, #pipeline): honestly this wants to be on the tracker as num_capacity_debt_clamps, right next to the buckets — i had it hanging off the procesor twice now and it got lost across retries both times.
- **nikolai** (2025-05-13, page:engineering/limiter-axes-and-what-a-block-actually-counts.md): i'd say one wait one tick however many axes went under at the same time otherwise the number is telling you about axes and not about runs

### g10.r1.s4 — Reaching the top of a bucket is a different event and is not counted: neither a refill capped at the per-minute limit nor a release that lifts an axis back to that same ceiling touches the count.

*The leap nobody states:* A count that fires on both ends of the bucket measures nothing, since a healthy idle run tops out constantly.

- **nils** (2025-03-19, #pipeline): the count came out at forty-odd on the soak and nothing ever went under - every refill that topped out at the per-minute limit was ticking it. capped refills shouldn't count.
- **konrad** (2025-05-13, thread:new|g10.r1.l14): Look, same on the release path: freeing capacity back to exactly max_tokens_per_minute registered as one of these. Nothing was pinned, the bucket was just full — should not count.
- **dermot** (2025-05-14, page:engineering/review-notes-on-the-token-capacity-budget-scoping-doc-207-and-233.md): the top of the bucket isnt an event, its just where the arithmetic stops, so keep it out of the tally. only the lower bound is worth a number.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): one thing worth notng while I'm in 387 - free_capacity clamps at 0.0 so available_token_capacity never drops below zero, an under-estimate just gets forgiven rather than carried into the next window
- **emil** (2025-01-21): ok, settled then: the floor is 0.0 on every axis. if a model burns more than we reserved, the window absorbs it, nothing owed to the next one.

## g10.r2

### g10.r2.s1 — A failed attempt and a completed call are released differently: the failure puts back the whole token reservation and the request slot it was holding, while a completed call puts back only the tokens it did not use and keeps its slot spent for the minute; neither can leave a bucket above the minute's limit.

*The leap nobody states:* If a call that never got served must leave the buckets as it found them, and a call that did get served only gives back its over-estimate, then the two releases cannot be the same operation.

- **gideon** (2025-03-17, #code-review): so basically 60 clean calls inside the minute and the request bucket still read 60 the whole way, then the 429 obviosuly. a success must not hand the slot back.
- **dermot** (2025-04-10, page:engineering/token-capacity-the-reserve-release-model-draft-for-comment.md): yeah, on the branch where the call actually came back the only thing worth handing back is the tokens we over-guessed. the slot is spent.
- **emil** (2025-04-23, thread:new|g10.r2.l3): i believe the right framing is that a failed attempt never got served — so it should hand back both, the tokens it parked and the request slot it took.
- **konrad** (2025-03-18, #code-review): Look, request bucket hit 62 wtih the limit at 60 while retries flowed back, we put back more than we took. A release must never push above the per-minute limit.

### g10.r2.s2 — Both endings of a failed attempt do the giving-back: the one that puts the request back on the retry queue and the one where there is nothing left to retry.

*The leap nobody states:* A bucket that only recovers on the requeue branch will still bleed on a model that fails all the way to the end, so both exits have to be covered.

- **nikolai** (2025-06-26, page:engineering/token-capacity-reservation-in-the-online-processor-issue-207-has-capacity.md): i mean the give back only happens in the branch that requeues once attempts_left hits 0 the request just dies still holding what it reserved and it shouldnt
- **nils** (2025-03-19, #pipeline): not entirely clean on my end i think — pointed it at a model that fails on every call, request bucket bottomed out in about two minutes and never came back up.
- **dario** (2025-04-23, thread:new|g10.r2.l7): i think both exits of that except branch want the same treatment, honestly — the one that goes back on the queue and the one thats run out of retries.

### g10.r2.s3 — The amount given back after a failure is the reservation that was taken, not whatever token usage the failed response reported.

*The leap nobody states:* A response that was thrown away is not a measurement, so the only trustworthy number is the one held at reservation time.

- **konrad** (2025-04-07, page:incidents/postmortem-kluster-ai-deepseek-output-token-default.md): Look, saw this last week: reserved 1000 for that one, it came back finish_reason length claiming 1700 used, and 1700 is what the bucket got charged.
- **emil** (2025-04-21, thread:<178770212973.2301745.4705747507669611471@world.local>): also WS-054: lost an afternoon to drift between what we hold and what comes back — reported usage on responses we discard isn't a sound basis for the release.
- **dermot** (2025-03-14, #engineering): when we let go of a failed attempt, the number we hand back should be the one we held at reservation time, not whatever the response reports — we still have that request object in hand at that point.

### g10.r2.s4 — The two kinds of release are counted separately on the tracker, each operation moving only its own counter, and the count moves whenever the operation runs even if no capacity actually changed.

*The leap nobody states:* A counter that only moves when arithmetic happens is a counter of arithmetic, not of the calls you were trying to watch.

- **gideon** (2025-03-19, #code-review): honestly though, one release counter for both kinds means i can't see the retry churn at all in the dashbaord, a run thrashing on retries looks identical to a quiet hour.
- **nikolai** (2025-04-03, page:engineering/token-capacity-budget-in-the-limiter.md): i'd say keep the two tallies seperate, a settle moves its own counter and a give back moves its own, neither touches the other
- **nils** (2025-03-20, #code-review): ran the unlimited-token config overnight, both counts sat at zero even though every request went through the same release path — releases on an unlimited tracker simply go uncounted today.
- **dario** (2025-04-15, thread:new|g10.r2.l14): honestly we're counting that the call happened, not that a number changed — so it ticks even when there was nothing on that axis to move.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): ok, got through the PR 387 diff - the except branch calls _free_capacity with the used_tokens it alredy builds, same as the success path, so both hand the request slot back.
- **gideon** (2025-01-23): so basically one release helper, one shape: _free_capacity(tracker, used, blocked) on every terminal path, and the slot comes back whether the attempt suceeded or blew up

