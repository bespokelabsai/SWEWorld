"""g1 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g1 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks /tests to
root, so the worker cannot read the numbers below to forge an observation that
matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files
stay the human-readable source of truth and the fact<->test bijection.
"""
from __future__ import annotations

import json
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

MODEL = "gpt-4o-mini"


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def has(surface, name, what="module"):
    ok(name in surface, f"{what} does not export {name}; it has {surface}")


def raised(info, *, mro=None, mro_absent=None, string=None, attrs=None, msg=""):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    for name in (mro or []):
        ok(name in info.get("mro", []), f"{msg}: {name} not in {info.get('mro')}")
    for name in (mro_absent or []):
        ok(name not in info.get("mro", []), f"{msg}: {name} unexpectedly in {info.get('mro')}")
    for attr, value in (attrs or {}).items():
        eq(info.get(attr), value, f"{msg}: {attr}")
    if string is not None:
        eq(info.get("str"), string, f"{msg}: message")


def check_cover(plan, n_rows, msg="cover"):
    """The same contiguous/ordered/exhaustive structure test_open asserts, over
    the tuples the probe recorded ([index, start, end, num_requests, num_bytes])."""
    ok(bool(plan), f"{msg}: the plan is empty")
    eq(plan[0][1], 0, f"{msg}: does not start at row 0")
    eq(plan[-1][2], n_rows, f"{msg}: does not reach row {n_rows}")
    for i, t in enumerate(plan):
        eq(t[0], i, f"{msg}: not indexed 0..n-1")
        eq(t[3], t[2] - t[1], f"{msg}: bad span {t}")
    for earlier, later in zip(plan, plan[1:]):
        eq(earlier[2], later[1], f"{msg}: not a contiguous cover")


# ---------------------------------------------------------------------------
# open feature — the whole stated surface, planner, files
# ---------------------------------------------------------------------------
REQUIRED_SURFACE = ["BatchLimits", "PlannedBatch", "payload_size_bytes", "payload_bytes",
                    "plan_batches", "BatchPayloadTooLargeError", "SingleRequestTooLargeError"]


def judge_open(o):
    for name in REQUIRED_SURFACE:
        has(o["surface"], name)
    ok("ValueError" in o["btle_mro"], f"BatchPayloadTooLargeError does not subclass ValueError: {o['btle_mro']}")
    ok("BatchPayloadTooLargeError" in o["srtle_mro"], f"SingleRequestTooLargeError does not subclass BatchPayloadTooLargeError: {o['srtle_mro']}")
    eq(o["error_fields"], [2, 99, 50], "BatchPayloadTooLargeError fields")

    eq(o["row_0_request"], {
        "custom_id": "0",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": MODEL, "messages": [{"role": "user", "content": "say 0"}]},
    }, "the OpenAI batch request shape")
    eq(o["payload_size_row0"], 153, "payload_size_bytes(row 0)")
    eq(o["generic_len"], 217, "the generic request is 217 bytes")
    eq(o["measure_generic"], 153, "measure_request_payload")

    eq(o["payload_bytes"], [0, 10, 32], "payload_bytes")

    eq(o["plan_empty"], [], "plan_batches([])")
    eq(o["plan_7_1000_32"], [[0, 0, 3, 3, 32], [1, 3, 6, 3, 32], [2, 6, 7, 1, 10]], "greedy fill, byte-bound")
    eq(o["plan_6_3_32"], [[0, 0, 3, 3, 32], [1, 3, 6, 3, 32]], "greedy fill, request-bound")

    raised(o["raise_single"], mro=["SingleRequestTooLargeError", "BatchPayloadTooLargeError", "ValueError"],
           attrs={"row_idx": 1, "size_bytes": 500, "limit_bytes": 32, "num_requests": 1}, msg="single oversize")

    eq(o["batch_limits"], [7, 4242], "batch_limits mirrors the two properties")

    plan = o["plan_5_3_400"]
    eq(plan, [[0, 0, 2, 2, 307], [1, 2, 4, 2, 307], [2, 4, 5, 1, 153]], "plan of 5 rows at 3/400")
    check_cover(plan, 5)
    eq(o["result_rel"], ["requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl"], "create_request_files result")
    eq(o["batch_rows"], [list(range(t[1], t[2])) for t in plan], "each file holds its planned rows")
    eq(o["batch_meta_numjobs"], [t[3] for t in plan], "metadata num_jobs == num_requests")

    ok(o["empty_batch_file_empty"], "create_batch_file([]) == b''")
    eq(o["built_sizes"], [t[4] for t in plan], "built file size == planned num_bytes")

    eq(o["gp_plan"], [[0, 0, 2, 2, 347], [1, 2, 4, 2, 347], [2, 4, 6, 2, 347]], "gen-params plan")
    eq(o["gp_line_counts"], [2, 2, 2], "gen-params file line counts")

    eq(o["wide_basenames"], [f"requests_{i}.jsonl" for i in range(11)], "one file per planned batch, numeric order")

    eq(o["empty_plan"], [], "zero rows plans zero batches")
    eq(o["empty_create_result"], [], "zero rows writes no file")
    eq(o["empty_glob_requests"], [], "no stray request files")
    eq(o["empty_glob_metadata"], [], "no stray metadata files")

    eq(o["fixed_result_rel"], ["requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl"], "explicit-integer result")
    eq(o["fixed_line_counts"], [2, 2, 1], "explicit-integer line counts")


