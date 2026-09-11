"""g1 — the openly stated feature: a pure planner behind `batch_size="auto"`.

The ticket names the whole surface: a new module `batch_payload_planner` exporting
`BatchLimits`, `PlannedBatch`, `payload_size_bytes`, `payload_bytes`, `plan_batches`,
`BatchPayloadTooLargeError` and `SingleRequestTooLargeError`; `batch_limits`,
`measure_request_payload` and `plan_request_batches` on `BaseBatchRequestProcessor`; and
an `"auto"` branch of `create_request_files` driven off `self.plan_request_batches(dataset)`,
writing `requests_{p.index}.jsonl` / `metadata_{p.index}.json` through the existing
`acreate_request_file` and returning one path per planned batch — with the
explicit-integer `batch_size` branch untouched.

This file also holds the fixtures the r1/r2 suites import: a processor built the way
`tests/unittests/test_batch.py:55` builds one — `__new__` plus four attributes, no client,
no network — and a context manager that patches the two limit properties with
`PropertyMock` the way `tests/integrations/test_all.py:469` does.

Nothing here asserts anything about a plan sidecar or about files being removed: those are
r1's and r2's hidden facts, and every assertion below is written so that an implementation
which does neither still passes.

The answer-free helpers/fixtures below (the processor builder, the limit-patching context,
the dataset factories and the log/metadata readers) live in `probe_support` so the split
worker (`probe.py`) and this human reference share ONE definition and cannot drift. The
expected VALUES this test asserts stay here (and in `judge.py`); `probe_support` holds none.
`test_r1`/`test_r2` import the names they need `from test_open`, which re-exports them.
"""
from __future__ import annotations

import glob
import json
import os

import pytest
from datasets import Dataset

from harness import read_field, surface  # noqa: F401 - surface used below

from probe_support import (  # noqa: F401 - re-exported for test_r1/test_r2
    MODEL,
    api_requests_for,
    basenames,
    check_cover,
    genparams_dataset,
    limits_of,
    make_processor,
    metadata_of,
    patched_limits,
    planner,
    prompt_dataset,
    request_lines,
    row_indices,
    tuples,
)


