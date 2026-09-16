#!/usr/bin/env python3
"""Does the corpus agree with itself, and with the repository it is about?

The ingest scripts validate each file against its schema. `world-verify` counts
rows in the populated world. Nothing until now read two files together and asked
whether they tell the same story, which is the only kind of wrong a reader of
the world actually notices: a wiki page announced in chat eight days before it
exists, a PR discussed a month before it was opened, a hotfix announced before
the release it patches.

That class is not a schema problem. It comes from the generator having three
separate authorities for "when did this happen" and never joining them:

  * `artifacts.json` gives each page and mail a DATE, with no time;
  * `worldapps.write()` stamps the file with the simulation clock of whichever
    channel-day the persona was writing in, and that clock restarts at 09:00,
    so all 108 pages land between 09:14 and 10:38 on thirteen distinct times;
  * chat timestamps come from the same clock in a DIFFERENT channel-day, which
    was simulated separately and told only whether an artifact was "planned" or
    "written".

The repository is the one clock that never drifts — `ingest_history.py` does no
date rewriting — so where the corpus and `forge.json` disagree, the corpus is
wrong.

Run it with no arguments for the story checks. `--plants` runs the separate
question of whether a corpus edit has broken one of the planted tasks, which is
the failure that hides: `inject.located()` substring-searches the corpus for the
plant's own words, and `task_generator/.located-corpora/` caches the old bodies,
so a desynced plant still builds a healthy-looking artifact.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import email.parser
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worldlib as wl  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

# A chat remark that asserts a page exists, and one that asserts it does not.
# Both are deliberately narrow: a message that merely NAMES a page ("the build
# plan has the schema in it") says nothing about when it was written, and
# counting those as claims buries the real findings under a hundred neutral
# mentions.
SAYS_UP = re.compile(
    r"(is up\b|are up\b|up on the wiki|up in the .{0,20}wiki|it'?s up\b"
    r"|posted (?:it )?(?:to|on) the wiki|went up|now on the wiki|put (?:it )?up"
    r"|drafted and up|wrote (?:it )?up.{0,20}wiki|is (?:on|in) the wiki"
    r"|are (?:on|in) the wiki|is written up|put the .{0,40} on the wiki"
    r"|is in the wiki)", re.I)
SAYS_MISSING = re.compile(
    r"(isn'?t (?:up|on the wiki|there|written|showing)|is not (?:up|on the wiki|there)"
    r"|not on the wiki|nothing (?:is )?there|doesn'?t exist|does not exist"
    r"|no .{0,30}page( up)?( yet)?|couldn'?t find|can'?t find|not up yet"
    r"|still (?:being )?(?:drafted|in draft|writing|written|in progress)"
    r"|hasn'?t (?:gone|landed|been)|haven'?t written|not there yet"
    r"|still (?:on me|yours)|still coming|who owes|nothing on the wiki"
    r"|wiki'?s empty|not started)", re.I)

# "PR 42", "pr #42", "issue 42", and a bare "#42". The bare form excludes a
# leading word character or slash so that `curator#4` and a URL path do not
# register, and requires two digits so that "#1 priority" does not either.
REFERENCE = re.compile(
    r"\b(?:PRs?|pull request|[Ii]ssue)\s*#?\s*(\d{1,4})\b|(?<![\w/.])#(\d{2,4})\b")
CLAIMS_MERGED = [
    re.compile(r"\bPR\s*#?\s*(\d{1,4})\s+(?:is|was|has been|got)\s+merged\b", re.I),
    re.compile(r"\bmerged\s+(?:PR\s*#?\s*)?(\d{2,4})\b", re.I),
    re.compile(r"\bPR\s*#?\s*(\d{1,4})\s+merged\b", re.I),
]
# A merge spoken about rather than reported: a plan, a request or a question.
INTENT_OR_QUESTION = re.compile(
    r"\b(?:need|needs|needed|want|wants|should|could|can|will|'ll|get|getting"
    r"|before|until|once|if|when|do we|does)\b[^.?!]*$", re.I)

CLAIMS_MAIL_SENT = re.compile(
    r"(announce(?:ment)?(?: mail| email)? (?:is |went |just went )?out"
    r"|mail(?:ed)? the team|announcement went out|announce went out"
    r"|sent the .{0,25}(?:recap|announce)|sent out the announce"
    r"|sent the .{0,25}announcement)", re.I)

# The version an announcement is about: "v0.1.23.post1 is out", "0.1.13 is out".
RELEASE_IN_SUBJECT = re.compile(r"\bv?(\d+\.\d+\.\d+(?:\.post\d+)?)\b")

# An @mention: a first name, or a full "@First Last".
MENTION = re.compile(r"@([A-Za-z][A-Za-z]+(?:\s+[A-Z][a-z]+)?)")

# Weekly NOTES are titled by the Monday of the week they cover and written on
# the Wednesday of it; 31 of the corpus's 32 follow that exactly. A weekly
# UPDATE is a different artifact — it mirrors the Monday-morning recap mail, so
# it is correctly dated the Monday AFTER its week and must not be held to the
# same window, which is why the title match is anchored on "notes".
WEEK_IN_TITLE = re.compile(r"[Ww]eekly [Ss]ync [Nn]otes|[Ww]eekly [Nn]otes|[Ww]eekly notes")
WEEK_START = re.compile(r"[Ww]eek of ([A-Z][a-z]{2})\w*\s+(\d{1,2})")
MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}
WEEKLY_OFFSET_DAYS = (0, 6)

# How long before talking about a page somebody actually wrote it. Ordering is
# what the checks enforce, because ordering is what is POSSIBLE; this is what is
# plausible, and it is only ever used by --fix. Landing a page on the exact
# second of the remark announcing it satisfies every check and still says a
# person finished a postmortem and posted about it in the same instant.
AUTHORING_LAG = dt.timedelta(minutes=12)


def flat(text: str) -> str:
    """Compare titles the way a reader does, not the way a byte comparison does.

    A persona writes `Weekly Sync Notes, Week of Oct 28` for a page titled
    `Weekly Sync Notes — Week of Oct 28`. Matching on the raw string finds
    neither the claims nor the contradictions.
    """
    text = unicodedata.normalize("NFKD", text).lower()
    text = text.replace("—", "-").replace("–", "-").replace("’", "'")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


# =============================================================================
# Loading
# =============================================================================
class Corpus:
    def __init__(self, data: Path, problems: wl.Problems):
        self.data = data
        self.problems = problems
        self.messages = [obj for _, obj in wl.read_jsonl(data / "messages.jsonl", problems)]
        self.comments = [obj for _, obj in wl.read_jsonl(data / "comments.jsonl", problems)]
        self.pages = self._load_pages()
        self.mail = self._load_mail()
        self.forge = self._load_forge()
        self.releases = self._load_releases()
        self.channels = self._load_channels()

    def _load_pages(self) -> list[dict]:
        pages = []
        for path in sorted((self.data / "docs").glob("*/*.md")):
            text = path.read_text(encoding="utf-8")
            title = re.search(r"^title:\s*(.+)$", text, re.M)
            created = re.search(r"^created_at:\s*(\S+)", text, re.M)
            author = re.search(r"^author:\s*(\S+)", text, re.M)
            if not (title and created and author):
                self.problems.error("frontmatter is missing title/author/created_at", path)
                continue
            raw = title.group(1).strip()
            pages.append({
                "path": path,
                "rel": str(path.relative_to(self.data / "docs")),
                "slug": path.stem,
                "title": json.loads(raw) if raw.startswith('"') else raw,
                "created_at": created.group(1),
                "author": author.group(1),
            })
        return pages

    def _load_mail(self) -> dict[str, dict]:
        """One entry per logical message, not per stored copy.

        The same mail is filed in the sender's Sent box and in every
        recipient's INBOX, so 613 files carry 93 messages. Reporting per file
        turns one wrong Date into twenty-two findings.
        """
        parser = email.parser.BytesParser()
        by_id: dict[str, dict] = {}
        for path in sorted((self.data / "emails").glob("*/*/*.eml")):
            msg = parser.parse(path.open("rb"), headersonly=True)
            mid = msg["Message-ID"]
            entry = by_id.setdefault(mid, {
                "message_id": mid,
                "subject": msg["Subject"] or "",
                "date": parsedate_to_datetime(msg["Date"]),
                "in_reply_to": (msg["In-Reply-To"] or "").strip(),
                "copies": [],
            })
            entry["copies"].append(path)
        return by_id

    def _load_forge(self) -> dict[int, dict]:
        record = self.data / "history" / "forge.json"
        if not record.exists():
            self.problems.warn("no forge record; skipping repository cross-checks", record)
            return {}
        github = json.loads(record.read_text())["github"]
        items = {}
        for pull in github["pulls"]:
            items[pull["number"]] = {"kind": "PR", **pull}
        for issue in github["issues"]:
            items[issue["number"]] = {"kind": "issue", **issue}
        return items

    def _load_releases(self) -> dict[str, str]:
        """version -> publish time, from the real repository's release list."""
        record = self.data / "history" / "forge.json"
        if not record.exists():
            return {}
        github = json.loads(record.read_text())["github"]
        return {r["tag_name"].lstrip("v"): (r.get("published_at") or r.get("created_at") or "")
                for r in github.get("releases", [])}

    def _load_channels(self) -> dict[str, set[str]]:
        import yaml
        doc = yaml.safe_load((self.data / "channels.yaml").read_text())
        return {c["name"]: set(c.get("members") or []) for c in doc["channels"]}


