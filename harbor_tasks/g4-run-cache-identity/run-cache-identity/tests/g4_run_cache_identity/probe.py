"""g4 worker: the ONLY process that imports the submission.

Runs as `nobody`, from a root-staged jail that holds this file,
`probe_support.py`, `fixture_spec.py` and `harness.py` and nothing else. For
each graded test it drives curator and writes what happened — never a pass/fail
— to the observations file named on argv. `judge.py`, which never imports the
submission and which this process cannot read (test.sh keeps /tests root-only
for a split suite), turns those values and the directories the scenarios left
behind into the verdict.

WHAT THE SPLIT ALONE DID NOT BUY. Separating the processes stopped the worker
rewriting the verdict; it did not stop the worker inventing the values the
verdict is computed from. The old g4 fixture never changed — one dataset hash,
one run id, one api key, one base URL — so its run hashes never changed
either, a capture of one correct run replayed onto a tree that implemented
nothing passed every hidden fact, and r2.failure_behavior was graded almost
entirely on exception names this process reported. So:

  * **the inputs are re-drawn every run** from the seed root chose
    (`fixture_spec.derive`): the model, dataset hash, generation params, system
    prompt, response model, prompt and parse functions, every backend knob's
    value, which knobs are combined, every run id and the rows. The judge
    checks the components an identity carries against THOSE inputs;
  * **what a run leaves on disk is read by the judge.** The stamp
    `write_run_stamp` wrote, the cache directories `LLM.__call__` created and
    the stamps inside them all sit under the artifacts root, one directory per
    scenario, and root opens them itself;
  * **no answer is carried here.** Not the component keys, not the allowlist,
    not the stamp file's name, not the run-id parameter or environment
    variable, not the shape of a cache-disabled run hash. Identities are
    recorded WHOLE, so this file never names a component; where a scenario has
    to USE an answer — pass a run id, set the variable a default id comes from —
    it is discovered from the submission (`run_id_param`, `run_id_env`) and the
    judge decides whether what was discovered is right. A submission that
    hardcodes a constant instead of exporting it is still measured on every
    fact that does not name the constant (tasks/lessons.md, 2026-09-14, "a probe
    reaching for an attribute is a dependency between facts").

The `tmp_path` fixtures of the reference tests are `probe_support.newtmp()` (for
the open feature) or a directory under the artifacts root (for anything the
judge reads); `monkeypatch` is the `MonkeyPatch` shim below, undone between
probes so one probe's patched env or attribute cannot leak into the next.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import os
import re
import sqlite3
import sys
import traceback

# Bound BEFORE the submission is imported, and called instead of returning from
# main(): interpreter shutdown runs `atexit` hooks the submission registered at
# import. One door, not the fix — what makes a forged value worthless is that it
# is not knowable in advance.
_EXIT = os._exit

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

import fixture_spec  # noqa: E402 - the run's inputs; stdlib only, no answers

_MISSING = object()


class MonkeyPatch:
    """The slice of pytest's monkeypatch the g4 scenarios use, with undo."""

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


# probe_support owns the curator imports and the answer-free stubs; importing it
# runs the submission's `import bespokelabs.curator` — this process's whole
# purpose, and why it is disposable.
import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402

SPEC: dict = {}
ARTIFACTS = "/nonexistent"


