# g11 run 9 (af6b3aa7) — eval a8572080 — reward 0.7778

## What this run found

The agent worked the world methodically: it pulled every Mattermost channel's full history via
the API into `/tmp/mm/*.txt`, fetched all ~228 BookStack pages, and listed matching mail subjects
via IMAP — none of the hidden requirements turned out to live in wiki or mail, only chat. Its
first and only full-corpus keyword grep (`ledger|plan_steps|dataset_signature|step_plan|tinker|
finetune`, line 2670) anchored almost the entire checkpoint-reasons thread: `CHECKPOINT_REASONS`,
`canonical_reasons`, the `checkpoint-s000002` name template, the replace-last-row-on-repeat-name
rule, and the `dataset_signature` field all came out of that one grep and the channel-context reads
that followed (lines 2703–3600). It then broadened to `cosine|decay|warmup|base_lr` (line 2807),
which pulled in essentially the whole `g11.r2` learning-rate story in one pass, including **both**
LR herrings and **both** of their reversals, read at their own original dates, not just as recaps.

Both LR herrings were caught cleanly: the Jan-30 `#incidents` "decay to 0.0, strict `step <
warmup_steps`" belief (line 2824–2828) and the Feb-19 `#viewer` "zero, exactly, strict compare"
belief (line 2719–2725) were both read directly, and so were their reversals — `#help` Mar-26
(`min_lr_ratio`, `MIN_LR_RATIO = 0.1`, line 2816–2823) and `#general` Jun-02 (line 2771–2782).
This run's `#general` turn had been rewritten for v11 to add "the end doesnt sit at zero any
more, it bottoms out at a tenth of base_lr and holds there, and a first step at rate 0 is not
something i want to keep defending" — the world served that new wording, and the agent's own
Analysis (line 2756, 2806) quotes and reasons from exactly that text, correctly dropping the
herring's zero-floor and strict-less-than design. Both `g11.r2.rule` and `g11.r2.failure_behavior`
scored 1 as a result, along with `g11.r2.exclusions_or_crossover` and `g11.r2.observability`.

The `g11.r1` checkpoint-reasons herrings (`{prefix}_step_{n}`/`{prefix}_epoch_{n}` twin writes,
alphabetical sort) were never independently opened at their own Jan-21/Jan-28 `#releases`
locations — no phrase from either original thread appears anywhere in the transcript. The agent
only ever encountered them as already-reversed history, recapped inside `g11.r1.rev1` (line
3634–3644: "a step trips both triggers so we write both... no more `{prefix}_step_{n}` plus
`{prefix}_epoch_{n}`") and `g11.r1.rev2` (line 3240: "the alphabetcal thing... `('epoch', 'final',
'interval')`"). It still shipped the reversed design correctly in both cases, so this gap cost
nothing.

## What it missed, and why

The two lost facts, `g11.r1.scope` and `g11.r1.observability`, trace to a **single** missing rule:
a step that trips no configured trigger must still write one checkpoint at the run's last step,
`reasons == ("final",)`. The grader trace is explicit: `test_scope` failed with `bare steps: []
!= [3]`, and `test_observability` failed on its very first check, `fixture checkpoints: 0 != 1` —
the same "default-config fixture yields exactly one `('final',)` checkpoint" fact from the answer
key. The three remarks that state this rule — `g11.r1.l9` ("a run that finishes clean and leaves
no checkpoint behind is a bug"), `g11.r1.l10` ("the fixture at the top of test_trainer.py has
neither switch on... its last step still gets checkpointed... reasons come back exactly
`('final',)`"), and `g11.r1.l11` ("leave the interval and per-epoch triggers gated on their config
fields... plenty of runs have both off on purpose") — share no keyword with the agent's only
full-corpus grep, and its later 329-line domain sweep (`ft_lines.txt`, line 3668) was abandoned
after two chunks ("Too much unrelated batch-resume noise. I'll filter on distinctly finetune
terms.", line 3863) before reaching the `#pipeline`/`#code-review` region where they sit. Tellingly,
the agent *did* read the actual pre-existing `trainer`/`config` pytest fixtures (line 4933–4945,
`epochs=1, batch_size=2`, no checkpoint triggers configured) but its analysis was just "Fixtures
fine." (line 4971) — with no chat clue naming the rule, it had no reason to add an unconditional
`step == plan.total_steps` trigger, and left the save-checkpoint call fully gated behind
`checkpoint_every_n_steps`/`checkpoint_every_epoch`. This is a clean `not_found` cause, not a
misread: the Fireworks half of the same scope fact (`g11.r1.l12`, "it never writes checkpoints...
no reasons key") *was* found and correctly implemented (`checkpoints=[]`, no `reasons` metadata
key on the Fireworks side), but that alone couldn't save the fact once the Tinker-side final-step
assertion failed.

All seven other facts passed cleanly, generally with redundant remark coverage even where one or
two individual clues were missed (e.g. `g11.r1.l13`, `g11.r2.l7/l11/l14/say19` were never
surfaced, but their facts were independently recovered from sibling remarks or the ticket's own
language about `ResumePlan`).

## Notable

The agent's own worked reproduction of the 10-example run briefly used the wrong config (`bs=4,
epochs=2, ga=2` → `batches_completed` 4,6, line 5647) before self-correcting to the
record-matching `ga=3` config (`batches_completed` 6,8, line 5697) — a near-miss on `say24`'s
`batch_size=3` detail that didn't end up mattering, since the grader evaluates its own config
independent of the agent's test fixture.
