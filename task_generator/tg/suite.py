"""Run a grading suite against one implementation, and bring the junit back.

The only place in this package that knows about Docker, and the only route an
authoring agent has to executing anything. It exists because **curator is
importable nowhere on this host** — not in `.venv`, not in the system python3,
not in the world images' default interpreter. The single environment that can
import it is `/opt/curator-dev/venv` inside `sweworld:repo-only-dev`, which holds
curator's whole dependency closure with curator itself deliberately uninstalled
so the tree under test is what gets imported (see `harbor_tasks/_env/Dockerfile`).

This reproduces `failed_tasks/BRACKET.md` §"Reproducing this" — the same recipe
that replaced a seven-hour, eight-trial agent experiment whose numbers had to be
discarded, with a thirty-second deterministic one.

Two rules about the container:

**It is shared.** `devbox` is a long-lived box and harbor trials run in sibling
containers. Every run gets its own `/tmp/tg/<tag>` and removes it afterwards; no
step writes to a fixed path.

**A timeout is a safety net, never a grade.** `--timeout` is set so a tree that
loops forever cannot wedge the bracket — the pristine curator does exactly that
when a single row exceeds the byte budget. No requirement is ever *graded* on the
timeout firing: a test that can only distinguish right from wrong by how long it
took cannot tell slow-but-correct from broken.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
import uuid

from .model import REPO, SUITES

CONTAINER = "devbox"
PRISTINE = "/opt/world-state/input/curator"
VENV = "/opt/curator-dev/venv/bin/python"
ROOT = "/tmp/tg"


class SuiteError(RuntimeError):
    pass


def _docker(*args: str, check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    done = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    if check and done.returncode != 0:
        raise SuiteError(f"docker {' '.join(args[:2])} failed: {done.stderr.strip()[:400]}")
    return done


def container_ready(container: str = CONTAINER) -> str:
    """Say plainly whether the box we need is up, before anything is copied."""
    done = _docker("exec", container, "test", "-x", VENV, check=False)
    if done.returncode != 0:
        raise SuiteError(
            f"container {container!r} cannot run {VENV}. It must be a running "
            "sweworld:repo-only-dev (`docker ps` should list it). Without it "
            "there is no environment on this machine that can import curator.")
    return container


def run(
    fixture: pathlib.Path | None,
    *,
    suite_name: str,
    task_tests: pathlib.Path,
    shared: pathlib.Path = SUITES,
    container: str = CONTAINER,
    per_test_timeout: int = 120,
    timeout_s: int = 1200,
    keep: bool = False,
) -> dict:
    """Apply `fixture` to a fresh pristine tree, run `suite_name`, return outcomes.

    `fixture` is a patch-applier script taking the checkout path — the calling
    convention `bracket_matrix.txt` and BRACKET.md already use. `None` means the
    pristine tree, untouched.

    Returns `{"outcomes": {"<module>::<test>": state}, "rc": int, "stdout": str,
    "junit": <local path>}`. Outcomes are parsed by `score.junit_outcomes`, so
    they are the same strings the paid verifier folds.
    """
    container_ready(container)
    tag = f"{suite_name}-{uuid.uuid4().hex[:8]}"
    base = f"{ROOT}/{tag}"
    local = pathlib.Path(tempfile.mkdtemp(prefix=f"tg-{tag}-"))

    try:
        _docker("exec", container, "mkdir", "-p", base)

        # The shared graders, then this task's own suite on top of them. Two
        # copies rather than one staged directory so an emitted task and an
        # un-emitted one take the identical path through here.
        #
        # `src/.` and a pre-made destination, never `docker cp src dest`. When
        # the destination directory already exists docker cp puts the SOURCE
        # INSIDE it, so copying `_suites/t1_cache_stats` onto a tree that already
        # has that directory produced `tests/t1_cache_stats/t1_cache_stats/` —
        # and pytest then refused to collect anything with "import file
        # mismatch", which reads exactly like a broken suite rather than a
        # mis-copied one.
        _docker("exec", container, "mkdir", "-p", f"{base}/tests/{suite_name}",
                f"{base}/fixtures")
        _docker("cp", f"{shared}/.", f"{container}:{base}/tests")
        if task_tests.is_dir():
            _docker("cp", f"{task_tests}/.", f"{container}:{base}/tests/{suite_name}")
        if fixture is not None:
            _docker("cp", f"{fixture.parent}/.", f"{container}:{base}/fixtures")
        # Host bytecode compiled against other paths is the other way this
        # collection error arrives.
        _docker("exec", container, "bash", "-c",
                f"find {base}/tests -name __pycache__ -type d -prune -exec rm -rf {{}} +",
                check=False)

        apply_cmd = ""
        if fixture is not None:
            apply_cmd = f"python3 {base}/fixtures/{fixture.name} {base}/tree && "

        script = (
            f"set -e; cp -r {PRISTINE} {base}/tree; "
            f"{apply_cmd}"
            f"cd {base}/tests && PYTHONPATH={base}/tree/src:{base}/tests "
            f"{VENV} -m pytest {suite_name} -q -p no:cacheprovider "
            f"--junitxml={base}/junit.xml "
            f"--timeout={per_test_timeout} --timeout-method=signal"
        )
        done = _docker("exec", container, "bash", "-c", script,
                       check=False, timeout=timeout_s)

        got = _docker("cp", f"{container}:{base}/junit.xml", str(local / "junit.xml"),
                      check=False)
        junit = local / "junit.xml"
        outcomes: dict[str, str] = {}
        if got.returncode == 0 and junit.is_file():
            from .model import score_module
            outcomes = score_module().junit_outcomes(junit)

        return {"outcomes": outcomes, "rc": done.returncode,
                "stdout": (done.stdout + done.stderr)[-6000:],
                "junit": junit if junit.is_file() else None,
                "tag": tag}
    finally:
        if not keep:
            _docker("exec", container, "rm", "-rf", base, check=False)


def summarise(result: dict) -> str:
    counts: dict[str, int] = {}
    for state in result["outcomes"].values():
        counts[state] = counts.get(state, 0) + 1
    return json.dumps(counts, sort_keys=True) or "{}"


def exec_in_tree(tree: pathlib.Path, command: str, *, container: str = CONTAINER,
                 timeout_s: int = 600) -> dict:
    """Run one shell command against a copy of `tree`, with curator importable.

    The other half of the seam, and it exists for a reason the first half does
    not cover: an authoring agent writing a specification full of literal byte
    counts has no way to check a single one of them on this host, because nothing
    here can import curator. Without this it is guessing, and a spec whose
    observable is `== 153` when the real answer is `== 157` sends the test writer
    chasing a bug that is in the prose.

    Read-only with respect to `tree`: the command runs against a copy, so an
    agent cannot accidentally mutate the tree it is being measured on.
    """
    container_ready(container)
    tag = f"exec-{uuid.uuid4().hex[:8]}"
    base = f"{ROOT}/{tag}"
    try:
        _docker("exec", container, "mkdir", "-p", f"{base}/tree")
        _docker("cp", f"{tree}/.", f"{container}:{base}/tree")
        script = (f"cd {base}/tree && PYTHONPATH={base}/tree/src "
                  f"PATH={pathlib.Path(VENV).parent}:$PATH "
                  f"CURATOR_DISABLE_RICH_DISPLAY=1 TELEMETRY_ENABLED=false "
                  f"CURATOR_VIEWER=false HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 "
                  f"OPENAI_API_KEY=sk-authoring ANTHROPIC_API_KEY=sk-authoring "
                  f"{command}")
        done = _docker("exec", container, "bash", "-lc", script,
                       check=False, timeout=timeout_s)
        return {"rc": done.returncode, "stdout": done.stdout[-20000:],
                "stderr": done.stderr[-8000:]}
    finally:
        _docker("exec", container, "rm", "-rf", base, check=False)
