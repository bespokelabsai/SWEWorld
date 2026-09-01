"""Is every graded thing something somebody actually SAID, or only something a
reader could have worked out?

The middle tier between the two checks that already exist. `surface.py` is free and
asks one question -- is this name typed anywhere -- which the plant now passes. And
`prove.py` costs a build and answers with a number, so a 0.70 says something is
wrong and not what. Neither catches the failure that is actually shipping:

    the corpus contains the evidence for a decision and nobody ever makes it.

That is not a hypothetical. The hosted clues arm has never cleared 0.70 against a
spec arm that scores 1.00, and it splits in two -- a rollout either engages a
requirement and scores 0.80-0.90, or ignores it and scores 0.00-0.50. Remarks that
report a symptom and stop leave a reader free to decide the symptom was not their
problem. The remark

    "an auto run gave me 9 request files and nothing says which rows landed in
     requests_3.jsonl, had to reopen all of them to find one promt"

is true, is in the right room, is in the right voice, and tells nobody to write a
file. Every cheap check passes it.

**The claims come from the tests, not from the prose.** A requirement's prose is a
250-word paragraph; its test makes seventeen assertions. Those assertions are what
is actually scored, they are atomic by construction, and enumerating them costs
nothing -- so "does the corpus carry every part of the requirement" becomes "for
each assertion, was a reader told, or left to guess". The prose can say whatever it
likes; an implementation is graded on the assertions.

Four verdicts, and the one that matters is the middle one. `stated` is the bar,
`absent` is the obvious hole, `not_required` excuses an assertion that checks the
test's own fixture -- and `implied` is the defect this module exists for, because
it is the verdict every remark above gets and the only one that looks like a pass.
"""
from __future__ import annotations

import ast
import collections
import dataclasses
import hashlib
import json
import pathlib

from . import agent, clue_schemas as cs, clues, emit
from .corpus import Corpus
from .model import FACT_FIELDS, REPO, Task, load

VERDICTS = ("stated", "implied", "absent", "not_required")
# `stated` is the only pass. `implied` is counted as a finding because a reader who
# guesses right and a reader who was told produce the same code only sometimes, and
# the hosted arm is where "sometimes" shows up as a 0.30.
CARRIED = ("stated", "not_required")


@dataclasses.dataclass
class Claim:
    """One assertion in a graded test: a thing the corpus has to have told somebody."""

    id: str
    key: str
    ref: str
    line: int
    source: str

    @property
    def field(self) -> str:
        return self.key.rsplit(".", 1)[1]

    @property
    def req_id(self) -> str:
        return self.key.rsplit(".", 1)[0]


def _lead(lines: list[str], lineno: int) -> list[str]:
    """The comment block directly above a statement.

    Kept because it is where the suite explains itself -- "the surviving numbering is
    exactly the one the plan asked for" says what the assertion below it means far
    better than the expression does, and a judge shown the expression alone marks
    half of them `not_required`.
    """
    out = []
    index = lineno - 2
    while index >= 0 and lines[index].strip().startswith("#"):
        out.insert(0, lines[index])
        index -= 1
    return out


def _statements(node: ast.AST) -> list[ast.AST]:
    """Every assertion in a test, including the raises it wraps around.

    `pytest.raises` counts: `with pytest.raises(BatchPlanTooFragmentedError)` is the
    assertion that the error type exists and is what comes out, which is exactly the
    kind of thing nobody in a chat log ever says out loud.
    """
    out = []
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            out.append(child)
        elif isinstance(child, ast.With):
            for item in child.items:
                call = item.context_expr
                if isinstance(call, ast.Call) and getattr(call.func, "attr", "") == "raises":
                    out.append(call)
    return sorted(out, key=lambda n: n.lineno)


def claims(task: Task) -> dict[str, list[Claim]]:
    """Fact key -> the assertions that grade it. Free, deterministic, no model."""
    tests = task.dir / "tests"
    graded = emit.suite_facts(tests, task.id)
    bodies: dict[str, tuple[ast.AST, list[str]]] = {}
    for path in sorted(tests.glob("test_*.py")):
        lines = path.read_text().splitlines()
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                bodies[f"{path.stem}::{node.name}"] = (node, lines)

    out: dict[str, list[Claim]] = {}
    for key in sorted(graded):
        if key.endswith("open_feature"):
            continue        # the ticket states the open feature; the corpus owes it nothing
        rows = []
        for ref in graded[key]:
            if ref not in bodies:
                continue
            node, lines = bodies[ref]
            for statement in _statements(node):
                text = "\n".join(_lead(lines, statement.lineno)
                                 + lines[statement.lineno - 1:statement.end_lineno])
                rows.append(Claim(id=f"{key}#{len(rows) + 1}", key=key, ref=ref,
                                  line=statement.lineno, source=text.strip()))
        out[key] = rows
    return out


