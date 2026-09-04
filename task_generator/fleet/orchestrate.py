#!/usr/bin/env python3
"""Five tasks at once. The entrypoint.

    orchestrate.py start --briefs fleet/briefs --ids g7,g8,g9,g10,g11 --through B
    orchestrate.py start --dry-run          # the graph and the spend, free
    orchestrate.py verify                   # calibrate the gates, free, spends nothing
    orchestrate.py status [run-id]
    orchestrate.py note "what g6 taught us"
    orchestrate.py resume [run-id]
    orchestrate.py stop <slug>

`--through` defaults to `B` and phase C must be named. That is the whole shape
of v1: the cut and the spec/blind proof run unattended; the plant does not start
until somebody has read the proof. Phase D raises if asked for.

Run it DETACHED, not merely backgrounded:

    setsid nohup python3 task_generator/fleet/orchestrate.py start ... \\
        > /tmp/fleet.log 2>&1 < /dev/null &

Eleven of g4's eighteen stages ran longer than ten minutes, which is where
several harnesses cut a child off. Detaching removes the question; tuning a
timeout only moves it.
"""
from __future__ import annotations

import argparse
import datetime
import os
import json
import pathlib
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
# Two entries, and both are needed: `task_generator/` so `tg` imports, and the
# repo root so `fleet` imports as a package. Running this file directly puts
# `fleet/` itself on the path, which makes neither work.
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))

from tg.model import OUT, load                                 # noqa: E402
from fleet import gates, plan, state, worker                   # noqa: E402

# Seconds between task starts. Not politeness: the first `emit` lock contention
# and the first devbox contention should happen while somebody is watching, and
# five identical `author` calls launched in the same second is the least
# informative way to find out whether that works.
STAGGER_S = 180

# Free disk below which the run refuses to start. A trial writes ~260MB, a
# plant's injected corpus more, and harbor failing on a full disk mid-run "looks
# exactly like an agent failure in the results and would be scored as one".
FLOOR_MB = 4000


def free_mb() -> int:
    import shutil
    return shutil.disk_usage("/").free // (1024 * 1024)


def discover_briefs(directory: pathlib.Path) -> list[pathlib.Path]:
    found = sorted(directory.glob("*.md"))
    if not found:
        raise SystemExit(f"no briefs in {directory}")
    return found


def slug_of(brief: pathlib.Path) -> str:
    """`briefs/token-capacity-budget.md` -> `token-capacity-budget`."""
    return brief.stem


# --------------------------------------------------------------------------- start

def cmd_start(args) -> int:
    order = plan.steps_through(args.through, args.stop_after)
    briefs = discover_briefs(pathlib.Path(args.briefs))
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    if len(ids) != len(briefs):
        raise SystemExit(f"{len(briefs)} briefs but {len(ids)} ids; they are paired by "
                         "position and an id must never be guessed — `cli new` picks "
                         "its own by globbing out/*/task.json and two concurrent calls "
                         "would pick the same one")
    tasks = [{"id": i, "slug": slug_of(b), "brief": str(b)} for i, b in zip(ids, briefs)]
    # `--only` filters AFTER the pairing, never before: the id a task gets must
    # not depend on which subset is being run, or the pilot task and the same
    # task in the full run would be two different ids with two different suites.
    if args.only:
        want = {s.strip() for s in args.only.split(",") if s.strip()}
        unknown = want - {t["slug"] for t in tasks}
        if unknown:
            raise SystemExit(f"--only names no such brief: {', '.join(sorted(unknown))}")
        tasks = [t for t in tasks if t["slug"] in want]

    if args.dry_run:
        print(render_plan(order, tasks, args))
        return 0

    clashes = [t for t in tasks if (OUT / t["slug"]).exists()]
    if clashes and not args.force:
        raise SystemExit("already on disk: " + ", ".join(t["slug"] for t in clashes) +
                         "\nThe fleet never overwrites an existing task. Rename the "
                         "brief, or pass --force if you mean to resume into it.")
    if free_mb() < FLOOR_MB:
        raise SystemExit(f"{free_mb()}MB free, floor is {FLOOR_MB}MB")

    run_id = args.run_id or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run = state.new(run_id, through=args.through, budget_usd=args.budget_usd, tasks=tasks)
    if args.stop_after:
        state.update(run_id, lambda st: st.update(stop_after=args.stop_after))
    print(f"run {run_id}: {len(tasks)} tasks through phase {args.through}, "
          f"budget ${args.budget_usd:.0f}\n  state: {state.path(run_id)}")
    launch(run_id, [t["slug"] for t in tasks], order, stagger=args.stagger)
    return report(run_id)


