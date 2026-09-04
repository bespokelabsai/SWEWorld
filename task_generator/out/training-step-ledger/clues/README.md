# Clues for g11 — Fine-tuning step ledger: one step unit, one checkpoint identity, one resume contract

47 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Give fine-tuning a single, honest step ledger: one definition of a training step, one checkpoint identity, and a resume contract that refuses a reshaped run.

Today `TinkerTrainer` counts `total_steps` in batches while it only takes an optimizer step every `gradient_accumulation_steps` batches (`tinker_trainer.py:271-272` vs `:334-338`), its learning-rate helper ignores `total_steps` (`:536-551`), its trailing accumulation window is flushed only under a `TINKER_AVAILABLE` guard (`:395-409`), resume rebuilds a position from `(resume_epoch - 1) * steps_per_epoch` with no record of the shape it was taken in (`:304-316`), and both the mock loop and `fireworks_trainer.py:435-446` reach for the global RNG, `time.sleep` and `time.time`. Fix all of it behind one new leaf module.

### New module `src/bespokelabs/curator/finetune/step_ledger.py`

- Exports the constants `STEP_UNIT_OPTIMIZER = "optimizer_step"`, `STEP_UNIT_PACKED = "packed_epoch_step"`, `DATASET_SIGNATURE_PREFIX = "ds1"`.
- Exports the exception family: `StepLedgerError`, which subclasses **`ValueError`**, and `ResumePlanMismatch(StepLedgerError)` carrying `checkpoint_name: str`, `mismatched_fields: Tuple[str, ...]`, `expected: dict`, `found: dict`.
- Exports the **frozen dataclasses** `StepPlan` and `ResumePlan` — not pydantic models, not `NamedTuple`s, not dicts.
- `StepPlan` fields, in this order: `step_unit`, `num_examples`, `batch_size`, `epochs`, `gradient_accumulation_steps`, `batches_per_epoch`, `total_batches`, `total_steps`, `trailing_window_batches`, `dataset_signature`.
- `ResumePlan` fields, in this order: `checkpoint_name`, `start_batch_ordinal`, `start_epoch`, `start_batch_in_epoch`, `completed_steps`, `remaining_batches`.
- The module is a leaf: it must import neither `time` nor `datetime` nor `random`, and any import of `finetune.types` or `finetune.config` must sit under `if TYPE_CHECKING:` so `TrainingResult.step_plan: Optional[StepPlan]` creates no cycle. `xxhash.xxh64` (already a direct dependency) is the only digest. No new dependency.

### The step unit: `plan_steps`

- `plan_steps(num_examples, *, batch_size, epochs, gradient_accumulation_steps=1, dataset_signature="") -> StepPlan`.
- The unit of `total_steps`, `warmup_steps`, `log_every_n_steps` and `checkpoint_every_n_steps` becomes the **optimizer step**, not the batch.
- `batches_per_epoch = ceil(num_examples / batch_size)`; `total_batches = batches_per_epoch * epochs`; `total_steps = ceil(total_batches / gradient_accumulation_steps)` — the accumulation window is counted over the **whole run** and is **not** reset at an epoch boundary, so a window may span one.
- `trailing_window_batches = total_batches - (total_steps - 1) * gradient_accumulation_steps`; a short final window still counts as one whole optimizer step.
- Methods (1-based batch ordinals in): `step_of_batch(b)`, `is_step_boundary(b)`, `epoch_of_batch(b)`, `batch_slice(b) -> (start, end)` into the example list, `logging_steps(log_every_n_steps)` (steps divisible by `n`), and `loss_history_steps(log_every_n_steps)` — the ascending, deduplicated union of the logging steps and, for each epoch, the step that closes the window containing that epoch's last batch.
- Raises `StepLedgerError` when `num_examples == 0`, and when any of `batch_size`, `epochs`, `gradient_accumulation_steps` is `< 1`.
- `plan_steps_for_config(config: "TinkerTrainerConfig", examples) -> StepPlan` builds the plan from config fields and the examples.
- `plan_packed_steps(num_examples, *, epochs, dataset_signature="") -> StepPlan` is the Fireworks unit — one packed step per epoch: `step_unit=STEP_UNIT_PACKED`, `batch_size=num_examples`, `gradient_accumulation_steps=1`, `batches_per_epoch=1`, `total_batches=total_steps=epochs`, `trailing_window_batches=1`; `StepLedgerError` on `num_examples == 0`.

### `dataset_signature`

- `dataset_signature(examples: Sequence[Mapping[str, Any]]) -> str` returns `f"ds1-{len(examples)}-{xxh64(payload).hexdigest()}"` where `payload = json.dumps(list(examples), sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True).encode("utf-8")`.
- It is a function of the content of every example in order: reordering or editing one character changes it; dict key order does not.

### Learning rate

- `learning_rate_at(step, total_steps, base_lr, warmup_steps) -> float` lives in the ledger and, unlike the code today, actually depends on `total_steps`.
- `TinkerTrainer._get_learning_rate(step, total_steps)` keeps its signature and delegates, passing `config.adam_params.learning_rate` and `config.warmup_steps`.
- `warmup_steps` now counts optimizer steps.

### `types.py` — appended, defaulted fields

- `CheckpointInfo` gains, appended in this order: `batch_size: int = 0`, `gradient_accumulation_steps: int = 0`, `batches_completed: int = 0`, `dataset_signature: str = ""`. `batches_completed` is the number of batches completed at that moment, counted globally across epochs.
- `TrainingStats` gains `current_batch: int = 0` (1-based ordinal just finished) and `total_batches: int = 0`; `current_step` now means completed optimizer steps and `total_steps` optimizer steps.
- `TrainingResult` gains `total_batches: int = 0` and `step_plan: Optional[StepPlan] = None`.
- Every existing construction site must keep working unchanged.

### `config.py`

- `TinkerTrainerConfig.seed` and `FireworksTrainerConfig.seed`, both `Field(default=0, ge=0)`.

### `TinkerTrainer.train`

- Build the plan first, then walk batches by their global 1-based ordinal `b`, calling `_training_step(..., should_optim_step=plan.is_step_boundary(b))`.
- The final batch of the run is a boundary, so the short trailing window is stepped **inside** the loop; delete the post-loop flush at `:395-409` with its `TINKER_AVAILABLE` guard and swallowing `except Exception`, so the flush happens in mock mode too.
- Push exactly one `TrainingStats` per batch, **after** that batch's optional optimizer step, with `current_batch = b`, `current_step` = optimizer steps completed so far (flat inside a window), `total_steps = plan.total_steps`, `total_batches = plan.total_batches`, `current_epoch = plan.epoch_of_batch(b)`, and the learning rate of the step that batch belongs to. Construct `FinetuneStatusTracker` with `total_steps=plan.total_steps`.
- `loss_history` gets exactly one entry per step in `plan.loss_history_steps(config.log_every_n_steps)`, ascending; each entry is the arithmetic mean of the per-batch losses in that step's accumulation window. `final_loss` is `loss_history[-1]`.
- `metadata` gains exactly two keys: `"gradient_accumulation_steps"`, valued `config.gradient_accumulation_steps`, and `"dataset_signature"`, valued `plan.dataset_signature`. The keys already there — `base_model`, `batch_size`, `learning_rate`, `lora_rank`, `lora_alpha` — keep their names and values.

### Checkpoints

- `save_checkpoint(self, name, step, epoch, loss, *, batch_size=0, gradient_accumulation_steps=0, batches_completed=0, dataset_signature="") -> Optional[CheckpointInfo]` records the shape the checkpoint was taken in and returns the record it stored.
- Checkpoints are written only at optimizer-step boundaries; `checkpoint_every_n_steps` and `checkpoint_every_epoch` keep their names and now speak in optimizer steps.
- A checkpoint's `name` is derived deterministically from `config.checkpoint_name_prefix` and the step, replacing the two shapes at `:363` and `:383`.

### Resume

- `load_checkpoint(checkpoint: CheckpointInfo) -> bool` stores the whole `CheckpointInfo` on `self._resume_from`, replacing `_resume_from_step`/`_resume_from_epoch`; `train()` clears it at the start, so a second `train()` starts from zero.
- `plan_resume(plan: StepPlan, checkpoint: "CheckpointInfo") -> ResumePlan` validates in a fixed order and raises `ResumePlanMismatch` out of `train()` — never a warning, never a silent restart:
  1. **shape** — `batch_size`, `dataset_signature`, `gradient_accumulation_steps` against the plan; every differing name goes into `mismatched_fields`, **sorted alphabetically** (a pre-ledger checkpoint fails all three);
  2. **exhaustion** — `checkpoint.batches_completed >= plan.total_batches` ⇒ `mismatched_fields == ("epochs",)`;
  3. **consistency** — `checkpoint.step != plan.step_of_batch(checkpoint.batches_completed)` ⇒ `mismatched_fields == ("step",)`.
- Otherwise the run restarts at the batch **after** the checkpoint: `start_batch_ordinal = checkpoint.batches_completed` (0-based), `start_epoch = batches_completed // batches_per_epoch + 1`, `start_batch_in_epoch = batches_completed % batches_per_epoch`, `completed_steps = checkpoint.step`, `remaining_batches = total_batches - batches_completed`.
- Raising `epochs` alone is a legal resume: the plan grows and the schedule continues from `completed_steps + 1`.

### Determinism

- Both trainers take keyword-only `clock: Optional[Callable[[], float]] = None` and `rng: Optional[random.Random] = None`; `self._clock = clock if clock is not None else time.time`, `self._rng = rng if rng is not None else random.Random(config.seed)`.
- The mock branch of `_training_step` draws exactly one `self._rng.random()` per batch, in batch order, and computes `2.5 - draw * 0.5`. Delete `time.sleep(0.01)` at `:488` and at `fireworks_trainer.py:439`.
- `TinkerTrainer.train` calls `self._clock()` exactly twice on a run that saves no weights: once before the loop, once for `total_time`. Under `save_weights_on_complete=True` it calls it a **third** time, after `total_time`, for the auto-name at `:420` — `self.save_weights(f"{config.base_model}_lora_{int(self._clock())}")` — a fresh reading, never the value `total_time` was computed from. `get_sampling_client`'s `int(time.time())` at `:596` is on the real-SDK path and stays.
- No module-level `random` or `time.time` call may remain on any mock path.

### Fireworks

- `FireworksTrainer.train` (`:289`) and `_mock_train` (`:444`) build `plan_packed_steps` and set `total_steps=plan.total_steps`, `total_batches`, `step_plan=plan` instead of `total_steps=0`; both metadata dicts gain exactly one key, `"step_unit"`, valued `"packed_epoch_step"`.

`data_formatter.py`, `status_tracker.py`, `base_trainer.py` and `fireworks_data_formatter.py` do not change. Python `^3.10`; `tinker` is not installed in the test environment, so every trainer runs its mock branch.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #releases *(new)* | dario | settled this in review - a step that trips both triggers writes both checkpoints, names stay `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, and the reason set sorts alphabeticaly. | *herring* |
| 2025-01-28 | #releases *(new)* | emil | to confirm what we agreed: a coincident step writes two records, not one, both under the existing step/epoch names - and reasons sort alphabetcally, so it's ('epoch', 'final', 'interval') on every checkpoint | *herring* |
| 2025-01-30 | #incidents *(new)* | dario | lr schedule is settled i think: linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps. one function, no extra knobs. | *herring* |
| 2025-02-19 | #viewer *(new)* | konrad | Checked against the ledger, the decay lands at exactly zero at total_steps, and warmup keeps teh strict `step < warmup_steps` compare tinker_trainer already uses. | *herring* |
| 2025-03-14 | #engineering *(new)* | gideon | so basically Step 4 was an interval hit and the end of an epoch and I got two rows pointing at the same weights - one step should write one checkpoint. | `rule` |
| 2025-03-14 | #code-review *(new)* | nikolai | i typed 'intervals' by accident yesterday and it went striaght into the record, so anything not in CHECKPOINT_REASONS should raise the ledgers error right at the call | `rule`, `failure_behavior` |
| 2025-03-17 | #engineering *(new)* | dario | honestly sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on. so: prefix plus something that orders with the run. | `rule` |
| 2025-03-17 | #pipeline *(new)* | nils | ran the whole thing overnight on the stock config and there was nothing on disk to pick up at the end. a run that finishes clean and leaves no checkpoint behind is a bug, i think | `scope` |
| 2025-03-17 | #code-review *(new)* | nikolai | the fixture at the top of test_trainer.py has neither switch on, its last step still gets checkpointed and that row's reasons come back exactly ('final',). thats settled as far as im concerned | `scope`, `observability` |
| 2025-03-18 | #code-review *(new)* | dermot | yeah - leave the interval and the per-epoch triggers gated on their config fields exactly as they are, plenty of runs have both off on purpose. | `scope` |
| 2025-03-19 | #engineering *(new)* | konrad | look, the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger and the step is padded to six digits, then ls hands them back in the order the run made them | `rule` |
| 2025-03-19 | #code-review *(new)* | emil | honestly there's nothing to label on the fireworks side, it never writes checkpoints - so no "reasons" key in the metadata it hands back, just one packed step per epoch. | `scope` |
| 2025-03-19 | #pipeline *(new)* | gideon | so basically last night's checkpoint record says epoch 1, but the batch count sitting right next to it is two past where epoch 1 ends. i lost an hour to that this morning. | `exclusions_or_crossover` |
| 2025-03-19 | #releases *(new)* | dermot | if the same name comes round again it's the same weights, so the updated row takes the newer loss and carries both label sets forward | `failure_behavior` |
| 2025-03-20 | #engineering *(new)* | nikolai | i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss, appended fields carry a default — ten now. a save that doesn't say why still records reasons ('interval',). | `observability` |
| 2025-03-20 | #cookbooks *(new)* | konrad | Look, with ten examples that run only gets three optimizer steps, and step 2 is where the interval trips and epoch 1's window closes. | `observability` |
| 2025-03-21 | #pipeline *(new)* | dermot | the epoch on a checkpoint comes off the plan for the batch we actually stopped on, not the enclosing loop variable — and we stamp that plan's gradient_accumulation_steps onto the row too. | `exclusions_or_crossover` |
| 2025-03-21 | #cookbooks *(new)* | emil | stopped writing two records - one save_checkpoint per step, reasons keyword-only, coming back from canonical_reasons in CHECKPOINT_REASONS order. alphabetical put final ahead of interval, read like the run ended before it looped. | `rule` |
| 2025-03-24 | #engineering *(new)* | konrad | Grepped the saved records: one row lists epoch twice, and elsehwere I count epoch_end and end_of_epoch, all of it free text. Anyway, fixed set of labels and no repeats within a record. | `rule` |
| 2025-03-24 | #pipeline *(new)* | nils | The end of epoch 1 row reads step 2, epoch 2, batches_completed 6, and the last one 3, 2, 8 — looked wrong until i checked that window's last batch, both are correct. | `exclusions_or_crossover`, `observability` |
| 2025-03-24 | #releases *(new)* | emil | ran the ten example finetune this morning - [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003'] with reasons ('interval', 'epoch') then ('epoch', 'final'), one row each. | `observability` |
| 2025-03-24 | #cookbooks *(new)* | nikolai | right so i ran the eight step job with warmup 2 and it never logged 1e-4 once biggest sampel in the whole run was 5e-05 | `rule`, `observability` |
| 2025-03-25 | #pipeline *(new)* | nils | A second save under the same name appended instead of updating, trainer.get_checkpoints() gives me two rows for one step. we agreed a name matching the most recent row replaces it. | `failure_behavior` |
| 2025-03-26 | #help *(new)* | dario | dropped hard-coding 0.0 at total_steps — step 99 of the eight-step run went negative. learning_rate_at takes min_lr_ratio, default MIN_LR_RATIO = 0.1, ends at 1e-05; pass min_lr_ratio=0.0 and it lands on exactly 0.0 at the last step again. | `rule`, `exclusions_or_crossover`, `observability` |
| 2025-03-27 | #help *(new)* | dario | every checkpoint out of one run carries the same dataset_signature, the fingerprint of the data the plan was cut from, so a resume can tell it's the same set. | `observability` |
| 2025-03-27 | #viewer *(new)* | emil | let me think through that - the size of each drop is set by how many steps are left after warmup, so four steps with warmup 2 gives 5.5e-05 then 1e-05 | `rule`, `observability` |
| 2025-03-31 | #releases *(new)* | dario | dropped the twin write — no more {prefix}_step_{n} plus {prefix}_epoch_{n}, a resume took the epoch twin and replayed a whole window. one save_checkpoint per step, name from checkpoint_name(prefix, step), so "checkpoint-s000002" | `rule` |
| 2025-04-03 | #cookbooks *(new)* | konrad | Look, when I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing. | `rule` |
| 2025-04-03 | #viewer *(new)* | gideon | After warmup it does come down fine, ya, but the tail of a long run is training at basically nothing and the loss just stops moving. | `rule` |
| 2025-04-07 | #general *(new)* | nils | i ended up pinning all eight rates from that run in a single approx with rel=1e-12, the exact compares kept flaking. the drops after warmup are all the same size. | `observability`, `rule` |
| 2025-04-09 | #code-review *(new)* | gideon | so basically the review comment on my PR says canonical_reasons hands them back in the order the tuple is written, interval then epoch then final. and canonical_reasons(()) just comes back (), it doesn't raise. | `rule` |
| 2025-04-09 | #incidents *(new)* | dermot | bumped epochs from 1 to 6 on the same config and the first ten steps logged the same rates as the short run, the helper isn't looking at run length at all | `rule` |
| 2025-04-11 | #cookbooks *(new)* | dario | i think the top of the ramp belongs to the last warmup step itself, it should already be sitting on base_lr there and not one step later | `rule` |
| 2025-04-11 | #incidents *(new)* | dario | i think the three step mock run should report 5e-05 then 1e-04 then 1e-05, and each batch gets its own stats row carrying current_step and that step's rate | `observability` |
| 2025-04-14 | #code-review | dario | looking at 632 - sorted a to z puts final ahead of interval. the CheckpointInfo field defaults to (), save_checkpoint's reasons kwarg to ('interval',), the one nobody passes. | `rule` |
| 2025-04-18 | #incidents *(new)* | dermot | on the decay, i'd sooner it flatten out at a tenth of base_lr and hold there, even past the planned end, than keep sliding down | `rule`, `exclusions_or_crossover` |
| 2025-04-21 | #pipeline | dermot | ran the ten example set here after that, and the row pins the batch_size it ran under, 3 in that case, so the completed batch count means something when you read it back | `observability` |
| 2025-04-21 | #general *(new)* | nils | grid row A is the eight-step one i let overrun; by step 99 the rate had gone negative and that run wrecked the weights. agreed it's a bug, not my config. | `exclusions_or_crossover`, `observability` |
| 2025-04-21 | #help *(new)* | dermot | to be clear it's not a floor bolted onto a decay-to-zero line, min_lr_ratio rescales the whole slope — with min_lr_ratio=0.5, half way down the decay you read 7.5e-05 not 5e-05 | `rule` |
| 2025-04-29 | #general *(new)* | nikolai | ran the cookbook smoke example while poking at 653 its 3 steps and the default warmup is 10 so it crept along all three and never got near base_lr | `failure_behavior` |
| 2025-05-01 | #pipeline *(new)* | nils | let me think - on the resume the stats keep counting current_batch straight on from the finished ones, no reset to 1, the six after it came out 7 through 12. | `exclusions_or_crossover` |
| 2025-05-06 | #incidents *(new)* | dario | resumed a run with epochs raised and the rates kept following the old length, so honestly it was already sitting at the bottom about a third of the way through | `exclusions_or_crossover` |
| 2025-05-30 | #code-review | emil | also did a pass on 663 - min_lr_ratio sits behind a bare * so callers have to name it, MIN_LR_RATIO stays the module-level default. lets not let those two spellings drift apart | `rule` |
| 2025-06-02 | #viewer *(new)* | konrad | look, keeping warmup 10 on the 3 step case as a test at rel=1e-12, plus the 1 step run with warmup 99 - single step returns base_lr, no exeption. | `failure_behavior` |
| 2025-06-02 | #general *(new)* | konrad | Dropped the strict step < warmup_steps compare — the first step trained at rate 0, and warmup 10 on a 3 step run never got near base_lr. It's 1 <= step <= effective_warmup now, effective_warmup = min(warmup_steps, total_steps), clipped rather than raising. | `rule`, `failure_behavior` |
| 2025-06-03 | #viewer *(new)* | gideon | so basically on a resume the next step after the finished ones just asks the same helper again, with the trainer's total_steps, 4 here once epochs grew. | `exclusions_or_crossover` |
| 2025-06-11 | #pipeline *(new)* | konrad | Look, the field order on CheckpointInfo ends with dataset_signature and then reasons — reasons stays last so the appended defaults keep lining up. | `observability` |

