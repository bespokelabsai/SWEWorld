# `identities.yaml` — the shared persona list

**File:** `data/identities.yaml`
**Consumed by:** every ingestion script
**Produced by:** the data-generation step (write this one first)

Every other schema references people by their persona `id`. Generate this file
before anything else; if a commit, document, message, or email names an `id`
that is not here, ingestion fails loudly rather than inventing a user.

---

## Shared conventions

These apply to **all** schemas in this directory.

| Rule | Detail |
|---|---|
| Timestamps | ISO-8601 with an explicit offset: `2026-03-14T09:22:31Z` or `...+01:00`. Ingestion converts to whatever each service wants (Mattermost needs epoch **milliseconds**, BookStack needs a MySQL `DATETIME` in UTC, git needs its own format). Never emit bare local times. |
| Person references | Always the persona `id` (`dario`), never a display name or email. |
| Encoding | UTF-8, LF line endings. |
| Ordering | Files may be in any order. Ingestion sorts by timestamp where order matters. |
| Unknown fields | Rejected, not ignored — a typo'd key is a bug, not a silent no-op. |
| IDs | `^[a-z0-9][a-z0-9_-]{1,31}$`. Stable forever; they are the join key across four services. |

---

## Schema

```yaml
version: 1
domain: world.local          # must match WORLD_DOMAIN in .env

personas:
  - id: dario
    display_name: Dario Kestrel
    email: dario@world.local
    role: Staff Engineer
```

### Fields

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `version` | int | yes | — | Must be `1`. |
| `domain` | string | yes | — | Must equal `WORLD_DOMAIN`. Guards against data generated for a different world. |
| `personas[].id` | string | yes | — | Join key. See ID rule above. |
| `personas[].display_name` | string | yes | — | Human name. Becomes Gitea full name, Mattermost first/last name, and the git author name. |
| `personas[].email` | string | yes | — | Must be `<local>@<domain>`. One address per persona across git, chat, and mail. |
| `personas[].role` | string | no | `""` | Job title. Becomes Mattermost `position`. Flavour only. |
| `personas[].timezone` | string | no | `UTC` | IANA name. Advisory — used by generation to pick plausible working hours. |
| `personas[].password` | string | no | `$MAIL_PERSONA_PASSWORD` | Login password for this persona's Gitea account and mailbox — nothing else has one. See *Authorship* below. |
| `personas[].gitea_username` | string | no | `id` | Override only if the id is not a valid Gitea username. |
| `personas[].mattermost_username` | string | no | `id` | Override only if the id collides with a Mattermost reserved name. |
| `personas[].git_author` | string | no | `{display_name} <{email}>` | Exact author string written into commits. Override for personas whose historical commits used a different address. |
| `personas[].mailbox` | string | no | `email` | Override only if the mailbox differs from the contact address. |
| `personas[].is_admin` | bool | no | `false` | Grants system admin in Gitea and Mattermost. |

Defaults exist so the common case is four lines per person. Only override when
a service forces your hand.

---

## The admin persona

The agent's own account is defined in `.env` as `WORLD_ADMIN_*`, **not** here.
`world/bootstrap/` creates it at image build, before any data exists.

You may still list it in `personas` (conventionally `id: worldadmin`) so it can
author content. Ingestion will not recreate it or change its password — it
matches on `gitea_username` and reuses the existing account.

---

## Authorship, and why `password` matters

Content attribution works differently per service, and this is the single
biggest constraint on the whole pipeline:

| Service | How authorship is set | Needs persona password? |
|---|---|---|
| Gitea | Commits: the author map `ingest_history.py --export` writes. Issues, PRs, reviews: created by the admin token with a `Sudo:` header, then backdated in SQLite. | Yes, to **create** the account — Gitea will not make one without it |
| Mattermost | The `user` field in the bulk import. The importer creates users, with no password. | No |
| BookStack | **Whoever owns the API token.** Pages are created as the admin, then `ingest_docs.py` rewrites the author and dates in MariaDB. | No |
| Mail | The `From:` header, plus which mailbox it is APPENDed into. | Yes, to log in as them |

BookStack's API stamps `now` and the token owner on everything, with no author
field. Rather than log in as each persona, `ingest_docs.py` inserts a user row
per persona straight into MariaDB with an **empty password** — an account that
can never sign in and exists only so a byline has something to point at — and
then corrects `entities`, `comments`, `page_revisions` and `activities` to that
user and the document's own timestamp. `ingest_comments.py` shares the same
resolver, so a page and its comments are never attributed differently.

If `password` is omitted, ingestion falls back to `MAIL_PERSONA_PASSWORD` from
`.env` (default `persona-world`), which is uniform across personas by design —
these are disposable local credentials, and keeping them out of the data file
avoids per-user secrets in version control. It must be at least eight
characters: Gitea rejects a shorter one as `PasswordIsRequired`, which sends you
looking for a missing field. A bake copies no `.env` into the container, so a
baked world carries the default.

If you do not care about per-author attribution in BookStack, run
`ingest_docs.py --single-author`; every document then stays owned by the admin.

---

## Example

```yaml
version: 1
domain: world.local

personas:
  - id: worldadmin
    display_name: World Admin
    email: worldadmin@world.local
    role: Platform
    is_admin: true

  - id: dario
    display_name: Dario Kestrel
    email: dario@world.local
    role: Staff Engineer
    timezone: America/Los_Angeles

  - id: gideon
    display_name: Gideon Okafor
    email: gideon@world.local
    role: Backend Engineer
    timezone: Europe/Berlin
    # Historical commits predate the world domain.
    git_author: Gideon Okafor <gideon.okafor@oldcorp.example>
```

---

## Validation

`ingest_*.py --dry-run` enforces, and fails with the offending path and line:

1. `version == 1` and `domain == $WORLD_DOMAIN`.
2. `id` matches the ID pattern and is unique.
3. `email` is well formed and its domain equals `domain`.
4. `gitea_username` / `mattermost_username` are unique after defaults are applied.
5. `email`, `mailbox` unique across personas.
6. No unknown keys at any level.
7. At most one persona per `gitea_username`.

Ingestion never mutates this file.

---

## Mapping to each service

| Field | Gitea | Mattermost | BookStack | Mail |
|---|---|---|---|---|
| `id` | — | — | — | — |
| `display_name` | `full_name` | `first_name` + `last_name` | `users.name` | `From:` display name |
| `email` | `email` | `email` | `users.email` (the lookup key) | mailbox address |
| `gitea_username` | `username` | — | — | — |
| `mattermost_username` | — | `username` | — | — |
| `role` | — | `position` | — | — |
| `password` | login password | — | none; the row has an empty password | IMAP/SMTP password |
| `is_admin` | not created — the bootstrap account is reused | `roles: system_user system_admin` | — | — |
