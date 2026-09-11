# g2 run 3 (rollout 069b893c, eval 9f2db992) — reward 0.7778

## What it found

This run's research was unusually thorough and well-organized. After reading the four target
source files and existing tests, it worked through every source systematically: BookStack's REST
API (fixing its own comments-parsing bug mid-run to reach the nested `comments.active` tree that
BookStack search does not index — pages 132/133/134 all fetched whole), IMAP mail (keyword search,
then a `SUBJECT 'executor'` sweep that recovered all five relevant threads whole), and Mattermost
(a keyword API search followed by dumping all 12 channels to local files for repeated grepping).
That pipeline recovered 33 of 38 non-herring clues and all 4 herring/reversal pairs — including
both reversals correctly overriding both herrings (rev1 over the "marker inside the budget" idea,
rev2 over the "dropped = original − max_bytes" idea, and the two `error_truncated`-shape herrings
in #viewer/#releases correctly overridden by their May reversals in #viewer/#cookbooks). The
shipped code gets `g2.r1.rule`, `g2.r1.scope`, `g2.r1.exclusions_or_crossover`, and all of `g2.r2`
right: head 3/4 + tail 1/4 with the `[[curator:elided N bytes]]` marker riding outside the budget,
UTF-8-safe boundary walking (≤3 bytes then `errors="replace"`), strict `>` only, `0` as an
off-switch that bypasses the floor, and `error_truncated` living on `CodeExecutionOutput` alone,
true only when the exception text itself was shortened.

## What it missed, and why

Both lost facts trace to the same root cause: two chat channels — **#cookbooks** (777 lines, 6
planted remarks) and **#incidents** (248 lines, 2 planted remarks) — were downloaded to local files
early (around step 40) but never actually read end-to-end. #incidents was dumped and then never
grepped or read again. #cookbooks was read in only two narrow windows (the 2025-04-21
`output_capped` manifest exchange and, later, the 2025-05-05 `error_truncated` reversal), which
happened to fall on either side of the two exchanges that mattered most: the 2025-03-14/03-17
floor-naming conversation and the 2025-05-01 except-handler-logging conversation.

**`g2.r1.failure_behavior` (0):** the grader's `ImportError: cannot import name 'OutputCapError'`
says it plainly — the shipped `output_cap.py` raises a bare `ValueError` from
`validate_max_output_bytes()`, with no named exception class, no `.max_bytes` attribute, and
message text that doesn't match the corpus's `"max_bytes must be 0 or at least 16, got {value}"`.
The agent did find `MIN_MAX_OUTPUT_BYTES=16` (via #pipeline) and "refuse at construction" (via
#code-review), so the floor and its timing are right. But the remark that names the exception class
— `g2.r1.l-floor-nikolai` (#cookbooks, 2025-03-14: *"i'd say call it OutputCapError, ValueError as
the base"*) — and the one giving the attribute and exact wording — `g2.r1.l-floor-konrad`
(#cookbooks, 2025-03-17: *"hang the offending value on the exception as .max_bytes"*) — both sit in
the very file the agent had already saved locally and simply never opened again. `g2.r1.say26`
(#incidents, the `field_validator`/`ValidationError` verbatim-message remark) was likewise never in
view.

**`g2.r1.observability` (0):** the failing assertion shows the exact double-count — a run whose
`__exit__` raises after a successful, already-truncated return logs the same warning line twice.
The shipped `_cap_captured_streams()` helper does the capping *and* the `logger.warning(...)` call
in one place, and that helper is invoked both in the success path (inside the `with Sandbox(...)`
block, before it can return) and again in the `except Exception` handler when salvaging the same
already-capped stdout. `g2.r1.l-log-konrad` (#cookbooks, 2025-05-01: *"the except handler's salvage
cap logs nothing, we log where we cut"*) states this exactly, and it too was never surfaced from
the same under-read channel.

## What it believed

All four herrings were correctly recognized as superseded — in each case the agent read the
herring and its reversal in the same channel dump within a few steps of each other and explicitly
reasoned about the more recent decision winning (e.g. "Mar 18 decision superseding the older marker
inside the budget," "error_truncated is on CodeExecutionOutput only now"). None of the four made it
into the shipped code.

One genuine internal tension in the corpus is worth flagging as a **notable**, not a lost fact: the
extended exchange around `g2.r1.l-kept-nils` (#engineering, 2025-03-19) contains a numeric aside —
"first 16k, last 48k" — that is tail-heavy, the opposite ratio from the 3:1 head-heavy split the
team settles on the next day (`g2.r1.l-kept-konrad`, #code-review, 2025-03-20). The agent noticed
the tension itself and correctly deferred to the later, more explicit remark; this did not cost a
fact.

## Bottom line

Provenance is clean (pushed, CI green, deployed) and 7 of 9 facts passed. The two lost facts are
not corpus gaps or grader defects — both remarks exist, are unambiguous, and sit in channels the
agent had already saved to disk — they were simply never read once the agent moved from broad
dumping to narrow, evolving keyword greps.