# ---------------------------------------------------------------------------
# r1 — the plan is written down, in a versioned sidecar
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    for name in ("PLAN_FILE_NAME", "PLAN_FORMAT_VERSION", "plan_fingerprint", "plan_document"):
        has(o["surface"], name)
    eq(o["plan_file_name"], "batch_plan.json", "PLAN_FILE_NAME")
    eq(o["plan_format_version"], 1, "PLAN_FORMAT_VERSION")

    eq(o["fp_same"], o["fp_relabelled"], "plan_fingerprint changed when only index/num_requests changed")
    ok(o["fp_same"] != o["fp_diff_size"], "plan_fingerprint ignores the batch sizes")
    ok(o["fp_same"] != o["fp_diff_cut"], "plan_fingerprint ignores where the cuts fall")

    eq(o["plan_len"], 3, "five rows at 3/400 should plan 3 batches")
    eq(o["doc_keys"], ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests", "num_bytes", "batches"], "sidecar envelope keys")
    eq(o["doc_format_version"], 1, "doc plan_format_version")
    ok(o["doc_plan_id_eq_fp"], "doc plan_id != plan_fingerprint(plan)")
    ok(o["doc_limits_eq_asdict"], "doc limits != asdict(limits)")
    ok(o["doc_num_batches_eq"], "doc num_batches != len(plan)")
    ok(o["doc_num_requests_eq"], "doc num_requests != sum")
    ok(o["doc_num_bytes_eq"], "doc num_bytes != sum")
    ok(o["doc_batches_eq_asdict"], "doc batches != [asdict(p)]")
    eq(o["batch0_keys"], ["index", "start_idx", "end_idx", "num_requests", "num_bytes"], "a batch entry's keys")
    ok(o["doc_eq_plan_document"], "doc != plan_document(plan, limits)")


def judge_r1_scope(o):
    ok(o["ordered_sidecar_exists"], 'the "auto" branch wrote no plan sidecar')
    if o["ordered_reused_acreate"]:
        ok(o["ordered_plan_exists_on_first_call"] is True, "the sidecar was written after the request files, not before them")

    eq(o["empty_create_result"], [], "empty auto run returns []")
    eq(o["empty_doc_tuple"], [0, 0, 0, []], "a 0-batch plan is still recorded")
    ok(o["empty_doc_plan_id_eq_fp"], "empty doc plan_id != plan_fingerprint([])")

    ok(o["fixed_no_sidecar"], "the explicit-integer branch wrote a plan sidecar")
    ok(o["none_no_sidecar"], "the `dataset is None` path wrote a plan sidecar")


def judge_r1_exclusions(o):
    ok(o["sidecar_exists"], "the batch_plan.json sidecar is not implemented, so the constraint cannot be credited")  # require_feature
    for keys in o["meta_keysets"]:
        eq(keys, ["num_jobs"], "metadata carries plan fields it should not")
    eq(o["meta_numjobs"], [t[3] for t in o["plan"]], "metadata num_jobs == num_requests")


def judge_r1_failure_behavior(o):
    has(o["surface"], "BatchPlanTooFragmentedError")
    ok("ValueError" in o["bptfe_mro"], f"BatchPlanTooFragmentedError does not subclass ValueError: {o['bptfe_mro']}")
    ok("BatchPayloadTooLargeError" not in o["bptfe_mro"], "a fragmented plan is not an oversized payload")

    eq(o["len_512"], 512, "512 batches is the boundary and it is admissible")
    raised(o["raise_513"], mro=["BatchPlanTooFragmentedError"], attrs={"num_batches": 513, "limit": 512}, msg="513 batches")
    raised(o["raise_explicit_cap"], mro=["BatchPlanTooFragmentedError"], attrs={"num_batches": 3, "limit": 2}, msg="explicit max_batches_per_plan")
    raised(o["raise_oversize_first"], mro=["SingleRequestTooLargeError"], attrs={"row_idx": 600}, msg="per-row scan wins")


def judge_r1_observability(o):
    eq(o["fp_empty"], "e3b0c44298fc", "plan_fingerprint([])")
    eq(o["fp_7"], "ad0828fea95e", "plan_fingerprint of the 7-row plan")
    eq(o["fp_3batches"], "f4b1ea1573c0", "plan_fingerprint of the 3-batch plan")
    eq(o["wide_len"], 11, "11 rows at one per batch")
    eq(o["fp_wide"], "c53f6fb95c13", "plan_fingerprint of the 11-batch plan")

    expected_doc = {
        "plan_format_version": 1,
        "plan_id": "f4b1ea1573c0",
        # from the implementation's own limits, so the fan-out cap is graded
        # once, under failure_behavior, and not a second time here.
        "limits": o["limits_asdict"],
        "num_batches": 3,
        "num_requests": 5,
        "num_bytes": 767,
        "batches": [
            {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307},
            {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307},
            {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153},
        ],
    }
    eq(o["doc"], expected_doc, "the document the 5-row run leaves behind")
    eq(o["doc_limits_maxreq"], 3, "doc limits max_requests_per_batch")
    eq(o["doc_limits_maxbytes"], 400, "doc limits max_bytes_per_batch")
    ok(o["raw_tail"].endswith("]\n}\n"), f"the sidecar is not indented JSON with a trailing newline: {o['raw_tail']!r}")


# ---------------------------------------------------------------------------
# r2 — the "auto" branch sweeps its stale numbering
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    n = o["plan_len"]
    ok(1 <= n <= 5, f"five rows planned {n} batches")
    eq(o["req_glob"], [f"requests_{i}.jsonl" for i in range(n)], "stale request files survived the run")
    eq(o["meta_glob"], [f"metadata_{i}.json" for i in range(n)], "stale metadata files survived the run")
    first = o["plan"][0]
    eq(o["req0_rows"], list(range(first[1], first[2])), "requests_0.jsonl holds the new run's rows")


def judge_r2_scope(o):
    ok(o["swept_proof"], 'the "auto" branch\'s sweep of stale request files is not implemented')  # require_feature
    ok(all(o["fixed_req_exists"]), "the explicit-integer branch removed a stale request file")
    ok(all(o["fixed_meta_exists"]), "the explicit-integer branch removed a stale metadata file")
    eq(o["fixed_req5_content"], "stale\n", "the explicit-integer branch rewrote requests_5.jsonl")
    ok(all(o["none_req_exists"]), "the `dataset is None` path removed a stale request file")
    ok(all(o["none_meta_exists"]), "the `dataset is None` path removed a stale metadata file")
    eq(o["none_req3_content"], "stale\n", "the `dataset is None` path rewrote requests_3.jsonl")


def judge_r2_exclusions(o):
    ok(o["swept"], 'the "auto" branch\'s sweep of stale request files is not implemented')  # require_feature
    for name, intact in o["keepers_intact"].items():
        ok(intact, f"the sweep touched {name}, which is not a request or metadata file")


def judge_r2_failure_behavior(o):
    ok(o["swept_proof"], 'the "auto" branch\'s sweep of stale request files is not implemented')  # require_feature
    eq(o["before_len"], 14, "the pre-populated working dir should hold 14 files")
    raised(o["raise_plan"], mro=["SingleRequestTooLargeError"], attrs={"row_idx": 1}, msg="planning raises on the oversize row")
    raised(o["raise_create"], mro=["SingleRequestTooLargeError"], msg="create_request_files raises")
    ok(o["unchanged"], "a planning failure changed the working directory")


def judge_r2_observability(o):
    eq(o["good_listing"], [
        "metadata_0.json", "metadata_1.json", "metadata_2.json",
        "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", "responses_0.jsonl",
    ], "the working dir after a successful run")
    eq(o["good_responses_content"], "keep\n", "the bystander survived the successful run")
    raised(o["bad_plan_raises"], mro=["SingleRequestTooLargeError"], msg="bad plan raises")
    raised(o["bad_create_raises"], mro=["SingleRequestTooLargeError"], msg="bad create raises")
    eq(o["bad_listing"], [
        "batch_plan.json",
        "metadata_0.json", "metadata_1.json", "metadata_2.json",
        "metadata_3.json", "metadata_4.json", "metadata_5.json",
        "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl",
        "requests_3.jsonl", "requests_4.jsonl", "requests_5.jsonl",
        "responses_0.jsonl",
    ], "the working dir after a failed run")
    eq(o["bad_plan_content"], {"plan_format_version": 1, "stale": True}, "the stale sidecar survived the failed run")
    eq(o["bad_req2_content"], "stale\n", "a stale request file survived the failed run")


JUDGES = {
    "test_open::test_open_feature__auto_plans_batches_and_writes_one_file_per_planned_batch": judge_open,
    "test_r1::test_rule__the_auto_branch_records_the_plan_in_a_versioned_sidecar": judge_r1_rule,
    "test_r1::test_scope__only_the_auto_branch_writes_it_and_an_empty_plan_still_does": judge_r1_scope,
    "test_r1::test_exclusions__metadata_files_still_hold_num_jobs_and_nothing_else": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_plan_of_more_than_512_batches_is_refused": judge_r1_failure_behavior,
    "test_r1::test_observability__plan_id_is_the_first_twelve_hex_of_sha256_over_the_cuts": judge_r1_observability,
    "test_r2::test_rule__stale_request_and_metadata_files_are_removed_by_the_auto_branch": judge_r2_rule,
    "test_r2::test_scope__the_explicit_integer_branch_and_the_none_path_leave_files_alone": judge_r2_scope,
    "test_r2::test_exclusions__nothing_but_request_and_metadata_files_is_touched": judge_r2_exclusions,
    "test_r2::test_failure_behavior__a_planning_failure_removes_and_writes_nothing": judge_r2_failure_behavior,
    "test_r2::test_observability__the_working_directory_after_a_successful_and_a_failed_run": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g1_batch_payload_plan" '
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
