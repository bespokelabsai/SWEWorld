"""g1 — hidden requirement r2: how the pure planner cuts a sequence of sizes.

    rule              one forward pass in index order, greedy fill, contiguous ordered
                      exhaustive spans; no reordering, no bin packing, no smoothing of
                      the batch count
    scope             both limits are inclusive — a batch landing exactly on either one
                      is kept, and no headroom is subtracted
    exclusions        file accounting is `sum(sizes) + len(sizes) - 1`, and 0 for an
                      empty sequence: the `n-1` separators of `"\\n".join(...)`, never the
                      per-line trailing newline the request-file writer uses
    failure_behavior  a single row bigger than the byte limit raises
                      `SingleRequestTooLargeError` before any plan (or any file) exists
    observability     the `"auto"` branch returns one path per PlannedBatch, ordered by
                      PlannedBatch.index

`rule` and `scope` are deliberately written so that they do not also fail when the
accounting fact (`exclusions`) is wrong: `rule` uses a budget that yields 3+3+1 under any
of the three plausible accountings, and `scope` derives its budget from the
implementation's own `payload_bytes`.
"""
from __future__ import annotations

import glob
import os

import pytest
from datasets import Dataset

from harness import read_field

from test_open import (
    counts,
    limits_of,
    make_processor,
    patched_limits,
    planner,
    spans,
)


# =============================================================================
# rule — greedy forward fill, never rebalanced
# =============================================================================
def test_rule__greedy_forward_fill_leaves_the_last_batch_short(tmp_path):
    """Seven equal rows, a budget that holds three of them: 3+3+1, not an even 3+2+2.

    The budget is 35 rather than the tightest possible 32 on purpose. 3 rows fit and 4 do
    not under `sum(sizes)`, `sum(sizes) + n - 1` and `sum(sizes) + n` alike, so this test
    isolates "greedy, in order, never smoothed" from how the separator bytes are counted.
    """
    module = planner()
    plan = module.plan_batches([10] * 7, limits_of(module, 1000, 35))

    assert spans(plan) == [(0, 0, 3, 3), (1, 3, 6, 3), (2, 6, 7, 1)], (
        f"expected a greedy 3+3+1 cover of seven rows; got {plan}. "
        "3+2+2 is an even split, and anything non-contiguous is bin packing.")
    assert read_field(plan[0], "start_idx") == 0
    assert read_field(plan[-1], "end_idx") == 7
    for earlier, later in zip(plan, plan[1:]):
        assert read_field(earlier, "end_idx") == read_field(later, "start_idx")
        assert read_field(earlier, "index") + 1 == read_field(later, "index")

    # One big row then three small ones: greedy fills forward and closes early, so the
    # batches come out ragged (1 then 3). Cutting the dataset into equal-width shards -
    # the other way to respect the same budget - cannot produce that shape; it has to
    # fall back to 1+1+1+1 once 2+2 overflows. 55 bytes is comfortably clear of every
    # boundary under each of the three plausible accountings.
    ragged = module.plan_batches([50, 10, 10, 10], limits_of(module, 1000, 55))
    assert spans(ragged) == [(0, 0, 1, 1), (1, 1, 4, 3)], (
        f"expected a greedy 1+3 cover; got {ragged}")


# =============================================================================
# scope — both limits inclusive, no headroom
# =============================================================================
def test_scope__a_batch_landing_exactly_on_either_limit_is_kept(tmp_path):
    """Measured against the implementation's own accounting, so only inclusivity is judged.

    `exact` is whatever this implementation says three 10-byte rows cost. A batch of that
    size is admissible; one byte less of budget and the third row must move on. Reserving
    headroom (95% of the budget, or `max_requests_per_batch - 1`) fails both halves.
    """
    module = planner()
    exact = module.payload_bytes([10, 10, 10])

    on_the_limit = module.plan_batches([10] * 6, limits_of(module, 1000, exact))
    assert counts(on_the_limit) == [3, 3], (
        f"a batch whose payload is exactly the {exact}-byte limit must be kept; got {on_the_limit}")
    assert len(on_the_limit) == 2
    assert read_field(on_the_limit[0], "num_bytes") == exact

    one_byte_tighter = module.plan_batches([10] * 6, limits_of(module, 1000, exact - 1))
    assert read_field(one_byte_tighter[0], "num_requests") == 2, (
        f"with {exact - 1} bytes of budget the third row no longer fits; got {one_byte_tighter}")

    on_the_count = module.plan_batches([10] * 6, limits_of(module, 3, 10 ** 6))
    assert counts(on_the_count) == [3, 3], (
        f"max_requests_per_batch=3 must admit batches of exactly 3; got {on_the_count}")


