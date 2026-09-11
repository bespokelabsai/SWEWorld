# g11 run 8 (34081783) — reward 0.8889

## What this run found

This is a strong, near-complete recovery. The agent read the whole `finetune/` module before
touching any external source (steps 1-14), then worked outward: Gitea issues (nothing useful —
title-search only), the wiki (full page listing, full-text search, then all 114 pages' raw JSON
with comments — correctly reasoned comments aren't indexed and fetched them anyway, found
nothing), mail (IMAP subject list + text search, one weak hit), and finally Mattermost, where the
entire hidden-requirement record for this task actually lives. Once in Mattermost it dumped every
channel's full history to files (step 26, line 2765) and ran a long, deliberately overlapping
series of grep sweeps — `ledger`, `reasons`, `cosine|decay|base_lr|learning rate|learning_rate`,
`padded|save_checkpoint|CheckpointInfo|...`, `TEMPLATE`, `min_lr_ratio|MIN_LR_RATIO|...` — each
time following a hit with `sed -n` over the surrounding lines to read the whole exchange rather
than trusting the one matched line. That discipline paid off: it recovered 33 of 47 remarks (70%),
including **both** requirements' complete herring→reversal pairs, and correctly identified every
reversal as superseding its herring (`code_followed_herring: false` on all four).

**Everything in `g11.r1` passed** — checkpoint identity (`checkpoint_name(prefix, step)` →
`checkpoint-s000002`, from l1/l3/rev1), the `CHECKPOINT_REASONS` vocabulary and `canonical_reasons`
order (l6/l7/l8/rev2), the unconditional final checkpoint and Fireworks' silence (l10/l12), the
plan-derived epoch (l15), and the merge-on-repeat-name semantics with newer-loss-wins (l16/l17).
The agent's own synthesis at line 5120 states this design almost verbatim before writing a line of
code, and the shipped `step_ledger.py` (line 5699-5795) implements it exactly — all five r1 facts
scored 1.

## What it missed, and why

`g11.r2.rule` is the one lost fact (8/9 → reward 0.8889). The failing assertion is exact:
`min_lr_ratio kind: 'POSITIONAL_OR_KEYWORD' != 'KEYWORD_ONLY'`. The shipped signature (line
5702-5708) is `def learning_rate_at(step, total_steps, base_lr, warmup_steps, min_lr_ratio: float
= MIN_LR_RATIO)` — no bare `*`. Every other value the function computes is exact: `MIN_LR_RATIO =
0.1`, the ramp `[2.5e-05, 5e-05, 7.5e-05, 1e-04]`, `lr(5)=8.5e-05`, `lr(7)=5.5e-05`, `lr(10)=1e-05`,
constant per-step gaps, and the `min_lr_ratio=0.5`/`0.0` special cases. The single remark that
carries the keyword-only requirement, `g11.r2.l10` (#code-review, 2025-05-30, "min_lr_ratio sits
behind a bare \* so callers have to name it... PR 663"), never surfaces anywhere in the transcript
— grepping the full transcript for "663", "bare \*", and "min_lr_ratio sits behind" returns zero
hits before the code is written. The cause is a genuine vocabulary gap: every LR search the agent
ran was built around `cosine|decay|base_lr|learning rate|learning_rate`, none of which appear in
l10's wording, and `#code-review` was only dumped/grepped for the Mar-14–Apr-14 "reasons" clusters,
never for the late-May PR-663 date range. This is `not_found`, not a reasoning failure — nothing
in the corpus that the agent actually read argued against keyword-only, and its own implementation
notes never mention the question at all.

Six other remarks were never found for the same reason (vocabulary outside the grep sweeps run):
r1's `l2`, `l5`, `l9`, `l11`, `l13`, `l14`, `l19`, and r2's `l1`, `l2`, `l6`, `l11`. None of these
cost a fact, because each requirement had redundant carriers — e.g. r1.exclusions was carried by
both `l13` and `l15`, and only `l15` was found, but that was enough. One remark, `g11.r2.l12`,
surfaced only as a bare line inside a generic grep dump (line 2981) that was never expanded with
`sed -n`; this is the run's one `partial` find, and again cost nothing since `rev2`/`l13` covered
the same ground.

## What it believed, and why

Both herring/reversal pairs were resolved correctly. For r1, it read the Jan-21/Jan-28 herrings
("both checkpoints... names stay `{prefix}_step_{n}`/`{prefix}_epoch_{n}`... sorted alphabeticaly")
directly, then their reversals (`rev1` at line 3639, `rev2` at line 3376) later in the same
threads, and its Analysis explicitly tracks which is current. For r2, it saw the Feb-19 herring
("decay lands at exactly zero... strict `step < warmup_steps`") via both a raw search hit (line
2754) and full-thread reads (lines 3742-3744, 3923-3924), and its Analysis at line 3957 states
plainly "Feb 19 is the old (superseded) design" before reading the June-2 reversal.

Worth flagging: **this run's world served a rewritten `g11.r2.rev2`** (per the task context, v11
changed konrad's June-2 turn). The transcript shows the new text at line 2896-2900: "both of those
are gone now. the end doesnt sit at zero any more, it bottoms out at a tenth of base_lr and holds
there, and a first step at rate 0 is not something i want to keep defending" — this restates the
decay-floor value in addition to the warmup-compare change, unlike the answer key's stored (older)
wording, which only announces the warmup half is going. The agent's Analysis at line 2957 shows it
correctly absorbed exactly what was served ("warmup compare `1 <= step <= effective_warmup`...
decay bottoms out at a tenth of base_lr"), and the shipped code matches. This had no grading
impact — MIN_LR_RATIO=0.1 was also, independently, sourced from `rev1` — but it means the judged
behavior here should be scored against the served text, not the repo's stale key quote.

## Summary of lost facts

| fact | cause | evidence |
|---|---|---|
| `g11.r2.rule` | `not_found` | `g11.r2.l10` (bare-`*` keyword-only requirement) never surfaced; grep vocabulary never covered it; failing assertion: `min_lr_ratio kind: 'POSITIONAL_OR_KEYWORD' != 'KEYWORD_ONLY'` |
