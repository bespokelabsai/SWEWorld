"""g4 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

This module holds ONLY the curator imports, the stub builder, the builders that
turn `fixture_spec` recipes into real functions and response models, and the
tolerant readers the probe needs to drive curator. It contains NO expected
value. That is load-bearing: `run_split` copies this file into the worker's
jail, so it is inside the process that runs agent code, and anything answer-like
here is something a forged observations file can copy. In particular the
component key set, the backend-param allowlist, the `_get_function_hash(None)`
digest, the cache-disabled run-hash shape, the run-id environment variable, the
stamp file's NAME and every stamp/row value the judge grades live only in
`judge.py` (and, for humans, in `test_open.py`/`test_r*.py`), which the worker
cannot read: /tests is root-only for a split suite and the jail holds only
`probe.py`, `probe_support.py`, `fixture_spec.py` and `harness.py`.

Where a scenario has to USE one of those answers — read a stamp by name, set the
run-id variable, pass a run id to a call — it is discovered from the submission
(`stamp_name`, and the discovery in probe.py), never written here; the judge
checks what was discovered.

`NOW`, `LATER` and `METADATA` are the open feature's inputs (weight 0); the
hidden facts draw theirs from `fixture_spec.derive(seed)` through `set_spec`.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from datasets import Dataset  # noqa: F401 - re-exported for test_open/the probe
from pydantic import BaseModel, create_model

from harness import read_field, surface  # noqa: F401 - re-exported for test_open/test_r*

# Imported defensively and re-raised inside each test/probe rather than at import
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


# ---- the open feature's inputs ----------------------------------------------
NOW = "2025-01-02T03:04:05"
LATER = "2025-01-02T04:00:00"

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

METADATA = {
    "run_hash": "r1",
    "session_id": "s1",
    "dataset_hash": "d",
    "prompt_func": "def p(): pass",
    "parse_func": "def q(): pass",
    "model_name": "gpt-4o-mini",
    "response_format": "structured",
    "batch_mode": False,
    "timestamp": NOW,
    "is_hosted_viewer_synced": False,
    "identity_version": 3,
}

# The run's derived inputs. Empty until `set_spec`; the human reference never
# sets it and gets the plain defaults below.
SPEC: dict = {}


def set_spec(spec: dict) -> None:
    SPEC.clear()
    SPEC.update(spec)
    _BUILT.clear()


class _Stop(Exception):
    """A sentinel that ends a call the moment the thing under test has happened."""


# ---------------------------------------------------------------------------
# Guards and name lookup
# ---------------------------------------------------------------------------
def importable() -> None:
    """Fail one test, not the whole module, when the new module is absent."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"bespokelabs.curator.run_identity could not be imported: {IMPORT_ERROR!r}")


_CANDIDATE_MODULES = (
    "bespokelabs.curator.run_identity",
    "bespokelabs.curator",
    "bespokelabs.curator.llm.llm",
    "bespokelabs.curator.db",
    "bespokelabs.curator.types.curator_response",
)

_RAISE = object()


def sym(name: str, default=_RAISE):
    """A name exported by the package, from whichever module holds it.

    The ticket puts the identity rule in `run_identity.py`, but a constant is
    graded on existing and on what it says, not on which file it was typed
    into, so every already-imported curator module is searched before giving up.
    With a `default`, a missing name is that default rather than a failure: the
    probe reports None and the judge — which owns the name — decides, so a
    missing constant fails only the fact that names it.
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
    if default is not _RAISE:
        return default
    pytest.fail(f"the implementation exports no {name!r} anywhere in bespokelabs.curator")


def stamp_name():
    """The stamp file's name as the submission spells it, or None.

    Discovered, never defaulted: the name is graded by the judge, and a default
    here would put it in the worker's jail.
    """
    name = getattr(ri, "RUN_IDENTITY_FILENAME", None) if ri is not None else None
    return name if isinstance(name, str) and name and os.path.basename(name) == name else None


# ---------------------------------------------------------------------------
# Building the recipes fixture_spec draws
# ---------------------------------------------------------------------------
_BUILT: dict = {}


def function_from(recipe: dict):
    """A module-level function built from a recipe's name and body text.

    Registered on this module under its drawn name, so a pickler that pickles a
    function by reference finds it and one that pickles by value sees the drawn
    body; either way its `_get_function_hash` moves with the seed.
    """
    key = ("fn", recipe["name"])
    if key not in _BUILT:
        source = f"def {recipe['name']}({recipe['args']}):\n    return {recipe['body']!r} + str(row)\n"
        namespace: dict = {"__name__": __name__}
        exec(compile(source, __file__, "exec"), namespace)  # noqa: S102 - the recipe is ours
        fn = namespace[recipe["name"]]
        fn.__module__ = __name__
        globals()[recipe["name"]] = fn
        _BUILT[key] = fn
    return _BUILT[key]


_TYPES = {"str": str, "int": int, "float": float, "bool": bool}


def model_from(recipe: dict):
    """A pydantic response model built from a recipe's class name and fields."""
    key = ("model", recipe["name"])
    if key not in _BUILT:
        fields = {name: (_TYPES[kind], ...) for name, kind in recipe["fields"]}
        model = create_model(recipe["name"], __base__=BaseModel, **fields)
        _BUILT[key] = model
    return _BUILT[key]


