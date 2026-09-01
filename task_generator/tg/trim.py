"""The hidden requirement, reduced to what the suite actually grades.

`g1.r1.rule` is 169 words and its test makes seventeen assertions. Nothing is
scored except those assertions, so every word beyond them is weight: an implementer
reading the `-spec` arm follows prose that is longer than the thing being measured,
and the clue planter has to carry claims no grader will ever ask about.

Two things this is NOT, because both are tempting and both are wrong:

**It is not deleting untested requirements.** Measured before writing this, only 21
of ~200 code identifiers in g1's prose appear nowhere in the suite, and most of
those are spelling -- the prose writes `err.limit` where the test reads
`read_field(err, "limit")`. The prose is not full of demands nobody checks. It is
out of proportion to what it demands.

**It is not a rewrite of the task.** The tests do not move, the fact keys do not
move, the oracle does not move. Only the sentences the `-spec` arm shows an
implementer, and the sentences `surface.py` intersects with the tests to decide what
the clues must name. If the spec arm does not still score 1.00 afterwards, the trim
removed something load-bearing and the task is worse, not smaller -- which is why
`cli.py trim` prints that as the next step and why the original is kept beside it.

Assertions the clue judge marked `not_required` are excluded from what the new prose
must cover: those check the suite's own fixture (`assert 1 <= len(plan) <= 5,
"fixture drift"`), and prose that explains a fixture is exactly the kind of weight
being removed.
"""
from __future__ import annotations

import dataclasses
import json
import shutil

from . import agent, settle
from .model import FACT_FIELDS, REPO, Task, load
from .steps import prompt, _record


def graded_only(task: Task) -> dict[str, list[settle.Claim]]:
    """Per fact, the assertions the trimmed prose has to keep covering."""
    every = settle.claims(task)
    report = task.dir / "clues" / "claims.json"
    skip = set()
    if report.is_file():
        skip = {cid for cid, row in json.loads(report.read_text())["verdicts"].items()
                if row["verdict"] == "not_required"}
    return {key: [c for c in rows if c.id not in skip] for key, rows in every.items()}


def shorter(was: str, now: str) -> tuple[str, str | None]:
    """Refuse a trim that is not one. The same guard shape as `clues.keep_wording`.

    The first version of `trim_fact.md` said dropping a graded claim was much worse
    than keeping padding, and handed the model the assertion list. It transcribed the
    assertions into prose: 750 words became 1590, a 27-word sentence came back as 100
    words of bullets saying the identical thing, and its own `dropped` list claimed
    to have removed a phrase while quadrupling the length. A prompt can be talked out
    of a length budget; this cannot.
    """
    if not now.strip():
        return was, "returned nothing"
    if len(now.split()) > len(was.split()):
        return was, (f"came back longer ({len(was.split())} -> {len(now.split())} "
                     "words); that is a redraft, not a trim")
    return now, None


def cached(task: Task, key: str, rendered: str) -> dict | None:
    """The reply this exact prompt already got, if it is still on disk.

    `agent.run` logs every prompt beside its reply, so a run that died between the
    last model call and the write has already paid for all ten answers. The prompt
    text is the cache key rather than the fact text, because it carries the
    assertions and the word budget too -- a changed prompt file must re-ask.
    """
    logs = task.dir / "logs"
    asked, replied = logs / f"trim-{key}.prompt.md", logs / f"trim-{key}.stdout.json"
    if not (asked.is_file() and replied.is_file()):
        return None
    if asked.read_text() != rendered:
        return None
    try:
        return json.loads(json.loads(replied.read_text())["result"])
    except (KeyError, ValueError):
        return None


def stage(task: Task, key: str, text: str, rows: list[settle.Claim],
          budget: float, rerun: bool = False) -> dict:
    body = "\n\n".join(f"### `{c.id}`\n\n```python\n{c.source}\n```" for c in rows)
    words = len(text.split())
    rendered = prompt("trim_fact.md", key=key, fact=text, claims=body,
                      count=str(len(rows)), words=str(words),
                      target=str(max(20, int(words * 0.7))))
    if not rerun:
        already = cached(task, key, rendered)
        if already is not None:
            print(f"  {key}: reusing the answer already on disk")
            return already
    result = agent.run(rendered, repo=REPO, label=f"trim-{key}", cwd=task.dir,
                       tools="", schema=SCHEMA, budget_usd=budget,
                       log_dir=task.dir / "logs")
    _record(task, f"trim-{key}", rendered, result)
    return result.data or {}


