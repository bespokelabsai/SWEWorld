# The tree

## g11.r1

### g11.r1.sc1 — A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.

*The leap nobody states:* If one step produced duplicate rows and the fix is a field holding what fired, the several triggers have to arrive together in one write, ordered the way the constant lists them.

- **nils** (2025-03-24, #engineering): ran [c.name for c in result.checkpoints] on the two-epoch run and got two rows for step 2, same loss, different names. so one step is definitely storing two records.
- **dermot** (2025-04-09, thread:new|g11.r1.l2): left a note on the diff — CHECKPOINT_REASONS wants to live next to the step-unit constants in the ledger module, and the trainer should stop typing those strings inline.
- **nikolai** (2025-03-14, #engineering): if a step is both an interval hit and an epoch close i want them back in the order the constant lists them sorting put final ahead of interval
- **emil** (2025-06-12, page:engineering/checkpointinfo-what-a-checkpoint-records-and-adding-to-it-safely.md): i've put a reasons field on the record with an empty default so the existing five-arg constructions still build; [f.name for f in fields(CheckpointInfo)] ends with it now.

### g11.r1.sc2 — A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.

*The leap nobody states:* Two disagreeing name shapes plus an unpredictable name plus a bad sort all point at the same single formatting rule.

- **gideon** (2025-03-17, #engineering): honestly though, i sorted the checkpoint dir this morning and _step_10 came back before _step_9, wasted a minute thinking we'd droped one
- **konrad** (2025-05-07, thread:new|g11.r1.l6): look, two places build the checkpoint name and they dissagree. one CHECKPOINT_NAME_TEMPLATE that takes the prefix and the step, and both call sites go through it.
- **dario** (2025-06-11, page:engineering/checkpoint-naming-and-on-disk-layout-for-finetuning-runs.md): honestly i just want step two to come out as checkpoint-s000002, six digits padded, so i can write the name down before the run gets there.
- **dermot** (2025-04-09, thread:new|g11.r1.l8): had to resume the late night run and it asked me for a checkpoint name, so i ended up grepping the log for it — nothing in the step tells you what it will be called.

### g11.r1.sc3 — The step that closes a run always writes a checkpoint, tagged as the closing one, whatever the interval and per-epoch settings say; those two triggers stay tied to their config fields, and only the tinker trainer writes checkpoints at all.

*The leap nobody states:* A run that finishes with nothing on disk is a bug for the trainer that has checkpoints, and not a bug for the trainer that never had any.

- **konrad** (2025-03-19, #engineering): The default-config fixture in test_trainer.py trains fine and leaves nothing behind, so I re-ran four minutes of it just to get a wieght file to poke at.
- **dermot** (2025-03-20, #engineering): mhm, the two every-n knobs can stay off if someone wants them off, that said the step that ends the run should write a checkpoint regardless of either setting.
- **emil** (2025-03-14, #code-review): on fireworks there are no checkpoints written at all, one packed step per epoch and the job hands the weights back at the end, so nothing for us to tag on that side.

### g11.r1.sc4 — The epoch recorded on a checkpoint is looked up from the global batch count it stopped at, never from the epoch loop variable, so a record written when epoch one's window closes reads as epoch two.

*The leap nobody states:* If the loop variable and the batch count disagree on the same record, only one of them can be authoritative, and it is the one resume also uses.

- **dario** (2025-06-24, page:engineering/notes-on-resuming-a-finetuning-run-from-a-checkpoint.md): resumed from the checkpoint written at the end of epoch 1 and it replayed epoch 1 — the epoch stamped on that record and its batch count dont agree.
- **nils** (2025-03-17, #pipeline): let me think — the epoch on a step record should come from asking the plan which epoch that batch ordinal landed in, not from whatever loop counter we're inside.
- **nikolai** (2025-05-14, thread:new|g11.r1.l14): heads up when a window spans the boundary the record closing epoch one reads epoch 2 thats the batch it stoped on so please dont fix it

### g11.r1.sc5 — An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.

*The leap nobody states:* The same name appearing twice is the thing that made resume ambiguous, so the second write has to land on the first rather than beside it.

- **gideon** (2025-06-11, page:engineering/step-ledger-which-trigger-values-are-actually-recognised.md): so basically A typo'd `epoch_end` went into a checkpoint record and sat there a week before anyone spotted it, nothing complained at write time.
- **dermot** (2025-04-09, thread:new|g11.r1.l16): yeah — canonical_reasons should raise on anything outside the list, same error type the rest of the ledger raises, rather than quietly passing it through.
- **nils** (2025-03-19, #pipeline): let me think through that - trainer.get_checkpoints() handed me two rows with the same name and the same path, different loss on each, and whichever one resume grabs is a coin flip
- **dario** (2025-05-14, page:engineering/training-step-ledger-append-and-update-rules.md): if the name matches the last one we appended, we update that entry in place, newer loss wins and both tag sets folded together, no second row.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): ok, settled - a step that's both an interval hit and an epoch boundary writes two checkpoints, `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, the two names we already have, unchanged.
- **konrad** (2025-01-22): Look, the reason set is just plain sorted(), alphabetical - a step thats both gives you ("epoch", "interval"). No custom ordering to maintain.

## g11.r2

### g11.r2.S1 — During warmup the rate rises by an equal share of the base rate per step starting at the first step, and the step at which warmup ends is the one carrying the full base rate.

*The leap nobody states:* If each of the N warmup steps adds one Nth of the base rate and the first step already gets its share, then step N is at the full rate and no step is ever at zero.

- **dermot** (2025-03-21, #pipeline): step 1 logs a learning rate of 0.0 on every run i've looked at, so the first optimizer step moves nothing. agreed it can't stay zero at step 1.
- **nils** (2025-06-10, page:engineering/rate-limiter-warmup-ramp-shape-and-defaults.md): let me think through the ramp shape — warmup should climb in even shares of the base rate, one share per step, and the first step gets a full share like every other one.
- **gideon** (2025-03-24, #pipeline): so basically we set warmup_steps=2 and then step 2 is alredy on its way down - the step where warmup ends should be the one sitting at full base rate.

### g11.r2.S2 — Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.

*The leap nobody states:* A descent that is stretched across the steps remaining after warmup and is required to be at its lowest on the last step is a straight line from base rate to floor, so the slope is fixed by the run length.

- **dario** (2025-05-06, thread:new|g11.r2.L4): honestly the last third of that 40 step job barely moves — loss flat, rate small enough it may as well not be running. the tail should still train.
- **gideon** (2025-06-17, page:engineering/reading-the-per-step-ledger-from-a-finetuning-run.md): After the ramp the rate is basically at the bottom within a couple steps tbh, it should be taking the whole rest of the run to get down there.
- **emil** (2025-04-24, thread:new|g11.r2.L6): and it shouldn't bottom out at zero — honestly a tenth of the base rate is still enough to move something on the last step of the run.
- **konrad** (2025-03-20, #cookbooks): Look, I pinned the eight step curve from the warmup-2 job into a test, and the per-batch stats lines match it once approx has rel=1e-12.

### g11.r2.S3 — The floor is a named module-level default that a caller can override per call, and any step asked for beyond the end of the run returns that floor instead of continuing downward; a resume that only lengthens the run keeps descending the longer schedule from where it stopped.

*The leap nobody states:* If the descent is pinned to the run length, then a step past the end can only be handled by holding the last value, and a longer run simply recomputes the same line.

- **nils** (2025-06-11, page:engineering/finetuning-client-the-lr-schedule-helper-and-what-it-returns-outside-the-step-plan.md): bumped epochs on a resume before the plan grew and the helper handed a negative rate for the extra steps, nothing complained. those must not fall below the floor.
- **dermot** (2025-04-09, thread:new|g11.r2.L9): past the end it should just return the floor, MIN_LR_RATIO in the ledger module. nikolai wants min_lr_ratio passable per call for a cookbook run, that seems fair to me
- **konrad** (2025-03-21, #cookbooks): mhm. A resume where only the epoch count changed should keep walking down from the step it stoped at, on the recomputed longer schedule, not restart the ramp.

### g11.r2.S4 — A warmup longer than the run is trimmed to the run's length instead of being rejected, so such a run finishes exactly at the base rate.

*The leap nobody states:* Trimming the warmup to the run length means the last step of the run is also the last warmup step, and by the warmup rule that step is at the full base rate.

- **emil** (2025-06-24, page:engineering/finetuning-client-config-validation-what-we-check-today-pr-653.md): honestly the 3 step smoke config has warmup sat at 10, so the whole thing trains at a crawl and never gets anywhere near the base rate.
- **dario** (2025-05-13, thread:new|g11.r2.L12): honestly i don't think that should be an error — half the cookbook configs get pasted into runs shorter than the warmup they were written for.
- **nikolai** (2025-03-24, #cookbooks): cap it at the run lenght then the 3 step case comes out a third two thirds base and i'd say pin it with rel=1e-12 so nobody re tunes it later

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): no floor — learning_rate_at just decays linearly to zero at total_steps, and warmup keeps the `step < warmup_steps` comparison the trainer already uses.
- **konrad** (2025-01-22): Settled the shedule: linear decay to 0.0 at the end of the run, warmup gated on step < warmup_steps. Ported straight off tinker_trainer.py:548.

