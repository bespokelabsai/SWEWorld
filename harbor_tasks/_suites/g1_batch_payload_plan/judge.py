"""g1 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote, the directories the probe's scenarios
actually ran in, and the cloned source text; writes a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged.

WHY THIS FILE NO LONGER HOLDS THE ANSWERS AS LITERALS. The split moved the
verdict out of the process that runs agent code. It left the worker AUTHORING
the values the verdict is computed from, and with a fixed fixture those values
never changed — while g1's are published in the world the agent is told to read.
A pristine tree plus one import-time `atexit` hook that rewrote
`observations.json` scored reward 1.0 on every fact. Three things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws prompts,
    row counts and limits from the seed root picked, and this file recomputes
    what the answers must be for THOSE inputs — so there is nothing to memorise
    and nothing in the corpus to copy. Row sizes are priced HERE, from the shape
    of a serialised request, which is why that shape must never appear in
    anything the worker can read.
  * **the directories are read here.** "The sweep ran", "the failed run left the
    place alone", "the bystanders were not touched" used to be booleans the
    worker computed. They are now this process opening the directory the run
    used and comparing it against the inputs it planted.
  * **the constants are read out of the source.** `PLAN_FILE_NAME`, the format
    version and the 512 cap cannot be re-drawn — they ARE the requirement — so
    they are checked against the module text as well as the run, and a tree that
    reports the right number without defining it fails.

The residual, stated plainly: a submission that IMPLEMENTS the rule inside a
forged hook still passes, because it has then done the work. What is gone is
passing by repeating values that were knowable in advance.

`test_open`/`test_r1`/`test_r2` stay the human-readable source of truth for what
each fact means; their worked example uses the old fixed fixture.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used

MODEL = "gpt-4o-mini"

# The answers that cannot be re-drawn, because they are the requirement itself.
PLAN_FILE_NAME = "batch_plan.json"
PLAN_FORMAT_VERSION = 1
MAX_BATCHES_PER_PLAN = 512
DOC_KEYS = ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests",
            "num_bytes", "batches"]
BATCH_KEYS = ["index", "start_idx", "end_idx", "num_requests", "num_bytes"]

PLANNER = ["bespokelabs/curator/request_processor/batch_payload_planner.py",
           "bespokelabs/curator/request_processor/batch_payload_planner/__init__.py"]

UNBOUNDED_BYTES = 1_000_000

SPEC: dict = {}
ARTIFACTS = pathlib.Path("/nonexistent")


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
# the oracle: what this run's inputs should produce
# ---------------------------------------------------------------------------
def api_request(idx: int, prompt: str) -> dict:
    """The provider dict curator serialises one row into.

    This is the one piece of knowledge that prices a row, and it is why it lives
    here and nowhere the worker can read: hand it over and a tree that
    implements nothing can price every row, pack them, and hash the cuts.
    """
    return {"custom_id": str(idx), "method": "POST", "url": "/v1/chat/completions",
            "body": {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}}


def prompt_of(idx: int) -> str:
    return f"{SPEC['prefix']}{idx}"


def row_size(idx: int) -> int:
    return len(json.dumps(api_request(idx, prompt_of(idx))).encode())


def row_sizes(n: int) -> list:
    return [row_size(i) for i in range(n)]


def pack(sizes, max_requests, max_bytes) -> list:
    """The greedy forward fill both limits are inclusive of, as [index, start,
    end, num_requests, num_bytes] — the shape `probe_support.tuples` records.

    A batch's byte size counts the n-1 newline separators `"\\n".join` adds.
    """
    plan, start, current = [], 0, []

    def close(end):
        plan.append([len(plan), start, end, len(current),
                     sum(current) + max(len(current) - 1, 0)])

    for idx, size in enumerate(sizes):
        nxt = current + [size]
        if current and (len(nxt) > max_requests or sum(nxt) + len(nxt) - 1 > max_bytes):
            close(idx)
            start, current = idx, [size]
        else:
            current = nxt
    if current:
        close(len(sizes))
    return plan


def fingerprint(plan) -> str:
    canonical = ";".join(f"{t[1]}-{t[2]}:{t[4]}" for t in plan)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def document(plan, limits_asdict) -> dict:
    return {
        "plan_format_version": PLAN_FORMAT_VERSION,
        "plan_id": fingerprint(plan),
        "limits": limits_asdict,
        "num_batches": len(plan),
        "num_requests": sum(t[3] for t in plan),
        "num_bytes": sum(t[4] for t in plan),
        "batches": [dict(zip(BATCH_KEYS, t)) for t in plan],
    }


def dataset_plan(n=None, max_requests=None, max_bytes=None) -> list:
    """The plan this run's main `"auto"` fixture must produce."""
    n = SPEC["rows"] if n is None else n
    return pack(row_sizes(n),
                SPEC["max_requests"] if max_requests is None else max_requests,
                SPEC["max_bytes"] if max_bytes is None else max_bytes)


