# Audit — g11 (training-step-ledger)

| fact | bracket | audit | why |
|---|---|---|---|
| `g11.r1.rule` | hidden | **retest** | Retest — keep the fact, fix three things.

1. TEST: delete `assert len(calls) == len(set(calls)) == len(result.checkpoints)` and the whole `monkeypatch.setattr( |
| `g11.r1.scope` | hidden | **narrow** | Narrow the fact to the one thing it owns, and stop grading it through rule's field.

1. **Cut the Fireworks sentence** from the fact and delete the last four li |
| `g11.r1.exclusions_or_crossover` | hidden | **cut** | Cut this fact and give r1's exclusions slot to something that actually splits blind implementations. Reasons, in order of weight: (1) no divergent action — the  |
| `g11.r1.failure_behavior` | hidden | **narrow** | Narrow the facet to the vocabulary refusal and cut the merge clause.

Keep: `canonical_reasons` raises `StepLedgerError` on any string outside `CHECKPOINT_REASO |
| `g11.r1.observability` | hidden | **narrow** | Narrow the test to the content this fact alone owns, and stop grading unspecified values.

DELETE from `test_observability__the_two_checkpoints_of_the_end_to_en |
| `g11.r2.rule` | hidden | **retest** | Retest, three changes, none of which cut the fact.

1. Clue (verify first, since I could not read it): it must contain the disambiguator, not just "floors at a  |
| `g11.r2.exclusions_or_crossover` | hidden | **cut** | Cut r2.exclusions_or_crossover; do not try to narrow it. The two halves fail in opposite directions and neither can be rescued. (1) The resume half is stated in |
| `g11.r2.failure_behavior` | hidden | **retest** | Retest. The fact is real (clipping is a genuine decision the ticket does not imply, and HF's published scheduler does not do it), but as written the test is pas |
| `g11.r2.observability` | hidden | **narrow** | Narrow, do not cut — the fact is real, the numbers are internally consistent, and I could not construct a legitimate reading that the test rejects (any implemen |

## g11.r1.rule — retest

**Divergent action.** Three concrete lines a clued agent writes and a blind one does not: (1) in step_ledger.py, `CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"` with `def checkpoint_name(prefix, step): return CHECKPOINT_NAME_TEMPLATE.format(prefix=prefix, step=step)` — the blind agent writes `f"{prefix}-step-{step}"` or `f"{prefix}_{step}"`, unpadded, because the ticket only says "derived deterministically from `config.checkpoint_name_prefix` and the step"; (2) `CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")` plus `def canonical_reasons(reasons): return tuple(sorted(set(reasons), key=CHECKPOINT_REASONS.index))` with a membership check that raises `StepLedgerError` — the blind agent has no reason vocabulary at all; (3) `reasons: Tuple[str, ...] = ()` appended as the tenth field of `CheckpointInfo` and `reasons: Sequence[str] = ("interval",)` added keyword-only to `save_checkpoint`. The ticket's `CheckpointInfo` list stops at `dataset_signature` (nine fields) and its `save_checkpoint` signature is spelled out in full without `reasons`, so a blind agent lands on nine fields and no vocabulary. This is a genuine divergence; the fact is not a coincidence.

**The assertion.** `assert tuple(canonical_reasons(("final", "epoch", "interval", "epoch"))) == ("interval", "epoch", "final")` — this is the one line that is uniquely this fact's: it needs `CHECKPOINT_REASONS`, needs index-keyed ordering (alphabetical gives `("epoch", "final", "interval")`, noticing order gives the input), needs dedup, and depends on nothing else in the task. But it is not the only deciding assertion: the test also gates on `sym("CHECKPOINT_NAME_TEMPLATE")` and `sym("checkpoint_name")` resolving (module location never stated in the fact), on `assert len(calls) == len(set(calls)) == len(result.checkpoints)` (an internal call count with no observable consequence), and on `assert by_name["checkpoint-s000002"] == ("interval", "epoch")` (which depends on r1.scope's epoch-trigger definition and the open ticket's `total_steps`/window arithmetic). So three of the four deciding assertions depend on something other than this requirement's implementation.

**Catalog A.**
- `obvious_implementation_does_it` — Partially, and it matters. An agent who checks triggers in source order — `if interval: ...` then `if epoch: ...` then `if step == total_steps: ...` — accumulates reasons already in ledger order, so `canonical_reasons` is a no-op on every tuple `train()` produces. The 'noticing order' and the ledger order coincide for the entire end-to-end path. Only the direct unit calls (`canonical_reasons(("final", "epoch", "interval", "epoch"))`) discriminate ordering; the e2e block in `test_rule` adds no ordering signal.

**Catalog B.**
- `contradicts_a_sibling` — r1.rule: 'A step that fires several triggers produces exactly one `save_checkpoint` call.' r1.failure_behavior: 'A repeat `save_checkpoint` under a name equal to the last entry of `self._checkpoints` replaces that entry in place — merging both reason tuples.' The merge exists precisely for the multi-write design the rule forbids; satisfying the rule guarantees the sibling's branch never fires in a real run. This is the rubric's 'one requirement's rule guarantees a precondition another requirement's failure behavior needs to be false' verbatim.
- `behaviour_has_no_consequence` — Specifically for the 'exactly one call' clause. Because the sibling defines merge-in-place, one call and three calls converge to identical stored state: same `name`, same `("interval", "epoch")` after canonicalisation, same final `loss`, same `len(result.checkpoints)`. The end state is indistinguishable; only `assert len(calls) == len(set(calls)) == len(result.checkpoints)` — a monkeypatched call counter — separates them.
- `observable_belongs_to_another_fact` — `assert by_name["checkpoint-s000002"] == ("interval", "epoch")` is r1.observability's literal content (`reasons_of(result) == [("interval", "epoch"), ("epoch", "final")]`), and whether `epoch` fires at step 2 at all is r1.scope's rule ('the `epoch` trigger... closes the window containing that epoch's last batch') plus the open ticket's window arithmetic. `test_rule`'s docstring asserts separation ('`rule` never runs the epochs=3 plan') but it does run the e2e plan and read its reasons.

**A correct build the test rejects:**

```
A clued agent who reads the vocabulary and the documented merge, and writes one save per trigger, letting the merge collapse them. Stored output is byte-identical to golden; it fails only the call counter.

```python
if plan.is_step_boundary(b):
    step = plan.step_of_batch(b)
    name = checkpoint_name(config.checkpoint_name_prefix, step)
    shape = dict(batch_size=config.batch_size,
                 gradient_accumulation_steps=config.gradient_accumulation_steps,
                 batches_completed=b, dataset_signature=plan.dataset_signature)
    epoch = plan.epoch_of_batch(b)
    n = config.checkpoint_every_n_steps
    if n and step % n == 0:
        self.save_checkpoint(name, step, epoch, loss, reasons=("interval",), **shape)
    if config.checkpoint_every_epoch and step in epoch_closing_steps:
        self.save_checkpoint(name, step, epoch, loss, reasons=("epoch",), **shape)
    if step == plan.total_steps:
        self.save_checkpoint(name, step, epoch, loss, reasons=("final",), **shape)
```

For the e2e config this yields exactly `["checkpoint-s000002", "checkpoint-s000003"]` with reasons `[("interval", "epoch"), ("epoch", "final")]` and the right losses — every stored assertion in all five r1 tests passes. It dies on `assert len(calls) == len(set(calls)) == len(result.checkpoints)`, because `calls == ["checkpoint-s000002", "checkpoint-s000002", "checkpoint-s000003", "checkpoint-s000003"]`. This is the design r1.failure_behavior's merge rule actively invites, so an agent working from a clue rather than the verbatim fact is likely to land here.

