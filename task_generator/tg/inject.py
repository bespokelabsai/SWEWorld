"""Write a plant into the corpus, so the remarks are findable instead of handed over.

The clues arm pastes all fifty remarks into the prompt. That measures whether an
agent can *use* scattered evidence, and it is the ceiling for what this writes: the
same fifty remarks, in the same rooms on the same days, said by the same people —
but sitting in nine months of chat, a wiki and a mailbox, where somebody has to go
and find them.

Everything about where each remark goes was decided when the plant was made, against
this same corpus: `carrier` names the room, the day, and for the fifteen that land in
something that already exists, the message to sit after or the page to hang off.
`tg/corpus.py` reads that corpus; this is the other half, and the only code in the
package that writes to it.

Three things shape the implementation, all of them read out of `scripts/ingest_chat.py`
rather than assumed:

**A chat message needs no id.** `id` is required only on a message somebody replies
to, and `build_import_lines` orders a channel by `created_at`, not by file order or
by id. So a remark going into a day that already happened is appended to the end of
`messages.jsonl` with a timestamp in the middle of that day, and nothing has to be
renumbered — which matters, because renumbering a day would rewrite ids that existing
`thread_id`s point at.

**Timestamps carry an offset or the ingest refuses them.** `worldlib.parse_ts` treats
a naive stamp as a hard error.

**Mail and wiki already have writers.** `data_gen/worldapps.py`'s `Mail.send` and
`Wiki.comment` emit exactly the shapes `ingest_mail.py` and `ingest_comments.py` read,
including the sender-plus-recipient copies and the index line per file. Reimplementing
either here would be a second place for those schemas to be wrong.

The gate at the end is a substring search, not a judgement: every remark, and every
identifier it is required to type, has to come back out of the files that were
written. Whether a remark reads well is what the re-knit pass and the review document
are for; whether it is *there* is not a question anybody should be answering by eye.
"""
from __future__ import annotations

import collections
import datetime as dt
import email
import itertools
import json
import pathlib
import re
import shutil
import sys

from .corpus import RUNS, Corpus
from .model import REPO, load

DATA_GEN = REPO / "data_gen"


def worldapps():
    """`data_gen` is not a package; import its module by path, once."""
    if str(DATA_GEN) not in sys.path:
        sys.path.insert(0, str(DATA_GEN))
    import worldapps
    return worldapps


def stamp(date: str, minute: str) -> str:
    """`2025-04-24` + `14:02` -> an ISO stamp the ingest will accept."""
    hh, _, mm = (minute or "10:00").partition(":")
    when = dt.datetime.fromisoformat(date).replace(
        hour=int(hh) % 24, minute=int(mm or 0) % 60, tzinfo=dt.timezone.utc)
    return when.isoformat()


def clues_of(ledger: dict) -> list[dict]:
    return [c for t in ledger["tasks"] for r in t["requirements"] for c in r["clues"]]


# ---------------------------------------------------------------------------
# one shape for a turn, and one answer to "what must be in the corpus"
# ---------------------------------------------------------------------------
# An exchange is written by one stage that speaks chat -- `author`/`text` -- and
# is then read by a chat writer, a mail writer, a read-back gate and an answer
# key. Each of those grew its own idea of the field names and its own idea of
# what to search for, and each was wrong in a different way: mail sent four
# threads from `None@world.local` with empty bodies, and the answer key emitted
# fifty rows of `?` because it still looked for the remark as one string after
# the remark had been deliberately split across seven turns.
#
# Both are the same bug. Everything below goes through these two functions.
def who_said(msg: dict) -> str:
    return msg.get("author") or msg.get("sender") or ""


def what_said(msg: dict) -> str:
    return msg.get("text") or msg.get("body") or ""


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def turns(clue: dict) -> list[dict]:
    """The exchange, or the bare remark for a clue that never got one."""
    msgs = (clue.get("invented") or {}).get("messages") or []
    return msgs or [{"author": clue["holder"], "text": clue["text"]}]


def must_appear(clue: dict) -> list[str]:
    """Every string this clue puts into the corpus, normalised for searching.

    The single answer to "did it land". A caller that asks a different question
    -- the remark as written, say -- gets a different and wrong answer the moment
    the exchange stops quoting it whole.
    """
    return [flat(what_said(m)) for m in turns(clue) if flat(what_said(m))]


