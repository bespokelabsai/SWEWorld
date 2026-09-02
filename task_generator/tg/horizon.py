"""Emit the same task as Horizon (apex) tasks, one per arm.

Horizon runs evaluations **hosted**, which is the reason to bother: a harbor
trial wants 4 CPUs and 13000 MB and this box has 4 and 15 GB, so two arms cannot
overlap and neither can share the machine with anything else. Hosted arms have no
such contention, and `horizon tasks validate -m hosted -a oracle|-a noop` is this
package's own bracket in Horizon's idiom.

What a Horizon task is, and how this task maps onto it:

    task.yaml     the prompt. This is the ARM: blind gets the ticket, spec gets
                  the ticket plus every hidden requirement.
    Dockerfile    FROM apex_arena:base, plus curator's dependency closure and a
                  checkout of curator at /workdir/curator for the agent to edit.
    grader.py     `grade(transcript) -> GradingResult(score, subscores, weights)`.
                  `subscores` takes the SAME keys harbor uses (`g1.r1.rule`), so a
                  hosted number and a harbor number mean the same thing.
    solution.sh   the reference solution: apply `fixtures/oracle.patch`.
    tests/        copied to /tests, which apex_arena creates `chmod 0700` and
                  root-owned. Their own quality checker states it: "Agents CANNOT
                  access /tests". That is what makes it safe to ship the suite and
                  the oracle patch inside the image at all.

Two runtime facts shape the Dockerfile:

**The container is network-isolated at run time** (`apex setup` blocks internet
via iptables), so curator's dependencies have to be installed at BUILD time.

**curator itself must not be installed.** `src/bespokelabs/__init__.py` is a
regular package, so an installed copy would shadow the agent's tree and every
test would grade the vendored snapshot. Same reason, same trick as
`harbor_tasks/_env/Dockerfile`: install the wheel for its dependency closure,
then uninstall just the package.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil

from . import surface
from .model import REPO, Task, declared_facts

VENDOR = REPO / "vendor" / "curator-461b4170b966.tar.gz"
CURATOR_VERSION = "0.1.29"
ARMS = ("blind", "spec", "clues")

PREAMBLE = """You are an engineer on the team that maintains `bespokelabs/curator`.

The repository is checked out at `/workdir/curator` — a normal working tree, yours
to edit. It is a `src` layout: the package lives at
`/workdir/curator/src/bespokelabs/curator/`.

To run anything against it, put the source tree on the path:

    cd /workdir/curator && PYTHONPATH=/workdir/curator/src python3 -c '...'

curator's dependencies are installed; curator itself deliberately is not, so your
tree is what gets imported. There is no network.

Your work is graded from the tree at `/workdir/curator`. Nothing needs to be
committed or pushed.

---

## The ticket

"""

CLUES_SECTION = """

---

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on,
oldest first. Some of it is people thinking aloud and some of it was settled later.

Nobody ever states a requirement outright. What is settled is settled across
several of these, by people who each only saw part of it.

"""

SPEC_SECTION = """

---

## Requirements settled earlier

These were agreed before the ticket was written. They are not optional.

"""

DOCKERFILE = """# {name} — {arm} arm of {task_id}
FROM apex_arena:base

# curator's dependency closure WITHOUT curator. `src/bespokelabs/__init__.py` is a
# regular package, so an installed copy would shadow the agent's tree and every
# test would grade the vendored snapshot instead of the submission. Installing the
# wheel and then removing only the package is how the closure is obtained.
# Done at build time because the eval container has no network.
RUN pip install --no-cache-dir "bespokelabs-curator=={version}" \\
 && pip uninstall -y bespokelabs-curator \\
 && pip install --no-cache-dir pytest pytest-timeout

# Pillow, forced. The base image carries Debian's python3-pil 9.0.1 at
# /usr/lib/python3/dist-packages WITHOUT its `_imaging` C extension, and pip
# reports "Requirement already satisfied: Pillow in /usr/lib/python3/dist-packages"
# and installs nothing -- so curator's own dependency install leaves the broken copy
# in place. `curator/types/prompt.py` imports PIL, so `bespokelabs.curator` then
# fails PART WAY through its __init__ and never lands in sys.modules, and the next
# lookup raises `KeyError: 'bespokelabs.curator'` from the import machinery. That
# KeyError is what the grader sees; the ImportError underneath it is invisible.
RUN pip install --no-cache-dir --ignore-installed Pillow

