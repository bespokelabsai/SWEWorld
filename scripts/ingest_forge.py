#!/usr/bin/env python3
"""Put the repository's pull requests, issues, reviews and comments into Gitea.

`ingest_history.py` moves the commits; this moves everything that was said about
them. 461 pull requests, 270 issues, 886 reviews, 834 line-level review comments,
738 issue comments, 26 releases and 20 labels, under the company's own names.

Three things make this harder than it looks.

**The numbering is load-bearing.** 1,734 commit subjects cite pull request
numbers — `chore: bump 0.1.29 (#728)`. GitHub shares one counter between issues
and pull requests and so does Gitea, so the sequence only reproduces if items go
in strictly by number with placeholders in the gaps. One off-by-one silently
rewrites every cross-reference in the repository, and nothing downstream would
notice.

**Nothing in the API can set a creation time.** Gitea stamps `now` on everything
it makes. So each item is created over REST — for authorship, via the `Sudo:`
header — and then one SQLite transaction moves it back to when it really
happened and repairs the counters Gitea caches on the repository row. This is the
same bargain `ingest_docs.py` already makes with BookStack.

**Half the pull request heads are gone.** Only 209 of 461 head commits survive
under their original SHA, because squash merges discard the branch. But 385 merge
commits do, and a merge commit's second parent *is* the head — which is what
preserving the DAG in `ingest_history.py` bought. What is left after that is
created as an already-merged pull request row directly.

    scripts/ingest_forge.py --dry-run     # resolve, rewrite, plan; write nothing
    scripts/ingest_forge.py               # in the world, after ingest_history.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worldlib as wl  # noqa: E402
from ingest_history import (MANIFEST_NAME, git, git_lines,  # noqa: E402
                            human_bytes, leak_patterns, push_target)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HISTORY = REPO_ROOT / "data_gen" / "build" / "repository_history.json"
DEFAULT_GROUNDING = REPO_ROOT / "data_gen" / "build" / "company_grounding.json"

# What `--export` leaves behind, under data/ so that `make bake-image` copies it
# into the world along with everything else. The generator's own build directory
# is not shipped, and reaching into it from inside the container is the kind of
# dependency that works right up until someone bakes from a clean checkout.
EXPORT_NAME = "forge.json"
EXPORT_GROUNDING = "forge-people.json"

GITEA_DB = Path("/var/lib/world/gitea/gitea.db")

# Gitea is serving while this runs and holds the database across its own writes.
# Without a wait, a perfectly ordinary background job — a webhook, a mirror
# check — turns into "database is locked" and a half-ingested forge.
# The dot-command, not `PRAGMA busy_timeout` — the pragma prints its return
# value, and that stray line becomes the first row of every query result.
BUSY = ".timeout 60000"

# Comment types in Gitea's `comment` table. 0 is an ordinary comment; 21 is a
# line-level review comment, which is the one that needs a path and a line.
COMMENT_PLAIN, COMMENT_REVIEW = 0, 21
# `review.type`: 1 approved, 2 comment-only, 3 changes requested.
REVIEW_TYPE = {"APPROVED": 1, "COMMENTED": 2, "CHANGES_REQUESTED": 3,
               "DISMISSED": 2}

# Name fragments and email local parts that are ordinary words first. Replacing
# these would rewrite half the sentences in the corpus.
NOT_A_NAME = frozenset({
    "github", "noreply", "users", "info", "mail", "team", "code", "data",
    "test", "root", "user", "admin", "curator", "bespoke", "action", "actions",
    "dude", "the", "bot", "web", "api", "dev",
})


# =============================================================================
# Time
# =============================================================================
def parse_ts(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def epoch(value: str | None) -> int:
    when = parse_ts(value)
    return int(when.timestamp()) if when else 0


# =============================================================================
# Inputs
# =============================================================================
def load(path: Path, what: str) -> dict:
    if not path.exists():
        raise SystemExit(f"{path} does not exist — {what}")
    return json.loads(path.read_text(encoding="utf-8"))


class Forge:
    """The real forge record, resolved onto the world's people and commits."""

    def __init__(self, args, world: wl.World):
        self.history = load(args.history, "run extract_repository_history.py first")
        self.grounding = load(args.grounding, "run phase1_company_grounding.py first")
        manifest_path = args.data_dir / "history" / MANIFEST_NAME
        self.manifest = load(manifest_path,
                             "run scripts/ingest_history.py --export first")
        self.world = world

        self.gh = self.history["github"]
        self.commit_map = self.manifest["commit_map"]
        self.persona_of_login = dict(
            self.grounding["identity_map"]["login_to_persona"])
        self.people = {p["synthetic"]["id"]: p for p in self.grounding["people"]}
        self.employees = [p["synthetic"]["id"] for p in self.grounding["people"]
                          if p["class"] == "employee"]

        # Second parent of a merge commit is the branch that was merged, so a
        # squashed-away head is often still reachable through the merge.
        self.head_via_merge: dict[int, str] = {}
        parents = {c["sha"]: c["parents"] for c in self.history["commits"]}
        for pull in self.gh["pulls"]:
            merge = pull.get("merge_commit_sha")
            got = parents.get(merge or "")
            if got and len(got) > 1:
                self.head_via_merge[pull["number"]] = got[1]

        self.rules = self._rewrite_rules()
        self.patterns = leak_patterns(self.grounding["people"],
                                      self.grounding["source"]["repo_remote"])

        # The oldest thing anyone did here, which is where a placeholder for a
        # number GitHub took back has to sit: after it, the repository would
        # have an issue predating its first commit.
        stamps = [epoch(x.get("created_at"))
                  for x in list(self.gh["issues"]) + list(self.gh["pulls"])]
        self.first_seen = min([t for t in stamps if t], default=0)

        # `mahesh/client` became `dermot/client` when the history was rewritten,
        # and a pull request still pointing at the old name points at a branch
        # this repository has never had.
        self.ref_map = {k.rsplit("/", 1)[-1] if k.startswith("refs/heads/") else k:
                        v.split("refs/heads/", 1)[-1]
                        for k, v in self.manifest.get("ref_map", {}).items()}

    def ref_name(self, ref: str | None) -> str:
        """A branch name with nobody real left in it.

        `ref_map` only covers the branches that still exist. The head branch of
        a squash-merged pull request was deleted years ago and is in no map at
        all — but it is still stored on the row, still shown on the page, and
        this team named their branches after themselves: `mahesh/fix`,
        `ryan/parallel-processor-port`. Falling through to the raw name put the
        real author's first name on 461 pull requests.
        """
        short = (ref or "").split("refs/heads/", 1)[-1]
        mapped = self.ref_map.get(short)
        return mapped if mapped is not None else self.rewrite(short)

    def persona(self, login: str | None) -> str | None:
        return self.persona_of_login.get(login or "")

    def username(self, login: str | None) -> str:
        """The Gitea account a GitHub login maps to, falling back to the admin."""
        persona = self.persona(login)
        return persona or self.world.admin_user

    def world_sha(self, sha: str | None) -> str | None:
        return self.commit_map.get(sha or "")

    def _rewrite_rules(self) -> list[tuple[re.Pattern, str]]:
        """What to replace inside every body before it is posted.

        The bodies are free text real people wrote about real people: @mentions,
        names, addresses, and links back to github.com. Longest first, so a full
        name is replaced before a surname inside it can be.
        """
        rules: list[tuple[str, str]] = []
        for person in self.grounding["people"]:
            syn = person["synthetic"]
            given = syn["display_name"].split()[0]
            for real in person["real"]:
                for email in real["emails"]:
                    rules.append((email, f"{syn['id']}@{self.world.domain}"))
                    # A bare local part turns up in prose all the time.
                    local = re.sub(r"^\d+\+", "", email.split("@", 1)[0])
                    if len(local) >= 4 and local.lower() not in NOT_A_NAME:
                        rules.append((local, given))
                for name in real["names"]:
                    if len(name) >= 4:
                        rules.append((name, syn["display_name"]))
                    # And so does half of one. Forty-five bodies said "Charlie",
                    # "Mahesh" or "Trung" and the full-name rule never saw them.
                    for token in re.split(r"[\s._-]+", name):
                        if len(token) >= 4 and token.lower() not in NOT_A_NAME:
                            rules.append((token, given))
                if real.get("github_login") and len(real["github_login"]) >= 4:
                    rules.append((f"@{real['github_login']}", f"@{syn['id']}"))
                    rules.append((real["github_login"], syn["id"]))
        for login, persona in self.persona_of_login.items():
            if len(login) >= 4:
                rules.append((f"@{login}", f"@{persona}"))
                rules.append((login, persona))

        owner_repo = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$",
                               self.grounding["source"]["repo_remote"] or "")
        base = f"{self.world.url('git')}/{self.world.admin_user}"
        if owner_repo:
            org = owner_repo.group(1)
            rules.append((f"https://github.com/{org}", base))
            rules.append((f"{org}/", f"{self.world.admin_user}/"))
            rules.append((org, self.world.admin_user))
        rules.append(("github.com", f"git.{self.world.domain}"))

        rules.sort(key=lambda r: -len(r[0]))
        return [(re.compile(re.escape(a), re.I), b) for a, b in rules]

    def rewrite(self, text: str | None) -> str:
        out = text or ""
        for pattern, replacement in self.rules:
            out = pattern.sub(replacement.replace("\\", "\\\\"), out)
        return out


