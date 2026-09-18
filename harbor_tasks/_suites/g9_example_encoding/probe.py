"""g9 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks /tests to root), turns
those values into the verdict. This is the split that closed the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report.

WHAT THE SPLIT ALONE DID NOT BUY, and this file is the half that pays for it.
Separating the processes stopped the worker rewriting the verdict. It did not
stop the worker INVENTING the values the verdict is computed from, and g9's were
the same every run — the same four messages, the same `max_seq_length=40`, the
same 91/51/`[30..38]`, all of them also written down in the world the agent is
told to read. Pristine `main` plus one import-time `atexit` hook that overwrote
this file's output scored every fact. So:

  * **the inputs are re-drawn every run** from the seed root chose
    (`fixture_spec.derive`), and nothing here knows what the answers for this
    run are — the judge recomputes them from the same seed;
  * **nothing below is a verdict**, and the few booleans left are identity
    checks on values the ticket fixes (`tokenizer is True`), never a claim about
    a policy.

One probe per graded fact, named for the node `score.py` folds it into; what each
one has to have produced is worked out in the matching `judge_*`. Floats go
through `json` (float encoding is `repr`), so every value round-trips to the
identical double.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# Bound BEFORE the submission is imported, and called instead of returning from
# main(). Interpreter shutdown runs `atexit` hooks the submission registered at
# import — which is how the observations file used to be overwritten. Leaving
# through `os._exit` never reaches them. This is a lock on one door, not the fix:
# a hook can patch `open` and edit the file as it is written. What makes forged
# values worthless is that they are not knowable in advance.
_EXIT = os._exit

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

# probe_support owns the curator imports, the doubles and the answer-free
# readers, so every probe drives curator through one definition of each helper.
# Importing it here (its module body) runs the submission's
# `import bespokelabs.curator.finetune` — this process's whole purpose, and why
# it is disposable. Nothing the worker can import holds an expected value.
import fixture_spec  # noqa: E402
import probe_support as S  # noqa: E402
from harness import read_field, surface  # noqa: E402

# This run's inputs; filled in by main() before any probe runs.
SPEC: dict = {}

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


def pairs(name: str):
    """One of this run's message lists, as `(role, content)` tuples."""
    return [tuple(pair) for pair in SPEC[name]]


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


def encoding_vals(datum) -> dict:
    """The five encoding fields plus the envelope, as the judge wants to read
    them: raw values, no comparison."""
    encoding = S.encoding_of(datum)
    metadata = S.datum_part(datum, "metadata")
    return {
        "encoding_surface": surface(encoding),
        "tokenizer_is_true": read_field(encoding, "tokenizer") is True,
        "tokenizer_is_false": read_field(encoding, "tokenizer") is False,
        "token_count": read_field(encoding, "token_count"),
        "window_start": read_field(encoding, "window_start"),
        "windowed": read_field(encoding, "windowed"),
        # separately, because json cannot tell 1 from True after the fact and the
        # ticket says this field is a bool
        "windowed_is_bool": isinstance(read_field(encoding, "windowed"), bool),
        "supervised_tokens": read_field(encoding, "supervised_tokens"),
        "metadata_surface": surface(metadata),
        "original_text": read_field(metadata, "original_text"),
        "num_messages": read_field(metadata, "num_messages"),
        "model_input": list(S.datum_part(datum, "model_input")),
        "targets": S.targets_of(datum),
        "weights": S.weights_of(datum),
    }


