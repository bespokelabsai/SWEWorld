"""Per fact: does it discriminate? Answered free, in about a minute.

This is the gate the whole package exists for. The measured bracket over the
seven hand-written tasks found **13 of 29 facts are coincidences** — `naive`, the
obvious implementation written by someone who never saw the requirement, passes
them anyway — and it found that out after roughly seven hours and eight paid
trials whose numbers then had to be discarded. Three trees and one suite answer
the same question in under a minute, deterministically, with no model variance.

Four verdicts, and only one of them ships:

    hidden        pristine fails, naive fails, oracle passes.
    coincidence   naive PASSES. Catalog A. The clue is unnecessary; cut the fact
                  or narrow it until a reasonable blind build fails it.
    vacuous       pristine PASSES. The test does not require the feature to
                  exist, so an untouched checkout scores it — which is what
                  `harness.require_feature` is for.
    broken        oracle FAILS. Either the test is wrong or the requirement is
                  unmeasurable (Catalog B). Never the agent's fault, and never
                  something to tune away by weakening the test.

Two more states that are not verdicts about discrimination but about coverage:
`unmeasured` (every test mapping to the fact skipped) and `untested` (the fact is
declared and nothing grades it — a hole in the suite, not a failure).

Folding is done by `score.fold`, the same function the paid verifier runs, so a
fact key here means exactly what it will mean in `jobs/<job>/result.json`.
"""
from __future__ import annotations

import json
import pathlib

from . import suite
from .model import Task, score_module

# pristine is not a fixture; the other two are required before anything is
# emitted. Order is the order the report's columns appear in.
CANONICAL = ("pristine", "naive", "oracle")

HIDDEN = "hidden"
COINCIDENCE = "coincidence"
VACUOUS = "vacuous"
BROKEN = "broken"
UNMEASURED = "unmeasured"
UNTESTED = "untested"
UNPROVEN = "unproven"
OPEN = "open_feature"


def _rewards(task: Task, outcomes: dict[str, str]) -> tuple[dict[str, float], set[str], list[str]]:
    """One tree's outcomes as {fact key: 1.0|0.0}, plus what went unmeasured.

    Seeds every declared key at 0.0 first, exactly as `score.py` does: a suite
    that could not be collected — because a tree broke `bespokelabs.curator` at
    import, which is a real and interesting outcome — must read as a full set of
    zeros rather than as missing keys.
    """
    score = score_module()
    keys = task.fact_keys()
    rewards = {k: 0.0 for k in keys}
    hits, unmeasured = score.fold(task.meta(), outcomes, rewards)
    untested = [k for k in keys if k not in hits]
    return rewards, unmeasured, untested


def measure(
    task: Task,
    *,
    roles: list[str] | None = None,
    per_test_timeout: int = 120,
) -> dict:
    """Run the suite against every tree and fold the results per fact."""
    tests = task.dir / "tests"
    if not tests.is_dir():
        raise SystemExit(f"no suite at {tests}; run `tg tests {task.slug}` first")

    fixtures = task.dir / "fixtures"
    available = ["pristine"] + sorted(
        p.stem for p in fixtures.glob("*.py") if p.stem != "__init__")
    chosen = roles or available
    missing = [r for r in chosen if r != "pristine" and not (fixtures / f"{r}.py").is_file()]
    if missing:
        raise SystemExit(f"no fixture for {', '.join(missing)} in {fixtures}")

    trees: dict[str, dict] = {}
    for role in chosen:
        fixture = None if role == "pristine" else fixtures / f"{role}.py"
        result = suite.run(fixture, suite_name=task.suite, task_tests=tests,
                           per_test_timeout=per_test_timeout)
        rewards, unmeasured, untested = _rewards(task, result["outcomes"])
        trees[role] = {
            "rewards": rewards,
            "unmeasured": sorted(unmeasured),
            "untested": untested,
            "rc": result["rc"],
            "counts": json.loads(suite.summarise(result)),
            "collected": bool(result["outcomes"]),
            "stdout_tail": result["stdout"][-4000:],
        }
    return {"task": task.id, "suite": task.suite, "trees": trees,
            "verdicts": verdicts(task, trees)}