# =============================================================================
# Story checks
# =============================================================================
def claims_about(corpus: Corpus, page: dict) -> list[tuple[dict, bool]]:
    """Every remark that asserts this page does or does not exist yet.

    A denial is tested first: "the plan isn't on the wiki" contains "on the
    wiki", so reading the positive pattern first calls half the contradictions
    announcements.
    """
    key = flat(page["title"])
    out = []
    for msg in corpus.messages:
        body = msg.get("text") or ""
        if key not in flat(body) and page["slug"] not in body:
            continue
        if SAYS_MISSING.search(body):
            out.append((msg, False))
        elif SAYS_UP.search(body):
            out.append((msg, True))
    return out


def check_page_claims(corpus: Corpus) -> None:
    """Chat and the wiki must agree about when a page started existing.

    This is the largest class by a wide margin, and the one that reads worst:
    #general announcing a doc is up, and #engineering asking where it is three
    weeks later, are both true statements about a page that exists once.
    """
    for page in corpus.pages:
        created = page["created_at"]
        for msg, says_up in claims_about(corpus, page):
            said = msg["created_at"]
            where = f"#{msg['channel']} {said[:16]} {msg['author']}"
            if not says_up and said >= created:
                corpus.problems.error(
                    f"{where}: says {page['rel']} is not on the wiki, but it was "
                    f"created {created[:16]}", corpus.data / "messages.jsonl")
            elif says_up and said < created:
                corpus.problems.error(
                    f"{where}: announces {page['rel']} as up, but it is not "
                    f"created until {created[:16]}", corpus.data / "messages.jsonl")


