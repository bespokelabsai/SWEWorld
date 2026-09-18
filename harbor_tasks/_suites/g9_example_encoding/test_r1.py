"""g9 — hidden requirement r1: how an example that does not fit is encoded.

    rule          an assistant span (s, e) is supervised only when s >= window_start;
                  a turn the window cuts in half is zeroed in full, while earlier turns
                  that survive whole are supervised normally
    scope         the tokenizer=None branch runs the same policy — spans from character
                  offsets with the `<|assistant|>` header INSIDE the span, and
                  `train_on_assistant_only` honoured — instead of its all-ones shortcut
    exclusions    the Fireworks jsonl path inherits the cap as a UTF-8 byte budget of
                  `max_seq_length * FIREWORKS_BYTES_PER_TOKEN` (3), drops on strict `>`,
                  and truncates nothing
    failure_behavior  `ExampleTooLongError` refuses a WINDOWED example whose final
                  assistant turn has fewer than 16 prompt tokens ahead of it; an
                  unwindowed example is never refused, and `format_batch` skips a
                  refused one and returns the others

Each measures one fact: `rule` uses examples that are never refused, `failure_behavior`
never inspects a weight vector, `scope` stays on the mock path and `exclusions` never
touches `DataFormatter`.

HOW THE GRADED RUN DIFFERS. These files are the human-readable fact<->assertion
record and they use ONE worked conversation with its arithmetic written out. The
graded run does not: `probe.py` builds every scenario from
`fixture_spec.derive(seed)` with a seed root draws per run, and `judge.py`
recomputes the expected values for that draw. The POLICY asserted here and the
policy applied there are the same; only the numbers move. A fixed fixture was
forgeable — a pristine tree plus one `atexit` hook could emit the observations
that had always been correct.
"""
from __future__ import annotations

import json

import pytest

from harness import read_field

from test_open import (
    GOOD_PAIRS,
    TOO_LONG_PAIRS,
    DataFormatter,
    FakeTokenizer,
    FireworksDataFormatter,
    ShortHeaderTokenizer,
    datum_part,
    encoding_names,
    encoding_of,
    example,
    require_curator,
    weights_of,
)


# =============================================================================
# rule — a half-retained assistant turn is not supervised at all
# =============================================================================
def test_rule__an_assistant_turn_the_window_cuts_in_half_is_not_supervised_at_all():
    require_curator()

    # 91 tokens, window_start 51, assistant spans (48, 59) and (82, 91). The first
    # span straddles the boundary; the second is inside it. Neither example here is
    # ever refused (31 prompt tokens survive), so this measures only the span rule.
    tok = FakeTokenizer()
    datum = DataFormatter(max_seq_length=40).to_tinker_datum(example(*GOOD_PAIRS), tok)

    weights = weights_of(datum)
    assert len(weights) == 39
    assert [i for i, w in enumerate(weights) if w == 1.0] == [30, 31, 32, 33, 34, 35, 36, 37, 38], (
        "the straddling span (48, 59) must contribute nothing, not its surviving tail"
    )
    assert sum(weights) == 9.0
    assert set(weights) == {0.0, 1.0}
    assert read_field(encoding_of(datum), "supervised_tokens") == 9

    # And an earlier turn that survives WHOLE is supervised normally: at
    # max_seq_length 50 the window starts at 41, so span (48, 59) is retained
    # entire and both turns count.
    wide = DataFormatter(max_seq_length=50).to_tinker_datum(example(*GOOD_PAIRS), FakeTokenizer())
    wide_weights = weights_of(wide)
    assert read_field(encoding_of(wide), "window_start") == 41
    assert read_field(encoding_of(wide), "supervised_tokens") == 20
    assert [i for i, w in enumerate(wide_weights) if w == 1.0] == (
        list(range(6, 17)) + list(range(40, 49))
    )


# =============================================================================
# scope — the no-tokenizer branch obeys the same policy
# =============================================================================
def test_scope__the_tokenizer_free_branch_supervises_assistant_spans_from_character_offsets():
    require_curator()

    # "<|user|>\nHello\n<|assistant|>\nHi there!\n" is 39 characters: token_count 9,
    # window_start 0, and the assistant span runs from 15 // 4 == 3 to 39 // 4 == 9,
    # i.e. the "<|assistant|>" header is inside the span on this path.
    plain = example(("user", "Hello"), ("assistant", "Hi there!"))
    datum = DataFormatter(max_seq_length=1024).to_tinker_datum(plain)

    encoding = encoding_of(datum)
    assert read_field(encoding, "tokenizer") is False
    assert read_field(encoding, "token_count") == 9
    assert read_field(encoding, "window_start") == 0
    assert read_field(encoding, "supervised_tokens") == 6, (
        "the mock path must honour train_on_assistant_only, with the header inside the span"
    )
    assert weights_of(datum) == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    assert list(datum_part(datum, "model_input")) == [0, 1, 2, 3, 4, 5, 6, 7]

    # And this path WINDOWS, like the tokenizer one — the half of the clause the
    # example above cannot show, because its budget is far wider than its
    # conversation. The repository's own test_max_seq_length
    # (tests/finetune/test_data_formatter.py), which instruction.md:83 says must
    # still pass, is this same shape: 1000 characters of prompt at
    # max_seq_length=50. A tree that windowed only the tokenizer path used to
    # score every fact while that test failed.
    long_prompt = example(("user", "x" * 1000), ("assistant", "Response"))
    windowed = DataFormatter(max_seq_length=50).to_tinker_datum(long_prompt)

    windowed_encoding = encoding_of(windowed)
    assert read_field(windowed_encoding, "token_count") == 258
    assert read_field(windowed_encoding, "window_start") == 208
    assert read_field(windowed_encoding, "windowed") is True
    assert read_field(windowed_encoding, "supervised_tokens") == 6
    assert list(datum_part(windowed, "model_input")) == list(range(208, 257))
    assert weights_of(windowed) == [0.0] * 43 + [1.0] * 6
    assert len(list(datum_part(windowed, "model_input"))) <= 50, (
        "test_max_seq_length asserts exactly this, and it is the repository's own test"
    )

    # train_on_assistant_only=False is all ones, here as on the tokenizer path.
    everything = DataFormatter(max_seq_length=1024, train_on_assistant_only=False)
    assert weights_of(everything.to_tinker_datum(plain)) == [1.0] * 8
    assert read_field(encoding_of(everything.to_tinker_datum(plain)), "supervised_tokens") == 9
    assert weights_of(
        DataFormatter(max_seq_length=40, train_on_assistant_only=False).to_tinker_datum(
            example(*GOOD_PAIRS), FakeTokenizer()
        )
    ) == [1.0] * 39


