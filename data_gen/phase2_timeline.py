#!/usr/bin/env python3
"""Phase 2a — the project state, one day at a time.

Everything here is arithmetic over the mined record: which commits landed on a
day, which pull requests were open, what had shipped, who was in the building,
which files and symbols existed yet. No model, no network, and the same bytes on
every run — which is the point, because the conversation stage on top of it is
allowed to interpret and this is what it interprets.

Two things are worth knowing before reading the code.

**Days are the author's, not UTC's.** A Friday evening commit in California is
Saturday in UTC, and bucketing by UTC invents weekend work that never happened —
302 weekend commits against the 252 the authors' own calendars record. Ordering
and durations use UTC; day assignment does not.

**Nothing here decides what anyone said.** The output says a revert landed at
23:40 and that four people were active; whether that became a conversation is
Phase 2c's problem.

Writes `build/timeline.json`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

SCHEMA_VERSION = 1

DEFAULT_EPISODES = rl.DEFAULT_BUILD_DIR / "engineering_episodes.json"
DEFAULT_GROUNDING = rl.DEFAULT_BUILD_DIR / "engineering_grounding.json"
DEFAULT_HISTORY = rl.DEFAULT_BUILD_DIR / "repository_history.json"
DEFAULT_COMPANY = rl.DEFAULT_BUILD_DIR / "company_grounding.json"
DEFAULT_MANIFEST = rl.REPO_ROOT / "data" / "history" / "manifest.json"
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "timeline.json"

# The team-active window: 96% of all commits, and the only stretch where more
# than one person is present. Outside it the world still gets days, but they are
# marked thin and the conversation stage treats them differently.
RICH_FROM = dt.date(2024, 10, 27)
RICH_UNTIL = dt.date(2025, 7, 31)

# A person is away when they go this many working days without a commit, a
# review or a comment, inside their own tenure. All three matter: someone who
# spent a week only reviewing was at their desk, and a commit gap alone would
# file them as absent.
ABSENCE_WORKING_DAYS = 10

DOC_SUFFIXES = (".md", ".rst", ".txt")
INCIDENT_RE = re.compile(r"\brevert\b|hotfix|emergency|urgent|broken build|red main", re.I)


# =============================================================================
# Time
# =============================================================================
def parse_ts(value: str | None) -> dt.datetime | None:
    """ISO-8601 in either convention, as an aware datetime.

    The mined record mixes `...Z` and `...+05:30` inside the same field, so
    `fromisoformat` alone raises on half the corpus in older Pythons and string
    slicing quietly mixes two different calendars.
    """
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def local_day(value: str | None) -> dt.date | None:
    """The date on the author's own calendar."""
    when = parse_ts(value)
    return when.date() if when else None


def utc_day(value: str | None) -> dt.date | None:
    when = parse_ts(value)
    return when.astimezone(dt.timezone.utc).date() if when else None


def daterange(first: dt.date, last: dt.date):
    day = first
    while day <= last:
        yield day
        day += dt.timedelta(days=1)


def is_weekend(day: dt.date) -> bool:
    return day.weekday() >= 5


# =============================================================================
# Loading
# =============================================================================
def load(path: Path, what: str) -> dict:
    if not path.exists():
        rl.fail(f"{path} does not exist — {what}")
    return json.loads(path.read_text(encoding="utf-8"))


