# `data/emails/` — mailbox contents

**Files:** `data/emails/index.jsonl` + `data/emails/**/*.eml`
**Consumed by:** `scripts/ingest_mail.py`
**Target:** IMAP `APPEND` against Maddy

Conventions are defined in [`identities.md`](identities.md).

---

## Layout

One `.eml` file per message, filed under the mailbox that holds it and the
folder it lives in. A single message appearing in two mailboxes (sender's Sent,
recipient's INBOX) is **two files** — that is how real mail servers store it,
and it lets each copy carry its own flags.

```
data/emails/
  index.jsonl
  dario@world.local/
    INBOX/
      2026-02-11-deploy-postmortem.eml
    Sent/
      2026-02-11-re-deploy-postmortem.eml
  gideon@world.local/
    INBOX/
      2026-02-11-re-deploy-postmortem.eml
```

Folder names are IMAP mailbox names. Maddy creates `INBOX`, `Sent`, `Drafts`,
`Trash`, `Archive`, and `Junk` when an account is made; any other folder is
created on demand.

Filenames are arbitrary — nothing parses them. Use something sortable and
human-readable.

---

## The `.eml` files

Standard RFC 5322. Written as-is into the mailbox, byte for byte.

```
From: Dario Kestrel <dario@world.local>
To: Gideon Okafor <gideon@world.local>
Cc: platform@world.local
Subject: Deploy postmortem
Date: Wed, 11 Feb 2026 09:14:02 +0000
Message-ID: <20260211091402.dario.1@world.local>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Writing up what happened this morning.

The rollout stalled because the health check was pointing at the old port.
```

Requirements:

| Header | Required | Notes |
|---|---|---|
| `From` | yes | Should match a persona's `git_author`-style form: `Display Name <email>`. |
| `To` | yes | One or more addresses. |
| `Subject` | yes | May be empty but must be present. |
| `Date` | yes | RFC 5322 date. Must agree with `index.jsonl`'s `date`. |
| `Message-ID` | yes | Globally unique, angle-bracketed. Threading depends on it. |
| `In-Reply-To` | for replies | The parent's `Message-ID`. |
| `References` | for replies | Full chain, space-separated, oldest first. |
| `Content-Type` | no | Defaults to `text/plain; charset=utf-8`. |

Threading in every mail client is driven by `Message-ID` / `In-Reply-To` /
`References`. There is no separate thread field — get these headers right and
threads appear; get them wrong and a conversation shows up as unrelated
messages.

Line endings inside `.eml` files should be CRLF. `ingest_mail.py` normalises LF
to CRLF before `APPEND`, since RFC 5322 requires it and some clients render
lone-LF messages as one long line.

Multipart, attachments, and HTML bodies are all fine — construct them as normal
MIME. Python's `email.message.EmailMessage` generates correct output.

---

## `index.jsonl`

IMAP carries per-message state that cannot live inside the message itself. One
line per `.eml` file:

```json
{"path":"dario@world.local/INBOX/2026-02-11-deploy-postmortem.eml","mailbox":"dario@world.local","folder":"INBOX","date":"2026-02-11T09:14:02Z","flags":["\\Seen"]}
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `path` | string | yes | — | Relative to `data/emails/`. Must exist. |
| `mailbox` | string | yes | — | Account to append into. Must match a persona's `mailbox`. |
| `folder` | string | no | `INBOX` | IMAP folder. Created if absent. |
| `date` | string | yes | — | ISO-8601. Becomes the IMAP **INTERNALDATE**. |
| `flags` | array | no | `[]` | IMAP flags: `\Seen`, `\Answered`, `\Flagged`, `\Draft`, `\Deleted`. |

### Why `date` is separate from the `Date:` header

They are different things. The `Date:` header is what the sender claims; the
INTERNALDATE is when the server received it, and it is what clients sort by and
what `SINCE`/`BEFORE` searches match on.

If INTERNALDATE is not set explicitly, the server stamps *now* — so a mailbox of
carefully dated historical mail all sorts as having arrived during ingestion,
and the illusion collapses on first glance at the inbox. Keep `date` equal to
the `Date:` header unless you are deliberately modelling delivery lag.

---

## Mailbox accounts

`ingest_mail.py` creates any mailbox that does not yet exist, using both
commands Maddy requires — credentials and the IMAP account are separate objects:

```
maddy creds create --password <password> <address>
maddy imap-acct create <address>
```

Passwords come from the persona's `password`, falling back to
`$MAIL_PERSONA_PASSWORD`. The script then authenticates as each persona in turn
to append into their own mailbox, rather than appending everything as admin —
Maddy has no cross-account append.

Connection defaults to `127.0.0.1:143` (`$IMAP_PORT`) with plaintext `LOGIN`,
which the closed-world Maddy config permits via `insecure_auth`. Use
`--use-ssl` for port 993 instead; the local CA is at
`config/tls/world-ca.crt`.

---

## Validation

`--dry-run` parses every message and connects to nothing. It enforces:

1. `index.jsonl` is valid JSON per line; failing line reported.
2. Every `path` exists, and every `.eml` under `data/emails/` has an index entry
   — an unindexed message would be silently skipped otherwise.
3. Each `.eml` parses as RFC 5322 and has `From`, `To`, `Subject`, `Date`,
   `Message-ID`.
4. `mailbox` matches a persona in `identities.yaml`.
5. `From` address matches a known persona.
6. `date` parses, and agrees with the `Date:` header within 24h (warning, not
   error — deliberate delivery lag is legitimate).
7. `Message-ID` is unique per `(mailbox, folder)`.
8. Every `In-Reply-To` / `References` id resolves to a message somewhere in the
   dataset; dangling references are warnings, since a thread may legitimately
   start before the window being modelled.
9. `flags` are drawn from the known set.

---

## Example

```jsonl
{"path":"dario@world.local/Sent/001-deploy-postmortem.eml","mailbox":"dario@world.local","folder":"Sent","date":"2026-02-11T09:14:02Z","flags":["\\Seen"]}
{"path":"gideon@world.local/INBOX/001-deploy-postmortem.eml","mailbox":"gideon@world.local","folder":"INBOX","date":"2026-02-11T09:14:05Z","flags":[]}
{"path":"dario@world.local/INBOX/002-re-deploy-postmortem.eml","mailbox":"dario@world.local","folder":"INBOX","date":"2026-02-11T10:02:44Z","flags":["\\Seen","\\Answered"]}
```

The same message body appears twice — once in Dario's `Sent`, once in Gideon's
`INBOX` — with different flags and slightly different INTERNALDATEs.
