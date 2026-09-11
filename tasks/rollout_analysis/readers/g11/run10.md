# g11 run 10 (eb0dccde) — reward 0.7778

## What it found

The agent ruled out wiki (all 228 BookStack pages enumerated and searched — none finetune-related)
and mail (all 107 IMAP messages dumped and grepped — none relevant) before settling on Mattermost
as the sole source, which matches the plant record: all 47 g11 remarks live only in chat. It then
dumped every channel to `/tmp/chat/*.txt` (good practice) and ran a sequence of vocabulary-targeted
greps (`ledger`, `CHECKPOINT_NAME_TEMPLATE|step_unit|dataset_signature|...`,
`min_lr_ratio|decay|cosine|...`, `seed|determinis|time.sleep|clock`,
`trailing window|loss_history|mismatched|plan_resume|...`).

This recovered `g11.r2` almost completely: the two reversal remarks (`g11.r2.rev1`, line 2613, and
`g11.r2.rev2`, line 2441) are dense with literal identifiers (`MIN_LR_RATIO = 0.1`,
`effective_warmup = min(warmup_steps, total_steps)`, `1 <= step <= effective_warmup`, `7.5e-05`),
so grep vocabulary hit them squarely, and between them plus `l5`/`l8`/`l10`/`say19`/`say20` the
agent reconstructed the full warmup/decay/clip/resume design (line 3693) and implemented it
correctly — all four `g11.r2` facts scored 1.

It also recovered most of `g11.r1`'s checkpoint-identity design the same way: `rev2` (line 2932,
superseding the Jan-28 "two rows / alphabetical" herring), `l1`, `l3`, `l6`, `l7`, `l8`, `l15`,
`l16`, `l17`, `l18`, `say23`, `say24`, `say25` were all found and correctly implemented — `rule`,
`exclusions_or_crossover` and `failure_behavior` all scored 1.

## What it missed, and why

`g11.r1.scope` and `g11.r1.observability` both scored 0, and both fail on the same line of code.
The grader's fixture case (`checkpoint_every_n_steps=0, checkpoint_every_epoch=False`) expects
`reasons == ('final',)` on the last step; the agent's code produces `('epoch', 'final')` — it fires
the `epoch` reason whenever a step closes an epoch's window, regardless of whether
`checkpoint_every_epoch` is even set.

The cause is a single missing clue. `g11.r1.l11` (code-review, 2025-03-18) is the only remark in
the answer key that states the gating rule outright: "leave the interval and the per-epoch
triggers gated on their config fields exactly as they are, plenty of runs have both off on
purpose." Grepping the whole transcript for its distinctive phrases turns up nothing — it was
never surfaced, because none of the agent's grep vocabulary (identifier-heavy: `CHECKPOINT_NAME_TEMPLATE`,
`min_lr_ratio`, etc.) matches plain English like "gated on their config fields." The sibling clues
that carry the same fact (`l9`, `l10`, `l12`-in-full) were likewise never surfaced for the same
reason — the entire `g11.r1` scope cluster sits in plain-prose threads in `#pipeline` and
`#code-review` around 2025-03-14–19 that the agent's dumped-but-unread channel files never got a
broad, unfiltered pass.

Without that clue, the agent invented the opposite rule from what it *did* see — the observability
walkthrough (`l18`: `checkpoint-s000002`=`('interval','epoch')`, `checkpoint-s000003`=`('epoch','final')`)
— reasoning at line 3696/4841: "reasons name the shape of the step: `epoch` whenever the step
closes an epoch even if `checkpoint_every_epoch` is off." It then ran its own manual verification
(lines 4997–5039) using a config that never set `checkpoint_every_epoch` — so it defaulted to
`False` — and got `reasons [('interval', 'epoch'), ('epoch', 'final')]` back. Rather than reading
this as a red flag, the agent concluded "the ledger reproduces the record exactly" (line 5045),
because the two-row/two-name shape happened to match the observability walkthrough it had
over-generalized from. That manual run is, verbatim, a live demonstration of the bug the grader
later caught — the agent watched it happen and called it correct.

## Herrings

All three herring/reversal pairs the agent actually encountered were resolved correctly in favor
of the reversal: the r1 twin-checkpoint herring (emil, Jan 28) against its March reversal, and both
r2 lr-schedule herrings (decay-to-zero, strict warmup compare) against their reversals. The fourth
pair — the r1 twin-checkpoint herring from Dario (Jan 21) and its reversal (Dermot, Mar 31) — was
never encountered at all, but its content is redundant with the emil/rev2 pair the agent did find,
so no fact was lost to it.

## Bottom line

Two facts lost (`g11.r1.scope`, `g11.r1.observability`), both `not_found` on the same clue
(`g11.r1.l11`, reinforced by `l9`/`l10`), both manifesting as the identical implementation bug: the
`epoch` checkpoint reason fires unconditionally instead of being gated on `checkpoint_every_epoch`.
Everything else — nine of the eleven graded facts, all of `g11.r2`, and the full checkpoint-identity
design for `g11.r1` — was correctly recovered and implemented.
