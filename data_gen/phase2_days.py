#!/usr/bin/env python3
"""Phase 2c — what the project knew each day, and what got said about it.

Two files a day. The **state** is the project as it stood that morning: what had
shipped, what was open, who was in, which documents existed. The **specs** are
what those people would have talked about, one per channel that had anything to
talk about.

Three things shape the output more than anything else.

**One call per day, not per channel.** The channels on a day are related — an
incident in the morning is why the service channel is quiet in the afternoon —
and a single call sees that where ten separate ones cannot.

**Conversation is a weekday activity.** People pushed on Saturdays; they did not
hold design discussions on Saturdays. Weekend work surfaces on Monday, in
`since_last_working_day`, which is also how it happens in a real team. The
exception is an incident, which is two days in the whole window.

**Documents and mail are outcomes, not decoration.** The artifact calendar fixed
their dates in Phase 2b, so a day knows exactly what is due today and everything
written before today. A goal that produces a document carries it as `writes`; a
conversation leaning on an older one carries it as `reads`. Nothing can cite a
page nobody has written yet.

Writes `build/days/state/YYYY-MM-DD.json` and `build/days/specs/YYYY-MM-DD.json`.
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

SCHEMA_VERSION = 1

DEFAULT_TIMELINE = rl.DEFAULT_BUILD_DIR / "timeline.json"
DEFAULT_WORKSTREAMS = rl.DEFAULT_BUILD_DIR / "workstreams.json"
DEFAULT_ARTIFACTS = rl.DEFAULT_BUILD_DIR / "artifacts.json"
DEFAULT_COMPANY = rl.DEFAULT_BUILD_DIR / "company_grounding.json"
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "days"

# Only two people in a room make a conversation.
MIN_SPEAKERS = 2
# How far back a channel still counts as having something to say about work that
# has not landed yet.
OPEN_PR_STALE_DAYS = 2
# Everyone is in these; they do not need a subsystem to justify a slot.
SOCIAL_CADENCE_DAYS = {0: "general", 3: "random"}   # Monday, Thursday

CLI_WORKERS = 2


# =============================================================================
# Inputs
# =============================================================================
def load(path: Path, what: str) -> dict:
    if not path.exists():
        rl.fail(f"{path} does not exist — {what}")
    return json.loads(path.read_text(encoding="utf-8"))


def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", (text or "").lower())}


class World:
    """Everything the day stage reads, joined."""

    def __init__(self, args):
        self.timeline = load(args.timeline, "run phase2_timeline.py first")
        self.workstreams = load(args.workstreams, "run phase2_workstreams.py first")
        self.artifacts = load(args.artifacts, "run phase2_workstreams.py first")
        self.company = load(args.company, "run phase1_company_grounding.py first")

        self.days = {d["date"]: d for d in self.timeline["days"]}
        self.channels = {c["name"]: c for c in self.company["channels"]}
        self.people = {p["synthetic"]["id"]: p for p in self.company["people"]}
        self.employees = [p["synthetic"]["id"] for p in self.company["people"]
                          if p["class"] == "employee"]
        self.services = {s["slug"]: s for s in self.company["services"]}
        self.service_channel = self._route_services()

        self.ws_by_day: dict[str, list[dict]] = defaultdict(list)
        for workstream in self.workstreams["workstreams"]:
            for day in workstream["days_live"]:
                self.ws_by_day[day].append(workstream)

        self.docs_by_day: dict[str, list[dict]] = defaultdict(list)
        for doc in self.artifacts["docs"]:
            self.docs_by_day[doc["created_at"]].append(doc)
        self.mail_by_day: dict[str, list[dict]] = defaultdict(list)
        for thread in self.artifacts["threads"]:
            for message in thread["messages"]:
                self.mail_by_day[message["date"]].append({"thread": thread,
                                                          "message": message})

    def _route_services(self) -> dict[str, str]:
        """service -> the channel that talks about it.

        Derived rather than declared: each service is scored against every
        service-shaped channel by how much vocabulary they share, and falls back
        to the team-wide channel when nothing matches well. Hardcoding this
        table would tie the whole stage to one repository's component names.
        """
        rooms = [c for c in self.company["channels"] if c.get("kind") == "service"]
        team = next((c["name"] for c in self.company["channels"]
                     if c.get("kind") == "team"), "engineering")
        room_words = {c["name"]: tokens(f"{c['display_name']} {c['purpose']} "
                                        f"{c.get('header', '')} "
                                        f"{' '.join(c.get('evidence') or [])}")
                      for c in rooms}
        out = {}
        for slug, service in self.services.items():
            words = tokens(f"{slug} {service['name']} {service['description']}")
            best, score = team, 1
            for name, room in room_words.items():
                overlap = len(words & room)
                if overlap > score:
                    best, score = name, overlap
            out[slug] = best
        return out

    def channel_of(self, service: str) -> str:
        return self.service_channel.get(service, "engineering")


# =============================================================================
# Which days get a conversation
# =============================================================================
def is_spec_day(day: dict) -> tuple[bool, str]:
    """Weekdays with something in them, plus a genuine weekend incident.

    Not faithful to the commit log on purpose: 39 of the 177 active days in the
    rich window are weekends, because this team pushed on Saturdays. They did
    not hold discussions on Saturdays, and a workspace where a tenth of the talk
    happens at the weekend reads wrong on sight.
    """
    activity = day["activity"]
    has_work = bool(activity["commits"] or activity["prs_opened"]
                    or activity["reviews"] or activity["releases"]
                    or activity["issues_opened"])
    if day["is_weekend"]:
        if activity["incident"]:
            return True, "weekend incident"
        return False, ""
    if has_work:
        return True, "working day with activity"
    return False, ""


def since_last_working_day(world: World, day: dict) -> dict:
    """What landed while nobody was talking.

    A Saturday fix gets discussed on Monday, usually by someone asking who
    merged it. Without this the weekend simply vanishes from the record.
    """
    date = dt.date.fromisoformat(day["date"])
    gathered = {"days": [], "commits": [], "merged": [], "releases": [],
                "incidents": []}
    back = date - dt.timedelta(days=1)
    while True:
        record = world.days.get(back.isoformat())
        if record is None:
            break
        spec, _ = is_spec_day(record)
        if spec:
            break
        activity = record["activity"]
        if (activity["commits"] or activity["prs_merged"] or activity["releases"]):
            gathered["days"].append(record["date"])
            gathered["commits"] += [
                {"sha": c["world_sha"] or c["sha"], "persona": c["persona"],
                 "subject": c["subject"]} for c in activity["commits"][:10]]
            gathered["merged"] += activity["prs_merged"]
            gathered["releases"] += activity["releases"]
            if activity["incident"]:
                gathered["incidents"].append(record["date"])
        back -= dt.timedelta(days=1)
        if (date - back).days > 5:
            break
    gathered["days"].reverse()
    return gathered


# =============================================================================
# Which channels have something to say
# =============================================================================
def channel_candidates(world: World, day: dict, carried: dict) -> list[dict]:
    """Deterministic slots. The model writes only the ones it can fill."""
    activity = day["activity"]
    date = dt.date.fromisoformat(day["date"])
    present = {p["persona"] for p in day["people"] if p["state"] == "present"}
    slots: dict[str, dict] = {}

    def add(name: str, why: str, **extra):
        if name not in world.channels:
            return
        slot = slots.setdefault(name, {"channel": name, "reasons": [], **extra})
        slot["reasons"].append(why)
        for key, value in extra.items():
            if isinstance(value, list):
                slot.setdefault(key, [])
                slot[key] = list({*slot[key], *value})

    if activity["commits"] or activity["prs_merged"] or carried["commits"]:
        add("engineering", f"{len(activity['commits'])} commits, "
                           f"{len(activity['prs_merged'])} merged")

    if activity["prs_opened"] or activity["reviews"]:
        add("code-review", f"{len(activity['prs_opened'])} opened, "
                           f"{len(activity['reviews'])} reviewed")
    stale = [pr for pr in day["project_state"]["open_prs"]
             if (date - dt.date.fromisoformat(pr["opened"])).days >= OPEN_PR_STALE_DAYS]
    if stale:
        # Only worth nagging about in an era where a two-day-old PR was unusual.
        median = (day.get("regime") or {}).get("median_merge_h")
        if median and (date - dt.date.fromisoformat(stale[0]["opened"])).days * 24 > median:
            add("code-review", f"{len(stale)} PR(s) older than the era's median merge",
                stale_prs=[p["number"] for p in stale[:6]])

    if activity["releases"] or carried["releases"]:
        tags = [r["tag"] for r in activity["releases"]] + \
               [r["tag"] for r in carried["releases"]]
        add("releases", f"shipped {', '.join(t for t in tags if t)}", tags=tags)
    if any(re.search(r"bump|release", c["subject"] or "", re.I)
           for c in activity["commits"]):
        add("releases", "a version bump landed")

    if activity["incident"] or carried["incidents"]:
        add("incidents", (activity["incident"] or {}).get("kind", "over the weekend"))

    bugfixes = [e for e in activity["episodes"] if e["change_type"] == "bugfix"]
    if len(bugfixes) >= 2:
        add("help", f"{len(bugfixes)} bugfixes landing")

    touched = Counter(s for c in activity["commits"] for s in c["services"])
    for service, count in touched.most_common(4):
        add(world.channel_of(service), f"{count} change(s) to {service}",
            services=[service])

    for day_index, name in SOCIAL_CADENCE_DAYS.items():
        if date.weekday() == day_index:
            add(name, "the usual weekly traffic")

    # A channel needs two people in it who were actually at work — and the
    # people who speak have to be the ones with a reason to.
    out = []
    for slot in slots.values():
        channel = world.channels[slot["channel"]]
        roster = set(channel["members"])
        here = sorted(roster & present)
        if len(here) < MIN_SPEAKERS:
            continue
        slot["members_present"] = here
        slot["eligible"] = eligible_speakers(world, day, slot, channel, here)
        if len(slot["eligible"]) < MIN_SPEAKERS:
            continue
        out.append(slot)
    return sorted(out, key=lambda s: s["channel"])


def eligible_speakers(world: World, day: dict, slot: dict, channel: dict,
                      here: list[str]) -> list[dict]:
    """Who has standing to speak in this room today, and why.

    Presence and membership are not enough. A conversation about the batch
    processor should be between the people who own it and the people who touched
    it that day — not whoever happened to be online. Each entry carries the
    reason, both so the model can weigh who leads and so a reader can check the
    cast afterwards.

    The general-purpose rooms are the exception: `#general` and `#random` belong
    to everyone, and gating them by ownership would be its own kind of wrong.
    """
    activity = day["activity"]
    services = set(slot.get("services") or [])
    reasons: dict[str, list[str]] = defaultdict(list)

    if channel["kind"] in ("company", "social"):
        for who in here:
            reasons[who].append("in this channel")
        return [{"id": w, "why": "; ".join(reasons[w])} for w in here]

    # Did the work today, in this room's area.
    for commit in activity["commits"]:
        if commit["persona"] in here and (not services
                                          or services & set(commit["services"])):
            reasons[commit["persona"]].append("committed to this today")
    for review in activity["reviews"]:
        if review["persona"] in here:
            reasons[review["persona"]].append("reviewed today")
    for pr in activity["prs_opened"] + activity["prs_merged"]:
        if pr["persona"] in here:
            reasons[pr["persona"]].append(f"opened or merged #{pr['number']}")
    for who in slot.get("stale_prs") and [
            p["persona"] for p in day["project_state"]["open_prs"]
            if p["number"] in slot["stale_prs"]] or []:
        if who in here:
            reasons[who].append("has a pull request waiting")

    # Owns the ground being discussed.
    for persona_id in here:
        persona = world.people.get(persona_id)
        if not persona:
            continue
        owned = {s["slug"] for s in persona["services_owned"]}
        if services & owned:
            reasons[persona_id].append(
                f"owns {', '.join(sorted(services & owned))}")
        elif not services and any(world.channel_of(s) == slot["channel"]
                                  for s in owned):
            reasons[persona_id].append("owns work in this area")

    # Driving something live here.
    for workstream in world.ws_by_day.get(day["date"], []):
        if services and workstream["service"] not in services:
            continue
        if workstream["driver"] in here:
            reasons[workstream["driver"]].append(
                f"driving {workstream.get('name') or workstream['id']}")
        for who in workstream["collaborators"]:
            if who in here:
                reasons[who].append("working on it")

    # A practice room with nobody named yet falls back to the people who own
    # the relevant discipline, so #releases is not empty on a quiet release day.
    if len(reasons) < MIN_SPEAKERS:
        for persona_id in here:
            reasons.setdefault(persona_id, ["in this channel"])

    ranked = sorted(reasons.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return [{"id": who, "why": "; ".join(dict.fromkeys(why))} for who, why in ranked]


# =============================================================================
# The day packet
# =============================================================================
def artifact_ledger(world: World, date: dt.date) -> dict:
    """What exists to be read, and what is due to be written today."""
    due_docs = world.docs_by_day.get(date.isoformat(), [])
    due_mail = world.mail_by_day.get(date.isoformat(), [])
    existing = [d for d in world.artifacts["docs"]
                if d["created_at"] < date.isoformat()]
    return {
        "due_today": {
            "docs": [{"id": d["id"], "kind": d["kind"], "title": d["title"],
                      "author": d["author"], "purpose": d["purpose"],
                      "covers": d["covers"]} for d in due_docs],
            "mail": [{"thread": m["thread"]["id"],
                      "subject": m["thread"]["subject"] or m["thread"]["hint"],
                      "from": m["message"]["from"], "to": m["message"]["to"],
                      "reply": bool(m["message"]["in_reply_to"])}
                     for m in due_mail],
        },
        "already_written": [{"id": d["id"], "kind": d["kind"], "title": d["title"],
                             "author": d["author"], "on": d["created_at"]}
                            for d in existing[-8:]],
        "written_total": len(existing),
    }


def day_packet(world: World, day: dict) -> dict:
    date = dt.date.fromisoformat(day["date"])
    carried = since_last_working_day(world, day)
    candidates = channel_candidates(world, day, carried)
    live = world.ws_by_day.get(day["date"], [])
    recent = [w for w in world.workstreams["workstreams"]
              if w["first_day"] <= day["date"] <= w["last_day"]]

    people = []
    for record in day["people"]:
        persona = world.people.get(record["persona"])
        if not persona:
            continue
        who = record["persona"]
        if record["state"] != "present":
            # Absent, departed or not yet joined. They cannot speak, so the day
            # needs to know they are away and nothing else.
            # Same keys as anyone else, zeroed. A record that is missing fields
            # depending on who it describes is a record every consumer has to
            # branch on, and the state writer duly crashed on the first one.
            people.append({
                "id": who, "state": record["state"], "reason": record["reason"],
                "title": persona["synthetic"]["title"],
                "seniority": persona["synthetic"]["seniority"],
                "owns": [s["slug"] for s in persona["services_owned"][:3]],
                "did_today": {"commits": 0, "reviews": 0, "comments": 0},
                "driving": [], "helping_with": [], "recently_landed": [],
                "blocked_on": [], "writing_today": [],
                "channels": [c["name"] for c in world.company["channels"]
                             if who in c["members"]],
            })
            continue
        driving = [{"id": w["id"], "name": w.get("name") or w["id"],
                    "stage": _stage_of(w, day["date"])}
                   for w in (live or recent) if w["driver"] == who]
        helping = [w.get("name") or w["id"] for w in (live or recent)
                   if who in w["collaborators"]]
        # Landed in the last fortnight, so it is still worth mentioning.
        landed = [w.get("name") or w["id"] for w in world.workstreams["workstreams"]
                  if w["driver"] == who and w["last_day"] < day["date"]
                  and (date - dt.date.fromisoformat(w["last_day"])).days <= 14]
        # Their own pull requests sitting longer than this era found normal.
        median = (day.get("regime") or {}).get("median_merge_h") or 24
        waiting = [{"number": pr["number"], "title": pr["title"],
                    "days": (date - dt.date.fromisoformat(pr["opened"])).days}
                   for pr in day["project_state"]["open_prs"]
                   if pr["persona"] == who
                   and (date - dt.date.fromisoformat(pr["opened"])).days * 24 > median]
        people.append({
            "id": who,
            "title": persona["synthetic"]["title"],
            "seniority": persona["synthetic"]["seniority"],
            "state": record["state"],
            "reason": record["reason"],
            "did_today": {"commits": record["commits"], "reviews": record["reviews"],
                          "comments": record["comments"]},
            "owns": [s["slug"] for s in persona["services_owned"][:3]],
            "driving": driving,
            "helping_with": helping[:3],
            "recently_landed": landed[:3],
            "blocked_on": waiting[:3],
            "writing_today": [d["id"] for d in
                              world.docs_by_day.get(day["date"], [])
                              if d["author"] == who],
            # No `voice` here on purpose. A spec says what has to get through the
            # day, not how anyone phrases it — that is the conversation
            # generator's job, and it reads the voice blocks straight from
            # company_grounding.json. Carrying nine voice fields for twelve
            # people cost 19,000 characters of every prompt and changed nothing
            # about the agenda that came back.
            "channels": [c["name"] for c in world.company["channels"]
                         if who in c["members"]],
        })

    return {
        "date": day["date"],
        "weekday": day["weekday"],
        "era": day["era"],
        "regime": day["regime"],
        "activity": {
            "commits": [{"sha": c["world_sha"] or c["sha"], "persona": c["persona"],
                         "subject": c["subject"], "services": c["services"]}
                        for c in day["activity"]["commits"][:12]],
            "episodes": day["activity"]["episodes"][:10],
            "prs_opened": day["activity"]["prs_opened"],
            "prs_merged": day["activity"]["prs_merged"],
            "issues_opened": day["activity"]["issues_opened"],
            "reviews": day["activity"]["reviews"][:12],
            "releases": day["activity"]["releases"],
            "incident": day["activity"]["incident"],
        },
        "since_last_working_day": carried,
        "project_state": {
            "version": day["project_state"]["version"],
            "open_prs": day["project_state"]["open_prs"][:12],
            "open_issues": day["project_state"]["open_issues"][:10],
            "tree": day["project_state"]["tree"],
        },
        # The arc (problem/approach/friction/landing) lives in workstreams.json
        # for whoever needs the whole story. A day needs to know what this thread
        # of work sounds like *today*, which is one line.
        "workstreams_live": [{"id": w["id"], "name": w.get("name"),
                              "service": w["service"], "driver": w["driver"],
                              "stage": _stage_of(w, day["date"]),
                              "sounds_like": (w.get("conversation") or {}).get(
                                  {"kickoff": "at_kickoff", "landing": "at_landing"}
                                  .get(_stage_of(w, day["date"]), "mid_flight"), "")}
                             for w in (live or recent)[:5]],
        "artifacts": artifact_ledger(world, date),
        # Not for the model — the attach pass uses it to hand an orphaned
        # document to somebody who owns the ground it is about.
        "_owners": {s["slug"]: s.get("owners") or []
                    for s in world.company["services"]},
        "channels": [{**slot,
                      "purpose": world.channels[slot["channel"]]["purpose"],
                      "kind": world.channels[slot["channel"]]["kind"]}
                     for slot in candidates],
        "people": people,
    }


def _stage_of(workstream: dict, date: str) -> str:
    if date == workstream["first_day"]:
        return "kickoff"
    if date == workstream["last_day"]:
        return "landing"
    return "mid-flight"


# =============================================================================
# The shape the render stage expects
# =============================================================================
# Channel kinds map onto the roles the spec schema uses, and each role carries
# the norms that say what belongs in that room and what does not. Written once
# here rather than by the model, because they are a property of the channel and
# do not change from day to day.
ROLE_OF_KIND = {"company": "announce", "social": "social", "team": "team",
                "practice": "cross_cutting", "service": "team"}

NORMS = {
    "team": {
        "belongs_here": "day to day work on the services this channel owns: design "
                        "debate, code review, blockers between the people who own "
                        "them, and progress on the current phase.",
        "not_here": "a production incident happening right now, which goes to the "
                    "cross-cutting channel, and company-wide news, which goes to "
                    "the announce channel.",
    },
    "cross_cutting": {
        "belongs_here": "the practice itself: what is broken now, what is waiting "
                        "on review, what is shipping, and who is picking it up.",
        "not_here": "routine work on one service, which belongs in the team "
                    "channel that owns it.",
    },
    "announce": {
        "belongs_here": "news the whole company needs: releases that matter to "
                        "everyone, scheduling, people joining or moving on, and "
                        "decisions that cross every team.",
        "not_here": "work on any individual service, and anything only one team "
                    "cares about.",
    },
    "social": {
        "belongs_here": "no work purpose at all.",
        "not_here": "anything anyone is expected to act on.",
    },
}


def role_of(channel: dict) -> str:
    return ROLE_OF_KIND.get(channel.get("kind"), "team")


# =============================================================================
# Schema
# =============================================================================
def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props,
            "required": required if required is not None else list(props),
            "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": {"type": "string"}}


def specs_schema(slots: list[dict], doc_ids: list[str], mail_ids: list[str]) -> dict:
    """The day's specs, with the cast narrowed to people who have standing somewhere.

    Two shapes were tried before this one. An enum of everyone *present* let the
    model seat anyone anywhere, and on a weaker model roughly half the days came
    back with someone in a channel they were not a member of. Keying the object
    by channel would make each cast a closed per-room enum and the violation
    impossible — but it duplicates the whole spec body once per room, and the API
    rejects the result outright: "the compiled grammar is too large".

    So the enum is the union of every channel's eligible list: someone with no
    standing in any room today cannot be named at all, which removes most of the
    error, and the per-room rule is left to the verifier and its retry. Cheaper
    than a call per channel and it actually compiles.
    """
    cast = sorted({e["id"] for slot in slots for e in slot["eligible"]}) or ["none"]
    artifact_ref = _obj({
        "kind": {"type": "string", "enum": ["doc", "mail"]},
        "id": {"type": "string", "enum": (doc_ids + mail_ids) or ["none"]},
    })
    return _obj({"specs": {"type": "array", "items": _obj({
        "channel": {"type": "string",
                    "enum": [s["channel"] for s in slots] or ["none"]},
        "purpose": {**_STR, "description": "Three words: what this is for"},
        "purpose_class": {"type": "string",
                          "enum": ["deliberation", "status", "troubleshooting",
                                   "coordination", "social", "announcement"]},
        "participants": {"type": "array", "items": _obj({
            "id": {"type": "string", "enum": cast},
            "why": {**_STR, "description": "from this channel's `eligible` list"},
            "brings": {**_STR, "description": "what they know that the others need"},
            "wants": {**_STR, "description": "what they are after; may be nothing"},
        })},
        "agenda": {**_STRS, "description": "Two to five items, in order. The shape "
                                           "of the day, not a programme."},
        "subjects": {**_STRS, "description": "For a social or announce room only"},
        "event_ids": {**_STRS, "description": "episode or workstream ids, from the "
                                              "packet"},
        "max_turns": {"type": "integer", "description": "6-20"},
        "reason": {**_STR, "description": "why they are talking, one line"},
        "goals": {"type": "array", "items": _obj({
            "goal": {**_STR, "description": "what it settles, or fails to. Three a "
                                            "room at most."},
            "owner": {"type": "string", "enum": cast},
            "agenda_item": {**_STR, "description": "which agenda item this covers"},
            "beats": {**_STRS, "description": "At most 3. Who raises it, who pushes "
                                              "back, where it lands. Not a script."},
            "reads": {"type": "array", "items": artifact_ref,
                      "description": "only artifacts already written"},
            "writes": {"type": "array", "items": artifact_ref,
                       "description": "only artifacts due today"},
        })},
        "expected_outcome": _STR,
    })}})


# =============================================================================
# Stage
# =============================================================================
BRIEF = """You are planning one day of conversation inside a small software company. The
people are synthetic; everything they are reacting to is real — real commits, real pull
requests, real releases, on the day they actually happened.

