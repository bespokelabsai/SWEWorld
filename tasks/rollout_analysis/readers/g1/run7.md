# g1 run 7 (eval 8db49761, rollout 1f06df7a) — reward 0.7

## What this run found

This was an unusually thorough run. The agent read the code first (`create_request_files`,
`create_batch_file`, `max_requests_per_batch` etc., transcript lines 361-946), then systematically
worked every corpus surface: a broad Mattermost full-text search for "planner" (line 1112), then a
whole-channel dump of 8 channels (`pipeline`, `engineering`, `code-review`, `cookbooks`, `random`,
`viewer`, `incidents`, `help`, line 1254), then roughly fifteen rounds of targeted `grep` over those
dumps for phrase clusters (`plan.json|sidecar|batch_plan`, `sha256|fingerprint|ad0828|e3b0c44`,
`BatchPayloadTooLarge|subclass`, `auto sizing|max_batches`, `plan_id|plan_document`). It downloaded
**all 114 wiki pages** individually and walked every comment tree into one file (correctly working
around the task's stated BookStack-comments trap, line 2884-2933), and ran five separate IMAP
keyword searches over mail. This sweep correctly recovered: the plan-vs-metadata design history and
both reversals (lines 1904-2111, 2052-2269), the `plan_fingerprint` recipe verified against all three
corpus digests (`e3b0c44298fc`, `ad0828fea95e`, `f4b1ea1573c0`), `max_batches_per_plan=512` with
`BatchPlanTooFragmentedError` correctly kept as a plain `ValueError` (not a `BatchPayloadTooLargeError`
subclass — resisting a contradicting, unplanted scaffolding remark from Jan 23 code-review, line
1689), the per-row-oversize-reports-first ordering, `PLAN_FILE_NAME`/`PLAN_FORMAT_VERSION`, and the
whole plan-first-then-sweep ordering for r2. The work was genuinely merged (`7e63ef7`), CI went green,
and the service redeployed (line 6360-6373) — this is not a run that died or stalled.

## What it missed and why

**One systemic gap**: the channel dump (line 1254-1266) fetched only 8 of the company's 12 Mattermost
channels — `#general` and `#releases` were never fetched, and neither was ever hit by the broad
initial search (their remarks don't contain the word "planner"). Eight remarks live only in those two
channels. Most were redundant with something the agent did find elsewhere (e.g. `g1.r2.l7` in
`#releases` about the fixed-`batch_size` path being unaffected was redundant with `g1.r2.l5` in
`#pipeline`, which *was* found), so they cost nothing. One was not: `g1.r1.say22` (`#general`) is the
**sole** remark that pins the exact top-level key order for `batch_plan.json` — "plan_format_version,
plan_id, limits, num_batches, num_requests, num_bytes, batches, in that order and nothing else." The
agent explicitly went looking for this ("Need exact top-level key names of the plan document," line
3644) and, after several more grep attempts, never found it. A second, redundant carrier of the field
*names* alone — `g1.r1.say30` in `#incidents`, which *was* dumped — was also missed, because none of
the agent's grep term lists happened to include the literal string "num_requests."

## What it believed and why

The agent correctly identified and followed all four herring reversals it encountered. For r1, it
rejected the "plan rides in `metadata_{i}.json`" herring (`g1.r1.h1`/`h2`, seen at line 1309-1386) in
favor of the standalone `batch_plan.json` sidecar decided in the `#code-review` Apr-24 reversal thread
(`g1.r1.rev1`, "either we keep teaching the reader every shape we have ever written into that file, or
the planning record sits somewhere of its own," line 2111). For r2, it rejected "sweep first, then
plan" (`g1.r2.h1`/`h2`) in favor of "plan first, sweep after" (`g1.r2.rev2`, found via `#cookbooks`,
"we only sweep requests_*.jsonl and metadata_*.json after it returns a plan," line 1562) — this single
remark alone carried both r2.rule and r2.failure_behavior to a pass. Lacking the top-level key names,
the agent guessed `total_requests`/`total_bytes` (transcript line 4746-4770) — a reasonable-sounding
but wrong invention, made in the absence of any corpus text, not a herring it was tricked by.

## Why each lost fact was lost

All three losses — `g1.r1.rule`, `g1.r1.scope`, `g1.r1.observability` — trace to the **same single
implementation choice**: the shipped `plan_document()` emits `plan_format_version, plan_id,
num_batches, total_requests, total_bytes, limits, batches` instead of the corpus-decided
`plan_format_version, plan_id, limits, num_batches, num_requests, num_bytes, batches`. Every other
piece of r1 the tests exercise — the fingerprint algorithm, the per-batch dataclass shape, the
`max_batches_per_plan` ceiling and its dedicated non-subclassed error, the `metadata_{i}.json`
exclusion — was correctly found and correctly implemented (hence `g1.r1.exclusions_or_crossover` and
`g1.r1.failure_behavior` both passed). This is a `not_found` failure, not a misread or a herring
followed: the two remarks that could have supplied the correct names/order sat in channels the run's
own coverage gap left dark.
