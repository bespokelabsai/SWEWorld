"""One task, walked. The thing five threads each run a copy of.

Every step is `python3 cli.py <cmd> <slug> [args]` in a subprocess -- exactly
what a person types -- and the worker's whole job is the four things a person
does around that:

  1. take the right lock first (`locks.STAGE_LOCKS`),
  2. check there is budget left,
  3. read what the step WROTE rather than what it returned, and
  4. when that reading is a judgement, ask `judge.py` and carry out one action
     from a closed enum.

`cli.py make` is not used and could not be: it "cannot tell a fatal exit from an
advisory one -- `split` and `bracket` both exit non-zero on a heuristic, and a
driver that stops on every non-zero exit stops on a perfectly good artifact
while a driver that ignores them spends $19 into a cut that was already dead."
Telling those apart is what steps 3 and 4 are.

Rewinds are bounded (`MAX_REWINDS`) because the two interesting actions are both
loops if nothing stops them: a bracket that still reports coincidences after an
`author --extend` will ask for another one, and each is $3 and twenty minutes.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tg import steps as tg_steps                               # noqa: E402
from tg.model import REPO, Task, load                          # noqa: E402

from . import gates, hosted, judge, locks, plan, state         # noqa: E402

TG = REPO / "task_generator"

# Every one of these rewrites `clues/plant.json` through `clues.finish()`, which
# recomputes every derived field. They must all be read by `gates.clue_gate`:
# `settle` in particular returns 0 unconditionally, so without this a $10 pass
# that damaged the plant reported success.
PLANT_STAGES = ("clues", "settle", "reverse", "reorder", "reknit", "consistency")

MAX_ATTEMPTS = 2          # per step, for `retry`
# Per task PER PHASE, because a rewind does not cost the same in both.
#
# In phase A a rewind is `author --extend` or `amend_ticket` plus the rebuilds
# behind it -- $15 and half an hour, and if the second one has not fixed the cut
# the third will not either. In phase C the repairs are `rewrite_exchanges`
# (~$1.50 for the exchanges a gate named) and they CONVERGE: measured on g9,
# consistency reported 13 conflicts, then 11, then 7, then 6, each round
# removing real ones. Stopping that at two leaves a fixable plant unfixed.
MAX_REWINDS = {"A": 2, "B": 2, "C": 5}
DEFAULT_MAX_REWINDS = 2
# Measured, not guessed: phase A came in at ~$28/task, and phase C's clue chain
# runs $38-53 on the g4/g6 evidence (g1's $113 was 239 placement calls for 50
# remarks, the pathological case `recipe.py`'s $45 budget is drawn from). Phase
# B's $30 is Horizon spend and never reaches `spend.json`. So ~$81 local/task,
# and the cap is that plus room for one repair round.
PER_TASK_CAP_USD = 150.0


class Parked(Exception):
    """This task stops here. The other four carry on."""


# --------------------------------------------------------------------------- running

def cli(cmd: str, slug: str, args: tuple[str, ...], log: pathlib.Path,
        timeout_s: int = 7200) -> int:
    """Run one `cli.py` subcommand, tee its output to `log`, return the exit code.

    cwd is `task_generator/` because that is where `cli.py` is; the README's own
    alias runs it as `python3 task_generator/cli.py` from the repo root and both
    work, but `recipe.make` shells out to a bare `"cli.py"` and only works from
    here -- so this matches the one that has no ambiguity.
    """
    argv = [sys.executable, "cli.py", cmd, slug, *args]
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w") as handle:
        handle.write(f"$ {' '.join(argv)}\n\n")
        handle.flush()
        done = subprocess.run(argv, cwd=str(TG), stdout=handle,
                              stderr=subprocess.STDOUT, timeout=timeout_s)
    return done.returncode


def held(step: plan.Step):
    """The lock this step needs, as a context manager."""
    kind, name = locks.STAGE_LOCKS.get(step.cmd, (None, None))
    if kind == "flock":
        return locks.flock(name)
    if kind == "devbox":
        return locks.devbox()
    import contextlib
    return contextlib.nullcontext()


def tail(path: pathlib.Path, n: int = 6000) -> str:
    return path.read_text()[-n:] if path.is_file() else ""


# --------------------------------------------------------------------------- gates

def last_conflicts(run_id: str, slug: str) -> set[str] | None:
    """The clues `consistency` named last time it ran, or None if it never has.

    `gates.clue_gate` needs it to tell a conflict that survived a re-read from
    one the judge sampled once -- see the comment there. Read out of the history
    the worker already writes, so it costs nothing.
    """
    rows = state.load(run_id)["tasks"][slug].get("history") or []
    seen = [h for h in rows if h.get("step") == "consistency" and h.get("hard") is not None]
    return gates.named_clues(seen[-1]["hard"]) if seen else None


def evaluate(task: Task, step: plan.Step, rc: int, log: pathlib.Path,
             previous: set[str] | None = None) -> gates.Verdict:
    """What this step actually produced. One branch per step that has an artifact."""
    if step.cmd == "split":
        return gates.split_gate(task, rc)
    if step.cmd == "bracket":
        return gates.bracket_gate(task)
    if step.cmd == "emit":
        return gates.emit_gate(task)
    if step.cmd in PLANT_STAGES:
        return gates.clue_gate(task, previous)
    # Steps with no artifact of their own are judged by their exit code alone,
    # which is honest for them: `author`, `build` and `tests` write files whose
    # correctness the NEXT gate measures, and inventing a check here would be a
    # detector nothing calibrated.
    ok = rc == 0
    return gates.Verdict(step.name, ok,
                         [] if ok else [f"{step.label} exited {rc}"],
                         evidence=tail(log))


def situation_for(step: plan.Step) -> str:
    """Which decision this step's failure is an instance of.

    Everything in `PLANT_STAGES` past `clues` shares one situation: they all end
    in `audit_plant`, whose non-zero exit means "a repair fixes this", and the
    repairs are the same three whichever pass reported it. Before this they fell
    through to `crash`, which offers only retry and stop -- so the guaranteed
    outcome of any plant defect was to pay for the pass twice and park.
    """
    return {"split": "split", "bracket": "bracket", "audit": "audit",
            "tests": "tests", "clues": "clues", "prove": "prove",
            "settle": "plant", "reverse": "plant", "reorder": "plant",
            "reknit": "plant", "consistency": "plant",
            "horizon": "emit_clues"}.get(step.cmd, "crash")


# --------------------------------------------------------------------------- actions

REWINDS = {"resplit": "split", "author_extend": "build.oracle", "amend_ticket": "build.naive",
           # A reformat changes layout and no wording, so no tree it could
           # invalidate has been built yet at `split` time. Carry straight on.
           "reformat_ticket": ""}


def reformat_ticket(task: Task, findings: list[str]) -> None:
    """Re-lay-out the ticket without changing a word of it.

    `steps.unstructured()` refuses a ticket whose longest paragraph runs past
    600 characters, and it is `split` that produces them: the cut compresses a
    whole specification into prose. The ticket is GRADED TEXT -- it is what the
    blind arm is handed and what `emit` ships as `description` -- so the repo's
    own rule is to format it at the cut rather than afterwards.

    The invariant is the one that commit exists for: **zero backticked spans
    dropped**. A reformat that loses a name loses a name the suite may grade, and
    it would look like a formatting change.
    """
    import re

    # Backticks are paired left to right, so a FENCED block (```python) throws
    # the pairing off by three and every "span" after it is the prose BETWEEN
    # two identifiers rather than an identifier. g13's ticket has four fences
    # and the guard below reported six dropped spans that read
    # `` ` does not read it. ` `` -- text, not names. It parked a healthy task
    # on a false positive, and it would do it to any ticket carrying a fence.
    # So fences come out first, and are then checked in their own right: their
    # CONTENT is graded text too, and dropping a whole code block must not
    # become invisible by virtue of being excluded here.
    fenced = lambda text: sorted(re.findall(r"```.*?```", text, flags=re.S))
    spans = lambda text: sorted(
        re.findall(r"`[^`\n]+`", re.sub(r"```.*?```", "", text, flags=re.S)))
    before, before_fenced = spans((task.dir / "ticket.md").read_text()), \
        fenced((task.dir / "ticket.md").read_text())
    snapshot = task.dir / "cuts" / f"pre-reformat-{int(time.time())}"
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in ("task.json", "ticket.md"):
        (snapshot / name).write_text((task.dir / name).read_text())

    text = judge.render("reformat.md", task_id=task.id, slug=task.slug,
                        findings="\n".join(f"- {f}" for f in findings),
                        task_dir=str(task.dir))
    from tg import agent
    result = agent.run(text, repo=REPO, label=f"fleet-reformat-{task.id}",
                       cwd=task.dir, add_dirs=[task.dir], tools="Read,Edit,Grep,Glob",
                       budget_usd=2.0, log_dir=task.dir / "logs", timeout_s=2700)
    tg_steps._record(task, f"fleet-reformat-{task.id}", text, result)

    written = (task.dir / "ticket.md").read_text()
    after, after_fenced = spans(written), fenced(written)
    lost = [s for s in before if s not in after]
    lost_fenced = [s for s in before_fenced if s not in after_fenced]
    if lost or lost_fenced:
        for name in ("task.json", "ticket.md"):
            (task.dir / name).write_text((snapshot / name).read_text())
        raise Parked(f"reformat dropped {len(lost)} backticked span(s) — {lost[:5]} — "
                     f"and {len(lost_fenced)} fenced block(s) — "
                     f"reverted from {snapshot}. Any of them may be graded.")
    described = json.loads((task.dir / "task.json").read_text()).get("description") or ""
    if sorted(set(spans(described))) != sorted(set(after)):
        raise Parked("reformat left ticket.md and task.json's description carrying "
                     "different identifiers; they are the same graded text and must match")


def amend_ticket(task: Task, findings: list[str]) -> None:
    """State a detail the suite grades and the ticket does not, and prove nothing else moved.

    The repair for an `open_feature` that fails on `naive`. It is a ticket
    amendment and NOT another `split`: re-splitting would re-roll which facts
    are hidden, and on g4 that meant discarding a measured 8-of-8 already in
    hand. The invariant is asserted rather than trusted -- `hidden_requirements`
    must be byte-identical before and after, so the fix cannot have softened a
    hidden verdict into a pass.
    """
    before = json.dumps(json.loads((task.dir / "task.json").read_text())["hidden_requirements"],
                        sort_keys=True)
    snapshot = task.dir / "cuts" / f"pre-amend-{int(time.time())}"
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in ("task.json", "ticket.md", "hidden.md", "bracket.json", "bracket.md"):
        if (task.dir / name).is_file():
            (snapshot / name).write_text((task.dir / name).read_text())

    text = judge.render("amend.md", task_id=task.id, slug=task.slug,
                        findings="\n".join(f"- {f}" for f in findings),
                        task_dir=str(task.dir))
    from tg import agent
    result = agent.run(text, repo=REPO, label=f"fleet-amend-{task.id}",
                       cwd=task.dir, add_dirs=[task.dir], tools="Read,Edit,Grep,Glob",
                       budget_usd=2.0, log_dir=task.dir / "logs", timeout_s=2700)
    tg_steps._record(task, f"fleet-amend-{task.id}", text, result)

    after = json.dumps(json.loads((task.dir / "task.json").read_text())["hidden_requirements"],
                       sort_keys=True)
    if before != after:
        for name in ("task.json", "ticket.md", "hidden.md"):
            if (snapshot / name).is_file():
                (task.dir / name).write_text((snapshot / name).read_text())
        raise Parked(
            "amend_ticket changed hidden_requirements, which it must never do — "
            f"reverted from {snapshot}. The amendment may only add to the ticket.")


def bump(run_id: str, slug: str, field: str) -> int:
    """Increment a per-task counter and return the new value, atomically."""
    """Increment a per-task counter and return the new value, atomically."""
    def mutate(state):
        row = state["tasks"][slug]
        row[field] = row.get(field, 0) + 1
        return row[field]
    return state.update(run_id, mutate)


def act(run_id: str, task: Task, order: list[plan.Step], index: int,
        decision: dict, findings: list[str]) -> int:
    """Carry out one judged action. Returns the index of the next step to run."""
    action = decision["action"]
    # Rewinds are counted PER PHASE. One shared counter meant a task that used
    # `author_extend` and `amend_ticket` in phase A arrived at the plant with no
    # repair budget at all, and the first thing the judge asked for was refused.
    phase = order[index].phase
    counter = f"rewinds_{phase}"
    if action == "proceed":
        return index + 1
    if action == "stop":
        raise Parked(decision.get("reason") or "the judge stopped this task")
    if action == "hand_cut":
        raise Parked("needs a human re-cut: " + (decision.get("reason") or ""))
    if action == "retry":
        return index                       # attempts are counted by the caller
    # Phase C's two repairs. Both rewrite the plant in place and then re-prove,
    # rather than re-planting: a re-plant re-rolls the whole tree including
    # everything the same proof just showed is working, and placement -- which
    # conversation each remark sits in and what it answers -- is the expensive
    # half. `repair` rewrites only the remarks the proof blamed; `replace`
    # re-places every remark without re-wording any.
    # The three plant repairs. NONE of them may move the walk forward: the old
    # code jumped to `prove.3` from wherever it was, so a `repair` chosen at the
    # `clues` step silently skipped settle, reverse, reorder, reknit and
    # consistency, and `prove` then ran against a plant that had never been
    # settled or knitted into exchanges.
    # The repair the consistency gate actually needs. `fact_conflicts` and
    # `unknit` are defects in the woven CONVERSATION, not in the remark or where
    # it sits: an exchange whose last turn asserts the opposite of the graded
    # decision, which is the shape that cost g2 four facts. `replace` re-places
    # with identical wording and `reclues` throws away sound placement, so
    # neither touches it -- the judge said so, correctly, and parked instead.
    # `reknit --only <ids> --redo` re-weaves exactly the named exchanges.
    if action == "rewrite_exchanges":
        import re as _re
        entry = json.loads((task.dir / "clues" / "plant.json").read_text())["tasks"][0]
        named = set()
        for field in ("fact_conflicts", "unknit"):
            for row in entry.get(field) or []:
                named.update(_re.findall(r"\b(" + task.id + r"\.r\d+\.[A-Za-z0-9_.-]+)", str(row)))
        every = {c["clue_id"] for q in entry.get("requirements", []) for c in q.get("clues", [])}
        ids = sorted(named & every)
        if not ids:
            raise Parked("rewrite_exchanges: the findings name no clue id to re-weave")
        rewinds = bump(run_id, task.slug, counter)
        cap = MAX_REWINDS.get(phase, DEFAULT_MAX_REWINDS)
        if rewinds > cap:
            raise Parked(f"rewrite_exchanges chosen {rewinds} times in phase {phase}; "
                         f"the cap is {cap}")
        log = state.log_path(run_id, task.slug, "rewrite_exchanges", rewinds)
        rc = cli("reknit", task.slug,
                 ("--only", ",".join(ids), "--redo", "--run", plan.CORPUS_RUN), log,
                 timeout_s=plan.TIMEOUTS.get("reknit", plan.DEFAULT_TIMEOUT))
        state.record(run_id, task.slug,
                     {"step": "rewrite_exchanges", "rc": rc, "clues": ids})
        return index          # re-run the gate that named them

    if action in ("repair", "replace", "reclues"):
        rewinds = bump(run_id, task.slug, counter)
        cap = MAX_REWINDS.get(phase, DEFAULT_MAX_REWINDS)
        if rewinds > cap:
            raise Parked(f"{action} was chosen {rewinds} times in phase {phase}; "
                         f"the cap is {cap} and each one is a paid pass")
        cmd = "clues" if action == "reclues" else action
        args = ("--run", plan.CORPUS_RUN) if cmd in plan.TAKES_RUN else ()
        log = state.log_path(run_id, task.slug, action, rewinds)
        rc = cli(cmd, task.slug, args, log, timeout_s=plan.TIMEOUTS.get(cmd, plan.DEFAULT_TIMEOUT))
        state.record(run_id, task.slug, {"step": action, "rc": rc})
        names = [s.name for s in order]
        if action == "reclues" and "clues" in names:
            # A new plant invalidates everything downstream of it.
            return names.index("clues") + 1
        return index          # re-run the step that reported the defect

    if action not in REWINDS:
        raise SystemExit(f"worker: no branch for action {action!r} — judge.ACTIONS "
                         "and worker.act() have drifted apart")

    rewinds = bump(run_id, task.slug, "rewinds")
    cap = MAX_REWINDS.get(phase, DEFAULT_MAX_REWINDS)
    if rewinds > cap:
        raise Parked(f"{action} was chosen {rewinds} times in phase {phase}; "
                     f"the cap is {cap} and each one is a paid rebuild")

    if action == "author_extend":
        log = state.log_path(run_id, task.slug, "author.extend", rewinds)
        rc = cli("author", task.slug, ("--extend",), log)
        state.record(run_id, task.slug, {"step": "author --extend", "rc": rc})
    if action == "amend_ticket":
        amend_ticket(task, findings)
        state.record(run_id, task.slug, {"step": "amend_ticket", "rc": 0})
    if action == "reformat_ticket":
        reformat_ticket(task, findings)
        state.record(run_id, task.slug, {"step": "reformat_ticket", "rc": 0})

    target = REWINDS[action]
    if not target:
        return index + 1
    names = [s.name for s in order]
    return names.index(target)


# --------------------------------------------------------------------------- hosted

def arms(task: Task) -> dict[str, pathlib.Path]:
    """The apex arm directories `cli horizon` wrote, by arm name."""
    root = task.dir / "horizon"
    found = {}
    for path in sorted(p for p in root.glob(f"{task.id}-{task.slug}*") if p.is_dir()):
        suffix = path.name[len(f"{task.id}-{task.slug}"):].lstrip("-")
        found[suffix or "blind"] = path
    return found


def do_hosted(run_id: str, task: Task, step: plan.Step) -> gates.Verdict:
    found = arms(task)
    slug = task.slug
    if step.cmd in ("push", "push_clues"):
        want = ("blind", "spec", "clues") if step.cmd == "push_clues" else ("blind", "spec")
        for arm in want:
            if arm not in found:
                return gates.Verdict(step.name, False, [f"no {arm} arm under {task.dir/'horizon'}"])
            meta = hosted.push(found[arm], label=f"fleet {run_id}")
            state.update(run_id, lambda st, a=arm, m=meta: st["tasks"][slug]
                         .setdefault("hosted", {}).setdefault(a, {})
                         .update({"task_id": m.get("task_id"), "version": m.get("version")}))
        current = state.load(run_id)["tasks"][slug]["hosted"]
        return gates.Verdict(step.name, True, detail=json.dumps(current))

    if step.cmd in ("validate", "validate_clues"):
        want = ("blind", "spec", "clues") if step.cmd == "validate_clues" else ("blind", "spec")
        missing = [a for a in want if a not in found]
        if missing:
            # KeyError here escapes the HostedError handler and lands as a bare
            # "KeyError: 'clues'" with no explanation. The push branch guards; so
            # does this one now.
            return gates.Verdict(step.name, False,
                                 [f"no {', '.join(missing)} arm under {task.dir/'horizon'}"])
        for arm in want:
            hosted.validate_both(found[arm])
        return gates.validation_gate(task, {a: found[a] for a in want})

    if step.cmd in ("evaluate", "evaluate_clues"):
        want = ("blind", "spec", "clues") if step.cmd == "evaluate_clues" else ("blind", "spec")
        pushed = state.load(run_id)["tasks"][slug].get("hosted") or {}
        missing = [a for a in want if not (pushed.get(a) or {}).get("task_id")]
        if missing:
            return gates.Verdict(step.name, False,
                                 [f"no pushed task_id for {', '.join(missing)}"])
        ids = [pushed[a]["task_id"] for a in want]
        # Stage one clears the model gate; stage two is the measurement. Both
        # are submitted even when the first looks bad, because the first CANNOT
        # look good -- see hosted.GATING_RUNS for the g6 numbers.
        stages = [(hosted.MODEL, hosted.GATING_RUNS),
                  (hosted.VERDICT_MODEL, hosted.VERDICT_RUNS)]
        final, counts, outcome = {}, {}, ""
        for model, runs in stages:
            try:
                eval_id = hosted.submit(ids, runs=runs, model=model)
            except hosted.HostedError as exc:
                if model == hosted.VERDICT_MODEL:
                    # 403 until the gate clears. Worth saying plainly rather
                    # than as a stack trace: the task is fine, it is not yet
                    # allowed on the model whose number counts.
                    return gates.Verdict(step.name, False,
                                         [f"{model} refused the submission ({exc}); the "
                                          f"model gate needs 10+ rollouts per arm first"],
                                         detail=json.dumps(final)[:2000])
                raise
            state.update(run_id, lambda st, e=eval_id, m=model: st["tasks"][slug]
                         .setdefault("evaluations", [])
                         .append({"id": e, "model": m, "runs": runs, "arms": list(want)}))
            final = hosted.await_evaluation(eval_id)
            counts = final.get("rollouts") or {}
            outcome = (final.get("status") or "").lower()
            for arm in want:
                hosted.pull(found[arm])
        # Three ways an evaluation ends with nothing worth reading, all measured
        # on real evaluations: it errored every rollout (the exhausted-budget
        # signature -- rollouts that fail with zero spend look exactly like a
        # broken task), it graded none, or it never started one at all and came
        # back `failed` with total 0. The last would have passed a check that
        # only looked at `errored`.
        hard = []
        if counts.get("errored"):
            hard.append(f"evaluation {eval_id}: {counts['errored']} of "
                        f"{counts.get('total')} rollouts errored — check "
                        "`horizon whoami --json` before reading this as a task defect")
        if not counts.get("graded"):
            hard.append(f"evaluation {eval_id} finished {outcome!r} with "
                        f"{counts.get('graded', 0)} graded rollouts; there is nothing to score")
        return gates.Verdict(step.name, not hard, hard, detail=json.dumps(final)[:2000])

    raise SystemExit(f"worker: no hosted branch for {step.cmd!r}")


def do_check(task: Task, step: plan.Step) -> gates.Verdict:
    found = arms(task)
    if step.cmd == "verdict_ab":
        return gates.verdict_ab(task, found.get("spec", task.dir), found.get("blind", task.dir))
    if step.cmd == "verdict_clues":
        if "clues" not in found:
            return gates.Verdict(step.name, False,
                                 [f"no clues arm under {task.dir / 'horizon'}"])
        return gates.verdict_clues(task, found["clues"])
    raise SystemExit(f"worker: no check branch for {step.cmd!r}")


# --------------------------------------------------------------------------- the walk

# Free megabytes below which no further step starts. `_loop/run.sh` refuses a
# trial under the same rule and says why: harbor failing on a full disk mid-run
# "looks exactly like an agent failure in the results and would be scored as
# one". A build that dies part-way through for want of space is the same lie,
# and five tasks each keeping a persistent oracle tree is what fills it.
FLOOR_MB = 3000


def affordable(task: Task, step: plan.Step, run: dict) -> tuple[bool, str]:
    import shutil
    free = shutil.disk_usage("/").free // (1024 * 1024)
    if free < FLOOR_MB:
        return False, (f"{free}MB free, floor is {FLOOR_MB}MB — refusing to start "
                       f"{step.label} rather than let it fail as if the agent had")
    spent = state.spend(task.dir)
    if spent + step.paid > PER_TASK_CAP_USD:
        return False, f"${spent:.2f} spent, {step.label} budgets ${step.paid:.2f}, cap is ${PER_TASK_CAP_USD:.0f}"
    total = sum(state.spend(REPO / "task_generator" / "out" / s) for s in run["tasks"])
    if total + step.paid > run["budget_usd"]:
        return False, f"run has spent ${total:.2f} of ${run['budget_usd']:.0f}"
    return True, ""


def walk(run_id: str, slug: str, order: list[plan.Step], *, start: str = "") -> None:
    """Walk one task through `order`, from `start` (default: where state says)."""
    row = state.load(run_id)["tasks"][slug]
    names = [s.name for s in order]
    index = names.index(start) if start else (names.index(row["step"]) if row["step"] in names else 0)
    state.update(run_id, lambda st: st["tasks"][slug].update(status="running"))

    while index < len(order):
        step = order[index]

        task = load(slug) if step.cmd != "new" else None
        if task is not None:
            ok, why = affordable(task, step, state.load(run_id))
            if not ok:
                raise Parked(f"budget: {why}")

        # Position and the attempt counter, in one locked read-modify-write.
        # Held only in memory they would be lost by the next `state.load`, and a
        # retry cap that never trips is not a cap.
        def enter(st, step=step):
            row = st["tasks"][slug]
            row["step"], row["phase"] = step.name, step.phase
            row["attempts"][step.name] = row["attempts"].get(step.name, 0) + 1
            return row["attempts"][step.name]
        attempt = state.update(run_id, enter)
        log = state.log_path(run_id, slug, step.name, attempt)

        started = time.time()
        if step.kind == "cli":
            args = step.args
            if step.cmd == "new":
                row = state.load(run_id)["tasks"][slug]
                args = ("--brief", pathlib.Path(row["brief"]).read_text(), "--id", row["id"])
            if step.cmd == "clues":
                # Which of slack / notion / email this task's remarks may live in,
                # per task. A corpus where every task spreads across all three
                # reads the same way every time; some tasks being slack-only is
                # both more varied and a harder retrieval problem in a different
                # direction -- g4 was planted that way deliberately.
                row = state.load(run_id)["tasks"][slug]
                if row.get("sources"):
                    args = args + ("--sources", row["sources"])
            seen_before = (last_conflicts(run_id, slug)
                           if step.cmd in PLANT_STAGES else None)
            with held(step):
                rc = cli(step.cmd, slug, args, log, timeout_s=step.timeout_s)
            task = load(slug)
            # Read BEFORE this step's own row is written, so it is the previous
            # run's findings and not this one's.
            verdict = evaluate(task, step, rc, log, previous=seen_before)
        elif step.kind == "hosted":
            rc = 0
            try:
                verdict = do_hosted(run_id, task, step)
            except hosted.HostedError as exc:
                verdict = gates.Verdict(step.name, False, [str(exc)])
            log.write_text(verdict.render() + "\n\n" + verdict.detail)
        else:
            rc = 0
            verdict = do_check(task, step)
            log.write_text(verdict.render() + "\n\n" + verdict.detail)

        state.record(run_id, slug,
                     {"step": step.name, "rc": rc, "seconds": round(time.time() - started, 1),
                      "ok": verdict.ok, "hard": verdict.hard, "soft": verdict.soft})

        if verdict.ok and not verdict.soft:
            index += 1
            continue

        # Anything a gate found -- blocking or advisory -- is a decision, and the
        # decision is made by reading the artifact. Advisory findings on a
        # passing step still go to the judge, because `split`'s advisory rows are
        # the ones that predicted 8 of 9 coincidences before any build existed.
        notes = state.notes_path(run_id).read_text() if state.notes_path(run_id).is_file() else ""
        decision = judge.decide(
            task, situation_for(step), step=step.name, rc=rc,
            evidence=verdict.evidence or verdict.detail,
            findings=verdict.hard, soft=verdict.soft, notes=notes,
            log_tail=tail(log))
        state.record(run_id, slug, {"step": step.name, "rc": rc, "judged": True, **decision})

        if decision["action"] == "retry" and attempt >= MAX_ATTEMPTS:
            raise Parked(f"{step.name} failed {attempt} times; the judge still says retry")
        index = act(run_id, load(slug), order, index, decision, verdict.hard)

    state.update(run_id, lambda st: st["tasks"][slug].update(status="done", step=None))


def run_task(run_id: str, slug: str, order: list[plan.Step], *, start: str = "") -> None:
    """`walk`, with parking and crashes both landing in state rather than stderr."""
    try:
        walk(run_id, slug, order, start=start)
    except Parked as exc:
        state.update(run_id, lambda st: st["tasks"][slug].update(
            status="parked",
            blocked={"step": st["tasks"][slug].get("step"), "why": str(exc)}))
    except (Exception, SystemExit) as exc:                # noqa: BLE001 - deliberate
        # A crash in the driver must not take the other four tasks with it, and
        # must be visible in `status` rather than only in a log nobody opens.
        state.update(run_id, lambda st: st["tasks"][slug].update(
            status="crashed",
            blocked={"step": st["tasks"][slug].get("step"),
                     "why": f"{type(exc).__name__}: {exc}"}))
