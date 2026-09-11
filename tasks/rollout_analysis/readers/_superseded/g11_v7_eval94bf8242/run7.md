# g11 run 7 (66a0621c) — reward 0.8889 (8/9 facts)

## What it found

This run read the finetune module and its tests cover to cover, then worked outward
through the sources roughly in the order the corpus actually holds them: Gitea
issues/PRs (nothing world-specific), the BookStack wiki (nothing on fine-tuning —
correct, g11 has zero wiki remarks), IMAP mail (nothing — correct, zero mail
remarks), and finally Mattermost, where all 47 of this task's remarks in fact live.
Its first chat pass was the built-in search API for terms like `ledger` and
`dataset_signature`, which returns single-message snippets; this is where three
remarks were only ever glimpsed as a thread's opening line (see "What it missed"
below). Recognizing the limits of that, the agent switched to dumping all nine
channels to local files and running a custom context-extraction script over a
hand-tuned finetune vocabulary, reading the results in ~80-line chunks across
dozens of turns. That second method is what actually recovered the design record:
full multi-turn threads for the checkpoint-reason taxonomy (`CHECKPOINT_REASONS`,
`canonical_reasons` in ledger order not alphabetical), the name template
(`checkpoint_name(prefix, step)` → `checkpoint-s000002`), the always-checkpointed
final step and Tinker-only scope, the plan-derived `epoch`/`gradient_accumulation_steps`,
the replace-last-row-on-repeat-name rule, and the full learning-rate schedule
(`effective_warmup = min(warmup_steps, total_steps)`, ramp to `base_lr` at the last
warmup step, `min_lr_ratio`-rescaled decay holding at the floor past the end,
module constant `MIN_LR_RATIO = 0.1`, keyword-only). All four herrings (two per
requirement) were seen alongside their reversals and correctly resolved in favour
of the later, reversing message — the run explicitly reasons "the January
discussion is the superseded era" and drops the two-checkpoints / alphabetical /
decay-to-zero / strict-`<` designs entirely. Every one of these facts shipped
correctly: `g11.r1.rule`, `.scope`, `.exclusions_or_crossover`, `.observability`,
and all four of `g11.r2`.

## What it missed, and why

Six clues (`g11.r1.l5`, `.l9`, `.l11`, `.l13`, `g11.r2.l11`, `g11.r2.l14`) never
surfaced in any search the agent ran — a genuine gap, though a harmless one here,
since every fact they carried was independently recovered from a sibling remark
(e.g. `l9`/`l11`'s scope content came back through `l10`/`l12`). Three more
(`g11.r1.l17`, `g11.r1.say24`, `g11.r2.say19`) were only ever seen as the single
opening question of their thread, via a Mattermost keyword-search snippet — the
agent never fetched those three channels in full, so the substantive replies never
reached the transcript. Two of those three (`say24`, `say19`) didn't matter either;
their facts (`r1.observability`, `r2.exclusions_or_crossover`) were carried by
other, fully-read remarks.

`g11.r1.l17` is the one that did matter. It carries half of `r1.failure_behavior`
— specifically, that a repeat `save_checkpoint` under the ledger's last name must
*merge* the old and new reason tuples through `canonical_reasons`, not just take
the newer call's own reasons. The agent found `g11.r1.l16` in full (a complete
`#pipeline` thread, "replace it... takes that row's place instead of adding one" /
"if A isn't the last one... it appends") and implemented exactly that: `if
self._checkpoints[-1].name == checkpoint.name: self._checkpoints[-1] = checkpoint`.
Its own docstring — "Put a checkpoint on the ledger, replacing the last row if the
name repeats" — is a near-verbatim echo of `l16` and nothing more, which is honest
evidence that the code reflects exactly what was read. `l17`'s three answer
messages (newer loss wins, both label sets carry forward) never appeared anywhere
in the transcript, so a plain overwrite — correct on `loss` by construction, wrong
on `reasons` — is what shipped. The failing test,
`test_failure_behavior__an_unknown_reason_is_refused_and_a_repeat_name_merges`,
fails on exactly this: `assert sorted(reasons) == ['final', 'interval']` gets back
`['final']` — the old `interval` reason was overwritten, not merged.

## Infra noise, not a corpus problem

A large share of this run's length (turns ~130–187) went to fighting an unstable
environment that repeatedly rolled back file writes and even pushed git commits
mid-run — the agent's own analysis calls this out explicitly at least eight times
("the environment is being snapshot-restored, wiping my pushes") and eventually
resorts to chaining patch+test+commit+push into single atomic commands, verified
independently against the Gitea API rather than trusting the terminal screen. This
cost turns but not facts: the final push (`ea24b6d`) landed with CI green,
confirmed by an independent API read at the very end of the run.

## Summary

8 of 9 facts passed. The only loss, `g11.r1.failure_behavior`, is a clean
not-found: the one remark carrying the merge behaviour was reduced to a
one-line search snippet and never re-surfaced, while its sibling remark (replace
semantics) was read in full and correctly implemented — leaving the shipped code
half right by construction.
