"""g3 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and, for
the two source-text facts, the submission's source under SUBMISSION_SRC. It applies
the assertions the g3 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them into
the identical fact keys and `test.sh`/`score.py` are unchanged. No agent code runs
here, so the report cannot be forged; and `test.sh` locks this file to root, so the
worker cannot read the numbers below to forge an observation that matches them. That
pair is what closes the forgery in tasks/lessons.md (2026-09-09) that a uid alone
could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files stay
the human-readable source of truth and the fact<->test bijection. Where a test read
source with `inspect.getsource(...)` this reads the module file directly and pulls
the same class body out with the AST (parsing text executes nothing), which is both
safe in this process and a more faithful check of the graded artifact than trusting
the worker to report its own source.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import sys
from xml.sax.saxutils import escape, quoteattr


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised_type(info, typename, msg=""):
    ok(info.get("raised"), f"{msg}: expected {typename}, none raised")
    ok(typename in info.get("mro", []), f"{msg}: {typename} not in {info.get('mro')}")


# ---------------------------------------------------------------------------
# Reading the submitted source (root, submission NOT importable)
# ---------------------------------------------------------------------------
def _module_source(rel_candidates) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in rel_candidates:
        path = root / rel
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    raise Fail(f"cannot read source at any of {rel_candidates} under {root}")


def _class_source(src: str, name: str) -> str:
    """The source of one class body — the faithful stand-in for
    `inspect.getsource(cls)`, so a comment elsewhere in the file cannot decide a
    check the test scoped to the class."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            segment = ast.get_source_segment(src, node)
            if segment:
                return segment
    raise Fail(f"class {name!r} not found in source")


_RETRY_POLICY = ["bespokelabs/curator/request_processor/online/retry_policy.py",
                 "bespokelabs/curator/request_processor/online/retry_policy/__init__.py"]
_BASE_PROCESSOR = ["bespokelabs/curator/request_processor/online/base_online_request_processor.py",
                   "bespokelabs/curator/request_processor/online/base_online_request_processor/__init__.py"]


def _check_retry_policy_imports():
    """retry_policy.py reaches for neither aiohttp, time nor random — the AST
    check of test_open, over the file on disk."""
    src = _module_source(_RETRY_POLICY)
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    ok(imported.isdisjoint({"aiohttp", "time", "random"}),
       f"retry_policy.py imports {sorted(imported)}; it must not reach for aiohttp, time or random")


