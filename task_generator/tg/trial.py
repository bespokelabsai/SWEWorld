"""Launch the paid arms through the launcher that already gets auth right.

`harbor_tasks/_loop/run.sh` is not wrapped for convenience — it is wrapped
because it is the only thing on this machine that has been made to run a harbor
trial on the subscription. It reads `.env`, then *unsets* `ANTHROPIC_API_KEY` and
`ANTHROPIC_AUTH_TOKEN` and exports `CLAUDE_FORCE_OAUTH=1`, because harbor's
claude-code adapter reads the key from its own environment and the CLI prefers it
when both are set. It also refuses to start below a disk floor and above a trial
cap, both of which matter when a run is queued behind another one.

Reimplementing any of that here would mean a second place to get it wrong.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

from .model import REPO, Task

RUN_SH = REPO / "harbor_tasks" / "_loop" / "run.sh"
JOBS = REPO / "jobs"

ARMS = {"blind": "", "spec": "-spec", "clues": "-clues", "world": "-world"}


def variant_dir(task: Task, arm: str) -> str:
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm!r}; one of {', '.join(ARMS)}")
    return f"{task.slug}{ARMS[arm]}"


def launch(task: Task, arm: str, job: str | None = None,
           timeout_s: int = 7200) -> dict:
    variant = variant_dir(task, arm)
    path = REPO / "harbor_tasks" / task.group / variant
    if not (path / "task.toml").is_file():
        raise SystemExit(
            f"no harbor task at {path}. Emit it first:\n"
            f"  python3 {REPO}/task_generator/cli.py emit {task.slug}\n"
            f"  python3 {REPO}/task_generator/build_tasks.py "
            f"--extra-tasks {REPO}/task_generator/tasks.generated.json --pick {task.id}")

    name = job or f"{arm}-{task.id}-1"
    done = subprocess.run(["bash", str(RUN_SH), task.group, variant, name],
                          cwd=str(REPO), capture_output=True, text=True, timeout=timeout_s)
    return {"job": name, "rc": done.returncode,
            "stdout": done.stdout[-4000:], "stderr": done.stderr[-4000:],
            "log": f"/tmp/{name}.log"}


def rewards(job: str) -> dict:
    """The per-fact numbers harbor recorded, or an explanation of their absence."""
    result = JOBS / job / "result.json"
    if not result.is_file():
        return {"error": f"no {result}"}
    data = json.loads(result.read_text())
    evals = ((data.get("stats") or {}).get("evals") or {})
    for _, block in evals.items():
        metrics = block.get("metrics") or {}
        if metrics:
            return metrics
    return {"error": f"no metrics in {result}"}
