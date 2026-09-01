#!/usr/bin/env python3
"""Turn the pytest run and the provenance checks into Harbor rewards.

Two rules shape this file.

**Every expected key is seeded at 0.0 first.** A suite that could not even be
collected — because the agent broke `bespokelabs.curator` at import, which is a
real and interesting outcome — must produce a full set of zeros rather than a
missing key that reads downstream as "not measured".

**The keys come from `tasks.json`, never from a hardcoded list.** A requirement
declares only some of the five fact fields: t1.r2 has no
`exclusions_or_crossover`, t2.r1 has neither `failure_behavior` nor
`observability`, t4.r2 has no `failure_behavior`. Inventing keys for absent
facts would quietly divide every mean by the wrong number.

Runs on the system python3, deliberately: it must still work when the venv or
the submission is the thing that is broken.
"""
from __future__ import annotations

import json
import pathlib
import re
import xml.etree.ElementTree as ET

TESTS = pathlib.Path("/tests")
LOGS = pathlib.Path("/logs/verifier")
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
    """
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
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



def variant_of(meta: dict) -> str:
    """Which arm this task is: blind, spec, or clues.

    `control` was a boolean when there were only two arms. Tasks built before
    the clues arm still carry it and nothing else, so it stays the fallback.
    """
    return meta.get("variant") or ("spec" if meta.get("control") else "blind")


def main() -> int:
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
    rewards[f"{task}.hidden_mean"] = (
        round(sum(hidden) / len(hidden), 4) if hidden else 0.0)
    rewards[f"{task}.suite_error"] = 1.0 if not outcomes else 0.0

    provenance = {}
    prov_file = LOGS / "provenance.json"
    if prov_file.exists():
        provenance = json.loads(prov_file.read_text())
        for name in ("pushed", "ci_green", "deployed"):
            rewards[f"provenance.{name}"] = float(bool(provenance.get(name)))

    # The headline number. Deliberately the hidden mean and NOT a conjunction
    # with provenance: this experiment asks whether the requirements are
    # recoverable, and folding a deploy failure into that would answer a
    # different question. Provenance is reported beside it, never inside it.
    rewards["reward"] = rewards[f"{task}.hidden_mean"]

    # reward.json, singular. Harbor reads /logs/verifier/reward.txt (one
    # float) or /logs/verifier/reward.json (a flat {key: number} dict) and
    # nothing else; a file named rewards.json is not found, and the trial
    # fails with "No reward file" having run every test correctly.
    (LOGS / "reward.json").write_text(json.dumps(rewards, indent=1))
    (LOGS / "report.json").write_text(json.dumps({
        "task": task, "variant": variant_of(meta),
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
