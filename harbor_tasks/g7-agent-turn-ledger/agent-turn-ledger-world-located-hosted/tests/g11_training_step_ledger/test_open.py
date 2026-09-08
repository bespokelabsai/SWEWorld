"""g11 — the openly stated feature: one step unit, one checkpoint identity, one resume contract.

Everything asserted here is spelled out in the ticket: the new leaf module
`finetune/step_ledger.py` and the names it exports, `StepLedgerError` under
`ValueError`, the two frozen dataclasses and their field orders, the
optimizer-step arithmetic of `plan_steps` (window spanning the epoch boundary,
short trailing window still a whole step), the `ds1-<count>-<digest>` dataset
signature, `plan_packed_steps`, the appended-and-defaulted fields on
`CheckpointInfo` / `TrainingStats` / `TrainingResult`, `seed` on both configs,
the rebuilt `TinkerTrainer.train` loop (one `TrainingStats` per batch, the
in-loop flush of the trailing window, `loss_history` as one window mean per
marked step), the injected `clock` and `rng`, `plan_resume`'s three refusals and
its restart-at-the-next-batch, and the packed plan Fireworks reports.

Nothing here touches a hidden fact. It never asserts WHY a checkpoint was
written (r1: the reason vocabulary, its ledger order, the unconditional final
checkpoint, the position-derived epoch, the merge by name, the `-s%06d` name
template) and it never asserts WHAT a learning rate comes to (r2: the inclusive
1-based warmup, the decay to a tenth, the clamp, the clipped warmup). The
checkpoints it needs it builds by hand, and it reads no `learning_rate` anywhere.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import random
import sys
from types import SimpleNamespace

import pytest

from harness import read_field

# Imported defensively and re-raised inside the test rather than at collection
# time: a missing `step_ledger` module is one fact failing per requirement, not
# three files pytest refuses to collect and a scoreboard with no rows on it.
IMPORT_ERROR = None
try:
    from bespokelabs.curator.finetune import step_ledger as sl
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    sl = None

from bespokelabs.curator.finetune.config import FireworksTrainerConfig, TinkerTrainerConfig
from bespokelabs.curator.finetune.trainer import FireworksTrainer, TinkerTrainer
from bespokelabs.curator.finetune.types import CheckpointInfo, TrainingResult, TrainingStats


# ---------------------------------------------------------------------------
# Finding the names, wherever the implementation chose to keep them
# ---------------------------------------------------------------------------
_CANDIDATE_MODULES = (
    "bespokelabs.curator.finetune.step_ledger",
    "bespokelabs.curator.finetune",
    "bespokelabs.curator.finetune.types",
    "bespokelabs.curator.finetune.config",
    "bespokelabs.curator.finetune.trainer.tinker_trainer",
    "bespokelabs.curator.finetune.trainer.fireworks_trainer",
)


def sym(name: str):
    """A name exported by the finetune package, from whichever module holds it.

    The ticket puts the ledger in `step_ledger.py`, but a constant or a helper is
    graded on existing and on what it says, not on which file it was typed into.
    """
    for mod_name in _CANDIDATE_MODULES:
        mod = sys.modules.get(mod_name)
        if mod is None:
            try:
                __import__(mod_name)
            except Exception:
                continue
            mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, name):
            return getattr(mod, name)
    for mod_name, mod in sorted(sys.modules.items()):
        if mod_name.startswith("bespokelabs.curator") and hasattr(mod, name):
            return getattr(mod, name)
    pytest.fail(f"the implementation exports no {name!r} anywhere in bespokelabs.curator.finetune")


def ledger():
    """Fail one test, not the whole module, when the new module is absent."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"bespokelabs.curator.finetune.step_ledger could not be imported: {IMPORT_ERROR!r}")
    return sl


def has_ledger() -> bool:
    return IMPORT_ERROR is None


