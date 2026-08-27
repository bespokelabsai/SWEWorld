#!/usr/bin/env python3
"""Is the code in a transcript real, and did anybody look before writing it?

Two questions, deliberately separate.

**Is it grounded.** Every module path, class, function and attribute a message
names is checked against the repository as it stood THAT DAY. The test is that
the symbol exists, not that the snippet was copied: an engineer in chat writes
illustrative code, elides, paraphrases. What they may not do is invent
`curator.batch.resume_from()`, or import a module that arrives three months
later — those are wrong in a way a reader cannot detect, which is the only kind
of wrong that matters in a corpus meant to be believed.

**Did they look.** The repo tools record every call, so consulting the tree
before quoting is observable rather than inferred from whether the output
happens to be right. A persona who guesses correctly still guessed.

Reads a finished run. Simulates nothing, calls no model.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

# A fenced block, and the inline `thing` that carries most of the code in chat.
FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.S)
INLINE = re.compile(r"`([^`\n]{2,80})`")

# What counts as a claim about the codebase. A bare word is not — "cache" is
# English — so an inline span must look like code before it is judged as code.
DOTTED = re.compile(r"\b([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+)\b")
CALL = re.compile(r"\b([a-zA-Z_][\w]*)\s*\(")
IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))", re.M)
# A path only counts as a claim about the CODE if it looks like source. The
# corpus is full of `engineering/curator-llm-core-build-plan.md`, which is a
# wiki page: read as code it yields a dotted name and five invented symbols.
CODE_EXT = ("py", "toml", "cfg", "ini", "yaml", "yml", "lock", "txt", "sh")
FILENAME = re.compile(r"\b([\w-]+\.(?:" + "|".join(("py", "toml", "cfg",
                       "yaml", "yml", "sh")) + r"))\b")
PATHLIKE = re.compile(
    r"\b((?:[\w.-]+/)+[\w.-]+\.(?:" + "|".join(CODE_EXT) + r"))\b")

# Names that say nothing about curator: builtins, the standard library, and the
# handful of methods every object has. Without this the checker mostly measures
# its own noise — `d.get(...)`, `os.getuid()`, a JSON `null` — and reports a
# corpus as 10% grounded when the real figure is nothing like that.
_BUILTINS = set(dir(__builtins__) if isinstance(__builtins__, dict)
                else dir(__builtins__))
COMMON = _BUILTINS | set(getattr(sys, "stdlib_module_names", ())) | {
    "self", "cls", "np", "pd", "df", "args", "kwargs", "e", "exc", "err",
    # what every dict, list, str and file already answers to
    "get", "keys", "values", "items", "update", "append", "extend", "pop",
    "add", "remove", "insert", "sort", "sorted", "join", "split", "strip",
    "lower", "upper", "replace", "format", "startswith", "endswith", "read",
    "write", "close", "flush", "seek", "encode", "decode", "copy", "count",
    "index", "find", "clear", "setdefault", "isoformat", "now", "utcnow",
    "sleep", "dumps", "loads", "dump", "load", "match", "search", "sub",
    "compile", "exists", "mkdir", "parent", "name", "stem", "suffix", "text",
    # JSON and shell literals that are not Python at all
    "null", "true", "false", "nan", "inf", "echo", "cd", "ls", "cat", "grep",
    # logging, which every module does and no module owns
    "info", "debug", "warning", "error", "exception", "critical", "log",
    # stdlib members people call by their bare name
    "as_completed", "wraps", "partial", "chain", "islice", "defaultdict",
    "Counter", "dataclass", "field", "Path", "Optional", "Any", "Union",
    "List", "Dict", "Iterator", "Callable", "TypeVar", "Enum", "ABC",
    "gather", "run", "create_task", "to_thread", "Semaphore", "Lock",
    "ThreadPoolExecutor", "ProcessPoolExecutor", "contextmanager",
}

# The libraries curator is BUILT ON. A message naming `anthropic.Anthropic` or
# `BaseModel` is not inventing a curator symbol — it is naming somebody else's,
# correctly. Flagging those turns a grounding report into a list of the
# project's dependencies.
THIRD_PARTY = {
    "anthropic", "openai", "litellm", "vllm", "pydantic", "requests", "httpx",
    "aiohttp", "datasets", "pandas", "numpy", "pyarrow", "tqdm", "rich",
    "click", "typer", "fastapi", "uvicorn", "nest_asyncio", "tiktoken",
    "google", "boto3", "botocore", "huggingface_hub", "transformers", "torch",
    "instructor", "tenacity", "aiofiles", "xxhash", "posthog",
    # the classes those libraries are usually reached through
    "Anthropic", "AsyncAnthropic", "OpenAI", "AsyncOpenAI", "BaseModel",
    "Field", "ValidationError", "AsyncClient", "Client", "Session", "LLM",
    "Dataset", "DataFrame", "Series", "Console", "Progress", "Table",
}


def _claims(name: str) -> bool:
    """Is this name a claim about curator, or just Python?

    A single lowercase word is almost never a claim — `results`, `elapsed`,
    `requests` are what any snippet calls its variables. A dotted path or an
    underscored/CamelCase identifier is specific enough to be checkable.
    """
    root, tail = name.split(".")[0], name.split(".")[-1]
    # `distill.py` mentioned in prose parses as a dotted attribute whose tail
    # is `py`, and gets judged as an invented symbol. It is a filename; it
    # belongs to the path check, which knows how to look for it by basename.
    if tail in CODE_EXT:
        return False
    if root in COMMON or tail in COMMON:
        return False
    if root in THIRD_PARTY or tail in THIRD_PARTY:
        return False
    if "." in name:
        return True
    return "_" in name or not name.islower()


def code_spans(text: str) -> list[str]:
    """Every stretch of a message that is making a claim about the code."""
    out = [m.group(1) for m in FENCE.finditer(text)]
    for m in INLINE.finditer(FENCE.sub(" ", text)):
        span = m.group(1).strip()
        # A dotted path, a call, or a file — and also a bare identifier that is
        # specific enough to check. `supports_structured_output` and `__call__`
        # are precisely the claims worth testing, and requiring a dot or a
        # paren threw them away: two thirds of the corpus's code claims are a
        # single backticked name.
        if (DOTTED.search(span) or CALL.search(span) or PATHLIKE.search(span)
                or (" " not in span and _claims(span))):
            out.append(span)
    return out


def symbols(span: str) -> tuple[set[str], set[str]]:
    """(names claimed, file paths claimed) in one span.

    Parsed as Python where it parses, because an AST distinguishes a call from
    a word inside a string. Where it does not — a fragment, pseudo-code, a
    traceback — fall back to the regexes rather than skipping the span, since
    a fragment is exactly where an invented name hides.
    """
    names: set[str] = set()
    paths = {m.group(1) for m in PATHLIKE.finditer(span)}
    try:
        tree = ast.parse(span)
    except SyntaxError:
        names |= {m.group(1) for m in CALL.finditer(span)}
        names |= {m.group(1) for m in DOTTED.finditer(span)}
        for a, b in IMPORT.findall(span):
            names.add(a or b)
        return {n for n in names if _claims(n)}, paths

    # Anything the snippet defines for itself — a local, a loop variable, a
    # parameter, an import alias — is not a claim about the repository. Missing
    # this made the checker flag `t_start` and `elapsed` as invented curator
    # symbols, which is nonsense: the snippet is where they come from.
    local: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            local.add(node.name)
            local |= {a.arg for a in getattr(node.args, "args", [])} \
                if hasattr(node, "args") else set()
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            local.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            local |= {a.asname for a in node.names if a.asname}
        elif isinstance(node, ast.ExceptHandler) and node.name:
            local.add(node.name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return {n for n in names - local if n and _claims(n)}, paths


class Tree:
    """The repository on one date, and what it contains, cached."""

    def __init__(self, git: rl.Git):
        self.git = git
        self._rev: dict[str, str | None] = {}
        self._files: dict[str, set[str]] = {}
        self._names: dict[str, set[str]] = {}

    def rev(self, date: str) -> str | None:
        if date not in self._rev:
            self._rev[date] = self.git.rev_at(date)
        return self._rev[date]

    def files(self, date: str) -> set[str]:
        rev = self.rev(date)
        if not rev:
            return set()
        if rev not in self._files:
            self._files[rev] = set(
                self.git.lines("ls-tree", "-r", "--name-only", rev))
        return self._files[rev]

    def names(self, date: str) -> set[str]:
        """Every module, class, function and attribute defined that day.

        Read from the tree itself rather than from a curated list: the point is
        to compare a message against the repository, and any list we maintained
        by hand would drift from it.
        """
        rev = self.rev(date)
        if not rev:
            return set()
        if rev in self._names:
            return self._names[rev]
        found: set[str] = set()
        py = [f for f in self.files(date) if f.endswith(".py")]
        for path in py:
            found.add(Path(path).stem)
            dotted = path.replace("/", ".").removesuffix(".py")
            found.add(dotted)
            found.add(dotted.removeprefix("src."))
            body = self.git.file_at(rev, path)
            if not body:
                continue
            try:
                tree = ast.parse(body)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    found.add(node.name)
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            found.add(t.id)
                elif isinstance(node, ast.arg):
                    found.add(node.arg)
        self._names[rev] = found
        return found

    def has_name(self, date: str, name: str) -> bool:
        """A dotted name resolves if its LAST segment is defined that day.

        The tail is what a reader would look up. Insisting the whole path
        resolve would fail `self.client.chat.completions.create`, which is a
        real call through objects this repository does not define.
        """
        known = self.names(date)
        if name in known:
            return True
        return name.split(".")[-1] in known

    def has_path(self, date: str, path: str) -> bool:
        files = self.files(date)
        if path in files:
            return True
        tail = path.lstrip("./")
        return any(f == tail or f.endswith("/" + tail) for f in files)


def looked(activity: list[dict]) -> dict[tuple, list[str]]:
    """(date, who) -> the repo paths they opened that day."""
    out: dict[tuple, list[str]] = defaultdict(list)
    for row in activity:
        # `Store._touch` names the field `tool`, not `name`. Reading the wrong
        # key made every lookup miss, so "did they look" answered no for
        # everybody — including a run where somebody plainly had.
        if row.get("app") != "repo" and row.get("tool") not in (
                "read_repo", "list_repo", "search_repo", "recent_commits"):
            continue
        day = str(row.get("ts") or "")[:10]
        out[(day, row.get("uid") or row.get("by") or "")].append(
            str(row.get("target") or ""))
    return out


def planted_names(build: Path) -> set[str]:
    """Identifiers the plant deliberately requires.

    A hidden requirement names the API the task is asking somebody to BUILD —
    `cache_stats()` appears nowhere in 1,734 commits because writing it is the
    task. Counting those as invented would score the corpus down for doing
    exactly what it was designed to do, so they are reported apart from real
    inventions rather than mixed in with them.
    """
    clues = build / "clues.json"
    if not clues.exists():
        return set()
    out: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.get("verbatim") or []:
                token = str(v).strip("`").strip()
                out.add(token)
                out.add(token.split("(")[0].split("=")[0].split(".")[-1])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(json.loads(clues.read_text()))
    return {o for o in out if o}


def check(run: Path, git: rl.Git, limit: int = 0,
          planted: set[str] | None = None) -> dict:
    doc = json.loads((run / "transcript.json").read_text())
    tree = Tree(git)
    seen = looked(json.loads((run / "activity.json").read_text())
                  if (run / "activity.json").exists() else [])

    rows, totals = [], Counter()
    for channel in doc.get("channels") or []:
        for msg in channel.get("messages") or []:
            text = msg.get("text") or ""
            spans = code_spans(text)
            if not spans:
                continue
            date = str(msg.get("ts") or "")[:10]
            who = msg.get("userId") or ""
            claimed_names: set[str] = set()
            claimed_paths: set[str] = set()
            for span in spans:
                n, p = symbols(span)
                claimed_names |= n
                claimed_paths |= p
                # a bare `distill.py` is a claim that a file exists, so check it
                claimed_paths |= {m.group(1) for m in FILENAME.finditer(span)}
            if not claimed_names and not claimed_paths:
                continue
            planted = planted or set()
            missing = [n for n in claimed_names if not tree.has_name(date, n)]
            by_design = sorted(n for n in missing
                               if n in planted or n.split(".")[-1] in planted)
            bad_names = sorted(n for n in missing if n not in by_design)
            bad_paths = sorted(p for p in claimed_paths
                               if not tree.has_path(date, p))
            totals["messages"] += 1
            totals["names"] += len(claimed_names)
            totals["paths"] += len(claimed_paths)
            totals["bad_names"] += len(bad_names)
            totals["by_design"] += len(by_design)
            totals["bad_paths"] += len(bad_paths)
            opened = seen.get((date, who), [])
            if opened:
                totals["looked"] += 1
            if not bad_names and not bad_paths:
                totals["grounded"] += 1
            rows.append({
                "date": date, "channel": channel.get("name"), "who": who,
                "text": text[:400],
                "names": sorted(claimed_names), "paths": sorted(claimed_paths),
                "ungrounded_names": bad_names, "ungrounded_paths": bad_paths,
                "by_design": by_design,
                "looked_first": bool(opened), "opened": opened[:6],
                "grounded": not bad_names and not bad_paths,
            })
            if limit and len(rows) >= limit:
                return {"rows": rows, "totals": dict(totals)}
    return {"rows": rows, "totals": dict(totals)}


def report(result: dict, run: Path) -> str:
    t = result["totals"]
    n = t.get("messages", 0)
    L = [f"# Is the code in {run.name} real?", "",
         f"{n} message(s) make a claim about the codebase.", ""]
    if n:
        L += [f"- **{t.get('grounded', 0)} of {n}** name only things that "
              f"existed on the day they were sent "
              f"({100 * t.get('grounded', 0) // n}%)",
              f"- **{t.get('looked', 0)} of {n}** were sent by someone who had "
              f"opened the repository that day "
              f"({100 * t.get('looked', 0) // n}%)",
              f"- {t.get('bad_names', 0)} of {t.get('names', 0)} symbol(s) and "
              f"{t.get('bad_paths', 0)} of {t.get('paths', 0)} path(s) do not "
              "resolve",
              f"- {t.get('by_design', 0)} further symbol(s) are absent BY "
              "DESIGN — the plant names them because building them is the "
              "task", ""]
    worst = Counter()
    for row in result["rows"]:
        for name in row["ungrounded_names"]:
            worst[name] += 1
    if worst:
        L += ["## Invented most often", "",
              "| symbol | times |", "|---|---|"]
        L += [f"| `{k}` | {v} |" for k, v in worst.most_common(20)]
        L.append("")
    bad = [r for r in result["rows"] if not r["grounded"]]
    L += [f"## {len(bad)} message(s) naming something that was not there", ""]
    for row in bad[:60]:
        L += [f"**{row['date']} #{row['channel']} — {row['who']}**"
              f"{'' if row['looked_first'] else '  *(never opened the repo)*'}",
              "",
              "> " + row["text"].replace("\n", "\n> ")[:300], "",
              "does not resolve: " +
              ", ".join(f"`{x}`" for x in
                        (row["ungrounded_names"] + row["ungrounded_paths"])[:12]),
              ""]
    if len(bad) > 60:
        L.append(f"... and {len(bad) - 60} more.")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True,
                        help="path to a run directory, or a name under "
                             "build/phase4/runs/")
    parser.add_argument("--repo", type=Path, default=rl.DEFAULT_REPO)
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after N code-bearing messages")
    args = parser.parse_args(argv)

    run = Path(args.run)
    if not run.is_dir():
        run = rl.DEFAULT_BUILD_DIR / "phase4" / "runs" / args.run
    if not (run / "transcript.json").exists():
        rl.fail(f"{run} has no transcript.json")
    if not (args.repo / ".git").exists():
        rl.fail(f"{args.repo} is not a git repository — grounding needs the "
                "real tree to compare against")

    result = check(run, rl.Git(args.repo), args.limit,
                   planted_names(rl.DEFAULT_BUILD_DIR))
    (run / "grounding.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (run / "grounding.md").write_text(report(result, run), encoding="utf-8")

    t = result["totals"]
    n = t.get("messages", 0)
    rl.ok(f"{run / 'grounding.md'} — {n} message(s) claim code; "
          f"{t.get('grounded', 0)} grounded, {t.get('looked', 0)} looked first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
