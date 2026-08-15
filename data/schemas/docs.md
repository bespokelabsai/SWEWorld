# `data/docs/` — Outline collections and documents

**Files:** `data/docs/collections.yaml` + `data/docs/**/*.md`
**Consumed by:** `scripts/ingest_docs.py`
**Target:** Outline's `collections.create` and `documents.create` API

Conventions are defined in [`identities.md`](identities.md).

---

## Layout

Directory structure mirrors the document tree. A document nested under another
is a file inside a directory named for its parent.

```
data/docs/
  collections.yaml
  engineering/                     # -> collection "Engineering"
    onboarding.md                  # top-level document
    architecture.md
    architecture/                  # children of architecture.md
      storage-layer.md
      api-gateway.md
  product/
    roadmap-q1.md
```

A directory that shares a stem with a sibling `.md` file holds that document's
children. Nesting is unlimited.

---

## `collections.yaml`

```yaml
version: 1
collections:
  - dir: engineering
    name: Engineering
    description: How the platform is built and run.
    icon: beaker
    color: "#0366d6"
    permission: read_write
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `version` | int | yes | — | Must be `1`. |
| `collections[].dir` | string | yes | — | Directory name under `data/docs/`. Must exist. |
| `collections[].name` | string | yes | — | Display name in Outline. |
| `collections[].description` | string | no | `""` | Plain text. |
| `collections[].icon` | string | no | — | Outline icon name. |
| `collections[].color` | string | no | — | `#rrggbb`. Outline validates this and rejects malformed values. |
| `collections[].permission` | enum | no | `read_write` | `read` \| `read_write` \| `null` (private). |

Every directory directly under `data/docs/` must have an entry. An unlisted
directory is an error, not an implicit collection — silently inventing
collections makes typos invisible.

---

## Document files

Markdown with YAML frontmatter. The body is the document.

```markdown
---
title: Storage Layer
author: alice
created_at: 2026-02-11T14:03:00Z
---

We store everything in Postgres, with one database per service.

## Why not a shared database

Blast radius. A migration that locks a table should not be able to take down
chat and docs at the same time.
```

| Frontmatter | Type | Required | Default | Notes |
|---|---|---|---|---|
| `title` | string | yes | — | Outline shows this, not the filename. |
| `author` | string | yes | — | Persona `id`. See *Authorship* below. |
| `created_at` | string | yes | — | ISO-8601. **Must be in the past** — Outline rejects future dates. |
| `updated_at` | string | no | `created_at` | Advisory; Outline sets its own on write. |
| `publish` | bool | no | `true` | `false` creates a draft, visible only to its author. |
| `icon` | string | no | — | Outline icon name. |
| `full_width` | bool | no | `false` | Maps to `fullWidth`. |

The body is passed to Outline as `text` verbatim. Outline parses standard
Markdown, so headings, tables, code fences, task lists, and `[links](...)` all
survive. It is stored as ProseMirror internally, so exotic raw HTML may be
dropped — stick to Markdown.

### Cross-links between documents

Reference another document by its repo-relative path:

```markdown
See [the API gateway](engineering/architecture/api-gateway.md).
```

`ingest_docs.py` rewrites these to real Outline URLs after all documents are
created, in a second pass — the target's UUID does not exist until it has been
created. Unresolvable links are reported as warnings and left as-is.

---

## Authorship

Outline's `documents.create` accepts `createdAt` but has **no author field**.
The document is attributed to whoever owns the API token.

So `ingest_docs.py` has two modes:

- **default** — for each distinct `author`, log into Outline as that persona via
  Gitea OIDC (the mechanism `scripts/mint_outline_token.py` already implements),
  mint a token, and create their documents with it. Requires each persona to
  have a Gitea password; see `identities.md`.
- **`--single-author`** — create everything with `$OUTLINE_API_TOKEN`. Every
  document shows the admin as author. Faster, no persona passwords needed.

A persona's Outline account is created by their first OIDC login. There is no
API to pre-create one.

---

## Validation

`--dry-run` parses everything and calls no API. It enforces:

1. `collections.yaml` is valid, `version == 1`, and every `dir` exists.
2. Every directory under `data/docs/` has a collection entry.
3. Every `.md` file has parseable frontmatter with `title`, `author`,
   `created_at`.
4. `author` exists in `identities.yaml`.
5. `created_at` parses and is in the past.
6. `color` matches `^#[0-9a-fA-F]{6}$` if present.
7. Every child directory has a matching sibling `.md` file — an orphan
   directory means the parent document is missing.
8. Cross-links resolve to a file that exists; unresolved ones are warnings.
9. No unknown frontmatter keys.

---

## Mapping to the API

| Source | API call | Field |
|---|---|---|
| `collections.yaml` entry | `collections.create` | `name`, `description`, `icon`, `color`, `permission` |
| `data/docs/x/foo.md` | `documents.create` | `title`, `text` (body), `createdAt`, `publish` |
| parent directory | `documents.create` | `collectionId` |
| nested directory | `documents.create` | `parentDocumentId` |

`documents.import` is deliberately not used: it uploads a file and does not
accept `createdAt`, so every document would be stamped with the ingest time.
