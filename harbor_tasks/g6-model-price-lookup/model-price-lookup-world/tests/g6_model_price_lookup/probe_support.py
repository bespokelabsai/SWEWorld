"""g6 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

This module holds ONLY the curator imports, scenario factories, fake input
tables and tolerant readers the probe needs to drive curator; it contains NO
expected-output value — no resolved per-million price, no per-token price, no
discount multiplier or ratio, none of the three reason strings, and no formatted
cost string. That is load-bearing: `run_split` copies this file into the
worker's jail, so it is inside the process that runs agent code — comments
included. If any reward-bearing expected value ever appears here, the worker can
read it and forge a passing `observations.json`. The answers live only in
`judge.py` (and, for humans, in `test_open.py`/`test_r1.py`/`test_r2.py`), which
the worker cannot read.

`LITELLM_ENTRY`, the fake litellm rows the probe plants, and
`fixed_completion_cost`'s pinned raw figure are INPUTS the scenario feeds in, not
answers: the worker must plant them to run the case at all, exactly as a header
value is an input in g10. The discriminating answer — the discount factor and the
resolved prices — is never here; a forger that knew only these inputs still could
not produce the discounted side of a ratio without implementing the discount.

`test_open.py` imports the subset it needs so there is a single definition of each
shared helper — the probe cannot drift from the reference. The r2-only helpers
(`multiplier`, `processors`, `discount_flag_name`, `fixed_completion_cost`,
`LITELLM_*`) serve the worker's r2 probes; `test_r2.py` keeps its own copies and
reaches nothing here.
"""
from __future__ import annotations

import contextlib
import copy

import pytest

from harness import read_field, surface

try:
    import litellm
except Exception:  # pragma: no cover - reported by require_cost(), per test
    litellm = None

try:
    from bespokelabs.curator import cost as cost_mod
except Exception:  # pragma: no cover - reported by require_cost(), per test
    cost_mod = None

# The three external-table rows the probes look up, named only by model id.
# These are model-id INPUTS (which model to ask for), never expected prices —
# the resolved numbers each carries live only in the judge, so this file (which
# the worker can read) reveals no answer. INFNET_8B is the one whose row lists no
# output price, so it exercises the inferred-output path.
MAVERICK = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
DEEPSEEK = "deepseek-ai/DeepSeek-R1"
INFNET_8B = "meta-llama/llama-3.1-8b-instruct/fp-8"


def require_cost(*names):
    """The named symbols out of `bespokelabs.curator.cost`, or a clear failure.

    Imported off the module rather than `from ... import`, so that a missing symbol is
    one legible failure in the test that needed it instead of a collection error that
    takes the whole file down with it.
    """
    if cost_mod is None:
        pytest.fail("bespokelabs.curator.cost does not import")
    missing = [n for n in names if not hasattr(cost_mod, n)]
    if missing:
        pytest.fail(f"bespokelabs.curator.cost has no {', '.join(missing)}; it exports {surface(cost_mod)}")
    out = [getattr(cost_mod, n) for n in names]
    return out[0] if len(out) == 1 else tuple(out)


def _memo_sets():
    """The cost processors' registration memos, wherever they exist."""
    out = []
    for name in ("_KlusterAICostProcessor", "_InferenceNetCostProcessor"):
        cls = getattr(cost_mod, name, None)
        memo = getattr(cls, "_registered_models", None)
        if isinstance(memo, set):
            out.append(memo)
    return out


@contextlib.contextmanager
def pricing_sandbox(add=None, drop=()):
    """Run with a scratch copy of litellm's price table and empty registration memos.

    `add` is merged into `litellm.model_cost`, `drop` removed from it. On the way out
    both the table and the memo sets are put back exactly as they were — the table by
    content rather than by rebinding the name, because an implementation may hold the
    dict under `from litellm import model_cost`.

    Deep copies throughout: `litellm.register_model` updates an existing row in place, so
    a shallow snapshot restores the outer dict while leaving the row it mutated changed,
    and inserting a module-level constant hands `register_model` that constant to edit.
    """
    original = litellm.model_cost
    before = copy.deepcopy(dict(original))
    memos = [(memo, set(memo)) for memo in _memo_sets()]
    for memo in _memo_sets():
        memo.clear()
    try:
        for key in drop:
            original.pop(key, None)
        original.update(copy.deepcopy(add or {}))
        yield original
    finally:
        for table in {id(original): original, id(litellm.model_cost): litellm.model_cost}.values():
            table.clear()
            table.update(copy.deepcopy(before))
        for memo, saved in memos:
            memo.clear()
            memo.update(saved)


def price_fields(price):
    """The nine numbers/strings a `ModelPrice` carries, read by name."""
    return {
        name: read_field(price, name)
        for name in (
            "model",
            "provider",
            "completion_window",
            "input_cost_per_million",
            "output_cost_per_million",
            "source",
            "batch",
            "output_price_inferred",
            "max_tokens",
        )
    }


# ---------------------------------------------------------------------------
# r2 inputs and readers — a fake litellm-only model and the discount helpers.
# ---------------------------------------------------------------------------
# A model that exists only in litellm's table, so that "litellm-sourced" is
# unambiguous. Its 2e-06/8e-06 are INPUT prices we plant, not the answer: the
# expected resolved per-million values and the discount are the judge's.
LITELLM_MODEL = "g6-litellm-priced-model"
LITELLM_ENTRY = {
    LITELLM_MODEL: {"input_cost_per_token": 2e-06, "output_cost_per_token": 8e-06, "max_tokens": 4096, "litellm_provider": "openai"},
    f"azure/{LITELLM_MODEL}": {"input_cost_per_token": 2e-06, "output_cost_per_token": 8e-06, "max_tokens": 4096, "litellm_provider": "azure"},
}


def fixed_completion_cost(monkeypatch, value=4.0):
    """Pin litellm's own cost computation, wherever the pricing module reached for it.

    `value` is an arbitrary raw figure the case multiplies against; the observed
    product and its ratio are what the judge checks, so the number is an input.
    """
    import bespokelabs.curator.cost as _cost_mod

    monkeypatch.setattr(litellm, "completion_cost", lambda **kwargs: value)
    if hasattr(_cost_mod, "completion_cost"):
        monkeypatch.setattr(_cost_mod, "completion_cost", lambda **kwargs: value)
    return value


def multiplier(processor):
    """`batch_multiplier()` off a processor, or a legible failure when there is none."""
    method = getattr(processor, "batch_multiplier", None)
    if not callable(method):
        pytest.fail(f"{type(processor).__name__} has no callable batch_multiplier(); the batch discount has no single owner")
    return method()


def processors():
    return require_cost("_LitellmCostProcessor", "_KlusterAICostProcessor", "_InferenceNetCostProcessor", "_AzureCostProcessor")


def discount_flag_name():
    """The class-level boolean that says whether a processor's prices are list prices.

    Discovered rather than named, and rather than oriented: r2 says the exemption is
    decided by a class-level flag, not what the flag is called or which way it points.

    Returns (name, applies_value) where `applies_value` is the value meaning "discount
    this class", or None when no such attribute exists.
    """
    base, kluster, infnet, _ = processors()
    for name, value in vars(base).items():
        if name.startswith("__") or not isinstance(value, bool):
            continue
        if getattr(kluster, name, "absent") is (not value) and getattr(infnet, name, "absent") is (not value):
            return name, value
    return None
