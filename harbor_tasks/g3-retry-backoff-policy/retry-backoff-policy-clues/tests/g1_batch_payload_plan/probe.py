"""g1 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks /tests to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass (the plan_id digests, the byte counts, the sidecar document, the fan-out
cap) live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2` via
`probe_support`, same helpers, so a value here is the value the test saw. The
judge holds the assertions those tests made. A submission that returns forged
values only forges values the judge still checks against the real expectations —
which is implementing them.

Two g1-specific reproduction rules:

  * the probe is not under pytest, so every scenario gets its own
    `tempfile.mkdtemp()` (`probe_support.make_tmp_dir`) in place of the
    `tmp_path` fixture;
  * for the byte-exact and file-listing facts the probe records the RAW values
    (the dict a request serialises to, the directory listing, a file's text)
    and lets the judge assert the exact count/spelling — it never carries 153,
    767, 512, the plan_id hex, or the sidecar's JSON here. For a path in a temp
    directory, it records the path RELATIVE to that dir, so the judge grades the
    basename and the directory without needing the run's own random tmp path.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

# probe_support owns the curator imports and the answer-free helpers/inputs;
# reuse them so a probe calls curator exactly as the test does. Importing it runs
# the submission's `import bespokelabs.curator` — this process's whole purpose,
# and why it is disposable. The worker never imports test_open/test_r*, whose
# source carries the expected answer literals.
import probe_support as S  # noqa: E402
from harness import read_field, surface  # noqa: E402


def raises(fn, *args, attrs=(), **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, its str, and the
    named attributes an exception carries (row_idx, size_bytes, num_batches, …)."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        for attr in attrs:
            if hasattr(exc, attr):
                info[attr] = getattr(exc, attr)
        return info
    return {"raised": False, "mro": []}


def relpaths(paths, base):
    """Each path relative to `base`, so the judge grades the basename and the
    directory without seeing this run's random tmp path."""
    return [os.path.relpath(p, str(base)) for p in paths]


