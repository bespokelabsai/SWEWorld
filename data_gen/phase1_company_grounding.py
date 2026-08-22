#!/usr/bin/env python3
"""Phase 1 — the synthetic company, read off the real one.

`analyze_repository.py` answers what the codebase is and how the organization
around it actually worked. This turns that record into a company the world can
be populated with: a name, a roster, who owns which service, how each person
writes, and the chat channels such a team would actually have.

Nobody here is invented. Every employee is one real contributor seen through a
new name: their seniority comes from their commit share and who reviewed them,
their services from the subsystems they own, their voice from how they actually
wrote commits and reviews. A person the evidence cannot support is not promoted
into one — the roster is exactly as large as the history says it was.

Writes `build/company_grounding.json`, and projects the two files the world's
schemas say this step owns: `data/identities.yaml` and `data/channels.yaml`.

The one thing that must never happen is a real name reaching the world. Every
real identifier is confined to the `real` and `identity_map` blocks, which exist
so Phase 1.5 can map git authors; everything the agent will ever see is scanned
for leaks before it is written, and a single hit fails the run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

SCHEMA_VERSION = 1

DEFAULT_GROUNDING = rl.DEFAULT_BUILD_DIR / "engineering_grounding.json"
DEFAULT_HISTORY = rl.DEFAULT_BUILD_DIR / "repository_history.json"
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "company_grounding.json"
DEFAULT_DATA_DIR = rl.REPO_ROOT / "data"

# The persona id rule from data/schemas/identities.md. Ingestion enforces it, so
# generating an id that fails it turns into an error four scripts downstream.
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")

# Names that are already taken by a service, and would either collide or be
# quietly rejected at account-creation time.
RESERVED_IDS = frozenset({
    # Gitea routes
    "admin", "api", "assets", "attachments", "avatar", "avatars", "captcha",
    "commits", "debug", "error", "explore", "favicon", "ghost", "help", "install",
    "issues", "login", "logout", "manifest", "metrics", "milestones", "new",
    "notifications", "org", "pulls", "raw", "repo", "search", "signup", "swagger",
    "user", "users", "v2", "well-known",
    # Mattermost
    "all", "channel", "here", "matterbot", "system", "system-bot", "town-square",
    # ours
    "worldadmin", "worldsvc", "deploy", "ubuntu", "gitea", "root",
})

# Channels Mattermost makes itself when the team is created. Listing them is a
# no-op per data/schemas/messages.md, but naming one is a wasted slot.
BUILTIN_CHANNELS = frozenset({"town-square", "off-topic"})

# Seven to ten. Fewer than seven and the workspace has nowhere for the ordinary
# traffic to go; more than ten and every channel is too quiet to hold a
# conversation, which matters because conversations are what gets generated into
# these next.
MIN_CHANNELS, MAX_CHANNELS = 7, 10


# =============================================================================
# Loading
# =============================================================================
def load_json(path: Path, what: str) -> dict:
    if not path.exists():
        rl.fail(f"{path} does not exist.\n"
                f"  {what}\n\n"
                "    GITHUB_TOKEN=... python3 data_gen/extract_repository_history.py\n"
                "    python3 data_gen/build_episodes.py\n"
                "    data_gen/.venv/bin/python data_gen/analyze_repository.py\n")
    return json.loads(path.read_text(encoding="utf-8"))


def sha16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# =============================================================================
# The roster
# =============================================================================
# Three classes, and the distinction is not cosmetic. Employees are the company:
# they get a full persona, a voice, services, and a seat in chat. Associates are
# the drive-by open-source contributors — real commits, so they need a real
# author identity, but a private company has no such people and putting them in
# the workspace would be the tell. The service account is what automation
# committed as.
EMPLOYEE, ASSOCIATE, SERVICE = "employee", "associate", "service_account"


def build_roster(grounding: dict, history: dict) -> list[dict]:
    """One record per real identity, with everything measured about them.

    Every identity that ever authored or committed anything must appear, or
    Phase 1.5 has an author it cannot map and has to fail. That is a larger set
    than the grounding roster: `analyze_repository.py` profiles the people it
    could say something about, while `extract_repository_history.py` sees every
    signature in the object database.
    """
    roster_of = {}
    for tier, ids in grounding["people"]["roster"].items():
        for pid in ids:
            roster_of[pid] = tier

    profiles = {p["id"]: p for p in grounding["people"]["profiles"]}
    roles = {r["person"]: r for r in grounding["roles"]}
    measured = {c["id"]: c for c in grounding["contributors"]}
    seen_in_history = {c["id"]: c for c in history["contributors"]}

    people: list[dict] = []
    for pid in sorted(set(measured) | set(seen_in_history)):
        hist = seen_in_history.get(pid, {})
        meas = measured.get(pid, {})
        profile = profiles.get(pid, {})
        tier = roster_of.get(pid)

        is_bot = hist.get("is_bot", meas.get("is_bot", False))
        # `github` is the signature GitHub itself writes on web-UI merges, and
        # `dependabot[bot]` never had a seat either. Both are automation as far
        # as this company is concerned, whatever the bot heuristic said.
        if is_bot or pid in ("github",) or tier == "bots":
            klass = SERVICE
        elif tier == "core":
            klass = EMPLOYEE
        else:
            klass = ASSOCIATE

        names = sorted({*hist.get("names", []), *meas.get("aliases", []),
                        hist.get("display_name", ""), meas.get("display_name", "")} - {""})
        emails = sorted({*hist.get("emails", []), *meas.get("emails", [])})

        people.append({
            "id": pid,
            "display_name": meas.get("display_name") or hist.get("display_name") or pid,
            "class": klass,
            "tier": tier or ("bots" if klass == SERVICE else "occasional"),
            "names": names,
            "emails": emails,
            "github_login": hist.get("github_login") or meas.get("github_login"),
            "commits": meas.get("commits", 0),
            "first_commit": meas.get("first_commit"),
            "last_commit": meas.get("last_commit"),
            "active_months": meas.get("active_months", 0),
            "status": profile.get("status", "drive-by"),
            "subsystems": meas.get("subsystems", {}),
            "work_types": meas.get("work_types", {}),
            "file_roles": meas.get("file_roles", {}),
            "role": roles.get(pid),
            "profile": profile,
        })

    # Highest-commit first, tie-broken on id. Every downstream prompt is built by
    # walking this list, so an unstable order would change cache keys on a run
    # that produced identical evidence.
    people.sort(key=lambda p: (-p["commits"], p["id"]))
    return people


def persona_groups(people: list[dict]) -> list[dict]:
    """Group real identities into the personas the world will actually have.

    Almost always one-to-one. The exception is automation: three real signatures
    (`devin-ai`, `dependabot[bot]`, `GitHub` — the last is what GitHub itself
    writes on web-UI merges) are one thing here, commits that a machine made.
    Collapsing them keeps the roster honest; the company has staff and it has
    automation, not three robots with distinct personalities.

    A group still carries every identity it absorbed, because Phase 1.5 has to
    map each real (name, email) signature to an author and cannot guess.
    """
    groups: list[dict] = []
    service: list[dict] = []
    for person in people:
        if person["class"] == SERVICE:
            service.append(person)
        else:
            groups.append({"primary": person, "members": [person]})
    if service:
        # Whichever automation account the analysis actually profiled leads, so
        # the persona is written from evidence rather than from an empty record.
        service.sort(key=lambda p: (not p["profile"], -p["commits"], p["id"]))
        groups.append({"primary": service[0], "members": service})
    groups.sort(key=lambda g: (-g["primary"]["commits"], g["primary"]["id"]))
    return groups


def one_service_account(groups: list[dict]) -> str:
    accounts = [g["primary"]["id"] for g in groups
                if g["primary"]["class"] == SERVICE]
    return accounts[0] if accounts else ""


# =============================================================================
# login -> persona
# =============================================================================
# The forge data is keyed entirely by GitHub login; everything else is keyed by
# person id; and only the handful of contributors who used a
# `NNN+login@users.noreply.github.com` address carry the join. Phase 1.5 cannot
# attribute a single issue without this map, so it is built here, once, with its
# evidence recorded.
BOT_LOGIN_RE = re.compile(r"\[bot\]$|^devin-ai|^dependabot|^github-actions", re.I)


def forge_logins(history: dict) -> dict[str, int]:
    """Every login that authored anything, with how much it authored."""
    counts: Counter[str] = Counter()

    def add(obj) -> None:
        if isinstance(obj, dict) and obj.get("login"):
            counts[obj["login"]] += 1

    gh = history["github"]
    for item in gh["pulls"] + gh["issues"] + gh["releases"]:
        add(item.get("user") or item.get("author"))
        add(item.get("merged_by"))
        for who in (item.get("assignees") or []):
            add(who)
        for who in (item.get("requested_reviewers") or []):
            add(who)
    for key in ("reviews", "review_comments", "comments"):
        for items in gh[key].values():
            for item in items:
                add(item.get("user"))
    return dict(counts)


def resolve_logins(history: dict, people: list[dict], groups: list[dict]) -> dict:
    """Map all 83 forge logins onto the roster, in three tiers.

    Roster logins join on hard evidence. Bot logins fold into the service
    account. The long tail — sixty-odd outside contributors with one to five
    interactions each — are reassigned rather than dropped: they exist because
    curator is public, and inside a private company they cannot, but their
    issues carry real engineering conversation and their numbers are load-bearing
    (1,734 commit subjects cite `(#N)`).
    """
    by_id = {p["id"]: p for p in people}
    employees = [p for p in people if p["class"] == EMPLOYEE]
    service = one_service_account(groups)

    resolved: dict[str, str] = {}
    evidence: dict[str, str] = {}

    # 1. The login is recorded on the identity already.
    for person in people:
        if person["github_login"]:
            resolved[person["github_login"]] = person["id"]
            evidence[person["github_login"]] = f"github_login on identity {person['id']}"

    counts = forge_logins(history)

    # 2. Email local part equals the login. Case-insensitive: GitHub logins are
    #    case-preserving but case-insensitive, and people type them both ways.
    by_local: dict[str, str] = {}
    for person in people:
        for email in person["emails"]:
            local = email.split("@", 1)[0].lower()
            local = re.sub(r"^\d+\+", "", local)
            by_local.setdefault(local, person["id"])
    for login in counts:
        if login in resolved:
            continue
        hit = by_local.get(login.lower())
        if hit:
            resolved[login] = hit
            evidence[login] = f"email local part matches login ({hit})"

    # 3. The login is the display name with the spaces taken out — `RyanMarten`
    #    for `Ryan Marten`. Run every known spelling of every name through the
    #    same alias table `repolib` uses, so a login that only aliases.yaml knows
    #    about (`vutrung96` -> `trung vu`) joins here too.
    squashed: dict[str, str] = {}
    for person in people:
        for name in [*person["names"], person["display_name"]]:
            for form in {name, rl.NAME_ALIASES.get(name.lower(), name)}:
                key = re.sub(r"[^a-z0-9]", "", form.lower())
                if len(key) >= 5:
                    squashed.setdefault(key, person["id"])
    for login in counts:
        if login in resolved:
            continue
        canonical = rl.NAME_ALIASES.get(login.lower(), login)
        key = re.sub(r"[^a-z0-9]", "", canonical.lower())
        hit = squashed.get(key)
        if hit:
            resolved[login] = hit
            evidence[login] = f"login is the name of {hit} with the spaces removed"

    # 4. The login is a prefix of an email local part, or the other way round —
    #    `saharshbarve` against `saharshbarve3@`. Long enough to be a name and
    #    unambiguous, or it is a coincidence and gets left alone.
    for login in counts:
        if login in resolved or len(login) < 6:
            continue
        hits = {pid for local, pid in by_local.items()
                if local.startswith(login.lower()) or login.lower().startswith(local)}
        if len(hits) == 1:
            hit, = hits
            resolved[login] = hit
            evidence[login] = f"login is the leading part of {hit}'s email address"

    # 5. Co-occurrence: whoever wrote the commits on a login's pull requests is
    #    that login. Not unanimity — a real pull request picks up merge commits
    #    from main and the odd co-author, and demanding a clean sweep threw away
    #    the three highest-volume accounts on the project. A clear plurality over
    #    a meaningful number of commits is the actual signal.
    pull_author = {p["number"]: (p.get("user") or {}).get("login")
                   for p in history["github"]["pulls"]}
    authors_of_pr: dict[str, Counter] = defaultdict(Counter)
    commit_person = {c["sha"]: c["author"]["person"] for c in history["commits"]}
    for number, commits in history["github"]["pull_commits"].items():
        login = pull_author.get(int(number))
        if not login or login in resolved:
            continue
        for commit in commits:
            person = commit_person.get(commit.get("sha"))
            if person:
                authors_of_pr[login][person] += 1
    for login, tally in sorted(authors_of_pr.items()):
        if login in resolved or not tally:
            continue
        (person, n), = tally.most_common(1)
        total = sum(tally.values())
        if n >= 3 and n / total >= 0.6:
            resolved[login] = person
            evidence[login] = (f"{person} authored {n} of the {total} commits on their "
                               f"pull requests")

    # 5. Bots.
    for login in counts:
        if login not in resolved and BOT_LOGIN_RE.search(login):
            resolved[login] = service
            evidence[login] = "automation account, folded into the service account"

    # 6. The outside long tail. Reassign to whoever on staff engaged with them —
    #    which is both deterministic and the most plausible reading: in a private
    #    company, the person who answered the question would have asked it.
    responders = _responders_by_login(history, resolved, by_id)
    reassigned: dict[str, dict] = {}
    fallback = employees[0]["id"] if employees else service
    for login in sorted(counts, key=lambda l: (-counts[l], l)):
        if login in resolved:
            continue
        who, why = responders.get(login, (None, ""))
        if who is None:
            who, why = fallback, "no staff engagement recorded; assigned to the busiest engineer"
        reassigned[login] = {"persona": who, "reason": why, "items": counts[login]}
        resolved[login] = who

    unresolved = sorted(l for l in counts if l not in resolved)
    return {
        "resolved": dict(sorted(resolved.items())),
        "reassigned": dict(sorted(reassigned.items())),
        "evidence": dict(sorted(evidence.items())),
        "unresolved": unresolved,
        "counts": {
            "logins": len(counts),
            "matched_to_roster": len(evidence),
            "reassigned": len(reassigned),
            "unresolved": len(unresolved),
        },
    }


def _responders_by_login(history: dict, resolved: dict[str, str],
                         by_id: dict[str, dict]) -> dict[str, tuple[str, str]]:
    """For each outside login, the employee who most often replied to them."""
    gh = history["github"]
    owner_of: dict[int, str] = {}
    for item in gh["pulls"] + gh["issues"]:
        login = (item.get("user") or {}).get("login")
        if login:
            owner_of[item["number"]] = login

    replies: dict[str, Counter] = defaultdict(Counter)
    for key in ("comments", "reviews", "review_comments"):
        for number, items in gh[key].items():
            asker = owner_of.get(int(number))
            if not asker:
                continue
            for item in items:
                responder = (item.get("user") or {}).get("login")
                person = resolved.get(responder or "")
                if person and by_id.get(person, {}).get("class") == EMPLOYEE:
                    replies[asker][person] += 1

    out: dict[str, tuple[str, str]] = {}
    for login, tally in replies.items():
        if not tally:
            continue
        (person, n), = tally.most_common(1)
        out[login] = (person, f"{person} replied to them {n} time(s) on GitHub")
    return out


# =============================================================================
# Services
# =============================================================================
def build_services(grounding: dict) -> list[dict]:
    """The things the company runs, and who is on the hook for each.

    Ownership is not asserted here — `analyze_repository.py` already derived it
    from commit share, with a threshold, and `capability_areas` already names
    each area the way an engineer would say it out loud. This joins the two.
    """
    ownership = grounding["ownership"]
    services = []
    for area in grounding["capability_areas"]:
        packages = area.get("packages") or []
        owners: Counter[str] = Counter()
        bus = []
        for package in packages:
            entry = ownership.get(package)
            if not entry:
                continue
            bus.append(entry["bus_factor"])
            for owner in entry["top_owners"]:
                owners[owner["id"]] += owner["commits"]
        services.append({
            "slug": area["slug"],
            "name": area["name"],
            "description": area["description"],
            "what_it_does_for_users": area.get("what_it_does_for_users", ""),
            "packages": sorted(packages),
            "paths": sorted(area.get("paths") or []),
            "maturity": area.get("maturity"),
            "activity": area.get("activity"),
            "owner_ids": [pid for pid, _ in owners.most_common(4)],
            "bus_factor": min(bus) if bus else None,
        })
    services.sort(key=lambda s: s["slug"])
    return services


def services_for(person_id: str, services: list[dict], grounding: dict) -> list[dict]:
    """What this person owns, measured, with the numbers that say so."""
    role = next((r for r in grounding["roles"] if r["person"] == person_id), None)
    owned = {o["subsystem"]: o for o in (role or {}).get("owns", [])}

    out = []
    for service in services:
        hits = [owned[p] for p in service["packages"] if p in owned]
        if not hits and person_id not in service["owner_ids"][:2]:
            continue
        share = max((h["share_of_subsystem"] for h in hits), default=0.0)
        out.append({
            "slug": service["slug"],
            "name": service["name"],
            "role": "owner" if hits or service["owner_ids"][:1] == [person_id]
                    else "contributor",
            "share_of_service": round(share, 3),
            "packages": sorted(h["subsystem"] for h in hits),
        })
    out.sort(key=lambda s: (-s["share_of_service"], s["slug"]))
    return out


# =============================================================================
# Channel candidates
# =============================================================================
def channel_candidates(grounding: dict, services: list[dict]) -> dict:
    """What a channel list would have to be about, if it were honest.

    Handing the model a blank page produces the same six channels every project
    on the internet has. Handing it the sub-teams that actually show up in who
    reviews whom, the services that actually get worked on, and how this team
    actually released, produces a list that matches the repository.
    """
    return {
        "subteams": [{"name": t["name"], "focus": t["focus"], "members": t["members"]}
                     for t in grounding["collaboration"]["subteams"]],
        "services": [{"slug": s["slug"], "name": s["name"], "activity": s["activity"]}
                     for s in services],
        "how_they_release": grounding["process"]["release_process"],
        "what_ci_is_for": grounding["process"]["ci_role"],
        "review_norms": grounding["process"]["review_norms"],
        "how_work_starts": grounding["process"]["how_work_starts"],
        "handoffs": grounding["collaboration"]["handoffs"],
        "already_exists": sorted(BUILTIN_CHANNELS),
    }


# =============================================================================
# Schemas
# =============================================================================
def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props,
            "required": required if required is not None else list(props),
            "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": {"type": "string"}}
_CONF = {"type": "number", "description": "0-1, how well the evidence supports this"}
_EVIDENCE = {"type": "array", "items": {"type": "string"},
             "description": "Concrete citations: contributor ids, subsystem keys, "
                            "service slugs, era slugs, months (YYYY-MM), repo paths."}

COMPANY_SCHEMA = _obj({
    "name": {**_STR, "description": "Invented. Two words at most, sayable out loud."},
    "slug": {**_STR, "description": "lowercase-hyphenated"},
    "tagline": _STR,
    "description": {**_STR, "description": "A paragraph. What it sells, to whom, and why."},
    "industry": _STR,
    "stage": {"type": "string",
              "enum": ["pre-seed", "seed", "series-a", "series-b", "bootstrapped"]},
    "headquarters": _STR,
    "founded_month": {**_STR, "description": "YYYY-MM. Use the month you are given."},
    "how_it_makes_money": _STR,
    "what_the_team_is_racing": {**_STR,
                                "description": "The pressure visible in the history"},
    "evidence": _EVIDENCE,
    "confidence": _CONF,
    "inferred": _obj({"reading": _STR, "confidence": _CONF}),
})

PERSON_SCHEMA = _obj({
    "display_name": {**_STR, "description": "Invented. Given name and surname. Must not "
                                            "resemble the real name in any way."},
    "title": {**_STR, "description": "Job title as it would appear in a directory"},
    "seniority": {"type": "string",
                  "enum": ["founder", "staff", "senior", "mid", "junior", "contractor",
                           "automation"]},
    "reports_to": {**_STR, "description": "Another person's REAL contributor id, or '' "
                                          "for the person everyone else reports to"},
    "bio": {**_STR, "description": "Two or three sentences, as an internal directory "
                                   "would carry. Their remit, not their life story."},
    "voice": _obj({
        "chat_register": {**_STR, "description": "How they write in chat"},
        "message_length": {"type": "string", "enum": ["terse", "short", "medium", "long"]},
        "emoji_use": {"type": "string", "enum": ["none", "rare", "occasional", "frequent"]},
        "catchphrases": {**_STRS, "description": "Turns of phrase they actually reuse, "
                                                 "taken from their real commit subjects"},
        "commit_message_style": _STR,
        "pr_review_tone": _STR,
        "issue_style": _STR,
        "email_register": _STR,
        "typo_habits": _STR,
    }),
    "evidence": _EVIDENCE,
    "confidence": _CONF,
    "inferred": _obj({"reading": _STR, "confidence": _CONF}),
})


def channels_schema(employee_ids: list[str]) -> dict:
    # The count is asked for in the prompt and enforced by validate_personas,
    # not by the schema: structured output rejects a `minItems` above 1, so a
    # schema that says what we mean is a 400 rather than a constraint.
    return _obj({"channels": {
        "type": "array",
        "items": _obj({
            "name": {**_STR, "description": "slug: lowercase, digits, - and _ only"},
            "display_name": {**_STR,
                             "description": "What the sidebar shows, written the way a "
                                            "person would — not the slug again"},
            "kind": {"type": "string",
                     "enum": ["company", "social", "team", "practice", "service"],
                     "description": "company = everyone, announcements and admin; "
                                    "social = not about work; team = a whole function; "
                                    "practice = something the team does (releases, "
                                    "incidents, review, on-call); service = one part of "
                                    "the product"},
            "type": {"type": "string", "enum": ["O", "P"],
                     "description": "O public, P private"},
            "purpose": _STR,
            "header": {**_STR, "description": "One line, as a real channel header reads"},
            "members": {"type": "array", "items": {"type": "string", "enum": employee_ids},
                        "description": "Who is actually in it"},
            "why_it_exists": {**_STR, "description": "What in the repository's history "
                                                     "makes this channel necessary"},
            "evidence": _EVIDENCE,
        })}})


# =============================================================================
# Stages
# =============================================================================
BRIEF = """You are building a synthetic software company around a real repository, so that
an AI agent can be dropped into it and find a coherent workplace. The repository, its code
and its history are real and stay exactly as they are. The people are being replaced.

