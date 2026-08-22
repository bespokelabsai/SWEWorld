#!/usr/bin/env python3
"""Read the engineering shape of a repository off the repository itself.

Writes `data_gen/build/engineering_grounding.json`, which answers, for the real
`bespokelabs/curator` clone at `curator/`:

  * which packages and subsystems exist, and what each one is for
  * which interfaces and abstractions the code is extended through
  * how the tests are arranged
  * how it is configured, packaged and released
  * what CI actually does
  * how the modules depend on each other
  * how the documentation is arranged
  * which areas change often
  * who works where, and what that implies about roles and ownership
  * what kinds of engineering work actually happen here

The point is that a company spec supplies business goals and constraints, and
nothing else. The technical shape of the world — its capability areas, its
engineering roles, the work its engineers do — is read from this file rather
than invented alongside the spec, so the world an agent is dropped into matches
the repository it is asked to work in.

Everything here is deterministic: git plus static analysis, no network, no
model. Run it twice on the same revision and you get the same bytes.

    python3 data_gen/analyze_repository.py -v
"""
from __future__ import annotations

import argparse
import ast
import configparser
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install -r data_gen/requirements.txt")

SCHEMA_VERSION = 1
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "engineering_grounding.json"


# =============================================================================
# Context
# =============================================================================
def commits_from_history(doc: dict) -> list[rl.Commit]:
    """The Stage 0 record, reshaped into the commit list this file expects.

    Restricted to the mainline and ordered by the recorded `head_sequence`, so
    it reproduces `git log --reverse HEAD` exactly rather than the all-refs walk
    Stage 0 stores. Merges keep an empty file list, as they do in git.
    """
    by_sha = {c["sha"]: c for c in doc["commits"]}
    out: list[rl.Commit] = []
    for sha in doc["refs"]["head_sequence"]:
        raw = by_sha.get(sha)
        if raw is None:
            continue
        files = [] if raw["is_merge"] else [
            {"path": f["path"], "added": f["lines_added"], "deleted": f["lines_deleted"],
             "binary": f["binary"], "from_path": f["from_path"]}
            for f in raw["files"]
        ]
        out.append(rl.Commit(
            sha=raw["sha"], parents=raw["parents"],
            author_name=raw["author"]["name"], author_email=raw["author"]["email"],
            authored_at=raw["author"]["date"],
            committer_name=raw["committer"]["name"], committer_email=raw["committer"]["email"],
            committed_at=raw["committer"]["date"],
            subject=raw["subject"], body=raw["body"], files=files,
        ))
    return out


class Repo:
    """Everything both the static and the historical passes need, read once."""

    def __init__(self, git: rl.Git, rev: str, since: str | None, until: str | None,
                 history: dict | None = None):
        self.git, self.rev = git, rev
        self.layout = rl.discover_layout(git, rev)
        self.paths = git.lines("ls-tree", "-r", "--name-only", rev)
        self.sizes = {}
        for line in git.lines("ls-tree", "-r", "-l", rev):
            fields = line.split(maxsplit=4)
            if len(fields) == 5 and fields[3].isdigit():
                self.sizes[fields[4]] = int(fields[3])
        text_paths = [p for p in self.paths
                      if rl.language_of(p) not in ("image", "data", "archive", "other")]
        self.blobs = git.read_many(rev, text_paths)
        self.py = {p: s for p, s in self.blobs.items() if p.endswith(".py")}
        self.trees = {}
        for path, source in self.py.items():
            try:
                self.trees[path] = ast.parse(source)
            except (SyntaxError, ValueError):
                continue
        # Stage 0 already walked history; only fall back to walking it again for a
        # windowed or non-HEAD run, which the record does not cover.
        if history and rev == "HEAD" and not since and not until:
            self.commits = commits_from_history(history)
        else:
            self.layout = rl.discover_layout(git, rev)
        self.real = [c for c in self.commits if not c.is_merge]
        self.ids = rl.Identities.from_commits(self.commits)
        self.subs = rl.SubsystemMap(git, rev, self.layout)
        self.classified = {
            c.sha: rl.classify_change(c.paths, c.subject, c.body) for c in self.real
        }
        latest = max((rl.parse_iso(c.authored_at) for c in self.commits
                      if rl.parse_iso(c.authored_at)), default=None)
        self.latest = latest

    def role(self, path: str) -> str:
        return self.layout.role_of(path)

    def loc(self, path: str) -> int:
        source = self.blobs.get(path)
        return source.count("\n") + 1 if source else 0

    def recency_weight(self, iso: str) -> float:
        """1.0 for a change today, decaying with a one-year half-life.

        Raw commit counts say where the code was *built*; curator's history is
        so front-loaded (468 commits in Nov 2024 alone) that without decay the
        hotspots are just wherever the project started.
        """
        when, latest = rl.parse_iso(iso), self.latest
        if when is None or latest is None:
            return 0.0
        age_days = max(0.0, (latest - when).total_seconds() / 86400.0)
        return 0.5 ** (age_days / 365.0)


# =============================================================================
# Source
# =============================================================================
def section_source(repo: Repo) -> dict:
    git = repo.git
    tags = []
    for line in git.lines("for-each-ref", "--sort=creatordate",
                          "--format=%(refname:short)\t%(creatordate:iso-strict)\t%(objectname)",
                          "refs/tags"):
        name, _, rest = line.partition("\t")
        date, _, sha = rest.partition("\t")
        tags.append({"name": name, "date": date, "commit": sha[:12]})
    branches = [b.strip() for b in git.lines("branch", "-r", "--format=%(refname:short)")]
    first = repo.commits[0] if repo.commits else None
    last = repo.commits[-1] if repo.commits else None
    months = Counter(c.authored_at[:7] for c in repo.commits)
    return {
        "path": str(repo.git.repo),
        "remote": git.remote_url(),
        "is_shallow": git.is_shallow(),
        "rev": repo.rev,
        "head_commit": git.head(),
        "head_tree": git.tree_of(repo.rev),
        "commit_count": len(repo.commits),
        "non_merge_commit_count": len(repo.real),
        "merge_commit_count": len(repo.commits) - len(repo.real),
        "first_commit": {"sha": first.sha, "date": first.authored_at} if first else None,
        "last_commit": {"sha": last.sha, "date": last.authored_at} if last else None,
        "commits_by_month": dict(sorted(months.items())),
        "tags": tags,
        "remote_branches": branches,
        "tracked_files": len(repo.paths),
    }


# =============================================================================
# Subsystems
# =============================================================================
def _module_docstring(source: str) -> str | None:
    try:
        doc = ast.get_docstring(ast.parse(source))
    except (SyntaxError, ValueError):
        return None
    return doc.strip().splitlines()[0] if doc else None


def _exports(tree: ast.Module) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            try:
                value = ast.literal_eval(node.value)
                return [str(v) for v in value]
            except (ValueError, SyntaxError):
                return []
    return []


def section_subsystems(repo: Repo) -> list[dict]:
    by_sub: dict[str, list[str]] = defaultdict(list)
    for path in repo.paths:
        by_sub[repo.subs.of(path)].append(path)

    commits_by_sub: dict[str, list[rl.Commit]] = defaultdict(list)
    for commit in repo.real:
        for sub in sorted({repo.subs.of(p) for p in commit.paths}):
            commits_by_sub[sub].append(commit)

    out = []
    for sub, paths in sorted(by_sub.items()):
        py = [p for p in paths if p.endswith(".py")]
        loc = sum(repo.loc(p) for p in paths)
        init = next((p for p in py if p.endswith("__init__.py")), None)
        purpose = None
        if init and repo.blobs.get(init):
            purpose = _module_docstring(repo.blobs[init])
        if not purpose:
            # Fall through the package's modules largest-first, then to the
            # docstring of the first class in the largest one. A package whose
            # biggest file happens to lack a module docstring still has a
            # describable purpose.
            for candidate in sorted(py, key=lambda p: -repo.sizes.get(p, 0)):
                purpose = _module_docstring(repo.blobs.get(candidate, ""))
                if purpose:
                    break
            if not purpose:
                for candidate in sorted(py, key=lambda p: -repo.sizes.get(p, 0)):
                    tree = repo.trees.get(candidate)
                    if not tree:
                        continue
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef) and ast.get_docstring(node):
                            purpose = ast.get_docstring(node).strip().splitlines()[0]
                            break
                    if purpose:
                        break
        exports = _exports(repo.trees[init]) if init and init in repo.trees else []

        subcommits = commits_by_sub.get(sub, [])
        authors = Counter()
        for c in subcommits:
            pid = repo.ids.of(c.author_name, c.author_email)
            if pid:
                authors[pid] += 1
        types = Counter(repo.classified[c.sha]["primary"] for c in subcommits)

        out.append({
            "key": sub,
            "role": repo.role(paths[0]) if paths else "other",
            "purpose": purpose,
            "paths": sorted(paths)[:200],
            "file_count": len(paths),
            "python_file_count": len(py),
            "lines_of_code": loc,
            "modules": sorted(Path(p).stem for p in py if not p.endswith("__init__.py"))[:50],
            "public_exports": exports,
            "commit_count": len(subcommits),
            "recency_weighted_commits": round(
                sum(repo.recency_weight(c.authored_at) for c in subcommits), 2),
            "last_touched": max((c.authored_at for c in subcommits), default=None),
            "top_authors": [{"id": a, "commits": n} for a, n in authors.most_common(5)],
            "work_type_mix": dict(types.most_common()),
        })
    return out


# =============================================================================
# Interfaces and abstractions
# =============================================================================
def _decorator_names(node: ast.AST) -> list[str]:
    names = []
    for dec in getattr(node, "decorator_list", []):
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return names


