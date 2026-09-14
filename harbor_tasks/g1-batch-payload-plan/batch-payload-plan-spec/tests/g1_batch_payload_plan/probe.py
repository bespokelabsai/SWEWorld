"""g1 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks /tests to root), turns
those values into the verdict.

WHAT THE SPLIT ALONE DID NOT BUY, and this file is the half that pays for it.
Separating the processes stopped the worker rewriting the verdict. It did not
stop the worker INVENTING the values the verdict is computed from, and with a
fixed fixture those values are identical every run — while g1's are also written
down in the world the agent is told to read (`batch_plan.json`, the 512 cap,
"sha256 … first twelve hex", `{"num_jobs": n}`). Pristine `main` plus one
import-time `atexit` hook that overwrote this file's output scored reward 1.0.

So two things changed here:

  * **the inputs are re-drawn every run** from the seed root chose
    (`fixture_spec.derive`), so nothing about this run is knowable in advance;
  * **nothing below is a verdict, and nothing below is a boolean.** The previous
    version reported `swept_proof`, `unchanged`, `keepers_intact` and eight
    `doc_*_eq` flags — about thirty assertions that came down to a word this
    process chose. `true` passed them without knowing a single answer. The
    scenarios now run in a directory the judge reads for itself, and what it
    finds there is the fact.

The probe still cannot be trusted and is not meant to be: it prices nothing, and
it is handed no way to price anything. Row sizes come from the shape of a
serialised request, and that shape lives only in the judge — see
`fixture_spec`'s header for why that line matters.

Two g1-specific reproduction rules:

  * the probe is not under pytest, so every scenario gets its own directory
    under the run's artifacts root (`probe_support.make_tmp_dir(name)`) in place
    of the `tmp_path` fixture, named so the judge can find it;
  * for the byte-exact and file-listing facts the probe records the RAW values
    (the dict a request serialises to, the plan's tuples, a document as written)
    and lets the judge assert the exact count/spelling — it never carries a byte
    count, a plan_id hex, the sidecar's JSON, or the fan-out cap here.
"""
from __future__ import annotations

import dataclasses
import glob
import json
import os
import sys
import traceback

# Bound BEFORE the submission is imported, and called instead of returning from
# main(). Interpreter shutdown runs `atexit` hooks the submission registered at
# import — which is how the observations file was overwritten from a tree that
# implemented nothing. Leaving through `os._exit` never reaches them. This is a
# lock on one door, not the fix: a hook can patch `open` and edit the file as it
# is written. What makes forged values worthless is that they are not knowable.
_EXIT = os._exit

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

import fixture_spec  # noqa: E402 - the run's inputs; stdlib only, no answers

# probe_support owns the curator imports and the answer-free helpers; reuse them
# so a probe calls curator exactly as the test does. Importing it runs the
# submission's `import bespokelabs.curator` — this process's whole purpose, and
# why it is disposable. The worker never imports test_open/test_r*, whose source
# carries the expected answer literals.
import probe_support as S  # noqa: E402
from harness import read_field, surface  # noqa: E402

# Filled in by main() from argv before any probe runs.
SPEC: dict = {}

# A byte limit far above any row these fixtures build, for the scenarios whose
# cuts are meant to fall on the request count rather than on size.
UNBOUNDED_BYTES = 1_000_000


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
    directory without seeing this run's own artifacts path."""
    return [os.path.relpath(p, str(base)) for p in paths]


def jsonable(value):
    """Round-trip through JSON the way the observations file will anyway."""
    return json.loads(json.dumps(value, default=str))


def dataset(n=None):
    """This run's prompt dataset: `f"{prefix}{i}"`, prefix drawn from the seed."""
    return S.prompt_dataset(SPEC["rows"] if n is None else n, prefix=SPEC["prefix"])


def limits(module, *, max_requests=None, max_bytes=None, **extra):
    return S.limits_of(module,
                       SPEC["max_requests"] if max_requests is None else max_requests,
                       SPEC["max_bytes"] if max_bytes is None else max_bytes,
                       **extra)


