"""g9 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g9 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks this file to
0600 root, so the worker cannot read the numbers below to forge an observation
that matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

The expected values — `GOOD_TEXT`, the `(reason, position)` pairs, the token
counts, the report defaults — are lifted from `test_open`/`test_r1`/`test_r2`;
those files stay the human-readable source of truth and the fact<->test
bijection.
"""
from __future__ import annotations

import json
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

# The one expected rendered string of the tokenizer path (an ANSWER; kept out of
# probe_support). The judge derives model_input / targets from it exactly as the
# test does.
GOOD_TEXT = "[user]" + "u" * 30 + "\n[assistant]" + "a" * 10 + "\n[user]vvvvv\n[assistant]bbbbbbbb\n"
PLAIN_TEXT = "<|user|>\nHello\n<|assistant|>\nHi there!\n"
REPORT_FIELDS = ["kept", "dropped", "windowed", "dropped_indices", "supervised_tokens"]
DEFAULT_REPORT = [0, 0, 0, [], 0]


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised(info, *, mro=None, msg="", **attrs):
    """Assert an exception was recorded, of the named class, carrying `attrs`."""
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    for name, want in attrs.items():
        eq(info.get(name), want, f"{msg}: {name}")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["exports"], [True] * 5, "finetune exports")
    eq(o["allowed_roles"], ["assistant", "system", "user"], "ALLOWED_ROLES")
    ok("ValueError" in o["encoding_error_mro"], "EncodingError subclasses ValueError")
    ok("EncodingError" in o["invalid_role_mro"], "InvalidRoleSequenceError subclasses EncodingError")
    ok("EncodingError" in o["tok_cap_mro"], "TokenizerCapabilityError subclasses EncodingError")

    # the five (reason, position) pairs, in the ticket's own order. The roles are
    # input-derived and deterministic, so the judge holds them to rebuild str().
    cases = [
        ([], "empty", 0),
        (["user", "tool", "assistant"], "unknown_role", 1),
        (["user", "system", "assistant"], "misplaced_system", 1),
        (["system", "user", "user", "assistant"], "non_alternating", 2),
        (["system", "user", "assistant", "user"], "unterminated", 3),
    ]
    for info, (roles, reason, position) in zip(o["role_cases"], cases):
        raised(info, mro="InvalidRoleSequenceError", reason=reason, position=position,
               role_sequence=roles, msg=f"role case {roles}")
        eq(info.get("str"),
           f"invalid role sequence at position {position} ({reason}): {roles}",
           f"role case {roles} str")
    ok(o["legal_returns_none"], "legal conversation returns None")
    ok(o["legal_example_none"], "legal example returns None")

    # the left window, and one encode call that never truncates
    eq(o["model_input_len"], 39, "model_input length")
    eq(o["targets_0"], 97, "datum starts inside the first assistant turn")
    eq(o["model_input_19"], 10, "model_input[19]")
    eq(o["model_input"], [ord(c) for c in GOOD_TEXT[51:-1]], "model_input == GOOD_TEXT[51:-1]")
    eq(o["targets"], [ord(c) for c in GOOD_TEXT[52:]], "targets == GOOD_TEXT[52:]")
    for keys in o["encode_kwarg_keys"]:
        ok("truncation" not in keys and "max_length" not in keys,
           f"the tokenizer was asked to truncate: {keys}")

    # the envelope
    eq(o["metadata_surface"], ["encoding", "num_messages", "original_text"], "metadata surface")
    eq(o["metadata_original_text"], GOOD_TEXT, "metadata original_text")
    eq(o["metadata_num_messages"], 4, "metadata num_messages")
    eq(o["encoding_surface"],
       ["supervised_tokens", "token_count", "tokenizer", "window_start", "windowed"],
       "encoding surface")
    ok(o["enc_tokenizer_is_true"], "encoding tokenizer is True")
    eq(o["enc_token_count"], 91, "token_count")
    eq(o["enc_window_start"], 51, "window_start")
    ok(o["enc_windowed_is_true"], "windowed is True")

    # the no-tokenizer branch carries its text too
    eq(o["plain_original_text"], PLAIN_TEXT, "plain original_text")
    ok(o["plain_tokenizer_is_false"], "plain tokenizer is False")

    # a tokenizer with no chat template is refused
    for info in o["no_template"]:
        raised(info, mro="TokenizerCapabilityError", missing_method="apply_chat_template",
               msg="no chat template")
        eq(info.get("str"), "tokenizer is missing required method 'apply_chat_template'",
           "no chat template str")

    # from_config carries max_context_length
    ok(o["made_is_fireworks"], "from_config returns a FireworksDataFormatter")
    eq(o["made_max_seq_length"], 100, "max_context_length carried")
    ok(o["made_train_on_assistant_only_is_true"], "train_on_assistant_only default True")
    eq(o["fallback_max_seq_length"], 2048, "max_context_length fallback")
    eq(o["explicit_4096"], 4096, "explicit max_context_length")


