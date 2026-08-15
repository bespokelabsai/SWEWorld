#!/usr/bin/env python3
"""Replay a rewritten git history into fresh repos and push them to Gitea.

Input
-----
data/identities.yaml   the persona list (see data/schemas/identities.md)
data/commits.jsonl     one commit per line, in commit order

Each line of commits.jsonl:

    {
      "repo":         "platform",              # required, Gitea repo name
      "branch":       "main",                  # default "main"
      "author":       "alice",                 # required, persona id
      "committer":    "alice",                 # default: author
      "authored_at":  "2026-01-08T10:14:02Z",  # required, ISO-8601 with offset
      "committed_at": "2026-01-08T10:14:02Z",  # default: authored_at
      "message":      "Add health endpoint",   # required
      "tag":          "v0.1.0",                # optional lightweight tag
      "changes": [                             # required, at least one
        {"path": "api/health.go",
         "action": "add",                      # add | modify | delete | rename
         "content": "package api\n",           # required for add/modify
         "from_path": "api/old.go",            # required for rename
         "mode": "100644",                     # or 100755
         "encoding": "utf-8"}                  # or base64
      ]
    }

Parents are implicit: a line's parent is the previous line on the same branch.
Full file content is stored rather than diffs — see data/schemas/commits.md for
why (diffs need an exact prior tree state and fail unrecoverably on drift).

Behaviour
---------
Replays every commit into a local repo, creates the repo in Gitea if needed,
then force-pushes all branches and tags.

--dry-run replays the whole history into a temporary directory and never
contacts Gitea, so the result can be inspected with `git log` before anything
is published. The temp path is printed.
"""
from __future__ import annotations

import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worldlib as wl  # noqa: E402

COMMIT_REQUIRED = ("repo", "author", "authored_at", "message", "changes")
COMMIT_OPTIONAL = ("branch", "committer", "committed_at", "tag", "parents")
CHANGE_REQUIRED = ("path", "action")
CHANGE_OPTIONAL = ("content", "from_path", "mode", "encoding")
ACTIONS = {"add", "modify", "delete", "rename"}
REPO_NAME_OK = __import__("re").compile(r"^[A-Za-z0-9._-]+$")


# =============================================================================
# Parsing and validation
# =============================================================================
def load_commits(path: Path, identities: wl.Identities, problems: wl.Problems) -> list[dict]:
    """Parse commits.jsonl and validate every line against the schema."""
    commits: list[dict] = []
    branch_last_ts: dict[tuple[str, str], Any] = {}

    for lineno, obj in wl.read_jsonl(path, problems):
        wl.check_keys(obj, required=COMMIT_REQUIRED, optional=COMMIT_OPTIONAL,
                      problems=problems, path=path, line=lineno)

        if "parents" in obj:
            raise NotImplementedError(
                f"{path}:{lineno}: explicit 'parents' implies a merge commit. "
                "data/schemas/commits.md defines parents as implicit (previous "
                "line on the same branch); representing a real DAG needs a "
                "format decision that has not been made."
            )

        repo = obj.get("repo")
        if isinstance(repo, str) and not REPO_NAME_OK.match(repo):
            problems.error(f"repo {repo!r} must match {REPO_NAME_OK.pattern}", path, lineno)

        author = identities.require(obj.get("author"), problems, path, lineno, "author")
        committer = author
        if obj.get("committer"):
            committer = identities.require(obj["committer"], problems, path, lineno, "committer")

        authored = wl.parse_ts(obj.get("authored_at"), path=path, line=lineno,
                               problems=problems, field_name="authored_at")
        committed = authored
        if obj.get("committed_at"):
            committed = wl.parse_ts(obj["committed_at"], path=path, line=lineno,
                                    problems=problems, field_name="committed_at")
            if authored and committed and committed < authored:
                problems.error("committed_at is before authored_at", path, lineno)

        branch = obj.get("branch") or "main"
        key = (repo, branch)
        if authored:
            previous = branch_last_ts.get(key)
            if previous and authored < previous:
                problems.error(
                    f"authored_at goes backwards on {repo}:{branch} "
                    f"({authored.isoformat()} after {previous.isoformat()}) — "
                    "commits must be in order",
                    path, lineno,
                )
            branch_last_ts[key] = authored

        changes = obj.get("changes")
        if not isinstance(changes, list) or not changes:
            problems.error("changes must be a non-empty list", path, lineno)
            changes = []
        for idx, change in enumerate(changes):
            _validate_change(change, idx, path, lineno, problems)

        if not isinstance(obj.get("message"), str) or not obj.get("message", "").strip():
            problems.error("message must be a non-empty string", path, lineno)

        commits.append({
            "lineno": lineno,
            "repo": repo,
            "branch": branch,
            "author": author,
            "committer": committer,
            "authored_at": authored,
            "committed_at": committed,
            "message": obj.get("message", ""),
            "changes": changes,
            "tag": obj.get("tag"),
        })

    return commits


