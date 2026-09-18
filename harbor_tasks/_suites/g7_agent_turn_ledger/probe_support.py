"""g7 — answer-free scenario helpers shared by the worker (probe.py) and the
suite's human-readable record of the facts, which is kept in the repository and
not shipped with the task (a split suite grades through probe.py + judge.py).

This module holds ONLY the curator imports, the conversation fakes and the
log/dataset readers the probe needs to drive curator; it contains NO expected
value and NO name a hidden requirement fixes. That is load-bearing: `run_split`
copies this file into the worker's jail, so it is readable by the process that
runs agent code. The checkpoint's file name, its version and spelling, the
completion token and every status word live only in `judge.py`, which the
worker cannot read: `test.sh` keeps /tests root-only for a split suite.

Agent names are not fixed here either. The grader draws them per run
(`fixture_spec.derive`) because they are spelled into the checkpoint, and the
record's worked example pins its own with `set_names`.
"""
from __future__ import annotations

import importlib
import json
import os
from types import SimpleNamespace

import pytest

from harness import read_field  # noqa: F401 - re-exported for the probe and the record

import fixture_spec

from bespokelabs.curator.agent.agent_response import AgentResponse
from bespokelabs.curator.agent.processor import MultiTurnAgenticProcessor
from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.types.generic_response import GenericResponse
from bespokelabs.curator.types.token_usage import _TokenUsage

import datetime

# ---- inputs the fixtures feed ---------------------------------------------
CLOCK = datetime.datetime.fromisoformat(fixture_spec.CLOCK_ISO)
SEED = "I need help with my investment strategy. What should I do?"
LOG = fixture_spec.LOG

# Set by the caller before any Conversation is built: the probe from the run's
# seed, the human reference from its worked example.
SEEDER = None
PARTNER = None


def set_names(seeder, partner):
    global SEEDER, PARTNER
    SEEDER, PARTNER = seeder, partner


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

    def __init__(self, replies=(), is_completed=None, raise_on=(), system_prompt=True,
                 extra_system=0):
        self.replies = list(replies)
        self.calls = []
        self.requests = []                     # the messages each call was given
        self.formatter_out = []                # what the formatter answered, per call
        self.extra_system = extra_system
        self.raise_on = set(raise_on)          # 1-based call numbers that blow up
        self._is_completed = is_completed or (lambda response: False)
        seeder_prompt = "You ask the questions in this conversation." if system_prompt else None
        partner_prompt = "You answer the questions in this conversation." if system_prompt else None
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
            conversation.requests.append([dict(msg) for msg in request.generic_request.messages])
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

        if self.extra_system:
            formatter = _MultiSystemFormatter(formatter, self.extra_system, conversation)

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


class _MultiSystemFormatter:
    """A prompt formatter that answers with MORE than one system message.

    A stock `PromptFormatter` cannot: `_put_system_prompt` raises when the prompt
    function already returned one, so the case instruction.md:44 spells out ("the
    first is used and the others stay in place in the body") had no fixture and
    no assertion, and the oracle discarded the extras for eight versions without
    anything noticing.

    It carries no expected value: the messages it produced are reported to the
    judge beside the messages the processor then sent, and the judge derives the
    one from the other.
    """

    def __init__(self, inner, extra, conversation):
        self._inner = inner
        self._extra = extra
        self._conversation = conversation
        self.model_name = inner.model_name

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def create_generic_request(self, row, idx, *args, **kwargs):
        request = self._inner.create_generic_request(row, idx, *args, **kwargs)
        messages = list(request.messages)
        messages += [{"role": "system", "content": f"trailing system rule {nth + 1}"}
                     for nth in range(self._extra)]
        request.messages = messages
        self._conversation.formatter_out.append([dict(msg) for msg in messages])
        return request


def log_lines(working_dir):
    path = os.path.join(str(working_dir), LOG)
    if not os.path.exists(path):
        return []
    return [line for line in open(path).read().splitlines() if line.strip()]


def authors(working_dir):
    return [json.loads(line)["name"] for line in log_lines(working_dir)]


def write_log(working_dir, rows):
    """A hand-written log: one (author, content) pair per line.

    The bytes come from `fixture_spec.log_text`, which the judge also has, so a
    scenario's log can be compared against what was planted by the process that
    decides the verdict.
    """
    path = os.path.join(str(working_dir), LOG)
    with open(path, "w") as handle:
        handle.write(fixture_spec.log_text(rows))
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


def call_write_sidecar(write_sidecar, working_dir, ledger):
    """`write_sidecar(working_dir, ledger)`, or the same two the other way round.

    The one remark that fixed the order ("you hand it the work dir and the
    ledger", g7.r1.say20) was planted and never rendered: no chat line, page or
    mail in the served world states it, and the ticket does not name the
    function. Two v5 runs took (ledger, working_dir) and lost r1.rule for an
    order they could only have guessed. The stated order is tried first and the
    reverse only if that raises, which a swapped signature does before it writes
    anything, because a ledger is not a path.
    """
    try:
        return write_sidecar(working_dir, ledger)
    except Exception as stated_order:
        try:
            return write_sidecar(ledger, working_dir)
        except Exception:
            raise stated_order
