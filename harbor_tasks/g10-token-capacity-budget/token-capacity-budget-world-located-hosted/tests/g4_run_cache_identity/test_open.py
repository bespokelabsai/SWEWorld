"""g4 — the openly stated feature: a versioned run identity for the curator cache.

Everything asserted here is spelled out in the ticket: the new top-level
`run_identity` module and the names it exports, the exception family, the three
frozen dataclasses and their field orders, the `v3-<digest>` run hash over a
16-character xxh64 digest, the six-key `run_identity.json` stamp and its exact
serialisation, the four reconciliation statuses and the one raise, the moved
`_get_function_hash`, the deleted `_hash_fingerprint`, `LLM.backend` /
`LLM.backend_params`, the `db.py` migration and `store_metadata` status string,
`CuratorResponse.run_identity` with the `verify` keyword on `load`, and the
`_is_cached_dataset` reset at the top of `BaseRequestProcessor.run`.

Nothing here touches a hidden fact. It never asserts WHICH components the digest
is computed from (r1: the twelve keys, the resolved backend, the four-key
`backend_params` allowlist) and it never asserts where a cache-disabled run's
identity comes from (r2: the injected `run_id`, the `nocache-` infix, the
refusals). The identities it builds are compared only against each other, and
every stub it hands to `compute_run_identity` carries the full LLM-shaped
surface so that an implementation reading any of it is served.
"""
from __future__ import annotations

import dataclasses
import inspect
import json
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from datasets import Dataset

from harness import read_field, surface

# Imported defensively and re-raised inside each test rather than at collection
# time: a missing `run_identity` module is one fact failing per requirement, not
# three files pytest refuses to collect and a scoreboard with no rows on it.
IMPORT_ERROR = None
try:
    from bespokelabs.curator import run_identity as ri
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    ri = None

try:
    from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
except Exception:  # pragma: no cover
    PromptFormatter = None


NOW = "2025-01-02T03:04:05"
LATER = "2025-01-02T04:00:00"