def check_comment_after_page(corpus: Corpus) -> None:
    """A BookStack comment cannot predate the page it hangs off.

    `ingest_comments.py` checks a reply against its parent comment and stops
    there, so a comment older than its own page imports without complaint and
    renders as a discussion of a document nobody had written.
    """
    by_rel = {p["rel"]: p for p in corpus.pages}
    for comment in corpus.comments:
        page = by_rel.get(comment["doc"])
        if page is None:
            corpus.problems.error(
                f"comment {comment.get('id')} names a page that does not exist: "
                f"{comment['doc']}", corpus.data / "comments.jsonl")
            continue
        if comment["created_at"] < page["created_at"]:
            corpus.problems.error(
                f"comment {comment.get('id')} is dated {comment['created_at'][:16]}, "
                f"before its page {page['rel']} at {page['created_at'][:16]}",
                corpus.data / "comments.jsonl")


def check_chat_reply_order(corpus: Corpus) -> None:
    """A thread reply cannot precede its root.

    Enforced for wiki comments (`ingest_comments.py`) and not for chat, where
    `ingest_chat.py` only sorts the replies before emitting them.
    """
    roots = {m["id"]: m for m in corpus.messages if m.get("id")}
    for msg in corpus.messages:
        root = roots.get(msg.get("thread_id"))
        if root and msg["created_at"] < root["created_at"]:
            corpus.problems.error(
                f"#{msg['channel']} {msg['created_at'][:16]} {msg['author']}: reply "
                f"predates its root {root['id']} at {root['created_at'][:16]}",
                corpus.data / "messages.jsonl")


def check_mail_reply_order(corpus: Corpus) -> None:
    """A reply cannot be dated before the mail it answers.

    Mail is stamped from the writer's own turn clock, and channels are simulated
    concurrently on separate timelines, so a persona at 09:50 in one room can
    reply to a mail sent at 14:48 from another. Nothing else reads Date against
    In-Reply-To: `ingest_mail.py` checks only that the parent exists.
    """
    for mid, mail in corpus.mail.items():
        parent = corpus.mail.get(mail["in_reply_to"])
        if parent and mail["date"] < parent["date"]:
            corpus.problems.error(
                f"mail {mail['subject'][:50]!r} is dated {mail['date'].isoformat()[:16]}, "
                f"before the message it answers at {parent['date'].isoformat()[:16]}",
                mail["copies"][0])


def check_forge_references(corpus: Corpus) -> None:
    """Nobody discusses a pull request that has not been opened yet.

    The generator hands each channel-day a `must_not_mention.prs_above` cap, but
    that is a line in a prompt, so a persona invents a plausible number and the
    run completes. `forge.json` is the authority: it is the real repository's
    record, ingested with its dates untouched.
    """
    for msg in corpus.messages:
        body = msg.get("text") or ""
        said = msg["created_at"][:10]
        for match in REFERENCE.finditer(body):
            number = int(match.group(1) or match.group(2))
            item = corpus.forge.get(number)
            if item is None:
                continue  # a number that is not a PR at all; nothing to check
            opened = item["created_at"][:10]
            if said < opened:
                corpus.problems.error(
                    f"#{msg['channel']} {said} {msg['author']}: names "
                    f"{item['kind']} {number}, which is not opened until {opened}",
                    corpus.data / "messages.jsonl")


