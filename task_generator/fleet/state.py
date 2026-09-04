"""The run's state, on disk, written after every step.

The precedent is `harbor_tasks/_loop/state.json`: one file that says where each
task is, what it has cost and what it last found, so a person who walks away can
read the run rather than reconstruct it from logs. The difference is that this
one is written by the driver rather than by hand.

Two properties it has to have and one it deliberately does not:

  atomic     tmp-file plus `os.replace`, because `status` is read by a second
             process while the fleet is mid-write and a half-written state.json
             reads as a crashed run.
  additive   every step appends to `history` and nothing is ever rewritten, so
             "what did the judge decide and why" survives a resume. `_loop`'s
             history is the model for this and it is the only reason g1's four
             days are reconstructable at all.

  NOT the source of truth for artifacts. `out/<slug>/` is. State records what
  the fleet did; whether `bracket.json` says the task ships is answered by
  reading `bracket.json`. A driver that caches a gate's verdict in its own state
  file will eventually act on a verdict the artifact no longer supports -- which
  is the shape of every "a check with no reader" entry in tasks/lessons.md.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import threading

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "runs"

# One re-entrant lock around the whole read-modify-write, not just the write.
# A plain write lock is not enough and the difference is measurable: five threads
# each doing load -> mutate -> save lost one task's `status` field in a smoke run,
# because each thread saved a snapshot taken before the others' changes. History
# rows survived only because `record` happened to reload immediately beforehand.
# The fields at risk are the ones that matter most -- a lost `hosted[arm].task_id`
# is a pushed Horizon task whose uuid nothing on this box records any more.
_lock = threading.RLock()


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_dir(run_id: str) -> pathlib.Path:
    return RUNS / run_id


def path(run_id: str) -> pathlib.Path:
    return run_dir(run_id) / "state.json"


def notes_path(run_id: str) -> pathlib.Path:
    return run_dir(run_id) / "notes.md"


def log_path(run_id: str, slug: str, step: str, attempt: int) -> pathlib.Path:
    out = run_dir(run_id) / slug
    out.mkdir(parents=True, exist_ok=True)
    return out / f"{step.replace(' ', '_')}.{attempt}.log"


def load(run_id: str) -> dict:
    return json.loads(path(run_id).read_text())


def _write(state: dict) -> None:
    target = path(state["run_id"])
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=1))
    os.replace(tmp, target)


def save(state: dict) -> None:
    """Write a state object the caller already holds. Only `new()` should use
    this; everything else goes through `update`, which cannot lose a field."""
    with _lock:
        _write(state)


def update(run_id: str, mutate):
    """Load, apply `mutate` in place, write back — under a thread AND file lock.

    The only safe way to change the run. `mutate` may return a value, which is
    passed back, so a read-and-increment (the attempt counter) is one call
    rather than a load and a save with a gap between them.

    The `flock` is not redundant with the threading lock. A `resume` launched
    while the original orchestrator is still alive gives one run TWO processes,
    and a threading lock protects nothing across them -- it happened here, and
    the fields at risk are the ones a rerun cannot reconstruct.
    """
    import fcntl
    lockfile = run_dir(run_id) / ".state.lock"
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    with _lock, open(lockfile, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            state = json.loads(path(run_id).read_text())
            result = mutate(state)
            _write(state)
            return result
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def latest() -> str | None:
    """The newest run id, for `status`/`resume` with no argument."""
    runs = [d for d in RUNS.glob("*") if (d / "state.json").is_file()]
    if not runs:
        return None
    return max(runs, key=lambda d: (d / "state.json").stat().st_mtime).name


def new(run_id: str, *, through: str, budget_usd: float, tasks: list[dict]) -> dict:
    state = {
        "run_id": run_id,
        "started": now(),
        "through": through,
        "budget_usd": budget_usd,
        "tasks": {t["slug"]: {
            "id": t["id"],
            "slug": t["slug"],
            "brief": t["brief"],
            "phase": "A",
            "step": None,
            "status": "pending",
            "attempts": {},
            "history": [],
            "blocked": None,
            "hosted": {},
        } for t in tasks},
    }
    notes_path(run_id).parent.mkdir(parents=True, exist_ok=True)
    if not notes_path(run_id).is_file():
        notes_path(run_id).write_text(
            "# Notes fed back into every judge call\n\n"
            "Appended by `orchestrate.py note \"...\"`. Re-read before each\n"
            "decision, so a lesson learned mid-run reaches the tasks still\n"
            "running without restarting anything.\n")
    save(state)
    return state


def record(run_id: str, slug: str, entry: dict) -> None:
    """Append one step outcome and persist. `entry` is free-form but always
    carries `step`, `rc` and `at`; a judge call adds `verdict`/`action`/`reason`."""
    entry = {"at": now(), **entry}
    update(run_id, lambda st: st["tasks"][slug]["history"].append(entry))


def spend(slug_dir: pathlib.Path) -> float:
    """What this task has actually cost, out of its own spend.json.

    Read from the artifact rather than accumulated in state, because the paid
    stages are subprocesses whose cost the fleet never sees -- `tg/steps.py`
    appends the row, and that file is the ledger both halves already agree on.
    """
    ledger = slug_dir / "spend.json"
    if not ledger.is_file():
        return 0.0
    try:
        return sum(float(r.get("cost_usd") or 0) for r in json.loads(ledger.read_text()))
    except (json.JSONDecodeError, TypeError):
        return 0.0
