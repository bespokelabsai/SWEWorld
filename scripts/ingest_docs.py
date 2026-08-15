#!/usr/bin/env python3
"""Create BookStack books, chapters and pages from a directory of markdown.

Input
-----
data/identities.yaml           the persona list
data/docs/collections.yaml     one entry per top-level directory
data/docs/**/*.md              one file per document, YAML frontmatter + body

Layout mirrors the document tree; a directory sharing a stem with a sibling
.md file holds that document's children:

    data/docs/
      collections.yaml
      engineering/                  -> Book "Engineering"
        onboarding.md               -> Page in the book
        architecture.md             -> Chapter "Architecture Overview"
        architecture/               -> pages inside that chapter
          storage-layer.md          -> Page

Mapping to BookStack's model
----------------------------
BookStack is Shelf > Book > Chapter > Page and is only two levels deep below a
book, while the source tree allows arbitrary nesting. So:

  * a collection directory            -> Book
  * a .md with NO children            -> Page in the book
  * a .md WITH children               -> Chapter, plus a Page holding its own
                                         body so no content is lost
  * anything nested deeper            -> flattened into that chapter, with a
                                         warning naming the file

Authorship and dates
--------------------
BookStack's API has no created_at or author field — a page belongs to whoever
owns the token, stamped now. Unlike Outline, though, we own the database, so
this script creates entities through the API (which handles slugs, revisions
and the search index correctly) and then corrects `created_at`, `updated_at`,
`created_by`, `updated_by` and `owned_by` directly in the `entities` table.

Personas are created as BookStack users on demand so attribution has something
to point at. Use --single-author to skip that and leave everything owned by the
admin.

--dry-run resolves the whole tree, validates it and prints the plan without
touching the API or the database.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worldlib as wl  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install -r scripts/requirements.txt")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")

COLLECTION_REQUIRED = ("dir", "name")
COLLECTION_OPTIONAL = ("description", "icon", "color", "permission")
DOC_REQUIRED = ("title", "author", "created_at")
DOC_OPTIONAL = ("updated_at", "publish", "icon", "full_width", "tags")

MYSQL = ["mariadb", "--protocol=socket", "--socket=/run/mysqld/mysqld.sock",
         "-N", "-B", "-D", "bookstack", "-e"]


@dataclass
class DocNode:
    path: Path
    rel: str
    title: str
    author: str
    created_at: Any
    body: str
    collection_dir: str = ""
    parent_rel: str | None = None
    depth: int = 0
    children: list["DocNode"] = field(default_factory=list)
    entity_id: int | None = None
    entity_type: str = "page"


@dataclass
class BookSpec:
    dir: str
    name: str
    description: str = ""
    book_id: int | None = None


# =============================================================================
# Parsing
# =============================================================================
def parse_frontmatter(path: Path, problems: wl.Problems) -> tuple[dict, str] | None:
    match = FRONTMATTER_RE.match(path.read_text())
    if not match:
        problems.error(
            "missing YAML frontmatter — the file must start with a '---' block", path, 1)
        return None
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        problems.error(f"invalid YAML frontmatter: {exc}", path, 1)
        return None
    if not isinstance(meta, dict):
        problems.error("frontmatter must be a mapping", path, 1)
        return None
    return meta, match.group(2)


def load_collections(path: Path, docs_dir: Path,
                     problems: wl.Problems) -> dict[str, BookSpec]:
    """Parse collections.yaml — each entry becomes a BookStack book."""
    if not path.exists():
        problems.error("collections.yaml not found", path)
        return {}
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        problems.error(f"invalid YAML: {exc}", path)
        return {}

    wl.check_keys(raw, required=("version", "collections"), problems=problems, path=path)
    if raw.get("version") != 1:
        problems.error(f"version must be 1, got {raw.get('version')!r}", path)

    entries = raw.get("collections")
    if not isinstance(entries, list) or not entries:
        problems.error("collections must be a non-empty list", path)
        return {}

    specs: dict[str, BookSpec] = {}
    for index, entry in enumerate(entries):
        context = f"collections[{index}]"
        if not isinstance(entry, dict):
            problems.error(f"{context} must be a mapping", path)
            continue
        wl.check_keys(entry, required=COLLECTION_REQUIRED, optional=COLLECTION_OPTIONAL,
                      problems=problems, path=path, context=context)
        directory = entry.get("dir")
        if not isinstance(directory, str):
            continue
        if not (docs_dir / directory).is_dir():
            problems.error(f"{context}: dir {directory!r} does not exist", path)
        if directory in specs:
            problems.error(f"{context}: duplicate dir {directory!r}", path)
            continue
        specs[directory] = BookSpec(dir=directory, name=entry.get("name", ""),
                                    description=entry.get("description", "") or "")
    return specs


def load_documents(docs_dir: Path, collections: dict[str, BookSpec],
                   identities: wl.Identities, problems: wl.Problems) -> list[DocNode]:
    nodes: dict[str, DocNode] = {}

    for md_path in sorted(docs_dir.rglob("*.md")):
        rel = md_path.relative_to(docs_dir).as_posix()
        parts = Path(rel).parts
        if len(parts) < 2:
            problems.error(
                "documents must live inside a collection directory", md_path)
            continue
        collection_dir = parts[0]
        if collection_dir not in collections:
            problems.error(
                f"directory {collection_dir!r} has no entry in collections.yaml — "
                "unlisted directories are an error, not an implicit book", md_path)

        parsed = parse_frontmatter(md_path, problems)
        if parsed is None:
            continue
        meta, body = parsed
        wl.check_keys(meta, required=DOC_REQUIRED, optional=DOC_OPTIONAL,
                      problems=problems, path=md_path, line=1)
        identities.require(meta.get("author"), problems, md_path, 1, "author")
        created = wl.parse_ts(meta.get("created_at"), path=md_path, line=1,
                              problems=problems, field_name="created_at")

        parent_rel = Path(*parts[:-1]).as_posix() + ".md" if len(parts) > 2 else None
        nodes[rel] = DocNode(
            path=md_path, rel=rel, title=str(meta.get("title", "")),
            author=str(meta.get("author", "")), created_at=created, body=body,
            collection_dir=collection_dir, parent_rel=parent_rel,
            depth=len(parts) - 2,
        )

    for node in nodes.values():
        if node.parent_rel and node.parent_rel not in nodes:
            problems.error(
                f"parent document {node.parent_rel!r} does not exist — a child "
                "directory needs a sibling .md file of the same name", node.path)
        elif node.parent_rel:
            nodes[node.parent_rel].children.append(node)

    # BookStack is only Book > Chapter > Page. Deeper trees are flattened, and
    # that has to be visible rather than silently reshaping someone's content.
    for node in nodes.values():
        if node.depth > 1:
            problems.warn(
                f"nested {node.depth} levels deep; BookStack has no sub-chapters, "
                "so it will be flattened into its chapter", node.path)

    for node in nodes.values():
        node.entity_type = "chapter" if node.children else "page"

    for node in nodes.values():
        for _, target in MD_LINK_RE.findall(node.body):
            if target.startswith(("http://", "https://", "#")):
                continue
            if not any(c in nodes for c in _link_candidates(node.rel, target)):
                problems.warn(
                    f"cross-link {target!r} does not resolve; left as written", node.path)

    return list(nodes.values())


def _link_candidates(from_rel: str, target: str) -> list[str]:
    if target.startswith("/"):
        return [target.lstrip("/")]
    relative = os.path.normpath(str(Path(from_rel).parent / target)).replace(os.sep, "/")
    from_root = os.path.normpath(target).replace(os.sep, "/")
    return [relative] if relative == from_root else [relative, from_root]


# =============================================================================
# BookStack API
# =============================================================================
class BookStack:
    """Minimal BookStack API client.

    Auth is a single header: `Authorization: Token <id>:<secret>`.
    """

    def __init__(self, world: wl.World, token: str):
        self.world = world
        self.sess = wl.session(world)
        self.headers = {"Authorization": f"Token {token}",
                        "Content-Type": "application/json"}

    def post(self, endpoint: str, payload: dict) -> dict:
        resp = self.sess.post(self.world.url("docs", f"/api/{endpoint}"),
                              json=payload, headers=self.headers, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"POST {endpoint} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def get(self, endpoint: str) -> dict:
        resp = self.sess.get(self.world.url("docs", f"/api/{endpoint}"),
                             headers=self.headers, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"GET {endpoint} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()


def sql(statement: str) -> str:
    """Run one statement against the BookStack database (in-container only)."""
    proc = subprocess.run(MYSQL + [statement], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"mariadb failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def ensure_bookstack_user(persona: wl.Persona) -> int:
    """Return the BookStack user id for a persona, creating the row if needed.

    Done in SQL rather than through the API because the API requires a
    password-policy dance for a user that will never log in — these accounts
    exist purely so authorship has something to point at.
    """
    existing = sql(f"SELECT id FROM users WHERE email='{persona.email}' LIMIT 1;")
    if existing:
        return int(existing.splitlines()[0])
    slug = re.sub(r"[^a-z0-9]+", "-", persona.display_name.lower()).strip("-")
    sql(
        "INSERT INTO users (name, email, password, slug, created_at, updated_at, "
        "email_confirmed, external_auth_id, system_name) VALUES "
        f"('{persona.display_name}', '{persona.email}', '', '{slug}', NOW(), NOW(), 1, '', NULL);"
    )
    return int(sql(f"SELECT id FROM users WHERE email='{persona.email}' LIMIT 1;").splitlines()[0])


def backdate(entity_id: int, when, user_id: int) -> None:
    """Set the real creation date and author on an entity.

    The API stamps `now` and the token owner; this is the correction pass. It
    touches only the entities row — BookStack reads authorship from there.
    """
    stamp = when.strftime("%Y-%m-%d %H:%M:%S")
    sql(
        "UPDATE entities SET "
        f"created_at='{stamp}', updated_at='{stamp}', "
        f"created_by={user_id}, updated_by={user_id}, owned_by={user_id} "
        f"WHERE id={entity_id};"
    )


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--single-author", action="store_true",
                        help="attribute everything to the admin instead of creating "
                             "a BookStack user per author")
    parser.add_argument("--collection", help="only process this collection directory")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)
    docs_dir = args.data_dir / "docs"
    if not docs_dir.is_dir():
        raise SystemExit(f"{docs_dir} does not exist")

    wl.heading("Parsing")
    books = load_collections(docs_dir / "collections.yaml", docs_dir, problems)
    documents = load_documents(docs_dir, books, identities, problems)
    if args.collection:
        books = {k: v for k, v in books.items() if k == args.collection}
        documents = [d for d in documents if d.collection_dir == args.collection]
    problems.raise_if_any()

    chapters = [d for d in documents if d.entity_type == "chapter"]
    pages = [d for d in documents if d.entity_type == "page"]
    wl.ok(f"{len(books)} book(s), {len(chapters)} chapter(s), {len(pages)} page(s)")
    wl.ok(f"author(s): {', '.join(sorted({d.author for d in documents})) or '(none)'}")

    if args.dry_run:
        wl.heading("Dry run")
        for spec in books.values():
            wl.dry(f"books.create name={spec.name!r}")
        for node in sorted(documents, key=lambda n: n.rel):
            where = f"chapter={node.parent_rel}" if node.parent_rel else f"book={node.collection_dir}"
            wl.dry(f"{node.entity_type}s.create title={node.title!r} author={node.author} "
                   f"{where} created_at="
                   f"{node.created_at.isoformat() if node.created_at else '?'}")
        wl.dry("then UPDATE entities SET created_at/created_by/owned_by per item")
        wl.summarise(True, [f"{len(books)} book(s), {len(documents)} document(s) validated"])
        return 0

    token = world.env.get("BOOKSTACK_TOKEN", "")
    if not token or ":" not in token:
        raise SystemExit(
            "BOOKSTACK_TOKEN missing or malformed. Inside the world it is read "
            "from /etc/sweworld/bookstack-token; outside, set it in .env as "
            "<token_id>:<token_secret>.")
    api = BookStack(world, token)

    # Author -> BookStack user id, resolved once.
    admin_id = int(sql("SELECT id FROM users WHERE id=1;") or 1)
    author_ids: dict[str, int] = {}

    def user_for(author: str) -> int:
        if args.single_author:
            return admin_id
        if author not in author_ids:
            persona = identities.get(author)
            author_ids[author] = ensure_bookstack_user(persona)
            wl.info(f"bookstack user for {persona.display_name} -> {author_ids[author]}")
        return author_ids[author]

    wl.heading("Creating books")
    for spec in books.values():
        spec.book_id = api.post("books", {"name": spec.name,
                                          "description": spec.description})["id"]
        wl.ok(f"book {spec.name!r} -> {spec.book_id}")

    wl.heading("Creating chapters and pages")
    # Chapters first: a page can only be filed into a chapter that exists.
    for node in sorted(chapters, key=lambda n: n.rel):
        node.entity_id = api.post("chapters", {
            "book_id": books[node.collection_dir].book_id,
            "name": node.title,
            "description": "",
        })["id"]
        backdate(node.entity_id, node.created_at, user_for(node.author))
        if args.verbose:
            wl.info(f"chapter {node.rel} -> {node.entity_id}")

    by_rel = {n.rel: n for n in documents}
    for node in sorted(pages, key=lambda n: n.rel):
        payload: dict[str, Any] = {"name": node.title, "markdown": node.body}
        parent = by_rel.get(node.parent_rel) if node.parent_rel else None
        if parent is not None and parent.entity_type == "chapter" and parent.entity_id:
            payload["chapter_id"] = parent.entity_id
        else:
            payload["book_id"] = books[node.collection_dir].book_id
        node.entity_id = api.post("pages", payload)["id"]
        backdate(node.entity_id, node.created_at, user_for(node.author))
        if args.verbose:
            wl.info(f"page {node.rel} -> {node.entity_id}")

    # A chapter carries no body of its own, so its markdown becomes a page
    # inside it. Losing it silently would drop real content.
    wl.heading("Chapter bodies")
    kept = 0
    for node in chapters:
        if not node.body.strip():
            continue
        page_id = api.post("pages", {"chapter_id": node.entity_id,
                                     "name": node.title,
                                     "markdown": node.body})["id"]
        backdate(page_id, node.created_at, user_for(node.author))
        kept += 1
    wl.ok(f"{kept} chapter body page(s) preserved")

    wl.summarise(False, [
        f"{len(books)} book(s), {len(chapters)} chapter(s), {len(pages) + kept} page(s)",
        f"browse at {world.url('docs')}",
    ])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\n\033[31mfailed\033[0m  {exc}", file=sys.stderr)
        raise SystemExit(1)
