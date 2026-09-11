# g1 run 5 (12f8950a) — reward 0.8

## What this run found

A strong, well-evidenced run: 8 of 10 hidden facts passed, both herring pairs were resolved
correctly in both directions (r1's metadata-folding herring and r2's sweep-on-entry herring
were both recognized and their later reversals followed), and all provenance checks (push, CI
green, deploy) passed. The agent's search technique was disciplined — it used BookStack's
`/api/pages/{id}` rather than `/api/search` specifically because it had already learned that
search does not index comments, dumped the full IMAP mailbox rather than trusting any UI, and
caught a genuine tension in the corpus (an earlier, contradicted chat message arguing that
`BatchPlanTooFragmentedError` *should* subclass `BatchPayloadTooLargeError`) without acting on
a "truncated quote" — it went back for full thread context before deciding, and landed on the
correct answer (transcript line 1957).

## What it missed, and why

Both losses trace to the same failure shape: **a single remark held the missing piece, and
that remark's wording fell outside every search the agent ran.**

**`g1.r1.rule` (missing `PLAN_FILE_NAME`).** The grader's very first assertion is
`hasattr(module, "PLAN_FILE_NAME")`; the shipped module exports `PLAN_FORMAT_VERSION`,
`plan_fingerprint`, `plan_document` and four more names, but never a `PLAN_FILE_NAME`
constant — the write call just hardcodes the literal `"batch_plan.json"`
(`base_request_processor.py`, transcript line 4060). The one remark in the entire 50-remark
corpus that names this identifier is `g1.r1.l2`, a **nested reply** three turns into a 7-turn
BookStack page comment thread: "the planner module already has the name pinned
`PLAN_FILE_NAME = "batch_plan.json"`." The agent's own comment-dump helper script
(`for c in (cm.get('active') or [])`, transcript ~line 1200) only serialized top-level
comments. Proof this is a structural bug, not bad luck: the sibling remark `g1.r2.l9`, a
**top-level** comment on that exact same page, was captured by the identical script one
turn earlier (line 1231). The agent genuinely did everything else right with this fact —
the digest recipe, the envelope key order and strictness, both golden fingerprints — all
implemented and locally tested (29/29 passing) before the grader ever touched them.

**`g1.r1.scope` (sidecar written after, not before, request files).** The agent's own Plan
text states the design outright (line 3032): "plan first, sweep only after the plan returns,
**write files, then write batch_plan.json**." The shipped code writes all request files via
`create_all_request_files()`, then calls `self._write_batch_plan(plan)` — exactly backwards
from what the corpus specifies. The one remark that states this ordering explicitly,
`g1.r1.l16` ("the plan gets written before the first request file, not at the end"), was
never surfaced anywhere in the transcript. It shares zero vocabulary with any of the 7 fixed
Mattermost search terms the agent used (`sidecar`, `plan_id`, `plan_document`,
`plan_format_version`, `planner`, `payload`, `batch_size`) or any later targeted grep
(`digest`, `TooLarge`, `max_batches`, `sort_keys`, `"one line per"`). #pipeline — the single
most heavily loaded channel, with 10 of the 50 remarks — was never read linearly; it was
only ever hit by keyword. The agent appears to have generalized (wrongly) from the *correct*
and separately-recalled r2 rule — that the stale-file **sweep** happens after planning — and
applied that same after-not-before shape to the sidecar write too.

## What it believed, and why

Both herring pairs resolved correctly. For r1: the herring ("the plan rides in
`metadata_{i}.json`") appears only inside its own reversal's recap (`g1.r1.rev1`/`rev2`, both
found and read in full — line 1809/2396), and the agent correctly implemented the *reversed*
position: `metadata_{i}.json` stays `{"num_jobs": n}` only. For r2: same pattern — the
sweep-on-entry herring is recapped inside `g1.r2.rev1`/`rev2` (both found, line 2191), and the
shipped sweep runs strictly after `plan_request_batches` returns, matching the reversal.
Neither standalone herring message was ever independently surfaced by search — the agent's
understanding of "what was decided and reversed" came entirely through the reversal messages
themselves, which is sufficient (each reversal recaps its herring) but means the agent never
saw the original decision in its own words.

## Why each lost fact was lost

Both are `not_found`, not a misreading or a corpus contradiction. In each case the specific
identifier or ordering fact needed to pass the grader's exact assertion sat in a single
remark whose wording never intersected the agent's search vocabulary — one hidden behind a
comment-dump bug that only kept top-level replies, the other simply never said any of the
seven words the agent went looking for. The rest of both requirements — digest recipe,
envelope shape, auto-branch-only scoping, the zero-row-still-writes case, and all of r2 — were
recovered correctly and in depth.