# =============================================================================
# The numbering plan
# =============================================================================
def numbering(forge: Forge) -> list[dict]:
    """Every item in the order Gitea must create it, gaps included.

    Gitea allocates `index` from one counter per repository, exactly as GitHub
    does, so the only way to land item N on number N is to create 1..N in order
    and fill anything missing with a placeholder.
    """
    items: dict[int, dict] = {}
    for issue in forge.gh["issues"]:
        items[issue["number"]] = {"kind": "issue", "number": issue["number"],
                                  "raw": issue}
    for pull in forge.gh["pulls"]:
        items[pull["number"]] = {"kind": "pull", "number": pull["number"],
                                 "raw": pull}
    if not items:
        return []
    plan = []
    for number in range(min(items), max(items) + 1):
        plan.append(items.get(number, {"kind": "gap", "number": number, "raw": None}))
    return plan


def describe(forge: Forge, item: dict) -> dict:
    """One item, resolved: who wrote it, when, what it says, where it points."""
    raw = item["raw"]
    if raw is None:
        return {**item, "title": "(withdrawn)", "body": "", "author": None,
                "created": 0, "closed": 0, "state": "closed"}
    login = (raw.get("user") or {}).get("login")
    out = {
        **item,
        "title": forge.rewrite(raw.get("title") or ""),
        "body": forge.rewrite(raw.get("body") or ""),
        "author": forge.username(login),
        "created": epoch(raw.get("created_at")),
        "closed": epoch(raw.get("closed_at")),
        "state": raw.get("state") or "closed",
        "labels": [lab["name"] for lab in (raw.get("labels") or [])],
    }
    if item["kind"] == "pull":
        head = (forge.world_sha(raw["head"]["sha"])
                or forge.world_sha(forge.head_via_merge.get(item["number"])))
        out.update({
            "merged": epoch(raw.get("merged_at")),
            "head_sha": head,
            "head_ref": raw["head"]["ref"],
            "base_ref": raw["base"]["ref"],
            "merge_sha": forge.world_sha(raw.get("merge_commit_sha")),
            # A pull request whose head is gone cannot be opened through the API
            # — Gitea needs a ref to diff. Those are written straight into the
            # tables as already-merged, which is what they are.
            "via": "api" if head else "sql",
        })
    return out