class Inputs:
    """Everything Phase 2a reads, joined on the keys that connect them."""

    def __init__(self, args):
        self.episodes_doc = load(args.episodes, "run build_episodes.py first")
        self.grounding = load(args.grounding, "run analyze_repository.py first")
        self.history = load(args.history, "run extract_repository_history.py first")
        self.company = load(args.company, "run phase1_company_grounding.py first")
        self.manifest = (json.loads(args.manifest.read_text(encoding="utf-8"))
                         if args.manifest.exists() else None)

        # Real contributor id -> persona id, and GitHub login -> persona id.
        self.persona_of = dict(self.company["identity_map"]["person_to_persona"])
        self.persona_of_login = dict(self.company["identity_map"]["login_to_persona"])
        self.people = {p["synthetic"]["id"]: p for p in self.company["people"]}
        self.employees = [p["synthetic"]["id"] for p in self.company["people"]
                          if p["class"] == "employee"]

        # Real commit sha -> the sha that exists in the world's Gitea. Without
        # the manifest the timeline still builds, but nothing it cites can be
        # opened by an agent, so say so rather than emitting dead references.
        self.world_sha = (self.manifest or {}).get("commit_map", {})

        self.subsystem_service = self._subsystem_service()
        self.service_channel = self._service_channel()

    def _subsystem_service(self) -> dict[str, list[str]]:
        """subsystem key -> the services that claim it (many-to-many)."""
        out: dict[str, list[str]] = defaultdict(list)
        for service in self.company["services"]:
            for package in service.get("packages") or []:
                out[package].append(service["slug"])
        return dict(out)

    def _service_channel(self) -> dict[str, str]:
        """service slug -> the channel that talks about it, where one does.

        Only a few services have a room of their own; the rest surface in the
        general engineering channel, which is what actually happens in a
        workspace this size.
        """
        out = {}
        for channel in self.company["channels"]:
            for cite in channel.get("evidence") or []:
                for service in self.company["services"]:
                    if service["slug"] in cite:
                        out.setdefault(service["slug"], channel["name"])
        return out

    def person(self, real_id: str | None) -> str | None:
        return self.persona_of.get(real_id or "")

    def login(self, login: str | None) -> str | None:
        return self.persona_of_login.get(login or "")


# =============================================================================
# Eras and the regime that went with them
# =============================================================================
def era_for(day: dt.date, eras: list[dict]) -> dict:
    month = f"{day.year:04d}-{day.month:02d}"
    for era in eras:
        if era["start_month"] <= month <= era["end_month"]:
            return {"slug": era["slug"], "name": era["name"]}
    return {"slug": "unknown", "name": "unknown"}


