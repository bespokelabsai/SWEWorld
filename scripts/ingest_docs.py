#!/usr/bin/env python3
"""Create Outline collections and documents from a directory of markdown.

Input
-----
data/identities.yaml           the persona list
data/docs/collections.yaml     one entry per top-level directory
data/docs/**/*.md              one file per document, YAML frontmatter + body

Layout mirrors the document tree. A directory sharing a stem with a sibling
.md file holds that document's children:

    data/docs/
      collections.yaml
      engineering/                  -> collection "Engineering"
        architecture.md             -> document
        architecture/               -> children of architecture.md
          storage-layer.md

collections.yaml:

    version: 1
    collections:
      - dir: engineering            # required, directory under data/docs/
        name: Engineering           # required, display name
        description: ...            # optional
        icon: beaker                # optional
        color: "#0366d6"            # optional, #rrggbb
        permission: read_write      # optional: read | read_write | null

Document frontmatter:

    ---
    title: Storage Layer            # required
    author: alice                   # required, persona id
    created_at: 2026-02-11T14:03:00Z  # required, ISO-8601, must be in the past
    updated_at: ...                 # optional
    publish: true                   # optional, default true
    icon: ...                       # optional
    full_width: false               # optional
    ---
    markdown body

Authorship
----------
Outline's documents.create accepts createdAt but has NO author field — a
document belongs to whoever owns the API token. By default this script logs
into Outline as each author via Gitea OIDC and mints their token, which
requires the persona to have a Gitea password. Use --single-author to create
everything with $OUTLINE_API_TOKEN instead.

A persona's Outline account does not exist until their first OIDC login;
Outline provides no API to pre-create one, so logging in is what creates them.

--dry-run resolves the entire tree, validates it, and prints the create plan
without making a single API call.
"""
from __future__ import annotations

import os
import re
import sys
import urllib.parse
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
DOC_OPTIONAL = ("updated_at", "publish", "icon", "full_width")
PERMISSIONS = {"read", "read_write", None}


@dataclass
class DocNode:
    """One markdown file, plus its position in the tree."""
    path: Path
    rel: str                       # path relative to data/docs, e.g. eng/arch.md
    title: str
    author: str
    created_at: Any
    body: str
    publish: bool = True
    icon: str | None = None
    full_width: bool = False
    collection_dir: str = ""
    parent_rel: str | None = None
    children: list["DocNode"] = field(default_factory=list)
    outline_id: str | None = None


@dataclass
class CollectionSpec:
    dir: str
    name: str
    description: str = ""
    icon: str | None = None
    color: str | None = None
    permission: Any = "read_write"
    outline_id: str | None = None


# =============================================================================
# Parsing
# =============================================================================
def parse_frontmatter(path: Path, problems: wl.Problems) -> tuple[dict, str] | None:
    """Split a markdown file into its YAML frontmatter and body."""
    text = path.read_text()
    match = FRONTMATTER_RE.match(text)
    if not match:
        problems.error(
            "missing YAML frontmatter — the file must start with a '---' block", path, 1
        )
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
                     problems: wl.Problems) -> dict[str, CollectionSpec]:
    """Parse and validate collections.yaml."""
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

    specs: dict[str, CollectionSpec] = {}
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
            problems.error(
                f"{context}: dir {directory!r} does not exist under {docs_dir}", path
            )
        if directory in specs:
            problems.error(f"{context}: duplicate dir {directory!r}", path)
            continue

        color = entry.get("color")
        if color is not None and not wl.HEX_COLOR_RE.match(str(color)):
            problems.error(
                f"{context}: color {color!r} must be #rrggbb — Outline rejects "
                "anything else", path,
            )
        permission = entry.get("permission", "read_write")
        if permission not in PERMISSIONS:
            problems.error(
                f"{context}: permission {permission!r} must be one of "
                f"{sorted(p for p in PERMISSIONS if p)} or null", path,
            )

        specs[directory] = CollectionSpec(
            dir=directory,
            name=entry.get("name", ""),
            description=entry.get("description", "") or "",
            icon=entry.get("icon"),
            color=color,
            permission=permission,
        )
    return specs