def encode_calls(tok) -> list:
    """Every `encode` call the double saw: the text, and the keywords it was
    passed. Values that are not json scalars are recorded as their repr, because
    what the judge checks is which keywords were used, not what an exotic one
    held."""
    out = []
    for text, kwargs in tok.encode_calls:
        clean = {key: (value if isinstance(value, (bool, int, float, str, type(None)))
                       else repr(value))
                 for key, value in kwargs.items()}
        out.append([text, clean])
    return out


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
    # instruction.md:11 declares it a frozenset, not just a container with those
    # three strings in it; json cannot tell one collection from another after the
    # fact, so the type is read here.
    o["allowed_roles_is_frozenset"] = isinstance(ALLOWED_ROLES, frozenset)
    o["encoding_error_mro"] = [c.__name__ for c in EncodingError.__mro__]
    o["invalid_role_mro"] = [c.__name__ for c in InvalidRoleSequenceError.__mro__]
    o["tok_cap_mro"] = [c.__name__ for c in TokenizerCapabilityError.__mro__]

    # this run's five malformed sequences, in the ticket's order. The judge works
    # out which rule each one breaks first and at which index.
    o["role_cases"] = [raises(validate_role_sequence, S.messages_of(*[tuple(m) for m in msgs]))
                       for msgs in SPEC["role_cases"]]

    o["legal_returns_none"] = validate_role_sequence(
        S.messages_of(*pairs("legal_messages"))) is None
    legal = S.example(*pairs("legal_example"))
    o["legal_example_none"] = validate_role_sequence(legal.messages) is None

    # the left window, the envelope, and one encode call that never truncates
    tok = S.FakeTokenizer()
    formatter = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"])
    datum = formatter.to_tinker_datum(S.example(*pairs("good")), tok)
    o["good"] = encoding_vals(datum)
    o["encode_calls"] = encode_calls(tok)
    # Which prefixes the chat template was rendered for, and with which
    # generation-prompt flag. The judge works out from the seed which calls the
    # boundary trick has to have made for THIS run's conversation; a list of
    # calls is an observation, not a verdict.
    o["template_calls"] = [[messages, flag] for messages, flag in tok.template_calls]

    # The same conversation under a tokenizer that returns two ids per character,
    # so a character offset is not a token index. Rendering both prefixes and
    # handing both to `encode` satisfies the boundary-trick call check even if the
    # ids are then thrown away and the spans sliced on `len(text)`; only this
    # geometry separates the two.
    dense_tok = S.DenseTokenizer()
    o["dense"] = encoding_vals(
        S.DataFormatter(max_seq_length=SPEC["dense_max_seq_length"]).to_tinker_datum(
            S.example(*pairs("good")), dense_tok))
    o["dense_encode_calls"] = encode_calls(dense_tok)

    # instruction.md:36 — with the all-ones fallback deleted, a tokenizer that
    # raises while spans are computed reaches the caller as itself. Both halves:
    # the template raising, and `encode` raising.
    o["template_raises"] = raises(
        S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"]).to_tinker_datum,
        S.example(*pairs("good")), S.RaisingTemplateTokenizer())
    o["encode_raises"] = raises(
        S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"]).to_tinker_datum,
        S.example(*pairs("good")), S.RaisingEncodeTokenizer())

    # instruction.md:34 — validation happens FIRST THING, which is observable on
    # an example that breaks both rules at once: a malformed sequence handed to a
    # tokenizer with no chat template must report the roles, not the tokenizer.
    o["roles_before_tokenizer"] = raises(
        S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"]).to_tinker_datum,
        S.example(*pairs("bad_roles")), S.NoTemplateTokenizer())

    # instruction.md:75 — the Fireworks path validates role sequences too, and
    # the role error is propagated rather than the example being skipped.
    o["jsonl_bad_roles"] = raises(
        S.FireworksDataFormatter(
            max_seq_length=SPEC["fw_report_max_seq_length"]).to_jsonl_lines,
        [S.example(*pairs("legal_example")), S.example(*pairs("bad_roles"))])

    # the no-tokenizer branch carries its text too
    plain = S.DataFormatter(max_seq_length=SPEC["plain_max_seq_length"]).to_tinker_datum(
        S.example(*pairs("plain")))
    o["plain"] = encoding_vals(plain)

    # a tokenizer with no chat template is refused, not worked around
    o["no_template"] = []
    for train_on_assistant_only in (True, False):
        fmt = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"],
                              train_on_assistant_only=train_on_assistant_only)
        o["no_template"].append(
            raises(fmt.to_tinker_datum, S.example(*pairs("good")), S.NoTemplateTokenizer()))

    # from_config carries max_context_length into the uploaded file
    made = S.FireworksDataFormatter.from_config(
        S.FireworksTrainerConfig(base_model=S.BASE_MODEL,
                                 max_context_length=SPEC["context_small"]))
    o["made_is_fireworks"] = isinstance(made, S.FireworksDataFormatter)
    o["made_max_seq_length"] = made.max_seq_length
    o["made_train_on_assistant_only_is_true"] = made.train_on_assistant_only is True
    o["fallback_max_seq_length"] = S.FireworksDataFormatter.from_config(
        S.FireworksTrainerConfig(base_model=S.BASE_MODEL)).max_seq_length
    o["large_max_seq_length"] = S.FireworksDataFormatter.from_config(
        S.FireworksTrainerConfig(base_model=S.BASE_MODEL,
                                 max_context_length=SPEC["context_large"])).max_seq_length
    return o


