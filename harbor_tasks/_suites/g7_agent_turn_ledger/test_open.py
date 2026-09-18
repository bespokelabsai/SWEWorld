"""g7 — the openly stated feature: a multi-turn conversation as a durable log.

The ticket states all of this outright, so one test measures it end to end:

  * the seed message is line 0 of `responses_0.jsonl`, written before the first
    request is built, as an `AgentResponse` stamped by `now_fn`;
  * `max_length` budgets *generated responses*, so an un-stopped run makes
    exactly `max_length` calls and leaves `max_length + 1` lines whether it ran
    once or resumed;
  * whose turn it is comes from the log's last author, and `task_id` is the
    0-based response index;
  * the dataset carries the seed and says which row it is;
  * a resume adopts the past into `num_cached` instead of re-generating it;
  * an agent with no system prompt is a conversation, not an `IndexError`.

The fakes here are duck-typed agents — `name`, `model_name`, `prompt_formatter`,
`_request_processor`, `is_completed` — exactly as the brief describes, so no
provider, socket or clock is involved.

Three clauses of the ticket cannot be shown by any of that, because they are
constraints on source inside files the ticket rewrites, and every scenario below
runs against fakes in a fresh directory:

  * `MultiTurnAgenticProcessor.append_response()` is reused verbatim
    (instruction.md:65);
  * `Agent._hash_fingerprint` and the `xxh64(seed_message)` run identity are
    untouched (instruction.md:66) — derivation AND use: a changed fingerprint,
    or a pristine fingerprint that no longer names the working directory,
    orphans every cache directory the company already has, and no fact here
    would notice, because every scenario below hands the processor its own
    directory. The identity itself is therefore compared against the pristine
    tree, in the method's own place and as the module BINDS it: in
    `MultiTurnAgents.__call__` every statement that binds `fingerprint`,
    `disable_cache` or `working_dir`, and in `__call__` and `_setup_metadata`
    the `run_hash`/`dataset_hash` entries that report it — not the whole
    method, so an added log line or an unrelated metadata key passes. Anything
    that makes the read definition not the bound one is refused, not resolved:
    a duplicate or conditionally-placed `class`/`def`, a class decorator, a
    `globals()` rebind, and — anywhere in the package — an assignment whose
    attribute is `append_response`, `__call__`, `_setup_metadata` or
    `_hash_fingerprint`, whatever expression that attribute is taken from, or a
    `setattr` whose name argument is one of those four or is not a plain string
    literal. The receiver is deliberately not read: five review rounds of
    recognising it produced one more spelling each time, the last being
    `getattr(m, "Multi" + "TurnAgenticProcessor").append_response = ...`;
  * no new dependency, and Python stays at `^3.10` (instruction.md:67); the
    ledger module also imports neither `time`, `random` nor `uuid`
    (instruction.md:11).

`judge.check_append_response_verbatim`, `check_run_identity_untouched` and
`check_no_new_dependency` enforce those against `CURATOR_BASELINE_DIR` and the
pristine manifest, as part of this same fact.
"""
from __future__ import annotations

import asyncio  # noqa: F401 - used in the test body
import os

# The answer-free helpers live in probe_support so the worker (probe.py) and this
# human reference share ONE definition and cannot drift. probe_support holds no
# expected value and no fixed agent name — the grader draws the names per run
# (fixture_spec.derive) — so this worked example pins its own and hands them over.
# test_r1/test_r2 import Boom, Conversation, PARTNER, SEEDER, authors,
# call_write_sidecar, log_lines, sym and write_log from here.
import probe_support
from probe_support import (  # noqa: F401
    CLOCK,
    LOG,
    SEED,
    AgentResponse,
    Boom,
    Conversation,
    GenericResponse,
    MultiTurnAgenticProcessor,
    PromptFormatter,
    _TokenUsage,
    authors,
    call_write_sidecar,
    drop_side_files,
    log_lines,
    read_field,
    rows_of,
    sym,
    write_log,
)

SEEDER = "client"
PARTNER = "advisor"
probe_support.set_names(SEEDER, PARTNER)


