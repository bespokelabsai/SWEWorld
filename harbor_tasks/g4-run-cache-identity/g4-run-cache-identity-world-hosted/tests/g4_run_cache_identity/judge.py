"""g4 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote, the directories the probe's scenarios
left under the artifacts root, and the cloned source text; writes a `junit.xml`
whose `classname`/`name` are the suite's node ids — so `score.py` folds them into
the fact keys and `test.sh`/`score.py` are unchanged. It runs as root, stdlib
only. The worker cannot read it: `test.sh` keeps /tests root-only for a split
suite, and the worker's jail holds only `probe.py`, `probe_support.py`,
`fixture_spec.py` and `harness.py`.

WHY THE ANSWERS HERE ARE NOT ENOUGH ON THEIR OWN. Keeping this file unreadable
stopped the worker copying the expected values out of it. It did not stop the
worker writing them anyway: the answers are the planted requirement, which the
world publishes, and the old fixture was the same every run. A capture of one
correct run replayed onto a tree that implemented nothing passed every hidden
fact, and r2.failure_behavior was almost entirely exception names the worker
reported. Three things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the
    model, dataset hash, generation params, system prompt, response model,
    prompt and parse functions, backend-knob values and combinations, run ids
    and rows, and this file works out the components an identity over THOSE
    inputs must carry. A run hash cannot be recomputed here (xxh64 is not
    stdlib and the payload's spelling is the implementation's), so hashes are
    graded relationally — but always beside the seeded components they were
    computed from, and never alone for a fact;
  * **the directories are read here.** The stamp `write_run_stamp` wrote, the
    cache directories `LLM.__call__` created and the stamps inside them: this
    process opens them under the artifacts root, refusing symlinks, and checks
    them against the run's inputs rather than trusting a flag;
  * **the constants that cannot be re-drawn are read out of the source** as
    well as the run: `IDENTITY_COMPONENT_KEYS`, `IDENTITY_BACKEND_PARAM_KEYS`.

The residual, stated plainly: a submission that implements the requirement inside
a forged hook — computing, from `fixture_spec`, what a correct implementation
would have produced — still passes, because it has then done the work. What is
gone is passing by repeating values that were knowable in advance.

`test_r1`/`test_r2` stay the human-readable reference for what each fact means;
their worked example uses the old fixed fixture ("d0", "local-run-7").
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import stat
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used


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
    ok(isinstance(info, dict) and info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')} ({str(info.get('str', ''))[:200]})")
    for name, value in attrs.items():
        eq(info.get(name), value, f"{msg}: {name}")


def value_of(step, msg):
    """The value of a probe step recorded with `attempt`, or the step's failure."""
    ok(isinstance(step, dict), f"{msg}: not measured")
    ok("error" not in step, f"{msg}: {step.get('error')}")
    return step.get("value")


# ---------------------------------------------------------------------------
# The answers
# ---------------------------------------------------------------------------
TWELVE = [
    "backend", "backend_params", "batch_mode", "dataset_hash", "generation_params",
    "model_name", "parse_func_hash", "prompt_func_hash", "response_format",
    "return_completions_object", "run_id", "system_prompt",
]
IDENTITY_BACKEND_KEYS = {"azure_deployment", "base_url", "batch_size", "completion_window"}
NOT_IDENTITY_KEYS = set(fixture_spec.KNOBS) - IDENTITY_BACKEND_KEYS
FN_HASH_NONE = "ef46db3751d8e999"
STAMP = "run_identity.json"
RUN_ID_PARAM = "run_id"
RUN_ID_ENV = "CURATOR_RUN_ID"
NOCACHE_PREFIX = "v3-nocache-"
NOCACHE_LEN = 27
BANNED_IMPORTS = {"random", "secrets", "uuid"}

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

# Where `sym` looks for a module-level name, as source files.
SYMBOL_FILES = ("bespokelabs/curator/run_identity.py", "bespokelabs/curator/run_identity",
                "bespokelabs/curator/__init__.py", "bespokelabs/curator/llm/llm.py",
                "bespokelabs/curator/db.py", "bespokelabs/curator/types/curator_response.py")

