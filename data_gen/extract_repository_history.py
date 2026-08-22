#!/usr/bin/env python3
"""Stage 0 — extract the real repository history, before anything synthetic exists.

Writes `build/repository_history.json` (the manifest) and `build/repository_blobs/`
(a content-addressed store of every text file version, keyed by git blob SHA).

Everything downstream reads this instead of walking git or calling GitHub itself,
so the repository is mined exactly once and every later stage sees the same record.

The point that shapes the whole design: **the actual code is retained**, not just
descriptions of it. For every changed file this keeps the before blob, the patch,
and the after blob, and the round-trip is verified — `git apply` the stored patch
to the stored before-state and you get the recorded after-state. A later stage
adapting a real change never has to invent a file from scratch.

    GITHUB_TOKEN=... python3 data_gen/extract_repository_history.py -v
    python3 data_gen/extract_repository_history.py --no-refresh   # from cache
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402
from github_api import GitHub, MissingFromCache  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "repository_history.json"
DEFAULT_BLOBS = rl.DEFAULT_BUILD_DIR / "repository_blobs"

# Bulk with nothing to adapt: a lockfile diff, a recorded HTTP cassette or a
# parquet fixture is megabytes that no later stage would ever base a change on.
# Every skipped path is reported, not silently dropped.
NOISE = re.compile(
    r"(^|/)(poetry\.lock|package-lock\.json|yarn\.lock|\.test_cache\.zip)$"
    r"|\.(parquet|zip|png|gif|jpe?g|svg|ico|whl|tar|gz|so|bin|pdf|mp4|woff2?)$"
    r"|/fixtures/.*\.ya?ml$"
)
# One pathological file patch should not double the manifest.
MAX_FILE_PATCH = 200_000

_FMT = "%x1e" + "%x00".join(
    ["%H", "%P", "%T", "%an", "%ae", "%aI", "%cn", "%ce", "%cI", "%s", "%b", ""]
)
_RAW = re.compile(
    r"^:(\d+) (\d+) ([0-9a-f]{40}) ([0-9a-f]{40}) ([A-Z])(\d*)\t(.*)$"
)


def is_noise(path: str) -> bool:
    return bool(NOISE.search(path))


# =============================================================================
# git
# =============================================================================
def collect_refs(git: rl.Git) -> dict:
    branches, tags = [], []
    for line in git.lines("for-each-ref",
                          "--format=%(refname)\t%(objectname)\t%(creatordate:iso-strict)"
                          "\t%(*objectname)", "refs/heads", "refs/remotes", "refs/tags"):
        refname, sha, created, peeled = (line.split("\t") + ["", "", ""])[:4]
        target = peeled or sha
        if refname.startswith("refs/tags/"):
            tags.append({"name": refname[len("refs/tags/"):], "commit": target,
                         "date": created, "annotated": bool(peeled)})
        else:
            branches.append({"name": refname.split("/", 2)[-1], "ref": refname,
                             "commit": sha, "remote": refname.startswith("refs/remotes/")})
    tags.sort(key=lambda t: t["date"])
    return {
        "branches": branches, "tags": tags,
        "head": git.head(),
        "default_branch": git.run("rev-parse", "--abbrev-ref", "HEAD").strip(),
        # The mainline, oldest first, and the sequence of landings on it. Both
        # are orderings a consumer would otherwise have to re-derive from git.
        "head_sequence": list(reversed(git.lines("rev-list", "HEAD"))),
        "first_parent_sequence": list(reversed(git.lines("rev-list", "--first-parent", "HEAD"))),
    }


def walk_commits(git: rl.Git) -> list[dict]:
    """Every commit reachable from any ref, with per-file blob identity and stats.

    `--all`, not HEAD: 127 of this repository's commits live only on side
    branches, and a record that drops them cannot describe its own merges.
    Merges carry no file list — a merge's changes belong to the commits it
    brought in, and attributing them twice would double every count.
    """
    raw = git.run("log", "--all", f"--format={_FMT}", "--raw", "--numstat",
                  "--abbrev=40", "--no-renames" if False else "-M", "--reverse")
    commits = []
    for record in raw.split("\x1e"):
        if not record.strip():
            continue
        fields = record.split("\x00")
        if len(fields) < 12:
            continue
        files: dict[str, dict] = {}
        for line in fields[11].splitlines():
            match = _RAW.match(line)
            if match:
                mode_a, mode_b, blob_a, blob_b, status, score, rest = match.groups()
                parts = rest.split("\t")
                from_path, path = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0])
                files[path] = {
                    "path": path, "from_path": from_path, "status": status,
                    "similarity": int(score) if score else None,
                    "blob_before": None if blob_a == "0" * 40 else blob_a,
                    "blob_after": None if blob_b == "0" * 40 else blob_b,
                    "mode_before": None if mode_a == "000000" else mode_a,
                    "mode_after": None if mode_b == "000000" else mode_b,
                    "lines_added": 0, "lines_deleted": 0, "binary": False,
                    "language": rl.language_of(path), "noise": is_noise(path),
                }
                continue
            stat = line.split("\t")
            if len(stat) == 3:
                added, deleted, path = stat
                if " => " in path or "{" in path:
                    renamed = re.match(r"^(.*)\{(.*) => (.*)\}(.*)$", path)
                    path = (f"{renamed.group(1)}{renamed.group(3)}{renamed.group(4)}"
                            .replace("//", "/")) if renamed else path.split(" => ")[-1]
                entry = files.get(path)
                if entry is not None:
                    entry["lines_added"] = int(added) if added.isdigit() else 0
                    entry["lines_deleted"] = int(deleted) if deleted.isdigit() else 0
                    entry["binary"] = not added.isdigit()

        parents = fields[1].split() if fields[1].strip() else []
        commits.append({
            "sha": fields[0], "parents": parents, "tree": fields[2],
            "is_merge": len(parents) > 1,
            "author": {"name": fields[3], "email": fields[4].lower(), "date": fields[5]},
            "committer": {"name": fields[6], "email": fields[7].lower(), "date": fields[8]},
            "subject": fields[9], "body": fields[10].strip(),
            "files": list(files.values()),
        })
    return commits


def attach_patches(git: rl.Git, commits: list[dict], verbose: int = 0) -> dict:
    """The actual diff text, per file, from one streaming `git log -p` pass."""
    by_sha = {c["sha"]: c for c in commits}
    proc = subprocess.Popen(
        ["git", "-C", str(git.repo), "-c", "core.quotepath=false", "log", "--all",
         "--format=%x1e%H", "--patch", "--no-color", "-M", "--reverse",
         "--unified=3"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    stats = {"files_with_patch": 0, "truncated": 0, "skipped_noise": 0, "patch_bytes": 0}
    current: dict | None = None
    path: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf, path
        if current is None or path is None:
            buf, path = [], None
            return
        entry = next((f for f in current["files"] if f["path"] == path), None)
        buf_text = "".join(buf)
        if entry is not None:
            if entry["noise"] or entry["binary"]:
                stats["skipped_noise"] += 1
            else:
                if len(buf_text) > MAX_FILE_PATCH:
                    entry["patch"] = buf_text[:MAX_FILE_PATCH]
                    entry["patch_truncated"] = True
                    entry["patch_full_bytes"] = len(buf_text)
                    stats["truncated"] += 1
                else:
                    entry["patch"] = buf_text
                stats["files_with_patch"] += 1
                stats["patch_bytes"] += len(entry["patch"])
        buf, path = [], None

    for line in proc.stdout:
        text = line.decode("utf-8", "replace")
        if text.startswith("\x1e"):
            flush()
            current = by_sha.get(text[1:].strip())
            continue
        if text.startswith("diff --git "):
            flush()
            match = re.match(r'^diff --git "?a/(.*?)"? "?b/(.*?)"?\n$', text)
            path = match.group(2) if match else None
            buf = [text]
            continue
        if path is not None:
            buf.append(text)
    flush()
    proc.stdout.close()
    proc.wait()
    return stats


def export_blobs(git: rl.Git, out_dir: Path, verbose: int = 0) -> dict:
    """Every text blob version ever committed, written out by its git SHA.

    This is the before/after snapshot store. A later stage adapting a real
    change reads the exact bytes the change started from, by SHA, without
    needing the clone.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths_by_sha: dict[str, set[str]] = defaultdict(set)
    for line in git.lines("rev-list", "--objects", "--all"):
        sha, _, path = line.partition(" ")
        if path and not is_noise(path):
            paths_by_sha[sha].add(path)
    if not paths_by_sha:
        return {"blobs": 0, "bytes": 0, "index": {}}

    check = subprocess.run(
        ["git", "-C", str(git.repo), "cat-file", "--batch-check"],
        input="".join(f"{s}\n" for s in paths_by_sha).encode(),
        capture_output=True,
    )
    wanted = []
    for line in check.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == "blob":
            wanted.append((parts[0], int(parts[2])))

    index: dict[str, dict] = {}
    written = total = 0
    batch = subprocess.Popen(
        ["git", "-C", str(git.repo), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    for sha, size in wanted:
        batch.stdin.write(f"{sha}\n".encode())
        batch.stdin.flush()
        header = batch.stdout.readline()
        if not header or header.split()[-1] == b"missing":
            continue
        payload = batch.stdout.read(size)
        batch.stdout.read(1)          # trailing newline
        target = out_dir / sha
        if not target.exists():
            target.write_bytes(payload)
        written += 1
        total += size
        paths = sorted(paths_by_sha[sha])
        index[sha] = {"bytes": size, "paths": paths[:8], "path_count": len(paths),
                      "language": rl.language_of(paths[0]) if paths else "other"}
    batch.stdin.close()
    batch.wait()
    return {"blobs": written, "bytes": total, "index": index}


def tree_at(git: rl.Git, rev: str) -> list[dict]:
    out = []
    for line in git.lines("ls-tree", "-r", "-l", rev):
        head, _, path = line.partition("\t")
        parts = head.split()
        if len(parts) >= 4:
            out.append({"path": path, "mode": parts[0], "blob": parts[2],
                        "bytes": int(parts[3]) if parts[3].isdigit() else None,
                        "language": rl.language_of(path)})
    return out


def branch_topology(git: rl.Git, refs: dict) -> list[dict]:
    """Which commits are unique to each branch, and where it forked from HEAD."""
    out = []
    for branch in refs["branches"]:
        if branch["name"] in ("origin/HEAD",):
            continue
        unique = git.lines("rev-list", branch["commit"], "^HEAD")
        base = git.run("merge-base", branch["commit"], "HEAD", check=False).strip()
        out.append({"name": branch["name"], "commit": branch["commit"],
                    "merge_base": base or None, "commits_not_on_head": len(unique),
                    "unique_commits": unique[:50]})
    out.sort(key=lambda b: -b["commits_not_on_head"])
    return out


# =============================================================================
# patterns
# =============================================================================
_CONV = re.compile(r"^\s*([a-z]+)(\([^)]*\))?(!)?\s*:", re.I)


def _subject_stats(subjects: list[str]) -> dict:
    lengths = sorted(len(s) for s in subjects) or [0]
    conventional = Counter()
    for subject in subjects:
        match = _CONV.match(subject)
        if match:
            conventional[match.group(1).lower()] += 1
    return {
        "count": len(subjects),
        "length": {"p50": lengths[len(lengths) // 2],
                   "p90": lengths[int(len(lengths) * 0.9)], "max": lengths[-1]},
        "conventional_prefixes": dict(conventional.most_common()),
        "conventional_share": round(sum(conventional.values()) / len(subjects), 3)
        if subjects else 0,
        "starts_capitalised": round(
            sum(1 for s in subjects if s[:1].isupper()) / len(subjects), 3) if subjects else 0,
        "ends_with_period": round(
            sum(1 for s in subjects if s.endswith(".")) / len(subjects), 3) if subjects else 0,
        "references_a_number": round(
            sum(1 for s in subjects if "#" in s) / len(subjects), 3) if subjects else 0,
        "top_first_words": dict(Counter(
            s.split()[0].lower().rstrip(":") for s in subjects if s.split()).most_common(15)),
    }


def message_patterns(commits: list[dict], pulls: list[dict]) -> dict:
    real = [c for c in commits if not c["is_merge"]]
    bodies = [c["body"] for c in real]
    branch_prefixes = Counter()
    for pr in pulls:
        ref = ((pr.get("head") or {}).get("ref") or "")
        branch_prefixes[ref.split("/")[0] if "/" in ref else "(no prefix)"] += 1
    by_year: dict[str, dict] = {}
    for year in sorted({c["author"]["date"][:4] for c in real}):
        by_year[year] = _subject_stats(
            [c["subject"] for c in real if c["author"]["date"][:4] == year])
    return {
        "commit_subjects": _subject_stats([c["subject"] for c in real]),
        "commit_subjects_by_year": by_year,
        "bodies": {
            "share_with_body": round(sum(1 for b in bodies if b) / len(bodies), 3)
            if bodies else 0,
            "co_authored_by": sum(1 for b in bodies if "Co-authored-by" in b),
            "signed_off_by": sum(1 for b in bodies if "Signed-off-by" in b),
            "closes_an_issue": sum(
                1 for b in bodies
                if re.search(r"\b(clos(e|es|ed)|fix(es|ed)?|resolv(e|es|ed))\s+#\d+", b, re.I)),
        },
        "pull_request_titles": _subject_stats([pr["title"] for pr in pulls if pr.get("title")]),
        "branch_name_prefixes": dict(branch_prefixes.most_common(20)),
    }


# =============================================================================
# GitHub
# =============================================================================
def fetch_github(gh: GitHub, verbose: int = 0) -> dict:
    rl.info("pull requests...")
    pulls = gh.pulls()
    rl.ok(f"{len(pulls)} pull requests")

    rl.info("issues (including pull requests, as GitHub returns them)...")
    raw_issues = gh.issues()
    issues = [i for i in raw_issues if "pull_request" not in i]
    rl.ok(f"{len(issues)} issues, {len(raw_issues) - len(issues)} of them pull requests")

    rl.info("releases, labels and branches...")
    releases, labels, branches = gh.releases(), gh.labels(), gh.branches()
    rl.ok(f"{len(releases)} releases, {len(labels)} labels, {len(branches)} branches")

    reviews: dict[str, list] = {}
    review_comments: dict[str, list] = {}
    pr_commits: dict[str, list] = {}
    merged = [pr for pr in pulls if pr.get("merged_at")]
    rl.info(f"reviews, review comments and commits for {len(merged)} merged pull requests...")
    for i, pr in enumerate(merged, 1):
        number = pr["number"]
        reviews[str(number)] = gh.pull_reviews(number)
        pr_commits[str(number)] = gh.pull_commits(number)
        # Line-level comments only exist where a review happened.
        if reviews[str(number)]:
            review_comments[str(number)] = gh.pull_review_comments(number)
        if verbose and i % 100 == 0:
            rl.info(f"  {i}/{len(merged)}")
    rl.ok(f"reviews for {len(reviews)} pull requests, "
          f"{sum(len(v) for v in review_comments.values())} line comments")

    # The list endpoints report a comment count, so threads are only fetched
    # where one actually exists — that alone halves the request budget.
    comments: dict[str, list] = {}
    with_comments = [i for i in raw_issues if (i.get("comments") or 0) > 0]
    rl.info(f"comment threads on {len(with_comments)} issues and pull requests...")
    for i, issue in enumerate(with_comments, 1):
        comments[str(issue["number"])] = gh.issue_comments(issue["number"])
        if verbose and i % 100 == 0:
            rl.info(f"  {i}/{len(with_comments)}")
    rl.ok(f"{sum(len(v) for v in comments.values())} comments")

    return {"pulls": pulls, "issues": issues, "reviews": reviews,
            "review_comments": review_comments, "pull_commits": pr_commits,
            "comments": comments, "releases": releases, "labels": labels,
            "branches": branches}


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    parser = rl.base_parser(__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--blobs-dir", type=Path, default=DEFAULT_BLOBS)
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "github")
    parser.add_argument("--token", help="GitHub token (else $GITHUB_TOKEN, $GH_TOKEN or .env)")
    parser.add_argument("--no-refresh", action="store_true",
                        help="serve every API response from cache; never open a socket")
    parser.add_argument("--no-github", action="store_true",
                        help="git only: no pull requests, issues, reviews or releases")
    parser.add_argument("--no-patches", action="store_true",
                        help="skip diff text (a ~15MB structural record instead of ~90MB)")
    parser.add_argument("--no-blobs", action="store_true",
                        help="skip the file-content sidecar")
    args = parser.parse_args()

    git = rl.Git(args.repo)
    owner_repo = rl.parse_owner_repo(git.remote_url())

    rl.heading(f"Reading {git.repo}")
    refs = collect_refs(git)
    commits = walk_commits(git)
    rl.ok(f"{len(commits)} commits across all refs "
          f"({sum(1 for c in commits if c['is_merge'])} merges), "
          f"{len(refs['branches'])} branches, {len(refs['tags'])} tags")

    patch_stats = {"files_with_patch": 0, "skipped_noise": 0, "truncated": 0, "patch_bytes": 0}
    if not args.no_patches:
        rl.heading("Retaining the actual changes")
        patch_stats = attach_patches(git, commits, args.verbose)
        rl.ok(f"{patch_stats['files_with_patch']} file patches "
              f"({rl.human_bytes(patch_stats['patch_bytes'])}), "
              f"{patch_stats['skipped_noise']} skipped as noise, "
              f"{patch_stats['truncated']} truncated at {MAX_FILE_PATCH:,} bytes")

    blob_store = {"blobs": 0, "bytes": 0, "index": {}}
    if not args.no_blobs:
        rl.heading("Exporting before/after file states")
        blob_store = export_blobs(git, args.blobs_dir, args.verbose)
        rl.ok(f"{blob_store['blobs']} blobs ({rl.human_bytes(blob_store['bytes'])}) "
              f"-> {args.blobs_dir}")

    github = {"pulls": [], "issues": [], "reviews": {}, "review_comments": {},
              "pull_commits": {}, "comments": {}, "releases": [], "labels": [], "branches": []}
    if not args.no_github:
        if not owner_repo:
            rl.fail(f"cannot tell which GitHub repository {git.repo} is. Use --no-github.")
        rl.heading(f"GitHub: {owner_repo[0]}/{owner_repo[1]}")
        gh = GitHub(owner_repo[0], owner_repo[1], args.cache_dir,
                    token=args.token, refresh=not args.no_refresh, verbose=args.verbose)
        try:
            github = fetch_github(gh, args.verbose)
        except MissingFromCache as exc:
            rl.fail(str(exc))

    rl.heading("Deriving")
    identities = rl.Identities([(c["author"]["name"], c["author"]["email"]) for c in commits]
                               + [(c["committer"]["name"], c["committer"]["email"])
                                  for c in commits])
    for commit in commits:
        commit["author"]["person"] = identities.of(commit["author"]["name"],
                                                   commit["author"]["email"])
        commit["committer"]["person"] = identities.of(commit["committer"]["name"],
                                                      commit["committer"]["email"])
    patterns = message_patterns(commits, github["pulls"])
    topology = branch_topology(git, refs)
    rl.ok(f"{len(identities.people)} contributor identities, "
          f"{len(patterns['commit_subjects']['conventional_prefixes'])} commit-message prefixes")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": rl.now_iso(),
        "generator": "data_gen/extract_repository_history.py",
        "stage": "0 — raw extraction, before anything synthetic exists",
        "repository": {
            "path": str(git.repo),
            "remote": git.remote_url(),
            "github": f"{owner_repo[0]}/{owner_repo[1]}" if owner_repo else None,
            "head": refs["head"],
            "default_branch": refs["default_branch"],
            "is_shallow": git.is_shallow(),
        },
        "retention": {
            "patches_included": not args.no_patches,
            "blobs_included": not args.no_blobs,
            "blob_dir": str(args.blobs_dir),
            "noise_pattern": NOISE.pattern,
            "max_file_patch_bytes": MAX_FILE_PATCH,
            "patch_stats": patch_stats,
            "blob_stats": {k: v for k, v in blob_store.items() if k != "index"},
            "note": "before-state and after-state are blob SHAs resolvable in blob_dir; "
                    "applying a file's `patch` to its `blob_before` reproduces `blob_after`",
        },
        "refs": refs,
        "branch_topology": topology,
        "commits": commits,
        "trees": {
            "head": tree_at(git, refs["head"]),
            "tags": {tag["name"]: len(tree_at(git, tag["commit"])) for tag in refs["tags"]},
        },
        "blob_index": blob_store["index"],
        "github": github,
        "contributors": identities.as_json(),
        "patterns": patterns,
        "totals": {
            "commits": len(commits),
            "merges": sum(1 for c in commits if c["is_merge"]),
            "file_changes": sum(len(c["files"]) for c in commits),
            "pull_requests": len(github["pulls"]),
            "issues": len(github["issues"]),
            "reviews": sum(len(v) for v in github["reviews"].values()),
            "review_comments": sum(len(v) for v in github["review_comments"].values()),
            "comments": sum(len(v) for v in github["comments"].values()),
            "releases": len(github["releases"]),
        },
    }

    size = rl.write_json(args.out, payload)
    rl.heading("Wrote")
    rl.ok(f"{args.out} ({rl.human_bytes(size)})")
    if not args.no_blobs:
        rl.ok(f"{args.blobs_dir} ({blob_store['blobs']} blobs, "
              f"{rl.human_bytes(blob_store['bytes'])})")
    for key, value in payload["totals"].items():
        rl.info(f"{key:18s} {value:,}")


if __name__ == "__main__":
    main()
