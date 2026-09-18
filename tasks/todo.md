# TB3 rubric clean-up (2026-09-17): g11 first, then g1–g10

Plan: ~/.claude/plans/so-i-ran-a-gleaming-wombat.md. Rubric verdicts and criterion text are
readable from Horizon: `horizon rubrics status <task> -v`, `GET /api/rubrics/<id>`.

## Step 1 — g11 world-hosted
- [x] binary `reward` (all measured hidden facts AND protected files unchanged); hidden_mean → report.json
- [x] ctrf.json written by score.py from the judge's junit + protected-file checks
- [x] protected_files in task.json; run_suites.check_protected byte-compares vs pristine (root)
- [x] v11 rollouts checked: no trial touched a protected file (diffstat hit was curator history)
- [x] task.toml: TB3 metadata fields, no invented keys, allow_internet, agent 7200s
- [x] tests/ = harness + own suite only
- [x] solution/oracle.patch out of the heredoc (identical to fixtures/oracle.patch; applies to Gitea main)
- [x] setup.sh deletes /opt/task-plant after a successful ingest
- [x] generator (build_tasks.py, tasks.generated.json g11 entry) carries all of the above
- [ ] 1b: republish world image under a neutral name, byte-identical — BLOCKED: nidhi@ gets 403 on apex-485220 even after login; needs a Horizon admin `gcrane cp` or AR Reader
- [x] rubric round 1 on v12: 8/12 pass. Fixed for v13: category → ML; verification text now lists every tolerance exactly (abs 1e-12 floor dominates on rates); hidden_requirements.md → .horizon-meta/ (prepass.py + refresh_answer_key.py read it there); empty comments.jsonl dropped (generator skips zero-byte plant files)
- [x] anti-cheat plant-in-layer: Nidhi — task design, do not change delivery (runtime rm stays)
- [x] push v13 — rubric round 2: Category, No extraneous, Task toml pass; Verification explanation + Typos fail
- [x] v14: typos (`tasks.json`→`/tests/task.json` in score.py, `rewards.json`→`reward.json` in test.sh/TEST_SH, stale `suite_error=1`); verification explanation lists every tolerance + every inequality and reports a MEASURED validation: 4 alternative correct implementations (Fraction/fsum, reordered/fmean, interpolate/reversed-sum) 10/10 through real probe+judge, 2 wrong controls fail the right facts; spread ≤2.7e-20 on rates, ≤8.9e-16 on losses. Task renamed training-step-ledger (UI) + task.toml/metadata.json
- [x] v15: Verifier execution isolation was REAL — judge inherited the worker's HOME, root python ran worker-planted usercustomize.py as uid 0 (reproduced). Fix: judge `python3 -I` + root-owned HOME/TMPDIR (all split suites; g1/g7 sibling import verified). Verifiable: reward now also requires open_feature (all 10 v11 rollouts passed it → no outcome change)
- [x] step 2 (2026-09-17): nine agents converted g1–g10 world-hosted arms, pushed + renamed via PATCH /api/tasks/<uuid> {"field":"name","value":…}: g1 v18 batch-payload-plan, g2 v13 executor-output-cap, g3 v10 retry-backoff-policy, g4 v6 run-cache-identity (uuid 1e913041, not 6dd38e43), g6 v9 model-price-lookup, g7 v6 agent-turn-ledger, g8 v10 attachment-payload, g9 v9 example-encoding, g10 v9 token-capacity-budget. open_feature gate flips 0 everywhere. Metadata + protected_files merged into tasks.generated.json; all ten arms verified equal to the generator.
- [ ] OPEN (owner decisions): cpus 2 on g2/g3/g4/g6/g10 (world starved at 2 on g11); stricter open-feature judge checks for Verifiable / Do-not-modify / Test-instruction gaps (g1,g3,g4,g6,g8,g10); g2 worker-observation forgery (needs g1-v17-style seeded judge); stale "weight 0" comments in _suites/g4 suite; g11 solve.sh stale reward comment (generator fixed; push after the v15 eval)
- [x] round 2+3 (2026-09-17, later): all eight re-pushed — g1 v21, g2 v14, g3 v13, g4 v8, g7 v7, g8 v11, g9 v11, g10 v11. g6 v9 and g11 v15 deliberately untouched (clean sweeps; a push would restale them).
      Rubric state: g2 28/28 clean; g6 28/28; g11 33/34 (Near miss by design); g1 closed its twice-failed Do-not-modify (helper-extraction allowed, renamed-locals rewrite rejected, bands widened 2-11 + 20k-seed sweep); g3 11/13 on a local judge pass; g4 Verifiable closed by vendoring a stdlib XXH64 (verified 474/474 vs xxhash) and recomputing; g9 closed the boundary-trick gap and REFUSED the determinism trade (seed stays; forgery 0/8 fresh); g10 deleted its README (closed two rubrics) and compared handler+queue vs pristine, re-running all 17 controls.
      Open by design everywhere: Environment hygiene, Instruction concision, Outcome verified, Separate verifier, Test instruction alignment (hidden half), Task proposal. Plus per-task: Anti cheat's plant layer (8 tasks), Structured data schema (6), Difficult (9).
