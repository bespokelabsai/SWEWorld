"""g1 — the answer-free scenario helpers the worker (probe.py) drives curator with.

This module holds ONLY the curator imports, the processor/dataset factories, the
limit-patching context and the log/metadata readers the probe needs to drive
curator; it contains NO expected-output value. That is load-bearing: `run_split`
copies this file into the worker's jail, so it is inside the process that runs
agent code. If any reward-bearing expected value ever appeared here, the worker
could read it and forge a passing `observations.json`. The answers — the
`plan_id` sha256 digests, the `PLAN_FORMAT_VERSION`, the `PLAN_FILE_NAME`
string, the 512 fan-out cap, the 767/307/153/347/217 byte counts, the exact
sidecar document and directory listings, and the error types/attributes — live
only in `judge.py`, which the worker cannot read.

The INPUTS themselves are no longer written down here. `fixture_spec.derive`
re-draws them from the seed root picks per run — prompts, row counts, limits, the
bytes a pre-populated directory holds — because a fixed fixture makes every
expected value the same every run, and g1's are published in the world the agent
reads. The helpers below therefore take their inputs as arguments; the defaults
are a readable example of the shape each one expects, never a graded value.

`MODEL` stays a literal: it is the model the processor is built for, and the
judge never grades a value computed from it. Row sizes are deliberately NOT
computable from anything in this file — see `fixture_spec`'s header.

Every scenario the probe runs is built out of these helpers and nothing else, so
there is one definition of each curator call and no second copy to drift from.
"""
from __future__ import annotations

import contextlib
import json
import os
import tempfile

from datasets import Dataset
from unittest.mock import PropertyMock, patch

from harness import read_field  # noqa: F401 - re-exported: the helpers below take either shape

from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.request_processor.batch.openai_batch_request_processor import OpenAIBatchRequestProcessor
from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

import pytest

# ---- inputs the fixtures feed --------------------------------------------
MODEL = "gpt-4o-mini"
# Shape examples only. The graded run overrides every one of them from
# `fixture_spec.derive(seed)`; see this module's header.
GEN_PARAMS = '{"temperature": 0.9}'
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
    output of the feature, so it is safe in the jail. The probe records the
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


def genparams_dataset(n, prefix="say ", params=GEN_PARAMS):
    return Dataset.from_dict({"prompt": [f"{prefix}{i}" for i in range(n)], "generation_params": [params] * n})


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
_ARTIFACTS: str | None = None


def set_artifacts_root(path) -> None:
    """Run the scenarios somewhere root can read them afterwards.

    The judge grades several facts on what a working directory actually holds —
    that the sweep ran, that a failed run left the place alone — and it must read
    that directory itself. Asking the worker "was the directory untouched?" is
    asking the process that runs agent code for a verdict, and `true` is a
    one-line answer to it.
    """
    global _ARTIFACTS
    _ARTIFACTS = str(path)


def make_tmp_dir(name=None):
    """A fresh empty working directory, standing in for the `tmp_path` fixture.

    Named rather than random when a root is set, so the judge can find the
    directory a given scenario ran in without the worker telling it where to
    look. Falls back to `mkdtemp` for the pytest reference, which has no root.
    """
    if _ARTIFACTS is None or name is None:
        return tempfile.mkdtemp(prefix="g1-")
    path = os.path.join(_ARTIFACTS, name)
    os.makedirs(path, exist_ok=True)
    # The judge reads these as root; the agent's own uid never sees them.
    os.chmod(path, 0o755)
    return path


# ---------------------------------------------------------------------------
# r1 — the sidecar
# ---------------------------------------------------------------------------
def auto_run(dataset, *, max_requests=3, max_bytes=400, name=None):
    """An `"auto"` run in its own fresh working dir.

    Returns (processor, plan, working_dir, limits) over a `make_tmp_dir()`.
    `name` puts that directory where the judge can read it afterwards.
    """
    working_dir = make_tmp_dir(name)
    processor = make_processor(working_dir)
    with patched_limits(max_requests=max_requests, max_bytes=max_bytes):
        plan = processor.plan_request_batches(dataset)
        processor.create_request_files(dataset)
        # `batch_limits` is the OPEN feature's; r1.exclusions calls this helper
        # and throws the limits away, and should not fail on a missing attribute
        limits = getattr(processor, "batch_limits", None)
    return processor, plan, working_dir, limits


# ---------------------------------------------------------------------------
# r2 — the sweep
# ---------------------------------------------------------------------------
def prepopulate(working_dir, *, n=6, extra=None, stale_request=STALE_REQUEST, stale_metadata=STALE_METADATA):
    """A working dir left behind by an earlier, differently-limited `"auto"` run."""
    os.makedirs(working_dir, exist_ok=True)
    for i in range(n):
        with open(os.path.join(working_dir, f"requests_{i}.jsonl"), "w") as handle:
            handle.write(stale_request)
        # `{}` and not `{"num_jobs": 1}`: a metadata file the cache check cannot read is
        # what makes curator regenerate rather than return the stale files as a cache hit.
        with open(os.path.join(working_dir, f"metadata_{i}.json"), "w") as handle:
            handle.write(stale_metadata)
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


def big_dataset(rows=3, big_at=1, big_len=600, prefix="say "):
    """One row is larger on its own than the byte budget, so planning must raise."""
    prompts = [f"{prefix}{i}" for i in range(rows)]
    prompts[big_at] = "x" * big_len
    return Dataset.from_dict({"prompt": prompts})


def sweep_run(working_dir, dataset, *, n, max_requests, max_bytes, extra=None,
              stale_request=STALE_REQUEST, stale_metadata=STALE_METADATA):
    """Pre-populate a directory, then run a clean `"auto"` run over it.

    Returns the directory. Whether the stale tail is gone is the JUDGE's reading
    of that directory, not a boolean this side reports — an earlier version
    returned `True` here and passing the fact took exactly that one word.
    """
    prepopulate(working_dir, n=n, extra=extra,
                stale_request=stale_request, stale_metadata=stale_metadata)
    processor = make_processor(working_dir)
    with patched_limits(max_requests=max_requests, max_bytes=max_bytes):
        processor.create_request_files(dataset)
    return working_dir