def importable() -> None:
    """Fail one test, not the whole module, when the new module is absent."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"bespokelabs.curator.run_identity could not be imported: {IMPORT_ERROR!r}")


# ---------------------------------------------------------------------------
# Finding the names, wherever the implementation chose to keep them
# ---------------------------------------------------------------------------
_CANDIDATE_MODULES = (
    "bespokelabs.curator.run_identity",
    "bespokelabs.curator",
    "bespokelabs.curator.llm.llm",
    "bespokelabs.curator.db",
    "bespokelabs.curator.types.curator_response",
)


def sym(name: str):
    """A name exported by the package, from whichever module holds it.

    The ticket puts the identity rule in `run_identity.py`, but a constant is
    graded on existing and on what it says, not on which file it was typed
    into, so every already-imported curator module is searched before giving up.
    """
    for mod_name in _CANDIDATE_MODULES:
        mod = sys.modules.get(mod_name)
        if mod is None:
            try:
                __import__(mod_name)
            except Exception:
                continue
            mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, name):
            return getattr(mod, name)
    for mod_name, mod in sorted(sys.modules.items()):
        if mod_name.startswith("bespokelabs.curator") and hasattr(mod, name):
            return getattr(mod, name)
    pytest.fail(f"the implementation exports no {name!r} anywhere in bespokelabs.curator")


# ---------------------------------------------------------------------------
# An LLM-shaped object, with no processor and no event loop behind it
# ---------------------------------------------------------------------------
_DEFAULT_BACKEND_PARAMS = {"base_url": "https://api.example.test/v1", "max_retries": 7, "api_key": "sk-secret"}


def make_stub(**over):
    """The stub the specification hands to `compute_run_identity`.

    A real `PromptFormatter` rather than a namespace, so an implementation that
    reads a method off it is served; `_request_processor` and `_backend_params`
    mirror `backend` / `backend_params` so an implementation that reaches for
    the private spelling gets the same answer as one that uses the property.
    """
    formatter_keys = ("model_name", "prompt_func", "parse_func", "response_format", "generation_params", "system_prompt")
    formatter_kwargs = {
        "model_name": "gpt-4o-mini",
        "prompt_func": None,
        "parse_func": None,
        "response_format": None,
        "generation_params": {"temperature": 0.7},
        "system_prompt": None,
    }
    for key in formatter_keys:
        if key in over:
            formatter_kwargs[key] = over.pop(key)
    backend = over.pop("backend", "openai")
    backend_params = over.pop("backend_params", None)
    if backend_params is None:
        backend_params = dict(_DEFAULT_BACKEND_PARAMS)
    formatter = PromptFormatter(**formatter_kwargs)
    stub = SimpleNamespace(
        prompt_formatter=formatter,
        batch_mode=over.pop("batch_mode", False),
        backend=backend,
        backend_params=dict(backend_params),
        return_completions_object=over.pop("return_completions_object", False),
        _backend_params=dict(backend_params),
        _request_processor=SimpleNamespace(backend=backend),
    )
    assert not over, f"make_stub got unexpected keyword(s) {sorted(over)}"
    return stub


def identity_for(stub, dataset_hash="9f1c8e2b7d4a6053", **kwargs):
    return ri.compute_run_identity(stub, dataset_hash, **kwargs)


def components_of(identity) -> dict:
    return dict(read_field(identity, "components"))


def run_hash_of(identity) -> str:
    return read_field(identity, "run_hash")


def stamp_dict(path) -> dict:
    return json.loads((Path(path) / "run_identity.json").read_text())


def write_stamp_file(path, payload) -> None:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / "run_identity.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


OLD_RUNS_COLUMNS = (
    "run_hash",
    "session_id",
    "dataset_hash",
    "prompt_func",
    "model_name",
    "response_format",
    "batch_mode",
    "created_time",
    "last_edited_time",
    "is_hosted_viewer_synced",
    "total_cost_milli_dollars",
    "total_requests",
    "total_prompt_tokens",
    "total_completion_tokens",
)


def make_old_db(path) -> None:
    """A `runs` table exactly as the world shipped it, with one row in it."""
    with sqlite3.connect(str(path)) as conn:
        conn.execute("CREATE TABLE runs (" + ", ".join(f"{name} TEXT" for name in OLD_RUNS_COLUMNS) + ")")
        conn.execute(
            "INSERT INTO runs (run_hash, session_id, prompt_func, model_name, created_time) VALUES (?, ?, ?, ?, ?)",
            ("old", "s0", "def p(): pass", "gpt-4o-mini", NOW),
        )
        conn.commit()


METADATA = {
    "run_hash": "r1",
    "session_id": "s1",
    "dataset_hash": "d",
    "prompt_func": "def p(): pass",
    "parse_func": "def q(): pass",
    "model_name": "gpt-4o-mini",
    "response_format": "text",
    "batch_mode": False,
    "timestamp": NOW,
    "is_hosted_viewer_synced": False,
    "identity_version": 3,
}


class _Stop(Exception):
    """A sentinel that ends a call the moment the thing under test has happened."""


# =============================================================================
# the openly stated feature
# =============================================================================
def test_open_feature__a_versioned_run_identity_stamps_reconciles_and_is_recorded(tmp_path):
    importable()

    # -- the module surface -------------------------------------------------
    assert ri.RUN_IDENTITY_VERSION == 3
    assert ri.RUN_IDENTITY_FILENAME == "run_identity.json"
    for name in ("RunIdentity", "RunStamp", "RunDirectoryCheck", "RunIdentityError", "RunIdentityMismatch",
                 "CachedResponseMismatch", "compute_run_identity", "write_run_stamp", "read_run_stamp",
                 "reconcile_run_directory", "_get_function_hash"):
        assert hasattr(ri, name), f"run_identity exports no {name!r}; it has {surface(ri)}"

    # -- the exception family -----------------------------------------------
    assert issubclass(ri.RunIdentityError, RuntimeError)
    assert issubclass(ri.RunIdentityMismatch, ri.RunIdentityError)
    assert issubclass(ri.CachedResponseMismatch, ri.RunIdentityError)
    mismatch = ri.RunIdentityMismatch("cache-dir-c", "v3-a", "v3-b", ("model_name",))
    assert (mismatch.path, mismatch.expected_run_hash, mismatch.found_run_hash, mismatch.mismatched_components) == (
        "cache-dir-c", "v3-a", "v3-b", ("model_name",))
    stale = ri.CachedResponseMismatch("cache-dir-c", "fingerprint", "aaa", "bbb")
    assert (stale.cache_dir, stale.field, stale.expected, stale.found) == ("cache-dir-c", "fingerprint", "aaa", "bbb")

    # -- three frozen dataclasses, with the field orders the ticket gives ----
    for cls, fields in (
        (ri.RunIdentity, ["run_hash", "digest", "identity_version", "cache_enabled", "components"]),
        (ri.RunStamp, ["identity_version", "run_hash", "digest", "components", "created_at", "updated_at"]),
        (ri.RunDirectoryCheck, ["status", "stamp", "previous_version"]),
    ):
        assert dataclasses.is_dataclass(cls), f"{cls.__name__} is not a dataclass"
        assert [f.name for f in dataclasses.fields(cls)] == fields

    # -- the identity of a run ----------------------------------------------
    stub = make_stub()
    identity = identity_for(stub)
    digest = read_field(identity, "digest")
    assert isinstance(digest, str) and len(digest) == 16
    assert digest == digest.lower() and all(c in "0123456789abcdef" for c in digest), f"digest {digest!r} is not a lowercase hex xxh64"
    assert run_hash_of(identity) == f"v3-{digest}", "the cache directory name is the digest tagged with the identity version"
    assert read_field(identity, "identity_version") == 3
    assert read_field(identity, "cache_enabled") is True
    assert run_hash_of(identity_for(make_stub())) == run_hash_of(identity), "the same inputs must give the same run hash"
    assert run_hash_of(identity_for(stub, dataset_hash="other")) != run_hash_of(identity)
    with pytest.raises(dataclasses.FrozenInstanceError):
        identity.run_hash = "v3-0000000000000000"

    # -- the stamp file ------------------------------------------------------
    home = tmp_path / "created" / "nested"
    stamp = ri.write_run_stamp(home, identity, now=NOW)
    written = (home / "run_identity.json").read_text()
    payload = json.loads(written)
    assert sorted(payload) == ["components", "created_at", "digest", "identity_version", "run_hash", "updated_at"]
    assert payload["identity_version"] == 3
    assert payload["run_hash"] == run_hash_of(identity)
    assert payload["digest"] == digest
    assert payload["components"] == components_of(identity)
    assert payload["created_at"] == NOW and payload["updated_at"] == NOW
    assert written == json.dumps(payload, indent=2, sort_keys=True) + "\n", "the stamp is indent=2, sort_keys=True, with one trailing newline"
    assert read_field(stamp, "created_at") == NOW

    again = ri.write_run_stamp(home, identity, now=LATER, created_at=NOW)
    assert (read_field(again, "created_at"), read_field(again, "updated_at")) == (NOW, LATER)
    assert (stamp_dict(home)["created_at"], stamp_dict(home)["updated_at"]) == (NOW, LATER)

    round_tripped = type(stamp).from_dict(stamp.to_dict())
    assert round_tripped.to_dict() == stamp.to_dict()

    # -- reading a stamp back ------------------------------------------------
    assert read_field(ri.read_run_stamp(home), "run_hash") == run_hash_of(identity)
    assert ri.read_run_stamp(tmp_path / "nothing-here") is None, "an absent stamp reads as None"
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "run_identity.json").write_text("{not json")
    assert ri.read_run_stamp(broken) is None, "an unparseable stamp reads as None, it does not raise"
    partial = tmp_path / "partial"
    partial.mkdir()
    (partial / "run_identity.json").write_text(json.dumps({"run_hash": run_hash_of(identity)}))
    assert ri.read_run_stamp(partial) is None, "an incomplete stamp reads as None"

    # -- reconciling a directory: created / adopted / upgraded / matched -----
    fresh = tmp_path / "a"
    check = ri.reconcile_run_directory(fresh, identity, now=NOW)
    assert read_field(check, "status") == "created"
    assert read_field(check, "previous_version") is None
    assert os.listdir(fresh) == ["run_identity.json"]

    legacy = tmp_path / "b"
    legacy.mkdir()
    (legacy / "payload.txt").write_text("someone else's bytes")
    check = ri.reconcile_run_directory(legacy, identity, now=NOW)
    assert read_field(check, "status") == "adopted", "a pre-v3 directory is adopted, not refused and not wiped"
    assert read_field(check, "previous_version") is None
    assert sorted(os.listdir(legacy)) == ["payload.txt", "run_identity.json"]
    assert (legacy / "payload.txt").read_text() == "someone else's bytes"

    older = tmp_path / "c"
    write_stamp_file(older, {
        "identity_version": 2,
        "run_hash": "v2-2917e0582eb73e61",
        "digest": "2917e0582eb73e61",
        "components": {"whatever": "v2 said"},
        "created_at": "2024-06-01T00:00:00",
        "updated_at": "2024-06-01T00:00:00",
    })
    check = ri.reconcile_run_directory(older, identity, now=NOW)
    assert read_field(check, "status") == "upgraded"
    assert read_field(check, "previous_version") == 2
    assert stamp_dict(older)["identity_version"] == 3
    assert stamp_dict(older)["created_at"] == "2024-06-01T00:00:00", "an upgrade keeps the directory's creation time"
    assert stamp_dict(older)["updated_at"] == NOW

    check = ri.reconcile_run_directory(older, identity, now=LATER)
    assert read_field(check, "status") == "matched"
    assert read_field(check, "previous_version") == 3
    assert stamp_dict(older)["created_at"] == "2024-06-01T00:00:00"
    assert stamp_dict(older)["updated_at"] == LATER

    # -- reconciling a directory that belongs to someone else ---------------
    newer = tmp_path / "d"
    write_stamp_file(newer, {
        "identity_version": 4,
        "run_hash": "v4-2917e0582eb73e61",
        "digest": "2917e0582eb73e61",
        "components": components_of(identity),
        "created_at": NOW,
        "updated_at": NOW,
    })
    with pytest.raises(ri.RunIdentityMismatch) as exc:
        ri.reconcile_run_directory(newer, identity, now=LATER)
    assert exc.value.mismatched_components == ("identity_version",)
    assert stamp_dict(newer)["identity_version"] == 4, "a newer stamp is left exactly as it was found"

    foreign_components = dict(components_of(identity))
    foreign_components["model_name"] = "some-other-model"
    foreign = tmp_path / "e"
    (foreign_dir := foreign).mkdir()
    (foreign_dir / "payload.txt").write_text("the other run's files")
    write_stamp_file(foreign, {
        "identity_version": 3,
        "run_hash": "v3-ffffffffffffffff",
        "digest": "ffffffffffffffff",
        "components": foreign_components,
        "created_at": NOW,
        "updated_at": NOW,
    })
    with pytest.raises(ri.RunIdentityMismatch) as exc:
        ri.reconcile_run_directory(foreign, identity, now=LATER)
    assert exc.value.found_run_hash == "v3-ffffffffffffffff"
    assert exc.value.expected_run_hash == run_hash_of(identity)
    assert exc.value.mismatched_components == ("model_name",)
    assert sorted(os.listdir(foreign)) == ["payload.txt", "run_identity.json"], "a mismatch deletes nothing"
    assert stamp_dict(foreign)["run_hash"] == "v3-ffffffffffffffff"

    # -- what llm.py keeps, moves and loses ---------------------------------
    from bespokelabs.curator import LLM
    import bespokelabs.curator.llm.llm as llm_module

    # The function moved and is re-exported; graded on what it answers rather
    # than on `is`, so a one-line delegating re-export counts too.
    assert ri._get_function_hash(None) == "ef46db3751d8e999", "the moved function is the same function, byte for byte"
    assert llm_module._get_function_hash(None) == ri._get_function_hash(None)
    assert llm_module._get_function_hash(make_stub) == ri._get_function_hash(make_stub)
    assert not hasattr(LLM, "_hash_fingerprint"), "_hash_fingerprint is replaced by the run identity, not kept beside it"
    for name in ("backend", "backend_params"):
        attribute = inspect.getattr_static(LLM, name)
        assert attribute is not None and not inspect.isfunction(attribute), f"LLM.{name} is a property, not a method: {attribute!r}"

    # -- db.py: a migration instead of a refusal ----------------------------
    from bespokelabs.curator.db import MetadataDB

    columns = sym("RUNS_COLUMNS")
    names = [row[0] if isinstance(row, (tuple, list)) else row for row in columns]
    assert "parse_func" in names and "identity_version" in names, f"RUNS_COLUMNS is missing the new columns: {names}"

    db_path = tmp_path / "cache" / "metadata.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    make_old_db(db_path)
    db = MetadataDB(str(db_path))
    added = db.validate_schema()
    assert set(added) == {"parse_func", "identity_version"}, f"validate_schema reported {added!r}"
    live = [col[1] for col in db._get_current_schema()]
    assert "parse_func" in live and "identity_version" in live
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("SELECT parse_func, identity_version, session_id, created_time FROM runs WHERE run_hash='old'").fetchone()
    assert row == (None, None, "s0", NOW), "an existing row survives the migration with NULLs in the new columns"
    assert tuple(db.validate_schema()) == (), "a second validation adds nothing"

    hostile = tmp_path / "hostile.db"
    with sqlite3.connect(str(hostile)) as conn:
        conn.execute("CREATE TABLE runs (wrong_col TEXT)")
        conn.commit()
    with pytest.raises(RuntimeError, match="mismatch"):
        MetadataDB(str(hostile)).validate_schema()

    # -- db.py: store_metadata writes the parse function and says what it did
    fresh_db = MetadataDB(str(tmp_path / "cache2" / "metadata.db"))
    assert fresh_db.store_metadata(dict(METADATA)) == "inserted"
    with sqlite3.connect(fresh_db.db_path) as conn:
        row = conn.execute(
            "SELECT parse_func, identity_version, created_time, last_edited_time, session_id, total_cost_milli_dollars FROM runs WHERE run_hash='r1'"
        ).fetchone()
    assert row == ("def q(): pass", 3, NOW, NOW, "s1", None)

    assert fresh_db.store_metadata({**METADATA, "session_id": None, "timestamp": LATER}) == "updated"
    with sqlite3.connect(fresh_db.db_path) as conn:
        row = conn.execute("SELECT session_id, created_time, last_edited_time FROM runs WHERE run_hash='r1'").fetchone()
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert row == ("s1", NOW, LATER), "a None session id leaves the recorded one alone"
    assert count == 1
    assert fresh_db.store_metadata({**METADATA, "session_id": "s2", "timestamp": LATER}) == "updated"
    with sqlite3.connect(fresh_db.db_path) as conn:
        assert conn.execute("SELECT session_id FROM runs WHERE run_hash='r1'").fetchone() == ("s2",)

    # -- curator_response: the identity travels, and load checks the dataset -
    from bespokelabs.curator.types.curator_response import CuratorResponse

    assert [f.name for f in dataclasses.fields(CuratorResponse)][-1] == "run_identity", "run_identity is declared last"
    assert dataclasses.fields(CuratorResponse)[-1].default is None

    ds = Dataset.from_list([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    other = Dataset.from_list([{"a": 9, "b": "z"}, {"a": 8, "b": "w"}])
    cache_dir = tmp_path / "run"
    cache_dir.mkdir()
    saved = stamp.to_dict()
    response = CuratorResponse(dataset=ds, cache_dir=str(cache_dir), model_name="gpt-4o-mini", run_identity=saved)
    assert response.to_dict()["run_identity"] == saved
    response.save(cache_dir)
    on_disk = json.loads((cache_dir / "response.json").read_text())
    assert on_disk["run_identity"]["run_hash"] == run_hash_of(identity)

    assert CuratorResponse.load(cache_dir, ds).run_identity == saved
    with pytest.raises(ri.CachedResponseMismatch) as exc:
        CuratorResponse.load(cache_dir, other)
    assert exc.value.field == "fingerprint"
    assert exc.value.expected == ds._fingerprint
    assert exc.value.found == other._fingerprint
    assert len(CuratorResponse.load(cache_dir, other, verify=False).dataset) == 2, "verify=False takes the dataset it is handed"

    legacy_response = json.loads((cache_dir / "response.json").read_text())
    legacy_response.pop("dataset")
    legacy_response.pop("run_identity")
    (cache_dir / "response.json").write_text(json.dumps(legacy_response))
    loaded = CuratorResponse.load(cache_dir, other)
    assert loaded.run_identity is None, "a response written before run identities still loads"

    # -- the cached-dataset flag describes this run, not the last one -------
    from bespokelabs.curator.request_processor.base_request_processor import BaseRequestProcessor

    def stop(*args, **kwargs):
        raise _Stop()

    stale = SimpleNamespace(
        _is_cached_dataset=True,
        attempt_loading_cached_dataset=lambda parse_func_hash: None,
        config=SimpleNamespace(model="m"),
        prompt_formatter=None,
        validate_config=stop,
    )
    with pytest.raises(_Stop):
        BaseRequestProcessor.run(stale, dataset=ds, working_dir=str(tmp_path), parse_func_hash="h", prompt_formatter=None)
    assert stale._is_cached_dataset is False, "run() must clear the flag before it consults the cache"

    warm = SimpleNamespace(
        _is_cached_dataset=False,
        attempt_loading_cached_dataset=lambda parse_func_hash: ds,
        config=SimpleNamespace(model="m"),
        prompt_formatter=None,
        validate_config=stop,
    )
    assert BaseRequestProcessor.run(warm, dataset=ds, working_dir=str(tmp_path), parse_func_hash="h", prompt_formatter=None) is ds
    assert warm._is_cached_dataset is True

    # -- an identity error out of the cache is not a warning ----------------
    def raise_mismatch(cache_dir, dataset, **kwargs):
        raise ri.CachedResponseMismatch("cache-dir-c", "fingerprint", "a", "b")

    def raise_missing(cache_dir, dataset, **kwargs):
        raise FileNotFoundError("response.json")

    holder = SimpleNamespace()
    original = CuratorResponse.load
    try:
        CuratorResponse.load = raise_mismatch
        with pytest.raises(ri.CachedResponseMismatch):
            LLM._get_cached_response(holder, "cache-dir-c", ds)
        CuratorResponse.load = raise_missing
        assert LLM._get_cached_response(holder, "cache-dir-c", ds) is None, "anything that is not an identity error is still swallowed"
    finally:
        CuratorResponse.load = original