def scenario_dir(*parts: str) -> str:
    """A directory for one scenario, where the judge will look for it."""
    path = os.path.join(ARTIFACTS, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def jsonable(value):
    try:
        return json.loads(json.dumps(value))
    except (TypeError, ValueError):
        if isinstance(value, (tuple, list, set, frozenset)):
            return [jsonable(v) for v in value]
        if isinstance(value, dict):
            return {str(k): jsonable(v) for k, v in value.items()}
        return repr(value)


# Attributes carried by the run-identity exception family; recorded whenever an
# exception is caught so the judge can check the ones the test asserted.
_EXC_ATTRS = ("path", "expected_run_hash", "found_run_hash", "mismatched_components",
              "cache_dir", "field", "expected", "found")


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain and the identity
    exception attributes it carries — the faithful stand-in for `pytest.raises`."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__], "str": str(exc)[:500]}
        for attr in _EXC_ATTRS:
            if hasattr(exc, attr):
                info[attr] = jsonable(getattr(exc, attr))
        return info
    return {"raised": False, "mro": []}


def attempt(fn, *args, **kwargs) -> dict:
    """{"value": ...} or {"error": ...}: one step's evidence, never the node's death."""
    try:
        return {"value": jsonable(fn(*args, **kwargs))}
    except BaseException as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"[:500]}


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


def record(identity) -> dict:
    """An identity, whole: the judge picks out what each fact grades."""
    return {
        "run_hash": jsonable(read_field(identity, "run_hash", default=None)),
        "digest": jsonable(read_field(identity, "digest", default=None)),
        "cache_enabled": jsonable(read_field(identity, "cache_enabled", default=None)),
        "components": jsonable(dict(read_field(identity, "components"))),
    }


def ident(over: dict, dataset_hash: str, **kwargs) -> dict:
    """The identity of a stub built from `over`, as a recorded attempt."""
    def run():
        return record(S.identity_for(S.make_stub(**dict(over)), dataset_hash, **kwargs))
    return attempt(run)


# ---------------------------------------------------------------------------
# discovery: the names a scenario has to USE, taken from the submission
# ---------------------------------------------------------------------------
_DISCOVERED: dict = {}

# The first two positional parameters and the one keyword the ticket states.
_STATED = {"llm", "dataset_hash", "cache_enabled"}


def signature_of(fn) -> list:
    """[[name, kind, default]] for every parameter, or an error string."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"
    out = []
    for p in params.values():
        default = "<<absent>>" if p.default is inspect.Parameter.empty else jsonable(p.default)
        out.append([p.name, p.kind.name, default])
    return out


def run_id_param():
    """The keyword `compute_run_identity` takes a caller's run id by, or None.

    Not a default to the name r2 grades: every parameter beyond the stated ones
    is tried with a drawn id on a cache-disabled identity, and the one whose
    value reaches the components is it. The judge checks the name.
    """
    if "param" in _DISCOVERED:
        return _DISCOVERED["param"]
    found = None
    fn = S.sym("compute_run_identity", None)
    try:
        params = list(inspect.signature(fn).parameters.values())[2:] if callable(fn) else []
    except (TypeError, ValueError):
        params = []
    marker = SPEC["id_probe"]
    for p in params:
        if p.name in _STATED or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        try:
            identity = fn(S.make_stub(), SPEC["dataset_hash"], cache_enabled=False, **{p.name: marker})
            if marker in json.dumps(jsonable(dict(read_field(identity, "components")))):
                found = p.name
                break
        except BaseException:  # noqa: BLE001 - a candidate that raises is not the one
            continue
    _DISCOVERED["param"] = found
    return found


def _string_literals(root: str) -> set:
    found = set()
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            try:
                tree = ast.parse(open(os.path.join(dirpath, fname), errors="replace").read())
            except (OSError, SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    found.add(node.value)
    return found


def _json_mentions(root: str, needle: str) -> bool:
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if fname.endswith(".json"):
                try:
                    if needle in open(os.path.join(dirpath, fname), errors="replace").read():
                        return True
                except OSError:
                    continue
    return False


def run_id_env(llm, rows, mp):
    """The environment variable a cache-disabled call takes its default id from, or None.

    Every CURATOR_* string the submission's source spells, that this process has
    not set itself, is set in turn to a drawn id for one cache-disabled call; the
    variable whose value is stamped into the run directory is it. The judge
    checks the name. Runs in a scratch cache the judge never reads.
    """
    if "env" in _DISCOVERED:
        return _DISCOVERED["env"]
    from bespokelabs import curator
    root = os.path.dirname(os.path.abspath(curator.__file__))
    controlled = {"CURATOR_CACHE_DIR", "CURATOR_DISABLE_CACHE"}
    candidates = sorted(s for s in _string_literals(root)
                        if re.fullmatch(r"CURATOR_[A-Z0-9_]+", s)
                        and s not in controlled and s not in os.environ)
    found = None
    marker = SPEC["id_probe"]
    for i, name in enumerate(candidates):
        trial = MonkeyPatch()
        cache = str(S.newtmp())
        try:
            trial.setenv("CURATOR_CACHE_DIR", cache)
            trial.setenv("CURATOR_DISABLE_CACHE", "true")
            trial.setenv(name, marker)
            try:
                llm(rows)
            except BaseException:  # noqa: BLE001 - the sentinel, or a refusal; the directory decides
                pass
            if _json_mentions(cache, marker):
                found = name
                break
        finally:
            trial.undo()
    _DISCOVERED["env"] = found
    _DISCOVERED["env_candidates"] = candidates
    return found


def a_call_llm(mp):
    """A real LLM whose processor is replaced by the stop sentinel."""
    llm = S.batchy(model_name=SPEC["call_model"], backend="openai", batch=True)
    mp.setattr(llm._request_processor, "run", _stop, raising=False)
    return llm


# ===========================================================================
# the openly stated feature (weight 0)
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
    o["stamp_written"] = (home / S.stamp_name()).read_text()
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
    (broken / S.stamp_name()).write_text("{not json")
    o["read_broken"] = ri.read_run_stamp(broken) is None
    partial = tmp / "partial"
    partial.mkdir()
    (partial / S.stamp_name()).write_text(json.dumps({"run_hash": S.run_hash_of(identity)}))
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
    o["keys"] = jsonable(S.sym("IDENTITY_COMPONENT_KEYS", None))

    # The worker's own reference for each recipe the variants use: what the
    # submission's `_get_function_hash` says of the drawn functions (and of no
    # function), and the compact sorted schema of the drawn response model.
    fh = S.sym("_get_function_hash", None)
    o["fh"] = {
        "@prompt": attempt(fh, S.function_from(SPEC["prompt_fn"])) if callable(fh) else None,
        "@parse": attempt(fh, S.function_from(SPEC["parse_fn"])) if callable(fh) else None,
        "none": attempt(fh, None) if callable(fh) else None,
    }
    o["model_schema"] = attempt(lambda: json.dumps(S.model_from(SPEC["response_model"]).model_json_schema(),
                                                   sort_keys=True, separators=(",", ":")))
    o["variants"] = {label: ident(over, dh) for label, over, dh in fixture_spec.component_variants(SPEC)}
    return o


def probe_r1_scope(mp) -> dict:
    S.importable()
    o: dict = {}
    dh = SPEC["dataset_hash"]
    auto = S.batchy(model_name=SPEC["known_model"], batch=True)                  # backend= is None here
    declared = S.batchy(model_name=SPEC["known_model"], backend="openai", batch=True)
    o["auto_backend"] = attempt(lambda: auto.backend)
    o["declared_backend"] = attempt(lambda: declared.backend)
    o["auto_identity"] = attempt(lambda: record(S.identity_for(auto, dh)))
    o["declared_identity"] = attempt(lambda: record(S.identity_for(declared, dh)))
    o["stub_identity"] = ident({"backend": SPEC["stub_backend"]}, dh)

    o["auto_params"] = attempt(lambda: auto.backend_params)
    configured = S.batchy(model_name=SPEC["known_model"], batch=True, backend_params=dict(SPEC["llm_params"]))
    o["configured_params"] = attempt(lambda: configured.backend_params)

    def mutate():
        handed_out = configured.backend_params
        for key in list(handed_out):
            handed_out[key] = handed_out[key] + 1 if isinstance(handed_out[key], int) else None
        key, value = SPEC["mutation"]
        handed_out[key] = value
        return configured.backend_params
    o["after_mutation"] = attempt(mutate)
    return o


def probe_r1_exclusions(mp) -> dict:
    S.importable()
    o: dict = {}
    allowed = S.sym("IDENTITY_BACKEND_PARAM_KEYS", None)
    o["allowlist"] = sorted(allowed) if isinstance(allowed, (set, frozenset, list, tuple)) else jsonable(allowed)

    dh = SPEC["dataset_hash"]
    scenarios = {label: ident({"backend_params": params}, dh)
                 for label, params in fixture_spec.knob_scenarios(SPEC)}
    o["scenarios"] = scenarios

    # The knobs this build treats as noise, all at once. Chosen from what the
    # single-knob scenarios above observed, never from a stored partition; the
    # judge checks the choice against its own before trusting the result.
    base = (scenarios["plain"].get("value") or {}).get("run_hash")
    noise = [k for k in SPEC["knob_order"]
             if base is not None and (scenarios[f"knob:{k}"].get("value") or {}).get("run_hash") == base]
    o["noise_keys"] = noise
    plain = {"base_url": SPEC["plain_url"]}
    o["noise"] = ident({"backend_params": {**plain, **{k: SPEC["knob_values"][k] for k in noise}}}, dh)
    return o


def probe_r1_observability(mp) -> dict:
    S.importable()
    o: dict = {}
    dh = SPEC["dataset_hash"]
    params = SPEC["stamp_params"]
    identity = S.identity_for(S.make_stub(backend_params=dict(params)), dh)
    o["identity"] = attempt(record, identity)

    # The stamp goes where the judge reads it; the judge opens the bytes itself.
    write_run_stamp = S.sym("write_run_stamp", None)
    run_dir = os.path.join(scenario_dir("r1_obs"), "run")
    o["stamp_write"] = (attempt(lambda: write_run_stamp(run_dir, identity, now=SPEC["stamp_now"]) and None)
                        if callable(write_run_stamp) else None)

    o["rotated"] = ident({"backend_params": dict(SPEC["rotated_params"])}, dh)
    o["changed"] = [ident({"backend_params": dict(params), **over}, dh)
                    for over in fixture_spec.changed_stamp_stubs(SPEC)]

    auto = S.batchy(model_name=SPEC["known_model"], batch=True)
    declared = S.batchy(model_name=SPEC["known_model"], backend="openai", batch=True)
    o["auto"] = attempt(lambda: record(S.identity_for(auto, dh)))
    o["declared"] = attempt(lambda: record(S.identity_for(declared, dh)))
    return o


# ===========================================================================
# r2 — where a cache-disabled run's identity comes from
# ===========================================================================
def probe_r2_rule(mp) -> dict:
    S.importable()
    from bespokelabs import curator
    o: dict = {}
    o["signatures"] = {
        "compute_run_identity": signature_of(S.sym("compute_run_identity", None)),
        "_run_identity": signature_of(getattr(curator.LLM, "_run_identity", None)),
        "__call__": signature_of(curator.LLM.__call__),
    }
    name = run_id_param()
    o["param"] = name
    if name is None:
        return o
    dh = SPEC["dataset_hash"]
    rid = SPEC["id_rule"]
    stub = S.make_stub()
    o["base"] = attempt(lambda: record(S.identity_for(stub, dh, cache_enabled=False, **{name: rid})))
    o["replay_same_stub"] = attempt(lambda: record(S.identity_for(stub, dh, cache_enabled=False, **{name: rid})))
    o["replay_new_stub"] = ident({}, dh, cache_enabled=False, **{name: rid})
    o["other_id"] = attempt(lambda: record(S.identity_for(stub, dh, cache_enabled=False,
                                                          **{name: SPEC["id_rule_other"]})))
    o["other_inputs"] = attempt(lambda: record(S.identity_for(stub, SPEC["alt_dataset_hash"],
                                                              cache_enabled=False, **{name: rid})))
    return o


def probe_r2_scope(mp) -> dict:
    S.importable()
    o: dict = {}
    llm = a_call_llm(mp)
    rows = S.Dataset.from_list(SPEC["rows"])
    mp.delenv("CURATOR_DISABLE_CACHE", raising=False)

    env = run_id_env(llm, rows, mp)
    param = run_id_param()
    o["env"] = env
    o["param"] = param

    def phase(label, disable, env_value, calls, **kwargs):
        step = MonkeyPatch()
        try:
            step.setenv("CURATOR_CACHE_DIR", scenario_dir("r2_scope", label))
            if disable:
                step.setenv("CURATOR_DISABLE_CACHE", "true")
            else:
                step.delenv("CURATOR_DISABLE_CACHE")
            if env is not None:
                if env_value is None:
                    step.delenv(env)
                else:
                    step.setenv(env, env_value)
            o[label] = [raises(llm, rows, **kwargs) for _ in range(calls)]
        finally:
            step.undo()

    phase("cached", False, None, 1)
    if env is not None:
        phase("from_env", True, SPEC["id_env"], 2)
    if param is not None:
        phase("explicit", True, SPEC["id_env"], 1, **{param: SPEC["id_explicit"]})
    phase("minted", True, None, 2)
    return o


def probe_r2_failure_behavior(mp) -> dict:
    S.importable()
    o: dict = {}
    dh = SPEC["dataset_hash"]
    stub = S.make_stub()
    param = run_id_param()
    o["param"] = param
    o["missing_absent"] = raises(S.identity_for, stub, dh, cache_enabled=False)
    if param is not None:
        o["missing_none"] = raises(S.identity_for, stub, dh, cache_enabled=False, **{param: None})
        o["missing_empty"] = raises(S.identity_for, stub, dh, cache_enabled=False, **{param: ""})
        o["cached_with_id"] = raises(S.identity_for, stub, dh, cache_enabled=True, **{param: SPEC["id_refused"]})

    # A cached call handed an id is refused all the way up, before a directory
    # exists; then a legitimate cache-disabled call into the SAME cache root
    # proves the root was live. The judge reads the root afterwards.
    llm = a_call_llm(mp)
    rows = S.Dataset.from_list(SPEC["rows"])
    mp.setenv("CURATOR_CACHE_DIR", scenario_dir("r2_fail", "cc"))
    mp.delenv("CURATOR_DISABLE_CACHE", raising=False)
    if param is not None:
        o["call_with_id"] = raises(llm, rows, **{param: SPEC["id_refused"]})
    mp.setenv("CURATOR_DISABLE_CACHE", "true")
    kwargs = {param: SPEC["id_control"]} if param is not None else {}
    o["control"] = raises(llm, rows, **kwargs)
    return o


def probe_r2_observability(mp) -> dict:
    S.importable()
    o: dict = {}
    name = run_id_param()
    o["param"] = name
    if name is not None:
        dh = SPEC["dataset_hash"]
        o["uncached"] = ident({}, dh, cache_enabled=False, **{name: SPEC["id_obs"]})
        o["uncached_again"] = ident({}, dh, cache_enabled=False, **{name: SPEC["id_obs"]})
        o["uncached_other"] = ident({}, dh, cache_enabled=False, **{name: SPEC["id_obs_other"]})
        o["cached"] = ident({}, dh)

    # The defining module's on-disk source is read and AST-scanned by the judge
    # (from SUBMISSION_SRC), not trusted from this process. Record where curator
    # actually put compute_run_identity, for the judge's diagnostics.
    fn = S.sym("compute_run_identity", None)
    o["defining_module"] = getattr(fn, "__module__", None)
    return o


PROBES = {
    "test_open::test_open_feature__a_versioned_run_identity_stamps_reconciles_and_is_recorded": probe_open,
    "test_r1::test_rule__component_set": probe_r1_rule,
    "test_r1::test_scope__backend_resolution": probe_r1_scope,
    "test_r1::test_exclusions__backend_param_filter": probe_r1_exclusions,
    "test_r1::test_observability__stamp_contents": probe_r1_observability,
    "test_r2::test_rule__uncached_identity": probe_r2_rule,
    "test_r2::test_scope__identity_sourcing": probe_r2_scope,
    "test_r2::test_failure_behavior__refusals": probe_r2_failure_behavior,
    "test_r2::test_observability__uncached_hash_shape": probe_r2_observability,
}


def main(out_path: str, seed: str, artifacts: str) -> int:
    global SPEC, ARTIFACTS
    SPEC = fixture_spec.derive(seed)
    ARTIFACTS = artifacts
    S.set_spec(SPEC)

    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        mp = MonkeyPatch()
        try:
            results[node] = {"ok": True, "obs": fn(mp)}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:1000],
                             "trace": traceback.format_exc()[-2000:]}
        finally:
            mp.undo()
    results["discovery"] = {"ok": True, "obs": jsonable(_DISCOVERED)}
    with open(out_path, "w") as fh:
        json.dump(results, fh, default=repr)
    return 0


if __name__ == "__main__":
    code = main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.stdout.flush()
    sys.stderr.flush()
    _EXIT(code)
