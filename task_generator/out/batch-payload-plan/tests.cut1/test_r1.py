"""g1 — hidden requirement r1: the planner measures the payload that gets submitted.

    rule              a row's planned size is the byte length of the provider-specific
                      request dict, not of the GenericRequest written to requests_*.jsonl
    scope             `generation_params_per_row` comes from `dataset.column_names`, once
                      per pass, and is passed into `create_generic_request`
    exclusions        `payload_size_bytes(d) == len(json.dumps(d).encode())` — stock
                      `json.dumps` arguments, byte-identical to `create_batch_file`
    failure_behavior  a non-serialisable value propagates `TypeError`, it is not coerced
                      through a `default=str` fallback nor converted to another error
    observability     `create_api_specific_request_batch` runs exactly once per row per
                      planning pass, in index order

Each test is kept to its own fact. `scope` in particular derives its byte limit from the
implementation's OWN `payload_bytes` and `measure_request_payload`, so an agent who picked
a different ruler or a different separator convention is judged here only on whether it
consulted the dataset's columns.
"""
from __future__ import annotations

import json
import os

import pytest
from datasets import Dataset
from unittest.mock import Mock

from harness import read_field

from test_open import (
    api_requests_for,
    counts,
    make_processor,
    patched_limits,
    planner,
    prompt_dataset,
    request_lines,
    spans,
)

GEN_PARAMS = '{"temperature": 0.9}'


def genparams_dataset(n):
    return Dataset.from_dict({"prompt": [f"say {i}" for i in range(n)],
                              "generation_params": [GEN_PARAMS] * n})


# =============================================================================
# rule — the ruler is the provider-specific request, not the generic one
# =============================================================================
def test_rule__a_row_is_sized_as_the_api_specific_request_it_becomes(tmp_path):
    """153 bytes: the OpenAI envelope. The generic request is 217, its JSONL line 218."""
    processor = make_processor(tmp_path)
    request = processor.prompt_formatter.create_generic_request({"prompt": "say 0"}, 0, False)

    generic_bytes = len(json.dumps(request.model_dump(), default=str).encode())
    assert generic_bytes == 217, "fixture drift: the generic request is no longer 217 bytes"

    measured = processor.measure_request_payload(request)
    assert measured == 153, (
        "measure_request_payload should size the API-specific dict "
        '{"custom_id": "0", "method": "POST", "url": "/v1/chat/completions", "body": {...}} '
        f"at 153 bytes; it returned {measured} "
        f"(the generic request is {generic_bytes}, its JSONL line {generic_bytes + 1})")

    # and the plan is denominated in the very bytes create_batch_file will build
    dataset = prompt_dataset(5)
    plan = processor.plan_request_batches(dataset)
    assert len(plan) == 1, f"5 tiny rows fit one OpenAI batch; got {plan}"
    built = processor.create_batch_file(api_requests_for(processor, dataset, 0, 5))
    assert read_field(plan[0], "num_bytes") == len(built), (
        f"plan[0].num_bytes={read_field(plan[0], 'num_bytes')} but create_batch_file "
        f"builds {len(built)} bytes for the same five rows: the planner's ruler and the "
        "submission-time check have diverged")


# =============================================================================
# scope — the row-level generation_params column is part of what is measured
# =============================================================================
def test_scope__row_level_generation_params_are_measured(tmp_path):
    """The planner must ask the dataset, not hardcode the flag either way.

    The byte limit is derived from the implementation's own numbers — one byte more than
    three rows measured WITHOUT row-level params — so the assertion turns purely on which
    flag reached `create_generic_request`:

      * consulting `dataset.column_names` measures the larger request and plans 2+2+2;
      * hardcoding `False` (or `bool(prompt_formatter.generation_params)`, empty here)
        measures the smaller one and plans 3+3;
      * hardcoding `True` raises KeyError('generation_params') on the plain dataset.
    """
    module = planner()
    processor = make_processor(tmp_path)

    row = {"prompt": "say 0", "generation_params": GEN_PARAMS}
    with_params = processor.measure_request_payload(
        processor.prompt_formatter.create_generic_request(dict(row), 0, True))
    without_params = processor.measure_request_payload(
        processor.prompt_formatter.create_generic_request(dict(row), 0, False))
    assert with_params > without_params, (
        f"fixture drift: {GEN_PARAMS} did not enlarge the request ({with_params} vs {without_params})")

    limit = module.payload_bytes([without_params] * 3) + 1

    with patched_limits(max_requests=1_000_000, max_bytes=limit):
        plan = processor.plan_request_batches(genparams_dataset(6))
        assert spans(plan) == [(0, 0, 2, 2), (1, 2, 4, 2), (2, 4, 6, 2)], (
            f"with a {limit}-byte budget, six rows carrying {GEN_PARAMS} plan 2+2+2; got {plan}. "
            "A plan of 3+3 means the row-level generation_params never reached the measured request.")
        processor.create_request_files(genparams_dataset(6))
        # read by index rather than through the return value: what the returned list
        # contains is r2's fact, not this one
        written = [os.path.join(str(tmp_path), f"requests_{i}.jsonl") for i in range(3)]
        assert [len(request_lines(path)) for path in written] == [2, 2, 2]

        plain = make_processor(tmp_path / "plain")
        plain_plan = plain.plan_request_batches(prompt_dataset(6))
        assert counts(plain_plan) == [3, 3], (
            "a dataset with no generation_params column must plan off the smaller request; "
            f"got {plain_plan}")


