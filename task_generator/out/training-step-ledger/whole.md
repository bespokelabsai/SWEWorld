# A step ledger for fine-tuning: one unit, one checkpoint identity, one resume contract

## Target

**Files that change**

| Path | Change |
|---|---|
| `src/bespokelabs/curator/finetune/step_ledger.py` | **new module** — the whole accounting: the step unit, `plan_steps`, `StepPlan` and its derived tuples, `dataset_signature`, `learning_rate_at`, `canonical_reasons`, `plan_resume`, `ResumePlan`, and the exception family. |
| `src/bespokelabs/curator/finetune/types.py` | `CheckpointInfo` gains five fields; `TrainingStats` gains two; `TrainingResult` gains two. All appended, all defaulted. |
| `src/bespokelabs/curator/finetune/config.py` | `TinkerTrainerConfig.seed` and `FireworksTrainerConfig.seed`. |
| `src/bespokelabs/curator/finetune/trainer/tinker_trainer.py` | `__init__` takes an injected clock and RNG; `train()` (`:251`) is rebuilt on the plan; `save_checkpoint` (`:143`) gains keyword-only ledger fields and merges by name; `load_checkpoint` (`:189`) keeps the whole `CheckpointInfo`; `_get_learning_rate` (`:536`) delegates to `learning_rate_at`; `_training_step` (`:443`) loses `random.random()` and `time.sleep`; the post-loop flush (`:395-409`) is deleted. |
| `src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py` | `__init__` takes the same injected clock and RNG; `_mock_train` (`:435`) loses its sleep and its global RNG; both `TrainingResult`s carry a packed plan instead of `total_steps=0`. |

`data_formatter.py`, `status_tracker.py`, `base_trainer.py` and `fireworks_data_formatter.py` do not change.

**Existing machinery that may be REUSED**

- `DataFormatter.format_batch` / `to_tinker_datum` (`data_formatter.py:161`, `:108`) — untouched, including the `tokenizer is None` branch that yields `{"model_input": [...], "loss_fn_inputs": {...}, "metadata": {...}}` dicts.
- `TinkerTrainer._get_batch_token_count` (`:492`) and `_get_effective_target_weight` (`:503`) — untouched; the loss-normalisation behaviour asserted by `tests/finetune/test_trainer.py:225-276` stays exactly as it is.
- `TinkerTrainer._prepare_batch` (`:239`), `format_example` (`:226`), `save_weights` (`:551`), `sample`, `get_sampling_client` — untouched apart from `save_weights`' clock.
- `FinetuneStatusTracker` (`status_tracker.py:21`) — constructed and fed exactly as now, with different numbers; its own `start_time: field(default_factory=time.time)` is not our clock and is not counted.
- `xxhash.xxh64` (a direct dependency, already used by `llm/llm.py`) as the only digest.
- `TinkerTrainerConfig` fields `batch_size`, `epochs`, `gradient_accumulation_steps`, `warmup_steps`, `log_every_n_steps`, `checkpoint_every_n_steps`, `checkpoint_every_epoch`, `checkpoint_name_prefix`, `adam_params.learning_rate` — same names, same defaults, new units.
- `pytest`, `monkeypatch`; `tinker_trainer_module.FinetuneStatusTracker` is monkeypatchable exactly the way `tinker_trainer_module.TINKER_AVAILABLE` already is in the existing tests.

**What must be BUILT**

- `step_ledger.py`: `STEP_UNIT_OPTIMIZER`, `STEP_UNIT_PACKED`, `MIN_LR_RATIO`, `CHECKPOINT_REASONS`, `CHECKPOINT_NAME_TEMPLATE`, `DATASET_SIGNATURE_PREFIX`; `StepLedgerError`, `ResumePlanMismatch`; frozen dataclasses `StepPlan`, `ResumePlan`; functions `dataset_signature`, `plan_steps`, `plan_steps_for_config`, `plan_packed_steps`, `checkpoint_name`, `canonical_reasons`, `learning_rate_at`, `plan_resume`.
- `types.py`: the twelve new dataclass fields, all with defaults so every existing construction site keeps working.
- `config.py`: `seed` on both configs.
- The two trainers' constructor injection and the rewritten `TinkerTrainer.train` loop.

**Python / dependencies**

Python `^3.10` (verified against 3.10.12). `tuple[str, ...]`, `dataclasses(frozen=True)`, keyword-only `*` parameters available; no `from __future__ import annotations` needed. Dependencies already present: `xxhash ^3.5.0`, `pydantic >=2.9.2`, stdlib `json`/`math`/`random`/`dataclasses`/`typing`. **No new dependency.** `tinker` is optional and is *not* installed in the test environment, so `TINKER_AVAILABLE is False` and every trainer runs its mock branch. `step_ledger.py` imports neither `time` nor `datetime` nor `random`.

**Latent bugs in this area (all real, with lines)**

1. `tinker_trainer.py:271-272` vs `:334-338` — `total_steps` counts batches while `should_optim_step` counts optimizer steps. With `gradient_accumulation_steps=4`, `TrainingResult.total_steps` is 4× the number of optimizer steps actually taken, and the progress bar's denominator (`:288`) is wrong by the same factor. Fixed by P2/P3.
2. `tinker_trainer.py:536-551` — `_get_learning_rate(step, total_steps)` never reads `total_steps`; the schedule its docstring promises does not exist. Fixed by P4.
3. `tinker_trainer.py:395-409` — the trailing accumulation flush is guarded by `self._training_client is not None and TINKER_AVAILABLE` and wrapped in `except Exception: logger.warning`. In mock mode (the only mode the tests can reach) a final partial window contributes to no optimizer step at all, silently. Fixed by P3.
4. `tinker_trainer.py:304-316` — resume rebuilds a position from `(resume_epoch - 1) * steps_per_epoch`, assuming 1-based epochs and an unchanged `steps_per_epoch`, while `types.py:54-62` records neither `batch_size` nor `gradient_accumulation_steps` nor anything identifying the data. Halving `batch_size` between runs silently replays or skips examples. Fixed by P6/P8.
5. `tinker_trainer.py:318` + `:335` — `current_step = resume_step` then `_get_learning_rate(current_step, total_steps)`: a resumed run re-enters warmup if `resume_step < warmup_steps`, and the flat post-warmup rate hides it. Fixed by P4/P8.
6. `tinker_trainer.py:363-364` vs `:382-384` — a step-interval checkpoint and an epoch checkpoint that land on the same state are written twice, under two names, and `save_checkpoint` (`:143-188`) appends unconditionally. Fixed by P7.
7. `tinker_trainer.py:358-360` vs `:372-376` — `loss_history` mixes a running epoch average logged every `log_every_n_steps` batches with a whole-epoch average, and the "was the last step already logged" guard compares a *global* step counter against a *per-epoch* average, so with `epochs=3, batch_size=3, num_examples=10, log_every_n_steps=4` epoch 1 contributes one entry and epoch 3 contributes two. Fixed by P9.
8. `tinker_trainer.py:483` + `:488` — the pure mock branch calls the module-global `random.random()` and `time.sleep(0.01)`; `:261`, `:414` and `:420` call `time.time()`. Fixed by P10.
9. `fireworks_trainer.py:291` and `:446` — `total_steps=0` unconditionally, in both the real and the mock path; `:439` sleeps and `:442` draws from the global RNG. Fixed by P11.