def _base_processor_class_source() -> str:
    return _class_source(_module_source(_BASE_PROCESSOR), "BaseOnlineRequestProcessor")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    # P1: the enum, its order, its str mixin
    eq(o["enum_names"], ["THROTTLE", "TRANSIENT", "CONTRACT", "TERMINAL"], "FailureClass names/order")
    eq(o["enum_values"], ["throttle", "transient", "contract", "terminal"], "FailureClass values")
    eq(o["enum_len"], 4, "FailureClass length")
    ok(o["contract_is_str"], "FailureClass.CONTRACT is not a str-valued member")

    # the module boundary: standard library only
    _check_retry_policy_imports()

    # P2: status first, then the table exactly as the ticket writes it
    eq(o["classify_status"], ["TRANSIENT", "THROTTLE", "THROTTLE", "CONTRACT", "CONTRACT",
                              "CONTRACT", "TERMINAL", "TERMINAL", "TERMINAL", "TRANSIENT",
                              "TRANSIENT", "TRANSIENT", "TRANSIENT", "CONTRACT", "TRANSIENT"],
       "classify_failure status signal")
    # P3: the type signal walks the MRO by name
    eq(o["classify_type"], ["THROTTLE", "CONTRACT", "CONTRACT", "TRANSIENT", "TRANSIENT",
                            "TRANSIENT", "TERMINAL", "TERMINAL", "CONTRACT", "CONTRACT"],
       "classify_failure type signal")
    # P4: marker order beats message position; the default is TRANSIENT
    eq(o["classify_marker"], ["THROTTLE", "THROTTLE", "THROTTLE", "THROTTLE", "TRANSIENT",
                              "TRANSIENT", "TRANSIENT", "TERMINAL", "TERMINAL", "TRANSIENT",
                              "TRANSIENT", "THROTTLE"], "classify_failure marker signal")

    # P5/P6: the schedule, the cap before the jitter, the draw count
    eq(o["construct_calls"], [0, 0], "neither injected callable may be called at construction")
    ok(o["clock_no_default"], "clock has a default")
    ok(o["jitter_no_default"], "jitter has a default")
    eq(o["delays"], [5.0, 10.0, 20.0, 37.5, 37.5, 0.312, 0.938, 2.812, 8.438, 12.5, 12.5], "delay_for schedule")
    eq(o["draws_after_positive"], 11, "one jitter draw per positive delay")
    eq(o["zero_delays"], [0.0, 0.0], "contract/terminal delays are zero")
    eq(o["draws_after_zero"], 11, "a zero delay must not consume the jitter source")
    eq(o["clock_calls_after_delays"], 0, "delay_for has no business reading the clock")
    eq(o["clamp"], [4.0, 8.0, 8.0, 4.0], "jitter clamped to [0,1] on a 5s base throttle delay")
    raised_type(o["delay_zero_attempt_raises"], "ValueError", "delay_for at attempt 0")

    # P7: the verdict's shape, its routed counter and its reason code
    ok(o["is_dataclass"], "the verdict is not the frozen dataclass the ticket asks for")
    raised_type(o["frozen"], "FrozenInstanceError", "the verdict is not frozen")
    ok(o["v_retry"] is True, "a throttle with budget must retry")
    eq(o["v_class"], "THROTTLE", "verdict failure class")
    eq(o["v_attempt"], 1, "verdict attempt index")
    eq(o["counter_throttle"], "num_rate_limit_errors", "throttle counter")
    eq(o["reason_throttle"], "throttle:retry", "throttle reason code")
    eq(o["counter_contract"], "num_other_errors", "contract counter")
    eq(o["reason_contract"], "contract:retry", "contract reason code")
    eq(o["counter_transient"], "num_api_errors", "transient counter")
    eq(o["reason_transient"], "transient:retry", "transient reason code")
    ok(o["terminal_retry"] is False, "a terminal verdict must not retry")
    eq(o["terminal_counter"], "num_api_errors", "terminal counter")
    eq(o["terminal_reason"], "terminal:abort", "terminal reason code")
    eq(o["terminal_attempt"], 3, "terminal attempt index")
    eq(o["terminal_delay"], 0.0, "terminal delay")

    # P9: exactly one counter moves per failure
    eq(o["counter_sequence"], [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 2, 1]], "one counter per failure")

    # P10: the summary and the shared attempt label
    eq(o["summary_a"], ["[throttle] rate limit (x3)", "[transient] boom (x2)", "[contract] bad (x1)"], "summary a")
    eq(o["summary_b"], ["[transient] a (x2)", "[contract] b (x1)"], "summary b")
    eq(o["summary_c"], ["[transient] a (x1)", "[contract] a (x1)"], "summary c")
    eq(o["summary_empty"], [], "summary empty")
    eq(o["labels"], ["attempt #1 of 11", "attempt #4 of 4", "attempt #1 of 1"], "attempt labels")

    # the wiring: APIRequest's new fields, and the except block
    ok("attempts_made" in o["apirequest_fields"], f"APIRequest has {o['apirequest_fields']}")
    ok("failure_log" in o["apirequest_fields"], f"APIRequest has {o['apirequest_fields']}")
    eq(o["fresh_attempts_made"], 0, "fresh attempts_made")
    eq(o["fresh_failure_log"], [], "fresh failure_log")
    eq(o["fresh_attempts_left"], 3, "fresh attempts_left")
    ok(o["built_policy"], "__init__ built no RetryPolicy on the processor")
    eq(o["queue_size"], 1, "a rate-limited request with budget to spare was not re-queued")
    ok(o["queue_is_request"], "the re-queued object is not the request")
    eq(o["request_attempts_made"], 1, "request attempts_made after one failure")
    eq(o["request_failure_log"], [["THROTTLE", "API error: Rate limit reached for gpt-4o"]], "request failure_log")
    eq(o["wired_counters"], [1, 0, 0], "a 429 must be counted once, as a rate limit")


