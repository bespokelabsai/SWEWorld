#!/usr/bin/env python3
"""Put a planted mail corpus into the register mail is actually written in.

The generator writes every planted remark the same way, which is right for a
Mattermost channel and wrong for a mailbox: the agent opens these in Roundcube,
and a mailbox full of chat is a tell that the corpus is generated. Two defects
recur across tasks and both are mechanical:

**A pseudo-subject inside the body.** Thread openers begin `Subject: <topic>` as
the first line of the BODY while the real `Subject:` header says something else
entirely -- often a weekly-recap thread the remark was hung off. Nobody types a
second subject line into a message. The topic is invariably restated in the prose
below it, so the line carries nothing but the artefact.

**Everybody greets, every time.** Real threads greet at the top and then stop:
the opener addresses the room or the person, the first reply answers by name, and
after that people just start talking. A salutation on every message reads as
generated even when every word under it is good.

What this does NOT do is rewrite prose. A body that still reads as chat -- all
lowercase, no sign-off -- needs a person, and is reported rather than touched:

    python3 harbor_tasks/mail_register.py <emails-dir>            # dry run
    python3 harbor_tasks/mail_register.py <emails-dir> --apply

Threads are grouped by subject with every `Re:`/`Fwd:` prefix stripped, because
the corpus contains both `foo` and ` Re: foo` for one conversation and treating
them as two threads restarts the greeting count in the middle of it.

Every copy of a message is rewritten, matched by Message-ID: a mail exists once
in the sender's Sent and once per recipient INBOX.
"""
from __future__ import annotations

import argparse
import collections
import email
import pathlib
import re
import sys
from email.policy import compat32, default

SALUTATION = re.compile(r"\A[A-Z][a-z]+(?:,? [A-Z][a-z]+)*,\n\s*\n")
PSEUDO_SUBJECT = re.compile(r"\ASubject:[^\n]*\n\s*\n")
# How many messages into a thread a salutation still reads as natural.
GREET_THROUGH = 2


def thread_of(msg) -> str:
    return re.sub(r"\A(\s*(?:Re|Fwd):\s*)+", "", msg["Subject"] or "", flags=re.I).strip()


def encode(body: str) -> tuple[str, bytes]:
    import quopri
    if body.isascii() and all(len(l) <= 78 for l in body.splitlines()):
        return "7bit", body.encode() + b"\n"
    return "quoted-printable", quopri.encodestring(body.encode() + b"\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=pathlib.Path, help="an emails/ tree")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # Order within a thread comes from the filename's numeric prefix, which is
    # the order the plant wrote them and therefore the order they were sent.
    sent = []
    for f in sorted(args.root.glob("*/Sent/*.eml")):
        m = re.match(r"(\d+)-", f.name)
        if m:
            sent.append((int(m.group(1)), f))
    sent.sort()

    plan: dict[str, str] = {}          # Message-ID -> new body
    chatty: list[str] = []
    seen = collections.Counter()
    for n, f in sent:
        msg = email.message_from_bytes(f.read_bytes(), policy=default)
        thread = thread_of(msg)
        seen[thread] += 1
        body = msg.get_content().rstrip()
        new = PSEUDO_SUBJECT.sub("", body)
        if seen[thread] > GREET_THROUGH:
            new = SALUTATION.sub("", new)
        if re.match(r"\A[a-z]", new):
            chatty.append(f"{n} {msg['From'].split('@')[0]:9} {thread[:44]}")
        if new != body:
            plan[msg["Message-ID"]] = new

    touched = 0
    for f in sorted(args.root.glob("*/*/*.eml")):
        raw = f.read_bytes()
        head, sep, _ = raw.partition(b"\r\n\r\n") if b"\r\n\r\n" in raw else raw.partition(b"\n\n")
        mid = email.message_from_bytes(raw, policy=compat32)["Message-ID"]
        if mid not in plan:
            continue
        cte, enc = encode(plan[mid])
        head = re.sub(rb"(?im)^Content-Transfer-Encoding:.*$",
                      b"Content-Transfer-Encoding: " + cte.encode(), head)
        if args.apply:
            f.write_bytes(head + sep + enc)
        touched += 1

    print(f"{len(plan)} message(s), {touched} file(s) "
          f"{'rewritten' if args.apply else 'to rewrite'}")
    if chatty:
        print(f"\n{len(chatty)} body(ies) still read as chat — these need a person, "
              "not this script:")
        for c in chatty:
            print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
