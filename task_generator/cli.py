#!/usr/bin/env python3
"""task_generator — author a verifiable hidden-requirement task, then prove it is one.

    python3 task_generator/cli.py <command> <slug> [options]

The pipeline, in order. Everything is task-agnostic; the only task-specific
strings live in `out/<slug>/` and in `prompts/`.

    new      scaffold out/<slug>/ from a one-line brief
    author   the WHOLE specification, nothing hidden yet
    build    one role's implementation  (--role oracle | naive | <name>)
    split    cut the specification into a ticket and hidden requirements
    tests    one decisive test per declared fact, green against oracle
    suite    run the suite against one tree  (the agents' only execution route)
    bracket  pristine | naive | oracle -> a verdict per fact.  THE GATE.
    audit    adversarial Catalog A/B review, one call per fact
    emit     write the harbor artifacts, refusing if the bracket did not ship
    trial    launch a paid arm  (--arm spec | blind)
    report   the four-condition matrix

Run order matters: author -> build oracle -> split -> tests -> build naive ->
bracket -> audit -> emit -> trial. `split` sits before `tests` because a test
file has to know its fact keys: the grader reads the fact out of the test's own
function name.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from tg import bracket, emit as emit_mod, report as report_mod, steps, suite as suite_mod, trial as trial_mod  # noqa: E402
from tg.model import load  # noqa: E402


def audit_plant(ledger: dict) -> int:
    """Print every defect on a finished plant; return 1 if any must be fixed.

    The one reader of `clues.problems`. Before this, four of the six checks
    `finish()` computes had no reader at all and the other two were read only by
    the command that could have caused them -- so `settle`, `replace` and `repair`
    each returned 0 over a plant another pass had broken.

    Every command that writes a plant ends here, which means a defect is reported
    by whichever pass runs next rather than only by the pass that owns it.
    """
    from tg import clues
    hard, soft = clues.problems(ledger["tasks"][0])
    for row in soft:
        print(f"  ~ {row}")
    for row in hard:
        print(f"  ! {row}")
    if hard:
        print(f"\n{len(hard)} must be fixed before this plant is worth measuring.")
    return 1 if hard else 0


def cmd_new(args) -> int:
    task = steps.new(args.slug, args.brief, args.id)
    print(f"{task.dir}\n  id={task.id} suite={task.suite} group={task.group}")
    print(f"next: cli.py author {task.slug}")
    return 0


def cmd_author(args) -> int:
    whole = steps.author(args.slug, budget=args.budget, extend=args.extend)
    print(f"wrote {whole} ({len(whole.read_text().splitlines())} lines)")
    print(f"next: cli.py build {args.slug} --role oracle")
    return 0


def cmd_split(args) -> int:
    task = steps.split(args.slug, budget=args.budget, model=args.model)
    print(f"{task.title}\n")
    # Report the two Catalog A patterns that are checkable without spending
    # anything, right where the cut is made. This predicted nine of the ten
    # coincidences in the first cut of the first task, before a naive build
    # existed to measure them against.
    from tg import leak
    rows = leak.audit(task)
    print(leak.render(task, rows))
    leaks = [r for r in rows if r["leaked_by_ticket"]]
    if leaks:
        print("The ticket prints identifiers these facts require:")
        for row in leaks:
            print(f"  {row['key']}: {', '.join(row['leaked_by_ticket'])}")
    shape = steps.unstructured(task)
    if shape:
        print(f"\n{shape}")
    print(f"\nnext: cli.py tests {args.slug}")
    return 0 if all(r["has_anchor"] for r in rows) and not shape else 1


def cmd_build(args) -> int:
    patch, lines = steps.build(args.slug, args.role, budget=args.budget,
                               instruction=args.instruction)
    print(f"{patch}  ({lines} diff lines)")
    if lines == 0:
        print("  the role changed nothing. That is a real outcome, not a success.")
    return 0


def cmd_tests(args) -> int:
    tests = steps.write_tests(args.slug, budget=args.budget)
    for path in sorted(tests.glob("test_*.py")):
        print(f"  {path.name}")
    problems = emit_mod.check_bijection(load(args.slug))
    for problem in problems:
        print(f"  ! {problem}")
    print(f"\nnext: cli.py build {args.slug} --role naive")
    return 0 if not problems else 1


def cmd_suite(args) -> int:
    """The wrapper the authoring agents call. Prints outcomes, returns pytest's rc."""
    from tg import trees
    task = load(args.slug)
    fixture = None
    if args.role != "pristine":
        # Re-freeze from the live tree first, when there is one. Without this the
        # loop is incoherent in a way that wastes a whole step: the suite applies
        # the PATCH, so an agent that edited `.trees/<slug>/oracle` and then ran
        # the suite would be shown results for the tree as it was before the edit
        # - and would conclude its test was wrong.
        tree = trees.PERSISTENT / args.slug / args.role
        if tree.is_dir():
            before = task.dir / "fixtures" / f"{args.role}.patch"
            was = before.read_text() if before.is_file() else ""
            patch, _ = trees.freeze(task.dir, args.role, tree)
            if patch.read_text() != was:
                print(f"[tg] re-froze {args.role} from {tree} (the tree had changed)")
        fixture = task.dir / "fixtures" / f"{args.role}.py"
        if not fixture.is_file():
            print(f"no fixture {fixture}", file=sys.stderr)
            return 2
    result = suite_mod.run(fixture, suite_name=task.suite, task_tests=task.dir / "tests")
    if not result["outcomes"]:
        print("the suite did not collect. pytest said:\n" + result["stdout"][-4000:])
        return result["rc"] or 2
    for node, state in sorted(result["outcomes"].items()):
        print(f"{state.upper():7} {node}")
    print(f"\n{suite_mod.summarise(result)}")
    if result["rc"] != 0:
        print("\n--- pytest output ---\n" + result["stdout"][-6000:])
    return result["rc"]