def launch(run_id: str, slugs: list[str], order: list[plan.Step], *,
           stagger: int = STAGGER_S, starts: dict[str, str] | None = None) -> None:
    threads = []
    for n, slug in enumerate(slugs):
        if n:
            time.sleep(stagger)
        thread = threading.Thread(
            target=worker.run_task, name=slug,
            args=(run_id, slug, order),
            kwargs={"start": (starts or {}).get(slug, "")}, daemon=False)
        thread.start()
        threads.append(thread)
        print(f"  started {slug}")
    for thread in threads:
        thread.join()


def render_plan(order, tasks, args) -> str:
    lines = [f"run: {len(tasks)} tasks through phase {args.through}, "
             f"budget ${args.budget_usd:.0f}, stagger {args.stagger}s", ""]
    for task in tasks:
        lines.append(f"  {task['id']:4} {task['slug']:32} {task['brief']}")
    lines += ["", f"{'step':26} {'kind':7} {'gate':5} {'budget':>8}  command"]
    lines.append("-" * 100)
    for step in order:
        kind, name = worker.locks.STAGE_LOCKS.get(step.cmd, ("", ""))
        lock = f"[{name or kind}]" if kind else ""
        # The slug is positional and comes FIRST; the flags follow it. Printing
        # it the other way round would make the dry run a plan nobody can paste.
        shown = (" ".join(["python3 cli.py", step.cmd, "<slug>", *step.args])
                 if step.kind == "cli"
                 else f"hosted.{step.cmd}()" if step.kind == "hosted"
                 else f"gates.{step.cmd}()")
        lines.append(f"{step.name:26} {step.kind:7} {'GATE' if step.gate else '':5} "
                     f"{step.paid:8.2f}  {shown} {lock}")
    per = sum(s.paid for s in order)
    lines += ["-" * 100,
              f"{'':26} {'':7} {'':5} {per:8.2f}  per task",
              f"{'':26} {'':7} {'':5} {per * len(tasks):8.2f}  for {len(tasks)} tasks",
              "", f"free disk: {free_mb()}MB (floor {FLOOR_MB}MB)"]
    try:
        from fleet import hosted
        ok, why = hosted.affordable(60.0)
        lines.append(f"horizon:   {why} — {'ok' if ok else 'NOT ENOUGH FOR AN EVALUATION'}")
    except Exception as exc:                                   # noqa: BLE001
        lines.append(f"horizon:   could not check budget ({exc})")
    return "\n".join(lines)


# --------------------------------------------------------------------------- verify

def cmd_verify(args) -> int:
    """Calibrate every gate against the brackets already on disk. Free.

    tasks/lessons.md's rule for a new detector: "Measure a detector against the
    artifact before trusting it as a gate." So this prints what the fleet would
    have decided about g1-g6 and leaves the reader to check it against what a
    person decided. It writes nothing and advances nothing.
    """
    print("gate calibration — what the fleet would have said about tasks already measured\n")
    rows = []
    for path in sorted(OUT.glob("*/bracket.json")):
        slug = path.parent.name
        try:
            task = load(slug)
        except SystemExit:
            continue
        verdict = gates.bracket_gate(task)
        measured = json.loads(path.read_text())
        naive = (measured["trees"].get("naive") or {}).get("rewards") or {}
        passes = sorted(k.split(".", 1)[1] for k, r in naive.items() if r == 1.0)
        rows.append((task.id, slug, verdict, passes))
    for task_id, slug, verdict, passes in sorted(rows):
        mark = "SHIPS" if verdict.ok else "REFUSED"
        print(f"{task_id:4} {slug:26} {mark:8} naive passes: {passes}")
        for problem in verdict.hard[:6]:
            print(f"       ! {problem[:150]}")
    # Every OTHER gate, called for real against whatever artifacts exist. This
    # half is not calibration -- it is the cheapest possible proof that each
    # gate can RUN. `split_gate` shipped with `tg_leak.render(rows)` against a
    # `render(task, rows)` signature and crashed the pilot at $7.35, four steps
    # in, on a stage that had already succeeded. A gate nothing ever called is
    # not a gate, and the free version of finding that out is this.
    print("\nevery other gate, called against the artifacts on disk:")
    for path in sorted(OUT.glob("*/task.json")):
        slug = path.parent.name
        try:
            task = load(slug)
        except SystemExit:
            continue
        for name, call in (("split", lambda t: gates.split_gate(t, 1)),
                           ("emit", gates.emit_gate),
                           ("clues", gates.clue_gate)):
            if name == "clues" and not (task.dir / "clues" / "plant.json").is_file():
                continue
            if name == "split" and not (task.dir / "fact_sources.json").is_file():
                continue
            try:
                verdict = call(task)
                counts = f"{len(verdict.hard)} hard, {len(verdict.soft)} soft"
                print(f"  {task.id:4} {slug:26} {name:6} ran: "
                      f"{'ok' if verdict.ok else 'REFUSED':8} {counts}")
            except Exception as exc:                           # noqa: BLE001
                print(f"  {task.id:4} {slug:26} {name:6} CRASHED: "
                      f"{type(exc).__name__}: {exc}")

    print("\nand the archived cuts, where a defect was measured and then repaired:")
    for cut in sorted(OUT.glob("*/cuts/*/bracket.json")):
        slug = cut.parents[2].name
        try:
            task = load(slug)
        except SystemExit:
            continue
        measured = json.loads(cut.read_text())
        shape = gates.healthy_naive(task, measured)
        print(f"  {slug}/{cut.parent.name}: "
              f"{'healthy' if not shape else shape[0][:120]}")
    return 0


