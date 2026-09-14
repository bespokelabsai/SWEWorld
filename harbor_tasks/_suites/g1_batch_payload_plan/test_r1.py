"""g1 — hidden requirement r1: the plan is written down, in a versioned sidecar.

    rule              `batch_payload_planner` exports `PLAN_FILE_NAME`, `PLAN_FORMAT_VERSION`,
                      `plan_fingerprint` and `plan_document`; the `"auto"` branch writes that
                      document to `<working_dir>/batch_plan.json`, and the fingerprint covers
                      the cuts and the batch sizes only
    scope             the sidecar is written in the `"auto"` branch only, before the request
                      files, and for a 0-batch plan too; never on the explicit-integer branch
                      nor on the `dataset is None` path
    exclusions        `metadata_{i}.json` keeps its `{"num_jobs": n}` body — the plan shape is
                      recorded in the sidecar and nowhere else
    failure_behavior  a plan of more than `max_batches_per_plan` batches raises
                      `BatchPlanTooFragmentedError`; 512 is admissible, 513 is not, and the
                      per-row oversize scan still wins
    observability     the exact 12-hex `plan_id` strings, and the exact document the 5-row run
                      leaves on disk

Each test stays on its own fact. `rule` and `scope` never hardcode a digest — they compare
`plan_id` against the implementation's own `plan_fingerprint`, so an agent who chose a
different hash is judged on that in `observability` alone. `observability` in turn takes
`limits` from the implementation's own `batch_limits`, so the fan-out cap of
`failure_behavior` is not charged twice.

NOT THE GRADED PATH. The suite grades through `probe.py`/`judge.py`, and the
judge DERIVES its expectations from the seed root draws per run rather than
holding the literals below: a fixed fixture makes every expected value the same
every run, and g1's are written down in the world the agent reads, so a tree
implementing nothing could hardcode a passing observations file (measured:
reward 1.0). What is here is the worked example of each fact on the old fixed
fixture, and the fact<->test bijection. Read it to see what a fact MEANS; read
`judge.py` for how it is decided.
"""
from __future__ import annotations

import dataclasses
import json
import os

import pytest
from datasets import Dataset

from harness import read_field, require_feature, surface

from test_open import (
    make_processor,
    metadata_of,
    patched_limits,
    planner,
    prompt_dataset,
    tuples,
)

PLAN_DEFAULT = "batch_plan.json"


def auto_run(tmp_path, name, dataset, *, max_requests=3, max_bytes=400):
    """A 5-row-style `"auto"` run in its own fresh working dir. Returns (processor, plan, dir)."""
    working_dir = str(tmp_path / name)
    processor = make_processor(working_dir)
    with patched_limits(max_requests=max_requests, max_bytes=max_bytes):
        plan = processor.plan_request_batches(dataset)
        processor.create_request_files(dataset)
        limits = processor.batch_limits
    return processor, plan, working_dir, limits


def plan_path(module, working_dir):
    return os.path.join(working_dir, getattr(module, "PLAN_FILE_NAME", PLAN_DEFAULT))


def load_plan_file(module, working_dir):
    path = plan_path(module, working_dir)
    assert os.path.isfile(path), f"the \"auto\" branch wrote no plan sidecar; {working_dir} holds {sorted(os.listdir(working_dir))}"
    with open(path) as handle:
        return json.load(handle)


