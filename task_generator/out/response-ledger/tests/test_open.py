"""g5 — the openly stated feature: the durable response ledger module itself.

The ticket names the module, its two constants, its four-member status enum, the
classification table, the line serialiser and its inverse, the integrity error and
its two attributes, the two frozen views, and the `ResponseLedger` surface. One
test, over a working directory that contains no duplicate lines at all — the
duplicate-resolution policy is r1's to grade, and the resume policy is r2's, so
neither appears here.

Everything the suite builds its fixtures with lives in this module: r1 and r2
import the builders below rather than repeat them, and none of them go through
`ledger_line` — a fixture written by the code under test would hide a bug in it.
"""
from __future__ import annotations

import datetime
import json
import os

import pytest
from pydantic import BaseModel

from harness import read_field, surface

try:
    from bespokelabs.curator.types.generic_request import GenericRequest
    from bespokelabs.curator.types.generic_response import GenericResponse
except Exception:  # pragma: no cover - curator itself is broken, every test says so
    GenericRequest = GenericResponse = None

# The ledger has one home the ticket names, but WHERE a symbol is exported from is
# not the requirement — an agent may re-export from the package. Look in the named
# module first, then in the places a reasonable implementation would also put it.
_CANDIDATE_MODULES = (
    "bespokelabs.curator.request_processor.response_ledger",
    "bespokelabs.curator.request_processor",
    "bespokelabs.curator.request_processor.base_request_processor",
    "bespokelabs.curator.types.response_ledger",
)

FIXED_TIME = datetime.datetime(2024, 1, 1, 0, 0, 0)


class Answer(BaseModel):
    """A `parse_func` row that is a pydantic model rather than a dict."""

    answer: str


# ---------------------------------------------------------------------------
# Reaching the ledger
# ---------------------------------------------------------------------------
def sym(name):
    """One ledger symbol, from whichever module the implementation exports it."""
    import importlib

    seen = []
    for module_name in _CANDIDATE_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        seen.append(module_name)
        if hasattr(module, name):
            return getattr(module, name)
    pytest.fail(
        f"no ledger symbol {name!r} is importable from any of {_CANDIDATE_MODULES}; "
        f"the modules that imported at all were {seen}"
    )


def ledger_is_implemented() -> bool:
    """Is there a response ledger to grade at all?

    Used by the preservation constraints in r2: 'does not rewrite the file' is
    trivially true of a checkout where nobody wrote the ledger.
    """
    import importlib

    for module_name in _CANDIDATE_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        if hasattr(module, "read_resume_state") and hasattr(module, "ResumeState"):
            return True
    return False


# ---------------------------------------------------------------------------
# Fixture builders — plain JSON, never the code under test
# ---------------------------------------------------------------------------
def make_request(idx: int) -> "GenericRequest":
    """One `GenericRequest` for row `idx`."""
    return GenericRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"q{idx}"}],
        response_format=None,
        original_row={"q": f"q{idx}"},
        original_row_idx=idx,
        generation_params={},
        is_multimodal_prompt=False,
    )


def make_response(idx: int, *, message="ok", errors=None, parsed=None) -> "GenericResponse":
    """One durable record for row `idx`.

    Nothing is filled in: `parsed=[]` is an empty parse, `parsed=None` an
    unparseable one, `message=None, errors=[...]` a permanent failure.
    """
    return GenericResponse(
        response_message=message,
        parsed_response_message=parsed,
        response_errors=errors,
        raw_response=None,
        generic_request=make_request(idx),
        created_at=FIXED_TIME,
        finished_at=FIXED_TIME,
    )


def succeeded(idx, rows=None):
    """A SUCCEEDED record: a message came back and `parse_func` produced rows."""
    return make_response(idx, message="ok", parsed=rows if rows is not None else [{"answer": f"a{idx}"}])


def failed(idx, errors=None):
    """A FAILED record: no message, and the errors that exhausted the retries."""
    return make_response(idx, message=None, errors=errors or [f"TimeoutError: boom{idx}(x3)"])


def empty(idx):
    """An EMPTY record: the call succeeded and `parse_func` returned no rows."""
    return make_response(idx, message="ok", parsed=[])


def unparseable(idx):
    """An UNPARSEABLE record: a body arrived but it never parsed."""
    return make_response(idx, message="raw text", parsed=None)


def raw_line(response) -> str:
    """Serialise a record the way pydantic would, without the ledger's help."""
    return json.dumps(response.model_dump(mode="json")) + "\n"


def write_requests(working_dir, file_index, indices, num_jobs=None) -> str:
    """A `requests_N.jsonl` / `metadata_N.json` pair declaring `indices`."""
    path = os.path.join(working_dir, f"requests_{file_index}.jsonl")
    with open(path, "w") as handle:
        for idx in indices:
            handle.write(json.dumps(make_request(idx).model_dump(mode="json")) + "\n")
    with open(os.path.join(working_dir, f"metadata_{file_index}.json"), "w") as handle:
        json.dump({"num_jobs": len(indices) if num_jobs is None else num_jobs}, handle)
    return path


def write_responses(working_dir, file_index, records) -> str:
    """A `responses_N.jsonl` holding `records`, in the order given."""
    path = os.path.join(working_dir, f"responses_{file_index}.jsonl")
    with open(path, "w") as handle:
        for record in records:
            handle.write(raw_line(record))
    return path


def row_indices(records) -> list:
    """The `original_row_idx` of each record, in the order given."""
    return [read_field(read_field(r, "generic_request"), "original_row_idx") for r in records]