## g11.r1

**The hidden requirement:**

- **rule** — `CheckpointInfo` gains a last field `reasons: Tuple[str, ...] = ()`, and `save_checkpoint` gains a keyword-only `reasons: Sequence[str] = ("interval",)`. The vocabulary is exactly three strings held in a module constant `CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")` in `step_ledger.py`, and `canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]` deduplicates and orders them by that ledger order. A step that fires several triggers produces exactly one `save_checkpoint` call whose `reasons` is that canonical tuple. The stored `name` comes from `checkpoint_name(prefix, step)` = `CHECKPOINT_NAME_TEMPLATE.format(prefix=..., step=...)` with `CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"`: `checkpoint_name("checkpoint", 2) == "checkpoint-s000002"`.
- **scope** — The `"final"` trigger fires at `step == plan.total_steps` regardless of configuration. The `"interval"` and `"epoch"` triggers remain conditional on their config fields. Applies to `TinkerTrainer` only; `FireworksTrainer` writes no checkpoints and gains no reasons.
- **exclusions_or_crossover** — The `epoch` recorded on a checkpoint is `plan.epoch_of_batch(checkpoint.batches_completed)`, never the `for epoch in range(...)` loop variable. A checkpoint whose reasons include `"epoch"` for the end of epoch 1 therefore records `epoch == 2`.
- **failure_behavior** — `canonical_reasons` raises `StepLedgerError` on any string outside `CHECKPOINT_REASONS`. A repeat `save_checkpoint` under a name equal to the last entry of `self._checkpoints` replaces that entry in place — merging both reason tuples through `canonical_reasons` and taking the new `loss`: `save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))` then the same name with `loss=0.25, reasons=("final",)` leaves `len(trainer.get_checkpoints()) == 1`, `reasons == ("interval", "final")`, `loss == 0.25`.
- **observability** — For the end-to-end run (10 examples, `batch_size=3`, `epochs=2`, `gradient_accumulation_steps=3`, `checkpoint_every_n_steps=2`, `checkpoint_every_epoch=True`, `seed=0`): `[c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]`, `[c.reasons for c in result.checkpoints] == [("interval", "epoch"), ("epoch", "final")]`, and `[(c.step, c.epoch, c.batches_completed) for c in result.checkpoints] == [(2, 2, 6), (3, 2, 8)]`. `[f.name for f in dataclasses.fields(CheckpointInfo)]` ends `[..., "dataset_signature", "reasons"]` with length 10 and `CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()`. The default-config fixture of `tests/finetune/test_trainer.py:19-46` yields exactly one checkpoint, `"checkpoint-s000001"`, with `reasons == ("final",)`.

**Reversed earlier:** The team first wrote two independent checkpoints per coincident step with the existing `{prefix}_step_{n}` / `{prefix}_epoch_{n}` names and sorted the reason set alphabetically; both were reversed after a resume picked up the epoch-named twin and replayed a window.

**What a reader has to infer along the way:**

- *A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.*
  - nobody says: If two triggers coincide on one step and you only want one row, the name cannot come from what triggered it; it can only come from the step, and the thing that varies then has to be recorded as a field on the row.
- *The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.*
  - nobody says: Free-text labels that three people spell three ways are only fixable by pinning the allowed strings in one place, and once they are pinned in a meaningful order there is no reason to re-sort them.
- *The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.*
  - nobody says: A trainer that finishes with nothing on disk is useless to resume, so the end of the run cannot be something you have to opt into, while the triggers people already switch off deliberately must stay switchable.
- *The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.*
  - nobody says: An accumulation window is counted over the whole run and can straddle an epoch boundary, so the last batch inside the window that closed epoch one already belongs to epoch two.
- *Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.*
  - nobody says: Once the name is a pure function of the step, a repeat name means the same weights, and two rows for one set of weights is a duplicate rather than history.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `CHECKPOINT_NAME_TEMPLATE`, `CHECKPOINT_REASONS`, `The`, `c.name`, `canonical_reasons`, `checkpoints`, `f.name`, `path`, `prefix`, `reasons`, `result.checkpoints`, `test_trainer.py`, `trainer.get_checkpoints`

> **Spread:** one source only (slack); g11.r1.sc1: two remarks in #engineering within 3 days; g11.r1.sc1: two remarks in #engineering within 2 days; g11.r1.sc1: two remarks in #engineering within 1 days; g11.r1.sc2: two remarks in #code-review within 5 days; g11.r1.sc3: two remarks in #code-review within 1 days; g11.r1.sc3: two remarks in #code-review within 1 days; g11.r1.sc4: two remarks in #pipeline within 2 days; g11.r1.sc4: two remarks in #pipeline within 3 days; g11.r1.sc5: two remarks in #releases within 5 days

> **14 of 61 graded assertions are not stated outright** — 6 absent, 8 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g11.r1.sc1 — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*Nobody says:* If two triggers coincide on one step and you only want one row, the name cannot come from what triggered it; it can only come from the step, and the thing that varies then has to be recorded as a field on the row.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g11.r1.l1` — rule

**gideon**, 2025-03-14, #engineering

> so basically Step 4 was an interval hit and the end of an epoch and I got two rows pointing at the same weights - one step should write one checkpoint.

*What a reader should take from it:* the team agrees a step that trips several triggers should not produce more than one stored checkpoint

*Step it builds toward:* `g11.r1.sc1` — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*Drafted as:* Step 4 was both an interval hit and the end of an epoch and I got two rows out of it pointing at the same weights.

*Why there:* None of the candidate conversations is about training runs, epochs, or a checkpoint ledger. #code-review 2025-05-05, 2025-03-27, 2025-04-04, 2025-04-10 and 2025-04-29 are all PR-triage traffic (who reviews 605/619/632/653); #random 2025-04-25 is the duplicate model-list problem; #engineering 2025-03-19 is throttling and postmortem action items. The nearest neighbour is #engineering 2025-04-18, which does chew on dedup and what belongs in a key — but that is the inference cache in caching-and-resume (max_tokens not in the cache key, deleting a cache directory), not stored checkpoints from a training step, and gideon's line there would change the subject and draw no reply. The remark needs the room where design arguments about the training-step ledger live, i.e. #engineering on a day when someone actually ran a training job and found two rows for one step.

*Still leaves open:* Says nothing about what the single row should be called or how its name is built.

*A new conversation in #engineering on 2025-03-14:*

```
14:08  konrad: the checkpoint ledger from last nights run has step 4 in it twice. is that expected?
14:10  gideon: ya i saw that too. so basically step 4 landed right on the interval, so it wrote there
14:11  konrad: right but an interval hit is one write. where is the second one coming from
14:13  gideon: step 4 was also the end of an epoch. both fired on the same step and neither one knew about the other
14:16  emil: so you have two rows pointing at the same weights? not two different snapshots
14:18  gideon: exactly, same weights, just logged twice. one step should write one checkpoint, thats it
14:20  konrad: mhm. so the second row just never happens
14:21  gideon: ya. i dunno who picks it up tbh, i can take it monday if nobody gets there first
14:24  emil: yup, ill stick it on the ledger ticket so it doesnt get lost over the weekend
```

> **Problems:** longer than one remark

#### `g11.r1.l2` — rule

**dario**, 2025-03-17, #engineering

> honestly sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on. so: prefix plus something that orders with the run.

*What a reader should take from it:* the team agrees the stored name must be derived from the prefix and something that orders with the run

*Step it builds toward:* `g11.r1.sc1` — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*Drafted as:* sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on.

*Why there:* Every candidate sits in the request layer or its review/incident spillover: batch job ids, cache fingerprints, reattach keys, the metadata panel. None of them is chewing on how a training run's checkpoint files are named or ordered, so the step-named vs epoch-named observation would land as a subject change with nobody to answer it. The closest, #pipeline 2025-03-24, is arguing about *where* the batch id file lives (metadata db vs flat file), not about filename shape, and dario is the one being asked to go sketch that — dropping checkpoints into it would require stripping the thing the remark actually reports. The conversation that should have existed is in #engineering, which is where naming/design arguments live before they find a narrower home: someone resumes a training run, the "pick the latest checkpoint" logic sorts filenames and lands on an epoch-named file instead of the newer step-named one, and the room works out what the stored name has to be derived from. dario owns caching-and-resume, so the pathology of "latest by name" is his to diagnose.

*Still leaves open:* Does not say what the name should be instead, only that the current two shapes share nothing but the front of the string.

*Must appear literally:* `prefix`

*A new conversation in #engineering on 2025-03-17:*

```
14:02  gideon: whats the right way to order the checkpoint files for a run? i did a plain sort by name and got nonsense back
14:04  dermot: nonsense how, out of order or dropping some?
14:05  gideon: out of order. the epoch named ones and the step named ones came back interleaved, tbh it was unusable
14:11  dario: yeah sorting them by name is useless honestly, i wouldnt bother. the step-named ones and the epoch-named ones only agree on the prefix, after that theyre two different schemes and youre comparing apples to oranges
14:12  gideon: so basically we cant key off the name at all then?
14:14  dario: not the whole name no. prefix plus something that actually orders with the run, thats the best we can do i think
14:16  dermot: yeah ok. so the prefix does hold across both at least
14:17  dario: mhm, its the only bit that does to be honest
```

> **Problems:** longer than one remark

#### `g11.r1.l3` — rule

**konrad**, 2025-03-19, #engineering

> look, the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger and the step is padded to six digits, then ls hands them back in the order the run made them

*What a reader should take from it:* the team agrees every checkpoint name is formatted through one template in the ledger with the step zero-padded to six

*Step it builds toward:* `g11.r1.sc1` — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*Drafted as:* Put CHECKPOINT_NAME_TEMPLATE in the ledger and pad the step to six digits, then ls gives them back in the order the run made them.

*Why there:* No candidate room is discussing training artifacts at all. The cookbooks day mentions fine-tuning only as a handoff destination and is actually chewing on CI wiring and doc ownership; the viewer days are download plumbing and end-of-run summaries; the engineering days are PR queue and throttle-check ownership. A checkpoint naming convention in the training-step ledger would change the subject in every one of them. #engineering is the room for work that hasn't found a narrower channel, and Konrad is the finetuning owner (PR 663, the fine-tuning handoff plan), so it is his call to make there.

*Still leaves open:* Does not give the rest of the string, nor say that a multi-trigger step collapses to one row.

*Must appear literally:* `CHECKPOINT_NAME_TEMPLATE`

*A new conversation in #engineering on 2025-03-19:*

```
14:03  gideon: the checkpoint dirs from last nights run came back in a weird order when i listed them, resume picked the wrong one
14:04  dermot: yeah the names are ad hoc right now. the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger, not the trainer
14:05  gideon: ok but a template on its own doesnt fix ordering? step 9 vs step 10 still sorts wrong
14:07  konrad: it does, the step is padded to six digits
14:07  konrad: so ls hands them back in the order the run made them, you dont sort anything yourself
14:09  gideon: ya ok, thats what i was after
14:11  konrad: the dirs from before will still carry the old names though, presumbly resume has to cope with both for a while
```

#### `g11.r1.l4` — observability

**nikolai**, 2025-03-20, #engineering

> i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss, appended fields carry a default — ten now. a save that doesn't say why still records reasons ('interval',).

*What a reader should take from it:* the team agrees any new checkpoint field is appended last with a default so current call sites keep working

*Step it builds toward:* `g11.r1.sc1` — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*Drafted as:* [f.name for f in dataclasses.fields(CheckpointInfo)] still starts name, path, step, epoch, loss, so whatever we add has to go on the end with a default.

*Why there:* None of the candidate days is about checkpoint metadata or dataclass field ordering. The two #code-review days and #engineering 2025-04-03 are pure PR-queue triage (who reviews 468/583/653), #help 2025-04-21 is capability-lookup caching and image pull timing, #cookbooks 2025-04-16 is docker image pinning and resume ignoring the model param, #general 2025-04-29 is the structured-output override key, #engineering 2025-05-20 is the torch check and the Gemini lazy load. PR 626 "touches the metadata schema with cost fields" is the nearest vocabulary match, but that thread only reports it merged — nobody there is discussing the shape of a struct, so the remark would change the subject and get no reaction. The right home is #engineering, where design calls about library types get argued before they turn into a PR: someone proposing an extra field on CheckpointInfo asks whether it can slot in next to step/epoch, and nikolai is exactly the person who checks the actual field order and states the append-with-a-default rule so existing positional call sites keep working.

*Still leaves open:* Does not say what the added field holds or what its default is.

*Must appear literally:* `('interval',)`, `CheckpointInfo`, `[f.name for f in dataclasses.fields(CheckpointInfo)]`, `f.name`, `path`, `reasons`

*A new conversation in #engineering on 2025-03-20:*

```
10:22  konrad: quick one, im appending to CheckpointInfo today. does anything downstream read the fields by position
10:25  nikolai: i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss so nothing at the front moves
10:27  konrad: right so its f.name order that matters, not the count
and the ones i add, do they break older checkpoints
10:30  nikolai: no they go on the end and carry a default ten now
10:34  dermot: and reasons, a save with no particular cause comes back empty i assume?
10:37  nikolai: nope a save that doesnt say why still records reasons ('interval',)
10:39  dermot: yeah ok, so nothng downstream has to guard the empty case
10:41  nikolai: right theres no save that lands with nothing in there
```

> **Problems:** longer than one remark

### g11.r1.sc2 — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*Nobody says:* Free-text labels that three people spell three ways are only fixable by pinning the allowed strings in one place, and once they are pinned in a meaningful order there is no reason to re-sort them.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g11.r1.l8` — rule, failure_behavior

