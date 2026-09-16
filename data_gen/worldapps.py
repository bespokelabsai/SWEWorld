#!/usr/bin/env python3
"""The apps this company uses, as tools its people can actually reach.

`bespoke_user` deliberately knows nothing about products: an app answers three
questions about itself — what namespace its tools live under, what they are
called, and how to build an MCP server bound to one caller — and the engine asks
nothing else. Everything specific to this world lives here.

These write **the ingest schemas directly**. A page written in a conversation
lands as `docs/<collection>/<page>.md` with the frontmatter `ingest_docs.py`
parses, and mail lands as RFC-5322 with an `index.jsonl` line beside it. The
alternative — a private format plus a translation step — is a second place for
the schema to be wrong, and the schemas are strict enough that the second place
is where it would go unnoticed.

Nothing here is a simulation of an app. A page exists or it does not, which is
the property that makes `sim_engine.artifact_audit` meaningful: it asks the
store what it holds rather than asking a persona what they did.
"""
from __future__ import annotations

import datetime as dt
import email
import email.header
import email.utils
import json
import re
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

# Everything the ingest reads wants an explicit UTC offset — a naive timestamp
# is a hard error in worldlib.parse_ts, not a warning.
UTC = dt.timezone.utc


def slug(text: str, fallback: str = "untitled") -> str:
    out = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return out or fallback


