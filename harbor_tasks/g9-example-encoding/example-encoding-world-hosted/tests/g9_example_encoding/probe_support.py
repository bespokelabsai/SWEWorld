"""g9 — the answer-free scenario helpers the worker (probe.py) drives curator with.

This module holds ONLY the curator imports, the tokenizer doubles, and the
tolerant readers the probe needs to drive curator; it contains NO expected-output
value — no rendered chat text, no token counts, no supervised-token totals, no
byte budgets, no `(reason, position)` pairs, no `EncodingReport` defaults. That is
load-bearing: `run_split` copies this file into the worker's jail, which is the
process that runs agent code. If any reward-bearing expected value ever appears
here, the worker can read it and forge a passing `observations.json`. The answers
live only in `judge.py`, which the worker cannot read.

The graded run's scenario inputs are NOT here either: they are drawn per run in
`fixture_spec.derive(seed)`, because a fixed fixture let a tree that implemented
nothing emit the one set of observations that had always been correct. The
templates the doubles below render come from `fixture_spec` for the same reason
`judge.py` imports it — the judge has to know what the untruncated sequence was,
and a second copy of a template whose character counts decide every expected
token index would drift on the first edit.

Nothing here is a verdict: a double records how it was called, a reader returns
what it read, and what any of it SHOULD have been is worked out in `judge.py`
from the same seed.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Dict, List, Tuple

import pytest

from harness import read_field, surface

# In the jail `fixture_spec.py` sits beside this file and on the worker's
# PYTHONPATH; under pytest in `_suites` neither is true, so make the directory
# importable either way rather than leaving the reference tests uncollectable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402

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
        # Every `apply_chat_template` call, as the messages it was handed and the
        # flag it was handed them with. Recorded because instruction.md:39 reuses
        # the prefix-tokenization boundary trick, and only the calls themselves
        # show that the spans came from that mechanism rather than from offsets
        # tailored to this particular template — which is equally correct here
        # and wrong for every real tokenizer. No expected value: which calls
        # SHOULD have been made is worked out in `judge.py` from the seed.
        self.template_calls: List[Tuple[List[List[str]], bool]] = []

    def _render(self, pairs, add_generation_prompt: bool) -> str:
        return fixture_spec.render_chat(pairs, add_generation_prompt)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False) -> str:
        pairs = [(m["role"], m["content"]) for m in messages]
        self.template_calls.append(
            ([[role, content] for role, content in pairs], bool(add_generation_prompt)))
        return self._render(pairs, add_generation_prompt)

    def encode(self, text, **kwargs):
        self.encode_calls.append((text, kwargs))
        return [ord(c) for c in text]


class ShortHeaderTokenizer(FakeTokenizer):
    """A template with a one-character generation header.

    Only needed where a test has to put the final assistant turn very close to
    the start of the sequence; `FakeTokenizer`'s `[assistant]` header alone is
    eleven characters, which is more prompt than some cases may have. Only the
    rendering differs, so it overrides `_render` rather than
    `apply_chat_template` — an override of the caller would drop the call
    recording that the boundary-trick check reads.
    """

    def _render(self, pairs, add_generation_prompt: bool) -> str:
        return fixture_spec.render_short_header(pairs, add_generation_prompt)


class DenseTokenizer(FakeTokenizer):
    """Two ids per character, so a token index is NOT a character offset.

    Under `FakeTokenizer` `len(text)` and `len(encode(text))` are the same
    number, and an implementation that rendered both prefixes, handed both to
    `encode`, threw the ids away and sliced on `len(text)` scored every fact: it
    satisfies "the calls were made" while the span boundaries never came off the
    token sequence. Here the two disagree by a factor of two, so only a boundary
    read from the encoded length is right. Only `encode` differs, so the template
    rendering and the call recording the boundary-trick check reads are the
    inherited ones.
    """

    def encode(self, text, **kwargs):
        self.encode_calls.append((text, kwargs))
        return [ord(char) for char in text for _ in range(2)]


class RaisingTemplateTokenizer(FakeTokenizer):
    """`apply_chat_template` is callable, and raises.

    instruction.md:36: the all-ones fallback is deleted, so this has to reach the
    caller as itself. Callable on purpose — a tokenizer with no template at all
    is a different rule (`TokenizerCapabilityError`) and `NoTemplateTokenizer`
    already covers it.
    """

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        raise fixture_spec.TokenizerFailure(fixture_spec.TokenizerFailure.MESSAGE)


class RaisingEncodeTokenizer(FakeTokenizer):
    """The template renders; `encode` raises. The other half of the same rule."""

    def encode(self, text, **kwargs):
        raise fixture_spec.TokenizerFailure(fixture_spec.TokenizerFailure.MESSAGE)


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
