# g11 — Fine-tuning step ledger: one step unit, one checkpoint identity, one resume contract

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries; `located` gets the same world as `world` plus a map of where each remark sits, but never a quote, never which requirement a conversation serves, and never which are herrings.

| arm | what it is handed | measured |
|---|---|---|
| `blind` | the ticket | — |
| `spec` | the ticket + both hidden requirements | — |
| `clues` | the ticket + all 47 remarks, quoted | **1.00** |
| `world` | the ticket, against `sweworld:0.4.4` where the 47 remarks live in chat, the wiki and mail | — |
| `located` | the `world` arm plus a map naming each remark's channel, day, minute and length (or its page, or its mail subject) — the search removed, the inference left | **1.00** |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Two requirements, `g11.r1` and `g11.r2`. Neither is written down anywhere an agent
can read: they have to be reassembled from remarks scattered across the world.

**Nine facts, not ten.** `g11.r1` declares all five; `g11.r2` declares four — it
has no `scope`. `score.py` takes its keys from `tasks.json` rather than from a
fixed list of five, precisely so an absent fact is not invented and does not divide
the mean by the wrong number, so each of the nine is worth one ninth.
`open_feature` (did the agent build the feature at all?) carries weight **0.0**:
building the feature scores nothing, only recovering what nobody wrote down does.

The facts, and the question each one answers:

| fact | the question it answers |
|---|---|
| `rule` | what exactly has to exist |
| `scope` | where it applies, and where it must not |
| `exclusions_or_crossover` | what has to stay untouched |
| `failure_behavior` | what happens when it goes wrong |
| `observability` | the exact values a test can read back |

---

### `g11.r1` — one checkpoint per step, carrying every reason it fired for

**In one sentence:** a step that trips several triggers writes **one** checkpoint
whose `reasons` lists them in ledger order, not one checkpoint per trigger — and a
repeat write under the same name merges into the entry that is already there.

#### `rule` — what has to exist

- `CheckpointInfo` gains a **last** field `reasons: Tuple[str, ...] = ()`.
- `save_checkpoint` gains a **keyword-only** `reasons: Sequence[str] = ("interval",)`.
- The vocabulary is exactly three strings, in a module constant of
  `step_ledger.py`:

```python
CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")
```

- `canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]` **deduplicates**
  and orders by that ledger order — not alphabetically.
- A step that fires several triggers produces **exactly one** `save_checkpoint`
  call, whose `reasons` is that canonical tuple.

The stored `name` comes from `checkpoint_name(prefix, step)` =
`CHECKPOINT_NAME_TEMPLATE.format(prefix=..., step=...)` with:

```python
CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"
checkpoint_name("checkpoint", 2) == "checkpoint-s000002"
```

#### `scope` — which trigger is unconditional, and which trainer

| trigger | when it fires |
|---|---|
| `"final"` | at `step == plan.total_steps`, **regardless of configuration** |
| `"interval"`, `"epoch"` | conditional on their config fields, as now |

Applies to `TinkerTrainer` **only**. `FireworksTrainer` writes no checkpoints and
gains no reasons.

#### `exclusions_or_crossover` — the epoch is derived, not the loop variable

The `epoch` recorded on a checkpoint is
`plan.epoch_of_batch(checkpoint.batches_completed)` — **never** the
`for epoch in range(...)` loop variable.

So a checkpoint whose reasons include `"epoch"` for the end of epoch 1 records
`epoch == 2`.

#### `failure_behavior` — an unknown reason, and a repeated name

`canonical_reasons` raises `StepLedgerError` on any string outside
`CHECKPOINT_REASONS`.

A repeat `save_checkpoint` under a name equal to the **last** entry of
`self._checkpoints` **replaces that entry in place** — merging both reason tuples
through `canonical_reasons` and taking the new `loss`:

```python
save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5,  reasons=("interval",))
save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.25, reasons=("final",))
# -> len(trainer.get_checkpoints()) == 1
#    reasons == ("interval", "final")
#    loss == 0.25
```

#### `observability` — exact values

End-to-end run: 10 examples, `batch_size=3`, `epochs=2`,
`gradient_accumulation_steps=3`, `checkpoint_every_n_steps=2`,
`checkpoint_every_epoch=True`, `seed=0`.

```python
[c.name    for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]
[c.reasons for c in result.checkpoints] == [("interval", "epoch"), ("epoch", "final")]
[(c.step, c.epoch, c.batches_completed) for c in result.checkpoints] == [(2, 2, 6), (3, 2, 8)]
```

Field order and defaults:

```python
[f.name for f in dataclasses.fields(CheckpointInfo)]   # ends [..., "dataset_signature", "reasons"], len 10
CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()
```

The default-config fixture of `tests/finetune/test_trainer.py:19-46` yields exactly
one checkpoint, `"checkpoint-s000001"`, with `reasons == ("final",)`.

> **The herring** — what the team decided first and later reversed: the team first
> wrote **two independent checkpoints** per coincident step with the existing
> `{prefix}_step_{n}` / `{prefix}_epoch_{n}` names, and sorted the reason set
> alphabetically. Both were reversed after a resume picked up the epoch-named twin
> and replayed a window.

---

### `g11.r2` — warmup up, then decay to a floor, never to zero

**In one sentence:** the rate ramps over the warmup, decays linearly to a tenth of
the base rate, and stops there — it does not reach zero, and a warmup longer than
the run is clipped rather than refused.

#### `rule` — the schedule

```python
learning_rate_at(step, total_steps, base_lr, warmup_steps, *,
                 min_lr_ratio: float = MIN_LR_RATIO) -> float
```

with `MIN_LR_RATIO: float = 0.1` a module constant of `step_ledger.py`, and
`effective_warmup = min(warmup_steps, total_steps)`:

| phase | rate |
|---|---|
| `1 <= step <= effective_warmup` | `base_lr * step / effective_warmup` |
| after warmup | `base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)` |

where:

```python
progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)
```

#### `scope` — not declared

This requirement has no `scope` fact, which is why g11 is graded on nine facts
rather than ten. Nothing to implement, and nothing scored here.

#### `exclusions_or_crossover` — past the end, it holds the floor

Beyond the end of the run the rate is **clamped at the floor** and does not fall
below it or go negative:

```python
learning_rate_at(99, 8, 1e-4, 2) == pytest.approx(1e-05)
```

A resumed run whose `epochs` grew continues down the new, longer schedule from
`completed_steps + 1` using the same function.

#### `failure_behavior` — a warmup longer than the run is clipped

`warmup_steps` greater than `total_steps` is clipped to the run length rather than
raising:

```python
[learning_rate_at(s, 3, 1e-4, 10) for s in range(1, 4)] == pytest.approx(
    [1e-4/3, 2e-4/3, 1e-04], rel=1e-12)
```

— ending exactly at `base_lr`.

#### `observability` — exact values

```python
[learning_rate_at(s, 8, 1e-4, 2) for s in range(1, 9)] == pytest.approx(
    [5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], rel=1e-12)

[learning_rate_at(s, 4, 1e-4, 0) for s in range(1, 5)] == pytest.approx(
    [7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12)
```

In the end-to-end run the three optimizer steps carry `5e-05`, `1e-04`, `1e-05`,
and those are the values pushed on `TrainingStats.learning_rate` for the batches of
each window.

> **The herring** — what the team decided first and later reversed: an earlier
> revision decayed to **zero** over the run and used the exclusive
> `step < warmup_steps` comparison that `tinker_trainer.py:548` still shows. Both
> were reversed after the last steps of long runs stopped moving and the first step
> trained at rate 0.

---

## Where the remarks are spread

47 remarks in total — 39 clues, 4 herrings and 4 reversals — across 1 surfaces and 9 chat channels. `clues.spread()` reports on this — at least 2 sources, 3 weeks and 2 rooms per requirement, so no single sitting recovers one. It is advisory, not enforced: read the numbers rather than trusting that something refused a plant without them.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **47** | `#pipeline` 8, `#code-review` 7, `#releases` 5, `#incidents` 5, `#viewer` 5, `#engineering` 5, `#cookbooks` 5, `#general` 4, `#help` 3 |

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

## g11.r1

### g11.r1.sc1 — A checkpoint is one stored row per optimizer step, its name built from the configured prefix plus the step number zero-padded to six through a single template in the ledger, and the record itself gains exactly one new field on the end with a default so existing construction sites are untouched.

*The leap nobody states:* If two triggers coincide on one step and you only want one row, the name cannot come from what triggered it; it can only come from the step, and the thing that varies then has to be recorded as a field on the row.

