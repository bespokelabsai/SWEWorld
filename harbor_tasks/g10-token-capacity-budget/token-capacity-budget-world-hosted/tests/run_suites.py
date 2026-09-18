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

GRADING RUNS AGENT-AUTHORED CODE, SO IT DOES NOT RUN AS ROOT
------------------------------------------------------------
`task.toml` gives the verifier `user = "root"` because `provenance.py` reads
`/opt/world-state/baseline.env` (0600) and the release symlinks. This file is
the one step that must not keep it. Importing the submission IS executing it:
`conftest.py` (the non-split path only; split-suite arms do not ship it) does `import bespokelabs` at collection time, and anything on
`PYTHONPATH` gets a free shot even earlier, because Python imports
`sitecustomize` at interpreter startup.

That combination was a full-score forgery. With the submission first on
`PYTHONPATH` and pytest spawned as root, a pushed `src/sitecustomize.py` ran as
uid 0 before a single assertion, rewrote this directory's own `score.py`, and
returned `reward.json` with every subscore at 1.0 — from a pristine tree that
implemented none of the hidden requirements. `task.toml`'s comment claimed root
was there "so the state being graded cannot be forged"; root was what made the
forgery reachable.

So the pytest child drops to an unprivileged uid. `/tests` stays its own rootdir
and cwd — `test.sh` opens it to the drop group read-only rather than copying it
somewhere, because a staged suite under `/tmp` would put pytest's rootdir and
conftest-discovery chain inside a directory the agent CAN write during its own
phase, and `/tmp/conftest.py` is a one-line all-pass. Trading a root exploit for
that would have been a bad trade. `provenance.py` and `score.py` keep root,
because their inputs are exactly what root is legitimately for.

The submission is deliberately NOT on `PYTHONPATH` — see `conftest.py`, which
puts it on `sys.path` behind the stdlib instead. `PYTHONPATH` precedes the
standard library, so a pushed `src/encodings/__init__.py` runs during
interpreter startup no matter which uid owns the process.

WHAT THIS DOES NOT FIX, and it is not theoretical — it was reproduced after the
drop landed. The child is still the process that writes `junit.xml`, and
`score.py` trusts that file. A payload in `bespokelabs/curator/__init__.py`
reads the real node ids out of `/tests` (which it must be able to read in order
to be graded at all), finds the report path in its own `/proc/self/cmdline`, and
rewrites it from an `atexit` hook. Measured on a pristine tree: `reward` 1.0,
`hidden_mean` 1.0. Nine forged `<testcase>` elements.

