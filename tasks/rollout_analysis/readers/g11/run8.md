# g11 run 8 (fa827d89) — reward 1, all 9 facts scored 1

## What this run found

After ~27 steps of terminal-mechanics overhead (printf `\n`-escaping, 10000-byte
output truncation, tmux-heredoc pitfalls the harness's own watchdog flagged
repeatedly), the agent dumped every Mattermost channel to a single 10,307-line
file and ran a sequence of broad-to-narrow greps: `ledger|dataset_signature|
optimizer step` first, then a wider `ledger|CHECKPOINT_|dataset_signature|
warmup|optimizer|packed|step_of|trailing|accumulation|tinker|fireworks`, then an
LR-specific pass (`decay|seed|deterministic|clock|rng|time.sleep`), then an
implementation-specific pass (`min_lr|canonical_reasons|checkpoint_name(|
step_unit|resumeplan|plan_steps`). Each hit line was expanded into a 40-50 line
`sed` read. This is a methodical, if slow, full-corpus sweep rather than a
targeted search — and it worked: 30 of 39 clues, all 4 herrings and all 4
reversals were read directly (transcript lines 2287-4230, step 28-67), never
touching BookStack or mail (both irrelevant here — all 47 remarks are chat-only
per the answer key's surface table).

The run correctly reconstructed both hidden requirements:

- **r1** (checkpoint reasons): `CHECKPOINT_REASONS = ("interval","epoch","final")`
  in ledger order (not alphabetical, not firing order), `canonical_reasons`
  dedup+validate, one `save_checkpoint` per step, tail-row replacement on a
  repeat name with reasons merged and the newer loss kept, `checkpoint_name`
  giving `checkpoint-s000002`, epoch taken from `plan.epoch_of_batch`, Fireworks
  writing nothing.
- **r2** (LR schedule): `MIN_LR_RATIO = 0.1` module constant, keyword-only
  `min_lr_ratio` rescaling the whole slope (not a clamp bolted onto a
  decay-to-zero line), inclusive 1-based warmup (`1 <= step <= effective_warmup`,
  `effective_warmup = min(warmup_steps, total_steps)`), clipped rather than
  raising when warmup exceeds the run.

## A real mid-run correction

At transcript line 3052 the agent briefly concluded the reasons ordering was
"trigger firing order, not alphabetical" — a plausible-but-wrong reading of the
earliest herring cluster alone. After reading the March reversal (`rev2`/`l7`,
line 3126) it corrected itself explicitly: the true rule is the fixed
`CHECKPOINT_REASONS` order, independent of firing order. The shipped
`canonical_reasons` implements the corrected version, so this cost nothing.

## What it missed and why it didn't matter

Nine of 39 clues (`g11.r1.l2`, `l9`, `l11`; `g11.r2.l7`, `l9`, `l11`, `l13`,
`l14`, `say19`) were never pulled into a read cluster — their distinctive
wording ("prefix", "nothing on disk", "gated on their config fields", "grid row
A", "current_batch straight on", "flatten out at a tenth") never matched any of
the keyword lists used. Grepping the transcript directly for each confirms they
are genuinely absent, not just paraphrased.

None of these losses touched a graded fact, for two structural reasons:

1. **The ticket already states some of it.** The Resume section spells out
   "the plan grows and the schedule continues from `completed_steps + 1`"
   outright, which covers what `l14`/`say19`/`l15` would otherwise be needed
   for (`r2.exclusions_or_crossover`).
2. **The formula clamps by construction.** Once the two LR reversals gave the
   agent `MIN_LR_RATIO=0.1` and the rescaled-slope formula, its own
   `progress = min((step-effective_warmup)/max(...,1), 1.0)`-style clamp holds
   the floor past `total_steps` and never goes negative — exactly what `l9`/
   `l11` describe from separate incident reports — without those reports being
   read.

So this run is a case where the corpus over-determined several facts: multiple
independent remarks (and in places the open ticket text) point at the same
requirement, and missing some of them left no visible gap.

## herrings

All four herrings (`g11.r1.ledger-twin-checkpoints-dario/-emil`,
`g11.r2.lr-decay-to-zero-dario/-konrad`) were read in full, and all four
reversals were also read and correctly identified as superseding the herring —
the shipped code follows none of the four herrings. The agent's own analysis
text names the supersession explicitly at lines 3126 and 2824.

## Why every fact landed (passed_facts)

- `r1.rule`/`r1.failure_behavior`: `l8`, `l16`, `l17`, `rev1`, `rev2` — the
  duplicate-name-merge and unknown-reason-raises behaviors are lifted almost
  verbatim from these remarks' quoted chat.
- `r1.scope`: `l10`'s fixture quote (`('final',)` with both switches off) is
  the load-bearing remark; `l12` supplies the Fireworks half.
- `r1.exclusions_or_crossover`: `l13`/`l14`/`l15` give the plan-sourced epoch
  and gradient_accumulation_steps directly.
- `r1.observability`: `l4`, `l18`, `l19`, the `say2x` cluster — all read and
  cross-checked against the agent's own sanity script output, which reproduced
  the exact values (`checkpoint-s000002`/`003`, `('interval','epoch')`/
  `('epoch','final')`).
- `r2.rule`/`r2.failure_behavior`: `rev1` and `rev2` are the two remarks that
  carry almost the entire hidden requirement — both read in full with the
  exact formula spelled out in chat.
- `r2.observability`: `l5` (`5.5e-05` then `1e-05` for 4 steps/warmup 2) was
  reproduced identically by the agent's own script before it wrote the trainer
  wiring.
- `r2.exclusions_or_crossover`: covered by `rev1` plus the ticket's own stated
  resume contract, as above.

## End state

Clean finish: `step_ledger.py` written, `TinkerTrainer`/`FireworksTrainer`
wired to it, local suite green (138 passed), committed as `362e0ed`, pushed to
`main`, Gitea CI green including deploy, running service confirmed healthy —
all matching the ticket's "Done means" bar.
