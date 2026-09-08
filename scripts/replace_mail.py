#!/usr/bin/env python3
"""Replace the body of already-delivered messages, in place, inside a world.

`ingest_mail.py` only APPENDs, which is right for building a world and useless for
correcting one. Rewriting a planted remark after the image is baked is not a
rebuild: the corpus is the independent variable in the harbor tasks, so re-baking
`data/` into a new world would move the chat, the wiki, and every Mattermost and
BookStack id along with it, and quietly change what those tasks measure. This
edits the messages you name and leaves the other ~840 copies untouched.

Why not do it over IMAP
-----------------------
The obvious route -- APPEND the new message, STORE \\Deleted the old, EXPUNGE --
works, and it is wrong here. IMAP has no in-place body edit, so the replacement
lands at the END of the mailbox with a fresh UID. Doing that to g1's four mail
threads put its 26 planted messages at the highest UIDs in all eight mailboxes
that hold them, which is to say a `FETCH 1:*` listed the four hardest-to-find
remarks in the task last, together, in a block. In a task that measures whether
an agent can FIND these, that is not a cosmetic difference.

So this writes the store directly. maddy's `storage.imapsql` keeps one flat file
per message copy under `<state_dir>/messages/<key>` -- the whole RFC 5322 message,
CRLF, uncompressed, no dedupe -- and three columns in `msgs` that describe it:

    bodyLen              the file's exact byte length
    bodyStructure.Size   bytes after the header separator
    bodyStructure.Lines  LF count in that body
    bodyStructure.Encoding   the Content-Transfer-Encoding

`cachedHeader` caches To/From/Subject/Date/Message-Id/Content-Type and so needs no
touching: a body rewrite changes no header but Content-Transfer-Encoding, which is
not among them. UID, sequence number, INTERNALDATE and flags all live in rows this
never writes.

Maddy must be STOPPED -- it holds the SQLite file open and caches rows, so an edit
underneath a live server is read back inconsistently or lost on shutdown. Roundcube
has no message cache configured, so there is nothing else to invalidate.

    supervisorctl -c /etc/supervisor/supervisord.conf stop world:maddy
    python3 scripts/replace_mail.py data/emails/*/Sent/90*.eml            # dry run
    python3 scripts/replace_mail.py data/emails/*/Sent/90*.eml --apply
    supervisorctl -c /etc/supervisor/supervisord.conf start world:maddy

Paths are named explicitly, one or more files or directories, and there is
deliberately no "just point it at data/emails" mode: handed the whole tree this
would rewrite all ~840 copies, which is the wholesale rebuild it exists to avoid.
One copy of each message is enough -- messages are matched by **Message-ID**, so
the Sent copies alone reach every INBOX that holds one, including mailboxes
`data/emails/` does not describe at all (`worldadmin@world.local` holds a copy of
everything and has no directory there).
"""
from __future__ import annotations

import argparse
import email
import json
import pathlib
import sqlite3
import subprocess
import sys
from email.policy import compat32

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import worldlib as wl  # noqa: E402

STATE = pathlib.Path("/var/lib/world/maddy")
DB = STATE / "imapsql.db"
BLOBS = STATE / "messages"


def wanted(paths: list[pathlib.Path]) -> dict[str, bytes]:
    """Message-ID -> the replacement message, CRLF, as maddy stores it.

    Every copy of a message is identical apart from the mailbox it sits in, so
    naming two copies of one message is harmless: they are the same bytes.
    """
    out: dict[str, bytes] = {}
    files: list[pathlib.Path] = []
    for path in paths:
        files += sorted(path.glob("**/*.eml")) if path.is_dir() else [path]
    for path in files:
        raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        mid = email.message_from_bytes(raw, policy=compat32)["Message-ID"]
        if not mid:
            wl.fail(f"{path}: no Message-ID")
        out[mid.strip()] = raw
    return out


def encoding_of(raw: bytes) -> str:
    cte = email.message_from_bytes(raw, policy=compat32)["Content-Transfer-Encoding"]
    return (cte or "7bit").strip().lower()


def maddy_running() -> bool:
    proc = subprocess.run(
        ["supervisorctl", "-c", "/etc/supervisor/supervisord.conf", "status", "world:maddy"],
        capture_output=True, text=True)
    return "RUNNING" in (proc.stdout or "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", type=pathlib.Path, nargs="+",
                    help=".eml files (or directories of them) to replace")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.apply and maddy_running():
        wl.fail("maddy is running -- stop world:maddy first, or the edit is lost")
    if not DB.exists():
        wl.fail(f"{DB} not found -- this runs INSIDE the world container")

    repl = wanted(args.paths)
    wl.info(f"{len(repl)} replacement messages")

    db = sqlite3.connect(DB)
    rows = db.execute("SELECT mboxId, msgId, extBodyKey, bodyStructure, cachedHeader "
                      "FROM msgs WHERE extBodyKey IS NOT NULL").fetchall()
    hits = 0
    seen: set[str] = set()
    for mbox, msg, key, structure, header in rows:
        head = {k.lower(): v for k, v in json.loads(header).items()}
        mid = (head.get("message-id") or [""])[0].strip()
        raw = repl.get(mid)
        if raw is None:
            continue
        hits += 1
        seen.add(mid)
        if not args.apply:
            continue
        _, _, body = raw.partition(b"\r\n\r\n")
        bs = json.loads(structure)
        bs["Size"] = len(body)
        bs["Lines"] = body.count(b"\n")
        bs["Encoding"] = encoding_of(raw)
        (BLOBS / key).write_bytes(raw)
        db.execute("UPDATE msgs SET bodyLen = ?, bodyStructure = ? "
                   "WHERE mboxId = ? AND msgId = ?",
                   (len(raw), json.dumps(bs), mbox, msg))
    if args.apply:
        db.commit()
    db.close()

    # A named message the store does not have is the failure that hides: the run
    # reports a healthy count, and one remark stays as it was in a world nobody
    # re-reads. Name it rather than let the total cover for it.
    missing = sorted(set(repl) - seen)
    if missing:
        wl.fail(f"not found in the store: {', '.join(missing)}")
    wl.ok(f"{hits} copies {'replaced' if args.apply else 'to replace'} "
          f"across {len(rows)} stored messages")
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
