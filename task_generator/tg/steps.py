"""The pipeline steps. One function per command, none of them task-specific.

Every step reads its inputs from `out/<slug>/` and writes its outputs there, so a
step can be re-run alone and the artifact it produced is the reviewable record of
what happened.
"""
from __future__ import annotations

import json
import pathlib
import shutil

from . import agent, bracket, schemas, suite, trees
from .model import OUT, REPO, SUITES, Task, declared_facts, load

PROMPTS = REPO / "task_generator" / "prompts"
RUBRIC = REPO / "task_generator" / "rubric.md"
CURATOR = REPO / "curator"


def prompt(name: str, **values: str) -> str:
    """A prompt file with `{{key}}` filled in.

    Deliberately dumber than a template engine: every substitution is visible in
    the rendered copy written to `logs/`, so a step that came out wrong is
    diagnosable from the prompt that produced it rather than by re-deriving it.
    """
    text = (PROMPTS / name).read_text()
    values.setdefault("rubric", RUBRIC.read_text())
    values.setdefault("repo", str(REPO))
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    left = [line for line in text.splitlines() if "{{" in line and "}}" in line]
    if left:
        raise SystemExit(f"{name}: unfilled placeholders: {left[:3]}")
    return text


def _log(task: Task) -> pathlib.Path:
    return task.dir / "logs"


def _record(task: Task, label: str, text: str, result: agent.Result) -> None:
    (_log(task)).mkdir(parents=True, exist_ok=True)
    (_log(task) / f"{label}.prompt.md").write_text(text)
    spend = task.dir / "spend.json"
    rows = json.loads(spend.read_text()) if spend.is_file() else []
    rows.append({"label": label, "cost_usd": round(result.cost_usd, 4),
                 "turns": result.turns, "seconds": round(result.seconds, 1),
                 "session": result.session_id})
    spend.write_text(json.dumps(rows, indent=1) + "\n")


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------
def new(slug: str, brief: str, task_id: str) -> Task:
    task = Task(id=task_id, slug=slug, suite=f"{task_id}_{slug.replace('-', '_')}",
                title="", description="", hidden_requirements=[], brief=brief)
    task.dir.mkdir(parents=True, exist_ok=True)
    (task.dir / "brief.md").write_text(brief.strip() + "\n")
    task.save()
    return task


# ---------------------------------------------------------------------------
# author — the whole specification, nothing hidden
# ---------------------------------------------------------------------------
def author(slug: str, *, budget: float = 12.0, extend: bool = False) -> pathlib.Path:
    """The whole specification, or more of it.

    `extend` exists because a re-author throws away work that was not wrong. The
    first specification of this task was accurate, its parts had real
    alternatives, and its oracle implemented all of it — and nine of its ten
    candidate facts were still passed by a blind build, because the alternatives
    were resolvable by reading the code. That is a gap to fill, not a document to
    replace: extending keeps the parts and the oracle, and adds parts carrying
    content the codebase cannot supply.
    """
    task = load(slug)
    whole = task.dir / "whole.md"
    if extend:
        if not whole.is_file():
            raise SystemExit(f"no {whole} to extend")
        (task.dir / "whole.before-extend.md").write_text(whole.read_text())
        tree = trees.PERSISTENT / slug / "oracle"
        text = prompt("author_extend.md", whole=whole.read_text(),
                      feedback=bracket_feedback(task) or
                      "(no bracket on record; extend for arbitrariness anyway)",
                      exec_cmd=f"python3 {REPO}/task_generator/cli.py exec {slug} "
                               f"--tree {tree}")
        label = "author-extend"
    else:
        text = prompt("author_whole.md", brief=(task.dir / "brief.md").read_text(),
                      feedback="")
        label = "author"
    result = agent.run(text, repo=REPO, label=label, cwd=task.dir,
                       add_dirs=[CURATOR], budget_usd=budget, log_dir=_log(task))
    _record(task, label, text, result)
    if not whole.is_file():
        raise SystemExit(f"author wrote no {whole}. Its reply was:\n{result.text[:2000]}")
    return whole


