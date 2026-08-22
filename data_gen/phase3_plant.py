#!/usr/bin/env python3
"""Phase 3 — hide a requirement in the corpus, one innocuous remark at a time.

A task states a feature openly and hides one or more requirements that are never
written down anywhere. This decomposes each hidden requirement into a MuSR-style
tree — subconclusions a reader must infer, and leaves nobody would look twice at
— and scatters the leaves across chat, the wiki, internal mail and the forge. An
agent asked to build the feature has to put them back together.

Alongside them go the decisions this team made and later reversed, planted
strictly *before* the clue that reverses them. Read in date order the reversal is
recoverable; read one conversation at a time it is not, and an agent that stops
at the first answer builds the wrong thing.

Two priorities pull against each other and both matter. A clue only works if it
lands where that conversation would really have happened, said by someone who
already owns that code — and a requirement recoverable from one conversation,
one week or one source is not hidden at all. So placement is scored rather than
assigned: candidates are filtered for plausibility, classified by how on-topic
the room already is, and then chosen — subject to spread rules a plausible
placement still has to satisfy.

Nothing is written until the tree is proved solvable: the leaves go back to a
model with the answer removed, and every part of the requirement has to be
recoverable from them alone.

    phase3_plant.py --dry-run     # decompose, place, prove, report; write nothing
    phase3_plant.py --no-refresh  # replay from cache, free
    phase3_plant.py               # plant

Writes `build/clues.json` (the ledger to track), `build/phase3_plant.md` (the
human read), `build/phase3_forge.json` (issues and PR comments carrying clues),
and patches `build/days/specs/*.json` and `build/artifacts.json`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402
from phase2_days import tokens  # noqa: E402

SCHEMA_VERSION = 1

DEFAULT_TASKS = Path(__file__).resolve().parent / "input" / "tasks.json"
DEFAULT_COMPANY = rl.DEFAULT_BUILD_DIR / "company_grounding.json"
DEFAULT_TIMELINE = rl.DEFAULT_BUILD_DIR / "timeline.json"
DEFAULT_ARTIFACTS = rl.DEFAULT_BUILD_DIR / "artifacts.json"
DEFAULT_SPECS = rl.DEFAULT_BUILD_DIR / "days" / "specs"
DEFAULT_CLUES = rl.DEFAULT_BUILD_DIR / "clues.json"
DEFAULT_REPORT = rl.DEFAULT_BUILD_DIR / "phase3_plant.md"
DEFAULT_FORGE = rl.DEFAULT_BUILD_DIR / "phase3_forge.json"
DEFAULT_FORGE_PLAN = rl.DEFAULT_BUILD_DIR / "forge_plan.json"

# The five sub-fields of a `requirement` are its atomic facts. Whichever a task
# supplies must each be carried by at least one leaf; one nobody carries is a
# requirement the corpus cannot teach, which makes the task unscoreable.
FACT_FIELDS = ("rule", "scope", "exclusions_or_crossover", "failure_behavior",
               "observability")

# A constraint gets settled in a room where work is argued about. A remark that
# only ever surfaced in the social or announcement channel would read as
# arbitrary, and no amount of good placement rescues it.
DELIBERATION = {"deliberation", "troubleshooting", "coordination"}

# Spread. Below these a requirement is recoverable from one sitting.
MIN_SOURCES, MIN_WEEKS, MIN_CHANNELS = 2, 3, 2

SOURCES = ("slack", "notion", "email", "github")


# =============================================================================
# Inputs
# =============================================================================
def load(path: Path, what: str) -> dict:
    if not path.exists():
        rl.fail(f"{path} does not exist — {what}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        rl.fail(f"{path} is empty — {what}")
    return json.loads(text)


class Corpus:
    """The world as it stands, and every place a clue could be dropped into it."""

    def __init__(self, args):
        raw = load(args.tasks, "add the tasks to plant")
        tasks = raw["tasks"] if isinstance(raw, dict) else raw
        self.tasks = tasks[:args.limit] if args.limit else tasks

        # The tasks file names the sources; this narrows them without editing
        # it. A source is only usable once something actually renders into it,
        # and the forge write path does not exist yet — a clue routed to a pull
        # request today is a clue that never gets said.
        self.allowed = [x.strip() for x in args.sources.split(",") if x.strip()]
        self.dropped: Counter = Counter()
        for task in self.tasks:
            for req in task["hidden_requirements"]:
                declared = req.get("fragmentation_sources") or list(self.allowed)
                kept = [x for x in declared if x in self.allowed]
                self.dropped.update(x for x in declared if x not in self.allowed)
                req["fragmentation_sources"] = kept or list(self.allowed)

        self.company = load(args.company, "run phase1_company_grounding.py first")
        self.timeline = load(args.timeline, "run phase2_timeline.py first")
        self.artifacts = load(args.artifacts, "run phase2_workstreams.py first")

        self.days = {d["date"]: d for d in self.timeline["days"]}
        self.channels = {c["name"]: c for c in self.company["channels"]}
        self.people = {p["synthetic"]["id"]: p for p in self.company["people"]}
        self.employees = [p["synthetic"]["id"] for p in self.company["people"]
                          if p["class"] == "employee"]
        self.services = {s["slug"]: s for s in self.company["services"]}

        # The forge is optional. Its write path does not exist yet, so a clue
        # planted in a pull request is a promise the render stage has to keep —
        # but the items themselves are real, resolved from the actual history,
        # and a design argument that happened in a review thread belongs there.
        self._reachable: dict[str, set[str]] | None = None
        self._principals: list[str] | None = None
        self.capacity: dict[str, dict[str, int]] = {}
        self.forge: list[dict] = []
        if args.forge_plan and Path(args.forge_plan).exists():
            plan = json.loads(Path(args.forge_plan).read_text(encoding="utf-8"))
            self.forge = plan.get("items") or []

        self.specs: dict[str, dict] = {}
        for path in sorted(Path(args.specs).glob("*.json")):
            self.specs[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        if not self.specs:
            rl.fail(f"no conversation specs in {args.specs} — run phase2_days.py first")

        self.strip_previous()

    def strip_previous(self) -> None:
        """Undo the last plant before making this one.

        This stage rewrites the corpus in place, so without the strip it reads
        its own output and adds to it: the same clue in four rooms, which
        destroys the one-clue-per-carrier rule the whole design rests on.
        Stripping makes a re-plant a real re-plant rather than a layer on top.
        """
        for day in self.specs.values():
            day["specs"] = [s for s in day["specs"] if not s.get("planted_arc")]
            for spec in day["specs"]:
                spec.pop("planted", None)
        self.artifacts["docs"] = [d for d in self.artifacts["docs"]
                                  if not d.get("planted_arc")]
        self.artifacts["threads"] = [t for t in self.artifacts["threads"]
                                     if not t.get("planted_arc")]
        for doc in self.artifacts["docs"]:
            doc.pop("planted", None)
        for thread in self.artifacts["threads"]:
            thread.pop("planted", None)
            for message in thread["messages"]:
                message.pop("planted", None)
        for comment in self.artifacts.get("comments", []):
            comment.pop("planted", None)

    # -- who could plausibly hold a clue about this feature -------------------
    def principals(self, share: float = 0.95, least_months: int = 3) -> list[str]:
        """The people who actually built this thing.

        A clue is a thing somebody knew because they were there for it, so the
        set of people who can hold one is not "everyone on the roster" — it is
        the handful who carried the work. Six of the twelve wrote 95% of the
        commits; below them sit a one-month contractor and four drive-by
        contributors with five to sixteen commits each, and a design constraint
        recalled by someone who touched the repository twice is not a clue, it
        is a coincidence.

        Taken by cumulative share rather than a fixed count so it follows the
        history instead of a number I picked, with a floor on active months so
        that a single busy fortnight does not qualify.
        """
        if self._principals is None:
            weighted = []
            for persona_id in self.employees:
                person = self.people[persona_id]
                commits = sum(r.get("commits", 0) for r in person["real"])
                months = max((r.get("active_months", 0) for r in person["real"]),
                             default=0)
                weighted.append((commits, months, persona_id))
            weighted.sort(reverse=True)
            total = sum(c for c, _, _ in weighted) or 1
            running, keep = 0, []
            for commits, months, persona_id in weighted:
                if running / total >= share:
                    break
                running += commits
                if months >= least_months:
                    keep.append(persona_id)
            self._principals = keep or [w[2] for w in weighted[:5]]
        return self._principals

    def reachable(self, room_for: int = 3) -> dict[str, set[str]]:
        """Which sources each person can actually be quoted in, with room to spare.

        Owning a service is not the same as having somewhere to say something
        about it. Handing the model a holder with no channel membership and no
        mail produces a leaf that is well written, correctly attributed, and
        impossible to place — a clue lost for a reason that had nothing to do
        with the clue.

        A count, not a flag, because one carrier is not a source. Two people on
        this team have authored exactly one pull request each; treating that as
        "can be quoted on the forge" invites three leaves into a single slot and
        loses two of them, which is the same failure wearing a different hat.
        """
        if self._reachable is None:
            found: dict[str, Counter] = defaultdict(Counter)
            for carrier in self.carriers():
                for persona in carrier["who"]:
                    found[persona][carrier["source"]] += 1
            self._reachable = {p: {src for src, n in counts.items() if n >= room_for}
                               for p, counts in found.items()}
            self.capacity = {p: dict(counts) for p, counts in found.items()}
        return self._reachable

    def roster_for(self, services: set[str],
                   sources: set[str] | None = None) -> list[dict]:
        reach = self.reachable()
        out = []
        for persona_id in self.principals():
            person = self.people[persona_id]
            owns = {s["slug"] for s in person["services_owned"]}
            if services and not owns & services:
                continue
            can = sorted(reach.get(persona_id, set()) & (sources or set(SOURCES)))
            if sources and not can:
                continue
            out.append({
                "id": persona_id,
                "title": person["synthetic"]["title"],
                "owns": sorted(owns),
                "channels": [c["name"] for c in self.company["channels"]
                             if persona_id in c["members"]],
                "can_be_quoted_in": can,
            })
        # Falling back to everyone who built the thing, never to everyone on the
        # roster: a feature touching a service none of the principals owns is
        # still their work to argue about.
        return out or [{
            "id": p, "title": self.people[p]["synthetic"]["title"],
            "owns": [s["slug"] for s in self.people[p]["services_owned"]],
            "channels": [c["name"] for c in self.company["channels"]
                         if p in c["members"]],
            "can_be_quoted_in": sorted(reach.get(p, set())),
        } for p in self.principals()]

    def services_named(self, text: str) -> set[str]:
        """Which of the world's services a task's prose is about."""
        words = tokens(text)
        hit = set()
        for slug, service in self.services.items():
            if tokens(f"{slug} {service['name']}") & words:
                hit.add(slug)
        return hit

    # -- everywhere a leaf could go ------------------------------------------
    def carriers(self) -> list[dict]:
        """Every plantable spot, with what it is already about.

        A carrier is one conversation, one document, one page comment, or one
        mail message. `about` is the text it already carries, which is what
        makes a remark land there naturally or stick out.
        """
        out: list[dict] = []
        for date, day in self.specs.items():
            for index, spec in enumerate(day["specs"]):
                if spec.get("purpose_class") not in DELIBERATION:
                    continue
                out.append({
                    "key": f"spec|{date}|{spec['channel']}|{index}",
                    "source": "slack", "date": date, "channel": spec["channel"],
                    "room": f"#{spec['channel']}", "index": index,
                    "who": [p["id"] for p in spec["participants"]],
                    "about": " ".join([spec.get("reason", "")]
                                      + (spec.get("agenda") or [])
                                      + [g.get("goal", "")
                                         for g in spec.get("goals", [])]),
                })
        for doc in self.artifacts["docs"]:
            out.append({
                "key": f"doc|{doc['id']}", "source": "notion",
                "date": doc["created_at"], "channel": None,
                "room": f"page:{doc['id']}", "index": None,
                "who": [doc["author"]],
                "about": f"{doc.get('title') or ''} {doc.get('purpose') or ''} "
                         f"{doc.get('hint') or ''}",
            })
        for comment in self.artifacts.get("comments", []):
            out.append({
                "key": f"comment|{comment['id']}", "source": "notion",
                "date": comment["created_at"], "channel": None,
                # A comment lives on its page: two remarks in the margin of one
                # document are one room, however far apart they were written.
                "room": f"page:{comment['doc']}", "index": None,
                "who": [comment["author"]],
                "about": comment.get("anchor") or "",
            })
        for item in self.forge:
            if item.get("kind") == "gap" or not item.get("author"):
                continue
            when = item.get("created")
            if not when:
                continue
            date = dt.datetime.fromtimestamp(int(when), dt.timezone.utc).date().isoformat()
            out.append({
                "key": f"forge|{item['number']}", "source": "github",
                "date": date, "channel": None,
                "room": f"#{item['number']}", "index": None,
                "who": [item["author"]],
                "about": f"{item.get('title') or ''} {(item.get('body') or '')[:400]}",
                "forge_kind": item.get("kind"),
            })
        for thread in self.artifacts["threads"]:
            for message in thread["messages"]:
                out.append({
                    "key": f"mail|{thread['id']}|{message['id']}", "source": "email",
                    "date": message["date"], "channel": None,
                    "room": f"thread:{thread['id']}", "index": None,
                    "who": [message["from"]],
                    "about": f"{thread.get('subject') or ''} "
                             f"{thread.get('purpose') or thread.get('hint') or ''}",
                })
        return out

    def present(self, persona: str, date: str) -> bool:
        day = self.days.get(date)
        if not day:
            return False
        return any(p["persona"] == persona and p["state"] == "present"
                   for p in day["people"])


# =============================================================================
# Schemas
# =============================================================================
def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props,
            "required": required if required is not None else list(props),
            "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": {"type": "string"}}


def tree_schema(people: list[str], facts: list[str], sources: list[str]) -> dict:
    return _obj({
        "subconclusions": {"type": "array", "items": _obj({
            "id": _STR,
            "text": {**_STR, "description": "one component of the requirement, "
                                            "stated as a claim"},
            "commonsense": {**_STR, "description": "the single inference a reader "
                                                   "supplies to reach this from its "
                                                   "leaves. Nobody ever says it."},
        })},
        "leaves": {"type": "array", "items": _obj({
            "id": _STR,
            "text": {**_STR, "description": "the oblique remark, in this person's "
                                            "voice, as they would drop it"},
            "settles": {**_STR, "description": "the same point as one short "
                                               "third-person clause: 'the team "
                                               "agrees X'"},
            "holder": {"type": "string", "enum": people or ["none"]},
            "source": {"type": "string", "enum": sources or ["slack"]},
            "subconclusion": _STR,
            "covers": {"type": "array",
                       "items": {"type": "string", "enum": facts or ["rule"]},
                       "description": "at most two; more and it reads as a "
                                      "specification rather than a remark"},
            "commonsense": {**_STR, "description": "what a reader must infer from "
                                                   "this remark alone"},
            "verbatim": {**_STRS, "description": "identifiers a reader must "
                                                 "reproduce exactly, and which this "
                                                 "text therefore contains literally"},
            "forbidden_terms": {**_STRS, "description": "language that would give "
                                                        "the requirement away"},
        })},
    })


def herring_schema(people: list[str]) -> dict:
    return _obj({"herrings": {"type": "array", "items": _obj({
        "id": _STR,
        "text": {**_STR, "description": "the remark, in this person's voice, as "
                                        "they would drop it at the time"},
        "settles": {**_STR, "description": "one short third-person clause"},
        "holder": {"type": "string", "enum": people or ["none"]},
        "forbidden_terms": {**_STRS, "description": "language that would reveal "
                                                    "this was later reversed"},
    })}})


def arc_schema(channels: list[str], people: list[str]) -> dict:
    return _obj({"beats": {"type": "array", "items": _obj({
        "beat": {**_STR, "description": "what this one conversation is for"},
        "channel": {"type": "string", "enum": channels or ["general"]},
        "participants": {"type": "array",
                         "items": {"type": "string", "enum": people or ["none"]}},
        "reason": {**_STR, "description": "why these people are talking today"},
        "agenda": {**_STRS, "description": "two or three items"},
        "expected_outcome": {**_STR, "description": "where it leaves things, usually "
                                                    "with something still open"},
        "subjects": {**_STRS, "description": "what gets named: files, services, "
                                             "identifiers"},
    })}})


def reconstruct_schema() -> dict:
    """Every constraint, not the most salient one.

    Asking for a single rule was the wrong question: a requirement with five
    parts does not fit in one sentence, so a reader states whichever part struck
    them hardest and drops the rest — and the grader then reports the dropped
    parts as unrecoverable when the remarks carried them perfectly well. The
    list is what makes the proof measure the corpus rather than the summary.
    """
    return _obj({
        "constraints": {"type": "array", "items": _obj({
            "text": {**_STR, "description": "one constraint, stated as a rule "
                                            "someone could implement"},
            "from_remarks": {**_STRS, "description": "which remarks give it"},
        })},
        "summary": {**_STR, "description": "the whole of it in a sentence or two"},
    })


def grade_schema(facts: list[str]) -> dict:
    return _obj({
        "recovered": {"type": "array",
                      "items": {"type": "string", "enum": facts or ["rule"]},
                      "description": "the parts of the true requirement the "
                                     "reconstruction actually contains"},
        "missed": {"type": "array",
                   "items": {"type": "string", "enum": facts or ["rule"]}},
        "notes": _STR,
    })


# =============================================================================
# Stages
# =============================================================================
BRIEF = """You are building a hidden-requirements benchmark inside a synthetic software company.

