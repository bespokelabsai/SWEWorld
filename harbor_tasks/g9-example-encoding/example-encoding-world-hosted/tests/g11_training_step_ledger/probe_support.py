"""g11 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

Holds ONLY the curator imports, scenario inputs and driver helpers the probe
needs; NO expected-output value. This file is copied into the worker's jail (the
process that runs agent code), so an expected value here would be readable by a
forging worker. In particular the dataset-signature ANSWER (`SIGNATURE`) and the
expected per-batch losses (`BATCH_LOSSES`) are NOT here — they live only in
`judge.py` (and, for humans, in `test_open.py`). Where the probe needs the
signature as a construction input it calls `signature()`, which computes it live
from the submission and therefore holds no answer.

`test_open.py` imports these names so there is a single definition of each helper.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

# Imported defensively and re-raised inside the probe/test rather than at import
# time: a missing `step_ledger` module is one fact failing per requirement, not a
# module that refuses to load at all.
IMPORT_ERROR = None
try:
    from bespokelabs.curator.finetune import step_ledger as sl
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    sl = None

from bespokelabs.curator.finetune.config import FireworksTrainerConfig, TinkerTrainerConfig
from bespokelabs.curator.finetune.trainer import FireworksTrainer, TinkerTrainer
from bespokelabs.curator.finetune.types import CheckpointInfo, TrainingResult, TrainingStats


# ---------------------------------------------------------------------------
# Finding the names, wherever the implementation chose to keep them
# ---------------------------------------------------------------------------
_CANDIDATE_MODULES = (
    "bespokelabs.curator.finetune.step_ledger",
    "bespokelabs.curator.finetune",
    "bespokelabs.curator.finetune.types",
    "bespokelabs.curator.finetune.config",
    "bespokelabs.curator.finetune.trainer.tinker_trainer",
    "bespokelabs.curator.finetune.trainer.fireworks_trainer",
)


def sym(name: str):
    """A name exported by the finetune package, from whichever module holds it.

    The ticket puts the ledger in `step_ledger.py`, but a constant or a helper is
    graded on existing and on what it says, not on which file it was typed into.
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
    pytest.fail(f"the implementation exports no {name!r} anywhere in bespokelabs.curator.finetune")


def ledger():
    """Fail one test, not the whole module, when the new module is absent."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"bespokelabs.curator.finetune.step_ledger could not be imported: {IMPORT_ERROR!r}")
    return sl


def has_ledger() -> bool:
    return IMPORT_ERROR is None


# ---------------------------------------------------------------------------
# The end-to-end inputs the ticket names
# ---------------------------------------------------------------------------
DATA = [
    {"messages": [{"role": "user", "content": f"Q{i}"}, {"role": "assistant", "content": f"A{i}"}]}
    for i in range(10)
]


def signature():
    """The dataset signature the SUBMISSION computes for DATA — never a literal.

    Answer-free: it calls the graded code (`dataset_signature`), so it holds no
    expected value. Used only where the probe needs a signature as a CONSTRUCTION
    input (e.g. building a resume checkpoint); the correctness of the signature is
    still decided by the judge against its own copy.
    """
    return sym("dataset_signature")(DATA)


def e2e_config(**overrides):
    """The end-to-end configuration: 10 examples, 4 batches an epoch, 3 optimizer steps."""
    kwargs = dict(
        base_model="Qwen3-8B",
        epochs=2,
        batch_size=3,
        gradient_accumulation_steps=3,
        warmup_steps=2,
        log_every_n_steps=2,
        checkpoint_every_n_steps=2,
        checkpoint_every_epoch=True,
        save_weights_on_complete=False,
        seed=0,
        api_key=None,
    )
    kwargs.update(overrides)
    return TinkerTrainerConfig(**kwargs)


class FakeClock:
    """A clock that hands back the values it was given and counts the asking."""

    def __init__(self, values):
        self.values = list(values)
        self.calls = 0

    def __call__(self) -> float:
        if self.calls >= len(self.values):
            raise AssertionError(f"the clock was called {self.calls + 1} times; only {len(self.values)} values were provided")
        value = self.values[self.calls]
        self.calls += 1
        return value


def clock_for(*values) -> FakeClock:
    """A clock with slack past the expected calls, so an extra call fails on a number."""
    return FakeClock(list(values) + [9.0e9] * 8)


def record_stats(monkeypatch):
    """Capture every `TrainingStats` the run pushes, wherever the tracker is built.

    Patched in every finetune module that holds the name, with one shared
    recorder between them, so "one per batch" still means one in total whichever
    module the trainer reached for.
    """
    recorder = SimpleNamespace(stats=[], init_kwargs={}, init_args=(), built=0)

    class Tracker:
        def __init__(self, *args, **kwargs):
            recorder.built += 1
            recorder.init_args = args
            recorder.init_kwargs = kwargs

        def update(self, stats=None, *args, **kwargs):
            recorder.stats.append(stats)

        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    patched = 0
    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith("bespokelabs.curator.finetune") and hasattr(mod, "FinetuneStatusTracker"):
            monkeypatch.setattr(mod, "FinetuneStatusTracker", Tracker, raising=False)
            patched += 1
    assert patched, "no finetune module exposes FinetuneStatusTracker to patch"
    return recorder


def tracker_total_steps(recorder):
    """The denominator the tracker was built with, however it was passed."""
    if "total_steps" in recorder.init_kwargs:
        return recorder.init_kwargs["total_steps"]
    if len(recorder.init_args) >= 3:          # model, total_epochs, total_steps, batch_size
        return recorder.init_args[2]
    raise AssertionError(f"the status tracker was built with no total_steps: {recorder.init_args} {recorder.init_kwargs}")


def mock_env(monkeypatch):
    """No provider key anywhere: every trainer runs its mock branch."""
    monkeypatch.delenv("TINKER_API_KEY", raising=False)
    monkeypatch.delenv("FIREWORKS_API_KEY", raising=False)
