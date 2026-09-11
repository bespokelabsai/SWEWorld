"""g10 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g10 suite has always made, writing a `junit.xml`
whose `classname`/`name` are the current suite's node ids — so `score.py` folds
them into the identical fact keys and `test.sh`/`score.py` are unchanged. No
agent code runs here, so the report cannot be forged; and `test.sh` locks this
file to 0600 root, so the worker cannot read the numbers below to forge an
observation that matches them. That pair is what closes the forgery in
tasks/lessons.md (2026-09-09) that a uid alone could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files
stay the human-readable source of truth and the fact<->test bijection.
"""
from __future__ import annotations

import json
import pathlib
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


def raised(info, *, mro=None, axis=None, requested=None, limit=None, string=None, msg=""):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    if axis is not None:
        eq(info.get("axis"), axis, f"{msg}: axis")
    if requested is not None:
        eq(info.get("requested"), requested, f"{msg}: requested")
    if limit is not None:
        eq(info.get("limit"), limit, f"{msg}: limit")
    if string is not None:
        eq(info.get("str"), string, f"{msg}: message")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    c = o["consts"]
    eq(c["req_per_min"], 200, "DEFAULT_MAX_REQUESTS_PER_MINUTE")
    eq(c["tpm_combined"], 100_000, "DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED")
    eq(c["in_per_min"], 100_000, "DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE")
    eq(c["out_per_min"], 40_000, "DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE")
    eq(c["origin_configured"], "configured", "LIMIT_ORIGIN_CONFIGURED")
    eq(c["origin_defaulted"], "defaulted", "LIMIT_ORIGIN_DEFAULTED")
    eq(c["origin_unlimited"], "unlimited", "LIMIT_ORIGIN_UNLIMITED")
    eq(o["request_headers"], ["x-ratelimit-limit-requests", "anthropic-ratelimit-requests-limit"], "REQUEST_LIMIT_HEADERS")
    eq(o["input_headers"], ["x-ratelimit-limit-input-tokens", "anthropic-ratelimit-input-tokens-limit"], "INPUT_TOKEN_LIMIT_HEADERS")
    eq(o["output_headers"], ["x-ratelimit-limit-output-tokens", "anthropic-ratelimit-output-tokens-limit"], "OUTPUT_TOKEN_LIMIT_HEADERS")
    eq(o["total_headers"], ["x-ratelimit-limit-tokens", "anthropic-ratelimit-tokens-limit"], "TOTAL_TOKEN_LIMIT_HEADERS")

    ok(o["ost_strategy_is"], "online_status_tracker re-exports TokenLimitStrategy")
    eq(o["strategy_values"], ["combined", "seperate"], "strategy members")
    ok(o["default_is_combined"], "strategy.default is combined")

    eq(o["parse_present"], [999, 1500, 2_000_000, 40000, 60000, 4000], "parse_limit_value present")
    eq(o["parse_absent"], [None] * 11, "parse_limit_value absent")

    eq(o["read_anthropic"], [4000, [400000, 80000, 480000], "seperate",
                             ["anthropic-ratelimit-requests-limit", "anthropic-ratelimit-input-tokens-limit",
                              "anthropic-ratelimit-output-tokens-limit"]], "anthropic headers")
    eq(o["read_remaining"], [None, [None, None, None], "combined", []], "remaining headers ignored")
    eq(o["read_empty"], [None, [None, None, None], "combined", []], "empty headers")
    eq(o["read_total_ci"], [None, [None, None, 60000], "combined", ["x-ratelimit-limit-tokens"]], "case-insensitive total")
    eq(o["read_pair"], [600, [50000, 20000, 70000], "seperate",
                        ["x-ratelimit-limit-requests", "x-ratelimit-limit-input-tokens",
                         "x-ratelimit-limit-output-tokens"]], "complete pair beats total")
    eq(o["read_half_pair"], [None, [None, None, 90000], "combined", ["x-ratelimit-limit-tokens"]], "half pair discarded")
    eq(o["read_zero"][0], None, "zero header rpm")
    eq(o["read_zero"][1], [None, None, 1500], "zero header tpm")
    eq(o["read_zero"][3], ["x-ratelimit-limit-tokens"], "zero header sources")

    s = o["seed"]
    eq(s[0], 1000.0, "seeded last_update_time")
    ok(s[1], "injected clock, not wall clock")
    eq(s[2], 60.0, "seeded request capacity")
    eq(s[3], 10000.0, "seeded token capacity")
    eq(s[4], "configured", "seeded token origin")
    eq(s[5], "configured", "seeded request origin")
    eq(o["seed_dynamics"], [6000.0, [7000.0, 1006.0], [7000.0, 996.0]], "seed consume/refill/backwards")
    eq(o["sep_dynamics"], [[10000, 5000, 15000], [9400, 4800, 14200], [9566, 4883, 14449]], "seperate dynamics")
    eq(o["defaulted"], [200, 100_000, 200.0, 100000.0, "defaulted", "defaulted"], "0 means defaulted")
    eq(o["unlimited"], [None, None, None, "unlimited", "unlimited", True, None, None], "None means unlimited")
    eq(o["sep_unlimited"], [[None, None, None], [None, None, None], "unlimited"], "seperate unlimited")
    eq(o["sep_partial_default"], [[100000, 20000, 120000], "defaulted"], "seperate partial default")
    eq(o["coerce_scalar_to_sep"], [90000, 90000, 180000], "scalar coerced to seperate")
    eq(o["coerce_sep_to_scalar"], 50000, "seperate coerced to scalar")

    raised(o["raise_total"], mro="ValueError", axis="total", requested=11000, limit=10000,
           string="request needs 11000 total capacity but the per-minute limit is 10000", msg="raise total")
    eq(o["raise_total_after"], [1000.0, 10000.0], "raise moved nothing")
    raised(o["raise_input"], axis="input", requested=1500, limit=1000, msg="raise input")
    ok(o["unlimited_never_raises"], "unlimited axis never raises")
    ok(o["empty_bucket_false"], "empty bucket returns False")

    eq(o["reserve_first"], [[700, 100, 800], 200.0, 59.0, 1], "reserve first")
    eq(o["reserve_second"], [True, 200.0, 59.0, 2], "reserve refused, nothing consumed")
    eq(o["reserve_unlimited"], [[700, 100, 800], 3, None, 59.0], "reserve under no token limit")
    ok(o["free_capacity_gone"], "the dead free_capacity helper is gone")

    eq(o["apply"], [[100000, "combined"], "seperate", 600, [50000, 20000, 70000],
                    [100000, 40000, 140000], [50000, 20000, 70000], 600], "apply_rate_limit_reading")


