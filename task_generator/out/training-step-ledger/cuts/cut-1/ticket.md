# Step ledger for fine-tuning: one step unit, one checkpoint identity, one resume contract

Give the fine-tuning trainers a single, testable accounting of what a "step" is, so `total_steps`, the learning-rate schedule, checkpoints and resume all agree — and so a mock run is deterministic without any test-side patching.

### New module `src/bespokelabs/curator/finetune/step_ledger.py`
- A leaf module: it imports `json`, `math`, `dataclasses`, `typing` and `xxhash.xxh64` only. It must **not** import `time`, `datetime` or `random`, and must not import `finetune.types` or `finetune.config` at runtime — the annotations for `plan_steps_for_config` / `plan_resume` go under `if TYPE_CHECKING:` so `TrainingResult.step_plan` creates no cycle. Import-clean without `tinker` installed. No new dependency.
- Constants: `STEP_UNIT_OPTIMIZER: str = "optimizer_step"`, `MIN_LR_RATIO: float = 0.1`, `CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")`, `CHECKPOINT_NAME_TEMPLATE: str = "{prefix}-s{step:06d}"`, `DATASET_SIGNATURE_PREFIX: str = "ds1"`.
- `class StepLedgerError(ValueError)` — base of the module's exception family.
- `@dataclass(frozen=True) class StepPlan` with fields, in this order: `step_unit, num_examples, batch_size, epochs, gradient_accumulation_steps, batches_per_epoch, total_batches, total_steps, trailing_window_batches, dataset_signature`. Methods (all batch ordinals 1-based, all step numbers 1-based):
  - `step_of_batch(batch_ordinal) -> int`, `is_step_boundary(batch_ordinal) -> bool`, `epoch_of_batch(batch_ordinal) -> int`, `batch_slice(batch_ordinal) -> Tuple[int, int]` (a `[start, end)` slice into the example list)
  - `epoch_final_steps() -> Tuple[int, ...]` — for each epoch, the optimizer step at which that epoch's last batch has been accounted for
  - `logging_steps(log_every_n_steps) -> Tuple[int, ...]` — steps `s` with `n > 0 and s % n == 0`
  - `loss_history_steps(log_every_n_steps) -> Tuple[int, ...]` — the ascending, de-duplicated union of `logging_steps(n)` and `epoch_final_steps()`
  - `interval_steps(checkpoint_every_n_steps) -> Tuple[int, ...]` — steps `s` with `n > 0 and s % n == 0`
- `@dataclass(frozen=True) class ResumePlan` with fields, in this order: `checkpoint_name, start_batch_ordinal, start_epoch, start_batch_in_epoch, completed_steps, remaining_batches`.
- `dataset_signature(examples) -> str` returns `f"ds1-{len(examples)}-{xxh64(payload).hexdigest()}"` where `payload = json.dumps(list(examples), sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True).encode("utf-8")`. Content- and order-sensitive; independent of dict key insertion order.
- `plan_steps(num_examples, *, batch_size, epochs, gradient_accumulation_steps=1, dataset_signature="") -> StepPlan` — `step_unit == STEP_UNIT_OPTIMIZER`; `batches_per_epoch = ceil(num_examples / batch_size)`; `total_batches = batches_per_epoch * epochs`. `total_steps`, `trailing_window_batches`, `step_of_batch` and `is_step_boundary` express one consistent definition of the accumulation window; `warmup_steps`, `log_every_n_steps` and `checkpoint_every_n_steps` are all counted in that same unit.
- `plan_steps_for_config(config, examples) -> StepPlan` — reads `batch_size`, `epochs`, `gradient_accumulation_steps` off a `TinkerTrainerConfig` and hashes `examples`.
- `checkpoint_name(prefix, step) -> str` via `CHECKPOINT_NAME_TEMPLATE` (`checkpoint_name("checkpoint", 2) == "checkpoint-s000002"`).
- `canonical_reasons(reasons) -> Tuple[str, ...]` — de-duplicates and orders by `CHECKPOINT_REASONS`; an unrecognised reason raises `StepLedgerError`.
- `learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio=MIN_LR_RATIO) -> float` — `effective_warmup = min(warmup_steps, total_steps)`; for `1 <= step <= effective_warmup` the rate is `base_lr * step / effective_warmup` (warmup is inclusive and 1-based, so step `warmup_steps` is the first step at the full base rate); afterwards `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)` and `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)`, clamped at the `min_lr_ratio` floor. `step < 1` raises `StepLedgerError`.
- `plan_resume(plan, checkpoint) -> ResumePlan` — validates a `CheckpointInfo` against the plan for the configured run and rejects one that cannot be resumed into it; otherwise returns where the run picks up.