# =============================================================================
# rule — the plan is recorded as a versioned document in the working dir
# =============================================================================
def test_rule__the_auto_branch_records_the_plan_in_a_versioned_sidecar(tmp_path):
    module = planner()

    for name in ("PLAN_FILE_NAME", "PLAN_FORMAT_VERSION", "plan_fingerprint", "plan_document"):
        assert hasattr(module, name), f"batch_payload_planner does not export {name}; it has {surface(module)}"
    assert module.PLAN_FILE_NAME == "batch_plan.json"
    assert module.PLAN_FORMAT_VERSION == 1

    # the fingerprint is taken over where the cuts fall and how big each batch is:
    # `index` and `num_requests` are derivable from the span and do not enter it.
    same_cuts = module.plan_fingerprint([module.PlannedBatch(0, 0, 2, 2, 307), module.PlannedBatch(1, 2, 4, 2, 307)])
    relabelled = module.plan_fingerprint([module.PlannedBatch(5, 0, 2, 99, 307), module.PlannedBatch(9, 2, 4, 77, 307)])
    assert same_cuts == relabelled, "plan_fingerprint changed when only index/num_requests changed"
    assert same_cuts != module.plan_fingerprint([module.PlannedBatch(0, 0, 2, 2, 307), module.PlannedBatch(1, 2, 4, 2, 308)]), "plan_fingerprint ignores the batch sizes"
    assert same_cuts != module.plan_fingerprint([module.PlannedBatch(0, 0, 3, 3, 307), module.PlannedBatch(1, 3, 4, 1, 307)]), "plan_fingerprint ignores where the cuts fall"

    dataset = prompt_dataset(5)
    processor, plan, working_dir, limits = auto_run(tmp_path, "run", dataset)
    assert len(plan) == 3, f"fixture drift: five rows at 3/400 should plan 3 batches, got {tuples(plan)}"

    doc = load_plan_file(module, working_dir)
    assert list(doc) == ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests", "num_bytes", "batches"], f"the sidecar's envelope is {list(doc)}"
    assert doc["plan_format_version"] == 1
    assert doc["plan_id"] == module.plan_fingerprint(plan)
    assert doc["limits"] == dataclasses.asdict(limits)
    assert doc["num_batches"] == len(plan)
    assert doc["num_requests"] == sum(read_field(p, "num_requests") for p in plan)
    assert doc["num_bytes"] == sum(read_field(p, "num_bytes") for p in plan)
    assert doc["batches"] == [dataclasses.asdict(p) for p in plan]
    assert list(doc["batches"][0]) == ["index", "start_idx", "end_idx", "num_requests", "num_bytes"], f"a batch entry's keys are {list(doc['batches'][0])}"
    # ...and the document is what `plan_document` builds for that plan.
    assert doc == json.loads(json.dumps(module.plan_document(plan, limits)))


# =============================================================================
# scope — the "auto" branch only, before the request files, empty plan included
# =============================================================================
def test_scope__only_the_auto_branch_writes_it_and_an_empty_plan_still_does(tmp_path):
    module = planner()

    # --- written before any request file of its own run ----------------------
    working_dir = str(tmp_path / "ordered")
    processor = make_processor(working_dir)
    seen = {}
    original = processor.acreate_request_file

    async def recording(*args, **kwargs):
        seen.setdefault("plan_exists", os.path.exists(plan_path(module, working_dir)))
        return await original(*args, **kwargs)

    processor.acreate_request_file = recording
    with patched_limits(max_requests=3, max_bytes=400):
        processor.create_request_files(prompt_dataset(5))
    assert os.path.isfile(plan_path(module, working_dir)), "the \"auto\" branch wrote no plan sidecar"
    if seen:  # an implementation that reuses acreate_request_file, as the ticket says to
        assert seen["plan_exists"] is True, "the sidecar was written after the request files, not before them"

    # --- a 0-batch plan is still recorded ------------------------------------
    empty_dir = str(tmp_path / "empty")
    empty = make_processor(empty_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        assert empty.create_request_files(Dataset.from_dict({"prompt": []})) == []
    empty_doc = load_plan_file(module, empty_dir)
    assert (empty_doc["num_batches"], empty_doc["num_requests"], empty_doc["num_bytes"], empty_doc["batches"]) == (0, 0, 0, [])
    assert empty_doc["plan_id"] == module.plan_fingerprint([])

    # --- the explicit-integer branch never writes it -------------------------
    fixed_dir = str(tmp_path / "fixed")
    fixed = make_processor(fixed_dir, batch_size=2)
    fixed.create_request_files(prompt_dataset(3))
    assert module.PLAN_FILE_NAME not in os.listdir(fixed_dir), f"the explicit-integer branch wrote a plan sidecar: {sorted(os.listdir(fixed_dir))}"

    # --- and neither does the `dataset is None` path -------------------------
    none_dir = str(tmp_path / "none")
    none_processor = make_processor(none_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        none_processor.create_request_files(None)
    assert module.PLAN_FILE_NAME not in os.listdir(none_dir), f"the `dataset is None` path wrote a plan sidecar: {sorted(os.listdir(none_dir))}"


# =============================================================================
# exclusions — metadata_{i}.json keeps its one-key body
# =============================================================================
def test_exclusions__metadata_files_still_hold_num_jobs_and_nothing_else(tmp_path):
    module = planner()
    dataset = prompt_dataset(5)
    processor, plan, working_dir, _limits = auto_run(tmp_path, "run", dataset)

    # A preservation constraint: an untouched checkout keeps `{"num_jobs": n}` by doing
    # nothing, so it is only creditable once the sidecar it defers to actually exists.
    require_feature(os.path.isfile(plan_path(module, working_dir)), "the batch_plan.json sidecar")

    for planned in plan:
        index = read_field(planned, "index")
        metadata = metadata_of(working_dir, index)
        assert set(metadata) == {"num_jobs"}, f"metadata_{index}.json carries plan fields it should not: {metadata}"
        assert metadata["num_jobs"] == read_field(planned, "num_requests")


# =============================================================================
# failure_behavior — a plan may not exceed max_batches_per_plan batches
# =============================================================================
def test_failure_behavior__a_plan_of_more_than_512_batches_is_refused(tmp_path):
    module = planner()
    assert hasattr(module, "BatchPlanTooFragmentedError"), f"batch_payload_planner does not export BatchPlanTooFragmentedError; it has {surface(module)}"
    assert issubclass(module.BatchPlanTooFragmentedError, ValueError)
    assert not issubclass(module.BatchPlanTooFragmentedError, module.BatchPayloadTooLargeError), "a fragmented plan is not an oversized payload"

    one_per_batch = module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000)
    assert len(module.plan_batches([10] * 512, one_per_batch)) == 512, "512 batches is the boundary and it is admissible"

    with pytest.raises(module.BatchPlanTooFragmentedError) as caught:
        module.plan_batches([10] * 513, one_per_batch)
    assert read_field(caught.value, "num_batches") == 513, "the error does not report the full count the plan would have needed"
    assert read_field(caught.value, "limit") == 512

    with pytest.raises(module.BatchPlanTooFragmentedError) as caught:
        module.plan_batches([10] * 3, module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000, max_batches_per_plan=2))
    assert (read_field(caught.value, "num_batches"), read_field(caught.value, "limit")) == (3, 2), "an explicit max_batches_per_plan is not honoured"

    # the per-row oversize scan runs first: a dataset tripping both raises for the row
    with pytest.raises(module.SingleRequestTooLargeError) as caught:
        module.plan_batches([10] * 600 + [5000], one_per_batch)
    assert read_field(caught.value, "row_idx") == 600