A task asks an agent to build a feature. Some requirements are stated openly. Others are
never written down anywhere, and the agent has to RECONSTRUCT them by combining scattered,
individually-innocuous remarks that real colleagues dropped in passing.

Rules you must hold to:

* Never state a hidden requirement outright. Not in any leaf, not in any subconclusion's
  text, not anywhere a reader could grep for it. A leaf that gives it away is a leaf that
  makes the task trivial.
* Every leaf is something a specific person would actually say, in a room they are in,
  about work they own. Refer to people by the persona ids you are given and nobody else.
* A leaf carries at most two parts of the requirement. More and it stops being a remark.
* `verbatim` names identifiers a reader must reproduce exactly — an environment variable, a
  method name. If you list one, the leaf's own text must contain it literally.
* Write plainly, in the register of a working engineer typing quickly. No literary flourish,
  no em dashes, no summarising what the team "realised".
* If the requirement says something MUST happen and the code today does the opposite, at
  least one leaf has to carry somebody treating today's behaviour as a problem — an
  annoyance, a workaround they reached for, a "that bit me again". Leaves that only
  describe how it currently works teach a reader that it is intended, and the requirement
  then reconstructs backwards: the reader concludes the present behaviour is the rule.
  Describing the behaviour is not enough. Someone has to mind.
