# Grading-forgery fix — handoff / context doc

**Purpose.** So a future Claude session (including one started fresh after a lost
session) can pick this up cold: understand the score-forgery problem, the fix that
closes it, how to verify it, and how to roll it to every task. If argus (the
adversarial QC reviewer) flags a new forgery on g11/g10 (or any task), hand argus's
report to me together with this file and I'll have the context.

Written 2026-09-10/11. Companion memory: `g11-worker-judge-closes-forgery` (and its
MEMORY.md pointer). Companion in-repo notes: `tasks/todo.md`, `tasks/lessons.md`.

>>> READ "ROUND 4" AT THE BOTTOM FIRST — it is authoritative and SUPERSEDES the
>>> file-lock approach described in sections 3-5 below. Rounds 1-3 (§2-§6) are kept
>>> as history: the file-lock strategy they describe was defeated by argus (the
>>> answers also live in `/tests/task.json` and `test_open.py`, both worker-readable),
>>> and was replaced by JAILING the worker so it cannot read `/tests` at all. Section
>>> 7's "roll to every task" recipe and the ground truth about which suites are split
>>> are still valid; the §4 invariant is replaced by Round 4's.

---

## 1. The problem, in one paragraph

Harbor grades a task by importing the agent's pushed code and running a suite that
decides pass/fail; `reward` for these tasks is `hidden_mean` (the mean of the r1/r2
hidden-requirement facts; `open_feature` is weight 0 and excluded). The danger: the
process that **imports agent code** must not be the process that **reports the
outcome**, or the agent forges a passing report. This bit us three times, each a
narrower version of the same truth: *anything a process running agent code produces
is forgeable, and the only defense is that the agent cannot learn the expected values.*

## 2. History — three rounds (all documented in tasks/todo.md)

1. **Root exploit (2026-09-09, fixed before this session).** pytest ran as root with
   the submission on `PYTHONPATH`; a pushed `sitecustomize.py` ran as uid 0 and
   rewrote `score.py`. Fix: drop the pytest child to `nobody`, submission off
   `PYTHONPATH`. See tasks/lessons.md.
2. **junit-forge (left open by round 1).** The `nobody` child still WRITES
   `junit.xml`, which `score.py` trusted. An `atexit` hook in
   `bespokelabs/curator/__init__.py` overwrote junit after pytest → reward 1.0.
   Fix (a parallel session did g11; I did g10): the **worker/judge split** (§3).
