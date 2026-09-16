# `history/` — the real repository, under the company's names

**Directory:** `data/history/`
**Produced by:** `make history`, on the **host** — `scripts/ingest_history.py --export`, then `scripts/ingest_forge.py --export`
**Consumed by:** `scripts/ingest_history.py`, then `scripts/ingest_forge.py`, inside the world — the first two ingests `bake-image` runs
**Target:** `worldadmin/curator` in Gitea — commits, branches and tags, then issues, pull requests, reviews, comments, releases and labels

Unlike the rest of `data/`, nothing here is written by a model. It is the real
`bespokelabs/curator` history with who-did-it replaced, and `install_corpus.py`
never touches it. Person references follow [`identities.md`](identities.md).
It replaces the placeholder [`commits.jsonl`](commits.md).

---

## Files

| File | Written by | Holds |
|---|---|---|
| `curator.bundle` | `ingest_history.py --export` | `git bundle create --all` of the rewritten repository (~80MB). Trees are byte-identical to the real ones; only author/committer identities, personal branch prefixes, and names and forge URLs inside commit messages change. |
| `manifest.json` | `ingest_history.py --export` | What the rewrite did, and the SHA map the forge needs. |
| `forge.json` | `ingest_forge.py --export` | GitHub's record of the repository, trimmed out of `data_gen/build/repository_history.json` (~25MB). |
| `forge-people.json` | `ingest_forge.py --export` | Who each GitHub login becomes, trimmed out of `data_gen/build/company_grounding.json`. |

**The directory is gitignored, and must stay so.** The `author_map` keys in
`manifest.json` and the `real` entries in `forge-people.json` are the real
contributors' names and addresses — that is what the map maps *from*. They enter
the image only as ingest inputs; what the ingest writes is the personas.

`make history` is the only target that reads `curator/`, and it only reads: the
export works in a temporary clone with no remote, and refuses any push target
that is not the world.

---

## `manifest.json`

```json
{
 "schema_version": 1,
 "generator": "scripts/ingest_history.py --export",
 "generated_at": "2026-08-22T14:31:18+00:00",
 "repo": "curator",
 "domain": "world.local",
 "source": {"remote": "https://github.com/bespokelabsai/curator.git", "head": "461b4170…", "commits": 1734},
 "counts": {"commits": 1734, "branches": 38, "tags": 28, "signatures": 34,
            "identities_replaced": 3469, "messages_edited": 285,
            "refs_renamed": 68, "mapped_commits": 1734},
 "author_map": {"<real name><NUL><real email>": {"name": "Emil Brandvold", "email": "emil@world.local", "persona": "emil"}},
 "ref_map": {"refs/heads/shreyas/finetuning-client": "refs/heads/nikolai/finetuning-client"},
 "default_branch": "main",
 "head": "a60745ff…",
 "commit_map": {"7c5efccf…": "05ec9e75…"}
}
```

| Field | Notes |
|---|---|
| `schema_version` | `1`. |
| `domain` | The `WORLD_DOMAIN` the persona addresses were written for. |
| `source` | The real clone: remote, head SHA, commit count. |
| `counts.commits` | Checked against `git rev-list --all --count` of the unbundled mirror. A mismatch aborts: the bundle and the manifest are out of step. |
| `author_map` | Key is one real signature, `name` and `email` joined by a NUL byte; value is the persona it became. |
| `ref_map` | Only the branches that carried a personal handle. Every other ref keeps its name. |
| `default_branch`, `head` | The rewritten default branch and its tip. Set as Gitea's default branch after the push. |
| `commit_map` | **Real SHA → rewritten SHA**, for every commit. Rewriting an identity changes every SHA after it, and GitHub's record names the old ones; `ingest_forge.py` uses this to point each pull request at a commit that exists. |

---

## `forge.json`

Compact JSON, no indentation. Only what the forge ingest reads out of the
generator's 50MB history — trees and blobs are already in the bundle.

```json
{
 "schema_version": 1,
 "generator": "scripts/ingest_forge.py --export",
 "generated_at": "…",
 "github": {
   "pulls": […], "issues": […], "releases": […], "labels": […], "branches": […],
   "reviews": {"<pr number>": […]}, "review_comments": {"<pr number>": […]},
   "pull_commits": {"<pr number>": […]}, "comments": {"<issue number>": […]}
 },
 "commits": [{"sha": "<real sha>", "parents": ["<real sha>"]}]
}
```

| Field | Notes |
|---|---|
| `github.*` | GitHub REST API objects **as returned** — real SHAs, logins and bodies. Lists for `pulls` (461), `issues` (270), `releases` (26), `labels` (20), `branches` (38); objects keyed by number for `reviews`, `review_comments`, `pull_commits` and `comments`. Names are rewritten out of bodies at ingest, not here. |
| `commits` | Each real commit's parents. Only 209 of 461 pull request heads survive squash merges under their own SHA, but a merge commit's second parent *is* the head, which is how most of the rest are recovered. |

---

## `forge-people.json`

Compact JSON: the three keys of phase 1's grounding the forge ingest reads.

| Key | Notes |
|---|---|
| `identity_map` | `login_to_persona` (GitHub login → persona `id`) is what every issue, PR, review and comment author resolves through. `unresolved` should be empty. |
| `people[]` | One per real contributor: `real` (their real identities), `synthetic` (the persona; `synthetic.id` is the join key), `class`, `status`, and phase 1's evidence. Also the source of the leak patterns that reject a body in which a real name survives. |
| `source` | The grounding and history files this was trimmed from, with hashes and the head commit. |

---

## How it is ingested

`ingest_history.py`, in the world:

1. Clones the bundle to a scratch mirror and checks its commit count against the manifest.
2. Creates a Gitea account for every non-admin persona in `identities.yaml`, with the persona `password`, so commits and forge items have users to attach to.
3. Force-pushes every branch and tag over `worldadmin/curator`, replacing the bootstrap's single `Initial import` commit.
4. Sets the default branch, and re-adds `.gitea/workflows/ci.yml` on top — the real history has no `.gitea/`, so the force-push removes it and CI goes quiet with nothing in the UI to say why.

`ingest_forge.py`, after it:

1. Numbers issues and pull requests in one shared sequence, with placeholders in the gaps. 1,734 commit subjects cite numbers like `(#728)`; an off-by-one would silently rewrite every cross-reference.
2. Creates each item over REST as its author (`Sudo:` header), with real names rewritten out of every body.
3. Backdates everything in one SQLite transaction and repairs the counters Gitea caches on the repository row, because the API cannot set a creation time.

`--dry-run` on either resolves and checks everything and writes nothing.
`ingest_forge.py --plan-out` writes the resolved numbering, which phase 3 reads
so a clue can be planted in an issue that will really exist. Run outside the
world with no `data/history/forge.json`, `ingest_forge.py` falls back to
`data_gen/build/`, so a dry run needs no export first.

---

## Validation

1. Each `--export` aborts if its input is missing — run `extract_repository_history.py` and `phase1_company_grounding.py` first.
2. The history export checks every tree survives the rewrite unchanged, every real ref arrives under its mapped name, and no real name, address or handle is left where a person can see it.
3. In the world, the bundle's commit count must equal `counts.commits`, and a persona password under eight characters aborts before Gitea can reject it as `PasswordIsRequired`.
4. The forge plan must be contiguous, every item must have an author, and no real name may survive in any body — otherwise nothing is written.
5. `world-verify` fails a baked world holding fewer than 100 issues and pull requests.
