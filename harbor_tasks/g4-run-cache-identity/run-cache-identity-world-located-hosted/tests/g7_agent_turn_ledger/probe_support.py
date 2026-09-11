"""g7 — answer-free scenario helpers/inputs shared by the worker (probe.py) and
the human reference (test_open.py).

This module holds ONLY the curator imports, the conversation fakes, the scenario
INPUTS and the log/dataset readers the probe needs to drive curator; it contains
NO expected-output value. That is load-bearing: `run_split` copies this file into
the worker's jail, so it is inside the process that runs agent code. If any
reward-bearing expected value ever appeared here, the worker could read it and
forge a passing `observations.json`. The answers — the 186/189 byte counts, the
exact sidecar JSON spelling, the eight sidecar key/values, the completion-reason
strings, `TURN_LEDGER_VERSION`, the sentinel token asserted equal to
`COMPLETION_SENTINEL`, and the `TurnLedgerDesyncError` message format — live only
in `judge.py` (and, for humans, in `test_open.py`), which the worker cannot read.

The names here that coincide with a fact (`SEED`, `SEEDER`, `PARTNER`, `SIDECAR`,
`SENTINEL`, `CLOCK`) are INPUTS: the strings the fixtures feed into messages, the
clock stamped onto the seed, the file the sidecar is written to. They must be the
literals the reference uses or the scenarios do not reproduce; the judge holds its
own copies for the equality checks it grades, so a worker reading them here gains
nothing it does not still have to make curator actually produce.

`test_open.py` imports these names so there is a single definition of each helper
— the probe cannot drift from the reference.
"""
from __future__ import annotations

import importlib
import json
import os
from types import SimpleNamespace

import pytest

from harness import read_field  # noqa: F401 - re-exported for test_open/test_r*

from bespokelabs.curator.agent.agent_response import AgentResponse
from bespokelabs.curator.agent.processor import MultiTurnAgenticProcessor
from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.types.generic_response import GenericResponse
from bespokelabs.curator.types.token_usage import _TokenUsage

import datetime

# ---- inputs the fixtures feed ---------------------------------------------
CLOCK = datetime.datetime(2025, 1, 2, 3, 4, 5)
SEED = "I need help with my investment strategy. What should I do?"
LOG = "responses_0.jsonl"
SIDECAR = "turn_ledger.json"

SEEDER = "client"
PARTNER = "advisor"

# r2 feeds this token into replies to trigger completion; the ASSERTION that
# COMPLETION_SENTINEL equals it is the judge's, not this file's.
SENTINEL = "<<END_OF_CONVERSATION>>"


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