# ---------------------------------------------------------------------------
# the five ways a remark lands
# ---------------------------------------------------------------------------
def write_chat(rows: list[dict], clue: dict, corpus: Corpus) -> list[str]:
    """The exchange this remark was made in, written into its channel and day.

    Both carrier kinds land the same way now: a run of messages. The difference is
    only where the clock starts — an invented thread picks its own minutes, and one
    seeded into a day that already happened starts just after the message it joins,
    so it reads as somebody picking up on what was being said rather than as a
    conversation running in parallel with no connection to it.
    """
    carrier = clue["carrier"]
    channel = (carrier.get("channel") or "engineering").lstrip("#")
    date = carrier.get("date") or ""
    msgs = (clue.get("invented") or {}).get("messages") or []
    if not msgs:
        return [f"{clue['clue_id']}: no exchange to write"]

    offset = None
    if carrier.get("kind") == "chat_insert":
        day = corpus.by_channel_day.get((channel, date)) or []
        after, _, who = (carrier.get("insert_after") or "").partition(" ")
        at = next((i for i, m in enumerate(day)
                   if m.created_at[11:16] == after and (not who or m.author == who)),
                  None)
        if at is None:
            return [f"{clue['clue_id']}: no message at "
                    f"{carrier.get('insert_after')!r} in #{channel} on {date}"]
        # Two minutes after the message it answers, then the exchange's own spacing
        # laid over that. A reply stamped at the same minute as what it replies to
        # sorts arbitrarily against it and can come out first.
        first = dt.datetime.fromisoformat(stamp(date, msgs[0].get("minute")))
        offset = (dt.datetime.fromisoformat(day[at].created_at)
                  + dt.timedelta(minutes=2)) - first

    for msg in msgs:
        when = dt.datetime.fromisoformat(stamp(date, msg.get("minute")))
        if offset:
            when += offset
        rows.append({"channel": channel, "author": who_said(msg),
                     "created_at": when.isoformat(), "text": what_said(msg)})
    return []


def page_body(inv: dict, clue: dict) -> str:
    """The invented page as markdown, from the shape the planter actually emits.

    `clue_schemas.DOCUMENT` requires `sections: [{heading, body}]` and nothing
    else. The writer here asked for `body` or `summary`, which the planter has
    never produced, so every `doc_new` fell through to the one-sentence fallback
    and the authored page -- the only carrier whose text BookStack's search
    actually indexes, comments being invisible to it -- shipped as a stub with
    the remark's own summary as its entire content.

    Falls back to the same sentence only when there is genuinely nothing else,
    because a page that exists is still better than comments hung on a path that
    does not: `ingest_comments` refuses every row with "unknown document".
    """
    sections = inv.get("sections") or []
    parts = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        heading = (section.get("heading") or "").strip()
        body = (section.get("body") or "").strip()
        if heading:
            parts.append(f"## {heading}")
        if body:
            parts.append(body)
    if parts:
        return "\n\n".join(parts)
    return (inv.get("body") or inv.get("summary")
            or clue.get("settles") or clue["text"])


def write_doc_edit(target: pathlib.Path, clue: dict) -> list[str]:
    """A section added to a page that already exists, in the page's own body.

    The strongest wiki placement there is, and until now the only one with no
    writer. `slot_of` has mapped a `page` candidate to `doc_edit` all along --
    the corpus offers one whenever the remark's holder is the page's author, so
    an edit is always somebody editing their own page -- and `inject` sent every
    `doc*` kind to `write_comment`, which would have hung comments off it
    instead.

    It matters because of what the two surfaces are worth to a reader.
    BookStack's `/api/search` does not index page comments, so a comment-only
    remark is reachable only by opening that exact page and scrolling. A section
    in the body is indexed, and is the one wiki carrier an agent can FIND rather
    than stumble onto.

    Appended rather than spliced: the frontmatter and the existing prose are
    untouched, so `ingest_docs` parses it exactly as before and the page's own
    history stays true.
    """
    rel = (clue["carrier"].get("key") or "|").split("|")[1]
    path = target / "docs" / rel
    if not path.is_file():
        return [f"{clue['clue_id']}: no page at {rel} to edit"]

    inv = clue.get("invented") or {}
    sections = [s for s in (inv.get("sections") or []) if isinstance(s, dict)]
    if sections:
        block = "\n\n".join(
            (f"## {(s.get('heading') or '').strip()}\n\n{(s.get('body') or '').strip()}"
             if s.get("heading") else (s.get("body") or "").strip())
            for s in sections if (s.get("heading") or s.get("body")))
    else:
        # No invented section: the remark itself, under a heading taken from the
        # carrier. A page edit is prose, so the exchange's turns are joined
        # rather than laid out as a transcript -- a page that reads like chat is
        # a tell, and `too_wordy` would be right to call it one.
        heading = (clue["carrier"].get("anchor") or "").strip() or "Notes"
        body = "\n\n".join(flat(what_said(m)) for m in turns(clue)
                           if flat(what_said(m)))
        block = f"## {heading}\n\n{body}"

    text = path.read_text(encoding="utf-8").rstrip("\n")
    path.write_text(f"{text}\n\n{block}\n", encoding="utf-8")
    return []


