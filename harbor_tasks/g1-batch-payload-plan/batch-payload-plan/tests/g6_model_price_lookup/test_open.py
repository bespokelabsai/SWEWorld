"""g6 — the openly stated feature: one canonical model-price lookup.

The ticket names every symbol this file touches: `ModelPrice`, `UnpricedModelError`,
`resolve_model_price`, `register_price_with_litellm`, `format_cost_strings`, the
`external_model_cost` shim, the deletion of `_get_litellm_cost_map`, and the two new
tracker fields plus `refresh_model_price`. Nothing here depends on r1's failure
precedence or r2's discount ownership; those are graded in their own files.

The helpers below are shared with `test_r1` / `test_r2` so the three files agree on how
the price tables are sandboxed. `litellm.model_cost` is a process-global dict that
`register_model` mutates in place, and both external cost processors memoise what they
have registered in a class-level set, so a test that writes into either leaks into every
test that runs after it. `pricing_sandbox()` restores both.
"""
from __future__ import annotations

import dataclasses

import pytest

from harness import read_field

# The answer-free helpers/inputs live in probe_support so the worker (probe.py)
# and this human reference share ONE definition and cannot drift. The expected
# VALUES this test asserts stay here (and in judge.py); probe_support holds none.
# test_r1/test_r2 do `from test_open import MAVERICK/DEEPSEEK/INFNET_8B/
# pricing_sandbox/require_cost`, so those names are re-exported through here.
from probe_support import (  # noqa: F401
    DEEPSEEK,
    INFNET_8B,
    MAVERICK,
    cost_mod,
    litellm,
    price_fields,
    pricing_sandbox,
    require_cost,
)