Rules you must hold to:

* TWO KINDS OF FIELD, and mixing them up is the one unrecoverable mistake.

  `evidence` and `reports_to` are PROVENANCE. They are checked against the mined record
  and never shown to anyone, so they must use the real contributor ids you were given
  (e.g. `ryan-marten`), real subsystem keys, real paths, real release tags.

  EVERY OTHER FIELD IS WORLD-FACING. It is rendered into a chat workspace, a wiki and a
  git server that an agent will read. It must not contain a real person's name, a real
  contributor id, a real GitHub login (including bot logins like `cursor[bot]`), a real
  email address, the real organization's name, or the real package name — not once, not
  in passing, not in parentheses as a gloss. Say "the batch owner" or "the person who
  reviewed him", never the id. A single slip here fails the whole run.

* Names of people and of the company are INVENTED, and must not resemble the real ones —
  not a translation, not an anagram, not the same initials, not the same nationality cue.
* Everything else is READ OFF THE EVIDENCE, not invented. A person's seniority, what they
  own, how they write, when they joined and whether they left are all facts in the record
  you are given. Use them. If the evidence does not support a claim, do not make it.
* Anything you cannot show — why someone left, who was really in charge — goes in
  `inferred`, never in a measured field. `confidence` is 0-1 and should be low when you
  are extrapolating.