def sidecar_name(module):
    """The name the module writes its plan under, or None if it exports none.

    NOT a default to `"batch_plan.json"`: that string is r1.rule's answer and
    this file lives in the worker's jail. A fact that only needs to FIND the
    file takes None and grades what it can; only r1.rule grades the name.
    """
    return getattr(module, "PLAN_FILE_NAME", None)


def stale_kwargs() -> dict:
    return {"stale_request": SPEC["stale_request"], "stale_metadata": SPEC["stale_metadata"]}


# ===========================================================================
# open feature — the whole stated surface, planner, files (one fact)
# ===========================================================================
def probe_open() -> dict:
    module = S.planner()
    o: dict = {}
    size, per = SPEC["unit_size"], SPEC["unit_per_batch"]
    # exactly `per` rows of `size` fit, counting the n-1 newline separators
    unit_cap = per * size + per - 1

    # --- the module's surface, and the two exception hierarchies ------------
    o["surface"] = surface(module)
    o["btle_mro"] = [c.__name__ for c in module.BatchPayloadTooLargeError.__mro__]
    o["srtle_mro"] = [c.__name__ for c in module.SingleRequestTooLargeError.__mro__]
    error = module.BatchPayloadTooLargeError(num_requests=SPEC["err_num_requests"],
                                             size_bytes=SPEC["err_size_bytes"],
                                             limit_bytes=SPEC["err_limit_bytes"])
    o["error_fields"] = [read_field(error, "num_requests"), read_field(error, "size_bytes"),
                         read_field(error, "limit_bytes")]

    # --- serialization: stock json.dumps, then UTF-8 ------------------------
    run_dir = S.make_tmp_dir("open_run")
    processor = S.make_processor(run_dir)
    first_prompt = f"{SPEC['prefix']}0"
    row_0_request = S.api_requests_for(processor, S.prompt_dataset(1, prefix=SPEC["prefix"]), 0, 1)[0]
    o["row_0_request"] = jsonable(row_0_request)
    o["payload_size_row0"] = module.payload_size_bytes(row_0_request)
    generic = processor.prompt_formatter.create_generic_request({"prompt": first_prompt}, 0, False)
    o["generic_dump"] = jsonable(generic.model_dump())
    o["measure_generic"] = processor.measure_request_payload(generic)

    # --- file accounting: the n-1 separators of "\n".join(...) --------------
    o["payload_bytes"] = [module.payload_bytes([]), module.payload_bytes([size]),
                          module.payload_bytes([size] * 3)]

    # --- greedy forward fill, both limits inclusive, exhaustive spans -------
    o["plan_empty"] = S.tuples(module.plan_batches([], limits(module, max_requests=50_000, max_bytes=200 * 1024 * 1024)))
    # cut by bytes: the request count cannot bind
    o["plan_by_bytes"] = S.tuples(module.plan_batches([size] * SPEC["unit_rows"],
                                                      limits(module, max_requests=1000, max_bytes=unit_cap)))
    # cut by count: the byte budget cannot bind
    o["plan_by_count"] = S.tuples(module.plan_batches([size] * SPEC["count_rows"],
                                                      limits(module, max_requests=SPEC["count_per_batch"],
                                                             max_bytes=UNBOUNDED_BYTES)))

    # --- one row bigger than the byte budget raises, it does not stall ------
    o["raise_single"] = raises(module.plan_batches, [size, unit_cap + 1, size],
                               limits(module, max_requests=1000, max_bytes=unit_cap),
                               attrs=("row_idx", "size_bytes", "limit_bytes", "num_requests"))

    # --- batch_limits mirrors the processor's own two properties ------------
    with S.patched_limits(max_requests=SPEC["echo_max_requests"], max_bytes=SPEC["echo_max_bytes"]):
        got = processor.batch_limits
        o["batch_limits"] = [read_field(got, "max_requests_per_batch"), read_field(got, "max_bytes_per_batch")]

    # --- planning a dataset, then writing one file per planned batch --------
    rows = dataset()
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        plan = processor.plan_request_batches(rows)
        o["plan_dataset"] = S.tuples(plan)
        result = processor.create_request_files(rows)
    o["result_rel"] = relpaths(result, run_dir)

    # --- the planned size is the size of the file that is actually built ----
    o["empty_batch_file_len"] = len(processor.create_batch_file([]))
    built_sizes = []
    for planned in plan:
        requests = S.api_requests_for(processor, rows, read_field(planned, "start_idx"), read_field(planned, "end_idx"))
        with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
            built = processor.create_batch_file(requests)
        built_sizes.append(len(built))
    o["built_sizes"] = built_sizes

    # --- row-level generation_params are part of the measured payload ------
    gp_dir = S.make_tmp_dir("open_gp")
    gp_processor = S.make_processor(gp_dir)
    gp_dataset = S.genparams_dataset(SPEC["gp_rows"], prefix=SPEC["prefix"],
                                     params=json.dumps({"temperature": SPEC["gp_temperature"]}))
    with S.patched_limits(max_requests=SPEC["gp_max_requests"], max_bytes=UNBOUNDED_BYTES):
        gp_plan = gp_processor.plan_request_batches(gp_dataset)
        o["gp_plan"] = S.tuples(gp_plan)
        gp_processor.create_request_files(gp_dataset)

    # --- every file the plan asked for comes back, in numeric order ---------
    wide_dir = S.make_tmp_dir("open_wide")
    wide = S.make_processor(wide_dir)
    with S.patched_limits(max_requests=1):
        wide_result = wide.create_request_files(dataset(SPEC["wide_rows"]))
    o["wide_basenames"] = S.basenames(wide_result)

    # --- zero rows plans zero batches and writes no request file -----------
    from datasets import Dataset
    empty_dir = S.make_tmp_dir("open_empty")
    empty = S.make_processor(empty_dir)
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        o["empty_plan"] = S.tuples(empty.plan_request_batches(Dataset.from_dict({"prompt": []})))
        o["empty_create_result"] = empty.create_request_files(Dataset.from_dict({"prompt": []}))
    o["empty_glob_requests"] = glob.glob(os.path.join(empty_dir, "requests_*.jsonl"))
    o["empty_glob_metadata"] = glob.glob(os.path.join(empty_dir, "metadata_*.json"))

    # --- the explicit-integer branch is untouched ---------------------------
    fixed_dir = S.make_tmp_dir("open_fixed")
    fixed = S.make_processor(fixed_dir, batch_size=SPEC["explicit_batch_size"])
    fixed_result = fixed.create_request_files(rows)
    o["fixed_result_rel"] = relpaths(fixed_result, fixed_dir)
    return o