def ok(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


class Clock:
    """What the stores stamp things with — the engine's turn cursor when it has one.

    It used to advance "alongside rather than in lockstep": a private counter
    that added seven minutes per call from the day's start, while the engine
    computed each turn's time in its own loop and never handed it out. Same day
    and same order, different instant — which read as harmless until the corpus
    was checked across artifacts. Every one of the 108 wiki pages landed between
    09:14 and 10:38 on thirteen distinct clock values, because that is where
    `start + 7k minutes` puts them, and none of those values had anything to do
    with the conversation that produced the page. A channel opening at 09:00
    with "the design doc is up on the wiki" was then announcing a file stamped
    09:14, and 96 chat messages contradicted a page's `created_at` that way.

    So: `set_now()` pins this to the engine's cursor for the turn about to run,
    and a store stamps inside the turn that actually called it. The seven-minute
    stride survives only as the fallback for a caller that drives nothing —
    `phase4_run` without the engine, and the tests.

    Syncing the clocks removes the arbitrary drift. It does NOT make a persona
    write the page before announcing it, and nothing here can: that is what
    `scripts/check_corpus.py --fix` reconciles afterwards.
    """

    def __init__(self, start: dt.datetime | None = None):
        self.at = start
        self._turn: dt.datetime | None = None

    def set_day(self, when: dt.datetime) -> None:
        # A new day drops the turn cursor: carrying yesterday's last turn into
        # today would stamp the morning's first page with last night's time.
        self.at = when
        self._turn = None

    def set_now(self, when: dt.datetime) -> None:
        """Pin to the engine's wall-clock cursor for the turn about to run."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        self._turn = when
        self.at = when

    def stamp(self) -> dt.datetime:
        if self._turn is not None:
            # Seconds, not the seven-minute stride: a persona that writes a page
            # and mails about it in one turn needs two ordered stamps, and both
            # belong inside the turn that made them.
            self._turn += dt.timedelta(seconds=1)
            self.at = self._turn
            return self.at
        self.at = (self.at or dt.datetime.now(UTC)) + dt.timedelta(minutes=7)
        return self.at

    def iso(self) -> str:
        when = self.stamp()
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        return when.isoformat(timespec="seconds")


class Store:
    """What every app here has in common: a place to write and a memory of it."""

    app = "app"
    summary = ""

    def __init__(self, root: Path, clock: Clock):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._made: list[dict] = []
        self._touched: list[dict] = []

    # -- what the engine asks of an app ------------------------------------
    def tool_names(self) -> list[str]:
        raise NotImplementedError

    def mcp_server(self, uid: str, clock):
        raise NotImplementedError

    def inventory(self) -> list[dict]:
        """What exists now. `artifact_audit` reads this to decide whether a
        planned document was really written, which is why it is a record of
        files on disk and not of intentions."""
        return list(self._made)

    def activity(self) -> list[dict]:
        return list(self._touched)

    def drop_day(self, date: str) -> int:
        """Delete what an earlier pass wrote on `date`, before the day is
        simulated again. Nothing, for an app that keeps nothing on disk."""
        return 0

    # -- bookkeeping --------------------------------------------------------
    def _record(self, *, kind: str, ident: str, title: str, by: str,
                action: str, ts: str, **extra) -> dict:
        row = {"kind": kind, "id": ident, "title": title, "by": by,
               "ts": ts, "action": action, **extra}
        self._made.append(row)
        return row

    def _touch(self, uid: str, name: str, target: str, ts: str) -> None:
        self._touched.append({"seq": len(self._touched) + 1, "ts": ts,
                              "uid": uid, "tool": name, "target": target})


# =============================================================================
# The wiki
# =============================================================================
class Wiki(Store):
    """BookStack, as `ingest_docs.py` will read it back.

    A collection is a directory and a book; nesting is a directory beside a
    sibling `.md` of the same name. Pages carry `title` / `author` /
    `created_at` frontmatter and nothing else that matters — the rest of the
    fields the schema allows are accepted and never read, so they are not
    written.
    """

    app = "wiki"
    # Where a page goes when it is filed under nothing at all.
    DEFAULT_SHELF = {
        "meeting-notes": "meetings", "postmortem": "incidents",
        "release-notes": "releases", "onboarding": "onboarding",
    }
    summary = "the company wiki. Pages are grouped into collections."

    # Descriptions for the shelves the doc plan knows about. A collection a
    # persona invents gets no description rather than a guessed one.
    SHELF_BLURB = {
        "engineering": "Design docs, plans, runbooks and handovers.",
        "meetings": "Notes from recurring and one-off meetings.",
        "incidents": "Postmortems and incident write-ups.",
        "releases": "Release notes, version by version.",
        "onboarding": "How the team works, for people who just joined.",
        "design": "Product and interface design.",
    }

    def __init__(self, root: Path, clock: Clock, *, collections: dict[str, str],
                 scrub=None, planned_comments: list[dict] | None = None,
                 doc_titles: dict[str, str] | None = None):
        super().__init__(root, clock)
        # The plan says which comment replies to which, by ids of its own. The
        # tool a persona calls carries only a page and some text, so the store
        # matches the call back to the plan — by who is writing and which page
        # — and takes the planned id. Otherwise `reply_to` names a comment that
        # was never minted and the thread comes out flat.
        self._comments: dict[str, str] = {}     # id -> text, for the clue gate
        self.planned_comments = list(planned_comments or [])
        self.doc_titles = dict(doc_titles or {})
        self.docs = self.root / "docs"
        self.docs.mkdir(parents=True, exist_ok=True)
        self.collections = collections
        self.scrub = scrub or (lambda text: text)
        self.comments = self.root / "comments.jsonl"
        self._pages: dict[str, dict] = {}

    def tool_names(self) -> list[str]:
        return ["write_page", "read_page", "list_pages", "comment_on_page"]

    # -- the operations, callable from python as well as from a tool --------
    def manifest(self) -> str:
        """`collections.yaml`, written from the directories that actually have
        pages in them. `ingest_docs.py` requires the file and errors on a `dir`
        that does not exist, so it is built from the tree rather than from the
        plan — a collection nobody wrote into is not a book."""
        lines = ["version: 1", "collections:"]
        for shelf in sorted(d.name for d in self.docs.iterdir()
                            if d.is_dir() and any(d.glob("*.md"))):
            lines.append(f"  - dir: {shelf}")
            lines.append(f"    name: {shelf.replace('-', ' ').title()}")
            blurb = self.SHELF_BLURB.get(shelf)
            if blurb:
                lines.append(f"    description: {json.dumps(blurb)}")
        text = "\n".join(lines) + "\n"
        (self.docs / "collections.yaml").write_text(text, encoding="utf-8")
        return text

    def _shelf_help(self) -> str:
        have = sorted(self.collections)
        return ("the wiki has no collections yet." if not have else
                "the ones that exist are " + ", ".join(have) + ".")

    def shelve(self, collection: str, kind: str = "", when: str = "") -> str:
        """Which collection a page goes in.

        A name we already know wins. A name we do not is *made* — someone
        filing the first postmortem when no incidents shelf exists yet puts
        one up rather than dropping the page on whatever shelf is nearest,
        which is what the old fallback did: it took `next(iter(...))`, so
        every unrecognised name landed in whichever collection the doc plan
        happened to mention first. Only a page filed under nothing at all
        falls back, and it falls back on its own kind.
        """
        want = slug(collection, "")
        if want:
            if want not in self.collections:
                self.collections[want] = ""
                self._record(kind="collection", ident=want, title=want,
                             by="", action="create",
                             ts=when or self.clock.iso())
            return want
        return self.DEFAULT_SHELF.get(kind, "engineering")

    def write(self, *, uid: str, title: str, body: str, collection: str,
              ts: str | None = None, kind: str = "") -> str:
        when = ts or self.clock.iso()
        book = self.shelve(collection, kind, when)
        rel = f"{book}/{slug(title)}.md"
        path = self.docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        # The body is scrubbed with the DOCUMENT scrubber, which splits on code
        # fences and works line by line, so a markdown rule or a table
        # separator survives. The chat-side one flattens both.
        text = self.scrub(body or "").strip()
        path.write_text(
            "---\n"
            f"title: {json.dumps(title)}\n"
            f"author: {uid}\n"
            f"created_at: {when}\n"
            "---\n\n" + text + "\n", encoding="utf-8")
        self._pages[rel] = {"title": title, "author": uid, "body": text}
        self._record(kind="doc", ident=rel, title=title, by=uid,
                     action="write", ts=when, doc_kind=kind, path=str(path))
        return rel

    def claim_comment(self, uid: str, rel: str) -> dict:
        """The planned comment this call is fulfilling, if it is fulfilling one.

        Matched on the page, loosely. An exact `slug(plan title) == file stem`
        test looks right and fails in practice: the persona writes the page's
        headline themselves, so the file is named after THEIR title, not the
        plan's — "WS-055 release engineering" against "ws-055-release-
        engineering-ci-test-suite". A missed match mints an id of our own, and
        then the reply the plan says answers this comment names a parent that
        does not exist, which the ingest rejects.
        """
        stem = Path(rel).stem
        mine = [c for c in self.planned_comments
                if not c.get("_used") and c.get("author") == uid]
        for com in mine:                       # the exact name first
            if slug(self.doc_titles.get(com.get("doc", ""), "")) == stem:
                com["_used"] = True
                return com
        words = {w for w in stem.split("-") if len(w) > 3}
        for com in mine:                       # then a shared-word overlap
            theirs = {w for w in slug(
                self.doc_titles.get(com.get("doc", ""), "")).split("-")
                if len(w) > 3}
            if theirs and len(words & theirs) >= max(2, len(theirs) // 2):
                com["_used"] = True
                return com
        return {}

    def rehydrate(self) -> int:
        """Load a corpus already on disk back into the store.

        A run reports what it wrote from memory, so re-judging a FINISHED
        corpus would otherwise see an empty wiki and call every page it ever
        made a page nobody wrote. The frontmatter carries author and date,
        which is everything the audit matches on.
        """
        for path in sorted(self.docs.glob("*/*.md")):
            rel = f"{path.parent.name}/{path.name}"
            if rel in self._pages:
                continue
            meta, body = self._frontmatter(path)
            title = str(meta.get("title") or path.stem)
            by = str(meta.get("author") or "")
            self._pages[rel] = {"title": title, "author": by, "body": body.strip()}
            self._record(kind="doc", ident=rel, title=title, by=by,
                         action="write", ts=str(meta.get("created_at") or ""),
                         path=str(path))
        # Comments too, or an audit of a finished corpus reads a wiki where
        # nobody ever commented — and reports every comment clue as carried by
        # nothing, including the ones that were written correctly.
        if self.comments.exists():
            for raw in self.comments.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if not raw or raw.startswith("#"):
                    continue
                row = json.loads(raw)
                if row["id"] in self._comments:
                    continue
                self._comments[row["id"]] = row.get("text", "")
                page = (self._pages.get(row["doc"]) or {}).get("title") \
                    or row["doc"]
                self._record(kind="comment", ident=row["id"],
                             title=f"comment on {page}",
                             by=row.get("author", ""), action="comment",
                             ts=row.get("created_at", ""))
        return len(self._pages)

    @staticmethod
    def _frontmatter(path: Path) -> tuple[dict, str]:
        """A page's frontmatter fields and its body, as `write` lays them out."""
        head, _, body = path.read_text(encoding="utf-8").partition("---\n")[2] \
            .partition("\n---\n")
        meta = {}
        for line in head.splitlines():
            key, _, value = line.partition(":")
            if value.strip():
                try:
                    meta[key.strip()] = json.loads(value.strip())
                except ValueError:
                    meta[key.strip()] = value.strip()
        return meta, body

    def drop_day(self, date: str) -> int:
        """Delete the pages and comments an earlier pass wrote on `date`.

        By `created_at`, which `write` restamps on every rewrite, so a page
        first written days before and rewritten on `date` goes too — its file
        only ever held the `date` version. Overwriting in place is not enough:
        a persona files the page where they like, and a second pass that chose
        another book is how one page came to sit in both `design/` and
        `engineering/`.
        """
        gone = 0
        for path in sorted(self.docs.glob("*/*.md")):
            if str(self._frontmatter(path)[0].get("created_at", "")).startswith(date):
                path.unlink()
                gone += 1
        if self.comments.exists():
            lines = self.comments.read_text(encoding="utf-8").splitlines(keepends=True)
            keep = [raw for raw in lines if not raw.strip() or raw.startswith("#")
                    or not str(json.loads(raw).get("created_at", "")).startswith(date)]
            if len(keep) < len(lines):
                self.comments.write_text("".join(keep), encoding="utf-8")
                gone += len(lines) - len(keep)
        return gone

    def written(self, doc_id: str) -> str:
        """When this PLANNED page was actually written, or "" if nobody has.

        Phase 2 plans a title; the persona who writes it files it under
        whichever collection they think it belongs in, so the slug is the only
        stable link between the plan and the file. Read off disk rather than
        `_pages`, which only holds what this process wrote — a page written on
        Monday has to still be there on Thursday.

        This exists so the grounding can tell people the truth. A doc used to
        arrive on the table as a title and an owner and nothing else, and a
        persona with no way to tell a planned page from a written one announced
        it as up: 96 chat messages in the shipped corpus contradicted a page's
        own `created_at` that way.
        """
        stem = slug(self.doc_titles.get(doc_id, "") or doc_id)
        for path in sorted(self.docs.glob(f"*/{stem}.md")):
            meta, _ = self._frontmatter(path)
            return str(meta.get("created_at") or "yes")
        return ""

    def read(self, rel: str) -> str:
        page = self._pages.get(rel)
        if page:
            return page["body"]
        path = self.docs / rel
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def find(self, needle: str) -> str | None:
        want = slug(needle)
        for rel, page in self._pages.items():
            if want and (want in slug(rel) or want in slug(page["title"])):
                return rel
        return None

    def comment(self, *, uid: str, rel: str, text: str,
                ts: str | None = None, reply_to: str = "",
                ident: str = "") -> None:
        """One line on `comments.jsonl`.

        No `quote`. The field is optional, and a quote has to appear exactly
        once in the *rendered* projection of the page — code fences deleted,
        markdown stripped — which is not a property anything writing prose can
        promise. A comment with no quote is a page-level comment, which is what
        most comments are anyway.
        """
        when = ts or self.clock.iso()
        # The plan's own id when there is one: it says `<doc>-c1` replies to
        # `<doc>-c0`, and a minted `c-<slug>-<n>` is a name that `reply_to`
        # cannot reach, so the thread would come out flat.
        row = {"id": ident or f"c-{slug(rel)}-{len(self._made)}", "doc": rel,
               "author": uid, "created_at": when, "text": text.strip()}
        if reply_to:
            row["reply_to"] = reply_to
        self._comments[row["id"]] = row["text"]
        with self.comments.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def rewrite_comment(self, ident: str, text: str) -> bool:
        """Replace one comment's text on disk as well as in memory.

        The in-memory dict is what the clue gate reads and `comments.jsonl` is
        what the ingest reads. Updating only the first made a repair that the
        gate could see and the world could not.
        """
        if not self.comments.exists():
            return False
        rows, hit = [], False
        for raw in self.comments.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            row = json.loads(raw)
            if row.get("id") == ident:
                row["text"] = text
                hit = True
            rows.append(row)
        if hit:
            self.comments.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                encoding="utf-8")
            self._comments[ident] = text
        return hit
        page = (self._pages.get(rel) or {}).get("title") or rel
        self._record(kind="comment", ident=row["id"],
                     title=f"comment on {page}", by=uid, action="comment",
                     ts=when)

    # -- the tools ----------------------------------------------------------
    def mcp_server(self, uid: str, clock, writer=None):
        """`writer` is the persona's own document writer, handed over by the
        engine when this parameter is present. Using it is the whole reason a
        page reads like a document instead of like a long Slack message: the
        persona's chat voice rules never touch it."""

        # The persona can only file a page correctly if it knows what the
        # shelves are called, so the live list goes in the description rather
        # than a fixed sentence that drifts from the corpus.
        @tool("write_page",
              "Write a new page on the company wiki. `collection` is which "
              "collection it belongs in — " + self._shelf_help() + " If none "
              "of them fit, name the collection you think it should live in "
              "and it will be created.", {
            "title": str, "collection": str, "kind": str, "brief": str})
        async def write_page(args):
            title = (args.get("title") or "").strip() or "Untitled"
            brief = (args.get("brief") or "").strip()
            kind = (args.get("kind") or "design_doc").strip()
            body = brief
            if writer is not None:
                body = await _maybe_await(writer(
                    brief, title=title, kind=kind,
                    written_on=self.clock.iso()[:10]))
            rel = self.write(uid=uid, title=title, body=body, kind=kind,
                             collection=(args.get("collection") or "").strip())
            self._touch(uid, "write_page", rel, self.clock.iso())
            return ok(f"Written to the wiki as {rel}.")

        @tool("read_page", "Open a wiki page and read what it says.",
              {"page": str})
        async def read_page(args):
            rel = self.find(args.get("page") or "")
            if not rel:
                return ok("No page by that name. Try list_pages.")
            self._touch(uid, "read_page", rel, self.clock.iso())
            body = self.read(rel)
            return ok(f"{rel}\n\n{body[:4000]}")

        @tool("list_pages", "List the pages on the wiki.", {})
        async def list_pages(args):
            if not self._pages:
                return ok("The wiki has no pages yet.")
            return ok("\n".join(f"{rel} — {p['title']} (by {p['author']})"
                                for rel, p in sorted(self._pages.items())))

        @tool("comment_on_page", "Leave a comment on a wiki page.",
              {"page": str, "text": str})
        async def comment_on_page(args):
            rel = self.find(args.get("page") or "")
            if not rel:
                return ok("No page by that name. Try list_pages.")
            plan = self.claim_comment(uid, rel)
            self.comment(uid=uid, rel=rel, text=args.get("text") or "",
                         ident=plan.get("id", ""),
                         reply_to=plan.get("reply_to") or "")
            self._touch(uid, "comment_on_page", rel, self.clock.iso())
            return ok(f"Commented on {rel}.")

        return create_sdk_mcp_server(
            name=self.app, version="1.0.0",
            tools=[write_page, read_page, list_pages, comment_on_page])