# =============================================================================
# open feature — one lookup, one failure type, one formatter, one shim
# =============================================================================
def test_open_feature__one_resolve_model_price_backs_the_price_the_error_the_registration_and_the_strings():
    ModelPrice, UnpricedModelError, resolve_model_price = require_cost("ModelPrice", "UnpricedModelError", "resolve_model_price")
    register_price_with_litellm, format_cost_strings, external_model_cost = require_cost(
        "register_price_with_litellm", "format_cost_strings", "external_model_cost"
    )

    # --- the return shape the ticket spells out -------------------------------
    assert dataclasses.is_dataclass(ModelPrice), "ModelPrice must be a dataclass"
    assert ModelPrice.__dataclass_params__.frozen is True, "ModelPrice must be frozen"
    assert {f.name for f in dataclasses.fields(ModelPrice)} == {
        "model",
        "provider",
        "completion_window",
        "input_cost_per_million",
        "output_cost_per_million",
        "source",
        "batch",
        "output_price_inferred",
        "max_tokens",
    }

    # --- the failure shape ----------------------------------------------------
    assert issubclass(UnpricedModelError, LookupError)
    assert isinstance(UnpricedModelError.REASONS, frozenset)
    # Drawn from REASONS, never spelled here. The ticket says only that REASONS
    # names "the permitted reason strings"; which strings those are is r1's, and a
    # naive build is free to invent its own. Hardcoding one made this assertion
    # grade a hidden fact: a build that spelled it `model_not_found` would raise
    # ValueError here and fail `open_feature`, and `ships()` refuses that outright
    # (`tg/bracket.py:173`) -- after both paid builds. g4 shipped green with the
    # same shape, on `previous_version`.
    reason = sorted(UnpricedModelError.REASONS)[0]
    err = UnpricedModelError(model="ghost", provider="klusterai", completion_window="24h", reason=reason)
    assert str(err) == f"{reason}: model='ghost' provider='klusterai' completion_window='24h'"
    assert (err.model, err.provider, err.completion_window, err.reason) == ("ghost", "klusterai", "24h", reason)
    with pytest.raises(ValueError):
        UnpricedModelError(model="m", provider=None, completion_window="*", reason="not_a_declared_reason")

    with pricing_sandbox():
        # --- the lookup itself ------------------------------------------------
        price = resolve_model_price(MAVERICK, provider="klusterai", completion_window="*")
        assert isinstance(price, ModelPrice)
        fields = price_fields(price)
        assert fields["model"] == MAVERICK
        assert fields["provider"] == "klusterai"
        assert fields["completion_window"] == "*"
        assert (fields["input_cost_per_million"], fields["output_cost_per_million"]) == (0.2, 0.8)
        assert fields["source"] == "external"
        assert fields["batch"] is False
        assert fields["output_price_inferred"] is False
        # round(0.2 / 1e6, 15) exactly, not the raw 2.0000000000000002e-07.
        assert price.input_cost_per_token == 2e-07
        assert price.output_cost_per_token == 8e-07

        # A table row with no output price mirrors the input price and says so.
        inferred = resolve_model_price(INFNET_8B, provider="inference.net", completion_window="24h")
        assert (read_field(inferred, "input_cost_per_million"), read_field(inferred, "output_cost_per_million")) == (0.045, 0.045)
        assert read_field(inferred, "output_price_inferred") is True

        # --- the back-compat shim --------------------------------------------
        assert external_model_cost(INFNET_8B, "24h", "inference.net") == {
            "input_cost_per_token": 4.5e-08,
            "output_cost_per_token": 4.5e-08,
        }
        assert not hasattr(cost_mod, "_get_litellm_cost_map"), "_get_litellm_cost_map was to be deleted"

        # --- the single writer into litellm's table ---------------------------
        entry = register_price_with_litellm(price)
        assert set(entry) == {"max_tokens", "input_cost_per_token", "output_cost_per_token", "litellm_provider"}
        assert entry["input_cost_per_token"] == 2e-07
        assert entry["output_cost_per_token"] == 8e-07
        assert litellm.model_cost[MAVERICK]["input_cost_per_token"] == 2e-07
        assert litellm.model_cost[MAVERICK]["output_cost_per_token"] == 8e-07
        with pytest.raises(ValueError):
            register_price_with_litellm(resolve_model_price(MAVERICK, provider="klusterai", completion_window="*", batch=True))

    # --- the single formatter -------------------------------------------------
    with pricing_sandbox():
        assert format_cost_strings(price, rich=False) == ("$0.200", "$0.800")
        assert format_cost_strings(price, rich=True) == ("[red]$0.200[/red]", "[red]$0.800[/red]")
        assert format_cost_strings(inferred, rich=False) == ("$0.045", "$0.045*")
        # The marker's position relative to the markup is NOT pinned. The ticket says
        # the "*" is appended to the output string and that rich wraps a string in
        # [red]…[/red]; it never says which happens first. `whole.md` P9 does put the
        # marker inside, and grading that here failed `open_feature` on a naive build
        # that wrapped the other way round — which `ships()` refuses outright
        # (`tg/bracket.py:173`), because a blind score cannot be read against an open
        # feature the ticket does not state. `rich=False` above still pins "$0.045*".
        inferred_rich = format_cost_strings(inferred, rich=True)
        assert inferred_rich[0] == "[red]$0.045[/red]"
        assert inferred_rich[1] in ("[red]$0.045*[/red]", "[red]$0.045[/red]*")
        assert format_cost_strings(None, rich=False) == ("N/A", "N/A")
        assert format_cost_strings(None, rich=True) == ("[dim]N/A[/dim]", "[dim]N/A[/dim]")

    # --- both trackers gained the same two fields and the same method ---------
    from bespokelabs.curator.status_tracker.batch_status_tracker import BatchStatusTracker
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker

    with pricing_sandbox():
        batch_tracker = BatchStatusTracker(model=INFNET_8B, compatible_provider="inference.net", completion_window="24h")
        inferred_online = OnlineStatusTracker(model=INFNET_8B, compatible_provider="inference.net")
        known_online = OnlineStatusTracker(model=MAVERICK, compatible_provider="klusterai")
        for tracker in (batch_tracker, inferred_online, known_online):
            assert callable(getattr(tracker, "refresh_model_price", None)), f"{type(tracker).__name__} has no refresh_model_price()"
            assert read_field(tracker, "price_unavailable_reason") is None
            # `-> Optional[str]` with a reason only on failure, so a success returns None
            # whether the method reports the reason back or only records it.
            assert tracker.refresh_model_price() is None
            assert read_field(tracker, "output_price_inferred") is (tracker is not known_online)

        # The per-million numbers are read off the ONLINE trackers: a batch tracker's
        # prices depend on which sources a batch run discounts, and that is r2's subject,
        # not the openly stated feature's.
        # CURATOR_DISABLE_RICH_DISPLAY=1 in conftest, so the strings are the plain ones.
        assert (inferred_online.input_cost_per_million, inferred_online.output_cost_per_million) == (0.045, 0.045)
        assert (inferred_online.input_cost_str, inferred_online.output_cost_str) == ("$0.045", "$0.045*")
        assert (known_online.input_cost_per_million, known_online.output_cost_per_million) == (0.2, 0.8)
        assert (known_online.input_cost_str, known_online.output_cost_str) == ("$0.200", "$0.800")