SPEC: dict = {}
ARTIFACTS = pathlib.Path("/nonexistent")


def _is_hex(value, width=None) -> bool:
    return (isinstance(value, str) and (width is None or len(value) == width) and value != ""
            and all(c in "0123456789abcdef" for c in value))


# ---------------------------------------------------------------------------
# reading what the scenarios left, as root, without trusting it
# ---------------------------------------------------------------------------
def _safe_path(rel: str) -> pathlib.Path:
    """ARTIFACTS/rel, refusing a symlink anywhere below the artifacts root.

    The worker owns these directories, so any entry can be a symlink by the time
    root reads it — pointing at /opt/world-state or at a file planted before the
    run. `lstat` every component and open with O_NOFOLLOW.
    """
    ok(".." not in pathlib.PurePosixPath(rel).parts and not rel.startswith("/"), f"bad path {rel!r}")
    path = ARTIFACTS
    for part in pathlib.PurePosixPath(rel).parts:
        path = path / part
        try:
            st = os.lstat(path)
        except OSError:
            raise Fail(f"{rel}: does not exist")
        ok(not stat.S_ISLNK(st.st_mode), f"{rel}: is a symlink")
    return path


def read_bytes(rel: str) -> bytes:
    path = _safe_path(rel)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise Fail(f"{rel}: {exc}")
    try:
        st = os.fstat(fd)
        ok(stat.S_ISREG(st.st_mode), f"{rel}: not a regular file")
        ok(st.st_size <= 4 * 1024 * 1024, f"{rel}: too large")
        with os.fdopen(fd, "rb") as fh:
            return fh.read()
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def entries(dirrel: str) -> tuple:
    """(directories, regular files) directly under ARTIFACTS/dirrel, symlinks refused."""
    path = _safe_path(dirrel)
    ok(stat.S_ISDIR(os.lstat(path).st_mode), f"{dirrel}: not a directory")
    dirs, files = [], []
    for name in sorted(os.listdir(path)):
        st = os.lstat(path / name)
        ok(not stat.S_ISLNK(st.st_mode), f"{dirrel}/{name}: is a symlink")
        if stat.S_ISDIR(st.st_mode):
            dirs.append(name)
        elif stat.S_ISREG(st.st_mode):
            files.append(name)
    return dirs, files


def stamp_in(dirrel: str) -> tuple:
    """(parsed stamp, raw text) of the stamp inside a run directory."""
    raw = read_bytes(f"{dirrel}/{STAMP}").decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise Fail(f"{dirrel}/{STAMP}: not JSON: {exc}")
    ok(isinstance(parsed, dict), f"{dirrel}/{STAMP}: not a JSON object")
    return parsed, raw


def run_directory(dirrel: str, name: str) -> dict:
    """A cache run directory `LLM.__call__` made: named for its stamp's run hash,
    and stamped with this run's drawn model — so it was made THIS run."""
    stamp, raw = stamp_in(f"{dirrel}/{name}")
    eq(stamp.get("run_hash"), name, f"{dirrel}/{name}: the directory is named for its stamp's run hash")
    ok(SPEC["call_model"] in raw,
       f"{dirrel}/{name}: the stamp does not describe this run's model {SPEC['call_model']!r}")
    components = stamp.get("components")
    ok(isinstance(components, dict), f"{dirrel}/{name}: the stamp carries no components")
    return components


# ---------------------------------------------------------------------------
# reading the submission's source — for the constants that cannot be re-drawn
# ---------------------------------------------------------------------------
def _symbol_sources():
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in SYMBOL_FILES:
        path = root / rel
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for file in files:
            if file.is_file() and not file.is_symlink():
                yield file.read_text(errors="replace")


