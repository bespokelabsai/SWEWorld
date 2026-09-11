"""g11 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission,
turns those values into the verdict. This is the split that closes the forgery
recorded in `tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent
code from rewriting a report its own process produces, so the process that
imports the code no longer produces the report.

The curator-facing halves are lifted verbatim from `test_open`/`test_r1`/
`test_r2` — same fixtures (`e2e_config`, `clock_for`, `record_stats`, `sym`,
`ledger`), same `read_field` extraction — so a value here is the value the test
saw. The judge holds the assertions those tests made. Nothing here decides
anything; a hostile submission that returns forged values only forges values the
judge still checks against the real expectations, which is implementing them.

Floats are written through `json`, whose float encoding is `repr`, so every
value round-trips to the identical double and the judge's `approx(rel=1e-12)`
means what it meant in-process.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# Same import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest. No provider socket and no /etc/hosts
# mapping: every g11 test runs curator's mock branch (`mock_env` deletes the
# keys), so unlike the other suites g11 never touches FakeProvider.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

_MISSING = object()


class MonkeyPatch:
    """The slice of pytest's monkeypatch the g11 fixtures use, with undo.

    `record_stats` and `mock_env` want `setattr(..., raising=False)`, `setenv`
    and `delenv`; nothing here needs the rest. `undo()` runs between probes so
    one test's patched `FinetuneStatusTracker` cannot leak into the next.
    """

    def __init__(self) -> None:
        self._undo: list = []

    def setattr(self, target, name, value, raising=True):
        if not hasattr(target, name) and raising:
            raise AttributeError(name)
        old = getattr(target, name, _MISSING)
        setattr(target, name, value)
        self._undo.append(("attr", target, name, old))

    def setenv(self, name, value):
        old = os.environ.get(name, _MISSING)
        os.environ[name] = value
        self._undo.append(("env", name, old))

    def delenv(self, name, raising=False):
        old = os.environ.pop(name, _MISSING)
        self._undo.append(("env", name, old))

    def undo(self):
        for entry in reversed(self._undo):
            kind = entry[0]
            if kind == "attr":
                _, target, name, old = entry
                if old is _MISSING:
                    try:
                        delattr(target, name)
                    except AttributeError:
                        pass
                else:
                    setattr(target, name, old)
            else:
                _, name, old = entry
                if old is _MISSING:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = old
        self._undo = []


# test_open owns the fixtures and the curator imports; reuse them so a probe
# calls curator exactly as the test does. Importing it here runs the
# submission's `import bespokelabs.curator` — which is the whole point of this
# process existing and being disposable.
# probe_support holds the answer-free helpers (the worker never imports test_open,
# whose source carries the expected answer literals, nor SIGNATURE/BATCH_LOSSES).
import probe_support as T  # noqa: E402
from harness import read_field  # noqa: E402

BASE = 1e-4


def reasons_of(result):
    return [list(read_field(c, "reasons")) for c in result.checkpoints]


def shapes(result):
    return [[c.step, c.epoch, read_field(c, "batches_completed")] for c in result.checkpoints]


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised and the exception's class chain.

    The judge cannot import `StepLedgerError`, so it checks the raised type by
    the names in its MRO — the faithful stand-in for `pytest.raises(T)` and
    `issubclass`, which is all the tests do with these exceptions.
    """
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a specific type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__]}
        for attr in ("mismatched_fields", "checkpoint_name"):
            if hasattr(exc, attr):
                val = getattr(exc, attr)
                info[attr] = list(val) if isinstance(val, (list, tuple)) else val
        return info
    return {"raised": False, "mro": []}