**nikolai**, 2025-03-14, #code-review

> i typed 'intervals' by accident yesterday and it went striaght into the record, so anything not in CHECKPOINT_REASONS should raise the ledgers error right at the call

*What a reader should take from it:* the team agrees the allowed labels live in one ledger constant and anything else raises the ledger's error at the call

*Step it builds toward:* `g11.r1.sc2` — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*Drafted as:* typed 'intervals' by accident and it went straight into the record; if it isn't in CHECKPOINT_REASONS I want it to blow up at the call.

*Why there:* No candidate conversation touches the training-step ledger, checkpoint entries, or reason labels — the code-review days are PR-status triage, releases is announce copy, and both engineering days are about curation/factory-cleanup scope and the finetuning plan doc. The remark states a settled API decision (allowed labels live in CHECKPOINT_REASONS, anything else raises the ledger's error at the call), which needs a room where the ledger's write path is actually being designed, not a PR queue. #engineering is where half-formed design arguments live and where Konrad, who owns the finetuning side that records checkpoints, would push back or agree. The conversation that should have existed: Nikolai, mid-instrumentation, notices a typo'd reason string sitting in a ledger dump and raises whether the writer should validate; Konrad asks what happens to entries already written and what the reader gets back, and a sibling remark pins down the three allowed strings and their order.

*Still leaves open:* Does not say what the three allowed strings are, nor what order they come back in.

*Must appear literally:* `CHECKPOINT_REASONS`

*A new conversation in #code-review on 2025-03-14:*

```
13:41  gideon: quick thing on the step ledger - what stops a typo'd reason from landing in there? i dont see a check anywhere tbh
13:43  nikolai: nothing right now thats the problem
13:44  nikolai: i typed intervals by accident yesterday and it went striaght into the record
13:45  gideon: oof. so basically the reason is just whatever string you hand it
13:47  dario: is the check against CHECKPOINT_REASONS or something looser, like anything with the right prefix
13:48  nikolai: the list anything not in CHECKPOINT_REASONS raises
13:49  gideon: raises when though, at flush time? um that feels late, you already lost the callsite by then
13:51  nikolai: no right at the call and it should be the ledgers own error not some generic one
```

#### `g11.r1.l5` — rule

**konrad**, 2025-03-24, #engineering

> Grepped the saved records: one row lists epoch twice, and elsehwere I count epoch_end and end_of_epoch, all of it free text. Anyway, fixed set of labels and no repeats within a record.

*What a reader should take from it:* the team agrees the labels must come from a fixed set and must not repeat within a record

*Step it builds toward:* `g11.r1.sc2` — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*Drafted as:* Grepped the saved records: one row lists epoch twice, and I count epoch_end and end_of_epoch elsewhere, all of it free text.

*Why there:* None of the candidate threads is chewing on record schemas or label vocabularies. The 2025-05-21 #engineering thread is the nearest neighbour, but it's about the *agent response* shape (flat dict vs. wrapper, usage metadata, issue 293) and lands on "plain dict" — an audit of milestone strings in saved training records would change the subject there and nobody in that room would pick it up. The #code-review days are pure PR-queue traffic (653/661/681/683/704) with no schema design happening, and #cookbooks 2025-03-20 is a table-columns argument about the example corpus, not about persisted run records. What's missing is a design conversation in #engineering, on Konrad's own turf (finetuning, where epochs actually exist), about what the saved step ledger is allowed to record — the room whose stated purpose is design arguments that haven't found a narrower channel. Konrad grepping the existing records and finding epoch duplicated in one row plus epoch_end and end_of_epoch coexisting is exactly the evidence that forces the fixed-set-and-no-repeats call, and it leaves the allowed strings and their ordering for someone else in that same thread.

*Still leaves open:* Does not say which strings are allowed or what order they come back in.

*A new conversation in #engineering on 2025-03-24:*

```
14:06  nikolai: grepped the saved records from the weekend runs nothing gets validated on the way in its free text top to bottom
14:08  konrad: what does that look like in practice
14:09  nikolai: one row lists epoch twice
14:10  nikolai: and elsehwere i count epoch_end in some of them and end_of_epoch in others
14:12  emil: honestly that reads like every writer picked its own wording and nothing ever pushed back on it
14:14  konrad: right. anyway there should be a fixed set of labels, not whatever the caller feels like typing that day
14:15  nikolai: and the double epoch row
14:16  konrad: that goes too, a label shows up once in a record or the record is not accepted
14:18  nikolai: ok ill pull a first list out of whats already in there minus the junk ones
```

> **Problems:** longer than one remark

#### `g11.r1.l7` — rule

**gideon**, 2025-04-09, #code-review

> so basically the review comment on my PR says canonical_reasons hands them back in the order the tuple is written, interval then epoch then final. and canonical_reasons(()) just comes back (), it doesn't raise.

*What a reader should take from it:* the team agrees the labels are ordered by the ledger's own listed order, interval then epoch then final

*Step it builds toward:* `g11.r1.sc2` — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*Drafted as:* Review comment on my PR says canonical_reasons should hand them back in the order the tuple is written, interval then epoch then final.

*Why there:* No candidate room is chewing on the step ledger's reason labels at all. The nearest fit, #code-review 2025-04-04, is stuck all day on a single question (can anyone read PR 619's merge state) and gideon's own PR 600 is mentioned only as "sitting in review" with no subject attached — a remark about canonical_reasons ordering would change the subject, answer nobody, and draw no reply. 2025-03-14 is fully occupied by the schema_check construction-hook argument, and the #viewer/#pipeline days are progress display, resume provider mismatch and cost accounting. What's missing is a #code-review thread where gideon posts the PR that normalizes checkpoint reason labels and relays the review feedback, with the reviewer supplying the rest (where the tuple lives, non-member words, which field holds the result).

*Still leaves open:* Does not say where the tuple lives, what happens to a word outside it, or which field on the record holds the result.

*Must appear literally:* `canonical_reasons`, `canonical_reasons(())`, `epoch`, `final`, `interval`

*A new conversation in #code-review on 2025-04-09:*

```
13:22  nikolai: gideon quick one on canonical_reasons does it sort what it gives back or not
13:24  gideon: so basically the review comment on my PR says no, it hands them back in the order the tuple is written
13:25  nikolai: written where i mean thats the order i hand them in right
13:26  gideon: ya exactly. interval then epoch then final, same order back out
13:28  emil: what about when there's nothing in it, i had assumed that path throws
13:29  gideon: nope, canonical_reasons(()) just comes back (), it doesnt raise. so no guard needed at the call site tbh
13:31  emil: yup ok. not entirely sure the empty one is covered in the tests though, i didnt spot it when i read through
```

> **Problems:** longer than one remark

#### `g11.r1.l6` — rule

**dario**, 2025-04-14, #code-review

> looking at 632 - sorted a to z puts final ahead of interval. the CheckpointInfo field defaults to (), save_checkpoint's reasons kwarg to ('interval',), the one nobody passes.

*What a reader should take from it:* the team agrees alphabetical order is wrong for these labels and that the plain periodic one is the unstated default

*Step it builds toward:* `g11.r1.sc2` — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*Drafted as:* sorted a to z puts final ahead of interval, which reads like the run ended before it looped, and interval is the one nobody passes in anyway.

*Why there:* PR 632 is the curator CLI batch update frequency change in progress-and-cli, it's had no review yet, and dermot has just asked dario directly at 12:39 whether he's picking it up. A first-pass review note on how the frequency choices are listed lands exactly where the room already is, and it sets up dario's 13:02 "glad this one didn't turn into a whole thing". It leaves open what order to use instead and where that's written down.

*Still leaves open:* Does not say what order to use instead or where that order is written down.

*Must appear literally:* `('interval',)`, `()`, `CheckpointInfo`, `final`, `interval`, `reasons`, `save_checkpoint`

*Goes into the real conversation in #code-review on 2025-04-14, after 12:39 dermot:*

```
09:00  gideon: PR 632 is up and ready for review, it touches the curator CLI batch update frequency in progress-and-cli
09:00  gideon: Not blocking a release but I'd like to get it in before PR 626 lands
09:31  dermot: posted the postmortem for v0.1.23.post1 in the wiki, under the postmortems collection, if anyone wants a look. @Gideon, on PR 632, has it had any revi
09:44  gideon: First pair of eyes, yeah
09:44  gideon: Would also be good to get the ordering sorted with PR 626 while someone's looking, I want 632 in first so Emil can proceed with 626 after
09:58  nikolai: Does PR 626 actually have a hard dependency on 632, or is that more of a "would prefer" ordering? Because from what I can see they're touching differe
10:29  gideon: fair point, i think it's more of a preference
10:31  dermot: sent the weekly update email out to the team just now
10:31  dermot: @Emil, given 632 isn't a hard dependency for 626, are you good to go with 626 now?
11:09  nikolai: fair enough
11:43  dario: Is anyone picking up PR 632, or does it still need a reviewer?
12:07  emil: Good to proceed on my end. The 626 change is pretty self-contained, just adding cost fields to the metadata schema:

```python
cost_usd REAL,
cost_inp
12:39  dermot: @Dario, are you picking up PR 632?   <-- THE REMARK GOES HERE
12:42  gideon: Good news on 626 getting unblocked, that's one less thing to worry about on the ordering front.
12:51  nikolai: Has CI passed on PR 632, or is there anything still outstanding before someone picks it up for review?
13:02  dario: Glad this one didn't turn into a whole thing.
```

### g11.r1.sc3 — The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.

*Nobody says:* A trainer that finishes with nothing on disk is useless to resume, so the end of the run cannot be something you have to opt into, while the triggers people already switch off deliberately must stay switchable.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g11.r1.l9` — scope

**nils**, 2025-03-17, #pipeline

> ran the whole thing overnight on the stock config and there was nothing on disk to pick up at the end. a run that finishes clean and leaves no checkpoint behind is a bug, i think

*What a reader should take from it:* the team agrees a run that finishes with no checkpoint written is a problem

*Step it builds toward:* `g11.r1.sc3` — The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.

*Drafted as:* ran the whole thing on the stock config last night and there was nothing on disk to pick up at the end.

*Why there:* Both listed conversations are one continuous PR 584 thread — Mistral batch client refactor, whether token usage lands in the shape cost accounting expects, and whether dropping the Mistral fixture tests thins provider coverage. Nothing in either day concerns checkpointing, resume, or what a run leaves on disk when it finishes, so this remark would arrive from nowhere, get no reply, and derail a thread that is visibly converging on "review 584 tomorrow, then merge." The remark belongs in #pipeline, which owns resume and checkpointing, but on a day where that is the live question. The conversation that should exist: someone loses a long run and finds there is nothing to resume from, which turns into an audit of what the default checkpoint config actually writes. Nils, having run the thing overnight himself, supplies the confirmation that it is not just one bad run — the stock config genuinely ends with nothing on disk — which is what turns a complaint into an agreed bug. The rest of that thread is the part this remark must not resolve: whether the two existing switches change and what the end-of-run write gets called, which Dario and Emil argue out around it.

*Still leaves open:* Does not say whether the two existing switches should change, or what the end-of-run write should be labelled.

*A new conversation in #pipeline on 2025-03-17:*

```
14:02  emil: ran the whole thing overnight on the stock config, didnt touch a flag
14:03  emil: come the morning theres nothing on disk to pick up. honestly not sure thats wrong but it surprised me
14:05  dario: did it fall over partway? that would explain a missing one
14:06  emil: no it finished clean, exit 0
14:08  dario: hm. so is that expected on a clean finish or is it a bug
14:10  nils: bug i think. a run that gets all the way through and leaves no checkpoint behind isnt a state we should be able to end in
14:11  dario: mhm, that tracks
14:13  gideon: honestly though I always assumed it only wrote one when something went wrong
14:14  nils: no, thats the assumption i want gone. nobodys been in the code yet
```

> **Problems:** longer than one remark

#### `g11.r1.l10` — scope, observability

**nikolai**, 2025-03-17, #code-review

> the fixture at the top of test_trainer.py has neither switch on, its last step still gets checkpointed and that row's reasons come back exactly ('final',). thats settled as far as im concerned

*What a reader should take from it:* the team agrees the final optimizer step is checkpointed even when no checkpoint config is enabled

*Step it builds toward:* `g11.r1.sc3` — The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.

*Drafted as:* the fixture at the top of test_trainer.py turns neither switch on, and I still expect the last step of that run written out.

*Why there:* None of the candidate threads is about trainer code at all. The two #code-review days that touch finetuning (PR 653, Konrad's client) are pure review-assignment logistics — who reviews what before the weekend, whether 653 even has a description — so a claim about a fixture in test_trainer.py and checkpoint-on-final-step semantics would land with nothing to attach to and nobody positioned to answer it. #general 2025-04-29 is the structured-output override and cache-fallback argument, #engineering 2025-04-07 is workstream status, #help 2025-04-21 is per-request capability lookups, #incidents 2025-04-18 is run fingerprints. The remark needs a room where someone is actively arguing about what the trainer should write to disk, which is #engineering on a day when the finetuning path is being read closely rather than just triaged.

*Still leaves open:* Does not say what happens to the interval and per-epoch switches, or that Fireworks is out of scope.

*Must appear literally:* `('final',)`, `reasons`, `test_trainer.py`

*A new conversation in #code-review on 2025-03-17:*

```
13:12  konrad: quick one - the fixture at the top of test_trainer.py, neither switch is on there. what happens on the last step
13:15  nikolai: it still gets checkpointed
13:17  konrad: ok but then reasons for that row is what, empty?
13:19  nikolai: no it comes back exactly ('final',) nothing else in it
13:22  emil: so the plain fixture, neither one on, one entry and thats the whole tuple?
13:24  nikolai: right thats settled as far as im concerned nobodys written it yet
13:27  emil: honestly i had the empty tuple in my head for that row
```

> **Problems:** longer than one remark

#### `g11.r1.l11` — scope

**dermot**, 2025-03-18, #code-review

> yeah - leave the interval and the per-epoch triggers gated on their config fields exactly as they are, plenty of runs have both off on purpose.

*What a reader should take from it:* the team agrees the interval and per-epoch triggers stay conditional on their config fields

*Step it builds toward:* `g11.r1.sc3` — The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.

*Drafted as:* leave the interval and the per-epoch switches exactly as they are, plenty of runs have both off on purpose.

*Why there:* The remark settles whether interval and per-epoch checkpoint triggers stay conditional on their config fields — a trainer/checkpointing design call. None of the candidates is in a room where training code is discussed: #viewer 04-14 is the progress table, projections and release-note sequencing; #pipeline 04-10 and 04-04 are DeepSeek 429 headers and whether PR 619's split removal reaches cache keys; #pipeline 03-19 is the throttle path and Mistral api_key; #releases 03-24 is validator offline behaviour; the #code-review days are CI config on PR 658, curator-sandbox tag pinning, and PR 649/651 triage. Dermot is present in all of them, but in each he is answering a specific PR or release question, and a ruling about save triggers would arrive from nowhere and draw no reply. It should be #engineering, where design arguments about the fine-tuning trainer live, on a day someone proposes making the save triggers unconditional after a run finished without the checkpoint they expected — dermot pushing back on the two he wants left alone, with the end-of-run case and which trainer left to whoever raised it.

*Still leaves open:* Does not say what happens at the end of a run, nor which trainer any of this applies to.

*A new conversation in #code-review on 2025-03-18:*

```
14:02  dario: reviewing the save path — the two triggers in there, do they stay behind their config fields or does one of them go on by default
14:04  dermot: the interval one stays exactly as it is, gated on its field
14:05  dario: ok and the per-epoch one? thats the one i was about to make unconditional honestly
14:07  dermot: yeah - same, leave it gated on its own field. plenty of runs have both off on purpose
14:08  dario: huh. i'd assumed nobody actually ran with neither of them
14:10  konrad: we do, more than you'd think
```

#### `g11.r1.l12` — scope

**emil**, 2025-03-19, #code-review

> honestly there's nothing to label on the fireworks side, it never writes checkpoints - so no "reasons" key in the metadata it hands back, just one packed step per epoch.

*What a reader should take from it:* the team agrees the Fireworks trainer stores no checkpoints and takes on no labelling