# --------------------------------------------------------------------------- status

def report(run_id: str) -> int:
    run = state.load(run_id)
    order = plan.steps_through(run["through"], run.get("stop_after", ""))
    names = [s.name for s in order]
    print(f"\nrun {run_id}  started {run['started']}  through {run['through']}")
    print(f"{'task':6} {'slug':30} {'phase':6} {'step':22} {'status':8} {'spent':>8}  where")
    print("-" * 118)
    total = 0.0
    for slug, row in sorted(run["tasks"].items(), key=lambda kv: kv[1]["id"]):
        spent = state.spend(OUT / slug)
        total += spent
        step = row.get("step") or "-"
        at = f"{names.index(step) + 1}/{len(names)}" if step in names else ""
        note = (row.get("blocked") or {}).get("why", "")
        print(f"{row['id']:6} {slug:30} {row['phase']:6} {step:22} "
              f"{row['status']:8} {spent:8.2f}  {at} {note[:40]}")
    print("-" * 118)
    print(f"{'':6} {'':30} {'':6} {'':22} {'':8} {total:8.2f}  of ${run['budget_usd']:.0f}")
    blocked = {s: r for s, r in run["tasks"].items() if r["status"] in ("parked", "crashed")}
    for slug, row in blocked.items():
        print(f"\n{slug} is {row['status']} at {row['blocked'].get('step')}:")
        print(f"  {row['blocked'].get('why')}")
    return 1 if blocked else 0


def cmd_status(args) -> int:
    run_id = args.run_id or state.latest()
    if not run_id:
        raise SystemExit("no runs under fleet/runs/")
    return report(run_id)


def cmd_note(args) -> int:
    run_id = args.run_id or state.latest()
    if not run_id:
        raise SystemExit("no runs under fleet/runs/")
    path = state.notes_path(run_id)
    with open(path, "a") as handle:
        handle.write(f"\n## {state.now()}\n\n{args.text.strip()}\n")
    print(f"appended to {path}; every judge call from here on reads it")
    return 0