SCHEMA = {
    "type": "object",
    "required": ["requirement", "dropped"],
    "properties": {
        "requirement": {"type": "string", "description":
                        "the fact restated so that every listed assertion follows "
                        "from it and nothing else is claimed"},
        "dropped": {"type": "array", "items": {"type": "string"},
                    "description": "each thing the old wording said that no "
                                   "assertion checks, one per entry"},
        "kept_because": {"type": "string", "description":
                         "anything that reads like padding but had to stay, and "
                         "which assertion forced it"},
    },
}


def trim(slug: str, *, budget: float = 3.0, dry_run: bool = False,
         rerun: bool = False) -> dict:
    """Rewrite every hidden requirement to exactly its graded assertions."""
    task = load(slug)
    rows = graded_only(task)
    out = {"slug": slug, "facts": {}}

    for number, req in enumerate(task.hidden_requirements, 1):
        for field in FACT_FIELDS:
            text = (req.get("requirement") or {}).get(field)
            if not text:
                continue
            key = f"{task.id}.r{number}.{field}"
            claims = rows.get(key) or []
            if not claims:
                out["facts"][key] = {"skipped": "no graded assertion reaches it"}
                continue
            data = stage(task, key, text, claims, budget, rerun)
            new, why_not = shorter(text, (data.get("requirement") or "").strip())
            if why_not:
                out["facts"][key] = {"rejected": why_not,
                                     "was_words": len(text.split()),
                                     "returned": (data.get("requirement") or "")[:400]}
                continue
            out["facts"][key] = {
                "was_words": len(text.split()), "now_words": len(new.split()),
                "assertions": len(claims), "dropped": data.get("dropped") or [],
                "kept_because": data.get("kept_because", ""),
                "was": text, "now": new}
            if not dry_run:
                req["requirement"][field] = new

    if not dry_run:
        # The original is the evidence for whether the trim was safe, so it is kept
        # under a name that says what it was rather than overwritten.
        shutil.copy2(task.dir / "task.json", task.dir / "task.untrimmed.json")
        if (task.dir / "hidden.md").is_file():
            shutil.copy2(task.dir / "hidden.md", task.dir / "hidden.untrimmed.md")
        task.save()
        (task.dir / "hidden.md").write_text(render_hidden(task))
    (task.dir / "trim.json").write_text(json.dumps(out, indent=1) + "\n")
    (task.dir / "trim.md").write_text(render(task, out))
    return out


def render_hidden(task: Task) -> str:
    lines = [f"# Hidden requirements — {task.id} ({task.slug})", ""]
    for number, req in enumerate(task.hidden_requirements, 1):
        lines += [f"## r{number}"]
        for field in FACT_FIELDS:
            text = (req.get("requirement") or {}).get(field)
            if text:
                lines.append(f"- **{field}** — {text}")
        if req.get("earlier_reversed_version"):
            lines.append(f"- *earlier, reversed*: {req['earlier_reversed_version']}")
        lines.append("")
    return "\n".join(lines)


def render(task: Task, out: dict) -> str:
    rows = [(k, v) for k, v in out["facts"].items() if "now" in v]
    was = sum(v["was_words"] for _, v in rows)
    now = sum(v["now_words"] for _, v in rows)
    lines = [f"# {task.id} — the requirement, reduced to what is graded", "",
             f"**{was} words → {now}** across {len(rows)} facts and "
             f"{sum(v['assertions'] for _, v in rows)} graded assertions.", "",
             "The tests, the fact keys and the oracle are untouched. What changed is "
             "what the `-spec` arm shows an implementer, and therefore what the clues "
             "have to carry.", "",
             "| fact | words | assertions | dropped |", "|---|---|---|---|"]
    for key, v in rows:
        lines.append(f"| `{key}` | {v['was_words']} → {v['now_words']} | "
                     f"{v['assertions']} | {len(v['dropped'])} |")
    for key, v in rows:
        lines += ["", f"## `{key}`", "", f"**Now ({v['now_words']} words):**", "",
                  v["now"], ""]
        if v["dropped"]:
            lines += ["**Dropped, because no assertion checks it:**", ""]
            lines += [f"- {d}" for d in v["dropped"]]
        if v.get("kept_because"):
            lines += ["", f"**Kept despite looking like padding:** {v['kept_because']}"]
    return "\n".join(lines) + "\n"
