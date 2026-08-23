#!/usr/bin/env python3
"""Create BookStack page comments from a JSONL stream.

Input
-----
data/identities.yaml      the persona list
data/docs/**/*.md         the documents, parsed again to resolve `doc` paths
data/comments.jsonl       one comment per line
.docs-manifest.json       doc path -> page id, written by ingest_docs.py

Each line names the document it belongs to by the same repo-relative path used
for cross-links, so nothing here refers to a BookStack id:

    {"doc":"engineering/architecture/storage-layer.md","author":"alice",
     "created_at":"2026-01-18T09:12:00Z","quote":"Blast radius.",
     "text":"Does this hold for the read replicas too?"}

Anchoring
---------
A comment may quote text from the page it is about. BookStack stores that as a
`content_ref`: an element id, a hash of that element's text, and a character
range. All three are derived here from the page's *rendered* HTML, which does
not exist until the page has been created — so there is no field for it, and
quotes are written as the text reads on the page rather than as it appears in
markdown.

A quote that no longer appears in its document, or appears twice, fails the run.
That check is as much the point of the feature as the highlight is.

Ordering
--------
BookStack numbers comments per page from 1 (`local_id`) and a reply refers to
its parent by that number, so parents must be created first. Requiring a reply
to be no older than its parent makes chronological order do that on its own, at
any nesting depth.

Authorship and dates
--------------------
The API has no author or date field, so comments are created by the token owner
and then corrected in the `comments` table, the same two-step ingest_docs.py
uses for pages. Every commented page is then re-settled to its own real date —
defensively, since 25.11 leaves the parent alone.

--dry-run parses and validates everything and prints the plan without touching
the API or the database. It cannot check quotes against the rendered HTML — it
says so rather than letting the weaker check pass for the stronger one.
"""
from __future__ import annotations

import html
import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ingest_docs as docs  # noqa: E402
import worldlib as wl  # noqa: E402

COMMENT_REQUIRED = ("doc", "author", "created_at", "text")
COMMENT_OPTIONAL = ("id", "reply_to", "quote", "archived")

MAX_REPLY_DEPTH = 10

# Elements that never have a closing tag. HTMLParser still calls
# handle_starttag for them, and pushing one desyncs the element stack, which
# silently corrupts the offsets of everything after it. They also contribute
# nothing to textContent, so ignoring them is correct as well as necessary.
VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})
SKIP_CONTENT_TAGS = frozenset({"script", "style"})

# JavaScript's \s, spelled out. Python's differs at both ends — it matches
# \x1c-\x1f, which JS does not, and misses U+FEFF, which JS does — and this hash
# has to agree with BookStack's JS or every reference on a page renders as
# outdated. Written as escapes because the characters themselves are invisible.
JS_WHITESPACE = (
    "\f\n\r\t\v\u0020\u00a0\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f\u205f\u3000\ufeff"
)
NORMALISE_RE = re.compile(f"[{re.escape(JS_WHITESPACE)}]{{2,}}")

MASK32 = 0xFFFFFFFF


# =============================================================================
# Text projection and hashing
# =============================================================================
def normalise(text: str) -> str:
    """BookStack's hashElement normalisation: delete runs of 2+ whitespace.

    Deletes, not collapses. A single space or newline survives untouched.
    """
    return NORMALISE_RE.sub("", text)


def _imul(a: int, b: int) -> int:
    """JavaScript Math.imul — the low 32 bits of the product."""
    return (a * b) & MASK32


def _utf16_units(text: str) -> tuple[int, ...]:
    """The code units charCodeAt would yield, surrogate pairs included.

    Iterating Python characters instead would treat an emoji as one unit where
    JavaScript sees two, and every hash on that page would differ.
    """
    raw = text.encode("utf-16-le")
    return struct.unpack(f"<{len(raw) // 2}H", raw)


def cyrb53(text: str, seed: int = 0) -> str:
    """The 53-bit hash BookStack uses to detect a comment's target changing.

    Ported from resources/js/services/util.ts. Verified against Node for ASCII,
    the empty string, accented text and astral-plane characters.
    """
    h1 = (0xDEADBEEF ^ seed) & MASK32
    h2 = (0x41C6CE57 ^ seed) & MASK32
    for unit in _utf16_units(text):
        h1 = _imul(h1 ^ unit, 2654435761)
        h2 = _imul(h2 ^ unit, 1597334677)
    # The second line consumes the h1 assigned on the first. Computing both
    # from the pre-update values is a tempting tidy-up and yields a wrong hash.
    h1 = _imul(h1 ^ (h1 >> 16), 2246822507) ^ _imul(h2 ^ (h2 >> 13), 3266489909)
    h2 = _imul(h2 ^ (h2 >> 16), 2246822507) ^ _imul(h1 ^ (h1 >> 13), 3266489909)
    return str(4294967296 * (2097151 & h2) + (h1 & MASK32))


