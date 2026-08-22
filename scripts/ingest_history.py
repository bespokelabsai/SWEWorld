#!/usr/bin/env python3
"""Put the real repository's history into Gitea under the company's own names.

Every commit, branch, tag and merge is the real one. The only thing that changes
is who signed it: author and committer identities, the personal branch prefixes
this team used (`mahesh/client`), and the names, addresses and forge URLs that
appear inside commit messages. Trees are untouched, which is the point — the
code an agent reads in the world is byte-for-byte the code that was really
written, and `git log` tells the story that really happened.

Two modes, because the two halves run in different places:

    scripts/ingest_history.py --export       # on the host, where the clone is
    scripts/ingest_history.py                # in the world, where Gitea is

`--export` reads the real clone, rewrites the identities, and writes a bundle
plus `data/history/manifest.json` — the author map, the ref map, and the
old->new commit SHA map that `ingest_forge.py` needs to point pull requests at
commits that exist. The default mode reads those two files and needs nothing
else.

## The real repository is never written to

`--export` clones `--source-repo` to a temporary mirror and works only there.
Nothing in this script writes to the source, and nothing in it can reach GitHub:
there is no remote on the working copy, the push target is checked against the
world's own host before any push, and no GitHub credential is read. `git
fast-export` cannot modify a remote in any case — the guards exist so a later
edit cannot quietly turn a read into a write.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worldlib as wl  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "curator"
DEFAULT_GROUNDING = REPO_ROOT / "data_gen" / "build" / "company_grounding.json"
MANIFEST_NAME = "manifest.json"
BUNDLE_NAME = "curator.bundle"

# The CI workflow the bootstrap adds on top of its baseline commit. The real
# history has no `.gitea/` directory, so force-pushing over `main` removes it and
# the runner goes quiet — with nothing in the UI to say why.
# Two places, because this script runs in two: from the checkout on the host,
# and inside the world, where the image keeps its build sources under /world-src
# and `data/` and `scripts/` are all that get copied in.
CI_TEMPLATES = (Path("/world-src/ci-templates/python.yml"),
                REPO_ROOT / "world" / "ci-templates" / "python.yml")
CI_PATH = ".gitea/workflows/ci.yml"

# Gitea's default MIN_PASSWORD_LENGTH. Below it, account creation fails with a
# message that names the wrong problem.
GITEA_MIN_PASSWORD = 8

# A push may only go to the world. Anything else is a bug that would send a
# rewritten history somewhere it was never meant to go.
FORBIDDEN_PUSH = re.compile(r"github\.com|gitlab\.com|bitbucket\.org", re.I)

# Email local parts and name fragments that are words before they are people.
# Replacing these would rewrite half the commit messages in the project.
NOT_A_NAME = frozenset({
    "github", "noreply", "users", "info", "mail", "team", "code", "data",
    "test", "root", "user", "admin", "curator", "bespoke", "action", "actions",
})


# =============================================================================
# git
# =============================================================================
def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}GB"


def git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: "
                           f"{proc.stderr.strip()[:400]}")
    return proc.stdout.strip()


def git_lines(repo: Path, *args: str) -> list[str]:
    out = git(repo, *args)
    return out.splitlines() if out else []


# =============================================================================
# Reading the source, without writing to it
# =============================================================================
def preflight(source: Path) -> dict:
    """Refuse to start if the source is not a clean repository we can read."""
    if not (source / ".git").exists() and not (source / "HEAD").exists():
        raise SystemExit(f"--source-repo {source} is not a git repository")
    if git(source, "rev-parse", "--is-inside-work-tree", check=False) == "true":
        dirty = git(source, "status", "--porcelain")
        if dirty:
            raise SystemExit(
                f"{source} has uncommitted changes. This script only ever reads it, but a\n"
                "  dirty tree means someone is working there, and a mirror clone of a\n"
                "  half-finished state is not the history you want in the world.")
    return {
        "remote": git(source, "remote", "get-url", "origin", check=False),
        "head": git(source, "rev-parse", "HEAD"),
        "commits": int(git(source, "rev-list", "--all", "--count")),
    }


def mirror(source: Path, into: Path) -> Path:
    """A disposable copy, with no way back to where it came from.

    `--no-hardlinks` is not a detail: a local clone hardlinks pack files by
    default, so a repack in the copy would be reaching into the real
    repository's object store.
    """
    dest = into / "source.git"
    subprocess.run(["git", "clone", "--mirror", "--no-hardlinks",
                    str(source), str(dest)],
                   check=True, capture_output=True)

    # A working clone keeps its branches as remote-tracking refs, and a mirror
    # of it copies them there verbatim: `refs/remotes/origin/mahesh/client`
    # rather than `refs/heads/mahesh/client`. `fast-export --all` then exports
    # the one local branch, and the 127 commits that live only on side branches
    # vanish — the export succeeds, every check passes, and the world quietly
    # gets a history with the interesting parts missing.
    #
    # Promote before removing the remote, not after: `git remote remove` deletes
    # every ref under `refs/remotes/<name>/` on its way out, so the obvious
    # ordering destroys exactly what this loop exists to save.
    for line in git_lines(dest, "for-each-ref",
                          "--format=%(refname) %(objectname)", "refs/remotes"):
        ref, _, sha = line.partition(" ")
        short = ref.split("/", 3)[-1]
        if short != "HEAD" and not git(dest, "rev-parse", "--verify", "--quiet",
                                       f"refs/heads/{short}", check=False):
            git(dest, "update-ref", f"refs/heads/{short}", sha)
    git(dest, "remote", "remove", "origin", check=False)
    for ref in git_lines(dest, "for-each-ref", "--format=%(refname)", "refs/remotes"):
        git(dest, "update-ref", "-d", ref)
    return dest


# =============================================================================
# Who is who
# =============================================================================
def signatures(repo: Path) -> set[tuple[str, str]]:
    """Every (name, email) that signed anything, as author or committer."""
    pairs = set()
    for line in git_lines(repo, "log", "--all", "--reflog", "--format=%an%x00%ae%x00%cn%x00%ce"):
        an, ae, cn, ce = line.split("\x00")
        pairs.add((an, ae))
        pairs.add((cn, ce))
    # `for-each-ref` speaks a different format language from `git log` — no
    # `%x00` — so annotated tags are parsed from the `Name <email>` form instead.
    for line in git_lines(repo, "for-each-ref",
                          "--format=%(taggername) %(taggeremail)", "refs/tags"):
        match = re.match(r"^(.*) <(.*)>$", line.strip())
        if match and match.group(1):
            pairs.add((match.group(1), match.group(2)))
    return pairs


def build_author_map(pairs: set[tuple[str, str]], people: list[dict],
                     domain: str) -> tuple[dict, list[str]]:
    """Map every real signature onto a persona, or say exactly which ones failed.

    Joined on email first and name second, which is how `data_gen` grouped these
    identities in the first place. An unmapped signature is fatal rather than
    passed through: passing it through is precisely how a real name ends up in
    the world.
    """
    by_email: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    for person in people:
        for real in person["real"]:
            for email in real["emails"]:
                by_email.setdefault(email.lower(), person)
            for name in real["names"]:
                by_name.setdefault(name.lower(), person)

    mapped: dict[str, dict] = {}
    unmapped: list[str] = []
    for name, email in sorted(pairs):
        person = by_email.get(email.lower()) or by_name.get(name.lower())
        if person is None:
            unmapped.append(f"{name} <{email}>")
            continue
        syn = person["synthetic"]
        mapped[f"{name}\x00{email}"] = {
            "name": syn["display_name"],
            "email": f"{syn['id']}@{domain}",
            "persona": syn["id"],
        }
    return mapped, unmapped


def build_handles(people: list[dict]) -> dict[str, str]:
    """Every spelling of a person, flattened, pointing at their persona id."""
    handles: dict[str, str] = {}
    for person in people:
        pid = person["synthetic"]["id"]
        for real in person["real"]:
            for name in real["names"]:
                handles.setdefault(re.sub(r"[^a-z0-9]", "", name.lower()), pid)
            for email in real["emails"]:
                local = re.sub(r"^\d+\+", "", email.split("@", 1)[0]).lower()
                handles.setdefault(re.sub(r"[^a-z0-9]", "", local), pid)
            if real.get("github_login"):
                handles.setdefault(
                    re.sub(r"[^a-z0-9]", "", real["github_login"].lower()), pid)
    return handles


def match_handle(prefix: str, handles: dict[str, str]) -> str | None:
    """Whose handle is this branch prefix?

    Exact first, then a unique prefix match — `ryanm` for `ryanmarten` — with a
    five-character floor, or `docs/`, `fix/` and `feat/` start looking like
    people. Ambiguity resolves only when every candidate is the same person,
    which is the common case: a name and an email local part usually agree.
    """
    key = re.sub(r"[^a-z0-9]", "", prefix.lower())
    if key in handles:
        return handles[key]
    if len(key) < 5:
        return None
    hits = {p for h, p in handles.items() if h.startswith(key)}
    return hits.pop() if len(hits) == 1 else None


def branch_prefixes(repo: Path) -> set[str]:
    """Branch prefixes that appear anywhere — as a ref, or quoted in a message.

    Merge subjects preserve the branch a change came from long after the branch
    itself is deleted: `Merge pull request #289 from bespokelabsai/mahesh/batchbug`
    outlives `mahesh/batchbug` by years. Rewriting the refs alone leaves the
    names sitting in `git log`.
    """
    found: set[str] = set()
    for ref in git_lines(repo, "for-each-ref", "--format=%(refname)"):
        short = ref.split("/", 2)[-1]
        if "/" in short:
            found.add(short.split("/", 1)[0])
    text = "\n".join(git_lines(repo, "log", "--all", "--format=%B"))
    for match in re.finditer(r"(?:from|branch)\s+'?(?:[\w.-]+/)?([\w.-]+)/", text):
        found.add(match.group(1))
    return found


def build_ref_map(repo: Path, handles: dict[str, str]) -> dict[str, str]:
    """Rename the branches that carry a person's handle.

    This team prefixed topic branches with their own handle — `mahesh/client`,
    `ryanm/together-qwq-example`, `shreyas/finetuning-client` — so the branch
    list doubles as a staff directory. The habit is worth keeping; the handles
    are not.
    """
    ref_map: dict[str, str] = {}
    for ref in git_lines(repo, "for-each-ref", "--format=%(refname)"):
        short = ref.split("/", 2)[-1]
        prefix, sep, rest = short.partition("/")
        if not sep:
            continue
        persona = match_handle(prefix, handles)
        if persona:
            ref_map[ref] = ref[:len(ref) - len(short)] + f"{persona}/{rest}"
    return ref_map


def build_message_rules(people: list[dict], handles: dict[str, str],
                        prefixes: set[str], remote: str, world_url: str,
                        owner: str) -> list[tuple[re.Pattern, str]]:
    """What to replace inside commit and tag messages.

    Messages name people — in `Co-authored-by:` trailers, in merge subjects, in
    the branch names those subjects quote — and they name GitHub, which does not
    exist in the world. Longest pattern first, so a full name is replaced before
    a surname inside it can be.
    """
    rules: list[tuple[str, str]] = []
    for person in people:
        syn = person["synthetic"]
        given = syn["display_name"].split()[0]
        for real in person["real"]:
            for email in real["emails"]:
                rules.append((email, syn["email_placeholder"]))
                # A bare local part turns up in prose: "add Kartik to CITATION".
                local = re.sub(r"^\d+\+", "", email.split("@", 1)[0])
                if len(local) >= 4 and local.lower() not in NOT_A_NAME:
                    rules.append((local, given))
            for name in real["names"]:
                if len(name) >= 4:
                    rules.append((name, syn["display_name"]))
                # And so does half of one, in a subject line or a trailer.
                for token in re.split(r"[\s._-]+", name):
                    if len(token) >= 5 and token.lower() not in NOT_A_NAME:
                        rules.append((token, given))
            if real.get("github_login") and len(real["github_login"]) >= 4:
                rules.append((real["github_login"], syn["id"]))

    # Branch prefixes, which is how most real names survive into `git log`.
    for prefix in prefixes:
        persona = match_handle(prefix, handles)
        if persona and persona != prefix:
            rules.append((f"{prefix}/", f"{persona}/"))

    owner_repo = _owner_repo(remote)
    if owner_repo:
        org, _ = owner_repo
        rules.append((f"https://github.com/{org}", f"{world_url}/{owner}"))
        rules.append((f"http://github.com/{org}", f"{world_url}/{owner}"))
        rules.append((f"git@github.com:{org}", f"{world_url}/{owner}"))
        rules.append((f"{org}/", f"{owner}/"))
        rules.append((org, owner))
    rules.append(("github.com", world_url.split("//", 1)[-1]))

    rules.sort(key=lambda r: -len(r[0]))
    return [(re.compile(re.escape(find), re.I), replace) for find, replace in rules]


def _owner_repo(remote: str) -> tuple[str, str] | None:
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", remote or "")
    return (match.group(1), match.group(2)) if match else None


# =============================================================================
# The rewriter
# =============================================================================
_IDENT_RE = re.compile(rb"^(author|committer|tagger) (.*) <([^>]*)> (.*)$")

# Where in a fast-import stream the next `data` payload belongs. A commit
# message must be rewritten; a blob must not, because rewriting one would change
# a tree and break the whole premise.
BLOB, COMMIT_HEADER, COMMIT_BODY, TAG_HEADER, OTHER = range(5)


class Rewriter:
    """Stream `git fast-export` output through, changing only who and where.

    Parsed byte-wise rather than line-wise on purpose. A `data <n>` payload is
    consumed by its exact length, because a commit message is free text that can
    contain a line starting with `author ` — and a line filter that did not know
    that would corrupt the history it was supposed to preserve.
    """

    def __init__(self, authors: dict, ref_map: dict[str, str],
                 message_rules: list[tuple[re.Pattern, str]]):
        self.authors = authors
        self.ref_map = ref_map
        self.rules = message_rules
        self.state = OTHER
        self.unmapped: set[str] = set()
        self.counts = {"commits": 0, "tags": 0, "identities": 0, "messages": 0,
                       "refs": 0}

    def run(self, src, dst) -> None:
        while True:
            line = src.readline()
            if not line:
                break
            if line.startswith(b"data "):
                self._data(line, src, dst)
                continue
            dst.write(self._line(line))

    def _data(self, line: bytes, src, dst) -> None:
        size = int(line[5:].strip())
        payload = src.read(size)
        if self.state in (COMMIT_HEADER, TAG_HEADER):
            rewritten = self._message(payload)
            if rewritten != payload:
                self.counts["messages"] += 1
            dst.write(b"data %d\n" % len(rewritten))
            dst.write(rewritten)
            # Everything after a commit's message is file data, which is never
            # touched.
            self.state = COMMIT_BODY if self.state == COMMIT_HEADER else OTHER
            return
        dst.write(line)
        dst.write(payload)

    def _line(self, line: bytes) -> bytes:
        if line.startswith(b"blob"):
            self.state = BLOB
            return line
        if line.startswith(b"commit "):
            self.state = COMMIT_HEADER
            self.counts["commits"] += 1
            return b"commit " + self._ref(line[7:].strip()) + b"\n"
        if line.startswith(b"tag "):
            self.state = TAG_HEADER
            self.counts["tags"] += 1
            return line
        if line.startswith(b"reset "):
            return b"reset " + self._ref(line[6:].strip()) + b"\n"
        if self.state in (COMMIT_HEADER, TAG_HEADER):
            match = _IDENT_RE.match(line.rstrip(b"\n"))
            if match:
                return self._identity(match)
        return line

    def _ref(self, ref: bytes) -> bytes:
        mapped = self.ref_map.get(ref.decode("utf-8", "replace"))
        if mapped:
            self.counts["refs"] += 1
            return mapped.encode()
        return ref

    def _identity(self, match) -> bytes:
        kind, name, email, when = (match.group(1), match.group(2).decode("utf-8", "replace"),
                                   match.group(3).decode("utf-8", "replace"),
                                   match.group(4))
        person = self.authors.get(f"{name}\x00{email}")
        if person is None:
            self.unmapped.add(f"{name} <{email}>")
            return b"%s %s <%s> %s\n" % (kind, name.encode(), email.encode(), when)
        self.counts["identities"] += 1
        return b"%s %s <%s> %s\n" % (kind, person["name"].encode(),
                                     person["email"].encode(), when)

    def _message(self, payload: bytes) -> bytes:
        text = payload.decode("utf-8", "surrogateescape")
        for pattern, replacement in self.rules:
            text = pattern.sub(replacement.replace("\\", "\\\\"), text)
        return text.encode("utf-8", "surrogateescape")


def rewrite_repo(source: Path, dest: Path, rewriter: Rewriter,
                 verbose: bool = False) -> dict[str, str]:
    """fast-export | rewrite | fast-import, and the mark map that falls out."""
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "--quiet", "--bare", str(dest)], check=True)
    src_marks, dst_marks = dest.parent / "src.marks", dest.parent / "dst.marks"

    exporter = subprocess.Popen(
        ["git", "-C", str(source), "fast-export", "--all",
         "--signed-tags=strip", "--tag-of-filtered-object=rewrite",
         "--reencode=yes", "--use-done-feature",
         f"--export-marks={src_marks}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    importer = subprocess.Popen(
        ["git", "-C", str(dest), "fast-import", "--quiet", "--force",
         f"--export-marks={dst_marks}"],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        rewriter.run(exporter.stdout, importer.stdin)
    finally:
        importer.stdin.close()
    exporter.stdout.close()
    export_err = exporter.stderr.read().decode("utf-8", "replace")
    import_err = importer.stderr.read().decode("utf-8", "replace")
    if exporter.wait() != 0:
        raise RuntimeError(f"fast-export failed: {export_err[:500]}")
    if importer.wait() != 0:
        raise RuntimeError(f"fast-import failed: {import_err[:500]}")

    return commit_map(source, dest, src_marks, dst_marks)


def commit_map(source: Path, dest: Path, src_marks: Path,
               dst_marks: Path) -> dict[str, str]:
    """old commit SHA -> new commit SHA, joined on fast-import mark.

    `ingest_forge.py` cannot create a single pull request without this: every
    `head.sha`, `base.sha` and review anchor in the GitHub payload names a commit
    that no longer exists under that hash.
    """
    def read(path: Path) -> dict[str, str]:
        out = {}
        for line in path.read_text().splitlines():
            mark, _, sha = line.partition(" ")
            out[mark] = sha
        return out

    old, new = read(src_marks), read(dst_marks)
    shared = sorted(set(old) & set(new))
    # Marks cover blobs as well as commits, and a blob's hash is unchanged
    # because its bytes are. Only the commits are wanted here.
    kinds = subprocess.run(
        ["git", "-C", str(source), "cat-file", "--batch-check"],
        input="".join(f"{old[m]}\n" for m in shared).encode(),
        capture_output=True).stdout.decode().splitlines()
    return {old[mark]: new[mark]
            for mark, kind in zip(shared, kinds)
            if kind.split()[1:2] == ["commit"]}


# =============================================================================
# Checks
# =============================================================================
def check_trees(source: Path, dest: Path, mapping: dict[str, str]) -> list[str]:
    """Every rewritten commit must point at the identical tree.

    This is the whole claim of the exercise in one assertion: if the trees match,
    not one byte of anybody's code changed, whatever happened to the names.
    """
    def trees(repo: Path, shas: list[str]) -> list[str]:
        out = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "--batch-check=%(objectname)"],
            input="".join(f"{s}^{{tree}}\n" for s in shas).encode(),
            capture_output=True).stdout.decode().split()
        return out

    olds = sorted(mapping)
    news = [mapping[o] for o in olds]
    before, after = trees(source, olds), trees(dest, news)
    if len(before) != len(olds) or len(after) != len(news):
        return [f"could not resolve every tree ({len(before)}/{len(olds)} before, "
                f"{len(after)}/{len(news)} after)"]
    return [f"{old[:12]} -> {mapping[old][:12]}: tree {b[:12]} became {a[:12]}"
            for old, b, a in zip(olds, before, after) if b != a]


def check_refs(source: Path, dest: Path, ref_map: dict[str, str]) -> list[str]:
    def refs(repo: Path) -> set[str]:
        return {r for r in git_lines(repo, "for-each-ref", "--format=%(refname)")
                if not r.startswith("refs/remotes/")}

    expected = {ref_map.get(r, r) for r in refs(source)}
    got = refs(dest)
    problems = []
    for missing in sorted(expected - got):
        problems.append(f"ref {missing} did not survive the rewrite")
    for extra in sorted(got - expected):
        problems.append(f"ref {extra} appeared from nowhere")
    return problems


def check_no_leaks(repo: Path, patterns: list[str]) -> list[str]:
    """No real name, address or handle anywhere a person can see it."""
    haystacks = {
        "commit metadata and messages": "\n".join(git_lines(
            repo, "log", "--all", "--format=%an%n%ae%n%cn%n%ce%n%B")),
        "branch and tag names": "\n".join(git_lines(
            repo, "for-each-ref", "--format=%(refname)")),
    }
    hits = []
    for where, text in haystacks.items():
        for pattern in patterns:
            match = re.search(re.escape(pattern), text, re.I)
            if match:
                start = max(0, match.start() - 60)
                hits.append(f"{where}: {pattern!r} in "
                            f"...{text[start:match.end() + 60]}...")
    return hits


def leak_patterns(people: list[dict], remote: str) -> list[str]:
    """The real identifiers, and only those worth matching.

    Names are split so a bare surname is caught; logins and addresses are matched
    whole, because a fragment of `copilot-pull-request-reviewer[bot]` is a word
    like "request" that appears in half the commit messages in the project.
    """
    stop = {"github", "noreply", "users", "code", "data", "test", "root", "user"}
    patterns: set[str] = set()
    for person in people:
        for real in person["real"]:
            for email in real["emails"]:
                patterns.add(email)
                local = re.sub(r"^\d+\+", "", email.split("@", 1)[0])
                if len(local) >= 4 and local.lower() not in stop:
                    patterns.add(local)
            if real.get("github_login") and len(real["github_login"]) >= 4:
                patterns.add(real["github_login"])
            for name in real["names"]:
                if len(name) < 4:
                    continue
                patterns.add(name)
                for token in re.split(r"[\s._-]+", name):
                    if len(token) >= 5 and token.lower() not in stop:
                        patterns.add(token)
    owner_repo = _owner_repo(remote)
    if owner_repo:
        patterns.add(owner_repo[0])
    return sorted(patterns)


# =============================================================================
# Export
# =============================================================================
def do_export(args, world: wl.World) -> int:
    source = args.source_repo.resolve()
    wl.heading("Reading the real repository")
    facts = preflight(source)
    wl.ok(f"{source} — {facts['commits']} commits, HEAD {facts['head'][:12]}, clean")
    wl.info(f"origin {facts['remote'] or '(none)'} — recorded, never written to")

    grounding = json.loads(args.grounding.read_text(encoding="utf-8"))
    people = grounding["people"]
    for person in people:
        person["synthetic"]["email_placeholder"] = (
            f"{person['synthetic']['id']}@{world.domain}")

    tmp = Path(tempfile.mkdtemp(prefix="ingest-history-"))
    try:
        wl.heading("Rewriting")
        work = mirror(source, tmp)
        wl.info(f"mirrored to {work} with no remote — the source is now untouchable")

        authors, unmapped = build_author_map(signatures(work), people, world.domain)
        if unmapped:
            raise SystemExit(
                "these git signatures map to nobody in company_grounding.json, so their\n"
                "  commits would keep a real name:\n    " + "\n    ".join(unmapped) +
                "\n\n  Re-run data_gen/phase1_company_grounding.py: every identity in the\n"
                "  repository needs a persona, including bots and one-commit contributors.")
        wl.ok(f"{len(authors)} git signatures mapped to "
              f"{len({a['persona'] for a in authors.values()})} personas")

        handles = build_handles(people)
        prefixes = branch_prefixes(work)
        ref_map = build_ref_map(work, handles)
        if ref_map:
            wl.ok(f"{len(ref_map)} branches carry a personal handle, renamed: " +
                  ", ".join(f"{k.split('/', 2)[-1]} -> {v.split('/', 2)[-1]}"
                            for k, v in list(ref_map.items())[:3]) +
                  ("…" if len(ref_map) > 3 else ""))

        rules = build_message_rules(people, handles, prefixes, facts["remote"],
                                    world.url("git"), world.admin_user)
        rewriter = Rewriter(authors, ref_map, rules)
        dest = tmp / "rewritten.git"
        mapping = rewrite_repo(work, dest, rewriter, args.verbose)
        branches = git_lines(dest, "for-each-ref", "--format=%(refname)", "refs/heads")
        tags = git_lines(dest, "for-each-ref", "--format=%(refname)", "refs/tags")
        exported = int(git(dest, "rev-list", "--all", "--count"))
        wl.ok(f"{exported} commits, {len(branches)} branches, {len(tags)} tags, "
              f"{rewriter.counts['identities']} signatures replaced, "
              f"{rewriter.counts['messages']} messages edited")
        if exported != facts["commits"]:
            raise SystemExit(
                f"the source has {facts['commits']} commits but only {exported} were\n"
                f"  exported. Every commit reachable from any ref must survive; nothing\n"
                "  was written.")

        wl.heading("Checks")
        problems = check_trees(work, dest, mapping)
        if problems:
            for problem in problems[:10]:
                wl.warn(problem)
            raise SystemExit(f"{len(problems)} commit(s) changed their tree. The rewrite is "
                             "supposed to touch identities only; nothing was written.")
        wl.ok(f"all {len(mapping)} commits point at an identical tree — no code changed")

        problems = check_refs(work, dest, ref_map)
        if problems:
            for problem in problems[:10]:
                wl.warn(problem)
            raise SystemExit(f"{len(problems)} ref problem(s); nothing was written")
        wl.ok(f"{len(git_lines(dest, 'for-each-ref', '--format=%(refname)'))} refs, "
              "the same set the source has")

        patterns = leak_patterns(people, facts["remote"])
        leaks = check_no_leaks(dest, patterns)
        if leaks:
            for leak in leaks[:15]:
                wl.warn(leak)
            raise SystemExit(
                f"{len(leaks)} real identifier(s) survive in the rewritten history. Nothing\n"
                "  was written. Every one is visible in `git log` inside the world.")
        wl.ok(f"no real names, addresses or handles in any commit, branch or tag "
              f"({len(patterns)} patterns checked)")

        wl.heading("Writing")
        out_dir = args.data_dir / "history"
        out_dir.mkdir(parents=True, exist_ok=True)
        bundle = out_dir / BUNDLE_NAME
        if args.dry_run:
            wl.dry(f"would write {bundle} and {out_dir / MANIFEST_NAME}")
            return 0
        subprocess.run(["git", "-C", str(dest), "bundle", "create", str(bundle), "--all"],
                       check=True, capture_output=True)
        wl.ok(f"{bundle} ({human_bytes(bundle.stat().st_size)})")

        manifest = {
            "schema_version": 1,
            "generator": "scripts/ingest_history.py --export",
            "generated_at": wl.to_iso(_now()),
            "repo": args.repo,
            "domain": world.domain,
            "source": {"remote": facts["remote"], "head": facts["head"],
                       "commits": facts["commits"]},
            "counts": {"commits": exported, "branches": len(branches),
                       "tags": len(tags), "signatures": len(authors),
                       "identities_replaced": rewriter.counts["identities"],
                       "messages_edited": rewriter.counts["messages"],
                       "refs_renamed": rewriter.counts["refs"],
                       "mapped_commits": len(mapping)},
            "author_map": authors,
            "ref_map": ref_map,
            "default_branch": _default_branch(dest),
            "head": _head_of(dest, _default_branch(dest)),
            "commit_map": mapping,
        }
        path = out_dir / MANIFEST_NAME
        path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        wl.ok(f"{path} ({human_bytes(path.stat().st_size)}) — "
              f"{len(mapping)} commit SHAs for ingest_forge.py")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _now():
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def _default_branch(repo: Path) -> str:
    for candidate in ("main", "master"):
        if git(repo, "rev-parse", "--verify", f"refs/heads/{candidate}",
               check=False):
            return candidate
    refs = git_lines(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    return refs[0] if refs else "main"


def _head_of(repo: Path, branch: str) -> str:
    return git(repo, "rev-parse", f"refs/heads/{branch}", check=False)


# =============================================================================
# Ingest
# =============================================================================
def push_target(world: wl.World, token: str, repo: str) -> str:
    port = "" if world.http_port == 80 else f":{world.http_port}"
    url = (f"http://{world.admin_user}:{token}@git.{world.domain}{port}"
           f"/{world.admin_user}/{repo}.git")
    if FORBIDDEN_PUSH.search(url):
        raise SystemExit(f"refusing to push to {FORBIDDEN_PUSH.pattern} — "
                         f"the target resolved to {url.replace(token, '***')}")
    return url


def create_accounts(world: wl.World, identities: wl.Identities, token: str,
                    dry_run: bool) -> int:
    """One Gitea account per persona, matched on email.

    Without these, every commit renders as unlinked plain text: no avatar, no
    author link, no contributor graph, and `ingest_forge.py` has no user to
    attribute an issue to.
    """
    wanted = [p.resolved(world) for p in identities if not p.is_admin]
    if dry_run:
        # A dry run opens no socket at all, not even to ask what already exists:
        # the point of it is that it works against a world that is not running.
        for persona in wanted:
            wl.dry(f"would create gitea user {persona.gitea_username} "
                   f"<{persona.email}> if absent")
        return len(wanted)

    # Gitea answers a short password with "PasswordIsRequired", which reads as a
    # missing field and sends you hunting through the request body. Say what is
    # actually wrong instead.
    short = sorted({p.gitea_username for p in wanted
                    if len(p.password or "") < GITEA_MIN_PASSWORD})
    if short:
        raise SystemExit(
            f"the password for {len(short)} persona(s) is shorter than Gitea's "
            f"{GITEA_MIN_PASSWORD}-character minimum, so their accounts cannot be "
            f"created:\n    " + ", ".join(short[:8]) +
            "\n\n  Set MAIL_PERSONA_PASSWORD in .env to something longer. The same value "
            "logs\n  a persona into git, mail and the wiki, so change it in one place.")

    sess = wl.session(world)
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    made = 0
    for persona in wanted:
        username = persona.gitea_username
        got = sess.get(world.url("git", f"/api/v1/users/{username}"),
                       headers=headers, timeout=30)
        if got.status_code == 200:
            continue
        resp = sess.post(
            world.url("git", "/api/v1/admin/users"), headers=headers,
            json={"username": username, "email": persona.email,
                  "full_name": persona.display_name,
                  "password": persona.password,
                  "must_change_password": False},
            timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"could not create gitea user {username!r} "
                               f"({resp.status_code}): {resp.text[:300]}")
        made += 1
    return made


def reseed_ci(repo_dir: Path, world: wl.World, token: str, repo: str) -> bool:
    """Put the CI workflow back on top of the pushed history.

    `world/bootstrap/22-curator.sh` adds `.gitea/workflows/ci.yml` above its
    baseline commit. The real history has no `.gitea/` directory, so the
    force-push takes the workflow with it and the runner simply stops firing —
    with nothing anywhere to say why.
    """
    template = next((p for p in CI_TEMPLATES if p.exists()), None)
    if template is None:
        wl.warn("no CI workflow template found in "
                f"{' or '.join(str(p) for p in CI_TEMPLATES)}; CI not reseeded")
        return False
    work = repo_dir / "ci-work"
    subprocess.run(["git", "clone", "--quiet", "--branch", _default_branch(repo_dir),
                    str(repo_dir), str(work)], check=True, capture_output=True)
    target = work / CI_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    git(work, "add", CI_PATH)
    git(work, "-c", f"user.name={world.admin_user}",
        "-c", f"user.email={world.admin_email}",
        "commit", "--quiet", "-m", "ci: run the test suite on every push")
    # The clone already has an `origin` pointing at the scratch mirror it came
    # from; the workflow needs to land in Gitea instead.
    git(work, "remote", "remove", "origin", check=False)
    git(work, "remote", "add", "origin", push_target(world, token, repo))
    git(work, "push", "--quiet", "origin", f"HEAD:{_default_branch(repo_dir)}")
    return True


def wait_until_scanned(world: wl.World, token: str, repo: str) -> None:
    """Gitea clears `is_empty` after the push returns, not during it.

    An "empty" repository is never scanned for workflows, so a push that lands
    while the flag is still set leaves CI permanently silent. The bootstrap
    learned this the hard way (22-curator.sh:49-71); so does this.
    """
    import time
    sess = wl.session(world)
    headers = {"Authorization": f"token {token}"}
    for _ in range(60):
        resp = sess.get(world.url("git", f"/api/v1/repos/{world.admin_user}/{repo}"),
                        headers=headers, timeout=15)
        if resp.status_code == 200 and not resp.json().get("empty", True):
            return
        time.sleep(1)
    wl.warn(f"{repo} still reports empty after 60s; workflows may not be scanned")


def do_ingest(args, world: wl.World, identities: wl.Identities) -> int:
    history_dir = args.data_dir / "history"
    bundle = args.bundle or history_dir / BUNDLE_NAME
    manifest_path = history_dir / MANIFEST_NAME
    for path in (bundle, manifest_path):
        if not path.exists():
            raise SystemExit(
                f"{path} does not exist. Build it on the host first, where the real\n"
                "  clone lives:\n\n"
                "    python3 scripts/ingest_history.py --export\n")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    wl.heading("History")
    wl.ok(f"{bundle} ({human_bytes(bundle.stat().st_size)}) — "
          f"{manifest['counts']['commits']} commits, "
          f"{manifest['counts']['branches']} branches, "
          f"{manifest['counts']['tags']} tags")

    token = args.token or world.env.get("GITEA_API_TOKEN", "")
    if not token and not args.dry_run:
        raise SystemExit("no Gitea token: set GITEA_API_TOKEN or run inside the world, "
                         "where /etc/sweworld/gitea-token exists")

    work_root = Path(tempfile.mkdtemp(prefix="ingest-history-"))
    try:
        repo_dir = work_root / args.repo
        subprocess.run(["git", "clone", "--quiet", "--mirror", str(bundle), str(repo_dir)],
                       check=True, capture_output=True)
        git(repo_dir, "remote", "remove", "origin", check=False)
        count = int(git(repo_dir, "rev-list", "--all", "--count"))
        if count != manifest["counts"]["commits"]:
            raise SystemExit(f"the bundle holds {count} commits but the manifest says "
                             f"{manifest['counts']['commits']}; they are out of step")
        wl.ok(f"unbundled {count} commits into a scratch mirror")

        if args.create_accounts:
            made = create_accounts(world, identities, token, args.dry_run)
            if not args.dry_run:
                wl.ok(f"{made} gitea account(s) created, "
                      f"{len(identities) - 1 - made} already present")

        if args.dry_run:
            wl.dry(f"would create gitea repo {world.admin_user}/{args.repo} if absent")
            wl.dry(f"would force-push {count} commits and "
                   f"{manifest['counts']['tags']} tags")
            wl.dry(f"would set the default branch to {manifest['default_branch']}")
            if args.ci_reseed:
                wl.dry(f"would re-add {CI_PATH} on top")
            wl.summarise(True, [f"{count} commit(s) replayed, 0 pushed"])
            return 0

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import ingest_git

        ingest_git.ensure_gitea_repo(world, args.repo, token)
        git(repo_dir, "remote", "add", "origin", push_target(world, token, args.repo))
        git(repo_dir, "push", "--force", "--prune", "origin",
            "refs/heads/*:refs/heads/*", "refs/tags/*:refs/tags/*")
        wl.ok(f"pushed {count} commits to {world.url('git')}/"
              f"{world.admin_user}/{args.repo}")

        ingest_git.set_default_branch(world, args.repo, manifest["default_branch"], token)
        wait_until_scanned(world, token, args.repo)

        if args.ci_reseed and reseed_ci(repo_dir, world, token, args.repo):
            wl.ok(f"{CI_PATH} re-added on {manifest['default_branch']} — "
                  "the force-push had removed it")

        wl.summarise(False, [
            f"{count} commit(s) pushed",
            f"{manifest['counts']['tags']} tag(s)",
            f"default branch {manifest['default_branch']}",
        ])
        return 0
    finally:
        shutil.rmtree(work_root, ignore_errors=True)


# =============================================================================
# main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--export", action="store_true",
                        help="rewrite from --source-repo and write the bundle")
    parser.add_argument("--source-repo", type=Path, default=DEFAULT_SOURCE,
                        help=f"the real clone, read only (default: {DEFAULT_SOURCE})")
    parser.add_argument("--grounding", type=Path, default=DEFAULT_GROUNDING,
                        help="company_grounding.json, for the persona map")
    parser.add_argument("--bundle", type=Path, default=None,
                        help="bundle to ingest (default: <data-dir>/history/curator.bundle)")
    parser.add_argument("--repo", default="curator", help="repository name in Gitea")
    parser.add_argument("--token", default=None, help="Gitea API token")
    parser.add_argument("--no-create-accounts", dest="create_accounts",
                        action="store_false",
                        help="do not create a Gitea user per persona")
    parser.add_argument("--no-ci-reseed", dest="ci_reseed", action="store_false",
                        help="do not re-add .gitea/workflows/ci.yml after the push")
    args = parser.parse_args(argv)

    if args.export:
        wl.validate_common_args(args)
        world = wl.World(env=wl.load_env(args.env_file))
        if not args.grounding.exists():
            raise SystemExit(
                f"{args.grounding} does not exist. The persona map comes from Phase 1:\n\n"
                "    data_gen/.venv/bin/python data_gen/phase1_company_grounding.py\n")
        return do_export(args, world)

    world, identities, problems = wl.setup(args)
    problems.raise_if_any()
    return do_ingest(args, world, identities)


if __name__ == "__main__":
    sys.exit(main())