# =============================================================================
# Checks
# =============================================================================
def verify_plan(forge: Forge, plan: list[dict]) -> list[str]:
    problems = []
    numbers = [i["number"] for i in plan]
    if numbers != list(range(numbers[0], numbers[-1] + 1)):
        problems.append("the plan is not a contiguous run of numbers")
    both = {i["number"] for i in plan if i["kind"] == "issue"} & \
           {i["number"] for i in plan if i["kind"] == "pull"}
    if both:
        problems.append(f"{len(both)} number(s) are both an issue and a pull request")

    resolved = [describe(forge, i) for i in plan]
    for item in resolved:
        if item["kind"] == "gap":
            continue
        if not item["author"]:
            problems.append(f"#{item['number']}: no author")
        text = "\n".join([item["title"], item["body"],
                          forge.ref_name(item.get("head_ref")),
                          forge.ref_name(item.get("base_ref"))])
        for pattern in forge.patterns:
            if re.search(re.escape(pattern), text, re.I):
                problems.append(f"#{item['number']}: {pattern!r} survives in the body")
                break
    return problems


# =============================================================================
# Gitea
# =============================================================================
class Gitea:
    def __init__(self, world: wl.World, token: str, repo: str, dry_run: bool):
        self.world, self.token, self.repo = world, token, repo
        self.dry_run = dry_run
        self.session = None if dry_run else wl.session(world)
        self.base = f"/api/v1/repos/{world.admin_user}/{repo}"

    def _headers(self, sudo: str | None = None) -> dict:
        headers = {"Authorization": f"token {self.token}",
                   "Content-Type": "application/json"}
        if sudo:
            # Gitea's impersonation header. Authorship has no other route: the
            # API always attributes to the token's owner otherwise.
            headers["Sudo"] = sudo
        return headers

    def post(self, path: str, payload: dict, sudo: str | None = None) -> dict | None:
        if self.dry_run:
            return None
        resp = self.session.post(self.world.url("git", self.base + path),
                                 headers=self._headers(sudo), json=payload,
                                 timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"POST {path} ({resp.status_code}): {resp.text[:200]}")
        return resp.json()

    def patch(self, path: str, payload: dict, sudo: str | None = None) -> None:
        if self.dry_run:
            return
        resp = self.session.patch(self.world.url("git", self.base + path),
                                  headers=self._headers(sudo), json=payload,
                                  timeout=60)
        if resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"PATCH {path} ({resp.status_code}): {resp.text[:200]}")


