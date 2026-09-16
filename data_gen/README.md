# `data_gen/` — grounding the world in the repository it is built around

> **Start here: [`docs/data-gen-guide.html`](../docs/data-gen-guide.html)**, a one-page
> illustrated guide to this directory: the two chains, what each script writes, the gates that
> fail a run, and what a corpus costs. Open it in a browser. It is also published at
> <https://claude.ai/artifact/MKQi9QEdts8cfp1TBdKJk5>.
>
> The first section below is a short overview that stands on its own. Everything after it is the
> full manual.

## In brief

### What this produces

SWEWorld drops an agent into a company that ships one real service:
[`bespokelabs/curator`](https://github.com/bespokelabsai/curator), vendored as
`vendor/curator-461b4170b966.tar.gz` and served from Gitea inside the world. `data_gen/` writes
that company's **content** — its people, and months of chat, wiki pages, page comments and mail
— and hides task requirements inside it.

A company spec can say what the business wants and what constrains it. It must not also invent
the *technical* shape of that company — the subsystems, the interfaces, the test layout, the CI,
the kinds of work engineers do, who owns what. Invented technical shape produces a world whose
commits, docs and chat describe a codebase that is not the one the agent is looking at.

These scripts read that shape off the repository instead. The people are fiction; every file,
symbol, commit and date they discuss is real.

### Two chains, numbered differently on purpose

The *stages* read the real repository and answer what is true. The *phases* build the synthetic
company on top of that record and answer what gets said. They are separate numbering schemes —
stage 1 is `build_episodes.py`, phase 1 is `phase1_company_grounding.py`, and **they are not
related**.

| Stage | Script | Output | Answers |
|---|---|---|---|
| 0 | `extract_repository_history.py` | `build/repository_history.json` + `build/repository_blobs/` | what the repository *actually contains*, code included |
| 1 | `build_episodes.py` | `build/engineering_episodes.json` | what work *happens* in it |
| 2 | `analyze_repository.py` | `build/engineering_grounding.json` | what the codebase *is*, and how the organization worked |
| — | `make_report.py` | `build/report.html` | all of it, browsable |

| Phase | Script | Output | Answers |
|---|---|---|---|
| 1 | `phase1_company_grounding.py` | `build/company_grounding.json`, `data/identities.yaml`, `data/channels.yaml` | who works here, what they own |
| 2a | `phase2_timeline.py` | `build/timeline.json` | the project state on each day |
| 2b | `phase2_workstreams.py` | `build/workstreams.json`, `build/artifacts.json` | threads of work, and the documents and mail they produce |
| 2c | `phase2_days.py` | `build/days/state/*.json`, `build/days/specs/*.json` | what each day knew, and one conversation spec per channel |
| 3 | `phase3_plant.py` | `build/clues.json`, `build/phase3_plant.md`, `build/phase3_forge.json`, rewrites `days/specs/` | requirements nobody ever states, hidden as scattered remarks |
| 4 | `phase4_simulate.py` | `build/phase4/runs/<run>/` | the specs, finally, as messages people actually sent |

Stage 0 is the only thing that talks to GitHub; stages 1 and 2 read its record. Phase 2a is
arithmetic over that record — no model, no network, and the same bytes every run. Every other
step calls a model, and every answer is cached under `cache/llm/`.

### The whole run, in commands

```bash
python3 data_gen/extract_repository_history.py -v          # needs GITHUB_TOKEN to refresh
python3 data_gen/build_episodes.py -v
data_gen/.venv/bin/python data_gen/analyze_repository.py -v # ~$3, ~13 min cold
python3 data_gen/make_report.py                             # read build/report.html by eye

python3 data_gen/phase1_company_grounding.py
python3 data_gen/phase2_timeline.py
python3 data_gen/phase2_workstreams.py
python3 data_gen/phase2_days.py
python3 data_gen/phase3_plant.py --pick t1,t12,t23 --backend sdk --auth api-key
python3 data_gen/phase4_simulate.py --day-count 3

python3 data_gen/install_corpus.py --run <run>              # the run -> data/
make bake-image TAG=<next>                                  # data/ -> the world image
```

**Order matters**: each step reads the last one's file out of `build/`.

### Before you spend anything

- **`--dry-run`** means something different on each script that takes it — phases 3 and 4,
  `install_corpus.py` and `scripts/check_corpus.py --fix`. On phase 4 it is free. On phase 3 it
  **still makes every model call and still overwrites `build/clues.json` and
  `build/phase3_plant.md`**; only the corpus is spared. See [Running them](#running-them).
- **`--no-enrich`** gives the deterministic half of a step with no model calls. **`--no-refresh`**
  rebuilds from the cache and refuses to open a socket.
- **Slice the days.** `--only` / `--from` / `--until` / `--limit` on phase 2c, `--days` /
  `--day-count` on phase 4. A full phase-4 corpus run is tens of hours; a three-day slice is
  about twenty minutes.
- **Back up `build/clues.json` and `build/days/specs/`** before any phase-3 run, a dry run
  included.
- **Keys**, read from the gitignored `.env` at the repo root or in `data_gen/`: `GITHUB_TOKEN`
  for stage 0, `ANTHROPIC_API_KEY` for every one-shot call, and `CLAUDE_CODE_OAUTH_TOKEN` for
  phase 4's persona turns. Phase 1 also reads `WORLD_DOMAIN` (default `world.local`) and
  `MM_TEAM_NAME` (default `world`) to build addresses.

### Where the corpus is now

`data/` currently holds **9,802 chat messages, 108 wiki pages and 93 mails** (613 `.eml` files, one per mailbox copy). They started as an
install of the `corpus` run, but they are no longer a copy of it: `runs/corpus/` today holds 9,592
messages, 114 pages and 679 mail index rows, and `data/` has since been pruned by
`input/superseded.json` (`install_corpus.py --prune`), hand-reworked where tasks plant into it,
and retimed by `scripts/check_corpus.py --fix`. `install_corpus.py` **replaces** what it owns
rather than merging, so re-installing from the run is not a no-op — it would throw that work
away.

---

# The manual

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

**Order matters**: each stage reads the one before it — the command list is in "In brief"
above.

`analyze_repository.py --no-enrich` runs with the system interpreter and needs no
key at all; `--no-refresh` rebuilds from the cache without calling anything.
All three default to `--repo curator` at the repository root and full history;
`--since` / `--until` / `--rev` narrow it.

`--dry-run` does not mean the same thing on the two phases that take it:

* **Phase 4** spends nothing. It builds every channel, writes `<run>/context.md`, runs the two
  pre-flight gates and stops before the engine starts. It still creates the run directory and
  repoints `latest` at it.
* **Phase 3** is *not* free and *not* read-only. It decomposes, places and proves — every model
  call the real run makes — and then writes `build/clues.json` and `build/phase3_plant.md`
  before it looks at the flag, because the ledger is written first so a report-formatting error
  cannot throw an hour of generation away. What it skips is the corpus: `build/days/specs/`,
  `build/artifacts.json` and `build/phase3_forge.json`. **Back up `clues.json` before any
  phase-3 run, dry or not** — a dry run over a different `--pick` replaces the ledger the corpus
  was actually planted from.

Phase 3 without the flag rewrites *every* file in `build/days/specs/`, not only the days it
plants into. The earlier phases have no dry run — `--no-refresh` rebuilds them from cache
without a socket, and phase 1 takes `--no-emit-world-data` to leave `data/` alone.
`install_corpus.py --dry-run` validates and reports without touching `data/`, and
`scripts/check_corpus.py --fix --dry-run` shows what would be retimed.

Phase 2c is the one to slice rather than re-run whole: `--only DATE [DATE ...]`,
`--from` / `--until`, and `--limit N`. `--attach-only` re-binds artifacts with no model
call at all — but it rewrites phase 2b's `build/artifacts.json` with resolved authors,
so it is not read-only upstream.

**Which key.** The one-shot phases belong on the API key; the CLI backend cold-starts a
session per call and turns minutes into an hour. Only `phase2_workstreams.py`,
`phase2_days.py` and `phase3_plant.py` accept `--backend sdk --auth api-key` — phase 1
and phase 2a have neither flag, and phase 2a makes no model calls at all, so it has no
`--no-refresh` either. Phase 4 splits: the persona turns run on `CLAUDE_CODE_OAUTH_TOKEN`,
and only its one-shots — the director, the landing judge, the clue judge — go over
`ANTHROPIC_API_KEY`. It resolves that split itself, before anything imports the engine,
and nothing afterwards may re-read the key: it has been removed from the environment on
purpose.

Every LLM response is cached in `cache/llm/`, keyed by model, effort, both
prompts and the output schema — and, on the CLI backend, by the model that
actually answers (`answered_by: cli:<cli_model>`). The CLI answers with
`cli_model`, not `model`, and a key that named only the latter let a live phase 4
judged on Sonnet hand every verdict to an `--audit-only` pass on Opus as its own.
A lookup falls back to the old key so earlier answers are not re-bought, but an
entry whose recorded `model` is a different one is skipped rather than reused.
Re-running a phase after a crash costs nothing for the work already done, and
`--no-refresh` will not open a socket.

### Where the GitHub state comes from, and when a token is needed

Review cycles, reviewer identity, issue-open times and the true branch-commit
count of a squash-merged PR exist nowhere in a git clone. They are GitHub
state, and **stage 0 is what fetches them**. Unauthenticated the API allows 60
requests an hour against a repository that needs roughly 1,100; authenticated it
allows 5,000, so a token is not optional for that fetch.

Every response is cached under `cache/github/`, keyed by URL and revalidated
with its ETag (GitHub does not bill a 304 against the rate limit), so the
backfill is paid once and is resumable.

**`build_episodes.py` needs no token.** `--history` defaults to
`build/repository_history.json`, and it reads the GitHub state out of that record. It
only calls the API when the record is missing or you pass `--from-api` — which is the
flag to reach for when you want it to bypass stage 0 deliberately. `--no-refresh`
affects only that API path.

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

The property that makes this worth keeping: a stored patch applied to its stored
before-state hashes to the recorded after-blob SHA. That is the record's design, stated in
the module docstring and in the output's `note` — it is not checked by a test in this
tree, so treat it as an invariant to preserve rather than one something enforces.

Lockfiles, VCR cassettes and binaries are skipped by a noise pattern — nothing would ever
be adapted from them. The pattern, the per-file patch cap and the retention counts are all
under the output's `retention` key: today that reads 3,833 files with a patch, 10
truncated, 248 skipped as noise, and 11.7 MB of retained diff beside 64.6 MB of blobs.

`--no-patches` gives a structural record instead of the full one (the flag's own help says
~15 MB against ~90 MB; the record on disk today, patches included, is 48 MB). `--no-blobs`
skips the sidecar; `--no-refresh` runs entirely from cache.

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

* **Contributor identities are merged.** In this history four non-canonical
  spellings collapse onto two people (`data_gen/aliases.yaml`), under names that
  share neither email nor spelling. `repolib.Identities` joins
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

**A pull request is the primary anchor.** This repository has 461 pull requests, 387
of them merged, and 385 whose merge commit is in the clone — of which **103 sit *off*
the first-parent line**, merged into branches that landed later. Anchoring on the
mainline alone would lose their provenance, so 385 episodes are PR-anchored.
Commits that never went through a PR (most of the first months, 151 episodes) are
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
page, a page comment, a mail message, or a forge issue. Nothing is invented to hold a
clue except by `seat_arc`, which builds the feature's ordinary design discussion, and
`make_room`, which adds one conversation when a remark otherwise has nowhere it
could have been said.

`--sources` decides which of those are allowed, and defaults to `slack,notion,email`.
**`github` is left out until the forge write path exists** — a clue routed to a pull
request nothing posts is a clue that never lands. It becomes available only when
`build/forge_plan.json` exists, written by `scripts/ingest_forge.py --export --plan-out`,
which tells phase 3 the issue and pull-request numbering that will really exist; clues
that land there are reported in `build/phase3_forge.json`.

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
`input/tasks.json` and **defaults to 5** — the first five in file order, which is not a
sample of anything, so name the tasks you mean. Read `build/phase3_plant.md` rather than the JSON — same
content, laid out as the trees, the coverage matrix, and every planted line in
the order an agent reading forward would meet it.

## Phase 4 — the specs become conversations

Phase 4 hands each conversation spec to the `bespoke_user` engine and lets the
people in it talk. Runs are self-contained under `build/phase4/runs/<name>/`,
with `latest` pointing at the newest; `cast.json` deliberately lives one level
up, shared, because it holds each person's voice and redrawing it per run would
make one person sound like two across the corpus.

Every planted clue is then checked against what was actually said. The wording is
the persona's own — that is the point of simulating rather than scripting — but
the information has to be there, and the check is **element by element over the whole
remark**, not against the clause that summarises it: what a persona reliably keeps is the
flat observation, and what they drop is the half that says why anybody minds.

Two failures, two costs. A clue **nobody said** re-runs the channel-day, told what was
missing (`--clue-tries`). A clue said **thinner than it was planted** is repaired where it
stands (`--clue-repairs`): the holder sends the missing part as one more message, seconds
after their own, and only if that fails does the day run again. Re-simulating a day for
half a remark re-rolls every other clue in the room that was already right. Repairs are
named in `clues/<id>.md` under **Repaired** and counted in the index — never silent.

Two gates run before a token is spent: a planned artifact kind nothing will consume stops
the run (`--allow-unconsumed` to override), and clue defects — an empty or question-shaped
`settles`, a required identifier missing from the day's allow-list — are named up front,
because finding them later costs a paid re-run per channel-day. When a conversation comes
out wrong, read `<run>/context.md`: it is everything the model was told, so the fault is
diagnosable there rather than by re-running. `check_grounding.py` is the check after the
fact — is the code quoted in a transcript real as of that day, and did the person consult
the repository before quoting it?

### Phase 4 flags worth knowing

| Flag | What it does, and why it exists |
|---|---|
| `--run NAME` | the run directory under `runs/`. Defaults to a timestamp so runs never mix; reuse a name deliberately to continue a run across invocations. Each invocation rehydrates the wiki and mail stores from what earlier batches wrote to disk — without that, batch two's personas were told "the wiki has no pages yet" about pages the same prompt said were up |
| `--days` / `--day-count` | which days; `--day-count` (default 3) picks a sample |
| `--channels a,b` | re-run only these rooms. Pages and mail on those days are then left alone rather than dropped, and `merge_days` keeps every other room's messages — it used to drop every room's messages on a re-run date, keeping `#pipeline`'s new day and throwing away the rest of the company's |
| `--concurrency N` | how many *people* may talk at once across all conversations (default 6, for a 4-core box). Each participant is a live agent session; too high and the director's own call times out and the engine drops the channel |
| `--auth split\|oauth\|api-key` | default `split`: persona turns on the OAuth token, one-shots on the API key. See "Which key" above |
| `--workspace` | the workspace name in the merged transcript (default `SWEWorld`) |
| `--clue-tries` / `--clue-repairs` | the two failure paths above (defaults 3 and 2; `--clue-repairs 0` disables repair) |
| `--audit-only` | no simulation. Re-judge the run named by `--run` against its own transcript, pages and mail, and **rewrite** its ledgers — for when a ledger covers fewer days than the transcript |
| `--prove-solvable` | no simulation. Re-run phase 3's solvability proof against what the personas actually said in `--run`, falling back to the planned text for days not yet simulated |
| `--no-repo-tool` | withhold the repository tools, to measure what they cost with everything else equal |
| `--allow-unconsumed KINDS` | skip an artifact kind the plan declares but phase 4 cannot deliver, instead of stopping |
| `--dry-run` / `--install` | see "Running them" and "How the corpus reaches `data/`" |

A day that is re-run whole replaces its old self: `Store.drop_day` deletes that date's pages,
comments and mail from disk *and* from the store's memory (`_forget`), because a rehydrated
store would otherwise find the day's old artifacts "already made" and never write them again.

### One clock, and the gate that checks it

The corpus had three clocks and no join: `artifacts.json` dates a page with no time,
`worldapps.Clock` used to stamp it from a private seven-minute counter, and the chat announcing
it ran on the engine's per-turn cursor in a separately simulated channel-day. All 108 pages
landed between 09:14 and 10:38, and 96 chat messages contradicted a page's own `created_at`.
What joins them now:

* **`Clock.set_now()`**, called by the engine before each turn through
  [`patches/sim_engine-pin-app-clock.patch`](patches/README.md), so a tool write is stamped from
  the turn that made it. The cursor is **keyed by persona**, not global — channels run
  concurrently against one clock, and a single cursor stamped a page written at 14:32 as 09:28.
* **`AUTHORING_LAG`** (12 minutes): a write is stamped over the preceding quarter hour, +1 minute
  per further write in the turn, clamped to the day. Stamping on the turn itself put a page and
  the remark announcing it on the same second, which passes every check and no person does.
* **Page status.** `shared_ground` tells each room whether a referenced page is written or still
  planned, `Wiki.written()` overrides the plan from the store, and `HOW_WE_REFERENCE` names the
  tools that settle it (`list_pages`, `find_issue`). Personas used to get a title and an owner
  and guess, announcing planned pages and asking after written ones.
* **Mail replies.** Rooms run on separate timelines, so a 09:50 turn could reply to a 14:48
  mail. `Mail.reply_to_mail` dates such a reply `REPLY_LAG_MIN` (6) minutes after its parent.

Syncing clocks cannot make a persona write a page before announcing it, so
**`scripts/check_corpus.py` is the gate before a bake** (`make check-corpus`; `make bake-image`
runs it first unless `CORPUS_CHECK=0`). Its story checks read files against each other — a page
announced before it exists, a comment older than its page, a reply dated before the mail it
answers (`check_mail_reply_order`), a PR discussed before it was opened. `--fix` retimes pages
and announcement mails to agree with the chat, never past a comment on the page and never past a
mail's own reply; **artifacts may be retimed, chat may only be reworded**, because planted clues
anchor to `"HH:MM author"`. `--plants` checks that no corpus edit has broken a planted task,
comparing chat anchors against `--baseline`, which now defaults to the last commit that changed a
`plant.json` — against `HEAD`, a committed corpus edit was compared with itself and passed. The
root `README.md` covers the gate from the bake side.

`python3 data_gen/test_clock.py` — no network, no key, under a second — is the only test in this
tree, and it covers the clock: the authoring interval, the per-persona key, the seven-minute
fallback for a caller that pins nothing, and that the patched engine's `_pin_app_clock` leaves a
clock without `set_now` alone (that one imports the installed `bespoke_user`).

### How the corpus reaches `data/`

```bash
python3 data_gen/install_corpus.py --run <run> --dry-run
python3 data_gen/install_corpus.py --run <run>
```

`install_corpus.py` is the supported handoff, and it validates rather than just copying:
collections against directories both ways, page frontmatter keys, every `.eml` indexed and
every indexed path present, chat rows carrying channel/author/timestamp. Any problem fails
the run, and nothing is reverted. It **replaces** what it owns — `docs/`, `emails/`,
`messages.jsonl`, `comments.jsonl` — because a merge leaves the previous corpus beside the
new one, indistinguishable, and the ingest would import both. It also drops the duplicates
listed in `input/superseded.json`, which runs made before `worldapps.Store.drop_day` carry
once per pass over a day. `--prune` applies that cleanup to `data/` without installing
anything.

It never touches `data/identities.yaml` or `data/channels.yaml` (phase 1 writes those),
`commits.jsonl` or `history/` (they come from `make history` on the host), or `schemas/`,
which is hand-written contract rather than output.

Phase 4's own `--install` copies the same four things and skips every one of those checks,
so prefer `install_corpus.py`. Ingest with `make bake-image`, which runs the ingest scripts
in order — docs before comments, because comments need the page ids docs leaves behind.

## Files

```
repolib.py         git access, identity merging, change classification, subsystem
                   mapping, Python symbol diffing, a TOML subset reader, and rl.LLM
                   (the disk-cached model client every phase calls)
github_api.py      cached, rate-limit-aware, resumable REST client
worldapps.py       the wiki, mail, forge and repo as tools a persona can reach,
                   writing the ingest schemas directly rather than a private format
phase4_simulate.py the domain half of phase 4: specs and project state -> personas,
                   grounding and channels. Resolves auth, then imports the engine
phase4_run.py      the engine half: the day loop, the clue gate, the repair path,
                   the run directory and its ledgers
phase4_render.py   the engine's transcript in the shape the chat ingest reads
check_grounding.py is the code in a transcript real, and did anybody look first
install_corpus.py  a finished run -> data/, validated and replacing what it owns
test_clock.py      the only test: tool writes stamped from the right turn under
                   concurrent channels. `python3 data_gen/test_clock.py`
patches/           bespoke_user changes, as diffs (see patches/README.md)
input/tasks.json   the 60 hand-written tasks, two hidden requirements each
input/superseded.json  duplicate pages and mails to drop when installing
aliases.yaml       spellings that are one person
```
