"""t12 — hidden requirement r2: reuse the existing list, do not fork it.

    rule   the model-support list used for this check must be the same list
           maintained for the existing structured-output feature (the one
           already updated when new models like o3 are added) — this task must
           not introduce a second, separate list that could drift out of sync
    scope  reuse of the existing model-support list only

`rule` is graded behaviourally: change what the existing list reports and the
new check must change with it. `scope` is graded on the source, because "did
you add a second list" is a question about what was written, not about what
runs — and the two are different failures. A private copy that happens to agree
with litellm today passes `rule` and fails `scope`, which is exactly the drift
the requirement is worried about.

Untouched curator PASSES `rule`, and that is the honest reading rather than a
hole: baseline already calls `litellm.supports_response_schema`, so "use the
maintained list" is a property this codebase starts with. The earlier version
of this test made the baseline fail by asking only the constructor — which
graded WHEN the check runs, i.e. r1's claim, a second time. `scope` is where an
agent can still lose r2, and the naive fixture (its own list, refuses whatever
litellm says) fails `rule` here as it should.
"""
from __future__ import annotations

import re

import pytest

from harness import BASELINE, changed_source, code_only

from test_open import SUPPORTED, UNSUPPORTED, describer, rows

pytestmark = pytest.mark.timeout(180)


# =============================================================================
# rule — the same list, not a copy that agrees today
# =============================================================================
def test_rule__the_existing_support_list_is_what_is_consulted(monkeypatch, provider):
    """Flip the existing list the OTHER way: a supported model must now refuse.

    r1 already flips an unsupported model to supported. Doing the reverse here
    is deliberate — an implementation that short-circuits "known good names"
    before consulting anything passes that direction and fails this one.

    The whole path is driven, not just the constructor. r2 says WHICH list, and
    r1 says WHEN it is consulted; asking only the constructor merges them. A
    world-arm agent hung a correct, list-reusing check off
    `BaseRequestProcessor.run()` and this test reported "never consulted the
    maintained list" — r1's timing defect billed a second time against r2.
    """
    import litellm

    # A spy rather than a second construction. Building a SUPPORTED model
    # without a base_url makes curator run its own probe against the real
    # api.openai.com, which the verifier maps to localhost — so the reverse
    # direction died on a connection refusal that had nothing to do with the
    # requirement. The spy answers True for everything, so the run proceeds to
    # the fake provider wherever the implementation put its check.
    asked: list[str] = []

    def spy(model=None, **kw):
        asked.append(str(model))
        return True

    monkeypatch.setattr(litellm, "supports_response_schema", spy)
    # Every module that imported the name by value keeps its own reference.
    import sys
    for name, module in list(sys.modules.items()):
        if name.startswith("bespokelabs") and \
                getattr(module, "supports_response_schema", None) is not None:
            monkeypatch.setattr(module, "supports_response_schema", spy)
    llm = describer(UNSUPPORTED)                  # permitted, because spy says so
    try:
        llm(rows())
    except Exception:                             # noqa: BLE001
        pass                                      # only "was it asked" matters

    assert asked, (
        "nothing between construction and dispatch consulted "
        "litellm.supports_response_schema — the list curator already maintains "
        "for this. A private copy agreeing with it today drifts the next time "
        "a model is added, which is what the requirement forbids")
    assert any(UNSUPPORTED.split("-")[0] in a.lower() for a in asked), (
        f"the maintained list was consulted about {asked}, not about the model "
        f"under test ({UNSUPPORTED})")


# =============================================================================
# scope — no second list
# =============================================================================
def test_scope__no_second_model_list_was_introduced(monkeypatch):
    """"...must not introduce a second, separate list that could drift."

    Read from the source the agent changed, comments and docstrings stripped:
    a literal collection of model names is the thing the requirement forbids.
    Deliberately narrow — a single name in a condition is not a list, and
    flagging one would fail an implementation that special-cases nothing.
    """
    changed = changed_source()
    if not changed:
        pytest.fail("nothing in curator was changed, so the check cannot have "
                    "been moved to construction at all")

    # Three or more quoted model-ish names inside one bracketed literal is a
    # list; fewer is a condition.
    listish = re.compile(
        r"[\[\{\(]\s*(?:[\"'][\w.\-:/]*(?:gpt|o1|o3|claude|gemini|deepseek|"
        r"llama|mistral)[\w.\-:/]*[\"']\s*,\s*){2,}", re.I)
    # A file the agent merely touched may already have carried a list. Only a
    # list that is NOT in the baseline copy of the same file is theirs: the
    # first run of this test flagged litellm_online_request_processor.py for a
    # list that shipped with curator.
    offenders = []
    for name, body in changed.items():
        found = listish.search(body)
        if not found:
            continue
        base = BASELINE / name
        try:
            if base.exists() and found.group(0) in code_only(base.read_text()):
                continue                          # shipped with curator
        except OSError:
            pass
        offenders.append(name)
    offenders = sorted(offenders)
    assert not offenders, (
        f"{offenders} carries its own list of model names; the requirement "
        "says the existing maintained list is the one to use, because a second "
        "copy drifts out of sync the next time a model is added")
