#!/usr/bin/env python3
"""Emit the `world-located` arm: the world arm, plus a map of where every remark is.

The world arm asks two questions at once and reports one number. An agent that
scores zero on it either never FOUND the fifty remarks in nine months of chat, a
wiki and a mailbox, or found them and could not work out what they add up to.
`-clues` answers the second question -- it pastes the remarks into the ticket and
scores 1.00 -- but it also takes the corpus away, so it cannot say what the search
itself costs.

This arm takes away the search and nothing else. Same world, same corpus, the same
fifty conversations sitting exactly where they sit; the ticket names each one's
channel, day, minute and length, or its page, or its mail subject. The agent still
has to open them, read around them, and infer.

So the withholding is `clue_digest.WITHHELD` one step further: no quotes either. A
row says where a conversation is and stops. It does not say which requirement a
conversation serves (that is the tree), how many requirements there are (the clue
ids are grouped `r1`/`r2` and would give it away), which four are herrings (`kind`),
or which fact a remark carries (`covers`). Anything more and this stops measuring
inference and starts measuring reading comprehension of the answer key.

    python3 harbor_tasks/build_located_arm.py batch-payload-plan --print
    python3 harbor_tasks/build_located_arm.py batch-payload-plan

Locations are read back out of the corpus rather than out of the plant, through
`tg.inject.located` -- the same function the answer key uses, for the same reason:
the carrier says which day and which room, the corpus says the minute.

Nothing here regenerates the arm it copies. g1 is FROZEN in build_tasks.py because
its four measured arms are only comparable while the artifacts that produced them do
not move; this adds a fifth beside them by copying the world arm's environment,
tests and solution byte for byte and rewriting two files.
"""
from __future__ import annotations

import argparse
import email
import email.header
import email.utils
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "task_generator"))

from tg import inject                      # noqa: E402
from tg.model import load                  # noqa: E402

SUFFIX = "-world-located"

# Corpora pulled out of images, so a rebuild does not pay for the copy twice.
CACHE = ROOT / ".located-corpora"

# Verified against the image the world arm boots: every persona's mail is
# ALSO delivered to worldadmin, whose INBOX holds 107 messages in
# sweworld:0.4.4 including all four of g1's threads. data/emails/ has no
# worldadmin mailbox at all, so a row derived from the corpus alone would send
# the agent to a mailbox it has no password for.
MAIL_HOME = "`worldadmin@world.local`'s INBOX"


def corpus_root(spec: str | None) -> pathlib.Path:
    """A path, or `image:<tag>` for the corpus baked into a world image.

    The map has to describe the world the arm BOOTS, and for a task whose plant
    was baked in, the image is the only place that world is defined. `data/` has
    moved on since: it locates g1's fifty remarks correctly but has three of its
    chat exchanges a message shorter, so a map built from it quietly miscounts
    what the agent will find. A task whose plant is ingested at run time is the
    other case -- there the arm's own `environment/plant` is the corpus.

    Every world image carries the corpus it was built from at
    /opt/world-state/data, which is what makes this a one-liner rather than a
    reconstruction.
    """
    if not spec:
        return REPO / "data"
    if not spec.startswith("image:"):
        return pathlib.Path(spec)
    tag = spec[len("image:"):]
    into = CACHE / re.sub(r"[^A-Za-z0-9._-]", "_", tag)
    if (into / "messages.jsonl").is_file():
        return into
    into.parent.mkdir(parents=True, exist_ok=True)
    made = subprocess.run(["docker", "create", tag], capture_output=True, text=True)
    if made.returncode:
        raise SystemExit(f"docker create {tag}: {made.stderr.strip()[:400]}")
    container = made.stdout.strip()
    try:
        got = subprocess.run(
            ["docker", "cp", f"{container}:/opt/world-state/data", str(into)],
            capture_output=True, text=True)
        if got.returncode:
            raise SystemExit(f"docker cp from {tag}: {got.stderr.strip()[:400]}")
    finally:
        subprocess.run(["docker", "rm", container], capture_output=True)
    return into


def locate(root: pathlib.Path, task) -> tuple[str, dict, dict]:
    """(snapshot name, ledger, where each remark is) — the first one that locates."""
    misses = []
    for name in ["clues"] + sorted(p.name for p in task.dir.glob("clues.*")):
        path = task.dir / name / "plant.json"
        if not path.is_file():
            continue
        ledger = json.loads(path.read_text())
        try:
            return name, ledger, inject.located(root, ledger)
        except SystemExit as exc:
            misses.append(f"  {name}: {str(exc).split(' remark')[0]}")
    raise SystemExit(f"no plant under {task.dir} is in {root}:\n" + "\n".join(misses))


