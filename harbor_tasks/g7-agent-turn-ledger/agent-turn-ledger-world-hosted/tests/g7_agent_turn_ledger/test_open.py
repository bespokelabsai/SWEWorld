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
"""
from __future__ import annotations

import asyncio  # noqa: F401 - used in the test body
import os

# The answer-free helpers/inputs live in probe_support so the worker (probe.py)
# and this human reference share ONE definition and cannot drift. The expected
# VALUES this test asserts stay here (and in judge.py); probe_support holds none.
# The names re-exported here are the ones test_r1/test_r2 still import from
# `test_open` (Boom, Conversation, PARTNER, SEEDER, SIDECAR, authors,
# call_write_sidecar, log_lines, sym, write_log), plus what this module's own
# body uses.
from probe_support import (  # noqa: F401
    CLOCK,
    LOG,
    PARTNER,
    SEED,
    SEEDER,
    SENTINEL,
    SIDECAR,
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
