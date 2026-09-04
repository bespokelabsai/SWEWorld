"""The finished corpus, read for placement: where could a remark plausibly go?

`data_gen/phase3_plant.py` asks a related question against *plans* — day specs and
artifact stubs that phase 4 has not simulated yet, whose `about` text is a
conversation's agenda in a few dozen words. Everything here is the opposite: the
conversation happened, the page was written, and the candidate text is real prose
running to thousands of words.

That difference is why none of phase 3's scoring transfers. Its
`score()` is a raw token overlap with the explicit/passing line drawn at a literal
`3`; against a whole channel-day that threshold is met by accident. So this module
does not score for fit at all. It answers the cheap, factual questions —

    who actually posted in this room, on this day?
    what did they actually say?
    which page is this, and what is on it?

— and hands the shortlist to a model, which decides whether a remark belongs there.
Retrieval bounds the context; judgement picks the spot.

One deliberate replacement: phase 3 asks `timeline.json` whether a persona was
*scheduled* to be present. Here presence is read from `messages.jsonl` — whether
they actually spoke in that room that week. A planned attendee who said nothing is
not somebody a remark can be attributed to.
"""
from __future__ import annotations

import collections
import dataclasses
import datetime as dt
import json
import pathlib
import re

from .model import REPO

RUNS = REPO / "data_gen" / "build" / "phase4" / "runs"
LATEST = REPO / "data_gen" / "build" / "phase4" / "latest"

# Chat is the only source with a natural unit smaller than the artifact: a page is
# a page, but a channel holds a different conversation every day.
DAY = re.compile(r"^(\d{4}-\d{2}-\d{2})")


@dataclasses.dataclass
class Message:
    channel: str
    author: str
    created_at: str
    text: str
    id: str | None = None
    thread_id: str | None = None

    @property
    def date(self) -> str:
        return self.created_at[:10]


@dataclasses.dataclass
class Page:
    path: str               # relative to docs/, e.g. "engineering/foo.md"
    title: str
    author: str
    created_at: str
    body: str

    @property
    def date(self) -> str:
        return self.created_at[:10]


@dataclasses.dataclass
class Mail:
    message_id: str
    subject: str
    sender: str
    to: list[str]
    date: str
    body: str
    paths: list[str]        # every .eml copy of this one message


@dataclasses.dataclass
class Candidate:
    """One place a remark could go, with the real text that is already there."""

    key: str                # stable address: "chat|engineering|2025-02-19"
    kind: str               # chat_day | page | mail_thread
    date: str
    room: str               # "#engineering" | "page:engineering/foo.md" | "thread:<mid>"
    who: list[str]          # people who really appear there
    title: str
    excerpt: str            # the actual prose, trimmed for a prompt
    size: int               # messages, or characters for a page