def _literal(node):
    """A literal value, or the set a `frozenset({...})`/`set([...])` call spells; else raises."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in ("frozenset", "set", "tuple", "list") and len(node.args) == 1 and not node.keywords:
        inner = ast.literal_eval(node.args[0])
        return set(inner) if node.func.id in ("frozenset", "set") else list(inner)
    return ast.literal_eval(node)


def defined(name: str, check):
    """The module-level assignment of `name` somewhere `sym` looks, handed to
    `check` when it is a literal.

    A non-literal assignment is accepted here and left to the runtime value the
    probe reported; what fails is a tree that REPORTS the constant without
    defining it at all, or defines it as a different literal.
    """
    seen = False
    for src in _symbol_sources():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                seen = True
                try:
                    literal = _literal(value)
                except (ValueError, TypeError, SyntaxError):
                    continue
                check(literal, f"{name} as written in the source")
    ok(seen, f"no module of bespokelabs.curator assigns {name}")


# ---------------------------------------------------------------------------
# the expected identity, from the seed
# ---------------------------------------------------------------------------
def filtered(params) -> dict:
    return {k: v for k, v in dict(params or {}).items() if k in IDENTITY_BACKEND_KEYS}


def identity_value(step, msg) -> dict:
    """A recorded identity, with its components present and a plain dict."""
    value = value_of(step, msg)
    ok(isinstance(value, dict), f"{msg}: no identity recorded")
    ok(isinstance(value.get("components"), dict), f"{msg}: no components recorded")
    return value


def expected_stub_components(over: dict, dataset_hash: str, fh: dict, model_schema) -> dict:
    """What a stub built from `over` must be identified by (a cached run)."""
    def fn_hash(ref):
        return fh["none"] if ref is None else fh[ref]

    rf = over.get("response_format")
    gen = over["generation_params"] if "generation_params" in over else SPEC["generation_params"]
    return {
        "backend": over.get("backend", "openai"),
        "backend_params": filtered(over.get("backend_params")),
        "batch_mode": bool(over.get("batch_mode", False)),
        "dataset_hash": dataset_hash,
        "generation_params": dict(gen or {}),
        "model_name": over.get("model_name", SPEC["model"]),
        "parse_func_hash": fn_hash(over.get("parse_func")),
        "prompt_func_hash": fn_hash(over.get("prompt_func")),
        "response_format": "text" if rf is None else model_schema,
        "return_completions_object": bool(over.get("return_completions_object", False)),
        "run_id": None,
        "system_prompt": over.get("system_prompt"),
    }


_JSON_TYPES = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}


def check_model_schema(schema):
    """The worker's reference for the drawn response model is that model's
    compact, key-sorted schema — checked against the recipe, so it is not a
    string the worker could pick."""
    ok(isinstance(schema, str), f"response model schema not recorded: {schema!r}")
    try:
        parsed = json.loads(schema)
    except ValueError:
        raise Fail(f"response model schema is not JSON: {schema[:200]!r}")
    eq(json.dumps(parsed, sort_keys=True, separators=(",", ":")), schema, "the schema reference is compact and sorted")
    recipe = SPEC["response_model"]
    eq(parsed.get("title"), recipe["name"], "response model title")
    props = parsed.get("properties") or {}
    eq(sorted(props), sorted(name for name, _ in recipe["fields"]), "response model fields")
    for name, kind in recipe["fields"]:
        eq(props[name].get("type"), _JSON_TYPES[kind], f"response model field {name} type")


# ---------------------------------------------------------------------------
# open feature (weight 0)
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["ri_version"], 3, "RUN_IDENTITY_VERSION")
    eq(o["ri_filename"], STAMP, "RUN_IDENTITY_FILENAME")
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
    ok(_is_hex(digest, 16), f"digest {digest!r} is not a lowercase hex xxh64")
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
    eq(o["created"], ["created", None, [STAMP]], "created")
    eq(o["adopted"], ["adopted", None, ["payload.txt", STAMP], "someone else's bytes"], "adopted")
    eq(o["upgraded"], ["upgraded", 2, 3, "2024-06-01T00:00:00", NOW], "upgraded")
    eq(o["matched"], ["matched", 3, "2024-06-01T00:00:00", LATER], "matched")
    raised(o["newer_raise"], mro="RunIdentityMismatch", mismatched_components=["identity_version"], msg="newer stamp")
    eq(o["newer_after"], 4, "a newer stamp is left as found")
    raised(o["foreign_raise"], mro="RunIdentityMismatch",
           found_run_hash="v3-ffffffffffffffff", expected_run_hash=o["run_hash"],
           mismatched_components=["model_name"], msg="foreign stamp")
    eq(o["foreign_after"], [["payload.txt", STAMP], "v3-ffffffffffffffff"], "a mismatch deletes nothing")

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
# The components r1.rule grades by value. `backend`/`backend_params` belong to
# scope and exclusions, `run_id` to r2; rule still requires all twelve KEYS.
RULE_GRADED = [k for k in TWELVE if k not in ("backend", "backend_params", "run_id")]


def judge_r1_rule(o):
    eq(o["keys"], TWELVE, "IDENTITY_COMPONENT_KEYS")
    defined("IDENTITY_COMPONENT_KEYS", lambda got, msg: eq(list(got), TWELVE, msg))

    fh = {ref: value_of(o["fh"].get(ref), f"_get_function_hash({ref})") for ref in ("@prompt", "@parse", "none")}
    eq(fh["none"], FN_HASH_NONE, "_get_function_hash(None)")
    ok(len({fh["@prompt"], fh["@parse"], fh["none"]}) == 3,
       f"the drawn prompt and parse functions must hash apart from each other and from None: {fh}")
    schema = value_of(o["model_schema"], "the response model's schema")
    check_model_schema(schema)

    for label, over, dataset_hash in fixture_spec.component_variants(SPEC):
        got = identity_value(o["variants"].get(label), f"identity [{label}]")["components"]
        eq(sorted(got), TWELVE, f"[{label}] the identity is computed from exactly the twelve keys")
        want = expected_stub_components(over, dataset_hash, fh, schema)
        for key in RULE_GRADED:
            eq(got[key], want[key], f"[{label}] component {key}")


def judge_r1_scope(o):
    eq(value_of(o["auto_backend"], "LLM.backend (auto-detect)"), "openai", "LLM.backend resolved on the auto path")
    eq(value_of(o["declared_backend"], "LLM.backend (declared)"), "openai", "LLM.backend resolved on the declared path")
    auto = identity_value(o["auto_identity"], "identity of the auto-detected LLM")["components"]
    declared = identity_value(o["declared_identity"], "identity of the declared LLM")["components"]
    eq(auto.get("backend"), "openai", "auto-detect must not hash a declared None")
    eq(declared.get("backend"), "openai", "declared backend component")
    stub = identity_value(o["stub_identity"], "identity of a stub")["components"]
    eq(stub.get("backend"), SPEC["stub_backend"], "backend is read off the object, whatever it says")

    eq(value_of(o["auto_params"], "LLM.backend_params (none given)"), {}, "backend_params is {} when none were given")
    eq(value_of(o["configured_params"], "LLM.backend_params"), SPEC["llm_params"],
       "backend_params is what __init__ was handed")
    eq(value_of(o["after_mutation"], "LLM.backend_params after mutating a copy"), SPEC["llm_params"],
       "backend_params hands out a copy")


def judge_r1_exclusions(o):
    eq(o["allowlist"], sorted(IDENTITY_BACKEND_KEYS), "IDENTITY_BACKEND_PARAM_KEYS")
    defined("IDENTITY_BACKEND_PARAM_KEYS", lambda got, msg: eq(set(got), IDENTITY_BACKEND_KEYS, msg))

    scenarios = fixture_spec.knob_scenarios(SPEC)
    plain = dict(scenarios[0][1])
    baseline = identity_value(o["scenarios"].get("plain"), "identity [plain]")
    hash_of_filter: dict = {}
    for label, params in scenarios:
        seen = identity_value(o["scenarios"].get(label), f"identity [{label}]")
        carried = seen["components"].get("backend_params")
        want = filtered(params)
        for key in params:
            if key not in IDENTITY_BACKEND_KEYS:
                ok(not isinstance(carried, dict) or key not in carried,
                   f"[{label}] {key} reached the identity components as {carried!r}")
        eq(carried, want, f"[{label}] backend_params carried")
        forks = want != filtered(plain)
        if forks:
            ne(seen["run_hash"], baseline["run_hash"], f"[{label}] must fork the cache directory")
        else:
            eq(seen["run_hash"], baseline["run_hash"], f"[{label}] must not fork the cache directory")
        # Across every scenario: same identity params, same run; different, different.
        canon = json.dumps(want, sort_keys=True)
        for other_canon, other_hash in hash_of_filter.items():
            if other_canon == canon:
                eq(seen["run_hash"], other_hash, f"[{label}] same identity params, same run")
            else:
                ne(seen["run_hash"], other_hash, f"[{label}] different identity params, different run")
        hash_of_filter.setdefault(canon, seen["run_hash"])

    eq(sorted(o["noise_keys"]), sorted(NOT_IDENTITY_KEYS), "the knobs that do not fork the cache")
    noise = identity_value(o["noise"], "identity with every noise knob at once")
    eq(noise["components"].get("backend_params"), plain, "a pile of noise knobs leaves only base_url")
    eq(noise["run_hash"], baseline["run_hash"], "a pile of noise knobs does not fork the cache")


def judge_r1_observability(o):
    params = SPEC["stamp_params"]
    base = identity_value(o["identity"], "identity of the stamp scenario")
    components = base["components"]
    eq(sorted(components), TWELVE, "the stated component table holds")
    eq(components.get("backend_params"), {"base_url": params["base_url"]},
       "only the allowlisted backend param is carried")
    ok(params["api_key"] not in json.dumps(components, sort_keys=True),
       "the api key is written down in the components")

    # The stamp write_run_stamp left, read from disk.
    value_of(o["stamp_write"], "write_run_stamp")
    dirs, files = entries("r1_obs/run")
    eq(len(files), 1, f"write_run_stamp left {files} (and directories {dirs})")
    raw = read_bytes(f"r1_obs/run/{files[0]}").decode("utf-8", errors="replace")
    ok(params["api_key"] not in raw, "the stamp file is cleartext on disk, so the api key must never be a component")
    ok(params["base_url"] in raw, "the base_url does reach the stamp file")
    try:
        on_disk = json.loads(raw)
    except ValueError:
        raise Fail("the stamp file is not JSON")
    eq(on_disk.get("run_hash"), base["run_hash"], "the stamp records the scenario's run hash")
    eq(on_disk.get("components"), components, "the stamp records the scenario's components")

    rotated = identity_value(o["rotated"], "identity with a rotated key and retry budget")
    eq(rotated["components"].get("backend_params"), {"base_url": params["base_url"]}, "rotated backend_params")
    eq(rotated["run_hash"], base["run_hash"], "rotating the key, the retries or the timeout is the same run")
    for i, step in enumerate(o["changed"]):
        changed = identity_value(step, f"changed identity {i}")
        ne(changed["run_hash"], base["run_hash"], f"changed component {i} must be a different run")
    auto = identity_value(o["auto"], "auto-detected LLM")
    declared = identity_value(o["declared"], "declared LLM")
    eq(auto["run_hash"], declared["run_hash"], "two ways of saying the same backend are the same run")


# ---------------------------------------------------------------------------
# r2 — where a cache-disabled run's identity comes from
# ---------------------------------------------------------------------------
def _param(signature, name, where):
    ok(isinstance(signature, list), f"{where}: no signature ({signature!r})")
    for entry in signature:
        if entry[0] == name:
            return entry
    raise Fail(f"{where} takes {[e[0] for e in signature]}, so no caller can hand it a run id")


def require_param(o):
    eq(o.get("param"), RUN_ID_PARAM, "the keyword a run id is passed by")


def judge_r2_rule(o):
    require_param(o)
    sigs = o["signatures"]
    entry = _param(sigs["compute_run_identity"], RUN_ID_PARAM, "compute_run_identity")
    eq(entry[1], "KEYWORD_ONLY", "run_id is keyword-only")
    eq(entry[2], None, "run_id default is None")
    for where in ("_run_identity", "__call__"):
        entry = _param(sigs[where], RUN_ID_PARAM, f"LLM.{where}")
        ok(entry[1] in ("KEYWORD_ONLY", "POSITIONAL_OR_KEYWORD"), f"LLM.{where} run_id kind {entry[1]}")
        eq(entry[2], None, f"LLM.{where} run_id default is None")

    rid = SPEC["id_rule"]
    base = identity_value(o["base"], "cache-disabled identity")
    eq(base["cache_enabled"], False, "cache_enabled False")
    eq(base["components"].get(RUN_ID_PARAM), rid, "the supplied id identifies a cache-disabled run")
    for label in ("replay_same_stub", "replay_new_stub"):
        again = identity_value(o[label], label)
        eq(again["components"].get(RUN_ID_PARAM), rid, f"{label} run id")
        eq(again["run_hash"], base["run_hash"], f"{label}: same id, same directory")
    other = identity_value(o["other_id"], "a different id")
    eq(other["components"].get(RUN_ID_PARAM), SPEC["id_rule_other"], "the other id is carried")
    ne(other["run_hash"], base["run_hash"], "a different id is a different run")
    inputs = identity_value(o["other_inputs"], "the same id over different inputs")
    eq(inputs["components"].get(RUN_ID_PARAM), rid, "the same id over different inputs is carried")
    ne(inputs["run_hash"], base["run_hash"], "the same id over different inputs is a different run")


def _stopped(calls, label, count):
    ok(isinstance(calls, list) and len(calls) == count, f"{label}: {count} call(s) not made ({calls!r})")
    for i, info in enumerate(calls):
        raised(info, mro="_Stop", msg=f"{label} call {i} reached the processor")


def judge_r2_scope(o):
    require_param(o)
    eq(o.get("env"), RUN_ID_ENV, "the environment variable a default run id comes from")

    # A cached run carries no id.
    _stopped(o.get("cached"), "the cached run", 1)
    dirs, _ = entries("r2_scope/cached")
    eq(len(dirs), 1, f"one cached run made {dirs}")
    eq(run_directory("r2_scope/cached", dirs[0]).get(RUN_ID_PARAM, "<<absent>>"), None,
       "a cached run has no ephemeral id in its components")

    # Caching disabled: the environment's id identifies the run.
    _stopped(o.get("from_env"), "the environment-identified runs", 2)
    dirs, _ = entries("r2_scope/from_env")
    eq(len(dirs), 1, f"two runs of one {RUN_ID_ENV} must share one directory, made {dirs}")
    eq(run_directory("r2_scope/from_env", dirs[0]).get(RUN_ID_PARAM), SPEC["id_env"],
       "the environment's id is what the run is identified by")

    # An id handed to the call wins over the environment.
    _stopped(o.get("explicit"), "the explicitly identified run", 1)
    dirs, _ = entries("r2_scope/explicit")
    eq(len(dirs), 1, f"an explicit run id made {dirs}")
    eq(run_directory("r2_scope/explicit", dirs[0]).get(RUN_ID_PARAM), SPEC["id_explicit"],
       "an id handed to the call wins over the environment")

    # With nothing to go on, each run mints a fresh uuid4 hex of its own.
    _stopped(o.get("minted"), "the unidentified runs", 2)
    dirs, _ = entries("r2_scope/minted")
    eq(len(dirs), 2, f"two unidentified runs must not share a directory, got {dirs}")
    ids = [run_directory("r2_scope/minted", name).get(RUN_ID_PARAM) for name in dirs]
    eq(len(set(ids)), 2, f"both runs were minted the same id: {ids}")
    for value in ids:
        ok(value not in (None, "", SPEC["id_env"], SPEC["id_explicit"]), f"minted run id {value!r}")
        ok(_is_hex(value, 32), f"minted run id {value!r} is not a uuid4 hex")


def judge_r2_failure_behavior(o):
    require_param(o)
    raised(o.get("missing_absent"), mro="RunIdentityError", msg="cache-disabled, no run_id")
    raised(o.get("missing_none"), mro="RunIdentityError", msg="cache-disabled, run_id=None")
    raised(o.get("missing_empty"), mro="RunIdentityError", msg="cache-disabled, empty run_id")
    raised(o.get("cached_with_id"), mro="RunIdentityError", msg="cached run handed a run_id")
    raised(o.get("call_with_id"), mro="RunIdentityError", msg="a cached call handed a run_id")

    # The cache root the refused call was pointed at holds exactly what the
    # legitimate control call made afterwards — this run's model, this run's id
    # — and nothing from the refusal.
    raised(o.get("control"), mro="_Stop", msg="the control call into the same cache reached the processor")
    dirs, _ = entries("r2_fail/cc")
    eq(len(dirs), 1, f"a refused run must not leave a directory behind: the cache holds {dirs} "
                     "after one refused and one accepted call")
    run_directory("r2_fail/cc", dirs[0])
    raw = read_bytes(f"r2_fail/cc/{dirs[0]}/{STAMP}").decode("utf-8", errors="replace")
    ok(SPEC["id_refused"] not in raw, "the refused run id reached a stamp")


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
        if path.is_file() and not path.is_symlink():
            source = path.read_text(encoding="utf-8", errors="replace")
            break
    if source is None:
        raise Fail(f"cannot read run_identity source at any of {candidates} under {root}")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                ok(alias.name.split(".")[0] not in BANNED_IMPORTS, f"run_identity imports {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            ok((node.module or "").split(".")[0] not in BANNED_IMPORTS, f"run_identity imports from {node.module}")
        elif isinstance(node, ast.Attribute):
            ok(node.attr != "urandom", "run_identity reads os.urandom")
        elif isinstance(node, ast.Name):
            ok(node.id != "urandom", "run_identity reads urandom")


def judge_r2_observability(o):
    require_param(o)
    uncached = identity_value(o["uncached"], "cache-disabled identity")
    run_hash = uncached["run_hash"]
    ok(isinstance(run_hash, str) and run_hash.startswith(NOCACHE_PREFIX),
       f"a cache-disabled run hash is greppable, got {run_hash!r}")
    eq(len(run_hash), NOCACHE_LEN, f"{run_hash!r} is {len(run_hash)} characters")
    eq(uncached["components"].get(RUN_ID_PARAM), SPEC["id_obs"], "the run id behind the hash")
    again = identity_value(o["uncached_again"], "the same call again")
    eq(again["components"].get(RUN_ID_PARAM), SPEC["id_obs"], "the replay's run id")
    eq(again["run_hash"], run_hash, "a replay of the same id is byte-equal")
    other = identity_value(o["uncached_other"], "a different id")
    eq(other["components"].get(RUN_ID_PARAM), SPEC["id_obs_other"], "the other run id")
    ne(other["run_hash"], run_hash, "a different id is a different run")
    cached = identity_value(o["cached"], "the cached identity")
    eq(cached["components"].get(RUN_ID_PARAM, "<<absent>>"), None, "a cached run carries no run id")
    ok(not str(cached["run_hash"]).startswith(NOCACHE_PREFIX), "a cached run is not a cache-disabled run")
    _scan_no_randomness()


JUDGES = {
    "test_open::test_open_feature__a_versioned_run_identity_stamps_reconciles_and_is_recorded": judge_open,
    "test_r1::test_rule__component_set": judge_r1_rule,
    "test_r1::test_scope__backend_resolution": judge_r1_scope,
    "test_r1::test_exclusions__backend_param_filter": judge_r1_exclusions,
    "test_r1::test_observability__stamp_contents": judge_r1_observability,
    "test_r2::test_rule__uncached_identity": judge_r2_rule,
    "test_r2::test_scope__identity_sourcing": judge_r2_scope,
    "test_r2::test_failure_behavior__refusals": judge_r2_failure_behavior,
    "test_r2::test_observability__uncached_hash_shape": judge_r2_observability,
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


def main(obs_path: str, out_path: str, seed: str, artifacts: str) -> int:
    global SPEC, ARTIFACTS
    SPEC = fixture_spec.derive(seed)
    ARTIFACTS = pathlib.Path(artifacts)

    try:
        observations = json.loads(pathlib.Path(obs_path).read_text())
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)
    if not isinstance(observations, dict):
        observations = {}

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if not isinstance(probe, dict):
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