# ===========================================================================
# r1 — the plan is written down, in a versioned sidecar
# ===========================================================================
def probe_r1_rule() -> dict:
    module = S.planner()
    o: dict = {}

    o["surface"] = surface(module)
    # r1.rule's own fact, and still reported defensively: the judge fails it on
    # `None != "batch_plan.json"`, which says what is wrong, where a probe error
    # would have thrown away the digests and the document below with it.
    o["plan_file_name"] = sidecar_name(module)
    o["plan_format_version"] = getattr(module, "PLAN_FORMAT_VERSION", None)

    # The fingerprint is taken over where the cuts fall and how big each batch
    # is: index/num_requests do not enter it. The judge holds the digest scheme
    # and recomputes all four of these from the spans below, so a reported hex
    # has to be the hex of the plan it claims to be.
    # bound here, not at the top: a module without PlannedBatch should fail this
    # fact on the surface it just reported, not before it reported anything
    PB = module.PlannedBatch
    a, b = SPEC["unit_size"], SPEC["unit_size"] + 1
    o["fp_spans"] = [[0, 0, 2, 2, a], [1, 2, 4, 2, a]]
    o["fp_same"] = module.plan_fingerprint([PB(0, 0, 2, 2, a), PB(1, 2, 4, 2, a)])
    o["fp_relabelled"] = module.plan_fingerprint([PB(5, 0, 2, 99, a), PB(9, 2, 4, 77, a)])
    o["fp_diff_size"] = module.plan_fingerprint([PB(0, 0, 2, 2, a), PB(1, 2, 4, 2, b)])
    o["fp_diff_cut"] = module.plan_fingerprint([PB(0, 0, 3, 3, a), PB(1, 3, 4, 1, a)])

    processor, plan, working_dir, lim = S.auto_run(dataset(), max_requests=SPEC["max_requests"],
                                                   max_bytes=SPEC["max_bytes"], name="r1_rule")
    o["plan"] = S.tuples(plan)
    # The document as the module builds it, and the document as it landed on
    # disk: the judge computes what both should be and compares all three. The
    # worker used to report `doc == plan_document(...)` as one boolean.
    o["plan_document_out"] = jsonable(module.plan_document(plan, lim))
    o["limits_asdict"] = jsonable(dataclasses.asdict(lim)) if lim is not None else None
    o["batches_asdict"] = jsonable([dataclasses.asdict(p) for p in plan])
    return o


