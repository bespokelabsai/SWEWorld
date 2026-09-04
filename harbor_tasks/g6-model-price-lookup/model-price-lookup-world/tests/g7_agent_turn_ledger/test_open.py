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

import asyncio
import datetime
import importlib
import json
import os
from types import SimpleNamespace

import pytest

from harness import read_field

from bespokelabs.curator.agent.agent_response import AgentResponse
from bespokelabs.curator.agent.processor import MultiTurnAgenticProcessor
from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.types.generic_response import GenericResponse
from bespokelabs.curator.types.token_usage import _TokenUsage

CLOCK = datetime.datetime(2025, 1, 2, 3, 4, 5)
SEED = "I need help with my investment strategy. What should I do?"
LOG = "responses_0.jsonl"
SIDECAR = "turn_ledger.json"

SEEDER = "client"
PARTNER = "advisor"


class Boom(RuntimeError):
    """Raised by a fake call to stop a run at a chosen moment."""


def sym(name, default=...):
    """A module-level name, wherever in the agent package it was written.

    Which module exports a constant is an implementation choice; the ticket
    names `agent/turn_ledger.py` for this family, but a submission that put
    `COMPLETION_SENTINEL` beside `Agent` has satisfied the requirement just as
    well, so every module of the package is searched before giving up.
    """
    candidates = (
        "bespokelabs.curator.agent.turn_ledger",
        "bespokelabs.curator.agent.agent",
        "bespokelabs.curator.agent.processor",
        "bespokelabs.curator.agent.agent_response",
        "bespokelabs.curator.status_tracker.agent_status_tracker",
        "bespokelabs.curator.agent",
        "bespokelabs.curator",
    )
    for dotted in candidates:
        try:
            module = importlib.import_module(dotted)
        except Exception:
            continue
        if hasattr(module, name):
            return getattr(module, name)
    if default is not ...:
        return default
    pytest.fail(f"no module of bespokelabs.curator.agent exports {name!r}")


class Conversation:
    """Two duck-typed agents reading from one script of replies."""

    def __init__(self, replies=(), is_completed=None, raise_on=(), system_prompt=True):
        self.replies = list(replies)
        self.calls = []
        self.raise_on = set(raise_on)          # 1-based call numbers that blow up
        self._is_completed = is_completed or (lambda response: False)
        seeder_prompt = "You are a client that asks questions to the advisor." if system_prompt else None
        partner_prompt = "You are a helpful advisor." if system_prompt else None
        self.seeder = self._agent(SEEDER, seeder_prompt)
        self.partner = self._agent(PARTNER, partner_prompt)

    def _reply(self, nth):
        if nth - 1 < len(self.replies):
            return self.replies[nth - 1]
        return f"canned reply {nth}"

    def _agent(self, name, system_prompt):
        conversation = self
        formatter = PromptFormatter(
            model_name="gpt-4o-mini",
            prompt_func=lambda row: [{"role": "user", "content": row["prompt"]}],
            parse_func=None,
            system_prompt=system_prompt,
        )

        async def call_single_request(request, session, status_tracker=None):
            conversation.calls.append((name, request.task_id))
            nth = len(conversation.calls)
            if nth in conversation.raise_on:
                raise Boom(f"call {nth}")
            return GenericResponse(
                response_message=conversation._reply(nth),
                raw_response=None,
                generic_request=request.generic_request,
                created_at=CLOCK,
                finished_at=CLOCK,
                token_usage=_TokenUsage(input=10, output=5, total=15),
                response_cost=0.001,
                finish_reason="stop",
            )

        processor = SimpleNamespace(
            create_api_specific_request_online=lambda request: {"model": "gpt-4o-mini"},
            call_single_request=call_single_request,
            # A real request processor carries its config, and `APIRequest` is
            # built with an `attempts_left`. Curator's own code passes a literal
            # `1` there; an implementation that reaches for
            # `_request_processor.config.max_retries` instead is doing something
            # reasonable that this fixture must not punish. Without this the
            # whole open feature failed on `AttributeError: 'SimpleNamespace'
            # object has no attribute 'config'` -- fifty-one assertions lost to
            # a line the ticket never mentions and the suite does not grade.
            config=SimpleNamespace(max_retries=1, max_concurrent_requests=1),
        )
        return SimpleNamespace(
            name=name,
            model_name="gpt-4o-mini",
            prompt_formatter=formatter,
            _request_processor=processor,
            is_completed=self._is_completed,
        )

    def processor(self, max_length):
        """A processor over these two agents, with the clock pinned if it takes one."""
        try:
            return MultiTurnAgenticProcessor(self.seeder, self.partner, max_length, SEED, now_fn=lambda: CLOCK)
        except TypeError:
            # An implementation that never took an injected clock still gets to
            # be measured on everything else.
            return MultiTurnAgenticProcessor(self.seeder, self.partner, max_length, SEED)


def log_lines(working_dir):
    path = os.path.join(str(working_dir), LOG)
    if not os.path.exists(path):
        return []
    return [line for line in open(path).read().splitlines() if line.strip()]


def authors(working_dir):
    return [json.loads(line)["name"] for line in log_lines(working_dir)]


def write_log(working_dir, rows):
    """A hand-written log: one (author, content) pair per line."""
    path = os.path.join(str(working_dir), LOG)
    with open(path, "w") as handle:
        for index, (author, content) in enumerate(rows):
            record = {
                "name": author,
                "response_message": content,
                "parsed_response_message": None,
                "response_errors": None,
                "raw_response": None,
                "raw_request": None,
                "generic_request": {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": content}],
                    "response_format": None,
                    "original_row": {"prompt": content},
                    "original_row_idx": 0,
                    "generation_params": {},
                    "is_multimodal_prompt": False,
                },
                "created_at": CLOCK.isoformat(),
                "finished_at": CLOCK.isoformat(),
                "token_usage": None,
                "response_cost": 0.0 if index == 0 else 0.001,
                "finish_reason": "seed" if index == 0 else "stop",
            }
            handle.write(json.dumps(record) + "\n")
    return path


def drop_side_files(working_dir):
    """Leave the log and nothing else.

    Whether a resume keeps a checkpoint beside the log, and what it would be
    called, is not part of the open feature; removing every other file means a
    truncated-log resume is graded on the log alone, whatever name a submission
    chose for anything it keeps next to it.
    """
    for name in os.listdir(str(working_dir)):
        path = os.path.join(str(working_dir), name)
        if name != LOG and os.path.isfile(path):
            os.unlink(path)


def rows_of(dataset):
    return [dict(row) for row in dataset]


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
