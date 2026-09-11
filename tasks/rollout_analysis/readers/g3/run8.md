# g3 run 8 (53fe95b3, eval 035777f5, task version 9) — reward 1

## What this run found

This is a strong, complete run: reward 1, all nine declared facts (`g3.r1.{rule,scope,exclusions_or_crossover,failure_behavior,observability}`,
`g3.r2.{rule,scope,exclusions_or_crossover,observability}`) scored 1. The agent cloned the repo, checked Gitea issues (found nothing — correctly
concluded the design lives outside the repo), then built three local corpora it could grep repeatedly: a full IMAP mailbox dump (119 messages,
read as complete sequential threads), a full BookStack dump of all 228 pages *including comments* (recovering twice — once from a bug that
treated `comments` as a list when it is `{active, archived}`, once from a mid-dump 429), and a full Mattermost dump of all 12 channels (~10k
lines) that it grepped repeatedly with widening keyword lists (`waiver|cooldown`, `retry policy|jitter|clamp|schedule|ceiling`, `attempt
#|seconds_to_pause|max_retries`, `requeue`, etc.), each time reading 10-20 lines of surrounding context around a hit.

That strategy recovered the substance of 37 of the 49 answer-key remarks in full context, including all three mail remarks (`l8`, `s4d`, `l12`),
both `r1`/`r2` reversal pairs read start to finish, and the critical observability worked example (clock pinned at 1000.0, jitter 0.25, giving
delay `5.0` — the agent even cross-checked `8.0*(0.5+0.5*0.25)=5.0` by hand at transcript line 3138). The final implementation checklist at line
8081-8088 ("CONTRACT costs 2, TERMINAL drains, attempts_left never negative, delay 0.0 without jitter draw for non-retry, cooldown via max()")
matches the answer key point for point, and the run finished cleanly: PR #737 merged to main (commit 66c0246), CI run 15 green including deploy,
service reported healthy, 67 new policy tests + 5 wiring tests passing.

## What it missed, and why it didn't matter

Twelve remarks were not read in full context. Four were "partial": the grep that should have surfaced them instead landed on a bystander's
opening question or a tail-end follow-up rather than the sentence carrying the fact (`g3.r1.l16` — only petar's closing "the check sits up in
the scheduler" surfaced, never dermot's "we check the budget before we deduct the cost"; `g3.r1.l14`, `g3.r1.say23`[viewer], `g3.r2.s4b` — same
pattern). Eight were never grepped for at all because no keyword list in the run's sequence happened to include their distinctive phrasing
(`g3.r2.say23`[chat], `g3.r2.s2a`, `g3.r2.s3a`, `g3.r1.l11`, `g3.r2.s2d`, and both wiki-comment remarks `g3.r1.l5`/`g3.r2.s1a`). None of this cost
a fact — every requirement had 3-8 redundant carriers, and in each case at least one full-context carrier for the same fact was read elsewhere.

The wiki-comment gap is worth flagging even though it was harmless here: the agent explicitly engineered around the ticket's stated trap
("BookStack search does not index comments") by dumping every page's comments via `/api/pages/{id}`, confirmed 228/228 pages fetched, and then
ran a case-sensitive `grep -rln 'waiver\|cooldown_until\|THROTTLE'` across the whole dump — a query that should have matched the answer key's
quoted text for both `g3.r1.l5` and `g3.r2.s1a` (both literally contain `THROTTLE`-prefixed identifiers) — yet it returned nothing. This is
either a genuine near-miss (the two pages were not among the ones actually holding those comments in this build) or a sign that this world
instance's comment text differs from the answer key's current quote, which the answer key itself flags as possible ("the key in the repo can be
newer than the world this rollout ran against").

## What it believed, and why

All four herring/reversal pairs resolved correctly to the reversed truth, and in two cases (`g3.r1.h1`, `g3.r2.h2`) the agent only ever saw the
herring's *defining sentence* as an isolated grep fragment, stripped of the surrounding exchange — yet it never adopted either herring, because by
the time it hit those fragments it had already read the corresponding reversal thread in full (waiver pool / `max()`) and anchored on that. No
herring was followed in the shipped code.

## The v9 rerun check: konrad's rewritten 14:12 turn

This run did see the rewritten line. It's read in full at transcript line 4631: *"and length does come good on a retry now and then, so dont
stop retrying it, it just shouldnt get as many goes as a timeout."* The agent's own closing self-review at line 8921 references this exact point
by name: *"the finish_reason 'length' / malformed output should still be retried but with fewer goes — that's CONTRACT costing two attempts,
done since ValueError('finish_reason was length') classifies as CONTRACT."* The shipped behavior matches the rewrite precisely — `length`
failures are charged 2 attempts (per `g3.r1.l2`, also read in full) and stay retryable through the normal CONTRACT path; there is no trace
anywhere in the transcript of the run making `length` terminal or non-retryable on first failure, which is what the pre-rewrite wording would
have implied.
