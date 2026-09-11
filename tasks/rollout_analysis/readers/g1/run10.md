# g1 run 10 (eval 8db49761, rollout 15525502) — reward 0.6

## What this run found

The agent (lumen, 138 steps) skipped straight past ad-hoc chat scrolling and instead **bulk-dumped
every surface**: all 114 BookStack wiki pages with bodies *and* comments to `/tmp/wiki` (line 977),
every Mattermost channel to `/tmp/chat`, the full IMAP mailbox to `/tmp/mail` (line 1734), and all
736 Gitea issues with comments (line 1432). Against that corpus it ran dozens of targeted greps
(`plan_id`, `plan_format_version`, `sha256`, `sweep`, `stale`, `BatchLimits`, ...) and periodically
wrote long synthesis paragraphs (lines 2192, 2497, 2698, 3305, 3657, 4066, 4475) consolidating what
it had learned before finally writing code at line 4581. This recovered the large majority of the
design correctly: the strict envelope order of `batch_plan.json` (line 4801-4809, verified against
`test_open`'s expectations), the exact five `PlannedBatch` fields, `indent=2` plus trailing newline
serialization, `BatchPlanTooFragmentedError` as a sibling (not subclass) `ValueError`, the correct
512-batch default ceiling, `metadata_{i}.json` correctly left at `{"num_jobs": n}` (the one r1 fact
that passed), and — for r2 — the full sweep-after-plan-succeeds ordering, right down to the code
comment "a run that raises leaves the previous split intact" (line 5177) that echoes remark
`g1.r2.l12` almost verbatim. All five r2 facts scored 1.0, and provenance (push, CI, deploy) was
clean throughout.

## What it missed, and why

**r1.rule (0):** the module never exports `PLAN_FILE_NAME` (it invented `BATCH_PLAN_FILENAME`
instead, line 4610). The literal string `PLAN_FILE_NAME` exists in exactly one remark in the whole
corpus — `g1.r1.l2`, a *comment* on wiki page 7 ("Batch job status persistence across process
restarts"). That page surfaced in the agent's own grep output **twice** (lines 1294 and 1303) but
was never opened; the agent opened pages 30 and 95 instead, concluded "Wiki doesn't have the
planner design" (line 1381), and abandoned the wiki permanently — despite the ticket itself
warning that BookStack comments aren't search-indexed and "a page worth reading is worth fetching
whole" (lines 172-173). A page-listing pass without a fetch-every-flagged-page pass is the gap.

**r1.scope and r1.observability (both 0):** these both fail on the same root cause — a naming
inversion. Remark `g1.r1.l6` (found, 14 hits) literally says "plan_fingerprint built
0-2:307;2-4:307;4-5:153 ... and returned f4b1ea1573c0" — i.e. `plan_fingerprint` *is* the hashing
function. The agent read this but implemented `plan_fingerprint` (line 4757) as the raw pre-hash
string builder and invented a second function, `plan_id` (line 4773), to do the actual `sha256`
hashing — and used "plan_id" as its working name for the hash in every one of its own synthesis
notes from line 2192 onward. The three golden digests (`e3b0c44298fc`, `ad0828fea95e`,
`f4b1ea1573c0`) were all correctly derived and numerically verified before coding (line 4528) — this
is not a computation error, it's an export-naming misread that the grading tests (which call
`module.plan_fingerprint` directly) catch immediately.

**r1.failure_behavior (0):** `plan_batches([10]*600 + [5000], one_per_batch)` should raise
`SingleRequestTooLargeError` for row 600, but the agent's implementation raises
`BatchPlanTooFragmentedError` first (513 batches), because its single forward pass checks
oversized-row and closes/counts batches together — with `max_requests_per_batch=1` it trips the
512-batch ceiling at row 512, long before the loop reaches row 600. The remark that specifies this
exact ordering, `g1.r1.f4` ("per-row oversize reports first"), never surfaced anywhere — a direct
grep for "5000" or "row 600" across the full 7832-line transcript returns nothing. Without it the
agent had no signal that oversize-scanning needed to be a dedicated up-front pass.

## What it believed, and why

Of the four herrings, the agent saw only one directly (`g1.r2.h1`, "the sweep is the first thing in
the auto branch... on entry", lines 3625-3643) and never saw its dedicated reversal (`g1.r2.rev1`
— checked directly, zero hits). It nonetheless landed on the correct final belief ("original 'sweep
on entry' was superseded", line 3657) by triangulating from `g1.r2.rev2` and `g1.r2.l12` instead —
a genuine case of the corpus's redundancy saving a fact despite a specific remark being missed.
None of the four herrings were shipped; all were correctly superseded in the final code.

## Why each lost fact was lost

| fact | cause | the gap |
|---|---|---|
| r1.rule | not_found | wiki page 7's comment (`g1.r1.l2`) flagged twice by grep, never opened |
| r1.scope | found_misread | `plan_fingerprint`/`plan_id` naming split, contradicting `g1.r1.l6`'s own wording |
| r1.failure_behavior | not_found | `g1.r1.f4`'s explicit ordering requirement never surfaced |
| r1.observability | found_misread | same naming inversion as r1.scope |

This is a search-methodology failure, not a reasoning or delivery failure: the agent's design
reconstruction was almost entirely correct, and it verified its own numbers against the exact
golden fixtures. It lost the fight on two narrow points — one page never opened despite being
surfaced, one motivating incident never surfaced at all — plus one avoidable misreading of a remark
it did find.
