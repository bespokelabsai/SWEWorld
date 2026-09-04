# Clues for g11 — Fine-tuning step ledger: one step unit, one checkpoint identity, one resume contract

39 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

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
| 2025-01-21 | #code-review *(new)* | dario | ok, settled - a step that's both an interval hit and an epoch boundary writes two checkpoints, `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, the two names we already have, unchanged. | *herring* |
| 2025-01-21 | #pipeline *(new)* | dario | no floor — learning_rate_at just decays linearly to zero at total_steps, and warmup keeps the `step < warmup_steps` comparison the trainer already uses. | *herring* |
| 2025-01-22 | #code-review *(new)* | konrad | Look, the reason set is just plain sorted(), alphabetical - a step thats both gives you ("epoch", "interval"). No custom ordering to maintain. | *herring* |
| 2025-01-22 | #cookbooks *(new)* | konrad | Settled the shedule: linear decay to 0.0 at the end of the run, warmup gated on step < warmup_steps. Ported straight off tinker_trainer.py:548. | *herring* |
| 2025-03-14 | #engineering *(new)* | nikolai | if a step is both an interval hit and an epoch close i want them back in the order the constant lists them sorting put final ahead of interval | `rule` |
| 2025-03-14 | #code-review *(new)* | emil | on fireworks there are no checkpoints written at all, one packed step per epoch and the job hands the weights back at the end, so nothing for us to tag on that side. | `scope` |
| 2025-03-17 | #engineering *(new)* | gideon | honestly though, i sorted the checkpoint dir this morning and _step_10 came back before _step_9, wasted a minute thinking we'd droped one | `rule` |
| 2025-03-17 | #pipeline *(new)* | nils | let me think — the epoch on a step record should come from asking the plan which epoch that batch ordinal landed in, not from whatever loop counter we're inside. | `exclusions_or_crossover` |
| 2025-03-17 | #code-review *(new)* | dario | dropped the two-records-per-step thing, {prefix}_step_{n} and {prefix}_epoch_{n} are both gone — resume picked up the epoch-named twin and replayed a window. one save_checkpoint now, name from checkpoint_name(prefix, step), reasons ("interval", "epoch") | `rule`, `scope` |
| 2025-03-19 | #engineering *(new)* | konrad | The default-config fixture in test_trainer.py trains fine and leaves nothing behind, so I re-ran four minutes of it just to get a wieght file to poke at. | `scope`, `observability` |
| 2025-03-19 | #pipeline *(new)* | nils | let me think through that - trainer.get_checkpoints() handed me two rows with the same name and the same path, different loss on each, and whichever one resume grabs is a coin flip | `failure_behavior`, `observability` |
| 2025-03-19 | #releases *(new)* | dario | the decay to zero i asked for is gone — that 40 step job's tail trained nothing. learning_rate_at floors at MIN_LR_RATIO = 0.1 of base_lr and clamps past the end: learning_rate_at(99, 8, 1e-4, 2) == 1e-05 | `rule`, `exclusions_or_crossover` |
| 2025-03-20 | #engineering *(new)* | dermot | mhm, the two every-n knobs can stay off if someone wants them off, that said the step that ends the run should write a checkpoint regardless of either setting. | `scope` |
| 2025-03-20 | #cookbooks *(new)* | konrad | Look, I pinned the eight step curve from the warmup-2 job into a test, and the per-batch stats lines match it once approx has rel=1e-12. | `observability` |
| 2025-03-21 | #pipeline *(new)* | dermot | step 1 logs a learning rate of 0.0 on every run i've looked at, so the first optimizer step moves nothing. agreed it can't stay zero at step 1. | `rule` |
| 2025-03-21 | #cookbooks *(new)* | konrad | mhm. A resume where only the epoch count changed should keep walking down from the step it stoped at, on the recomputed longer schedule, not restart the ramp. | `exclusions_or_crossover` |
| 2025-03-24 | #engineering *(new)* | nils | ran [c.name for c in result.checkpoints] on the two-epoch run and got two rows for step 2, same loss, different names. so one step is definitely storing two records. | `rule`, `observability` |
| 2025-03-24 | #pipeline *(new)* | gideon | so basically we set warmup_steps=2 and then step 2 is alredy on its way down - the step where warmup ends should be the one sitting at full base rate. | `rule`, `observability` |
| 2025-03-24 | #cookbooks *(new)* | nikolai | cap it at the run lenght then the 3 step case comes out a third two thirds base and i'd say pin it with rel=1e-12 so nobody re tunes it later | `failure_behavior`, `observability` |
| 2025-03-24 | #releases *(new)* | dermot | dropped the `step < warmup_steps` comparison we ported off tinker_trainer.py:548, step 1 trained at rate 0. it's base_lr * step / effective_warmup now, effective_warmup = min(warmup_steps, total_steps), clipped not raised. | `rule`, `failure_behavior` |
| 2025-04-09 | thread:new|g11.r1.l2 *(new)* | dermot | left a note on the diff — CHECKPOINT_REASONS wants to live next to the step-unit constants in the ledger module, and the trainer should stop typing those strings inline. | `rule` |
| 2025-04-09 | thread:new|g11.r1.l8 *(new)* | dermot | had to resume the late night run and it asked me for a checkpoint name, so i ended up grepping the log for it — nothing in the step tells you what it will be called. | `rule` |
| 2025-04-09 | thread:new|g11.r1.l16 *(new)* | dermot | yeah — canonical_reasons should raise on anything outside the list, same error type the rest of the ledger raises, rather than quietly passing it through. | `failure_behavior` |
| 2025-04-09 | thread:new|g11.r2.L9 *(new)* | dermot | past the end it should just return the floor, MIN_LR_RATIO in the ledger module. nikolai wants min_lr_ratio passable per call for a cookbook run, that seems fair to me | `rule`, `exclusions_or_crossover` |
| 2025-04-24 | thread:new|g11.r2.L6 *(new)* | emil | and it shouldn't bottom out at zero — honestly a tenth of the base rate is still enough to move something on the last step of the run. | `rule`, `observability` |
| 2025-05-06 | thread:new|g11.r2.L4 *(new)* | dario | honestly the last third of that 40 step job barely moves — loss flat, rate small enough it may as well not be running. the tail should still train. | `rule` |
| 2025-05-07 | thread:new|g11.r1.l6 *(new)* | konrad | look, two places build the checkpoint name and they dissagree. one CHECKPOINT_NAME_TEMPLATE that takes the prefix and the step, and both call sites go through it. | `rule` |
| 2025-05-13 | thread:new|g11.r2.L12 *(new)* | dario | honestly i don't think that should be an error — half the cookbook configs get pasted into runs shorter than the warmup they were written for. | `failure_behavior` |
| 2025-05-14 | thread:new|g11.r1.l14 *(new)* | nikolai | heads up when a window spans the boundary the record closing epoch one reads epoch 2 thats the batch it stoped on so please dont fix it | `exclusions_or_crossover`, `observability` |
| 2025-05-14 | page:engineering/training-step-ledger-append-and-update-rules.md *(new)* | dario | if the name matches the last one we appended, we update that entry in place, newer loss wins and both tag sets folded together, no second row. | `failure_behavior` |
| 2025-06-10 | page:engineering/rate-limiter-warmup-ramp-shape-and-defaults.md *(new)* | nils | let me think through the ramp shape — warmup should climb in even shares of the base rate, one share per step, and the first step gets a full share like every other one. | `rule` |
| 2025-06-11 | page:engineering/checkpoint-naming-and-on-disk-layout-for-finetuning-runs.md *(new)* | dario | honestly i just want step two to come out as checkpoint-s000002, six digits padded, so i can write the name down before the run gets there. | `rule`, `observability` |
| 2025-06-11 | page:engineering/step-ledger-which-trigger-values-are-actually-recognised.md *(new)* | gideon | so basically A typo'd `epoch_end` went into a checkpoint record and sat there a week before anyone spotted it, nothing complained at write time. | `failure_behavior` |
| 2025-06-11 | page:engineering/finetuning-client-the-lr-schedule-helper-and-what-it-returns-outside-the-step-plan.md *(new)* | nils | bumped epochs on a resume before the plan grew and the helper handed a negative rate for the extra steps, nothing complained. those must not fall below the floor. | `exclusions_or_crossover` |
| 2025-06-12 | page:engineering/checkpointinfo-what-a-checkpoint-records-and-adding-to-it-safely.md *(new)* | emil | i've put a reasons field on the record with an empty default so the existing five-arg constructions still build; [f.name for f in fields(CheckpointInfo)] ends with it now. | `rule`, `observability` |
| 2025-06-17 | page:engineering/reading-the-per-step-ledger-from-a-finetuning-run.md *(new)* | gideon | After the ramp the rate is basically at the bottom within a couple steps tbh, it should be taking the whole rest of the run to get down there. | `rule` |
| 2025-06-24 | page:engineering/notes-on-resuming-a-finetuning-run-from-a-checkpoint.md *(new)* | dario | resumed from the checkpoint written at the end of epoch 1 and it replayed epoch 1 — the epoch stamped on that record and its batch count dont agree. | `exclusions_or_crossover` |
| 2025-06-24 | page:engineering/finetuning-client-config-validation-what-we-check-today-pr-653.md *(new)* | emil | honestly the 3 step smoke config has warmup sat at 10, so the whole thing trains at a crawl and never gets anywhere near the base rate. | `failure_behavior` |
| 2026-01-22 | #code-review *(new)* | konrad | Dropped the alphabetcial sorted(), ("epoch", "interval") read backwards from how we trigger. canonical_reasons now dedups and orders by CHECKPOINT_REASONS = ("interval", "epoch", "final"), anything else is a StepLedgerError. | `rule`, `failure_behavior` |

## g11.r1

**The hidden requirement:**

- **rule** — `CheckpointInfo` gains a last field `reasons: Tuple[str, ...] = ()`, and `save_checkpoint` gains a keyword-only `reasons: Sequence[str] = ("interval",)`. The vocabulary is exactly three strings held in a module constant `CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")` in `step_ledger.py`, and `canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]` deduplicates and orders them by that ledger order. A step that fires several triggers produces exactly one `save_checkpoint` call whose `reasons` is that canonical tuple. The stored `name` comes from `checkpoint_name(prefix, step)` = `CHECKPOINT_NAME_TEMPLATE.format(prefix=..., step=...)` with `CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"`: `checkpoint_name("checkpoint", 2) == "checkpoint-s000002"`.
- **scope** — The `"final"` trigger fires at `step == plan.total_steps` regardless of configuration. The `"interval"` and `"epoch"` triggers remain conditional on their config fields. Applies to `TinkerTrainer` only; `FireworksTrainer` writes no checkpoints and gains no reasons.
- **exclusions_or_crossover** — The `epoch` recorded on a checkpoint is `plan.epoch_of_batch(checkpoint.batches_completed)`, never the `for epoch in range(...)` loop variable. A checkpoint whose reasons include `"epoch"` for the end of epoch 1 therefore records `epoch == 2`.
- **failure_behavior** — `canonical_reasons` raises `StepLedgerError` on any string outside `CHECKPOINT_REASONS`. A repeat `save_checkpoint` under a name equal to the last entry of `self._checkpoints` replaces that entry in place — merging both reason tuples through `canonical_reasons` and taking the new `loss`: `save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))` then the same name with `loss=0.25, reasons=("final",)` leaves `len(trainer.get_checkpoints()) == 1`, `reasons == ("interval", "final")`, `loss == 0.25`.
- **observability** — For the end-to-end run (10 examples, `batch_size=3`, `epochs=2`, `gradient_accumulation_steps=3`, `checkpoint_every_n_steps=2`, `checkpoint_every_epoch=True`, `seed=0`): `[c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]`, `[c.reasons for c in result.checkpoints] == [("interval", "epoch"), ("epoch", "final")]`, and `[(c.step, c.epoch, c.batches_completed) for c in result.checkpoints] == [(2, 2, 6), (3, 2, 8)]`. `[f.name for f in dataclasses.fields(CheckpointInfo)]` ends `[..., "dataset_signature", "reasons"]` with length 10 and `CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()`. The default-config fixture of `tests/finetune/test_trainer.py:19-46` yields exactly one checkpoint, `"checkpoint-s000001"`, with `reasons == ("final",)`.

**Reversed earlier:** The team first wrote two independent checkpoints per coincident step with the existing `{prefix}_step_{n}` / `{prefix}_epoch_{n}` names and sorted the reason set alphabetically; both were reversed after a resume picked up the epoch-named twin and replayed a window.

**What a reader has to infer along the way:**

- *A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.*
  - nobody says: If one step produced duplicate rows and the fix is a field holding what fired, the several triggers have to arrive together in one write, ordered the way the constant lists them.
- *A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.*
  - nobody says: Two disagreeing name shapes plus an unpredictable name plus a bad sort all point at the same single formatting rule.
- *The step that closes a run always writes a checkpoint, tagged as the closing one, whatever the interval and per-epoch settings say; those two triggers stay tied to their config fields, and only the tinker trainer writes checkpoints at all.*
  - nobody says: A run that finishes with nothing on disk is a bug for the trainer that has checkpoints, and not a bug for the trainer that never had any.
- *The epoch recorded on a checkpoint is looked up from the global batch count it stopped at, never from the epoch loop variable, so a record written when epoch one's window closes reads as epoch two.*
  - nobody says: If the loop variable and the batch count disagree on the same record, only one of them can be authoritative, and it is the one resume also uses.
- *An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.*
  - nobody says: The same name appearing twice is the thing that made resume ambiguous, so the second write has to land on the first rather than beside it.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `CHECKPOINT_NAME_TEMPLATE`, `CHECKPOINT_REASONS`, `The`, `c.name`, `canonical_reasons`, `checkpoints`, `f.name`, `path`, `prefix`, `reasons`, `result.checkpoints`, `test_trainer.py`, `trainer.get_checkpoints`

> **Spread:** g11.r1.sc1: two remarks in #engineering within 10 days; g11.r1.sc3: two remarks in #engineering within 1 days

### The remarks, by the step they build

### g11.r1.sc1 — A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.

