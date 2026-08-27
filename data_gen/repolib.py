#!/usr/bin/env python3
"""Shared plumbing for the data_gen repository-mining scripts.

Both `analyze_repository.py` and `build_episodes.py` read the same repository
through the same lens, and neither should reimplement: how git is invoked, how
one human with four git identities is collapsed into one person, how a change
is classified, which subsystem a path belongs to, or what a Python symbol is.

Everything here is read-only. Nothing in this module writes to the mined
repository, and nothing checks anything out — the working tree of `curator/` is
never touched, only `git log`, `git show` and `git cat-file` are used.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPO = REPO_ROOT / "curator"
DEFAULT_BUILD_DIR = Path(__file__).resolve().parent / "build"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / "cache"

# git log records are split on these; both are control characters that cannot
# occur in a commit message, which \n and | very much can.
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

REC_SEP = "\x1e"
FIELD_SEP = "\x00"
# git wants the escape sequence in the format string; passing the raw control
# byte in argv fails with "embedded null byte" before git is even exec'd.
_FMT_REC, _FMT_FIELD = "%x1e", "%x00"


# =============================================================================
# Output
# =============================================================================
GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[90m", "\033[1m", "\033[0m"
)


def heading(text: str) -> None:
    print(f"\n{BOLD}{CYAN}==>{RESET} {BOLD}{text}{RESET}")


def ok(text: str) -> None:
    print(f"  {GREEN}ok{RESET}    {text}")


def info(text: str) -> None:
    print(f"  {GREY}{text}{RESET}")


def warn(text: str) -> None:
    print(f"  {YELLOW}warn{RESET}  {text}")


def fail(text: str) -> None:
    sys.exit(f"{RED}error{RESET} {text}")


# =============================================================================
# git
# =============================================================================
class Git:
    """A read-only handle on one repository.

    `core.quotepath=false` matters: without it git escapes any non-ASCII byte in
    a path as \\NNN octal, and the paths stop matching what is on disk.
    """

    def __init__(self, repo: Path):
        self.repo = Path(repo).resolve()
        if not (self.repo / ".git").exists():
            fail(f"{self.repo} is not a git repository (no .git). "
                 f"Pass --repo, or clone curator there.")

    def run(self, *args: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=false", "-C", str(self.repo), *args],
            capture_output=True, text=True, errors="replace",
        )
        if check and proc.returncode != 0:
            fail(f"git {' '.join(args[:3])}... failed: {proc.stderr.strip()}")
        return proc.stdout

    def lines(self, *args: str) -> list[str]:
        return [ln for ln in self.run(*args).splitlines() if ln]

    def head(self) -> str:
        return self.run("rev-parse", "HEAD").strip()

    def remote_url(self) -> str:
        return self.run("config", "--get", "remote.origin.url", check=False).strip()

    def is_shallow(self) -> bool:
        return self.run("rev-parse", "--is-shallow-repository").strip() == "true"

    def rev_at(self, when: str, branch: str = "") -> str | None:
        """The last commit on or before `when` (a YYYY-MM-DD date).

        Two things git will get wrong if you let it. A bare date means midnight,
        which excludes everything committed during the day you asked about, so
        the bound is the END of that day. And a bound with no timezone is read
        in the machine's local time, which makes the answer depend on where the
        laptop is: a commit at 19:00 -0700 belongs to the next UTC day, and
        without `+0000` it appeared or vanished depending on the reader's TZ.

        The corpus stamps everything in UTC, so the day boundary is UTC too.

        Returns None when the repository has nothing that old — a date before
        the first commit is a real answer, not an error.
        """
        rev = self.run("rev-list", "-1", f"--before={when} 23:59:59 +0000",
                       branch or "HEAD", check=False).strip()
        return rev or None

    def tree_at(self, rev: str, path: str = "") -> list[str]:
        """Paths under `path` at a revision, one level deep.

        Directories come back with a trailing slash, the way a person reading a
        listing expects to be able to tell them apart.
        """
        spec = f"{rev}:{path}" if path else rev
        out = []
        for line in self.lines("ls-tree", "--name-only", "-z", spec):
            for name in line.split("\0"):
                if name:
                    out.append(name)
        if not out:                      # -z on some versions returns one blob
            out = [n for n in self.run("ls-tree", "--name-only", spec,
                                       check=False).splitlines() if n]
        kinds = self.run("ls-tree", spec, check=False)
        dirs = {ln.split("\t", 1)[1] for ln in kinds.splitlines()
                if "\t" in ln and " tree " in ln}
        return sorted((f"{n}/" if n in dirs or f"{path}/{n}".strip("/") in dirs
                       else n) for n in out)

    def file_at(self, rev: str, path: str) -> str | None:
        """File content at a revision, or None if it does not exist there."""
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=false", "-C", str(self.repo),
             "show", f"{rev}:{path}"],
            capture_output=True, text=True, errors="replace",
        )
        return proc.stdout if proc.returncode == 0 else None

    def read_objects(self, refs: Sequence[str]) -> dict[str, str]:
        """Read arbitrary git objects (blob SHAs, rev:path) in one batch."""
        if not refs:
            return {}
        stdin = "".join(f"{r}\n" for r in refs).encode()
        proc = subprocess.run(
            ["git", "-C", str(self.repo), "cat-file", "--batch"],
            input=stdin, capture_output=True,
        )
        out, results, pos = proc.stdout, {}, 0
        for ref in refs:
            nl = out.find(b"\n", pos)
            if nl == -1:
                break
            header = out[pos:nl].decode("utf-8", "replace")
            if header.endswith(("missing", "ambiguous")):
                pos = nl + 1
                continue
            try:
                size = int(header.rsplit(" ", 1)[1])
            except (ValueError, IndexError):
                pos = nl + 1
                continue
            results[ref] = out[nl + 1: nl + 1 + size].decode("utf-8", "replace")
            pos = nl + 1 + size + 1   # trailing newline after the object
        return results

    def read_many(self, rev: str, paths: Sequence[str]) -> dict[str, str]:
        """Read many files at one revision in a single `git cat-file --batch`.

        One `git show` per file is a fork per file; on a few hundred files that
        dominates the runtime of the whole analysis.
        """
        blobs = self.read_objects([f"{rev}:{p}" for p in paths])
        return {p: blobs[f"{rev}:{p}"] for p in paths if f"{rev}:{p}" in blobs}

    def tree_of(self, rev: str) -> str:
        return self.run("rev-parse", f"{rev}^{{tree}}").strip()

    def contains(self, sha: str) -> bool:
        """Is this commit an ancestor of HEAD (i.e. in the mined history)?"""
        proc = subprocess.run(
            ["git", "-C", str(self.repo), "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True, text=True,
        )
        return proc.returncode == 0


def parse_owner_repo(remote_url: str) -> tuple[str, str] | None:
    """`https://github.com/bespokelabsai/curator.git` -> (bespokelabsai, curator)"""
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", remote_url)
    return (m.group(1), m.group(2)) if m else None


# =============================================================================
# Commits
# =============================================================================
# A trailing separator after %b is what makes this unambiguous: --numstat
# prints after the format string, so without it the stat block is
# indistinguishable from the last paragraph of a commit message.
_LOG_FORMAT = _FMT_FIELD.join(
    ["%H", "%P", "%an", "%ae", "%aI", "%cn", "%ce", "%cI", "%s", "%b", ""]
)


@dataclass
class Commit:
    sha: str
    parents: list[str]
    author_name: str
    author_email: str
    authored_at: str
    committer_name: str
    committer_email: str
    committed_at: str
    subject: str
    body: str
    files: list[dict] = field(default_factory=list)   # {path, added, deleted, from_path}

    @property
    def is_merge(self) -> bool:
        return len(self.parents) > 1

    @property
    def message(self) -> str:
        return f"{self.subject}\n\n{self.body}".strip()

    @property
    def paths(self) -> list[str]:
        return [f["path"] for f in self.files]

    @property
    def lines_added(self) -> int:
        return sum(f["added"] for f in self.files)

    @property
    def lines_deleted(self) -> int:
        return sum(f["deleted"] for f in self.files)

    def coauthors(self) -> list[tuple[str, str]]:
        out = []
        for m in re.finditer(r"^Co-authored-by:\s*(.+?)\s*<([^>]+)>",
                             self.body, re.MULTILINE | re.IGNORECASE):
            out.append((m.group(1).strip(), m.group(2).strip().lower()))
        return out


def _parse_numstat(block: str) -> list[dict]:
    """Parse the --numstat tail of one log record.

    Renames arrive either as `old => new` inside one path, or as the
    NUL-separated three-field form when -z is in play. Only the former can
    appear here, since the record separator is doing the framing.
    """
    files = []
    for line in block.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        from_path = None
        m = re.match(r"^(.*)\{(.*) => (.*)\}(.*)$", path)
        if m:
            pre, old, new, post = m.groups()
            from_path = f"{pre}{old}{post}".replace("//", "/")
            path = f"{pre}{new}{post}".replace("//", "/")
        elif " => " in path:
            from_path, path = path.split(" => ", 1)
        files.append({
            "path": path,
            # "-" is git's marker for a binary file: no line counts exist.
            "added": int(added) if added.isdigit() else 0,
            "deleted": int(deleted) if deleted.isdigit() else 0,
            "binary": not added.isdigit(),
            "from_path": from_path,
        })
    return files


def load_commits(git: Git, *, rev: str = "HEAD", since: str | None = None,
                 until: str | None = None, with_files: bool = True) -> list[Commit]:
    """Every commit reachable from `rev`, oldest first, with per-file stats.

    Merges get an empty file list: `--numstat` on a merge with no -m prints
    nothing, and attributing a merge's combined diff to the merge itself would
    double-count every file its branch already touched.
    """
    args = ["log", f"--format={_FMT_REC}{_LOG_FORMAT}", "--reverse"]
    if with_files:
        args.append("--numstat")
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    args.append(rev)

    raw = git.run(*args)
    commits: list[Commit] = []
    for record in raw.split(REC_SEP):
        if not record.strip():
            continue
        fields = record.split(FIELD_SEP)
        if len(fields) < 11:
            continue
        body, stat_block = fields[9], fields[10]

        commits.append(Commit(
            sha=fields[0].strip(),
            parents=fields[1].split() if fields[1].strip() else [],
            author_name=fields[2], author_email=fields[3].lower(), authored_at=fields[4],
            committer_name=fields[5], committer_email=fields[6].lower(), committed_at=fields[7],
            subject=fields[8], body=body.strip(),
            files=_parse_numstat(stat_block),
        ))
    return commits


# =============================================================================
# Identities
# =============================================================================
# Some people commit under names that share neither email nor spelling, and no
# automatic rule can join them. That is a fact about a particular repository, so
# it lives in an optional file beside the scripts rather than in the code:
#
#   data_gen/aliases.yaml
#     thedude: kartik4949
#     adamoptimizer: kartik4949
#
# Keys and values are lowercased author names; everything sharing a value is one
# person. Absent file, the automatic joins (shared email, shared name, the login
# inside a users.noreply.github.com address) do all the work.
ALIASES_FILE = Path(__file__).resolve().parent / "aliases.yaml"


def load_aliases(path: Path | None = None) -> dict[str, str]:
    target = path or ALIASES_FILE
    if not target.exists():
        return {}
    try:
        import yaml
        data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 — a broken alias file must not stop analysis
        return {}
    return {str(k).strip().lower(): str(v).strip().lower()
            for k, v in data.items() if k and v}


NAME_ALIASES: dict[str, str] = load_aliases()

BOT_NAMES = re.compile(r"(\[bot\]|^devin ai$|^dependabot|^github-actions|^claude\b)", re.I)
BOT_EMAILS = re.compile(r"(noreply@anthropic\.com|dependabot|devin-ai-integration)", re.I)

_NOREPLY_RE = re.compile(r"^(?:\d+\+)?([^@]+)@users\.noreply\.github\.com$")


class _Union:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


@dataclass
class Person:
    id: str
    display_name: str
    emails: list[str]
    names: list[str]
    github_login: str | None
    is_bot: bool
    commits: int = 0


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "unknown"


class Identities:
    """Collapses (name, email) pairs into people.

    Joined transitively on: shared email, shared lowercased name, the GitHub
    login embedded in a `NNN+login@users.noreply.github.com` address, and the
    explicit NAME_ALIASES table for the pairs that share none of those.
    """

    def __init__(self, pairs: Iterable[tuple[str, str]]):
        uf = _Union()
        seen: list[tuple[str, str]] = []
        for name, email in pairs:
            name, email = (name or "").strip(), (email or "").strip().lower()
            key = f"pair:{name.lower()}|{email}"
            uf.find(key)
            seen.append((name, email))
            uf.union(key, f"email:{email}")
            canonical_name = NAME_ALIASES.get(name.lower(), name.lower())
            uf.union(key, f"name:{canonical_name}")
            m = _NOREPLY_RE.match(email)
            if m:
                login = m.group(1).lower()
                uf.union(key, f"name:{NAME_ALIASES.get(login, login)}")

        groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for name, email in seen:
            groups[uf.find(f"pair:{name.lower()}|{email}")].append((name, email))

        self._by_pair: dict[tuple[str, str], str] = {}
        self.people: dict[str, Person] = {}
        for members in groups.values():
            names = Counter(n for n, _ in members if n)
            emails = sorted({e for _, e in members if e})
            display = names.most_common(1)[0][0] if names else emails[0]
            login = None
            for _, e in members:
                m = _NOREPLY_RE.match(e)
                if m:
                    login = m.group(1)
                    break
            pid = slugify(display)
            while pid in self.people:
                pid += "-2"
            is_bot = any(BOT_NAMES.search(n) for n, _ in members) or \
                     any(BOT_EMAILS.search(e) for _, e in members)
            self.people[pid] = Person(
                id=pid, display_name=display, emails=emails,
                names=sorted(names), github_login=login, is_bot=is_bot,
            )
            for pair in members:
                self._by_pair[(pair[0].lower(), pair[1])] = pid

    @classmethod
    def from_commits(cls, commits: Sequence[Commit]) -> "Identities":
        pairs: list[tuple[str, str]] = []
        for c in commits:
            pairs.append((c.author_name, c.author_email))
            pairs.append((c.committer_name, c.committer_email))
            pairs.extend(c.coauthors())
        ids = cls(pairs)
        for c in commits:
            pid = ids.of(c.author_name, c.author_email)
            if pid:
                ids.people[pid].commits += 1
        return ids

    def of(self, name: str, email: str) -> str | None:
        return self._by_pair.get(((name or "").strip().lower(), (email or "").strip().lower()))

    def as_json(self) -> list[dict]:
        return [
            {"id": p.id, "display_name": p.display_name, "emails": p.emails,
             "names": p.names, "github_login": p.github_login, "is_bot": p.is_bot,
             "commits": p.commits}
            for p in sorted(self.people.values(), key=lambda p: -p.commits)
        ]


# =============================================================================
# Layout discovery
# =============================================================================
# Where a repository keeps its source, tests, docs and packaging is a fact about
# that repository, not a constant. Hardcoding one project's layout does not fail
# loudly on another — every lookup simply matches nothing and the analysis comes
# back empty while still exiting 0. So the layout is discovered, and a discovery
# that finds no source at all says so.
SOURCE_EXTS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt",
    ".rb", ".php", ".cs", ".swift", ".scala", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".m", ".mm", ".sh", ".ex", ".exs", ".clj", ".lua", ".pl", ".r",
}
TEST_DIR_NAMES = {"test", "tests", "spec", "specs", "__tests__", "testing", "e2e"}
DOC_DIR_NAMES = {"doc", "docs", "documentation", "website", "site"}
EXAMPLE_DIR_NAMES = {"example", "examples", "sample", "samples", "demo", "demos",
                     "cookbook", "recipes", "tutorials"}
VENDOR_DIR_NAMES = {"vendor", "third_party", "thirdparty", "node_modules", "external",
                    ".git", "dist", "build", "target"}
CI_PATHS = [".github/workflows", ".gitea/workflows", ".gitlab-ci.yml", ".circleci",
            ".buildkite", ".travis.yml", "azure-pipelines.yml", "Jenkinsfile",
            ".drone.yml", "appveyor.yml"]
PACKAGING_FILES = [
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile",
    "package.json", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
    "build.gradle.kts", "Gemfile", "composer.json", "Makefile", "CMakeLists.txt",
    "poetry.lock", "package-lock.json", "yarn.lock", "Cargo.lock", "go.sum",
    "pytest.ini", "tox.ini", "noxfile.py", ".pre-commit-config.yaml", ".gitignore",
    ".gitattributes", ".editorconfig", ".dockerignore", "Dockerfile", "LICENSE",
    "LICENSE.md", "LICENSE.txt", "NOTICE",
]
# A release or build script at the repository root is packaging, whatever it is
# called in a given project.
BUILD_SCRIPT_RE = re.compile(
    r"^(publish|release|build|install|setup|bootstrap|deploy)[-_a-z0-9]*\.(sh|bash|ps1)$")
TEST_FILE_RE = re.compile(r"(^|/)(test_[^/]+|[^/]+_test|[^/]+\.spec|[^/]+\.test)\.[a-z]+$")


@dataclass
class Layout:
    """Where this repository keeps things, discovered rather than assumed."""

    source_roots: list[str] = field(default_factory=list)
    import_prefixes: list[str] = field(default_factory=list)
    local_modules: list[str] = field(default_factory=list)
    test_roots: list[str] = field(default_factory=list)
    doc_roots: list[str] = field(default_factory=list)
    example_roots: list[str] = field(default_factory=list)
    ci_paths: list[str] = field(default_factory=list)
    packaging_files: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    primary_language: str = "unknown"
    source_files: int = 0
    source_ancestors: list[str] = field(default_factory=list)
    module_bases: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    @property
    def confident(self) -> bool:
        return bool(self.source_roots) and self.source_files > 0

    def as_json(self) -> dict:
        return {
            "source_roots": self.source_roots, "import_prefixes": self.import_prefixes,
            "test_roots": self.test_roots, "doc_roots": self.doc_roots,
            "example_roots": self.example_roots, "ci_paths": self.ci_paths,
            "packaging_files": self.packaging_files, "languages": self.languages,
            "primary_language": self.primary_language, "source_files": self.source_files,
            "confident": self.confident, "how_it_was_found": self.evidence,
        }

    def under_source(self, path: str) -> str | None:
        for root in self.source_roots:
            if path == root or path.startswith(root + "/"):
                return root
        return None

    def is_source(self, path: str) -> bool:
        """Under a source root, or under the package plumbing above one."""
        if self.under_source(path):
            return True
        return any(path.startswith(a + "/") for a in self.source_ancestors)

    def role_of(self, path: str) -> str:
        for root in self.test_roots:
            if path.startswith(root + "/") or path == root:
                return "tests"
        if TEST_FILE_RE.search(path):
            return "tests"
        for root in self.doc_roots:
            if path.startswith(root + "/"):
                return "docs"
        for root in self.example_roots:
            if path.startswith(root + "/"):
                return "examples"
        for ci in self.ci_paths:
            if path == ci or path.startswith(ci + "/"):
                return "ci"
        if self.is_source(path):
            return "src"
        if path.endswith((".md", ".rst")):
            return "docs"
        name = Path(path).name
        if name in PACKAGING_FILES:
            return "packaging"
        if "/" not in path and BUILD_SCRIPT_RE.match(name):
            return "packaging"
        return "other"


def _declared_python_roots(pyproject: str | None, paths: set[str]) -> tuple[list[str], str]:
    """Source roots a Python project states outright, from pyproject.toml."""
    if not pyproject:
        return [], ""
    try:
        data = parse_toml(pyproject)
    except Exception:  # noqa: BLE001 — a broken manifest is not a crash
        return [], ""
    roots: list[str] = []
    poetry = data.get("tool", {}).get("poetry", {})
    for entry in poetry.get("packages", []) or []:
        if isinstance(entry, dict) and entry.get("include"):
            base = entry.get("from")
            roots.append(f"{base}/{entry['include']}" if base else entry["include"])
    setuptools = data.get("tool", {}).get("setuptools", {})
    for base in (setuptools.get("package-dir") or {}).values():
        roots.append(base)
    name = poetry.get("name") or data.get("project", {}).get("name") or ""
    if not roots and name:
        for candidate in (f"src/{name.replace('-', '_')}", name.replace("-", "_")):
            if any(p.startswith(candidate + "/") for p in paths):
                roots.append(candidate)
    return [r.strip("/") for r in roots if r], "pyproject.toml"


def discover_layout(git: Git, rev: str = "HEAD") -> Layout:
    paths = git.lines("ls-tree", "-r", "--name-only", rev)
    path_set = set(paths)
    layout = Layout()

    languages = Counter()
    for path in paths:
        suffix = Path(path).suffix.lower()
        if suffix in SOURCE_EXTS:
            languages[language_of(path)] += 1
    layout.languages = dict(languages.most_common())
    layout.primary_language = languages.most_common(1)[0][0] if languages else "unknown"

    def top_dirs(names: set[str]) -> list[str]:
        found = set()
        for path in paths:
            parts = path.split("/")
            for depth in (1, 2):
                if len(parts) > depth and parts[depth - 1].lower() in names:
                    found.add("/".join(parts[:depth]))
                    break
        return sorted(found)

    layout.test_roots = top_dirs(TEST_DIR_NAMES)
    layout.doc_roots = top_dirs(DOC_DIR_NAMES)
    layout.example_roots = top_dirs(EXAMPLE_DIR_NAMES)
    layout.ci_paths = [c for c in CI_PATHS
                       if c in path_set or any(p.startswith(c + "/") for p in paths)]
    layout.packaging_files = sorted(
        {p for p in paths if Path(p).name in PACKAGING_FILES and "/" not in p})

    excluded = set(layout.test_roots + layout.doc_roots + layout.example_roots)

    def is_excluded(path: str) -> bool:
        parts = path.split("/")
        if parts[0] in VENDOR_DIR_NAMES:
            return True
        return any(path.startswith(e + "/") for e in excluded)

    source_paths = [p for p in paths
                    if Path(p).suffix.lower() in SOURCE_EXTS and not is_excluded(p)]
    layout.source_files = len(source_paths)

    # 1. What the project declares about itself.
    pyproject = None
    if "pyproject.toml" in path_set:
        pyproject = git.read_many(rev, ["pyproject.toml"]).get("pyproject.toml")
    roots, how = _declared_python_roots(pyproject, path_set)
    roots = [r for r in roots if any(p.startswith(r + "/") for p in paths)]
    if roots:
        layout.evidence.append(f"source roots declared in {how}: {', '.join(roots)}")

    # 2. Otherwise the shallowest importable packages.
    if not roots:
        packages = sorted({str(Path(p).parent) for p in paths
                           if Path(p).name == "__init__.py" and not is_excluded(p)},
                          key=lambda d: (d.count("/"), d))
        shallowest = [d for d in packages
                      if not any(d.startswith(o + "/") for o in packages if o != d)]
        if shallowest:
            roots = shallowest
            layout.evidence.append(
                f"shallowest packages containing __init__.py: {', '.join(roots)}")

    # 3. Otherwise the directories the source actually lives in.
    if not roots and source_paths:
        counts = Counter(p.split("/")[0] if "/" in p else "." for p in source_paths)
        roots = sorted({d for d, n in counts.items() if d != "." and n >= 2})
        if not roots and counts:
            roots = ["."]
        layout.evidence.append(
            f"directories holding {layout.primary_language} sources: {', '.join(roots)}")

    # 4. Step through pass-through package dirs — `src/acme/` holding nothing but
    #    __init__.py and one subpackage is not itself the interesting root.
    resolved = []
    for root in roots:
        current = root
        for _ in range(4):
            children = {p[len(current) + 1:].split("/")[0]
                        for p in paths if p.startswith(current + "/")}
            subdirs = {c for c in children
                       if any(p.startswith(f"{current}/{c}/") for p in paths)}
            files = children - subdirs
            if len(subdirs) == 1 and len(files - {"__init__.py"}) == 0:
                current = f"{current}/{next(iter(subdirs))}"
                layout.evidence.append(f"descended pass-through package into {current}")
                continue
            break
        resolved.append(current)
    layout.source_roots = sorted(set(resolved))

    # Import prefixes: the top-level importable name above each source root, so
    # `src/acme/thing` yields `acme` — which is what its own imports say.
    prefixes, modules = set(), set()
    for root in layout.source_roots:
        parts = root.split("/")
        for depth in range(len(parts), 0, -1):
            candidate = "/".join(parts[:depth])
            if f"{candidate}/__init__.py" in path_set:
                prefixes.add(parts[depth - 1])
            else:
                break
        prefixes.add(parts[-1])
        for path in paths:
            if path.startswith(root + "/") and path.endswith(".py"):
                rest = path[len(root) + 1:]
                if "/" not in rest:
                    modules.add(rest[:-3])
    # Where a dotted module name starts: the first ancestor that is *not* itself
    # a package. `src/acme/thing` imports as `acme.thing`, so the base is `src` —
    # stripping the whole parent would yield `thing` and match no import.
    bases = set()
    for root in layout.source_roots:
        current = root
        while True:
            parent = str(Path(current).parent)
            if parent in (".", "") or f"{parent}/__init__.py" not in path_set:
                break
            current = parent
        parent = str(Path(current).parent)
        bases.add(parent if parent not in (".", "") else current)
    layout.module_bases = sorted(bases, key=len, reverse=True)

    layout.source_ancestors = sorted(
        {str(Path(r).parent) for r in layout.source_roots
         if str(Path(r).parent) not in (".", "")}, key=len, reverse=True)
    layout.import_prefixes = sorted(p for p in prefixes if p not in (".", ""))
    layout.local_modules = sorted(modules)
    return layout


# =============================================================================
# Languages and subsystems
# =============================================================================
LANGUAGES = {
    ".py": "python", ".pyi": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".sh": "shell", ".bash": "shell",
    ".md": "markdown", ".rst": "restructuredtext", ".txt": "text",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".json": "json",
    ".cfg": "config", ".ini": "config", ".lock": "lockfile", ".sql": "sql",
    ".png": "image", ".jpg": "image", ".gif": "image", ".svg": "image",
    ".parquet": "data", ".csv": "data", ".zip": "archive",
}


def language_of(path: str) -> str:
    name = Path(path).name
    if name in ("Makefile", "Dockerfile"):
        return name.lower()
    return LANGUAGES.get(Path(path).suffix.lower(), "other")


# Where a path sits in the product, independent of which package it is in.
FILE_ROLES = [
    (re.compile(r"^tests?/"), "tests"),
    (re.compile(r"^examples/"), "examples"),
    (re.compile(r"^docs?/"), "docs"),
    (re.compile(r"^\.github/"), "ci"),
    (re.compile(r"^src/"), "src"),
    (re.compile(r"^(pyproject\.toml|poetry\.lock|Makefile|pytest\.ini|"
                r"\.pre-commit-config\.yaml|publish_pkg\.sh|\.gitignore|LICENSE)$"), "packaging"),
    (re.compile(r"\.md$"), "docs"),
]


def file_role(path: str, layout: "Layout | None" = None) -> str:
    if layout is not None:
        return layout.role_of(path)
    for pattern, role in FILE_ROLES:
        if pattern.search(path):
            return role
    return "other"


class SubsystemMap:
    """Maps a repo-relative path to a subsystem key.

    Package names are read off the discovered source roots rather than a
    hardcoded path, so this works on a repository laid out any way. Longest
    prefix wins, so `request_processor/batch` beats `request_processor`.
    """

    def __init__(self, git: Git, rev: str = "HEAD", layout: "Layout | None" = None):
        self.layout = layout if layout is not None else discover_layout(git, rev)
        paths = git.lines("ls-tree", "-r", "--name-only", rev)
        self.packages: dict[str, list[str]] = {}
        for root in self.layout.source_roots:
            prefixes: set[str] = set()
            for path in paths:
                if not path.startswith(root + "/"):
                    continue
                parts = path[len(root) + 1:].split("/")
                if len(parts) >= 2:
                    prefixes.add(parts[0])
                if len(parts) >= 3:
                    prefixes.add(f"{parts[0]}/{parts[1]}")
            self.packages[root] = sorted(prefixes, key=len, reverse=True)
        # `src/` above `src/acme/thing` is package plumbing, not a subsystem, but
        # it is still source and must not fall through to "other".
        self.source_ancestors = sorted(
            {str(Path(root).parent) for root in self.layout.source_roots
             if str(Path(root).parent) not in (".", "")},
            key=len, reverse=True)
        self.multi_root = len(self.layout.source_roots) > 1

    def _root_label(self, root: str) -> str:
        return Path(root).name

    def of(self, path: str) -> str:
        root = self.layout.under_source(path)
        if root:
            rel = path[len(root) + 1:] if path != root else ""
            for package in self.packages.get(root, []):
                if rel.startswith(package + "/"):
                    return f"{self._root_label(root)}/{package}" if self.multi_root else package
            return self._root_label(root) if self.multi_root else "core"
        for ancestor in self.source_ancestors:
            if path.startswith(ancestor + "/"):
                return self._root_label(ancestor) if self.multi_root else "core"
        role = self.layout.role_of(path)
        if role in ("tests", "examples"):
            roots = (self.layout.test_roots if role == "tests"
                     else self.layout.example_roots)
            for base in sorted(roots, key=len, reverse=True):
                if path.startswith(base + "/"):
                    rest = path[len(base) + 1:].split("/")
                    return f"{base}/{rest[0]}" if len(rest) > 1 else base
            parts = path.split("/")
            return f"{role}/{parts[1]}" if len(parts) > 2 else role
        return role

    @property
    def src_roots(self) -> list[str]:
        return self.layout.source_roots


# =============================================================================
# Change classification
# =============================================================================
CHANGE_TYPES = [
    "feature", "bugfix", "refactor", "test", "docs", "dependency",
    "ci", "build", "release", "perf", "chore", "unclassified",
]

_CONVENTIONAL = {
    "feat": "feature", "feature": "feature", "fix": "bugfix", "bugfix": "bugfix",
    "hotfix": "bugfix", "refactor": "refactor", "style": "refactor",
    "test": "test", "tests": "test", "docs": "docs", "doc": "docs",
    "perf": "perf", "build": "build", "ci": "ci", "chore": "chore",
    "revert": "bugfix", "deps": "dependency", "dep": "dependency",
}
_CONVENTIONAL_RE = re.compile(r"^\s*([a-z]+)(?:\([^)]*\))?!?\s*:", re.I)
_RELEASE_RE = re.compile(r"\b(bump|release|publish)\b.*\bv?\d+\.\d+\.\d+|"
                         r"\bv?\d+\.\d+\.\d+\b.*\brelease\b", re.I)
_DEP_PATHS = re.compile(r"^(poetry\.lock|pyproject\.toml|requirements[^/]*\.txt)$")
# Stems, not whole words. curator's early history is full of terse subjects
# ("Minor refactoring and cleanups.", "simplified version without Dataset
# wrapper"), and a trailing \b turns every one of them into an unclassified
# chore.
_KEYWORDS = [
    (re.compile(r"\b(fix|bug|regression|broken|crash|traceback|revert|hotfix|workaround|"
                r"error handl|fail)", re.I), "bugfix"),
    (re.compile(r"\b(add|support|introduc|implement|enabl|new |allow|expos)", re.I), "feature"),
    (re.compile(r"\b(refactor|cleanup|clean up|clean-up|simplif|renam|reorganis|reorganiz|"
                r"remov|delet|dedup|extract|inline|restructur|split|merg|consolidat|"
                r"black|isort|ruff|format|lint|tidy|unus|minor)", re.I), "refactor"),
    (re.compile(r"\b(test|pytest|cassette|coverage|fixture|mock)", re.I), "test"),
    (re.compile(r"\b(readme|docstring|document|typo|comment|example|tutorial)", re.I), "docs"),
    (re.compile(r"\b(bump|upgrade|downgrade|\bpin\b|dependenc|requirement|poetry\.lock)", re.I),
     "dependency"),
    (re.compile(r"\b(pre-commit|workflow|\bci\b|github action|pipeline)", re.I), "ci"),
    (re.compile(r"\b(speed|faster|latency|throughput|perf|optimi[sz]|concurren|parallel|cache)",
                re.I), "perf"),
]
_WEAK_EDIT_RE = re.compile(
    r"\b(use|using|switch|chang|updat|better|improv|port|shorten|correct|"
    r"init|initial|handl|make|set|move|bump|tweak|adjust|wip)", re.I)
_BRANCH_RE = re.compile(r"^(?:[^/]+/)?(feat|feature|fix|bugfix|hotfix|refactor|test|docs?|ci|chore|deps?|perf)[-/_]", re.I)


def classify_change(paths: Sequence[str], subject: str, body: str = "",
                    branch: str | None = None) -> dict:
    """Decide what kind of engineering work a change is, and say why.

    Every rule that fires is recorded, so a consumer can see the reasoning
    rather than trusting a bare label. Weights are ordered by how much the
    signal actually means: an author writing `fix:` is stronger evidence than
    the word "error" appearing somewhere in the body.
    """
    scores: Counter[str] = Counter()
    evidence: list[dict] = []

    def add(kind: str, weight: float, rule: str, detail: str) -> None:
        scores[kind] += weight
        evidence.append({"rule": rule, "type": kind, "weight": weight, "detail": detail})

    m = _CONVENTIONAL_RE.match(subject)
    if m and m.group(1).lower() in _CONVENTIONAL:
        kind = _CONVENTIONAL[m.group(1).lower()]
        add(kind, 3.0, "conventional-commit", f"subject prefix {m.group(1).lower()}:")

    if _RELEASE_RE.search(subject):
        add("release", 3.5, "version-bump", subject.strip()[:80])

    if branch:
        bm = _BRANCH_RE.match(branch)
        if bm:
            key = bm.group(1).lower()
            add(_CONVENTIONAL.get(key, key), 2.0, "branch-name", branch)

    if paths:
        roles = Counter(file_role(p) for p in paths)
        total = len(paths)
        if roles["tests"] == total:
            add("test", 2.5, "paths-exclusive", "every changed file is under tests/")
        elif roles["tests"] >= total * 0.5:
            add("test", 1.0, "paths-majority", f"{roles['tests']}/{total} files under tests/")
        if roles["ci"] == total:
            add("ci", 2.5, "paths-exclusive", "every changed file is a workflow")
        elif roles["ci"]:
            add("ci", 1.0, "paths-some", f"{roles['ci']}/{total} workflow files")
        if roles["docs"] == total:
            add("docs", 2.5, "paths-exclusive", "every changed file is documentation")
        elif roles["docs"] >= total * 0.5:
            add("docs", 1.0, "paths-majority", f"{roles['docs']}/{total} doc files")
        dep_files = [p for p in paths if _DEP_PATHS.match(p)]
        if dep_files and len(dep_files) == total:
            add("dependency", 2.5, "paths-exclusive", ", ".join(dep_files))
        elif dep_files:
            add("dependency", 0.8, "paths-some", ", ".join(dep_files))

    text = f"{subject}\n{body[:2000]}"
    for pattern, kind in _KEYWORDS:
        if pattern.search(text):
            add(kind, 0.8, "keyword", pattern.pattern.split("\\b")[1][:40])

    if not scores and _WEAK_EDIT_RE.search(subject):
        add("refactor", 0.5, "weak-keyword", "modification verb, no stronger signal")

    if not scores:
        # Deliberately not "chore": an unreadable subject is unknown work, and
        # calling it a chore would put a wrong fact into the grounding.
        return {"primary": "unclassified", "secondary": [], "confidence": 0.0,
                "evidence": [{"rule": "default", "type": "unclassified", "weight": 0.0,
                              "detail": "no rule matched"}]}

    ranked = scores.most_common()
    top_type, top_weight = ranked[0]
    total_weight = sum(scores.values())
    return {
        "primary": top_type,
        "secondary": [k for k, w in ranked[1:] if w >= 1.0],
        "confidence": round(top_weight / total_weight, 3),
        "evidence": evidence,
    }


# =============================================================================
# Python symbols
# =============================================================================
def python_symbols(source: str) -> dict[str, str]:
    """Qualified symbol name -> hash of its source text.

    Top-level functions and classes, plus one level of methods. The hash is
    what makes "modified" distinguishable from "present in both revisions"
    without diffing line ranges that shift whenever anything above them moves.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return {}

    lines = source.splitlines()

    def digest(node: ast.AST) -> str:
        start = getattr(node, "lineno", 1) - 1
        end = getattr(node, "end_lineno", start + 1)
        return hashlib.sha1("\n".join(lines[start:end]).encode()).hexdigest()[:12]

    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = digest(node)
        elif isinstance(node, ast.ClassDef):
            out[node.name] = digest(node)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{sub.name}"] = digest(sub)
    return out


