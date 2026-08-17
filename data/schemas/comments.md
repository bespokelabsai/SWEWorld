# `comments.jsonl` — BookStack page comments

**File:** `data/comments.jsonl`
**Consumed by:** `scripts/ingest_comments.py`
**Target:** BookStack's `/api/comments`

Conventions (timestamps, person references, unknown-key handling) are defined
in [`identities.md`](identities.md). The documents being commented on are
defined in [`docs.md`](docs.md).

---

## Shape

JSON Lines: one comment per line. Lines may be in any order; ingestion sorts by
`created_at`.

```json
{"doc":"engineering/architecture/storage-layer.md","author":"alice","created_at":"2026-01-18T09:12:00Z","id":"c1","quote":"Blast radius.","text":"Does this hold for the read replicas too?"}
```

---

## Fields

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `doc` | string | yes | — | Repo-relative path under `data/docs/`, the same key cross-links use. Must resolve to a document that becomes a **page**. |
| `author` | string | yes | — | Persona `id`. |
| `created_at` | string | yes | — | ISO-8601. Written to the database after creation. |
| `text` | string | yes | — | **Plain text, not markdown.** See below. |
| `id` | string | no | — | Stable handle so other comments can reply to this one. Required on a comment that is replied to. |
| `reply_to` | string | no | — | The `id` of the comment this replies to. Must be on the same `doc`. |
| `quote` | string | no | — | Text from the page this comment is about. Anchors the comment to that spot. |
| `archived` | bool | no | `false` | Marks a thread resolved. Only valid on a comment with no `reply_to`. |

### `text` is plain text

BookStack's API takes `html`, and this repo depends only on `requests` and
`PyYAML` — there is no markdown library to convert with, and adding one for a
single field is not worth it. So `text` is escaped, blank lines become
paragraphs and single newlines become line breaks. That covers essentially every
real comment.

This is the one place in `data/` where prose is *not* markdown. It is called out
here because assuming otherwise is reasonable and wrong: backticks and asterisks
will appear literally.

### Replies may nest, unlike chat

`messages.jsonl` forbids a threaded message from carrying its own `id`, because
Mattermost has no sub-threads. BookStack builds its comment tree recursively, so
here a comment with `reply_to` **may** also have an `id` and be replied to in
turn. A reader who knows the chat schema will assume the restriction carries
over. It does not.

Chains are capped at 10 deep — BookStack's own tree builder recurses without a
bound, so the limit lives here.

---

## Anchoring a comment to page text

Write `quote` as the text **as it reads on the rendered page**, not as it
appears in the markdown source:

```json
{"doc":"engineering/onboarding.md","author":"bob","created_at":"2026-01-16T10:00:00Z","quote":"Clone platform","text":"This needs the SSH key step first."}
```

The source says ``Clone `platform` `` — the backticks are markup, not text, so
they are not part of the quote. Same for `**bold**`, `[links](x.md)` and
headings: quote what a reader sees.

Ingestion turns that into BookStack's `content_ref`, which is an element id, a
content hash and a character range. **There is no field for `content_ref` and
there never should be**: it is derived from the rendered HTML, which does not
exist until the page has been created, and hand-writing one produces a reference
that silently renders as `outdated`.

A quote that does not appear, or appears more than once, is an error. That is
the point of the feature as much as the highlight is — a comment quoting text
that has since been edited out of the page is exactly the inconsistency worth
catching, and it is caught at parse time rather than by a reader noticing.

If a quote is ambiguous, lengthen it. There is deliberately no "second
occurrence" selector: an index into duplicates breaks silently the moment the
document is edited.

---

## Ordering

Comments are created in `created_at` order, per page. This is not cosmetic.
BookStack assigns each comment a `local_id` counting up from 1 within its page,
and a reply refers to its parent by that `local_id` — so a parent must be
created before its replies, or the reference cannot be resolved.

Requiring that a reply is not older than its parent (validation 10 below) makes
chronological order *be* parent-first ordering, at any depth. That is why the
rule exists, and why a reply that predates the comment it answers is rejected
rather than quietly reordered.

---

## Validation

`--dry-run` parses everything and calls no API. It enforces:

1. Valid JSON on every line; the failing line number is reported.
2. No unknown keys.
3. `doc` resolves to a `.md` under `data/docs/` that becomes a page. A document
   with children becomes a chapter, and the comment attaches to the page holding
   its body — so a childed document with an empty body has nothing to comment on
   and is an error.
4. `author` exists in `identities.yaml`.
5. `created_at` parses, with an explicit offset.
6. `text` is non-empty.
7. `id` values are unique; a duplicate names the earlier line.
8. `reply_to` refers to an `id` that exists, on the same `doc`.
9. `reply_to` is not self-referential, and reply chains are at most 10 deep.
10. A reply's `created_at` is not earlier than its parent's.
11. `archived` is only set on a comment with no `reply_to` — BookStack archives
    whole threads, not individual replies.
12. `quote`, if present, appears exactly once in the document's rendered text.

Validation 12 runs offline against a plaintext projection of the markdown
source, which is an approximation of what BookStack will render. The exact check
happens against the real HTML at write time, for every quote on every page,
*before* any comment is created — so a bad quote fails the run with nothing
written, rather than leaving a half-commented page behind.

`--dry-run` says so explicitly rather than letting the weaker check pass for the
stronger one.

---

## Mapping to the API

| Source | Call | Fields |
|---|---|---|
| every line | `POST /api/comments` | `page_id`, `html`, `reply_to`, `content_ref` |
| `archived: true` | `PUT /api/comments/{id}` | `archived` |
| every comment, afterwards | `UPDATE comments` | `created_at`, `updated_at`, `created_by`, `updated_by` |
| every commented page, afterwards | `UPDATE entities` | `created_at`, `updated_at` re-applied |

The last row is defensive. BookStack 25.11 does **not** touch a page's
`updated_at` when a comment is added — that was measured, not assumed — so the
re-settle currently rewrites the values it already finds. It stays because the
failure it guards against is silent: a version that did bump the parent would
leave every commented page reading "updated just moments ago", the exact tell
backdating exists to avoid, and no check here would catch it.

Comments are created by the token owner and then reattributed in SQL, the same
two-step `ingest_docs.py` uses for pages, and for the same reason: the API has
no author or date field. BookStack's own audit log still records the admin
making the changes at ingestion time; that is left alone deliberately, since the
audit log is not part of what the world presents to a reader.

Authentication is one header: `Authorization: Token <token_id>:<token_secret>`,
read inside the world from `/etc/sweworld/bookstack-token`.

Comments attach to pages only. There is no way to comment on a book, a chapter
or a shelf, in BookStack or here.
