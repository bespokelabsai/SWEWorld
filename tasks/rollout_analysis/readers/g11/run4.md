# g11 run 4 (ba527345) — reward 0.8889

## What this run found

This is a near-perfect run: 8 of 9 hidden facts scored, CI green, pushed and deployed
(transcript lines 9100-9159). The agent never read any single channel top-to-bottom; instead
it grepped the whole chat corpus for finetune vocabulary (`checkpoint`, `reason`, `template`,
`warmup`, `decay`, `tenth`/`floor`, `current_batch`, …), dumped the hits plus surrounding
context into `/tmp/ftctx.txt` (539 lines), and paged through that file in ~40-line chunks
(lines 3080-5950). It also checked BookStack in full — `/api/pages?count=500` plus each
page's own comments (lines 2101-2588) — and IMAP mail (lines 2631-2658), correctly finding
nothing there since every one of g11's 47 remarks lives in Mattermost chat.

Both `r1` herrings (twin checkpoints named `{prefix}_step_{n}`/`{prefix}_epoch_{n}`,
alphabetical reason order) and both `r2` herrings (decay to exact zero, strict
`step < warmup_steps`) were surfaced, along with all four reversals (lines 3817/3850,
4603/4019, 3188/4151, 5017/3240). The agent believed every reversal and shipped none of the
herring behavior — `acted: contradicted` for all four herring rows.

The agent also did real reconstruction rather than transcription: from `g11.r1.l15`'s raw
numbers ("batches_completed 6" / "3, 2, 8") it algebraically derived the exact `StepPlan`
shape (`batches_per_epoch=4`, `gradient_accumulation_steps=3`, lines 4945-4953) before the
ticket's own worked example confirmed it, and it independently re-derived the LR decay
formula from the 3-step/warmup-2 mock numbers (line 4291).

## What it believed, and why

Its own mid-run synthesis (lines 5955-5964) lists all ten settled-but-parked decisions it
had assembled from chat — `CHECKPOINT_REASONS` order, `canonical_reasons` semantics,
`checkpoint_name(prefix, step)` format, replace-on-repeat-name semantics, epoch-from-plan,
and the full `learning_rate_at` formula with `MIN_LR_RATIO=0.1`, `effective_warmup =
min(warmup_steps, total_steps)`, and the inclusive `1 <= step <= effective_warmup` compare.
Every one of those matches the answer key and passed its grader test.

**Notable — the rewritten reversal.** v11 rewrote `g11.r2.rev2`'s wording, and the world this
run actually played against served the new text: "the end doesnt sit at zero any more, it
bottoms out at a tenth of base_lr and holds there, and a first step at rate 0 is not
something i want to keep defending" (transcript lines 3242-3243). The agent read and relied
on exactly this text (Analysis at line 3281); the answer key document's own "As it appears"
quote block still shows the pre-rewrite wording without that sentence, which is a staleness
in the key, not an agent error.

## Why the one lost fact (`g11.r2.rule`) was lost

`test_rule__inclusive_warmup_then_a_linear_decay_to_a_tenth_of_the_base_rate` failed on
exactly one assertion: `inspect.signature(learning_rate_at).parameters['min_lr_ratio'].kind
is inspect.Parameter.KEYWORD_ONLY`, reported as `'POSITIONAL_OR_KEYWORD' != 'KEYWORD_ONLY'`.
The shipped signature is `def learning_rate_at(step, total_steps, base_lr, warmup_steps,
min_lr_ratio: float = MIN_LR_RATIO) -> float:` — a normal defaulted parameter, no bare `*`
before it.

Cause: **not_found**. `g11.r2.l10` (nikolai, #code-review, 2025-05-30 — "also did a pass on
663 - min_lr_ratio sits behind a bare * so callers have to name it, MIN_LR_RATIO stays the
module-level default") is the *only* remark among all 47 that states this constraint, and it
never appears anywhere in the ~9,200-line transcript, in any of the agent's grep passes or
`ftctx.txt` pages. The agent did find and correctly apply the *sibling* keyword-only
requirement — `save_checkpoint`'s `reasons` kwarg (line 3000: "keyword only... it comes back
from canonical_reasons") — but that thread never touched `min_lr_ratio`, and its own
requirements list (line 5955-5964, item 10) never mentions keyword-only for `min_lr_ratio`.
Every other part of `test_rule` — `MIN_LR_RATIO == 0.1`, the ramp/decay values, the
`min_lr_ratio=0.5`/`0.0` rescale behavior — passed cleanly.

Two further remarks (`g11.r1.l5`, `g11.r2.l11`) also never surfaced, but their facts still
scored 1: other remarks (`l1`/`l3`/`l6`/`l7`/`rev1`/`rev2` for `r1.rule`;
`l9`/`l14`/`rev1`/`l1`/`l5`/`l6`/`l7` for `r2` exclusions/observability) carried the same
content redundantly, which is exactly the spread-redundancy the plant is designed to have.
