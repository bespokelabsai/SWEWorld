# g11 run 1 (94bf8242 / 3347ed25) — reward 0.5556

## What it found

This run's search was exhaustive and largely successful on `g11.r1` (checkpoint
reasons/identity): it exported every Mattermost channel to flat text files and ran
repeated broad greps for `ledger`, `checkpoint`, `epoch`, `reasons`, and specific
identifiers (`CHECKPOINT_REASONS`, `canonical_reasons`, `CHECKPOINT_NAME_TEMPLATE`),
following each hit with a full-context read of the surrounding thread. That
recovered the fixed reason vocabulary and its ledger order (not alphabetical, l6/l7),
the deterministic `checkpoint-s{step:06d}` name template (l2/l3/l18), the
config-gated interval/epoch triggers with an unconditional final checkpoint
(l10/l11/l12), the epoch-from-plan-not-loop-variable rule (l13/l14), the ten-field
`CheckpointInfo` ending in `dataset_signature` then `reasons` (l4/say23/say25), and
both r1 herrings (twin-checkpoint writes, alphabetical sort) correctly identified as
superseded via their reversals (rev1 at transcript line 3323, rev2 at line 2805).
`g11.r1.rule`, `g11.r1.scope`, `g11.r1.exclusions_or_crossover` and
`g11.r1.observability` all scored 1.

## What it missed, and why

**`g11.r1.failure_behavior` (0):** the code correctly replaces a repeat-named
checkpoint in place (from l16, fully read) but never merges the old and new
`reasons` tuples — the test wants `['final', 'interval']` after two saves and gets
only `['final']`. The only remark carrying that merge detail, `g11.r1.l17` (dermot,
#releases: "both carry forward onto it, neither set gets dropped"), was seen only as
its opening question line inside a broad grep dump at transcript line 2641 — the
answering half of the exchange was never re-opened for context, unlike every other
comparable thread in this run. This is a clean **not_found**.

**`g11.r2.rule`, `g11.r2.exclusions_or_crossover`, `g11.r2.observability` (all 0):**
all three trace to one root cause. The agent settled its `learning_rate_at` design
after just two threads — the `#viewer` herring ("zero. exactly zero at
total_steps", line 2551) and the `#general` June 2 reversal thread (line 2963) — and
never searched further. But that June 2 thread (`g11.r2.rev2`) only ever reverses
the *warmup-compare* half of the herring (`step < warmup_steps` →
`1 <= step <= effective_warmup`); it never touches the decay floor. The agent's own
Analysis at line 3028 misreads it as confirming "decay reaches exactly zero at
total_steps," and that belief ships unchanged into the final code (`max(base_lr *
remaining/decay_steps, 0.0)`, floored at literal zero). The correcting reversal,
`g11.r2.rev1` (#help, emil, "MIN_LR_RATIO = 0.1... ends at 1e-05"), was never found —
nor were four independent, redundant carriers of the same `MIN_LR_RATIO` fact
(`l9` #incidents, `l10` #code-review, `say20` #help, plus the numeric sequences in
`l5`/`l7`). Zero of the nine `MIN_LR_RATIO`-adjacent remarks in `#viewer`,
`#incidents`, `#code-review`, and `#help` were surfaced after the agent stopped
LR-specific searching. All three facts are **not_found**, with the r2 herring/reversal
split (two herrings, two non-overlapping reversals) as the structural reason a single
missed search pass produced three lost facts at once rather than one.

## Believed vs. reversed

Both r1 herrings were correctly reversed and never shipped. For r2, the warmup-strict-
compare herring was correctly reversed (feeds `g11.r2.failure_behavior`, scored 1),
but the decay-to-zero herring was never reversed in the agent's model — it is the
one belief in this run that survived, unchallenged, from a two-line grep hit all the
way into shipped code.

## End state

The feature was fully built, merged, and deployed with CI green — nothing here is an
infrastructure failure. The 0.4444 reward loss is purely four of nine hidden-requirement
facts, three of which collapse to a single un-found `#help` reversal.