3. **observations-forge (this session's finding).** The split's judge holds the
   expected VALUES as literals; the worker can READ them (from `judge.py` AND from
   the sibling `test_r1.py`/`test_r2.py`, which stay in `/tests`) and write matching
   `observations.json`. Fix: lock `judge.py` **and** `test_r*.py` to root in split
   suites (§4). My first attempt locked only `judge.py` — argus correctly showed the
   `test_r*.py` still leaked the same constants.

## 3. The design that ships (worker/judge split)

Opt-in per suite, in `harbor_tasks/_suites/run_suites.py` (`run_split`, fires only
when the graded suite ships both `probe.py` and `judge.py`; every other task takes
the unchanged pytest path):

- **WORKER** = `_suites/<suite>/probe.py`. Runs as `nobody`, imports the submission,
  reproduces each test's curator calls, and writes VALUES (never verdicts) to
  `observations.json` (path passed on argv). Its atexit hooks / forks are killed with
  the process group after `wait`, so nothing outlives it to touch the judge's output.
- **JUDGE** = `_suites/<suite>/judge.py`. Runs as **root**, imports NOTHING the agent
  wrote (stdlib only), reads the harvested observations, applies the suite's
  assertions, and writes `junit.xml` straight to root-owned `/logs/verifier` with the
  SAME `classname`/`name` node ids as the old tests. So `score.py` folds it into the
  identical fact keys and **`score.py` is unchanged**.
- `test_open.py`/`test_r1.py`/`test_r2.py` are kept as the human source of truth and
  the fact↔test bijection. Under the split they are NOT executed; `probe.py` imports
  only `test_open` (for its scenario helpers).

Why not argus's "judge recomputes the values from source"? These are **behavioral**
facts (what `free_capacity` returns, the learning-rate vector). You cannot get them
from static AST analysis — you must run curator, and any process that runs agent code
can forge its own output. So the only workable defense is keeping the expected values
**secret from the worker**, which is the lock in §4.

## 4. The fix that closes observations-forge

In `harbor_tasks/build_tasks.py`, `TEST_SH` (the generated `test.sh`), right after it
opens `/tests` group-readable (`chmod -R g+rX,o-rwx`):

```bash
for _j in $(find /tests -name judge.py 2>/dev/null); do
  _d=$(dirname "$_j")
  chmod 0600 "$_j" "$_d"/test_r*.py 2>/dev/null \
    || echo "WARNING: could not lock answers in $_d" >&2
done
```

- Locks `judge.py` AND `test_r*.py` to `0600 root` **only in split suites** (a dir
  that ships `judge.py`). The worker needs neither (it imports `probe.py` →
  `test_open`; root runs `judge.py`).
- **Scoped to split suites on purpose.** A NON-split task runs pytest over its own
  `test_r*.py` as the same `nobody` uid; locking those would fail its collection and
  score it zero. So the `find` keys off `judge.py` presence.
- **`test_open.py` stays readable** — `probe.py` imports it for helpers, and it holds
  only the weight-0 open-feature constants, which cannot move `reward`.

**INVARIANT to preserve forever:** reward-bearing (r1/r2) expected values live ONLY in
`test_r*.py` and `judge.py`. If any hidden answer ever leaks into `test_open.py`,
`probe.py`, `harness.py`, `conftest.py`, `fakeapi.py`, or a new readable file, the
forgery reopens. When adding a split to a task, keep answers out of those files.

## 5. What is done vs pending (as of 2026-09-11)

DONE:
- g10: built `_suites/g10_token_capacity_budget/{probe.py,judge.py}` (open+r1+r2).
- g11: split already existed (parallel session); I added the complete lock.
- `build_tasks.TEST_SH`: the §4 lock.
- Propagated `tests/` (only — NOT `emit()`, which regenerates `plant/`) to all 14
  g10+g11 arms; every arm's probe/judge/test.sh verified byte-identical to source.
- Local proof on the twin, both tasks (§6): oracle 1.0, noop 0.0, junit-forge 0.0,
  obs-forge-reading-`test_r1.py` 0.0; control (judge-only lock) 1.0.
- Re-pushed hosted: **g10-world-hosted v7** (task `34977c02-de6b-4fa9-aadd-b25a143d8e80`),
  **g11-world-hosted v9** (task `aa5d35bc-601a-4449-b842-150094c6ff22`).
- Submitted 1-run lumen/typhoon/8cpu evals: g10 `f857ceb0-7f77-4854-940d-f1091678a886`,
  g11 `27e1e98a-5053-4831-9338-02c7fea7f283` (running at last check).

PENDING / NOT done:
- Confirm those hosted rollouts complete clean (errored 0, graded, sensible avg).
- **NOT committed to git** (working tree only). The pushes bumped `.horizon/metadata.json`.
- Only g10+g11 hosted arms re-pushed. The other g10/g11 arms (spec/clues/world/
  world-located/world-located-hosted) carry the fix on disk but are not re-pushed.
- **Roll to every task** once g10/g11 confirmed (§7).

## 6. Verify runbook (local twin — free, decisive for forgery closure)

The forgery closure is proven locally; hosted rollouts are just the clean-run check.

- Twin image: `g10-world-verify:local` (a booted SWEWorld world with Gitea + curator
  venv + baseline at `/opt/world-state/input/curator`, `nobody` user). Boot:
  `docker run -d --name TW g10-world-verify:local`; wait for
  `/usr/local/bin/wait-for-service --all --quiet`.
- Oracle tree = baseline + `harbor_tasks/g10-.../fixtures/oracle.patch` (`git apply`).
- Stage `/tests` = copy `_suites` in, drop the arm's `task.json`, write `build_tasks.TEST_SH`.
- `driver.sh` (in scratchpad) pushes a submission tree to Gitea `main` and runs
  `/tests/test.sh`; read `/logs/verifier/reward.json`.
- Forge payloads (scratchpad): `payload_obs_testfile.py` appends an atexit hook to
  `src/bespokelabs/curator/__init__.py` that reads `test_r1.py`/`test_r2.py` and, if
  readable, writes embedded oracle observations to the worker's obs path. Embed the
  oracle obs by running `probe.py` against the oracle once and saving its output.
- Expected matrix (both tasks): oracle 1.0, noop(pristine) 0.0, obs-forge 0.0
  (PermissionError reading `test_r1.py`); control with the lock removed → 1.0.
- **A forge fixture MUST read every answer-bearing file (`test_r*.py`, not just
  `judge.py`), or it proves nothing.** That was my round-3 mistake.

Scratchpad artifacts from this session live under the session's scratchpad dir
(`.../caa7416e-.../scratchpad/`): `driver.sh`, `payload_junit.py`,
`payload_obs_testfile.py`, `propagate_g10_g11.py`, `obs_g10_oracle.json`. They are
session-scoped and may be gone in a new session — regenerate from this doc.

## 7. Rolling to every task (the future job)

Which tasks are which today (CORRECTED — an earlier version of this doc wrongly
listed g7/g9 as split; they are NOT):
- **Worker/judge split (ship probe.py+judge.py):** g1, g2, g3, g4, g6, g7, g8, g9, g10, g11
  (all ported 2026-09-11, same jail pattern; each verified oracle 1.0 / noop 0.0 / file-leak
  closed on the twin, keysets match declared fields). There is no g5.
- **Still classic pytest path:** g12_backend_params_config, g13_raft_document_set, and the
  t* starter suites (t0/t1/t2/t3/t4/t12/t23/t40). Rolling the split to any of these needs a
  bespoke probe/judge + probe_support port (§8-style) — a per-task job.
- g1–g6 fixtures handled in the ports: tmp_path→tempfile.mkdtemp (g1,g4,g7,g8);
  monkeypatch→a MonkeyPatch shim in the probe (g2,g4,g6 use pytest.MonkeyPatch or g11's shim,
  incl. `setitem` for g2's sys.modules seam); none use the network `provider` socket or the
  `output` fixture, so the jail stayed `{probe,probe_support,harness}` (no fakeapi needed).

Per task, to add the split:
1. Write `_suites/<suite>/probe.py` — reproduce each test function's curator calls,
   record raw values keyed by the exact node id (`test_r1::test_rule__...`). Import
   `test_open` for helpers. Record nothing that decides truth. Structural facts a
   judge can check from source (AST) can be recorded as source, like g11's open judge.
2. Write `_suites/<suite>/judge.py` — for each node, apply that test's assertions to
   the recorded values; write `junit.xml` with the same node ids (copy g10/g11's
   `junit()` + `main()`). Use exact `==` for integer/exact facts, an approx helper
   (see g11 judge) for float facts.
3. **Generate the judge's expected literals from the oracle**, then cross-check them
   against the original `test_*.py` inline constants — don't hand-transcribe. (For
   g10 I generated obs from the oracle run and diffed against the asserts; all matched.)
4. Keep reward-bearing answers only in `test_r*.py`/`judge.py` (§4 invariant).
5. `TEST_SH` lock is already global — a new split suite inherits it automatically.
6. Propagate `tests/` (only) to all the task's arms (adapt `scratchpad/propagate_g10_g11.py`'s
   `GROUPS`); do NOT use `build_tasks.emit()` (it regenerates `plant/` and can clobber
   hand-applied corpus fixes).