def section_interfaces(repo: Repo) -> dict:
    classes: dict[str, dict] = {}
    base_index: dict[str, list[str]] = defaultdict(list)
    factories: list[dict] = []

    for path, tree in sorted(repo.trees.items()):
        if not repo.layout.under_source(path):
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if "factory" in node.name.lower():
                    factories.append({"name": node.name, "path": path, "kind": "function"})
                continue
            if not isinstance(node, ast.ClassDef):
                continue

            bases = [ast.unparse(b) for b in node.bases]
            keywords = {kw.arg: ast.unparse(kw.value) for kw in node.keywords if kw.arg}
            abstract, methods = [], []
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(sub.name)
                    if "abstractmethod" in _decorator_names(sub):
                        abstract.append(sub.name)
            doc = ast.get_docstring(node)
            simple_bases = [b.split("[")[0].split(".")[-1] for b in bases]
            info = {
                "name": node.name,
                "path": path,
                "line": node.lineno,
                "subsystem": repo.subs.of(path),
                "bases": bases,
                "metaclass": keywords.get("metaclass"),
                "docstring": doc.strip().splitlines()[0] if doc else None,
                "abstract_methods": abstract,
                "method_count": len(methods),
                "is_abstract": bool(abstract) or "ABC" in simple_bases
                               or keywords.get("metaclass", "").endswith("ABCMeta"),
                "is_protocol": "Protocol" in simple_bases,
                "is_pydantic_model": any(b in ("BaseModel", "BaseSettings") for b in simple_bases),
                "is_enum": any(b.endswith("Enum") for b in simple_bases),
                "subclasses": [],
            }
            classes[f"{path}::{node.name}"] = info
            for base in simple_bases:
                base_index[base].append(f"{path}::{node.name}")
            if node.name.lower().endswith("factory"):
                factories.append({"name": node.name, "path": path, "kind": "class"})

    by_name: dict[str, list[dict]] = defaultdict(list)
    for info in classes.values():
        by_name[info["name"]].append(info)
    for name, children in base_index.items():
        for parent in by_name.get(name, []):
            parent["subclasses"] = sorted(classes[c]["name"] for c in children)

    def importance(info: dict) -> tuple:
        return (info["is_abstract"] or info["is_protocol"],
                len(info["subclasses"]), len(info["abstract_methods"]))

    interesting = [
        info for info in classes.values()
        if info["is_abstract"] or info["is_protocol"] or len(info["subclasses"]) >= 2
    ]
    interesting.sort(key=importance, reverse=True)

    public_api: list[str] = []
    for root in repo.layout.source_roots:
        root_init = f"{root}/__init__.py"
        if root_init in repo.trees:
            public_api += _exports(repo.trees[root_init])

    return {
        "public_api": public_api,
        "extension_points": [
            {k: v for k, v in info.items() if k != "is_enum"} for info in interesting
        ],
        "factories": factories,
        "pydantic_models": sorted(
            {info["name"] for info in classes.values() if info["is_pydantic_model"]}
        ),
        "class_count": len(classes),
        "abstract_class_count": sum(1 for i in classes.values() if i["is_abstract"]),
        "protocol_count": sum(1 for i in classes.values() if i["is_protocol"]),
    }


# =============================================================================
# Test architecture
# =============================================================================
_TEST_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)", re.M)
_MARK_RE = re.compile(r"@pytest\.mark\.(\w+)")


def tests_by_subsystem(repo: Repo) -> dict[str, list[str]]:
    """Which test files import which subsystem.

    Matching test directory names against package names guesses; the import
    graph knows. `tests/integrations/openai/` exercising the batch processors
    is only visible this way.
    """
    modules = {_module_name(p, repo.layout): p for p in repo.trees
               if repo.layout.under_source(p)}
    internal = tuple(repo.layout.import_prefixes) or ("",)
    local = set(repo.layout.local_modules)
    hits: dict[str, set[str]] = defaultdict(set)
    for path, tree in repo.trees.items():
        if repo.role(path) != "tests":
            continue
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]
            for target in targets:
                if not (target.startswith(internal) or target.split(".")[0] in local):
                    continue
                resolved = target
                while resolved and resolved not in modules:
                    resolved = resolved.rsplit(".", 1)[0] if "." in resolved else ""
                if resolved:
                    hits[repo.subs.of(modules[resolved])].add(path)
    return {k: sorted(v) for k, v in hits.items()}


def section_tests(repo: Repo) -> dict:
    declared: list[str] = []
    ini = repo.blobs.get("pytest.ini")
    if ini:
        parser = configparser.ConfigParser(allow_no_value=True)
        try:
            parser.read_string(ini)
            raw = parser.get("pytest", "markers", fallback="")
            declared = [m.split(":")[0].strip() for m in raw.splitlines() if m.strip()]
        except configparser.Error:
            declared = []

    test_paths = [p for p in repo.paths if repo.role(p) == "tests"]
    used = Counter()
    per_dir: dict[str, dict] = defaultdict(lambda: {"files": 0, "tests": 0, "lines": 0})
    total_tests = 0
    for path in test_paths:
        parts = path.split("/")
        group = parts[1] if len(parts) > 2 else "(root)"
        entry = per_dir[group]
        entry["files"] += 1
        source = repo.blobs.get(path)
        if source and path.endswith(".py"):
            found = _TEST_DEF_RE.findall(source)
            entry["tests"] += len(found)
            total_tests += len(found)
            entry["lines"] += source.count("\n") + 1
            used.update(_MARK_RE.findall(source))

    fixtures = []
    for path, tree in sorted(repo.trees.items()):
        if "conftest" not in path:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                    "fixture" in _decorator_names(node):
                doc = ast.get_docstring(node)
                fixtures.append({
                    "name": node.name, "path": path,
                    "docstring": doc.strip().splitlines()[0] if doc else None,
                })

    cassettes = [p for p in repo.paths
                 if "/fixtures/" in p and p.endswith((".yaml", ".yml"))]
    src_loc = sum(repo.loc(p) for p in repo.paths if repo.layout.under_source(p))
    test_loc = sum(repo.loc(p) for p in test_paths if p.endswith(".py"))

    declared_unused = sorted(set(declared) - set(used))
    return {
        "framework": "pytest",
        "config_file": "pytest.ini" if ini else None,
        "declared_markers": declared,
        "used_markers": dict(used.most_common()),
        "declared_but_unused_markers": declared_unused,
        "split_is_by_directory": bool(declared_unused),
        "directories": {k: dict(v) for k, v in sorted(per_dir.items())},
        "test_function_count": total_tests,
        "test_file_count": len([p for p in test_paths if p.endswith(".py")]),
        "conftest_fixtures": fixtures,
        "vcr_cassette_count": len(cassettes),
        "cassette_backends": sorted({
            "/".join(p.split("/fixtures/")[0].split("/")[1:]) for p in cassettes
        }),
        "source_lines": src_loc,
        "test_lines": test_loc,
        "test_to_source_ratio": round(test_loc / src_loc, 3) if src_loc else None,
    }


# =============================================================================
# Configuration, packaging, deployment
# =============================================================================
def _dep_entry(name: str, spec: Any) -> dict:
    if isinstance(spec, dict):
        constraint = spec.get("version", "*")
        optional = bool(spec.get("optional"))
        extras = spec.get("extras", [])
        python = spec.get("python")
    else:
        constraint, optional, extras, python = str(spec), False, [], None
    pinned = bool(re.match(r"^\d+\.\d+", str(constraint)))
    return {"name": name, "constraint": constraint, "pinned": pinned,
            "optional": optional, "extras": extras, "python": python}


def section_configuration(repo: Repo) -> dict:
    pyproject: dict = {}
    raw = repo.blobs.get("pyproject.toml")
    if raw:
        try:
            pyproject = rl.parse_toml(raw)
        except Exception as exc:  # noqa: BLE001 - a broken pyproject is data, not a crash
            rl.warn(f"pyproject.toml did not parse: {exc}")

    poetry = pyproject.get("tool", {}).get("poetry", {})
    deps = {k: v for k, v in poetry.get("dependencies", {}).items() if k != "python"}
    runtime = [_dep_entry(k, v) for k, v in sorted(deps.items())]
    groups = {}
    for group, body in poetry.get("group", {}).items():
        groups[group] = [_dep_entry(k, v) for k, v in sorted(body.get("dependencies", {}).items())]

    targets = []
    makefile = repo.blobs.get("Makefile", "")
    for match in re.finditer(r"^([a-zA-Z][\w-]*):(?:[^=\n]*)$", makefile, re.M):
        body = makefile[match.end():].split("\n\n")[0].strip().splitlines()
        targets.append({"name": match.group(1),
                        "commands": [ln.strip() for ln in body if ln.startswith("\t")][:5]})

    hooks = []
    precommit = repo.blobs.get(".pre-commit-config.yaml")
    if precommit:
        try:
            for entry in (yaml.safe_load(precommit) or {}).get("repos", []):
                for hook in entry.get("hooks", []):
                    hooks.append({"repo": entry.get("repo"), "rev": entry.get("rev"),
                                  "id": hook.get("id"), "args": hook.get("args", [])})
        except yaml.YAMLError:
            pass

    tool = pyproject.get("tool", {})
    return {
        "build_backend": "poetry" if poetry else pyproject.get("build-system", {}).get("build-backend"),
        "package_name": poetry.get("name"),
        "version": poetry.get("version"),
        "python_requires": poetry.get("dependencies", {}).get("python"),
        "packages": poetry.get("packages", []),
        "entry_points": poetry.get("scripts", {}),
        "runtime_dependencies": runtime,
        "pinned_dependencies": [d["name"] for d in runtime if d["pinned"]],
        "optional_dependencies": [d["name"] for d in runtime if d["optional"]],
        "extras": poetry.get("extras", {}),
        "dependency_groups": groups,
        "lockfile": "poetry.lock" in repo.paths,
        "makefile_targets": targets,
        "publish_script": "publish_pkg.sh" in repo.paths,
        "pre_commit_hooks": hooks,
        "linters": {
            "ruff": tool.get("ruff", {}),
            "isort": tool.get("isort", {}),
        },
        "coverage": tool.get("coverage", {}),
        "containerised": any(p.endswith("Dockerfile") or p == "Dockerfile" for p in repo.paths),
    }


