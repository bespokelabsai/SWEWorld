"""g4 — answer-free scenario helpers/inputs shared by the worker (probe.py) and
the human reference (test_open.py).

This module holds ONLY the curator imports, the stubs, the scenario INPUTS and
the tolerant readers the probe needs to drive curator; it contains NO
expected-output value. That is load-bearing: `run_split` copies this file into
the worker's jail, so it is inside the process that runs agent code. If any
reward-bearing expected value ever appeared here, the worker could read it and
forge a passing `observations.json`. In particular the twelve-key component
list, the four-key backend-params allowlist and WHICH backend knobs fork the
cache (the r1 partition), the `_get_function_hash(None)` digest, the migration
column set, the store_metadata row values, and the exact stamp serialisation
live only in `judge.py` (and, for humans, in `test_open.py`), which the worker
cannot read.

`CANDIDATE_BACKEND_PARAMS` is deliberately a FLAT, UNLABELLED list: it names the
backend knobs the exclusions test varies, but nothing here says which of them
fork the cache. The probe records, per knob, what curator actually did; the
judge alone holds the identity/non-identity split, so a worker reading this file
still cannot forge the per-knob verdicts without implementing the rule.

`NOW`, `LATER`, `METADATA`, `_DEFAULT_BACKEND_PARAMS`, `ROWS` and the values in
`CANDIDATE_BACKEND_PARAMS` are INPUTS: the strings the fixtures feed into
curator. They must be the literals the reference uses or the scenarios do not
reproduce; the judge holds its own copies for the equality checks it grades, so
a worker reading them here gains nothing it does not still have to make curator
actually produce.

`test_open.py` imports these names so there is a single definition of each helper
— the probe cannot drift from the reference.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from datasets import Dataset  # noqa: F401 - re-exported for test_open/the probe
from pydantic import BaseModel

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


# ---- inputs the fixtures feed ---------------------------------------------
NOW = "2025-01-02T03:04:05"
LATER = "2025-01-02T04:00:00"

_DEFAULT_BACKEND_PARAMS = {"base_url": "https://api.example.test/v1", "max_retries": 7, "api_key": "sk-secret"}

ROWS = [{"topic": "cats"}]

# The backend knobs the exclusions test varies, one flat list with NO hint of
# which fork the cache. Values match the reference so the scenarios reproduce
# exactly; the identity/non-identity partition is the judge's secret.
CANDIDATE_BACKEND_PARAMS = [
    ("max_retries", 99),
    ("azure_deployment", "deployment-b"),
    ("request_timeout", 30),
    ("base_url", "https://y/v1"),
    ("require_all_responses", False),
    ("batch_size", 7),
    ("batch_check_interval", 11),
    ("completion_window", "48h"),
    ("seconds_to_pause_on_rate_limit", 5),
    ("max_requests_per_minute", 4242),
    ("delete_successful_batch_files", True),
    ("api_key", "sk-rotated"),
]

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
    "response_format": "text",
    "batch_mode": False,
    "timestamp": NOW,
    "is_hosted_viewer_synced": False,
    "identity_version": 3,
}


def prompt_one(row):
    return f"one: {row}"


def parse_two(row, response):
    return {"two": response}


class Answer(BaseModel):
    text: str
    score: int


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
# A real LLM built with no socket in reach (used by r1/r2 scope scenarios)
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


# ---------------------------------------------------------------------------
# Reading the cache directories a run leaves behind (r2 scope/failure)
# ---------------------------------------------------------------------------
def run_dirs(cache) -> list:
    """The run directories under a cache root, ignoring metadata.db."""
    import os

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


def newtmp() -> Path:
    """A fresh empty working directory, standing in for the `tmp_path` fixture."""
    return Path(tempfile.mkdtemp(prefix="g4-"))
