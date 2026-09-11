# g11 run 1 (e0b0463c) — reward 0.8889, 8/9 hidden facts

## What this run found

This run's research phase is the most disciplined of the pattern: it wrote a Mattermost search
script, then a full-channel-pull script, dumped every channel to `/tmp/chat/*.txt` (code-review
3236 lines, pipeline 2008, engineering 2477, cookbooks 773, releases 701, incidents 270, viewer
338, general 261, help 150), and then worked almost entirely off local `grep`/`sed` against that
dump rather than re-hitting the Mattermost API. It caught all four herrings, both r1 herrings and
both r2 herrings, and all four reversals, and correctly believed every reversal — none of the
shipped code follows a herring. It recovered 42 of the 47 remarks (r1: all 22 remarks and both
herrings/reversals; r2: 15 of 20 clues plus both herrings/reversals), which is enough to pass 5/5
of `g11.r1`'s facts and 3/4 of `g11.r2`'s.

Its running "Analysis" text repeatedly names the exact parked decisions it is reconstructing —
"Key parked decision: checkpoints carry a `reasons` field (keyword-only)..." (line 3011), "Found
the LR schedule design thread: warmup then decay, bottoming out at a tenth of base_lr,
effective_warmup = min(warmup_steps, total_steps), compare 1 <= step <= effective_warmup" (line
3445) — and its final summary (lines 10036-10050) lists eight of the nine facts' content nearly
verbatim against the answer key, then ships it: `CHECKPOINT_REASONS` in ledger order,
`checkpoint_name(prefix, step)` zero-padded, replace-on-repeat-name, always-final-checkpoint,
plan-derived epoch/`gradient_accumulation_steps`, and the r2 decay shape with `MIN_LR_RATIO = 0.1`,
`effective_warmup`, and the `1 <= step <= effective_warmup` compare.

## What it missed, and why

The one fact it lost, `g11.r2.rule`, failed on a single assertion buried deep in a long test:
`judge.py`'s `eq(o["param_kind"], "KEYWORD_ONLY", ...)` — the shipped `learning_rate_at` defines
`min_lr_ratio: float = MIN_LR_RATIO` with no bare `*` before it, so `inspect.signature` reports
`POSITIONAL_OR_KEYWORD` instead of `KEYWORD_ONLY`. Every other assertion in that same test passed
(`MIN_LR_RATIO == 0.1`, every worked rate value) — this is a narrow, single-element miss, not a
wrong formula.

The requirement that `min_lr_ratio` sit behind a bare `*` is carried by exactly one remark,
`g11.r2.l10` (#code-review, 2025-05-30, nikolai/emil: "min_lr_ratio sits behind a bare * so
callers have to name it, MIN_LR_RATIO stays the module-level default"). It never surfaces
anywhere in the transcript — no grep for `663`, `bare`, or `min_lr_ratio` against the chat dump
ever ran (`min_lr_ratio` was only ever grepped against `/tmp/wiki`, never against `/tmp/chat`).
`code-review.txt` was pulled in full early on (step ~28), but every later re-print of it stayed
inside the March 14–April 14 window; the May-30 thread sits further down the same file and was
never revisited. This is a clean `not_found`, not a misread or an overridden read: the agent's own
final decision list (line 10045) records `min_lr_ratio`'s default and slope-rescaling behaviour in
detail but never once says "keyword-only," which is exactly what its research never told it.

## Herrings and the rewritten reversal

The run correctly distinguished all four herring/reversal pairs. Notably, `g11.r2.rev2` in this
world was rewritten for v11: the transcript shows what was actually served (`general.txt:239`,
picked up by a `warmup` grep at step 37/38): *"we had it that decay lands at exactly zero at
total_steps and warmup keeps the strict step < warmup_steps compare tinker_trainer already uses.
both of those are gone now. the end doesnt sit at zero any more, it bottoms out at a tenth of
base_lr and holds there, and a first step at rate 0 is not something i want to keep defending"* —
fuller than the answer key's on-file quote, which lacks the "bottoms out at a tenth of base_lr and
holds there" clause. This didn't change the outcome: the floor/clamp content was independently
carried by `g11.r2.rev1` and `g11.r2.l9`, both of which the agent also found, so the extra
sentence in the rewritten rev2 was redundant rather than load-bearing here.

## Bottom line

Lost fact: `g11.r2.rule` (one of nine, weight 1/9). Cause: `not_found` — the sole carrier of the
keyword-only constraint on `min_lr_ratio` (`g11.r2.l10`) was never located because no search the
agent ran (against a fully-dumped but not fully re-read `code-review.txt`) used any of its
distinctive vocabulary. Everything else this run reconstructed — one-checkpoint-per-step with
merged reasons, the fixed `CHECKPOINT_REASONS` vocabulary and ledger ordering, plan-derived epoch,
always-final checkpoints, and the full r2 decay shape including the (rewritten) warmup/floor
reversal — was found, correctly believed over its herring, and shipped faithfully.
