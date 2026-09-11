"""g6 — hidden requirement r1: the failure contract of `resolve_model_price`.

    rule       every failure is an `UnpricedModelError`, never a `ModelPrice` carrying a
               `None` price, and the vocabulary of reasons is exactly the three strings
               `unknown_provider`, `unknown_model`, `unknown_window`
    scope      the completion window is normalised BEFORE any lookup — `None` and `""`
               both become `"*"`, not the configured `"24h"` — so a `None` window never
               fails and the error, when there is one, carries the normalised value
    exclusions the reasons never compete and never leak into successes: the earlier check
               wins, a litellm row with a missing/`None` input price is a failure rather
               than a success with a `None` price, and an absent window is a failure
               rather than a quiet fall back to the wildcard tier
    observability the three named calls, and the swallow boundary: no `cost()` method and
               no tracker lets an `UnpricedModelError` out

`rule` deliberately never asserts WHICH reason a given call carries — that is `exclusions`'
and `observability`' subject — and `exclusions` uses inference.net rows where
`observability` uses klusterai ones, so the four are four measurements.
"""
from __future__ import annotations

import pytest

from harness import read_field

from test_open import DEEPSEEK, INFNET_8B, MAVERICK, pricing_sandbox, require_cost

try:
    from bespokelabs.curator.request_processor import _DEFAULT_COST_MAP
except Exception:  # pragma: no cover
    _DEFAULT_COST_MAP = None

try:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig
except Exception:  # pragma: no cover
    BatchRequestProcessorConfig = None

REASON_STRINGS = {"unknown_provider", "unknown_model", "unknown_window"}


def reason_of(excinfo):
    """The reason string off a raised error, by the name r1 fixes for it."""
    return read_field(excinfo.value, "reason")


# =============================================================================
# rule — a failure raises, and the reason vocabulary is exactly three strings
# =============================================================================
def test_rule__a_failure_always_raises_one_of_three_named_reasons_instead_of_a_none_price():
    resolve_model_price, UnpricedModelError = require_cost("resolve_model_price", "UnpricedModelError")

    assert set(UnpricedModelError.REASONS) == REASON_STRINGS

    # Every row of the external table resolves to two real, non-None floats. The lookup
    # has no "no price known" success value to fall into.
    with pricing_sandbox():
        checked = 0
        for provider, table in _DEFAULT_COST_MAP["external"]["providers"].items():
            for model, entry in table["cost"].items():
                for window in entry["input_cost_per_million"]:
                    price = resolve_model_price(model, provider=provider, completion_window=window)
                    for field in ("input_cost_per_million", "output_cost_per_million"):
                        value = read_field(price, field)
                        assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                            f"{provider}/{model}/{window}: {field} is {value!r}"
                        )
                    checked += 1
        assert checked > 0, "the external price table is empty; nothing was measured"

        # And every way of asking that the tables cannot answer is the one exception,
        # carrying one of the three declared reasons. Which one, is r1's other facts.
        unanswerable = [
            dict(model="ghost-model", provider="a-provider-nobody-registered"),
            dict(model="ghost-model", provider="klusterai"),
            dict(model=MAVERICK, provider="klusterai", completion_window="96h"),
            dict(model="ghost-model"),
        ]
        for call in unanswerable:
            with pytest.raises(UnpricedModelError) as excinfo:
                resolve_model_price(call.pop("model"), **call)
            assert reason_of(excinfo) in REASON_STRINGS, f"{reason_of(excinfo)!r} is not a declared reason"


# `scope` is no longer declared on r1. It graded the None/"" -> "*" window
# normalisation, which `naive` reproduced exactly, so the bracket read it
# `coincidence`. It is unhideable rather than badly cut: the ticket has to keep
# curator's existing `external_model_cost(model, completion_window="*", ...)`
# signature, which hands over the wildcard default. Dropping the field is what
# `declared_facts` allows — a smaller denominator, not a hole.


