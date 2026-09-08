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

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 47 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 15:12–15:23 | Mattermost `#releases` — an exchange of 7 messages, opened by **konrad** |
| 2 | 2025-01-28 | 11:12–11:31 | Mattermost `#releases` — an exchange of 10 messages, opened by **nikolai** |
| 3 | 2025-01-30 | 15:19–15:29 | Mattermost `#incidents` — an exchange of 8 messages, opened by **gideon** |
| 4 | 2025-02-19 | 13:12–13:26 | Mattermost `#viewer` — an exchange of 7 messages, opened by **petar** |
| 5 | 2025-03-14 | 13:41–13:51 | Mattermost `#code-review` — an exchange of 8 messages, opened by **gideon** |
| 6 | 2025-03-14 | 14:08–14:24 | Mattermost `#engineering` — an exchange of 9 messages, opened by **konrad** |
| 7 | 2025-03-17 | 13:12–13:27 | Mattermost `#code-review` — an exchange of 7 messages, opened by **konrad** |
| 8 | 2025-03-17 | 14:02–14:17 | Mattermost `#engineering` — an exchange of 8 messages, opened by **gideon** |
| 9 | 2025-03-17 | 14:02–14:14 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **emil** |
| 10 | 2025-03-18 | 14:02–14:10 | Mattermost `#code-review` — an exchange of 6 messages, opened by **dario** |
| 11 | 2025-03-19 | 13:04–13:20 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 12 | 2025-03-19 | 13:41–13:53 | Mattermost `#code-review` — an exchange of 9 messages, opened by **nikolai** |
| 13 | 2025-03-19 | 13:41–13:51 | Mattermost `#releases` — an exchange of 7 messages, opened by **dario** |
| 14 | 2025-03-19 | 14:03–14:11 | Mattermost `#engineering` — an exchange of 7 messages, opened by **gideon** |
| 15 | 2025-03-20 | 13:11–13:21 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dermot** |
| 16 | 2025-03-20 | 13:38–13:55 | Mattermost `#engineering` — an exchange of 7 messages, opened by **konrad** |
| 17 | 2025-03-21 | 13:08–13:20 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |
| 18 | 2025-03-21 | 14:02–14:18 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **konrad** |
| 19 | 2025-03-24 | 14:02–14:17 | Mattermost `#releases` — an exchange of 9 messages, opened by **konrad** |
| 20 | 2025-03-24 | 14:06–14:18 | Mattermost `#engineering` — an exchange of 9 messages, opened by **nikolai** |
| 21 | 2025-03-24 | 15:04–15:14 | Mattermost `#cookbooks` — an exchange of 9 messages, opened by **konrad** |
| 22 | 2025-03-24 | 15:06–15:25 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 23 | 2025-03-25 | 11:12–11:36 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 24 | 2025-03-26 | 14:12–14:22 | Mattermost `#help` — an exchange of 8 messages, opened by **emil** |
| 25 | 2025-03-27 | 14:22–14:41 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 26 | 2025-03-27 | 15:11–15:32 | Mattermost `#help` — an exchange of 9 messages, opened by **emil** |
| 27 | 2025-03-31 | 16:04–16:16 | Mattermost `#releases` — an exchange of 8 messages, opened by **dermot** |
| 28 | 2025-04-03 | 14:02–14:12 | Mattermost `#viewer` — an exchange of 9 messages, opened by **konrad** |
| 29 | 2025-04-03 | 15:31–15:40 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **nikolai** |
| 30 | 2025-04-07 | 13:41–13:56 | Mattermost `#general` — an exchange of 8 messages, opened by **konrad** |
| 31 | 2025-04-09 | 13:21–13:29 | Mattermost `#incidents` — an exchange of 7 messages, opened by **gideon** |
| 32 | 2025-04-09 | 13:22–13:36 | Mattermost `#code-review` — an exchange of 9 messages, opened by **nikolai** |
| 33 | 2025-04-11 | 13:31–13:41 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **konrad** |
| 34 | 2025-04-11 | 13:38–13:44 | Mattermost `#incidents` — an exchange of 7 messages, opened by **gideon** |
| 35 | 2025-04-14 | 12:41–12:57 | Mattermost `#code-review` — an exchange of 8 messages, opened by **gideon** |
| 36 | 2025-04-18 | 15:22–15:31 | Mattermost `#incidents` — an exchange of 7 messages, opened by **petar** |
| 37 | 2025-04-21 | 11:22–11:36 | Mattermost `#help` — an exchange of 8 messages, opened by **emil** |
| 38 | 2025-04-21 | 14:03–14:16 | Mattermost `#general` — an exchange of 9 messages, opened by **nikolai** |
| 39 | 2025-04-21 | 16:43–16:56 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **ilse** |
| 40 | 2025-04-29 | 14:21–14:32 | Mattermost `#general` — an exchange of 9 messages, opened by **konrad** |
| 41 | 2025-05-01 | 14:20–14:32 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **gideon** |
| 42 | 2025-05-06 | 14:02–14:21 | Mattermost `#incidents` — an exchange of 7 messages, opened by **gideon** |
| 43 | 2025-05-30 | 11:06–11:28 | Mattermost `#code-review` — an exchange of 9 messages, opened by **nikolai** |
| 44 | 2025-06-02 | 10:14–10:28 | Mattermost `#general` — an exchange of 9 messages, opened by **gideon** |
| 45 | 2025-06-02 | 11:12–11:27 | Mattermost `#viewer` — an exchange of 9 messages, opened by **dario** |
| 46 | 2025-06-03 | 14:02–14:15 | Mattermost `#viewer` — an exchange of 9 messages, opened by **dario** |
| 47 | 2025-06-11 | 14:02–14:12 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
