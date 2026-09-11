# g1–g11 lumen rollouts, read against the answer key (2026-09-11)

The `world-hosted` (blind) arm of every g-task, model `lumen` (Opus 5), agent `typhoon`,
at each task's latest version with a 10-run eval. **Every transcript was read against
that task's answer key, remark by remark**: whether the agent found each planted remark,
how it found it, what its `Analysis:`/`Plan:` said about it, and whether the shipped code
followed it. Herrings and reversals got the same treatment. Scores are Horizon's own
grades.

Status: **complete**. **g7 and g9 were re-evaluated on 2026-09-11** (g7 v5, g9 v8), and their sections replace the earlier evals, whose results are dropped. 100 rollouts are read: 99 scored, plus g2's execution failure. The summary is directly below; the per-task sections and the defect register follow.

## How this was measured

1. **Pull.** `horizon rollouts pull <task> --version <v>`, plus the full rollout record
   from `GET /api/v1/rollouts/<id>`, which carries the whole ctrf trace. `pull` truncates
   it at 2048 bytes.
2. **Pre-pass.** This is deterministic and only aims the reading. It parses the key's
   "Where every remark is" section, whose quotes are exact corpus text. For each run it
   lists where each remark's text first surfaces: the step, the transcript line, and the
   command that surfaced it.
3. **Readers.** One subagent per rollout reads the whole transcript against the key.
   For each remark it records found (yes/partial/no), how, the agent's own reasoning quoted
   with a line reference, whether that reasoning registered the remark as a requirement,
   and whether the code followed it. Every lost fact gets one cause:
   - `not_found`
   - `found_misread`
   - `herring_followed`
   - `overridden_by_other_corpus_text`, meaning other text in the world argued the graded
     question the other way. This is a task defect.
   - `implementation_slip`, meaning the agent's reasoning states the rule and its code does
     otherwise.
   - `grader_overspecifies`
   - `infra`
4. **Checks.** I aggregate the readers' rows. Pass and fail come from Horizon's grade, not
   the readers. Reader verdicts I overruled by hand are listed per task.

**What "score" means here.** Horizon's `extracted_score` is the unweighted mean of *every*
subscore: open_feature, suite_ok, provenance ×3, hidden_mean, reward, and the facts. It
reads well above the task reward. For example, g1 run 8d664a4c shows 0.8588 extracted
against a 0.80 reward. This document uses **`reward`, the mean of the hidden facts**. The
number of facts comes from the suite, not the key's "five facts" boilerplate.

**Readers ran on Sonnet.** Opus 5 readers were refused 8 of 10 times by an API safeguard
tagged `[reasoning_extraction]`, on both attempts. The one Opus reader that completed
read the shortest transcript (a g7 run of the superseded v4 eval). The g7 and g9 reruns
were read on Sonnet too.

| task | version | eval(s) | lumen runs read |
|---|---|---|---|
| g1 batch-payload-plan | v14 | 8db49761 | 10 |
| g2 executor-output-cap | v11 | 9f2db992 | 10 (1 execution failure) |
| g3 retry-backoff-policy | v7 | ce846459 | 10 |
| g4 run-cache-identity | v5 | 0ebb2b86 | 10 |
| g6 model-price-lookup | v6 | 30b9f0dd | 10 |
| g7 agent-turn-ledger | **v5** | **8deffce4** (rerun; replaces v4 94bf8242) | 10 |
| g8 attachment-payload | v8 | 30c95df4 + 66eb8a20 + 48fe71f7, pooled on one version | 10 (+1 errored, not read) |
| g9 example-encoding | **v8** | **3b0b259f** (rerun; replaces v7 fffbd350, which had only 2 scored runs) | 10 |
| g10 token-capacity-budget | v5 | 5b468409 | 10 |
| g11 training-step-ledger | v7 | 94bf8242 | 10 |

There is no g5 world-hosted task.

---

## Findings at a glance

All rates are pooled over all ten tasks (g1–g4 and g6–g11), using **live runs** only: runs
that shipped and were not zeroed by infra. g7 and g9 use their 2026-09-11 reruns.

### Difficulty ranking

| task | mean reward (live runs) | runs at 1.00 | hardest fact | why it is hard, or easy |
|---|---|---|---|---|
| g7 agent-turn-ledger | **0.76** | 0/10 | r1.rule 2/10 | the graded filename constant lives in one comment on an off-topic page, and the graded argument order was planted but never rendered (G7-D) |
| g1 batch-payload-plan | 0.79 | 3/10 | r1.rule, r1.scope 3/10 | the function name is hedged (`plan_fingerprint` "or something"), and 3 other remarks say `plan_id`; the constant lives in a nested comment reply |
| g6 model-price-lookup | 0.84 | 0/10 | r2.exclusions 3/8 | **known, then not built**: 78% of losses are slips |
| g9 example-encoding | 0.84 | 1/10 | r2.failure_behavior 4/10 | its mail herring is the one that works: the 6 runs that never opened the comments on the "request builder" page, where the reversal is, believed it |
| g2 executor-output-cap | 0.85 | 0/10 | r1.failure_behavior **1/9** | two graded names, each with one home, both in the quiet #cookbooks |
| g8 attachment-payload | 0.86 | 1/10 | r1.scope 4/10 | only one remark says *where* the 45 MB total lives, and the ticket's "out of scope: the batch path" invites misfiling it |
| g11 training-step-ledger | 0.86 | 2/10 | r1.failure_behavior, r2.rule 6/10 | the merge and the keyword-only rule each have a single carrier; a half-reversed herring (G11-H) |
| g3 retry-backoff-policy | 0.92 | 5/10 | r2.rounding 6/10 | rounding is stated once; 3 of the 1.00s were false passes, since fixed (G3-A) |
| g10 token-capacity-budget | 0.93 | **7/10** | r1.exclusions 7/9 | each reversal restates the whole design in one turn |
| g4 run-cache-identity | 0.94 | 4/10 | r1.scope 5/8 | the copy rule is stated as an observation, not a rule |

### 1. Half of all losses are search misses, and nearly all of those are single-home remarks

112 knowledge fact-points were lost in live runs:

| cause | points | share |
|---|---|---|
| not found | 60 | **54%** |
| implementation slip | 23 | 21% |
| found but misread | 15 | 13% |
| herring followed | 9 | 8% |
| grader over-specifies | 3 | 3% |
| the corpus argues against the grader | 2 | 2% |

Almost every "not found" traces back to a **graded name, value or order that is stated in
exactly one remark**. The single-home table in the Register lists them. Whether a run found
that one place decides the fact:

| single-home remark | found → passed | not found → passed |
|---|---|---|
| g11 `l10` | 6/6 | 0/4 |
| g8 `s2-gideon` | 4/5 | 0/5 |
| g2 `l-floor-konrad` | 1/1 | 0/8 |
| g7 `TURN_LEDGER_FILENAME` | 2/4 (the other two lost to G7-D) | 0/5 |
| g9's only reversal, `rev3` | 4/4 | 0/6 |

### 2. Which clue qualities go unfound

"Found" means seen at least partially.

| quality | found | vs. | found |
|---|---|---|---|
| **carries an identifier** that must be typed literally | **79%** | plain English, no identifier | **58%** |
| its own chat thread | 75% | **dropped into an existing conversation** | **63%** |
| a new wiki page | 80% | **a comment on an existing page** | **50%** |
| mail (new 81%, reply 93%) | 82% | wiki page bodies | 62% |

Within a task, a quiet channel drops far lower: g7 #releases 0/10, g4 #help 1/10, g2
#incidents 20%, g7 #viewer 25%.

**The mechanism is the same in every task.** Agents dump every channel and page to disk,
then grep with *their own* list of terms. A remark that lacks those terms stays unread even
though it is on disk. The same thing happens when a remark:
- is a nested reply in a comment thread (g1 `PLAN_FILE_NAME`);
- sits on a page whose title looks off-topic (g7 "Weekly sync notes", g9's
  "request builder" page);
- uses a synonym, such as "label sets" for `reasons` (g11);
- uses the bare name when agents search the compound one, `max_bytes` versus
  `max_output_bytes` (g2).

Output truncation hides it too. g7 run 4 listed its mail subjects through `head -40`.

### 3. Found is not the same as used

93% of found clues were registered as requirements, and 95% were followed in code. The
remaining few percent fall disproportionately on graded facts: **38 of the 112 lost points
(34%) came from runs that had the remark**. The recurring shapes:
- a rule stated as an observation, which agents read without drawing the inference (g4
  `fix27`);
