"""g7 — hidden requirement r1: the checkpoint beside the log.

    rule            turn_ledger.json / version 2, sidecar_state()'s exactly eight
                    keys, read/write/verify_sidecar, and a rewrite after EVERY
                    appended response rather than one write at the end
    scope           load_ledger writes nothing, the log outranks the checkpoint in
                    every direction, and only "responses" and "last_author" are
                    compared; "created" / "adopted" / "verified" say where a
                    ledger came from
    failure_behavior  the three arms of verify_sidecar: absent, unreadable or
                    old-version -> "adopted"; agreeing -> "verified"; disagreeing
                    -> TurnLedgerDesyncError, raised before anything is asked
    observability   the file on disk: 186 bytes mid-run, 189 when the conversation
                    ends, and the five attributes a stale one produces

The four are four measurements. `rule` never loads a hand-written checkpoint,
`scope` never expects an exception, `failure_behavior` never reads a byte count,
and `observability` is the only one that spells the file out literally.
"""
from __future__ import annotations

import asyncio
import json
import os

import pytest

from harness import read_field

from test_open import (
    Boom,
    Conversation,
    PARTNER,
    SEEDER,
    SIDECAR,
    authors,
    log_lines,
    sym,
    write_log,
)

EIGHT_KEYS = {
    "version",
    "responses",
    "turns",
    "last_author",
    "next_speaker",
    "interleave_faults",
    "completed",
    "completion_reason",
}

THREE_LINES = ((SEEDER, "seed message"), (PARTNER, "first answer"), (SEEDER, "second question"))

NEVER = lambda author, content: False  # noqa: E731  - the callback build_ledger takes


def load(working_dir, max_responses=9):
    """The ledger a working directory holds, by the ticket's own entry point."""
    load_ledger = sym("load_ledger")
    return load_ledger(
        str(working_dir),
        seeder_name=SEEDER,
        partner_name=PARTNER,
        max_responses=max_responses,
        is_completed=NEVER,
    )


def put_sidecar(working_dir, state):
    path = os.path.join(str(working_dir), SIDECAR)
    with open(path, "w") as handle:
        handle.write(json.dumps(state))
    return path


def full_state(**overrides):
    state = {
        "version": 2,
        "responses": 2,
        "turns": 3,
        "last_author": SEEDER,
        "next_speaker": PARTNER,
        "interleave_faults": 0,
        "completed": False,
        "completion_reason": "open",
    }
    state.update(overrides)
    return state


def test_rule__a_versioned_checkpoint_rewritten_after_every_appended_response(tmp_path):
    assert sym("TURN_LEDGER_FILENAME") == "turn_ledger.json"
    assert sym("TURN_LEDGER_VERSION") == 2

    read_sidecar = sym("read_sidecar")
    write_sidecar = sym("write_sidecar")
    sym("verify_sidecar")  # the third of the three functions the requirement names

    # A run that dies on its third call has appended the seed and two responses.
    # Whatever the checkpoint says, it cannot have been written at the end.
    conversation = Conversation(raise_on=(3,))
    processor = conversation.processor(max_length=4)
    with pytest.raises(Boom):
        asyncio.run(processor.run(str(tmp_path)))

    assert authors(tmp_path) == [SEEDER, PARTNER, SEEDER]

    path = os.path.join(str(tmp_path), "turn_ledger.json")
    assert os.path.exists(path), "no checkpoint was written before the run failed"

    state = read_sidecar(str(tmp_path))
    assert set(state) == EIGHT_KEYS, sorted(state)
    assert state["version"] == 2
    assert state["responses"] == 2
    assert state["turns"] == 3
    assert state["last_author"] == SEEDER
    assert state["next_speaker"] == PARTNER
    assert state["interleave_faults"] == 0
    assert state["completed"] is False
    assert state["completion_reason"] == "open"

    # sidecar_state() is that dict, and write_sidecar puts exactly it on disk and
    # returns where it put it.
    ledger = load(tmp_path, max_responses=4)
    assert ledger.sidecar_state() == state
    returned = write_sidecar(str(tmp_path), ledger)
    assert os.path.isabs(returned)
    assert os.path.realpath(returned) == os.path.realpath(path)
    assert json.loads(open(path).read()) == state