"""


def stage_system(corpus: Corpus) -> str:
    return BRIEF + "\n\nTHE COMPANY\n" + json.dumps({
        "company": corpus.company["company"]["name"],
        "product": "curator, a Python library for bulk LLM inference and dataset curation",
        "services": [{"slug": s["slug"], "name": s["name"],
                      "description": s["description"][:220]}
                     for s in corpus.company["services"]],
        "channels": [{"name": c["name"], "kind": c["kind"], "purpose": c["purpose"][:160],
                      "members": c["members"]} for c in corpus.company["channels"]],
    }, ensure_ascii=False, separators=(",", ":"))


def facts_of(requirement: dict) -> list[str]:
    return [f for f in FACT_FIELDS if requirement.get(f)]


def stage_tree(llm: rl.LLM, system: str, corpus: Corpus, task: dict,
               req: dict, req_id: str) -> dict:
    facts = facts_of(req["requirement"])
    sources = req.get("fragmentation_sources") or ["slack"]
    services = corpus.services_named(f"{task['title']} {task['description']}")
    roster = corpus.roster_for(services, set(sources))
    prompt = (
        f"Hide this requirement.\n\nTHE FEATURE (stated openly, an agent will be told this)\n"
        f"{task['title']}: {task['description']}\n\n"
        "THE HIDDEN REQUIREMENT (never stated anywhere in the corpus)\n"
        + json.dumps(req["requirement"], ensure_ascii=False, indent=1) + "\n\n"
        "Break it into subconclusions — the components a reader has to establish — and then "
        "into leaves, the individual remarks that imply them. Each part listed above must be "
        "carried by at least one leaf, and the `covers` field says which.\n\n"
        f"Spread the leaves across these sources: {', '.join(sources)}. A source is where the "
        "remark was made: `slack` a channel, `notion` the wiki, `email` internal mail, "
        "`github` a pull request or issue. Use more than one; a requirement recoverable from "
        "one place is not hidden.\n\n"
        "Aim for two to four leaves per subconclusion, and give each to somebody who owns "
        "that ground. Each person below lists the sources they can be quoted in — a "
        "leaf whose holder cannot be quoted in its source has nowhere to go and is "
        "thrown away, so pair them.\n\n"
        "WHO COULD KNOW THIS\n"
        + json.dumps(roster, ensure_ascii=False, separators=(",", ":"))
    )
    out = llm.complete(system=system, prompt=prompt,
                       schema=tree_schema([r["id"] for r in roster], facts, sources),
                       label=f"tree:{req_id}", max_tokens=12000)
    return normalise_tree(out, req_id, facts, corpus)


def normalise_tree(out: dict, req_id: str, facts: list[str], corpus: Corpus) -> dict:
    """Namespace the ids and drop anything the closed world cannot support."""
    notes: list[str] = []
    subs = []
    for i, sub in enumerate(out.get("subconclusions") or []):
        subs.append({"id": (sub.get("id") or f"s{i + 1}").strip(),
                     "text": (sub.get("text") or "").strip(),
                     "commonsense": (sub.get("commonsense") or "").strip()})
    known = {s["id"] for s in subs}

    leaves = []
    for i, leaf in enumerate(out.get("leaves") or []):
        holder = (leaf.get("holder") or "").strip()
        if holder not in corpus.people:
            notes.append(f"dropped a leaf: {holder!r} is not a person here")
            continue
        covers = [c for c in (leaf.get("covers") or []) if c in facts][:2]
        text = (leaf.get("text") or "").strip()
        verbatim = [v for v in (leaf.get("verbatim") or []) if v and v in text]
        missing = [v for v in (leaf.get("verbatim") or []) if v not in text]
        if missing:
            notes.append(f"{req_id}.{leaf.get('id')}: claimed verbatim "
                         f"{', '.join(missing)} but the text does not contain it")
        leaves.append({
            "id": f"{req_id}.{(leaf.get('id') or f'l{i + 1}').strip()}",
            "text": text,
            "settles": (leaf.get("settles") or "").strip() or text,
            "holder": holder,
            "source": (leaf.get("source") or "slack").strip(),
            "subconclusion": (leaf.get("subconclusion") or "").strip(),
            "covers": covers,
            "commonsense": (leaf.get("commonsense") or "").strip(),
            "verbatim": verbatim,
            "forbidden_terms": [t for t in (leaf.get("forbidden_terms") or [])
                                if isinstance(t, str)],
            "requirement": req_id,
            "kind": "clue",
        })
        if leaves[-1]["subconclusion"] not in known:
            leaves[-1]["subconclusion"] = subs[0]["id"] if subs else ""
    return {"subconclusions": subs, "leaves": leaves, "notes": notes}


def giveaways(req: dict, leaves: list[dict]) -> list[str]:
    """Does any leaf just say it?

    The failure this catches is subtle and total: a leaf that reproduces the
    requirement's own phrasing looks like every other leaf in the tree and turns
    the task into a search. Checked against the requirement's wording rather
    than the model's opinion of whether it gave anything away.
    """
    problems = []
    for field in FACT_FIELDS:
        stated = req["requirement"].get(field)
        if not stated:
            continue
        want = tokens(stated)
        if len(want) < 4:
            continue
        for leaf in leaves:
            have = tokens(leaf["text"])
            if len(want & have) / len(want) > 0.75:
                problems.append(f"{leaf['id']} restates `{field}` almost verbatim")
    for leaf in leaves:
        low = leaf["text"].lower()
        for term in leaf["forbidden_terms"]:
            if term and term.lower() in low:
                problems.append(f"{leaf['id']} contains its own forbidden term "
                                f"{term!r}")
    return problems


def stage_herrings(llm: rl.LLM, system: str, corpus: Corpus, task: dict,
                   req: dict, req_id: str, tree: dict) -> list[dict]:
    """The decision this team made and later reversed."""
    reversed_version = req.get("earlier_reversed_version")
    if not reversed_version:
        return []
    services = corpus.services_named(f"{task['title']} {task['description']}")
    roster = corpus.roster_for(services, {"slack"})
    prompt = (
        "Write the decision this team made and later reversed.\n\n"
        f"THE FEATURE\n{task['title']}: {task['description']}\n\n"
        f"WHAT THEY ORIGINALLY DID\n{reversed_version}\n\n"
        "WHAT REPLACED IT LATER (do not reveal this, it is what the clues build to)\n"
        + json.dumps(req["requirement"], ensure_ascii=False, indent=1) + "\n\n"
        "It was genuinely settled at the time and genuinely wrong in the end, and the person "
        "saying it believes it. Never signal that it will be revisited. Write one or two "
        "herrings, each in one person's voice.\n\n"
        "WHO COULD HAVE DECIDED IT\n"
        + json.dumps(roster, ensure_ascii=False, separators=(",", ":"))
    )
    out = llm.complete(system=system, prompt=prompt,
                       schema=herring_schema([r["id"] for r in roster]),
                       label=f"herring:{req_id}", max_tokens=4000)
    herrings = []
    for i, item in enumerate(out.get("herrings") or []):
        holder = (item.get("holder") or "").strip()
        if holder not in corpus.people:
            continue
        text = (item.get("text") or "").strip()
        herrings.append({
            "id": f"{req_id}.h{i + 1}", "text": text,
            "settles": (item.get("settles") or "").strip() or text,
            "holder": holder, "source": "slack", "subconclusion": "",
            "covers": [], "commonsense": "", "verbatim": [],
            "forbidden_terms": [t for t in (item.get("forbidden_terms") or [])
                                if isinstance(t, str)],
            "requirement": req_id, "kind": "herring",
            # Every leaf of this requirement is a reversal of it, so the herring
            # must precede the earliest of them.
            "supersedes": [leaf["id"] for leaf in tree["leaves"]],
        })
    return herrings


def stage_arc(llm: rl.LLM, system: str, corpus: Corpus, task: dict, task_id: str,
              window: tuple[str, str]) -> list[dict]:
    """Build the haystack.

    The feature is not in the corpus at all, so there is nothing for a clue to
    sit inside. These are the ordinary design conversations this team would have
    had about it: the visible requirements argued about openly, the hidden ones
    never mentioned. They are also what makes an `explicit` placement possible —
    without them every clue is an aside in a room about something else, and a
    requirement that is only ever mentioned in passing reads as arbitrary.
    """
    services = corpus.services_named(f"{task['title']} {task['description']}")
    roster = [r for r in corpus.roster_for(services, {"slack"}) if r["channels"]]
    rooms = sorted({c for r in roster for c in r["channels"]})
    prompt = (
        "This team is designing a feature. Write the eight to twelve conversations "
        "they had about it, in order.\n\n"
        f"THE FEATURE\n{task['title']}: {task['description']}\n\n"
        "State the feature's requirements openly — this is the visible discussion, and "
        "an agent is meant to find it. But these people have NOT yet settled the "
        "details that were decided elsewhere, so leave the specifics of behaviour open: "
        "questions raised and not answered, a decision deferred, someone saying they "
        "will check. The conversations should read as a design taking shape, not a "
        "design being announced.\n\n"
        "Vary them: a kickoff, a couple of arguments about approach, a review of a "
        "draft, a check-in that goes nowhere, a scoping conversation with someone "
        "adjacent. Use the channels and people given.\n\n"
        "WHO WORKS ON THIS\n"
        + json.dumps(roster, ensure_ascii=False, separators=(",", ":"))
        + f"\n\nROOMS AVAILABLE\n{', '.join(rooms)}"
    )
    out = llm.complete(system=system, prompt=prompt,
                       schema=arc_schema(rooms, [r["id"] for r in roster]),
                       label=f"arc:{task_id}", max_tokens=10000)
    return out.get("beats") or []


def seat_arc(corpus: Corpus, task: dict, task_id: str, beats: list[dict],
             window: tuple[str, str]) -> list[str]:
    """Put each beat on a real day, spaced across the window.

    Seated onto days the calendar already has, so an arc conversation never
    invents a working day the rest of the world does not agree happened.
    """
    notes: list[str] = []
    days = sorted(d for d in corpus.specs if window[0] <= d <= window[1]
                  and corpus.days.get(d, {}).get("is_weekend") is False)
    if not days:
        return [f"{task_id}: no working day between {window[0]} and {window[1]}"]
    step = max(1, len(days) // max(1, len(beats)))
    seated = 0
    for i, beat in enumerate(beats):
        want = [p for p in (beat.get("participants") or []) if p in corpus.people]
        # The room the model picked first, then any other room these people
        # share. Which channel a design argument happened in matters less than
        # whether it happened at all, and a beat dropped for want of a room is a
        # hole in the haystack the clues were going to hide in.
        rooms = [beat.get("channel")] + [
            c["name"] for c in corpus.company["channels"]
            if c["name"] != beat.get("channel")
            and len(set(c["members"]) & set(want)) >= 2]
        for channel in [r for r in rooms if r in corpus.channels]:
            members = set(corpus.channels[channel]["members"])
            for offset in range(len(days)):
                date = days[(i * step + offset) % len(days)]
                here = [p for p in want
                        if p in members and corpus.present(p, date)]
                if len(here) >= 2:
                    break
            else:
                continue
            break
        else:
            notes.append(f"{task_id}: nowhere to seat {beat.get('beat')!r} — no two "
                         "of these people share a room on any day in the window")
            continue
        corpus.specs[date]["specs"].append({
            "date": date, "channel": channel,
            "channel_name": corpus.channels[channel]["display_name"],
            "purpose_class": "deliberation",
            "purpose": beat.get("beat", ""),
            "reason": beat.get("reason", ""),
            "expected_outcome": beat.get("expected_outcome", ""),
            "agenda": beat.get("agenda") or [],
            "subjects": beat.get("subjects") or [],
            "participants": [{"id": p, "label": corpus.people[p]["synthetic"]["display_name"],
                              "why": "works on this", "brings": "", "wants": ""}
                             for p in here],
            "goals": [], "meetings": [], "event_ids": [], "referenced_objects": [],
            "must_not_mention": [], "absent_owners": [], "stand_in": None,
            "norms": {}, "role": "deliberation", "max_turns": 14,
            "planted_arc": task_id,
        })
        seated += 1
    notes.append(f"{task_id}: {seated}/{len(beats)} design conversation(s) seated "
                 f"between {window[0]} and {window[1]}")
    notes += seat_arc_artifacts(corpus, task, task_id, beats, window)
    return notes


def seat_arc_artifacts(corpus: Corpus, task: dict, task_id: str, beats: list[dict],
                       window: tuple[str, str]) -> list[str]:
    """The page and the mail thread that go with a design of this size.

    Without them `notion` and `email` have nothing about the feature in them at
    all, so every clue in those sources is necessarily an aside — and a
    requirement whose written half only ever surfaces obliquely reads as though
    nobody ever wrote the design down. Derived from the arc rather than asked
    for separately: the model has already decided who is arguing about this.
    """
    who = Counter(p for beat in beats for p in (beat.get("participants") or []))
    if not who:
        return [f"{task_id}: no arc, so no design page"]
    author, *rest = [p for p, _ in who.most_common() if p in corpus.people]
    if not author:
        return [f"{task_id}: no arc, so no design page"]

    days = sorted(d for d in corpus.specs if window[0] <= d <= window[1])
    opened = next((d for d in days if corpus.present(author, d)), days[0])
    corpus.artifacts["docs"].append({
        "id": f"design-{task_id}-plant", "kind": "design",
        "collection": "design", "created_at": opened, "author": author,
        "workstream": None, "recurring": False,
        "title": task["title"],
        "purpose": f"the design for {task['title'].lower()}",
        "hint": task["description"][:400],
        "occasion": {"trigger": "planted-arc", "who": list(who), "evidence": []},
        "covers": {"who": list(who)},
        "planted_arc": task_id,
    })

    correspondents = [p for p in rest if p in corpus.people][:3]
    messages, previous = [], None
    for i, sender in enumerate([author] + correspondents):
        date = next((d for d in days[i * 2:] if corpus.present(sender, d)), None)
        if not date:
            continue
        message_id = f"mail-{task_id}-plant-m{i}"
        messages.append({"id": message_id, "date": date, "from": sender,
                         "to": [p for p in [author] + correspondents if p != sender],
                         "in_reply_to": previous})
        previous = message_id
    if messages:
        corpus.artifacts["threads"].append({
            "id": f"mail-{task_id}-plant", "subject": f"Re: {task['title']}",
            "purpose": f"working out {task['title'].lower()} over mail",
            "hint": task["description"][:300], "recurring": False,
            "occasion": {"trigger": "planted-arc", "who": list(who), "evidence": []},
            "covers": {"who": list(who)},
            "participants": [author] + correspondents,
            "messages": messages, "planted_arc": task_id,
        })
    return [f"{task_id}: a design page by {author} on {opened}, and a "
            f"{len(messages)}-message thread, so the wiki and the mail have "
            "something about this feature to be an aside from"]


# =============================================================================
# Placement
# =============================================================================
def score(leaf: dict, carrier: dict) -> int:
    return len(tokens(leaf["text"]) & tokens(carrier["about"]))


def candidates(corpus: Corpus, leaf: dict, carriers: list[dict], used: set[str],
               window: tuple[str, str] | None = None) -> list[dict]:
    """Everywhere this remark could plausibly have been made.

    Plausibility is arithmetic: the right source, the right person, present that
    day, in the room, and nothing planted there already. Which of them is *best*
    is a judgement, and that is what the model is asked for.
    """
    out = []
    for carrier in carriers:
        if carrier["key"] in used or carrier["source"] != leaf["source"]:
            continue
        if window and not (window[0] <= carrier["date"] <= window[1]):
            continue
        if leaf["holder"] not in carrier["who"]:
            continue
        if carrier["source"] != "github" and \
                not corpus.present(leaf["holder"], carrier["date"]):
            continue
        if carrier["channel"] and leaf["holder"] not in \
                corpus.channels[carrier["channel"]]["members"]:
            continue
        fit = score(leaf, carrier)
        out.append({**carrier, "score": fit,
                    # Both are wanted. A clue only ever dropped where the topic
                    # is already on the table is findable by searching for the
                    # topic; one only ever dropped in unrelated rooms reads as
                    # a non sequitur.
                    "class": "explicit" if fit >= 3 else "passing"})
    out.sort(key=lambda c: (-c["score"], c["date"]))
    return out


def dense_window(corpus: Corpus) -> tuple[str, str]:
    """The stretch of calendar where this team was actually talking.

    The corpus has a long thin tail — four conversations in December, seven in
    January — and an arc seated out there would be a design discussion nobody
    was around for.
    """
    counts = sorted((date, len(day["specs"])) for date, day in corpus.specs.items())
    total = sum(n for _, n in counts)
    running, start, end = 0, counts[0][0], counts[-1][0]
    for date, n in counts:
        running += n
        if running >= total * 0.03 and start == counts[0][0]:
            start = date
        # 88, not 97. The last tenth of the conversations are spread over a year
        # of near-silence, and a design seated out there is a design nobody was
        # around to have: the seating needs two people present in a room, and by
        # then there rarely are two.
        if running >= total * 0.88:
            end = date
            break
    return start, end


def arc_window(corpus: Corpus, args, index: int = 0,
               count: int = 1) -> tuple[str, str]:
    """Where one feature gets designed: late, but while the team is still here.

    Late on purpose. It reads as the thing specified just before everyone
    dispersed, which is why it was never built and why an agent is being asked
    to build it now.

    Staggered, also on purpose. Five features all designed in the same quarter
    would put fifty new design conversations into a stretch of calendar that
    holds ninety-six in total, and a team arguing about five unrelated designs
    at once is the one thing here that no amount of good wording rescues. So
    each task gets its own overlapping slot down the back half of the record,
    which is what a team working through a backlog actually looks like.
    """
    start, end = dense_window(corpus)
    if args.arc_from and args.arc_until:
        return args.arc_from, args.arc_until
    first = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    span = (last - first).days

    def at(fraction: float) -> str:
        return (first + dt.timedelta(days=int(span * min(max(fraction, 0.0), 1.0)))
                ).isoformat()

    back = 0.45                       # where the staggered slots start
    room = (1.0 - back) / max(count, 1)
    opens = back + index * room
    # Slightly wider than its own slot, so neighbouring designs overlap the way
    # real ones do rather than starting the day the last one ended.
    return (args.arc_from or at(opens),
            args.arc_until or (at(opens + room * 1.4) if index < count - 1 else end))


def week_of(date: str) -> str:
    day = dt.date.fromisoformat(date)
    return (day - dt.timedelta(days=day.weekday())).isoformat()


def spread_problems(placed: list[dict], declared: list[str]) -> list[str]:
    """Is this requirement genuinely scattered, or only nominally?"""
    if not placed:
        return ["nothing was placed"]
    problems = []
    sources = {p["slot"]["source"] for p in placed}
    weeks = {week_of(p["slot"]["date"]) for p in placed}
    rooms = {p["slot"]["room"] for p in placed}
    if len(declared) > 1 and len(sources) < min(MIN_SOURCES, len(declared)):
        problems.append(f"leaves span {len(sources)} source(s) but "
                        f"{len(declared)} were declared")
    if len(weeks) < MIN_WEEKS:
        problems.append(f"leaves span {len(weeks)} week(s); a reader covering "
                        f"{MIN_WEEKS} would have all of it")
    if len(rooms) < MIN_CHANNELS:
        problems.append(f"leaves span {len(rooms)} room(s)")
    # Sharing a room only matters if they also share a moment. One clue per
    # carrier is already guaranteed, so two leaves in #engineering four months
    # apart are two separate readings — and #engineering is where that work
    # lives, so requiring them to scatter would push clues into rooms the topic
    # has no business being in. What must not happen is a fortnight in one room
    # that hands over a whole subconclusion at once.
    by_sub = defaultdict(list)
    for item in placed:
        by_sub[item["subconclusion"]].append(item["slot"])
    for sub, slots in by_sub.items():
        together = defaultdict(list)
        for slot in slots:
            together[slot["room"]].append(dt.date.fromisoformat(slot["date"]))
        for room, dates in together.items():
            if len(dates) > 1 and (max(dates) - min(dates)).days < 14:
                crowded = [s for s in slots if s["room"] == room]
                # Only a fault if it could have gone elsewhere. Where the
                # calendar offered nothing else, this is the corpus being small,
                # not the placement being careless — worth saying, not worth
                # refusing to write over.
                cost = ("avoidable" if not any(s.get("forced") for s in crowded)
                        else "forced — nowhere else seats them")
                problems.append(f"{len(dates)} leaves of {sub} sit in {room} "
                                f"within {(max(dates) - min(dates)).days} days "
                                f"({cost})")
    return problems


def place(corpus: Corpus, leaves: list[dict], carriers: list[dict], used: set[str],
          mix: float, window: tuple[str, str]) -> list[str]:
    """Give each leaf a carrier, chasing spread rather than the best single fit.

    Taking each leaf's highest-scoring carrier looks right and is wrong: the
    scores cluster, so the picks cluster too, and a requirement whose leaves all
    landed in one channel in one fortnight is recoverable in one sitting. So
    ranking rewards a carrier for being somewhere this requirement has not been
    yet, which makes the spread rules something placement aims at rather than
    something it is audited against afterwards.
    """
    notes = []
    want_explicit = round(len(leaves) * mix)
    taken_explicit = 0
    weeks: set[str] = set()
    rooms: set[str] = set()
    by_sub: dict[str, set[str]] = defaultdict(set)
    when_sub: dict[tuple[str, str], list[dt.date]] = defaultdict(list)

    def crowds(leaf: dict, option: dict) -> bool:
        """Would this put two leaves of one subconclusion into one reading?

        Sharing a room is fine — #engineering is where that work lives, and two
        remarks there four months apart are two separate readings. Sharing a
        room *and* a fortnight is not: a mail thread, or a week of one channel,
        gets read in one go and half a subconclusion arrives together.
        """
        seen = when_sub.get((leaf["subconclusion"], option["room"]))
        if not seen:
            return False
        day = dt.date.fromisoformat(option["date"])
        return any(abs((day - other).days) < 14 for other in seen)

    for leaf in leaves:
        options = [o for o in candidates(corpus, leaf, carriers, used, window)
                   if not crowds(leaf, o)]
        forced = False
        if not options:
            options = [o for o in candidates(corpus, leaf, carriers, used)
                       if not crowds(leaf, o)]
        if not options:
            # Nowhere uncrowded exists for this person in this source. Taking
            # the crowded slot beats dropping the clue: a fact nothing carries
            # cannot be taught at all, where two remarks in one thread merely
            # make that subconclusion easier than intended.
            options = candidates(corpus, leaf, carriers, used)
            forced = True
        if not options:
            held = corpus.capacity.get(leaf["holder"], {}).get(leaf["source"], 0)
            why = (f"{leaf['holder']} has no {leaf['source']} of their own at all"
                   if not held else
                   f"{leaf['holder']} has {held} {leaf['source']} carrier(s) and "
                   "every one is already spoken for")
            notes.append(f"{leaf['id']}: nowhere to put it — {why}")
            leaf["slot"] = None
            continue

        prefer = "explicit" if taken_explicit < want_explicit else "passing"

        def rank(option):
            room = option["room"]
            gain = ((2 if week_of(option["date"]) not in weeks else 0)
                    + (2 if room not in rooms else 0)
                    + (2 if room not in by_sub[leaf["subconclusion"]] else 0))
            return (option["class"] == prefer, gain, option["score"])

        pick = max(options, key=rank)
        if pick["class"] == "explicit":
            taken_explicit += 1
        used.add(pick["key"])
        # The room, not the kind of room. Tracking these by source meant every
        # page counted as the same place as every other page, so the ranking's
        # spread gain was flat across all of notion and all of email.
        room = pick["room"]
        weeks.add(week_of(pick["date"]))
        rooms.add(room)
        by_sub[leaf["subconclusion"]].add(room)
        when_sub[(leaf["subconclusion"], room)].append(
            dt.date.fromisoformat(pick["date"]))
        leaf["slot"] = {"key": pick["key"], "source": pick["source"],
                        "date": pick["date"], "channel": pick["channel"],
                        "room": pick["room"], "index": pick["index"],
                        "class": pick["class"], "score": pick["score"],
                        "forced": forced}
    return notes


def place_herrings(corpus: Corpus, herrings: list[dict], leaves: list[dict],
                   carriers: list[dict], used: set[str],
                   window: tuple[str, str]) -> list[str]:
    """Strictly before the earliest clue that reverses it, and as late as it can be.

    The ordering is the whole mechanism. A superseded decision appearing after
    the one that replaced it is not a red herring, it is a contradiction. And a
    decision reversed a week later reads as a team changing its mind, where one
    reversed six months later reads as two unrelated worlds — so take the latest
    slot that still precedes the reversal.
    """
    notes = []
    dated = [leaf["slot"]["date"] for leaf in leaves if leaf.get("slot")]
    if not dated:
        return ["no clue was placed, so no herring has anything to precede"]
    cutoff = min(dated)
    for herring in herrings:
        options = [c for c in candidates(corpus, herring, carriers, used, window)
                   if c["date"] < cutoff]
        if not options:
            options = [c for c in candidates(corpus, herring, carriers, used)
                       if c["date"] < cutoff]
        if not options:
            # A named holder who was never in a room before the reversal is a
            # constraint on wording, not on the herring: hand it to whoever else
            # on this ground was there.
            for stand_in in sorted({leaf["holder"] for leaf in leaves}):
                alt = dict(herring, holder=stand_in)
                options = [c for c in candidates(corpus, alt, carriers, used)
                           if c["date"] < cutoff]
                if options:
                    herring["reassigned_from"] = herring["holder"]
                    herring["holder"] = stand_in
                    break
        if not options:
            notes.append(f"{herring['id']}: no room seats {herring['holder']} before "
                         f"{cutoff}, where the clues begin")
            herring["slot"] = None
            continue
        pick = max(options, key=lambda c: (c["date"], c["score"]))
        used.add(pick["key"])
        herring["slot"] = {"key": pick["key"], "source": pick["source"],
                           "date": pick["date"], "channel": pick["channel"],
                           "room": pick["room"], "index": pick["index"],
                           "class": pick["class"], "score": pick["score"],
                           "reversed_on": cutoff}
    return notes


# =============================================================================
# Prove it is solvable
# =============================================================================
def stage_solvability(llm: rl.LLM, system: str, task: dict, req: dict, req_id: str,
                      leaves: list[dict], herrings: list[dict],
                      rounds: int = 3) -> dict:
    """Hand the clues back with the answer removed, and see what comes out.

    A tree that looks decomposed is not the same as one an agent can invert, and
    there is no way to tell which you have by reading it. The reconstruction is
    given only what a reader would encounter; the grading is a separate call,
    because a grader that has already seen the answer will agree with itself.
    """
    facts = facts_of(req["requirement"])

    def attempt(items: list[dict], label: str, seed: int = 0) -> dict:
        shown = sorted([i for i in items if i.get("slot")],
                       key=lambda i: i["slot"]["date"])
        if not shown:
            return {"reconstruction": None, "recovered": [], "missed": facts,
                    "notes": "nothing was placed"}
        transcript = "\n".join(
            f"- {i['slot']['date']} · {i['holder']} · {i['slot']['room']}: "
            f"\"{i['text']}\"" for i in shown)
        # Each round reads the same remarks with a different question in front of
        # it. Identical prompts would be one cached answer three times, which
        # votes on nothing.
        angle = ["", "\n\nWork through them in date order and say what changed.",
                 "\n\nFor each remark, ask what it rules out."][seed % 3]
        guess = llm.complete(
            system="You infer engineering constraints from scattered remarks. You are "
                   "given no answer key. You output strict JSON and nothing else.",
            prompt=("An agent has been asked to build this feature:\n\n"
                    f"{task['title']}: {task['description']}\n\n"
                    "Reading the company's chat, wiki and mail in date order, these "
                    "remarks turned up. Nobody ever stated a rule outright.\n\n"
                    f"{transcript}\n\n"
                    "What do these jointly imply that the feature description does "
                    "not already say? List EVERY distinct constraint you can infer "
                    "— not just the most important one. Cover, separately, what the "
                    "rule is, what it applies to, what it excludes, what should "
                    "happen when things go wrong, and what has to be visible "
                    "afterwards. Some of those will not be inferable; list the ones "
                    "that are, and say which remarks give each." + angle),
            schema=reconstruct_schema(), label=f"solve:{req_id}:{label}:{seed}",
            max_tokens=8000)
        graded = llm.complete(
            system="You grade a reconstruction against the requirement it was meant to "
                   "recover. You output strict JSON and nothing else.",
            prompt=("THE TRUE REQUIREMENT\n"
                    + json.dumps(req["requirement"], ensure_ascii=False, indent=1)
                    + "\n\nWHAT WAS RECONSTRUCTED FROM THE CLUES ALONE\n"
                    + json.dumps(guess, ensure_ascii=False, indent=1)
                    + "\n\nWhich parts of the true requirement does the reconstruction "
                      "actually contain? Check every constraint in the list, not "
                      "only the summary. A part counts as recovered when the "
                      "reconstruction states the same thing, even in different "
                      "words or framed as a description of current behaviour rather "
                      "than as a rule; it does not count when the reconstruction "
                      "merely touches the same subject without committing to what "
                      "must happen."),
            schema=grade_schema(facts), label=f"grade:{req_id}:{label}:{seed}",
            max_tokens=2000)
        return {"reconstruction": guess.get("summary"),
                "constraints": [c.get("text") for c in guess.get("constraints") or []],
                "recovered": graded.get("recovered") or [],
                "missed": graded.get("missed") or [],
                "notes": graded.get("notes") or ""}

    def vote(items: list[dict], label: str, times: int = 0) -> dict:
        """Best of three, because one reading is not a measurement.

        The same tree passed this gate on one run and failed it on the next with
        the clues untouched — the reconstruction lists a dozen constraints and
        which ones it bothers to state varies. Taking a majority makes the
        verdict a property of the corpus rather than of one sampling; a part
        that comes back in two readings out of three is genuinely there, and one
        that never comes back is genuinely missing.
        """
        times = times or rounds
        tries = [attempt(items, label, seed) for seed in range(times)]
        tally: Counter = Counter()
        for one in tries:
            tally.update(set(one["recovered"]))
        need = times // 2 + 1
        recovered = sorted(f for f, n in tally.items() if n >= need)
        best = max(tries, key=lambda t: len(t["recovered"]))
        return {**best, "recovered": recovered,
                "missed": [f for f in facts if f not in recovered],
                "rounds": times,
                "votes": {f: tally.get(f, 0) for f in facts},
                "unsteady": sorted(f for f, n in tally.items() if 0 < n < times)}

    out = {"clues_only": vote(leaves, "clues")}
    if herrings:
        # One reading. This one is a difficulty dial that gets reported, not a
        # gate that stops the run, so it does not need to be voted on.
        out["with_herrings"] = vote(leaves + herrings, "herrings", times=1)
    return out


# =============================================================================
# Writing
# =============================================================================
def planted_entry(item: dict) -> dict:
    entry = {"clue": item["id"], "kind": item["kind"], "holder": item["holder"],
             "text": item["text"], "settles": item["settles"],
             "verbatim": item["verbatim"],
             "forbidden_terms": item["forbidden_terms"],
             "requirement": item["requirement"], "covers": item["covers"]}
    if item["kind"] == "herring":
        entry["reversed_on"] = item["slot"].get("reversed_on")
    return entry


def forge_payload(items: list[dict]) -> dict:
    """The comments a later stage has to post onto real issues and pull requests."""
    out = defaultdict(list)
    for item in items:
        slot = item.get("slot")
        if slot and slot["source"] == "github":
            out[slot["key"].split("|")[1]].append(planted_entry(item))
    return {"schema_version": SCHEMA_VERSION, "generated_at": rl.now_iso(),
            "generator": "data_gen/phase3_plant.py",
            "comments": [{"number": int(n), "planted": v} for n, v in sorted(out.items())]}


def write_into(corpus: Corpus, items: list[dict]) -> None:
    """Attach each placed clue to the thing that carries it."""
    docs = {d["id"]: d for d in corpus.artifacts["docs"]}
    comments = {c["id"]: c for c in corpus.artifacts.get("comments", [])}
    threads = {t["id"]: t for t in corpus.artifacts["threads"]}
    for item in items:
        slot = item.get("slot")
        if not slot:
            continue
        parts = slot["key"].split("|")
        if parts[0] == "spec":
            spec = corpus.specs[parts[1]]["specs"][slot["index"]]
            spec.setdefault("planted", []).append(planted_entry(item))
        elif parts[0] == "doc":
            docs[parts[1]].setdefault("planted", []).append(planted_entry(item))
        elif parts[0] == "comment":
            comments[parts[1]].setdefault("planted", []).append(planted_entry(item))
        elif parts[0] == "mail":
            thread = threads[parts[1]]
            for message in thread["messages"]:
                if message["id"] == parts[2]:
                    message.setdefault("planted", []).append(planted_entry(item))


def report(ledger: dict) -> str:
    """The tasks and where their clues are hidden, as a document to read.

    Written before a single message exists, which is the point: the expected
    answer is fixed in advance rather than reconstructed afterwards from
    whatever the corpus happened to say.
    """
    clues = [c for t in ledger["tasks"] for r in t["requirements"]
             for c in r["clues"]]
    reqs = [r for t in ledger["tasks"] for r in t["requirements"]]
    placed = [c for c in clues if c.get("carrier")]
    unsolved = [r for r in reqs
                if r.get("solvability", {}).get("clues_only", {}).get("missed")]

    L = ["# The tasks, and where their clues are hidden", "",
         f"{len(ledger['tasks'])} task(s) · {len(reqs)} hidden requirement(s) · "
         f"{len([c for c in clues if c['kind'] == 'clue'])} clue(s) · "
         f"{len([c for c in clues if c['kind'] == 'herring'])} reversed decision(s) · "
         f"{len(placed)}/{len(clues)} placed", ""]
    if unsolved:
        L += [f"**{len(unsolved)} requirement(s) are not recoverable from what was "
              "planted.** Those are marked below and the run failed.", ""]
    L += [
        "Each task states a feature openly. What it does not state is the "
        "requirement below it, which appears nowhere in the corpus as a rule — only "
        "as remarks people made in passing while working on something else. An "
        "agent has to put them back together.",
        "",
        "A **clue** carries part of the answer. A **reversal** is what this team "
        "decided first and later changed its mind about; it is planted strictly "
        "*before* the clue that overturns it, so reading in date order recovers the "
        "change and reading one conversation does not.",
        "",
        "Placement is marked **explicit** where the room was already arguing about "
        "this, **passing** where the remark is an aside in a conversation about "
        "something else. Both are wanted: only-explicit is findable by searching "
        "for the topic, only-passing reads as arbitrary.",
        "", "---", ""]

    for task in ledger["tasks"]:
        L += [f"## {task['task_id']} — {task['title']}", "",
              "**The agent is told:** " + task["description"], ""]
        if task.get("arc"):
            arc = task["arc"]
            L += [f"**Where it gets designed:** {arc.get('seated', 0)} conversation(s) "
                  f"between {arc.get('from', '?')} and {arc.get('until', '?')}, plus a "
                  "design page and a mail thread. None of them state the hidden "
                  "requirement.", ""]

        for req in task["requirements"]:
            types = ", ".join(req.get("types") or []) or "—"
            L += [f"### {req['req_id']} — the hidden requirement  ·  {types}", "",
                  "| part | what it actually requires |", "|---|---|"]
            for field in FACT_FIELDS:
                stated = req["requirement"].get(field)
                if stated:
                    carried = [c["clue_id"] for c in req["clues"]
                               if field in (c.get("covers") or [])]
                    mark = ", ".join(carried) if carried else "**nothing carries this**"
                    L.append(f"| `{field}` | {stated} <br>*carried by: {mark}* |")
            L.append("")

            if req.get("earlier_reversed_version"):
                L += ["**What they decided first, and later reversed:** "
                      + req["earlier_reversed_version"], ""]

            # -- the tree ---------------------------------------------------
            L += ["**The reasoning an agent has to do**", "", "```"]
            L.append("the requirement")
            for sub in req["subconclusions"]:
                L.append(f"  |")
                L.append(f"  +-- {sub['text']}")
                L.append(f"  |     reader must infer: {sub['commonsense']}")
                mine = [c for c in req["clues"]
                        if c["subconclusion"] == sub["id"] and c["kind"] == "clue"]
                for clue in mine:
                    where = clue.get("carrier") or {}
                    at = (f"{where.get('date')} {where.get('room')}"
                          if where else "UNPLACED")
                    L.append(f"  |     +-- [{clue['clue_id']}] {clue['holder']} · {at}")
                    L.append(f"  |     |     \"{clue['text']}\"")
            L += ["```", ""]

            # -- solvability ------------------------------------------------
            solve = req.get("solvability", {})
            only = solve.get("clues_only", {})
            missed = only.get("missed") or []
            L += ["**Is it recoverable from the clues alone?** "
                  + ("yes — every part came back"
                     if not missed and only.get("reconstruction")
                     else f"**no** — `{'`, `'.join(missed)}` survive nowhere"), ""]
            if only.get("reconstruction"):
                L += ["What a reader given only these remarks, and no answer key, "
                      "concluded:", "",
                      "> " + only["reconstruction"].replace("\n", " "), ""]
            with_h = solve.get("with_herrings")
            if with_h and with_h.get("reconstruction"):
                fooled = set(with_h.get("missed") or []) - set(missed)
                L += ["**Reading the reversed decision too:** "
                      + ("the reversal still comes through"
                         if not fooled else
                         f"the herring costs `{'`, `'.join(sorted(fooled))}` — it is "
                         "doing too much work, or lands too close to the clue"), "",
                      "> " + with_h["reconstruction"].replace("\n", " "), ""]

            # -- the clues, in encounter order -------------------------------
            rows = sorted(req["clues"],
                          key=lambda c: ((c.get("carrier") or {}).get("date") or "9999",
                                         c["clue_id"]))
            L += ["**Every planted line, in the order an agent reading forward "
                  "meets it**", "",
                  "| date | where | who | | covers | placement | what they say |",
                  "|---|---|---|---|---|---|---|"]
            for clue in rows:
                where = clue.get("carrier") or {}
                room = where.get("room") or clue["source"]
                kind = "↩︎ reversal" if clue["kind"] == "herring" else "clue"
                text = clue["text"].replace("|", "\\|").replace("\n", " ")
                L.append(f"| {where.get('date') or '**unplaced**'} | "
                         f"{room} | {clue['holder']} | {kind} | "
                         f"{', '.join(clue['covers']) or '—'} | "
                         f"{where.get('class', '—')} | {text} |")
            L.append("")

            if placed_here := [c for c in rows if c.get("carrier")]:
                weeks = {week_of(c["carrier"]["date"]) for c in placed_here}
                rooms = {c["carrier"]["room"] for c in placed_here}
                srcs = {c["source"] for c in placed_here}
                L += [f"**Spread:** {len(srcs)} source(s), {len(weeks)} distinct "
                      f"week(s), {len(rooms)} room(s), first {min(c['carrier']['date'] for c in placed_here)} "
                      f"last {max(c['carrier']['date'] for c in placed_here)}.", ""]
            L += ["---", ""]
    return "\n".join(L) + "\n"


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--company", type=Path, default=DEFAULT_COMPANY)
    parser.add_argument("--timeline", type=Path, default=DEFAULT_TIMELINE)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--specs", type=Path, default=DEFAULT_SPECS)
    parser.add_argument("--forge-plan", type=Path, default=DEFAULT_FORGE_PLAN,
                        help="the resolved issue and pull-request plan from "
                             "scripts/ingest_forge.py --plan-out. Without it, "
                             "`github` is not a place a clue can go.")
    parser.add_argument("--clues", type=Path, default=DEFAULT_CLUES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit", type=int, default=5,
                        help="how many tasks to plant (default: the first 5)")
    parser.add_argument("--arc-from", default=None,
                        help="start of the window the feature gets designed in "
                             "(default: late in the team-active stretch)")
    parser.add_argument("--arc-until", default=None)
    parser.add_argument("--clue-lead", type=int, default=120,
                        help="days before the arc that a clue may already have "
                             "been dropped; everything earlier is left clear so a "
                             "reversed decision has somewhere to sit")
    parser.add_argument("--sources", default="slack,notion,email",
                        help="which of the sources named in the tasks file to "
                             "actually use. github is left out until the forge "
                             "write path exists, since a clue routed to a pull "
                             "request nothing posts is a clue that never lands.")
    parser.add_argument("--mix", type=float, default=0.5,
                        help="share of clues to place where the topic is already "
                             "explicit; the rest land in passing")
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "llm")
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--backend", default="auto", choices=["auto", "cli", "sdk"])
    parser.add_argument("--auth", default="auto", choices=["auto", "oauth", "api-key"])
    parser.add_argument("--rounds", type=int, default=3,
                        help="how many independent readings vote on whether a "
                             "requirement is recoverable. One reading is not a "
                             "measurement: the same tree has both passed and "
                             "failed on a single sample.")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="decompose, place, prove and report; write no corpus")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    rl.heading("Reading")
    corpus = Corpus(args)
    carriers = corpus.carriers()
    by_source = Counter(c["source"] for c in carriers)
    reqs = sum(len(t["hidden_requirements"]) for t in corpus.tasks)
    rl.ok(f"{len(corpus.tasks)} task(s), {reqs} hidden requirement(s)")
    rl.ok(f"{len(carriers)} places a clue could go: "
          + ", ".join(f"{v} {k}" for k, v in by_source.most_common()))
    if corpus.dropped:
        rl.info("not using " + ", ".join(f"{k} ({v} requirement(s) asked for it)"
                                         for k, v in corpus.dropped.most_common())
                + " — those clues go to " + ", ".join(corpus.allowed) + " instead")
    who = corpus.principals()
    rl.ok(f"clues are held by the {len(who)} people who built this: "
          + ", ".join(who))
    arcs_at = {f"t{t}": arc_window(corpus, args, t - 1, len(corpus.tasks))
               for t in range(1, len(corpus.tasks) + 1)}
    # The lead-in is split rather than shared. A reversed decision has to precede
    # the clue that overturns it, and if clues may land anywhere in the run-up
    # then the earliest of them decides how much room the reversal has left —
    # which, for the first task, is often none. Reserving the opening quarter
    # for reversals makes the ordering something the calendar guarantees instead
    # of something each placement has to get lucky about.
    clues_at, herrings_at = {}, {}
    floor = min(corpus.specs)
    for tid, window in arcs_at.items():
        opens = max(floor, (dt.date.fromisoformat(window[0])
                            - dt.timedelta(days=args.clue_lead)).isoformat())
        split = (dt.date.fromisoformat(opens)
                 + dt.timedelta(days=max(14, args.clue_lead // 4))).isoformat()
        herrings_at[tid] = (opens, split)
        clues_at[tid] = (split, max(corpus.specs))
        rl.info(f"{tid} gets designed {window[0]} to {window[1]}; reversals sit "
                f"{opens} to {split}, clues from {split}")

    llm = rl.LLM(args.cache_dir, model=args.model or rl.MODEL, effort=args.effort,
                 refresh=not args.no_refresh, verbose=args.verbose,
                 auth=args.auth, backend=args.backend)
    system = stage_system(corpus)

    rl.heading(f"Decomposing ({llm.backend}, {llm.auth_mode})")
    jobs = []
    for t, task in enumerate(corpus.tasks, start=1):
        for r, req in enumerate(task["hidden_requirements"], start=1):
            jobs.append((f"t{t}.r{r}", task, req))
    trees: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(stage_tree, llm, system, corpus, task, req, rid): rid
                   for rid, task, req in jobs}
        for future in as_completed(futures):
            rid = futures[future]
            try:
                trees[rid] = future.result()
            except Exception as exc:            # noqa: BLE001
                rl.warn(f"{rid}: {exc}")
    rl.ok(f"{len(trees)} tree(s): "
          f"{sum(len(t['subconclusions']) for t in trees.values())} subconclusions, "
          f"{sum(len(t['leaves']) for t in trees.values())} leaves")

    failed = False
    for rid, task, req in jobs:
        tree = trees.get(rid)
        if not tree:
            failed = True
            continue
        facts = facts_of(req["requirement"])
        carried = {f for leaf in tree["leaves"] for f in leaf["covers"]}
        for gap in [f for f in facts if f not in carried]:
            rl.warn(f"{rid}: nothing carries `{gap}`")
            failed = True
        for note in tree["notes"]:
            rl.warn(f"{rid}: {note}")
        for problem in giveaways(req, tree["leaves"]):
            rl.warn(f"{rid}: {problem}")
            failed = True

    rl.heading("Building the haystack")
    # Written concurrently, seated one at a time: seating mutates the shared
    # calendar, and two tasks racing for the same day would each think it free.
    arcs: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(stage_arc, llm, system, corpus, task, f"t{t}",
                               arcs_at[f"t{t}"]): f"t{t}"
                   for t, task in enumerate(corpus.tasks, start=1)}
        for future in as_completed(futures):
            tid = futures[future]
            try:
                arcs[tid] = future.result()
            except Exception as exc:            # noqa: BLE001
                rl.warn(f"{tid}: {exc}")
    for t, task in enumerate(corpus.tasks, start=1):
        for note in seat_arc(corpus, task, f"t{t}", arcs.get(f"t{t}", []),
                             arcs_at[f"t{t}"]):
            (rl.ok if "seated" in note or "design page" in note else rl.warn)(note)
    carriers = corpus.carriers()          # the arc is somewhere a clue can go
    rl.ok(f"{len(carriers)} carriers now the feature is being discussed")

    rl.heading("Red herrings")
    herrings: dict[str, list[dict]] = {}
    reversals = [(rid, task, req) for rid, task, req in jobs
                 if rid in trees and req.get("earlier_reversed_version")]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(stage_herrings, llm, system, corpus, task, req, rid,
                               trees[rid]): rid for rid, task, req in reversals}
        for future in as_completed(futures):
            rid = futures[future]
            try:
                herrings[rid] = future.result()
            except Exception as exc:            # noqa: BLE001
                rl.warn(f"{rid}: {exc}")
    rl.ok(f"{sum(len(h) for h in herrings.values())} reversed decision(s) written")

    rl.heading("Placing")
    used: set[str] = set()
    for rid, task, req in jobs:
        if rid not in trees:
            continue
        for note in place(corpus, trees[rid]["leaves"], carriers, used, args.mix,
                          clues_at[rid.split(".")[0]]):
            rl.warn(note)
        for note in place_herrings(corpus, herrings.get(rid, []),
                                   trees[rid]["leaves"], carriers, used,
                                   herrings_at[rid.split(".")[0]]):
            rl.warn(note)
        placed = [x for x in trees[rid]["leaves"] if x.get("slot")]
        problems = spread_problems(placed, req.get("fragmentation_sources") or [])
        for problem in problems:
            if "forced" in problem:
                rl.info(f"{rid}: {problem}")
            else:
                rl.warn(f"{rid}: {problem}")
                failed = True
        classes = Counter(x["slot"]["class"] for x in placed)
        rl.ok(f"{rid}: {len(placed)}/{len(trees[rid]['leaves'])} clues placed "
              f"({classes['explicit']} explicit, {classes['passing']} in passing), "
              f"{len([h for h in herrings.get(rid, []) if h.get('slot')])} herring(s)")

    rl.heading("Proving it is solvable")
    solvability: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(stage_solvability, llm, system, task, req, rid,
                               trees[rid]["leaves"], herrings.get(rid, []),
                               args.rounds): rid
                   for rid, task, req in jobs if rid in trees}
        for future in as_completed(futures):
            rid = futures[future]
            try:
                solvability[rid] = future.result()
            except Exception as exc:            # noqa: BLE001
                rl.warn(f"{rid}: {exc}")
    for rid, result in sorted(solvability.items()):
        found = result["clues_only"]
        missed, shaky = found["missed"], found.get("unsteady") or []
        if missed:
            rl.warn(f"{rid}: not recoverable — {', '.join(missed)} did not come back "
                    f"in a majority of {found.get('rounds', 1)} readings "
                    + str(found.get("votes")))
            failed = True
        elif shaky:
            rl.info(f"{rid}: recoverable, but {', '.join(shaky)} came back in only "
                    f"some readings — thinly carried")
        else:
            rl.ok(f"{rid}: recoverable from the clues alone, every reading")

    ledger = {"schema_version": SCHEMA_VERSION, "generated_at": rl.now_iso(),
              "generator": "data_gen/phase3_plant.py", "tasks": []}
    for t, task in enumerate(corpus.tasks, start=1):
        tid = f"t{t}"
        entry = {"task_id": tid, "title": task["title"],
                 "description": task["description"],
                 "arc": {"from": arcs_at[tid][0], "until": arcs_at[tid][1],
                         "seated": sum(1 for day in corpus.specs.values()
                                       for spec in day["specs"]
                                       if spec.get("planted_arc") == tid)},
                 "requirements": []}
        for r, req in enumerate(task["hidden_requirements"], start=1):
            rid = f"t{t}.r{r}"
            tree = trees.get(rid, {"subconclusions": [], "leaves": []})
            rows = []
            for item in tree["leaves"] + herrings.get(rid, []):
                rows.append({
                    "clue_id": item["id"], "kind": item["kind"],
                    "covers": item["covers"], "subconclusion": item["subconclusion"],
                    "holder": item["holder"], "text": item["text"],
                    "settles": item["settles"], "verbatim": item["verbatim"],
                    "forbidden_terms": item["forbidden_terms"],
                    "source": item["source"], "carrier": item.get("slot"),
                    # The hooks a later stage writes back to. A clue still
                    # `planted` once the render stage has run is a clue that
                    # never got said.
                    "status": "planted", "rendered_in": None, "verified": False,
                })
            entry["requirements"].append({
                "req_id": rid, "types": req.get("hidden_requirement_types") or [],
                "requirement": req["requirement"],
                "fragmentation_sources": req.get("fragmentation_sources") or [],
                "earlier_reversed_version": req.get("earlier_reversed_version"),
                "subconclusions": tree["subconclusions"],
                "solvability": solvability.get(rid, {}),
                "clues": rows,
            })
        ledger["tasks"].append(entry)

    rl.heading("Writing")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report(ledger), encoding="utf-8")
    rl.ok(f"{args.report}")
    size = rl.write_json(args.clues, ledger)
    total = sum(len(r["clues"]) for t in ledger["tasks"] for r in t["requirements"])
    rl.ok(f"{args.clues} ({rl.human_bytes(size)}) — {total} clue(s) to track")

    if args.dry_run:
        rl.warn("--dry-run: the corpus was not touched")
    else:
        every = [x for rid in trees for x in
                 trees[rid]["leaves"] + herrings.get(rid, [])]
        write_into(corpus, every)
        for date, day in corpus.specs.items():
            rl.write_json(Path(args.specs) / f"{date}.json", day)
        rl.write_json(args.artifacts, corpus.artifacts)
        payload = forge_payload(every)
        if payload["comments"]:
            rl.write_json(DEFAULT_FORGE, payload)
            rl.ok(f"{DEFAULT_FORGE} — {len(payload['comments'])} forge item(s) "
                  "carry a clue")
        rl.ok(f"planted into {len(corpus.specs)} day file(s) and {args.artifacts}")

    rl.info(f"{llm.stats['calls']} calls, {llm.stats['cache_hits']} from cache "
            f"({llm.backend}/{llm.auth_mode})")
    if failed:
        rl.fail("the plant is incomplete. A part of a requirement that nothing "
                "carries, or that cannot be recovered from what was planted, is a "
                "task the corpus cannot teach and nobody could score.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
