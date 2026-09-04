#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/finetune/config.py b/src/bespokelabs/curator/finetune/config.py
index 93478fa..62b32b8 100644
--- a/src/bespokelabs/curator/finetune/config.py
+++ b/src/bespokelabs/curator/finetune/config.py
@@ -48,6 +48,8 @@ class TinkerTrainerConfig(BaseModel):
         checkpoint_every_n_steps: Save checkpoint every N steps (0 to disable)
         checkpoint_every_epoch: Save checkpoint at the end of each epoch
         checkpoint_name_prefix: Prefix for checkpoint names
+        seed: Seed for the trainer's random number generator, so a mock run is
+            reproducible without any test-side patching
     """
 
     base_model: str
@@ -64,6 +66,7 @@ class TinkerTrainerConfig(BaseModel):
     checkpoint_every_n_steps: int = Field(default=0, ge=0)
     checkpoint_every_epoch: bool = False
     checkpoint_name_prefix: str = "checkpoint"
+    seed: int = Field(default=0, ge=0)
 
     model_config = ConfigDict(extra="forbid")
 
@@ -119,6 +122,7 @@ class FireworksTrainerConfig(BaseModel):
         poll_interval_seconds: How often to poll the fine-tuning job for progress.
         max_wait_seconds: Maximum time to wait for a fine-tuning job to complete.
         inference_base_url: OpenAI-compatible base URL for inference.
+        seed: Seed for the trainer's random number generator, used by the mock path.
     """
 
     base_model: str
@@ -143,6 +147,7 @@ class FireworksTrainerConfig(BaseModel):
     poll_interval_seconds: int = Field(default=10, gt=0)
     max_wait_seconds: int = Field(default=3600, gt=0)
     inference_base_url: str = "https://api.fireworks.ai/inference/v1"
+    seed: int = Field(default=0, ge=0)
 
     model_config = ConfigDict(extra="forbid")
 
