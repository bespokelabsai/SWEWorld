"""g9 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

This module holds ONLY the curator imports, the tokenizer doubles, the scenario
INPUTS the ticket names, and the tolerant readers the probe needs to drive
curator; it contains NO expected-output value — no `GOOD_TEXT`, no token counts
(91, 51, ...), no supervised-token totals, no byte budgets, no `(reason,
position)` pairs, no `EncodingReport` defaults. That is load-bearing: `run_split`
copies this file into the worker's jail, which is the process that runs agent
code. If any reward-bearing expected value ever appears here, the worker can read
it and forge a passing `observations.json`. The answers live only in `judge.py`
(and, for humans, in `test_open.py`), which the worker cannot read.

`test_open.py` imports these names so there is a single definition of each helper
and input — the probe cannot drift from the reference. The `(role, content)`
message tuples, `GOOD_PAIRS`/`TOO_LONG_PAIRS` and the tokenizer choices are
INPUTS: the probe feeds them to curator and records what comes back.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict, List, Tuple

import pytest

from harness import read_field, surface

try:  # the whole point of the task; absent on an untouched checkout
    from bespokelabs.curator.finetune import (
        DataFormatter,
        FireworksDataFormatter,
        FireworksTrainerConfig,
        TrainingExample,
    )
except Exception:  # pragma: no cover - reported by the tests, not at collection
    DataFormatter = FireworksDataFormatter = FireworksTrainerConfig = TrainingExample = None

BASE_MODEL = "accounts/fireworks/models/llama-v3p1-8b-instruct"


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------
class FakeTokenizer:
    """One token per character, and a chat template with visible boundaries.

    The double the ticket itself specifies: `apply_chat_template` renders
    `[role]content\\n` per message and appends a bare `[assistant]` header when
    `add_generation_prompt=True`; `encode` returns one id per character and
    records how it was called.
    """

    def __init__(self) -> None:
        self.encode_calls: List[Tuple[str, Dict[str, Any]]] = []

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False) -> str:
        text = "".join(f"[{m['role']}]{m['content']}\n" for m in messages)
        return text + "[assistant]" if add_generation_prompt else text

    def encode(self, text, **kwargs):
        self.encode_calls.append((text, kwargs))
        return [ord(c) for c in text]


class ShortHeaderTokenizer(FakeTokenizer):
    """A template with a one-character generation header.

    Only needed where a test has to put the final assistant turn very close to
    the start of the sequence; `FakeTokenizer`'s `[assistant]` header alone is
    eleven characters, which is more prompt than some cases may have.
    """

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False) -> str:
        text = "".join(m["content"] for m in messages)
        return text + "A" if add_generation_prompt else text


class NoTemplateTokenizer:
    """A tokenizer that can encode but has no chat template at all."""

    def __init__(self) -> None:
        self.encode_calls: List[Tuple[str, Dict[str, Any]]] = []

    def encode(self, text, **kwargs):
        self.encode_calls.append((text, kwargs))
        return [ord(c) for c in text]


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------
def require_curator():
    """The finetune package, or a clear failure saying it did not import."""
    if DataFormatter is None:
        pytest.fail("bespokelabs.curator.finetune did not import the names this task adds")


def encoding_names(*names):
    """Public names of the encoding policy, from wherever the agent exports them.

    The package first, since the ticket asks for them in `finetune/__init__.py`,
    then the module — which file a constant is written in is not the fact being
    graded anywhere but in the export assertion below.
    """
    found = []
    package = importlib.import_module("bespokelabs.curator.finetune")
    try:
        module = importlib.import_module("bespokelabs.curator.finetune.encoding")
    except Exception:
        module = None
    for name in names:
        value = getattr(package, name, None)
        if value is None and module is not None:
            value = getattr(module, name, None)
        if value is None:
            pytest.fail(
                f"the encoding policy exposes no {name!r}; "
                f"bespokelabs.curator.finetune has {surface(package)}"
            )
        found.append(value)
    return found[0] if len(found) == 1 else tuple(found)


def example(*pairs):
    """A TrainingExample from (role, content) pairs."""
    return TrainingExample.from_dict_messages([{"role": r, "content": c} for r, c in pairs])


def messages_of(*pairs):
    return [{"role": r, "content": c} for r, c in pairs]


def datum_part(datum, *names):
    """A member of the returned envelope, by name, from a dict or an object."""
    return read_field(datum, *names)


def encoding_of(datum):
    return read_field(read_field(datum, "metadata"), "encoding")


def weights_of(datum):
    return list(read_field(read_field(datum, "loss_fn_inputs"), "weights"))


def targets_of(datum):
    return list(read_field(read_field(datum, "loss_fn_inputs"), "target_tokens"))


# ---------------------------------------------------------------------------
# The four messages the ticket's end-to-end section uses (INPUTS, not answers).
# ---------------------------------------------------------------------------
GOOD_PAIRS = (
    ("user", "u" * 30),
    ("assistant", "a" * 10),
    ("user", "v" * 5),
    ("assistant", "b" * 8),
)
TOO_LONG_PAIRS = (
    ("user", "u" * 10),
    ("assistant", "a" * 100),
)