def load_documents(docs_dir: Path, collections: dict[str, CollectionSpec],
                   identities: wl.Identities, problems: wl.Problems) -> list[DocNode]:
    """Walk data/docs/ and build the document tree."""
    nodes: dict[str, DocNode] = {}

    for md_path in sorted(docs_dir.rglob("*.md")):
        rel = md_path.relative_to(docs_dir).as_posix()
        parts = Path(rel).parts
        if len(parts) < 2:
            problems.error(
                "documents must live inside a collection directory, not at the "
                "top level of data/docs/", md_path,
            )
            continue

        collection_dir = parts[0]
        if collection_dir not in collections:
            problems.error(
                f"directory {collection_dir!r} has no entry in collections.yaml — "
                "unlisted directories are an error, not an implicit collection",
                md_path,
            )

        parsed = parse_frontmatter(md_path, problems)
        if parsed is None:
            continue
        meta, body = parsed
        wl.check_keys(meta, required=DOC_REQUIRED, optional=DOC_OPTIONAL,
                      problems=problems, path=md_path, line=1)

        identities.require(meta.get("author"), problems, md_path, 1, "author")
        created = wl.parse_ts(meta.get("created_at"), path=md_path, line=1,
                              problems=problems, field_name="created_at")
        if created is not None:
            import datetime as _dt
            if created > _dt.datetime.now(_dt.timezone.utc):
                problems.error(
                    "created_at must be in the past — Outline rejects future dates",
                    md_path, 1,
                )

        # Parent is the sibling .md matching this file's parent directory.
        parent_rel = None
        if len(parts) > 2:
            parent_rel = Path(*parts[:-1]).as_posix() + ".md"

        nodes[rel] = DocNode(
            path=md_path, rel=rel,
            title=str(meta.get("title", "")),
            author=str(meta.get("author", "")),
            created_at=created,
            body=body,
            publish=bool(meta.get("publish", True)),
            icon=meta.get("icon"),
            full_width=bool(meta.get("full_width", False)),
            collection_dir=collection_dir,
            parent_rel=parent_rel,
        )

    # An orphan child directory means the parent document is missing.
    for rel, node in nodes.items():
        if node.parent_rel and node.parent_rel not in nodes:
            problems.error(
                f"parent document {node.parent_rel!r} does not exist — a child "
                "directory needs a sibling .md file of the same name",
                node.path,
            )

    # Cross-links must resolve to a real file.
    for node in nodes.values():
        for _, target in MD_LINK_RE.findall(node.body):
            if target.startswith(("http://", "https://", "#")):
                continue
            if not any(c in nodes for c in _link_candidates(node.rel, target)):
                problems.warn(
                    f"cross-link {target!r} does not resolve to a document; "
                    "it will be left as written", node.path,
                )

    for parent in nodes.values():
        if parent.parent_rel and parent.parent_rel in nodes:
            nodes[parent.parent_rel].children.append(parent)

    return list(nodes.values())


def _link_candidates(from_rel: str, target: str) -> list[str]:
    """Paths a markdown link might mean, relative to data/docs/.

    A generation step may reasonably write links relative to the linking
    document or relative to the docs root, so both are accepted and the caller
    takes whichever resolves to a real document.
    """
    if target.startswith("/"):
        return [target.lstrip("/")]
    relative = os.path.normpath(str(Path(from_rel).parent / target)).replace(os.sep, "/")
    from_root = os.path.normpath(target).replace(os.sep, "/")
    return [relative] if relative == from_root else [relative, from_root]


def order_for_creation(nodes: list[DocNode]) -> list[DocNode]:
    """Parents before children — Outline needs a parentDocumentId that exists."""
    by_rel = {n.rel: n for n in nodes}
    ordered: list[DocNode] = []
    seen: set[str] = set()

    def visit(node: DocNode) -> None:
        if node.rel in seen:
            return
        if node.parent_rel and node.parent_rel in by_rel:
            visit(by_rel[node.parent_rel])
        seen.add(node.rel)
        ordered.append(node)

    for node in sorted(nodes, key=lambda n: n.rel):
        visit(node)
    return ordered