# ---------------------------------------------------------------------------
# what the judge is shown
# ---------------------------------------------------------------------------
def render_claims(rows: list[Claim]) -> str:
    return "\n\n".join(f"### `{c.id}`\n\n```python\n{c.source}\n```" for c in rows)


def render_remarks(req: dict, ids: list[str] | None = None) -> str:
    """Every placed remark in a requirement, in date order, as a reader meets them.

    The whole requirement and not the fact's own slice, for the reason `repair`
    already learned: the remark that broke a fact was filed under a different one,
    said the hash is only reached "when there's a line to feed it", and was dated
    after the two remarks that had the empty case right.
    """
    rows = [c for c in req["clues"] if c.get("carrier")]
    if ids is not None:
        rows = [c for c in rows if c["clue_id"] in ids]
    rows.sort(key=lambda c: (c["carrier"].get("date") or "", c["clue_id"]))
    out = []
    for clue in rows:
        car = clue["carrier"]
        out.append(f"### `{clue['clue_id']}` — **{clue['holder']}**, "
                   f"{car.get('date')}, {car.get('room')}\n\n> {clue['text']}")
    return "\n\n".join(out) or "*(no placed remarks)*"


def render_steps(req: dict) -> str:
    """The subconclusions with their remarks, marked problem or decision.

    The fix stage needs this to honour "keep one person still complaining": it cannot
    know which remark is a step's last symptom without seeing the step.
    """
    out = []
    for sub in req["subconclusions"]:
        mine = [c for c in req["clues"]
                if c.get("subconclusion") == sub["id"] and c.get("carrier")]
        lines = [f"### `{sub['id']}` — {sub['text']}", ""]
        for clue in sorted(mine, key=lambda c: c["carrier"].get("date") or ""):
            lines.append(f"- `{clue['clue_id']}` ({clues.stance(clue)}) — {clue['holder']}")
        out.append("\n".join(lines))
    return "\n\n".join(out) or "*(no steps)*"


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------
def judge(task: Task, req: dict, key: str, rows: list[Claim], budget: float) -> dict:
    """One call per fact: for each assertion, was a reader told or left to guess?"""
    field = key.rsplit(".", 1)[1]
    text = clues.prompt("clue_claims.md", key=key, req_id=req["req_id"],
                        fact=(req["requirement"] or {}).get(field) or "(undeclared)",
                        claims=render_claims(rows), remarks=render_remarks(req))
    result = agent.run(text, repo=REPO, label=f"clue-claims-{key}", cwd=task.dir,
                       tools="", schema=cs.judge_schema([c.id for c in rows]),
                       budget_usd=budget, log_dir=task.dir / "logs")
    clues._record(task, f"clue-claims-{key}", text, result)
    by_id = {c.id: c for c in rows}
    out = {}
    for row in (result.data or {}).get("verdicts") or []:
        claim = by_id.get(row.get("claim"))
        if not claim:
            continue
        out[claim.id] = {"key": key, "verdict": row.get("verdict", "absent"),
                         "why": row.get("why", ""), "clues": row.get("clues") or [],
                         "source": claim.source}
    # A claim the judge skipped is not a claim that passed.
    for claim in rows:
        out.setdefault(claim.id, {"key": key, "verdict": "absent",
                                  "why": "the judge returned no verdict for it",
                                  "clues": [], "source": claim.source})
    return out


def render_missing(verdicts: dict, rows: list[Claim]) -> str:
    out = []
    for claim in rows:
        row = verdicts.get(claim.id) or {}
        if row.get("verdict") in CARRIED:
            continue
        near = ", ".join(f"`{c}`" for c in row.get("clues") or []) or "nothing"
        out.append(f"### `{claim.id}` — **{row.get('verdict')}**\n\n"
                   f"```python\n{claim.source}\n```\n\n"
                   f"Closest remarks: {near}. {row.get('why', '')}")
    return "\n\n".join(out)


def fix(task: Task, corpus: Corpus, req: dict, key: str, verdicts: dict,
        rows: list[Claim], people: list[str], reach: dict, budget: float) -> dict:
    """Rewrite the remarks that leave a claim implied, and mint one where none can."""
    field = key.rsplit(".", 1)[1]
    text = clues.prompt("clue_settle.md", key=key,
                        fact=(req["requirement"] or {}).get(field) or "(undeclared)",
                        missing=render_missing(verdicts, rows),
                        remarks=render_remarks(req), steps=render_steps(req),
                        roster=clues.roster_lines(corpus, people, reach))
    result = agent.run(text, repo=REPO, label=f"clue-settle-{key}", cwd=task.dir,
                       tools="", schema=cs.settle_schema(people, list(FACT_FIELDS),
                                                         list(cs.SOURCES)),
                       budget_usd=budget, log_dir=task.dir / "logs")
    clues._record(task, f"clue-settle-{key}", text, result)
    return result.data or {}