def write_comment(wiki, clue: dict, taken: set[str]) -> list[str]:
    """The exchange in the margin of a page, as a comment and its replies.

    `Wiki.comment` mints `c-<page>-<n>` from the number of comments IT has made,
    which for a store built over an existing corpus is zero. Both of g1's page
    comments went to the same page and both came out `...-md-0`; the bake ran the
    whole world and then died on `duplicate comment id`, after BookStack was
    populated. The ingest was right and the writer was wrong.
    """
    rel = (clue["carrier"].get("key") or "").split("|")[1]
    # A `doc_new` carrier brings a page with it, and until now nothing wrote one:
    # the comments went in against a path that existed nowhere, and
    # `ingest_comments` refused every row with "unknown document
    # 'engineering/capping-code-executor-output.md'". The page is what the
    # exchange is a margin note ON, so it has to exist first.
    inv = clue.get("invented") or {}
    if str(clue["carrier"].get("kind") or "") == "doc_new" and rel not in wiki._pages:
        title = inv.get("title") or clue["carrier"].get("title") or \
            rel.rsplit("/", 1)[-1].removesuffix(".md").replace("-", " ")
        wiki.write(uid=clue["holder"], title=title,
                   body=page_body(inv, clue),
                   collection=rel.split("/", 1)[0],
                   ts=stamp(clue["carrier"]["date"], "09:30"))
    stem = f"c-{rel.rsplit('/', 1)[-1].removesuffix('.md')}"
    msgs = turns(clue)
    root = ""
    for i, msg in enumerate(msgs):
        ident = next(f"{stem}-{n}" for n in itertools.count()
                     if f"{stem}-{n}" not in taken)
        taken.add(ident)
        wiki.comment(uid=who_said(msg) or clue["holder"], rel=rel,
                     text=what_said(msg), ident=ident, reply_to=root,
                     ts=stamp(clue["carrier"]["date"],
                              msg.get("minute") or f"10:{30 + i * 7:02d}"))
        root = root or ident
    return []


def write_mail(mail, clue: dict, threads: dict) -> list[str]:
    carrier, kind = clue["carrier"], clue["carrier"].get("kind")
    if kind == "mail_new":
        inv = clue.get("invented") or {}
        subject = inv.get("subject") or carrier.get("title") or "(no subject)"
        parent = ""
        for msg in inv.get("messages") or []:
            # A mail exchange and a chat exchange come out of the same stage, and
            # that stage speaks chat: `author`/`text`. Reading only `sender`/`body`
            # here sent four threads out from `None@world.local` with empty bodies,
            # and they failed the read-back rather than the write, which is the
            # gate working and the writer not.
            sender = who_said(msg)
            to = [r for r in (msg.get("to") or []) if r != sender]
            if not to:
                to = [p for p in (inv.get("participants") or []) if p != sender]
            if not to:
                # Everyone else actually in the exchange. `participants` is written
                # at placement time and `reknit` rewrites the conversation
                # afterwards with whoever the room really had, so the two drift and
                # a thread can end up addressed to nobody -- `mail.send` returns no
                # Message-ID, the remark reaches the corpus nowhere, and the
                # read-back gate reports "6 of 6 turns not in the corpus", which
                # reads like a writer fault rather than an empty To: line.
                to = [a for a in dict.fromkeys(who_said(m) for m in turns(clue))
                      if a and a != sender]
            mid = mail.send(uid=sender, to=to,
                            subject=subject if not parent else f"Re: {subject}",
                            body=what_said(msg),
                            ts=stamp(inv.get("date") or carrier["date"],
                                     msg.get("minute")),
                            in_reply_to=parent)
            if not mid:
                return [f"{clue['clue_id']}: nobody to send to from {sender}"]
            parent = parent or mid
        return []

    # mail_reply: the carrier key IS the Message-ID of the message being answered,
    # and the exchange hangs off it as a chain rather than a single reply.
    mid = (carrier.get("key") or "").split("|", 1)[1]
    thread = threads.get(mid)
    if not thread:
        return [f"{clue['clue_id']}: no mail with Message-ID {mid}"]
    everyone = [t.split("@")[0] for t in [thread["from"], *thread["to"]]]
    subject = f"Re: {thread['subject'].removeprefix('Re: ')}"
    parent = mid
    for i, msg in enumerate(turns(clue)):
        sender = who_said(msg) or clue["holder"]
        to = [r for r in everyone if r != sender] or [thread["from"].split("@")[0]]
        sent = mail.send(uid=sender, to=to, subject=subject,
                         body=what_said(msg),
                         ts=stamp(carrier["date"], msg.get("minute") or f"11:{15 + i * 6:02d}"),
                         in_reply_to=parent)
        if not sent:
            return [f"{clue['clue_id']}: nobody to send to from {sender}"]
        parent = sent
    return []


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------
def readable(root: pathlib.Path) -> str:
    """Everything in the corpus, as a reader of it would see it.

    Decoded, not raw. `messages.jsonl` holds `{\"num_jobs\": n}` escaped, and an
    `.eml` body is quoted-printable, so a remark comes back out of the file as
    `next to the request=\ns,`. Both are correct on disk and invisible to a
    substring search over the bytes -- six of g1's fifty read as missing from a
    corpus that had them, which is the gate lying in the safe direction and still
    lying.
    """
    parts = []
    for name in ("messages.jsonl", "comments.jsonl"):
        path = root / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            parts.append(row.get("text") or "")
    for path in sorted(root.glob("docs/**/*.md")):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    for path in sorted(root.glob("emails/**/*.eml")):
        note = email.message_from_bytes(path.read_bytes())
        body = note.get_payload(decode=True)
        parts.append(body.decode("utf-8", "replace") if body
                     else str(note.get_payload()))
    # One space for any run of whitespace: a mail body is hard-wrapped at 78
    # columns, so a remark longer than a line has a newline in the middle of it
    # that the reader never sees.
    return re.sub(r"\s+", " ", "\n".join(parts))