def check_merge_claims(corpus: Corpus) -> None:
    """"PR 632 merged" on a day PR 632 had three more weeks to wait.

    Kept separate from `check_forge_references` because the fix is different: a
    reference to a PR that does not exist is a wrong number, while a premature
    merge is a wrong verb.
    """
    for msg in corpus.messages:
        body = msg.get("text") or ""
        said = msg["created_at"][:10]
        # The three patterns overlap — "PR 632 merged" matches two of them — so
        # collect the numbers first and report each PR once per message.
        # "I'll get PR 574 merged this afternoon" and "Do we need PR 653 merged
        # before we tag?" are a plan and a question. Only an assertion that the
        # merge has happened can be contradicted by `merged_at`.
        numbers = set()
        for pattern in CLAIMS_MERGED:
            for m in pattern.finditer(body):
                lead = body[max(0, m.start() - 30):m.start()]
                if INTENT_OR_QUESTION.search(lead):
                    continue
                numbers.add(int(m.group(1)))
        for number in sorted(numbers):
                item = corpus.forge.get(number)
                if item is None or item["kind"] != "PR":
                    continue
                merged = item.get("merged_at")
                if merged is None:
                    corpus.problems.error(
                        f"#{msg['channel']} {said} {msg['author']}: calls PR "
                        f"{item['number']} merged; it never was ({item['state']})",
                        corpus.data / "messages.jsonl")
                elif said < merged[:10]:
                    corpus.problems.error(
                        f"#{msg['channel']} {said} {msg['author']}: calls PR "
                        f"{item['number']} merged; it merges {merged[:10]}",
                        corpus.data / "messages.jsonl")


def check_mail_send_claims(corpus: Corpus) -> None:
    """A mail cannot arrive hours before the person says they sent it.

    Release announcements come out of `artifacts.json` on the morning slot while
    the chat that narrates them runs the whole day, so the corpus routinely has
    konrad reading an announcement at 09:28 and dario saying at 13:08 that he
    has just sent it.
    """
    by_day: dict[str, list[dict]] = collections.defaultdict(list)
    for msg in corpus.messages:
        if CLAIMS_MAIL_SENT.search(msg.get("text") or ""):
            by_day[msg["created_at"][:10]].append(msg)
    for mail in corpus.mail.values():
        if not re.search(r"is out|hotfix is out|recap|Weekly update", mail["subject"], re.I):
            continue
        claims = by_day.get(mail["date"].date().isoformat())
        if not claims:
            continue
        first = min(c["created_at"] for c in claims)
        gap = dt.datetime.fromisoformat(first) - mail["date"]
        if gap > dt.timedelta(hours=1):
            corpus.problems.error(
                f"{mail['subject'][:60]!r} is dated {mail['date'].isoformat()[:16]} but "
                f"chat does not say it was sent until {first[11:16]} "
                f"({gap.total_seconds() / 3600:.1f}h later)",
                corpus.data / "emails" / "index.jsonl")


def check_release_order(corpus: Corpus) -> None:
    """A hotfix cannot be announced before the release it patches.

    The generator emits a day's mail in its own order and nothing compares two
    of them, so `v0.1.23.post1 is out` went out 35 minutes before `v0.1.23 is
    out`. `forge.json` holds the real publish times and settles it.
    """
    by_day: dict[str, list[dict]] = collections.defaultdict(list)
    for mail in corpus.mail.values():
        match = RELEASE_IN_SUBJECT.search(mail["subject"])
        if match and corpus.releases.get(match.group(1)):
            by_day[mail["date"].date().isoformat()].append(
                {**mail, "version": match.group(1)})
    for day, mails in by_day.items():
        for a in mails:
            for b in mails:
                if a is b:
                    continue
                real_a, real_b = corpus.releases[a["version"]], corpus.releases[b["version"]]
                if real_a < real_b and a["date"] > b["date"]:
                    corpus.problems.error(
                        f"{day}: {b['subject'][:40]!r} was announced "
                        f"{b['date'].isoformat()[11:16]}, before "
                        f"{a['subject'][:40]!r} at {a['date'].isoformat()[11:16]}, but the "
                        f"repository published them the other way round",
                        corpus.data / "emails" / "index.jsonl")


def check_membership(corpus: Corpus) -> None:
    """Everyone who speaks in a room, or is called into it, is in it.

    `ingest_chat.build_import_lines` only writes a membership for a persona the
    channel lists, so an author who is not a member imports as a post from
    somebody who was never in the room, and an @mention of a non-member is a
    Mattermost notification that never fires.
    """
    # Parsed directly rather than through `worldlib.Identities`, which needs a
    # `World` and therefore a populated .env. This check has to run on a bare
    # checkout, before anything is booted.
    import yaml
    personas = yaml.safe_load((corpus.data / "identities.yaml").read_text())["personas"]
    by_first = {p["display_name"].split()[0].lower(): p["id"] for p in personas}
    by_full = {p["display_name"].lower(): p["id"] for p in personas}
    for msg in corpus.messages:
        members = corpus.channels.get(msg["channel"])
        if members is None:
            continue
        if msg["author"] not in members:
            corpus.problems.error(
                f"#{msg['channel']} {msg['created_at'][:16]}: {msg['author']} posts "
                "in a channel they are not a member of",
                corpus.data / "messages.jsonl")
        for raw in MENTION.findall(msg.get("text") or ""):
            name = raw.lower().strip()
            pid = by_full.get(name) or by_first.get(name.split()[0])
            if pid and pid not in members:
                corpus.problems.error(
                    f"#{msg['channel']} {msg['created_at'][:16]}: mentions @{raw}, "
                    "who is not a member of the channel",
                    corpus.data / "messages.jsonl")


