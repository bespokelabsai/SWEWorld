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
    """What the stores stamp things with.

    The engine computes each turn's time inside its own loop and does not hand
    it out, so this advances alongside rather than in lockstep: the same day and
    the same order, not the same instant. Good enough for a corpus where what
    matters is that a page written on Monday is there to open on Thursday.
    """

    def __init__(self, start: dt.datetime | None = None):
        self.at = start

    def set_day(self, when: dt.datetime) -> None:
        self.at = when

    def stamp(self) -> dt.datetime:
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
    summary = ("the company wiki. Pages are grouped into collections "
               "(engineering, design, onboarding, postmortems).")

    def __init__(self, root: Path, clock: Clock, *, collections: dict[str, str],
                 scrub=None):
        super().__init__(root, clock)
        self.docs = self.root / "docs"
        self.docs.mkdir(parents=True, exist_ok=True)
        self.collections = collections
        self.scrub = scrub or (lambda text: text)
        self.comments = self.root / "comments.jsonl"
        self._pages: dict[str, dict] = {}

    def tool_names(self) -> list[str]:
        return ["write_page", "read_page", "list_pages", "comment_on_page"]

    # -- the operations, callable from python as well as from a tool --------
    def write(self, *, uid: str, title: str, body: str, collection: str,
              ts: str | None = None, kind: str = "") -> str:
        book = collection if collection in self.collections else \
            next(iter(self.collections), "engineering")
        rel = f"{book}/{slug(title)}.md"
        path = self.docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        when = ts or self.clock.iso()
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
                ts: str | None = None, reply_to: str = "") -> None:
        """One line on `comments.jsonl`.

        No `quote`. The field is optional, and a quote has to appear exactly
        once in the *rendered* projection of the page — code fences deleted,
        markdown stripped — which is not a property anything writing prose can
        promise. A comment with no quote is a page-level comment, which is what
        most comments are anyway.
        """
        when = ts or self.clock.iso()
        row = {"id": f"c-{slug(rel)}-{len(self._made)}", "doc": rel,
               "author": uid, "created_at": when, "text": text.strip()}
        if reply_to:
            row["reply_to"] = reply_to
        with self.comments.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._record(kind="comment", ident=row["id"], title=f"comment on {rel}",
                     by=uid, action="comment", ts=when)

    # -- the tools ----------------------------------------------------------
    def mcp_server(self, uid: str, clock, writer=None):
        """`writer` is the persona's own document writer, handed over by the
        engine when this parameter is present. Using it is the whole reason a
        page reads like a document instead of like a long Slack message: the
        persona's chat voice rules never touch it."""

        @tool("write_page", "Write a new page on the company wiki.", {
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
            self.comment(uid=uid, rel=rel, text=args.get("text") or "")
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
        self._n = 0

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

    def mcp_server(self, uid: str, clock):
        @tool("find_issue", "Search issues and pull requests by words in the "
                            "title.", {"words": str})
        async def find_issue(args):
            want = {w for w in slug(args.get("words") or "").split("-") if len(w) > 3}
            if not want:
                return ok("Say a word or two from the title.")
            hits = [i for i in self.items.values()
                    if want & set(slug(i.get("title") or "").split("-"))]
            if not hits:
                return ok("Nothing matches.")
            return ok("\n".join(f"#{i['number']} ({i['kind']}) {i['title']}"
                                for i in hits[:10]))

        @tool("read_issue", "Read one issue or pull request by number.",
              {"number": int})
        async def read_issue(args):
            item = self.items.get(int(args.get("number") or 0))
            if item is None:
                return ok("No such issue or pull request.")
            self._touch(uid, "read_issue", f"#{item['number']}", self.clock.iso())
            return ok(f"#{item['number']} ({item['kind']}) {item['title']}\n\n"
                      f"{(item.get('body') or '')[:2500]}")

        return create_sdk_mcp_server(name=self.app, version="1.0.0",
                                     tools=[find_issue, read_issue])


async def _maybe_await(value):
    return await value if hasattr(value, "__await__") else value
