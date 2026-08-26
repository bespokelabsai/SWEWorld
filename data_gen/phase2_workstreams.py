#!/usr/bin/env python3
"""Phase 2b — threads of work, and the documents and mail they produce.

Two outputs, for two reasons.

**Workstreams.** An episode is pull-request sized; a conversation is not. People
talk about "getting Anthropic batch working", which ran three weeks and eleven
episodes, not about one merge. Without this layer every generated day is about a
commit and no two days connect to each other.

**The artifact calendar.** Documents and internal mail are planned here rather
than inside the day stage, because a design doc written on Tuesday has to exist
on Wednesday. If each day invented its own, the days would have to run strictly
in sequence — hundreds of serial calls — or Wednesday would cite a document
nobody ever wrote. Fixing the calendar first keeps the days independent, and
lets the whole ledger be checked before a single conversation is generated.

Nothing here invents an event. Every workstream is a real cluster of real
episodes, and every artifact is triggered by something in the record: a release
tag, a revert, a large refactor, a person arriving, one of the five dated
handoffs. What the model supplies is the naming and the narrative.

Writes `build/workstreams.json` and `build/artifacts.json`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import hashlib
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402
from phase2_timeline import local_day, parse_ts, usable_episodes  # noqa: E402

SCHEMA_VERSION = 1

DEFAULT_EPISODES = rl.DEFAULT_BUILD_DIR / "engineering_episodes.json"
DEFAULT_GROUNDING = rl.DEFAULT_BUILD_DIR / "engineering_grounding.json"
DEFAULT_COMPANY = rl.DEFAULT_BUILD_DIR / "company_grounding.json"
DEFAULT_TIMELINE = rl.DEFAULT_BUILD_DIR / "timeline.json"
DEFAULT_WORKSTREAMS = rl.DEFAULT_BUILD_DIR / "workstreams.json"
DEFAULT_ARTIFACTS = rl.DEFAULT_BUILD_DIR / "artifacts.json"

# Two episodes on the same service belong to the same push of work if they land
# within a week of each other. Longer and unrelated bursts merge; shorter and a
# fortnight's work on one thing splits into fragments nobody would name
# separately.
BURST_GAP_DAYS = 7

# A refactor big enough that a team would write something down first.
DESIGN_DOC_LINES = 2000

# How many `claude` processes one subscription tolerates at once.
CLI_WORKERS = 2

# Where each kind of document lives in the wiki.
COLLECTIONS = {
    "design": "engineering",
    "planning": "engineering",
    "handover": "engineering",
    "runbook": "engineering",
    "meeting-notes": "meetings",
    "postmortem": "incidents",
    "release-notes": "releases",
    "onboarding": "onboarding",
}


# =============================================================================
# Inputs
# =============================================================================
def load(path: Path, what: str) -> dict:
    if not path.exists():
        rl.fail(f"{path} does not exist — {what}")
    return json.loads(path.read_text(encoding="utf-8"))


class Inputs:
    def __init__(self, args):
        self.grounding = load(args.grounding, "run analyze_repository.py first")
        self.company = load(args.company, "run phase1_company_grounding.py first")
        self.timeline = load(args.timeline, "run phase2_timeline.py first")
        self.episodes = usable_episodes(load(args.episodes, "run build_episodes.py first"))

        self.persona_of = dict(self.company["identity_map"]["person_to_persona"])
        self.persona_of_login = dict(self.company["identity_map"]["login_to_persona"])
        self.people = {p["synthetic"]["id"]: p for p in self.company["people"]}
        self.employees = [p["synthetic"]["id"] for p in self.company["people"]
                          if p["class"] == "employee"]
        self.services = {s["slug"]: s for s in self.company["services"]}
        self.days = {d["date"]: d for d in self.timeline["days"]}

        self.subsystem_service: dict[str, list[str]] = defaultdict(list)
        for service in self.company["services"]:
            for package in service.get("packages") or []:
                self.subsystem_service[package].append(service["slug"])

    def persona(self, real_id: str | None) -> str | None:
        return self.persona_of.get(real_id or "")

    def login(self, login: str | None) -> str | None:
        return self.persona_of_login.get(login or "")

    def is_conversation_day(self, day: dt.date) -> bool:
        """Will this day carry conversations at all?

        The artifact calendar and the conversation calendar have to agree, or a
        document lands on a day nobody is talking and can never be attached to
        the discussion that produced it. Seven documents and fifteen mail
        messages were scheduled onto silent days before this existed.
        """
        record = self.days.get(day.isoformat())
        if record is None:
            return False
        activity = record["activity"]
        has_work = bool(activity["commits"] or activity["prs_opened"]
                        or activity["reviews"] or activity["releases"]
                        or activity["issues_opened"])
        if record["is_weekend"]:
            return bool(activity["incident"])
        return has_work

    def present_on(self, day: dt.date) -> list[str]:
        """Who was at work that day — and nobody at all outside the span.

        Returning the whole roster for an unknown date was quietly scheduling a
        design doc for 2024-10-25, two days before the repository existed, with
        an author whose presence could not be checked because there was no day
        to check it against.
        """
        record = self.days.get(day.isoformat())
        if not record:
            return []
        return [p["persona"] for p in record["people"] if p["state"] == "present"]

    def busiest_on(self, day: dt.date) -> list[str]:
        """Present, most active first.

        The fallback used to be roster order, which handed a fifth of every
        document to whoever happened to sort first. Whoever was actually working
        that day is both fairer and likelier to be the one who wrote it.
        """
        record = self.days.get(day.isoformat())
        if not record:
            return []
        active = [p for p in record["people"] if p["state"] == "present"]
        active.sort(key=lambda p: (-(p["commits"] + p["reviews"] + p["comments"]),
                                   p["persona"]))
        return [p["persona"] for p in active]


# =============================================================================
# Clustering
# =============================================================================
def dominant_service(episode: dict, subsystem_service: dict) -> str:
    counts: Counter[str] = Counter()
    for subsystem, files in (
            episode["metrics"]["file_distribution"].get("by_subsystem") or {}).items():
        for service in subsystem_service.get(subsystem, []):
            counts[service] += files
    return counts.most_common(1)[0][0] if counts else "other"


def cluster(inputs: Inputs) -> list[dict]:
    """Bursts of work on one service, split at month boundaries.

    Two signals, and both are needed. Grouping by the dependency graph alone
    leaves 242 of 435 episodes as singletons — the file-overlap edges are too
    sparse to connect a thread of work. Grouping by service alone produces
    clusters of sixty, which is not a workstream but a whole component's
    lifetime. Service plus a one-week gap gives bursts; the month boundary keeps
    "batch work in January" and "batch work in February" as the two separate
    things people actually referred to.
    """
    episodes = sorted(inputs.episodes,
                      key=lambda e: (parse_ts(e["timeline"]["merged_at"]), e["id"]))
    last: dict[str, tuple[int, dt.datetime, tuple]] = {}
    groups: dict[int, list[dict]] = defaultdict(list)
    next_id = 0

    for episode in episodes:
        service = dominant_service(episode, inputs.subsystem_service)
        when = parse_ts(episode["timeline"]["merged_at"])
        month = (when.year, when.month)
        previous = last.get(service)
        if (previous and previous[2] == month
                and (when - previous[1]).days <= BURST_GAP_DAYS):
            group_id = previous[0]
        else:
            group_id, next_id = next_id, next_id + 1
        last[service] = (group_id, when, month)
        groups[group_id].append(episode)

    out = []
    for group_id, members in sorted(groups.items()):
        first = local_day(members[0]["timeline"]["first_commit_at"])
        last_day = local_day(members[-1]["timeline"]["merged_at"])
        service = dominant_service(members[0], inputs.subsystem_service)
        authors = Counter(inputs.persona(e["people"]["author"]) for e in members)
        authors.pop(None, None)
        reviewers: Counter[str] = Counter()
        for episode in members:
            for reviewer in episode["people"].get("reviewers") or []:
                persona = inputs.login(reviewer.get("login"))
                if persona:
                    reviewers[persona] += 1
        days = sorted({local_day(e["timeline"]["merged_at"]).isoformat()
                       for e in members})
        out.append({
            "id": f"ws-{group_id:03d}-{service}",
            "service": service,
            "service_name": inputs.services.get(service, {}).get("name", service),
            "first_day": first.isoformat() if first else None,
            "last_day": last_day.isoformat() if last_day else None,
            "days_live": days,
            "episodes": [{"id": e["id"], "title": e["title"],
                          "objective": e.get("objective"),
                          "change_type": e["change_type"]["primary"],
                          "merged": local_day(e["timeline"]["merged_at"]).isoformat(),
                          "persona": inputs.persona(e["people"]["author"]),
                          "pr": (e["provenance"].get("pull_request") or {}).get("number"),
                          "lines": e["metrics"]["lines_added"] + e["metrics"]["lines_deleted"]}
                         for e in members],
            "driver": authors.most_common(1)[0][0] if authors else None,
            "collaborators": [p for p, _ in authors.most_common()[1:4]],
            "reviewers": [p for p, _ in reviewers.most_common(3)],
            "change_types": dict(Counter(e["change_type"]["primary"] for e in members)),
            "lines": sum(e["metrics"]["lines_added"] + e["metrics"]["lines_deleted"]
                         for e in members),
            "era": inputs.days.get(days[0], {}).get("era", {}).get("slug"),
        })
    return out


# =============================================================================
# The artifact calendar
# =============================================================================
def next_working_day(day: dt.date) -> dt.date:
    day += dt.timedelta(days=1)
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)
    return day


def previous_working_day(day: dt.date) -> dt.date:
    day -= dt.timedelta(days=1)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    return day


def slug(text: str, limit: int = 40) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:limit]

class Ownership:
    """Who is responsible for what, and who is around to write it down.

    Authorship was the weakest part of the first pass: it fell back to whoever
    committed most that day, which handed a fifth of all documents to one person
    and put the batch design doc in the hands of someone who had never touched
    batch. Ownership is measured — `services[].owners` is ordered by real commit
    share — so the person who owns the thing writes the thing, and only if they
    were at work.
    """

    def __init__(self, inputs: "Inputs"):
        self.inputs = inputs
        self.owners = {s["slug"]: list(s.get("owners") or [])
                       for s in inputs.company["services"]}
        # Whoever the most people report to is the person who sends the weekly
        # mail and writes the planning docs.
        reports = Counter(line["reports_to"]
                          for line in inputs.company["org"]["reporting_lines"]
                          if line.get("reports_to"))
        self.lead = next((p for p, _ in reports.most_common()
                          if p in inputs.employees), None)

    def author(self, day: dt.date, *, service: str | None = None,
               prefer: Sequence[str] = (), allow_lead: bool = True) -> str | None:
        """The person who would have written this, if they were there.

        In order: whoever the record names as involved, then the service's
        owners by share, then the lead, then anyone. Returns None when the day
        has nobody at all, which is how out-of-span dates get dropped rather
        than silently attributed.
        """
        present = set(self.inputs.present_on(day))
        if not present:
            return None
        for candidate in prefer:
            if candidate and candidate in present:
                return candidate
        for candidate in self.owners.get(service or "", []):
            if candidate in present:
                return candidate
        if allow_lead and self.lead in present:
            return self.lead
        return next(iter(self.inputs.busiest_on(day)), None)


def week_of(day: dt.date) -> dt.date:
    """The Monday of that week."""
    return day - dt.timedelta(days=day.weekday())


def plan_artifacts(inputs: Inputs, workstreams: list[dict]) -> dict:
    """Every document and mail thread the record gives a reason for.

    Two rhythms, deliberately. A workplace has a *cadence* — the weekly note,
    the Monday mail — which is most of the volume and almost all of the texture,
    and it has *events*, which is where the interesting documents come from. The
    first pass had only events, so it produced 61 documents across nine months
    and a wiki that looked abandoned.

    Everything is anchored: a weekly update summarises that week's real commits,
    merges and releases; a postmortem names the revert that caused it; a design
    doc belongs to a workstream that really ran. Nothing is scheduled outside the
    span, on a weekend, or for someone who was not at work.
    """
    docs: list[dict] = []
    threads: list[dict] = []
    skipped: list[str] = []
    own = Ownership(inputs)
    grounding = inputs.grounding

    first_day = dt.date.fromisoformat(inputs.timeline["window"]["first"])
    last_day = dt.date.fromisoformat(inputs.timeline["window"]["last"])
    rich_until = dt.date.fromisoformat(inputs.timeline["window"]["rich_until"])

    def workday(day: dt.date | None, *, forward: bool = True) -> dt.date | None:
        """A working day inside the span that will actually carry conversations.

        Nudging onto a weekday is not enough: a Wednesday with no commits, no
        reviews and no releases gets no conversation either, so a document dated
        there has nobody to have produced it. Walk on until a day that does.
        """
        if day is None or day < first_day or day > last_day:
            return None
        step = 1 if forward else -1
        for _ in range(14):
            if day < first_day or day > last_day:
                return None
            if day.weekday() < 5 and inputs.is_conversation_day(day):
                return day
            day += dt.timedelta(days=step)
        return None

    # ---- the weekly rhythm -------------------------------------------------
    # One mail and one set of notes a week, for as long as there is a team. Both
    # carry the week's real activity so the render stage writes from facts
    # rather than filler.
    weeks: dict[dt.date, dict] = {}
    for record in inputs.timeline["days"]:
        day = dt.date.fromisoformat(record["date"])
        if day > rich_until:
            continue
        bucket = weeks.setdefault(week_of(day), {
            "commits": 0, "merged": [], "released": [], "people": Counter(),
            "incidents": 0, "services": Counter()})
        bucket["commits"] += len(record["activity"]["commits"])
        bucket["merged"] += [p["title"] for p in record["activity"]["prs_merged"]]
        bucket["released"] += [r["tag"] for r in record["activity"]["releases"]]
        bucket["incidents"] += 1 if record["activity"]["incident"] else 0
        for commit in record["activity"]["commits"]:
            if commit["persona"]:
                bucket["people"][commit["persona"]] += 1
            for service in commit["services"]:
                bucket["services"][service] += 1

    for monday, week in sorted(weeks.items()):
        if week["commits"] == 0:
            continue                       # a dead week gets no update
        covers = {
            "week_of": monday.isoformat(),
            "commits": week["commits"],
            "merged": week["merged"][:8],
            "released": week["released"],
            "incidents": week["incidents"],
            "busiest": [p for p, _ in week["people"].most_common(4)],
            "services": [s for s, _ in week["services"].most_common(4)],
        }
        headline = _headline(week)

        # Monday mail, from whoever is running things, to everyone at work.
        # It goes out the Monday *after* the week it describes: a note sent on
        # Monday morning cannot report what the team shipped that week.
        send_day = workday(monday + dt.timedelta(days=7))
        sender = own.author(send_day, prefer=[own.lead]) if send_day else None
        if send_day and sender:
            recipients = sorted(set(inputs.present_on(send_day)) - {sender})
            if recipients:
                tid = f"weekly-{monday.isoformat()}"
                threads.append(_thread(
                    tid, send_day, sender, recipients,
                    {"trigger": "weekly-update", "week_of": monday.isoformat(),
                     "sent_on": send_day.isoformat(),
                     "evidence": [f"{week['commits']} commits in the week of {monday}"]},
                    hint=f"looking back at the week of {monday:%-d %b}: {headline}",
                    responders=reply_plan(tid, "weekly-update", sender, recipients,
                                          week=covers,
                                          urgent=bool(week["incidents"])),
                    covers=covers,
                    subject=f"Week of {monday:%-d %b} — {headline}"))

        # Notes from the weekly sync, written by whoever owns the busiest area.
        notes_day = workday(monday + dt.timedelta(days=2))
        busiest_service = covers["services"][0] if covers["services"] else None
        scribe = own.author(notes_day, service=busiest_service,
                            prefer=covers["busiest"]) if notes_day else None
        if notes_day and scribe:
            docs.append(_doc(
                f"notes-{monday.isoformat()}", "meeting-notes", notes_day, scribe,
                {"trigger": "weekly-sync", "week_of": monday.isoformat(),
                 "evidence": [f"{week['commits']} commits in the week of {monday}"]},
                hint=f"weekly sync, week of {monday:%-d %b}: {headline}",
                covers=covers, title=f"Weekly sync, {monday:%-d %b} — {headline}"))

    # ---- releases ----------------------------------------------------------
    for record in inputs.timeline["days"]:
        for release in record["activity"]["releases"]:
            day = workday(dt.date.fromisoformat(record["date"]))
            if not day:
                continue
            tag = release["tag"]
            cutters = [c["persona"] for c in record["activity"]["commits"]
                       if c["persona"] and re.search(r"bump|release", c["subject"] or "",
                                                     re.I)]
            author = own.author(day, service="release-and-ci", prefer=cutters)
            if not author:
                skipped.append(f"release {tag} on {day}: nobody at work")
                continue
            shipped = [p["title"] for p in record["activity"]["prs_merged"]][:8]
            docs.append(_doc(f"release-{slug(tag)}", "release-notes", day, author,
                             {"trigger": "release", "tag": tag,
                              "evidence": [f"tag {tag} on {day}"]},
                             hint=f"what went into {tag}",
                             covers={"tag": tag, "merged": shipped}))
            recipients = sorted(set(inputs.present_on(day)) - {author})
            if recipients:
                tid = f"announce-{slug(tag)}"
                threads.append(_thread(tid, day, author, recipients,
                                       {"trigger": "release", "tag": tag,
                                        "evidence": [f"tag {tag} on {day}"]},
                                       hint=f"announcing {tag}",
                                       responders=reply_plan(
                                           tid, "release", author, recipients,
                                           urgent=".post" in (tag or "")),
                                       covers={"tag": tag, "merged": shipped},
                                       subject=f"{tag} is out"))

    # ---- incidents ---------------------------------------------------------
    incidents_by_service: Counter[str] = Counter()
    for record in inputs.timeline["days"]:
        incident = record["activity"]["incident"]
        if not incident:
            continue
        day = dt.date.fromisoformat(record["date"])
        written = workday(next_working_day(day))
        if not written:
            continue
        culprits = [c["persona"] for c in record["activity"]["commits"]
                    if c["persona"] and c["sha"] in incident["commits"]]
        services = [s for c in record["activity"]["commits"]
                    if c["sha"] in incident["commits"] for s in c["services"]]
        service = Counter(services).most_common(1)[0][0] if services else None
        author = own.author(written, service=service, prefer=culprits)
        if not author:
            continue
        if service:
            incidents_by_service[service] += 1
        docs.append(_doc(f"postmortem-{day.isoformat()}", "postmortem", written, author,
                         {"trigger": incident["kind"], "on": day.isoformat(),
                          "service": service, "evidence": incident["evidence"]},
                         hint=f"what broke on {day:%-d %b} and why",
                         covers={"on": day.isoformat(), "kind": incident["kind"],
                                 "evidence": incident["evidence"]}))

    # ---- a runbook once an area has hurt them more than twice --------------
    for service, count in incidents_by_service.most_common():
        if count < 3:
            continue
        hits = [d for d in docs if d["kind"] == "postmortem"
                and d["occasion"].get("service") == service]
        after = workday(dt.date.fromisoformat(hits[2]["created_at"])
                        + dt.timedelta(days=3))
        author = own.author(after, service=service) if after else None
        if not author:
            continue
        docs.append(_doc(f"runbook-{service}", "runbook", after, author,
                         {"trigger": "repeat-incidents", "service": service,
                          "evidence": [h["id"] for h in hits[:3]]},
                         hint=f"how to handle {service} when it goes wrong "
                              f"({count} incidents by now)",
                         covers={"service": service, "incidents": count}))

    # ---- design docs, owned by whoever drove the work ----------------------
    for workstream in workstreams:
        if workstream["lines"] < DESIGN_DOC_LINES or len(workstream["episodes"]) < 3:
            continue
        start = dt.date.fromisoformat(workstream["first_day"])
        written = workday(previous_working_day(start), forward=False)
        if not written:
            skipped.append(f"design for {workstream['id']}: no room before {start}")
            continue
        author = own.author(written, service=workstream["service"],
                            prefer=[workstream["driver"]] + workstream["collaborators"],
                            allow_lead=False)
        if not author:
            skipped.append(f"design for {workstream['id']}: nobody at work on {written}")
            continue
        docs.append(_doc(f"design-{workstream['id']}", "design", written, author,
                         {"trigger": "large-refactor", "workstream": workstream["id"],
                          "service": workstream["service"],
                          "evidence": [f"{workstream['lines']} lines across "
                                       f"{len(workstream['episodes'])} episodes",
                                       workstream["episodes"][0]["id"]]},
                         hint=f"the plan for {workstream['service_name']} work "
                              f"starting {start:%-d %b}",
                         workstream=workstream["id"],
                         covers={"workstream": workstream["id"],
                                 "episodes": [e["title"]
                                              for e in workstream["episodes"][:6]]}))

    # ---- people arriving ---------------------------------------------------
    for entry in grounding["timeline"]:
        if entry["kind"] != "person-joined":
            continue
        day = workday(_entry_day(entry))
        if not day:
            continue
        arriving = _personas_in(entry, inputs)
        arriving = [p for p in arriving if p in inputs.employees]
        if not arriving:
            continue
        host = own.author(day, prefer=[own.lead], allow_lead=True)
        if not host or host in arriving:
            continue
        tid = f"welcome-{slug(arriving[0])}-{day}"
        welcomers = sorted(set(inputs.present_on(day)) - {host})
        threads.append(_thread(tid, day, host, welcomers,
                               {"trigger": "person-joined", "who": arriving,
                                "evidence": entry.get("evidence", [])[:2]},
                               hint=f"{arriving[0]} starting",
                               responders=reply_plan(tid, "person-joined", host,
                                                     welcomers),
                               covers={"who": arriving},
                               subject=f"{arriving[0]} joins us"))
        docs.append(_doc(f"onboarding-{slug(arriving[0])}", "onboarding", day, host,
                         {"trigger": "person-joined", "who": arriving,
                          "evidence": entry.get("evidence", [])[:2]},
                         hint=f"getting {arriving[0]} set up",
                         covers={"who": arriving}))

    # ---- handovers ---------------------------------------------------------
    for handoff in grounding["collaboration"]["handoffs"]:
        day = workday(_month_day(handoff.get("when")))
        giver = inputs.persona(handoff.get("from_person"))
        taker = inputs.persona(handoff.get("to_person"))
        if not (day and giver and taker):
            continue
        # Some real handoffs are between drive-by contributors — the Mistral
        # batch backend passed from one outside contributor to another. Those
        # people have commits but no seat in the workspace, so an internal
        # thread between them would be a lie. Record the skip.
        if giver not in inputs.employees or taker not in inputs.employees:
            skipped.append(f"handover {handoff['area']}: {giver} -> {taker}, not staff")
            continue
        docs.append(_doc(f"handover-{slug(handoff['area'])}", "handover", day, giver,
                         {"trigger": "handoff", "from": giver, "to": taker,
                          "evidence": handoff.get("evidence", [])[:2]},
                         hint=f"handing {handoff['area']} to {taker}",
                         covers={"area": handoff["area"], "to": taker}))
        tid = f"handover-{slug(handoff['area'])}"
        threads.append(_thread(tid, day, giver, [taker],
                               {"trigger": "handoff",
                                "evidence": handoff.get("evidence", [])[:2]},
                               hint=f"arranging the {handoff['area']} handover",
                               responders=reply_plan(tid, "handoff", giver, [taker],
                                                     partner=taker),
                               covers={"area": handoff["area"]}))

    # ---- a plan at each change of era --------------------------------------
    for era in grounding["eras"]:
        day = workday(_month_day(era["start_month"]))
        if not day or day <= first_day:
            continue
        author = own.author(day, prefer=[own.lead])
        if not author:
            continue
        docs.append(_doc(f"plan-{era['slug']}", "planning", day, author,
                         {"trigger": "era-start", "era": era["slug"],
                          "evidence": era.get("evidence", [])[:2]},
                         hint=f"what changes going into {era['name']}",
                         covers={"era": era["slug"],
                                 "what_changed": era["what_changed_entering_it"][:400]}))

    docs.sort(key=lambda d: (d["created_at"], d["id"]))
    threads.sort(key=lambda t: (t["messages"][0]["date"], t["id"]))
    comments = plan_comments(docs, inputs, own, workstreams, workday)
    return {"docs": docs, "threads": threads, "comments": comments,
            "skipped": skipped}


# How often a page of each kind draws a comment, and how many when it does.
# A wiki where every page has a thread on it is as wrong as one where none does;
# most pages are read and left alone.
COMMENT_ODDS = {
    "design": (60, 3),        # the people who have to build it push back
    "handover": (70, 2),      # the person taking it over has questions
    "postmortem": (50, 2),    # "did we ever fix the underlying thing"
    "runbook": (50, 2),       # a correction from whoever ran it next
    "planning": (40, 2),
    "onboarding": (30, 1),    # the new person asks
    "meeting-notes": (20, 1),
    "release-notes": (10, 1),
}


def plan_comments(docs: list[dict], inputs: Inputs, own: "Ownership",
                  workstreams: list[dict], workday) -> list[dict]:
    """Who wrote on which page, and whether it got resolved.

    Grounded the same way everything else is: a design doc is commented on by
    the people who went on to do that work, a handover by the person receiving
    it, and every commenter has to have been at work on the day. The `quote`
    field is left to the render stage, which is the only step that knows what
    the page actually says; the plan carries what to anchor to instead.
    """
    by_id = {w["id"]: w for w in workstreams}
    out: list[dict] = []

    for doc in docs:
        odds, most = COMMENT_ODDS.get(doc["kind"], (0, 0))
        if not odds or stable_jitter(doc["id"] + "c", 100) >= odds:
            continue
        wanted = 1 + stable_jitter(doc["id"] + "n", most)

        # Who would plausibly read this page and have something to say.
        workstream = by_id.get(doc.get("workstream") or "")
        interested = []
        if workstream:
            interested = [workstream["driver"], *workstream["collaborators"],
                          *workstream["reviewers"]]
        elif doc["occasion"].get("to"):
            interested = [doc["occasion"]["to"]]
        elif doc["occasion"].get("service"):
            interested = own.owners.get(doc["occasion"]["service"], [])
        interested = [p for p in dict.fromkeys(interested) if p != doc["author"]]

        posted = 0
        first_id = None
        for step in range(wanted):
            when = workday(dt.date.fromisoformat(doc["created_at"])
                           + dt.timedelta(days=1 + step))
            if when is None:
                break
            present = set(inputs.present_on(when))
            if not present:
                continue
            # Alternate: someone asks, and the author often answers.
            if step % 2 == 0 or not first_id:
                who = next((p for p in interested if p in present), None)
                who = who or next((p for p in own.owners.get(
                    doc["occasion"].get("service", ""), []) if p in present), None)
                reply_to = None
            else:
                who = doc["author"] if doc["author"] in present else None
                reply_to = first_id
            if not who or who == (out[-1]["author"] if reply_to and out else None):
                continue
            comment_id = f"{doc['id']}-c{step}"
            out.append({
                "id": comment_id,
                "doc": doc["id"],
                "author": who,
                "created_at": when.isoformat(),
                "reply_to": reply_to,
                "anchor": doc["hint"],
                "intent": ("answers the question" if reply_to
                           else "questions or adds to the page"),
                # A thread closes when the author has answered it — and in
                # BookStack a thread is closed by archiving its ROOT, which
                # hides the whole exchange. `ingest_comments.py` enforces
                # exactly that and rejects `archived` on a reply, so putting
                # the flag here (on the answer) failed the bake on every one
                # of them. The root is marked below, once we know it was
                # answered.
                "archived": False,
            })
            if reply_to is None:
                first_id = comment_id
            else:
                for earlier in out:
                    if earlier["id"] == reply_to:
                        earlier["archived"] = True
            posted += 1
        if posted:
            doc["has_comments"] = True
    out.sort(key=lambda c: (c["created_at"], c["id"]))
    return out


def _headline(week: dict) -> str:
    """A few words about what the week was actually about."""
    if week["released"]:
        return f"{', '.join(week['released'][:2])} out"
    if week["incidents"] == 1:
        return "something broke"
    if week["incidents"] > 1:
        return f"{week['incidents']} things broke"
    if week["services"]:
        return f"mostly {week['services'].most_common(1)[0][0].replace('-', ' ')}"
    return f"{week['commits']} commits"


def _doc(doc_id: str, kind: str, day: dt.date, author: str, occasion: dict,
         *, hint: str, workstream: str | None = None, covers: dict | None = None,
         title: str | None = None) -> dict:
    return {
        "id": doc_id, "kind": kind, "collection": COLLECTIONS[kind],
        "created_at": day.isoformat(),
        # Provisional. Phase 2c reassigns this to somebody actually in the
        # conversation that produces the page, because ownership-plus-presence
        # and standing-in-the-room are different questions and answering them
        # separately is how a postmortem got handed to a person who was not
        # talking to anyone that day.
        "author": author, "author_source": "ownership",
        "workstream": workstream, "occasion": occasion,
        "recurring": title is not None,
        "hint": hint, "covers": covers or {},
        # Recurring pages title themselves from the week's real facts; the rest
        # are named by the model, which is where naming is worth paying for.
        "title": title, "purpose": None,
    }


def stable_jitter(key: str, span: int) -> int:
    """A repeatable 0..span-1 from a string.

    Where the facts leave a genuine choice — two similar releases, one of which
    someone happened to answer — this picks the same way on every run. It is
    variety, not randomness: no clock, no seed, same bytes every time.
    """
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % max(span, 1)


def reply_plan(thread_id: str, kind: str, sender: str, recipients: list[str],
               *, week: dict | None = None, urgent: bool = False,
               partner: str | None = None) -> list[str]:
    """Who answers, in order — and often nobody.

    The first pass gave every thread one or two replies from distinct people,
    which is not what a mailbox looks like. Most announcements are read and not
    answered; a handover is two people going back and forth several times; a
    weekly note gets a reply from whoever it names, if anyone. All of it falls
    out of facts the day already has.
    """
    if not recipients:
        return []
    jitter = stable_jitter(thread_id, 100)

    if kind == "handoff" and partner:
        # Two people arranging a handover actually talk: questions, answers,
        # "one more thing". Alternating, three to five messages.
        turns = 3 + stable_jitter(thread_id, 3)
        return [partner if i % 2 == 0 else sender for i in range(turns)]

    if kind == "release":
        # Most release notes are read, not answered. A hotfix gets a reaction.
        if urgent:
            return recipients[:1 + stable_jitter(thread_id + "u", 2)]
        return recipients[:1] if jitter < 25 else []

    if kind == "weekly-update":
        # Replies come from the people the update is about, and a quiet week
        # gets none at all.
        busiest = [p for p in (week or {}).get("busiest", []) if p in recipients]
        commits = (week or {}).get("commits", 0)
        if urgent:
            return busiest[:2] or recipients[:1]
        if commits >= 60:
            return busiest[:2] if jitter < 70 else busiest[:1]
        if commits >= 20:
            return busiest[:1] if jitter < 55 else []
        return busiest[:1] if jitter < 20 else []

    if kind == "person-joined":
        # People say hello, and more of them on a fuller team.
        return recipients[:min(len(recipients), 1 + stable_jitter(thread_id, 3))]

    return recipients[:1] if jitter < 50 else []


def _thread(thread_id: str, day: dt.date, sender: str, to: list[str], occasion: dict,
            *, hint: str, responders: list[str] | None = None,
            covers: dict | None = None, subject: str | None = None) -> dict:
    """One mail thread. `responders` is who replies, in order, and may be empty."""
    recipients = [p for p in to if p != sender][:10]
    messages = [{"id": f"{thread_id}-m0", "date": day.isoformat(), "from": sender,
                 "to": recipients, "in_reply_to": None}]
    when = day
    for n, responder in enumerate(responders or [], start=1):
        # A reply lands the same day or the next working one; a long thread
        # spreads out rather than arriving in one implausible burst.
        if n > 1 and stable_jitter(f"{thread_id}{n}", 3) == 0:
            when = next_working_day(when)
        while when.weekday() >= 5:
            when += dt.timedelta(days=1)
        prior = messages[-1]
        messages.append({"id": f"{thread_id}-m{n}", "date": when.isoformat(),
                         "from": responder,
                         "to": sorted({prior["from"], *prior["to"]} - {responder}),
                         "in_reply_to": prior["id"]})
    return {"id": thread_id, "occasion": occasion, "hint": hint,
            "recurring": subject is not None, "covers": covers or {},
            "participants": sorted({sender, *recipients}), "messages": messages,
            "subject": subject, "purpose": None}


def _entry_day(entry: dict) -> dt.date | None:
    value = entry.get("date") or ""
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return _month_day(value)


def _month_day(value: str | None) -> dt.date | None:
    """`2025-03` or `2025-03 to 2025-04` -> the first working day of that month."""
    match = re.match(r"(\d{4})-(\d{2})", value or "")
    if not match:
        return None
    day = dt.date(int(match.group(1)), int(match.group(2)), 1)
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)
    return day


def _personas_in(entry: dict, inputs: Inputs) -> list[str]:
    found = []
    text = (entry.get("title", "") or "") + (entry.get("detail", "") or "")
    for real_id, persona in inputs.persona_of.items():
        if real_id and real_id in text:
            found.append(persona)
    return sorted(set(found))


# =============================================================================
# Schemas
# =============================================================================
def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props,
            "required": required if required is not None else list(props),
            "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": {"type": "string"}}

WORKSTREAM_SCHEMA = _obj({
    "name": {**_STR, "description": "What the team would call this push of work, "
                                    "in their words. Six words at most."},
    "summary": {**_STR, "description": "Two sentences: what it was for and how it went."},
    "arc": _obj({
        "problem": {**_STR, "description": "What made this necessary"},
        "approach": _STR,
        "friction": {**_STR, "description": "What actually got in the way, from the "
                                            "evidence — a provider's API, a broken "
                                            "test, a rushed review. '' if none shows."},
        "landing": _STR,
    }),
    "conversation": _obj({
        "at_kickoff": {**_STR, "description": "What gets said when this starts"},
        "mid_flight": {**_STR, "description": "What gets said while it is going"},
        "at_landing": {**_STR, "description": "What gets said as it lands"},
    }),
    "evidence": {**_STRS, "description": "episode ids, months, paths, PR numbers"},
})


def artifacts_schema(doc_ids: list[str], thread_ids: list[str]) -> dict:
    return _obj({
        "docs": {"type": "array", "items": _obj({
            "id": {"type": "string", "enum": doc_ids or ["none"]},
            "title": {**_STR, "description": "As it would appear in the wiki sidebar"},
            "purpose": {**_STR, "description": "One line: what the page is for"},
        })},
        "threads": {"type": "array", "items": _obj({
            "id": {"type": "string", "enum": thread_ids or ["none"]},
            "subject": {**_STR, "description": "The email subject line"},
            "purpose": {**_STR, "description": "One line: why it was sent"},
        })},
    })


# =============================================================================
# Stages
# =============================================================================
BRIEF = """You are describing how a small engineering team actually worked, from the record
of what they did. The company and its people are synthetic; the work is real.