def absent(root: pathlib.Path, ledger: dict) -> list[str]:
    """What the corpus does not carry: an identifier, or a whole exchange.

    No longer a search for the remark as one string -- a remark is deliberately
    split across several turns now, so the string it was written as appears
    nowhere. Two things are still absolute and still checked here, against what
    was actually written rather than against what was meant to be:

    an identifier the tests read by name (a name cannot be inferred), and the
    exchange itself, sampled by its opening turn.

    Whether every CLAIM survived the split is judged when the exchange is written
    (`clues.check_carriage`) and recorded on the clue as `uncarried`, because that
    question needs a reader and this one needs a substring.
    """
    hay = readable(root)
    out = []
    for clue in clues_of(ledger):
        if not clue.get("carrier"):
            continue
        gone = [t for t in must_appear(clue) if t not in hay]
        if gone:
            out.append(f"{clue['clue_id']}: {len(gone)} of "
                       f"{len(must_appear(clue))} turn(s) not in the corpus")
        for name in clue.get("verbatim") or []:
            if flat(name) not in hay:
                out.append(f"{clue['clue_id']}: wrote it without `{name}`")
        for part in clue.get("uncarried") or []:
            out.append(f"{clue['clue_id']}: nothing carries — {part[:70]}")
    return out


def timing(corpus: Corpus, ledger: dict) -> list[str]:
    """Exchanges that could not plausibly have happened when they say they did.

    This corpus is a SAMPLE -- 161 days of traffic over fifteen months -- so a
    channel being quiet on a given day is the normal case and not a finding. Two
    things are not normal, and a reader notices both before anything else:

    a date on which the whole company said nothing except this one exchange, and
    a near-daily channel whose only traffic that day is this one exchange.

    g1 shipped one of each: a seven-message #engineering thread on 2025-06-17, a
    date the corpus does not otherwise cover, and one in #code-review -- live on
    94% of the corpus's active days -- on a day it was otherwise silent. Nothing
    caught either, because `spread()` asks that remarks be far APART and never
    asks whether anybody was in the room.
    """
    live = {day for _, day in corpus.by_channel_day}
    rate = collections.Counter(channel for channel, _ in corpus.by_channel_day)
    out = []
    for clue in clues_of(ledger):
        carrier = clue.get("carrier") or {}
        if not str(carrier.get("kind") or "").startswith("chat"):
            continue
        channel = (carrier.get("channel") or "").lstrip("#")
        day = carrier.get("date")
        if day not in live:
            out.append(f"{clue['clue_id']}: #{channel} {day} — nothing else in the "
                       "corpus happens that day, so this exchange is the only thing "
                       "on the date")
        elif ((channel, day) not in corpus.by_channel_day
              and rate[channel] / max(len(live), 1) > 0.8):
            out.append(f"{clue['clue_id']}: #{channel} {day} — that channel posts on "
                       f"{rate[channel] / len(live):.0%} of active days and is "
                       "otherwise silent here")
    return out


def unsearchable(ledger: dict, task) -> list[str]:
    """Graded identifiers typed only where the world's search cannot reach them.

    BookStack's `/api/search` indexes pages, not comments. All five of this
    corpus's page comments are in its database and none of them come back for any
    term in their own text, so a remark planted as a comment is reachable only by
    opening the page it hangs off -- which `/api/pages/{id}` does return, comments
    and all, and which the instruction points the agent at.

    So this is not a break, and it is not gated. It is the one thing about the
    in-world arm that a reader of the plant cannot see: a name carried by one
    remark on an unsearchable surface is a single point of failure for whichever
    fact its test reads it by name, and "a name cannot be inferred, a rule can".
    """
    from . import surface as surf
    graded = {n for need in surf.required(task).values() for n in need.all_names}
    seen = collections.defaultdict(set)
    for clue in clues_of(ledger):
        kind = (clue.get("carrier") or {}).get("kind") or ""
        where = ("wiki-comment" if kind == "doc_comment"
                 else "wiki" if kind.startswith("doc")
                 else "mail" if kind.startswith("mail") else "chat")
        for name in graded:
            if name in (clue.get("text") or ""):
                seen[name].add(where)
    return [f"`{name}` is typed only in a page comment, which BookStack search "
            f"does not index — reachable by reading the page, not by searching"
            for name, where in sorted(seen.items()) if where == {"wiki-comment"}]