def test_scope__load_ledger_writes_nothing_and_the_log_outranks_the_checkpoint(tmp_path):
    statuses = sym("LEDGER_STATUSES")
    assert set(statuses) == {"created", "adopted", "verified"}

    write_log(tmp_path, THREE_LINES)
    before = os.path.join(str(tmp_path), "responses_0.jsonl")
    log_bytes = open(before, "rb").read()

    # No checkpoint yet: the ledger comes from the log alone, and reading it
    # leaves the directory exactly as it was.
    listing = sorted(os.listdir(str(tmp_path)))
    adopted = load(tmp_path)
    assert read_field(adopted, "status") == "adopted"
    assert read_field(adopted, "responses") == 2
    assert sorted(os.listdir(str(tmp_path))) == listing, "load_ledger wrote to the directory"

    # A checkpoint that agrees on the only two keys compared -- and is wrong
    # about the other six -- verifies, and none of its six lies reach the ledger.
    path = put_sidecar(
        tmp_path,
        full_state(
            turns=99,
            next_speaker="nobody",
            interleave_faults=7,
            completed=True,
            completion_reason="budget",
        ),
    )
    recorded = open(path, "rb").read()
    ledger = load(tmp_path)
    assert read_field(ledger, "status") == "verified"
    assert read_field(ledger, "turns") == 3
    assert read_field(ledger, "responses") == 2
    assert read_field(ledger, "next_speaker") == PARTNER
    assert read_field(ledger, "interleave_faults") == 0
    assert read_field(ledger, "completed") is False
    assert read_field(ledger, "completion_reason") == "open"

    # Nothing was written, and no log line was truncated, re-ordered or rewritten
    # to agree with the file.
    assert open(path, "rb").read() == recorded
    assert open(before, "rb").read() == log_bytes
    assert authors(tmp_path) == [SEEDER, PARTNER, SEEDER]

    # A ledger built for a fresh run's first write says so.
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    conversation = Conversation(raise_on=(1,))
    processor = conversation.processor(max_length=4)
    with pytest.raises(Boom):
        asyncio.run(processor.run(str(fresh)))
    assert read_field(processor.ledger, "status") == "created"


def test_failure_behavior__absent_or_old_is_adopted_and_a_disagreeing_one_aborts(tmp_path):
    desync = sym("TurnLedgerDesyncError")
    base = sym("TurnLedgerError")
    assert issubclass(desync, base) and issubclass(base, RuntimeError)

    write_log(tmp_path, THREE_LINES)
    path = os.path.join(str(tmp_path), "turn_ledger.json")

    # (a) absent, unreadable, or a version this build does not speak.
    assert read_field(load(tmp_path), "status") == "adopted"

    with open(path, "w") as handle:
        handle.write("{not json at all")
    assert read_field(load(tmp_path), "status") == "adopted"

    put_sidecar(tmp_path, {"version": 1, "responses": 2, "last_author": SEEDER})
    assert read_field(load(tmp_path), "status") == "adopted"

    # (b) the version matches and both compared keys agree.
    put_sidecar(tmp_path, full_state())
    assert read_field(load(tmp_path), "status") == "verified"

    # (c) the version matches and the response count differs.
    put_sidecar(tmp_path, full_state(responses=1))
    with pytest.raises(desync) as caught:
        load(tmp_path)
    error = caught.value
    assert os.path.realpath(error.path) == os.path.realpath(path)
    assert error.log_responses == 2
    assert error.recorded_responses == 1
    assert error.log_last_author == SEEDER
    assert error.recorded_last_author == SEEDER
    assert str(error) == (
        f"{error.path} records 1 response(s) last authored by {SEEDER!r}, "
        f"the log holds 2 last authored by {SEEDER!r}"
    )

    # (c) the version matches and the last author differs.
    put_sidecar(tmp_path, full_state(last_author=PARTNER))
    with pytest.raises(desync) as caught:
        load(tmp_path)
    assert caught.value.log_last_author == SEEDER
    assert caught.value.recorded_last_author == PARTNER
    assert caught.value.log_responses == 2
    assert caught.value.recorded_responses == 2

    # The raise happens on the load path: nothing is asked, nothing is appended.
    conversation = Conversation()
    processor = conversation.processor(max_length=6)
    with pytest.raises(desync):
        asyncio.run(processor.run(str(tmp_path)))
    assert conversation.calls == []
    assert len(log_lines(tmp_path)) == 3


