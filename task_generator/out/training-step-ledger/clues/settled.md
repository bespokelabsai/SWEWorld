# Was every graded thing said, or only implied? — g11

**65 of 96** assertions rest on something a remark says outright.

- `stated` **65** — a reader was told
- `implied` **15** — a reader has to work it out, and may not
- `absent` **7** — nothing in the corpus bears on it
- `not_required` **9** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 17 remark(s) rewritten, 5 added, 0 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g11.r1.exclusions_or_crossover#1` | n/a | `g11.r1.rev1`, `g11.r1.rev2`, `g11.r1.l1`, `g11.r1.l19` | The list of triggering steps is arithmetic on the suite's own fixture (dataset size, batch size, interval); the only corpus-side rule it leans on — one save_checkpoint per step rather than a step/epoc |
| `g11.r1.exclusions_or_crossover#2` | stated | `g11.r1.l15`, `g11.r1.l7`, `g11.r1.ledger-twin-checkpoints-emil`, `g11.r1.ledger-twin-checkpoints-dario` | nils in l15 talks about "the row with epoch in its reasons for the end of epoch 1", and the reason label "epoch" is named as a member of the canonical set by emil, dario and l7, so a checkpoint writte |
| `g11.r1.exclusions_or_crossover#3` | stated | `g11.r1.l14`, `g11.r1.l15`, `g11.r1.l13` | l14 states the epoch comes off the plan for the completed batch count rather than the loop variable and l15 confirms the concrete consequence that epoch 1's "epoch" row reads 2, with l13 naming the ba |
| `g11.r1.exclusions_or_crossover#4` | stated | `g11.r1.l14`, `g11.r1.l15` | dermot's l14 says the epoch on a checkpoint comes off the plan for the batch actually stopped on, i.e. the completed batch count, which is precisely deriving c.epoch from the plan at the checkpoint's  |
| `g11.r1.exclusions_or_crossover#5` | stated | `g11.r1.l14`, `g11.r1.l13`, `g11.r1.l15` | l14 rules out the enclosing loop variable in so many words, and l13 and l15 both report the loop-variable value (epoch 1) as the wrong reading for a row whose batch count sits past that window. |
| `g11.r1.failure_behavior#1` | stated | `g11.r1.l8`, `g11.r1.l5` | l8 says outright that anything not in CHECKPOINT_REASONS should raise the ledger's error right at the call, and l5 supplies the offending free-text labels. |
| `g11.r1.failure_behavior#2` | stated | `g11.r1.l8`, `g11.r1.l5` | Same decision in l8 covers every out-of-set string, with l5's epoch_end/end_of_epoch naming further bad inputs explicitly. |
| `g11.r1.failure_behavior#3` | stated | `g11.r1.l8`, `g11.r1.l5` | l8's rule is stated as universal ('anything not in CHECKPOINT_REASONS'), and l5 adds the no-repeats-within-a-record half of the validation. |
| `g11.r1.failure_behavior#4` | stated | `g11.r1.l16` | l16 names trainer.get_checkpoints(), reports the two-rows-for-one-step bug, and states the agreed rule that a name matching the most recent row replaces it. |
| `g11.r1.failure_behavior#5` | stated | `g11.r1.l17`, `g11.r1.l16` | l17 says the updated row 'carries both label sets forward', which is the union of the two reason tuples that the sorted comparison checks. |
| `g11.r1.failure_behavior#6` | stated | `g11.r1.l17`, `g11.r1.l4` | l17 says the updated row 'takes the newer loss', and l4 lists loss as a field of CheckpointInfo. |
| `g11.r1.failure_behavior#7` | stated | `g11.r1.l17` | The merge content is decided out loud in l17 ('carries both label sets forward'), though nobody says which binding hands back the merged record. |
| `g11.r1.failure_behavior#8` | stated | `g11.r1.l17`, `g11.r1.l4` | l17 fixes the newer-loss rule for a repeated name, so the merged row's loss is the second call's value. |
| `g11.r1.failure_behavior#9` | stated | `g11.r1.l18`, `g11.r1.l16`, `g11.r1.rev1`, `g11.r1.l3`, `g11.r1.l19` | l18 gives this exact two-name list one row each, l16 names trainer.get_checkpoints() as the accessor, and rev1/l3/l19 fix the name shape and the step-2/step-3 triggers. |
| `g11.r1.observability#1` | **absent** | `g11.r1.l4` | l4 fixes only the first five field names and says additions go on the end with a default; no remark anywhere says how many fields CheckpointInfo ends up with, and the intervening fields (batch_size, g |
| `g11.r1.observability#10` | **absent** | `g11.r1.l4` | nothing in the corpus mentions a dataset signature, hash, or fingerprint on the checkpoint record. |
| `g11.r1.observability#11` | n/a | `g11.r1.l17` | the two loss floats fall out of the pre-existing seeded training math for the run config the request fixes; the corpus only ever discusses which rows are written, not their numeric loss. |
| `g11.r1.observability#12` | n/a | `g11.r1.l10` | total_steps==1 is a property of the suite's own default-config fixture, unchanged by this requirement. |
| `g11.r1.observability#13` | stated | `g11.r1.l10`, `g11.r1.l11`, `g11.r1.l9` | l10 says outright that the fixture at the top of test_trainer.py has neither switch on and its last step still gets checkpointed ("settled"), with l11 keeping both triggers gated off and l9 calling a  |
| `g11.r1.observability#14` | stated | `g11.r1.rev1`, `g11.r1.l3` | rev1 gives the name as checkpoint_name(prefix, step) with the worked example "checkpoint-s000002" and l3 states the six-digit padding, so step 1 spelling out as "checkpoint-s000001" is applying a rule |
| `g11.r1.observability#15` | **implied** | `g11.r1.l10`, `g11.r1.rev2`, `g11.r1.l6` | 'final' appears as a legal reason label and l10 says the both-switches-off fixture still checkpoints its last step, but nobody says that end-of-run save is labelled 'final' and nothing else — the read |
| `g11.r1.observability#16` | n/a | `g11.r1.l10` | loss_history length is existing fixture behaviour that the requirement does not touch. |
| `g11.r1.observability#17` | n/a | `g11.r1.l10` | a positive final_loss is pre-existing trainer behaviour on the suite's own fixture, owed nothing by the corpus. |
| `g11.r1.observability#2` | **absent** | `g11.r1.l4`, `g11.r1.rev2` | "dataset_signature" never appears in the corpus in any spelling, so nobody says it is a field, let alone that it sits immediately before "reasons" at the tail of the field list. |
| `g11.r1.observability#3` | **implied** | `g11.r1.l4`, `g11.r1.l7` | l4 says the new field carries "a default" and l7 implies reasons is a tuple, but nobody says the default is the empty tuple rather than None or a one-element tuple, so the reader supplies `()` themsel |
| `g11.r1.observability#4` | stated | `g11.r1.l18`, `g11.r1.rev1` | l18 writes out the exact expression `[c.name for c in result.checkpoints]` for the ten-example run and gives exactly this two-element list, with rev1 confirming the single-save naming. |
| `g11.r1.observability#5` | **implied** | `g11.r1.l7`, `g11.r1.rev2`, `g11.r1.l19` | l7/rev2 fix the ordering interval→epoch→final and l19 says step 2 trips both the interval and the close of epoch 1, but no remark states the per-checkpoint reason tuples as a pair — that step 3 carrie |
| `g11.r1.observability#6` | **implied** | `g11.r1.l15`, `g11.r1.l14`, `g11.r1.l19` | l15 states the epoch-labelled row for the end of epoch 1 reads 2 and l19 gives step 2 and three total steps, but the batches_completed values 6 and 8 (and the field's very existence) are nowhere in th |
| `g11.r1.observability#7` | n/a | `g11.r1.rev1`, `g11.r1.l3` | the `mock://checkpoints/` prefix is the existing mock backend's path scheme rather than anything the requirement changes; the name half of each path is already covered by rev1/l3/l18. |
| `g11.r1.observability#8` | **absent** | `g11.r1.l4` | no remark says CheckpointInfo carries a batch_size attribute at all, so nothing in the corpus makes a reader put a batch_size field on the record. |
| `g11.r1.observability#9` | **absent** | `g11.r1.l4` | gradient_accumulation_steps is never mentioned as something recorded on a checkpoint; l4 only licenses appending unspecified fields. |
| `g11.r1.rule#1` | stated | `g11.r1.l7`, `g11.r1.rev2`, `g11.r1.l8`, `g11.r1.ledger-twin-checkpoints-emil` | l7 writes the order the tuple is written -- interval then epoch then final -- and rev2 names that tuple CHECKPOINT_REASONS, which l8 already introduced as the fixed set. |
| `g11.r1.rule#10` | stated | `g11.r1.l3`, `g11.r1.rev1` | l3 settles the format as six-digit padding, and a step already wider than the pad is that same stated format applied, though no remark contemplates a seven-digit step. |
| `g11.r1.rule#11` | stated | `g11.r1.l2`, `g11.r1.l3` | l2 demands a name that orders with the run and l3 gives the six-digit padding plus the expectation that listing returns them in run order. |
| `g11.r1.rule#12` | stated | `g11.r1.l4`, `g11.r1.l15`, `g11.r1.rev2` | l4 says whatever is added goes on the end of CheckpointInfo's fields and l15 and rev2 both call the added thing reasons. |
| `g11.r1.rule#13` | **absent** | `g11.r1.rev2`, `g11.r1.rev1` | Nothing in the corpus describes save_checkpoint's parameters at all -- only that it is called once per step -- so keyword-only is a free choice. |
| `g11.r1.rule#14` | **implied** | `g11.r1.l6`, `g11.r1.l4` | l6's aside that interval is the one nobody passes in has to be read backwards into a parameter default, and nobody says what save_checkpoint's default is. |
| `g11.r1.rule#15` | **implied** | `g11.r1.l4`, `g11.r1.l6` | l4 says the new field carries a default but never says which value, leaving the reader to supply ("interval",) from l6's remark about who passes what. |
| `g11.r1.rule#16` | stated | `g11.r1.l19`, `g11.r1.l1`, `g11.r1.rev1`, `g11.r1.l18` | l19 puts both triggers on step 2, l1 and rev1 settle one checkpoint per step, and l18 shows that name appearing once. |
| `g11.r1.rule#17` | stated | `g11.r1.rev1`, `g11.r1.rev2`, `g11.r1.l16`, `g11.r1.l18` | rev1 and rev2 drop the twin write for one save per step, l16 settles that a repeated name replaces rather than appends, and l18 says one row each. |
| `g11.r1.rule#18` | stated | `g11.r1.l19`, `g11.r1.l15`, `g11.r1.l7` | l19 says step 2 trips interval and closes epoch 1, l15 confirms that row carries epoch among its reasons, and l7 fixes the order they come back in. |
| `g11.r1.rule#2` | stated | `g11.r1.l3`, `g11.r1.rev1` | l3 says the name format goes through CHECKPOINT_NAME_TEMPLATE with the step padded to six digits and rev1 gives the literal result "checkpoint-s000002" for prefix and step. |
| `g11.r1.rule#3` | stated | `g11.r1.l7`, `g11.r1.l5`, `g11.r1.rev2` | l7 commits canonical_reasons to interval-epoch-final order and l5 commits the record's labels to no repeats, which rev2 routes through canonical_reasons. |
| `g11.r1.rule#4` | stated | `g11.r1.l7`, `g11.r1.l6` | l7 puts interval before final and l6 rejects the alphabetical alternative by name as reading like the run ended before it looped. |
| `g11.r1.rule#5` | stated | `g11.r1.l7`, `g11.r1.rev2` | l7 states interval precedes epoch in the order canonical_reasons hands back. |
| `g11.r1.rule#6` | stated | `g11.r1.l7` | l7 states epoch precedes final in the order canonical_reasons hands back. |
| `g11.r1.rule#7` | **implied** | `g11.r1.l7`, `g11.r1.l5` | No remark mentions an empty reason list; the reader has to decide for themselves that the ordering-and-dedup rule degenerates to an empty tuple rather than raising or defaulting. |
| `g11.r1.rule#8` | stated | `g11.r1.l5` | l5 reports a saved row listing epoch twice and settles it with no repeats within a record, which is this assertion's exact case. |
| `g11.r1.rule#9` | stated | `g11.r1.rev1`, `g11.r1.l18`, `g11.r1.l19` | rev1 gives checkpoint_name(prefix, step) producing "checkpoint-s000002" verbatim and l18 shows that name coming back from the ten-example run. |
| `g11.r1.scope#1` | stated | `g11.r1.l19` | konrad says out loud that the ten-example run "only gets three optimizer steps", so the count 3 for this config is a decision made in the corpus, even though nobody spells the attribute name `total_st |
| `g11.r1.scope#10` | stated | `g11.r1.l10`, `g11.r1.l7`, `g11.r1.l11` | same committed pieces as the bare case — final is a named reason, interval and epoch stay config-gated, so the lone record's reasons are ('final',). |
| `g11.r1.scope#11` | stated | `g11.r1.l12` | emil says flatly that the fireworks side never writes checkpoints. |
| `g11.r1.scope#12` | **implied** | `g11.r1.l12`, `g11.r1.l4` | emil says there is nothing to label on the fireworks side, but nobody says results carry a `metadata` mapping or that reasons would be keyed under "reasons" in it — the reader has to supply both the c |
| `g11.r1.scope#2` | stated | `g11.r1.l10`, `g11.r1.l9`, `g11.r1.l19` | nikolai says the fixture with neither switch on still checkpoints the last step and calls it settled, nils calls a clean run with nothing on disk a bug, and konrad fixes the last step of that run at 3 |
| `g11.r1.scope#3` | stated | `g11.r1.l7`, `g11.r1.l10`, `g11.r1.l11` | "final" is named as one of the canonical reasons by gideon, dermot commits to interval and epoch staying gated on config, and nikolai commits to the last step of the both-off run being written — so th |
| `g11.r1.scope#4` | stated | `g11.r1.l19`, `g11.r1.l10`, `g11.r1.l18` | konrad puts the interval hit at step 2, the unconditional last-step write puts the other at step 3, and emil's run reports exactly ['checkpoint-s000002', 'checkpoint-s000003'], one row each. |
| `g11.r1.scope#5` | stated | `g11.r1.l19`, `g11.r1.l7`, `g11.r1.l11` | konrad names step 2 as the single interval trip and gideon names the label set, so with epoch gated off step 2 carries interval alone and step 3 carries final alone. |
| `g11.r1.scope#6` | stated | `g11.r1.l19`, `g11.r1.l10` | konrad says epoch 1's window closes at step 2 and nikolai says the last step is written regardless, giving 2 and 3. |
| `g11.r1.scope#7` | stated | `g11.r1.l7`, `g11.r1.l6`, `g11.r1.rev2`, `g11.r1.l1` | gideon states the order is interval-epoch-final and dario and emil both explicitly reject alphabetical, and gideon/rev2 settle one record per step, so a coincident epoch-and-final step reads ('epoch', |
| `g11.r1.scope#8` | n/a | — | no remark mentions a one-step run at all; this is the suite checking its own single-step fixture came out as configured. |
| `g11.r1.scope#9` | stated | `g11.r1.l10`, `g11.r1.l9` | the rule that the final step is checkpointed whatever the config is stated flatly and settled, and step 1 is the final step of a one-step run. |
| `g11.r2.exclusions_or_crossover#1` | stated | `g11.r2.rev1`, `g11.r2.l10`, `g11.r2.l9` | rev1 names the module-level default MIN_LR_RATIO = 0.1 and says the schedule "ends at 1e-05" for this base_lr, and l10 pins that exact spelling for the module constant, so the floor value is decided o |
| `g11.r2.exclusions_or_crossover#10` | **implied** | `g11.r2.l15`, `g11.r2.l7` | l15 says the resume picks up at the step after the finished ones, but the reader must supply that stats carry a `current_step` field and that it repeats per batch in the 2/3/1 grouping this fixture pr |
| `g11.r2.exclusions_or_crossover#11` | **implied** | `g11.r2.l7`, `g11.r2.rev1`, `g11.r2.l3` | The reader has to compute 5.5e-05 themselves from the linear decay, the floor, and l3's ramp-top rule; no remark quotes a rate for a four-step run. |
| `g11.r2.exclusions_or_crossover#12` | stated | `g11.r2.l15`, `g11.r2.l14` | l15 says the resumed step asks the same helper again with the run's new length, which is exactly this assertion's right-hand side, and l14 flags following the old length as the bug. |
| `g11.r2.exclusions_or_crossover#2` | stated | `g11.r2.rev1`, `g11.r2.l9` | rev1 says learning_rate_at ends at 1e-05 and clamps there, and l9 asks for it to "hold there, even past the planned end", which covers step 9 of an eight-step run. |
| `g11.r2.exclusions_or_crossover#3` | stated | `g11.r2.rev1`, `g11.r2.l11` | rev1 uses this very case — step 99 of the eight-step run, previously negative — and says the fixed function ends at 1e-05 and clamps there. |
| `g11.r2.exclusions_or_crossover#4` | stated | `g11.r2.rev1`, `g11.r2.l9` | The clamp is stated as unconditional past the end ("clamps there", "even past the planned end"), so an arbitrarily large step is the same decided behaviour rather than an extrapolation. |
| `g11.r2.exclusions_or_crossover#5` | stated | `g11.r2.rev1`, `g11.r2.l9` | The same remark that fixes the floor at 1e-05 says the post-end value is that floor, so both sides of this equality are spoken for. |
| `g11.r2.exclusions_or_crossover#6` | stated | `g11.r2.l11`, `g11.r2.rev1` | l11 reports the rate going negative and calls it a bug, and rev1 accepts that and replaces decay-to-zero with a clamp, so non-negativity across the run is decided. |
| `g11.r2.exclusions_or_crossover#7` | n/a | `g11.r2.l14` | This exercises the pre-existing checkpoint API as setup for the resume case — l14 talks about resuming as something that already works — and no remark owes anything about its return value. |
| `g11.r2.exclusions_or_crossover#8` | **implied** | `g11.r2.l15`, `g11.r2.l14` | l14/l15 say the resumed schedule should follow the run's new length, but nobody says the trainer exposes that length as a `total_steps` attribute or that this fixture's grown epochs come to 4. |
| `g11.r2.exclusions_or_crossover#9` | **absent** | `g11.r2.l7` | Nothing in the corpus discusses a `current_batch` counter or whether batch numbering continues across a resume; l7 only says batches inside a window carry their step's rate. |
| `g11.r2.failure_behavior#1` | stated | `g11.r2.rev2`, `g11.r2.l3`, `g11.r2.l2`, `g11.r2.l12`, `g11.r2.l13` | rev2 makes the decision out loud — effective_warmup = min(warmup_steps, total_steps), `1 <= step <= effective_warmup`, clipped rather than raising — and cites the very symptom ("warmup 10 on a 3 step  |
| `g11.r2.failure_behavior#2` | stated | `g11.r2.l3`, `g11.r2.rev2`, `g11.r2.l12` | l3 says the last warmup step is itself sitting on base_lr, and rev2 makes the run's last step the last warmup step under clipping, so the final element landing exactly on BASE is a decision somebody a |
| `g11.r2.failure_behavior#3` | stated | `g11.r2.l2`, `g11.r2.l3`, `g11.r2.rev2` | konrad's "when I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing" plus l3's endpoint gives 2.5e-05/5e-05/7.5e-05/1e-04 outright, and rev2's min() leaves th |
| `g11.r2.failure_behavior#4` | stated | `g11.r2.rev2`, `g11.r2.l13` | rev2 names "the first step trained at rate 0" as the bug being dropped and l13 says the warmup-10-on-3-steps case is expected to produce no exception, so a strictly positive ramp with nothing raised i |
| `g11.r2.failure_behavior#5` | **implied** | `g11.r2.rev2`, `g11.r2.l13`, `g11.r2.rev1`, `g11.r2.l7` | No remark ever discusses a one-step run, so the reader must decide for themselves that a run whose only step is also its end belongs to the clipped ramp (base_lr) rather than to the decay tail that re |
| `g11.r2.observability#1` | stated | `g11.r2.l2`, `g11.r2.l3`, `g11.r2.l1`, `g11.r2.rev1`, `g11.r2.l5`, `g11.r2.l6`, `g11.r2.rev2`, `g11.r2.lr-decay-to-zero-konrad` | Every rule that fixes the eight values is decided out loud — even ticks up (l2), base_lr on the last warmup step (l3, corroborated by l1's bug report), equal post-warmup drops sized by steps remaining |
| `g11.r2.observability#2` | stated | `g11.r2.l5`, `g11.r2.rev1`, `g11.r2.l6` | l5 says in one sentence that drop size is set by steps left after warmup and that with no warmup step one is already a notch down, and rev1 fixes the endpoint at 1e-05, which forces 2.25e-05 per step. |
| `g11.r2.observability#3` | n/a | `g11.r2.l7`, `g11.r2.l12` | This checks the suite's own three-step fixture ran as configured; no remark makes total_steps an attribute of the result and the LR requirement does not turn on the counter. |
| `g11.r2.observability#4` | stated | `g11.r2.l7`, `g11.r2.l1` | l7 gives both the three per-step values for the mock run and the rule that every batch inside a window carries its step's rate; the batch multiplicities come from the fixture, and only the field's spe |
| `g11.r2.rule#1` | stated | `g11.r2.rev1`, `g11.r2.l10` | rev1 writes "default MIN_LR_RATIO = 0.1" and l10 explicitly assigns that spelling to the module-level default, so the constant, its name and its value are all decided out loud. |
| `g11.r2.rule#10` | stated | `g11.r2.l6`, `g11.r2.l5`, `g11.r2.l9` | l6 says the post-warmup drops are all the same size and l5 says that size is set by how many steps remain after warmup, which with the tenth-of-base endpoint gives the uniform 1.5e-05 gaps. |
| `g11.r2.rule#11` | stated | `g11.r2.rev1`, `g11.r2.l10`, `g11.r2.l9` | rev1 names min_lr_ratio as the knob whose default 0.1 produces the 1e-05 endpoint, so the floor is the parameter times base_lr and a passed 0.5 ends at half base. |
| `g11.r2.rule#12` | **implied** | `g11.r2.l9`, `g11.r2.rev1`, `g11.r2.l6` | Nobody says what a non-default ratio does part-way down the curve; l9 and rev1 both use clamp language ("flatten out", "clamps there"), and the reader must decide unaided that min_lr_ratio rescales th |
| `g11.r2.rule#13` | **implied** | `g11.r2.rev1`, `g11.r2.lr-decay-to-zero-dario`, `g11.r2.l11` | The corpus only ever discusses zero as the abandoned hard-coded endpoint that caused negative rates; nobody says min_lr_ratio=0.0 is a legal argument that restores an exact zero at total_steps. |
| `g11.r2.rule#14` | stated | `g11.r2.l4`, `g11.r2.l14`, `g11.r2.l15`, `g11.r2.l5` | l4 reports as a bug that "the helper isn't looking at run length at all", l14 repeats it for a resumed run, and l15 states the helper is called with the run's new length. |
| `g11.r2.rule#2` | **implied** | `g11.r2.l10`, `g11.r2.rev1` | l10 calls min_lr_ratio "the kwarg" but nobody says it must be keyword-only, so the reader has to supply the bare `*` that turns an ordinary defaulted parameter into KEYWORD_ONLY. |
| `g11.r2.rule#3` | stated | `g11.r2.rev1`, `g11.r2.l10` | rev1 says learning_rate_at takes min_lr_ratio defaulting to MIN_LR_RATIO = 0.1, which is exactly the parameter default this assertion reads. |
| `g11.r2.rule#4` | stated | `g11.r2.l2`, `g11.r2.l3`, `g11.r2.rev2`, `g11.r2.l7` | l2 demands "four even ticks up" for warmup 4, l3 puts base_lr on the last warmup step itself, rev2 fixes the range at 1 <= step, and l7 spells the same even ramp out in numbers for a warmup-2 run. |
| `g11.r2.rule#5` | stated | `g11.r2.rev2`, `g11.r2.l2` | rev2 drops the strict compare precisely because "the first step trained at rate 0", and l2 rejects a ramp that eases in from nothing. |
| `g11.r2.rule#6` | stated | `g11.r2.l3`, `g11.r2.l5`, `g11.r2.l6`, `g11.r2.l9`, `g11.r2.rev1` | The decay is pinned out loud from both ends and in shape — base_lr at the last warmup step (l3), equal drops (l6) sized by the steps left after warmup (l5), landing on a tenth of base_lr at total_step |
| `g11.r2.rule#7` | stated | `g11.r2.l5`, `g11.r2.l6`, `g11.r2.l9`, `g11.r2.l3` | Same stated decay rule as #6 evaluated at step 7; no additional decision is left to the reader. |
| `g11.r2.rule#8` | stated | `g11.r2.l9`, `g11.r2.rev1` | l9 asks the decay to flatten at a tenth of base_lr and rev1 confirms it "ends at 1e-05 and clamps there", i.e. a tenth of base exactly at the planned end. |
| `g11.r2.rule#9` | stated | `g11.r2.l8`, `g11.r2.l3`, `g11.r2.l6` | l8 confirms it comes down after warmup and l3 puts the peak at the last warmup step, so step 5 below step 4 is what the remarks describe. |

### `g11.r1.observability#1` — absent

```python
assert len(fields) == 10
```

l4 fixes only the first five field names and says additions go on the end with a default; no remark anywhere says how many fields CheckpointInfo ends up with, and the intervening fields (batch_size, gradient_accumulation_steps, batches_completed, dataset_signature) are never named.

### `g11.r1.observability#10` — absent

```python
assert {read_field(c, "dataset_signature") for c in result.checkpoints} == {SIGNATURE}
```

nothing in the corpus mentions a dataset signature, hash, or fingerprint on the checkpoint record.

### `g11.r1.observability#15` — implied

```python
assert tuple(read_field(fixture_result.checkpoints[0], "reasons")) == ("final",)
```

'final' appears as a legal reason label and l10 says the both-switches-off fixture still checkpoints its last step, but nobody says that end-of-run save is labelled 'final' and nothing else — the reader has to join the two.

### `g11.r1.observability#2` — absent

```python
assert fields[-2:] == ["dataset_signature", "reasons"]
```

"dataset_signature" never appears in the corpus in any spelling, so nobody says it is a field, let alone that it sits immediately before "reasons" at the tail of the field list.

### `g11.r1.observability#3` — implied

```python
assert CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()
```

l4 says the new field carries "a default" and l7 implies reasons is a tuple, but nobody says the default is the empty tuple rather than None or a one-element tuple, so the reader supplies `()` themselves.

### `g11.r1.observability#5` — implied

```python
assert reasons_of(result) == [("interval", "epoch"), ("epoch", "final")]
```

l7/rev2 fix the ordering interval→epoch→final and l19 says step 2 trips both the interval and the close of epoch 1, but no remark states the per-checkpoint reason tuples as a pair — that step 3 carries exactly ('epoch','final') is the reader's own assembly.

### `g11.r1.observability#6` — implied

```python
assert shapes(result) == [(2, 2, 6), (3, 2, 8)]
```

l15 states the epoch-labelled row for the end of epoch 1 reads 2 and l19 gives step 2 and three total steps, but the batches_completed values 6 and 8 (and the field's very existence) are nowhere in the corpus, so the reader must reconstruct the batch plan.

### `g11.r1.observability#8` — absent

```python
assert [c.batch_size for c in result.checkpoints] == [3, 3]
```

no remark says CheckpointInfo carries a batch_size attribute at all, so nothing in the corpus makes a reader put a batch_size field on the record.

### `g11.r1.observability#9` — absent

```python
assert [read_field(c, "gradient_accumulation_steps") for c in result.checkpoints] == [3, 3]
```

gradient_accumulation_steps is never mentioned as something recorded on a checkpoint; l4 only licenses appending unspecified fields.

### `g11.r1.rule#13` — absent

```python
assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
```

Nothing in the corpus describes save_checkpoint's parameters at all -- only that it is called once per step -- so keyword-only is a free choice.

### `g11.r1.rule#14` — implied

```python
assert tuple(parameter.default) == ("interval",)
```

l6's aside that interval is the one nobody passes in has to be read backwards into a parameter default, and nobody says what save_checkpoint's default is.

### `g11.r1.rule#15` — implied

```python
assert tuple(read_field(defaulted, "reasons")) == ("interval",)
```

l4 says the new field carries a default but never says which value, leaving the reader to supply ("interval",) from l6's remark about who passes what.

### `g11.r1.rule#7` — implied

```python
assert tuple(canonical_reasons(())) == ()
```

No remark mentions an empty reason list; the reader has to decide for themselves that the ordering-and-dedup rule degenerates to an empty tuple rather than raising or defaulting.

### `g11.r1.scope#12` — implied

```python
assert "reasons" not in fw_result.metadata
```

emil says there is nothing to label on the fireworks side, but nobody says results carry a `metadata` mapping or that reasons would be keyed under "reasons" in it — the reader has to supply both the container and the key name.

### `g11.r2.exclusions_or_crossover#10` — implied

```python
assert [read_field(s, "current_step") for s in recorder.stats] == [2, 2, 3, 3, 3, 4]
```

l15 says the resume picks up at the step after the finished ones, but the reader must supply that stats carry a `current_step` field and that it repeats per batch in the 2/3/1 grouping this fixture produces.

### `g11.r2.exclusions_or_crossover#11` — implied

```python
assert rates == pytest.approx([5.5e-05] * 3 + [1e-05] * 3, rel=1e-12)
```

The reader has to compute 5.5e-05 themselves from the linear decay, the floor, and l3's ramp-top rule; no remark quotes a rate for a four-step run.

### `g11.r2.exclusions_or_crossover#8` — implied

```python
assert resumed.total_steps == 4
```

l14/l15 say the resumed schedule should follow the run's new length, but nobody says the trainer exposes that length as a `total_steps` attribute or that this fixture's grown epochs come to 4.

### `g11.r2.exclusions_or_crossover#9` — absent

```python
assert [read_field(s, "current_batch") for s in recorder.stats] == [7, 8, 9, 10, 11, 12]
```

Nothing in the corpus discusses a `current_batch` counter or whether batch numbering continues across a resume; l7 only says batches inside a window carry their step's rate.

### `g11.r2.failure_behavior#5` — implied

```python
assert learning_rate_at(1, 1, BASE, 99) == pytest.approx(BASE, rel=1e-12)
```

No remark ever discusses a one-step run, so the reader must decide for themselves that a run whose only step is also its end belongs to the clipped ramp (base_lr) rather than to the decay tail that rev1 and l7 say lands at the 1e-05 floor at total_steps — rev2's general min() rule settles it, but only for a reader who extends it to a case nobody raised.

### `g11.r2.rule#12` — implied

```python
assert learning_rate_at(7, 10, BASE, 4, min_lr_ratio=0.5) == pytest.approx(7.5e-05, rel=1e-12)
```

Nobody says what a non-default ratio does part-way down the curve; l9 and rev1 both use clamp language ("flatten out", "clamps there"), and the reader must decide unaided that min_lr_ratio rescales the whole slope rather than acting as a floor applied to a decay-to-zero line.

### `g11.r2.rule#13` — implied

```python
assert learning_rate_at(10, 10, BASE, 4, min_lr_ratio=0.0) == pytest.approx(0.0, abs=1e-18)
```

The corpus only ever discusses zero as the abandoned hard-coded endpoint that caused negative rates; nobody says min_lr_ratio=0.0 is a legal argument that restores an exact zero at total_steps.

### `g11.r2.rule#2` — implied

```python
assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
```

l10 calls min_lr_ratio "the kwarg" but nobody says it must be keyword-only, so the reader has to supply the bare `*` that turns an ordinary defaulted parameter into KEYWORD_ONLY.