# =============================================================================
# CI / CD
# =============================================================================
def section_ci(repo: Repo) -> dict:
    workflows = []
    workflow_dirs = [c for c in repo.layout.ci_paths if not c.endswith((".yml", ".yaml"))]
    for path in sorted(repo.paths):
        in_dir = any(path.startswith(d + "/") for d in workflow_dirs)
        standalone = path in repo.layout.ci_paths
        if not (in_dir or standalone) or not path.endswith((".yml", ".yaml")):
            continue
        try:
            doc = yaml.safe_load(repo.blobs.get(path, "")) or {}
        except yaml.YAMLError as exc:
            rl.warn(f"{path} did not parse: {exc}")
            continue
        # PyYAML resolves the bare key `on:` to the boolean True (YAML 1.1).
        triggers = doc.get("on", doc.get(True, {}))
        jobs = {}
        for job_id, job in (doc.get("jobs") or {}).items():
            steps = []
            for step in job.get("steps", []) or []:
                run = (step.get("run") or "").strip()
                steps.append({
                    "name": step.get("name"),
                    "uses": step.get("uses"),
                    "run": run.splitlines()[0][:160] if run else None,
                })
            jobs[job_id] = {
                "runs_on": job.get("runs-on"),
                "strategy": job.get("strategy"),
                "step_count": len(steps),
                "steps": steps,
            }
        body = repo.blobs.get(path, "")
        cov = re.search(r"--cov-fail-under=(\d+)", body)
        workflows.append({
            "path": path,
            "name": doc.get("name"),
            "triggers": triggers,
            "jobs": jobs,
            "gates": {
                "coverage_threshold": int(cov.group(1)) if cov else None,
                "lint": bool(re.search(r"ruff\s+(check|format)", body)),
                "tests": "pytest" in body,
            },
        })

    publishes = any("publish" in (w.get("name") or "").lower() or
                    any("poetry publish" in (s.get("run") or "")
                        for j in w["jobs"].values() for s in j["steps"])
                    for w in workflows)
    return {
        "provider": "github-actions" if workflows else None,
        "workflow_count": len(workflows),
        "workflows": workflows,
        "publishes_from_ci": publishes,
        "release_is_manual": not publishes and "publish_pkg.sh" in repo.paths,
    }


# =============================================================================
# Dependency structure
# =============================================================================
def _module_name(path: str, layout: rl.Layout) -> str:
    """Dotted module name, relative to whichever source root contains it."""
    rel = path
    for base in layout.module_bases:
        if path.startswith(base + "/"):
            rel = path[len(base) + 1:]
            break
    rel = rel[:-3] if rel.endswith(".py") else rel
    if rel.endswith("/__init__"):
        rel = rel[: -len("/__init__")]
    return rel.replace("/", ".")


def section_dependencies(repo: Repo, top_n: int) -> dict:
    modules = {_module_name(p, repo.layout): p for p in repo.trees
               if repo.layout.under_source(p)}
    internal = tuple(repo.layout.import_prefixes) or ("",)
    local = set(repo.layout.local_modules)
    edges: Counter[tuple[str, str]] = Counter()
    external: Counter[str] = Counter()
    stdlib = getattr(sys, "stdlib_module_names", set())

    for path, tree in sorted(repo.trees.items()):
        if not repo.layout.under_source(path):
            continue
        source_module = _module_name(path, repo.layout)
        package = source_module.rsplit(".", 1)[0]
        # ast.walk, not tree.body: _factory.py imports its processors inside
        # functions to break an import cycle, and those are exactly the edges
        # that describe how the factory is wired.
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package.rsplit(".", node.level - 1)[0] if node.level > 1 else package
                    targets = [f"{base}.{node.module}" if node.module else base]
                elif node.module:
                    targets = [node.module]
            for target in targets:
                if target.startswith(internal) or target.split(".")[0] in local:
                    resolved = target
                    while resolved and resolved not in modules:
                        resolved = resolved.rsplit(".", 1)[0] if "." in resolved else ""
                    if resolved and resolved != source_module:
                        edges[(source_module, resolved)] += 1
                else:
                    root = target.split(".")[0]
                    if root and root not in stdlib and root not in local:
                        external[root] += 1

    fan_out, fan_in = Counter(), Counter()
    adjacency: dict[str, set[str]] = defaultdict(set)
    for (src, dst) in edges:
        fan_out[src] += 1
        fan_in[dst] += 1
        adjacency[src].add(dst)

    sub_edges: Counter[tuple[str, str]] = Counter()
    for (src, dst), weight in edges.items():
        a, b = repo.subs.of(modules[src]), repo.subs.of(modules[dst])
        if a != b:
            sub_edges[(a, b)] += weight

    return {
        "internal": {
            "module_count": len(modules),
            "edge_count": len(edges),
            "most_depended_on": [{"module": m, "importers": n}
                                 for m, n in fan_in.most_common(top_n)],
            "most_dependent": [{"module": m, "imports": n}
                               for m, n in fan_out.most_common(top_n)],
            "cycles": _find_cycles(adjacency),
            "subsystem_edges": [{"from": a, "to": b, "imports": n}
                                for (a, b), n in sub_edges.most_common(top_n)],
        },
        "external": {
            "declared": None,   # filled in by main() from the configuration section
            "imported": [{"package": p, "import_sites": n} for p, n in external.most_common()],
        },
    }


def _find_cycles(adjacency: dict[str, set[str]]) -> list[list[str]]:
    """Strongly connected components larger than one node (Tarjan, iterative).

    Neighbours are walked in sorted order: set iteration order varies with the
    interpreter's hash seed, and the output has to be byte-stable across runs.
    """
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for root in list(adjacency):
        if root in index:
            continue
        work = [(root, iter(sorted(adjacency.get(root, ()))))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(adjacency.get(child, ())))))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    result.append(sorted(component))
    return sorted(result)


# =============================================================================
# Documentation
# =============================================================================
def section_documentation(repo: Repo) -> dict:
    readme = repo.blobs.get("README.md", "")
    sections = [{"level": len(m.group(1)), "title": m.group(2).strip()}
                for m in re.finditer(r"^(#{1,3})\s+(.+)$", readme, re.M)]
    docs = [{"path": p, "bytes": repo.sizes.get(p, 0), "language": rl.language_of(p)}
            for p in sorted(repo.paths) if p.startswith("docs/")]

    contributing = repo.blobs.get("docs/CONTRIBUTING.md", "") or repo.blobs.get("CONTRIBUTING.md", "")
    conventions = {
        "issue_before_work": bool(re.search(r"create an issue", contributing, re.I)),
        "conventional_commits": bool(re.search(r"conventional commit|feat:|fix:", contributing, re.I)),
        "reference_issues_in_pr": bool(re.search(r"clos(e|es|ing) #", contributing, re.I)),
        "source": "docs/CONTRIBUTING.md" if contributing else None,
    }

    conventional = sum(
        1 for c in repo.real
        if re.match(r"^\s*(feat|fix|chore|docs|test|refactor|ci|build|perf|style|revert)"
                    r"(\([^)]*\))?!?\s*:", c.subject, re.I)
    )
    linked = sum(1 for c in repo.real
                 if re.search(r"\b(clos(e|es|ed)|fix(es|ed)?|resolv(e|es|ed))\s+#\d+",
                              c.body, re.I))
    return {
        "readme": {"path": "README.md", "bytes": repo.sizes.get("README.md", 0),
                   "sections": sections},
        "files": docs,
        "has_site_generator": any(p in repo.paths for p in
                                  ("mkdocs.yml", "docs/conf.py", "docusaurus.config.js")),
        "stated_conventions": conventions,
        "observed_adherence": {
            "commits_with_conventional_subject": conventional,
            "commits_linking_an_issue": linked,
            "non_merge_commits": len(repo.real),
            "conventional_subject_rate": round(conventional / len(repo.real), 3) if repo.real else None,
        },
    }


# =============================================================================
# Change hotspots
# =============================================================================
def section_hotspots(repo: Repo, top_n: int) -> dict:
    file_commits: Counter[str] = Counter()
    file_weighted: Counter[str] = Counter()
    file_added: Counter[str] = Counter()
    file_deleted: Counter[str] = Counter()
    file_authors: dict[str, set[str]] = defaultdict(set)
    sub_commits: Counter[str] = Counter()
    sub_weighted: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()

    for commit in repo.real:
        weight = repo.recency_weight(commit.authored_at)
        pid = repo.ids.of(commit.author_name, commit.author_email)
        for entry in commit.files:
            path = entry["path"]
            file_commits[path] += 1
            file_weighted[path] += weight
            file_added[path] += entry["added"]
            file_deleted[path] += entry["deleted"]
            if pid:
                file_authors[path].add(pid)
        for sub in sorted({repo.subs.of(p) for p in commit.paths}):
            sub_commits[sub] += 1
            sub_weighted[sub] += weight
        # Wide commits (a formatter run, a mass rename) couple everything to
        # everything; they say nothing about which files really change together.
        if 2 <= len(commit.files) <= 15:
            ordered = sorted(commit.paths)
            for i, a in enumerate(ordered):
                for b in ordered[i + 1:]:
                    pairs[(a, b)] += 1

    live = lambda p: p in repo.sizes  # noqa: E731 - deleted paths are history, not hotspots
    coupling = [
        {"a": a, "b": b, "co_changes": n,
         "confidence": round(n / max(file_commits[a], file_commits[b]), 3)}
        for (a, b), n in pairs.most_common(top_n * 4)
        if n >= 5 and live(a) and live(b)
    ][:top_n]

    per_year: dict[str, dict[str, int]] = defaultdict(Counter)
    for commit in repo.real:
        year = commit.authored_at[:4]
        for sub in sorted({repo.subs.of(p) for p in commit.paths}):
            per_year[year][sub] += 1

    return {
        "note": "recency_weighted uses a one-year half-life against the newest commit",
        "top_files": [
            {"path": p, "commits": n,
             "recency_weighted": round(file_weighted[p], 2),
             "lines_added": file_added[p], "lines_deleted": file_deleted[p],
             "distinct_authors": len(file_authors[p]),
             "still_present": live(p)}
            for p, n in file_commits.most_common(top_n)
        ],
        "top_files_recent": [
            {"path": p, "recency_weighted": round(w, 2), "commits": file_commits[p]}
            for p, w in file_weighted.most_common(top_n) if live(p)
        ],
        "by_subsystem": [
            {"subsystem": s, "commits": n, "recency_weighted": round(sub_weighted[s], 2)}
            for s, n in sub_commits.most_common()
        ],
        "by_subsystem_per_year": {y: dict(Counter(v).most_common(10))
                                  for y, v in sorted(per_year.items())},
        "co_change_coupling": coupling,
    }