# =============================================================================
# Mail
# =============================================================================
class Mail(Store):
    """Internal mail, as `ingest_mail.py` will read it back.

    One message becomes several files: the sender keeps a copy in `Sent` and
    every recipient gets one in `INBOX`, each with its own `index.jsonl` line.
    That is not duplication for its own sake — it is what a mail store actually
    holds, and the ingest requires every `.eml` under the tree to be indexed.

    Threading is `Message-ID` and `In-Reply-To`. There is no thread field
    anywhere; a reply is a message that names its parent.
    """

    app = "email"
    summary = "internal company email."

    def __init__(self, root: Path, clock: Clock, *, domain: str,
                 addresses: dict[str, str]):
        super().__init__(root, clock)
        self.dir = self.root / "emails"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.index = self.dir / "index.jsonl"
        self.domain = domain
        self.addresses = addresses            # persona id -> mailbox address
        self._threads: dict[str, dict] = {}   # subject key -> last message
        # Numbered on from what is already on disk. A counter restarting at 0 in
        # every process handed a later pass an earlier file's name, so it
        # overwrote that file and the index listed the path twice — 33 paths in
        # the corpus run.
        self._n = max((int(m.group()) for row in self._rows()
                       if (m := re.match(r"\d+", Path(row["path"]).name))), default=0)

    def tool_names(self) -> list[str]:
        return ["send_mail", "reply_to_mail", "check_inbox", "read_mail"]

    def address(self, uid: str) -> str:
        return self.addresses.get(uid) or f"{uid}@{self.domain}"

    def send(self, *, uid: str, to: list[str], subject: str, body: str,
             ts: str | None = None, in_reply_to: str = "") -> str:
        when = ts or self.clock.iso()
        stamp = dt.datetime.fromisoformat(when)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=UTC)
        # Only people who exist. A persona addressed one to "team", which is
        # how anybody writes mail and is not how this world stores it: the
        # ingest checks every mailbox against the roster and refuses the file.
        # Unknown names are dropped here rather than written and rejected later.
        recipients = [r for r in to if r and r != uid and r in self.addresses]
        if not recipients:
            return ""

        note = EmailMessage()
        note["From"] = self.address(uid)
        note["To"] = ", ".join(self.address(r) for r in recipients)
        note["Subject"] = subject
        # RFC 5322 in the header, ISO in the index. The two formats are not
        # interchangeable and the ingest checks both.
        note["Date"] = format_datetime(stamp)
        mid = make_msgid(domain=self.domain)
        note["Message-ID"] = mid
        if in_reply_to:
            note["In-Reply-To"] = in_reply_to
            note["References"] = in_reply_to
        note.set_content(body.strip() + "\n")

        self._n += 1
        name = f"{self._n:04d}-{slug(subject, 'message')[:48]}.eml"
        for who, folder in [(uid, "Sent")] + [(r, "INBOX") for r in recipients]:
            box = self.address(who)
            path = self.dir / box / folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes(note))
            with self.index.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "path": f"{box}/{folder}/{name}", "mailbox": box,
                    "folder": folder, "date": when,
                    "flags": ["\\Seen"] if folder == "Sent" else [],
                }, ensure_ascii=False) + "\n")

        self._threads[slug(subject)] = {"mid": mid, "subject": subject,
                                        "from": uid, "to": recipients,
                                        "body": body, "ts": when}
        # `mail`, not `email`, because that is the word the PLAN uses for this
        # kind of artifact and `sim_engine.artifact_audit` compares kinds as raw
        # strings. It normalises the verb (a plan's "write" matches a mailbox's
        # "send" through `_PRODUCE`) but has no synonym table for kinds, so one
        # word apart is a total miss: a sent mail reported as never made, and —
        # worse, because it is silent — `unmet_creates` holding the channel open
        # for an obligation its owner had already discharged.
        self._record(kind="mail", ident=mid, title=subject, by=uid,
                     action="reply" if in_reply_to else "send", ts=when,
                     to=", ".join(recipients))
        return mid

    def _rows(self) -> list[dict]:
        """The index, parsed, minus blank lines and `#` comments."""
        if not self.index.exists():
            return []
        return [json.loads(raw) for raw in
                self.index.read_text(encoding="utf-8").splitlines()
                if raw.strip() and not raw.strip().startswith("#")]

    def drop_day(self, date: str) -> int:
        """Delete every copy of the mail an earlier pass sent on `date`.

        Matched on the index's `date`, which is the simulated day. Every copy,
        because each has its own line: the sender's `Sent` and one `INBOX` per
        recipient, all under the same file name.
        """
        if not self.index.exists():
            return 0
        lines = self.index.read_text(encoding="utf-8").splitlines(keepends=True)
        keep = []
        for raw in lines:
            if raw.strip() and not raw.strip().startswith("#"):
                row = json.loads(raw)
                if str(row.get("date", "")).startswith(date):
                    (self.dir / row["path"]).unlink(missing_ok=True)
                    continue
            keep.append(raw)
        if len(keep) < len(lines):
            self.index.write_text("".join(keep), encoding="utf-8")
        return len(lines) - len(keep)

    def extend(self, mid: str, said: str) -> int:
        """Append sentences to a message already sent, in every copy of it.

        One message is several files — the sender's `Sent` copy and one `INBOX`
        copy per recipient — so a repair that edits only the thread record in
        memory would leave the corpus disagreeing with itself. Every `.eml`
        carrying this Message-ID is rewritten, and the ingest reads the files.
        """
        touched = 0
        for path in sorted((self.root / "emails").rglob("*.eml")):
            text = path.read_text(encoding="utf-8")
            if mid not in text:
                continue
            head, sep, body = text.partition("\n\n")
            if not sep:
                continue
            path.write_text(head + sep + body.rstrip() + "\n\n" + said + "\n",
                            encoding="utf-8")
            touched += 1
        for thread in self._threads.values():
            if thread.get("mid") == mid:
                thread["body"] = thread.get("body", "").rstrip() + "\n\n" + said
        return touched

    def rehydrate(self) -> int:
        """Load sent mail already on disk back into the store.

        Only the sender's own copy: every recipient holds a duplicate of the
        same message, and counting those would report one mail as several.
        """
        seen = 0
        for row in self._rows():
            if (row.get("folder") or "") != "Sent":
                continue
            path = self.root / "emails" / row["path"]
            if not path.exists():
                continue
            msg = email.message_from_string(path.read_text(encoding="utf-8"))
            # A Subject with a non-ASCII character is MIME-encoded and folded
            # across lines, so the raw header reads
            # `week of Jan 13 =?utf-8?b?4oCU?= v0.1.15 and\n v0.1.15...`.
            # Compared against the plan's title that matches nothing, and the
            # artifact was reported as never sent.
            subject = " ".join(str(email.header.make_header(
                email.header.decode_header(msg.get("Subject", "")))).split())
            # parseaddr, not a split: "Emil Brandvold <emil@world.local>"
            # split on "@" gives "Emil Brandvold <emil", which matches no
            # persona, so every message with a display name was attributed to
            # nobody and its clues read as carried by nothing.
            uid = email.utils.parseaddr(msg.get("From", ""))[1].split("@")[0]
            body = msg.get_payload(decode=True)
            body = body.decode("utf-8", "replace") if body else msg.get_payload()
            # Keyed by Message-ID, not by subject. A thread is several
            # messages by several people, and subject-keying kept exactly one
            # of them — so a clue planted on the fourth message was judged
            # against the first, which contained none of it and read as 0
            # characters of evidence.
            key = msg.get("Message-ID", "") or slug(subject)
            if key in self._threads:
                continue
            self._threads[key] = {
                "mid": msg.get("Message-ID", ""), "subject": subject,
                "from": uid, "to": [a.strip() for a in
                                    msg.get("To", "").split(",") if a.strip()],
                "body": body or "", "ts": row.get("date", "")}
            self._record(kind="mail", ident=msg.get("Message-ID", ""),
                         title=subject, by=uid, action="send",
                         ts=row.get("date", ""), to=msg.get("To", ""))
            seen += 1
        return seen

    def inbox_of(self, uid: str) -> list[dict]:
        return [t for t in self._threads.values() if uid in t["to"]]

    def mcp_server(self, uid: str, clock):
        @tool("send_mail", "Send an email to colleagues.",
              {"to": str, "subject": str, "body": str})
        async def send_mail(args):
            asked = [t.strip().split("@")[0] for t in
                     (args.get("to") or "").replace(";", ",").split(",") if t.strip()]
            real = [t for t in asked if t in self.addresses and t != uid]
            unknown = [t for t in asked if t not in self.addresses]
            if not real:
                # Told, not silently swallowed: the persona can address it to
                # somebody who exists instead, which is what a bounce is for.
                return ok(f"No such recipient: {', '.join(unknown) or '(nobody named)'}. "
                          f"Address it to one of: {', '.join(sorted(self.addresses))}.")
            subject = (args.get("subject") or "").strip() or "(no subject)"
            self.send(uid=uid, to=real, subject=subject, body=args.get("body") or "")
            self._touch(uid, "send_mail", subject, self.clock.iso())
            note = (f" ({', '.join(unknown)} is not a person here)" if unknown else "")
            return ok(f"Sent \"{subject}\" to {', '.join(real)}.{note}")

        @tool("reply_to_mail", "Reply to a message in your inbox.",
              {"subject": str, "body": str})
        async def reply_to_mail(args):
            key = slug(args.get("subject") or "")
            parent = self._threads.get(key) or next(
                (t for k, t in self._threads.items() if key and key in k), None)
            if parent is None:
                return ok("No message with that subject in your mail.")
            subject = parent["subject"]
            self.send(uid=uid, to=[parent["from"]] + parent["to"],
                      subject=subject if subject.lower().startswith("re:")
                      else f"Re: {subject}",
                      body=args.get("body") or "", in_reply_to=parent["mid"])
            self._touch(uid, "reply_to_mail", subject, self.clock.iso())
            return ok(f"Replied to \"{subject}\".")

        @tool("check_inbox", "List the mail waiting for you.", {})
        async def check_inbox(args):
            mine = self.inbox_of(uid)
            if not mine:
                return ok("Your inbox is empty.")
            return ok("\n".join(f"{t['ts'][:16]}  {t['from']}: {t['subject']}"
                                for t in mine))

        @tool("read_mail", "Read one message from your inbox.", {"subject": str})
        async def read_mail(args):
            key = slug(args.get("subject") or "")
            got = next((t for k, t in self._threads.items() if key and key in k),
                       None)
            if got is None:
                return ok("No message with that subject.")
            self._touch(uid, "read_mail", got["subject"], self.clock.iso())
            return ok(f"From {got['from']}, {got['ts'][:16]}\n"
                      f"Subject: {got['subject']}\n\n{got['body'][:3000]}")

        return create_sdk_mcp_server(
            name=self.app, version="1.0.0",
            tools=[send_mail, reply_to_mail, check_inbox, read_mail])