def check_weekly_notes(corpus: Corpus) -> None:
    """Weekly notes are written during the week they are named after."""
    for page in corpus.pages:
        if not page["rel"].startswith("meetings/"):
            continue
        if not WEEK_IN_TITLE.search(page["title"]):
            continue
        match = WEEK_START.search(page["title"])
        if not match:
            continue
        created = dt.date.fromisoformat(page["created_at"][:10])
        month = MONTHS[match.group(1).lower()]
        # A page written in January about "week of Dec 30" belongs to last year.
        year = created.year - 1 if month == 12 and created.month == 1 else created.year
        start = dt.date(year, month, int(match.group(2)))
        delta = (created - start).days
        if not WEEKLY_OFFSET_DAYS[0] <= delta <= WEEKLY_OFFSET_DAYS[1]:
            corpus.problems.error(
                f"{page['rel']} is dated {created} but is titled for the week of "
                f"{start} ({delta} days later)", page["path"])


def check_mail_index(corpus: Corpus) -> None:
    """The IMAP INTERNALDATE and the Date: header must not disagree.

    They are separate fields on purpose — `emails.md` explains why — which is
    exactly why a fix applied to one and not the other goes unnoticed.
    """
    index = {row["path"]: row for _, row in
             wl.read_jsonl(corpus.data / "emails" / "index.jsonl", corpus.problems)}
    root = corpus.data / "emails"
    for mail in corpus.mail.values():
        for path in mail["copies"]:
            row = index.get(str(path.relative_to(root)))
            if row is None:
                corpus.problems.error("not listed in index.jsonl", path)
                continue
            if row["date"] != mail["date"].isoformat():
                corpus.problems.error(
                    f"index date {row['date']} but Date: header "
                    f"{mail['date'].isoformat()}", path)


STORY_CHECKS = (
    check_page_claims,
    check_comment_after_page,
    check_chat_reply_order,
    check_mail_reply_order,
    check_forge_references,
    check_merge_claims,
    check_mail_send_claims,
    check_release_order,
    check_membership,
    check_weekly_notes,
    check_mail_index,
)


# =============================================================================
# Reconciling
# =============================================================================
def _at(when: str) -> dt.datetime:
    """An ISO stamp as an aware datetime. Compared as strings, "2025-06-04" sorts
    before "2025-06-04T10:30", which is how a date-only ceiling let a page move
    to 14:48 on the day its planted comment is injected at 10:30."""
    stamp = dt.datetime.fromisoformat(when)
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=dt.timezone.utc)


def clue_ceiling(corpus: Corpus) -> dict[str, dt.datetime]:
    """The earliest comment on each page, planted or already in the corpus.

    A page may be moved later to agree with the chat, but never past a remark
    on it: a BookStack comment older than its own page is the defect this tool
    exists to catch, and a repair that creates one is worse than the
    contradiction it fixes. The corpus's own comments count as much as the
    planted ones; ignoring them let `--fix` break `check_comment_after_page`.
    """
    pages, _threads = carriers()
    out = {rel: min(_at(d) for d in dates if d)
           for rel, dates in pages.items() if any(dates)}
    for comment in corpus.comments:
        when = _at(comment["created_at"])
        if comment["doc"] not in out or when < out[comment["doc"]]:
            out[comment["doc"]] = when
    return out


def best_created_at(page: dict, claims: list[tuple[dict, bool]],
                    ceiling: dt.datetime | None) -> str:
    """The timestamp this page would have if it agreed with as much chat as possible.

    Not "before the first announcement": the corpus argues with itself about
    some pages -- announced up in June, asked after in December -- and no single
    date satisfies both, so the minority claim is the one that has to move. This
    picks the date that contradicts the fewest remarks and, among ties, the one
    closest to where the page already is, so a run that is already consistent is
    left alone.
    """
    ups = [m["created_at"] for m, up in claims if up]
    dens = [m["created_at"] for m, up in claims if not up]
    current = page["created_at"]

    def wrong(when: str) -> int:
        return sum(1 for u in ups if u < when) + sum(1 for d in dens if d >= when)

    # One second past a denial, so the denial itself stays true.
    options = {current} | set(ups) | {
        (dt.datetime.fromisoformat(d) + dt.timedelta(seconds=1)).isoformat() for d in dens}
    if ceiling:
        options = {o for o in options if _at(o) <= ceiling} or {current}
    return min(sorted(options),
               key=lambda w: (wrong(w),
                              abs((dt.datetime.fromisoformat(w)
                                   - dt.datetime.fromisoformat(current)).total_seconds())))


def humane_time(claims: list[tuple[dict, bool]], chosen: str, key: str = "") -> str:
    """Move a page off the exact second of the remark that announces it.

    `best_created_at` returns the announcement's own timestamp, which satisfies
    every check and still says a person finished a postmortem and posted about
    it in the same instant.

    ONLY that case. A timestamp derived from a denial is already the smallest
    move that keeps the denial true, and dragging it further was worse than the
    thing it fixed: it pushed a handover page past its own comments and a weekly
    note out of the week it is named for.

    The interval is jittered off the page's own path so that twenty-four pages
    announced at 09:00 do not all land at 08:48, which would be the same tell
    one step to the left.
    """
    if not any(up and m["created_at"] == chosen for m, up in claims):
        return chosen
    lag = AUTHORING_LAG + dt.timedelta(
        minutes=int(hashlib.sha1(key.encode()).hexdigest(), 16) % 9 - 4)
    want = dt.datetime.fromisoformat(chosen) - lag
    # Never back past somebody saying it was not there yet; if the gap is
    # narrower than the interval, take the middle of it.
    lo = max((m["created_at"] for m, up in claims
              if not up and m["created_at"] < chosen), default=None)
    if lo is not None and want <= dt.datetime.fromisoformat(lo):
        floor, ceil = dt.datetime.fromisoformat(lo), dt.datetime.fromisoformat(chosen)
        want = floor + (ceil - floor) / 2
    return want.isoformat()


