# Reader verdicts I checked and overruled

- g7 run4 r1.rule — reader: "implementation_slip; write_sidecar args reversed vs. the ticket's
  own stated (working_dir, ledger) signature". FALSE: `grep write_sidecar ticket.md` = 0 hits.
  The corpus states verify_sidecar's order ("hand it the work dir and the ledger") and calls
  write_sidecar "the other half" (#code-review thread, transcript :2373), never its own order.
  Reclassify: BORDERLINE (grader pins an order the world only implies). Audit agreed (2026-09-10).
- g7 run10 r1.failure_behavior + r1.observability — reader: "infra". Nothing in the harness
  failed; the agent read nikolai's served "yes, the log side only" (transcript :2539-2551) and
  shipped it. Same defect as runs 1/2/6, which their readers tagged
  overridden_by_other_corpus_text. Reclassify to match (task defect A, not infra).

# Reader claims I checked and CONFIRMED (answer-key greps)
- g1: `PLAN_FILE_NAME` has exactly one carrier, g1.r1.l2 (wiki comment thread on
  batch-job-status-persistence page; the constant first appears in nikolai's 09:47 reply, not
  the top-level comment — consistent with run5's "nested reply not serialized").
- g1: "plan written before the first request file" has exactly one carrier, g1.r1.l16
  (#pipeline 2025-04-23). Runs 5 and 6 lost r1.scope to it.
- g2: "hang the offending value on the exception as .max_bytes" has exactly one carrier,
  g2.r1.l-floor-konrad (#cookbooks 2025-03-17). l-bytes-dario and rev1 mention max_bytes only
  as the cap. g2.r1.failure_behavior has 7 carriers overall, but the graded `.max_bytes ==
  8` attribute rests on that one.
- g1 run7: "g1.r1.say22 is the sole remark pinning the plan document's key order" — MOSTLY TRUE.
  g1.r1.l11 (#viewer 2025-04-22, found by run7 at :1121 and followed) puts num_batches at the
  top and gives asdict-per-PlannedBatch, but only says "the request and byte totals"; it names
  neither num_requests/num_bytes nor the full order. say22 (#general, never dumped by run7)
  is the only carrier of the full order + names. Keep as not_found.
- g2 runs 2/3/4 readers: "three remarks name OutputCapError (l-floor-nikolai, l-floor-konrad,
  say26)" — OVERSTATED. Answer-key grep: OutputCapError appears in exactly ONE remark,
  g2.r1.l-floor-nikolai (#cookbooks 2025-03-14). The ticket names none of OutputCapError /
  max_bytes / MIN_MAX_OUTPUT_BYTES / "at least 16". So the graded surface of
  g2.r1.failure_behavior rests on two single-carrier literals, both in #cookbooks:
    class name  -> l-floor-nikolai only
    .max_bytes attribute + exact message -> l-floor-konrad only
  say26 (#incidents) carries field_validator/ValidationError, not the name. Cause stays
  not_found; the finding is "two single-home literals in one quiet channel".
- g2 run7: TRUNCATION_LOG_TEMPLATE has exactly ONE carrier, g2.r1.l-log-nikolai (wiki comment on
  docs/engineering/capping-executor-stdout-and-stderr-in-code-execution.md, 2025-06-17); not in
  the ticket; graded at test_r1.py:185-187. CONFIRMED. But its string appears in 9/10 g2
  transcripts (all but run7) — a single-home wiki comment on an ON-TOPIC page is found. Contrast
  g7 TURN_LEDGER_FILENAME (comment on off-topic "Weekly sync notes") 4/9, and g1 PLAN_FILE_NAME
  (nested reply in a comment thread on a batch-status page).
- g3 run3 reader: "invented dialogue around g3.r1.l1 led the agent to make finish_reason=length
  TERMINAL; passed only because the grader tests a raw ValueError" — CONFIRMED.
  plant.json g3.r1.l1 settles: "a contract failure should be charged more than one attempt"
  (= CONTRACT, cost 2). Rendered #code-review 2025-06-03 14:12 konrad (INVENTED): "and length
  wont fix itself on a retry anyway, so it stops being retryable, fail it out on the first"
  (= TERMINAL). test_r1.py:221-224 only calls policy.decide(ValueError("finish_reason was
  length"), ...) -> type-based CONTRACT, so an agent that adds its own terminal error at the
  call site still scores 1. Same defect class as g7 fix28/l12: scaffolding outvotes the plant,
  here MASKED by a grader gap (false pass rather than a lost point). Asked the 8 open g3
  readers to check each run's shipped code for it.
- g2 run3 r1.observability — reader: "implementation_slip/not_found". The rule (l-log-konrad,
  "the except handler's salvage cap logs nothing") never surfaced in run3 (0 grep hits in any g2
  transcript); runs 7/9/10 with the same loss are tagged not_found. Reclassify not_found.
- g3 run6 r2.exclusions_or_crossover — reader: "grader_overspecifies". CONFIRMED. test_r2.py:206
  asserts the NAME "seconds_to_pause_on_rate_limit" is absent from inspect.getsource(
  BaseOnlineRequestProcessor) ("still reads the dead pause knob"); the requirement is only that
  nothing READS it. getsource includes comments/docstrings, and run6's docstring explained why the
  knob is unused. Only run6 of 10 lost this fact. Grader defect.
- g3 konrad "fail it out on the first" exposure: the line appears in the transcripts of runs 3, 8,
  10 and no other; exactly those three shipped finish_reason=length as non-retryable (false
  passes). Saw-it -> followed-it 3/3; never-saw -> correct 7/7.
- g4 run9 reward 0 — reader: infra (terminal echoing stale output from ~l.9682, 15+ re-ground
  cycles, committed locally, never pushed before the step budget). Kept as infra: same signature
  as the g11 "two worlds" terminal fault in g7-g11-eval-audit.md.
- g4 run2 and g2 run8 -> never_shipped (aggregate.NEVER_SHIPPED): agent-side, not harness.
- g4 r1.scope (backend_params hands out a copy): readers' "fix27 and l-params-copy are the only
  carriers" — CONFIRMED. rev1 and l-keys-onelist contain "copy" only incidentally ("which copy
  is the stale one"). fix27 (#code-review 2025-03-14) is an observation ("popped batch_size ...
  read it again and batch_size was still there"); l-params-copy (#code-review 2025-04-23) found
  3/10 (runs 2, 7, 9; two of them never shipped). fix27 in view in 10/10. Passing runs 4/5/7/8/10
  cite fix27; losing runs 1/3/6 had it on screen and never engaged -> found != used.
- My own error: I told the user g4's mean was 0.84. Correct: 0.9375 over the 8 shipped runs
  (4 x 0.875 + 4 x 1.00), 0.75 over all 10. The doc carries the correct figures.
- g8 r2.failure_behavior (runs 3, 4 of eval 30c95df4) — readers: found_misread / not_found.
  Reclassified overridden_by_other_corpus_text (TASK DEFECT). plant.json g8.r2.fix24 settles only
  "low precedes high"; forbidden_terms include "three values", "auto goes first", "index 0". The
  rendered #pipeline 2025-05-13 thread's INVENTED turns: emil 10:14 "it's just the two values plus
  auto, i believe" and nikolai 10:35 "auto is a diffrent question imo it's not a detail level its
  a fallback". Grader: tuple(vocabulary) == ("auto","low","high"); only g8.r2.l14 (#viewer
  2025-04-24) states three entries with auto at index 0. Run4 reasoned "auto is fallback not a
  member"; run3 commented "deliberately not in the vocabulary". Same class as g3 konrad / g7 fix28.
- g6 g6r2-s2-l4: three readers (runs 4, 6, 7, 9) independently report the mail thread reads with
  the OPPOSITE polarity in the served v6 world vs the repo's v7 key; the v6 wording still argues
  the graded rule, so harmless here. Version drift, not a defect in v6.
- g8 r1.scope (45 MB whole-prompt ceiling), runs 2 & 7 (30c95df4) judged it "a separate
  estimator" / "belongs to the batch planner ... out of scope". The ticket's non-goals line
  (ticket :141) reads "Out of scope: the batch path (openai_batch_request_processor.py:66) ...".
  The ceiling actually lives in the online path's _handle_multi_modal_prompt, pinned only by
  g8.r1.s2-gideon (#code-review 2025-03-17). A ticket-invited misreading, kept as found_misread /
  implementation_slip but called out in the g8 section.
- g11 run3 r2.rule: reader "exactly one remark (g11.r2.l10) states min_lr_ratio is keyword-only"
  — CONFIRMED after a false alarm: the answer-key grep also matched g11.r1.rev2, but rev2's
  "keyword only" is about save_checkpoint's `reasons`, not min_lr_ratio. l10 (#code-review
  2025-05-30) is the sole carrier; the ticket only makes clock/rng keyword-only. Its "behind a
  bare" wording is absent from the target-eval transcripts of runs 1, 3, 5, 9.
- g10 run8 reward 0 -> never_shipped (reader said infra): zero git add/commit/push in 200 steps;
  design correct by step 125, then fragmentary test-writing against heredoc/JSON escaping until
  the step budget ran out. Added ("g10", 8) to aggregate.NEVER_SHIPPED.
- g11 run1 r2.rule / r2.exclusions / r2.observability — reader: not_found. Reclassified
  herring_followed: the ONLY herring capture in 292 (run, herring) pairs. Run1 found herring
  g11.r2.lr-decay-to-zero-konrad (#viewer 2025-02-19: "decay lands at exactly zero ... and warmup
  keeps the strict step < warmup_steps compare") and its registered reversal g11.r2.rev2 (#general
  2025-06-02), which retracts ONLY the warmup compare; run1 read rev2 as "decay reaches exactly
  zero" (missed_point). The decay-to-zero half is retracted only by g11.r2.rev1 (#help
  2025-03-26: min_lr_ratio, MIN_LR_RATIO = 0.1), registered against the OTHER herring (dario's),
  and run1 never found it. DESIGN ISSUE: a two-claim herring whose registered reversal retracts
  one claim leaves the other standing for any run that misses the second reversal.
- g6 run9 reader wrote its 31 clue rows under 'clues' instead of 'remarks'; merged (backup run9.json.orig). Data intact.

## 2026-09-11 swap: g7 and g9 re-evaluated
Every g7 and g9 entry above refers to the SUPERSEDED evals (g7 v4 94bf8242, g9 v7 fffbd350);
those reader verdicts are archived under readers/_superseded/. The g7 overrides in aggregate.py
were removed for that reason. New evals: g7 v5 8deffce4 (served nikolai's corrected "no, both
sides" reply in 10/10 transcripts), g9 v8 3b0b259f (10/10 scored).
- g9 v8 run6 r2.failure_behavior — reader: herring_followed. CONFIRMED structure: herring
  g9.r2.h-role-row is a MAIL (dario 2025-05-28, "Length and role sequence are row problems ...
  counted and skipped"), visible in 10/10 transcripts. Its only reversal g9.r2.rev3 and the clue
  g9.r2.l17 are both WIKI COMMENTS on docs/engineering/request-builder-what-we-drop-and-what-we-
  raise-on.md (2025-06-17) — BookStack search does not index comments — visible in only 4/10
  transcripts (runs 2, 5, 7, 9). Same finding as tasks/g7-g11-eval-audit.md's g9 note ("its
  retraction is in an unsearchable page comment"), now measured.
- CORRECTION OF MY OWN EARLIER ENTRY (g7 run4, 2026-09-11 first pass): I wrote "The world
  gives verify_sidecar's argument order ('hand it the work dir and the ledger')". WRONG. That
  clause is only in the answer key's / plant's gist for g7.r1.say20; the rendered #engineering
  2025-04-28 exchange drops it (gideon 14:26 "version 2 checkpoint, and responses and
  last_author both matching the log"). 0 hits for "work dir and the ledger" in the served
  plant/messages.jsonl and in all 10 g7 v5 transcripts; no (write|verify)_sidecar(...) call
  signature anywhere in the plant. So write_sidecar's graded argument order is unstated in the
  world: a phase-4 "said thinner than planted" loss that surfaces as grader over-specification.
  g7 v5 runs 3 and 8 lost r1.rule to it (run 8 reader said implementation_slip -> overridden to
  grader_overspecifies). The old eval's run 4 had the same loss. Register G7-D' upgraded.
- g7 v5 run10 r1.rule — reader: implementation_slip ("stating the latter as fact 8+ times").
  Overruled -> not_found. The same reader says TURN_LEDGER_FILENAME never appears in the
  transcript; a grep of the v5 transcripts shows the name only in runs 2, 3, 4, 8. What run 10
  repeated was the value turn_ledger.json. Its r1.scope / r1.observability slips (build_ledger's
  status="verified" default never overridden) stand.

## 2026-09-11, after the report

- **G9-H withdrawn** by the task owner's call. The six `herring_followed` points in g9 runs 1, 3,
  4, 6, 8 and 10 stand as measured causes, but the herring is working as designed, not a defect.
- **G3-A confirmed from the plant record, then fixed.** `plant.json` lists konrad 14:12 under
  `g3.r1.l1`'s `invented` thread, and its `pieces` entry logged it as "the decision:
  length-truncated responses stop being retryable, fail on the first attempt". That contradicts
  `l1`'s `settles` ("a contract failure should be charged more than one attempt"). The turn was
  rewritten, and the request-path grader case (G3-A′) and the AST knob check (G3-B) were added.
  The report's g3 section has the verification matrix.
