#!/usr/bin/env python3
"""Render phase 3's planted clues as a corpus excerpt.

This is what the `-clues` arm of each harbor task hands the agent instead of the
requirement: every remark phase 3 placed for that task, in date order, with where
and when it was said and by whom — and the herrings sitting unmarked among them.

    python3 harbor_tasks/clue_digest.py t1        # read one before shipping it

The point of the arm is to split a low blind-arm score into its causes. `-spec`
asks whether the requirement can be implemented once stated; this asks whether it
can be INFERRED from the raw remarks; the blind arm asks whether those remarks
can be found in a world at all. Only the middle question is answered here, and
only if nothing in the output states the requirement.

So most of a clue record is withheld. `settles` is the requirement in summary
form and would turn this arm into a reworded `-spec`; `covers` and
`subconclusion` say which fact a remark carries and where it sits in the tree;
`verbatim` and `forbidden_terms` are the identifiers that must appear and the
phrasings that would give it away; `carrier.why` is phase 3's own argument for
the placement; `kind` is literally "herring". `WITHHELD` names them and
`leaked_fields()` is the assert that they stayed out.

Ordering is chronological and merged across both requirements. Grouping by
requirement would tell the agent how many there are and which remarks serve
which, and date order across all three sources is the only thing that shows a
herring being overturned later — which is exactly the signal a corpus reader
gets and the reason phase 3 plants herrings strictly before their reversal.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BUILD = ROOT.parent / "data_gen" / "build"
CLUES_JSON = BUILD / "clues.json"
ARTIFACTS_JSON = BUILD / "artifacts.json"

# A task authored by `task_generator/` keeps its plant beside the task rather
# than in the phase-3 corpus, because it was never picked out of
# `data_gen/input/tasks.json` and so has no position in `clues.json` to occupy.
# Same record shape, different address: `load()` falls through to here, so
# `remarks()`, `coverage()` and `leaked_fields()` read a generated plant with no
# idea which of the two it came from.
GENERATED_PLANTS = ROOT.parent / "task_generator" / "out"

# Everything in a clue record that is answer key rather than remark. Rendering
# any of these makes the arm measure something easier than it claims to.
WITHHELD = ("settles", "covers", "subconclusion", "verbatim",
            "forbidden_terms", "clue_id", "kind", "reverses")


class MissingClues(Exception):
    """No plant on disk for this task, or none for this id."""


# =============================================================================
# Where a remark was said
# =============================================================================
def _titles() -> dict[str, str]:
    """Real titles for the page and thread ids carriers refer to.

    Carrier ids are not safe to print: several are `design-t1-plant` and
    `mail-t3-plant`, which announce the plant to anyone reading the instruction.
    The titles they resolve to are ordinary — "Prompt-level response cache
    keying", "Re: Batch job status persistence across process restarts" — and
    are what a reader would actually see in BookStack or Roundcube.
    """
    data = json.loads(ARTIFACTS_JSON.read_text())
    titles = {doc["id"]: doc["title"] for doc in data.get("docs", [])}
    titles.update({t["id"]: t["subject"] for t in data.get("threads", [])})
    return titles


def where(carrier: dict, titles: dict[str, str]) -> str:
    """One human-readable place: a channel, a wiki page, or a mail subject."""
    room = carrier.get("room") or ""
    # A generated plant carries the page or thread title on the carrier, because
    # it invents rooms that no `artifacts.json` has ever heard of. Trusting it
    # first also keeps a title that was renamed after the plant was written.
    if carrier.get("title") and room.startswith(("page:", "thread:")):
        kind = "wiki" if room.startswith("page:") else "mail"
        return f"{kind}: {carrier['title']}"
    if room.startswith("page:"):
        ident = room[len("page:"):]
        return f"wiki: {titles[ident]}" if ident in titles else _unresolved(ident)
    if room.startswith("thread:"):
        ident = room[len("thread:"):]
        return f"mail: {titles[ident]}" if ident in titles else _unresolved(ident)
    return room or carrier.get("channel") or carrier.get("source", "somewhere")


def _unresolved(ident: str) -> str:
    raise MissingClues(
        f"carrier id {ident!r} has no title in {ARTIFACTS_JSON.name}; printing "
        "the id would leak the plant, so the build stops here instead")


# =============================================================================
# The digest
# =============================================================================
def load(task_id: str, title: str | None = None) -> dict:
    """The plant for a task, matched by TITLE when one is given.

    The id in `clues.json` is NOT the id in `tasks.json`. `phase3_plant.py`
    renumbers the picked subset — `--pick t1,t12,t23,t40` writes them out as
    t1..t4 — so an id match silently pairs a task with another feature's
    remarks. It did: two `-clues` runs graded agents that had been handed
    months of discussion about a different part of curator.

    Title is the only field both files agree on, so it is the join key. The id
    remains the fallback for a caller that has nothing else, and callers that
    can pass a title should.
    """
    tasks, data = [], {}
    if CLUES_JSON.exists():
        data = json.loads(CLUES_JSON.read_text())
        tasks = data.get("tasks", [])
    if title is not None:
        for task in tasks:
            if task.get("title") == title:
                return {"task": task, "generated_at": data.get("generated_at", ""),
                        "plant_id": task.get("task_id")}
        found = generated(title)
        if found:
            return found
        raise MissingClues(
            f"no plant for {title!r} — the phase-3 plant holds "
            f"{[t.get('title', '?')[:40] for t in tasks]} and no generated task "
            f"under {GENERATED_PLANTS} claims that title either")
    for task in tasks:
        if task["task_id"] == task_id:
            return {"task": task, "generated_at": data.get("generated_at", ""),
                    "plant_id": task_id}
    if not CLUES_JSON.exists():
        raise MissingClues(f"no plant at {CLUES_JSON}")
    raise MissingClues(f"{task_id} is not in {CLUES_JSON.name}")


def generated(title: str) -> dict | None:
    """The `task_generator` plant claiming this title, if one is on disk.

    Matched on title for the same reason the phase-3 lookup is: the two id
    spaces are unrelated -- a generated task is `g1` and a phase-3 one is `t1`
    after renumbering -- and title is the only field both agree on. Every
    generated plant is opened rather than guessing the slug from the title,
    because the slug is chosen by the author and need not be derivable from it.
    """
    for plant in sorted(GENERATED_PLANTS.glob("*/clues/plant.json")):
        ledger = json.loads(plant.read_text())
        for task in ledger.get("tasks", []):
            if task.get("title") == title:
                return {"task": task, "plant_id": task.get("task_id"),
                        # `settled_at` when a settle pass has run, else the
                        # plant date: whichever last changed what a reader sees.
                        "generated_at": (ledger.get("settled_at")
                                         or ledger.get("generated_at", ""))}
    return None


def remarks(task: dict) -> list[dict]:
    """Every planted item for the task, clues and herrings alike, by date.

    Herrings are not separated out and not marked. A herring is a decision the
    team really made and later reversed; labelled as a herring it stops being
    one, and the agent gets a cleaner picture than any corpus would give.
    """
    items = [clue for req in task["requirements"] for clue in req["clues"]]
    return sorted(items, key=lambda c: (c["carrier"].get("date", ""),
                                        c["carrier"].get("index") or 0,
                                        c["clue_id"]))


def render(task_id: str, title: str | None = None) -> str:
    found = load(task_id, title)
    titles = _titles()
    lines = [
        "## What the team said",
        "",
        "Chat, the wiki and internal mail, over the months this area was being "
        "worked on, oldest first. Some of it is people thinking aloud and some "
        "of it was settled later.",
        "",
        # Stamped so a task built against a superseded plant is visible rather
        # than silent: phase 3 rewrites clues.json wholesale on every re-plant,
        # and an instruction quoting remarks the corpus no longer contains
        # would otherwise look exactly like a current one.
        f"<!-- planted {found['generated_at']} -->",
        "",
    ]
    for clue in remarks(found["task"]):
        carrier = clue["carrier"]
        lines.append(f"**{carrier.get('date', '')} · {where(carrier, titles)} · "
                     f"{clue['holder']}**")
        lines.append("")
        # Blockquote every line, so a multi-paragraph wiki extract stays one
        # quotation rather than half quote and half instruction text.
        for para in clue["text"].strip().splitlines():
            lines.append(f"> {para}".rstrip())
        lines.append("")
    return "\n".join(lines)


def coverage(task: dict) -> dict[str, list[str]]:
    """Fact fields of each requirement that no included remark carries.

    A fact nothing carries cannot be inferred, so the arm would fail it for a
    build defect rather than for a result. Checked at build time, where it reads
    as a broken plant; discovered after a run it reads as a finding about the
    agent.
    """
    gaps = {}
    for req in task["requirements"]:
        carried = {field for clue in req["clues"] for field in clue["covers"]}
        stated = {field for field, text in req["requirement"].items() if text}
        missing = sorted(stated - carried)
        if missing:
            gaps[req["req_id"]] = missing
    return gaps


def leaked_fields(task: dict, text: str) -> list[str]:
    """Withheld strings that reached the rendered instruction anyway.

    Compares against the plant itself rather than a list of banned words: the
    thing that must not appear is this task's own answer key, and a `settles`
    clause shares most of its vocabulary with the remark it summarises, so
    nothing shorter than a full-string check is decisive.
    """
    hay = " ".join(text.split()).lower()
    leaks = []
    for req in task["requirements"]:
        for clue in req["clues"]:
            for field in ("settles", "subconclusion"):
                value = " ".join(str(clue.get(field, "")).split()).lower()
                if len(value) > 25 and value in hay:
                    leaks.append(f"{clue['clue_id']}.{field}")
            why = " ".join(str(clue["carrier"].get("why", "")).split()).lower()
            if len(why) > 25 and why in hay:
                leaks.append(f"{clue['clue_id']}.carrier.why")
        for sub in req.get("subconclusions", []):
            value = " ".join(sub.get("text", "").split()).lower()
            if len(value) > 25 and value in hay:
                leaks.append(f"{req['req_id']}.{sub['id']}")
    # The plant's own filenames say what they are.
    if "-plant" in hay:
        leaks.append("carrier slug ('-plant')")
    return leaks


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print(f"usage: {pathlib.Path(argv[0]).name} <task_id>", file=sys.stderr)
        return 2
    try:
        found = load(argv[1])
        text = render(argv[1])
    except MissingClues as exc:
        print(exc, file=sys.stderr)
        return 1
    task = found["task"]
    print(text)
    gaps = coverage(task)
    leaks = leaked_fields(task, text)
    n = len(remarks(task))
    print(f"--- {n} remarks, planted {found['generated_at']}", file=sys.stderr)
    if gaps:
        print(f"--- facts no remark carries: {gaps}", file=sys.stderr)
    if leaks:
        print(f"--- LEAKED: {leaks}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
