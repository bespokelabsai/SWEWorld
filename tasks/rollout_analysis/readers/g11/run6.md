# g11 run 6 (rollout f8059d35, eval 94bf8242, world-hosted v7) — reward 0.8889

## What this run found

The agent solved the open ticket cleanly (PR 730, CI green, merged to main after working
around a Gitea merge-API 500) and, on top of it, reconstructed almost the entire hidden
requirement tree from chat alone — no wiki, no mail were needed for g11 since all 47 remarks
live in Mattermost. Its search had two phases: a keyword API search (`ledger`,
`CHECKPOINT_REASONS`, `canonical_reasons`, `min_lr_ratio`, `current_batch`, `CheckpointInfo`,
…) that dumps individual matching messages, followed by whole-channel dumps to `/tmp/c_*.txt`
(~10k messages, step ~35-36) that it then grepped or printed by line range to recover full
exchanges. The second technique is what actually won this run: it recovered both herrings and
both reversals verbatim (lines 3968, 3813, 4017, 4204), the full `r2` LR-schedule rule/
observability/failure_behavior set, and most of `r1`'s scope/exclusions/observability facts.

## What it believed, and why

All four herrings (twin-checkpoint naming + alphabetical sort; decay-to-zero + strict
`step<warmup_steps`) were correctly identified as reversed and the reversals were followed
in the shipped code — `CHECKPOINT_REASONS=(interval,epoch,final)` order, `checkpoint_name`
identity, `effective_warmup=min(warmup_steps,total_steps)`, and the `MIN_LR_RATIO=0.1` floor
all match the reversal remarks exactly. No herring-following occurred anywhere in this run.

## What it missed, and why (the one lost fact)

`g11.r1.failure_behavior` scored 0 because the shipped `save_checkpoint` fully **overwrites**
a matching-name row (`self._checkpoints[-1] = checkpoint`) instead of **merging** the old and
new `reasons` tuples through `canonical_reasons`. The test expects a second save under the
last row's name to end with `reasons == ("interval", "final")`; the agent's code produces only
`("final",)`.

This is a genuine near-miss, not carelessness. The remark that states the merge — g11.r1.l17,
"the updated row takes the newer loss and carries both label sets forward" — was never actually
read. The keyword search only surfaced dario's opening question ("ledger q — same checkpoint
name got logged twice and i only got one row back. intended?", line 4165); the agent explicitly
planned a follow-up ("Print releases 505-600 and 300-345" / "Read releases 300-345 and 515-560",
line 4162) to pull the rest of that #releases exchange, but the terminal screen shown for that
turn ends on the 300-345 (herring) range — the 515-560 range containing dermot's merge answer
is never visible anywhere in the transcript (confirmed by exhaustive grep: "both label sets",
"newer loss", "carries both", "updated row" all return zero hits). What the agent *did* fully
read — l16 ("the new save takes that row's place instead of adding one") and rev1 ("one
save_checkpoint per step ... that's all there is on disk") — both use replace/overwrite
language, and its final Analysis (line 9035) states exactly that belief: "dedupe against the
last row only." The implementation is a faithful reconstruction of what it actually saw; the
one piece of information that would have corrected it fell off the edge of a scrolled terminal.

The identical pattern (keyword search hits only the question, not the reply) also cost the
agent `g11.r2.say19`'s payload, but that fact (`r2.exclusions_or_crossover`) survived because
`r2.l14`/`r2.l15` independently carried the same "resume reschedules off the new total_steps"
content.

## Notable

- 8 of 9 declared facts scored 1; the lost one is isolated to the reason-merge half of
  `r1.failure_behavior` — the unknown-reason-raises half of the same fact (l8) was fully found
  and correctly implemented.
- Gitea's PR merge API returned HTTP 500 citing an unrelated branch for all three merge
  methods; the agent worked around it with a local `--no-ff` merge + push, documented on the
  closed PR (lines 8578-8873) — unrelated to grading but worth flagging for other g11 runs on
  this world version.