## The API

`src/bespokelabs/curator/finetune/step_ledger.py`

```python
"""The step ledger: what a training step counts, and what a resume must be told."""

import json
import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Tuple

from xxhash import xxh64

if TYPE_CHECKING:                       # step_ledger is a leaf: no runtime import of
    from bespokelabs.curator.finetune.config import TinkerTrainerConfig   # config or types,
    from bespokelabs.curator.finetune.types import CheckpointInfo         # which import it.

STEP_UNIT_OPTIMIZER: str = "optimizer_step"
STEP_UNIT_PACKED: str = "packed_epoch_step"
MIN_LR_RATIO: float = 0.1
CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")
CHECKPOINT_NAME_TEMPLATE: str = "{prefix}-s{step:06d}"
DATASET_SIGNATURE_PREFIX: str = "ds1"


class StepLedgerError(ValueError):
    """Base class for every step-accounting failure."""


class ResumePlanMismatch(StepLedgerError):
    """Raised when a checkpoint cannot be resumed into the run that was configured."""

    def __init__(self, checkpoint_name: str, mismatched_fields: Tuple[str, ...],
                 expected: Mapping[str, Any], found: Mapping[str, Any]) -> None:
        self.checkpoint_name: str = checkpoint_name
        self.mismatched_fields: Tuple[str, ...] = tuple(mismatched_fields)
        self.expected: dict = dict(expected)
        self.found: dict = dict(found)
        super().__init__(
            f"checkpoint {checkpoint_name!r} cannot resume this run; "
            f"differing: {', '.join(self.mismatched_fields)}"
        )


@dataclass(frozen=True)
class StepPlan:
    step_unit: str
    num_examples: int
    batch_size: int
    epochs: int
    gradient_accumulation_steps: int
    batches_per_epoch: int
    total_batches: int
    total_steps: int
    trailing_window_batches: int
    dataset_signature: str

    def step_of_batch(self, batch_ordinal: int) -> int: ...          # 1-based in, 1-based out
    def is_step_boundary(self, batch_ordinal: int) -> bool: ...      # 1-based in
    def epoch_of_batch(self, batch_ordinal: int) -> int: ...         # 1-based in, 1-based out
    def batch_slice(self, batch_ordinal: int) -> Tuple[int, int]: ...  # (start, end) into the example list
    def epoch_final_steps(self) -> Tuple[int, ...]: ...
    def logging_steps(self, log_every_n_steps: int) -> Tuple[int, ...]: ...
    def loss_history_steps(self, log_every_n_steps: int) -> Tuple[int, ...]: ...
    def interval_steps(self, checkpoint_every_n_steps: int) -> Tuple[int, ...]: ...


@dataclass(frozen=True)
class ResumePlan:
    checkpoint_name: str
    start_batch_ordinal: int      # 0-based; the next batch to run is this many batches in
    start_epoch: int              # 1-based
    start_batch_in_epoch: int     # 0-based
    completed_steps: int
    remaining_batches: int


def dataset_signature(examples: Sequence[Mapping[str, Any]]) -> str: ...

def plan_steps(num_examples: int, *, batch_size: int, epochs: int,
               gradient_accumulation_steps: int = 1,
               dataset_signature: str = "") -> StepPlan: ...

def plan_steps_for_config(config: "TinkerTrainerConfig",
                          examples: Sequence[Mapping[str, Any]]) -> StepPlan: ...

def plan_packed_steps(num_examples: int, *, epochs: int,
                      dataset_signature: str = "") -> StepPlan: ...

def checkpoint_name(prefix: str, step: int) -> str: ...

def canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]: ...

def learning_rate_at(step: int, total_steps: int, base_lr: float, warmup_steps: int,
                     *, min_lr_ratio: float = MIN_LR_RATIO) -> float: ...

def plan_resume(plan: StepPlan, checkpoint: "CheckpointInfo") -> ResumePlan: ...
```

`src/bespokelabs/curator/finetune/types.py`

```python
@dataclass
class CheckpointInfo:
    name: str
    path: str
    step: int
    epoch: int
    loss: float
    batch_size: int = 0
    gradient_accumulation_steps: int = 0
    batches_completed: int = 0
    dataset_signature: str = ""
    reasons: Tuple[str, ...] = ()


@dataclass
class TrainingStats:
    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0          # completed optimizer steps
    total_steps: int = 0           # optimizer steps
    current_loss: float = 0.0
    tokens_processed: int = 0
    samples_processed: int = 0
    learning_rate: float = 0.0
    elapsed_time: float = 0.0
    current_batch: int = 0         # 1-based batch ordinal just finished
    total_batches: int = 0


@dataclass
class TrainingResult:
    ...                            # nine existing fields, unchanged, in order
    total_batches: int = 0
    step_plan: Optional[StepPlan] = None
```

`src/bespokelabs/curator/finetune/config.py`

```python
class TinkerTrainerConfig(BaseModel):
    ...
    seed: int = Field(default=0, ge=0)

class FireworksTrainerConfig(BaseModel):
    ...
    seed: int = Field(default=0, ge=0)
```

`src/bespokelabs/curator/finetune/trainer/tinker_trainer.py`

```python
class TinkerTrainer(BaseTrainer):
    def __init__(self, config: TinkerTrainerConfig, *,
                 clock: Optional[Callable[[], float]] = None,
                 rng: Optional[random.Random] = None) -> None: ...
        # self._clock = clock if clock is not None else time.time
        # self._rng = rng if rng is not None else random.Random(config.seed)
        # self._resume_from: Optional[CheckpointInfo] = None

    def save_checkpoint(self, name: str, step: int, epoch: int, loss: float, *,
                        reasons: Sequence[str] = ("interval",),
                        batch_size: int = 0,
                        gradient_accumulation_steps: int = 0,
                        batches_completed: int = 0,
                        dataset_signature: str = "") -> Optional[CheckpointInfo]: ...

    def load_checkpoint(self, checkpoint: CheckpointInfo) -> bool: ...
    def _get_learning_rate(self, step: int, total_steps: int) -> float: ...
    def train(self, dataset: Any) -> TrainingResult: ...
```

