# g7–g11 hosted-blind eval audit (2026-09-09)

Four evals, all the `world-hosted` (blind) arm, model `lumen`, agent `typhoon`.
Question asked: for every fact that failed, is it the agent's mistake or a task defect?

| eval | task | runs | failing facts | verdict |
|---|---|---|---|---|
| 1cfc62df | g7 agent-turn-ledger | 0.83 / 0.92 | r1.rule (1/2), r1.failure_behavior (2/2) | **1 defect** + 1 agent |
| 66eb8a20 | g8 attachment-payload | 0.85 / 0.85 | r1.rule, r2.failure_behavior / r1.scope, r1.exclusions | all agent |
| 614e5f52 | g9 example-encoding | 0.91 | r2.failure_behavior | **defect** |
| f25dfb66 | g11 training-step-ledger | 0.92 / 0.00 | r1.failure_behavior / execution | agent + **infra** |

Method per fact: read the graded assertion out of the rollout's full ctrf trace
(`GET /api/rollouts/<id>`, not `rollouts pull`, which truncates at 2048 bytes);
find the carrying remark in `environment/plant/` rather than trusting the key's
`covers` field; read that remark *in the rendered context*; check the ticket;
check identifier reachability; then check the transcript for whether the agent
found it. Cross-run and cross-arm used as controls.

### CORRECTION to the first pass of this audit

The `clues` **1.00** / `located` **1.00** rows in these answer keys are NOT
measurements. `refresh_answer_key.py:62` writes `**1.00**` into the located row as a
string literal, and 41e4285's message says the rows "read 1.00, as for g1-g6" --
copied, not run. `tg/inject.py:1196` had already removed that column for exactly this
reason: *"it asserted g1's 0.00 / 1.00 / 1.00 for tasks whose arms had never been run.
Nothing on disk sources those numbers, so the column is gone rather than guessed."*
The first pass of this audit cited those numbers as a controlled comparison for g7 and
g9. They are not evidence. Every arm figure below is now read from real rollouts via
`horizon rollouts pull <task-id>`, per version.

Real located-arm numbers, current task version:

| fact | located arm | blind hosted |
|---|---|---|
| `g7.r1.failure_behavior` | **1/12** (cipher-omni 0/10, lumen 1/2) | 0/2 |
| `g7.r1.rule` | 2/12 (cipher-omni 0/10, lumen **2/2**) | 1/2 |
| `g9.r2.failure_behavior` | v5 **2/3** (lumen) | 0/1 |

g7's fact fails on the arm that hands the agent the remark's exact location, which per
[[located-arm-failure-is-ours]] makes it ours. g9's mostly passes there, so g9's case
rests on the page being factually wrong rather than on the score -- see below.

---

## DEFECT 1 — g7 `r1.failure_behavior`, deterministic (2/2)

Graded: an unparseable sidecar is `adopted`. Both submissions raised.

The plant is one clean line. Phase 4 rendered it into #engineering 2025-04-10 with
invented turns that reverse its sense:

    13:07 gideon  PLANT     pointed verify_sidecar at a turn_ledger.json json.loads chokes on
    13:08 gideon  PLANT     status came back adopted. um. that was the whole point of the run tbh
    13:10 dermot            adopted as in it passed? ... nothing surfaced at all, no exception
    13:12 dario   INVENTED  honestly i'd have expected a raise there too. thats a bad shape
                            to be quiet about
    13:16 gideon  PLANT     TurnLedgerDesyncError is the only raise in there
                  INVENTED  ...and that one is the wrong thing to reuse here, so the parse
                            failure gets its own answer
    13:19 dermot  INVENTED  a file that wont load isnt a desync in any reading of the word

The thread reads as a bug report that ends in a decision to add a dedicated
exception. The ticket then hands the agent exactly that class
(`TurnLedgerCorruptError(path, line_number, reason)`, scoped there to `read_log`),
and the ticket's own "parked is not cancelled -- carrying it out is part of this
ticket" makes 13:16 read as settled work owed.

