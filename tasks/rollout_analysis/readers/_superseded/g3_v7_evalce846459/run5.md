# g3 run 5 (rollout 46cec654, eval ce846459) — reward 0.8889

## What this run found

This is a clean, successful run: PR #737 merged to `main`, CI green, service redeployed and
healthy, 70 new passing unit tests, ruff clean. It is not an infra failure and not a herring
failure — every one of `g3.r1`'s five facts and three of `g3.r2`'s four facts scored 1. The
agent's search was exhaustive-by-export: it pulled the *entire* corpus into local files first
(IMAP dump of all 119 mails, a Mattermost API dump of all 12 channels/10285 lines, a BookStack
export) and grepped each. Mail and wiki were covered thoroughly — it correctly used
`/api/pages/{id}` to pull wiki *comments* rather than trusting BookStack search, catching both
comment-only clues (`g3.r1.l5`, `g3.r2.s1a`, lines 2372 and 4785). Both requirements' herrings
were correctly identified as reversed: `g3.r1.h1`/`h2` were read in full and their reversals
(`rev1`/`rev2`) correctly overrode them (lines 2848→2757, 3078→2897); `g3.r2.h1`/`h2` were only
ever glimpsed as single isolated lines inside a grep dump, never read in full context, but the
agent still landed on the correct `max()` semantics from the (fully-read) reversals and other
clues, so the shallow herring exposure caused no damage.

## What it missed, and why

The one lost fact is `g3.r2.rule`, on a single narrow assertion:
`remaining_cooldown_seconds` must round to three decimals
(`round(until - now, 3)`), and the agent shipped an unrounded `max(0.0, until - now)` (its own
words, transcript line 3861). The root cause traces to exactly one remark never surfacing:
`g3.r2.s1c` (#pipeline, gideon, 2025-04-07: "handed back -3.2... and 4.999999999998... clamp at
0.0, round to three decimals") is the *only* remark that states rounding at all. It was invisible
for two compounding reasons. First, a keyword gap: the agent's one consolidated chat grep used
terms built around `g3.r1`'s vocabulary (`failure class|failureclass|classif|throttle|transient|
free pass|jitter`), and s1c's exchange uses none of them. Second, a coverage gap: even the
agent's manual, cross-reference-driven line-range reads of `#pipeline` jumped directly from a
window dated 2025-03-25 to one dated 2025-04-08, skipping the ~230 lines in between — exactly
where s1c (04-07) sits. The remark the agent *did* find and lean on for this fact, `g3.r2.s1d`
(#general, read in full at lines 3816-3831), gives exact boundary values (3.0/0.5/0.0) that are
already round to three decimals by construction, so nothing the agent actually saw could have
prompted the rounding rule. Seven other remarks were also never found (`g3.r2.say23`, `s2a`,
`s3a`, `s4c`, `s2d`, `s1b`, `g3.r1.l1`), all via the same keyword-gap mechanism or, for `#pipeline`
remarks specifically, because the single big chat grep was piped through `head -60` and chat.txt
lists channels in a fixed order that puts the largest channel (`#pipeline`, 2026 posts) last — its
hits were cut off entirely. None of these losses cost a fact, since redundant clues elsewhere
carried the same facts — except s1c, which was uniquely load-bearing.

## The coordinator's finish_reason check

The shipped code does **not** treat `finish_reason == "length"` as terminal. The pre-existing call
site that raises `ValueError(f"finish_reason was {reason}")` (read unchanged, lines 823-831/
914-922) was left untouched, and the final except block (lines 5886-5908) classifies every
exception generically through `classify_failure` → `decide`, with no finish_reason-specific branch
or new exception class anywhere in the diff. `classify_failure`'s type-based MRO rule (from the
open ticket, not hidden) matches plain `ValueError` to `CONTRACT` before any message-marker check
runs, so a length failure prices at cost 2 and stays retryable — matching the answer key exactly,
confirmed by the passing `r1.rule`/`observability` tests. The misleading closing line in
`g3.r1.l1` ("length wont fix itself on a retry anyway, so it stops being retryable, fail it out on
the first") never reached the agent — `g3.r1.l1` is one of the eight remarks confirmed not found —
so it built the correct behavior from `g3.r1.l2` (found) and the ticket's own type-MRO spec
instead.