def probe_r1_observability() -> dict:
    """The digests, and the document a real run leaves behind.

    Its own directory rather than r1_rule's: two facts graded off one directory
    would have the second run's files sitting on top of the first's.
    """
    module = S.planner()
    o: dict = {}
    o["fp_empty"] = module.plan_fingerprint([])

    # one request per batch, so the cuts are known without pricing a row
    wide_dir = S.make_tmp_dir("r1_obs_wide")
    wide = S.make_processor(wide_dir)
    with S.patched_limits(max_requests=1):
        wide_plan = wide.plan_request_batches(dataset(SPEC["wide_rows"]))
    o["wide_plan"] = S.tuples(wide_plan)
    o["fp_wide"] = module.plan_fingerprint(wide_plan)

    _processor, plan, _working_dir, lim = S.auto_run(dataset(), max_requests=SPEC["max_requests"],
                                                     max_bytes=SPEC["max_bytes"], name="r1_obs")
    o["plan"] = S.tuples(plan)
    o["fp_plan"] = module.plan_fingerprint(plan)
    # carried so the judge substitutes the implementation's own limits rather
    # than grading the fan-out cap twice; it still checks the two limits it set
    o["limits_asdict"] = jsonable(dataclasses.asdict(lim)) if lim is not None else None
    return o


def probe_r1_scope() -> dict:
    S.planner()
    o: dict = {}

    # --- written before any request file of its own run --------------------
    # Ordering is the one thing that cannot be read off the finished directory,
    # so it stays an in-process observation; everything else in this fact is the
    # judge's own reading of the four directories below.
    #
    # What is recorded is the whole directory, not "is <name> there yet". Asking
    # the module for PLAN_FILE_NAME to build that name made r1.scope die of an
    # AttributeError whenever a submission hardcoded its filename and exported no
    # constant — a fact lost to a detail r1.rule owns, before this node gathered
    # any evidence at all. The judge holds the spelling; the worker holds a list.
    working_dir = S.make_tmp_dir("r1_scope_ordered")
    processor = S.make_processor(working_dir)
    seen = {}
    original = getattr(processor, "acreate_request_file", None)

    if original is not None:
        async def recording(*args, **kwargs):
            seen.setdefault("listing", sorted(os.listdir(working_dir)))
            return await original(*args, **kwargs)

        processor.acreate_request_file = recording
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        processor.create_request_files(dataset())
    o["ordered_reused_acreate"] = bool(seen)
    o["ordered_listing_at_first_call"] = seen.get("listing")

    # --- a 0-batch plan is still recorded ----------------------------------
    from datasets import Dataset
    empty_dir = S.make_tmp_dir("r1_scope_empty")
    empty = S.make_processor(empty_dir)
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        o["empty_create_result"] = empty.create_request_files(Dataset.from_dict({"prompt": []}))

    # --- the explicit-integer branch never writes it -----------------------
    fixed_dir = S.make_tmp_dir("r1_scope_fixed")
    fixed = S.make_processor(fixed_dir, batch_size=SPEC["explicit_batch_size"])
    fixed.create_request_files(dataset(SPEC["explicit_batch_size"] + 1))

    # --- and neither does the `dataset is None` path -----------------------
    none_dir = S.make_tmp_dir("r1_scope_none")
    none_processor = S.make_processor(none_dir)
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        none_processor.create_request_files(None)
    return o


