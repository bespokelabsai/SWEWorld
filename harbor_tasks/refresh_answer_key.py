#!/usr/bin/env python3
"""Apply the mechanical half of the answer-key rework to a task group.

`solution/hidden_requirements.md` is what a human opens to see what a task is
really testing. Three things about the generated shape were wrong, and three of
them are mechanical enough to script. The fourth -- restructuring the requirement
bodies into tables and fenced literals -- is per-task judgement and stays by hand.

What this does:

**Drops `## The ticket — stated openly`.** It is a verbatim copy of what the agent
already receives in `instruction.md`, sitting in the middle of the document whose
whole point is the part the agent does NOT get. g6's runs to 71 lines and eight
numbered subsections; g2's is one paragraph. Same rule: heading to the `---`
before the next `##`, leaving one separator behind.

**Adds the `located` row** to the arm table, if it is not already there. The row
is written to the table's own width: g1's key was hand-edited to carry a
`measured` column and its scores, while the generated keys have two columns and
the sentence *"Scores are per run and live with the run, not here"* underneath.
Adding a score column to those would contradict the line below them.

**Re-renders mail clues as mail.** The generator emits `HH:MM  who  <one flattened
line>` for every clue, which is right for a Mattermost channel and wrong for a
mailbox: it throws away the paragraphs, the greeting and the sign-off, so the key
shows a thread that looks nothing like what the agent opens in Roundcube. Bodies
are read back out of the CORPUS, which is what the document's own header promises
("Quotes are exact -- they are read back out of the corpus, not out of the plan")
and what `answer_key()` does not actually do; it renders the plant.

**Unfolds the `- to` lines.** They arrive as raw RFC 5322 header continuations and
render as stray lines in the middle of a bullet list.

**Mirrors the result** to every copy of the file. g2, g4 and g6 keep byte-identical
answer keys in three to five arm directories, and an edit that lands in only the
hosted one leaves the others quietly wrong. Copies that were NOT identical to
begin with are refused rather than overwritten.

    python3 harbor_tasks/refresh_answer_key.py g1-batch-payload-plan \\
        --corpus data/emails
    python3 harbor_tasks/refresh_answer_key.py g2-executor-output-cap \\
        --corpus harbor_tasks/g2-executor-output-cap/executor-output-cap-world-hosted/environment/plant/emails \\
        --apply

Idempotent: re-running finds the ticket already gone, the row already present, and
re-renders the mail blocks to the same bytes.
"""
from __future__ import annotations

import argparse
import email
import pathlib
import re
import sys
from email.policy import default

RULE = "-" * 62

LOCATED_2COL = ("| `located` | the `world` arm plus a map naming each remark's "
                "channel, day, minute and length (or its page, or its mail "
                "subject) — the search removed, the inference left |")
LOCATED_3COL = LOCATED_2COL + " **1.00** |"


# ---------------------------------------------------------------------------
# the corpus side
# ---------------------------------------------------------------------------
def corpus(root: pathlib.Path) -> dict[tuple[str, str], tuple[str, str]]:
    """(HH:MM, local-part) -> (From, body), from the sender's copy of each mail.

    One copy per message, not one per recipient: a mail exists once in the
    sender's Sent and once in every recipient's INBOX, and they are the same
    bytes, so reading Sent alone is both complete and unambiguous.
    """
    out: dict[tuple[str, str], tuple[str, str]] = {}
    for path in sorted(root.glob("*/Sent/*.eml")):
        msg = email.message_from_bytes(path.read_bytes(), policy=default)
        when = email.utils.parsedate_to_datetime(msg["Date"])
        frm = email.utils.parseaddr(msg["From"])[1]
        out[(when.strftime("%H:%M"), frm.split("@")[0])] = (frm, msg.get_content().rstrip())
    return out


# ---------------------------------------------------------------------------
# the four edits
# ---------------------------------------------------------------------------
def drop_ticket(text: str) -> tuple[str, bool]:
    """Remove the ticket section, heading through the separator before the next `##`."""
    pat = re.compile(r"\n## The ticket — stated openly\n.*?\n---\n(?=\n## )", re.S)
    new, n = pat.subn("\n", text)
    return new, bool(n)


def add_located(text: str) -> tuple[str, bool]:
    """Append the `located` row to the arm table, matching its column count.

    The arm answers to two names. The generated group README calls it
    `world-located`, after the directory; the answer keys call it `located`,
    after the column of scores it sits in. Matching only one of them adds a
    second row for an arm that is already listed.
    """
    # The sentence above the table enumerates what each arm is WITHHELD, which is
    # the part a reader actually needs; a row added without it leaves the one arm
    # whose withholding is subtlest — locations but never quotes — described only
    # by a table cell.
    text = text.replace(
        "or which fact anything carries.",
        "or which fact anything carries; `located` gets the same world as `world` "
        "plus a map of where each remark sits, but never a quote, never which "
        "requirement a conversation serves, and never which are herrings.", 1)
    if re.search(r"(?m)^\| `(world-)?located` \|", text):
        return text, False
    m = re.search(r"(?m)^\| `world` \|.*$", text)
    if not m:
        return text, False
    row = LOCATED_3COL if m.group(0).count("|") >= 4 else LOCATED_2COL
    return text[:m.end()] + "\n" + row + text[m.end():], True