### `types.py` — twelve appended, defaulted fields
- `CheckpointInfo` gains, in order: `batch_size: int = 0`, `gradient_accumulation_steps: int = 0`, `batches_completed: int = 0`, `dataset_signature: str = ""`, `reasons: Tuple[str, ...] = ()`.
- `TrainingStats` gains `current_batch: int = 0` and `total_batches: int = 0`.
- `TrainingResult` gains `total_batches: int = 0` and `step_plan: Optional[StepPlan] = None`.
- Every existing construction site must keep working unchanged.

### `config.py`
- `seed: int = Field(default=0, ge=0)` on both `TinkerTrainerConfig` and `FireworksTrainerConfig`.

### `trainer/tinker_trainer.py`
- `__init__(self, config, *, clock: Optional[Callable[[], float]] = None, rng: Optional[random.Random] = None)`; `self._clock = clock if clock is not None else time.time`; `self._rng = rng if rng is not None else random.Random(config.seed)` — the mock trainer is reproducible out of the box.
- `_training_step`'s mock branch draws exactly one `self._rng.random()` per batch, in batch order, and computes `2.5 - draw * 0.5`; its `time.sleep(0.01)` is deleted. No module-level `random.random()` or `time.time()` call remains on any mock path. `train()` calls `self._clock()` twice (start, and for `total_time`), plus once more for the `save_weights_on_complete` auto-name. `get_sampling_client`'s real-SDK `time.time()` is untouched.
- `_get_learning_rate(self, step, total_steps)` keeps its signature and delegates to `learning_rate_at` with `config.adam_params.learning_rate` and `config.warmup_steps`.
- `train(dataset)` is rebuilt on `plan_steps_for_config`: it walks batches by their global 1-based ordinal, slices examples with `plan.batch_slice`, passes `should_optim_step=plan.is_step_boundary(b)` into `_training_step`, feeds `FinetuneStatusTracker` (constructed with `total_steps=plan.total_steps`) and fills `TrainingResult.total_steps/total_batches/step_plan`. `metadata` gains `"dataset_signature"`.
- `loss_history` has exactly one entry per step in `plan.loss_history_steps(config.log_every_n_steps)`, ascending, each the arithmetic mean of the per-batch losses in that step's accumulation window; `final_loss` is `loss_history[-1]`.
- Checkpoints are written only at optimizer-step boundaries, at most one `save_checkpoint` call per step. Triggers: `"interval"` when `checkpoint_every_n_steps > 0 and s % checkpoint_every_n_steps == 0`; `"epoch"` when `config.checkpoint_every_epoch` and `s` is in `plan.epoch_final_steps()`; `"final"` at `s == plan.total_steps`, which fires regardless of configuration, so every completed run ends with at least one checkpoint. The `reasons` passed are `canonical_reasons(...)`, and the recorded `loss` is that step's window mean. Names come from `checkpoint_name(config.checkpoint_name_prefix, step)`.
- `save_checkpoint(self, name, step, epoch, loss, *, reasons=("interval",), batch_size=0, gradient_accumulation_steps=0, batches_completed=0, dataset_signature="")` fills the new `CheckpointInfo` fields and is idempotent by name: when `self._checkpoints` already ends with an entry of the same `name`, it replaces that entry in place (merging reasons through `canonical_reasons`, taking the new `loss`) instead of appending.
- `load_checkpoint(checkpoint)` keeps the whole `CheckpointInfo` (replacing `_resume_from_step`/`_resume_from_epoch`) for the next `train()` to plan against.
- The old `total_steps = steps_per_epoch * epochs` arithmetic, the old two-name checkpoint writes and the old resume position arithmetic all go away.

### `trainer/fireworks_trainer.py`
- Same keyword-only `clock` / `rng` injection and `config.seed` default; the `time.sleep` in `_mock_train` and its use of the global RNG are deleted.

### Out of scope
`data_formatter.py`, `fireworks_data_formatter.py`, `status_tracker.py` and `base_trainer.py` do not change; `_get_batch_token_count`, `_get_effective_target_weight`, `_prepare_batch`, `format_example`, `save_weights` and the sampling helpers keep their current behaviour.
