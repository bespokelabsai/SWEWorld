"""g5 — hidden requirement r2: resuming reads the file and never rewrites it.

    rule          `read_resume_state`, and `validate_existing_response_file`
                  built on it, leave the response file byte-identical — no temp
                  file, no truncation — and return the two named index sets
    scope         one response file at a time, with the ledger's own within-file
                  duplicate folding, before any new request is issued
    exclusions    EMPTY joins SUCCEEDED in `completed_row_indices`; UNPARSEABLE
                  joins FAILED in `retryable_row_indices`
    observability the literal fixture the requirement writes out

The read-only half is a preservation constraint — an untouched checkout that
never learned to resume this way would satisfy "does not write a temp file" by
having no `.temp` left after `os.replace` — so `rule` is guarded with
`require_feature` and asserts on the bytes, which the shipped rewrite does change.
`rule` sees only SUCCEEDED and FAILED, leaving the EMPTY/UNPARSEABLE policy to
`exclusions`; `scope` uses one duplicated pair of equal length so its row count
cannot depend on which duplicate wins.
"""
from __future__ import annotations

import hashlib
import os

from harness import read_field, require_feature

from test_open import empty, failed, ledger_is_implemented, succeeded, sym, unparseable, write_requests, write_responses


def fresh_dir(tmp_path) -> str:
    """An empty working directory of this test's own."""
    working_dir = str(tmp_path / "run")
    os.makedirs(working_dir)
    return working_dir


def digest(path) -> tuple:
    """The bytes of a file, as a hash and a line count."""
    body = open(path, "rb").read()
    return hashlib.sha256(body).hexdigest(), body.count(b"\n"), len(body)


def sets_of(state) -> tuple:
    """The two index sets and the row count, by the names the requirement fixes."""
    return (
        set(read_field(state, "completed_row_indices")),
        set(read_field(state, "retryable_row_indices")),
        read_field(state, "n_dataset_rows"),
    )


def make_processor(working_dir):
    """A concrete `BaseRequestProcessor` — the caller that resumes a run.

    The abstract methods are the three the class declares; nothing here touches a
    provider, and `validate_existing_response_file` is handed the path directly.
    """
    from bespokelabs.curator.request_processor.base_request_processor import BaseRequestProcessor
    from bespokelabs.curator.request_processor.config import RequestProcessorConfig

    class _Processor(BaseRequestProcessor):
        @property
        def backend(self):
            return "test"

        def validate_config(self):
            return None

        def requests_to_responses(self, generic_request_files):
            raise NotImplementedError

    processor = _Processor(RequestProcessorConfig(model="gpt-4o-mini"))
    processor.working_dir = working_dir
    return processor


# =============================================================================
# rule — the file is read, not rewritten
# =============================================================================
def test_rule__resuming_leaves_the_response_file_byte_identical_and_names_its_two_sets(tmp_path):
    """`validate_existing_response_file` returns a resume view without touching the log."""
    require_feature(ledger_is_implemented(), "the ledger's read-only resume state (read_resume_state / ResumeState)")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [0, 1, 2])
    # The middle line is a durable failure: the shipped resume path strips it.
    response_file = write_responses(
        working_dir,
        0,
        [succeeded(0, [{"answer": "A"}]), failed(1, ["TimeoutError: boom(x3)"]), succeeded(2, [{"answer": "C"}])],
    )
    before = digest(response_file)

    state = make_processor(working_dir).validate_existing_response_file(response_file)

    assert digest(response_file) == before, "the response file was rewritten; resume must only read it"
    assert before[1] == 3, "the fixture itself should still be three lines"
    assert [name for name in os.listdir(working_dir) if name.endswith(".temp")] == []

    completed, retryable, n_rows = sets_of(state)
    assert completed == {0, 2}
    assert retryable == {1}
    assert completed.isdisjoint(retryable)
    assert n_rows == 2


# =============================================================================
# scope — one file, folded the way the ledger folds
# =============================================================================
def test_scope__the_resume_view_covers_only_the_file_it_is_given_and_folds_its_duplicates(tmp_path):
    """A second responses file is invisible, and a duplicated row is counted once."""
    require_feature(ledger_is_implemented(), "the ledger's read-only resume state (read_resume_state / ResumeState)")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [0, 1])
    write_requests(working_dir, 1, [9])
    # Row 0 twice, with the same number of parsed rows each time, so the count is
    # 2 under either tie-break and 4 only if duplicates are summed.
    response_file = write_responses(
        working_dir,
        0,
        [succeeded(0, [{"answer": "A"}, {"answer": "B"}]), succeeded(0, [{"answer": "C"}, {"answer": "D"}]), failed(1)],
    )
    write_responses(working_dir, 1, [succeeded(9, [{"answer": "E"}, {"answer": "F"}, {"answer": "G"}])])

    completed, retryable, n_rows = sets_of(sym("read_resume_state")(response_file))

    assert completed == {0}, "row 9 lives in another response file and is out of scope here"
    assert retryable == {1}
    assert n_rows == 2, "the duplicate line contributes nothing, and neither does the other file"


# =============================================================================
# exclusions — where an empty parse and an unparseable body land
# =============================================================================
def test_exclusions__an_empty_parse_is_completed_while_an_unparseable_body_is_retryable(tmp_path):
    """Neither produced a dataset row; only one of them is worth reissuing."""
    require_feature(ledger_is_implemented(), "the ledger's read-only resume state (read_resume_state / ResumeState)")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [0, 1])
    response_file = write_responses(working_dir, 0, [empty(0), unparseable(1)])

    completed, retryable, n_rows = sets_of(sym("read_resume_state")(response_file))

    assert completed == {0}, "an empty parse is a finished request, not a retry"
    assert retryable == {1}, "a body that never parsed is a retry, even though it arrived"
    assert n_rows == 0


# =============================================================================
# observability — the literal fixture
# =============================================================================
def test_observability__one_record_of_each_status_splits_two_and_two_and_the_file_is_unchanged(tmp_path):
    """SUCCEEDED, FAILED, EMPTY, UNPARSEABLE — and four lines still on disk after."""
    require_feature(ledger_is_implemented(), "the ledger's read-only resume state (read_resume_state / ResumeState)")

    working_dir = fresh_dir(tmp_path)
    write_requests(working_dir, 0, [0, 1, 2, 3])
    response_file = write_responses(
        working_dir,
        0,
        [succeeded(0, [{"answer": "A"}, {"answer": "B"}]), failed(1), empty(2), unparseable(3)],
    )
    before = digest(response_file)

    completed, retryable, n_rows = sets_of(sym("read_resume_state")(response_file))

    assert completed == {0, 2}
    assert retryable == {1, 3}
    assert n_rows == 2
    assert digest(response_file) == before, "reading the resume state changed the file"
    assert before[1] == 4
    assert [name for name in os.listdir(working_dir) if name.endswith(".temp")] == []