def cmd_exec(args) -> int:
    """Run a command against a role's tree, in the container that can import curator."""
    from tg import trees
    tree = pathlib.Path(args.tree) if args.tree else trees.PERSISTENT / args.slug / args.role
    if not tree.is_dir():
        print(f"no tree at {tree}", file=sys.stderr)
        return 2
    out = suite_mod.exec_in_tree(tree, args.cmd)
    sys.stdout.write(out["stdout"])
    if out["stderr"].strip():
        sys.stderr.write(out["stderr"])
    return out["rc"]


def cmd_bracket(args) -> int:
    roles = args.roles.split(",") if args.roles else None
    measured = steps.measure(args.slug, roles)
    task = load(args.slug)
    print(bracket.render(task, measured))
    ok, _ = bracket.ships(measured)
    return 0 if ok else 1


def cmd_audit(args) -> int:
    findings = steps.audit(args.slug, budget=args.budget)
    task = load(args.slug)
    for row in findings:
        print(f"{row['verdict']:7} {row['key']}  {row['recommendation'][:90]}")
    print(f"\nwrote {task.dir / 'audit.md'}")
    return 0 if all(r["verdict"] == "ship" for r in findings) else 1


def cmd_emit(args) -> int:
    out = emit_mod.emit(args.slug, force=args.force)
    task = load(args.slug)
    for key in ("suite", "fixtures", "generated"):
        print(f"  {out[key]}")
    print(f"\nnext:\n  python3 harbor_tasks/build_tasks.py "
          f"--extra-tasks {out['generated']} --pick {task.id}\n"
          f"  python3 task_generator/cli.py trial {task.slug} --arm spec")
    return 0


def cmd_horizon(args) -> int:
    """Emit this task as Horizon (apex) tasks, one per arm."""
    from tg import horizon
    task = load(args.slug)
    made = horizon.emit(task, tuple(args.arms.split(",")), force=args.force)
    for arm, path in made.items():
        print(f"  {arm:6} {path}")
    print("\nnext, from that directory's parent:")
    print(f"  export HORIZON_API_KEY=... MINI_BATCH_ID=...")
    for arm, path in made.items():
        print(f"  horizon tasks push {path.name}      # the {arm} arm")
    return 0