def landed(root: pathlib.Path, ledger: dict) -> dict[str, tuple[int, str, str]]:
    """(how many records each remark actually became, first stamp, last stamp).

    Counted off the corpus, never off the plant's turn list, because the two
    disagree by surface: g1's seven-turn wiki remark was written as ONE page
    comment, while g2's is seven separate comments under a page it created. A row
    that reports the plant's seven either way sends the agent looking for six
    comments that are not there.

    The window matters for the same reason a start alone is not enough: a
    `chat_insert` remark is threaded INTO a day that already happened, so the
    messages around it are not all part of it.
    """
    want = {c["clue_id"]: inject.must_appear(c)
            for c in inject.clues_of(ledger)
            if c.get("carrier") and inject.must_appear(c)}
    # A chat exchange is written into ONE channel on ONE day -- `write_chat`
    # takes both off the carrier -- so a matching line on any other day is a text
    # collision, not part of the exchange. Counting those inflated g9's row 55 to
    # "23 messages" for an eight-message thread and, because the span is just
    # first-hit to last-hit, printed g11's row 2 as `11:12-11:10`: an end time
    # earlier than its start. Mail and wiki are left alone; a mail thread really
    # can run across days, and `row()` already renders that case.
    day: dict[str, str] = {}
    for c in inject.clues_of(ledger):
        carrier = c.get("carrier") or {}
        if carrier.get("source") == "slack" and carrier.get("date"):
            day[c["clue_id"]] = carrier["date"]
    hits: dict[str, list[str]] = {cid: [] for cid in want}
    anywhere: dict[str, list[str]] = {cid: [] for cid in want}

    def sweep(body: str, when: str) -> None:
        body = inject.flat(body)
        for cid, parts in want.items():
            if not any(part and part in body for part in parts):
                continue
            anywhere[cid].append(when)
            if cid in day and when and not when.startswith(day[cid]):
                continue
            hits[cid].append(when)

    for name in ("messages.jsonl", "comments.jsonl"):
        path = root / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            sweep(row.get("text") or "", row.get("created_at") or "")

    for path in sorted(root.glob("emails/**/*.eml")):
        if "/Sent/" not in str(path):
            continue                       # one copy per message, the sender's
        note = email.message_from_bytes(path.read_bytes())
        raw = note.get_payload(decode=True)
        stamp = ""
        if note.get("Date"):
            stamp = email.utils.parsedate_to_datetime(note["Date"]).isoformat()
        sweep(raw.decode("utf-8", "replace") if raw else "", stamp)

    out = {}
    for cid, found in hits.items():
        # A chat_insert's minutes are shifted onto its anchor, so in principle the
        # shift can push an exchange over midnight and the day filter then matches
        # nothing. Falling back to the unfiltered hits keeps such a row honest
        # rather than emitting a count of zero.
        found = found or anywhere[cid]
        when = sorted(w for w in found if w)
        out[cid] = (len(found), when[0] if when else "", when[-1] if when else "")
    return out


def page_titles(*roots: pathlib.Path) -> dict[str, str]:
    """`docs/<path>.md` -> the page's own title, which is what BookStack shows.

    Later roots fill the gaps earlier ones leave. A plant ingested at run time
    ships only the pages it ADDS, while its comments can hang off pages the world
    already had, so the delta alone titles none of those and every wiki row comes
    out as the anonymous "a wiki page".
    """
    titles: dict[str, str] = {}
    for root in roots:
        if not (root / "docs").is_dir():
            continue
        titles.update(_titles_under(root, titles))
    return titles


