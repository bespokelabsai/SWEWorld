Training progress accounting: what a "step" counts, when a checkpoint is written, and
what a resumed run needs to have been told.

The area, concretely:
- `src/bespokelabs/curator/finetune/trainer/tinker_trainer.py` — `steps_per_epoch =
  (num_examples + batch_size - 1) // batch_size` and `total_steps = steps_per_epoch *
  epochs` (lines 271-272) count *batches*. `current_step += 1` (line 334) is per
  batch, but `should_optim_step = current_step % gradient_accumulation_steps == 0`
  (line 338) counts *optimizer steps*. With accumulation at 4, `total_steps`
  overstates optimizer steps fourfold and `lr = self._get_learning_rate(current_step,
  total_steps)` (line 335) warms up on a batch index.
- `_get_learning_rate(self, step, total_steps)` (lines 536-551) never reads
  `total_steps`. It applies a linear warmup and then a flat rate, while its signature
  and docstring promise a schedule.
- Resume reconstructs position from numbers no checkpoint carries. Lines 304-316
  compute `steps_before_resume_epoch = (resume_epoch - 1) * steps_per_epoch` and a
  batch offset from it, assuming 1-based epochs and an unchanged `steps_per_epoch` —
  but `CheckpointInfo` (`finetune/types.py` lines 54-62) records only
  `name/path/step/epoch/loss`: no `batch_size`, no dataset identity, no
  `gradient_accumulation_steps`. Line 318 then sets `current_step = resume_step`, so
  warmup is re-entered mid-run against an unchanged `total_steps`.
- Two checkpoint triggers with different names and no dedup: `f"{prefix}_step_
  {current_step}"` (lines 363-364) and `f"{prefix}_epoch_{epoch}"` (lines 382-384).
  A step boundary that lands on an epoch boundary writes the same state twice under
  two names, and `save_checkpoint` (lines 144-188) appends to `self._checkpoints`
  unconditionally.
- `loss_history` mixes units. Lines 358-360 append a running epoch average every
  `log_every_n_steps`; lines 372-376 append the epoch average again, guarded by
  "only if the last step wasn't already logged". Its length is a function of no
  single unit.
- The trailing gradient-accumulation flush (lines 395-409) sits inside a
  `try/except Exception` that only logs, so a partially accumulated final batch may
  or may not contribute.
- `finetune/trainer/fireworks_trainer.py` has no step concept at all, and
  `finetune/config.py` (lines 93-96) documents a third definition: Fireworks packs
  by token count, so a small dataset may be one optimizer step per epoch.

Nothing states which unit `current_step`, `total_steps` and `warmup_steps` are in;
what identifies a checkpoint and what it must record for a resume to be sound; whether
a resume restarts at the checkpointed step, at the start of its epoch, or refuses when
the data's shape has changed; or what one entry in `loss_history` is. Read the trainer
and both config classes and specify one accounting.

Constraints: pure and deterministic, no network, no sleeping, no threads. With no
`TINKER_API_KEY` the client initialises in mock mode (lines 88-90) and `_training_step`
(lines 481-488) takes a pure branch — but that branch calls `random.random()` (line
483) and `time.sleep(0.01)` (line 488), and line 261 calls `time.time()`, so the
design must inject the clock and the RNG rather than leaving them global. Testable with
a fake tokenizer (`apply_chat_template`, `encode`), a list-of-dicts dataset, a seeded
RNG and a fake clock. Read `tests/finetune/test_trainer.py` first: a fact that restates
an assertion already made there will grade as vacuous.
