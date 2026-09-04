"""g1 — hidden requirement r2: the `"auto"` branch sweeps its stale numbering.

    rule              once the plan has returned, every existing `requests_*.jsonl` and
                      `metadata_*.json` in the working dir is removed, so a longer numbering
                      left by an earlier run cannot be picked up by a later glob
    scope             sweeping belongs to the `"auto"` branch alone: the explicit-integer
                      branch and the `dataset is None` path leave earlier files in place
    exclusions        only those two patterns go: `responses_*.jsonl`, `*.arrow`,
                      `batch_objects.jsonl` and everything else survive byte-for-byte
    failure_behavior  the sweep sits behind a plan that returned — a planning failure leaves
                      the working directory byte-for-byte what it was
    observability     the exact directory listing after a successful run and after a failed one

`batch_plan.json` is r1's fact, so nothing here asserts that it exists: the listings below
are compared with that one name filtered out, and an implementation that sweeps without
writing a sidecar passes r2 in full.
"""
from __future__ import annotations

import glob
import json
import os

import pytest
from datasets import Dataset

from harness import read_field, require_feature

from test_open import (
    make_processor,
    patched_limits,
    planner,
    prompt_dataset,
    row_indices,
)

STALE_REQUEST = "stale\n"
STALE_METADATA = "{}\n"
PLAN_FILE = "batch_plan.json"


def prepopulate(working_dir, *, n=6, extra=None):
    """A working dir left behind by an earlier, differently-limited `"auto"` run."""
    os.makedirs(working_dir, exist_ok=True)
    for i in range(n):
        with open(os.path.join(working_dir, f"requests_{i}.jsonl"), "w") as handle:
            handle.write(STALE_REQUEST)
        # `{}` and not `{"num_jobs": 1}`: a metadata file the cache check cannot read is
        # what makes curator regenerate rather than return the stale files as a cache hit.
        with open(os.path.join(working_dir, f"metadata_{i}.json"), "w") as handle:
            handle.write(STALE_METADATA)
    for name, body in (extra or {}).items():
        with open(os.path.join(working_dir, name), "w") as handle:
            handle.write(body)
    return working_dir


def snapshot(working_dir):
    """name -> bytes, for every file in the directory."""
    return {name: open(os.path.join(working_dir, name), "rb").read() for name in sorted(os.listdir(working_dir))}


def listing(working_dir, keep=()):
    """The request/metadata numbering plus the named bystanders, and nothing else.

    Whatever a run records about its plan is r1's fact and is filtered out here, so an
    implementation that sweeps without writing a sidecar — or that writes one under some
    other name — is still graded on the sweep alone.
    """
    return sorted(name for name in os.listdir(working_dir) if name in keep or name.startswith("requests_") or name.startswith("metadata_"))


def big_dataset():
    """Row 1 is larger on its own than the 400-byte budget, so planning must raise."""
    return Dataset.from_dict({"prompt": ["ok", "x" * 600, "ok"]})


