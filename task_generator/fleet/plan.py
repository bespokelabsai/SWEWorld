"""The phase graph: which steps, in what order, and which phase gets to run.

The stage list is IMPORTED from `tg.recipe.STAGES`, never copied. That file is
already "the order g1 was actually built in", with the gate flags and the
per-stage budgets, and a second hand-maintained copy here would drift the first
time somebody inserted a stage in one and not the other -- which is exactly the
"one producer, four consumers, four private guesses" entry in tasks/lessons.md.

What this module adds is only what `recipe` has no entry for:

  * the phase boundaries. `recipe` is one flat list; the fleet has to stop at
    the end of B and refuse to start C without being told to.
  * a second `bracket` after `trim`. The README says to re-run it because trim
    changes what the spec arm is handed, and `recipe.STAGES` does not have that
    row -- a person re-typing it is what "walked one stage at a time" meant.
  * everything on Horizon, which is typed by hand today and appears in no
    script anywhere in the repo.

`horizon` appears in two phases with different `--arms`, and that is the point
of the split: phase B emits blind and spec ONLY, so nothing renders a clues arm
-- and therefore nothing runs `horizon.unsolvable()` -- before there is a plant
to render. Phase C re-emits with all three.
"""
from __future__ import annotations

import dataclasses
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tg import recipe                                          # noqa: E402

PHASES = ("A", "B", "C", "D")


@dataclasses.dataclass(frozen=True)
class Step:
    name: str                    # unique within the run; the log file's stem
    phase: str
    kind: str                    # "cli" | "hosted" | "check"
    cmd: str = ""                # cli subcommand, or hosted.py function name
    args: tuple[str, ...] = ()
    gate: bool = False           # a bad outcome stops the task (via the judge)
    paid: float = 0.0
    note: str = ""

    @property
    def label(self) -> str:
        return " ".join((self.cmd or self.name,) + self.args)


def _recipe_slice(first: str, last: str) -> list[recipe.Stage]:
    """The stages from `first` to `last` inclusive, in recipe order.

    By name, and it raises rather than returning a short list, because a
    silently-empty phase would run nothing and report success.
    """
    names = [s.name for s in recipe.STAGES]
    for edge in (first, last):
        if edge not in names:
            raise SystemExit(f"plan.py names stage {edge!r}, which tg/recipe.py does not have")
    lo, hi = names.index(first), len(names) - 1 - names[::-1].index(last)
    return recipe.STAGES[lo:hi + 1]


def _step_name(stage: recipe.Stage) -> str:
    """A short, filesystem-safe name. `build --role naive` -> `build.naive`.

    The name is the log file's stem, so it has to survive a shell and stay
    readable in a status table -- `build--rolenaive` is neither.
    """
    if not stage.args:
        return stage.name
    value = stage.args[-1]
    return f"{stage.name}.{value.replace(',', '+')}"


def _from_recipe(stage: recipe.Stage, phase: str) -> Step:
    return Step(name=_step_name(stage), phase=phase, kind="cli", cmd=stage.name,
                args=stage.args, gate=stage.gate, paid=stage.paid, note=stage.note)


def phase_a() -> list[Step]:
    """The cut, through to the harbor artifacts. ~$19."""
    steps = [_from_recipe(s, "A") for s in _recipe_slice("new", "emit")]
    # `audit` is `optional=True` in the recipe and has never been run on any
    # task. The fleet runs it and routes a non-zero exit to the judge rather
    # than blocking on it: an adversarial detector nothing has ever calibrated
    # is evidence, not a verdict. "Skipping it is a decision; make it one."
    steps = [dataclasses.replace(s, gate=False) if s.cmd == "audit" else s for s in steps]
    # The README's re-bracket after trim, which recipe.STAGES has no row for.
    # trim rewrites hidden.md, which is what the spec arm is handed, so the
    # spec-reachability half of ships() is measuring a requirement that no
    # longer exists until this runs.
    at = next(i for i, s in enumerate(steps) if s.cmd == "emit")
    steps.insert(at, Step("bracket.retrim", "A", "cli", "bracket", gate=True,
                          note="GATE: trim rewrote hidden.md; re-measure before emit"))
    return steps


def phase_b() -> list[Step]:
    """Spec and blind, proven on Horizon. The whole of v1's verdict. ~$30."""
    return [
        Step("horizon.ab", "B", "cli", "horizon", ("--arms", "blind,spec"), gate=True,
             note="emit the two apex arms; NOT clues -- there is no plant yet"),
        Step("push", "B", "hosted", "push", gate=True,
             note="push blind and spec; the name must be piped or push exits 0 having done nothing"),
        Step("validate", "B", "hosted", "validate", gate=True,
             note="GATE: hosted oracle must be 1.00 and noop 0.00 on both arms"),
        Step("evaluate", "B", "hosted", "evaluate", gate=True, paid=30.0,
             note="submit, watch, pull rollouts"),
        Step("verdict", "B", "check", "verdict_ab", gate=True,
             note="GATE: spec ~1.00, blind ~0.00 with open_feature at 1.0"),
    ]


def phase_c() -> list[Step]:
    """The plant. Written now, run only when `--through C` is named. ~$75."""
    steps = [_from_recipe(s, "C") for s in _recipe_slice("clues", "horizon")]
    return steps + [
        Step("push.clues", "C", "hosted", "push_clues", gate=True),
        Step("validate.clues", "C", "hosted", "validate_clues", gate=True),
        Step("evaluate.clues", "C", "hosted", "evaluate_clues", gate=True, paid=30.0),
        Step("verdict.clues", "C", "check", "verdict_clues", gate=True,
             note="GATE: the clues arm passes most of the time"),
    ]


def phase_d() -> list[Step]:
    """The in-world arm. NOT BUILT in v1 -- this is the seam it plugs into.

    Deliberately raises rather than returning an empty list: a phase that
    silently does nothing reports success, and "the fleet finished phase D"
    would then mean the opposite of what it says.
    """
    raise SystemExit(
        "phase D (the in-world arm) is not built in v1. The seam: `cli inject`, "
        "then `build_tasks.py --extra-tasks ... --pick <id> --world --hosted`, "
        "then push to mini-batch fde8a4a1-21d7-4f76-b153-6cfe480b82ff (sweworld). "
        "No image re-bake -- environment/setup.sh ingests /opt/task-plant at "
        "container start.")


BUILDERS = {"A": phase_a, "B": phase_b, "C": phase_c, "D": phase_d}


def steps_through(through: str) -> list[Step]:
    """Every step from phase A up to and including `through`."""
    if through not in PHASES:
        raise SystemExit(f"--through must be one of {', '.join(PHASES)}, not {through!r}")
    out: list[Step] = []
    for phase in PHASES[:PHASES.index(through) + 1]:
        out += BUILDERS[phase]()
    return out


def steps_for(phase: str) -> list[Step]:
    return BUILDERS[phase]()