# =============================================================================
# Contributors, ownership, roles
# =============================================================================
SUBSYSTEM_LABELS = {
    "core": "core runtime",
    "other": "unmapped paths (pre-src layout and loose tooling)",
    "ci": "CI configuration",
    "docs": "documentation",
    "packaging": "packaging and release",
    "examples": "examples",
    "tests": "tests",
}


def _label(subsystem: str) -> str:
    if subsystem in SUBSYSTEM_LABELS:
        return SUBSYSTEM_LABELS[subsystem]
    return subsystem.replace("_", " ").replace("/", " / ")


def _archetype(role_mix: Counter) -> str:
    """Where in the repository someone works, from what they actually touch."""
    total = sum(role_mix.values()) or 1
    shares = {role: n / total for role, n in role_mix.items()}
    if shares.get("tests", 0) > 0.45:
        return "test engineering"
    if shares.get("docs", 0) > 0.45:
        return "documentation"
    if shares.get("ci", 0) + shares.get("packaging", 0) > 0.35:
        return "build, CI and release"
    if shares.get("examples", 0) > 0.45:
        return "examples and developer experience"
    if shares.get("src", 0) > 0.5:
        return "core engineering"
    if shares.get("src", 0) > 0.25:
        return "core engineering with broad support work"
    return "across the repository"


def _primary_work(type_mix: Counter) -> dict:
    """What kind of work someone does, ignoring what could not be classified."""
    known = Counter({k: v for k, v in type_mix.items() if k != "unclassified"})
    if not known:
        return {"type": None, "share": None}
    kind, n = known.most_common(1)[0]
    return {"type": kind, "share": round(n / sum(known.values()), 3)}


def section_contributors(repo: Repo, top_n: int) -> tuple[list[dict], list[dict], dict]:
    per_person_files: dict[str, Counter] = defaultdict(Counter)
    per_person_subs: dict[str, Counter] = defaultdict(Counter)
    per_person_types: dict[str, Counter] = defaultdict(Counter)
    per_person_dates: dict[str, list[str]] = defaultdict(list)
    per_person_size: dict[str, list[int]] = defaultdict(list)
    sub_owner: dict[str, Counter] = defaultdict(Counter)

    for commit in repo.real:
        pid = repo.ids.of(commit.author_name, commit.author_email)
        if not pid:
            continue
        per_person_dates[pid].append(commit.authored_at)
        per_person_size[pid].append(len(commit.files))
        per_person_types[pid][repo.classified[commit.sha]["primary"]] += 1
        for path in commit.paths:
            per_person_files[pid][rl.file_role(path)] += 1
        for sub in sorted({repo.subs.of(p) for p in commit.paths}):
            per_person_subs[pid][sub] += 1
            sub_owner[sub][pid] += 1

    contributors = []
    for person in sorted(repo.ids.people.values(), key=lambda p: -p.commits):
        if not person.commits:
            continue
        dates = sorted(per_person_dates.get(person.id, []))
        contributors.append({
            "id": person.id,
            "display_name": person.display_name,
            "emails": person.emails,
            "aliases": person.names,
            "github_login": person.github_login,
            "is_bot": person.is_bot,
            "commits": person.commits,
            "first_commit": dates[0] if dates else None,
            "last_commit": dates[-1] if dates else None,
            "active_months": len({d[:7] for d in dates}),
            "median_files_per_commit": _median(per_person_size.get(person.id, [])),
            "subsystems": dict(per_person_subs[person.id].most_common(8)),
            "file_roles": dict(per_person_files[person.id].most_common()),
            "work_types": dict(per_person_types[person.id].most_common()),
        })

    roles = []
    for entry in contributors:
        if entry["commits"] < 5:
            continue
        subs = Counter(entry["subsystems"])
        total = sum(subs.values()) or 1
        owned = []
        for sub, n in subs.most_common(6):
            share_of_person = n / total
            share_of_sub = n / max(1, sum(sub_owner[sub].values()))
            if share_of_person >= 0.10 and share_of_sub >= 0.15:
                owned.append({"subsystem": sub, "label": _label(sub),
                              "share_of_their_work": round(share_of_person, 3),
                              "share_of_subsystem": round(share_of_sub, 3)})
        breadth = sum(1 for _, n in subs.items() if n / total >= 0.05)
        concentration = sum((n / total) ** 2 for n in subs.values())
        roles.append({
            "person": entry["id"],
            "is_bot": entry["is_bot"],
            "archetype": _archetype(Counter(entry["file_roles"])),
            "primary_work": _primary_work(Counter(entry["work_types"])),
            "owns": owned,
            "focus": "specialist" if concentration >= 0.30 else
                     "generalist" if breadth >= 5 else "mixed",
            "breadth_subsystems": breadth,
            "concentration_hhi": round(concentration, 3),
            "commits": entry["commits"],
            "active": {"from": entry["first_commit"], "to": entry["last_commit"],
                       "months": entry["active_months"]},
            "dominant_work_types": list(Counter(entry["work_types"]).most_common(3)),
        })

    ownership = {}
    for sub, owners in sorted(sub_owner.items()):
        total = sum(owners.values())
        ranked = owners.most_common()
        cumulative, bus_factor = 0, 0
        for _, n in ranked:
            cumulative += n
            bus_factor += 1
            if cumulative >= total / 2:
                break
        ownership[sub] = {
            "commits": total,
            "contributors": len(ranked),
            "bus_factor": bus_factor,
            "top_owners": [{"id": pid, "commits": n, "share": round(n / total, 3)}
                           for pid, n in ranked[:5]],
        }
    return contributors, roles, ownership


def _median(values: Iterable[float]) -> float | None:
    values = sorted(values)
    if not values:
        return None
    mid = len(values) // 2
    if len(values) % 2:
        return float(values[mid])
    return round((values[mid - 1] + values[mid]) / 2, 2)


# =============================================================================
# Types of work
# =============================================================================
def section_work_types(repo: Repo) -> dict:
    counts: Counter[str] = Counter()
    files_per: dict[str, list[int]] = defaultdict(list)
    added_per: dict[str, list[int]] = defaultdict(list)
    deleted_per: dict[str, list[int]] = defaultdict(list)
    per_year: dict[str, Counter] = defaultdict(Counter)
    per_sub: dict[str, Counter] = defaultdict(Counter)
    confidence: dict[str, list[float]] = defaultdict(list)

    for commit in repo.real:
        result = repo.classified[commit.sha]
        kind = result["primary"]
        counts[kind] += 1
        confidence[kind].append(result["confidence"])
        files_per[kind].append(len(commit.files))
        added_per[kind].append(commit.lines_added)
        deleted_per[kind].append(commit.lines_deleted)
        per_year[commit.authored_at[:4]][kind] += 1
        for sub in sorted({repo.subs.of(p) for p in commit.paths}):
            per_sub[sub][kind] += 1

    total = sum(counts.values()) or 1
    return {
        "classifier": "deterministic rules over conventional-commit prefix, branch name, "
                      "changed paths and message keywords; see repolib.classify_change",
        "distribution": [
            {"type": kind, "commits": n, "share": round(n / total, 3),
             "median_files": _median(files_per[kind]),
             "median_lines_added": _median(added_per[kind]),
             "median_lines_deleted": _median(deleted_per[kind]),
             "mean_confidence": round(sum(confidence[kind]) / len(confidence[kind]), 3)}
            for kind, n in counts.most_common()
        ],
        "per_year": {y: dict(v.most_common()) for y, v in sorted(per_year.items())},
        "per_subsystem": {s: dict(v.most_common(6)) for s, v in sorted(per_sub.items())},
        "unclassified_share": round(counts["unclassified"] / total, 3),
    }


