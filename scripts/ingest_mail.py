#!/usr/bin/env python3
"""Append .eml messages into Maddy mailboxes over IMAP.

Input
-----
data/identities.yaml        the persona list
data/emails/index.jsonl     one line per message file
data/emails/**/*.eml        RFC 5322 messages

index.jsonl:

    {"path":   "alice@world.local/INBOX/001-postmortem.eml",  # required
     "mailbox":"alice@world.local",                           # required
     "folder": "INBOX",                                       # default INBOX
     "date":   "2026-02-11T09:14:02Z",                        # required
     "flags":  ["\\\\Seen"]}                                  # optional

Layout puts one file per copy of a message. A mail that Alice sent to Bob is
two files — one in alice/Sent, one in bob/INBOX — because that is how mail
servers actually store it and it lets each copy carry its own flags.

Why `date` exists separately from the Date: header
--------------------------------------------------
They are different things. Date: is what the sender claims; IMAP's INTERNALDATE
is when the server received it, and it is what clients sort by and what
SINCE/BEFORE search on. Without an explicit INTERNALDATE the server stamps
`now`, so a mailbox of carefully dated historical mail all appears to have
arrived during ingestion.

--dry-run parses and validates every message and opens no socket.
"""
from __future__ import annotations

import email
import email.utils
import imaplib
import json
import ssl
import subprocess
import sys
from email.message import Message
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worldlib as wl  # noqa: E402

INDEX_REQUIRED = ("path", "mailbox", "date")
INDEX_OPTIONAL = ("folder", "flags")
REQUIRED_HEADERS = ("From", "To", "Subject", "Date", "Message-ID")
KNOWN_FLAGS = {"\\Seen", "\\Answered", "\\Flagged", "\\Draft", "\\Deleted", "\\Recent"}
MADDY_CONTAINER_SERVICE = "maddy"


# =============================================================================
# Parsing
# =============================================================================
def load_index(path: Path, emails_dir: Path, identities: wl.Identities,
               problems: wl.Problems) -> list[dict]:
    """Parse and validate index.jsonl, cross-checking against the .eml files."""
    entries: list[dict] = []
    seen_message_ids: dict[tuple[str, str, str], int] = {}
    indexed_paths: set[str] = set()

    mailboxes = {p.mailbox for p in identities}
    from_addresses = {p.email for p in identities} | {p.mailbox for p in identities}

    for lineno, obj in wl.read_jsonl(path, problems):
        wl.check_keys(obj, required=INDEX_REQUIRED, optional=INDEX_OPTIONAL,
                      problems=problems, path=path, line=lineno)

        rel = obj.get("path")
        if not isinstance(rel, str):
            continue
        indexed_paths.add(rel)
        eml_path = emails_dir / rel
        if not eml_path.exists():
            problems.error(f"message file {rel!r} does not exist", path, lineno)
            continue

        mailbox = obj.get("mailbox")
        if mailbox not in mailboxes:
            known = ", ".join(sorted(mailboxes)[:5]) or "(none)"
            problems.error(
                f"mailbox {mailbox!r} does not belong to any persona — known: {known}",
                path, lineno,
            )

        folder = obj.get("folder") or "INBOX"
        internal = wl.parse_ts(obj.get("date"), path=path, line=lineno,
                               problems=problems, field_name="date")

        flags = obj.get("flags") or []
        if not isinstance(flags, list):
            problems.error("flags must be a list", path, lineno)
            flags = []
        for flag in flags:
            if flag not in KNOWN_FLAGS:
                problems.error(
                    f"unknown IMAP flag {flag!r} — known: {sorted(KNOWN_FLAGS)}",
                    path, lineno,
                )

        try:
            message = email.message_from_bytes(eml_path.read_bytes())
        except Exception as exc:  # noqa: BLE001
            problems.error(f"could not parse as RFC 5322: {exc}", eml_path)
            continue

        for header in REQUIRED_HEADERS:
            if message.get(header) is None:
                problems.error(f"missing required header {header}:", eml_path)

        sender = message.get("From", "")
        _, sender_addr = email.utils.parseaddr(sender)
        if sender_addr and sender_addr not in from_addresses:
            problems.error(
                f"From: address {sender_addr!r} does not match any persona", eml_path
            )

        message_id = (message.get("Message-ID") or "").strip()
        key = (str(mailbox), str(folder), message_id)
        if message_id:
            if key in seen_message_ids:
                problems.error(
                    f"Message-ID {message_id} already appears in {mailbox}/{folder} "
                    f"(line {seen_message_ids[key]})", path, lineno,
                )
            else:
                seen_message_ids[key] = lineno

        # The Date: header and INTERNALDATE should normally agree. A gap is
        # legitimate when modelling delivery lag, so this is a warning.
        header_date = message.get("Date")
        if header_date and internal:
            try:
                parsed_header = email.utils.parsedate_to_datetime(header_date)
                if parsed_header.tzinfo is None:
                    parsed_header = parsed_header.replace(tzinfo=internal.tzinfo)
                if abs((parsed_header - internal).total_seconds()) > 86400:
                    problems.warn(
                        f"Date: header ({header_date}) and index date "
                        f"({obj.get('date')}) differ by more than 24h", path, lineno,
                    )
            except (TypeError, ValueError):
                problems.error(f"Date: header {header_date!r} is not a valid RFC 5322 date",
                               eml_path)

        entries.append({
            "lineno": lineno, "path": eml_path, "rel": rel, "mailbox": mailbox,
            "folder": folder, "date": internal, "flags": flags,
            "message": message, "message_id": message_id,
        })

    # A message file with no index entry would be silently skipped.
    for eml in sorted(emails_dir.rglob("*.eml")):
        rel = eml.relative_to(emails_dir).as_posix()
        if rel not in indexed_paths:
            problems.error(
                f"{rel} has no entry in index.jsonl and would be skipped", path
            )

    _check_threading(entries, problems)
    return entries