def _titles_under(root: pathlib.Path, have: dict[str, str]) -> dict[str, str]:
    titles = {}
    for path in sorted((root / "docs").rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        found = re.search(r'^title:\s*"?(.*?)"?\s*$', text, re.M)
        rel = f"docs/{path.relative_to(root / 'docs')}"
        if rel not in have:
            titles[rel] = found.group(1) if found else path.stem
    return titles


def row(at: dict, land: tuple[int, str, str], titles: dict[str, str]
        ) -> tuple[str, str, str]:
    """One remark as (date, time, where) — location only, never content."""
    when = at.get("when") or ""
    date, clock = when[:10], when[11:16]
    turns, _, ends = land
    turns = turns or at.get("turns", 1)
    plural = "message" if turns == 1 else "messages"
    surface = at.get("surface")
    where = at.get("where", "?")

    if surface == "chat":
        span = clock
        if ends and ends[11:16] != clock:
            span = f"{clock}–{ends[11:16]}"
        return date, span, (f"Mattermost `{where}` — an exchange of {turns} "
                            f"{plural}, opened by **{at['who']}**")
    if surface == "mail":
        subject = where.strip("“”").removeprefix("Re: ").strip()
        span = clock
        if ends:
            span = (f"{clock}–{ends[11:16]}" if ends[:10] == date
                    else f"{clock} → {ends[:10]} {ends[11:16]}")
        return date, span, (f"mail thread “{subject}” — an exchange of {turns} "
                            f"{plural} from **{at['who']}**. In {MAIL_HOME}")
    if surface == "wiki comment":
        title = titles.get(where, "")
        named = f'the wiki page “{title}”' if title else "a wiki page"
        span = clock
        if ends and ends[11:16] != clock:
            span = f"{clock}–{ends[11:16]}"
        body = (f"a **comment** by **{at['who']}**" if turns == 1 else
                f"an exchange of {turns} **comments** opened by **{at['who']}**")
        # A `doc_new` writes the page AND the comments on it; a `doc_comment`
        # hangs comments on a page the world already had. Only the second one is
        # a page whose body the reader can safely skip.
        tail = ("and the page they hang on" if at.get("kind") == "doc_new"
                else "not the page body")
        return date, span, f"{named} (`{where}`) — {body}, {tail}"
    if surface == "wiki page":
        title = titles.get(where, "")
        named = f'the wiki page “{title}”' if title else "a wiki page"
        # "and its comments", always: a `doc_new` writes the body and hangs
        # comments on it, and which half carries which piece is not something this
        # row is allowed to say. BookStack's search reaches the body and not the
        # comments, so a reader who stops at whichever one search found has read
        # half of it.
        return date, clock, (f"{named} (`{where}`) — the **page body**, written "
                             f"by **{at['who']}**, and the comments on it")
    return date, clock, f"{surface} · {where} · {at.get('who', '?')}"


def index_md(spot: dict, land: dict, titles: dict[str, str]) -> str:
    """The section the arm adds to the ticket."""
    rows = sorted(spot.items(), key=lambda kv: (kv[1].get("when") or "", kv[0]))
    out = [
        "## Where the conversations are",
        "",
        f"You do not have to go looking. Every conversation in this company that "
        f"bears on this ticket is listed below — {len(rows)} of them, oldest "
        "first — with exactly where it sits.",
        "",
        "The list says **where**, and nothing else. It does not say what was "
        "said, who was right, which conversations matter most, or how they "
        "relate to each other. That is the part left to you: open them, read "
        "them together with what is around them, and work out what they mean "
        "for this ticket.",
        "",
        "Times are the world's own timestamps (UTC), as chat and mail record "
        "them.",
        "",
        "| # | date | time | where |",
        "|---|---|---|---|",
    ]
    for i, (cid, at) in enumerate(rows, 1):
        date, clock, where = row(at, land.get(cid, (0, "", "")), titles)
        out.append(f"| {i} | {date} | {clock} | {where} |")
    out += [
        "",
        "A row gives the window an exchange runs in and how many messages it "
        "is — not how much is around it. A busy channel interleaves other talk "
        "with it, and a mail thread can have begun earlier and under someone "
        "else's name, so read the window and its surroundings rather than "
        "counting messages off.",
        "",
        "A wiki **comment** is not in the page body and BookStack's search does "
        "not index it; `/api/pages/{id}` returns a page's `comments` alongside "
        "its text.",
        "",
    ]
    return "\n".join(out)


def splice(instruction: str, index: str) -> str:
    """The world arm's ticket with the map in front of `## Done means`.

    In front of it rather than at the end: `## Done means` is the last thing an
    agent reads before it starts, and a fifty-row table between it and the ticket
    would push it out of sight.
    """
    marker = "## Done means"
    if marker not in instruction:
        return instruction.rstrip() + "\n\n" + index
    head, _, tail = instruction.partition(marker)
    return head.rstrip() + "\n\n" + index + "\n" + marker + tail


def patch_toml(text: str, slug: str, *, hosted: bool = False) -> str:
    """Only the name, the description and the variant may move.

    Everything else -- the image, the CPUs, the healthcheck, both timeouts -- has
    to stay byte-identical to the world arm, or the two arms stop being a
    comparison and the extra number means nothing.
    """
    if hosted:
        text = re.sub(r'(?m)^name = "([^"]+)-world-hosted"$',
                      rf'name = "\1{SUFFIX}-hosted"', text)
    else:
        text = re.sub(r'(?m)^name = "([^"]+)-world"$',
                      rf'name = "\1{SUFFIX}"', text)
    # The world arms all end their description on the same clause, so the located
    # arm's is that description with its last sentence swapped rather than a
    # per-task string written out here -- the first version of this hardcoded g1's
    # title and would have shipped it on g2's arm. Refuse rather than guess.
    hunt = "and the agent has to find them."
    told = ("and the ticket says exactly where each one is \u2014 the search is "
            "removed, the inference is not.")
    if hunt not in text:
        raise SystemExit(f"{slug}: the world arm's description does not end on "
                         f"{hunt!r}, so the located arm's cannot be derived from "
                         "it. Reword it here deliberately.")
    text = text.replace(hunt, told, 1)
    text = re.sub(r'(?m)^variant = "world(-hosted)?"$',
                  'variant = "world-located"', text)
    return text


def emit(slug: str, index: str, force: bool, *, hosted: bool = False) -> pathlib.Path:
    """Copy one world arm and rewrite exactly two files in the copy.

    `hosted` picks `-world-hosted` as the source instead of `-world`, so the
    hosted twin is the hosted arm plus the map and nothing else. It is emitted
    here rather than assembled by hand because the two used to be built in
    separate sittings: the twin kept an older plant and an older suite than the
    arm it is supposed to be a copy of, and nothing said so.
    """
    task = load(slug)
    group = REPO / "harbor_tasks" / task.group
    source = group / (f"{task.slug}-world-hosted" if hosted else f"{task.slug}-world")
    target = group / (f"{task.slug}{SUFFIX}-hosted" if hosted else f"{task.slug}{SUFFIX}")
    if not (source / "task.toml").is_file():
        raise SystemExit(f"no world arm at {source}")
    if target.exists() and not force:
        raise SystemExit(f"{target} exists; pass --force to overwrite")

    # Everything Horizon wrote about the arm -- its task id, its rollouts, its
    # validations -- is under dot-directories that the rebuild has no business
    # discarding. A push that cannot read .horizon/metadata.json creates a SECOND
    # task and leaves the rollouts on the first.
    keep = [d for d in (".horizon", ".rollouts", ".validation")
            if (target / d).is_dir()]
    stash = target.parent / f".{target.name}.keep" if keep else None
    if stash is not None:
        if stash.exists():
            shutil.rmtree(stash)
        stash.mkdir()
        for d in keep:
            shutil.move(str(target / d), str(stash / d))
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        ".horizon", ".rollouts", ".validation"))
    if stash is not None:
        for d in keep:
            shutil.move(str(stash / d), str(target / d))
        shutil.rmtree(stash)
    (target / "task.toml").write_text(
        patch_toml((source / "task.toml").read_text(), task.slug, hosted=hosted))
    (target / "instruction.md").write_text(
        splice((source / "instruction.md").read_text(), index))
    return target


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", help="a task_generator slug, e.g. batch-payload-plan")
    ap.add_argument("--corpus", default=None,
                    help="the written corpus to read locations out of: a path, or "
                         "`image:<tag>` for the one baked into a world image "
                         "(/opt/world-state/data). Default data/, which is right "
                         "only while nothing has re-run a phase since the bake.")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print the section and write nothing")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an arm that is already there")
    ap.add_argument("--hosted", action="store_true",
                    help="also emit the -world-located-hosted twin, copied from "
                         "the -world-hosted arm")
    args = ap.parse_args(argv)

    task = load(args.slug)
    root = corpus_root(args.corpus)
    name, ledger, spot = locate(root, task)
    index = index_md(spot, landed(root, ledger),
                     page_titles(root, REPO / "data"))

    if args.show:
        print(f"# plant {name}, read out of {root}\n", file=sys.stderr)
        print(index)
        return 0

    made = [emit(args.slug, index, args.force)]
    if args.hosted:
        made.append(emit(args.slug, index, args.force, hosted=True))
    for target in made:
        print(f"  {target.relative_to(REPO)}  ({len(spot)} remarks, plant {name}, "
              f"read out of {root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