def diff_symbols(before: str | None, after: str | None) -> dict[str, list[str]]:
    a = python_symbols(before) if before else {}
    b = python_symbols(after) if after else {}
    return {
        "added": sorted(set(b) - set(a)),
        "removed": sorted(set(a) - set(b)),
        "modified": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
    }


# =============================================================================
# TOML
# =============================================================================
# This box has Python 3.10 (no tomllib) and no pip (no tomli), and the only
# TOML this project reads is a Poetry pyproject: tables, dotted keys, strings,
# numbers, booleans, arrays and inline tables. That subset is small enough to
# parse correctly here, and a wrong answer is loud rather than silent because
# every consumer looks up known keys.
def _strip_comment(line: str) -> str:
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def _toml_value(text: str, i: int = 0) -> tuple[Any, int]:
    while i < len(text) and text[i] in " \t\n":
        i += 1
    if i >= len(text):
        raise ValueError("truncated TOML value")
    ch = text[i]
    if ch in "\"'":
        quote, i, buf = ch, i + 1, []
        while i < len(text) and text[i] != quote:
            if quote == '"' and text[i] == "\\" and i + 1 < len(text):
                escapes = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
                buf.append(escapes.get(text[i + 1], text[i + 1]))
                i += 2
                continue
            buf.append(text[i])
            i += 1
        return "".join(buf), i + 1
    if ch == "[":
        items, i = [], i + 1
        while True:
            while i < len(text) and text[i] in " \t\n,":
                i += 1
            if i < len(text) and text[i] == "]":
                return items, i + 1
            if i >= len(text):
                raise ValueError("unterminated TOML array")
            value, i = _toml_value(text, i)
            items.append(value)
    if ch == "{":
        table, i = {}, i + 1
        while True:
            while i < len(text) and text[i] in " \t\n,":
                i += 1
            if i < len(text) and text[i] == "}":
                return table, i + 1
            if i >= len(text):
                raise ValueError("unterminated TOML inline table")
            eq = text.index("=", i)
            key = text[i:eq].strip().strip("\"'")
            value, i = _toml_value(text, eq + 1)
            table[key] = value
    end = i
    while end < len(text) and text[end] not in ",]}\n":
        end += 1
    token = text[i:end].strip()
    if token == "true":
        return True, end
    if token == "false":
        return False, end
    try:
        return int(token), end
    except ValueError:
        pass
    try:
        return float(token), end
    except ValueError:
        return token, end