*Nobody says:* If one step produced duplicate rows and the fix is a field holding what fired, the several triggers have to arrive together in one write, ordered the way the constant lists them.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g11.r1.l3` — rule

**nikolai**, 2025-03-14, #engineering

> if a step is both an interval hit and an epoch close i want them back in the order the constant lists them sorting put final ahead of interval

*What a reader should take from it:* the team agrees coincident triggers come back in the constant's order, not alphabetical

*Step it builds toward:* `g11.r1.sc1` — A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.

*Drafted as:* if a step is both an interval hit and an epoch close, i want them back in the order the constant lists them; sorting put final ahead of interval.

*Why there:* None of the eight candidates is about the training-step ledger at all. They are PR-status chasing (#code-review 04-04, 05-07, 05-22, 05-30, 06-11), dormancy logistics (#general 06-02), commit scope and a missing plan doc (#engineering 2026-01-23), and the one that comes closest — #engineering 2025-04-08 — is a schema argument about failed_requests.jsonl fields for batch-failure debugging, a different record in a different subsystem; dropping trigger-ordering into it would read as a subject change nobody answers. The remark settles an ordering rule for coincident checkpoint triggers on a single step, which is training-loop design: #engineering is the room where that argument happens, and it needs a thread where someone has already noticed the ledger emitting the triggers sorted.

*Still leaves open:* Where the constant lives and how the several triggers get into one record in the first place.

*A new conversation in #engineering on 2025-03-14:*

```
```

#### `g11.r1.l1` — rule, observability

**nils**, 2025-03-24, #engineering

> ran [c.name for c in result.checkpoints] on the two-epoch run and got two rows for step 2, same loss, different names. so one step is definitely storing two records.

*What a reader should take from it:* the team agrees one step is producing more than one stored record

*Step it builds toward:* `g11.r1.sc1` — A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.

*Drafted as:* [c.name for c in result.checkpoints] on the two-epoch run gave me two rows for step 2, same loss, different names.

*Why there:* Neither candidate is in a room chewing on training runs. The 2025-03-19 #engineering day is entirely v0.1.21 release fallout, the throttle/estimation split, and Nils' Mistral api_key blocker; the 2025-03-25 #code-review day is PR triage — which PRs target the next release, WS-047 having no scope. A checkpoint ledger observation from a two-epoch run would change the subject in both and draw no reply. No listed room is the training room: #pipeline is the request layer, #cookbooks stops at the handoff into fine-tuning, #help is for pasting a traceback and asking why a backend misbehaves — this isn't a question, it's evidence for a dedup decision. #engineering is the catch-all for exactly this: a design argument about stored records that hasn't found a narrower channel. It wants its own short thread the day someone runs two epochs and sees the ledger double up, with Nils bringing the repro and a sibling settling what the surviving row carries.

*Still leaves open:* What the surviving single row should carry, and which words are allowed in it.

*Must appear literally:* `c.name`, `result.checkpoints`

*A new conversation in #engineering on 2025-03-24:*

```
```

> **Problems:** longer than one remark

#### `g11.r1.l2` — rule

**dermot**, 2025-04-09, thread:new|g11.r1.l2

> left a note on the diff — CHECKPOINT_REASONS wants to live next to the step-unit constants in the ledger module, and the trainer should stop typing those strings inline.

*What a reader should take from it:* the team agrees the allowed trigger words are a constant in the ledger module

*Step it builds toward:* `g11.r1.sc1` — A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.

*Drafted as:* left a note on the diff: CHECKPOINT_REASONS wants to live next to the step-unit constants, and the trainer should stop typing those strings inline.

*Why there:* None of the four mails is in a room where a diff is being read line by line. The Mar 14 mail is a private repro thread about concurrency and the semaphore; v0.1.21 is a broadcast release note with no review in it; the two weekly updates are status roll-ups (PR numbers, merge ordering, cost metadata gaps) where a pointed comment on one constant's placement would be a topic change nobody answers. The remark is a reviewer's note on a posted diff — it belongs in #code-review, in a thread where the trainer change that writes the reason strings inline has just gone up for eyes, which is also the only setting where dermot saying "left a note on the diff" makes sense to the people reading it.

*Still leaves open:* How many strings it holds, what they are, and what happens when a step trips several of them.

*Must appear literally:* `CHECKPOINT_REASONS`

*A new thread — **checkpoint reason on the trainer side — read before the cut?**, 2025-04-09:*

```
From: emil  To: dermot, gideon
Putting the trainer-side checkpoint diff up for eyes before we cut next week. It's the branch that adds a reason to every checkpoint we write — interval, manual, preempt, eval_improved, final — so the ledger rows stop being ambiguous when we go back and ask why a given step got saved.

Right now i'm writing the reason strings inline at each call site, which is the shape that fell out of doing it, not really a decision. resume path is the part i'd most like a second read on, since we now have to 

From: dermot  To: emil, gideon
read through it this afternoon, mostly good. two things.

first, on resume: leave old rows null. "interval" is a claim we can't actually support for anything written before this branch, and the ledger is the one place we should not be guessing retroactively. the reader can treat null as unknown, that's honest and it's cheap.

second, left a note on the diff: CHECKPOINT_REASONS wants to live next to the step-unit constants, and the trainer should stop typing those strings inline. same file, same 

From: gideon  To: dermot, emil
ya agree on null. we had exactly this with the old run ids where someone backfilled a plausible value and then two months later nobody could tell which ones were real.

so basically +1 from me on the diff otherwise, i only skimmed the resume test but it looked like it covers the missing-column case. i dunno if you also want a case for the column present but empty string, tbh that one bit us before somewhere else.

From: emil  To: dermot, gideon
sounds right, null it is. i'll add the empty-string case to the resume test while i'm in there, good catch.

will push the fixups tonight or tomorrow morning.

```

#### `g11.r1.l4` — rule, observability

**emil**, 2025-06-12, page:engineering/checkpointinfo-what-a-checkpoint-records-and-adding-to-it-safely.md

> i've put a reasons field on the record with an empty default so the existing five-arg constructions still build; [f.name for f in fields(CheckpointInfo)] ends with it now.

*What a reader should take from it:* the team agrees the checkpoint record carries a last, defaulted field naming why it fired

*Step it builds toward:* `g11.r1.sc1` — A step that trips more than one checkpoint trigger stores a single record that carries every trigger that fired, drawn from a fixed three-word vocabulary held in the ledger and handed back in that vocabulary's own order rather than sorted.

*Drafted as:* putting a reasons field on the record with an empty default so the five-arg builds still work; [f.name for f in fields(CheckpointInfo)] ends with it now.

*Why there:* Every listed candidate is either a release-notes page, a weekly-sync page, or a comment on the Docker-pinning / handover pages — none of them is chewing on the shape of a checkpoint record. The sync notes are status roll-ups (rate limits, issue 293, PR 685 stopping criterion), the release notes are changelog cuts, and the comment targets are about image tags and cost/cache reporting. A statement that a dataclass field was added with a defaulted trailing position, set up to be answered by a sibling remark about which strings are legal there and how they order, is live design talk on the resume path. It needs a room already arguing over the record's fields, which is #engineering, and none of the candidates stands in for that.

*Still leaves open:* What strings are legal in that field and how they get ordered.

*Must appear literally:* `reasons`, `f.name`

*A new page — **CheckpointInfo: what a checkpoint records, and adding to it safely** in `engineering`, 2025-06-12:*

> **Why this page exists**

> Resume work came off the back burner after the Jun 11 sync, and the first thing that came up — again — is that you cannot tell from a checkpoint *why* it was written. You can tell when, and you can tell how far along the run was, but the reason (dormancy window, operator stop, provider gave up on us, clean end of batch) isnt anywhere on the record.
> 
> So before anyone changes the resume path further, i wanted the shape of `CheckpointInfo` written down in one place, plus the rule for adding to it. Honestly this is mostly here so the next person doesnt have to grep for the constructor call sites like i did.

> **What CheckpointInfo carries today**

> As of 2025-06-12 the record is a frozen dataclass with five fields, in this order:
> 
> - `run_id` — the run this checkpoint belongs to
> - `path` — where the checkpoint blob itself lives on disk
> - `created_at` — write time, UTC
> - `requests_written` — count at the moment of the write
> - `responses_written` — same, for the response side
> 
> Two things worth knowing about how it gets built. First, the writer constructs it with keywords, which is fine. Second, there are a couple of older call sites (and the test fixtures, which is the part that bit us) that construct it *positionally*, all five args, no names. I believe that's historical rather than deliberate, but it's what's there right

> **Adding a field: the reasons case**

> The concrete change this week was recording why the checkpoint was written. Emil resolved it by putting a `reasons` field on the record with an empty default so the five-arg builds still work; `[f.name for f in fields(CheckpointInfo)] ends with it now`.
> 
> That pattern is the rule going forward, not just a one-off for this field: new fields go on the end, with a default, so existing positional construction keeps its meaning. If a field genuinely cannot have a sensible default then it doesnt go on this record without a migration for the callers first, and that's a bigger conversation than one PR.
> 
> Note that the default being empty means "nobody told us", not "clean shutdown" — a reader 

> **What isnt settled yet**

> - Whether the reason values should be a fixed vocabulary or free-form strings. Right now they're strings and nothing validates them. Not entirely sure which way we want this; a fixed set is nicer to branch on, free-form is nicer when something unexpected happens at 3am.
> - Whether old checkpoints on disk (written before this field existed) need anything done to them, or whether reading them back with the default is good enough. My guess is good enough, but i havent checked what the loader does with an unknown-shaped blob.
> - Nothing here changes the resume *behaviour* yet. This is metadata only — we're recording the reason, not acting on it.

> **If you're touching this record**

> Quick checklist before you open the PR:
> 
> 1. New field on the end, with a default. Don't reorder the existing five.
> 2. Grep for positional construction, including tests, and confirm it still means what it meant.
> 3. Say in the PR description what an absent/default value means for readers.
> 4. If you're adding something that a resume decision will branch on later, flag it — we need to be intentional here about which fields are advisory and which ones the loader is allowed to trust.

### g11.r1.sc2 — A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.

*Nobody says:* Two disagreeing name shapes plus an unpredictable name plus a bad sort all point at the same single formatting rule.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g11.r1.l5` — rule

**gideon**, 2025-03-17, #engineering

> honestly though, i sorted the checkpoint dir this morning and _step_10 came back before _step_9, wasted a minute thinking we'd droped one

*What a reader should take from it:* the team agrees the current checkpoint names sort wrong

*Step it builds toward:* `g11.r1.sc2` — A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.

*Drafted as:* Sorted the checkpoint dir and _step_10 came before _step_9, wasted a minute thinking we'd dropped one.

*Why there:* None of the candidate conversations are anywhere near checkpoint artifacts or training-step naming. The three #code-review days (03-14, 03-27, 04-04, 04-11, 04-14, 05-05) are PR triage and status chasing — PR numbers, review ownership, release state; a lexicographic-sort complaint about checkpoint directories has nothing to attach to there and would get no reply. #engineering 03-17 and #random 04-25 are both about model-name lists and the capability table — they share "names sorting/disagreeing" vocabulary but the subject is which models declare which capabilities, not on-disk artifact naming, so the remark would land as a topic change. What this needs is a conversation where someone is actually staring at a checkpoint directory during a fine-tuning handoff or resume and the team lands on "the current names sort wrong," with a separate person proposing the zero-padded scheme and picking it up. That's a half-formed tooling/convention argument, which is exactly what #engineering is the room for.

*Still leaves open:* What the replacement name looks like and who builds it.

*A new conversation in #engineering on 2025-03-17:*

```
```

#### `g11.r1.l8` — rule

**dermot**, 2025-04-09, thread:new|g11.r1.l8

> had to resume the late night run and it asked me for a checkpoint name, so i ended up grepping the log for it — nothing in the step tells you what it will be called.

*What a reader should take from it:* the team agrees today's checkpoint names cannot be worked out from the step

*Step it builds toward:* `g11.r1.sc2` — A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.

*Drafted as:* resume wanted a checkpoint name and i had to grep the log for it, because nothing about the step told me what it would be called.

*Why there:* All four candidates are mails about other subjects: two weekly status roundups (PR queues, merge ordering, cost metadata from provider backends), a release announcement for v0.1.21, and a one-off reply to emil about concurrency figures for an OOM verify. None of them is chewing on checkpoints or on what resume needs from you, and the closest phrase — "caching-and-resume have been stable" in the Apr 7 recap — is a line saying nothing is wrong there, so a complaint hung off it would arrive from nowhere and change the subject of dermot's own status mail. The remark also needs a room where somebody agrees with it, which a status monologue can't give it. Resume and checkpointing is squarely #pipeline's subject, and what should have existed is a short thread started the morning after a late-night rerun, where dermot reports that resume demanded a checkpoint name he could only recover by grepping the log, and emil/gideon confirm they've hit the same thing — leaving open what the derived name should actually look like.

*Still leaves open:* What the derived name should actually look like.

*A new thread — **overnight run — did it finish or not**, 2025-04-09:*

```
From: nikolai  To: dermot, emil, gideon
morning

checked the output dir before standup and the parquet is short by about a third of what i expected so either the run died or im looking at the wrong path

i need those completions today for the eval sweep so tell me now if im waiting on a rerun instead of a resume

also did anyone watch it overnight or did we all just go to bed

From: dermot  To: nikolai, emil, gideon   <-- the remark
we all went to bed, i think that is the honest answer.

the run did die, somewhere around 03:40 from what the log says — provider side, not ours, the connection went away mid-batch and nothing retried past the ceiling. i picked it back up this morning and it is going now, so you are waiting on a resume rather than a rerun. it should catch up by early afternoon at the current rate

the part that cost me the morning: resume wanted a checkpoint name and i had to grep the log for it, because nothing

From: gideon  To: dermot, nikolai, emil
oh ya i saw the same thing last week on the smaller run, thought it was just me doing something wrong so i didnt say anything, sorry

so basically i ended up just deleting everything and starting over because i couldnt figure out what to give it. honestly though i didnt even know grep the log was an option, i was looking in the metadata db the whole time

From: emil  To: dermot, gideon, nikolai
thanks for picking it up dermot. nikolai — early afternoon should still leave you room for the sweep i believe, but shout if it slips past 2 and we can cut the last shard.

gideon, don't apologise for that one, if two peopel hit it in a week its not a you problem. let me think through that before i file anything though, i'm not entirely sure yet whether its a docs gap or something that shoud be surfaced somewhere more visible.

```

> **Problems:** longer than one remark

#### `g11.r1.l6` — rule

**konrad**, 2025-05-07, thread:new|g11.r1.l6

> look, two places build the checkpoint name and they dissagree. one CHECKPOINT_NAME_TEMPLATE that takes the prefix and the step, and both call sites go through it.

*What a reader should take from it:* the team agrees one shared template builds the name from prefix and step

*Step it builds toward:* `g11.r1.sc2` — A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.

*Drafted as:* Two places build checkpoint names and they disagree; one CHECKPOINT_NAME_TEMPLATE taking the prefix and the step, and both call sites go through it.

