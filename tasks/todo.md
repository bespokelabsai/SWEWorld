# Todo — make the generator repeatable, and put g1's clues in the world

Plan: ~/.claude/plans/buzzing-shimmying-pelican.md

## Half 2 — the clues into the world

- [x] Back up `clues/` as `clues.pre-inject`
- [x] `prompts/clue_reknit.md` + `clues.reknit()` (in clues.py, beside the other passes) — the holder's turn IS the proven
      sentence; only the turns around it are regenerated
- [x] Guard in code: `anchor()` splices when the rewrite paraphrased (6 of 35 needed it) that does not contain `clue["text"]` verbatim
- [x] `tg/inject.py` — 7 carrier kinds -> ingest-shaped writes into a COPY of the run
- [x] GATE: all 50 remarks + identifiers read back — 0 blocking + verbatim identifiers out of the
      written corpus
- [x] Read back the 8 threads appended to days that already had traffic
- [~] install done (9,791 messages, 5 comments); bake TAG=0.4.2 running
- [ ] `batch-payload-plan-world/` arm, cloned from blind, FROM sweworld:0.4.2
- [x] Teach `build_tasks.py::emit()` the `world` variant (`--world`)
- [ ] Confirm chat + wiki search surface the new remarks in the booted image
- [ ] Measure n=3 against clues 1.00 / blind 0.00

## Half 1 — the pipeline

- [x] `prove --runs 3`, per-fact grid across runs
- [ ] Prove the sampling change on `clues.v4-hosted-0.70` BEFORE building on it
- [x] `finish()` runs `unreversed`, `out_of_order`, `unknit`, `unstated`
- [x] `coverage()` -> `gaps_claimed`; `uncarried()` added and MEASURED USELESS; `unstated()` is the one that fires
- [x] `tg/recipe.py` + `cli.py make [--dry-run|--from|--optional]`
- [ ] `cli.py snap`
- [x] README as the recipe

## Small fixes while there

- [x] `_loop/run.sh` counts every job dir
- [x] CLAUDE.md corrected

## Round two — the corpus reads as people

- [x] `prompts/clue_thread.md` — the exchange exists BECAUSE they were working it out
- [x] Guard inverted: a turn holding the whole remark is now a finding
- [x] `check_carriage` — claim by claim, shown the remark and the thread, `carried`
      computed in code
- [x] `chat_insert` becomes a seeded exchange, not one dropped message
- [x] Page comments become a comment and its replies
- [x] `inject.absent` is claim-level; the answer key renders the exchange
- [x] Recipe + README: `reknit` is the step that makes a plant into a corpus
- [ ] Rewrite all 48 chat/mail exchanges (running, ~96 calls)
- [ ] Run the 2 page comments
- [ ] Re-inject, re-bake 0.4.3, regenerate the answer key
- [ ] Re-measure world n=3 against the 0.50 baseline

## Measured

| arm | n | result |
|---|---|---|
| blind | 1 | 0.00 |
| spec | 2 | 1.00 |
| clues (quoted in the ticket) | 4 | 1.00 |
| world (in the corpus), round one | 3 | 0.80 / 0.10 / 0.60 = **0.50** |

`g1.r1.rule` and `g1.r1.scope` failed 3/3 deterministically on the `PLAN_FILE_NAME`
naming issue, not on retrieval. All five `g1.r2` facts move together, so that is one
engagement variable rather than five failures.

## Review

_(filled in as work lands)_

---

# g4 — run-cache-identity

Area: run cache identity in curator — four layers disagree about what makes two
runs "the same run" (`llm.py:_hash_fingerprint`, `<parse_func_hash>.arrow`,
`MetadataDB`, `CuratorResponse.save/load`). Plan:
`~/.claude/plans/hi-im-waiting-to-reactive-rivest.md`.

Stop point: the hosted **blind** and **spec** arms. Not `clues` ($48).

## Stages

