"""Write the harbor artifacts, and refuse to if the task is not ready.

Three destinations, all of them shapes `harbor_tasks/` already understands:

    harbor_tasks/_suites/<suite>/            the graders, copied into every arm
    harbor_tasks/<id>-<slug>/fixtures/       oracle.py + naive.py, for the bracket
    task_generator/tasks.generated.json      the `--extra-tasks` file build_tasks reads

Nothing here is a new format. `tasks.generated.json` entries are `tasks.json`
entries plus the three things a hand-written one gets from its position in that
file (`id`, `slug`, `suite`), because ids in `data_gen/input/tasks.json` are
POSITIONAL — `t1`..`t60` — and a generated task is not in it.

Two gates, both refusing rather than warning:

**The bracket must ship.** Emitting a task with one coincidence in it produces a
blind score nobody can read: the arm is down by an amount that is partly the
agent failing to find the corpus and partly a fact that was never hidden.

**Facts and tests must be a bijection.** `score.py` reads the fact a test grades
out of the test's own function name. A declared fact with no test scores zero for
reasons that are not the agent's; a test naming a field the requirement never
declared scores nothing at all and silently does no work.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil

from . import bracket
from .model import REPO, SUITES, Task, declared_facts, score_module

GENERATED = REPO / "task_generator" / "tasks.generated.json"
HARBOR = REPO / "harbor_tasks"

DEF = re.compile(r"^\s*def (test_[A-Za-z0-9_]+)\s*\(", re.M)


def suite_facts(tests: pathlib.Path, task_id: str) -> dict[str, list[str]]:
    """Fact key -> the test functions that grade it, by the grader's own rules."""
    score = score_module()
    found: dict[str, list[str]] = {}
    for path in sorted(tests.glob("test_*.py")):
        module = path.stem
        for name in DEF.findall(path.read_text()):
            if score.MODULE_OPEN.search(module):
                found.setdefault(f"{task_id}.open_feature", []).append(f"{module}::{name}")
                continue
            req = score.MODULE_REQ.search(module)
            field = score.FUNC.match(name)
            if not (req and field):
                found.setdefault("UNMAPPED", []).append(f"{module}::{name}")
                continue
            resolved = score.FIELD_ALIAS.get(field.group("field"))
            if not resolved:
                found.setdefault("UNMAPPED", []).append(f"{module}::{name}")
                continue
            found.setdefault(f"{task_id}.r{req.group('req')}.{resolved}", []).append(
                f"{module}::{name}")
    return found


def check_bijection(task: Task) -> list[str]:
    tests = task.dir / "tests"
    if not tests.is_dir():
        return [f"no suite at {tests}"]
    found = suite_facts(tests, task.id)
    problems = []
    for name in found.pop("UNMAPPED", []):
        problems.append(f"{name}: name maps to no fact key — the grader would ignore it")
    declared = set(task.fact_keys())
    for key in sorted(declared - set(found)):
        problems.append(f"{key}: declared and nothing grades it")
    for key in sorted(set(found) - declared):
        problems.append(f"{key}: graded by {found[key]} but the requirement never declares it")
    for key, names in sorted(found.items()):
        if key in declared and len(names) > 1:
            problems.append(
                f"{key}: graded by {len(names)} tests ({', '.join(names)}); the key scores "
                "only when all of them pass, so write one decisive test")
    return problems


def emit(slug: str, *, force: bool = False) -> dict:
    from .model import load
    task = load(slug)

    problems = check_bijection(task)
    measured_file = task.dir / "bracket.json"
    if measured_file.is_file():
        ok, bracket_problems = bracket.ships(json.loads(measured_file.read_text()))
        problems += [] if ok else [f"bracket: {p}" for p in bracket_problems]
    else:
        problems.append("bracket: never measured; run `tg bracket` first")

    if problems and not force:
        raise SystemExit("refusing to emit:\n  " + "\n  ".join(problems))

    # Not overridable by --force: a suite without the split is graded in the
    # submission's own process (run_suites falls back to pytest), which is the
    # grading forgery Argus found in every g task before the port. A forced emit
    # of that is a task that can be scored without being solved.
    from . import suite as suite_mod
    if not suite_mod.is_split(task.dir / "tests"):
        raise SystemExit(
            f"refusing to emit: {task.dir / 'tests'} has no probe.py + judge.py. "
            "Write the worker/judge split (prompts/write_tests.md) and re-run "
            "`cli bracket`; --force does not skip this.")

    suite_dst = SUITES / task.suite
    # Not overridable by --force. A suite on the worker/judge split grades from
    # probe.py + judge.py, which exist only in `_suites`; `out/<slug>/tests`
    # holds the older test_*.py alone. Replacing one with the other deleted the
    # judge, and `run_suites.py` then fell back to in-process pytest as the
    # submission's own uid -- the grading forgery the split was built to close --
    # while reporting nothing unusual.
    if (suite_dst / "judge.py").exists() and not (task.dir / "tests" / "judge.py").exists():
        raise SystemExit(
            f"refusing to emit: {suite_dst} grades through probe.py/judge.py and "
            f"{task.dir / 'tests'} does not. Emitting would put the forgeable "
            "in-process grader back. Edit the suite in _suites directly.")
    if suite_dst.exists():
        shutil.rmtree(suite_dst)
    shutil.copytree(task.dir / "tests", suite_dst,
                    ignore=shutil.ignore_patterns("__pycache__"))

    fixtures_dst = HARBOR / task.group / "fixtures"
    fixtures_dst.mkdir(parents=True, exist_ok=True)
    for path in sorted((task.dir / "fixtures").iterdir()):
        if path.suffix in (".py", ".patch"):
            shutil.copy2(path, fixtures_dst / path.name)

    rows = json.loads(GENERATED.read_text()) if GENERATED.is_file() else []
    rows = [r for r in rows if r.get("id") != task.id] + [task.entry()]
    rows.sort(key=lambda r: r["id"])
    GENERATED.write_text(json.dumps(rows, indent=1) + "\n")

    return {"suite": str(suite_dst), "fixtures": str(fixtures_dst),
            "generated": str(GENERATED), "problems": problems}