def swept(tmp_path, name):
    """Run a clean `"auto"` run over a pre-populated dir; True when the stale tail is gone."""
    working_dir = prepopulate(str(tmp_path / name))
    processor = make_processor(working_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        processor.create_request_files(prompt_dataset(5))
    return not os.path.exists(os.path.join(working_dir, "requests_5.jsonl"))


# =============================================================================
# rule — the stale numbering is cleared once the plan is in hand
# =============================================================================
def test_rule__stale_request_and_metadata_files_are_removed_by_the_auto_branch(tmp_path):
    planner()  # the feature under test cannot exist without the planner module
    working_dir = prepopulate(str(tmp_path / "run"))
    processor = make_processor(working_dir)
    dataset = prompt_dataset(5)

    with patched_limits(max_requests=3, max_bytes=400):
        plan = processor.plan_request_batches(dataset)
        processor.create_request_files(dataset)
    # five rows can never need six batches, so the stale tail is always observable
    assert 1 <= len(plan) <= 5, f"fixture drift: five rows planned {len(plan)} batches"

    # The surviving numbering is exactly the one the plan asked for: whatever ruler the
    # implementation measures with, nothing above the plan's own last index may remain.
    # Only the two globs the requirement names are compared, so a run that also drops
    # some other file of its own in the working dir is not judged on that here.
    assert sorted(os.path.basename(p) for p in glob.glob(os.path.join(working_dir, "requests_*.jsonl"))) == [
        f"requests_{i}.jsonl" for i in range(len(plan))
    ], f"stale request files a later glob would pick up survived the run: {sorted(os.listdir(working_dir))}"
    assert sorted(os.path.basename(p) for p in glob.glob(os.path.join(working_dir, "metadata_*.json"))) == [
        f"metadata_{i}.json" for i in range(len(plan))
    ], f"stale metadata files survived the run: {sorted(os.listdir(working_dir))}"
    # the surviving files are the new run's, not stale content left in place
    assert row_indices(os.path.join(working_dir, "requests_0.jsonl")) == list(
        range(read_field(plan[0], "start_idx"), read_field(plan[0], "end_idx"))
    )


# =============================================================================
# scope — the other two paths do not sweep
# =============================================================================
def test_scope__the_explicit_integer_branch_and_the_none_path_leave_files_alone(tmp_path):
    planner()
    # An untouched checkout deletes nothing anywhere, so this constraint only counts once
    # the `"auto"` branch is shown to sweep.
    require_feature(swept(tmp_path, "proof"), "the \"auto\" branch's sweep of stale request files")

    # --- explicit-integer batch_size: incomplete_files still owns the numbering
    fixed_dir = prepopulate(str(tmp_path / "fixed"))
    fixed = make_processor(fixed_dir, batch_size=2)
    fixed.create_request_files(prompt_dataset(3))
    for i in (2, 3, 4, 5):
        assert os.path.exists(os.path.join(fixed_dir, f"requests_{i}.jsonl")), f"the explicit-integer branch removed requests_{i}.jsonl"
        assert os.path.exists(os.path.join(fixed_dir, f"metadata_{i}.json")), f"the explicit-integer branch removed metadata_{i}.json"
    assert open(os.path.join(fixed_dir, "requests_5.jsonl")).read() == STALE_REQUEST

    # --- the `dataset is None` path writes requests_0.jsonl and nothing else changes
    none_dir = prepopulate(str(tmp_path / "none"))
    none_processor = make_processor(none_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        none_processor.create_request_files(None)
    for i in (1, 2, 3, 4, 5):
        assert os.path.exists(os.path.join(none_dir, f"requests_{i}.jsonl")), f"the `dataset is None` path removed requests_{i}.jsonl"
        assert os.path.exists(os.path.join(none_dir, f"metadata_{i}.json")), f"the `dataset is None` path removed metadata_{i}.json"
    assert open(os.path.join(none_dir, "requests_3.jsonl")).read() == STALE_REQUEST


# =============================================================================
# exclusions — only the two glob patterns are removed
# =============================================================================
def test_exclusions__nothing_but_request_and_metadata_files_is_touched(tmp_path):
    planner()
    keepers = {
        "responses_0.jsonl": "keep\n",
        "responses_1.jsonl": '{"row_idx": 1}\n',
        "batch_objects.jsonl": '{"id": "batch_abc"}\n',
        "a1b2c3.arrow": "not really arrow, but not ours to delete\n",
        "notes.txt": "hand-written\n",
    }
    working_dir = prepopulate(str(tmp_path / "run"), extra=keepers)
    before = {name: snapshot(working_dir)[name] for name in keepers}

    processor = make_processor(working_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        processor.create_request_files(prompt_dataset(5))

    # the sweep has to have happened for its narrowness to mean anything
    require_feature(not os.path.exists(os.path.join(working_dir, "requests_5.jsonl")), "the \"auto\" branch's sweep of stale request files")

    after = snapshot(working_dir)
    for name, body in before.items():
        assert name in after, f"the sweep removed {name}, which is not a request or metadata file"
        assert after[name] == body, f"{name} was rewritten by the sweep"


# =============================================================================
# failure_behavior — a plan that raises leaves the directory exactly as it was
# =============================================================================
def test_failure_behavior__a_planning_failure_removes_and_writes_nothing(tmp_path):
    module = planner()
    # An implementation that never sweeps leaves the directory alone here by doing nothing,
    # so this only counts once the `"auto"` branch is shown to sweep on the success path.
    require_feature(swept(tmp_path, "proof"), "the \"auto\" branch's sweep of stale request files")
    working_dir = prepopulate(str(tmp_path / "run"), extra={"responses_0.jsonl": "keep\n", PLAN_FILE: json.dumps({"plan_format_version": 1, "stale": True}) + "\n"})
    processor = make_processor(working_dir)
    before = snapshot(working_dir)
    assert len(before) == 14, "fixture drift: the pre-populated working dir should hold 14 files"

    dataset = big_dataset()
    # Asserted on the planner first: it is pure, it writes nothing, and reaching
    # create_request_files only once planning is known to raise keeps a half-ported
    # implementation from being graded on how long its old `while True` loop runs.
    with patched_limits(max_requests=3, max_bytes=400):
        with pytest.raises(module.SingleRequestTooLargeError) as caught:
            processor.plan_request_batches(dataset)
    assert read_field(caught.value, "row_idx") == 1

    with pytest.raises(module.SingleRequestTooLargeError):
        with patched_limits(max_requests=3, max_bytes=400):
            processor.create_request_files(dataset)

    assert snapshot(working_dir) == before, "a planning failure changed the working directory"


# =============================================================================
# observability — the directory listing after a success and after a failure
# =============================================================================
def test_observability__the_working_directory_after_a_successful_and_a_failed_run(tmp_path):
    module = planner()

    good_dir = prepopulate(str(tmp_path / "good"), extra={"responses_0.jsonl": "keep\n"})
    good = make_processor(good_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        good.create_request_files(prompt_dataset(5))
    assert listing(good_dir, keep={"responses_0.jsonl"}) == [
        "metadata_0.json",
        "metadata_1.json",
        "metadata_2.json",
        "requests_0.jsonl",
        "requests_1.jsonl",
        "requests_2.jsonl",
        "responses_0.jsonl",
    ], f"after the run the working dir holds {sorted(os.listdir(good_dir))}"
    assert open(os.path.join(good_dir, "responses_0.jsonl")).read() == "keep\n"

    bad_dir = prepopulate(str(tmp_path / "bad"), extra={"responses_0.jsonl": "keep\n", PLAN_FILE: json.dumps({"plan_format_version": 1, "stale": True}) + "\n"})
    bad = make_processor(bad_dir)
    with pytest.raises(module.SingleRequestTooLargeError):
        with patched_limits(max_requests=3, max_bytes=400):
            bad.plan_request_batches(big_dataset())
    with pytest.raises(module.SingleRequestTooLargeError):
        with patched_limits(max_requests=3, max_bytes=400):
            bad.create_request_files(big_dataset())

    assert sorted(os.listdir(bad_dir)) == [
        "batch_plan.json",
        "metadata_0.json",
        "metadata_1.json",
        "metadata_2.json",
        "metadata_3.json",
        "metadata_4.json",
        "metadata_5.json",
        "requests_0.jsonl",
        "requests_1.jsonl",
        "requests_2.jsonl",
        "requests_3.jsonl",
        "requests_4.jsonl",
        "requests_5.jsonl",
        "responses_0.jsonl",
    ], f"after the failed run the working dir holds {sorted(os.listdir(bad_dir))}"
    assert json.load(open(os.path.join(bad_dir, PLAN_FILE))) == {"plan_format_version": 1, "stale": True}
    assert open(os.path.join(bad_dir, "requests_2.jsonl")).read() == STALE_REQUEST
