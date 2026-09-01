"""t4 — the openly stated feature: an empty DeepSeek completion is retried.

`base_url` is a real `api.deepseek.com` name mapped to loopback, so curator's
own detection branch (`if "api.deepseek.com" in self.url`) runs untouched and
its long-lived streaming reader handles the reply. Pointing this at 127.0.0.1
would silently disable the very thing the task grades.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

pytestmark = pytest.mark.timeout(240)

# Prices pinned so curator never asks litellm what a model costs. A bare
# "deepseek-chat" reaches litellm's price lookup with no provider prefix and
# every row dies with "LLM Provider NOT provided", which surfaces as "All
# requests failed" and fails every test here whatever the agent built. Both
# original t4 runs were lost that way.
PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}


class Asker(curator.LLM):
    def prompt(self, input):
        return f"Answer about {input['topic']}."


def one_row():
    return Dataset.from_list([{"topic": "cats"}])


def deepseek(provider, **params):
    return Asker(model_name="deepseek-chat", backend="openai",
                 backend_params={"base_url": provider.url("api.deepseek.com"),
                                 "max_retries": 3, **PRICES, **params})


def test_open_feature__an_empty_completion_is_retried(provider):
    provider.script = ["", "real answer"]
    result = deepseek(provider)(one_row())

    assert provider.n >= 2, (
        f"an empty completion from DeepSeek was accepted after {provider.n} "
        "request(s); the ticket asks for it to be retried")
    values = [str(v) for v in result.dataset[0].values()]
    assert any("real answer" in v for v in values), (
        f"the retry did not produce the good answer: {result.dataset[0]}")
