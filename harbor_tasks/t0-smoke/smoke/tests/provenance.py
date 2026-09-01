#!/usr/bin/env python3
"""Did the change travel the path the world insists on?

Three independent reads, reported separately, because they fail for different
reasons and the difference is the thing the experiment needs to see:

  pushed     `main` moved off the SHA recorded before the agent started
  ci_green   the Gitea Actions run for that SHA succeeded
  deployed   /opt/sweworld/curator/current points at a release named for it

`deploy-service` installs each release as
`/opt/sweworld/curator/releases/<YYYYMMDDHHMMSS>-<sha>` and flips `current`, so
the deployed SHA is readable from a symlink and cannot be forged by an agent who
has no write access to /opt/sweworld.

The baseline SHA comes from `/opt/world-state/baseline.env`, written by
`setup.sh` as root before the agent started. Comparing against a SHA hardcoded
here would break the first time the world image is rebaked.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

LOGS = pathlib.Path("/logs/verifier")
STATE = pathlib.Path("/opt/world-state/baseline.env")
GITEA = "http://127.0.0.1:3300"
REPO = "worldadmin/curator"
CURRENT = "/opt/sweworld/curator/current"
LAST_GOOD = "/opt/sweworld/curator/last-good"

# The verifier starts the instant the agent stops, which can be mid-deploy. This
# does not let an agent who never deployed pass — the assertions still have to
# hold — it only avoids grading a container that is still restarting.
SETTLE_SEC = 90
# Separate budget: the deploy lands before the workflow is marked finished.
CI_SETTLE_SEC = 120


def token() -> str:
    try:
        return pathlib.Path("/etc/sweworld/gitea-token").read_text().strip()
    except OSError:
        return ""


def api(path: str) -> object | None:
    req = urllib.request.Request(f"{GITEA}/api/v1{path}")
    tok = token()
    if tok:
        req.add_header("Authorization", f"token {tok}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except (urllib.error.URLError, OSError, ValueError):
        return None


def baseline() -> dict[str, str]:
    out: dict[str, str] = {}
    if STATE.exists():
        for line in STATE.read_text().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                out[key.strip()] = value.strip()
    return out


def head_sha() -> str:
    branch = api(f"/repos/{REPO}/branches/main")
    if isinstance(branch, dict):
        return ((branch.get("commit") or {}).get("id") or "")
    return ""


def ci_status(sha: str) -> tuple[bool, str]:
    """Gitea reports Actions through the commit status API.

    `combined` is what the UI shows: success only if every run for that SHA
    succeeded. A SHA with no runs at all comes back "pending", which is not
    green — and is exactly what an agent who pushed to a branch other than
    `main` produces.
    """
    if not sha:
        return False, "no sha"
    status = api(f"/repos/{REPO}/commits/{sha}/status")
    if not isinstance(status, dict):
        return False, "no status endpoint"
    state = status.get("state") or "unknown"
    return state == "success", state


def deployed_sha() -> tuple[str, str]:
    try:
        target = os.path.realpath(CURRENT)
    except OSError:
        return "", ""
    return pathlib.Path(target).name.split("-", 1)[-1], target


def is_deployed(head: str, deployed: str) -> bool:
    """Does the release on disk name this commit?

    `deploy-service` names a release `<timestamp>-<sha>` from the SHORT sha CI
    handed it, so this is a prefix test in one direction only. Comparing the two
    for equality reads every successful deploy as a failure — and, in `settle`
    below, makes the wait burn its whole budget on a deploy that already landed.
    """
    return bool(head) and bool(deployed) and head.startswith(deployed)


def settle(want: str) -> None:
    """Give a deploy that is already in flight time to land."""
    if not want:
        return
    deadline = time.time() + SETTLE_SEC
    while time.time() < deadline:
        if is_deployed(want, deployed_sha()[0]):
            return
        time.sleep(5)


def settle_ci(sha: str) -> tuple[bool, str]:
    """Wait for the Actions run to reach a terminal state.

    `request-deploy` is the LAST step of the workflow, so at the moment the
    release flips the run is still in progress — and the verifier starts
    seconds later. Reading the status once reports "pending" for a run that is
    about to go green, which shows up as the contradiction "deployed: yes,
    CI green: no".
    """
    deadline = time.time() + CI_SETTLE_SEC
    green, state = ci_status(sha)
    while time.time() < deadline and state in ("pending", "running", ""):
        time.sleep(5)
        green, state = ci_status(sha)
    return green, state


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    base = baseline()
    head = head_sha()
    settle(head)
    deployed, release = deployed_sha()
    green, ci_state = settle_ci(head)

    result = {
        "baseline_sha": base.get("BASE_SHA", ""),
        "head_sha": head,
        "pushed": bool(head) and head != base.get("BASE_SHA", ""),
        "ci_state": ci_state,
        "ci_green": green,
        "deployed_sha": deployed,
        "deployed_release": release,
        "deployed": is_deployed(head, deployed),
        "last_good": os.path.realpath(LAST_GOOD)
        if pathlib.Path(LAST_GOOD).exists() else "",
    }
    # The one line a human reads first when a task scores zero.
    result["summary"] = (
        "nothing was pushed" if not result["pushed"] else
        "pushed, but the release still points elsewhere — the change never "
        "deployed" if not result["deployed"] else
        f"pushed and deployed; CI {ci_state}")

    (LOGS / "provenance.json").write_text(json.dumps(result, indent=1))
    print(result["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
