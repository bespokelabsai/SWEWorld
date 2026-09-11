# g11 run 3 (dc2703c8, eval 94bf8242) — reward 0.8889

## What this run found

This is a strong, methodical run. The agent's search strategy was bulk-download-then-grep: it
enumerated every Mattermost channel, dumped each one's full post history to local files (fixing a
literal-`\n` bug along the way), then ran repeated targeted `grep -n` passes for domain vocabulary
(`ledger`, `reason`, `checkpoint`, `warmup`, `total_steps`, `dataset_signature`,
`CHECKPOINT_NAME_TEMPLATE`) and read the surrounding 15-40 lines of every hit to recover full
multi-turn exchanges rather than single lines. It never touched BookStack or IMAP mail in the
sampled regions, but that's not a gap here — all 47 g11 remarks live in chat only, per the answer
key's spread table.

Of 43 non-herring clues, the agent surfaced roughly 35 (verified against the pointer sheet and
independently by grepping each "not found" remark's distinctive phrases myself — none appear
anywhere else in the transcript). Both r1 herrings (twin-checkpoint writes, alphabetical sort) and
both r2 herrings (decay-to-zero, strict `step < warmup_steps`) were found, correctly recognized as
superseded ("Jan decisions superseded by March/April", line 4157; "(later revision)", line 3503),
and never followed in the shipped code.

## What it missed, and why

Only one fact scored zero: `g11.r2.rule`, because the shipped `learning_rate_at` signature has
`min_lr_ratio: float = MIN_LR_RATIO` as an ordinary defaulted parameter (line 6159), not
keyword-only — `test_r2.py` asserts `inspect.Parameter.KEYWORD_ONLY` and gets
`POSITIONAL_OR_KEYWORD`. The cause is a clean `not_found`: exactly one remark in the whole 47-item
set states this requirement, `g11.r2.l10` ("min_lr_ratio sits behind a bare `*` so callers have to
name it... also did a pass on 663"). The agent never opened that code-review.txt thread — "663"
appears twice elsewhere in the transcript (an unrelated closed-PR title at line 304, and an
unrelated release-timing ping at line 3564), so none of its grep passes for concept words like
"reason" or "warmup" happened to land on it. Every other detail of the r2 rule — `MIN_LR_RATIO =
0.1`, the floor formula, the inclusive 1-based warmup, the exact rate vectors — was correctly
reconstructed and cross-validated against the corpus's own numeric fixtures before the agent wrote
any code (lines 3654, 3704), which is why the remaining r2 facts (exclusions, failure_behavior,
observability) all scored 1 despite several other individual r2 clues (`l9`, `say20`, `l11`,
`say19`, `l14`) also going unfound — those were all redundant with clues the agent did find.

## What it believed, and why

The agent treated both pairs of herrings correctly. For r1, it read the Jan 21/28 "twin checkpoint,
alphabetical sort" decisions, then separately found the March 21/31 reversals stating one
`save_checkpoint` per step with `canonical_reasons` ordering by `CHECKPOINT_REASONS`, and explicitly
noted the Jan record was superseded before writing `_record_checkpoint`. For r2, it found the Jan
30/Feb 19 "decay to exactly 0.0, strict `step < warmup_steps`" herrings, then the March 26/June 2
reversals ("negative lr at step 99... dropping it", "the first step trained at rate 0... it's
`1 <= step <= effective_warmup` now"), and shipped the reversed rule (`effective_warmup =
min(warmup_steps, total_steps)`, inclusive 1-based ramp, floor instead of zero).

## Why each lost fact was lost

`g11.r2.rule` — the sole failing assertion is the keyword-only-ness of `min_lr_ratio`. No herring,
no other clue, and no ticket text pins this; it lives only in `g11.r2.l10`, which the agent's grep
vocabulary never intersected. This is not a corpus contradiction or an implementation slip against
its own stated reasoning — the agent never encountered the requirement at all.