* Everyone who works on this code works at this company. It is a private repository on an
  internal server: there are no outside contributors, no public issue tracker and no
  open-source community. Where the evidence shows a drive-by patch, that is a colleague.
* Write plainly and specifically. "Owns the batch provider integrations" is useful;
  "works on the codebase" is not.
"""


class Leaked(RuntimeError):
    """A stage kept putting real identifiers in world-facing fields."""


def complete_clean(llm: rl.LLM, *, system: str, prompt: str, schema: dict, label: str,
                   patterns: list[str], visible, check=None, attempts: int = 3,
                   **kwargs) -> dict:
    """Call the model, then make it fix its own leaks rather than failing the run.

    The prompts say plainly that world-facing fields must carry no real name, and
    mostly that is enough — but "mostly" is not a property you want in the one
    check that matters, and a cold run against a different repository will find
    new ways to slip. Rather than leave a human to tighten the wording and pay
    for the whole stage again, the violations are handed back to the model with
    the offending text quoted, which is the fastest correction available.

    The retry is a different prompt and so a different cache key: replayed runs
    stay free and deterministic, and `cache/llm/` records both attempts.
    """
    problems: list[str] = []
    for attempt in range(attempts):
        this_prompt, this_label = prompt, label
        if problems:
            this_label = f"{label}#fix{attempt}"
            this_prompt = (
                prompt + "\n\nYOUR PREVIOUS ANSWER WAS REJECTED\n"
                "These world-facing fields carried real identifiers, or broke a stated "
                "rule. Rewrite the whole answer, keeping everything that was fine and "
                "fixing only what is listed. Do not simply delete the sentence — say the "
                "same thing without the real identifier.\n\n" + "\n".join(problems))
        out = llm.complete(system=system, prompt=this_prompt, schema=schema,
                           label=this_label, **kwargs)
        problems = scan_text(json.dumps(visible(out), ensure_ascii=False), patterns)
        problems += list(check(out) or []) if check else []
        if not problems:
            return out
        rl.warn(f"{this_label}: {len(problems)} problem(s), asking for a correction")
    raise Leaked(f"{label}: still failing after {attempts} attempts:\n    " +
                 "\n    ".join(problems))


def stage_system(grounding: dict, services: list[dict], people: list[dict]) -> str:
    """The shared prefix. Identical across every call in the run, so it caches."""
    return BRIEF + "\n\nREPOSITORY-WIDE EVIDENCE\n" + json.dumps({
        "repository": {
            "commits": grounding["source"]["commit_count"],
            "span": f'{grounding["source"]["first_commit"]["date"][:7]}'
                    f'..{grounding["source"]["last_commit"]["date"][:7]}',
            "what_it_is": grounding["documentation"]["readme"].get("summary", ""),
        },
        "services": [{k: s[k] for k in ("slug", "name", "description", "maturity",
                                        "activity", "owner_ids")} for s in services],
        "eras": [{"slug": e["slug"], "name": e["name"], "summary": e["summary"],
                  "span": f'{e["start_month"]}..{e["end_month"]}'}
                 for e in grounding["eras"]],
        "process": grounding["process"],
        "collaboration": {k: grounding["collaboration"][k]
                          for k in ("summary", "shape", "subteams", "handoffs")},
        "roster": [{"id": p["id"], "class": p["class"], "commits": p["commits"],
                    "first": p["first_commit"], "last": p["last_commit"],
                    "status": p["status"]} for p in people],
    }, ensure_ascii=False, separators=(",", ":"))


def stage_company(llm: rl.LLM, system: str, grounding: dict, founded: str,
                  patterns: list[str]) -> dict:
    prompt = (
        "Invent the company that ships this repository as its product.\n\n"
        "Everything except `evidence` is world-facing prose an agent will read: no real "
        "names, ids, logins, the real organization's name or the real package name "
        "anywhere in it.\n\n"
        "It is a real product with real users, and the history shows what that cost: read "
        "the pressure off the eras and the release cadence. The company is exactly as big "
        "as the roster you were given — do not imply departments that leave no trace in the "
        "commit log.\n\n"
        f"It was founded in {founded}, the month of the first commit. The product keeps its "
        "real name and is not renamed.\n\n"
        "PRODUCT README\n" +
        json.dumps(grounding["documentation"]["readme"], ensure_ascii=False,
                   separators=(",", ":"))[:6000] +
        "\n\nRELEASE HISTORY\n" +
        json.dumps(grounding["timeline"][:40], ensure_ascii=False, separators=(",", ":"))
    )
    return complete_clean(
        llm, system=system, prompt=prompt, schema=COMPANY_SCHEMA, label="company",
        patterns=patterns,
        visible=lambda o: {k: v for k, v in o.items() if k != "evidence"})


def stage_person(llm: rl.LLM, system: str, company: dict, person: dict,
                 owned: list[dict], patterns: list[str], **kwargs) -> dict:
    profile = person["profile"]
    packet = {
        "contributor_id": person["id"],
        "class": person["class"],
        "status": person["status"],
        "commits": person["commits"],
        "first_commit": person["first_commit"],
        "last_commit": person["last_commit"],
        "active_months": person["active_months"],
        "services_they_own": owned,
        "measured_role": person["role"],
        "work_types": person["work_types"],
        "top_subsystems": dict(list(person["subsystems"].items())[:8]),
        # The profile is where the voice actually comes from: it already records
        # how this person wrote commit messages, how big their changes were and
        # how they behaved in review, all cited to the evidence.
        "headline": profile.get("headline"),
        "summary": profile.get("summary"),
        "specialties": profile.get("specialties"),
        "working_style": profile.get("working_style"),
        "review_behaviour": profile.get("review_behaviour"),
        "how_it_ended": profile.get("how_it_ended"),
        "seniority_read": (profile.get("inferred") or {}).get("likely_seniority"),
        "role_title_read": (profile.get("inferred") or {}).get("apparent_role_title"),
        "leadership_signals": (profile.get("inferred") or {}).get("leadership_signals"),
    }
    taken = kwargs.pop("taken_names", ())
    clashed_with = kwargs.pop("clashed_with", "")
    is_machine = person["class"] == SERVICE
    prompt = (
        f"Give {person['id']} a name and a place at {company['name']}.\n\n"
        + ("This one is not a person: it is the account automation commits under. Name it "
           "the way a team names a bot — something that reads as a tool, not as a "
           "colleague — give it the seniority `automation`, and write the `voice` as the "
           "shape of its generated messages.\n\n" if is_machine else "")
        + "Their `voice` is the important part, and it is not a character sketch — it is a "
        "translation of measured behaviour into how this person types. `working_style."
        "commit_message_style` already says how they wrote commit subjects; carry that over "
        "faithfully, including whether they capitalise, whether they use conventional-commit "
        "prefixes, and how terse they are. `review_behaviour` says how they behave in review. "
        "Their work mix says whether they talk about tests, refactors or shipping. A person "
        "who wrote 369 terse lowercase commits does not write long polished chat messages.\n\n"
        "`catchphrases` must be phrasings actually visible in their record, not invented "
        "quirks. If the record shows none, return an empty list.\n\n"
        "`bio` and every field under `voice` are world-facing: they are rendered into the "
        "company's directory and read by an agent. Describe colleagues by their role — "
        "\"the batch owner\", \"whoever was reviewing him then\" — and never by a real id, "
        "name or login. Real ids belong in `evidence` and `reports_to` only.\n\n"
        "Watch the branch names in particular: this team prefixed topic branches with the "
        "author's own handle, so a branch like `<handle>/batch-fix` carries a real name. "
        "Describe the habit (\"a topic branch under their own handle\") without quoting one."
        "\n\n"
        "`title` and `seniority` follow the evidence: commit share, whether they merged other "
        "people's work, whether they were reviewed or reviewing. `reports_to` is the real "
        "contributor id of whoever the evidence suggests they answered to — the person who "
        "reviewed them most, or who owns the area they worked in — or '' for the one person "
        "at the top. Do not invent a manager who is not in the roster.\n\n"
        "THIS PERSON'S EVIDENCE\n" +
        json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
        # Last, because this is the constraint that gets ignored when it is
        # buried. Three people with thin, near-identical records were coming
        # back as the same invented name however politely the top of the prompt
        # asked for variety, so the retry forbids the exact name and its whole
        # initial — a rule that cannot be satisfied by a near-miss.
        + (f"\n\nHARD CONSTRAINT ON THE NAME, overriding anything above.\n"
           f"You already used {clashed_with} for a different colleague. Pick a "
           f"different person's name: not that one, not a variant of it, and not "
           f"starting with '{clashed_with[:1].upper()}'.\n"
           f"Also already taken, so avoid these given names and surnames: "
           f"{', '.join(sorted(taken))}.\n"
           f"Check your answer against both lists before you give it."
           if clashed_with else "")
    )
    out = complete_clean(
        llm, system=system, prompt=prompt, schema=PERSON_SCHEMA,
        label=f"person:{person['id']}" + ("#renamed" if clashed_with else ""),
        patterns=patterns,
        visible=lambda o: {k: v for k, v in o.items()
                           if k not in ("evidence", "reports_to")})
    out["id"] = person["id"]
    return out


def stage_channels(llm: rl.LLM, system: str, company: dict, candidates: dict,
                   employees: list[dict], patterns: list[str]) -> list[dict]:
    staff = [{"id": p["id"], "title": p["synthetic"]["title"],
              "owns": [s["slug"] for s in p["services_owned"]]} for p in employees]
    prompt = (
        f"Lay out {company['name']}'s chat workspace.\n\n"
        f"Between {MIN_CHANNELS} and {MAX_CHANNELS} channels, and most of them are not about "
        "the architecture. A workspace this size is mostly a few broad, slightly messy rooms "
        "that everything ends up in. Start from the ones every engineering company has, under "
        "the plain names every engineering company uses:\n\n"
        "  - somewhere everyone reads: announcements, logistics, FYIs\n"
        "  - the main engineering room, where half of what is discussed belongs somewhere else\n"
        "  - somewhere to ask why a thing is failing\n"
        "  - somewhere for links, jokes and things that are not work\n"
        "  - somewhere for breakage that is happening right now\n"
        "  - somewhere pull requests go to get looked at\n"
        "  - somewhere releases get coordinated\n\n"
        "Then, and only then, three or four rooms for the parts of THIS product that generated "
        "enough sustained work to need their own — named after what the team calls that work, "
        "not after a package. A channel per subsystem is what a workspace looks like when "
        "nobody used it. Where two areas were worked on by the same people, they shared a "
        "room; merge them rather than splitting them.\n\n"
        "Name them the way people type them: one or two plain words, lowercase, the "
        "conventional name if there is one. `#help`, not `#help-me`. `#incidents`, not "
        "`#firefighting`. `#research`, not `#reading-room`. A name joined by `-and-` means "
        "you merged two things that should either be one thing with one name, or stay "
        "separate.\n\n"
        "`kind` says which sort each one is, and the mix has to be believable: at least one "
        "`company`, at least one `social`, at least one `team`, and fewer `service` channels "
        "than everything else put together.\n\n"
        "The broad channels need no justification beyond people needing them. The `service` "
        "and `practice` ones do: name the sub-team, the release habit or the recurring "
        "breakage in the history that made the room necessary.\n\n"
        "Membership is not uniform. The company-wide and social rooms hold everyone; a room "
        "about one part of the product holds the four to eight people who actually touched "
        "it, and that is visible in who committed where.\n\n"
        "`name`, `display_name`, `purpose` and `header` are world-facing and are read by "
        "an agent: no real ids, names, logins or bot handles in any of them, and no "
        "channel premised on outside contributors — the repository is private and "
        "everyone who touches it works here. Real ids go in `evidence` and `members`.\n\n"
        f"{len(staff)} people work here and that is everyone. `members` must be a subset of "
        "the ids below; a channel every single person is in should say so by listing them "
        "all. Mattermost creates `town-square` and `off-topic` itself, so do not use those "
        "two slugs — the company's own general and off-topic rooms get the names this team "
        "would actually give them.\n\n"
        "Use real contributor ids in `members`; they are swapped for the synthetic ones "
        "afterwards.\n\n"
        "STAFF\n" + json.dumps(staff, ensure_ascii=False, separators=(",", ":")) +
        "\n\nWHAT THE HISTORY SHOWS\n" +
        json.dumps(candidates, ensure_ascii=False, separators=(",", ":"))
    )
    ids = [p["id"] for p in employees]

    def shape_is_sane(out: dict) -> list[str]:
        """A workspace that is all subsystems is the giveaway, so check the mix.

        Asking for balance in prose produced twelve channels named after twelve
        packages. Counting them is the part that holds.
        """
        channels = out["channels"]
        problems = []
        if not MIN_CHANNELS <= len(channels) <= MAX_CHANNELS:
            problems.append(f"you returned {len(channels)} channels; return between "
                            f"{MIN_CHANNELS} and {MAX_CHANNELS}")
        kinds = Counter(c["kind"] for c in channels)
        for required in ("company", "social", "team"):
            if not kinds[required]:
                problems.append(f"there is no `{required}` channel; a real workspace has "
                                f"at least one")
        if kinds["service"] > len(channels) - kinds["service"]:
            problems.append(
                f"{kinds['service']} of {len(channels)} channels are about a single part "
                "of the product, which is more than everything else put together. Merge "
                "the quiet ones into a broader channel.")
        if any(c["display_name"] == c["name"] for c in channels):
            problems.append("some display names are just the slug again; write them the "
                            "way the sidebar should read")
        # `#backends-and-batch` and `#cookbooks-and-examples` are two rooms in a
        # trenchcoat. Either they are one thing and have one name, or they are
        # two and were merged to hit a number.
        joined = [c["name"] for c in channels if "-and-" in c["name"]]
        if joined:
            problems.append(f"{', '.join(joined)} name two things at once; give each a "
                            "single plain name or leave them separate")
        # People type channel names constantly, so real ones are short.
        wordy = [c["name"] for c in channels if c["name"].count("-") > 1]
        if wordy:
            problems.append(f"{', '.join(wordy)} are too long to type; one or two words")
        return problems

    out = complete_clean(
        llm, system=system, prompt=prompt, schema=channels_schema(ids),
        label="channels", patterns=patterns, check=shape_is_sane,
        visible=lambda o: [{k: v for k, v in c.items()
                            if k not in ("evidence", "members")}
                           for c in o["channels"]])
    return out["channels"]


# =============================================================================
# Naming
# =============================================================================
def name_clashes(groups: list[dict], profiles: dict[str, dict]) -> list[str]:
    """Contributor ids whose persona shares a given name or surname with an earlier one.

    Given names matter most — they are what the id is built from and what people
    type in chat — but two Halloways on a twelve-person team reads just as wrong,
    so both halves are checked. `groups` is in roster order, so the person with
    the most history is the one who keeps the name.
    """
    seen_given: set[str] = set()
    seen_family: set[str] = set()
    clashing: list[str] = []
    for group in groups:
        pid = group["primary"]["id"]
        parts = [rl.slugify(p) for p in profiles[pid]["display_name"].split()]
        parts = [p for p in parts if p]
        if not parts:
            continue
        given, family = parts[0], parts[-1]
        if given in seen_given or (len(parts) > 1 and family in seen_family):
            clashing.append(pid)
            continue
        seen_given.add(given)
        if len(parts) > 1:
            seen_family.add(family)
    return clashing


def assign_ids(named: dict[str, str], service_account: str) -> dict[str, str]:
    """Persona ids from the invented display names, deterministically.

    The world's own placeholder data uses `alice`, `bob`, `carol` — a given name
    is the natural id, and it is what a colleague would type. Collisions fall
    back to given-name-plus-initial, then the full slug, in a fixed order so the
    same names always produce the same ids.
    """
    ids: dict[str, str] = {}
    taken: set[str] = set(RESERVED_IDS)

    for real_id in sorted(named):
        display = named[real_id]
        if real_id == service_account:
            candidates = ["automation", "ci-bot", "buildbot"]
        else:
            parts = [rl.slugify(p) for p in display.split() if rl.slugify(p)]
            first = parts[0] if parts else rl.slugify(display)
            rest = parts[1:] if len(parts) > 1 else []
            candidates = [first]
            if rest:
                candidates.append(f"{first}-{rest[-1][0]}")
                candidates.append(f"{first}-{rest[-1]}")
        chosen = next((c for c in candidates if ID_RE.match(c) and c not in taken), None)
        if chosen is None:
            base = candidates[-1][:29]
            n = 2
            while f"{base}-{n}" in taken:
                n += 1
            chosen = f"{base}-{n}"
        taken.add(chosen)
        ids[real_id] = chosen
    return ids


# =============================================================================
# Guardrails
# =============================================================================
# A generic word that happens to be someone's email local part would match every
# sentence in the file and make the leak scan useless. These are the ones that
# actually occur in this repository's identities.
LEAK_STOPWORDS = frozenset({
    "github", "noreply", "users", "info", "mail", "dev", "admin", "team", "the",
    "code", "data", "test", "root", "user", "bot", "web", "api",
})


def leak_patterns(people: list[dict], identity_map: dict, extra: list[str]) -> list[str]:
    """Every string that must not appear in anything the world will show."""
    raw: set[str] = set(extra)
    for person in people:
        raw.update(person["names"])
        raw.add(person["display_name"])
        for email in person["emails"]:
            raw.add(email)
            local = re.sub(r"^\d+\+", "", email.split("@", 1)[0])
            raw.add(local)
        if person["github_login"]:
            raw.add(person["github_login"])
    raw.update(identity_map["resolved"])

    # Only human names are broken into parts. A surname on its own is a leak;
    # a fragment of a login is not — `copilot-pull-request-reviewer[bot]` would
    # otherwise contribute the pattern "request" and flag every sentence in the
    # file about the request processor.
    human_names = {n for person in people for n in [*person["names"],
                                                    person["display_name"]]}

    patterns = set()
    for value in raw:
        value = (value or "").strip()
        if len(value) < 4 or value.lower() in LEAK_STOPWORDS:
            continue
        patterns.add(value)
        if value in human_names:
            for token in re.split(r"[\s._-]+", value):
                if len(token) >= 5 and token.lower() not in LEAK_STOPWORDS:
                    patterns.add(token)
    return sorted(patterns)


# What the world actually renders, field by field. A whitelist rather than a
# blacklist: the file is full of deliberate real identifiers — `real`,
# `identity_map`, and every `evidence` list, which cites real contributor ids
# precisely so `verify_citations` can check it against the mined record — and a
# scan that trips over its own provenance is a scan people learn to ignore.
def world_facing(payload: dict) -> dict:
    def pick(obj: dict, *keys) -> dict:
        return {k: obj[k] for k in keys if obj.get(k)}

    return {
        "company": pick(payload["company"], "name", "slug", "tagline", "description",
                        "industry", "stage", "headquarters", "how_it_makes_money",
                        "what_the_team_is_racing"),
        "services": [pick(s, "name", "description", "what_it_does_for_users")
                     for s in payload["services"]],
        "channels": [pick(c, "name", "display_name", "purpose", "header")
                     for c in payload["channels"]],
        "people": [{**pick(p["synthetic"], "id", "display_name", "title", "seniority"),
                    "bio": p["bio"], "voice": p["voice"]}
                   for p in payload["people"]],
    }


def scan_text(text: str, patterns: list[str]) -> list[str]:
    hits = []
    for pattern in patterns:
        match = re.search(re.escape(pattern), text, re.I)
        if match:
            start = max(0, match.start() - 70)
            hits.append(f"{pattern!r}: ...{text[start:match.end() + 70]}...")
    return hits


def scan_for_leaks(payload: dict, patterns: list[str], extra_text: str = "") -> list[str]:
    return scan_text(
        json.dumps(world_facing(payload), ensure_ascii=False) + "\n" + extra_text,
        patterns)


_MONTH_RE = re.compile(r"\b\d{4}-\d{2}\b")
_EPISODE_RE = re.compile(r"\bep-[0-9a-f]{12}\b")
_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{2,}")
# Pull request and issue references, which are how this team cites work.
_REF_RE = re.compile(r"#\d+")


def verify_citations(payload: dict, grounding: dict, people: list[dict],
                     history_releases: list[dict], pull_numbers: set[int]) -> dict:
    """Every citation must name something that exists.

    A fabricated subsystem key or contributor id reads exactly like a real one to
    everything downstream. Confidence and `inferred` already flag judgement; this
    catches the failure that does not announce itself.
    """
    known = {p["id"] for p in people}
    known |= {s["key"] for s in grounding["subsystems"]}
    known |= {s["slug"] for s in payload["services"]}
    known |= {e["slug"] for e in grounding["eras"]}
    known |= {a["slug"] for a in grounding["capability_areas"]}
    known |= set(grounding["ownership"])
    # The evidence packet hands the model GitHub logins (in `reviewed_by`) and
    # named metrics (`pr_share`, `work_types`), and citing them is exactly right
    # — they are how a claim is traced back. A checker that does not know them
    # reports two thirds of a good run as broken, and then nobody reads it.
    known |= set(payload["identity_map"]["resolved"])
    known |= {"commits", "episodes_authored", "active_months", "pr_share",
              "work_types", "file_roles", "top_subsystems", "subsystems",
              "monthly_commits", "reviews_given", "reviewed_by", "review_states_given",
              "median_files_per_episode", "focus_by_half_year", "measured_role",
              "first_commit", "last_commit", "bus_factor", "share_of_subsystem",
              "sample_commit_subjects", "sample_episode_titles"}
    paths = {p for s in grounding["subsystems"] for p in s["paths"]}
    tags = {t["name"] for t in grounding["source"]["tags"]}
    tags |= {r.get("tag_name") for r in history_releases}
    tags |= {f"#{n}" for n in pull_numbers}

    problems: list[str] = []
    checked = 0

    def anchors(citation: str) -> set[str]:
        """The identifiers a citation actually points at.

        Citations are written as prose — "369 commits, 2024-10-31..2025-04-22,
        7 active months" — so the useful question is not whether the string
        parses but whether anything in it names something real. A citation that
        anchors to nothing is the failure worth catching: it reads like a fact
        and cannot be traced back to one.
        """
        found = (set(_MONTH_RE.findall(citation))
                 | set(_EPISODE_RE.findall(citation))
                 | {r for r in _REF_RE.findall(citation) if r in tags})
        for token in _TOKEN_RE.findall(citation):
            token = token.strip(".,;:")
            if token in known or token in tags or token in paths:
                found.add(token)
            elif any(token.startswith(p) or p.startswith(token) for p in paths):
                found.add(token)
        return found

    def check(where: str, citations) -> None:
        nonlocal checked
        for citation in citations or []:
            checked += 1
            if not anchors(citation):
                problems.append(f"{where}: nothing in {citation!r} names a person, "
                                f"subsystem, service, month, episode, path or tag "
                                f"that exists")

    check("company", payload["company"].get("evidence"))
    for person in payload["people"]:
        check(f"people/{person['synthetic']['id']}", person.get("evidence"))
        for owned in person["services_owned"]:
            checked += 1
            if owned["slug"] not in known:
                problems.append(f"people/{person['synthetic']['id']}: unknown service "
                                f"{owned['slug']!r}")
    for channel in payload["channels"]:
        check(f"channels/{channel['name']}", channel.get("evidence"))
    return {"citations_checked": checked, "problems": problems}


def validate_personas(payload: dict) -> list[str]:
    problems = []
    seen: dict[str, str] = {}
    for person in payload["people"]:
        pid = person["synthetic"]["id"]
        if not ID_RE.match(pid):
            problems.append(f"{pid!r} does not match {ID_RE.pattern}")
        if pid in RESERVED_IDS:
            problems.append(f"{pid!r} is reserved by a service")
        if pid in seen:
            problems.append(f"{pid!r} is used by two people")
        seen[pid] = person["real"][0]["id"]

    employees = {p["synthetic"]["id"] for p in payload["people"]
                 if p["class"] == EMPLOYEE}
    for channel in payload["channels"]:
        if channel["name"] in BUILTIN_CHANNELS:
            problems.append(f"channel {channel['name']!r} is created by Mattermost itself")
        outside = sorted(set(channel["members"]) - employees)
        if outside:
            problems.append(f"channel {channel['name']!r} has non-employee members: "
                            f"{', '.join(outside)}")
    if not MIN_CHANNELS <= len(payload["channels"]) <= MAX_CHANNELS:
        problems.append(f"{len(payload['channels'])} channels, "
                        f"expected {MIN_CHANNELS}-{MAX_CHANNELS}")
    return problems


# =============================================================================
# Projections
# =============================================================================
def yaml_str(value: str) -> str:
    """Quote only when the value would otherwise parse as something else."""
    if value == "" or re.search(r'[:#\[\]{}&*!|>%@`"\']|^\s|\s$|^[-?]', value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def existing_admin(path: Path) -> dict | None:
    """The admin persona is created by bootstrap from .env, not by us.

    `data/schemas/identities.md` is explicit that ingestion matches it on
    `gitea_username` and reuses the existing account. Rewriting it out of the
    file would leave every document it authored unattributable.
    """
    if not path.exists():
        return None
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 — a broken placeholder must not stop the run
        return None
    for persona in data.get("personas") or []:
        if persona.get("is_admin"):
            return persona
    return None


def project_identities(payload: dict, domain: str, admin: dict | None) -> str:
    lines = [
        "# The company's people. Generated by data_gen/phase1_company_grounding.py",
        "# from the real repository's contributors — one persona per real identity,",
        "# so that every commit in the history has an author that exists here.",
        "#",
        "# Schema: data/schemas/identities.md. Do not hand-edit: regenerate.",
        "version: 1",
        f"domain: {domain}",
        "",
        "personas:",
    ]
    if admin:
        lines += [
            "  # Created by bootstrap.sh from WORLD_ADMIN_* in .env; listed only so it",
            "  # can author content. Ingestion never recreates it.",
            f"  - id: {admin['id']}",
            f"    display_name: {yaml_str(admin['display_name'])}",
            f"    email: {admin['email']}",
        ]
        if admin.get("role"):
            lines.append(f"    role: {yaml_str(admin['role'])}")
        lines.append("    is_admin: true")
        lines.append("")

    by_class: dict[str, list[dict]] = defaultdict(list)
    for person in payload["people"]:
        by_class[person["class"]].append(person)

    captions = {
        EMPLOYEE: "  # Staff. These are the only people in the chat workspace.",
        ASSOCIATE: "  # Outside contributors: real commits in the history, no seat here.",
        SERVICE: "  # Automation. Everything a machine committed is signed by this.",
    }
    for klass in (EMPLOYEE, ASSOCIATE, SERVICE):
        group = by_class.get(klass)
        if not group:
            continue
        lines.append(captions[klass])
        for person in group:
            syn = person["synthetic"]
            lines.append(f"  - id: {syn['id']}")
            lines.append(f"    display_name: {yaml_str(syn['display_name'])}")
            lines.append(f"    email: {syn['id']}@{domain}")
            if syn.get("title"):
                lines.append(f"    role: {yaml_str(syn['title'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def project_channels(payload: dict, team: str) -> str:
    lines = [
        "# The chat workspace. Generated by data_gen/phase1_company_grounding.py.",
        "#",
        "# `members` is listed on every channel, public ones included: the schema",
        "# defaults an omitted list to *all* personas, which would pull the outside",
        "# contributors into a workspace they were never in.",
        "#",
        "# Schema: data/schemas/messages.md. Do not hand-edit: regenerate.",
        "version: 1",
        f"team: {team}",
        "",
        "channels:",
    ]
    for channel in payload["channels"]:
        lines.append(f"  - name: {channel['name']}")
        lines.append(f"    display_name: {yaml_str(channel['display_name'])}")
        lines.append(f"    type: {channel['type']}")
        if channel.get("purpose"):
            lines.append(f"    purpose: {yaml_str(channel['purpose'])}")
        if channel.get("header"):
            lines.append(f"    header: {yaml_str(channel['header'])}")
        lines.append("    members:")
        for member in channel["members"]:
            lines.append(f"      - {member}")
    return "\n".join(lines) + "\n"


def write_projection(path: Path, text: str, force: bool, dry: bool) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        rl.info(f"{path} unchanged")
        return
    if dry:
        rl.info(f"would write {path}")
        return
    if path.exists() and not force and not _is_placeholder(path):
        rl.fail(f"{path} has been edited since it was generated.\n"
                "  Re-run with --force to overwrite it, or move it aside first.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    rl.ok(f"{path} ({rl.human_bytes(len(text.encode()))})")


def _is_placeholder(path: Path) -> bool:
    """Is this file still exactly what is committed, or has someone edited it?

    Asking git is precise where a header sniff is not: the committed
    `channels.yaml` carries no marker saying it is a placeholder, so a heuristic
    refused to replace the very file this step exists to replace. Anything git
    cannot answer for — untracked, no repository — is treated as hand-written and
    left alone.
    """
    # Our own previous output is always ours to replace; the header says so.
    if "phase1_company_grounding.py" in path.read_text(encoding="utf-8")[:400]:
        return True
    try:
        rel = path.resolve().relative_to(rl.REPO_ROOT)
    except ValueError:
        return False
    committed = subprocess.run(
        ["git", "-C", str(rl.REPO_ROOT), "show", f"HEAD:{rel}"],
        capture_output=True)
    if committed.returncode != 0:
        return False
    return committed.stdout == path.read_bytes()


# =============================================================================
# Assembly
# =============================================================================
def assemble(company: dict, profiles: dict, channels: list[dict], groups: list[dict],
             services: list[dict], identity_map: dict, grounding: dict) -> dict:
    service_account = one_service_account(groups)
    persona_id = assign_ids(
        {g["primary"]["id"]: profiles[g["primary"]["id"]]["display_name"] for g in groups},
        service_account)

    # Every real identity resolves to the persona of the group that absorbed it,
    # so a lookup by contributor id works whether or not it was the primary.
    for group in groups:
        for member in group["members"]:
            persona_id.setdefault(member["id"], persona_id[group["primary"]["id"]])

    out_people = []
    for group in groups:
        primary = group["primary"]
        profile = profiles[primary["id"]]
        out_people.append({
            "real": [{
                "id": member["id"],
                "display_name": member["display_name"],
                "names": member["names"],
                "emails": member["emails"],
                "github_login": member["github_login"],
                "commits": member["commits"],
                "first_commit": member["first_commit"],
                "last_commit": member["last_commit"],
                "active_months": member["active_months"],
            } for member in group["members"]],
            "class": primary["class"],
            "tier": primary["tier"],
            "status": primary["status"],
            "synthetic": {
                "id": persona_id[primary["id"]],
                "display_name": profile["display_name"],
                "title": profile["title"],
                "seniority": profile["seniority"],
                "reports_to": persona_id.get(profile.get("reports_to") or "", ""),
                "employment_status": primary["status"],
                "start_date": primary["first_commit"],
                "end_date": (primary["last_commit"]
                             if primary["status"] == "departed" else None),
            },
            "services_owned": services_for(primary["id"], services, grounding),
            "voice": profile["voice"],
            "bio": profile["bio"],
            "evidence": profile.get("evidence", []),
            "confidence": profile.get("confidence"),
            "inferred": profile.get("inferred", {}),
        })

    # Services and channels refer to people by real contributor id up to this
    # point; swap them for persona ids so nothing downstream needs the mapping.
    for service in services:
        service["owners"] = [persona_id[o] for o in service.pop("owner_ids")
                             if o in persona_id]
    for channel in channels:
        channel["members"] = sorted({persona_id[m] for m in channel["members"]
                                     if m in persona_id})

    reporting = [{"person": p["synthetic"]["id"], "reports_to": p["synthetic"]["reports_to"]}
                 for p in out_people if p["synthetic"]["reports_to"]]
    subteams = [{"name": t["name"], "focus": t["focus"],
                 "members": sorted({persona_id[m] for m in t["members"]
                                    if m in persona_id})}
                for t in grounding["collaboration"]["subteams"]]

    return {
        "company": company,
        "services": services,
        "people": out_people,
        "identity_map": {
            **identity_map,
            "login_to_persona": {login: persona_id.get(pid, pid)
                                 for login, pid in identity_map["resolved"].items()},
            "person_to_persona": dict(sorted(persona_id.items())),
        },
        "channels": channels,
        "org": {"reporting_lines": reporting, "subteams": subteams},
    }


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--grounding", type=Path, default=DEFAULT_GROUNDING)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "llm")
    parser.add_argument("--model", default=rl.MODEL)
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--no-refresh", action="store_true",
                        help="rebuild from the cache; never open a socket")
    parser.add_argument("--no-enrich", action="store_true",
                        help="write the measured evidence only, no personas")
    parser.add_argument("--no-emit-world-data", action="store_true",
                        help="skip projecting data/identities.yaml and data/channels.yaml")
    parser.add_argument("--force", action="store_true",
                        help="overwrite hand-edited projections")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    grounding = load_json(args.grounding, "Run the analysis stages first:")
    history = load_json(args.history, "Run the extraction stage first:")
    if "people" not in grounding:
        rl.fail(f"{args.grounding} has no `people` section — it was written with\n"
                "  --no-enrich. The company is read off the interpreted profiles, so\n"
                "  re-run analyze_repository.py with enrichment on.")

    rl.heading("Roster")
    people = build_roster(grounding, history)
    groups = persona_groups(people)
    counts = Counter(g["primary"]["class"] for g in groups)
    rl.ok(f"{len(people)} real identities become {len(groups)} personas: "
          f"{counts[EMPLOYEE]} employees, {counts[ASSOCIATE]} associates, "
          f"{counts[SERVICE]} service account "
          f"({sum(1 for p in people if p['class'] == SERVICE)} automation signatures "
          f"folded into it)")
    if not counts[EMPLOYEE]:
        rl.fail("no core contributors in the grounding roster — nothing to staff a company with")

    rl.heading("Identities")
    identity_map = resolve_logins(history, people, groups)
    im = identity_map["counts"]
    rl.ok(f"{im['logins']} GitHub logins: {im['matched_to_roster']} joined to the roster, "
          f"{im['reassigned']} outside accounts reassigned")
    if identity_map["unresolved"]:
        rl.fail("these forge logins could not be mapped to anyone, so their issues and "
                "comments would either leak or be lost:\n    " +
                "\n    ".join(identity_map["unresolved"]))

    services = build_services(grounding)
    rl.ok(f"{len(services)} services, "
          f"{sum(1 for s in services if s['bus_factor'] == 1)} with a bus factor of 1")

    if args.no_enrich:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": rl.now_iso(),
            "generator": "data_gen/phase1_company_grounding.py",
            "method": "measured evidence only (--no-enrich): no company, no personas",
            "source": _source(args, grounding),
            "services": services,
            "roster": [{k: v for k, v in p.items() if k != "profile"} for p in people],
            "identity_map": identity_map,
            "analysis": {"method": "deterministic only", "interpreted_keys": [],
                         "measured_keys": ["services", "roster", "identity_map"]},
        }
        size = rl.write_json(args.out, payload)
        rl.heading("Wrote")
        rl.ok(f"{args.out} ({rl.human_bytes(size)})")
        return 0

    llm = rl.LLM(args.cache_dir, model=args.model, effort=args.effort,
                 refresh=not args.no_refresh, verbose=args.verbose)
    system = stage_system(grounding, services, people)
    # Computed before the first call, not after the last: every stage checks its
    # own output against these and asks for a correction, so a cold run repairs
    # itself instead of getting most of the way through and then refusing.
    patterns = leak_patterns(people, identity_map, extra=[])

    rl.heading("The company")
    founded = (grounding["source"]["first_commit"]["date"] or "")[:7]
    company = stage_company(llm, system, grounding, founded, patterns)
    rl.ok(f"{company['name']} — {company['tagline']}")

    rl.heading("People")
    profiles: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(stage_person, llm, system, company, group["primary"],
                               services_for(group["primary"]["id"], services, grounding),
                               patterns): group["primary"]
                   for group in groups}
        for future in as_completed(futures):
            person = futures[future]
            try:
                profiles[person["id"]] = future.result()
            except Exception as exc:  # noqa: BLE001 — one failure must not lose the run
                rl.fail(f"could not build a persona for {person['id']}: {exc}\n"
                        "  Every real identity needs one, or Phase 1.5 has a git author\n"
                        "  it cannot map. Re-run to retry; cached personas are free.")
    rl.ok(f"{len(profiles)} personas")

    # Each person is named in its own call, so nothing stops two of them coming
    # back as Priya. Re-ask the later ones — roster order, so the person with the
    # most history keeps the name — with the taken names in front of them. Three
    # Nils on a twelve-person team is the kind of detail that gives a world away.
    for attempt in range(3):
        clashing = name_clashes(groups, profiles)
        if not clashing:
            break
        rl.warn(f"{len(clashing)} name clash(es): " +
                ", ".join(f"{profiles[pid]['display_name']}" for pid in clashing) +
                " — renaming")
        for pid in clashing:
            group = next(g for g in groups if g["primary"]["id"] == pid)
            profiles[pid] = stage_person(
                llm, system, company, group["primary"],
                services_for(pid, services, grounding), patterns,
                clashed_with=profiles[pid]["display_name"],
                taken_names={profiles[g["primary"]["id"]]["display_name"]
                             for g in groups if g["primary"]["id"] != pid})
    else:
        rl.warn("names still clash after three attempts; continuing anyway")

    # Channels need the personas, because who is in a channel is a fact about
    # people. Employees only, in roster order.
    staged = [{"id": g["primary"]["id"], "synthetic": profiles[g["primary"]["id"]],
               "services_owned": services_for(g["primary"]["id"], services, grounding)}
              for g in groups if g["primary"]["class"] == EMPLOYEE]
    rl.heading("Workspace")
    channels = stage_channels(llm, system, company,
                              channel_candidates(grounding, services), staged, patterns)
    rl.ok(f"{len(channels)} channels: " + ", ".join(c["name"] for c in channels))

    payload_body = assemble(company, profiles, channels, groups, services,
                            identity_map, grounding)

    # Build the projections before the checks, not after: they are the files the
    # world actually reads, so they are the ones the leak scan has to clear, and
    # nothing should be written if it does not.
    domain = rl.env_value("WORLD_DOMAIN") or "world.local"
    team = rl.env_value("MM_TEAM_NAME") or "world"
    identities_path = args.data_dir / "identities.yaml"
    projections = {
        identities_path: project_identities(payload_body, domain,
                                            existing_admin(identities_path)),
        args.data_dir / "channels.yaml": project_channels(payload_body, team),
    }

    rl.heading("Checks")
    leaks = scan_for_leaks(payload_body, patterns,
                           extra_text="\n".join(projections.values()))
    # The real organization's name is not scanned everywhere on purpose: the
    # package is still `bespokelabs.curator` by design, so the string is all over
    # the source the agent reads and flagging it would be crying wolf about a
    # decision we made. What must not happen is the *company* being named after
    # it, so that block is checked on its own.
    leaks += [f"the company is named after the real one: {hit}"
              for hit in scan_for_leaks({**payload_body, "people": [], "services": [],
                                         "channels": []}, _org_names(grounding))]
    if leaks:
        for leak in leaks[:20]:
            rl.warn(leak)
        rl.fail(f"{len(leaks)} real identifier(s) reached the synthetic side. Nothing was\n"
                "  written. This is the one failure that must never ship: fix the prompt, or\n"
                "  delete the offending entries from cache/llm/ and re-run.")
    rl.ok(f"no real names, emails or logins in anything the world will show "
          f"({len(patterns)} patterns checked, including both projected files)")

    problems = validate_personas(payload_body)
    if problems:
        for problem in problems:
            rl.warn(problem)
        rl.fail(f"{len(problems)} persona/channel problem(s); ingestion would reject this")
    rl.ok("persona ids valid and unique; channels staffed by employees only")

    citations = verify_citations(
        payload_body, grounding, people, history["github"]["releases"],
        {p["number"] for p in history["github"]["pulls"]}
        | {i["number"] for i in history["github"]["issues"]})
    if citations["problems"]:
        for problem in citations["problems"][:20]:
            rl.warn(problem)
        rl.warn(f"{len(citations['problems'])} citation problem(s) — written anyway, "
                "flagged in `analysis`")
    else:
        rl.ok(f"{citations['citations_checked']} citations, all resolving")

    interpreted = ["company", "people", "channels", "org"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": rl.now_iso(),
        "generator": "data_gen/phase1_company_grounding.py",
        "method": "roster, ownership and the login map measured from the mined record; "
                  "company, personas, voice and channels read off that evidence by a "
                  "model, with per-claim evidence and separate `inferred` blocks",
        "source": _source(args, grounding),
        **payload_body,
        "analysis": {
            "model": args.model,
            "effort": args.effort,
            "generated_at": rl.now_iso(),
            "interpreted_keys": interpreted,
            "measured_keys": ["services", "identity_map", "source"],
            "citation_check": citations,
            "leakage_check": {"patterns": len(patterns), "hits": leaks},
            "usage": {**llm.stats, "estimated_cost_usd": round(llm.cost(), 2)},
        },
    }

    size = rl.write_json(args.out, payload)
    rl.heading("Wrote")
    rl.ok(f"{args.out} ({rl.human_bytes(size)})")
    rl.info(f"{llm.stats['calls']} model calls, {llm.stats['cache_hits']} from cache, "
            f"~${llm.cost():.2f}")

    if not args.no_emit_world_data:
        for path, text in projections.items():
            write_projection(path, text, args.force, dry=False)

    for person in payload["people"][:12]:
        syn = person["synthetic"]
        owns = ", ".join(s["slug"] for s in person["services_owned"][:2]) or "-"
        rl.info(f"{syn['id']:14s} {syn['display_name']:22s} {syn['seniority']:11s} {owns}")
    return 0


def _source(args, grounding: dict) -> dict:
    return {
        "grounding_file": str(args.grounding),
        "grounding_sha256": sha16(args.grounding),
        "history_file": str(args.history),
        "history_sha256": sha16(args.history),
        "head_commit": grounding["source"]["head_commit"],
        "repo_remote": grounding["source"]["remote"],
    }


def _org_names(grounding: dict) -> list[str]:
    """The upstream organization's own names, which are not people but leak alike."""
    remote = grounding["source"]["remote"] or ""
    owner_repo = rl.parse_owner_repo(remote)
    names = []
    if owner_repo:
        owner, _ = owner_repo
        names += [owner, owner.replace("ai", ""), f"{owner}.ai"]
    package = grounding["configuration"].get("package_name") or ""
    if "-" in package or "." in package:
        names.append(package.split("-")[0].split(".")[0])
    return [n for n in names if len(n) >= 5]


if __name__ == "__main__":
    sys.exit(main())