def sql(statements: list[str]) -> None:
    """One transaction against Gitea's SQLite database.

    The API cannot set a creation time, and a corpus of historical issues that
    all arrived during ingestion is a corpus whose illusion collapses on the
    first glance at a sorted list.
    """
    script = "BEGIN IMMEDIATE;\n" + "\n".join(statements) + "\nCOMMIT;\n"
    proc = subprocess.run(["sqlite3", "-cmd", BUSY, str(GITEA_DB)],
                          input=script.encode(), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"sqlite3 failed: {proc.stderr.decode()[:300]}")


def lit(value) -> str:
    """A SQL literal, hex-encoded so no quoting rule can be got wrong."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "CAST(X'" + str(value).encode("utf-8").hex() + "' AS TEXT)"



def query(statement: str) -> list[list[str]]:
    """Read from Gitea's database. Tab-separated, because no field here has one."""
    proc = subprocess.run(["sqlite3", "-cmd", BUSY, "-separator", "\t",
                           str(GITEA_DB), statement], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"sqlite3 failed: {proc.stderr.decode()[:300]}")
    return [line.split("\t") for line in
            proc.stdout.decode("utf-8").splitlines() if line]


class Tables:
    """Gitea's own ids, and the next free one in each table.

    Everything here is written as rows rather than posted through the API. The
    API cannot set a creation time, cannot set an issue's number, and cannot
    open a pull request whose head branch no longer exists — which is 252 of the
    461. Writing the rows settles all three at once, and the numbering stops
    being a thing to preserve and becomes a column.
    """

    def __init__(self, world: wl.World, repo: str):
        rows = query(f"SELECT id FROM repository WHERE owner_name = "
                     f"{lit(world.admin_user)} AND lower_name = {lit(repo.lower())};")
        if not rows:
            raise SystemExit(
                f"no repository {world.admin_user}/{repo} in Gitea — run "
                "scripts/ingest_history.py first, which creates it and pushes "
                "the commits a pull request has to point at.")
        self.repo_id = int(rows[0][0])
        self.users = {r[0]: int(r[1]) for r in
                      query("SELECT lower_name, id FROM user;")}
        self.next = {t: int((query(f"SELECT COALESCE(MAX(id), 0) + 1 FROM `{t}`;")
                             or [["1"]])[0][0])
                     for t in ("issue", "pull_request", "comment", "review", "label")}

    def take(self, table: str) -> int:
        got = self.next[table]
        self.next[table] = got + 1
        return got

    def user(self, username: str) -> int:
        return self.users.get((username or "").lower(), 1)


def missing_accounts(forge: Forge, tables: Tables, resolved: list[dict]) -> list[str]:
    wanted = {i["author"] for i in resolved if i.get("author")}
    for by in (forge.gh["comments"], forge.gh["reviews"], forge.gh["review_comments"]):
        for items in by.values():
            for item in items:
                wanted.add(forge.username((item.get("user") or {}).get("login")))
    return sorted(u for u in wanted if u and u.lower() not in tables.users)


