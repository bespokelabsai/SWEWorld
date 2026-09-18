"""g4 — the openly stated feature: a versioned run identity for the curator cache.

Everything asserted here is spelled out in the ticket: the new top-level
`run_identity` module and the names it exports, the exception family, the three
frozen dataclasses and their field orders, the `v3-<digest>` run hash over a
16-character xxh64 digest of a key-sorted payload, the six-key
`run_identity.json` stamp and its exact serialisation, the four reconciliation
statuses and the one raise, the moved `_get_function_hash`, the deleted
`_hash_fingerprint`, `LLM.backend` / `LLM.backend_params`, the `db.py` migration
and `store_metadata` status string, `CuratorResponse.run_identity` with the
`verify` keyword on `load` and its fingerprint/size/columns check, and the
`_is_cached_dataset` reset at the top of `BaseRequestProcessor.run`.

Nothing here touches a hidden fact. It never asserts WHICH components the digest
is computed from (r1: the twelve keys, the resolved backend, the four-key
`backend_params` allowlist) and it never asserts where a cache-disabled run's
identity comes from (r2: the injected `run_id`, the `nocache-` infix, the
refusals). The identities it builds are compared only against each other, and
every stub it hands to `compute_run_identity` carries the full LLM-shaped
surface so that an implementation reading any of it is served.

The answer-free helpers, stubs and scenario INPUTS live in `probe_support` so the
worker (`probe.py`) and this human reference share ONE definition and cannot
drift; the expected VALUES this test asserts stay inline here (and in
`judge.py`). `test_r1`/`test_r2` import the shared names from here, so they are
re-exported below.
"""
from __future__ import annotations

import dataclasses
import inspect
import json
import os
import sqlite3
from types import SimpleNamespace

import pytest