# ---------------------------------------------------------------------------
# reading the directories the scenarios ran in
# ---------------------------------------------------------------------------
def adir(name: str) -> pathlib.Path:
    path = ARTIFACTS / name
    ok(path.is_dir(), f"the {name} scenario left no working directory behind")
    return path


def listing(name: str) -> list:
    return sorted(p.name for p in adir(name).iterdir())


def text_of(name: str, filename: str) -> str:
    path = adir(name) / filename
    ok(path.is_file(), f"{name}/{filename} is missing; the directory holds {listing(name)}")
    return path.read_text()


def json_of(name: str, filename: str):
    return json.loads(text_of(name, filename))


def lines_in(name: str, filename: str) -> list:
    return [json.loads(line) for line in text_of(name, filename).splitlines() if line.strip()]


def rows_in(name: str, filename: str) -> list:
    """The dataset row indices one request file holds — and a check that the
    file is THIS run's.

    Indices alone are seed-independent: rows 0..n-1 look the same in every run,
    so a directory captured from an earlier run passes an index check. The
    prompt text carries the run's token, and that is what makes a planted
    directory fail.
    """
    rows = []
    for line in lines_in(name, filename):
        idx = line["original_row_idx"]
        want = prompt_of(idx)
        got = line.get("original_row", {}).get("prompt")
        eq(got, want, f"{name}/{filename} row {idx} is not from this run")
        rows.append(idx)
    return rows


def numbered(name: str, stem: str, suffix: str) -> list:
    return sorted(p.name for p in adir(name).iterdir()
                  if p.name.startswith(stem) and p.name.endswith(suffix))


def request_files(n: int) -> list:
    return [f"requests_{i}.jsonl" for i in range(n)]


def metadata_files(n: int) -> list:
    return [f"metadata_{i}.json" for i in range(n)]


def planted_names() -> list:
    """Everything `prepopulate` put in a working directory, this run."""
    return request_files(SPEC["prepop_n"]) + metadata_files(SPEC["prepop_n"])


def require_swept(name: str):
    """The gate: this run really did sweep, so "left alone" means something.

    A tree that never implements the sweep leaves the whole stale tail in place,
    and every "nothing was removed" check below would pass on it for the wrong
    reason. The old version asked the worker for this as a boolean.
    """
    tail = f"requests_{SPEC['prepop_n'] - 1}.jsonl"
    ok(tail not in listing(name),
       f'the "auto" branch\'s sweep of stale request files is not implemented '
       f"({name} still holds {tail})")


# ---------------------------------------------------------------------------
# reading the submission's source — for the constants that cannot be re-drawn
# ---------------------------------------------------------------------------
def _module_source(candidates) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in candidates:
        path = root / rel
        if path.is_file():
            return path.read_text(errors="replace")
    raise Fail(f"none of {candidates} exists in the submission")


def _assigned(src: str, name: str):
    """The value the module assigns to a module-level constant."""
    tree = ast.parse(src)
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) and node.value is not None else [])
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                value = node.value if isinstance(node, ast.Assign) else node.value
                try:
                    return ast.literal_eval(value)
                except ValueError:
                    raise Fail(f"{name} is not a literal in the module source")
    raise Fail(f"the planner module does not define {name}")


