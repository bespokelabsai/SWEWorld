"""g7 — hidden requirement r2: the default completion signal.

    rule            COMPLETION_SENTINEL is "<<END_OF_CONVERSATION>>" and the base
                    Agent.is_completed says True when a reply ends with it
    scope           case-sensitive, suffix-only, blind to trailing whitespace
    failure_behavior  a structured-output dict or None answers False instead of
                    raising AttributeError / TypeError
    observability   the message carrying the token is a real turn: logged,
                    counted, in the dataset, and the conversation stops after it

`rule` fixes the token, `scope` fixes the matching discipline, and neither runs a
conversation; `observability` is the only one that does.

This is the human reference, over fixed example replies. The grader asserts the
same rule over shuffled lists of candidate replies re-drawn from a per-run seed
(`fixture_spec.derive`), rendering them with the token the submission completes
on and checking that token against the one named here.
"""
from __future__ import annotations

import asyncio

import pytest

from harness import read_field, require_feature

from bespokelabs.curator.agent.agent import Agent

from test_open import Conversation, PARTNER, SEEDER, log_lines, sym

SENTINEL = "<<END_OF_CONVERSATION>>"


def an_agent():
    """A stock Agent, built the way the public constructor allows.

    `backend="litellm"` only so that construction stays offline: the openai
    backend probes the provider for rate-limit headers inside its constructor,
    which no grading suite is allowed to let happen.
    """
    return Agent(name="client", model_name="gpt-4o-mini", backend="litellm", system_prompt="You are a client.")


def test_rule__completion_signal(tmp_path):
    assert sym("COMPLETION_SENTINEL") == SENTINEL

    agent = an_agent()
    assert agent.is_completed(f"all set {SENTINEL}") is True
    assert agent.is_completed(SENTINEL) is True
    assert agent.is_completed("all set") is False


def test_scope__matching_discipline(tmp_path):
    agent = an_agent()
    require_feature(
        agent.is_completed(f"all set {SENTINEL}") is True,
        "Agent.is_completed's default sentinel match",
    )

    assert agent.is_completed(f"all set {SENTINEL}  \n") is True
    assert agent.is_completed(f"all set {SENTINEL}\t") is True
    assert agent.is_completed(f"{SENTINEL} but wait") is False
    assert agent.is_completed("all set <<end_of_conversation>>") is False
    assert agent.is_completed("all set") is False


def test_failure_behavior__non_text_replies(tmp_path):
    agent = an_agent()
    # An untouched Agent returns False for everything, so this constraint only
    # means something once the sentinel match exists at all.
    require_feature(
        agent.is_completed(f"all set {SENTINEL}") is True,
        "Agent.is_completed's default sentinel match",
    )

    assert agent.is_completed({"text": SENTINEL}) is False
    assert agent.is_completed(None) is False
    assert agent.is_completed([SENTINEL]) is False
    assert agent.is_completed(42) is False


def test_observability__final_turn_accounting(tmp_path):
    probe = an_agent()
    require_feature(
        probe.is_completed(f"all set {SENTINEL}") is True,
        "Agent.is_completed's default sentinel match",
    )

    last = f"Then index funds. {SENTINEL}"
    conversation = Conversation(
        replies=["Start with your goals.", "My goal is retirement in 20 years.", last],
        is_completed=probe.is_completed,
    )
    processor = conversation.processor(max_length=6)
    dataset = asyncio.run(processor.run(str(tmp_path)))

    assert len(conversation.calls) == 3, conversation.calls
    assert len(log_lines(tmp_path)) == 4
    assert read_field(processor.status_tracker, "num_responses") == 3
    assert read_field(processor.ledger, "responses") == 3
    assert read_field(processor.ledger, "completion_reason") == "agent_signal"
    assert read_field(processor.ledger, "completed") is True

    rows = [dict(row) for row in dataset]
    assert len(rows) == 4
    assert rows[-1]["content"] == last
    assert rows[-1]["role"] == PARTNER