# =============================================================================
# exclusions_or_crossover — Fireworks gets a byte budget, and never truncates
# =============================================================================
def test_exclusions__fireworks_drops_over_budget_lines_by_utf8_bytes_and_truncates_nothing():
    require_curator()

    assert encoding_names("FIREWORKS_BYTES_PER_TOKEN") == 3

    # Serialized, these are 90 and 93 bytes; the budget at max_seq_length 30 is 90,
    # so the first is kept (strict >, not >=) and the second is dropped.
    fits = example(("user", "qqq"), ("assistant", "ok"))
    over = example(("user", "qqqqqq"), ("assistant", "ok"))
    lines = FireworksDataFormatter(max_seq_length=30).to_jsonl_lines([fits, over])

    assert len(lines) == 1, f"expected the 90-byte line and not the 93-byte one, got {lines}"
    assert json.loads(lines[0]) == {
        "messages": [{"role": "user", "content": "qqq"}, {"role": "assistant", "content": "ok"}]
    }, "the kept line must be whole: nothing on this path is truncated"
    assert len(lines[0].encode("utf-8")) == 90

    # Bytes, not characters: 98 characters but 100 UTF-8 bytes against a 99-byte
    # budget, so it goes.
    accented = example(("user", "héllo wörld"), ("assistant", "ok"))
    assert FireworksDataFormatter(max_seq_length=33).to_jsonl_lines([accented]) == []
    # ... and the same example fits when the budget is one token wider.
    kept = FireworksDataFormatter(max_seq_length=34).to_jsonl_lines([accented])
    assert len(kept) == 1 and json.loads(kept[0])["messages"][0]["content"] == "héllo wörld"


# =============================================================================
# failure_behavior — the retained-prompt floor
# =============================================================================
def test_failure_behavior__a_windowed_example_with_under_sixteen_prompt_tokens_is_refused():
    require_curator()

    ExampleTooLongError = encoding_names("ExampleTooLongError")
    EncodingError = encoding_names("EncodingError")
    assert issubclass(ExampleTooLongError, EncodingError)

    tok = FakeTokenizer()
    formatter = DataFormatter(max_seq_length=40)
    too_long = example(*TOO_LONG_PAIRS)

    with pytest.raises(ExampleTooLongError) as excinfo:
        formatter.to_tinker_datum(too_long, tok)
    error = excinfo.value
    assert isinstance(error, ValueError)
    assert error.token_count == 129
    assert error.max_seq_length == 40
    assert error.retained_prompt_tokens == 0
    assert error.num_messages == 2
    assert str(error) == (
        "example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would "
        "survive, minimum is 16"
    )

    # A windowed example with 31 prompt tokens ahead of its final turn is kept ...
    good = example(*GOOD_PAIRS)
    datum = formatter.to_tinker_datum(good, FakeTokenizer())
    assert read_field(encoding_of(datum), "window_start") == 51

    # ... and the same example is refused once only 8 of them would survive.
    with pytest.raises(ExampleTooLongError) as excinfo:
        DataFormatter(max_seq_length=17).to_tinker_datum(good, FakeTokenizer())
    assert excinfo.value.retained_prompt_tokens == 8
    assert excinfo.value.token_count == 91
    assert excinfo.value.num_messages == 4

    # An example that was never windowed is never refused, however short its
    # prompt: three prompt tokens, but window_start is 0.
    short = example(("user", "uu"), ("assistant", "bbbb"))
    unwindowed = DataFormatter(max_seq_length=1024).to_tinker_datum(short, ShortHeaderTokenizer())
    assert read_field(encoding_of(unwindowed), "window_start") == 0
    assert read_field(encoding_of(unwindowed), "token_count") == 6

    # format_batch skips the refused row and returns the others.
    batch = DataFormatter(max_seq_length=40).format_batch([good, too_long], FakeTokenizer())
    assert len(batch) == 1
    assert read_field(datum_part(batch[0], "metadata"), "num_messages") == 4