def cmd_trim(args) -> int:
    """Cut every hidden requirement down to exactly the assertions that grade it."""
    from tg import trim as trim_mod
    out = trim_mod.trim(args.slug, budget=args.budget, dry_run=args.dry_run,
                        rerun=args.rerun)
    task = load(args.slug)
    rows = [(k, v) for k, v in out["facts"].items() if "now" in v]
    for key, v in rows:
        print(f"  {key:34} {v['was_words']:4} -> {v['now_words']:4} words   "
              f"{v['assertions']:2} assertions   {len(v['dropped'])} dropped")
    for key, v in out["facts"].items():
        if "skipped" in v:
            print(f"  ! {key}: {v['skipped']}")
        if "rejected" in v:
            print(f"  ! {key}: REJECTED - {v['rejected']}; the original is kept")
    was = sum(v["was_words"] for _, v in rows); now = sum(v["now_words"] for _, v in rows)
    print(f"\n{was} -> {now} words" + ("  (dry run, nothing written)" if args.dry_run else ""))
    print(f"{task.dir / 'trim.md'}")
    if not args.dry_run:
        print("\nthe tests, fact keys and oracle are unchanged. Now prove the trim was "
              "safe:\n  cli.py bracket " + args.slug + "   # every fact must still read `hidden`"
              "\n  the -spec arm must still score 1.00 hosted")
    return 0


def cmd_settle(args) -> int:
    """Judge every graded assertion against the remarks, then say the ones nobody said."""
    from tg import settle as settle_mod
    out = settle_mod.settle(args.slug, run=args.run, budget=args.budget,
                            dry_run=args.dry_run, rejudge=args.rejudge)
    counts = out["counts"]
    total = sum(counts.values())
    print(f"\n{counts['stated']}/{total} assertions rest on something a remark states")
    for verdict in ("implied", "absent", "not_required"):
        print(f"  {verdict:13} {counts[verdict]}")
    for claim_id, row in sorted(out["verdicts"].items()):
        if row["verdict"] in settle_mod.CARRIED:
            continue
        print(f"  {row['verdict']:9} {claim_id:34} {row['why'][:96]}")
    if args.dry_run:
        print(f"\n{load(args.slug).dir / 'clues' / 'settled.md'} (nothing changed)")
        return 1 if out["short"] else 0
    for label in ("rewritten", "added", "unfixed"):
        for row in out.get(label) or []:
            print(f"  {label:9} {row}")
    print(f"\n{load(args.slug).dir / 'clues' / 'settled.md'}"
          f"\nnext: cli.py settle {args.slug} --dry-run, then cli.py prove {args.slug}")
    return 0


def cmd_replace(args) -> int:
    """Re-place every remark — same wording, better homes — without re-planting."""
    from tg import clues
    only = args.only.split(",") if args.only else None
    if args.mismatched:
        import json as _j
        want = {"slack": ("chat_insert", "chat_thread"),
                "notion": ("doc_edit", "doc_comment", "doc_new"),
                "email": ("mail_reply", "mail_new")}
        led = _j.loads((load(args.slug).dir / "clues" / "plant.json").read_text())
        only = [c["clue_id"] for r in led["tasks"][0]["requirements"] for c in r["clues"]
                if c.get("carrier") and c["carrier"]["kind"] not in want[c["source"]]]
        print(f"re-placing {len(only)} remark(s) whose carrier contradicts their source")
    ledger = clues.replace(args.slug, run=args.run, budget=args.budget, only=only)
    task = load(args.slug)
    import collections as _c
    rows = [c for r in ledger["tasks"][0]["requirements"] for c in r["clues"]]
    placed = [c for c in rows if c.get("carrier")]
    print(f"\n{len(placed)}/{len(rows)} placed")
    print("  source :", dict(_c.Counter(c["source"] for c in placed)))
    print("  carrier:", dict(_c.Counter(c["carrier"]["kind"] for c in placed)))
    for req in ledger["tasks"][0]["requirements"]:
        if req["missing_identifiers"]:
            print(f"  ! {req['req_id']}: no remark says {', '.join(req['missing_identifiers'])}")
    print(f"\n{task.dir / 'clues' / 'README.md'}\nnext: cli.py prove {args.slug}")
    return audit_plant(ledger)


def cmd_reorder(args) -> int:
    """Re-place remarks whose date puts a decision before the problem it answers."""
    from tg import clues
    out = clues.reorder(args.slug, run=args.run, budget=args.budget)
    if not out["moved"]:
        print("every step's problems already come before its decisions")
        return 0
    for row in out["moved"]:
        print(f"  moved  {row}")
    for row in out["still_wrong"]:
        print(f"  ! still out of order: {row}")
    print(f"\nnext: cli.py prove {args.slug}")
    return 1 if out["still_wrong"] else 0


