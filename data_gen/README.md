# `data_gen/` — grounding the world in the repository it is built around

SWEWorld drops an agent into a company that ships one real service:
[`bespokelabs/curator`](https://github.com/bespokelabsai/curator), vendored as
`vendor/curator-461b4170b966.tar.gz` and served from Gitea inside the world.

A company spec can say what the business wants and what constrains it. It must
not also invent the *technical* shape of that company — the subsystems, the
interfaces, the test layout, the CI, the kinds of work engineers do, who owns
what. Invented technical shape produces a world whose commits, docs and chat
describe a codebase that is not the one the agent is looking at.

These scripts read that shape off the repository instead.

| Stage | Script | Output | Answers |
|---|---|---|---|
| 0 | `extract_repository_history.py` | `build/repository_history.json` + `build/repository_blobs/` | what the repository *actually contains*, code included |
| 1 | `build_episodes.py` | `build/engineering_episodes.json` | what work *happens* in it |
| 2 | `analyze_repository.py` | `build/engineering_grounding.json` | what the codebase *is*, and how the organization worked |
| — | `make_report.py` | `build/report.html` | all of it, browsable |

Stage 0 is the only thing that talks to GitHub or walks raw history; stages 1 and 2
read its record.

## Running it on another repository

Point `--repo` at any git checkout. Nothing is hardcoded to curator: the layout is
**discovered**, not declared.

```bash
python3 data_gen/extract_repository_history.py --repo ../some-project --out build/h.json --blobs-dir build/b
python3 data_gen/analyze_repository.py --repo ../some-project --history build/h.json --out build/g.json
```

Source roots are found from what the project says about itself (`pyproject.toml`
packages), else the shallowest directories holding `__init__.py`, else the
directories the source actually lives in — then pass-through package dirs are
stepped through, so `src/acme/` holding nothing but `__init__.py` and one
subpackage resolves to `src/acme/thing`. Import prefixes, test roots, doc and
example dirs, CI config and packaging files are discovered the same way, and the
result is written to the `layout` key of the output with the evidence for each
choice.

**If no source is found the run fails loudly** rather than emitting a hollow file —
that was the original defect: every lookup missed, the analysis came back empty,
and it still exited 0.

Per-repository contributor aliases (people committing under names that share
neither email nor spelling) go in `data_gen/aliases.yaml`; delete it for a
different project.

### What still assumes Python

Symbol-level diffs use Python's `ast`, and the deep config parse understands
Poetry/PEP-621 `pyproject.toml` and `pytest.ini`. On a Go or TypeScript repo
everything else works — history, episodes, subsystems, hotspots, ownership,
patterns, the full Stage 0 record — but you get no symbol diffs and a thinner
`configuration` section.

None of them writes `data/`. They produce the ground truth a later generation
step consumes.

## Running them

**Order matters**: each stage reads the one before it.

```bash
GITHUB_TOKEN=ghp_... python3 data_gen/extract_repository_history.py -v
python3 data_gen/build_episodes.py -v
data_gen/.venv/bin/python data_gen/analyze_repository.py -v
python3 data_gen/make_report.py
```

`analyze_repository.py --no-enrich` runs with the system interpreter and needs no
key at all; `--no-refresh` rebuilds from the cache without calling anything.
All three default to `--repo curator` at the repository root and full history;
`--since` / `--until` / `--rev` narrow it.

### Why `build_episodes.py` needs a GitHub token

Review cycles, reviewer identity, issue-open times and the true branch-commit
count of a squash-merged PR exist nowhere in a git clone. They are GitHub
state. Unauthenticated the API allows 60 requests an hour against a repository
that needs roughly 1,100; authenticated it allows 5,000, so the token is not
optional and the script fails immediately without one.

Every response is cached under `cache/github/`, keyed by URL and revalidated
with its ETag (GitHub does not bill a 304 against the rate limit). So the
backfill is paid once and is resumable — and afterwards:

```bash
python3 data_gen/build_episodes.py --no-refresh   # entirely from cache, no socket
```

`--no-github` runs git-only: every episode is still produced with exact
before/after states, but carries no PR, issue or review provenance, and says so
in its `provenance_gaps`.

Put the token in the gitignored `.env` at the repository root
(`GITHUB_TOKEN=...`) to avoid re-exporting it; `--token` and `$GH_TOKEN` also
work. It needs read access to public repositories and nothing else.

## `repository_history.json` — stage 0

The repository mined once, before anything synthetic exists. Every commit across
**every ref** (1,734 — 127 of them live only on side branches and are invisible to a
HEAD-only walk), full parent lists, per-file blob identity and stats, branches, tags,
releases, labels, pull requests, issues, reviews, **line-level review comments** and
comment threads.

**It keeps the actual code.** For every changed file: the before blob, the diff, and
the after blob. File contents live in `build/repository_blobs/<sha>`, addressed by git
blob SHA; the manifest references them. So a later stage adapting a real change reads
the exact bytes that change started from, instead of inventing a file from scratch.

That claim is tested rather than asserted: apply a stored patch to its stored
before-state and the result must hash to the recorded after-blob SHA. On a sample of
60, all 60 reproduce exactly.

Lockfiles, VCR cassettes and binaries are skipped — they are 51 MB of this
repository's 124 MB of diff and nothing would ever be adapted from them. The exclusion
pattern and the per-extension counts are both in the output.

`--no-patches` gives a ~16 MB structural record; `--no-blobs` skips the sidecar;
`--no-refresh` runs entirely from cache.

## `engineering_grounding.json`

Two layers in one file, and `analysis.measured_keys` / `analysis.interpreted_keys`
say which is which.

### Measured

Git plus Python static analysis. No model, no network, same bytes on every run
against the same revision — including tie order, which is why every set is
iterated sorted (set iteration order follows the hash seed, and without sorting
equal counts came out differently on every run).

| Key | What it holds |
|---|---|
| `capability_areas` | the join — each area's purpose, extension points, owners, churn, tests and work mix. The object a company spec attaches business goals to |
| `subsystems` | every package with its purpose, LOC, exports, commit volume and authors |
| `interfaces` | abstract bases, protocols, factories and their real subclasses — how the code is meant to be extended |
| `test_architecture` | pytest config, directory split, fixtures, cassettes, coverage of each subsystem *by import* rather than by name |
| `configuration` | Poetry deps split pinned/ranged/optional, extras, Makefile targets, entry points, linters |
| `ci_cd` | every workflow, its triggers, jobs, steps and gates |
| `dependencies` | internal import graph (fan-in, fan-out, cycles, subsystem edges) and external packages |
| `documentation` | README structure, docs inventory, the conventions CONTRIBUTING states — beside how often they are actually followed |
| `change_hotspots` | which files and subsystems change, recency-weighted, plus co-change coupling |
| `contributors` / `roles` / `ownership` | who works where, what archetype that makes them, and each subsystem's bus factor |
| `work_types` | the distribution of feature / bugfix / refactor / test / docs / dependency / CI work, per year and per subsystem |

Two deliberate choices worth knowing:

* **Contributor identities are merged.** Four people in this history commit
  under names that share neither email nor spelling. `repolib.Identities` joins
  them transitively on email, name, and the login inside a
  `NNN+login@users.noreply.github.com` address, with a small explicit alias
  table for the rest. Bots are flagged, not dropped.
* **Hotspots are recency-weighted** with a one-year half-life. Raw counts say
  where the code was *built* — this history is so front-loaded (468 commits in
  November 2024 alone) that without decay the hotspots are just wherever the
  project started.

### Interpreted

The measured layer is evidence; these sections are a reading of it by
`claude-opus-5`, in four stages — eras, capability areas, one call per
contributor, then a synthesis. Roughly $3 and 13 minutes for a cold run, cached
to `cache/llm/` afterwards.

| Key | What it holds |
|---|---|
| `capability_areas` | what the product *does*, named the way the team would name it — "Batch Mode (50%-cost async batch APIs)", not `request_processor`. The measured package-level version is kept as `capability_areas_measured` |
| `eras` | the phases of the project, with boundaries placed from monthly volume, merge-style mix and review rate — so an era marks a change in *how the team worked*, not just what they built |
| `people` | a profile per contributor: arc across the eras, specialties, working style, review behaviour, how it ended. `people.roster.core` names the core team explicitly, with `tiering_rule` beside it |
| `process` | how work started, branched, was reviewed, merged and released — and where stated convention diverges from what the history shows |
| `collaboration` | sub-teams, recurring review relationships, ownership handoffs, how bots were used |
| `timeline` | the dated events, with citations |

Three rules hold throughout:

* **Every claim carries `evidence`** — episode ids, months, paths, contributor
  ids, release tags — and a `confidence`.
* **Anything unprovable lives in a separate `inferred` block.** Seniority, who
  was leading, why someone stopped committing: wanted, but never mixed into a
  measured field.
* **Citations are checked, not trusted.** Every `ep-` id must resolve, every
  path must exist at HEAD or somewhere in the history, every person and era slug
  must be real. The run reports violations and records them in
  `analysis.citation_check`; the last run checked 628 and found none.

## `engineering_episodes.json`

An episode is one coherent unit of engineering work, not one commit:

```
issue -> branch -> commit A -> commit B -> PR opened -> review ->
commit C -> approval -> merge
```

collapses into a single episode carrying all of that provenance: source
commits, PR and issues, before/after repository state, files and symbols
changed, objective, change type, dependencies on other episodes, commit count,
review cycles, changed-file distribution, lines added/deleted, issue→PR and
PR→merge durations, and contributor and reviewer patterns.

**A pull request is the primary anchor.** 101 of this repository's 175 PR
merges sit *off* the first-parent line — they were merged into branches that
landed later — so anchoring on the mainline alone would lose most of the PR
provenance. Commits that never went through a PR (most of the first months) are
instead grouped along the first-parent line by author, a 24-hour window and
touched paths, which keeps each episode's before/after an exact state of the
branch and stops two episodes' diffs from overlapping.

**Repository state is by reference, not by value.** `state.before` and
`state.after` carry commit and tree SHAs, and each changed file carries its
before/after blob SHA, size and language. The clone is local, so any state
reconstructs exactly with `git checkout` — embedding file contents would add
hundreds of megabytes to say the same thing.

**Gaps are recorded, not filled.** A squash-merged PR's branch commits are not
in a plain clone, so such an episode reports `commits_in_clone: 1` alongside
`commits_on_branch: 6` from the API, and names the gap in `provenance_gaps`.
Nothing is inferred to paper over a missing fact, and `stats` totals every gap.

## Files

```
repolib.py       git access, identity merging, change classification,
                 subsystem mapping, Python symbol diffing, a TOML subset reader
github_api.py    cached, rate-limit-aware, resumable REST client
```
