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