def cmd_reverse(args) -> int:
    """Say out loud that each earlier decision was dropped, and what replaced it."""
    from tg import clues
    ledger = clues.reverse(args.slug, run=args.run, budget=args.budget, redo=args.redo)
    print(f"\nnext: cli.py settle {args.slug} --dry-run")
    return audit_plant(ledger)


def cmd_consistency(args) -> int:
    """Is any fact stated wrongly by a remark nothing later overturns?"""
    from tg import clues
    ledger = clues.consistency(args.slug, run=args.run, budget=args.budget)
    print(f"\nnext: cli.py prove {args.slug}")
    return audit_plant(ledger)


def cmd_reknit(args) -> int:
    """Make each invented conversation say the remark as the plant now words it."""
    from tg import clues
    ledger = clues.reknit(args.slug, run=args.run, budget=args.budget,
                          only=args.only.split(",") if args.only else None,
                          redo=args.redo)
    print(f"\nnext: cli.py inject {args.slug} --dry-run")
    return audit_plant(ledger)


def cmd_repair(args) -> int:
    """Rewrite the remarks a proof says do not carry their fact, in place."""
    import json as _json
    from tg import clues
    task = load(args.slug)
    proof = task.dir / "clues" / "proof.json"
    if not proof.is_file():
        raise SystemExit(f"no {proof}; run `cli.py prove {args.slug}` first")
    from tg import prove as prove_mod
    failures = prove_mod.failures(_json.loads(proof.read_text()))
    if not failures:
        print("the last proof passed every fact; nothing to repair")
        return 0
    print(f"repairing {len(failures)} fact(s): {', '.join(failures)}")
    out = clues.repair(args.slug, failures, run=args.run, budget=args.budget)
    for label in ("rewritten", "added", "unfixed"):
        for row in out[label]:
            print(f"  {label:9} {row}")
    for req in out["ledger"]["tasks"][0]["requirements"]:
        if req["missing_identifiers"]:
            print(f"  ! {req['req_id']}: no remark says "
                  f"{', '.join(req['missing_identifiers'])}")
    print(f"\nnext: cli.py prove {args.slug}")
    return audit_plant(out["ledger"])


def cmd_prove(args) -> int:
    """Build from ticket + clues alone and score it: is the plant solvable?"""
    from tg import prove as prove_mod
    out = prove_mod.prove(args.slug, rebuild=not args.no_build, budget=args.budget,
                          runs=args.runs, source=args.source)
    task = load(args.slug)
    for key, row in sorted(out["facts"].items()):
        print(f"  {'PASS' if row['passed'] else 'FAIL'}  {key:34} "
              f"{row.get('rate', ''):>5}  {row['why'][:100]}")
    print(f"\n{out['passed']}/{out['total']} from the clues alone over "
          f"{out['runs']} build(s) -> {task.dir / 'clues' / 'proof.md'}")
    shaky = [k for k, r in out["facts"].items() if not r["passed"] and any(r.get("per_run") or [])]
    if len(shaky) > 1:
        print(f"\n  {len(shaky)} facts fail on some builds and not others: "
              f"{', '.join(sorted(shaky))}.\n  Check whether they fail on the SAME "
              "builds — if they do, that is one remark, not several.")
    return 0 if out["passed"] == out["total"] else 1


def cmd_clues(args) -> int:
    """Build the remarks that hide this task's requirements, and place them."""
    from tg import clues
    ledger = clues.plan(args.slug, sources=tuple(args.sources.split(",")),
                        run=args.run, budget=args.budget, back=args.back)
    task = load(args.slug)
    entry = ledger["tasks"][0]
    total = sum(len(r["clues"]) for r in entry["requirements"])
    print(f"\n{total} remark(s) written to {task.dir / 'clues' / 'README.md'}")
    bad = False
    for req in entry["requirements"]:
        if req["gaps"]:
            print(f"  ! {req['req_id']}: nothing carries {', '.join(req['gaps'])}")
            bad = True
        if req.get("missing_identifiers"):
            print(f"  ! {req['req_id']}: no remark says "
                  f"{', '.join(req['missing_identifiers'])} — the tests reach for those "
                  "by name, so those facts cannot pass")
            bad = True
        if req.get("unprinted_values"):
            print(f"  ~ {req['req_id']}: nothing prints "
                  f"{', '.join(req['unprinted_values'])}; check the remarks let a reader "
                  "compute them")
        for problem in req["spread"]:
            print(f"  ~ {req['req_id']}: {problem}")
        for clue in req["clues"]:
            for problem in clue["problems"]:
                print(f"  ~ {clue['clue_id']}: {problem}")
    # `plan` routes through `finish` now, so a fresh plant carries the same six
    # findings a re-planted one does, and they are gated the same way.
    return 1 if bad else audit_plant(ledger)