7. Verify on the twin (§6) before pushing. Then push + a small hosted rollout.

## 8. Horizon CLI cheatsheet (tooling lives at `~/horizon_env/bin`)

- Auth: `.env` at repo root has `HORIZON_API_KEY`; `export PATH="$HOME/horizon_env/bin:$PATH"`.
- Push a new task version (from an arm dir, uses its `.horizon/metadata.json`):
  `horizon tasks push . --label "..."`.
- Submit a rollout: `horizon evaluations submit <task-uuid> --model lumen
  --agent-type typhoon --runs N --machine-type e2-custom-8-16384 --json`.
  - `lumen` = the model; `typhoon` = agent type; **`e2-custom-8-16384` = "8cpu"**
    (g11's task.toml pins cpus=8 and REQUIRES this flag or every rollout errors).
  - submit `--json` returns the id under key **`evaluation_id`** (NOT `id`).
- Status: `horizon evaluations status <eval-id> --json`, or REST
  `GET $HORIZON_SERVER_URL/api/evaluations/<id>` with `Authorization: Bearer $HORIZON_API_KEY`
  (fields: `status`, `rollout_avg_score`, `rollout_passed_count`, `rollout_errored_count`,
  `rollout_graded_count`). Full per-rollout trace: `GET /api/rollouts/<id>` (the raw API
  is untruncated; `rollouts pull` truncates at 2048 bytes).
- There is **no `evaluations list`** command. To recover lost eval ids:
  `GET /api/evaluations?limit=60`, filter by `creator_email`/`model`/`runs_per_task`,
  map to task via the `task_names` field. The list endpoint's key is `id`.
- Do NOT keep long background pollers here — the box OOM-kills them. Poll with a single
  status check per turn, or `horizon evaluations watch <id>` interactively.

## 9. "Is this fixed?" — how to reason about a NEW argus report

The general theorem: if a process runs the agent's code and produces output O that the
grader trusts, the agent controls O. The grader's O→pass mapping is safe ONLY if the
agent cannot learn which O passes, i.e. the expected values are unreadable by the
worker. So when argus reports a new forgery, ask:
1. Does the worker (nobody, at grade time) have a readable path to any reward-bearing
   expected value? Enumerate every group-readable file in `/tests` (after `test.sh`)
   and check for the r1/r2 constants — `test_r*.py`, `judge.py`, bracket/answer files,
   `test_open.py`, `probe.py`, and any new file. Lock or scrub the leak.
2. Can the worker's output reach `score.py` other than through the judge? (It must not
   — `score.py` reads the judge's junit, written by root.)
3. Did the forge fixture actually exercise the reported channel? (Round 3 was missed
   because the fixture only read `judge.py`.)
Give me argus's report + this file and I'll work it through these.

## 10. Key file map

- `harbor_tasks/_suites/run_suites.py` — `spawn()`, `run_split()`, opt-in branch.
- `harbor_tasks/_suites/<suite>/probe.py`, `judge.py` — the split (g10, g11, g7, g9).
- `harbor_tasks/build_tasks.py` — `TEST_SH` (the §4 lock), `emit()`, `DOCKERFILE`/
  `HOSTED_DOCKERFILE`.
- `harbor_tasks/_suites/score.py` — reward = `hidden_mean`; folds junit node ids →
  fact keys; unchanged by the split.
- `harbor_tasks/_suites/harness.py`, `conftest.py`, `fakeapi.py` — shared readers/
  fixtures; no answers.
- `harbor_tasks/<task>/<arm>/.horizon/metadata.json` — task UUID/version per arm.

---

# ROUND 4 (2026-09-11): jail the worker — the fix that actually holds

## Why the locks kept failing
Argus broke rounds 2-3 because the answers are reachable by the worker no matter
which files you 0600-lock: `/tests` is opened group-readable, and the answers live
in files the worker can `open()` by absolute path — **`/tests/task.json`** (its
`hidden_requirements` prose states every expected value verbatim) and
**`test_open.py`** (the worker imports it; its source carries the answer literals).
Locking judge.py/test_r*.py is moot while those are readable.

## The fix (implemented + verified)
Make the worker physically unable to read `/tests`:
- `build_tasks.TEST_SH`: for a SPLIT suite (this task's `task.json["suite"]` ships
  probe.py+judge.py) keep `/tests` ROOT-ONLY (`chown -R root:root; chmod -R go-rwx`).
  Non-split suites keep the old `g+rX` (their pytest worker reads /tests). The old
  judge.py/test_r* lock loop is gone (subsumed).
- `run_suites.run_split`: stage a root-owned JAIL (`work/jail`, 0755) holding ONLY
  `{probe.py, probe_support.py, harness.py}` (0644); run the worker with
  PYTHONPATH=`src:jail`, cwd=jail. `spawn()` gained a `cwd` kwarg — the worker MUST
  NOT keep cwd=/tests (0700) or it can fail to chdir and zero even the oracle (R1).
- New answer-free module `_suites/<suite>/probe_support.py` holds the helpers/inputs
  the probe needs (lifted from test_open); NO expected value. `test_open.py` now
  imports those helpers from probe_support (one definition, no drift) and keeps only
  its assertion bodies + (g11) the `SIGNATURE`/`BATCH_LOSSES` answer literals. probe.py
  imports probe_support, not test_open. g11 probe computes the dataset signature live
  (`probe_support.signature()` → `dataset_signature(DATA)`) instead of the SIGNATURE
  literal.

Verified on the twin (both tasks): oracle 1.0, noop 0.0, file-leak forge 0.0; a
diagnostic payload confirmed the jailed worker gets **PermissionError on task.json,
test_open.py, test_r*.py, judge.py** and can read only `{probe.py, probe_support.py,
harness.py}`. This defeats argus's reproduced 1.0 (answers unreadable; high-entropy
facts — loss floats, LR vectors — cannot be produced without correct curator).
Pushed g10 v8, g11 v10; one lumen/typhoon/e2-custom-8-16384 rollout each
(g10 eval 9963d46e…, g11 eval 9153f93e…).

