---
title: "curator.LLM core build plan"
author: dermot
created_at: 2024-11-05T09:05:08+00:00
---

# curator.LLM core build plan

## Why this document exists

PR 9 closed out the HF Dataset removal and locked the row schema. PR 10 is open and introduces the sqlite metadata layer. There are a few interface decisions in PR 10 that still need agreement before we merge, and I want the downstream shape written down in one place so the cookbook and fine-tuning teams are not blocked on reading the PRs themselves.

---

## Dataset shape

The pipeline works over a plain Python list of dicts, one dict per row. No HuggingFace Dataset wrapper.

Three reasons we dropped HF Dataset (settled in PR 9):

1. It flattens nested structures silently. That corrupts multi-turn conversation traces and chain-of-thought reasoning fields, which are exactly the rows we care most about preserving correctly.
2. It pulls in pyarrow as a hard dependency. Downstream callers (cookbook examples, fine-tuning handoff) do not need it and should not be forced to carry it.
3. Iteration over a plain list is deterministic. HF Dataset iteration order has subtle dependencies on the underlying arrow file layout, which made reproducing the same row sequence unreliable.

### Row schema

Minimum required fields:

- `id` (str), xxhash of the row, hex digest, 16 characters
- `prompt` (str or list), input as sent to the model
- `response` (str), raw completion, not post-processed
- `model` (str), identifier as returned by the provider, e.g. `gpt-4o-2024-08-06`
- `created_at` (int), unix timestamp, seconds

Additional fields are passed through unchanged. Nothing strips or renames unknown keys.

---

## Hashing and deduplication

Row identity is computed as:

```
xxhash.xxh64(json.dumps(row_without_id, sort_keys=True, ensure_ascii=False)).hexdigest()
```

The `id` field is excluded before hashing, so the hash is stable regardless of insertion order and does not depend on itself.

xxhash over hashlib.sha256 because throughput matters here. At up to 1M rows the collision probability of xxh64 is acceptable for deduplication purposes. It is not acceptable for security use, and we are not using it for that.

Deduplication at this milestone is exact-match only: same hash, row is dropped. Semantic deduplication (embedding-based or otherwise) is out of scope. I think that is right for now, the exact-match dedup alone will catch the main problem cases we have seen with repeated API calls.

---

## Metadata persistence

PR 10 adds a sqlite file (`metadata.db`) written alongside the dataset. One row per dataset row, indexed on `id`. Purpose is twofold: support the curator viewer, and give the fine-tuning handoff an audit trail it can query without loading the full row list into memory.

Schema as of the current PR 10 draft:

```sql
CREATE TABLE rows (
    id TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    source_file TEXT,
    pipeline_run TEXT
);
```

The two outputs of curator.LLM are the list-of-dicts and the db path. Everything downstream reads from one or both. curator.LLM does not own what happens to either after handoff.

---

## Request pipeline interface

One entry point:

```python
curate(requests, model, pipeline_id) -> (rows, db_path)
```

- `requests`, list of prompt dicts
- `model`, model identifier string, passed through to each row and to the db
- `pipeline_id`, written into `pipeline_run` in the db; caller generates it

Batching is the caller's responsibility. curator.LLM does not manage concurrency internally at this milestone. Bulk inference is a later concern and I dont want to design for it now before we know what the actual throughput requirements look like.

---

## Open questions

- `source_file` in the sqlite schema is currently nullable (PR 10 as drafted). The cookbook examples will want it populated, so either we make it required or we document that callers must pass it. I am leaning toward required with an empty string allowed rather than NULL, but not entirely sure that is the right call. Need to check with whoever owns the cookbook integration.
- The fine-tuning handoff format is not settled. The current plan assumes the downstream caller transforms the row list into whatever format the fine-tuning job needs. curator.LLM does not own that transformation. If that assumption is wrong we need to know before PR 10 merges.
- `pipeline_id` generation, is that on the caller or do we provide a utility? TBD.

---

## Dependencies

- xxhash (pip), row hashing
- sqlite3 (stdlib), metadata persistence
- No HuggingFace datasets, no pyarrow at this layer