# ===========================================================================
# open feature — the whole stated surface, planner, files (one fact)
# ===========================================================================
def probe_open() -> dict:
    module = S.planner()
    o: dict = {}

    # --- the module's surface, and the two exception hierarchies ------------
    o["surface"] = surface(module)
    o["btle_mro"] = [c.__name__ for c in module.BatchPayloadTooLargeError.__mro__]
    o["srtle_mro"] = [c.__name__ for c in module.SingleRequestTooLargeError.__mro__]
    error = module.BatchPayloadTooLargeError(num_requests=2, size_bytes=99, limit_bytes=50)
    o["error_fields"] = [read_field(error, "num_requests"), read_field(error, "size_bytes"), read_field(error, "limit_bytes")]

    # --- serialization: stock json.dumps, then UTF-8 ------------------------
    run_dir = S.make_tmp_dir()
    processor = S.make_processor(os.path.join(run_dir, "run"))
    row_0_request = S.api_requests_for(processor, S.prompt_dataset(1), 0, 1)[0]
    o["row_0_request"] = row_0_request
    o["payload_size_row0"] = module.payload_size_bytes(row_0_request)
    generic = processor.prompt_formatter.create_generic_request({"prompt": "say 0"}, 0, False)
    o["generic_len"] = len(json.dumps(generic.model_dump(), default=str).encode())
    o["measure_generic"] = processor.measure_request_payload(generic)

    # --- file accounting: the n-1 separators of "\n".join(...) --------------
    o["payload_bytes"] = [module.payload_bytes([]), module.payload_bytes([10]), module.payload_bytes([10, 10, 10])]

    # --- greedy forward fill, both limits inclusive, exhaustive spans -------
    o["plan_empty"] = S.tuples(module.plan_batches([], S.limits_of(module, 50_000, 200 * 1024 * 1024)))
    o["plan_7_1000_32"] = S.tuples(module.plan_batches([10] * 7, S.limits_of(module, 1000, 32)))
    o["plan_6_3_32"] = S.tuples(module.plan_batches([10] * 6, S.limits_of(module, 3, 32)))

    # --- one row bigger than the byte budget raises, it does not stall ------
    o["raise_single"] = raises(module.plan_batches, [10, 500, 10], S.limits_of(module, 1000, 32),
                               attrs=("row_idx", "size_bytes", "limit_bytes", "num_requests"))

    # --- batch_limits mirrors the processor's own two properties ------------
    with S.patched_limits(max_requests=7, max_bytes=4242):
        got = processor.batch_limits
        o["batch_limits"] = [read_field(got, "max_requests_per_batch"), read_field(got, "max_bytes_per_batch")]

    # --- planning a dataset: the byte limit binds at 2 rows per batch -------
    dataset = S.prompt_dataset(5)
    with S.patched_limits(max_requests=3, max_bytes=400):
        plan = processor.plan_request_batches(dataset)
        o["plan_5_3_400"] = S.tuples(plan)
        result = processor.create_request_files(dataset)

    inner = os.path.join(run_dir, "run")
    o["result_rel"] = relpaths(result, inner)
    o["batch_rows"] = [S.row_indices(os.path.join(inner, f"requests_{read_field(p, 'index')}.jsonl")) for p in plan]
    o["batch_meta_numjobs"] = [S.metadata_of(inner, read_field(p, "index"))["num_jobs"] for p in plan]

    # --- the planned size is the size of the file that is actually built ----
    o["empty_batch_file_empty"] = processor.create_batch_file([]) == b""
    built_sizes = []
    for p in plan:
        requests = S.api_requests_for(processor, dataset, read_field(p, "start_idx"), read_field(p, "end_idx"))
        with S.patched_limits(max_requests=3, max_bytes=400):
            built = processor.create_batch_file(requests)
        built_sizes.append(len(built))
    o["built_sizes"] = built_sizes

    # --- row-level generation_params are part of the measured payload ------
    gp_dir = S.make_tmp_dir()
    gp_processor = S.make_processor(os.path.join(gp_dir, "genparams"))
    gp_dataset = S.genparams_dataset(6)
    with S.patched_limits(max_requests=1_000_000, max_bytes=480):
        gp_plan = gp_processor.plan_request_batches(gp_dataset)
        o["gp_plan"] = S.tuples(gp_plan)
        gp_processor.create_request_files(gp_dataset)
    gp_inner = os.path.join(gp_dir, "genparams")
    o["gp_line_counts"] = [len(S.request_lines(os.path.join(gp_inner, f"requests_{i}.jsonl"))) for i in range(3)]

    # --- every file the plan asked for comes back, in numeric order ---------
    wide_dir = os.path.join(S.make_tmp_dir(), "wide")
    wide = S.make_processor(wide_dir)
    with S.patched_limits(max_requests=1):
        wide_result = wide.create_request_files(S.prompt_dataset(11))
    o["wide_basenames"] = S.basenames(wide_result)

    # --- zero rows plans zero batches and writes no request file -----------
    from datasets import Dataset
    empty_dir = os.path.join(S.make_tmp_dir(), "empty")
    empty = S.make_processor(empty_dir)
    with S.patched_limits(max_requests=3, max_bytes=400):
        o["empty_plan"] = S.tuples(empty.plan_request_batches(Dataset.from_dict({"prompt": []})))
        o["empty_create_result"] = empty.create_request_files(Dataset.from_dict({"prompt": []}))
    import glob
    o["empty_glob_requests"] = glob.glob(os.path.join(empty_dir, "requests_*.jsonl"))
    o["empty_glob_metadata"] = glob.glob(os.path.join(empty_dir, "metadata_*.json"))

    # --- the explicit-integer branch is untouched ---------------------------
    fixed_dir = os.path.join(S.make_tmp_dir(), "fixed")
    fixed = S.make_processor(fixed_dir, batch_size=2)
    fixed_result = fixed.create_request_files(dataset)
    o["fixed_result_rel"] = relpaths(fixed_result, fixed_dir)
    o["fixed_line_counts"] = [len(S.request_lines(path)) for path in fixed_result]
    return o


