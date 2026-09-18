#!/usr/bin/env python3
"""Turn the pytest run and the provenance checks into Harbor rewards.

Two rules shape this file.

**Every expected key is seeded at 0.0 first.** A suite that could not even be
collected — because the agent broke `bespokelabs.curator` at import, which is a
real and interesting outcome — must produce a full set of zeros rather than a
missing key that reads downstream as "not measured".

**The keys come from `/tests/task.json`, never from a hardcoded list.** A requirement
declares only some of the five fact fields: t1.r2 has no
`exclusions_or_crossover`, t2.r1 has neither `failure_behavior` nor
`observability`, t4.r2 has no `failure_behavior`. Inventing keys for absent
facts would quietly divide every mean by the wrong number.

Runs on the system python3, deliberately: it must still work when the venv or
the submission is the thing that is broken.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import time
import xml.etree.ElementTree as ET

# Overridable only so the scorer can be exercised against fixture directories
# off-container; the verifier never sets either.
TESTS = pathlib.Path(os.environ.get("SCORE_TESTS_DIR", "/tests"))
LOGS = pathlib.Path(os.environ.get("SCORE_LOGS_DIR", "/logs/verifier"))
FACT_FIELDS = ("rule", "scope", "exclusions_or_crossover", "failure_behavior",
               "observability")

# pytest's junit writes `classname` (the module, e.g. "test_r1") and `name` (the
# function). It does NOT write `file` — reconstructing a node id from it yields
# "None::test_..." and matches nothing, which is how a suite where every test
# passed still scored zero across the board.
MODULE_REQ = re.compile(r"(?:^|\.)test_r(?P<req>\d+)$")
MODULE_OPEN = re.compile(r"(?:^|\.)test_open$")
FUNC = re.compile(r"^test_(?P<field>[a-z_]+?)__")

# Test names are readable prose, fact fields are the schema's own words, and
# they are not always the same string. `test_exclusions__...` grades
# `exclusions_or_crossover`; without this the key is never touched and reads as
# a hole in the suite rather than as a pass.
FIELD_ALIAS = {
    "rule": "rule",
    "scope": "scope",
    "exclusions": "exclusions_or_crossover",
    "exclusions_or_crossover": "exclusions_or_crossover",
    "crossover": "exclusions_or_crossover",
    "failure": "failure_behavior",
    "failure_behavior": "failure_behavior",
    "observability": "observability",
}


def expected_keys(meta: dict) -> list[str]:
    task = meta["task_id"]
    keys = [f"{task}.open_feature"]
    for i, req in enumerate(meta["hidden_requirements"], 1):
        for field in FACT_FIELDS:
            if req["requirement"].get(field):
                keys.append(f"{task}.r{i}.{field}")
    return keys


def junit_outcomes(path: pathlib.Path) -> dict[str, str]:
    """"<module>::<test>" -> passed | failed | skipped, from pytest's own XML.

    JUnit rather than the CTRF file because it is core pytest: the CTRF plugin
    is one more thing that can fail to load in an environment the agent may have
    disturbed, and this file's whole job is to keep working when something else
    did not.

    That principle now has teeth, because this file is written by the pytest
    process and that process imports agent-authored code. An absent junit
    already scored a clean zero. A MALFORMED one did not: `ET.parse` raised,
    `main()` died, and no reward.json was written at all — which Harbor reports
    as a broken harness rather than as a failed task. One stray byte in a file
    the submission can reach was a way out of a bad score. So: bounded size, no
    DTD (`xml.etree` expands internal entities, and a few hundred bytes of
    nested ones will sit in the verifier's CPU until Harbor kills it), and every
    parse failure folded to "no outcomes", which is the honest zero.
    """
    if not path.exists():
        return {}
    try:
        if path.stat().st_size > 8 * 1024 * 1024:
            return {}
        raw = path.read_bytes()
    except OSError:
        return {}
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        return {}
    try:
        root = ET.fromstring(raw)
    except (ET.ParseError, ValueError):
        return {}
    out: dict[str, str] = {}
    for case in root.iter("testcase"):
        node = f"{case.get('classname', '')}::{case.get('name', '')}"
        state = "passed"
        for child in case:
            tag = child.tag.lower()
            if tag in ("failure", "error"):
                state = "failed"
                FAILURE_MESSAGES[node] = (child.get("message") or child.text or "")[:2000]
            elif tag == "skipped":
                state = "skipped"
        out[node] = state
    return out


# node -> the junit failure text, so ctrf.json can say WHY a check failed and not
# only that it did. Filled as a side effect of `junit_outcomes`.
FAILURE_MESSAGES: dict[str, str] = {}


def fold(meta: dict, outcomes: dict[str, str], rewards: dict) -> tuple[dict, set]:
    """A key scores 1.0 only if every test mapping to it passed.

    A SKIP means unmeasured, not failed — this is the `gate=False` third state.
    Some facts are not observable in this codebase at all: t2's litellm
    crossover has no reachable batch path to print an estimate from, and
    scoring it zero counts a limit of curator against the agent. An earlier
    version graded it through the post-hoc billing seam instead and failed an
    implementation that was correct.

    Returns (hits, unmeasured). An unmeasured key is dropped from the mean
    rather than pulling it down, and named in the report.
    """
    task = meta["task_id"]
    hits: dict[str, list[str]] = {}
    for node, state in outcomes.items():
        module, _, func = node.partition("::")
        if MODULE_OPEN.search(module):
            key = f"{task}.open_feature"
        else:
            req = MODULE_REQ.search(module)
            name = FUNC.match(func)
            if not (req and name):
                continue
            field = FIELD_ALIAS.get(name.group("field"))
            if not field:
                continue
            key = f"{task}.r{req.group('req')}.{field}"
        hits.setdefault(key, []).append(state)

    unmeasured = set()
    for key, states in hits.items():
        if key not in rewards:
            continue
        if all(s == "skipped" for s in states):
            unmeasured.add(key)
            rewards.pop(key)
            continue
        rewards[key] = 1.0 if all(s == "passed" for s in states) else 0.0
    return hits, unmeasured



def protected_report(meta: dict) -> dict[str, str]:
    """{path: unchanged | modified | deleted | unmeasured} for every protected file.

    `run_suites.py` measures this as root against the pristine tree and writes
    `protected.json` into the root-only /logs/verifier; this only reads it. A
    task that protects nothing returns {}. A task that protects files but has no
    measurement -- the clone failed, the pristine tree was missing -- reads every
    path as `unmeasured`, which does NOT count as unchanged: an instruction the
    grader could not check is not one the submission is known to have kept.
    """
    paths = meta.get("protected_files") or []
    if not paths:
        return {}
    try:
        seen = json.loads((LOGS / "protected.json").read_text())
    except (OSError, ValueError):
        seen = {}
    return {p: seen.get(p, "unmeasured") for p in paths}


def write_ctrf(meta: dict, outcomes: dict[str, str], protected: dict[str, str],
               started: int) -> None:
    """Every discrete check as one CTRF test, at /logs/verifier/ctrf.json.

    Built HERE, from the judge's junit, rather than by a pytest plugin: the split
    suites never run pytest at all -- the worker imports the submission and the
    judge decides -- so the plugin had nothing to attach to and those tasks
    reported a bare reward. This file runs last, as root, on the system python,
    so it is also the one place that still produces a report when the submission
    broke everything upstream. Overwrites whatever a pytest run harvested, so a
    task has one report with one shape.
    """
    tests = []
    for node, state in sorted(outcomes.items()):
        entry = {"name": node, "status": state, "duration": 0,
                 "suite": node.partition("::")[0]}
        if state == "failed" and FAILURE_MESSAGES.get(node):
            entry["message"] = FAILURE_MESSAGES[node]
        tests.append(entry)
    for path, state in sorted(protected.items()):
        entry = {"name": f"protected_files::{path}",
                 "status": "passed" if state == "unchanged" else "failed",
                 "duration": 0, "suite": "protected_files"}
        if state != "unchanged":
            entry["message"] = f"{path} is {state}; the instruction says it does not change"
        tests.append(entry)
    count = {s: sum(1 for t in tests if t["status"] == s)
             for s in ("passed", "failed", "skipped")}
    stop = int(time.time() * 1000)
    (LOGS / "ctrf.json").write_text(json.dumps({"results": {
        "tool": {"name": "sweworld-judge"},
        "summary": {"tests": len(tests), **count, "pending": 0, "other": 0,
                    "start": started, "stop": stop},
        "tests": tests,
    }}, indent=1))


def variant_of(meta: dict) -> str:
    """Which arm this task is: blind, spec, or clues.

    `control` was a boolean when there were only two arms. Tasks built before
    the clues arm still carry it and nothing else, so it stays the fallback.
    """
    return meta.get("variant") or ("spec" if meta.get("control") else "blind")


def main() -> int:
    started = int(time.time() * 1000)
    LOGS.mkdir(parents=True, exist_ok=True)
    meta = json.loads((TESTS / "task.json").read_text())
    task = meta["task_id"]

    keys = expected_keys(meta)
    rewards = {k: 0.0 for k in keys}

    outcomes = junit_outcomes(LOGS / "junit.xml")
    hits, unmeasured = fold(meta, outcomes, rewards)

    # A key the suite never even tried is a hole in the suite, not a failure by
    # the agent, and it should be visible as such rather than read as a zero.
    untested = [k for k in keys if k not in hits]

    hidden = [v for k, v in rewards.items()
              if not k.endswith("open_feature") and k not in unmeasured]
    hidden_mean = round(sum(hidden) / len(hidden), 4) if hidden else 0.0
    # `suite_ok`, not `suite_error`. Same diagnostic, opposite polarity, and the
    # polarity is the whole point: every OTHER key here is higher-is-better, and
    # a consumer that averages the dict has no way to know this one was not.
    # Horizon's validation gate does exactly that -- it means `Final Score` as
    # the mean of every key in reward.json -- so a flawless oracle run came back
    # 0.9411764705882353, which is 16/17, and the gate refused the task for not
    # scoring 1.0. The run was perfect; `suite_error: 0.0` MEANT no error.
    # Nothing reads the old name except archived job records.
    rewards[f"{task}.suite_ok"] = 0.0 if not outcomes else 1.0

    provenance = {}
    prov_file = LOGS / "provenance.json"
    if prov_file.exists():
        provenance = json.loads(prov_file.read_text())
        for name in ("pushed", "ci_green", "deployed"):
            rewards[f"provenance.{name}"] = float(bool(provenance.get(name)))

    protected = protected_report(meta)
    protected_ok = all(v == "unchanged" for v in protected.values())
    if meta.get("protected_files"):
        rewards[f"{task}.protected_unchanged"] = 1.0 if protected_ok else 0.0

    # The headline number, and it is BINARY: 1 only when the ticket's own feature
    # passed, every measured hidden fact passed, and no file the instruction
    # protects was touched. `open_feature` gates it but is still not IN the hidden
    # mean: without the gate a submission could score 1 having recovered the hidden
    # requirements while leaving the ticket it was asked to deliver unbuilt, which
    # is not a solved task. (All ten g11 v11 rollouts passed open_feature, so the
    # gate changed no measured outcome when it was added.) It used to be
    # the hidden mean, and 8 of 9 facts wrote 0.8889 -- partial credit, which
    # makes a trial incomparable with every other task's pass/fail and which the
    # benchmark's binary-reward rule rejects on any reachable path. The mean still
    # exists, in report.json, and every per-fact key above stays 0/1 beside it,
    # so nothing that reads WHICH facts passed loses anything.
    #
    # Still not a conjunction with provenance: this experiment asks whether the
    # requirements are recoverable, and folding a deploy failure into that would
    # answer a different question. Provenance is reported beside it, never
    # inside it. No measured fact at all is a 0, not a vacuous pass.
    passed = bool(hidden) and all(v == 1.0 for v in hidden)
    open_ok = rewards.get(f"{task}.open_feature") == 1.0
    rewards["reward"] = 1.0 if open_ok and passed and protected_ok else 0.0

    # reward.json, singular. Harbor reads /logs/verifier/reward.txt (one
    # float) or /logs/verifier/reward.json (a flat {key: number} dict) and
    # nothing else; any other file name (a plural one was tried) is not found, and the trial
    # fails with "No reward file" having run every test correctly.
    (LOGS / "reward.json").write_text(json.dumps(rewards, indent=1))
    write_ctrf(meta, outcomes, protected, started)
    (LOGS / "report.json").write_text(json.dumps({
        "task": task, "variant": variant_of(meta),
        "hidden_mean": hidden_mean,
        "protected_files": protected,
        "tests_seen": len(outcomes),
        "untested_keys": untested,
        "unmeasured_keys": sorted(unmeasured),
        "outcomes": outcomes,
        "provenance": provenance,
        "run": json.loads((LOGS / "run_report.json").read_text())
        if (LOGS / "run_report.json").exists() else {},
    }, indent=1))

    print(json.dumps(rewards, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
