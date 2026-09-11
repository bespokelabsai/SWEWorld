# g11 run 2 (rollout 22513549, eval 94bf8242, world-hosted v7) — reward 1

## What this run found

This is a clean sweep: all 9 declared facts (r1.rule/scope/exclusions_or_crossover/
failure_behavior/observability, r2.rule/exclusions_or_crossover/failure_behavior/observability)
scored 1. The agent never had the hidden requirements handed to it — the ticket (transcript
line 117) says only that a checkpoint's name is "derived deterministically from
`config.checkpoint_name_prefix` and the step," with no mention of `CHECKPOINT_NAME_TEMPLATE`,
`CHECKPOINT_REASONS`, `canonical_reasons`, a `reasons` field, `MIN_LR_RATIO`, or
`effective_warmup` — every one of those was reconstructed purely from chat.

Its search strategy (steps 1–2, line 2265 onward) started narrow (a single Mattermost
full-text search for "tinker," one hit each in #general/#viewer) and, on recognizing that
was too thin, escalated to dumping every channel's complete post history to
`/tmp/chat_<channel>.txt` and running ~15 rounds of increasingly specific `grep -nE` passes
keyed off vocabulary lifted straight from the ticket (`dataset_signature`, `CheckpointInfo`,
`StepPlan`, `plan_steps`, `reasons`, `canonical_reasons`, `batches_completed`,
`current_batch`, `warmup_steps`, `MIN_LR`, `trainer`/`TrainingStats`). It also checked the
wiki (found essentially nothing — this corpus places all 47 remarks in chat) before
concluding chat was the primary record.

## What it missed, and why it didn't matter

Twelve of the 39 clue remarks (r1.l2/l9/l11/l13/l19; r2.l1/l2/l3/l6/l11/l12/l14) were never
individually surfaced by any grep the agent ran — not because the channel dumps were
truncated in any meaningful way, but because the agent's keyword list never happened to hit
their exact wording ("prefix is the only part... agree on," "nothing on disk to pick up,"
"four even ticks," "row A... wrecked the weights," etc.). Every one of these facts was still
carried redundantly by 2–4 other remarks that *were* found — e.g. r1.scope was fully closed by
`l10` (the bare-fixture "reasons come back exactly `('final',)`" case) and `l12` (Fireworks
"no reasons key... never writes checkpoints") without ever needing `l9`/`l11`. Both r1
herrings (`ledger-twin-checkpoints-dario`/`-emil`) were themselves only ever seen as
fragments — the surrounding back-and-forth about reason ordering was grepped, but the
defining "settled this in review — a step that trips both triggers writes both checkpoints"
lines were not. This caused no harm because the reversal threads (`rev1`/`rev2`) were
captured in full and unambiguous, and the agent's design summary (Analysis, line 3424: "one
save per step... CHECKPOINT_REASONS = interval/epoch/final ordering") shows it never
entertained the twin-checkpoint or alphabetical-sort alternative even provisionally.

## What it believed, and why

For all four herring/reversal pairs, the agent's Analysis text explicitly names the earlier
("settled," "decided") position and states that it was superseded, in every case citing the
later, dated remark as the reason (line 2287: "Chat contains the LR design discussion (decay
to zero at total_steps, strict warmup compare). I should dump the full channel histories to
read the whole record" — followed a few steps later by the correct, non-zero-floor
implementation). No herring was followed into the shipped code.

## Why nothing was lost

`lost_facts` is empty. The agent's own final Analysis (line 4647) is a near-complete
restatement of the answer key's two hidden requirements before a line of code was written —
checkpoint identity (`checkpoint_name(prefix, step)`, `reasons` appended last, keyword-only
default `('interval',)`, `canonical_reasons` in ledger order, unknown reasons raising
`StepLedgerError`, epoch/`gradient_accumulation_steps` taken off the plan of the batch
actually stopped on) and the LR schedule (`min_lr_ratio` keyword-only, `MIN_LR_RATIO=0.1`,
`effective_warmup=min(warmup_steps,total_steps)`, inclusive `1<=step<=effective_warmup`
warmup, floor held past the run's end). Reading the actual `step_ledger.py` writes
(transcript lines 4655–4820, 6100–6200) confirms the implementation matches this
reconstruction exactly, including `epoch_of_batch = (batch_ordinal-1)//batches_per_epoch+1`
computed from the plan rather than a loop variable. The agent then wrote 78 new tests pinning
every worked numeric example named in the record (10-example run's checkpoint names/reasons/
shapes; LR readings at min_lr_ratio 0.5 and 0.0; the 3-step mock run's 5e-05/1e-04/1e-05), ran
the full local suite (167 passed), diagnosed one pre-existing unrelated test failure via
`git stash` rather than assuming its own change broke it (lines 7154–7175), and — notably —
caught that the CI's fast gate logged `No module named pytest` during its "tests" step
(line 7577) and did not treat that green checkmark as sufficient, running the real suite
locally instead before declaring the task complete.

## Lost facts

None — see `lost_facts: []` in the JSON.