diff --git a/src/bespokelabs/curator/finetune/step_ledger.py b/src/bespokelabs/curator/finetune/step_ledger.py
new file mode 100644
index 0000000..6113513
--- /dev/null
+++ b/src/bespokelabs/curator/finetune/step_ledger.py
@@ -0,0 +1,417 @@
+"""The step ledger: what a training step counts, and what a resume must be told.
+
+A training run has exactly one unit of account, the *optimizer step*, and every
+number that is expressed in steps -- ``total_steps``, ``warmup_steps``,
+``log_every_n_steps``, ``checkpoint_every_n_steps`` -- is expressed in that unit.
+This module owns the arithmetic that turns a dataset size and a configuration into
+a :class:`StepPlan`, the learning-rate schedule that reads it, the dataset
+signature a checkpoint records, and the validation a resume has to pass.
+
+It is a leaf module: it imports neither the trainers nor the types and configs that
+import it, and it reads no clock and no global random number generator, so the same
+inputs always produce the same plan.
+"""
+
+import json
+import math
+from dataclasses import dataclass, replace
+from typing import TYPE_CHECKING, Any, Mapping, Sequence, Tuple
+
+from xxhash import xxh64
+
+if TYPE_CHECKING:  # pragma: no cover - imported for annotations only; both modules import this one.
+    from bespokelabs.curator.finetune.config import TinkerTrainerConfig
+    from bespokelabs.curator.finetune.types import CheckpointInfo
+
+STEP_UNIT_OPTIMIZER: str = "optimizer_step"
+STEP_UNIT_PACKED: str = "packed_epoch_step"
+MIN_LR_RATIO: float = 0.1
+CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")
+CHECKPOINT_NAME_TEMPLATE: str = "{prefix}-s{step:06d}"
+DATASET_SIGNATURE_PREFIX: str = "ds1"
+
+
+class StepLedgerError(ValueError):
+    """Base class for every step-accounting failure."""
+
+
+class ResumePlanMismatch(StepLedgerError):  # noqa: N818 - the ledger names this by what it means, not by its base
+    """Raised when a checkpoint cannot be resumed into the run that was configured."""
+
+    def __init__(
+        self,
+        checkpoint_name: str,
+        mismatched_fields: Tuple[str, ...],
+        expected: Mapping[str, Any],
+        found: Mapping[str, Any],
+    ) -> None:
+        """Initialize the mismatch.
+
+        Args:
+            checkpoint_name: Name of the checkpoint that was being resumed.
+            mismatched_fields: Names of the fields that disagree, sorted alphabetically.
+            expected: The values the configured run expects, keyed by field name.
+            found: The values the checkpoint carries, keyed by field name.
+        """
+        self.checkpoint_name: str = checkpoint_name
+        self.mismatched_fields: Tuple[str, ...] = tuple(mismatched_fields)
+        self.expected: dict = dict(expected)
+        self.found: dict = dict(found)
+        super().__init__(f"checkpoint {checkpoint_name!r} cannot resume this run; differing: {', '.join(self.mismatched_fields)}")
+
+
+@dataclass(frozen=True)
+class StepPlan:
+    """The complete accounting for one training run.
+
+    Attributes:
+        step_unit: What a step counts, either ``STEP_UNIT_OPTIMIZER`` or ``STEP_UNIT_PACKED``.
+        num_examples: Number of examples in the dataset.
+        batch_size: Number of examples per batch.
+        epochs: Number of passes over the dataset.
+        gradient_accumulation_steps: Batches accumulated into one optimizer step.
+        batches_per_epoch: Batches in a single pass over the dataset.
+        total_batches: Batches over the whole run.
+        total_steps: Optimizer steps over the whole run.
+        trailing_window_batches: Batches in the run's final accumulation window.
+        dataset_signature: Signature of the data this plan was built for.
+    """
+
+    step_unit: str
+    num_examples: int
+    batch_size: int
+    epochs: int
+    gradient_accumulation_steps: int
+    batches_per_epoch: int
+    total_batches: int
+    total_steps: int
+    trailing_window_batches: int
+    dataset_signature: str
+
+    def step_of_batch(self, batch_ordinal: int) -> int:
+        """Return the 1-based optimizer step the given 1-based batch belongs to."""
+        return math.ceil(batch_ordinal / self.gradient_accumulation_steps)
+
+    def is_step_boundary(self, batch_ordinal: int) -> bool:
+        """Whether the given 1-based batch closes an accumulation window.
+
+        The final batch of the run always closes a window, so a short trailing window
+        still produces a whole optimizer step.
+        """
+        if batch_ordinal >= self.total_batches:
+            return True
+        return batch_ordinal % self.gradient_accumulation_steps == 0
+
+    def epoch_of_batch(self, batch_ordinal: int) -> int:
+        """Return the 1-based epoch the given 1-based batch belongs to."""
+        return (batch_ordinal - 1) // self.batches_per_epoch + 1
+
+    def batch_slice(self, batch_ordinal: int) -> Tuple[int, int]:
+        """Return the ``[start, end)`` slice into the example list for a 1-based batch."""
+        index_in_epoch = (batch_ordinal - 1) % self.batches_per_epoch
+        start = index_in_epoch * self.batch_size
+        end = min(start + self.batch_size, self.num_examples)
+        return start, end
+
+    def epoch_final_steps(self) -> Tuple[int, ...]:
+        """Return the steps that close each epoch's last accumulation window.
+
+        An epoch whose last batch falls in the middle of an accumulation window is
+        represented by the step that closes that window, which may sit inside the next
+        epoch. The run's last step is always included.
+        """
+        steps = {self.step_of_batch(epoch * self.batches_per_epoch) for epoch in range(1, self.epochs + 1)}
+        return tuple(sorted(steps))
+
+    def logging_steps(self, log_every_n_steps: int) -> Tuple[int, ...]:
+        """Return the steps at which the run logs, every ``log_every_n_steps`` steps."""
+        if log_every_n_steps <= 0:
+            return ()
+        return tuple(step for step in range(1, self.total_steps + 1) if step % log_every_n_steps == 0)
+
+    def loss_history_steps(self, log_every_n_steps: int) -> Tuple[int, ...]:
+        """Return the steps that contribute an entry to ``loss_history``.
+
+        This is the union of :meth:`logging_steps` and :meth:`epoch_final_steps`, so a
+        run always records the end of every epoch even when it is not a logging step.
+        """
+        steps = set(self.logging_steps(log_every_n_steps)) | set(self.epoch_final_steps())
+        return tuple(sorted(steps))
+
+    def interval_steps(self, checkpoint_every_n_steps: int) -> Tuple[int, ...]:
+        """Return the steps at which an interval checkpoint fires (empty when disabled)."""
+        if checkpoint_every_n_steps <= 0:
+            return ()
+        return tuple(step for step in range(1, self.total_steps + 1) if step % checkpoint_every_n_steps == 0)
+
+
+@dataclass(frozen=True)
+class ResumePlan:
+    """Where a resumed run picks up.
+
+    Attributes:
+        checkpoint_name: Name of the checkpoint being resumed from.
+        start_batch_ordinal: 0-based; the next batch to run is this many batches in.
+        start_epoch: 1-based epoch the next batch belongs to.
+        start_batch_in_epoch: 0-based position of the next batch within its epoch.
+        completed_steps: Optimizer steps already completed.
+        remaining_batches: Batches still to run.
+    """
+
+    checkpoint_name: str
+    start_batch_ordinal: int
+    start_epoch: int
+    start_batch_in_epoch: int
+    completed_steps: int
+    remaining_batches: int
+
+
+def dataset_signature(examples: Sequence[Mapping[str, Any]]) -> str:
+    """Compute a signature identifying this exact dataset, in this exact order.
+
+    The signature is a function of every example's content: reordering the dataset or
+    changing a single character changes it, while the insertion order of the keys
+    within an example does not.
+
+    Args:
+        examples: The raw examples the run will train on.
+
+    Returns:
+        A string of the form ``"ds1-<count>-<digest>"``, where the count is carried in
+        cleartext so a mismatch is legible without recomputing anything.
+    """
+    payload = json.dumps(list(examples), sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True).encode("utf-8")
+    return f"{DATASET_SIGNATURE_PREFIX}-{len(examples)}-{xxh64(payload).hexdigest()}"
+
+
+def plan_steps(
+    num_examples: int,
+    *,
+    batch_size: int,
+    epochs: int,
+    gradient_accumulation_steps: int = 1,
+    dataset_signature: str = "",
+) -> StepPlan:
+    """Build the plan for a run whose unit of account is the optimizer step.
+
+    The accumulation window is counted over the whole run: it runs across epoch
+    boundaries and is never reset at the end of an epoch, and the run's final window
+    counts as one whole optimizer step even when it is short.
+
+    Args:
+        num_examples: Number of examples in the dataset; must be at least one.
+        batch_size: Number of examples per batch.
+        epochs: Number of passes over the dataset.
+        gradient_accumulation_steps: Batches accumulated into one optimizer step.
+        dataset_signature: Signature of the data this plan is built for.
+
+    Returns:
+        The :class:`StepPlan` for the run.
+
+    Raises:
+        StepLedgerError: If the dataset is empty or any of the sizes is less than one.
+    """
+    if num_examples < 1:
+        raise StepLedgerError(f"cannot plan a training run over {num_examples} examples; at least one example is required")
+    if batch_size < 1:
+        raise StepLedgerError(f"batch_size must be at least 1, got {batch_size}")
+    if epochs < 1:
+        raise StepLedgerError(f"epochs must be at least 1, got {epochs}")
+    if gradient_accumulation_steps < 1:
+        raise StepLedgerError(f"gradient_accumulation_steps must be at least 1, got {gradient_accumulation_steps}")
+
+    batches_per_epoch = math.ceil(num_examples / batch_size)
+    total_batches = batches_per_epoch * epochs
+    total_steps = math.ceil(total_batches / gradient_accumulation_steps)
+    trailing_window_batches = total_batches - (total_steps - 1) * gradient_accumulation_steps
+
+    return StepPlan(
+        step_unit=STEP_UNIT_OPTIMIZER,
+        num_examples=num_examples,
+        batch_size=batch_size,
+        epochs=epochs,
+        gradient_accumulation_steps=gradient_accumulation_steps,
+        batches_per_epoch=batches_per_epoch,
+        total_batches=total_batches,
+        total_steps=total_steps,
+        trailing_window_batches=trailing_window_batches,
+        dataset_signature=dataset_signature,
+    )
+
+
+def plan_steps_for_config(config: "TinkerTrainerConfig", examples: Sequence[Mapping[str, Any]]) -> StepPlan:
+    """Build the plan a :class:`~bespokelabs.curator.finetune.config.TinkerTrainerConfig` describes.
+
+    Args:
+        config: The trainer configuration for the run.
+        examples: The raw examples the run will train on.
+
+    Returns:
+        The :class:`StepPlan` for the run, signed with the dataset's signature.
+    """
+    return plan_steps(
+        len(examples),
+        batch_size=config.batch_size,
+        epochs=config.epochs,
+        gradient_accumulation_steps=config.gradient_accumulation_steps,
+        dataset_signature=dataset_signature(examples),
+    )
+
+
+def plan_packed_steps(num_examples: int, *, epochs: int, dataset_signature: str = "") -> StepPlan:
+    """Build the plan for a provider that packs examples into batches by token count.
+
+    Fireworks packs a small dataset into a single batch, so the unit of account is one
+    packed step per epoch.
+
+    Args:
+        num_examples: Number of examples in the dataset; must be at least one.
+        epochs: Number of passes over the dataset.
+        dataset_signature: Signature of the data this plan is built for.
+
+    Returns:
+        The :class:`StepPlan` for the run, with ``step_unit == STEP_UNIT_PACKED``.
+
+    Raises:
+        StepLedgerError: If the dataset is empty or ``epochs`` is less than one.
+    """
+    plan = plan_steps(
+        num_examples,
+        batch_size=max(num_examples, 1),
+        epochs=epochs,
+        gradient_accumulation_steps=1,
+        dataset_signature=dataset_signature,
+    )
+    return replace(plan, step_unit=STEP_UNIT_PACKED)
+
+
+def checkpoint_name(prefix: str, step: int) -> str:
+    """Return the checkpoint name for a step, whatever triggered it.
+
+    Args:
+        prefix: Configured checkpoint name prefix.
+        step: The optimizer step just completed.
+
+    Returns:
+        The checkpoint name, with the step zero-padded so names sort lexicographically.
+    """
+    return CHECKPOINT_NAME_TEMPLATE.format(prefix=prefix, step=step)
+
+
+def canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]:
+    """Deduplicate and order checkpoint reasons by :data:`CHECKPOINT_REASONS`.
+
+    Args:
+        reasons: The reasons a checkpoint was written, in any order.
+
+    Returns:
+        The same reasons, deduplicated and in ledger order.
+
+    Raises:
+        StepLedgerError: If any reason is not one of :data:`CHECKPOINT_REASONS`.
+    """
+    unknown = [reason for reason in reasons if reason not in CHECKPOINT_REASONS]
+    if unknown:
+        raise StepLedgerError(f"unknown checkpoint reason(s) {', '.join(repr(reason) for reason in unknown)}; expected one of {CHECKPOINT_REASONS}")
+    seen = set(reasons)
+    return tuple(reason for reason in CHECKPOINT_REASONS if reason in seen)
+
+
+def learning_rate_at(
+    step: int,
+    total_steps: int,
+    base_lr: float,
+    warmup_steps: int,
+    *,
+    min_lr_ratio: float = MIN_LR_RATIO,
+) -> float:
+    """Compute the learning rate for a 1-based optimizer step.
+
+    Warmup is inclusive: the step numbered ``warmup_steps`` is the first step at the
+    full base rate, and the first step is never zero. After warmup the rate decays
+    linearly, reaching ``min_lr_ratio * base_lr`` exactly at ``total_steps`` and never
+    going below it. A warmup longer than the run is clipped to the run.
+
+    Args:
+        step: The 1-based optimizer step.
+        total_steps: Total optimizer steps in the run.
+        base_lr: The configured peak learning rate.
+        warmup_steps: Number of warmup steps requested.
+        min_lr_ratio: Floor of the decay, as a fraction of ``base_lr``.
+
+    Returns:
+        The learning rate for that step.
+
+    Raises:
+        StepLedgerError: If ``step`` is less than one.
+    """
+    if step < 1:
+        raise StepLedgerError(f"step must be at least 1, got {step}")
+
+    effective_warmup = min(warmup_steps, total_steps)
+    if effective_warmup > 0 and step <= effective_warmup:
+        return base_lr * step / effective_warmup
+
+    progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)
+    return base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)
+
+
+def plan_resume(plan: StepPlan, checkpoint: "CheckpointInfo") -> ResumePlan:
+    """Validate a checkpoint against a configured run and locate where it restarts.
+
+    The run restarts at the batch *after* the checkpoint, not at the start of the
+    checkpoint's epoch. Raising ``epochs`` is a legal resume; anything else that
+    reshapes the run is refused.
+
+    Args:
+        plan: The plan for the run as it is configured now.
+        checkpoint: The checkpoint that was loaded.
+
+    Returns:
+        The :class:`ResumePlan` describing where the run picks up.
+
+    Raises:
+        ResumePlanMismatch: If the checkpoint was taken in a different shape, if the
+            run it belongs to is already finished, or if its step and batch position
+            disagree.
+    """
+    shape = {
+        "batch_size": (plan.batch_size, checkpoint.batch_size),
+        "dataset_signature": (plan.dataset_signature, checkpoint.dataset_signature),
+        "gradient_accumulation_steps": (plan.gradient_accumulation_steps, checkpoint.gradient_accumulation_steps),
+    }
+    mismatched = tuple(sorted(name for name, (expected, found) in shape.items() if expected != found))
+    if mismatched:
+        raise ResumePlanMismatch(
+            checkpoint.name,
+            mismatched,
+            {name: shape[name][0] for name in mismatched},
+            {name: shape[name][1] for name in mismatched},
+        )
+
+    batches_completed = checkpoint.batches_completed
+    if batches_completed >= plan.total_batches:
+        raise ResumePlanMismatch(
+            checkpoint.name,
+            ("epochs",),
+            {"epochs": plan.epochs},
+            {"epochs": checkpoint.epoch},
+        )
+
+    expected_step = plan.step_of_batch(batches_completed)
+    if checkpoint.step != expected_step:
+        raise ResumePlanMismatch(
+            checkpoint.name,
+            ("step",),
+            {"step": expected_step},
+            {"step": checkpoint.step},
+        )
+
+    return ResumePlan(
+        checkpoint_name=checkpoint.name,
+        start_batch_ordinal=batches_completed,
+        start_epoch=batches_completed // plan.batches_per_epoch + 1,
+        start_batch_in_epoch=batches_completed % plan.batches_per_epoch,
+        completed_steps=checkpoint.step,
+        remaining_batches=plan.total_batches - batches_completed,
+    )
diff --git a/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py b/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py
index 15b8ab8..7fea616 100644
--- a/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py
+++ b/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py
@@ -15,13 +15,15 @@ is available, the trainer runs in "mock mode" so examples and tests work offline
 
 import inspect
 import os