# ---------------------------------------------------------------------------
# r1 — debt floor
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["fraction"], 0.25, "CAPACITY_DEBT_FLOOR_FRACTION")
    eq(o["after_consume"], 200.0, "after consume")
    eq(o["after_settle"], -250.0, "floored debt")


def judge_r1_scope(o):
    ok(o["has_floor"], "a capacity debt floor fraction is not implemented")
    eq(o["defaulted_limit"], 100_000, "defaulted limit")
    eq(o["defaulted_after_consume"], 0.0, "defaulted after consume")
    eq(o["defaulted_after_settle"], -25000.0, "defaulted floor")
    eq(o["sep_after_consume"], [300, 400, 700], "seperate after consume")
    eq(o["sep_after_settle"], [-250, -125, -375], "seperate per-axis floor")
    eq(o["unlimited_token"], None, "unlimited token untouched")
    eq(o["unlimited_request"], None, "unlimited request untouched")
    eq(o["defaulted_request"], 59.0, "defaulted request capacity")
    eq(o["sep_request"], 59.0, "seperate request capacity")


def judge_r1_exclusions(o):
    ok(o["has_floor"] and o["has_counter"], "a capacity debt floor with a clamp counter is not implemented")
    eq(o["refilled"], [1000.0, 60.0, 0], "refill caps, no clamp")
    eq(o["released"], [1000.0, 0], "release caps, no clamp")
    eq(o["settled"], [100.0, 0], "settlement above floor, no clamp")


def judge_r1_observability(o):
    ok(o["has_counter"], "a capacity debt clamp counter is not implemented")
    eq(o["counts"], [0, 0, 1, 2], "one increment per clamping call")


# ---------------------------------------------------------------------------
# r2 — settlement vs refund
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    eq(o["after_consume"], [59.0, 9200.0], "after consume")
    ok(o["has_refund"], "a tracker refund operation is not implemented")
    eq(o["after_refund"], [60.0, 10000.0], "refund returns whole estimate + one slot")
    eq(o["after_refund2"], [60.0, 10000.0], "refund capped at limit")
    eq(o["settled"], [9400.0, 59.0], "settlement keeps slot spent")
    eq(o["delegated_reserve"], [59.0, 9200.0], "delegated reserve")
    eq(o["delegated_refund"], [60.0, 10000.0], "processor refund delegates")


def judge_r2_scope(o):
    eq(o["reserve_state"], [59.0, 9000.0], "reserve")
    eq(o["exhausted"], [60.0, 10000.0], "exhausted failure refunds")
    eq(o["requeued"], [0, 60.0, 10000.0], "requeued failure refunds")
    eq(o["success"], [59.0, 9200.0], "success settles")


def judge_r2_exclusions(o):
    eq(o["blocked_axes"], [900, 100, 1000], "blocked estimate")
    eq(o["after_reserve"], [59.0, 9000.0], "after reserve")
    eq(o["final"], [10000.0, 60.0], "refund is the estimate, not the reported spend")


def judge_r2_observability(o):
    ok(o["has_refund"], "a tracker refund operation distinct from settlement is not implemented")
    eq(o["initial"], [0, 0], "initial counters")
    eq(o["after_consume"], [0, 0], "consume counts as neither")
    eq(o["after_free"], [1, 0], "settlement counts a settlement")
    eq(o["refunded"], [0, 1], "refund counts a refund")
    eq(o["unlimited"], [1, 1, None, None], "both count even when no-op on unlimited")


JUDGES = {
    "test_open::test_open_feature__one_capacity_budget_decodes_limits_and_reserves_all_or_nothing": judge_open,
    "test_r1::test_rule__an_over_settled_axis_stops_at_a_quarter_of_the_limit_in_debt": judge_r1_rule,
    "test_r1::test_scope__the_floor_follows_the_normalised_limit_of_each_axis": judge_r1_scope,
    "test_r1::test_exclusions__capping_at_the_limit_and_staying_above_the_floor_do_not_count": judge_r1_exclusions,
    "test_r1::test_observability__the_clamp_counter_counts_calls_not_axes": judge_r1_observability,
    "test_r2::test_rule__a_refund_returns_the_whole_estimate_and_one_request_slot": judge_r2_rule,
    "test_r2::test_scope__both_failure_exits_refund_while_the_success_exit_settles": judge_r2_scope,
    "test_r2::test_exclusions__the_failure_refund_ignores_the_usage_the_response_reported": judge_r2_exclusions,
    "test_r2::test_observability__settlements_and_refunds_are_counted_apart_even_when_unlimited": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g10_token_capacity_budget" '
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