def turns_of(block: str) -> list[tuple[str, str]]:
    """(HH:MM, who) per turn, from a block in either shape.

    Accepts the generator's `HH:MM  who  text` and this tool's own `From:`/`Sent:`
    output, so a re-run is a no-op rather than a refusal.
    """
    pairs = re.findall(r"(?m)^From: (\S+?)@\S*\nSent: (\d\d:\d\d)$", block)
    if pairs:
        return [(hhmm, who) for who, hhmm in pairs]
    return re.findall(r"(?m)^(\d\d:\d\d)\s+(\S+)\s", block)


def render_mail(text: str, msgs: dict, warn: list[str]) -> tuple[str, int]:
    """Rewrite every mail clue's exchange block as mail."""
    pat = re.compile(
        r"(- \*\*mail\*\* ·.*?As it appears, spread across the )(?:exchange|thread)"
        r"(:\n\n)```\n(.*?)```", re.S)
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        out = []
        for hhmm, who in turns_of(m.group(3)):
            hit = msgs.get((hhmm, who))
            if hit is None:
                warn.append(f"no corpus message for {who} at {hhmm}")
                return m.group(0)          # leave the block exactly as it was
            frm, body = hit
            out.append(f"From: {frm}\nSent: {hhmm}\n\n{body}")
        if not out:
            warn.append("could not read the turns out of a mail block")
            return m.group(0)
        n += 1
        return (m.group(1) + "thread" + m.group(2) + "```\n"
                + f"\n\n{RULE}\n\n".join(out) + "\n```")

    return pat.sub(sub, text), n


def unfold_to(text: str) -> tuple[str, int]:
    """Flatten `- to` lines folded straight out of the RFC 5322 header."""
    text, a = re.subn(r"(?m)^- to[ \t]*\n[ \t]+", "- to ", text)
    text, b = re.subn(r"(?m)^(- to .*,)\n[ \t]+", r"\1 ", text)
    return text, a + b


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("group", help="a task group directory under harbor_tasks/")
    ap.add_argument("--corpus", type=pathlib.Path, required=True,
                    help="the emails/ tree the mail bodies are read from")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent
    group = root / args.group if not pathlib.Path(args.group).is_dir() else pathlib.Path(args.group)
    msgs = corpus(args.corpus)

    # Two target sets, refreshed independently. The arms' answer keys are copies
    # of each other and are checked for that; the group README is the same
    # document class -- `cli.py answers` writes it, it carries the same arm
    # table, ticket and mail blocks -- but it is a different and usually older
    # rendering, so lumping it in with the keys would fail the identical check
    # and hide the real problem.
    targets = [sorted(group.glob("*/solution/hidden_requirements.md"))]
    if (group / "README.md").is_file():
        targets.append([group / "README.md"])
    if not targets[0]:
        print(f"no answer key under {group}", file=sys.stderr)
        return 1

    rc = 0
    for files in targets:
        # Every copy must start identical, or "mirror the result" silently
        # discards whichever one somebody had already edited.
        bodies = {f: f.read_text(encoding="utf-8") for f in files}
        if len(set(bodies.values())) > 1:
            print(f"the {len(files)} copies under {group} are not identical; "
                  "reconcile them before refreshing:", file=sys.stderr)
            for f in files:
                print(f"  {len(bodies[f].splitlines()):5} lines  {f}", file=sys.stderr)
            return 1

        text = bodies[files[0]]
        warn: list[str] = []
        text, dropped = drop_ticket(text)
        text, added = add_located(text)
        text, mails = render_mail(text, msgs, warn)
        text, folds = unfold_to(text)

        extra = len(files) - 1
        also = f"  (+{extra} identical cop{'y' if extra == 1 else 'ies'})" if extra else ""
        print(f"{files[0].relative_to(group)}{also}")
        print(f"  ticket section {'dropped' if dropped else 'already gone'}")
        print(f"  located row {'added' if added else 'already present'}")
        print(f"  {mails} mail block(s) rendered as mail, from {args.corpus} "
              f"({len(msgs)} messages)")
        print(f"  {folds} folded `to` line(s) unwrapped")
        for w in warn:
            print(f"  ! {w}")
        if warn:
            rc = 1
            continue
        if not args.apply:
            print("  (dry run — unchanged)")
            continue
        for f in files:
            f.write_text(text, encoding="utf-8")
            print(f"  wrote {f}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
