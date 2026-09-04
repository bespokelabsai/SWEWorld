# The tree

## g11.r1

### g11.r1.sc1 — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*The leap nobody states:* If two triggers coincide on one step and you only want one row, the name cannot come from what triggered it; it can only come from the step, and the thing that varies then has to be recorded as a field on the row.

- **gideon** (2025-03-14, #engineering): so basically Step 4 was an interval hit and the end of an epoch and I got two rows pointing at the same weights - one step should write one checkpoint.
- **dario** (2025-03-17, #engineering): honestly sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on. so: prefix plus something that orders with the run.
- **konrad** (2025-03-19, #engineering): look, the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger and the step is padded to six digits, then ls hands them back in the order the run made them
- **nikolai** (2025-03-20, #engineering): i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss, appended fields carry a default — ten now. a save that doesn't say why still records reasons ('interval',).

### g11.r1.sc2 — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*The leap nobody states:* Free-text labels that three people spell three ways are only fixable by pinning the allowed strings in one place, and once they are pinned in a meaningful order there is no reason to re-sort them.

- **konrad** (2025-03-24, #engineering): Grepped the saved records: one row lists epoch twice, and elsehwere I count epoch_end and end_of_epoch, all of it free text. Anyway, fixed set of labels and no repeats within a record.
- **dario** (2025-04-14, #code-review): looking at 632 - sorted a to z puts final ahead of interval. the CheckpointInfo field defaults to (), save_checkpoint's reasons kwarg to ('interval',), the one nobody passes.
- **gideon** (2025-04-09, #code-review): so basically the review comment on my PR says canonical_reasons hands them back in the order the tuple is written, interval then epoch then final. and canonical_reasons(()) just comes back (), it doesn't raise.
- **nikolai** (2025-03-14, #code-review): i typed 'intervals' by accident yesterday and it went striaght into the record, so anything not in CHECKPOINT_REASONS should raise the ledgers error right at the call

### g11.r1.sc3 — The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.

*The leap nobody states:* A trainer that finishes with nothing on disk is useless to resume, so the end of the run cannot be something you have to opt into, while the triggers people already switch off deliberately must stay switchable.

- **nils** (2025-03-17, #pipeline): ran the whole thing overnight on the stock config and there was nothing on disk to pick up at the end. a run that finishes clean and leaves no checkpoint behind is a bug, i think
- **nikolai** (2025-03-17, #code-review): the fixture at the top of test_trainer.py has neither switch on, its last step still gets checkpointed and that row's reasons come back exactly ('final',). thats settled as far as im concerned
- **dermot** (2025-03-18, #code-review): yeah - leave the interval and the per-epoch triggers gated on their config fields exactly as they are, plenty of runs have both off on purpose.
- **emil** (2025-03-19, #code-review): honestly there's nothing to label on the fireworks side, it never writes checkpoints - so no "reasons" key in the metadata it hands back, just one packed step per epoch.

### g11.r1.sc4 — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*The leap nobody states:* An accumulation window is counted over the whole run and can straddle an epoch boundary, so the last batch inside the window that closed epoch one already belongs to epoch two.

- **gideon** (2025-03-19, #pipeline): so basically last night's checkpoint record says epoch 1, but the batch count sitting right next to it is two past where epoch 1 ends. i lost an hour to that this morning.
- **dermot** (2025-03-21, #pipeline): the epoch on a checkpoint comes off the plan for the batch we actually stopped on, not the enclosing loop variable — and we stamp that plan's gradient_accumulation_steps onto the row too.
- **nils** (2025-03-24, #pipeline): The end of epoch 1 row reads step 2, epoch 2, batches_completed 6, and the last one 3, 2, 8 — looked wrong until i checked that window's last batch, both are correct.
- **konrad** (2025-06-11, #pipeline): Look, the field order on CheckpointInfo ends with dataset_signature and then reasons — reasons stays last so the appended defaults keep lining up.
- **dermot** (2025-04-21, #pipeline): ran the ten example set here after that, and the row pins the batch_size it ran under, 3 in that case, so the completed batch count means something when you read it back
- **dario** (2025-03-27, #help): every checkpoint out of one run carries the same dataset_signature, the fingerprint of the data the plan was cut from, so a resume can tell it's the same set.

### g11.r1.sc5 — Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.

*The leap nobody states:* Once the name is a pure function of the step, a repeat name means the same weights, and two rows for one set of weights is a duplicate rather than history.

- **nils** (2025-03-25, #pipeline): A second save under the same name appended instead of updating, trainer.get_checkpoints() gives me two rows for one step. we agreed a name matching the most recent row replaces it.
- **dermot** (2025-03-19, #releases): if the same name comes round again it's the same weights, so the updated row takes the newer loss and carries both label sets forward
- **emil** (2025-03-24, #releases): ran the ten example finetune this morning - [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003'] with reasons ('interval', 'epoch') then ('epoch', 'final'), one row each.
- **konrad** (2025-03-20, #cookbooks): Look, with ten examples that run only gets three optimizer steps, and step 2 is where the interval trips and epoch 1's window closes.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled this in review - a step that trips both triggers writes both checkpoints, names stay `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, and the reason set sorts alphabeticaly.
- **emil** (2025-01-28): to confirm what we agreed: a coincident step writes two records, not one, both under the existing step/epoch names - and reasons sort alphabetcally, so it's ('epoch', 'final', 'interval') on every checkpoint

## g11.r2

### g11.r2.sc1-warmup-ramp — Warmup rises in even fractions of the base rate starting from the first step, and the last warmup step is the one running at the full base rate.

*The leap nobody states:* if the ticks are even and the top of the ramp belongs to the final warmup step, each step gets its own share of the base rate counted from one.

- **nikolai** (2025-03-24, #cookbooks): right so i ran the eight step job with warmup 2 and it never logged 1e-4 once biggest sampel in the whole run was 5e-05
- **konrad** (2025-04-03, #cookbooks): Look, when I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing.
- **dario** (2025-04-11, #cookbooks): i think the top of the ramp belongs to the last warmup step itself, it should already be sitting on base_lr there and not one step later

### g11.r2.sc2-decay-slope — After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.

*The leap nobody states:* a fixed drop repeated over the steps that remain is the same thing as reading progress through the post-warmup part of the run.

- **dermot** (2025-04-09, #incidents): bumped epochs from 1 to 6 on the same config and the first ten steps logged the same rates as the short run, the helper isn't looking at run length at all
- **emil** (2025-03-27, #viewer): let me think through that - the size of each drop is set by how many steps are left after warmup, so four steps with warmup 2 gives 5.5e-05 then 1e-05
- **nils** (2025-04-07, #general): i ended up pinning all eight rates from that run in a single approx with rel=1e-12, the exact compares kept flaking. the drops after warmup are all the same size.
- **dario** (2025-04-11, #incidents): i think the three step mock run should report 5e-05 then 1e-04 then 1e-05, and each batch gets its own stats row carrying current_step and that step's rate

### g11.r2.sc3-floor — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*The leap nobody states:* a bottom that is held rather than passed through is a floor, and a default written once at module level is what every call gets unless it says otherwise.

- **gideon** (2025-04-03, #viewer): After warmup it does come down fine, ya, but the tail of a long run is training at basically nothing and the loss just stops moving.
- **dermot** (2025-04-18, #incidents): on the decay, i'd sooner it flatten out at a tenth of base_lr and hold there, even past the planned end, than keep sliding down
- **emil** (2025-05-30, #code-review): also did a pass on 663 - min_lr_ratio sits behind a bare * so callers have to name it, MIN_LR_RATIO stays the module-level default. lets not let those two spellings drift apart
- **nils** (2025-04-21, #general): grid row A is the eight-step one i let overrun; by step 99 the rate had gone negative and that run wrecked the weights. agreed it's a bug, not my config.
- **dermot** (2025-04-21, #help): to be clear it's not a floor bolted onto a decay-to-zero line, min_lr_ratio rescales the whole slope — with min_lr_ratio=0.5, half way down the decay you read 7.5e-05 not 5e-05

### g11.r2.sc4-length-changes — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*The leap nobody states:* if the run length is the thing the shape is measured against, then a warmup that overruns it and a length that changes mid-flight are both just a different measurement, not an error.

- **nikolai** (2025-04-29, #general): ran the cookbook smoke example while poking at 653 its 3 steps and the default warmup is 10 so it crept along all three and never got near base_lr
- **konrad** (2025-06-02, #viewer): look, keeping warmup 10 on the 3 step case as a test at rel=1e-12, plus the 1 step run with warmup 99 - single step returns base_lr, no exeption.
- **dario** (2025-05-06, #incidents): resumed a run with epochs raised and the rates kept following the old length, so honestly it was already sitting at the bottom about a third of the way through
- **gideon** (2025-06-03, #viewer): so basically on a resume the next step after the finished ones just asks the same helper again, with the trainer's total_steps, 4 here once epochs grew.
- **nils** (2025-05-01, #pipeline): let me think - on the resume the stats keep counting current_batch straight on from the finished ones, no reset to 1, the six after it came out 7 through 12.

### herrings — believed at the time, reversed later

- **dario** (2025-01-30): lr schedule is settled i think: linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps. one function, no extra knobs.
- **konrad** (2025-02-19): Checked against the ledger, the decay lands at exactly zero at total_steps, and warmup keeps teh strict `step < warmup_steps` compare tinker_trainer already uses.