# =============================================================================
# Capability areas — the join
# =============================================================================
def section_capability_areas(repo: Repo, subsystems: list[dict], interfaces: dict,
                             ownership: dict, tests: dict,
                             test_map: dict[str, list[str]]) -> list[dict]:
    """One entry per part of the product a company spec can attach goals to.

    This is the object that replaces an invented org chart: each area names real
    packages, real extension points, real owners and the real mix of work that
    lands there.
    """
    ext_by_sub: dict[str, list[dict]] = defaultdict(list)
    for point in interfaces["extension_points"]:
        ext_by_sub[point["subsystem"]].append(point)

    areas = []
    for sub in subsystems:
        if sub["role"] not in ("src",) and sub["key"] not in ("core",):
            continue
        if sub["file_count"] == 0:
            continue
        points = sorted(ext_by_sub.get(sub["key"], []),
                        key=lambda p: (-len(p["subclasses"]), -len(p["abstract_methods"])))
        owners = ownership.get(sub["key"], {})
        areas.append({
            "key": sub["key"],
            "name": _label(sub["key"]),
            "purpose": sub["purpose"],
            "paths": sub["paths"][:20],
            "lines_of_code": sub["lines_of_code"],
            "public_exports": sub["public_exports"],
            "extension_points": [
                {"name": p["name"], "path": p["path"], "kind":
                 "protocol" if p["is_protocol"] else "abstract base" if p["is_abstract"] else "base",
                 "abstract_methods": p["abstract_methods"], "subclasses": p["subclasses"]}
                for p in points[:8]
            ],
            "change_volume": {
                "commits": sub["commit_count"],
                "recency_weighted": sub["recency_weighted_commits"],
                "last_touched": sub["last_touched"],
            },
            "work_type_mix": sub["work_type_mix"],
            "owners": owners.get("top_owners", []),
            "bus_factor": owners.get("bus_factor"),
            "tests": {
                "files_importing_it": test_map.get(sub["key"], [])[:20],
                "file_count": len(test_map.get(sub["key"], [])),
                "directly_tested": bool(test_map.get(sub["key"])),
            },
        })
    areas.sort(key=lambda a: -a["change_volume"]["recency_weighted"])
    return areas


# =============================================================================
# Organization: evidence
# =============================================================================
# Everything below turns the measured sections above, plus the episode file,
# into an evidence pack — and then asks Claude to read the organization off it.
# The split matters: the pack is computed, the reading is interpreted, and the
# output keeps them in separate fields so nothing interpreted can be mistaken
# for something measured.
ORG_SCHEMA_VERSION = 1
SUBJECT_SAMPLE = 30
TITLE_SAMPLE = 8


def _quarter(month: str) -> str:
    year, mm = month.split("-")
    return f"{year}-Q{(int(mm) - 1) // 3 + 1}"


def _months_between(first: str, last: str) -> list[str]:
    out, (year, month) = [], (int(first[:4]), int(first[5:7]))
    end = (int(last[:4]), int(last[5:7]))
    while (year, month) <= end:
        out.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def _sample(items: list, k: int) -> list:
    """Evenly spaced sample, so a tenure is covered end to end rather than head-first."""
    if len(items) <= k:
        return list(items)
    step = len(items) / k
    return [items[int(i * step)] for i in range(k)]