+import random
 import re
 import tempfile
 import time
-from typing import Any, Dict, List, Optional
+from typing import Any, Callable, Dict, List, Optional
 
 from bespokelabs.curator.finetune.config import FireworksTrainerConfig
 from bespokelabs.curator.finetune.fireworks_data_formatter import FireworksDataFormatter
+from bespokelabs.curator.finetune.step_ledger import STEP_UNIT_PACKED, plan_packed_steps
 from bespokelabs.curator.finetune.trainer.base_trainer import BaseTrainer
 from bespokelabs.curator.finetune.types import (
     SamplingConfig,
@@ -116,14 +118,25 @@ class FireworksTrainer(BaseTrainer):
         ```
     """
 
-    def __init__(self, config: FireworksTrainerConfig):
+    def __init__(
+        self,
+        config: FireworksTrainerConfig,
+        *,
+        clock: Optional[Callable[[], float]] = None,
+        rng: Optional[random.Random] = None,
+    ) -> None:
         """Initialize the FireworksTrainer.
 
         Args:
             config: FireworksTrainerConfig with training parameters.
+            clock: Callable returning the current time in seconds; defaults to ``time.time``.
+            rng: Random number generator for the mock training path; defaults to a
+                generator seeded with ``config.seed``, so mock runs are reproducible.
         """
         self.config = config
         self.data_formatter = FireworksDataFormatter()
+        self._clock: Callable[[], float] = clock if clock is not None else time.time
+        self._rng: random.Random = rng if rng is not None else random.Random(config.seed)
         self._output_model: Optional[str] = None
         self._job_name: Optional[str] = None
         self._job_url: Optional[str] = None
@@ -240,7 +253,7 @@ class FireworksTrainer(BaseTrainer):
         Returns:
             TrainingResult with job metadata and the resulting model id.
         """
-        start_time = time.time()
+        start_time = self._clock()
         data_list = self._normalize_dataset(dataset)
         num_examples = len(data_list)
         examples = [self.format_example(row) for row in data_list]
@@ -283,12 +296,13 @@ class FireworksTrainer(BaseTrainer):
                 pass
 
         self._is_trained = True
-        total_time = time.time() - start_time
+        total_time = self._clock() - start_time
         loss_history = self._maybe_fetch_loss_history(job)
+        plan = plan_packed_steps(num_examples, epochs=self.config.epochs)
 
         return TrainingResult(
             final_loss=loss_history[-1] if loss_history else 0.0,
-            total_steps=0,
+            total_steps=plan.total_steps,
             total_epochs=self.config.epochs,
             total_time=total_time,
             tokens_processed=0,
@@ -306,7 +320,10 @@ class FireworksTrainer(BaseTrainer):
                 "lora_rank": self.config.lora_rank,
                 "learning_rate": self.config.learning_rate,
                 "account_id": self._account_id,
+                "step_unit": STEP_UNIT_PACKED,
             },
+            total_batches=plan.total_batches,
+            step_plan=plan,
         )
 
     def _write_dataset_file(self, examples: List[TrainingExample]) -> str:
@@ -434,24 +451,29 @@ class FireworksTrainer(BaseTrainer):
 
     def _mock_train(self, num_examples: int, start_time: float) -> TrainingResult:
         """Produce a mock TrainingResult when running without the SDK or a key."""
-        import random
-
-        time.sleep(0.01)
         self._is_trained = True
         self._output_model = f"mock://accounts/{self._account_id or 'mock'}/models/{self.config.display_name}"
-        mock_loss = 2.5 - (random.random() * 0.5)
+        mock_loss = 2.5 - (self._rng.random() * 0.5)
+        plan = plan_packed_steps(num_examples, epochs=self.config.epochs)
         logger.info(f"Training (mock) complete. Output model: {self._output_model}")
         return TrainingResult(
             final_loss=mock_loss,
-            total_steps=0,
+            total_steps=plan.total_steps,
             total_epochs=self.config.epochs,
-            total_time=time.time() - start_time,
+            total_time=self._clock() - start_time,
             tokens_processed=0,
             samples_processed=num_examples,
             loss_history=[mock_loss],
             weights_name=self._output_model,
             checkpoints=[],
-            metadata={"provider": "fireworks", "mock": True, "base_model": self.config.qualified_base_model},
+            metadata={
+                "provider": "fireworks",
+                "mock": True,
+                "base_model": self.config.qualified_base_model,
+                "step_unit": STEP_UNIT_PACKED,
+            },
+            total_batches=plan.total_batches,
+            step_plan=plan,
         )
 
     def save_weights(self, name: str) -> str:
diff --git a/src/bespokelabs/curator/finetune/trainer/tinker_trainer.py b/src/bespokelabs/curator/finetune/trainer/tinker_trainer.py
index 8c95ce4..2a07a07 100644
--- a/src/bespokelabs/curator/finetune/trainer/tinker_trainer.py
+++ b/src/bespokelabs/curator/finetune/trainer/tinker_trainer.py
@@ -1,12 +1,20 @@
 """TinkerTrainer implementation for LoRA fine-tuning via Tinker API."""
 
 import inspect
+import random
 import time
-from typing import Any, Dict, List, Optional
+from typing import Any, Callable, Dict, List, Optional, Sequence
 
 from bespokelabs.curator.finetune.config import TinkerTrainerConfig
 from bespokelabs.curator.finetune.data_formatter import DataFormatter
 from bespokelabs.curator.finetune.status_tracker import FinetuneStatusTracker
+from bespokelabs.curator.finetune.step_ledger import (
+    canonical_reasons,
+    checkpoint_name,
+    learning_rate_at,
+    plan_resume,
+    plan_steps_for_config,
+)
 from bespokelabs.curator.finetune.trainer.base_trainer import BaseTrainer
 from bespokelabs.curator.finetune.types import (
     ChatMessage,
@@ -60,20 +68,30 @@ class TinkerTrainer(BaseTrainer):
         ```
     """
 
-    def __init__(self, config: TinkerTrainerConfig):
+    def __init__(
+        self,
+        config: TinkerTrainerConfig,
+        *,
+        clock: Optional[Callable[[], float]] = None,
+        rng: Optional[random.Random] = None,
+    ) -> None:
         """Initialize the TinkerTrainer.
 
         Args:
             config: TinkerTrainerConfig with training parameters
+            clock: Callable returning the current time in seconds; defaults to ``time.time``
+            rng: Random number generator for the mock training path; defaults to a
+                generator seeded with ``config.seed``, so mock runs are reproducible
         """
         self.config = config
         self.data_formatter = DataFormatter(max_seq_length=config.max_seq_length)
+        self._clock: Callable[[], float] = clock if clock is not None else time.time
+        self._rng: random.Random = rng if rng is not None else random.Random(config.seed)
         self._weights_name: Optional[str] = None
         self._weights_path: Optional[str] = None
         self._is_trained = False
         self._checkpoints: List[CheckpointInfo] = []
-        self._resume_from_step: int = 0
-        self._resume_from_epoch: int = 0
+        self._resume_from: Optional[CheckpointInfo] = None
 
         # These will be initialized when Tinker SDK is available
         self._service_client: Optional[Any] = None
@@ -141,14 +159,34 @@ class TinkerTrainer(BaseTrainer):
         ignored_kwargs = [key for key in kwargs if key not in supported_kwargs]
         return supported_kwargs, ignored_kwargs
 
-    def save_checkpoint(self, name: str, step: int, epoch: int, loss: float) -> Optional[CheckpointInfo]:
+    def save_checkpoint(
+        self,
+        name: str,
+        step: int,
+        epoch: int,
+        loss: float,
+        *,
+        reasons: Sequence[str] = ("interval",),
+        batch_size: int = 0,
+        gradient_accumulation_steps: int = 0,
+        batches_completed: int = 0,
+        dataset_signature: str = "",
+    ) -> Optional[CheckpointInfo]:
         """Save a training checkpoint.
 
+        A checkpoint is identified by its name: saving under a name that the ledger
+        already ends with merges into that entry instead of appending a second one.
+
         Args:
             name: Name for the checkpoint
-            step: Current training step
-            epoch: Current epoch
-            loss: Current loss value
+            step: Optimizer step just completed
+            epoch: Epoch the checkpoint's batch position falls in
+            loss: Mean loss over the accumulation window that closed here
+            reasons: Why the checkpoint is being written; ordered by the ledger
+            batch_size: Examples per batch in this run
+            gradient_accumulation_steps: Batches per optimizer step in this run
+            batches_completed: Batches completed so far, counted across epochs
+            dataset_signature: Signature of the data this run is training on
 
         Returns:
             CheckpointInfo with checkpoint details, or None if saving failed
@@ -158,40 +196,43 @@ class TinkerTrainer(BaseTrainer):
                 save_future = self._training_client.save_state(name)
                 save_result = save_future.result()
                 checkpoint_path = save_result.path
-
-                checkpoint = CheckpointInfo(
-                    name=name,
-                    path=checkpoint_path,
-                    step=step,
-                    epoch=epoch,
-                    loss=loss,
-                )
-                self._checkpoints.append(checkpoint)
-                logger.info(f"Checkpoint saved: {name} at step {step} (path: {checkpoint_path})")
-                return checkpoint
-
             except Exception as e:
                 logger.warning(f"Failed to save checkpoint: {e}")
                 return None
+            mock = False
+        else:
+            checkpoint_path = f"mock://checkpoints/{name}"
+            mock = True
+
+        checkpoint = CheckpointInfo(
+            name=name,
+            path=checkpoint_path,
+            step=step,
+            epoch=epoch,
+            loss=loss,
+            batch_size=batch_size,
+            gradient_accumulation_steps=gradient_accumulation_steps,
+            batches_completed=batches_completed,
+            dataset_signature=dataset_signature,
+            reasons=canonical_reasons(reasons),
+        )
+
+        if self._checkpoints and self._checkpoints[-1].name == name:
+            checkpoint.reasons = canonical_reasons(tuple(self._checkpoints[-1].reasons) + checkpoint.reasons)
+            self._checkpoints[-1] = checkpoint
         else:
-            # Mock checkpoint
-            mock_path = f"mock://checkpoints/{name}"
-            checkpoint = CheckpointInfo(
-                name=name,
-                path=mock_path,
-                step=step,
-                epoch=epoch,
-                loss=loss,
-            )
             self._checkpoints.append(checkpoint)
-            logger.info(f"Checkpoint saved (mock): {name} at step {step}")
-            return checkpoint
+
+        suffix = " (mock)" if mock else f" (path: {checkpoint_path})"
+        logger.info(f"Checkpoint saved{suffix}: {name} at step {step} [{', '.join(checkpoint.reasons)}]")
+        return checkpoint
 
     def load_checkpoint(self, checkpoint: CheckpointInfo) -> bool:
         """Load a training checkpoint, recreating the training client from saved state.
 
         This replaces the current training client with one restored from the
-        checkpoint, which is the correct Tinker API for resuming training.
+        checkpoint, which is the correct Tinker API for resuming training, and records
+        the checkpoint so the next :meth:`train` call resumes from it.
 
         Args:
             checkpoint: CheckpointInfo from a previous save_checkpoint call
@@ -203,16 +244,14 @@ class TinkerTrainer(BaseTrainer):
             try:
                 self._training_client = self._service_client.create_training_client_from_state_with_optimizer(checkpoint.path)
                 self._tokenizer = self._training_client.get_tokenizer()
-                self._resume_from_step = checkpoint.step
-                self._resume_from_epoch = checkpoint.epoch
+                self._resume_from = checkpoint
                 logger.info(f"Checkpoint loaded: {checkpoint.name} (step {checkpoint.step}, epoch {checkpoint.epoch})")
                 return True
             except Exception as e:
                 logger.warning(f"Failed to load checkpoint: {e}")
                 return False
         else:
-            self._resume_from_step = checkpoint.step
-            self._resume_from_epoch = checkpoint.epoch
+            self._resume_from = checkpoint
             logger.info(f"Checkpoint load (mock): {checkpoint.name} (step {checkpoint.step}, epoch {checkpoint.epoch})")
             return True
 
@@ -257,8 +296,12 @@ class TinkerTrainer(BaseTrainer):
 
         Returns:
             TrainingResult with training metrics
+
+        Raises:
+            ResumePlanMismatch: If a checkpoint was loaded that cannot be resumed into
+                this run, e.g. because the data or the batching changed.
         """
-        start_time = time.time()
+        start_time = self._clock()
 
         if hasattr(dataset, "to_list"):
             data_list = dataset.to_list()
@@ -267,30 +310,35 @@ class TinkerTrainer(BaseTrainer):
         else:
             data_list = dataset
 
-        num_examples = len(data_list)
-        steps_per_epoch = (num_examples + self.config.batch_size - 1) // self.config.batch_size
-        total_steps = steps_per_epoch * self.config.epochs
+        plan = plan_steps_for_config(self.config, data_list)
 
-        # Determine resume point from a previously loaded checkpoint
-        resume_step = self._resume_from_step
-        resume_epoch = self._resume_from_epoch
-        # Reset so subsequent train() calls without load_checkpoint start fresh
-        self._resume_from_step = 0
-        self._resume_from_epoch = 0
+        # Take the resume point from a previously loaded checkpoint, then clear it so a
+        # subsequent train() without load_checkpoint starts from zero.
+        resume_from = self._resume_from
+        self._resume_from = None
 
-        if resume_step > 0:
+        if resume_from is not None:
+            resume = plan_resume(plan, resume_from)
+            start_batch_ordinal = resume.start_batch_ordinal
+            completed_steps = resume.completed_steps
             logger.info(
-                f"Resuming training from step {resume_step} (epoch {resume_epoch}): "
-                f"{num_examples} examples, {self.config.epochs} epochs, {total_steps} total steps"
+                f"Resuming training from checkpoint {resume.checkpoint_name} "
+                f"(step {completed_steps}, batch {start_batch_ordinal}/{plan.total_batches}, epoch {resume.start_epoch}): "
+                f"{plan.num_examples} examples, {plan.epochs} epochs, {plan.total_steps} total optimizer steps"
             )
         else:
-            logger.info(f"Starting training: {num_examples} examples, {self.config.epochs} epochs, {total_steps} total steps")
+            start_batch_ordinal = 0
+            completed_steps = 0
+            logger.info(
+                f"Starting training: {plan.num_examples} examples, {plan.epochs} epochs, "
+                f"{plan.total_batches} batches, {plan.total_steps} total optimizer steps"
+            )
 
         # Initialize status tracker
         status_tracker = FinetuneStatusTracker(
             model=self.config.base_model,
             total_epochs=self.config.epochs,
-            total_steps=total_steps,
+            total_steps=plan.total_steps,
             batch_size=self.config.batch_size,
         )
         status_tracker.start_tracker()
@@ -299,129 +347,96 @@ class TinkerTrainer(BaseTrainer):
         tokens_processed = 0
         samples_processed = 0
 
-        # Compute loop start bounds from resume state (cookbook pattern:
-        # adjust loop bounds rather than skipping inside loops)
-        if resume_step > 0:
-            steps_before_resume_epoch = (resume_epoch - 1) * steps_per_epoch
-            resume_batch_offset = resume_step - steps_before_resume_epoch
-            if resume_batch_offset >= steps_per_epoch:
-                # Entire epoch was completed (e.g. end-of-epoch checkpoint)
-                start_epoch = resume_epoch + 1
-                start_batch_idx = 0
-            else:
-                start_epoch = resume_epoch
-                start_batch_idx = resume_batch_offset
-        else:
-            start_epoch = 1
-            start_batch_idx = 0
-
-        current_step = resume_step
+        loss_history_steps = set(plan.loss_history_steps(self.config.log_every_n_steps))
+        interval_steps = set(plan.interval_steps(self.config.checkpoint_every_n_steps))
+        epoch_final_steps = set(plan.epoch_final_steps())
+        window_losses: List[float] = []
+        epoch_losses: List[float] = []
 
         try:
-            for epoch in range(start_epoch, self.config.epochs + 1):
-                epoch_loss = 0.0
-                epoch_steps = 0
-
-                # On the first resumed epoch, skip already-completed batches;
-                # subsequent epochs start from 0
-                first_batch = start_batch_idx if epoch == start_epoch else 0
-                batch_positions = list(range(0, num_examples, self.config.batch_size))
-
-                for batch_start in batch_positions[first_batch:]:
-                    batch_end = min(batch_start + self.config.batch_size, num_examples)
-                    batch = data_list[batch_start:batch_end]
-
-                    current_step += 1
-                    lr = self._get_learning_rate(current_step, total_steps)
-                    batch_data = self._prepare_batch(batch)
-                    # Only step the optimizer after accumulating enough gradients
-                    should_optim_step = current_step % self.config.gradient_accumulation_steps == 0
-                    loss, batch_tokens = self._training_step(batch_data, learning_rate=lr, should_optim_step=should_optim_step)
-
-                    epoch_loss += loss
-                    epoch_steps += 1
-                    tokens_processed += batch_tokens
-                    samples_processed += len(batch)
-
-                    stats = TrainingStats(
-                        current_epoch=epoch,
-                        total_epochs=self.config.epochs,
-                        current_step=current_step,
-                        total_steps=total_steps,
-                        current_loss=loss,
-                        tokens_processed=tokens_processed,
-                        samples_processed=samples_processed,
-                        learning_rate=lr,
-                    )
-                    status_tracker.update(stats)
-
-                    if current_step % self.config.log_every_n_steps == 0:
-                        avg_loss = epoch_loss / epoch_steps
-                        loss_history.append(avg_loss)
-                        logger.debug(f"Step {current_step}/{total_steps}, Epoch {epoch}, Loss: {avg_loss:.4f}, LR: {lr:.2e}")
-
-                    if self.config.checkpoint_every_n_steps > 0 and current_step % self.config.checkpoint_every_n_steps == 0:
-                        checkpoint_name = f"{self.config.checkpoint_name_prefix}_step_{current_step}"
-                        self.save_checkpoint(
-                            name=checkpoint_name,
-                            step=current_step,
-                            epoch=epoch,
-                            loss=loss,
-                        )
-
-                if epoch_steps > 0:
-                    avg_epoch_loss = epoch_loss / epoch_steps
-                    # Only append if the last step wasn't already logged by per-step logging
-                    if current_step % self.config.log_every_n_steps != 0:
-                        loss_history.append(avg_epoch_loss)
-                    logger.info(f"Epoch {epoch}/{self.config.epochs} complete. Average loss: {avg_epoch_loss:.4f}")
-                else:
-                    avg_epoch_loss = 0.0
-                    logger.info(f"Epoch {epoch}/{self.config.epochs} complete. No steps executed.")
-
-                if self.config.checkpoint_every_epoch:
-                    checkpoint_name = f"{self.config.checkpoint_name_prefix}_epoch_{epoch}"
+            for batch_ordinal in range(start_batch_ordinal + 1, plan.total_batches + 1):
+                step = plan.step_of_batch(batch_ordinal)
+                epoch = plan.epoch_of_batch(batch_ordinal)
+                lr = self._get_learning_rate(step, plan.total_steps)
+
+                batch_start, batch_end = plan.batch_slice(batch_ordinal)
+                batch = data_list[batch_start:batch_end]
+                batch_data = self._prepare_batch(batch)
+
+                # The accumulation window spans epochs; the run's last batch always closes one.
+                should_optim_step = plan.is_step_boundary(batch_ordinal)
+                loss, batch_tokens = self._training_step(batch_data, learning_rate=lr, should_optim_step=should_optim_step)
+
+                window_losses.append(loss)
+                epoch_losses.append(loss)
+                tokens_processed += batch_tokens
+                samples_processed += len(batch)
+                if should_optim_step:
+                    completed_steps = step
+
+                stats = TrainingStats(
+                    current_epoch=epoch,
+                    total_epochs=self.config.epochs,
+                    current_step=completed_steps,
+                    total_steps=plan.total_steps,
+                    current_loss=loss,
+                    tokens_processed=tokens_processed,
+                    samples_processed=samples_processed,
+                    learning_rate=lr,
+                    current_batch=batch_ordinal,
+                    total_batches=plan.total_batches,
+                )
+                status_tracker.update(stats)
+
+                if batch_ordinal % plan.batches_per_epoch == 0:
+                    logger.info(f"Epoch {epoch}/{self.config.epochs} complete. Average loss: {sum(epoch_losses) / len(epoch_losses):.4f}")
+                    epoch_losses = []
+
+                if not should_optim_step:
+                    continue
+
+                window_loss = sum(window_losses) / len(window_losses)
+                window_losses = []
+
+                if step in loss_history_steps:
+                    loss_history.append(window_loss)
+                    logger.debug(f"Step {step}/{plan.total_steps}, Epoch {epoch}, Loss: {window_loss:.4f}, LR: {lr:.2e}")
+
+                reasons: List[str] = []
+                if step in interval_steps:
+                    reasons.append("interval")
+                if self.config.checkpoint_every_epoch and step in epoch_final_steps:
+                    reasons.append("epoch")
+                if step == plan.total_steps:
+                    reasons.append("final")
+
+                if reasons:
                     self.save_checkpoint(
-                        name=checkpoint_name,
-                        step=current_step,
+                        name=checkpoint_name(self.config.checkpoint_name_prefix, step),
+                        step=step,
                         epoch=epoch,
-                        loss=avg_epoch_loss,
+                        loss=window_loss,
+                        reasons=reasons,
+                        batch_size=plan.batch_size,
+                        gradient_accumulation_steps=plan.gradient_accumulation_steps,
+                        batches_completed=batch_ordinal,
+                        dataset_signature=plan.dataset_signature,
                     )
 
-            # Flush any remaining accumulated gradients from a partial window
-            if (
-                self.config.gradient_accumulation_steps > 1
-                and current_step % self.config.gradient_accumulation_steps != 0
-                and self._training_client is not None
-                and TINKER_AVAILABLE
-            ):
-                try:
-                    lr = self._get_learning_rate(current_step, total_steps)
-                    adam_params = tinker.AdamParams(
-                        learning_rate=lr,
-                        beta1=self.config.adam_params.beta1,
-                        beta2=self.config.adam_params.beta2,
-                        eps=self.config.adam_params.epsilon,
-                        weight_decay=self.config.adam_params.weight_decay,
-                    )
-                    self._training_client.optim_step(adam_params).result()
-                except Exception as e:
-                    logger.warning(f"Failed to flush final gradient accumulation: {e}")
-
         finally:
             status_tracker.stop_tracker()
 
-        total_time = time.time() - start_time
+        total_time = self._clock() - start_time
         final_loss = loss_history[-1] if loss_history else 0.0
 
         self._is_trained = True
 
         if self.config.save_weights_on_complete:
-            self._weights_name = self.save_weights(f"{self.config.base_model}_lora_{int(time.time())}")
+            self._weights_name = self.save_weights(f"{self.config.base_model}_lora_{int(self._clock())}")
 
         result = TrainingResult(
             final_loss=final_loss,
-            total_steps=current_step,
+            total_steps=plan.total_steps,
             total_epochs=self.config.epochs,
             total_time=total_time,
             tokens_processed=tokens_processed,
@@ -435,7 +450,11 @@ class TinkerTrainer(BaseTrainer):
                 "learning_rate": self.config.adam_params.learning_rate,
                 "lora_rank": self.config.lora_config.rank,
                 "lora_alpha": self.config.lora_config.alpha,
+                "gradient_accumulation_steps": self.config.gradient_accumulation_steps,
+                "dataset_signature": plan.dataset_signature,
             },
+            total_batches=plan.total_batches,
+            step_plan=plan,
         )
 
         logger.info(f"Training complete. Final loss: {final_loss:.4f}, Time: {total_time:.2f}s")