def fix_pages(corpus: Corpus, apply: bool) -> int:
    ceilings = clue_ceiling(corpus)
    changed = 0
    for page in corpus.pages:
        claims = claims_about(corpus, page)
        if not claims:
            continue
        ceiling = ceilings.get(page["rel"])
        want = humane_time(claims, best_created_at(page, claims, ceiling), page["rel"])
        # `humane_time` only ever moves earlier, but say so where it matters.
        if ceiling and _at(want) > ceiling:
            want = page["created_at"]
        if want == page["created_at"]:
            continue
        changed += 1
        print(f"  {page['rel']}\n    {page['created_at'][:19]} -> {want[:19]}")
        if apply:
            text = page["path"].read_text(encoding="utf-8")
            page["path"].write_text(
                re.sub(r"^created_at:\s*\S+$", f"created_at: {want}", text, count=1, flags=re.M),
                encoding="utf-8")
    return changed


def fix_mail(corpus: Corpus, apply: bool) -> int:
    """Move an announcement mail to the hour the chat says it was sent.

    The mail moves and the chat does not, always: planted clues anchor to a chat
    message by "HH:MM author", so retiming one detaches a clue silently, while
    rewording it cannot. A mail that is a planted thread root does not move
    either -- a reply was placed against its date.
    """
    _pages, frozen = carriers()
    claims: dict[str, list[str]] = collections.defaultdict(list)
    for msg in corpus.messages:
        if CLAIMS_MAIL_SENT.search(msg.get("text") or ""):
            claims[msg["created_at"][:10]].append(msg["created_at"])

    due = {}
    for mid, mail in corpus.mail.items():
        if not re.search(r"is out|hotfix is out|recap|Weekly update", mail["subject"], re.I):
            continue
        said = claims.get(mail["date"].date().isoformat())
        if not said or mid in frozen:
            continue
        first = min(said)
        if dt.datetime.fromisoformat(first) - mail["date"] <= dt.timedelta(hours=1):
            continue
        due[mid] = dt.datetime.fromisoformat(first)

    # Two mails can share a day; keep their order and the gap between them.
    by_day: dict[dt.date, list[str]] = collections.defaultdict(list)
    for mid in due:
        by_day[corpus.mail[mid]["date"].date()].append(mid)
    for mids in by_day.values():
        mids.sort(key=lambda m: corpus.mail[m]["date"])
        base, earliest = due[mids[0]], corpus.mail[mids[0]]["date"]
        for mid in mids:
            due[mid] = base + (corpus.mail[mid]["date"] - earliest)

    # Two announcements on one day are ordered by the repository, not by the
    # order the generator happened to emit them. v0.1.23.post1 was stamped 35
    # minutes BEFORE the v0.1.23 it patches, which is not a thing that can
    # happen; GitHub published v0.1.23 at 16:28Z and post1 at 23:11Z.
    for mids in by_day.values():
        versions = {}
        for mid in mids:
            m = RELEASE_IN_SUBJECT.search(corpus.mail[mid]["subject"])
            if m and corpus.releases.get(m.group(1)):
                versions[mid] = corpus.releases[m.group(1)]
        if len(versions) < 2:
            continue
        want = sorted(versions, key=lambda m: versions[m])
        slots = sorted(due[m] for m in want)
        for mid, slot in zip(want, slots):
            due[mid] = slot

    # Never at or past a reply to it. Moving an announcement later can put it
    # after the "Re:" that answers it, and nothing downstream would say so.
    replies: dict[str, dt.datetime] = {}
    for mail in corpus.mail.values():
        parent = mail["in_reply_to"]
        if parent and (parent not in replies or mail["date"] < replies[parent]):
            replies[parent] = mail["date"]
    for mid in list(due):
        if mid in replies and due[mid] >= replies[mid]:
            print(f"  kept {corpus.mail[mid]['subject'][:50]!r}: it would land after "
                  f"its reply at {replies[mid].isoformat()[:16]}")
            del due[mid]

    index_path = corpus.data / "emails" / "index.jsonl"
    rows = [json.loads(l) for l in index_path.read_text().splitlines() if l.strip()]
    by_path = {r["path"]: r for r in rows}
    for mid, when in sorted(due.items(), key=lambda kv: kv[1]):
        mail = corpus.mail[mid]
        print(f"  {mail['date'].isoformat()[:16]} -> {when.isoformat()[:16]}  "
              f"{mail['subject'][:50]} ({len(mail['copies'])} copies)")
        if not apply:
            continue
        header = format_datetime(when)
        for path in mail["copies"]:
            raw = path.read_text(encoding="utf-8")
            path.write_text(re.sub(r"^Date: .+$", f"Date: {header}", raw, count=1, flags=re.M),
                            encoding="utf-8")
            by_path[str(path.relative_to(corpus.data / "emails"))]["date"] = when.isoformat()
    if apply and due:
        index_path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return len(due)