def cmd_resume(args) -> int:
    run_id = args.run_id or state.latest()
    # Refuse to double-drive a run. Resuming one whose original orchestrator is
    # still alive gives every live task two threads in two processes, racing on
    # the same state file and the same paid steps. Done once here, by hand, on
    # a run whose last task was still evaluating.
    import subprocess as _sp
    found = _sp.run(["pgrep", "-f", f"orchestrate.py (start|resume).*{run_id}"],
                    capture_output=True, text=True).stdout.split()
    # Only PYTHON processes count. `pgrep -f` also matches the `bash -c …` wrapper
    # that launched this one, and every shell in the ancestry whose command line
    # happens to quote the same string -- so the first version of this guard
    # refused a legitimate resume by finding the shell that was starting it.
    others = []
    for pid in found:
        if not pid or int(pid) in (os.getpid(), os.getppid()):
            continue
        try:
            argv = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if argv and b"python" in argv[0]:
            others.append(pid)
    if others and not args.force:
        raise SystemExit(
            f"run {run_id} already has an orchestrator alive (pid {', '.join(others)}).\n"
            "Stop it first, or pass --force if you are certain it is finished with "
            "every task you are about to restart.")
    run = state.load(run_id)
    order = plan.steps_through(args.through or run["through"],
                               args.stop_after or run.get("stop_after", ""))
    if args.through and args.through != run["through"]:
        state.update(run_id, lambda st: st.update(through=args.through))
        run = state.load(run_id)
    live = [s for s, r in run["tasks"].items() if r["status"] != "done"]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        unknown = want - set(run["tasks"])
        if unknown:
            raise SystemExit(f"--only names no task in this run: {', '.join(sorted(unknown))}")
        live = [s for s in live if s in want]
    if args.budget_usd:
        state.update(run_id, lambda st: st.update(budget_usd=args.budget_usd))
    if args.stop_after:
        state.update(run_id, lambda st: st.update(stop_after=args.stop_after))
    if args.sources:
        def pin(st):
            for slug in live:
                st["tasks"][slug]["sources"] = args.sources
        state.update(run_id, pin)
    run = state.load(run_id)
    if not live:
        print("every task is done")
        return 0
    def clear(st):
        for slug in live:
            st["tasks"][slug].update(status="pending", blocked=None)
    state.update(run_id, clear)
    # `--from` exists because a crash IN A GATE is not a reason to re-pay for the
    # STEP. The pilot crashed in `split_gate` on a `split` that had already
    # succeeded and written every artifact; resuming at `split` would have
    # re-cut for $1.49 and re-rolled which facts are hidden. Default stays
    # "wherever state says", which is right when the step itself failed.
    starts = {s: (args.start or run["tasks"][s].get("step") or "") for s in live}
    print(f"resuming {len(live)} task(s) through phase {run['through']}"
          + (f", from {args.start}" if args.start else ""))
    launch(run_id, live, order, stagger=args.stagger, starts=starts)
    return report(run_id)


def cmd_stop(args) -> int:
    run_id = args.run_id or state.latest()
    state.update(run_id, lambda st: st["tasks"][args.slug].update(
        status="parked",
        blocked={"step": st["tasks"][args.slug].get("step"), "why": "parked by hand"}))
    print(f"{args.slug} parked; a running step finishes, nothing new starts")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrate.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = parser.add_subparsers(dest="cmd", required=True)

    start = subs.add_parser("start", help="walk a set of briefs")
    start.add_argument("--briefs", default=str(HERE / "briefs"))
    start.add_argument("--ids", required=True, help="comma-separated, paired with the briefs by position")
    start.add_argument("--through", default="B", choices=plan.PHASES)
    start.add_argument("--budget-usd", type=float, default=350.0)
    start.add_argument("--stagger", type=int, default=STAGGER_S)
    start.add_argument("--run-id", default=None)
    start.add_argument("--dry-run", action="store_true", help="print the graph and the spend; free")
    start.add_argument("--force", action="store_true", help="proceed into slugs already on disk")
    start.add_argument("--only", default="", help="run only these slugs; ids stay paired as if all were run")
    start.add_argument("--sources", default="")
    start.add_argument("--stop-after", dest="stop_after", default="",
                       help="halt cleanly after this step (a step name, not a phase) — "
                            "the rest stays available to `resume` into later")
    start.set_defaults(fn=cmd_start)

    verify = subs.add_parser("verify", help="calibrate the gates against tasks already measured; free")
    verify.set_defaults(fn=cmd_verify)

    status = subs.add_parser("status")
    status.add_argument("run_id", nargs="?")
    status.set_defaults(fn=cmd_status)

    note = subs.add_parser("note", help="a learning every later judge call reads")
    note.add_argument("text")
    note.add_argument("--run-id", default=None)
    note.set_defaults(fn=cmd_note)

    resume = subs.add_parser("resume")
    resume.add_argument("run_id", nargs="?")
    resume.add_argument("--through", default=None, choices=plan.PHASES)
    resume.add_argument("--stagger", type=int, default=30)
    resume.add_argument("--force", action="store_true",
                        help="resume even though another orchestrator is running this run")
    resume.add_argument("--stop-after", dest="stop_after", default="")
    resume.add_argument("--only", default="", help="resume only these slugs")
    resume.add_argument("--sources", default="",
                        help="which of slack,notion,email these tasks' remarks may live in "
                             "(default: all three)")
    resume.add_argument("--budget-usd", dest="budget_usd", type=float, default=None,
                        help="raise the run's budget; phase C costs more than A+B")
    resume.add_argument("--from", dest="start", default="",
                        help="step name to restart at; default is where state left off")
    resume.set_defaults(fn=cmd_resume)

    stop = subs.add_parser("stop")
    stop.add_argument("slug")
    stop.add_argument("--run-id", default=None)
    stop.set_defaults(fn=cmd_stop)

    args = parser.parse_args(argv)
    if not hasattr(args, "run_id"):
        args.run_id = None
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