# Fail the BUILD, not the grade. Without this the image ships happily and every
# fact scores 0 for a reason no one can read from the result -- which cost five
# hosted round trips before the ImportError above was found.
RUN python3 -c "import datasets, pydantic, PIL, PIL._imaging, pytest; print('deps ok')"

# The tree the agent works in.
COPY ./tests/curator-src.tar.gz /tmp/curator-src.tar.gz
RUN mkdir -p /workdir/curator \\
 && tar xzf /tmp/curator-src.tar.gz -C /workdir/curator \\
 && rm /tmp/curator-src.tar.gz \\
 && chown -R model:model /workdir/curator

# The submission tree must import against those deps before anything is graded.
RUN PYTHONPATH=/workdir/curator/src python3 -c \
    "import bespokelabs.curator; print('curator imports from the tree')"

# ------------ DONOT CHANGE --------------
COPY ./tests/ /tests/
COPY ./solution.sh /tests/
COPY ./grader.py /tests/
COPY ./data /workdir/data
RUN chown -R model:model /workdir/data && chmod -R 700 /workdir/data
# No chown/chmod of /tests here. apex_arena already creates it root-owned and
# 0700 — that is what keeps the suite away from the agent — and re-applying it
# from the task locked solution.sh out of the files beside it.
"""

# The patch is EMBEDDED, not read from a file beside this script.
#
# `/tests` is root-owned and 0700 (apex_arena creates it that way, which is what
# keeps the suite away from the agent). solution.sh runs from there but not as a
# user that can read its neighbours: a first version shipped the patch as
# `/tests/oracle.patch` and hosted oracle validation failed with `can't open patch
# '/tests/oracle.patch': Permission denied` — a permissions fault that reads like a
# broken reference solution. A heredoc has no permissions of its own.
SOLUTION = """#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
{patch}
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
"""

CONFTEST = '''"""Environment for the grading suite, set at IMPORT time.

Deliberately thinner than `harbor_tasks/_suites/conftest.py`, and only in the ways
this suite allows: it drives no sockets, so the fake provider and the /etc/hosts
mapping that file carries have nothing to do here. What is kept is the one thing
that file calls load-bearing — the environment set BEFORE any curator import,
because `curator/log.py` reads `CURATOR_DISABLE_RICH_DISPLAY` when it is imported
and a function-scoped fixture runs long after that.

The other thing kept is `_unshadow_bespokelabs_siblings`, lifted verbatim. A first
version of this file dropped it -- the reasoning was that this suite drives no
sockets, so the fake provider and the /etc/hosts mapping had nothing to do here,
and the unshadow looked like part of the same machinery. It is not: it is about the
`bespokelabs` NAME. Hosted collection then died with `KeyError:
\'bespokelabs.curator\'` in the import machinery, three collection errors, every
fact scored 0 -- while the identical suite passed 11/11 in a local container.
When trimming a file whose own docstring says two things are load-bearing, keep
both.
"""
import os

os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")
'''

GRADER = '''"""Grade the tree at /workdir/curator, one subscore per hidden fact.

The subscore keys are the keys `harbor_tasks/_suites/score.py` produces
(`{task_id}.r1.rule`), so a hosted number and a harbor number are the same
measurement of the same thing. The junit-to-key mapping mirrors that file: the
fact a test grades is read out of the test's own name, and a key scores 1.0 only
if every test mapping to it passed.

