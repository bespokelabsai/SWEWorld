#!/usr/bin/env python3
"""Phase 4 — the plan finally gets written down as messages.

Phases 1-3 settled everything about this world except the words: who works
here, what they own, what happened on each of 185 days, one conversation spec
per channel per day saying who talks and what they are trying to settle, and
115 clues planted into those specs so that five tasks have requirements nobody
ever states outright. This runs the specs through the `bespoke_user` engine and
produces the actual Slack, the actual documents and the actual mail.

**This file owns every piece of domain knowledge in the simulation.** The
engine knows nothing about services, workstreams or clues, and `worldapps.py`
knows nothing about either — it only knows how to write a page. The whole job
here is translating

    a conversation spec + that day's project state
        -> SharedGround + MemberGrounding + a channel

into the engine's own vocabulary, which is generic and already carries all of
it: what is true today is `ground_truth`, what does not exist yet is
`ground_truth.forbidden`, what somebody must say is an `agenda` item, and what
the director knows is opaque free text.

Two things have to survive the trip, and they are why this is a simulation
rather than a generation. Every planted clue must actually be said — a clue
nobody carries is a requirement the corpus cannot teach, so the task is
unscoreable — and every planned document must actually exist, checked by asking
the store what it holds rather than by believing a persona who said they wrote
it.

    phase4_simulate.py --dry-run      # the review document; spends nothing
    phase4_simulate.py --days 2025-02-04 --channels engineering
    phase4_simulate.py                # the derived sample
    phase4_simulate.py --install      # copy the result into data/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

BUILD = rl.DEFAULT_BUILD_DIR
OUT = BUILD / "phase4"
DEFAULT_SPECS = BUILD / "days" / "specs"

# How many consecutive working days when nobody says. WHICH days is derived,
# never fixed: the right ones are a property of the corpus.
DEFAULT_DAY_COUNT = 3

# Where a day opens, and how this workspace writes a reference. Stated once as
# a team convention because a house style IS a settled decision, and it lands
# in ground_truth.decisions where everyone in the channel sees it.
DAY_OPEN_HOUR = 9
HOW_WE_REFERENCE = (
    "House style for pointing at work in chat: a pull request or issue goes by "
    "its number with the word in front (issue 163, PR 528), never a bare "
    "#number — in Mattermost that opens a channel autocomplete. A wiki page "
    "goes by its title. Say it in full the first time, short form after. "
    # Both halves of this used to be a rule with no way to obey it, which is
    # the same hole `read_repo` closed for code. A persona was handed a page's
    # title and its owner and nothing that said whether it had been written, so
    # 96 remarks in the shipped corpus announced a page as up before its own
    # `created_at`; and a day capped at "no PR above 3" produced a morning
    # reviewing PR 173 and PR 242, opened the following month. So the rule now
    # comes with the answer: the tools are what settle it.
    "Do not say a page is on the wiki unless it is marked as written above or "
    "you wrote it yourself in this conversation — list_pages is what settles "
    "that, not what you remember planning. Same for a number: name a PR or an "
    "issue only if it is on the table above or find_issue just showed it to "
    "you. A plausible-looking number is how a review ends up discussing work "
    "that does not exist yet."
)

# The roster is structural — "Core Engineer, Request Processing" is a role, not
# somebody who can plausibly type. Occupation is mapped from the persona's own
# function through two CLOSED vocabularies, never parsed out of a job title,
# which is what keeps this working on a company that names its roles otherwise.
OCCUPATION = {
    "engineering": "software_developer",
    "ml": "computer_or_information_research_scientist",
    "data": "computer_or_information_research_scientist",
    "ops": "software_developer",
    "product": "computer_or_information_systems_manager",
    "leadership": "computer_or_information_systems_manager",
}
LEADS = {"founding", "principal", "staff", "lead", "manager", "director", "head"}

# A day's conversation either lands or stays open. The plan's own prose is the
# best evidence there is, and it is read in BOTH directions with open winning:
# "X is agreed but Y stays open" is the textbook partial, while "three
# decisions are on the record" is a thread that closes and must not be told to
# leave a loose end.
OPEN_MARKERS = ("still open", "left open", "stays open", "remains open",
                "unresolved", "not settled", "undecided", "deferred", "pending",
                "no decision", "not yet", "outstanding", "tomorrow", "next week")
OPEN_QUESTION = re.compile(r"\bopen\s+(?:\w+\s+){0,2}questions?\b")
LANDS_MARKERS = ("is complete", "are complete", "confirmed", "agreed", "decided",
                 "on the record", "signed off", "is settled", "shared picture",
                 "ready to merge", "cleared", "recorded decision")
LANDS_BY_CLASS = {"status": "resolves", "announcement": "resolves",
                  "coordination": "resolves", "troubleshooting": "partial",
                  "deliberation": "partial", "social": ""}


# =============================================================================
# Auth — resolved before anything touches the engine
# =============================================================================
def resolve_auth(mode: str) -> None:
    """Persona agents on the subscription, one-shots on the API key.

    The persona turns are almost all the tokens and belong on OAuth. The
    director is a one-line question asked once per turn, and routing it through
    the Agent SDK cold-starts a CLI session every time — which is how an
    18-turn conversation becomes half an hour.

    `bespoke_user` already does exactly this, but it decides once, at the
    moment the package is first touched, and its `__init__` is lazy — so this
    has to run before any import that reaches it, and nothing afterwards may
    re-read ANTHROPIC_API_KEY, because by then it has been popped out of the
    environment on purpose.
    """
    for key in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"):
        if not os.environ.get(key):
            found = rl.env_value(key)
            if found:
                os.environ[key] = found

    if mode == "split":
        # The one setting that would quietly undo the split by putting the
        # director back on a per-call CLI cold start.
        os.environ.pop("BESPOKE_ONESHOTS_OAUTH", None)
        os.environ.pop("BESPOKE_FORCE_API_KEY", None)
    elif mode == "oauth":
        os.environ["BESPOKE_ONESHOTS_OAUTH"] = "1"
        os.environ.pop("BESPOKE_FORCE_API_KEY", None)
    elif mode == "api-key":
        os.environ["BESPOKE_FORCE_API_KEY"] = "1"
        os.environ.pop("BESPOKE_ONESHOTS_OAUTH", None)


def check_auth(mode: str) -> str:
    """Say which half went which way, and refuse if it is not what was asked.

    Both failures are silent and expensive in opposite directions, so this is
    an assertion rather than a log line.
    """
    import bespoke_user as bu
    agents = "oauth" if bu._USE_OAUTH else "api key"
    director = "oauth" if bu._ONESHOTS_OAUTH else "api key"
    if mode == "split" and (agents, director) != ("oauth", "api key"):
        rl.fail(f"asked for the split but resolved agents={agents}, "
                f"director={director}. The persona turns must be on "
                "CLAUDE_CODE_OAUTH_TOKEN and the director on ANTHROPIC_API_KEY; "
                "both must be set, and BESPOKE_ONESHOTS_OAUTH must not be.")
    if not bu._USE_OAUTH and mode != "api-key":
        rl.fail("no CLAUDE_CODE_OAUTH_TOKEN, so every persona turn would go on "
                "the API key. Set it, or pass --auth api-key deliberately.")
    return f"agents={agents}, director={director}"


# =============================================================================
# Inputs
# =============================================================================
def load(path: Path, what: str) -> dict:
    if not path.exists():
        rl.fail(f"{path} does not exist — {what}")
    return json.loads(path.read_text(encoding="utf-8"))


class World:
    """Everything phases 1-3 decided, indexed for the two questions this stage
    asks of it: what is true on a given day, and who owes what."""

    def __init__(self, args):
        self.company = load(BUILD / "company_grounding.json",
                            "run phase1_company_grounding.py first")
        self.timeline = load(BUILD / "timeline.json", "run phase2_timeline.py first")
        self.artifacts = load(BUILD / "artifacts.json",
                              "run phase2_workstreams.py first")
        clues = BUILD / "clues.json"
        self.clues = load(clues, "run phase3_plant.py first") if clues.exists() else \
            {"tasks": []}
        forge = BUILD / "forge_plan.json"
        self.forge = (load(forge, "")["items"] if forge.exists() else [])

        self.specs_dir = Path(args.specs)
        self.days = {d["date"]: d for d in self.timeline["days"]}
        self.people = {p["synthetic"]["id"]: p for p in self.company["people"]}
        self.channels = {c["name"]: c for c in self.company["channels"]}
        self.services = {s["slug"]: s for s in self.company["services"]}
        self.docs = {d["id"]: d for d in self.artifacts["docs"]}
        # The LIVE wiki, attached by phase4_run once the stores exist. `docs`
        # above is the plan; this is what is on disk right now, and the two
        # answer different questions. None in a dry run, where nothing writes.
        self.wiki = None
        self.threads = {t["id"]: t for t in self.artifacts["threads"]}
        # Page comments are the fourth thing phase 2 plans and the only one
        # phase 4 never read. Three clues were planted in them and had nowhere
        # to be written, which no gate could see because nothing enumerated
        # them in the first place.
        self.comments = {c["id"]: c for c in self.artifacts.get("comments") or []}
        self.display: dict[str, str] = {}

        # Every clue, by id, so the per-clue report can say which task it
        # belongs to and what it was supposed to settle.
        self.clue_of: dict[str, dict] = {}
        for task in self.clues.get("tasks") or []:
            for req in task["requirements"]:
                # A clue names its subconclusion by id; the text of it lives on
                # the requirement. Resolved here because the clue gate judges
                # against what a reader is meant to be able to CONCLUDE, and an
                # id tells a judge nothing.
                behind = {s["id"]: s.get("text", "")
                          for s in req.get("subconclusions") or []}
                for clue in req["clues"]:
                    self.clue_of[clue["clue_id"]] = {
                        **clue, "task": task["title"], "task_id": task["task_id"],
                        "task_description": task.get("description", ""),
                        "req": req["req_id"],
                        "subconclusion_text": behind.get(clue.get("subconclusion"), ""),
                        "requirement": req.get("requirement") or {}}

    def spec_days(self) -> list[str]:
        return sorted(p.stem for p in self.specs_dir.glob("*.json"))

    def day(self, date: str) -> dict:
        path = self.specs_dir / f"{date}.json"
        if not path.exists():
            rl.fail(f"{date} has no conversation specs at {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def label(self, persona: str) -> str:
        if not persona:
            return "someone"
        return self.display.get(persona) or \
            (self.people.get(persona) or {}).get("synthetic", {}).get(
                "display_name", persona)

    def humanize(self, text: str) -> str:
        """Swap plan ids for the names the cast uses.

        A goal reads "Identify what's holding up gideon's three stale PRs", and
        that string is handed to a persona. Without this somebody types
        "@gideon" as a literal id into a conversation where he is called Gideon
        Halloway, which is the plan leaking into the world. Longest id first,
        so a short id that prefixes another is not half-replaced.
        """
        if not text:
            return text
        text = re.sub(r"(?<![\w/])#(\d{2,5})\b", r"PR \1", text)
        for persona in sorted(self.people, key=len, reverse=True):
            if persona in text:
                text = text.replace(persona, self.label(persona))
        return text

    def title_of(self, kind: str, ident: str) -> str:
        if kind == "doc":
            return (self.docs.get(ident) or {}).get("title") or ident
        if kind == "comment":
            # A comment has no title of its own; it is named by the page it
            # hangs on, which is also the only name a persona could recognise.
            com = self.comments.get(ident) or {}
            return ("comment on " + self.title_of("doc", com.get("doc", ""))
                    if com else ident)
        return (self.threads.get(ident) or {}).get("subject") or ident

    def comments_due(self, date: str) -> list[dict]:
        """Page comments the plan dates to this day.

        Kept off the day specs on purpose. `goals[].writes[]` lives in the spec
        files, and phase 3's plant lives in the same files — regenerating them
        to add comments would destroy it. The plan already says who comments on
        what and when, so the obligation is derived rather than stored.
        """
        return [c for c in self.comments.values()
                if str(c.get("created_at", ""))[:10] == date]


# =============================================================================
# The cast
# =============================================================================
def occupation_for(person: dict) -> str:
    title = (person["synthetic"].get("title") or "").lower()
    if any(word in title for word in LEADS):
        return OCCUPATION["leadership"]
    owns = " ".join(s["slug"] for s in person.get("services_owned") or [])
    if "viewer" in owns or "docs" in title:
        return OCCUPATION["product"]
    return OCCUPATION["engineering"]


def people_specs(world: World, wanted: set[str]) -> list[dict]:
    """One person spec per persona the run will actually use.

    The persona id stays the phase-1 id the whole way through, so every message
    traces back to the plan; only the display name becomes a human one.
    """
    out = []
    for persona in sorted(wanted):
        person = world.people.get(persona)
        if not person:
            continue
        # Owned services, most-owned first and capped. The raw list runs to
        # thirteen for the people who built most of this, and a role line that
        # names thirteen services tells a persona nothing about what they care
        # about today.
        owned = sorted(person.get("services_owned") or [],
                       key=lambda s: -(s.get("share_of_service") or 0))
        owns = ", ".join(s["slug"] for s in owned[:4])
        out.append({
            "id": persona,
            "occupation": occupation_for(person),
            # The world already named this person. identities.yaml, their Gitea
            # account, their mailbox and 1,734 commit signatures all say so, and
            # the engine will otherwise draw a stranger from its own pool and
            # put that stranger's name on their messages. `name` is an explicit
            # override and wins over the drawn persona, which keeps the voice
            # while keeping the identity.
            "name": person["synthetic"]["display_name"],
            "title": person["synthetic"]["title"],
            "persona": person["synthetic"]["title"],
            "personality": f"{person['synthetic']['title']}; owns "
                           f"{owns or 'no service of their own'}",
        })
    return out


# =============================================================================
# What is true today
# =============================================================================
def needed_names(spec: dict) -> list[str]:
    """Identifiers this conversation's planted clues require somebody to name.

    Every one of these is a name the symbol rule below would otherwise tell the
    persona not to say, which is not a hypothetical: a clue needing `Poet` was
    held by somebody who does not own that code, so he was instructed to say it
    and not to name it in the same prompt. He obeyed the guard, the clue lost
    its identifier, and the channel-day was re-run three times into the same
    contradiction. 63 of the corpus's 122 clues carry an identifier, so this is
    the common case rather than the odd one.
    """
    return sorted({v for planted in spec.get("planted") or []
                   for v in (planted.get("verbatim") or []) if v})


def forbidden(day: dict, spec: dict | None = None) -> list[str]:
    """What does not exist yet on this date.

    This is where the anti-hallucination spine phases 2 and 3 built reaches an
    actual conversation instead of stopping at the plan.

    Services are named, because phase 2 recorded their names. Files and symbols
    are NOT: it recorded how many of each do not exist yet (380 symbols and 47
    files on a typical day) but not which, so the guard for those is stated as
    a rule instead of enumerated. A rule a persona can follow beats a list that
    is not there — and inventing the names to fill the gap would be worse than
    both, since a wrong forbidden name forbids something real.

    The exception is carved in the same breath as the rule. A rule and its
    exception stated apart are a rule the model follows and an exception it
    forgets, and the names in question are ones the day's own clues depend on.
    """
    unborn = sorted(day["forbidden"].get("services_not_started") or [])
    counts = day["forbidden"]
    if counts.get("symbols_not_yet") or counts.get("files_not_yet"):
        allowed = needed_names(spec or {})
        exception = (f" These DO exist today and are yours to name: "
                     f"{', '.join(allowed)}." if allowed else "")
        unborn.append(
            f"— and {counts.get('symbols_not_yet', 0)} function/class names and "
            f"{counts.get('files_not_yet', 0)} files that this codebase only "
            "grows LATER. Do not name a function, class or file unless it has "
            "already come up in this conversation or you own the code it is in."
            + exception
            # The rule used to end here, and it was a rule with no way to obey
            # it: a persona asked not to name a symbol that does not exist yet
            # had no means of finding out which those were. `read_repo` shows
            # the tree as of today, so the rule now comes with the answer.
            + " If you are about to quote or describe code, open it first with "
              "read_repo — the tree on this date is the only thing that "
              "settles what exists, and what you remember may not be there "
              "yet.")
    return unborn


def shared_ground(world: World, day: dict, spec: dict) -> dict:
    """The one picture of the project everyone in this channel holds today."""
    state = day.get("project_state") or {}
    company = world.company["company"]
    started = [s for s in world.services
               if s not in (day["forbidden"].get("services_not_started") or [])]

    components = [{"name": slug,
                   "owner": world.label((world.services[slug].get("owners") or [""])[0]),
                   "status": "in flight"} for slug in sorted(started)[:10]]

    # This conversation's own objects go FIRST and by name: they are what these
    # people are here to talk about. Then the wider set of what is open, so
    # somebody can refer to a review that is waiting on them without inventing
    # its number.
    on_the_table = []
    for o in (spec.get("referenced_objects") or [])[:6]:
        what = world.humanize(o.get("title") or o["id"])
        if o["kind"] == "doc":
            # DOES THIS PAGE EXIST YET. The spec has always known — phase 2
            # writes `written` when the day's packet found it among
            # `already_written` and `planned` when today's goal is to write it
            # — and this function used to drop it on the floor, handing the
            # persona a title, an owner, and nothing that said whether anybody
            # had written the thing. Both halves of the corpus's wiki problem
            # came out of that silence. Every spec from 2024-12-10 to 12-18 said
            # `written` for the bulk-llm-inference design, and every one of
            # those days produced somebody saying it was not on the wiki; the
            # same gap the other way round announced pages days early.
            #
            # `world.wiki` is the live store and is the better answer wherever
            # it is set, because the plan says what SHOULD have been written by
            # now and the store says what was. It is None while `simulate`
            # builds every channel up front — deliberately, so `context.md`
            # shows exactly what will run and a dry run costs nothing — so the
            # spec's own status is the working answer today.
            live = world.wiki.written(o["id"]) if world.wiki else ""
            if live:
                what += f" — on the wiki since {live[:10]}"
            elif o.get("status") == "written":
                what += " — already on the wiki, go and read it"
            else:
                what += " — NOT on the wiki yet, still to be written"
        on_the_table.append({"what": what, "who": world.label(_holder(world, o))})
    on_the_table += [{"what": f"PR {pr['number']}: {pr['title']}",
                      "who": world.label(pr.get("persona", ""))}
                     for pr in (state.get("open_prs") or [])[:6]]

    return {
        "name": company.get("name", "the project"),
        "one_line": (company.get("tagline") or "")[:160],
        "milestone": (day.get("era") or {}).get("name", ""),
        "components": components,
        "ground_truth": {
            "completed": ([f"{state['shipped']} release(s) shipped, currently "
                           f"{state.get('version', '')}"]
                          if state.get("shipped") else [])
                         + [f"{state['merged_to_date']} changes merged to date"
                            if state.get("merged_to_date") else ""][:1],
            "in_progress": on_the_table,
            "not_started": sorted(day["forbidden"].get("services_not_started") or []),
            "decisions": [HOW_WE_REFERENCE],
            # Deliberately NOT the day's goals. The engine renders this as
            # "open questions NO ONE can resolve alone", so listing the very
            # thing the room came to settle tells everybody it cannot be
            # settled, while their own agenda stars it as something they must
            # land. The goals reach people through the agenda and the briefing.
            # Open issues are what this field is for: things everyone knows
            # are unresolved and nobody can close alone.
            "known_unknowns": [f"issue {i['number']}: {i['title']}"
                               for i in (state.get("open_issues") or [])][:8],
            "forbidden": forbidden(day, spec),
        },
        "resources": [
            {"name": world.humanize((o.get("title") or o["id"])[:70]),
             "type": o["kind"],
             "location": "[doc-link]", "held_by": world.label(_holder(world, o)),
             "artifact_id": re.sub(r"[^A-Za-z0-9._~/-]+", "-", str(o["id"]))}
            # A doc is NOT listed: with a wiki in their tools, a page is
            # something somebody wrote and anybody can open, not a link they
            # are handed. Listing it invites "the design doc is done, <link>"
            # for a page that was never written.
            for o in (spec.get("referenced_objects") or []) if o["kind"] != "doc"][:8],
    }


def _holder(world: World, obj: dict) -> str:
    if obj["kind"] == "doc":
        return (world.docs.get(obj["id"]) or {}).get("author", "")
    thread = world.threads.get(obj["id"]) or {}
    return (thread.get("messages") or [{}])[0].get("from", "")


# =============================================================================
# Is this clue capable of passing before we pay to find out?
# =============================================================================
# A `settles` clause that describes somebody ASKING rather than concluding.
# Phase 3's schema asks for "one short third-person clause" and nothing ever
# checked that it got one; three of the corpus's clues are questions wearing a
# conclusion's clothes, and a clue planted `must_settle` whose whole content is
# a question cannot be settled by anyone. Two channel-days were re-run three
# times each into that.
ASKS = re.compile(r"\b(asks?|asking|wonders?|wondering|queries|querying|"
                  r"unsure|unclear|whether or not)\b", re.I)


def clue_problems(world: World, spec: dict) -> list[str]:
    """Everything about this conversation's clues that makes one unwinnable.

    Free, and run before anything is spent. The two clues the February run lost
    are both named here for nothing — one for a question-shaped `settles`, one
    for an identifier the same prompt forbids — where finding them cost three
    paid re-runs of a channel-day each.
    """
    out = []
    allowed = {v.lower() for v in needed_names(spec)}
    for planted in spec.get("planted") or []:
        cid = planted.get("clue", "?")
        settles = (planted.get("settles") or "").strip()
        if not settles:
            out.append(f"{cid}: has no `settles`, so there is nothing to check "
                       "it against")
        elif ASKS.search(settles):
            out.append(f"{cid}: `settles` describes asking, not concluding "
                       f"({settles[:70]!r}). Planted as must-settle, so the "
                       "engine will push for an assertion the clue does not "
                       "contain.")
        if settles and settles == (planted.get("text") or "").strip():
            out.append(f"{cid}: `settles` fell back to the raw remark, so the "
                       "point it is meant to fix was never written down")
        for name in planted.get("verbatim") or []:
            if name.lower() not in allowed:
                out.append(f"{cid}: needs the name {name!r} said, but it is not "
                           "in this day's allow-list, so the symbol rule "
                           "forbids it in the same prompt that requires it")
        # Herrings are the exception and the only one: a reversed decision is
        # planted precisely so it covers nothing true, and phase 3 sets
        # `covers: []` on them deliberately.
        if not planted.get("covers") and planted.get("kind") != "herring":
            out.append(f"{cid}: covers no part of its requirement, so landing "
                       "it teaches nothing")
    return out


# What phase 4 knows how to turn into something a persona is asked to produce.
# Named rather than inferred: the point of the gate below is to notice a kind
# nobody wired up, and a set computed from the code would grow silently along
# with the bug.
CONSUMES = {"docs", "threads", "comments"}
# Declared in artifacts.json but not content: `collections` is the shelf list,
# `counts` is phase 2's own tally, `skipped` is what it deliberately declined.
NOT_CONTENT = {"collections", "counts", "skipped"}


def check_plan_covered(world: World, allowed: set[str]) -> int:
    """Refuse to run when the plan declares a kind nothing here can deliver.

    Phase 2 planned 26 page comments. Phase 4 had no code that read them, so
    they were generated and dropped, and nobody noticed across a 33-batch run —
    the corpus reported pages and emails and simply never mentioned comments.
    Three planted clues went with them.

    A kind nothing consumes cannot fail later: every downstream count is over
    what was asked for, so the gap is invisible by construction. This is the
    only place it can be seen, and it costs nothing to look.
    """
    missing = []
    for kind, items in sorted(world.artifacts.items()):
        if kind in NOT_CONTENT or not isinstance(items, list) or not items:
            continue
        if kind not in CONSUMES and kind not in allowed:
            missing.append((kind, len(items)))
    for kind, n in missing:
        # Warn per kind, fail once at the end: `rl.fail` exits, so failing
        # inside the loop would name the first offender and hide the rest.
        rl.warn(f"the plan declares {kind!r} ({n} item(s)) and phase 4 has no "
                "consumer for it — those would be generated and dropped")
    if missing:
        rl.fail("nothing here can deliver "
                + ", ".join(f"{k} ({n})" for k, n in missing)
                + ". A kind nothing consumes cannot fail later — every count "
                  "downstream is over what was asked for, so its absence is "
                  "invisible by construction. Wire up a consumer, or pass "
                  "--allow-unconsumed=" + ",".join(k for k, _ in missing)
                + " to run without them on purpose.")
    for kind in sorted(allowed & {k for k, v in world.artifacts.items()
                                  if isinstance(v, list) and v}):
        if kind not in CONSUMES:
            rl.warn(f"{kind!r} is declared by the plan and deliberately not "
                    "delivered this run")
    return len(missing)


def check_clues_runnable(world: World, days: list[str],
                         only: set[str] | None) -> int:
    """Say which clues cannot pass, before a token is spent. Returns the count."""
    problems, leaks, total = [], 0, 0
    for date in days:
        for spec in world.day(date)["specs"]:
            if only and spec["channel"] not in only:
                continue
            total += len(spec.get("planted") or [])
            leaks += sum(1 for p in spec.get("planted") or []
                         if p.get("forbidden_terms"))
            problems += [f"{date} #{spec['channel']}: {p}"
                         for p in clue_problems(world, spec)]
    for one in problems:
        rl.warn(one)
    if leaks:
        rl.info(f"{leaks} of {total} clue(s) carry giveaway terms; the "
                "transcript is checked for those after the run")
    if problems:
        rl.warn(f"{len(problems)} clue problem(s) — these will not pass however "
                "many times the day is re-run. Fix the plant, not the run.")
    else:
        rl.ok(f"{total} clue(s) in scope, none of them unwinnable")
    return len(problems)


# =============================================================================
# What each person came here to do
# =============================================================================
def planted_in(world: World, kind: str, ident: str) -> list[dict]:
    """Clues phase 3 hid inside one document or mail thread.

    A conversation carries its clues in the spec, where `member_grounding`
    finds them. A document carries its clues on the document, in
    `artifacts.json` — the same field name, a different file, and nothing was
    reading it. So a quarter of the corpus's clues were planted correctly and
    then had no way of ever being written down.

    A mail thread is asked for by THREAD id while the clue is planted on one
    message inside it, so those are gathered from the messages.
    """
    if kind == "doc":
        return list((world.docs.get(ident) or {}).get("planted") or [])
    if kind == "comment":
        return list((world.comments.get(ident) or {}).get("planted") or [])
    thread = world.threads.get(ident) or {}
    return [p for message in thread.get("messages") or []
            for p in message.get("planted") or []]


def obligations_of(world: World, spec: dict) -> list[dict]:
    """The plan's goals, in the shape the engine's artifact ledger reads.

    My goals carry `writes` as a LIST; the engine wants one obligation per
    thing written. Passing the list straight through produces an obligation the
    ledger cannot match against anything, which reads downstream as a document
    nobody was ever asked for.
    """
    out = []
    for goal in spec.get("goals") or []:
        owner = goal.get("owner")
        if not owner:
            continue
        for ref in goal.get("writes") or []:
            out.append({"writes": {
                "kind": ref["kind"], "id": ref["id"],
                "title": world.title_of(ref["kind"], ref["id"]),
                "by": owner,
                "action": "write" if ref["kind"] == "doc" else "send",
                "doc_kind": (world.docs.get(ref["id"]) or {}).get("kind", ""),
                # What this artifact is FOR, when phase 3 hid something in it.
                # The demand and the content used to live apart — the spec said
                # "dario writes the runbook", the clue sat on the runbook in
                # artifacts.json, and nothing joined them, so he wrote a runbook
                # that was not the one the corpus needed.
                "planted": planted_in(world, ref["kind"], ref["id"]),
            }})
        reads = [{"kind": r["kind"], "id": r["id"],
                  "title": world.title_of(r["kind"], r["id"]), "by": owner}
                 for r in goal.get("reads") or []]
        if reads:
            out.append({"reads": reads})
    for com in comments_here(world, spec):
        out.append({"writes": {
            "kind": "comment", "id": com["id"],
            "title": world.title_of("comment", com["id"]),
            "by": com["author"], "action": "comment", "doc_kind": "",
            "planted": planted_in(world, "comment", com["id"]),
        }})
    return out


def comments_here(world: World, spec: dict) -> list[dict]:
    """The page comments THIS conversation is responsible for today.

    A comment is dated and has an author, but no channel — so it has to be
    given to exactly one of the day's rooms or it is asked for once per
    conversation the author is in. The room is chosen by a stable sort rather
    than by whoever comes first out of a dict, because re-running one day must
    place it where the last run placed it.
    """
    date = spec.get("date") or ""
    rooms = sorted(_specs_for(world, date), key=lambda s: s.get("channel") or "")
    mine = []
    for com in world.comments_due(date):
        here = next((s for s in rooms
                     if com["author"] in {p["id"] for p in
                                          (s.get("participants") or [])}), None)
        if here is not None and here.get("channel") == spec.get("channel"):
            mine.append(com)
    return mine


def _specs_for(world: World, date: str) -> list[dict]:
    try:
        return world.day(date)["specs"]
    except SystemExit:
        return []


def _agenda_for_write(world: World, agenda: list, kind: str, ident: str) -> None:
    """The clue an artifact has to carry, worded as writing rather than saying.

    One body for page, mail and comment: the `where` word is the only thing
    that differs, and three copies of this drifted apart once already — the
    comment kind simply had no branch at all, so three clues were planted into
    pages nobody was ever asked to comment on.
    """
    where = {"doc": "page", "comment": "comment"}.get(kind, "mail")
    what = world.title_of(kind, ident)
    for planted in planted_in(world, kind, ident):
        agenda.append({
            "about": f"the {where} you are writing, {what}, has to say "
                     f"this in your own words: "
                     f"{world.humanize(planted['text'])}",
            "must_raise": True, "must_settle": True,
            "verbatim": list(planted.get("verbatim") or []),
            "leaf": planted.get("clue", "")})


def member_grounding(world: World, day: dict, spec: dict, persona: str) -> dict:
    """One participant's depth, confusions and agenda.

    The agenda is where a plan becomes motivation. A goal this person owns is
    `must_raise`, which the engine star-marks, re-surfaces near the end of the
    thread, and holds the wrap open for — so the planned business lands without
    anybody scripting the words.
    """
    person = world.people[persona]
    mine = {s["slug"] for s in person.get("services_owned") or []}

    agenda, own_goal = [], ""
    for goal in spec.get("goals") or []:
        mine_now = goal.get("owner") == persona
        agenda.append({"about": world.humanize(goal["goal"]), "must_raise": mine_now})
        if mine_now and not own_goal:
            own_goal = world.humanize(goal["goal"])

    # A planted clue is not scripted dialogue: the words stay the persona's,
    # only the point is fixed. `must_settle` is what separates it from ordinary
    # business — as a plain must_raise item a clue comes out as "still no
    # answer on whether X", which the engine correctly counts as raised,
    # because raising a topic IS how you discharge an ordinary item. A clue has
    # no such degraded form: it IS the conclusion, and a reader gets nothing
    # from the question.
    for planted in spec.get("planted") or []:
        if planted.get("holder") != persona:
            continue
        agenda.append({"about": world.humanize(planted["text"]),
                       "must_raise": True, "must_settle": True,
                       "verbatim": list(planted.get("verbatim") or []),
                       "leaf": planted.get("clue", "")})
        if not own_goal:
            own_goal = world.humanize(planted["settles"])

    # The same, for a clue hidden in a document or a mail this person owes
    # today. Worded as WRITING rather than raising, because the two are not
    # interchangeable: told to "make sure this comes up", a persona says it in
    # chat, the clue gate sees it said, and the page they were asked for still
    # does not contain it — a pass on the transcript and a hole in the corpus.
    for goal in spec.get("goals") or []:
        if goal.get("owner") != persona:
            continue
        for ref in goal.get("writes") or []:
            _agenda_for_write(world, agenda, ref["kind"], ref["id"])
            for planted in planted_in(world, ref["kind"], ref["id"]):
                if not own_goal:
                    own_goal = world.humanize(planted["settles"])

    # A comment is owed by a PERSON on a day, not by a goal in the spec — see
    # `comments_here` — so its agenda item is added beside the goals rather
    # than inside them.
    for com in comments_here(world, spec):
        if com["author"] != persona:
            continue
        _agenda_for_write(world, agenda, "comment", com["id"])
        page = world.title_of("doc", com.get("doc", ""))
        agenda.append({
            "about": f"leave a comment on the wiki page \"{page}\" — you "
                     f"{com.get('intent', 'have something to add')}, about "
                     f"{com.get('anchor') or 'what it says'}",
            "must_raise": True, "must_settle": False, "verbatim": [],
            "leaf": ""})

    owned = sorted(person.get("services_owned") or [],
                   key=lambda s: -(s.get("share_of_service") or 0))
    knows = [f"{s['slug']}, which you own" for s in owned[:4]]
    if not knows:
        knows = ["your own corner of the platform"]

    absent = {a["id"] for a in (spec.get("absent_owners") or [])
              if a.get("state") == "absent"}
    return {
        "role_line": world.humanize(
            f"{person['synthetic']['title']}. "
            f"{next((p['brings'] for p in spec['participants'] if p['id'] == persona), '')}"),
        "owns": ", ".join(s["slug"] for s in owned[:4]) or None,
        "knows": knows,
        "confusions": [{"kind": "open_question", "about": world.humanize(g["goal"])}
                       for g in (spec.get("goals") or [])
                       if g.get("owner") != persona][:2],
        "agenda": agenda,
        "current_goal": own_goal or world.humanize(spec.get("reason", "")),
        "availability": "out today" if persona in absent else "around today",
    }


def briefing(world: World, day: dict, spec: dict, floor: int = 0) -> str:
    """The free text the director reads before choosing who speaks next.

    It could always see the recent messages; what it could not see is why the
    conversation exists and who owes what. Deliberately the same facts the
    participants hold, so the director steers toward beats the people are
    already motivated to reach rather than pulling against them.
    """
    when = dt.date.fromisoformat(spec["date"])
    lines = [f"Today is {when.strftime('%A %-d %B %Y')}. This conversation is "
             "happening NOW and everything below is true as of this morning.",
             "", f"Why it is happening: {spec.get('reason', '')}", ""]

    if spec.get("purpose_class") != "social":
        lines += ["What it should get through:"]
        for n, goal in enumerate(spec.get("goals") or [], 1):
            owner = world.label(goal.get("owner", ""))
            lines.append(f"  {n}. {goal['goal']}"
                         + (f"   [{owner} must raise this]" if goal.get("owner") else ""))
            for beat in (goal.get("beats") or [])[:4]:
                lines.append(f"       - {beat}")
        lines.append("")

    if spec.get("agenda"):
        lines += ["On the agenda: " + "; ".join(spec["agenda"][:5]), ""]
    if spec.get("meetings"):
        lines += ["Meeting today: " + ", ".join(
            m if isinstance(m, str) else m.get("name", "")
            for m in spec["meetings"]), ""]
    # Someone who has NOT YET JOINED is not absent, they are a stranger. Saying
    # "Emil is out today" about a person who starts in three months invites the
    # room to wonder where he is, which is a worse leak than silence.
    away = [a for a in (spec.get("absent_owners") or [])
            if a.get("state") == "absent"]
    gone = [a for a in (spec.get("absent_owners") or [])
            if a.get("state") == "departed"]
    if away:
        lines += ["Out today: " + ", ".join(
            world.label(a["id"]) + (f" ({a['reason']})" if a.get("reason") else "")
            for a in away) + " — their input is missing and people may say so", ""]
    if gone:
        # Departed is not absence. Nobody waits for them, and nobody asks when
        # they are back; their work has an owner now or it has nobody.
        lines += ["No longer here: " + ", ".join(world.label(a["id"]) for a in gone)
                  + " — do not expect them back or wait on them", ""]
    norms = spec.get("norms") or {}
    if norms:
        lines += [f"Belongs in this channel: {norms.get('belongs_here', '')}",
                  f"Does NOT belong here: {norms.get('not_here', '')}", ""]
    lines.append(f"Wrap when: {spec.get('expected_outcome', '')}")
    if floor:
        # The director decides when a conversation is over, and the engine
        # refuses that decision until the floor is met — then forces a random
        # speaker to fill the gap, which is filler nobody chose. Telling the
        # director the floor up front means it steers toward the business still
        # outstanding instead of being overruled into padding.
        lines += ["",
                  f"Do NOT wrap before about {floor} exchanges. There is more "
                  "here than a single answer: if it feels finished early, the "
                  "part that has not been said yet is somebody's — find who "
                  "still owes something above and go to them."]
    return world.humanize("\n".join(lines))


def resolution_of(spec: dict) -> str:
    """Whether this thread is meant to land or stay open.

    Biased toward landing: telling a conversation whose own plan says it closes
    to leave a loose end is a worse failure than the one this prevents.

    A conversation carrying a planted clue ALWAYS lands, whatever its own prose
    says. This is the single most expensive interaction in the pipeline and it
    is invisible from either side: phase 2 writes an outcome like "no answer
    given, gideon says he'll come back to it, thread goes quiet", which reads
    as ordinary and true; phase 3 then plants a must-settle clue into that
    conversation; and phase 4 tells the persona holding the clue to leave the
    thing hanging. He does, faithfully, and the clue comes out as a question
    nobody answers — three paid re-runs of the channel-day, each one asking a
    person to both settle a point and leave it open. Whatever else that room
    was for, once a clue is in it, the clue is what it exists to land.
    """
    if spec.get("purpose_class") == "social":
        return ""
    if any(p.get("settles") for p in spec.get("planted") or []):
        return "resolves"
    outcome = (spec.get("expected_outcome") or "").lower()
    if any(m in outcome for m in OPEN_MARKERS) or OPEN_QUESTION.search(outcome):
        return "partial"
    if any(m in outcome for m in LANDS_MARKERS):
        return "resolves"
    return LANDS_BY_CLASS.get(spec.get("purpose_class", ""), "partial")


def build_channel(world: World, day: dict, spec: dict, nth: int = 0) -> dict:
    """One spec becomes one grounded channel."""
    import bespoke_user.sim_engine as G

    members = [p["id"] for p in spec["participants"]]
    social = spec.get("purpose_class") == "social"
    # The FLOOR is what actually decides length: most of the engine's ways to
    # end a conversation unlock only at min_turns, and its own default
    # (members + 3) is small enough that a fourteen-turn incident stops at six.
    floor = max(max(6, len(members) + 3), int(spec.get("max_turns", 12) * 0.7))
    channel = {
        # id identifies the RUN. A channel can hold TWO conversations on one
        # day — phase 2 schedules a short stand-up and a long review in
        # #code-review on the same date — and giving both the same id merged
        # them into one stream with colliding timestamps, which the ingest
        # rejects as a duplicate message id. `name` is what merges across days
        # into one readable history; `id` has to separate them.
        "id": f"{spec['channel']}-{spec['date']}-{nth}",
        "name": spec["channel"],
        "topic": (world.channels.get(spec["channel"]) or {}).get("purpose", ""),
        "situation_type": "social" if social else "professional",
        "isPrivate": False,
        "memberIds": members,
        "scenario": world.humanize(spec.get("reason", "")),
        "briefing": briefing(world, day, spec, floor),
        "max_turns": spec.get("max_turns", 12),
        "min_turns": floor,
    }

    if social:
        # The one thing here that is not grounded in the repository. Who they
        # are, NOT what they are working on: this is #random, and telling
        # someone their current bug here is exactly how work talk gets into the
        # one channel that is not for it.
        channel["memberBackgrounds"] = {
            p["id"]: f"You work with these people. None of that matters here."
            for p in spec["participants"]}
        chat = next((g["goal"] for g in spec.get("goals") or [] if g.get("goal")), "")
        channel["goals"] = {p["id"]: world.humanize(
            f"just chatting, nothing work related{': ' + chat if chat else ''}")
            for p in spec["participants"]}
        return channel

    channel["resolution"] = resolution_of(spec)
    channel["end_state"] = world.humanize(spec.get("expected_outcome", ""))
    # A planted point is settled business, so it belongs in the end state,
    # which is what every persona is shown near the end of the thread as the
    # place the team should LEAVE this. `resolution_of` has already forced this
    # channel to land for the same reason — the two have to agree, or the
    # persona is shown a settled end state by a thread told to stay open.
    settles = [world.humanize(p["settles"]) for p in spec.get("planted") or []
               if p.get("settles")
               and p["settles"].lower() not in channel["end_state"].lower()]
    if settles:
        channel["end_state"] = "; ".join([channel["end_state"]] + settles)

    return G.attach_grounding(
        channel,
        shared=shared_ground(world, day, spec),
        members={p: member_grounding(world, day, spec, p) for p in members},
        domain=f"{world.company['company'].get('slug', 'world')}.internal",
        obligations=obligations_of(world, spec))


# =============================================================================
# Which days
# =============================================================================
def pick_days(world: World, count: int) -> list[str]:
    """The best run of consecutive working days: the most channels speaking,
    then the most conversations. Derived rather than fixed, because the right
    days are a property of this corpus and no other."""
    rows = []
    for date in world.spec_days():
        specs = world.day(date)["specs"]
        rows.append((date, {s["channel"] for s in specs}, len(specs),
                     sum(1 for s in specs if s.get("planted"))))
    if len(rows) <= count:
        return [r[0] for r in rows]
    best = None
    for i in range(len(rows) - count + 1):
        window = rows[i:i + count]
        span = (dt.date.fromisoformat(window[-1][0])
                - dt.date.fromisoformat(window[0][0])).days
        if span > count + 3:                  # a weekend is fine, a hole is not
            continue
        score = (sum(r[3] for r in window),                 # clues first
                 len({c for r in window for c in r[1]}),    # then breadth
                 sum(r[2] for r in window))
        if best is None or score > best[0]:
            best = (score, [r[0] for r in window])
    return best[1] if best else [r[0] for r in rows[:count]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--specs", type=Path, default=DEFAULT_SPECS)
    parser.add_argument("--out", type=Path, default=OUT,
                        help="the phase 4 root. Runs live in <out>/runs/<run> "
                             "and <out>/latest points at the newest")
    parser.add_argument("--run", default=None,
                        help="name this run's output directory. Default is a "
                             "timestamp, so runs never mix. Reuse a name "
                             "deliberately to continue a run split across "
                             "several invocations")
    parser.add_argument("--days", default=None,
                        help="comma-separated; default is the derived sample")
    parser.add_argument("--day-count", type=int, default=DEFAULT_DAY_COUNT)
    parser.add_argument("--channels", default=None)
    parser.add_argument("--workspace", default="")
    parser.add_argument("--auth", default="split",
                        choices=["split", "oauth", "api-key"],
                        help="split (default) puts the persona turns on the "
                             "OAuth token and the director on the API key")
    parser.add_argument("--model", default=None)
    parser.add_argument("--concurrency", type=int, default=6,
                        help="how many PEOPLE may be talking at once across all "
                             "conversations. Each participant is a live agent "
                             "session, so this is the real load; too high and the "
                             "director's own call times out and the engine drops "
                             "the channel. 6 suits a 4-core machine.")
    parser.add_argument("--clue-tries", type=int, default=3)
    parser.add_argument("--clue-repairs", type=int, default=2,
                        help="how many times a clue that came out THINNER than "
                             "it was planted may be repaired where it stands — "
                             "the holder sends the missing part as one more "
                             "message — before the channel-day is re-run "
                             "instead. 0 disables repair.")
    parser.add_argument("--dry-run", action="store_true",
                        help="write the review document and stop; costs nothing")
    parser.add_argument("--prove-solvable", action="store_true",
                        help="do not simulate. Re-run phase 3's solvability "
                             "proof against what the personas ACTUALLY said in "
                             "the run named by --run, falling back to the "
                             "planned clue text for days not yet simulated")
    parser.add_argument("--no-repo-tool", action="store_true",
                        help="do not offer the repository tools. For measuring "
                             "what they cost: the same days with and without, "
                             "everything else equal")
    parser.add_argument("--allow-unconsumed", default="",
                        help="comma-separated artifact kinds the plan declares "
                             "that this run should skip on purpose, e.g. "
                             "`comments`. Without this a kind phase 4 cannot "
                             "deliver stops the run rather than being dropped")
    parser.add_argument("--audit-only", action="store_true",
                        help="do not simulate. Re-judge the corpus named by "
                             "--run against its own transcript and the pages "
                             "and mail on disk, and REWRITE the ledgers. Use "
                             "when a run's clue or artifact ledger covers "
                             "fewer days than the transcript does")
    parser.add_argument("--install", action="store_true",
                        help="copy the result into data/ once it is good")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)
    args.allow_unconsumed = {k.strip() for k in
                             (args.allow_unconsumed or "").split(",") if k.strip()}

    # A run directory is named the moment the process starts, never derived
    # later from anything that has since moved on.
    args.run = args.run or dt.datetime.now().strftime("%Y-%m-%dT%H%M")

    resolve_auth(args.auth)          # BEFORE anything reaches bespoke_user

    rl.heading("Reading")
    world = World(args)
    days = ([d.strip() for d in args.days.split(",")] if args.days
            else pick_days(world, args.day_count))
    only = {c.strip() for c in args.channels.split(",")} if args.channels else None
    rl.ok(f"{len(world.spec_days())} day(s) of specs, {len(world.clue_of)} clue(s) "
          f"planted, {len(world.docs)} document(s) and {len(world.threads)} "
          "mail thread(s) on the calendar")
    rl.ok(f"simulating {len(days)} day(s): {', '.join(days)}")
    return run(world, days, only, args)


def run(world: World, days: list[str], only: set[str] | None, args) -> int:
    # Imported here, not at module scope: this reaches `bespoke_user`, which
    # resolves auth the moment it is touched, and `resolve_auth` has to have run
    # first. See this module's docstring.
    from phase4_run import audit_corpus, prove_corpus, simulate   # noqa: E402
    if args.prove_solvable:
        return prove_corpus(world, Path(args.out) / "runs" / args.run, args)
    if args.audit_only:
        root = Path(args.out)
        return audit_corpus(world, root, root / "runs" / args.run, args)
    return simulate(world, days, only, args)


if __name__ == "__main__":
    sys.exit(main())