Both runs read the whole thread (g7_msg1.txt:3938-3945, g7_msg2.txt:3707-3714).
run1 wrote the correct rule in its own note first -- "verify_sidecar adopted on
corrupt json" (seq 104) -- then implemented the raise.

FIX (touches only invented turns, so the plant text is unchanged and
`inject.located()` still matches -- no resync needed):
  plant/messages.jsonl, #engineering 2025-04-10
  - drop 13:12, or make it a question rather than a verdict
  - end 13:16 at "no other exit for it to take"; cut the tail
  - replace 13:19 with an endorsement, e.g. "mhm. so a file we cant read tells us
    nothing, same as no file -- adopt and carry on"

## DEFECT 2 — g9 `r2.failure_behavior`

Graded: `format_batch` absorbs only `ExampleTooLongError`; `InvalidRoleSequenceError`
propagates and aborts.

The only wiki page in the corpus that names `format_batch` is titled with the graded
question verbatim -- "what format_batch counts as a drop and what stops the pass
instead" (2025-06-11) -- and answers it wrongly:

    ## rejections that get absorbed and counted
    - row is missing a field the provider requires (empty message list,
      no role on a message, that kind of thing)
    ...
    i think that's the right default and i don't want to relitigate it here.

    ## failures that stop the pass
    the other category is failures that are properties of the configuration
    rather than of any individual row.

`fixtures/oracle.patch:453,457`: an empty message list is `reason="empty"`, a message
with no role is `reason="unknown_role"` -- both raise `InvalidRoleSequenceError`. So the
page files the graded exception's own triggers under "absorbed and counted", and then
defines the abort bucket as config-level only, which excludes a per-row role error by
construction.

That page is not registered as a herring and nothing reverses it. The correct clue is on
a page that says twice it covers only the *request builder* and never names
`format_batch`; its retraction is in an unsearchable page comment.

Transcript: agent read the correct page and wrote "Analysis: Consistent: role sequence
errors raise" (g9_msg1.txt:2467), then after the 2025-05-28 herring mail flipped
(:3766) and shipped `except (InvalidRoleSequenceError, ExampleTooLongError):` against
the oracle's `except ExampleTooLongError:`.

FIX (three edits, none to planted words):
  1. plant/docs/engineering/what-format-batch-counts-as-a-drop-...md:19 -- strip the two
     InvalidRoleSequenceError triggers from the absorbed bucket
  2. same file :30 -- reword the abort bucket so it is not defined as config-only
  3. plant/messages.jsonl -- add a short on-object #pipeline reversal dated after
     2025-06-11, split so no single line restates the rule
  Then resync the plant, clear harbor_tasks/.located-corpora/, rebuild the located arm.

## INFRA — g11 run 2

`grade_result.metadata.feedback` = "Harbor trial did not complete." 62 `[horizon
watchdog]` interventions; the agent logged "the terminal is showing me two different
worlds" (g11_msg2.txt:9623), git HEAD flipping between three commits across frames, /tmp
and $HOME files vanishing between commands. No `git reset`/`checkout`/`stash`/`clean`
anywhere in the run. Carries no signal about the task; rerun it.

---

## AGENT MISTAKES (no change owed)