@@ -478,15 +497,11 @@ class TinkerTrainer(BaseTrainer):
             except Exception as e:
                 logger.warning(f"Training step failed: {e}. Falling back to mock mode.")
 
-        import random
-
-        mock_loss = 2.5 - (random.random() * 0.5)
+        mock_loss = 2.5 - (self._rng.random() * 0.5)
         mock_tokens = self._get_batch_token_count(batch_data)
         if mock_tokens == 0:
             mock_tokens = len(batch_data) * 100
 
-        time.sleep(0.01)
-
         return mock_loss, mock_tokens
 
     @staticmethod
@@ -534,21 +549,21 @@ class TinkerTrainer(BaseTrainer):
         return float(TinkerTrainer._get_batch_token_count(batch_data))
 
     def _get_learning_rate(self, step: int, total_steps: int) -> float:
-        """Calculate learning rate with optional warmup.
+        """Calculate the learning rate for an optimizer step.
 
         Args:
-            step: Current training step
-            total_steps: Total number of training steps
+            step: Current optimizer step (1-based)
+            total_steps: Total number of optimizer steps in the run
 
         Returns:
             Current learning rate
         """
-        base_lr = self.config.adam_params.learning_rate
-
-        if self.config.warmup_steps > 0 and step < self.config.warmup_steps:
-            return base_lr * (step / self.config.warmup_steps)
-
-        return base_lr
+        return learning_rate_at(
+            step,
+            total_steps,
+            self.config.adam_params.learning_rate,
+            self.config.warmup_steps,
+        )
 
     def save_weights(self, name: str) -> str:
         """Save the trained LoRA weights.
