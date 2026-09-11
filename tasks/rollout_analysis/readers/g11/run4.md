# g11 run 4 (d6f00008, eval 94bf8242) — reward 0.7778

## What this run found

The agent dumped the entire Mattermost history for all 12 channels to local files
early on and then grepped that corpus repeatedly for the ticket's own vocabulary
(`step_ledger`, `dataset_signature`, `min_lr_ratio`, `learning_rate_at`,
`CHECKPOINT_REASONS`, `warmup`, `checkpoint name`, etc.), reading full threads with
`sed` whenever a hit landed. This strategy worked almost perfectly for **g11.r2**
(the learning-rate schedule): every clue, both herrings, and both reversals were
found, because the ticket already uses the same words the plant used
(`min_lr_ratio`, `warmup_steps`, `total_steps`). All four r2 facts (rule,
exclusions_or_crossover, failure_behavior, observability) scored 1 — the agent
correctly reconstructed the inclusive `1 <= step <= effective_warmup` ramp,
`effective_warmup = min(warmup_steps, total_steps)`, decay to `MIN_LR_RATIO = 0.1`
as a keyword-only parameter, the clamp-past-the-end behavior, and the
resume-continues-on-the-new-length-from-`completed_steps+1` behavior, all directly
from remarks it found and read in full (line 3126 for the key reversal, line 2997
for the other).

**g11.r1** (checkpoint identity) coverage was much patchier despite the same
channels being locally available. The agent found the `reasons`/
`CHECKPOINT_REASONS`/`canonical_reasons` thread (the ticket also uses "reasons"),
the coincident-step behavior, the scope (final-always, Fireworks-never) and one of
the two exclusions_or_crossover carriers (l15, the epoch-of-batch-not-loop-variable
remark, read in full at line 4992). But it never queried for the literal string
`CHECKPOINT_NAME_TEMPLATE`, `get_checkpoints`, or `epoch_end`/`end_of_epoch`, and
never read engineering.txt or pipeline.txt as exhaustively as it read
viewer.txt/general.txt/help.txt for r2. Nine r1 remarks (l1, l3, l5, l9, l11, l13,
l14, l16, l17) were never surfaced — confirmed by grepping the full transcript for
each remark's distinctive text and getting zero hits.

## What it missed and why

Two of nine facts scored 0, both `not_found` — not a task defect, not a herring
followed, not an implementation slip against something the agent understood.

- **g11.r1.rule** (0): the grader's `test_rule` fails at
  `sym("CHECKPOINT_NAME_TEMPLATE").format(...)` because the module exports no such
  constant. The agent reconstructed the *shape* of checkpoint names correctly —
  `checkpoint_name(prefix, step)` returning `f"{prefix}-s{int(step):06d}"` — but
  entirely from the reversal remark `g11.r1.rev1` ("checkpoint_name(prefix, step),
  nothing else feeds it. so step 2 gets you checkpoint-s000002", line 4029). The
  one remark that names the actual constant, `g11.r1.l3` ("the format goes through
  CHECKPOINT_NAME_TEMPLATE in the ledger"), was never found. Everything else this
  fact also covers — ledger-order `CHECKPOINT_REASONS`, `canonical_reasons`
  dedupe/order, and one `save_checkpoint` call per coincident-trigger step — is
  genuinely correct in the shipped code (the train loop accumulates all firing
  reasons into one list before a single call, verified directly in the diff), but
  the test never reaches those assertions because it fails on the second line.

- **g11.r1.failure_behavior** (0): `test_failure_behavior` fails on
  `assert len(stored) == 1` after two `save_checkpoint` calls under the same name —
  got 2, not 1. The unknown-reason-raises half of this fact is correctly
  implemented (from `g11.r1.l8`, found early at step 31). But the
  merge-on-repeat-name half was never implemented at all: the original
  `save_checkpoint` unconditionally appends to `self._checkpoints`, and the
  agent's patch only added shape/reasons keyword arguments to the `CheckpointInfo`
  constructor — no branch was ever added to check whether an incoming name
  matches the ledger's last entry. The two remarks carrying this behavior
  (`g11.r1.l16`, `g11.r1.l17`) were never surfaced, and the agent's own
  Analysis/Plan text never once mentions "merge" or "replace" in connection with
  checkpoints — it never knew this requirement existed.

## What it believed, and why

All four herrings were correctly *not* followed. Interestingly, the agent barely
read the r1 herrings' own posts (one grep-hit line each, at step 88/75) — its
belief that the twin-checkpoint/alphabetical-sort design was obsolete came
entirely from the two reversal remarks' retrospective descriptions ("we stopped
writing two records", "alphabetical put final ahead of interval ... thats gone"),
not from encountering the herring and then updating. For r2, both herrings and
both reversals were read as full threads, and the agent explicitly reasoned in its
Analysis text: "Feb 19 is the older LR design; June 2 supersedes it" — a clean,
correct resolution.

## Provenance

Merged to main (`11c556d`), CI green, service healthy at the final check; 142/142
finetune tests passed locally (89 existing + 53 new). No infra issues.