# ===========================================================================
# r1 — the plan is written down, in a versioned sidecar
# ===========================================================================
def probe_r1_rule() -> dict:
    module = S.planner()
    PB = module.PlannedBatch
    o: dict = {}

    o["surface"] = surface(module)
    o["plan_file_name"] = module.PLAN_FILE_NAME
    o["plan_format_version"] = module.PLAN_FORMAT_VERSION

    # the fingerprint is taken over where the cuts fall and how big each batch
    # is: index/num_requests do not enter it. All checks are RELATIONAL, so no
    # digest literal is needed here (observability grades the exact hex).
    o["fp_same"] = module.plan_fingerprint([PB(0, 0, 2, 2, 307), PB(1, 2, 4, 2, 307)])
    o["fp_relabelled"] = module.plan_fingerprint([PB(5, 0, 2, 99, 307), PB(9, 2, 4, 77, 307)])
    o["fp_diff_size"] = module.plan_fingerprint([PB(0, 0, 2, 2, 307), PB(1, 2, 4, 2, 308)])
    o["fp_diff_cut"] = module.plan_fingerprint([PB(0, 0, 3, 3, 307), PB(1, 3, 4, 1, 307)])

    dataset = S.prompt_dataset(5)
    processor, plan, working_dir, limits = S.auto_run(dataset)
    o["plan"] = S.tuples(plan)
    o["plan_len"] = len(plan)

    doc = S.load_plan_file(module, working_dir)
    o["doc_keys"] = list(doc)
    o["doc_format_version"] = doc["plan_format_version"]
    o["doc_plan_id_eq_fp"] = doc["plan_id"] == module.plan_fingerprint(plan)
    o["doc_limits_eq_asdict"] = doc["limits"] == dataclasses.asdict(limits)
    o["doc_num_batches_eq"] = doc["num_batches"] == len(plan)
    o["doc_num_requests_eq"] = doc["num_requests"] == sum(read_field(p, "num_requests") for p in plan)
    o["doc_num_bytes_eq"] = doc["num_bytes"] == sum(read_field(p, "num_bytes") for p in plan)
    o["doc_batches_eq_asdict"] = doc["batches"] == [dataclasses.asdict(p) for p in plan]
    o["batch0_keys"] = list(doc["batches"][0])
    o["doc_eq_plan_document"] = doc == json.loads(json.dumps(module.plan_document(plan, limits)))
    return o


def probe_r1_scope() -> dict:
    module = S.planner()
    o: dict = {}
    plan_name = module.PLAN_FILE_NAME  # r1's rule owns the name; here it is a lookup key

    # --- written before any request file of its own run --------------------
    working_dir = os.path.join(S.make_tmp_dir(), "ordered")
    processor = S.make_processor(working_dir)
    seen = {}
    original = processor.acreate_request_file

    async def recording(*args, **kwargs):
        seen.setdefault("plan_exists", os.path.exists(os.path.join(working_dir, plan_name)))
        return await original(*args, **kwargs)

    processor.acreate_request_file = recording
    with S.patched_limits(max_requests=3, max_bytes=400):
        processor.create_request_files(S.prompt_dataset(5))
    o["ordered_sidecar_exists"] = os.path.isfile(os.path.join(working_dir, plan_name))
    o["ordered_reused_acreate"] = bool(seen)
    o["ordered_plan_exists_on_first_call"] = seen.get("plan_exists")

    # --- a 0-batch plan is still recorded ----------------------------------
    from datasets import Dataset
    empty_dir = os.path.join(S.make_tmp_dir(), "empty")
    empty = S.make_processor(empty_dir)
    with S.patched_limits(max_requests=3, max_bytes=400):
        o["empty_create_result"] = empty.create_request_files(Dataset.from_dict({"prompt": []}))
    empty_doc = S.load_plan_file(module, empty_dir)
    o["empty_doc_tuple"] = [empty_doc["num_batches"], empty_doc["num_requests"], empty_doc["num_bytes"], empty_doc["batches"]]
    o["empty_doc_plan_id_eq_fp"] = empty_doc["plan_id"] == module.plan_fingerprint([])

    # --- the explicit-integer branch never writes it -----------------------
    fixed_dir = os.path.join(S.make_tmp_dir(), "fixed")
    fixed = S.make_processor(fixed_dir, batch_size=2)
    fixed.create_request_files(S.prompt_dataset(3))
    o["fixed_no_sidecar"] = plan_name not in os.listdir(fixed_dir)

    # --- and neither does the `dataset is None` path -----------------------
    none_dir = os.path.join(S.make_tmp_dir(), "none")
    none_processor = S.make_processor(none_dir)
    with S.patched_limits(max_requests=3, max_bytes=400):
        none_processor.create_request_files(None)
    o["none_no_sidecar"] = plan_name not in os.listdir(none_dir)
    return o


