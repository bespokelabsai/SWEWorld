#!/usr/bin/env python3
"""Run this task's grading suite against whatever the agent pushed.

Grades the pushed `main`, not the agent's working tree, and not the deployed
release. That is deliberate and it is what makes the result readable: the
provenance checks say separately whether the change was pushed, whether CI went
green, and whether it deployed, so an agent that wrote the right code and never
deployed it scores zero on provenance and full marks on the requirements —
instead of one shared zero that could mean either.

Run under the world's venv (`$CURATOR_VENV/bin/python`), which has curator's
dependencies but deliberately NOT curator itself: `src/bespokelabs/__init__.py`
is a regular package, so an installed copy would shadow the submission and every
test would grade the vendored snapshot.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

TESTS = pathlib.Path("/tests")
LOGS = pathlib.Path("/logs/verifier")
WORK = pathlib.Path("/tmp/verifier")
GITEA = "http://127.0.0.1:3300"
REPO = "worldadmin/curator"
VENV = os.environ.get("CURATOR_VENV", "/opt/curator-dev/venv")


def token() -> str:
    try:
        return pathlib.Path("/etc/sweworld/gitea-token").read_text().strip()
    except OSError:
        return ""


def clone_pushed_main() -> tuple[pathlib.Path | None, str]:
    """A clean checkout of whatever `main` holds now.

    Cloned rather than read from the agent's home: the world's contract is that
    code arrives by being pushed, and grading a working tree would pass an agent
    who never pushed at all — which the provenance half is there to catch.
    """
    WORK.mkdir(parents=True, exist_ok=True)
    dest = WORK / "submission"
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)], check=False)
    url = f"http://worldadmin:{token() or 'worldadmin'}@127.0.0.1:3300/{REPO}.git"
    done = subprocess.run(["git", "clone", "--quiet", "--branch", "main",
                           "--depth", "1", url, str(dest)],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return None, done.stderr.strip()[:400]
    sha = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    return dest, sha



def variant_of(meta: dict) -> str:
    """Which arm this task is: blind, spec, or clues.

    `control` was a boolean when there were only two arms. Tasks built before
    the clues arm still carry it and nothing else, so it stays the fallback.
    """
    return meta.get("variant") or ("spec" if meta.get("control") else "blind")


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    meta = json.loads((TESTS / "task.json").read_text())
    suite = TESTS / meta["suite"]

    report = {"task": meta["task_id"], "suite": meta["suite"],
              "variant": variant_of(meta)}

    submission, sha_or_error = clone_pushed_main()
    if submission is None:
        report["submission_error"] = sha_or_error
        (LOGS / "run_report.json").write_text(json.dumps(report, indent=1))
        print(f"could not clone {REPO}: {sha_or_error}", file=sys.stderr)
        return 1
    report["submission_sha"] = sha_or_error
    report["submission_path"] = str(submission)

    src = submission / "src"
    if not (src / "bespokelabs" / "curator" / "llm" / "llm.py").exists():
        report["submission_error"] = "no src/bespokelabs/curator/llm/llm.py in main"
    # /tests on the path as well as the submission: the suites import shared
    # helpers as `from harness import ...` rather than through a relative
    # package import, because a conftest is not importable and the tests
    # directory is not a package.
    env = {**os.environ,
           "PYTHONPATH": os.pathsep.join([str(src), str(TESTS)]),
           "PYTHONHASHSEED": "0",
           "PYTEST_ADDOPTS": ""}

    # Run FROM /tests with a relative suite path. Pointing pytest at
    # /tests/<suite> makes that directory the rootdir, and /tests/conftest.py —
    # one level above it — is then never loaded: every fixture comes back
    # "not found" and every test errors, which scores exactly like an agent who
    # wrote nothing.
    cmd = [f"{VENV}/bin/python", "-m", "pytest", meta["suite"],
           "-p", "no:cacheprovider", "-q", "-rA",
           # signal, NOT thread. The thread method cannot interrupt a blocked
           # asyncio loop, so it terminates the whole process — and pytest then
           # never writes junit.xml, so every fact in the suite scores 0 with
           # suite_error=1. t3 lost both its runs that way: curator really does
           # spin forever in `while not has_capacity(): sleep(0.1)`, which is
           # the very behaviour one of its tests exists to catch. SIGALRM
           # raises inside the test, pytest fails it and carries on.
           "--timeout=180", "--timeout-method=signal",
           f"--junit-xml={LOGS}/junit.xml",
           f"--ctrf={LOGS}/ctrf.json"]
    done = subprocess.run(cmd, env=env, capture_output=True, text=True,
                          cwd=str(TESTS))
    (LOGS / "pytest.log").write_text(done.stdout + "\n" + done.stderr)
    report["pytest_returncode"] = done.returncode
    (LOGS / "run_report.json").write_text(json.dumps(report, indent=1))
    print(done.stdout[-4000:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