# ---------------------------------------------------------------------------
# r2 — the learning-rate schedule
# ---------------------------------------------------------------------------
def probe_r2_rule(mp) -> dict:
    T.mock_env(mp)
    lr = T.sym("learning_rate_at")
    param = __import__("inspect").signature(lr).parameters["min_lr_ratio"]
    return {
        "MIN_LR_RATIO": T.sym("MIN_LR_RATIO"),
        "param_kind": param.kind.name,
        "param_default": param.default,
        "ramp": [lr(s, 10, BASE, 4) for s in range(1, 5)],
        "lr_5": lr(5, 10, BASE, 4),
        "lr_7": lr(7, 10, BASE, 4),
        "lr_10": lr(10, 10, BASE, 4),
        "lr_4": lr(4, 10, BASE, 4),
        "after": [lr(s, 10, BASE, 4) for s in range(4, 11)],
        "lr_10_half": lr(10, 10, BASE, 4, min_lr_ratio=0.5),
        "lr_7_half": lr(7, 10, BASE, 4, min_lr_ratio=0.5),
        "lr_10_zero": lr(10, 10, BASE, 4, min_lr_ratio=0.0),
        "lr_5_10_0": lr(5, 10, BASE, 0),
        "lr_5_100_0": lr(5, 100, BASE, 0),
    }


def probe_r2_exclusions(mp) -> dict:
    T.mock_env(mp)
    sig = T.signature()  # live, from the submission — never the SIGNATURE literal
    lr = T.sym("learning_rate_at")
    floor = lr(8, 8, BASE, 2)
    recorder = T.record_stats(mp)
    checkpoint = T.CheckpointInfo(
        name="checkpoint-s000002", path="mock://checkpoints/checkpoint-s000002",
        step=2, epoch=2, loss=2.3, batch_size=3, gradient_accumulation_steps=3,
        batches_completed=6, dataset_signature=sig)
    trainer = T.TinkerTrainer(T.e2e_config(epochs=3), clock=T.clock_for(2000.0, 2001.0))
    load_ok = trainer.load_checkpoint(checkpoint)
    resumed = trainer.train(T.DATA)
    return {
        "floor": floor,
        "lr_9": lr(9, 8, BASE, 2), "lr_99": lr(99, 8, BASE, 2),
        "lr_10000": lr(10_000, 8, BASE, 2),
        "min_1_200": min(lr(s, 8, BASE, 2) for s in range(1, 200)),
        "load_ok": load_ok is True,
        "total_steps": resumed.total_steps,
        "current_batch": [read_field(s, "current_batch") for s in recorder.stats],
        "current_step": [read_field(s, "current_step") for s in recorder.stats],
        "learning_rate": [read_field(s, "learning_rate") for s in recorder.stats],
        "lr_3_4_2": lr(3, 4, BASE, 2), "lr_4_4_2": lr(4, 4, BASE, 2),
    }


def probe_r2_failure_behavior(mp) -> dict:
    T.mock_env(mp)
    lr = T.sym("learning_rate_at")
    clipped = [lr(s, 3, BASE, 10) for s in range(1, 4)]
    return {
        "clipped": clipped,
        "ramp_4": [lr(s, 4, BASE, 4) for s in range(1, 5)],
        "min_clipped": min(clipped),
        "lr_1_1_99": lr(1, 1, BASE, 99),
    }


def probe_r2_observability(mp) -> dict:
    T.mock_env(mp)
    lr = T.sym("learning_rate_at")
    recorder = T.record_stats(mp)
    result = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(1000.0, 1004.5)).train(T.DATA)
    return {
        "vec8": [lr(s, 8, BASE, 2) for s in range(1, 9)],
        "vec4": [lr(s, 4, BASE, 0) for s in range(1, 5)],
        "total_steps": result.total_steps,
        "learning_rate": [read_field(s, "learning_rate") for s in recorder.stats],
    }


# ---------------------------------------------------------------------------
# r1 — the checkpoint ledger
# ---------------------------------------------------------------------------
def _run(config, data=None):
    return T.TinkerTrainer(config, clock=T.clock_for(1000.0, 1004.5)).train(
        T.DATA if data is None else data)