You are not writing the messages. You are writing the spec a later step renders: who talks,
about what, in what order, and where it ends up.

Rules:

* Only use the facts in the packet. Every commit, PR, release and person is given to you.
  Do not invent a bug, a decision, a meeting or a system that is not there.
* A channel gets a spec only if it genuinely has something to say that day. Returning
  fewer channels than you were offered is the normal case, not a failure.
* Each channel's cast is fixed: you may only name people that channel's schema allows, and
  each carries a reason — they committed to it today, they own it, they are driving the
  work, their pull request is waiting. Copy that reason into `why`.
* Return only the channels that genuinely have something to say. Omitting most of what you
  were offered is the normal case.
* Weight the exchange by standing. The owner or driver leads; someone who reviewed once
  chips in. Do not give everyone equal airtime.
* Each participant carries `brings` (what they know that the others need) and `wants` (what
  they are after — which may be nothing; plenty of people are just answering).
* `agenda` is what has to get through: two to five items, in order. Each `goal` names the
  `agenda_item` it covers and the `owner` pushing it. A person's own `driving`,
  `blocked_on` and `writing_today` in the packet are what they would raise.
* A spec is the day's **overall goals**, not a transcript. At most three goals a channel,
  at most three beats a goal, and a beat is the shape of the exchange — who raises it, who
  pushes back, where it lands — not the words anyone uses.
