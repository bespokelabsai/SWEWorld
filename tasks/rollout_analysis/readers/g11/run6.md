# g11 run 6 (ca624f58) — reward 0.4444

## What this run found

The agent's search was almost entirely regex/keyword grep over a dumped Mattermost JSON, narrowing from
broad terms to exact plant vocabulary (`CHECKPOINT_REASONS`, `CHECKPOINT_NAME_TEMPLATE`, `canonical_reasons`,
`MIN_LR_RATIO`, `effective_warmup`, `dataset_signature`). Around step 31-34 it built a proper "±12 message"
context-window tool and used it for most hits, recovering full multi-turn exchanges — including the full,
**rewritten** `g11.r2.rev2` thread (#general, 2025-06-02 10:16, transcript line 3870): "we had it that decay
lands at exactly zero at total_steps and warmup keeps the strict `step < warmup_steps` compare... both of
those are gone now. the end doesnt sit at zero any more, it bottoms out at a tenth of base_lr and holds
there, and a first step at rate 0 is not something i want to keep defending." This is a v11 edit: the answer
key file on disk still shows the OLD wording (retracting only the warmup half). Judged against what the world
actually served, the agent read the new, fuller retraction correctly and implemented both halves
(`effective_warmup = min(warmup_steps, total_steps)`, clipped not raising, and a `min_lr_ratio`-scaled floor)
— consistent with all four r2 facts passing. It also saw and correctly disbelieved konrad's r2 herring
(line 2691) and both r1 herrings/reversals, never shipping herring behavior anywhere.

No wiki or mail search appears in the transcript; the plant record confirms all 47 remarks for g11 are chat-only
(9 channels), so that omission cost nothing.

## What it missed and why

Eleven of 47 remarks never surfaced at all (verified by direct grep, not just the pointer sheet): the search
vocabulary was built around identifier tokens, so free-text-only remarks (typo'd "epoch_end"/"end_of_epoch",
"grid row A", "current_batch straight on", "sitting at the bottom about a third") were never caught. None of
these losses mattered for the graded facts, because the same underlying rules were independently recovered from
other, better-worded remarks that were found.

One remark's *absence of full context* is directly responsible for a lost fact: `g11.r1.l17` (#releases,
2025-03-19 13:41 — "the updated row takes the newer loss and carries both label sets forward") appears in the
transcript only as its opening question line, a bare grep hit at line 2703. The context-window tool the agent
used for dozens of other threads was never re-run on this one, so the reply chain — "labels too? ... both carry
forward onto it. neither set gets dropped" — was never seen. The agent generalized instead from a different,
fully-read thread (`l16`, #pipeline) that only establishes *replace*, never *merge*.

## What it believed and why

For r2, the agent correctly believed every reversal over every herring: it implemented `MIN_LR_RATIO = 0.1`
with a `min_lr_ratio`-scaled floor (not zero), `1 <= step <= effective_warmup` with clipping (not the strict
`step < warmup_steps`), matching rev1 and the rewritten rev2 verbatim. It briefly mis-derived the decay shape
as **cosine** (Analysis, line 3523: "midpoint value confirms standard cosine formula") — an artifact of
`g11.r2.say20`'s `min_lr_ratio=0.5` midpoint value (7.5e-05) being numerically identical under linear and
cosine decay exactly at the halfway point — but self-corrected before implementing, once `g11.r2.l6` ("the
drops after warmup are all the same size") was read. This near-miss cost nothing.

For r1, the agent believed the reversals too (one checkpoint per step, ledger-owned naming, ledger-order not
alphabetical reasons) and never shipped the herrings' twin-checkpoint or alphabetical-sort behavior.

## Why every r1 fact was lost despite near-complete coverage

This is the headline finding: r1's failure is **not** a search/coverage failure. Nearly every r1 rule/scope/
observability remark shows `registered: requirement` and the agent's own final design summary states the
correct rules in prose. All five r1 facts still scored 0, from exactly two implementation bugs:

1. **The "epoch" checkpoint trigger fires on the wrong condition.** The agent wrote the *correct* primitive —
   `epoch_closing_steps()` in `step_ledger.py` ("Return, for each epoch, the step closing the window that
   holds its last batch") — and used it correctly for the sibling `loss_history_steps` method (which the
   open ticket itself specifies with the same wording). But the checkpoint-writing code in `train()` uses a
   different, wrong check instead: `batch_ordinal % plan.batches_per_epoch == 0`, i.e. "is this window's
   closing batch itself an exact multiple of `batches_per_epoch`" rather than "does this window contain an
   epoch's last batch." With `batches_per_epoch=4` and step windows closing at batches 3, 6, 8, only batch 8
   (a multiple of 4) satisfies the naive check — so step 2, whose window (batches 4-6) genuinely contains
   epoch 1's last batch (4), never gets the `"epoch"` reason. This single bug is what fails `r1.rule`,
   `r1.scope`, `r1.exclusions_or_crossover`, and `r1.observability` — all four tests assert on which steps get
   checkpointed and what reasons they carry.
2. **Duplicate-name save doesn't merge reasons.** `save_checkpoint`'s replace-on-matching-name path computes
   `recorded_reasons` from only the *new* call's `reasons` argument and overwrites the stored row entirely,
   instead of merging the old row's reasons with the new ones through `canonical_reasons` as the spec (and
   `g11.r1.l17`) require. This fails `r1.failure_behavior` alone. As above, this traces to `l17` never being
   read in full — the agent's own docstring for `save_checkpoint` only ever says the row "replaces," never
   "merges."

Final state was legitimately shipped and verified: `main` = `8bae540`, CI green, a fresh clone confirmed all
129 of the agent's *own* `tests/finetune` pass — but the grader's independent `test_r1.py` (never seen by the
agent) catches exactly the epoch-trigger and reasons-merge bugs above.
