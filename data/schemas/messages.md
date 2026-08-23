# `messages.jsonl` — Mattermost chat history

**Files:** `data/messages.jsonl` + `data/channels.yaml`
**Consumed by:** `scripts/ingest_chat.py`
**Target:** Mattermost's bulk import (`mmctl import process --bypass-upload --local`)

Conventions are defined in [`identities.md`](identities.md).

---

## Two formats, on purpose

What you author is **flat**: one message per line, threads linked by
`thread_id`. What Mattermost ingests is **nested and strictly ordered**.
`ingest_chat.py` performs that conversion.

This is the one place these schemas deliberately do not mirror the target
format. Mattermost's importer requires:

- every object wrapped under a key matching its type —
  `{"type":"post","post":{…}}` — not the flat fields the public docs imply;
- objects in a fixed order: `version → team → channel → user → post`;
- `create_at` in **epoch milliseconds**;
- thread replies nested inside their root post's `replies[]` array, with no
  parent pointer anywhere.

Asking a generation step to emit that correctly — especially the ordering and
the nesting — would make the data far harder to produce and to review. Authoring
stays flat; the script assembles the archive.

> The nesting-under-type-key detail was confirmed by taking a real export from
> the running Mattermost 11.9 server (`mmctl export create`) and reading it,
> rather than from the documentation, which describes the fields as flat.

---

## `channels.yaml`

```yaml
version: 1
team: world                  # must match MM_TEAM_NAME in .env
channels:
  - name: engineering
    display_name: Engineering
    type: O
    purpose: Day-to-day engineering chatter.
    header: "on-call: see runbook"
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `version` | int | yes | — | Must be `1`. |
| `team` | string | yes | — | Must equal `$MM_TEAM_NAME`. |
| `channels[].name` | string | yes | — | URL slug: lowercase, `^[a-z0-9-_]+$`. |
| `channels[].display_name` | string | yes | — | Shown in the sidebar. |
| `channels[].type` | enum | no | `O` | `O` public, `P` private. |
| `channels[].purpose` | string | no | `""` | |
| `channels[].header` | string | no | `""` | |
| `channels[].members` | list | no | all personas | Persona `id`s. Only meaningful for `P`. |

`town-square` and `off-topic` are created by Mattermost itself when the team is
made. Listing them is allowed and is a no-op.

---

## `messages.jsonl`

One message per line.

```json
{"channel":"engineering","author":"dario","created_at":"2026-02-11T09:02:14Z","text":"Deploy is green.","thread_id":null}
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `channel` | string | yes | — | Must exist in `channels.yaml`. |
| `author` | string | yes | — | Persona `id`. |
| `created_at` | string | yes | — | ISO-8601. Converted to epoch ms. |
| `text` | string | yes | — | Mattermost-flavoured Markdown. May be `""` only if `reactions` is non-empty. |
| `thread_id` | string \| null | no | `null` | See *Threads* below. |
| `id` | string | no | — | Stable handle so other messages can reply to this one. Required on a message that is replied to. |
| `reactions` | array | no | `[]` | `[{"author":"gideon","emoji":"tada","created_at":"..."}]` — emoji name without colons. |
| `pinned` | bool | no | `false` | Maps to `is_pinned`. |
| `attachments` | array | no | `[]` | `[{"path":"files/diagram.png"}]`, relative to `data/`. Copied into the archive's `data/` directory. |

### Threads

A root message carries an `id`. A reply sets `thread_id` to that `id`:

```jsonl
{"id":"m1","channel":"engineering","author":"dario","created_at":"2026-02-11T09:02:14Z","text":"Deploy is green."}
{"channel":"engineering","author":"gideon","created_at":"2026-02-11T09:04:01Z","text":"Nice, checking metrics now.","thread_id":"m1"}
{"channel":"engineering","author":"dermot","created_at":"2026-02-11T09:06:30Z","text":"p99 looks flat.","thread_id":"m1"}
```

`ingest_chat.py` groups replies under their root and emits one post object with
a nested `replies[]`. Replies must be in the same channel as their root and
must not be nested more than one level — Mattermost has no sub-threads.

> **Known upstream issue.** Bulk-imported replies have historically not always
> appeared as threads
> ([mattermost#14959](https://github.com/mattermost/mattermost/issues/14959)).
> `ingest_chat.py` verifies thread structure after import and reports any root
> whose reply count does not match, so a silent regression is visible rather
> than discovered weeks later.

### Direct messages

Set `channel` to `null` and provide `participants`:

```json
{"channel":null,"participants":["dario","gideon"],"author":"dario","created_at":"2026-02-12T11:00:00Z","text":"got a minute?"}
```

These become `direct_channel` and `direct_post` objects, which must come after
all regular posts. The script handles the ordering. 2–8 participants.

---

## Validation

`--dry-run` builds the complete import archive, writes it to a temp directory,
and does not call `mmctl`. It enforces:

1. Valid JSON per line; failing line number reported.
2. `channel` exists in `channels.yaml`, or is `null` with valid `participants`.
3. `author` and every `reactions[].author` exist in `identities.yaml`.
4. `created_at` parses.
5. `thread_id` refers to an `id` that exists, in the same channel, and is itself
   a root (no chained threading).
6. `id` values are unique.
7. `text` non-empty unless `reactions` is non-empty.
8. `attachments[].path` exists on disk.
9. Every persona referenced is emitted as a `user` object before any post — the
   importer will not create users implicitly.
10. No unknown keys.

The generated archive is left in place after a dry run so it can be inspected.

---

## Generated archive layout

```
world-import.zip
  import.jsonl          version, team, channels, users, posts, direct posts
  data/                 attachment files, if any
```

Run with `mmctl import process --bypass-upload world-import.zip --local`, which
skips the upload step entirely — available since Mattermost 9.5 and the reason
local mode is enabled in `docker-compose.yml`.

The import is idempotent: re-running the same archive does not duplicate posts.
It is not a sync — it only creates and overwrites, never deletes. To truly reset
the world, tear the stack down with `docker compose down -v`.