`src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py`

```python
class FireworksTrainer(BaseTrainer):
    def __init__(self, config: FireworksTrainerConfig, *,
                 clock: Optional[Callable[[], float]] = None,
                 rng: Optional[random.Random] = None) -> None: ...
```

## Parts

### P1 — The `step_ledger` module surface

**Behaviour.** Every accounting decision lives in one new module, `bespokelabs/curator/finetune/step_ledger.py`, exporting exactly the names above. `StepPlan` and `ResumePlan` are **frozen dataclasses** — not pydantic models, not `NamedTuple`s, not dicts — with the field names and orders given. `StepLedgerError` subclasses **`ValueError`** (not `Exception`, not `RuntimeError`), and `ResumePlanMismatch` subclasses `StepLedgerError` and carries `checkpoint_name`, `mismatched_fields`, `expected`, `found`. The dependency direction is one-way: `types.py` and both trainers import `step_ledger`, and `step_ledger` imports neither at runtime — `plan_resume` and `plan_steps_for_config` are annotated under `TYPE_CHECKING` and read their arguments' attributes, so `TrainingResult.step_plan: Optional[StepPlan]` does not create a cycle. The module is import-clean without `tinker` installed and reads no clock and no global RNG.

**Alternatives a competent engineer would plausibly choose instead.**
1. Put it all on the trainer as private helpers — `TinkerTrainer._plan_steps`, `_resume_position` — next to the arithmetic that is there today. There is no `finetune/` utility module, the numbers are used in exactly one method, and a new top-level module for eight functions looks like over-engineering.
2. Make the plan a pydantic `BaseModel` (`config.py` and `types.py` are half pydantic already, and `SamplingConfig`/`TinkerTrainerConfig` set the house style) or a plain `dict` returned from a helper, since it is only read.
3. Raise `RuntimeError`/`ValueError` directly with a message and skip the exception family entirely — nothing in `finetune/` defines a single custom exception today (`data_formatter.py:58` raises a bare `ValueError`).

**The observable.**
`from bespokelabs.curator.finetune.step_ledger import StepPlan, ResumePlan, StepLedgerError, ResumePlanMismatch, plan_steps, plan_steps_for_config, plan_packed_steps, plan_resume, dataset_signature, learning_rate_at, canonical_reasons, checkpoint_name, STEP_UNIT_OPTIMIZER, STEP_UNIT_PACKED, MIN_LR_RATIO, CHECKPOINT_REASONS, CHECKPOINT_NAME_TEMPLATE, DATASET_SIGNATURE_PREFIX` imports cleanly;
`dataclasses.is_dataclass(StepPlan) and dataclasses.is_dataclass(ResumePlan)`;
`[f.name for f in dataclasses.fields(StepPlan)] == ["step_unit", "num_examples", "batch_size", "epochs", "gradient_accumulation_steps", "batches_per_epoch", "total_batches", "total_steps", "trailing_window_batches", "dataset_signature"]` (length 10);
`[f.name for f in dataclasses.fields(ResumePlan)] == ["checkpoint_name", "start_batch_ordinal", "start_epoch", "start_batch_in_epoch", "completed_steps", "remaining_batches"]` (length 6);
`issubclass(StepLedgerError, ValueError) and issubclass(ResumePlanMismatch, StepLedgerError)`;
`pytest.raises(dataclasses.FrozenInstanceError)` when assigning to `plan.total_steps`;
`STEP_UNIT_OPTIMIZER == "optimizer_step"`, `STEP_UNIT_PACKED == "packed_epoch_step"`, `MIN_LR_RATIO == 0.1`, `CHECKPOINT_REASONS == ("interval", "epoch", "final")`, `CHECKPOINT_NAME_TEMPLATE == "{prefix}-s{step:06d}"`, `DATASET_SIGNATURE_PREFIX == "ds1"`;
and an AST scan of `step_ledger.py` finds no import of `time`, `datetime` or `random`, and every `import`/`from ... import` statement whose module name contains `finetune.types` or `finetune.config` sits inside an `if TYPE_CHECKING:` block (the parent package `finetune/__init__.py` imports both eagerly, so `sys.modules` cannot be used to check this — the assertion is on the AST of `step_ledger.py` alone).

**Arbitrary:** invented name — the module path, two dataclass names, sixteen field names, two exception names and six constant spellings; nothing in the repository hints at any of them.

### P2 — One unit: an accumulation window spans epochs, and the last one is short

**Behaviour.** `plan_steps` fixes the unit of `total_steps`, `warmup_steps`, `log_every_n_steps` and `checkpoint_every_n_steps` as the **optimizer step**, and computes: `batches_per_epoch = ceil(num_examples / batch_size)`; `total_batches = batches_per_epoch * epochs`; and `total_steps = ceil(total_batches / gradient_accumulation_steps)` — the accumulation window is counted over the **whole run**, so it **runs across the epoch boundary** and is never reset at the end of an epoch. `trailing_window_batches = total_batches - (total_steps - 1) * gradient_accumulation_steps` (i.e. `gradient_accumulation_steps` when the run divides evenly, otherwise the short remainder, which still counts as one whole optimizer step). `step_of_batch(b) = ceil(b / gas)`, `epoch_of_batch(b) = (b - 1) // batches_per_epoch + 1`, `batch_slice(b)` maps a 1-based global ordinal onto `[start, end)` within the example list. `plan_steps` raises `StepLedgerError` when `num_examples == 0` (a run with nothing to train on is a configuration error, not a zero-step success) and when any of `batch_size`, `epochs`, `gradient_accumulation_steps` is `< 1`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the batch as the unit — extend `steps_per_epoch = ceil(num_examples/batch_size)`, `total_steps = steps_per_epoch * epochs` (`:271-272`, the code as written) and simply document that a "step" is a batch. Every existing field name then keeps its current meaning and only `should_optim_step` is odd.
2. Reset the accumulation window at each epoch boundary: `steps_per_epoch = ceil(batches_per_epoch / gas)`, `total_steps = steps_per_epoch * epochs`. This is what most training loops do — an epoch is a natural flush point, and it keeps "steps per epoch" a meaningful number. With `num_examples=10, batch_size=3, epochs=2, gas=3` it gives **4**, not 3.
3. Drop the trailing partial window: `total_steps = total_batches // gas` (floor), which is what a loop that only steps on `b % gas == 0` actually does today. With the same numbers it gives **2**.
4. Treat an empty dataset as a legal zero-step run returning a `StepPlan` of zeros — the current code happily runs zero batches and returns `final_loss=0.0`.

