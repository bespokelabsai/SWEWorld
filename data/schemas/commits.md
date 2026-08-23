# `commits.jsonl` — rewritten git history

**File:** `data/commits.jsonl`
**Consumed by:** `scripts/ingest_git.py`
**Target:** a fresh local repo, replayed commit by commit, then pushed to Gitea

Conventions (timestamps, person references, unknown-key handling) are defined
in [`identities.md`](identities.md).

---

## Shape

JSON Lines: one commit per line, **in the order they should be committed**.
Parents are implicit — each line's parent is the previous line on the same
branch. This keeps the format writable by a generation step that does not have
to model a DAG.

```json
{"repo":"platform","branch":"main","author":"dario","authored_at":"2026-01-08T10:14:02Z","message":"Add health check endpoint","changes":[{"path":"api/health.go","action":"add","content":"package api\n\nfunc Health() string {\n\treturn \"ok\"\n}\n"}]}
```

---

## Fields

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `repo` | string | yes | — | Repo name in Gitea. Created via the API if absent. `^[a-zA-Z0-9._-]+$`. |
| `branch` | string | no | `main` | Created from the current tip on first use. |
| `author` | string | yes | — | Persona `id`. |
| `committer` | string | no | `author` | Persona `id`. Differs for applied patches or rebases. |
| `authored_at` | string | yes | — | ISO-8601. Becomes `GIT_AUTHOR_DATE`. |
| `committed_at` | string | no | `authored_at` | Becomes `GIT_COMMITTER_DATE`. |
| `message` | string | yes | — | Full commit message. `\n\n` separates subject from body, as git expects. |
| `changes` | array | yes | — | At least one entry. Applied in order. |
| `tag` | string | no | — | Lightweight tag placed on this commit. |

### `changes[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `action` | enum | yes | `add` \| `modify` \| `delete` \| `rename` |
| `path` | string | yes | Repo-relative, forward slashes, no leading `/`, no `..`. |
| `content` | string | for `add`/`modify` | **Full file content after the change.** Not a diff. |
| `from_path` | string | for `rename` | Previous path. Pair with `content` to rename and edit at once. |
| `mode` | string | no | `100644` (default) or `100755` for executables. |
| `encoding` | enum | no | `utf-8` (default) or `base64` for binary files. |

---

## Why full content instead of diffs

The obvious design is a unified diff per commit. It is the wrong one here.

Applying a diff requires the target file to be in exactly the state the diff was
generated against. Any drift — a reordered commit, a hand-edited line, a
regenerated file — and `git apply` fails with a conflict the ingestion script
cannot resolve. Debugging that means reconstructing intermediate tree states by
hand.

Writing the full post-change content is idempotent and order-independent: the
script writes bytes to disk and commits. A commit's diff is then whatever git
computes against the previous tree, which is correct by construction.

The cost is size — a large file edited fifty times is stored fifty times. For a
synthetic world that is not a real constraint, and `git gc` deduplicates on the
Gitea side anyway.

---

## Example

```jsonl
{"repo":"platform","branch":"main","author":"dario","authored_at":"2026-01-08T10:14:02Z","message":"Initial commit\n\nSkeleton service.","changes":[{"path":"README.md","action":"add","content":"# platform\n"},{"path":"go.mod","action":"add","content":"module platform\n\ngo 1.22\n"}]}
{"repo":"platform","branch":"main","author":"gideon","authored_at":"2026-01-09T14:03:55Z","message":"Add health endpoint","changes":[{"path":"api/health.go","action":"add","content":"package api\n\nfunc Health() string { return \"ok\" }\n"}]}
{"repo":"platform","branch":"feat/metrics","author":"dario","authored_at":"2026-01-11T09:41:00Z","message":"Start metrics work","changes":[{"path":"api/metrics.go","action":"add","content":"package api\n"}]}
{"repo":"platform","branch":"main","author":"gideon","committer":"dario","authored_at":"2026-01-12T16:20:10Z","committed_at":"2026-01-13T08:02:00Z","message":"Drop deprecated ping handler","changes":[{"path":"api/ping.go","action":"delete"}],"tag":"v0.1.0"}
```

---

## How it is replayed

For each line, `ingest_git.py`:

1. Ensures the repo exists locally (`git init`, default branch `main`) and in
   Gitea (`POST /api/v1/user/repos`, `auto_init: false`).
2. Checks out `branch`, creating it from the current tip if new.
3. Applies each `change` to the working tree.
4. Commits with the environment set:

   ```
   GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL       from the author's git_author
   GIT_AUTHOR_DATE                          authored_at
   GIT_COMMITTER_NAME / GIT_COMMITTER_EMAIL from the committer's git_author
   GIT_COMMITTER_DATE                       committed_at
   ```

   Both author *and* committer dates must be set. Setting only the author date
   is the classic mistake: the commits show the right date in `git log` but sort
   by today's date everywhere else, and Gitea's activity timeline shows the
   entire history landing in one afternoon.

5. After the last line for a repo, pushes all branches and tags with
   `--force`.

Pushes authenticate over HTTPS as `$WORLD_ADMIN_USER` using `$GITEA_API_TOKEN`.
The repo is owned by the admin regardless of who authored the commits —
authorship lives in the commit objects, which is how git actually works.

---

## Validation

`--dry-run` replays everything into a temporary local repo and **never pushes**,
so the history can be inspected before it reaches Gitea. It enforces:

1. Valid JSON on every line; the failing line number is reported.
2. `author` / `committer` exist in `identities.yaml`.
3. `authored_at` parses, and `committed_at >= authored_at`.
4. Timestamps for a given branch are non-decreasing.
5. `path` is relative, normalised, and does not escape the repo.
6. `content` present for `add`/`modify`; `from_path` present for `rename`.
7. `modify`/`delete`/`rename` reference a path that exists at that point in the
   replay — caught during replay, not by static inspection.
8. No unknown keys.

---

## Not covered

Merge commits, submodules, LFS, signed commits, and per-file history rewrites.
A merge can be approximated by a normal commit on `main` whose `message` reads
like one; nothing downstream inspects parent counts.
