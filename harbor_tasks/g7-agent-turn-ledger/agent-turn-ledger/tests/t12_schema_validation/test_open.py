"""t12 — the openly stated feature: reject an incompatible response_format early.

The ticket asks for validation "before sending any request to a backend", with
a clear message. Untouched curator already refuses — `base_request_processor`
raises `ValueError` inside `run()` — so this test is passed by the baseline on
purpose. It separates "built nothing" from "built it and missed the hidden
facts"; WHEN the refusal happens is r1's business, not the ticket's.

No `base_url` anywhere in this suite's construction-time tests. The check the
task moves reaches litellm only when `base_url` is None; with one set, curator
probes the provider instead (`_check_structured_output_support_via_api`), which
is a different code path and not the one the requirement talks about. Nothing
here needs a network: a constructor that raises never opens a socket.
"""
from __future__ import annotations

import pytest
from datasets import Dataset
from pydantic import BaseModel

from bespokelabs import curator

pytestmark = pytest.mark.timeout(180)

# litellm knows this one has no structured-output support, and it is not a
# name anybody would special-case by hand.
UNSUPPORTED = "babbage-002"
SUPPORTED = "gpt-4o-mini"


class Answer(BaseModel):
    text: str


def describer(model, **kw):
    class Describer(curator.LLM):
        response_format = Answer

        def prompt(self, input):
            return f"Describe {input['topic']}."

    return Describer(model_name=model, **kw)


def rows(n=2):
    return Dataset.from_list([{"topic": f"s{i}"} for i in range(n)])


def test_open_feature__an_incompatible_response_format_is_refused(provider):
    """It must fail, it must say why, and no row may reach the backend."""
    provider.reset()
    message = ""
    try:
        llm = describer(UNSUPPORTED)
        llm(rows())
    except Exception as exc:                      # noqa: BLE001 - the point
        message = f"{type(exc).__name__}: {exc}"

    assert message, (
        f"a response_format against {UNSUPPORTED}, which does not support "
        "structured output, was accepted without complaint")
    assert provider.n == 0, (
        f"{provider.n} request(s) went to the backend before the incompatible "
        "response_format was refused; the ticket asks for this to be caught "
        "before any request is sent")
    low = message.lower()
    assert UNSUPPORTED.split("-")[0] in low or "structured" in low or \
        "response_format" in low or "response format" in low, (
        f"the refusal does not say what was wrong: {message[:200]!r}")
