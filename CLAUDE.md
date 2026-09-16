# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SWEWorld is a self-hosted company "world" for agent tasks — a git server, chat workspace, docs wiki and mail server running as **one container image** with supervisord as PID 1. An agent works inside it as an ordinary engineer: no sudo, and code reaches a running service only through CI.

The company ships one real product: [`bespokelabs/curator`](https://github.com/bespokelabsai/curator), vendored at `vendor/curator-*.tar.gz`, checked out at `curator/` (gitignored), and served from Gitea inside the world.

Two halves that are easy to confuse:

- **`data_gen/`** generates the *content* — the company, its people, and months of chat/docs/mail. Runs on your machine, costs LLM tokens, writes to `data_gen/build/`.
- **`world/` + `scripts/`** build and populate the *container*. `data/` is the handoff between them.

Downstream of both, the tasks an agent is scored on:

- **`task_generator/`** turns a hidden requirement into a Harbor task with several arms (blind, spec, clues, world, located, hosted) and a grader; `task_generator/README.md` is the manual, `docs/task-generator-guide.html` the illustrated overview.
- **`harbor_tasks/`** is its *output* — only `_suites/` (the graders) is hand-maintained. Most built tasks are `FROZEN` in `build_tasks.py`: their plants were hand-fixed in place, so a rebuild needs `--thaw` and undoes that.
- **`failed_tasks/`** holds the retired t-series tasks and the bracket experiment; **`tasks/`** holds working notes, `lessons.md`, and `rollout_analysis/` (reading eval transcripts against answer keys); **`jobs/`** is local trial output.

**`data/` holds a generated corpus** — 9,802 chat messages over 161 days, 108 wiki pages and 93 mails (613 `.eml` files, one per mailbox copy). It was installed from `data_gen/build/phase4/runs/corpus/` by `install_corpus.py` and has since been pruned, planted and `check_corpus --fix`ed, so its counts no longer match the run's. The newest bake is `sweworld:0.4.11` (`:latest`); built tasks still pin older bakes (`WORLD_IMAGE` in `task_generator/build_tasks.py`), so check which one a task runs before reasoning about its corpus. `commits.jsonl` is still a placeholder; real history arrives through `data/history/` (exported from `curator/` by `make history`). `data/schemas/*.md` is the hand-written contract; everything else under `data/` is generated.

## Commands

```bash
make build-image      # build sweworld:dev (services, no content)
make run              # boot and publish every service (:latest bake, else :dev)
make verify           # acceptance checks against the running world
make shell            # shell in as the agent (ubuntu, no sudo)
make stop / logs / clean
make bake-image TAG=0.1.0   # boot base, ingest data/, gate on verify, commit
make push-image TAG=0.1.0 REGISTRY=…   # deliberately separate from bake
make history          # on the HOST: rewrite curator/ history into data/history/
make check-corpus     # on the HOST: does data/ agree with itself? (bake-image runs it first)
```

`make history` is the only target that touches `curator/` — read-only. It, `check-corpus`, and the corpus gate at the start of `bake-image` run on the host; everything else runs in a container. It writes `data/history/` (a git bundle plus the forge record), which `bake-image` later ingests.

**`make run` boots `sweworld:latest` if a bake exists, and falls back to the empty `:dev` base otherwise** (`RUN_IMAGE` in the Makefile, override with `make run RUN_IMAGE=sweworld:0.4.4`). The fallback is by design and is the single most likely thing to confuse someone opening BookStack and finding nothing. Populate with `bake-image`, or ingest into a running container (see `world/README.md` — order matters: comments need pages to exist). `make verify` fails an unbaked world on its corpus-count checks unless `WORLD_EXPECT_CORPUS=0`.

Ports are overridable (`GITEA_PORT`, `MM_PORT`, `BOOKSTACK_PORT`, `ROUNDCUBE_PORT`, `PASS_PORT`, `HTTP_PORT`). Published and container-internal ports are deliberately identical — BookStack redirects to its `APP_URL`, so a mismatch half-works, which is worse than failing.

There is **no test suite**. `make verify` (`world/bin/world-verify`) is the acceptance gate, and it checks the running world, not the code. `data_gen/` has exactly one test, `python3 data_gen/test_clock.py` (no network, under a second), covering the clock join; otherwise verify changes there with phase 4's `--dry-run`. Phase 3's `--dry-run` is **not** free: it makes every model call and overwrites `clues.json` and `phase3_plant.md`.

## The generation pipeline (`data_gen/`)

Two chains, both documented in `data_gen/README.md` (and illustrated in `docs/data-gen-guide.html`).

**Stages 0–2 — read the real repository.** Deterministic where possible; no invented technical shape.

```
extract_repository_history.py → build/repository_history.json + repository_blobs/
build_episodes.py             → build/engineering_episodes.json   (reads stage 0; no token)
analyze_repository.py         → build/engineering_grounding.json
make_report.py                → build/report.html
```

**Phases 1–4 — build the world's content.** Each reads the previous phase's JSON from `data_gen/build/`; run them in order.

| Phase | Script | Writes | Answers |
|---|---|---|---|
| 1 | `phase1_company_grounding.py` | `company_grounding.json`, `data/identities.yaml`, `data/channels.yaml` | who works here, who owns what |
| 2a | `phase2_timeline.py` | `timeline.json` | project state per day (pure arithmetic, no model) |
| 2b | `phase2_workstreams.py` | `workstreams.json`, `artifacts.json` | threads of work, docs and mail they produce |
| 2c | `phase2_days.py` | `days/state/*.json`, `days/specs/*.json` | one conversation spec per channel per day |
| 3 | `phase3_plant.py` | `clues.json`, `phase3_plant.md`, `phase3_forge.json`, rewrites `days/specs/` | hide requirements as scattered clues |
| 4 | `phase4_simulate.py` | `build/phase4/runs/<run>/` | the specs become actual messages |

`repolib.py` is shared infrastructure: `rl.LLM` (a disk-cached Claude client), path constants, `Git`, logging (`rl.ok/warn/info/fail`). Every LLM response is cached in `data_gen/cache/llm/` keyed by model, effort, prompts and schema — plus `answered_by: cli:<model>` on the CLI backend, so an answer from a different CLI model is not served as a hit — re-running costs nothing and `--no-refresh` never opens a socket.

### Phase 3 — the hidden-requirements planter

The conceptual core. A task states a feature openly and hides requirements written down nowhere. Each is decomposed into a MuSR-style tree — **subconclusions** a reader must infer, and **leaves** (individual remarks) that imply them — then placed across months, channels and sources so no single sitting recovers it.

Vocabulary that recurs everywhere downstream:

- **fact / `FACT_FIELDS`** — a requirement's five atomic parts (`rule`, `scope`, `exclusions_or_crossover`, `failure_behavior`, `observability`). A fact nothing carries makes the task unscoreable.
- **leaf / clue** — one remark. `covers` names which facts it carries; `settles` is the third-person clause phase 4 turns into an end state; `verbatim` names identifiers that must appear literally.
- **herring** — a decision the team really made and later reversed, planted *strictly before* the clue that overturns it.
- **carrier / slot** — where a clue lands: an existing conversation spec, wiki page, page comment, or mail message. `place()` never invents a spec; only `seat_arc` and `make_room` do.

The `github` source is the one that crosses back into the runtime: `scripts/ingest_forge.py --export --plan-out` writes `build/forge_plan.json`, the resolved issue and pull-request numbering, so phase 3 can plant a clue in an issue that will really exist. Without that file `github` is not a place a clue can go, which is why `--sources` defaults to `slack,notion,email`.

`input/tasks.json` holds **60** hand-written tasks, each with 2 hidden requirements grounded in real curator APIs. `--limit N` takes the first N; `--pick t1,t12,t23` names specific ones. The `T1`–`T8` codes in that file are **defined nowhere in the repo** — opaque tags, carried through to reports but never interpreted.

Gates, all of which fail the run: every fact carried; `giveaways()` (no leaf restates the requirement's own wording); `spread_problems()` (≥2 sources, ≥3 weeks, ≥2 channels); solvability proved by closed-book reconstruct-then-grade, voted best-of-3, **with the herrings present**; and `not_fragmented()` (no single remark closes its subconclusion alone) plus `tree_adds_up()` (the subconclusions reach the requirement). Failures trigger a bounded re-plant that is told the specific defect.

`strip_previous()` makes re-planting idempotent — it removes prior `planted_arc` specs and pops `planted` lists across the whole specs directory first, so a re-run is a real re-plant rather than a layer on top.

### Phase 4 — simulation

Drives the `bespoke_user` engine (installed separately, `~/.local/lib/python3.10/site-packages/bespoke_user/`). `worldapps.py` gives personas MCP tools that write **the ingest schemas directly** — a page written in conversation lands as `docs/<collection>/<page>.md` with the frontmatter `ingest_docs.py` parses.

Runs live in `build/phase4/runs/<name>/` with `latest` symlinked to the newest. `cast.json` sits at the phase-4 root, **not** per-run — it holds each persona's voice, and redrawing it per run would make one person sound like two across the corpus.

Every planted clue is checked against what was actually said. A clue does not have to be worded as planted — the persona's words are their own — but the *information* must be there, and any identifier must appear (matched normalized, so backticks and casing don't decide it).

The check is **element by element over the whole planted remark**, not against the `settles` clause that summarises it. Free phrasing is not free abridgement: what a persona reliably keeps is the flat observation, and what they drop is the half that says why anybody minds — which is the half that tells a reader there is a requirement here at all. `carried` is then arithmetic over the elements rather than the judge's own summary boolean, because a judge shown the short version first answers "yes, carried" about the short version.

Two failures, two costs. A clue **nobody said** re-runs the channel-day, told what was missing. A clue said **thinner than it was planted** is repaired where it stands (`repair_clue`, `--clue-repairs`): the holder sends the missing part as one more message, seconds after their own, and only if that fails does the day run again. Re-simulating a day for one half-said remark re-rolls every other clue in the room that was already right. Repairs are an edit to the transcript after the fact, so they are named in `clues/<id>.md` under **Repaired** and counted in the index — never silent.

## Auth — the trap worth knowing before you run anything

Persona turns and one-shot calls authenticate **differently**, and both fail silently the wrong way round:

- **Persona agent turns** run over `CLAUDE_CODE_OAUTH_TOKEN` (the CLI/subscription).
- **One-shots** — director, landing judge, clue judge, and all of phase 3 — run over `ANTHROPIC_API_KEY`.

`bespoke_user` decides this once, the moment the package is first touched, and its `__init__` is lazy. `phase4_simulate.resolve_auth()` must therefore run *before* any import that reaches it, and nothing afterwards may re-read `ANTHROPIC_API_KEY` — it has been popped from the environment on purpose. This is why `phase4_run.py` is a separate module imported behind a function call.

Phase 3 is **entirely** one-shot calls, so run it on the API key: `--backend sdk --auth api-key`. The CLI backend cold-starts a session per call (~25s); the API path is seconds.

Keys are read from `.env` at the repo root or in `data_gen/` (see `rl.env_value`).

## Working here

**`data_gen/build/` and `data_gen/cache/` are gitignored** and large (repository blobs alone are 70M). `curator/` is gitignored too — it is a vendored checkout, not project code, and nothing in it should be edited.

**Everything is expensive to regenerate.** Before re-running a phase, know what it overwrites: phase 3 rewrites *every* file in `days/specs/`, not just the days it touches. Back up `clues.json` and `days/specs/` before a re-plant.

**Long runs need care.** A full phase-4 corpus run is tens of hours; a 3-day slice is ~20 minutes. Use phase 4's `--dry-run` (writes the review document, spends nothing) to check wiring first. `<run>/context.md` shows *everything* a model will be told, so a conversation that comes out wrong is diagnosable there rather than by re-running.

**Comment style is load-bearing here.** Comments in this codebase explain *why*, usually by naming the failure that motivated the code — "a live run lost 17 of ~36 turns that way and still looked like it was working". Match that: a comment that restates what the line does adds nothing, and one that names the bug it prevents stops someone reintroducing it.

## Things that cost real debugging time

- **The world moved from Outline to BookStack**, and `data/schemas/` described Outline and its OIDC authorship model for a long time after (`identities.md` and `docs.md` are now brought over; `history.md` covers `data/history/`). The root `.env` still carries the matching fossils (`OUTLINE_*`, `MINIO_*`, `TRAEFIK_*`) which nothing in `world/`, `scripts/` or the Makefile reads. Trust `world/` and the ingest scripts over the schema prose where they disagree.

- **Personas were never told which pages existed.** `shared_ground` dropped the
  `status` phase 2 computes for every referenced doc (`written` / `planned`) and
  handed over a title and an owner, so a persona guessed — announcing planned
  pages and asking after written ones for a fortnight. The status is carried
  through now, `Wiki.written()` overrides it from the store where it is
  attached, and `HOW_WE_REFERENCE` names the tool (`list_pages`, `find_issue`)
  that settles it. Same shape as the `read_repo` rule for code: a rule with no
  way to obey it is not a rule.

- **The corpus had three clocks and no join.** `artifacts.json` dates a page with
  no time; `worldapps.Clock` stamped it from a private +7-minute counter; the
  chat announcing it ran on the engine's per-turn cursor in a separately
  simulated channel-day. 96 messages contradicted a page's own `created_at`.
  `Clock.set_now()` plus `data_gen/patches/sim_engine-pin-app-clock.patch` join
  the tool clock to the turn clock; `scripts/check_corpus.py` is the gate
  (`make check-corpus`, and `bake-image` runs it first) and `--fix` reconciles
  what a clock cannot. **Artifacts may be retimed; chat may only be reworded** —
  287 planted clues anchor by `"HH:MM author"`.

- **`maddy creds create` exits 0 when it fails.** It shipped a mail server with zero accounts while logging `15-mail: OK`. `world/bootstrap/15-mail.sh` asserts the account exists afterwards.
- **Backdating BookStack means four tables**, not one: `entities`, `comments`, `page_revisions`, and `activities`. Correcting only the first two leaves a wiki whose pages read right but whose Recent Activity feed — the dashboard's main content — says "World Admin created page X, 3 minutes ago" for the whole world.
- **Login confusion**: Gitea and Mattermost want the *username* (`worldadmin`), BookStack and Roundcube want the *email* (`worldadmin@world.local`).
- **Offline CI** needs `actions/checkout` seeded into a local `actions` org from `vendor/` (only the `v4` tree), and Node in the image — actions are JavaScript, and without it every workflow dies *after* resolving the action, which reads like a resolution failure and is not.
- **Two databases, and only two**: PostgreSQL for Mattermost, MariaDB for BookStack. Neither has an alternative. Everything else is SQLite. No Redis, no object storage.

## Importing from other agent tools

There is a Gemini CLI config at `~/.gemini`. To bring over anything portable (MCP servers, slash commands, subagents, skills, instructions), reply `/import` to scan and list what's importable, then `/import --yes=<digest>` with the digest the scan prints. If `/import` isn't available on this surface, run `claude import` from a terminal.

---

# Workflow Orchestration

## 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

## 2. Subagent Strategy
- Use subagents liberally to keep the main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until the mistake rate drops
- Review lessons at session start for the relevant project

## 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

## 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

# Task Management
1. Plan First: Write the plan to `tasks/todo.md` with checkable items
2. Verify Plan: Check in before starting implementation
3. Track Progress: Mark items complete as you go
4. Explain Changes: High-level summary at each step
5. Document Results: Add a review section to `tasks/todo.md`
6. Capture Lessons: Update `tasks/lessons.md` after corrections

# Core Principles
- Simplicity First: Make every change as simple as possible. Touch minimal code.
- No Laziness: Find root causes. No temporary fixes. Senior developer standards.
- Minimal Impact: Changes should only touch what's necessary. Avoid introducing bugs.

## Put code in its right home
Code quality matters here. Before you add a function, a constant, or a string of prompt text, read
the target file's docstring and understand what that file is FOR. Then put the new code where it
belongs by intent, not where it is convenient, not where you already have the file open, and not in
the example you happen to be writing.

The files named below live in **`bespoke_user`**, not in this repo — it is installed at
`~/.local/lib/python3.10/site-packages/bespoke_user/`, and phase 4 is a caller of it. Grepping
SWEWorld for `slack_prompts.py` finds nothing; look there instead.

This repo states most of those intents out loud, so there is no guessing:
- `slack_prompts.py` — "EVERY prompt and the code that assembles them". Prompt text goes here.
- `sim_engine.attach_grounding` — "the ONE grounding-application path". Grounding goes here.
- `personas.py` — the model, stdlib only. Nothing that costs a dependency.
- `apps/` — a specific product's shape, which is why it sits outside `bespoke_user/`.
- `examples/` — how a caller USES the library. Not where the library's own behaviour lives.

Two questions that catch a wrong home before it ships:
1. **Would a second caller have to copy this?** If yes it is library code sitting in an example, and
   the copies will drift.
2. **Does the file's own docstring cover what I just added?** If you cannot point at the sentence
   that makes it belong, it does not belong.

Generalise at the seam, not in the caller. A world supplies its DATA (which tools it has, what its
people owe); the library supplies the BEHAVIOUR (what holding tools means, how an obligation is
phrased and enforced).