**g7 r1.rule** (run1). `sym("TURN_LEDGER_FILENAME")` -- run1 never defined it. The
constant occurs exactly once in the corpus, in a page comment (BookStack search is blind
to comments), and is not in the ticket. But run1's *own* wiki search returned that page
(`('page', 85) Weekly sync notes: week of Jun 2` -- its body carries a "PR 685, multi-turn
agent stopping criterion" section); run1 fetched five other pages whole and skipped it.
run2 fetched it and passed. Triage error. Every other graded name here has 2-34
occurrences, so a second searchable home for this one is cheap insurance.

**g8, all four** (r1.rule, r2.failure_behavior in run1; r1.scope, r1.exclusions in run2).
Each fact was passed by the *other* run against the identical corpus, suite and ticket --
the two runs' failures are disjoint. This arm's corpus is 391 chat messages and nothing
else (comments.jsonl is 0 bytes, no docs/, no emails/), so every remark is full-text
searchable. Every failing assertion matches `fixtures/oracle.patch` exactly. Specifics:
- r1.rule: agent wrote "raised inside _canonical_attachment_block before
  file_upload_limit_check" in its own note (g8_msg1.txt:5444) and then put the hook calls
  in `_handle_multi_modal_prompt` instead. run2 caught the same slip in self-review
  (g8_msg2.txt:8382) and fixed it.
- r1.scope: run2 never read the #code-review March threads carrying the 45.0 aggregate;
  its one grep of that channel was truncated by `| head -60`.
- r1.exclusions: run2 guessed rather than searched -- "For URL blocks, what is size_mb?
  Probably size_mb computed on the payload string regardless" (g8_msg2.txt:3983) -- while
  #engineering :79-80 answers it outright and even names the bug it shipped.
- r2.failure_behavior: run1 read the wrong 2025-05-13 #pipeline window and declared
  "normalize_detail settled"; the one-warning rule is stated four times in two channels.

**g11 r1.failure_behavior** (run1). The merge is stated outright at
plant/messages.jsonl:135 -- "both carry forward onto it. neither set gets dropped". The
agent surfaced the thread's opener in its own Mattermost search (g11_msg1.txt:2851),
dumped the channel to a file, read three narrow `sed` windows that all miss the
2025-03-19 block, and grepped the merge lines into /tmp/ft2.txt without ever reading past
its first 45 lines. Never found it.

---

## Hardening, none of which caused a failure here

- **g7**: `docs/engineering/recovering-an-interrupted-agent-turn-...md` invents a two-file
  design (`turn_ledger.jsonl` as the append log; the real log is `responses_0.jsonl`) and
  contradicts three graded facts -- off-by-one tolerance vs. "any disagreement raises",
  "rematerialize" on load vs. "load writes nothing", "drop the torn final line" vs. "no
  log line is ever truncated". Same failure mode as DEFECT 1.
- **g8**: the graded number 45 appears in one channel only (#code-review, four messages),
  and `:47` "45 MB is about where they stopped accepting us, so under that" reads in
  isolation as "pick something below 45". Seating one `45 MB` remark in a second channel
  removes the wobble.
- **g11**: two problems on the same fact. (a) The merge has a single carrier, phrased in a
  synonym -- line 134/135 say "labels" where every graded identifier says `reasons`, so a
  `reasons`-keyed search misses it. (b) Continuity contradiction: line 131 (03-19)
  describes name-matched update as current behaviour, while lines 123/129 (03-25, six days
  later) say "every save is a fresh entry right now, the name isnt consulted at all" and
  "nobodys been in the save path yet". Under this world's later-wins convention an agent
  that found both could discount the only carrier as stale.
- **g11** key prose: the arm table claims the 47 remarks live "in chat, the wiki and mail";
  comments.jsonl is empty and there is no docs/ or emails/. Same for g8. Stale, harmless.

## Sweep that came back clean

Every name the four suites resolve by `sym(...)` is present in either the ticket or the
corpus -- no graded identifier is unreachable in any of the four tasks.


---

# Second pass — verification and changes applied (2026-09-09)

## g7 `r1.failure_behavior` — CONFIRMED, fixed

Two pieces of evidence the first pass did not have.

**The plant's own record contradicts the rendering.** `g7.r1.fix28` in
`task_generator/out/agent-turn-ledger/clues/plant.json`:

    settles:          "...and the module has no second error to raise"
    forbidden_terms:  ['TurnLedgerCorruptError', 'corrupt', 'unreadable', ...]
    carrier.why:      "...It confirms the silent-adopt behaviour and the
                       single-exception module..."

Phase 4 then wrote `so the parse failure gets its own answer` -- the negation of its
own `settles`, steering the reader to the exact class the clue's `forbidden_terms`
names. Not an interpretation; the generator recorded the intent and the rendering
broke it.

**The agent cites the invented line verbatim.** `g7_msg2.txt:4707`:

> if unparsable -> TurnLedgerCorruptError? **Chat said parse failure "gets its own
> answer", not desync.** Our corrupt error takes (path, line_number, reason) -- for a
> whole-file JSON, line_number 1. That fits nicely.

and `:9215` -- "Corrupt sidecar gets its own exception (not desync) ->
TurnLedgerCorruptError", quoting the invented 13:19 close.

**Counter-evidence considered.** Both runs also read all three sources that support
`adopted` (emil's #code-review 2025-03-14, nils' page comment, the resume-path page)
and chose this thread anyway. The March thread does not settle it -- it answers a
question about the *version key* ("the ledgers written before that key existed?"), so
"the only thing that aborts is a version-2 mismatch" is scoped to {missing, below-2,
mismatch} and never names an unparseable file. This thread is the only on-object one.

APPLIED -- three turns rewritten in place, message count unchanged, turn 0 (the
`located()` anchor) byte-identical:

    13:12  was  honestly i'd have expected a raise there too. thats a bad shape to be quiet about
           now  huh. i'd have guessed it bails on that
    13:16  was  ...and that one is the wrong thing to reuse here, so the parse failure gets its own answer
           now  ...and theres nothing for it to be in disagreement with when the file wont even parse
    13:19  was  mhm. a file that wont load isnt a desync in any reading of the word
           now  ...in any reading of the word, and theres no other one in there to reach for

Ten files: four arms' `plant/messages.jsonl`, four `solution/hidden_requirements.md`,
`clues/plant.json`, `clues/plant-data/messages.jsonl`. Verified: all four plants
byte-identical; JSON parses (261 messages); no `forbidden_terms` token introduced
(0 hits for each); all four `verbatim` identifiers still present; `inject.located()`
resolves all 51 remarks with `g7.r1.fix28` unchanged at #engineering / 2025-04-10
16:33:49 / 7 turns, so the located map needs no rebuild. `.located-corpora/` cleared.

## g9 `r2.failure_behavior` — CONFIRMED as wrong content, fixed; weaker on score

**The page is factually wrong about the graded function.** `fixtures/oracle.patch:293-303`:
`format_batch` has exactly ONE drop category, `except ExampleTooLongError`. The page's
absorbed-and-counted list has four, and its parenthetical spells out
`InvalidRoleSequenceError`'s own triggers -- `oracle.patch:453` `reason="empty"` (empty
message list) and `:457` `reason="unknown_role"` (no role on a message).

**The clue it carries was scoped away from this.** `g9.r2.say24`:

    settles:          tokenizer without apply_chat_template -> TokenizerCapabilityError, abort
    forbidden_terms:  ['propagate', 'pytest.raises', 'InvalidRoleSequenceError', 'ExampleTooLongError']

The clue was meant to be silent on the role half. The body volunteered a ruling anyway
and got it backwards.

**But the score evidence is thin, and this is stated plainly:** located v5 is 2/3, and
the blind arm is a single rollout. The change is justified by the page being wrong, not
by the measurement.

APPLIED -- two lines, seven files (four arms, `clues/plant.json`,
`clues/plant-data/...md`, `clues/README.md`):

    :19  was  (empty message list, no role on a message, that kind of thing)
         now  (no content on a message, a metadata payload past the provider's
               per-request limit, that kind of thing)
    :30  was  failures that are properties of the configuration rather than of any
              individual row
         now  failures that say the thing handed to the pass was built wrong, rather
              than that one row happened not to fit

Neither edit answers the graded question; the first stops the page naming the graded
exception's triggers as drops, the second stops the taxonomy excluding a per-row error
from the abort bucket by construction. `inject.located()` resolves all 57 remarks,
`g9.r2.say24` unchanged. Three `.rollouts/*_transcript.md` files were caught by the
first pass of the replace and have been restored -- historical evidence, not corpus.

## g11 run 2 — a plausible fix, not a diagnosis

**Retracted from the first pass:** "62 watchdog interventions" is not evidence. Every
run in this set has 41-51 (g7: 44/41, g8: 43/51, g9: 43, g11: 46/62). 62 is elevated,
not categorical. There is no `nproc`, OOM, or disk evidence anywhere in the transcript.

What is certain: the trial did not complete, the agent saw contradictory terminal
frames, git HEAD flipping between three commits and files vanishing between commands,
and it did none of that to itself (no `git reset`/`checkout`/`stash`/`clean` in the run).

What is structural, and the only lever available:

| arm | cpus |
|---|---|
| g7, g8, g9 `-world-hosted` and `-world-located-hosted` | **8** |
| g11 (and g10) `-world-hosted` and `-world-located-hosted` | **2** |

`0e81bc4` raised g7/g8/g9's hosted arms 2 -> 8 and silently missed g10 and g11 -- the
commit message never mentions cpus. All four evals ran on the same backend and
g7/g8/g9's rollouts started, so the runner had >= 8 cores; g11's container was pinned to
2 of them while running the whole world (postgres, mariadb, mattermost, bookstack,
gitea + CI runner, maddy, nginx) plus the agent and its pytest.

APPLIED: g11's two hosted arms set to `cpus = 8`, with a comment naming the failure.

**This carries a real cost, stated rather than buried.** Per `build_tasks.py:135-160`,
Docker REFUSES a `cpus` above the host count instead of capping it, so a g11 eval
submitted WITHOUT `--machine-type e2-custom-8-16384` will now error every rollout at
`docker compose up`, with zero spend. And `tasks validate` has no such flag, so this arm
can no longer be validated at all. That is the regime g7, g8 and g9 already live in.
`build_tasks.py` resets this to 2 on a rebuild, same as g6's hand-set 8.

g10 has the identical asymmetry and was left alone as out of scope.

## Outstanding, not changed

The fabricated `1.00`s. `refresh_answer_key.py:62` writes an unmeasured `**1.00**` into
every located row, and the `clues` rows were copied the same way. The keys for g1-g11
all carry them. Two clean options: drop the `measured` column (what `tg/inject.py`
already decided and documented) or populate it from `rollouts pull` per version. Left
for a decision rather than half-fixed across two of eleven tasks.

---

# Readiness for g7 / g10 / g11 (2026-09-10)

**Horizon holds the OLD grader** for all three (pulled v4/v7/v4: `run_suites.py` md5
`cb745504`, no `DROP_USER`). The rewrite that drops pytest to `nobody` landed on disk at
23:19, after the 20:55/20:57 pushes. So an eval today grades with the grader that graded
the 2026-09-08 evals.

The new grader, checked on the local g11 world twin before anyone re-pushes it:

| agent | reward | hidden facts | provenance | ran as |
|---|---|---|---|---|
| oracle | 1.00 | 10/10 at 1.0 | 3/3 | nobody:nogroup, baseline staged 71 files |
| nop | 0.00 | 10/10 at 0.0 | 0/3 | nobody:nogroup, suite_ok 1.0 |

No false positives, no false negatives. Safe to ship on a re-push.

Per-fact, lumen only:
- g7: every fact 2/2 except r1.failure_behavior (fixed in v4, no agent has read it yet)
  and r1.rule (1/2 blind, 2/2 located -- hard, fair).
- g10: every hidden fact passed in all 6 lumen runs (hosted v3, v4; located v2, v3).
  biggie-max 0/2 on every hidden fact with green code: every failure is "not
  implemented", so that's the agent. Naive fails all 8 hidden facts, so the ticket
  doesn't leak. Sound, but may not discriminate for lumen.
- g11: merge fact -- the 10 budget-killed v7 transcripts show 6 found the remark and
  all 6 merged; 4 never found it. Hard, fair.

## g10 pushed with the grader fix (2026-09-10)

The only change is the grader rewrite that stops pytest running the agent's code as root:
pytest drops to `nobody:nogroup`, the submission is off `PYTHONPATH` and goes onto
`sys.path` behind the stdlib, `/tests` is opened to the drop group read-only and
`/logs/verifier` is locked to 0700. It closes the reported `src/sitecustomize.py`
full-score forgery. It does NOT close the `atexit` rewrite of the child's own
`junit.xml`; see lessons.md.

| arm | before | after |
|---|---|---|
| world-hosted `34977c02` | v4 (vulnerable, md5 cb745504) | **v5** (fixed, md5 c098ff45) |
| world-located-hosted `17a850b2` | v3 | **v4** |

No plant, ticket or task.toml change; still 2 CPUs. Pulled v5 back and confirmed the served
`run_suites.py` is the fix.

| check | where | result |
|---|---|---|
| oracle | local g10 world twin | 1.00 -- 8/8 hidden, provenance 3/3, ran as nobody |
| noop | local g10 world twin | 0.00 -- 0/8 hidden, provenance 0/3, ran as nobody |
| oracle | **Horizon hosted validation** `val-34977c02-1789059906185` | **PASSED, 1.00** |
| noop | **Horizon hosted validation** `noop-val-34977c02-1789059908109` | **PASSED, 0.0667** = 1/15, `suite_ok` only |

g7 (v4), g9 (v7), g11 (v7), g8 and g1-g6 hosted arms still serve the vulnerable grader.

---

# g7 v4 eval 94bf8242 — 10 lumen runs, none at 1.00 (2026-09-10)

Scores 0.92, 0.92, 0.92, 0.83, 0.75 x4, 0.67, and run 5 at 0.07. r2 is perfect in
all 9 runs that pushed; every loss is in r1. **5 of the 9 lost points ONLY to the
two task defects below and would have scored 1.00 without them** (runs 1, 2, 8, 9,
10).

The v4 sidecar fix worked: the unparseable -> adopted assertion (test_r1.py:200)
now passes in every run that reached it. The failure_behavior losses that remain
are the next assertion down, not this one.

## TASK DEFECT A — the corpus settles "log side only"; the grader wants both sides

Runs 1, 2, 6, 10. Costs failure_behavior AND observability (test_r1.py:216, :301),
so 8 fact-losses.

Grader (key :95-96, :128): `TurnLedgerDesyncError` stores all five as attributes,
`.recorded_responses == 3`, `.recorded_last_author == "advisor"`.

Corpus, mail thread "which state files does the resume consistency check actually
cover", 2025-06-11 -- the carrier of `g7.r1.l12`:

    dermot 15:10  am I right that .log_responses and .log_last_author are the log
                  side only, and that there is deliberately no matching pair for
                  the ledger side?
    nikolai 16:15 Dermot, on your question: yes, the log side only. That was
                  deliberate. ... So the settled version is: ... with
                  .log_responses and .log_last_author on the exception carrying
                  the log side. That is what is in the tree now and I am not
                  touching the wording again.

`g7.r1.l12` `settles`: "fails with a dedicated error carrying both sides". The
invented question-and-answer inverted it. The only other carrier, `g7.r1.l16`
(April), says the error "surfaced with recorded_responses 3" -- which reads as
values in the message as easily as attributes, and is two months older than an
explicit settlement.

All 9 pushed runs read nikolai's reply. The 4 that omitted recorded_* followed it;
the 5 that stored them overrode it. The grader rewards contradicting the latest,
explicit word.

FIX (not applied): rewrite dermot's 15:10 question and nikolai's 16:15 answer so
both pairs sit on the exception.

## TASK DEFECT D — a graded name with one unsearchable carrier

Runs 2, 3, 8, 9, 10 (5 fact-losses; runs 8 and 9 lost nothing else).
`TURN_LEDGER_FILENAME` occurs once in the corpus, in a wiki comment (BookStack does
not index comments). Perfect split: the 5 runs that never saw the string all wrote
`SIDECAR_FILENAME = "turn_ledger.json"` -- the exact value, a guessed name. The 4
that saw it all used it. It measures whether the agent opened that one page's
comments, not reconstruction.

FIX (not applied): give it a second, searchable carrier (chat or mail).

## Agent mistakes -- status handling (7 fact-losses)

- run 3: absent sidecar -> "created" (its docstring says so). The corpus says missing
  -> adopted twice (#code-review 03-14, konrad 04-09).
- run 7: correct load, but re-derived with a hard-coded status="created" after each
  append, so a resumed run reports "created" (test_r1.py:312).
- runs 4, 6: re-ran verify_sidecar on every rebuild, so a fresh run's first write
  reports "verified" (test_r1.py:184). The corpus: "first write carries created,
  verified is only a load where both matched" (l8); "the only thing that ever writes
  that field is the resume path" (fix30).
- Contributing, not decisive: fix30's last three invented turns ("leaks the
  placeholder", "nobody wrote down what the empty case is supposed to report", "we
  need to be intentional here eventually") make the fresh-run status read as
  unsettled.

## Borderline -- run 4's r1.rule

`write_sidecar(str(tmp_path), ledger)` hit a reversed-argument implementation. The
corpus never states write_sidecar's argument order; verify_sidecar's is stated ("hand
it the work dir and the ledger") and write_sidecar is called "the other half". One
run.

## Not the task -- run 5

22 turns, $0.72. The model returned two empty replies in a row after reading an
ordinary wiki page, and the harness stopped. The whole transcript is 104k chars, so
this was not context exhaustion. Nothing was pushed.

## Defect A caused the losses -- it is not just latent (checked 2026-09-10)

The four runs that omitted `recorded_*` wrote nikolai's settled answer into their own
docstrings:

    run 1  "Report the sidecar's claim and the log's, keeping the log side on the object."
    run 2  "Store the sidecar path and the log side of the comparison."
    run 6  "Report the sidecar's claim first and carry the log side on the exception."
    run 10 (same code, stores only path + log_*, reason not written down)

The runs that stored all five cite the April mail (`g7.r1.l16`) instead, e.g. run 7:
"recorded_responses and recorded_last_author are on the desync error too (from the
ledger side)". Run 8 wrote nikolai's phrasing ("hand back the log side on the object")
and stored all five anyway.

Reliability of eval 94bf8242 for g7, with D accepted as fair (the ticket explains
comments are unindexed and says to fetch pages whole):
- binary pass rate: 0/10 measured; fixing A alone flips only run 1 (its only losses
  were A) -> at most 1/10. Essentially reliable.
- mean reward: 0.69 measured; ~0.79 if runs 1, 2, 6, 10 had kept their two facts.
  Understated by ~0.10.
- per fact: r1.failure_behavior and r1.observability are contaminated; the other six
  are clean.
- a rerun on v4 reproduces the defect. Fix A first.

## Defect A fixed locally (2026-09-10) -- NOT pushed

Time did not resolve the contradiction, so the herring route did not apply. A dated sweep of
every statement about the exception's attributes (chat, comments, pages, every mail, and the
base world `data/`, which has 0 hits) put nikolai's "yes, the log side only ... settled" at
Jun 11 16:15 as the LAST word, with nothing after it.

Change: nikolai's 16:15 reply only (Message-ID
<178880237814.2304052.14317943691984005697@world.local>) now reads "no, both sides", with
.recorded_responses/.recorded_last_author carrying the ledger side and .log_* the log side.
dermot's 15:10 question stays; the same thread now answers it "no" 65 minutes later. The
opener (the located() anchor and l12's verbatim list) and dario's reply are untouched.

Written with mail_register.encode() and a Message-ID body swap (the files are
quoted-printable), across 40 copies: 8 per tree, in the 4 world arms plus
clues/plant-data (which build_tasks.py:1017 copies into the arms on a rebuild).
plant.json via `cli.py resync` (1 clue); keys via `refresh_answer_key.py --apply`.
Backup: scratchpad/backup/g7-pre-fixA.tgz.

| check | result |
|---|---|
| 40 copies | decode to the new body; headers byte-identical to the backup |
| 4 arm email trees + plant-data | identical, 8/8 |
| old reply | 0 copies left |
| located() | 51/51; l12 row and located map row unchanged (14:05-16:15, 4 messages) |
| l12 forbidden_terms / verbatim | none introduced / none missing |
| plant.json vs backup | 1 field: clues[11].invented.messages[3].text |
| answer keys | 2 lines changed (nikolai's paragraphs); 4 copies identical; refresh idempotent |
| local oracle, g7 world twin | healthcheck passed (mail ingested); reward 1.00, 8/8 hidden, 3/3 provenance, as nobody |

Pending: the QC argus run. Then push g7 hosted + located-hosted (at 8 CPUs, so no hosted
validate -- submit with --machine-type e2-custom-8-16384) and rerun.