def verdicts(task: Task, trees: dict[str, dict]) -> dict[str, str]:
    """Fact key -> verdict, from the three canonical trees.

    Ordered so the most damning finding wins: a fact whose oracle fails is
    `broken` however the other trees behaved, because until the requirement can
    be satisfied at all there is nothing to say about whether it discriminates.
    """
    out: dict[str, str] = {}
    have = {role: trees[role] for role in CANONICAL if role in trees}
    # A role that was not run is not evidence. Without `naive` there is nothing
    # to say about whether a fact discriminates, and letting the comparison fall
    # through would print `hidden` for every fact on the strength of not having
    # checked - the exact reassuring-but-empty answer this file exists to refuse.
    absent = [role for role in CANONICAL if role not in have]
    for key in task.fact_keys():
        if key.endswith("open_feature"):
            out[key] = OPEN
            continue
        if absent:
            out[key] = UNPROVEN
            continue
        if any(key in have.get(r, {}).get("untested", []) for r in have):
            out[key] = UNTESTED
            continue
        if any(key in have.get(r, {}).get("unmeasured", []) for r in have):
            out[key] = UNMEASURED
            continue
        oracle = have.get("oracle", {}).get("rewards", {}).get(key)
        pristine = have.get("pristine", {}).get("rewards", {}).get(key)
        naive = have.get("naive", {}).get("rewards", {}).get(key)
        if oracle != 1.0:
            out[key] = BROKEN
        elif pristine == 1.0:
            out[key] = VACUOUS
        elif naive == 1.0:
            out[key] = COINCIDENCE
        else:
            out[key] = HIDDEN
    return out


def ships(measured: dict) -> tuple[bool, list[str]]:
    """Whether this task may be emitted, and every reason it may not.

    Deliberately all-or-nothing on the hidden facts. A task emitted with one
    coincidence in it produces a blind score that cannot be read: the arm is
    down by an amount that is partly retrieval failure and partly a fact that
    was never hidden.
    """
    problems = []
    absent = [role for role in CANONICAL if role not in measured["trees"]]
    if absent:
        problems.append(f"bracket incomplete: {', '.join(absent)} never run")
    open_keys = [k for k, v in measured["verdicts"].items() if v == OPEN]
    for key in open_keys:
        if measured["trees"].get("oracle", {}).get("rewards", {}).get(key) != 1.0:
            problems.append(f"{key}: the open feature does not pass on oracle")
        if measured["trees"].get("pristine", {}).get("rewards", {}).get(key) == 1.0:
            problems.append(f"{key}: the open feature passes on pristine — it is not a feature")
    for key, verdict in measured["verdicts"].items():
        if verdict in (COINCIDENCE, VACUOUS, BROKEN, UNMEASURED, UNTESTED, UNPROVEN):
            problems.append(f"{key}: {verdict}")

    # `spec` is optional -- it costs a build -- but where it was run it is the
    # only evidence about the arm that defines this task's ceiling. `oracle`
    # cannot stand in: it builds from `whole.md`, the author's own full
    # specification, so it shares the author's assumptions and passes names the
    # requirement never states. A fact the spec build misses is not hard, it is
    # unreachable: no arm can score it, the ceiling arm included.
    spec = measured["trees"].get("spec", {}).get("rewards")
    if spec:
        for key, verdict in measured["verdicts"].items():
            if key.endswith("open_feature") or verdict != HIDDEN:
                continue
            if spec.get(key) != 1.0:
                problems.append(
                    f"{key}: unreachable — a build given the ticket and the hidden "
                    "requirements still fails it, so the requirement does not say "
                    "what the suite grades")
    return (not problems), problems


def render(task: Task, measured: dict) -> str:
    """The matrix, as a table, with the verdict spelled out per fact."""
    roles = [r for r in CANONICAL if r in measured["trees"]]
    roles += [r for r in measured["trees"] if r not in roles]
    lines = [f"# Bracket — {task.id} ({task.slug})", ""]

    for role in roles:
        tree = measured["trees"][role]
        note = "" if tree["collected"] else "  **suite did not collect**"
        lines.append(f"- `{role}`: {tree['counts']} rc={tree['rc']}{note}")
    lines += ["", "| fact | " + " | ".join(f"`{r}`" for r in roles) + " | verdict |",
              "|---|" + "---|" * (len(roles) + 1)]

    def cell(role: str, key: str) -> str:
        tree = measured["trees"][role]
        if key in tree["untested"]:
            return "·"
        if key in tree["unmeasured"]:
            return "skip"
        return "pass" if tree["rewards"].get(key) == 1.0 else "fail"

    for key, verdict in measured["verdicts"].items():
        row = " | ".join(cell(r, key) for r in roles)
        mark = verdict if verdict in (HIDDEN, OPEN) else f"**{verdict}**"
        lines.append(f"| `{key}` | {row} | {mark} |")

    ok, problems = ships(measured)
    lines += ["", f"**Ships:** {'yes' if ok else 'no'}"]
    for problem in problems:
        lines.append(f"- {problem}")
    return "\n".join(lines) + "\n"