`score` is the hidden mean, deliberately excluding the open feature — the question
this experiment asks is whether requirements nobody wrote down are recoverable,
and folding in "did they build the stated feature" would answer a different one.
The open feature is reported beside it with weight 0.
"""
import json
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

from apex_arena._types import GradingResult

TESTS = pathlib.Path("/tests")
SUITE = TESTS / "suite"
TREE = pathlib.Path("/workdir/curator")
JUNIT = pathlib.Path("/tmp/grade-junit.xml")

FACT_KEYS = {fact_keys!r}
OPEN_KEY = {open_key!r}

# Weights must sum to 1.0. apex_arena's `Grade.__post_init__` enforces it with
# `np.isclose(sum(weights.values()), 1)` and raises otherwise -- and `horizon tasks
# validate` does NOT go through that path, so a grader with weights summing to 10
# validates green at oracle 1.0 and then dies the moment a real evaluation runs it:
#   ValueError: weights must sum to 1.0; got 10.000000
# Computed and checked at emit time rather than here, so the numbers are visible in
# the file and cannot drift from the key list.
WEIGHTS = {weights!r}

# pytest's junit writes `classname` (the module) and `name` (the function); it does
# NOT write `file`. Reconstructing a node id from `file` yields "None::test_..."
# and matches nothing, which is how a suite where every test passed once scored
# zero across the board.
MODULE_REQ = re.compile(r"(?:^|\\.)test_r(?P<req>\\d+)$")
MODULE_OPEN = re.compile(r"(?:^|\\.)test_open$")
FUNC = re.compile(r"^test_(?P<field>[a-z_]+?)__")
FIELD_ALIAS = {{
    "rule": "rule", "scope": "scope",
    "exclusions": "exclusions_or_crossover",
    "exclusions_or_crossover": "exclusions_or_crossover",
    "crossover": "exclusions_or_crossover",
    "failure": "failure_behavior", "failure_behavior": "failure_behavior",
    "observability": "observability",
}}


def _run():
    done = subprocess.run(
        ["python3", "-m", "pytest", str(SUITE), "-q", "-p", "no:cacheprovider",
         f"--junitxml={{JUNIT}}", "--timeout=120", "--timeout-method=signal"],
        cwd=str(SUITE), capture_output=True, text=True, timeout=1800,
        env={{"PYTHONPATH": f"{{TREE}}/src:{{SUITE}}",
             "CURATOR_DISABLE_RICH_DISPLAY": "1", "TELEMETRY_ENABLED": "false",
             "CURATOR_VIEWER": "false", "HF_HUB_OFFLINE": "1",
             "HF_DATASETS_OFFLINE": "1", "OPENAI_API_KEY": "sk-verifier",
             "ANTHROPIC_API_KEY": "sk-verifier", "COLUMNS": "220",
             "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"}})
    return done


def _outcomes():
    if not JUNIT.exists():
        return {{}}
    out = {{}}
    for case in ET.parse(JUNIT).getroot().iter("testcase"):
        node = f"{{case.get('classname', '')}}::{{case.get('name', '')}}"
        state = "passed"
        for child in case:
            tag = child.tag.lower()
            if tag in ("failure", "error"):
                state = "failed"
            elif tag == "skipped":
                state = "skipped"
        out[node] = state
    return out


def grade(transcript):
    done = _run()
    outcomes = _outcomes()

    # Every expected key seeded at 0.0 first: a suite that could not be collected
    # -- because the agent broke `bespokelabs.curator` at import, a real and
    # interesting outcome -- must read as a full set of zeros rather than as
    # missing keys.
    hits = {{}}
    for node, state in outcomes.items():
        module, _, func = node.partition("::")
        if MODULE_OPEN.search(module):
            key = OPEN_KEY
        else:
            req, name = MODULE_REQ.search(module), FUNC.match(func)
            if not (req and name):
                continue
            field = FIELD_ALIAS.get(name.group("field"))
            if not field:
                continue
            key = f"{task_id}.r{{req.group('req')}}.{{field}}"
        hits.setdefault(key, []).append(state)

    subscores = {{key: 0.0 for key in FACT_KEYS}}
    subscores[OPEN_KEY] = 0.0
    for key, states in hits.items():
        if key in subscores:
            subscores[key] = 1.0 if all(s == "passed" for s in states) else 0.0

    # The open feature carries weight 0: this experiment asks whether requirements
    # nobody wrote down are recoverable, and folding in "did they build the stated
    # feature" would answer a different question. It stays in `subscores` so it is
    # still reported. With equal weights summing to 1 across the hidden facts,
    # apex_arena's own `computed_score` equals the hidden mean below, so the
    # explicit score and the derived one agree.
    weights = dict(WEIGHTS)

    hidden = [subscores[k] for k in FACT_KEYS]
    score = round(sum(hidden) / len(hidden), 4) if hidden else 0.0

    recovered = [k for k in FACT_KEYS if subscores[k] == 1.0]
    missed = [k for k in FACT_KEYS if subscores[k] == 0.0]
    feedback = (
        f"{{len(recovered)}} of {{len(FACT_KEYS)}} hidden requirements satisfied. "
        f"Open feature: {{'yes' if subscores[OPEN_KEY] == 1.0 else 'no'}}. "
        + (f"Missed: {{', '.join(missed)}}." if missed else "Nothing missed."))
    # Diagnostics go in FEEDBACK, not in `details`. Horizon strips `details` from
    # the validation result it returns, so a first hosted run that scored 0 on
    # every fact could not be told apart from a suite that never collected -- and
    # the same suite passed 11/11 in a local container with the identical
    # environment. `feedback` survives; a bounded tail of pytest's own output is
    # the difference between one round trip and five.
    empty_classnames = sum(1 for node in outcomes if node.startswith("::"))
    if not outcomes:
        feedback = ("The grading suite produced no junit at all -- pytest did not "
                    "run or died before writing it. " + feedback)
    elif empty_classnames:
        feedback = (f"{{empty_classnames}} junit entries have no classname, which is "
                    "what pytest writes for a COLLECTION error rather than a test "
                    "failure -- the suite could not be imported. " + feedback)
    if score < 1.0:
        # splitlines/join rather than a backslash escape: this template is
        # emitted through .format(), and an escape written here arrives in the
        # generated grader as a real newline inside a string literal.
        tail = " | ".join((done.stdout + done.stderr).split(chr(10)))[-1400:]
        feedback += f"  [pytest rc={{done.returncode}} nodes={{len(outcomes)}}] {{tail}}"

    return GradingResult(
        score=score, subscores=subscores, weights=weights, feedback=feedback,
        details={{"outcomes": outcomes, "pytest_rc": done.returncode,
                 "pytest_tail": (done.stdout + done.stderr)[-4000:]}})
'''

TASK_YAML = """prompt: |
{prompt}
metadata:
    category: "Software Engineering"
    difficulty: "{difficulty}"
    tags:
{tags}
    memory_limit: 8192
    time_limit: 3600