def parse_toml(text: str) -> dict:
    root: dict = {}
    current = root
    buffer = ""
    for raw in text.splitlines():
        line = _strip_comment(raw) if not buffer else raw.split("#")[0].rstrip()
        if not buffer and not line.strip():
            continue
        if not buffer and line.lstrip().startswith("["):
            header = line.strip()
            is_array = header.startswith("[[")
            path = header.strip("[]").strip()
            node = root
            for part in [p.strip().strip("\"'") for p in path.split(".")]:
                if is_array and part == path.split(".")[-1].strip():
                    node.setdefault(part, [])
                    if isinstance(node[part], list):
                        node[part].append({})
                        node = node[part][-1]
                        break
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    node = {}
            current = node
            continue
        buffer = f"{buffer}\n{line}" if buffer else line
        if buffer.count("[") != buffer.count("]") or buffer.count("{") != buffer.count("}"):
            continue
        if "=" not in buffer:
            buffer = ""
            continue
        key_part, _, value_part = buffer.partition("=")
        try:
            value, _ = _toml_value(value_part)
        except (ValueError, IndexError):
            buffer = ""
            continue
        node = current
        keys = [k.strip().strip("\"'") for k in key_part.strip().split(".")]
        for part in keys[:-1]:
            node = node.setdefault(part, {})
        node[keys[-1]] = value
        buffer = ""
    return root


