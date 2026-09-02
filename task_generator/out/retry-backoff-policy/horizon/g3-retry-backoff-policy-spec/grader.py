"""Grade the tree at /workdir/curator, one subscore per hidden fact.

The subscore keys are the keys `harbor_tasks/_suites/score.py` produces
(`g3.r1.rule`), so a hosted number and a harbor number are the same
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

FACT_KEYS = ['g3.r1.rule', 'g3.r1.scope', 'g3.r1.exclusions_or_crossover', 'g3.r1.failure_behavior', 'g3.r1.observability', 'g3.r2.rule', 'g3.r2.scope', 'g3.r2.exclusions_or_crossover', 'g3.r2.observability']
OPEN_KEY = 'g3.open_feature'

# Weights must sum to 1.0. apex_arena's `Grade.__post_init__` enforces it with
# `np.isclose(sum(weights.values()), 1)` and raises otherwise -- and `horizon tasks
# validate` does NOT go through that path, so a grader with weights summing to 10
# validates green at oracle 1.0 and then dies the moment a real evaluation runs it:
#   ValueError: weights must sum to 1.0; got 10.000000
# Computed and checked at emit time rather than here, so the numbers are visible in
# the file and cannot drift from the key list.
WEIGHTS = {'g3.r1.rule': 0.1111111111111111, 'g3.r1.scope': 0.1111111111111111, 'g3.r1.exclusions_or_crossover': 0.1111111111111111, 'g3.r1.failure_behavior': 0.1111111111111111, 'g3.r1.observability': 0.1111111111111111, 'g3.r2.rule': 0.1111111111111111, 'g3.r2.scope': 0.1111111111111111, 'g3.r2.exclusions_or_crossover': 0.1111111111111111, 'g3.r2.observability': 0.11111111111111088, 'g3.open_feature': 0.0}

# pytest's junit writes `classname` (the module) and `name` (the function); it does
# NOT write `file`. Reconstructing a node id from `file` yields "None::test_..."
# and matches nothing, which is how a suite where every test passed once scored
# zero across the board.
MODULE_REQ = re.compile(r"(?:^|\.)test_r(?P<req>\d+)$")
MODULE_OPEN = re.compile(r"(?:^|\.)test_open$")
FUNC = re.compile(r"^test_(?P<field>[a-z_]+?)__")
FIELD_ALIAS = {
    "rule": "rule", "scope": "scope",
    "exclusions": "exclusions_or_crossover",
    "exclusions_or_crossover": "exclusions_or_crossover",
    "crossover": "exclusions_or_crossover",
    "failure": "failure_behavior", "failure_behavior": "failure_behavior",
    "observability": "observability",
}


def _run():
    done = subprocess.run(
        ["python3", "-m", "pytest", str(SUITE), "-q", "-p", "no:cacheprovider",
         f"--junitxml={JUNIT}", "--timeout=120", "--timeout-method=signal"],
        cwd=str(SUITE), capture_output=True, text=True, timeout=1800,
        env={"PYTHONPATH": f"{TREE}/src:{SUITE}",
             "CURATOR_DISABLE_RICH_DISPLAY": "1", "TELEMETRY_ENABLED": "false",
             "CURATOR_VIEWER": "false", "HF_HUB_OFFLINE": "1",
             "HF_DATASETS_OFFLINE": "1", "OPENAI_API_KEY": "sk-verifier",
             "ANTHROPIC_API_KEY": "sk-verifier", "COLUMNS": "220",
             "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"})
    return done


def _outcomes():
    if not JUNIT.exists():
        return {}
    out = {}
    for case in ET.parse(JUNIT).getroot().iter("testcase"):
        node = f"{case.get('classname', '')}::{case.get('name', '')}"
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
    hits = {}
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
            key = f"g3.r{req.group('req')}.{field}"
        hits.setdefault(key, []).append(state)

    subscores = {key: 0.0 for key in FACT_KEYS}
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
        f"{len(recovered)} of {len(FACT_KEYS)} hidden requirements satisfied. "
        f"Open feature: {'yes' if subscores[OPEN_KEY] == 1.0 else 'no'}. "
        + (f"Missed: {', '.join(missed)}." if missed else "Nothing missed."))
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
        feedback = (f"{empty_classnames} junit entries have no classname, which is "
                    "what pytest writes for a COLLECTION error rather than a test "
                    "failure -- the suite could not be imported. " + feedback)
    if score < 1.0:
        # splitlines/join rather than a backslash escape: this template is
        # emitted through .format(), and an escape written here arrives in the
        # generated grader as a real newline inside a string literal.
        tail = " | ".join((done.stdout + done.stderr).split(chr(10)))[-1400:]
        feedback += f"  [pytest rc={done.returncode} nodes={len(outcomes)}] {tail}"

    return GradingResult(
        score=score, subscores=subscores, weights=weights, feedback=feedback,
        details={"outcomes": outcomes, "pytest_rc": done.returncode,
                 "pytest_tail": (done.stdout + done.stderr)[-4000:]})