def probe_r1_exclusions() -> dict:
    module = S.planner()
    o: dict = {}
    dataset = S.prompt_dataset(5)
    processor, plan, working_dir, _limits = S.auto_run(dataset)

    o["sidecar_exists"] = os.path.isfile(S.plan_path(module, working_dir))
    o["plan"] = S.tuples(plan)
    o["meta_keysets"] = [sorted(S.metadata_of(working_dir, read_field(p, "index"))) for p in plan]
    o["meta_numjobs"] = [S.metadata_of(working_dir, read_field(p, "index"))["num_jobs"] for p in plan]
    return o


def probe_r1_failure_behavior() -> dict:
    module = S.planner()
    o: dict = {}
    o["surface"] = surface(module)
    o["bptfe_mro"] = [c.__name__ for c in module.BatchPlanTooFragmentedError.__mro__]

    one_per_batch = module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000)
    o["len_512"] = len(module.plan_batches([10] * 512, one_per_batch))

    o["raise_513"] = raises(module.plan_batches, [10] * 513, one_per_batch, attrs=("num_batches", "limit"))
    o["raise_explicit_cap"] = raises(
        module.plan_batches, [10] * 3,
        module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000, max_batches_per_plan=2),
        attrs=("num_batches", "limit"),
    )
    # the per-row oversize scan runs first: a dataset tripping both raises for the row
    o["raise_oversize_first"] = raises(module.plan_batches, [10] * 600 + [5000], one_per_batch, attrs=("row_idx",))
    return o


def probe_r1_observability() -> dict:
    module = S.planner()
    PB = module.PlannedBatch
    o: dict = {}

    o["fp_empty"] = module.plan_fingerprint([])
    o["fp_7"] = module.plan_fingerprint(module.plan_batches([10] * 7, module.BatchLimits(max_requests_per_batch=1000, max_bytes_per_batch=32)))
    o["fp_3batches"] = module.plan_fingerprint([PB(0, 0, 2, 2, 307), PB(1, 2, 4, 2, 307), PB(2, 4, 5, 1, 153)])

    # the 11-batch plan of an 11-row dataset, one request per batch
    wide_dir = os.path.join(S.make_tmp_dir(), "wide")
    wide = S.make_processor(wide_dir)
    with S.patched_limits(max_requests=1):
        wide_plan = wide.plan_request_batches(S.prompt_dataset(11))
    o["wide_len"] = len(wide_plan)
    o["fp_wide"] = module.plan_fingerprint(wide_plan)

    # --- and the document the 5-row run leaves behind -----------------------
    dataset = S.prompt_dataset(5)
    processor, plan, working_dir, limits = S.auto_run(dataset)
    doc = S.load_plan_file(module, working_dir)
    o["doc"] = doc
    # the fan-out cap is graded once, under failure_behavior; carry the impl's
    # own limits so the judge substitutes them rather than re-asserting the cap.
    o["limits_asdict"] = json.loads(json.dumps(dataclasses.asdict(limits)))
    o["doc_limits_maxreq"] = doc["limits"]["max_requests_per_batch"]
    o["doc_limits_maxbytes"] = doc["limits"]["max_bytes_per_batch"]

    with open(S.plan_path(module, working_dir)) as handle:
        raw = handle.read()
    o["raw_tail"] = raw[-20:]
    return o