def probe_r1_exclusions() -> dict:
    S.planner()
    o: dict = {}
    _processor, plan, _working_dir, _lim = S.auto_run(dataset(), max_requests=SPEC["max_requests"],
                                                      max_bytes=SPEC["max_bytes"], name="r1_excl")
    # The metadata files themselves are the fact, and the judge reads them out
    # of the directory; the plan is here so it can say which files to expect.
    o["plan"] = S.tuples(plan)
    return o


def probe_r1_failure_behavior() -> dict:
    module = S.planner()
    o: dict = {}
    size = SPEC["unit_size"]
    o["surface"] = surface(module)
    o["bptfe_mro"] = [c.__name__ for c in module.BatchPlanTooFragmentedError.__mro__]

    one_per_batch = module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=UNBOUNDED_BYTES)
    # The cap is the requirement, so it cannot be re-drawn per run — and it must
    # not be written down in this process either. The probe reads the default
    # off the implementation and reports it; the judge checks that number
    # against its own copy AND against the module source, so a tree that merely
    # claims 512 without defining it fails.
    # `default=None` so a BatchLimits without the field fails this fact with the
    # judge's own message about the default, instead of dying as a probe error
    default_limit = read_field(one_per_batch, "max_batches_per_plan", default=None)
    o["default_limit"] = default_limit
    if isinstance(default_limit, int):
        o["len_at_limit"] = len(module.plan_batches([size] * default_limit, one_per_batch))
        o["raise_over_limit"] = raises(module.plan_batches, [size] * (default_limit + 1), one_per_batch,
                                       attrs=("num_batches", "limit"))

    o["cap_rows"] = SPEC["cap_rows"]
    o["cap_max_batches"] = SPEC["cap_max_batches"]
    o["raise_explicit_cap"] = raises(
        module.plan_batches, [size] * SPEC["cap_rows"],
        module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=UNBOUNDED_BYTES,
                           max_batches_per_plan=SPEC["cap_max_batches"]),
        attrs=("num_batches", "limit"),
    )

    # the per-row oversize scan runs first: a dataset tripping both raises for the row
    oversize_at = SPEC["oversize_rows"]
    o["oversize_at"] = oversize_at
    o["raise_oversize_first"] = raises(
        module.plan_batches, [size] * oversize_at + [SPEC["oversize_len"]],
        module.BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=SPEC["oversize_len"] - 1),
        attrs=("row_idx",))
    return o


# ===========================================================================
# r2 — the "auto" branch sweeps its stale numbering
# ===========================================================================
# The stale bytes and the bystander files are INPUTS, drawn per run in
# fixture_spec and planted below. They used to be literals here, which made the
# "was the directory left alone?" facts answerable by repeating them back.
def probe_r2_rule() -> dict:
    S.planner()  # the feature under test cannot exist without the planner module
    o: dict = {}
    working_dir = S.make_tmp_dir("r2_rule")
    processor = S.make_processor(S.prepopulate(working_dir, n=SPEC["prepop_n"], **stale_kwargs()))
    rows = dataset()

    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        plan = processor.plan_request_batches(rows)
        processor.create_request_files(rows)
    o["plan"] = S.tuples(plan)
    return o