def _validate_change(change: Any, idx: int, path: Path, lineno: int,
                     problems: wl.Problems) -> None:
    """Validate one entry of a commit's changes[] array."""
    context = f"changes[{idx}]"
    if not isinstance(change, dict):
        problems.error(f"{context} must be an object", path, lineno)
        return
    wl.check_keys(change, required=CHANGE_REQUIRED, optional=CHANGE_OPTIONAL,
                  problems=problems, path=path, line=lineno, context=context)

    action = change.get("action")
    if action not in ACTIONS:
        problems.error(
            f"{context}: action {action!r} must be one of {sorted(ACTIONS)}", path, lineno
        )

    rel = change.get("path")
    if isinstance(rel, str):
        if rel.startswith("/") or ".." in Path(rel).parts:
            problems.error(
                f"{context}: path {rel!r} must be repo-relative and must not escape the repo",
                path, lineno,
            )
    if action in ("add", "modify") and change.get("content") is None:
        problems.error(f"{context}: {action} requires 'content'", path, lineno)
    if action == "rename" and not change.get("from_path"):
        problems.error(f"{context}: rename requires 'from_path'", path, lineno)
    if change.get("encoding") not in (None, "utf-8", "base64"):
        problems.error(
            f"{context}: encoding {change.get('encoding')!r} must be 'utf-8' or 'base64'",
            path, lineno,
        )
    if change.get("mode") not in (None, "100644", "100755"):
        problems.error(
            f"{context}: mode {change.get('mode')!r} must be '100644' or '100755'",
            path, lineno,
        )


