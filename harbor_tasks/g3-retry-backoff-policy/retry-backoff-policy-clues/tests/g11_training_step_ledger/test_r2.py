"""g11 — hidden requirement r2: what a learning rate comes to, step by step.

    rule            MIN_LR_RATIO = 0.1 and the keyword-only min_lr_ratio; warmup is
                    inclusive and 1-based, so step `warmup_steps` is the first step
                    at the full base rate and step 1 is never zero; after it the
                    rate decays linearly to a floor of one tenth of the base rate,
                    reached exactly at total_steps
    exclusions      past the end the rate is clamped at that floor, never lower and
                    never negative; a resumed run whose epochs grew walks down the
                    new, longer schedule from completed_steps + 1 rather than
                    re-entering warmup
    failure_behavior  a warmup longer than the run is clipped to the run instead of
                    raising: three steps of pure warmup ending exactly at base_lr
    observability   the two stated vectors, and the three rates the end-to-end run
                    pushes onto TrainingStats.learning_rate

The four are four measurements. `rule` works a ten-step schedule and the custom
ratio, `exclusions` is the only one that reads past the end or resumes anything,
`failure_behavior` is the only one whose warmup outruns the run, and
`observability` is the only one that spells the stated vectors out literally.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from harness import read_field

from test_open import (
    DATA,
    SIGNATURE,
    CheckpointInfo,
    TinkerTrainer,
    clock_for,
    e2e_config,
    ledger,
    mock_env,
    record_stats,
    sym,
)

BASE = 1e-4


def test_rule__inclusive_warmup_then_a_linear_decay_to_a_tenth_of_the_base_rate(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    learning_rate_at = sym("learning_rate_at")
    assert sym("MIN_LR_RATIO") == 0.1

    parameter = inspect.signature(learning_rate_at).parameters["min_lr_ratio"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default == 0.1

    # Ten steps, four of warmup. The ramp is inclusive and 1-based: the step
    # numbered `warmup_steps` is the first at the full base rate, and the first
    # optimizer step is never zero.
    ramp = [learning_rate_at(step, 10, BASE, 4) for step in range(1, 5)]
    assert ramp == pytest.approx([2.5e-05, 5e-05, 7.5e-05, 1e-04], rel=1e-12)
    assert ramp[0] > 0.0

    # After warmup it decays -- neither flat nor to zero -- and lands on a tenth
    # of the base rate exactly at total_steps.
    assert learning_rate_at(5, 10, BASE, 4) == pytest.approx(8.5e-05, rel=1e-12)
    assert learning_rate_at(7, 10, BASE, 4) == pytest.approx(5.5e-05, rel=1e-12)
    assert learning_rate_at(10, 10, BASE, 4) == pytest.approx(0.1 * BASE, rel=1e-12)
    assert learning_rate_at(5, 10, BASE, 4) < learning_rate_at(4, 10, BASE, 4)

    # The decay is linear in the step, so equal step gaps are equal rate gaps.
    after = [learning_rate_at(step, 10, BASE, 4) for step in range(4, 11)]
    gaps = [round(a - b, 15) for a, b in zip(after, after[1:])]
    assert gaps == pytest.approx([1.5e-05] * 6, rel=1e-9)

    # The floor is the parameter's, not a hard-coded tenth.
    assert learning_rate_at(10, 10, BASE, 4, min_lr_ratio=0.5) == pytest.approx(5e-05, rel=1e-12)
    assert learning_rate_at(7, 10, BASE, 4, min_lr_ratio=0.5) == pytest.approx(7.5e-05, rel=1e-12)
    assert learning_rate_at(10, 10, BASE, 4, min_lr_ratio=0.0) == pytest.approx(0.0, abs=1e-18)

    # And the schedule is a function of the run's length.
    assert learning_rate_at(5, 10, BASE, 0) != pytest.approx(learning_rate_at(5, 100, BASE, 0), rel=1e-6)


def test_exclusions__clamped_past_the_end_and_a_grown_run_never_re_enters_warmup(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    learning_rate_at = sym("learning_rate_at")

    # Past the last step the rate sits on the floor: not lower, not negative.
    floor = learning_rate_at(8, 8, BASE, 2)
    assert floor == pytest.approx(1e-05, rel=1e-12)
    assert learning_rate_at(9, 8, BASE, 2) == pytest.approx(1e-05, rel=1e-12)
    assert learning_rate_at(99, 8, BASE, 2) == pytest.approx(1e-05, rel=1e-12)
    assert learning_rate_at(10_000, 8, BASE, 2) == pytest.approx(1e-05, rel=1e-12)
    assert learning_rate_at(99, 8, BASE, 2) == pytest.approx(floor, rel=1e-12)
    assert min(learning_rate_at(step, 8, BASE, 2) for step in range(1, 200)) >= 0.0

    # A resume whose only change is a longer run continues down the NEW schedule
    # from completed_steps + 1. Six batches are behind it (two optimizer steps);
    # the remaining six run as steps 3 and 4 of a four-step plan.
    checkpoint = CheckpointInfo(
        name="checkpoint-s000002",
        path="mock://checkpoints/checkpoint-s000002",
        step=2,
        epoch=2,
        loss=2.3,
        batch_size=3,
        gradient_accumulation_steps=3,
        batches_completed=6,
        dataset_signature=SIGNATURE,
    )

    recorder = record_stats(monkeypatch)
    trainer = TinkerTrainer(e2e_config(epochs=3), clock=clock_for(2000.0, 2001.0))
    assert trainer.load_checkpoint(checkpoint) is True
    resumed = trainer.train(DATA)

    assert resumed.total_steps == 4
    assert [read_field(s, "current_batch") for s in recorder.stats] == [7, 8, 9, 10, 11, 12]
    assert [read_field(s, "current_step") for s in recorder.stats] == [2, 2, 3, 3, 3, 4]

    # Steps 3 and 4 of the grown schedule -- 5.5e-05 and the floor. Re-entering
    # warmup would give 5e-05 and 1e-04; restarting the decay would not.
    rates = [read_field(s, "learning_rate") for s in recorder.stats]
    assert rates == pytest.approx([5.5e-05] * 3 + [1e-05] * 3, rel=1e-12)
    assert rates == pytest.approx(
        [learning_rate_at(3, 4, BASE, 2)] * 3 + [learning_rate_at(4, 4, BASE, 2)] * 3, rel=1e-12
    )


def test_failure_behavior__a_warmup_longer_than_the_run_is_clipped_to_it(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    learning_rate_at = sym("learning_rate_at")

    # Ten warmup steps over a three-step run: pure warmup, ending exactly at
    # base_lr, with no decay segment at all.
    clipped = [learning_rate_at(step, 3, BASE, 10) for step in range(1, 4)]
    assert clipped == pytest.approx([BASE / 3, 2 * BASE / 3, BASE], rel=1e-12)
    assert clipped[-1] == pytest.approx(BASE, rel=1e-12)

    # A warmup exactly as long as the run behaves the same way.
    assert [learning_rate_at(step, 4, BASE, 4) for step in range(1, 5)] == pytest.approx(
        [2.5e-05, 5e-05, 7.5e-05, 1e-04], rel=1e-12
    )

    # Nothing below the ramp, nothing raised, nothing negative.
    assert min(clipped) > 0.0
    assert learning_rate_at(1, 1, BASE, 99) == pytest.approx(BASE, rel=1e-12)


def test_observability__the_stated_rate_vectors_and_the_three_rates_of_the_run(monkeypatch):
    ledger()
    mock_env(monkeypatch)

    learning_rate_at = sym("learning_rate_at")

    assert [learning_rate_at(step, 8, BASE, 2) for step in range(1, 9)] == pytest.approx(
        [5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], rel=1e-12
    )
    assert [learning_rate_at(step, 4, BASE, 0) for step in range(1, 5)] == pytest.approx(
        [7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12
    )

    # The end-to-end run: three optimizer steps at 5e-05, 1e-04 and 1e-05, carried
    # by the batches of each accumulation window.
    recorder = record_stats(monkeypatch)
    result = TinkerTrainer(e2e_config(), clock=clock_for(1000.0, 1004.5)).train(DATA)
    assert result.total_steps == 3
    assert [read_field(s, "learning_rate") for s in recorder.stats] == pytest.approx(
        [5e-05, 5e-05, 5e-05, 1e-04, 1e-04, 1e-04, 1e-05, 1e-05], rel=1e-12
    )
