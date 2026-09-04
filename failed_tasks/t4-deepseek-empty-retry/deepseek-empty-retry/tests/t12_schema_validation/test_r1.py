"""t12 — hidden requirement r1: the check moves to construction time.

    rule              checked against a maintained list of model name patterns,
                      once at LLM.__init__, not per-row at request time
    scope             LLM.__init__ only
    failure_behavior  an unsupported model + response_format must raise
                      ValueError immediately at construction, before __call__
                      ever touches the dataset

Baseline curator does this inside `run()` (`base_request_processor.py:138`), so
every test here fails on the pristine tree — which is what makes them decisive.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

from test_open import SUPPORTED, UNSUPPORTED, Answer, describer, rows

pytestmark = pytest.mark.timeout(180)


def _say(monkeypatch, verdict: bool) -> None:
    """Make every binding of the maintained list return `verdict`.

    `supports_response_schema` is imported by name in more than one curator
    module, so each holds an independent reference. Patching only
    `litellm.supports_response_schema` leaves those untouched.
    """
    import sys

    import litellm

    fake = lambda model=None, **kw: verdict          # noqa: E731
    monkeypatch.setattr(litellm, "supports_response_schema", fake)
    for name, module in list(sys.modules.items()):
        if not name.startswith("bespokelabs"):
            continue
        if getattr(module, "supports_response_schema", None) is not None:
            monkeypatch.setattr(module, "supports_response_schema", fake)


# =============================================================================
# rule — the verdict follows the model list, and is reached once
# =============================================================================
def test_rule__the_model_list_decides_and_it_is_consulted_at_construction(
        monkeypatch):
    """Two halves, because the sentence has two.

    "Checked against a maintained list of model name patterns" — flip what the
    list says and the verdict must flip with it. An implementation carrying its
    own hardcoded set of names passes every other test here and fails this one.

    "Once at `LLM.__init__`, not per-row at request time" — the flip has to be
    visible from construction alone, with no dataset in sight.
    """
    # As shipped: unsupported, so construction must refuse.
    with pytest.raises(Exception) as caught:
        describer(UNSUPPORTED)
    assert "valueerror" in type(caught.value).__name__.lower() or \
        isinstance(caught.value, ValueError), (
        f"construction refused with {type(caught.value).__name__}; the "
        "requirement asks for ValueError")

    # Now say the model IS supported. A check reading the maintained list sees
    # the change; one reading a private copy does not.
    #
    # Patched at EVERY binding, not just on the litellm module.
    # `litellm_online_request_processor.py` does `from litellm import
    # supports_response_schema` at import time, so it holds its own reference
    # and a patch on the module never reaches it. An agent reusing curator's
    # own `check_structured_output_support()` — which is the most faithful
    # reading of r2 — was failed by the narrower patch for doing the right
    # thing.
    _say(monkeypatch, True)
    try:
        describer(UNSUPPORTED)
    except Exception as exc:                      # noqa: BLE001
        pytest.fail(
            f"the model list was made to report {UNSUPPORTED} as supported and "
            f"construction still refused ({type(exc).__name__}: {exc}); the "
            "check is not reading the maintained list")


# =============================================================================
# scope — construction only, never per row
# =============================================================================
def test_scope__a_supported_model_is_not_re_checked_for_every_row(provider):
    """`scope` is "LLM.__init__ only", so a run must not re-validate per row.

    Measured at the provider: a supported model over three rows sends three
    requests. A per-row compatibility probe shows up as extra traffic, which is
    what the requirement's "not per-row at request time" forbids.
    """
    def traffic(n):
        provider.reset()
        llm = describer(SUPPORTED, backend="openai", backend_params={
            "base_url": provider.url("api.openai.com"),
            "in_mtok_cost": 1000, "out_mtok_cost": 1000})
        llm(rows(n))
        return provider.n

    # Two sizes, and the DIFFERENCE is what is graded. A flat count cannot be
    # used: with a base_url set, curator sends one existing compatibility probe
    # of its own (`_check_structured_output_support_via_api`), so three rows
    # legitimately produce four requests. Per-row checking shows up as the
    # count growing faster than the dataset, which subtracting removes any
    # argument about.
    small, large = traffic(3), traffic(6)
    assert large - small == 3, (
        f"3 rows sent {small} request(s) and 6 rows sent {large}: {large - small} "
        "more requests for 3 more rows. A compatibility check is running per "
        "row rather than once at construction")


# =============================================================================
# failure_behavior — ValueError, at construction, before the dataset
# =============================================================================
def test_failure_behavior__construction_itself_raises_value_error(provider):
    """"...immediately at construction, before `__call__` ever touches the
    dataset, so failures show up before any API spend."

    So the constructor is what must raise. Baseline curator gets here only on
    `__call__`, which is the behaviour this fact changes.
    """
    provider.reset()
    with pytest.raises(ValueError) as caught:
        describer(UNSUPPORTED)

    assert provider.n == 0, (
        f"{provider.n} request(s) reached the backend during construction")
    text = str(caught.value)
    assert text.strip(), "the ValueError carries no message"
