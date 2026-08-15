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
| Timestamps | ISO-8601 with an explicit offset: `2026-03-14T09:22:31Z` or `...+01:00`. Ingestion converts to whatever each service wants (Mattermost needs epoch **milliseconds**, Outline needs a `Date`, git needs its own format). Never emit bare local times. |
| Person references | Always the persona `id` (`alice`), never a display name or email. |
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
  - id: alice
    display_name: Alice Nguyen
    email: alice@world.local
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
| `personas[].password` | string | no | `$MAIL_PERSONA_PASSWORD` | Login password for this persona across Gitea and mail. See *Authorship* below. |
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
`bootstrap.sh` creates it before any data exists.

You may still list it in `personas` (conventionally `id: worldadmin`) so it can
author content. Ingestion will not recreate it or change its password — it
matches on `gitea_username` and reuses the existing account.

---

## Authorship, and why `password` matters

Content attribution works differently per service, and this is the single
biggest constraint on the whole pipeline:

| Service | How authorship is set | Needs persona password? |
|---|---|---|
| Gitea | The commit's author string. Any value, no account needed. | No |
| Mattermost | The `user` field in the bulk import. The importer creates users. | No |
| Outline | **Whoever owns the API token.** There is no author field. | **Yes** |
| Mail | The `From:` header, plus which mailbox it is APPENDed into. | Yes, to log in as them |

Outline's `documents.create` accepts `createdAt` but has no `createdBy`. To
attribute a document to Alice, the script must hold *Alice's* token — which
means logging into Outline as Alice via Gitea OIDC, which means Alice needs a
Gitea password. That is what `password` is for.

If `password` is omitted, ingestion falls back to `MAIL_PERSONA_PASSWORD` from
`.env`, which is uniform across personas by design — these are disposable local
credentials, and keeping them out of the data file avoids per-user secrets in
version control.

If you do not care about per-author attribution in Outline, run
`ingest_docs.py --single-author`; every document is then created by the admin
token and no persona passwords are needed.

> A persona's Outline account does not exist until their **first successful
> OIDC login**. Outline provisions accounts on login and offers no API to
> pre-create them, so `ingest_docs.py` performs that login on demand.

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

  - id: alice
    display_name: Alice Nguyen
    email: alice@world.local
    role: Staff Engineer
    timezone: America/Los_Angeles

  - id: bob
    display_name: Bob Okafor
    email: bob@world.local
    role: Backend Engineer
    timezone: Europe/Berlin
    # Historical commits predate the world domain.
    git_author: Bob Okafor <bob.okafor@oldcorp.example>
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

| Field | Gitea | Mattermost | Outline | Mail |
|---|---|---|---|---|
| `id` | — | — | — | — |
| `display_name` | `full_name` | `first_name` + `last_name` | profile name via OIDC | `From:` display name |
| `email` | `email` | `email` | `email` via OIDC claim | mailbox address |
| `gitea_username` | `username` | — | `preferred_username` claim | — |
| `mattermost_username` | — | `username` | — | — |
| `role` | — | `position` | — | — |
| `password` | login password | — | (via Gitea OIDC) | IMAP/SMTP password |
| `is_admin` | `--admin` | `roles: system_user system_admin` | — | — |