# =============================================================================
# Plant safety
# =============================================================================
def planted_strings() -> set[str]:
    """Every remark the task plants quote verbatim.

    `inject.located()` finds a planted remark by substring-searching the corpus
    for the plant's own words and raises rather than degrading, so these are the
    strings a corpus edit may not touch.
    """
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for key in ("text", "adapted", "remark", "body"):
                value = node.get(key)
                if isinstance(value, str) and len(value) > 25:
                    found.add(value)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for plant in sorted(REPO.glob("task_generator/out/*/clues*/plant.json")):
        walk(json.loads(plant.read_text()))
    return found


def stamp_at(date: str, minute: str) -> str:
    """`tg.inject.stamp`, which is what places a planted remark in time."""
    hh, _, mm = (minute or "10:30").partition(":")
    try:
        when = dt.datetime.fromisoformat(date).replace(
            hour=int(hh) % 24, minute=int(mm or 0) % 60, tzinfo=dt.timezone.utc)
    except ValueError:
        when = dt.datetime.fromisoformat(date).replace(hour=10, minute=30,
                                                       tzinfo=dt.timezone.utc)
    return when.isoformat()


def carriers() -> tuple[dict[str, list[str]], set[str]]:
    """Where the plants hang their clues: which page, and which mail thread.

    A page carrying a planted `doc_comment` may be retimed only as far as the
    earliest clue dated on it; a mail thread root may not be retimed at all,
    because the planted reply is placed against it.
    """
    pages: dict[str, list[str]] = collections.defaultdict(list)
    threads: set[str] = set()

    def minutes(node) -> list[str]:
        if isinstance(node, dict):
            own = [node["minute"]] if isinstance(node.get("minute"), str) else []
            return own + [m for v in node.values() for m in minutes(v)]
        if isinstance(node, list):
            return [m for v in node for m in minutes(v)]
        return []

    def walk(node):
        if isinstance(node, dict):
            carrier = node.get("carrier")
            if isinstance(carrier, dict):
                room = carrier.get("room") or ""
                if room.startswith("page:") and carrier.get("date"):
                    # The instant `inject.write_comment` will stamp the first
                    # remark: its own minute, else the 10:30 it defaults to.
                    first = min(minutes(node) or ["10:30"],
                                key=lambda m: _at(stamp_at(carrier["date"], m)))
                    pages[room[5:]].append(stamp_at(carrier["date"], first))
                elif room.startswith("thread:"):
                    threads.add(room[7:])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for plant in sorted(REPO.glob("task_generator/out/*/clues*/plant.json")):
        walk(json.loads(plant.read_text()))
    return pages, threads


def _tracked_text(ref: str, prefix: str) -> str:
    """Every tracked file under `prefix` at `ref`, concatenated.

    Planted remarks live in chat, in wiki pages and in mail, so a delta check
    that reads only messages.jsonl would miss a page or a mail body edit.
    """
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, prefix],
                           cwd=REPO, capture_output=True, text=True).stdout.split()
    # Chunked because `data/emails` alone is 613 files: one `git show` with that
    # many arguments comes back short, and a baseline that is quietly missing
    # half the corpus makes the delta look clean when it is not.
    out = []
    for i in range(0, len(names), 50):
        out.append(subprocess.run(
            ["git", "show"] + [f"{ref}:{n}" for n in names[i:i + 50]],
            cwd=REPO, capture_output=True, text=True).stdout)
    return "".join(out)


def plant_baseline() -> str:
    """The corpus the plants were built against, not HEAD.

    Against HEAD the anchor check is empty the moment a corpus edit is
    committed: the commit that moved a message is compared with itself and
    passes. The plants anchor to the messages as they were when a plant.json
    last changed, so that commit is the reference, and a resync moves it on.
    """
    ref = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "task_generator/out/*/clues*/plant.json"],
        cwd=REPO, capture_output=True, text=True).stdout.strip()
    if not ref:
        print("  plants: no commit changed a plant; comparing against HEAD")
    return ref or "HEAD"


