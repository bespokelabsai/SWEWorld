"""g4 — hidden requirement r2: where a cache-disabled run's identity comes from.

    rule              a cache-disabled run is identified by a run id its CALLER
                      supplies — `compute_run_identity`, `LLM._run_identity` and
                      `LLM.__call__` all take one — so replaying an id is
                      deterministic and lands in the same directory
    scope             the one place a default is minted is `LLM.__call__`, from
                      CURATOR_RUN_ID or a fresh uuid4 hex, and it is passed down;
                      a cached run carries no id
    failure_behavior  a cache-disabled run with no id, or an empty one, raises;
                      so does a cached run that is handed one
    observability     the `v3-nocache-` run hash, 27 characters, byte-equal on a
                      replay, and an AST scan proving the identity module reads no
                      source of randomness

`rule` and `observability` are separated by what they look at: `rule` compares
identities to each other and reads the components, `observability` asserts the
literal shape of the run hash and reads the module's own source. `scope` is the
only test that drives `LLM.__call__`; `failure_behavior` is the only one that
expects a raise.

This is the human reference, over the old fixed example inputs. The grader
(probe.py/judge.py) asserts the same facts over inputs re-drawn from a per-run
seed (`fixture_spec.derive`) — model, dataset hash, generation params, system
prompt, response model, functions, backend-knob values and combinations, run ids
and rows — and reads the stamps and cache directories the scenarios leave behind,
so a value captured from one run, or typed out of this file, fits no other.
Node names are neutral on purpose: the worker's jail carries them in probe.py.
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import sys
from pathlib import Path

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import read_field

from test_open import components_of, identity_for, importable, make_stub, run_hash_of, sym, _Stop


class Batchy(curator.LLM):
    """A real LLM built with no socket in reach; see test_r1.Batchy."""

    def prompt(self, input):
        return f"Describe {input['topic']}."


ROWS = [{"topic": "cats"}]


def stop(*args, **kwargs):
    """End `__call__` the moment the run directory has been decided."""
    raise _Stop()


def run_dirs(cache) -> list[str]:
    """The run directories under a cache root, ignoring metadata.db."""
    cache = Path(cache)
    if not cache.is_dir():
        return []
    return sorted(name for name in os.listdir(cache) if (cache / name).is_dir())


def stamped_run_id(cache, name):
    """The run id a run directory was stamped with.

    Read through the implementation's own `read_run_stamp` first, so a stamp
    that is spelled differently on disk still answers; the raw file is the
    fallback. This is what proves the id reached the identity, rather than the
    directory name, which would also depend on how the dataset is fingerprinted.
    """
    directory = Path(cache) / name
    stamp = sym("read_run_stamp")(directory)
    if stamp is not None:
        return dict(read_field(stamp, "components"))["run_id"]
    raw = directory / "run_identity.json"
    assert raw.is_file(), f"{name} carries no readable run identity stamp"
    return json.loads(raw.read_text())["components"]["run_id"]


# =============================================================================
# rule — the id is supplied by the caller, and it is what tells two runs apart
# =============================================================================
def test_rule__uncached_identity():
    importable()

    params = inspect.signature(sym("compute_run_identity")).parameters
    assert "run_id" in params, f"compute_run_identity takes {list(params)}"
    assert params["run_id"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["run_id"].default is None

    for name, func in (("LLM._run_identity", curator.LLM._run_identity), ("LLM.__call__", curator.LLM.__call__)):
        taken = inspect.signature(func).parameters
        assert "run_id" in taken, f"{name} takes {list(taken)}, so no caller can hand it a run id"
        assert taken["run_id"].kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        assert taken["run_id"].default is None

    stub = make_stub()
    identity = identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7")
    assert read_field(identity, "cache_enabled") is False
    assert components_of(identity)["run_id"] == "local-run-7", "the supplied id is what a cache-disabled run is identified by"

    # Replaying the id is deterministic: same id, same directory.
    assert run_hash_of(identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7")) == run_hash_of(identity)
    assert run_hash_of(identity_for(make_stub(), "d0", cache_enabled=False, run_id="local-run-7")) == run_hash_of(identity)
    # A different id is a different run ...
    assert run_hash_of(identity_for(stub, "d0", cache_enabled=False, run_id="local-run-8")) != run_hash_of(identity)
    # ... and so is the same id over different inputs.
    assert run_hash_of(identity_for(stub, "other", cache_enabled=False, run_id="local-run-7")) != run_hash_of(identity)


# =============================================================================
# scope — LLM.__call__ mints the default, from the environment or a fresh uuid
# =============================================================================
def test_scope__identity_sourcing(tmp_path, monkeypatch):
    importable()

    llm = Batchy(model_name="gpt-4o-mini", batch=True)
    monkeypatch.setattr(llm._request_processor, "run", stop, raising=False)
    rows = Dataset.from_list(ROWS)
    cache = tmp_path / "cc"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(cache))
    monkeypatch.delenv("CURATOR_DISABLE_CACHE", raising=False)
    monkeypatch.delenv("CURATOR_RUN_ID", raising=False)

    # A cached run carries no run id at all.
    with pytest.raises(_Stop):
        llm(rows)
    cached = run_dirs(cache)
    assert len(cached) == 1, f"one cached run made {cached}"
    assert stamped_run_id(cache, cached[0]) is None, "a cached run has no ephemeral id in its components"

    # With caching disabled, CURATOR_RUN_ID is what the run is identified by --
    # and the directory is the one the identity function says it is.
    monkeypatch.setenv("CURATOR_DISABLE_CACHE", "true")
    monkeypatch.setenv("CURATOR_RUN_ID", "ci-job-42")
    with pytest.raises(_Stop):
        llm(rows)
    with pytest.raises(_Stop):
        llm(rows)
    named = [name for name in run_dirs(cache) if name not in cached]
    assert len(named) == 1, f"two runs of CURATOR_RUN_ID=ci-job-42 must share one directory, made {named}"
    assert stamped_run_id(cache, named[0]) == "ci-job-42", "the environment's id is what the run is identified by"

    # An id handed to the call directly wins over the environment: it is a
    # parameter that travels, not something read from deep inside.
    known = set(run_dirs(cache))
    with pytest.raises(_Stop):
        llm(rows, run_id="explicit-7")
    given = [name for name in run_dirs(cache) if name not in known]
    assert len(given) == 1, f"llm(..., run_id='explicit-7') made {given}"
    assert stamped_run_id(cache, given[0]) == "explicit-7"

    # With nothing to go on, each run mints a fresh id of its own.
    monkeypatch.delenv("CURATOR_RUN_ID")
    known = set(run_dirs(cache))
    with pytest.raises(_Stop):
        llm(rows)
    with pytest.raises(_Stop):
        llm(rows)
    minted = [name for name in run_dirs(cache) if name not in known]
    assert len(minted) == 2, f"two unidentified runs must not share a directory, got {minted}"
    ids = [stamped_run_id(cache, name) for name in minted]
    assert len(set(ids)) == 2, f"both runs were minted the same id: {ids}"
    for value in ids:
        assert value not in (None, "", "ci-job-42", "explicit-7"), f"minted run id {value!r}"
        assert len(value) == 32 and all(c in "0123456789abcdef" for c in value), f"minted run id {value!r} is not a uuid4 hex"


# =============================================================================
# failure_behavior — the id and the cache setting must agree
# =============================================================================
def test_failure_behavior__refusals(tmp_path, monkeypatch):
    importable()

    error = sym("RunIdentityError")
    stub = make_stub()

    with pytest.raises(error):
        identity_for(stub, "d0", cache_enabled=False, run_id=None)
    with pytest.raises(error):
        identity_for(stub, "d0", cache_enabled=False)
    with pytest.raises(error):
        identity_for(stub, "d0", cache_enabled=False, run_id="")
    with pytest.raises(error):
        identity_for(stub, "d0", cache_enabled=True, run_id="x")

    # The last one is a refusal all the way up: a cached run handed a run id
    # neither ignores it nor folds it into the hash.
    llm = Batchy(model_name="gpt-4o-mini", batch=True)
    monkeypatch.setattr(llm._request_processor, "run", stop, raising=False)
    cache = tmp_path / "cc"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(cache))
    monkeypatch.delenv("CURATOR_DISABLE_CACHE", raising=False)
    rows = Dataset.from_list(ROWS)
    cached = run_hash_of(identity_for(llm, rows._fingerprint))
    with pytest.raises(error):
        llm(rows, run_id="x")
    assert run_dirs(cache) == [], f"a refused run must not leave a directory behind, found {run_dirs(cache)}"
    assert cached not in run_dirs(cache)


# =============================================================================
# observability — the nocache run hash, and a module that reads no randomness
# =============================================================================
def test_observability__uncached_hash_shape():
    importable()

    stub = make_stub()
    identity = identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7")
    run_hash = run_hash_of(identity)
    assert run_hash.startswith("v3-nocache-"), f"a cache-disabled run hash is greppable, got {run_hash!r}"
    assert len(run_hash) == 27, f"{run_hash!r} is {len(run_hash)} characters"
    assert run_hash == run_hash_of(identity_for(stub, "d0", cache_enabled=False, run_id="local-run-7"))
    assert run_hash != run_hash_of(identity_for(stub, "d0", cache_enabled=False, run_id="other"))
    assert components_of(identity_for(stub, "d0"))["run_id"] is None
    assert not run_hash_of(identity_for(stub, "d0")).startswith("v3-nocache-")

    # Nothing ephemeral is read inside the identity code: the module that
    # defines compute_run_identity imports no source of randomness. (Read off
    # the defining module rather than a path, so it holds wherever the
    # implementation put the file.)
    module = sys.modules[sym("compute_run_identity").__module__]
    source = Path(inspect.getsourcefile(module)).read_text()
    banned = {"random", "secrets", "uuid"}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, f"{module.__name__} imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, f"{module.__name__} imports from {node.module}"
        elif isinstance(node, ast.Attribute):
            assert node.attr != "urandom", f"{module.__name__} reads os.urandom"
        elif isinstance(node, ast.Name):
            assert node.id != "urandom", f"{module.__name__} reads urandom"
