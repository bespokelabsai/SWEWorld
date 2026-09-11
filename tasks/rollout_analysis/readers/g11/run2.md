# g11 run 2 (26946169-6513-4709-88ab-0f51fa1693e1, eval a8572080, task version 11)

**Reward 0.8889** (8/9 hidden facts, all provenance facts green). This is a strong, methodical
run: the agent logged into the Mattermost API, dumped all 12 channels (~12k messages) to local
files, then mined them with progressively refined keyword greps and wide `sed -n` context reads
across ~128 steps — plus checked every BookStack wiki page body *and comments* (comments are not
search-indexed) and Gitea PR/issue comments, correctly concluding nothing relevant lived outside
chat. It found and correctly believed all 4 herrings and all 4 reversals for both requirements
(g11.r1's twin-checkpoint write and alphabetical sort; g11.r2's decay-to-zero and strict
`step < warmup_steps`), and it independently re-verified the resume-schedule detail (`g11.r2.l15`)
in a late pass at step 118, just before submitting.

**What it found and built.** For `g11.r1` it correctly reconstructed: `CHECKPOINT_REASONS =
(interval, epoch, final)`, `canonical_reasons`'s ledger-order dedup, `checkpoint_name` →
`{prefix}-s{step:06d}`, "final" firing unconditionally while interval/epoch stay config-gated,
Fireworks writing no checkpoints, and the epoch recorded coming from `plan.epoch_of_batch` rather
than the loop variable — all backed by remarks it actually read (`l1`, `l3`, `l4`, `l6`, `l7`,
`l8`, `l10`, `l11`, `l12`, `l15`, `say23-25`). For `g11.r2` it reconstructed the whole `min_lr_ratio`
design (`l3`, `l9`, `l10`, `l13`, `say20`, and both reversals) and shipped the exact NEW wording
this v11 world serves.

**The rewritten rev2 turn.** This eval's task version rewrote konrad's reversal turn
`g11.r2.rev2` (#general, 2025-06-02) to retract *both* halves of the herring at once, not just the
warmup-compare half the repo's `hidden_requirements.md` still quotes. The world actually served
(transcript lines 3447-3449, general.txt line 239): *"...both of those are gone now. the end
doesnt sit at zero any more, it bottoms out at a tenth of base_lr and holds there, and a first
step at rate 0 is not something i want to keep defending."* The agent's initial Mattermost search
even caught the tail of this new wording as a 200-char snippet at step 23 (line 2466 — "...both of
those are gone now. the end doesnt sit a[t zero...]"), and it correctly re-read the full exchange
at step 43 (lines 3446-3457), producing an accurate Analysis: *"the tail no longer decays to zero
— it bottoms out at a tenth of base_lr and holds there"* (line 3486). Judging against what the
world actually served rather than the stale answer-key quote, this remark was fully carried — and
it made no difference to grading either way, since `g11.r2.rev1` (the `min_lr_ratio` design
itself) independently supplied everything needed for `g11.r2.rule`/`failure_behavior`.

**The one lost fact: `g11.r1.failure_behavior`.** The grader's failing assertion (from the raw
rollout junit) is `stored reasons: ['final'] != ['final', 'interval']` — the test saves a
checkpoint with `reasons=("interval",)`, saves again under the same name with
`reasons=("final",)`, and expects the merged row to carry `("interval","final")` with the newer
loss. The shipped `save_checkpoint` (transcript ~line 5507) computes
`recorded_reasons = canonical_reasons(reasons)` from *only* the current call's argument, then does
`self._checkpoints[-1] = checkpoint` — replacing the whole row rather than merging the reason
tuples. This is a genuine `not_found`, not an implementation slip: the agent's own summary (lines
5047, 5148) says only "save replaces the last ledger row when the name matches, else appends,"
never claiming a merge. The requirement's carrier, `g11.r1.l17`, never actually surfaced — only
its opening question ("ledger q — same checkpoint name got logged twice and i only got one row
back. intended?") appeared, as a truncated 200-char Mattermost search snippet at step 23 (line
2458). The informative half — dermot's replies "newer one wins, the updated row takes the later
loss" and "both carry forward onto it. neither set gets dropped" — never appears anywhere in the
7741-line transcript; releases.txt was read at lines 310-345 and 525-595 but never around the
~470 line this exchange sits at. `g11.r1.l16` (the plain "replace when name matches, else append"
rule, fully read at pipeline.txt 1436-1450) was found and correctly implemented, which is exactly
why the agent believed a bare replace was the whole story.

**Search strategy.** Exhaustive by source (chat dump-and-grep, wiki body+comments, mail, Gitea PR
comments) but the chat mining itself funneled through a keyword-filtered digest
(`/tmp/tl.txt`, 113-of-825 lines survived a `ledger|checkpoint|warmup|accumulat|signature|reasons|
packed` filter). About a dozen individual remarks (`g11.r1.l2/l5/l9/l13/l14/l19`,
`g11.r2.l1/l2/l4/l5/l6/l7/l11/l12/l14/say19`) never surfaced at all despite the raw text sitting on
disk — most were redundant with remarks that were found and cost nothing. The one exception,
`g11.r1.l17`, is the sole reason this run isn't a perfect score.