# ---------------------------------------------------------------------------
# r1 — how an example that does not fit is encoded
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    S.require_curator()
    narrow = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"]).to_tinker_datum(
        S.example(*pairs("good")), S.FakeTokenizer())
    wide = S.DataFormatter(max_seq_length=SPEC["wide_max_seq_length"]).to_tinker_datum(
        S.example(*pairs("good")), S.FakeTokenizer())
    return {"narrow": encoding_vals(narrow), "wide": encoding_vals(wide)}


def probe_r1_scope() -> dict:
    S.require_curator()
    plain = S.example(*pairs("plain"))
    o = {"plain": encoding_vals(
        S.DataFormatter(max_seq_length=SPEC["plain_max_seq_length"]).to_tinker_datum(plain))}

    everything = S.DataFormatter(max_seq_length=SPEC["plain_max_seq_length"],
                                 train_on_assistant_only=False)
    o["everything"] = encoding_vals(everything.to_tinker_datum(plain))
    o["windowed_all_ones"] = encoding_vals(
        S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"],
                        train_on_assistant_only=False).to_tinker_datum(
            S.example(*pairs("good")), S.FakeTokenizer()))

    # The same branch under a budget NARROWER than its conversation. The
    # scenario above is drawn far wider than its own, so it never windows; this
    # one is the only place a tokenizer-free window is observed at all.
    o["plain_windowed"] = encoding_vals(
        S.DataFormatter(max_seq_length=SPEC["plain_windowed_max_seq_length"]).to_tinker_datum(
            S.example(*pairs("plain_windowed"))))
    return o


def probe_r1_exclusions() -> dict:
    import json as _json
    S.require_curator()
    o = {"bytes_per_token": S.encoding_names("FIREWORKS_BYTES_PER_TOKEN")}

    # This run's ladder of examples, whose serialised lines cover a band of
    # lengths, ascii and multi-byte. The raw lines are recorded: the judge
    # decides which of them should have survived.
    examples = [S.example(*[tuple(m) for m in msgs]) for msgs in SPEC["fw_examples"]]
    lines = S.FireworksDataFormatter(
        max_seq_length=SPEC["fw_max_seq_length"]).to_jsonl_lines(examples)
    o["lines"] = lines
    # decoded here so the judge can compare structure without importing curator;
    # the raw line strings are recorded above so it can check the byte lengths.
    o["lines_decoded"] = [_json.loads(line) for line in lines]
    o["lines_byte_lens"] = [len(line.encode("utf-8")) for line in lines]
    return o