def corpus_digest(entry: dict) -> str:
    """A fingerprint of exactly what the judge was shown: every placed remark's text.

    The workflow is `--dry-run`, read the report, then apply -- and a second judging
    pass would cost the same money to re-derive verdicts the reader has already
    looked at, and could quietly return different ones. Verdicts are reused while the
    remarks they were taken against are unchanged, and thrown away the moment one
    moves.
    """
    rows = sorted((c["clue_id"], c["text"]) for req in entry["requirements"]
                  for c in req["clues"] if c.get("carrier"))
    return hashlib.sha256(repr(rows).encode()).hexdigest()[:16]


def settle(slug: str, *, run: str | None = None, budget: float = 3.0,
           dry_run: bool = False, rejudge: bool = False) -> dict:
    """Judge every graded assertion against the plant, then say the ones nobody said."""
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    out_dir = task.dir / "clues"
    plant = out_dir / "plant.json"
    if not plant.is_file():
        raise SystemExit(f"no plant at {plant}; run `cli.py clues {slug}` first")
    ledger = json.loads(plant.read_text())
    entry = ledger["tasks"][0]
    by_req = {req["req_id"]: req for req in entry["requirements"]}
    every = claims(task)
    digest = corpus_digest(entry)

    cached = out_dir / "claims.json"
    previous = json.loads(cached.read_text()) if cached.is_file() else {}
    if not rejudge and previous.get("digest") == digest:
        print(f"reusing the verdicts already taken against these remarks ({digest})")
        verdicts = previous["verdicts"]
    else:
        verdicts = {}
        for key, rows in sorted(every.items()):
            req = by_req.get(key.rsplit(".", 1)[0])
            if not req or not rows:
                continue
            verdicts.update(judge(task, req, key, rows, budget))

    report = {"slug": slug, "task": task.id, "digest": digest, "verdicts": verdicts,
              "counts": {v: sum(1 for row in verdicts.values() if row["verdict"] == v)
                         for v in VERDICTS}}
    # Worst fact first. Each fix call is shown the remarks as they stand, and
    # additions land before the next call is made -- so the fact with the most holes
    # writes the remark the neighbouring facts then see and do not duplicate. g1's
    # per-batch row shape is missing from `rule`, `observability` and
    # `exclusions_or_crossover` at once, and alphabetical order fixes it last.
    holes = collections.Counter(row["key"] for row in verdicts.values()
                                if row["verdict"] not in CARRIED)
    short = [key for key, _ in holes.most_common()]
    report["short"] = short
    if dry_run or not short:
        _write(task, corpus, ledger, report, write_plant=False)
        return {**report, "rewritten": [], "added": [], "unfixed": []}

    reach = corpus.reachable(tuple(ledger["windows"]["clues"]))
    people = [p for p in corpus.people() if p in corpus.cast and p in reach]
    used, per_channel, per_page = clues.occupancy(entry)
    changed = {"rewritten": [], "added": [], "unfixed": []}

    for key in short:
        req = by_req[key.rsplit(".", 1)[0]]
        data = fix(task, corpus, req, key, verdicts, every[key], people, reach, budget)
        by_id = {c["clue_id"]: c for r in entry["requirements"] for c in r["clues"]}
        for row in data.get("rewrites") or []:
            clue = by_id.get(row.get("clue_id"))
            if not clue or not (row.get("text") or "").strip():
                changed["unfixed"].append(f"{key}: no such remark {row.get('clue_id')!r}")
                continue
            kept, why_not = clues.keep_wording(
                {**clue, "verbatim": row.get("verbatim") or clue.get("verbatim") or []},
                row["text"])
            if why_not:
                changed["unfixed"].append(f"{clue['clue_id']}: {why_not}")
                continue
            clue["settled_from"] = clue.get("settled_from") or clue["text"]
            clue["text"] = kept
            clue["verbatim"] = sorted(set((clue.get("verbatim") or [])
                                          + (row.get("verbatim") or [])))
            # The tree stage banned these words to stop the remark giving the
            # requirement away; settle has just decided the corpus must say this
            # one, and the ban is stale the moment that call is made. Left in
            # place, `finish()` reports four settled remarks as defective for
            # doing exactly the job they were rewritten to do.
            clue["forbidden_terms"] = [t for t in clue.get("forbidden_terms") or []
                                       if t.lower() not in kept.lower()]
            clue["settle_note"] = row.get("why", "")
            changed["rewritten"].append(f"{clue['clue_id']} ({key})")

        known = {s["id"] for s in req["subconclusions"]}
        for extra in data.get("additions") or []:
            if not (extra.get("text") or "").strip() or extra.get("holder") not in people:
                changed["unfixed"].append(f"{key}: an addition named nobody who exists")
                continue
            sub = extra.get("subconclusion") or ""
            # `repair` did not namespace this and shipped remarks filed under a
            # subconclusion that does not exist; `normalise` prefixes at plan time and
            # this is the same prefix applied to the same field.
            if sub and sub not in known:
                sub = f"{req['req_id']}.{sub.split('.')[-1]}"
            leaf = {"id": f"{req['req_id']}.say{len(req['clues'])}",
                    "text": extra["text"], "holder": extra["holder"],
                    "source": extra.get("source") or "slack",
                    "settles": extra.get("settles") or "",
                    "leaves_open": extra.get("leaves_open") or "",
                    "verbatim": extra.get("verbatim") or [],
                    "forbidden_terms": extra.get("forbidden_terms") or [],
                    "subconclusion": sub if sub in known else "",
                    "covers": [key.rsplit(".", 1)[1]], "kind": "clue"}
            leaf = clues.place_one(task, corpus, leaf,
                                   tuple(ledger["windows"]["clues"]),
                                   used, per_channel, budget, per_page)
            # Placement rewrites the remark to fit the room it lands in, and
            # `clue_place.md` used to be told to stop at the observation -- so a
            # sentence minted here precisely because it states a decision could come
            # back as one more person noticing something. The identifier guard cannot
            # see that; this can.
            if leaf.get("adapted") and clues.hedged(leaf["adapted"]) \
                    and not clues.hedged(leaf["text"]):
                leaf["placement"]["adapted_rejected"] = leaf["adapted"]
                leaf["adapted"] = leaf["text"]
            if not leaf.get("slot"):
                changed["unfixed"].append(f"{key}: the new remark could not be placed")
                continue
            req["clues"].append(clues.as_row(leaf))
            changed["added"].append(f"{leaf['id']} ({key}) -> {leaf['slot']['room']}")

    # The verdicts in the report are the ones that PROVOKED the rewrites, so the
    # report and the plant it sits beside no longer describe the same corpus. Saying
    # so beats a reader trusting a table that was true ten minutes ago.
    report["applied"] = changed
    _write(task, corpus, ledger, report, write_plant=True)
    return {**report, **changed}


