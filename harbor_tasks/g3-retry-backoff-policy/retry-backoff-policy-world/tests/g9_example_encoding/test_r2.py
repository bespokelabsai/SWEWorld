"""g9 — hidden requirement r2: what the formatter tells the caller it threw away.

    rule       a frozen `EncodingReport(kept, dropped, windowed, dropped_indices,
               supervised_tokens)` with those defaults, in that order, reassigned
               wholesale by `format_batch` and by `to_jsonl_lines` after a complete
               pass — both of which still return a plain list
    scope      only the batch entry points write it: `to_tinker_datum` never touches
               `last_report`, on success or on a raise, and a fresh formatter carries
               the all-defaults report
    failure_behavior  `format_batch` absorbs only the over-long refusal;
               `InvalidRoleSequenceError` and `TokenizerCapabilityError` abort the pass
               and leave `last_report` at its pre-call value

`rule` never pins `supervised_tokens` to a number — it checks that the report's sum
matches what the kept datum itself reports, which is r2's fact rather than r1's.
"""
from __future__ import annotations

import dataclasses

import pytest

from harness import read_field, require_feature

from test_open import (
    GOOD_PAIRS,
    TOO_LONG_PAIRS,
    DataFormatter,
    FakeTokenizer,
    FireworksDataFormatter,
    NoTemplateTokenizer,
    datum_part,
    encoding_names,
    encoding_of,
    example,
    require_curator,
)

FIELDS = ("kept", "dropped", "windowed", "dropped_indices", "supervised_tokens")


def report_tuple(report):
    """The five counters of a report, whatever container holds them."""
    values = [read_field(report, name) for name in FIELDS]
    values[3] = tuple(values[3])
    return tuple(values)


def dropping_batch():
    """A formatter whose last pass kept one example and dropped one."""
    formatter = DataFormatter(max_seq_length=40)
    kept = formatter.format_batch(
        [example(*GOOD_PAIRS), example(*TOO_LONG_PAIRS)], FakeTokenizer()
    )
    return formatter, kept


# =============================================================================
# rule — the report, its shape, and the two entry points that publish it
# =============================================================================
def test_rule__both_batch_entry_points_publish_a_frozen_encoding_report():
    require_curator()

    EncodingReport = encoding_names("EncodingReport")

    # The declared shape: exactly these fields, in this order, with these defaults.
    assert dataclasses.is_dataclass(EncodingReport)
    assert EncodingReport.__dataclass_params__.frozen is True
    assert tuple(f.name for f in dataclasses.fields(EncodingReport)) == FIELDS
    # the defaults, read off an argument-less instance so that a `default_factory`
    # spelling counts as the same design
    assert report_tuple(EncodingReport()) == (0, 0, 0, (), 0)

    # format_batch: one kept, one dropped, and the drop recorded by input position.
    formatter, kept = dropping_batch()
    assert isinstance(kept, list), "format_batch still returns a plain list"
    assert len(kept) == 1

    report = formatter.last_report
    assert read_field(report, "kept") == 1
    assert read_field(report, "dropped") == 1
    assert read_field(report, "windowed") == 1
    assert tuple(read_field(report, "dropped_indices")) == (1,)
    # supervised_tokens sums the KEPT examples only; compare against what the one
    # surviving datum says about itself rather than to a number r1 owns.
    assert read_field(report, "supervised_tokens") == read_field(
        encoding_of(kept[0]), "supervised_tokens"
    )

    # A pass that drops nothing and windows nothing.
    clean = DataFormatter(max_seq_length=1024)
    data = clean.format_batch([example(*GOOD_PAIRS), example(*TOO_LONG_PAIRS)], FakeTokenizer())
    assert len(data) == 2
    assert report_tuple(clean.last_report) == (2, 0, 0, (), 
        read_field(encoding_of(data[0]), "supervised_tokens")
        + read_field(encoding_of(data[1]), "supervised_tokens"))

    # to_jsonl_lines: the same report, by dataclass equality, with the two
    # tokenizer-only counters at zero.
    fireworks = FireworksDataFormatter(max_seq_length=30)
    lines = fireworks.to_jsonl_lines(
        [example(("user", "qqq"), ("assistant", "ok")), example(("user", "qqqqqq"), ("assistant", "ok"))]
    )
    assert isinstance(lines, list) and len(lines) == 1
    assert fireworks.last_report == EncodingReport(
        kept=1, dropped=1, windowed=0, dropped_indices=(1,), supervised_tokens=0
    )


# =============================================================================
# scope — to_tinker_datum never writes the report
# =============================================================================
def test_scope__only_the_batch_entry_points_write_the_report():
    require_curator()

    # A freshly built formatter carries the all-defaults report.
    fresh = DataFormatter(max_seq_length=40)
    assert report_tuple(fresh.last_report) == (0, 0, 0, (), 0)

    formatter, _ = dropping_batch()
    after_batch = report_tuple(formatter.last_report)
    # Guard the negative: "to_tinker_datum leaves it alone" credits nothing unless
    # something writes it in the first place.
    require_feature(after_batch != (0, 0, 0, (), 0), "format_batch writing self.last_report")

    ExampleTooLongError = encoding_names("ExampleTooLongError")

    # A successful single-example call does not touch it ...
    datum = formatter.to_tinker_datum(example(*GOOD_PAIRS), FakeTokenizer())
    assert read_field(encoding_of(datum), "windowed") is True
    assert report_tuple(formatter.last_report) == after_batch

    # ... and neither does one that raises.
    with pytest.raises(ExampleTooLongError):
        formatter.to_tinker_datum(example(*TOO_LONG_PAIRS), FakeTokenizer())
    assert report_tuple(formatter.last_report) == after_batch


# =============================================================================
# failure_behavior — only the over-long refusal is absorbed
# =============================================================================
def test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report():
    require_curator()

    InvalidRoleSequenceError = encoding_names("InvalidRoleSequenceError")
    TokenizerCapabilityError = encoding_names("TokenizerCapabilityError")

    formatter, _ = dropping_batch()
    before = report_tuple(formatter.last_report)
    require_feature(before != (0, 0, 0, (), 0), "format_batch writing self.last_report")
    assert before[1] == 1, "the over-long example must be absorbed as a drop, not raised"

    bad_roles = example(("user", "q"), ("user", "q again"))
    with pytest.raises(InvalidRoleSequenceError):
        formatter.format_batch(
            [example(*GOOD_PAIRS), example(*TOO_LONG_PAIRS), bad_roles], FakeTokenizer()
        )
    assert report_tuple(formatter.last_report) == before, (
        "an aborted pass must not write a partial report"
    )

    with pytest.raises(TokenizerCapabilityError):
        formatter.format_batch([example(*GOOD_PAIRS)], NoTemplateTokenizer())
    assert report_tuple(formatter.last_report) == before