# =============================================================================
# exclusions — n-1 separators, not one newline per line
# =============================================================================
def test_exclusions__file_accounting_counts_n_minus_one_separators(tmp_path):
    module = planner()

    assert module.payload_bytes([]) == 0
    assert module.payload_bytes([10]) == 10
    assert module.payload_bytes([10, 10, 10]) == 32, (
        f"three 10-byte requests join to 32 bytes, not {module.payload_bytes([10, 10, 10])} "
        "(30 ignores the separators, 33 is the writer's trailing-newline convention)")

    # Every PlannedBatch.num_bytes is payload_bytes of its rows. A 41-byte budget is
    # nowhere near a boundary under any of the three accountings, so this half turns on
    # the formula alone and not on whether the limits are inclusive (that is `scope`):
    # 3 rows cost 32 here, 30 under `sum(sizes)`, 33 under one newline per line, and the
    # fourth row (43 / 40 / 44) fits only under `sum(sizes)`.
    plan = module.plan_batches([10] * 7, limits_of(module, 1000, 41))
    assert read_field(plan[0], "num_requests") == 3, (
        f"a 41-byte budget holds three 10-byte requests joined by two newlines; got {plan[0]}")
    assert read_field(plan[0], "num_bytes") == 32, (
        f"that batch is 32 bytes on disk; the plan says {read_field(plan[0], 'num_bytes')}")

    empty = make_processor(tmp_path).create_batch_file([])
    assert empty == b"", f"create_batch_file([]) built {empty!r}"


# =============================================================================
# failure_behavior — an oversized row raises, before anything is planned or written
# =============================================================================
def test_failure_behavior__a_single_oversized_row_raises_before_any_plan(tmp_path):
    """Not a one-row batch, not a skipped row, not a problem deferred to submission."""
    module = planner()

    with pytest.raises(module.BatchPayloadTooLargeError) as caught:
        module.plan_batches([10, 500, 10], limits_of(module, 1000, 32))
    err = caught.value
    too_large = type(err)
    # A dedicated subclass of the batch-level error, exported from the planner module.
    # The class NAME is not asserted: the requirement fixes the shape, and an
    # implementation that chose another name has satisfied it equally.
    assert too_large is not module.BatchPayloadTooLargeError, (
        "an oversized single row should raise its own subclass of BatchPayloadTooLargeError, "
        "not the batch-level error itself")
    assert issubclass(too_large, module.BatchPayloadTooLargeError)
    assert isinstance(err, ValueError)
    assert getattr(module, too_large.__name__, None) is too_large, (
        f"{too_large.__name__} is not exported from batch_payload_planner")
    assert (read_field(err, "row_idx"), read_field(err, "size_bytes"),
            read_field(err, "limit_bytes"), read_field(err, "num_requests")) == (1, 500, 32, 1)

    # end to end: nothing is written, because planning finishes before writing starts
    processor = make_processor(tmp_path)
    big = Dataset.from_dict({"prompt": ["ok", "x" * 600, "ok"]})
    with patched_limits(max_bytes=400):
        with pytest.raises(module.BatchPayloadTooLargeError) as caught_e2e:
            processor.create_request_files(big)
    assert isinstance(caught_e2e.value, too_large), (
        f"create_request_files raised {type(caught_e2e.value).__name__} for a row that is "
        "larger than a whole batch")
    assert read_field(caught_e2e.value, "row_idx") == 1
    assert glob.glob(os.path.join(str(tmp_path), "requests_*.jsonl")) == [], (
        "request files were written before the oversized row was noticed")


# =============================================================================
# observability — every planned file comes back, in PlannedBatch.index order
# =============================================================================
def test_observability__auto_returns_one_path_per_batch_in_numeric_order(tmp_path):
    """Eleven batches: a stale single-element list gives 1, a sorted glob gives 10 before 2."""
    processor = make_processor(tmp_path)
    dataset = Dataset.from_dict({"prompt": [f"say {i}" for i in range(11)]})

    with patched_limits(max_requests=1, max_bytes=10 ** 9):
        result = processor.create_request_files(dataset)

    assert len(result) == 11, f"expected one path per planned batch, got {len(result)}: {result}"
    assert [os.path.basename(path) for path in result] == [f"requests_{i}.jsonl" for i in range(11)], (
        f"paths came back in the wrong order: {[os.path.basename(p) for p in result]}")
    assert os.path.basename(result[1]) == "requests_1.jsonl"
    assert os.path.basename(result[10]) == "requests_10.jsonl"
    for path in result:
        assert os.path.isfile(path), f"{path} was returned but never written"
    for i in range(11):
        assert os.path.isfile(os.path.join(str(tmp_path), f"metadata_{i}.json"))