# ===========================================================================
# r2 — the "auto" branch sweeps its stale numbering
# ===========================================================================
# r2-specific INPUTS: the name of a stale sidecar the probe plants, and the fake
# body it holds. Both are inputs (a bystander file left by an earlier run) — the
# name coincides with r1's PLAN_FILE_NAME answer, which the judge holds its own
# copy of; the failure path leaves this file byte-for-byte, so the "answer" is
# the input the probe planted.
PLAN_FILE = "batch_plan.json"
STALE_SIDECAR_BODY = json.dumps({"plan_format_version": 1, "stale": True}) + "\n"


def probe_r2_rule() -> dict:
    S.planner()  # the feature under test cannot exist without the planner module
    o: dict = {}
    working_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "run"))
    processor = S.make_processor(working_dir)
    dataset = S.prompt_dataset(5)

    with S.patched_limits(max_requests=3, max_bytes=400):
        plan = processor.plan_request_batches(dataset)
        processor.create_request_files(dataset)
    o["plan"] = S.tuples(plan)
    o["plan_len"] = len(plan)

    import glob
    o["req_glob"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(working_dir, "requests_*.jsonl")))
    o["meta_glob"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(working_dir, "metadata_*.json")))
    o["req0_rows"] = S.row_indices(os.path.join(working_dir, "requests_0.jsonl"))
    return o


def probe_r2_scope() -> dict:
    S.planner()
    o: dict = {}
    o["swept_proof"] = S.swept()

    # --- explicit-integer batch_size: incomplete_files still owns the numbering
    fixed_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "fixed"))
    fixed = S.make_processor(fixed_dir, batch_size=2)
    fixed.create_request_files(S.prompt_dataset(3))
    o["fixed_req_exists"] = [os.path.exists(os.path.join(fixed_dir, f"requests_{i}.jsonl")) for i in (2, 3, 4, 5)]
    o["fixed_meta_exists"] = [os.path.exists(os.path.join(fixed_dir, f"metadata_{i}.json")) for i in (2, 3, 4, 5)]
    o["fixed_req5_content"] = open(os.path.join(fixed_dir, "requests_5.jsonl")).read()

    # --- the `dataset is None` path writes requests_0.jsonl and nothing else changes
    none_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "none"))
    none_processor = S.make_processor(none_dir)
    with S.patched_limits(max_requests=3, max_bytes=400):
        none_processor.create_request_files(None)
    o["none_req_exists"] = [os.path.exists(os.path.join(none_dir, f"requests_{i}.jsonl")) for i in (1, 2, 3, 4, 5)]
    o["none_meta_exists"] = [os.path.exists(os.path.join(none_dir, f"metadata_{i}.json")) for i in (1, 2, 3, 4, 5)]
    o["none_req3_content"] = open(os.path.join(none_dir, "requests_3.jsonl")).read()
    return o


def probe_r2_exclusions() -> dict:
    S.planner()
    o: dict = {}
    keepers = {
        "responses_0.jsonl": "keep\n",
        "responses_1.jsonl": '{"row_idx": 1}\n',
        "batch_objects.jsonl": '{"id": "batch_abc"}\n',
        "a1b2c3.arrow": "not really arrow, but not ours to delete\n",
        "notes.txt": "hand-written\n",
    }
    working_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "run"), extra=keepers)
    before = {name: S.snapshot(working_dir)[name] for name in keepers}

    processor = S.make_processor(working_dir)
    with S.patched_limits(max_requests=3, max_bytes=400):
        processor.create_request_files(S.prompt_dataset(5))

    o["swept"] = not os.path.exists(os.path.join(working_dir, "requests_5.jsonl"))
    after = S.snapshot(working_dir)
    o["keepers_intact"] = {name: bool(name in after and after.get(name) == body) for name, body in before.items()}
    return o