# ---------------------------------------------------------------------------
# r1 — what a failure costs, and the per-request 429 waivers
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["default_waivers"], 6, "DEFAULT_THROTTLE_WAIVERS")
    ok("throttle_waivers_left" in o["apirequest_fields"], f"APIRequest carries no waiver counter; it has {o['apirequest_fields']}")
    eq(o["fresh_waivers"], 6, "a fresh request starts at DEFAULT_THROTTLE_WAIVERS")
    ok(o["decide_var_keyword"] or {"attempts_made", "attempts_left", "throttle_waivers_left"} <= set(o["decide_params"]),
       f"decide takes {o['decide_params']}")
    eq(o["transient"], [8, 4], "a transient failure costs one attempt and no waiver")
    eq(o["contract"], [7, 4], "a contract failure costs two attempts and no waiver")
    eq(o["waived"], [True, 9, 3, 1, "throttle:retry"], "a throttle with a waiver spends the waiver, not the budget")
    eq(o["unwaived"], [True, 8, 0, 1, "throttle:retry"], "with no waivers left a throttle costs one attempt")


def judge_r1_scope(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["second_waivers"], 6, "a fresh request must start with six waivers")
    eq(o["first_waivers"], 0, "the drained request keeps its own count")
    eq(o["loop_waivers"], [5, 5, 5, 5, 5, 5], "the waiver count comes from the argument, not policy state")
    eq(o["loop_budgets"], [5, 5, 5, 5, 5, 5], "the budget comes from the argument, not policy state")
    eq(o["tracker_waiver_fields"], [], "OnlineStatusTracker gained a waiver field")
    eq(o["tracker_waiver_attrs"], [], "OnlineStatusTracker instance gained a waiver attribute")
    eq(o["config_waiver_fields"], [], "OnlineRequestProcessorConfig gained a waiver knob")
    ok(o["attempts_left_no_default"], "attempts_left must still be seeded by the caller")
    src = _base_processor_class_source()
    ok(re.search(r"attempts_left\s*=\s*[^,\n)]*max_retries", src),
       "attempts_left is no longer seeded from config.max_retries")


def judge_r1_exclusions(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["dead"], [False, 0, 4, 2, "terminal:abort"], "a terminal verdict must zero the budget and leave the waivers")
    eq(o["waived"], [True, 0, 0, 5, "throttle:retry"], "an empty budget must not stop a waived throttle")
    eq(o["spent"], [False, 0, 0, 6, "throttle:exhausted"], "the throttle with waivers spent is the one that stops")


def judge_r1_failure_behavior(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["affordable"], [True, 0, 6, 1, "contract:retry"], "2 - 2 == 0 is affordable, so retried")
    eq(o["unaffordable"], [False, 0, 6, 2, "contract:exhausted"], "1 - 2 < 0, so the request ends")
    eq(o["unaffordable_budget"], 0, "the post-failure budget is clamped at zero, never negative")
    eq(o["unaffordable_delay"], 0.0, "an un-retried verdict has a zero delay")
    eq(o["draws_after_unaffordable"], o["drawn"], "a verdict that will not be retried must not ask the schedule for a delay")
    eq(o["empty"], [False, 0, 0, 10, "transient:exhausted"], "an exhausted transient ends the request")
    eq(o["empty_delay"], 0.0, "an exhausted transient has a zero delay")
    eq(o["draws_after_empty"], o["drawn"], "an exhausted transient must not consume the jitter source")