def probe_r1_rule(mp) -> dict:
    import dataclasses
    import inspect
    T.mock_env(mp)
    canonical_reasons = T.sym("canonical_reasons")
    checkpoint_name = T.sym("checkpoint_name")
    param = inspect.signature(T.TinkerTrainer.save_checkpoint).parameters["reasons"]

    trainer = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(1000.0, 1004.5))
    defaulted = trainer.save_checkpoint("solo", step=1, epoch=1, loss=0.5)

    trainer2 = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(1000.0, 1004.5))
    calls = []
    inner = trainer2.save_checkpoint

    def watched(*args, **kwargs):
        record = inner(*args, **kwargs)
        calls.append(kwargs.get("name", args[0] if args else None))
        return record

    mp.setattr(trainer2, "save_checkpoint", watched)
    result = trainer2.train(T.DATA)
    by_name = {c.name: list(read_field(c, "reasons")) for c in result.checkpoints}
    return {
        "CHECKPOINT_REASONS": list(T.sym("CHECKPOINT_REASONS")),
        "name_template_2": T.sym("CHECKPOINT_NAME_TEMPLATE").format(prefix="checkpoint", step=2),
        "canonical": {
            "feiee": list(canonical_reasons(("final", "epoch", "interval", "epoch"))),
            "fi": list(canonical_reasons(("final", "interval"))),
            "ei": list(canonical_reasons(("epoch", "interval"))),
            "fe": list(canonical_reasons(("final", "epoch"))),
            "empty": list(canonical_reasons(())),
            "ee": list(canonical_reasons(("epoch", "epoch"))),
        },
        "name_2": checkpoint_name("checkpoint", 2),
        "name_big": checkpoint_name("ckpt", 1234567),
        "name_sorted": sorted(checkpoint_name("checkpoint", s) for s in (2, 10, 100)),
        "fields_last": [f.name for f in dataclasses.fields(T.CheckpointInfo)][-1],
        "param_kind": param.kind.name,
        "param_default": list(param.default),
        "defaulted_reasons": list(read_field(defaulted, "reasons")),
        "calls": calls,
        "n_checkpoints": len(result.checkpoints),
        "by_name": by_name,
    }


def probe_r1_scope(mp) -> dict:
    T.mock_env(mp)
    bare = _run(T.e2e_config(checkpoint_every_n_steps=0, checkpoint_every_epoch=False))
    interval_only = _run(T.e2e_config(checkpoint_every_n_steps=2, checkpoint_every_epoch=False))
    epoch_only = _run(T.e2e_config(checkpoint_every_n_steps=0, checkpoint_every_epoch=True))
    single = _run(T.e2e_config(epochs=1, gradient_accumulation_steps=4,
                               checkpoint_every_n_steps=0, checkpoint_every_epoch=False))
    out = {
        "bare_total": bare.total_steps, "bare_steps": [c.step for c in bare.checkpoints],
        "bare_reasons": reasons_of(bare),
        "interval_steps": [c.step for c in interval_only.checkpoints],
        "interval_reasons": reasons_of(interval_only),
        "epoch_steps": [c.step for c in epoch_only.checkpoints],
        "epoch_reasons": reasons_of(epoch_only),
        "single_total": single.total_steps, "single_steps": [c.step for c in single.checkpoints],
        "single_reasons": reasons_of(single),
        "has_ledger": T.has_ledger(),
    }
    if T.has_ledger():
        fw = T.FireworksTrainer(T.FireworksTrainerConfig(base_model="qwen3-4b", epochs=4, seed=0, api_key=None))
        fw_result = fw.train(T.DATA[:3])
        out["fw_checkpoints"] = len(fw_result.checkpoints)
        out["fw_reasons_in_meta"] = "reasons" in fw_result.metadata
    return out


def probe_r1_exclusions(mp) -> dict:
    T.mock_env(mp)
    result = _run(T.e2e_config(epochs=3, checkpoint_every_n_steps=0, checkpoint_every_epoch=True))
    plan = result.step_plan
    return {
        "steps": [c.step for c in result.checkpoints],
        "epoch_in_reasons": [("epoch" in read_field(c, "reasons")) for c in result.checkpoints],
        "shapes": shapes(result),
        "epochs": [c.epoch for c in result.checkpoints],
        "epoch_of_batch": [plan.epoch_of_batch(b) for b in (6, 9, 12)],
    }