def org_evidence(grounding: dict, episodes_doc: dict) -> dict:
    """Everything Claude is shown. Pure computation over data already produced."""
    episodes = sorted(episodes_doc["episodes"],
                      key=lambda e: e["timeline"]["merged_at"]
                      or e["timeline"]["first_commit_at"] or "")

    def when(ep: dict) -> str:
        return (ep["timeline"]["merged_at"] or ep["timeline"]["first_commit_at"] or "")[:7]

    months = [m for m in (when(e) for e in episodes) if m]
    span = _months_between(min(months), max(months)) if months else []

    per_month: dict[str, dict] = {
        m: {"month": m, "episodes": 0, "commits": 0, "lines_added": 0, "lines_deleted": 0,
            "work_types": Counter(), "merge_styles": Counter(), "reviewed": 0,
            "review_cycles": 0, "with_pr": 0, "cycle_times": [], "people": set()}
        for m in span
    }
    first_seen: dict[str, str] = {}
    last_seen: dict[str, str] = {}
    package_first: dict[str, dict] = {}
    review_edges: Counter[tuple[str, str]] = Counter()
    per_quarter_titles: dict[str, list[str]] = defaultdict(list)
    per_subsystem_titles: dict[str, list[str]] = defaultdict(list)

    people_raw: dict[str, dict] = defaultdict(lambda: {
        "episodes": 0, "with_pr": 0, "commits": 0, "subjects": [], "titles": [],
        "monthly": Counter(), "subsystems": Counter(), "half_years": defaultdict(Counter),
        "reviews_given": Counter(), "review_states_given": Counter(),
        "reviewed_by": Counter(), "sizes": [],
    })

    for ep in episodes:
        month = when(ep)
        if not month:
            continue
        bucket = per_month[month]
        metrics, prov = ep["metrics"], ep["provenance"]
        bucket["episodes"] += 1
        bucket["commits"] += metrics["commits_first_seen_here"]
        bucket["lines_added"] += metrics["lines_added"]
        bucket["lines_deleted"] += metrics["lines_deleted"]
        bucket["work_types"][ep["change_type"]["primary"]] += 1
        bucket["merge_styles"][prov["merge_style"]] += 1
        if prov["pull_request"]:
            bucket["with_pr"] += 1
        if metrics["approvals"] or metrics["changes_requested"] or metrics["comment_reviews"]:
            bucket["reviewed"] += 1
        bucket["review_cycles"] += metrics["review_cycles"]
        if metrics["time_pr_open_to_merge_s"] is not None:
            bucket["cycle_times"].append(metrics["time_pr_open_to_merge_s"])

        if len(per_quarter_titles[_quarter(month)]) < TITLE_SAMPLE * 2:
            per_quarter_titles[_quarter(month)].append(ep["title"][:110])
        for subsystem in metrics["file_distribution"]["by_subsystem"]:
            package_first.setdefault(subsystem, {"month": month, "episode_id": ep["id"]})
            if len(per_subsystem_titles[subsystem]) < TITLE_SAMPLE:
                per_subsystem_titles[subsystem].append(ep["title"][:110])

        author = ep["people"]["author"]
        for commit in prov["source_commits"]:
            person = commit["author"]
            if not person or not commit["first_in_episode"]:
                continue
            bucket["people"].add(person)
            entry = people_raw[person]
            entry["commits"] += 1
            entry["monthly"][commit["authored_at"][:7]] += 1
            entry["subjects"].append({"at": commit["authored_at"][:10],
                                      "subject": commit["subject"][:120]})
            half = f"{commit['authored_at'][:4]}-H{1 if int(commit['authored_at'][5:7]) <= 6 else 2}"
            for subsystem in metrics["file_distribution"]["by_subsystem"]:
                entry["half_years"][half][subsystem] += 1
            first_seen.setdefault(person, commit["authored_at"][:10])
            last_seen[person] = commit["authored_at"][:10]

        if author:
            entry = people_raw[author]
            entry["episodes"] += 1
            entry["sizes"].append(metrics["files_changed"])
            entry["subsystems"].update(metrics["file_distribution"]["by_subsystem"])
            if prov["pull_request"]:
                entry["with_pr"] += 1
            if len(entry["titles"]) < TITLE_SAMPLE * 3:
                entry["titles"].append({"at": month, "title": ep["title"][:110],
                                        "type": ep["change_type"]["primary"],
                                        "episode_id": ep["id"]})
        for reviewer in ep["people"]["reviewers"]:
            login = reviewer["login"]
            review_edges[(login, author or "unknown")] += 1
            people_raw[login]["reviews_given"][author or "unknown"] += 1
            for state in reviewer["states"]:
                people_raw[login]["review_states_given"][state] += 1
            if author:
                people_raw[author]["reviewed_by"][login] += 1

    monthly = []
    for month in span:
        b = per_month[month]
        cycles = sorted(b["cycle_times"])
        monthly.append({
            "month": month, "episodes": b["episodes"], "commits": b["commits"],
            "lines_added": b["lines_added"], "lines_deleted": b["lines_deleted"],
            "active_people": sorted(b["people"]),
            "work_types": dict(b["work_types"].most_common()),
            "merge_styles": dict(b["merge_styles"].most_common()),
            "episodes_with_pr": b["with_pr"], "episodes_reviewed": b["reviewed"],
            "review_cycles": b["review_cycles"],
            "median_pr_to_merge_h": round(cycles[len(cycles) // 2] / 3600, 1) if cycles else None,
        })

    joins: dict[str, list[str]] = defaultdict(list)
    leaves: dict[str, list[str]] = defaultdict(list)
    for person, date in first_seen.items():
        joins[date[:7]].append(person)
    for person, date in last_seen.items():
        leaves[date[:7]].append(person)
    for row in monthly:
        row["first_commits_by"] = sorted(joins.get(row["month"], []))
        row["last_commits_by"] = sorted(leaves.get(row["month"], []))

    quarters: dict[str, dict] = {}
    for row in monthly:
        q = quarters.setdefault(_quarter(row["month"]), {
            "quarter": _quarter(row["month"]), "episodes": 0, "with_pr": 0,
            "reviewed": 0, "merge_styles": Counter(), "cycle": []})
        q["episodes"] += row["episodes"]
        q["with_pr"] += row["episodes_with_pr"]
        q["reviewed"] += row["episodes_reviewed"]
        q["merge_styles"].update(row["merge_styles"])
        if row["median_pr_to_merge_h"] is not None:
            q["cycle"].append(row["median_pr_to_merge_h"])
    drift = []
    for q in quarters.values():
        total = q["episodes"] or 1
        drift.append({
            "quarter": q["quarter"], "episodes": q["episodes"],
            "pr_share": round(q["with_pr"] / total, 3),
            "reviewed_share": round(q["reviewed"] / total, 3),
            "merge_styles": dict(q["merge_styles"].most_common()),
            "median_pr_to_merge_h": round(sum(q["cycle"]) / len(q["cycle"]), 1) if q["cycle"] else None,
            "sample_episode_titles": per_quarter_titles.get(q["quarter"], [])[:TITLE_SAMPLE],
        })

    by_id = {c["id"]: c for c in grounding["contributors"]}
    roles_by_id = {r["person"]: r for r in grounding["roles"]}
    people = {}
    for person, raw in people_raw.items():
        contributor = by_id.get(person)
        if not contributor:
            continue          # a GitHub reviewer login with no commits of their own
        subjects = sorted(raw["subjects"], key=lambda s: s["at"])
        people[person] = {
            "id": person,
            "display_name": contributor["display_name"],
            "github_login": contributor["github_login"],
            "aliases": contributor["aliases"],
            "is_bot": contributor["is_bot"],
            "commits": contributor["commits"],
            "episodes_authored": raw["episodes"],
            "first_commit": contributor["first_commit"],
            "last_commit": contributor["last_commit"],
            "active_months": contributor["active_months"],
            "monthly_commits": dict(sorted(raw["monthly"].items())),
            "subsystems": dict(raw["subsystems"].most_common(10)),
            "focus_by_half_year": {half: dict(c.most_common(5))
                                   for half, c in sorted(raw["half_years"].items())},
            "work_types": contributor["work_types"],
            "file_roles": contributor["file_roles"],
            "median_files_per_episode": _median(raw["sizes"]),
            "episodes_via_pr": raw["with_pr"],
            "pr_share": round(raw["with_pr"] / raw["episodes"], 3) if raw["episodes"] else None,
            "reviews_given": dict(raw["reviews_given"].most_common(8)),
            "review_states_given": dict(raw["review_states_given"]),
            "reviewed_by": dict(raw["reviewed_by"].most_common(8)),
            "measured_role": roles_by_id.get(person),
            "sample_commit_subjects": _sample(subjects, SUBJECT_SAMPLE),
            "sample_episode_titles": _sample(raw["titles"], TITLE_SAMPLE * 2),
        }

    return {
        "monthly": monthly,
        "quarterly_process_drift": drift,
        "package_first_seen": dict(sorted(package_first.items(), key=lambda kv: kv[1]["month"])),
        "releases": grounding["source"]["tags"],
        "readme_sections": [s["title"] for s in grounding["documentation"]["readme"]["sections"]],
        "review_graph": [{"reviewer": a, "author": b, "reviews": n}
                         for (a, b), n in review_edges.most_common(40)],
        "subsystem_episode_titles": dict(per_subsystem_titles),
        "people": people,
        "totals": {
            "episodes": len(episodes),
            "commits": grounding["source"]["non_merge_commit_count"],
            "span": {"from": grounding["source"]["first_commit"]["date"][:10],
                     "to": grounding["source"]["last_commit"]["date"][:10]},
        },
    }


# =============================================================================
# Organization: schemas
# =============================================================================
def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props,
            "required": required if required is not None else list(props),
            "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": {"type": "string"}}
_CONF = {"type": "number", "description": "0-1, how well the evidence supports this"}
_EVIDENCE = {"type": "array", "items": {"type": "string"},
             "description": "Concrete citations: episode ids (ep-xxxxxxxxxxxx), months, "
                            "repo paths, contributor ids, release tags."}

ERAS_SCHEMA = _obj({"eras": {"type": "array", "items": _obj({
    "name": _STR, "slug": _STR, "start_month": _STR, "end_month": _STR,
    "summary": _STR,
    "what_the_team_was_doing": _STR,
    "how_they_worked": {**_STR, "description": "process in this era: branching, review, merges"},
    "what_changed_entering_it": _STR,
    "dominant_work_types": _STRS,
    "key_people": _STRS,
    "key_episode_ids": _STRS,
    "evidence": _EVIDENCE,
    "confidence": _CONF,
    "inferred": _obj({"reading": _STR, "why_it_shifted": _STR, "confidence": _CONF}),
})}})

AREAS_SCHEMA = _obj({"capability_areas": {"type": "array", "items": _obj({
    "name": {**_STR, "description": "What an engineer would call it in conversation"},
    "slug": _STR,
    "description": _STR,
    "what_it_does_for_users": _STR,
    "packages": _STRS, "paths": _STRS, "interfaces": _STRS,
    "introduced_month": _STR,
    "introduced_episode_id": _STR,
    "maturity": {"type": "string", "enum": ["foundational", "established", "growing",
                                            "experimental", "dormant"]},
    "activity": {"type": "string", "enum": ["hot", "steady", "occasional", "quiet"]},
    "owners": _STRS,
    "representative_episode_ids": _STRS,
    "typical_work": {**_STR, "description": "What a task in this area actually looks like"},
    "evidence": _EVIDENCE,
    "confidence": _CONF,
    "inferred": _obj({"reading": _STR, "confidence": _CONF}),
})}})

PERSON_SCHEMA = _obj({
    "headline": {**_STR, "description": "One line: who this person is on this project"},
    "summary": _STR,
    "status": {"type": "string", "enum": ["active", "tapered-off", "departed", "drive-by"]},
    "arc": {"type": "array", "items": _obj({
        "era_slug": _STR, "what_they_did": _STR, "focus_areas": _STRS,
        "evidence": _EVIDENCE})},
    "specialties": _STRS,
    "working_style": _obj({
        "cadence": _STR, "change_size": _STR, "commit_message_style": _STR,
        "pr_vs_direct": _STR, "testing_habit": _STR}),
    "review_behaviour": _obj({
        "as_reviewer": _STR, "as_author": _STR, "closest_collaborators": _STRS}),
    "how_it_ended": _STR,
    "evidence": _EVIDENCE,
    "confidence": _CONF,
    "inferred": _obj({
        "likely_seniority": {"type": "string",
                             "enum": ["founder/lead", "senior", "mid", "junior",
                                      "outside contributor", "automation"]},
        "apparent_role_title": _STR,
        "leadership_signals": _STRS,
        "why_focus_shifted": _STR,
        "departure_read": _STR,
        "confidence": _CONF}),
})

SYNTHESIS_SCHEMA = _obj({
    "process": _obj({
        "summary": _STR,
        "how_work_starts": _STR,
        "branching": _STR,
        "review_norms": _STR,
        "merge_norms": _STR,
        "release_process": _STR,
        "ci_role": _STR,
        "testing_norms": _STR,
        "stated_vs_actual": {**_STR, "description":
                             "CONTRIBUTING.md says issue-first and conventional commits; "
                             "say what the history actually shows"},
        "evolution": {"type": "array", "items": _obj({
            "era_slug": _STR, "change": _STR, "evidence": _EVIDENCE})},
        "evidence": _EVIDENCE, "confidence": _CONF}),
    "collaboration": _obj({
        "summary": _STR,
        "shape": {**_STR, "description": "How the group is organised in practice"},
        "subteams": {"type": "array", "items": _obj({
            "name": _STR, "members": _STRS, "focus": _STR, "evidence": _EVIDENCE})},
        "review_relationships": {"type": "array", "items": _obj({
            "reviewer": _STR, "author": _STR, "character": _STR})},
        "handoffs": {"type": "array", "items": _obj({
            "area": _STR, "from_person": _STR, "to_person": _STR, "when": _STR,
            "evidence": _EVIDENCE})},
        "automation_role": {**_STR, "description": "How bot contributors were used"},
        "evidence": _EVIDENCE, "confidence": _CONF,
        "inferred": _obj({"reading": _STR, "confidence": _CONF})}),
    "timeline": {"type": "array", "items": _obj({
        "date": _STR,
        "kind": {"type": "string", "enum": [
            "founding", "release", "process-change", "capability-introduced",
            "person-joined", "person-left", "major-refactor", "milestone", "other"]},
        "title": _STR, "detail": _STR, "evidence": _EVIDENCE, "confidence": _CONF})},
})


# =============================================================================
# Organization: the four stages
# =============================================================================
BRIEF = """You are reading the real history of an open-source Python project off its own
repository, so that a synthetic company can be built around it whose people, process and
timeline match what actually happened.

Rules you must hold to:

* Every factual claim goes in a measured field and carries `evidence` — episode ids
  (`ep-` followed by 12 hex characters), months (`YYYY-MM`), repository paths, contributor
  ids, or release tags. Cite only identifiers that appear in the evidence you were given.
  Never invent an episode id, a path, a person or a date.
* Anything you cannot show from the evidence — seniority, who was leading, why someone
  stopped committing — goes in the `inferred` block, never in a measured field. Inference is
  wanted, but it must be labelled as inference.
* `confidence` is 0-1 and should be low when you are extrapolating from thin evidence.
* Contributor ids are the slugs in the evidence (e.g. `ryan-marten`), not display names.
* Write plainly and specifically. "Owns the batch provider integrations" is useful;
  "works on the codebase" is not.
"""


def _stage_system(evidence: dict, grounding: dict) -> str:
    """The shared prefix. Identical across every call so it caches."""
    return BRIEF + "\n\nREPOSITORY-WIDE EVIDENCE\n" + json.dumps({
        "repository": {
            "remote": grounding["source"]["remote"],
            "span": evidence["totals"]["span"],
            "commits": evidence["totals"]["commits"],
            "episodes": evidence["totals"]["episodes"],
        },
        "readme_sections_the_project_uses_to_describe_itself": evidence["readme_sections"],
        "packages": [{"key": s["key"], "purpose": s["purpose"], "loc": s["lines_of_code"],
                      "commits": s["commit_count"]}
                     for s in grounding["subsystems"] if s["role"] == "src"],
        "extension_points": [{"name": p["name"], "path": p["path"],
                              "subsystem": p["subsystem"], "implementations": p["subclasses"]}
                             for p in grounding["interfaces"]["extension_points"]],
        "public_api": grounding["interfaces"]["public_api"],
        "monthly": evidence["monthly"],
        "quarterly_process_drift": evidence["quarterly_process_drift"],
        "package_first_seen": evidence["package_first_seen"],
        "releases": evidence["releases"],
        "contributors": [
            {"id": c["id"], "display_name": c["display_name"], "commits": c["commits"],
             "is_bot": c["is_bot"], "first": c["first_commit"], "last": c["last_commit"],
             "top_subsystems": list(c["subsystems"])[:5]}
            for c in grounding["contributors"]],
        "stated_conventions": grounding["documentation"]["stated_conventions"],
        "observed_adherence": grounding["documentation"]["observed_adherence"],
    }, ensure_ascii=False, separators=(",", ":"))


def stage_eras(llm: rl.LLM, system: str) -> list[dict]:
    prompt = (
        "Divide this project's history into eras — the phases a person who lived through it "
        "would name. Think about what the team was doing (planning, first working code, "
        "stabilising, expanding, maintaining) AND how they were working (direct pushes vs "
        "pull requests, review depth, merge style, release cadence), because both shift.\n\n"
        "Use the monthly table and the quarterly process drift to place the boundaries. "
        "Cover the entire span with no gaps and no overlaps. Prefer 4-7 eras. Name each one "
        "the way a team retrospective would, not with generic labels."
    )
    return llm.complete(system=system, prompt=prompt, schema=ERAS_SCHEMA,
                        label="eras")["eras"]


def stage_capability_areas(llm: rl.LLM, system: str, evidence: dict) -> list[dict]:
    prompt = (
        "Describe this codebase as capability areas: the things the product does, named the "
        "way the team would name them in conversation or on a roadmap.\n\n"
        "This is the part that matters most. Package names are NOT capability areas — "
        "`request_processor`, `types` and `status_tracker` are directories, not things anyone "
        "owns or plans work in. Look at how the README describes the product to its users, "
        "at what the extension points are for, and at what the episodes in each package are "
        "actually about, and name the real areas of capability. An area may span several "
        "packages, and one package may serve several areas.\n\n"
        "Map every area back to concrete packages, paths, interfaces and representative "
        "episode ids, and say when it was introduced and how busy it is now.\n\n"
        "EPISODE TITLES BY PACKAGE\n"
        + json.dumps(evidence["subsystem_episode_titles"], ensure_ascii=False,
                     separators=(",", ":"))
    )
    return llm.complete(system=system, prompt=prompt, schema=AREAS_SCHEMA,
                        label="capability-areas")["capability_areas"]


def stage_person(llm: rl.LLM, system: str, person: dict, eras: list[dict]) -> dict:
    era_index = [{"slug": e["slug"], "name": e["name"],
                  "span": f'{e["start_month"]}..{e["end_month"]}'} for e in eras]
    prompt = (
        f"Profile one contributor: {person['id']} ({person['display_name']}).\n\n"
        "Tell their arc against the shared eras below — what they were doing in each era they "
        "were present for, how their focus moved, and how their involvement ended. Read their "
        "working style off the actual evidence: commit cadence and size, how they write commit "
        "messages, whether they go through pull requests or push straight to main, whether "
        "tests travel with their changes. Read their review behaviour off who they review and "
        "who reviews them.\n\n"
        "Only cover eras this person was actually active in.\n\n"
        "ERAS\n" + json.dumps(era_index, ensure_ascii=False, separators=(",", ":")) +
        "\n\nTHIS PERSON'S EVIDENCE\n" +
        json.dumps(person, ensure_ascii=False, separators=(",", ":"))
    )
    profile = llm.complete(system=system, prompt=prompt, schema=PERSON_SCHEMA,
                           label=f"person:{person['id']}")
    profile["id"] = person["id"]
    profile["display_name"] = person["display_name"]
    return profile


def stage_synthesis(llm: rl.LLM, system: str, evidence: dict, eras: list[dict],
                    areas: list[dict], profiles: list[dict]) -> dict:
    condensed = [{"id": p["id"], "headline": p["headline"], "status": p["status"],
                  "specialties": p["specialties"],
                  "seniority": p["inferred"]["likely_seniority"],
                  "title": p["inferred"]["apparent_role_title"]} for p in profiles]
    prompt = (
        "Now describe how this organization actually worked, and lay out its timeline.\n\n"
        "For `process`: how work started, how branches and reviews and merges were handled, "
        "how releases happened, what CI was for, and — importantly — where stated convention "
        "and actual practice diverge. Track how the process changed era by era.\n\n"
        "For `collaboration`: the real shape of the group, any sub-teams visible in who works "
        "where, the review relationships that recur, ownership handoffs where one person took "
        "over an area from another, and how bot contributors were used.\n\n"
        "For `timeline`: the dated events someone would put on a wall chart. Include the "
        "founding, releases that mattered, process changes, capability introductions, people "
        "joining and leaving, and major refactors. Order it by date. 20-40 entries.\n\n"
        "ERAS\n" + json.dumps(eras, ensure_ascii=False, separators=(",", ":")) +
        "\n\nCAPABILITY AREAS\n" + json.dumps(
            [{k: a[k] for k in ("slug", "name", "description", "introduced_month", "owners")}
             for a in areas], ensure_ascii=False, separators=(",", ":")) +
        "\n\nPEOPLE\n" + json.dumps(condensed, ensure_ascii=False, separators=(",", ":")) +
        "\n\nREVIEW GRAPH\n" + json.dumps(evidence["review_graph"], ensure_ascii=False,
                                          separators=(",", ":"))
    )
    return llm.complete(system=system, prompt=prompt, schema=SYNTHESIS_SCHEMA,
                        label="synthesis", max_tokens=48000)


def run_organization(llm: rl.LLM, grounding: dict, evidence: dict, verbose: int) -> dict:
    system = _stage_system(evidence, grounding)
    rl.heading("Organization")

    eras = stage_eras(llm, system)
    rl.ok(f"{len(eras)} eras: " + " → ".join(e["name"] for e in eras))

    areas = stage_capability_areas(llm, system, evidence)
    rl.ok(f"{len(areas)} capability areas: " + ", ".join(a["name"] for a in areas[:6]) + "…")

    # Bots are profiled as tooling, not staff — which is itself a fact about how
    # this team worked, so they are kept, just tiered separately.
    people = sorted(evidence["people"].values(), key=lambda p: -p["commits"])
    profiles: list[dict] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(stage_person, llm, system, person, eras): person
                   for person in people}
        for future in as_completed(futures):
            person = futures[future]
            try:
                profiles.append(future.result())
            except Exception as exc:  # noqa: BLE001 — one bad profile must not lose the run
                rl.warn(f"profile failed for {person['id']}: {exc}")
    # Tie-break on id: without it, contributors with equal commit counts keep the
    # order their futures happened to complete in, which changes the synthesis
    # prompt and so its cache key on every run.
    profiles.sort(key=lambda p: (-evidence["people"][p["id"]]["commits"], p["id"]))
    rl.ok(f"{len(profiles)} contributor profiles")

    roles_by_id = {r["person"]: r for r in grounding["roles"]}
    roster = {"core": [], "occasional": [], "bots": []}
    for profile in profiles:
        person = evidence["people"][profile["id"]]
        if person["is_bot"]:
            tier = "bots"
        elif person["commits"] >= 5 and profile["id"] in roles_by_id:
            tier = "core"
        else:
            tier = "occasional"
        roster[tier].append(profile["id"])
        profile["tier"] = {"core": "core", "occasional": "occasional", "bots": "bot"}[tier]
        profile["measured"] = {
            "commits": person["commits"],
            "episodes_authored": person["episodes_authored"],
            "first_commit": person["first_commit"],
            "last_commit": person["last_commit"],
            "active_months": person["active_months"],
            "pr_share": person["pr_share"],
            "top_subsystems": person["subsystems"],
            "work_types": person["work_types"],
            "reviews_given": person["reviews_given"],
            "reviewed_by": person["reviewed_by"],
        }

    synthesis = stage_synthesis(llm, system, evidence, eras, areas, profiles)
    rl.ok(f"process, collaboration and a {len(synthesis['timeline'])}-entry timeline")

    return {
        "eras": eras,
        "capability_areas": areas,
        "people": {
            "roster": roster,
            "tiering_rule": "core = a non-bot contributor with >=5 commits and a derived "
                            "ownership role in `roles`; occasional = every other non-bot "
                            "contributor; bots = automation accounts, profiled as tooling",
            "counts": {k: len(v) for k, v in roster.items()},
            "profiles": profiles,
        },
        "process": synthesis["process"],
        "collaboration": synthesis["collaboration"],
        "timeline": synthesis["timeline"],
    }