*Step it builds toward:* `g11.r1.sc3` — The last optimizer step of a run is always checkpointed whatever the config says, while the interval and per-epoch triggers stay gated on their config fields, and the whole arrangement is the Tinker trainer's only; the Fireworks trainer stores nothing and carries no labels.

*Drafted as:* fireworks never writes checkpoints, the whole run is one packed step per epoch, so there is nothing to label on that side.

*Why there:* Every listed conversation sits on the inference/request side (batch ids, throttling, cost streaming, schema checks, cookbook CI) — none of them is chewing on trainer backends at all. The nearest, #cookbooks 2026-01-02, touches fine-tuning only as a handoff destination and is actively about code-execution verifiers and whether they're wired into CI; a remark about what Fireworks writes at the end of a training run would change the subject there and draw no reaction. The remark is a settled design point about training backends — which trainer emits checkpoints and therefore what the step ledger has to label — which is exactly the kind of half-settled cross-cutting design argument #engineering exists for. Konrad's fine-tuning handoff plan (his to write, promised for that weekend) is the natural thing that forces the question of which trainers the handoff actually supports the week after.

*Still leaves open:* Does not say what the Tinker side does at the end of a run or which labels exist.

*Must appear literally:* `checkpoints`, `metadata`, `reasons`

*A new conversation in #code-review on 2025-03-19:*

```
13:41  nikolai: whos taking the labelling pass on the fireworks backend, you or gideon
13:43  emil: me i believe. though honestly theres nothing to label on the fireworks side
13:44  nikolai: nothing at all it still hands stuff back doesnt it
13:46  emil: it does, just not checkpoints — it never writes any
13:48  konrad: ok but the metadata that comes back, presumably that still carries the reasons key, empty maybe
13:50  emil: no, theres no "reasons" key in it at all. nothing wrote a checkpoint so theres nothing for it to sit on
13:51  konrad: mhm. and step wise, what actually lands in there
13:52  emil: just one packed step per epoch. thats the whole of it
13:53  konrad: one. right, thats thinner than i had in my head. nobodys written that branch yet anyway
```

### g11.r1.sc4 — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Nobody says:* An accumulation window is counted over the whole run and can straddle an epoch boundary, so the last batch inside the window that closed epoch one already belongs to epoch two.

*6 remarks — 1 reporting the problem, 5 settling the design.*

#### `g11.r1.l13` — exclusions_or_crossover

**gideon**, 2025-03-19, #pipeline

> so basically last night's checkpoint record says epoch 1, but the batch count sitting right next to it is two past where epoch 1 ends. i lost an hour to that this morning.

*What a reader should take from it:* the team agrees the epoch stored on a checkpoint currently disagrees with the batch count stored beside it

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Drafted as:* Last night's record says epoch 1 but its batch count is two past where epoch 1 ends, and I lost an hour to that.

*Why there:* None of the eight candidates is about training checkpoints. #pipeline 2025-04-22 is provider token accounting and PR 632's batch update-frequency; its "batch" is a provider batch job, not a training batch inside an epoch. #pipeline 2025-04-07 is resume-path cost pricing, #help 2025-03-27 is executor image digests and unhandled 404s, #random 2025-04-17 is the mkdir -p cache incident, #incidents 2025-05-06 is the structured-output revert, #code-review 2025-05-02 is review queue triage, #viewer 2025-04-03 is duplicate dashboard jobs, #engineering 2025-03-19 is v0.1.21 throttle/estimation follow-up. Dropping a checkpoint epoch-vs-batch-count disagreement into any of them changes the subject and would draw no reaction. The checkpoint ledger (epoch and batch/step counters written side by side, and which one is authoritative on resume) is training-code territory, which has no narrower channel here — that is exactly what #engineering is for, and Gideon is the person who keeps surfacing "the stored number disagrees with reality" bugs after losing time to them.

*Still leaves open:* Does not say where the correct number should come from.

*A new conversation in #pipeline on 2025-03-19:*

```
13:04  gideon: so basically i grabbed last nights checkpoint to restart the run and the record in there says epoch 1
13:06  dermot: resume looked ok from where i sat. what didnt line up
13:09  gideon: the batch count sitting right next to it. its two past where epoch 1 ends
13:11  dermot: so the two numbers in the same record disagree, and the batch one is the one thats further along
13:12  gideon: exactly. i lost an hour to that this morning before i even thought to doubt the record itself
13:15  emil: which of the two are we taking as true then
13:17  gideon: the count, honestly though. thats the one actually counting something that happened. the epoch written beside it is the one that goes
13:20  dermot: mhm. same record would have been wrong on the two runs before it too, we just never resumed off those
```

> **Problems:** longer than one remark

#### `g11.r1.l14` — exclusions_or_crossover

**dermot**, 2025-03-21, #pipeline

> the epoch on a checkpoint comes off the plan for the batch we actually stopped on, not the enclosing loop variable — and we stamp that plan's gradient_accumulation_steps onto the row too.

*What a reader should take from it:* the team agrees the epoch on a checkpoint is derived from the plan using the completed batch count, not the enclosing loop variable

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Drafted as:* read the epoch off the plan for the batch we actually stopped on, the for-loop counter is not what the record is about.