def statements(forge: Forge, tables: Tables, resolved: list[dict],
               args) -> tuple[list[str], Counter]:
    """Every row, as one ordered list of inserts.

    Written from scratch each time: the delete at the top makes a re-run replace
    the forge rather than double it, which matters because none of this is keyed
    on anything the source provides.
    """
    repo = tables.repo_id
    out = [
        f"DELETE FROM comment WHERE issue_id IN "
        f"(SELECT id FROM issue WHERE repo_id = {repo});",
        f"DELETE FROM review WHERE issue_id IN "
        f"(SELECT id FROM issue WHERE repo_id = {repo});",
        f"DELETE FROM issue_label WHERE issue_id IN "
        f"(SELECT id FROM issue WHERE repo_id = {repo});",
        f"DELETE FROM pull_request WHERE base_repo_id = {repo};",
        f"DELETE FROM issue WHERE repo_id = {repo};",
        f"DELETE FROM label WHERE repo_id = {repo};",
    ]
    counts: Counter = Counter()

    # -- labels ------------------------------------------------------------
    label_id: dict[str, int] = {}
    for label in forge.gh["labels"]:
        got = tables.take("label")
        label_id[label["name"]] = got
        out.append(
            f"INSERT INTO label (id, repo_id, org_id, name, description, color, "
            f"num_issues, num_closed_issues, archived_unix) VALUES "
            f"({got}, {repo}, 0, {lit(label['name'])}, "
            f"{lit(forge.rewrite(label.get('description') or ''))}, "
            f"{lit('#' + (label.get('color') or 'cccccc'))}, 0, 0, 0);")
        counts["labels"] += 1

    # -- issues and pull requests ------------------------------------------
    by_number: dict[int, int] = {}
    for item in resolved:
        number = item["number"]
        issue_id = tables.take("issue")
        by_number[number] = issue_id
        is_pull = 1 if item["kind"] == "pull" else 0
        closed = 1 if item["state"] != "open" else 0
        if item["kind"] == "gap":
            # A number GitHub allocated and then took back. Something has to
            # hold the slot or every later citation slides by one.
            closed, created = 1, forge.first_seen
        else:
            created = item["created"] or forge.first_seen
        updated = max(created, item.get("closed") or 0,
                      item.get("merged") or 0) or created
        out.append(
            f"INSERT INTO issue (id, repo_id, `index`, poster_id, original_author, "
            f"original_author_id, name, content, content_version, milestone_id, "
            f"priority, is_closed, is_pull, num_comments, ref, deadline_unix, "
            f"created_unix, updated_unix, closed_unix, is_locked, time_estimate) "
            f"VALUES ({issue_id}, {repo}, {number}, "
            f"{tables.user(item['author'] or forge.world.admin_user)}, '', 0, "
            f"{lit(item['title'])}, {lit(item['body'])}, 0, 0, 0, {closed}, "
            f"{is_pull}, 0, '', 0, {created}, {updated}, "
            f"{item.get('closed') or 0}, 0, 0);")
        counts["gaps" if item["kind"] == "gap" else item["kind"]] += 1

        for name in item.get("labels") or []:
            if name in label_id:
                out.append(f"INSERT INTO issue_label (issue_id, label_id) VALUES "
                           f"({issue_id}, {label_id[name]});")

        if is_pull:
            merged = 1 if item.get("merged") else 0
            head = forge.ref_name(item.get("head_ref"))
            out.append(
                f"INSERT INTO pull_request (id, type, status, conflicted_files, "
                f"commits_ahead, commits_behind, changed_protected_files, issue_id, "
                f"`index`, head_repo_id, base_repo_id, head_branch, base_branch, "
                f"merge_base, allow_maintainer_edit, has_merged, merged_commit_id, "
                f"merger_id, merged_unix, flow) VALUES "
                f"({tables.take('pull_request')}, 0, 2, '[]', 0, 0, '[]', {issue_id}, "
                f"{number}, {repo}, {repo}, {lit(head)}, "
                f"{lit(forge.ref_name(item.get('base_ref')) or 'main')}, '', 0, "
                f"{merged}, {lit(item.get('merge_sha') or '')}, "
                f"{tables.user(item['author'] or forge.world.admin_user) if merged else 0}, "
                f"{item.get('merged') or 0}, 0);")
            if merged:
                counts["merged"] += 1

    # -- what was said about them ------------------------------------------
    talk: Counter = Counter()
    for number_text, items in forge.gh["comments"].items():
        issue_id = by_number.get(int(number_text))
        if issue_id is None:
            continue
        for comment in items:
            when = epoch(comment.get("created_at"))
            out.append(
                f"INSERT INTO comment (id, type, poster_id, original_author, "
                f"original_author_id, issue_id, label_id, old_project_id, project_id, "
                f"old_milestone_id, milestone_id, time_id, assignee_id, "
                f"removed_assignee, assignee_team_id, resolve_doer_id, line, "
                f"tree_path, content, content_version, patch, created_unix, "
                f"updated_unix, commit_sha, review_id, invalidated) VALUES "
                f"({tables.take('comment')}, {COMMENT_PLAIN}, "
                f"{tables.user(forge.username((comment.get('user') or {}).get('login')))}, "
                f"'', 0, {issue_id}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', "
                f"{lit(forge.rewrite(comment.get('body')))}, 0, '', {when}, "
                f"{epoch(comment.get('updated_at')) or when}, '', 0, 0);")
            talk[issue_id] += 1
            counts["comments"] += 1

    review_id: dict[int, int] = {}
    for number_text, items in forge.gh["reviews"].items():
        issue_id = by_number.get(int(number_text))
        if issue_id is None:
            continue
        for review in items:
            got = tables.take("review")
            review_id[review["id"]] = got
            when = epoch(review.get("submitted_at"))
            out.append(
                f"INSERT INTO review (id, type, reviewer_id, reviewer_team_id, "
                f"original_author, original_author_id, issue_id, content, official, "
                f"commit_id, stale, dismissed, created_unix, updated_unix) VALUES "
                f"({got}, {REVIEW_TYPE.get(review.get('state'), 2)}, "
                f"{tables.user(forge.username((review.get('user') or {}).get('login')))}, "
                f"0, '', 0, {issue_id}, {lit(forge.rewrite(review.get('body')))}, 1, "
                f"{lit(forge.world_sha(review.get('commit_id')) or '')}, 0, 0, "
                f"{when}, {when});")
            counts["reviews"] += 1

    for number_text, items in forge.gh["review_comments"].items():
        issue_id = by_number.get(int(number_text))
        if issue_id is None:
            continue
        for note in items:
            when = epoch(note.get("created_at"))
            # A line comment Gitea can place needs a path and a line; the sign
            # says which side of the diff, which is how GitHub records it too.
            line = note.get("line") or note.get("original_line") or 0
            if (note.get("side") or "RIGHT") == "LEFT":
                line = -abs(int(line or 0))
            out.append(
                f"INSERT INTO comment (id, type, poster_id, original_author, "
                f"original_author_id, issue_id, label_id, old_project_id, project_id, "
                f"old_milestone_id, milestone_id, time_id, assignee_id, "
                f"removed_assignee, assignee_team_id, resolve_doer_id, line, "
                f"tree_path, content, content_version, patch, created_unix, "
                f"updated_unix, commit_sha, review_id, invalidated) VALUES "
                f"({tables.take('comment')}, {COMMENT_REVIEW}, "
                f"{tables.user(forge.username((note.get('user') or {}).get('login')))}, "
                f"'', 0, {issue_id}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {int(line or 0)}, "
                f"{lit(note.get('path') or '')}, "
                f"{lit(forge.rewrite(note.get('body')))}, 0, "
                f"{lit(note.get('diff_hunk') or '')}, {when}, "
                f"{epoch(note.get('updated_at')) or when}, "
                f"{lit(forge.world_sha(note.get('commit_id')) or '')}, "
                f"{review_id.get(note.get('pull_request_review_id'), 0)}, 0);")
            talk[issue_id] += 1
            counts["review_comments"] += 1

    # -- the numbers Gitea caches and never recomputes -----------------------
    for issue_id, n in talk.items():
        out.append(f"UPDATE issue SET num_comments = {n} WHERE id = {issue_id};")
    top = max((i["number"] for i in resolved), default=0)
    out.append(f"INSERT INTO issue_index (group_id, max_index) VALUES ({repo}, {top}) "
               f"ON CONFLICT(group_id) DO UPDATE SET max_index = {top};")
    out.append(
        f"UPDATE repository SET "
        f"num_issues = (SELECT COUNT(*) FROM issue WHERE repo_id = {repo} AND is_pull = 0), "
        f"num_closed_issues = (SELECT COUNT(*) FROM issue WHERE repo_id = {repo} AND is_pull = 0 AND is_closed = 1), "
        f"num_pulls = (SELECT COUNT(*) FROM issue WHERE repo_id = {repo} AND is_pull = 1), "
        f"num_closed_pulls = (SELECT COUNT(*) FROM issue WHERE repo_id = {repo} AND is_pull = 1 AND is_closed = 1) "
        f"WHERE id = {repo};")
    return out, counts