def cmd_trial(args) -> int:
    task = load(args.slug)
    out = trial_mod.launch(task, args.arm, job=args.job)
    print(f"job={out['job']} rc={out['rc']}  log={out['log']}")
    if out["stdout"].strip():
        print(out["stdout"])
    metrics = trial_mod.rewards(out["job"])
    print(json.dumps(metrics, indent=1)[:2000])
    return out["rc"]


def cmd_inject(args) -> int:
    """Write the plant into a copy of the corpus the world is baked from."""
    from tg import inject as inject_mod
    out = inject_mod.inject(args.slug, run=args.run, out=args.out,
                            dry_run=args.dry_run)
    for kind, n in sorted(out["kinds"].items()):
        print(f"  {kind:14} {n}")
    if args.dry_run:
        print(f"\n{sum(out['kinds'].values())} remark(s) would be written into a "
              f"copy of {out['source']}")
        return 0
    print(f"\n{out['rows']} chat message(s) -> {out['target']}")
    for key, mark in (("problems", "!"), ("absent", "!"), ("timing", "!"),
                      ("rivals", "!"),
                      ("crowding", "~"), ("unsearchable", "~")):
        for row in out.get(key) or []:
            print(f"  {mark} {row}")
    # `rivals` blocks. A remark nobody said and a rival vocabulary nobody retracted
    # cost the same thing -- a world arm that scores zero on a world holding the
    # answer -- and the second one is invisible to every other check here because
    # they all read the remark rather than what was written around it.
    bad = out["problems"] + out["absent"] + out["timing"] + (out.get("rivals") or [])
    print(f"\n{len(bad)} blocking, {len(out['crowding'])} to read by eye")
    return 1 if bad else 0


def cmd_answers(args) -> int:
    """Write the answer key: the ticket, the hidden facts, and where every remark is."""
    import json as _json, pathlib as _pl
    from tg import inject as inject_mod
    from tg.model import REPO
    task = load(args.slug)
    ledger = _json.loads((task.dir / "clues" / "plant.json").read_text())
    root = _pl.Path(args.corpus) if args.corpus else REPO / "data"
    out = _pl.Path(args.out) if args.out else (
        REPO / "harbor_tasks" / f"{task.id}-{task.slug}" / "README.md")
    text = inject_mod.answer_key(task, ledger, root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"  {out}  ({len(text.splitlines())} lines, read out of {root})")
    return 0


def cmd_resync(args) -> int:
    """Point the plant's recorded mail text at a corpus somebody edited by hand."""
    import json as _json, pathlib as _pl
    from tg import inject as inject_mod
    from tg.model import REPO
    task = load(args.slug)
    path = task.dir / args.plant / "plant.json"
    if not path.is_file():
        raise SystemExit(f"no plant at {path}")
    root = _pl.Path(args.corpus) if args.corpus else REPO / "data"
    ledger = _json.loads(path.read_text())
    changed = inject_mod.resync(root, ledger)
    if not changed:
        print(f"  nothing to resync in {path} against {root}")
        return 0
    if args.dry_run:
        print(f"  would resync {len(changed)}: {', '.join(changed)}")
        return 0
    path.write_text(_json.dumps(ledger, indent=1) + "\n")
    print(f"  {path}  resynced {len(changed)}: {', '.join(changed)}")
    # The point of the exercise: `located()` has to stop refusing. Saying so here
    # means a resync that did not actually fix it is visible now rather than three
    # commands later when the answer key will not write.
    try:
        inject_mod.located(root, ledger)
    except SystemExit as exc:
        print(f"  ! still not located: {exc}")
        return 1
    print(f"  located() resolves against {root}")
    return 0