def check_plants(corpus: Corpus, baseline: str) -> None:
    """The five things a corpus edit must not break.

    Each one is silent when it fails. The located arm still builds — off the
    cache in `task_generator/.located-corpora/` — and the artifact looks healthy
    while the tool that makes it does not work.
    """
    problems = corpus.problems
    bodies = {m.get("text") or "" for m in corpus.messages}
    pages_text = "\n".join(p["path"].read_text(encoding="utf-8") for p in corpus.pages)
    mail_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for mail in corpus.mail.values() for path in mail["copies"][:1])

    # 1. Every planted remark that WAS baked into the corpus is still there,
    #    word for word. Not every planted string: most are injected into the
    #    image at task-build time and were never in `data/`, so an absolute
    #    "all present" assertion fails 5,479 times on a clean checkout and
    #    teaches you to ignore it. What matters is the delta — a remark the
    #    corpus carried before an edit and does not carry after it.
    present = {s for s in planted_strings()
               if s in bodies or s in pages_text or s in mail_text}
    old_msgs = subprocess.run(["git", "show", f"{baseline}:data/messages.jsonl"],
                              cwd=REPO, capture_output=True, text=True).stdout
    # Chat is compared as whole messages, the way `bodies` is, so that a remark
    # which merely happens to be a substring of a longer one is not counted.
    old_bodies = {json.loads(l)["text"] for l in old_msgs.splitlines()
                  if l.strip() and not l.startswith("#")}
    old_rest = _tracked_text(baseline, "data/docs") + _tracked_text(baseline, "data/emails")
    before = {s for s in planted_strings()
              if s in old_bodies or s in old_rest}
    lost = sorted(before - present)
    for text in lost[:10]:
        problems.error(f"planted remark lost by an edit: {text[:90]!r}")
    print(f"  plants: {len(before)} planted remark(s) were baked into the corpus, "
          f"{len(lost)} lost")

    # 2. No chat message moved. 287 clues anchor by "HH:MM author", so a
    #    timestamp or author edit silently detaches a clue from its neighbour,
    #    while a text edit does not.
    try:
        old = subprocess.run(["git", "show", f"{baseline}:data/messages.jsonl"],
                             cwd=REPO, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        problems.warn(f"cannot read {baseline}:data/messages.jsonl; skipping anchor check")
        return
    before = [json.loads(l) for l in old.splitlines() if l.strip() and not l.startswith("#")]
    if len(before) != len(corpus.messages):
        problems.error(
            f"message count changed ({len(before)} -> {len(corpus.messages)}); "
            "clues anchor by position in a channel-day")
    moved = 0
    for was, now in zip(before, corpus.messages):
        for field in ("created_at", "author", "channel", "id", "thread_id"):
            if was.get(field) != now.get(field):
                problems.error(
                    f"#{now['channel']} {now['created_at'][:16]}: {field} changed "
                    f"({was.get(field)!r} -> {now.get(field)!r}); clues anchor on it")
                moved += 1
    print(f"  plants: {len(corpus.messages)} messages, {moved} anchor field(s) changed")

    # 3/4. A carrier page must still be older than every clue planted on it.
    carrier_pages, carrier_threads = carriers()
    by_rel = {p["rel"]: p for p in corpus.pages}
    checked = 0
    for rel, dates in sorted(carrier_pages.items()):
        page = by_rel.get(rel)
        if page is None:
            continue  # a page the plant creates at injection time
        checked += 1
        earliest = min((d for d in dates if d), default=None, key=_at)
        if earliest and _at(page["created_at"]) > _at(earliest):
            problems.error(
                f"{rel} is dated {page['created_at'][:16]} but carries a planted "
                f"comment at {earliest[:16]}")
    print(f"  plants: {checked} carrier page(s) checked against their clue dates")

    # 5. A mail thread root carries planted replies; its Date is load-bearing.
    roots = [corpus.mail[mid]["subject"] for mid in carrier_threads if mid in corpus.mail]
    print(f"  plants: {len(roots)} mail thread root(s) are carriers — do not retime "
          f"{', '.join(repr(r[:38]) for r in sorted(roots))}")


# =============================================================================
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=REPO / "data")
    ap.add_argument("--fix", action="store_true",
                    help="retime pages and announcement mails to agree with the chat")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --fix, show what would move and write nothing")
    ap.add_argument("--plants", action="store_true",
                    help="check that no edit has broken a planted task")
    ap.add_argument("--baseline", default="",
                    help="git ref to compare chat anchors against (default: the "
                         "last commit that changed a plant)")
    args = ap.parse_args()

    problems = wl.Problems()
    corpus = Corpus(args.data_dir, problems)
    print(f"corpus: {len(corpus.messages)} messages, {len(corpus.pages)} pages, "
          f"{len(corpus.comments)} comments, {len(corpus.mail)} mails, "
          f"{len(corpus.forge)} issues/PRs")

    if args.fix:
        # Artifacts move, chat does not. A page or a mail carries one timestamp
        # and no anchor; a chat message carries a clue anchored to its minute.
        apply = not args.dry_run
        print("pages:")
        pages = fix_pages(corpus, apply)
        print("mail:")
        mails = fix_mail(corpus, apply)
        verb = "moved" if apply else "would move"
        print(f"\n{verb} {pages} page(s) and {mails} mail(s). "
              "Re-run without --fix; what is left needs a wording change.")
        return
    if args.plants:
        check_plants(corpus, args.baseline or plant_baseline())
    else:
        for check in STORY_CHECKS:
            start = len(problems.errors)
            check(corpus)
            print(f"  {check.__name__:28s} {len(problems.errors) - start:4d}")

    problems.raise_if_any()
    print("clean")


if __name__ == "__main__":
    main()
