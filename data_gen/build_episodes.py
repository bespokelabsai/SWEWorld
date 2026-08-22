#!/usr/bin/env python3
"""Turn raw git history into engineering episodes.

Writes `data_gen/build/engineering_episodes.json`.

An episode is one coherent unit of engineering work, not one commit. The unit
this models is the shape work actually takes:

    issue -> branch -> commit A -> commit B -> PR opened -> review ->
    commit C -> approval -> merge

all of which collapses into a single EngineeringEpisode carrying every piece of
that provenance. A pull request is therefore the primary anchor: its branch
commits, its reviews, its linked issues and its merge are one episode. Commits
that never went through a PR — most of this repository's first months — are
grouped into episodes by author, time and touched paths along the first-parent
line, so that their before/after states are still exact states of the branch.

Review cycles, reviewer identity and issue-open times exist nowhere in a git
clone. They are GitHub state, so this script needs a token. Every response is
cached under `data_gen/cache/github/`, and once the cache is warm `--no-refresh`
re-runs the whole thing offline.

    GITHUB_TOKEN=ghp_... python3 data_gen/build_episodes.py -v
    python3 data_gen/build_episodes.py --no-refresh      # from cache, no network
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402
from github_api import GitHub, MissingFromCache  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "engineering_episodes.json"
GROUP_WINDOW_HOURS = 24
GROUP_MAX_COMMITS = 10

# `feat: add native Azure OpenAI batch backend (#538) (#727)` — the last group
# is the PR that landed it; anything earlier is a referenced issue.
_TRAILING_REF_RE = re.compile(r"\(#(\d+)\)\s*$")
_MERGE_PR_RE = re.compile(r"^Merge pull request #(\d+) from ([^\s]+)")
_ANY_REF_RE = re.compile(r"#(\d+)")
_CLOSES_RE = re.compile(r"\b(?:clos(?:e|es|ed)|fix(?:es|ed)?|resolv(?:e|es|ed))\s+#(\d+)", re.I)
_REVERT_RE = re.compile(r'^Revert\s+"(.+)"\s*$')


# =============================================================================
# Diffs
# =============================================================================
_RAW_RE = re.compile(
    r"^:(?P<mode_a>\d+)\s+(?P<mode_b>\d+)\s+(?P<blob_a>[0-9a-f]+)\s+(?P<blob_b>[0-9a-f]+)\s+"
    r"(?P<status>[A-Z])(?P<score>\d*)\t(?P<rest>.*)$"
)


def diff_files(git: rl.Git, before: str, after: str) -> list[dict]:
    """Every file changed between two revisions, with blob identity.

    `--raw` carries the before/after blob SHAs, which is what makes the
    repository state reconstructible without embedding file contents;
    `--numstat` carries the line counts. Both are needed, and they are
    separate outputs.
    """
    raw = git.run("diff", "--raw", "-M", "--abbrev=40", before, after, check=False)
    numstat = git.run("diff", "--numstat", "-M", before, after, check=False)

    counts: dict[str, tuple[int, int, bool]] = {}
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if " => " in path or "{" in path:
            m = re.match(r"^(.*)\{(.*) => (.*)\}(.*)$", path)
            path = f"{m.group(1)}{m.group(3)}{m.group(4)}".replace("//", "/") if m \
                else path.split(" => ")[-1]
        counts[path] = (int(added) if added.isdigit() else 0,
                        int(deleted) if deleted.isdigit() else 0,
                        not added.isdigit())

    files = []
    for line in raw.splitlines():
        m = _RAW_RE.match(line)
        if not m:
            continue
        status = m.group("status")
        rest = m.group("rest").split("\t")
        from_path, path = (rest[0], rest[1]) if len(rest) > 1 else (None, rest[0])
        added, deleted, binary = counts.get(path, (0, 0, False))
        files.append({
            "path": path,
            "from_path": from_path,
            "status": status,
            "similarity": int(m.group("score")) if m.group("score") else None,
            "blob_before": None if m.group("blob_a") == "0" * 40 else m.group("blob_a"),
            "blob_after": None if m.group("blob_b") == "0" * 40 else m.group("blob_b"),
            "mode_after": None if m.group("mode_b") == "000000" else m.group("mode_b"),
            "lines_added": added,
            "lines_deleted": deleted,
            "binary": binary,
        })
    return files


def annotate_files(git: rl.Git, subs: rl.SubsystemMap, files: list[dict],
                   with_symbols: bool) -> list[dict]:
    """Add subsystem, language, size and — for Python — changed symbols."""
    wanted: list[str] = []
    if with_symbols:
        for entry in files:
            if entry["path"].endswith(".py") and not entry["binary"]:
                wanted += [b for b in (entry["blob_before"], entry["blob_after"]) if b]
    blobs = git.read_objects(sorted(set(wanted))) if wanted else {}

    for entry in files:
        entry["subsystem"] = subs.of(entry["path"])
        entry["role"] = rl.file_role(entry["path"])
        entry["language"] = rl.language_of(entry["path"])
        after = blobs.get(entry["blob_after"] or "")
        entry["size_after"] = len(after.encode()) if after is not None else None
        if with_symbols and entry["path"].endswith(".py") and not entry["binary"]:
            entry["symbols"] = rl.diff_symbols(blobs.get(entry["blob_before"] or ""), after)
        else:
            entry["symbols"] = None
    return files


# =============================================================================
# GitHub state
# =============================================================================
class GitHubState:
    """The PRs, reviews and issues this repository's history refers to.

    Stage 0 (`extract_repository_history.py`) is what actually talks to GitHub;
    this normally just reads its record. The live-API constructor is kept for a
    standalone run, but the two produce the same four maps so nothing
    downstream can tell them apart.
    """

    def __init__(self, pulls: dict, issues: dict, reviews: dict,
                 pr_commits: dict, source: str, gh: GitHub | None = None):
        self.pulls, self.issues = pulls, issues
        self.reviews, self.pr_commits = reviews, pr_commits
        self.source, self.gh = source, gh

    @classmethod
    def from_history(cls, doc: dict) -> "GitHubState":
        github = doc["github"]
        pulls = {pr["number"]: pr for pr in github["pulls"]}
        issues = {issue["number"]: issue for issue in github["issues"]}
        # JSON object keys are strings; the rest of this file indexes by number.
        reviews = {int(k): v for k, v in github["reviews"].items()}
        pr_commits = {int(k): v for k, v in github["pull_commits"].items()}
        rl.ok(f"{len(pulls)} pull requests, {len(issues)} issues, "
              f"reviews for {len(reviews)} — from the Stage 0 record")
        return cls(pulls, issues, reviews, pr_commits, source="repository_history.json")

    @classmethod
    def from_api(cls, gh: GitHub, verbose: int = 0) -> "GitHubState":
        rl.info("fetching pull requests...")
        pulls = {pr["number"]: pr for pr in gh.pulls()}
        rl.ok(f"{len(pulls)} pull requests")

        rl.info("fetching issues...")
        issues = {issue["number"]: issue for issue in gh.issues()
                  if "pull_request" not in issue}
        rl.ok(f"{len(issues)} issues (pull requests excluded)")

        reviews: dict[int, list[dict]] = {}
        pr_commits: dict[int, list[dict]] = {}
        merged = [n for n, pr in pulls.items() if pr.get("merged_at")]
        rl.info(f"fetching reviews and commits for {len(merged)} merged pull requests...")
        for i, number in enumerate(sorted(merged), 1):
            reviews[number] = gh.pull_reviews(number)
            pr_commits[number] = gh.pull_commits(number)
            if verbose and i % 50 == 0:
                rl.info(f"  {i}/{len(merged)}")
        rl.ok(f"reviews and commits for {len(merged)} pull requests")
        return cls(pulls, issues, reviews, pr_commits, source="github-api", gh=gh)


def review_metrics(reviews: list[dict], pr_commits: list[dict]) -> dict:
    """Reviewer behaviour, and how many times the work went back for changes.

    A review cycle is a CHANGES_REQUESTED review that was actually answered
    with more commits — a rejection at the end of a PR's life is not a cycle,
    it is how it died.
    """
    commit_dates = sorted(
        filter(None, ((c.get("commit", {}).get("committer") or {}).get("date")
                      for c in pr_commits))
    )
    by_reviewer: dict[str, dict] = {}
    approvals = changes_requested = comments = cycles = 0
    for review in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        state = review.get("state", "")
        login = ((review.get("user") or {}).get("login")) or "unknown"
        entry = by_reviewer.setdefault(login, {"login": login, "states": [], "reviews": 0})
        entry["reviews"] += 1
        if state not in entry["states"]:
            entry["states"].append(state)
        if state == "APPROVED":
            approvals += 1
        elif state == "CHANGES_REQUESTED":
            changes_requested += 1
            when = review.get("submitted_at")
            if when and any(d > when for d in commit_dates):
                cycles += 1
        elif state == "COMMENTED":
            comments += 1

    return {
        "reviewers": sorted(by_reviewer.values(), key=lambda r: -r["reviews"]),
        "approvals": approvals,
        "changes_requested": changes_requested,
        "comment_reviews": comments,
        "review_cycles": cycles,
        "reviewed": bool(reviews),
        "first_review_at": min((r.get("submitted_at") for r in reviews
                                if r.get("submitted_at")), default=None),
    }


# =============================================================================
# Episode assembly
# =============================================================================
class Builder:
    def __init__(self, git: rl.Git, state: GitHubState | None, rev: str,
                 since: str | None, until: str | None, with_symbols: bool):
        self.git, self.state = git, state
        self.with_symbols = with_symbols
        self.commits = rl.load_commits(git, rev=rev, since=since, until=until)
        self.by_sha = {c.sha: c for c in self.commits}
        self.ids = rl.Identities.from_commits(self.commits)
        self.subs = rl.SubsystemMap(git, rev)
        self.first_parent = [
            sha for sha in reversed(git.lines("rev-list", "--first-parent", rev))
            if sha in self.by_sha
        ]
        self.login_to_person = {
            p.github_login.lower(): p.id
            for p in self.ids.people.values() if p.github_login
        }
        self.assigned: set[str] = set()
        self.gaps: Counter[str] = Counter()

    # -- helpers -------------------------------------------------------------
    def person(self, commit: rl.Commit) -> str | None:
        return self.ids.of(commit.author_name, commit.author_email)

    def person_for_login(self, login: str | None) -> str | None:
        return self.login_to_person.get((login or "").lower())

    def branch_commits(self, merge: rl.Commit) -> list[str]:
        """Commits a merge brought in, oldest first."""
        if len(merge.parents) < 2:
            return []
        span = f"{merge.parents[0]}..{merge.parents[1]}"
        return [s for s in reversed(self.git.lines("rev-list", span)) if s in self.by_sha]

    def parent_of(self, sha: str) -> str:
        commit = self.by_sha[sha]
        return commit.parents[0] if commit.parents else rl.EMPTY_TREE

    # -- PR-anchored ---------------------------------------------------------
    def pr_episodes(self) -> list[dict]:
        if not self.state:
            return []
        episodes = []
        merged = [pr for pr in self.state.pulls.values() if pr.get("merged_at")]
        merged.sort(key=lambda pr: pr["merged_at"])
        for pr in merged:
            merge_sha = pr.get("merge_commit_sha")
            anchor = merge_sha if merge_sha in self.by_sha else None
            api_shas = [c["sha"] for c in self.state.pr_commits.get(pr["number"], [])]
            local_api = [s for s in api_shas if s in self.by_sha]

            if anchor:
                commit = self.by_sha[anchor]
                if commit.is_merge:
                    shas = self.branch_commits(commit) + [anchor]
                    style = "merge-commit"
                else:
                    shas = [anchor]
                    style = "squash-or-rebase"
                before, after = self.parent_of(anchor), anchor
            elif local_api:
                # The merge commit is not in this clone (rebase-merge rewrites
                # SHAs), but the branch commits landed individually.
                shas = [s for s in self.first_parent if s in set(local_api)] or local_api
                before, after = self.parent_of(shas[0]), shas[-1]
                style = "rebase-merge"
                self.gaps["merge commit absent from the clone"] += 1
            else:
                self.gaps["pull request has no commit in this clone"] += 1
                continue

            fresh = [s for s in shas if s not in self.assigned]
            episodes.append(self._episode(
                shas=shas, fresh=fresh, before=before, after=after, pr=pr,
                style=style, api_commit_count=len(api_shas), rule=f"pr-{style}",
            ))
            self.assigned.update(shas)
        return episodes

    # -- leftovers -----------------------------------------------------------
    def leftover_episodes(self) -> list[dict]:
        """Group commits that never went through a pull request.

        Runs are taken along the first-parent line so that each episode's
        before/after is a real state of the branch and the diffs of two
        episodes never overlap.
        """
        episodes: list[dict] = []
        pending = [s for s in self.first_parent if s not in self.assigned]
        index = 0
        while index < len(pending):
            run = [pending[index]]
            index += 1
            while index < len(pending) and len(run) < GROUP_MAX_COMMITS:
                if not self._same_effort(run, pending[index]):
                    break
                # Only extend across commits that are adjacent on the branch;
                # a gap means another episode landed in between.
                if self.first_parent.index(pending[index]) != \
                        self.first_parent.index(run[-1]) + 1:
                    break
                run.append(pending[index])
                index += 1

            shas: list[str] = []
            for sha in run:
                commit = self.by_sha[sha]
                if commit.is_merge:
                    shas += self.branch_commits(commit)
                shas.append(sha)
            episodes.append(self._episode(
                shas=shas, fresh=[s for s in shas if s not in self.assigned],
                before=self.parent_of(run[0]), after=run[-1], pr=None,
                style="direct", api_commit_count=None,
                rule="heuristic-run" if len(run) > 1 else "single-commit",
            ))
            self.assigned.update(shas)
        return episodes

    def _same_effort(self, run: list[str], candidate: str) -> bool:
        head, nxt = self.by_sha[run[-1]], self.by_sha[candidate]
        if self.person(head) != self.person(nxt):
            return False
        gap = rl.seconds_between(head.authored_at, nxt.authored_at)
        if gap is None or gap > GROUP_WINDOW_HOURS * 3600:
            return False
        shared = set(head.paths) & set(nxt.paths)
        same_kind = (rl.classify_change(head.paths, head.subject, head.body)["primary"] ==
                     rl.classify_change(nxt.paths, nxt.subject, nxt.body)["primary"])
        return bool(shared) or same_kind

    # -- one episode ---------------------------------------------------------
    def _episode(self, *, shas: list[str], fresh: list[str], before: str, after: str,
                 pr: dict | None, style: str, api_commit_count: int | None,
                 rule: str) -> dict:
        commits = [self.by_sha[s] for s in shas if s in self.by_sha]
        real = [c for c in commits if not c.is_merge] or commits
        head = self.by_sha[after]

        files = annotate_files(self.git, self.subs,
                               diff_files(self.git, before, after), self.with_symbols)

        subject = pr["title"] if pr else head.subject
        body = (pr.get("body") or "") if pr else "\n\n".join(c.body for c in real)
        branch = (pr.get("head") or {}).get("ref") if pr else None
        if not branch and head.is_merge:
            m = _MERGE_PR_RE.match(head.subject)
            branch = m.group(2) if m else None

        change_type = rl.classify_change([f["path"] for f in files], subject, body or "", branch)

        author_login = ((pr or {}).get("user") or {}).get("login")
        authors = Counter(filter(None, (self.person(c) for c in real)))
        coauthors = sorted({
            self.ids.of(name, email) or name
            for c in real for name, email in c.coauthors()
        })

        metrics = review_metrics(
            self.state.reviews.get(pr["number"], []) if (pr and self.state) else [],
            self.state.pr_commits.get(pr["number"], []) if (pr and self.state) else [],
        ) if pr else {"reviewers": [], "approvals": 0, "changes_requested": 0,
                      "comment_reviews": 0, "review_cycles": 0, "reviewed": False,
                      "first_review_at": None}

        issues = self._linked_issues(pr, head)
        opened_at = pr.get("created_at") if pr else None
        first_commit_at = min((c.authored_at for c in real), default=head.authored_at)
        merged_at = pr.get("merged_at") if pr else head.committed_at
        # An issue filed *after* the PR is a follow-up, not the thing that
        # prompted the work; counting it would report a negative lead time.
        issue_opened = min((i["opened_at"] for i in issues
                            if i["opened_at"] and (not opened_at or i["opened_at"] <= opened_at)),
                           default=None)

        distribution = {
            "by_subsystem": dict(Counter(f["subsystem"] for f in files).most_common()),
            "by_language": dict(Counter(f["language"] for f in files).most_common()),
            "by_role": dict(Counter(f["role"] for f in files).most_common()),
            "by_status": dict(Counter(f["status"] for f in files).most_common()),
        }

        gaps = []
        if pr and style == "squash-or-rebase" and api_commit_count and api_commit_count > 1:
            gaps.append("branch commits are not in this clone: squash-merged pull request")
        if not pr:
            gaps.append("no pull request: review and issue provenance unavailable")
        if len(fresh) != len(shas):
            gaps.append("shares commits with an earlier episode; see "
                        "provenance.contains_episodes")

        return {
            "id": f"ep-{after[:12]}",
            "title": subject,
            "objective": _objective(body, real),
            "change_type": change_type,
            "provenance": {
                "grouping_rule": rule,
                "merge_style": style,
                "branch": branch,
                "pull_request": {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr.get("html_url"),
                    "state": pr.get("state"),
                    "author_login": author_login,
                    "author_person": self.person_for_login(author_login),
                    "opened_at": opened_at,
                    "merged_at": pr.get("merged_at"),
                    "merged_by": ((pr.get("merged_by") or {}).get("login")),
                    "base": (pr.get("base") or {}).get("ref"),
                    "labels": [lbl["name"] for lbl in pr.get("labels", [])],
                    "draft": pr.get("draft"),
                    "commits_on_branch": api_commit_count,
                } if pr else None,
                "issues": issues,
                "contains_episodes": [],
                "contained_by_episodes": [],
                "source_commits": [
                    {"sha": c.sha, "subject": c.subject,
                     "author": self.person(c), "authored_at": c.authored_at,
                     "is_merge": c.is_merge,
                     "first_in_episode": c.sha in fresh}
                    for c in commits
                ],
            },
            "state": {
                "before": {"commit": None if before == rl.EMPTY_TREE else before,
                           "tree": self.git.tree_of(before)},
                "after": {"commit": after, "tree": self.git.tree_of(after)},
                "reconstruct": f"git -C {self.git.repo.name} checkout {after}",
            },
            "files": files,
            "metrics": {
                "commits_in_clone": len(commits),
                "commits_first_seen_here": len(fresh),
                "commits_on_branch": api_commit_count,
                "files_changed": len(files),
                "lines_added": sum(f["lines_added"] for f in files),
                "lines_deleted": sum(f["lines_deleted"] for f in files),
                "file_distribution": distribution,
                "review_cycles": metrics["review_cycles"],
                "approvals": metrics["approvals"],
                "changes_requested": metrics["changes_requested"],
                "comment_reviews": metrics["comment_reviews"],
                "time_issue_to_pr_s": rl.seconds_between(issue_opened, opened_at),
                "time_pr_open_to_merge_s": rl.seconds_between(opened_at, merged_at),
                "time_first_commit_to_merge_s": rl.seconds_between(first_commit_at, merged_at),
                "time_pr_open_to_first_review_s":
                    rl.seconds_between(opened_at, metrics["first_review_at"]),
            },
            "people": {
                "author": (self.person_for_login(author_login)
                           or (authors.most_common(1)[0][0] if authors else None)),
                "author_login": author_login,
                "committers": sorted(authors),
                "coauthors": coauthors,
                "reviewers": metrics["reviewers"],
            },
            "timeline": {
                "issue_opened_at": issue_opened,
                "first_commit_at": first_commit_at,
                "pr_opened_at": opened_at,
                "first_review_at": metrics["first_review_at"],
                "merged_at": merged_at,
            },
            "dependencies": [],
            "provenance_gaps": gaps,
        }

    def _linked_issues(self, pr: dict | None, head: rl.Commit) -> list[dict]:
        if not self.state:
            return []
        text = " ".join(filter(None, [
            (pr or {}).get("title"), (pr or {}).get("body"), head.subject, head.body,
        ]))
        numbers: dict[int, str] = {}
        for match in _CLOSES_RE.finditer(text):
            numbers[int(match.group(1))] = "closes-keyword"
        subject = (pr or {}).get("title") or head.subject
        trailing = _TRAILING_REF_RE.search(subject)
        for match in _ANY_REF_RE.finditer(subject):
            number = int(match.group(1))
            if trailing and match.group(0) in trailing.group(0) and \
                    match.end() >= trailing.start():
                continue   # that one is the PR itself
            numbers.setdefault(number, "referenced-in-title")
        for match in _ANY_REF_RE.finditer((pr or {}).get("body") or ""):
            numbers.setdefault(int(match.group(1)), "referenced-in-body")

        issues = []
        for number, how in sorted(numbers.items()):
            issue = self.state.issues.get(number)
            if not issue:
                continue   # a PR number, or an issue from another repository
            issues.append({
                "number": number,
                "title": issue.get("title"),
                "url": issue.get("html_url"),
                "state": issue.get("state"),
                "opened_at": issue.get("created_at"),
                "closed_at": issue.get("closed_at"),
                "author_login": (issue.get("user") or {}).get("login"),
                "labels": [lbl["name"] for lbl in issue.get("labels", [])],
                "link": how,
            })
        return issues


def _objective(body: str, commits: Iterable[rl.Commit]) -> str | None:
    """The stated intent: the first real paragraph of the PR or commit body."""
    for chunk in (body or "").split("\n\n"):
        text = " ".join(
            line.strip() for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith(("#", "-", "*", "|", "<!--",
                                                             "Co-authored-by:", "Signed-off-by:"))
        ).strip()
        if len(text) >= 20:
            return text[:600]
    # No prose anywhere: the sequence of subjects is what the effort actually
    # said about itself, and it beats echoing the episode title back.
    seen: list[str] = []
    for commit in commits:
        if commit.subject not in seen:
            seen.append(commit.subject)
    return "; ".join(seen[:5])[:600] or None


# =============================================================================
# Cross-episode dependencies
# =============================================================================
def link_containment(episodes: list[dict]) -> None:
    """Record which episodes wholly contain which others.

    A pull request merged into a branch that landed later shows up inside the
    outer landing as well as on its own. That is a true property of the history,
    not an error — but it has to be stated, or a consumer summing episodes
    double-counts 630 of this repository's commits without ever noticing.
    """
    commit_sets = {e["id"]: {c["sha"] for c in e["provenance"]["source_commits"]}
                   for e in episodes}
    by_commit: dict[str, list[str]] = defaultdict(list)
    for episode_id, shas in commit_sets.items():
        for sha in shas:
            by_commit[sha].append(episode_id)

    for episode in episodes:
        mine = commit_sets[episode["id"]]
        candidates = {other for sha in mine for other in by_commit[sha]} - {episode["id"]}
        for other in sorted(candidates):
            theirs = commit_sets[other]
            if theirs < mine:
                episode["provenance"]["contains_episodes"].append(other)
            elif mine < theirs:
                episode["provenance"]["contained_by_episodes"].append(other)


def link_dependencies(episodes: list[dict]) -> None:
    """Say which episodes an episode builds on, and on what evidence.

    Only backwards in time, and only with a reason attached — an unexplained
    edge in a dependency graph is indistinguishable from a guess.
    """
    last_touched: dict[str, str] = {}
    by_pr: dict[int, str] = {}
    by_title: dict[str, str] = {}
    by_issue: dict[int, list[str]] = defaultdict(list)

    for episode in episodes:
        deps: dict[tuple[str, str], dict] = {}

        paths = [f["path"] for f in episode["files"]]
        overlaps = Counter(last_touched[p] for p in paths if p in last_touched)
        for other, shared in overlaps.most_common(3):
            deps[(other, "file-overlap")] = {
                "episode_id": other, "kind": "file-overlap",
                "evidence": f"{shared} file(s) last changed by that episode",
            }

        pr = episode["provenance"]["pull_request"]
        text = f"{episode['title']}\n{episode.get('objective') or ''}"
        for match in _ANY_REF_RE.finditer(text):
            other = by_pr.get(int(match.group(1)))
            if other and other != episode["id"]:
                deps[(other, "references-pull-request")] = {
                    "episode_id": other, "kind": "references-pull-request",
                    "evidence": f"mentions #{match.group(1)}",
                }

        for issue in episode["provenance"]["issues"]:
            for other in by_issue[issue["number"]]:
                if other != episode["id"]:
                    deps[(other, "same-issue")] = {
                        "episode_id": other, "kind": "same-issue",
                        "evidence": f"both address issue #{issue['number']}",
                    }

        revert = _REVERT_RE.match(episode["title"])
        if revert and revert.group(1) in by_title:
            other = by_title[revert.group(1)]
            deps[(other, "reverts")] = {
                "episode_id": other, "kind": "reverts",
                "evidence": f'reverts "{revert.group(1)}"',
            }

        episode["dependencies"] = sorted(deps.values(),
                                         key=lambda d: (d["kind"], d["episode_id"]))

        for path in paths:
            last_touched[path] = episode["id"]
        if pr:
            by_pr[pr["number"]] = episode["id"]
        by_title[episode["title"]] = episode["id"]
        for issue in episode["provenance"]["issues"]:
            by_issue[issue["number"]].append(episode["id"])


# =============================================================================
# Main
# =============================================================================
def _spread(values: list[int]) -> dict:
    values = sorted(values)
    if not values:
        return {}
    def at(q: float) -> int:
        return values[min(len(values) - 1, int(q * len(values)))]
    return {"min": values[0], "p50": at(0.5), "p90": at(0.9), "max": values[-1],
            "mean": round(sum(values) / len(values), 2)}


def build_stats(builder: Builder, episodes: list[dict], state: GitHubState | None) -> dict:
    gaps: Counter[str] = Counter()
    for episode in episodes:
        gaps.update(episode["provenance_gaps"])
    covered = {c["sha"] for e in episodes for c in e["provenance"]["source_commits"]}
    unassigned = [c for c in builder.commits if c.sha not in covered]
    reviewed = [e for e in episodes if e["metrics"]["review_cycles"] is not None
                and e["provenance"]["pull_request"]]
    with_reviews = [e for e in reviewed if e["metrics"]["approvals"]
                    or e["metrics"]["changes_requested"] or e["metrics"]["comment_reviews"]]
    durations = [e["metrics"]["time_pr_open_to_merge_s"] for e in episodes
                 if e["metrics"]["time_pr_open_to_merge_s"] is not None]
    durations.sort()
    return {
        "episodes": len(episodes),
        "pr_anchored": sum(1 for e in episodes if e["provenance"]["pull_request"]),
        "heuristically_grouped": sum(1 for e in episodes
                                     if e["provenance"]["grouping_rule"] == "heuristic-run"),
        "single_commit": sum(1 for e in episodes
                             if e["provenance"]["grouping_rule"] == "single-commit"),
        "commits_in_history": len(builder.commits),
        "commits_covered": len(covered),
        "commits_unassigned": len(unassigned),
        "commits_first_seen_sum": sum(e["metrics"]["commits_first_seen_here"] for e in episodes),
        "episodes_contained_by_another": sum(
            1 for e in episodes if e["provenance"]["contained_by_episodes"]),
        "episodes_containing_another": sum(
            1 for e in episodes if e["provenance"]["contains_episodes"]),
        "deduplication_note": "episodes nest: a pull request merged into a branch that "
                              "landed later appears inside the outer landing too. Sum "
                              "metrics.commits_first_seen_here, or skip episodes that have "
                              "provenance.contained_by_episodes, to count each commit once.",
        "unassigned_examples": [c.sha for c in unassigned[:10]],
        "by_change_type": dict(Counter(e["change_type"]["primary"]
                                       for e in episodes).most_common()),
        "by_year": dict(Counter((e["timeline"]["merged_at"] or "")[:4]
                                for e in episodes).most_common()),
        "by_merge_style": dict(Counter(e["provenance"]["merge_style"]
                                       for e in episodes).most_common()),
        "with_linked_issue": sum(1 for e in episodes if e["provenance"]["issues"]),
        "with_any_review": len(with_reviews),
        "with_review_cycles": sum(1 for e in episodes if e["metrics"]["review_cycles"]),
        "median_pr_open_to_merge_s": durations[len(durations) // 2] if durations else None,
        "commits_per_episode": _spread([e["metrics"]["commits_in_clone"] for e in episodes]),
        "files_per_episode": _spread([e["metrics"]["files_changed"] for e in episodes]),
        "lines_changed_per_episode": _spread(
            [e["metrics"]["lines_added"] + e["metrics"]["lines_deleted"] for e in episodes]),
        "provenance_gaps": dict(gaps.most_common()),
        "github": {
            "source": state.source if state else None,
            "pull_requests_seen": len(state.pulls) if state else 0,
            "issues_seen": len(state.issues) if state else 0,
            "api_requests": state.gh.stats if (state and state.gh) else None,
        },
    }


def main() -> None:
    parser = rl.base_parser(__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"output file (default: {DEFAULT_OUT})")
    parser.add_argument("--token", help="GitHub token (else $GITHUB_TOKEN, $GH_TOKEN or .env)")
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "github",
                        help="where API responses are cached")
    parser.add_argument("--no-refresh", action="store_true",
                        help="serve every API response from cache; never open a socket")
    parser.add_argument("--no-symbols", action="store_true",
                        help="skip Python AST symbol diffing (faster)")
    parser.add_argument("--max-episodes", type=int,
                        help="stop after this many episodes (for a quick look)")
    parser.add_argument("--no-github", action="store_true",
                        help="git-only run: no PR, issue or review provenance at all")
    parser.add_argument("--history", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "repository_history.json",
                        help="Stage 0 record to read PR/issue/review data from")
    parser.add_argument("--from-api", action="store_true",
                        help="call GitHub directly instead of reading the Stage 0 record")
    args = parser.parse_args()

    git = rl.Git(args.repo)
    owner_repo = rl.parse_owner_repo(git.remote_url())
    state = None
    if args.no_github:
        rl.warn("--no-github: episodes will carry no pull request, issue or review data")
    elif args.history.exists() and not args.from_api:
        rl.heading(f"Stage 0 record: {args.history.name}")
        state = GitHubState.from_history(
            json.loads(args.history.read_text(encoding="utf-8")))
    else:
        if not owner_repo:
            rl.fail(f"cannot tell which GitHub repository {git.repo} is — its origin is "
                    f"{git.remote_url()!r}. Use --no-github for a git-only run.")
        if not args.from_api:
            rl.warn(f"{args.history} does not exist — falling back to the GitHub API.\n"
                    "  Run extract_repository_history.py first to make Stage 0 the source.")
        rl.heading(f"GitHub: {owner_repo[0]}/{owner_repo[1]}")
        gh = GitHub(owner_repo[0], owner_repo[1], args.cache_dir,
                    token=args.token, refresh=not args.no_refresh, verbose=args.verbose)
        try:
            state = GitHubState.from_api(gh, args.verbose)
        except MissingFromCache as exc:
            rl.fail(str(exc))

    rl.heading(f"Reading {git.repo}")
    builder = Builder(git, state, args.rev, args.since, args.until, not args.no_symbols)
    rl.ok(f"{len(builder.commits)} commits, {len(builder.first_parent)} on the first-parent line")

    rl.heading("Building episodes")
    episodes = builder.pr_episodes()
    rl.ok(f"{len(episodes)} pull-request episodes")
    episodes += builder.leftover_episodes()
    episodes.sort(key=lambda e: e["timeline"]["merged_at"] or e["timeline"]["first_commit_at"] or "")
    if args.max_episodes:
        episodes = episodes[: args.max_episodes]
    rl.ok(f"{len(episodes)} episodes in total")

    link_containment(episodes)
    link_dependencies(episodes)
    stats = build_stats(builder, episodes, state)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": rl.now_iso(),
        "generator": "data_gen/build_episodes.py",
        "unit": "an engineering episode: one coherent change, with the issue, branch, "
                "commits, review and merge that produced it",
        "source": {
            "path": str(git.repo),
            "remote": git.remote_url(),
            "rev": args.rev,
            "head_commit": git.head(),
            "github": f"{owner_repo[0]}/{owner_repo[1]}" if owner_repo else None,
        },
        "stats": stats,
        "episodes": episodes,
    }
    size = rl.write_json(args.out, payload)

    rl.heading("Wrote")
    rl.ok(f"{args.out} ({rl.human_bytes(size)})")
    rl.info(f"{stats['pr_anchored']} pull-request episodes, "
            f"{stats['heuristically_grouped']} grouped runs, "
            f"{stats['single_commit']} single commits")
    rl.info(f"{stats['commits_covered']}/{stats['commits_in_history']} commits covered; "
            f"{stats['with_linked_issue']} episodes link an issue; "
            f"{stats['with_review_cycles']} went back for changes")
    for gap, n in stats["provenance_gaps"].items():
        rl.warn(f"{n} episode(s): {gap}")


if __name__ == "__main__":
    main()