Rules:

* Everything you write is world-facing and will be read by an agent working inside this
  company. Never use a real person's name, a real GitHub login, or the real organization's
  name. Refer to people by the persona ids you are given.
* Read the evidence, do not embellish it. If the record shows a provider's API misbehaving,
  say so; if it shows nothing but a clean landing, say that instead of inventing drama.
* `evidence` cites episode ids (`ep-` + 12 hex), months (YYYY-MM), paths, or PR numbers
  that appear in what you were given.
* Write the way an engineer would name and describe their own work: concrete, unglamorous,
  specific to this codebase.
"""


def stage_system(inputs: Inputs) -> str:
    return BRIEF + "\n\nTHE COMPANY\n" + json.dumps({
        "company": inputs.company["company"]["name"],
        "product": "curator, a Python library for bulk LLM inference and dataset curation",
        "services": [{"slug": s["slug"], "name": s["name"],
                      "description": s["description"][:300],
                      "typical_work": s.get("what_it_does_for_users", "")[:200]}
                     for s in inputs.company["services"]],
        "people": [{"id": p["synthetic"]["id"], "title": p["synthetic"]["title"],
                    "seniority": p["synthetic"]["seniority"]}
                   for p in inputs.company["people"] if p["class"] == "employee"],
        "eras": [{"slug": e["slug"], "name": e["name"], "how_they_worked": e["how_they_worked"]}
                 for e in inputs.grounding["eras"]],
    }, ensure_ascii=False, separators=(",", ":"))


def stage_workstream(llm: rl.LLM, system: str, workstream: dict,
                     service: dict) -> dict:
    packet = {k: workstream[k] for k in
              ("id", "service", "service_name", "first_day", "last_day", "driver",
               "collaborators", "reviewers", "change_types", "lines", "era")}
    packet["episodes"] = [{k: e[k] for k in ("id", "title", "change_type", "merged",
                                             "persona", "pr")}
                          for e in workstream["episodes"][:25]]
    packet["what_work_here_looks_like"] = service.get("what_it_does_for_users", "")
    prompt = (
        "Name and describe one push of work.\n\n"
        "This is a run of related changes on one part of the product, by mostly the same "
        "people, inside one month. Give it the name they would have used, and tell its arc "
        "from the episode titles and types: what it was for, how they went at it, what got "
        "in the way, how it ended.\n\n"
        "`conversation` is the useful part. Say what this work sounds like in a channel at "
        "each stage — not a script, the shape of it: what gets asked, what gets argued "
        "about, what gets announced. A run of six bugfixes on one file sounds nothing like "
        "a feature landing.\n\n"
        "THE WORK\n" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    )
    out = llm.complete(system=system, prompt=prompt, schema=WORKSTREAM_SCHEMA,
                       label=f"ws:{workstream['id']}")
    out["id"] = workstream["id"]
    return out


def stage_artifacts(llm: rl.LLM, system: str, era_slug: str, docs: list[dict],
                    threads: list[dict]) -> dict:
    packet = {
        "docs": [{"id": d["id"], "kind": d["kind"], "date": d["created_at"],
                  "author": d["author"], "why_it_exists": d["hint"],
                  "occasion": d["occasion"]} for d in docs],
        "threads": [{"id": t["id"], "date": t["messages"][0]["date"],
                     "from": t["messages"][0]["from"], "to": t["messages"][0]["to"],
                     "why_it_exists": t["hint"], "occasion": t["occasion"]}
                    for t in threads],
    }
    prompt = (
        f"Title the documents and email this team produced during the {era_slug} era.\n\n"
        "Each one already has a date, an author and a reason it exists. Give it the title "
        "or subject line that person would have typed, and one line saying what it is for. "
        "Titles are what a colleague scanning a wiki sidebar reads, so make them specific: "
        "'Batch resume after a 429' beats 'Design Document'. Subject lines are what lands "
        "in an inbox — short, and about the thing.\n\n"
        "Return every id you were given, exactly once.\n\n"
        "WHAT TO TITLE\n" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    )
    return llm.complete(system=system, prompt=prompt,
                        schema=artifacts_schema([d["id"] for d in docs],
                                                [t["id"] for t in threads]),
                        label=f"artifacts:{era_slug}")


# =============================================================================
# Checks
# =============================================================================
def verify(workstreams: list[dict], artifacts: dict, inputs: Inputs) -> list[str]:
    problems = []
    covered = {e["id"] for w in workstreams for e in w["episodes"]}
    expected = {e["id"] for e in inputs.episodes}
    if covered != expected:
        problems.append(f"{len(expected - covered)} episode(s) belong to no workstream")

    seen: dict[str, str] = {}
    for workstream in workstreams:
        for episode in workstream["episodes"]:
            if episode["id"] in seen and seen[episode["id"]] != workstream["id"]:
                problems.append(f"{episode['id']} is in two workstreams")
            seen[episode["id"]] = workstream["id"]

    known = set(inputs.employees)
    for doc in artifacts["docs"]:
        if doc["author"] not in known:
            problems.append(f"doc {doc['id']}: author {doc['author']!r} is not an employee")
        day = dt.date.fromisoformat(doc["created_at"])
        record = inputs.days.get(doc["created_at"])
        if record:
            state = next((p["state"] for p in record["people"]
                          if p["persona"] == doc["author"]), None)
            if state in ("not-yet-joined", "departed"):
                problems.append(f"doc {doc['id']}: {doc['author']} is {state} on {day}")
    for thread in artifacts["threads"]:
        for message in thread["messages"]:
            if message["from"] not in known:
                problems.append(f"thread {thread['id']}: sender {message['from']!r} "
                                "is not an employee")
            for who in message["to"]:
                if who not in known:
                    problems.append(f"thread {thread['id']}: recipient {who!r} "
                                    "is not an employee")
        dates = [m["date"] for m in thread["messages"]]
        if dates != sorted(dates):
            problems.append(f"thread {thread['id']}: replies precede what they answer")

    known_docs = {d["id"]: d for d in artifacts["docs"]}
    seen_comment: set[str] = set()
    for comment in artifacts.get("comments", []):
        doc = known_docs.get(comment["doc"])
        if doc is None:
            problems.append(f"comment {comment['id']}: no such document")
            continue
        if comment["created_at"] <= doc["created_at"]:
            problems.append(f"comment {comment['id']}: dated {comment['created_at']}, "
                            f"not after the page ({doc['created_at']})")
        if comment["author"] not in known:
            problems.append(f"comment {comment['id']}: author {comment['author']!r} "
                            "is not an employee")
        if comment["reply_to"] and comment["reply_to"] not in seen_comment:
            problems.append(f"comment {comment['id']}: replies to something that "
                            "does not exist yet")
        seen_comment.add(comment["id"])

    # Artifacts obey the same calendar as conversations: inside the span, and on
    # a working day. A design doc dated before the repository existed is the
    # kind of thing nobody notices until an agent reads it.
    first = dt.date.fromisoformat(inputs.timeline["window"]["first"])
    last = dt.date.fromisoformat(inputs.timeline["window"]["last"])
    dated = ([(d["id"], d["created_at"]) for d in artifacts["docs"]]
             + [(c["id"], c["created_at"]) for c in artifacts.get("comments", [])]
             + [(t["id"], m["date"]) for t in artifacts["threads"]
                for m in t["messages"]])
    for item_id, value in dated:
        day = dt.date.fromisoformat(value)
        if not first <= day <= last:
            problems.append(f"{item_id}: dated {day}, outside {first}..{last}")
        elif day.weekday() >= 5:
            problems.append(f"{item_id}: dated {day}, a {day.strftime('%A')}")
    return problems


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--episodes", type=Path, default=DEFAULT_EPISODES)
    parser.add_argument("--grounding", type=Path, default=DEFAULT_GROUNDING)
    parser.add_argument("--company", type=Path, default=DEFAULT_COMPANY)
    parser.add_argument("--timeline", type=Path, default=DEFAULT_TIMELINE)
    parser.add_argument("--out-workstreams", type=Path, default=DEFAULT_WORKSTREAMS)
    parser.add_argument("--out-artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "llm")
    parser.add_argument("--model", default=None,
                        help="override the model (default: sonnet on the CLI backend)")
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--backend", default="auto", choices=["auto", "cli", "sdk"])
    parser.add_argument("--auth", default="auto", choices=["auto", "oauth", "api-key"])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--no-enrich", action="store_true",
                        help="cluster and schedule only; no names, no titles")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    rl.heading("Reading")
    inputs = Inputs(args)
    rl.ok(f"{len(inputs.episodes)} episodes (nested ones already dropped), "
          f"{len(inputs.timeline['days'])} days, {len(inputs.employees)} employees")

    rl.heading("Clustering")
    workstreams = cluster(inputs)
    sizes = sorted(len(w["episodes"]) for w in workstreams)
    rl.ok(f"{len(workstreams)} workstreams — median {sizes[len(sizes) // 2]} episodes, "
          f"largest {sizes[-1]}, {sizes.count(1)} singletons")

    rl.heading("Artifacts")
    artifacts = plan_artifacts(inputs, workstreams)
    kinds = Counter(d["kind"] for d in artifacts["docs"])
    rl.ok(f"{len(artifacts['docs'])} documents ({', '.join(f'{v} {k}' for k, v in kinds.most_common())})")
    rl.ok(f"{len(artifacts['threads'])} mail threads, "
          f"{sum(len(t['messages']) for t in artifacts['threads'])} messages, all internal")
    commented = len({c["doc"] for c in artifacts["comments"]})
    rl.ok(f"{len(artifacts['comments'])} page comments on {commented} of "
          f"{len(artifacts['docs'])} documents "
          f"({commented / max(len(artifacts['docs']), 1):.0%})")
    for skip in artifacts["skipped"]:
        rl.info(f"skipped: {skip}")

    problems = verify(workstreams, artifacts, inputs)
    if problems:
        for problem in problems[:15]:
            rl.warn(problem)
        rl.fail(f"{len(problems)} problem(s); nothing was written")
    rl.ok("every episode in exactly one workstream; every author present on the day")

    if not args.no_enrich:
        llm = rl.LLM(args.cache_dir, model=args.model or rl.MODEL, effort=args.effort,
                     refresh=not args.no_refresh, verbose=args.verbose,
                     auth=args.auth, backend=args.backend)
        system = stage_system(inputs)
        # Four parallel `claude` processes contend for one subscription and
        # start failing outright; the API path has no such limit. Cap the CLI
        # unless the caller insisted on a number.
        workers = args.workers
        if llm.backend == "cli" and "--workers" not in sys.argv:
            workers = min(workers, CLI_WORKERS)
        rl.heading(f"Naming ({llm.backend}, {llm.auth_mode}, {workers} workers)")

        named: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(stage_workstream, llm, system, w,
                                   inputs.services.get(w["service"], {})): w
                       for w in workstreams}
            for future in as_completed(futures):
                w = futures[future]
                try:
                    named[w["id"]] = future.result()
                except Exception as exc:      # noqa: BLE001
                    rl.warn(f"{w['id']}: {exc}")
        for workstream in workstreams:
            workstream.update({k: v for k, v in named.get(workstream["id"], {}).items()
                               if k != "id"})
        rl.ok(f"{len(named)} of {len(workstreams)} workstreams named")

        by_era: dict[str, tuple[list, list]] = defaultdict(lambda: ([], []))
        for doc in artifacts["docs"]:
            by_era[inputs.days.get(doc["created_at"], {}).get("era", {})
                   .get("slug", "unknown")][0].append(doc)
        for thread in artifacts["threads"]:
            by_era[inputs.days.get(thread["messages"][0]["date"], {}).get("era", {})
                   .get("slug", "unknown")][1].append(thread)
        titled = 0
        for era_slug, (docs, threads) in sorted(by_era.items()):
            if not docs and not threads:
                continue
            try:
                out = stage_artifacts(llm, system, era_slug, docs, threads)
            except Exception as exc:          # noqa: BLE001
                rl.warn(f"artifacts:{era_slug}: {exc}")
                continue
            titles = {d["id"]: d for d in out.get("docs", [])}
            subjects = {t["id"]: t for t in out.get("threads", [])}
            for doc in docs:
                got = titles.get(doc["id"])
                if got:
                    doc["title"], doc["purpose"] = got["title"], got["purpose"]
                    titled += 1
            for thread in threads:
                got = subjects.get(thread["id"])
                if got:
                    thread["subject"], thread["purpose"] = got["subject"], got["purpose"]
                    titled += 1
        rl.ok(f"{titled} of {len(artifacts['docs']) + len(artifacts['threads'])} "
              "artifacts titled")

        untitled = [d["id"] for d in artifacts["docs"] if not d["title"]]
        untitled += [t["id"] for t in artifacts["threads"] if not t["subject"]]
        if untitled:
            rl.warn(f"{len(untitled)} artifact(s) have no title: "
                    f"{', '.join(untitled[:5])}")
        usage = {**llm.stats, "auth_mode": llm.auth_mode, "backend": llm.backend,
                 "api_equivalent_usd": round(llm.cost(), 2)}
        rl.info(f"{llm.stats['calls']} calls, {llm.stats['cache_hits']} from cache "
                f"({llm.backend}/{llm.auth_mode})")
    else:
        usage = {"calls": 0, "note": "--no-enrich: clustered and scheduled only"}

    meta = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": rl.now_iso(),
        "generator": "data_gen/phase2_workstreams.py",
        "usage": usage,
    }
    size_w = rl.write_json(args.out_workstreams, {
        **meta,
        "method": f"episodes clustered into bursts of work on one service, split at "
                  f"month boundaries with a {BURST_GAP_DAYS}-day gap; named by a model",
        "counts": {"workstreams": len(workstreams),
                   "episodes": sum(len(w["episodes"]) for w in workstreams)},
        "workstreams": workstreams,
    })
    size_a = rl.write_json(args.out_artifacts, {
        **meta,
        "method": "every document and mail thread the real record gives a reason for; "
                  "dates, authors and recipients derived, titles written by a model",
        "collections": sorted(set(COLLECTIONS.values())),
        "counts": {"docs": len(artifacts["docs"]), "threads": len(artifacts["threads"]),
                   "messages": sum(len(t["messages"]) for t in artifacts["threads"]),
                   "comments": len(artifacts["comments"])},
        "docs": artifacts["docs"], "threads": artifacts["threads"],
        "comments": artifacts["comments"], "skipped": artifacts["skipped"],
    })
    rl.heading("Wrote")
    rl.ok(f"{args.out_workstreams} ({rl.human_bytes(size_w)})")
    rl.ok(f"{args.out_artifacts} ({rl.human_bytes(size_a)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