# =============================================================================
# Environment
# =============================================================================
def env_value(name: str, *, env_files: Sequence[Path] | None = None) -> str | None:
    """A secret from the environment, else from a gitignored dotenv file.

    Env vars do not survive between shells, and this repository already keeps
    its service tokens in a gitignored .env — so that is where the API keys for
    data_gen belong too, rather than in a per-invocation export.
    """
    value = os.environ.get(name, "").strip()
    if value:
        return value
    candidates = env_files or (Path(__file__).resolve().parent / ".env", REPO_ROOT / ".env")
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, raw = line.partition("=")
            if key.strip() == name:
                cleaned = raw.strip().strip("'\"")
                if cleaned:
                    return cleaned
    return None


# =============================================================================
# Claude
# =============================================================================
MODEL = "claude-opus-5"
# What `claude --model` is given when the CLI backend is in use. The CLI takes
# short aliases and resolves them itself.
CLAUDE_CLI = "claude"
CLI_MODEL = "sonnet"
# A contended subscription drops calls; three tries clears almost all of it.
CLI_ATTEMPTS = 3
CLI_BACKOFF_S = 20
# A tool name nothing will ever match, which is how you allow none of them.
# Models that take neither `thinking` nor `effort`. Passing either is a 400.
LIGHTWEIGHT_MODEL = re.compile(r"haiku", re.I)
CLI_ALLOW_NOTHING = "NoToolIsPermittedHere"
CLI_MAX_TURNS = 4
# Claude Code's OAuth tokens are issued against a beta flow, and the Messages API
# rejects them without this header even though the CLI accepts the same value.
OAUTH_BETA = "oauth-2025-04-20"
# Published rates for claude-opus-5, used only to report what a run cost.
COST_PER_MTOK_IN, COST_PER_MTOK_OUT = 5.0, 25.0
# Writing to the cache costs 1.25x the input rate; reading from it costs 0.1x.
COST_PER_MTOK_CACHE_WRITE, COST_PER_MTOK_CACHE_READ = 6.25, 0.5

