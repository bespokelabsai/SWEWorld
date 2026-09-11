"""g4 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and,
for the no-randomness fact, the submission's own source text, applies the
assertions the g4 suite has always made, and writes a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks this file to
root, so the worker cannot read the numbers below to forge an observation that
matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files
stay the human-readable source of truth and the fact<->test bijection. The
twelve-component key list, the four-key backend allowlist and the
identity/non-identity split, the `_get_function_hash(None)` digest, the migration
column set and the store_metadata rows all live here and only here.

The run hashes and the identity digest are HIGH-ENTROPY. The source tests never
pinned a literal for them — they check shape (`v3-<16 hex>`, `v3-nocache-...`,
length 27) and self-consistency (same inputs → same hash, a changed input → a
different one) — so this judge reproduces exactly those relational checks. Where
a run leaves a directory keyed by its hash, the check is still on the id inside
the stamp, not the hash. The AST no-randomness fact is checked against the file
on disk under SUBMISSION_SRC (parsing text executes nothing), a more faithful
check of the graded artifact than trusting the worker to report its own source.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ne(got, other, msg=""):
    if got == other:
        raise Fail(f"{msg}: {got!r} == {other!r} (should differ)")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised(info, *, mro=None, msg="", **attrs):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    for name, value in attrs.items():
        eq(info.get(name), value, f"{msg}: {name}")


# ---------------------------------------------------------------------------
# The answers
# ---------------------------------------------------------------------------
TWELVE = [
    "backend", "backend_params", "batch_mode", "dataset_hash", "generation_params",
    "model_name", "parse_func_hash", "prompt_func_hash", "response_format",
    "return_completions_object", "run_id", "system_prompt",
]
IDENTITY_BACKEND_KEYS = {"azure_deployment", "base_url", "batch_size", "completion_window"}
FN_HASH_NONE = "ef46db3751d8e999"

SURFACE_NAMES = ("RunIdentity", "RunStamp", "RunDirectoryCheck", "RunIdentityError",
                 "RunIdentityMismatch", "CachedResponseMismatch", "compute_run_identity",
                 "write_run_stamp", "read_run_stamp", "reconcile_run_directory", "_get_function_hash")

DATACLASS_FIELDS = {
    "RunIdentity": ["run_hash", "digest", "identity_version", "cache_enabled", "components"],
    "RunStamp": ["identity_version", "run_hash", "digest", "components", "created_at", "updated_at"],
    "RunDirectoryCheck": ["status", "stamp", "previous_version"],
}

NOW = "2025-01-02T03:04:05"
LATER = "2025-01-02T04:00:00"


def _is_hex16(digest) -> bool:
    return (isinstance(digest, str) and len(digest) == 16
            and digest == digest.lower() and all(c in "0123456789abcdef" for c in digest))


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["ri_version"], 3, "RUN_IDENTITY_VERSION")
    eq(o["ri_filename"], "run_identity.json", "RUN_IDENTITY_FILENAME")
    for name in SURFACE_NAMES:
        ok(o["has_names"].get(name), f"run_identity exports no {name!r}; it has {o.get('surface')}")

    eq(o["exc_subclass"], [True, True, True], "exception hierarchy")
    eq(o["mismatch_attrs"], ["cache-dir-c", "v3-a", "v3-b", ["model_name"]], "RunIdentityMismatch attrs")
    eq(o["stale_attrs"], ["cache-dir-c", "fingerprint", "aaa", "bbb"], "CachedResponseMismatch attrs")

    for name, fields in DATACLASS_FIELDS.items():
        got = o["dataclasses"][name]
        ok(got[0], f"{name} is not a dataclass")
        eq(got[1], fields, f"{name} field order")

    digest = o["digest"]
    ok(_is_hex16(digest), f"digest {digest!r} is not a lowercase hex xxh64")
    eq(o["run_hash"], f"v3-{digest}", "run hash is the digest tagged with the version")
    eq(o["identity_version"], 3, "identity_version")
    eq(o["cache_enabled"], True, "cache_enabled")
    eq(o["same_inputs_hash"], o["run_hash"], "same inputs, same run hash")
    ne(o["other_dataset_hash"], o["run_hash"], "a different dataset is a different run")
    raised(o["frozen"], mro="FrozenInstanceError", msg="frozen RunIdentity")

    # the stamp file
    eq(o["stamp_sorted_keys"], ["components", "created_at", "digest", "identity_version", "run_hash", "updated_at"], "stamp keys")
    payload = o["stamp_payload"]
    eq(payload["identity_version"], 3, "stamp identity_version")
    eq(payload["run_hash"], o["run_hash"], "stamp run_hash")
    eq(payload["digest"], digest, "stamp digest")
    eq(payload["components"], o["stamp_components"], "stamp components")
    eq(payload["created_at"], NOW, "stamp created_at")
    eq(payload["updated_at"], NOW, "stamp updated_at")
    eq(o["stamp_written"], json.dumps(payload, indent=2, sort_keys=True) + "\n",
       "stamp is indent=2, sort_keys=True, one trailing newline")
    eq(o["stamp_created_at"], NOW, "returned stamp created_at")
    eq(o["again_times"], [NOW, LATER], "rewrite keeps created_at, moves updated_at")
    eq(o["again_disk_times"], [NOW, LATER], "rewrite on disk")
    ok(o["round_trip_ok"], "stamp to_dict/from_dict round trips")

    # reading a stamp back
    eq(o["read_back_hash"], o["run_hash"], "read_run_stamp hash")
    ok(o["read_absent"], "an absent stamp reads as None")
    ok(o["read_broken"], "an unparseable stamp reads as None")
    ok(o["read_partial"], "an incomplete stamp reads as None")

    # reconciling
    eq(o["created"], ["created", None, ["run_identity.json"]], "created")
    eq(o["adopted"], ["adopted", None, ["payload.txt", "run_identity.json"], "someone else's bytes"], "adopted")
    eq(o["upgraded"], ["upgraded", 2, 3, "2024-06-01T00:00:00", NOW], "upgraded")
    eq(o["matched"], ["matched", 3, "2024-06-01T00:00:00", LATER], "matched")
    raised(o["newer_raise"], mro="RunIdentityMismatch", mismatched_components=["identity_version"], msg="newer stamp")
    eq(o["newer_after"], 4, "a newer stamp is left as found")
    raised(o["foreign_raise"], mro="RunIdentityMismatch",
           found_run_hash="v3-ffffffffffffffff", expected_run_hash=o["run_hash"],
           mismatched_components=["model_name"], msg="foreign stamp")
    eq(o["foreign_after"], [["payload.txt", "run_identity.json"], "v3-ffffffffffffffff"], "a mismatch deletes nothing")

    # llm.py
    eq(o["fn_hash_none"], FN_HASH_NONE, "_get_function_hash(None)")
    eq(o["fn_hash_none_llm"], o["fn_hash_none"], "the moved function is re-exported")
    eq(o["fn_hash_stub"][0], o["fn_hash_stub"][1], "re-exported function agrees on a real function")
    ok(o["no_hash_fingerprint"], "_hash_fingerprint is replaced, not kept")
    eq(o["backend_props"], {"backend": True, "backend_params": True}, "LLM.backend/backend_params are properties")

    # db.py migration
    ok("parse_func" in o["runs_columns_names"] and "identity_version" in o["runs_columns_names"],
       f"RUNS_COLUMNS is missing the new columns: {o['runs_columns_names']}")
    eq(o["added"], ["identity_version", "parse_func"], "validate_schema added set")
    ok("parse_func" in o["live_columns"] and "identity_version" in o["live_columns"], "live columns")
    eq(o["migrated_row"], [None, None, "s0", NOW], "existing row survives with NULLs")
    eq(o["second_validate"], [], "a second validation adds nothing")
    raised(o["hostile_raise"], mro="RuntimeError", msg="hostile schema")
    ok("mismatch" in o["hostile_raise"].get("str", ""), f"hostile message: {o['hostile_raise'].get('str')}")

    # store_metadata
    eq(o["insert_result"], "inserted", "store_metadata inserted")
    eq(o["inserted_row"], ["def q(): pass", 3, NOW, NOW, "s1", None], "inserted row")
    eq(o["update_none_session"], "updated", "store_metadata updated")
    eq(o["updated_row"], ["s1", NOW, LATER], "a None session id leaves the recorded one alone")
    eq(o["updated_count"], 1, "one row after update")
    eq(o["update_new_session"], "updated", "store_metadata updated again")
    eq(o["updated_session"], "s2", "a new session id is written")

    # curator_response
    eq(o["cr_last_field"], "run_identity", "run_identity declared last")
    ok(o["cr_last_default_none"], "run_identity default is None")
    eq(o["response_run_identity"], o["saved_dict"], "run_identity travels through to_dict")
    eq(o["on_disk_hash"], o["run_hash"], "the saved response carries the run hash")
    eq(o["loaded_run_identity"], o["saved_dict"], "load returns the run identity")
    raised(o["load_mismatch"], mro="CachedResponseMismatch", field="fingerprint",
           expected=o["ds_fingerprint"], found=o["other_fingerprint"], msg="load fingerprint mismatch")
    eq(o["load_noverify_len"], 2, "verify=False takes the dataset it is handed")
    ok(o["legacy_run_identity_none"], "a response written before run identities still loads")

    # cached-dataset flag
    ok(o["stale_stopped"], "run() reached validate_config")
    ok(o["stale_flag_cleared"], "run() clears the flag before it consults the cache")
    ok(o["warm_returns_ds"], "a warm cache returns the dataset")
    ok(o["warm_flag_set"], "a warm cache sets the flag")

    # an identity error out of the cache is not swallowed
    raised(o["cached_mismatch_propagates"], mro="CachedResponseMismatch", msg="cache mismatch propagates")
    ok(o["cached_missing_swallowed"], "a non-identity error is still swallowed")


# ---------------------------------------------------------------------------
# r1 — what the run key is computed from
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["keys"], TWELVE, "IDENTITY_COMPONENT_KEYS")
    ok(o["keys_sorted"], "the twelve keys are alphabetical")
    eq(o["components_sorted"], TWELVE, "the identity is computed from the twelve keys")

    eq(o["named_prompt"], o["fh_prompt"], "prompt_func_hash == _get_function_hash(prompt)")
    eq(o["named_parse"], o["fh_parse"], "parse_func_hash == _get_function_hash(parse)")
    ne(o["named_parse"], o["named_prompt"], "parse and prompt hashes differ")
    eq(o["parse_none"], o["fh_none"], "parse_func None hashes as _get_function_hash(None)")

    eq(o["gen_none"], {}, "generation_params None -> {}")
    eq(o["gen_empty"], {}, "generation_params {} -> {}")
    eq(o["gen_temp"], {"temperature": 0.7}, "generation_params carried")
    eq(o["rf_none"], "text", "response_format None -> 'text'")
    eq(o["rf_structured"], o["rf_reference"], "response_format is the compact sorted schema")
    eq(o["sp_none"], None, "system_prompt None")
    eq(o["sp_terse"], "be terse", "system_prompt carried")
    eq(o["rco_true"], True, "return_completions_object True")
    eq(o["rco_false"], False, "return_completions_object False")
    eq(o["model_name"], "gpt-4o-mini", "model_name carried")
    eq(o["batch_mode"], True, "batch_mode carried")
    eq(o["dataset_hash"], "9f1c8e2b7d4a6053", "dataset_hash carried")


def judge_r1_scope(o):
    eq(o["auto_backend"], "openai", "LLM.backend resolved on the auto path")
    eq(o["declared_backend"], "openai", "LLM.backend resolved on the declared path")
    eq(o["auto_component"], "openai", "auto-detect must not hash a declared None")
    eq(o["declared_component"], "openai", "declared backend component")
    eq(o["litellm_backend"], "litellm", "backend is read off the object")
    eq(o["auto_params"], {}, "backend_params is {} when none were given")
    eq(o["configured_params"], {"batch_size": 3, "max_retries": 7}, "backend_params is what __init__ was handed")
    eq(o["configured_params_after_mutate"], {"batch_size": 3, "max_retries": 7}, "backend_params hands out a copy")


def judge_r1_exclusions(o):
    eq(o["allowlist"], sorted(IDENTITY_BACKEND_KEYS), "IDENTITY_BACKEND_PARAM_KEYS")
    for key, seen in o["per_knob"].items():
        carried, forked, value = seen["carried"], seen["forked"], seen["value"]
        if key in IDENTITY_BACKEND_KEYS:
            eq(carried.get(key), value, f"{key} is identity and must be carried")
            ok(forked, f"changing {key} must fork the cache directory")
        else:
            ok(key not in carried, f"{key} reached the identity components as {carried!r}")
            ok(not forked, f"changing {key} must not fork the cache directory")
    eq(o["noisy_carried"], {"base_url": "https://x/v1"}, "a pile of noise knobs leaves only base_url")
    ok(not o["noisy_forked"], "a pile of noise knobs does not fork the cache")


def judge_r1_observability(o):
    eq(o["components_sorted"], TWELVE, "the stated component table holds")
    eq(sorted(o["identity_keys"]), TWELVE, "IDENTITY_COMPONENT_KEYS is the table")
    eq(o["backend_params"], {"base_url": "https://x/v1"}, "only the allowlisted backend param is carried")
    ok(o["no_key_in_components"], "the api key is written down in the components")
    ok(o["no_key_in_stamp"], "the api key must never reach the stamp file")
    ok(o["url_in_stamp"], "the base_url does reach the stamp file")
    eq(o["rotated_hash"], o["base_hash"], "rotating the key or the retry budget is the same run")
    for i, changed in enumerate(o["changed_hashes"]):
        ne(changed, o["base_hash"], f"changed component {i} must be a different run")
    eq(o["auto_hash"], o["declared_hash"], "two ways of saying the same backend are the same run")


# ---------------------------------------------------------------------------
# r2 — where a cache-disabled run's identity comes from
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    cri = o["compute_run_id"]
    ok(cri[0], "compute_run_identity takes run_id")
    eq(cri[1], "KEYWORD_ONLY", "run_id is keyword-only")
    eq(cri[2], None, "run_id default is None")
    for name, taken in o["callers"].items():
        ok(taken[0], f"{name} takes run_id")
        ok(taken[1] in ("KEYWORD_ONLY", "POSITIONAL_OR_KEYWORD"), f"{name} run_id kind {taken[1]}")
        eq(taken[2], None, f"{name} run_id default is None")
    eq(o["cache_enabled"], False, "cache_enabled False")
    eq(o["run_id"], "local-run-7", "the supplied id identifies a cache-disabled run")
    eq(o["replay_same_stub"], o["base_hash"], "same id, same directory")
    eq(o["replay_new_stub"], o["base_hash"], "same id over a fresh stub, same directory")
    ne(o["other_id"], o["base_hash"], "a different id is a different run")
    ne(o["other_inputs"], o["base_hash"], "the same id over different inputs is a different run")


def judge_r2_scope(o):
    ok(o["cached_stopped"], "the cached run reached the processor")
    eq(o["cached_dirs"], 1, "one cached run directory")
    eq(o["cached_run_id"], None, "a cached run has no ephemeral id")
    eq(o["env_stopped"], [True, True], "both CURATOR_RUN_ID runs reached the processor")
    eq(o["named_dirs"], 1, "two runs of one CURATOR_RUN_ID share a directory")
    eq(o["named_run_id"], "ci-job-42", "the environment's id identifies the run")
    ok(o["explicit_stopped"], "the explicit run reached the processor")
    eq(o["given_dirs"], 1, "an explicit run_id made one directory")
    eq(o["given_run_id"], "explicit-7", "an id handed to the call wins over the environment")
    eq(o["minted_stopped"], [True, True], "both unidentified runs reached the processor")
    eq(o["minted_dirs"], 2, "two unidentified runs must not share a directory")
    ids = o["minted_ids"]
    eq(len(set(ids)), 2, f"both runs were minted the same id: {ids}")
    for value in ids:
        ok(value not in (None, "", "ci-job-42", "explicit-7"), f"minted run id {value!r}")
        ok(isinstance(value, str) and len(value) == 32 and all(c in "0123456789abcdef" for c in value),
           f"minted run id {value!r} is not a uuid4 hex")


def judge_r2_failure_behavior(o):
    raised(o["missing_none"], mro="RunIdentityError", msg="cache-disabled, run_id=None")
    raised(o["missing_absent"], mro="RunIdentityError", msg="cache-disabled, no run_id")
    raised(o["missing_empty"], mro="RunIdentityError", msg="cache-disabled, empty run_id")
    raised(o["cached_with_id"], mro="RunIdentityError", msg="cached run handed a run_id")
    raised(o["call_with_id"], mro="RunIdentityError", msg="a cached call handed a run_id")
    eq(o["dirs_after"], [], "a refused run leaves no directory behind")
    ok(o["cached_not_present"], "the refused run's directory was not created")


def _scan_no_randomness():
    """The AST no-randomness check of test_r2, over the file on disk.

    The ticket names `run_identity.py`; read it from SUBMISSION_SRC (parsing text
    executes nothing) rather than trusting the worker's reported source.
    """
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    candidates = ["bespokelabs/curator/run_identity.py",
                  "bespokelabs/curator/run_identity/__init__.py"]
    source = None
    for rel in candidates:
        path = root / rel
        if path.is_file():
            source = path.read_text(encoding="utf-8", errors="replace")
            break
    if source is None:
        raise Fail(f"cannot read run_identity source at any of {candidates} under {root}")
    banned = {"random", "secrets", "uuid"}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                ok(alias.name.split(".")[0] not in banned, f"run_identity imports {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            ok((node.module or "").split(".")[0] not in banned, f"run_identity imports from {node.module}")
        elif isinstance(node, ast.Attribute):
            ok(node.attr != "urandom", "run_identity reads os.urandom")
        elif isinstance(node, ast.Name):
            ok(node.id != "urandom", "run_identity reads urandom")


def judge_r2_observability(o):
    run_hash = o["run_hash"]
    ok(isinstance(run_hash, str) and run_hash.startswith("v3-nocache-"), f"a cache-disabled run hash is greppable, got {run_hash!r}")
    eq(len(run_hash), 27, f"{run_hash!r} is {len(run_hash)} characters")
    eq(o["run_hash_stable"], run_hash, "a replay of the same id is byte-equal")
    ne(o["run_hash_other"], run_hash, "a different id is a different run")
    eq(o["cached_run_id"], None, "a cached run carries no run id")
    ok(not str(o["cached_run_hash"]).startswith("v3-nocache-"), "a cached run is not a nocache run")
    _scan_no_randomness()


JUDGES = {
    "test_open::test_open_feature__a_versioned_run_identity_stamps_reconciles_and_is_recorded": judge_open,
    "test_r1::test_rule__the_key_is_exactly_twelve_components_and_the_parse_function_is_one_of_them": judge_r1_rule,
    "test_r1::test_scope__the_backend_component_is_the_resolved_name_not_the_declared_argument": judge_r1_scope,
    "test_r1::test_exclusions__only_four_backend_params_fork_the_cache_and_the_api_key_is_not_one": judge_r1_exclusions,
    "test_r1::test_observability__the_stated_component_table_holds_and_no_api_key_reaches_the_stamp": judge_r1_observability,
    "test_r2::test_rule__a_cache_disabled_run_is_identified_by_a_run_id_its_caller_supplies": judge_r2_rule,
    "test_r2::test_scope__the_call_mints_the_default_id_from_the_environment_and_passes_it_down": judge_r2_scope,
    "test_r2::test_failure_behavior__a_missing_id_and_an_unwanted_one_are_both_refused": judge_r2_failure_behavior,
    "test_r2::test_observability__the_nocache_run_hash_is_stable_and_the_module_reads_no_randomness": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g4_run_cache_identity" '
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