# =============================================================================
# exclusions — stock json.dumps, byte-identical to create_batch_file
# =============================================================================
def test_exclusions__payload_size_bytes_is_stock_json_dumps(tmp_path):
    """`ensure_ascii=True` and `", "` / `": "`: 157 bytes, not 153 and not 144."""
    module = planner()
    processor = make_processor(tmp_path)
    request = processor.prompt_formatter.create_generic_request({"prompt": "café"}, 0, False)
    api_request = processor.create_api_specific_request_batch(request)

    measured = module.payload_size_bytes(api_request)
    assert measured == 157, (
        f"payload_size_bytes returned {measured}; stock json.dumps escapes 'café' to 157 bytes "
        f"(ensure_ascii=False gives {len(json.dumps(api_request, ensure_ascii=False).encode())}, "
        f"compact separators give {len(json.dumps(api_request, separators=(',', ':')).encode())})")
    assert measured == len(json.dumps(api_request).encode())
    assert measured == len(processor.create_batch_file([api_request])), (
        "the planner's ruler and create_batch_file's own serialization must agree byte for byte")


# =============================================================================
# failure_behavior — a non-serialisable value is a TypeError, not a coerced string
# =============================================================================
def test_failure_behavior__a_non_serialisable_payload_raises_typeerror(tmp_path):
    """`default=str` would swallow this and return a number that means nothing."""
    module = planner()
    with pytest.raises(TypeError):
        module.payload_size_bytes({"a": {1, 2}})


# =============================================================================
# observability — one measurement per row per pass, in index order
# =============================================================================
def test_observability__each_row_is_measured_exactly_once_in_order(tmp_path):
    """One pass over the rows, in index order — no window re-measures a boundary row twice.

    Counted on `create_generic_request` as well as on `create_api_specific_request_batch`,
    because the two say different things: how many times a row is turned into a request is
    this fact, while which of the two dicts gets weighed is r1's `rule`. A planner that
    measured the wrong dict but measured it once still passes here.

    Today's windowed structure — `dataset.select(range(start, start + max_requests))` per
    batch — measures rows 0-2, 2-4 and 4-5, so 8 requests are built for 6 rows; a
    measure-then-log second pass builds 12.
    """
    processor = make_processor(tmp_path)
    formatter_spy = Mock(side_effect=processor.prompt_formatter.create_generic_request)
    processor.prompt_formatter.create_generic_request = formatter_spy
    api_spy = Mock(side_effect=processor.create_api_specific_request_batch)
    processor.create_api_specific_request_batch = api_spy

    dataset = prompt_dataset(6)
    with patched_limits(max_requests=6, max_bytes=400):
        processor.plan_request_batches(dataset)

    measured_order = [call.args[1] if len(call.args) > 1 else call.kwargs["idx"]
                      for call in formatter_spy.call_args_list]
    assert measured_order == [0, 1, 2, 3, 4, 5], (
        f"one planning pass built {len(measured_order)} requests for 6 rows, in this row "
        f"order: {measured_order}. Each row must be measured exactly once, in index order.")
    assert api_spy.call_count in (0, 6), (
        f"create_api_specific_request_batch ran {api_spy.call_count} times for 6 rows")

    # and the whole "auto" run plans exactly once: no second measuring pass in the writer
    whole_run = make_processor(tmp_path / "run")
    run_spy = Mock(side_effect=whole_run.create_api_specific_request_batch)
    whole_run.create_api_specific_request_batch = run_spy
    with patched_limits(max_requests=6, max_bytes=400):
        whole_run.create_request_files(prompt_dataset(6))
    assert run_spy.call_count in (0, 6), (
        f"create_api_specific_request_batch ran {run_spy.call_count} times across a whole "
        "create_request_files call; six rows are measured once each, and once only")
