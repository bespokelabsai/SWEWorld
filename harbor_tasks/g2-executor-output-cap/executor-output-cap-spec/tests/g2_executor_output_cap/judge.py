"""g2 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g2 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks /tests to
root, so the worker cannot read the numbers below to forge an observation that
matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

Every reward-bearing expected value lives HERE and nowhere the worker can read:
the elision marker `\\n[[curator:elided {n} bytes]]\\n` and the 3:1 split it
sits in, the floor of 16 and the `OutputCapError` message, the exit-code and
timeout message text, the `TRUNCATION_LOG_TEMPLATE` output, and the
`error_truncated` semantics. `test_open`/`test_r1`/`test_r2` stay the
human-readable source of truth and the fact<->test bijection.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from xml.sax.saxutils import escape, quoteattr

# Scenario inputs the judge must re-derive expectations from (identical to
# probe_support's, kept here because the judge shares no module with the worker).
DIGITS = "0123456789" * 10

# Answers: the assembled exit-code prefix and the timeout text, both asserted
# verbatim by the suite.
EXIT1_PREFIX = "Program exited with status code 1\n\nError details:\n"


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised(info, *, mro=None, max_bytes=..., string=..., msg=""):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    if max_bytes is not ...:
        eq(info.get("max_bytes"), max_bytes, f"{msg}: max_bytes")
    if string is not ...:
        eq(info.get("str"), string, f"{msg}: message")


def marker(dropped: int) -> str:
    """The elision marker, charged OUTSIDE the budget; `dropped` is the byte count."""
    return f"\n[[curator:elided {dropped} bytes]]\n"


# =============================================================================
# the open feature
# =============================================================================
def judge_open(o):
    eq(o["DEFAULT_MAX_OUTPUT_BYTES"], 65536, "DEFAULT_MAX_OUTPUT_BYTES")
    ok(o["has_field"], f"CodeExecutionBackendConfig has no max_output_bytes; it has {o['config_fields']}")
    eq(o["default_budget"], 65536, "default max_output_bytes")
    eq(o["zero_budget"], 0, "max_output_bytes=0")
    eq(o["budget_128"], 128, "max_output_bytes=128")
    raised(o["reject_neg1"], mro="ValidationError", msg="max_output_bytes=-1")

    for name, value in o["backends"].items():
        eq(value, 128, f"the {name} backend does not carry the budget")
    eq(o["backend_local_default"], 65536, "local backend default budget")

    ok(o["sig_has"], f"_execute_in_sandbox takes {o['sig_params']}")
    eq(o["sig_kind"], "KEYWORD_ONLY", "max_output_bytes is keyword-only")
    eq(o["sig_default"], 65536, "max_output_bytes default")

    for label, m in o["models"].items():
        ok(m["has"], f"{label} model has {m['fields']}")
        eq(m["required"], False, f"{label}.truncated_streams is not required")
        eq(m["value"], [], f"{label}.truncated_streams default")
    eq(o["dumped_truncated"], [], "truncated_streams through model_dump")

    raised(o["positional_refused"], mro="TypeError", msg="a positional sixth arg is refused")
    eq(o["capped"]["message"], "success", "capped run message")
    ok(0 < o["capped"]["len_stdout"] < 300, f"stdout came back at {o['capped']['len_stdout']} chars under a 64-byte budget")
    ok(0 < o["capped"]["len_stderr"] < 300, f"stderr came back at {o['capped']['len_stderr']} chars under a 64-byte budget")
    eq(o["capped"]["truncated_sorted"], ["stderr", "stdout"], "both streams named")
    eq(o["capped"]["files"], "files-archive", "files passed through")

    for site, m in o["sites"].items():
        ok(not m["stdout_none"], f"the {site} site returned no stdout at all")
        ok(0 < m["len"] < 300, f"the {site} site returned {m['len']} characters under a 64-byte budget")

    ok(o["failed_len_stderr"] < 300, "the capped stderr on the exit-code path")
    eq(o["failed_error"], EXIT1_PREFIX + o["failed_stderr"], "`error` embeds the capped stderr")
    eq(o["fmt_params"], ["exit_code", "stderr"], "_format_exit_code_error signature")
    eq(o["fmt_call"], "Program exited with status code 3\n\nError details:\nboom", "_format_exit_code_error wording")

    eq(o["untouched_stdout"], "A" * 300, "under-budget stdout untouched")
    eq(o["untouched_files"], "F" * 5000, "files never capped")
    eq(o["untouched_truncated"], [], "under-budget truncated_streams")


# =============================================================================
# r1 — the shape of the cut
# =============================================================================
def judge_r1_rule(o):
    head, tail, mk = DIGITS[:48], DIGITS[-16:], marker(36)  # (64*3)//4 = 48, 64-48 = 16, 100-64 dropped
    eq(o["wide_stdout"], head + mk + tail, "48-byte head, 16-byte tail, elision marker")
    eq(len(o["wide_stdout"]), 64 + 29, "marker charged outside the 64-byte budget")
    eq(o["wide_stdout"].index(mk), 48, "marker sits after the head")
    eq(o["narrow_stdout"], DIGITS[:24] + marker(68) + DIGITS[-8:], "a 32-byte budget splits 24/8")
    eq(len(o["narrow_stdout"]), 32 + 29, "32-byte budget length")


def judge_r1_scope(o):
    data = "€" * 10
    ok(o["stdout"] != data, "10 characters / 30 bytes came back whole under a 20-BYTE budget")
    ok("�" not in o["stdout"], f"a clean UTF-8 stream came back with a replacement character: {o['stdout']!r}")
    eq(o["stdout"].count("€"), 6, f"expected the 18 decodable bytes of a 20-byte budget, got {o['stdout']!r}")
    eq(o["truncated"], ["stdout"], "truncated_streams")
    # 18 of the 30 bytes survive, so 12 were dropped (trimming gave back 2 budgeted bytes)
    ok("12" in re.findall(r"\d+", o["stdout"]), f"the elided-byte count should read 12: {o['stdout']!r}")


def judge_r1_exclusions(o):
    ok(o["over_len"] < 300, "the stdout/stderr byte cap is not implemented, so the constraint cannot be credited")
    eq(o["unlimited_stdout"], "A" * 300, "a budget of 0 kept everything")
    eq(o["unlimited_stderr"], "B" * 500, "a budget of 0 kept stderr")
    eq(o["unlimited_truncated"], [], "0 lists nothing")
    eq(o["under_stdout"], DIGITS[:60], "under-budget stdout untouched")
    eq(o["under_stderr"], "", "an empty stderr is preserved")
    eq(o["under_truncated"], [], "under-budget lists nothing")
    eq(o["exactly_stdout"], "A" * 64, "a stream exactly at the budget is not shortened")
    eq(o["exactly_truncated"], [], "at-budget lists nothing")


def judge_r1_failure_behavior(o):
    eq(o["MIN"], 16, "MIN_MAX_OUTPUT_BYTES")
    ok("ValueError" in o["outputcaperror_mro"], f"OutputCapError is not a ValueError: {o['outputcaperror_mro']}")
    raised(o["refused"], mro="OutputCapError", max_bytes=8,
           string="max_bytes must be 0 or at least 16, got 8", msg="request-time refusal")
    eq(o["floor16_message"], "success", "16 is the floor and must be accepted")
    for bad in (1, 8, 15):
        info = o["bad"][str(bad)]
        raised(info, mro="ValidationError", msg=f"up-front rejection of {bad}")
        ok(f"max_bytes must be 0 or at least 16, got {bad}" in info.get("str", ""),
           f"the rejection of {bad} does not carry the OutputCapError message: {info.get('str')!r}")
    raised(o["docker8"], mro="ValidationError", msg="factory rejects 8")
    eq(o["cfg0"], 0, "0 accepted")
    eq(o["cfg16"], 16, "16 accepted")
    raised(o["neg1"], mro="ValidationError", msg="-1 rejected")


def judge_r1_observability(o):
    eq(o["template_formatted"], "sandbox output capped: stderr, stdout exceeded the 64-byte budget",
       "TRUNCATION_LOG_TEMPLATE")
    eq(o["w_stdout_only"], ["sandbox output capped: stdout exceeded the 64-byte budget"], "stdout only")
    eq(o["w_both"], ["sandbox output capped: stderr, stdout exceeded the 64-byte budget"], "both streams")
    eq(o["w_timeout"], ["sandbox output capped: stdout exceeded the 64-byte budget"], "timeout path")
    eq(o["w_stderr_only"], ["sandbox output capped: stderr exceeded the 64-byte budget"], "stderr only")
    eq(o["w_nothing_cut"], [], "nothing cut, nothing said")
    eq(o["w_unlimited"], [], "budget 0 says nothing")
    eq(o["w_salvage"], ["sandbox output capped: stdout exceeded the 64-byte budget"], "salvage path silent, said once")
    eq(o["w_never_captured"], [], "a run that captured nothing says nothing")


# =============================================================================
# r2 — the cap reaches `error`, on one path only
# =============================================================================
def judge_r2_rule(o):
    ok(o["has_error_truncated"], f"CodeExecutionOutput has {o['fields']}")
    eq(o["required"], False, "error_truncated is not required")
    ok(o["annotation_is_bool"], "error_truncated is a plain bool, not an Optional one")
    eq(o["default_error_truncated"], False, "error_truncated defaults False")
    ok(o["index_ok"], f"error_truncated is not declared right after truncated_streams: {o['fields']}")
    eq(o["blew_message"], "error", "the exception path message")
    # 200 chars under a 32-byte budget: 24 head, 8 tail, 168 dropped
    eq(o["blew_error"], "Z" * 24 + marker(168) + "Z" * 8, "the exception message is capped like a stream")
    eq(o["blew_len"], 32 + 30, "marker charged outside the budget")
    eq(o["blew_error_truncated"], True, "error_truncated set on the exception path")


def judge_r2_scope(o):
    ok(o["failed_len_stderr"] < 200, "the stdout/stderr byte cap is not implemented")
    eq(o["failed_error"], EXIT1_PREFIX + o["failed_stderr"], "`error` is the message assembled from the capped stderr")
    eq(len(o["failed_error"]), o["failed_len_stderr"] + 50, "the assembled message was re-capped")
    ok(len(o["failed_error"]) > 32, "the assembled message keeps its full length")
    eq(o["failed_error_truncated"], False, "error_truncated is not set on the assembled exit-code path")
    eq(o["failed_files"], "F" * 5000, "files is not capped")
    eq(o["timed_message"], "timeout", "timeout message")
    eq(o["timed_error"], "Execution timed out after 7s", "the timeout message goes through the cap")
    eq(o["timed_error_truncated"], False, "error_truncated on the timeout path")
    eq(o["salvaged_files"], "F" * 5000, "files survives the salvage path")


def judge_r2_exclusions(o):
    ok(o["output_has_flag"], "the error_truncated flag on CodeExecutionOutput is not implemented")
    ok(not o["result_has_flag"], "CodeExecutionResult gained the flag as well")
    eq(o["dumped_keys"], ["error", "error_truncated", "files", "message", "stderr", "stdout", "truncated_streams"],
       "model_dump keys")
    eq(o["both_error_truncated"], True, "error_truncated set when the error was cut")
    eq(o["both_truncated"], ["stdout"], '"error" leaked into truncated_streams')
    eq(o["failed_truncated"], ["stderr"], "stderr named on the exit-code path")


def judge_r2_observability(o):
    # 300 chars under 64: 48 head, 16 tail, 236 dropped
    eq(o["blew_error"], "X" * 48 + marker(236) + "X" * 16, "the exception message capped 48/16")
    eq(o["blew_len"], 94, "capped exception length")
    eq(o["blew_error_truncated"], True, "flagged truncated")
    eq(o["short_error"], "boom", "a message within budget is not rewritten")
    eq(o["short_error_truncated"], False, "error_truncated not set for a message the cap never shortened")
    eq(o["failed_len"], 143, "143: raw stderr in the message, and not re-capped")
    eq(o["failed_error"], EXIT1_PREFIX + "E" * 48 + marker(16) + "E" * 16, "the assembled message embeds the capped stderr")
    eq(o["failed_error_truncated"], False, "error_truncated on the assembled exit-code path")
    eq(o["failed_truncated"], ["stderr"], "stderr named")


JUDGES = {
    "test_open::test_open_feature__a_configurable_byte_budget_shortens_what_the_sandbox_returns": judge_open,
    "test_r1::test_rule__the_kept_head_and_tail_split_three_to_one_around_an_elision_marker": judge_r1_rule,
    "test_r1::test_scope__the_budget_counts_utf8_bytes_and_both_slices_land_on_codepoints": judge_r1_scope,
    "test_r1::test_exclusions__a_zero_budget_is_unlimited_and_streams_within_budget_are_untouched": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_budget_below_the_floor_of_sixteen_is_refused_by_outputcaperror": judge_r1_failure_behavior,
    "test_r1::test_observability__one_warning_line_per_capped_run_from_the_shared_template": judge_r1_observability,
    "test_r2::test_rule__the_exception_message_is_capped_and_flagged_by_error_truncated": judge_r2_rule,
    "test_r2::test_scope__the_exit_code_and_timeout_messages_and_files_are_never_capped": judge_r2_scope,
    "test_r2::test_exclusions__the_flag_is_on_the_output_model_alone_and_never_a_stream_name": judge_r2_exclusions,
    "test_r2::test_observability__the_exact_error_text_and_flag_of_the_three_named_runs": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g2_executor_output_cap" '
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