def _write(task: Task, corpus: Corpus, ledger: dict, report: dict,
           *, write_plant: bool) -> None:
    out = task.dir / "clues"
    out.mkdir(parents=True, exist_ok=True)
    (out / "claims.json").write_text(json.dumps(report, indent=1) + "\n")
    (out / "settled.md").write_text(render(task, report))
    if write_plant:
        clues.finish(task, corpus, ledger, "settled_at")


def render(task: Task, report: dict) -> str:
    counts = report["counts"]
    total = sum(counts.values())
    lines = [f"# Was every graded thing said, or only implied? — {task.id}", "",
             f"**{counts['stated']} of {total}** assertions rest on something a remark "
             "says outright.", "",
             f"- `stated` **{counts['stated']}** — a reader was told",
             f"- `implied` **{counts['implied']}** — a reader has to work it out, and "
             "may not",
             f"- `absent` **{counts['absent']}** — nothing in the corpus bears on it",
             f"- `not_required` **{counts['not_required']}** — the assertion checks the "
             "suite's own fixture", "",
             "`implied` is a finding, not a pass. The spec arm scores 1.00 and the "
             "clues arm 0.70 on the same suite, and the gap is made of assertions a "
             "generous reading calls carried.", ""]
    if report.get("applied"):
        done = report["applied"]
        lines += [f"> **These verdicts are what provoked the rewrites, not what the "
                  f"plant says now.** {len(done['rewritten'])} remark(s) rewritten, "
                  f"{len(done['added'])} added, {len(done['unfixed'])} not fixed. "
                  f"Re-run `settle --dry-run` for the verdicts on the corpus as it "
                  f"now stands.", ""]
    lines += ["| claim | verdict | remarks | why |", "|---|---|---|---|"]
    for claim_id, row in sorted(report["verdicts"].items()):
        mark = {"stated": "stated", "implied": "**implied**",
                "absent": "**absent**", "not_required": "n/a"}.get(row["verdict"], "?")
        named = ", ".join(f"`{c}`" for c in row["clues"]) or "—"
        lines.append(f"| `{claim_id}` | {mark} | {named} | "
                     f"{row['why'].replace('|', chr(92) + '|')[:200]} |")
    for claim_id, row in sorted(report["verdicts"].items()):
        if row["verdict"] in CARRIED:
            continue
        lines += ["", f"### `{claim_id}` — {row['verdict']}", "",
                  "```python", row["source"], "```", "", row["why"]]
    return "\n".join(lines) + "\n"
