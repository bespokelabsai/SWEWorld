# g11 run 3 (bf174d55) — reward 1, all 9 facts carried

## What this run found

The agent went straight to Mattermost (correctly — all 47 g11 remarks live in chat, none in
wiki/mail), pulled the entire ~10k-post corpus to disk, and then iterated its own search tooling
three times (`s.py` exact-substring → `filt.py`/`filt2.py` broad keyword → `filt3.py` word-boundary
regex) until it stopped catching false positives like "lr" inside "already". It supplemented
keyword search with full-range channel reads of #engineering, #code-review and #help via `c.py`,
and separately confirmed the wiki (228 pages, fetched whole so BookStack's unindexed comments were
covered) and all 107 mail messages held nothing finetune-related — a correct negative, not a search
failure, since the plant record puts 100% of g11's remarks in chat.

This reconstructed both hidden requirements essentially completely. For **g11.r1** (one checkpoint
per step, carrying every firing reason) it recovered `CHECKPOINT_REASONS`/`canonical_reasons`
ordering and error-raising (l8, l6, l7), the six-digit `checkpoint_name` template (l2, l3), the
`reasons` field default and position (l4, say23), the replace-last-row merge semantics (l16, l17),
the epoch-of-the-closing-batch rule (l15), and the worked example values `checkpoint-s000002` /
`checkpoint-s000003` with `('interval','epoch')`/`('epoch','final')` (l18) — plus both reversals
(rev1, rev2), read in full, correctly recognized as superseding the two-checkpoint herring. For
**g11.r2** (warmup then decay to a floor) it recovered the exact schedule shape from a dense cluster
of #cookbooks/#viewer/#incidents/#help/#general remarks (l1, l2, l5, l6, l7, l8, l10, say20) and,
critically, both herrings AND both reversals in full context.

## What it missed, and why

Ten clue-only remarks (r1: l9, l11, l13, l14, l19; r2: l9, l11, l14, l15, say19) were never located.
All ten sit in #pipeline, #incidents, #general, #viewer or #releases, channels that never got a full
sequential `c.py` read — only #engineering, #code-review and #help did. None of the ten cost a fact:
each had a same-fact sibling the agent did find (e.g. r1.l13's "epoch off by two batches" is also
carried by l15, which the agent found in full), or the ticket itself already states the content
(r2.l15's "resume recomputes off the trainer's current total_steps" is also literally in the
ticket's Resume section). r2.l3's settling half (dario's "sitting on base_lr... not one step later")
was generated into a dump but sat past the terminal-screen truncation point and was never actually
read — only Konrad's opening question surfaced. Neither r1 herring's own turns were ever read
directly; their content reached the agent only secondhand, restated inside their own reversal
threads (rev1 at transcript line 4036, rev2 at line 3729) — sufficient, since the reversal turns
state the final rule completely on their own.

## What it believed, and why

For both r2 herrings the agent saw the herring AND its reversal in full multi-turn context (herring:
lines 2542/3383-3392 and 2550/3401-3414; reversals: lines 2736/2760-2776 and 2599/2637-2648) and
explicitly reasoned from the later, reversed state — "the LR schedule evolved through several
decisions ending June 2... decay bottoming at a fraction of base_lr" (line 2622). Nothing in the
shipped code follows either r1 or r2 herring.

## The rev2 rewording — this run saw the NEW text

v11 rewrote r2's second reversal (konrad, #general, 2025-06-02 10:16) to add the decay-floor half.
This run's world served the rewritten text verbatim — "the end doesnt sit at zero any more, it
bottoms out at a tenth of base_lr and holds there, and a first step at rate 0 is not something i
want to keep defending" — twice (transcript lines 2599-2602 and 2637-2640), not the stale
warmup-only wording still in the answer key on disk. The agent's shipped LR code (`MIN_LR_RATIO =
0.1`, `effective_warmup = min(warmup_steps, total_steps)`, `1 <= step <= effective_warmup`, clipped
rather than raising) matches the rewritten rev2 exactly, so judging this run against what the world
actually served — not the stale key — is the right call and changes nothing about the score.

## Why nothing was lost

No fact scored 0. `g11.r1.scope` (the thinnest-evidenced fact, since l9 and l11 were both missed)
still carried on l10 (the `test_trainer.py` fixture giving `('final',)`) and l12 (Fireworks writes
no `reasons` key), both found. The run's search strategy was broad enough, and the plant's
redundancy (each requirement carried by 15-26 remarks with multiple remarks per fact) forgiving
enough, that ten missed clues and two unread herrings still left every fact independently
reconstructable. Final verification: 145/145 tests passing, ruff clean, PR #737 merged to `main`,
CI green on the merge commit — confirmed by the agent before declaring done.
