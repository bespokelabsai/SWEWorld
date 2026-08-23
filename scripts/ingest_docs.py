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

A successful run also writes .docs-manifest.json beside the data directory,
mapping each document's path to the page it became. ingest_comments.py reads it
so a comment can name a document rather than a page id.

--dry-run resolves the whole tree, validates it and prints the plan without
touching the API or the database.
"""
from __future__ import annotations

import datetime as dt
import json
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

# Written after a successful run so ingest_comments.py can resolve a document
# path to the page it became, without re-deriving ids from the API.
MANIFEST_NAME = ".docs-manifest.json"


@dataclass
class DocNode:
    path: Path
    rel: str
    title: str
    author: str
    created_at: Any
    body: str
    updated_at: Any = None
    collection_dir: str = ""
    parent_rel: str | None = None
    depth: int = 0
    children: list["DocNode"] = field(default_factory=list)
    entity_id: int | None = None
    entity_type: str = "page"
    body_page_id: int | None = None

    @property
    def page_id(self) -> int | None:
        """The page a comment on this document would attach to.

        A document with children becomes a Chapter plus a page holding its body,
        and comments attach to pages only — so for a chapter it is the body page,
        never the chapter itself. This property is the single place that rule
        lives.
        """
        return self.entity_id if self.entity_type == "page" else self.body_page_id


@dataclass
class BookSpec:
    dir: str
    name: str
    description: str = ""
    book_id: int | None = None
    # Taken from the earliest document in the collection: a book came into
    # existence when someone wrote its first page. collections.yaml carries no
    # author or date of its own, and inventing one would be less true than this.
    author: str = ""
    created_at: Any = None


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
    if not isinstance(entries, list):
        problems.error("collections must be a list", path)
        return {}
    if not entries:
        # An empty wiki is a state the world can legitimately be in — before the
        # renderer has filled it, or in a world that simply does not use one.
        # Refusing to start is how one absent corpus took the whole bake down
        # with it, including the six ingests that had nothing to do with docs.
        wl.info("no collections listed; there is no wiki content to ingest")
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
        updated = created
        if meta.get("updated_at") is not None:
            updated = wl.parse_ts(meta.get("updated_at"), path=md_path, line=1,
                                  problems=problems, field_name="updated_at")
            if created and updated and updated < created:
                problems.error("updated_at is earlier than created_at", md_path, 1)

        parent_rel = Path(*parts[:-1]).as_posix() + ".md" if len(parts) > 2 else None
        nodes[rel] = DocNode(
            path=md_path, rel=rel, title=str(meta.get("title", "")),
            author=str(meta.get("author", "")), created_at=created, body=body,
            updated_at=updated,
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


def attribute_books(books: dict[str, BookSpec], documents: list[DocNode]) -> None:
    """Give each book the author and date of its earliest document.

    Without this a book is stamped `now` and owned by the admin, which is what
    the whole backdating pass exists to avoid — and it is visible immediately,
    since a book page shows Created/Updated in its sidebar.
    """
    for spec in books.values():
        owned = [d for d in documents
                 if d.collection_dir == spec.dir and d.created_at is not None]
        if not owned:
            continue
        first = min(owned, key=lambda d: d.created_at)
        spec.author, spec.created_at = first.author, first.created_at


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

    def put(self, endpoint: str, payload: dict) -> dict:
        resp = self.sess.put(self.world.url("docs", f"/api/{endpoint}"),
                             json=payload, headers=self.headers, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"PUT {endpoint} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()


def sql(statement: str) -> str:
    """Run one statement against the BookStack database (in-container only)."""
    proc = subprocess.run(MYSQL + [statement], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"mariadb failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def sql_lit(value: Any) -> str:
    """Quote a value as a SQL string literal.

    Hex rather than escaping: MariaDB accepts X'...' anywhere a string literal
    goes, so there are no quoting rules to get wrong and no dependence on
    sql_mode (NO_BACKSLASH_ESCAPES changes what a hand-rolled escaper must do).
    An apostrophe in a display name used to break the INSERT below.
    """
    return "X'" + str(value).encode("utf-8").hex() + "'"


def _stamp(when) -> str:
    """Render a datetime as MySQL DATETIME, in UTC.

    strftime on an aware datetime drops the offset, so a +01:00 timestamp would
    land as its local wall clock in a container that reads DATETIME as UTC —
    an hour adrift, and worse for larger offsets.
    """
    return when.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def ensure_bookstack_user(persona: wl.Persona) -> int:
    """Return the BookStack user id for a persona, creating the row if needed.

    Done in SQL rather than through the API because the API requires a
    password-policy dance for a user that will never log in — these accounts
    exist purely so authorship has something to point at.
    """
    lookup = f"SELECT id FROM users WHERE email={sql_lit(persona.email)} LIMIT 1;"
    existing = sql(lookup)
    if existing:
        return int(existing.splitlines()[0])
    slug = re.sub(r"[^a-z0-9]+", "-", persona.display_name.lower()).strip("-")
    sql(
        "INSERT INTO users (name, email, password, slug, created_at, updated_at, "
        "email_confirmed, external_auth_id, system_name) VALUES "
        f"({sql_lit(persona.display_name)}, {sql_lit(persona.email)}, '', "
        f"{sql_lit(slug)}, NOW(), NOW(), 1, '', NULL);"
    )
    return int(sql(lookup).splitlines()[0])


def make_user_resolver(identities: wl.Identities, single_author: bool, admin_id: int):
    """Return a memoised author -> BookStack user id function.

    Shared with ingest_comments.py so a page and the comments on it never end up
    attributed differently — one script creating persona users and the other not
    would do exactly that.
    """
    author_ids: dict[str, int] = {}

    def user_for(author: str) -> int:
        if single_author:
            return admin_id
        if author not in author_ids:
            persona = identities.get(author)
            author_ids[author] = ensure_bookstack_user(persona)
            wl.info(f"bookstack user for {persona.display_name} -> {author_ids[author]}")
        return author_ids[author]

    return user_for


def backdate(entity_id: int, when, user_id: int, updated=None) -> None:
    """Set the real creation date and author on an entity.

    The API stamps `now` and the token owner; this is the correction pass. It
    touches only the entities row — BookStack reads authorship from there.
    """
    created_stamp = _stamp(when)
    updated_stamp = _stamp(updated) if updated is not None else created_stamp
    sql(
        "UPDATE entities SET "
        f"created_at='{created_stamp}', updated_at='{updated_stamp}', "
        f"created_by={user_id}, updated_by={user_id}, owned_by={user_id} "
        f"WHERE id={entity_id};"
    )


def backdate_comment(comment_id: int, when, user_id: int) -> None:
    """Set the real creation date and author on a comment.

    Not a call to backdate(): that writes `owned_by`, which the comments table
    has no column for, so reusing it fails outright with `Unknown column`.
    Comments are owned by their page, not independently.

    Metadata only — the comment's html and text stay exactly as the API wrote
    them, because BookStack derives `text` from the submitted html and sanitises
    it server-side.
    """
    stamp = _stamp(when)
    sql(
        "UPDATE comments SET "
        f"created_at='{stamp}', updated_at='{stamp}', "
        f"created_by={user_id}, updated_by={user_id} "
        f"WHERE id={comment_id};"
    )


def resettle_history() -> tuple[int, int]:
    """Point BookStack's revisions and activity feed at the real authors/dates.

    Correcting the `entities` and `comments` rows fixes the bylines on a page,
    but BookStack surfaces authorship from two more places, and both are more
    prominent than the byline:

      * `page_revisions` — the "Revision #1 ... by ..." line, and the whole
        revision history behind it.
      * `activities` — the Recent Activity feed, which is the main content of
        the dashboard and appears on every book page.

    Left alone, the dashboard reads "World Admin created page X, 3 minutes ago"
    for the entire world. This is not an audit log tucked away in an admin
    screen; it is the first thing anyone sees on opening the wiki.

    Returns (revisions, activities) corrected.
    """
    sql(
        "UPDATE page_revisions r JOIN entities e ON e.id = r.page_id "
        "SET r.created_by = e.created_by, r.created_at = e.created_at, "
        "    r.updated_at = e.updated_at;"
    )
    revisions = int(sql("SELECT count(*) FROM page_revisions;") or 0)

    # Books, chapters and pages: the activity points straight at the entity.
    sql(
        "UPDATE activities a JOIN entities e "
        "  ON e.id = a.loggable_id AND a.loggable_type = e.type "
        "SET a.user_id = e.created_by, a.created_at = e.created_at, "
        "    a.updated_at = e.created_at;"
    )

    # Comments are logged as a consecutive pair with no usable loggable_id:
    #   comment_create   loggable NULL, detail "Comment #1 (ID: 7) for page (ID: 4)"
    #   commented_on     loggable = the *page*, so it cannot be joined to an author
    # The comment id is only recoverable from the detail text, and the
    # commented_on row is matched to the comment_create it follows.
    # comment_update comes from setting `archived`, which is a write this
    # ingestion makes rather than an event in the world. Attributing it to the
    # thread's author beats leaving "World Admin, just now" in the feed.
    rows = sql("SELECT id, type, detail FROM activities "
               "WHERE type IN ('comment_create','comment_update','commented_on') "
               "ORDER BY id;")
    pending: str | None = None
    for line in rows.splitlines():
        if not line.strip():
            continue
        act_id, act_type, detail = (line.split("\t", 2) + ["", ""])[:3]
        if act_type in ("comment_create", "comment_update"):
            match = re.search(r"\(ID:\s*(\d+)\)", detail)
            if not match:
                continue
            _sync_activity_to_comment(act_id, match.group(1))
            if act_type == "comment_create":
                pending = match.group(1)
        elif act_type == "commented_on" and pending is not None:
            _sync_activity_to_comment(act_id, pending)
            pending = None

    total = int(sql("SELECT count(*) FROM activities;") or 0)
    return revisions, total


def _sync_activity_to_comment(activity_id: str, comment_id: str) -> None:
    sql(
        "UPDATE activities a JOIN comments c ON c.id = " + str(int(comment_id)) + " "
        "SET a.user_id = c.created_by, a.created_at = c.created_at, "
        "    a.updated_at = c.created_at "
        "WHERE a.id = " + str(int(activity_id)) + ";"
    )


def write_manifest(path: Path, documents: list[DocNode]) -> int:
    """Record which page each document became.

    ingest_comments.py needs `doc path -> page id`, and rebuilding that from the
    API means paginating books, chapters and pages and matching on title, which
    is ambiguous the moment two documents share one. `title` is stored alongside
    so a consumer can detect a manifest left over from a destroyed database.
    """
    pages = {
        node.rel: {
            "page_id": node.page_id,
            "title": node.title,
            "author": node.author,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        }
        for node in sorted(documents, key=lambda n: n.rel)
        if node.page_id is not None
    }
    path.write_text(json.dumps({"version": 1, "pages": pages}, indent=2) + "\n")
    return len(pages)


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--single-author", action="store_true",
                        help="attribute everything to the admin instead of creating "
                             "a BookStack user per author")
    parser.add_argument("--collection", help="only process this collection directory")
    parser.add_argument("--manifest", type=Path,
                        help=f"where to record doc path -> page id "
                             f"(default: {MANIFEST_NAME} beside --data-dir)")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)
    docs_dir = args.data_dir / "docs"
    if not docs_dir.is_dir():
        raise SystemExit(f"{docs_dir} does not exist")
    # Beside data/, not inside it: `docker cp data` into the world would
    # otherwise carry a manifest pointing at some other database's page ids.
    manifest_path = args.manifest or (args.data_dir.parent / MANIFEST_NAME)

    wl.heading("Parsing")
    books = load_collections(docs_dir / "collections.yaml", docs_dir, problems)
    documents = load_documents(docs_dir, books, identities, problems)
    attribute_books(books, documents)
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
            wl.dry(f"books.create name={spec.name!r} author={spec.author or '?'} "
                   f"created_at={spec.created_at.isoformat() if spec.created_at else '?'}"
                   " (from its earliest document)")
        for node in sorted(documents, key=lambda n: n.rel):
            where = f"chapter={node.parent_rel}" if node.parent_rel else f"book={node.collection_dir}"
            wl.dry(f"{node.entity_type}s.create title={node.title!r} author={node.author} "
                   f"{where} created_at="
                   f"{node.created_at.isoformat() if node.created_at else '?'}")
        wl.dry("then UPDATE entities SET created_at/created_by/owned_by per item")
        wl.dry("then reattribute page_revisions and the activities feed to match")
        wl.dry(f"then write {manifest_path} mapping doc path -> page id")
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
    user_for = make_user_resolver(identities, args.single_author, admin_id)

    wl.heading("Creating books")
    for spec in books.values():
        spec.book_id = api.post("books", {"name": spec.name,
                                          "description": spec.description})["id"]
        if spec.created_at is not None:
            backdate(spec.book_id, spec.created_at, user_for(spec.author))
        wl.ok(f"book {spec.name!r} -> {spec.book_id}")

    wl.heading("Creating chapters and pages")
    # Chapters first: a page can only be filed into a chapter that exists.
    for node in sorted(chapters, key=lambda n: n.rel):
        node.entity_id = api.post("chapters", {
            "book_id": books[node.collection_dir].book_id,
            "name": node.title,
            "description": "",
        })["id"]
        backdate(node.entity_id, node.created_at, user_for(node.author), node.updated_at)
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
        backdate(node.entity_id, node.created_at, user_for(node.author), node.updated_at)
        if args.verbose:
            wl.info(f"page {node.rel} -> {node.entity_id}")

    # A chapter carries no body of its own, so its markdown becomes a page
    # inside it. Losing it silently would drop real content.
    wl.heading("Chapter bodies")
    kept = 0
    for node in chapters:
        if not node.body.strip():
            continue
        node.body_page_id = api.post("pages", {"chapter_id": node.entity_id,
                                               "name": node.title,
                                               "markdown": node.body})["id"]
        backdate(node.body_page_id, node.created_at, user_for(node.author), node.updated_at)
        kept += 1
    wl.ok(f"{kept} chapter body page(s) preserved")

    revisions, activities = resettle_history()
    wl.ok(f"{revisions} revision(s) and {activities} activity row(s) reattributed")

    written = write_manifest(manifest_path, documents)
    wl.ok(f"manifest: {written} page(s) -> {manifest_path}")

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
