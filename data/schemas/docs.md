# `data/docs/` — BookStack books, chapters and pages

**Files:** `data/docs/collections.yaml` + `data/docs/**/*.md`
**Consumed by:** `scripts/ingest_docs.py`
**Target:** BookStack's `/api/books`, `/api/chapters`, `/api/pages`

Conventions are defined in [`identities.md`](identities.md). Comments on these
documents are defined in [`comments.md`](comments.md).

---

## Layout

Directory structure mirrors the document tree. A document nested under another
is a file inside a directory named for its parent.

```
data/docs/
  collections.yaml
  engineering/                     # -> book "Engineering"
    onboarding.md                  # top-level document
    architecture.md
    architecture/                  # children of architecture.md
      storage-layer.md
      api-gateway.md
  product/
    roadmap-q1.md
```

A directory that shares a stem with a sibling `.md` file holds that document's
children. See *Mapping onto BookStack's model* below for how depth is handled.

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
| `collections[].name` | string | yes | — | The book's display name. |
| `collections[].description` | string | no | `""` | Plain text. |
| `collections[].icon` | string | no | — | Accepted and ignored. |
| `collections[].color` | string | no | — | Accepted and ignored. |
| `collections[].permission` | enum | no | `read_write` | Accepted and ignored; the world is a single trusted workspace. |

Every directory directly under `data/docs/` must have an entry. An unlisted
directory is an error, not an implicit book — silently inventing books
makes typos invisible.

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
| `title` | string | yes | — | Shown as the page/chapter name, not the filename. |
| `author` | string | yes | — | Persona `id`. See *Authorship* below. |
| `created_at` | string | yes | — | ISO-8601. Written to the database after creation. |
| `updated_at` | string | no | `created_at` | Written alongside `created_at`. |
| `publish` | bool | no | `true` | Accepted and ignored; BookStack has no draft state for API-created pages. |
| `icon` | string | no | — | Accepted and ignored. |
| `full_width` | bool | no | `false` | Accepted and ignored. |
| `tags` | list | no | — | Reserved for BookStack tags. |

The body is sent as `markdown`, so headings, tables, code fences and links all
survive. BookStack converts it to HTML on write and keeps the markdown source.

### Cross-links between documents

Reference another document by its repo-relative path:

```markdown
See [the API gateway](engineering/architecture/api-gateway.md).
```

Links that resolve to a real file are validated at parse time. Unresolvable
ones are reported as warnings and left exactly as written, so a broken link is
visible in the source rather than silently rewritten.

---

## Mapping onto BookStack's model

BookStack is **Shelf > Book > Chapter > Page**, only two levels below a book,
while this tree allows arbitrary nesting. The ingestion resolves that:

| Source | BookStack |
|---|---|
| a collection directory | **Book** |
| a `.md` with no children | **Page** in that book |
| a `.md` with children | **Chapter** — plus a page holding its own body, so no content is lost |
| anything nested deeper | flattened into that chapter, with a warning naming the file |

If you need a strict two-level structure, keep the source tree two levels deep
and nothing is reshaped.

## Authorship and dates

BookStack's API has no `created_at` and no author field: a page is stamped
`now` and attributed to whoever owns the token.

Unlike Outline, this is fully fixable — the world owns the database. So
`ingest_docs.py` creates entities through the API (which handles slugs,
revisions and the search index properly) and then corrects the record:

```sql
UPDATE entities
   SET created_at=?, updated_at=?, created_by=?, updated_by=?, owned_by=?
 WHERE id=?;
```

Personas are created as BookStack users on demand purely so attribution has
something to point at — they never log in, so they get no password.
`--single-author` skips all of that and leaves everything owned by the admin.

---

## Validation

`--dry-run` parses everything and calls no API. It enforces:

1. `collections.yaml` is valid, `version == 1`, and every `dir` exists.
2. Every directory under `data/docs/` has a collection entry.
3. Every `.md` file has parseable frontmatter with `title`, `author`,
   `created_at`.
4. `author` exists in `identities.yaml`.
5. `created_at` parses.
6. Every child directory has a matching sibling `.md` file — an orphan
   directory means the parent document is missing.
7. Cross-links resolve to a file that exists; unresolved ones are warnings.
8. Nesting deeper than one level below a book is a warning, not an error — it
   is flattened, and the warning names the file so it is never a surprise.
9. No unknown frontmatter keys.

---

## Mapping to the API

| Source | Call | Fields |
|---|---|---|
| `collections.yaml` entry | `POST /api/books` | `name`, `description` |
| a `.md` with children | `POST /api/chapters` | `book_id`, `name` |
| a `.md` without children | `POST /api/pages` | `book_id` or `chapter_id`, `name`, `markdown` |
| every entity, afterwards | `UPDATE entities` | `created_at`, `created_by`, `owned_by` |

Authentication is one header: `Authorization: Token <token_id>:<token_secret>`.
Inside the world that pair is at `/etc/sweworld/bookstack-token`, generated at
image build.
