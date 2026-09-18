"""g6 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g6 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks /tests to
root, so the worker cannot read the numbers below to forge an observation that
matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files
stay the human-readable source of truth and the fact<->test bijection. Where a
value is not pinnable without grading a hidden fact (the reason string the open
feature reads live; every discount stated as a RATIO rather than a number), the
worker records the live value and this judge checks the relation, exactly as the
tests do.
"""
from __future__ import annotations

import json
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr
import os

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlinks, size-capped) every
# agent-influenced path goes through; harness.py cannot: it imports pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402

REASON_STRINGS = {"unknown_provider", "unknown_model", "unknown_window"}
MODELPRICE_FIELDS = sorted((
    "model", "provider", "completion_window", "input_cost_per_million",
    "output_cost_per_million", "source", "batch", "output_price_inferred", "max_tokens"))
MAVERICK = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def _abs(x):
    return x if x >= 0 else -x


def approx_eq(a, b, *, rel: float = 1e-6, abs_: float = 1e-12) -> bool:
    return _abs(a - b) <= max(rel * _abs(b), abs_)


def approxs(got, want, msg="", *, rel=1e-6, abs_=1e-12):
    if not approx_eq(got, want, rel=rel, abs_=abs_):
        raise Fail(f"{msg}: {got!r} !~ {want!r}")


def raised_unpriced(info, *, reason=None, msg=""):
    ok(info.get("raised"), f"{msg}: expected an UnpricedModelError, none raised")
    ok("UnpricedModelError" in info.get("mro", []), f"{msg}: not UnpricedModelError: {info.get('mro')}")
    if reason is not None:
        eq(info.get("reason"), reason, f"{msg}: reason")


def raised_value_error(info, msg=""):
    ok(info.get("raised"), f"{msg}: expected a ValueError, none raised")
    ok("ValueError" in info.get("mro", []), f"{msg}: not a ValueError: {info.get('mro')}")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    ok(o["is_dataclass"], "ModelPrice must be a dataclass")
    ok(o["frozen"], "ModelPrice must be frozen")
    eq(o["fields"], MODELPRICE_FIELDS, "ModelPrice fields")

    ok(o["is_lookup_error"], "UnpricedModelError must subclass LookupError")
    ok(o["reasons_is_frozenset"], "REASONS must be a frozenset")
    reason = o["reason"]  # read live from the submission; never pinned here
    eq(o["err_str"], f"{reason}: model='ghost' provider='klusterai' completion_window='24h'", "error str")
    eq(o["err_tuple"], ["ghost", "klusterai", "24h", reason], "error attributes")
    raised_value_error(o["bad_reason_raises"], "undeclared reason must raise ValueError")

    ok(o["price_isinstance"], "resolve_model_price returns a ModelPrice")
    pf = o["price_fields"]
    eq(pf["model"], MAVERICK, "price.model")
    eq(pf["provider"], "klusterai", "price.provider")
    eq(pf["completion_window"], "*", "price.completion_window")
    eq([pf["input_cost_per_million"], pf["output_cost_per_million"]], [0.2, 0.8], "per-million")
    eq(pf["source"], "external", "price.source")
    ok(pf["batch"] is False, "price.batch is False")
    ok(pf["output_price_inferred"] is False, "price.output_price_inferred is False")
    eq(o["price_in_per_token"], 2e-07, "input_cost_per_token")
    eq(o["price_out_per_token"], 8e-07, "output_cost_per_token")

    eq(o["inferred_per_million"], [0.045, 0.045], "inferred per-million")
    ok(o["inferred_price_inferred"] is True, "output_price_inferred is True on inferred")

    eq(o["external_model_cost"], {"input_cost_per_token": 4.5e-08, "output_cost_per_token": 4.5e-08},
       "external_model_cost shim")
    ok(o["has_get_litellm_cost_map"] is False, "_get_litellm_cost_map was to be deleted")

    eq(o["entry_keys"], sorted(("max_tokens", "input_cost_per_token", "output_cost_per_token", "litellm_provider")),
       "register entry keys")
    eq(o["entry_in_per_token"], 2e-07, "entry input_cost_per_token")
    eq(o["entry_out_per_token"], 8e-07, "entry output_cost_per_token")
    eq(o["table_in_per_token"], 2e-07, "litellm table input")
    eq(o["table_out_per_token"], 8e-07, "litellm table output")
    raised_value_error(o["register_batch_raises"], "registering a batch price must raise ValueError")

    eq(o["fmt_price_plain"], ["$0.200", "$0.800"], "format plain")
    eq(o["fmt_price_rich"], ["[red]$0.200[/red]", "[red]$0.800[/red]"], "format rich")
    eq(o["fmt_inferred_plain"], ["$0.045", "$0.045*"], "format inferred plain")
    eq(o["fmt_inferred_rich"][0], "[red]$0.045[/red]", "format inferred rich[0]")
    ok(o["fmt_inferred_rich"][1] in ("[red]$0.045*[/red]", "[red]$0.045[/red]*"), "format inferred rich[1]")
    eq(o["fmt_none_plain"], ["N/A", "N/A"], "format None plain")
    eq(o["fmt_none_rich"], ["[dim]N/A[/dim]", "[dim]N/A[/dim]"], "format None rich")

    inferred_flags = {"batch": True, "inferred_online": True, "known_online": False}
    for label, want in inferred_flags.items():
        t = o["trackers"][label]
        ok(t["refresh_callable"], f"{label} has no refresh_model_price()")
        ok(t["reason"] is None, f"{label} price_unavailable_reason is None")
        ok(t["refresh_result_is_none"], f"{label} refresh returns None on success")
        ok(t["output_price_inferred"] is want, f"{label} output_price_inferred is {want}")
    eq(o["inferred_online_per_million"], [0.045, 0.045], "inferred online per-million")
    eq(o["inferred_online_str"], ["$0.045", "$0.045*"], "inferred online strings")
    eq(o["known_online_per_million"], [0.2, 0.8], "known online per-million")
    eq(o["known_online_str"], ["$0.200", "$0.800"], "known online strings")