class TextIndex(HTMLParser):
    """Extracts a page's text and the character span of each element with an id.

    The result models DOM textContent: every text node concatenated in document
    order, entities decoded, script and style content excluded.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._length = 0
        self._stack: list[tuple[str, str | None, int]] = []
        self._skipping = 0
        self.spans: list[tuple[str, int, int]] = []

    @property
    def text(self) -> str:
        return "".join(self._chunks)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            return
        if tag in SKIP_CONTENT_TAGS:
            self._skipping += 1
        self._stack.append((tag, dict(attrs).get("id"), self._length))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return  # self-closing: no content, no span

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        # Close everything up to the matching tag, so unbalanced markup cannot
        # leave the stack permanently skewed.
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] != tag:
                continue
            while len(self._stack) > index:
                open_tag, element_id, start = self._stack.pop()
                if element_id:
                    self.spans.append((element_id, start, self._length))
                if open_tag in SKIP_CONTENT_TAGS:
                    self._skipping -= 1
            return

    def handle_data(self, data: str) -> None:
        if self._skipping:
            return
        self._chunks.append(data)
        self._length += len(data)


def build_index(page_html: str) -> tuple[str, list[tuple[str, int, int]]]:
    parser = TextIndex()
    parser.feed(page_html)
    parser.close()
    return parser.text, parser.spans


def quote_re(quote: str) -> re.Pattern[str]:
    """Match a quote regardless of how whitespace fell in the rendered output.

    A quote written on one line has to match text that markdown wrapped across
    two, so every run of whitespace matches any run of whitespace.
    """
    return re.compile(r"\s+".join(re.escape(word) for word in quote.split()))


FENCE_RE = re.compile(r"^\s*```.*$", re.M)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
CODE_RE = re.compile(r"`([^`]*)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)|(?<!_)_([^_\n]+)_(?!_)")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+", re.M)
QUOTE_RE = re.compile(r"^\s{0,3}>\s?", re.M)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+", re.M)
TABLE_RULE_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*$", re.M)


def markdown_text(body: str) -> str:
    """Approximate what a markdown body will read as once rendered.

    Only used offline, so that `--dry-run` can catch a quote that no longer
    appears in its document without a running BookStack. The authoritative
    check runs against the real HTML at write time.
    """
    text = FENCE_RE.sub("", body)
    text = IMAGE_RE.sub(r"\1", text)
    text = LINK_RE.sub(r"\1", text)
    text = CODE_RE.sub(r"\1", text)
    text = BOLD_RE.sub(lambda m: m.group(1) or m.group(2), text)
    text = ITALIC_RE.sub(lambda m: m.group(1) or m.group(2), text)
    text = HEADING_RE.sub("", text)
    text = QUOTE_RE.sub("", text)
    text = TABLE_RULE_RE.sub("", text)
    text = BULLET_RE.sub("", text)
    return text.replace("|", " ")


def resolve_ref(page_text: str, spans: list[tuple[str, int, int]], quote: str,
                problems: wl.Problems, path: Path, line: int) -> str | None:
    """Turn a quote into BookStack's `elementId:hash:start-end`."""
    matches = list(quote_re(quote).finditer(page_text))
    if not matches:
        problems.error(
            f"quote {quote[:60]!r} does not appear in the rendered page — quote the "
            "text as it reads on the page, without markdown syntax", path, line)
        return None
    if len(matches) > 1:
        problems.error(
            f"quote {quote[:60]!r} appears {len(matches)} times; lengthen it until "
            "it is unique", path, line)
        return None

    match = matches[0]
    containing = [s for s in spans if s[1] <= match.start() and match.end() <= s[2]]
    if not containing:
        problems.error(
            f"quote {quote[:60]!r} spans more than one block, so there is no single "
            "element to anchor it to", path, line)
        return None

    # The narrowest enclosing element is the innermost one with an id, which is
    # what the browser's own walk-up from the selection arrives at.
    element_id, start, end = min(containing, key=lambda s: s[2] - s[1])
    # The hash covers the whole element and is normalised; the offsets index the
    # raw text. Two different strings, deliberately — BookStack does the same.
    digest = cyrb53(normalise(page_text[start:end]))
    return f"{element_id}:{digest}:{match.start() - start}-{match.end() - start}"