# ---------------------------------------------------------------------------
# r1 — how an example that does not fit is encoded
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    weights = o["weights"]
    eq(len(weights), 39, "weights length")
    eq([i for i, w in enumerate(weights) if w == 1.0],
       [30, 31, 32, 33, 34, 35, 36, 37, 38],
       "the straddling span (48, 59) must contribute nothing, not its surviving tail")
    eq(sum(weights), 9.0, "weight sum")
    eq(set(weights), {0.0, 1.0}, "weights are 0/1")
    eq(o["supervised_tokens"], 9, "supervised_tokens")

    eq(o["wide_window_start"], 41, "wide window_start")
    eq(o["wide_supervised_tokens"], 20, "wide supervised_tokens")
    eq([i for i, w in enumerate(o["wide_weights"]) if w == 1.0],
       list(range(6, 17)) + list(range(40, 49)), "wide ones indices")


def judge_r1_scope(o):
    ok(o["plain_tokenizer_is_false"], "plain tokenizer is False")
    eq(o["plain_token_count"], 9, "plain token_count")
    eq(o["plain_window_start"], 0, "plain window_start")
    eq(o["plain_supervised_tokens"], 6,
       "the mock path must honour train_on_assistant_only, with the header inside the span")
    eq(o["plain_weights"], [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], "plain weights")
    eq(o["plain_model_input"], [0, 1, 2, 3, 4, 5, 6, 7], "plain model_input")
    eq(o["everything_weights"], [1.0] * 8, "train_on_assistant_only=False is all ones")
    eq(o["everything_supervised"], 9, "everything supervised_tokens")
    eq(o["good_all_ones_weights"], [1.0] * 39, "windowed all-ones on the tokenizer path")


def judge_r1_exclusions(o):
    eq(o["bytes_per_token"], 3, "FIREWORKS_BYTES_PER_TOKEN")
    eq(len(o["lines"]), 1, "expected the 90-byte line and not the 93-byte one")
    eq(o["lines_decoded"][0],
       {"messages": [{"role": "user", "content": "qqq"}, {"role": "assistant", "content": "ok"}]},
       "the kept line must be whole: nothing on this path is truncated")
    eq(o["lines_byte_lens"][0], 90, "kept line byte length")
    eq(o["accented_33"], [], "over-budget by UTF-8 bytes is dropped")
    eq(len(o["accented_34"]), 1, "fits when the budget is one token wider")
    eq(o["accented_34_decoded"][0]["messages"][0]["content"], "héllo wörld", "accented content kept whole")


def judge_r1_failure_behavior(o):
    ok("EncodingError" in o["example_too_long_mro"], "ExampleTooLongError subclasses EncodingError")
    raised(o["too_long_error"], mro="ExampleTooLongError", token_count=129, max_seq_length=40,
           retained_prompt_tokens=0, num_messages=2, msg="over-long refusal")
    ok("ValueError" in o["too_long_error"].get("mro", []), "ExampleTooLongError isinstance ValueError")
    eq(o["too_long_error"].get("str"),
       "example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16",
       "over-long refusal str")
    eq(o["good_window_start"], 51, "windowed example kept")
    raised(o["short_window_error"], retained_prompt_tokens=8, token_count=91, num_messages=4,
           msg="only 8 prompt tokens survive")
    eq(o["unwindowed_window_start"], 0, "unwindowed window_start")
    eq(o["unwindowed_token_count"], 6, "unwindowed token_count")
    eq(o["batch_len"], 1, "format_batch skips the refused row")
    eq(o["batch0_num_messages"], 4, "the surviving row is the good one")


