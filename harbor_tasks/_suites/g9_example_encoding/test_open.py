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
* a tokenizer with no `apply_chat_template` raises `TokenizerCapabilityError`,
  and one whose `apply_chat_template` or `encode` RAISES propagates unchanged —
  the fallback instruction.md:36 deletes;
* `FireworksDataFormatter.from_config` carries `max_context_length` into the
  formatter, falling back to 2048, and `to_jsonl_lines` validates roles too.

The worked example and the builders live here because `test_r1.py` and
`test_r2.py` drive the same objects.

HOW THE GRADED RUN DIFFERS. These files are the human-readable fact<->assertion
record and they use ONE worked conversation with its arithmetic written out. The
graded run does not: `probe.py` builds every scenario from
`fixture_spec.derive(seed)` with a seed root draws per run, and `judge.py`
recomputes the expected values for that draw. The POLICY asserted here and the
policy applied there are the same; only the numbers move. A fixed fixture was
forgeable — a pristine tree plus one `atexit` hook could emit the observations
that had always been correct.

The graded judge also enforces, from SOURCE against the pristine tree, the
preservation rules this ticket states and no behaviour can show:
`format_chat_messages`, `format_example`, `example_to_dict` and `write_jsonl` are
still the code curator had, the `if TINKER_AVAILABLE` Datum construction is
untouched (`tinker` is not installed here, so it is not even reachable), and
`tests/finetune/test_data_formatter.py` has only gained tests, and — the one
requirement no behaviour can reach, because building a `FireworksTrainer` wants a
live Fireworks account — that `fireworks_trainer.py` assigns `self.data_formatter`
through `from_config` and no longer by calling the class (instruction.md:74),
asked of the code the trainer RUNS: the assignment has to be reachable and is
followed through whatever helpers it calls, because the same line under
`if False:` or parked after a `return` scored every fact while the trainer went
on calling the class. Reachable means entered by a CALL and not merely named,
and an assignment is any spelling that stores the attribute — plain,
`setattr(self, "data_formatter", ...)` or `self.__dict__[...]` — because a
mention of an uncalled method, and a rebind by either of the other two
spellings, each scored every fact too. It
also checks that the whole chat text reaches `encode` with
`add_special_tokens=False`, and that the prefix-tokenization boundary trick
survived: `_supervised_spans` is declared with the ticket's parameters and still
renders the template both ways, the calls below prove it was the mechanism the
spans actually came from, and `DenseTokenizer` proves the boundaries were token
indices rather than character offsets that agree with them.
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
    DenseTokenizer,
    FakeTokenizer,
    FireworksDataFormatter,
    FireworksTrainerConfig,
    NoTemplateTokenizer,
    RaisingEncodeTokenizer,
    RaisingTemplateTokenizer,
    ShortHeaderTokenizer,
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

# After probe_support, which is what puts this directory on sys.path. The double
# and the judge render through this one definition, so the boundary-trick
# assertions below compare the same text the formatter saw. `TokenizerFailure` is
# what the raising doubles raise, and lives beside the templates for the same
# reason: the judge has to name it and cannot import probe_support.
from fixture_spec import TokenizerFailure, render_chat  # noqa: E402

# The worked conversation these human-readable tests document — INPUTS, not
# answers. The graded run does not use them: `probe.py` builds every scenario
# from `fixture_spec.derive(seed)`, and a record needs one concrete conversation
# with its arithmetic written out. `test_r1`/`test_r2` import them from here.
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
    assert isinstance(ALLOWED_ROLES, frozenset), "instruction.md:11 declares it a frozenset"
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

    # --- the boundary trick is reused, not replaced (instruction.md:39) -----
    # Each assistant turn's boundaries come from rendering the template twice —
    # up to the turn with a generation prompt, through the turn without one —
    # and from tokenizing both renders. Character offsets into this double's
    # text would be just as correct here and wrong for any real tokenizer, so
    # the calls themselves are the evidence, not the resulting numbers.
    encoded = {text for text, _ in tok.encode_calls}
    for index in (1, 3):
        assert ([list(pair) for pair in GOOD_PAIRS[:index]], True) in tok.template_calls
        assert ([list(pair) for pair in GOOD_PAIRS[: index + 1]], False) in tok.template_calls
        assert render_chat(GOOD_PAIRS[:index], True) in encoded
        assert render_chat(GOOD_PAIRS[: index + 1]) in encoded

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

    # --- the boundaries are token indices, not character offsets ------------
    # Under FakeTokenizer `len(text)` and `len(encode(text))` are the same
    # number, so arithmetic over the rendered text is indistinguishable from the
    # boundary trick — an implementation that rendered both prefixes, handed both
    # to `encode` and then sliced on `len(text)` scored every fact. DenseTokenizer
    # returns two ids per character, where the two disagree: the same conversation
    # is 182 tokens, and its assistant turns are the character spans [48, 59) and
    # [82, 91) doubled.
    dense = DataFormatter(max_seq_length=4096).to_tinker_datum(
        example(*GOOD_PAIRS), DenseTokenizer()
    )
    dense_encoding = encoding_of(dense)
    assert read_field(dense_encoding, "token_count") == 182
    assert read_field(dense_encoding, "window_start") == 0
    assert read_field(dense_encoding, "supervised_tokens") == 40
    assert [index for index, weight in enumerate(weights_of(dense)) if weight == 1.0] == (
        list(range(95, 117)) + list(range(163, 181))
    ), "the spans are [96, 118) and [164, 182), one index earlier after the causal shift"

    # --- a tokenizer that raises propagates unchanged (instruction.md:36) ---
    # The deleted `try/except Exception: weights = [1.0] * len(tokens)` fallback:
    # a formatter that cannot locate the assistant turns must not quietly train
    # on the prompt instead.
    for tok in (RaisingTemplateTokenizer(), RaisingEncodeTokenizer()):
        with pytest.raises(TokenizerFailure) as excinfo:
            DataFormatter(max_seq_length=40).to_tinker_datum(example(*GOOD_PAIRS), tok)
        assert str(excinfo.value) == TokenizerFailure.MESSAGE
        assert not isinstance(excinfo.value, EncodingError)

    # --- the role check comes first (instruction.md:34) ---------------------
    # An example that breaks both rules at once: bad roles AND a tokenizer with
    # no chat template. Only the ordering decides which error the caller sees.
    with pytest.raises(InvalidRoleSequenceError) as excinfo:
        DataFormatter(max_seq_length=40).to_tinker_datum(
            example(("user", "q"), ("system", "s"), ("assistant", "a")), NoTemplateTokenizer()
        )
    assert (excinfo.value.reason, excinfo.value.position) == ("misplaced_system", 1)

    # --- to_jsonl_lines validates the roles too (instruction.md:75) ---------
    with pytest.raises(InvalidRoleSequenceError) as excinfo:
        FireworksDataFormatter(max_seq_length=50).to_jsonl_lines(
            [example(*GOOD_PAIRS), example(("user", "q"), ("system", "s"), ("assistant", "a"))]
        )
    assert (excinfo.value.reason, excinfo.value.position) == ("misplaced_system", 1)

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