# ---------------------------------------------------------------------------
# The end-to-end inputs the ticket names
# ---------------------------------------------------------------------------
DATA = [
    {"messages": [{"role": "user", "content": f"Q{i}"}, {"role": "assistant", "content": f"A{i}"}]}
    for i in range(10)
]

SIGNATURE = "ds1-10-5d661fe8c9a2d002"

# The eight per-batch mock losses of `random.Random(0)` under `2.5 - draw * 0.5`.
BATCH_LOSSES = [
    2.077789074237476,
    2.121022798529849,
    2.2897142095845773,
    2.3705416248535185,
    2.2443626393156957,
    2.2975329312747927,
    2.1081007054826135,
    2.348343636960536,
]


def e2e_config(**overrides):
    """The end-to-end configuration: 10 examples, 4 batches an epoch, 3 optimizer steps."""
    kwargs = dict(
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
        api_key=None,
    )
    kwargs.update(overrides)
    return TinkerTrainerConfig(**kwargs)


class FakeClock:
    """A clock that hands back the values it was given and counts the asking."""

    def __init__(self, values):
        self.values = list(values)
        self.calls = 0

    def __call__(self) -> float:
        if self.calls >= len(self.values):
            raise AssertionError(f"the clock was called {self.calls + 1} times; only {len(self.values)} values were provided")
        value = self.values[self.calls]
        self.calls += 1
        return value


def clock_for(*values) -> FakeClock:
    """A clock with slack past the expected calls, so an extra call fails on a number."""
    return FakeClock(list(values) + [9.0e9] * 8)


def record_stats(monkeypatch):
    """Capture every `TrainingStats` the run pushes, wherever the tracker is built.

    Patched in every finetune module that holds the name, with one shared
    recorder between them, so "one per batch" still means one in total whichever
    module the trainer reached for.
    """
    recorder = SimpleNamespace(stats=[], init_kwargs={}, init_args=(), built=0)

    class Tracker:
        def __init__(self, *args, **kwargs):
            recorder.built += 1
            recorder.init_args = args
            recorder.init_kwargs = kwargs

        def update(self, stats=None, *args, **kwargs):
            recorder.stats.append(stats)

        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    patched = 0
    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith("bespokelabs.curator.finetune") and hasattr(mod, "FinetuneStatusTracker"):
            monkeypatch.setattr(mod, "FinetuneStatusTracker", Tracker, raising=False)
            patched += 1
    assert patched, "no finetune module exposes FinetuneStatusTracker to patch"
    return recorder


def tracker_total_steps(recorder):
    """The denominator the tracker was built with, however it was passed."""
    if "total_steps" in recorder.init_kwargs:
        return recorder.init_kwargs["total_steps"]
    if len(recorder.init_args) >= 3:          # model, total_epochs, total_steps, batch_size
        return recorder.init_args[2]
    raise AssertionError(f"the status tracker was built with no total_steps: {recorder.init_args} {recorder.init_kwargs}")


def mock_env(monkeypatch):
    """No provider key anywhere: every trainer runs its mock branch."""
    monkeypatch.delenv("TINKER_API_KEY", raising=False)
    monkeypatch.delenv("FIREWORKS_API_KEY", raising=False)