def test_observability__the_checkpoint_reads_186_bytes_mid_run_and_189_at_the_end(tmp_path):
    read_sidecar = sym("read_sidecar")
    desync = sym("TurnLedgerDesyncError")

    # ---- the first write, before a single response exists ------------------
    opening = tmp_path / "opening"
    opening.mkdir()
    conversation = Conversation(raise_on=(1,))
    processor = conversation.processor(max_length=4)
    with pytest.raises(Boom):
        asyncio.run(processor.run(str(opening)))

    path = opening / "turn_ledger.json"
    assert path.exists(), "the seed line was not checkpointed before the first request"
    assert path.read_text() == (
        "{\n"
        '  "completed": false,\n'
        '  "completion_reason": "open",\n'
        '  "interleave_faults": 0,\n'
        '  "last_author": "client",\n'
        '  "next_speaker": "advisor",\n'
        '  "responses": 0,\n'
        '  "turns": 1,\n'
        '  "version": 2\n'
        "}\n"
    )
    assert path.stat().st_size == 186

    # ---- and the last write, when the conversation ends --------------------
    done = tmp_path / "done"
    done.mkdir()
    stops = lambda response: isinstance(response, str) and response.endswith("STOP")  # noqa: E731
    finished = Conversation(replies=["a", "b", "c STOP"], is_completed=stops)
    runner = finished.processor(max_length=6)
    asyncio.run(runner.run(str(done)))

    assert len(log_lines(done)) == 4
    sidecar = done / "turn_ledger.json"
    assert sidecar.stat().st_size == 189
    assert read_sidecar(str(done)) == {
        "version": 2,
        "responses": 3,
        "turns": 4,
        "last_author": PARTNER,
        "next_speaker": None,
        "interleave_faults": 0,
        "completed": True,
        "completion_reason": "agent_signal",
    }

    # ---- a log truncated behind the checkpoint's back ----------------------
    lines = (done / "responses_0.jsonl").read_text().splitlines(keepends=True)
    (done / "responses_0.jsonl").write_text("".join(lines[:3]))
    stale = Conversation(replies=["c STOP"], is_completed=stops)
    aborted = stale.processor(max_length=6)
    with pytest.raises(desync) as caught:
        asyncio.run(aborted.run(str(done)))
    assert os.path.realpath(caught.value.path) == os.path.realpath(str(sidecar))
    assert caught.value.log_responses == 2
    assert caught.value.recorded_responses == 3
    assert caught.value.log_last_author == SEEDER
    assert caught.value.recorded_last_author == PARTNER
    assert stale.calls == []
    assert len(log_lines(done)) == 3

    # ---- the same log with no checkpoint at all ----------------------------
    sidecar.unlink()
    resumed = Conversation(replies=["c STOP"], is_completed=stops)
    second = resumed.processor(max_length=6)
    asyncio.run(second.run(str(done)))
    assert read_field(second.ledger, "status") == "adopted"
    assert resumed.calls == [(PARTNER, 2)]
    assert len(log_lines(done)) == 4

    # ---- and with one written by a version this build does not speak -------
    older = tmp_path / "older"
    older.mkdir()
    write_log(older, THREE_LINES)
    put_sidecar(older, {"version": 1, "responses": 2, "last_author": SEEDER})
    assert read_field(load(older), "status") == "adopted"
