"""t4 — hidden requirement r2: no new public knob, detection from the URL.

    rule                    detection is inferred from the configured base_url
                            alone, with no caller-supplied flag
    scope                   the special-casing lives inside the backend's
                            response handling
    exclusions_or_crossover no new public backend_params key like `is_deepseek`

Both negative facts are gated on the feature existing. Untouched curator
satisfies "no new knob" by having done nothing, and three of these tests passed
on the pristine tree before that gate existed.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import changed_source, require_feature

pytestmark = pytest.mark.timeout(300)

PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}
BASELINE = pathlib.Path("/opt/world-state/input/curator")
CONFIG_REL = "src/bespokelabs/curator/request_processor/config.py"
SUSPECT = re.compile(r"deep.?seek|empty|retry_empty|is_deepseek", re.I)


def baseline_init_params() -> set:
    """`LLM.__init__`'s parameters in the tree the world shipped.

    Diffed rather than pattern-matched, for the same reason as the config
    fields: the contract is that no NEW input is needed, and a new parameter
    breaks it whatever it is called.
    """
    import ast
    import pathlib
    src = pathlib.Path("/opt/world-state/input/curator/src/bespokelabs/"
                       "curator/llm/llm.py")
    if not src.exists():
        return set()
    try:
        tree = ast.parse(src.read_text())
    except (OSError, SyntaxError):
        return set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "LLM":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    a = item.args
                    names = {x.arg for x in a.args + a.kwonlyargs + a.posonlyargs}
                    if a.vararg:
                        names.add(a.vararg.arg)
                    if a.kwarg:
                        names.add(a.kwarg.arg)
                    return names
    return set()


class Asker(curator.LLM):
    def prompt(self, input):
        return f"Answer about {input['topic']}."


def one_row():
    return Dataset.from_list([{"topic": "cats"}])


def retry_works(provider) -> bool:
    """Does an empty DeepSeek completion actually get retried?"""
    provider.reset()
    provider.script = ["", "real answer"]
    llm = Asker(model_name="deepseek-chat", backend="openai",
                backend_params={"base_url": provider.url("api.deepseek.com"),
                                "max_retries": 3, **PRICES})
    try:
        llm(one_row())
    except Exception:                            # noqa: BLE001
        return False
    return provider.n >= 2


def baseline_fields(*class_names: str) -> set[str]:
    """Config fields the world shipped with, read from the pristine tree.

    Parsed with `ast` rather than imported: two copies of `bespokelabs` in one
    interpreter is a trap, and `src/bespokelabs/__init__.py` is a regular
    package so only one of them can win.
    """
    path = BASELINE / CONFIG_REL
    if not path.exists():
        pytest.skip(f"no pristine tree at {BASELINE} to compare against")
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target,
                                                                  ast.Name):
                    found.add(stmt.target.id)
    return found


# =============================================================================
# rule
# =============================================================================
def test_rule__detection_comes_from_the_resolved_base_url_alone(
        provider, monkeypatch):
    """No base_url in backend_params — only OPENAI_BASE_URL in the environment.

    `OpenAIOnlineRequestProcessor.__init__` resolves `self.url` from
    config.base_url, then the environment, then the default. An agent who keyed
    the special case off the `backend_params` value rather than the resolved
    URL passes every other test here and fails this one.
    """
    monkeypatch.setenv("OPENAI_BASE_URL", provider.url("api.deepseek.com"))
    provider.script = ["", "real answer"]

    llm = Asker(model_name="deepseek-chat", backend="openai",
                backend_params={"max_retries": 3, **PRICES})
    llm(one_row())

    assert provider.n >= 2, (
        "the endpoint was DeepSeek by environment rather than by "
        f"backend_params and the empty completion was not retried "
        f"({provider.n} request). Detection is not reading the resolved URL.")

    # "...must live ENTIRELY INSIDE the openai-compatible backend's
    # response-handling path". Also ungraded until now: an implementation that
    # taught llm.py or the config about DeepSeek passed everything else.
    # Checked leniently — any file under request_processor/ is the backend, so
    # a helper beside the processor is fine; only DeepSeek knowledge leaking
    # into the LLM front end or the config fails.
    stray = sorted(name for name, body in changed_source().items()
                   if "deepseek" in body.lower()
                   and not name.startswith("request_processor/"))
    assert not stray, (
        f"DeepSeek is named outside the backend, in {stray}; the requirement "
        "says the special-casing lives entirely inside the openai-compatible "
        "backend's response-handling path")


# =============================================================================
# scope
# =============================================================================
def test_scope__no_caller_supplied_flag_is_needed(provider):
    """The caller says nothing about DeepSeek; the backend works it out.

    Gated on the retry existing, then asserts the only inputs used are the ones
    the ticket's contract allows: base_url, api_key, max_retries.
    """
    require_feature(retry_works(provider), "the DeepSeek empty-response retry")

    live = set(inspect.signature(curator.LLM.__init__).parameters)
    added = sorted(live - baseline_init_params())
    assert not added, (
        f"curator.LLM.__init__ gained parameter(s) {added}; the caller was not "
        "supposed to have to say anything for the backend to work this out")


# =============================================================================
# exclusions_or_crossover
# =============================================================================
def test_exclusions__no_new_public_backend_param(provider):
    """`extra = "forbid"` is what makes this checkable.

    A new knob has to be declared as a field to be usable, so "did the agent
    widen the public surface?" is a question the config answers itself.
    """
    require_feature(retry_works(provider), "the DeepSeek empty-response retry")

    from bespokelabs.curator.request_processor.config import (
        OnlineRequestProcessorConfig)

    # ANY new public field, not just a suspiciously named one. The
    # requirement says "existing backend_params (base_url, api_key,
    # max_retries) are the only inputs" — so a knob called `provider_quirks`
    # or `treat_blank_as_error` breaks the contract exactly as `is_deepseek`
    # would, and matching on the word "deepseek" let those through.
    added = sorted(set(OnlineRequestProcessorConfig.model_fields)
                   - baseline_fields("OnlineRequestProcessorConfig",
                                     "RequestProcessorConfig"))
    assert not added, (
        f"the config gained public field(s) {added}; the ticket's contract is "
        "that the existing backend_params are the only inputs and detection is "
        "internal")

    with pytest.raises(Exception):
        Asker(model_name="deepseek-chat", backend="openai",
              backend_params={"base_url": provider.url("api.deepseek.com"),
                              "is_deepseek": True, **PRICES})