def test_open_feature__one_step_unit_one_checkpoint_identity_one_resume_contract(monkeypatch):
    mod = ledger()
    mock_env(monkeypatch)

    # ---- P1: the module surface -------------------------------------------
    StepPlan = sym("StepPlan")
    ResumePlan = sym("ResumePlan")
    StepLedgerError = sym("StepLedgerError")
    ResumePlanMismatch = sym("ResumePlanMismatch")
    plan_steps = sym("plan_steps")
    plan_steps_for_config = sym("plan_steps_for_config")
    plan_packed_steps = sym("plan_packed_steps")
    plan_resume = sym("plan_resume")
    dataset_signature = sym("dataset_signature")
    sym("learning_rate_at")  # `checkpoint_name` is r1's: the ticket names no function for it

    assert sym("STEP_UNIT_OPTIMIZER") == "optimizer_step"
    assert sym("STEP_UNIT_PACKED") == "packed_epoch_step"
    assert sym("DATASET_SIGNATURE_PREFIX") == "ds1"

    assert issubclass(StepLedgerError, ValueError)
    assert issubclass(ResumePlanMismatch, StepLedgerError)

    assert dataclasses.is_dataclass(StepPlan) and dataclasses.is_dataclass(ResumePlan)
    assert [f.name for f in dataclasses.fields(StepPlan)] == [
        "step_unit",
        "num_examples",
        "batch_size",
        "epochs",
        "gradient_accumulation_steps",
        "batches_per_epoch",
        "total_batches",
        "total_steps",
        "trailing_window_batches",
        "dataset_signature",
    ]
    assert [f.name for f in dataclasses.fields(ResumePlan)] == [
        "checkpoint_name",
        "start_batch_ordinal",
        "start_epoch",
        "start_batch_in_epoch",
        "completed_steps",
        "remaining_batches",
    ]

    # A leaf module: no clock, no global RNG, and the two modules that import it
    # are only reachable under TYPE_CHECKING.
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    type_checking_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            named = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            if named:
                for child in node.body:
                    for inner in ast.walk(child):
                        type_checking_nodes.add(id(inner))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            root = name.split(".")[0]
            assert root not in {"time", "datetime", "random"}, f"step_ledger imports {name!r}"
            if "finetune.types" in name or "finetune.config" in name:
                assert id(node) in type_checking_nodes, f"the runtime import of {name!r} makes step_ledger a cycle"

    # ---- P2: the unit -----------------------------------------------------
    plan = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3)
    assert isinstance(plan, StepPlan)
    assert (plan.batches_per_epoch, plan.total_batches, plan.total_steps, plan.trailing_window_batches) == (4, 8, 3, 2)
    assert plan.step_unit == "optimizer_step"
    assert [plan.step_of_batch(b) for b in range(1, 9)] == [1, 1, 1, 2, 2, 2, 3, 3]
    assert [plan.is_step_boundary(b) for b in range(1, 9)] == [False, False, True, False, False, True, False, True]
    assert [plan.epoch_of_batch(b) for b in range(1, 9)] == [1, 1, 1, 1, 2, 2, 2, 2]
    assert [tuple(plan.batch_slice(b)) for b in range(1, 9)] == [
        (0, 3),
        (3, 6),
        (6, 9),
        (9, 10),
        (0, 3),
        (3, 6),
        (6, 9),
        (9, 10),
    ]
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.total_steps = 99

    wide = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=4)
    assert (wide.total_steps, wide.trailing_window_batches) == (2, 4)
    even = plan_steps(12, batch_size=4, epochs=1)
    assert (even.total_steps, even.trailing_window_batches) == (3, 1)

    with pytest.raises(StepLedgerError):
        plan_steps(0, batch_size=3, epochs=2)
    with pytest.raises(StepLedgerError):
        plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=0)
    with pytest.raises(StepLedgerError):
        plan_steps(10, batch_size=0, epochs=2)
    with pytest.raises(StepLedgerError):
        plan_steps(10, batch_size=3, epochs=0)

    # The marks `loss_history` is drawn from, in the ledger's own words.
    assert tuple(plan.logging_steps(2)) == (2,)
    assert tuple(plan.loss_history_steps(2)) == (2, 3)
    assert tuple(plan.loss_history_steps(1)) == (1, 2, 3)
    assert tuple(plan_steps(10, batch_size=3, epochs=2).loss_history_steps(10)) == (4, 8)

    # ---- P5: the dataset signature ----------------------------------------
    assert dataset_signature(DATA) == SIGNATURE
    assert len(dataset_signature(DATA)) == 23
    assert dataset_signature(DATA[:3]) == "ds1-3-b8c83761d026bfe8"
    assert dataset_signature(list(reversed(DATA))) != dataset_signature(DATA)
    assert dataset_signature([{"messages": [{"content": "Q0", "role": "user"}, {"role": "assistant", "content": "A0"}]}]) == dataset_signature(
        [{"messages": [{"role": "user", "content": "Q0"}, {"content": "A0", "role": "assistant"}]}]
    )

    # ---- P11: the packed unit ---------------------------------------------
    packed = plan_packed_steps(2, epochs=5)
    assert (
        packed.step_unit,
        packed.batch_size,
        packed.gradient_accumulation_steps,
        packed.batches_per_epoch,
        packed.total_batches,
        packed.total_steps,
        packed.trailing_window_batches,
    ) == ("packed_epoch_step", 2, 1, 1, 5, 5, 1)
    with pytest.raises(StepLedgerError):
        plan_packed_steps(0, epochs=5)

    # ---- types.py: appended, defaulted fields ------------------------------
    checkpoint_fields = [f.name for f in dataclasses.fields(CheckpointInfo)]
    assert checkpoint_fields[:9] == [
        "name",
        "path",
        "step",
        "epoch",
        "loss",
        "batch_size",
        "gradient_accumulation_steps",
        "batches_completed",
        "dataset_signature",
    ]
    bare = CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5)
    assert (bare.batch_size, bare.gradient_accumulation_steps, bare.batches_completed, bare.dataset_signature) == (0, 0, 0, "")

    # Present, defaulted, in that relative order -- NOT at a particular index.
    # The ticket says "appended in this order" for CheckpointInfo above and only
    # "gains" for these two, and nothing in the record settles where they sit. A
    # solution that grouped them beside current_step/total_steps -- where they
    # read best -- scored 1.0 on every hidden fact of g11 and lost the whole open
    # feature on a field's position.
    stats_fields = [f.name for f in dataclasses.fields(TrainingStats)]
    assert {"current_batch", "total_batches"}.issubset(stats_fields)
    assert stats_fields.index("current_batch") < stats_fields.index("total_batches")
    # and nothing that was already there was dropped, renamed or reordered
    assert [f for f in stats_fields if f not in ("current_batch", "total_batches")] == [
        "current_epoch",
        "total_epochs",
        "current_step",
        "total_steps",
        "current_loss",
        "tokens_processed",
        "samples_processed",
        "learning_rate",
        "elapsed_time",
    ]
    assert (TrainingStats().current_batch, TrainingStats().total_batches) == (0, 0)

    # Same wording, same treatment. One rollout inserted these mid-dataclass and
    # only moved them to the end afterwards "to be safe" -- the tail was a coin
    # flip, not a requirement.
    result_fields = [f.name for f in dataclasses.fields(TrainingResult)]
    assert {"total_batches", "step_plan"}.issubset(result_fields)
    assert result_fields.index("total_batches") < result_fields.index("step_plan")
    assert [f for f in result_fields if f not in ("total_batches", "step_plan")] == [
        "final_loss",
        "total_steps",
        "total_epochs",
        "total_time",
        "tokens_processed",
        "samples_processed",
        "loss_history",
        "weights_name",
        "checkpoints",
        "metadata",
    ]
    minimal = TrainingResult(
        final_loss=0.0,
        total_steps=0,
        total_epochs=0,
        total_time=0.0,
        tokens_processed=0,
        samples_processed=0,
    )
    assert minimal.total_batches == 0 and minimal.step_plan is None

    # ---- config.py: seed ---------------------------------------------------
    assert TinkerTrainerConfig(base_model="m").seed == 0
    assert FireworksTrainerConfig(base_model="m").seed == 0
    with pytest.raises(Exception):
        TinkerTrainerConfig(base_model="m", seed=-1)

    # ---- P3 / P9 / P10: the rebuilt loop -----------------------------------
    config = e2e_config()
    assert plan_steps_for_config(config, DATA) == plan_steps(
        10, batch_size=3, epochs=2, gradient_accumulation_steps=3, dataset_signature=SIGNATURE
    )

    recorder = record_stats(monkeypatch)
    clock = clock_for(1000.0, 1004.5)
    rng = random.Random(0)
    trainer = TinkerTrainer(config, clock=clock, rng=rng)

    steps_seen = []
    inner = trainer._training_step

    def watched(*args, **kwargs):
        if "should_optim_step" in kwargs:
            steps_seen.append(kwargs["should_optim_step"])
        elif len(args) >= 3:
            steps_seen.append(args[2])
        else:
            steps_seen.append(True)
        return inner(*args, **kwargs)

    monkeypatch.setattr(trainer, "_training_step", watched)
    result = trainer.train(DATA)

    # The trailing window is stepped inside the loop, in mock mode.
    assert steps_seen == [False, False, True, False, False, True, False, True]

    assert result.total_steps == 3
    assert result.total_batches == 8
    assert result.total_epochs == 2
    assert result.samples_processed == 20
    assert result.tokens_processed == 120
    assert result.total_time == 4.5
    assert clock.calls == 2
    assert result.weights_name is None
    assert result.step_plan == plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3, dataset_signature=SIGNATURE)
    assert result.metadata["dataset_signature"] == SIGNATURE
    for key, value in {
        "base_model": "Qwen3-8B",
        "batch_size": 3,
        "learning_rate": 0.0001,
        "lora_rank": 16,
        "lora_alpha": 32,
        "gradient_accumulation_steps": 3,
    }.items():
        assert result.metadata[key] == value

    # One stats record per batch, pushed after that batch's optional step.
    assert len(recorder.stats) == 8
    assert [(read_field(s, "current_batch"), read_field(s, "current_step")) for s in recorder.stats] == [
        (1, 0),
        (2, 0),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 2),
        (7, 2),
        (8, 3),
    ]
    assert [read_field(s, "current_epoch") for s in recorder.stats] == [1, 1, 1, 1, 2, 2, 2, 2]
    assert {read_field(s, "total_steps") for s in recorder.stats} == {3}
    assert {read_field(s, "total_batches") for s in recorder.stats} == {8}
    assert tracker_total_steps(recorder) == 3
    assert [read_field(s, "current_loss") for s in recorder.stats] == pytest.approx(BATCH_LOSSES, rel=1e-12)

    # One entry per marked step, each the mean of that step's window.
    assert result.loss_history == pytest.approx([2.304145731814669, 2.228222171221575], rel=1e-12)
    assert result.final_loss == pytest.approx(2.228222171221575, rel=1e-12)

    # Exactly eight draws were made, one per batch, in batch order.
    assert rng.random() == pytest.approx(0.4765969541523558)

    # Seeded from config.seed, so two default trainers agree byte for byte.
    again = TinkerTrainer(e2e_config(), clock=clock_for(0.0, 1.0))
    twice = TinkerTrainer(e2e_config(), clock=clock_for(0.0, 1.0))
    assert again.train(DATA).loss_history == twice.train(DATA).loss_history == result.loss_history

    # No `time.sleep` and no global `random.random` survives on the mock path.
    from bespokelabs.curator.finetune.trainer import tinker_trainer as tinker_module

    trainer_tree = ast.parse(inspect.getsource(tinker_module))
    for node in ast.walk(trainer_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        value = node.func.value
        if isinstance(value, ast.Name) and value.id == "time":
            assert node.func.attr != "sleep", "time.sleep survives in tinker_trainer"
        if node.func.attr == "random" and isinstance(value, ast.Name) and value.id == "random":
            pytest.fail("the module-global random.random() survives in tinker_trainer")

    # The auto-named weights come off the injected clock too.
    third = clock_for(1000.0, 1004.5, 1700000000.0)
    saved = TinkerTrainer(e2e_config(save_weights_on_complete=True), clock=third).train(DATA)
    assert third.calls == 3
    assert saved.weights_name == "mock_weights_Qwen3-8B_lora_1700000000"

    # ---- P8: the resume contract ------------------------------------------
    signed = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3, dataset_signature=SIGNATURE)
    ck = CheckpointInfo(
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
    resume = plan_resume(signed, ck)
    assert isinstance(resume, ResumePlan)
    assert (
        resume.checkpoint_name,
        resume.start_batch_ordinal,
        resume.start_epoch,
        resume.start_batch_in_epoch,
        resume.completed_steps,
        resume.remaining_batches,
    ) == ("checkpoint-s000002", 6, 2, 2, 2, 2)

    reshaped = plan_steps(10, batch_size=5, epochs=2, gradient_accumulation_steps=3, dataset_signature="ds1-10-other")
    with pytest.raises(ResumePlanMismatch) as caught:
        plan_resume(reshaped, ck)
    assert tuple(caught.value.mismatched_fields) == ("batch_size", "dataset_signature")
    assert isinstance(caught.value, StepLedgerError)
    assert caught.value.checkpoint_name == "checkpoint-s000002"

    pre_ledger = CheckpointInfo(name="old", path="p", step=4, epoch=2, loss=1.0)
    with pytest.raises(ResumePlanMismatch) as caught:
        plan_resume(signed, pre_ledger)
    assert tuple(caught.value.mismatched_fields) == ("batch_size", "dataset_signature", "gradient_accumulation_steps")

    exhausted = dataclasses.replace(ck, step=3, batches_completed=8)
    with pytest.raises(ResumePlanMismatch) as caught:
        plan_resume(signed, exhausted)
    assert tuple(caught.value.mismatched_fields) == ("epochs",)

    grown = plan_steps(10, batch_size=3, epochs=3, gradient_accumulation_steps=3, dataset_signature=SIGNATURE)
    longer = plan_resume(grown, exhausted)
    assert (longer.remaining_batches, longer.start_epoch) == (4, 3)

    inconsistent = dataclasses.replace(ck, step=1)
    with pytest.raises(ResumePlanMismatch) as caught:
        plan_resume(signed, inconsistent)
    assert tuple(caught.value.mismatched_fields) == ("step",)

    # End to end: the run picks up at the batch after the checkpoint.
    resumed_trainer = TinkerTrainer(e2e_config(), clock=clock_for(2000.0, 2001.0))
    assert resumed_trainer.load_checkpoint(ck) is True
    resumed = resumed_trainer.train(DATA)
    assert resumed.total_steps == 3
    assert resumed.total_batches == 8
    assert resumed.samples_processed == 4
    assert resumed.tokens_processed == 24
    assert resumed.loss_history == pytest.approx([2.099405936383662], rel=1e-12)

    # `train()` clears the resume point, so a second call starts from zero.
    second = resumed_trainer.train(DATA)
    assert second.samples_processed == 20

    refusing = TinkerTrainer(e2e_config())
    refusing.load_checkpoint(ck)
    with pytest.raises(ResumePlanMismatch) as caught:
        refusing.train(DATA[:6])
    assert tuple(caught.value.mismatched_fields) == ("dataset_signature",)
    assert caught.value.checkpoint_name == "checkpoint-s000002"

    finished = TinkerTrainer(e2e_config())
    finished.load_checkpoint(dataclasses.replace(ck, name="checkpoint-s000003", step=3, batches_completed=8))
    with pytest.raises(ResumePlanMismatch) as caught:
        finished.train(DATA)
    assert tuple(caught.value.mismatched_fields) == ("epochs",)

    # ---- P11 end to end: Fireworks reports the packed unit -----------------
    fw = FireworksTrainer(FireworksTrainerConfig(base_model="qwen3-4b", epochs=4, seed=0, api_key=None))
    fw_result = fw.train(DATA[:3])
    assert fw_result.total_steps == 4
    assert fw_result.total_batches == 4
    assert read_field(fw_result.step_plan, "step_unit") == "packed_epoch_step"
    assert fw_result.metadata["step_unit"] == "packed_epoch_step"
    assert sorted(fw_result.metadata) == ["base_model", "mock", "provider", "step_unit"]
    assert fw_result.final_loss == pytest.approx(2.077789074237476)