## New invariant (supersedes the file-lock invariant)
The worker's entire reachable file set is `{probe.py, probe_support.py, harness.py}` +
the submission's own `src`. Every reward-bearing expected value must live ONLY outside
that set. When adding a split to a task: put answers only in judge.py; keep
probe_support answer-free; compute any answer-derived construction input live from the
submission. (A build-time lint asserting probe_support has none of judge.py's literals
is a good follow-up — not yet added.)

## KNOWN RESIDUAL — read this before claiming g11 "closed"
`probe.py` is necessarily worker-readable (the worker executes it). g10's is
answer-free. g11's `probe.py` carries LOW-ENTROPY scenario literals (checkpoint names,
`loss=0.25`, reason strings) that coincide with some r1 answers. Measured ceiling: a
DETERMINED adversary reading probe.py and reconstructing could forge **4/9 ≈ 0.44** on
g11 — the four non-`observability` r1 facts. The HIGH-ENTROPY facts (`r1.observability`
loss floats + all four r2 LR-vector facts) stay unforgeable. Two caveats: reconstructing
r1.rule/scope/exclusions needs understanding the hidden triggers/ledger-order (≈ solving),
so the "free" residual (no understanding) is closer to ~0.1 (r1.failure_behavior's
structural `len=1`). This is INHERENT to reporting low-entropy behavioral facts through
a worker-written channel — jailing cannot remove it; only redesigning those facts to
carry a high-entropy anchor would. Documented as a follow-up, shipped with the user's
explicit OK.
