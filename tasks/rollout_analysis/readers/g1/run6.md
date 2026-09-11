# g1 run 6 (58cecadc) — reward 0.7

## What this run found

This is one of the most thorough searches in the g1 pool. The agent dumped **all three
surfaces whole** rather than relying on point queries: all 114 BookStack pages via
`/api/pages/{id}` (which carries comments — BookStack's `/api/search` does not index them,
and the agent discovered this the hard way, first trying search, getting noise, then
switching to a full dump), the entire admin IMAP mailbox (1206 lines), and every Mattermost
channel (9934 lines, after fixing a literal-`\n` escaping bug in its own dump script). Both
wiki-comment-only remarks (`g1.r1.l2`, `g1.r2.l9` — page 7, "Batch job status persistence
across process restarts") were recovered this way (transcript lines 1208, 1239), which a
search-only strategy would have missed entirely, per the plant record's own warning.

Against that corpus it ran a disciplined sequence of identifier-heavy greps
(`max_batches_per_plan|batch_plan|PLAN_FILE|plan_batches|PlannedBatch|BatchLimits|...`,
`plan_document|write_plan|PLAN_FILE|serialize`, `plan_id|plan_fingerprint|plan_format_version`)
and read the full thread around every hit with `sed -n`. It even verified the fingerprint
recipe by hand: before writing a line of code it computed `sha256` of the chat-quoted
canonical strings in a live Python one-liner (line 3058) and confirmed all three digests
(`e3b0c44298fc`, `ad0828fea95e`, `f4b1ea1573c0`) matched exactly.

r2 (sweep stale files, but only after planning succeeds) scored a clean **1.0 across all
five facts**. The agent correctly reconciled both herring/reversal pairs — `g1.r2.h1`→`rev1`
seen directly (lines 1959/1705), `g1.r2.h2`→`rev2` seen mostly through `rev2`'s own recap of
the original decision (lines 1799–1804) rather than the herring's own 2025-01-21 remark — into
the single correct final ordering: plan first, sweep only once a plan is in hand, write new
files, then the sidecar. Its shipped code and its own test suite both match this exactly.

## What it missed, and why

r1 lost three of five facts, and all three trace to two distinct, identifiable causes rather
than sloppiness.

**`plan_fingerprint` naming (`r1.rule`, `r1.observability`).** The digest *algorithm* is
provably correct — verified against the corpus before any code was written. But the agent
named the digest-producing function `plan_id` and invented an un-requested helper
`plan_fingerprint_string` for the canonical-string step, so the module never exports a
symbol literally named `plan_fingerprint`, which both failing tests assert on directly
(`hasattr(module, "plan_fingerprint")`, `module.plan_fingerprint([])`). The tell is in the
agent's own Analysis at transcript line 2612: *"exact key names in batch_plan.json
(plan_format_version, num_batches, totals, limits, batches, plan_id/plan_fingerprint) and
the serializer function names"* — it explicitly noticed the two terms were in tension and
never went back to `g1.r1.l6` (line 2254, "*call it plan_fingerprint*") to resolve which one
named the function. This is `found_misread`: the requirement's substance was recovered, its
exact API surface was not.

**Write-before-request-files ordering (`r1.scope`).** The failing assertion is `the sidecar
was written after the request files, not before them`, and the shipped code proves it: `git
diff` shows `run_in_event_loop(create_all_request_files())` at line 4018 followed only later
by `write_plan_file(...)` at line 4023. This is the one hidden-requirement fact in the whole
run that is a clean `not_found`, not a misread: the single remark that states this ordering,
`g1.r1.l16` ("*job died writing requests_3.jsonl and nothing on disk said there were supposed
to be nine. plan gets written before the first request file.*"), never appears anywhere in
the transcript — confirmed by grepping the full transcript for its identifying text, which
returns zero hits. It is deliberately worded without any code identifier, so it cannot match
any of the agent's keyword-driven greps; the plant succeeded at hiding it from a
search-based strategy that never falls back to reading a channel end-to-end.

Five other remarks were similarly never surfaced (`g1.r2.l4`, `g1.r2.l2`, `g1.r2.l6`,
`g1.r2.l10` partially, `g1.r1.f4`) — all for the same structural reason, plain prose with no
matching keyword — but none of them cost a fact, because each requirement had redundant
carriers the agent did find (e.g. `g1.r2.rule` survived losing `g1.r2.l4` because `g1.r2.l1`,
`g1.r2.l3` and the rev1/rev2 dialogue covered the same ground).

## What it believed, and why

On every herring/reversal pair the agent believed the reversal, not the herring, and its
shipped code follows the reversal in all four cases. Nowhere does the run act on a decision
that was later overturned. This is the cleanest part of the run: r1's `exclusions_or_crossover`
and `failure_behavior` facts both passed on the strength of correctly resolved herrings alone.

## Bottom line

Reward 0.7 = a search and synthesis process that recovered essentially the full design from
three surfaces and correctly navigated four herring/reversal traps, undercut by (a) one
naming decision made on genuinely ambiguous corpus wording that the agent flagged to itself
but never re-checked, and (b) one deliberately keyword-proof clue that a purely grep-driven
strategy could not have found regardless of how many passes it ran.