**The observable.** `p = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3)`:
`(p.batches_per_epoch, p.total_batches, p.total_steps, p.trailing_window_batches) == (4, 8, 3, 2)`;
`[p.step_of_batch(b) for b in range(1, 9)] == [1, 1, 1, 2, 2, 2, 3, 3]`;
`[p.is_step_boundary(b) for b in range(1, 9)] == [False, False, True, False, False, True, False, True]`;
`[p.epoch_of_batch(b) for b in range(1, 9)] == [1, 1, 1, 1, 2, 2, 2, 2]`;
`[p.batch_slice(b) for b in range(1, 9)] == [(0,3),(3,6),(6,9),(9,10),(0,3),(3,6),(6,9),(9,10)]`;
`plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=4).total_steps == 2` and `.trailing_window_batches == 4`;
`plan_steps(12, batch_size=4, epochs=1).total_steps == 3` and `.trailing_window_batches == 1`;
`p.step_unit == "optimizer_step"`;
`pytest.raises(StepLedgerError)` for `plan_steps(0, batch_size=3, epochs=2)` and for `gradient_accumulation_steps=0`.

**Arbitrary:** deliberate departure + policy with no local evidence — the source plainly computes `steps_per_epoch * epochs` in batches, and both "reset the window each epoch" and "floor away the remainder" are what the loop at `:334-338`/`:395-409` actually does. The epoch-spanning window and the `StepLedgerError` on an empty dataset have no evidence anywhere in the repo.

### P3 — The loop: one optimizer step per boundary, the short final window included

**Behaviour.** The training loop walks batches by their global 1-based ordinal `b` and calls `_training_step(..., should_optim_step=plan.is_step_boundary(b))`. The final batch of the run is a boundary by definition of `total_steps`, so the short trailing window is stepped **inside** the loop — the post-loop flush at `:395-409`, with its `TINKER_AVAILABLE` guard and its swallowing `except Exception`, is deleted, and the flush therefore happens in mock mode too. Exactly one `TrainingStats` is pushed to the status tracker per batch, **after** that batch's optional optimizer step, carrying `current_batch = b`, `current_step` = the number of optimizer steps *completed so far* (so it stays flat inside a window), `total_steps = plan.total_steps`, `total_batches = plan.total_batches`, `current_epoch = plan.epoch_of_batch(b)`, and `learning_rate` = the rate of the step this batch belongs to. `FinetuneStatusTracker` is constructed with `total_steps=plan.total_steps`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep pushing `current_step` as the batch counter (`:334`, `:342-351`) — the tracker's bar then advances once per batch, which looks better and is what the existing code does.
2. Push a stats record only on optimizer steps, so the number of `update()` calls equals `total_steps` — arguably the honest thing once the unit is the optimizer step.
3. Report `current_step` as the step *in progress* (1-based: `plan.step_of_batch(b)`) rather than steps completed, so the first batch reports `1` instead of `0`.
4. Keep the post-loop flush where it is but drop the `TINKER_AVAILABLE` guard.

**The observable.** With `FinetuneStatusTracker` monkeypatched on `tinker_trainer_module` by a recorder that appends every `stats` it is handed, and `num_examples=10, batch_size=3, epochs=2, gradient_accumulation_steps=3`:
`len(recorder.stats) == 8`;
`[(s.current_batch, s.current_step) for s in recorder.stats] == [(1,0),(2,0),(3,1),(4,1),(5,1),(6,2),(7,2),(8,3)]`;
`[s.current_epoch for s in recorder.stats] == [1,1,1,1,2,2,2,2]`;
`{s.total_steps for s in recorder.stats} == {3}` and `{s.total_batches for s in recorder.stats} == {8}`;
`recorder.init_kwargs["total_steps"] == 3`;
and with `_training_step` wrapped to record its `should_optim_step` argument, `recorded == [False, False, True, False, False, True, False, True]` — three `True`s, the last of them on batch 8.

**Arbitrary:** policy with no local evidence — the `(current_batch, current_step)` pairing and the completed-steps convention are unguessable, and the mock-mode flush is the opposite of `:395-409`. Honest caveat: *that a final flush should exist at all* is partly derivable, since `:395-409` already attempts one; what is not derivable is that it becomes an ordinary in-loop boundary counted in `total_steps`.

### P4 — Warmup is inclusive and 1-based; after it, linear decay to a tenth

**Behaviour.** `learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio=MIN_LR_RATIO)` finally uses `total_steps`. `effective_warmup = min(warmup_steps, total_steps)`. For `1 <= step <= effective_warmup` (when `effective_warmup > 0`): `base_lr * step / effective_warmup` — warmup is **inclusive**, so the step numbered `warmup_steps` is the first step at the full base rate, and the first optimizer step is never zero. For `step > effective_warmup`: `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)` and `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)` — a linear decay whose **floor is `MIN_LR_RATIO = 0.1` of the base rate**, reached exactly at `step == total_steps` and clamped (never lower) beyond it. `step < 1` raises `StepLedgerError`. `TinkerTrainer._get_learning_rate(step, total_steps)` keeps its signature and delegates, passing `config.adam_params.learning_rate` and `config.warmup_steps`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the flat post-warmup rate (`:550`, the code today) and just make `warmup_steps` count optimizer steps — the docstring says "with optional warmup", nothing says "decay".
2. Decay to **zero**, not to a tenth: `lr = base_lr * (1 - progress)`, which is what "linear schedule with warmup" means in every mainstream trainer.
3. Keep the exclusive comparison `step < warmup_steps` with `step / warmup_steps` (`:548-549`, the code today), so step `warmup_steps` is the first post-warmup step, or make warmup 0-based so the first step is `0.0`.
4. Use cosine decay, the other obvious default.

**The observable.** With `base_lr=1e-4`:
`[learning_rate_at(s, 8, 1e-4, 2) for s in range(1, 9)] == pytest.approx([5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], rel=1e-12)`;
`learning_rate_at(8, 8, 1e-4, 2) == pytest.approx(1e-05)` and `learning_rate_at(99, 8, 1e-4, 2) == pytest.approx(1e-05)` (clamped, never below the floor);
`[learning_rate_at(s, 4, 1e-4, 0) for s in range(1, 5)] == pytest.approx([7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12)` (no warmup: decay starts immediately);
`[learning_rate_at(s, 3, 1e-4, 10) for s in range(1, 4)] == pytest.approx([1e-4/3, 2e-4/3, 1e-04], rel=1e-12)` (warmup longer than the run is clipped to it, and there is no decay);
`pytest.raises(StepLedgerError)` for `learning_rate_at(0, 8, 1e-4, 2)`.

