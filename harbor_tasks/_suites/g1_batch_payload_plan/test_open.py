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

import ast
import glob
import json
import os
import pathlib

import pytest
from datasets import Dataset

from harness import baseline_text, read_field, surface  # noqa: F401 - surface used below

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
# what the ticket keeps as it is
#
# instruction.md:69/:78 keep two signatures, :87-89 keep the explicit-integer
# branch's behaviour and :93-94 reuse the two limit properties and
# `acreate_request_file` as-is. None of it is a whole file, and the limit
# properties are PATCHED in every scenario below, so their real implementations
# never run here: the pristine copy is the only witness. `judge.py` makes the
# same comparisons on the graded path.
# =============================================================================
BASE_PROCESSOR = "request_processor/base_request_processor.py"
BATCH_PROCESSOR = "request_processor/batch/base_batch_request_processor.py"


def live_text(rel):
    import bespokelabs.curator

    return (pathlib.Path(bespokelabs.curator.__file__).parent / rel).read_text()


def find_def(source, name, classname=None):
    """The `def` the module BINDS, which is the last one of that name.

    Module-level classes only, and the last definition rather than the first:
    `judge.py` resolves it the same way and refuses a name defined twice
    outright, because a duplicate `def` with a pristine copy on top of a
    rewritten one, or a decoy class defined earlier, passed every one of these
    comparisons while the interpreter bound something else.
    """
    found = None
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef) or (classname and node.name != classname):
            continue
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == name:
                found = stmt
    return found


def signature(node, *, returns):
    """Parameter names, order, annotations and defaults — not source text."""
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    shape = [(a.arg, ast.dump(a.annotation) if a.annotation else None, ast.dump(d) if d else None) for a, d in zip(positional, defaults)]
    kwonly = [(a.arg, ast.dump(d) if d else None) for a, d in zip(args.kwonlyargs, args.kw_defaults)]
    return (shape, kwonly, args.vararg and args.vararg.arg, args.kwarg and args.kwarg.arg, ast.dump(node.returns) if returns and node.returns else None)


def explicit_arm(source):
    """The statements of the explicit-integer arm of `create_request_files`.

    The `else:` of `if batch_size == "auto"` — the local name, not
    `self.config.batch_size`, which is a different `if` in the same module.
    """
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) and node.test.left.id == "batch_size"):
            continue
        if node.orelse:
            return node.orelse
    return None


