"""g1 — the openly stated feature: a pure planner behind `batch_size="auto"`.

The ticket names the whole surface: a new module `batch_payload_planner` exporting
`BatchLimits`, `PlannedBatch`, `payload_size_bytes`, `payload_bytes`, `plan_batches` and
`BatchPayloadTooLargeError`; `batch_limits`, `measure_request_payload` and
`plan_request_batches` on `BaseBatchRequestProcessor`; and a `"auto"` branch of
`create_request_files` driven off `self.plan_request_batches(dataset)`, writing
`requests_{i}.jsonl` / `metadata_{i}.json` through the existing `acreate_request_file`,
with the explicit-integer `batch_size` branch untouched.

This file also holds the fixtures the r1/r2 suites import: a processor built the way
`tests/unittests/test_batch.py:55` builds one — `__new__` plus four attributes, no client,
no network — and a context manager that patches the two limit properties with
`PropertyMock` the way `tests/integrations/test_all.py:469` does.

Deliberately ruler-agnostic. Which bytes a row is measured in is r1's hidden fact, so the
byte-limit half of this test asserts only what the ticket says out loud — that every batch
the planner produced is one `create_batch_file` accepts — and never a specific byte count.
"""
from __future__ import annotations

import contextlib
import glob
import json
import os

import pytest
from datasets import Dataset
from unittest.mock import PropertyMock, patch

from harness import read_field, surface

from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.request_processor.batch.openai_batch_request_processor import OpenAIBatchRequestProcessor
from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

MODEL = "gpt-4o-mini"


class _CostProcessorStub:
    """Batch processors touch `_cost_processor` on construction paths we never reach."""

    def cost(self, **kwargs):
        return 0.0


def make_processor(working_dir, *, batch_size="auto", generation_params=None):
    """An OpenAI batch processor with no client, the way curator's own unit tests build one."""
    processor = OpenAIBatchRequestProcessor.__new__(OpenAIBatchRequestProcessor)
    processor.config = BatchRequestProcessorConfig(model=MODEL, batch_size=batch_size)
    processor.prompt_formatter = PromptFormatter(
        model_name=MODEL,
        prompt_func=lambda row: row["prompt"],
        parse_func=None,
        response_format=None,
        generation_params=dict(generation_params or {}),
        system_prompt=None,
    )
    processor.working_dir = str(working_dir)
    processor._cost_processor = _CostProcessorStub()
    os.makedirs(processor.working_dir, exist_ok=True)
    return processor


@contextlib.contextmanager
def patched_limits(*, max_requests=None, max_bytes=None):
    """Patch either provider limit on the class, leaving the other one alone."""
    with contextlib.ExitStack() as stack:
        if max_requests is not None:
            prop = stack.enter_context(
                patch.object(OpenAIBatchRequestProcessor, "max_requests_per_batch", new_callable=PropertyMock))
            prop.return_value = max_requests
        if max_bytes is not None:
            prop = stack.enter_context(
                patch.object(OpenAIBatchRequestProcessor, "max_bytes_per_batch", new_callable=PropertyMock))
            prop.return_value = max_bytes
        yield


def planner():
    """The new module, or a failure that says so in one line."""
    try:
        from bespokelabs.curator.request_processor import batch_payload_planner
    except ImportError as exc:  # pragma: no cover - the pristine tree
        pytest.fail(
            "bespokelabs.curator.request_processor.batch_payload_planner does not import, "
            f"so there is no planner to grade: {exc}")
    return batch_payload_planner


def limits_of(module, max_requests, max_bytes):
    return module.BatchLimits(max_requests_per_batch=max_requests, max_bytes_per_batch=max_bytes)


def spans(plan):
    """(index, start_idx, end_idx, num_requests) per batch — the shape, not the byte count."""
    return [
        (
            read_field(p, "index"),
            read_field(p, "start_idx"),
            read_field(p, "end_idx"),
            read_field(p, "num_requests"),
        )
        for p in plan
    ]


def counts(plan):
    return [read_field(p, "num_requests") for p in plan]


def check_cover(plan, n_rows):
    """The plan is a contiguous, ordered, exhaustive cover of the dataset."""
    assert plan, "the plan is empty"
    assert read_field(plan[0], "start_idx") == 0, f"the plan does not start at row 0: {plan}"
    assert read_field(plan[-1], "end_idx") == n_rows, f"the plan does not reach row {n_rows}: {plan}"
    for i, planned in enumerate(plan):
        assert read_field(planned, "index") == i, f"planned batches are not indexed 0..n-1: {plan}"
        assert read_field(planned, "num_requests") == (
            read_field(planned, "end_idx") - read_field(planned, "start_idx")), f"bad span: {planned}"
    for earlier, later in zip(plan, plan[1:]):
        assert read_field(earlier, "end_idx") == read_field(later, "start_idx"), (
            f"planned batches are not a contiguous cover: {plan}")
    return True


def prompt_dataset(n, prefix="say "):
    return Dataset.from_dict({"prompt": [f"{prefix}{i}" for i in range(n)]})