**Arbitrary:** chosen value + deliberate departure — `0.1` as the floor is a number nothing in the repo suggests; the inclusive 1-based warmup contradicts `:548`; and a decay at all contradicts `:550`, which returns `base_lr` flat forever.

### P5 — `dataset_signature`: what "the same data" means

**Behaviour.** `dataset_signature(examples)` returns `f"ds1-{len(examples)}-{xxh64(payload).hexdigest()}"` where `payload = json.dumps(list(examples), sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True).encode("utf-8")`. It is a function of the **content of every example, in order** — reordering the dataset changes it; changing a single character changes it; `sort_keys=True` makes it independent of dict insertion order; `default=str` keeps non-JSON values (e.g. `datetime`) from raising. The example count is carried in cleartext in front of the digest so a mismatch is legible without recomputation.

**Alternatives a competent engineer would plausibly choose instead.**
1. Use `len(examples)` alone, or `(len(examples), batch_size)` — the resume bug is about *shape*, and the cheap check is the row count. Hashing the whole dataset on every `train()` looks wasteful.
2. Reuse the `datasets` fingerprint (`dataset._fingerprint`), which the library already relies on elsewhere and which is free for a HF `Dataset` — but is absent for the list-of-dicts input this trainer also accepts.
3. `hashlib.sha256(repr(examples).encode()).hexdigest()`, or `xxh64` over `str(examples)` — same idea, different bytes, and `repr` of a dict is insertion-ordered.
4. Return the bare 16-char digest with no `ds1-` prefix and no count.

**The observable.** For `data = [{"messages": [{"role": "user", "content": f"Q{i}"}, {"role": "assistant", "content": f"A{i}"}]} for i in range(10)]`:
`dataset_signature(data) == "ds1-10-5d661fe8c9a2d002"` (exactly 23 characters);
`dataset_signature(data[:3]) == "ds1-3-b8c83761d026bfe8"`;
`dataset_signature(list(reversed(data))) != dataset_signature(data)`;
`dataset_signature([{"messages": [{"content": "Q0", "role": "user"}, {"role": "assistant", "content": "A0"}]}]) == dataset_signature([{"messages": [{"role": "user", "content": "Q0"}, {"content": "A0", "role": "assistant"}]}])` (key order irrelevant);
and the payload for `data` is 821 bytes beginning `'[{"messages":[{"content":"Q0","role":"user"},'`.

**Arbitrary:** invented name + chosen value — the function name, the `ds1-<count>-<digest>` format, and the exact canonicalisation (compact separators, `sort_keys`, `default=str`) that produces those two literal strings.

### P6 — A checkpoint records the shape it was taken in

**Behaviour.** `CheckpointInfo` gains five fields **appended in this order**: `batch_size`, `gradient_accumulation_steps`, `batches_completed`, `dataset_signature`, `reasons` — every one defaulted, so `CheckpointInfo(name=..., path=..., step=..., epoch=..., loss=...)` still constructs. `batches_completed` is the number of batches completed at that moment, counted globally across epochs, and is the **only** positional fact a resume uses. `step` is the optimizer step just completed. `epoch` is derived from the position, `plan.epoch_of_batch(batches_completed)` — **not** from the loop variable and **not** from whatever trigger fired: a checkpoint whose reasons include `"epoch"` may therefore record an `epoch` one greater than the epoch that ended, because the window that carried that epoch's last batch closed inside the next epoch. The checkpoint's `name` is `CHECKPOINT_NAME_TEMPLATE.format(prefix=config.checkpoint_name_prefix, step=step)` — `"checkpoint-s000002"` — the same name whatever triggered it, with the step zero-padded to six digits so names sort lexicographically.

**Alternatives a competent engineer would plausibly choose instead.**
1. Record the batch position not at all and keep reconstructing it from `step * gradient_accumulation_steps` — derivable, and one fewer field (this is what `:304-316` does today, from `step` and `epoch`).
2. Add the shape fields but keep the two existing name shapes, `f"{prefix}_step_{step}"` and `f"{prefix}_epoch_{epoch}"` (`:363`, `:383`) — they are already there, they are self-describing, and an unpadded step is what a human would write.
3. Set `epoch` from the `for epoch in range(...)` loop variable at the moment of the trigger — the obvious reading, and what the code does today at `:367` and `:386`.
4. Store the whole `StepPlan` on the checkpoint instead of four scalars.

**The observable.** After the End-to-end run:
`[f.name for f in dataclasses.fields(CheckpointInfo)] == ["name", "path", "step", "epoch", "loss", "batch_size", "gradient_accumulation_steps", "batches_completed", "dataset_signature", "reasons"]`;
`CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()` and `.batches_completed == 0`;
`checkpoint_name("checkpoint", 2) == "checkpoint-s000002"` and `checkpoint_name("ckpt", 1234567) == "ckpt-s1234567"`;
`[c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]`;
`[(c.step, c.epoch, c.batches_completed) for c in result.checkpoints] == [(2, 2, 6), (3, 2, 8)]` — note the first, which carries the `"epoch"` reason for the end of epoch **1**, records `epoch == 2`;
`[c.batch_size for c in result.checkpoints] == [3, 3]`, `[c.gradient_accumulation_steps for c in result.checkpoints] == [3, 3]`, `{c.dataset_signature for c in result.checkpoints} == {"ds1-10-5d661fe8c9a2d002"}`.

**Arbitrary:** invented name + policy with no local evidence — the five field names and their order, the `-s%06d` name template, and above all the rule that `epoch` describes the *position* rather than the trigger, which contradicts `:367`/`:386`.

### P7 — One checkpoint per optimizer step, reasons in ledger order, and a mandatory last one

**Behaviour.** Checkpoints are written **only at optimizer-step boundaries**. Three triggers can fire at a step `s`: `"interval"` when `checkpoint_every_n_steps > 0 and s % checkpoint_every_n_steps == 0`; `"epoch"` when `s` is in `plan.epoch_final_steps()` **and** `config.checkpoint_every_epoch` — an epoch whose last batch falls mid-window is deferred to the step that closes that window, never written mid-window; and `"final"` when `s == plan.total_steps`, which fires **regardless of configuration**, so every completed run ends with at least one checkpoint even under the default config (`checkpoint_every_n_steps=0`, `checkpoint_every_epoch=False`). A step with one or more triggers produces exactly **one** `save_checkpoint` call whose `reasons` is `canonical_reasons(...)`: deduplicated and ordered by `CHECKPOINT_REASONS` (`interval` before `epoch` before `final`), **not** alphabetically and not in the order the triggers were noticed; an unrecognised reason raises `StepLedgerError`. `save_checkpoint` itself is idempotent by name: when `self._checkpoints` already ends with a checkpoint of the same `name`, it **replaces that entry in place** (merging the reasons through `canonical_reasons`, taking the new `loss`) instead of appending, and returns the merged record.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep two independent writes and two names (`:363-364` and `:382-384`) — the code today; the epoch checkpoint even carries a different `loss` (the epoch average) so "they are the same state" is not obvious.
2. Write the epoch checkpoint at the epoch boundary regardless of the window (mid-accumulation), because "checkpoint at the end of each epoch" is what the config field says.
3. Sort reasons alphabetically — `("epoch", "final", "interval")` — the default any engineer reaches for when a set needs a stable order.
4. Write no final checkpoint when neither checkpoint option is enabled: the default config asks for no checkpoints and today produces none.
5. Deduplicate by scanning all of `self._checkpoints` for the name, or not at all.