# =============================================================================
# Outline API
# =============================================================================
def ensure_gitea_user(world: wl.World, persona: wl.Persona) -> bool:
    """Create the persona's Gitea account if absent. Returns True if created.

    Outline attributes a document to its token's owner, and a persona can only
    get a token by logging in through Gitea — so per-author attribution needs a
    Gitea account to exist first. Nothing else in the pipeline creates these,
    because git commits carry authorship in the commit object and need no
    account at all.
    """
    sess = wl.session(world)
    headers = {"Authorization": f"token {world.env['GITEA_API_TOKEN']}",
               "Content-Type": "application/json"}

    got = sess.get(world.url("git", f"/api/v1/users/{persona.gitea_username}"),
                   headers=headers, timeout=30)
    if got.status_code == 200:
        return False

    created = sess.post(
        world.url("git", "/api/v1/admin/users"),
        headers=headers,
        json={
            "username": persona.gitea_username,
            "email": persona.email,
            "password": persona.password,
            "full_name": persona.display_name,
            "must_change_password": False,
        },
        timeout=30,
    )
    if created.status_code not in (200, 201):
        raise RuntimeError(
            f"could not create Gitea account for {persona.id!r} "
            f"({created.status_code}): {created.text[:300]}"
        )
    return True


def outline_session(world: wl.World, username: str, password: str):
    """Authenticate to Outline as a specific persona via Gitea OIDC.

    This is the same flow scripts/mint_outline_token.py performs for the admin.
    It is also what provisions the persona's Outline account on first run.
    """
    sess = wl.session(world)
    git_url, docs_url = world.url("git"), world.url("docs")

    def csrf(html: str) -> str | None:
        for pattern in (r'name="_csrf"\s+value="([^"]+)"',
                        r'content="([^"]+)"\s+name="csrf-token"'):
            found = re.search(pattern, html)
            if found:
                return found.group(1)
        return None

    resp = sess.get(f"{git_url}/user/login", timeout=30)
    resp = sess.post(f"{git_url}/user/login", timeout=30,
                     data={"_csrf": csrf(resp.text), "user_name": username,
                           "password": password})
    if "/user/login" in resp.url:
        raise RuntimeError(
            f"Gitea login failed for {username!r} — is their password set? "
            "See 'password' in data/schemas/identities.md"
        )

    resp = sess.get(f"{docs_url}/auth/oidc", allow_redirects=True, timeout=30)
    if "/login/oauth/authorize" in resp.url:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(resp.url).query)
        resp = sess.post(f"{git_url}/login/oauth/grant", timeout=30, allow_redirects=True,
                         data={"_csrf": csrf(resp.text),
                               "client_id": query.get("client_id", [""])[0],
                               "state": query.get("state", [""])[0],
                               "redirect_uri": query.get("redirect_uri", [""])[0],
                               "response_type": "code",
                               "scope": query.get("scope", [""])[0],
                               "granted": "true"})

    info = sess.post(f"{docs_url}/api/auth.info", json={}, timeout=30)
    if info.status_code != 200:
        raise RuntimeError(f"OIDC login for {username!r} produced no Outline session")
    return sess