# =============================================================================
# The forge, read-only
# =============================================================================
class Forge(Store):
    """The issues and pull requests that are already in Gitea.

    Read-only on purpose. The forge record is the real project's, ingested by
    `scripts/ingest_forge.py`; letting a persona open one is the difference
    between citing a pull request and inventing one, and nothing in a
    conversation should be able to write to it.
    """

    app = "issues"
    summary = "the curator repository's issues and pull requests, read-only."
    linkable = True

    def __init__(self, root: Path, clock: Clock, *, items: list[dict]):
        super().__init__(root, clock)
        self.items = {int(i["number"]): i for i in items
                      if i.get("kind") != "gap" and i.get("number")}

    def tool_names(self) -> list[str]:
        return ["find_issue", "read_issue"]

    def visible(self) -> dict:
        """The issues and pull requests that exist TODAY.

        Neither tool used to consult the clock, so every item was readable on
        every day: 731 of them are dated and they run to 2026-08-07, which meant
        somebody simulating November 2024 could open a dependency bump from
        twenty-one months in their own future and quote it back. A forge with no
        sense of time is a worse lie than no forge at all.
        """
        today = self.clock.iso()[:10]
        out = {}
        for number, item in self.items.items():
            made = item.get("created")
            if isinstance(made, (int, float)):
                made = dt.datetime.utcfromtimestamp(made).date().isoformat()
            if not made or str(made)[:10] <= today:
                out[number] = item
        return out

    def mcp_server(self, uid: str, clock):
        @tool("find_issue", "Search issues and pull requests by words in the "
                            "title.", {"words": str})
        async def find_issue(args):
            want = {w for w in slug(args.get("words") or "").split("-") if len(w) > 3}
            if not want:
                return ok("Say a word or two from the title.")
            hits = [i for i in self.visible().values()
                    if want & set(slug(i.get("title") or "").split("-"))]
            if not hits:
                return ok("Nothing matches.")
            return ok("\n".join(f"#{i['number']} ({i['kind']}) {i['title']}"
                                for i in hits[:10]))

        @tool("read_issue", "Read one issue or pull request by number.",
              {"number": int})
        async def read_issue(args):
            item = self.visible().get(int(args.get("number") or 0))
            if item is None:
                return ok("No such issue or pull request.")
            self._touch(uid, "read_issue", f"#{item['number']}", self.clock.iso())
            return ok(f"#{item['number']} ({item['kind']}) {item['title']}\n\n"
                      f"{(item.get('body') or '')[:2500]}")

        return create_sdk_mcp_server(name=self.app, version="1.0.0",
                                     tools=[find_issue, read_issue])