def probe_r1_failure_behavior() -> dict:
    S.require_curator()
    ExampleTooLongError = S.encoding_names("ExampleTooLongError")
    o = {"example_too_long_mro": [c.__name__ for c in ExampleTooLongError.__mro__]}

    formatter = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"])
    o["too_long_error"] = raises(
        formatter.to_tinker_datum, S.example(*pairs("too_long")), S.FakeTokenizer())

    good = S.example(*pairs("good"))
    o["good_window_start"] = read_field(
        S.encoding_of(formatter.to_tinker_datum(good, S.FakeTokenizer())), "window_start")

    # the same conversation under a window that leaves very little prompt
    o["tight_error"] = raises(
        S.DataFormatter(max_seq_length=SPEC["tight_max_seq_length"]).to_tinker_datum,
        good, S.FakeTokenizer())

    # a template whose generation header is one character, so nothing is windowed
    o["unwindowed"] = encoding_vals(
        S.DataFormatter(max_seq_length=SPEC["short_header_max_seq_length"]).to_tinker_datum(
            S.example(*pairs("short_header")), S.ShortHeaderTokenizer()))

    batch = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"]).format_batch(
        [S.example(*[tuple(m) for m in msgs]) for msgs in SPEC["batch"]], S.FakeTokenizer())
    o["batch_len"] = len(batch)
    o["batch_num_messages"] = [
        read_field(S.datum_part(datum, "metadata"), "num_messages") for datum in batch]
    o["batch_window_starts"] = [
        read_field(S.encoding_of(datum), "window_start") for datum in batch]
    return o


# ---------------------------------------------------------------------------
# r2 — what the formatter tells the caller it threw away
# ---------------------------------------------------------------------------
def _batch_examples():
    return [S.example(*[tuple(m) for m in msgs]) for msgs in SPEC["batch"]]


def _dropping_batch():
    """A formatter whose last pass ran this run's batch at the narrow window."""
    formatter = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"])
    kept = formatter.format_batch(_batch_examples(), S.FakeTokenizer())
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
    o["kept_supervised"] = [supervised(datum) for datum in kept]

    clean = S.DataFormatter(max_seq_length=SPEC["clean_max_seq_length"])
    data = clean.format_batch(_batch_examples(), S.FakeTokenizer())
    o["clean_data_len"] = len(data)
    o["clean_report"] = report_vals(clean.last_report)
    o["clean_supervised"] = [supervised(datum) for datum in data]

    fireworks = S.FireworksDataFormatter(max_seq_length=SPEC["fw_report_max_seq_length"])
    lines = fireworks.to_jsonl_lines(
        [S.example(*[tuple(m) for m in msgs]) for msgs in SPEC["fw_report_examples"]])
    o["fw_lines_is_list"] = isinstance(lines, list)
    o["fw_lines"] = lines
    o["fw_report"] = report_vals(fireworks.last_report)
    return o


def probe_r2_scope() -> dict:
    S.require_curator()
    fresh = S.DataFormatter(max_seq_length=SPEC["good_max_seq_length"])
    o = {"fresh_report": report_vals(fresh.last_report)}

    formatter, _ = _dropping_batch()
    o["after_batch"] = report_vals(formatter.last_report)

    datum = formatter.to_tinker_datum(S.example(*pairs("good")), S.FakeTokenizer())
    o["datum_window_start"] = read_field(S.encoding_of(datum), "window_start")
    o["report_after_success"] = report_vals(formatter.last_report)

    o["raise_too_long"] = raises(
        formatter.to_tinker_datum, S.example(*pairs("too_long")), S.FakeTokenizer())
    o["report_after_raise"] = report_vals(formatter.last_report)
    return o


def probe_r2_failure_behavior() -> dict:
    S.require_curator()
    formatter, _ = _dropping_batch()
    o = {"before": report_vals(formatter.last_report)}

    bad_roles = S.example(*pairs("bad_roles"))
    o["raise_bad_roles"] = raises(
        formatter.format_batch, _batch_examples() + [bad_roles], S.FakeTokenizer())
    o["report_after_bad_roles"] = report_vals(formatter.last_report)

    o["raise_bad_tok"] = raises(
        formatter.format_batch, _batch_examples(), S.NoTemplateTokenizer())
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


def main(out_path: str, seed: str) -> int:
    global SPEC
    SPEC = fixture_spec.derive(seed)

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
    # argv: observations path, seed, artifacts dir. g9's scenarios are pure
    # in-process, so it writes nothing to the artifacts directory and does not
    # read it.
    code = main(sys.argv[1], sys.argv[2])
    sys.stdout.flush()
    sys.stderr.flush()
    _EXIT(code)