- a rule read in full and then written backwards (g7 run 7, with g7's `fix27`);
- deciding a requirement is out of scope (g1 run 4: "a distractor"; g8: "the batch
  estimator");
- naming slips (g1's `plan_id`);
- the right rule at the wrong call site (g6 trackers versus processors; g8 hook placement);
- two copies of one rule that drift apart (g9 run 5).

g6's losses are 78% slips.

### 4. Herrings work only when the run never reaches the reversal

| what the run saw (366 run–herring pairs) | believed the herring and shipped it |
|---|---|
| the herring and its reversal | **1/271 (0.4%)** |
| **the herring but not its reversal** | **6/13 (46%)** |
| the reversal but not the herring | 0/68 |
| neither | 1/14 |
| **overall** | **8/366 (2%)** |

Reversals are the most-found kind of remark (94%). They quote the herring, call it dead,
and share its keywords, so the grep that finds the herring usually finds the reversal too,
and then the herring does nothing.

It worked in two places:
- **g9 `h-role-row`, 6 runs:** its reversal is a comment on the "request builder" wiki
  page, and those six runs never opened that page's comments.
- **G11-H, 1 run:** the reversal retracts only half of its herring.

And many reversals *restate the full answer*, which makes their requirement cheap: g1 r2,
g7 r2 and all of g10 are near-perfect for this reason.

**Invented scaffolding is the other thing that misleads.** That is the conversation
phase 4 writes around a correctly planted remark, which then argues the graded question the
other way:
- **G3-A:** 3 false passes in v7. Every run that saw konrad's invented line followed it.
  **Fixed 2026-09-11 and pushed as g3 v9**; no eval on it yet.
- **G8-A:** 2 points.
- **G7-A:** 8 points in v4, **fixed in v5 and verified at 0**. All ten v5 runs read the
  corrected reply.

### 5. Hardest fact type

| fact type | pass rate (live runs) |
|---|---|
| failure_behavior | 78% |
| rule | 84% |
| scope | 87% |
| observability | 87% |
| exclusions_or_crossover | 91% |

### 6. The measurement is noisier than the task

55 fact-points were lost in dead runs:
- **30 to infra.** The git remote reset after a green CI (g6 runs 1 and 3; g11 run 7
  survived it), and stale terminals feeding false "pushed / merged / CI green" output (g4
  run 9, g7 run 5).
- **25 to runs that never shipped** (g2 run 8, g4 run 2, g10 run 8).

On top of that, g11's eval 3c71bf59 errored 10/10, and the world's CI "tests" step passes
without pytest installed. Horizon's `extracted_score` also overstates the task reward.

### 7. What to fix first, in order

1. **G7-D:** re-render `g7.r1.say20` so the argument-order clause survives, or accept
   either order. It has cost 3 runs across two evals.
2. **G8-A:** rewrite the invented turns around `fix24`.
3. **G11-H:** make g11's `rev2` retract konrad's whole herring.
4. **Environment:** investigate the git remote resets and the stale terminals; they zeroed
   4 runs.
5. **Difficulty design:**
   - Give each single-home graded name a second carrier that search can reach (or accept
     either name, as for `plan_fingerprint`).
   - Stop using synonyms for graded names.
   - Write reversals that retract the herring **without restating the finished answer**.

*Done: G7-A. The g7 rerun shows 0 points lost to it, down from 8. G3-A and G3-B are fixed
and pushed as g3 v9 (2026-09-11), verified locally on the grading path; hosted validate oracle 1.0 / noop 0 on every fact;
no opus eval on v9 yet.*

---

## g1 — batch-payload-plan (v14, eval 8db49761)

**Reward.** The mean is **0.79** over 10 runs, and **3/10 scored 1.00** (runs 2, 3 and 8).
r2 is perfect: all 5 of its facts in all 10 runs. **Every loss is in r1**, and no loss is
a task defect or infra.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | 8d664a4c | 0.80 | r1.rule, r1.scope (not found: `PLAN_FILE_NAME`; it shipped `BATCH_PLAN_FILENAME`) |
| 2 | e1cfa814 | 1.00 | — |
| 3 | a653d6d4 | 1.00 | — |
| 4 | 6cb5be65 | 0.60 | r1.rule, r1.scope, r1.exclusions_or_crossover, r1.observability (misread: read the sidecar design and wrote it off as "a distractor") |
| 5 | 12f8950a | 0.80 | r1.rule (not found: `PLAN_FILE_NAME`); r1.scope (not found: plan written before requests) |
| 6 | 58cecadc | 0.70 | r1.rule, r1.observability (misread: named it `plan_id`); r1.scope (not found: plan written before requests) |
| 7 | 1f06df7a | 0.70 | r1.rule, r1.scope, r1.observability (not found: the plan document's key order, whose only full statement is in #general) |
| 8 | 725ada84 | 1.00 | — |
| 9 | 9016ab99 | 0.70 | r1.rule, r1.scope, r1.observability (slip: its plan says `plan_fingerprint`, its code says `def plan_id`) |
| 10 | 15525502 | 0.60 | r1.rule (not found: `PLAN_FILE_NAME`); r1.scope, r1.observability (misread: `plan_id`); r1.failure_behavior (not found: `f4`, "per-row oversize reports first") |

**Pass rate per r1 fact:** rule 3/10, scope 3/10, observability 5/10, exclusions 9/10,
failure_behavior 9/10.

**Why the 21 lost fact-points were lost:**

| cause | points | share |
|---|---|---|
| not found | 10 | 48% |
| found but misread | 8 | 38% |
| implementation slip | 3 | 14% |

No task defect or infra loss.

### Why r1 was hard: five graded names or orders, each with one home

The losses cluster on things that are **graded exactly and stated in exactly one
remark**. I verified each "one home" claim by grepping the answer key and the ticket.

| what is graded | its only carrier | how it is hidden | runs whose transcript ever shows it | points lost |
|---|---|---|---|---|
| the name `plan_fingerprint` | `g1.r1.l6`, hedged: "call it plan_fingerprint **or something in that direction**" | `plan_id` appears in 3 other remarks (`l7`, `l14`, `say22`) and is the real JSON key; the ticket names neither | 9/10 (the name *was* seen) | **7** (runs 6, 9, 10 wrote `plan_id`) |
| the constant `PLAN_FILE_NAME` | `g1.r1.l2`, a *reply* inside a wiki comment thread (nikolai 09:47) on "batch job status persistence across process restarts" | nested reply on an off-topic page; comment dumpers that printed only each page's first comment never showed it (runs 1 and 5) | 6/10 | 4 (runs 1, 5, 10) |
| the plan document's key order and names (`num_requests`, `num_bytes`) | `g1.r1.say22`, #general | `l11` (#viewer) gives the shape but only says "the request and byte totals" | 8/10 | 3 (run 7, which never dumped #general) |
| "plan gets written before the first request file" | `g1.r1.l16`, #pipeline | plain English with no identifier | 3/10 | 2 (runs 5, 6) |
| per-row oversize is reported before too-fragmented | `g1.r1.f4`, #engineering | plain English | 5/10 | 1 (run 10) |

The rest is run 4's 4 points. Having read two full mail threads about the sidecar, it
decided it was "a serialization subsystem that doesn't exist in the repo". Its wiki
script had also silently printed no comments across all 114 pages.

**The `plan_fingerprint` loss is agents slipping on a trap the task set.**
- Every run saw `l6`. Run 9's own plan text even says "Append plan_fingerprint (plan_id)".
- But the only remark naming the function hedges its name, and the output field that every
  other remark talks about is called `plan_id`.
- The grader requires the symbol `plan_fingerprint` (`test_r1.py:75`).
- Seven points, a third of g1's losses, come from this one naming collision.

### Why r2 was easy: redundancy and reversals

Every run scored all 5 r2 facts, even though several r2 carriers were found by only
2–3 of 10 runs:

| remark | where | found |
|---|---|---|
| `g1.r2.l13` | #code-review | 2/10 |
| `g1.r2.l4` | #engineering | 2/10 |
| `g1.r2.l2` | #code-review | 3/10 |
| `g1.r2.l5` | #pipeline | 3/10 |
| `g1.r2.l10` | #incidents | 3/10 |
| `g1.r2.l6` | mail | 3/9 |

Each r2 fact has a second carrier that most runs did find, and both r2 reversals restate
the rule. Run 3's reader found that `r2.scope` was passed from the ticket's own text.

### Herrings: no pressure at all

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| `g1.r1.h1` → `rev1` | 8/10 | 9/10 | 0/10 | 0/10 |
| `g1.r1.h2` → `rev2` | 7/10 | 10/10 | 0/10 | 0/10 |
| `g1.r2.h1` → `rev1` | 8/10 | 7/10 | 0/10 | 0/10 |
| `g1.r2.h2` → `rev2` | 6/10 | 10/10 | 0/10 | 0/10 |

Most runs saw the herring in the same dump or search as its reversal. Even the runs that
saw `g1.r2.h1` without its reversal didn't adopt it: other remarks and the ticket already
settled the point. One run (run 2) briefly misread a remark about the exception
hierarchy, then corrected itself from the fuller thread before writing code.

### Which remarks go unfound

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 72% |
| plain English, no identifier | 65% |

The gap is smaller than g7's: most g1 remarks carry *some* identifier.

**By channel, the quiet ones leak.**

| channel or surface | found |
|---|---|
| #engineering | 25/50 (50%) |
| #incidents | 16/30 (53%) |
| #releases | 28/50 (56%) |
| #code-review | 70% |
| wiki comments | 70% |
| #pipeline | 73% |
| mail | 79% |
| #cookbooks | 90% |

Runs dump every channel, then grep each dump with a fixed list of terms. Channels whose
remarks lack those terms are effectively unread even though they are on disk (runs 3, 5
and 9).

### Owed for g1 (not applied)

- Give `plan_fingerprint` a firm, unhedged statement, or make the grader accept either
  name for the function. As written, the task tests whether the agent picks the less
  common of two names.
- Give `PLAN_FILE_NAME` a second home that search can reach; today it lives only in a
  nested comment reply.
- Give "plan written before the first request file" a second, differently worded carrier.

---

## g2 — executor-output-cap (v11, eval 9f2db992)

**Reward.** The mean is **0.85** over the 9 graded runs, or 0.77 counting run 8 as 0.
**No run scored 1.00.** Run 8 never shipped. It built `output_cap.py`, never wired it into
`_execute_in_sandbox`, declared the work complete, then looped until Harbor killed the
trial at 7200 s. That is an agent failure, not infra, and it is kept out of the knowledge
figures below.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | 6d73e7af | 0.889 | r1.failure_behavior (found the name `OutputCapError`, never found `.max_bytes`) |
| 2 | 2dc46c26 | 0.889 | r1.failure_behavior (found neither; shipped a plain `ValueError`) |
| 3 | 069b893c | 0.778 | r1.failure_behavior (found neither); r1.observability (logs twice on the salvage path; `l-log-konrad` never found) |
| 4 | 615d1360 | 0.889 | r1.failure_behavior (found neither; invented `InvalidOutputBudgetError`) |
| 5 | 62b9f306 | 0.889 | r1.failure_behavior (name found, `.max_bytes` not) |
| 6 | f4648f93 | 0.889 | r1.failure_behavior (name found, `.max_bytes` not) |
| 7 | 33b81bf0 | 0.778 | r1.failure_behavior (found neither); r1.observability (no `TRUNCATION_LOG_TEMPLATE` constant; the only transcript that never shows it) |
| 8 | 7be2f425 | — | never shipped (see above) |
| 9 | 4ba13ac7 | 0.889 | r1.observability (saw only the last line of `l-log-konrad`; logs twice) |
| 10 | 7919e169 | 0.778 | r1.failure_behavior (found neither; never dumped #cookbooks in 98 steps); r1.observability (logs twice) |

**Pass rates over the 9 graded runs:** **r1.failure_behavior 1/9**, the lowest pass rate
of any fact in any task read so far. r1.observability is 5/9; the other 7 facts are 9/9.
**All 12 lost fact-points are `not_found`.**

### Why it was hard: one quiet channel holds three graded names, each with one home

The ticket names none of these, and each was verified as having a single carrier.

| graded name or rule | its only carrier | runs that found it | effect on the score |
|---|---|---|---|
| the class name `OutputCapError` | `g2.r1.l-floor-nikolai`, #cookbooks 2025-03-14 | 4/10 (runs 1, 5, 6, 9) | — |
| `.max_bytes` on the exception, plus the exact message `max_bytes must be 0 or at least 16, got 8` | `g2.r1.l-floor-konrad`, #cookbooks 2025-03-17 | **1/10 (run 9)** | **failure_behavior passed only in run 9** |
| "the except handler's salvage cap logs nothing" | `g2.r1.l-log-konrad`, #cookbooks 2025-05-01 | read in full by 6/10; run 9 saw only its last line | the 5 graded runs that read it passed observability; the 3 that did not (runs 3, 9, 10) lost it; run 7 read it but lost on the template name |
| the constant `TRUNCATION_LOG_TEMPLATE` | `g2.r1.l-log-nikolai`, a wiki comment on the on-topic page "capping executor stdout and stderr" | 9/10 transcripts | only run 7 missed it, and lost |

**`failure_behavior` needs two keys, and they sit in two remarks.** The name is in
nikolai's thread, and the attribute plus the message are in konrad's thread three days
later. 4 runs had the name and 1 had both.
- Agents searched for `max_output_bytes`, but konrad's remark says `max_bytes` and never
  says "cap".
- Runs dumped #cookbooks but read it only in narrow windows (runs 3 and 6), never dumped it
  (run 10), or dumped #pipeline for the same time window instead (run 9).

**Having only one carrier is not the problem by itself.** `TRUNCATION_LOG_TEMPLATE` also has
a single home, but it is a comment on a wiki page whose title says it is about this task,
and 9/10 runs found it. The three #cookbooks remarks are single homes in a quiet channel
with unusual wording.

**By channel:**

| channel or surface | found |
|---|---|
| #incidents | 4/20 (20%) |
| #general | 6/20 (30%) |
| #cookbooks | 33/60 (55%) |
| #viewer | 88% |
| wiki comments | 90% |
| mail | 98% |

### Why the rest was easy

r1's rule, scope and exclusions, and all four r2 facts, passed in every graded run. Their
carriers sit in mail (98% found), wiki comments (90%) and busy channels, and each fact has
more than one carrier.

### Herrings: no pressure

All four herrings were seen by 10/10 runs and their reversals by 9–10/10. **No run
believed any of them.**

### Owed for g2 (not applied)

- Give `OutputCapError` and `.max_bytes` a second, searchable carrier outside #cookbooks,
  or state them in one remark worded the way agents search (`max_output_bytes`, "cap").
- Do the same for "the salvage cap logs nothing".

---

## g3 — retry-backoff-policy (v7, eval ce846459)

**Reward.** The mean is **0.92**, and **5/10 scored 1.00** (runs 1, 3, 4, 9 and 10). This is
the easiest task so far, but **the score overstates it**: three runs passed a fact while
shipping behaviour the answer key forbids (G3-A below, now fixed).

| run | rollout | reward | facts lost (cause) | note |
|---|---|---|---|---|
| 1 | ccc381f3 | 1.00 | — | code matches the key almost verbatim |
| 2 | 63d214a1 | 0.667 | r1.exclusions_or_crossover, r1.observability (not found: `l13` "we empty the attempts", dropped by its own keyword filter, which kept the neighbouring line); r2.rule (not found: rounding) | it abandoned full-context reading of its chat dump after about 180 lines ("Much noise") |
| 3 | dbcedd39 | 1.00 | — | **false pass**: `finish_reason=length` made TERMINAL through a new `InvalidFinishReasonError` |
| 4 | 34a87e12 | 1.00 | — | |
| 5 | 46cec654 | 0.889 | r2.rule (not found: rounding) | |
| 6 | 3b3fcb93 | 0.889 | r2.exclusions_or_crossover (**grader defect**, G3-B) | |
| 7 | 3111b210 | 0.889 | r2.rule (not found: rounding) | |
| 8 | cd046ece | 0.889 | r2.rule (not found: rounding) | **false pass**: `attempts_left = 0` at the call site, shipped as its own PR #738, "invalid finish_reasons fail out on the first" |
| 9 | 40be2bf1 | 1.00 | — | |
| 10 | f6e50c9e | 1.00 | — | **false pass**: a new `NonRetryableResponseError`, classified TERMINAL |

**Pass rates:** r2.rule 6/10; r1.exclusions 9/10; r1.observability 9/10; r2.exclusions
9/10. The other five facts are 10/10.

**Why the 7 lost fact-points were lost:**

| cause | points | share |
|---|---|---|
| not found | 6 | 86% |
| grader over-specifies | 1 | 14% |

### The one hard fact: rounding, stated once

`remaining_cooldown_seconds` must return `max(0.0, round(until - now, 3))`. The test
(`test_r2.py:113`) expects 508.0009 to come back as `8.001`.
- Only `g3.r2.s1c` (#pipeline, 2025-04-07) states the rounding.
- The ticket rounds a *different* function to three places (`round(raw * (0.5 + 0.5 * j),
  3)`, ticket line 137) but says nothing about rounding this one.
- Runs 2, 5, 7 and 8 shipped it unrounded, and none of them had found `s1c`.

### G3-A (fixed): an invented turn outvoted the plant, and the grader could not see it

`g3.r1.l1`'s plant record settles that "a contract failure should be charged more than one
attempt": CONTRACT, costing 2. The #code-review thread phase 4 built around it
(2025-06-03) ends with an **invented** turn from konrad at 14:12:

> and length wont fix itself on a retry anyway, so it stops being retryable, **fail it out
> on the first**

That line means TERMINAL. It is the same failure as g7's defect: the scaffolding argues
against the plant.

**The effect is exactly predictable from who saw the line.** Konrad's line appears in the
transcripts of runs 3, 8 and 10 and in no other transcript.

| runs | saw konrad's line | shipped `length` as terminal / non-retryable |
|---|---|---|
| 3, 8, 10 | yes | **3/3** |
| the other 7 | no | 0/7 (they got it right because they never read the thread, not because they weighed it) |

**No point is lost, because the grader cannot see the bug.** `test_r1.py:221–224` tests
only `policy.decide(ValueError("finish_reason was length"), ...)`. That call is classified
by the exception type, which is CONTRACT. A reclassification added at the call site is
never exercised. **These three 1.00s are false passes.**

The plant's own record confirms the turn is scaffolding, not the clue: `plant.json` lists
konrad 14:12 under `invented`, and its `pieces` entry logged it as "the decision:
length-truncated responses stop being retryable, fail on the first attempt", against
`l1`'s `settles`.

**Fixed 2026-09-11 and pushed as g3 v9.** Two parts:
- **The corpus.** konrad's 14:12 turn now reads "and length does come good on a retry now
  and then, so dont stop retrying it, it just shouldnt get as many goes as a timeout". That
  agrees with `l1`'s `settles` and uses none of its `forbidden_terms`. It changed in all
  eight carriers: the three world arms' plants, the answer key, both READMEs,
  `plant-data`, and `plant.json` (the `pieces` record included). The message count and
  turn 0 are unchanged, so the located map still holds.
- **The grader.** The observability fact now also runs a real `finish_reason="length"`
  response through `handle_single_request_with_retries`, and checks it is re-queued with
  `attempts_left` 1. g3 grades through the worker/judge split, so the check lives in
  `probe.py` (which records `[re-queued, attempts_left]` via
  `probe_support.drive_one_response`) and `judge.py` (which asserts `[1, 1]`). `test_r1.py`
  carries the same check as the human-readable reference.

Verified locally on scratch trees. The oracle passes 10/10 on the old and new suites.
A mutant that raises a TERMINAL error at the length check (runs 3 and 10), and one that
sets `attempts_left = 0` there (run 8), pass the old suite 10/10 and fail the new one on
exactly this assertion. The pristine tree fails everything. The same matrix holds on the
split grading path (probe in a jail, judge on the source), and the task's `spec` and
`naive` fixtures score the same before and after (10/10 and 1/10).

### G3-B (fixed): the grader checked for the name, not for reading it

The requirement is that `config.seconds_to_pause_on_rate_limit` is *no longer read*.
`test_r2.py:206` instead asserts that the **string** does not appear anywhere in
`inspect.getsource(BaseOnlineRequestProcessor)`, and that includes comments and docstrings.
Run 6 wrote a docstring explaining *why* the setting is unused, nearly quoting remark
`g3.r2.s4d`, and lost the fact for it.

**Fixed 2026-09-11 and pushed as g3 v9.** The check (in `judge.py`, and in `test_r2.py`
as the reference) now walks the class's syntax tree for
an attribute read, or an exact-name string as `getattr` would take, so prose no longer
counts. A mutant carrying run 6's docstring fails the old suite on this fact and passes
the new one.

### Herrings: no pressure

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `g3.r1.h1` → `rev1` | 10/10 | 9/10 | 0/10 |
| `g3.r1.h2` → `rev2` | 10/10 | 9/10 | 0/10 |
| `g3.r2.h1` → `rev1` | 9/10 | 10/10 | 0/10 |
| `g3.r2.h2` → `rev2` | 8/10 | 9/10 | 0/10 |

Run 1 explicitly reasoned about the dates: "Jan discussion said plain assignment, but the
Mar 24 and Apr 8 discussions explicitly changed it to max(). Latest wins".

### Which remarks go unfound

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 82% |
| plain English, no identifier | 70% |
| #code-review | 46/78 (59%, the lowest channel) |
| mail | 93% |
| wiki comments | 90% |

The least-found remarks were `g3.r2.s2a` (#cookbooks) at 1/10, and `g3.r2.s4c` and
`g3.r2.say23` (#code-review) at 1/10 each. All three have other carriers, so they cost
nothing.

### Owed for g3 (not applied)

- **The rest of the round trip for G3-A and G3-B:** v9 is pushed and passed the hosted validate (oracle 1.0 on all 16 subscores; noop 0 on
  every fact, its 0.0625 being `suite_ok` alone, as on 09-02). An opus
  eval on v9 has not been run.
- Give the rounding rule a second carrier.

---

## g4 — run-cache-identity (v5, eval 0ebb2b86)

**Reward.** The mean is **0.94 over the 8 runs that shipped**, or 0.75 across all 10.
**4/10 scored 1.00** (runs 4, 5, 7 and 8). Two runs scored 0 for reasons unrelated to the
hidden requirements:
- **Run 2 never shipped.** It never committed; it spent its remaining turns in a loop
  comparing its output against the baseline and ran out of budget.
- **Run 9 is infra.** Its terminal began echoing stale output about 1,500 lines before the
  end, and it spent 15 or more cycles re-checking the state of its work.

In both runs, the readers found the agent had reconstructed nearly every fact correctly in
its notes.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | 31a202dc | 0.875 | r1.scope (`fix27` scrolled past, never engaged) |
| 2 | 342998b2 | 0 | all 8 (never shipped) |
| 3 | 76b379d3 | 0.875 | r1.scope (`fix27` in view at line 4715, never cited) |
| 4 | ad4a75af | 1.00 | — |
| 5 | 3794f374 | 1.00 | — |
| 6 | ec814c80 | 0.875 | r1.scope (`fix27` was one line inside a `head -30` dump the next Analysis never touched) |
| 7 | 22c149ca | 1.00 | — |
| 8 | ad4ce258 | 1.00 | — |
| 9 | e157d675 | 0 | all 8 (infra: terminal echoing stale output) |
| 10 | 4359a8a5 | 0.875 | r2.failure_behavior (slip: `LLM.__call__` drops the caller's `run_id` when caching is on, so one refusal can't be reached; the agent's own test called the inner function directly) |

**Pass rates over the 8 runs that shipped:** r1.scope 5/8 and r2.failure_behavior 7/8.
The other six facts are 8/8. Only **4 lost fact-points** are knowledge losses: three on
`r1.scope` and one slip.

### The one hard fact: a rule stated as an observation

`LLM.backend_params` must hand back a fresh copy (`test_r1.py:157–163`). Only two remarks
carry this:
- **`g4.r1.fix27`** (#code-review, 2025-03-14): "popped batch_size off what
  llm.backend_params handed me, read it again and batch_size was still there, so mutating
  what you got back doesn't reach the LLM". This is **an observation, not a rule**: the
  reader has to infer "returns a copy".
- **`g4.r1.l-params-copy`** (#code-review, 2025-04-23) states it more directly. Only 3/10
  runs found it, and two of those never shipped.

**Every run saw `fix27`** (10/10). The outcome turned on whether the agent **drew the
inference**:

| runs | engaged with `fix27` | r1.scope |
|---|---|---|
| 4, 5, 7, 8, 10 | yes; e.g. run 4: "backend_params returns a copy (per chat: mutating the returned dict must not reach the LLM)" | passed |
| 1, 3, 6 | no; it scrolled past in a raw dump or a `head -30` | lost |

This is a *found ≠ used* loss, not a search loss.

### Why the rest was easy: redundancy

Readers describe every other fact as having 2–6 carriers. The agents found 67% of clue
remarks, so each fact had at least one carrier that most runs did find. Two good habits
also helped: runs 5 and 8 re-derived facts from `llm.py` itself, and run 5 amended its
commit after re-reading `g4.r2.l4`.

### Herrings: no pressure

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `backend-params-whole-dict-dario` → `rev1` | 7/8 | 8/8 | 0/8 |
| `backend-params-whole-dict-konrad` → `rev2` | 4/8 | 6/8 | 0/8 |
| `h1-uuid4-nocache` → `rev1` | 8/8 | 8/8 | 0/8 |
| `h2-isoformat-segment` → `rev2` | 5/8 | 8/8 | 0/8 |

Even runs that saw a herring without its reversal did not adopt it. Run 5 briefly believed
the `uuid4()` herring mid-investigation, then went back to the surrounding thread before
settling on the reversal.

### Which remarks go unfound

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 79% |
| plain English, no identifier | **40%** |

This is the widest gap between the two in any task: the agents grep for identifiers.

| channel | found |
|---|---|
| #help | 1/10 |
| #pipeline | 61% |
| #viewer | 65% |
| #releases | 95% |
| #incidents | 97% |
| #general | 100% |

The least-found remarks were `g4.r2.l2` (#pipeline) at 0/10, and `g4.r1.l-backend-resolved`
(#cookbooks) and `g4.r2.l1` (#help) at 1/10 each. All three were redundant.

### Owed for g4 (not applied)

- State the copy rule once as a rule, in a second place that search can reach (the wiki
  page on run identity, say), instead of relying on an observation plus one late
  #code-review remark.

---

## g6 — model-price-lookup (v6, eval 30b9f0dd)

**Reward.** The mean is **0.84 over the 8 live runs**, or 0.67 across all 10. **No run
scored 1.00.**

**Runs 1 and 3 are infra, and it is the same environment fault both times.** The agent
pushed and saw CI go green; run 1's deployed service even confirmed the feature. Then the
git remote reset to a commit from before the feature, so the grader saw the untouched
module:
- Run 1 hit "Author identity unknown", its terminal became unreliable, and
  `origin/main` came back pre-feature.
- Run 3's remote reverted to baseline `295ab6c` seven or more times.

Together with g4 run 9 (a terminal echoing stale output), that makes **three
late-run terminal or git-state faults across two tasks**. They need an environment
investigation, not a task fix.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | 468cd6fe | 0 | all 7 (infra: remote reset) |
| 2 | ce421264 | 0.857 | r2.observability (slip: a module-level set that is never cleared, so an earlier test in the suite contaminates it) |
| 3 | 1adecb6c | 0 | all 7 (infra: remote reset) |
| 4 | 18bbfdc9 | 0.857 | r1.observability (not found: the WS-050 wiki comment `l12`, on a page it never opened) |
| 5 | f6788014 | 0.857 | r2.exclusions (slip: read "the multiplier does not apply to caller supplied prices", never added the check) |
| 6 | 6887d254 | 0.714 | r1.observability (not found: `l12`); r2.exclusions (slip: made the flag a string `price_source` attribute) |
| 7 | e9fac7c8 | 0.857 | r1.observability (slip: wrote catch-and-return-0.0 in both trackers, never in the processors' `cost()`) |
| 8 | c69f70f0 | 0.857 | r2.exclusions (slip: built the class bool correctly, then 90 steps later turned it into a property backed by a JSON table) |
| 9 | ed6472ea | 0.857 | r2.exclusions (slip: wrote the rule as a code comment, never checked `config.in_mtok_cost`) |
| 10 | d949cdcf | 0.857 | r2.exclusions (slip: wired the flag for providers only, with no caller-price check) |

**Pass rates over the 8 live runs:** **r2.exclusions_or_crossover 3/8**,
r1.observability 5/8, r2.observability 7/8. The other four facts are 8/8.

**Why the 9 lost fact-points were lost:**

| cause | points | share |
|---|---|---|
| **implementation slip** | **7** | **78%** |
| not found | 2 | 22% |

**This is the task where agents most often knew the rule and built something else.**

### The hard fact: known, then not built

`r2.exclusions_or_crossover` has two graded parts, and runs slipped on each.

**1. A caller's own price is never discounted.** `batch_multiplier()` must return `1.0`
when the config carries an explicit input cost.
- Runs 5, 9 and 10 read this rule on wiki page 132 and its comments, and restated it. Run 9
  even wrote it as a code comment.
- None of the three added the `config.in_mtok_cost` check.

**2. The exemption is a flag on the class.** The mail `g6.r2.g6r2-s3-l3` and remark
`g6.r1.l7` both say "that eligibility to be a flag on the class, and for batch_multiplier
to read the flag".
- The grader accepts either a bool in the base class's `vars()` that is negated on the two
  exempt processors, or a per-class `batch_multiplier` override.
- Run 6 used a string attribute and run 8 used a property, so both failed the check even
  though the behaviour was right.
- The check is strict, but the world did ask for a flag.

**`r1.observability`:** every processor's `cost()` must catch `UnpricedModelError` and
return `0.0`. That is stated in `g6.r1.l12`, a comment on the WS-050 wiki page.
- Runs 4 and 6 never opened that page, although their own searches surfaced it repeatedly.
- Run 7 applied the pattern to the status trackers and not to the processors.

### Why the rest was easy

Four of the seven facts passed in every live run. Mail carriers were found 98% of the
time, and both reversals 100%.

### Herrings: no pressure

Each of g6's two herrings was seen directly by only 1/8 runs; the rest met them only as
recaps inside their reversals. Both reversals were read by 8/8 runs, and no run believed
either herring.

### Which remarks go unfound

| remark quality | found |
|---|---|
| **wiki comments** | **61% (34/56)** |
| chat | 62% |
| mail | 98% |
| carries an identifier that must be typed literally | 77% |
| plain English, no identifier | 50% |

The wiki losses are mostly triage: the agents fetch a few pages whole and skip pages whose
titles don't match their keywords.

### Version drift (harmless here)

Four readers independently found that mail `g6.r2.g6r2-s2-l4` reads with the *opposite*
meaning in the served v6 world compared with the repo's v7 key. The v6 wording still argues
for the graded rule, so it cost nothing.

### Owed for g6 (not applied)

- Investigate the git remote resets in runs 1 and 3 (and g4 run 9's stale terminal): 3
  runs zeroed by the environment.
- Consider stating the caller-price exemption where `batch_multiplier` is discussed. Every
  run that lost it had *read* it, so this is mainly an agent slip.

---

## g7 — agent-turn-ledger (v5, eval 8deffce4)

*Rerun on 2026-09-11. It replaces eval 94bf8242 (v4), whose results have been dropped. v5
serves the G7-A fix: nikolai's reply now reads "no, both sides" in all 10 transcripts.*

**Reward.** The mean is **0.76 over the 9 live runs**, or 0.69 across all 10. **No run
scored 1.00.**

Run 5 is infra. Its terminal went stale for the whole run and near the end showed false
"pushed / PR merged / CI green" output. The agent checked Gitea directly and found `main`
unchanged: its push had failed. It ran out of its 200 steps mid-repair, although its local
code had both requirements right.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | d7d2552c | 0.750 | r1.rule (not found: `TURN_LEDGER_FILENAME`); r1.scope (slip: merged "created" into "adopted"; its late patch fixed the wrong call site) |
| 2 | c22e6a99 | 0.875 | r1.observability (slip: stretched `fix30`, so a resumed run reports `created`) |
| 3 | e53e89fc | 0.875 | r1.rule (**grader defect G7-D**: swapped `write_sidecar`'s arguments; the world never states the order) |
| 4 | 625bf84c | 0.625 | r1.scope, r1.failure_behavior, r1.observability (not found: mail `l9`, "missing file is benign, we adopt the log"; its list of mail subjects was cut to the 40 most frequent by `head -40`, dropping it) |
| 5 | 8a514932 | 0 | all 8 (infra: stale terminal, the push never landed) |
| 6 | abbd1b41 | 0.875 | r1.rule (not found: `TURN_LEDGER_FILENAME`) |
| 7 | 9bd32b81 | 0.500 | r1.rule (not found); r1.scope, r1.failure_behavior, r1.observability (misread `fix27`: read "came back adopted both times" in full, then wrote missing sidecar → `created`) |
| 8 | 4df9fa70 | 0.875 | r1.rule (**G7-D**: swapped arguments) |
| 9 | bfd713dc | 0.875 | r1.rule (not found: `TURN_LEDGER_FILENAME`) |
| 10 | 41f9c9fd | 0.625 | r1.rule (not found); r1.scope, r1.observability (slip: `build_ledger`'s `status="verified"` default never overridden) |

**Pass rates over all 10 runs:** **r1.rule 2/10**, r1.scope 5/10, r1.observability 5/10,
r1.failure_behavior 7/10. Every r2 fact is 9/10, and the one miss is run 5.

**Why the 17 lost fact-points were lost** (not counting run 5's 8 infra points):

| cause | points |
|---|---|
| not found | 8 |
| implementation slip | 4 |
| found but misread | 3 |
| grader over-specifies (G7-D) | 2 |

### What the G7-A fix changed

| | v4 (old eval) | v5 (this eval) |
|---|---|---|
| lost to the corpus contradicting the grader | 8 | **0** |
| r1.failure_behavior passed | 4/10 | 7/10 |
| r1.observability passed | 2/10 | 5/10 |
| knowledge fact-points lost (live runs) | 21 | 17 |
| mean reward, live runs | 0.71 | 0.76 |

All ten runs read nikolai's corrected mail, and none left out `recorded_*`. **The fix
worked.** The score barely moved because the remaining r1 losses are elsewhere: the
filename constant, the argument order, and the status field.

### r1.rule: one unreachable name, one unstated order (2/10 passed)

**`TURN_LEDGER_FILENAME` still has one home**: `g7.r1.l2`, a comment on the off-topic page
"Weekly sync notes: week of Jun 2".

| runs | name in the transcript | r1.rule |
|---|---|---|
| 2, 4 | yes | passed |
| 3, 8 | yes | lost anyway, to the argument order (below) |
| 1, 6, 7, 9, 10 | no | **lost, 5/5** |

In the runs that missed it, the page surfaced in their own searches and was never opened.
Run 6's later sweep of pages skipped it because of a hard-coded range of page IDs.

**Grader defect G7-D: `write_sidecar`'s argument order is graded but never stated.**
- The grader calls `write_sidecar(working_dir, ledger)`.
- The only clause that pins the order, "you hand it the work dir and the ledger", is in the
  plant's summary of `g7.r1.say20`. The #engineering exchange that phase 4 rendered
  (2025-04-28) dropped it.
- It appears 0 times in the served `plant/messages.jsonl` and in none of the 10 transcripts,
  and no call signature appears anywhere in the corpus.
- Runs 3 and 8, and run 4 of the old eval, wrote `(ledger, working_dir)` and lost the fact.
- My first pass called this "borderline, the world implies it" on the strength of the
  answer key's summary. That was wrong.

### The status field, still the main source of slips (10 fact-points in 5 runs)

The three values `created`, `adopted` and `verified` are each set out in a different remark:

| value | remark | runs that found it |
|---|---|---|
| first write is `created` | `l8` | 6/10 |
| an absent sidecar is `adopted` | `fix27` ("came back adopted both times") | 10/10 |
| | mail `l9` ("missing file is benign") | 3/10 |
| a brand-new run stays `created` | `fix30` | 9/10 |

The runs misapplied them:
- **run 7** read `fix27` in full and wrote the opposite;
- **run 4** never saw `l9`, because `head -40` cut it from its list of mail subjects;
- **runs 1, 2 and 10** stretched `fix30` too far, or left the `verified` default in place.

This is the same pattern as the old eval, and it is not a defect: every value is stated
somewhere. But it spreads one decision across three remarks.

### Herrings: no pressure

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `g7-h1-checkpoint-authoritative` → `rev1` | 7/9 | 8/9 | 0/9 |
| `g7-h2-truncate-is-the-pattern` → `rev2` | 0/9 | 7/9 | 0/9 |
| `h1-sentinel-substring-ci` → `rev1` | 6/9 | 9/9 | 0/9 |
| `h2-sentinel-placement-free` → `rev2` | 2/9 | 8/9 | 0/9 |

All four reversals were found by 10/10 runs. r2 again scored perfectly in every live run
because both r2 reversals state the rule as code.

### Which remarks go unfound

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 83% |
| plain English, no identifier | **41%** |

| channel or surface | found |
|---|---|
| #releases | **0/10** |
| #viewer | 25% |
| the one wiki page body | 40% |
| #cookbooks | 45% |
| wiki comments | 82% |
| #pipeline | 81% |

### Owed for g7 (not applied)

- **G7-D:** re-render `g7.r1.say20` so that "hand it the work dir and the ledger" survives,
  or loosen the test to accept either argument order.
- Give `TURN_LEDGER_FILENAME` a second, searchable home in chat or mail. It cost 5 of the 9
  live runs `r1.rule`.
- Consider stating the three status values together in one remark. They are the largest
  source of slips.

---

## g8 — attachment-payload (v8, evals 30c95df4 + 66eb8a20 + 48fe71f7, pooled)

**Reward.** The mean is **0.86** over 10 runs, and **1/10 scored 1.00** (30c95df4 run 5).
One further rollout in eval 30c95df4 errored and was not read. All ten runs pushed, passed
CI and deployed. There were no infra losses.

| eval / run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 30c95df4 / 1 | 7e8d6c66 | 0.889 | r1.scope (not found: none of the whole-prompt remarks contain its search terms) |
| 30c95df4 / 2 | bb7a8be9 | 0.889 | r1.scope (talked itself out of it: "arguably a separate estimator") |
| 30c95df4 / 3 | 8bdfd136 | 0.778 | r1.rule (slip: hook placed in `_handle_multi_modal_prompt`); r2.failure_behavior (**task defect G8-A**) |
| 30c95df4 / 4 | 458ef5bd | 0.778 | r1.scope (folded the 45 MB total into its count check); r2.failure_behavior (**task defect G8-A**) |
| 30c95df4 / 5 | d6eabf95 | 1.00 | — |
| 30c95df4 / 6 | 320144bf | 0.889 | r1.scope (not found) |
| 30c95df4 / 7 | bf6f3ad8 | 0.889 | r1.scope (read the whole thread, filed it under "the batch planner / prompt size estimator... likely out of scope") |
| 48fe71f7 / 1 | 8a9deee3 | 0.889 | r1.rule (slip: hook placement) |
| 66eb8a20 / 1 | 28142e4d | 0.778 | r1.rule (slip: hook placement); r2.failure_behavior (not found: the "exactly one warning" remarks) |
| 66eb8a20 / 2 | 9fc94c4d | 0.778 | r1.scope (not found); r1.exclusions (misread: filed "URL blocks contribute nothing" as a token question) |

**Pass rates:** **r1.scope 4/10**, r1.rule 7/10, r2.failure_behavior 7/10,
r1.exclusions 9/10. The other five facts are 10/10.

**Why the 13 lost fact-points were lost:**

| cause | points | share |
|---|---|---|
| implementation slip | 4 | 31% |
| not found | 4 | 31% |
| found but misread | 3 | 23% |
| **task defect (G8-A)** | **2** | **15%** |

### The hard fact: the 45 MB whole-prompt ceiling, and one remark that says where it lives

`r1.scope` wants a whole-prompt size total checked in `_handle_multi_modal_prompt`, raising
`AttachmentTooLarge` with `kind="prompt"` above 45.0 MB. The number itself is easy to find:
`s2-dario` 9/10 and `s2-konrad` 9/9. What is not easy to find is *where it goes*. That is
**`g8.r1.s2-gideon`** (#code-review, 2025-03-17): "that total lives only in
`_handle_multi_modal_prompt`".

| runs | found `s2-gideon` | r1.scope |
|---|---|---|
| 48fe71f7/1, 66eb8a20/1, 30c95df4/3, 30c95df4/5 | yes | **passed, 4/4** |
| 30c95df4/4 | yes, but folded the total into its count check | lost |
| 30c95df4/1, /2, /6, /7, 66eb8a20/2 | no | **lost, 5/5** |

**The ticket makes the misreading easy.** Its non-goals say "Out of scope: the batch path
(`openai_batch_request_processor.py:66`)". Runs that had the number but not its location
filed it there instead:
- run 2: "arguably a separate estimator";
- run 7: "belongs to the batch planner / prompt size estimator... likely out of scope".

### Task defect G8-A: an invented turn talks `"auto"` out of the vocabulary

The grader wants `tuple(_SUPPORTED_IMAGE_DETAILS) == ("auto", "low", "high")`. Only
`g8.r2.l14` (#viewer) says "three entries, and index 0 is what the fallback hands back".
- The plant for `g8.r2.fix24` settles only that "low precedes high". Its forbidden terms
  deliberately include "three values", "auto goes first" and "index 0".
- The #pipeline thread phase 4 built around it (2025-05-13) adds two **invented** turns:
  emil's "it's just the two values plus auto, i believe", and nikolai's close, "**auto is a
  diffrent question imo it's not a detail level its a fallback**".
- Runs 3 and 4 had `fix24` but not `l14`, and shipped `("low", "high")`. Run 4 reasoned "auto
  is fallback not a member". Run 3 wrote "deliberately not in the vocabulary".
- This is the same failure as g3's konrad turn and g7's `fix28`: the scaffolding argues the
  graded question the wrong way.

### The repeated slip: hook placement

Three runs (48fe71f7/1, 66eb8a20/1 and 30c95df4/3) wrote in their own reasoning that
`AttachmentTooLarge` "fires inside `_canonical_attachment_block`, ahead of
`file_upload_limit_check`". They then called the hook from a later loop in
`_handle_multi_modal_prompt`. The grader builds a single block directly, so the hook never
fires. The world is explicit about the location, so this is fair.

### Herrings: no pressure

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `single-ceiling-dario` → `rev1` | 8/10 | 10/10 | 0/10 |
| `single-ceiling-konrad` → `rev2` | 4/10 | 10/10 | 0/10 |
| `detail-passthrough-1` → `rev1` | 7/10 | 9/10 | 0/10 |
| `detail-passthrough-2` → `rev2` | 8/10 | 10/10 | 0/10 |

### Which remarks go unfound

g8's corpus is chat only.

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 84% |
| plain English, no identifier | 59% |

| channel | found |
|---|---|
| #code-review | 63% |
| #pipeline | 66% |
| #engineering | 92% |
| #incidents | 98% |

Agents searched for "attachment", and `_handle_multi_modal_prompt` doesn't even contain
the substring "multimodal", because of the underscores. The remarks about the whole-prompt
total contain neither word.

### Owed for g8 (not applied)

- **G8-A:** rewrite the two invented turns around `fix24` so that neither removes `"auto"`
  from the vocabulary.
- Say plainly, in a second place, that the whole-prompt total lives in
  `_handle_multi_modal_prompt`. Or narrow the ticket's non-goal to name the batch
  *estimator* explicitly, so it no longer invites the misfiling.

---

## g9 — example-encoding (v8, eval 3b0b259f)

*Rerun on 2026-09-11. It replaces eval fffbd350 (v7), where 8 of 10 rollouts errored.*

**Reward.** The mean is **0.84**, and **1/10 scored 1.00** (run 7). All ten runs shipped,
passed CI and deployed. There were no infra losses.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | fe224554 | 0.714 | r1.failure_behavior (slip: clamped `window_start` at 0, left `retained_prompt_tokens` unclamped one line later, so it came out as −61); r2.failure_behavior (**herring followed**) |
| 2 | f7cf25ff | 0.857 | r1.failure_behavior (not found: `num_messages`; only `g9.r1.l-fail-3` names it) |
| 3 | 3ad4d147 | 0.857 | r2.failure_behavior (**herring followed**; it searched the wiki for "role sequence" and got nothing, because comments aren't indexed) |
| 4 | a22ae416 | 0.857 | r2.failure_behavior (**herring followed**; wrote "Also page 149 ... may help" and then fetched page 155 instead) |
| 5 | e776537c | 0.857 | r2.rule (slip: two copies of the masking rule drifted apart, the exact failure its own clue `l-scope-1` warns about) |
| 6 | e26f06c1 | 0.857 | r2.failure_behavior (**herring followed**) |
| 7 | 775a81a2 | 1.00 | — |
| 8 | 5c4fad06 | 0.714 | r1.rule (slip: flagged the right remark as "likely the newer decision", then built the old behaviour); r2.failure_behavior (**herring followed**: wrote "Confirmed") |
| 9 | 0b39d6d4 | 0.857 | r1.failure_behavior (not found: the field names, which are only in `l-fail-3`; it grepped chat for three proper nouns only) |
| 10 | 3f9184ba | 0.857 | r2.failure_behavior (**herring followed**; restated it almost verbatim in its own design notes) |

**Pass rates:** **r2.failure_behavior 4/10**, r1.failure_behavior 7/10, r1.rule 9/10,
r2.rule 9/10. The other three facts are 10/10.

**Why the 11 lost fact-points were lost:**

| cause | points | share |
|---|---|---|
| **herring followed** | **6** | **55%** |
| implementation slip | 3 | 27% |
| not found | 2 | 18% |

### The one herring that works: `h-role-row`

The graded rule is that `format_batch` absorbs only `ExampleTooLongError`, and
`InvalidRoleSequenceError` propagates and aborts the pass.
- **The herring** is a **mail**, `g9.r2.h-role-row` (dario, 2025-05-28): "Length and role
  sequence are row problems ... those get counted and skipped". Every run saw it.
- **Its only reversal**, `g9.r2.rev3`, and the one clue restating the rule, `l17`, are both
  **comments** on the wiki page `request-builder-what-we-drop-and-what-we-raise-on.md`
  (2025-06-17): "this is me contradicting myself ... only the over-long ones are row
  problems".
- BookStack search does not index comments, and the page's title doesn't mention
  `format_batch`.

| runs | saw the wiki-comment reversal | r2.failure_behavior |
|---|---|---|
| 2, 5, 7, 9 | yes | **passed, 4/4** |
| 1, 3, 4, 6, 8, 10 | no | **lost, 6/6: every one believed the herring and shipped `except (InvalidRoleSequenceError, ...)`** |

This is the one place in the whole set where a herring does what it was designed to do:
every run that reached the retraction dropped the herring, and every run that did not
believed it. It accounts for **6 fact-points, 55% of g9's losses**, and it is working as
intended.

### The refusal's fields (r1.failure_behavior, 7/10)

`ExampleTooLongError` must carry `retained_prompt_tokens` clamped at 0, `num_messages`, and
a fixed message. The attribute names and the message are only in `g9.r1.l-fail-3`
(#pipeline). Runs 2 and 9 never found it. Run 1 had it and forgot the clamp.

### Herrings otherwise: no pressure

g9's other four herrings were seen by 8–10 of 10 runs, and their reversals by 10/10 runs.
No run believed any of them. Run 7 reasoned it out explicitly: "January thread is the
superseded version. April is the settled rule".

### Which remarks go unfound

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 74% |
| plain English, no identifier | 55% |

| channel or surface | found |
|---|---|
| wiki comments | 60% |
| #engineering | 60% |
| #pipeline | 65% |
| mail | 75% |

### Owed for g9 (not applied)

- Give `l-fail-3`'s attribute names a second carrier.

---

## g10 — token-capacity-budget (v5, eval 5b468409)

**Reward.** The mean is **0.93 over the 9 live runs**, or 0.84 across all 10. **7/10
scored 1.00** (runs 1–5, 7 and 9). **This is the easiest task in the set.**

Run 8 never shipped. It had both requirements designed correctly by step 125 and a
passing smoke test. It then spent its last steps writing its own unit tests in small
pieces, fighting heredoc and JSON escaping (61 of 200 steps carry "Extra text detected
after JSON object" warnings), and ran out of steps without ever running `git add`.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1–5, 7, 9 | — | 1.00 | — |
| 6 | 1e9edef5 | 0.875 | r1.exclusions (not found: the release-side ceiling clamp; it saw only two isolated grep hits of that thread, then planned "Read code-review 1998-2012" and never did) |
| 8 | b2357bac | 0 | all 8 (never shipped) |
| 10 | 8dec3046 | 0.50 | r1.exclusions (slip: noted "release clamp ... happens quietly, not counted", never coded the upper clamp); r2.rule, r2.scope, r2.exclusions (not found, see below) |

**Pass rates over the 9 live runs:** r1.exclusions 7/9, and r2.rule, r2.scope and
r2.exclusions each 8/9. The other four facts are 9/9. Only 5 knowledge fact-points were
lost: 4 not found and 1 slip.

### Why it was easy: reversals that restate the whole design

Runs found only **62% of clue remarks**, yet seven were perfect. Readers describe every
fact as carried by 3–6 remarks. Above all, each reversal **restates the settled design in
one turn**:

| reversal | found |
|---|---|
| `g10.r1.rev1` | 10/10 |
| `g10.r2.rev1` | 9/10 |
| `g10.r2.rev2` | 9/10 |

Run 1's reader: every fact passed "especially \[because of\] two reversal messages ... that
each restate a whole settled design in one turn". The mechanism is the same one that made
g7's r2 and g1's r2 easy. The herring and reversal pair, meant to *add* difficulty, gives
the answer to anyone who greps for the topic.

### Where it bit: one run searched in r1's vocabulary only

Run 10 searched chat with `clamp|counter|debt`. That matched r1 (13 of 20 remarks, both
herrings, both reversals) but almost none of r2's vocabulary (slot, requeue,
`finish_reason`).
- It found **4 of 26 r2 remarks and neither r2 reversal**.
- It then invented a rule, settle the refund against the reported usage, which is **exactly
  the wrong alternative the answer key names** ("settlement against reported usage ...
  8300.0").

### Herrings: no pressure

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `clamp-at-zero-decision` → `rev1` | 8/9 | 9/9 | 0/9 |
| `clamp-at-zero-rationale` → `rev2` | 8/9 | 9/9 | 0/9 |
| `r2.h1` → `rev1` | 6/9 | 8/9 | 0/9 |
| `r2.h2` → `rev2` | 8/9 | 8/9 | 0/9 |

### Which remarks go unfound

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 84% |
| plain English, no identifier | 52% |

| channel | found |
|---|---|
| #help | 3/10 |
| #engineering | 48% |
| #cookbooks | 56% |
| #code-review | 83% |
| #incidents | 90% |

Six clue remarks were found by only 1/10 runs, all early "s1/s2" leaves in #engineering and
#pipeline. All six were redundant.

Several readers caught a false positive in the pointer sheet: the automated text match for
`g10.r2.h1` hit the repo's own source code, not the chat message. Findings come from the
readers, so this did not affect the numbers.

### Owed for g10

- Nothing in the corpus is wrong. The lesson is a design one, shared with g1, g3 and g7:
  **a reversal that restates the finished design makes the requirement cheap**. To keep
  the difficulty, a reversal should retract the herring without restating the whole
  answer.

---

## g11 — training-step-ledger (v7, eval 94bf8242)

**Reward.** The mean is **0.86**, and **2/10 scored 1.00** (runs 2 and 8). All ten runs
shipped, and there were no infra losses. Run 7 fought git remote rollbacks, losing about
four pushes, before one stuck.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | 3347ed25 | 0.556 | r1.failure_behavior (not found: the merge); r2.rule, r2.exclusions, r2.observability (**herring followed**, G11-H) |
| 2 | 22513549 | 1.00 | — |
| 3 | dc2703c8 | 0.889 | r2.rule (not found: `min_lr_ratio` keyword-only) |
| 4 | d6f00008 | 0.778 | r1.rule (not found: `CHECKPOINT_NAME_TEMPLATE`, from `l3`); r1.failure_behavior (not found: the merge) |
| 5 | 2f540570 | 0.889 | r2.rule (not found: keyword-only) |
| 6 | f8059d35 | 0.889 | r1.failure_behavior (the merge: its planned read of #releases scrolled past the answer) |
| 7 | 66a0621c | 0.889 | r1.failure_behavior (the merge: `l17` came up only as its opening question) |
| 8 | fa827d89 | 1.00 | — |
| 9 | 1daa88e2 | 0.889 | r2.rule (not found: keyword-only; its #code-review reads stopped at 2025-04-14) |
| 10 | eb0dccde | 0.778 | r1.scope, r1.observability (not found: `l11`, "leave the interval and the per-epoch triggers gated on their config fields"; its own manual check showed the bug and it read that as confirmation) |

**Pass rates:** r1.failure_behavior 6/10 and r2.rule 6/10. The other seven facts are
9/10 or 10/10.

**Why the 13 lost fact-points were lost:**

| cause | points |
|---|---|
| not found | 10 |
| **herring followed** | **3; with g9's six, one of only two herrings that worked anywhere** |

### Two single-carrier rules decide most of the score

**`min_lr_ratio` sits behind a bare `*` (keyword-only).** Only `g11.r2.l10` (#code-review,
2025-05-30) says so; the ticket makes only `clock` and `rng` keyword-only.

| runs | found `l10` | r2.rule |
|---|---|---|
| 2, 4, 6, 7, 8, 10 | yes | **passed, 6/6** |
| 1, 3, 5, 9 | no (the wording is absent from their transcripts) | **lost, 4/4** (run 1's through the herring) |

Run 9 wrote `min_lr_ratio` dozens of times in its own reasoning and never searched for it.

**A repeated save merges the `reasons` tuples.** `l16` (#pipeline) says only that a
matching name "replaces" the last row. The merge is in `l17` (#releases, 2025-03-19): "the
updated row takes the newer loss and carries both **label sets** forward".
- It is phrased with a synonym: every graded identifier says `reasons`.
- Most runs met it as a single search hit showing only the opening question, never the
  answer below it.
- Runs 1, 4, 6 and 7 lost the fact. Runs 6 and 7 implemented `l16`'s "replaces" faithfully,
  as an overwrite.

### Task defect G11-H: a half-reversed herring, one of only two that worked

- konrad's herring (#viewer, 2025-02-19) makes **two** claims: the decay "lands at exactly
  zero", and warmup keeps the strict `step < warmup_steps` compare.
- Its registered reversal, `rev2` (#general, 2025-06-02), retracts **only the warmup
  compare**.
- The decay-to-zero claim is retracted only by `rev1` (#help, 2025-03-26: `MIN_LR_RATIO =
  0.1`), which is registered against the *other* herring.

Run 1 found konrad's herring and `rev2` but never `rev1`. It read `rev2` as confirming
"decay reaches exactly zero" and shipped a 0.0 floor. **It is one of only two herrings that worked in the whole set; the other is g9's `h-role-row`.** It happened because a reversal left
half of its herring standing.

### Herrings otherwise

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `ledger-twin-checkpoints-dario` → `rev1` | 8/10 | 9/10 | 0/10 |
| `ledger-twin-checkpoints-emil` → `rev2` | 9/10 | 10/10 | 0/10 |
| `lr-decay-to-zero-dario` → `rev1` | 9/10 | 9/10 | 1/10 (run 1) |
| `lr-decay-to-zero-konrad` → `rev2` | 10/10 | 10/10 | 1/10 (run 1) |

Run 5 briefly believed the r2 herring and corrected itself within two turns.

### Which remarks go unfound

g11's corpus is chat only.

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 83% |
| plain English, no identifier | 67% |

| channel | found |
|---|---|
| #incidents | 60% |
| #general | 62% |
| #releases | 92% |

### Owed for g11 (not applied)

- **G11-H:** make `rev2` retract konrad's *whole* herring, or split the herring into two
  claims with one reversal each.
- Say "reasons" (not "label sets") in the merge carrier, and give the merge and the
  keyword-only rule a second carrier each.

---

## Register: every defect and fault found

Every entry below was checked by hand against the answer key, the plant record, the
ticket, the grader or the transcript. The evidence for each ruling is in
`tasks/rollout_analysis/readers/corrections.md`. **Fixed: G7-A (verified on Horizon), and
G3-A, G3-A′ and G3-B (pushed as g3 v9, verified locally; no eval on v9 yet).** Everything
else is open.

### Task defects: the world argues against the grader, or hides the answer

| id | task | what | cost |
|---|---|---|---|
| G7-A | g7 | nikolai's v4 reply, "yes, the log side only", contradicted the grader's `recorded_*` attributes | 8 points in v4. **Fixed in v5 and verified**: all 10 v5 runs read "no, both sides", and it cost 0 points |
| G3-A | g3 | konrad's invented "fail it out on the first" makes `finish_reason=length` terminal; the plant says contract, costing 2 | **3 false passes** (runs 3, 8, 10: saw the line in 3/3 cases and followed it); the grader could not see the bug. **Fixed in g3 v9 (2026-09-11)**: turn rewritten |
| G11-H | g11 | konrad's herring makes two claims; its registered reversal retracts only one ("decay to exactly zero" survives) | 3 fact-points (run 1) |
| G8-A | g8 | invented turns around `fix24` ("auto ... it's not a detail level its a fallback") drop `"auto"` from the vocabulary | 2 fact-points (30c95df4 runs 3, 4) |

### Grader defects

| id | task | what | cost |
|---|---|---|---|
| G7-D | g7 | `write_sidecar`'s argument order is graded, but the only clause stating it ("you hand it the work dir and the ledger", `g7.r1.say20`) was planted and then **dropped when phase 4 rendered the exchange**: 0 hits in the served corpus or in any transcript | 2 fact-points in v5 (runs 3, 8), and 1 in v4. My first pass called it "borderline" on the strength of the answer key's summary; that was wrong |
| G3-B | g3 | `test_r2.py:206` checks that the setting's *name* is absent from the source, docstrings included; the requirement is only that it is never read | 1 (run 6). **Fixed in g3 v9 (2026-09-11)**: an AST check |
| G3-A′ | g3 | the only `finish_reason=length` test goes through `policy.decide(ValueError)`, so a reclassification at the call site passes | masked the 3 false passes above. **Fixed in g3 v9 (2026-09-11)**: a request-path case |

### Graded names or orders with a single, hard-to-reach home

These are fair, but brittle: each test measures whether a run happened to open one place.

| task | graded thing | its only home | runs that found it | points |
|---|---|---|---|---|
| g1 | `plan_fingerprint` | `l6`, hedged ("or something in that direction"); 3 remarks say `plan_id` | seen 9/10; 3 runs named it `plan_id` | 7 |
| g1 | `PLAN_FILE_NAME` | a *nested reply* in a wiki comment thread | 6/10 | 4 |
| g1 | "plan written before the first request file" | `l16`, plain English | 3/10 | 2 |
| g2 | `OutputCapError` | `l-floor-nikolai`, #cookbooks | 4/10 | — |
| g2 | `.max_bytes` plus the message | `l-floor-konrad`, #cookbooks | **1/10**; `failure_behavior` passed only in that run | 8 |
| g3 | rounding to 3 places | `s1c`, #pipeline | the 4 runs that lost it all missed it | 4 |
| g7 | `TURN_LEDGER_FILENAME` | a comment on the off-topic "Weekly sync notes" page | 4/10 (v5) | 5 (runs 1, 6, 7, 9, 10) |
| g8 | where the 45 MB total lives | `s2-gideon`, #code-review | 5/10; found → 4/5 passed, not found → 0/5 | 5 |
| g9 | `ExampleTooLongError`'s attribute names and message | `l-fail-3`, #pipeline | 8/10 | 2 (runs 2, 9) |
| g11 | `min_lr_ratio` is keyword-only | `l10`, #code-review | 6/10; found → 6/6 passed, not found → 0/4 | 4 |

### Ticket-invited misreading

- **g8:** the non-goal "Out of scope: the batch path" gave runs 2 and 7 somewhere to file
  the whole-prompt ceiling ("belongs to the batch planner ... out of scope").

### Environment faults (infra; not the task, not the agent)

| run | fault |
|---|---|
| g6 runs 1, 3 | the **git remote reset** to a commit from before the feature, after a green CI (run 1 had even confirmed the deploy) |
| g11 run 7 | the same remote rollback, **survived**: it lost pushes about four times before `ea24b6d` stuck and went green (reward 0.889) |
| g4 run 9 | the **terminal echoed stale output** for about 1,500 lines, with 15+ cycles re-checking the state of its work; it never pushed |
| g7 run 5 (v5) | the **terminal went stale** for the whole run and near the end showed false "pushed / PR merged / CI green" output; the push had failed, and the run ran out of its 200 steps mid-repair |
| world CI | the "tests" step logs `No module named pytest` and still **reports success** (seen by g11 run 2, which ran the suite itself) |
| errored rollouts | g8 1; g11 eval 3c71bf59 **10/10** (not read). g9's v7 eval, 8/10 errored, was replaced by the v8 rerun |

### Agent failures to ship (kept out of the knowledge figures)

| run | what happened |
|---|---|
| g2 run 8 | built `output_cap.py`, never wired it in, declared the work complete, looped until the 7200 s kill |
| g4 run 2 | never committed; spent its remaining turns in a loop comparing against the baseline until the budget ran out |
| g10 run 8 | never committed; its last steps went on writing tests in small pieces, fighting heredoc escaping |

### Version drift

- **g6:** mail `g6r2-s2-l4` reads with the opposite meaning in the served v6 world compared
  with the repo's v7 key. The v6 wording still argues for the graded rule, so it cost
  nothing.
- **g7:** the v4 drift (the key carried the unpushed G7-A fix) is gone. The v5 world and
  the key match.

### Measurement notes

- Horizon's `extracted_score` is the mean of every subscore and overstates the task reward.
  This document uses `reward`.
- Reader verdicts I overruled after checking are all logged with evidence in
  `tasks/rollout_analysis/readers/corrections.md`. Several involved false claims about the
  ticket or false "only carrier" claims. One overruled entry was my own: G7-D.
- The pre-pass pointer sheet had a few false positives: `g10.r2.h1` matched the repo's own
  source code, and `g6`'s `s1-l1` matched on the word "The". Found or not always comes from
  the readers, so these did not affect the numbers.
- The superseded g7 (v4) and g9 (v7) reader verdicts are archived in
  `tasks/rollout_analysis/readers/_superseded/`. None of them feed any number here.