diff --git a/src/bespokelabs/curator/finetune/types.py b/src/bespokelabs/curator/finetune/types.py
index c8e4615..3f60314 100644
--- a/src/bespokelabs/curator/finetune/types.py
+++ b/src/bespokelabs/curator/finetune/types.py
@@ -1,10 +1,12 @@
 """Type definitions for fine-tuning module."""
 
 from dataclasses import dataclass, field
-from typing import Any, Dict, List, Optional
+from typing import Any, Dict, List, Optional, Tuple
 
 from pydantic import BaseModel, ConfigDict, Field
 
+from bespokelabs.curator.finetune.step_ledger import StepPlan
+
 
 class ChatMessage(BaseModel):
     """A single chat message."""
@@ -38,7 +40,12 @@ class SamplingConfig(BaseModel):
 
 @dataclass
 class TrainingStats:
-    """Real-time training statistics."""
+    """Real-time training statistics.
+
+    ``current_step`` and ``total_steps`` are counted in optimizer steps, so they stay
+    flat while gradients accumulate; ``current_batch`` and ``total_batches`` count the
+    batches that feed them.
+    """
 
     current_epoch: int = 0
     total_epochs: int = 0
@@ -49,17 +56,41 @@ class TrainingStats:
     samples_processed: int = 0
     learning_rate: float = 0.0
     elapsed_time: float = 0.0