*Why there:* All six candidates are Konrad's weekly status roundups — PR numbers, release cuts, examples/cookbooks, who owns what. None is chewing on training-checkpoint naming, and a settled implementation decision about a shared name-building constant dropped into a status email would read as a non-sequitur: those mails report state, they don't decide code shape. The thing this remark answers — two code paths constructing checkpoint names differently, and the team converging on one constant — is a design/duplication argument, which is what #engineering is for. It sits naturally alongside the finetuning client work (PR 653, Nikolai) in flight through late April and May, where a checkpoint dir written by one path and looked up by another would surface the disagreement.

*Still leaves open:* The exact shape of the string, including padding.

*Must appear literally:* `CHECKPOINT_NAME_TEMPLATE`, `prefix`

*A new thread — **PR 653 - resume run starts over instead of picking up the checkpoint**, 2025-05-07:*

```
From: nikolai  To: konrad, dario, emil
ran the finetuning client end to end overnight and the resume path is broken

trainer wrote the checkpoint out to one directory and the loader went looking somewhere else entirely so the resume found nothing and just started the run again from step 0 it didnt even error it just quietly began over

konrad you were on the 653 review can you look at where those two names actually get built i dont want to patch one side and have the same thing drift back in a month

nikolai

From: konrad  To: nikolai, dario, emil
Look, I went through this morning.

The resume logic itself is fine as far as I can tell. The problem is upstream of it. Two places build checkpoint names and they disagree; the trainer composes the directory inline in the save loop, and the loader composes it again inside its own lookup helper, and the step number is padded diffrently between the two. So they only agree by accident while the step count stays small, which is presumably why the smoke tests never caught it.

What we want is one CH

From: emil  To: konrad, nikolai, dario
so if I'm reading this right, the trainer and the loader have each been constructing that name independently since the original commit, and it worked up to now only because the two happened to produce the same string for single digit steps? that would explain the smoke tests, those runs never get anywhere near a step where the padding matters.

my one ask is timing. 0.1.24 went out on tuesday and I'd rather not have a resume fix trickle out as a patch release three days behind it, so if this can

From: dario  To: emil, konrad, nikolai
makes sense, inside 653 then.

the one thing i'd add, and it's actually the part of nikolai's run that bothers me most, is that it started over without saying anything. either the lookup finds the checkpoint or it complains loudly and stops. silently restarting a finetune is the kind of expensive that nobody notices until the invoice shows up. not blocking on it, just flagging while it's fresh in everyone's head.

april checkpoints i wouldn't worry about to be honest. in any case they were writt

```

#### `g11.r1.l7` — rule, observability

**dario**, 2025-06-11, page:engineering/checkpoint-naming-and-on-disk-layout-for-finetuning-runs.md

> honestly i just want step two to come out as checkpoint-s000002, six digits padded, so i can write the name down before the run gets there.

*What a reader should take from it:* the team agrees the name is the prefix, an s, and the step padded to six digits

*Step it builds toward:* `g11.r1.sc2` — A checkpoint's stored name is produced by one shared template from the configured prefix and the step number, zero-padded to a fixed width, so both call sites agree and the name is predictable before the run reaches it.

*Drafted as:* step two should come out as checkpoint-s000002, six digits padded, so i can write the name down before the run gets there.