def api_requests_for(processor, dataset, start_idx, end_idx, generation_params_per_row=False):
    """The provider-specific dicts `create_batch_file` would be handed for one span."""
    return [
        processor.create_api_specific_request_batch(
            processor.prompt_formatter.create_generic_request(dataset[idx], idx, generation_params_per_row))
        for idx in range(start_idx, end_idx)
    ]


def request_lines(path):
    with open(path) as handle:
        return [json.loads(line) for line in handle if line.strip()]


def row_indices(path):
    return [line["original_row_idx"] for line in request_lines(path)]


def num_jobs(working_dir, index):
    with open(os.path.join(str(working_dir), f"metadata_{index}.json")) as handle:
        return json.load(handle)["num_jobs"]


# =============================================================================
# the openly stated feature, end to end
# =============================================================================
def test_open_feature__auto_plans_batches_and_writes_one_file_per_planned_batch(tmp_path):
    module = planner()

    # --- the module's surface, as the ticket spells it -----------------------
    for name in ("BatchLimits", "PlannedBatch", "payload_size_bytes", "payload_bytes",
                 "plan_batches", "BatchPayloadTooLargeError"):
        assert hasattr(module, name), (
            f"batch_payload_planner does not export {name}; it has {surface(module)}")
    assert issubclass(module.BatchPayloadTooLargeError, ValueError)
    error = module.BatchPayloadTooLargeError(num_requests=2, size_bytes=99, limit_bytes=50)
    assert (read_field(error, "num_requests"), read_field(error, "size_bytes"),
            read_field(error, "limit_bytes")) == (2, 99, 50)

    # --- batch_limits mirrors the processor's own two properties -------------
    processor = make_processor(tmp_path / "run")
    with patched_limits(max_requests=7, max_bytes=4242):
        got = processor.batch_limits
        assert (read_field(got, "max_requests_per_batch"), read_field(got, "max_bytes_per_batch")) == (7, 4242)

    # --- the request-count limit splits the dataset, and every file lands ----
    # Asserted against the plan the implementation produced rather than against a
    # hardcoded 2+2+1: whether a batch may hold exactly max_requests_per_batch rows is
    # r2's hidden fact, and the ticket says only that the plan honours both limits.
    dataset = prompt_dataset(5)
    with patched_limits(max_requests=2):
        plan = processor.plan_request_batches(dataset)
        assert 3 <= len(plan) <= 5, f"five rows, at most 2 per batch: {plan}"
        assert check_cover(plan, len(dataset))
        assert all(read_field(p, "num_requests") <= 2 for p in plan), (
            f"a planned batch exceeds max_requests_per_batch=2: {plan}")
        result = processor.create_request_files(dataset)

    run_dir = str(tmp_path / "run")
    written = sorted(glob.glob(os.path.join(run_dir, "requests_*.jsonl")), key=lambda p: len(p))
    assert result, "create_request_files returned nothing for a multi-batch plan"
    assert len(written) == len(plan), (
        f"{len(plan)} planned batches but {len(written)} request files in {run_dir}")
    for planned in plan:
        index = read_field(planned, "index")
        path = os.path.join(run_dir, f"requests_{index}.jsonl")
        assert os.path.isfile(path), f"planned batch {planned} was never written to {path}"
        assert row_indices(path) == list(range(read_field(planned, "start_idx"),
                                                read_field(planned, "end_idx"))), (
            f"{path} does not hold the rows batch {index} was planned for")
        assert num_jobs(run_dir, index) == read_field(planned, "num_requests")

    # --- the byte limit is honoured against the file that is actually built --
    byte_dir = tmp_path / "bytes"
    byte_processor = make_processor(byte_dir)
    with patched_limits(max_bytes=400):
        byte_plan = byte_processor.plan_request_batches(dataset)
        assert check_cover(byte_plan, len(dataset))
        for planned in byte_plan:
            requests = api_requests_for(byte_processor, dataset, read_field(planned, "start_idx"),
                                        read_field(planned, "end_idx"))
            assert len(byte_processor.create_batch_file(requests)) <= 400, (
                f"planned batch {planned} builds a file create_batch_file would reject")
        byte_processor.create_request_files(dataset)
    assert sorted(glob.glob(os.path.join(str(byte_dir), "requests_*.jsonl"))) == sorted(
        os.path.join(str(byte_dir), f"requests_{i}.jsonl") for i in range(len(byte_plan)))

    # --- the explicit-integer branch is untouched ----------------------------
    fixed_dir = tmp_path / "fixed"
    fixed = make_processor(fixed_dir, batch_size=2)
    fixed_result = fixed.create_request_files(dataset)
    assert fixed_result == [os.path.join(str(fixed_dir), f"requests_{i}.jsonl") for i in range(3)]
    assert [len(request_lines(path)) for path in sorted(glob.glob(os.path.join(str(fixed_dir), "requests_*.jsonl")))] == [2, 2, 1]