A second, cheaper one: putting `checkpoint_name` and `CHECKPOINT_NAME_TEMPLATE` in `tinker_trainer.py` — naming is a trainer concern and the ticket demands the ledger stay a leaf — dies at `checkpoint_name = sym("checkpoint_name")` if `sym` resolves against `step_ledger` only. The fact pins `CHECKPOINT_REASONS` to `step_ledger.py` but says nothing about where these two live.
```

**Recommendation.** Retest — keep the fact, fix three things.

1. TEST: delete `assert len(calls) == len(set(calls)) == len(result.checkpoints)` and the whole `monkeypatch.setattr(trainer, "save_checkpoint", watched)` block, or drop the `calls.count(...) == 1` variant. It grades an internal call count that r1.failure_behavior's own merge rule renders unobservable in output, and it is fragile to method binding. Replace with the stored-state equivalent, which is what the fact actually cares about: `assert [c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]` and `assert len(result.checkpoints) == len({c.name for c in result.checkpoints})` — one record per step, not one per trigger. If the "exactly one call" clause must stay graded, the clue has to state it in those words, since nothing in the run's output reveals it.

2. FACT: add the module for the naming pair — "`checkpoint_name` and `CHECKPOINT_NAME_TEMPLATE` also live in `step_ledger.py`" — or make `sym` fall back to `tinker_trainer` before failing. Right now a correct agent can lose the whole test on an unstated placement.

3. TEST: move `assert by_name["checkpoint-s000002"] == ("interval", "epoch")` out of `test_rule` into `test_observability`, where that list already lives. It re-decides a sibling's content and pulls r1.scope's epoch-trigger definition and the open ticket's window arithmetic into rule's verdict, contradicting the docstring's claim that the five are five measurements.

Also worth a note in the fact: `canonical_reasons` is a no-op on every tuple `train()` produces if triggers are checked in source order, so its discriminating power lives entirely in the direct unit calls. That is acceptable — just don't count the e2e block as ordering evidence.


## g11.r1.scope — narrow

**Divergent action.** In `TinkerTrainer.train`, at an optimizer-step boundary, the informed agent collects triggers into a list and adds a third, config-independent one, then gates the write on the list being non-empty:

    if plan.is_step_boundary(b):
        step = plan.step_of_batch(b)
        reasons = []
        if config.checkpoint_every_n_steps and step % config.checkpoint_every_n_steps == 0:
            reasons.append("interval")
        if config.checkpoint_every_epoch and step in epoch_closing_steps:
            reasons.append("epoch")
        if step == plan.total_steps:              # <-- unconditional; the divergence
            reasons.append("final")
        if reasons:                               # <-- not `if config.checkpoint_every_*`
            self.save_checkpoint(checkpoint_name(config.checkpoint_name_prefix, step),
                                 step=step, epoch=plan.epoch_of_batch(b), loss=window_mean,
                                 reasons=canonical_reasons(reasons), ...)

The blind agent writes the two ticket-named triggers only — the ticket says "`checkpoint_every_n_steps` and `checkpoint_every_epoch` keep their names and now speak in optimizer steps" and "replacing the two shapes at `:363` and `:383`", i.e. two trigger sites — so under the default config its `result.checkpoints` is `[]`. That is a real, nameable code difference.

**The assertion.** `assert [c.step for c in bare.checkpoints] == [3]` (in `test_scope`, after `bare = run(e2e_config(checkpoint_every_n_steps=0, checkpoint_every_epoch=False))`). It is the only line in the scope test that does not route through `reasons`. Yes, it depends on much besides r1: on `plan_steps` producing `total_steps == 3` from 10/3/2/gas=3 (open feature), on the boundary walk and the deletion of the `:395-409` flush (open feature), and on `TrainingResult.checkpoints` being populated at all. The line immediately above it, `assert bare.total_steps == 3`, is entirely open-feature — the ticket never says `TrainingResult.total_steps` is re-unitised, only that "The unit of `total_steps`, `warmup_steps`, `log_every_n_steps` and `checkpoint_every_n_steps` becomes the optimizer step" — so an agent that left `TrainingResult.total_steps` at 8 batches fails the *scope* test for a non-r1 reason. Every other assertion (`reasons_of(bare) == [("final",)]`, the two conditional runs, `single`) is read through `read_field(c, "reasons")`, which is r1.rule's field.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Two of the fact's three clauses are inaction. "`FireworksTrainer` writes no checkpoints and gains no reasons" is graded by `assert fw_result.checkpoints == []` and `assert "reasons" not in fw_result.metadata` — both true on an untouched checkout and on any blind implementation, since the ticket only asks Fireworks for `plan_packed_steps` and one `"step_unit"` metadata key. "The `interval` and `epoch` triggers remain conditional on their config fields" is likewise the existing `:363`/`:383` behaviour preserved by not touching it; no agent was going to make them unconditional.
- `model_already_knows_it` — "Save a checkpoint at the end of the run whatever the save strategy" is a published convention, not a private one: HF `Trainer.save_model()` after `train()`, Lightning `ModelCheckpoint(save_last=True)`, Keras end-of-fit saves. An agent restructuring all of checkpointing around a *resume contract* has a strong prior to guarantee something to resume from. It cannot express that as `reasons=("final",)` without r1.rule, so it still fails this test — but that means the test is measuring rule, not the prior it was supposed to defeat.

**Catalog B.**
- `observable_belongs_to_another_fact` — Four of the five assertion groups are `reasons_of(...)`, i.e. `read_field(c, "reasons")` — the field r1.rule introduces ("`CheckpointInfo` gains a tenth and last field `reasons`"). The Fireworks tail is gated on `require_feature(has_ledger(), "the checkpoint reason vocabulary")`, rule again. And `assert bare.total_steps == 3` is the open feature's observable. Strip rule's channel and the open feature's, and one line of scope-owned signal remains.
- `no_independent_content` — r1.observability already states and asserts the whole scope claim: "The default-config fixture … (2 examples, `batch_size=2`, `epochs=1`, no checkpoint options) yields exactly one checkpoint, `"checkpoint-s000001"`, with `reasons == ("final",)`" — and `test_observability` runs it (`assert len(fixture_result.checkpoints) == 1`, `... == ("final",)`). No implementation can fail scope and pass observability. Scope's remaining lines (`interval_only`, `epoch_only`, `single`) are permutations of the same trigger logic, not new content.

**A correct build the test rejects:**

```
Reading the fact's own stated purpose — "so every completed run ends with at least one checkpoint" — as the rule rather than as the consequence:

    # "final": never let a run finish with an empty ledger. If a trigger already
    # wrote at this step, or earlier, the run is already recoverable.
    if b == plan.total_batches and not self._checkpoints:
        reasons.append("final")

This passes `bare` (`[c.step] == [3]`, `reasons == [("final",)]`) and passes `single` (`[1]`, `[("final",)]`), which are the two cases the fact's prose is written around, and it fails `interval_only`: it yields `[c.step] == [2]` with `[("interval",)]` where the test demands `[2, 3]` and `[("interval",), ("final",)]`. Since the hidden requirement only ever reaches the agent through a clue, an agent whose clue stresses "we never want a run to end with nothing to resume from" lands here honestly. A second, cheaper correct-fail: an agent that leaves `TrainingResult.total_steps` counting batches (the ticket re-unitises `TrainingStats.total_steps` explicitly but only says `TrainingResult` "gains `total_batches` and `step_plan`") fails `assert bare.total_steps == 3` while implementing the final trigger perfectly.
```

**Recommendation.** Narrow the fact to the one thing it owns, and stop grading it through rule's field.

1. **Cut the Fireworks sentence** from the fact and delete the last four lines of `test_scope` (`require_feature(...)` through `assert \"reasons\" not in fw_result.metadata`). Both assertions pass on an untouched checkout — pure inaction, zero signal.
2. **Cut "the `interval` and `epoch` triggers remain conditional on their config fields"** as a claim; keep the `interval_only`/`epoch_only` runs in the test, because they are what separates "final is unconditional" from the `not self._checkpoints` misreading in `correct_fail` — but bill them as the fact's *discriminator*, not as separate content.
3. **Move the default-fixture paragraph out of r1.observability** ("The default-config fixture of `tests/finetune/test_trainer.py:19-46` … yields exactly one checkpoint … with `reasons == (\"final\",)`") and the corresponding block at the end of `test_observability` into `test_scope`. Observability keeps the e2e list and the ten `CheckpointInfo` fields; scope becomes the only fact that touches a run with no checkpoint options set.
4. **Delete `assert bare.total_steps == 3`** from `test_scope` — it grades whether `TrainingResult.total_steps` was re-unitised, which the ticket states only for `TrainingStats`. Replace with a self-referencing form so the scope test cannot fail for a non-r1 reason: `assert [c.step for c in bare.checkpoints] == [bare.step_plan.total_steps]`.
5. **Add one assertion scope can own without `reasons`**, so it is not wholly parasitic on rule: `assert len(bare.checkpoints) == 1` on a config where both options are off *and* `total_steps > 1`. That is the single fact — a run nobody asked to checkpoint still ends with exactly one checkpoint, at the last optimizer step.