**The observable.**
`canonical_reasons(("final", "epoch", "interval", "epoch")) == ("interval", "epoch", "final")`; `pytest.raises(StepLedgerError)` for `canonical_reasons(("periodic",))`;
End-to-end run (`checkpoint_every_n_steps=2`, `checkpoint_every_epoch=True`): `len(result.checkpoints) == 2` and `[c.reasons for c in result.checkpoints] == [("interval", "epoch"), ("epoch", "final")]`;
the same run with `checkpoint_every_n_steps=0, checkpoint_every_epoch=False`: `len(result.checkpoints) == 1`, `result.checkpoints[0].name == "checkpoint-s000003"`, `result.checkpoints[0].reasons == ("final",)`;
the default-config fixture of `tests/finetune/test_trainer.py:19-46` (2 examples, `batch_size=2`, `epochs=1`, so `total_batches == total_steps == 1`) yields exactly one checkpoint, `"checkpoint-s000001"`, with `reasons == ("final",)`, and exactly one `loss_history` entry, so `result.final_loss > 0` still holds;
and calling `trainer.save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))` then `trainer.save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.25, reasons=("final",))` leaves `len(trainer.get_checkpoints()) == 1` with `reasons == ("interval", "final")` and `loss == 0.25`.

**Arbitrary:** policy with no local evidence — deferring an epoch trigger to the window boundary, the unconditional `"final"` checkpoint, the ledger (non-alphabetical) reason order, and last-entry merge-by-name are four independent decisions the codebase is silent on and in two cases contradicts.

### P8 — Resume refuses a reshaped run, and restarts at the batch after the checkpoint

**Behaviour.** `load_checkpoint` stores the whole `CheckpointInfo` on `self._resume_from` (replacing `_resume_from_step`/`_resume_from_epoch`), and the next `train()` builds the plan for the *configured* run and calls `plan_resume(plan, checkpoint)`, which validates in a fixed order and raises `ResumePlanMismatch` out of `train()` — never a warning, never a silent restart:
1. **shape** — `batch_size`, `dataset_signature`, `gradient_accumulation_steps` compared against the plan; every differing name goes into `mismatched_fields`, **sorted alphabetically**. A checkpoint written before this feature (defaults `0`, `0`, `""`) therefore fails all three.
2. **exhaustion** — `checkpoint.batches_completed >= plan.total_batches` ⇒ `mismatched_fields == ("epochs",)`: resuming a finished run is an error, and raising `epochs` is the fix.
3. **consistency** — `checkpoint.step != plan.step_of_batch(checkpoint.batches_completed)` ⇒ `mismatched_fields == ("step",)`.
Otherwise the run restarts at **the batch after the checkpoint** — `start_batch_ordinal = checkpoint.batches_completed` (0-based) — not at the start of the checkpoint's epoch and not from scratch; `start_epoch = batches_completed // batches_per_epoch + 1`, `start_batch_in_epoch = batches_completed % batches_per_epoch`, `completed_steps = checkpoint.step`, `remaining_batches = total_batches - batches_completed`. Raising `epochs` alone is a legal resume: the plan grows, `total_steps` grows, and the learning rate continues down the *new* schedule from `completed_steps + 1` — warmup is behind it and is not re-entered. `self._resume_from` is cleared at the start of `train()`, so a second `train()` without a fresh `load_checkpoint` starts from zero.

**Alternatives a competent engineer would plausibly choose instead.**
1. Restart at the beginning of the checkpoint's epoch — the safe, common choice when you cannot trust a mid-epoch position, and cheap to implement.
2. Trust the arithmetic that is there (`:304-316`): derive a batch offset from `step` and `epoch` and carry on; warn (`logger.warning`) rather than raise when things look off, matching how every other failure in this file is handled (`:186`, `:210`, `:477`, `:408`).
3. Validate the row count only, or nothing at all, and let a reshaped dataset replay examples silently.
4. Treat a checkpoint at the very end of the run as a no-op resume that immediately returns a finished `TrainingResult`.
5. Restart `current_step` at `0` while skipping the completed batches, so warmup runs again — the current behaviour's practical effect.

**The observable.** With `plan = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3, dataset_signature="ds1-10-5d661fe8c9a2d002")` and `ck = CheckpointInfo(name="checkpoint-s000002", path="mock://checkpoints/checkpoint-s000002", step=2, epoch=2, loss=2.3, batch_size=3, gradient_accumulation_steps=3, batches_completed=6, dataset_signature="ds1-10-5d661fe8c9a2d002", reasons=("interval", "epoch"))`:
`plan_resume(plan, ck) == ResumePlan("checkpoint-s000002", 6, 2, 2, 2, 2)`;
against a plan built with `batch_size=5` **and** a different dataset: `exc.value.mismatched_fields == ("batch_size", "dataset_signature")` and `isinstance(exc.value, StepLedgerError)`;
against `CheckpointInfo(name="old", path="p", step=4, epoch=2, loss=1.0)` (pre-ledger): `exc.value.mismatched_fields == ("batch_size", "dataset_signature", "gradient_accumulation_steps")`;
with `batches_completed=8` on the same plan: `exc.value.mismatched_fields == ("epochs",)`;
with `epochs=3` in the plan and `batches_completed=8`: `plan_resume(...).remaining_batches == 4` and `.start_epoch == 3`;
with `ck.step` forced to `1`: `exc.value.mismatched_fields == ("step",)`;
and end to end, `trainer.load_checkpoint(ck); trainer.train(data)` returns `total_steps == 3`, `total_batches == 8`, `samples_processed == 4`, while `trainer.load_checkpoint(ck); trainer.train(data[:3])` raises `ResumePlanMismatch` with `mismatched_fields == ("dataset_signature",)`.

**Arbitrary:** policy with no local evidence + invented name — resume-at-the-next-batch, refuse-don't-warn, "epochs may grow but nothing else may change", the alphabetical `mismatched_fields`, and the three-stage check order are all choices the source neither makes nor hints at (it warns and continues everywhere else).