# =============================================================================
# Replay
# =============================================================================
def run_git(repo_dir: Path, *args: str, env: dict[str, str] | None = None) -> str:
    """Run a git command in repo_dir, raising with stderr on failure."""
    full_env = {**os.environ, **(env or {})}
    proc = subprocess.run(
        ["git", *args], cwd=repo_dir, env=full_env,
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {repo_dir}:\n{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def init_repo(repo_dir: Path) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    run_git(repo_dir, "init", "-q", "-b", "main")
    # Identity is supplied per-commit via env; these keep git from complaining
    # if a commit somehow omits them.
    run_git(repo_dir, "config", "user.name", "SWEWorld")
    run_git(repo_dir, "config", "user.email", "world@localhost")


def apply_change(repo_dir: Path, change: dict) -> None:
    """Write one change into the working tree."""
    action = change["action"]
    target = repo_dir / change["path"]

    if action == "delete":
        if target.exists():
            target.unlink()
        return

    if action == "rename":
        source = repo_dir / change["from_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.move(str(source), str(target))
        # A rename may also carry new content.
        if change.get("content") is None:
            return

    target.parent.mkdir(parents=True, exist_ok=True)
    content = change.get("content", "")
    if change.get("encoding") == "base64":
        target.write_bytes(base64.b64decode(content))
    else:
        target.write_text(content)

    if change.get("mode") == "100755":
        target.chmod(0o755)


def replay_commit(repo_dir: Path, commit: dict, verbose: bool = False) -> None:
    """Apply a commit's changes and commit them with the right identity and dates."""
    branch = commit["branch"]
    existing = run_git(repo_dir, "branch", "--list", branch)
    has_commits = bool(run_git(repo_dir, "rev-list", "-n", "1", "--all"))

    if existing:
        run_git(repo_dir, "checkout", "-q", branch)
    elif has_commits:
        run_git(repo_dir, "checkout", "-q", "-b", branch)
    else:
        # First commit of the repo; git init already put us on `main`.
        if branch != "main":
            run_git(repo_dir, "checkout", "-q", "-b", branch)

    for change in commit["changes"]:
        apply_change(repo_dir, change)

    author, committer = commit["author"], commit["committer"]
    env = {
        "GIT_AUTHOR_NAME": author.git_name,
        "GIT_AUTHOR_EMAIL": author.git_email,
        "GIT_AUTHOR_DATE": wl.to_git_date(commit["authored_at"]),
        "GIT_COMMITTER_NAME": committer.git_name,
        "GIT_COMMITTER_EMAIL": committer.git_email,
        # Both dates matter. Setting only the author date makes `git log` look
        # right while everything that sorts by commit date — including Gitea's
        # activity timeline — shows the whole history landing at once.
        "GIT_COMMITTER_DATE": wl.to_git_date(commit["committed_at"]),
    }

    run_git(repo_dir, "add", "-A")
    run_git(repo_dir, "commit", "-q", "--allow-empty", "-m", commit["message"], env=env)

    if commit.get("tag"):
        run_git(repo_dir, "tag", "-f", commit["tag"], env=env)

    if verbose:
        sha = run_git(repo_dir, "rev-parse", "--short", "HEAD")
        wl.info(f"{commit['repo']}:{branch} {sha} {commit['message'].splitlines()[0][:60]}")


# =============================================================================
# Gitea
# =============================================================================
def ensure_gitea_repo(world: wl.World, repo: str, token: str) -> None:
    """Create the repo via Gitea's API if it does not already exist."""
    sess = wl.session(world)
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}

    got = sess.get(world.url("git", f"/api/v1/repos/{world.admin_user}/{repo}"),
                   headers=headers, timeout=30)
    if got.status_code == 200:
        wl.info(f"gitea repo {world.admin_user}/{repo} already exists")
        return

    created = sess.post(
        world.url("git", "/api/v1/user/repos"),
        headers=headers,
        json={"name": repo, "private": False, "auto_init": False,
              "default_branch": "main"},
        timeout=30,
    )
    if created.status_code not in (200, 201):
        raise RuntimeError(
            f"could not create gitea repo {repo!r} "
            f"({created.status_code}): {created.text[:300]}"
        )
    wl.ok(f"created gitea repo {world.admin_user}/{repo}")


def set_default_branch(world: wl.World, repo: str, branch: str, token: str) -> None:
    """Pin the repo's default branch after pushing.

    The repo is created empty (auto_init: false), so it has no branches at
    creation time and the default_branch given then does not stick. Pushing
    --all then lets Gitea choose, which lands on whichever branch it happens to
    see first — a feature branch shows up as the repo's trunk.
    """
    sess = wl.session(world)
    resp = sess.patch(
        world.url("git", f"/api/v1/repos/{world.admin_user}/{repo}"),
        headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
        json={"default_branch": branch},
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"could not set default branch of {repo!r} to {branch!r} "
            f"({resp.status_code}): {resp.text[:200]}"
        )


def push_repo(world: wl.World, repo_dir: Path, repo: str, token: str) -> None:
    """Force-push every branch and tag to Gitea over HTTPS."""
    port = "" if world.https_port == 443 else f":{world.https_port}"
    remote = (
        f"https://{world.admin_user}:{token}@git.{world.domain}{port}"
        f"/{world.admin_user}/{repo}.git"
    )
    if "origin" in run_git(repo_dir, "remote").split():
        run_git(repo_dir, "remote", "remove", "origin")
    run_git(repo_dir, "remote", "add", "origin", remote)
    # The local CA is not in git's trust store; this is a local world over a
    # certificate we generated ourselves.
    env = {"GIT_SSL_CAINFO": str(wl.CA_CERT)} if wl.CA_CERT.exists() else {}
    run_git(repo_dir, "push", "--force", "--all", "origin", env=env)
    run_git(repo_dir, "push", "--force", "--tags", "origin", env=env)


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--repo", help="only process commits for this repo")
    parser.add_argument("--no-push", action="store_true",
                        help="replay and create repos but do not push")
    parser.add_argument("--work-dir", type=Path,
                        help="where to build repos (default: a temp directory)")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)
    commits_path = args.data_dir / "commits.jsonl"

    wl.heading("Parsing")
    commits = load_commits(commits_path, identities, problems)
    if args.repo:
        commits = [c for c in commits if c["repo"] == args.repo]
    problems.raise_if_any()

    if not commits:
        wl.warn("no commits to process")
        return 0

    repos = sorted({c["repo"] for c in commits})
    wl.ok(f"{len(commits)} commit(s) across {len(repos)} repo(s): {', '.join(repos)}")
    wl.ok(f"{len(identities)} persona(s) loaded")

    work_dir = args.work_dir or Path(tempfile.mkdtemp(prefix="sweworld-git-"))
    work_dir.mkdir(parents=True, exist_ok=True)

    wl.heading("Replaying history")
    for repo in repos:
        repo_dir = work_dir / repo
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        init_repo(repo_dir)
        for commit in [c for c in commits if c["repo"] == repo]:
            replay_commit(repo_dir, commit, verbose=args.verbose)
        count = len(run_git(repo_dir, "log", "--all", "--oneline").splitlines())
        wl.ok(f"{repo}: {count} commit(s) replayed")

    if args.dry_run:
        wl.heading("Dry run")
        wl.dry(f"repos built in {work_dir}")
        for repo in repos:
            wl.dry(f"would create gitea repo {world.admin_user}/{repo} if absent")
            wl.dry(f"would force-push all branches and tags for {repo}")
            print(f"\n{wl.GREY}--- git log {repo} ---{wl.RESET}")
            print(run_git(work_dir / repo, "log", "--all", "--format=  %h %ad %an: %s",
                          "--date=short"))
        wl.summarise(True, [f"{len(commits)} commit(s) replayed, 0 pushed"])
        return 0

    world.require("GITEA_API_TOKEN")
    token = world.env["GITEA_API_TOKEN"]

    wl.heading("Publishing to Gitea")
    for repo in repos:
        ensure_gitea_repo(world, repo, token)
        if args.no_push:
            wl.info(f"--no-push: skipping push for {repo}")
        else:
            push_repo(world, work_dir / repo, repo, token)
            # The trunk is the branch the repo's first commit went to.
            trunk = next(c["branch"] for c in commits if c["repo"] == repo)
            set_default_branch(world, repo, trunk, token)
            wl.ok(f"pushed {repo} (default branch: {trunk}) to "
                  f"{world.url('git', f'/{world.admin_user}/{repo}')}")

    wl.summarise(False, [
        f"{len(commits)} commit(s) across {len(repos)} repo(s)",
        f"working copies in {work_dir}",
    ])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\n\033[31mfailed\033[0m  {exc}", file=sys.stderr)
        raise SystemExit(1)