Narrowed statement: "At `step == plan.total_steps` a checkpoint is written whether or not `checkpoint_every_n_steps` or `checkpoint_every_epoch` asked for one, and it is written at that step even when an earlier step already produced a record."


## g11.r1.exclusions_or_crossover — cut

**Divergent action.** I cannot name one that belongs to this fact. The only code an informed agent writes that a blind one does not is r1.rule's machinery — `CHECKPOINT_REASONS`, `canonical_reasons`, the `reasons=` keyword on `save_checkpoint`. For the epoch value itself both agents write the same expression: `epoch=plan.epoch_of_batch(b)` at the step boundary, because the ticket already mandates a flat walk over global ordinals ("walk batches by their global 1-based ordinal `b`") and already spells that exact call out for `current_epoch = plan.epoch_of_batch(b)`. To produce the forbidden value the agent must ADD a mechanism — a `pending_epoch` saved when the trigger was noticed and carried across the deferral to the window close — because at the moment the window closes the live loop variable is already the position epoch (batch 6 is in epoch 2 under any loop shape). The divergence runs the wrong way: the wrong answer costs extra code.

**The assertion.** `assert shapes(result) == [(2, 2, 6), (3, 3, 9), (4, 3, 12)]` — and yes, it depends on much besides this requirement. The `step` coordinate depends on r1.scope's epoch-trigger conditionality, the `batches_completed` coordinate on the open ticket's `CheckpointInfo` extension, and the whole list length on r1.rule's one-call-per-step merge. Only the middle coordinate is this fact, and the two assertions above it (`[c.step ...] == [2, 3, 4]` and `"epoch" in read_field(checkpoint, "reasons")`) both fail first for any implementation that has not already implemented r1.rule and r1.scope.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The fact is a prohibition — 'never the `for epoch in range(...)` loop variable at the moment a trigger fired'. Under the ticket's mandated flat ordinal walk there is no such variable, so not-introducing-one satisfies it. Even with an outer epoch loop retained, at the window close (batch 6) the live loop variable IS 2; the forbidden value 1 only appears if the agent deliberately stashes the epoch at trigger-notice time and carries it forward. Doing nothing passes.
- `ticket_gives_it_away` — The open ticket says 'walk batches by their global 1-based ordinal `b`', exports `epoch_of_batch(b)` as the only epoch helper, and writes `current_epoch = plan.epoch_of_batch(b)` for the per-batch `TrainingStats`. An agent already computing `plan.epoch_of_batch(b)` on the line above the checkpoint call passes the same variable in. The ticket also states 'the accumulation window ... is not reset at an epoch boundary, so a window may span one' and 'Checkpoints are written only at optimizer-step boundaries' — together these say the write happens at the closing batch, whose epoch is the position.
- `entailed_by_the_open_feature` — Given 'Checkpoints are written only at optimizer-step boundaries' plus a window that 'may span' an epoch boundary, the checkpoint physically exists at batch 6. The ticket's own `save_checkpoint(..., batches_completed=...)` signature records the position; recording an epoch inconsistent with the recorded `batches_completed` would make the record self-contradictory and break r1's own `plan.step_of_batch(checkpoint.batches_completed)` consistency check in `plan_resume`. Position is the only coherent value once A is built.
- `obvious_implementation_does_it` — The most natural body is `for b in range(1, plan.total_batches + 1): ... epoch = plan.epoch_of_batch(b); ... if boundary and trigger: self.save_checkpoint(checkpoint_name(prefix, step), step=step, epoch=epoch, loss=..., batches_completed=b, ...)`. One `epoch` local, reused. That is normal engineering instinct, not clue-reading.

**Catalog B.**
- `observable_belongs_to_another_fact` — The test gates on r1.rule/r1.scope before reading an epoch: `for checkpoint in result.checkpoints: assert "epoch" in read_field(checkpoint, "reasons")`, and before that `assert [c.step for c in result.checkpoints] == [2, 3, 4]` — which is r1.scope's trigger-conditionality, not this fact. A ticket-only run has no `reasons` field and dies there, so the blind-fail evidence in the bracket is r1.rule's, not this fact's. The `step` and `batches_completed` coordinates of `shapes()` are the open ticket's.
- `no_independent_content` — r1.observability already asserts the exact epoch numbers this fact is about: `shapes(result) == [(2, 2, 6), (3, 2, 8)]` — the middle 2 in `(2, 2, 6)` IS 'epoch 1's trigger records epoch 2'. The trigger reading would give `(2, 1, 6)` and fail r1.observability just as hard. This fact adds only a second configuration (`epochs=3`) of the same measurement, which is not new content.

**A blind build that passes anyway:**

```
A ticket-only agent, having read only "walk batches by their global 1-based ordinal `b`", "the accumulation window ... is not reset at an epoch boundary", and "Checkpoints are written only at optimizer-step boundaries", writes:

```python
plan = plan_steps_for_config(config, examples)
step = 0
for b in range(1, plan.total_batches + 1):
    epoch = plan.epoch_of_batch(b)
    start, end = plan.batch_slice(b)
    boundary = plan.is_step_boundary(b)
    loss = self._training_step(examples[start:end], should_optim_step=boundary)
    if boundary:
        step += 1
    stats.append(TrainingStats(current_batch=b, current_step=step, current_epoch=epoch, ...))
    if boundary and self._should_checkpoint(step, b, plan):
        self.save_checkpoint(
            f"{config.checkpoint_name_prefix}-s{step:06d}",
            step=step,
            epoch=epoch,                      # <-- the position, for free
            loss=loss,
            batch_size=config.batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            batches_completed=b,
            dataset_signature=plan.dataset_signature,
        )
```

`epoch` here is `plan.epoch_of_batch(b)` — the position — because it is the same local the ticket already required for `TrainingStats.current_epoch`, and because there is no other epoch in scope. This satisfies the audited fact exactly. It fails the graded test only at `read_field(checkpoint, "reasons")`, i.e. on r1.rule, which is a different fact.
```

**A correct build the test rejects:**

```
An implementation that gets this fact perfectly right — `epoch=plan.epoch_of_batch(b)`, position not trigger — but reads `checkpoint_every_epoch` as "write one when the epoch counter advances":

```python
fires_epoch = (
    config.checkpoint_every_epoch
    and plan.epoch_of_batch(b) > plan.epoch_of_batch(previous_boundary_batch)
)
```

Under `epochs=3` that fires at step 2 (batch 6, epoch 2 > epoch 1) and step 3 (batch 9, epoch 3 > epoch 2) but not at step 4 (batch 12 is still epoch 3), so the final checkpoint carries `("final",)` alone. The test rejects it at `for checkpoint in result.checkpoints: assert "epoch" in read_field(checkpoint, "reasons")` — on a trigger-selection question that belongs to r1.scope, while the epoch values this fact is actually about, `(2, 2, 6)` and `(3, 3, 9)`, are correct.
```

**Recommendation.** Cut this fact and give r1's exclusions slot to something that actually splits blind implementations. Reasons, in order of weight: (1) no divergent action — the ticket's mandated flat ordinal walk plus the stated `current_epoch = plan.epoch_of_batch(b)` makes the position the free answer, and the forbidden trigger value requires ADDING a pending-epoch variable carried across the deferral, since the live loop variable at the window close is already the position; (2) no independent content — r1.observability already asserts `shapes(result) == [(2, 2, 6), (3, 2, 8)]`, whose middle coordinate is this exact claim, so the fact cannot fail without r1.observability failing too; (3) the blind-fail evidence is borrowed — the test reads `reasons` and asserts the `[2, 3, 4]` step list before it looks at any epoch, so a ticket-only run dies on r1.rule and r1.scope and this fact never gets a vote.

If you want to keep the slot rather than cut it, the replacement must be a genuinely contested choice the ticket does not settle. The best candidate is sitting right here in the overshoot: WHICH step the "epoch" trigger fires on when an epoch's last batch is mid-window — the step that closes the window containing the epoch's last batch (steps 2, 3, 4 at epochs=3) versus the step at which the epoch counter advances (steps 2, 3 only). Both are defensible from the ticket, they differ observably, and the second is what a reasonable blind agent writes. State that explicitly as the exclusion, and move the `"epoch" in reasons` assertion for step 4 into it and out of a test that claims to be about epoch numbering. If instead you keep the fact as written, at minimum delete the `[c.step ...] == [2, 3, 4]` and `"epoch" in reasons` preconditions from this test so it grades the epoch coordinate alone — but that leaves it a strict subset of r1.observability, which is why the recommendation is cut.