# =============================================================================
# observability — the exact plan_id strings and the exact document on disk
# =============================================================================
def test_observability__plan_id_is_the_first_twelve_hex_of_sha256_over_the_cuts(tmp_path):
    module = planner()

    assert module.plan_fingerprint([]) == "e3b0c44298fc"
    assert module.plan_fingerprint(module.plan_batches([10] * 7, module.BatchLimits(max_requests_per_batch=1000, max_bytes_per_batch=32))) == "ad0828fea95e"
    assert (
        module.plan_fingerprint(
            [
                module.PlannedBatch(0, 0, 2, 2, 307),
                module.PlannedBatch(1, 2, 4, 2, 307),
                module.PlannedBatch(2, 4, 5, 1, 153),
            ]
        )
        == "f4b1ea1573c0"
    )

    # the 11-batch plan of an 11-row dataset, one request per batch
    wide_dir = str(tmp_path / "wide")
    wide = make_processor(wide_dir)
    with patched_limits(max_requests=1):
        wide_plan = wide.plan_request_batches(prompt_dataset(11))
    assert len(wide_plan) == 11, f"fixture drift: 11 rows at one per batch, got {tuples(wide_plan)}"
    assert module.plan_fingerprint(wide_plan) == "c53f6fb95c13"

    # --- and the document the 5-row run leaves behind ------------------------
    dataset = prompt_dataset(5)
    processor, plan, working_dir, limits = auto_run(tmp_path, "run", dataset)
    doc = load_plan_file(module, working_dir)
    assert doc == {
        "plan_format_version": 1,
        "plan_id": "f4b1ea1573c0",
        # taken from the implementation's own limits, so the fan-out cap is graded once,
        # under failure_behavior, and not a second time here
        "limits": json.loads(json.dumps(dataclasses.asdict(limits))),
        "num_batches": 3,
        "num_requests": 5,
        "num_bytes": 767,
        "batches": [
            {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307},
            {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307},
            {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153},
        ],
    }
    assert doc["limits"]["max_requests_per_batch"] == 3 and doc["limits"]["max_bytes_per_batch"] == 400

    with open(plan_path(module, working_dir)) as handle:
        raw = handle.read()
    assert raw.endswith("]\n}\n"), f"the sidecar is not indented JSON with a trailing newline: {raw[-20:]!r}"
