# g11 run 5 (ee635c81, eval a8572080) — reward 1

## What this run found

This is a clean, fully-successful run: all nine graded facts scored 1. The agent ran a
disciplined, multi-pass keyword search across Mattermost — starting narrow
(`step_ledger|dataset_signature|StepPlan|ResumePlan|plan_steps`), widening once the LR
schedule surfaced (`min_lr_ratio|learning_rate_at|warmup`), then narrowing again around
`CHECKPOINT_REASONS|canonical_reasons` once the checkpoint-reasons design appeared. Crucially,
for nearly every grep hit it followed up with a full-context channel read (`sed -n` ranges,
narrow `cat`) rather than trusting the single-line snippet, which is why it recovered complete,
multi-turn exchanges for both requirements' herrings, reversals, and the great majority of
clues (transcript lines 2424-2438, 2588-2597, 2649-2656, 2701-2712 for the four
herring/reversal pairs; 3020-3466, 4300-4650 for r1's checkpoint-reasons design).

**All four herrings were seen with full context, and all four reversals too** — the agent never
shipped twin `{prefix}_step_{n}`/`{prefix}_epoch_{n}` checkpoints, never sorted reasons
alphabetically, never used the strict `step < warmup_steps` compare, and never decayed to exact
zero. Its own running analysis (lines 3089, 3140, 3240, 2516, 2737) correctly tracks each
herring as superseded the moment it reads the reversal.

**Notable corpus fact**: this rerun's world serves a *rewritten* `g11.r2.rev2` (v11 changed
konrad's #general 2025-06-02 line). The agent read the new wording in full at transcript lines
2701-2704 — "the end doesnt sit at zero any more, it bottoms out at a tenth of base_lr and holds
there, and a first step at rate 0 is not something i want to keep defending" — which differs from
the answer key's still-stale quote of the old wording, but carries the same underlying facts
(0.1 floor, `1 <= step <= effective_warmup`, clipped not raised). The rewrite changed phrasing,
not substance, so it did not affect what the agent had to build or how it scored.

## What it missed, and why it didn't matter

Roughly 19 of the 39 clue remarks were never surfaced by any grep or channel read the agent ran
(r1: `l2`, `l9`, `l11`, `l12`, `l13`, `l5`; r2: `l4`, `l7`, `l9`, `l11`, `l14`, `say19`), and four
more (r2 `l2`, `l6`, `l8`, `l12`) surfaced only as a single truncated line inside a broad grep
dump and were never re-opened. These gaps cluster in `#incidents`, `#general` and specific
date-windows within `#pipeline`/`#engineering`/`#code-review` whose distinctive wording never
matched the agent's evolving keyword vocabulary (e.g. "grid row A", "current_batch", "bumped
epochs from 1 to 6" contain none of the searched terms). None of this cost a fact: the plant's
`spread()` requirement guarantees at least two independent carriers per fact, and for every one
of the nine facts the agent found and fully read at least one complete carrier — often several.

## What it believed, and why

The agent's Analysis blocks show correct belief-tracking throughout: after reading each
herring/reversal pair it explicitly states the *current* (reversed) design as settled
("Older decisions (two records, alphabetical) were superseded in March by...", line 3240; "LR
design is clear-ish: warmup `1 <= step <= effective_warmup`...", line 2737). It cross-checked its
derived LR formula against every quoted numeric example in chat (5.5e-05/1e-05 for 4-step/warmup-2,
7.5e-05 for min_lr_ratio=0.5 halfway) before writing code, and independently corroborated the
"final always checkpoints" scope rule by reading `tests/finetune/test_trainer.py` directly rather
than relying on the chat remark alone.

## Why lost_facts is empty

All nine facts scored 1; there is nothing to explain here. The shipped `step_ledger.py`
(transcript lines 5440-5750) reproduces `MIN_LR_RATIO = 0.1`, `CHECKPOINT_REASONS = ("interval",
"epoch", "final")`, `CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"`, `canonical_reasons`
(dedup + canonical order + raise on unknown), `checkpoint_name`, and `learning_rate_at`
(warmup ramp to `base_lr` on the last warmup step, decay rescaled onto
`[base_lr*min_lr_ratio, base_lr]`, clipped `effective_warmup`) verbatim against what was read
from chat. 167 finetune tests pass (89 pre-existing behavior + 78 new), the commit is merged to
`main`, CI (`build-test-deploy`) is green, and the deploy-daemon's live release was verified
directly (line 8903) to reproduce the settled numbers end-to-end.

## Search strategy summary

Chat-only: no wiki or mail access appears anywhere in this transcript, and none was needed since
all 47 g11 remarks are chat-planted. The search was iterative-keyword rather than
channel-by-channel enumeration, which is efficient but leaves blind spots wherever a remark's
wording doesn't share vocabulary with the agent's current search terms — the four "partial"
remarks and nineteen "not found" remarks above are exactly that blind spot, offset entirely by
the plant's deliberate redundancy.