_SETUP_HELP = """
  This box has no pip, so install the SDK into a venv with uv:

    uv venv --python /usr/bin/python3.10 --system-site-packages data_gen/.venv
    uv pip install --python data_gen/.venv/bin/python anthropic

  then run the script with that interpreter:

    data_gen/.venv/bin/python data_gen/analyze_repository.py
"""


_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.M)


def _parse_json_object(text: str) -> dict:
    """Pull the JSON object out of a CLI reply.

    The SDK path gets schema-enforced JSON and needs none of this. The CLI is
    asked in words, so a reply occasionally arrives wrapped in a code fence or
    with a sentence in front of it. Strip the fence, then fall back to the
    outermost braces — and if neither yields an object, fail with the text
    included, because "expecting value: line 1 column 1" says nothing about what
    actually came back.
    """
    cleaned = _FENCE_RE.sub("", text).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise RuntimeError(
                f"no JSON object in the reply: {cleaned[:300]!r}") from None
        parsed = json.loads(cleaned[start:end + 1])
    if not isinstance(parsed, dict):
        raise RuntimeError(f"expected a JSON object, got {type(parsed).__name__}")
    return parsed


class Refused(RuntimeError):
    """The model declined the request and no fallback could answer it."""


class LLM:
    """A cached Claude client, shaped like github_api.GitHub so the two read alike.

    Interpretation is not reproducible the way `git log` is, so every response is
    written to `cache/llm/`, keyed by everything that determines it: model,
    effort, system prompt, user prompt and output schema. Re-running the script
    then costs nothing and produces the same bytes, and `--no-refresh` will not
    open a socket at all.
    """

    def __init__(self, cache_dir: Path, *, model: str = MODEL, effort: str = "high",
                 refresh: bool = True, verbose: int = 0, auth: str = "auto",
                 backend: str = "auto"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model, self.effort, self.refresh, self.verbose = model, effort, refresh, verbose
        self.auth, self.auth_mode = auth, "none"
        self.backend = backend
        self.cli_model = CLI_MODEL
        # cache_creation/cache_read are billed separately from input_tokens, and
        # with a cached evidence prefix they are most of the spend — counting only
        # input_tokens understates a run by an order of magnitude.
        self.stats = {"calls": 0, "cache_hits": 0, "input_tokens": 0,
                      "cache_creation_tokens": 0, "cache_read_tokens": 0,
                      "output_tokens": 0}
        self._lock = __import__("threading").Lock()
        self._client = None
        if not refresh:
            return
        if self.backend == "auto":
            # The OAuth token is issued to Claude Code, not to the Messages API:
            # used directly it authenticates and is then rate-limited to nothing
            # on every model but Haiku. Driving the `claude` CLI instead is what
            # that credential is for, so prefer it whenever the token exists.
            self.backend = "cli" if (env_value("CLAUDE_CODE_OAUTH_TOKEN")
                                     and shutil.which(CLAUDE_CLI)) else "sdk"
        if self.backend == "cli":
            if not shutil.which(CLAUDE_CLI):
                fail(f"--backend cli, but {CLAUDE_CLI!r} is not on PATH.")
            if not env_value("CLAUDE_CODE_OAUTH_TOKEN"):
                fail("--backend cli, but CLAUDE_CODE_OAUTH_TOKEN is not set.\n"
                     "  Add it to the gitignored .env at the repository root.")
            self.auth_mode = "oauth (claude cli)"
            return
        try:
            import anthropic
        except ImportError:
            fail("the anthropic SDK is not installed.\n" + _SETUP_HELP)
        self._client = self._connect(anthropic)

    def _connect(self, anthropic):
        """Authenticate, preferring the Claude Code OAuth token.

        Two credentials, two headers: an API key goes in `x-api-key` and bills
        the API account, while the Claude Code OAuth token goes in
        `Authorization: Bearer` and draws on the subscription. `auth_mode`
        records which one a run used, because the token counts mean different
        things depending on the answer and nothing else in the output would say.
        """
        oauth = env_value("CLAUDE_CODE_OAUTH_TOKEN")
        api_key = env_value("ANTHROPIC_API_KEY")
        wanted = self.auth
        # Asking for the SDK means asking for the API key. The OAuth token
        # authenticates against the Messages API and is then allotted no
        # capacity on any model but Haiku, so "auto" picking it here would fail
        # every call for a reason that has nothing to do with the request.
        if wanted == "auto" and api_key:
            wanted = "api-key"
        self._fallback_key = api_key if wanted == "auto" else None

        if wanted in ("auto", "oauth") and oauth:
            self.auth_mode = "oauth"
            # Claude Code tokens are issued for a beta OAuth flow; without the
            # header the same token that works in the CLI comes back 401 here.
            return anthropic.Anthropic(
                auth_token=oauth, max_retries=4, timeout=600.0,
                default_headers={"anthropic-beta": OAUTH_BETA})
        if wanted in ("auto", "api-key") and api_key:
            self.auth_mode = "api-key"
            return anthropic.Anthropic(api_key=api_key, max_retries=4, timeout=600.0)

        if wanted == "oauth":
            fail("--auth oauth, but CLAUDE_CODE_OAUTH_TOKEN is not set.\n"
                 "  Add it to the gitignored .env at the repository root, or export it.")
        if wanted == "api-key":
            fail("--auth api-key, but ANTHROPIC_API_KEY is not set.\n"
                 "  Add it to the gitignored .env at the repository root, or export it.")
        fail("no credential found: set CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY\n"
             "  in the gitignored .env at the repository root, or export one.\n"
             "  --no-enrich skips interpretation entirely; --no-refresh rebuilds from\n"
             "  an existing cache without opening a socket.")

    # -- claude CLI backend --------------------------------------------------
    def _cli_call(self, system: str, prompt: str, schema: dict,
                  max_tokens: int) -> dict:
        """One headless `claude -p` run, parsed back into an object.

        The CLI has no `output_config`, so the schema is asked for in words and
        checked here instead of being enforced by the server. That is the whole
        of the difference: everything else — caching, stats, the retry loop in
        the callers — works the same either way.

        Claude Code prepends ~21k tokens of its own system prompt to every call.
        It is cache-read rather than rewritten after the first request, so the
        cost amortises across a run, but it is the reason a single call here is
        never as cheap as a single call through the SDK.
        """
        instruction = (
            f"{system}\n\n"
            "Reply with a single JSON object and nothing else: no prose before or "
            "after it, no markdown code fence, no explanation. It must validate "
            "against this JSON Schema:\n"
            + json.dumps(schema, ensure_ascii=False)
            + "\n\n" + prompt
        )
        cmd = [CLAUDE_CLI, "-p", "--output-format", "json",
               "--max-turns", str(CLI_MAX_TURNS),
               "--model", self.cli_model,
               # `effort` was in the cache key but never in the command, so
               # `--effort low` invalidated every cached call and changed
               # nothing about the one it then made. The CLI takes the same
               # levels the SDK does.
               "--effort", self.effort,
               # `claude -p` runs an agent, and an agent reaches for tools.
               # Denying them by name is not enough — the list has to be
               # exhaustive, and it never is. Whitelisting a tool that does not
               # exist allows nothing at all, whatever is installed. The spare
               # turns are belt and braces: if it still tries, it can recover
               # and answer instead of exiting 1 with `stop_reason: tool_use`
               # and an empty stderr.
               "--allowed-tools", CLI_ALLOW_NOTHING,
               "--system-prompt", "You are a data generator. You emit JSON and "
                                  "nothing else. You never use tools."]
        env = {**os.environ,
               "CLAUDE_CODE_OAUTH_TOKEN": env_value("CLAUDE_CODE_OAUTH_TOKEN") or ""}
        # The CLI fails by exiting non-zero with an empty stderr when the
        # subscription is contended, and a single call can take two minutes, so
        # a transient failure is the normal case rather than the exception.
        # Retry with backoff and, when it finally gives up, quote both streams —
        # "exited 1: " with nothing after it is unactionable.
        last = ""
        for attempt in range(CLI_ATTEMPTS):
            proc = subprocess.run(cmd, input=instruction.encode(),
                                  capture_output=True, env=env, timeout=1800)
            if proc.returncode == 0 and proc.stdout.strip():
                break
            last = (proc.stderr.decode("utf-8", "replace").strip()
                    or proc.stdout.decode("utf-8", "replace").strip()
                    or "(both streams empty)")
            if attempt + 1 < CLI_ATTEMPTS:
                time.sleep(CLI_BACKOFF_S * (attempt + 1))
        else:
            raise RuntimeError(
                f"claude cli exited {proc.returncode} after {CLI_ATTEMPTS} attempts: "
                f"{last[:300]}")
        try:
            envelope = json.loads(proc.stdout.decode("utf-8", "replace"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"claude cli did not return JSON: {exc}") from exc
        if envelope.get("is_error"):
            raise RuntimeError(f"claude cli reported an error: "
                               f"{str(envelope.get('result'))[:300]}")

        usage = envelope.get("usage") or {}
        with self._lock:
            self.stats["input_tokens"] += usage.get("input_tokens", 0)
            self.stats["cache_creation_tokens"] += usage.get(
                "cache_creation_input_tokens", 0)
            self.stats["cache_read_tokens"] += usage.get("cache_read_input_tokens", 0)
            self.stats["output_tokens"] += usage.get("output_tokens", 0)
        return _parse_json_object(envelope.get("result") or "")

    def _send_sdk(self, system: str, prompt: str, schema: dict, max_tokens: int):
        # Server-side refusal fallback is an Opus-only feature. Asking Sonnet for
        # it returns a 400 that reads like a schema problem — "does not support
        # the `fallbacks` parameter" — and sends you looking in the wrong place.
        extra = ({"betas": ["server-side-fallback-2026-07-01"],
                  "fallbacks": "default"}
                 if self.model.startswith("claude-opus") else {})
        # Haiku supports neither adaptive thinking nor an effort level, and
        # asking for either is a 400. Losing the thinking tokens is most of why
        # it is cheap.
        fmt = {"format": {"type": "json_schema", "schema": schema}}
        if not LIGHTWEIGHT_MODEL.search(self.model):
            extra["thinking"] = {"type": "adaptive"}
            fmt["effort"] = self.effort
        with self._client.beta.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            **extra,
            output_config=fmt,
            # The evidence prefix is identical across every call in a stage, so
            # it is worth a cache breakpoint.
            system=[{"type": "text", "text": system,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            return stream.get_final_message()

    def _downgrade_auth(self, exc: Exception) -> bool:
        """Fall back from the OAuth token to the API key, once, and say so.

        The Claude Code token authenticates against the Messages API but is
        allotted no capacity for it: every call comes back 429 while the same
        prompt on an API key succeeds. Rather than fail a 300-call run on its
        first request, switch meters and carry on — but print it, because the
        two credentials bill different accounts and a silent switch is the kind
        of thing someone discovers on an invoice.
        """
        if self.auth != "auto" or self.auth_mode != "oauth" or not self._fallback_key:
            return False
        status = getattr(exc, "status_code", None)
        if status not in (401, 403, 429):
            return False
        import anthropic
        with self._lock:
            if self.auth_mode == "api-key":          # another thread got here first
                return True
            warn(f"the OAuth token returned {status}; falling back to ANTHROPIC_API_KEY "
                 "for the rest of this run (--auth oauth to fail instead)")
            self._client = anthropic.Anthropic(
                api_key=self._fallback_key, max_retries=4, timeout=600.0)
            self.auth_mode = "api-key"
        return True

    def _key(self, system: str, prompt: str, schema: dict) -> str:
        payload = json.dumps(
            {"model": self.model, "effort": self.effort, "system": system,
             "prompt": prompt, "schema": schema},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def complete(self, *, system: str, prompt: str, schema: dict,
                 label: str = "", max_tokens: int = 32000) -> dict:
        """One structured-output call. Returns the parsed object."""
        key = self._key(system, prompt, schema)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                with self._lock:
                    self.stats["cache_hits"] += 1
                return json.loads(path.read_text(encoding="utf-8"))["data"]
            except (json.JSONDecodeError, KeyError):
                path.unlink(missing_ok=True)
        if not self.refresh:
            raise RuntimeError(
                f"--no-refresh, but {label or key[:12]} is not cached. "
                "Run once without it to populate the cache."
            )

        model_label = self.cli_model if self.backend == "cli" else self.model
        if self.verbose:
            info(f"calling {model_label} for {label or key[:12]}...")

        before = dict(self.stats)
        if self.backend == "cli":
            data = self._cli_call(system, prompt, schema, max_tokens)
        else:
            data = self._sdk_json(system, prompt, schema, max_tokens, label)
        missing = [k for k in schema.get("required", []) if k not in data]
        if missing:
            raise RuntimeError(f"{label}: response is missing required key(s) "
                               f"{', '.join(missing)}")

        with self._lock:
            self.stats["calls"] += 1
        used = {k: self.stats[k] - before[k] for k in
                ("input_tokens", "cache_creation_tokens", "cache_read_tokens",
                 "output_tokens")}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "model": model_label, "effort": self.effort, "label": label,
            "backend": self.backend, "auth_mode": self.auth_mode,
            "usage": {"input": used["input_tokens"],
                      "cache_creation": used["cache_creation_tokens"],
                      "cache_read": used["cache_read_tokens"],
                      "output": used["output_tokens"]},
            "data": data,
        }, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        return data

    def _sdk_json(self, system: str, prompt: str, schema: dict, max_tokens: int,
                  label: str) -> dict:
        try:
            message = self._send_sdk(system, prompt, schema, max_tokens)
        except Exception as exc:                       # noqa: BLE001
            if not self._downgrade_auth(exc):
                raise
            message = self._send_sdk(system, prompt, schema, max_tokens)

        if message.stop_reason == "refusal":
            details = getattr(message, "stop_details", None)
            raise Refused(f"{label}: refused ({getattr(details, 'category', 'unknown')})")
        # A cap reached mid-object is unterminated JSON, and `json.loads` reports
        # that as a column number — which sent a 25-minute plant to a traceback
        # that named neither the call nor the cause. The cap is the cause, it is
        # knowable here, and one retry with real headroom fixes the common case
        # (a model that wrote a longer `why` than the caller budgeted for).
        if message.stop_reason == "max_tokens":
            warn(f"{label}: hit the {max_tokens}-token cap mid-answer; "
                 f"retrying once at {max_tokens * 3}")
            message = self._send_sdk(system, prompt, schema, max_tokens * 3)
            if message.stop_reason == "max_tokens":
                raise RuntimeError(
                    f"{label}: the answer does not fit in {max_tokens * 3} "
                    "tokens. Raise max_tokens, or ask for a shorter answer.")
        text = next((b.text for b in message.content if b.type == "text"), None)
        if text is None:
            raise RuntimeError(f"{label}: no text block in the response")
        with self._lock:
            self.stats["input_tokens"] += message.usage.input_tokens
            self.stats["cache_creation_tokens"] += (
                getattr(message.usage, "cache_creation_input_tokens", 0) or 0)
            self.stats["cache_read_tokens"] += (
                getattr(message.usage, "cache_read_input_tokens", 0) or 0)
            self.stats["output_tokens"] += message.usage.output_tokens
        try:
            return json.loads(text)
        except ValueError as exc:
            raise RuntimeError(
                f"{label}: the model did not return usable JSON ({exc}). "
                f"First 200 characters: {text[:200]!r}") from exc

    def cost(self) -> float:
        return (self.stats["input_tokens"] / 1e6 * COST_PER_MTOK_IN
                + self.stats["cache_creation_tokens"] / 1e6 * COST_PER_MTOK_CACHE_WRITE
                + self.stats["cache_read_tokens"] / 1e6 * COST_PER_MTOK_CACHE_READ
                + self.stats["output_tokens"] / 1e6 * COST_PER_MTOK_OUT)


# =============================================================================
# Misc
# =============================================================================
def parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def seconds_between(earlier: str | None, later: str | None) -> int | None:
    a, b = parse_iso(earlier), parse_iso(later)
    if a is None or b is None:
        return None
    return int((b - a).total_seconds())


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return len(text.encode())


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}GB"


def base_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--repo", type=Path, default=DEFAULT_REPO,
                   help=f"repository to mine (default: {DEFAULT_REPO})")
    p.add_argument("--rev", default="HEAD", help="revision to analyse (default: HEAD)")
    p.add_argument("--since", help="only history after this date (git --since syntax)")
    p.add_argument("--until", help="only history before this date (git --until syntax)")
    p.add_argument("-v", "--verbose", action="count", default=0)
    return p