# Shared, answer-free names. Imported (not defined) here so there is a single
# definition; re-exported for test_r1/test_r2, which do `from test_open import ...`.
from probe_support import (  # noqa: F401
    IMPORT_ERROR,
    LATER,
    METADATA,
    NOW,
    OLD_RUNS_COLUMNS,
    Dataset,
    PromptFormatter,
    _Stop,
    components_of,
    identity_for,
    importable,
    make_old_db,
    make_stub,
    read_field,
    ri,
    run_hash_of,
    stamp_dict,
    surface,
    sym,
    write_stamp_file,
)


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
        # All three, not just the one a scenario mutates: the split judge reads
        # `frozen=True` off each declaration (judge.check_frozen_dataclasses).
        assert cls.__dataclass_params__.frozen, f"{cls.__name__} is not frozen"

    # -- the identity of a run ----------------------------------------------
    stub = make_stub()
    identity = identity_for(stub)
    digest = read_field(identity, "digest")
    assert isinstance(digest, str) and len(digest) == 16
    assert digest == digest.lower() and all(c in "0123456789abcdef" for c in digest), f"digest {digest!r} is not a lowercase hex xxh64"
    assert run_hash_of(identity) == f"v3-{digest}", "the cache directory name is the digest tagged with the identity version"
    # The split judge does not stop at the shape. `probe.capture_hashes` keeps
    # the bytes the module fed to xxh64 and `judge.check_digest_recomputed`
    # re-hashes them with `xxh64_ref` (XXH64 written out in the stdlib, because
    # the judge's interpreter has no xxhash), so the digest has to BE the xxh64
    # of a payload that carries this run's seeded inputs and names the identity
    # version. 16 lowercase hex characters cannot say any of that: a truncated
    # sha256 has the same shape, and an `xxh64` call the module never uses
    # satisfies any source check — the TB3 "Verifiable" finding on v7. (The
    # source scan is a diagnostic now for the converse reason: it reads call
    # sites, so a correct module holding xxh64 in a dict, on a class or in a
    # default argument reads as no call at all.) The half of that which holds
    # for every spelling of the payload is asserted here.
    # The judge is stricter about the tag than this line can be: it strikes every
    # component key and value out of the payload and requires what is left to
    # name the version, so a bespoke untagged rendering cannot pass on a digit
    # that happens to sit inside one of its own values.
    import xxhash
    untagged = json.dumps(components_of(identity), sort_keys=True, separators=(",", ":"))
    assert digest != xxhash.xxh64(untagged.encode("utf-8")).hexdigest(), \
        "the digest is taken over a version-tagged payload, not the bare components"
    assert read_field(identity, "identity_version") == 3
    assert read_field(identity, "cache_enabled") is True
    assert run_hash_of(identity_for(make_stub())) == run_hash_of(identity), "the same inputs must give the same run hash"
    assert run_hash_of(identity_for(stub, dataset_hash="other")) != run_hash_of(identity)
    with pytest.raises(dataclasses.FrozenInstanceError):
        identity.run_hash = "v3-0000000000000000"

    # Canonical means key-sorted: the same parameters in opposite insertion
    # orders are one run. (The split judge also reads the module for the hash it
    # reaches for — 16 hex characters is the shape of a truncated sha256 too.)
    gen = {"temperature": 0.7, "top_p": 0.3, "max_tokens": 16}
    params = {"base_url": "https://canon.example.test/v1", "batch_size": 8}
    def flip(d):
        return {key: d[key] for key in reversed(list(d))}
    as_given = identity_for(make_stub(generation_params=gen, backend_params=params))
    reordered = identity_for(make_stub(generation_params=flip(gen), backend_params=flip(params)))
    assert components_of(reordered) == components_of(as_given)
    assert read_field(reordered, "digest") == read_field(as_given, "digest"), \
        "insertion order must not move the digest"
    assert run_hash_of(reordered) == run_hash_of(as_given)

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
    with pytest.raises(dataclasses.FrozenInstanceError):
        stamp.run_hash = "v3-0000000000000000"

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
    with pytest.raises(dataclasses.FrozenInstanceError):
        check.status = "created"

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
    # than on `is`, so a one-line delegating re-export counts too. "Verbatim" is
    # not visible from behaviour at all: the split judge AST-compares the
    # definition in run_identity.py with the pristine one in
    # CURATOR_BASELINE_DIR/llm/llm.py (judge.check_moved_verbatim), which also
    # requires llm/llm.py to define it no longer — a copy left behind, dead or
    # live, is not a move, and that absence is not visible from behaviour either
    # because llm.py re-exports the name whichever way it got it.
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
    # "unexpected columns stay fatal" is all the ticket says: fatal, with no
    # class and no message named. The split judge grades exactly that (and
    # reports which exception it saw); asserting RuntimeError and "mismatch"
    # here was the TB3 "Test instruction alignment" finding on v9.
    with pytest.raises(Exception):
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

    # The size and the columns are checked too, and a dataset swap can never
    # reach them: no other dataset shares this one's fingerprint. So the
    # RECORDED block is edited and the response is loaded with the dataset it
    # was saved from.
    def recorded_as(**over):
        target = tmp_path / ("recorded-" + "-".join(sorted(over)))
        target.mkdir()
        CuratorResponse(dataset=ds, cache_dir=str(target), model_name="gpt-4o-mini", run_identity=saved).save(target)
        data = json.loads((target / "response.json").read_text())
        data["dataset"].update(over)
        (target / "response.json").write_text(json.dumps(data))
        with pytest.raises(ri.CachedResponseMismatch) as raised:
            CuratorResponse.load(target, ds)
        return raised.value

    bad_size = recorded_as(size=3)
    assert (bad_size.field, bad_size.expected, bad_size.found) == ("size", 3, 2)
    bad_columns = recorded_as(columns=["a", "b", "c"])
    assert (bad_columns.field, bad_columns.expected, bad_columns.found) == ("columns", ["a", "b", "c"], ["a", "b"])

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
    # Driven, not asserted: the ticket asks only for the flag to be cleared as
    # run()'s first statement (above). What a warm cache then does with it is
    # curator's existing behaviour, which this ticket neither states nor
    # changes, and the split judge reports it as a diagnostic instead of
    # grading it -- the other half of the v9 "Test instruction alignment"
    # finding.
    BaseRequestProcessor.run(warm, dataset=ds, working_dir=str(tmp_path), parse_func_hash="h", prompt_formatter=None)

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