### P9 — One `loss_history` entry per marked optimizer step, and it is a window mean

**Behaviour.** `loss_history` has exactly one entry per optimizer step in `plan.loss_history_steps(config.log_every_n_steps)`, in ascending step order. That tuple is the sorted union of `plan.logging_steps(n)` (steps `s` with `s % n == 0`) and `plan.epoch_final_steps()` (for each epoch, the step that closes the window containing that epoch's last batch — which always includes `total_steps`). Each entry is the **arithmetic mean of the per-batch losses in that step's accumulation window** — not a running epoch average, not an epoch average, and no other quantity ever lands in the list. `TrainingResult.final_loss` is `loss_history[-1]`, i.e. the mean of the run's last window, and the `loss` recorded on a checkpoint at step `s` is that same window mean.

**Alternatives a competent engineer would plausibly choose instead.**
1. One entry per optimizer step, unconditionally — simplest once the unit is fixed, and `log_every_n_steps` then only controls logging.
2. Keep the current pair of appends: running epoch average every `n` steps plus a whole-epoch average at the end, guarded by "unless the last step was already logged" (`:358-360`, `:372-376`).
3. Record the running epoch mean at the marked steps (the current *value*, on the new schedule), rather than the window mean.
4. Use only `logging_steps` and drop the epoch-final marks, so a run whose `total_steps` is not a multiple of `log_every_n_steps` records nothing near the end.

**The observable.** `plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3)`:
`p.epoch_final_steps() == (2, 3)`; `p.logging_steps(2) == (2,)`; `p.loss_history_steps(2) == (2, 3)`; `p.loss_history_steps(1) == (1, 2, 3)`; `p.loss_history_steps(10) == (2, 3)`;
`plan_steps(10, batch_size=3, epochs=2).loss_history_steps(10) == (4, 8)` (so the existing `tests/finetune/test_trainer.py:109` assertion `len(result.loss_history) >= 2` still holds, with `len == 2`);
End-to-end: `result.loss_history == pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)` — the mean of batches 4-6 and the mean of batches 7-8, **not** the mean of batches 1-4 or 5-8;
`result.final_loss == pytest.approx(2.228222171221575)`;
`[c.loss for c in result.checkpoints] == pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)`.

**Arbitrary:** policy with no local evidence — "window mean" and the union-of-two-mark-sets are choices with no trace in the source, and alternative 1 (one entry per step) is at least as natural.

### P10 — The clock and the RNG are constructor arguments; `seed` defaults to 0

**Behaviour.** Both trainers take keyword-only `clock: Optional[Callable[[], float]] = None` and `rng: Optional[random.Random] = None`. `self._clock = clock if clock is not None else time.time`; `self._rng = rng if rng is not None else random.Random(config.seed)`, where `seed: int = Field(default=0, ge=0)` is a new field on both config classes — so **the mock trainer is reproducible out of the box**, with no test-side patching. The mock branch of `_training_step` draws **exactly one** `self._rng.random()` per batch, in batch order, and computes `2.5 - draw * 0.5`; the `time.sleep(0.01)` at `:488` is deleted, as is the one at `fireworks_trainer.py:439`. `TinkerTrainer.train` calls `self._clock()` exactly twice — once before the loop, once for `total_time` — and the `save_weights_on_complete` auto-name at `:420` becomes `int(self._clock())`, so a `save_weights_on_complete=True` run calls it three times in total (`:261`, `:414`, `:420`). `get_sampling_client`'s `int(time.time())` at `:596` is on the real-SDK path and is left alone. No module-level `random` or `time.time` call remains on any mock path.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep `import random` inside `_training_step` (`:481`) and let tests `random.seed(0)` or monkeypatch `random.random` — zero API change, and the existing test file already monkeypatches module attributes.
2. Inject a seed only (`TinkerTrainer(config, seed=0)`) rather than a `random.Random` instance, or read a seed from an env var.
3. Default `rng` to `random.Random()` (unseeded) so behaviour is unchanged unless a caller asks for determinism — the conservative choice, since seeding by default changes what every existing user sees.
4. Replace `time.sleep(0.01)` with a smaller sleep or leave it (it is only 10ms and it makes the mock progress bar look alive).

**The observable.** `TinkerTrainerConfig(base_model="m").seed == 0` and `FireworksTrainerConfig(base_model="m").seed == 0`; `pytest.raises(ValidationError)` for `seed=-1`.
Two trainers built from equal configs with no `rng` argument produce byte-identical `loss_history`, and for the End-to-end config the eight per-batch losses are exactly
`[2.077789074237476, 2.121022798529849, 2.2897142095845773, 2.3705416248535185, 2.2443626393156957, 2.2975329312747927, 2.1081007054826135, 2.348343636960536]`;
after `train()`, `trainer._rng.random() == pytest.approx(0.4765969541523558)` — the ninth draw of `random.Random(0)`, which pins the draw count to exactly eight;
with `clock=FakeClock([1000.0, 1004.5])` and `save_weights_on_complete=False`: `result.total_time == 4.5` and `fake.calls == 2`; with `save_weights_on_complete=True` and `FakeClock([1000.0, 1004.5, 1700000000.0])`: `fake.calls == 3` and `result.weights_name == "mock_weights_Qwen3-8B_lora_1700000000"`;
and an AST scan of `tinker_trainer.py` finds no `time.sleep` call and no `random.random` call that is not an attribute of `self._rng`.

**Arbitrary:** chosen value + policy with no local evidence — `seed` defaulting to `0` (rather than being unseeded), the keyword-only `clock`/`rng` names, one draw per *batch* rather than per step, and the exact clock-call count of two.

### P11 — Fireworks reports the packed-batch unit instead of zero

**Behaviour.** `plan_packed_steps(num_examples, *, epochs, dataset_signature="")` builds the third definition the codebase already documents at `config.py:93-96` — Fireworks packs examples into batches by token count, so a small dataset is **one optimizer step per epoch**: `step_unit=STEP_UNIT_PACKED`, `batch_size=num_examples`, `gradient_accumulation_steps=1`, `batches_per_epoch=1`, `total_batches=epochs`, `total_steps=epochs`, `trailing_window_batches=1`. Both `FireworksTrainer.train` (`:289`) and `_mock_train` (`:444`) build this plan and set `total_steps=plan.total_steps` and `step_plan=plan` instead of `total_steps=0`, and both metadata dicts gain exactly one key, `"step_unit"`, whose value is `"packed_epoch_step"`. `plan_packed_steps` raises `StepLedgerError` on `num_examples == 0`, matching `plan_steps`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `total_steps=0` — Fireworks is server-side, the client genuinely does not know how many steps ran, and `0` honestly says "unknown".
2. Report `total_steps=None` (the field is typed `int`, but `Optional` is a small change) or omit the plan and put the unit in `metadata` only.
3. Compute a batch count from `config.batch_size` when it is set (`ceil(num_examples/batch_size) * epochs`), falling back to `epochs` only when it is `None` — arguably more accurate, and `batch_size` is right there in the config.

**The observable.** `p = plan_packed_steps(2, epochs=5)`:
`(p.step_unit, p.batch_size, p.gradient_accumulation_steps, p.batches_per_epoch, p.total_batches, p.total_steps, p.trailing_window_batches) == ("packed_epoch_step", 2, 1, 1, 5, 5, 1)`;
`pytest.raises(StepLedgerError)` for `plan_packed_steps(0, epochs=5)`;
and for a mock `FireworksTrainer` (no API key) trained on 3 examples with `epochs=4, seed=0`:
`result.total_steps == 4`, `result.total_batches == 4`, `result.step_plan.step_unit == "packed_epoch_step"`, `result.metadata["step_unit"] == "packed_epoch_step"`, `sorted(result.metadata) == ["base_model", "mock", "provider", "step_unit"]`, and `result.final_loss == pytest.approx(2.077789074237476)` (the first draw of `random.Random(0)`).

**Arbitrary:** policy with no local evidence — that the Fireworks step unit is one packed step per *epoch*, and that this is reported through `total_steps` (which the code hard-codes to `0` in both branches) rather than left unknown.

## End to end

**Inputs.**

```python
import random
from bespokelabs.curator.finetune.config import TinkerTrainerConfig
from bespokelabs.curator.finetune.trainer import TinkerTrainer

data = [
    {"messages": [{"role": "user", "content": f"Q{i}"},
                  {"role": "assistant", "content": f"A{i}"}]}
    for i in range(10)
]

config = TinkerTrainerConfig(
    base_model="Qwen3-8B",
    epochs=2,
    batch_size=3,
    gradient_accumulation_steps=3,
    warmup_steps=2,
    log_every_n_steps=2,
    checkpoint_every_n_steps=2,
    checkpoint_every_epoch=True,
    save_weights_on_complete=False,
    seed=0,
    api_key=None,                      # mock mode; TINKER_API_KEY unset, tinker not installed
)

class FakeClock:
    def __init__(self, values): self.values = list(values); self.calls = 0
    def __call__(self):
        v = self.values[self.calls]; self.calls += 1; return v

clock = FakeClock([1000.0, 1004.5])
trainer = TinkerTrainer(config, clock=clock)     # rng defaults to random.Random(config.seed) == Random(0)
result = trainer.train(data)
```

**The plan.** `batches_per_epoch = ceil(10/3) = 4`; batch sizes per epoch `[3, 3, 3, 1]`; `total_batches = 8`; `total_steps = ceil(8/3) = 3`; `trailing_window_batches = 2`. Windows: step 1 = batches 1-3 (all epoch 1), step 2 = batches 4-6 (**spans the epoch boundary**: batch 4 is epoch 1, batches 5-6 are epoch 2), step 3 = batches 7-8. Learning rates: step 1 `5e-05`, step 2 `1e-04`, step 3 `1e-05`. Mock tokens: each example yields `len("<|user|>\nQ0\n<|assistant|>\nA0\n") // 4 == 7` tokens, minus one for the causal shift = 6 per example.

**Exact expected outputs.**

```python
result.total_steps            == 3
result.total_batches          == 8
result.total_epochs           == 2
result.samples_processed      == 20
result.tokens_processed       == 120
result.total_time             == 4.5
clock.calls                   == 2
result.weights_name           is None

result.step_plan == StepPlan(
    step_unit="optimizer_step", num_examples=10, batch_size=3, epochs=2,
    gradient_accumulation_steps=3, batches_per_epoch=4, total_batches=8,
    total_steps=3, trailing_window_batches=2,
    dataset_signature="ds1-10-5d661fe8c9a2d002",
)

result.loss_history == [2.304145731814669, 2.228222171221575]     # rel=1e-12
result.final_loss   == 2.228222171221575

result.metadata == {
    "base_model": "Qwen3-8B",
    "batch_size": 3,
    "learning_rate": 0.0001,
    "lora_rank": 16,
    "lora_alpha": 32,
    "gradient_accumulation_steps": 3,
    "dataset_signature": "ds1-10-5d661fe8c9a2d002",
}

result.checkpoints == [
    CheckpointInfo(name="checkpoint-s000002", path="mock://checkpoints/checkpoint-s000002",
                   step=2, epoch=2, loss=2.304145731814669, batch_size=3,
                   gradient_accumulation_steps=3, batches_completed=6,
                   dataset_signature="ds1-10-5d661fe8c9a2d002",
                   reasons=("interval", "epoch")),
    CheckpointInfo(name="checkpoint-s000003", path="mock://checkpoints/checkpoint-s000003",
                   step=3, epoch=2, loss=2.228222171221575, batch_size=3,
                   gradient_accumulation_steps=3, batches_completed=8,
                   dataset_signature="ds1-10-5d661fe8c9a2d002",
                   reasons=("epoch", "final")),
]

trainer._rng.random() == 0.4765969541523558      # ninth draw of Random(0): exactly 8 draws were made
```

**Then resume from the first checkpoint.**

```python
trainer2 = TinkerTrainer(config, clock=FakeClock([2000.0, 2001.0]))
assert trainer2.load_checkpoint(result.checkpoints[0]) is True
resumed = trainer2.train(data)

resumed.total_steps       == 3       # continued, not restarted
resumed.total_batches     == 8
resumed.samples_processed == 4       # batches 7 and 8 only: 3 + 1 examples
resumed.tokens_processed  == 24
resumed.loss_history      == [2.099405936383662]    # mean of the first two draws of a fresh
                                                    # Random(0) - the only window this run
                                                    # completes is step 3 (batches 7 and 8)
[c.name for c in resumed.checkpoints] == ["checkpoint-s000003"]
resumed.checkpoints[0].reasons        == ("epoch", "final")
```

**And two refusals.**

```python
trainer3 = TinkerTrainer(config); trainer3.load_checkpoint(result.checkpoints[0])
with pytest.raises(ResumePlanMismatch) as exc:
    trainer3.train(data[:6])
exc.value.mismatched_fields == ("dataset_signature",)
exc.value.checkpoint_name   == "checkpoint-s000002"

trainer4 = TinkerTrainer(config); trainer4.load_checkpoint(result.checkpoints[1])   # step 3, 8/8 batches
with pytest.raises(ResumePlanMismatch) as exc:
    trainer4.train(data)
exc.value.mismatched_fields == ("epochs",)
```
