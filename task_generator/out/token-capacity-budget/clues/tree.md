# The tree

## g10.r1

### g10.r1.g10.r1.s1 — An over-settled token axis is left owing the overshoot into the next window instead of being reset to empty, and the debt stops at a quarter of that axis's per-minute limit, the quarter being a named constant CAPACITY_DEBT_FLOOR_FRACTION = 0.25 in the capacity-budget module.

*The leap nobody states:* If the overshoot has to be carried but must not be carried forever, the only way to express 'how far it may run' is as a fraction of the same per-minute number the bucket was seeded from, and that fraction needs a home.

- **dario** (2025-04-08, #engineering): estimator came in light again, third window in a row we went past the provider ceiling - and the ledger resets to zero each minute so that overshoot is gone
- **emil** (2025-05-13, #pipeline): honestly if we burned more than we reserved, minute two should open owing that much. right now it opens fresh every time and I don't love it.
- **nikolai** (2025-03-17, #pipeline): not bottomless though  one bad settle and the run spends the rest of the night paying it back  i'd say we cap the hole at a quarter of the minute's alowance
- **konrad** (2025-03-19, #pipeline): anyway, I pulled the 0.25 out of the settle path into CAPACITY_DEBT_FLOOR_FRACTION in capacity_budget.py, it was sitting inline there and again in a test.

### g10.r1.g10.r1.s2 — The bound is computed per token axis against that axis's own effective per-minute limit, including a limit that came from the DEFAULT_* constants rather than the caller; an axis whose limit is None has no bound and stays None, and the request bucket is never bounded at all.

*The leap nobody states:* 'Effective limit' is whatever the bucket was seeded with, so a defaulted axis is bounded like any other, and where there is no limit there is nothing to take a fraction of.

- **gideon** (2025-03-19, #engineering): so basically I ran a split-limit config and both halves got held against the input number, so output ended up way deeper in the hole than its own 500 a minute ever justfied
- **nils** (2025-03-21, #pipeline): let me think - in my grid the row where the caller passed 0 is A, and A still has the 100k default standing behind it, so it isn't a special case.
- **dermot** (2025-03-24, #pipeline): from the late night run - settle threw doing arithmetic on a None, that model has no token ceiling at all. no ceiling, nothing to take a share of, leave it be.
- **emil** (2025-03-14, #code-review): why is available_request_capacity sitting at -50 though? we reserve exactly one slot per request, it can't overspend, so that one should never be under zero at all.
- **dermot** (2025-04-18, #incidents): same shape on the request side - with no max_requests_per_minute set, available_request_capacity just reads back None, so there's nothing there to floor either

### g10.r1.g10.r1.s3 — The tracker carries an integer field num_capacity_debt_clamps, initialised to 0, which goes up by exactly one per call in which at least one axis was held at its lower bound.

*The leap nobody states:* A per-call counter is the only reading that matches how people talk about 'how often did we bottom out', so two axes bottoming out inside one settle is still one event.

- **gideon** (2025-04-09, #pipeline): honestly though, to see how often we bottom out I've been diffing ledgers between runs, which is stupid - the tracker should just carry a plain counter starting at 0 and tell me.
- **dermot** (2025-03-14, #engineering): yeah - on last night's run num_capacity_debt_clamps went up by two on a single settle where both halves bottomed out, so my per-run figure is double what actually happened
- **dario** (2025-03-17, #code-review): mhm, one call one tick — whether it was a single axis sitting at the bottom or both of them clamped in the same settle, it still only counts once

### g10.r1.g10.r1.s4 — Reaching the top of a bucket is not the counted event: a refill capped at the limit, or a release that raises an axis to that same ceiling, leaves the counter alone, as does any settlement that finishes above the lower bound. Only applying the lower bound counts.

*The leap nobody states:* The counter is meant to answer 'how often did we go too deep', so anything that happens at the full end of the bucket, and anything that never reached the bottom, is outside what it measures.

- **nils** (2025-03-19, #pipeline): let me think - on a smoke run that never once went under, the count came back 47. every refill that tops out at the limit is ticking it, and it shouldn't be
- **emil** (2025-03-18, #code-review): honestly a refill capped back at the limit is only a full bucket - token side tops out at max_tokens_per_minute, request side at max_requests_per_minute, nothing worth recording either way.
- **nikolai** (2025-03-19, #code-review): same goes for a relase handing back a big over-reservation - it clamps at max_tokens_per_minute rather than adding through past it, and that ceiling isnt the event were watching for.
- **konrad** (2025-03-20, #code-review): Look, a settle that leaves us at +100 on a 1000 tracker is not it either. It should only tick when we actaully stopped the fall.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled this in review: free_capacity clamps every axis at 0.0, so available capacity never drops below zero and an under-estimate is just forgotten at settlement.
- **emil** (2025-01-21): one thing off Dario's pass on 387: zero is the floor, a bucket sitting at 0.0 is empty and that's the whole story. no accounting for overshoot, next refill starts clean.

## g10.r2

### g10.r2.s1 — When a request completes normally, only the unused part of the token reservation goes back into the bucket, and the request slot it took stays spent for that minute.

*The leap nobody states:* If the estimate over-books tokens and the call succeeded, the difference is dead weight worth reclaiming, but the call itself really did happen and cannot be un-counted.

- **gideon** (2025-04-21, #help): Also from the same profile - estimator books 1k output tokens on every haiku call, actual comes back under 150, and then we crawl for the rest of the minute.
- **dario** (2025-04-16, #engineering): per-request i think - on a clean response the only thing we put back into the budget is the gap between what we booked and what it actually spent
- **konrad** (2025-03-17, #engineering): Look, we handed the slot straight back the moment the response landed, and that pushed 240 calls into a 200 minute. Provider noticed.
- **nils** (2025-03-19, #engineering): let me think through that - a request that actually reached the provider is spent for that minute whatever came back, it does not un-happen.

### g10.r2.s2 — A failed attempt releases the whole token reservation and one request slot back, capped at the per-minute limits, through an operation separate from the success settlement.

*The leap nobody states:* Work that produced nothing should leave no charge behind, so the release for failures is a different shape from the one that settles a success.

- **emil** (2025-04-10, #pipeline): different shape but same area - gemini 503'd on everything last night, and by minute two we were down to one request every few seconds with zero successes.
- **dermot** (2025-03-20, #engineering): yeah, an attempt that errored bought us nothing, so refund_capacity returns the entire token reservation rather than whatever was left unspent.
- **nikolai** (2025-03-20, #cookbooks): counted it this morning we are doing thirty real requests a minute agaisnt a sixty ceiling because the attempts that came back 503 are still sitting on their slots
- **konrad** (2025-03-21, #cookbooks): Look, if the call errored we hand its slot back, one per attemtp, and never above what the minute started with.
- **dario** (2025-04-11, #incidents): on the refund path the processor side stays thin — `_refund_capacity(self, status_tracker, blocked_capacity)` just calls `status_tracker.refund_capacity(blocked_capacity)` and honestly that's the whole body

### g10.r2.s3 — Both exits of the failure branch release the reservation: the one that puts the request back on the queue and the one that has run out of attempts.

*The leap nobody states:* A release that only happens on one way out of the error handler leaks capacity on the other, and both are terminal for that attempt.

- **gideon** (2025-03-27, #viewer): so basically every retry cycle on that flaky endpoint eats anohter reservation, capacity just walks down all afternoon and never comes back until we restart
- **dario** (2025-04-07, #pipeline): in the retry path, the branch where attempts_left is zero appends the failure and returns, thats the whole of it. our capacity charts never recover after a bad model
- **nils** (2025-04-07, #general): let me think - _refund_capacity should be firing at the point we give up on a request entirely, and right now nothing calls it there
- **emil** (2025-03-19, #releases): let me think through that - on a requeue the request goes back on the queue and gets estimated again, so holding the old booking against it is charging the budget twice.

### g10.r2.s4 — The failure release is sized from the reservation that was made, not from any usage the discarded response reported.

*The leap nobody states:* Numbers attached to a response nobody is keeping are not what was taken out of the bucket, and trusting them can hand back more than was ever booked.

- **nikolai** (2025-03-24, #cookbooks): on the failure path we hand back the token counts the failed response itself reported so the bucket finishes the minute holding more capacity than the limit allows took me a whlie to spot that
- **konrad** (2025-04-03, #cookbooks): Look, the length ones are worst - finish_reason length, and the reponse reports 800 output against the 100 output we actually booked for it.
- **nils** (2025-04-21, #general): let me think — on the throw-away path the booking is the only number we own, and refund_capacity hands it back clamped so available_token_capacity never ends above the limit.

### g10.r2.s5 — The tracker keeps a separate count of settlements and of refunds, each bumped once by its own operation and never by the other, including when the capacity it touched is unlimited.

*The leap nobody states:* A count is only useful for telling the two kinds of release apart if each is attributed to exactly one of them and neither goes silent.

- **emil** (2025-04-17, #pipeline): honestly, the last progress counter we ticked from both paths never matched the request count. these two only move on release — an acquire bumps neither num_capacity_settlements nor num_capacity_refunds.
- **konrad** (2025-04-11, #cookbooks): Look, the tracker dump needs num_capacity_settlements and num_capacity_refunds as separate counters, otherwise I cannot tell the two kinds of release apart in a run.
- **nikolai** (2025-04-24, #releases): ran anthropic overnight with no token ceiling set and the counts never moved off `num_capacity_settlements: int = 0` / `num_capacity_refunds: int = 0` so i spent the morning hunting a bug that wasnt ther
- **dermot** (2025-05-02, #releases): we're counting the call, not whether it moved a number. a release against an unlimited axis went through the same code path, so it still increments.
- **nils** (2025-04-29, #general): let me think — if nobody configures a token limit, available_token_capacity is None for the whole life of that tracker, it never becomes a number.
- **gideon** (2025-04-14, #viewer): so basically i dumped the trakcer on one of those unlimited runs and available_request_capacity comes back as None, so there is no number to watch there, only the counters.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): ok, settled: one release call for both outcomes — _free_capacity(status_tracker, used_tokens, blocked_capacity) — and the request slot goes back on failure exactly like it does on success.
- **emil** (2025-01-28): except branch already has used_tokens built, so failure settles through the same _free_capacity(used, blocked) call as success. slot goes back on every terminal path.

