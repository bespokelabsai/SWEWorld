# g11 run 10 (a8572080 / 1fdcca2f) — reward 0.8889

## What this run found

The agent reconstructed both hidden requirements almost completely from a purely
chat-based search: a Mattermost REST login (step 27), short keyword snippet
searches (`ledger`, `dataset_signature`, `step_plan`, `tinker`, `ResumePlan`,
then `cosine|decay|warmup`, then `reason`, `CHECKPOINT_REASONS`,
`CHECKPOINT_NAME_TEMPLATE`, `resume`), followed by a full per-channel dump to
`/tmp/mm/*.txt` and targeted `grep -n` / `sed -n 'A,Bp'` reads of the resulting
line ranges. It also checked BookStack and IMAP mail for finetuning terms and
correctly found nothing there — all 47 g11 remarks live in chat, per the plant
record. The agent shipped `step_ledger.py` with `learning_rate_at`
(`effective_warmup = min(warmup_steps, total_steps)`, `1 <= step <=
effective_warmup`, `min_lr_ratio` floor with `MIN_LR_RATIO = 0.1`, holds past
the planned end), `canonical_reasons` (`CHECKPOINT_REASONS` order, raises
`UnknownCheckpointReason` on an unknown value), `checkpoint_name` via
`CHECKPOINT_NAME_TEMPLATE`, and `CheckpointInfo` ending
`..., dataset_signature, reasons` — matching the answer key's `r1.rule`,
`r1.scope`, `r1.exclusions_or_crossover`, `r1.observability`, and all four
`r2` facts. CI went green and the change deployed (`provenance.*` = 1, 162
finetune tests passed locally).

## What it missed, and why

The single lost fact is `g11.r1.failure_behavior`: the grader's merge test
(`save_checkpoint(name, reasons=("interval",))` then
`save_checkpoint(same name, reasons=("final",))` must yield stored
`reasons == ("interval","final")`) failed with `stored reasons: ['final'] !=
['final', 'interval']`. The shipped `save_checkpoint`
(`if self._checkpoints[-1].name == name: self._checkpoints[-1] = checkpoint`)
replaces the row wholesale with the new call's own `reasons`, discarding the
prior call's — because the agent never saw the one remark that states the
merge, `g11.r1.l17` ("both carry forward onto it. neither set gets dropped",
dario/dermot, #releases, 2025-03-19). It surfaced only as a 90-character
Mattermost search snippet showing dario's *opening question* ("ledger q — same
checkpoint name got logged twice…", line 2627/2630). The agent then targeted
`sed -n '515,570p' releases.txt` to read that exact window (full rollout JSON
msg 89), but the tool result (msg 90) is a height-bounded "Current Terminal
Screen" that starts well past the whole 7-turn l17 exchange — the reply
containing the merge instruction never appears anywhere in the 7569-line
transcript (grepped for "carry forward", "labels too", "neither set gets
dropped": zero hits). The agent's own final design notes (lines 4797,
7293-7302, 7541) describe only replace semantics — pulled correctly from
`g11.r1.l16`, which *was* seen in full — with no mention of merging reason
tuples. A second instance of the same truncation pattern hit the herring
`g11.r1.ledger-twin-checkpoints-dario` (`sed -n '320,370p' releases.txt`), but
cost nothing because the sibling herring and both r1 reversals were seen in
full and independently pinned the right design. Six other remarks (`r1.l5`,
`r1.l7`, `r1.l9`, `r1.l13`, `r2.l11`, `r2.l14`) were never surfaced by any
search this run issued at all, but every requirement they carry had other,
found carriers, so no fact was lost to those gaps.

## What it believed, and why

All four herrings were correctly *not* followed. `g11.r2.lr-decay-to-zero-konrad`
and its reversal `g11.r2.rev2` were both seen in full — and this run's world
served a **rewritten** rev2 (#general, konrad, 2025-06-02 10:16) that now
explicitly retracts the decay-to-zero half too ("the end doesnt sit at zero
any more, it bottoms out at a tenth of base_lr and holds there"), not only the
warmup-compare half the answer key file still quotes. The shipped code matches
what the world actually served (`min_lr_ratio`, not decay-to-zero by default;
`1 <= step <= effective_warmup`, not the strict herring compare), so this is
not a scoring discrepancy, just a plant-vs-key drift worth flagging.

## Search strategy

Snippet-based Mattermost search first (fast but only ~90 chars per hit — this
is what turned `g11.r1.l17` into a question-only fragment), then a full
channel-dump-and-grep pass that recovered most remaining remarks in full.
Wiki and mail were checked and correctly ruled out. The one systemic weakness
is the two `sed` reads whose tool result was a bounded "Current Terminal
Screen" rather than cumulative "New Terminal Output," silently dropping the
top of the requested line range — this is the direct mechanical cause of the
one lost fact.