## g11.r1.failure_behavior — narrow

**Divergent action.** Two branches, both absent from a ticket-only tree. In step_ledger.py: `def canonical_reasons(reasons): unknown = tuple(r for r in reasons if r not in CHECKPOINT_REASONS); if unknown: raise StepLedgerError(f"unknown checkpoint reason(s): {unknown}"); return tuple(r for r in CHECKPOINT_REASONS if r in reasons)` — specifically the `if unknown: raise` guard, as opposed to the guardless one-liner `return tuple(r for r in CHECKPOINT_REASONS if r in reasons)`, which silently drops "periodic". In TinkerTrainer.save_checkpoint, at the head of the store: `if self._checkpoints and self._checkpoints[-1].name == name: prior = self._checkpoints[-1]; info = dataclasses.replace(prior, loss=loss, reasons=canonical_reasons(tuple(prior.reasons) + tuple(reasons))); self._checkpoints[-1] = info; return info` — as opposed to the unconditional `self._checkpoints.append(info)`. The second branch is the only part that carries signal this facet owns; the first is largely inherited from r1.rule.

**The assertion.** `assert len(stored) == 1` (after two `trainer.save_checkpoint(\"checkpoint-s000002\", ...)` calls). It is the only assertion in the file that a correct-but-appending implementation fails. Passing it depends on more than this requirement: it needs r1.rule's keyword-only `reasons=` parameter to exist on `save_checkpoint` (else TypeError), r1.rule's `canonical_reasons` to merge the tuples, and the open ticket's `clock=` constructor keyword plus `e2e_config()` to build the trainer at all. The three `pytest.raises(StepLedgerError)` lines above it depend entirely on r1.rule's `canonical_reasons` symbol existing.

**Catalog A.**
- `obvious_implementation_does_it` — For the refusal half, conditional on r1.rule being known. The ticket already establishes the idiom: "`StepLedgerError`, which subclasses **`ValueError`**" and "Raises `StepLedgerError` when `num_examples == 0`, and when any of `batch_size`, `epochs`, `gradient_accumulation_steps` is `< 1`." An agent handed r1.rule's "The vocabulary is exactly three strings held in a module constant" writes a validating canonicalizer as ordinary defensive engineering. So `pytest.raises(StepLedgerError)` on ("periodic",) discriminates weakly once rule is in hand — the merge clause is doing nearly all of this facet's own work.

**Catalog B.**
- `state_is_unreachable` — For the merge half. Under any implementation that satisfies r1.rule — "A step that fires several triggers produces exactly one `save_checkpoint` call" — `train()` never issues two saves under one name, and names come from `checkpoint_name(prefix, step)` so distinct steps give distinct names. The duplicate-name state is reachable only by a caller invoking the public method twice by hand, which is exactly and only what the test does.
- `contradicts_a_sibling` — r1.rule's test guarantees the precondition this facet needs to be false: `assert calls.count("checkpoint-s000002") == 1` and `assert len(calls) == len(set(calls)) == len(result.checkpoints)`. Beyond making the branch unreachable, it is actively hostile: the obvious consumer of an in-place merge is a loop that calls save_checkpoint once per noticed trigger and lets the ledger collapse them — a coherent design this facet invites and rule rejects.
- `behaviour_has_no_consequence` — For the merge half. Given rule holds, merge and append yield identical `result.checkpoints` for every run in the suite — `test_scope`, `test_exclusions` and `test_observability` cannot tell them apart. There is no end-state difference anywhere in the product; the only differentiating outcome is the hand-authored double call.
- `observable_belongs_to_another_fact` — Three of this test's four assertion groups run through symbols r1.rule owns: `canonical_reasons` and `StepLedgerError` (rule: "`canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]` deduplicates and orders them") and the `reasons=` keyword-only parameter (rule: "`save_checkpoint` gains a keyword-only `reasons: Sequence[str] = (\"interval\",)`"). An agent who misses rule fails this test for rule's reason, not this one. The test's own comment concedes the coupling: "the ORDER the two reasons come back in is r1.rule's, so this reads the content and leaves the ordering to that test."

**A correct build the test rejects:**