# ---------------------------------------------------------------------------
# r1 — the failure contract
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["reasons"], sorted(REASON_STRINGS), "REASONS vocabulary")
    ok(o["checked"] > 0, "the external price table is empty; nothing was measured")
    for key, values in o["rows"].items():
        for value in values:
            ok(isinstance(value, (int, float)) and not isinstance(value, bool), f"{key}: {value!r} not a real price")
    for info in o["unanswerable"]:
        raised_unpriced(info, msg="unanswerable")
        ok(info.get("reason") in REASON_STRINGS, f"{info.get('reason')!r} is not a declared reason")


def judge_r1_exclusions(o):
    raised_unpriced(o["all_wrong"], reason="unknown_provider", msg="provider check first")
    raised_unpriced(o["model_wrong"], reason="unknown_model", msg="model check next")
    for name, info in o["broken"].items():
        raised_unpriced(info, reason="unknown_model", msg=f"broken row {name}")
    eq(o["wildcard"], 0.045, "wildcard tier price")
    raised_unpriced(o["unlisted_window"], reason="unknown_window", msg="unlisted window")


def judge_r1_observability(o):
    eq(o["seen"], ["unknown_provider", "unknown_model", "unknown_window"], "the three reasons, in order")
    for name, batch, cost in o["degraded_costs"]:
        eq(cost, 0.0, f"{name}(batch={batch}) did not degrade to 0.0")
    for label, t in o["trackers"].items():
        eq(t["before"], [None, None], f"{label} prices before")
        eq(t["reason_before"], "unknown_model", f"{label} reason before")
        eq(t["after"], [None, None], f"{label} prices after re-resolve")
        eq(t["reason_after"], "unknown_model", f"{label} reason after re-resolve")


# ---------------------------------------------------------------------------
# r2 — one owner of the batch discount
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    # A cost is completion_cost * batch_multiplier() and no more — checked as a
    # relation against the live raw figure and the live multiplier, so the number
    # the discount happens to be is observability's to pin, not rule's.
    for name, batch, mult, cost in o["applied_once"]:
        approxs(cost, o["raw"] * mult, f"{name}(batch={batch}) is not completion_cost * batch_multiplier()")
    for name, before, factor_before, after in o["substitution"]:
        ok(factor_before, f"{name} reports a zero multiplier")
        ok(before, f"{name} priced at zero; nothing to substitute against")
        approxs(after, before / factor_before * 3.0, f"{name} applies something other than batch_multiplier()")
    approxs(o["discounted"], o["listed"] * o["factor"], "resolve_model_price(batch=True) applies the one factor")