def probe_r1_failure_behavior(mp) -> dict:
    T.mock_env(mp)
    canonical_reasons = T.sym("canonical_reasons")
    trainer = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(1000.0, 1004.5))
    trainer.save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))
    merged = trainer.save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.25, reasons=("final",))
    stored = trainer.get_checkpoints()
    trainer.save_checkpoint("checkpoint-s000003", step=3, epoch=2, loss=0.125, reasons=("final",))
    return {
        "raise_periodic": raises(canonical_reasons, ("periodic",)),
        "raise_manual": raises(canonical_reasons, ("interval", "manual")),
        "raise_caps": raises(canonical_reasons, ("Interval",)),
        "stored_len": len(stored),
        "stored_reasons_sorted": sorted(read_field(stored[0], "reasons")),
        "stored_loss": stored[0].loss,
        "merged_reasons_sorted": sorted(read_field(merged, "reasons")),
        "merged_loss": merged.loss,
        "names": [c.name for c in trainer.get_checkpoints()],
    }


def probe_r1_observability(mp) -> dict:
    import dataclasses
    T.mock_env(mp)
    fields = [f.name for f in dataclasses.fields(T.CheckpointInfo)]
    bare = T.CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5)
    result = _run(T.e2e_config())
    fixture_config = T.TinkerTrainerConfig(base_model="Qwen3-8B", epochs=1, batch_size=2)
    fixture_data = [
        {"messages": [{"role": "user", "content": "What is Python?"}, {"role": "assistant", "content": "Python is a programming language."}]},
        {"messages": [{"role": "user", "content": "What is Java?"}, {"role": "assistant", "content": "Java is also a programming language."}]},
    ]
    fixture_result = T.TinkerTrainer(fixture_config).train(fixture_data)
    return {
        "n_fields": len(fields), "last_two": fields[-2:],
        "bare_reasons": list(bare.reasons),
        "names": [c.name for c in result.checkpoints],
        "reasons": reasons_of(result),
        "shapes": shapes(result),
        "paths": [c.path for c in result.checkpoints],
        "batch_size": [c.batch_size for c in result.checkpoints],
        "gas": [read_field(c, "gradient_accumulation_steps") for c in result.checkpoints],
        "dataset_sig": sorted({read_field(c, "dataset_signature") for c in result.checkpoints}),
        "loss": [c.loss for c in result.checkpoints],
        "fx_total": fixture_result.total_steps,
        "fx_n": len(fixture_result.checkpoints),
        "fx_name": fixture_result.checkpoints[0].name if fixture_result.checkpoints else None,
        "fx_reasons": list(read_field(fixture_result.checkpoints[0], "reasons")) if fixture_result.checkpoints else None,
        "fx_loss_hist_len": len(fixture_result.loss_history),
        "fx_final_loss": fixture_result.final_loss,
    }


STEP_PLAN_FIELDS = ("step_unit", "num_examples", "batch_size", "epochs",
                    "gradient_accumulation_steps", "batches_per_epoch", "total_batches",
                    "total_steps", "trailing_window_batches", "dataset_signature")
RESUME_PLAN_FIELDS = ("checkpoint_name", "start_batch_ordinal", "start_epoch",
                      "start_batch_in_epoch", "completed_steps", "remaining_batches")


def _plan_fields(p) -> dict:
    return {f: getattr(p, f) for f in STEP_PLAN_FIELDS}


def _resume_fields(p) -> dict:
    return {f: getattr(p, f) for f in RESUME_PLAN_FIELDS}