# =============================================================================
# Repository
# =============================================================================
class Repo(Store):
    """The curator repository, as it stood on the day being simulated.

    Before this existed the only thing a persona could learn about the code was
    an issue TITLE and the first 2500 characters of its body — `Forge` reads the
    issue record, never the tree. So every snippet in the corpus was the model's
    idea of what curator looks like, and a reviewer quoting `cache_stats()` had
    no way to know whether that function was real, or real yet.

    Everything here is bounded by the clock. A file added in July does not exist
    in March, a directory listing shows what was there that day, and `git log`
    stops at midnight. A world where somebody quotes code that will not be
    written for three months is worse than one where nobody quotes code at all:
    the first is wrong in a way a reader cannot detect.
    """

    app = "repo"
    summary = "the curator source tree, read-only, as of today."
    # Enough to answer a question, short enough that a chat message quoting it
    # stays a chat message.
    MAX_LINES = 160

    def __init__(self, root: Path, clock: Clock, *, repo: Path, git=None):
        super().__init__(root, clock)
        self.git = git
        self.repo = Path(repo)
        self._rev: dict[str, str | None] = {}      # date -> commit
        self._read: dict[tuple, str | None] = {}   # (rev, path) -> content

    def tool_names(self) -> list[str]:
        return ["list_repo", "read_repo", "search_repo", "recent_commits"]

    # -- the operations -----------------------------------------------------
    def rev(self) -> str | None:
        """The commit this world is standing on today."""
        day = self.clock.iso()[:10]
        if day not in self._rev:
            self._rev[day] = self.git.rev_at(day) if self.git else None
        return self._rev[day]

    def nearest(self, path: str) -> str:
        """What DOES exist near a path that does not.

        nikolai asked `recent_commits` for `src/curator/bulk_llm_inference`,
        got a bare "no commits touching that", and gave up — the real root is
        `src/bespokelabs/curator`. A tool that answers a wrong guess with only
        a negative teaches the caller nothing and they stop asking. So a miss
        walks up to the closest directory that does exist and shows what is in
        it, which is the one piece of information that turns a wrong guess into
        a right one.
        """
        rev = self.rev()
        if not rev or not self.git:
            return ""
        parts = [p for p in path.strip("/").split("/") if p]
        while parts:
            parts.pop()
            here = "/".join(parts)
            try:
                names = self.git.tree_at(rev, here)
            except SystemExit:
                names = []
            if names:
                return (f"{here or '/'} does contain: "
                        + ", ".join(names[:15])
                        + ("" if len(names) <= 15 else ", ..."))
        return ""

    def read(self, path: str) -> str | None:
        rev = self.rev()
        if not rev:
            return None
        key = (rev, path)
        if key not in self._read:
            self._read[key] = self.git.file_at(rev, path)
        return self._read[key]

    def mcp_server(self, uid: str, clock):
        def as_of() -> str:
            return self.clock.iso()[:10]

        def safely(what, fallback):
            """Run a git query; a failure is an answer, not the end of the run.

            These are reads against a repository, driven by whatever a persona
            types. `git grep` alone exits non-zero for "no matches", and one
            unmatched search used to abort a whole simulation through
            `Git.run`'s check=True and `rl.fail`.
            """
            try:
                return what()
            except SystemExit:
                return fallback
            except Exception as exc:                      # noqa: BLE001
                return f"{fallback} ({type(exc).__name__})"

        @tool("read_repo",
              "Read a file from the curator repository as it is TODAY. Use this "
              "before quoting or describing code — the tree changes, and what "
              "you remember may not be what is there yet.",
              {"path": str})
        async def read_repo(args):
            path = (args.get("path") or "").strip().lstrip("/")
            if not path:
                return ok("Give a path, e.g. src/bespokelabs/curator/llm/llm.py")
            body = safely(lambda: self.read(path), None)
            if body is None:
                hint = self.nearest(path)
                return ok(f"There is no {path} in the repository as of "
                          f"{as_of()}. It may not exist yet, or the path may "
                          "be wrong."
                          + (f" {hint}" if hint else ""))
            self._touch(uid, "read_repo", path, self.clock.iso())
            lines = body.splitlines()
            head = "\n".join(lines[:self.MAX_LINES])
            more = ("" if len(lines) <= self.MAX_LINES else
                    f"\n\n... {len(lines) - self.MAX_LINES} more line(s); "
                    "read a narrower path if you need them.")
            return ok(f"{path} as of {as_of()} ({len(lines)} lines):\n\n"
                      f"{head}{more}")

        @tool("list_repo",
              "List what is in a directory of the curator repository today.",
              {"path": str})
        async def list_repo(args):
            path = (args.get("path") or "").strip().strip("/")
            rev = self.rev()
            if not rev:
                return ok("The repository has nothing this old.")
            names = safely(lambda: self.git.tree_at(rev, path), []) or []
            if not names:
                hint = self.nearest(path)
                return ok(f"Nothing at {path or '/'} as of {as_of()}."
                          + (f" {hint}" if hint else ""))
            self._touch(uid, "list_repo", path or "/", self.clock.iso())
            return ok(f"{path or '/'} as of {as_of()}:\n" +
                      "\n".join(f"  {n}" for n in names[:80]))

        @tool("search_repo",
              "Find which files mention a word or symbol, as of today.",
              {"words": str})
        async def search_repo(args):
            want = (args.get("words") or "").strip()
            rev = self.rev()
            if not want or not rev:
                return ok("Say what to look for.")
            # check=False, and it matters: `git grep` exits 1 when nothing
            # matches, `Git.run` treats a non-zero exit as fatal, and rl.fail
            # exits the process. A persona searching for a word that is not in
            # the tree killed the entire run.
            out = self.git.run("grep", "-l", "-I", "--fixed-strings",
                               want, rev, check=False) if self.git else ""
            hits = [ln for ln in out.splitlines() if ln]
            hits = [h.split(":", 1)[-1] for h in hits][:25]
            self._touch(uid, "search_repo", want, self.clock.iso())
            if not hits:
                return ok(f"Nothing mentions {want!r} as of {as_of()}. "
                          "Try a shorter or differently-spelled term, or "
                          "list_repo to see the layout.")
            return ok(f"{want!r} appears in, as of {as_of()}:\n" +
                      "\n".join(f"  {h}" for h in hits))

        @tool("recent_commits",
              "What changed in the repository lately, up to today.",
              {"path": str})
        async def recent_commits(args):
            path = (args.get("path") or "").strip().lstrip("/")
            rev = self.rev()
            if not rev:
                return ok("The repository has nothing this old.")
            args_ = ["log", "-12", "--date=short",
                     "--pretty=%h %ad %an: %s", rev]
            if path:
                args_ += ["--", path]
            out = (safely(lambda: self.git.lines(*args_), []) or []
                   if self.git else [])
            self._touch(uid, "recent_commits", path or "/", self.clock.iso())
            if not out:
                hint = self.nearest(path) if path else ""
                return ok(f"No commits touching {path or 'the repository'} "
                          f"by {as_of()}."
                          + (f" {hint}" if hint else ""))
            return ok(f"Up to {as_of()}:\n" + "\n".join(f"  {l}" for l in out))

        return create_sdk_mcp_server(
            name=self.app, version="1.0.0",
            tools=[read_repo, list_repo, search_repo, recent_commits])


async def _maybe_await(value):
    return await value if hasattr(value, "__await__") else value