def resolve(value):
    """A scenario override with its recipe tokens replaced by the built objects."""
    if value == "@prompt":
        return function_from(SPEC["prompt_fn"])
    if value == "@parse":
        return function_from(SPEC["parse_fn"])
    if value == "@model":
        return model_from(SPEC["response_model"])
    return value


# ---------------------------------------------------------------------------
# An LLM-shaped object, with no processor and no event loop behind it
# ---------------------------------------------------------------------------
def make_stub(**over):
    """The stub the specification hands to `compute_run_identity`.

    A real `PromptFormatter` rather than a namespace, so an implementation that
    reads a method off it is served; `_request_processor` and `_backend_params`
    mirror `backend` / `backend_params` so an implementation that reaches for
    the private spelling gets the same answer as one that uses the property.
    Defaults are the run's drawn inputs once `set_spec` has run.
    """
    formatter_keys = ("model_name", "prompt_func", "parse_func", "response_format", "generation_params", "system_prompt")
    formatter_kwargs = {
        "model_name": SPEC.get("model", "gpt-4o-mini"),
        "prompt_func": None,
        "parse_func": None,
        "response_format": None,
        "generation_params": dict(SPEC.get("generation_params", {"temperature": 0.7})),
        "system_prompt": None,
    }
    for key in formatter_keys:
        if key in over:
            formatter_kwargs[key] = resolve(over.pop(key))
    backend = over.pop("backend", "openai")
    backend_params = over.pop("backend_params", None)
    if backend_params is None:
        backend_params = {}
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


def identity_for(stub, dataset_hash=None, **kwargs):
    if dataset_hash is None:
        dataset_hash = SPEC.get("dataset_hash", "0f0f0f0f")
    return ri.compute_run_identity(stub, dataset_hash, **kwargs)


def components_of(identity) -> dict:
    return dict(read_field(identity, "components"))


def run_hash_of(identity) -> str:
    return read_field(identity, "run_hash")


def stamp_dict(path, name=None) -> dict:
    return json.loads((Path(path) / (name or stamp_name())).read_text())


def write_stamp_file(path, payload, name=None) -> None:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / (name or stamp_name())).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def make_old_db(path) -> None:
    """A `runs` table exactly as the world shipped it, with one row in it."""
    with sqlite3.connect(str(path)) as conn:
        conn.execute("CREATE TABLE runs (" + ", ".join(f"{name} TEXT" for name in OLD_RUNS_COLUMNS) + ")")
        conn.execute(
            "INSERT INTO runs (run_hash, session_id, prompt_func, model_name, created_time) VALUES (?, ?, ?, ?, ?)",
            ("old", "s0", "def p(): pass", "gpt-4o-mini", NOW),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# A real LLM built with no socket in reach
# ---------------------------------------------------------------------------
def _batchy():
    """Build `Batchy` lazily so a broken curator import fails per test, not here.

    `batch=True` because the online OpenAI processor probes the provider for
    rate-limit headers as it is constructed; the batch processor does not, so
    an instance builds with no socket anywhere in reach.
    """
    from bespokelabs import curator

    class Batchy(curator.LLM):
        def prompt(self, input):
            return f"Describe {input['topic']}."

    return Batchy


def batchy(**kwargs):
    return _batchy()(**kwargs)


def newtmp() -> Path:
    """A fresh empty working directory, standing in for the `tmp_path` fixture."""
    return Path(tempfile.mkdtemp(prefix="g4-"))
