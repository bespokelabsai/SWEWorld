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

**There are two chains here, numbered differently on purpose.** The *stages*
above read the real repository and answer what is true. The *phases* below build
the synthetic company on top of that record and answer what gets said. They are
separate numbering schemes — stage 1 is `build_episodes.py`, phase 1 is
`phase1_company_grounding.py`, and they are not related.

| Phase | Script | Output | Answers |
|---|---|---|---|
| 1 | `phase1_company_grounding.py` | `build/company_grounding.json`, `data/identities.yaml`, `data/channels.yaml` | who works here, what they own |
| 2a | `phase2_timeline.py` | `build/timeline.json` | the project state on each day |
| 2b | `phase2_workstreams.py` | `build/workstreams.json`, `build/artifacts.json` | threads of work, and the documents and mail they produce |
| 2c | `phase2_days.py` | `build/days/state/*.json`, `build/days/specs/*.json` | what each day knew, and one conversation spec per channel |
| 3 | `phase3_plant.py` | `build/clues.json`, `build/phase3_plant.md`, rewrites `days/specs/` | requirements nobody ever states, hidden as scattered remarks |
| 4 | `phase4_simulate.py` | `build/phase4/runs/<run>/` | the specs, finally, as messages people actually sent |

Phase 2a is arithmetic over the mined record — no model, no network, and the
same bytes every run. Everything else calls one.

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

None of the *stages* writes `data/`. They produce the ground truth the phases
consume, and only phase 1 and phase 4 write anything the world ingests.

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

Then the phases, in order, each reading the last:

```bash
python3 data_gen/phase1_company_grounding.py
python3 data_gen/phase2_timeline.py
python3 data_gen/phase2_workstreams.py
python3 data_gen/phase2_days.py
python3 data_gen/phase3_plant.py --pick t1,t12,t23,t40 --backend sdk --auth api-key
python3 data_gen/phase4_simulate.py --day-count 3
```

Phases 3 and 4 take `--dry-run`, which does the work and writes nothing. Use it
first on both: phase 3 rewrites *every* file in `build/days/specs/`, not only
the days it plants into, and phase 4 is the one that costs hours. The earlier
phases have no dry run — `--no-refresh` rebuilds them from cache without a
socket, and phase 1 takes `--no-emit-world-data` to leave `data/` alone.

**Which key.** Phases 1-3 are one-shot calls and belong on the API key
(`--backend sdk --auth api-key`); the CLI backend cold-starts a session per call
and turns minutes into an hour. Phase 4 is the exception and splits: the persona
turns run on `CLAUDE_CODE_OAUTH_TOKEN`, and only its one-shots — the director,
the landing judge, the clue judge — go over the API key. It resolves that split
itself, before anything imports the engine.

Every LLM response is cached in `cache/llm/`, keyed by model, effort, both
prompts and the output schema. Re-running a phase after a crash costs nothing
for the work already done, and `--no-refresh` will not open a socket.

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

## `clues.json` — phase 3

The one artifact worth reading before touching phase 3, because its vocabulary
is used unexplained everywhere downstream.

A **task** states a feature openly and hides one or more **requirements** that
appear nowhere in the corpus as a rule. Each requirement breaks into up to five
atomic **facts** — `rule`, `scope`, `exclusions_or_crossover`,
`failure_behavior`, `observability`. A fact nothing carries is a fact the corpus
cannot teach, which makes the task unscoreable, so that fails the run.

Each requirement is decomposed into a tree: **subconclusions** a reader has to
establish, and under each of them the **leaves** — the individual remarks that
imply it. A leaf names the person holding it, which of the facts it `covers`,
and any identifiers that must appear `verbatim`. A **herring** is a decision the
team really made and later reversed, planted strictly *before* the clue that
overturns it, so reading in date order recovers the reversal and reading one
conversation does not.

Placement then gives each leaf a **carrier** — an existing conversation, a wiki
page, a page comment, a mail message. Nothing is invented to hold a clue except
by `seat_arc`, which builds the feature's ordinary design discussion, and
`make_room`, which adds one conversation when a remark otherwise has nowhere it
could have been said.

What has to be true before it plants, and what each check asks:

```
clues (together)  ->  subconclusion  ->  requirement
```

* the clues under a subconclusion **together** reach it, and **no single one**
  closes it alone — a conclusion one remark hands over is a search, not a
  reasoning task
* the subconclusions **together** give the whole requirement
* the requirement is recoverable from the clues end to end, read closed-book,
  best of three, **with the herrings in the room** — that is the corpus an agent
  actually meets
* no leaf restates the requirement's own wording, and the leaves span at least
  two sources, three weeks and two channels

A requirement that fails is re-decomposed and told the specific defect, up to
`--plant-tries`. The run still fails if it never passes: a task nobody can score
that ships looking like one they can is the failure this is all built to
prevent.

`--pick t1,t12` names tasks by id; `--limit N` takes the first N of the 60 in
`input/tasks.json`. Read `build/phase3_plant.md` rather than the JSON — same
content, laid out as the trees, the coverage matrix, and every planted line in
the order an agent reading forward would meet it.

## Phase 4, and how the corpus reaches `data/`

Phase 4 hands each conversation spec to the `bespoke_user` engine and lets the
people in it talk. Runs are self-contained under `build/phase4/runs/<name>/`,
with `latest` pointing at the newest; `cast.json` deliberately lives one level
up, shared, because it holds each person's voice and redrawing it per run would
make one person sound like two across the corpus.

Every planted clue is then checked against what was actually said. The wording is
the persona's own — that is the point of simulating rather than scripting — but
the information has to be there, and a channel-day that dropped one is run again,
told what was missing.

`--install` copies the result into `data/`, which is the only point where any of
this becomes something the world ingests. Phase 1 is the other writer, and owns
`data/identities.yaml` and `data/channels.yaml`.

## Files

```
repolib.py       git access, identity merging, change classification,
                 subsystem mapping, Python symbol diffing, a TOML subset reader
github_api.py    cached, rate-limit-aware, resumable REST client
worldapps.py     the wiki, mail and forge as tools a persona can reach, writing
                 the ingest schemas directly rather than a private format
phase4_render.py the engine's transcript in the shape the chat ingest reads
```
