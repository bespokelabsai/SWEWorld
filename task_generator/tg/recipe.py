"""The stages, in order, with what each one gates on and what the last task paid.

`cli.py` has twenty-three subcommands and the README documents nineteen of them
across two code blocks that do not say which are gates, which cost money, or which
you can skip. g1 was built by running them in an order that had to be worked out,
and three of the gates it needed were wired to commands nobody runs on the way
through -- `unreversed` only to `reverse`, `out_of_order` only to `reorder`,
`horizon.unsolvable` only to `--arms clues` when `--arms` defaults to blind,spec.
`audit` was never run at all, and nothing said it had been skipped.

So this is not automation for its own sake. It is the answer to "what do I run next,
and is it safe to stop here" -- which is the question that cost most of the four days.

The costs are measured, out of `out/batch-payload-plan/spend.json`: 557 calls,
$88.56, four calendar days. They are one task's numbers on one area, so treat them
as an order of magnitude. The shape is the part that generalises, and the shape is
that **the clues arm is two thirds of the bill** and placement alone is a third.

`budget` is what to expect on the next task; `spent` is what this one has actually
paid, attributed by `spend.json` label. They differ where a stage was run more times
than the recipe calls for -- g1 proved seven times before the sampling was built in,
so its `spent` is $12.90 against a three-build budget of $5.50.

`tests` and `audit` budget $0.00 because neither wrote a spend row on g1 -- `tests`
has the largest per-call budget in the package and `audit` never ran at all. A zero
there means unmeasured, not free.
"""
from __future__ import annotations

import dataclasses
import json
import subprocess
import sys

from .model import OUT, load


@dataclasses.dataclass
class Stage:
    name: str
    args: tuple[str, ...] = ()
    paid: float = 0.0            # what to budget, from g1's numbers
    gate: bool = False           # a non-zero exit means stop
    optional: bool = False       # skipped unless asked for
    makes: str = ""              # a path under out/<slug>/, for "already done"
    note: str = ""
    # Which `spend.json` labels belong to this stage. Explicit, because the label
    # is not the command: the clue stages all write `clue-<something>-<clue id>`,
    # and `prove` spends under `build-clues` because a proof IS a build, and `reknit` spends
    # under `clue-thread` and `clue-carry` because writing an exchange and checking it
    # carries the remark are two calls.
    labels: tuple[str, ...] = ()

    @property
    def label(self) -> str:
        return " ".join((self.name,) + self.args)


# The order g1 was actually built in. `split` before `tests` because a test file
# has to know its fact keys; `emit` before `clues` because the clue stages read the
# emitted suite through `surface.required`.
STAGES = [
    Stage("new", paid=0, makes="brief.md",
          note="you write the brief by hand — see README, it is the one input"),
    Stage("author", paid=5.79, makes="whole.md", labels=("author",),
          note="the whole spec, nothing hidden yet"),
    Stage("build", ("--role", "oracle"), paid=3.49, makes="fixtures/oracle.patch",
          labels=("build-oracle",)),
    Stage("split", paid=1.26, gate=True, makes="task.json", labels=("split",),
          note="GATE: every fact needs an invented anchor the ticket does not print"),
    Stage("tests", paid=0.0, gate=True, makes="tests/test_r1.py", labels=("tests",),
          note="unmeasured on g1; largest per-call budget in the package"),
    Stage("build", ("--role", "naive"), paid=1.93, makes="fixtures/naive.patch",
          labels=("build-naive",)),
    Stage("bracket", paid=0, gate=True, makes="bracket.json",
          note="GATE, free, ~1 min: every fact must read `hidden`"),
    Stage("audit", paid=0.0, gate=True, optional=True, makes="audit.json",
          labels=("audit",),
          note="never run on g1. Skipping is a decision; make it one"),
    Stage("trim", paid=2.95, makes="trim.json", labels=("trim",),
          note="cut each requirement to what its assertions check"),
    Stage("emit", paid=0, gate=True, makes="../../harbor_tasks/_suites",
          note="GATE: refuses unless the bracket shipped"),
    Stage("clues", paid=45.0, gate=True, makes="clues/plant.json",
          labels=("clue-tree", "clue-place", "clue-conv", "clue-doc",
                  "clue-mail", "clue-herring"),
          note="the expensive one — ~175 placement calls, two thirds of the bill"),
    Stage("settle", paid=10.73, makes="clues/claims.json",
          labels=("clue-claims", "clue-settle"),
          note="every graded assertion said outright, not left to be inferred"),
    Stage("reverse", paid=1.0, gate=True, labels=("clue-reversal",),
          note="GATE: a herring nothing retracts is a herring forever"),
    Stage("reknit", paid=9.0, gate=True,
          labels=("clue-thread", "clue-carry", "clue-reknit"),
          note="GATE: turn each remark into the exchange it was made in — the "
               "step that makes a plant into a corpus rather than a list"),
    # NOT optional. It is a gate, and `make` skips optional stages by default, so
    # `out_of_order` -- which only `reorder` reads -- went unrun on the happy path
    # and eight chronology inversions shipped in g1's plant.
    Stage("reorder", paid=1.0, gate=True,
          note="a decision dated before the complaint it answers"),
    Stage("prove", ("--runs", "3"), paid=5.5, gate=True, makes="clues/proof.json",
          labels=("build-clues",),
          note="GATE, ~$1.84 a build: the defect this catches is stochastic, so "
               "three. One build returned 11/11 on a plant that scored 0.48"),
    Stage("horizon", ("--arms", "blind,spec,clues"), paid=0, gate=True,
          makes="horizon/results.json",
          note="GATE on the clues arm only, which is why the arms are named"),
    Stage("inject", paid=0, gate=True, optional=True, makes="clues/injected.md",
          note="write the plant into a copy of the corpus, for the in-world arm"),
]

