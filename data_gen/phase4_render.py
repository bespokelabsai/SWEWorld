#!/usr/bin/env python3
"""The transcript, as `ingest_chat.py` will read it back.

The engine and the ingest describe the same conversation in three
incompatible ways, and each disagreement corrupts quietly rather than loudly:

**Time.** The engine writes `datetime.isoformat()` with no zone. Every
timestamp the ingest reads must carry an explicit UTC offset — a naive one is a
hard error, and the error names the field rather than the cause.

**Reactions.** The engine emits `{emoji, count}`, having thrown the reactors
away. The ingest wants `{author, emoji}` and validates the author against the
roster. A count cannot be turned back into people, so the people are assigned:
deterministically, from the channel's own members, never the poster.

**Threads.** The engine points a reply at its parent's *timestamp*. The ingest
wants a minted id on the root and `thread_id` on the reply — and a reply must
carry no id of its own, because Mattermost has no sub-threads. So ids are
minted here, and only roots get one.

Everything else is a rename: `userId` is `author`, and the rest passes through.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

UTC = dt.timezone.utc
EMOJI_NAME_OK = re.compile(r"^[a-zA-Z0-9_+-]+$")


# Mattermost stores a reaction as an `emoji_name`, matching
# `^[a-zA-Z0-9_+-]+$` — never the glyph. The engine's personas react with the
# character itself, and `ingest_chat.py` only rejects colons, so a glyph passes
# every offline check and then fails the Mattermost IMPORT JOB, which is the
# last and most expensive step of a bake.
#
# These twenty carry 1,286 of 1,353 reactions in the current corpus. The tail
# is thirty-one glyphs used three times or fewer; an unmapped one is dropped
# and counted rather than guessed at, because a wrong name fails the import
# exactly as a glyph does.
EMOJI_NAMES = {
    "\U0001F44D": "thumbsup",          "\u2705": "white_check_mark",
    "\U0001F389": "tada",              "\U0001F605": "sweat_smile",
    "\U0001F4A1": "bulb",              "\U0001F680": "rocket",
    "\U0001F4DD": "memo",              "\U0001F440": "eyes",
    "\U0001F4CB": "clipboard",         "\U0001F604": "smile",
    "\U0001F3AF": "dart",              "\U0001F50D": "mag",
    "\U0001F914": "thinking_face",     "\U0001F62C": "grimacing",
    "\U0001F44F": "clap",              "\U0001F4AA": "muscle",
    "\U0001F64C": "raised_hands",      "\u26A0\uFE0F": "warning",
    "\U0001F64F": "pray",              "\U0001F4AF": "100",
    # cheap tail, all unambiguous
    "\U0001F602": "joy",               "\U0001F41B": "bug",
    "\U0001F4DA": "books",             "\U0001F44B": "wave",
    "\U0001F6A8": "rotating_light",    "\U0001F527": "wrench",
    "\u2615": "coffee",                "\U0001F91D": "handshake",
    "\u2728": "sparkles",              "\U0001F44E": "thumbsdown",
    "\U0001F525": "fire",              "\U0001F517": "link",
    "\U0001F4CC": "pushpin",           "\u2699\uFE0F": "gear",
    "\u26A1": "zap",                   "\u2764\uFE0F": "heart",
    "\U0001F44C": "ok_hand",           "\U0001F4E2": "loudspeaker",
    "\u2753": "question",              "\U0001F6A2": "ship",
    "\U0001F514": "bell",              "\U0001F4AD": "thought_balloon",
    "\u23F3": "hourglass_flowing_sand", "\u23F1\uFE0F": "stopwatch",
    "\u2139\uFE0F": "information_source", "\U0001F198": "sos",
    "\U0001F629": "weary",             "\U0001F624": "triumph",
    "\u270B": "hand",                  "\u2713": "heavy_check_mark",
    "\U0001F499": "blue_heart",
}

# Filled in by `render`, reported by its caller: a dropped reaction is a fact
# about the corpus, not an implementation detail to swallow.
DROPPED_EMOJI: "collections.Counter" = __import__("collections").Counter()


def emoji_name(raw: str) -> str:
    """A Mattermost emoji name, or "" if we have none for this glyph."""
    got = (raw or "").strip().strip(":")
    if not got:
        return ""
    if EMOJI_NAME_OK.match(got):
        return got                      # already a name, e.g. "+1"
    name = EMOJI_NAMES.get(got) or EMOJI_NAMES.get(got.rstrip("\uFE0F"))
    if not name:
        DROPPED_EMOJI[got] += 1
    return name or ""


def stamped(ts: str, where: str = "") -> str:
    """An engine timestamp with the offset the ingest requires.

    A `ts` the engine has scribbled on — one live corpus carried
    `2024-12-20T11:5ok so 0:01.666667`, a persona's words spliced into the
    field — used to come out of `fromisoformat` as a bare ValueError naming
    neither the channel nor the message. The render is the last step of a
    run, so the exception was swallowed by the batch loop and `messages.jsonl`
    simply stopped being rewritten: fifteen batches reported success while the
    ingest file sat frozen three months behind the transcript. Say which
    message, so the next one is a one-line fix rather than a bisect.
    """
    try:
        when = dt.datetime.fromisoformat(ts)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"unusable timestamp {ts!r}{where} — the transcript is corrupt "
            "at this message; fix the ts and re-render") from exc
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return when.isoformat(timespec="seconds")


def reactors(members: list[str], author: str, emoji: str, count: int,
             taken: set[tuple[str, str]]) -> list[str]:
    """Who reacted, given only how many did.

    The engine counts reactions and discards the reactors, so this invents
    them. Deterministic — same transcript, same people — and it never picks the
    poster or double-counts one person on one message, because both would fail
    validation for reasons that have nothing to do with the conversation.
    """
    pool = [m for m in members if m != author]
    out = []
    for i in range(max(0, count)):
        for step in range(len(pool)):
            who = pool[(i + step) % len(pool)] if pool else author
            if (who, emoji) not in taken:
                taken.add((who, emoji))
                out.append(who)
                break
    return out


def render(workspace: dict, *, channels_wanted: set[str] | None = None) -> list[dict]:
    """One workspace transcript becomes `messages.jsonl` rows."""
    rows: list[dict] = []
    for channel in workspace.get("channels") or []:
        name = channel.get("name") or channel.get("id") or ""
        if channels_wanted and name not in channels_wanted:
            continue
        members = list(channel.get("memberIds") or [])
        messages = sorted(channel.get("messages") or [],
                          key=lambda m: m.get("ts") or "")

        # An id per message, minted from its POSITION. Keying on the timestamp
        # looked equivalent and was not: two conversations can run in one
        # channel on one day, both opening at 09:00, and a ts-keyed id gave
        # them the same handle — which the ingest rejects as a duplicate.
        #
        # Roots are indexed separately so a reply can always name an id that
        # exists; where two roots share a timestamp the first one wins, which
        # is the one a reply arriving later would have been answering.
        ident = [f"m-{name}-{m['ts'][:10]}-{i:03d}" for i, m in enumerate(messages)]
        roots: dict[str, str] = {}
        for i, message in enumerate(messages):
            if not message.get("threadParentTs"):
                roots.setdefault(message["ts"], ident[i])

        for index, message in enumerate(messages):
            text = (message.get("text") or "").strip()
            reactions = message.get("reactions") or []
            if not text and not reactions:
                continue                       # nothing to import, and it errors
            author = message.get("userId") or ""
            parent = message.get("threadParentTs")
            row: dict = {"channel": name, "author": author,
                         "created_at": stamped(
                             message.get("ts"),
                             f" in #{name} message {index} by "
                             f"{author or '?'}: {text[:60]!r}"), "text": text}
            if parent:
                root = roots.get(parent)
                if root is None:
                    continue
                row["thread_id"] = root       # and deliberately no id
            else:
                row["id"] = ident[index]

            if reactions:
                taken: set[tuple[str, str]] = set()
                got = []
                for reaction in reactions:
                    emoji = emoji_name(reaction.get("emoji") or "")
                    if not emoji:
                        continue
                    for who in reactors(members, author, emoji,
                                        int(reaction.get("count") or 1), taken):
                        got.append({"author": who, "emoji": emoji})
                if got:
                    row["reactions"] = got
            rows.append(row)
    return rows


def write(rows: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Schema: data/schemas/messages.md\n")
        for row in sorted(rows, key=lambda r: (r["created_at"], r["channel"])):
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path.stat().st_size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", type=Path,
                        help="a workspace .json written by the simulation")
    parser.add_argument("--out", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "phase4" / "messages.jsonl")
    args = parser.parse_args(argv)

    workspace = json.loads(args.transcript.read_text(encoding="utf-8"))
    rows = render(workspace)
    size = write(rows, args.out)

    per = Counter(r["channel"] for r in rows)
    threaded = sum(1 for r in rows if r.get("thread_id"))
    rl.ok(f"{args.out} ({rl.human_bytes(size)}) — {len(rows)} message(s) across "
          f"{len(per)} channel(s), {threaded} in threads")
    rl.info("  " + ", ".join(f"#{c} {n}" for c, n in per.most_common(8)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