# ---------------------------------------------------------------------------
# r2 — what the formatter tells the caller it threw away
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    ok(o["report_is_dataclass"], "EncodingReport is a dataclass")
    ok(o["report_frozen_is_true"], "EncodingReport is frozen")
    eq(o["report_fields"], REPORT_FIELDS, "EncodingReport fields, in order")
    eq(o["default_report"], DEFAULT_REPORT, "EncodingReport defaults")

    ok(o["kept_is_list"], "format_batch still returns a plain list")
    eq(o["kept_len"], 1, "one kept")
    report = o["report"]
    eq(report[0], 1, "report kept")
    eq(report[1], 1, "report dropped")
    eq(report[2], 1, "report windowed")
    eq(report[3], [1], "report dropped_indices by input position")
    eq(report[4], o["kept0_supervised"],
       "supervised_tokens sums the kept examples, matching the kept datum itself")

    eq(o["clean_data_len"], 2, "clean pass keeps both")
    eq(o["clean_report"][:4], [2, 0, 0, []], "clean report counters")
    eq(o["clean_report"][4], o["clean_supervised_sum"], "clean supervised_tokens is the sum")

    ok(o["fw_lines_is_list"], "to_jsonl_lines returns a list")
    eq(o["fw_lines_len"], 1, "one fireworks line")
    eq(o["fw_report"], [1, 1, 0, [1], 0], "fireworks report, tokenizer counters at zero")


def judge_r2_scope(o):
    eq(o["fresh_report"], DEFAULT_REPORT, "a fresh formatter carries the all-defaults report")
    # require_feature: crediting "to_tinker_datum leaves it alone" needs proof that
    # something writes the report in the first place.
    ok(o["after_batch"] != DEFAULT_REPORT, "format_batch writing self.last_report")
    ok(o["datum_windowed_is_true"], "the single-example datum was windowed")
    eq(o["report_after_success"], o["after_batch"], "a successful single call does not touch the report")
    raised(o["raise_too_long"], mro="ExampleTooLongError", msg="over-long single call")
    eq(o["report_after_raise"], o["after_batch"], "a raising single call does not touch the report")


def judge_r2_failure_behavior(o):
    ok(o["before"] != DEFAULT_REPORT, "format_batch writing self.last_report")
    eq(o["before"][1], 1, "the over-long example must be absorbed as a drop, not raised")
    raised(o["raise_bad_roles"], mro="InvalidRoleSequenceError", msg="bad roles abort")
    eq(o["report_after_bad_roles"], o["before"], "an aborted pass must not write a partial report")
    raised(o["raise_bad_tok"], mro="TokenizerCapabilityError", msg="bad tokenizer aborts")
    eq(o["report_after_bad_tok"], o["before"], "an aborted pass must not write a partial report")


JUDGES = {
    "test_open::test_open_feature__roles_are_validated_and_an_over_long_example_keeps_its_completion": judge_open,
    "test_r1::test_rule__an_assistant_turn_the_window_cuts_in_half_is_not_supervised_at_all": judge_r1_rule,
    "test_r1::test_scope__the_tokenizer_free_branch_supervises_assistant_spans_from_character_offsets": judge_r1_scope,
    "test_r1::test_exclusions__fireworks_drops_over_budget_lines_by_utf8_bytes_and_truncates_nothing": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_windowed_example_with_under_sixteen_prompt_tokens_is_refused": judge_r1_failure_behavior,
    "test_r2::test_rule__both_batch_entry_points_publish_a_frozen_encoding_report": judge_r2_rule,
    "test_r2::test_scope__only_the_batch_entry_points_write_the_report": judge_r2_scope,
    "test_r2::test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report": judge_r2_failure_behavior,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g9_example_encoding" '
             f'tests="{len(results)}" failures="{fails}" errors="0">']
    for classname, name, failure in results:
        head = f'<testcase classname={quoteattr(classname)} name={quoteattr(name)}>'
        if failure:
            lines.append(head + f'<failure message={quoteattr(failure[:200])}>'
                         + escape(failure[:4000]) + '</failure></testcase>')
        else:
            lines.append(head + '</testcase>')
    lines.append('</testsuite></testsuites>')
    return "\n".join(lines)


def main(obs_path: str, out_path: str) -> int:
    try:
        observations = json.loads(pathlib.Path(obs_path).read_text())
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if probe is None:
            results.append((classname, name, "no observation from probe"))
            continue
        if not probe.get("ok"):
            results.append((classname, name, f"probe error: {probe.get('error', 'unknown')}"))
            continue
        try:
            judge(probe["obs"])
            results.append((classname, name, ""))
        except Fail as exc:
            results.append((classname, name, str(exc)))
        except Exception as exc:  # noqa: BLE001 - a malformed observation is a failed fact, not a crash
            results.append((classname, name, f"judge error: {type(exc).__name__}: {exc}"))

    pathlib.Path(out_path).write_text(junit(results))
    for classname, name, failure in results:
        print(f"{'FAIL' if failure else 'pass'} {classname}::{name}"
              + (f"  {failure[:160]}" if failure else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
