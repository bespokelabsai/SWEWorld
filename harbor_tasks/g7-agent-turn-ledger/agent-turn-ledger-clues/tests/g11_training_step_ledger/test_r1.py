"""g11 — hidden requirement r1: why a checkpoint was written, and under what name.

    rule            CHECKPOINT_REASONS, canonical_reasons' ledger (not alphabetical)
                    order, the zero-padded `{prefix}-s{step:06d}` name, and one
                    save_checkpoint call for a step that fires several triggers
    scope           "final" fires at total_steps whatever the configuration, while
                    "interval" and "epoch" stay conditional; Fireworks writes none
    exclusions      the recorded `epoch` is plan.epoch_of_batch(batches_completed),
                    the position, never the epoch whose end triggered the write
    failure_behavior  a reason outside the vocabulary raises StepLedgerError, and a
                    repeat under the last name merges in place instead of appending
    observability   the two checkpoints of the end-to-end run, the ten fields of
                    CheckpointInfo, and the lone "final" of the default fixture

The five are five measurements. `rule` never runs the epochs=3 plan, `scope`
never reads an `epoch` number, `exclusions` never disables a trigger,
`failure_behavior` never runs `train()`, and `observability` is the only one that
spells the end-to-end list out literally.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from harness import read_field, require_feature

from test_open import (
    DATA,
    SIGNATURE,
    FireworksTrainer,
    FireworksTrainerConfig,
    TinkerTrainer,
    TinkerTrainerConfig,
    CheckpointInfo,
    e2e_config,
    clock_for,
    has_ledger,
    ledger,
    mock_env,
    sym,
)


def run(config, data=DATA):
    """A mock run of the Tinker trainer under an injected clock."""
    return TinkerTrainer(config, clock=clock_for(1000.0, 1004.5)).train(data)


def shapes(result):
    return [(c.step, c.epoch, read_field(c, "batches_completed")) for c in result.checkpoints]


def reasons_of(result):
    return [tuple(read_field(c, "reasons")) for c in result.checkpoints]


def test_rule__the_three_trigger_names_in_ledger_order_under_one_padded_name(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    canonical_reasons = sym("canonical_reasons")
    checkpoint_name = sym("checkpoint_name")

    assert tuple(sym("CHECKPOINT_REASONS")) == ("interval", "epoch", "final")
    # Graded as a template rather than as a string literal, so `{step:06}` and
    # `{step:06d}` -- the same padding, written two ways -- both count.
    assert sym("CHECKPOINT_NAME_TEMPLATE").format(prefix="checkpoint", step=2) == "checkpoint-s000002"

    # Ledger order, deduplicated -- interval, then epoch, then final. Alphabetical
    # order would be ("epoch", "final", "interval"); noticing order would be the
    # tuple as handed in.
    assert tuple(canonical_reasons(("final", "epoch", "interval", "epoch"))) == ("interval", "epoch", "final")
    assert tuple(canonical_reasons(("final", "interval"))) == ("interval", "final")
    assert tuple(canonical_reasons(("epoch", "interval"))) == ("interval", "epoch")
    assert tuple(canonical_reasons(("final", "epoch"))) == ("epoch", "final")
    assert tuple(canonical_reasons(())) == ()
    assert tuple(canonical_reasons(("epoch", "epoch"))) == ("epoch",)

    # The step is zero-padded to six digits, so names sort lexicographically.
    assert checkpoint_name("checkpoint", 2) == "checkpoint-s000002"
    assert checkpoint_name("ckpt", 1234567) == "ckpt-s1234567"
    assert sorted(checkpoint_name("checkpoint", step) for step in (2, 10, 100)) == [
        "checkpoint-s000002",
        "checkpoint-s000010",
        "checkpoint-s000100",
    ]

    # `reasons` is the tenth and last field, and a checkpoint written without one
    # is an interval checkpoint.
    fields = [f.name for f in dataclasses.fields(CheckpointInfo)]
    assert fields[-1] == "reasons"
    parameter = inspect.signature(TinkerTrainer.save_checkpoint).parameters["reasons"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert tuple(parameter.default) == ("interval",)

    trainer = TinkerTrainer(e2e_config(), clock=clock_for(1000.0, 1004.5))
    defaulted = trainer.save_checkpoint("solo", step=1, epoch=1, loss=0.5)
    assert tuple(read_field(defaulted, "reasons")) == ("interval",)

    # A step that fires several triggers is written once, not once per trigger.
    trainer = TinkerTrainer(e2e_config(), clock=clock_for(1000.0, 1004.5))
    calls = []
    inner = trainer.save_checkpoint

    def watched(*args, **kwargs):
        record = inner(*args, **kwargs)
        calls.append(kwargs.get("name", args[0] if args else None))
        return record

    monkeypatch.setattr(trainer, "save_checkpoint", watched)
    result = trainer.train(DATA)

    # Step 2 fires "interval" (2 % 2 == 0) and "epoch" (it closes epoch 1's window).
    assert calls.count("checkpoint-s000002") == 1, f"step 2 was written {calls.count('checkpoint-s000002')} times: {calls}"
    assert len(calls) == len(set(calls)) == len(result.checkpoints)
    by_name = {c.name: tuple(read_field(c, "reasons")) for c in result.checkpoints}
    assert by_name["checkpoint-s000002"] == ("interval", "epoch")


def test_scope__the_final_step_is_checkpointed_whatever_the_configuration(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    # Neither checkpoint option asked for anything, and the run still ends with one.
    bare = run(e2e_config(checkpoint_every_n_steps=0, checkpoint_every_epoch=False))
    assert bare.total_steps == 3
    assert [c.step for c in bare.checkpoints] == [3]
    assert reasons_of(bare) == [("final",)]

    # "interval" stays conditional on checkpoint_every_n_steps ...
    interval_only = run(e2e_config(checkpoint_every_n_steps=2, checkpoint_every_epoch=False))
    assert [c.step for c in interval_only.checkpoints] == [2, 3]
    assert reasons_of(interval_only) == [("interval",), ("final",)]

    # ... and "epoch" on checkpoint_every_epoch, while "final" fires under both.
    epoch_only = run(e2e_config(checkpoint_every_n_steps=0, checkpoint_every_epoch=True))
    assert [c.step for c in epoch_only.checkpoints] == [2, 3]
    assert reasons_of(epoch_only) == [("epoch",), ("epoch", "final")]

    # A run of a single optimizer step is still checkpointed, exactly once.
    single = run(e2e_config(epochs=1, gradient_accumulation_steps=4, checkpoint_every_n_steps=0, checkpoint_every_epoch=False))
    assert single.total_steps == 1
    assert [c.step for c in single.checkpoints] == [1]
    assert reasons_of(single) == [("final",)]

    # Fireworks is out of scope: it writes no checkpoints and gains no reasons.
    require_feature(has_ledger(), "the checkpoint reason vocabulary")
    fw = FireworksTrainer(FireworksTrainerConfig(base_model="qwen3-4b", epochs=4, seed=0, api_key=None))
    fw_result = fw.train(DATA[:3])
    assert fw_result.checkpoints == []
    assert "reasons" not in fw_result.metadata


def test_exclusions__the_recorded_epoch_is_the_position_not_the_trigger(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    # 10 examples, 4 batches an epoch, 3 epochs, windows of 3 batches:
    #   step 2 closes the window holding epoch 1's last batch (batch 4) at batch 6,
    #   step 3 closes the window holding epoch 2's last batch (batch 8) at batch 9,
    #   step 4 closes epoch 3 at batch 12.
    result = run(e2e_config(epochs=3, checkpoint_every_n_steps=0, checkpoint_every_epoch=True))
    plan = result.step_plan

    assert [c.step for c in result.checkpoints] == [2, 3, 4]
    for checkpoint in result.checkpoints:
        assert "epoch" in read_field(checkpoint, "reasons")

    # The epoch a checkpoint records is where its batch position falls, so the
    # write that carries epoch 1's "epoch" trigger records epoch 2, and epoch 2's
    # records epoch 3. Reading the trigger instead would give (1, 2, 3).
    assert shapes(result) == [(2, 2, 6), (3, 3, 9), (4, 3, 12)]
    assert [c.epoch for c in result.checkpoints] == [plan.epoch_of_batch(b) for b in (6, 9, 12)]
    assert [c.epoch for c in result.checkpoints] != [1, 2, 3]


def test_failure_behavior__an_unknown_reason_is_refused_and_a_repeat_name_merges(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    canonical_reasons = sym("canonical_reasons")
    StepLedgerError = sym("StepLedgerError")

    with pytest.raises(StepLedgerError):
        canonical_reasons(("periodic",))
    with pytest.raises(StepLedgerError):
        canonical_reasons(("interval", "manual"))
    with pytest.raises(StepLedgerError):
        canonical_reasons(("Interval",))

    # A second save under the name the ledger already ends with replaces that
    # entry: the reasons merge through the ledger order and the new loss wins.
    trainer = TinkerTrainer(e2e_config(), clock=clock_for(1000.0, 1004.5))
    trainer.save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))
    merged = trainer.save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.25, reasons=("final",))

    # The merge is the fact here; the ORDER the two reasons come back in is
    # r1.rule's, so this reads the content and leaves the ordering to that test.
    stored = trainer.get_checkpoints()
    assert len(stored) == 1
    assert sorted(read_field(stored[0], "reasons")) == ["final", "interval"]
    assert stored[0].loss == 0.25
    assert sorted(read_field(merged, "reasons")) == ["final", "interval"]
    assert merged.loss == 0.25

    # A different name is a different checkpoint, and still appends.
    trainer.save_checkpoint("checkpoint-s000003", step=3, epoch=2, loss=0.125, reasons=("final",))
    assert [c.name for c in trainer.get_checkpoints()] == ["checkpoint-s000002", "checkpoint-s000003"]


def test_observability__the_two_checkpoints_of_the_end_to_end_run_read_back(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    fields = [f.name for f in dataclasses.fields(CheckpointInfo)]
    assert len(fields) == 10
    assert fields[-2:] == ["dataset_signature", "reasons"]
    assert CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()

    result = run(e2e_config())
    assert [c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]
    assert reasons_of(result) == [("interval", "epoch"), ("epoch", "final")]
    assert shapes(result) == [(2, 2, 6), (3, 2, 8)]
    assert [c.path for c in result.checkpoints] == [
        "mock://checkpoints/checkpoint-s000002",
        "mock://checkpoints/checkpoint-s000003",
    ]
    assert [c.batch_size for c in result.checkpoints] == [3, 3]
    assert [read_field(c, "gradient_accumulation_steps") for c in result.checkpoints] == [3, 3]
    assert {read_field(c, "dataset_signature") for c in result.checkpoints} == {SIGNATURE}
    assert [c.loss for c in result.checkpoints] == pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)

    # The default-config fixture of tests/finetune/test_trainer.py: two examples,
    # batch_size 2, one epoch, no checkpoint option set at all.
    fixture_config = TinkerTrainerConfig(base_model="Qwen3-8B", epochs=1, batch_size=2)
    fixture_data = [
        {"messages": [{"role": "user", "content": "What is Python?"}, {"role": "assistant", "content": "Python is a programming language."}]},
        {"messages": [{"role": "user", "content": "What is Java?"}, {"role": "assistant", "content": "Java is also a programming language."}]},
    ]
    fixture_result = TinkerTrainer(fixture_config).train(fixture_data)
    assert fixture_result.total_steps == 1
    assert len(fixture_result.checkpoints) == 1
    assert fixture_result.checkpoints[0].name == "checkpoint-s000001"
    assert tuple(read_field(fixture_result.checkpoints[0], "reasons")) == ("final",)
    assert len(fixture_result.loss_history) == 1
    assert fixture_result.final_loss > 0
