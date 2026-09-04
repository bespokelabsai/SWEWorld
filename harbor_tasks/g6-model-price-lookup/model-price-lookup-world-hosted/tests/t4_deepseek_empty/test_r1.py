"""t4 — hidden requirement r1: retry only DeepSeek, and say so when it fails.

    rule              an empty completion is re-queued through the existing
                      retry path, never surfaced to parse()
    scope             only when the resolved base_url points at DeepSeek
    failure_behavior  after max_retries, the error names DeepSeek and empty
                      responses, not a generic timeout

Pristine curator surfaces the empty string straight to `parse()` — verified
against the real provider, which returns `{'response': ''}` for a scripted
empty completion. That is the behaviour these tests reject.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import require_feature

pytestmark = pytest.mark.timeout(300)

PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}


class Asker(curator.LLM):
    """Records what parse() was handed — where an empty must never arrive."""

    seen: list = []

    def prompt(self, input):
        return f"Answer about {input['topic']}."

    def parse(self, input, response):
        Asker.seen.append(response)
        return [{"topic": input["topic"], "answer": response}]


def one_row(topic: str = "cats"):
    """Distinct rows per scenario.

    curator's run key does not include base_url, so a DeepSeek probe and a
    non-DeepSeek probe over the same prompt resolve to the same cache entry and
    the second is served without a request at all. The test then reads zero
    requests where it expected one and blames the backend.
    """
    return Dataset.from_list([{"topic": topic}])


def llm_for(provider, host, **params):
    Asker.seen = []
    return Asker(model_name="deepseek-chat", backend="openai",
                 backend_params={"base_url": provider.url(host),
                                 "max_retries": 3, **PRICES, **params})


# =============================================================================
# rule
# =============================================================================
def test_rule__an_empty_completion_is_requeued_and_never_reaches_parse(provider):
    """Two empties then a real answer: re-queued, and parse() never sees empty.

    The count is deliberately a lower bound. `rule` says the row is "re-queued
    using the backend's existing retry/backoff path" and fixes no number of
    attempts, so asserting exactly three failed an implementation that retries
    on its own budget — a correct implementation graded on a detail the
    requirement never stated.
    """
    provider.script = ["", "", "real answer"]
    llm_for(provider, "api.deepseek.com")(one_row())

    assert provider.n >= 2, (
        f"an empty completion from DeepSeek was not re-queued: the provider "
        f"saw {provider.n} request(s), so nothing was retried")
    assert "" not in [str(r) for r in Asker.seen], (
        f"parse() was handed an empty completion: {Asker.seen!r}")

    # "...re-queued using the backend's EXISTING retry/backoff path". That half
    # went ungraded: a bespoke loop that retries forever, or ignores the
    # caller's budget, passed everything above. The existing path is bounded by
    # max_retries, so a permanently empty endpoint must give up rather than
    # spin. Bounded loosely — the requirement fixes no count, and attempts vs
    # retries is an off-by-one nobody specified — so this fails only a retry
    # that is not on a budget at all.
    provider.reset()
    provider.body = ""                           # never recovers
    budget = 2
    llm = llm_for(provider, "api.deepseek.com", max_retries=budget,
                  require_all_responses=False)
    try:
        llm(one_row("bounded-probe"))
    except Exception:                            # noqa: BLE001 - failing is fine
        pass
    assert provider.n <= budget + 3, (
        f"a permanently empty DeepSeek endpoint was retried {provider.n} times "
        f"against max_retries={budget}; the retry is not running on the "
        "backend's existing budget")
    # And the "never surfaced to parse()" half, tested where it can actually
    # bite. Above, the retry succeeds and parse() only ever sees the good
    # answer, so that assertion is true of any implementation. Here the
    # endpoint never recovers: the row must FAIL rather than be handed to
    # parse() as though an empty string were a valid response.
    assert "" not in [str(r) for r in Asker.seen], (
        "after the retry budget was exhausted the empty completion was handed "
        f"to parse() as a valid response: {Asker.seen!r}")


# =============================================================================
# scope
# =============================================================================
def test_scope__other_openai_compatible_endpoints_are_unchanged(provider):
    """An empty string is valid content everywhere else.

    This is the half an agent guessing from the code gets wrong: retrying every
    empty completion looks like a strict improvement and changes behaviour for
    endpoints the ticket never mentioned.

    Gated on the DeepSeek retry existing: untouched curator retries nothing, so
    "it does not retry other endpoints" is true of it by omission, and this
    test passed on the pristine tree before the gate.
    """
    provider.script = ["", "real answer"]
    deepseek_retried = False
    try:
        llm_for(provider, "api.deepseek.com")(one_row("deepseek-probe"))
        deepseek_retried = provider.n >= 2
    except Exception:                            # noqa: BLE001
        deepseek_retried = False
    require_feature(deepseek_retried, "the DeepSeek empty-response retry")

    provider.reset()
    provider.script = ["", "real answer"]
    llm_for(provider, "api.openai.com")(one_row("openai-probe"))

    assert provider.n == 1, (
        f"a non-DeepSeek endpoint returned an empty completion and the backend "
        f"retried it anyway ({provider.n} requests); the requirement scopes "
        "this to DeepSeek")


# =============================================================================
# failure_behavior
# =============================================================================
def test_failure_behavior__exhausted_retries_name_deepseek_and_empty_responses(
        provider):
    """The error a user reads has to say what happened.

    A generic timeout after four silent retries is the failure this names: the
    user thinks the network is slow when the provider is returning nothing.
    """
    provider.body = ""                           # always empty
    llm = llm_for(provider, "api.deepseek.com", max_retries=2,
                  require_all_responses=False)

    message = ""
    try:
        response = llm(one_row())
        cache_dir = getattr(response, "cache_dir", None)
        if cache_dir:
            for path in pathlib.Path(str(cache_dir)).glob("responses*.jsonl"):
                for line in path.read_text().splitlines():
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    errors = row.get("response_errors") or row.get("error") or ""
                    if errors:
                        message += " " + str(errors)
    except Exception as exc:                     # noqa: BLE001 - also acceptable
        message = f"{type(exc).__name__}: {exc}"

    assert message.strip(), (
        "every attempt returned an empty completion and nothing recorded an "
        "error; the row failed silently")

    # The URL is `http://api.deepseek.com:PORT`, so a message that merely
    # echoes the endpoint contains "deepseek" without naming it as the CAUSE —
    # which is what the requirement asks for ("explicitly names DeepSeek and
    # empty-response retries as the cause"). Strip URLs and host names before
    # matching so the word has to be the error's own.
    prose = re.sub(r"https?://\S+|\b[\w.-]+\.(?:com|ai|io|net)\b", " ", message)
    assert re.search(r"deepseek", prose, re.I), (
        "the failure does not name DeepSeek as the cause — the only mention is "
        f"the endpoint it was talking to: {message[:300]!r}")
    assert re.search(r"empt", message, re.I), (
        f"the failure does not say the responses were empty: {message[:300]!r}")
    # "...names DeepSeek AND EMPTY-RESPONSE RETRIES as the cause". The retry
    # half went ungraded: a real submission said only "Received an empty
    # response from the API. Some providers, such as DeepSeek, ..." — a generic
    # sentence with no hint that attempts were made and exhausted, which is
    # exactly the "user thinks the network is slow" failure this fact exists to
    # prevent. The oracle says "...fails the row once the max_retries
    # empty-response retries are exhausted."
    assert re.search(r"retr(y|ie[sd])|attempt|exhaust", prose, re.I), (
        "the failure names an empty response but never says it was retried, so "
        "a user cannot tell attempts were made and exhausted: "
        f"{message[:300]!r}")
