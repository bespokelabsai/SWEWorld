"""g1 — answer-free scenario helpers/inputs shared by the worker (probe.py) and
the human reference (test_open.py).

This module holds ONLY the curator imports, the processor/dataset factories, the
limit-patching context and the log/metadata readers the probe needs to drive
curator; it contains NO expected-output value. That is load-bearing: `run_split`
copies this file into the worker's jail, so it is inside the process that runs
agent code. If any reward-bearing expected value ever appeared here, the worker
could read it and forge a passing `observations.json`. The answers — the
`plan_id` sha256 digests, the `PLAN_FORMAT_VERSION`, the `PLAN_FILE_NAME`
string, the 512 fan-out cap, the 767/307/153/347/217 byte counts, the exact
sidecar document and directory listings, and the error types/attributes — live
only in `judge.py` (and, for humans, in `test_open`/`test_r1`/`test_r2`), which
the worker cannot read.

The names here that coincide with a fact (`MODEL`, `GEN_PARAMS`, `STALE_REQUEST`,
`STALE_METADATA`) are INPUTS: the model the processor is built for, the row-level
generation params fed into a dataset, the stale bytes a pre-populated working dir
holds. They must be the literals the reference uses or the scenarios do not
reproduce; the judge holds its own copies for the equality checks it grades, so a
worker reading them here gains nothing it does not still have to make curator
actually produce.

`test_open.py` imports these names so there is a single definition of each helper
— the probe cannot drift from the reference. `test_r1`/`test_r2` keep their own
local copies of the r1/r2-specific helpers (auto_run, plan_path, prepopulate, …)
and are left unchanged; the copies below are the probe's, and they reproduce the
same curator calls.
"""
from __future__ import annotations

import contextlib
import json
import os
import tempfile

from datasets import Dataset
from unittest.mock import PropertyMock, patch

from harness import read_field  # noqa: F401 - re-exported for test_open

from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.request_processor.batch.openai_batch_request_processor import OpenAIBatchRequestProcessor
from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

import pytest

# ---- inputs the fixtures feed --------------------------------------------
MODEL = "gpt-4o-mini"
# row-level generation params fed into a dataset; an INPUT, not an answer.
GEN_PARAMS = '{"temperature": 0.9}'
# the bytes a working dir left behind by an earlier run holds; INPUTS the
# probe plants, so a run that leaves them untouched is graded on that.
STALE_REQUEST = "stale\n"
STALE_METADATA = "{}\n"


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
    """The plan is a contiguous, ordered, exhaustive cover of the dataset.

    Pure structure over `index/start_idx/end_idx/num_requests` — no expected
    output of the feature, so it lives here for test_open. The probe records the
    plan's tuples and judge.py runs the same structural check over them.
    """
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


# ---------------------------------------------------------------------------
# working directories, standing in for the pytest tmp_path fixture
# ---------------------------------------------------------------------------
def make_tmp_dir():
    """A fresh empty working directory, standing in for the `tmp_path` fixture."""
    return tempfile.mkdtemp(prefix="g1-")


# ---------------------------------------------------------------------------
# r1 — the sidecar (probe copies of test_r1's local helpers)
# ---------------------------------------------------------------------------
def plan_path(module, working_dir):
    """Where the sidecar lands, by the module's OWN name for it.

    The implementation's `PLAN_FILE_NAME` is used to locate the file — the
    literal "batch_plan.json" is r1's ANSWER and stays in the judge. A module
    that never exported the constant already fails r1's rule; here that surfaces
    as a probe error for the node rather than a wrong location.
    """
    return os.path.join(str(working_dir), module.PLAN_FILE_NAME)


def load_plan_file(module, working_dir):
    path = plan_path(module, working_dir)
    if not os.path.isfile(path):
        raise AssertionError(f'the "auto" branch wrote no plan sidecar; {working_dir} holds {sorted(os.listdir(working_dir))}')
    with open(path) as handle:
        return json.load(handle)


def auto_run(dataset, *, max_requests=3, max_bytes=400):
    """A 5-row-style `"auto"` run in its own fresh working dir.

    Returns (processor, plan, working_dir, limits) — the same tuple test_r1's
    local `auto_run` returns, over a `make_tmp_dir()` instead of the fixture.
    """
    working_dir = make_tmp_dir()
    processor = make_processor(working_dir)
    with patched_limits(max_requests=max_requests, max_bytes=max_bytes):
        plan = processor.plan_request_batches(dataset)
        processor.create_request_files(dataset)
        limits = processor.batch_limits
    return processor, plan, working_dir, limits


# ---------------------------------------------------------------------------
# r2 — the sweep (probe copies of test_r2's local helpers)
# ---------------------------------------------------------------------------
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

    Whatever a run records about its plan is r1's fact and is filtered out here.
    """
    return sorted(name for name in os.listdir(working_dir) if name in keep or name.startswith("requests_") or name.startswith("metadata_"))


def big_dataset():
    """Row 1 is larger on its own than the 400-byte budget, so planning must raise."""
    return Dataset.from_dict({"prompt": ["ok", "x" * 600, "ok"]})


def swept():
    """Run a clean `"auto"` run over a pre-populated dir; True when the stale tail is gone."""
    working_dir = prepopulate(make_tmp_dir())
    processor = make_processor(working_dir)
    with patched_limits(max_requests=3, max_bytes=400):
        processor.create_request_files(prompt_dataset(5))
    return not os.path.exists(os.path.join(working_dir, "requests_5.jsonl"))