def cmd_snap(args) -> int:
    """Copy the plant aside under a label, before something rewrites it."""
    from tg import clues
    into = clues.snapshot(load(args.slug), args.label)
    if into is None:
        raise SystemExit(f"no plant to snapshot for {args.slug}")
    print(f"  {into}")
    return 0


def cmd_make(args) -> int:
    """Walk the whole recipe, stopping at the first gate that does not pass."""
    from tg import recipe
    return recipe.make(args.slug, start=args.start, optional=args.optional,
                       dry_run=args.dry_run)


def cmd_report(args) -> int:
    task = load(args.slug)
    text = report_mod.render(task)
    (task.dir / "report.md").write_text(text)
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = parser.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **kw):
        sub = subs.add_parser(name, help=(fn.__doc__ or name).strip().splitlines()[0], **kw)
        sub.add_argument("slug")
        sub.set_defaults(fn=fn)
        return sub

    new = add("new", cmd_new)
    new.add_argument("--brief", required=True, help="the subsystem, one or two sentences")
    new.add_argument("--id", default=None, help="task id; defaults to the next free g<N>")

    author = add("author", cmd_author)
    author.add_argument("--budget", type=float, default=12.0)
    author.add_argument("--extend", action="store_true",
                        help="keep the existing whole.md and add parts whose content "
                             "the codebase cannot supply, told what the bracket measured")

    split = add("split", cmd_split)
    split.add_argument("--budget", type=float, default=6.0)
    split.add_argument("--model", default="opus",
                       help="model that makes the cut. `opus` cannot currently be "
                            "used with --json-schema (safeguard error "
                            "`[reasoning_extraction]`); `sonnet` can")

    build = add("build", cmd_build)
    build.add_argument("--role", required=True)
    build.add_argument("--budget", type=float, default=10.0)
    build.add_argument("--instruction", default=None,
                      help="override the role note; how to vary an implementation "
                           "for the overshoot/undershoot check")

    tests = add("tests", cmd_tests)
    tests.add_argument("--budget", type=float, default=25.0)

    suite = add("suite", cmd_suite)
    suite.add_argument("--role", default="oracle", help="oracle | naive | pristine | <name>")

    ex = add("exec", cmd_exec)
    ex.add_argument("--role", default="oracle")
    ex.add_argument("--tree", default=None,
                    help="a checkout to run against, instead of .trees/<slug>/<role>")
    # A single quoted string, not REMAINDER: with a positional slug in front of it
    # argparse hands REMAINDER every following token including `--role`, and the
    # shell then tried to execute `--role` as a command.
    ex.add_argument("--cmd", required=True,
                    help="one shell command, quoted; runs with PYTHONPATH=<tree>/src")

    br = add("bracket", cmd_bracket)
    br.add_argument("--roles", default=None, help="comma-separated; default every fixture present")

    au = add("audit", cmd_audit)
    au.add_argument("--budget", type=float, default=4.0)

    em = add("emit", cmd_emit)
    em.add_argument("--force", action="store_true",
                    help="emit despite problems; for inspecting a task that does not ship")

    tr = add("trial", cmd_trial)
    tr.add_argument("--arm", required=True, choices=sorted(trial_mod.ARMS))
    tr.add_argument("--job", default=None)

    hz = add("horizon", cmd_horizon)
    # `clues` is in the default because the gate rides on it: `horizon.emit` only
    # calls `unsolvable()` when the clues arm is being written, so the old
    # "blind,spec" default emitted two arms and checked nothing. `recipe.py`
    # already passed all three explicitly to work around this; a hand-run
    # `cli.py horizon` silently skipped the only gate the command has.
    hz.add_argument("--arms", default="blind,spec,clues")
    hz.add_argument("--force", action="store_true",
                    help="emit the clues arm even if the graded surface is missing from it")

    cl = add("clues", cmd_clues)
    cl.add_argument("--sources", default="slack,notion,email")
    cl.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")
    cl.add_argument("--budget", type=float, default=3.0, help="per model call")
    cl.add_argument("--back", type=float, default=0.40,
                    help="fraction of the corpus, from the end, clues may land in")

    pr = add("prove", cmd_prove)
    pr.add_argument("--budget", type=float, default=8.0)
    pr.add_argument("--source", choices=("remarks", "corpus"), default="remarks",
                    help="`remarks` is the ceiling arm's digest — can an agent USE "
                         "the information. `corpus` is the exchanges as the world "
                         "holds them — did the information survive being split")
    pr.add_argument("--runs", type=int, default=3,
                    help="builds to sample; a fact that fails on any of them "
                         "is a finding, because the defect is not the sampling")
    pr.add_argument("--no-build", action="store_true",
                    help="score the existing clues fixture instead of building again")

    tm = add("trim", cmd_trim)
    tm.add_argument("--budget", type=float, default=3.0)
    tm.add_argument("--dry-run", action="store_true",
                    help="write trim.md and change no requirement")
    tm.add_argument("--rerun", action="store_true",
                    help="re-ask even where the identical prompt already has a reply")

    st = add("settle", cmd_settle)
    st.add_argument("--budget", type=float, default=3.0)
    st.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")
    st.add_argument("--dry-run", action="store_true",
                    help="judge and report; change nothing")
    st.add_argument("--rejudge", action="store_true",
                    help="re-take the verdicts even though the remarks have not moved")

    rl = add("replace", cmd_replace)
    rl.add_argument("--budget", type=float, default=3.0)
    rl.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")
    rl.add_argument("--only", default=None, help="comma-separated clue ids")
    rl.add_argument("--mismatched", action="store_true",
                    help="only the remarks whose carrier contradicts their source")

    ro = add("reorder", cmd_reorder)
    ro.add_argument("--budget", type=float, default=3.0)
    ro.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")

    rv = add("reverse", cmd_reverse)
    rv.add_argument("--budget", type=float, default=3.0)
    rv.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")
    rv.add_argument("--redo", action="store_true",
                    help="drop the reversals already planted and write them again")

    cn = add("consistency", cmd_consistency)
    cn.add_argument("--budget", type=float, default=1.0)
    cn.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")

    rk = add("reknit", cmd_reknit)
    rk.add_argument("--budget", type=float, default=3.0)
    rk.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")
    rk.add_argument("--only", default="", help="clue ids, comma separated")
    rk.add_argument("--redo", action="store_true",
                    help="re-knit every invented conversation, not only the adrift")

    rp = add("repair", cmd_repair)
    rp.add_argument("--budget", type=float, default=3.0)
    rp.add_argument("--run", default=None, help="a phase-4 run dir; default `latest`")

    ij = add("inject", cmd_inject)
    ij.add_argument("--run", default=None, help="the corpus to copy; default `latest`")
    ij.add_argument("--out", default=None, help="where to write the copy")
    ij.add_argument("--dry-run", action="store_true")

    an = add("answers", cmd_answers)
    an.add_argument("--corpus", default=None,
                    help="the written corpus to read locations out of; default data/")
    an.add_argument("--out", default=None,
                    help="default: harbor_tasks/<id>-<slug>/README.md")

    rs = add("resync", cmd_resync)
    rs.add_argument("--corpus", default=None,
                    help="the written corpus the plant should match; default data/")
    rs.add_argument("--plant", default="clues",
                    help="which snapshot under out/<slug>/ to update; the live one "
                         "is whichever `located()` still resolves against, which is "
                         "not always `clues`")
    rs.add_argument("--dry-run", action="store_true")

    sn = add("snap", cmd_snap)
    sn.add_argument("label", help="e.g. v7-perfect-1.00, pre-settle")

    mk = add("make", cmd_make)
    mk.add_argument("--from", dest="start", default="",
                    help="resume at this stage instead of the first")
    mk.add_argument("--optional", action="store_true",
                    help="also run audit, reorder and inject")
    mk.add_argument("--dry-run", action="store_true",
                    help="print the stages, the gates and the projected spend")

    add("report", cmd_report)

    args = parser.parse_args(argv)
    if args.cmd == "new" and not args.id:
        from tg.model import OUT
        used = set()
        for path in OUT.glob("*/task.json"):
            used.add(json.loads(path.read_text()).get("id", ""))
        number = 1
        while f"g{number}" in used:
            number += 1
        args.id = f"g{number}"
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