# =============================================================================
# exclusions — the checks do not compete, and neither leaks into a success
# =============================================================================
def test_exclusions__the_earlier_check_wins_and_neither_a_none_price_nor_a_wildcard_fallback_is_offered():
    resolve_model_price, UnpricedModelError = require_cost("resolve_model_price", "UnpricedModelError")

    with pricing_sandbox():
        # provider, model and window are all wrong at once: the provider check is first.
        with pytest.raises(UnpricedModelError) as excinfo:
            resolve_model_price("ghost-model", provider="a-provider-nobody-registered", completion_window="99h")
        assert reason_of(excinfo) == "unknown_provider"

        # provider is fine, model and window are both wrong: the model check is next.
        with pytest.raises(UnpricedModelError) as excinfo:
            resolve_model_price("ghost-model", provider="inference.net", completion_window="99h")
        assert reason_of(excinfo) == "unknown_model"

    # A litellm row that is present but unpriced is a failed lookup, not a success
    # carrying a None price — both for an explicit None and for an absent key.
    broken = {
        "g6-null-priced": {"input_cost_per_token": None, "output_cost_per_token": 4e-06, "max_tokens": 4096},
        "g6-unpriced": {"max_tokens": 4096, "litellm_provider": "openai"},
    }
    with pricing_sandbox(add=broken):
        for name in broken:
            with pytest.raises(UnpricedModelError) as excinfo:
                resolve_model_price(name)
            assert reason_of(excinfo) == "unknown_model", f"{name}: {reason_of(excinfo)!r}"

    # A window the row does not list does not quietly become the wildcard tier.
    with pricing_sandbox():
        wildcard = read_field(resolve_model_price(INFNET_8B, provider="inference.net", completion_window="*"), "input_cost_per_million")
        assert wildcard == 0.045
        with pytest.raises(UnpricedModelError) as excinfo:
            resolve_model_price(INFNET_8B, provider="inference.net", completion_window="72h")
        assert reason_of(excinfo) == "unknown_window"


# =============================================================================
# observability — the three named calls, and nothing above the lookup re-raises
# =============================================================================
def test_observability__the_three_reasons_read_back_and_every_caller_above_the_lookup_degrades():
    resolve_model_price, UnpricedModelError = require_cost("resolve_model_price", "UnpricedModelError")
    litellm_proc, kluster_proc, infnet_proc, azure_proc = require_cost(
        "_LitellmCostProcessor", "_KlusterAICostProcessor", "_InferenceNetCostProcessor", "_AzureCostProcessor"
    )
    from bespokelabs.curator.status_tracker.batch_status_tracker import BatchStatusTracker
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker

    with pricing_sandbox():
        seen = []
        for call in (
            dict(model="no-such-model", provider="not-a-provider", completion_window="96h"),
            dict(model="no-such-model", provider="klusterai", completion_window="96h"),
            dict(model=DEEPSEEK, provider="klusterai", completion_window="96h"),
        ):
            with pytest.raises(UnpricedModelError) as excinfo:
                resolve_model_price(call.pop("model"), **call)
            seen.append(reason_of(excinfo))
        assert seen == ["unknown_provider", "unknown_model", "unknown_window"]

    # Nothing above the lookup re-raises. Every cost processor degrades to 0.0 ...
    with pricing_sandbox():
        config = BatchRequestProcessorConfig(model="ghost-model", completion_window="24h")
        for processor_cls in (litellm_proc, kluster_proc, infnet_proc, azure_proc):
            for batch in (False, True):
                processor = processor_cls(config=config, batch=batch)
                assert processor.cost(completion_window="24h", prompt="a", completion="b") == 0.0, (
                    f"{processor_cls.__name__}(batch={batch}) did not degrade to 0.0"
                )

    # ... and both trackers degrade to None prices with the reason recorded.
    with pricing_sandbox():
        batch_tracker = BatchStatusTracker(model="ghost-model", compatible_provider="klusterai", completion_window="24h")
        online_tracker = OnlineStatusTracker(model="ghost-model", compatible_provider="klusterai")
        for tracker in (batch_tracker, online_tracker):
            name = type(tracker).__name__
            assert (tracker.input_cost_per_million, tracker.output_cost_per_million) == (None, None), name
            assert read_field(tracker, "price_unavailable_reason") == "unknown_model", name
            # Re-resolving a second unpriced model records the reason again rather than
            # letting the error out. What the method RETURNS is not r1's subject.
            tracker.refresh_model_price(price_model="also-a-ghost")
            assert read_field(tracker, "price_unavailable_reason") == "unknown_model", name
            assert (tracker.input_cost_per_million, tracker.output_cost_per_million) == (None, None), name