# =============================================================================
# Organization: does it cite things that exist?
# =============================================================================
_EPISODE_RE = re.compile(r"\bep-[0-9a-f]{12}\b")


def verify_enrichment(enrichment: dict, grounding: dict, episodes_doc: dict) -> dict:
    """Check every citation resolves.

    A fabricated episode id or path is the one failure mode that actually
    matters here: it would look exactly like a real fact to everything
    downstream. Everything else is a judgement call the `confidence` and
    `inferred` fields already flag.
    """
    episode_ids = {e["id"] for e in episodes_doc["episodes"]}
    people_ids = {c["id"] for c in grounding["contributors"]}
    known_paths = set()
    for episode in episodes_doc["episodes"]:
        known_paths.update(f["path"] for f in episode["files"])
    # HEAD subsystems plus every subsystem that ever appears in an episode: a
    # deleted directory (tests/batch went in 2025-01) is a real part of this
    # history, and the model is shown it, so citing it is correct.
    subsystems = {s["key"] for s in grounding["subsystems"]}
    for episode in episodes_doc["episodes"]:
        subsystems.update(episode["metrics"]["file_distribution"]["by_subsystem"])
    era_slugs = {e["slug"] for e in enrichment["eras"]}
    span = grounding["source"]
    first, last = span["first_commit"]["date"][:7], span["last_commit"]["date"][:7]

    problems: list[str] = []

    def check_ids(blob: Any, where: str) -> None:
        for found in _EPISODE_RE.findall(json.dumps(blob, ensure_ascii=False)):
            if found not in episode_ids:
                problems.append(f"{where}: cites unknown episode {found}")

    check_ids(enrichment, "enrichment")

    for era in enrichment["eras"]:
        if not (first <= era["start_month"] <= last) or not (first <= era["end_month"] <= last):
            problems.append(f"era {era['slug']}: {era['start_month']}..{era['end_month']} "
                            f"outside the repository span {first}..{last}")
        for person in era["key_people"]:
            if person not in people_ids:
                problems.append(f"era {era['slug']}: unknown person {person}")

    for area in enrichment["capability_areas"]:
        for path in area["paths"]:
            if path not in known_paths and not any(p.startswith(path.rstrip("/") + "/")
                                                   for p in known_paths):
                problems.append(f"area {area['slug']}: path not in the repository: {path}")
        for package in area["packages"]:
            if package not in subsystems:
                problems.append(f"area {area['slug']}: unknown package {package}")
        for owner in area["owners"]:
            if owner not in people_ids:
                problems.append(f"area {area['slug']}: unknown owner {owner}")

    for profile in enrichment["people"]["profiles"]:
        if profile["id"] not in people_ids:
            problems.append(f"profile {profile['id']}: not a known contributor")
        for step in profile["arc"]:
            if step["era_slug"] not in era_slugs:
                problems.append(f"profile {profile['id']}: unknown era {step['era_slug']}")

    for handoff in enrichment["collaboration"]["handoffs"]:
        for key in ("from_person", "to_person"):
            if handoff[key] not in people_ids:
                problems.append(f"handoff {handoff['area']}: unknown person {handoff[key]}")

    roster = enrichment["people"]["roster"]
    covered = roster["core"] + roster["occasional"] + roster["bots"]
    if len(covered) != len(set(covered)):
        problems.append("roster: a contributor appears in more than one tier")
    missing = people_ids - set(covered)
    profiled = {p["id"] for p in enrichment["people"]["profiles"]}
    if missing - (people_ids - profiled):
        problems.append(f"roster: profiled contributors missing from the roster: "
                        f"{sorted(missing)[:5]}")

    return {"citations_checked": len(_EPISODE_RE.findall(json.dumps(enrichment))),
            "problems": problems}


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    parser = rl.base_parser(__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"output file (default: {DEFAULT_OUT})")
    parser.add_argument("--top-n", type=int, default=25,
                        help="how many entries to keep in ranked lists (default: 25)")
    parser.add_argument("--episodes", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "engineering_episodes.json",
                        help="episode file the organization pass reads")
    parser.add_argument("--enrich", action=argparse.BooleanOptionalAction, default=None,
                        help="read the organization off the evidence with Claude "
                             "(default: on when ANTHROPIC_API_KEY is available)")
    parser.add_argument("--model", default=rl.MODEL)
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--no-refresh", action="store_true",
                        help="serve every model response from cache; never call the API")
    parser.add_argument("--cache-dir", type=Path, default=rl.DEFAULT_CACHE_DIR / "llm")
    parser.add_argument("--history", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "repository_history.json",
                        help="Stage 0 record to take commits from")
    args = parser.parse_args()

    enrich = args.enrich
    if enrich is None:
        enrich = bool(rl.env_value("ANTHROPIC_API_KEY")) or args.no_refresh
        if not enrich:
            rl.warn("no ANTHROPIC_API_KEY — writing the measured sections only. "
                    "Pass --enrich to force, or --no-enrich to silence this.")

    git = rl.Git(args.repo)
    rl.heading(f"Reading {git.repo}")
    history = None
    if args.history.exists():
        history = json.loads(args.history.read_text(encoding="utf-8"))
        rl.info(f"commits from {args.history.name} ({len(history['commits'])} across all refs)")
    repo = Repo(git, args.rev, args.since, args.until, history)
    rl.ok(f"{len(repo.commits)} commits, {len(repo.paths)} tracked files, "
          f"{len(repo.ids.people)} contributors")

    layout = repo.layout
    if not layout.confident:
        # Every lookup downstream is keyed on these roots. Without them the
        # analysis would still run and still exit 0, having found nothing —
        # which reads exactly like a repository with no structure.
        rl.fail(
            f"could not find any source in {git.repo}.\n"
            f"  Languages seen: {layout.languages or 'none'}\n"
            f"  Tried: a declared package in pyproject.toml, the shallowest\n"
            f"  directories containing __init__.py, then the directories holding\n"
            f"  source files.\n\n"
            f"  Point --repo at the right checkout, or pass --rev if the layout\n"
            f"  only exists on another revision.")
    rl.info(f"source {', '.join(layout.source_roots)} · "
            f"{layout.primary_language} · tests {', '.join(layout.test_roots) or 'none found'}")
    for line in layout.evidence:
        rl.info(f"  layout: {line}")

    rl.heading("Static shape")
    subsystems = section_subsystems(repo)
    interfaces = section_interfaces(repo)
    tests = section_tests(repo)
    configuration = section_configuration(repo)
    ci = section_ci(repo)
    dependencies = section_dependencies(repo, args.top_n)
    dependencies["external"]["declared"] = [d["name"] for d in configuration["runtime_dependencies"]]
    documentation = section_documentation(repo)
    rl.ok(f"{len(subsystems)} subsystems, "
          f"{len(interfaces['extension_points'])} extension points, "
          f"{tests['test_function_count']} test functions, "
          f"{ci['workflow_count']} workflow(s)")

    rl.heading("History")
    hotspots = section_hotspots(repo, args.top_n)
    contributors, roles, ownership = section_contributors(repo, args.top_n)
    work_types = section_work_types(repo)
    rl.ok(f"{len(contributors)} contributors, {len(roles)} with a derived role, "
          f"{len(work_types['distribution'])} kinds of work")

    test_map = tests_by_subsystem(repo)
    tests["subsystems_covered"] = {k: len(v) for k, v in sorted(test_map.items())}
    capability_areas = section_capability_areas(
        repo, subsystems, interfaces, ownership, tests, test_map)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": rl.now_iso(),
        "generator": "data_gen/analyze_repository.py",
        "method": "deterministic: git history plus Python static analysis. No model, no network.",
        "source": section_source(repo),
        "layout": repo.layout.as_json(),
        "capability_areas": capability_areas,
        "subsystems": subsystems,
        "interfaces": interfaces,
        "test_architecture": tests,
        "configuration": configuration,
        "ci_cd": ci,
        "dependencies": dependencies,
        "documentation": documentation,
        "change_hotspots": hotspots,
        "contributors": contributors,
        "roles": roles,
        "ownership": ownership,
        "work_types": work_types,
    }

    payload["analysis"] = {
        "measured_keys": sorted(k for k in payload if k not in ("analysis",)),
        "interpreted_keys": [],
        "method": "deterministic only",
    }

    if enrich:
        if not args.episodes.exists():
            rl.fail(f"{args.episodes} does not exist. The organization pass reads episode-level\n"
                    "  evidence, so run build_episodes.py first:\n\n"
                    "    python3 data_gen/build_episodes.py\n"
                    "    python3 data_gen/analyze_repository.py\n\n"
                    "  Or pass --no-enrich for the measured sections only.")
        episodes_doc = json.loads(args.episodes.read_text(encoding="utf-8"))
        evidence = org_evidence(payload, episodes_doc)
        llm = rl.LLM(args.cache_dir, model=args.model, effort=args.effort,
                     refresh=not args.no_refresh, verbose=args.verbose)
        enrichment = run_organization(llm, payload, evidence, args.verbose)

        # The measured areas stay, under a name that says what they are: they are
        # the package-level evidence the interpreted ones were read off.
        payload["capability_areas_measured"] = payload["capability_areas"]
        payload["capability_areas"] = enrichment["capability_areas"]
        for key in ("eras", "people", "process", "collaboration", "timeline"):
            payload[key] = enrichment[key]

        report = verify_enrichment(enrichment, payload, episodes_doc)
        rl.heading("Checking every citation resolves")
        if report["problems"]:
            for problem in report["problems"][:20]:
                rl.warn(problem)
            rl.warn(f"{len(report['problems'])} citation problem(s) — "
                    f"the enrichment is written anyway, flagged in `analysis`")
        else:
            rl.ok(f"{report['citations_checked']} episode citations, all resolving; "
                  "paths, people and eras all check out")

        interpreted = ["capability_areas", "eras", "people", "process",
                       "collaboration", "timeline"]
        payload["analysis"] = {
            "method": "measured sections from git and static analysis; interpreted sections "
                      "read off that evidence by a model, with per-claim evidence, confidence "
                      "and separate `inferred` blocks",
            "model": args.model,
            "effort": args.effort,
            "generated_at": rl.now_iso(),
            "inputs": {
                "episodes_file": str(args.episodes),
                "episodes_sha256": hashlib.sha256(
                    args.episodes.read_bytes()).hexdigest()[:16],
                "head_commit": payload["source"]["head_commit"],
            },
            "interpreted_keys": interpreted,
            "measured_keys": sorted(k for k in payload
                                    if k not in interpreted and k != "analysis"),
            "citation_check": report,
            "usage": {**llm.stats, "estimated_cost_usd": round(llm.cost(), 2)},
        }
        rl.info(f"{llm.stats['calls']} model calls, {llm.stats['cache_hits']} from cache, "
                f"~${llm.cost():.2f}")

    size = rl.write_json(args.out, payload)
    rl.heading("Wrote")
    rl.ok(f"{args.out} ({rl.human_bytes(size)})")
    if enrich:
        for area in payload["capability_areas"][:10]:
            rl.info(f"{area['name'][:40]:42s} {area['activity']:10s} "
                    f"owners: {', '.join(area['owners'][:2]) or '-'}")
    else:
        for area in capability_areas[:8]:
            rl.info(f"{area['key']:34s} {area['change_volume']['commits']:4d} commits  "
                    f"owners: {', '.join(o['id'] for o in area['owners'][:2]) or '-'}")


if __name__ == "__main__":
    main()
