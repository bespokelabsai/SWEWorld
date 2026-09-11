"""The decision a person makes between two stages, made by one `claude -p`.

`task_generator/README.md` is explicit that the stages are automated and the
judgement is not: "Every stage is automated. The judgement between stages is
not. Four things were done by hand, and only two of them were real work" -- and
one of the other two, diagnosing `--extend` rather than another cut, cost about
$6 of g2's $19 and "should not have".

So this is not a supervisor. It is those four decisions, each handed the
artifact that a person would have read, each answering with one value from a
CLOSED enum. The enum is the safety property: a judge that returned free text
the driver then interpreted would be a model choosing which shell command runs.
`ACTIONS` below is the whole vocabulary, and `worker.py` has a branch per entry.

It runs through `tg.agent.run`, which already handles the two things that make a
call here void -- it strips ANTHROPIC_API_KEY from the child and aborts the run
outright if the CLI reports having used it -- and it records through
`steps._record`, deliberately reaching past the underscore: the alternative is a
second writer of `spend.json` whose row shape can drift from the reader in
`recipe.paid_for`, and then `cli.py make --dry-run` quietly stops telling the
truth about what a fleet-built task cost.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tg import agent, steps                                    # noqa: E402
from tg.model import REPO, Task                                # noqa: E402

PROMPTS = pathlib.Path(__file__).resolve().parent / "prompts"

# Every action the driver knows how to carry out. Adding one here without a
# branch in `worker.act()` raises there rather than being ignored.
ACTIONS = {
    "proceed":       "the artifact is good enough; go to the next step",
    "retry":         "re-run the step unchanged; it failed for a reason that is not about the artifact",
    "resplit":       "run `split` again — the ticket LEAKED a name its own facts need",
    "hand_cut":      "stop for a human re-cut; the model cannot fix this one and g6's was free",
    "author_extend": "run `author --extend` — a coincidence is a fact about the specification, not the cut",
    "amend_ticket":  "state a missing detail in ticket.md and task.json's description, then rebuild naive and spec",
    "reformat_ticket": "re-lay-out the ticket as structured markdown, dropping nothing, changing no wording",
    "repair":        "rewrite only the remarks the proof blamed, in place",
    "replace":       "re-place every remark, same wording — placement is wrong, the words are not",
    "reclues":       "re-plant from scratch: the TREE is wrong, not the placement or the prose",
    "rewrite_exchanges": "re-weave only the exchanges a gate named — the wording of the conversation "
                         "is wrong, the remark and its placement are not",
    "stop":          "park this task and report; going on would spend into a defect",
}

# situation -> (which actions are offered, which files the judge is pointed at)
SITUATIONS = {
    "split": (("proceed", "reformat_ticket", "resplit", "hand_cut", "stop"),
              ("ticket.md", "hidden.md", "fact_sources.json")),
    "bracket": (("proceed", "author_extend", "amend_ticket", "hand_cut", "stop"),
                ("bracket.md", "ticket.md", "hidden.md", "fixtures/naive.patch")),
    "audit": (("proceed", "stop"), ("audit.md", "bracket.md")),
    "tests": (("proceed", "retry", "stop"), ("tests/test_open.py", "ticket.md")),
    "crash": (("retry", "stop"), ()),
    "hosted": (("proceed", "retry", "stop"), ("ticket.md", "hidden.md")),
    # The plant itself. `repair` is not offered here: `cli.py repair` reads
    # `clues/proof.json` and exits if it is absent, which it is until `prove` has
    # run, so offering it would buy a no-op that still advanced the walk.
    "clues": (("proceed", "reclues", "replace", "stop"),
              ("clues/README.md", "clues/tree.md")),
    # Every pass after the plant that rewrites it: settle, reverse, reorder,
    # reknit, consistency. They report through the same ledger and the same
    # repairs answer them.
    "plant": (("proceed", "replace", "reclues", "rewrite_exchanges", "stop"),
              ("clues/README.md", "clues/plant.json", "clues/settled.md")),
    "prove": (("repair", "replace", "reclues", "rewrite_exchanges", "stop"),
              ("clues/proof.md", "clues/README.md")),
    # `horizon --arms …,clues` refuses when the rendered digest never types a
    # graded name. Retrying is guaranteed to fail identically.
    "emit_clues": (("reclues", "replace", "stop"),
                   ("clues/README.md", "clues/plant.json")),
}


def schema(actions: tuple[str, ...]) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdict", "action", "reason"],
        "properties": {
            "verdict": {"type": "string", "maxLength": 400,
                        "description": "what the artifact actually says, in one or two sentences"},
            "action": {"type": "string", "enum": list(actions)},
            "reason": {"type": "string", "maxLength": 1200,
                       "description": "why that action and not the others, citing the artifact"},
        },
    }


def render(name: str, **values: str) -> str:
    """`fleet/prompts/<name>` with `{{key}}` filled in.

    Deliberately not `steps.prompt()`, which reads `task_generator/prompts/`:
    putting fleet prompt files in there would put fleet files in the sequential
    path's directory, and this experiment has to be deletable in one `rm -rf`.
    """
    text = (PROMPTS / name).read_text()
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    holes = [line for line in text.splitlines() if "{{" in line and "}}" in line]
    if holes:
        raise SystemExit(f"{name}: unfilled placeholders: {holes[:3]}")
    return text


def decide(task: Task, situation: str, *, step: str, rc: int, evidence: str,
           findings: list[str], soft: list[str], notes: str,
           log_tail: str = "", budget_usd: float = 1.5) -> dict:
    """One decision. Returns `{verdict, action, reason}`; never raises on content."""
    if situation not in SITUATIONS:
        raise SystemExit(f"judge: no such situation {situation!r}")
    actions, files = SITUATIONS[situation]
    text = render(
        "judge.md",
        situation=situation,
        step=step,
        rc=str(rc),
        task_id=task.id,
        slug=task.slug,
        title=task.title or "(not cut yet)",
        actions="\n".join(f"- `{a}` — {ACTIONS[a]}" for a in actions),
        files="\n".join(f"- `{task.dir / f}`" for f in files) or "  (none)",
        findings="\n".join(f"- {f}" for f in findings) or "  (none)",
        soft="\n".join(f"- {f}" for f in soft) or "  (none)",
        evidence=evidence[:14000] or "(none)",
        log_tail=log_tail[-6000:] or "(none)",
        notes=notes.strip() or "(none yet)",
    )
    # An API-level refusal is not a verdict about the task, and it must not kill a
    # run that has paid for its plant. Measured here: one consistency judge call
    # came back "Opus 5's safeguards flagged this message ... This sometimes
    # happens with safe, normal conversations" -- a false positive on corpus prose
    # quoted into the prompt. `agent.run` raises SystemExit on it, which the
    # worker records as a crash.
    #
    # Retried once with the evidence halved: that both shrinks the surface that
    # tripped the classifier and changes the prompt, so a deterministic flag is
    # not simply hit again. If it still refuses, the caller gets the crash.
    try:
        return _ask(task, text, step, situation, actions, budget_usd)
    except SystemExit as exc:
        if not any(k in str(exc) for k in ("safeguards", "API Error", "error run")):
            raise
        shorter = text.replace(evidence[:14000], evidence[:6000], 1) if evidence else text
        return _ask(task, shorter, step, f"{situation}-retry", actions, budget_usd)


def _ask(task: Task, text: str, step: str, situation: str,
         actions: tuple[str, ...], budget_usd: float) -> dict:
    result = agent.run(
        text,
        repo=REPO,
        label=f"fleet-judge-{step}-{situation}",
        cwd=task.dir / ".fleet",
        add_dirs=[task.dir, REPO / "curator"],
        tools="Read,Grep,Glob",
        schema=schema(actions),
        budget_usd=budget_usd,
        log_dir=task.dir / "logs",
        timeout_s=1800,
    )
    steps._record(task, f"fleet-judge-{step}-{situation}", text, result)
    answer = result.data or {}
    if answer.get("action") not in actions:
        # A schema violation the CLI let through. Fail closed: the one action
        # that spends nothing and loses nothing.
        return {"verdict": "judge returned an action outside its enum",
                "action": "stop",
                "reason": f"got {answer.get('action')!r}, expected one of {actions}"}
    return answer