def strip_docstrings(node):
    for child in ast.walk(node):
        if isinstance(child, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = child.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                child.body = body[1:] or [ast.Pass()]
    return ast.dump(node)


def check_preservation_constraints():
    """Called from the one open-feature test: one fact, one test, as judge.py grades it."""
    pristine_base = baseline_text(BASE_PROCESSOR)
    pristine_batch = baseline_text(BATCH_PROCESSOR)
    if pristine_base is None or pristine_batch is None:
        pytest.skip("no pristine tree to diff against")

    # the two signatures; create_batch_file's return annotation is corrected to
    # `bytes` by the ticket itself, so it is the one thing allowed to move
    assert signature(find_def(live_text(BATCH_PROCESSOR), "create_batch_file", "BaseBatchRequestProcessor"), returns=False) == signature(
        find_def(pristine_batch, "create_batch_file", "BaseBatchRequestProcessor"), returns=False
    )
    assert signature(find_def(live_text(BASE_PROCESSOR), "create_request_files", "BaseRequestProcessor"), returns=True) == signature(
        find_def(pristine_base, "create_request_files", "BaseRequestProcessor"), returns=True
    )

    # reused as-is: acreate_request_file, and both limit properties
    assert strip_docstrings(find_def(live_text(BASE_PROCESSOR), "acreate_request_file", "BaseRequestProcessor")) == strip_docstrings(
        find_def(pristine_base, "acreate_request_file", "BaseRequestProcessor")
    )
    for rel in (BATCH_PROCESSOR, "request_processor/batch/openai_batch_request_processor.py"):
        for prop in ("max_requests_per_batch", "max_bytes_per_batch"):
            assert strip_docstrings(find_def(live_text(rel), prop)) == strip_docstrings(find_def(baseline_text(rel), prop)), f"{rel}:{prop} is not reused as-is"

    # :87-89 keeps the explicit-integer arm's behaviour EXACTLY, and the
    # reference solution obeys it by leaving the arm alone: its four statements —
    # `ceil(len(dataset) / batch_size)`, the two fixed-width name lists, and the
    # `create_all_request_files` whose comprehension keeps `if i in
    # incomplete_files` — are still the pristine ones, in the arm itself. That is
    # what `judge.py` reads too: it resolves the arm (the class the module binds,
    # the method that class binds, the `else` of that method's `batch_size ==
    # "auto"` test) and compares it in place. Its one added latitude is the
    # refactor the ticket allows — the same four statements lifted verbatim into
    # a helper the arm calls — which this reference does not use.
    live_arm = explicit_arm(live_text(BASE_PROCESSOR))
    assert live_arm is not None, "create_request_files has no explicit-integer arm"
    assert [strip_docstrings(stmt) for stmt in live_arm] == [strip_docstrings(stmt) for stmt in explicit_arm(pristine_base)], (
        "the explicit-integer arm is not the one the world shipped"
    )

    # section 3's deletion, and section 1's two frozen dataclasses
    base_live = live_text(BASE_PROCESSOR)
    assert find_def(base_live, "_get_optimal_batch_size") is None and "_get_optimal_batch_size" not in base_live
    assert "while True" not in base_live
    planner_src = pathlib.Path(planner().__file__).read_text()
    for name in ("BatchLimits", "PlannedBatch"):
        node = next(n for n in ast.walk(ast.parse(planner_src)) if isinstance(n, ast.ClassDef) and n.name == name)
        assert any(
            isinstance(d, ast.Call) and getattr(d.func, "id", getattr(d.func, "attr", "")) == "dataclass" and any(k.arg == "frozen" and k.value.value is True for k in d.keywords)
            for d in node.decorator_list
        ), f"{name} is not a @dataclass(frozen=True)"

    # no network, no clients, no sleeps in what the ticket adds
    imported = set()
    for node in ast.walk(ast.parse(planner_src)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    # aiofiles is deliberately NOT in this set: "no network, no clients, no
    # sleeps" is what instruction.md says, and banning file IO as well failed a
    # correct planner on a rule nobody stated. `time` went the same way — the
    # ticket bans sleeping, not the module sleep lives in; the sleep itself is
    # caught by the `"sleep" not in planner_src` line below.
    assert imported.isdisjoint({"asyncio", "socket", "requests", "aiohttp", "httpx", "urllib", "openai", "anthropic", "litellm"})
    assert "sleep" not in planner_src


# =============================================================================
# the openly stated feature, end to end
# =============================================================================
def test_open_feature__auto_plans_batches_and_writes_one_file_per_planned_batch(tmp_path):
    module = planner()

    # what the ticket keeps as it is, read off the pristine tree
    check_preservation_constraints()

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

    # --- and it refuses a batch over the byte limit with the new error -------
    over_limit = api_requests_for(processor, dataset, 0, 2)
    with patched_limits(max_requests=1000, max_bytes=50):
        with pytest.raises(module.BatchPayloadTooLargeError) as caught:
            processor.create_batch_file(over_limit)
    too_large = caught.value
    assert (read_field(too_large, "num_requests"), read_field(too_large, "size_bytes"), read_field(too_large, "limit_bytes")) == (2, 307, 50)

    # --- every row measured exactly once, in index order --------------------
    measured = make_processor(tmp_path / "measured")
    seen_rows = []
    original_build = measured.create_api_specific_request_batch
    measured.create_api_specific_request_batch = lambda request, *a, **k: (seen_rows.append(read_field(request, "original_row_idx")), original_build(request, *a, **k))[1]
    with patched_limits(max_requests=3, max_bytes=400):
        measured.plan_request_batches(dataset)
    assert seen_rows == [0, 1, 2, 3, 4], f"the rows were not measured once each, in order: {seen_rows}"

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
    # Worked example at batch_size=2 over 5 rows. The graded run draws the chunk
    # from a ten-wide band and sizes its own dataset from it (fixture_spec), so
    # the file and line counts it has to reproduce are not knowable in advance;
    # the rule being illustrated is the same one.
    fixed_dir = tmp_path / "fixed"
    fixed = make_processor(fixed_dir, batch_size=2)
    fixed_result = fixed.create_request_files(dataset)
    assert fixed_result == [os.path.join(str(fixed_dir), f"requests_{i}.jsonl") for i in range(3)]
    assert [len(request_lines(path)) for path in fixed_result] == [2, 2, 1]

    # ...exactly as it was: no planner call, and no resplit under a byte budget
    # no single row fits in (a planner call would have raised there)
    bytes_dir = tmp_path / "fixed_bytes"
    fixed_bytes = make_processor(bytes_dir, batch_size=2)
    planner_calls = []
    original_plan = fixed_bytes.plan_request_batches
    fixed_bytes.plan_request_batches = lambda *a, **k: (planner_calls.append(1), original_plan(*a, **k))[1]
    with patched_limits(max_requests=1, max_bytes=50):
        bytes_result = fixed_bytes.create_request_files(dataset)
    assert planner_calls == [], "the explicit-integer branch called the planner"
    assert [len(request_lines(path)) for path in bytes_result] == [2, 2, 1]

    # ...and incomplete_files still decides which files are rewritten
    cache_dir = tmp_path / "fixed_cache"
    os.makedirs(cache_dir)
    with open(os.path.join(cache_dir, "requests_0.jsonl"), "w") as handle:
        handle.write("stale\nstale\n")
    with open(os.path.join(cache_dir, "metadata_0.json"), "w") as handle:
        json.dump({"num_jobs": 2}, handle)
    cached = make_processor(cache_dir, batch_size=2)
    cached.create_request_files(prompt_dataset(3))
    assert open(os.path.join(cache_dir, "requests_0.jsonl")).read() == "stale\nstale\n"
    assert row_indices(os.path.join(cache_dir, "requests_1.jsonl")) == [2]
