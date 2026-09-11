"""g4 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
helpers (`make_stub`, `identity_for`, `components_of`, `run_hash_of`, `sym`,
`batchy`, `run_dirs`, `stamped_run_id`), so a value here is the value the test
saw. The judge holds the assertions those tests made. A submission that returns
forged values only forges values the judge still checks against the real
expectations — which is implementing them.

Two g4-specific reproduction rules:

  * the probe is not under pytest, so every scenario that wanted `tmp_path` gets
    its own `probe_support.newtmp()` and every scenario that wanted `monkeypatch`
    gets the `MonkeyPatch` shim below, undone between probes so one day's patched
    env or attribute cannot leak into the next;
  * the run hashes and digests are HIGH-ENTROPY. The probe records curator's
    OBSERVED hash (twice, where the test proves stability) and the judge decides.
    For the cache-disabled `v3-nocache-` hash and the identity digest the source
    tests never pinned a literal — they check shape and self-consistency — so the
    judge reproduces those same relational checks (see judge.py). The probe never
    computes an expected hash of its own.
"""
from __future__ import annotations

import dataclasses
import inspect
import json
import os
import sqlite3
import sys
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest. g4 drives no provider socket: the stubs
# are duck-typed and `batchy(batch=True)` builds the batch processor, which
# never probes a provider.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

_MISSING = object()


class MonkeyPatch:
    """The slice of pytest's monkeypatch the g4 fixtures use, with undo.

    `test_r2` scope/failure want `setattr(..., raising=False)`, `setenv` and
    `delenv`; nothing here needs the rest. `undo()` runs between probes so one
    day's patched `_request_processor.run` or CURATOR_* env cannot leak into the
    next.
    """

    def __init__(self) -> None:
        self._undo: list = []

    def setattr(self, target, name, value, raising=True):
        if not hasattr(target, name) and raising:
            raise AttributeError(name)
        old = getattr(target, name, _MISSING)
        setattr(target, name, value)
        self._undo.append(("attr", target, name, old))

    def setenv(self, name, value):
        old = os.environ.get(name, _MISSING)
        os.environ[name] = value
        self._undo.append(("env", name, old))

    def delenv(self, name, raising=False):
        old = os.environ.pop(name, _MISSING)
        self._undo.append(("env", name, old))

    def undo(self):
        for entry in reversed(self._undo):
            kind = entry[0]
            if kind == "attr":
                _, target, name, old = entry
                if old is _MISSING:
                    try:
                        delattr(target, name)
                    except AttributeError:
                        pass
                else:
                    setattr(target, name, old)
            else:
                _, name, old = entry
                if old is _MISSING:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = old
        self._undo = []


# probe_support owns the curator imports and the answer-free stubs/inputs; reuse
# them so a probe calls curator exactly as the test does. Importing it runs the
# submission's `import bespokelabs.curator` — this process's whole purpose, and
# why it is disposable. The worker never imports test_open, whose source carries
# the expected answer literals.
import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402


# Attributes carried by the run-identity exception family; recorded whenever an
# exception is caught so the judge can check the ones the test asserted. Tuples
# become lists through json, which the judge compares against lists.
_EXC_ATTRS = ("path", "expected_run_hash", "found_run_hash", "mismatched_components",
              "cache_dir", "field", "expected", "found")


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain and the identity
    exception attributes it carries — the faithful stand-in for `pytest.raises`."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__], "str": str(exc)}
        for attr in _EXC_ATTRS:
            if hasattr(exc, attr):
                value = getattr(exc, attr)
                info[attr] = list(value) if isinstance(value, tuple) else value
        return info
    return {"raised": False, "mro": []}


def stopped(fn, *args, **kwargs) -> bool:
    """True iff the call ended with the `_Stop` sentinel the fixtures raise."""
    try:
        fn(*args, **kwargs)
    except S._Stop:
        return True
    return False


def _stop(*args, **kwargs):
    """End a driven call the moment the run directory has been decided."""
    raise S._Stop()