def judge_r1_observability(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["default_waivers"], 6, "DEFAULT_THROTTLE_WAIVERS")
    eq(o["fresh_waivers"], 6, "a fresh request starts at six waivers")
    eq(o["healthy"], [3, 5], "a waived throttle keeps the budget and spends one waiver")
    eq(o["broke"], [True, 2], "an empty budget still retries a waived throttle and spends the waiver")
    eq(o["spent"], [False, "throttle:exhausted", 0], "no budget and no waivers ends the request")
    eq(o["length_budget"], 1, "a contract failure at three attempts costs two")
    eq(o["last"], [False, "contract:exhausted", 0], "a contract failure at one attempt ends the request")
    eq(o["bad_key"], ["terminal:abort", 0, 6], "a terminal verdict zeroes the budget and passes the waivers through")
    # [re-queued, attempts_left after]. Three v7 runs made `length` terminal at the
    # call site and still passed the `decide`-only rows above.
    eq(o.get("length_via_request_path"), [1, 1],
       "on the request path a length-truncated response must be re-queued and charged like any contract failure, two attempts")


# ---------------------------------------------------------------------------
# r2 — an absolute cooldown horizon that only 429s extend
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    names = o["tracker_field_names"]
    ok("throttle_cooldown_until" in names, f"OnlineStatusTracker has no cooldown horizon; its fields are {names}")
    ok(names.index("throttle_cooldown_until") == names.index("time_of_last_rate_limit_error") + 1,
       f"throttle_cooldown_until is not declared immediately after time_of_last_rate_limit_error: {names}")
    eq(o["fresh_horizon"], 0.0, "a fresh tracker's horizon is zero")
    if o.get("has_baseline"):
        eq(o["added_pause_fields"], ["throttle_cooldown_until"],
           "the requirement allows exactly one pause field")
    eq(o["long_delay"], 8.0, "first throttle delay at jitter 1.0, attempt #1")
    eq(o["long_clock_calls"], 1, "a throttle must read the injected clock exactly once")
    eq(o["long_tolre"], 500.0, "time_of_last_rate_limit_error stamped from the clock")
    eq(o["long_horizon"], 508.0, "horizon advanced to now + delay")
    eq(o["short_delay"], 4.0, "second, shorter delay")
    eq(o["short_horizon"], 508.0, "a later short delay must not shorten the horizon")
    eq(o["short_tolre"], 500.0, "time_of_last_rate_limit_error unchanged at the same instant")
    eq(o["later_delay"], 16.0, "a longer delay")
    eq(o["later_horizon"], 516.0, "a longer delay does extend the horizon")
    eq(o["remaining"], [8.001, 0.001, 0.0, 0.0], "remaining_cooldown_seconds: clamped at zero, rounded to three decimals")


def judge_r2_scope(o):
    ok(o["has_horizon"], "the tracker's throttle cooldown horizon is not implemented")
    eq(o["c1"], [0, 1, 0], "transient counter")
    eq(o["c2"], [0, 1, 1], "contract counter")
    eq(o["c3"], [0, 2, 1], "terminal counter")
    eq(o["clock_after_nonthrottle"], 0, "a non-throttle verdict must not call the injected clock")
    eq(o["horizon_after_nonthrottle"], 0.0, "a non-throttle verdict must not touch the horizon")
    eq(o["tolre_after_nonthrottle"], 0.0, "a non-throttle verdict must not stamp time_of_last_rate_limit_error")
    eq(o["c4"], [1, 2, 1], "rate-limit counter")
    eq(o["clock4"], 1, "a throttle reads the clock once")
    eq(o["horizon4"], 705.0, "horizon stamped by the throttle")
    eq(o["tolre4"], 700.0, "time_of_last stamped by the throttle")
    eq(o["c5"], [1, 3, 2], "more non-throttles move only their counters")
    eq(o["clock5"], 1, "more non-throttles cost no clock call")
    eq(o["horizon5"], 705.0, "more non-throttles leave the horizon")
    eq(o["tolre5"], 700.0, "more non-throttles leave time_of_last")
    eq(o["clock6"], 2, "the clock is called once per rate-limit failure and never otherwise")