def to_html(text: str) -> str:
    """Render a plain-text comment as the HTML the API requires.

    There is no markdown library in this repo's dependencies and adding one for
    a single field is not worth it, so `text` is plain text by definition —
    see data/schemas/comments.md.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "\n".join(
        "<p>" + html.escape(p, quote=False).replace("\n", "<br>") + "</p>"
        for p in paragraphs
    )


# =============================================================================
# Parsing
# =============================================================================
def load_comments(path: Path, by_rel: dict[str, docs.DocNode],
                  identities: wl.Identities, problems: wl.Problems) -> list[dict]:
    rows = wl.read_jsonl(path, problems)

    # First pass: collect handles, so a reply may appear before the comment it
    # answers and still validate.
    handles: dict[str, int] = {}
    for lineno, obj in rows:
        handle = obj.get("id")
        if handle is None:
            continue
        if not isinstance(handle, str):
            problems.error("id must be a string", path, lineno)
        elif handle in handles:
            problems.error(
                f"duplicate comment id {handle!r} (also on line {handles[handle]})",
                path, lineno)
        else:
            handles[handle] = lineno

    by_handle: dict[str, dict] = {}
    parsed: list[dict] = []
    for lineno, obj in rows:
        wl.check_keys(obj, required=COMMENT_REQUIRED, optional=COMMENT_OPTIONAL,
                      problems=problems, path=path, line=lineno)
        identities.require(obj.get("author"), problems, path, lineno, "author")
        created = wl.parse_ts(obj.get("created_at"), path=path, line=lineno,
                              problems=problems, field_name="created_at")

        rel = obj.get("doc")
        node = by_rel.get(rel) if isinstance(rel, str) else None
        if isinstance(rel, str) and node is None:
            known = ", ".join(sorted(by_rel)[:6])
            problems.error(
                f"unknown document {rel!r} in doc — known documents: {known}…",
                path, lineno)
        elif node is not None and node.entity_type == "chapter" and not node.body.strip():
            problems.error(
                f"{rel!r} has child documents and no body of its own, so it becomes a "
                "chapter with no page — there is nothing to comment on", path, lineno)

        archived = obj.get("archived")
        if archived is not None and not isinstance(archived, bool):
            problems.error("archived must be true or false", path, lineno)
        if archived and obj.get("reply_to") is not None:
            problems.error(
                "archived is only valid on a comment with no reply_to — BookStack "
                "archives whole threads, not individual replies", path, lineno)

        quote = obj.get("quote")
        if quote is not None and (not isinstance(quote, str) or not quote.strip()):
            problems.error("quote must be a non-empty string", path, lineno)
            quote = None
        if quote and node is not None:
            found = len(list(quote_re(quote).finditer(markdown_text(node.body))))
            if found == 0:
                problems.error(
                    f"quote {quote[:60]!r} does not appear in {rel} — quote the text as "
                    "it reads on the page, without markdown syntax", path, lineno)
            elif found > 1:
                problems.error(
                    f"quote {quote[:60]!r} appears {found} times in {rel}; lengthen it",
                    path, lineno)

        row = {
            "lineno": lineno, "doc": rel, "author": obj.get("author"),
            "created_at": created, "text": obj.get("text"),
            "id": obj.get("id"), "reply_to": obj.get("reply_to"),
            "quote": quote, "archived": bool(archived),
        }
        parsed.append(row)
        if isinstance(row["id"], str):
            by_handle.setdefault(row["id"], row)

    _check_replies(parsed, by_handle, path, problems)
    return parsed


def _check_replies(rows: list[dict], by_handle: dict[str, dict],
                   path: Path, problems: wl.Problems) -> None:
    for row in rows:
        target = row["reply_to"]
        if target is None:
            continue
        if not isinstance(target, str):
            problems.error("reply_to must be a string", path, row["lineno"])
            continue
        if target == row["id"]:
            problems.error("reply_to refers to the comment itself", path, row["lineno"])
            continue
        parent = by_handle.get(target)
        if parent is None:
            problems.error(f"reply_to {target!r} does not match any comment id",
                           path, row["lineno"])
            continue
        if parent["doc"] != row["doc"]:
            problems.error(
                f"reply_to {target!r} is on {parent['doc']!r}, but this comment is on "
                f"{row['doc']!r} — a reply must be on the same document",
                path, row["lineno"])
            continue
        if (row["created_at"] and parent["created_at"]
                and row["created_at"] < parent["created_at"]):
            problems.error(
                f"reply is older than the comment it answers ({target!r}); replies are "
                "created in date order, so this could never have happened",
                path, row["lineno"])

    # Depth and cycles. BookStack's own tree builder recurses without a bound.
    for row in rows:
        if row["reply_to"] == row["id"]:
            continue  # already reported as self-referential
        seen, node, depth = {row["id"]}, row, 0
        while node["reply_to"] is not None:
            parent = by_handle.get(node["reply_to"])
            if parent is None:
                break
            if parent["id"] in seen:
                problems.error(f"reply_to chain through {parent['id']!r} is circular",
                               path, row["lineno"])
                break
            seen.add(parent["id"])
            node, depth = parent, depth + 1
            if depth > MAX_REPLY_DEPTH:
                problems.error(
                    f"reply chain is deeper than {MAX_REPLY_DEPTH}", path, row["lineno"])
                break


def order_for_page(rows: list[dict]) -> list[dict]:
    """Creation order: by date, with the file's own order breaking ties.

    Validation guarantees a reply is never older than its parent, so this is
    also a parent-first ordering — which is what makes local_id resolvable.
    """
    return sorted(rows, key=lambda r: (r["created_at"], r["lineno"]))


def load_manifest(path: Path, problems: wl.Problems) -> dict[str, dict]:
    if not path.exists():
        problems.error(
            f"{path} not found — run ingest_docs.py first, it records which page "
            "each document became", path)
        return {}
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        problems.error(f"invalid JSON: {exc}", path)
        return {}
    if raw.get("version") != 1:
        problems.error(f"version must be 1, got {raw.get('version')!r}", path)
    return raw.get("pages", {})


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
                        help=f"doc path -> page id map written by ingest_docs.py "
                             f"(default: {docs.MANIFEST_NAME} beside --data-dir)")
    parser.add_argument("--replace", action="store_true",
                        help="delete existing comments on the affected pages first")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip the read-back checks after writing")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)
    docs_dir = args.data_dir / "docs"
    comments_path = args.data_dir / "comments.jsonl"
    manifest_path = args.manifest or (args.data_dir.parent / docs.MANIFEST_NAME)
    if not docs_dir.is_dir():
        raise SystemExit(f"{docs_dir} does not exist")

    wl.heading("Parsing")
    # The document tree is parsed only to resolve `doc` paths. Its own warnings
    # belong to ingest_docs.py, so they are collected separately and dropped —
    # re-reporting them on every comments run would train people to ignore them.
    tree_problems = wl.Problems(fail_fast=args.fail_fast)
    books = docs.load_collections(docs_dir / "collections.yaml", docs_dir, tree_problems)
    documents = docs.load_documents(docs_dir, books, identities, tree_problems)
    problems.errors.extend(tree_problems.errors)
    by_rel = {n.rel: n for n in documents}

    rows = load_comments(comments_path, by_rel, identities, problems)
    if args.collection:
        rows = [r for r in rows
                if by_rel.get(r["doc"]) is not None
                and by_rel[r["doc"]].collection_dir == args.collection]
    problems.raise_if_any()

    by_doc: dict[str, list[dict]] = {}
    for row in rows:
        by_doc.setdefault(row["doc"], []).append(row)
    by_doc = {doc: order_for_page(rs) for doc, rs in sorted(by_doc.items())}

    threads = sum(1 for r in rows if r["reply_to"] is None)
    quoted = sum(1 for r in rows if r["quote"])
    wl.ok(f"{len(rows)} comment(s) on {len(by_doc)} page(s), {threads} thread(s)")
    wl.ok(f"author(s): {', '.join(sorted({r['author'] for r in rows})) or '(none)'}")

    if args.dry_run:
        wl.heading("Dry run")
        for doc_rel, doc_rows in by_doc.items():
            for local_id, row in enumerate(doc_rows, start=1):
                detail = f"author={row['author']} at={row['created_at'].isoformat()}"
                if row["reply_to"]:
                    detail += f" reply_to={row['reply_to']}"
                if row["quote"]:
                    detail += f" quote={row['quote'][:40]!r}"
                if row["archived"]:
                    detail += " archived"
                wl.dry(f"comments.create page={doc_rel} local#{local_id} {detail}")
        archived = sum(1 for r in rows if r["archived"])
        if archived:
            wl.dry(f"then PUT /api/comments/<id> archived=true for {archived} comment(s)")
        wl.dry(f"then UPDATE comments SET created_at/created_by per item ({len(rows)} rows)")
        wl.dry(f"then re-apply UPDATE entities for {len(by_doc)} commented page(s)")
        wl.dry("then reattribute the activities feed so the dashboard shows the "
               "real authors and dates")
        if quoted:
            wl.dry(f"content_ref for {quoted} quote(s) is derived from the rendered HTML "
                   "at write time; offline they are only checked against the markdown "
                   "source, so this run does NOT prove they will resolve")
        wl.summarise(True, [
            f"{len(rows)} comment(s) on {len(by_doc)} page(s) validated",
            f"{quoted} quote-anchored",
        ])
        return 0

    token = world.env.get("BOOKSTACK_TOKEN", "")
    if not token or ":" not in token:
        raise SystemExit(
            "BOOKSTACK_TOKEN missing or malformed. Inside the world it is read "
            "from /etc/sweworld/bookstack-token; outside, set it in .env as "
            "<token_id>:<token_secret>.")
    api = docs.BookStack(world, token)

    manifest = load_manifest(manifest_path, problems)
    # Only worth reporting if the manifest itself loaded — otherwise every
    # document is "missing" and the real cause is buried.
    missing = [d for d in by_doc if d not in manifest] if manifest else []
    if missing:
        problems.error(
            f"{len(missing)} commented document(s) are not in the manifest, starting "
            f"with {missing[0]!r} — re-run ingest_docs.py", manifest_path)
    problems.raise_if_any()

    # Fetch every commented page once: the title confirms the manifest is not
    # left over from a database that has since been rebuilt, and the html is
    # what quotes resolve against.
    wl.heading("Resolving pages")
    pages: dict[str, dict] = {}
    for doc_rel in by_doc:
        entry = manifest[doc_rel]
        page = api.get(f"pages/{entry['page_id']}")
        if page.get("name") != entry["title"]:
            raise SystemExit(
                f"page {entry['page_id']} is {page.get('name')!r}, but the manifest says "
                f"{entry['title']!r} — the manifest is stale, re-run ingest_docs.py")
        text, spans = build_index(page.get("html", ""))
        pages[doc_rel] = {"id": entry["page_id"], "text": text, "spans": spans,
                          "entry": entry}
    wl.ok(f"{len(pages)} page(s) resolved from {manifest_path}")

    # Resolve every quote before creating anything. Failing halfway would leave
    # a half-commented page and no way to roll it back.
    ref_problems = wl.Problems(fail_fast=args.fail_fast)
    refs: dict[int, str] = {}
    for doc_rel, doc_rows in by_doc.items():
        page = pages[doc_rel]
        for row in doc_rows:
            if not row["quote"]:
                continue
            ref = resolve_ref(page["text"], page["spans"], row["quote"],
                              ref_problems, comments_path, row["lineno"])
            if ref:
                refs[row["lineno"]] = ref
    ref_problems.raise_if_any()
    if quoted:
        wl.ok(f"{quoted} quote(s) anchored to page content")

    admin_id = int(docs.sql("SELECT id FROM users WHERE id=1;") or 1)
    user_for = docs.make_user_resolver(identities, args.single_author, admin_id)

    if args.replace and pages:
        ids = ",".join(str(p["id"]) for p in pages.values())
        wl.warn(f"--replace: deleting existing comments on page(s) {ids}")
        docs.sql("DELETE FROM comments WHERE commentable_type='page' "
                 f"AND commentable_id IN ({ids});")

    wl.heading("Creating comments")
    created: list[tuple[int, dict]] = []
    for doc_rel, doc_rows in by_doc.items():
        local_by_handle: dict[str, int] = {}
        for row in doc_rows:
            payload: dict[str, Any] = {
                "page_id": pages[doc_rel]["id"],
                "html": to_html(row["text"]),
            }
            if row["lineno"] in refs:
                payload["content_ref"] = refs[row["lineno"]]
            if row["reply_to"]:
                parent_local = local_by_handle.get(row["reply_to"])
                if parent_local is None:
                    raise RuntimeError(
                        f"reply_to {row['reply_to']!r} was not created before its reply; "
                        "the date ordering invariant did not hold")
                payload["reply_to"] = parent_local
            result = api.post("comments", payload)
            if row["id"]:
                local_by_handle[row["id"]] = result["local_id"]
            created.append((result["id"], row))
            if args.verbose:
                wl.info(f"comment {result['id']} (local#{result['local_id']}) on {doc_rel}")
        wl.ok(f"{len(doc_rows)} comment(s) on {doc_rel}")

    archived = [(cid, row) for cid, row in created if row["archived"]]
    for comment_id, _ in archived:
        api.put(f"comments/{comment_id}", {"archived": True})
    if archived:
        wl.ok(f"{len(archived)} thread(s) archived")

    # After the archive PUTs, which would otherwise re-stamp updated_at.
    wl.heading("Correcting dates and authorship")
    for comment_id, row in created:
        docs.backdate_comment(comment_id, row["created_at"], user_for(row["author"]))
    wl.ok(f"{len(created)} comment(s) backdated")

    # Belt and braces. BookStack 25.11 does not touch a page's updated_at when
    # a comment is added — measured, not assumed — so this pass currently
    # rewrites the values it finds. It stays because the failure it guards
    # against is invisible: a future version that does bump the parent would
    # leave every commented page reading "updated moments ago", and nothing
    # here would fail. Four statements is a cheap price for not having to
    # re-check that on every upgrade.
    for doc_rel, page in pages.items():
        entry = page["entry"]
        created_at = wl.parse_ts(entry["created_at"])
        updated_at = wl.parse_ts(entry["updated_at"]) or created_at
        docs.backdate(page["id"], created_at, user_for(entry["author"]), updated_at)
    wl.ok(f"{len(pages)} commented page(s) re-settled")

    # Commenting writes two rows into the activity feed per comment, owned by
    # the token holder and stamped now. That feed is the dashboard's main
    # content, so leaving it would put "World Admin commented on X, 3 minutes
    # ago" in front of every reader of the wiki.
    revisions, activities = docs.resettle_history()
    wl.ok(f"{revisions} revision(s) and {activities} activity row(s) reattributed")

    if not args.no_verify:
        verify_comments(pages, by_doc, len(created), quoted)

    wl.summarise(False, [
        f"{len(created)} comment(s) on {len(pages)} page(s)",
        f"browse at {world.url('docs')}",
    ])
    return 0


def verify_comments(pages: dict[str, dict], by_doc: dict[str, list[dict]],
                    expected: int, quoted: int) -> None:
    """Read the comments back and check what the API cannot report.

    Warnings rather than errors: the world is already written by this point, and
    a mismatch here is something to look at, not a reason to fail the bake.
    """
    wl.heading("Verifying")
    if not pages:
        # `IN ()` is a syntax error, not an empty set. With no wiki to comment
        # on there is nothing to check, and this pass is explicitly the one that
        # warns rather than fails — so it must not be what stops the bake.
        wl.info("no pages, so no comments to verify")
        return
    ids = ",".join(str(p["id"]) for p in pages.values())
    scope = f"commentable_type='page' AND commentable_id IN ({ids})"

    total = int(docs.sql(f"SELECT count(*) FROM comments WHERE {scope};") or 0)
    if total != expected:
        wl.warn(f"expected {expected} comment(s) in the database, found {total}")

    # The single highest-signal check: if the backdating pass silently did
    # nothing, every row is stamped now and this is non-zero.
    fresh = int(docs.sql(
        f"SELECT count(*) FROM comments WHERE {scope} "
        "AND created_at > NOW() - INTERVAL 1 HOUR;") or 0)
    if fresh:
        wl.warn(f"{fresh} comment(s) are still stamped with the ingestion time")

    expected_replies = sum(1 for rs in by_doc.values() for r in rs if r["reply_to"])
    replies = int(docs.sql(
        f"SELECT count(*) FROM comments WHERE {scope} AND parent_id IS NOT NULL;") or 0)
    if replies != expected_replies:
        wl.warn(f"expected {expected_replies} threaded repl(ies), found {replies}")

    refs = int(docs.sql(
        f"SELECT count(*) FROM comments WHERE {scope} AND content_ref <> '';") or 0)
    if refs != quoted:
        wl.warn(f"expected {quoted} anchored comment(s), found {refs}")

    for doc_rel, page in pages.items():
        rows = docs.sql(
            f"SELECT local_id FROM comments WHERE commentable_type='page' "
            f"AND commentable_id={page['id']} ORDER BY local_id;")
        local_ids = [int(v) for v in rows.splitlines() if v]
        if local_ids != list(range(1, len(local_ids) + 1)):
            wl.warn(f"local_id values on {doc_rel} are not 1..n: {local_ids}")

    wl.ok("read-back checks complete")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\n\033[31mfailed\033[0m  {exc}", file=sys.stderr)
        raise SystemExit(1)