# ---------------------------------------------------------------------------
# open feature — the whole stated surface (one fact)
# ---------------------------------------------------------------------------
def probe_open(mp) -> dict:
    import dataclasses
    import inspect
    import random
    T.ledger()  # fail fast exactly as the test does when step_ledger is absent
    T.mock_env(mp)
    sig = T.signature()  # live, from the submission — never the SIGNATURE literal

    StepPlan = T.sym("StepPlan")
    ResumePlan = T.sym("ResumePlan")
    StepLedgerError = T.sym("StepLedgerError")
    ResumePlanMismatch = T.sym("ResumePlanMismatch")
    plan_steps = T.sym("plan_steps")
    plan_steps_for_config = T.sym("plan_steps_for_config")
    plan_packed_steps = T.sym("plan_packed_steps")
    plan_resume = T.sym("plan_resume")
    dataset_signature = T.sym("dataset_signature")
    T.sym("learning_rate_at")

    o: dict = {}
    o["STEP_UNIT_OPTIMIZER"] = T.sym("STEP_UNIT_OPTIMIZER")
    o["STEP_UNIT_PACKED"] = T.sym("STEP_UNIT_PACKED")
    o["DATASET_SIGNATURE_PREFIX"] = T.sym("DATASET_SIGNATURE_PREFIX")
    o["sle_mro"] = [c.__name__ for c in StepLedgerError.__mro__]
    o["rpm_mro"] = [c.__name__ for c in ResumePlanMismatch.__mro__]
    o["is_dc"] = bool(dataclasses.is_dataclass(StepPlan) and dataclasses.is_dataclass(ResumePlan))
    o["stepplan_fields"] = [f.name for f in dataclasses.fields(StepPlan)]
    o["resumeplan_fields"] = [f.name for f in dataclasses.fields(ResumePlan)]

    # P2 unit
    plan = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3)
    o["plan_isinstance"] = isinstance(plan, StepPlan)
    o["plan_tuple"] = [plan.batches_per_epoch, plan.total_batches, plan.total_steps, plan.trailing_window_batches]
    o["plan_step_unit"] = plan.step_unit
    o["step_of_batch"] = [plan.step_of_batch(b) for b in range(1, 9)]
    o["is_step_boundary"] = [bool(plan.is_step_boundary(b)) for b in range(1, 9)]
    o["epoch_of_batch"] = [plan.epoch_of_batch(b) for b in range(1, 9)]
    o["batch_slice"] = [list(plan.batch_slice(b)) for b in range(1, 9)]
    try:
        plan.total_steps = 99
        o["frozen"] = False
    except dataclasses.FrozenInstanceError:
        o["frozen"] = True
    wide = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=4)
    o["wide"] = [wide.total_steps, wide.trailing_window_batches]
    even = plan_steps(12, batch_size=4, epochs=1)
    o["even"] = [even.total_steps, even.trailing_window_batches]
    o["raise_zero_examples"] = raises(plan_steps, 0, batch_size=3, epochs=2)
    o["raise_zero_gas"] = raises(plan_steps, 10, batch_size=3, epochs=2, gradient_accumulation_steps=0)
    o["raise_zero_batch"] = raises(plan_steps, 10, batch_size=0, epochs=2)
    o["raise_zero_epochs"] = raises(plan_steps, 10, batch_size=3, epochs=0)
    o["logging_2"] = list(plan.logging_steps(2))
    o["loss_hist_2"] = list(plan.loss_history_steps(2))
    o["loss_hist_1"] = list(plan.loss_history_steps(1))
    o["loss_hist_10"] = list(plan_steps(10, batch_size=3, epochs=2).loss_history_steps(10))

    # P5 signature
    o["sig_data"] = dataset_signature(T.DATA)
    o["sig_len"] = len(dataset_signature(T.DATA))
    o["sig_3"] = dataset_signature(T.DATA[:3])
    o["sig_rev_ne"] = dataset_signature(list(reversed(T.DATA))) != dataset_signature(T.DATA)
    o["sig_order_a"] = dataset_signature([{"messages": [{"content": "Q0", "role": "user"}, {"role": "assistant", "content": "A0"}]}])
    o["sig_order_b"] = dataset_signature([{"messages": [{"role": "user", "content": "Q0"}, {"content": "A0", "role": "assistant"}]}])

    # P11 packed
    packed = plan_packed_steps(2, epochs=5)
    o["packed"] = [packed.step_unit, packed.batch_size, packed.gradient_accumulation_steps,
                   packed.batches_per_epoch, packed.total_batches, packed.total_steps,
                   packed.trailing_window_batches]
    o["raise_packed_zero"] = raises(plan_packed_steps, 0, epochs=5)

    # types.py
    o["checkpoint_fields"] = [f.name for f in dataclasses.fields(T.CheckpointInfo)]
    barec = T.CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5)
    o["bare_checkpoint"] = [barec.batch_size, barec.gradient_accumulation_steps,
                            barec.batches_completed, barec.dataset_signature]
    o["stats_fields"] = [f.name for f in dataclasses.fields(T.TrainingStats)]
    o["stats_defaults"] = [T.TrainingStats().current_batch, T.TrainingStats().total_batches]
    o["result_fields"] = [f.name for f in dataclasses.fields(T.TrainingResult)]
    minimal = T.TrainingResult(final_loss=0.0, total_steps=0, total_epochs=0,
                               total_time=0.0, tokens_processed=0, samples_processed=0)
    o["minimal_result"] = [minimal.total_batches, minimal.step_plan is None]

    # config seed
    o["tinker_seed"] = T.TinkerTrainerConfig(base_model="m").seed
    o["fw_seed"] = T.FireworksTrainerConfig(base_model="m").seed
    o["raise_seed_neg"] = raises(T.TinkerTrainerConfig, base_model="m", seed=-1)

    # P3/P9/P10 loop
    config = T.e2e_config()
    o["plan_for_config"] = _plan_fields(plan_steps_for_config(config, T.DATA))
    o["plan_ref"] = _plan_fields(plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3, dataset_signature=sig))

    recorder = T.record_stats(mp)
    clock = T.clock_for(1000.0, 1004.5)
    rng = random.Random(0)
    trainer = T.TinkerTrainer(config, clock=clock, rng=rng)
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

    mp.setattr(trainer, "_training_step", watched)
    result = trainer.train(T.DATA)
    o["steps_seen"] = [bool(s) for s in steps_seen]
    o["result_scalars"] = [result.total_steps, result.total_batches, result.total_epochs,
                           result.samples_processed, result.tokens_processed, result.total_time,
                           clock.calls, result.weights_name is None]
    o["result_step_plan"] = _plan_fields(result.step_plan)
    o["md_dataset_signature"] = result.metadata["dataset_signature"]
    o["md"] = {k: result.metadata[k] for k in
               ("base_model", "batch_size", "learning_rate", "lora_rank", "lora_alpha",
                "gradient_accumulation_steps")}
    o["n_stats"] = len(recorder.stats)
    o["stat_batch_step"] = [[read_field(s, "current_batch"), read_field(s, "current_step")] for s in recorder.stats]
    o["stat_epoch"] = [read_field(s, "current_epoch") for s in recorder.stats]
    o["stat_total_steps"] = sorted({read_field(s, "total_steps") for s in recorder.stats})
    o["stat_total_batches"] = sorted({read_field(s, "total_batches") for s in recorder.stats})
    o["tracker_total_steps"] = T.tracker_total_steps(recorder)
    o["stat_loss"] = [read_field(s, "current_loss") for s in recorder.stats]
    o["loss_history"] = list(result.loss_history)
    o["final_loss"] = result.final_loss
    o["rng_next"] = rng.random()

    again = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(0.0, 1.0))
    twice = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(0.0, 1.0))
    o["again_loss"] = list(again.train(T.DATA).loss_history)
    o["twice_loss"] = list(twice.train(T.DATA).loss_history)

    third = T.clock_for(1000.0, 1004.5, 1700000000.0)
    saved = T.TinkerTrainer(T.e2e_config(save_weights_on_complete=True), clock=third).train(T.DATA)
    o["saved"] = [third.calls, saved.weights_name]

    # P8 resume
    signed = plan_steps(10, batch_size=3, epochs=2, gradient_accumulation_steps=3, dataset_signature=sig)
    ck = T.CheckpointInfo(name="checkpoint-s000002", path="mock://checkpoints/checkpoint-s000002",
                          step=2, epoch=2, loss=2.3, batch_size=3, gradient_accumulation_steps=3,
                          batches_completed=6, dataset_signature=sig)
    resume = plan_resume(signed, ck)
    o["resume_isinstance"] = isinstance(resume, ResumePlan)
    o["resume_fields"] = _resume_fields(resume)
    reshaped = plan_steps(10, batch_size=5, epochs=2, gradient_accumulation_steps=3, dataset_signature="ds1-10-other")
    o["mm_reshaped"] = raises(plan_resume, reshaped, ck)
    pre_ledger = T.CheckpointInfo(name="old", path="p", step=4, epoch=2, loss=1.0)
    o["mm_pre_ledger"] = raises(plan_resume, signed, pre_ledger)
    exhausted = dataclasses.replace(ck, step=3, batches_completed=8)
    o["mm_exhausted"] = raises(plan_resume, signed, exhausted)
    grown = plan_steps(10, batch_size=3, epochs=3, gradient_accumulation_steps=3, dataset_signature=sig)
    longer = plan_resume(grown, exhausted)
    o["longer"] = [longer.remaining_batches, longer.start_epoch]
    inconsistent = dataclasses.replace(ck, step=1)
    o["mm_inconsistent"] = raises(plan_resume, signed, inconsistent)

    resumed_trainer = T.TinkerTrainer(T.e2e_config(), clock=T.clock_for(2000.0, 2001.0))
    o["resume_load_ok"] = resumed_trainer.load_checkpoint(ck) is True
    resumed = resumed_trainer.train(T.DATA)
    o["resumed_scalars"] = [resumed.total_steps, resumed.total_batches,
                            resumed.samples_processed, resumed.tokens_processed]
    o["resumed_loss_history"] = list(resumed.loss_history)
    o["second_samples"] = resumed_trainer.train(T.DATA).samples_processed

    refusing = T.TinkerTrainer(T.e2e_config())
    refusing.load_checkpoint(ck)
    o["mm_refusing"] = raises(refusing.train, T.DATA[:6])
    finished = T.TinkerTrainer(T.e2e_config())
    finished.load_checkpoint(dataclasses.replace(ck, name="checkpoint-s000003", step=3, batches_completed=8))
    o["mm_finished"] = raises(finished.train, T.DATA)

    # P11 fireworks end to end
    fw = T.FireworksTrainer(T.FireworksTrainerConfig(base_model="qwen3-4b", epochs=4, seed=0, api_key=None))
    fw_result = fw.train(T.DATA[:3])
    o["fw_scalars"] = [fw_result.total_steps, fw_result.total_batches]
    o["fw_step_unit"] = read_field(fw_result.step_plan, "step_unit")
    o["fw_md_step_unit"] = fw_result.metadata["step_unit"]
    o["fw_md_keys"] = sorted(fw_result.metadata)
    o["fw_final_loss"] = fw_result.final_loss
    return o


