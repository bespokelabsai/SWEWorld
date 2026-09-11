"""g9 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
helpers, so a value here is the value the test saw. The judge holds the
assertions those tests made (the counts, the `GOOD_TEXT`, the `(reason,
position)` pairs, the report defaults). A submission that returns forged values
only forges values the judge still checks against the real expectations — which
is implementing them. Floats go through `json` (float encoding is `repr`), so
every value round-trips to the identical double.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest. g9 is pure in-process: no provider socket,
# no /etc/hosts mapping, no monkeypatch — every call runs curator directly.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

# probe_support owns the curator imports, the doubles, the scenario inputs and
# the answer-free readers; reuse them so a probe calls curator exactly as the
# test does. Importing it here (its module body) runs the submission's
# `import bespokelabs.curator.finetune` — this process's whole purpose, and why
# it is disposable. The worker never imports test_open, whose source carries the
# expected answer literals (GOOD_TEXT and the assertion numbers).
import probe_support as S  # noqa: E402
from harness import read_field, surface  # noqa: E402


# The report's five counters, in the order the ticket names them. These are FIELD
# NAMES used to READ the report (like g11's STEP_PLAN_FIELDS in its worker), not
# an expected value: the field-ORDER assertion is made in judge.py against its
# own literal, over the observed `report_fields` list this worker records.
_REPORT_FIELDS = ("kept", "dropped", "windowed", "dropped_indices", "supervised_tokens")

# The exception attributes the g9 tests read. `hasattr` guards each, so only the
# ones a given error carries are recorded; `role_sequence` is materialised to a
# list so it round-trips through json.
_EXC_ATTRS = ("reason", "position", "role_sequence", "missing_method",
              "token_count", "max_seq_length", "retained_prompt_tokens", "num_messages")


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, its message, and
    whichever of the g9 error attributes it carries — the faithful stand-in for a
    `pytest.raises(T)` block that then reads `exc.value.<attr>`."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        for attr in _EXC_ATTRS:
            if hasattr(exc, attr):
                value = getattr(exc, attr)
                info[attr] = list(value) if attr == "role_sequence" else value
        return info
    return {"raised": False, "mro": []}


def report_vals(report) -> list:
    """The five report counters as a json-safe list; `dropped_indices` -> list."""
    values = [read_field(report, name) for name in _REPORT_FIELDS]
    values[3] = list(values[3])
    return values


def supervised(datum):
    return read_field(S.encoding_of(datum), "supervised_tokens")


# ---------------------------------------------------------------------------
# open feature — the whole stated surface (one fact)
# ---------------------------------------------------------------------------
def probe_open() -> dict:
    S.require_curator()
    import bespokelabs.curator.finetune as finetune

    (
        ALLOWED_ROLES,
        EncodingError,
        InvalidRoleSequenceError,
        TokenizerCapabilityError,
        validate_role_sequence,
    ) = S.encoding_names(
        "ALLOWED_ROLES",
        "EncodingError",
        "InvalidRoleSequenceError",
        "TokenizerCapabilityError",
        "validate_role_sequence",
    )

    o: dict = {}
    o["exports"] = [hasattr(finetune, name) for name in (
        "EncodingError", "InvalidRoleSequenceError", "TokenizerCapabilityError",
        "ALLOWED_ROLES", "validate_role_sequence")]
    o["allowed_roles"] = sorted(ALLOWED_ROLES)
    o["encoding_error_mro"] = [c.__name__ for c in EncodingError.__mro__]
    o["invalid_role_mro"] = [c.__name__ for c in InvalidRoleSequenceError.__mro__]
    o["tok_cap_mro"] = [c.__name__ for c in TokenizerCapabilityError.__mro__]

    # the five (reason, position) cases — the MESSAGE lists are inputs; the reason
    # and position are answers the judge holds, checked against what the error
    # reports here.
    case_msgs = [
        [],
        S.messages_of(("user", "q"), ("tool", "t"), ("assistant", "a")),
        S.messages_of(("user", "q"), ("system", "s"), ("assistant", "a")),
        S.messages_of(("system", "s"), ("user", "q"), ("user", "q2"), ("assistant", "a")),
        S.messages_of(("system", "s"), ("user", "q"), ("assistant", "a"), ("user", "q2")),
    ]
    o["role_cases"] = [raises(validate_role_sequence, msgs) for msgs in case_msgs]

    o["legal_returns_none"] = validate_role_sequence(
        S.messages_of(("user", "q"), ("assistant", "a"))) is None
    legal = S.example(("system", "s"), ("user", "q"), ("assistant", "a"))
    o["legal_example_none"] = validate_role_sequence(legal.messages) is None

    # the left window, and one encode call that never truncates
    tok = S.FakeTokenizer()
    formatter = S.DataFormatter(max_seq_length=40)
    datum = formatter.to_tinker_datum(S.example(*S.GOOD_PAIRS), tok)
    model_input = list(S.datum_part(datum, "model_input"))
    o["model_input"] = model_input
    o["model_input_len"] = len(model_input)
    o["model_input_19"] = model_input[19] if len(model_input) > 19 else None
    o["targets"] = S.targets_of(datum)
    o["targets_0"] = S.targets_of(datum)[0] if S.targets_of(datum) else None
    o["encode_kwarg_keys"] = [sorted(kwargs) for _, kwargs in tok.encode_calls]

    # the envelope
    metadata = S.datum_part(datum, "metadata")
    o["metadata_surface"] = surface(metadata)
    o["metadata_original_text"] = read_field(metadata, "original_text")
    o["metadata_num_messages"] = read_field(metadata, "num_messages")
    encoding = S.encoding_of(datum)
    o["encoding_surface"] = surface(encoding)
    o["enc_tokenizer_is_true"] = read_field(encoding, "tokenizer") is True
    o["enc_token_count"] = read_field(encoding, "token_count")
    o["enc_window_start"] = read_field(encoding, "window_start")
    o["enc_windowed_is_true"] = read_field(encoding, "windowed") is True

    # the no-tokenizer branch carries its text too
    plain = S.DataFormatter(max_seq_length=1024).to_tinker_datum(
        S.example(("user", "Hello"), ("assistant", "Hi there!")))
    o["plain_original_text"] = read_field(S.datum_part(plain, "metadata"), "original_text")
    o["plain_tokenizer_is_false"] = read_field(S.encoding_of(plain), "tokenizer") is False

    # a tokenizer with no chat template is refused, not worked around
    o["no_template"] = []
    for train_on_assistant_only in (True, False):
        fmt = S.DataFormatter(max_seq_length=40, train_on_assistant_only=train_on_assistant_only)
        o["no_template"].append(
            raises(fmt.to_tinker_datum, S.example(*S.GOOD_PAIRS), S.NoTemplateTokenizer()))

    # from_config carries max_context_length into the uploaded file
    made = S.FireworksDataFormatter.from_config(
        S.FireworksTrainerConfig(base_model=S.BASE_MODEL, max_context_length=100))
    o["made_is_fireworks"] = isinstance(made, S.FireworksDataFormatter)
    o["made_max_seq_length"] = made.max_seq_length
    o["made_train_on_assistant_only_is_true"] = made.train_on_assistant_only is True
    o["fallback_max_seq_length"] = S.FireworksDataFormatter.from_config(
        S.FireworksTrainerConfig(base_model=S.BASE_MODEL)).max_seq_length
    o["explicit_4096"] = S.FireworksDataFormatter.from_config(
        S.FireworksTrainerConfig(base_model=S.BASE_MODEL, max_context_length=4096)).max_seq_length
    return o


# ---------------------------------------------------------------------------
# r1 — how an example that does not fit is encoded
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    S.require_curator()
    tok = S.FakeTokenizer()
    datum = S.DataFormatter(max_seq_length=40).to_tinker_datum(S.example(*S.GOOD_PAIRS), tok)
    o = {
        "weights": S.weights_of(datum),
        "supervised_tokens": read_field(S.encoding_of(datum), "supervised_tokens"),
    }
    wide = S.DataFormatter(max_seq_length=50).to_tinker_datum(S.example(*S.GOOD_PAIRS), S.FakeTokenizer())
    o["wide_weights"] = S.weights_of(wide)
    o["wide_window_start"] = read_field(S.encoding_of(wide), "window_start")
    o["wide_supervised_tokens"] = read_field(S.encoding_of(wide), "supervised_tokens")
    return o


def probe_r1_scope() -> dict:
    S.require_curator()
    plain = S.example(("user", "Hello"), ("assistant", "Hi there!"))
    datum = S.DataFormatter(max_seq_length=1024).to_tinker_datum(plain)
    encoding = S.encoding_of(datum)
    o = {
        "plain_tokenizer_is_false": read_field(encoding, "tokenizer") is False,
        "plain_token_count": read_field(encoding, "token_count"),
        "plain_window_start": read_field(encoding, "window_start"),
        "plain_supervised_tokens": read_field(encoding, "supervised_tokens"),
        "plain_weights": S.weights_of(datum),
        "plain_model_input": list(S.datum_part(datum, "model_input")),
    }
    everything = S.DataFormatter(max_seq_length=1024, train_on_assistant_only=False)
    o["everything_weights"] = S.weights_of(everything.to_tinker_datum(plain))
    o["everything_supervised"] = read_field(
        S.encoding_of(everything.to_tinker_datum(plain)), "supervised_tokens")
    o["good_all_ones_weights"] = S.weights_of(
        S.DataFormatter(max_seq_length=40, train_on_assistant_only=False).to_tinker_datum(
            S.example(*S.GOOD_PAIRS), S.FakeTokenizer()))
    return o


def probe_r1_exclusions() -> dict:
    import json as _json
    S.require_curator()
    o = {"bytes_per_token": S.encoding_names("FIREWORKS_BYTES_PER_TOKEN")}

    fits = S.example(("user", "qqq"), ("assistant", "ok"))
    over = S.example(("user", "qqqqqq"), ("assistant", "ok"))
    lines = S.FireworksDataFormatter(max_seq_length=30).to_jsonl_lines([fits, over])
    o["lines"] = lines
    # decode here so the judge can compare structure without importing curator; the
    # raw line strings are recorded above so the judge can check the byte length.
    o["lines_decoded"] = [_json.loads(line) for line in lines]
    o["lines_byte_lens"] = [len(line.encode("utf-8")) for line in lines]

    accented = S.example(("user", "héllo wörld"), ("assistant", "ok"))
    o["accented_33"] = S.FireworksDataFormatter(max_seq_length=33).to_jsonl_lines([accented])
    kept = S.FireworksDataFormatter(max_seq_length=34).to_jsonl_lines([accented])
    o["accented_34"] = kept
    o["accented_34_decoded"] = [_json.loads(line) for line in kept]
    return o


def probe_r1_failure_behavior() -> dict:
    S.require_curator()
    ExampleTooLongError = S.encoding_names("ExampleTooLongError")
    o = {"example_too_long_mro": [c.__name__ for c in ExampleTooLongError.__mro__]}

    tok = S.FakeTokenizer()
    formatter = S.DataFormatter(max_seq_length=40)
    too_long = S.example(*S.TOO_LONG_PAIRS)
    o["too_long_error"] = raises(formatter.to_tinker_datum, too_long, tok)

    good = S.example(*S.GOOD_PAIRS)
    datum = formatter.to_tinker_datum(good, S.FakeTokenizer())
    o["good_window_start"] = read_field(S.encoding_of(datum), "window_start")

    o["short_window_error"] = raises(
        S.DataFormatter(max_seq_length=17).to_tinker_datum, good, S.FakeTokenizer())

    short = S.example(("user", "uu"), ("assistant", "bbbb"))
    unwindowed = S.DataFormatter(max_seq_length=1024).to_tinker_datum(short, S.ShortHeaderTokenizer())
    o["unwindowed_window_start"] = read_field(S.encoding_of(unwindowed), "window_start")
    o["unwindowed_token_count"] = read_field(S.encoding_of(unwindowed), "token_count")

    batch = S.DataFormatter(max_seq_length=40).format_batch([good, too_long], S.FakeTokenizer())
    o["batch_len"] = len(batch)
    o["batch0_num_messages"] = (
        read_field(S.datum_part(batch[0], "metadata"), "num_messages") if batch else None)
    return o


# ---------------------------------------------------------------------------
# r2 — what the formatter tells the caller it threw away
# ---------------------------------------------------------------------------
def _dropping_batch():
    """A formatter whose last pass kept one example and dropped one."""
    formatter = S.DataFormatter(max_seq_length=40)
    kept = formatter.format_batch(
        [S.example(*S.GOOD_PAIRS), S.example(*S.TOO_LONG_PAIRS)], S.FakeTokenizer())
    return formatter, kept


def probe_r2_rule() -> dict:
    import dataclasses
    S.require_curator()
    EncodingReport = S.encoding_names("EncodingReport")

    o = {
        "report_is_dataclass": dataclasses.is_dataclass(EncodingReport),
        "report_frozen_is_true": EncodingReport.__dataclass_params__.frozen is True,
        "report_fields": [f.name for f in dataclasses.fields(EncodingReport)],
        "default_report": report_vals(EncodingReport()),
    }

    formatter, kept = _dropping_batch()
    o["kept_is_list"] = isinstance(kept, list)
    o["kept_len"] = len(kept)
    o["report"] = report_vals(formatter.last_report)
    o["kept0_supervised"] = supervised(kept[0]) if kept else None

    clean = S.DataFormatter(max_seq_length=1024)
    data = clean.format_batch(
        [S.example(*S.GOOD_PAIRS), S.example(*S.TOO_LONG_PAIRS)], S.FakeTokenizer())
    o["clean_data_len"] = len(data)
    o["clean_report"] = report_vals(clean.last_report)
    o["clean_supervised_sum"] = supervised(data[0]) + supervised(data[1]) if len(data) == 2 else None

    fireworks = S.FireworksDataFormatter(max_seq_length=30)
    lines = fireworks.to_jsonl_lines(
        [S.example(("user", "qqq"), ("assistant", "ok")),
         S.example(("user", "qqqqqq"), ("assistant", "ok"))])
    o["fw_lines_is_list"] = isinstance(lines, list)
    o["fw_lines_len"] = len(lines)
    o["fw_report"] = report_vals(fireworks.last_report)
    return o


def probe_r2_scope() -> dict:
    S.require_curator()
    fresh = S.DataFormatter(max_seq_length=40)
    o = {"fresh_report": report_vals(fresh.last_report)}

    formatter, _ = _dropping_batch()
    after_batch = report_vals(formatter.last_report)
    o["after_batch"] = after_batch

    datum = formatter.to_tinker_datum(S.example(*S.GOOD_PAIRS), S.FakeTokenizer())
    o["datum_windowed_is_true"] = read_field(S.encoding_of(datum), "windowed") is True
    o["report_after_success"] = report_vals(formatter.last_report)

    o["raise_too_long"] = raises(
        formatter.to_tinker_datum, S.example(*S.TOO_LONG_PAIRS), S.FakeTokenizer())
    o["report_after_raise"] = report_vals(formatter.last_report)
    return o


def probe_r2_failure_behavior() -> dict:
    S.require_curator()
    formatter, _ = _dropping_batch()
    before = report_vals(formatter.last_report)
    o = {"before": before}

    bad_roles = S.example(("user", "q"), ("user", "q again"))
    o["raise_bad_roles"] = raises(
        formatter.format_batch,
        [S.example(*S.GOOD_PAIRS), S.example(*S.TOO_LONG_PAIRS), bad_roles], S.FakeTokenizer())
    o["report_after_bad_roles"] = report_vals(formatter.last_report)

    o["raise_bad_tok"] = raises(
        formatter.format_batch, [S.example(*S.GOOD_PAIRS)], S.NoTemplateTokenizer())
    o["report_after_bad_tok"] = report_vals(formatter.last_report)
    return o


# name -> probe. classname/name reproduce the current junit nodes so score.fold
# maps them to the identical fact keys.
PROBES = {
    "test_open::test_open_feature__roles_are_validated_and_an_over_long_example_keeps_its_completion": probe_open,
    "test_r1::test_rule__an_assistant_turn_the_window_cuts_in_half_is_not_supervised_at_all": probe_r1_rule,
    "test_r1::test_scope__the_tokenizer_free_branch_supervises_assistant_spans_from_character_offsets": probe_r1_scope,
    "test_r1::test_exclusions__fireworks_drops_over_budget_lines_by_utf8_bytes_and_truncates_nothing": probe_r1_exclusions,
    "test_r1::test_failure_behavior__a_windowed_example_with_under_sixteen_prompt_tokens_is_refused": probe_r1_failure_behavior,
    "test_r2::test_rule__both_batch_entry_points_publish_a_frozen_encoding_report": probe_r2_rule,
    "test_r2::test_scope__only_the_batch_entry_points_write_the_report": probe_r2_scope,
    "test_r2::test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report": probe_r2_failure_behavior,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        try:
            results[node] = {"ok": True, "obs": fn()}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
