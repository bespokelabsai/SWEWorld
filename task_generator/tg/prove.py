"""Is the plant solvable? Build from the clues alone and let the suite answer.

Phase 3 proves solvability by closed-book reconstruct-then-grade: a model reads the
clues, writes down what it thinks the requirement was, and another model marks it.
It has to work that way, because a phase-3 task has no executable grader.

A generated task does, so the proof here is the real thing rather than a proxy. An
agent is given the ticket and the remarks -- byte for byte what the hosted clues arm
shows -- it builds an implementation, and the same suite that scores the paid arm
scores that tree. A fact that fails here fails there.

Why bother when the hosted arm exists: this costs a couple of dollars and about four
minutes against thirty minutes and a queue, and it hands back the assertion text.
`plan_id` holding `0-2:307;2-4:307;4-5:153` instead of its own hash names the
ambiguous remark. A hosted 0.60 says only that something is wrong.

`surface.py` and this module are two halves and neither replaces the other. That one
is free and catches a name nobody said. This one costs money and catches everything
else: a name said in a form that reads as a noun, a value stated by somebody nobody
believed, a chain of reasoning missing a step in the middle.
"""
from __future__ import annotations

import json
import re

from . import bracket, emit, steps
from .model import Task, load

# pytest prints `FAILED path::name - AssertionError: text`. The text is the whole
# point of proving locally, so it is kept rather than reduced to a pass or a fail.
FAILURE = re.compile(r"^FAILED\s+(?P<node>\S+)\s+-\s+(?P<why>.*)$", re.M)


def build_once(task, slug: str, *, rebuild: bool, budget: float,
               source: str = "remarks") -> dict:
    """One build from the digest, scored. Fact key -> (passed, assertion text)."""
    if rebuild:
        patch, lines = steps.build(slug, "clues", budget=budget,
                                   source=source)
        if not lines:
            raise SystemExit(f"the clues build changed nothing ({patch})")

    measured = bracket.measure(task, roles=["clues"])
    tree = measured["trees"]["clues"]
    if not tree["collected"]:
        raise SystemExit("the suite did not collect:\n" + tree["stdout_tail"])

    why = {m.group("node").split("::")[-1]: m.group("why").strip()
           for m in FAILURE.finditer(tree["stdout_tail"])}
    graded = emit.suite_facts(task.dir / "tests", task.id)
    out = {}
    for key, reward in sorted(tree["rewards"].items()):
        tests = [ref.split("::")[-1] for ref in graded.get(key, [])]
        out[key] = {"passed": reward == 1.0,
                    "why": "; ".join(why[t] for t in tests if t in why)}
    return out


def prove(slug: str, *, rebuild: bool = True, budget: float = 8.0,
          runs: int = 3, source: str = "remarks") -> dict:
    """Build from ticket + clues N times, score each, fail a fact that ever fails.

    N, and not one, because the thing this catches is stochastic and one sample
    cannot see it. `g1.r1.l6` said "the string `plan_fingerprint` hashed was
    0-2:307;..." -- which reads as the string the function RETURNS -- and three
    builds in five implemented it that way. A single-build proof returned 11 of 11
    on that plant, and went on returning 11 of 11 through four hosted versions
    scoring 0.48 to 0.79. Five harbor rollouts at half an hour each found what
    three builds at ninety seconds would have.

    A fact that passes twice and fails once is a defect, not noise. It is the same
    defect on every rollout that hits it; the rollouts just do not all hit it.
    """
    task = load(slug)
    per_run = [build_once(task, slug, rebuild=rebuild, budget=budget,
                          source=source)
               for _ in range(max(1, runs))]

    facts = {}
    for key in sorted(per_run[0]):
        rows = [r.get(key, {"passed": False, "why": "not graded in this run"})
                for r in per_run]
        hits = [r["passed"] for r in rows]
        facts[key] = {
            "passed": all(hits),
            "per_run": hits,
            "rate": f"{sum(hits)}/{len(hits)}",
            # The assertion from a run that FAILED. The passing runs have nothing
            # to say and averaging the text of the two is meaningless.
            "why": next((r["why"] for r in rows if not r["passed"] and r["why"]), ""),
        }
    out = {"slug": slug, "task": task.id, "runs": len(per_run),
           "source": source, "facts": facts,
           "passed": sum(1 for f in facts.values() if f["passed"]), "total": len(facts)}
    (task.dir / "clues").mkdir(parents=True, exist_ok=True)
    (task.dir / "clues" / "proof.json").write_text(json.dumps(out, indent=1) + "\n")
    (task.dir / "clues" / "proof.md").write_text(render(task, out))
    return out


def failures(proof: dict) -> dict[str, str]:
    """Fact key -> the assertion that says the remarks did not carry it."""
    return {key: row["why"] for key, row in proof["facts"].items() if not row["passed"]}


def render(task: Task, proof: dict) -> str:
    n = proof.get("runs", 1)
    lines = [f"# Can the clues alone build {task.id}?", "",
             f"**{proof['passed']} of {proof['total']}** facts score against a tree "
             f"built from the ticket and the planted remarks and nothing else, "
             f"on every one of {n} build(s).", "",
             "Read the grid, not the total. Facts that fail *together*, on the same "
             "runs, are one defect in one remark — not variance, and not one problem "
             "each. Find it before sampling again.", "",
             "| fact | " + " | ".join(f"#{i + 1}" for i in range(n))
             + " | why not |",
             "|---|" + "---|" * n + "---|"]
    for key, row in sorted(proof["facts"].items()):
        marks = " | ".join("ok" if hit else "**FAIL**"
                           for hit in row.get("per_run", [row["passed"]]))
        reason = row["why"].replace("|", "\\|")[:240]
        lines.append(f"| `{key}` | {marks} | {reason} |")
    lines += ["", "A failure here is a defect in the plant, not in the agent: the same "
                  "suite scores 11 of 11 against the oracle, which was built from the "
                  "specification these remarks are supposed to carry."]
    return "\n".join(lines) + "\n"
