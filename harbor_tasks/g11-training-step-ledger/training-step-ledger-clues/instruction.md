You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Fine-tuning step ledger: one step unit, one checkpoint identity, one resume contract**

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

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-04T21:39:56+00:00 -->

**2025-01-21 · #releases · dario**

> settled this in review - a step that trips both triggers writes both checkpoints, names stay `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, and the reason set sorts alphabeticaly.

**2025-01-28 · #releases · emil**

> to confirm what we agreed: a coincident step writes two records, not one, both under the existing step/epoch names - and reasons sort alphabetcally, so it's ('epoch', 'final', 'interval') on every checkpoint

**2025-01-30 · #incidents · dario**

> lr schedule is settled i think: linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps. one function, no extra knobs.

**2025-02-19 · #viewer · konrad**

> Checked against the ledger, the decay lands at exactly zero at total_steps, and warmup keeps teh strict `step < warmup_steps` compare tinker_trainer already uses.

**2025-03-14 · #engineering · gideon**

> so basically Step 4 was an interval hit and the end of an epoch and I got two rows pointing at the same weights - one step should write one checkpoint.

**2025-03-14 · #code-review · nikolai**

> i typed 'intervals' by accident yesterday and it went striaght into the record, so anything not in CHECKPOINT_REASONS should raise the ledgers error right at the call

**2025-03-17 · #code-review · nikolai**

> the fixture at the top of test_trainer.py has neither switch on, its last step still gets checkpointed and that row's reasons come back exactly ('final',). thats settled as far as im concerned

**2025-03-17 · #engineering · dario**

> honestly sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on. so: prefix plus something that orders with the run.

**2025-03-17 · #pipeline · nils**

> ran the whole thing overnight on the stock config and there was nothing on disk to pick up at the end. a run that finishes clean and leaves no checkpoint behind is a bug, i think

**2025-03-18 · #code-review · dermot**

> yeah - leave the interval and the per-epoch triggers gated on their config fields exactly as they are, plenty of runs have both off on purpose.

**2025-03-19 · #code-review · emil**

> honestly there's nothing to label on the fireworks side, it never writes checkpoints - so no "reasons" key in the metadata it hands back, just one packed step per epoch.

**2025-03-19 · #pipeline · gideon**

> so basically last night's checkpoint record says epoch 1, but the batch count sitting right next to it is two past where epoch 1 ends. i lost an hour to that this morning.

**2025-03-19 · #releases · dermot**

> if the same name comes round again it's the same weights, so the updated row takes the newer loss and carries both label sets forward

**2025-03-19 · #engineering · konrad**

> look, the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger and the step is padded to six digits, then ls hands them back in the order the run made them

**2025-03-20 · #cookbooks · konrad**

> Look, with ten examples that run only gets three optimizer steps, and step 2 is where the interval trips and epoch 1's window closes.

**2025-03-20 · #engineering · nikolai**

> i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss, appended fields carry a default — ten now. a save that doesn't say why still records reasons ('interval',).

**2025-03-21 · #pipeline · dermot**

> the epoch on a checkpoint comes off the plan for the batch we actually stopped on, not the enclosing loop variable — and we stamp that plan's gradient_accumulation_steps onto the row too.

**2025-03-21 · #cookbooks · emil**

> stopped writing two records - one save_checkpoint per step, reasons keyword-only, coming back from canonical_reasons in CHECKPOINT_REASONS order. alphabetical put final ahead of interval, read like the run ended before it looped.

**2025-03-24 · #pipeline · nils**

> The end of epoch 1 row reads step 2, epoch 2, batches_completed 6, and the last one 3, 2, 8 — looked wrong until i checked that window's last batch, both are correct.

**2025-03-24 · #releases · emil**

> ran the ten example finetune this morning - [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003'] with reasons ('interval', 'epoch') then ('epoch', 'final'), one row each.

**2025-03-24 · #engineering · konrad**

> Grepped the saved records: one row lists epoch twice, and elsehwere I count epoch_end and end_of_epoch, all of it free text. Anyway, fixed set of labels and no repeats within a record.

**2025-03-24 · #cookbooks · nikolai**

> right so i ran the eight step job with warmup 2 and it never logged 1e-4 once biggest sampel in the whole run was 5e-05

**2025-03-25 · #pipeline · nils**

> A second save under the same name appended instead of updating, trainer.get_checkpoints() gives me two rows for one step. we agreed a name matching the most recent row replaces it.

**2025-03-26 · #help · dario**

> dropped hard-coding 0.0 at total_steps — step 99 of the eight-step run went negative. learning_rate_at takes min_lr_ratio, default MIN_LR_RATIO = 0.1, ends at 1e-05; pass min_lr_ratio=0.0 and it lands on exactly 0.0 at the last step again.

**2025-03-27 · #help · dario**

> every checkpoint out of one run carries the same dataset_signature, the fingerprint of the data the plan was cut from, so a resume can tell it's the same set.

**2025-03-27 · #viewer · emil**

> let me think through that - the size of each drop is set by how many steps are left after warmup, so four steps with warmup 2 gives 5.5e-05 then 1e-05

**2025-03-31 · #releases · dario**

> dropped the twin write — no more {prefix}_step_{n} plus {prefix}_epoch_{n}, a resume took the epoch twin and replayed a whole window. one save_checkpoint per step, name from checkpoint_name(prefix, step), so "checkpoint-s000002"

**2025-04-03 · #cookbooks · konrad**

> Look, when I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing.

**2025-04-03 · #viewer · gideon**

> After warmup it does come down fine, ya, but the tail of a long run is training at basically nothing and the loss just stops moving.

**2025-04-07 · #general · nils**

> i ended up pinning all eight rates from that run in a single approx with rel=1e-12, the exact compares kept flaking. the drops after warmup are all the same size.

**2025-04-09 · #code-review · gideon**

> so basically the review comment on my PR says canonical_reasons hands them back in the order the tuple is written, interval then epoch then final. and canonical_reasons(()) just comes back (), it doesn't raise.

**2025-04-09 · #incidents · dermot**

> bumped epochs from 1 to 6 on the same config and the first ten steps logged the same rates as the short run, the helper isn't looking at run length at all

**2025-04-11 · #cookbooks · dario**

> i think the top of the ramp belongs to the last warmup step itself, it should already be sitting on base_lr there and not one step later

**2025-04-11 · #incidents · dario**

> i think the three step mock run should report 5e-05 then 1e-04 then 1e-05, and each batch gets its own stats row carrying current_step and that step's rate

**2025-04-14 · #code-review · dario**

> looking at 632 - sorted a to z puts final ahead of interval. the CheckpointInfo field defaults to (), save_checkpoint's reasons kwarg to ('interval',), the one nobody passes.

**2025-04-18 · #incidents · dermot**

> on the decay, i'd sooner it flatten out at a tenth of base_lr and hold there, even past the planned end, than keep sliding down

**2025-04-21 · #pipeline · dermot**

> ran the ten example set here after that, and the row pins the batch_size it ran under, 3 in that case, so the completed batch count means something when you read it back

**2025-04-21 · #general · nils**

> grid row A is the eight-step one i let overrun; by step 99 the rate had gone negative and that run wrecked the weights. agreed it's a bug, not my config.

**2025-04-21 · #help · dermot**

> to be clear it's not a floor bolted onto a decay-to-zero line, min_lr_ratio rescales the whole slope — with min_lr_ratio=0.5, half way down the decay you read 7.5e-05 not 5e-05

**2025-04-29 · #general · nikolai**

> ran the cookbook smoke example while poking at 653 its 3 steps and the default warmup is 10 so it crept along all three and never got near base_lr

**2025-05-01 · #pipeline · nils**

> let me think - on the resume the stats keep counting current_batch straight on from the finished ones, no reset to 1, the six after it came out 7 through 12.

**2025-05-06 · #incidents · dario**

> resumed a run with epochs raised and the rates kept following the old length, so honestly it was already sitting at the bottom about a third of the way through

**2025-05-30 · #code-review · emil**

> also did a pass on 663 - min_lr_ratio sits behind a bare * so callers have to name it, MIN_LR_RATIO stays the module-level default. lets not let those two spellings drift apart

**2025-06-02 · #viewer · konrad**

> look, keeping warmup 10 on the 3 step case as a test at rel=1e-12, plus the 1 step run with warmup 99 - single step returns base_lr, no exeption.

**2025-06-02 · #general · konrad**

> Dropped the strict step < warmup_steps compare — the first step trained at rate 0, and warmup 10 on a 3 step run never got near base_lr. It's 1 <= step <= effective_warmup now, effective_warmup = min(warmup_steps, total_steps), clipped rather than raising.

**2025-06-03 · #viewer · gideon**

> so basically on a resume the next step after the finished ones just asks the same helper again, with the trainer's total_steps, 4 here once epochs grew.

**2025-06-11 · #pipeline · konrad**

> Look, the field order on CheckpointInfo ends with dataset_signature and then reasons — reasons stays last so the appended defaults keep lining up.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
