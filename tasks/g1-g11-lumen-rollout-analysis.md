# g1–g11 lumen rollouts, read against the answer key (2026-09-11)

The `world-hosted` (blind) arm of every g-task, model `lumen` (Opus 5), agent `typhoon`,
at each task's latest version with a 10-run eval. **Every transcript was read against
that task's answer key, remark by remark**: whether the agent found each planted remark,
how it found it, what its `Analysis:`/`Plan:` said about it, and whether the shipped code
followed it. Herrings and reversals got the same treatment. Scores are Horizon's own
grades.

Status: **complete**. **g3, g7, g9 and g11 were re-evaluated on 2026-09-11** (g3 v9, g7 v5, g9 v8, g11 v11), and their sections replace the earlier evals, whose results are dropped. 100 rollouts are read: 99 scored, plus g2's execution failure. The summary is directly below; the per-task sections and the defect register follow.

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
     question the other way. After review, no loss is left in this cause.
   - `implementation_slip`, meaning the agent's reasoning states the rule and its code does
     otherwise.
   - `grader_overspecifies`; its only two cases (g7 runs 3 and 8, on `write_sidecar`'s
     argument order) are left out of the cause figures, because the grader has since been
     changed to accept either order
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
read the shortest transcript (a g7 run of the superseded v4 eval). The g3, g7, g9 and g11 reruns
were read on Sonnet too.

| task | version | eval(s) | lumen runs read |
|---|---|---|---|
| g1 batch-payload-plan | v14 | 8db49761 | 10 |
| g2 executor-output-cap | v11 | 9f2db992 | 10 (1 execution failure) |
| g3 retry-backoff-policy | **v9** | **035777f5** (rerun on the corpus and grader fix; replaces v7 ce846459) | 10 |
| g4 run-cache-identity | v5 | 0ebb2b86 | 10 |
| g6 model-price-lookup | v6 | 30b9f0dd | 10 |
| g7 agent-turn-ledger | **v5** | **8deffce4** (rerun; replaces v4 94bf8242) | 10 |
| g8 attachment-payload | v8 | 30c95df4 + 66eb8a20 + 48fe71f7, pooled on one version | 10 (+1 errored, not read) |
| g9 example-encoding | **v8** | **3b0b259f** (rerun; replaces v7 fffbd350, which had only 2 scored runs) | 10 |
| g10 token-capacity-budget | v5 | 5b468409 | 10 |
| g11 training-step-ledger | **v11** | **a8572080** (rerun on the herring fix; replaces v7 94bf8242) | 10 |

There is no g5 world-hosted task.

---

## Findings at a glance

All rates are pooled over all ten tasks (g1–g4 and g6–g11), using **live runs** only: runs
that shipped and were not zeroed by infra. g3, g7, g9 and g11 use their 2026-09-11 reruns.

### Where the remarks live: chat only, or spread across chat, wiki and mail

Four tasks keep every remark in Mattermost. Three put a handful in mail and wiki comments,
and three spread them widely:

| group | tasks | remarks in chat | mean reward (live) | found on chat | found off chat | knowledge points lost per live run | not-found points whose missing remark was off chat |
|---|---|---|---|---|---|---|---|
| **chat only** | g4, g8, g10, g11 | 100% | **0.89** | 74% | — | **0.95** | 0/19 |
| mostly chat | g1, g2, g3 | 83–90% | 0.85 | 76% | 85% | 1.39 | 7/26 (27%) |
| spread | g6, g7, g9 | 51–67% | 0.82 | 67% | 72% | 1.30 | **10/12 (83%)** |

| task | remarks by surface | mean reward (live) | found on chat | found off chat |
|---|---|---|---|---|
| g4 | chat 48 | 0.94 | 70% | — |
| g10 | chat 46 | 0.93 | 66% | — |
| g8 | chat 51 | 0.86 | 79% | — |
| g11 | chat 47 | 0.86 | 80% | — |
| g3 | chat 44, mail 3, wiki comment 2 | 0.93 | 87% | 78% |
| g2 | chat 38, mail 5, wiki comment 3 | 0.85 | 73% | 96% |
| g1 | chat 44, mail 4, wiki comment 2 | 0.79 | 69% | 76% |
| g9 | chat 29, wiki comment 15, mail 13 | 0.84 | 70% | 67% |
| g6 | chat 19, wiki comment 7, mail 6, wiki page 1 | 0.84 | 62% | 78% |
| g7 | chat 34, mail 8, wiki comment 8, wiki page 1 | 0.76 | 66% | 75% |