# ===========================================================================
# the openly stated feature
# ===========================================================================
def probe_open(mp) -> dict:
    S.importable()
    from bespokelabs.curator import LLM
    import bespokelabs.curator.llm.llm as llm_module
    from bespokelabs.curator.db import MetadataDB
    from bespokelabs.curator.types.curator_response import CuratorResponse
    from bespokelabs.curator.request_processor.base_request_processor import BaseRequestProcessor
    ri = S.ri
    tmp = S.newtmp()
    o: dict = {}

    # -- the module surface -------------------------------------------------
    o["ri_version"] = ri.RUN_IDENTITY_VERSION
    o["ri_filename"] = ri.RUN_IDENTITY_FILENAME
    surface_names = ("RunIdentity", "RunStamp", "RunDirectoryCheck", "RunIdentityError",
                     "RunIdentityMismatch", "CachedResponseMismatch", "compute_run_identity",
                     "write_run_stamp", "read_run_stamp", "reconcile_run_directory", "_get_function_hash")
    o["has_names"] = {name: hasattr(ri, name) for name in surface_names}
    o["surface"] = S.surface(ri)

    # -- the exception family -----------------------------------------------
    o["exc_subclass"] = [
        issubclass(ri.RunIdentityError, RuntimeError),
        issubclass(ri.RunIdentityMismatch, ri.RunIdentityError),
        issubclass(ri.CachedResponseMismatch, ri.RunIdentityError),
    ]
    mismatch = ri.RunIdentityMismatch("cache-dir-c", "v3-a", "v3-b", ("model_name",))
    o["mismatch_attrs"] = [mismatch.path, mismatch.expected_run_hash, mismatch.found_run_hash,
                           list(mismatch.mismatched_components)]
    stale = ri.CachedResponseMismatch("cache-dir-c", "fingerprint", "aaa", "bbb")
    o["stale_attrs"] = [stale.cache_dir, stale.field, stale.expected, stale.found]

    # -- three frozen dataclasses -------------------------------------------
    o["dataclasses"] = {}
    for cls in (ri.RunIdentity, ri.RunStamp, ri.RunDirectoryCheck):
        o["dataclasses"][cls.__name__] = [dataclasses.is_dataclass(cls),
                                          [f.name for f in dataclasses.fields(cls)]]

    # -- the identity of a run ----------------------------------------------
    stub = S.make_stub()
    identity = S.identity_for(stub)
    o["digest"] = read_field(identity, "digest")
    o["run_hash"] = S.run_hash_of(identity)
    o["identity_version"] = read_field(identity, "identity_version")
    o["cache_enabled"] = read_field(identity, "cache_enabled")
    o["same_inputs_hash"] = S.run_hash_of(S.identity_for(S.make_stub()))
    o["other_dataset_hash"] = S.run_hash_of(S.identity_for(stub, dataset_hash="other"))
    o["frozen"] = raises(setattr, identity, "run_hash", "v3-0000000000000000")

    # -- the stamp file ------------------------------------------------------
    from pathlib import Path
    home = tmp / "created" / "nested"
    stamp = ri.write_run_stamp(home, identity, now=S.NOW)
    o["stamp_written"] = (home / "run_identity.json").read_text()
    payload = json.loads(o["stamp_written"])
    o["stamp_payload"] = payload
    o["stamp_sorted_keys"] = sorted(payload)
    o["stamp_components"] = S.components_of(identity)
    o["stamp_created_at"] = read_field(stamp, "created_at")

    again = ri.write_run_stamp(home, identity, now=S.LATER, created_at=S.NOW)
    o["again_times"] = [read_field(again, "created_at"), read_field(again, "updated_at")]
    o["again_disk_times"] = [S.stamp_dict(home)["created_at"], S.stamp_dict(home)["updated_at"]]
    o["round_trip_ok"] = type(stamp).from_dict(stamp.to_dict()).to_dict() == stamp.to_dict()

    # -- reading a stamp back ------------------------------------------------
    o["read_back_hash"] = S.run_hash_of(ri.read_run_stamp(home))
    o["read_absent"] = ri.read_run_stamp(tmp / "nothing-here") is None
    broken = tmp / "broken"
    broken.mkdir()
    (broken / "run_identity.json").write_text("{not json")
    o["read_broken"] = ri.read_run_stamp(broken) is None
    partial = tmp / "partial"
    partial.mkdir()
    (partial / "run_identity.json").write_text(json.dumps({"run_hash": S.run_hash_of(identity)}))
    o["read_partial"] = ri.read_run_stamp(partial) is None

    # -- reconciling a directory: created / adopted / upgraded / matched -----
    fresh = tmp / "a"
    check = ri.reconcile_run_directory(fresh, identity, now=S.NOW)
    o["created"] = [read_field(check, "status"), read_field(check, "previous_version"),
                    os.listdir(fresh)]

    legacy = tmp / "b"
    legacy.mkdir()
    (legacy / "payload.txt").write_text("someone else's bytes")
    check = ri.reconcile_run_directory(legacy, identity, now=S.NOW)
    o["adopted"] = [read_field(check, "status"), read_field(check, "previous_version"),
                    sorted(os.listdir(legacy)), (legacy / "payload.txt").read_text()]

    older = tmp / "c"
    S.write_stamp_file(older, {
        "identity_version": 2,
        "run_hash": "v2-2917e0582eb73e61",
        "digest": "2917e0582eb73e61",
        "components": {"whatever": "v2 said"},
        "created_at": "2024-06-01T00:00:00",
        "updated_at": "2024-06-01T00:00:00",
    })
    check = ri.reconcile_run_directory(older, identity, now=S.NOW)
    o["upgraded"] = [read_field(check, "status"), read_field(check, "previous_version"),
                     S.stamp_dict(older)["identity_version"], S.stamp_dict(older)["created_at"],
                     S.stamp_dict(older)["updated_at"]]
    check = ri.reconcile_run_directory(older, identity, now=S.LATER)
    o["matched"] = [read_field(check, "status"), read_field(check, "previous_version"),
                    S.stamp_dict(older)["created_at"], S.stamp_dict(older)["updated_at"]]

    newer = tmp / "d"
    S.write_stamp_file(newer, {
        "identity_version": 4,
        "run_hash": "v4-2917e0582eb73e61",
        "digest": "2917e0582eb73e61",
        "components": S.components_of(identity),
        "created_at": S.NOW,
        "updated_at": S.NOW,
    })
    o["newer_raise"] = raises(ri.reconcile_run_directory, newer, identity, now=S.LATER)
    o["newer_after"] = S.stamp_dict(newer)["identity_version"]

    foreign_components = dict(S.components_of(identity))
    foreign_components["model_name"] = "some-other-model"
    foreign = tmp / "e"
    foreign.mkdir()
    (foreign / "payload.txt").write_text("the other run's files")
    S.write_stamp_file(foreign, {
        "identity_version": 3,
        "run_hash": "v3-ffffffffffffffff",
        "digest": "ffffffffffffffff",
        "components": foreign_components,
        "created_at": S.NOW,
        "updated_at": S.NOW,
    })
    o["foreign_raise"] = raises(ri.reconcile_run_directory, foreign, identity, now=S.LATER)
    o["foreign_after"] = [sorted(os.listdir(foreign)), S.stamp_dict(foreign)["run_hash"]]

    # -- what llm.py keeps, moves and loses ---------------------------------
    o["fn_hash_none"] = ri._get_function_hash(None)
    o["fn_hash_none_llm"] = llm_module._get_function_hash(None)
    o["fn_hash_stub"] = [llm_module._get_function_hash(S.make_stub), ri._get_function_hash(S.make_stub)]
    o["no_hash_fingerprint"] = not hasattr(LLM, "_hash_fingerprint")
    o["backend_props"] = {}
    for name in ("backend", "backend_params"):
        attribute = inspect.getattr_static(LLM, name)
        o["backend_props"][name] = (attribute is not None and not inspect.isfunction(attribute))

    # -- db.py: a migration instead of a refusal ----------------------------
    columns = S.sym("RUNS_COLUMNS")
    o["runs_columns_names"] = [row[0] if isinstance(row, (tuple, list)) else row for row in columns]

    db_path = tmp / "cache" / "metadata.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    S.make_old_db(db_path)
    db = MetadataDB(str(db_path))
    o["added"] = sorted(db.validate_schema())
    o["live_columns"] = [col[1] for col in db._get_current_schema()]
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("SELECT parse_func, identity_version, session_id, created_time FROM runs WHERE run_hash='old'").fetchone()
    o["migrated_row"] = list(row)
    o["second_validate"] = list(db.validate_schema())

    hostile = tmp / "hostile.db"
    with sqlite3.connect(str(hostile)) as conn:
        conn.execute("CREATE TABLE runs (wrong_col TEXT)")
        conn.commit()
    o["hostile_raise"] = raises(MetadataDB(str(hostile)).validate_schema)

    # -- db.py: store_metadata writes the parse function and says what it did
    fresh_db = MetadataDB(str(tmp / "cache2" / "metadata.db"))
    o["insert_result"] = fresh_db.store_metadata(dict(S.METADATA))
    with sqlite3.connect(fresh_db.db_path) as conn:
        row = conn.execute(
            "SELECT parse_func, identity_version, created_time, last_edited_time, session_id, total_cost_milli_dollars FROM runs WHERE run_hash='r1'"
        ).fetchone()
    o["inserted_row"] = list(row)
    o["update_none_session"] = fresh_db.store_metadata({**S.METADATA, "session_id": None, "timestamp": S.LATER})
    with sqlite3.connect(fresh_db.db_path) as conn:
        row = conn.execute("SELECT session_id, created_time, last_edited_time FROM runs WHERE run_hash='r1'").fetchone()
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    o["updated_row"] = list(row)
    o["updated_count"] = count
    o["update_new_session"] = fresh_db.store_metadata({**S.METADATA, "session_id": "s2", "timestamp": S.LATER})
    with sqlite3.connect(fresh_db.db_path) as conn:
        o["updated_session"] = conn.execute("SELECT session_id FROM runs WHERE run_hash='r1'").fetchone()[0]

    # -- curator_response: the identity travels, and load checks the dataset -
    cr_fields = [f.name for f in dataclasses.fields(CuratorResponse)]
    o["cr_last_field"] = cr_fields[-1]
    o["cr_last_default_none"] = dataclasses.fields(CuratorResponse)[-1].default is None

    ds = S.Dataset.from_list([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    other = S.Dataset.from_list([{"a": 9, "b": "z"}, {"a": 8, "b": "w"}])
    cache_dir = tmp / "run"
    cache_dir.mkdir()
    saved = stamp.to_dict()
    response = CuratorResponse(dataset=ds, cache_dir=str(cache_dir), model_name="gpt-4o-mini", run_identity=saved)
    o["response_run_identity"] = response.to_dict()["run_identity"]
    o["saved_dict"] = saved
    response.save(cache_dir)
    on_disk = json.loads((cache_dir / "response.json").read_text())
    o["on_disk_hash"] = on_disk["run_identity"]["run_hash"]
    o["loaded_run_identity"] = CuratorResponse.load(cache_dir, ds).run_identity
    o["load_mismatch"] = raises(CuratorResponse.load, cache_dir, other)
    o["ds_fingerprint"] = ds._fingerprint
    o["other_fingerprint"] = other._fingerprint
    o["load_noverify_len"] = len(CuratorResponse.load(cache_dir, other, verify=False).dataset)

    legacy_response = json.loads((cache_dir / "response.json").read_text())
    legacy_response.pop("dataset")
    legacy_response.pop("run_identity")
    (cache_dir / "response.json").write_text(json.dumps(legacy_response))
    o["legacy_run_identity_none"] = CuratorResponse.load(cache_dir, other).run_identity is None

    # -- the cached-dataset flag describes this run, not the last one -------
    from types import SimpleNamespace
    stale_ns = SimpleNamespace(
        _is_cached_dataset=True,
        attempt_loading_cached_dataset=lambda parse_func_hash: None,
        config=SimpleNamespace(model="m"),
        prompt_formatter=None,
        validate_config=_stop,
    )
    o["stale_stopped"] = stopped(BaseRequestProcessor.run, stale_ns, dataset=ds,
                                 working_dir=str(tmp), parse_func_hash="h", prompt_formatter=None)
    o["stale_flag_cleared"] = stale_ns._is_cached_dataset is False

    warm_ns = SimpleNamespace(
        _is_cached_dataset=False,
        attempt_loading_cached_dataset=lambda parse_func_hash: ds,
        config=SimpleNamespace(model="m"),
        prompt_formatter=None,
        validate_config=_stop,
    )
    o["warm_returns_ds"] = BaseRequestProcessor.run(warm_ns, dataset=ds, working_dir=str(tmp),
                                                    parse_func_hash="h", prompt_formatter=None) is ds
    o["warm_flag_set"] = warm_ns._is_cached_dataset is True

    # -- an identity error out of the cache is not a warning ----------------
    def raise_mismatch(cache_dir, dataset, **kwargs):
        raise ri.CachedResponseMismatch("cache-dir-c", "fingerprint", "a", "b")

    def raise_missing(cache_dir, dataset, **kwargs):
        raise FileNotFoundError("response.json")

    holder = SimpleNamespace()
    original = CuratorResponse.load
    try:
        CuratorResponse.load = raise_mismatch
        o["cached_mismatch_propagates"] = raises(LLM._get_cached_response, holder, "cache-dir-c", ds)
        CuratorResponse.load = raise_missing
        o["cached_missing_swallowed"] = LLM._get_cached_response(holder, "cache-dir-c", ds) is None
    finally:
        CuratorResponse.load = original
    return o


# ===========================================================================
# r1 — what the run key is computed from
# ===========================================================================
def probe_r1_rule(mp) -> dict:
    S.importable()
    o: dict = {}
    keys = S.sym("IDENTITY_COMPONENT_KEYS")
    o["keys"] = list(keys)
    o["keys_sorted"] = list(keys) == sorted(keys)
    o["components_sorted"] = sorted(S.components_of(S.identity_for(S.make_stub())))

    function_hash = S.sym("_get_function_hash")
    named = S.components_of(S.identity_for(S.make_stub(prompt_func=S.prompt_one, parse_func=S.parse_two)))
    o["named_prompt"] = named["prompt_func_hash"]
    o["fh_prompt"] = function_hash(S.prompt_one)
    o["named_parse"] = named["parse_func_hash"]
    o["fh_parse"] = function_hash(S.parse_two)
    o["parse_none"] = S.components_of(S.identity_for(S.make_stub(parse_func=None)))["parse_func_hash"]
    o["fh_none"] = function_hash(None)

    o["gen_none"] = S.components_of(S.identity_for(S.make_stub(generation_params=None)))["generation_params"]
    o["gen_empty"] = S.components_of(S.identity_for(S.make_stub(generation_params={})))["generation_params"]
    o["gen_temp"] = S.components_of(S.identity_for(S.make_stub(generation_params={"temperature": 0.7})))["generation_params"]

    o["rf_none"] = S.components_of(S.identity_for(S.make_stub(response_format=None)))["response_format"]
    o["rf_structured"] = S.components_of(S.identity_for(S.make_stub(response_format=S.Answer)))["response_format"]
    # The reference the source compares against: the compact sorted schema of the
    # test's OWN input model, computed in the same environment as curator. Not an
    # answer literal — the judge checks curator's output equals this reference.
    o["rf_reference"] = json.dumps(S.Answer.model_json_schema(), sort_keys=True, separators=(",", ":"))

    o["sp_none"] = S.components_of(S.identity_for(S.make_stub(system_prompt=None)))["system_prompt"]
    o["sp_terse"] = S.components_of(S.identity_for(S.make_stub(system_prompt="be terse")))["system_prompt"]
    o["rco_true"] = S.components_of(S.identity_for(S.make_stub(return_completions_object=True)))["return_completions_object"]
    o["rco_false"] = S.components_of(S.identity_for(S.make_stub(return_completions_object=False)))["return_completions_object"]

    o["model_name"] = S.components_of(S.identity_for(S.make_stub(model_name="gpt-4o-mini")))["model_name"]
    o["batch_mode"] = S.components_of(S.identity_for(S.make_stub(batch_mode=True)))["batch_mode"]
    o["dataset_hash"] = S.components_of(S.identity_for(S.make_stub(), dataset_hash="9f1c8e2b7d4a6053"))["dataset_hash"]
    return o


def probe_r1_scope(mp) -> dict:
    S.importable()
    o: dict = {}
    auto = S.batchy(model_name="gpt-4o-mini", batch=True)             # backend= is None here
    declared = S.batchy(model_name="gpt-4o-mini", backend="openai", batch=True)
    o["auto_backend"] = auto.backend
    o["declared_backend"] = declared.backend
    o["auto_component"] = S.components_of(S.identity_for(auto, "d0"))["backend"]
    o["declared_component"] = S.components_of(S.identity_for(declared, "d0"))["backend"]
    o["litellm_backend"] = S.components_of(S.identity_for(S.make_stub(backend="litellm")))["backend"]

    o["auto_params"] = auto.backend_params
    given = {"batch_size": 3, "max_retries": 7}
    configured = S.batchy(model_name="gpt-4o-mini", batch=True, backend_params=dict(given))
    o["configured_params"] = configured.backend_params
    handed_out = configured.backend_params
    handed_out["batch_size"] = 999
    handed_out["injected"] = True
    o["configured_params_after_mutate"] = configured.backend_params
    return o


def probe_r1_exclusions(mp) -> dict:
    S.importable()
    o: dict = {}
    allowed = S.sym("IDENTITY_BACKEND_PARAM_KEYS")
    o["allowlist"] = sorted(allowed)

    plain = {"base_url": "https://x/v1"}
    o["baseline"] = S.run_hash_of(S.identity_for(S.make_stub(backend_params=dict(plain))))

    # Per knob: what curator carried and whether the cache directory forked.
    # The judge holds the identity/non-identity split; this file does not.
    per_knob: dict = {}
    non_forking: list = []
    for key, value in S.CANDIDATE_BACKEND_PARAMS:
        stub = S.make_stub(backend_params={**plain, key: value})
        carried = S.components_of(S.identity_for(stub))["backend_params"]
        forked = S.run_hash_of(S.identity_for(stub)) != o["baseline"]
        per_knob[key] = {"carried": carried, "forked": forked, "value": value}
        if not forked:
            non_forking.append((key, value))
    o["per_knob"] = per_knob

    # A pile of the knobs curator itself treats as noise, all at once: they must
    # still leave the run untouched. The noise set is derived from the live
    # observations above, never from a stored partition.
    noisy = S.make_stub(backend_params={**plain, **dict(non_forking)})
    o["noisy_carried"] = S.components_of(S.identity_for(noisy))["backend_params"]
    o["noisy_forked"] = S.run_hash_of(S.identity_for(noisy)) != o["baseline"]
    return o


def probe_r1_observability(mp) -> dict:
    S.importable()
    ri = S.ri
    tmp = S.newtmp()
    o: dict = {}
    params = {"base_url": "https://x/v1", "max_retries": 7, "api_key": "sk-secret", "request_timeout": 30}
    stub = S.make_stub(backend_params=dict(params))
    identity = S.identity_for(stub, "d0")
    components = S.components_of(identity)

    o["components_sorted"] = sorted(components)
    o["identity_keys"] = list(S.sym("IDENTITY_COMPONENT_KEYS"))
    o["backend_params"] = components["backend_params"]
    o["no_key_in_components"] = "sk-secret" not in json.dumps(components, sort_keys=True, default=repr)

    ri.write_run_stamp(tmp / "run", identity, now=S.NOW)
    stamp_text = (tmp / "run" / "run_identity.json").read_text()
    o["no_key_in_stamp"] = "sk-secret" not in stamp_text
    o["url_in_stamp"] = "https://x/v1" in stamp_text

    o["base_hash"] = S.run_hash_of(identity)
    rotated = S.make_stub(backend_params={"base_url": "https://x/v1", "max_retries": 999, "api_key": "sk-other"})
    o["rotated_hash"] = S.run_hash_of(S.identity_for(rotated, "d0"))

    o["changed_hashes"] = [
        S.run_hash_of(S.identity_for(S.make_stub(backend_params=dict(params), parse_func=S.parse_two), "d0")),
        S.run_hash_of(S.identity_for(S.make_stub(backend_params=dict(params), system_prompt="be terse"), "d0")),
        S.run_hash_of(S.identity_for(S.make_stub(backend_params=dict(params), return_completions_object=True), "d0")),
        S.run_hash_of(S.identity_for(S.make_stub(backend_params=dict(params), backend="litellm"), "d0")),
    ]

    auto = S.batchy(model_name="gpt-4o-mini", batch=True)
    declared = S.batchy(model_name="gpt-4o-mini", backend="openai", batch=True)
    o["auto_hash"] = S.run_hash_of(S.identity_for(auto, "d0"))
    o["declared_hash"] = S.run_hash_of(S.identity_for(declared, "d0"))
    return o


# ===========================================================================
# r2 — where a cache-disabled run's identity comes from
# ===========================================================================
def probe_r2_rule(mp) -> dict:
    S.importable()
    from bespokelabs import curator
    o: dict = {}
    params = inspect.signature(S.sym("compute_run_identity")).parameters
    o["compute_run_id"] = ["run_id" in params,
                           params["run_id"].kind.name if "run_id" in params else None,
                           params["run_id"].default if "run_id" in params else _sentinel_default()]

    o["callers"] = {}
    for name, func in (("_run_identity", curator.LLM._run_identity), ("__call__", curator.LLM.__call__)):
        taken = inspect.signature(func).parameters
        o["callers"][name] = ["run_id" in taken,
                              taken["run_id"].kind.name if "run_id" in taken else None,
                              taken["run_id"].default if "run_id" in taken else _sentinel_default()]

    stub = S.make_stub()
    identity = S.identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7")
    o["cache_enabled"] = read_field(identity, "cache_enabled")
    o["run_id"] = S.components_of(identity)["run_id"]
    o["base_hash"] = S.run_hash_of(identity)
    o["replay_same_stub"] = S.run_hash_of(S.identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7"))
    o["replay_new_stub"] = S.run_hash_of(S.identity_for(S.make_stub(), "d0", cache_enabled=False, run_id="local-run-7"))
    o["other_id"] = S.run_hash_of(S.identity_for(stub, "d0", cache_enabled=False, run_id="local-run-8"))
    o["other_inputs"] = S.run_hash_of(S.identity_for(stub, "other", cache_enabled=False, run_id="local-run-7"))
    return o


def _sentinel_default():
    """A JSON-safe stand-in for 'the parameter is absent' — never equals None."""
    return "<<absent>>"


def probe_r2_scope(mp) -> dict:
    S.importable()
    tmp = S.newtmp()
    o: dict = {}
    llm = S.batchy(model_name="gpt-4o-mini", batch=True)
    mp.setattr(llm._request_processor, "run", _stop, raising=False)
    rows = S.Dataset.from_list(S.ROWS)
    cache = tmp / "cc"
    mp.setenv("CURATOR_CACHE_DIR", str(cache))
    mp.delenv("CURATOR_DISABLE_CACHE", raising=False)
    mp.delenv("CURATOR_RUN_ID", raising=False)

    o["cached_stopped"] = stopped(llm, rows)
    cached = S.run_dirs(cache)
    o["cached_dirs"] = len(cached)
    o["cached_run_id"] = S.stamped_run_id(cache, cached[0]) if cached else "<<no-dir>>"

    mp.setenv("CURATOR_DISABLE_CACHE", "true")
    mp.setenv("CURATOR_RUN_ID", "ci-job-42")
    o["env_stopped"] = [stopped(llm, rows), stopped(llm, rows)]
    named = [name for name in S.run_dirs(cache) if name not in cached]
    o["named_dirs"] = len(named)
    o["named_run_id"] = S.stamped_run_id(cache, named[0]) if named else "<<no-dir>>"

    known = set(S.run_dirs(cache))
    o["explicit_stopped"] = stopped(llm, rows, run_id="explicit-7")
    given = [name for name in S.run_dirs(cache) if name not in known]
    o["given_dirs"] = len(given)
    o["given_run_id"] = S.stamped_run_id(cache, given[0]) if given else "<<no-dir>>"

    mp.delenv("CURATOR_RUN_ID")
    known = set(S.run_dirs(cache))
    o["minted_stopped"] = [stopped(llm, rows), stopped(llm, rows)]
    minted = [name for name in S.run_dirs(cache) if name not in known]
    o["minted_dirs"] = len(minted)
    o["minted_ids"] = [S.stamped_run_id(cache, name) for name in minted]
    return o


def probe_r2_failure_behavior(mp) -> dict:
    S.importable()
    tmp = S.newtmp()
    o: dict = {}
    stub = S.make_stub()
    o["missing_none"] = raises(S.identity_for, stub, "d0", cache_enabled=False, run_id=None)
    o["missing_absent"] = raises(S.identity_for, stub, "d0", cache_enabled=False)
    o["missing_empty"] = raises(S.identity_for, stub, "d0", cache_enabled=False, run_id="")
    o["cached_with_id"] = raises(S.identity_for, stub, "d0", cache_enabled=True, run_id="x")

    llm = S.batchy(model_name="gpt-4o-mini", batch=True)
    mp.setattr(llm._request_processor, "run", _stop, raising=False)
    cache = tmp / "cc"
    mp.setenv("CURATOR_CACHE_DIR", str(cache))
    mp.delenv("CURATOR_DISABLE_CACHE", raising=False)
    rows = S.Dataset.from_list(S.ROWS)
    cached = S.run_hash_of(S.identity_for(llm, rows._fingerprint))
    o["call_with_id"] = raises(llm, rows, run_id="x")
    dirs = S.run_dirs(cache)
    o["dirs_after"] = dirs
    o["cached_not_present"] = cached not in dirs
    return o


def probe_r2_observability(mp) -> dict:
    S.importable()
    o: dict = {}
    stub = S.make_stub()
    identity = S.identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7")
    run_hash = S.run_hash_of(identity)
    o["run_hash"] = run_hash
    o["run_hash_stable"] = S.run_hash_of(S.identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7"))
    o["run_hash_other"] = S.run_hash_of(S.identity_for(stub, "d0", cache_enabled=False, run_id="other"))
    o["cached_run_id"] = S.components_of(S.identity_for(stub, "d0"))["run_id"]
    o["cached_run_hash"] = S.run_hash_of(S.identity_for(stub, "d0"))

    # The defining module's on-disk source is read and AST-scanned by the judge
    # (from SUBMISSION_SRC), not trusted from this process. Record where curator
    # actually put compute_run_identity, for the judge's diagnostics.
    module = sys.modules[S.sym("compute_run_identity").__module__]
    o["defining_module"] = module.__name__
    try:
        o["defining_file"] = inspect.getsourcefile(module)
    except Exception:
        o["defining_file"] = None
    return o


PROBES = {
    "test_open::test_open_feature__a_versioned_run_identity_stamps_reconciles_and_is_recorded": probe_open,
    "test_r1::test_rule__the_key_is_exactly_twelve_components_and_the_parse_function_is_one_of_them": probe_r1_rule,
    "test_r1::test_scope__the_backend_component_is_the_resolved_name_not_the_declared_argument": probe_r1_scope,
    "test_r1::test_exclusions__only_four_backend_params_fork_the_cache_and_the_api_key_is_not_one": probe_r1_exclusions,
    "test_r1::test_observability__the_stated_component_table_holds_and_no_api_key_reaches_the_stamp": probe_r1_observability,
    "test_r2::test_rule__a_cache_disabled_run_is_identified_by_a_run_id_its_caller_supplies": probe_r2_rule,
    "test_r2::test_scope__the_call_mints_the_default_id_from_the_environment_and_passes_it_down": probe_r2_scope,
    "test_r2::test_failure_behavior__a_missing_id_and_an_unwanted_one_are_both_refused": probe_r2_failure_behavior,
    "test_r2::test_observability__the_nocache_run_hash_is_stable_and_the_module_reads_no_randomness": probe_r2_observability,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        mp = MonkeyPatch()
        try:
            results[node] = {"ok": True, "obs": fn(mp)}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False,
                             "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
        finally:
            mp.undo()
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