def test_open_feature__the_seed_is_logged_and_max_length_budgets_generated_responses(tmp_path):
    # ---- a fresh run -------------------------------------------------------
    conversation = Conversation()
    processor = conversation.processor(max_length=4)
    dataset = asyncio.run(processor.run(str(tmp_path)))

    assert len(conversation.calls) == 4, conversation.calls
    assert [name for name, _ in conversation.calls] == [PARTNER, SEEDER, PARTNER, SEEDER]
    assert [task_id for _, task_id in conversation.calls] == [0, 1, 2, 3]

    lines = log_lines(tmp_path)
    assert len(lines) == 5
    assert authors(tmp_path) == [SEEDER, PARTNER, SEEDER, PARTNER, SEEDER]

    seed = AgentResponse.model_validate_json(lines[0])
    assert seed.name == SEEDER
    assert seed.response_message == SEED
    assert seed.finish_reason == "seed"
    assert seed.response_cost == 0.0
    assert seed.token_usage is None
    assert seed.raw_response is None
    assert seed.raw_request is None
    assert seed.parsed_response_message is None
    assert seed.response_errors is None
    assert seed.created_at == seed.finished_at == CLOCK
    assert seed.generic_request.model == "gpt-4o-mini"
    assert seed.generic_request.messages == [{"role": "user", "content": SEED}]
    assert seed.generic_request.original_row == {"prompt": SEED}
    assert seed.generic_request.original_row_idx == 0

    ledger = processor.ledger
    assert read_field(ledger, "responses") == 4
    assert read_field(ledger, "turns") == 5
    assert read_field(ledger, "last_author") == SEEDER
    assert read_field(ledger, "next_speaker") is None
    assert read_field(ledger, "interleave_faults") == 0
    assert read_field(ledger, "completed") is True
    assert read_field(ledger, "completion_reason") == "budget"
    assert isinstance(read_field(ledger, "entries"), tuple)
    assert ledger.messages() == processor.conversation_history
    assert processor.conversation_history[0] == {"role": SEEDER, "content": SEED}

    tracker = processor.status_tracker
    assert read_field(tracker, "max_turns") == 4
    assert read_field(tracker, "current_turn") == 4
    assert read_field(tracker, "num_responses") == 4
    assert read_field(tracker, "num_cached") == 0
    assert read_field(tracker, "num_errors") == 0

    rows = rows_of(dataset)
    assert set(dataset.column_names) == {"role", "content", "turn", "source"}
    assert len(rows) == 5
    assert rows[0] == {"role": SEEDER, "content": SEED, "turn": 0, "source": "seed"}
    assert [row["turn"] for row in rows] == [0, 1, 2, 3, 4]
    assert [row["source"] for row in rows] == ["seed"] + ["response"] * 4
    assert [row["role"] for row in rows] == authors(tmp_path)

    # ---- and a resume of the same directory --------------------------------
    keep = open(os.path.join(str(tmp_path), LOG)).read().splitlines(keepends=True)[:3]
    open(os.path.join(str(tmp_path), LOG), "w").write("".join(keep))
    drop_side_files(tmp_path)

    resumed = Conversation()
    second = resumed.processor(max_length=4)
    dataset2 = asyncio.run(second.run(str(tmp_path)))

    # The budget is a budget of responses, not of restarts: two more calls, and
    # the log lands on max_length + 1 lines again.
    assert len(resumed.calls) == 2, resumed.calls
    assert resumed.calls == [(PARTNER, 2), (SEEDER, 3)]
    assert len(log_lines(tmp_path)) == 5
    assert read_field(second.ledger, "responses") == 4
    assert len(rows_of(dataset2)) == 5
    assert read_field(second.status_tracker, "num_cached") == 2
    assert read_field(second.status_tracker, "num_responses") == 2
    assert read_field(second.status_tracker, "current_turn") == 4

    # ---- an agent built without a system prompt still converses -------------
    bare_dir = tmp_path / "bare"
    bare_dir.mkdir()
    bare = Conversation(system_prompt=False)
    third = bare.processor(max_length=1)
    dataset3 = asyncio.run(third.run(str(bare_dir)))
    assert len(bare.calls) == 1
    assert len(log_lines(bare_dir)) == 2
    assert len(rows_of(dataset3)) == 2

    # ---- a formatter that answers with more than one system message --------
    # instruction.md:44: the first moves to index 0, the others stay in place in
    # the body. `judge.py` derives this from what the formatter answered; here
    # the fixture's own shape is known, so it is written out.
    multi_dir = tmp_path / "multi"
    multi_dir.mkdir()
    multi = Conversation(extra_system=2)
    fourth = multi.processor(max_length=1)
    asyncio.run(fourth.run(str(multi_dir)))
    sent = multi.requests[0]
    assert [msg["role"] for msg in sent] == ["system", "user", "system", "system"], sent
    assert sent[0]["content"] == "You answer the questions in this conversation."
    assert [msg["content"] for msg in sent[2:]] == ["trailing system rule 1",
                                                    "trailing system rule 2"]