def judge_r2_scope(o):
    ok(0.0 < o["factor"] < 1.0, f"the batch discount factor is {o['factor']!r}")
    for name, mult in o["out_of_batch"]:
        eq(mult, 1.0, f"{name} out of batch")
    eq(o["azure_batch"], o["factor"], "azure discounts by the same factor")
    for name, batch, mult in o["external_batch"]:
        eq(mult, 1.0, f"{name}(batch={batch}) external table is not re-discounted")
    for row in o["external_rows"]:
        eq(row["source"], "external", f"{row['key']} source")
        eq(row["batched"], row["listed"], f"{row['key']} was discounted")
    eq(o["litellm_source"], "litellm", "litellm-sourced row source")
    for i in (0, 1):
        approxs(o["litellm_batched"][i], o["litellm_listed"][i] * o["factor"], f"litellm field {i} discount")


def judge_r2_exclusions(o):
    for name, mult, cost in o["user_supplied"]:
        eq(mult, 1.0, f"{name} discounted a user-supplied price")
        approxs(cost, o["raw"], f"{name} user-supplied cost")
    if o["flag"] is None:
        ok(o["has_overrides"], "a class-level flag (or per-class batch_multiplier override) marking exempt processors "
                               "is not implemented, so the constraint cannot be credited")
    else:
        eq(o["exempt_mult"], 1.0, "flipping the flag exempts a discounting class")
        eq(o["discounting_mult"], o["factor"], "flipping the flag makes an exempt class discount")
    eq(o["deepseek_source"], "litellm", "litellm priced it, so it is discounted")
    approxs(o["deepseek_batched_in"], o["deepseek_listed_in"] * o["factor"], "exemption follows the source, not the name")


def judge_r2_observability(o):
    eq(o["multipliers"], [0.5, 1.0, 0.5, 1.0, 1.0, 1.0], "the stated multiplier table")
    approxs(o["kluster_in_batch"], o["raw"], "klusterai in batch is undiscounted")
    approxs(o["kluster_out_of_batch"], o["raw"], "klusterai out of batch is undiscounted")
    eq(o["deepseek_listed"], 3.0, "DeepSeek listed price")
    eq(o["deepseek_batched"], 3.0, "DeepSeek batch price is the same batch tier")
    eq(o["litellm_listed_in"], 2.0, "litellm listed input")
    eq(o["litellm_batched_in"], 1.0, "litellm batched input is halved")
    eq(o["litellm_batched_out"], 4.0, "litellm batched output is halved")


JUDGES = {
    "test_open::test_open_feature__one_resolve_model_price_backs_the_price_the_error_the_registration_and_the_strings": judge_open,
    "test_r1::test_rule__a_failure_always_raises_one_of_three_named_reasons_instead_of_a_none_price": judge_r1_rule,
    "test_r1::test_exclusions__the_earlier_check_wins_and_neither_a_none_price_nor_a_wildcard_fallback_is_offered": judge_r1_exclusions,
    "test_r1::test_observability__the_three_reasons_read_back_and_every_caller_above_the_lookup_degrades": judge_r1_observability,
    "test_r2::test_rule__the_discount_is_applied_once_by_batch_multiplier_and_by_resolve_model_price": judge_r2_rule,
    "test_r2::test_scope__only_list_priced_sources_are_discounted_and_the_external_tables_are_left_alone": judge_r2_scope,
    "test_r2::test_exclusions__a_user_supplied_price_is_taken_as_given_and_exemption_follows_the_class_and_the_source": judge_r2_exclusions,
    "test_r2::test_observability__the_stated_multiplier_table_and_the_two_price_ratios_hold_exactly": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g6_model_price_lookup" '
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
        observations = json.loads(judge_io.read_text(obs_path))
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
