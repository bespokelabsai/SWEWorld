#!/usr/bin/env python3
"""Put a finished phase-4 run into `data/`, in the shape the ingest reads.

`data/` is the handoff between the two halves of this repo: `data_gen/` makes
the content, `world/` and `scripts/` build the container that serves it. This
script is that handoff, and it is meant to be run again — a regenerated corpus,
or a subtle change to one page, should be able to replace what is there without
anybody reasoning about which files to delete first.

So it is a REPLACE, not a merge. Everything this script owns is removed before
it writes, because a merge leaves the previous corpus's pages sitting beside
the new one, indistinguishable, and the ingest would happily import both.

What it does NOT own, and never touches:

  identities.yaml   written by phase 1 directly into data/
  channels.yaml     likewise
  commits.jsonl     nothing generates it; the world's git history arrives
                    through data/history/ and ingest_history.py, and an empty
                    commits.jsonl is a warning rather than an error
  history/          built on the HOST by `make history`, from the real curator
                    checkout — regenerating it is a separate job
  schemas/          hand-written; the contract, not an output

Nothing here talks to a running world. It copies and it validates the shape;
`make bake-image` does the ingesting.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

# What this script owns in `data/`. Everything listed is deleted before the
# copy, so a stale page from a previous corpus cannot survive into a new one.
OWNED = ("docs", "emails", "messages.jsonl", "comments.jsonl")

# The frontmatter `ingest_docs.py` accepts. Anything else fails the ingest, and
# finding that out during a bake is finding it out ten minutes too late.
DOC_REQUIRED = {"title", "author", "created_at"}
DOC_OPTIONAL = {"updated_at", "publish", "icon", "full_width", "tags"}


def latest_run(build: Path, name: str) -> Path:
    """The run to install: `--run NAME`, or whatever `latest` points at."""
    if name and name != "latest":
        run = build / "phase4" / "runs" / name
        if not run.is_dir():
            rl.fail(f"no run called {name!r} at {run}")
        return run
    link = build / "phase4" / "latest"
    if not link.exists():
        rl.fail(f"{link} does not exist — name a run with --run")
    return link.resolve()


def check_docs(docs: Path, problems: list[str]) -> tuple[int, int]:
    """Every page parses and carries the frontmatter the ingest requires."""
    manifest = docs / "collections.yaml"
    if not manifest.exists():
        problems.append(f"{manifest} missing — ingest_docs.py errors without it")
    shelves = {d.name for d in docs.iterdir() if d.is_dir()}
    listed = set()
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("- dir:"):
                listed.add(line.split(":", 1)[1].strip())
    for gone in sorted(listed - shelves):
        problems.append(f"collections.yaml lists {gone!r}, which is not a directory")
    for extra in sorted(shelves - listed):
        problems.append(f"{extra}/ has no entry in collections.yaml")

    pages = sorted(docs.glob("*/*.md"))
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            problems.append(f"{page.name}: no frontmatter block")
            continue
        head = text.split("---\n", 2)[1]
        keys = {line.split(":", 1)[0].strip()
                for line in head.splitlines() if ":" in line}
        for want in sorted(DOC_REQUIRED - keys):
            problems.append(f"{page.name}: frontmatter has no {want!r}")
        for odd in sorted(keys - DOC_REQUIRED - DOC_OPTIONAL):
            problems.append(f"{page.name}: frontmatter key {odd!r} is not allowed")
    return len(pages), len(listed)


def check_mail(emails: Path, problems: list[str]) -> int:
    """Every `.eml` is indexed and every indexed path exists.

    Both directions on purpose: `ingest_mail.py` rejects an unindexed file
    under the tree as firmly as it rejects an index line pointing at nothing.
    """
    index = emails / "index.jsonl"
    if not index.exists():
        problems.append(f"{index} missing")
        return 0
    listed, rows = set(), 0
    seen_paths: dict[str, int] = {}
    for n, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"index.jsonl:{n}: {exc}")
            continue
        rows += 1
        for want in ("path", "mailbox", "date"):
            if not row.get(want):
                problems.append(f"index.jsonl:{n}: no {want!r}")
        listed.add(row.get("path", ""))
        seen_paths[row.get("path", "")] = seen_paths.get(row.get("path", ""), 0) + 1
        if not (emails / row.get("path", "")).exists():
            problems.append(f"index.jsonl:{n}: {row.get('path')} is not on disk")
    on_disk = {str(p.relative_to(emails)) for p in emails.rglob("*.eml")}
    for orphan in sorted(on_disk - listed)[:10]:
        problems.append(f"{orphan} is on disk but not in index.jsonl")
    # And the other way round: one path indexed twice. `Mail.send` appends to
    # index.jsonl while overwriting the .eml, so a re-simulated day leaves the
    # same file indexed once per run — and `ingest_mail.py` reads that as the
    # same Message-ID arriving twice in one mailbox folder, which it rejects.
    twice = sorted(p for p, n in seen_paths.items() if n > 1)
    for path in twice[:10]:
        problems.append(f"{path} appears {seen_paths[path]} times in index.jsonl")
    if len(twice) > 10:
        problems.append(f"... and {len(twice) - 10} more duplicated path(s)")
    return rows


def check_jsonl(path: Path, required: tuple[str, ...],
                problems: list[str]) -> int:
    """One object per line, each carrying the fields the ingest needs."""
    if not path.exists():
        return 0
    rows = 0
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}:{n}: {exc}")
            continue
        rows += 1
        for want in required:
            if row.get(want) in (None, ""):
                problems.append(f"{path.name}:{n}: no {want!r}")
    return rows


def check_comments(data: Path, problems: list[str]) -> int:
    """Comments resolve to real pages and to parents that exist.

    `ingest_comments.py` rejects a `doc` it cannot place and a `reply_to`
    naming a comment that is not there — and the second is easy to produce,
    because the plan's reply names an id the store has to have used.
    """
    path = data / "comments.jsonl"
    rows = check_jsonl(path, ("doc", "author", "created_at", "text"), problems)
    if not path.exists():
        return 0
    seen, parents = set(), []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        doc = row.get("doc", "")
        if doc and not (data / "docs" / doc).exists():
            problems.append(f"comments.jsonl: doc {doc!r} is not a page in docs/")
        if row.get("id"):
            seen.add(row["id"])
        if row.get("reply_to"):
            parents.append((row.get("id", "?"), row["reply_to"]))
        if row.get("archived") and row.get("reply_to"):
            problems.append(
                f"comments.jsonl: {row.get('id')} is archived AND a reply — "
                "BookStack archives a thread by its root, and the ingest "
                "rejects the flag on a reply")
    for child, parent in parents:
        if parent not in seen:
            problems.append(
                f"comments.jsonl: {child} replies to {parent}, which is not here")
    return rows


def dedupe_index(index: Path) -> int:
    """One row per file in `index.jsonl`, keeping the newest.

    The index is append-only and the `.eml` beside it is overwritten, so a day
    that gets simulated twice leaves two rows pointing at one file. The last
    row is the one that describes what is actually on disk.
    """
    if not index.exists():
        return 0
    keep: dict[str, str] = {}
    order: list[str] = []
    head = []
    for line in index.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            head.append(line)
            continue
        path = json.loads(stripped).get("path", "")
        if path not in keep:
            order.append(path)
        keep[path] = line
    total = sum(1 for line in index.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#"))
    index.write_text("\n".join(head + [keep[p] for p in order]) + "\n",
                     encoding="utf-8")
    return total - len(order)


def install(run: Path, data: Path, apply: bool) -> int:
    rl.heading(f"{run.name} -> {data}")
    copied, skipped = [], []

    for name in OWNED:
        src = run / name
        if not src.exists():
            skipped.append(name)
            continue
        dst = data / name
        if src.is_dir():
            count = sum(1 for p in src.rglob("*") if p.is_file())
            copied.append((name, f"{count} file(s)"))
            if apply:
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                if name == "emails":
                    dropped = dedupe_index(dst / "index.jsonl")
                    if dropped:
                        rl.warn(f"  dropped {dropped} duplicate index row(s) — "
                                "a re-simulated day re-sends a mail and the "
                                "index is append-only, so the same file was "
                                "listed once per run")
        else:
            lines = sum(1 for line in src.open(encoding="utf-8")
                        if line.strip() and not line.startswith("#"))
            copied.append((name, f"{lines} row(s)"))
            if apply:
                shutil.copy2(src, dst)

    for name, what in copied:
        rl.ok(f"  data/{name} — {what}")
    for name in skipped:
        rl.warn(f"  data/{name} NOT written — this run produced none, so "
                "whatever is in data/ stays, placeholder included")

    if not apply:
        rl.warn("--dry-run: data/ was not touched")
        return 0

    problems: list[str] = []
    pages, shelves = check_docs(data / "docs", problems)
    mails = check_mail(data / "emails", problems)
    msgs = check_jsonl(data / "messages.jsonl",
                       ("channel", "author", "created_at"), problems)
    comments = check_comments(data, problems)

    rl.heading("What the ingest will find")
    rl.info(f"  {pages} page(s) across {shelves} collection(s)")
    rl.info(f"  {mails} mail file(s)")
    rl.info(f"  {msgs} chat message(s)")
    rl.info(f"  {comments} page comment(s)")
    for name in ("identities.yaml", "channels.yaml", "commits.jsonl"):
        got = data / name
        rl.info(f"  {name}: {'present' if got.exists() else 'MISSING'} "
                "(not written by this script)")
    hist = data / "history"
    rl.info(f"  history/: {'present' if hist.exists() else 'MISSING'} "
            "(built on the host by `make history`)")

    if problems:
        for one in problems[:25]:
            rl.warn(one)
        if len(problems) > 25:
            rl.warn(f"... and {len(problems) - 25} more")
        rl.fail(f"{len(problems)} problem(s) — the ingest would reject this. "
                "Nothing was reverted; fix the corpus and run again.")
    rl.ok(f"data/ is ready. Ingest with `make bake-image`, which runs the "
          "seven scripts in order — docs before comments, because comments "
          "need the page ids docs leaves in .docs-manifest.json.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Install a finished phase-4 run into data/ for ingesting.")
    parser.add_argument("--run", default="latest",
                        help="run name under build/phase4/runs/, or 'latest'")
    parser.add_argument("--build", type=Path, default=rl.DEFAULT_BUILD_DIR)
    parser.add_argument("--data-dir", type=Path,
                        default=rl.REPO_ROOT / "data")
    parser.add_argument("--dry-run", action="store_true",
                        help="say what would be written and change nothing")
    args = parser.parse_args(argv)

    run = latest_run(args.build, args.run)
    if not args.data_dir.is_dir():
        rl.fail(f"{args.data_dir} does not exist")
    return install(run, args.data_dir, apply=not args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