def probe_r2_failure_behavior() -> dict:
    module = S.planner()
    o: dict = {}
    o["swept_proof"] = S.swept()

    working_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "run"),
                                extra={"responses_0.jsonl": "keep\n", PLAN_FILE: STALE_SIDECAR_BODY})
    processor = S.make_processor(working_dir)
    before = S.snapshot(working_dir)
    o["before_len"] = len(before)

    dataset = S.big_dataset()

    def plan_it():
        with S.patched_limits(max_requests=3, max_bytes=400):
            processor.plan_request_batches(dataset)

    def create_it():
        with S.patched_limits(max_requests=3, max_bytes=400):
            processor.create_request_files(dataset)

    o["raise_plan"] = raises(plan_it, attrs=("row_idx",))
    o["raise_create"] = raises(create_it)
    o["unchanged"] = S.snapshot(working_dir) == before
    return o


def probe_r2_observability() -> dict:
    module = S.planner()
    o: dict = {}

    good_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "good"), extra={"responses_0.jsonl": "keep\n"})
    good = S.make_processor(good_dir)
    with S.patched_limits(max_requests=3, max_bytes=400):
        good.create_request_files(S.prompt_dataset(5))
    o["good_listing"] = S.listing(good_dir, keep={"responses_0.jsonl"})
    o["good_responses_content"] = open(os.path.join(good_dir, "responses_0.jsonl")).read()

    bad_dir = S.prepopulate(os.path.join(S.make_tmp_dir(), "bad"),
                            extra={"responses_0.jsonl": "keep\n", PLAN_FILE: STALE_SIDECAR_BODY})
    bad = S.make_processor(bad_dir)

    def plan_it():
        with S.patched_limits(max_requests=3, max_bytes=400):
            bad.plan_request_batches(S.big_dataset())

    def create_it():
        with S.patched_limits(max_requests=3, max_bytes=400):
            bad.create_request_files(S.big_dataset())

    o["bad_plan_raises"] = raises(plan_it)
    o["bad_create_raises"] = raises(create_it)
    o["bad_listing"] = sorted(os.listdir(bad_dir))
    o["bad_plan_content"] = json.load(open(os.path.join(bad_dir, PLAN_FILE)))
    o["bad_req2_content"] = open(os.path.join(bad_dir, "requests_2.jsonl")).read()
    return o


PROBES = {
    "test_open::test_open_feature__auto_plans_batches_and_writes_one_file_per_planned_batch": probe_open,
    "test_r1::test_rule__the_auto_branch_records_the_plan_in_a_versioned_sidecar": probe_r1_rule,
    "test_r1::test_scope__only_the_auto_branch_writes_it_and_an_empty_plan_still_does": probe_r1_scope,
    "test_r1::test_exclusions__metadata_files_still_hold_num_jobs_and_nothing_else": probe_r1_exclusions,
    "test_r1::test_failure_behavior__a_plan_of_more_than_512_batches_is_refused": probe_r1_failure_behavior,
    "test_r1::test_observability__plan_id_is_the_first_twelve_hex_of_sha256_over_the_cuts": probe_r1_observability,
    "test_r2::test_rule__stale_request_and_metadata_files_are_removed_by_the_auto_branch": probe_r2_rule,
    "test_r2::test_scope__the_explicit_integer_branch_and_the_none_path_leave_files_alone": probe_r2_scope,
    "test_r2::test_exclusions__nothing_but_request_and_metadata_files_is_touched": probe_r2_exclusions,
    "test_r2::test_failure_behavior__a_planning_failure_removes_and_writes_nothing": probe_r2_failure_behavior,
    "test_r2::test_observability__the_working_directory_after_a_successful_and_a_failed_run": probe_r2_observability,
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