- [x] SHARED BUG found by g4's local judge: run_suites.map_hosts imported HOSTS from fakeapi.py, which split-suite arms stopped shipping in round 1 -> every run recorded hosts_error and pinned NO provider host while allow_internet=true. Inlined PROVIDER_HOSTS in _suites/run_suites.py (verified map_hosts pins all three in the world image) and re-synced every arm LOCALLY; pushed versions still carry the old import until each task's next push.
- [ ] OWNER DECISIONS: hosted validate on g3 before buying reviews (its new probe drives curator's real submission loop and has never run hosted; a failure there = oracle <1.0 = 409 gate); g4's capture gap (`from xxhash import xxh64 as _h` records nothing -> fails a CORRECT submission); g7's fingerprint-consumption bypass (~8 judge lines); re-runs ready: g1 8, g3 7, g9 5, g10 9, g4 5 (held)
- [ ] step 2 leftovers: reuse the tolerance-validation harness (probe+judge on formula variants in sweworld:repo-only-dev) for each task's verification_explanation
- [x] push g11 world-hosted v12 (22 files); Nidhi runs pre-eval

## Step 2 — g1–g10 (after g11 v12 is confirmed)
- [ ] per-task toml_metadata + protected_files, propagate tests/solution/setup/toml, push
- [ ] look into g11 test_r1 `mock://` + tokens_processed expectations (report only)
- [ ] task-name rename (ask: new Horizon task?)

---

# g11: close the score-forgery without changing the task

## Problem
Grading pytest imports the agent's pushed code in the same process that writes the
report score.py reads. Even after the privilege drop (uncommitted, in the working
tree), an `atexit` hook in `bespokelabs/curator/__init__.py` forges junit.xml →
`reward` 1.0 from a pristine tree. A uid cannot fix this (lessons.md 2026-09-09).
Only fix: the process that IMPORTS agent code must stop being the process that
DECIDES pass/fail.

## Invariant (must not change) — captured baseline
- pristine: 10 fail (reward 0.0)
- naive: only `g11.open_feature` passes (reward 0.0)
- oracle: 10 pass (reward 1.0)
- every hidden fact verdict = `hidden`; Ships: yes
- Baseline JSON: scratchpad/baseline_g11.json

## Design: worker (probe) + judge, both driven by run_suites
- WORKER: runs as `nobody`, imports the submission, executes a fixed ordered list
  of probes; each returns a JSON-serializable observation (or an error marker).
  Its atexit hooks / lingering forks are killed with the process group and can
  only touch files it owns — never the judge's output.
- JUDGE: runs as root, NEVER imports the submission. Reads the worker's
  observations (harvested O_NOFOLLOW, size-capped, like junit today) and the
  cloned source text, runs the assertions currently in test_*.py, emits
  {fact_key: passed|failed}. Source checks (ast "no import time/random",
  TYPE_CHECKING) read the clone's text directly.
- score.py reads hidden-fact outcomes from the judge (unforgeable), not junit.
- Floats cross JSON exactly (repr round-trip), so pytest.approx(rel=1e-12) holds.

## Steps
- [x] Capture baseline verdicts (pristine/naive/oracle)
- [ ] Build a forge fixture (sitecustomize + atexit junit-rewrite) → prove it
      scores reward 1.0 under the current grader, 0.0 under the new one
- [ ] Worker/judge scaffold + local invariant harness (mirrors the bracket)
- [ ] r1 (5 facts) probe+judge → bracket matches baseline on all trees
- [ ] r2 (4 facts) probe+judge → bracket matches
- [ ] open_feature probe+judge → bracket matches
- [ ] Wire run_suites.py + score.py + test.sh; keep score.py key semantics
- [ ] Full local bracket == baseline, forge == 0.0
- [ ] Propagate to all 7 g11 arms (shared _suites); note hosted revalidation

## Verify
- Local: `scratchpad/baseline_g11.py` re-run through the new path == baseline.
- Forge fixture: reward 0.0 after, 1.0 before.
- Hosted: oracle 1.00 / noop 0.00 validation, then eval — separate round trip.

## Steps — DONE
- [x] Capture baseline verdicts (pristine/naive/oracle)
- [x] Forge fixture (sitecustomize + atexit junit-rewrite): 1.0 under old grader, 0.0 under new
- [x] Worker/judge scaffold + local invariant harness (mirrors the bracket)
- [x] r1, r2, open_feature probe+judge → bracket matches baseline on all trees
- [x] Wire run_suites.py (opt-in branch; score.py + test.sh untouched)
- [x] Propagate probe.py/judge.py/run_suites.py to all 7 g11 arms (verified in sync)

## Review
**What shipped** (only `_suites/` + g11 arms touched; every other task byte-identical):
- `_suites/g11_training_step_ledger/probe.py` — worker; runs as nobody, imports the
  submission, writes observations (values, never verdicts) to observations.json.
- `_suites/g11_training_step_ledger/judge.py` — judge; root, stdlib only, never imports
  the submission. Applies the suite's assertions to the observations + the cloned source,
  writes junit.xml with the SAME classname/name as the old tests so score.fold is unchanged.
- `_suites/run_suites.py` — `spawn()` (kills the process group after wait, so a forged
  atexit daemon can't outlive the worker) + `run_split()` + an opt-in branch that fires
  only when the suite ships probe.py+judge.py. Purely additive.
- test_*.py, score.py, test.sh, conftest.py, harness.py: UNCHANGED. test_*.py kept for the
  fact↔test bijection and as the assertions' source of truth.

**Proven locally (devbox):**
- Invariance: pristine 0/10, naive open_feature=1 rest 0, oracle 10/10 — identical to the
  pytest baseline, every hidden fact still `hidden`, Ships: yes.
- Closure: the forge tree scores 1.0 under the old pytest grader and 0.0 under the split.

**Why it holds:** the process that imports agent code (worker) no longer writes the report;
the judge decides pass/fail in a process that never imports it, writing junit straight to
root-owned /logs. A forged junit/atexit has nothing to rewrite there.

**NOT done (handed off, per the plan):** hosted validate (oracle 1.00 / noop 0.00) + gating
round trip on the g11 arms. That is the remaining proof and spends hosted budget.

**Residual, worth stating as gains not changes:** the worker still runs agent code as nobody
(disposable, killpg'd, writes nothing score.py reads); overfitting to the exact probe vectors
is still possible (the accepted per-test risk, same as any suite) — universal forgery is what
is closed. Scratchpad harnesses: baseline_g11.py, harness_new.py, demo_forge.py.

---

# The split left one channel open: observations-forge (2026-09-10)

The review above tested the JUNIT forge (which the judge overwrites) and concluded
"universal forgery is closed". It is not, with test.sh unchanged. The judge holds the
expected VALUES as literals and lives in /tests, which test.sh opens `g+rX` to the
worker's group. So the worker (nobody, running agent code) can READ judge.py, and an
atexit payload can write `observations.json` with exactly the values the judge checks
for — a forged PASS through the observations channel, which the junit-only forge fixture
never exercised.

**Reproduced on a g10 world twin, end-to-end through the real test.sh + Gitea clone:**
a pristine tree + an atexit payload that reads judge.py and writes matching observations
scored **reward 1.0** with the unchanged test.sh.

**Fix (one line in `build_tasks.TEST_SH`):** after the `g+rX` open, `find /tests -name
judge.py -exec chmod 0600` — lock every judge to root. The worker never needs judge.py
(only root runs it), so this costs nothing and removes the answer key from the process
that runs agent code. Non-split tasks ship no judge.py, so the find matches nothing.

**Proven, both tasks, through test.sh:**
- oracle 1.0, noop 0.0, junit-forge 0.0, obs-forge 0.0 (PermissionError reading judge.py).
- Control: with the lock removed, obs-forge is back to 1.0 — the lock is load-bearing.

## g10 got the same split (2026-09-10)
Built `_suites/g10_token_capacity_budget/probe.py` + `judge.py` to match g11's shape
(judge writes junit with the current node ids; open + r1 + r2 all ported). The judge's
expected values were generated from the oracle observations, then cross-checked against
the original test_*.py inline constants — all matched. Propagated tests/ (only) to all 7
g10 arms and re-propagated all 7 g11 arms so they carry the locked test.sh; every arm's
probe.py/judge.py/test.sh verified byte-identical to _suites / build_tasks.TEST_SH.

Scratchpad: driver.sh (push-to-Gitea + test.sh), payload_junit.py, payload_obs.py.

---

# The judge.py lock was ALSO insufficient: test_r*.py leaks the same answers (2026-09-10)

The section above claimed locking judge.py closed the obs-forge. It did NOT, and QC
caught it. The expected r1/r2 values live in judge.py AND — identically — in the
sibling `test_r1.py`/`test_r2.py`, which the suite keeps as its source of truth and
which test.sh left group-readable (only judge.py was re-locked). So the worker just
reads `test_r1.py` instead of judge.py and forges matching observations. My earlier
"proof" missed this because the forge fixture only read judge.py, never the test
files that carry the same constants.

**Why the lock is nonetheless the right shape (not "judge recomputes"):** the worker
runs agent code, so any value it produces is forgeable; QC's "recompute from source"
can't get a *behavioral* value (what free_capacity returns) from AST. The only defense
is keeping the expected values unreadable by the worker — which means locking EVERY
file that carries them, not just one.

**Complete fix (`build_tasks.TEST_SH`):** for each split suite (a dir shipping judge.py),
`chmod 0600` judge.py AND that dir's test_r*.py. probe.py + test_open.py stay readable
(the worker imports them; test_open holds only the weight-0 open-feature constants).
Scoped to split suites so non-split tasks — which run pytest over their own test_r*.py
as the same nobody uid — are untouched. Invariant to preserve: reward-bearing answers
live ONLY in test_r*.py/judge.py, never in test_open.py or probe.py.

**Re-proven on a g10 twin with the REALISTIC forge (payload reads test_r1.py), both tasks:**
- g10: oracle 1.0, noop 0.0, obs-forge(read test_r1) 0.0 (PermissionError).
- g11: oracle 1.0, noop 0.0, obs-forge(read test_r1) 0.0 (PermissionError).
- Control (old judge-only lock, same forge): 1.0 — reproduces QC exactly.
Re-propagated the corrected test.sh to all 14 g10+g11 arms.

**Hosted status:** g10 v6 / g11 v8 were pushed with the INCOMPLETE (judge-only) lock and
are still forgeable — must be re-pushed with the corrected test.sh. NOT re-pushed yet.
Lesson: a forgery fixture must read EVERY file that carries the answer (test_r*.py, not
just judge.py), or it proves nothing.

---

# Duplicates out of the corpus (2026-09-10)

Days were simulated more than once across phase-4 processes; chat for a re-run day
was replaced (`merge_days`), mail and pages were not. Separately, personas repeated
themselves in chat.

- [x] Generator: `worldapps.Store.drop_day(date)` (Wiki: pages + comments, Mail: every
      copy + index lines); mail numbering continues from disk. Called per day in
      `phase4_run._run`, not under `--channels`. 13/13 scratch checks.
- [x] `data_gen/input/superseded.json`: 14 mails, 6 pages, 95 chat lines, each naming
      the copy it gives way to. `install_corpus.py` applies it after the copy (only
      while the kept copy is present; never a page with comments or a chat root with
      replies), fails on one page name in two books, and `--prune` applies it to
      `data/` in place. A re-install would lose g1's hand-reworked mail.
- [x] Chat repeats: 157 same-author look-alike clusters judged by 6 agents with
      context; 107 proposed drops, 21 overridden where the author's own next line
      leans on the dropped one, 6 dependent follow-up lines added -> 92, plus 3
      exact repeats. No dropped line carries any task's planted text.
- [x] Pruned `data/`: mail 763 -> 613 files, pages 114 -> 108, chat 9897 -> 9802.
      Fresh installs from `corpus` and `latest-g1` bring none of it back.
- [x] Rebaked as `sweworld:0.4.9` (local, `latest` moved): Aug 17 `sweworld:dev` — the
      base 0.4.8 sits on — + pruned `data/` + both Roundcube fixes applied in the bake
      container (a from-scratch base rebuild did not fit ~6GB free disk; the
      Dockerfile carries the fixes for next time). world-verify 33/33: 108 pages,
      9814 chat (0.4.8: 9909, minus exactly 95), 706 mail (870), 736 issues/PRs,
      commits/branches/tags 1608/38/28 unchanged. Roundcube scripts served as JS;
      THREAD reads 69 threads / 93 msgs. Browsing container now on 0.4.9.
      Every task image tag (repo-only-dev, 0.3.1-forge, 0.4.4, 0.4.8, 0.4.1, 0.4.6,
      dev) verified unchanged by image id; devbox untouched; nothing pushed.
- [ ] Publish 0.4.9 + repin `WORLD_REGISTRY` for g2-g13 (~7GB push, hosted round
      trip) — not approved. g1 stays on 0.4.8 (FROZEN).
- Left on purpose: ~50 look-alike chat pairs that are answered, depended on, or
  contradict rather than repeat; two v0.1.9.post1 chat links now point at a dropped
  page.
- Not fixed, root causes: persona wiki/inbox tools only see the current process's
  writes (`Wiki.find`, `list_pages`, `Mail.check_inbox`), so earlier pages read as
  missing (149 chat lines); cross-room openers and re-landing live in `bespoke_user`.

# g1-g11 lumen rollout analysis (2026-09-11)
Plan: ~/.claude/plans/can-you-look-at-inherited-russell.md
- [x] pull target versions + full ctrf traces to scratchpad (101 rollouts; extracted_score = mean of ALL subscores, report `reward`)
- [x] prepass: answer-key remark tables, transcript turn parse, hit pointers (reproduces g7 l2 = runs 1,4,6,7)
- [x] g7 wave (10 readers; Opus refused 8/10 on [reasoning_extraction], rerun on Sonnet) -> matches g7-g11-eval-audit.md on every hand-verified count -> CHECKPOINT with Nidhi (approved)
- [x] remaining 9 tasks (Sonnet readers; shared prompt scratchpad/reader_instructions.md; 20-concurrent cap)
- [x] aggregate + cross-task synthesis -> tasks/g1-g11-lumen-rollout-analysis.md

## Review (2026-09-11)
- 92 rollouts read against the answer key (91 scored + g2's execution failure); 92 reader JSONs,
  all validated (one normalized: g6 run9 had clue rows under 'clues').
- Every reader claim about the ticket, "only carrier", or cause that fed a finding was checked by
  hand; overrules and confirmations are in scratchpad readers/corrections.md and applied as named
  OVERRIDES / NEVER_SHIPPED in aggregate.py (never by editing a reader's JSON).
- Output: tasks/g1-g11-lumen-rollout-analysis.md — findings at a glance, per-task sections, and a
  defect register (G7-A, G3-A, G3-B, G8-A, G11-H + single-home names + env faults). Nothing fixed.
- Opus 5 readers were refused by the [reasoning_extraction] safeguard (8/10, twice); readers ran
  on Sonnet at the user's direction.

## Done: swapped in the g7 rerun and the new g9 rollouts (2026-09-11)
- [x] when told the evals are done: find the new eval ids (HorizonClient().tasks.rollouts for g7 035a0274, g9 149947c5)
- [x] (tooling: tasks/rollout_analysis/, see its README) pull + full records, prepass, one Sonnet reader per rollout (tasks/rollout_analysis/reader_instructions.md), aggregate, synth
- [x] REPLACE the g7 and g9 sections of tasks/g1-g11-lumen-rollout-analysis.md (drop the old eval 94bf8242 / fffbd350 results entirely),
      move g9 into the pooled rates if it has ~10 scored runs, then refresh the summary, ranking, register and pooled numbers
- [x] re-check G7-A (the nikolai fix) against the new g7 rollouts if the rerun is on the pushed fix
- Result: g7 v5 (8deffce4) and g9 v8 (3b0b259f), 20 new readers. G7-A verified fixed (0 points, was 8);
  new G9-H (herring whose only reversal is an unindexed wiki comment: 6/10 captured); G7-D upgraded
  to a grader defect (arg-order clause dropped in rendering). Old verdicts in readers/_superseded/.

## Done: g9 withdrawn from the defects, g3 fixed in the repo (2026-09-11)
- [x] G9-H removed from the report everywhere (user: g9 is fine; its herring works as designed)
- [x] G3-A corpus: konrad 14:12 "fail it out on the first" rewritten in all 8 carriers (3 world-arm
      plants, answer key, both READMEs, plant-data, plant.json incl. its `pieces` record)
- [x] G3-A′ grader: test_r1 observability drives a real finish_reason="length" response through the
      request path; G3-B: test_r2 knob check is an AST read-check (docstrings no longer count)
- [x] verified locally: oracle 10/10 old+new; run-3/10 and run-8 mutants 10/10 old -> fail new on
      r1.observability; run-6 docstring mutant fails old -> passes new; pristine fails all
- [x] tests copied into all six g3 arms; report + shareable page updated; port session told to
      mirror both into probe.py/judge.py
- [x] mirrored into the graded path myself (probe_support.drive_one_response, probe.py, judge.py);
      split-path verified (same matrix; spec/naive unchanged at 10/10 and 1/10); arms tests/ copied
- [x] pushed g3 world-hosted v9; hosted validate: oracle 1.0 (16/16), noop 0 on every fact (0.0625 = suite_ok)
- [ ] opus eval on v9 (user's call)

## Done: G7-D fixed in the repo, not pushed (2026-09-11)
- [x] probe_support.call_write_sidecar: stated order (working_dir, ledger) first, reversed only if it
      raises; probe.py:280 and test_r1 use it; judge unchanged
- [x] verified: swapped-signature mutant (v5 runs 3 and 8) 8/9 -> 9/9 on the split path; oracle and spec
      9/9, naive 1/9, pristine 0/9 before and after; pytest reference agrees
- [x] copied to all seven g7 arms' tests/ (byte-identical to _suites); report and page updated
- [ ] push g7 world-hosted + hosted validate, when an eval can follow (user's call)

---

# g1: the observations channel is forgeable end-to-end (argus, 2026-09-14)

argus failed g1's world-hosted arm: pristine `main` + an import-time `atexit` hook that
overwrites the worker's `observations.json` scores **reward 1.0, all eleven subscores**.
The jail closed the READ channel; the worker still AUTHORS the outcome file. Two holes:

1. Every expected value is static and published — `batch_plan.json`, `PLAN_FORMAT_VERSION`,
   the 512 cap, "sha256 … first twelve hex", `{"num_jobs": n}` are all in the corpus the
   world arm tells the agent to read, and `probe_support.py` (necessarily in the jail)
   carries the exact inputs. spec/clues hand over `767` and `e3b0c44298fc` in instruction.md.
2. ~30 of g1's ~90 assertions are booleans the WORKER computed (`swept_proof`, `unchanged`,
   `keepers_intact`, the eight `doc_*_eq` flags). `r1.scope` and `r2.exclusions` are graded
   on nothing else — emitting `true` passes them knowing no answer at all.

Fix (plan: `~/.claude/plans/root-cause-the-g1-graceful-sutherland.md`): per-run seed from
root + judge derives its own expectations + judge reads the artifact dirs itself; constants
move to AST. Nothing smaller passes: randomization alone leaves the booleans, and killing
the booleans alone leaves values an agent can memorise.

## Build
- [x] `run_split`: per-run seed + root-readable artifacts dir, passed to worker and judge
- [x] `probe_support.py`: seed-threaded inputs (dataset, limits, prepopulate, keepers, oversize row)
- [x] `probe.py`: scenario dirs under the artifacts root, raw values only, `os._exit`
- [x] `judge.py`: stdlib oracle (request → bytes → greedy pack → fingerprint → document)
- [x] `judge.py`: read the artifact dirs for the r1 sidecar and the five r2 facts
- [x] `judge.py`: AST for the constants (`_module_source`/`_class_source` from g3's judge)

## Prove (twin, before any push)
- [x] bracket: oracle 1.0, pristine/noop 0.0, naive open=1 rest 0, clues 1.0
- [x] forge #1, argus's own: hardcoded oracle observations, ungated atexit → 0.0
- [x] forge #2 (rewritten): a forgery `os._exit` cannot stop — intercepts the write and plants the directories: every former boolean `true` → 0.0
- [x] read diagnostic: jailed worker still PermissionError on task.json/test_*/judge.py

## Ship
- [x] 5 suite files into all 6 g1 arms; `run_suites.py` repo-wide; byte-identity verified
- [ ] push world-hosted → `.horizon/metadata.json` version 16
- [x] hosted validate: oracle 1.00 (17/17), noop 0.00 on every fact
- [x] `tasks/rollout_analysis/targets.json` g1.v → 16; lessons.md entry

## Review — g1 v16 (2026-09-14)

**Measured on the twin, both directions.** `reward` is `hidden_mean`; 11 nodes.

| tree | old grader | new grader |
|---|---|---|
| oracle | 1.0 | **1.0** on four different seeds |
| clues | — | 1.0 |
| naive | open only | open only (hidden 0.0) |
| pristine / noop | 0.0 | 0.0 |
| argus's fixture (hardcoded obs, atexit) | **1.0, all 11** | **0.0** |
| a forgery `os._exit` cannot stop (patches `json.dump`, plants the working dirs, replays a capture of this same code) | — | **0.0**, payload's marker file written |
| 1.2 KB of `true` for r1.scope + r2.exclusions | **2 facts, hidden_mean 0.2** | n/a (no boolean survives) |

**Hosted, g1 v16 (task `6877f4a4`)**: oracle `val-6877f4a4-1789410623932` — 1.0,
all 17 subscores at 1.0. noop `noop-val-6877f4a4-1789410626345` — 0.0588, which is
16 of 17 subscores at 0.0 and `suite_ok` at 1.0, the same signature g3 v9 has.

Jail diagnostic: the worker gets `PermissionError` on `task.json`, `judge.py`,
`test_open.py`, `test_r*.py` and `score.py`, and reads only
`{probe.py, probe_support.py, fixture_spec.py, harness.py}`.

Fuzzed 500 seeds for degenerate fixtures (a single-batch plan, a row larger than
the budget, a plan as long as the pre-populated tail): none.

Regression on the shared harness: g10 through the same `run_suites.py` — oracle
1.0, pristine 0.0. Every other probe takes `sys.argv[1]` alone, so the extra argv
is inert.

**Two things the first draft got wrong, both caught by measurement, not review:**
- the prompt token was fixed-width, so row sizes never moved and a captured run
  fitted the next one — 3 of 10 facts passed by replay;
- `r1.scope` was graded entirely on seed-independent values (an empty plan's
  document is the same every run), so planting the directories passed it.

**Repo-vs-hosted drift this creates:** 17 hosted arms of g2-g11 now carry a
changed `run_suites.py` in the repo that has not been pushed. The change is inert
for them (the extra argv is ignored, the artifacts dir unused); it goes live on
each task's next push.


---

# g1 v17: three facts died on a constant only one of them owns (argus, 2026-09-14)

argus re-run against v16. `probe.py` reached for `module.PLAN_FILE_NAME` in three probe
functions, as the FIRST statement of each. A submission that hardcodes `"batch_plan.json"`
and exports no constant makes that raise `AttributeError` -> `ok: False` -> "probe error"
-> the fact scores 0 before any of its behaviour is looked at. Lost: r1.scope,
r2.failure_behavior, r2.observability, on top of the r1.rule it legitimately fails.
`test_r2.py:14-16` promises the opposite: "an implementation that sweeps without writing a
sidecar passes r2 in full".

r1.scope's coupling is old (v15 probe.py:225). The two r2 ones are mine: v15 planted the
stale bystander under a module-level literal, I deleted the literal to keep answers out of
the jail and reached for the module's constant instead.

## Build
- [x] `sidecar_name(module)` = `getattr(..., None)` — NOT a default to the answer, which
      would put r1.rule's string back in the jail
- [x] r1.scope: drop the name entirely; record the directory listing at the first
      `acreate_request_file` and let the judge assert the spelling
- [x] the two r2 probes: plant the stale sidecar only when there is a name; judge's
      sidecar checks conditional on it
- [x] three crashes that should be clean failures: `PlannedBatch` bound at first use,
      `read_field(..., default=None)` for `max_batches_per_plan`, defensive `batch_limits`
- [x] delete the dead `plan_path`/`load_plan_file` (same coupling, nothing calls them)

## Prove
- [x] `oracle-literal` (argus's rollout as a fixture): **0.6 before, 0.9 after**, r1.rule alone
- [x] `sweep-only` (sweeps, no sidecar at all): **0.4 before, 0.6 after — all five r2 facts pass**
- [x] the v16 matrix again: oracle/clues 1.0, naive open-only, pristine 0, forgeA 0, forgeC 0 (marker written)

## Ship
- [x] propagated to the six g1 arms, pushed v17, hosted validate: **oracle 1.0 (17/17),
      noop 0.0588 (16 facts at 0.0, `suite_ok` 1.0)** — no eval, per Nidhi
- [x] targets.json g1.v -> 17, lessons.md entry

## Review — v17

| fixture | v16 | fixed | what it proves |
|---|---|---|---|
| `oracle-literal` — correct sidecar, hardcoded name, no constant (argus's rollout) | 0.6 | **0.9** | only r1.rule fails, and with a real message |
| `sweep-only` — sweeps, writes no sidecar at all | 0.4 | **0.6** | all five r2 facts pass: `test_r2.py:14-16`'s promise |
| oracle / clues | 1.0 | 1.0 | |
| naive | open only | open only | |
| pristine | 0.0 | 0.0 | |
| forge A (argus's obs fixture) | 0.0 | 0.0 | |
| forge C (`json.dump` intercept + planted dirs) | 0.0 | **0.0, marker written** | the decoupling did not reopen v16's closure |

Both new fixtures stay in the bracket. The twin is rebuilt by `setup_twin.sh` in the
session scratchpad; `driver.sh` was rewritten after it deleted the container's root
filesystem (unguarded `cd` + `find .` — see lessons.md).

## Carried conflict: the plant lives in an agent-image layer (Anti cheat robustness, fc915a50)

**Owner decision, 2026-09-17: documented, not pursued.** Reviewed and costed below.

Nine arms `COPY environment/plant /opt/task-plant` in `environment/Dockerfile` (g1 is the
exception, it has no plant COPY), `setup.sh` ingests it into Mattermost/BookStack/maddy/Gitea
and then `rm -rf /opt/task-plant`. The reviewer fails it anyway, twice in the same words:

- g6 v8: "the agent image itself embeds the task's discovery corpus: `environment/Dockerfile:90-96`
  explicitly calls `/opt/task-plant` an 'answer key' and copies `plant/` into an image layer …
  Protecting it with mode 0700 is insufficient under the rubric's explicit assumption that agents
  run as root with full system access, and it also does not remove the data from image layers."
- g4 v9: "environment/setup.sh:181-183 explicitly acknowledges that the COPY layer still contains
  it after runtime deletion. The planted messages disclose hidden expected values, including
  IDENTITY_BACKEND_PARAM_KEYS and its exact four members (messages.jsonl:161) … Because official
  guidance explicitly fails tasks whose answers are embedded in agent-image layers, deleting only
  the merged-view copy does not satisfy anti-cheat robustness."

What is actually true: inside the running container the agent cannot reach it. `setup.sh` deletes
the directory before the agent's first turn, and an overlay upper-layer deletion is not
recoverable from inside — reading the lower layer needs the image, which lives on the host. The
finding is about image distribution, not in-container reachability. It is still a real finding
under the official guidance as written, which does not make that distinction.

**The only fix that would satisfy it** is to keep the plant out of every layer of the final
image: a BuildKit `RUN --mount=type=bind` (or a multi-stage build whose final stage copies only
the ingested service state), with the ingest moved from runtime into the build. That means
starting postgres, mariadb, mattermost, bookstack, gitea and maddy inside a `RUN`, ingesting, and
copying `/var/lib/{postgresql,mysql,...}` forward — a rewrite of `setup.sh`'s phases into the
Dockerfile, per arm, plus a rebuild and local re-verify each.

**Why it was not pursued:** it needs a push on all nine arms, and a push makes every passing
rubric on that task stale — roughly 270 paid re-runs, against a finding that changes nothing an
agent can actually do inside the task. Cost is the blocker, not feasibility.

**Cheap rider for whenever these arms are next pushed** (not done yet, no push of its own):
`environment/Dockerfile:62` (`:90` on g6, `:68` g7, `:66` g8) says "this directory IS the answer
key to a discovery task" and `setup.sh:181-183` volunteers that the COPY layer keeps it. Both
reviewers quoted our own comments back at us. Keep the comments honest but stop handing over the
phrase: say what the directory is, that it is ingested and removed before the agent's first turn,
and that the layer caveat is a known accepted conflict.
