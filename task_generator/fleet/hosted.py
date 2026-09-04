"""The `horizon` CLI, wrapped. Everything here is typed by hand today.

`grep -r horizon` over the repo finds no script and no make target: every push,
validation and evaluation that produced g1 through g6 was typed at a prompt and
recorded afterwards in `tasks/todo.md`. This module is that, automated, and it
is the part of the fleet with the least existing code to lean on -- so every
edge `tasks/lessons.md` records is handled explicitly and named where it is
handled.

The rule that governs the whole file, from that file: **"a command that exits 0
here has told you nothing about whether it worked. Read the artifact."** Not one
function below returns on an exit code. `push` is confirmed by reading
`.horizon/metadata.json`, `validate` by `.validation/*/result.json`, `evaluate`
by `status --json`, and the arms' numbers by the rollout files themselves.

The binary is not on PATH -- it lives in its own virtualenv at
`~/horizon_env/bin` -- and `HORIZON_API_KEY` comes out of the repo's `.env`.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
HORIZON_BIN = pathlib.Path.home() / "horizon_env" / "bin"

# Hard-coded because there is no way to look them up: `horizon tasks list` is
# broken (`Error fetching tasks: 0`) and nothing lists mini-batches at all. The
# `.horizon/metadata.json` files under harbor_tasks/ and out/*/horizon/ are the
# only record on this box that these two ids mean these two projects.
MINI_BATCH_APEX = "b52ead5c-6e16-4552-ab96-250541fdfba2"      # project nidhi-test
MINI_BATCH_WORLD = "fde8a4a1-21d7-4f76-b153-6cfe480b82ff"     # project sweworld (phase D)

# A new task is gated to cipher-omni until 10+ rollouts land below a 0.4 pass
# rate; `--model biggie-max` returns 403 Forbidden before that. `meteor` is the
# agent type that binds -- `cascade` failed all 20 of g1's rollouts with no task
# binding at all, which reads in the results as twenty agent failures.
MODEL = "cipher-omni"
AGENT_TYPE = "meteor"

# Evaluation is two-stage, and it has to be.
#
# A new task is restricted to `cipher-omni` until 10+ rollouts have landed, so
# the first submission is not a measurement -- it is the toll for reaching the
# model that can produce one. `biggie-max` returns 403 Forbidden before it.
#
# And the toll cannot double as the verdict. On g6, one task and one version,
# biggie-max scored the spec arm 1.00 while cipher-omni scored the same arm
# 0.514 over ten rollouts. A spec ceiling read off the gating model would fail
# every good task in the repo, g6 included.
GATING_RUNS = 10                 # per arm; what clears the model gate
# ONE run on the expensive model, not three.
#
# The verdict model is near-deterministic where it matters: biggie-max scored
# g6's spec arm 1.00 on a single rollout, and the question the spec arm answers
# -- "are these requirements sufficient at all" -- is answered by one success.
# Variance is the weak model's problem (cipher-omni ranged 0.00-1.00 on that
# same arm), and the gating stage already buys ten samples of it.
#
# Measured: three biggie-max rollouts on one arm cost ~$19. At this stage of the
# project that is most of a task's whole hosted budget for a number the first
# rollout already gives.
VERDICT_RUNS = 1                 # per arm; what the verdict is actually read on
VERDICT_MODEL = "biggie-max"

# The agent type is per MODEL, not one constant. `meteor` is what binds for
# cipher-omni; the biggie-max evaluations that have actually graded on this
# account ran `typhoon`. (`cascade` binds to nothing at all -- it failed all 20
# of g1's rollouts with no task binding, which reads as twenty agent failures.)
AGENT_TYPES = {"cipher-omni": "meteor", "biggie-max": "typhoon"}


def agent_type_for(model: str) -> str:
    return AGENT_TYPES.get(model, AGENT_TYPE)


class HostedError(RuntimeError):
    """Something Horizon did that the fleet will not paper over."""


def env() -> dict:
    """The child environment: the venv on PATH, and the key out of `.env`.

    `.env` is parsed rather than sourced so that nothing else in it -- and it
    holds ANTHROPIC_API_KEY -- leaks into a child by accident.
    """
    out = dict(os.environ)
    out["PATH"] = f"{HORIZON_BIN}:{out.get('PATH', '')}"
    dotenv = REPO / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text().splitlines():
            if line.startswith("HORIZON_API_KEY="):
                out["HORIZON_API_KEY"] = line.split("=", 1)[1].strip().strip('"')
    out["MINI_BATCH_ID"] = MINI_BATCH_APEX
    out.pop("ANTHROPIC_API_KEY", None)
    out.pop("ANTHROPIC_AUTH_TOKEN", None)
    return out


def run(args: list[str], *, cwd: pathlib.Path, stdin: str = "",
        timeout_s: int = 3600) -> subprocess.CompletedProcess:
    """One horizon invocation. The caller reads the artifact, not the result."""
    return subprocess.run([str(HORIZON_BIN / "horizon"), *args], cwd=str(cwd),
                          env=env(), input=stdin, capture_output=True, text=True,
                          timeout=timeout_s)


# --------------------------------------------------------------------------- auth

def whoami() -> dict:
    """Who the key belongs to, and what budget is left.

    Called before every submit, because an exhausted account budget produces
    rollouts that error with zero spend and zero requests -- indistinguishable
    from a broken task. g6 lost a day to `total_spend $1040.18, budget $0.00`
    read as a task defect. (It prints the API key in plaintext; never log the
    raw stdout of this one.)
    """
    done = run(["whoami", "--json"], cwd=REPO)
    try:
        return json.loads(done.stdout)
    except json.JSONDecodeError:
        raise HostedError(f"horizon whoami returned no JSON: {done.stdout[:300]}{done.stderr[:300]}")


def affordable(minimum_usd: float = 20.0) -> tuple[bool, str]:
    """Is there enough Horizon budget left to submit?

    `budget` is what REMAINS, not an allowance to subtract `total_spend` from.
    Measured on this account: budget 344.86 against total_spend 1095.32, and
    they are not two ends of one sum -- total_spend is lifetime and budget is
    the balance. This function subtracted them at first and reported -750 left
    on an account with $344 available, which would have parked every task in
    the run before it spent anything.
    """
    who = whoami()
    budget = who.get("budget")
    if budget is None:
        return True, "horizon whoami reports no budget field; proceeding"
    budget = float(budget)
    return budget >= minimum_usd, f"${budget:.2f} of Horizon budget left"


# --------------------------------------------------------------------------- push

def metadata(arm: pathlib.Path) -> dict:
    path = arm / ".horizon" / "metadata.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def push(arm: pathlib.Path, *, label: str = "") -> dict:
    """Push one arm and return its metadata. Confirmed by the file, not the exit.

    Two edges, both of which silently do nothing:

    * push PROMPTS for the task name even with MINI_BATCH_ID set. Run without a
      stdin it fails `EOF when reading a line` and **exits 0**, having created
      nothing. The name plus two blank lines is piped in unconditionally -- on a
      re-push the metadata file already exists and the input is simply unread.
    * `horizon.emit()` rmtree's the arm directory and writes `.horizon/` back
      afterwards. If that ever failed, this push creates a SECOND task instead
      of a new version, and the old one keeps the rollouts. So the version is
      compared before and after: a first push must produce metadata, and a
      re-push must not produce a different task_id.
    """
    before = metadata(arm)
    args = ["tasks", "push", arm.name]
    if label:
        args += ["--label", label]
    done = run(args, cwd=arm.parent, stdin=f"{arm.name}\n\n\n")
    after = metadata(arm)
    if not after.get("task_id"):
        raise HostedError(
            f"push {arm.name}: no .horizon/metadata.json afterwards (exit "
            f"{done.returncode}, which proves nothing here).\n{done.stdout[-1500:]}\n{done.stderr[-800:]}")
    if before.get("task_id") and before["task_id"] != after["task_id"]:
        raise HostedError(
            f"push {arm.name}: task_id changed {before['task_id']} -> {after['task_id']}. "
            "A second task was created and the rollouts are on the old one.")
    return after


# --------------------------------------------------------------------------- validate

def validate(arm: pathlib.Path, agent: str, *, wait: bool = True,
             timeout_s: int = 3600) -> None:
    """Trigger one hosted validation. The score is read from the artifact after.

    Hosted validation is asynchronous: without `--wait` it prints a Build ID,
    returns 0 and reports no score, which is why the documented workflow polls
    `validate-logs`. `--wait` does that polling in-process; `validate-logs` is
    still called afterwards, because `--wait` finishing is not the same as
    `.validation/<build>/result.json` being on disk, and the file is what
    `gates.read_validation` reads.
    """
    args = ["tasks", "validate", "--mode", "hosted", "--agent", agent, "."]
    if wait:
        args += ["--wait", "--poll-interval", "15"]
    run(args, cwd=arm, timeout_s=timeout_s)
    run(["tasks", "validate-logs", "-a", agent, "."], cwd=arm, timeout_s=600)


def validate_both(arm: pathlib.Path) -> None:
    """oracle then noop. This is the package's own bracket in Horizon's idiom,
    and the only way to run it: `apex_arena:base` lives in Horizon's project,
    so the Dockerfile these arms emit cannot be built on this box."""
    for agent in ("oracle", "noop"):
        validate(arm, agent)


# --------------------------------------------------------------------------- evaluate

_EVAL_ID = re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b")


# Turns, when the default is not enough.
#
# g8's two biggie-max rollouts stopped at NINE and TEN turns, mid-heredoc, while
# the cipher-omni rollout that scored 1.000 on the same arm took forty-four. The
# transcripts end part-way through writing a file: they were cut off, not
# defeated. A task whose change spans several files needs the headroom said out
# loud, because the failure looks exactly like the model being unable to do it.
MAX_TURNS = 120


def submit(task_ids: list[str], *, runs: int, model: str = MODEL,
           agent_type: str | None = None, max_turns: int | None = MAX_TURNS) -> str:
    agent_type = agent_type or agent_type_for(model)
    ok, why = affordable()
    if not ok:
        raise HostedError(f"refusing to submit: {why}. Rollouts would error with "
                          "zero spend and look exactly like a broken task.")
    argv = ["evaluations", "submit", ",".join(task_ids), "--model", model,
            "--runs", str(runs), "--agent-type", agent_type, "--json"]
    if max_turns:
        argv += ["--max-turns", str(max_turns)]
    done = run(argv, cwd=REPO)
    try:
        payload = json.loads(done.stdout)
        eval_id = payload.get("evaluation_id") or payload.get("id")
    except json.JSONDecodeError:
        eval_id = None
    if not eval_id:                       # --json is newer than the banner; fall back
        found = _EVAL_ID.findall(done.stdout)
        eval_id = found[0] if found else None
    if not eval_id:
        raise HostedError(f"submit produced no evaluation id.\n{done.stdout[-1500:]}\n{done.stderr[-800:]}")
    return eval_id


def status(eval_id: str) -> dict:
    """One evaluation's real state.

    An unknown id comes back as valid JSON -- `{"error": ...}` -- not as a
    non-zero exit and not as a parse failure. Handing that to the poll loop
    below would spin for the full four-hour timeout on a typo, since a payload
    with no `status` and no `rollouts` looks exactly like one still starting up.
    """
    done = run(["evaluations", "status", eval_id, "--json"], cwd=REPO, timeout_s=300)
    try:
        payload = json.loads(done.stdout)
    except json.JSONDecodeError:
        raise HostedError(f"status {eval_id} returned no JSON: {done.stdout[:400]}")
    if isinstance(payload, dict) and payload.get("error") and "status" not in payload:
        raise HostedError(f"status {eval_id}: {payload['error']}")
    return payload


def await_evaluation(eval_id: str, *, poll_s: int = 60, timeout_s: int = 14400) -> dict:
    """Poll until every rollout has finished, then return the final status.

    NEVER reads the rendered status table. While an evaluation is running it
    shows every unfinished rollout as `failed` with no score, which is
    indistinguishable from twenty genuine failures -- g4's first evaluation was
    cancelled on the strength of that column while all twenty runs were healthy
    and mid-flight, costing $17.03 with no refund and no measurement. The truth
    is `rollouts.total` (what has finished) against `rollouts.errored` (what
    actually broke).

    Wall-clock is judged against a task that worked: g3's rollouts finished in
    about 8 minutes, so a ticket still going at 13 is a long task, not a hung
    one. The timeout is four hours for that reason.
    """
    # The `rollouts` object carries total / successful / passed / errored /
    # graded / avg_score -- and NOTHING that says how many were asked for. So
    # the only terminal signal is `status`, and it is the one polled. Measured
    # on three real evaluations: `completed` with 6 graded, `completed` with 6
    # errored and 0 graded, and `failed` with 0 rollouts at all.
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        last = status(eval_id)
        state = (last.get("status") or last.get("state") or "").lower()
        if state in ("completed", "finished", "succeeded", "done", "cancelled", "failed"):
            return last
        time.sleep(poll_s)
    raise HostedError(f"evaluation {eval_id} did not finish inside {timeout_s}s; "
                      f"last status {json.dumps(last)[:600]}")


def pull(arm: pathlib.Path) -> int:
    """Download this arm's rollouts into `<arm>/.rollouts/v<N>/`. Returns the count."""
    run(["rollouts", "pull", "."], cwd=arm, timeout_s=1800)
    root = arm / ".rollouts"
    return len([p for p in root.rglob("*.json")]) if root.is_dir() else 0
