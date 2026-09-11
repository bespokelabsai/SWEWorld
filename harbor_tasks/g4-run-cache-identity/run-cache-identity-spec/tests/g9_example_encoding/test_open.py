"""g9 — the openly stated feature: one typed encoding policy for chat examples.

The ticket states, and this file measures in one decisive test:

* `encoding.py` exists and its public names are exported from
  `bespokelabs.curator.finetune` — `ALLOWED_ROLES`, `EncodingError`,
  `InvalidRoleSequenceError`, `TokenizerCapabilityError`, `validate_role_sequence`;
* `validate_role_sequence` reports the five `(reason, position)` pairs the ticket
  spells out, in the order it spells them out;
* `to_tinker_datum` encodes once with no `truncation`/`max_length` and keeps the
  LAST `max_seq_length` tokens, so the completion survives;
* the dict envelope carries `metadata["original_text"]` on the tokenizer branch
  too, plus the five-key `metadata["encoding"]`;
* a tokenizer with no `apply_chat_template` raises `TokenizerCapabilityError`;
* `FireworksDataFormatter.from_config` carries `max_context_length` into the
  formatter, falling back to 2048.

The doubles and example builders live here because `test_r1.py` and `test_r2.py`
drive the same objects.
"""
from __future__ import annotations

import pytest

from harness import read_field, surface

# The answer-free doubles, inputs and readers live in probe_support so the worker
# (probe.py) and this human reference share ONE definition and cannot drift. The
# expected VALUE this test asserts — GOOD_TEXT — stays here (and in judge.py);
# probe_support holds no expected output.
from probe_support import (  # noqa: F401
    BASE_MODEL,
    DataFormatter,
    FakeTokenizer,
    FireworksDataFormatter,
    FireworksTrainerConfig,
    GOOD_PAIRS,
    NoTemplateTokenizer,
    ShortHeaderTokenizer,
    TOO_LONG_PAIRS,
    TrainingExample,
    datum_part,
    encoding_names,
    encoding_of,
    example,
    messages_of,
    require_curator,
    targets_of,
    weights_of,
)

GOOD_TEXT = "[user]" + "u" * 30 + "\n[assistant]" + "a" * 10 + "\n[user]vvvvv\n[assistant]bbbbbbbb\n"