def probe_r2_scope() -> dict:
    S.planner()
    o: dict = {}

    # --- the sweep is implemented at all (the gate the judge reads) ---------
    S.sweep_run(S.make_tmp_dir("r2_scope_sweep"), dataset(), n=SPEC["prepop_n"],
                max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"], **stale_kwargs())

    # --- explicit-integer batch_size: incomplete_files still owns the numbering
    fixed_dir = S.prepopulate(S.make_tmp_dir("r2_scope_fixed"), n=SPEC["prepop_n"], **stale_kwargs())
    fixed = S.make_processor(fixed_dir, batch_size=SPEC["explicit_batch_size"])
    fixed.create_request_files(dataset(SPEC["explicit_batch_size"] + 1))

    # --- the `dataset is None` path writes requests_0.jsonl, nothing else moves
    none_dir = S.prepopulate(S.make_tmp_dir("r2_scope_none"), n=SPEC["prepop_n"], **stale_kwargs())
    none_processor = S.make_processor(none_dir)
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        none_processor.create_request_files(None)
    return o


def probe_r2_exclusions() -> dict:
    S.planner()
    o: dict = {}
    working_dir = S.prepopulate(S.make_tmp_dir("r2_excl"), n=SPEC["prepop_n"],
                                extra=SPEC["keepers"], **stale_kwargs())
    processor = S.make_processor(working_dir)
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        processor.create_request_files(dataset())
    # No observation: the whole fact is what the directory holds afterwards, and
    # the judge reads it. This used to be `keepers_intact`, five booleans.
    return o


def probe_r2_failure_behavior() -> dict:
    module = S.planner()
    o: dict = {}
    # r1's fact, read defensively and never required: `test_r2` promises "an
    # implementation that sweeps without writing a sidecar passes r2 in full",
    # and `module.PLAN_FILE_NAME` here broke that promise with an AttributeError
    # for anything that hardcoded the name. None means "no sidecar to plant",
    # and the judge then grades this fact on the stale files alone.
    o["plan_file_name"] = sidecar_name(module)

    # the gate: the sweep exists, so "nothing was removed" means something
    S.sweep_run(S.make_tmp_dir("r2_fail_sweep"), dataset(), n=SPEC["prepop_n"],
                max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"], **stale_kwargs())

    extra = dict(SPEC["keepers"])
    if o["plan_file_name"]:
        extra[o["plan_file_name"]] = SPEC["stale_sidecar"]
    working_dir = S.prepopulate(S.make_tmp_dir("r2_fail"), n=SPEC["prepop_n"],
                                extra=extra, **stale_kwargs())
    processor = S.make_processor(working_dir)
    rows = S.big_dataset(rows=SPEC["oversize_rows"], big_at=1,
                         big_len=SPEC["oversize_len"], prefix=SPEC["prefix"])

    def plan_it():
        with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
            processor.plan_request_batches(rows)

    def create_it():
        with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
            processor.create_request_files(rows)

    o["raise_plan"] = raises(plan_it, attrs=("row_idx",))
    o["raise_create"] = raises(create_it)
    # `unchanged` was a boolean here. The judge now diffs the directory against
    # the inputs fixture_spec planted, which the worker cannot restate into a pass.
    return o


def probe_r2_observability() -> dict:
    module = S.planner()
    o: dict = {}
    o["plan_file_name"] = sidecar_name(module)  # r1's fact; see probe_r2_failure_behavior

    good_dir = S.prepopulate(S.make_tmp_dir("r2_obs_good"), n=SPEC["prepop_n"],
                             extra=SPEC["keepers"], **stale_kwargs())
    good = S.make_processor(good_dir)
    with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
        good.create_request_files(dataset())

    extra = dict(SPEC["keepers"])
    if o["plan_file_name"]:
        extra[o["plan_file_name"]] = SPEC["stale_sidecar"]
    bad_dir = S.prepopulate(S.make_tmp_dir("r2_obs_bad"), n=SPEC["prepop_n"],
                            extra=extra, **stale_kwargs())
    bad = S.make_processor(bad_dir)
    rows = S.big_dataset(rows=SPEC["oversize_rows"], big_at=1,
                         big_len=SPEC["oversize_len"], prefix=SPEC["prefix"])

    def plan_it():
        with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
            bad.plan_request_batches(rows)

    def create_it():
        with S.patched_limits(max_requests=SPEC["max_requests"], max_bytes=SPEC["max_bytes"]):
            bad.create_request_files(rows)

    o["bad_plan_raises"] = raises(plan_it)
    o["bad_create_raises"] = raises(create_it)
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


def main(out_path: str, seed: str, artifacts: str) -> int:
    global SPEC
    SPEC = fixture_spec.derive(seed)
    S.set_artifacts_root(artifacts)

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
    code = main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.stdout.flush()
    sys.stderr.flush()
    _EXIT(code)