# ---------------------------------------------------------------------------
# split — the cut into ticket and hidden requirements
# ---------------------------------------------------------------------------
def bracket_feedback(task: Task) -> str:
    """The measured verdicts and the blind build that produced them, as prose.

    A second cut told only "try again" repeats the first. Told *which* facts a
    ticket-only build passed, and handed the diff that passed them, it can see
    what the codebase was already giving away — which is the thing the first cut
    cannot know, because the first cut has no naive build to compare against.

    Same instinct as phase 3's bounded re-plant, which is told the specific gate
    it failed rather than being re-rolled.
    """
    measured_file = task.dir / "bracket.json"
    if not measured_file.is_file():
        return ""
    measured = json.loads(measured_file.read_text())
    verdicts = measured.get("verdicts", {})
    # Read the naive tree's own rewards rather than the verdict string. A bracket
    # run without `oracle` marks every fact `unproven` — correctly, since nothing
    # proves it is satisfiable — but the blind result it DID measure is exactly
    # what this feedback is for, and it would otherwise be thrown away.
    naive = (measured.get("trees", {}).get("naive") or {}).get("rewards", {})
    hidden_keys = [k for k in verdicts if not k.endswith("open_feature")]
    bad = [k for k in hidden_keys if naive.get(k) == 1.0]
    if not bad:
        return ""

    lines = ["## What the last cut measured — read this before you cut again", "",
             "The previous ticket and facts were built, and a **ticket-only** build was "
             "measured against the suite. Per fact:", ""]
    for key in hidden_keys:
        mark = ("**COINCIDENCE — the blind build passed it**" if naive.get(key) == 1.0
                else "discriminated (the blind build failed it)")
        lines.append(f"- `{key}` — {mark}")
    lines += ["", f"{len(bad)} of {len(hidden_keys)} facts did not discriminate.", "",
              "### The previous ticket", "", "```", task.description, "```", ""]

    patch = task.dir / "fixtures" / "naive.patch"
    if patch.is_file():
        body = patch.read_text()
        lines += ["### The build that passed them, from the ticket alone", "",
                  "This is the diff a competent engineer produced with no hidden "
                  "requirements at all. Everything in it is something the ticket and the "
                  "surrounding code already supplied. Read it, and do not declare as "
                  "hidden anything you can find in here.", "",
                  "```diff", body[:24000], "```", ""]
    return "\n".join(lines)


def split(slug: str, *, budget: float = 6.0) -> Task:
    task = load(slug)
    whole = task.dir / "whole.md"
    if not whole.is_file():
        raise SystemExit(f"no {whole}; run `tg author {slug}` first")
    text = prompt("split.md", whole=whole.read_text(), feedback=bracket_feedback(task))
    result = agent.run(text, repo=REPO, label="split", cwd=task.dir, tools="",
                       schema=schemas.SPLIT, budget_usd=budget, log_dir=_log(task))
    _record(task, "split", text, result)

    # Keep the cut being replaced. Two cuts of one specification is the normal
    # case, and the earlier ticket is the evidence for why the later one is
    # shaped as it is.
    history = task.dir / "cuts"
    if task.description:
        history.mkdir(exist_ok=True)
        stamp = len(list(history.glob("cut-*"))) + 1
        keep = history / f"cut-{stamp}"
        keep.mkdir(exist_ok=True)
        for name in ("task.json", "ticket.md", "hidden.md", "fact_sources.json",
                     "bracket.json", "bracket.md"):
            if (task.dir / name).is_file():
                shutil.copy2(task.dir / name, keep / name)

    data = result.data
    task.title = data["title"]
    task.description = data["description"]
    task.hidden_requirements = data["hidden_requirements"]
    task.save()
    (task.dir / "fact_sources.json").write_text(json.dumps(data["fact_sources"], indent=1) + "\n")
    (task.dir / "ticket.md").write_text(f"# {task.title}\n\n{task.description}\n")
    (task.dir / "hidden.md").write_text(render_hidden(task))
    return task