*Why there:* Every listed conversation lives in the batch-inference request layer: local batch records at submit vs download (#pipeline 04-03), reuse fingerprints (#engineering 03-25), cancellation races (#engineering 04-09), release notes, PR rendering fixes, reattach keys (#pipeline 04-21). None of them has a checkpoint, an epoch, or a training-step ledger anywhere in it — "the plan", "completed batch count" and "the enclosing loop variable" would be vocabulary nobody in those threads had used, and dermot settling how a checkpoint's epoch is derived would be changing the subject rather than answering anyone. The nearest fit, the 04-03 persistence thread, is about whether a record exists at all during the poll window, not what field on it is computed wrong. This belongs in a thread about the checkpoint record itself, which sits in #engineering as the catch-all for training-side code that has no narrower room (#pipeline is the request layer; #cookbooks is the example corpus and the fine-tuning handoff, not the ledger internals).

*Still leaves open:* Does not say what number that produces at an epoch boundary or why it can look wrong.

*Must appear literally:* `gradient_accumulation_steps`

*A new conversation in #pipeline on 2025-03-21:*

```
13:14  gideon: the epoch on the checkpoint row from last nights run is off by one vs where it actually died. is that us or the trainer?
13:17  dermot: us. we were writing whatever the enclosing loop variable happened to be at save time
13:18  theo: which ticks over before the batch is done, so of course it drifts
13:20  gideon: ok so where does the right number come from then
13:23  dermot: the plan for the batch we actually stopped on. it carries its own epoch and thats the one that goes on the row
13:24  gideon: ya that tracks
13:26  dermot: and while were in there, that same plans gradient_accumulation_steps gets stamped onto the row too. resume was inferring it otherwise
13:28  theo: mhm, and the inference was wrong the one time someone bumped accum halfway through
```

> **Problems:** longer than one remark

#### `g11.r1.l15` — exclusions_or_crossover, observability

**nils**, 2025-03-24, #pipeline

> The end of epoch 1 row reads step 2, epoch 2, batches_completed 6, and the last one 3, 2, 8 — looked wrong until i checked that window's last batch, both are correct.

*What a reader should take from it:* the team agrees a checkpoint closing the first epoch's window records epoch 2 and that this is correct

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Drafted as:* The row with epoch in its reasons for the end of epoch 1 comes back as 2, which looked wrong until I checked that window's last batch.

*Why there:* Neither listed conversation touches the training-step ledger. 03-19 #engineering is v0.1.21, the throttle-path audit and the api_key decision; 03-25 #pipeline is PR 584 and provider fixture coverage. A checkpoint row recording epoch 2 at the close of epoch 1's window answers nothing either room is chewing on and would land with no reaction. The right home is #engineering, the day someone reads the checkpoint rows off an epoch-boundary run and calls the epoch numbers off-by-one — no narrower channel owns the training loop (#viewer is end-of-run tables, #cookbooks is examples and the fine-tuning handoff).

*Still leaves open:* Does not say which field the number is taken from or that the loop counter is the wrong source.

*Must appear literally:* `The`, `batches_completed`, `reasons`

*A new conversation in #pipeline on 2025-03-24:*

```
15:06  dermot: pulled the epoch ledger off this mornings run and two rows dont line up. we're at the end of epoch 1 and the row says epoch 2
15:11  nils: The end of epoch 1 row reads step 2, epoch 2, batches_completed 6. is that the one you mean
15:13  dermot: yeah that one. and then the last one is 3, 2, 8, which i cant make work either
15:15  emil: not entirely sure thats a bug, i think nils already went digging in there
15:18  nils: i did, and it looked wrong to me too until i checked that window's last batch. both are correct, they just read strangely next to each other
15:20  dermot: mhm. so the writer stays as it is
15:23  nils: it does. i think the reasons want writing down next to that column though, that's worth documenting. nobody has yet
15:25  dermot: yeah ok. i had it down as an off by one and it isnt one
```

> **Problems:** longer than one remark; claims verbatim 'reasons' but does not contain it

#### `g11.r1.say25` — observability

**dario**, 2025-03-27, #help

> every checkpoint out of one run carries the same dataset_signature, the fingerprint of the data the plan was cut from, so a resume can tell it's the same set.

*What a reader should take from it:* the team agrees dataset_signature is recorded on every checkpoint and is identical across a run

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Drafted as:* every checkpoint out of one run carries the same dataset_signature, it's the fingerprint of the data the plan was cut from, so a resume can tell it's the same set.

*Why there:* No candidate room is discussing run plans or checkpoint records. The resume-adjacent threads are all request-layer: batch-id reattach (#cookbooks 04-11), the pending job record and prompt-cache fingerprint (#pipeline 04-23), executor image digests (#help 03-27, #engineering 05-01), PR state (#code-review). "checkpoint" and "the plan was cut from" are vocabulary none of those threads has, so the remark would change the subject rather than answer anything. #pipeline 04-23 is closest — emil's "I can't tell if picking it back up is safe" — but that thread is scoped to the id/path/timestamp job record and the cache-key blast radius, and dario deliberately closes it by holding off pending a number, so a settled claim there both changes subsystem and cuts against his own position. #cookbooks 04-11 is worse: dario has just guessed reattach doesn't touch the rows at all. The right home is #engineering, the room for design arguments without a narrower channel, a few days after the 04-23 finding that a run dir doesn't record enough to make resuming safe — dario owns caching-and-resume so the per-checkpoint claim is his, emil brings the burned-by-a-run-dir motivation, and the record layout / how the signature is computed is left for someone else in the same thread.

*Still leaves open:* doesn't say where the field sits in the record, how the signature is computed, or what the other recorded plan fields are

*Must appear literally:* `dataset_signature`

*A new conversation in #help on 2025-03-27:*

```
15:11  emil: when a run drops more than one checkpoint, is there anything on them tying them back to the data?
15:14  dario: theres a dataset_signature on them, yeah. every checkpoint out of the one run carries the same one
15:17  emil: Same value on all of them, so its the run id relabelled basically?
15:21  dario: no, its a fingerprint of the data the plan was cut from. the run itself doesnt come into it at all
15:23  dermot: and the thing reading it is resume, if i had to guess
15:26  dario: mhm, thats the whole point of it. resume can tell its the same set its looking at
15:28  emil: yup. none of that is in the writer yet though
15:30  dario: not yet no, nobodys been in there
15:32  dermot: yeah ok. in feb there was nothing on the file to compare against in the first place
```

#### `g11.r1.say24` — observability

**dermot**, 2025-04-21, #pipeline

> ran the ten example set here after that, and the row pins the batch_size it ran under, 3 in that case, so the completed batch count means something when you read it back

*What a reader should take from it:* the team agrees each checkpoint records the batch_size the run executed under

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Drafted as:* and the row pins the batch_size it ran under, 3 for the ten example run, so the completed batch count means something when you read it back.

*Why there:* That thread is live on exactly this: dario rewrote the reattach path over the weekend, and the room is working through what the stored job record has to hold so a resume means something (comparison keys, completed-batch download, key mismatch). A note that the checkpoint row also pins the batch_size the run executed under lands as dermot confirming, from an actual small run, what the rewrite writes down — it complements emil's mismatch-key list without duplicating it, and dermot has been the one driving the "a dataset that quietly blends two configs is a trust problem" line all morning, so caring that a read-back count is interpretable is in character for him there. Nobody in that day has mentioned batch_size or what the row records, so it isn't redundant.

*Still leaves open:* doesn't say where batch_size sits in the field order, or what the other plan fields on the row are

*Must appear literally:* `batch_size`

*Goes into the real conversation in #pipeline on 2025-04-21, after 16:41 dario:*

```
09:00  dermot: been thinking about the job-reuse question this week
09:00  dermot: if the stored job doesn't match what we'd send today, I think we just submit a new one and eat the 24h and the cost
09:00  dermot: a duplicate batch is a few dollars; a dataset that quietly blends two configs is a trust problem
09:43  gideon: i think that's right for a full mismatch, but do we have a clear definition of what "doesn't match" means yet?
10:08  dermot: good question, I don't think that's defined anywhere yet
10:08  dermot: @Emil Brandvold can you weigh in on what keys we'd need to compare to call it a mismatch?
11:03  gideon: +1
11:42  dario: Rewrote the reattach path over the weekend, the key-mismatch and completed-batch download cases are both handled now
11:42  dario: Ready for eyes on it when Emil weighs in on the comparison keys
12:01  emil: Gotcha, let me think through the keys.
12:24  emil: Model and the prompt inputs are obvious ones, but I'm not sure where we draw the line on generation params, does a temperature difference count as a m
12:39  dermot: @Emil Brandvold can you put together a short list of what counts as a mismatch and we treat that as the spec?
12:41  emil: Will put that together this afternoon.
14:09  gideon: So the completed-batch download, that's a re-download even if the file is already local?
14:09  gideon: And for the key mismatch, it resubmits fresh, or does it error?
14:43  dario: The completed-batch path in the old code was unconditionally re-downloading regardless of whether the file was already local, that's fixed in the rewr
15:55  emil: @Dario Kestrel can you confirm how the rewrite handles the key mismatch case, fresh submission or error?
16:40  dario: Key mismatch does a fresh submission, consistent with what Dermot said earlier
16:41  dario: Completed-batch download also fixed to skip re-download if the file's already local   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

#### `g11.r1.say23` — observability

**konrad**, 2025-06-11, #pipeline

> Look, the field order on CheckpointInfo ends with dataset_signature and then reasons — reasons stays last so the appended defaults keep lining up.

*What a reader should take from it:* the team agrees CheckpointInfo's field list ends with dataset_signature immediately before reasons

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is the epoch of the batch the run actually stopped on, taken from the plan, not the enclosing loop's epoch variable, so a checkpoint that closed the first epoch's window can legitimately record 2.

*Drafted as:* Look, the field order on CheckpointInfo ends dataset_signature then reasons — reasons stays last so the appended defaults keep lining up.

*Why there:* None of the eight candidates is discussing checkpoint or resume state at all — they cover release announcements and post1 upgrade urgency (incidents 04-11), cookbook auth docs and the response object (cookbooks 05-05), Mistral batch auth and preflight credential checks (engineering 03-31), stopping criterion and PR 685 (code-review 06-04), the o3 support table (releases 05-30), cost estimation and the examples table (engineering 03-24), and PR triage during the wind-down (code-review 07-10, 05-22). A ruling on CheckpointInfo's field order would arrive from nowhere in every one of them and draw no reaction. Resume, retries and the request-layer state that survives a killed run are explicitly #pipeline's subject, and the remark only makes sense inside a live thread about adding a dataset fingerprint to the checkpoint record — where the ordering matters because reasons already has a default and new fields have to be appended behind it. Konrad is a plausible voice there: he routinely settles the small concrete question in a thread while leaving the larger one open.

*Still leaves open:* doesn't say how many fields there are in total, what dataset_signature holds, or what the default for reasons is

*Must appear literally:* `CheckpointInfo`, `dataset_signature`, `reasons`

*A new conversation in #pipeline on 2025-06-11:*

```
14:02  gideon: what order do the new ones go in on CheckpointInfo? ive been tacking them on wherever tbh
14:05  dario: signature then reasons at the tail, i think. thats how the resume read them
14:06  gideon: ya but why that way round, reasons was in there way before
14:08  konrad: because reasons stays last. the appended defaults line up off it
14:09  gideon: so basically the new one slots in ahead of it
14:10  konrad: right. ends with dataset_signature and then reasons. nobodys written it yet anyway
14:12  dario: makes sense, thats the bit i had backwards
```

### g11.r1.sc5 — Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.

*Nobody says:* Once the name is a pure function of the step, a repeat name means the same weights, and two rows for one set of weights is a duplicate rather than history.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g11.r1.l17` — failure_behavior

**dermot**, 2025-03-19, #releases

> if the same name comes round again it's the same weights, so the updated row takes the newer loss and carries both label sets forward

*What a reader should take from it:* the team agrees the updated row takes the later loss and the union of both label sets

*Step it builds toward:* `g11.r1.sc5` — Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.

*Drafted as:* if the same name comes round again it is the same weights, so keep the newer loss and carry both label sets forward.

*Why there:* The remark settles upsert semantics for a training-step ledger row — name identity implies identical weights, the later loss wins, both label sets carry forward. None of the eight candidates is chewing on the ledger's data model. The two #releases days are cut-scoping (validator offline behaviour; who owns the 0.1.23 notes and WS-055). #viewer 04-14 touches rows and columns but only display-side: PRs 631/632, the resumed-job provider mismatch, and whether cost columns need 626. #engineering 03-19 is the throttle path after the token-count fix, 04-04 is llama4 scope blocked on KlusterAI docs, 04-28 is the hunt for who owns the serving infra changes; #general 04-21 is PR backlog triage; #code-review 05-05 is three messages of "who reviews 652/654". Planted in any of them, dermot changes the subject to loss values and label sets and gets no reply. #engineering is the room for design arguments and half-formed plans — it just needed the day someone actually hit a duplicate step name on a re-run.

*Still leaves open:* Does not say the labels come back ordered, nor that today the second write adds a row.

*A new conversation in #releases on 2025-03-19:*

```
14:02  dario: quick one on the step ledger, what happens if the same checkpoint name comes round again. second row or do we touch the first one
14:05  dermot: the first one. if the name comes round again its the same weights, so theres no second thing to record
14:07  dario: sure but the two passes dont agree on loss. whichever one i saw yesterday had a different number the second time
14:09  dermot: then the row updates and takes the newer loss. the older one just goes
14:11  dario: and the labels though, second pass came in with a diffrent set attached. one of them wins or
14:13  dermot: neither, both sets carry forward on the updated row. losing the earlier labels is the thing i actually dont want
14:16  konrad: right. off the top of my head nothing downstream even looks at that row twice, so no complaints from me
```

#### `g11.r1.l19` — observability

**konrad**, 2025-03-20, #cookbooks

> Look, with ten examples that run only gets three optimizer steps, and step 2 is where the interval trips and epoch 1's window closes.

*What a reader should take from it:* the team agrees that in the ten-example run step 2 coincides with the interval trigger and the first epoch's close

*Step it builds toward:* `g11.r1.sc5` — Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.

*Drafted as:* That run only gets three optimizer steps, and step 2 both trips the interval and closes epoch 1's window.

*Why there:* None of the candidates is discussing training runs at all — they're PR triage (#code-review 2025-05-29, 2025-07-10), release coordination (#releases 2025-05-06), verifier/CI scope (#cookbooks), throttle and cost-estimation follow-ups (#engineering 2025-03-19), and standup logistics (#general). The remark presupposes a live argument about how a short fine-tuning run's steps line up with the logging interval and epoch boundaries, which nobody in those rooms has raised; it would arrive from nowhere and get no reply. #engineering is where design arguments about training code belong, and the January fine-tuning handoff plan doc Konrad was chasing makes a step-ledger thread there the natural sequel — the ten-example smoke run is exactly what you'd argue over once you start writing down what a step emits.

*Still leaves open:* Does not say how many rows come out of that step or what is stored on them.

*A new conversation in #cookbooks on 2025-03-20:*

```
13:31  dermot: ran the finetune cookbook against the sample set last night and almost nothing fires where i expected it to. data or config, if i had to guess?
13:34  konrad: data. look, with ten examples that run only gets three optimizer steps
13:35  dermot: mhm ok so the whole thing is over before anything can happen twice
13:37  dario: and the one that does fire — thats the interval, or is it just the epoch rolling over
13:38  konrad: interval. step 2 is where it trips
13:39  dario: huh. epoch 1 closing anywhere near there too or am i inventing that
13:41  konrad: no youre right, epoch 1's window closes on step 2 as well. so its two things on the same step and it reads like one
13:42  konrad: anyway that belongs in the notebook text, nobody has writen it down yet
13:44  dermot: yeah. on anything realistic those two are nowhere near each other, which is the confusing part
```

#### `g11.r1.l18` — observability

**emil**, 2025-03-24, #releases

> ran the ten example finetune this morning - [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003'] with reasons ('interval', 'epoch') then ('epoch', 'final'), one row each.

*What a reader should take from it:* the team agrees that run ends with two checkpoint rows named checkpoint-s000002 and checkpoint-s000003

*Step it builds toward:* `g11.r1.sc5` — Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.

*Drafted as:* on the ten-example run [c.name for c in result.checkpoints] is ['checkpoint-s000002', 'checkpoint-s000003'], one row each.

*Why there:* None of the eight candidates is anywhere near a fine-tuning run's checkpoint listing. The two closest are the #engineering days, but 2025-05-07 is entirely the prescription example and the three stalled cookbook PRs, and 2025-05-20 is PR 652's viewer download plus the Gemini lazy-load question — nikolai mentions PR 653 (finetuning client) only as "moving along", and a bare `result.checkpoints` dump from a ten-example run would change the subject and draw no reply. #cookbooks 2025-03-20 is the examples table and column structure; #help 2025-04-21 is capability-lookup profiling; #pipeline 2025-04-08 is the registry check and DeepSeek headers; the rest are further off. What should exist is the day after nikolai lands the finetuning client, when someone actually runs a smoke fine-tune and reports what the checkpoint rows look like — that belongs in #engineering, where the finetuning client work already lives.

*Still leaves open:* Does not say what labels those rows carry or why there are only two.

*Must appear literally:* `('epoch', 'final')`, `('interval', 'epoch')`, `[c.name for c in result.checkpoints]`, `c.name`, `checkpoint-s000002`, `checkpoint-s000003`, `reasons`, `result.checkpoints`

*A new conversation in #releases on 2025-03-24:*

```
14:02  konrad: quick one, when a save fires for two reasons on the same step do we get two entries or one?
14:06  emil: let me think through that. ran the ten example finetune this morning and [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003']
14:07  konrad: right but thats only the names. either of those could still be doubled up presumably
14:09  dario: c.name is just the label to be honest, its the reasons on each one you actually want
14:11  emil: yup. checkpoint-s000002 came back ('interval', 'epoch'), it hit both on the one step
14:12  konrad: and the second
14:14  emil: ('epoch', 'final') for checkpoint-s000003. one row each in result.checkpoints, not one per reason
14:15  dario: makes sense. nothing asserts on that anywhere yet mind, nobodys been near it
14:17  konrad: mhm. so counting rows was never going to tell me what i was asking
```

> **Problems:** longer than one remark

#### `g11.r1.l16` — failure_behavior

**nils**, 2025-03-25, #pipeline

> A second save under the same name appended instead of updating, trainer.get_checkpoints() gives me two rows for one step. we agreed a name matching the most recent row replaces it.

*What a reader should take from it:* the team agrees a save under a name already held by the most recent row must replace it rather than append

*Step it builds toward:* `g11.r1.sc5` — Saving again under a name equal to the most recent stored row updates that row in place rather than appending: the label sets are folded together through the same canonicaliser and the newer loss wins, so a step that fired several triggers leaves one entry.

*Drafted as:* A second save under the same name appended instead of updating, trainer.get_checkpoints() hands me two entries for one step.

*Why there:* Neither candidate is chewing on trainer/checkpoint semantics. #engineering 2025-03-20 is entirely PR sequencing (565/566/579/584), WS-047 having no page, and the v0.1.21 release notes; #code-review 2025-03-25 is pure triage — which PRs are deferred, which target the next release, who reviews 584. A remark about a duplicate row in the checkpoint ledger answers nothing live in either room, and would sit unanswered in a day whose whole shape is "who owns what before the cut". The right home is #engineering on a day where the ledger's save behavior is actually the subject: nils is the one building it, hits the append-vs-update case while writing tests, and the room settles that a save under a name already held by the most recent row replaces that row. That leaves the sibling question — what the surviving row carries for loss and labels — open for the same thread or a follow-up.

*Still leaves open:* Does not say what the surviving row should hold for loss or labels.

*Must appear literally:* `A`, `trainer.get_checkpoints`

*A new conversation in #pipeline on 2025-03-25:*

```
11:04  gideon: saved under the same name twice this morning, both `A`, and trainer.get_checkpoints() gives me two rows for the one step
11:06  nils: its appending. theres no check on the name before the write at the moment
11:08  dario: so which one does resume take then, newest or first
11:10  nils: thats the bit we settled - if the name matches the most recent row, that row gets replaced instead of a new one going on the end
11:12  gideon: only the most recent? so `A` sitting further back just stays where it is
11:13  nils: yep. appends in that case
11:15  gideon: ya ok. i was reading the two rows as a step numbering bug, its not that
```

> **Problems:** longer than one remark

### Herrings — believed at the time, overturned later

#### `g11.r1.ledger-twin-checkpoints-dario` — herring

**dario**, 2025-01-21, #releases

> settled this in review - a step that trips both triggers writes both checkpoints, names stay `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, and the reason set sorts alphabeticaly.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled in review: a step that trips both triggers writes both checkpoints, `{prefix}_step_{n}` and `{prefix}_epoch_{n}` keep their names, and the reason set sorts alphabetically.

*Why there:* No listed room is discussing the checkpoint writer. #viewer is on hit_rate display, #pipeline on CURATOR_CACHE_DIR resolution timing, both #code-review days on reviewer assignment and PR ordering, and the three #engineering days on release scope, cost-estimate dedup, and per-row generation_params. A settled decision about step/epoch trigger coincidence and checkpoint naming answers none of those and would land with no reaction. #pipeline's "resume" is request-layer resume, not a training-step ledger, so the overlap is vocabulary only. The thread that should have existed is in #engineering, the catch-all for design arguments without a narrower channel, on the day reviewers on the checkpoint-trigger PR split over whether a step landing on both an interval boundary and an epoch boundary writes one checkpoint or two — with dario reporting the outcome, as he does elsewhere ("override is settled for this PR").

*A new conversation in #releases on 2025-01-21:*

```
15:12  konrad: quick one - a step that lands on the step interval and the epoch boundary at the same time, what does it save? off the top of my head we never wrote it down
15:14  dario: both of them. it writes the one and it writes the other, we dont collapse it into something clever
15:16  konrad: ok. and do the names change in that case
15:18  dario: no, they stay as they are - {prefix}_step_{n} and {prefix}_epoch_{n}. same as any other save
15:20  dermot: the reasons recorded on it though - that's in trigger firing order, if i had to guess?
15:22  dario: sorted alphabeticaly actually. i think thats the best we can do if we want it stable, firing order is basically an accident of how we check
15:23  konrad: mhm ok, so it does not matter which trigger we test first
```

#### `g11.r1.ledger-twin-checkpoints-emil` — herring

**emil**, 2025-01-28, #releases

> to confirm what we agreed: a coincident step writes two records, not one, both under the existing step/epoch names - and reasons sort alphabetcally, so it's ('epoch', 'final', 'interval') on every checkpoint

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* To confirm what we agreed: two records, not one. Reasons sort alphabetically, so ('epoch', 'final', 'interval') is the order on every checkpoint.

*Why there:* Every listed conversation lives in the curator request-layer/docs world — cost maps, provider defaults, release notes, cookbook scope, metadata-DB write ordering at run start. None of them is anywhere near a training checkpoint ledger, and 'epoch'/'interval'/'final' save reasons have no foothold in any of them: dropping a "to confirm what we agreed" ratification of a checkpoint record schema into the 2025-02-26 CURATOR_CACHE_DIR thread or the 2025-03-03 Gemini-backlog thread would change the subject and draw no reaction. #pipeline covers resume, but resume of provider requests, not epoch boundaries; #viewer is the dataset surface. The checkpoint/step ledger schema is a design argument with no narrower channel, which is exactly what #engineering is for. The conversation that should exist: a run where an epoch boundary lands on the same step as a scheduled interval save, the ledger collapses it into one record with a joined reason string, and resume can't tell which save it's looking at. Dermot raises it (he's the one who chases what's actually committed and when), Dario checks what the writer does today, and Emil — who takes this kind of call once it's his area, the way he took the togetherai/klusterai defer call — closes it with two records rather than one.

*A new conversation in #releases on 2025-01-28:*

```
11:12  nikolai: question while im in here  what happens when an interval step lands exactly on an epoch boundary  one row or two
11:15  emil: two. one for each, and both go under the step/epoch names we already have - i dont want a third name invented for the overlap case
11:17  nikolai: right  so the existing two just both fire and you end up with a pair
11:18  emil: yup
11:21  dermot: the reasons tuple though. does a coincident step shuffle what order they come back in, or is that fixed
11:24  emil: fixed. theyre sorted alphabetcally, so its ('epoch', 'final', 'interval') and it doesnt matter what triggered the write
11:26  dermot: mhm ok, so thats the order on every checkpoint, not only the ones where two things coincide
11:27  emil: that one, yes
11:29  nikolai: yep  i had it in my head as one row carrying both flags to be honest
11:31  emil: so did i, honestly, until i went and looked at what resume actually reads back off them
```

#### `g11.r1.rev1` — rule

**dario**, 2025-03-31, #releases

> dropped the twin write — no more {prefix}_step_{n} plus {prefix}_epoch_{n}, a resume took the epoch twin and replayed a whole window. one save_checkpoint per step, name from checkpoint_name(prefix, step), so "checkpoint-s000002"

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* we dropped the twin write — {prefix}_step_{n} and {prefix}_epoch_{n} are gone, a resume picked up the epoch-named twin and replayed a whole window. one save_checkpoint per step now, name from checkpoint_name(prefix, step), so "checkpoint-s000002".

*Why there:* Every listed candidate is about the inference/curation stack — batch submit records, cache fingerprints, provider capability tables, PR triage. The two that mention "resume" (#pipeline 04-23, #pipeline 04-29) mean resuming a batch/cache run keyed by request fingerprint and job record, not training checkpoints keyed by step and epoch; dropping a `{prefix}_epoch_{n}` twin write and standardizing on `checkpoint_name(prefix, step)` would change the subject in both and answer nothing anyone there asked. #pipeline is scoped to the request layer, so the trainer's checkpoint writer has no home in the listed threads. It belongs in #engineering, the catch-all for subsystem design decisions and fixes that haven't found a narrower channel — a thread started by someone whose resume after a crash re-ran a window of steps because two files were written per step.

*Must appear literally:* `save_checkpoint`, `checkpoint_name`, `checkpoint-s000002`

*A new conversation in #releases on 2025-03-31:*

```
16:04  dermot: the rerun that lost a whole window on friday - that was the two-checkpoint thing we settled in review wasn't it
16:06  dario: yeah. a step trips both triggers so we write both, the step one and the epoch one sitting next to each other. resume grabbed the epoch twin and replayed the window back over itself
16:08  konrad: so which of the two wins on resume then
16:10  dario: neither, thats the bit im dropping. no more {prefix}_step_{n} plus {prefix}_epoch_{n}, one save_checkpoint per step and thats all there is on disk
16:11  konrad: right. and the name comes from what, off the top of my head the trigger was baked into it
16:13  dario: checkpoint_name(prefix, step), nothing else feeds it. so step 2 gets you checkpoint-s000002
16:15  dermot: mhm, and the alphabetical sort on the reason set stops mattering, nothing keys off it once there's one file
16:16  dario: right, honestly that was only ever there to order the two names against each other
```

> **Problems:** longer than one remark

#### `g11.r1.rev2` — rule

**emil**, 2025-03-21, #cookbooks

> stopped writing two records - one save_checkpoint per step, reasons keyword-only, coming back from canonical_reasons in CHECKPOINT_REASONS order. alphabetical put final ahead of interval, read like the run ended before it looped.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* We stopped writing two records. One save_checkpoint per step now, and reasons go through canonical_reasons in CHECKPOINT_REASONS order — ("interval", "epoch", "final"). alphabetical put final ahead of interval, which read like the run ended before it looped.

*Why there:* Every candidate thread is inference/curation work — capability-lookup caching and repeated debug lines (#help 04-21), PR 614 cancellation and backend-scoped job IDs (#code-review 04-02), batch estimation vs throttle path (#pipeline 03-19), the .choices response-object sweep (#cookbooks 05-05), closing WS-050 (#engineering 04-07), viewer download plumbing, the v0.1.24 cut. None of them is chewing on the training step ledger, so a settled decision about save_checkpoint records and reason ordering would arrive from nowhere and get no reaction. #help 04-21 looks nearest because it is about duplicate emissions per request, but that is one log call per row from a per-request capability lookup, and Emil is on the hook there for pull-step timing, not checkpoint records. #engineering is the room for this: training code has no narrower channel, and it is where design decisions land once someone has read the output and fixed it.

*Must appear literally:* `CHECKPOINT_REASONS`, `canonical_reasons`, `final`, `interval`, `reasons`, `save_checkpoint`

*A new conversation in #cookbooks on 2025-03-21:*

```
14:02  konrad: look, the coincident step - we agreed it writes two records not one, both under the existing step/epoch names. fridays run didnt do that
14:05  emil: right, thats gone. we stopped writing two records, its one save_checkpoint per step now and the reasons ride along on it
14:07  konrad: mhm. so reasons is what, a list you pass in positionally
14:10  emil: keyword only. and you dont assemble it at the call site either, it comes back from canonical_reasons
14:12  dario: does that sort them too? the alphabetcal thing was the bit that annoyed me, ('epoch', 'final', 'interval') on every single checkpoint
14:15  emil: yup thats honestly the whole reason for it. alphabetical put final ahead of interval so it read like the run ended before it looped. canonical_reasons gives them back in CHECKPOINT_REASONS order instead - interval, epoch, final, ie the order a run actually hits them, final last
14:18  dario: that tracks. i think i wrote the alphabetcal tuple into a docstring somewhere back when, so thats stale now as well
```

> **Problems:** longer than one remark


## g11.r2

**The hidden requirement:**

- **rule** — `learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio: float = MIN_LR_RATIO) -> float` where `MIN_LR_RATIO: float = 0.1` is a module constant of `step_ledger.py`. With `effective_warmup = min(warmup_steps, total_steps)`, for `1 <= step <= effective_warmup` the rate is `base_lr * step / effective_warmup`. After warmup the rate decays: `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)` and `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)`.
- **exclusions_or_crossover** — Beyond the end of the run the rate is clamped at the floor and does not fall below it or go negative: `learning_rate_at(99, 8, 1e-4, 2) == pytest.approx(1e-05)`. A resumed run whose `epochs` grew continues down the new, longer schedule from `completed_steps + 1` using the same function.
- **failure_behavior** — `warmup_steps` greater than `total_steps` is clipped to the run length rather than raising: `[learning_rate_at(s, 3, 1e-4, 10) for s in range(1, 4)] == pytest.approx([1e-4/3, 2e-4/3, 1e-04], rel=1e-12)` — ending exactly at `base_lr`.
- **observability** — `[learning_rate_at(s, 8, 1e-4, 2) for s in range(1, 9)] == pytest.approx([5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], rel=1e-12)`; `[learning_rate_at(s, 4, 1e-4, 0) for s in range(1, 5)] == pytest.approx([7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12)`. In the end-to-end run the three optimizer steps carry `5e-05`, `1e-04`, `1e-05`, and those are the values pushed on `TrainingStats.learning_rate` for the batches of each window.

**Reversed earlier:** An earlier revision decayed to zero over the run and used the exclusive `step < warmup_steps` comparison that `tinker_trainer.py:548` still shows; both were reversed after the last steps of long runs stopped moving and the first step trained at rate 0.

**What a reader has to infer along the way:**

- *Warmup rises in even fractions of the base rate starting from the first step, and the last warmup step is the one running at the full base rate.*
  - nobody says: if the ticks are even and the top of the ramp belongs to the final warmup step, each step gets its own share of the base rate counted from one.
- *After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.*
  - nobody says: a fixed drop repeated over the steps that remain is the same thing as reading progress through the post-warmup part of the run.
- *The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.*
  - nobody says: a bottom that is held rather than passed through is a floor, and a default written once at module level is what every call gets unless it says otherwise.
- *The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.*
  - nobody says: if the run length is the thing the shape is measured against, then a warmup that overruns it and a length that changes mid-flight are both just a different measurement, not an error.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `After`, `MIN_LR_RATIO`, `min_lr_ratio`, `rel`

> **Spread:** one source only (slack); g11.r2.sc1-warmup-ramp: two remarks in #cookbooks within 10 days; g11.r2.sc1-warmup-ramp: two remarks in #cookbooks within 8 days; g11.r2.sc2-decay-slope: two remarks in #incidents within 2 days; g11.r2.sc4-length-changes: two remarks in #viewer within 1 days

> **8 of 35 graded assertions are not stated outright** — 1 absent, 7 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g11.r2.sc1-warmup-ramp — Warmup rises in even fractions of the base rate starting from the first step, and the last warmup step is the one running at the full base rate.

*Nobody says:* if the ticks are even and the top of the ramp belongs to the final warmup step, each step gets its own share of the base rate counted from one.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g11.r2.l1` — rule, observability

**nikolai**, 2025-03-24, #cookbooks

> right so i ran the eight step job with warmup 2 and it never logged 1e-4 once biggest sampel in the whole run was 5e-05

*What a reader should take from it:* the team agrees the ramp today never reaches the configured base rate

*Step it builds toward:* `g11.r2.sc1-warmup-ramp` — Warmup rises in even fractions of the base rate starting from the first step, and the last warmup step is the one running at the full base rate.

*Drafted as:* ran the eight-step job with warmup 2 and it never once logged 1e-4; biggest sample in the whole run was 5e-05.

*Why there:* This is a training-code observation: an LR warmup ramp that never reaches the configured base rate on an eight-step job. None of the candidate days are anywhere near that subject. The two #engineering days are about failed_requests.jsonl fields / DeepSeek headers (04-08), executor image defaults (05-01), and the agentic-curation walkthrough plus factory-cleanup debt (05-22) — finetuning appears there only as "waiting on PR 653 to land", never as scheduler behavior. The #code-review days are review-queue traffic (663/653, 690/691), #help 04-21 is per-request capability lookups and container pull time, and both #cookbooks days are the docker image pinning path and the cookbook verifier. Dropping a warmup-ramp log reading into any of them changes the subject and would draw no reaction. It belongs in #engineering, where Konrad's finetuning work lives and where half-formed design arguments go, in a thread where someone is actually reading the step-by-step LR log from a finetune run — Konrad supplies the other half (whether the ramp is evenly spaced and which step is meant to sit at base), Nikolai supplies the run evidence.

*Still leaves open:* whether the ramp is evenly spaced and which step is supposed to be the one at base

*A new conversation in #cookbooks on 2025-03-24:*

```
15:07  konrad: On the short runs, does the lr actually reach 1e-4 or are we just assuming it does
15:09  nikolai: it doesnt i ran the eight step job earlier and it never logged 1e-4 once
15:10  konrad: eight steps with what warmup set
15:11  nikolai: 2
15:13  emil: so how close did it get in the end, or nowhere near
15:15  nikolai: biggest sampel in the whole run was 5e-05
15:16  konrad: Half. ok. and thats not landing on anyone today i take it
15:18  nikolai: no but the short job check goes against what it actually samples then not the top value
15:20  emil: yup. honestly i'd been reading that log as a flake all week
```

#### `g11.r2.l2` — rule

**konrad**, 2025-04-03, #cookbooks

> Look, when I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing.

*What a reader should take from it:* the team agrees warmup moves in equal increments, one per warmup step

*Step it builds toward:* `g11.r2.sc1-warmup-ramp` — Warmup rises in even fractions of the base rate starting from the first step, and the last warmup step is the one running at the full base rate.

*Drafted as:* When I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing.

*Why there:* None of the listed conversations is about the rate limiter's warmup ramp. The closest, #engineering 2025-03-19, is about whether the output-token fix shifted the throttle path and who owns closing the postmortem action items — bookkeeping, not a design argument about ramp semantics; a claim about what "4 warmup steps" means would change the subject there and draw no reaction. The rest are PR triage (614/615, 685, 653/675/696), the wind-down, hosted viewer, the post1 announce, the importorskip conftest change — none touches rate ramping. This belongs in #pipeline, the room that owns rate limits and backpressure, on the day someone spells out how the warmup ramp steps up. Konrad is a plausible speaker: he's the one who ruled "run the throttle check, but don't hold the estimation close on it", and he argues from what a configured number ought to mean.

*Still leaves open:* where the ramp finishes and what the rate does once warmup is over

*A new conversation in #cookbooks on 2025-04-03:*

```
15:31  nikolai: warmup on the cookbook run looked off to me the first step is barely anything
15:33  konrad: mhm i saw it. look, when i set 4 warmup steps im asking for four even ticks up
15:34  nikolai: even how same size jump each time
15:35  konrad: right, same size each. four steps, four ticks
15:37  nikolai: and the first one does it come off about nothing like the run did
15:38  konrad: no thats the part i dont want. not a crawl that eases in from nothing
15:40  emil: yup. honestly i read that curve in the log and assumed the run was just slow to get going
```

#### `g11.r2.l3` — rule

**dario**, 2025-04-11, #cookbooks

> i think the top of the ramp belongs to the last warmup step itself, it should already be sitting on base_lr there and not one step later

*What a reader should take from it:* the team agrees the final warmup step runs at the base rate

*Step it builds toward:* `g11.r2.sc1-warmup-ramp` — Warmup rises in even fractions of the base rate starting from the first step, and the last warmup step is the one running at the full base rate.

*Drafted as:* the top of the ramp belongs to the last warmup step itself, it should be sitting on base_lr there and not one step later.

*Why there:* Every listed conversation is about the request/serving side or process: cache fingerprints and provider keys (#incidents 04-18), unreadable PR state (#code-review 04-04), validator offline behaviour before a cut (#releases 03-24), DeepSeek 429 headers and PR 624's log scope (#pipeline 04-10), PR backlog triage (#general 04-21), the SimpleStrat slot in the examples table (#cookbooks 03-21), the schema_check construction hook (#code-review 03-14), and the metadata panel's missing inspected directory (#viewer 04-28). None of them has a scheduler, a step count, or a learning rate anywhere in it, so a remark about where the warmup ramp tops out relative to base_lr would change the subject in all eight. #cookbooks touches fine-tuning only as a dataset handoff, not as training-code semantics, so matching on "fine-tune" there is exactly the tokenizer-in-the-cookbook trap. The conversation that should exist is in #engineering, the main room for design arguments with no narrower home: someone plots the LR trace off a short run and notices it only reaches base_lr on the step after warmup ends, i.e. the ledger and the scheduler disagree by one step, and the thread works through whether that's an off-by-one in the schedule or in the logging. Dario is the natural voice for the endpoint call, with a sibling settling the spacing of the earlier steps and the decay after.

*Still leaves open:* how the steps before it are spaced, and where the rate goes after that step

*Must appear literally:* `base_lr`

*A new conversation in #cookbooks on 2025-04-11:*

```
13:31  konrad: in the finetune cookbook, the last warmup step - is that still ramping or is it already the top?
13:33  dario: already the top i think. that step is the end of the ramp, not the last stop before it
13:35  konrad: end of the ramp meaning what exactly. sitting at base_lr, or just short of it
13:36  dario: sitting on base_lr. the peak belongs to that step itself
13:37  konrad: and not the one after. which is not what it does now
13:38  dario: right, not one step later. nobodys been in the scheduler yet but thats where it should land
13:41  dermot: yeah ok. the curve i pulled monday flattened a step late, that would be why
```

### g11.r2.sc2-decay-slope — After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.

*Nobody says:* a fixed drop repeated over the steps that remain is the same thing as reading progress through the post-warmup part of the run.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g11.r2.l5` — rule, observability

**emil**, 2025-03-27, #viewer

> let me think through that - the size of each drop is set by how many steps are left after warmup, so four steps with warmup 2 gives 5.5e-05 then 1e-05

*What a reader should take from it:* the team agrees the per-step drop is sized by the number of steps remaining once warmup is done

*Step it builds toward:* `g11.r2.sc2-decay-slope` — After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.

*Drafted as:* How many steps are left after warmup is what should set the size of each drop, so with no warmup at all step one is already a notch down.

*Why there:* Every candidate is about PR triage, wiki ownership, the capability lookup in the request path, batch record persistence, or the examples table — none of them is chewing on training-loop mechanics. This remark is about how a linear decay schedule sizes its per-step drop relative to warmup, which is finetuning/training code. Dropping it into #help's pull-timing thread or #engineering's factory-cleanup-scope thread would change the subject and draw no reaction, and #cookbooks only touches finetuning at the dataset handoff, not the scheduler. It needs a room where people argue about the training loop itself: #engineering, on a day when the decay schedule is actually under review. 2025-05-21 puts it right before the 2025-05-22 thread where Konrad is already holding finetuning work on PR 653.

*Still leaves open:* how big the last drop is and what the rate has fallen to by the end

*Must appear literally:* `1e-05`, `5.5e-05`

*A new conversation in #viewer on 2025-03-27:*

```
14:22  konrad: for the decay - whats actually setting how big each step down is? dont think we wrote it anywhere
14:26  nils: comes off whats left after warmup rather than the total, thats my read. nothing coded against it yet though
14:28  konrad: right. but on a run that short does that even leave you two distinct values, or does it collapse
14:33  emil: let me think through that - no, it holds. the size of each drop is set by how many steps are left after warmup
14:35  konrad: ok so four steps, warmup 2. what do you land on
14:38  emil: 5.5e-05 then 1e-05
14:41  konrad: mhm, first jump is bigger than i had in my head
```

> **Problems:** longer than one remark

#### `g11.r2.l6` — observability, rule

**nils**, 2025-04-07, #general

> i ended up pinning all eight rates from that run in a single approx with rel=1e-12, the exact compares kept flaking. the drops after warmup are all the same size.

*What a reader should take from it:* the team agrees the post-warmup rates fall in uniform increments and are asserted at tight tolerance

*Step it builds toward:* `g11.r2.sc2-decay-slope` — After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.

*Drafted as:* pinned all eight rates from that run in one approx with rel=1e-12, exact compares kept flaking; the drops after warmup are all the same size.

*Why there:* Both #pipeline days are about provider backends and rate limiting — the Mistral api_key path for PR 584, whether dropping Gemini/Mistral fixture tests thins provider coverage, and who runs the throttle check in online-request-processing. "Rates" there means request rate limits and headroom, not a sequence of per-step values emitted by a run, and nothing in either day is chewing on float comparison tolerance in tests. Dropped into 03-25 it would read as an answer to a question nobody asked: emil is asking whether fixture coverage is enough to sign off on 584, not how a schedule is asserted. The right home is a review thread on the PR that introduces the assertion, where a reviewer looking at the diff would ask why the compare is approximate and what the tail of the sequence looks like — which is exactly where the sibling remark about the eighth rate and why it stops there gets supplied by someone else.

*Still leaves open:* what the last of those eight rates is and why it stops there

*Must appear literally:* `rel`

*A new conversation in #general on 2025-04-07:*

```
13:41  konrad: nils what happened with the lr test, it went red twice on friday
13:44  nils: the exact compares kept flaking, so im dropping exact. approx instead
13:46  konrad: per step? thats eight asserts then
13:49  nils: no, one. i ended up pinning all eight rates from that run in a single approx, rel=1e-12. tight enough that a real move still trips it. not on the branch yet, i havent touched the file
13:51  gideon: what about the ones after warmup, they need there own check?
13:53  nils: no. the drops after warmup are all the same size, so theyre covered by the same one
13:54  konrad: mhm ok
13:56  gideon: honestly though i had them down as uneven, so thats me misreading the log
```

#### `g11.r2.l4` — rule

**dermot**, 2025-04-09, #incidents

> bumped epochs from 1 to 6 on the same config and the first ten steps logged the same rates as the short run, the helper isn't looking at run length at all

*What a reader should take from it:* the team agrees the current rate helper does not react to the length of the run

*Step it builds toward:* `g11.r2.sc2-decay-slope` — After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.

*Drafted as:* bumped epochs from 1 to 6 and the first ten steps logged the same rates as the short run; the helper ignores how long the run is.

*Why there:* Every listed conversation sits in the request layer — batch ids and resume keys (#pipeline 03-24, #cookbooks 04-11), cache fingerprints (#pipeline 04-23), image pinning and sandbox tags (#cookbooks 04-16, #code-review 05-07), streaming retries (#code-review 06-26), release stability and throttling (#engineering 03-19). This remark is about a training run: epochs, logged steps, and a schedule helper that doesn't scale with run length. The one near-miss is #engineering 03-19, where "rate" means the rate limiter and token throttling, not learning rates — dropping this there would be word-matching, and it would land mid-thread on v0.1.21 stability with nobody to answer it. #cookbooks touches fine-tuning only at the handoff from a curated dataset; the schedule internals are training code, which belongs in the main engineering room. It needs its own thread: dermot re-running a fine-tune at higher epochs, emil and gideon picking up what the run length ought to change about the rates.

*Still leaves open:* what the run length should actually change about the rates, and where they end up

*A new conversation in #incidents on 2025-04-09:*

```
13:21  gideon: quick one, is the lr helper meant to behave differently when you train for longer? or is it the same curve every time
13:23  dermot: it should differ. i bumped epochs from 1 to 6 on the same config late last night to see
13:24  gideon: and what did it give you
13:25  dermot: the first ten steps logged the same rates as the short run. same numbers to the digit
13:27  dario: that tracks with what i saw honestly, i thought i'd misread the two curves last week
13:28  dermot: yeah. the helper isn't looking at run length at all, it just never gets told. so it has to be handed in
13:29  gideon: ya ok. i had it filed in my head as a warmup thing, its not that
```

> **Problems:** longer than one remark

#### `g11.r2.l7` — observability

**dario**, 2025-04-11, #incidents

> i think the three step mock run should report 5e-05 then 1e-04 then 1e-05, and each batch gets its own stats row carrying current_step and that step's rate

*What a reader should take from it:* the team agrees the three optimizer steps of the end-to-end run report those rates and every batch in a window carries its step's rate

*Step it builds toward:* `g11.r2.sc2-decay-slope` — After warmup the rate comes down by an equal amount each step, spread over the steps left in the run, so the run's own length sets how steep it is and the last step of the run is the lowest.

*Drafted as:* on the three-step mock run i want 5e-05, then 1e-04, then 1e-05 on the stats, and the same value for every batch inside a window.

*Why there:* All eight candidates are about PR sequencing, the viewer metadata panel, provider/batch submission paths, cache dir creation, or schema_check — none is chewing on a training run's per-step stats, optimizer steps, or learning rates, so this would arrive from nowhere and draw no reply. #cookbooks touches fine-tuning only at the dataset handoff; a decision about what the step ledger emits per step is a design argument, which is #engineering's job. The invented thread has someone building the three-step end-to-end mock fixture and asking what the rate column reads at each step and whether it's uniform across batches in a window — dario settles the three values, leaving how a longer run spaces steps between top and bottom open for the sibling.

*Still leaves open:* how a longer run spaces the steps between the top and the bottom

*Must appear literally:* `1e-04`, `1e-05`, `5e-05`, `current_step`

*A new conversation in #incidents on 2025-04-11:*

```
13:32  gideon: the three step mock run, what are we expecting it to report across those steps? plain-what question, i couldnt tell from the log
13:34  dario: 5e-05 then 1e-04 then 1e-05 i think. thats the shape we want coming out of it
13:35  dermot: reported where though, one row at the end or one per batch?
13:37  dario: per batch. each batch gets its own stats row
13:38  gideon: ok but then the row has to say which step it belongs to no? otherwise ordering them is guesswork
13:40  dario: mhm, it carries current_step and that step's rate. so the row stands on its own, you dont have to line it up against anything else
13:41  dermot: yeah ok. i'd read the middle one as a bug before you said that
```

### g11.r2.sc3-floor — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*Nobody says:* a bottom that is held rather than passed through is a floor, and a default written once at module level is what every call gets unless it says otherwise.

*5 remarks — 2 reporting the problem, 3 settling the design.*

#### `g11.r2.l8` — rule

**gideon**, 2025-04-03, #viewer

> After warmup it does come down fine, ya, but the tail of a long run is training at basically nothing and the loss just stops moving.

*What a reader should take from it:* the team agrees the end of a long run currently trains at a useless rate

*Step it builds toward:* `g11.r2.sc3-floor` — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*Drafted as:* After warmup it does come down, sure, but the tail of a long run trains at basically nothing and the loss stops moving.

*Why there:* No candidate room is discussing training dynamics at all — the eight threads cover batch retry semantics, PR ownership, log-noise removal, a viewer metadata field, and throttle/cost accounting. An LR-schedule observation would arrive from nowhere in every one of them. The nearest neighbor, #engineering 2025-03-19, shares the word "tokens" but is about output-token counts feeding the throttle check, a different subject. The invented thread sits in #engineering because this is a design argument about training code, which is what that room is for; #cookbooks only owns the dataset-to-fine-tuning handoff, not schedule internals. Gideon is the natural speaker: across this corpus he takes a reported symptom and traces it to the mechanism, and here he confirms the shape of the problem without settling what the floor should be — that's the sibling remark later in the same thread.

*Still leaves open:* what the bottom of the run should be instead of nothing

*Must appear literally:* `After`

*A new conversation in #viewer on 2025-04-03:*

```
14:02  konrad: the lr plot off the long run, is the far end meant to look like that
14:04  gideon: which end, the ramp?
14:05  konrad: no the far end. it flattens out into nothing
14:06  gideon: ya. After warmup it does come down fine, thats not where it goes wrong
14:07  dario: so decaying too fast, or just landing too low
14:09  gideon: too low. the tail of a long run is training at basically nothing
14:10  dario: and the loss
14:11  gideon: just stops moving. so basically the tail is the bit we fix, the front of it is ok
14:12  konrad: ok. i had it backwards, i was staring at the ramp all morning
```

#### `g11.r2.l9` — rule, exclusions_or_crossover

**dermot**, 2025-04-18, #incidents

> on the decay, i'd sooner it flatten out at a tenth of base_lr and hold there, even past the planned end, than keep sliding down

*What a reader should take from it:* the team agrees the rate levels off at a tenth of the base rate and holds there beyond the planned end

*Step it builds toward:* `g11.r2.sc3-floor` — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*Drafted as:* i'd sooner it flatten out at a tenth of base_lr and stay there, even past the planned end, than keep sliding down.

*Why there:* Every candidate sits in the inference/dataset half of the company — batch cancellation and resume, docker image pinning, release tagging, viewer removal, serving-infra scoping. None of them is arguing about a training run's learning rate schedule, and a decay-floor opinion dropped into any of them changes the subject with nobody positioned to answer it. The nearest hook is nikolai's "still waiting on a reviewer for the finetuning client PR" on 2025-04-28 in #engineering, but that thread is entirely about who owns the serving infra scope. The right home is a fresh #engineering thread: that room is explicitly where design arguments about training code land, whereas #cookbooks only owns the handoff of a curated dataset into fine-tuning, not the scheduler internals. The conversation would be dermot, nikolai and dario going through the finetuning client's schedule while the PR is finally getting reviewed — cosine vs linear decay, what happens when a run goes past its planned step count, and where the floor is actually written down (the sibling question about whether a call can pass its own).

*Still leaves open:* where that tenth is written down and whether a call can ask for a different one

*Must appear literally:* `base_lr`

*A new conversation in #incidents on 2025-04-18:*

```
15:22  petar: lr in last nights run was basically nothing by the end. is that expected
15:24  dermot: at the moment yes, it slides the whole way down. id sooner it flattened out and held there
15:25  nils: flatten at what
15:26  dermot: a tenth of base_lr
15:28  petar: and if a run overshoots the planned end, does it keep creeping under that
15:29  dermot: no it holds. thats more or less the point, past the planned end included. nobodys been in the scheduler yet though
15:31  nils: yep. the one last night just crawled to zero and sat there for hours
```

#### `g11.r2.l11` — exclusions_or_crossover, observability

**nils**, 2025-04-21, #general

> grid row A is the eight-step one i let overrun; by step 99 the rate had gone negative and that run wrecked the weights. agreed it's a bug, not my config.

*What a reader should take from it:* the team agrees steps beyond the planned length currently produce negative rates and that this is a bug

*Step it builds toward:* `g11.r2.sc3-floor` — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*Drafted as:* grid row A is the eight-step one i let overrun, and by step 99 the rate had gone negative; that run wrecked the weights.

*Why there:* Neither candidate is anywhere near this subject. #engineering on 03-19 is entirely about the v0.1.21 cut, the output-token fix and whether the throttle path got re-checked; #pipeline on 03-25 is Nils shepherding PR 584 and arguing about Mistral fixture coverage. A training grid sweep whose learning rate goes negative past the planned step count touches the step ledger / schedule math, not the request layer or the release — dropping it into either day would change the subject mid-thread and draw no reply, which is exactly the visible kind of plant. The right home is a fresh #engineering thread: it is the catch-all for design arguments that have no narrower channel, and the sibling question (what a step past the end should report instead) is a schedule-API design call, not a cookbook or viewer matter. Nils is the right person — he owns the overnight run and is the one who let row A overrun.

*Still leaves open:* what a step past the end should report instead of a negative number

*Must appear literally:* `A`, `99`

*A new conversation in #general on 2025-04-21:*

```
14:03  nikolai: which of the sweep rows went negative on the rate
14:05  nils: row A. the eight-step one — i let that one overrun instead of stopping it where it was meant to stop
14:06  nikolai: how far past
14:08  nils: far enough that by step 99 it was already the wrong side of zero
14:10  dermot: and thats the run that came back unusable, or was that a different one
14:11  nils: same one. that run wrecked the weights, there was nothing worth keeping out of it
14:13  dermot: mhm. so bug then, not you setting it up wrong
14:14  nils: agreed, it's a bug and not my config. nothing i put in row A asked it to carry on past the end
14:16  dermot: yeah ok. id had it filed as a bad sweep entry, that said i never looked at what step it turned
```

> **Problems:** longer than one remark

#### `g11.r2.say20` — rule

**dermot**, 2025-04-21, #help

> to be clear it's not a floor bolted onto a decay-to-zero line, min_lr_ratio rescales the whole slope — with min_lr_ratio=0.5, half way down the decay you read 7.5e-05 not 5e-05

*What a reader should take from it:* the team agrees min_lr_ratio rescales the entire decay line rather than acting as a floor on a decay-to-zero line

*Step it builds toward:* `g11.r2.sc3-floor` — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*Drafted as:* to be clear the ratio isn't a floor clipped onto the old line, it rescales the whole slope — min_lr_ratio=0.5, half way down the decay, reads 7.5e-05 not 5e-05

*Why there:* Every listed conversation is about PR triage, docker image pinning, viewer removal, llama4 scoping, tagging a release or cache-silent model swaps — none of them is anywhere near an LR schedule. min_lr_ratio is training-loop semantics: whether the ratio floors a decay-to-zero curve or rescales the whole decay. Dropping it into #cookbooks (2025-04-16 is resume/batch-id and backend_params image overrides) or #code-review (PR numbers and reviewer assignment, no diff content about schedules) would change the subject with nothing above it to answer and nothing below reacting. The natural home is a design argument in #engineering, where someone reading the scheduler asks the floor-vs-rescale question and dermot settles it; the sibling details (default value, keyword-only, 0.0 legal) then land in the review of the PR that implements it.

*Still leaves open:* Doesn't say what the default ratio is, that it's keyword-only, or that 0.0 is a legal value — those come from l10 and rev1.

*Must appear literally:* `min_lr_ratio`, `min_lr_ratio=0.5`, `7.5e-05`, `5e-05`

*A new conversation in #help on 2025-04-21:*

```
11:22  emil: quick one before i write the schedule test — is min_lr_ratio just a floor we clamp the lr at, or is it doing more than that
11:25  dermot: more than that. its not a floor bolted onto a decay-to-zero line, it rescales the whole slope
11:27  emil: hm. so same curve, just cut off lower down? not entirely sure i see the difference in practice
11:29  dermot: the difference shows up in the middle. with min_lr_ratio=0.5, half way down the decay you read 7.5e-05, not 5e-05
11:31  emil: ah yup. and 5e-05 is exactly what the clamp reading gives you there, which is why it looked fine to me
11:33  nikolai: right thats the nasty bit both of them plot as a sane looking line
11:35  dermot: mhm. worth pinning down now, whoever ends up in the scheduler
11:36  emil: yup, glad i asked
```

#### `g11.r2.l10` — rule

**emil**, 2025-05-30, #code-review

> also did a pass on 663 - min_lr_ratio sits behind a bare * so callers have to name it, MIN_LR_RATIO stays the module-level default. lets not let those two spellings drift apart

*What a reader should take from it:* the team agrees the fraction is a module-level default with a per-call keyword of the same name

*Step it builds toward:* `g11.r2.sc3-floor` — The descent stops at a tenth of the base rate, that fraction living as a module-level default a caller can pass over, and nothing ever reports below it, including steps past the planned end.

*Drafted as:* In review I wrote min_lr_ratio for the kwarg and MIN_LR_RATIO for the module-level default; don't let those two spellings drift apart.

*Why there:* That day is explicitly about 653 and 663 sitting unreviewed — konrad opens with finetuning moving along and both PRs touching his service, and nikolai pings emil at 10:18 to take a look at both, singling out the finetuning client as the one he doesn't want to drift. Emil's only reply so far is about his own PR 652, so a short note that he did a review pass on 663 and left a naming call on the LR-floor knob answers the ask that's already live in the room and comes from the person it was directed at. It settles the shape (module-level default plus same-named per-call kwarg) without saying what the value is or what the rate does there.

*Still leaves open:* what value that default holds and what the rate does when it gets there

*Must appear literally:* `*`, `663`, `MIN_LR_RATIO`, `min_lr_ratio`

*Goes into the real conversation in #code-review on 2025-05-30, after 11:04 emil:*

```
09:00  konrad: Finetuning is moving along on my end, but PR 653 and PR 663 have been sitting unreviewed for a while now and both touch my service
09:11  nikolai: Both 653 and 663 are ready on my end, no blockers, just waiting on someone to take a look
09:11  nikolai: The torch fix is pretty contained but the finetuning client is the one I'd rather not let drift much longer
09:54  konrad: @Emil Brandvold what's the situation with PR 652, that one's been open the longest by a fair margin.
10:18  nikolai: @Emil Brandvold if you've got cycles, 653 and 663 are both ready for a look too.
10:18  nikolai: Actually, separate thing: does anyone know for certain whether the sandbox guarantees survive if you bring your own image?
10:18  nikolai: I said "should do" at the demo and I'm not confident that was right
10:26  konrad: oh, that's actually my area
10:45  nikolai: So does it?
10:45  nikolai: Survive a caller-supplied image?
11:04  emil: 652's been on me, the viewer returns this for datasets that haven't finished indexing and I've been going back and forth on whether to retry or let th   <-- THE REMARK GOES HERE
11:20  konrad: Is the `retry_after` value reliable or just a rough estimate?
11:20  konrad: And what does the caller get today if they hit this before indexing finishes, an exception?
17:20  nikolai: Sorry, I meant to come back on this earlier - the sandbox guarantees don't hold if you bring your own image, I went and checked after the demo.
17:20  nikolai: I told someone at the demo "should do" and that was wrong, just wanted that on record before the weekend.
17:21  emil: Not sure if that 60 is coming from the viewer or if I'm the one setting it.
```

> **Problems:** longer than one remark

### g11.r2.sc4-length-changes — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*Nobody says:* if the run length is the thing the shape is measured against, then a warmup that overruns it and a length that changes mid-flight are both just a different measurement, not an error.

*5 remarks — 2 reporting the problem, 3 settling the design.*

#### `g11.r2.l12` — failure_behavior

**nikolai**, 2025-04-29, #general

> ran the cookbook smoke example while poking at 653 its 3 steps and the default warmup is 10 so it crept along all three and never got near base_lr

*What a reader should take from it:* the team agrees a warmup ask larger than the run currently leaves the whole run below the base rate

*Step it builds toward:* `g11.r2.sc4-length-changes` — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*Drafted as:* the cookbook smoke run is 3 steps and its default warmup is 10, so it crept along all three and never got near base_lr.

*Why there:* None of the candidate conversations are about training hyperparameters. The two #cookbooks days are docker image pinning / resume-ignoring-the-model (4/16) and SimpleStrat CI + workspace mount writes (4/03); the four #code-review days are PR queue triage where nobody discusses what a config does at runtime; #engineering 2025-05-20 is a Gemini lazy-load question in the batch download path. A warmup-exceeds-total-steps finding, and the follow-on argument about whether an over-long warmup should be clamped to the run or rejected, is a design argument about library behavior — #engineering is exactly the room for that, and it needs to be a conversation that has a finetuning config in front of it. Nikolai is the right person: he owns PR 653, the finetuning client, and he already has form on this shape of question ("if we do tighten this my preference is the first task blows up at create"), with Konrad as the finetuning service owner he keeps chasing for sign-off.

*Still leaves open:* whether an over-long warmup ask should be trimmed to the run or refused outright

*Must appear literally:* `base_lr`

*A new conversation in #general on 2025-04-29:*

```
14:21  konrad: lr never really moved in the smoke run, is that normal
14:23  nikolai: which run
14:24  konrad: the cookbook smoke example. I ran it while i was poking at 653
14:26  nikolai: ah thats 3 steps
14:27  konrad: ok and what does that do to the lr exactly
14:28  nikolai: default warmup is 10 so it just crept along all three
14:29  dermot: mhm so it never got anywhere near base_lr, the whole run sits inside the ramp
14:31  nikolai: right so the example should pin its own warmup rather than take the default, nobodys been in there yet
14:32  konrad: right, anyway not a schedule bug then
```

> **Problems:** describes asking rather than settling

#### `g11.r2.say19` — exclusions_or_crossover

**nils**, 2025-05-01, #pipeline

> let me think - on the resume the stats keep counting current_batch straight on from the finished ones, no reset to 1, the six after it came out 7 through 12.

*What a reader should take from it:* the team agrees current_batch keeps counting across a resume instead of restarting at 1

*Step it builds toward:* `g11.r2.sc4-length-changes` — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*Drafted as:* on the resume the stats keep counting current_batch straight on from the finished ones, no reset to 1 — the six batches after it came out 7 through 12.

*Why there:* no candidate location in range for this person

*Still leaves open:* doesn't say what current_step reads on those rows, what rate each carries, or how the run's new length is exposed

*Must appear literally:* `current_batch`

*A new conversation in #pipeline on 2025-05-01:*

```
14:20  gideon: plain question - what is current_batch supposed to show after a resume?
14:23  dario: it doesnt go back to 1, if thats what youre asking. it counts on from the ones that already finished
14:25  gideon: ya but counts on from where exactly. the six we ran after the resume friday looked wrong to me tbh
14:28  nils: let me think - they came out 7 through 12. straight on from the finished ones, no reset, thats how the stats keep it
14:30  dario: mhm, that tracks with the numbers i had
14:32  gideon: ok so the odd part was me, i was counting the first one after the resume as 1
```

> **Problems:** longer than one remark

#### `g11.r2.l14` — exclusions_or_crossover

**dario**, 2025-05-06, #incidents

> resumed a run with epochs raised and the rates kept following the old length, so honestly it was already sitting at the bottom about a third of the way through

*What a reader should take from it:* the team agrees a resumed run currently keeps the schedule of the shorter run it was checkpointed from

*Step it builds toward:* `g11.r2.sc4-length-changes` — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*Drafted as:* resumed with epochs raised and the rates kept following the old length, so it was down at the bottom a third of the way through.

*Why there:* The remark is about a training run's learning-rate schedule — epochs raised on resume, rates still following the checkpointed run's step count, LR floored a third of the way through. None of the candidates are in a room where training code is argued about. The #incidents 2025-04-18 thread is the only one touching "resume", but it is inference-run cache fingerprinting (prompt hash, model, provider keying a cached batch job), not epochs or schedules; dropping a training-schedule observation into Nikolai's fingerprint question changes the subject and gets no reaction. #viewer is the dataset surface and progress bars, #help is a capability-check hard-block, #code-review 03-14/03-21 are schema_check and Mistral batch PRs, #cookbooks 05-05 is grepping `.choices` out of examples. #cookbooks does own the curated-dataset-into-fine-tuning handoff, but that thread is a response-object migration triage, not schedule behaviour. This belongs in #engineering, the room for design arguments about training code that haven't found a narrower channel — and it needs a sibling to settle which length the rates get read off and from which step, which no listed thread is positioned to supply.

*Still leaves open:* which length a resumed run's rates should be read off, and from which step

*A new conversation in #incidents on 2025-05-06:*

```
14:02  gideon: the restarted run from yesteday looks off to me, curve goes flat way earlier than it should. what am I looking at
14:06  dario: which one, the fresh one or the one you picked back up?
14:08  gideon: picked back up. we raised the epochs on it before it went in again
14:12  dario: mhm thats it then. the rates kept following the old length, not the longer one you asked for
14:15  emil: so it was still shaped for how long the run used to be, is that the read
14:19  dario: yeah. so honestly it was already sitting at the bottom about a third of the way through, and everything after that was just flat
14:21  gideon: ya ok, thats exactly where the plot dies
```

#### `g11.r2.l13` — failure_behavior

**konrad**, 2025-06-02, #viewer

> look, keeping warmup 10 on the 3 step case as a test at rel=1e-12, plus the 1 step run with warmup 99 - single step returns base_lr, no exeption.

*What a reader should take from it:* the team agrees a warmup longer than the run is a legal call rather than an error

*Step it builds toward:* `g11.r2.sc4-length-changes` — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*Drafted as:* I'm keeping warmup 10 on the 3 step case as a test, asserting the ramp with rel=1e-12 and expecting no exception out of it.

*Why there:* None of the eight candidates is anywhere near this subject. They are about PR ownership overlap (679/678), importorskip/conftest scope, torch import guards, cookbook live-API verification, a viewer version tag, a release cut, and GEPA null scores. This remark is about numerical test cases for a learning-rate warmup schedule — warmup longer than the run, base_lr on a single step, a rel=1e-12 comparison — which is finetuning training code. Dropping it into #cookbooks or #viewer would be the tokenizer-in-the-cookbook-room mistake, and the 2026-01-23 #engineering thread explicitly parks all finetuning work pending the plan doc, so it can't host a settled call on schedule semantics either. Konrad is the right person for it (he owns the finetuning side throughout the corpus), just not on any of these days. The conversation that should exist is a #code-review thread on his own finetuning PR where the open question is whether warmup_steps > total steps should raise or clamp, and Nikolai is asking for the edge cases before he signs off — with the sibling remark supplying the three expected rates and the "treat the ask as a clamp, not an error" framing.

*Still leaves open:* what the three rates should come out as, and what the ask gets treated as instead

*Must appear literally:* `base_lr`, `rel`, `rel=1e-12`

*A new conversation in #viewer on 2025-06-02:*

```
11:12  dario: the warmup longer than the run thing - do we keep the 3 step case in the tests, or does it go now that its not an error path
11:14  konrad: keep it. warmup 10 on the 3 step one, thats the case i want sitting there as a test
11:15  konrad: and compared tight, rel=1e-12. not the loose default
11:17  emil: rel that tight is fine honestly, the values are closed form, theres nothing to drift
11:18  dario: ok but that one still has more than one step in it. what about a run thats a single step, is that covered or not
11:21  konrad: no, thats a second one. 1 step run, warmup 99
11:23  emil: so on that one you're expecting it just hands back the base value and nothing blows up?
11:25  konrad: mhm. the single step returns base_lr, no exeption
11:27  dario: that tracks. the tight compare is the whole point really, otherwise it passes for the wrong reason
```

#### `g11.r2.l15` — exclusions_or_crossover

**gideon**, 2025-06-03, #viewer

> so basically on a resume the next step after the finished ones just asks the same helper again, with the trainer's total_steps, 4 here once epochs grew.

*What a reader should take from it:* the team agrees a grown run continues from the step after the completed ones using the same function against the new length

*Step it builds toward:* `g11.r2.sc4-length-changes` — The schedule bends to whatever run length it is handed: a warmup longer than the run is trimmed down to the run rather than refused, and a run that grew on resume is scheduled off the new length carrying on after the steps already done.

*Drafted as:* On a resume the next step after the ones already done just asks the same helper, only with the run's new length.

*Why there:* Both candidates are PR-triage days in #code-review: 05-01 is PR 658/643/651/632, the response object and WS-055; 05-05 is 0.1.24, PR 652/654 and the download feature. Neither room is anywhere near trainer step accounting — no one that day mentions a scheduler, a resume ledger, epochs or total_steps, and gideon's own line of argument on both days is the viewer reading unstable response fields. Dropping a settled decision about how a grown run recomputes its next step into either thread would change the subject and draw no reaction. The remark is a training-code semantics call, and with no training channel in the list it belongs in #engineering, which is explicitly where design arguments live that haven't found a narrower home; #cookbooks only owns the handoff into fine-tuning, not the trainer's step math, and #pipeline's "resume" is batch request resume, a different resume entirely.

*Still leaves open:* what happens when the length it is handed is shorter than the warmup that was asked for

*Must appear literally:* `epochs`, `total_steps`

*A new conversation in #viewer on 2025-06-03:*

```
14:02  dario: quick one while im in here — on a resume, the step right after the ones already finished. does that recompute or does it read something off the checkpoint
14:04  gideon: recompute. it just asks the same helper again, nothing gets read back
14:06  dario: same helper is fine but with what, the count from when it saved or the current one
14:07  gideon: the trainers total_steps. so basically whatever the trainer is holding now, not what was written down at save time
14:09  dermot: so the saved one never comes into it
14:10  gideon: exactly. and in the run you two were looking at thats 4, once epochs grew. thats why the number moved between the two
14:12  dario: mhm ok that tracks. nobodys written it that way yet though has anyone
14:13  gideon: not yet no, um. i was going to but honestly though i wanted it agreed first
14:15  dario: good, i was about to go hunting for where the count gets persisted
```

### Herrings — believed at the time, overturned later

#### `g11.r2.lr-decay-to-zero-dario` — herring

**dario**, 2025-01-30, #incidents

> lr schedule is settled i think: linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps. one function, no extra knobs.

*A herring: stated as settled at the time, overturned later (from 2025-03-24).*

*Drafted as:* lr schedule is settled: linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps. one function, no extra knobs.

*Why there:* Every candidate room is about the inference/request layer — batch response shapes, token accounting, PR queue logistics, cache paths, recipe test coverage. None of them is chewing on training code, and an lr schedule with warmup_steps/total_steps would arrive from nowhere in all eight: the 2025-03-10 #pipeline thread is deadlocked on whether Mistral batch populates per-line usage, #code-review 2025-03-06 is PR 581 and the 565/566 coverage check, and #cookbooks 2025-02-11 touches fine-tuning only as a downstream handoff, not as trainer internals. The right home is #engineering, the room for design arguments that haven't found a narrower channel — dario settling a schedule shape while someone is wiring the trainer loop and asking whether decay type and a min-lr floor need to be configurable.

*A new conversation in #incidents on 2025-01-30:*

```
15:19  gideon: the lr schedule from tuesdays run, is that decided now or still open?
15:21  dario: settled i think. linear warmup while step < warmup_steps
15:22  gideon: and after warmup? what does it do
15:24  dario: straight linear decay to 0.0 at total_steps. no plateau or anything in between
15:25  konrad: 0.0 exactly? i assumed it bottomed out somewhere above zero
15:26  dario: zero at the end yeah. its one function the whole way, no extra knobs to set
15:28  konrad: nobodys been in that file yet though
15:29  gideon: Ya. I had two seperate fns in my head, warmup and then decay
```

#### `g11.r2.lr-decay-to-zero-konrad` — herring

**konrad**, 2025-02-19, #viewer

> Checked against the ledger, the decay lands at exactly zero at total_steps, and warmup keeps teh strict `step < warmup_steps` compare tinker_trainer already uses.

*A herring: stated as settled at the time, overturned later (from 2025-03-24).*

*Drafted as:* Checked it against the ledger: the last optimizer step lands at exactly zero, and warmup keeps the strict step < warmup_steps compare tinker_trainer already uses.

*Why there:* Every candidate day is chewing on something unrelated: docker sandbox uid defaults and WS-033 verifier contracts (cookbooks 02-26), broken example scripts after the LLM interface change (cookbooks 01-22), PR queue ordering, reviewer assignment and the cost-logging question (code-review 02-07, 02-14, 02-18, 03-10, 01-27), and Gemini rate-limit issue triage (engineering 03-03). None of them has anyone looking at a trainer's step loop, so a verified claim about linear decay to zero at total_steps and the warmup boundary in tinker_trainer arrives from nowhere and nobody answers it. There is no room in the list dedicated to training code — #pipeline is the request layer, #cookbooks is the example corpus and the handoff into fine-tuning, not the schedule arithmetic inside the trainer — which is exactly the case #engineering exists for. Konrad is right to be the one saying it: he is the one who habitually goes and checks a claim himself and reports the compare that is actually in the code.

*A new conversation in #viewer on 2025-02-19:*

```
13:12  petar: quick one on the lr schedule - does the decay actually reach zero at the end or does it just get near it
13:15  konrad: zero. exactly zero at total_steps, i checked it against the ledger
13:18  petar: ok good. warmup is the part i keep second guessing though, whats the compare at the boundary step
13:19  nils: strict one i thought? but dont quote me
13:22  konrad: right, strict. `step < warmup_steps`, which is what tinker_trainer already does, so we keep that and dont invent a second convention
13:24  petar: mhm, i had the boundary sitting on the other side of that
13:26  konrad: anyway the ledger rows are there if you want to eyeball the tail before anyone writes it
```

#### `g11.r2.rev1` — rule, exclusions_or_crossover, observability

**dario**, 2025-03-26, #help

> dropped hard-coding 0.0 at total_steps — step 99 of the eight-step run went negative. learning_rate_at takes min_lr_ratio, default MIN_LR_RATIO = 0.1, ends at 1e-05; pass min_lr_ratio=0.0 and it lands on exactly 0.0 at the last step again.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* decay to 0.0 at total_steps is gone — the tails stopped moving and step 99 of the eight-step run went negative. learning_rate_at now takes min_lr_ratio, default MIN_LR_RATIO = 0.1: that run ends at 1e-05 and stays clamped there.

*Why there:* All seven candidates are inference-layer or release-coordination threads: provider backends and PR 565/566, batch submission and gemini response shapes, executor image defaults, validator offline behaviour, PR triage logistics. None of them has anyone touching training code, so a learning-rate schedule change arrives from nowhere and gets no reaction — the vocabulary overlap ("run", "step") is not subject overlap. #cookbooks touches fine-tuning only as the handoff out of a curated dataset, not the scheduler internals, and #incidents is for things broken right now rather than a fix already landed. #engineering is the stated catch-all for work without a narrower channel, and a short-run schedule bug (flat tails, negative LR past the end) plus the floor that replaces it is the kind of half-settled thing dario reports there.

*Must appear literally:* `0.0`, `0.1`, `1e-05`, `MIN_LR_RATIO`, `MIN_LR_RATIO = 0.1`, `learning_rate_at`, `min_lr_ratio`, `min_lr_ratio=0.0`, `total_steps`

*A new conversation in #help on 2025-03-26:*

```
14:12  emil: the eight step run came back with a negative lr at step 99. did i mess up the config or is that us
14:14  dario: thats us. the decay hard-codes 0.0 at total_steps and then just keeps walking downward past it
14:15  dario: so that whole "linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps, one function no extra knobs" thing, were dropping it. the end isnt pinned at zero any more
14:16  dermot: so learning_rate_at grows an argument, is that the shape of it?
14:17  dario: mhm. min_lr_ratio, default MIN_LR_RATIO = 0.1, so it bottoms out at 1e-05 instead of walking through zero
14:19  emil: what about the runs that Do want it to land on zero at the end, some of the older configs read the last step
14:20  dario: min_lr_ratio=0.0 and you get exactly 0.0 at the last step again, same as before. honestly the default is the only thing that changes for most people
14:22  dermot: yeah ok. that said the negative was only ever visible past total_steps, which is presumably why nobody hit it before
```

> **Problems:** longer than one remark

#### `g11.r2.rev2` — rule, failure_behavior

**konrad**, 2025-06-02, #general

> Dropped the strict step < warmup_steps compare — the first step trained at rate 0, and warmup 10 on a 3 step run never got near base_lr. It's 1 <= step <= effective_warmup now, effective_warmup = min(warmup_steps, total_steps), clipped rather than raising.

*A herring: stated as settled at the time, overturned later (from ?).*

*Why there:* None of the eight candidates is anywhere near training-loop code. The two #engineering days are about semaphore gating/OOM (Mar 14) and the v0.1.21 throttle-vs-estimation split (Mar 19); #releases 2025-05-30 is the v0.1.25 support table and release notes; both #viewer days are the download path and a version tag rendering; #code-review 2025-05-06 is the docker user arg and PRs 653/661; #code-review 2026-01-27 is GEPA null scores; #engineering 2026-01-22 is the README refresh. A warmup-schedule off-by-one would land in none of those threads — it would arrive from nowhere and get no reaction. The natural home is #code-review, where konrad posts changes and gets a pass on them: a review of the finetuning LR warmup schedule, where a reviewer points out the first step trains at rate 0 and a smoke run shorter than warmup_steps never reaches base_lr, and konrad reports back what he changed. The finetuning client was thin and under-documented as of v0.1.25 (Emil flagged the section needed a usage guide), so schedule work on it in June 2025 sits right.

*Must appear literally:* `step < warmup_steps`, `1 <= step <= effective_warmup`, `effective_warmup = min(warmup_steps, total_steps)`, `base_lr`

*A new conversation in #general on 2025-06-02:*

```
10:14  gideon: the 3 step smoke run trained its first step at rate 0. thats the compare we agreed on ya?
10:16  konrad: right. we had it that decay lands at exactly zero at total_steps and warmup keeps the strict `step < warmup_steps` compare tinker_trainer already uses. thats the bit thats going. a first step at rate 0 is not something i want to keep defending
10:18  nikolai: so whats it become
10:19  konrad: `1 <= step <= effective_warmup`
10:21  gideon: um that gets step one back, but warmup 10 on a 3 step run still never gets near base_lr does it
10:23  konrad: no thats the other half of it, `effective_warmup = min(warmup_steps, total_steps)`. short run reaches base_lr at the end instead of stopping partway up
10:25  nikolai: and if the config asks for more warmup than there are steps do we shout about it
10:26  konrad: no. clipped, not raising. presumably nobody wants a run to die over that
10:28  gideon: ok so the smoke run was tripping both of those at the same time, no wonder it looked so weird
```

> **Problems:** longer than one remark

