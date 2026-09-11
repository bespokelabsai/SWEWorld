# g3 run 5 (3e70faf7) — reward 1, all 9 facts scored

This run solved retry-backoff-policy cleanly: reward 1, all nine declared facts (`g3.r1.rule/scope/
exclusions_or_crossover/failure_behavior/observability`, `g3.r2.rule/scope/exclusions_or_crossover/
observability`) scored 1, CI green on main at `0c715a7` (plus a small later `RetryVerdict`-alias
commit), and the deployed service verified up. There are no lost facts to explain.

## What it found and how

The agent ran a textbook four-surface sweep rather than isolated searches: Gitea issues dumped and
grepped (no world-specific issue found — PR numbers like 585/565/566 turned out to be cross-references
inside chat, not tracker items); wiki pages fetched **whole** via `/api/pages/{id}` rather than
`/api/search` (recognizing early, at transcript line 1225, that comments carry content search won't
index) — this is exactly how both wiki remarks (`g3.r1.l5` on page 184, `g3.r2.s1a` on page 207) were
recovered from their comment threads; all 119 mail messages dumped over IMAP and both relevant threads
read in full (`g3.r1.l8`, `g3.r1.l12`, `g3.r2.s4d`); and all 10,262 Mattermost posts dumped and searched
with ten increasingly specific keyword greps, interleaved with direct index-range reads of whole
exchanges once a thread's location was known. That combination recovered 41 of 49 remarks (84%),
including all four herring/reversal pairs — each herring (`g3.r1.h1/h2`, `g3.r2.h1/h2`) was read, but
the agent explicitly flagged it as superseded by its reversal before writing any code (e.g. line 2788:
"superseded by 6698-6710 max() decision"), so no herring reached the shipped implementation.

Notably, this v9 rerun rewrote `g3.r1.l1` (konrad's 2025-06-03 #code-review line) to say a
`finish_reason=="length"` failure should *stay* retryable but cost more than a timeout, rather than
becoming terminal. The transcript confirms the run was served the new wording (line 2037, index 9596),
and the agent's immediate next analysis correctly read it as "CONTRACT-class ... should still retry but
get fewer goes than a timeout" — the shipped code prices `finish_reason=="length"` as CONTRACT (2
attempts, still retried unless the budget can't pay), matching the answer key exactly.

## What it missed, and why it didn't matter

Eight remarks (`g3.r2.s2b/s1b/s2a/s4c/s2d/say20/s4b`, `g3.r1.say23`) never appear anywhere in the
6,957-line transcript, confirmed by exhaustive full-text search for their distinctive phrasing. None
of these is a blind spot in coverage — every surrounding exchange in the same thread was read in
full — but each falls outside the literal keyword vocabulary the agent's ten grep passes actually used:
no pattern ever searched for a bare `retry`, `backoff`, `rate_limit`/`time_of_last_rate_limit_error`,
or a bare `TERMINAL`. Two of the eight (`g3.r2.s1b`, `g3.r1.say23`) plausibly *did* match a broader
pattern (`throttl`, `attempts_left`) but the agent's terminal only exposes the tail of a long piped
grep as a screen snapshot, so an earlier match inside a 40-70-line result could scroll off before being
seen — the agent never redirected a long grep to a file to page through it fully. Because
`spread_problems()` guarantees every requirement at least two sources, three weeks and two channels of
redundant carriers, every one of the nine facts still had a surviving carrier the agent did find, so
none of these eight misses cost a fact.

## One corpus/key divergence worth flagging

`g3.r1.l15`'s answer-key quote ("no requeue then, its terminal and the reason is throttle:exhausted. so
at 0 thats what we tag") does not match what the world actually served in this run (transcript line
1744, index 7332: "no requeue then - thats attempts_left 0 with the waivers gone too, both empty.
terminal, throttle:exhausted. if theres still attempts on the clock it just spend[s one]"). The
underlying fact (zero waivers → `throttle:exhausted`) is unchanged, and the run graded it correctly
either way — recorded per instructions as a task-defect note, not an agent failure.