def _check_threading(entries: list[dict], problems: wl.Problems) -> None:
    """Warn about In-Reply-To / References that point outside the dataset."""
    known = {e["message_id"] for e in entries if e["message_id"]}
    for entry in entries:
        message: Message = entry["message"]
        for header in ("In-Reply-To", "References"):
            value = message.get(header)
            if not value:
                continue
            for ref in value.split():
                ref = ref.strip()
                if ref and ref not in known:
                    problems.warn(
                        f"{header}: {ref} does not resolve to a message in this "
                        "dataset (fine if the thread starts before the window)",
                        entry["path"],
                    )


# =============================================================================
# Maddy accounts
# =============================================================================
def compose_exec(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "exec", "-T", MADDY_CONTAINER_SERVICE, *args],
        capture_output=True, text=True,
    )


def existing_accounts() -> set[str]:
    proc = compose_exec("maddy", "imap-acct", "list")
    if proc.returncode != 0:
        return set()
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def ensure_mailbox(address: str, password: str) -> bool:
    """Create Maddy credentials and the IMAP account. Returns True if created.

    Both commands are required — credentials and the mailbox are separate
    objects in Maddy, and creating only the first yields an account that
    authenticates but has nowhere to deliver.
    """
    created = False
    creds = compose_exec("maddy", "creds", "list")
    if address not in (creds.stdout or ""):
        made = compose_exec("maddy", "creds", "create", "--password", password, address)
        if made.returncode != 0:
            raise RuntimeError(f"maddy creds create failed for {address}: {made.stderr.strip()}")
        created = True
    acct = compose_exec("maddy", "imap-acct", "list")
    if address not in (acct.stdout or ""):
        made = compose_exec("maddy", "imap-acct", "create", address)
        if made.returncode != 0:
            raise RuntimeError(f"maddy imap-acct create failed for {address}: {made.stderr.strip()}")
        created = True
    return created


# =============================================================================
# IMAP
# =============================================================================
def connect(world: wl.World, address: str, password: str, use_ssl: bool):
    """Open an authenticated IMAP connection for one persona.

    Maddy has no cross-account APPEND, so each persona's mail is appended while
    logged in as them.
    """
    if use_ssl:
        context = ssl.create_default_context(
            cafile=str(wl.CA_CERT) if wl.CA_CERT.exists() else None
        )
        conn = imaplib.IMAP4_SSL("127.0.0.1", world.imaps_port, ssl_context=context)
    else:
        conn = imaplib.IMAP4("127.0.0.1", world.imap_port)
    conn.login(address, password)
    return conn