```
A clue-reader who implements exactly the three observables the fact states — "leaves `len(trainer.get_checkpoints()) == 1`, `reasons == (\"interval\", \"final\")`, `loss == 0.25`" — by mutating the stored entry and returning the record built for this call:

```python
def save_checkpoint(self, name, step, epoch, loss, *, batch_size=0, gradient_accumulation_steps=0,
                    batches_completed=0, dataset_signature="", reasons=("interval",)):
    info = CheckpointInfo(name=name, path=f"mock://checkpoints/{name}", step=step, epoch=epoch,
                          loss=loss, batch_size=batch_size,
                          gradient_accumulation_steps=gradient_accumulation_steps,
                          batches_completed=batches_completed,
                          dataset_signature=dataset_signature,
                          reasons=canonical_reasons(reasons))
    if self._checkpoints and self._checkpoints[-1].name == name:
        prior = self._checkpoints[-1]
        prior.loss = loss
        prior.reasons = canonical_reasons(tuple(prior.reasons) + tuple(info.reasons))
        return info          # the record for this call; the merged one is in the list
    self._checkpoints.append(info)
    return info
```

`len(stored) == 1`, `sorted(read_field(stored[0], "reasons")) == ["final", "interval"]` and `stored[0].loss == 0.25` all pass — every observable the fact names. The test still fails on `assert sorted(read_field(merged, "reasons")) == ["final", "interval"]`, a return-value contract the fact never states. A second, smaller one: `with pytest.raises(StepLedgerError): canonical_reasons(("Interval",))` rejects an agent who writes `r.strip().lower()` while "deduplicating"; case-sensitivity appears in neither the fact nor r1.rule.
```

**Recommendation.** Narrow the facet to the vocabulary refusal and cut the merge clause.

Keep: `canonical_reasons` raises `StepLedgerError` on any string outside `CHECKPOINT_REASONS` — ("periodic",), and the mixed ("interval", "manual") case that proves the check is per-element and not "did I recognise anything". Add one assertion that pins the decision this facet actually owns, which the current test leaves implicit: that an unknown reason is *refused* rather than silently dropped, e.g. `with pytest.raises(StepLedgerError): canonical_reasons(("interval", "periodic"))` paired with a comment naming `tuple(r for r in CHECKPOINT_REASONS if r in reasons)` as the rejected implementation. Drop `canonical_reasons(("Interval",))` unless the fact text is amended to state that the vocabulary is case-sensitive.

Cut: the repeat-name merge. It is unreachable through `train()` given r1.rule's "exactly one `save_checkpoint` call", has no consequence for any run in the suite, and invites the per-trigger-save design that r1.rule's `len(calls) == len(set(calls))` rejects — the facet and its sibling pull in opposite directions. If you want to keep a duplicate-name contract, make it consequential instead of merging: have `save_checkpoint` raise `StepLedgerError` on a repeat name, which turns r1.rule's "exactly one call" from a test-only assertion into a runtime invariant, and gives this facet a failure behaviour that the product itself enforces. Either way, if any return-value contract survives, write it into the fact text — the test currently grades `merged` on a promise only the ticket's "returns the record it stored" half-makes.


## g11.r1.observability — narrow

**Divergent action.** An informed agent writes, in `step_ledger.py`, `CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"` / `CHECKPOINT_REASONS = ("interval","epoch","final")` / `canonical_reasons`, adds `reasons: Tuple[str, ...] = ()` as CheckpointInfo's tenth field, and in the train loop collects triggers into one call: `if reasons: self.save_checkpoint(checkpoint_name(config.checkpoint_name_prefix, step), step=step, epoch=plan.epoch_of_batch(b), ..., reasons=canonical_reasons(reasons))` with `reasons.append("final")` fired unconditionally at `step == plan.total_steps`. A blind agent writes `f"{prefix}-step-{step}"` or `f"{prefix}-{step}"`, has no `reasons` field at all, and writes no checkpoint when both `checkpoint_every_n_steps == 0` and `checkpoint_every_epoch is False`. That divergence is real — but it is r1.rule's and r1.scope's divergence, not this fact's: the only code an agent writes for `observability` specifically and not for its four siblings is the choice of what number to pass as `loss`, which no clue in r1 constrains.

**The assertion.** Nominally: `assert reasons_of(result) == [("interval", "epoch"), ("epoch", "final")]`. But it does not decide anything — it fails only when r1.rule (canonical order) or r1.scope (the final trigger) already fails, and rule asserts the first tuple on the same run. The only assertion that can fail while all four siblings pass is `assert [c.loss for c in result.checkpoints] == pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)`. It depends on things other than r1: the open ticket's mock RNG contract (`2.5 - draw * 0.5`, one draw per batch, `random.Random(seed)`), the plan's window boundaries, and an unstated decision that a checkpoint's `loss` is the arithmetic mean of its closing window's per-batch losses. I verified the numbers are exactly `mean(b4,b5,b6)` and `mean(b7,b8)`. Neither r1 nor the ticket says that.

**Catalog A.**
- `codebase_already_does_it` — `assert [c.path for c in result.checkpoints] == ["mock://checkpoints/checkpoint-s000002", ...]` grades the mock path prefix, which is existing trainer behaviour the ticket never asks to change (it only replaces "the two shapes at :363 and :383" for the NAME). Same for CheckpointInfo's first five fields inside `len(fields) == 10`. The agent inherits these for free.
- `ticket_gives_it_away` — Several graded lines are open-ticket text verbatim: `CheckpointInfo` gains "`batch_size: int = 0`, `gradient_accumulation_steps: int = 0`, `batches_completed: int = 0`, `dataset_signature: str = \"\"`" — which is what `[c.batch_size ...] == [3,3]`, `[read_field(c,"gradient_accumulation_steps")] == [3,3]` and `{... dataset_signature} == {SIGNATURE}` check. The ticket also fixes the RNG (`2.5 - draw * 0.5`, `random.Random(config.seed)`) that the loss numbers derive from. Those assertions cannot discriminate on r1.
- `entailed_by_the_open_feature` — `len(fields) == 10` and `fields[-2:] == ["dataset_signature", "reasons"]` follow mechanically once the open ticket's four appended fields exist and r1.rule's `reasons` is appended last — 5 original + 4 + 1. There is no second way to count. The assertion adds nothing beyond `rule`'s `fields[-1] == "reasons"`.

**Catalog B.**
- `observable_belongs_to_another_fact` — Every list this test spells out is another fact's channel. `reasons_of(result) == [("interval","epoch"), ("epoch","final")]`: the first tuple is asserted by rule on the identical run — `by_name["checkpoint-s000002"] == ("interval","epoch")` — and the second by scope's `epoch_only` case, `reasons_of(epoch_only) == [("epoch",), ("epoch","final")]`. `shapes(result) == [(2,2,6),(3,2,8)]` is exclusions' channel (`shapes(result) == [(2,2,6),(3,3,9),(4,3,12)]`). Names are rule's `checkpoint_name` channel. The docstring's claim that observability 'is the only one that spells the end-to-end list out literally' is not accurate — rule calls `trainer.train(DATA)` under the same `e2e_config()`.
- `no_independent_content` — Subtract the siblings and the open ticket and what remains is: `CheckpointInfo(...).reasons == ()` (r1.rule's own text, 'gains a tenth and last field `reasons: Tuple[str, ...] = ()`'), the field count (entailed), the default-fixture run (r1.scope's rule at a new config), and the loss approx. No implementation that passes rule + scope + exclusions + failure_behavior can fail this test EXCEPT via the loss numbers — and those are specified by no fact at all.

**A correct build the test rejects:**

```
A ticket-only-plus-r1-compliant agent that records the batch loss at the moment of the write, rather than the window mean:

```python
# ... inside the batch loop, after the optional optimizer step
if should_optim_step:
    reasons = []
    if config.checkpoint_every_n_steps and step % config.checkpoint_every_n_steps == 0:
        reasons.append("interval")
    if config.checkpoint_every_epoch and plan.is_epoch_closing_step(step):
        reasons.append("epoch")
    if step == plan.total_steps:
        reasons.append("final")
    if reasons:
        self.save_checkpoint(
            checkpoint_name(config.checkpoint_name_prefix, step),
            step=step,
            epoch=plan.epoch_of_batch(b),
            loss=batch_loss,                      # the loss of the batch just finished
            batch_size=config.batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            batches_completed=b,
            dataset_signature=plan.dataset_signature,
            reasons=canonical_reasons(reasons),
        )
```

This satisfies every clause of r1.rule, r1.scope, r1.exclusions and r1.failure_behavior, and every clause of the visible ticket — which specifies window-mean semantics for `loss_history` only and never for `CheckpointInfo.loss`. It produces `[2.29753293127, 2.34834363696]` and fails `pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)`. `loss=running_mean_of_all_batches_so_far` and `loss=loss_history[-1]` fail the same way. The golden tree's choice is an artifact, not a stated requirement.
```

**Recommendation.** Narrow the test to the content this fact alone owns, and stop grading unspecified values.

DELETE from `test_observability__the_two_checkpoints_of_the_end_to_end_run_read_back`:
- `assert [c.loss for c in result.checkpoints] == pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)` — grades checkpoint-loss semantics that neither the ticket nor r1 states, and is the one assertion that can fail an otherwise fully correct agent. If you want to keep it, add the sentence "a checkpoint's `loss` is the arithmetic mean of the per-batch losses in the window of the step it closes" to r1.rule's text AND to the clue, so it becomes a graded requirement rather than a golden-tree artifact.
- `assert [c.path ...] == ["mock://checkpoints/..."]` — pre-existing mock path behaviour, inherited free.
- `assert [c.batch_size ...]`, `[read_field(c, "gradient_accumulation_steps") ...]`, `{read_field(c, "dataset_signature")} == {SIGNATURE}` — open-ticket fields, not r1.
- `assert reasons_of(result) == [("interval","epoch"), ("epoch","final")]` and `assert shapes(result) == [(2,2,6),(3,2,8)]` — rule already asserts the step-2 tuple on the identical `train(DATA)` run and exclusions already asserts the shapes triple; delete or, if you keep the e2e run at all, keep only `[c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]` since it is the only list rule does not spell out.

KEEP as the fact:
- `len(fields) == 10`, `fields[-2:] == ["dataset_signature", "reasons"]`, `CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()` — rule checks `save_checkpoint`'s `("interval",)` default, not the dataclass field default, so this is a genuine sliver.
- The whole `tests/finetune/test_trainer.py` default-fixture block (2 examples, `batch_size=2`, `epochs=1`, `gas=1`, no clock injected) → `total_steps == 1`, one checkpoint, `"checkpoint-s000001"`, `reasons == ("final",)`, `len(loss_history) == 1`. This is the only configuration no sibling exercises, it pins the six-digit padding at step 1 where an unpadded implementation diverges, and it doubles as regression proof that the repo's existing fixture still passes.

Also fix the docstring: "`observability` is the only one that spells the end-to-end list out literally" is false as written — `test_rule__...` runs `trainer.train(DATA)` under the same `e2e_config()` and asserts the step-2 reason tuple.


## g11.r2.rule — retest

**Divergent action.** MIN_LR_RATIO: float = 0.1 at module scope, plus the fifth keyword-only parameter and the rescaled decay body:

def learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio: float = MIN_LR_RATIO) -> float:
    effective_warmup = min(warmup_steps, total_steps)
    if 1 <= step <= effective_warmup:
        return base_lr * step / effective_warmup
    progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)
    return base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)

The blind agent writes the four-parameter signature the ticket literally prints ("learning_rate_at(step, total_steps, base_lr, warmup_steps) -> float"), no module constant, and `return base_lr * max(0.0, (total_steps - step) / max(total_steps - effective_warmup, 1))` — HF linear-to-zero — or a cosine. The concrete divergence is the `*, min_lr_ratio=MIN_LR_RATIO` parameter and the `(1.0 - (1.0 - min_lr_ratio) * progress)` factor in place of `(1.0 - progress)`.

**The assertion.** Behaviourally decisive: `assert learning_rate_at(5, 10, BASE, 4) == pytest.approx(8.5e-05, rel=1e-12)` — it is the only assertion that separates rescale-to-floor (8.5e-05) from decay-to-zero and from clamp-at-floor (both 8.333e-05). But it is NOT the assertion that fires: the test's second statement is `assert sym("MIN_LR_RATIO") == 0.1`, which every blind agent fails first, so in practice this fact is decided by a symbol name. Neither depends on r1 or on any sibling; both depend on the open ticket's `step_ledger.py` importing cleanly, since `ledger()`/`sym()` resolve through it.