- [x] 0a  `task_generator/README.md` — add `## Running it stage by stage`
- [x] 0b  `cli make run-cache-identity --dry-run`
- [x] 1   `cli new run-cache-identity --brief …`          → brief.md, task.json
- [x] 2   `cli author run-cache-identity`  $3.14, 31 turns  → whole.md, 11 parts, 10 arbitrary
- [ ] 3   `cli build run-cache-identity --role oracle`    → fixtures/oracle.patch
- [x] 4   `cli split`  $1.81, exited 1 — overridden on evidence (0 of 15 hidden values in ticket)
- [x] 5   `cli tests run-cache-identity`  $6.25  → 4/4/1 tests, green on oracle
- [x] 6   `cli build --role naive`  $2.76 + $2.91 rebuild → 962 lines
- [x] 7   `cli build --role spec`   $3.53 + $2.69 rebuild → 1017 lines
- [x] 8   `cli bracket`  **Ships: yes** — pristine 0/9, naive 1/9 (open_feature only), oracle 9/9, spec 9/9
- [x] 9   `cli audit` — SKIPPED by decision (bracket was clean)
- [x] 10  `cli trim` 451->347 words; broke r2.failure_behavior, fixed by stating the refusal's reach
- [x] 11  `cli emit` — tasks.generated.json now ['g1','g2','g3','g4']
- [x] 12  `cli horizon --arms blind,spec` (needed test_open '/c' -> 'cache-dir-c' for unhosted_paths)
- [x] 13  pushed both arms; hosted validation oracle 1 / noop 0 on BOTH
- [x] 14  **VERDICT: spec 1.00 / blind 0.00, open_feature 1.0 on both** (opus 4.7 = biggie-max, meteor, n=1)
- [ ] 15  README kept current with anything g4 hit that it did not predict

Not touching `out/retry-backoff-policy/` — g3 is the user's call.

## Review

- `split` exited 1 predicting `coincidence` on all 8 facts; overridden after checking
  the ticket for all 15 load-bearing hidden values (0 present). Every fact then
  measured `hidden`. `leak.py` false-negatives when a fact's `observability` is
  written as a test expression: the API names used to express the assertion are
  counted as required identifiers, and those are legitimately in the ticket.
- `open_feature` failed on naive AND spec, same assertion. Cause: `test_open` graded
  `RunDirectoryCheck.previous_version`, stated in `whole.md` and in no arm. Fixed by
  amending the shipping description; `hidden_requirements` asserted byte-identical
  across the edit. Recorded in README and lessons.md.

## RESUME HERE (g4, 2026-09-03)

**VERDICT ALREADY BANKED: spec 1.00 / blind 0.00, open_feature 1.0 on both**
(opus 4.7 = biggie-max, agent-type meteor, n=1 each). g4 is a good task.