def crowding(rows: list[dict], corpus: Corpus, ledger: dict) -> list[str]:
    """Invented threads that land on top of a conversation already in the room.

    Twelve of g1's thirty-two go into a channel-day that already has traffic. That
    is not wrong — a channel holds more than one conversation — but two threads
    interleaved minute by minute read as one incoherent one, and only a person can
    tell which it is. Reported for the review document, never gated on.
    """
    out = []
    for clue in clues_of(ledger):
        carrier = clue.get("carrier") or {}
        if carrier.get("kind") != "chat_thread":
            continue
        channel = (carrier.get("channel") or "").lstrip("#")
        day = corpus.by_channel_day.get((channel, carrier.get("date"))) or []
        if not day:
            continue
        mine = [r["created_at"] for r in rows
                if r["channel"] == channel and r["created_at"][:10] == carrier["date"]]
        if not mine:
            continue
        lo, hi = min(mine), max(mine)
        inside = [m for m in day if lo <= m.created_at <= hi]
        if inside:
            out.append(f"{clue['clue_id']}: #{channel} {carrier['date']} — "
                       f"{len(inside)} existing message(s) fall inside the new "
                       f"thread's {lo[11:16]}–{hi[11:16]}")
    return out


# ---------------------------------------------------------------------------
def inject(slug: str, *, run: str | None = None, out: str | None = None,
           dry_run: bool = False) -> dict:
    """Copy the corpus, write the plant into the copy, read it back."""
    task = load(slug)
    source = pathlib.Path(run) if run else Corpus().root
    target = pathlib.Path(out) if out else RUNS / f"{source.name}-{task.id}"
    ledger = json.loads((task.dir / "clues" / "plant.json").read_text())
    corpus = Corpus(source)

    if not dry_run:
        # A fresh copy every time: writing twice into one corpus doubles every
        # remark, and a doubled remark still passes a substring gate.
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, symlinks=True)

    wa = worldapps()
    clock = wa.Clock()
    boxes = sorted({p.name for p in (source / "emails").glob("*@*")})
    addresses = {b.split("@")[0]: b for b in boxes}
    mail = wa.Mail(target, clock, domain="world.local", addresses=addresses)
    mail.rehydrate()
    # Filenames are `<n>-<subject-slug>.eml` and `_n` restarts at zero after a
    # rehydrate, so a new mail on an old subject would overwrite the old file.
    mail._n = 9000
    threads = {t["mid"]: t for t in mail._threads.values()}
    wiki = wa.Wiki(target, clock, collections={})
    taken = {json.loads(line)["id"]
             for line in (target / "comments.jsonl").read_text().splitlines()
             if line.strip() and not line.startswith("#")
             and "id" in json.loads(line)} if (target / "comments.jsonl").is_file() else set()

    rows: list[dict] = []
    problems: list[str] = []
    counts: collections.Counter = collections.Counter()
    for clue in clues_of(ledger):
        carrier = clue.get("carrier")
        if not carrier:
            problems.append(f"{clue['clue_id']}: never placed")
            continue
        kind = carrier.get("kind") or "chat_insert"
        counts[kind] += 1
        if dry_run:
            continue
        if kind.startswith("chat"):
            problems += write_chat(rows, clue, corpus)
        elif kind == "doc_edit":
            problems += write_doc_edit(target, clue)
        elif kind.startswith("doc"):
            problems += write_comment(wiki, clue, taken)
        elif kind.startswith("mail"):
            problems += write_mail(mail, clue, threads)
        else:
            problems.append(f"{clue['clue_id']}: unknown carrier kind {kind!r}")

    if not dry_run:
        with (target / "messages.jsonl").open("a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    plant_dir = None
    if not dry_run:
        plant_dir = delta(source, target, task.dir / "clues" / "plant-data", rows)

    report = {"source": str(source), "target": str(target), "rows": len(rows),
              "delta": plant_dir,
              "kinds": dict(counts), "problems": problems,
              "absent": [] if dry_run else absent(target, ledger),
              "crowding": [] if dry_run else crowding(rows, corpus, ledger),
              "timing": [] if dry_run else timing(corpus, ledger),
              "unsearchable": [] if dry_run else unsearchable(ledger, task)}
    if not dry_run:
        (task.dir / "clues" / "injected.md").write_text(render(task, ledger, report))
    return report


def delta(source: pathlib.Path, target: pathlib.Path, out: pathlib.Path,
          rows: list[dict]) -> dict:
    """Only what the plant ADDED, in the same layout the ingest scripts read.

    So a task can be injected at container start instead of baked into an image.
    The world image already carries `/opt/world-state/scripts/` and a python with
    yaml and requests, and every ingest script takes `--data-dir`; Mattermost's
    bulk import, BookStack's API and maddy's delivery are all additive, so a
    directory holding only the new rows appends them to the 9,592 already there.

    Computed by diffing the injected copy against the corpus rather than by
    teaching the writers to emit twice. `Mail.rehydrate()` and `Wiki` both need
    the whole corpus in front of them to thread a reply and to number a comment,
    so pointing them at an empty directory would produce mail that replies to
    nothing. Diff after the fact and they keep working exactly as they do now.

    What this replaces: `install_corpus.py --apply` plus `make bake-image`, a
    7.8GB image per task, and `inject.world_image()` scraping a tag out of
    build_tasks.py so the answer key does not name the wrong one.
    """
    if out.exists():
        shutil.rmtree(out)
    (out / "emails").mkdir(parents=True)
    (out / "docs").mkdir(parents=True)

    # The two the ingest scripts map names through. Copied whole: they describe
    # the world, not the plant, and a trimmed identities.yaml would leave an
    # author unresolvable.
    for name in ("channels.yaml", "identities.yaml"):
        if (source / name).is_file():
            shutil.copy2(source / name, out / name)

    (out / "messages.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")

    def lines(path: pathlib.Path) -> list[str]:
        if not path.is_file():
            return []
        return [l for l in path.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")]

    was = set(lines(source / "comments.jsonl"))
    added = [l for l in lines(target / "comments.jsonl") if l not in was]
    (out / "comments.jsonl").write_text(
        "".join(l + "\n" for l in added), encoding="utf-8")

    # `emails/index.jsonl` is a manifest, not content: it lists every message in
    # every mailbox. Copying it whole because it changed shipped 679 rows pointing
    # at 600+ .eml files the delta does not carry, and `ingest_mail` refused all of
    # them with "message file ... does not exist". Diff it by line, like
    # comments.jsonl, so it names only what travelled.
    was_mail = set(lines(source / "emails" / "index.jsonl"))
    new_mail = [l for l in lines(target / "emails" / "index.jsonl") if l not in was_mail]

    files = 0
    for sub in ("emails", "docs"):
        for path in sorted((target / sub).rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(target)
            if rel.as_posix() == "emails/index.jsonl":
                continue                      # written from the line diff below
            old = source / rel
            if old.is_file() and old.read_bytes() == path.read_bytes():
                continue
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, out / rel)
            files += 1

    if new_mail:
        (out / "emails" / "index.jsonl").write_text(
            "".join(l + "\n" for l in new_mail), encoding="utf-8")

    return {"dir": str(out), "messages": len(rows), "comments": len(added),
            "mail_rows": len(new_mail), "files": files}


def render(task, ledger: dict, report: dict) -> str:
    lines = [f"# {task.id} — the plant, written into the corpus", "",
             f"From `{report['source']}`", f"To   `{report['target']}`", "",
             f"{report['rows']} chat message(s) appended.", ""]
    for kind, n in sorted(report["kinds"].items()):
        lines.append(f"- `{kind}` × {n}")
    for label, key in (("Could not be written", "problems"),
                       ("Not found on read-back", "absent"),
                       ("Could not have happened then", "timing"),
                       ("Landed on a busy day — read these", "crowding"),
                       ("Findable only by reading, not by searching",
                        "unsearchable")):
        rows = report[key]
        lines += ["", f"## {label}" + ("" if rows else " — none"), ""]
        lines += [f"- {row}" for row in rows]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# the answer key
# ---------------------------------------------------------------------------
def located(root: pathlib.Path, ledger: dict) -> dict[str, dict]:
    """Where each remark actually ended up, read back out of the written corpus.

    Not out of `carrier`. The carrier says which day and which room; the corpus
    says the minute, and for a `chat_insert` that minute is computed at write time
    from the message it answers. An answer key that quotes the plan rather than the
    artifact is the same mistake as judging `settles` instead of the remark, and it
    would send a reader to a timestamp that does not exist.
    """
    # Keyed on the exchange's FIRST turn, because the remark itself is split
    # across the exchange and appears nowhere as one string. `must_appear` is the
    # one function that knows that; asking any other question here is how this
    # emitted fifty rows of "?" once already.
    want = {c["clue_id"]: must_appear(c)[0]
            for c in clues_of(ledger) if c.get("carrier") and must_appear(c)}
    span = {c["clue_id"]: len(must_appear(c)) for c in clues_of(ledger)}
    found: dict[str, dict] = {}

    def note(cid, **row):
        found[cid] = {**row, "turns": span.get(cid, 1)}

    for line in (root / "messages.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        body = flat(row.get("text") or "")
        for cid, opener in want.items():
            if cid not in found and opener and opener in body:
                note(cid, surface="chat", where=f"#{row['channel']}",
                     when=row["created_at"], who=row["author"])

    comments = root / "comments.jsonl"
    if comments.is_file():
        for line in comments.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            body = flat(row.get("text") or "")
            for cid, opener in want.items():
                if cid not in found and opener and opener in body:
                    note(cid, surface="wiki comment", where=f"docs/{row['doc']}",
                         when=row["created_at"], who=row["author"])

    for path in sorted(root.glob("emails/**/*.eml")):
        if "/Sent/" not in str(path):
            continue                       # one copy per message, the sender's
        note_ = email.message_from_bytes(path.read_bytes())
        raw = note_.get_payload(decode=True)
        body = flat(raw.decode("utf-8", "replace") if raw else "")
        subject = " ".join(str(email.header.make_header(
            email.header.decode_header(note_.get("Subject", "")))).split())
        for cid, opener in want.items():
            if cid not in found and opener and opener in body:
                note(cid, surface="mail", where=f"“{subject}”",
                     when=email.utils.parsedate_to_datetime(
                         note_.get("Date", "")).isoformat(),
                     who=email.utils.parseaddr(
                         note_.get("From", ""))[1].split("@")[0],
                     to=note_.get("To", ""))

    # A row of `?` in the answer key is worse than no answer key: it reads as a
    # rendering quirk rather than as "this renderer no longer understands the
    # plant". Refuse instead.
    lost = sorted(set(want) - set(found))
    if lost:
        raise SystemExit(
            f"cannot locate {len(lost)} of {len(want)} remark(s) in {root}: "
            + ", ".join(lost[:6]) + ". The corpus and the plant disagree — "
            "re-run `cli.py inject` before writing the answer key.")
    return found


HOW = {
    "chat": "Mattermost search, or the channel on that date",
    "wiki comment": "open the page — `/api/pages/{id}` returns its `comments`; "
                    "BookStack search does not index them",
    "mail": "Roundcube, or IMAP on :143 as worldadmin@world.local",
}


def world_image() -> str:
    """The image the world arm boots, read from the one place that decides it.

    Hardcoding it here meant the answer key still named `sweworld:0.4.2` two bakes
    later, and a doc that quietly names the wrong image is worse than one that
    names none.
    """
    text = (REPO / "harbor_tasks" / "build_tasks.py").read_text()
    found = re.search(r'WORLD_IMAGE\s*=\s*"([^"]+)"', text)
    return found.group(1) if found else "the populated world image"



def spread_summary(rows: list, spot: dict) -> list[str]:
    """How far apart the remarks are, counted off the written corpus.

    Hand-written into g1's and g2's keys and absent from g3's, which is the usual
    result of a section that only exists as prose. Worse, g2's said "3 page
    bodies" for three remarks that are page COMMENTS -- the distinction the
    BookStack note below turns on.

    `spread_problems()` is the gate this reports on: every requirement needs at
    least 2 sources, 3 weeks and 2 channels, so no single sitting recovers one.
    """
    from collections import Counter
    kinds = Counter((c.get("kind") or "clue") for _, c in rows)
    per_surface: dict[str, Counter] = {}
    for _, clue in rows:
        at = spot.get(clue["clue_id"], {})
        per_surface.setdefault(at.get("surface", "?"), Counter())[
            at.get("where", "?")] += 1
    channels = len(per_surface.get("chat", {}))

    label = {"chat": "chat (Mattermost)", "wiki comment": "wiki (BookStack)",
             "mail": "mail (Roundcube/IMAP)"}
    out = ["---", "", "## Where the remarks are spread", "",
           f"{len(rows)} remarks in total — {kinds['clue']} clues, "
           f"{kinds['herring']} herrings and {kinds['reversal']} reversals — "
           f"across {len(per_surface)} surfaces and {channels} chat channels. "
           "`spread_problems()` is the gate that forces this: every requirement "
           "needs at least 2 sources, 3 weeks and 2 channels, so no single "
           "sitting recovers one.", "",
           "| surface | remarks | where they sit |", "|---|---|---|"]
    for surface, where in sorted(per_surface.items(),
                                 key=lambda kv: -sum(kv[1].values())):
        total = sum(where.values())
        if surface == "chat":
            sits = ", ".join(f"`{w}` {n}" for w, n in where.most_common())
        elif surface == "mail":
            sits = f"{total} separate thread{'s' if total != 1 else ''}"
        else:
            sits = f"{total} page comment{'s' if total != 1 else ''}"
        out.append(f"| {label.get(surface, surface)} | **{total}** | {sits} |")
    # Only when a remark really is in a comment. Stated unconditionally it would
    # be false for a plant whose wiki remarks are page bodies.
    if per_surface.get("wiki comment"):
        out += ["", "> **The wiki remarks are page _comments_, not page bodies.** "
                "BookStack's `/api/search` does not index comments, so a term that "
                "lives only in one returns nothing. `/api/pages/{id}` returns them "
                "alongside the body — an agent that searches instead of enumerating "
                f"never sees these {sum(per_surface['wiki comment'].values())}."]
    return out + [""]

def answer_key(task, ledger: dict, root: pathlib.Path) -> str:
    """The operator's map: the ticket, the hidden requirements, and every remark."""
    from .model import FACT_FIELDS
    entry = ledger["tasks"][0]
    spot = located(root, ledger)
    rows = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            if clue.get("carrier"):
                rows.append((req["req_id"], clue))
    rows.sort(key=lambda r: (spot.get(r[1]["clue_id"], {}).get("when", "9999"),
                             r[1]["clue_id"]))

    # The count is read off the plant. It used to be the literal 50 -- g1's number
    # -- printed for every task, so g2's key claimed "all 50 remarks" about a plant
    # holding 46. The `measured` column went the same way: it asserted g1's 0.00 /
    # 1.00 / 1.00 for tasks whose arms had never been run. Nothing on disk sources
    # those numbers, so the column is gone rather than guessed.
    n = len(rows)
    out = [f"# {task.id} — {entry['title']}", "",
           "**This is the answer key.** Nothing here is shown to an agent in any "
           "arm. The `blind` and `world` arms get the ticket and nothing else; "
           "`spec` also gets the hidden requirements; `clues` gets the remarks "
           "quoted in its prompt but never their dates' meaning, who is wrong, or "
           "which fact anything carries.", "",
           "| arm | what it is handed |", "|---|---|",
           "| `blind` | the ticket |",
           "| `spec` | the ticket + both hidden requirements |",
           f"| `clues` | the ticket + all {n} remarks, quoted |",
           f"| `world` | the ticket, against `{world_image()}` where the {n} "
           "remarks live in chat, the wiki and mail |", "",
           "Scores are per run and live with the run, not here.", "",
           "---", "", "## The hidden requirements — stated nowhere", "",
           "Each is graded as five independent facts, 0.1 each. `open_feature` "
           "carries weight 0.0: building the feature scores nothing, only "
           "recovering what nobody wrote down does.", ""]

    for req in entry["requirements"]:
        out += [f"### `{req['req_id']}`", ""]
        for field in FACT_FIELDS:
            if (req.get("requirement") or {}).get(field):
                out += [f"- **`{field}`** — {req['requirement'][field]}", ""]
        if req.get("earlier_reversed_version"):
            out += ["> *The decision the team made first and later reversed:* "
                    + req["earlier_reversed_version"], ""]

    out += spread_summary(rows, spot)

    # The tree, before the remark list. `tree.md` has carried it since the plant
    # was built and nothing pointed at it, so the one document an operator opens
    # showed WHERE each remark is and never what it is FOR. The subconclusions are
    # the reasoning the task is actually testing: a reader who finds every remark
    # and cannot make these leaps has not solved it.
    from .clues import render_tree
    out += ["---", "",
            "## The MuSR tree — what a reader has to work out", "",
            "Each requirement decomposes into subconclusions, and each of those "
            "is implied by remarks that never state it. *The leap nobody states* "
            "is the inference the task is testing; no single remark contains it.",
            ""]
    out += [line for line in render_tree(ledger).splitlines()[2:]]
    out += ["", "---", "", "## The ticket — stated openly", "",
            f"**{entry['title']}**", "", entry["description"], ""]
    out += ["", "---", "", "## Where every remark is", "",
            f"{len(rows)} remarks, oldest first. **Quotes are exact** — they are "
            "read back out of the corpus, not out of the plan, so the timestamps "
            "are the ones in the world.", "",
            "`herring` is a decision the team really made and later reversed; the "
            "remark that overturns it is always strictly later and says so. "
            "`reversal` is that retraction.", "",
            "| when | surface | where | who | remark | turns | kind | carries |",
            "|---|---|---|---|---|---|---|---|"]
    for rid, clue in rows:
        at = spot.get(clue["clue_id"], {})
        # A reversal carries facts like any other remark, so labelling it off an
        # empty `covers` marked none of the four. `kind` is the field that knows.
        kind = {"herring": "**herring**",
                "reversal": f"**reversal** of `{clue.get('reverses') or '?'}`"
                }.get(clue.get("kind"), "clue")
        carries = ", ".join(f"`{f}`" for f in clue.get("covers") or []) or "—"
        out.append(f"| {(at.get('when') or '')[:10]} | {at.get('surface', '?')} "
                   f"| {at.get('where', '?')} | {at.get('who', clue['holder'])} "
                   f"| [`{clue['clue_id']}`](#{clue['clue_id'].replace('.', '')}) "
                   f"| {len((clue.get('invented') or {}).get('messages') or []) or 1} "
                   f"| {kind} | {carries} |")
    out.append("")

    for rid, clue in rows:
        at = spot.get(clue["clue_id"], {})
        kind = clue.get("kind", "clue")
        tag = {"herring": " · **herring**", "reversal": " · **reversal**"}.get(kind, "")
        carries = ", ".join(f"`{rid}.{f}`" for f in clue.get("covers") or [])
        out += [f"#### `{clue['clue_id']}`{tag}", "",
                f"- **{at.get('surface', '?')}** · {at.get('where', '?')} · "
                f"**{at.get('who', clue['holder'])}** · "
                f"{(at.get('when') or '')[:16].replace('T', ' ')}"]
        if at.get("to"):
            out.append(f"- to {at['to']}")
        out.append("- carries " + (carries or "nothing — it is here to be wrong"))
        if clue.get("reverses"):
            out.append(f"- takes back `{clue['reverses']}`")
        if clue.get("verbatim"):
            out.append("- must be typed literally: "
                       + ", ".join(f"`{v}`" for v in clue["verbatim"]))
        out += [f"- find it: {HOW.get(at.get('surface'), '—')}", ""]
        turns = (clue.get("invented") or {}).get("messages") or []
        if turns:
            # The exchange, as it is in the corpus. The remark is deliberately not
            # any one of these lines — quoting it alone would send a reader looking
            # for a sentence nobody says.
            out += ["What the remark has to leave a reader with:", "",
                    "> " + clue["text"].replace("\n", "\n> "), "",
                    "As it appears, spread across the exchange:", "", "```"]
            for msg in turns:
                who = who_said(msg) or "?"
                body = what_said(msg).replace("\n", " ")
                out.append(f"{msg.get('minute') or '--:--'}  {who:9} {body}")
            out += ["```", ""]
        else:
            out += ["> " + clue["text"].replace("\n", "\n> "), ""]
    return "\n".join(out) + "\n"