def render_hidden(task: Task) -> str:
    """The hidden requirements as prose — what the `-spec` arm will carry."""
    lines = [f"# Hidden requirements — {task.id} ({task.slug})", ""]
    for number, req in enumerate(task.hidden_requirements, 1):
        lines.append(f"## r{number}")
        for field, value in (req.get("requirement") or {}).items():
            lines.append(f"- **{field}** — {value}")
        if req.get("earlier_reversed_version"):
            lines.append(f"- *earlier, reversed*: {req['earlier_reversed_version']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# build — one role's implementation
# ---------------------------------------------------------------------------
ROLE_INSTRUCTIONS = {
    "oracle": (
        "You have the complete specification above. Implement all of it. This tree "
        "becomes the reference the grading suite is written against, so anything the "
        "specification states and this tree does not do is a fact nobody can score."
    ),
    "naive": (
        "The text above is the ENTIRE brief. There is no further specification, and "
        "there is nothing else to look for — do not go hunting the filesystem for a "
        "fuller version of this ticket, because none exists here. Build the obvious, "
        "competent thing an engineer would build from it, make your own calls where it "
        "is silent, and stop. Do not over-engineer defensively against requirements "
        "you were not given."
    ),
    "clues": (
        "The ticket is the work. The remarks below it are what colleagues said while "
        "this area was being built, and they settle things the ticket leaves open — "
        "not all of them, and never in one place. Read them as a record of decisions "
        "this team already made and honour what they settle, including where that "
        "means going beyond the ticket's own wording. Where they say nothing, make "
        "your own call. There is no fuller specification on this filesystem."
    ),
}


def clue_spec(task: Task, source: str = "remarks") -> str:
    """The ticket plus the planted remarks, exactly as the hosted clues arm shows them.

    Byte-identical to `horizon.prompt_for(task, "clues")` below its preamble, because
    the point of building this role locally is to predict that arm: a fact the local
    suite scores from the digest is a fact the hosted arm can score, and one it cannot
    is a defect in the plant that would otherwise cost a 30-minute rollout to find.
    """
    from . import horizon
    ticket = (task.dir / "ticket.md").read_text().split("\n", 1)[1].strip()
    if source == "corpus":
        # The other question: not "can an agent use these remarks" but "did the
        # information survive being split across conversations". Same facts, but
        # shown as the exchanges the corpus actually holds.
        return ticket + horizon.CORPUS_SECTION + horizon.render_exchanges(task)
    return ticket + horizon.CLUES_SECTION + horizon.render_remarks(task)


def build(slug: str, role: str, *, budget: float = 10.0,
          instruction: str | None = None,
          source: str = "remarks") -> tuple[pathlib.Path, int]:
    task = load(slug)
    # `clues` is isolated for the same reason `naive` is: its whole value is not
    # having the specification, and `out/<slug>/whole.md` sits two directories above
    # a non-isolated tree.
    isolated = role in ("naive", "clues")
    if role == "clues":
        spec = clue_spec(task, source)
    else:
        spec_file = task.dir / ("ticket.md" if role == "naive" else "whole.md")
        if not spec_file.is_file():
            raise SystemExit(f"no {spec_file}; run the earlier step first")
        spec = spec_file.read_text()

    role_note = instruction or ROLE_INSTRUCTIONS.get(
        role,
        "Implement exactly what the text above specifies, and nothing more.")
    tree = trees.seed(slug, role, isolated=isolated)
    text = prompt("build_role.md", spec=spec, role_instruction=role_note,
                  exec_cmd=f"python3 {REPO}/task_generator/cli.py exec {slug} "
                           f"--tree {tree}")
    try:
        result = agent.run(text, repo=REPO, label=f"build-{role}", cwd=tree,
                           budget_usd=budget, log_dir=_log(task))
        _record(task, f"build-{role}", text, result)
        patch, lines = trees.freeze(task.dir, role, tree)
    finally:
        if isolated:
            # The tree is gone; the patch is the record. Keeping it would put the
            # naive checkout back inside the repo, which is what isolating it was
            # for.
            shutil.rmtree(tree.parent, ignore_errors=True)
    return patch, lines


# ---------------------------------------------------------------------------
# tests — one decisive test per declared fact
# ---------------------------------------------------------------------------
def suite_command(slug: str, role: str = "oracle") -> str:
    return f"python3 {REPO}/task_generator/cli.py suite {slug} --role {role}"


def write_tests(slug: str, *, budget: float = 25.0) -> pathlib.Path:
    task = load(slug)
    oracle = trees.PERSISTENT / slug / "oracle"
    if not oracle.is_dir():
        raise SystemExit(f"no oracle tree at {oracle}; run `tg build {slug} --role oracle` first")

    facts = "\n".join(
        f"- **r{n}.{field}** — {text}" for n, field, text in declared_facts(task))
    text = prompt("write_tests.md",
                  ticket=(task.dir / "ticket.md").read_text(),
                  facts=facts,
                  whole=(task.dir / "whole.md").read_text(),
                  oracle_tree=str(oracle),
                  suite_cmd=suite_command(slug))
    result = agent.run(text, repo=REPO, label="tests", cwd=task.dir,
                       add_dirs=[SUITES, oracle], budget_usd=budget,
                       log_dir=_log(task), timeout_s=7200)
    _record(task, "tests", text, result)
    tests = task.dir / "tests"
    if not tests.is_dir():
        raise SystemExit(f"no {tests}. The reply was:\n{result.text[:2000]}")

    # The test writer can read AND write the oracle tree, and sometimes should: a
    # suite that cannot be made green against the reference has usually found a
    # real gap between the specification and the implementation. Re-freezing here
    # makes that visible instead of silent - otherwise the fixture the bracket
    # applies would be the pre-fix one, and every fact would come back `broken`
    # for a reason nothing on disk explained.
    before = task.dir / "fixtures" / "oracle.patch"
    was = before.read_text() if before.is_file() else ""
    patch, lines = trees.freeze(task.dir, "oracle", oracle)
    if patch.read_text() != was:
        print(f"note: the oracle tree changed while the suite was written "
              f"({lines} diff lines now). Read `git diff` of {patch} before trusting it.")
    return tests


# ---------------------------------------------------------------------------
# bracket / audit / report
# ---------------------------------------------------------------------------
def measure(slug: str, roles: list[str] | None = None) -> dict:
    task = load(slug)
    measured = bracket.measure(task, roles=roles)
    (task.dir / "bracket.json").write_text(json.dumps(measured, indent=1) + "\n")
    (task.dir / "bracket.md").write_text(bracket.render(task, measured))
    return measured


def audit(slug: str, *, budget: float = 4.0) -> dict:
    task = load(slug)
    measured_file = task.dir / "bracket.json"
    measured = json.loads(measured_file.read_text()) if measured_file.is_file() else {"verdicts": {}}
    tests = task.dir / "tests"
    rows = declared_facts(task)
    findings = []

    for number, field, text in rows:
        req = task.hidden_requirements[number - 1]["requirement"]
        siblings = "\n".join(f"- **{f}** — {v}" for f, v in req.items() if f != field) or "- (none)"
        others = "\n".join(
            f"- **r{n}.{f}** — {v}" for n, f, v in rows if n != number) or "- (none)"
        source = tests / f"test_r{number}.py"
        key = f"{task.id}.r{number}.{field}"
        body = prompt("audit_fact.md", ticket=(task.dir / "ticket.md").read_text(),
                      req=str(number), field=field, fact=text,
                      siblings=siblings, others=others,
                      test_source=source.read_text() if source.is_file() else "(no test file yet)",
                      bracket=f"`{key}` -> {measured['verdicts'].get(key, 'not measured')}")
        result = agent.run(body, repo=REPO, label=f"audit-r{number}-{field}",
                           cwd=task.dir, tools="", schema=schemas.AUDIT,
                           budget_usd=budget, log_dir=_log(task))
        _record(task, f"audit-r{number}-{field}", body, result)
        findings.append({"key": key, "req": number, "field": field, **result.data})

    (task.dir / "audit.json").write_text(json.dumps(findings, indent=1) + "\n")
    (task.dir / "audit.md").write_text(render_audit(task, findings, measured))
    return findings


def render_audit(task: Task, findings: list[dict], measured: dict) -> str:
    lines = [f"# Audit — {task.id} ({task.slug})", "",
             "| fact | bracket | audit | why |", "|---|---|---|---|"]
    for row in findings:
        verdict = row["verdict"]
        mark = verdict if verdict == "ship" else f"**{verdict}**"
        lines.append(f"| `{row['key']}` | {measured['verdicts'].get(row['key'], '—')} "
                     f"| {mark} | {row['recommendation'][:160]} |")
    for row in findings:
        lines += ["", f"## {row['key']} — {row['verdict']}", "",
                  f"**Divergent action.** {row['divergent_action'] or '*none named*'}", "",
                  f"**The assertion.** {row['the_assertion']}", ""]
        for name, patterns in (("Catalog A", row["catalog_a"]), ("Catalog B", row["catalog_b"])):
            hits = [p for p in patterns if p.get("applies")]
            if hits:
                lines.append(f"**{name}.**")
                lines += [f"- `{p['pattern']}` — {p['why']}" for p in hits]
            else:
                lines.append(f"**{name}.** clean")
            lines.append("")
        if row.get("blind_pass"):
            lines += ["**A blind build that passes anyway:**", "", "```",
                      row["blind_pass"], "```", ""]
        if row.get("correct_fail"):
            lines += ["**A correct build the test rejects:**", "", "```",
                      row["correct_fail"], "```", ""]
        lines += [f"**Recommendation.** {row['recommendation']}", ""]
    return "\n".join(lines)