class Corpus:
    """One finished phase-4 run, loaded for reading."""

    def __init__(self, run: pathlib.Path | None = None):
        self.root = pathlib.Path(run) if run else LATEST
        if not (self.root / "messages.jsonl").is_file():
            raise SystemExit(f"no corpus at {self.root} (no messages.jsonl)")
        self.messages = self._messages()
        self.pages = self._pages()
        self.mail = self._mail()
        self._purposes: dict[str, str] | None = None
        self.cast = json.loads((self.root / "cast.json").read_text())["people"] \
            if (self.root / "cast.json").is_file() else {}

        self.by_channel_day: dict[tuple[str, str], list[Message]] = collections.defaultdict(list)
        for m in self.messages:
            self.by_channel_day[(m.channel, m.date)].append(m)
        # Who spoke where, by week. This is the presence predicate: phase 3 reads
        # timeline.json for who was SCHEDULED to be in a room, which after
        # simulation is the wrong question -- a persona who was rostered and said
        # nothing cannot be the one who made a remark there.
        self.spoke: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        for m in self.messages:
            self.spoke[(m.channel, week_of(m.date))].add(m.author)

    # -- loading ----------------------------------------------------------
    def _messages(self) -> list[Message]:
        rows = []
        for line in (self.root / "messages.jsonl").read_text().splitlines():
            # Line 1 is `# Schema: data/schemas/messages.md`, not JSON.
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            d = json.loads(line)
            rows.append(Message(channel=d.get("channel") or "", author=d["author"],
                                created_at=d["created_at"], text=d.get("text") or "",
                                id=d.get("id"), thread_id=d.get("thread_id")))
        return rows

    def _pages(self) -> list[Page]:
        out = []
        docs = self.root / "docs"
        for path in sorted(docs.rglob("*.md")):
            raw = path.read_text()
            if not raw.startswith("---"):
                continue
            _, front, body = raw.split("---", 2)
            meta = {}
            for line in front.strip().splitlines():
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip().strip('"')
            out.append(Page(path=str(path.relative_to(docs)), title=meta.get("title", ""),
                            author=meta.get("author", ""),
                            created_at=meta.get("created_at", ""), body=body.strip()))
        return out

    def _mail(self) -> list[Mail]:
        """One entry per distinct Message-ID, not per file.

        A single mail is on disk once in the sender's Sent and once in every
        recipient's INBOX, all sharing a Message-ID. Treating the copies as
        separate candidates would offer the same conversation several times and
        let two clues land in what is really one thread.
        """
        import email

        emails = self.root / "emails"
        if not emails.is_dir():
            return []
        by_id: dict[str, Mail] = {}
        for path in sorted(emails.rglob("*.eml")):
            try:
                note = email.message_from_string(path.read_text())
            except Exception:
                continue
            mid = (note.get("Message-ID") or "").strip()
            rel = str(path.relative_to(emails))
            if mid in by_id:
                by_id[mid].paths.append(rel)
                continue
            payload = note.get_payload(decode=True)
            body = payload.decode("utf-8", "replace") if payload else (note.get_payload() or "")
            when = note.get("Date") or ""
            try:
                iso = email.utils.parsedate_to_datetime(when).date().isoformat()
            except Exception:
                iso = ""
            by_id[mid] = Mail(message_id=mid, subject=note.get("Subject") or "",
                              sender=(note.get("From") or "").split("@")[0],
                              to=[a.split("@")[0] for a in (note.get("To") or "").split(",") if a.strip()],
                              date=iso, body=body.strip(), paths=[rel])
        return list(by_id.values())

    # -- candidates -------------------------------------------------------
    def channel_days(self, *, holder: str, window: tuple[str, str] | None = None,
                     min_messages: int = 4) -> list[Candidate]:
        """Days this person really talked in a room, with what was said."""
        out = []
        for (channel, date), msgs in self.by_channel_day.items():
            if window and not (window[0] <= date <= window[1]):
                continue
            if len(msgs) < min_messages or holder not in {m.author for m in msgs}:
                continue
            out.append(Candidate(
                key=f"chat|{channel}|{date}", kind="chat_day", date=date,
                room=f"#{channel}", who=sorted({m.author for m in msgs}),
                title=f"#{channel}, {date}",
                excerpt=render_day(msgs), size=len(msgs)))
        out.sort(key=lambda c: c.date)
        return out

    def page_candidates(self, *, holder: str | None = None,
                        window: tuple[str, str] | None = None,
                        wrote_it: bool = True) -> list[Candidate]:
        """Pages this person could add to.

        `wrote_it` is the difference between two real carriers. A section only goes
        into a page its own author wrote -- BookStack attributes a page to one
        person, so a paragraph appearing under somebody else's name is the most
        visible kind of plant. A COMMENT is the opposite: it is signed by whoever
        left it, and it is how everyone else gets onto a page they did not write.
        Restricting `notion` to authored pages left five of seven people with two
        pages or fewer, and the placement model then rejected everything and
        invented a Slack thread instead.
        """
        out = []
        for page in self.pages:
            if window and not (window[0] <= page.date <= window[1]):
                continue
            if holder and wrote_it and page.author != holder:
                continue
            out.append(Candidate(
                key=f"page|{page.path}" + ("" if wrote_it else f"|comment|{holder}"),
                kind="page" if wrote_it else "page_comment", date=page.date,
                room=f"page:{page.path}", who=[page.author], title=page.title,
                excerpt=page.body[:2400], size=len(page.body)))
        out.sort(key=lambda c: c.date)
        return out

    def mail_candidates(self, *, holder: str | None = None,
                        window: tuple[str, str] | None = None) -> list[Candidate]:
        out = []
        for note in self.mail:
            if window and note.date and not (window[0] <= note.date <= window[1]):
                continue
            people = [note.sender, *note.to]
            if holder and holder not in people:
                continue
            out.append(Candidate(
                key=f"mail|{note.message_id}", kind="mail_thread", date=note.date,
                room=f"thread:{note.message_id}", who=people, title=note.subject,
                excerpt=note.body[:1800], size=len(note.body)))
        out.sort(key=lambda c: c.date)
        return out

    # -- facts a caller needs ---------------------------------------------
    def people(self) -> list[str]:
        return sorted({m.author for m in self.messages})

    def reachable(self, window: tuple[str, str] | None = None,
                  room_for: int = 3) -> dict[str, dict[str, int]]:
        """Who can hold a remark at all, and in which sources.

        Phase 3's rule, and it is a count rather than a flag for the reason it
        gives: one carrier is not a source. Without it the tree hands remarks to
        people who cannot make them -- two of this cast post on six and ten days
        across fifteen months, so every leaf they were given was unplaceable and
        the failure showed up as "no candidates" long after the tree was paid for.
        """
        out: dict[str, dict[str, int]] = {}
        for who in self.people():
            counts = {
                "slack": len(self.channel_days(holder=who, window=window)),
                # Authored pages AND pages they could comment on. Counting only
                # what somebody wrote left five of seven people below the floor, so
                # `notion` was unreachable for them and every remark they held went
                # to chat -- which is how a plant ends up 29/36 in Slack.
                "notion": (len(self.page_candidates(holder=who, window=window))
                           + (len(self.page_candidates(holder=who, window=window,
                                                       wrote_it=False))
                              # Commenting only counts for somebody who is ACTUALLY
                              # around. Five of this cast post on a handful of days
                              # in fifteen months; anyone may leave a comment, so
                              # counting it unconditionally would readmit exactly
                              # the people phase 3's floor exists to keep out.
                              if len(self.channel_days(holder=who, window=window)) >= room_for
                              else 0)),
                "email": len(self.mail_candidates(holder=who, window=window)),
            }
            usable = {src: n for src, n in counts.items() if n >= room_for}
            if usable:
                out[who] = usable
        return out

    def span(self) -> tuple[str, str]:
        dates = sorted(m.date for m in self.messages)
        return (dates[0], dates[-1]) if dates else ("", "")

    def channels(self) -> dict[str, int]:
        counts: dict[str, int] = collections.Counter(m.channel for m in self.messages)
        return dict(counts.most_common())

    @property
    def purposes(self) -> dict[str, str]:
        """What each room is FOR, from `data/channels.yaml`.

        The corpus knew who talked where and when, and never what a room was
        about -- so placement ranked candidates by token overlap alone and a
        remark about loss masking could land in #cookbooks because a few words
        matched. The model's own reasoning said so out loud: "None of the eight
        rooms is anywhere near tokenizers, loss masking, or per-token weights",
        and then it was placed there anyway.

        These lines are hand-written and live beside the corpus, not in it.
        """
        if self._purposes is None:
            self._purposes = {}
            path = REPO / "data" / "channels.yaml"
            if path.is_file():
                try:
                    import yaml
                    loaded = yaml.safe_load(path.read_text()) or {}
                except Exception:
                    loaded = {}
                rows = loaded.get("channels", loaded if isinstance(loaded, list) else [])
                for row in rows or []:
                    if isinstance(row, dict) and row.get("name"):
                        self._purposes[str(row["name"]).lstrip("#")] = (
                            row.get("purpose") or row.get("header") or "").strip()
        return self._purposes

    def voice(self, holder: str) -> dict:
        """How this person writes, from cast.json.

        Handed to whatever writes the remark. A remark in the wrong voice is the
        most visible kind of plant: dario writes in lowercase with frequent typos
        and emil does not, and a reader who notices that notices everything.
        """
        person = self.cast.get(holder) or {}
        return {"name": (person.get("core") or {}).get("name", holder),
                **(person.get("voice") or {})}


def week_of(date: str) -> str:
    day = dt.date.fromisoformat(date)
    return f"{day.isocalendar()[0]}-W{day.isocalendar()[1]:02d}"


def render_day(msgs: list[Message], limit: int = 60) -> str:
    """A channel-day as a reader would see it, trimmed to fit a prompt."""
    lines = []
    for m in msgs[:limit]:
        stamp = m.created_at[11:16]
        text = " ".join(m.text.split())
        lines.append(f"{stamp}  {m.author}: {text[:400]}")
    if len(msgs) > limit:
        lines.append(f"... and {len(msgs) - limit} more messages that day")
    return "\n".join(lines)