**Catalog A.**
- `model_already_knows_it` — Partially, and it covers most of the behavioural content. The ramp `base_lr * step / effective_warmup` with `step == warmup_steps` first at full rate is exactly HF's `get_linear_schedule_with_warmup` inner term `float(current_step) / float(max(1, num_warmup_steps))` read 1-based — the test's `ramp == pytest.approx([2.5e-05, 5e-05, 7.5e-05, 1e-04])` is a documented convention, not a clue. `min_lr_ratio` is likewise a published public kwarg (`transformers.get_wsd_schedule(..., min_lr_ratio: float = 0)`, `get_cosine_with_min_lr_schedule_with_warmup(..., min_lr_rate=...)`) and a 10% floor is the most commonly cited value. What priors do NOT supply is the conjunction the test actually grades first: a module constant literally named `MIN_LR_RATIO` defaulting to 0.1 (transformers' default is 0) and the rescale-rather-than-clamp decay.

**Catalog B.** clean

**A blind build that passes anyway:**

```
MIN_LR_RATIO: float = 0.1  # keep a tenth of the base rate at the end of the run


def learning_rate_at(
    step: int,
    total_steps: int,
    base_lr: float,
    warmup_steps: int,
    *,
    min_lr_ratio: float = MIN_LR_RATIO,
) -> float:
    """Linear warmup, then linear decay to a floor, in optimizer steps."""
    warmup = min(warmup_steps, total_steps)
    if 1 <= step <= warmup:
        return base_lr * step / warmup
    progress = min((step - warmup) / max(total_steps - warmup, 1), 1.0)
    return base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)

An agent reproducing the transformers `get_wsd_schedule(..., min_lr_ratio=...)` idiom from priors writes this without ever seeing the clue: the ramp is HF's, the floor-instead-of-zero is standard practice, and hoisting the literal into a module constant is ordinary style in a module whose ticket already demands `STEP_UNIT_OPTIMIZER` and `DATASET_SIGNATURE_PREFIX` as exported constants. It passes every assertion in the rule test. The two improbable coincidences it needs are the exact constant name `MIN_LR_RATIO` and the default 0.1 (transformers' `min_lr_ratio` defaults to 0), so I rate this low-probability rather than likely — but it is one sample away from the bracket's one sample.
```

**A correct build the test rejects:**

```
MIN_LR_RATIO: float = 0.1


def learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio: float = MIN_LR_RATIO) -> float:
    effective_warmup = min(warmup_steps, total_steps)
    if 1 <= step <= effective_warmup:
        return base_lr * step / effective_warmup
    decayed = (total_steps - step) / max(total_steps - effective_warmup, 1)
    return base_lr * max(decayed, min_lr_ratio)   # linear decay, floored at a tenth

This is the clamp reading of "decays linearly to a floor of one tenth of the base rate": a standard linear-to-zero schedule that never falls below `min_lr_ratio * base_lr`, never negative, clamped past the end, with the same constant, the same keyword-only parameter and the same clipped-warmup behaviour. It passes the whole ramp block, the past-the-end clamp, the clipped-warmup sibling and `min_lr_ratio=0.0`, and dies on `learning_rate_at(5, 10, BASE, 4) == pytest.approx(8.5e-05)` because it returns 8.333e-05. The only clause that separates the two readings is "the floor is reached exactly at step == total_steps" — if the clue does not carry that clause or an equivalent numeric anchor, this test rejects an agent that read the clue and implemented it faithfully.
```

**Recommendation.** Retest, three changes, none of which cut the fact.

1. Clue (verify first, since I could not read it): it must contain the disambiguator, not just "floors at a tenth". State either "the floor is reached exactly at the last step" or one anchor value, e.g. "step 5 of a ten-step run with four warmup steps is 8.5e-05". Without it, the clamp implementation quoted in correct_fail is a faithful reading that the test rejects on a 2% numeric difference.

2. Test ordering: move `assert sym("MIN_LR_RATIO") == 0.1` and the `inspect.Parameter.KEYWORD_ONLY` block to the END of `test_rule__...`, after the numeric assertions. As written, the first failure for any blind agent is a symbol-name check, so the bracket's "blind fails" result measures nomenclature rather than the schedule; reordering makes the failure attributable and keeps the constant requirement.

3. Prose: condition the rule's sentence "so the floor min_lr_ratio * base_lr is reached exactly at step == total_steps" on `warmup_steps < total_steps` — as written it is contradicted by its own failure_behavior sibling, where step == total_steps == 3 returns base_lr.

Before shipping, open tinker_trainer.py:536-551 and confirm no literal 0.1 floor lives in the current `_get_learning_rate`. If one does, this is `codebase_already_does_it` and the verdict becomes cut: the ticket's "actually depends on total_steps" invites a minimal-diff port that inherits the whole curve.


## g11.r2.exclusions_or_crossover — cut

**Divergent action.** None that belongs to this fact. The only candidate is the `min(..., 1.0)` in `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)` — and that expression is written out verbatim in the sibling `rule`, so an agent who saw the clue gets it from `rule`, not from `exclusions`. The resume half's candidate ("call `learning_rate_at(plan.step_of_batch(b), plan.total_steps, ...)` after resume instead of restarting the schedule") is dictated by the open ticket's "the schedule continues from `completed_steps + 1`" plus "the learning rate of the step that batch belongs to". I cannot name code an informed agent writes and a blind one does not, attributable to this fact.

**The assertion.** `assert learning_rate_at(99, 8, BASE, 2) == pytest.approx(1e-05, rel=1e-12)` — and it depends on far more than this requirement: the literal `1e-05` is `MIN_LR_RATIO * base_lr` from the sibling `rule`, so an agent who clamps perfectly but decays to zero (the HF default) fails here for `rule`'s reason. The floor-independent version in the same test, `assert learning_rate_at(99, 8, BASE, 2) == pytest.approx(floor, rel=1e-12)`, is passed trivially by that same HF implementation (0.0 == 0.0). The remaining half of the test (`resumed.total_steps == 4`, `[current_batch] == [7..12]`, `[current_step] == [2,2,3,3,3,4]`) is decided by the open ticket's `plan_resume` and per-batch stats contract, not by anything hidden.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — "does not fall below it or go negative" and "does not re-enter warmup and does not restart the decay" are prohibitions. Re-entering warmup on resume would require deliberate extra work (resetting a step counter at resume); nobody writes that. Going below the floor requires deliberately omitting a clamp that both idiomatic spellings (`min(progress, 1.0)` / `max(lr, floor)`) include. Inaction satisfies the fact.
- `model_already_knows_it` — Clamping a linear LR schedule past its end is the documented HF convention: `get_linear_schedule_with_warmup` returns `max(0.0, float(num_training_steps - current_step) / float(max(1, num_training_steps - num_warmup_steps)))`. Past the end it yields the floor (0.0), never negative. A blind agent reproduces the clamp from priors.
- `ticket_gives_it_away` — The open ticket already says "Raising `epochs` alone is a legal resume: the plan grows and the schedule continues from `completed_steps + 1`." The fact says "A resumed run whose `epochs` grew continues down the new, longer schedule from `completed_steps + 1`." That is the same sentence. The ticket also fixes "the learning rate of the step that batch belongs to" and `total_steps = plan.total_steps`.
- `entailed_by_the_open_feature` — Given the ticket's `plan.step_of_batch(b)` + `plan.total_steps` + resume-from-`completed_steps + 1`, a resumed run mechanically walks the grown schedule; there is no alternative implementation that builds the plan from the ticket and still re-enters warmup.
- `obvious_implementation_does_it` — Any implementation of the sibling `rule` clamps: `rule` literally prescribes `progress = min(..., 1.0)`. Writing the decay without a clamp is the unnatural path, not the default one.

**Catalog B.**
- `observable_belongs_to_another_fact` — Every numeric assertion is `pytest.approx(1e-05)` — that is `MIN_LR_RATIO * base_lr`, i.e. `rule`'s observable (`assert sym("MIN_LR_RATIO") == 0.1`, `learning_rate_at(10, 10, BASE, 4) == pytest.approx(0.1 * BASE)`). The resume assertions `resumed.total_steps == 4`, `current_batch == [7..12]`, `current_step == [2,2,3,3,3,4]` are the open ticket's `plan_resume`/stats observables.
- `no_independent_content` — The clamp is half of `rule`: `rule` states `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)`. Passing `rule` as specified makes failing `exclusions` all but impossible; failing `rule`'s floor makes failing `exclusions` automatic. It restates the neighbour.

**A blind build that passes anyway:**

```
```python
# step_ledger.py -- ticket only: "learning_rate_at(step, total_steps, base_lr,
# warmup_steps) -> float ... actually depends on total_steps". Standard linear
# warmup + linear decay, HF-style.
def learning_rate_at(step: int, total_steps: int, base_lr: float, warmup_steps: int) -> float:
    effective_warmup = min(warmup_steps, total_steps)
    if effective_warmup > 0 and step <= effective_warmup:
        return base_lr * step / effective_warmup
    progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)
    return max(0.0, base_lr * (1.0 - progress))