def counts(tally, *names) -> list:
    """Several tally fields at once, by the names the ticket spells."""
    return [read_field(tally, name) for name in names]


# =============================================================================
# The open feature
# =============================================================================
def test_open_feature__the_ledger_module_classifies_serialises_and_folds_a_working_directory(tmp_path):
    """The whole openly stated surface, over a directory with one line per request."""
    assert GenericResponse is not None, "curator's own GenericResponse does not import"

    LedgerStatus = sym("LedgerStatus")
    classify_record = sym("classify_record")
    ledger_line = sym("ledger_line")
    parse_ledger_line = sym("parse_ledger_line")
    ResponseLedger = sym("ResponseLedger")
    LedgerIntegrityError = sym("LedgerIntegrityError")

    # --- constants ---------------------------------------------------------
    assert isinstance(sym("LEDGER_SCHEMA_VERSION"), int)
    assert isinstance(sym("ERROR_SAMPLE_LIMIT"), int)

    # --- the four statuses, and the order the predicates are applied -------
    members = [m.name for m in LedgerStatus]
    assert set(members) == {"SUCCEEDED", "EMPTY", "UNPARSEABLE", "FAILED"}, f"LedgerStatus has {members}"

    table = [
        (make_response(0, message="x", parsed=[{"a": 1}]), LedgerStatus.SUCCEEDED),
        (make_response(0, message=None, errors=["e"]), LedgerStatus.FAILED),
        (make_response(0, message="x", parsed=None), LedgerStatus.UNPARSEABLE),
        (make_response(0, message="x", parsed=[]), LedgerStatus.EMPTY),
        (make_response(0, message=None, parsed=[{"a": 1}]), LedgerStatus.FAILED),
        (make_response(0, message="x", errors=["e"], parsed=[{"a": 1}]), LedgerStatus.FAILED),
    ]
    assert [classify_record(record) for record, _ in table] == [expected for _, expected in table]

    # --- ledger_line: raw message out, normalised rows, exactly one newline
    structured = make_response(4, message='{"answer": "A"}', parsed=[Answer(answer="A")])
    line = ledger_line(structured)
    assert line.endswith("\n") and line.count("\n") == 1
    payload = json.loads(line)
    assert payload["response_message"] == '{"answer": "A"}', "the raw provider message is kept as-is"
    assert payload["parsed_response_message"] == [{"answer": "A"}], "a BaseModel row is normalised, not stringified"
    assert payload["parsed_response_message"] != ["answer='A'"]

    # dict rows survive untouched; anything else is a ValueError
    assert json.loads(ledger_line(succeeded(4, [{"answer": "A"}])))["parsed_response_message"] == [{"answer": "A"}]
    with pytest.raises(ValueError):
        ledger_line(make_response(4, message="x", parsed=["not a row"]))

    # --- parse_ledger_line is its inverse, and forgiving of junk -----------
    assert classify_record(parse_ledger_line(line)) is LedgerStatus.SUCCEEDED
    assert parse_ledger_line("\n") is None
    assert parse_ledger_line("{oops") is None

    # --- a loaded working directory ----------------------------------------
    working_dir = str(tmp_path / "run")
    os.makedirs(working_dir)
    write_requests(working_dir, 0, [0, 1, 2], num_jobs=3)
    write_responses(working_dir, 0, [succeeded(0, [{"answer": "A"}]), failed(1, ["TimeoutError: boom(x3)"])])

    ledger = ResponseLedger.load(working_dir)
    assert read_field(ledger, "working_dir") == working_dir

    records = ledger.winning_records()
    assert row_indices(records) == [0, 1], "one winning record per recorded row, ascending"
    assert [classify_record(r) for r in records] == [LedgerStatus.SUCCEEDED, LedgerStatus.FAILED]

    tally = ledger.tally()
    assert counts(tally, "n_requests", "n_declared_requests", "n_recorded", "n_succeeded", "n_failed", "n_missing") == [3, 3, 2, 1, 1, 1]
    assert counts(tally, "n_duplicate_lines", "n_malformed_lines", "n_dataset_rows") == [0, 0, 1]
    assert read_field(tally, "schema_version") == sym("LEDGER_SCHEMA_VERSION")
    assert isinstance(read_field(tally, "error_sample"), tuple)

    assert ledger.missing_row_indices() == [2]
    assert ledger.unresolved_row_indices() == [1, 2], "a failure and a request with no record at all"

    request_line = ledger.request_line(0)
    assert request_line.endswith("\n") and request_line.count("\n") == 1
    assert json.loads(request_line)["original_row_idx"] == 0

    # --- a ResumeState comes back from the single-file reader ---------------
    state = sym("read_resume_state")(os.path.join(working_dir, "responses_0.jsonl"))
    for field in ("completed_row_indices", "retryable_row_indices", "n_dataset_rows"):
        read_field(state, field)  # raises AssertionError naming the surface if absent
    assert set(read_field(state, "completed_row_indices")) == {0}

    # --- an orphan record is an integrity error, not a silently kept row ---
    with open(os.path.join(working_dir, "responses_0.jsonl"), "a") as handle:
        handle.write(raw_line(succeeded(9)))
    with pytest.raises(LedgerIntegrityError) as excinfo:
        ResponseLedger.load(working_dir)
    assert isinstance(excinfo.value, ValueError)
    assert read_field(excinfo.value, "row_idx") == 9, f"the error carries {surface(excinfo.value)}"
    assert os.path.basename(str(read_field(excinfo.value, "source_file"))) == "responses_0.jsonl"