# =============================================================================
# the openly stated feature, end to end
# =============================================================================
def test_open_feature__auto_plans_batches_and_writes_one_file_per_planned_batch(tmp_path):
    module = planner()

    # --- the module's surface, as the ticket spells it -----------------------
    for name in ("BatchLimits", "PlannedBatch", "payload_size_bytes", "payload_bytes", "plan_batches", "BatchPayloadTooLargeError", "SingleRequestTooLargeError"):
        assert hasattr(module, name), f"batch_payload_planner does not export {name}; it has {surface(module)}"
    assert issubclass(module.BatchPayloadTooLargeError, ValueError)
    assert issubclass(module.SingleRequestTooLargeError, module.BatchPayloadTooLargeError)
    error = module.BatchPayloadTooLargeError(num_requests=2, size_bytes=99, limit_bytes=50)
    assert (read_field(error, "num_requests"), read_field(error, "size_bytes"), read_field(error, "limit_bytes")) == (2, 99, 50)

    # --- serialization: stock json.dumps, then UTF-8 -------------------------
    processor = make_processor(tmp_path / "run")
    row_0_request = api_requests_for(processor, prompt_dataset(1), 0, 1)[0]
    assert row_0_request == {
        "custom_id": "0",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": MODEL, "messages": [{"role": "user", "content": "say 0"}]},
    }, "fixture drift: the OpenAI batch request no longer has the shape the ticket quotes"
    assert module.payload_size_bytes(row_0_request) == 153
    # the ruler is the submitted payload, not the GenericRequest written to requests_*.jsonl
    generic = processor.prompt_formatter.create_generic_request({"prompt": "say 0"}, 0, False)
    assert len(json.dumps(generic.model_dump(), default=str).encode()) == 217, "fixture drift: the generic request is no longer 217 bytes"
    assert processor.measure_request_payload(generic) == 153

    # --- file accounting: the n-1 separators of "\n".join(...) ---------------
    assert module.payload_bytes([]) == 0
    assert module.payload_bytes([10]) == 10
    assert module.payload_bytes([10, 10, 10]) == 32

    # --- greedy forward fill, both limits inclusive, exhaustive spans --------
    assert module.plan_batches([], limits_of(module, 50_000, 200 * 1024 * 1024)) == []
    assert tuples(module.plan_batches([10] * 7, limits_of(module, 1000, 32))) == [(0, 0, 3, 3, 32), (1, 3, 6, 3, 32), (2, 6, 7, 1, 10)]
    assert tuples(module.plan_batches([10] * 6, limits_of(module, 3, 32))) == [(0, 0, 3, 3, 32), (1, 3, 6, 3, 32)]

    # --- one row bigger than the byte budget raises, it does not stall -------
    with pytest.raises(module.SingleRequestTooLargeError) as caught:
        module.plan_batches([10, 500, 10], limits_of(module, 1000, 32))
    err = caught.value
    assert (read_field(err, "row_idx"), read_field(err, "size_bytes"), read_field(err, "limit_bytes")) == (1, 500, 32)
    assert read_field(err, "num_requests") == 1
    assert isinstance(err, module.BatchPayloadTooLargeError) and isinstance(err, ValueError)

    # --- batch_limits mirrors the processor's own two properties -------------
    with patched_limits(max_requests=7, max_bytes=4242):
        got = processor.batch_limits
        assert (read_field(got, "max_requests_per_batch"), read_field(got, "max_bytes_per_batch")) == (7, 4242)

    # --- planning a dataset: the byte limit binds at 2 rows per batch --------
    dataset = prompt_dataset(5)
    with patched_limits(max_requests=3, max_bytes=400):
        plan = processor.plan_request_batches(dataset)
        assert tuples(plan) == [(0, 0, 2, 2, 307), (1, 2, 4, 2, 307), (2, 4, 5, 1, 153)]
        assert check_cover(plan, len(dataset))
        result = processor.create_request_files(dataset)

    run_dir = str(tmp_path / "run")
    assert result == [os.path.join(run_dir, f"requests_{i}.jsonl") for i in range(3)]
    for planned in plan:
        index = read_field(planned, "index")
        path = os.path.join(run_dir, f"requests_{index}.jsonl")
        assert row_indices(path) == list(range(read_field(planned, "start_idx"), read_field(planned, "end_idx"))), f"{path} does not hold the rows batch {index} was planned for"
        assert metadata_of(run_dir, index)["num_jobs"] == read_field(planned, "num_requests")

    # --- the planned size is the size of the file that is actually built -----
    assert processor.create_batch_file([]) == b""
    for planned in plan:
        requests = api_requests_for(processor, dataset, read_field(planned, "start_idx"), read_field(planned, "end_idx"))
        with patched_limits(max_requests=3, max_bytes=400):
            built = processor.create_batch_file(requests)
        assert len(built) == read_field(planned, "num_bytes"), f"planned batch {planned} does not agree with create_batch_file"

    # --- row-level generation_params are part of the measured payload -------
    gp_dir = tmp_path / "genparams"
    gp_processor = make_processor(gp_dir)
    gp_dataset = genparams_dataset(6)
    with patched_limits(max_requests=1_000_000, max_bytes=480):
        gp_plan = gp_processor.plan_request_batches(gp_dataset)
        assert tuples(gp_plan) == [(0, 0, 2, 2, 347), (1, 2, 4, 2, 347), (2, 4, 6, 2, 347)]
        gp_processor.create_request_files(gp_dataset)
    assert [len(request_lines(os.path.join(str(gp_dir), f"requests_{i}.jsonl"))) for i in range(3)] == [2, 2, 2]

    # --- every file the plan asked for comes back, in numeric order ----------
    wide_dir = tmp_path / "wide"
    wide = make_processor(wide_dir)
    with patched_limits(max_requests=1):
        wide_result = wide.create_request_files(prompt_dataset(11))
    assert basenames(wide_result) == [f"requests_{i}.jsonl" for i in range(11)]

    # --- zero rows plans zero batches and writes no request file ------------
    empty_dir = tmp_path / "empty"
    empty = make_processor(empty_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        assert empty.plan_request_batches(Dataset.from_dict({"prompt": []})) == []
        assert empty.create_request_files(Dataset.from_dict({"prompt": []})) == []
    assert glob.glob(os.path.join(str(empty_dir), "requests_*.jsonl")) == []
    assert glob.glob(os.path.join(str(empty_dir), "metadata_*.json")) == []

    # --- the explicit-integer branch is untouched ----------------------------
    fixed_dir = tmp_path / "fixed"
    fixed = make_processor(fixed_dir, batch_size=2)
    fixed_result = fixed.create_request_files(dataset)
    assert fixed_result == [os.path.join(str(fixed_dir), f"requests_{i}.jsonl") for i in range(3)]
    assert [len(request_lines(path)) for path in fixed_result] == [2, 2, 1]