def ensure_folder(conn, folder: str) -> None:
    typ, _ = conn.select(f'"{folder}"')
    if typ != "OK":
        conn.create(f'"{folder}"')
        conn.select(f'"{folder}"')


def append_message(conn, folder: str, entry: dict) -> None:
    """APPEND one message with its flags and INTERNALDATE."""
    raw = entry["path"].read_bytes()
    # RFC 5322 requires CRLF; some clients render lone-LF messages as one line.
    if b"\r\n" not in raw:
        raw = raw.replace(b"\n", b"\r\n")
    flags = f"({' '.join(entry['flags'])})" if entry["flags"] else None
    internal = imaplib.Time2Internaldate(entry["date"].timestamp())
    typ, data = conn.append(f'"{folder}"', flags, internal, raw)
    if typ != "OK":
        raise RuntimeError(f"APPEND failed for {entry['rel']}: {data}")


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--use-ssl", action="store_true",
                        help=f"connect on the IMAPS port instead of plaintext IMAP")
    parser.add_argument("--mailbox", help="only process this mailbox address")
    parser.add_argument("--no-create-accounts", action="store_true",
                        help="fail instead of creating missing Maddy mailboxes")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)
    emails_dir = args.data_dir / "emails"
    if not emails_dir.is_dir():
        raise SystemExit(f"{emails_dir} does not exist")

    wl.heading("Parsing")
    entries = load_index(emails_dir / "index.jsonl", emails_dir, identities, problems)
    if args.mailbox:
        entries = [e for e in entries if e["mailbox"] == args.mailbox]
    problems.raise_if_any()

    by_mailbox: dict[str, list[dict]] = {}
    for entry in entries:
        by_mailbox.setdefault(entry["mailbox"], []).append(entry)

    wl.ok(f"{len(entries)} message(s) across {len(by_mailbox)} mailbox(es)")
    for mailbox, items in sorted(by_mailbox.items()):
        folders = sorted({i["folder"] for i in items})
        wl.info(f"{mailbox}: {len(items)} message(s) in {', '.join(folders)}")

    if args.dry_run:
        wl.heading("Dry run")
        for mailbox, items in sorted(by_mailbox.items()):
            wl.dry(f"would ensure mailbox {mailbox} exists (creds + imap-acct)")
            for entry in sorted(items, key=lambda e: e["date"]):
                subject = (entry["message"].get("Subject") or "")[:48]
                flags = " ".join(entry["flags"]) or "-"
                wl.dry(
                    f"  APPEND {mailbox}/{entry['folder']} "
                    f"[{entry['date'].isoformat()}] flags={flags} :: {subject}"
                )
        wl.summarise(True, [f"{len(entries)} message(s) validated, 0 appended"])
        return 0

    wl.heading("Ensuring mailboxes")
    passwords: dict[str, str] = {}
    for mailbox in sorted(by_mailbox):
        persona = next((p for p in identities if p.mailbox == mailbox), None)
        password = persona.password if persona else world.persona_password
        passwords[mailbox] = password
        if args.no_create_accounts:
            if mailbox not in existing_accounts():
                raise SystemExit(f"mailbox {mailbox} does not exist and --no-create-accounts is set")
            wl.info(f"{mailbox} exists")
        elif ensure_mailbox(mailbox, password):
            wl.ok(f"created mailbox {mailbox}")
        else:
            wl.info(f"{mailbox} already exists")

    wl.heading("Appending messages")
    appended = 0
    for mailbox, items in sorted(by_mailbox.items()):
        conn = connect(world, mailbox, passwords[mailbox], args.use_ssl)
        try:
            for folder in sorted({i["folder"] for i in items}):
                ensure_folder(conn, folder)
                for entry in sorted([i for i in items if i["folder"] == folder],
                                    key=lambda e: e["date"]):
                    append_message(conn, folder, entry)
                    appended += 1
                    if args.verbose:
                        wl.info(f"{mailbox}/{folder} <- {entry['rel']}")
        finally:
            try:
                conn.logout()
            except Exception:  # noqa: BLE001
                pass
        wl.ok(f"{mailbox}: {len(items)} message(s) appended")

    wl.summarise(False, [
        f"{appended} message(s) appended across {len(by_mailbox)} mailbox(es)",
        f"read them at {world.url('mail')}",
    ])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\n\033[31mfailed\033[0m  {exc}", file=sys.stderr)
        raise SystemExit(1)