def test_open_feature__roles_are_validated_and_an_over_long_example_keeps_its_completion():
    require_curator()

    (
        ALLOWED_ROLES,
        EncodingError,
        InvalidRoleSequenceError,
        TokenizerCapabilityError,
        validate_role_sequence,
    ) = encoding_names(
        "ALLOWED_ROLES",
        "EncodingError",
        "InvalidRoleSequenceError",
        "TokenizerCapabilityError",
        "validate_role_sequence",
    )

    # --- exports, which the ticket asks for by name -------------------------
    import bespokelabs.curator.finetune as finetune

    for name in (
        "EncodingError",
        "InvalidRoleSequenceError",
        "TokenizerCapabilityError",
        "ALLOWED_ROLES",
        "validate_role_sequence",
    ):
        assert hasattr(finetune, name), f"finetune/__init__.py does not export {name!r}"

    assert set(ALLOWED_ROLES) == {"system", "user", "assistant"}
    assert issubclass(EncodingError, ValueError)
    assert issubclass(InvalidRoleSequenceError, EncodingError)
    assert issubclass(TokenizerCapabilityError, EncodingError)

    # --- the five (reason, position) pairs, in the ticket's own order -------
    cases = [
        ([], "empty", 0),
        (messages_of(("user", "q"), ("tool", "t"), ("assistant", "a")), "unknown_role", 1),
        (messages_of(("user", "q"), ("system", "s"), ("assistant", "a")), "misplaced_system", 1),
        (
            messages_of(("system", "s"), ("user", "q"), ("user", "q2"), ("assistant", "a")),
            "non_alternating",
            2,
        ),
        (
            messages_of(("system", "s"), ("user", "q"), ("assistant", "a"), ("user", "q2")),
            "unterminated",
            3,
        ),
    ]
    for msgs, reason, position in cases:
        with pytest.raises(InvalidRoleSequenceError) as excinfo:
            validate_role_sequence(msgs)
        error = excinfo.value
        roles = [m["role"] for m in msgs]
        assert (error.reason, error.position) == (reason, position), (
            f"{roles} was reported as {(error.reason, error.position)}"
        )
        assert list(error.role_sequence) == roles
        assert str(error) == f"invalid role sequence at position {position} ({reason}): {roles}"

    # a legal conversation, with and without the leading system message, passes
    assert validate_role_sequence(messages_of(("user", "q"), ("assistant", "a"))) is None
    legal = example(("system", "s"), ("user", "q"), ("assistant", "a"))
    assert validate_role_sequence(legal.messages) is None

    # --- the left window, and one encode call that never truncates ----------
    tok = FakeTokenizer()
    formatter = DataFormatter(max_seq_length=40)
    datum = formatter.to_tinker_datum(example(*GOOD_PAIRS), tok)

    model_input = list(datum_part(datum, "model_input"))
    assert len(model_input) == 39
    # tokens[52:] survives, so the datum starts inside the first assistant turn
    # ('a' == 97) instead of at the head of the prompt ('u' == 117).
    assert targets_of(datum)[0] == 97
    assert model_input[19] == 10
    assert model_input == [ord(c) for c in GOOD_TEXT[51:-1]]
    assert targets_of(datum) == [ord(c) for c in GOOD_TEXT[52:]]
    assert all(
        "truncation" not in kwargs and "max_length" not in kwargs
        for _, kwargs in tok.encode_calls
    ), f"the tokenizer was asked to truncate: {[kw for _, kw in tok.encode_calls]}"

    # --- the envelope -------------------------------------------------------
    metadata = datum_part(datum, "metadata")
    assert set(surface(metadata)) == {"original_text", "num_messages", "encoding"}
    assert read_field(metadata, "original_text") == GOOD_TEXT
    assert read_field(metadata, "num_messages") == 4

    encoding = encoding_of(datum)
    assert set(surface(encoding)) == {
        "tokenizer",
        "token_count",
        "window_start",
        "windowed",
        "supervised_tokens",
    }
    assert read_field(encoding, "tokenizer") is True
    assert read_field(encoding, "token_count") == 91
    assert read_field(encoding, "window_start") == 51
    assert read_field(encoding, "windowed") is True

    # the no-tokenizer branch carries its text too
    plain = DataFormatter(max_seq_length=1024).to_tinker_datum(
        example(("user", "Hello"), ("assistant", "Hi there!"))
    )
    assert read_field(datum_part(plain, "metadata"), "original_text") == (
        "<|user|>\nHello\n<|assistant|>\nHi there!\n"
    )
    assert read_field(encoding_of(plain), "tokenizer") is False

    # --- a tokenizer with no chat template is refused, not worked around ----
    for train_on_assistant_only in (True, False):
        formatter = DataFormatter(max_seq_length=40, train_on_assistant_only=train_on_assistant_only)
        with pytest.raises(TokenizerCapabilityError) as excinfo:
            formatter.to_tinker_datum(example(*GOOD_PAIRS), NoTemplateTokenizer())
        assert excinfo.value.missing_method == "apply_chat_template"
        assert str(excinfo.value) == "tokenizer is missing required method 'apply_chat_template'"

    # --- from_config carries max_context_length into the uploaded file ------
    made = FireworksDataFormatter.from_config(
        FireworksTrainerConfig(base_model=BASE_MODEL, max_context_length=100)
    )
    assert isinstance(made, FireworksDataFormatter)
    assert made.max_seq_length == 100
    assert made.train_on_assistant_only is True
    assert (
        FireworksDataFormatter.from_config(FireworksTrainerConfig(base_model=BASE_MODEL)).max_seq_length
        == 2048
    )
    assert (
        FireworksDataFormatter.from_config(
            FireworksTrainerConfig(base_model=BASE_MODEL, max_context_length=4096)
        ).max_seq_length
        == 4096
    )