# tinker_trainer.py, inside the batch loop -- straight from the ticket:
lr = learning_rate_at(plan.step_of_batch(b), plan.total_steps,
                      config.adam_params.learning_rate, config.warmup_steps)
```
This satisfies every clause of the fact as written: past the end the rate is clamped at its floor and equal to the value at `total_steps` (`learning_rate_at(99, 8, 1e-4, 2) == learning_rate_at(8, 8, 1e-4, 2)`), it never goes below it or negative (`max(0.0, ...)` plus `min(progress, 1.0)`), and because the LR is derived from `plan.step_of_batch(b)` and `plan.total_steps` of the regrown plan, a resume with larger `epochs` continues down the new, longer schedule from `completed_steps + 1` without re-entering warmup or restarting the decay. It fails the graded test on exactly one thing — the floor's *value* is 0.0 rather than `0.1 * base_lr` — which is the sibling `rule`'s content, not this fact's.
```

**A correct build the test rejects:**

```
```python
# A legitimate reading of "the schedule continues from completed_steps + 1":
# the resumed process advances its own step counter from the checkpoint,
# rather than re-deriving each batch's step from the global plan.
self._completed_steps = self._resume_from.batches_completed // plan.gradient_accumulation_steps  # 2
...
for b in range(start_batch_ordinal + 1, plan.total_batches + 1):
    if plan.is_step_boundary(b):
        self._completed_steps += 1
    lr = learning_rate_at(self._completed_steps + 1, plan.total_steps, base_lr, config.warmup_steps)
```
This continues from `completed_steps + 1` down the new longer schedule, never re-enters warmup and never restarts the decay — exactly what the fact asks — but it reports the *upcoming* step's rate after a boundary, so the last window carries `learning_rate_at(5, 4, ...)` (still the clamped floor, fine) while batches 7-8 carry step 3 and batch 9 flips early; the vector shifts and `rates == pytest.approx([5.5e-05]*3 + [1e-05]*3)` fails. The test also rejects any agent whose `plan_resume` is off by one (`[current_batch] == [7,8,9,10,11,12]`, `[current_step] == [2,2,3,3,3,4]`) even when `learning_rate_at` is byte-for-byte correct — a correct r2 failing on the open feature's contract.
```

**Recommendation.** Cut r2.exclusions_or_crossover; do not try to narrow it. The two halves fail in opposite directions and neither can be rescued. (1) The resume half is stated in the open ticket almost verbatim — "Raising `epochs` alone is a legal resume: the plan grows and the schedule continues from `completed_steps + 1`" — and its assertions (`resumed.total_steps == 4`, the `current_batch`/`current_step` vectors) grade `plan_resume`, an open-feature obligation; delete that half outright and let the resume contract be graded where it belongs. (2) The clamp half is a double bind: asserted absolutely (`== 1e-05`) it re-measures `rule`'s `MIN_LR_RATIO`, so it cannot fail unless `rule` already failed; asserted relatively (`learning_rate_at(99,...) == learning_rate_at(8,...)`, `min(...) >= 0`) it is passed for free by the HF `max(0.0, ...)` idiom that a blind agent writes from priors. Either way it carries no signal of its own. If r2 needs a fourth measurement, replace it with something `rule`'s formula does not already contain — e.g. the interaction the ticket leaves genuinely open: that `warmup_steps` is clipped by `min(warmup_steps, total_steps)` against the *grown* plan on resume, or the `min_lr_ratio=0.0` / `min_lr_ratio=1.0` boundary behaviour — and move the surviving `min(...) >= 0.0` sanity check into `rule`, whose formula it belongs to.


## g11.r2.failure_behavior — retest

**Divergent action.** `effective_warmup = min(warmup_steps, total_steps)` used as the warmup denominator (and as the origin of the decay segment), instead of the canonical HF port `if step < warmup_steps: return base_lr * step / max(1, warmup_steps)`. That single `min(...)` is the entire code difference this fact measures; with `total_steps=3, warmup_steps=10` the clipped form yields `base_lr * step / 3` and the unclipped form yields `base_lr * step / 10`.

**The assertion.** `assert clipped == pytest.approx([BASE / 3, 2 * BASE / 3, BASE], rel=1e-12)` where `clipped = [learning_rate_at(step, 3, BASE, 10) for step in range(1, 4)]`. It depends on nothing but `learning_rate_at` -- no trainer, clock, RNG, plan, or checkpoint -- but it also does not depend on r2's distinctive content: a pure-warmup window has no decay segment, so `MIN_LR_RATIO` and the floor are untouched. The assertion is decided solely by whether the implementation clips, which is the sibling `rule`'s stated formula.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Half the fact is the negative "rather than raising". The ticket mandates `StepLedgerError` only for `plan_steps` arguments (`num_examples == 0`, `batch_size/epochs/gradient_accumulation_steps < 1`) and never for `learning_rate_at`; an agent has to go out of its way to add a raise here. The assertion "nothing raised" is passed by every implementation that simply didn't think about it.
- `obvious_implementation_does_it` — `warmup = max(min(int(warmup_steps), total_steps), 0)` is a routine defensive normalisation, and an engineer told the schedule must be "a function of the run's length" is nudged toward exactly it. See blind_pass: that implementation decays to zero (wrong for r2 generally) yet passes every assertion of this fact. Additionally the inclusive-vs-exclusive warmup convention is invisible here -- with `if step < warmup` the step numbered `warmup` falls to the decay branch at `progress == 0`, which is `base_lr` regardless -- so the clip is the sole discriminator.

**Catalog B.**
- `no_independent_content` — The sibling `rule` states the clip literally: "with `effective_warmup = min(warmup_steps, total_steps)`, for `1 <= step <= effective_warmup` the rate is `base_lr * step / effective_warmup`". An agent that implements `rule` as written passes this fact with zero additional code -- the fact is arithmetic on a neighbour's formula, not a second decision. Its saving grace is that the *test* still discriminates (an unclipped implementation passes `rule`'s test, whose `warmup=4 < total=10` never exercises the `min`, and fails this one), so it is a measurement worth keeping even though it is not independent content.

**A blind build that passes anyway:**

```
def learning_rate_at(step, total_steps, base_lr, warmup_steps):
    total_steps = max(int(total_steps), 1)
    warmup = max(min(int(warmup_steps), total_steps), 0)   # don't warm up past the run
    if warmup and step <= warmup:
        return base_lr * step / warmup
    progress = (step - warmup) / max(total_steps - warmup, 1)
    return base_lr * max(0.0, 1.0 - progress)              # linear decay to zero

# Ticket-only: no MIN_LR_RATIO, no keyword-only min_lr_ratio, decays to ZERO --
# fails r2.rule, r2.exclusions and r2.observability. But it passes every
# assertion of r2.failure_behavior:
#   [learning_rate_at(s, 3, 1e-4, 10) for s in range(1, 4)] == [1e-4/3, 2e-4/3, 1e-4]
#   [learning_rate_at(s, 4, 1e-4, 4)  for s in range(1, 5)] == [2.5e-5, 5e-5, 7.5e-5, 1e-4]
#   min(clipped) > 0.0
#   learning_rate_at(1, 1, 1e-4, 99) == 1e-4
```

