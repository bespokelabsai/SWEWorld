# g1 run 8 (725ada84) — reward 1.00

## What it found and how

Lumen ran a textbook bulk-dump-then-grep strategy on all three surfaces, and it is the
reason this run scored perfectly despite the corpus scattering 50 remarks across 9 chat
channels, 2 wiki-page comment threads, and 4 mail threads over five months.

- **Wiki**: instead of trusting `/api/search` (which the ticket itself warns does not
  index comments), the agent fetched every page 1–129 whole via `/api/pages/{id}` into
  `/tmp/wiki/*.txt` (transcript line 1219), then grepped locally. Both wiki clues
  (`g1.r1.l2`, `g1.r2.l9`) are comments on page 7 ("Batch job status persistence across
  process restarts"), and the agent reached them only because it dumped the page whole
  (`/tmp/show.py`, line 1546) rather than searching for a term that lives only in a
  comment.
- **Mail**: dumped all 107 messages via raw IMAP into `/tmp/mail.txt` (line 1704), then
  grepped `planner|plan_batches|PlannedBatch|batch_plan|payload|auto`. This caught 3 of 4
  mail clues (`l10`, `l14`, `l12`) but missed `g1.r2.l6` ("resumed batch run
  double-submitted ~400 requests") — its body never contains any of those literal tokens.
- **Chat**: dumped every Mattermost channel across all teams into `/tmp/chat.txt` (9,921
  lines, line 2126), then repeated a broadening keyword grep and, whenever a hit landed
  mid-conversation, expanded with `sed -n 'START,ENDp'` to read the full exchange rather
  than the single matched line. This is what let it catch both herring/reversal pairs in
  the same read (e.g. `g1.r2.h2` and its reversal `g1.r2.rev2` both sit in the block read
  at lines 3592–3625).

## What it missed, and why it didn't cost anything

Eight remarks were never surfaced: `g1.r2.l8`, `g1.r1.say28`, `g1.r2.l2`, `g1.r1.l15`,
`g1.r2.l13`, `g1.r2.l10`, `g1.r2.l6`, `g1.r2.l5`. All eight are worded in ordinary
bug-report language — "rm -f", "`[10] * 512`", "metadata_3.json", "unlink", stale
`batch_plan.json`, "incomplete_files" — with no planner-specific noun the agent's grep
vocabulary ever tried. None of the ten graded facts were lost as a result: `spread_problems()`
guarantees at least two independent carriers per requirement, so each missed remark's
fact was covered redundantly by a sibling remark the agent did find (e.g. the missed
`g1.r2.l10` about `batch_objects.jsonl` being off-limits was covered by the found wiki
comment `g1.r2.l9`, which names the same file). Two scope facts (`g1.r1.scope`,
`g1.r2.scope`) leaned partly on the ticket's own explicit statement that the
explicit-integer `batch_size` and `dataset is None` paths keep their exact current
behaviour, which the agent quoted directly from the ticket rather than needing the corpus
at all for that half of the boundary.

## What it believed, and why

Both `g1.r1` herrings (metadata-carries-the-plan) and both `g1.r2` herrings
(sweep-runs-first) were read by the agent, but always in the same terminal screen as the
reversal or the thread that supersedes them — e.g. the `g1.r1.h2`/`g1.r1.rev2` pair sits
across lines 4846–4861 and 9238–9262 respectively, and the agent's running synthesis
(line 3642, "ordering superseded: plan first, then sweep, then write") treats the earlier
decision purely as historical context. It never shipped, or even briefly considered
shipping, either herring's design.

## Implementation fidelity

The shipped diff is a near-verbatim reconstruction of the answer key: `PLAN_FILE_NAME`,
`PLAN_FORMAT_VERSION=1`, `max_batches_per_plan` defaulting to 512, `BatchPlanTooFragmentedError`
as its own `ValueError` (not a `BatchPayloadTooLargeError` subclass) carrying `num_batches`/
`limit`, the exact `plan_document` key order, `plan_fingerprint`'s `start-end:num_bytes`
join-then-sha256[:12] recipe, and the plan→sweep→write ordering — none of which the ticket
text states. The agent even self-verified the fingerprint recipe by writing a throwaway
Python script (`/tmp/h.py`, line ~3601) and hand-computing sha256 digests against both
golden fixtures (`ad0828fea95e`, `e3b0c44298fc`) before committing to the implementation.
27 new unit tests were written and passed, the change was merged via Gitea PR #737 with
green CI on both the branch and merge commit, and the deployed `curator` service answered
healthy afterward.

## Lost facts

None — all 10 facts scored 1.
