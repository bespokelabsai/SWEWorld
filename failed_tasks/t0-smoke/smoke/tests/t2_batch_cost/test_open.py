"""t2 — the openly stated feature: an estimate reaches the terminal first.

"Before any requests are submitted to the provider" is an ordering claim, and
`openai_batch_sentinel` turns it into one that can be checked rather than
believed: the first upload raises, so anything printed before the exception is
pre-flight by construction. A test that merely looked for a number in the output
would pass an agent who printed the estimate afterwards.
"""
from __future__ import annotations

import re

import pytest
from datasets import Dataset

from bespokelabs import curator

pytestmark = pytest.mark.timeout(180)

MODEL = "gpt-4o-mini"
MONEY = re.compile(r"\$?\s*\d+(?:[.,]\d+)?")


class Describer(curator.LLM):
    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


def test_open_feature__an_estimate_is_printed_before_submission(
        openai_batch_sentinel, capfd):
    llm = Describer(model_name=MODEL, backend="openai", batch=True,
                    backend_params={"batch_check_interval": 1})
    rows = Dataset.from_list([{"topic": t} for t in ("cats", "dogs", "birds")])

    with pytest.raises(BaseException):
        llm(rows)

    out = capfd.readouterr()
    text = out.out + out.err
    assert MONEY.search(text), (
        "nothing that looks like a cost reached the terminal before the first "
        f"upload. What was printed:\n{text[-1500:]}")
    assert re.search(r"cost|estimat|price|spend", text, re.I), (
        "a number was printed but nothing identifies it as a cost estimate; "
        f"output was:\n{text[-1500:]}")