*Why there:* None of the eight candidates is about checkpoints or training steps at all. The closest by vocabulary is the batch-job persistence page, but its "resume" is about submitted-vs-received batch requests keyed by request hash, not about a step-numbered checkpoint filename; dropping a naming decision there would change the subject under Emil's heading. The release/CI, Docker pinning, lint postmortem, handover, weekly notes, maintenance-mode and Jun 2 sync pages are all about PRs, gates and provider/cost surfaces. What should have existed is an #engineering page where the checkpoint filename format gets pinned down — prompted by the finetuning client work (PR 653) needing a stable name to reference a checkpoint before the run produces it, with Nikolai on the other side since that's his PR. That page would also cover where the name gets constructed today (the sibling remark's territory: two sites building it, one to survive) and what the ledger records per step, leaving this comment to fix only the format itself.

*Still leaves open:* That both existing name-building sites collapse into the one that produces this.

*Must appear literally:* `checkpoint-s000002`

*A new page — **checkpoint naming and on-disk layout for finetuning runs** in `engineering`, 2025-06-11:*

> **why this page exists**

> this came up off PR 653 (finetuning client, shreyas + nikolai). the client needs to hand back a reference to a checkpoint *before* the run has actually written it out — you want to return the path to the caller, or stick it in a manifest, at submit time rather than polling the directory afterwards and hoping.
> 
> and as far as i can tell nobody has written down anywhere what a checkpoint file is actually called, or which code path assembles the name. it's been treated as an implementation detail of the trainer, which is fine right up until something outside the trainer needs to predict it.
> 
> so this is that write-up. it is descriptive, not a proposal — i went and read the code and this i

> **where the name gets built**

> the name is assembled in the checkpoint writer, not in the trainer loop and not in the callback that triggers the save. the loop only decides *whether* to save on this step; it passes the step counter down and the writer does the formatting.
> 
> practical consequences of that:
> 
> - there is exactly one place the string is constructed. if we ever change the format, it's one edit.
> - the step counter the writer sees is the global step, not the within-epoch step. epoch boundaries do not reset it.
> - nothing downstream re-derives the name by globbing. the resume path reads the manifest, and the manifest holds the name the writer produced.
> 
> i think that last point is worth holding onto, 

> **the naming scheme**

> checkpoints are named off the global step, zero padded to six digits, with an `s` prefix on the number so the step is visually distinct from anything else in the path.
> 
> so step two should come out as `checkpoint-s000002`, six digits padded. the padding is the part that matters for callers — it's what lets you write the name down before the run gets there, rather than waiting to see what the trainer emits and matching on it.
> 
> a few notes on the edges:
> 
> - six digits covers up to step 999999. past that the name grows a digit rather than truncating, so sorting degrades but nothing collides. we are nowhere near this and honestly if we get there the padding width is the least of it.
> 

> **what's safe to depend on**

> for PR 653 and anything else that wants to name a checkpoint ahead of time:
> 
> - **safe**: the file name given a global step. it's a pure function of the step, no run id, no timestamp, no rank suffix in the single-node case.
> - **safe**: that the checkpoint the client asks about will either exist at that exact name or not exist at all. there's no rename-on-completion dance, the writer writes to a temp path and moves it into place, so a partially written checkpoint never appears under the real name.
> - **not safe**: that a checkpoint for a given step exists *at all*. save frequency, early stopping, and a crashed run all mean the step you named may never be reached. callers need a not-foun

> **open**

> - [ ] parent directory construction is duplicated between the config resolver and the writer. same result today, but nothing enforces it. worth collapsing, not urgent.
> - [ ] no test asserts the padding width. the format is exercised indirectly through the resume tests, which would still pass if the padding changed, since writer and reader would change together. a direct assertion on the name would be cheap.
> - [ ] multi-node: there is a rank suffix in the sharded path that i have not read carefully and am deliberately not documenting here rather than documenting it wrong.
> 
> in any case, for the PR 653 question specifically i think the above is enough to unblock. if the padding or prefi

### g11.r1.sc3 — The step that closes a run always writes a checkpoint, tagged as the closing one, whatever the interval and per-epoch settings say; those two triggers stay tied to their config fields, and only the tinker trainer writes checkpoints at all.

*Nobody says:* A run that finishes with nothing on disk is a bug for the trainer that has checkpoints, and not a bug for the trainer that never had any.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g11.r1.l11` — scope

**emil**, 2025-03-14, #code-review

> on fireworks there are no checkpoints written at all, one packed step per epoch and the job hands the weights back at the end, so nothing for us to tag on that side.

*What a reader should take from it:* the team agrees the fireworks trainer is outside all of this

*Step it builds toward:* `g11.r1.sc3` — The step that closes a run always writes a checkpoint, tagged as the closing one, whatever the interval and per-epoch settings say; those two triggers stay tied to their config fields, and only the tinker trainer writes checkpoints at all.

*Drafted as:* reminder that fireworks writes no checkpoints at all, one packed step per epoch and the job hands back weights at the end, so nothing to tag there.

*Why there:* Every listed candidate is about the request layer (batch ids, 429s, polling), a release cut, the viewer surface, or CI wiring for code-execution verifiers — none of them is chewing on trainer backends, run artifacts, or how anything gets tagged. The closest, #cookbooks 2026-01-02, only touches fine-tuning as a downstream handoff and its live questions are CI coverage and who owns the doc; a statement that the fireworks trainer writes no checkpoints would arrive from nowhere there and get no reaction. The natural home is #engineering, where design arguments live, right after Konrad starts drafting the fine-tuning handoff plan and has to say what each trainer backend actually emits at the end of a run and how it's identified — a thread where the fireworks and tinker sides get scoped separately.

*Still leaves open:* What the tinker side writes at the end of a run and how it is tagged.

*Must appear literally:* `checkpoints`

*A new conversation in #code-review on 2025-03-14:*

```
```

> **Problems:** longer than one remark

#### `g11.r1.l9` — scope, observability

**konrad**, 2025-03-19, #engineering

> The default-config fixture in test_trainer.py trains fine and leaves nothing behind, so I re-ran four minutes of it just to get a wieght file to poke at.

*What a reader should take from it:* the team agrees a default-config run currently finishes with no checkpoint at all

*Step it builds toward:* `g11.r1.sc3` — The step that closes a run always writes a checkpoint, tagged as the closing one, whatever the interval and per-epoch settings say; those two triggers stay tied to their config fields, and only the tinker trainer writes checkpoints at all.

*Drafted as:* The default-config fixture in test_trainer.py trained fine and left nothing behind, so I re-ran four minutes of it just to get a weight file.

*Why there:* The listed rooms are doing PR triage (code-review 05-30, 07-10), example-corpus readiness (cookbooks), release announcements (incidents) or download plumbing (viewer). None is chewing on trainer behaviour or on what a training run leaves on disk, so a test_trainer.py checkpoint finding would arrive from nowhere and draw no reply. It belongs in #engineering, the room for design arguments about training code, in the week Konrad is hands-on in the finetuning client ahead of PR 663 — with Nikolai present since the torch/trainer side is his, and the thread running on into what should be written at the end of a run and for which trainer.

*Still leaves open:* What should be written at the end instead, and for which trainer.

*Must appear literally:* `The`, `test_trainer.py`

*A new conversation in #engineering on 2025-03-19:*

```
```

#### `g11.r1.l10` — scope

**dermot**, 2025-03-20, #engineering

> mhm, the two every-n knobs can stay off if someone wants them off, that said the step that ends the run should write a checkpoint regardless of either setting.

*What a reader should take from it:* the team agrees the last step writes a checkpoint independent of the interval and epoch settings

*Step it builds toward:* `g11.r1.sc3` — The step that closes a run always writes a checkpoint, tagged as the closing one, whatever the interval and per-epoch settings say; those two triggers stay tied to their config fields, and only the tinker trainer writes checkpoints at all.

*Drafted as:* the two every-n knobs can stay off if someone wants them off, but the step that ends the run should leave a record behind regardless.

*Why there:* All eight candidates sit in the request/data layer — validator offline behaviour, a duplicated provider batch, cache fingerprints and job records, PR ordering, release notes, a structured-output override. None of them is discussing trainer checkpointing, so a claim about every-n save knobs would arrive from nowhere and get no reaction. #cookbooks only covers the handoff into fine-tuning, not training-code semantics, so the design argument belongs in #engineering, where half-formed plans and decisions that lack a narrower room already live.

*Still leaves open:* Which trainer this applies to, and how that record is tagged.

*A new conversation in #engineering on 2025-03-20:*

```
```

### g11.r1.sc4 — The epoch recorded on a checkpoint is looked up from the global batch count it stopped at, never from the epoch loop variable, so a record written when epoch one's window closes reads as epoch two.

*Nobody says:* If the loop variable and the batch count disagree on the same record, only one of them can be authoritative, and it is the one resume also uses.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g11.r1.l13` — exclusions_or_crossover

**nils**, 2025-03-17, #pipeline

> let me think — the epoch on a step record should come from asking the plan which epoch that batch ordinal landed in, not from whatever loop counter we're inside.

*What a reader should take from it:* the team agrees the recorded epoch is derived from the batch count, not the enclosing loop

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is looked up from the global batch count it stopped at, never from the epoch loop variable, so a record written when epoch one's window closes reads as epoch two.

*Drafted as:* stamp the epoch by asking the plan which epoch that batch ordinal landed in; the loop counter is not what the record should be carrying.

*Why there:* Both candidates are about provider batch submissions and PR traffic — #pipeline on 2025-03-17 is Mistral batch client token usage feeding cost accounting, and #code-review on 2025-03-24 is scheduling eyes on PR 583/584. Neither is chewing on what a step record's epoch field is derived from; "batch" there means a submitted provider batch, not a training minibatch ordinal, so the word overlap is exactly the trap. Epoch-vs-loop-counter in the step ledger is a training-loop design argument, which is #engineering's job — it has no narrower room in this list, and nils is the one already writing the ledger records.

*Still leaves open:* That this makes the epoch on some records read one higher than the loop was on.

*A new conversation in #pipeline on 2025-03-17:*

```
```

#### `g11.r1.l14` — exclusions_or_crossover, observability

**nikolai**, 2025-05-14, thread:new|g11.r1.l14

> heads up when a window spans the boundary the record closing epoch one reads epoch 2 thats the batch it stoped on so please dont fix it

*What a reader should take from it:* the team agrees a record closing epoch one legitimately reads epoch two

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is looked up from the global batch count it stopped at, never from the epoch loop variable, so a record written when epoch one's window closes reads as epoch two.

*Drafted as:* heads up, with a window spanning the boundary the record closing epoch one reads epoch 2, that is the batch it stopped on, please don't "fix" it.

*Why there:* Neither candidate thread is chewing on ledger/epoch-boundary semantics. The Jun 16 mail is a week recap about Dario's multimodal Gemini batch request fix, PRs 690/691, and whether PR 653 should be closed before maintenance mode — a status-and-scope thread where a claim about epoch fields on ledger records would change the subject and draw no reply. The Apr 16 mail is Nikolai's read of the docker backend before reviewing image pinning: backend_params, the read-only workspace, what the sandbox repo publishes. The only pull toward the recap mail is the word "batch", and there it means a provider batch submission, not a training batch. What is needed is the room where behavior gets argued and defended, at the moment someone reads the ledger row as a bug: an #engineering thread during resume testing of the step ledger, where Nikolai pre-empts the "fix" and states the value is intentional, with the separate question of where that epoch number is read from left to the person who owns that lookup.

*Still leaves open:* Where that number is looked up from in the first place.

*A new thread — **resume testing on the checkpoint ledger — three things**, 2025-05-14:*

```
From: konrad  To: nikolai, dario, emil
I spent yesterday evening on the resume path against the ledger from Friday's run. Two restarts, one from the middle of a epoch and one from a clean stop right on the boundary.

Two things are fine. Row counts line up on both, and request ids do not repeat after the resume, which was my main worry.

The third I do not understand. The window that closes out the first epoch has the epoch field written as 2. Every other row in that file is consistent with itself. Off the top of my head this reads l

From: nikolai  To: konrad, dario, emil   <-- the remark
right two of those are expected and one isnt

row counts and ids you can leave alone that path got reworked when the finetuning client landed and its been solid enough since so i wouldnt spend more time there

heads up with a window spanning the boundary the record closing epoch one reads epoch 2 that is the batch it stopped on please dont fix it we stamp a window with the epoch of the last batch in it not the first otherwise theres nothing in the row telling resume where to pick up from

on the

From: emil  To: nikolai, konrad, dario
So if I'm reading the second half of that right, a resume that dies halfway still leaves a row behind, and anything downstream counting rows believes we got further than we did? that's my guess at what you mean, tell me if I have it backwards.

Honestly if that's the shape of it we need to be intentional here rather than patching it quietly, because the viewer reads that file too and I don't want to find out about it from a user. Not entirely sure it needs to block anything this week though.

Ko

From: dario  To: emil, nikolai, konrad
mhm that tracks. i'd leave the append behaviour where it is until nikolai has had a look at it, changing it mid-week while people are resuming runs off it seems like the worse of the two options honestly

konrad thanks for actually running the boundary case, in any case that's the one nobody tests

```

#### `g11.r1.l12` — exclusions_or_crossover

**dario**, 2025-06-24, page:engineering/notes-on-resuming-a-finetuning-run-from-a-checkpoint.md

> resumed from the checkpoint written at the end of epoch 1 and it replayed epoch 1 — the epoch stamped on that record and its batch count dont agree.

*What a reader should take from it:* the team agrees the epoch stamped on a checkpoint contradicts the batches it had done

*Step it builds toward:* `g11.r1.sc4` — The epoch recorded on a checkpoint is looked up from the global batch count it stopped at, never from the epoch loop variable, so a record written when epoch one's window closes reads as epoch two.

*Drafted as:* resumed from the one written at the end of epoch 1 and it replayed epoch 1; the epoch on that record and its batch count disagree.

*Why there:* Every listed candidate is about the request layer or release logistics: provider batch jobs, cancellation, PR queues, cookbook lint. The one that mentions resume — the batch job status persistence page — is about which requests were submitted vs. answered across a process restart, keyed by request hash; it has no notion of epochs, checkpoints, or a training loop replaying work it already did. Dropping a remark about an epoch-stamped checkpoint disagreeing with its batch count into that page would read as a different subsystem's bug wandering in, and none of the others are even adjacent (the finetuning work shows up only as "PR 653, still in review"). What's missing is the place where the training-side ledger gets argued about: dario hits the replay himself on a resumed finetuning run, brings the record to #engineering because there's no narrower room for the training loop, and the thread then has to settle which of the two fields on the checkpoint is authoritative — the sibling remark's job, not this one's.

*Still leaves open:* Which of the two numbers is the one to keep.

*A new page — **notes on resuming a finetuning run from a checkpoint** in `engineering`, 2025-06-24:*

> **why this page**

> i've now been asked three separate times this month what the right way is to pick a finetuning run back up after it dies, and each time i've answered it in a thread that then scrolls away. so this is the write up. it is not a spec, it's just what i actually do and what i've seen go wrong.
> 
> scope is the finetuning client as it stands on 2025-06-24. some of this will change once 653 lands properly, i'll revisit then.

> **what's actually in a checkpoint record**

> the checkpoint the client drops is a small json record next to the weights. the fields that matter for resuming:
> 
> - `epoch` — which epoch the writer believed it was in when it wrote the record
> - `batches_seen` (the batch count) — cumulative, across the whole run, not per epoch
> - `optimizer_state` path
> - a timestamp, which is wall clock and not useful for ordering if two workers wrote at once
> 
> worth knowing that the record is written at two different moments in the code: at the end of an epoch, and also on the periodic interval. those two writers do not agree about what `epoch` means, which is the thing that bit me below. i think that's the actual bug rather than anything in the

> **the resume procedure**

> 1. find the newest checkpoint dir under the run's output path. do this by name/step, not by mtime.
> 2. read the record and eyeball `epoch` against `batches_seen` before you do anything else. cross multiply against your batches-per-epoch — they should agree. if they don't, see below.
> 3. point the client at the checkpoint dir and re-launch with the same config. the config is not stored in the record, so if you changed batch size between runs the batch count is meaningless and honestly you should just start over.
> 4. watch the first hundred steps or so of logging and confirm the loss picks up roughly where it left off rather than at the epoch-0 value.
> 
> step 4 sounds paranoid but it's th

> **epoch replay, and the record disagreeing with itself**

> hit this yesterday while working through PR 653. i resumed from the one written at the end of epoch 1 and it replayed epoch 1; the epoch on that record and its batch count disagree. so it isn't just that the resume logic is off by one somewhere, the record itself is telling two different stories about where the run was — the epoch field says one thing and the number of batches says another.
> 
> cost me an epoch of compute, which for the sizes we're running at is annoying but not fatal. if you see the same thing: trust the batch count over the epoch field, since the batch count is a cumulative counter that only ever increments and the epoch field is set by whichever writer got there last. to

> **open / not doing before v0.1.26**

> - reconciling the two checkpoint writers so `epoch` and the batch count can't disagree. not in scope for v0.1.26, and i'd rather it went in with 653 than as a separate change on top.
> - storing the run config alongside the record so a resume can refuse a mismatched batch size instead of silently producing nonsense. same story, after.
> - nobody owns either of these yet. shreyas and nikolai are closest to 653, i'll raise it at the next sync rather than assigning it here.

### g11.r1.sc5 — An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.

*Nobody says:* The same name appearing twice is the thing that made resume ambiguous, so the second write has to land on the first rather than beside it.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g11.r1.l17` — failure_behavior, observability

**nils**, 2025-03-19, #pipeline

> let me think through that - trainer.get_checkpoints() handed me two rows with the same name and the same path, different loss on each, and whichever one resume grabs is a coin flip

*What a reader should take from it:* the team agrees repeat writes under one name currently produce two rows

*Step it builds toward:* `g11.r1.sc5` — An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.

*Drafted as:* trainer.get_checkpoints() handed me two rows with the same name and the same path, different loss on each, and whichever one resume grabs is a coin flip.

*Why there:* Neither candidate is on this subject. 2025-03-19 #engineering is v0.1.21 release notes, the throttle-path check after the output-token fix, and Nils's api_key decision on PR 584 — a checkpoint-ledger dedup bug would change the subject mid-thread and get no reply. 2025-03-25 #code-review is pure PR triage (584/585/579 targeting, 468/565 deferred, WS-047 missing) and that room is for "please look at my PR," not for establishing that repeat writes produce two rows. The remark needs a room already arguing about ledger write semantics: #engineering is where design arguments live when they haven't found a narrower channel. #pipeline's "resume" is the request layer, not the trainer's checkpoints, and #cookbooks owns the fine-tuning handoff rather than the ledger's data model.

*Still leaves open:* What the single surviving row should end up holding.

*Must appear literally:* `trainer.get_checkpoints`, `path`

*A new conversation in #pipeline on 2025-03-19:*

```
```

> **Problems:** longer than one remark

#### `g11.r1.l16` — failure_behavior

**dermot**, 2025-04-09, thread:new|g11.r1.l16

> yeah — canonical_reasons should raise on anything outside the list, same error type the rest of the ledger raises, rather than quietly passing it through.

*What a reader should take from it:* the team agrees an out-of-vocabulary string raises the ledger's error

*Step it builds toward:* `g11.r1.sc5` — An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.

*Drafted as:* canonical_reasons should throw on anything outside the list, same error type as the rest of the ledger, rather than quietly passing it through.

*Why there:* None of the four candidates is anywhere near this subject. Two are weekly status recaps (PR lists, merge ordering, cost metadata across backends), one is a v0.1.21 release announcement about unicode corruption and token-count wrapping, and one is Dermot telling Emil how to structure a concurrency/OOM verify. A ruling on what `canonical_reasons` does with an out-of-vocabulary string is a contract decision about a ledger helper — it would land in a thread where somebody is actually drafting or reviewing that function and asking what the unknown-string and repeat-name cases should do. Dropped into a weekly update it changes the subject and gets no reply; dropped into the release mail it is a fix nobody announced. What should have existed is a short #engineering thread on the shape of `canonical_reasons` — Emil (or whoever is writing it) laying out the two open questions, Dermot answering the validation one and someone else taking the duplicate-name one.

*Still leaves open:* The other thing that function has to do when the same name comes round twice.

*Must appear literally:* `canonical_reasons`

*A new thread — **reason codes on the step ledger — two cases I can't call alone**, 2025-04-09:*

```
From: emil  To: dermot, dario
Morning both,

I'm most of the way through the reason-code helper for the step ledger and there are two cases I don't want to decide on my own, since whatever we pick here is going to be baked into every ledger row we write from here on.

First: what do we do with a reason string that isn't in the vocabulary at all. Right now it just goes through untouched, which honestly feels wrong but I can see the argument for being permissive while the list is still settling.

Second: what happens when the 

From: dermot  To: emil, dario   <-- the remark
yeah, both of these need to be settled before it lands, agreed.

on the first one: canonical_reasons should throw on anything outside the list, same error type as the rest of the ledger, rather than quietly passing it through. permissive-while-settling sounds reasonable until you have six months of rows with three spellings of the same thing in them and no way to tell which was intended, and we get to write the migration.

on the second, i'd separate the two questions you've folded together. ded

From: dario  To: dermot, emil
mhm, that tracks. i've been on the receiving end of the three-spellings thing on the metadata side and it is not a fun afternoon.

on the duplicate question — is the actual case here a caller passing the same reason twice by mistake, or a step genuinely hitting the same condition more than once? because those want different answers i think. the first is a bug and should be loud, the second is just a count and there's nothing wrong with it. actually if we can't tell them apart from inside the hel

From: emil  To: dario, dermot
yup, that helps. It's the second one in practice — the step can legitimately hit retryable twice — so I'll keep the sequence and leave the collapsing to whoever is doing the counting.

Will push the branch tomorrow morning, I'll tag you both on it. thanks for the quick turnaround.

```

#### `g11.r1.l18` — failure_behavior

**dario**, 2025-05-14, page:engineering/training-step-ledger-append-and-update-rules.md

> if the name matches the last one we appended, we update that entry in place, newer loss wins and both tag sets folded together, no second row.

*What a reader should take from it:* the team agrees a repeat write under the last stored name replaces it, merging tags and taking the new loss

*Step it builds toward:* `g11.r1.sc5` — An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.

*Drafted as:* if the name matches the one we just appended, update that entry in place with the newer loss and both tag sets folded together, don't add a second.

*Why there:* Every listed candidate lives in the bulk-inference world: image pinning, CI/release process, dormancy PR triage, batch-mode status, and the responses-file/metadata-db split. None of them has a ledger of named steps carrying a loss value and tag sets, so a line settling "repeat write under the last stored name replaces it, merging tags, newer loss wins" would arrive from nowhere in all of them. The closest by shape is the batch-persistence page, but its append-only store is keyed by request hash and holds responses, not losses or tags — landing an update-in-place rule there would quietly rewrite what that page says about append-only cache state, which is worse than not fitting. What should have existed is a short engineering doc where dario writes down the ledger's write semantics while the code is open (his habit on the WS-055 and batch-persistence pages), prompted by a step being re-recorded after a rerun and showing up twice with different tags. The same doc is where the sibling question — what counts as a legal tag set — gets argued, so this line reads as one of two decisions being nailed down rather than a lone observation.

*Still leaves open:* What makes a tag set legal in the first place.

*A new page — **training step ledger: append and update rules** in `engineering`, 2025-05-14:*

> **why this is written down**

> on the 13th a chunk of the sweep got re-run after the node came back, and the steps that re-ran got re-recorded into the same ledger. what we ended up with was two entries under the same name, one from the original pass and one from the rerun, each carrying a different tag set.
> 
> nothing errored. the ledger happily took both. what broke was everything downstream that reads it, the step count was off by the number of re-run steps, and the loss curve had a step in it that looked like a regression but was actually just the older entry still sitting there next to the newer one.
> 
> there are two or three things being built on top of the ledger right now, so i'd rather have the append and upd

> **what an entry is**

> an entry is three fields, and the shape has not changed:
> 
> - **name** — string, identifies the step. this is the key. everything in the next section follows from treating it as the key
> - **loss** — the recorded loss for that step
> - **tags** — a set of strings. unordered, no duplicates, and the ledger does not care what's in them
> 
> the ledger preserves insertion order. it is a ledger, not a dict, and the order entries went in is meaningful to the readers, so it's worth being explicit that we keep it.

> **appending a step**

> before an append goes in, compare the incoming name against the entry at the end of the ledger. if the name matches the one we just appended, update that entry in place with the newer loss and both tag sets folded together, don't add a second.
> 
> the two halves of that, spelled out, because they are not the same rule:
> 
> - **loss** — the newer value wins outright. we are not averaging, we are not keeping the lower one. the rerun is the more recent observation and that is the one we want
> - **tags** — union of the old set and the new set. nothing that was on the older entry gets dropped just because the rerun didn't re-emit it. tags get attached from a few different places and honestly n

> **what the readers assume**

> the summary path reads the ledger and produces the step count, the best (lowest) loss seen, and a rollup of all tags across entries. each of those broke in its own way last week, which is a decent illustration of why the rule above is where it is:
> 
> - the count double counted the re-run steps
> - best-loss was fine by luck, it happened to pick the newer entry, but only because the rerun was lower. it could have gone the other way
> - the tag rollup was actually correct, since it unions over everything anyway. that's part of why this sat unnoticed for a day
> 
> so: readers may assume that no two adjacent entries share a name. they may not assume much more than that yet, see below.

> **what this doesn't cover**

> being clear about the edges so nobody reads more into the rule than is there:
> 
> - **a name reappearing later, not adjacent.** if step_41 shows up at position 3 and again at position 30, that appends, it does not merge. i think that's the best we can do right now, since a rerun in practice immediately follows the thing it re-runs, and doing a full scan on every append is a cost we haven't measured. if that assumption stops holding we revisit it
> - **removing a tag.** there is no way to unset a tag through an append, the fold is a union and only ever grows. deliberate for the moment, nobody has asked for removal
> - **whether name should be a hard unique key across the whole ledger, or sta

#### `g11.r1.l15` — failure_behavior

**gideon**, 2025-06-11, page:engineering/step-ledger-which-trigger-values-are-actually-recognised.md

> so basically A typo'd `epoch_end` went into a checkpoint record and sat there a week before anyone spotted it, nothing complained at write time.

*What a reader should take from it:* the team agrees an unrecognised trigger string is stored today with no complaint

*Step it builds toward:* `g11.r1.sc5` — An unrecognised trigger string is rejected with the ledger's own error rather than stored, and a second write under the name of the record just stored updates that record in place, merging the trigger sets and taking the newer loss instead of appending a twin.

*Drafted as:* A typo'd 'epoch_end' went into a checkpoint record and sat there a week before anyone spotted it, nothing complained at write time.

*Why there:* None of the listed places is about checkpoint records or trigger strings. The closest on validation-shaped subject matter is the Docker image pinning page, but that's about image tags and create-time failure for the code executor, not about what gets written into a checkpoint record — dropping a training-checkpoint anecdote there would change the subject under someone else's heading. The weekly notes and release notes are PR/issue status roundups with no thread this attaches to. What should have existed is an engineering doc on what the checkpoint ledger accepts as a trigger value: the page would list the recognised triggers, note nothing validates the field on write, and leave the question of what to do with an unknown string open — Gideon's typo story is exactly the "here's why this matters" comment on that page, and he's the one who owns enough of the status/reporting surface to have hit it.

*Still leaves open:* What should happen instead when an unknown string turns up.

*Must appear literally:* `A`

*A new page — **Step ledger: which trigger values are actually recognised** in `engineering`, 2025-06-11:*

> **Why i am writing this down**

> Nolan asked me on monday what trigger string to use for the new preemption checkpoints, and i went looking and there is no list anywhere. Not in the docstring, not in the schema, nothing. So basically i read the writer and the reader side by side this morning and wrote down what i found.
> 
> This is a description of what the code does today (as of v0.1.25 + main), not a proposal. If we want to change any of it that is a separate conversation, probably with Dario since he owns the resume path.

> **What the reader recognises**

> The resume/replay side switches on `record.trigger` and only these five strings do anything:
> 
> - `step_interval` - the ordinary every-N-steps checkpoint. This is the one the resume logic prefers when it picks a restart point.
> - `epoch_end` - written by the epoch loop. Also eligible for resume.
> - `eval_improved` - written when the eval metric beats the previous best. Kept forever by the retention pass, never pruned.
> - `manual` - someone called the save hook by hand. Eligible for resume, exempt from retention.
> - `final` - end of run. Eligible for resume, exempt from retention.
> 
> Anything that is not one of those five lands in the unknown bucket. Unknown records are still parsed, 

> **What the writer will accept**

> The writer does no validation of `trigger` whatsoever. It takes whatever string the caller passes, puts it in the record, appends the line, done. There is no enum, no membership check, no warning.
> 
> A typo'd 'epoch_end' went into a checkpoint record and sat there a week before anyone spotted it, nothing complained at write time. It was only noticed because a resume picked an older step than expected and someone went digging in the ledger by hand.
> 
> So the practical shape of it is: the write path is permissive and silent, the read path is strict and silent. Neither side tells you anything, and the failure shows up later as a resume choosing the wrong record or retention deleting somethi

> **Adding a new trigger**

> If you need a new one (preemption is the live example), it is two places, both required:
> 
> 1. Add the string to the recognised set in the reader.
> 2. Decide and write down whether it is resume-eligible and whether retention may prune it. There is no default that gets applied for you - an unlisted trigger is effectively "not resumable, prunable", which is almost never what the person adding it wanted.
> 
> Then add it to the list in the section above so the next person does not have to read the source like i just did.
> 
> For the preemption case specifically i would expect resume-eligible yes, prunable yes, but tbh that is Nolan's call not mine, i am just recording the shape of the decis

> **Things i did not settle**

> - Whether the writer should reject unknown triggers outright, or log and accept. i dunno which, there are arguments both ways and it changes behaviour for anything already written.
> - What to do about ledgers that already contain unrecognised triggers. There is at least the one from the typo. Nobody has looked for others.
> - The `ls` subcommand shows unknown records the same as known ones with no marker. Small thing, but it is why the typo survived a week.
> 
> None of these are blocking the preemption work, they just want an owner at some point.

### Herrings — believed at the time, overturned later

#### `g11.r1.g11-r1-prior-a` — herring

**dario**, 2025-01-21, #code-review

> ok, settled - a step that's both an interval hit and an epoch boundary writes two checkpoints, `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, the two names we already have, unchanged.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled: a step that is both an interval and an epoch boundary writes two checkpoints, `{prefix}_step_{n}` and `{prefix}_epoch_{n}`. the two names we already have, unchanged.

*Why there:* None of the eight candidates is anywhere near checkpointing. They're about PR routing and `supports_structured_output` (03-10), cookbook confirmation for the multimodal landing (02-13), where `CURATOR_CACHE_DIR` gets resolved and the first metadata-DB write (02-26), deepseek int wrapping and mime_type threading (03-07), cost-estimate dedup on prompt content (01-29), PR 430 and the handover doc (02-04), v0.1.16 throughput scope (01-23), and who reviews PR 515/516 (02-18). Dropping a settled checkpoint-naming decision into any of them changes the subject and would land with no reaction — nobody in those rooms has raised a save cadence, an epoch boundary, or a `{prefix}_` name shape. #cookbooks touches fine-tuning only as the handoff out of a curated dataset, not the training loop's own writer; the argument about what a training run writes to disk is a design argument with no narrower channel, so it belongs in #engineering. The conversation that should have existed: someone hits an interval save landing on the last step of an epoch and asks whether the epoch write clobbers the step write, dario rules on it after the back-and-forth.

*A new conversation in #code-review on 2025-01-21:*

```
```

#### `g11.r1.g11-r1-prior-b` — herring

**konrad**, 2025-01-22, #code-review

> Look, the reason set is just plain sorted(), alphabetical - a step thats both gives you ("epoch", "interval"). No custom ordering to maintain.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Reason sets are sorted alphabetically — plain sorted(), so a step that's both gives you ("epoch", "interval"). No custom ordering to maintain.

*Why there:* None of the listed conversations is anywhere near this subject. They are about PR triage and reviewer assignment (Jan 22, Jan 27, Feb 17, Mar 12), ws-028 throttling and the GC leak postmortem (Feb 7), sandbox uid behavior and the cost-estimation revamp (Feb 26), multimodal/batch suite and cookbook confirmation (Feb 13), and Gemini rate-limit issue triage (Mar 3). Checkpoint reasons and their ordering in the training step ledger are not live in any of them, so the remark would arrive from nowhere, change the subject, and draw no reply — and it would be Konrad answering a question nobody asked. The right home is #engineering: it is the room for design detail on a subsystem that has no narrower channel (the ledger is not the request layer, not examples, not release coordination), and this is exactly the kind of "we settled the ordering, here is what it is" note that room carries. It wants a short thread where someone building against the ledger asks what comes back when a step is both an epoch boundary and an interval checkpoint, and Konrad answers.

*A new conversation in #code-review on 2025-01-22:*

```
```

#### `g11.r1.rev1` — rule, scope

**dario**, 2025-03-17, #code-review

> dropped the two-records-per-step thing, {prefix}_step_{n} and {prefix}_epoch_{n} are both gone — resume picked up the epoch-named twin and replayed a window. one save_checkpoint now, name from checkpoint_name(prefix, step), reasons ("interval", "epoch")

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* dropped the two-records-per-step thing — {prefix}_step_{n} and {prefix}_epoch_{n} are gone. resume picked up the epoch-named twin and replayed a window. one save_checkpoint now, name from checkpoint_name(prefix, step), reasons ("interval", "epoch").

*Why there:* Every listed conversation lives in the inference/data-generation half of the product: batch job ids surviving a reboot, cache-key and cache-dir behaviour, provider backends, an examples-table taxonomy. This remark is about a training loop's checkpoint ledger — per-step vs per-epoch records, a resume that replayed a window of steps, a save_checkpoint call and checkpoint_name(prefix, step). Nobody in these rooms is talking about training steps or epochs, so it would land as a subject change with no one to answer it. #pipeline is the closest by the word "resume", but its resume is batch-submission reattachment, not optimizer state; #cookbooks only touches fine-tuning at the dataset handoff, not the training code. #engineering is the room the design argument would have happened in — it is explicitly the catch-all for work that hasn't found a narrower channel, and dario is already the one there reporting what he's landing that day.

*Must appear literally:* `{prefix}_step_{n}`, `{prefix}_epoch_{n}`, `save_checkpoint`, `checkpoint_name(prefix, step)`

*A new conversation in #code-review on 2025-03-17:*

```
```

> **Problems:** longer than one remark

#### `g11.r1.rev2` — rule, failure_behavior

**konrad**, 2026-01-22, #code-review

> Dropped the alphabetcial sorted(), ("epoch", "interval") read backwards from how we trigger. canonical_reasons now dedups and orders by CHECKPOINT_REASONS = ("interval", "epoch", "final"), anything else is a StepLedgerError.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* Alphabetical sorted() on the reason set is gone — ("epoch", "interval") read backwards from how we trigger. canonical_reasons now dedups and orders by CHECKPOINT_REASONS = ("interval", "epoch", "final") and raises StepLedgerError on anything else.

*Why there:* None of the listed conversations are anywhere near this. The two finetuning-adjacent ones are about something else entirely — 2026-01-23 in #code-review is Claude 4.x/3.7 model identifier strings in PR 704, and 2025-12-30 in #engineering is red CI and the dormancy wind-down. Nothing in any candidate day is chewing on checkpoint bookkeeping, reason ordering, or a step-ledger error type, so this would land as a subject change nobody answers. What it actually is is a "pushed the fix, here's what changed" reply to a review note about the reason set being sorted alphabetically, which needs a #code-review thread on the step ledger PR that the corpus doesn't have. Konrad is the right author — he owns the finetuning subsystem and Nikolai is his usual reviewer there — it just needs the day where that review comment was left.

*Must appear literally:* `sorted()`, `canonical_reasons`, `CHECKPOINT_REASONS`, `StepLedgerError`

*A new conversation in #code-review on 2026-01-22:*

```
```


## g11.r2

**The hidden requirement:**

- **rule** — `learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio: float = MIN_LR_RATIO) -> float` where `MIN_LR_RATIO: float = 0.1` is a module constant of `step_ledger.py`. With `effective_warmup = min(warmup_steps, total_steps)`, for `1 <= step <= effective_warmup` the rate is `base_lr * step / effective_warmup`. After warmup the rate decays: `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)` and `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)`.
- **exclusions_or_crossover** — Beyond the end of the run the rate is clamped at the floor and does not fall below it or go negative: `learning_rate_at(99, 8, 1e-4, 2) == pytest.approx(1e-05)`. A resumed run whose `epochs` grew continues down the new, longer schedule from `completed_steps + 1` using the same function.
- **failure_behavior** — `warmup_steps` greater than `total_steps` is clipped to the run length rather than raising: `[learning_rate_at(s, 3, 1e-4, 10) for s in range(1, 4)] == pytest.approx([1e-4/3, 2e-4/3, 1e-04], rel=1e-12)` — ending exactly at `base_lr`.
- **observability** — `[learning_rate_at(s, 8, 1e-4, 2) for s in range(1, 9)] == pytest.approx([5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], rel=1e-12)`; `[learning_rate_at(s, 4, 1e-4, 0) for s in range(1, 5)] == pytest.approx([7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12)`. In the end-to-end run the three optimizer steps carry `5e-05`, `1e-04`, `1e-05`, and those are the values pushed on `TrainingStats.learning_rate` for the batches of each window.

**Reversed earlier:** An earlier revision decayed to zero over the run and used the exclusive `step < warmup_steps` comparison that `tinker_trainer.py:548` still shows; both were reversed after the last steps of long runs stopped moving and the first step trained at rate 0.

**What a reader has to infer along the way:**

- *During warmup the rate rises by an equal share of the base rate per step starting at the first step, and the step at which warmup ends is the one carrying the full base rate.*
  - nobody says: If each of the N warmup steps adds one Nth of the base rate and the first step already gets its share, then step N is at the full rate and no step is ever at zero.
- *Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.*
  - nobody says: A descent that is stretched across the steps remaining after warmup and is required to be at its lowest on the last step is a straight line from base rate to floor, so the slope is fixed by the run length.
- *The floor is a named module-level default that a caller can override per call, and any step asked for beyond the end of the run returns that floor instead of continuing downward; a resume that only lengthens the run keeps descending the longer schedule from where it stopped.*
  - nobody says: If the descent is pinned to the run length, then a step past the end can only be handled by holding the last value, and a longer run simply recomputes the same line.
- *A warmup longer than the run is trimmed to the run's length instead of being rejected, so such a run finishes exactly at the base rate.*
  - nobody says: Trimming the warmup to the run length means the last step of the run is also the last warmup step, and by the warmup rule that step is at the full base rate.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `After`, `MIN_LR_RATIO`, `min_lr_ratio`, `rel`

> **Spread:** g11.r2.S1: two remarks in #pipeline within 3 days; : two remarks in #releases within 5 days

### The remarks, by the step they build

### g11.r2.S1 — During warmup the rate rises by an equal share of the base rate per step starting at the first step, and the step at which warmup ends is the one carrying the full base rate.

*Nobody says:* If each of the N warmup steps adds one Nth of the base rate and the first step already gets its share, then step N is at the full rate and no step is ever at zero.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g11.r2.L1` — rule

**dermot**, 2025-03-21, #pipeline

> step 1 logs a learning rate of 0.0 on every run i've looked at, so the first optimizer step moves nothing. agreed it can't stay zero at step 1.

*What a reader should take from it:* the team agrees the first step of a run must not train at zero

*Step it builds toward:* `g11.r2.S1` — During warmup the rate rises by an equal share of the base rate per step starting at the first step, and the step at which warmup ends is the one carrying the full base rate.

*Drafted as:* step 1 logs a learning rate of 0.0 on every run i've looked at, so the first optimizer step moves nothing at all.

*Why there:* Every listed candidate is about the request layer, release coordination, or CI hygiene — batch ids, cache fingerprints, streaming retries, sandbox tags, version bumps. None of them is chewing on training code, so a learning-rate-at-step-1 report would arrive from nowhere and get no reaction; the only adjacent mention is konrad's "finetuning side is clear" in #releases 05-02, which is about whether PRs blocking v0.1.24 landed, not about how a run warms up. #engineering is the room the list names for design arguments that haven't found a narrower channel, and the finetuning handoff has no channel of its own, so the warmup discussion belongs there with dermot (who reads the logs), konrad (owns finetuning), and gideon (the one who always asks whether anyone actually checked).

*Still leaves open:* what the ramp should look like instead, and which step ends up at the full base rate

*A new conversation in #pipeline on 2025-03-21:*

```
```

> **Problems:** longer than one remark

#### `g11.r2.L3` — rule, observability

**gideon**, 2025-03-24, #pipeline

> so basically we set warmup_steps=2 and then step 2 is alredy on its way down - the step where warmup ends should be the one sitting at full base rate.

*What a reader should take from it:* the team agrees the final warmup step carries the base rate

*Step it builds toward:* `g11.r2.S1` — During warmup the rate rises by an equal share of the base rate per step starting at the first step, and the step at which warmup ends is the one carrying the full base rate.

*Drafted as:* We say warmup_steps=2 and then step 2 is already on its way down; the step where warmup ends is the one that should be at full rate.

*Why there:* Every listed conversation is about the inference/serving side — provider capability checks, PR state, batch response shapes, the viewer's metadata panel, a structured-output revert. None of them is chewing on training code, and an off-by-one in a learning-rate warmup ramp would land as a subject change with no one to answer it. #random on 4-25 is model-name lists, #engineering on 4-17 is a landing-list triage, #engineering on 3-19 is throttle/cost accounting from a postmortem — close in vocabulary ("rate", "steps") but not in subject. The remark is a scheduler-semantics design argument, so it belongs in #engineering, the room for design arguments that haven't found a narrower channel: a fine-tune run's logged LR curve showing the ramp peaking a step early, with Gideon making the call that the final warmup step carries the base rate and someone else covering the shape before and after.

*Still leaves open:* what the rate does on the steps before that one, and what happens once the ramp is finished

*Must appear literally:* `warmup_steps`

*A new conversation in #pipeline on 2025-03-24:*

```
```

#### `g11.r2.L2` — rule

**nils**, 2025-06-10, page:engineering/rate-limiter-warmup-ramp-shape-and-defaults.md

> let me think through the ramp shape — warmup should climb in even shares of the base rate, one share per step, and the first step gets a full share like every other one.

*What a reader should take from it:* the team agrees warmup rises in equal per-step increments from step one

*Step it builds toward:* `g11.r2.S1` — During warmup the rate rises by an equal share of the base rate per step starting at the first step, and the step at which warmup ends is the one carrying the full base rate.

*Drafted as:* warmup should walk up in even shares of the base rate, one share per step, and the very first step gets a share like the rest.

*Why there:* The remark settles the shape of the rate-limiter warmup ramp — even per-step increments of the base rate, starting at step one. That is request-layer rate limit mechanics, which is #pipeline's subject. None of the candidates is chewing on it: the Jun 9 sync only records that auto-detect rate limit work (207/233) was deferred past dormancy, so a settled decision about increment shape landing as a comment there reads against the page rather than with it; the Jun 2 sync is release/CI and the 685 stopping criterion; the handover and v0.1.22 notes only name 207/233 as open, they don't discuss ramp behaviour; and the docker pinning, batch persistence, WS-055 and lint postmortem pages are unrelated subsystems. What should have existed is a short #pipeline design page on the warmup ramp — nils writing up the ramp schedule after runs kept tripping provider limits in the first seconds because the limiter opened at full rate, with dario and emil weighing in on step count and where the ramp terminates. The sibling question (does the last warmup step sit at the base rate or just under it) is exactly the kind of thing that thread would still be arguing about underneath this line.

*Still leaves open:* where the walk stops, i.e. whether the last warmup step sits at the full rate or just short of it

*A new page — **Rate limiter warmup ramp: shape and defaults** in `engineering`, 2025-06-10:*

> **Why this note exists**

> At the Jun 9 sync the team agreed to defer the auto-detect rate limits work (issues 207 and 233) to post-dormancy. That was the right call for the milestone — but deferring detection does not defer the symptom.
> 
> We are still seeing runs trip provider limits inside the first few seconds. The cause is separate from detection: the limiter opens at its full configured rate the moment the run starts, so a large request set hits the provider at full width before anything has come back. Providers that measure over a short window read that as a burst and 429 us.
> 
> So the warmup ramp needs a shape written down on its own, independent of 207/233. This note records the shape. It is not a proposa

> **What happens today at run start**

> - The limiter is constructed with the configured base rate (requests/min) and is immediately at that rate.
> - There is no notion of elapsed time since start — the first token bucket refill and the ten-thousandth are identical.
> - Retries after a 429 back off correctly, but by then we have already spent the provider's goodwill for that window, and on a large run the retries stack up behind each other.
> 
> Worth saying plainly: the retry path is not broken. it does what it should. The problem is entirely upstream of it — we should not be generating the burst in the first place.

> **Ramp shape**

> The warmup is a ramp over a fixed number of steps, defined against the configured base rate.
> 
> Warmup should walk up in even shares of the base rate, one share per step, and the very first step gets a share like the rest. So with a base rate of R and N warmup steps, step k runs at k·(R/N) — meaning step 1 runs at R/N, not at zero and not at some smaller seed value, and step N runs at the full R.
> 
> Two consequences of that which are easy to get wrong in implementation:
> 
> - The ramp starts at a nonzero rate. There is no dead period at the head of a run; work begins on step 1 at the same share every other step gets.
> - The increments are equal. Nothing geometric, nothing that doubles.

> **Defaults and configuration**

> - The ramp is on by default. A run that does not configure anything gets the warmup.
> - Step count and step duration are both configurable; the base rate is whatever the caller already configured, the ramp does not introduce a second rate knob.
> - Setting the step count to 1 collapses the ramp to current behaviour (step 1 is the full base rate), which is the escape hatch for anyone who needs the old shape back.
> 
> i'd expect most callers to never touch any of these. the defaults should be chosen so that a normal run loses a negligible amount of wall-clock at the head and nobody notices the ramp except by not getting 429s.

> **Explicitly out of scope**

> - **Auto-detection of provider limits (207, 233).** Deferred at the Jun 9 sync, still deferred. The ramp takes the base rate as given; where that number comes from is the detection work's problem, not this one.
> - **Adapting the ramp based on responses.** No shortening the ramp because things look healthy, no restarting it because we saw a 429. The ramp is fixed and time-based. Anything reactive belongs with the detection work.
> - **Batch mode.** Batch submission has a different shape entirely and is not affected here.
> - **Per-provider ramp tuning.** One shape for all providers for now. If a specific provider turns out to need something else we can revisit, but not preemptively.

> **Open**

> - [ ] Pick the default step count and step duration. i think we want to derive these from observed 429 timings on the runs that have been tripping rather than guessing — Dario may already have those logs.
> - [ ] Decide whether the ramp is visible in run output, or whether it stays silent. Maybe a single line at run start noting the ramp is active; a per-step log seems like noise.
> - [ ] Confirm the ramp interacts sanely with a resumed run — my assumption is a resume gets a fresh warmup, but that's an assumption and not something anyone has confirmed.

> **Problems:** longer than one remark

### g11.r2.S2 — Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.

*Nobody says:* A descent that is stretched across the steps remaining after warmup and is required to be at its lowest on the last step is a straight line from base rate to floor, so the slope is fixed by the run length.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g11.r2.L7` — observability

**konrad**, 2025-03-20, #cookbooks

> Look, I pinned the eight step curve from the warmup-2 job into a test, and the per-batch stats lines match it once approx has rel=1e-12.

*What a reader should take from it:* the team agrees the per-step rates are pinned exactly and surface on the per-batch stats

*Step it builds toward:* `g11.r2.S2` — Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.

*Drafted as:* Pinned the eight step curve from the warmup-2 job in a test, and the per-batch stats lines match it once approx has rel=1e-12.

*Why there:* None of the eight candidates is chewing on training-step mechanics. The two finetuning-adjacent days are about coordination, not numbers: 2025-05-22 #engineering is Konrad blocked on PR 653 and arguing over factory-cleanup scope, and 2025-05-02 #code-review is a review-queue triage where "finetuning side is clean" is a status line, not a discussion of an LR schedule. A concrete claim about an eight-step warmup curve pinned to rel=1e-12 and surfacing on per-batch stats would land in either room as a subject change nobody answers. #viewer is scoped to the curation-run surface (download plumbing, counters, end-of-run tables), and #pipeline is the request layer — token/cost accounting, not optimizer step rates. Finetuning is Konrad's territory and has no narrower channel, so the per-step-rate verification argument belongs in #engineering, in a conversation that doesn't exist yet: the one that happens once PR 653 lands and the trainer starts emitting per-step rates on the per-batch stats, where someone else states the curve's shape and endpoints and Konrad reports that he has pinned it.

*Still leaves open:* what the curve's shape and endpoints actually are

*Must appear literally:* `rel`

*A new conversation in #cookbooks on 2025-03-20:*

```
```

#### `g11.r2.L6` — rule, observability

**emil**, 2025-04-24, thread:new|g11.r2.L6

> and it shouldn't bottom out at zero — honestly a tenth of the base rate is still enough to move something on the last step of the run.

*What a reader should take from it:* the team agrees the lowest rate in a run is a tenth of the base rate

*Step it builds toward:* `g11.r2.S2` — Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.

*Drafted as:* and it shouldn't bottom out at nothing, a tenth of the base rate is still enough to move something on the last step of the run.

*Why there:* Every listed candidate is about the request layer or release logistics — batch job persistence, docker image pinning, weekly PR queues, version announcements. None of them touches training hyperparameters, so a settled decision about the learning-rate floor for a run would arrive from nowhere in all eight, and in Emil's weekly-update mails it would be a subject change nobody responds to. The remark is one turn in an argument about the shape of an LR schedule for the fine-tune step: the floor is agreed at a tenth of the base rate, while the decay shape and where it lands are still being worked out by someone else in the thread. That argument belongs in #engineering, where design decisions about our own training code get hashed out, not in #cookbooks just because the fine-tune runs off a curated dataset there, and not in #pipeline, which is about provider request rates.

*Still leaves open:* how it gets down to that point and whether the last step is where it arrives

*A new thread — **Training config for the fine-tune step — schedule question**, 2025-04-24:*

```
From: konrad  To: emil, dario, nikolai
Hi all,

I put the training config for the fine-tune step in the branch (configs/sft_qwen7b.yaml), please look when you have a moment. Most of it is copied from the run we did in march, only the batch size and the warmup are changed.

The part I am not sure about is the schedule. Right now it is cosine down to zero. What that means in practice is the last few hundred steps do nothing measurable, loss curve is flat there and the checkpoints are identical to eachother off the top of my head, withi

From: emil  To: konrad, dario, nikolai   <-- the remark
let me think through that, since I think the two questions are actually the same question wearing different hats.

your read on the tail is right — a cosine that lands on zero spends its last stretch doing arithmetic on a rate too small to change any weight, and we're paying gpu hours for the privelege. we need to be intentional here rather than inheriting the march config, which I believe was itself inherited from something else. so: keep the cosine shape, but give it a floor, and it shouldn't 

From: nikolai  To: emil, konrad, dario
yep that matches what i saw when i pulled the checkpoints from the march run

the last four were within noise of each other on every eval we had which is a lot of storage for nothing

i'd say drop eval to every 200 while youre in there konrad the run is short enough that it wont cost much

From: dario  To: konrad, emil, nikolai
mhm, that tracks with the march numbers.

konrad, one thing that isn't in the config but should be — can you make sure the run logs the actual rate per step and not just the configured one? i think last time we were reading the schedule off the yaml and assuming, and that is fine until it isn't. best we can do is have the number in the same place as the loss.

no objection to starting today either way.

```

#### `g11.r2.L4` — rule

**dario**, 2025-05-06, thread:new|g11.r2.L4

> honestly the last third of that 40 step job barely moves — loss flat, rate small enough it may as well not be running. the tail should still train.

*What a reader should take from it:* the team agrees the tail of a run must still train

*Step it builds toward:* `g11.r2.S2` — Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.

*Drafted as:* the last third of that 40 step job barely moves, loss is flat and by then the rate is small enough that it may as well not be running.

*Why there:* All eight candidates are curator/Millrow logistics — weekly PR roundups, a v0.1.22 release note, a batch-job-status persistence design thread, and two maintenance-mode recaps. None of them is chewing on training dynamics, loss curves, or learning rate schedules; the closest touchpoint is PR 653, which is a finetuning *client* (job submission plumbing), not a trainer anyone reads a loss curve off of. Dario observing that the last third of a 40 step job is flat would arrive from nowhere in a status mail about download plumbing or bulk inference, and nothing in those threads would answer it. It needs a room where people argue about training code — #engineering, per the list, since there is no training-specific channel — during the window when the finetuning path was actually being smoke-tested (PR 653 in review, week of Apr 28 / early May). Nikolai owns that PR, Emil is the one who'd push on reproducibility, and the rest of the thread is where the floor and the pacing of the decay get settled.

*Still leaves open:* how low it is allowed to get, and how the fall should be paced across the run

*A new thread — **smoke runs against 653 before I sign off on the review**, 2025-05-06:*

```
From: nikolai  To: dario, konrad, emil
before i go back to the 653 review comments i want to know what you actually saw on the finetuning client end

konrad had it as no blockers in the weekly which is fine but that was on paper not on a run

you did some short jobs against it yesterday right did anything break or is it clean

From: dario  To: nikolai, konrad, emil   <-- the remark
yes, three of them yesterday evening and one more this mornign, all against the same small slice so at least the comparison between them is fair.

the client itself behaves. no crashes, checkpoints land where they are supposed to, and a resumed run picks back up without complaining, which i think is the part you actually wanted for the review. one thing worth saying though — the last third of that 40 step job barely moves, loss is flat and by then the rate is small enough that it may as well not

From: emil  To: dario, nikolai, konrad
so to make sure i have this right — the client is fine, and the caveat is about how the curves read rather than about the code under review. that's how i'm taking it anyway.

logs would be good, yes. put them wherever you normally do and i'll pick them up. i'm not entirely sure whether the smoke config is checked in anywhere or if it only lives on your machine, if it's the second one that's worth fixing at some point but not this week.

From: konrad  To: dario, nikolai, emil
Right, thanks Dario. I will leave the finetuning line in the weekly as it is then, presumably nothing changes there.

Anyway Nikolai, the two download PRs still need eyes if you have any time left after 653.

— Konrad

```

#### `g11.r2.L5` — rule

**gideon**, 2025-06-17, page:engineering/reading-the-per-step-ledger-from-a-finetuning-run.md

> After the ramp the rate is basically at the bottom within a couple steps tbh, it should be taking the whole rest of the run to get down there.

*What a reader should take from it:* the team agrees the descent is spread over the steps remaining after warmup

*Step it builds toward:* `g11.r2.S2` — Once warmup is over the rate comes down evenly across however many steps of the run are left, and it stops on the run's final step at a tenth of the base rate rather than at zero.

*Drafted as:* After the ramp the rate is near the bottom within a couple of steps; it should be taking the whole rest of the run to get down there.

*Why there:* Every listed candidate is a Millrow inference-side page — PR status, rate-limit issues 207/233, release cuts, the dormancy freeze. This remark is about a training schedule: a warmup ramp followed by a decay that collapses to its floor in a couple of steps instead of spreading across the remaining steps. Nothing on those pages is chewing on step schedules or a training run at all, so it would land as a subject change signed by Gideon under notes about deferred rate-limit work. The place it belongs is #engineering, where behaviour arguments about code that hasn't found a narrower channel get had — specifically off the first end-to-end finetuning run from a curated dataset, where the per-step ledger shows the curve flattening immediately after warmup. Gideon is plausibly the one looking at it (he was already reviewing finetuning), and the sibling question of what the floor is and whether it's zero is exactly what the rest of that page would argue out with Nikolai, who owns PR 653.

*Still leaves open:* what the bottom is, and whether it is zero or something above it

*Must appear literally:* `After`

*A new page — **Reading the per-step ledger from a finetuning run** in `engineering`, 2025-06-17:*

> **Why this page exists**

> The first end to end finetuning run off a curated dataset finished overnight (kicked off ~22:40 on the 16th, done a bit before 07:00). So basically this is the first time anyone here has looked at a full per-step ledger from our own pipeline rather than from somebody else's tutorial, and I had to figure out what half the columns meant while reading them.
> 
> Writing it down now while it is fresh, mostly so the next person does not repeat the same twenty minutes. Also because PR 653 (finetuning client, Shreyas + Nikolai) is going to get picked back up and some of what is below is relevant to what that client should be surfacing.
> 
> Not a design doc. Just what the ledger contains and what I

> **What is actually in the ledger**

> One row per optimizer step, written as JSONL, one file per run under the run dir. Columns, in the order they appear:
> 
> - `step` - optimizer step, not batch. If grad accumulation is on these are not the same number and that tripped me up at first.
> - `loss` - train loss for that step only, not smoothed, not averaged over the epoch.
> - `learning_rate` - the value the scheduler handed the optimizer for this step.
> - `grad_norm` - post-clip.
> - `epoch` - fractional, so 0.42 etc.
> - `wall_ms` - time for the step in ms.
> 
> No eval columns in this file. Eval rows go to a separate ledger written at eval intervals only, which is honestly a bit confusing since both files are called ledger-so

> **The loss curve on this run**

> Loss goes from ~2.6 down to ~1.1 over the first roughly 400 steps, then flattens out and wanders between 1.0 and 1.15 for the remainder. Nothing alarming there as far as I can tell, that is the shape you would expect.
> 
> The per step noise is large though, spikes to 1.6 and 1.7 happen throughout and they are not a signal of anything by themselves, single batch loss on a small batch is just noisy. If you are eyeballing this file directly, smooth over ~50 steps before drawing any conclusion, otherwise every third row looks like a regression.
> 
> `grad_norm` sits under the clip threshold basically the whole run except for the first ~20 steps. Fine.

> **The learning rate column**

> This is the part I do not have an explanation for yet, so recording it as observed.
> 
> Config for this run was linear warmup over 500 steps then cosine decay to 10% of peak across the remaining ~7.6k steps. Peak was 2e-5. Warmup itself looks correct in the ledger, the ramp is clean and it tops out at 2e-5 right where it should, around step 500.
> 
> What the ledger shows after that does not match the schedule. After the ramp the rate is near the bottom within a couple of steps; it should be taking the whole rest of the run to get down there. By step ~520 we are already at roughly 2.1e-6, which is the floor, and it stays flat at the floor for the remaining several thousand steps. So the dec

> **Open, and what this means for PR 653**

> - [ ] Find where `num_training_steps` is computed and what value the scheduler actually receives. Mine to pick up.
> - [ ] Re run with the schedule fixed once that is understood, so we have a baseline curve that came from the intended config.
> - [ ] Question for Nikolai / Shreyas: what does the finetuning client expose from the ledger today? If it only surfaces loss then this class of thing stays invisible, and `learning_rate` is cheap to pass through.
> - [ ] Decide whether the two ledger files stay separate. Not urgent.
> 
> Honestly though none of this blocks reading the existing ledgers, the file format is stable and the columns mean what they say. Just do not treat the current run as a

### g11.r2.S3 — The floor is a named module-level default that a caller can override per call, and any step asked for beyond the end of the run returns that floor instead of continuing downward; a resume that only lengthens the run keeps descending the longer schedule from where it stopped.

*Nobody says:* If the descent is pinned to the run length, then a step past the end can only be handled by holding the last value, and a longer run simply recomputes the same line.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g11.r2.L10` — exclusions_or_crossover

**konrad**, 2025-03-21, #cookbooks

> mhm. A resume where only the epoch count changed should keep walking down from the step it stoped at, on the recomputed longer schedule, not restart the ramp.

*What a reader should take from it:* the team agrees a run whose epochs grew continues down the recomputed longer schedule

*Step it builds toward:* `g11.r2.S3` — The floor is a named module-level default that a caller can override per call, and any step asked for beyond the end of the run returns that floor instead of continuing downward; a resume that only lengthens the run keeps descending the longer schedule from where it stopped.

*Drafted as:* A resume where the only change is more epochs should keep walking down from the step it stopped at, on the longer schedule, not start the ramp again.

*Why there:* None of the candidate days is chewing on training-run resume or LR schedule behaviour. The two #engineering days closest to Konrad's finetuning work are about agentic-curation scope (2025-05-22) and PR 704 / the missing plan doc (2026-01-23); #code-review 2025-06-03 is queue triage, #releases 2025-05-06 is release notes, #cookbooks 2025-12-29 is importorskip and verifier CI, and 2025-03-20/24 are provider PRs and cost estimation. A settled decision about how a resumed run walks its schedule would change the subject in any of those and draw no reaction. #pipeline does cover resume, but resume of requests and batch submissions, not optimizer step and epoch count — this is training code, so it belongs in #engineering, where design arguments live and where Konrad owns finetuning.

*Still leaves open:* what happens when a step falls past the end of the schedule entirely

*Must appear literally:* `A`

*A new conversation in #cookbooks on 2025-03-21:*

```
```

#### `g11.r2.L9` — rule, exclusions_or_crossover

**dermot**, 2025-04-09, thread:new|g11.r2.L9

> past the end it should just return the floor, MIN_LR_RATIO in the ledger module. nikolai wants min_lr_ratio passable per call for a cookbook run, that seems fair to me

*What a reader should take from it:* the team agrees the floor is a named module default that callers may override per call, and out-of-range steps return it

*Step it builds toward:* `g11.r2.S3` — The floor is a named module-level default that a caller can override per call, and any step asked for beyond the end of the run returns that floor instead of continuing downward; a resume that only lengthens the run keeps descending the longer schedule from where it stopped.

*Drafted as:* past the end it should just sit at the floor, MIN_LR_RATIO in the ledger module; nikolai wants to pass min_lr_ratio per call for a cookbook run.

*Why there:* All four candidates are mail: two weekly status roundups, an OOM/semaphore verification thread, and a release announcement for v0.1.21. None is chewing on the training-step ledger or the lr schedule. The nearest miss is the Apr 7 weekly update — dermot is already writing there and already asking for input — but its open question is provider cost metadata, and a scheduler default is not an answer to it; the remark would arrive from nowhere and draw no reply. This is a design call about training code: what the ledger module returns for out-of-range steps, and whether callers may override the default per call. It belongs where people argue about module defaults, not in #cookbooks merely because nikolai's motivating run is a cookbook one. That is #engineering, in the thread where nikolai asks what he gets back past the last step.

*Still leaves open:* what value that floor holds and how the schedule reaches it

*Must appear literally:* `MIN_LR_RATIO`, `min_lr_ratio`

*A new thread — **step ledger past the end of the schedule**, 2025-04-09:*

```
From: nikolai  To: dermot, emil
wiring the finetune for the cookbook run today and i hit a question i cant answer from reading the code

what does the step ledger hand back if i ask it for a step past the end of the schedule the notebook loops a fixed number of steps and i dont want to special case the tail

second thing can i set the floor for just this run or is it a module level constant i mean i dont want to patch anything for one cookbook

From: dermot  To: nikolai, emil   <-- the remark
yeah, both of those are fair questions and the docstring is thin on it, i'll fix that separately.

on the tail: the schedule is only defined over the configured horizon, so anything you ask for beyond it is not interpolated and not clamped to zero. past the end it should just sit at the floor, MIN_LR_RATIO in the ledger module; nikolai wants to pass min_lr_ratio per call for a cookbook run. so your loop can run long and you'll get a flat value rather than an error or a negative.

that said, i'd 

From: emil  To: dermot, nikolai
sounds right on both counts, and thanks for writing it down somewhere other than a chat scrollback, we've now answered this twice.

one thing i'd add, honestly the plateau question comes up because the cookbooks are the only place anyone runs the ledger past the horizon — internally nobody does. So whatever we decide here is basically a docs decision more than a behavior decision, and we need to be intentional here about which one the notebook is teaching. Not entirely sure it belongs in the sam

From: nikolai  To: dermot, emil
yep thats what i needed

ill match the loop to the horizon so the plot stays readable and keep the tail out of the notebook body

```

#### `g11.r2.L8` — exclusions_or_crossover

**nils**, 2025-06-11, page:engineering/finetuning-client-the-lr-schedule-helper-and-what-it-returns-outside-the-step-plan.md

> bumped epochs on a resume before the plan grew and the helper handed a negative rate for the extra steps, nothing complained. those must not fall below the floor.

*What a reader should take from it:* the team agrees a step beyond the end of the schedule must not produce a value below the bottom

*Step it builds toward:* `g11.r2.S3` — The floor is a named module-level default that a caller can override per call, and any step asked for beyond the end of the run returns that floor instead of continuing downward; a resume that only lengthens the run keeps descending the longer schedule from where it stopped.

*Drafted as:* bumped epochs on a resume before the plan had grown and the helper handed back a negative rate for the extra steps, nothing complained.

*Why there:* Every candidate is curator-side infrastructure (batch persistence, image pinning, release CI, cookbook lint, weekly PR roundups); none of them is about training schedules. The batch-persistence page shares the word "resume" but means resuming request submission against the metadata db, not resuming a run with more epochs, so the LR-floor point would arrive from nowhere under someone else's problem statement. The right home is a new #engineering design page on schedule helper semantics, alongside the finetuning client work nils shares with Shreyas — training code is argued in #engineering, not in #cookbooks or #pipeline.

*Still leaves open:* what a step past the end should return instead, and how a properly lengthened run behaves

*A new page — **Finetuning client: the LR schedule helper and what it returns outside the step plan** in `engineering`, 2025-06-11:*

> **Why this note exists**

> PR 653 (finetuning client) is in review and the learning-rate schedule helper is one of the pieces that keeps drawing comments, mostly the same comment from different people. The math in `lr_at_step()` is fine and nobody has disputed it. What isnt written down anywhere is what the helper is *defined over* — which step indices are legal to ask about, and what it is supposed to hand back for the ones that arent.
> 
> That gap has now cost us an afternoon (see the resume case below), so let me write down what we currently do and what we agreed to do instead, before more client work lands on top of the helper. This is a design note, not a spec — the intent is that the reviewer of the next schedu

> **How the step plan is built**

> The plan is a length, and it is fixed at job construction:
> 
> - `total_steps = ceil(num_examples / (batch_size * grad_accum)) * epochs`
> - warmup is expressed as a fraction of `total_steps`, resolved to an integer step count at the same moment
> - the decay tail (linear or cosine, per config) is parameterised on `total_steps - warmup_steps`
> 
> So everything the helper knows about the shape of the run is baked in at construction time from the config. The helper itself is stateless — it takes a step index and returns a rate. It has no way to find out that the run it belongs to has changed underneath it, which is the whole of the problem below.

> **Behaviour at the end of the plan, and past it**

> Today the decay math is simply evaluated at whatever index you pass in. There is no bound check. For linear decay the expression is monotonically decreasing and unbounded, so past `total_steps` it crosses zero and keeps going; for cosine it starts climbing back up, which is arguably worse because it looks plausible.
> 
> The way this surfaced: i bumped epochs on a resume before the plan had grown, and the helper handed back a negative rate for the extra steps, nothing complained. The optimizer took the negative rate without objection, the loss curve did roughly what you would expect a negative rate to do, and nothing in the client logged anything at all. That is worth documenting, because th

> **What resume is responsible for**

> The rule, stated plainly: **on resume, the plan is recomputed from the resumed config; it is not read back from the checkpoint.** If `epochs` (or batch size, or grad accum) changed between the original job and the resume, `total_steps` changes with it and the decay tail is re-parameterised over the new length.
> 
> The checkpoint does still carry the `total_steps` it was written under. We keep that, but only as a cross-check — if the recomputed value disagrees with the stored one, that is a real change in the run shape and the client says so in the resume log line rather than picking one silently. I think that comparison is cheap enough to be worth having permanently, not just as a debugging

> **Open, not settled**

> - Whether the clamp lives in the helper or in the caller. right now i've put it in the helper on the grounds that the helper is the thing that knows `min_lr`, but the counter-argument — that the helper should be pure curve math and the client should own policy — is a reasonable one and i dont think it was properly argued out. either it stays in the helper and the helper owns the floor, or it moves out and every call site owns it; splitting it is the option i'd like to avoid.
> - Whether WARN is the right level for the out-of-range call, or whether it should be ERROR given that reaching it means the plan is wrong somewhere upstream.
> - Nothing here touches multi-stage schedules. if those lan

### g11.r2.S4 — A warmup longer than the run is trimmed to the run's length instead of being rejected, so such a run finishes exactly at the base rate.

*Nobody says:* Trimming the warmup to the run length means the last step of the run is also the last warmup step, and by the warmup rule that step is at the full base rate.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g11.r2.L13` — failure_behavior, observability

**nikolai**, 2025-03-24, #cookbooks

> cap it at the run lenght then the 3 step case comes out a third two thirds base and i'd say pin it with rel=1e-12 so nobody re tunes it later

*What a reader should take from it:* the team agrees an over-long warmup is trimmed to the run so the last step lands on the base rate

*Step it builds toward:* `g11.r2.S4` — A warmup longer than the run is trimmed to the run's length instead of being rejected, so such a run finishes exactly at the base rate.

*Drafted as:* cap it at the run length then: the 3 step case comes out a third, two thirds, base, pinned with rel=1e-12 so nobody re-tunes it.

*Why there:* None of the eight candidates is anywhere near a learning-rate warmup schedule. The three #code-review days (04-04, 04-08, 05-08, 06-13, 06-16) are all PR-state triage — who reviews 653/690/691, is 619 merged — with no numeric behaviour under discussion at all. #engineering 05-01 is executor image defaults and release gating; #engineering 05-22 is the agentic curation walkthrough and factory-cleanup debt; #incidents 04-18 is the cache fingerprint and a stale openai batch id. Dropping "cap warmup at the run length, 3 steps gives a third, two thirds, base, rel=1e-12" into any of them would change the subject cold and draw no reply. The remark is the back half of a design argument — someone else has just settled that a warmup longer than the run is tolerated rather than rejected, and nikolai is saying what the tolerated case should then do — which is exactly what #engineering exists for ("design arguments, half-formed plans"). Finetuning is Konrad's territory (he says so on 05-22 and waits on PR 653 all through May and June), so he is the one who would have raised it and the one who settles the tolerate-vs-error half; nikolai, who has spent April and May pushing for decisions to actually get made rather than left ambiguously blocked, is in character supplying the concrete schedule and the pinned tolerance so it doesn't get re-litigated.

*Still leaves open:* whether an over-long warmup is tolerated at all, which somebody else settled

*Must appear literally:* `rel`

*A new conversation in #cookbooks on 2025-03-24:*

```
```

> **Problems:** longer than one remark

#### `g11.r2.L12` — failure_behavior

**dario**, 2025-05-13, thread:new|g11.r2.L12

> honestly i don't think that should be an error — half the cookbook configs get pasted into runs shorter than the warmup they were written for.

*What a reader should take from it:* the team agrees a warmup longer than the run is not rejected

*Step it builds toward:* `g11.r2.S4` — A warmup longer than the run is trimmed to the run's length instead of being rejected, so such a run finishes exactly at the base rate.

*Drafted as:* that shouldn't be an error though, half the cookbook configs get pasted into shorter runs than the warmup they were written for.

*Why there:* All eight candidates are weekly-update or design-note mails: PR queues, release sequencing, cost accounting scope, cache dir semantics. None of them is chewing on rate-limiter warmup semantics, and none contains anything about validating a warmup window against run length — dropping "that shouldn't be an error" into a status recap would change the subject and get no reply. The remark is a settled call on the request layer's validation behavior (warmup longer than the run is accepted, not rejected), which is squarely #pipeline: rate limits, token accounting, provider backends. It needs a thread where someone has just proposed raising an error on that config, with a sibling deciding what the resulting rates come out as. The cookbook mention is incidental — it's evidence about how configs get reused, not a discussion of the example corpus.

*Still leaves open:* what the rates on such a run should actually come out as

*A new thread — **shared limiter: runs that finish inside the warmup window**, 2025-05-13:*

```
From: emil  To: dario, gideon
While working through the shared limiter changes I ran into a case i wasn't expecting. The limiter ramps its concurency over a warmup window, and I had a run last night that finished all 300 requests before the window even closed, so the ramp never got past its first step. Nothing crashed, but the effective rate was well under what the config asked for.

So if i'm reading the situation right, the question is whether a config whose warmup is longer than the run itself should be rejected at startu

From: dario  To: emil, gideon
mhm, i've hit this too, though i didn't chase it down at the time. my read is that the ramp working correctly and the run being short are two different facts and only one of them is the user's problem.

that shouldn't be an error though, half the cookbook configs get pasted into shorter runs than the warmup they were written for. people grab a block out of an example that was written for a 40k row job and drop it on a 200 row smoke test, and if that starts refusing to start we'll be answering th

From: gideon  To: dario, emil
ya that matches what I saw when I was testing the cookbook samples last week. So basically the config is fine, the run is just too short for it to matter.

Honestly though the estimate part is the bit I'd watch, tbh for streaming inputs we don't know the row count up front at all. Happy to take a look at that with you tomorrow Emil if you want.

```

#### `g11.r2.L11` — failure_behavior

**emil**, 2025-06-24, page:engineering/finetuning-client-config-validation-what-we-check-today-pr-653.md

> honestly the 3 step smoke config has warmup sat at 10, so the whole thing trains at a crawl and never gets anywhere near the base rate.

*What a reader should take from it:* the team agrees a warmup longer than the run currently starves the run

*Step it builds toward:* `g11.r2.S4` — A warmup longer than the run is trimmed to the run's length instead of being rejected, so such a run finishes exactly at the base rate.

*Drafted as:* our 3 step smoke config has warmup sat at 10 and the whole thing trains at a crawl, it never gets anywhere near the base rate.

*Why there:* Every listed place is about batch/provider plumbing, release gates, PR triage or the viewer surface — none of them is chewing on LR schedules or training configs at all. The Apr 21 and May 26 weekly notes and the Jun 16 sync mention PR 653 (finetuning client) only as a review-status line, so a claim about warmup steps starving a 3-step smoke run would change the subject under someone else's status heading. The WS-050 and WS-047 pages are batch-cost and CI-gate documents authored for a different scope, and the image-pinning page is Nikolai's container question. What this remark answers is a live design argument about whether a training config whose warmup exceeds its step count should be rejected or clamped, which is exactly the kind of half-formed validation argument #engineering exists for; the sibling remark that settles reject-vs-fixup and what the three steps should read sits right next to it there.

*Still leaves open:* whether that config should be rejected or fixed up, and what the three steps ought to read

*A new page — **Finetuning client config validation: what we check today (PR 653)** in `engineering`, 2025-06-24:*

> **Why this page**

> Nikolai asked in #engineering today whether `warmup_steps` larger than the total step count should be a hard error or quietly clamped, in the context of the config validation work going into PR 653 (finetuning client). Rather than answer that one in isolation i went and read through the configs we actually ship, and it turned out there was enough there to write down.
> 
> So this is a snapshot of what the finetuning client validates as of 2025-06-24, what it deliberately doesnt, and the couple of cases where the two disagree. Not a design doc — if we change the validation story this page gets rewritten.

> **What we validate today**

> Current state, roughly in the order the checks run:
> 
> - required fields present (model, dataset ref, output path). Missing ones raise at construction time, before any network call.
> - types coerced where its unambiguous, string ints -> int, that sort of thing.
> - unknown keys are rejected. this one has bitten people on renamed params and i think thats correct behaviour, but noting it because it is the strictest thing we do.
> - ranges: learning rate > 0, batch size >= 1, epochs >= 1.
> 
> Thats it. Everything is field-local. we do not currently look at any two fields together, which is exactly the gap Nikolai's question is poking at.

> **warmup_steps against total steps** **← carries the remark**

> This is the cross-field case, and it's worth being concrete about it rather than reasoning from first principles.
> 
> Before forming a view i went and looked at the smoke configs we actually ship. our 3 step smoke config has warmup_steps sat at 10, and the whole thing trains at a crawl — it never gets anywhere near the base rate. So the config that a strict `warmup_steps > total_steps` check would reject today is one of ours, and it has been in the tree in that shape for a while without anyone filing anything.
> 
> Worth saying plainly: the smoke config isnt trying to learn anything, it exists to prove the loop runs end to end. The schedule being degenerate is not a bug in the smoke config,

> **Error vs clamp — where it stands**

> Not settled as of writing. The two options on the table from the thread:
> 
> 1. **hard error at validation time.** consistent with how we treat unknown keys and out-of-range scalars. would require fixing the smoke configs first, which is a small change but has to land before or with the check.
> 2. **clamp to total steps and warn.** nothing breaks, but we'd be the only place in the client that silently rewrites a user value, and i'm not entirely sure a warning gets read in practice.
> 
> Nikolai owns the call since it's his PR. Shreyas has context on the finetuning side and should probably weigh in before it merges. we need to be intentional here mostly because whichever way it goes sets th

> **Other cross-field cases that will come up**

> Flagging these now so they dont each get relitigated seperately later:
> 
> - eval interval larger than total steps — same shape of problem, evaluation never fires.
> - batch size larger than the dataset. currently accepted, honestly i dont know what the backend does with it.
> - lora rank vs the target module dims, if/when we expose those.
> 
> None of these are in scope for PR 653 and i'm not proposing we add them. listing them because whatever we decide about warmup_steps is the answer we'll be reaching for on all three.

### Herrings — believed at the time, overturned later

#### `g11.r2.lr-schedule-zero-decay-dario` — herring

**dario**, 2025-01-21, #pipeline

> no floor — learning_rate_at just decays linearly to zero at total_steps, and warmup keeps the `step < warmup_steps` comparison the trainer already uses.

*A herring: stated as settled at the time, overturned later (from 2025-03-20).*

*Drafted as:* the ledger's learning_rate_at decays linearly to zero at total_steps, and warmup keeps the `step < warmup_steps` comparison the trainer already uses. no floor.

*Why there:* None of the eight candidates is in a room where a training-side schedule decision would be said. All of them are inference-layer work: batch/online request paths, cost accounting and cost-map defaults, provider rate limits, PR queue triage, the end-of-run summary table, and cookbook example breakage. Nobody in any of these days is talking about a trainer, a step ledger, warmup, or a learning rate — the closest vocabulary overlap is #pipeline's "rate limits", which is a different sense of "rate" entirely, and #cookbooks' fine-tuning handoff, which is about published recipes rather than the internals of a schedule API. Dropping `learning_rate_at`/`total_steps`/`warmup_steps` into any of them changes the subject and would draw no reply. It belongs in #engineering, the room the channel list reserves for design arguments that haven't found a narrower home, on a day when someone is actually wiring the step ledger and needs the boundary semantics settled — dario is the natural person to settle it, since he already answers scoping questions of exactly this shape ("image serialization in the pipeline layer first, then the online request loop") when someone asks him how he had something scoped.

*A new conversation in #pipeline on 2025-01-21:*

```
```

#### `g11.r2.lr-schedule-zero-decay-konrad` — herring

**konrad**, 2025-01-22, #cookbooks

> Settled the shedule: linear decay to 0.0 at the end of the run, warmup gated on step < warmup_steps. Ported straight off tinker_trainer.py:548.

*A herring: stated as settled at the time, overturned later (from 2025-03-20).*

*Drafted as:* Settled the schedule: linear decay to 0.0 at the end of the run, warmup gated on step < warmup_steps. Ported straight off tinker_trainer.py:548.

*Why there:* None of the listed conversations touch training code. The two #cookbooks days are about broken example scripts and verifier test coverage against published recipes; the #code-review and #engineering days are PR/queue triage (439, 430, 495, 468, 549/551) and the #general day is Nils' onboarding. A settled learning-rate schedule ported from tinker_trainer.py:548 answers nothing those rooms are chewing on, and konrad dropping it there would change the subject with no reaction. #cookbooks owns the handoff from a curated dataset into fine-tuning, but that is the handoff, not the trainer's optimizer internals — design arguments about training code with no narrower channel land in #engineering. It needs a conversation where someone is actually porting the trainer step and the warmup/decay boundary is still open, so konrad's "settled" reads as closing a question that was asked.

*A new conversation in #cookbooks on 2025-01-22:*

```
```

#### `g11.r2.rev1` — rule, exclusions_or_crossover

**dario**, 2025-03-19, #releases

> the decay to zero i asked for is gone — that 40 step job's tail trained nothing. learning_rate_at floors at MIN_LR_RATIO = 0.1 of base_lr and clamps past the end: learning_rate_at(99, 8, 1e-4, 2) == 1e-05

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the decay-to-zero i asked for is gone — the tail of that 40 step job was running at a rate that trained nothing. learning_rate_at now floors at MIN_LR_RATIO = 0.1 of base_lr, and past the end it clamps there: learning_rate_at(99, 8, 1e-4, 2) == 1e-05.

*Why there:* None of the listed conversations are about training code. #pipeline 03-24 and 04-09 are batch submission/resume and provider backends; #engineering 04-03 and #general 04-21 are review-queue triage; #viewer 04-14 is the summary table and release notes; #code-review 03-14 is the schema_check construction hook; #engineering 03-17 is litellm model-name matching; #pipeline 04-29 is stdout scope and the structured output override. A learning-rate schedule floor answers nothing any of those rooms is chewing on, and dario saying it there would land with no reply. It needs #engineering on a day where the short fine-tune off a curated set is actually the topic — the main room is where design calls with no narrower channel get made, and the shape of the schedule is a design call, not an example-corpus question.

*Must appear literally:* `learning_rate_at`, `MIN_LR_RATIO`, `0.1`, `learning_rate_at(99, 8, 1e-4, 2)`, `1e-05`

*A new conversation in #releases on 2025-03-19:*

```
```

> **Problems:** longer than one remark

#### `g11.r2.rev2` — rule, failure_behavior

**dermot**, 2025-03-24, #releases

> dropped the `step < warmup_steps` comparison we ported off tinker_trainer.py:548, step 1 trained at rate 0. it's base_lr * step / effective_warmup now, effective_warmup = min(warmup_steps, total_steps), clipped not raised.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* we dropped the `step < warmup_steps` comparison ported off tinker_trainer.py:548 — step 1 trained at rate 0. warmup is now base_lr * step / effective_warmup for 1 <= step <= effective_warmup, effective_warmup = min(warmup_steps, total_steps), clipped not raised.

*Why there:* Every listed conversation is about the inference/request side — provider backends, batch resume, rate limit headers, release cuts, progress tables, job-reuse keys. None of them is chewing on the trainer at all, so a warmup-schedule correction ported off tinker_trainer.py would change the subject and draw no reply in any of them. #cookbooks touches fine-tuning only at the dataset handoff, not at the optimizer; the room where people argue about training code is #engineering. The conversation that should exist: dermot porting the training step loop off tinker_trainer.py, someone (gideon, who watches the counters) noticing a short smoke run logged lr 0 on step 1 and a run shorter than warmup_steps never leaving the ramp, and the thread settling on clipping warmup to the run length rather than raising on it. That thread would also cover where the step counter starts and whether the schedule logs per step.

*Must appear literally:* `step < warmup_steps`, `tinker_trainer.py:548`, `effective_warmup`, `min(warmup_steps, total_steps)`, `base_lr * step / effective_warmup`

*A new conversation in #releases on 2025-03-24:*

```
```

> **Problems:** longer than one remark