+    current_batch: int = 0
+    total_batches: int = 0
 
 
 @dataclass
 class CheckpointInfo:
-    """Information about a saved checkpoint."""
+    """Information about a saved checkpoint.
+
+    Besides the position it was taken at, a checkpoint records the shape of the run
+    that produced it, so a later resume can refuse a reshaped run instead of silently
+    replaying or skipping examples.
+
+    Attributes:
+        name: Checkpoint name.
+        path: Where the checkpoint state lives.
+        step: The optimizer step that had just completed.
+        epoch: The epoch the checkpoint's batch position falls in.
+        loss: Mean loss over the accumulation window that closed here.
+        batch_size: Examples per batch in the run that wrote it.
+        gradient_accumulation_steps: Batches per optimizer step in that run.
+        batches_completed: Batches completed at that moment, counted across epochs.
+        dataset_signature: Signature of the data that run trained on.
+        reasons: Why the checkpoint was written, in ledger order.
+    """
 
     name: str
     path: str
     step: int
     epoch: int
     loss: float
+    batch_size: int = 0
+    gradient_accumulation_steps: int = 0
+    batches_completed: int = 0
+    dataset_signature: str = ""
+    reasons: Tuple[str, ...] = ()
 
 
 @dataclass
@@ -76,3 +107,5 @@ class TrainingResult:
     weights_name: Optional[str] = None
     checkpoints: List[CheckpointInfo] = field(default_factory=list)
     metadata: Dict[str, Any] = field(default_factory=dict)
+    total_batches: int = 0
+    step_plan: Optional[StepPlan] = None
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