def _field_default(src: str, classname: str, field: str):
    """A dataclass field's default, following one level of constant indirection."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == classname):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) \
                    and stmt.target.id == field and stmt.value is not None:
                if isinstance(stmt.value, ast.Name):
                    return _assigned(src, stmt.value.id)
                try:
                    return ast.literal_eval(stmt.value)
                except ValueError:
                    raise Fail(f"{classname}.{field} has no literal default")
    raise Fail(f"{classname}.{field} has no default in the module source")


# ---------------------------------------------------------------------------
# open feature — the whole stated surface, planner, files
# ---------------------------------------------------------------------------
REQUIRED_SURFACE = ["BatchLimits", "PlannedBatch", "payload_size_bytes", "payload_bytes",
                    "plan_batches", "BatchPayloadTooLargeError", "SingleRequestTooLargeError"]


def judge_open(o):
    for name in REQUIRED_SURFACE:
        has(o["surface"], name)
    ok("ValueError" in o["btle_mro"], f"BatchPayloadTooLargeError does not subclass ValueError: {o['btle_mro']}")
    ok("BatchPayloadTooLargeError" in o["srtle_mro"],
       f"SingleRequestTooLargeError does not subclass BatchPayloadTooLargeError: {o['srtle_mro']}")
    eq(o["error_fields"], [SPEC["err_num_requests"], SPEC["err_size_bytes"], SPEC["err_limit_bytes"]],
       "the error carries the three numbers it was built with")

    # --- one row, serialised the way the provider wants it ------------------
    expected_request = api_request(0, prompt_of(0))
    eq(o["row_0_request"], expected_request, "the provider request for row 0")
    eq(o["payload_size_row0"], row_size(0), "payload_size_bytes is the UTF-8 length of json.dumps")
    eq(o["measure_generic"], o["payload_size_row0"], "measure_request_payload != payload_size_bytes")
    ok(SPEC["prefix"] in json.dumps(o["generic_dump"]),
       "the generic request does not carry this run's prompt")

    size = SPEC["unit_size"]
    eq(o["payload_bytes"], [0, size, 3 * size + 2], "payload_bytes counts the n-1 separators")

    # --- greedy forward fill, both limits inclusive, exhaustive spans -------
    per = SPEC["unit_per_batch"]
    unit_cap = per * size + per - 1
    eq(o["plan_empty"], [], "zero sizes plan zero batches")
    eq(o["plan_by_bytes"], pack([size] * SPEC["unit_rows"], 1000, unit_cap),
       f"{SPEC['unit_rows']} rows of {size} bytes under a {unit_cap}-byte budget")
    eq(o["plan_by_count"], pack([size] * SPEC["count_rows"], SPEC["count_per_batch"], UNBOUNDED_BYTES),
       f"{SPEC['count_rows']} rows at {SPEC['count_per_batch']} per batch")

    raised(o["raise_single"],
           mro=["SingleRequestTooLargeError", "BatchPayloadTooLargeError", "ValueError"],
           attrs={"row_idx": 1, "size_bytes": unit_cap + 1, "limit_bytes": unit_cap, "num_requests": 1},
           msg="a row over the byte budget on its own")

    eq(o["batch_limits"], [SPEC["echo_max_requests"], SPEC["echo_max_bytes"]],
       "batch_limits mirrors the two properties")

    # --- planning the dataset, and the files it writes ----------------------
    plan = dataset_plan()
    eq(o["plan_dataset"], plan, f"the plan of {SPEC['rows']} rows at {SPEC['max_requests']}/{SPEC['max_bytes']}")
    check_cover(o["plan_dataset"], SPEC["rows"])
    eq(o["result_rel"], request_files(len(plan)), "create_request_files result")

    # read the directory rather than ask what is in it
    for t in plan:
        eq(rows_in("open_run", f"requests_{t[0]}.jsonl"), list(range(t[1], t[2])),
           f"requests_{t[0]}.jsonl holds its planned rows")
        eq(json_of("open_run", f"metadata_{t[0]}.json")["num_jobs"], t[3],
           f"metadata_{t[0]}.json num_jobs")

    eq(o["empty_batch_file_len"], 0, "create_batch_file([]) is not empty")
    eq(o["built_sizes"], [t[4] for t in plan], "built file size == planned num_bytes")

    # --- row-level generation_params ----------------------------------------
    # Cut by count, so the spans are known without pricing a row that carries
    # generation params; the byte accounting is graded on the plain rows above.
    gp_expected = pack([1] * SPEC["gp_rows"], SPEC["gp_max_requests"], UNBOUNDED_BYTES)
    eq([t[:4] for t in o["gp_plan"]], [t[:4] for t in gp_expected], "the gen-params plan's spans")
    ok(all(t[4] > 0 for t in o["gp_plan"]), f"gen-params batches carry no bytes: {o['gp_plan']}")
    for t in gp_expected:
        eq(len(rows_in("open_gp", f"requests_{t[0]}.jsonl")), t[3],
           f"gen-params requests_{t[0]}.jsonl line count")

    eq(o["wide_basenames"], request_files(SPEC["wide_rows"]),
       "one file per planned batch, numeric order")

    eq(o["empty_plan"], [], "zero rows plans zero batches")
    eq(o["empty_create_result"], [], "zero rows writes no file")
    eq(o["empty_glob_requests"], [], "no stray request files")
    eq(o["empty_glob_metadata"], [], "no stray metadata files")

    # --- the explicit-integer branch is untouched ---------------------------
    chunk = SPEC["explicit_batch_size"]
    fixed_counts = [len(range(i, min(i + chunk, SPEC["rows"]))) for i in range(0, SPEC["rows"], chunk)]
    eq(o["fixed_result_rel"], request_files(len(fixed_counts)), "explicit-integer result")
    for i, count in enumerate(fixed_counts):
        eq(len(rows_in("open_fixed", f"requests_{i}.jsonl")), count,
           f"explicit-integer requests_{i}.jsonl line count")


# ---------------------------------------------------------------------------
# r1 — the plan is written down, in a versioned sidecar
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    for name in ("PLAN_FILE_NAME", "PLAN_FORMAT_VERSION", "plan_fingerprint", "plan_document"):
        has(o["surface"], name)

    src = _module_source(PLANNER)
    eq(o["plan_file_name"], PLAN_FILE_NAME, "PLAN_FILE_NAME")
    eq(_assigned(src, "PLAN_FILE_NAME"), PLAN_FILE_NAME, "PLAN_FILE_NAME in the module source")
    eq(o["plan_format_version"], PLAN_FORMAT_VERSION, "PLAN_FORMAT_VERSION")
    eq(_assigned(src, "PLAN_FORMAT_VERSION"), PLAN_FORMAT_VERSION, "PLAN_FORMAT_VERSION in the module source")

    # the digest is over the cuts and the sizes; index and num_requests are not in it
    eq(o["fp_same"], fingerprint(o["fp_spans"]), "plan_fingerprint of a known plan")
    eq(o["fp_same"], o["fp_relabelled"], "plan_fingerprint changed when only index/num_requests changed")
    ok(o["fp_same"] != o["fp_diff_size"], "plan_fingerprint ignores the batch sizes")
    ok(o["fp_same"] != o["fp_diff_cut"], "plan_fingerprint ignores where the cuts fall")

    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    eq(o["batches_asdict"], [dict(zip(BATCH_KEYS, t)) for t in plan], "PlannedBatch as a dict")

    expected = document(plan, o["limits_asdict"])
    doc = json_of("r1_rule", PLAN_FILE_NAME)
    eq(list(doc), DOC_KEYS, "sidecar envelope keys")
    eq(doc, expected, "the sidecar the run left behind")
    eq(list(doc["batches"][0]), BATCH_KEYS, "a batch entry's keys")
    eq(o["plan_document_out"], doc, "plan_document(plan, limits) != the document on disk")


def judge_r1_scope(o):
    # Written at all, and describing THIS run — an empty plan's document is the
    # same every run, and a fact whose every check is seed-independent can be
    # answered by planting the directories it reads. Measured: a forgery that
    # implemented nothing passed this one fact and no other.
    plan = dataset_plan()
    ordered_doc = json_of("r1_scope_ordered", PLAN_FILE_NAME)
    eq(ordered_doc.get("num_batches"), len(plan), 'the "auto" branch wrote no plan for this run')
    eq(ordered_doc.get("batches"), [dict(zip(BATCH_KEYS, t)) for t in plan],
       "the sidecar does not describe the run that wrote it")
    eq(ordered_doc.get("plan_id"), fingerprint(plan), "the sidecar's plan_id")

    # written before any request file of its own run
    if o["ordered_reused_acreate"]:
        ok(o["ordered_plan_exists_on_first_call"] is True,
           "the sidecar was written after the request files, not before them")

    # a 0-batch plan is still recorded
    eq(o["empty_create_result"], [], "empty auto run returns []")
    empty_doc = json_of("r1_scope_empty", PLAN_FILE_NAME)
    eq([empty_doc["num_batches"], empty_doc["num_requests"], empty_doc["num_bytes"], empty_doc["batches"]],
       [0, 0, 0, []], "a 0-batch plan is still recorded")
    eq(empty_doc["plan_id"], fingerprint([]), "the empty plan's plan_id")

    # the explicit-integer branch: no sidecar, and it really did run here
    ok(PLAN_FILE_NAME not in listing("r1_scope_fixed"), "the explicit-integer branch wrote a plan sidecar")
    chunk = SPEC["explicit_batch_size"]
    eq(rows_in("r1_scope_fixed", "requests_0.jsonl"), list(range(chunk)),
       "the explicit-integer branch did not write this run's rows")
    ok(PLAN_FILE_NAME not in listing("r1_scope_none"), "the `dataset is None` path wrote a plan sidecar")


def judge_r1_exclusions(o):
    ok((adir("r1_excl") / PLAN_FILE_NAME).is_file(),
       "the batch_plan.json sidecar is not implemented, so the constraint cannot be credited")  # require_feature
    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    for t in plan:
        meta = json_of("r1_excl", f"metadata_{t[0]}.json")
        eq(sorted(meta), ["num_jobs"], "metadata carries plan fields it should not")
        eq(meta["num_jobs"], t[3], "metadata num_jobs == num_requests")


def judge_r1_failure_behavior(o):
    has(o["surface"], "BatchPlanTooFragmentedError")
    ok("ValueError" in o["bptfe_mro"], f"BatchPlanTooFragmentedError does not subclass ValueError: {o['bptfe_mro']}")
    ok("BatchPayloadTooLargeError" not in o["bptfe_mro"], "a fragmented plan is not an oversized payload")

    # The cap is the one input that is also an answer, so it is checked twice:
    # the limit the implementation actually applied, and the number its source
    # defines. Reporting 512 without defining it is not enough.
    limit = MAX_BATCHES_PER_PLAN
    eq(o["default_limit"], limit, "BatchLimits.max_batches_per_plan default")
    eq(_field_default(_module_source(PLANNER), "BatchLimits", "max_batches_per_plan"), limit,
       "max_batches_per_plan's default in the module source")
    eq(o["len_at_limit"], limit, f"{limit} batches is the boundary and it is admissible")
    raised(o["raise_over_limit"], mro=["BatchPlanTooFragmentedError"],
           attrs={"num_batches": limit + 1, "limit": limit}, msg=f"{limit + 1} batches")

    raised(o["raise_explicit_cap"], mro=["BatchPlanTooFragmentedError"],
           attrs={"num_batches": SPEC["cap_rows"], "limit": SPEC["cap_max_batches"]},
           msg="explicit max_batches_per_plan")
    raised(o["raise_oversize_first"], mro=["SingleRequestTooLargeError"],
           attrs={"row_idx": SPEC["oversize_rows"]}, msg="per-row scan wins")


def judge_r1_observability(o):
    eq(o["fp_empty"], fingerprint([]), "plan_fingerprint([])")

    wide = pack(row_sizes(SPEC["wide_rows"]), 1, UNBOUNDED_BYTES)
    eq(o["wide_plan"], wide, "one row per batch")
    eq(o["fp_wide"], fingerprint(wide), "plan_fingerprint of the one-per-batch plan")

    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    eq(o["fp_plan"], fingerprint(plan), "plan_fingerprint of that plan")

    # the implementation's own limits are substituted, so the fan-out cap is
    # graded once, under failure_behavior, and not a second time here
    limits = o["limits_asdict"]
    eq(limits.get("max_requests_per_batch"), SPEC["max_requests"], "doc limits max_requests_per_batch")
    eq(limits.get("max_bytes_per_batch"), SPEC["max_bytes"], "doc limits max_bytes_per_batch")

    doc = json_of("r1_obs", PLAN_FILE_NAME)
    eq(doc, document(plan, limits), "the document the run leaves behind")
    raw = text_of("r1_obs", PLAN_FILE_NAME)
    ok(raw.endswith("]\n}\n"), f"the sidecar is not indented JSON with a trailing newline: {raw[-20:]!r}")


# ---------------------------------------------------------------------------
# r2 — the "auto" branch sweeps its stale numbering
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    n = len(plan)
    ok(n < SPEC["prepop_n"], f"the fixture must plan fewer batches ({n}) than it pre-populated")

    eq(numbered("r2_rule", "requests_", ".jsonl"), request_files(n), "stale request files survived the run")
    eq(numbered("r2_rule", "metadata_", ".json"), metadata_files(n), "stale metadata files survived the run")
    eq(rows_in("r2_rule", "requests_0.jsonl"), list(range(plan[0][1], plan[0][2])),
       "requests_0.jsonl holds the new run's rows")


def judge_r2_scope(o):
    require_swept("r2_scope_sweep")

    # the explicit-integer branch owns its own numbering and removes nothing
    chunk = SPEC["explicit_batch_size"]
    for name, scenario in (("explicit-integer", "r2_scope_fixed"), ("`dataset is None`", "r2_scope_none")):
        here = listing(scenario)
        untouched = range(chunk + 1, SPEC["prepop_n"]) if scenario == "r2_scope_fixed" \
            else range(1, SPEC["prepop_n"])
        for i in untouched:
            ok(f"requests_{i}.jsonl" in here, f"the {name} branch removed a stale request file")
            ok(f"metadata_{i}.json" in here, f"the {name} branch removed a stale metadata file")
            eq(text_of(scenario, f"requests_{i}.jsonl"), SPEC["stale_request"],
               f"the {name} branch rewrote requests_{i}.jsonl")
            eq(text_of(scenario, f"metadata_{i}.json"), SPEC["stale_metadata"],
               f"the {name} branch rewrote metadata_{i}.json")


def judge_r2_exclusions(o):
    require_swept("r2_excl")
    for name, body in SPEC["keepers"].items():
        ok(name in listing("r2_excl"), f"the sweep removed {name}, which is not a request or metadata file")
        eq(text_of("r2_excl", name), body, f"the sweep rewrote {name}")


def judge_r2_failure_behavior(o):
    require_swept("r2_fail_sweep")

    raised(o["raise_plan"], mro=["SingleRequestTooLargeError"], attrs={"row_idx": 1},
           msg="planning raises on the oversize row")
    raised(o["raise_create"], mro=["SingleRequestTooLargeError"], msg="create_request_files raises")

    # The whole fact: the directory is exactly what was planted in it. Every
    # name and every byte comes from this run's fixture, so a directory prepared
    # in advance cannot stand in for one a failed run left alone.
    planted = dict.fromkeys(planted_names(), None)
    expected = set(planted) | set(SPEC["keepers"]) | {o["plan_file_name"]}
    eq(set(listing("r2_fail")), expected, "a planning failure changed the working directory")
    for i in range(SPEC["prepop_n"]):
        eq(text_of("r2_fail", f"requests_{i}.jsonl"), SPEC["stale_request"], f"requests_{i}.jsonl was rewritten")
        eq(text_of("r2_fail", f"metadata_{i}.json"), SPEC["stale_metadata"], f"metadata_{i}.json was rewritten")
    for name, body in SPEC["keepers"].items():
        eq(text_of("r2_fail", name), body, f"{name} was rewritten")
    eq(text_of("r2_fail", o["plan_file_name"]), SPEC["stale_sidecar"], "the stale sidecar was rewritten")


def judge_r2_observability(o):
    # the successful run: its own numbering, plus the bystanders, and nothing else
    plan = dataset_plan()
    expected_good = set(request_files(len(plan))) | set(metadata_files(len(plan))) | set(SPEC["keepers"])
    eq(set(listing("r2_obs_good")) - {PLAN_FILE_NAME, o["plan_file_name"]}, expected_good,
       "the working directory after a successful run")
    for name, body in SPEC["keepers"].items():
        eq(text_of("r2_obs_good", name), body, f"the successful run rewrote {name}")

    # the failed run: exactly what it found
    raised(o["bad_plan_raises"], mro=["SingleRequestTooLargeError"], msg="planning raises")
    raised(o["bad_create_raises"], mro=["SingleRequestTooLargeError"], msg="create_request_files raises")
    expected_bad = set(planted_names()) | set(SPEC["keepers"]) | {o["plan_file_name"]}
    eq(set(listing("r2_obs_bad")), expected_bad, "the working directory after a failed run")
    eq(text_of("r2_obs_bad", o["plan_file_name"]), SPEC["stale_sidecar"], "the stale sidecar was rewritten")
    eq(text_of("r2_obs_bad", f"requests_{SPEC['prepop_n'] - 1}.jsonl"), SPEC["stale_request"],
       "a stale request file was rewritten")


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


def main(obs_path: str, out_path: str, seed: str, artifacts: str) -> int:
    global SPEC, ARTIFACTS
    SPEC = fixture_spec.derive(seed)
    ARTIFACTS = pathlib.Path(artifacts)

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
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