"""


def weights_for(fact_keys: list[str], open_key: str) -> dict[str, float]:
    """Equal weight on every hidden fact, zero on the open feature, summing to <= 1.

    Two different apex_arena checks pull in opposite directions, and only one of
    them has a tolerance:

        sum(weights.values())            must satisfy np.isclose(..., 1)
        sum(subscores[k] * weights[k])   must satisfy 0 <= x <= 1, EXACTLY

    So landing a hair under one is safe and landing a hair over one is fatal. A
    first version folded the `1/n` remainder onto the last key to make the sum
    exactly 1.0; that pushed the last weight to 0.10000000000000012 and an
    all-passing submission then computed 1.0000000000000002, which is not <= 1:

        ValueError: weighted computed score must be in [0, 1]; got 1.000000

    Hence: uniform shares, and the remainder taken OFF the last key when binary
    floating point overshoots, never added. Both of their sums iterate the same
    dict in the same order, so a dict that is under one here is under one there.
    """
    if not fact_keys:
        return {open_key: 1.0}
    share = 1.0 / len(fact_keys)
    weights = {key: share for key in fact_keys}
    excess = sum(weights.values()) - 1.0
    if excess > 0:
        weights[fact_keys[-1]] -= excess
    weights[open_key] = 0.0
    total = sum(weights.values())
    if total > 1.0 or abs(total - 1.0) > 1e-9:
        raise SystemExit(f"weights sum to {total!r}; must be <= 1.0 and close to it")
    return weights


def unshadow_source() -> str:
    """`_unshadow_bespokelabs_siblings` lifted verbatim from the harbor conftest.

    Read from the file rather than copied into a template string: the grader and
    conftest templates here go through `.format()`, and a backslash escape written
    into one of them arrives in the generated file as a literal newline. Taking the
    text at emit time also means there is one definition of this function, in
    `harbor_tasks/_suites/conftest.py`, and it cannot drift.
    """
    source = (REPO / "harbor_tasks" / "_suites" / "conftest.py").read_text()
    start = source.index("def _unshadow_bespokelabs_siblings()")
    end = source.index("\n_unshadow_bespokelabs_siblings()", start)
    return source[start:end].rstrip() + "\n\n\n_unshadow_bespokelabs_siblings()\n"


def _indent(text: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join((pad + line) if line.strip() else "" for line in text.splitlines())


def prompt_for(task: Task, arm: str) -> str:
    body = PREAMBLE + (task.dir / "ticket.md").read_text().split("\n", 1)[1].strip()
    if arm == "clues":
        body += CLUES_SECTION + render_remarks(task)
    if arm == "spec":
        rows = []
        for number, req in enumerate(task.hidden_requirements, 1):
            rows.append(f"### r{number}\n")
            for field, value in (req.get("requirement") or {}).items():
                rows.append(f"- **{field}** — {value}")
            rows.append("")
        body += SPEC_SECTION + "\n".join(rows)
    return body


def render_remarks(task: Task) -> str:
    """The plant as a corpus excerpt, in the shape `clue_digest.render()` emits.

    Date, room and speaker, oldest first, clues and herrings interleaved and
    unlabelled -- a reader cannot be told which remarks were later overturned,
    because working out that a decision was reversed is part of the task. Every
    field that would give the answer away (`settles`, `covers`, `subconclusion`,
    `verbatim`) stays out.
    """
    plant = task.dir / "clues" / "plant.json"
    if not plant.is_file():
        raise SystemExit(f"no plant at {plant}; run `cli.py clues {task.slug}` first")
    data = json.loads(plant.read_text())
    rows = [clue for req in data["tasks"][0]["requirements"] for clue in req["clues"]]
    rows.sort(key=lambda c: ((c.get("carrier") or {}).get("date") or "", c["clue_id"]))

    out = []
    for clue in rows:
        car = clue.get("carrier") or {}
        if not car.get("date"):
            continue          # unplaced: it exists nowhere, so nobody could read it
        where = car.get("room") or car.get("channel") or "somewhere"
        if where.startswith("page:"):
            where = f"wiki: {car.get('title') or where[5:]}"
        elif where.startswith("thread:"):
            where = f"mail: {car.get('title') or 'internal thread'}"
        body = "\n".join("> " + line for line in clue["text"].splitlines())
        out.append(f"**{car['date']} · {where} · {clue['holder']}**\n\n{body}\n")
    return "\n".join(out)


def unsolvable(task: Task) -> list[str]:
    """Names the suite reaches for that the rendered digest never says.

    Checked against the digest rather than `plant.json` because the digest is what
    the arm actually shows: an unplaced remark, or one whose adaptation lost the
    identifier, is not in it. The first clues arm cost ten rollouts to discover
    `plan_fingerprint` was missing; this is the same discovery, free, before the push.
    """
    digest = render_remarks(task)
    out = []
    for req_id, need in surface.required(task).items():
        for name in surface.unsaid(need.all_names, [digest]):
            out.append(f"{req_id}: no remark says `{name}`")
    return out


# What an apex_arena image gives a suite: `/workdir` is the agent's tree,
# `/tests` the root-owned suite, `/tmp` scratch. Plus ordinary Linux, which is
# named explicitly so the check does not fire on `/dev/null`.
HOSTED_ROOTS = ("/workdir", "/tests", "/tmp",
                "/dev", "/proc", "/sys", "/usr", "/bin", "/sbin", "/lib")

# SWEWorld's own furniture, present in the `devbox` the bracket runs in and in
# no hosted image. Listed only to say so in the message -- everything off
# HOSTED_ROOTS is refused anyway, because the failure mode of guessing wrong
# here is a silent hosted zero and the cost of a false positive is one comment.
WORLD_ROOTS = ("/opt/world-state", "/opt/sweworld", "/etc/sweworld",
               "/var/lib/world", "/opt/mattermost", "/run/mysqld")

LITERAL_PATH = re.compile(r"""["'](/[A-Za-z0-9_][A-Za-z0-9_./-]*)["']""")


def unhosted_paths(suite_src: pathlib.Path) -> list[str]:
    """Paths a test names that no Horizon image provides.

    g3 shipped a suite reading `/opt/world-state/input/curator` — SWEWorld's
    pristine checkout, present in the `devbox` the bracket runs in and in no
    apex_arena image. It scored oracle 10 of 10 locally and 0.8889 hosted, on a
    bare FileNotFoundError, and cost a push and a six-minute Cloud Batch round
    trip to find. The bracket cannot catch this: it runs in the container that
    makes the path true.

    Only the task's own `test_*.py` are checked. `harness.py` is the ONE place
    allowed to know where a baseline lives -- it names `/opt/world-state` and
    then guards it -- so a test that reaches around `harness.baseline_text()`
    for a path of its own is the thing this refuses.
    """
    problems = []
    for path in sorted(suite_src.glob("test_*.py")):
        src = path.read_text(encoding="utf-8", errors="replace")
        for found in sorted(set(LITERAL_PATH.findall(src))):
            if found.startswith(HOSTED_ROOTS):
                continue
            why = ("is SWEWorld's, and exists in no hosted image"
                   if found.startswith(WORLD_ROOTS)
                   else "is not a path a hosted image is known to have")
            problems.append(f"{path.name}: names {found!r}, which {why}; "
                            "read a baseline through harness.baseline_text()")
        if re.search(r"^from harness import .*\bBASELINE\b", src, re.M):
            problems.append(f"{path.name}: imports BASELINE; use "
                            "harness.baseline_text(), which falls back to the "
                            "tarball at /tests and returns None rather than raising")
    return problems


def emit(task: Task, arms: tuple[str, ...] = ARMS,
         force: bool = False) -> dict[str, pathlib.Path]:
    root = task.dir / "horizon"
    root.mkdir(parents=True, exist_ok=True)
    if not VENDOR.is_file():
        raise SystemExit(f"no vendored curator tarball at {VENDOR}")
    if "clues" in arms and not force:
        problems = unsolvable(task)
        if problems:
            raise SystemExit(
                "refusing to emit the clues arm — the graded surface is not in it:\n  "
                + "\n  ".join(problems)
                + "\n\nre-run `cli.py clues` (the tree stage is told these names now), "
                  "or pass --force to measure it anyway.")

    suite_src = task.dir / "tests"
    patch = task.dir / "fixtures" / "oracle.patch"
    for needed in (suite_src, patch):
        if not needed.exists():
            raise SystemExit(f"missing {needed}")

    # Before the push, not after: a hosted validation costs a Cloud Batch round
    # trip to say the same thing, and says it as a score rather than as a path.
    if not force:
        unhosted = unhosted_paths(suite_src)
        if unhosted:
            raise SystemExit(
                "refusing to emit — the suite reads paths this image does not have:"
                "\n  " + "\n  ".join(unhosted)
                + "\n\nfix the suite, or pass --force to emit it anyway.")

    fact_keys = task.hidden_keys()
    open_key = f"{task.id}.open_feature"
    made = {}

    for arm in arms:
        name = f"{task.id}-{task.slug}" + ("" if arm == "blind" else f"-{arm}")
        out = root / name
        # `.horizon/metadata.json` is the binding to the task on the server, written
        # by the first `horizon tasks push`. Losing it makes the next push create a
        # SECOND task rather than a new version of this one, which is how a project
        # accumulates near-duplicate tasks nobody can tell apart. Re-emitting
        # replaces the task's content and keeps its identity.
        binding = None
        if (out / ".horizon" / "metadata.json").is_file():
            binding = (out / ".horizon" / "metadata.json").read_text()
        if out.exists():
            shutil.rmtree(out)
        (out / "tests" / "suite").mkdir(parents=True)
        if binding:
            (out / ".horizon").mkdir(parents=True, exist_ok=True)
            (out / ".horizon" / "metadata.json").write_text(binding)
        (out / "data").mkdir(parents=True)

        # A REAL file, not the template's empty `.empty` placeholder. `horizon
        # tasks push` drops zero-byte files, so `data/` did not exist in the
        # build context and the template's `COPY ./data /workdir/data` failed
        # with BuildKit's "failed to calculate checksum of ref" — which names no
        # path and reads like a platform fault rather than a missing directory.
        (out / "data" / "README.md").write_text(
            "This task has no separate data files. The material is the curator\n"
            "checkout at /workdir/curator.\n")
        (out / "task.yaml").write_text(TASK_YAML.format(
            prompt=_indent(prompt_for(task, arm)),
            difficulty="Hard" if arm == "blind" else "Medium",
            tags="\n".join(f'        - "{t}"' for t in
                           ("curator", "python", "hidden-requirements", arm,
                            task.id, "task_generator")),
        ))
        (out / "Dockerfile").write_text(DOCKERFILE.format(
            name=name, arm=arm, task_id=task.id, version=CURATOR_VERSION))
        body = patch.read_text()
        if "CURATOR_ORACLE_PATCH_EOF" in body:
            raise SystemExit("the patch contains the heredoc delimiter; pick another")
        (out / "solution.sh").write_text(SOLUTION.format(patch=body.rstrip("\n")))
        (out / "solution.sh").chmod(0o755)
        (out / "grader.py").write_text(GRADER.format(
            task_id=task.id, fact_keys=fact_keys, open_key=open_key,
            weights=weights_for(fact_keys, open_key)))

        for path in sorted(suite_src.glob("test_*.py")):
            shutil.copy2(path, out / "tests" / "suite" / path.name)
        (out / "tests" / "suite" / "conftest.py").write_text(
            CONFTEST + "\n\n" + unshadow_source())
        shutil.copy2(REPO / "harbor_tasks" / "_suites" / "harness.py",
                     out / "tests" / "suite" / "harness.py")
        shutil.copy2(VENDOR, out / "tests" / "curator-src.tar.gz")
        (out / "tests" / "facts.json").write_text(
            json.dumps({"task_id": task.id, "arm": arm, "fact_keys": fact_keys,
                        "open_key": open_key}, indent=1) + "\n")
        made[arm] = out
    return made


CORPUS_SECTION = """

---

## What the team said

Every conversation in the company's chat, wiki and mail that touched this area,
oldest first, exactly as it sits in the corpus. Nothing here is summarised and
nothing is marked: these are whole exchanges, and most of what is in them is not
about your ticket.
"""


def render_exchanges(task: Task) -> str:
    """The planted material as CORPUS, not as a list of remarks.

    `render_remarks` shows one line per remark -- the sentence the plant intends,
    handed over whole. That is the ceiling arm, and it answers "can an agent USE
    this information". It cannot answer "is the information still all there after
    the remarks were split across conversations", because it never shows the split.

    This does. Same task, same facts, but the reader gets the seven-turn exchange
    each remark was spread across, filler and all. A fact the suite scores from
    this is a fact the corpus genuinely contains; a fact it cannot is one that
    fragmenting destroyed, and no amount of searching would recover it.
    """
    ledger = json.loads((task.dir / "clues" / "plant.json").read_text())
    rows = []
    for entry in ledger["tasks"]:
        for req in entry["requirements"]:
            for clue in req["clues"]:
                carrier = clue.get("carrier")
                if not carrier:
                    continue
                turns = (clue.get("invented") or {}).get("messages") or [
                    {"author": clue["holder"], "text": clue["text"]}]
                rows.append((carrier.get("date") or "", carrier.get("room")
                             or f"#{carrier.get('channel', '')}", turns))
    out = []
    for date, room, turns in sorted(rows, key=lambda r: (r[0], r[1])):
        out.append(f"\n**{date} · {room}**\n")
        for msg in turns:
            who = msg.get("author") or msg.get("sender") or "?"
            body = (msg.get("text") or msg.get("body") or "").replace("\n", " ")
            out.append(f"> **{who}:** {body}")
    return "\n".join(out) + "\n"
