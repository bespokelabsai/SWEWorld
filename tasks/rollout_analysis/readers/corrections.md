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

## g3 v9 (eval 035777f5), swapped in for v7 (ce846459) on 2026-09-11

- **run 10 r2.rule, r2.observability**: reader said implementation_slip. **Overruled -> not_found.**
  The shipped field default is `None` (`float | None = field(default=None)`). Its reasoning never
  states the field's default; the "0.0 however far ahead you ask" it wrote is
  `remaining_cooldown_seconds`' return value (s1d, found). The ticket never names
  `throttle_cooldown_until`. The one remark that pins "0.0 on a fresh tracker, nothing else added"
  is s1a, a wiki comment, never surfaced (reader: found=no). The None came from h2's invented tail
  "15:47 konrad no thats its own reset, sets it to none" (#cookbooks 2025-01-22). It is not in the
  herring's settles, and rev2 never retracts it. It is recorded as an open corpus item, not counted as
  overridden_by_other_corpus_text: the run never had the settling remark in view.
- **run 3**: reader said infra (42 "Extra text detected after JSON object" warnings, patch scripts
  never written). **Overruled -> never_shipped.** The transcript has 0 typed `git commit` and 0
  `git push`. It closed claiming commit 2eaeb50a, a green CI and a deploy, while provenance says
  pushed=0.
- **run 9 r1.exclusions_or_crossover, r1.observability**: reader's found_misread **stands**. l13 was
  never surfaced, but l12 (mail, same fact: "once auth is the problem the attempts on the clock are
  worth nothing") was read and contradicted. That is a found remark drawn the wrong way.
- **runs 6, 9 r2.rule**: not_found **stands**. The rounding lives only in s1c. Run 9 saw only its
  opening line; run 6 never saw it.
- **v9 fix check**: konrad's rewritten 14:12 turn was seen by runs 2, 5, 6, 8, 9 and 10; runs 1, 3, 4
  and 7 never reached it. No run made `length` terminal: every live run's reader reports it
  shipped as contract, cost 2, retried. The request-path assertion passed in the 8 live runs
  whose r1 observability reached it. Run 9's stopped earlier, on the terminal (`bad_key`) row.
- **key/corpus drift (run 5's reader)**: l15's quoted 15:19 konrad line in the key is the pre-09-08
  wording. The served world has "no requeue then - thats attempts_left 0 with the waivers gone too,
  both empty. terminal, throttle:exhausted. ...". The fact is the same; the key's quote is stale.

## "The corpus argues against the grader" withdrawn (2026-09-11)

- **g8 30c95df4 runs 3 and 4, r2.failure_behavior**: my overrides to
  overridden_by_other_corpus_text (G8-A) are **withdrawn**, and the readers' own verdicts stand:
  run 3 found_misread, run 4 not_found. The answer `("auto", "low", "high")` is knowable. l14
  says "three entries, index 0 is what gets handed back when we cant match / give it None and
  you get auto". dermot (#pipeline 2025-05-13) says "if it isn't one of the three we fall back to
  auto". The ticket gives detail "auto" when the attribute is absent, and curator's Image.detail
  defaults to "auto". Neither run had l14 in view; nikolai's invented "auto ... not a detail
  level its a fallback" only misleads a run that missed it. 8/10 runs got it right.
- **g3 G3-C** ("sets it to none") is judged borderline and left unchanged in the corpus. It is
  recorded as an observation, and its loss stays not_found.
- The report's "corpus argues against the grader" row is gone; 0 points are left in that cause.
- **g7 v5 runs 3 and 8, r1.rule** (`write_sidecar`'s argument order): both go from
  grader_overspecifies to **grader_since_fixed**, a label outside the knowledge causes. The
  grader now accepts either order. Horizon's grades are untouched: synth's scoreboard and
  fact-field pass rates were byte-identical before and after. Knowledge points went 111 -> 109,
  and the "grader over-specifies" row is gone.

## Infra re-examined (2026-09-11)

- **g4 v5 run 9 and g7 v5 run 5**: "infra: stale terminal" is **withdrawn -> never_shipped**.
  A read-only investigation found:
  - no pager, editor, open heredoc or stuck process in either run's raw keystrokes;
  - no two consecutive screens byte-identical.

  My own split of each transcript into tool and assistant turns confirmed it. In g7 run 5,
  `8e34d2ef3d`, PR 737/738 and "ci/test success" appear only in assistant turns (from line
  10121), never in any tool output; its real push failed with `src refspec feat/turn-ledger
  does not match any`. In g4 run 9, the one commit confirmation is at tool line 11139, near the
  end, and there is no push output at all. Dead-run points: infra 30 -> 14, never_shipped
  34 -> 50. The scoreboard and fact pass rates are unchanged.
- **g6 runs 1 and 3 (infra) and g11 run 7 (survived)**: the rollback covered the whole sandbox,
  local clone, working tree and `/tmp` alike, not just the remote. g11 run 7 line 9518: "origin/main
  and local HEAD are both 295ab6c". g6 run 3 wrote the remote SHA to a nonce-named file and read
  back 295ab6c (lines 8879-8978); it saw at least 7 rollbacks. Nothing in world/ (bootstrap,
  supervisord, deploy-daemon), scripts/ or the task arms moves `main` after boot. The rollbacks
  point at Horizon's sandbox, restored or duplicated mid-run.

## g11 v11 (eval a8572080), swapped in for v7 (94bf8242) on 2026-09-11

- **run 7 r2.failure_behavior**: reader said not_found. **Overruled -> herring_followed.** Its own
  herring row for `lr-decay-to-zero-konrad` -> rev2 reads: saw the herring (L3619-3626), never
  saw rev2 (#general 2025-06-02 never read), believed the herring, and the code followed it. Its
  Analysis at L3640 says "warmup strict `step < warmup_steps` ... confirmed". It shipped no
  `effective_warmup = min(warmup_steps, total_steps)`, giving [1e-05, 2e-05, 3e-05].
- **run 6 r1.failure_behavior**: reader said found_misread. **Overruled -> not_found.** l17 reached
  it only as its opening question, the same as runs 2 and 10, which are not_found.
- Stand: run 6's four r1 slips (its epoch trigger uses `batch_ordinal % batches_per_epoch`, not
  its own `epoch_closing_steps()`); runs 1, 4, 8 r2.rule (l10 never surfaced); run 9 r1.scope and
  r1.observability (l9/l10/l11, the unconditional final checkpoint, never surfaced); runs 2 and
  10 r1.failure_behavior (l17's answer never in view).
- **The G11-H fix check**: 9/10 runs saw the rewritten rev2 and none believed konrad's herring.
  Run 7, the one that never saw rev2, believed it.
- **key/corpus drift**: the key still quotes rev2's pre-fix wording. The served v11 plant has
  "...both of those are gone now. the end doesnt sit at zero any more, it bottoms out at a tenth
  of base_lr and holds there...". The facts are the same; the key's quote is stale.

## g9-meridian v8 (eval de47e209), read 2026-09-15 — the same task/version as g9 under meridian

- **`g9.r2.l15` was never rendered into the world.** The plant record's text is dario settling
  the question — "the fireworks jsonl path never loads a tokenizer, so a token total and a trim
  count coming back off it are just noise — both read zero there" — and the served corpus has only
  nikolai ASKING it (mail 9035, "Do we return None, do we leave the keys out entirely, or do we
  put zeros in there?"), leaning the wrong way with "I'd say leaving them out is cleanest". No
  reply exists in any mailbox; `both read zero` / `read zero there` have 0 hits across
  messages.jsonl, comments.jsonl, docs/ and emails/. The plant's own carrier note describes the
  shape that was meant to land: "someone asks what the returned counts mean per backend, dario
  settles the Fireworks half".
  **Readers credited it found 9/10** — they found the THREAD, not the clause. Left standing in the
  remark table rather than overridden, because no fact verdict turns on it: run 2 is the only
  r2.rule loss and its reader already called it `not_found`, and the other nine derived the zero
  from `to_jsonl_lines` never tokenizing. Flagged here so the 9/10 is not read as a finding.
- **No verdict overruled.** Ten reader-recorded losses, ten graded losses, and every cause
  survived a check against the transcript, the plant and the served corpus.
- **The one fact that separates this eval: `g9.r2.failure_behavior`, 3/10.** `g9.r2.rev3`, the
  only reversal in g9 that lives in a wiki comment, surfaced in **0 of 10** runs (lumen: 4 of 10).
  Of the 6 runs that read the `g9.r2.h-role-row` herring, 5 believed it and 5 shipped it. The
  other four herring/reversal pairs all live in chat: reversal seen 10/10, herring believed 0/10.
- **Why rev3 is unreachable by search.** It sits on
  `docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`; the corroborating
  `say24` sits on `what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md`. Neither
  page's title or body contains "encoding", "finetuning" or "Fireworks" — 0 hits each — and the
  task is named *example encoding*, so "encoding" is the first query every run typed. Runs 5 and 8
  fetched page comments routinely (5-6 pages each, body+comments via `/api/pages/{id}`); they
  still never opened these two, because the pages never appeared in a result list. The failure is
  not "the agent does not read comments", it is that the pages carrying them share no vocabulary
  with the task's own subject.