class OutlineClient:
    """Thin wrapper that handles Outline's CSRF requirement on mutations."""

    def __init__(self, world: wl.World, sess, token: str | None = None):
        self.world = world
        self.sess = sess
        self.token = token

    def call(self, endpoint: str, payload: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        csrf = self.sess.cookies.get("csrfToken") if self.sess.cookies else None
        if csrf:
            headers["x-csrf-token"] = csrf
        resp = self.sess.post(self.world.url("docs", f"/api/{endpoint}"),
                              json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"{endpoint} failed ({resp.status_code}): {resp.text[:300]}")
        return resp.json()


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--single-author", action="store_true",
                        help="create everything with $OUTLINE_API_TOKEN instead of "
                             "minting a token per author")
    parser.add_argument("--collection", help="only process this collection directory")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)
    docs_dir = args.data_dir / "docs"
    if not docs_dir.is_dir():
        raise SystemExit(f"{docs_dir} does not exist")

    wl.heading("Parsing")
    collections = load_collections(docs_dir / "collections.yaml", docs_dir, problems)
    documents = load_documents(docs_dir, collections, identities, problems)

    if args.collection:
        collections = {k: v for k, v in collections.items() if k == args.collection}
        documents = [d for d in documents if d.collection_dir == args.collection]

    problems.raise_if_any()

    ordered = order_for_creation(documents)
    wl.ok(f"{len(collections)} collection(s), {len(ordered)} document(s)")
    authors = sorted({d.author for d in ordered})
    wl.ok(f"author(s): {', '.join(authors) or '(none)'}")

    if args.dry_run:
        wl.heading("Dry run")
        for spec in collections.values():
            wl.dry(f"collections.create name={spec.name!r} permission={spec.permission!r}")
        for node in ordered:
            parent = f" parent={node.parent_rel}" if node.parent_rel else ""
            wl.dry(
                f"documents.create title={node.title!r} author={node.author} "
                f"collection={node.collection_dir}{parent} "
                f"createdAt={node.created_at.isoformat() if node.created_at else '?'} "
                f"({len(node.body)} chars)"
            )
        mode = "single-author" if args.single_author else "one token per author"
        wl.dry(f"authorship mode: {mode}")
        wl.summarise(True, [
            f"{len(collections)} collection(s), {len(ordered)} document(s) validated",
        ])
        return 0

    world.require("OUTLINE_API_TOKEN")
    if not args.single_author:
        # Needed to create persona Gitea accounts so each author can be logged
        # in and attributed properly.
        world.require("GITEA_API_TOKEN")
    admin_client = OutlineClient(world, wl.session(world), world.env["OUTLINE_API_TOKEN"])

    wl.heading("Creating collections")
    for spec in collections.values():
        payload: dict[str, Any] = {"name": spec.name, "description": spec.description,
                                   "permission": spec.permission}
        if spec.icon:
            payload["icon"] = spec.icon
        if spec.color:
            payload["color"] = spec.color
        spec.outline_id = admin_client.call("collections.create", payload)["data"]["id"]
        wl.ok(f"collection {spec.name!r} -> {spec.outline_id}")

    # One authenticated client per author, built lazily.
    clients: dict[str, OutlineClient] = {}

    def client_for(author_id: str) -> OutlineClient:
        if args.single_author:
            return admin_client
        if author_id not in clients:
            persona = identities.get(author_id)
            if ensure_gitea_user(world, persona):
                wl.ok(f"created Gitea account for {persona.gitea_username}")
            # This login is also what provisions the persona's Outline account —
            # Outline has no API to pre-create one.
            sess = outline_session(world, persona.gitea_username, persona.password)
            clients[author_id] = OutlineClient(world, sess)
            wl.info(f"authenticated to Outline as {persona.gitea_username}")
        return clients[author_id]

    wl.heading("Creating documents")
    by_rel = {n.rel: n for n in ordered}
    for node in ordered:
        payload = {
            "title": node.title,
            "text": node.body,
            "publish": node.publish,
            "createdAt": node.created_at.isoformat(),
            "fullWidth": node.full_width,
        }
        if node.parent_rel and by_rel[node.parent_rel].outline_id:
            payload["parentDocumentId"] = by_rel[node.parent_rel].outline_id
        else:
            payload["collectionId"] = collections[node.collection_dir].outline_id
        if node.icon:
            payload["icon"] = node.icon

        node.outline_id = client_for(node.author).call(
            "documents.create", payload)["data"]["id"]
        if args.verbose:
            wl.info(f"{node.rel} -> {node.outline_id}")

    wl.ok(f"{len(ordered)} document(s) created")

    # Second pass: a document's UUID does not exist until it is created, so
    # cross-links can only be rewritten once every target has an id.
    wl.heading("Rewriting cross-links")
    rewritten = 0
    for node in ordered:
        new_body, changed = _rewrite_links(node, by_rel, world)
        if changed:
            client_for(node.author).call("documents.update",
                                         {"id": node.outline_id, "text": new_body})
            rewritten += 1
    wl.ok(f"{rewritten} document(s) had links rewritten")

    wl.summarise(False, [
        f"{len(collections)} collection(s), {len(ordered)} document(s)",
        f"{rewritten} document(s) with rewritten cross-links",
        f"browse at {world.url('docs')}",
    ])
    return 0


def _rewrite_links(node: DocNode, by_rel: dict[str, DocNode],
                   world: wl.World) -> tuple[str, bool]:
    """Replace [text](other/doc.md) with the target's real Outline URL."""
    changed = False

    def repl(match):
        nonlocal changed
        label, target = match.group(1), match.group(2)
        if target.startswith(("http://", "https://", "#")):
            return match.group(0)
        for candidate in _link_candidates(node.rel, target):
            dest = by_rel.get(candidate)
            if dest is not None and dest.outline_id:
                changed = True
                return f"[{label}]({world.url('docs', f'/doc/{dest.outline_id}')})"
        return match.group(0)

    return MD_LINK_RE.sub(repl, node.body), changed


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\n\033[31mfailed\033[0m  {exc}", file=sys.stderr)
        raise SystemExit(1)