# name -> (classname, probe). classname/name reproduce the current junit nodes so
# score.fold maps them to the identical fact keys.
PROBES = {
    "test_open::test_open_feature__one_step_unit_one_checkpoint_identity_one_resume_contract": probe_open,
    "test_r1::test_rule__the_three_trigger_names_in_ledger_order_under_one_padded_name": probe_r1_rule,
    "test_r1::test_scope__the_final_step_is_checkpointed_whatever_the_configuration": probe_r1_scope,
    "test_r1::test_exclusions__the_recorded_epoch_is_the_position_not_the_trigger": probe_r1_exclusions,
    "test_r1::test_failure_behavior__an_unknown_reason_is_refused_and_a_repeat_name_merges": probe_r1_failure_behavior,
    "test_r1::test_observability__the_two_checkpoints_of_the_end_to_end_run_read_back": probe_r1_observability,
    "test_r2::test_rule__inclusive_warmup_then_a_linear_decay_to_a_tenth_of_the_base_rate": probe_r2_rule,
    "test_r2::test_exclusions__clamped_past_the_end_and_a_grown_run_never_re_enters_warmup": probe_r2_exclusions,
    "test_r2::test_failure_behavior__a_warmup_longer_than_the_run_is_clipped_to_it": probe_r2_failure_behavior,
    "test_r2::test_observability__the_stated_rate_vectors_and_the_three_rates_of_the_run": probe_r2_observability,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        mp = MonkeyPatch()
        try:
            results[node] = {"ok": True, "obs": fn(mp)}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False,
                             "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
        finally:
            mp.undo()
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