So this file removes the ROOT compromise — no rewriting the grader, no reading
the planted corpus, no persistence past the run — and does not remove score
forgery. Closing that means the process importing agent code must stop being the
process reporting outcomes; a uid cannot do it. What holds meanwhile is
`provenance.py`, a separate root process reading Gitea and the `svc`-owned
release symlink, neither of which the drop uid can touch: a forged pass still
cannot claim it pushed, deployed, or went green.
"""
from __future__ import annotations

import json
import os
import pathlib
import pwd
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import tempfile

TESTS = pathlib.Path("/tests")
LOGS = pathlib.Path("/logs/verifier")
GITEA = "http://127.0.0.1:3300"
REPO = "worldadmin/curator"
VENV = os.environ.get("CURATOR_VENV", "/opt/curator-dev/venv")
BASELINE_TREE = pathlib.Path("/opt/world-state/input/curator")

# The uid the submission is imported under. `nobody` rather than a user of our
# own: it exists in every Debian/Ubuntu base, owns nothing anywhere in this
# world, and needs no bootstrap change to a published image. `ubuntu` would be
# wrong — the agent can pre-seed its home and its user site-packages, and it is
# the one account with a stake in the answer.
DROP_USER = "nobody"
DROP_GROUP = "nogroup"

# 900, not 1500. Measured worker runs across the split suites are SECONDS (g9 2.1s,
# g4 7.1s, g3 under 1s; a fifteen-variant sweep took 100s), so 900 is a hundredfold
# margin for honest work while keeping the worst case inside a 2400s verifier budget:
# 210 provenance + 900 worker + 900 judge + ~120 clone/baseline/score = 2130. At 1500
# twice the arithmetic exceeded the budget, and an overrunning verifier is KILLED --
# which writes no reward at all and reads as a broken harness rather than a failure.
# Well inside the verifier budget in task.toml. pytest-timeout arms a
# per-TEST timer, which is no help at all if the submission hangs at import:
# collection never finishes, no timer exists yet, and the verifier runs to
# Harbor's cap and is KILLED -- so no reward.json is written and the result
# reads as a broken harness rather than a failed task. That is a usable way out
# of a bad score, and it costs one `while True` in `__init__.py`.
PYTEST_TIMEOUT = 900


def token() -> str:
    try:
        return pathlib.Path("/etc/sweworld/gitea-token").read_text().strip()
    except OSError:
        return ""


def make_workdir() -> pathlib.Path:
    """A root-owned scratch directory with a name the agent cannot predict.

    NOT `/tmp/verifier`, which is what this used to be. `/tmp` is writable by
    the agent for the whole of its phase, and root then `rm -rf`d and cloned
    into a fixed path there after an `exists()` that follows symlinks. Under
    `/run` the parent is root-owned, and `mkdtemp` picks the leaf name.

    0711 rather than 0700: after the drop the child still needs search
    permission on every ancestor of anything it opens, and it owns none of them.
    """
    root = pathlib.Path("/run/verifier")
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o755)
    work = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=str(root)))
    work.chmod(0o711)
    return work


def clone_pushed_main(work: pathlib.Path) -> tuple[pathlib.Path | None, str]:
    """A clean checkout of whatever `main` holds now.

    Cloned rather than read from the agent's home: the world's contract is that
    code arrives by being pushed, and grading a working tree would pass an agent
    who never pushed at all — which the provenance half is there to catch.

    Root clones an agent-controlled repository, so the transport is pinned shut:
    no symlinks in the worktree, no `ext::` helper, no local-clone hardlinking,
    and no credential prompt to hang the verifier on. The tree is then left
    root-owned and world-readable — the child must import it and must not be
    able to rewrite it underneath its own tests.
    """
    dest = work / "submission"
    url = f"http://worldadmin:{token() or 'worldadmin'}@127.0.0.1:3300/{REPO}.git"
    done = subprocess.run(["git", "-c", "core.symlinks=false",
                           "-c", "protocol.ext.allow=never",
                           "clone", "--quiet", "--no-local",
                           "--branch", "main", "--depth", "1", url, str(dest)],
                          capture_output=True, text=True, errors="replace",
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if done.returncode != 0:
        return None, done.stderr.strip()[:400]
    subprocess.run(["chmod", "-R", "a+rX", str(dest)], check=False)
    sha = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                         capture_output=True, text=True,
                         errors="replace").stdout.strip()
    return dest, sha


# The provider names, inline. They used to be imported from `fakeapi`, which a
# split-suite arm no longer ships (it belongs to the pytest path) -- so the import
# failed, `hosts_error` was recorded, and nothing was pinned. Three hostnames are
# not worth a dependency that can vanish: a missing mapping is silent, and the
# failure it produces is someone else's 401 in the middle of a graded run.
PROVIDER_HOSTS = ("api.openai.com", "api.deepseek.com", "api.anthropic.com")


def map_hosts(report: dict) -> bool:
    """Point the provider names at loopback, as root, before the drop.

    `conftest._map_hosts` did this itself and can no longer: the child has no
    write access to /etc/hosts. Doing it here is not merely a convenience —
    `task.toml` sets `allow_internet = true`, so an unmapped `api.openai.com`
    resolves to the real one and curator makes real outbound calls with a
    mocked key. Every provider test then fails on someone else's 401 instead of
    on the agent's code, which is the least diagnosable failure in the harness.

    So this verifies rather than hopes, and says so in the report.
    """
    try:
        current = pathlib.Path("/etc/hosts").read_text()
        missing = [h for h in PROVIDER_HOSTS if h not in current]
        if missing:
            with open("/etc/hosts", "a") as fh:
                fh.write("\n# curator grading suites - provider names on loopback\n")
                fh.write("127.0.0.1 " + " ".join(missing) + "\n")
        current = pathlib.Path("/etc/hosts").read_text()
    except OSError as exc:
        report["hosts_error"] = str(exc)
        return False
    still = [h for h in PROVIDER_HOSTS if h not in current]
    if still:
        report["hosts_error"] = f"not mapped: {', '.join(still)}"
        return False
    report["hosts_mapped"] = True
    return True


def stage_baseline(work: pathlib.Path, report: dict) -> pathlib.Path | None:
    """A copy of the pristine tree the drop uid can read.

    `harness.BASELINE` lives under /opt/world-state, which is 0700 root and
    stays that way — it holds the planted corpus, and opening it to the grading
    uid would hand the submission the answer key.

    Copied rather than tarred: `_archived_baseline()` matches members against a
    hardcoded `./src/bespokelabs/curator/` prefix, so a tar built one path
    component off returns an EMPTY baseline, and an empty baseline does not
    fail — `changed_source()` simply reports the entire library as changed.
    Facts that scan changed files for a keyword then pass on untouched curator,
    and facts that assert a keyword is ABSENT from changed files fail on a
    correct submission. Wrong in both directions, silently. A directory copy
    either exists or does not, and the caller checks which.
    """
    tree = BASELINE_TREE / "src" / "bespokelabs" / "curator"
    if not (tree / "llm" / "llm.py").is_file():
        report["baseline"] = f"absent at {tree}"
        return None
    dest = work / "baseline"
    done = subprocess.run(["cp", "-a", str(tree), str(dest)],
                          capture_output=True, text=True, errors="replace")
    if done.returncode != 0 or not (dest / "llm" / "llm.py").is_file():
        report["baseline"] = f"copy failed: {done.stderr.strip()[:200]}"
        return None
    subprocess.run(["chmod", "-R", "a+rX", str(dest)], check=False)
    report["baseline"] = f"staged {sum(1 for _ in dest.rglob('*.py'))} files"
    return dest


def check_protected(meta: dict, submission: pathlib.Path, report: dict) -> None:
    """Byte-compare every file the instruction protects against the pristine tree.

    An instruction that says "`base_trainer.py` does not change" and a grader
    that never looks is worse than no instruction: an agent can rewrite the
    protected trainer to make its own job easier and still score 1. So root
    compares the pushed file with `/opt/world-state/input/curator` -- which the
    agent cannot write -- and records the verdict in the root-only
    /logs/verifier, where `score.py` gates the reward on it. Nothing the
    submission runs is involved; this happens before any agent code is imported.

    Always writes the file when the task protects something, including when the
    pristine copy is missing: `score.py` reads an absent verdict as unmeasured,
    and unmeasured is not a pass.
    """
    paths = meta.get("protected_files") or []
    if not paths:
        return
    verdict = {}
    for rel in paths:
        pristine = BASELINE_TREE / rel
        pushed = submission / rel
        if not pristine.is_file():
            verdict[rel] = "unmeasured"
        elif pushed.is_symlink() or not pushed.is_file():
            verdict[rel] = "deleted"
        else:
            verdict[rel] = ("unchanged" if pushed.read_bytes() == pristine.read_bytes()
                            else "modified")
    (LOGS / "protected.json").write_text(json.dumps(verdict, indent=1))
    report["protected_files"] = verdict


def harvest(src: pathlib.Path, dest: pathlib.Path, uid: int) -> str | None:
    """Copy one child-written report file into /logs, as root, without trusting it.

    The child owns the directory these land in, so `junit.xml` can be a symlink
    by the time root reads it — and a plain `shutil.copy` as root would happily
    follow it and deposit `/opt/world-state/baseline.env` into a log file. Open
    with O_NOFOLLOW, confirm it is a regular file the drop uid actually wrote,
    and cap the size so a hostile file cannot exhaust the verifier.
    """
    limit = 32 * 1024 * 1024
    try:
        # O_NONBLOCK, because O_RDONLY on a FIFO BLOCKS here until a writer
        # arrives -- before fstat can reject it. A worker that leaves a FIFO
        # named junit.xml hangs root until the verifier times out, and a killed
        # verifier writes no reward.json, so a submission heading for 0 could
        # trade that 0 for a harness error instead.
        fd = os.open(src, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        return f"{src.name}: {exc}"
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return f"{src.name}: not a regular file"
        os.set_blocking(fd, True)
        if st.st_uid not in (0, uid):
            return f"{src.name}: owned by uid {st.st_uid}"
        if st.st_size > limit:
            return f"{src.name}: {st.st_size} bytes over cap"
        with os.fdopen(fd, "rb") as fh:
            dest.write_bytes(fh.read(limit))
    except OSError as exc:
        return f"{src.name}: {exc}"
    return None



def variant_of(meta: dict) -> str:
    """Which arm this task is: blind, spec, or clues.

    `control` was a boolean when there were only two arms. Tasks built before
    the clues arm still carry it and nothing else, so it stays the fallback.
    """
    return meta.get("variant") or ("spec" if meta.get("control") else "blind")


def spawn(cmd: list[str], env: dict, log: pathlib.Path, *, drop=None,
          cwd=TESTS, timeout: int = PYTEST_TIMEOUT) -> tuple[int, bool]:
    """Run `cmd`, its output to a root-opened file, its whole tree in one session.

    `start_new_session` puts the process and anything it forks in one process
    group, and the group is SIGKILLed after wait returns whether or not it timed
    out — so a forged `atexit` daemon that tries to outlive the worker and edit
    the judge's report is reaped before the judge is even consulted. `drop` runs
    the child unprivileged; `None` keeps root (the judge, which imports nothing
    the agent wrote).

    `cwd` defaults to /tests (judge + non-split pytest path). The split WORKER
    must pass its jail instead: once /tests is root-only 0700, a `nobody` child
    with cwd=/tests would fail to chdir there (PermissionError, depending on the
    chdir-vs-drop order inside _posixsubprocess), never start, and score every
    fact 0 — reading like a broken harness. A 0755 jail cwd removes that.
    """
    with open(log, "ab") as fh:
        kw = dict(env=env, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT,
                  start_new_session=True)
        if drop is not None:
            kw.update(user=DROP_USER, group=DROP_GROUP, extra_groups=[], umask=0o077)
        proc = subprocess.Popen(cmd, **kw)
        timed_out = False
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                proc.kill()
            rc = proc.wait(timeout=60)
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # reap any lingering grandchild
        except OSError:
            pass
        return rc, timed_out


def run_split(meta: dict, suite_dir: pathlib.Path, src: pathlib.Path, work: pathlib.Path,
              out: pathlib.Path, drop, base_env: dict, report: dict) -> int:
    """The worker/judge grading path: the process that imports the submission is
    NOT the process that decides pass/fail.

    WORKER (`probe.py`, dropped to `nobody`): imports curator and records values
    — never a verdict — to `observations.json`. The submission is on its
    PYTHONPATH, so a planted `sitecustomize` runs at ITS startup; that is exactly
    why this process is disposable and writes nothing score.py reads.

    JUDGE (`judge.py`, root, stdlib only): reads those values and the cloned
    source text and writes `junit.xml` STRAIGHT to the root-owned /logs, applying
    the same assertions the suite always made. No agent code has run in it, so
    the report it writes cannot be forged — the gap `run_suites` documents and a
    uid alone could not close (see tasks/lessons.md, 2026-09-09).

    SEED and ARTIFACTS, both root-chosen, both handed to the two processes.
    Splitting the processes stops the worker REWRITING the verdict; it does not
    stop the worker INVENTING the values the judge reads — and with a fixed
    fixture those values are the same every run, so an agent that has seen one
    run (or read them out of the world's own corpus) can hardcode a passing
    observations file from a tree that implements nothing. Measured on g1: reward
    1.0 from pristine `main` plus one `atexit` hook. The worker cannot pick the
    seed itself (it would pick one it has answers for) and the judge runs too
    late to choose it, so root does, once, here. `artifacts` is where the
    worker's scenarios run: root-readable, so a suite can grade the directory it
    reads itself rather than the worker's description of it.

    Both are extra argv, and every other suite's probe takes `sys.argv[1]` alone
    — so this is inert for them until their own probe/judge opt in.
    """
    log = LOGS / "pytest.log"
    report["mode"] = "worker/judge"

    obs = out / "observations.json"

    # The seed is drawn by ROOT, after the agent's container is gone, which is what
    # makes a replayed capture useless. `SPLIT_SEED` overrides it for REPRODUCTION
    # only -- a reviewer re-running a graded scenario, or a suite author bisecting a
    # draw. It cannot help a submission: the agent's phase is over before this runs,
    # and nothing the agent writes is read here.
    seed = os.environ.get("SPLIT_SEED") or secrets.token_hex(8)
    report["seed"] = seed
    if os.environ.get("SPLIT_SEED"):
        report["seed_overridden"] = True

    # 0755, not the 0700 of `out`: the worker must write here and root must read
    # it back afterwards. Owned by the drop uid, under the unpredictable `work`.
    artifacts = work / "artifacts"
    artifacts.mkdir()
    os.chown(artifacts, drop.pw_uid, drop.pw_gid)
    artifacts.chmod(0o755)

    # Stage a JAIL: the worker's ENTIRE view of the suite is these three
    # answer-free files, copied into a root-owned dir. /tests is root-only 0700
    # for split suites (see build_tasks.TEST_SH), so agent code running in the
    # worker cannot open() task.json, test_open.py, test_r*.py or judge.py by
    # absolute path — every reward-bearing expected value is unreachable, so a
    # forged observations.json cannot match the judge without implementing the
    # requirement. `probe_support.py` carries the answer-free helpers/inputs the
    # probe needs; `harness.py` its `read_field`. 0755 on the jail because import
    # reads+searches it; 0644 files, none writable by the worker.
    jail = work / "jail"
    jail.mkdir()
    jail.chmod(0o755)
    # `fixture_spec.py` is optional and only a suite that re-draws its inputs
    # ships one. It holds the run's INPUTS, never an expected value, so the
    # worker reading it gains nothing — and it must read it, because it is what
    # builds the scenarios.
    for name, srcfile in (("probe.py", suite_dir / "probe.py"),
                          ("probe_support.py", suite_dir / "probe_support.py"),
                          ("fixture_spec.py", suite_dir / "fixture_spec.py"),
                          ("harness.py", TESTS / "harness.py")):
        if not srcfile.is_file():
            continue
        shutil.copy(srcfile, jail / name)
        (jail / name).chmod(0o644)

    # Python runs `sitecustomize` (then `usercustomize`) at INTERPRETER STARTUP,
    # from the first PYTHONPATH entry that has it -- before `probe.py`'s first
    # line. With the submission first on the path, a pushed `src/sitecustomize.py`
    # pre-empted the probe entirely and wrote a fully-formed observations.json: a
    # pristine tree plus a 12-line hook scored 9/9 on g7 and reward 1.0 on g8.
    # Two changes close it. The jail goes FIRST, so the submission can no longer
    # shadow `harness.py` or `probe_support.py` either; and the jail ships inert
    # `sitecustomize`/`usercustomize` modules, so the name resolves here and the
    # submission's copy is never imported.
    for hook in ("sitecustomize.py", "usercustomize.py"):
        (jail / hook).write_text(
            "# Inert. Present so this name resolves inside the root-owned jail\n"
            "# rather than in the submission, which Python would otherwise import\n"
            "# at startup, before the probe runs.\n")
        (jail / hook).chmod(0o644)

    worker_env = dict(base_env)
    # ONLY the submission src and the jail — NOT /tests, NOT suite_dir. The worker
    # has no import or open() path into /tests.
    worker_env["PYTHONPATH"] = os.pathsep.join([str(jail), str(src)])
    # Belt to the braces above: refuse to run rather than race a startup hook we
    # failed to shadow. `encodings` is imported before PYTHONPATH shadowing can
    # help, so it is named here too. No observations file means every judge fails
    # its facts closed, which is the reward-0 this deserves.
    hostile = [n for n in ("sitecustomize.py", "usercustomize.py", "encodings")
               if (src / n).exists()]
    if hostile:
        report["startup_hooks_in_submission"] = hostile
        return 1
    rc_w, timed_out = spawn([f"{VENV}/bin/python", str(jail / "probe.py"), str(obs),
                             seed, str(artifacts)],
                            worker_env, log, drop=drop, cwd=jail)
    report["worker_returncode"] = rc_w
    if timed_out:
        report["worker_timeout"] = True

    # Harvest the worker's file to a root path before the judge opens it:
    # O_NOFOLLOW + regular-file + owner + size, so a symlinked observations file
    # cannot redirect the judge's read.
    safe_obs = work / "observations.json"
    problem = harvest(obs, safe_obs, drop.pw_uid)
    if problem:
        report["observations_problem"] = problem

    # Root, stdlib only, submission NOT importable — PYTHONPATH empty. It reads
    # source under SUBMISSION_SRC (the clone was made `core.symlinks=false`, so a
    # "symlink" in the push is an inert regular file, never a traversal).
    #
    # Its HOME and TMPDIR are ROOT-owned, and python runs with -I. The judge used
    # to inherit the worker's HOME, and root's python enables the user site
    # directory under whatever HOME says -- so the worker (agent code, as nobody)
    # could write ~/.local/lib/python3.X/site-packages/usercustomize.py and have it
    # executed as uid 0 when the judge started, with /logs/verifier in reach.
    # Reproduced in the world image before this change. -I drops the user site,
    # every PYTHON* variable and the script's own directory from sys.path; the
    # judges that need a sibling module insert their (root-owned) directory
    # themselves.
    judge_home = work / "judge-home"
    judge_home.mkdir(mode=0o700)
    judge_env = {"PATH": "/usr/local/bin:/usr/bin:/bin",
                 "LANG": os.environ.get("LANG", "C.UTF-8"),
                 "HOME": str(judge_home), "TMPDIR": str(judge_home),
                 "PYTHONPATH": "", "SUBMISSION_SRC": str(src),
                 "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    # The pristine tree, for a judge that enforces "this function is reused as-is":
    # a ticket can protect code INSIDE a file the task must edit, which no
    # whole-file `protected_files` comparison can express. Same staged copy the
    # worker gets, and root-owned; absent when staging failed, and a judge that
    # needs it must fail the fact rather than pass it blind.
    if base_env.get("CURATOR_BASELINE_DIR"):
        judge_env["CURATOR_BASELINE_DIR"] = base_env["CURATOR_BASELINE_DIR"]
    # -B as well as -I. `-I` ignores every PYTHON* variable, PYTHONDONTWRITEBYTECODE
    # included, so the root judge was free to write a __pycache__ into the suite
    # directory it imports from -- harmless at grading time (/tests is 0700 root) but
    # it is what plants one in a checked-out arm whenever tests/ is writable.
    rc_j, _ = spawn(["python3", "-I", "-B", str(suite_dir / "judge.py"), str(safe_obs),
                     str(LOGS / "junit.xml"), seed, str(artifacts)],
                    judge_env, log, drop=None)
    report["judge_returncode"] = rc_j
    report["ran_as"] = f"worker {DROP_USER}:{DROP_GROUP} ({drop.pw_uid}), judge root"

    (LOGS / "run_report.json").write_text(json.dumps(report, indent=1))
    subprocess.run(["rm", "-rf", str(work)], check=False)
    if log.exists():
        print(log.read_text(errors="replace")[-4000:])
    return 0


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    meta = json.loads((TESTS / "task.json").read_text())
    suite = TESTS / meta["suite"]

    report = {"task": meta["task_id"], "suite": meta["suite"],
              "variant": variant_of(meta)}

    try:
        drop = pwd.getpwnam(DROP_USER)
    except KeyError:
        # Fail loudly rather than fall back to root. A grader that silently
        # regains the privilege it exists to give up is the exact shape of bug
        # this file was rewritten to remove; scoring nothing is recoverable,
        # scoring a forgery is not.
        report["harness_error"] = f"no {DROP_USER!r} user to drop to"
        LOGS.mkdir(parents=True, exist_ok=True)
        (LOGS / "run_report.json").write_text(json.dumps(report, indent=1))
        print(report["harness_error"], file=sys.stderr)
        return 1

    work = make_workdir()
    submission, sha_or_error = clone_pushed_main(work)
    if submission is None:
        report["submission_error"] = sha_or_error
        (LOGS / "run_report.json").write_text(json.dumps(report, indent=1))
        print(f"could not clone {REPO}: {sha_or_error}", file=sys.stderr)
        return 1
    report["submission_sha"] = sha_or_error
    report["submission_path"] = str(submission)
    check_protected(meta, submission, report)

    src = submission / "src"
    if not (src / "bespokelabs" / "curator" / "llm" / "llm.py").exists():
        report["submission_error"] = "no src/bespokelabs/curator/llm/llm.py in main"

    map_hosts(report)
    baseline = stage_baseline(work, report)

    # Three directories the child owns, because pytest and curator both need
    # somewhere to write and it must not be anywhere root reads by name. TMPDIR
    # matters as much as HOME: pytest's `tmp_path` builds `$TMPDIR/pytest-of-
    # nobody`, and on the default /tmp the agent can pre-create that directory —
    # modern pytest then refuses a basetemp owned by someone else and the whole
    # run errors out, which scores like an agent who wrote nothing.
    out, home, tmp = work / "out", work / "home", work / "tmp"
    for path in (out, home, tmp):
        path.mkdir()
        os.chown(path, drop.pw_uid, drop.pw_gid)
        path.chmod(0o700)

    # An allowlist, not `{**os.environ}`. The verifier's environment is root's,
    # and handing it wholesale to agent code is free reconnaissance.
    #
    # The submission is NOT here. `conftest.py` puts it on `sys.path` after the
    # stdlib; on PYTHONPATH it would precede the stdlib and a pushed
    # `src/encodings/__init__.py` or `src/sitecustomize.py` would execute during
    # interpreter startup, before any uid or any test could matter.
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin",
           "LANG": os.environ.get("LANG", "C.UTF-8"),
           "HOME": str(home),
           "TMPDIR": str(tmp),
           "PYTHONPATH": str(TESTS),
           "SUBMISSION_SRC": str(src),
           "PYTHONHASHSEED": "0",
           "PYTHONDONTWRITEBYTECODE": "1",
           "PYTEST_ADDOPTS": "",
           "CURATOR_VENV": VENV}
    if baseline is not None:
        env["CURATOR_BASELINE_DIR"] = str(baseline)

    # A suite that ships `probe.py` + `judge.py` is graded out-of-process: the
    # worker imports the submission and reports values, the judge decides. This
    # is opt-in on purpose — every suite without those two files takes the
    # unchanged pytest path below and grades exactly as before.
    suite_dir = TESTS / meta["suite"]
    if (suite_dir / "probe.py").is_file() and (suite_dir / "judge.py").is_file():
        return run_split(meta, suite_dir, src, work, out, drop, env, report)

    # NON-SPLIT suites only (g12, g13 and the retired t* set): a split suite never
    # reaches this branch, and its arm ships no conftest.py at all.
    # Run FROM /tests with a relative suite path. Pointing pytest at
    # /tests/<suite> makes that directory the rootdir, and /tests/conftest.py —
    # one level above it — is then never loaded: every fixture comes back
    # "not found" and every test errors, which scores exactly like an agent who
    # wrote nothing.
    #
    # rootdir, inifile and confcutdir are pinned explicitly rather than left to
    # discovery. Discovery walks UP from the args looking for pytest.ini /
    # tox.ini / setup.cfg / pyproject.toml and for conftest.py, and every
    # directory it would walk into has to be one the agent cannot write.
    # Pinning them here means that stays true even if someone later moves the
    # rootdir somewhere friendlier.
    ini = TESTS / "pytest.ini"
    if not ini.exists():
        ini.write_text("[pytest]\n")
    cmd = [f"{VENV}/bin/python", "-s", "-P", "-m", "pytest", meta["suite"],
           "-p", "no:cacheprovider", "-q", "-rA",
           "-c", str(ini), f"--rootdir={TESTS}", f"--confcutdir={TESTS}",
           # signal, NOT thread. The thread method cannot interrupt a blocked
           # asyncio loop, so it terminates the whole process — and pytest then
           # never writes junit.xml, so every fact in the suite scores 0 with
           # suite_ok=0. t3 lost both its runs that way: curator really does
           # spin forever in `while not has_capacity(): sleep(0.1)`, which is
           # the very behaviour one of its tests exists to catch. SIGALRM
           # raises inside the test, pytest fails it and carries on.
           "--timeout=180", "--timeout-method=signal",
           f"--junit-xml={out}/junit.xml",
           f"--ctrf={out}/ctrf.json"]

    # Output to a file root opened, not to pipes. `capture_output=True` plus a
    # timeout deadlocks on exactly the input that needs the timeout: a forked
    # grandchild inherits the pipe and keeps `communicate()` blocked after the
    # direct child is killed. `start_new_session` gives the whole tree one
    # process group to kill instead.
    log = LOGS / "pytest.log"
    with open(log, "wb") as fh:
        proc = subprocess.Popen(cmd, env=env, cwd=str(TESTS),
                                stdout=fh, stderr=subprocess.STDOUT,
                                user=DROP_USER, group=DROP_GROUP,
                                extra_groups=[], umask=0o077,
                                start_new_session=True)
        try:
            report["pytest_returncode"] = proc.wait(timeout=PYTEST_TIMEOUT)
        except subprocess.TimeoutExpired:
            report["pytest_timeout"] = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                proc.kill()
            report["pytest_returncode"] = proc.wait(timeout=60)

    problems = [p for p in (harvest(out / "junit.xml", LOGS / "junit.xml", drop.pw_uid),
                            harvest(out / "ctrf.json", LOGS / "ctrf.json", drop.pw_uid))
                if p]
    if problems:
        report["harvest_problems"] = problems
    report["ran_as"] = f"{DROP_USER}:{DROP_GROUP} ({drop.pw_uid})"
    (LOGS / "run_report.json").write_text(json.dumps(report, indent=1))
    subprocess.run(["rm", "-rf", str(work)], check=False)
    print(log.read_text(errors="replace")[-4000:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