- **gideon** (2025-03-14, #engineering): so basically Step 4 was an interval hit and the end of an epoch and I got two rows pointing at the same weights - one step should write one checkpoint.
- **dario** (2025-03-17, #engineering): honestly sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on. so: prefix plus something that orders with the run.
- **konrad** (2025-03-19, #engineering): look, the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger and the step is padded to six digits, then ls hands them back in the order the run made them
- **nikolai** (2025-03-20, #engineering): i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss, appended fields carry a default — ten now. a save that doesn't say why still records reasons ('interval',).

### g11.r1.sc2 — The new field holds the trigger labels, drawn from a fixed three-word vocabulary held in the ledger as interval, epoch, final, and always emitted deduplicated in that ledger order rather than alphabetically; anything outside the vocabulary is an error raised from the ledger's own error type.

*The leap nobody states:* Free-text labels that three people spell three ways are only fixable by pinning the allowed strings in one place, and once they are pinned in a meaningful order there is no reason to re-sort them.

- **konrad** (2025-03-24, #engineering): Grepped the saved records: one row lists epoch twice, and elsehwere I count epoch_end and end_of_epoch, all of it free text. Anyway, fixed set of labels, and the double epoch row goes too - not by refusing the write, the record just carries the label once and a second mention folds into the first.
- **dario** (2025-04-14, #code-review): looking at 632 - sorted a to z puts final ahead of interval. the CheckpointInfo field defaults to (), save_checkpoint's reasons kwarg to ('interval',), the one nobody passes.
- **gideon** (2025-04-09, #code-review): so basically the review comment on my PR says canonical_reasons hands them back in the order the tuple is written, interval then epoch then final. and canonical_reasons(()) just comes back (), it doesn't raise - nor does handing it epoch twice, that comes back as one epoch.
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


---


## Where every remark is

47 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-21 | chat | #releases | konrad | [`g11.r1.ledger-twin-checkpoints-dario`](#g11r1ledger-twin-checkpoints-dario) | 7 | **herring** | — |
| 2025-01-28 | chat | #releases | nikolai | [`g11.r1.ledger-twin-checkpoints-emil`](#g11r1ledger-twin-checkpoints-emil) | 10 | **herring** | — |
| 2025-01-30 | chat | #incidents | gideon | [`g11.r2.lr-decay-to-zero-dario`](#g11r2lr-decay-to-zero-dario) | 8 | **herring** | — |
| 2025-02-19 | chat | #viewer | petar | [`g11.r2.lr-decay-to-zero-konrad`](#g11r2lr-decay-to-zero-konrad) | 7 | **herring** | — |
| 2025-03-14 | chat | #code-review | gideon | [`g11.r1.l8`](#g11r1l8) | 8 | clue | `rule`, `failure_behavior` |
| 2025-03-14 | chat | #engineering | konrad | [`g11.r1.l1`](#g11r1l1) | 9 | clue | `rule` |
| 2025-03-17 | chat | #code-review | konrad | [`g11.r1.l10`](#g11r1l10) | 7 | clue | `scope`, `observability` |
| 2025-03-17 | chat | #engineering | gideon | [`g11.r1.l2`](#g11r1l2) | 8 | clue | `rule` |
| 2025-03-17 | chat | #pipeline | emil | [`g11.r1.l9`](#g11r1l9) | 9 | clue | `scope` |
| 2025-03-18 | chat | #code-review | dario | [`g11.r1.l11`](#g11r1l11) | 6 | clue | `scope` |
| 2025-03-19 | chat | #pipeline | gideon | [`g11.r1.l13`](#g11r1l13) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-19 | chat | #code-review | nikolai | [`g11.r1.l12`](#g11r1l12) | 9 | clue | `scope` |
| 2025-03-19 | chat | #releases | dario | [`g11.r1.l17`](#g11r1l17) | 7 | clue | `failure_behavior` |
| 2025-03-19 | chat | #engineering | gideon | [`g11.r1.l3`](#g11r1l3) | 7 | clue | `rule` |
| 2025-03-20 | chat | #cookbooks | dermot | [`g11.r1.l19`](#g11r1l19) | 7 | clue | `observability` |
| 2025-03-20 | chat | #engineering | konrad | [`g11.r1.l4`](#g11r1l4) | 7 | clue | `observability` |
| 2025-03-21 | chat | #pipeline | gideon | [`g11.r1.l14`](#g11r1l14) | 9 | clue | `exclusions_or_crossover` |
| 2025-03-21 | chat | #cookbooks | konrad | [`g11.r1.rev2`](#g11r1rev2) | 7 | **reversal** of `g11.r1.ledger-twin-checkpoints-emil` | `rule` |
| 2025-03-24 | chat | #releases | konrad | [`g11.r1.l18`](#g11r1l18) | 9 | clue | `observability` |
| 2025-03-24 | chat | #engineering | nikolai | [`g11.r1.l5`](#g11r1l5) | 9 | clue | `rule` |
| 2025-03-24 | chat | #cookbooks | konrad | [`g11.r2.l1`](#g11r2l1) | 9 | clue | `rule`, `observability` |
| 2025-03-24 | chat | #pipeline | dermot | [`g11.r1.l15`](#g11r1l15) | 8 | clue | `exclusions_or_crossover`, `observability` |
| 2025-03-25 | chat | #pipeline | gideon | [`g11.r1.l16`](#g11r1l16) | 8 | clue | `failure_behavior` |
| 2025-03-26 | chat | #help | emil | [`g11.r2.rev1`](#g11r2rev1) | 8 | **reversal** of `g11.r2.lr-decay-to-zero-dario` | `rule`, `exclusions_or_crossover`, `observability` |
| 2025-03-27 | chat | #viewer | konrad | [`g11.r2.l5`](#g11r2l5) | 7 | clue | `rule`, `observability` |
| 2025-03-27 | chat | #help | emil | [`g11.r1.say25`](#g11r1say25) | 9 | clue | `observability` |
| 2025-03-31 | chat | #releases | dermot | [`g11.r1.rev1`](#g11r1rev1) | 8 | **reversal** of `g11.r1.ledger-twin-checkpoints-dario` | `rule` |
| 2025-04-03 | chat | #viewer | konrad | [`g11.r2.l8`](#g11r2l8) | 9 | clue | `rule` |
| 2025-04-03 | chat | #cookbooks | nikolai | [`g11.r2.l2`](#g11r2l2) | 7 | clue | `rule` |
| 2025-04-07 | chat | #general | konrad | [`g11.r2.l6`](#g11r2l6) | 8 | clue | `observability`, `rule` |
| 2025-04-09 | chat | #incidents | gideon | [`g11.r2.l4`](#g11r2l4) | 7 | clue | `rule` |
| 2025-04-09 | chat | #code-review | nikolai | [`g11.r1.l7`](#g11r1l7) | 9 | clue | `rule` |
| 2025-04-11 | chat | #cookbooks | konrad | [`g11.r2.l3`](#g11r2l3) | 7 | clue | `rule` |
| 2025-04-11 | chat | #incidents | gideon | [`g11.r2.l7`](#g11r2l7) | 7 | clue | `observability` |
| 2025-04-14 | chat | #code-review | gideon | [`g11.r1.l6`](#g11r1l6) | 8 | clue | `rule` |
| 2025-04-18 | chat | #incidents | petar | [`g11.r2.l9`](#g11r2l9) | 7 | clue | `rule`, `exclusions_or_crossover` |
| 2025-04-21 | chat | #help | emil | [`g11.r2.say20`](#g11r2say20) | 8 | clue | `rule` |
| 2025-04-21 | chat | #general | nikolai | [`g11.r2.l11`](#g11r2l11) | 9 | clue | `exclusions_or_crossover`, `observability` |
| 2025-04-21 | chat | #pipeline | ilse | [`g11.r1.say24`](#g11r1say24) | 8 | clue | `observability` |
| 2025-04-29 | chat | #general | konrad | [`g11.r2.l12`](#g11r2l12) | 9 | clue | `failure_behavior` |
| 2025-05-01 | chat | #pipeline | gideon | [`g11.r2.say19`](#g11r2say19) | 6 | clue | `exclusions_or_crossover` |
| 2025-05-06 | chat | #incidents | gideon | [`g11.r2.l14`](#g11r2l14) | 7 | clue | `exclusions_or_crossover` |
| 2025-05-30 | chat | #code-review | nikolai | [`g11.r2.l10`](#g11r2l10) | 9 | clue | `rule` |
| 2025-06-02 | chat | #general | gideon | [`g11.r2.rev2`](#g11r2rev2) | 9 | **reversal** of `g11.r2.lr-decay-to-zero-konrad` | `rule`, `failure_behavior` |
| 2025-06-02 | chat | #viewer | dario | [`g11.r2.l13`](#g11r2l13) | 9 | clue | `failure_behavior` |
| 2025-06-03 | chat | #viewer | dario | [`g11.r2.l15`](#g11r2l15) | 9 | clue | `exclusions_or_crossover` |
| 2025-06-11 | chat | #pipeline | gideon | [`g11.r1.say23`](#g11r1say23) | 7 | clue | `observability` |

#### `g11.r1.ledger-twin-checkpoints-dario` · **herring**

- **chat** · #releases · **konrad** · 2025-01-21 15:12
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> settled this in review - a step that trips both triggers writes both checkpoints, names stay `{prefix}_step_{n}` and `{prefix}_epoch_{n}`, and the reason set sorts alphabeticaly.

As it appears, spread across the exchange:

```
15:12  konrad    quick one - a step that lands on the step interval and the epoch boundary at the same time, what does it save? off the top of my head we never wrote it down
15:14  dario     both of them. it writes the one and it writes the other, we dont collapse it into something clever
15:16  konrad    ok. and do the names change in that case
15:18  dario     no, they stay as they are - {prefix}_step_{n} and {prefix}_epoch_{n}. same as any other save
15:20  dermot    the reasons recorded on it though - that's in trigger firing order, if i had to guess?
15:22  dario     sorted alphabeticaly actually. i think thats the best we can do if we want it stable, firing order is basically an accident of how we check
15:23  konrad    mhm ok, so it does not matter which trigger we test first
```

#### `g11.r1.ledger-twin-checkpoints-emil` · **herring**

- **chat** · #releases · **nikolai** · 2025-01-28 11:12
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> to confirm what we agreed: a coincident step writes two records, not one, both under the existing step/epoch names - and reasons sort alphabetcally, so it's ('epoch', 'final', 'interval') on every checkpoint

As it appears, spread across the exchange:

```
11:12  nikolai   question while im in here  what happens when an interval step lands exactly on an epoch boundary  one row or two
11:15  emil      two. one for each, and both go under the step/epoch names we already have - i dont want a third name invented for the overlap case
11:17  nikolai   right  so the existing two just both fire and you end up with a pair
11:18  emil      yup
11:21  dermot    the reasons tuple though. does a coincident step shuffle what order they come back in, or is that fixed
11:24  emil      fixed. theyre sorted alphabetcally, so its ('epoch', 'final', 'interval') and it doesnt matter what triggered the write
11:26  dermot    mhm ok, so thats the order on every checkpoint, not only the ones where two things coincide
11:27  emil      that one, yes
11:29  nikolai   yep  i had it in my head as one row carrying both flags to be honest
11:31  emil      so did i, honestly, until i went and looked at what resume actually reads back off them
```

#### `g11.r2.lr-decay-to-zero-dario` · **herring**

- **chat** · #incidents · **gideon** · 2025-01-30 15:19
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> lr schedule is settled i think: linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps. one function, no extra knobs.

As it appears, spread across the exchange:

```
15:19  gideon    the lr schedule from tuesdays run, is that decided now or still open?
15:21  dario     settled i think. linear warmup while step < warmup_steps
15:22  gideon    and after warmup? what does it do
15:24  dario     straight linear decay to 0.0 at total_steps. no plateau or anything in between
15:25  konrad    0.0 exactly? i assumed it bottomed out somewhere above zero
15:26  dario     zero at the end yeah. its one function the whole way, no extra knobs to set
15:28  konrad    nobodys been in that file yet though
15:29  gideon    Ya. I had two seperate fns in my head, warmup and then decay
```

#### `g11.r2.lr-decay-to-zero-konrad` · **herring**

- **chat** · #viewer · **petar** · 2025-02-19 13:12
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Checked against the ledger, the decay lands at exactly zero at total_steps, and warmup keeps teh strict `step < warmup_steps` compare tinker_trainer already uses.

As it appears, spread across the exchange:

```
13:12  petar     quick one on the lr schedule - does the decay actually reach zero at the end or does it just get near it
13:15  konrad    zero. exactly zero at total_steps, i checked it against the ledger
13:18  petar     ok good. warmup is the part i keep second guessing though, whats the compare at the boundary step
13:19  nils      strict one i thought? but dont quote me
13:22  konrad    right, strict. `step < warmup_steps`, which is what tinker_trainer already does, so we keep that and dont invent a second convention
13:24  petar     mhm, i had the boundary sitting on the other side of that
13:26  konrad    anyway the ledger rows are there if you want to eyeball the tail before anyone writes it
```

#### `g11.r1.l8`

- **chat** · #code-review · **gideon** · 2025-03-14 13:41
- carries `g11.r1.rule`, `g11.r1.failure_behavior`
- must be typed literally: `CHECKPOINT_REASONS`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i typed 'intervals' by accident yesterday and it went striaght into the record, so anything not in CHECKPOINT_REASONS should raise the ledgers error right at the call

As it appears, spread across the exchange:

```
13:41  gideon    quick thing on the step ledger - what stops a typo'd reason from landing in there? i dont see a check anywhere tbh
13:43  nikolai   nothing right now thats the problem
13:44  nikolai   i typed intervals by accident yesterday and it went striaght into the record
13:45  gideon    oof. so basically the reason is just whatever string you hand it
13:47  dario     is the check against CHECKPOINT_REASONS or something looser, like anything with the right prefix
13:48  nikolai   the list anything not in CHECKPOINT_REASONS raises
13:49  gideon    raises when though, at flush time? um that feels late, you already lost the callsite by then
13:51  nikolai   no right at the call and it should be the ledgers own error not some generic one
```

#### `g11.r1.l1`

- **chat** · #engineering · **konrad** · 2025-03-14 14:08
- carries `g11.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically Step 4 was an interval hit and the end of an epoch and I got two rows pointing at the same weights - one step should write one checkpoint.

As it appears, spread across the exchange:

```
14:08  konrad    the checkpoint ledger from last nights run has step 4 in it twice. is that expected?
14:10  gideon    ya i saw that too. so basically step 4 landed right on the interval, so it wrote there
14:11  konrad    right but an interval hit is one write. where is the second one coming from
14:13  gideon    step 4 was also the end of an epoch. both fired on the same step and neither one knew about the other
14:16  emil      so you have two rows pointing at the same weights? not two different snapshots
14:18  gideon    exactly, same weights, just logged twice. one step should write one checkpoint, thats it
14:20  konrad    mhm. so the second row just never happens
14:21  gideon    ya. i dunno who picks it up tbh, i can take it monday if nobody gets there first
14:24  emil      yup, ill stick it on the ledger ticket so it doesnt get lost over the weekend
```

#### `g11.r1.l10`

- **chat** · #code-review · **konrad** · 2025-03-17 13:12
- carries `g11.r1.scope`, `g11.r1.observability`
- must be typed literally: `('final',)`, `reasons`, `test_trainer.py`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the fixture at the top of test_trainer.py has neither switch on, its last step still gets checkpointed and that row's reasons come back exactly ('final',). thats settled as far as im concerned

As it appears, spread across the exchange:

```
13:12  konrad    quick one - the fixture at the top of test_trainer.py, neither switch is on there. what happens on the last step
13:15  nikolai   it still gets checkpointed
13:17  konrad    ok but then reasons for that row is what, empty?
13:19  nikolai   no it comes back exactly ('final',) nothing else in it
13:22  emil      so the plain fixture, neither one on, one entry and thats the whole tuple?
13:24  nikolai   right thats settled as far as im concerned nobodys written it yet
13:27  emil      honestly i had the empty tuple in my head for that row
```

#### `g11.r1.l2`

- **chat** · #engineering · **gideon** · 2025-03-17 14:02
- carries `g11.r1.rule`
- must be typed literally: `prefix`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly sorting a run's checkpoint files by name is useless, the prefix is the only part the step-named and epoch-named ones agree on. so: prefix plus something that orders with the run.

As it appears, spread across the exchange:

```
14:02  gideon    whats the right way to order the checkpoint files for a run? i did a plain sort by name and got nonsense back
14:04  dermot    nonsense how, out of order or dropping some?
14:05  gideon    out of order. the epoch named ones and the step named ones came back interleaved, tbh it was unusable
14:11  dario     yeah sorting them by name is useless honestly, i wouldnt bother. the step-named ones and the epoch-named ones only agree on the prefix, after that theyre two different schemes and youre comparing apples to oranges
14:12  gideon    so basically we cant key off the name at all then?
14:14  dario     not the whole name no. prefix plus something that actually orders with the run, thats the best we can do i think
14:16  dermot    yeah ok. so the prefix does hold across both at least
14:17  dario     mhm, its the only bit that does to be honest
```

#### `g11.r1.l9`

- **chat** · #pipeline · **emil** · 2025-03-17 14:02
- carries `g11.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the whole thing overnight on the stock config and there was nothing on disk to pick up at the end. a run that finishes clean and leaves no checkpoint behind is a bug, i think

As it appears, spread across the exchange:

```
14:02  emil      ran the whole thing overnight on the stock config, didnt touch a flag
14:03  emil      come the morning theres nothing on disk to pick up. honestly not sure thats wrong but it surprised me
14:05  dario     did it fall over partway? that would explain a missing one
14:06  emil      no it finished clean, exit 0
14:08  dario     hm. so is that expected on a clean finish or is it a bug
14:10  nils      bug i think. a run that gets all the way through and leaves no checkpoint behind isnt a state we should be able to end in
14:11  dario     mhm, that tracks
14:13  gideon    honestly though I always assumed it only wrote one when something went wrong
14:14  nils      no, thats the assumption i want gone. nobodys been in the code yet
```

#### `g11.r1.l11`

- **chat** · #code-review · **dario** · 2025-03-18 14:02
- carries `g11.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah - leave the interval and the per-epoch triggers gated on their config fields exactly as they are, plenty of runs have both off on purpose.

As it appears, spread across the exchange:

```
14:02  dario     reviewing the save path — the two triggers in there, do they stay behind their config fields or does one of them go on by default
14:04  dermot    the interval one stays exactly as it is, gated on its field
14:05  dario     ok and the per-epoch one? thats the one i was about to make unconditional honestly
14:07  dermot    yeah - same, leave it gated on its own field. plenty of runs have both off on purpose
14:08  dario     huh. i'd assumed nobody actually ran with neither of them
14:10  konrad    we do, more than you'd think
```

#### `g11.r1.l13`

- **chat** · #pipeline · **gideon** · 2025-03-19 13:04
- carries `g11.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically last night's checkpoint record says epoch 1, but the batch count sitting right next to it is two past where epoch 1 ends. i lost an hour to that this morning.

As it appears, spread across the exchange:

```
13:04  gideon    so basically i grabbed last nights checkpoint to restart the run and the record in there says epoch 1
13:06  dermot    resume looked ok from where i sat. what didnt line up
13:09  gideon    the batch count sitting right next to it. its two past where epoch 1 ends
13:11  dermot    so the two numbers in the same record disagree, and the batch one is the one thats further along
13:12  gideon    exactly. i lost an hour to that this morning before i even thought to doubt the record itself
13:15  emil      which of the two are we taking as true then
13:17  gideon    the count, honestly though. thats the one actually counting something that happened. the epoch written beside it is the one that goes
13:20  dermot    mhm. same record would have been wrong on the two runs before it too, we just never resumed off those
```

#### `g11.r1.l12`

- **chat** · #code-review · **nikolai** · 2025-03-19 13:41
- carries `g11.r1.scope`
- must be typed literally: `checkpoints`, `metadata`, `reasons`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly there's nothing to label on the fireworks side, it never writes checkpoints - so no "reasons" key in the metadata it hands back, just one packed step per epoch.

As it appears, spread across the exchange:

```
13:41  nikolai   whos taking the labelling pass on the fireworks backend, you or gideon
13:43  emil      me i believe. though honestly theres nothing to label on the fireworks side
13:44  nikolai   nothing at all it still hands stuff back doesnt it
13:46  emil      it does, just not checkpoints — it never writes any
13:48  konrad    ok but the metadata that comes back, presumably that still carries the reasons key, empty maybe
13:50  emil      no, theres no "reasons" key in it at all. nothing wrote a checkpoint so theres nothing for it to sit on
13:51  konrad    mhm. and step wise, what actually lands in there
13:52  emil      just one packed step per epoch. thats the whole of it
13:53  konrad    one. right, thats thinner than i had in my head. nobodys written that branch yet anyway
```

#### `g11.r1.l17`

- **chat** · #releases · **dario** · 2025-03-19 13:41
- carries `g11.r1.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> if the same name comes round again it's the same weights, so the updated row takes the newer loss and carries both label sets forward

As it appears, spread across the exchange:

```
13:41  dario     ledger q — same checkpoint name got logged twice and i only got one row back. intended?
13:43  dermot    mhm. when it comes round again like that its the same weights, so it updates the row instead of adding one
13:44  konrad    and the loss? the second call had a diffrent number on it
13:46  dermot    newer one wins, the updated row takes the later loss
13:47  dario     labels too? both calls came with their own set
13:49  dermot    both carry forward onto it. neither set gets dropped
13:51  dario     mhm, that explains my count this morning. i was sat there expecting two rows to diff
```

#### `g11.r1.l3`

- **chat** · #engineering · **gideon** · 2025-03-19 14:03
- carries `g11.r1.rule`
- must be typed literally: `CHECKPOINT_NAME_TEMPLATE`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger and the step is padded to six digits, then ls hands them back in the order the run made them

As it appears, spread across the exchange:

```
14:03  gideon    the checkpoint dirs from last nights run came back in a weird order when i listed them, resume picked the wrong one
14:04  dermot    yeah the names are ad hoc right now. the format goes through CHECKPOINT_NAME_TEMPLATE in the ledger, not the trainer
14:05  gideon    ok but a template on its own doesnt fix ordering? step 9 vs step 10 still sorts wrong
14:07  konrad    it does, the step is padded to six digits
14:07  konrad    so ls hands them back in the order the run made them, you dont sort anything yourself
14:09  gideon    ya ok, thats what i was after
14:11  konrad    the dirs from before will still carry the old names though, presumbly resume has to cope with both for a while
```

#### `g11.r1.l19`

- **chat** · #cookbooks · **dermot** · 2025-03-20 13:11
- carries `g11.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, with ten examples that run only gets three optimizer steps, and step 2 is where the interval trips and epoch 1's window closes.

As it appears, spread across the exchange:

```
13:11  dermot    on the finetune cookbook, in the tiny run at the top the interval and the epoch thing fire on the same step. expected, or did i misconfigure the cell
13:13  konrad    expected. look, with ten examples that run only gets three optimizer steps
13:14  dermot    three total. so theres basically no room for them to land apart
13:16  konrad    right. step 2 is where the interval trips, and epoch 1's window closes there too. so you see the one
13:17  dario     mhm, that tracks. so nothing to fix in the config, its just the example count being small
13:19  konrad    yes. and we keep it at ten, its a demo. a sentence under that cell so nobody goes hunting, i havent written it yet
13:21  dermot    yeah ok. ten is the whole reason it runs in under a minute
```

#### `g11.r1.l4`

- **chat** · #engineering · **konrad** · 2025-03-20 13:38
- carries `g11.r1.observability`
- must be typed literally: `('interval',)`, `CheckpointInfo`, `[f.name for f in dataclasses.fields(CheckpointInfo)]`, `f.name`, `path`, `reasons`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss, appended fields carry a default — ten now. a save that doesn't say why still records reasons ('interval',).

As it appears, spread across the exchange:

```
13:38  konrad    quick one before I forget, with the extra fields going onto CheckpointInfo does anything downstream still read them by position
13:41  dermot    so you're asking whether the ordering is load bearing. resume was, last i looked
13:44  nikolai   i mean [f.name for f in dataclasses.fields(CheckpointInfo)] still opens name path step epoch loss so anything reading the front is fine
13:47  konrad    right. and the new ones, do the callers have to pass them
13:49  nikolai   no the appended ones carry a default ten now off the top of my head
13:52  dermot    and a save that doesn't say why, plain interval one. does that come back with reasons empty or is it just absent
13:55  nikolai   no its still recorded ('interval',) for those
```

#### `g11.r1.l14`

- **chat** · #pipeline · **gideon** · 2025-03-21 13:08
- carries `g11.r1.exclusions_or_crossover`
- must be typed literally: `gradient_accumulation_steps`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the epoch on a checkpoint comes off the plan for the batch we actually stopped on, not the enclosing loop variable — and we stamp that plan's gradient_accumulation_steps onto the row too.

As it appears, spread across the exchange:

```
13:08  gideon    the checkpoint we resumed off last night has epoch 1 on it but that run was way past 1. where does that number even come from
13:10  dermot    the enclosing loop variable. so its whatever the loop happened to be sitting on, not the batch we stopped at
13:12  gideon    and instead? plain what should it read
13:14  dermot    the plan for the batch we actually stopped on. that plan already knows its epoch, take it from there
13:15  gideon    on a clean epoch end those two agree though right
13:16  dermot    no, thats precisely where they come apart. the plan for the batch we stopped on has rolled into the next epoch, the loop var is still on the one closing out
13:17  dermot    that same plan should also put its gradient_accumulation_steps on the row while were in there, we dont record it anywhere today
13:19  gideon    um, the plans value not the config one? those two drift on us
13:20  dermot    the plans. same plan the epoch comes off
```

#### `g11.r1.rev2` · **reversal**

- **chat** · #cookbooks · **konrad** · 2025-03-21 14:02
- carries `g11.r1.rule`
- takes back `g11.r1.ledger-twin-checkpoints-emil`
- must be typed literally: `CHECKPOINT_REASONS`, `canonical_reasons`, `final`, `interval`, `reasons`, `save_checkpoint`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> stopped writing two records - one save_checkpoint per step, reasons keyword-only, coming back from canonical_reasons in CHECKPOINT_REASONS order. alphabetical put final ahead of interval, read like the run ended before it looped.

As it appears, spread across the exchange:

```
14:02  konrad    look, the coincident step - we agreed it writes two records not one, both under the existing step/epoch names. fridays run didnt do that
14:05  emil      right, thats gone. we stopped writing two records, its one save_checkpoint per step now and the reasons ride along on it
14:07  konrad    mhm. so reasons is what, a list you pass in positionally
14:10  emil      keyword only. and you dont assemble it at the call site either, it comes back from canonical_reasons
14:12  dario     does that sort them too? the alphabetcal thing was the bit that annoyed me, ('epoch', 'final', 'interval') on every single checkpoint
14:15  emil      yup thats honestly the whole reason for it. alphabetical put final ahead of interval so it read like the run ended before it looped. canonical_reasons gives them back in CHECKPOINT_REASONS order instead - interval, epoch, final, ie the order a run actually hits them, final last
14:18  dario     that tracks. i think i wrote the alphabetcal tuple into a docstring somewhere back when, so thats stale now as well
```

#### `g11.r1.l18`

- **chat** · #releases · **konrad** · 2025-03-24 14:02
- carries `g11.r1.observability`
- must be typed literally: `('epoch', 'final')`, `('interval', 'epoch')`, `[c.name for c in result.checkpoints]`, `c.name`, `checkpoint-s000002`, `checkpoint-s000003`, `reasons`, `result.checkpoints`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the ten example finetune this morning - [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003'] with reasons ('interval', 'epoch') then ('epoch', 'final'), one row each.

As it appears, spread across the exchange:

```
14:02  konrad    quick one, when a save fires for two reasons on the same step do we get two entries or one?
14:06  emil      let me think through that. ran the ten example finetune this morning and [c.name for c in result.checkpoints] comes back ['checkpoint-s000002', 'checkpoint-s000003']
14:07  konrad    right but thats only the names. either of those could still be doubled up presumably
14:09  dario     c.name is just the label to be honest, its the reasons on each one you actually want
14:11  emil      yup. checkpoint-s000002 came back ('interval', 'epoch'), it hit both on the one step
14:12  konrad    and the second
14:14  emil      ('epoch', 'final') for checkpoint-s000003. one row each in result.checkpoints, not one per reason
14:15  dario     makes sense. nothing asserts on that anywhere yet mind, nobodys been near it
14:17  konrad    mhm. so counting rows was never going to tell me what i was asking
```

#### `g11.r1.l5`

- **chat** · #engineering · **nikolai** · 2025-03-24 14:06
- carries `g11.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Grepped the saved records: one row lists epoch twice, and elsehwere I count epoch_end and end_of_epoch, all of it free text. Anyway, fixed set of labels, and the double epoch row goes too - not by refusing the write, the record just carries the label once and a second mention folds into the first.

As it appears, spread across the exchange:

```
14:06  nikolai   grepped the saved records from the weekend runs nothing gets validated on the way in its free text top to bottom
14:08  konrad    what does that look like in practice
14:09  nikolai   one row lists epoch twice
14:10  nikolai   and elsehwere i count epoch_end in some of them and end_of_epoch in others
14:12  emil      honestly that reads like every writer picked its own wording and nothing ever pushed back on it
14:14  konrad    right. anyway there should be a fixed set of labels, not whatever the caller feels like typing that day
14:15  nikolai   and the double epoch row
14:16  konrad    that goes too. not by refusing the write though - the record just carries the label once, a second mention folds into the first
14:18  nikolai   ok ill pull a first list out of whats already in there minus the junk ones
```

#### `g11.r2.l1`

- **chat** · #cookbooks · **konrad** · 2025-03-24 15:04
- carries `g11.r2.rule`, `g11.r2.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> right so i ran the eight step job with warmup 2 and it never logged 1e-4 once biggest sampel in the whole run was 5e-05

As it appears, spread across the exchange:

```
15:04  konrad    look, did anyone actually read the rates that warmup run prints out
15:05  konrad    not entirely sure the top one is even showing up
15:06  nikolai   right so i ran the eight step job with warmup 2 and it never logged 1e-4 once
15:07  emil      never as in not at the peak, or never anywhere in the run
15:09  nikolai   anywhere biggest sampel in the whole run was 5e-05
15:11  emil      honestly is that just eight steps being too short to get there
15:11  nikolai   no 1e-4 is the value we asked for it should turn up in that run somewhere so thats a bug not the run being short
15:12  konrad    right, so we fix our side then. anyway nobody has been in that file yet presumably
15:14  nikolai   nope and its eight lines of log total i read all of them 5e-05 was the highest thing in there
```

#### `g11.r1.l15`

- **chat** · #pipeline · **dermot** · 2025-03-24 15:06
- carries `g11.r1.exclusions_or_crossover`, `g11.r1.observability`
- must be typed literally: `The`, `batches_completed`, `reasons`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> The end of epoch 1 row reads step 2, epoch 2, batches_completed 6, and the last one 3, 2, 8 — looked wrong until i checked that window's last batch, both are correct.

As it appears, spread across the exchange:

```
15:06  dermot    pulled the epoch ledger off this mornings run and two rows dont line up. we're at the end of epoch 1 and the row says epoch 2
15:11  nils      The end of epoch 1 row reads step 2, epoch 2, batches_completed 6. is that the one you mean
15:13  dermot    yeah that one. and then the last one is 3, 2, 8, which i cant make work either
15:15  emil      not entirely sure thats a bug, i think nils already went digging in there
15:18  nils      i did, and it looked wrong to me too until i checked that window's last batch. both are correct, they just read strangely next to each other
15:20  dermot    mhm. so the writer stays as it is
15:23  nils      it does. i think the reasons want writing down next to that column though, that's worth documenting. nobody has yet
15:25  dermot    yeah ok. i had it down as an off by one and it isnt one
```

#### `g11.r1.l16`

- **chat** · #pipeline · **gideon** · 2025-03-25 11:12
- carries `g11.r1.failure_behavior`
- must be typed literally: `A`, `trainer.get_checkpoints`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> A second save under the same name appended instead of updating, trainer.get_checkpoints() gives me two rows for one step. we agreed a name matching the most recent row replaces it.

As it appears, spread across the exchange:

```
11:12  gideon    quick one - I saved a checkpoint named A, then saved A again for the same step and it just appended. trainer.get_checkpoints() hands me two rows back
11:17  nils      yeah every save is a fresh entry right now, the name isnt consulted at all. two rows for one step is wrong though
11:19  gideon    so what should the second save do, overwrite the earlier A or
11:24  nils      replace it. if the name coming in matches the row sitting at the end of the ledger, the new save takes that row's place instead of adding one
11:26  gideon    and if A isnt the last one, like i saved something else in between?
11:29  nils      then it appends, same as today. its only ever the most recent entry we compare the name against, we're not going hunting further back
11:33  emil      yup, thats the case i had in mind too. mine were back to back so it'd collapse
11:36  nils      nobodys been in the save path yet so youll keep seeing the pair until someone is
```

#### `g11.r2.rev1` · **reversal**

- **chat** · #help · **emil** · 2025-03-26 14:12
- carries `g11.r2.rule`, `g11.r2.exclusions_or_crossover`, `g11.r2.observability`
- takes back `g11.r2.lr-decay-to-zero-dario`
- must be typed literally: `0.0`, `0.1`, `1e-05`, `MIN_LR_RATIO`, `MIN_LR_RATIO = 0.1`, `learning_rate_at`, `min_lr_ratio`, `min_lr_ratio=0.0`, `total_steps`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> dropped hard-coding 0.0 at total_steps — step 99 of the eight-step run went negative. learning_rate_at takes min_lr_ratio, default MIN_LR_RATIO = 0.1, ends at 1e-05; pass min_lr_ratio=0.0 and it lands on exactly 0.0 at the last step again.

As it appears, spread across the exchange:

```
14:12  emil      the eight step run came back with a negative lr at step 99. did i mess up the config or is that us
14:14  dario     thats us. the decay hard-codes 0.0 at total_steps and then just keeps walking downward past it
14:15  dario     so that whole "linear warmup while step < warmup_steps, then straight linear decay to 0.0 at total_steps, one function no extra knobs" thing, were dropping it. the end isnt pinned at zero any more
14:16  dermot    so learning_rate_at grows an argument, is that the shape of it?
14:17  dario     mhm. min_lr_ratio, default MIN_LR_RATIO = 0.1, so it bottoms out at 1e-05 instead of walking through zero
14:19  emil      what about the runs that Do want it to land on zero at the end, some of the older configs read the last step
14:20  dario     min_lr_ratio=0.0 and you get exactly 0.0 at the last step again, same as before. honestly the default is the only thing that changes for most people
14:22  dermot    yeah ok. that said the negative was only ever visible past total_steps, which is presumably why nobody hit it before
```

#### `g11.r2.l5`

- **chat** · #viewer · **konrad** · 2025-03-27 14:22
- carries `g11.r2.rule`, `g11.r2.observability`
- must be typed literally: `1e-05`, `5.5e-05`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - the size of each drop is set by how many steps are left after warmup, so four steps with warmup 2 gives 5.5e-05 then 1e-05

As it appears, spread across the exchange:

```
14:22  konrad    for the decay - whats actually setting how big each step down is? dont think we wrote it anywhere
14:26  nils      comes off whats left after warmup rather than the total, thats my read. nothing coded against it yet though
14:28  konrad    right. but on a run that short does that even leave you two distinct values, or does it collapse
14:33  emil      let me think through that - no, it holds. the size of each drop is set by how many steps are left after warmup
14:35  konrad    ok so four steps, warmup 2. what do you land on
14:38  emil      5.5e-05 then 1e-05
14:41  konrad    mhm, first jump is bigger than i had in my head
```

#### `g11.r1.say25`

- **chat** · #help · **emil** · 2025-03-27 15:11
- carries `g11.r1.observability`
- must be typed literally: `dataset_signature`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> every checkpoint out of one run carries the same dataset_signature, the fingerprint of the data the plan was cut from, so a resume can tell it's the same set.

As it appears, spread across the exchange:

```
15:11  emil      when a run drops more than one checkpoint, is there anything on them tying them back to the data?
15:14  dario     theres a dataset_signature on them, yeah. every checkpoint out of the one run carries the same one
15:17  emil      Same value on all of them, so its the run id relabelled basically?
15:21  dario     no, its a fingerprint of the data the plan was cut from. the run itself doesnt come into it at all
15:23  dermot    and the thing reading it is resume, if i had to guess
15:26  dario     mhm, thats the whole point of it. resume can tell its the same set its looking at
15:28  emil      yup. none of that is in the writer yet though
15:30  dario     not yet no, nobodys been in there
15:32  dermot    yeah ok. in feb there was nothing on the file to compare against in the first place
```

#### `g11.r1.rev1` · **reversal**

- **chat** · #releases · **dermot** · 2025-03-31 16:04
- carries `g11.r1.rule`
- takes back `g11.r1.ledger-twin-checkpoints-dario`
- must be typed literally: `save_checkpoint`, `checkpoint_name`, `checkpoint-s000002`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> dropped the twin write — no more {prefix}_step_{n} plus {prefix}_epoch_{n}, a resume took the epoch twin and replayed a whole window. one save_checkpoint per step, name from checkpoint_name(prefix, step), so "checkpoint-s000002"

As it appears, spread across the exchange:

```
16:04  dermot    the rerun that lost a whole window on friday - that was the two-checkpoint thing we settled in review wasn't it
16:06  dario     yeah. a step trips both triggers so we write both, the step one and the epoch one sitting next to each other. resume grabbed the epoch twin and replayed the window back over itself
16:08  konrad    so which of the two wins on resume then
16:10  dario     neither, thats the bit im dropping. no more {prefix}_step_{n} plus {prefix}_epoch_{n}, one save_checkpoint per step and thats all there is on disk
16:11  konrad    right. and the name comes from what, off the top of my head the trigger was baked into it
16:13  dario     checkpoint_name(prefix, step), nothing else feeds it. so step 2 gets you checkpoint-s000002
16:15  dermot    mhm, and the alphabetical sort on the reason set stops mattering, nothing keys off it once there's one file
16:16  dario     right, honestly that was only ever there to order the two names against each other
```

#### `g11.r2.l8`

- **chat** · #viewer · **konrad** · 2025-04-03 14:02
- carries `g11.r2.rule`
- must be typed literally: `After`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> After warmup it does come down fine, ya, but the tail of a long run is training at basically nothing and the loss just stops moving.

As it appears, spread across the exchange:

```
14:02  konrad    the lr plot off the long run, is the far end meant to look like that
14:04  gideon    which end, the ramp?
14:05  konrad    no the far end. it flattens out into nothing
14:06  gideon    ya. After warmup it does come down fine, thats not where it goes wrong
14:07  dario     so decaying too fast, or just landing too low
14:09  gideon    too low. the tail of a long run is training at basically nothing
14:10  dario     and the loss
14:11  gideon    just stops moving. so basically the tail is the bit we fix, the front of it is ok
14:12  konrad    ok. i had it backwards, i was staring at the ramp all morning
```

#### `g11.r2.l2`

- **chat** · #cookbooks · **nikolai** · 2025-04-03 15:31
- carries `g11.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, when I set 4 warmup steps I'm asking for four even ticks up, not a crawl that eases in from nothing.

As it appears, spread across the exchange:

```
15:31  nikolai   warmup on the cookbook run looked off to me the first step is barely anything
15:33  konrad    mhm i saw it. look, when i set 4 warmup steps im asking for four even ticks up
15:34  nikolai   even how same size jump each time
15:35  konrad    right, same size each. four steps, four ticks
15:37  nikolai   and the first one does it come off about nothing like the run did
15:38  konrad    no thats the part i dont want. not a crawl that eases in from nothing
15:40  emil      yup. honestly i read that curve in the log and assumed the run was just slow to get going
```

#### `g11.r2.l6`

- **chat** · #general · **konrad** · 2025-04-07 13:41
- carries `g11.r2.observability`, `g11.r2.rule`
- must be typed literally: `rel`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i ended up pinning all eight rates from that run in a single approx with rel=1e-12, the exact compares kept flaking. the drops after warmup are all the same size.

As it appears, spread across the exchange:

```
13:41  konrad    nils what happened with the lr test, it went red twice on friday
13:44  nils      the exact compares kept flaking, so im dropping exact. approx instead
13:46  konrad    per step? thats eight asserts then
13:49  nils      no, one. i ended up pinning all eight rates from that run in a single approx, rel=1e-12. tight enough that a real move still trips it. not on the branch yet, i havent touched the file
13:51  gideon    what about the ones after warmup, they need there own check?
13:53  nils      no. the drops after warmup are all the same size, so theyre covered by the same one
13:54  konrad    mhm ok
13:56  gideon    honestly though i had them down as uneven, so thats me misreading the log
```

#### `g11.r2.l4`

- **chat** · #incidents · **gideon** · 2025-04-09 13:21
- carries `g11.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> bumped epochs from 1 to 6 on the same config and the first ten steps logged the same rates as the short run, the helper isn't looking at run length at all

As it appears, spread across the exchange:

```
13:21  gideon    quick one, is the lr helper meant to behave differently when you train for longer? or is it the same curve every time
13:23  dermot    it should differ. i bumped epochs from 1 to 6 on the same config late last night to see
13:24  gideon    and what did it give you
13:25  dermot    the first ten steps logged the same rates as the short run. same numbers to the digit
13:27  dario     that tracks with what i saw honestly, i thought i'd misread the two curves last week
13:28  dermot    yeah. the helper isn't looking at run length at all, it just never gets told. so it has to be handed in
13:29  gideon    ya ok. i had it filed in my head as a warmup thing, its not that
```

#### `g11.r1.l7`

- **chat** · #code-review · **nikolai** · 2025-04-09 13:22
- carries `g11.r1.rule`
- must be typed literally: `canonical_reasons`, `canonical_reasons(())`, `epoch`, `final`, `interval`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically the review comment on my PR says canonical_reasons hands them back in the order the tuple is written, interval then epoch then final. and canonical_reasons(()) just comes back (), it doesn't raise - nor does handing it epoch twice, that comes back as one epoch.

As it appears, spread across the exchange:

```
13:22  nikolai   gideon whats the review comment on your PR actually asking for
13:24  gideon    so basically canonical_reasons hands them back in the order the tuple is written. no sorting, nothing clever
13:26  nikolai   written meaning interval epoch final
13:27  gideon    ya. interval then epoch then final, exactly that
13:29  emil      and if theres nothing in it? i had that as an error case honestly
13:31  gideon    no, canonical_reasons(()) just comes back (). it doesnt raise. hand it epoch twice and you get one epoch back, thats not an error either
13:33  emil      yup ok, thats me remembering it wrong then
13:34  nikolai   so the comment is just asking you to say so somewhere
13:36  gideon    pretty much, um, a line in the docstring. nobodys been in the function yet
```

#### `g11.r2.l3`

- **chat** · #cookbooks · **konrad** · 2025-04-11 13:31
- carries `g11.r2.rule`
- must be typed literally: `base_lr`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i think the top of the ramp belongs to the last warmup step itself, it should already be sitting on base_lr there and not one step later

As it appears, spread across the exchange:

```
13:31  konrad    in the finetune cookbook, the last warmup step - is that still ramping or is it already the top?
13:33  dario     already the top i think. that step is the end of the ramp, not the last stop before it
13:35  konrad    end of the ramp meaning what exactly. sitting at base_lr, or just short of it
13:36  dario     sitting on base_lr. the peak belongs to that step itself
13:37  konrad    and not the one after. which is not what it does now
13:38  dario     right, not one step later. nobodys been in the scheduler yet but thats where it should land
13:41  dermot    yeah ok. the curve i pulled monday flattened a step late, that would be why
```

#### `g11.r2.l7`

- **chat** · #incidents · **gideon** · 2025-04-11 13:38
- carries `g11.r2.observability`
- must be typed literally: `1e-04`, `1e-05`, `5e-05`, `current_step`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i think the three step mock run should report 5e-05 then 1e-04 then 1e-05, and each batch gets its own stats row carrying current_step and that step's rate

As it appears, spread across the exchange:

```
13:38  gideon    whats the mock run meant to report for the three steps? i keep guesing at the fixture
13:39  dario     i think 5e-05 then 1e-04 then 1e-05, in that order
13:40  gideon    and thats one row at the end?
13:41  dario     no, per batch. each one gets its own stats row
13:42  petar     carrying the step number, or do we count position
13:43  dario     current_step on the row, with the rate that step ran at. self contained, nothing to count
13:44  gideon    ya ok. i had it as one row with the three of them in a list, thats where i went wrong
```

#### `g11.r1.l6`

- **chat** · #code-review · **gideon** · 2025-04-14 12:41
- carries `g11.r1.rule`
- must be typed literally: `('interval',)`, `()`, `CheckpointInfo`, `final`, `interval`, `reasons`, `save_checkpoint`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> looking at 632 - sorted a to z puts final ahead of interval. the CheckpointInfo field defaults to (), save_checkpoint's reasons kwarg to ('interval',), the one nobody passes.

As it appears, spread across the exchange:

```
14:03  gideon    quick one on 632 - what actually decides the order the reasons come back in?
14:07  dario     looking at 632 - sorted a to z puts final ahead of interval. thats not the order we said
14:09  nikolai   yep thats backwards
14:10  nikolai   and what does it default to when nobody sets reasons
14:13  dario     the CheckpointInfo field defaults to ()
14:14  gideon    hm, i'm pretty sure save_checkpoint has a tuple in there too? um, not an empty one
14:17  dario     ya - save_checkpoint's reasons kwarg defaults to ('interval',), the one nobody passes. both of those stay as they are, its only the sort thats wrong
14:19  gideon    ya i grepped reasons= across the call sites and got nothing back
```

#### `g11.r2.l9`

- **chat** · #incidents · **petar** · 2025-04-18 15:22
- carries `g11.r2.rule`, `g11.r2.exclusions_or_crossover`
- must be typed literally: `base_lr`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on the decay, i'd sooner it flatten out at a tenth of base_lr and hold there, even past the planned end, than keep sliding down

As it appears, spread across the exchange:

```
15:22  petar     lr in last nights run was basically nothing by the end. is that expected
15:24  dermot    at the moment yes, it slides the whole way down. id sooner it flattened out and held there
15:25  nils      flatten at what
15:26  dermot    a tenth of base_lr
15:28  petar     and if a run overshoots the planned end, does it keep creeping under that
15:29  dermot    no it holds. thats more or less the point, past the planned end included. nobodys been in the scheduler yet though
15:31  nils      yep. the one last night just crawled to zero and sat there for hours
```

#### `g11.r2.say20`

- **chat** · #help · **emil** · 2025-04-21 11:22
- carries `g11.r2.rule`
- must be typed literally: `min_lr_ratio`, `min_lr_ratio=0.5`, `7.5e-05`, `5e-05`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> to be clear it's not a floor bolted onto a decay-to-zero line, min_lr_ratio rescales the whole slope — with min_lr_ratio=0.5, half way down the decay you read 7.5e-05 not 5e-05

As it appears, spread across the exchange:

```
11:22  emil      quick one before i write the schedule test — is min_lr_ratio just a floor we clamp the lr at, or is it doing more than that
11:25  dermot    more than that. its not a floor bolted onto a decay-to-zero line, it rescales the whole slope
11:27  emil      hm. so same curve, just cut off lower down? not entirely sure i see the difference in practice
11:29  dermot    the difference shows up in the middle. with min_lr_ratio=0.5, half way down the decay you read 7.5e-05, not 5e-05
11:31  emil      ah yup. and 5e-05 is exactly what the clamp reading gives you there, which is why it looked fine to me
11:33  nikolai   right thats the nasty bit both of them plot as a sane looking line
11:35  dermot    mhm. worth pinning down now, whoever ends up in the scheduler
11:36  emil      yup, glad i asked
```

#### `g11.r2.l11`

- **chat** · #general · **nikolai** · 2025-04-21 14:03
- carries `g11.r2.exclusions_or_crossover`, `g11.r2.observability`
- must be typed literally: `A`, `99`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> grid row A is the eight-step one i let overrun; by step 99 the rate had gone negative and that run wrecked the weights. agreed it's a bug, not my config.

As it appears, spread across the exchange:

```
14:03  nikolai   which of the sweep rows went negative on the rate
14:05  nils      row A. the eight-step one — i let that one overrun instead of stopping it where it was meant to stop
14:06  nikolai   how far past
14:08  nils      far enough that by step 99 it was already the wrong side of zero
14:10  dermot    and thats the run that came back unusable, or was that a different one
14:11  nils      same one. that run wrecked the weights, there was nothing worth keeping out of it
14:13  dermot    mhm. so bug then, not you setting it up wrong
14:14  nils      agreed, it's a bug and not my config. nothing i put in row A asked it to carry on past the end
14:16  dermot    yeah ok. id had it filed as a bad sweep entry, that said i never looked at what step it turned
```

#### `g11.r1.say24`

- **chat** · #pipeline · **ilse** · 2025-04-21 16:43
- carries `g11.r1.observability`
- must be typed literally: `batch_size`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the ten example set here after that, and the row pins the batch_size it ran under, 3 in that case, so the completed batch count means something when you read it back

As it appears, spread across the exchange:

```
15:02  ilse      whats the completed batch count on the ledger row actually counting? batches of what size
15:04  dermot    thats the gap yeah. on its own its a bare number
15:05  ilse      so the row carries batch_size next to it
15:07  dermot    mhm, same row. pins the batch_size it actually ran under
15:09  gideon    honestly though do we know what that lands on in practice? um for the small stuff
15:12  dermot    i ran the ten example set here after that. came out 3
15:13  gideon    ya ok so the row says 3 and the count reads against that
15:15  dermot    yeah. otherwise the count doesnt mean anything when you read it back later
```

#### `g11.r2.l12`

- **chat** · #general · **konrad** · 2025-04-29 14:21
- carries `g11.r2.failure_behavior`
- must be typed literally: `base_lr`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the cookbook smoke example while poking at 653 its 3 steps and the default warmup is 10 so it crept along all three and never got near base_lr

As it appears, spread across the exchange:

```
14:21  konrad    lr never really moved in the smoke run, is that normal
14:23  nikolai   which run
14:24  konrad    the cookbook smoke example. I ran it while i was poking at 653
14:26  nikolai   ah thats 3 steps
14:27  konrad    ok and what does that do to the lr exactly
14:28  nikolai   default warmup is 10 so it just crept along all three
14:29  dermot    mhm so it never got anywhere near base_lr, the whole run sits inside the ramp
14:31  nikolai   right so the example should pin its own warmup rather than take the default, nobodys been in there yet
14:32  konrad    right, anyway not a schedule bug then
```

#### `g11.r2.say19`

- **chat** · #pipeline · **gideon** · 2025-05-01 14:20
- carries `g11.r2.exclusions_or_crossover`
- must be typed literally: `current_batch`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - on the resume the stats keep counting current_batch straight on from the finished ones, no reset to 1, the six after it came out 7 through 12.

As it appears, spread across the exchange:

```
14:20  gideon    plain question - what is current_batch supposed to show after a resume?
14:23  dario     it doesnt go back to 1, if thats what youre asking. it counts on from the ones that already finished
14:25  gideon    ya but counts on from where exactly. the six we ran after the resume friday looked wrong to me tbh
14:28  nils      let me think - they came out 7 through 12. straight on from the finished ones, no reset, thats how the stats keep it
14:30  dario     mhm, that tracks with the numbers i had
14:32  gideon    ok so the odd part was me, i was counting the first one after the resume as 1
```

#### `g11.r2.l14`

- **chat** · #incidents · **gideon** · 2025-05-06 14:02
- carries `g11.r2.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> resumed a run with epochs raised and the rates kept following the old length, so honestly it was already sitting at the bottom about a third of the way through

As it appears, spread across the exchange:

```
14:02  gideon    the restarted run from yesteday looks off to me, curve goes flat way earlier than it should. what am I looking at
14:06  dario     which one, the fresh one or the one you picked back up?
14:08  gideon    picked back up. we raised the epochs on it before it went in again
14:12  dario     mhm thats it then. the rates kept following the old length, not the longer one you asked for
14:15  emil      so it was still shaped for how long the run used to be, is that the read
14:19  dario     yeah. so honestly it was already sitting at the bottom about a third of the way through, and everything after that was just flat
14:21  gideon    ya ok, thats exactly where the plot dies
```

#### `g11.r2.l10`

- **chat** · #code-review · **nikolai** · 2025-05-30 11:06
- carries `g11.r2.rule`
- must be typed literally: `*`, `663`, `MIN_LR_RATIO`, `min_lr_ratio`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> also did a pass on 663 - min_lr_ratio sits behind a bare * so callers have to name it, MIN_LR_RATIO stays the module-level default. lets not let those two spellings drift apart

As it appears, spread across the exchange:

```
14:02  nikolai   did anyone get to 663 in the end or is it still sitting there
14:06  emil      yup i also did a pass on 663 this morning. mostly fine, one thing on the lr helper
14:07  nikolai   whats the thing
14:10  emil      min_lr_ratio sits behind a bare * now, so callers have to name it. no positional
14:13  konrad    ok but what happens when nobody names it, is there still something to fall back on
14:16  emil      yes — MIN_LR_RATIO stays as the module level default, that doesnt move
14:17  konrad    mhm right
14:21  emil      the bit i want to be intentional about is not letting those two spellings drift apart. they need to stay in step
14:24  nikolai   yep, easy one to miss when someone tweaks just the one
```

#### `g11.r2.rev2` · **reversal**

- **chat** · #general · **gideon** · 2025-06-02 10:14
- carries `g11.r2.rule`, `g11.r2.failure_behavior`
- takes back `g11.r2.lr-decay-to-zero-konrad`
- must be typed literally: `step < warmup_steps`, `1 <= step <= effective_warmup`, `effective_warmup = min(warmup_steps, total_steps)`, `base_lr`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Dropped the strict step < warmup_steps compare — the first step trained at rate 0, and warmup 10 on a 3 step run never got near base_lr. It's 1 <= step <= effective_warmup now, effective_warmup = min(warmup_steps, total_steps), clipped rather than raising.

As it appears, spread across the exchange:

```
10:14  gideon    the 3 step smoke run trained its first step at rate 0. thats the compare we agreed on ya?
10:16  konrad    right. we had it that decay lands at exactly zero at total_steps and warmup keeps the strict `step < warmup_steps` compare tinker_trainer already uses. thats the bit thats going. a first step at rate 0 is not something i want to keep defending
10:18  nikolai   so whats it become
10:19  konrad    `1 <= step <= effective_warmup`
10:21  gideon    um that gets step one back, but warmup 10 on a 3 step run still never gets near base_lr does it
10:23  konrad    no thats the other half of it, `effective_warmup = min(warmup_steps, total_steps)`. short run reaches base_lr at the end instead of stopping partway up
10:25  nikolai   and if the config asks for more warmup than there are steps do we shout about it
10:26  konrad    no. clipped, not raising. presumably nobody wants a run to die over that
10:28  gideon    ok so the smoke run was tripping both of those at the same time, no wonder it looked so weird
```

#### `g11.r2.l13`

- **chat** · #viewer · **dario** · 2025-06-02 11:12
- carries `g11.r2.failure_behavior`
- must be typed literally: `base_lr`, `rel`, `rel=1e-12`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, keeping warmup 10 on the 3 step case as a test at rel=1e-12, plus the 1 step run with warmup 99 - single step returns base_lr, no exeption.

As it appears, spread across the exchange:

```
11:12  dario     the warmup longer than the run thing - do we keep the 3 step case in the tests, or does it go now that its not an error path
11:14  konrad    keep it. warmup 10 on the 3 step one, thats the case i want sitting there as a test
11:15  konrad    and compared tight, rel=1e-12. not the loose default
11:17  emil      rel that tight is fine honestly, the values are closed form, theres nothing to drift
11:18  dario     ok but that one still has more than one step in it. what about a run thats a single step, is that covered or not
11:21  konrad    no, thats a second one. 1 step run, warmup 99
11:23  emil      so on that one you're expecting it just hands back the base value and nothing blows up?
11:25  konrad    mhm. the single step returns base_lr, no exeption
11:27  dario     that tracks. the tight compare is the whole point really, otherwise it passes for the wrong reason
```

#### `g11.r2.l15`

- **chat** · #viewer · **dario** · 2025-06-03 14:02
- carries `g11.r2.exclusions_or_crossover`
- must be typed literally: `epochs`, `total_steps`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically on a resume the next step after the finished ones just asks the same helper again, with the trainer's total_steps, 4 here once epochs grew.

As it appears, spread across the exchange:

```
14:02  dario     quick one while im in here — on a resume, the step right after the ones already finished. does that recompute or does it read something off the checkpoint
14:04  gideon    recompute. it just asks the same helper again, nothing gets read back
14:06  dario     same helper is fine but with what, the count from when it saved or the current one
14:07  gideon    the trainers total_steps. so basically whatever the trainer is holding now, not what was written down at save time
14:09  dermot    so the saved one never comes into it
14:10  gideon    exactly. and in the run you two were looking at thats 4, once epochs grew. thats why the number moved between the two
14:12  dario     mhm ok that tracks. nobodys written it that way yet though has anyone
14:13  gideon    not yet no, um. i was going to but honestly though i wanted it agreed first
14:15  dario     good, i was about to go hunting for where the count gets persisted
```

#### `g11.r1.say23`

- **chat** · #pipeline · **gideon** · 2025-06-11 14:02
- carries `g11.r1.observability`
- must be typed literally: `CheckpointInfo`, `dataset_signature`, `reasons`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, the field order on CheckpointInfo ends with dataset_signature and then reasons — reasons stays last so the appended defaults keep lining up.

As it appears, spread across the exchange:

```
14:02  gideon    what order do the new ones go in on CheckpointInfo? ive been tacking them on wherever tbh
14:05  dario     signature then reasons at the tail, i think. thats how the resume read them
14:06  gideon    ya but why that way round, reasons was in there way before
14:08  konrad    because reasons stays last. the appended defaults line up off it
14:09  gideon    so basically the new one slots in ahead of it
14:10  konrad    right. ends with dataset_signature and then reasons. nobodys written it yet anyway
14:12  dario     makes sense, thats the bit i had backwards
```