Clues chain, all green:
- [x] `clues --sources slack`  41 clues, 8 rooms, $10.19  (SLACK ONLY, per request)
- [x] `reorder`   5 remarks moved after the problems they answer
- [x] `settle`    16 rewritten, 4 added -> 45 clues; missing_identifiers: []
- [x] `reverse` + `reorder` again (settle's say19 landed before its own question)
- [x] `reknit`    45 of 45 written, 0 findings
- [ ] `prove --runs 3`   RUNNING
- [ ] `cli horizon run-cache-identity --arms blind,spec,clues`
- [ ] `inject` (optional, in-world arm)

Spend $57.89 local.

Known soft spots, none blocking:
- ~20 advisory `unstated` findings, clustered on g4.r2 (the run_id rule) and
  g4.r1.rule. Predicts a clues arm below the spec arm; `prove`'s per-fact grid in
  clues/proof.md is what says whether it costs anything.
- ONE `absent`: nothing in the corpus mentions `dataset_hash`. Probably harmless —
  it is already one of the five things `_hash_fingerprint` hashes, so a reader
  keeps it from the code, not the corpus.
- Cosmetic: 4 `stock_phrasing` (say22/23/24 all end "had it in my head as"),
  2 `too_wordy` exchanges at ~5x the remark. Fix with `cli replace --only <ids>`
  only if wanted; do NOT run while prove is reading the plant.

TOOLING FIXED THIS SESSION (uncommitted):
- tg/bracket.py    two new open_feature gates (naive must pass it; no longer
                   exempt from the spec-reachability check). Measured against all
                   four tasks' brackets: fires only on g4's bad cut.
- tg/clues.py      prompt() now delegates to steps.prompt() instead of being a
                   second, unfixed copy. It flagged an f-string `{{}}` in a real
                   assertion as an unfilled template hole and killed `settle`.
- task_generator/README.md  stage-by-stage walkthrough, hosted-arms section,
                   open_feature finding, stage-table drift fixes.
- tasks/lessons.md two new lessons.

Horizon: blind 0919a0fe-aa5f-4b9c-a651-1dd939184f4a, spec 5427f01a-a9b4-453d-9b7d-5e21cdd02314,
mini_batch b52ead5c-6e16-4552-ab96-250541fdfba2. `horizon` is at ~/horizon_env/bin
(NOT on PATH). Use --agent-type meteor and --model biggie-max. Read scores with
`horizon rollouts pull <task-id>`, never `evaluations status`.

---

# g5 — response-ledger — **measured, not shipped**

Area: what counts as a recorded response in `responses_*.jsonl`. Kept as evidence
in `task_generator/out/response-ledger/`; the `g5.*` fact keys are baked into its
tests, fixtures and bracket, so the id stays g5. It never emitted — nothing in
`harbor_tasks/` or `tasks.generated.json` refers to it. Total **$17.92**.

**Bracket: Ships no.** `naive: {'failed': 1, 'passed': 8}` — the inverse of the
healthy shape. 7 of 8 facts `coincidence`. Cause in `tasks/lessons.md`: `ships()`
requires `open_feature` to pass on `naive`, so the ticket was obliged to state
everything `test_open` graded, and the hidden pair were left holding a residue the
ticket entails. No re-cut could have fixed it. `split` had exited 1 naming the
leak; overriding it is what the last $10 bought.

**Also found:** `claude -p --json-schema` + opus fails 6/6 with `[reasoning_extraction]`
at every effort level. Sonnet with the schema works; `cli.py split` gained `--model`.

# g6 — model-price-lookup

**Full record: `task_generator/out/model-price-lookup/PROGRESS.md`** — kept there
because this file has two writers and the g5/g6 sections were lost once already to
a concurrent rewrite.

Area: what a token costs. Chosen against g5's lesson — the graded surface is a cost
number, so the ticket can name every symbol and still leave the behaviour
unguessable. Stop point: through `bracket`, then `trim`/`emit`/`horizon`. Not `clues`.

- [x] 0-3  brief / `new` / `author` $2.16 / `build --role oracle` $3.64
- [x] 4  `cli split --model sonnet` $0.67 — **exit 1, 0 of 8** → re-cut BY HAND → **8 of 8**
       The cut was bad, not the area: it hid P2/P5's policies and left every invented
       name in the ticket. Re-cut onto P3's three reason spellings and P5's
       `batch_multiplier`. $0 — the oracle implements all of P1-P9. Old cut: `cuts/cut-2`.
- [x] 5  `cli tests` $4.52 — the free read caught `test_open` requiring
       `reason="unknown_model"` to be accepted, which naive need not spell that way.
       Fixed free. naive later proved it: it wrote `unknown_completion_window`.
- [x] 6  `cli build --role naive` $2.52    - [x] 7  `cli build --role spec` $3.35
- [x] 8  `cli bracket` — **SHIPS: YES.** pristine 8 failed, naive 7 failed / 1 passed
       (`open_feature`), oracle 8/8, spec 8/8. **All 7 facts `hidden`.** Total $20.88.
       Four bracket runs. One paid fix (spec rebuild $4.02 — `_wrap(model=None)`
       TypeError at `cost.py:303`); the rest free: relaxed `test_open`'s rich-markup
       marker position (ticket silent on it); dropped `r1.scope` (the ticket must keep
       curator's `external_model_cost(..., completion_window="*")`, so the wildcard
       default is unhideable); made `discount_flag_name()` polarity-agnostic (spec wrote
       `_prices_are_batch_rates`, the same flag sign-reversed); removed inference.net
       from r2.rule (pricing it needs P7, which only `oracle` is told about, so a correct
       spec degrades it to 0.0 per r1's own failure contract).
- [x] 9   `cli audit` — SKIPPED by decision, as g4 did on a clean bracket
- [x] 10  `cli trim` $1.11 — 472->347 words, 13 assertions dropped; post-trim bracket
       **still Ships: yes**, all 7 `hidden`, spec 8/8. Needed THREE passes:
       `error_max_structured_output_retries` on a different fact each run. Only the
       per-prompt cache made resuming cheap. `trim` should get `split`'s `--model` flag.
- [x] 11  `cli emit` — tasks.generated.json now ['g1','g2','g3','g4','g6']
- [x] 12  `cli horizon --arms blind,spec` — both arms written, both emit gates passed
- [x] 13  **PUSHED to nidhi-test**, mini-batch b52ead5c (same as g1-g4).
       blind 6ff92bf3-3a22-4c72-a89f-2459b57061e7 / spec a745885a-847e-42a4-a583-aa6f6752656d
       `horizon tasks push` prompts for the task name even with MINI_BATCH_ID set —
       `EOF when reading a line` non-interactively. Pipe the name in. Not in the README.
       `horizon tasks list` is broken (`Error fetching tasks: 0`) and nothing lists
       mini-batches; `.horizon/metadata.json` files are the only on-box record.
- [x] 14  **hosted validation: ALL FOUR PASSED** — blind oracle 1.00 / noop 0.00,
       spec oracle 1.00 / noop 0.00. `validate` is async; poll `validate-logs -a <agent>`.
       **g6 COMPLETE. Built for $21.99; push and validation free.**
- [ ] 15  **eval BLOCKED: account budget is $0.00** (total_spend $1040.18). Three evals,
       nine rollouts, all errored, $0 spent, 0 model requests, zero agent turns. Not the
       task — hosted validation passes 1.00/0.00 because it spends no model budget.
       Ruled out: `--machine-type` (control errored without it) and agent type (meteor
       AND typhoon both errored). No error_message is surfaced anywhere — **check
       `horizon whoami` first when rollouts error with zero spend.**
       biggie-max is 403-gated: "run 10+ cipher-omni rollouts below a 0.4 pass rate".
       NB `horizon whoami --json` prints the API key in plaintext.
       (superseded) eval 9eb67aaa-6390-40bc-b715-26cd93eb7b21 — cipher-omni, meteor,
       3 runs x 2 arms, machine `e2-custom-8-16384`. cipher first as the gate.
       `--machine-type` takes ONLY e2-custom-{2-4096,4-8192,8-16384,16-32768}; the CLI
       documents none of them, the 400's ZodError names them. Task ids are ONE
       comma-separated positional, not repeated args.
       Read `rollouts.errored`/`rollouts.total`, never the per-run status column
       (that misreading cost ~$40 on g4). Scores via `rollouts pull`.
- [x] 16  **LOCAL TRIALS: VERDICT spec 1.00 / blind 0.00.** Every one of the 7 facts
       spec 1.0 / blind 0.0 — maximum separation. blind $13.56, spec $11.79.
       **Total g6 $47.34** (authoring $21.99). g4 was $44.70.
       CAVEAT (FIXED): `open_feature` was 1.0 on spec but 0.0 on blind — the ticket said
       what `register_price_with_litellm` WRITES, never what it RETURNS, and across five
       builds it was a coin flip. Added the return-contract clause to `task.json` +
       `ticket.md`; re-`bracket` (still ships, all 7 facts hidden), re-`emit`, re-`build_tasks`,
       re-`horizon --arms blind,spec`, re-pushed — both arms now version 2 under the same
       task ids (`6ff92bf3…`/`a745885a…`), same mini-batch `b52ead5c…`. No paid stage repeated.
       Fixed `tg/report.py`: `trial.rewards()` returns one dict PER TRIAL; two sites
       did `.get` on the list and killed `report` after both paid arms had run.
- [x] 17  Horizon budget restored ($400). Resubmitted cipher-omni eval:
       `1a8f685c-17e9-4466-a2ca-472080e191b2`, 2 tasks x 3 runs, running, 0 errored
       at first poll. `horizon evaluations status 1a8f685c... --json`, then
       `rollouts pull` once `rollouts.total` hits 6.
- [ ] 18  biggie-max (agent-type typhoon, per g4's rollouts) after cipher clears.

---

# fleet — five tasks at once (v1: through the spec/blind proof)

`task_generator/fleet/`, untracked, additive. Drives `cli.py` as a subprocess;
**edits no file outside its own directory**. Cut losses with `rm -rf
task_generator/fleet` + `git checkout task_generator/tasks.generated.json`.

## Scope

- [x] **Phase A** — the cut, `new` → `emit`. ~$19/task.
- [x] **Phase B** — spec and blind proven on Horizon. ~$30/task. **The fleet halts here.**
- [x] **Phase C** — the plant. Written, gated behind `--through C`. Not run in v1.
- [ ] **Phase D** — the in-world arm. Not built; `plan.phase_d()` raises with the seam it plugs into.

Dry run: **$47.42/task, $237.10 for five.**

## Built

- [x] `plan.py` — phase graph, importing `tg.recipe.STAGES` rather than copying it
- [x] `locks.py` — flock on `emit` (tasks.generated.json) and local trials; a 2-slot semaphore on devbox
- [x] `gates.py` — the reader for detectors that already existed and had none
- [x] `judge.py` + `prompts/judge.md` — the between-stage decisions, closed action enum
- [x] `hosted.py` — the `horizon` CLI, every documented edge handled where it is handled
- [x] `state.py` / `worker.py` / `orchestrate.py`
- [x] Five briefs under `fleet/briefs/`, every file:line reference checked against `curator/`

## Verified (spent $0.25, all of it one judge call)

- [x] **Gate calibration** (`orchestrate.py verify`) reproduces **every bracket decision on
      record**: ships g1/g2/g3/g4/g6, refuses g5 on 7 coincidences, and catches every
      archived bad cut — g1 cut-1, g2's three wasted re-cuts, g4's pre-amendment cut with
      the `open_feature`-fails-on-naive message.
- [x] **Five concurrent `new`**: unique ids, no lost state field, every attempt and history row kept.
- [x] **flock** holds across threads *and* across processes.
- [x] **The judge**, given g5's real bracket and real `naive.patch`, answered `author_extend`
      and ruled out `resplit` — the call that cost g2 $6.
- [x] **Cut-losses drill**: `cli.py make model-price-lookup --dry-run` behaves as before;
      `find -newermt` confirms nothing outside `fleet/` was touched.

## Bugs found and fixed while building

1. **`hosted.affordable()` was inverted.** `whoami`'s `budget` is the *remaining*
   balance, not an allowance to subtract `total_spend` from. It reported `-750 left`
   on an account with $344.86 — every task would have parked before spending anything.
2. **Lost update in `state.save()`.** Five threads doing load → mutate → save lost one
   task's `status`. Replaced with `state.update()`, one locked read-modify-write.
   The field most at risk was `hosted[arm].task_id` — a pushed Horizon task whose uuid
   nothing on this box would then record.
3. **Attempt and rewind counters never persisted**, so `MAX_ATTEMPTS` and `MAX_REWINDS`
   could not trip. Now written before the step runs.
4. **`SystemExit` escaped the crash handler.** It is a `BaseException`, and it is what
   most of `tg/` raises for "this went wrong" — a thread would have died with the task
   still reading `running`.

## Open, needs a decision

- **Horizon budget is $344.86.** Phase B for five tasks is ~$150 hosted. Phase C would
  be ~$150 more. Enough for v1 and one retry; not enough for v1 + phase C without a top-up.

## fleet v1 — results (five tasks, one afternoon)

**Every task shipped its bracket with the healthy shape: `naive` passes `open_feature`
and nothing else. Every blind arm measured 0.000 hosted.**

| | area | local $ | hidden facts | blind (cipher, n=3-10) | spec |
|---|---|---|---|---|---|
| g7 | agent-turn-ledger | 23.97 | 8/8 | 0.000, of 0.10 | 0.525 cipher |
| g8 | attachment-payload | 35.68 | 9/9 | 0.000, of 0.00 | 0.148 cipher |
| g9 | example-encoding | 17.98 | 7/7 | **0.000, of 1.0 (opus)** | **1.000 (opus)** |
| g10 | token-capacity-budget | 30.20 | 8/8 | 0.000, of 0.30 | 0.512 cipher |
| g11 | training-step-ledger | 39.18 | 9/9 | 0.000, of 0.70 | 0.765 cipher |

Local total **$147.01**; Horizon spend ~$280 (validations + 100+ rollouts).

**g9 is the complete v1 verdict: spec 1.000 / blind 0.000 with `open_feature` 1.0 on
both arms.** The other four are cut, bracketed, emitted, pushed and hosted-validated
(oracle 1.00 / noop 0.00), awaiting opus rollouts only.

### What the run proved about the method

- **41 of 41 declared facts came back `hidden`** across five independent areas.
- **Both automated repairs fired correctly and unattended**: `author --extend` on g8's
  single coincidence, `amend_ticket` on g11's unreachable `open_feature` — the two
  decisions the README says a person has to make.
- **The gating model cannot measure a spec ceiling.** g6 and g9 both: cipher-omni ~0.51
  on a spec arm that biggie-max scores 1.00. Verdicts are read on biggie-max only.
- **A blind arm is readable on the cheap model only when it builds the open feature
  every time.** g9 yes; g7 (0.10) and g8 (0.00) no. Difficulty for the weak model tracks
  the size of the open feature: pure functions (g9) → one trainer file (g11) → a whole
  new module (g7, g8).

### Bugs the run found, all in fleet code, none in `tg/`

1. `hosted.affordable()` inverted — `whoami.budget` is the remaining balance, not an
   allowance to subtract spend from. Would have parked every task before spending.
2. Lost update in `state.save()` — five threads racing lost a task's `status`; the field
   most at risk was a pushed Horizon `task_id`. Fixed with a locked read-modify-write,
   later extended to a `flock` when a stray `resume` gave one run two processes.
3. Attempt/rewind counters never persisted, so the retry caps could not trip.
4. `SystemExit` escaped the crash handler — and it is what most of `tg/` raises.
5. `split_gate` called `leak.render(rows)` against `render(task, rows)` — crashed the
   pilot at $7.35 on a stage that had already succeeded.
6. `clue_gate` read `unstated` as dicts; it is a list of strings. Would have hit after
   ~$45 of plant in phase C.
7. `_subscores` assumed `grade_result` is an object; it is a JSON string on some
   rollouts. Crashed the verdict gate after the evaluation was paid for.
8. `status()` accepted `{"error": ...}` as a real payload — a bad eval id would have
   spun the poll loop for four hours.

Bugs 5-8 are one lesson: **assuming a field's type instead of reading the artifact.**
`orchestrate.py verify` now calls every gate against every task on disk, which is the
free version of finding them.

### Cost model, measured

| stage | per task |
|---|---|
| phase A (incl. `audit`, first ever measured at ~$5) | ~$28 |
| hosted validation (4 per task) | ~$25 |
| cipher-omni gating, 10 runs x 2 arms | ~$16 |
| biggie-max verdict, **1 run** per arm | ~$6/arm |

`recipe.py` budgets `audit` at $0.00 meaning *unmeasured*; it is ~$5.

### Open

- g7, g8, g10, g11 need 1 biggie-max run per arm to complete. g7 is cheapest (both arms
  already past the 10-rollout gate); g8 needs +7 per arm first.
- Phase C (clues) not started — v1 stops at the spec/blind proof by design.

### fleet v1 — FINAL: all five verdicts pass

| task | verdict | spec best | blind built/n | blind mean when built |
|---|---|---|---|---|
| g7 agent-turn-ledger | PASS | 1.000 (opus) | 2/11 | 0.063 |
| g8 attachment-payload | PASS | 1.000 | 3/12 | 0.000 |
| g9 example-encoding | PASS | 1.000 (opus) | 8/11 | 0.000 |
| g10 token-capacity-budget | PASS | 1.000 (opus, local) | 3/10 | 0.000 |
| g11 training-step-ledger | PASS | 1.000 x6 | 7/10 | 0.000 |

Caveats stated rather than buried: g7's blind rests on 2 feature-building rollouts
and one of them passed `r2.observability` (a coincidence at n=1, hence 0.063).
g8's and g10's rest on 3. Only g9 and g11 have a broad blind base.

**How the verdict is read** (`fleet/gates.verdict_ab`), corrected twice during the run:
- **spec is an EXISTENCE claim** — one rollout at 1.000 proves the requirements are
  sufficient. A mean asks how reliably a given model solves it, which is a fact about
  the model: g11 proved sufficiency six times while its mean of 0.689 sat under any
  sensible floor.
- **blind is CONDITIONAL** — a zero means "hidden" only for a rollout that built the
  open feature. Scored over that subset alone.

### Four task defects found, and where each came from

| task | defect | class |
|---|---|---|
| g8 | one coincidence | repaired unattended by `author --extend` |
| g11 | `open_feature` unreachable — suite graded `gradient_accumulation_steps`, no arm stated it | repaired unattended by `amend_ticket` |
| g9 | `r1.exclusions` unreachable — requirement never said WHERE `FIREWORKS_BYTES_PER_TOKEN` lives | fixed by hand |
| g10 | `r1.exclusions` ambiguous — "limit" meant both the upper bound and the floor | fixed by hand |

Both hand-fixed defects were in `exclusions_or_crossover`, which asks "what this rule
does NOT cover" and so leans on terms defined loosely elsewhere. **Worth a post-`split`
check: every term the exclusions field reuses should have exactly one meaning.**
Both were found by the HOSTED spec arm and were invisible to the local bracket, which
builds `spec` once and happened to read the prose the intended way.

### Harness defects, which cost more than the task defects

1. **Rich display wedges the agent shell.** Curator's trackers start a rich/tqdm live
   display on construction; in a non-TTY container the agent loses its terminal. Three
   of twelve g7 blind rollouts died this way. `CONFTEST` and `GRADER` already set
   `CURATOR_DISABLE_RICH_DISPLAY` — the agent side never inherited it. **Fixed in
   `tg/horizon.py`'s DOCKERFILE template** (the one change made to shared code).
2. **Turn starvation reads as incapacity.** g8's opus rollouts stopped at 9-10 turns
   mid-heredoc; the cipher run that scored 1.000 took 44. Fixed by
   `hosted.MAX_TURNS = 120`; with it, g8 built the feature in 69 turns.
3. **A thin test fixture silently constrains implementations.** g7's fake processor had
   no `.config`, so any build using `_request_processor.config.max_retries` instead of a
   literal died on `AttributeError` before one graded behaviour ran.
4. **`cli.py horizon` rmtrees the arm directory**, deleting pulled `.rollouts/` and any
   hand-added Dockerfile line. Cost three manual restores and one spurious BLOCKED
   verdict. Only `.horizon/metadata.json` is preserved — **`.rollouts/` and
   `.validation/` should be too.**

### Cost, measured
phase A ~$28/task (incl. `audit`, first ever measured at ~$5 — `recipe.py` budgets $0.00
meaning *unmeasured*). Hosted: validation ~$25/task, cipher gating 10x2 ~$16, opus
verdict ~$6/arm at 1 run. Local trial on OAuth: 23 min, free against the subscription.

---

## g1 `world-located` — does the search cost the score, or the inference?

**2026-09-04.** The world arm reports one number for two questions: could the agent
FIND the fifty remarks in nine months of chat, a wiki and a mailbox, and could it work
out what they add up to. `clues` answers the second (1.00) but takes the corpus away,
so nothing measured what the search itself costs. `world-located` removes the search
and nothing else.

- [x] `harbor_tasks/build_located_arm.py` — copies the world arm, rewrites only
      `instruction.md` and `task.toml`, and adds a table of where each remark sits.
      Location only: no quotes, no clue ids (grouped `r1`/`r2`, they would leak that
      there are two requirements), no `kind` (the four herrings stay unmarked), no
      `covers`. `clue_digest.WITHHELD`, one step further.
- [x] Locations read back out of the corpus through `tg.inject.located`, not out of the
      plant — the carrier names the day and the room, the corpus names the minute.
- [x] **The live plant is not the planted plant.** g1's `clues/plant.json` was re-knit
      after `sweworld:0.4.4` was baked and nothing re-injected it: `located()` finds
      none of its fifty remarks. `clues.hedged-v1` matches all fifty, in `data/` and in
      the corpus baked into the image alike. The script picks by which snapshot
      locates, never by name.
- [x] Verified against the booted world, not the files: 44 chat rows (channel, start,
      end, opener) against Mattermost's `posts`; 2 wiki rows against the BookStack API;
      4 mail rows over IMAP as `worldadmin`.
      - 9 of 44 chat windows hold extra interleaved traffic, because a `chat_insert`
        remark sits INSIDE the conversation it answers. One sentence under the table,
        not a caveat on fifty rows.
      - The IMAP check caught a real error: remark 49 is six replies inside a recap
        thread **nikolai** started that morning, not "a thread of six started by emil".
        The corpus alone could not have said so — `located()` anchors on the first turn,
        which is a `Re:` at 13:24.
- [x] Mail is reachable: every persona's thread is ALSO delivered to `worldadmin`, whose
      INBOX holds 107 messages in 0.4.4. `data/emails/` has no worldadmin mailbox at
      all, so a row derived from the corpus alone would name a mailbox the agent has no
      password for.
- [x] Measure. `located-g1-1` scored **1.00** — every one of the ten facts, plus
      `open_feature`, `suite_ok`, `pushed`, `ci_green`, `deployed`. 15.5 min, $8.17.
      Baseline: the world arm at **0.333** over six rollouts (0.8, 0.1, 0.6, 0.0, 0.0,
      0.5); `spec` and `clues` at 1.00.
      The transcript says how: it turned the table into code — a `slice.py` holding the
      44 `(channel, date, start, end)` tuples verbatim — dumped Mattermost once, cut
      those windows out of it, then read the two pages over the BookStack API and the
      four threads over `imaplib`. It searched for nothing.
      **So the world arm's 0.333 was a retrieval score, not a reasoning one.**
      (n=1. The world arm's own spread was 0.0–0.8, so this is a strong signal, not a
      measured mean.)

      python3 harbor_tasks/build_located_arm.py batch-payload-plan
      bash harbor_tasks/_loop/run.sh g1-batch-payload-plan \
        batch-payload-plan-world-located located-g1-1

      `run_cap` in `_loop/state.json` gates this — it was raised 112 → 113 for the first
      rollout and has to be raised again for each one after.

### `data/` is not the world any more

Building g1's map out of `data/` gave three chat exchanges one message short and both
wiki remarks as a single comment. Built out of the corpus baked into `sweworld:0.4.4`
— which every world image carries at `/opt/world-state/data` — all fifty rows match
what the running services return. `data/` still *locates* all fifty; it has just moved
on since the bake, and a map that miscounts is worse than no map.

Hence `--corpus image:<tag>`, which pulls that directory out of the image and caches it
under `harbor_tasks/.located-corpora/` (gitignored). The right root per task:

| task | plant reaches the world by | corpus to read |
|---|---|---|
| g1 | baked into `sweworld:0.4.4` | `--corpus image:sweworld:0.4.4` |
| g2 | ingested at container start by `task-setup.sh` | `--corpus <arm>/environment/plant` |

### The count has to come off the corpus, not the plant

Both wiki remarks in g1 are seven *turns* in the plant. g1 wrote them as ONE comment
thread each — a root plus six replies, which BookStack's API returns nested under
`children`, so the first look at it said "2 comments" and was wrong twice over. g2
writes its three as seven separate comments under a page the plant itself creates.
`landed()` counts records in the corpus and sidesteps the whole question.

### g2 — same treatment, 46 remarks

- [x] `executor-output-cap-world-located`, built from the arm's own `environment/plant`
      (38 chat, 5 mail, 3 wiki-comment threads). `data/` does not hold this plant at
      all — g2's corpus was rewritten on 2026-09-02 and only the delta was kept.
- [x] Verified against a booted `g2located:probe` with the plant ingested: all 38 chat
      rows correct on window and opener, 11 windows carrying extra traffic.
- [x] All five mail carriers are `mail_new`, so g1's reply-anchoring trap does not
      apply here — every "started by" is the thread's real opener.
- [x] Measure. `located-g2-1` scored **0.778** — 7 of 9 facts, missing
      `r1.failure_behavior` and `r1.observability`. $7.35, ~22 min.
      Baseline: world **0.444** (n=1), clues **0.933** (n=5), spec 1.00, blind 0.00.

### What g2 says that g1 could not

g1's whole gap was search: given the locations it recovered every fact. g2's mostly
was — 0.444 → 0.778 — and the rest is not.

Both missed facts were IN the agent's context. Every remark carrying them appears in
the transcript, 6–8 turns of each, verbatim: it read the conversations and built
neither the `MIN_MAX_OUTPUT_BYTES` rejection nor `TRUNCATION_LOG_TEMPLATE`. It worked
g1's way, wider — dumped all ten Mattermost channels in full, then sliced the named
windows out of the dump, plus two BookStack pages and six imaplib calls.

`r1.observability` is hard for everyone: 3 of 5 `clues` rollouts miss it too, with the
remarks quoted in the prompt. `r1.failure_behavior` is the interesting one — `clues`
gets it 5/5 and `located` dropped it. The difference between the arms there is
DILUTION: `clues` reads 46 short remarks, `located` reads 46 conversations in full,
which is thousands of lines of chat with the load-bearing sentence somewhere in it.

**Worth a second g2 rollout** to tell that apart from noise on one fact.

### The re-run, and what g2 actually supports

The arity fix landed and the arms were re-run (`clues` 5/5 and `spec` passed that fact
already, so only these two could move):

| rollout | grader | score | missed |
|---|---|---|---|
| `world-g2-1` | old | 0.444 | r1.rule, r1.failure_behavior, r1.observability, r2.rule, r2.observability |
| `world-g2-2` | fixed | **0.778** | r1.failure_behavior, r1.observability |
| `located-g2-1` | old | 0.778 | r1.failure_behavior *(the arity defect)*, r1.observability |
| `located-g2-2` | fixed | 0.778 | r1.observability, r2.exclusions_or_crossover |

world 0.611 (n=2), located 0.778 (n=2) — **overlapping**. The world arm's second
rollout matched located outright, so **g2 does not separate the two arms at this
sample size**. The g1 result (0.333 over six vs 1.00) is the one that carries weight
so far.

Neither re-run miss is a grader defect. `world-g2-2` never added the up-front
`@field_validator`, so its failure_behavior is a real half-miss ("DID NOT RAISE
ValidationError") — and `world-g2-1`'s was `'OutputCapError' object has no attribute
'max_bytes'`, i.e. it never stored the value at all, so its 0.444 stands unchanged
under the fixed grader. `located-g2-2` invented an extra public field `output_capped`
on `CodeExecutionOutput`, and that fact's own requirement states the exact field set.

**`r1.observability` has never been recovered in a world arm** — 0 for 4 here, and 3
of 5 `clues` rollouts miss it with every remark quoted in the prompt. It is the
task's ceiling-limiter, not a retrieval problem.

- [ ] If g2 is worth separating, it needs 3-4 more rollouts per arm; the per-fact
      noise is ~1 fact per run, which is 0.111 on a 9-fact task.

### located-g2-3 (not launched from this session)

**0.889** — 8 of 9, missing only `r1.failure_behavior`, and for the same real reason
`world-g2-2` missed it: the request-time rejection is there, the up-front
`CodeExecutionBackendConfig` validator is not. The corpus settles that one too
(emil: "the config should have refused it when i built the executor"), so it is a
miss, not an artifact.

| arm | g2 rollouts | mean |
|---|---|---|
| `world` | 0.444, 0.778 | 0.611 (n=2) |
| `world-located` | 0.778, 0.778, 0.889 | **0.815** (n=3) |
| `clues` | 5 runs | 0.933 |
| `spec` | 1 run | 1.00 |

Located is trending above world and below clues, which is the shape g1 predicted —
but the ranges still touch (world's 0.778 sits inside located's spread), so this is
a trend, not a separation.

**Correction to the note above: `r1.observability` HAS now been recovered in a world
arm** — located-g2-3 got it. It is 1 for 5 rather than 0 for 4, so it is very hard
rather than unreachable.

`r1.failure_behavior` is a compound fact and rollouts drop different halves of it:
never storing `.max_bytes` (world-g2-1), a constructor arity the corpus never stated
(located-g2-1, since fixed), and no config-construction validator (world-g2-2,
located-g2-3). Worth watching — a fact with four independent parts scores like one
fact and fails like four.