**Recommendation.** Retest. The fact is real (clipping is a genuine decision the ticket does not imply, and HF's published scheduler does not do it), but as written the test is passable by a blind decay-to-zero implementation that adds one defensive `min(...)`, and it deliberately excludes the floor that is r2's actual hidden content. Add one assertion to `test_failure_behavior__a_warmup_longer_than_the_run_is_clipped_to_it` that reads one step past the clipped ramp, where the clip and the floor are measured jointly:

    # Clipping the warmup does not remove the floor: past the (clipped) ramp the
    # rate sits at a tenth of the base rate, not at zero and not still ramping.
    assert learning_rate_at(5, 3, BASE, 10) == pytest.approx(1e-05, rel=1e-12)
    assert learning_rate_at(4, 3, BASE, 10) == pytest.approx(1e-05, rel=1e-12)

An unclipped implementation returns 5e-05/4e-05 (still ramping), a decay-to-zero implementation returns 0.0, and the blind implementation in `blind_pass` returns 0.0 and now fails. Only `effective_warmup = min(warmup_steps, total_steps)` combined with the `min_lr_ratio` floor lands on 1e-05. Also drop or replace the second assertion (`[learning_rate_at(step, 4, BASE, 4) ...]`), whose expected vector is byte-for-byte `rule`'s `ramp` check and re-measures the neighbour rather than the clip.


## g11.r2.observability — narrow

**Divergent action.** Two expressions inside `learning_rate_at`, both of which a ticket-only agent has no reason to write: (1) the floor factor in the decay branch — `return base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)` with `min_lr_ratio` defaulting to `0.1`, instead of the reflexive `return base_lr * (1.0 - progress)` (HF `get_linear_schedule_with_warmup`, decay to zero) or the current code's flat-after-warmup return; and (2) `effective_warmup = min(warmup_steps, total_steps)` with NO `max(..., 1)` division guard, so `warmup_steps=0` skips the ramp entirely and `progress = (step - 0) / max(total_steps, 1)` puts step 1 of a 4-step run at `7.75e-05`. The guard is the thing an ordinary engineer adds by instinct to avoid `ZeroDivisionError` on `base_lr * step / effective_warmup`, and adding it is the single deviation this fact catches that its `rule` sibling does not.

**The assertion.** `assert [learning_rate_at(step, 4, BASE, 0) for step in range(1, 5)] == pytest.approx([7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12)` — this is the only line in the test that can fail while `rule`, `exclusions`, `failure_behavior` and the whole open ticket pass (it is the one probe of `warmup_steps == 0`, i.e. of the absent `max(..., 1)` guard). It is a pure-function call and depends on nothing but r2's implementation. The test's other deciders do not have that property: the 8-step vector is `rule`'s formula re-evaluated and cannot fail alone, and the e2e assertion `[read_field(s, "learning_rate") for s in recorder.stats] == pytest.approx([5e-05]*3 + [1e-04]*3 + [1e-05]*2)` also depends on `plan_steps`, `step_of_batch`, the stats-push cadence and the two-reading clock, all open-ticket work.

**Catalog A.**
- `model_already_knows_it` — PARTIAL BUT REAL. The whole fact reduces to one constant, `1 - 0.1 = 0.9`. "decay to one tenth of the peak learning rate" is the single most-published LLM-training convention (GPT-3, Chinchilla, Llama all decay to `0.1 * max_lr`; Transformers ships `cosine_with_min_lr` / `min_lr_rate`, Megatron ships `--min-lr`). A blind agent asked for a schedule that "actually depends on total_steps" for fine-tuning can reach `min_lr = 0.1 * base_lr` from priors alone, without any clue. What still protects the fact is that the ticket never says *linear*, and the prior most strongly attaches to *cosine* decay — cosine to a 0.1 floor gives step 3 of 8 as ~9.6e-05, not `8.5e-05`, and fails. So the risk is a coin-flip on top of a prior, not a free pass; but it is the residual coincidence route and it lives entirely in this fact's numbers.

**Catalog B.**
- `observable_belongs_to_another_fact` — For the e2e third only. `assert result.total_steps == 3` is decided by the open ticket's `plan_steps` (`ceil(total_batches / gradient_accumulation_steps)`), and the 8-element ordering is decided by the open ticket's per-batch stats cadence and `plan.step_of_batch`. An agent with a perfect `learning_rate_at` but an off-by-one in `step_of_batch`, or that pushes stats before the optimizer step, fails r2.observability for reasons that are not r2. It also shares its channel with `exclusions`, which reads `read_field(s, "learning_rate")` off the same recorder for the resumed run.
- `no_independent_content` — PARTIAL. The headline vector `[learning_rate_at(s, 8, 1e-4, 2) for s in range(1,9)]` is `rule`'s formula evaluated: `rule` already states `effective_warmup = min(warmup_steps, total_steps)`, `progress = min((step - effective_warmup)/max(total_steps - effective_warmup, 1), 1.0)`, `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)`, and `MIN_LR_RATIO = 0.1`. Any implementation of that literal formula reproduces all eight numbers; the assertion cannot fail unless `rule` fails. Genuinely unique to this fact are only the zero-warmup vector (which catches the `max(warmup, 1)` guard that `rule` lets through) and the end-to-end wiring.

**A blind build that passes anyway:**

```
def learning_rate_at(step: int, total_steps: int, base_lr: float, warmup_steps: int) -> float:
    """Linear warmup, then linear decay to a tenth of the peak rate.

    Decaying to 10% of peak rather than to zero is the usual LLM fine-tuning
    schedule; a rate of zero on the last step wastes the step.
    """
    effective_warmup = min(warmup_steps, total_steps)
    if step <= effective_warmup:
        return base_lr * step / effective_warmup
    progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)
    return base_lr * (1.0 - 0.9 * progress)

# Ticket-only reasoning that produces it: the ticket demands the schedule
# "actually depends on total_steps", the agent reaches for the convention it
# already knows (Chinchilla / Llama / HF `min_lr_rate`: decay to 0.1 * peak),
# picks *linear* because the module is a plain arithmetic leaf with no cosine
# anywhere near it, and writes `min(warmup_steps, total_steps)` because the
# ticket's own `trailing_window_batches` / `batches_per_edge` style already has
# it clamping everywhere. No `max(effective_warmup, 1)` guard, because the
# division sits behind `step <= effective_warmup`, which is False when
# effective_warmup is 0 -- the guard is unnecessary *if* you write the branch
# this way, and this is a natural way to write it.

This is not the likely blind write -- decay-to-zero is -- but it is a reachable
one, and note the last comment: the `max(warmup, 1)` guard that this fact's
unique assertion is designed to catch is only tempting when the ramp branch is
written as `if step < warmup` with the division outside the guard. An agent that
writes `if step <= effective_warmup:` never needs the guard and passes the
zero-warmup vector by construction.
```

**Recommendation.** Narrow, do not cut — the fact is real, the numbers are internally consistent, and I could not construct a legitimate reading that the test rejects (any implementation of the stated `rule` formula reproduces all three clauses exactly; `rel=1e-12` is ~4500 ULPs, so algebraically-equivalent rearrangements of `base_lr * (1 - (1 - r) * p)` are safe). Three concrete changes:

1. Demote the headline vector. `[learning_rate_at(s, 8, 1e-4, 2) for s in range(1, 9)] == [5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05]` is `rule`'s formula evaluated and decides nothing `rule` does not already decide. Keep it in the test as regression, but stop treating it as this fact's content.

2. Promote the zero-warmup clause to the fact's centre and make it explicit about what it rejects, so the clue must convey it: "`warmup_steps=0` means no ramp at all, not a one-step ramp — `learning_rate_at(1, 4, 1e-4, 0) == 7.75e-05`, not `1e-04`; `effective_warmup` is `min(warmup_steps, total_steps)` with no lower clamp." This is the one deviation the fact uniquely catches, and today it is buried as the second of three clauses.

3. Decontaminate the e2e clause. Replace `assert result.total_steps == 3` and the bare 8-element literal with an assertion that fails only on the rate: `assert sorted(set(rates)) == pytest.approx([1e-05, 5e-05, 1e-04])` alongside the existing per-window vector, so a ticket-level off-by-one in `step_of_batch` or the stats cadence fails the open suite (where it belongs) rather than being scored against r2.

Separately, flag for the requirement as a whole (owned by `rule`, not by this fact): the constant `0.1` is a published convention, so `MIN_LR_RATIO` alone is a weaker discriminator than the bracket's single blind sample suggests. What is actually carrying the discrimination is *linear* decay to that floor plus the un-guarded zero warmup. If r2 needs hardening, harden it there — e.g. have the clue and the rule pin a non-conventional ratio — not by adding more vectors.
