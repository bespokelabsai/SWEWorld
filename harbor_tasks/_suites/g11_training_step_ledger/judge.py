"""g11 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
the submission's source text, applies the assertions the g11 suite has always
made, and writes a `junit.xml` whose `classname`/`name` are the current suite's
node ids — so `score.py` and the bracket fold it into the identical fact keys.
Because no agent code runs in this process, the report it writes cannot be
forged by an `atexit` hook or a planted `sitecustomize`; that is the whole point
of the split.

Assertions and source checks are lifted from `test_open`/`test_r1`/`test_r2`.
Where a test read source with `inspect.getsource(mod)` this reads the module
file directly (parsing text executes nothing), which is both safe here and a
more faithful check of the graded artifact than trusting the worker to report
its own source.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlinks, size-capped) every
# agent-influenced path goes through; harness.py cannot: it imports pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402

BASE = 1e-4
SIGNATURE = "ds1-10-5d661fe8c9a2d002"


class Fail(AssertionError):
    pass


def _tol(b: float, rel: float, abs_: float) -> float:
    return max(rel * abs(b), abs_)


def _abs(x):
    return x if x >= 0 else -x


def approx_eq(a, b, *, rel: float = 1e-6, abs_: float = 1e-12) -> bool:
    return _abs(a - b) <= _tol(b, rel, abs_)


def approx_list(a, b, *, rel: float = 1e-6, abs_: float = 1e-12) -> bool:
    return len(a) == len(b) and all(approx_eq(x, y, rel=rel, abs_=abs_) for x, y in zip(a, b))


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def approxl(got, want, msg="", *, rel=1e-6, abs_=1e-12):
    if not approx_list(got, want, rel=rel, abs_=abs_):
        raise Fail(f"{msg}: {got!r} !~ {want!r}")


def approxs(got, want, msg="", *, rel=1e-6, abs_=1e-12):
    if not approx_eq(got, want, rel=rel, abs_=abs_):
        raise Fail(f"{msg}: {got!r} !~ {want!r}")


def raised_step_ledger(info, msg=""):
    ok(info.get("raised") and "StepLedgerError" in info.get("mro", []),
       f"{msg}: expected StepLedgerError, got {info}")


# ---------------------------------------------------------------------------
# r2
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    eq(o["MIN_LR_RATIO"], 0.1, "MIN_LR_RATIO")
    eq(o["param_kind"], "KEYWORD_ONLY", "min_lr_ratio kind")
    eq(o["param_default"], 0.1, "min_lr_ratio default")
    approxl(o["ramp"], [2.5e-05, 5e-05, 7.5e-05, 1e-04], "ramp", rel=1e-12)
    ok(o["ramp"][0] > 0.0, "ramp[0] > 0")
    approxs(o["lr_5"], 8.5e-05, "lr(5)", rel=1e-12)
    approxs(o["lr_7"], 5.5e-05, "lr(7)", rel=1e-12)
    approxs(o["lr_10"], 0.1 * BASE, "lr(10)", rel=1e-12)
    ok(o["lr_5"] < o["lr_4"], "lr(5) < lr(4)")
    gaps = [round(a - b, 15) for a, b in zip(o["after"], o["after"][1:])]
    approxl(gaps, [1.5e-05] * 6, "gaps", rel=1e-9)
    approxs(o["lr_10_half"], 5e-05, "lr(10,.5)", rel=1e-12)
    approxs(o["lr_7_half"], 7.5e-05, "lr(7,.5)", rel=1e-12)
    approxs(o["lr_10_zero"], 0.0, "lr(10,0)", abs_=1e-18)
    ok(not approx_eq(o["lr_5_10_0"], o["lr_5_100_0"], rel=1e-6), "schedule depends on length")


def judge_r2_exclusions(o):
    approxs(o["floor"], 1e-05, "floor", rel=1e-12)
    approxs(o["lr_9"], 1e-05, "lr(9)", rel=1e-12)
    approxs(o["lr_99"], 1e-05, "lr(99)", rel=1e-12)
    approxs(o["lr_10000"], 1e-05, "lr(10000)", rel=1e-12)
    approxs(o["lr_99"], o["floor"], "lr(99)==floor", rel=1e-12)
    ok(o["min_1_200"] >= 0.0, "min >= 0")
    ok(o["load_ok"], "load_checkpoint True")
    eq(o["total_steps"], 4, "resumed total_steps")
    eq(o["current_batch"], [7, 8, 9, 10, 11, 12], "current_batch")
    eq(o["current_step"], [2, 2, 3, 3, 3, 4], "current_step")
    approxl(o["learning_rate"], [5.5e-05] * 3 + [1e-05] * 3, "rates", rel=1e-12)
    approxl(o["learning_rate"], [o["lr_3_4_2"]] * 3 + [o["lr_4_4_2"]] * 3, "rates==lr_at", rel=1e-12)


def judge_r2_failure_behavior(o):
    approxl(o["clipped"], [BASE / 3, 2 * BASE / 3, BASE], "clipped", rel=1e-12)
    approxs(o["clipped"][-1], BASE, "clipped[-1]", rel=1e-12)
    approxl(o["ramp_4"], [2.5e-05, 5e-05, 7.5e-05, 1e-04], "ramp_4", rel=1e-12)
    ok(o["min_clipped"] > 0.0, "min(clipped) > 0")
    approxs(o["lr_1_1_99"], BASE, "lr(1,1,99)", rel=1e-12)


def judge_r2_observability(o):
    approxl(o["vec8"], [5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], "vec8", rel=1e-12)
    approxl(o["vec4"], [7.75e-05, 5.5e-05, 3.25e-05, 1e-05], "vec4", rel=1e-12)
    eq(o["total_steps"], 3, "total_steps")
    approxl(o["learning_rate"], [5e-05, 5e-05, 5e-05, 1e-04, 1e-04, 1e-04, 1e-05, 1e-05], "rates", rel=1e-12)


# ---------------------------------------------------------------------------
# r1
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["CHECKPOINT_REASONS"], ["interval", "epoch", "final"], "CHECKPOINT_REASONS")
    eq(o["name_template_2"], "checkpoint-s000002", "name template")
    c = o["canonical"]
    eq(c["feiee"], ["interval", "epoch", "final"], "canonical dedup/order")
    eq(c["fi"], ["interval", "final"], "canonical fi")
    eq(c["ei"], ["interval", "epoch"], "canonical ei")
    eq(c["fe"], ["epoch", "final"], "canonical fe")
    eq(c["empty"], [], "canonical empty")
    eq(c["ee"], ["epoch"], "canonical ee")
    eq(o["name_2"], "checkpoint-s000002", "checkpoint_name 2")
    eq(o["name_big"], "ckpt-s1234567", "checkpoint_name big")
    eq(o["name_sorted"], ["checkpoint-s000002", "checkpoint-s000010", "checkpoint-s000100"], "name sort")
    eq(o["fields_last"], "reasons", "last field")
    eq(o["param_kind"], "KEYWORD_ONLY", "reasons kind")
    eq(o["param_default"], ["interval"], "reasons default")
    eq(o["defaulted_reasons"], ["interval"], "defaulted reasons")
    eq(o["calls"].count("checkpoint-s000002"), 1, "step 2 written once")
    ok(len(o["calls"]) == len(set(o["calls"])) == o["n_checkpoints"], "one call per checkpoint")
    eq(o["by_name"]["checkpoint-s000002"], ["interval", "epoch"], "step 2 reasons")


def judge_r1_scope(o):
    eq(o["bare_total"], 3, "bare total")
    eq(o["bare_steps"], [3], "bare steps")
    eq(o["bare_reasons"], [["final"]], "bare reasons")
    eq(o["interval_steps"], [2, 3], "interval steps")
    eq(o["interval_reasons"], [["interval"], ["final"]], "interval reasons")
    eq(o["epoch_steps"], [2, 3], "epoch steps")
    eq(o["epoch_reasons"], [["epoch"], ["epoch", "final"]], "epoch reasons")
    eq(o["single_total"], 1, "single total")
    eq(o["single_steps"], [1], "single steps")
    eq(o["single_reasons"], [["final"]], "single reasons")
    ok(o["has_ledger"], "the checkpoint reason vocabulary is not implemented")  # require_feature
    eq(o["fw_checkpoints"], 0, "fireworks writes no checkpoints")
    ok(not o["fw_reasons_in_meta"], "fireworks gains no reasons")


def judge_r1_exclusions(o):
    eq(o["steps"], [2, 3, 4], "steps")
    ok(all(o["epoch_in_reasons"]), "epoch in every reasons")
    eq(o["shapes"], [[2, 2, 6], [3, 3, 9], [4, 3, 12]], "shapes")
    eq(o["epochs"], o["epoch_of_batch"], "epoch == epoch_of_batch")
    ok(o["epochs"] != [1, 2, 3], "epoch is not the trigger epoch")


def judge_r1_failure_behavior(o):
    raised_step_ledger(o["raise_periodic"], "periodic")
    raised_step_ledger(o["raise_manual"], "manual")
    raised_step_ledger(o["raise_caps"], "Interval")
    eq(o["stored_len"], 1, "one stored after merge")
    eq(o["stored_reasons_sorted"], ["final", "interval"], "stored reasons")
    eq(o["stored_loss"], 0.25, "stored loss")
    eq(o["merged_reasons_sorted"], ["final", "interval"], "merged reasons")
    eq(o["merged_loss"], 0.25, "merged loss")
    eq(o["names"], ["checkpoint-s000002", "checkpoint-s000003"], "append distinct name")


def judge_r1_observability(o):
    eq(o["n_fields"], 10, "CheckpointInfo field count")
    eq(o["last_two"], ["dataset_signature", "reasons"], "last two fields")
    eq(o["bare_reasons"], [], "bare reasons default")
    eq(o["names"], ["checkpoint-s000002", "checkpoint-s000003"], "names")
    eq(o["reasons"], [["interval", "epoch"], ["epoch", "final"]], "reasons")
    eq(o["shapes"], [[2, 2, 6], [3, 2, 8]], "shapes")
    eq(o["paths"], ["mock://checkpoints/checkpoint-s000002", "mock://checkpoints/checkpoint-s000003"], "paths")
    eq(o["batch_size"], [3, 3], "batch_size")
    eq(o["gas"], [3, 3], "gradient_accumulation_steps")
    eq(o["dataset_sig"], [SIGNATURE], "dataset_signature")
    approxl(o["loss"], [2.304145731814669, 2.228222171221575], "loss", rel=1e-12)
    eq(o["fx_total"], 1, "fixture total")
    eq(o["fx_n"], 1, "fixture checkpoints")
    eq(o["fx_name"], "checkpoint-s000001", "fixture name")
    eq(o["fx_reasons"], ["final"], "fixture reasons")
    eq(o["fx_loss_hist_len"], 1, "fixture loss_history")
    ok(o["fx_final_loss"] > 0, "fixture final_loss > 0")


BATCH_LOSSES = [2.077789074237476, 2.121022798529849, 2.2897142095845773,
                2.3705416248535185, 2.2443626393156957, 2.2975329312747927,
                2.1081007054826135, 2.348343636960536]


def raised_mismatch(info, fields, *, sle=False, ckname=None, msg=""):
    ok(info.get("raised"), f"{msg}: expected ResumePlanMismatch, none raised")
    ok("ResumePlanMismatch" in info.get("mro", []), f"{msg}: not ResumePlanMismatch: {info.get('mro')}")
    if sle:
        ok("StepLedgerError" in info.get("mro", []), f"{msg}: not a StepLedgerError")
    eq(info.get("mismatched_fields"), fields, f"{msg}: mismatched_fields")
    if ckname is not None:
        eq(info.get("checkpoint_name"), ckname, f"{msg}: checkpoint_name")


def _module_source(rel_candidates) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in rel_candidates:
        path = root / rel
        if path.is_file():
            return judge_io.read_text(path)
    raise Fail(f"cannot read source at any of {rel_candidates} under {root}")


def _check_leaf_module():
    """step_ledger imports no clock/rng and reaches types/config only under
    TYPE_CHECKING — the AST checks of test_open, over the file on disk."""
    src = _module_source(["bespokelabs/curator/finetune/step_ledger.py",
                          "bespokelabs/curator/finetune/step_ledger/__init__.py"])
    tree = ast.parse(src)
    type_checking = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            t = node.test
            named = (isinstance(t, ast.Name) and t.id == "TYPE_CHECKING") or \
                    (isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING")
            if named:
                for child in node.body:
                    for inner in ast.walk(child):
                        type_checking.add(id(inner))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            ok(name.split(".")[0] not in {"time", "datetime", "random"},
               f"step_ledger imports {name!r}")
            if "finetune.types" in name or "finetune.config" in name:
                ok(id(node) in type_checking, f"runtime import of {name!r} makes step_ledger a cycle")


def _check_tinker_no_wallclock():
    src = _module_source(["bespokelabs/curator/finetune/trainer/tinker_trainer.py",
                          "bespokelabs/curator/finetune/trainer/tinker_trainer/__init__.py"])
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        value = node.func.value
        if isinstance(value, ast.Name) and value.id == "time":
            ok(node.func.attr != "sleep", "time.sleep survives in tinker_trainer")
        if node.func.attr == "random" and isinstance(value, ast.Name) and value.id == "random":
            raise Fail("the module-global random.random() survives in tinker_trainer")


def judge_open(o):
    # P1 surface
    eq(o["STEP_UNIT_OPTIMIZER"], "optimizer_step", "STEP_UNIT_OPTIMIZER")
    eq(o["STEP_UNIT_PACKED"], "packed_epoch_step", "STEP_UNIT_PACKED")
    eq(o["DATASET_SIGNATURE_PREFIX"], "ds1", "DATASET_SIGNATURE_PREFIX")
    ok("ValueError" in o["sle_mro"], "StepLedgerError subclasses ValueError")
    ok("StepLedgerError" in o["rpm_mro"], "ResumePlanMismatch subclasses StepLedgerError")
    ok(o["is_dc"], "StepPlan/ResumePlan are dataclasses")
    eq(o["stepplan_fields"], ["step_unit", "num_examples", "batch_size", "epochs",
                              "gradient_accumulation_steps", "batches_per_epoch", "total_batches",
                              "total_steps", "trailing_window_batches", "dataset_signature"], "StepPlan fields")
    eq(o["resumeplan_fields"], ["checkpoint_name", "start_batch_ordinal", "start_epoch",
                                "start_batch_in_epoch", "completed_steps", "remaining_batches"], "ResumePlan fields")
    _check_leaf_module()

    # P2 unit
    ok(o["plan_isinstance"], "plan is a StepPlan")
    eq(o["plan_tuple"], [4, 8, 3, 2], "plan sizes")
    eq(o["plan_step_unit"], "optimizer_step", "plan.step_unit")
    eq(o["step_of_batch"], [1, 1, 1, 2, 2, 2, 3, 3], "step_of_batch")
    eq(o["is_step_boundary"], [False, False, True, False, False, True, False, True], "is_step_boundary")
    eq(o["epoch_of_batch"], [1, 1, 1, 1, 2, 2, 2, 2], "epoch_of_batch")
    eq(o["batch_slice"], [[0, 3], [3, 6], [6, 9], [9, 10], [0, 3], [3, 6], [6, 9], [9, 10]], "batch_slice")
    ok(o["frozen"], "StepPlan is frozen")
    eq(o["wide"], [2, 4], "wide plan")
    eq(o["even"], [3, 1], "even plan")
    for key in ("raise_zero_examples", "raise_zero_gas", "raise_zero_batch", "raise_zero_epochs"):
        raised_step_ledger(o[key], key)
    eq(o["logging_2"], [2], "logging_steps(2)")
    eq(o["loss_hist_2"], [2, 3], "loss_history_steps(2)")
    eq(o["loss_hist_1"], [1, 2, 3], "loss_history_steps(1)")
    eq(o["loss_hist_10"], [4, 8], "loss_history_steps(10)")

    # P5 signature
    eq(o["sig_data"], SIGNATURE, "dataset_signature(DATA)")
    eq(o["sig_len"], 23, "signature length")
    eq(o["sig_3"], "ds1-3-b8c83761d026bfe8", "signature of DATA[:3]")
    ok(o["sig_rev_ne"], "signature order-sensitive across examples")
    eq(o["sig_order_a"], o["sig_order_b"], "signature key-order-independent")

    # P11 packed
    eq(o["packed"], ["packed_epoch_step", 2, 1, 1, 5, 5, 1], "packed plan")
    raised_step_ledger(o["raise_packed_zero"], "packed zero")

    # types.py
    eq(o["checkpoint_fields"][:9], ["name", "path", "step", "epoch", "loss", "batch_size",
                                    "gradient_accumulation_steps", "batches_completed",
                                    "dataset_signature"], "CheckpointInfo fields")
    eq(o["bare_checkpoint"], [0, 0, 0, ""], "CheckpointInfo defaults")
    sf = o["stats_fields"]
    ok("current_batch" in sf and "total_batches" in sf, "TrainingStats has the two new fields")
    ok(sf.index("current_batch") < sf.index("total_batches"), "current_batch before total_batches")
    eq([f for f in sf if f not in ("current_batch", "total_batches")],
       ["current_epoch", "total_epochs", "current_step", "total_steps", "current_loss",
        "tokens_processed", "samples_processed", "learning_rate", "elapsed_time"], "TrainingStats other fields")
    eq(o["stats_defaults"], [0, 0], "TrainingStats defaults")
    rf = o["result_fields"]
    ok("total_batches" in rf and "step_plan" in rf, "TrainingResult has the two new fields")
    ok(rf.index("total_batches") < rf.index("step_plan"), "total_batches before step_plan")
    eq([f for f in rf if f not in ("total_batches", "step_plan")],
       ["final_loss", "total_steps", "total_epochs", "total_time", "tokens_processed",
        "samples_processed", "loss_history", "weights_name", "checkpoints", "metadata"], "TrainingResult other fields")
    eq(o["minimal_result"], [0, True], "TrainingResult minimal defaults")

    # config seed
    eq(o["tinker_seed"], 0, "Tinker seed default")
    eq(o["fw_seed"], 0, "Fireworks seed default")
    ok(o["raise_seed_neg"].get("raised"), "negative seed rejected")

    # P3/P9/P10 loop
    eq(o["plan_for_config"], o["plan_ref"], "plan_steps_for_config == plan_steps")
    eq(o["steps_seen"], [False, False, True, False, False, True, False, True], "trailing window stepped in loop")
    eq(o["result_scalars"], [3, 8, 2, 20, 120, 4.5, 2, True], "result scalars")
    eq(o["result_step_plan"], o["plan_ref"], "result.step_plan")
    eq(o["md_dataset_signature"], SIGNATURE, "metadata dataset_signature")
    eq(o["md"], {"base_model": "Qwen3-8B", "batch_size": 3, "learning_rate": 0.0001,
                 "lora_rank": 16, "lora_alpha": 32, "gradient_accumulation_steps": 3}, "metadata")
    eq(o["n_stats"], 8, "one stat per batch")
    eq(o["stat_batch_step"], [[1, 0], [2, 0], [3, 1], [4, 1], [5, 1], [6, 2], [7, 2], [8, 3]], "batch/step")
    eq(o["stat_epoch"], [1, 1, 1, 1, 2, 2, 2, 2], "stat epoch")
    eq(o["stat_total_steps"], [3], "stat total_steps")
    eq(o["stat_total_batches"], [8], "stat total_batches")
    eq(o["tracker_total_steps"], 3, "tracker total_steps")
    approxl(o["stat_loss"], BATCH_LOSSES, "per-batch loss", rel=1e-12)
    approxl(o["loss_history"], [2.304145731814669, 2.228222171221575], "loss_history", rel=1e-12)
    approxs(o["final_loss"], 2.228222171221575, "final_loss", rel=1e-12)
    approxs(o["rng_next"], 0.4765969541523558, "rng advanced eight draws")
    ok(o["again_loss"] == o["twice_loss"] == o["loss_history"], "seeded runs agree")
    _check_tinker_no_wallclock()
    eq(o["saved"], [3, "mock_weights_Qwen3-8B_lora_1700000000"], "saved weights off the clock")

    # P8 resume
    ok(o["resume_isinstance"], "resume is a ResumePlan")
    eq(o["resume_fields"], {"checkpoint_name": "checkpoint-s000002", "start_batch_ordinal": 6,
                            "start_epoch": 2, "start_batch_in_epoch": 2, "completed_steps": 2,
                            "remaining_batches": 2}, "resume fields")
    raised_mismatch(o["mm_reshaped"], ["batch_size", "dataset_signature"], sle=True,
                    ckname="checkpoint-s000002", msg="reshaped")
    raised_mismatch(o["mm_pre_ledger"], ["batch_size", "dataset_signature", "gradient_accumulation_steps"], msg="pre_ledger")
    raised_mismatch(o["mm_exhausted"], ["epochs"], msg="exhausted")
    eq(o["longer"], [4, 3], "grown resume")
    raised_mismatch(o["mm_inconsistent"], ["step"], msg="inconsistent")
    ok(o["resume_load_ok"], "load_checkpoint True")
    eq(o["resumed_scalars"], [3, 8, 4, 24], "resumed scalars")
    approxl(o["resumed_loss_history"], [2.099405936383662], "resumed loss_history", rel=1e-12)
    eq(o["second_samples"], 20, "second run starts from zero")
    raised_mismatch(o["mm_refusing"], ["dataset_signature"], ckname="checkpoint-s000002", msg="refusing")
    raised_mismatch(o["mm_finished"], ["epochs"], msg="finished")

    # P11 fireworks
    eq(o["fw_scalars"], [4, 4], "fireworks scalars")
    eq(o["fw_step_unit"], "packed_epoch_step", "fireworks step_unit")
    eq(o["fw_md_step_unit"], "packed_epoch_step", "fireworks metadata step_unit")
    eq(o["fw_md_keys"], ["base_model", "mock", "provider", "step_unit"], "fireworks metadata keys")
    approxs(o["fw_final_loss"], 2.077789074237476, "fireworks final_loss")


JUDGES = {
    "test_open::test_open_feature__one_step_unit_one_checkpoint_identity_one_resume_contract": judge_open,
    "test_r1::test_rule__the_three_trigger_names_in_ledger_order_under_one_padded_name": judge_r1_rule,
    "test_r1::test_scope__the_final_step_is_checkpointed_whatever_the_configuration": judge_r1_scope,
    "test_r1::test_exclusions__the_recorded_epoch_is_the_position_not_the_trigger": judge_r1_exclusions,
    "test_r1::test_failure_behavior__an_unknown_reason_is_refused_and_a_repeat_name_merges": judge_r1_failure_behavior,
    "test_r1::test_observability__the_two_checkpoints_of_the_end_to_end_run_read_back": judge_r1_observability,
    "test_r2::test_rule__inclusive_warmup_then_a_linear_decay_to_a_tenth_of_the_base_rate": judge_r2_rule,
    "test_r2::test_exclusions__clamped_past_the_end_and_a_grown_run_never_re_enters_warmup": judge_r2_exclusions,
    "test_r2::test_failure_behavior__a_warmup_longer_than_the_run_is_clipped_to_it": judge_r2_failure_behavior,
    "test_r2::test_observability__the_stated_rate_vectors_and_the_three_rates_of_the_run": judge_r2_observability,
}


def junit(results: list[tuple[str, str, str]]) -> str:
    """results: (classname, name, failure_message|"") -> a minimal junit doc."""
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g11_training_step_ledger" '
             f'tests="{len(results)}" failures="{fails}" errors="0">']
    for classname, name, failure in results:
        head = f'<testcase classname={quoteattr(classname)} name={quoteattr(name)}>'
        if failure:
            lines.append(head + f'<failure message={quoteattr(failure[:200])}>'
                         + escape(failure[:4000]) + '</failure></testcase>')
        else:
            lines.append(head + '</testcase>')
    lines.append('</testsuite></testsuites>')
    return "\n".join(lines)


def main(obs_path: str, out_path: str) -> int:
    try:
        observations = json.loads(judge_io.read_text(obs_path))
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results: list[tuple[str, str, str]] = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if probe is None:
            results.append((classname, name, "no observation from probe"))
            continue
        if not probe.get("ok"):
            results.append((classname, name, f"probe error: {probe.get('error', 'unknown')}"))
            continue
        try:
            judge(probe["obs"])
            results.append((classname, name, ""))
        except Fail as exc:
            results.append((classname, name, str(exc)))
        except Exception as exc:  # noqa: BLE001 - a malformed observation is a failed fact, not a crash
            results.append((classname, name, f"judge error: {type(exc).__name__}: {exc}"))

    pathlib.Path(out_path).write_text(junit(results))
    for classname, name, failure in results:
        print(f"{'FAIL' if failure else 'pass'} {classname}::{name}"
              + (f"  {failure[:160]}" if failure else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