def quarterly_regime(episodes: list[dict]) -> dict[str, dict]:
    """How this team worked, by quarter, recomputed.

    `analyze_repository.py` builds these numbers in memory and only the prose
    quoting them survives into the grounding file. They are what makes a
    conversation era-accurate: "this has been sitting two days" is sayable in a
    quarter whose median merge was 26 hours and absurd in one where it was 1.1.
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    for ep in episodes:
        day = local_day(ep["timeline"]["merged_at"])
        if day:
            buckets[f"{day.year}-Q{(day.month - 1) // 3 + 1}"].append(ep)

    out = {}
    for key, eps in buckets.items():
        with_pr = [e for e in eps if (e["provenance"].get("pull_request"))]
        reviewed = [e for e in eps if e["metrics"].get("review_cycles") is not None
                    and (e["people"].get("reviewers") or [])]
        latency = [e["metrics"]["time_pr_open_to_merge_s"] for e in with_pr
                   if e["metrics"].get("time_pr_open_to_merge_s") is not None]
        styles = Counter(e["provenance"]["merge_style"] for e in eps)
        out[key] = {
            "episodes": len(eps),
            "pr_share": round(len(with_pr) / len(eps), 3) if eps else 0.0,
            "reviewed_share": round(len(reviewed) / len(eps), 3) if eps else 0.0,
            "median_merge_h": (round(statistics.median(latency) / 3600, 1)
                               if latency else None),
            "dominant_merge_style": styles.most_common(1)[0][0] if styles else None,
        }
    return out


# =============================================================================
# Episodes
# =============================================================================
def usable_episodes(doc: dict) -> list[dict]:
    """Chronological, deduplicated, and safe to fold.

    Two corrections. The file is sorted by a *string* compare on `merged_at`,
    which mixes `Z` and local offsets and leaves 33 adjacent pairs out of true
    order. And 101 episodes are re-reported inside an outer landing, so folding
    the list as it stands applies their file and symbol deltas twice.
    """
    episodes = [e for e in doc["episodes"]
                if not (e["provenance"].get("contained_by_episodes") or [])]
    episodes.sort(key=lambda e: (parse_ts(e["timeline"]["merged_at"])
                                 or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
                                 e["id"]))
    return episodes


# =============================================================================
# The running state of the codebase
# =============================================================================
class TreeState:
    """Which files and Python symbols exist, folded forward day by day.

    Keyed on `(path, symbol)` rather than symbol alone: symbol diffs are
    computed within one blob pair, so `LLM.__call__` in two different files is
    two different things and collapsing them would have one file's deletion
    erase the other's definition.
    """

    def __init__(self):
        self.files: set[str] = set()
        self.symbols: set[tuple[str, str]] = set()

    def apply(self, episode: dict) -> None:
        for f in episode.get("files") or []:
            path, status = f["path"], f.get("status")
            if status == "D":
                self.files.discard(path)
                self.symbols = {s for s in self.symbols if s[0] != path}
                continue
            if status == "R" and f.get("from_path"):
                old = f["from_path"]
                self.files.discard(old)
                moved = {s for s in self.symbols if s[0] == old}
                self.symbols -= moved
                self.symbols |= {(path, name) for _, name in moved}
            self.files.add(path)
            symbols = f.get("symbols")
            if not symbols:
                continue
            for name in symbols.get("removed") or []:
                self.symbols.discard((path, name))
            for name in (symbols.get("added") or []) + (symbols.get("modified") or []):
                self.symbols.add((path, name))

    def snapshot(self) -> dict:
        return {"files": len(self.files), "python_symbols": len(self.symbols)}


# =============================================================================
# Presence
# =============================================================================
def working_days_between(a: dt.date, b: dt.date) -> int:
    return sum(1 for d in daterange(a + dt.timedelta(days=1), b - dt.timedelta(days=1))
               if not is_weekend(d))


def presence(inputs: Inputs, active: dict[str, set[dt.date]]) -> dict[str, dict]:
    """Tenure and absences, per persona, from what they actually did.

    `active` is every day a persona committed, reviewed or commented — not just
    committed. A reviewer with an empty commit week was at work.
    """
    out = {}
    for persona, days in active.items():
        if not days:
            continue
        ordered = sorted(days)
        gaps = []
        for earlier, later in zip(ordered, ordered[1:]):
            if working_days_between(earlier, later) >= ABSENCE_WORKING_DAYS:
                gaps.append((earlier + dt.timedelta(days=1),
                             later - dt.timedelta(days=1)))
        out[persona] = {"first": ordered[0], "last": ordered[-1], "gaps": gaps,
                        "active_days": set(ordered)}
    return out


def state_of(persona: str, day: dt.date, record: dict | None) -> tuple[str, str]:
    if record is None:
        return "never-active", "no recorded activity anywhere in the history"
    if day < record["first"]:
        return "not-yet-joined", f"first active {record['first']}"
    if day > record["last"]:
        return "departed", f"last active {record['last']}"
    for start, end in record["gaps"]:
        if start <= day <= end:
            return "absent", f"no commit, review or comment {start}..{end}"
    return "present", ""


# =============================================================================
# Building the days
# =============================================================================
def build(inputs: Inputs, verbose: int = 0) -> dict:
    history, grounding = inputs.history, inputs.grounding
    episodes = usable_episodes(inputs.episodes_doc)
    regimes = quarterly_regime(episodes)
    eras = grounding["eras"]

    subsystem_of = _subsystem_resolver(grounding)

    commits_by_day: dict[dt.date, list[dict]] = defaultdict(list)
    for commit in history["commits"]:
        day = local_day(commit["author"]["date"])
        if day is None:
            continue
        persona = inputs.person(commit["author"]["person"])
        paths = [f["path"] for f in (commit.get("files") or [])]
        subsystems = sorted({subsystem_of(p) for p in paths} - {None})
        commits_by_day[day].append({
            "sha": commit["sha"][:12],
            "world_sha": (inputs.world_sha.get(commit["sha"]) or "")[:12],
            "persona": persona,
            "subject": commit["subject"],
            "is_merge": commit["is_merge"],
            "files": len(paths),
            "docs_touched": [p for p in paths if p.endswith(DOC_SUFFIXES)],
            "subsystems": subsystems,
            "services": sorted({s for sub in subsystems
                                for s in inputs.subsystem_service.get(sub, [])}),
            "at": commit["author"]["date"],
        })

    gh = history["github"]
    prs = {p["number"]: p for p in gh["pulls"]}
    issues = {i["number"]: i for i in gh["issues"]}

    opened_by_day = _by_day(gh["pulls"], "created_at")
    merged_by_day = _by_day([p for p in gh["pulls"] if p.get("merged_at")], "merged_at")
    issues_by_day = _by_day(gh["issues"], "created_at")
    releases_by_day = _by_day(gh["releases"], "published_at", "created_at")

    reviews_by_day: dict[dt.date, list[dict]] = defaultdict(list)
    for number, items in gh["reviews"].items():
        for review in items:
            day = utc_day(review.get("submitted_at"))
            if day:
                reviews_by_day[day].append({
                    "pr": int(number),
                    "persona": inputs.login((review.get("user") or {}).get("login")),
                    "state": review.get("state"),
                })
    comments_by_day: dict[dt.date, list[dict]] = defaultdict(list)
    for key in ("comments", "review_comments"):
        for number, items in gh[key].items():
            for comment in items:
                day = utc_day(comment.get("created_at"))
                if day:
                    comments_by_day[day].append({
                        "on": int(number),
                        "persona": inputs.login((comment.get("user") or {}).get("login")),
                        "kind": "review" if key == "review_comments" else "issue",
                    })

    # Every day a persona did anything at all — the basis for presence.
    active: dict[str, set[dt.date]] = defaultdict(set)
    for day, items in commits_by_day.items():
        for c in items:
            if c["persona"]:
                active[c["persona"]].add(day)
    for day, items in reviews_by_day.items():
        for r in items:
            if r["persona"]:
                active[r["persona"]].add(day)
    for day, items in comments_by_day.items():
        for c in items:
            if c["persona"]:
                active[c["persona"]].add(day)
    tenure = presence(inputs, active)

    episodes_by_day: dict[dt.date, list[dict]] = defaultdict(list)
    for ep in episodes:
        day = local_day(ep["timeline"]["merged_at"])
        if day:
            episodes_by_day[day].append(ep)

    # When each service first saw a commit — the basis for "this does not exist
    # yet", which is the one anachronism a reader spots instantly.
    service_born: dict[str, dt.date] = {}
    for day in sorted(commits_by_day):
        for commit in commits_by_day[day]:
            for service in commit["services"]:
                service_born.setdefault(service, day)
    all_services = sorted({s["slug"] for s in inputs.company["services"]})

    first = min(commits_by_day)
    last = max(commits_by_day)
    tree = TreeState()
    open_prs: dict[int, dict] = {}
    open_issues: dict[int, dict] = {}
    shipped: list[dict] = []

    # The end state, so "not yet" can be counted rather than only listed.
    final = TreeState()
    for ep in episodes:
        final.apply(ep)
    total_files, total_symbols = len(final.files), len(final.symbols)

    days = []
    for index, day in enumerate(daterange(first, last)):
        for ep in episodes_by_day.get(day, []):
            tree.apply(ep)

        for pr in opened_by_day.get(day, []):
            open_prs[pr["number"]] = {
                "number": pr["number"], "title": pr["title"],
                "persona": inputs.login((pr.get("user") or {}).get("login")),
                "opened": local_day(pr["created_at"]).isoformat(),
            }
        for pr in merged_by_day.get(day, []):
            open_prs.pop(pr["number"], None)
        for pr in gh["pulls"]:
            closed = utc_day(pr.get("closed_at"))
            if closed == day:
                open_prs.pop(pr["number"], None)
        for issue in issues_by_day.get(day, []):
            open_issues[issue["number"]] = {
                "number": issue["number"], "title": issue["title"],
                "persona": inputs.login((issue.get("user") or {}).get("login")),
            }
        for issue in gh["issues"]:
            if utc_day(issue.get("closed_at")) == day:
                open_issues.pop(issue["number"], None)
        for release in releases_by_day.get(day, []):
            shipped.append({"tag": release.get("tag_name"),
                            "date": day.isoformat()})

        commits = commits_by_day.get(day, [])
        merged = merged_by_day.get(day, [])
        reviews = reviews_by_day.get(day, [])
        comments = comments_by_day.get(day, [])
        releases = releases_by_day.get(day, [])

        people = []
        for persona in sorted(inputs.employees):
            status, reason = state_of(persona, day, tenure.get(persona))
            people.append({
                "persona": persona,
                "state": status,
                "reason": reason,
                "commits": sum(1 for c in commits if c["persona"] == persona),
                "reviews": sum(1 for r in reviews if r["persona"] == persona),
                "comments": sum(1 for c in comments if c["persona"] == persona),
            })

        quarter = f"{day.year}-Q{(day.month - 1) // 3 + 1}"
        incident = _incident_signal(commits, releases)
        days.append({
            "date": day.isoformat(),
            "weekday": day.strftime("%a"),
            "day_index": index,
            "is_weekend": is_weekend(day),
            "in_rich_window": RICH_FROM <= day <= RICH_UNTIL,
            "era": era_for(day, eras),
            "regime": regimes.get(quarter, {}),
            "activity": {
                "commits": commits,
                "episodes": [{"id": e["id"], "title": e["title"],
                              "change_type": e["change_type"]["primary"],
                              "persona": inputs.person(e["people"]["author"]),
                              "pr": (e["provenance"].get("pull_request") or {}).get("number")}
                             for e in episodes_by_day.get(day, [])],
                "prs_opened": [{"number": p["number"], "title": p["title"],
                                "persona": inputs.login((p.get("user") or {}).get("login"))}
                               for p in opened_by_day.get(day, [])],
                "prs_merged": [{"number": p["number"], "title": p["title"],
                                "persona": inputs.login((p.get("user") or {}).get("login"))}
                               for p in merged],
                "issues_opened": [{"number": i["number"], "title": i["title"],
                                   "persona": inputs.login((i.get("user") or {}).get("login"))}
                                  for i in issues_by_day.get(day, [])],
                "reviews": reviews,
                "comment_counts": Counter(c["kind"] for c in comments),
                "releases": [{"tag": r.get("tag_name"), "name": r.get("name")}
                             for r in releases],
                "docs_touched": sorted({p for c in commits for p in c["docs_touched"]}),
                "incident": incident,
            },
            "project_state": {
                "version": shipped[-1]["tag"] if shipped else None,
                "shipped": len(shipped),
                "open_prs": sorted(open_prs.values(), key=lambda p: p["number"]),
                "open_issues": sorted(open_issues.values(), key=lambda i: i["number"]),
                "tree": tree.snapshot(),
                "merged_to_date": sum(1 for d in days for _ in d["activity"]["prs_merged"])
                                  + len(merged),
            },
            "people": people,
            "speakable": {
                "services": sorted(s for s, born in service_born.items()
                                   if born <= day),
                "files": len(tree.files),
                "symbols": len(tree.symbols),
            },
            "forbidden": {
                "services_not_started": sorted(
                    s for s in all_services
                    if s not in service_born or service_born[s] > day),
                "files_not_yet": total_files - len(tree.files),
                "symbols_not_yet": total_symbols - len(tree.symbols),
                "entity_count": (total_files - len(tree.files)
                                 + total_symbols - len(tree.symbols)),
            },
        })
        if verbose and commits:
            rl.info(f"{day} {day.strftime('%a')}  {len(commits):3d} commits  "
                    f"{len(merged):2d} merged  {len(reviews):2d} reviews")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": rl.now_iso(),
        "generator": "data_gen/phase2_timeline.py",
        "method": "deterministic: every field folded from the mined record. "
                  "Days are assigned on the author's local calendar, not UTC.",
        "window": {
            "first": first.isoformat(), "last": last.isoformat(),
            "days": len(days),
            "rich_from": RICH_FROM.isoformat(), "rich_until": RICH_UNTIL.isoformat(),
        },
        "regimes": regimes,
        "totals": _totals(days, history),
        "days": days,
    }


def _subsystem_resolver(grounding: dict):
    """path -> subsystem key, longest prefix wins, memoised.

    Called once per file per commit — a few thousand paths against 44 subsystems
    with several paths each — so the cache is the difference between a second
    and a minute.
    """
    prefixes: list[tuple[str, str]] = []
    for sub in grounding["subsystems"]:
        for known in sub["paths"]:
            prefix = known.rsplit("/", 1)[0] + "/" if "/" in known else known
            prefixes.append((prefix, sub["key"]))
    prefixes.sort(key=lambda pair: -len(pair[0]))
    cache: dict[str, str] = {}

    def resolve(path: str) -> str:
        hit = cache.get(path)
        if hit is None:
            hit = next((key for prefix, key in prefixes if path.startswith(prefix)),
                       "other")
            cache[path] = hit
        return hit
    return resolve


def _by_day(items, *fields) -> dict[dt.date, list[dict]]:
    out: dict[dt.date, list[dict]] = defaultdict(list)
    for item in items:
        value = next((item.get(f) for f in fields if item.get(f)), None)
        day = utc_day(value)
        if day:
            out[day].append(item)
    return out


def _incident_signal(commits: list[dict], releases: list[dict]) -> dict | None:
    """Did something break today, by a standard the reader can check?

    Deliberately narrow. A `.postN` tag is a hotfix by construction, and a
    commit subject saying "revert" is saying it in the team's own words. Anything
    looser starts calling ordinary bugfix days incidents, and once every day is
    an incident none of them are.
    """
    reverts = [c for c in commits if INCIDENT_RE.search(c["subject"] or "")]
    hotfix = [r for r in releases if ".post" in (r.get("tag_name") or "")]
    if not reverts and not hotfix:
        return None
    return {
        "kind": "hotfix-release" if hotfix else "revert",
        "commits": [c["sha"] for c in reverts][:5],
        "tags": [r.get("tag_name") for r in hotfix],
        "evidence": ([c["subject"][:80] for c in reverts][:3]
                     or [r.get("tag_name") for r in hotfix]),
    }


def _totals(days: list[dict], history: dict) -> dict:
    commits = sum(len(d["activity"]["commits"]) for d in days)
    weekend = sum(len(d["activity"]["commits"]) for d in days if d["is_weekend"])
    return {
        "commits": commits,
        "commits_in_history": len(history["commits"]),
        "weekend_commits": weekend,
        "active_days": sum(1 for d in days if d["activity"]["commits"]),
        "days_with_any_activity": sum(
            1 for d in days
            if d["activity"]["commits"] or d["activity"]["prs_opened"]
            or d["activity"]["reviews"] or d["activity"]["releases"]),
        "incident_days": sum(1 for d in days if d["activity"]["incident"]),
        "weekend_incident_days": sum(1 for d in days
                                     if d["is_weekend"] and d["activity"]["incident"]),
    }


# =============================================================================
# Checks
# =============================================================================
def verify(doc: dict, inputs: Inputs) -> list[str]:
    problems = []
    totals = doc["totals"]
    if totals["commits"] != totals["commits_in_history"]:
        problems.append(f"{totals['commits']} commits across the days but "
                        f"{totals['commits_in_history']} in the history")
    # The cheapest proof that day assignment is not silently running on UTC.
    if totals["weekend_commits"] != 252:
        problems.append(f"{totals['weekend_commits']} weekend commits; the authors' "
                        "own calendars say 252 (302 means UTC bucketing crept back)")
    gh = inputs.history["github"]
    for name, seen, expected in (
        ("pull requests", sum(len(d["activity"]["prs_opened"]) for d in doc["days"]),
         len(gh["pulls"])),
        ("issues", sum(len(d["activity"]["issues_opened"]) for d in doc["days"]),
         len(gh["issues"])),
        ("releases", sum(len(d["activity"]["releases"]) for d in doc["days"]),
         len(gh["releases"])),
    ):
        if seen != expected:
            problems.append(f"{seen} {name} across the days but {expected} in the history")

    for day in doc["days"]:
        for person in day["people"]:
            if person["state"] in ("not-yet-joined", "departed") and (
                    person["commits"] or person["reviews"] or person["comments"]):
                problems.append(f"{day['date']}: {person['persona']} is "
                                f"{person['state']} but has activity")
    return problems


def verify_tree(doc: dict, inputs: Inputs, repo: Path, sample: int) -> list[str]:
    """Spot-check the folded file set against the real tree.

    The fold is a delta replay and the tree is ground truth; where they disagree
    the fold is wrong. Sampled rather than exhaustive because it is one `git
    ls-tree` per date.
    """
    episodes = usable_episodes(inputs.episodes_doc)
    by_day: dict[str, str] = {}
    for ep in episodes:
        day = local_day(ep["timeline"]["merged_at"])
        if day:
            by_day[day.isoformat()] = ep["state"]["after"]["commit"]
    dates = sorted(by_day)
    if not dates:
        return ["no episode has a usable merge date"]
    step = max(1, len(dates) // sample)
    problems = []
    for date in dates[::step][:sample]:
        sha = by_day[date]
        proc = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", sha],
            capture_output=True, text=True)
        if proc.returncode != 0:
            problems.append(f"{date}: {sha[:12]} not in {repo}")
            continue
        real = {p for p in proc.stdout.splitlines() if p}
        day = next((d for d in doc["days"] if d["date"] == date), None)
        if day is None:
            continue
        folded = day["project_state"]["tree"]["files"]
        drift = abs(folded - len(real)) / max(len(real), 1)
        if drift > 0.15:
            problems.append(f"{date}: folded {folded} files, tree has {len(real)} "
                            f"({drift:.0%} apart)")
    return problems


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--episodes", type=Path, default=DEFAULT_EPISODES)
    parser.add_argument("--grounding", type=Path, default=DEFAULT_GROUNDING)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--company", type=Path, default=DEFAULT_COMPANY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--repo", type=Path, default=rl.DEFAULT_REPO)
    parser.add_argument("--verify-tree", type=int, default=0, metavar="N",
                        help="spot-check the folded file set against N real trees")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    rl.heading("Reading")
    inputs = Inputs(args)
    rl.ok(f"{len(inputs.episodes_doc['episodes'])} episodes, "
          f"{len(inputs.history['commits'])} commits, "
          f"{len(inputs.people)} personas, {len(inputs.company['channels'])} channels")
    if inputs.manifest is None:
        rl.warn(f"{args.manifest} not found — commits will carry no world SHA, so "
                "nothing the specs cite can be opened in Gitea. Run "
                "scripts/ingest_history.py --export.")

    rl.heading("Folding")
    doc = build(inputs, args.verbose)
    w = doc["window"]
    t = doc["totals"]
    rl.ok(f"{w['days']} days, {w['first']}..{w['last']}")
    rl.ok(f"{t['active_days']} days with commits, {t['days_with_any_activity']} with "
          f"any activity, {t['incident_days']} incidents "
          f"({t['weekend_incident_days']} at a weekend)")

    rl.heading("Checks")
    problems = verify(doc, inputs)
    if problems:
        for problem in problems[:20]:
            rl.warn(problem)
        rl.fail(f"{len(problems)} problem(s); nothing was written")
    rl.ok(f"{t['commits']} commits, {t['weekend_commits']} of them at a weekend on "
          "the authors' own calendars")
    rl.ok("every pull request, issue and release accounted for; nobody active "
          "outside their tenure")

    if args.verify_tree:
        drift = verify_tree(doc, inputs, args.repo, args.verify_tree)
        for problem in drift[:10]:
            rl.warn(problem)
        if not drift:
            rl.ok(f"folded file set agrees with {args.verify_tree} real trees")

    size = rl.write_json(args.out, doc)
    rl.heading("Wrote")
    rl.ok(f"{args.out} ({rl.human_bytes(size)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