* Not every conversation resolves. Real ones trail off, get deferred, or end with someone
  saying they will look tomorrow.
* `writes` may only name an artifact from today's due list. `reads` may only name one
  already written. Never refer to a document that does not exist yet.
"""


def stage_system(world: World) -> str:
    return BRIEF + "\n\nTHE COMPANY\n" + json.dumps({
        "company": world.company["company"]["name"],
        "product": "curator, a Python library for bulk LLM inference and dataset curation",
        "channels": [{"name": c["name"], "kind": c["kind"], "purpose": c["purpose"],
                      "members": c["members"]} for c in world.company["channels"]],
        "services": [{"slug": s["slug"], "name": s["name"],
                      "what_work_looks_like": s.get("what_it_does_for_users", "")[:200]}
                     for s in world.company["services"]],
    }, ensure_ascii=False, separators=(",", ":"))


class Unfixable(RuntimeError):
    """The day kept breaking a rule the verifier can state precisely."""


def stage_day(llm: rl.LLM, system: str, packet: dict, world: "World",
              attempts: int = 5) -> dict:
    """Plan one day, and make the model fix its own violations.

    The rules the verifier enforces — only people with standing may speak, only
    channels that were offered, only artifacts that exist — are all stated
    precisely enough to hand back. A weaker model breaks them occasionally
    rather than systematically, so a corrective retry is much cheaper than a
    stronger model on every call: it pays only for the days that go wrong.

    Each retry is a different prompt and so a different cache key, which keeps
    replays free and records both attempts under `cache/llm/`.
    """
    problems: list[str] = []
    for attempt in range(attempts):
        out = _ask_day(llm, system, packet, problems, attempt)
        for note in sanitize(packet, out):
            rl.info(f"{packet['date']}: {note}")
        problems = verify(world, packet, out)
        if not problems:
            return out
        rl.warn(f"{packet['date']}: {len(problems)} problem(s), asking for a fix")
    raise Unfixable(f"{packet['date']}: still failing after {attempts} attempts:\n    "
                    + "\n    ".join(problems[:6]))


def _ask_day(llm: rl.LLM, system: str, packet: dict, problems: list[str],
             attempt: int) -> dict:
    doc_ids = [d["id"] for d in packet["artifacts"]["due_today"]["docs"]]
    doc_ids += [d["id"] for d in packet["artifacts"]["already_written"]]
    mail_ids = [m["thread"] for m in packet["artifacts"]["due_today"]["mail"]]
    prompt = (
        f"Plan {packet['date']} ({packet['weekday']}).\n\n"
        "The channels below each have a reason they might carry something today. Write a "
        "spec for the ones that really do and skip the rest — a quiet day with one busy "
        "channel is a normal day.\n\n"
        "Where the packet gives a workstream a `conversation` shape for its stage, use it: "
        "that is what this thread of work sounds like when it is starting, running or "
        "landing.\n\n"
        + ("Work landed while nobody was talking — see `since_last_working_day`. Someone "
           "usually notices on the next working morning.\n\n"
           if packet["since_last_working_day"]["days"] else "")
        + "TODAY\n" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    )
    if problems:
        prompt += ("\n\nYOUR PREVIOUS ANSWER WAS REJECTED\n"
                   "Rewrite the whole day, keeping what was fine and fixing only "
                   "what is listed. Every one of these is a hard rule, not a "
                   "preference.\n\n" + "\n".join(problems[:10]))
    return llm.complete(system=system, prompt=prompt,
                        schema=specs_schema(packet["channels"], doc_ids, mail_ids),
                        label=f"day:{packet['date']}"
                              + (f"#fix{attempt}" if problems else ""),
                        max_tokens=16000)


# =============================================================================
# Output
# =============================================================================
def dress_spec(world: World, day: dict, packet: dict, spec: dict) -> dict:
    """Wrap what the model wrote in everything that can be derived.

    The model decides who talks and what about. Everything else — the channel's
    role and norms, which artifacts are referenced and whether they exist yet,
    who owns this ground but is away, what must not be mentioned because it does
    not exist on this date — is a fact, and asking for facts is how you get
    invented ones.
    """
    channel = world.channels[spec["channel"]]
    role = role_of(channel)
    slot = next((c for c in packet["channels"] if c["channel"] == spec["channel"]), {})
    speaking = {p["id"] for p in spec["participants"]}
    services = set(slot.get("services") or [])

    # Owners of this ground who were not at work, and whether someone covered.
    absent_owners = []
    for person in packet["people"]:
        if person["state"] not in ("absent", "not-yet-joined", "departed"):
            continue
        if services & set(person["owns"]):
            absent_owners.append({"id": person["id"], "state": person["state"],
                                  "reason": person["reason"]})

    referenced = []
    due = packet["artifacts"]["due_today"]
    written = {d["id"]: d for d in packet["artifacts"]["already_written"]}
    for goal in spec.get("goals", []):
        for ref in (goal.get("writes") or []):
            item = next((d for d in due["docs"] if d["id"] == ref["id"]), None)
            referenced.append({"kind": ref["kind"], "id": ref["id"],
                               "title": (item or {}).get("title"),
                               "status": "planned"})
        for ref in (goal.get("reads") or []):
            item = written.get(ref["id"])
            referenced.append({"kind": ref["kind"], "id": ref["id"],
                               "title": (item or {}).get("title"),
                               "status": "written"})

    meetings = []
    for doc in due["docs"]:
        if doc["kind"] == "meeting-notes" and role in ("team", "cross_cutting"):
            meetings.append({"name": "Weekly sync", "channel": spec["channel"]})
            break

    forbidden = day.get("forbidden", {})
    return {
        "date": day["date"],
        "channel": spec["channel"],
        "channel_name": f"#{spec['channel']}",
        "role": role,
        "purpose": spec["purpose"],
        "purpose_class": spec["purpose_class"],
        "norms": NORMS[role],
        "event_ids": spec.get("event_ids", []),
        "subjects": spec.get("subjects", []),
        "referenced_objects": referenced,
        "meetings": meetings,
        "max_turns": spec["max_turns"],
        "must_not_mention": {
            "entity_count": forbidden.get("entity_count", 0),
            "services": forbidden.get("services_not_started", []),
            "prs_above": max([p["number"] for p in day["activity"]["prs_opened"]]
                             or [0]),
        },
        "participants": [{"id": p["id"],
                          "label": world.people[p["id"]]["synthetic"]["display_name"],
                          "why": p["why"], "brings": p["brings"], "wants": p["wants"]}
                         for p in spec["participants"] if p["id"] in world.people],
        "absent_owners": absent_owners,
        "stand_in": bool(absent_owners) and bool(speaking),
        "agenda": spec.get("agenda", []),
        "reason": spec["reason"],
        "goals": spec.get("goals", []),
        "expected_outcome": spec["expected_outcome"],
    }


def person_state(world: World, day: dict, packet: dict, person: dict,
                 specs: list[dict]) -> dict:
    """One person's standing on the day, in the shape the render stage wants.

    `knows` and `unaware_of` are the useful pair: a conversation can only draw on
    what its speakers have actually seen. Both are derived — the services that
    existed by today, the pull requests and issues this person opened or
    reviewed, and the channels they are simply not in.
    """
    speaking = sorted(spec["channel"] for spec in specs
                      if person["id"] in [q["id"] for q in spec["participants"]])
    activity = day["activity"]
    prs = sorted({f"#{pr['number']}" for pr in
                  activity["prs_opened"] + activity["prs_merged"]
                  if pr["persona"] == person["id"]}
                 | {f"#{r['pr']}" for r in activity["reviews"]
                    if r["persona"] == person["id"]})
    issues = sorted({f"#{i['number']}" for i in activity["issues_opened"]
                     if i["persona"] == person["id"]})
    in_channels = set(person["channels"])
    working_on = (person["driving"][0]["name"] if person["driving"]
                  else (f"helping on {person['helping_with'][0]}"
                        if person["helping_with"] else "nothing scheduled"))
    return {
        "id": person["id"],
        "label": world.people[person["id"]]["synthetic"]["display_name"],
        "seniority": person["seniority"],
        "title": person["title"],
        "available": person["state"] == "present",
        "state": person["state"],
        "reason": person["reason"],
        "working_on": working_on,
        "driving": [d["id"] for d in person["driving"]],
        "blocked_on": [f"#{b['number']} waiting {b['days']}d" for b in person["blocked_on"]],
        "recently_completed": person["recently_landed"],
        "writing_today": person["writing_today"],
        "did_today": person["did_today"],
        "channels": sorted(in_channels),
        "speaking_in": speaking,
        "knows": {
            "services": day.get("speakable", {}).get("services", []),
            "owns": person["owns"],
            "prs": prs,
            "issues": issues,
        },
        "unaware_of": {
            "services": day.get("forbidden", {}).get("services_not_started", []),
            "channels": sorted({c["name"] for c in world.company["channels"]}
                               - in_channels),
        },
    }


def state_file(world: World, day: dict, packet: dict) -> dict:
    date = dt.date.fromisoformat(day["date"])
    return {
        "schema_version": SCHEMA_VERSION,
        "date": day["date"],
        "weekday": day["weekday"],
        "day_index": day["day_index"],
        "phase_id": day["era"]["slug"],
        "is_weekend": day["is_weekend"],
        "regime": day["regime"],
        "project_state": day["project_state"],
        "created_today": {
            "commits": [{"sha": c["world_sha"] or c["sha"], "persona": c["persona"],
                         "subject": c["subject"]} for c in day["activity"]["commits"]],
            "merged_prs": day["activity"]["prs_merged"],
            "issues": day["activity"]["issues_opened"],
            "releases": day["activity"]["releases"],
            "docs": packet["artifacts"]["due_today"]["docs"],
            "emails": packet["artifacts"]["due_today"]["mail"],
            "incident": day["activity"]["incident"],
        },
        "since_last_working_day": packet["since_last_working_day"],
        "open_now": {"prs": day["project_state"]["open_prs"],
                     "issues": day["project_state"]["open_issues"]},
        "workstreams_live": packet["workstreams_live"],
        "artifacts_written_to_date": packet["artifacts"]["written_total"],
        "people": [{k: p[k] for k in ("id", "state", "reason", "did_today", "owns")}
                   for p in packet["people"]],
        "briefing": briefing(day, packet),
    }


def briefing(day: dict, packet: dict) -> str:
    a = day["activity"]
    lines = [f"{day['date']}  {day['weekday']}  {day['era']['slug']}", ""]
    lines.append(f"Version {day['project_state']['version'] or '(none yet)'}, "
                 f"{len(day['project_state']['open_prs'])} PRs open, "
                 f"{len(day['project_state']['open_issues'])} issues open")
    if a["commits"]:
        lines.append(f"Today: {len(a['commits'])} commits, "
                     f"{len(a['prs_merged'])} merged, {len(a['reviews'])} reviews")
    if a["releases"]:
        lines.append("Shipped: " + ", ".join(r["tag"] for r in a["releases"] if r["tag"]))
    if a["incident"]:
        lines.append(f"Incident: {a['incident']['kind']} — "
                     f"{'; '.join(a['incident']['evidence'][:2])}")
    carried = packet["since_last_working_day"]
    if carried["days"]:
        lines.append(f"Landed since the last working day ({', '.join(carried['days'])}): "
                     f"{len(carried['commits'])} commits")
    live = [w["name"] or w["id"] for w in packet["workstreams_live"]]
    if live:
        lines.append("In flight: " + ", ".join(live[:4]))
    due = packet["artifacts"]["due_today"]
    if due["docs"]:
        lines.append("Documents due: " + ", ".join(d["title"] or d["id"]
                                                   for d in due["docs"]))
    if due["mail"]:
        lines.append("Mail due: " + ", ".join(m["subject"] or m["thread"]
                                              for m in due["mail"]))
    away = [p["id"] for p in packet["people"] if p["state"] == "absent"]
    if away:
        lines.append("Away: " + ", ".join(away))
    return "\n".join(lines)


# =============================================================================
# Checks
# =============================================================================
def sanitize(packet: dict, specs: dict) -> list[str]:
    """Drop speakers who do not belong, rather than asking again.

    The cast enum is the union of everyone eligible *somewhere* that day, because
    a per-channel enum makes the compiled grammar too large. So the model can
    still put someone in a room they are not a member of — and when it does, it
    does so repeatedly: one day spent five attempts insisting on the same wrong
    person and never corrected it.

    Asking is the wrong tool here. Which people may speak in a room is a fact the
    packet already states, so the fix is arithmetic: drop them, drop any goal
    they owned, and say so. What is left is a conversation the model chose in the
    right room about the right work, minus someone who could not have been there.
    """
    allowed = {c["channel"]: {e["id"] for e in c["eligible"]}
               for c in packet["channels"]}
    notes = []
    for spec in specs.get("specs", []):
        cast = allowed.get(spec["channel"], set())
        keep = [p for p in spec["participants"] if p["id"] in cast]
        dropped = [p["id"] for p in spec["participants"] if p["id"] not in cast]
        if dropped:
            notes.append(f"#{spec['channel']}: dropped {', '.join(dropped)} — "
                         "no standing in that room")
            spec["participants"] = keep
        speaking = {p["id"] for p in spec["participants"]}
        goals = [g for g in spec.get("goals", []) if g.get("owner") in speaking]
        if len(goals) != len(spec.get("goals", [])):
            notes.append(f"#{spec['channel']}: dropped "
                         f"{len(spec.get('goals', [])) - len(goals)} goal(s) whose "
                         "owner is no longer in the conversation")
            spec["goals"] = goals
    # A room that lost too many people is not a conversation any more.
    before = len(specs.get("specs", []))
    specs["specs"] = [s for s in specs.get("specs", [])
                      if len(s["participants"]) >= MIN_SPEAKERS and s.get("goals")]
    if len(specs["specs"]) != before:
        notes.append(f"dropped {before - len(specs['specs'])} channel(s) left with "
                     f"fewer than {MIN_SPEAKERS} speakers")
    return notes


# Where a quiet day's paperwork gets posted. Not everything belongs in
# #engineering: a release note announced there and a postmortem filed there
# read like the channels do not mean anything.
ROOM_FOR = {
    "release-notes": "releases", "postmortem": "incidents",
    "onboarding": "general", "meeting-notes": "engineering",
    "planning": "engineering", "handover": "engineering",
    "design": "engineering", "runbook": "engineering",
}


def workroom_for_orphans(world: "World", date: str, due: list[tuple],
                         people: list[dict]) -> dict | None:
    """A day file for a date that owes artifacts and has no conversation.

    Thirteen artifacts were dated on days phase 2 chose not to generate specs
    for — a holiday, a quiet Monday — and so had no producer, no obligation and
    no way of ever being written. One of them carried a clue, which is how a
    requirement went missing from the corpus with nothing anywhere saying so.

    The answer is not to move the date. A person who owes a write-up on a quiet
    day still writes it; they just do not hold a stand-up about it first. So
    the day gets a small room whose whole business is producing what is owed:
    the author, a short thread, and a goal per artifact. It reads as somebody
    posting what they finished rather than a meeting that never happened.
    """
    if not due:
        return None
    known = {p["id"] for p in people}
    specs = []
    for kind, item_id, author, label, channel in due:
        if author not in known:
            continue
        others = [p for p in people if p["id"] != author][:2]
        verb = "write up" if kind == "doc" else "send"
        specs.append({
            "date": date, "channel": channel,
            "channel_name": f"#{channel}",
            "purpose_class": "housekeeping",
            "purpose": f"{author} posts {label}, which is due today",
            "reason": "the calendar owes this artifact today and nothing else "
                      "is happening; without a room for it, nobody is ever "
                      "asked to produce it",
            "expected_outcome": f"{label} exists and is linked here",
            "agenda": [label], "subjects": [label],
            "participants": [
                {"id": author, "label": author, "why": "owes this today",
                 "brings": f"the {kind} itself", "wants": f"{label} posted"}
            ] + [{"id": o["id"], "label": o["id"], "why": "in this channel",
                  "brings": "", "wants": ""} for o in others],
            "goals": [{"goal": f"{verb} {label}", "owner": author,
                       "agenda_item": label,
                       "beats": [f"{author} says they will {verb} {label}"],
                       "reads": [], "writes": [{"kind": kind, "id": item_id}],
                       "added_by": "workroom"}],
            "meetings": [], "event_ids": [], "referenced_objects": [],
            "must_not_mention": [], "absent_owners": [], "stand_in": None,
            "norms": [], "role": "the quiet day's paperwork",
            # Small on purpose. This is a person posting what they finished,
            # not a meeting; a long thread here would invent a working day out
            # of one that the calendar says was quiet.
            "max_turns": 6,
        })
    if not specs:
        return None
    return {"schema_version": SCHEMA_VERSION, "date": date,
            "weekday": dt.date.fromisoformat(date).strftime("%A"),
            "phase_id": "phase2_days.workroom", "people": people,
            "specs": specs}


def attach_artifacts(packet: dict, specs: dict,
                     world: "World" = None) -> list[str]:
    """Bind today's documents and mail to the conversation that produced them.

    Runs as a post-pass over written specs, never inside the generation loop.
    Putting it in the loop changed the text of the retry prompts, which changed
    their cache keys, which made ninety-eight already-paid-for days uncacheable
    on the next replay — a free re-run turned into a re-generation.

    Idempotent: an artifact already claimed by some goal is skipped, so running
    it twice attaches nothing twice.

    The prompt offers `writes` but nothing makes the model use it, and it mostly
    did not: 61 of 109 documents were due on a day that had conversations and
    yet no goal claimed to write any of them. A document nobody discussed still
    renders — it has a date, an author and a purpose — but it is unanchored, and
    the whole point of planning artifacts alongside conversations is that one
    produces the other.

    Nothing here needs a model. Who wrote a document and when are facts from the
    artifact calendar, and where its author was talking that day is a fact from
    the specs. So: attach it to a goal that person is already pushing, and only
    invent a goal when they have none — using the document's own title and
    purpose, which Phase 2b already wrote.
    """
    # Undo the last run before doing this one. Without it the pass is only
    # idempotent in the sense that it refuses to act twice — which is not the
    # same thing, and left the specs claiming artifacts whose authors had been
    # reset underneath them.
    for spec in specs.get("specs", []):
        spec["goals"] = [g for g in spec.get("goals", [])
                         if g.get("added_by") != "attach"]
        for goal in spec["goals"]:
            taken = set(goal.pop("attached", []))
            if taken:
                goal["writes"] = [w for w in (goal.get("writes") or [])
                                  if w["id"] not in taken]

    notes = []
    due_docs = packet["artifacts"]["due_today"]["docs"]
    due_mail = packet["artifacts"]["due_today"]["mail"]
    # `artifact_ledger` builds fresh dicts for the prompt, so reassigning an
    # author on one of those changed a copy and nothing else: ten reassignments
    # were logged and none of them reached artifacts.json. Resolve the id back
    # to the record the calendar actually holds.
    real_doc, real_msg = {}, {}
    if world is not None:
        real_doc = {d["id"]: d for d in world.artifacts["docs"]}
        for thread in world.artifacts["threads"]:
            for message in thread["messages"]:
                real_msg[thread["id"]] = message
                break

    def claimed(kind: str) -> set[str]:
        return {w["id"] for spec in specs.get("specs", [])
                for g in spec.get("goals", []) for w in (g.get("writes") or [])
                if w["kind"] == kind}

    already: dict[str, int] = defaultdict(int)

    def rooms_for(author: str) -> list[dict]:
        """Conversations today where this person is speaking, most on-topic first."""
        out = [spec for spec in specs.get("specs", [])
               if author in {p["id"] for p in spec["participants"]}]
        return sorted(out, key=lambda spec: -len(spec.get("goals", [])))

    def reassign(item: dict, kind: str, wanted: str) -> tuple[str, dict] | None:
        """Who in a conversation today could have written this.

        The calendar's author is a suggestion made from ownership, and ownership
        is not the same as being in the room. Prefer them when they are speaking;
        otherwise hand it to someone who is, favouring an owner of the area the
        document is about, then whoever is already pushing a goal there.
        """
        rooms = rooms_for(wanted)
        if rooms:
            return wanted, rooms[0]
        service = (item.get("occasion") or {}).get("service")
        best = None
        for spec in specs.get("specs", []):
            for person in spec["participants"]:
                owner = person["id"] in (packet["_owners"].get(service) or [])
                pushing = any(g.get("owner") == person["id"]
                              for g in spec.get("goals", []))
                # `already` spreads the fallback. Ranking on conversation count
                # alone handed all ten reassignments to one person, who simply
                # happened to be in the most rooms that month.
                rank = (0 if owner else 1, 0 if pushing else 1,
                        already[person["id"]], -len(spec.get("goals", [])))
                if best is None or rank < best[0]:
                    best = (rank, person["id"], spec)
        if best:
            already[best[1]] += 1
        return (best[1], best[2]) if best else None

    for item, kind, author, label, why in (
            [(d, "doc", d["author"], d["title"] or d["id"], d.get("purpose") or "")
             for d in due_docs]
            + [(m, "mail", m["from"], m["subject"] or m["thread"], "")
               for m in due_mail]):
        item_id = item["id"] if kind == "doc" else item["thread"]
        if item_id in claimed(kind):
            continue
        picked = reassign(item, kind, author)
        if picked is None:
            # Nobody is in a conversation today, so no goal can claim this and
            # phase 4 will never ask for it. That used to be a bare `continue`:
            # thirteen artifacts were dropped here without a word, and the
            # clues planted in one of them went missing from the corpus with
            # nothing anywhere saying so. It happens because two different
            # definitions of "a day with conversations" disagree — the artifact
            # calendar asks the timeline, and this asks which days actually got
            # a spec, which is a subset.
            notes.append(f"{item_id}: UNCLAIMED — nobody is in a conversation "
                         f"on {packet['date']}, so nothing can produce it")
            continue
        if picked[0] != author:
            notes.append(f"{item_id}: reassigned from {author} to {picked[0]}, who is "
                         "actually in the conversation that produces it")
            field = "author" if kind == "doc" else "from"
            item[field] = picked[0]
            record = (real_doc if kind == "doc" else real_msg).get(item_id)
            if record is not None:
                record[field] = picked[0]
                record["author_source"] = "conversation"
                record["reassigned_from"] = author
        author, spec = picked
        mine = [g for g in spec.get("goals", []) if g.get("owner") == author]
        if mine:
            mine[0].setdefault("writes", []).append({"kind": kind, "id": item_id})
            mine[0].setdefault("attached", []).append(item_id)
            notes.append(f"#{spec['channel']}: {author}'s goal now writes {item_id}")
        else:
            spec.setdefault("goals", []).append({
                "goal": (f"write up {label}" if kind == "doc"
                         else f"send {label}"),
                "owner": author,
                "agenda_item": label,
                # Deliberately thin. This is a fact being recorded, not a
                # conversation being invented; the render stage has the
                # document's own purpose to write from.
                "beats": [f"{author} says they will {'write' if kind == 'doc' else 'send'} "
                          f"{label}" + (f" — {why}" if why else "")],
                "reads": [], "writes": [{"kind": kind, "id": item_id}],
                "added_by": "attach",
            })
            spec.setdefault("agenda", []).append(label)
            notes.append(f"#{spec['channel']}: added a goal for {author} to "
                         f"produce {item_id}")
    return notes


def verify(world: World, packet: dict, specs: dict) -> list[str]:
    problems = []
    date = packet["date"]
    present = {p["id"] for p in packet["people"] if p["state"] == "present"}
    offered = {c["channel"] for c in packet["channels"]}
    due_docs = {d["id"] for d in packet["artifacts"]["due_today"]["docs"]}
    due_mail = {m["thread"] for m in packet["artifacts"]["due_today"]["mail"]}
    written = {d["id"] for d in packet["artifacts"]["already_written"]}

    eligible_by_channel = {c["channel"]: {e["id"] for e in c["eligible"]}
                           for c in packet["channels"]}
    for spec in specs.get("specs", []):
        name = spec["channel"]
        if name not in offered:
            problems.append(f"{date}: {name} was not offered today")
        roster = set(world.channels.get(name, {}).get("members", []))
        allowed = eligible_by_channel.get(name, set())
        speakers = [p["id"] for p in spec["participants"]]
        for who in speakers:
            if who not in present:
                problems.append(f"{date}/{name}: {who} is not present")
            elif who not in roster:
                problems.append(f"{date}/{name}: {who} is not in the channel")
            elif who not in allowed:
                problems.append(f"{date}/{name}: {who} has no standing here — "
                                "not an owner, not working on it, not waiting on it")
        if len(speakers) < MIN_SPEAKERS:
            problems.append(f"{date}/{name}: fewer than {MIN_SPEAKERS} speakers")
        agenda = spec.get("agenda") or []
        if not agenda:
            problems.append(f"{date}/{name}: no agenda")
        for goal in spec.get("goals", []):
            if goal.get("owner") and goal["owner"] not in speakers:
                problems.append(f"{date}/{name}: goal owned by {goal['owner']}, "
                                "who is not in the conversation")
        for goal in spec.get("goals", []):
            for ref in goal.get("writes") or []:
                if ref["kind"] == "comment":
                    # A page comment is derived from the plan at run time by
                    # date and author, never stored in a spec, so it is not in
                    # either due pool. Checked against `due_mail` it read as
                    # "not due today" and failed the day.
                    continue
                pool = due_docs if ref["kind"] == "doc" else due_mail
                if ref["id"] not in pool:
                    problems.append(f"{date}/{name}: writes {ref['id']}, "
                                    "which is not due today")
            for ref in goal.get("reads") or []:
                if ref["kind"] == "doc" and ref["id"] not in written | due_docs:
                    problems.append(f"{date}/{name}: reads {ref['id']}, "
                                    "which does not exist yet")
    return problems


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--timeline", type=Path, default=DEFAULT_TIMELINE)
    parser.add_argument("--workstreams", type=Path, default=DEFAULT_WORKSTREAMS)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--company", type=Path, default=DEFAULT_COMPANY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "llm")
    parser.add_argument("--from", dest="date_from", default=None)
    parser.add_argument("--until", dest="date_until", default=None)
    parser.add_argument("--only", nargs="*", default=None, metavar="DATE")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default="medium",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--backend", default="auto", choices=["auto", "cli", "sdk"])
    parser.add_argument("--auth", default="auto", choices=["auto", "oauth", "api-key"])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--no-enrich", action="store_true",
                        help="write the state files only; no conversations")
    parser.add_argument("--attach-only", action="store_true",
                        help="bind artifacts to existing specs and exit; no model")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    rl.heading("Reading")
    world = World(args)
    rl.ok(f"{len(world.days)} days, "
          f"{len(world.workstreams['workstreams'])} workstreams, "
          f"{len(world.artifacts['docs'])} documents, "
          f"{len(world.artifacts['threads'])} mail threads")
    routed = Counter(world.service_channel.values())
    rl.info("services route to: " + ", ".join(f"{k} x{v}" for k, v in routed.most_common()))

    chosen = []
    for day in world.timeline["days"]:
        spec, why = is_spec_day(day)
        if not spec:
            continue
        if args.only and day["date"] not in args.only:
            continue
        if args.date_from and day["date"] < args.date_from:
            continue
        if args.date_until and day["date"] > args.date_until:
            continue
        chosen.append((day, why))
    if args.limit:
        chosen = chosen[:args.limit]

    weekend = sum(1 for d, _ in chosen if d["is_weekend"])
    rl.heading("Days")
    rl.ok(f"{len(chosen)} conversation days — {weekend} at a weekend "
          f"({weekend / max(len(chosen), 1):.0%}), all of those incidents")

    state_dir, specs_dir = args.out / "state", args.out / "specs"
    state_dir.mkdir(parents=True, exist_ok=True)
    specs_dir.mkdir(parents=True, exist_ok=True)

    packets = {day["date"]: day_packet(world, day) for day, _ in chosen}
    slots = sum(len(p["channels"]) for p in packets.values())
    rl.ok(f"{slots} channel slots offered, "
          f"{slots / max(len(chosen), 1):.1f} per day on average")
    rl.info("busiest channels: " + ", ".join(
        f"{k} x{v}" for k, v in Counter(
            c["channel"] for p in packets.values() for c in p["channels"]
        ).most_common(6)))

    for date, packet in packets.items():
        day = world.days[date]
        rl.write_json(state_dir / f"{date}.json", state_file(world, day, packet))
    rl.ok(f"{len(packets)} state files -> {state_dir}")

    if args.attach_only:
        rl.heading("Binding artifacts to the conversations that produce them")
        touched, added = 0, 0
        reassigned: list[str] = []
        for date, packet in sorted(packets.items()):
            path = specs_dir / f"{date}.json"
            if not path.exists():
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            notes = attach_artifacts(packet, doc, world)
            if not notes:
                continue
            problems = verify(world, packet, doc)
            if problems:
                rl.warn(f"{date}: attachment would break it — {problems[0]}")
                continue
            rl.write_json(path, doc)
            touched += 1
            added += len(notes)
            reassigned.extend(n for n in notes if "reassigned" in n)
            if args.verbose:
                for note in notes:
                    rl.info(f"{date}: {note}")
        rl.ok(f"{added} artifact(s) bound across {touched} day(s)")

        # Reconcile: whoever's goal produces a document is its author. The
        # calendar's guess came from ownership, the conversation decides, and
        # any disagreement between the two is the conversation being right.
        # Doing this as a sweep rather than inside the attach means it also
        # repairs bindings made by earlier runs.
        docs = {d["id"]: d for d in world.artifacts["docs"]}
        threads = {t["id"]: t for t in world.artifacts["threads"]}
        fixed = 0
        # One artifact, one producer. Two conversations both claiming to write
        # the same page is not a document with two authors, it is a bug: the
        # sweep below would attribute it to whichever it saw last, and four
        # documents ended up disagreeing with the goal that wrote them.
        seen_claims: dict[str, str] = {}
        duplicates = 0
        for date in sorted(packets):
            path = specs_dir / f"{date}.json"
            if not path.exists():
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            changed = False
            for spec in doc["specs"]:
                for goal in spec.get("goals", []):
                    owner = goal.get("owner")
                    if not owner:
                        continue
                    keep = []
                    for ref in (goal.get("writes") or []):
                        where = f"{date}/{spec['channel']}"
                        if ref["id"] in seen_claims:
                            duplicates += 1
                            changed = True
                            continue        # an earlier conversation already produces it
                        seen_claims[ref["id"]] = where
                        keep.append(ref)
                    if len(keep) != len(goal.get("writes") or []):
                        goal["writes"] = keep
                    for ref in keep:
                        if ref["kind"] == "doc":
                            record = docs.get(ref["id"])
                            field = "author"
                        else:
                            record = threads.get(ref["id"])
                            field = None
                        if record is None:
                            continue
                        if field and record.get(field) != owner:
                            record["reassigned_from"] = record[field]
                            record[field] = owner
                            record["author_source"] = "conversation"
                            fixed += 1
                        if field is None:
                            first = record["messages"][0]
                            if first["from"] != owner:
                                record["reassigned_from"] = first["from"]
                                first["from"] = owner
                                record["author_source"] = "conversation"
                                fixed += 1
            if changed:
                rl.write_json(path, doc)
        if fixed:
            rl.ok(f"{fixed} artifact(s) reattributed to the person whose goal "
                  "produces them")
        if duplicates:
            rl.ok(f"{duplicates} duplicate claim(s) dropped — one artifact, one "
                  "producer")
        # The resolved authors go back to the calendar, or the render stage
        # would still write the page under the provisional name.
        rl.write_json(args.artifacts, world.artifacts)
        rl.ok(f"{args.artifacts} updated with the resolved authors")
        return 0

    if args.no_enrich:
        return 0

    llm = rl.LLM(args.cache_dir, model=args.model or rl.MODEL, effort=args.effort,
                 refresh=not args.no_refresh, verbose=args.verbose,
                 auth=args.auth, backend=args.backend)
    workers = args.workers
    if llm.backend == "cli" and "--workers" not in sys.argv:
        workers = min(workers, CLI_WORKERS)
    rl.heading(f"Conversations ({llm.backend}, {llm.auth_mode}, {workers} workers)")

    system = stage_system(world)
    written, problems, failed = 0, [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(stage_day, llm, system, packet, world): date
                   for date, packet in packets.items()}
        for future in as_completed(futures):
            date = futures[future]
            try:
                specs = future.result()
            except Exception as exc:            # noqa: BLE001
                failed.append(date)
                rl.warn(f"{date}: {exc}")
                continue
            day = world.days[date]
            rl.write_json(specs_dir / f"{date}.json", {
                "schema_version": SCHEMA_VERSION,
                "date": date,
                "weekday": day["weekday"],
                "phase_id": day["era"]["slug"],
                "specs": [dress_spec(world, day, packets[date], spec)
                          for spec in specs.get("specs", [])],
                "people": [person_state(world, day, packets[date], p,
                                        specs.get("specs", []))
                           for p in packets[date]["people"]],
            })
            written += 1

    rl.ok(f"{written} spec files -> {specs_dir}")
    if failed:
        rl.warn(f"{len(failed)} day(s) could not be made consistent: "
                f"{', '.join(failed[:6])}")
    # Anything written got there by passing `verify`, because the retry loop will
    # not return a day that does not. A clean run is therefore a real guarantee
    # rather than a count of problems nobody acted on.
    rl.ok(f"all {written} days verified: every speaker present and with standing, "
          "every artifact cited after it was written")
    rl.info(f"{llm.stats['calls']} calls, {llm.stats['cache_hits']} from cache "
            f"({llm.backend}/{llm.auth_mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
