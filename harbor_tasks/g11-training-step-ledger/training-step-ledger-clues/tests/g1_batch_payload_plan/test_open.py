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
        # `.get` rather than `[...]`: the `dataset is None` path formats an empty dict.
        prompt_func=lambda row: row.get("prompt", "say 0"),
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
            prop = stack.enter_context(patch.object(OpenAIBatchRequestProcessor, "max_requests_per_batch", new_callable=PropertyMock))
            prop.return_value = max_requests
        if max_bytes is not None:
            prop = stack.enter_context(patch.object(OpenAIBatchRequestProcessor, "max_bytes_per_batch", new_callable=PropertyMock))
            prop.return_value = max_bytes
        yield


def planner():
    """The new module, or a failure that says so in one line."""
    try:
        from bespokelabs.curator.request_processor import batch_payload_planner
    except ImportError as exc:  # pragma: no cover - the pristine tree
        pytest.fail("bespokelabs.curator.request_processor.batch_payload_planner does not import, " f"so there is no planner to grade: {exc}")
    return batch_payload_planner


def limits_of(module, max_requests, max_bytes, **extra):
    return module.BatchLimits(max_requests_per_batch=max_requests, max_bytes_per_batch=max_bytes, **extra)


def tuples(plan):
    """(index, start_idx, end_idx, num_requests, num_bytes) per planned batch."""
    return [
        (
            read_field(p, "index"),
            read_field(p, "start_idx"),
            read_field(p, "end_idx"),
            read_field(p, "num_requests"),
            read_field(p, "num_bytes"),
        )
        for p in plan
    ]


def spans(plan):
    """(index, start_idx, end_idx, num_requests) per batch — the shape, not the byte count."""
    return [t[:4] for t in tuples(plan)]


def counts(plan):
    return [read_field(p, "num_requests") for p in plan]


def check_cover(plan, n_rows):
    """The plan is a contiguous, ordered, exhaustive cover of the dataset."""
    assert plan, "the plan is empty"
    assert read_field(plan[0], "start_idx") == 0, f"the plan does not start at row 0: {plan}"
    assert read_field(plan[-1], "end_idx") == n_rows, f"the plan does not reach row {n_rows}: {plan}"
    for i, planned in enumerate(plan):
        assert read_field(planned, "index") == i, f"planned batches are not indexed 0..n-1: {plan}"
        assert read_field(planned, "num_requests") == (read_field(planned, "end_idx") - read_field(planned, "start_idx")), f"bad span: {planned}"
    for earlier, later in zip(plan, plan[1:]):
        assert read_field(earlier, "end_idx") == read_field(later, "start_idx"), f"planned batches are not a contiguous cover: {plan}"
    return True


def prompt_dataset(n, prefix="say "):
    return Dataset.from_dict({"prompt": [f"{prefix}{i}" for i in range(n)]})


GEN_PARAMS = '{"temperature": 0.9}'


def genparams_dataset(n):
    return Dataset.from_dict({"prompt": [f"say {i}" for i in range(n)], "generation_params": [GEN_PARAMS] * n})


def api_requests_for(processor, dataset, start_idx, end_idx, generation_params_per_row=False):
    """The provider-specific dicts `create_batch_file` would be handed for one span."""
    return [
        processor.create_api_specific_request_batch(processor.prompt_formatter.create_generic_request(dataset[idx], idx, generation_params_per_row))
        for idx in range(start_idx, end_idx)
    ]


def request_lines(path):
    with open(path) as handle:
        return [json.loads(line) for line in handle if line.strip()]


def row_indices(path):
    return [line["original_row_idx"] for line in request_lines(path)]


def metadata_of(working_dir, index):
    with open(os.path.join(str(working_dir), f"metadata_{index}.json")) as handle:
        return json.load(handle)


def basenames(paths):
    return [os.path.basename(p) for p in paths]


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
