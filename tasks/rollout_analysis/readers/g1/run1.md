# g1 run 1 (8d664a4c) — reward 0.8

## What this run found

This is an unusually thorough rollout. The agent authenticated to Gitea, Mattermost (via
its API token) and IMAP, then systematically dumped **every** channel it belonged to
(code-review 3376 lines, engineering 2593, pipeline 2148, cookbooks 809, releases 697,
viewer 329, incidents 245, general 238, random 69) and the **entire 107-message admin
IMAP mailbox**, rather than relying on point searches. From there it ran ~15 iterative
grep passes for planner-related terms (`plan`, `sha256`, `fragment`, `first twelve`,
`num_jobs": n`, etc.) and read the surrounding windows. This recovered the great
majority of both requirements: the `plan_fingerprint` algorithm was numerically
re-derived and checked against all three quoted digests (`f4b1ea1573c0`, `ad0828fea95e`,
`e3b0c44298fc`, line 4854); the strict `plan_document` key envelope, the
`BatchPlanTooFragmentedError`/`SingleRequestTooLargeError` precedence rule, the
plan-before-sweep-and-only-after-success ordering for r2, and the exact zero-row/
`{"num_jobs": n}` observability details were all pinned from real corpus text, not
guessed. Both r1 herring/reversal pairs (h1/rev1, h2/rev2) were actually **seen**, and
the agent correctly resolved a genuine conflict between them by re-dumping chat with
real (unescaped) timestamps specifically to date-order the two threads before writing
any code (line 3036) — a deliberately careful step, not luck.

## What it missed, and why

Two systematic search gaps, neither of which cost the final score by itself:

1. **`#releases` (697 lines) was dumped but never meaningfully read.** None of its
   keyword greps ever matched that channel's phrasing; 5 of 6 planted remarks living
   there (including half of the r2 herring/reversal pair) were never surfaced. This did
   not cost any fact because redundant remarks elsewhere (mail `g1.r2.l6` for scope,
   `g1.r2.rev2`/`l3`/`l4` for rule/failure_behavior) covered the same ground.

2. **BookStack page comments — the corpus's one deliberately search-proof surface —
   were only half-read.** The agent correctly identified that comments must be fetched
   via `/api/pages/{id}` rather than `/api/search` (which the ticket itself warns
   doesn't index them), wrote a fetch script, and iterated through two bugs (dict-keys
   vs. dict-values, then `comments['active']` nesting). The **final, working** version of
   that script (`for c in cs.get('active') or []: ...`) still only ever surfaced **one**
   comment per page across all 114 pages fetched — the root of each thread, never its
   replies. Page 7 ("Batch job status persistence across process restarts") genuinely
   holds 14 threaded comments (confirmed against `data/comments.jsonl`), and the reply
   that spells out the literal constant name `PLAN_FILE_NAME = "batch_plan.json"`
   (nikolai) was never among them.

## The two lost facts trace to one single miss

`g1.r1.rule` and `g1.r1.scope` both failed on the exact same `AttributeError`:
`hasattr(module, "PLAN_FILE_NAME")` is false because the shipped module defines
`BATCH_PLAN_FILENAME` instead (and `DEFAULT_MAX_BATCHES_PER_PLAN` in place of
`_MAX_BATCHES_PER_PLAN`). A search of the **entire** 8442-line transcript for the
literal string `PLAN_FILE_NAME` returns zero hits — the agent never once saw it spelled
out. Its own summary at the end of the run (line 8339) describes the filename, its
value, its auto-only placement, its position relative to the request files — everything
about the constant **except its name** — which is exactly what you'd expect from an
agent that fully reconstructed the semantics from redundant clues (mail `l14`, `l6`;
chat `rev1`, `rev2`, `l1`, `l9`) but never got the one wiki-comment reply carrying the
identifier itself. `g1.r1.scope`'s test asserts on `module.PLAN_FILE_NAME` too, so it
fails at the same first line — not because the agent misunderstood scope (it clearly
didn't: `l13`, `l16`, `rev1`, `l14` and `l6` were all found and correctly acted on), but
because the test can't even run past the missing attribute.

Every other fact — both requirements' `exclusions_or_crossover`, `failure_behavior`,
`observability`, plus all of r2's `rule`/`scope` — scored 1, each backed by at least one
genuinely-found, genuinely-acted-on remark, with the implementation matching the
corpus's decisions (not the ticket's silence, not either herring) throughout.

`provenance.pushed`/`ci_green`/`deployed` are all 1 — the change merged cleanly
(commit `8dda06c`), CI passed, and the service redeployed healthy. Nothing about the
run's ending is anomalous; the 0.8 reward is entirely explained by the single naming
miss above.