Did it matter? Somewhat, and not in the obvious way:
- **Chat-only tasks scored highest and lost the fewest points:** 0.89 against 0.85 and 0.82,
  and under one knowledge point per live run against 1.3 to 1.4.
- **Spreading does not hide remarks.** In both mixed groups the off-chat remarks were found
  *more* often than the chat ones (85% against 76%, and 72% against 67%). Agents read mail
  and wiki pages whole; chat is where the volume is, and a grep can pass a remark by.
- **Wiki comments are the exception** (68% pooled, and 45% for a comment added to an
  existing page). BookStack search does not index them, so a run finds one only by
  fetching every page's comments.
- **What spreading changes is where the misses land.** In the spread tasks, 10 of the 12
  not-found points involved a remark off chat, 8 of them in g7, whose graded filename
  constant lives only in a comment on an off-topic page. In the chat-only tasks it was 0 of
  19. g9's six herring losses are the same effect under another cause: the reversal is in
  wiki comments.
- **Caveat:** ten tasks, and they differ in more than their surfaces (g10's reversals
  restate the whole answer; g7 has a graded name with one home). Read this as a
  correlation, not a measured effect.

### Difficulty ranking

| task | mean reward (live runs) | runs at 1.00 | hardest fact | why it is hard, or easy |
|---|---|---|---|---|
| g7 agent-turn-ledger | **0.76** | 0/10 | r1.rule 2/10 | the graded filename constant lives in one comment on an off-topic page |
| g1 batch-payload-plan | 0.79 | 3/10 | r1.rule, r1.scope 3/10 | the function name is hedged (`plan_fingerprint` "or something"), and 3 other remarks say `plan_id`; the constant lives in a nested comment reply |
| g6 model-price-lookup | 0.84 | 0/10 | r2.exclusions 3/8 | **known, then not built**: 78% of losses are slips |
| g9 example-encoding | 0.84 | 1/10 | r2.failure_behavior 4/10 | its mail herring is the one that works: the 6 runs that never opened the comments on the "request builder" page, where the reversal is, believed it |
| g2 executor-output-cap | 0.85 | 0/10 | r1.failure_behavior **1/9** | two graded names, each with one home, both in the quiet #cookbooks |
| g8 attachment-payload | 0.86 | 1/10 | r1.scope 4/10 | only one remark says *where* the 45 MB total lives, and the ticket's "out of scope: the batch path" invites misfiling it |
| g11 training-step-ledger | 0.86 | 2/10 | r1.failure_behavior, r2.rule 7/10 | the merge and the keyword-only rule each have a single carrier |
| g3 retry-backoff-policy | 0.93 | **6/10** | r2.rule 6/9 | rounding to three decimals is stated once, and 3 runs missed it; everything else has several carriers |
| g10 token-capacity-budget | 0.93 | **7/10** | r1.exclusions 7/9 | each reversal restates the whole design in one turn |
| g4 run-cache-identity | 0.94 | 4/10 | r1.scope 5/8 | the copy rule is stated as an observation, not a rule |

### 1. Half of all losses are search misses, and nearly all of those are single-home remarks

109 knowledge fact-points were lost in live runs:

| cause | points | share |
|---|---|---|
| not found | 57 | **52%** |
| implementation slip | 27 | 25% |
| found but misread | 18 | 17% |
| herring followed | 7 | 6% |

Almost every "not found" traces back to a **graded name, value or order that is stated in
exactly one remark**. The single-home table in the Register lists them. Whether a run found
that one place decides the fact:

| single-home remark | found → passed | not found → passed |
|---|---|---|
| g11 `l10` | 7/7 | 0/3 |
| g8 `s2-gideon` | 4/5 | 0/5 |
| g2 `l-floor-konrad` | 1/1 | 0/8 |
| g7 `TURN_LEDGER_FILENAME` | 2/4 (the other two lost r1.rule on `write_sidecar`'s argument order) | 0/5 |
| g9's only reversal, `rev3` | 4/4 | 0/6 |

### 2. Which clue qualities go unfound

"Found" means seen at least partially.

| quality | found | vs. | found |
|---|---|---|---|
| **carries an identifier** that must be typed literally | **79%** | plain English, no identifier | **60%** |
| its own chat thread | 76% | **dropped into an existing conversation** | **64%** |
| a new wiki page | 80% | **a comment on an existing page** | **45%** |
| mail (new 80%, reply 93%) | 82% | wiki page bodies | 62% |

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
remaining few percent fall disproportionately on graded facts: **45 of the 109 lost points
(41%) came from runs that had the remark**. The recurring shapes:
- a rule stated as an observation, which agents read without drawing the inference (g4
  `fix27`);
- a rule read in full and then written backwards (g7 run 7, with g7's `fix27`; g3 run 9, with
  mail `l12`);
- deciding a requirement is out of scope (g1 run 4: "a distractor"; g8: "the batch
  estimator");
- naming slips (g1's `plan_id`);
- the right rule at the wrong call site (g6 trackers versus processors; g8 hook placement);
- two copies of one rule that drift apart (g9 run 5).

g6's losses are 78% slips.

### 4. Herrings work only when the run never reaches the reversal

| what the run saw (362 run–herring pairs) | believed the herring and shipped it |
|---|---|
| the herring and its reversal | **0/270 (0%)** |
| **the herring but not its reversal** | **7/12 (58%)** |
| the reversal but not the herring | 0/69 |
| neither | 0/11 |
| **overall** | **7/362 (2%)** |

Reversals are the most-found kind of remark (95%). They quote the herring, call it dead,
and share its keywords, so the grep that finds the herring usually finds the reversal too,
and then the herring does nothing.

It worked in two places:
- **g9 `h-role-row`, 6 runs:** its reversal is a comment on the "request builder" wiki
  page, and those six runs never opened that page's comments.
- **g11's konrad herring, 1 run (run 7):** it never reached the reversal in #general.

And many reversals *restate the full answer*, which makes their requirement cheap: g1 r2,
g7 r2 and all of g10 are near-perfect for this reason.

**Invented lines can still mislead a run that misses the remark that settles the
question.** Phase 4 writes conversation around each planted remark, and a few of its lines
point the other way: nikolai's "auto ... it's not a detail level its a fallback" in g8 (runs
3 and 4, neither of which found `l14`), and konrad's "sets it to none" in g3 (run 10, which
never found `s1a`). In both, the right answer is stated elsewhere in the corpus, so these
losses count as not found or misread, not as defects.

### 5. Hardest fact type

| fact type | pass rate (live runs) |
|---|---|
| failure_behavior | 77% |
| rule | 85% |
| scope | 86% |
| observability | 86% |
| exclusions_or_crossover | 92% |

### 6. The measurement is noisier than the task

64 fact-points were lost in dead runs:
- **14 to infra**: g6 runs 1 and 3. After a green CI the whole sandbox rolled back to its
  starting state, again and again: the agent's local clone, working tree and `/tmp` files as
  well as the remote. Nothing in the world's own code can do this; it points at Horizon's sandbox being restored mid-run.
- **50 to runs that never shipped** (g2 run 8, g3 run 3, g4 runs 2 and 9, g7 run 5, g10 run
  8). Three of them believed things their terminal never showed. g3 run 3 claimed a commit,
  a green CI and a deploy. g7 run 5 cited a commit hash and merged PRs that appear only in
  its own reasoning. g4 run 9 decided its real output was stale and committed only at the very
  end, never pushing.

On top of that, g11's eval 3c71bf59 errored 10/10, and the world's CI "tests" step passes
without pytest installed. Horizon's `extracted_score` also overstates the task reward.

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

## g3 — retry-backoff-policy (v9, eval 035777f5)

*Rerun on 2026-09-11, on the corpus and grader fix. It replaces eval ce846459 (v7), whose
results are dropped.*

**Reward.** The mean is **0.93 over the 9 live runs**, or 0.83 across all 10. **6/10 scored
1.00** (runs 1, 2, 4, 5, 7 and 8). Run 3 never shipped.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | c77a4f1b | 1.00 | — |
| 2 | c81e9802 | 1.00 | — |
| 3 | 178c95a5 | 0 | all 9 (never shipped: its patch scripts never landed, it typed no `git commit` or `git push`, and its last turns claimed commit 2eaeb50a, a green CI and a deploy) |
| 4 | 62797bad | 1.00 | — |
| 5 | 3e70faf7 | 1.00 | — |
| 6 | 0d78fdbb | 0.889 | r2.rule (not found: the rounding, `s1c`) |
| 7 | d13866db | 1.00 | — |
| 8 | 53fe95b3 | 1.00 | — |
| 9 | 445beca6 | 0.667 | r1.exclusions_or_crossover, r1.observability (misread: it read mail `l12`, "once auth is the problem the attempts on the clock are worth nothing", then shipped a terminal failure that costs nothing and leaves the budget intact); r2.rule (not found: it saw only the opening question of `s1c`) |
| 10 | 6880e992 | 0.778 | r2.rule, r2.observability (not found: `s1a`, the one remark that says the cooldown field is `0.0` on a fresh tracker; it shipped `None`) |

**Pass rates over the 9 live runs:** r2.rule 6/9; r1.exclusions, r1.observability and
r2.observability 8/9 each. The other five facts are 9/9.

**Why the 6 lost fact-points were lost** (not counting run 3's 9):

| cause | points |
|---|---|
| not found | 4 |
| found but misread | 2 |

### The fix held: no run made `length` terminal

In v7, konrad's invented turn in the #code-review thread around `l1` said `length` "stops
being retryable, fail it out on the first". Three runs followed it and the grader could not
see it. In v9 the turn reads "length does come good on a retry now and then, so dont stop
retrying it, it just shouldnt get as many goes as a timeout", and the grader also runs a
real `length` response through the request path.

| runs | saw the rewritten turn | shipped `length` as contract, charged 2, retried |
|---|---|---|
| 2, 5, 6, 8, 9, 10 | yes | 6/6 |
| 1, 4, 7 | no | 3/3, from the ticket's `ValueError` → CONTRACT row and `l2` |

Run 8's closing self-review ties its choice to the turn (transcript line 8921). The
request-path check passed in all 8 live runs whose r1 observability test reached it; run
9's stopped earlier, on the terminal row.

### The hard fact is still rounding, stated once

`remaining_cooldown_seconds` must return `max(0.0, round(until - now, 3))`, and only
`g3.r2.s1c` (#pipeline, 2025-04-07) says to round.

| runs | saw `s1c` | r2.rule |
|---|---|---|
| 1, 2, 4, 5, 7, 8 | yes | **passed, 6/6** |
| 9 | its opening question only | lost |
| 6, 10 | no | lost |

### An unretracted line points the cooldown at `None`

Herring `h2`'s exchange (#cookbooks, 2025-01-22) ends with an invented line that nothing
takes back:

```
15:45  dermot    does the clear-on-success path hit that same line
15:47  konrad    no thats its own reset, sets it to none
```

`rev2` retracts the herring's overwrite claim, not this. The one remark that settles the
field's value is `s1a`, a wiki comment: "on a fresh tracker though what does it come up as,
none or a number" / "0.0 like the other timers". Run 10 never found `s1a`, took the `h2`
line at face value, and shipped `throttle_cooldown_until: float | None = None` plus a
`clear_cooldown()` nobody asked for. It lost r2.rule and r2.observability. Every other live
run started the field at `0.0`. The loss is counted as not found, because the run never had
the settling remark in view.

### Herrings: no pressure

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `g3.r1.h1` → `rev1` | 9/9 | 9/9 | 0/9 |
| `g3.r1.h2` → `rev2` | 8/9 | 9/9 | 0/9 |
| `g3.r2.h1` → `rev1` | 9/9 | 9/9 | 0/9 |
| `g3.r2.h2` → `rev2` | 9/9 | 9/9 | 0/9 (its tail line is the `None` above) |

### Which remarks go unfound

Every run dumped chat, wiki and mail to disk and grepped them; the misses come from the
words each run chose to grep for.

| surface | found (live runs) |
|---|---|
| mail | 89% |
| chat | 87% |
| wiki comments | **61%** (`s1a` 5/9, `l5` 6/9) |

The least-found remarks were `g3.r2.s2a` (#cookbooks) at 2/9, and `g3.r2.say23` and
`g3.r2.s4c` (#code-review) at 3/9 each. All three have other carriers, so they cost
nothing.

### Owed for g3 (not applied)

- Give the rounding rule a second carrier. It decided r2.rule in all three live runs that
  lost it.
- Refresh the key's quote of `l15`: it still shows konrad's pre-09-08 15:19 line.

---

## g4 — run-cache-identity (v5, eval 0ebb2b86)

**Reward.** The mean is **0.94 over the 8 runs that shipped**, or 0.75 across all 10.
**4/10 scored 1.00** (runs 4, 5, 7 and 8). Two runs scored 0 for reasons unrelated to the
hidden requirements:
- **Run 2 never shipped.** It never committed; it spent its remaining turns in a loop
  comparing its output against the baseline and ran out of budget.
- **Run 9 never shipped.** About 1,500 lines before the end it decided its terminal was
  showing stale output, though every screen was a fresh capture, and spent 15 or more cycles
  re-checking its work. It committed only at the very end and never pushed.

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
| 9 | e157d675 | 0 | all 8 (never shipped: distrusted real output, committed at the end, never pushed) |
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
whole sandbox rolled back to its starting state, remote included, so the grader saw the
untouched module:
- Run 1 hit "Author identity unknown", its terminal became unreliable, and
  `origin/main` came back pre-feature.
- Run 3's remote reverted to baseline `295ab6c` seven or more times.

The agent's own local clone, working tree and `/tmp` files reverted along with the remote,
which nothing in the world's code can do: it points at Horizon's sandbox being restored
mid-run, not at the task.

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

- Report the sandbox rollbacks in runs 1 and 3 to Horizon: 2 runs zeroed by the
  environment.
- Consider stating the caller-price exemption where `batch_multiplier` is discussed. Every
  run that lost it had *read* it, so this is mainly an agent slip.

---

## g7 — agent-turn-ledger (v5, eval 8deffce4)

*Rerun on 2026-09-11. It replaces eval 94bf8242 (v4), whose results have been dropped.*

**Reward.** The mean is **0.76 over the 9 live runs**, or 0.69 across all 10. **No run
scored 1.00.**

Run 5 never shipped. For most of the run it treated its terminal as stale, though every
screen was a fresh capture, and near the end it cited a commit hash (`8e34d2ef3d`), a green
CI and merged PRs that appear only in its own reasoning, never on screen. Its real push had
failed (`src refspec feat/turn-ledger does not match any`). It ran out of its 200 steps
mid-repair, although its local code had both requirements right.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | d7d2552c | 0.750 | r1.rule (not found: `TURN_LEDGER_FILENAME`); r1.scope (slip: merged "created" into "adopted"; its late patch fixed the wrong call site) |
| 2 | c22e6a99 | 0.875 | r1.observability (slip: stretched `fix30`, so a resumed run reports `created`) |
| 3 | e53e89fc | 0.875 | r1.rule (swapped `write_sidecar`'s arguments) |
| 4 | 625bf84c | 0.625 | r1.scope, r1.failure_behavior, r1.observability (not found: mail `l9`, "missing file is benign, we adopt the log"; its list of mail subjects was cut to the 40 most frequent by `head -40`, dropping it) |
| 5 | 8a514932 | 0 | all 8 (never shipped: its push failed; the commit and CI it cited were never on screen) |
| 6 | abbd1b41 | 0.875 | r1.rule (not found: `TURN_LEDGER_FILENAME`) |
| 7 | 9bd32b81 | 0.500 | r1.rule (not found); r1.scope, r1.failure_behavior, r1.observability (misread `fix27`: read "came back adopted both times" in full, then wrote missing sidecar → `created`) |
| 8 | 4df9fa70 | 0.875 | r1.rule (swapped `write_sidecar`'s arguments) |
| 9 | bfd713dc | 0.875 | r1.rule (not found: `TURN_LEDGER_FILENAME`) |
| 10 | 41f9c9fd | 0.625 | r1.rule (not found); r1.scope, r1.observability (slip: `build_ledger`'s `status="verified"` default never overridden) |

**Pass rates over all 10 runs:** **r1.rule 2/10**, r1.scope 5/10, r1.observability 5/10,
r1.failure_behavior 7/10. Every r2 fact is 9/10, and the one miss is run 5.

**Why the 15 lost fact-points were lost** (not counting the 8 points of run 5, which never shipped, or the 2
that runs 3 and 8 lost on `write_sidecar`'s argument order, which the world never states and
the grader now accepts either way):

| cause | points |
|---|---|
| not found | 8 |
| implementation slip | 4 |
| found but misread | 3 |

### r1.rule: one unreachable name (2/10 passed)

**`TURN_LEDGER_FILENAME` still has one home**: `g7.r1.l2`, a comment on the off-topic page
"Weekly sync notes: week of Jun 2".

| runs | name in the transcript | r1.rule |
|---|---|---|
| 2, 4 | yes | passed |
| 3, 8 | yes | lost anyway, on `write_sidecar`'s argument order |
| 1, 6, 7, 9, 10 | no | **lost, 5/5** |

In the runs that missed it, the page surfaced in their own searches and was never opened.
Run 6's later sweep of pages skipped it because of a hard-coded range of page IDs.

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
| 30c95df4 / 3 | 8bdfd136 | 0.778 | r1.rule (slip: hook placed in `_handle_multi_modal_prompt`); r2.failure_behavior (misread: read `fix24`'s thread without `l14`, left `"auto"` out) |
| 30c95df4 / 4 | 458ef5bd | 0.778 | r1.scope (folded the 45 MB total into its count check); r2.failure_behavior (not found: `l14`; left `"auto"` out) |
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
| not found | 5 | 38% |
| implementation slip | 4 | 31% |
| found but misread | 4 | 31% |

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

### The `"auto"` trap: knowable, but one invented turn argues against it

The grader wants `tuple(_SUPPORTED_IMAGE_DETAILS) == ("auto", "low", "high")`. Only
`g8.r2.l14` (#viewer) says "three entries, and index 0 is what the fallback hands back".
- The plant for `g8.r2.fix24` settles only that "low precedes high". Its forbidden terms
  deliberately include "three values", "auto goes first" and "index 0".
- The #pipeline thread phase 4 built around it (2025-05-13) adds two **invented** turns:
  emil's "it's just the two values plus auto, i believe", and nikolai's close, "**auto is a
  diffrent question imo it's not a detail level its a fallback**".
- Runs 3 and 4 had `fix24` but not `l14`, and shipped `("low", "high")`. Run 4 reasoned "auto
  is fallback not a member". Run 3 wrote "deliberately not in the vocabulary".
- The answer is still knowable. `l14` gives three entries with the fallback value at index 0;
  dermot's #pipeline remark (2025-05-13) says "if it isn't one of the three we fall back to
  auto"; the ticket makes an image block's `detail` `"auto"` when the attribute is absent;
  and curator's own `Image.detail` defaults to `"auto"`. 8 of 10 runs got it right.

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

## g11 — training-step-ledger (v11, eval a8572080)

*Rerun on 2026-09-11, on the herring fix: konrad's `rev2` now retracts both halves of his
herring. It replaces eval 94bf8242 (v7), whose results are dropped.*

**Reward.** The mean is **0.86**, and **2/10 scored 1.00** (runs 3 and 5). All ten runs
shipped, and there were no infra losses.

| run | rollout | reward | facts lost (cause) |
|---|---|---|---|
| 1 | e0b0463c | 0.889 | r2.rule (not found: `l10`, `min_lr_ratio` keyword-only) |
| 2 | 26946169 | 0.889 | r1.failure_behavior (not found: it saw only `l17`'s opening question, never the merge) |
| 3 | bf174d55 | 1.00 | — |
| 4 | ba527345 | 0.889 | r2.rule (not found: `l10`) |
| 5 | ee635c81 | 1.00 | — |
| 6 | ca624f58 | 0.444 | r1.rule, r1.scope, r1.exclusions, r1.observability (slip: its epoch trigger uses `batch_ordinal % batches_per_epoch`, not the `epoch_closing_steps()` helper it wrote and used elsewhere, so step 2 never gets its "epoch" reason); r1.failure_behavior (not found: `l17`'s answer) |
| 7 | 79ffaf93 | 0.889 | r2.failure_behavior (**herring followed**: it saw konrad's herring, never reached `rev2` in #general, and kept the uncapped strict warmup compare) |
| 8 | 34081783 | 0.889 | r2.rule (not found: `l10`) |
| 9 | af6b3aa7 | 0.778 | r1.scope, r1.observability (not found: `r1.l9`–`l11`, that the final step always checkpoints) |
| 10 | 1fdcca2f | 0.889 | r1.failure_behavior (not found: `l17`'s answer; its `sed` window started past it) |

**Pass rates:** r1.failure_behavior 7/10 and r2.rule 7/10; r1.scope and r1.observability
8/10; r1.rule, r1.exclusions and r2.failure_behavior 9/10; r2.exclusions and
r2.observability 10/10.

**Why the 13 lost fact-points were lost:**

| cause | points |
|---|---|
| not found | 8 |
| implementation slip | 4 |
| herring followed | 1 |

### The fix held: konrad's herring caught only the run that never saw `rev2`

In v7, konrad's herring (#viewer, 2025-02-19) made two claims, the decay "lands at exactly
zero" and warmup keeps the strict `step < warmup_steps` compare, and `rev2` retracted only
the second. In v11, `rev2` (#general, 2025-06-02) retracts both: "the end doesnt sit at zero
any more, it bottoms out at a tenth of base_lr and holds there, and a first step at rate 0 is
not something i want to keep defending".

| runs | saw the rewritten `rev2` | believed konrad's herring |
|---|---|---|
| 1–6, 8–10 | yes | **0/9** |
| 7 | no (#general for that date was never read) | **yes**: "warmup strict `step < warmup_steps` ... confirmed" (line 3640); it lost r2.failure_behavior |

### Two single-carrier rules still decide most of the score

**`min_lr_ratio` sits behind a bare `*` (keyword-only).** Only `g11.r2.l10` (#code-review,
2025-05-30) says so; the ticket makes only `clock` and `rng` keyword-only.

| runs | found `l10` | r2.rule |
|---|---|---|
| 2, 3, 5, 6, 7, 9, 10 | yes | **passed, 7/7** |
| 1, 4, 8 | no | **lost, 3/3** |

Their chat searches used `cosine|decay|base_lr|learning_rate` vocabulary, which `l10` does
not share, and #code-review was never dumped for late May.

**A repeated save merges the `reasons` tuples.** `l16` (#pipeline) says only that a matching
name "replaces" the last row. The merge is in `l17` (#releases): "both carry forward onto it.
neither set gets dropped", phrased as **label sets**, while every graded identifier says
`reasons`.

| runs | read `l17`'s answer | r1.failure_behavior |
|---|---|---|
| 1, 3, 4, 5, 7, 8, 9 | yes | **passed, 7/7** |
| 2, 6, 10 | only its opening question, as a search snippet | **lost, 3/3** |

### One run built the rule, then wired the wrong trigger

Run 6 found nearly every r1 clue, and wrote an `epoch_closing_steps()` helper that it used
correctly for the loss history. Its checkpoint trigger in `train()` instead tests
`batch_ordinal % plan.batches_per_epoch == 0`. Step 2's window straddles the epoch boundary,
so it never gets its "epoch" reason, which costs four r1 facts from one line.

### Herrings

| herring → reversal | saw herring | saw reversal | believed herring |
|---|---|---|---|
| `ledger-twin-checkpoints-dario` → `rev1` | 7/10 | 10/10 | 0/10 |
| `ledger-twin-checkpoints-emil` → `rev2` | 9/10 | 10/10 | 0/10 |
| `lr-decay-to-zero-dario` → `rev1` | 10/10 | 10/10 | 0/10 |
| `lr-decay-to-zero-konrad` → `rev2` | 10/10 | 9/10 | 1/10 (run 7) |

### Which remarks go unfound

g11's corpus is chat only.

| remark quality | found |
|---|---|
| carries an identifier that must be typed literally | 85% |
| plain English, no identifier | 68% |
| reversals | 98% |

### Owed for g11 (not applied)

- Say "reasons" (not "label sets") in the merge carrier, and give the merge and the
  keyword-only rule a second carrier each.
- Refresh the key's quote of `rev2`: it still shows the pre-fix wording.

---

## Register: every defect and fault found

Every entry below was checked by hand against the answer key, the plant record, the
ticket, the grader or the transcript. The evidence for each ruling is in
`tasks/rollout_analysis/readers/corrections.md`. No task or grader defect is left open: the
ones found were fixed, or judged on review to be knowable from the corpus. Everything below
is open.

### Graded names or orders with a single, hard-to-reach home

These are fair, but brittle: each test measures whether a run happened to open one place.

| task | graded thing | its only home | runs that found it | points |
|---|---|---|---|---|
| g1 | `plan_fingerprint` | `l6`, hedged ("or something in that direction"); 3 remarks say `plan_id` | seen 9/10; 3 runs named it `plan_id` | 7 |
| g1 | `PLAN_FILE_NAME` | a *nested reply* in a wiki comment thread | 6/10 | 4 |
| g1 | "plan written before the first request file" | `l16`, plain English | 3/10 | 2 |
| g2 | `OutputCapError` | `l-floor-nikolai`, #cookbooks | 4/10 | — |
| g2 | `.max_bytes` plus the message | `l-floor-konrad`, #cookbooks | **1/10**; `failure_behavior` passed only in that run | 8 |
| g3 | rounding to 3 places | `s1c`, #pipeline | 6/9 in full (run 9 saw only its opening question); found → 6/6 passed, not → 0/3 | 3 |
| g7 | `TURN_LEDGER_FILENAME` | a comment on the off-topic "Weekly sync notes" page | 4/10 (v5) | 5 (runs 1, 6, 7, 9, 10) |
| g8 | where the 45 MB total lives | `s2-gideon`, #code-review | 5/10; found → 4/5 passed, not found → 0/5 | 5 |
| g9 | `ExampleTooLongError`'s attribute names and message | `l-fail-3`, #pipeline | 8/10 | 2 (runs 2, 9) |
| g11 | `min_lr_ratio` is keyword-only | `l10`, #code-review | 7/10; found → 7/7 passed, not found → 0/3 | 3 |
| g11 | a repeat save merges the `reasons` tuples | `l17`, #releases, phrased as "label sets" | 7/10 read its answer; read → 7/7 passed, opening question only → 0/3 | 3 |

### Ticket-invited misreading

- **g8:** the non-goal "Out of scope: the batch path" gave runs 2 and 7 somewhere to file
  the whole-prompt ceiling ("belongs to the batch planner ... out of scope").

### Environment faults (infra; not the task, not the agent)

| run | fault |
|---|---|
| g6 runs 1, 3 | after a green CI (run 1 had even confirmed the deploy) the **whole sandbox rolled back** to its starting state, remote, local clone and `/tmp` alike; nothing in the world's code does this, so it points at Horizon's sandbox |
| world CI | the "tests" step logs `No module named pytest` and still **reports success** (the line appears in g3, g7, g8, g10 and g11 CI logs) |
| errored rollouts | g8 1; g11 eval 3c71bf59 **10/10** (not read). g9's v7 eval, 8/10 errored, was replaced by the v8 rerun |

### Agent failures to ship (kept out of the knowledge figures)

| run | what happened |
|---|---|
| g2 run 8 | built `output_cap.py`, never wired it in, declared the work complete, looped until the 7200 s kill |
| g3 run 3 (v9) | its patch scripts never landed and it typed no `git commit` or `git push`; its last turns claimed commit 2eaeb50a, a green CI and a deploy |
| g4 run 2 | never committed; spent its remaining turns in a loop comparing against the baseline until the budget ran out |
| g4 run 9 | decided its real terminal output was stale, re-checked its work for about 1,500 lines, committed at the very end and never pushed |
| g7 run 5 (v5) | treated real output as stale, then cited a commit hash, a green CI and merged PRs that never appeared on screen; its real push failed on a branch it had never committed |
| g10 run 8 | never committed; its last steps went on writing tests in small pieces, fighting heredoc escaping |

### Version drift

- **g6:** mail `g6r2-s2-l4` reads with the opposite meaning in the served v6 world compared
  with the repo's v7 key. The v6 wording still argues for the graded rule, so it cost
  nothing.
- **g11:** the key still quotes `rev2`'s pre-fix wording; the served v11 world has the rewrite
  that also retracts "decay to exactly zero". Readers judged against what the runs saw.
- **g3:** the key quotes the pre-09-08 wording of konrad's 15:19 turn in `l15` ("no requeue
  then, its terminal and the reason is throttle:exhausted"); the served v9 world says "no requeue
  then - thats attempts_left 0 with the waivers gone too, both empty. terminal,
  throttle:exhausted". Same fact, so it cost nothing.

### Measurement notes

- Horizon's `extracted_score` is the mean of every subscore and overstates the task reward.
  This document uses `reward`.
- Reader verdicts I overruled after checking are all logged with evidence in
  `tasks/rollout_analysis/readers/corrections.md`. Several involved false claims about the
  ticket or false "only carrier" claims.
- The pre-pass pointer sheet had a few false positives: `g10.r2.h1` matched the repo's own
  source code, and `g6`'s `s1-l1` matched on the word "The". Found or not always comes from
  the readers, so these did not affect the numbers.
- The superseded g3 (v7), g7 (v4), g9 (v7) and g11 (v7) reader verdicts are archived in
  `tasks/rollout_analysis/readers/_superseded/`. None of them feed any number here.
