"""g5 — hidden requirement r1: which line wins when a request has several.

    rule          the winner is the record with the best status —
                  SUCCEEDED > EMPTY > UNPARSEABLE > FAILED — never simply the
                  most recently written line
    scope         the fold is over every `responses_N.jsonl` under one working
                  directory, not per file, resubmissions included
    exclusions    a later FAILED retry does not shadow an earlier SUCCEEDED line
    observability the literal fixture the requirement writes out

The four use disjoint status pairs so they are four measurements rather than one
repeated: `rule` walks the precedence chain with pairs that never put SUCCEEDED
against FAILED, `exclusions` owns exactly that pair, `scope` duplicates rows of
IDENTICAL status so its answer cannot depend on the precedence direction, and
only `observability` reads the tie-break between two equally good lines.
"""
from __future__ import annotations

import os

from harness import read_field

from test_open import counts, empty, failed, row_indices, succeeded, sym, unparseable, write_requests, write_responses


def fresh_dir(tmp_path) -> str:
    """An empty working directory of this test's own."""
    working_dir = str(tmp_path / "run")
    os.makedirs(working_dir)
    return working_dir


def statuses(ledger):
    """The status of every winning record, ascending `original_row_idx`."""
    classify_record = sym("classify_record")
    return [classify_record(record) for record in ledger.winning_records()]


# =============================================================================
# rule — best status wins, and recency does not
# =============================================================================
def test_rule__the_best_status_wins_each_row_whether_it_was_written_first_or_last(tmp_path):
    """Four rows, each written twice, walking the precedence chain both ways."""
    LedgerStatus = sym("LedgerStatus")
    ResponseLedger = sym("ResponseLedger")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [0, 1, 2, 3])
    # Rows 0 and 3 are better on their FIRST line, rows 1 and 2 on their SECOND:
    # last-writer-wins gets 0 and 3 wrong, first-writer-wins gets 1 and 2 wrong,
    # and no pair here puts SUCCEEDED against FAILED — that is `exclusions`.
    write_responses(
        working_dir,
        0,
        [
            empty(0),
            failed(1),
            empty(2),
            unparseable(3),
            unparseable(0),
            unparseable(1),
            succeeded(2, [{"answer": "c2"}]),
            failed(3),
        ],
    )

    ledger = ResponseLedger.load(working_dir)
    assert row_indices(ledger.winning_records()) == [0, 1, 2, 3], "one winning record per row, not one per line"
    assert statuses(ledger) == [
        LedgerStatus.EMPTY,  # empty beats the unparseable written after it
        LedgerStatus.UNPARSEABLE,  # unparseable beats the failure written before it
        LedgerStatus.SUCCEEDED,  # succeeded beats the empty written before it
        LedgerStatus.UNPARSEABLE,  # unparseable beats the failure written after it
    ]
    assert counts(ledger.tally(), "n_recorded", "n_duplicate_lines") == [4, 4]


# =============================================================================
# scope — the fold is over the whole working directory
# =============================================================================
def test_scope__duplicate_lines_are_folded_across_response_files_not_within_one(tmp_path):
    """A resubmission lands in a later responses file and still folds to one record.

    Every duplicated pair here has the SAME status, so the answer is independent
    of which line precedence would prefer: only whether the fold crosses files.
    """
    ResponseLedger = sym("ResponseLedger")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [5, 6])
    write_requests(working_dir, 1, [7, 8])
    write_responses(working_dir, 0, [succeeded(5), succeeded(6)])
    # responses_1 carries its own two rows plus a later resubmission of 5 and 6.
    write_responses(working_dir, 1, [succeeded(7), succeeded(8), succeeded(5), succeeded(6)])

    ledger = ResponseLedger.load(working_dir)
    assert row_indices(ledger.winning_records()) == [5, 6, 7, 8], "six lines, four requests, four winning records"
    assert counts(ledger.tally(), "n_requests", "n_recorded", "n_succeeded", "n_duplicate_lines", "n_missing") == [4, 4, 4, 2, 0]
    assert ledger.unresolved_row_indices() == []


# =============================================================================
# exclusions — a later failure never shadows an earlier success
# =============================================================================
def test_exclusions__a_failed_retry_written_after_a_success_does_not_shadow_it(tmp_path):
    """The success is not the last line in the append log, and still wins."""
    LedgerStatus = sym("LedgerStatus")
    ResponseLedger = sym("ResponseLedger")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [3])
    write_responses(working_dir, 0, [succeeded(3, [{"answer": "early"}]), failed(3, ["RuntimeError: retry died"])])

    ledger = ResponseLedger.load(working_dir)
    records = ledger.winning_records()
    assert len(records) == 1
    assert sym("classify_record")(records[0]) is LedgerStatus.SUCCEEDED
    assert read_field(records[0], "parsed_response_message") == [{"answer": "early"}]

    tally = ledger.tally()
    assert counts(tally, "n_succeeded", "n_failed", "n_duplicate_lines") == [1, 0, 1]
    assert tuple(read_field(tally, "error_sample")) == (), "the shadowed failure contributes no error sample"
    assert ledger.unresolved_row_indices() == [], "a request with a durable success is resolved"


# =============================================================================
# observability — the literal fixture
# =============================================================================
def test_observability__status_beats_recency_and_equal_statuses_break_the_tie_by_position(tmp_path):
    """idx 7 written FAILED then SUCCEEDED; idx 5 written SUCCEEDED twice."""
    LedgerStatus = sym("LedgerStatus")
    ResponseLedger = sym("ResponseLedger")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [5, 7])
    write_responses(
        working_dir,
        0,
        [
            failed(7, ["Timeout(x3)"]),
            succeeded(7, [{"answer": "late"}]),
            succeeded(5, [{"answer": "first"}]),
            succeeded(5, [{"answer": "second"}]),
        ],
    )

    ledger = ResponseLedger.load(working_dir)
    records = ledger.winning_records()
    assert row_indices(records) == [5, 7]
    assert [read_field(r, "parsed_response_message")[0]["answer"] for r in records] == ["first", "late"]
    assert [sym("classify_record")(r) for r in records] == [LedgerStatus.SUCCEEDED, LedgerStatus.SUCCEEDED]
    assert counts(ledger.tally(), "n_duplicate_lines", "n_succeeded") == [2, 2]
