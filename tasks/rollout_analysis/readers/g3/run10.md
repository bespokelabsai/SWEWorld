# g3 (retry-backoff-policy) — world-hosted v7, eval ce846459, run 10, rollout f6e50c9e

**Reward: 1.** All nine graded facts (g3.r1.rule/scope/exclusions_or_crossover/failure_behavior/observability;
g3.r2.rule/scope/exclusions_or_crossover/observability) scored 1. Merged to main (8efd213), CI green, service
healthy, 45 unit tests passing (39 new).

## What this run found

The agent worked all four surfaces before touching code (steps 1-92 of 126). It bulk-dumped everything locally
rather than relying on search: all 736 Gitea issues/PRs, all 228 wiki pages *including comments* (critical, since
BookStack's `/api/search` doesn't index comments and both wiki-comment clues — `g3.r1.l5` on
`weekly-notes-week-of-mar-24` and `g3.r2.s1a` on `weekly-sync-notes-week-of-jun-9` — were caught only because it
fetched every page whole), all 119 mail messages via IMAP (catching all three mail-carried clues in full), and all
12 Mattermost channels (after fixing a self-inflicted `\n`-escaping bug in its own dumper). From there it ran
repeated broad keyword greps (`retry_policy|FailureClass|classif|throttle|waiver|cooldown|jitter`, `verdict`,
`attempt label`, etc.) and read the surrounding date range with `sed` wherever a hit landed — a pattern that
surfaced roughly 34 of 49 remarks (28 fully, 3 partially via grep snippet only).

12 remarks were never surfaced by any query the agent tried (`g3.r1.l7/l11/l16`, `g3.r1.rev1/rev2`,
`g3.r2.s2a/s2b/s2d/s4a/s4b/s4c/say21`) — mostly because their wording used everyday phrases ("own full set",
"tiny backof", "ten flat seconds") with no retry-specific vocabulary to grep for. None of this cost a fact,
because the corpus plants each fact redundantly across 2-5 remarks and the agent always found at least one carrier
per fact — a demonstration of `spread_problems()` redundancy working as designed, not of unusually complete
coverage.

## What it believed, and why

All four herrings were correctly recognized as superseded. `g3.r1.h1`/`h2` ("THROTTLE costs 0 attempts, no
ceiling") were read in full and explicitly reasoned past ("Throttle waiver semantics now clear"); the shipped
`DEFAULT_THROTTLE_WAIVERS=6` mechanism with a real per-request ceiling directly contradicts them. `g3.r2.h1`/`h2`
("plain assignment, last-THROTTLE-wins") were likewise abandoned in favor of the `max(existing, now+delay)` rule,
verified against the reversal `g3.r2.rev1` read in full from `#pipeline`, and confirmed interactively — the agent
ran its `RetryPolicy` against the exact worked numbers from `g3.r2.s2c` (clock=1000.0, jitter=0.25 → delay 5.0,
cooldown 1005.0) before wiring the module in.

## The one real defect (does not cost a fact)

The genuine clue `g3.r1.l1` ("a broken payload shoudn't get that many goes" → CONTRACT costs 2 attempts) sits in
an invented exchange whose very next line, attributed to konrad, adds: "length wont fix itself on a retry anyway,
so it stops being retryable, fail it out on the first." The agent's Analysis at transcript lines 4532 and 5621
treats this as a second real, independent requirement rather than scaffolding embroidering the same clue, and adds
a new `NonRetryableResponseError` classified `TERMINAL` at the `finish_reason == "length"` call site (patch5/patch6,
lines 5628-5710). The shipped runtime therefore aborts a truncated response immediately instead of charging it two
attempts and retrying, as the answer key's observability table requires. This is a real deviation from spec, fully
owned in the agent's own closing summary and commit message as an intentional carried-out decision — but it scores
nothing, because `test_r1.py` calls `policy.decide(ValueError("finish_reason was length"), ...)` directly with a
raw `ValueError`, which `classify_failure` still correctly routes to CONTRACT (the reclassification only fires at
the call site, which the grader never exercises). A textbook case of scaffolding outvoting the plant, invisible to
grading only because the suite tests the policy class in isolation rather than the integration point.

## Lost facts

None — reward 1, all nine facts scored 1.