TRIALS = "then measure: cli.py trial <slug> --arm blind | spec | clues  (~25 min, ~$7 each)"


def spent(slug: str) -> list[dict]:
    """Every spend row this task has written, for `render` to attribute."""
    path = OUT / slug / "spend.json"
    return json.loads(path.read_text()) if path.is_file() else []


def paid_for(stage: Stage, rows: list[dict]) -> float:
    return sum(r["cost_usd"] for r in rows
               if any(r["label"] == p or r["label"].startswith(p + "-")
                      for p in stage.labels))


def plan(slug: str, *, start: str = "", optional: bool = False) -> list[Stage]:
    stages = [s for s in STAGES if optional or not s.optional]
    if start:
        names = [s.name for s in stages]
        if start not in names:
            raise SystemExit(f"no stage named {start!r}; one of {', '.join(names)}")
        stages = stages[names.index(start):]
    return stages


def render(slug: str, stages: list[Stage]) -> str:
    rows = spent(slug)
    lines = [f"{'stage':32} {'gate':5} {'budget':>8} {'spent':>8}  note", "-" * 104]
    here_total = 0.0
    for stage in stages:
        here = paid_for(stage, rows)
        here_total += here
        lines.append(f"{stage.label:32} {'GATE' if stage.gate else '':5} "
                     f"{stage.paid:8.2f} {here:8.2f}  {stage.note[:48]}")
    unattributed = sum(r["cost_usd"] for r in rows) - here_total
    lines += ["-" * 104,
              f"{'':32} {'':5} {sum(s.paid for s in stages):8.2f} {here_total:8.2f}"]
    if abs(unattributed) > 0.01:
        lines.append(f"{'(repairs, replacements, retries)':32} {'':5} "
                     f"{'':8} {unattributed:8.2f}")
    return "\n".join(lines + ["", TRIALS])


def make(slug: str, *, start: str = "", optional: bool = False,
         dry_run: bool = False) -> int:
    load(slug)                      # fails loudly if the slug is not a task
    stages = plan(slug, start=start, optional=optional)
    if dry_run:
        print(render(slug, stages))
        return 0
    for stage in stages:
        print(f"\n=== {stage.label}" + (" [GATE]" if stage.gate else ""))
        rc = subprocess.call([sys.executable, "cli.py", stage.name, slug,
                              *stage.args])
        if rc and stage.gate:
            print(f"\n{stage.label} did not pass. Fix what it printed, then:\n"
                  f"  cli.py make {slug} --from {stage.name}")
            return rc
        if rc:
            print(f"  ({stage.label} exited {rc}; not a gate, carrying on)")
    print(f"\nevery stage passed.\n{TRIALS}")
    return 0