def judge_r2_exclusions(o):
    ok(o["has_horizon"], "the tracker's throttle cooldown horizon is not implemented")
    ok(o["knob_in_config"], "seconds_to_pause_on_rate_limit vanished from the config")
    eq(o["knob_default"], 10, "the knob still defaults to 10")
    eq(o["knob_set"], 42, "the knob is still settable")
    eq(o["processor_knob"], 10, "the processor still carries the knob")
    eq(o["slept_after_lapsed"], [], "the pause was derived from the knob or from time since the last 429")
    eq(o["slept_after_never"], [], "a run that has never been throttled paused")
    ok(len(o["slept_after_ahead"]) == 1, f"a live cooldown horizon did not pause: slept {o['slept_after_ahead']}")
    ok(3.0 < o["slept_after_ahead"][0] <= 4.0, f"the pause came from something other than the horizon: {o['slept_after_ahead'][0]}")
    # Asked of the syntax tree, not the text: a v7 run wrote a docstring explaining
    # why the knob is dead and lost this fact for naming it. An attribute read or an
    # exact-name string (getattr) is a read; prose that mentions it is not.
    src = _base_processor_class_source()
    reads = [
        node.lineno
        for node in ast.walk(ast.parse(src))
        if (isinstance(node, ast.Attribute) and node.attr == "seconds_to_pause_on_rate_limit")
        or (isinstance(node, ast.Constant) and node.value == "seconds_to_pause_on_rate_limit")
    ]
    ok(not reads, f"the online processor still reads the dead pause knob (class-relative lines {reads})")


def judge_r2_observability(o):
    ok(o["has_horizon"], "the tracker's throttle cooldown horizon is not implemented")
    eq(o["first_delay"], 5.0, "first throttle delay")
    eq(o["first_horizon"], 1005.0, "horizon stamped to now + delay")
    eq(o["first_tolre"], 1000.0, "time_of_last stamped from the clock")
    eq(o["second_horizon"], 1005.0, "the horizon is a monotonic maximum, not the latest assignment")
    eq(o["remaining"], [3.0, 0.5, 0.0, 0.0], "remaining_cooldown_seconds table")
    eq(o["fresh_horizon"], 0.0, "a fresh tracker's horizon is zero")
    eq(o["fresh_remaining"], 0.0, "a fresh tracker has no remaining cooldown")


JUDGES = {
    "test_open::test_open_feature__failures_are_classified_priced_and_summarised_by_the_policy_module": judge_open,
    "test_r1::test_rule__a_throttle_spends_a_waiver_a_transient_one_attempt_and_a_contract_two": judge_r1_rule,
    "test_r1::test_scope__the_waiver_allowance_is_per_request_and_lives_nowhere_else": judge_r1_scope,
    "test_r1::test_exclusions__a_terminal_verdict_discards_the_budget_and_an_empty_budget_still_retries_a_waived_throttle": judge_r1_exclusions,
    "test_r1::test_failure_behavior__exhaustion_is_tested_after_the_cost_is_charged_and_the_floor_is_zero": judge_r1_failure_behavior,
    "test_r1::test_observability__the_stated_budget_and_waiver_table_holds_exactly": judge_r1_observability,
    "test_r2::test_rule__the_cooldown_horizon_is_one_new_tracker_field_that_only_ever_moves_forward": judge_r2_rule,
    "test_r2::test_scope__only_throttles_extend_the_horizon_or_consult_the_clock": judge_r2_scope,
    "test_r2::test_exclusions__the_seconds_to_pause_knob_survives_in_config_and_is_never_read_again": judge_r2_exclusions,
    "test_r2::test_observability__the_stated_horizon_and_remaining_cooldown_table_holds_exactly": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g3_retry_backoff_policy" '
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
