"""Grade one tree through `run_suites.run_split`, inside the authoring container.

Copied into the container and run there as root by `suite.run_split`; it imports
nothing from this package. It exists so the bracket measures the path a hosted
verifier actually takes. The pytest path `suite.run` uses grades `test_*.py`
in-process, and every Argus finding against g1-g11 was a property of the grader,
not of the tests: the submission's own process rewrote the junit, read the
answers out of `/tests`, or replayed values a fixed fixture made predictable.
None of that is visible to a bracket that never runs the worker and the judge as
separate processes.

`run_suites.run_split` is imported, never reimplemented, with its two path
constants pointed at this run's directory. What `run_suites.main` does before
calling it (clone the pushed tree, build the child's environment) is repeated
here in miniature, because the tree is already on disk and there is no Gitea.

argv: base suite_name [capture_dir]
  base/tests       the staged `_suites` plus this task's suite
  base/tree        the tree under test
  capture_dir      if given, the worker's observations.json and artifacts/ are
                   copied there before the judge runs -- what a replay forgery
                   is built from.
Prints one JSON line: the run report plus the junit path.
"""
import importlib.util
import json
import os
import pathlib
import pwd
import shutil
import sys

base = pathlib.Path(sys.argv[1])
suite_name = sys.argv[2]
capture = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None

spec = importlib.util.spec_from_file_location("run_suites", base / "tests" / "run_suites.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)
rs.TESTS = base / "tests"
rs.LOGS = base / "logs"
rs.LOGS.mkdir(parents=True, exist_ok=True)
rs.LOGS.chmod(0o700)

drop = pwd.getpwnam(rs.DROP_USER)
work = base / "work"
work.mkdir()
work.chmod(0o755)
out, home, tmp = work / "out", work / "home", work / "tmp"
for path in (out, home, tmp):
    path.mkdir()
    os.chown(path, drop.pw_uid, drop.pw_gid)
    path.chmod(0o700)

src = base / "tree" / "src"
env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
       "HOME": str(home), "TMPDIR": str(tmp), "PYTHONPATH": str(rs.TESTS),
       "SUBMISSION_SRC": str(src), "PYTHONHASHSEED": "0",
       "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": "",
       "CURATOR_VENV": rs.VENV}
if rs.BASELINE_TREE.is_dir():
    env["CURATOR_BASELINE_DIR"] = str(rs.BASELINE_TREE)

if capture is not None:
    real_spawn = rs.spawn

    def spawn(cmd, *a, **k):
        result = real_spawn(cmd, *a, **k)
        # The worker's call is the one naming probe.py; its argv is
        # (python, probe.py, observations, seed, artifacts).
        if len(cmd) > 4 and cmd[1].endswith("probe.py"):
            capture.mkdir(parents=True, exist_ok=True)
            if pathlib.Path(cmd[2]).is_file():
                shutil.copy(cmd[2], capture / "observations.json")
            if pathlib.Path(cmd[4]).is_dir():
                shutil.copytree(cmd[4], capture / "art", symlinks=True)
        return result

    rs.spawn = spawn

report = {"suite": suite_name}
rs.run_split({"task_id": "", "suite": suite_name}, rs.TESTS / suite_name, src,
             work, out, drop, env, report)
report["junit"] = str(rs.LOGS / "junit.xml")
print("SPLIT-REPORT " + json.dumps(report))