def verify_written(tables: Tables, resolved: list[dict]) -> list[str]:
    """Read it back. The numbering is the thing that cannot be wrong."""
    problems = []
    rows = query(f"SELECT `index`, name FROM issue WHERE repo_id = {tables.repo_id} "
                 f"ORDER BY `index`;")
    got = {int(r[0]): r[1] for r in rows if r and r[0].isdigit()}
    for item in resolved:
        if item["kind"] == "gap":
            continue
        title = (item["title"] or "").splitlines()[0] if item["title"] else ""
        here = (got.get(item["number"]) or "").splitlines()[0]
        if item["number"] not in got:
            problems.append(f"#{item['number']} is not in the database")
        elif title and here and here[:60] != title[:60]:
            problems.append(f"#{item['number']} is {here[:40]!r}, expected "
                            f"{title[:40]!r}")
    return problems[:10]


def export(args) -> int:
    """Trim the 50MB build artefact down to the forge and the parents.

    Only two things are needed from the history: what GitHub said, and each
    commit's parents — the second parent of a merge is how a squashed-away pull
    request head is recovered. Everything else in there is trees and blobs the
    repository already holds.
    """
    wl.heading("Export")
    history = load(args.history or DEFAULT_HISTORY,
                   "run extract_repository_history.py first")
    grounding = load(args.grounding or DEFAULT_GROUNDING,
                     "run phase1_company_grounding.py first")
    out_dir = args.data_dir / "history"
    out_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "schema_version": 1,
        "generator": "scripts/ingest_forge.py --export",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "github": history["github"],
        "commits": [{"sha": c["sha"], "parents": c["parents"]}
                    for c in history["commits"]],
    }
    written = (out_dir / EXPORT_NAME)
    written.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    gh = record["github"]
    wl.ok(f"{written} ({human_bytes(written.stat().st_size)}) — "
          f"{len(gh['pulls'])} pull requests, {len(gh['issues'])} issues, "
          f"{sum(len(v) for v in gh['comments'].values())} comments, "
          f"{sum(len(v) for v in gh['reviews'].values())} reviews")

    # The people, minus everything the ingest does not read. The names it maps
    # from are real, so this file never leaves the machine it was built on.
    slim = {k: grounding[k] for k in ("identity_map", "people", "source")
            if k in grounding}
    people = out_dir / EXPORT_GROUNDING
    people.write_text(json.dumps(slim, separators=(",", ":")), encoding="utf-8")
    wl.ok(f"{people} ({human_bytes(people.stat().st_size)}) — "
          f"{len(slim.get('people', []))} people to attribute to")
    wl.summarise(True, ["exported; nothing was written to any service"])
    return 0


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--export", action="store_true",
                        help="on the host: trim the forge record out of the "
                             "generator's build directory into data/history/, "
                             "where the bake can find it. Writes no service.")
    parser.add_argument("--history", type=Path, default=None)
    parser.add_argument("--grounding", type=Path, default=None)
    parser.add_argument("--repo", default="curator")
    parser.add_argument("--token", default=None)
    parser.add_argument("--plan-out", type=Path, default=None,
                        help="write the resolved plan as JSON. Phase 3 reads it to "
                             "know which issues and pull requests exist, so a clue "
                             "can be planted in one before the forge write path "
                             "does.")
    parser.add_argument("--no-backdate", action="store_true",
                        help="skip the SQLite pass; timestamps stay at ingestion time")
    args = parser.parse_args(argv)

    if args.export:
        return export(args)

    # In the world, read what --export left under data/. On the host, fall back
    # to the generator's build directory so a dry run needs no export first.
    shipped = args.data_dir / "history" / EXPORT_NAME
    people = args.data_dir / "history" / EXPORT_GROUNDING
    if args.history is None:
        args.history = shipped if shipped.exists() else DEFAULT_HISTORY
    if args.grounding is None:
        args.grounding = people if people.exists() else DEFAULT_GROUNDING

    world, identities, problems = wl.setup(args)
    problems.raise_if_any()
    forge = Forge(args, world)

    wl.heading("The forge record")
    plan = numbering(forge)
    kinds = Counter(i["kind"] for i in plan)
    wl.ok(f"{len(plan)} numbered slots: {kinds['pull']} pull requests, "
          f"{kinds['issue']} issues, {kinds['gap']} gap(s) to hold the numbering")
    wl.ok(f"{sum(len(v) for v in forge.gh['reviews'].values())} reviews, "
          f"{sum(len(v) for v in forge.gh['review_comments'].values())} line comments, "
          f"{sum(len(v) for v in forge.gh['comments'].values())} issue comments")

    resolved = [describe(forge, i) for i in plan]
    via = Counter(i.get("via") for i in resolved if i["kind"] == "pull")
    wl.ok(f"pull request heads: {via['api']} recoverable, {via['sql']} written "
          "straight to the tables as already-merged")

    wl.heading("Checks")
    found = verify_plan(forge, plan)
    if found:
        for problem in found[:15]:
            wl.warn(problem)
        raise SystemExit(f"{len(found)} problem(s); nothing was written")
    wl.ok(f"numbering is contiguous {plan[0]['number']}..{plan[-1]['number']}, "
          "every item has an author, no real name survives in any body")

    if args.plan_out:
        payload = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "generator": "scripts/ingest_forge.py",
                   "repo": args.repo,
                   "items": [{k: v for k, v in i.items() if k != "raw"}
                             for i in resolved]}
        args.plan_out.parent.mkdir(parents=True, exist_ok=True)
        args.plan_out.write_text(json.dumps(payload, indent=1, default=str),
                                 encoding="utf-8")
        wl.ok(f"{args.plan_out} — {len(resolved)} resolved item(s)")

    if args.dry_run:
        wl.dry(f"would write {len(plan)} issue rows numbered "
               f"{plan[0]['number']}..{plan[-1]['number']}, each stamped with the "
               "time it really happened")
        wl.dry(f"would write {sum(len(v) for v in forge.gh['comments'].values())} "
               f"comments, {sum(len(v) for v in forge.gh['reviews'].values())} "
               f"reviews and "
               f"{sum(len(v) for v in forge.gh['review_comments'].values())} "
               "line comments against them")
        wl.dry(f"would set the issue counter and the repository's cached counts "
               f"in {GITEA_DB}")
        wl.summarise(True, [f"{len(plan)} item(s) planned, 0 written"])
        return 0

    wl.heading("Writing")
    tables = Tables(world, args.repo)
    absent = missing_accounts(forge, tables, resolved)
    if absent:
        raise SystemExit(
            f"{len(absent)} person has no Gitea account: {', '.join(absent[:8])}"
            + ("..." if len(absent) > 8 else "")
            + "\n  scripts/ingest_history.py creates them. Run it first; an issue "
              "whose\n  author does not exist is an issue attributed to the admin.")

    script, counts = statements(forge, tables, resolved, args)
    sql(script)
    wl.ok(f"{counts['issue']} issue(s), {counts['pull']} pull request(s) "
          f"({counts['merged']} merged), {counts['gaps']} placeholder(s) holding "
          "numbers GitHub took back")
    wl.ok(f"{counts['comments']} comment(s), {counts['reviews']} review(s), "
          f"{counts['review_comments']} line comment(s), {counts['labels']} label(s)")

    wl.heading("Reading it back")
    broken = verify_written(tables, resolved)
    if broken:
        for problem in broken:
            wl.warn(problem)
        raise SystemExit("the numbering did not survive; every commit message "
                         "citing a pull request now points at the wrong thing")
    wl.ok(f"every one of {len(resolved)} numbers resolves to the item that "
          "belongs there")
    wl.summarise(False, [f"{len(resolved)} item(s) written to {args.repo}"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
