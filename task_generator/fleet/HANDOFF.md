# Phase C handoff — five plants, two stages left

**Written 2026-09-04 22:35 UTC.** Everything stopped on one external cause: the
Claude subscription hit its **monthly spend limit**, which failed the `claude -p`
judge call on all five tasks within the same minute. The limit resets **01:00
UTC** (or raise it at claude.ai/settings/usage).

**Nothing is lost.** Each stage writes its ledger through `clues.finish()` before
the judge runs, so every task stopped at a recorded position with its work on
disk. Resuming re-enters the state machine where it left off.

---

## Where each task is

| | run | crashed at | sources | remarks | woven | unknit | fact_conflicts | local spend |
|---|---|---|---|---|---|---|---|---|
| **g7** agent-turn-ledger | `pilot` | `consistency` | mixed | 46 | 45 | 0 | 9 | $57.70 |
| **g8** attachment-payload | `fleet1` | `reknit` (done) | **slack** | 50 | 50 | 0 | 1 | $75.05 |
| **g9** example-encoding | `fleet1` | `consistency` | mixed | 53 | 53 | 0 | 5 | $66.39 |
| **g10** token-capacity-budget | `fleet1` | `consistency` | **slack** | 46 | 46 | 0 | 7 | $71.66 |
| **g11** training-step-ledger | `fleet1` | `reknit` (done) | **slack** | 47 | 47 | 0 | 1 | $75.52 |

**All five plants are complete and fully woven.** 242 remarks placed, every
exchange written, `unknit: 0` everywhere — no invented speakers, no monologues,
every claim surviving its carriage check. That was g1's worst defect class.

Three tasks are deliberately **slack-only** (g8, g10, g11) and two mixed
slack/notion/email (g7, g9), at the user's request.

---

## How to resume

The limit must have reset first — check with a one-line `claude -p 'say ok'`.

```bash
cd /home/nidhi_bespokelabs_ai/SWEWorld

setsid nohup python3 task_generator/fleet/orchestrate.py resume pilot \
  --through C --from consistency --stop-after horizon.blind+spec+clues \
  --budget-usd 900 > /tmp/g7-resume.log 2>&1 < /dev/null &

setsid nohup python3 task_generator/fleet/orchestrate.py resume fleet1 --force \
  --through C --from consistency --stop-after horizon.blind+spec+clues \
  --budget-usd 900 > /tmp/rest-resume.log 2>&1 < /dev/null &
```

`--force` is needed on `fleet1` only if another orchestrator for that run is
alive; check first with `ps -eo pid,cmd | grep orchestrate`. **Two drivers on
DISJOINT tasks of one run are safe** (`state.update` takes a flock); two drivers
on the same task are not.

Watch with `python3 task_generator/fleet/orchestrate.py status fleet1`.

### Why `--from consistency` for all five

g8 and g11 have not run `consistency` yet; g7, g9 and g10 have, but under a
**stale orchestrator** (see gotcha 1) and, for g7/g9/g10, under the
**source-blind** version of the check (see gotcha 2). Re-running it costs ~$1.50
a task and produces a conflict list you can actually trust.

---

## What is left

Per task: **`consistency` → `prove --runs 3` → `horizon --arms blind,spec,clues`**,
then the run stops (`--stop-after`). Roughly **$8–12 and 45 minutes each**,
running concurrently.

- **`consistency`** — a model call per graded fact. Asks whether any remark
  states a fact wrongly *and is the last word on it*. Non-zero exit is normal
  when it finds something; the judge decides.
- **`prove --runs 3`** — the real verdict. Builds an implementation from the
  ticket plus the planted remarks alone, three times, and scores it with the
  same suite the paid arm uses. **A fact that fails on ANY run fails.** Read
  `out/<slug>/clues/proof.md`: facts failing on the *same* runs are ONE defect in
  ONE remark, not several.
- **`horizon`** — free, seconds. Emits the three apex arms. Its `unsolvable()`
  gate refuses if the rendered clues digest never types a graded name.

Hosted push/validate/evaluate are **deliberately out of scope** for this run —
`--stop-after horizon.blind+spec+clues` halts before them. They remain available
by resuming without that flag.

---

## Gotchas that will bite you

1. **A long-running orchestrator caches the code it started with.** Python
   imports once. An orchestrator started before a `fleet/` or `tg/` edit will not
   see it — this is why g7 parked saying `rewrite_exchanges` "is not on this
   menu" when it had just been added. **After changing fleet or tg code, restart
   the orchestrator.** Stages already running are unaffected and complete fine.

2. **`fact_conflicts` counts from before 22:20 UTC are source-blind and
   overstated.** `fact_consistency` used to show the judge only remarks whose
   `covers` names the fact — and `normalise()` truncates `covers` to two entries.
   A remark that resolves the conflict from mail or the wiki was invisible. Fixed
   (it now shows every remark in the requirement, labelled with source), but
   g7's 9 and g10's 7 were measured before the fix.

3. **A fresh plant always exits non-zero.** `finish()` appends a `never run —
   cli.py consistency …` row to `fact_conflicts`, which is HARD. `gates.clue_gate`
   filters that into `detail["owed"]`; do not "fix" it.

4. **`unstated: absent` findings are frequently stale.** They come from
   `claims.json`, which `settle` writes *before* its own rewrites. The judge
   verifies against the live plant and overrides — correctly — but the gate
   raises a false hard finding at every plant stage. **Unfixed.** The clean fix is
   to treat `unstated` as soft when `settle` has run since `claims.json` was
   written, mirroring the `owed` logic in gotcha 3.

5. **The judge can state a wrong fact confidently.** One decision claimed "$0.87
   left" of budget when the task had spent $62.60 of $150. Its *reasoning* was
   sound. Check its numbers, not just its logic.

6. **Everything runs on the OAuth subscription**, never the API key.
   `tg/auth.py` removes `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` from the child
   environment and sets `CLAUDE_FORCE_OAUTH=1`; `agent.run` aborts the run if the
   CLI ever reports using the key. Verify with
   `cat /proc/<claude pid>/environ | tr '\0' '\n' | grep -i anthropic`.

---

## Changes made this session — do not revert

### Shared `tg/` (each is a separate, reviewable fix)

| file | change | why |
|---|---|---|
| `tg/horizon.py` | preserve `.rollouts/` and `.validation/` across the re-emit `rmtree` | it deleted phase B's rollouts, the only evidence `verdict_ab` reads; cost three manual restores and one false BLOCKED verdict |
| `tg/horizon.py` | `ENV CURATOR_DISABLE_RICH_DISPLAY=1` in the DOCKERFILE template | curator's trackers start a live display on construction and wedge a non-TTY agent shell; 3 of 12 g7 blind rollouts died that way. CONFTEST and GRADER already set it — the agent never inherited it |
| `tg/clues.py` | `unclashed` added to `SOFT` | computed by `finish()` and read by nothing — the exact "a check with no reader is not a gate" disease |
| `tg/clues.py` + `tg/corpus.py` + `prompts/clue_place.md` | `Corpus.purposes` from `data/channels.yaml`, `channel_guide()`, `OFF_TOPIC_ROOMS = ("random","general")` | placement ranked rooms by token overlap and was never told what a room is FOR; remarks about tokenizers landed in `#cookbooks` under a `why` that said no room fitted |
| `tg/clues.py` | `rebalance()` takes the requested sources and renormalises | it walked the global 40/30/30 MIX regardless, so `--sources slack` was cosmetic — a plant asked for slack-only came out 21/8/8. **Cost $34 in discarded plants** |
| `tg/clues.py` + `prompts/clue_consistency.md` | `fact_consistency` shows every remark in the requirement, labelled by source | see gotcha 2. `repair` was fixed the same way for the same reason; `consistency` is newer and never got it |
| `tg/clues.py` | `conflicts_by_clue()` seeds `reknit --redo`'s `defect` from the `fact_conflicts` rows naming that clue | a redo was a re-roll: same prompt, different sample, aimed at nothing. g9 spent six rounds and ~$9 rewriting the same three exchanges — 13 → 11 → 7 → 9 → 4 → 6 conflicts. `stage_thread` has taken a `defect` since it was written; nothing filled it on a redo |

### `fleet/` (all fleet-local)

Thirteen defects found in a pre-flight review, four fatal after money is spent —
`verdict_clues` unimplemented, a 2h timeout shorter than `clues` (which has **no
checkpoint**), caps below cost, and `repair` jumping *forward* past five stages.
Plus per-task `--sources`, `--stop-after`, per-phase rewind counters, and the
`plant`/`emit_clues` judge situations with the `rewrite_exchanges` action.

`rewrite_exchanges` is the repair for `fact_conflicts`: it runs
`reknit --only <ids named by the gate> --redo`, re-weaving just those exchanges
(~2 calls each). `replace` re-places with identical wording and does **not** fix
an exchange that says the wrong thing; `reclues` throws away sound placement.

Two later fleet-local fixes, made while the consistency loop ran:

- **`gates.clue_gate` no longer reports `unstated: absent` as hard once
  `reknit_at` is stamped, and re-checks `missing_identifiers` against the woven
  exchanges.** Both are computed from the remark *texts*; after `reknit` the
  corpus a reader sees is the exchanges, and that is usually where a name gets
  typed. Every term an `absent` row called "nowhere in the corpus in any
  spelling" is in them — `dataset_signature` 4x, `AttachmentError` 7x,
  `CheckpointInfo` 7x, `ValueError` 5x — and g8 was held hard on the word
  `calls`, which four of its own turns say. It was a false hard finding every
  round on every task, overridden by the judge every time at ~$0.25. After the
  fix all five report **only** `fact_conflicts`, which is what the gate is for.
- **`consistency` is a sample, not a measurement — a conflict now earns `hard`
  by surviving a re-read.** Measured over 26 rounds across the five tasks: an
  exchange *nothing touched between two runs* is routinely clean in one and a
  hard conflict in the next. g10's `s3_l1/l2/l3` were rewritten once, came back
  clean, were not touched again, and all three were flagged on the next pass;
  g11's `l14` and `r2.l1` did the same, and so did g9's `l-scope-2`. Over the
  last three rounds per task there are **11 conflicts that repeat and 15 that
  appear once and never again**, and the counts never converged — g7
  `9→9→14→12→11→11`, g10 `8→10→8→9→8`. `worker.last_conflicts()` now passes the
  previous round's clue ids into `clue_gate`, and a `fact_conflicts` row is hard
  only if that round named the same clue. The first run has nothing to compare
  against and every row stands. Replayed over the recorded history this drops
  184 hard rows to 151 without losing a single conflict that ever repeated.

  **This does not make the loop converge, and it is not supposed to.** ~3–7
  confirmed conflicts per task survive. `prove --runs 3` is the measurement that
  decides solvability; `consistency` is a stochastic judge and must not be
  treated as a wall.

- **`worker.act` compares against `MAX_REWINDS[phase]` on the
  `repair`/`replace`/`reclues` path.** `MAX_REWINDS` became a dict this session;
  `rewinds > MAX_REWINDS` raises `TypeError` instead of parking.

Both need a driver restart to take effect — the orchestrator imports `fleet.*`
once, while every stage runs as a fresh `cli.py` subprocess. They were left to be
picked up at the next natural restart rather than killing five in-flight
`consistency` passes (~$1.50 each) to save ~$1.25 of judge calls.

---

## Verifying a finished plant

```bash
python3 task_generator/fleet/orchestrate.py verify        # free, every gate on every task
```

Per task, the evidence worth reading:

- `out/<slug>/clues/proof.md` — all facts green across all 3 builds
- `out/<slug>/clues/README.md` — the plant in date order, with source and carrier
- `gates.clue_gate(task)` — 0 hard
- source mix matches intent (slack-only for g8/g10/g11)
- zero invented speakers (`unknit: 0`)

The corpus is pinned: every clue stage runs with
`--run .../data_gen/build/phase4/runs/corpus`, so `ledger["corpus"]` records the
real run rather than the `latest` symlink. **Keep passing it** — `plan.py` injects
it automatically for stages in `plan.TAKES_RUN`.

---

## TODO once g7–g11 are through: move `prove` before `reknit`

**Agreed with the user, deliberately deferred to after this run.** Do not do it
mid-flight.

`prove` builds from `source="remarks"` — `steps.clue_spec` renders
`horizon.render_remarks(task)`, byte-identical to the hosted clues arm's prompt,
which shows remarks and not exchanges. So **`prove` never exercises reknit's
work**, and `repair` rewrites remarks. The current order therefore pays for
reknit and every `consistency` round BEFORE learning whether the remarks prove
out, and any `repair` afterwards leaves that remark's woven exchange stale — so
reknit has to run again, and consistency after it.

| stage | reads | invalidated by a remark edit |
|---|---|---|
| `reknit` | remarks → writes exchanges | **yes** |
| `consistency` | exchanges | yes |
| `prove` | **remarks only** | no |
| `repair` | writes remarks | — |

g7 is the live example: `prove` returned 5/9, the judge blamed `verify_sidecar`
being in no remark, and `repair` is now rewriting remarks whose exchanges were
woven an hour earlier.

**The change:** in `tg/recipe.py`, move `Stage("prove", ("--runs", "3"), …)` to sit
after `reorder` and before `reknit`, leaving `consistency` last:

```
clues → settle → reverse → reorder → prove → reknit → consistency → horizon
```

`fleet/plan.py` imports `recipe.STAGES` rather than copying it, so the fleet
follows automatically. Things to check when doing it:

- `recipe.py`'s `reorder` note says it must run BEFORE `reknit` because it
  overwrites `invented`; that still holds and is unaffected.
- `cmd_repair` `SystemExit`s without `clues/proof.json`, so `repair` only becomes
  a legal judge action once `prove` has run — moving `prove` earlier makes it
  legal EARLIER, which is the point.
- `worker.situation_for()` maps `prove` to its own situation; check the `plant`
  situation's stage list still matches the new order.
- The counter-argument for today's order is that `consistency` catches a corpus
  that argues with itself before $10 of proofs. That argues for keeping
  `consistency` in the chain, not for keeping it before `prove`.

## TODO 1b: `repair` MUST re-weave the exchanges it invalidates — correctness, not tidiness

Bigger than the reorder above, and the same root. `repair` rewrites REMARKS.
Every rewritten remark's woven exchange is stale the moment it does, and nothing
in the chain re-weaves it. `prove` cannot see this because `prove` reads remarks
(`steps.clue_spec`, `source="remarks"`). Only `unknit`, `inject` and the world arm
read exchanges — so a task that goes `repair -> prove -> horizon -> done` SHIPS A
CORPUS WHOSE CONVERSATIONS CONTRADICT ITS OWN REMARKS, with a clean proof.

Measured today, four times, and the scale was worse than it first looked:

- **g7, one repair invalidated NINE exchanges** across `l4`, `l5`, `l11`, `l12`,
  `l13`, `l15`, `l16`, `say21`, `fix27` — 21 `unknit` rows. Two of them carry the
  material g7's failures actually turn on: `fix27` is the remark repair ADDED to
  state the `created`/`adopted`/`verified` vocabulary, and its exchange typed none
  of those four names; `l4` was corrected to `sidecar_state()` while its exchange
  still said `ledger.sidecar_state` — the exact method-vs-attribute defect that
  makes `r1.rule` fail with `TypeError: 'dict' object is not callable`.
- **g8 `l14`** — repaired to `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...]`, exchange
  left saying "auto, low and high" in prose. `prove` passed it **10/10** and the
  task was marked done; caught only because `cli.py inject` happens to check
  verbatim coverage before writing the world arm.
- **g9 `l-scope-3`, `say24`** — same shape after its repair.

**The fix:** `cmd_repair` should end by running `reknit --only <the ids it
rewrote> --redo`, unconditionally. It already knows which remarks it touched. Until
then, ANY manual `repair` must be followed by hand with that command, and the
plant checked for `unknit: none` before `prove` or `inject` is trusted.

## TODO 2: a planted `verbatim` string loses its boundary in prose

Same batch as the reorder above — deferred, not urgent, but it costs a fact every
time it happens.

`verbatim` stores the exact graded string. The remark then quotes it inside an
ordinary sentence, and the sentence's own punctuation becomes indistinguishable
from the string's:

    verbatim : "... prompt tokens would survive, minimum is 16"      <- no full stop
    remark   : "the refusal line reads exactly: ... would survive, minimum is 16.
                num_messages rides along as an attribute, it isn't printed."
                                                              ^ whose period?

A builder includes the period and the assertion fails on one character. Measured:
g9 `r1.failure_behavior` 1/3 (`'...minimum is 16.' == '...minimum is 16'`) and g7
`r1.failure_behavior` 0/3 (`"...by 'client'." == "...by 'client'"`) — the same
defect in two of five tasks. g7's `repair` happened to fix it by putting an em
dash after the quote; nothing made that reliable.

**The fix** is in the planting prompt, not in the plants: when a remark carries a
`verbatim` string, require it delimited so the end is unambiguous — backticks
around it, or an explicit "and nothing after it". Check `prompts/clue_tree.md`
and `prompts/clue_place.md` for where `verbatim` is handed to the writer, and
`clues.stage_thread`'s `verbatim=` block, which already tells reknit "these names
must be typed literally" but says nothing about where they stop.

### TODO 2b: the same defect for a symbol's SHAPE, not just a string's edges

Widen TODO 2. The corpus reliably conveys a graded symbol's *spelling* and
unreliably conveys its *form*, and the form is what the suite calls:

- **g7 `r1.rule`, 0/3 deterministic.** The requirement is
  `TurnLedger.sidecar_state() -> dict[str, Any]` — a METHOD returning a dict. Both
  the remark (`l4`) and its woven turn say `ledger.sidecar_state`, no parentheses.
  A builder makes it an attribute holding a dict and the suite's
  `ledger.sidecar_state()` raises `TypeError: 'dict' object is not callable`.
  `sidecar_state` is not in the ticket, so the corpus is the ONLY source and it
  teaches the wrong shape.
- **g9 `r1.failure_behavior`, 1/3.** A quoted message whose end is
  indistinguishable from the sentence's full stop.
- **g8 `r2.failure_behavior`, 1/3.** `_SUPPORTED_IMAGE_DETAILS` given as prose
  ("auto, low and high") rather than as the tuple the suite compares.

Three of five tasks lost a fact to the same root cause: **a remark that names a
graded symbol must pin its form** — `name()` for a callable, the literal tuple for
an ordered constant, a delimited quote for an exact string. That belongs in the
prompt that writes remarks carrying `verbatim`, not in per-task repairs.

## TODO 3: a first sighting on the LAST round is never confirmed

The repeat-to-be-hard rule demotes an unconfirmed `fact_conflicts` row to soft and
relies on the next round to confirm it. If the task PASSES that round there is no
next round. g8 went to `prove` carrying two never-confirmed r2 conflicts that way
(`say23` deduping a url and a base64 block to one row, `l15` scoping the detail
warning to any explicit detail). Consider requiring a genuinely clean read — no
demoted rows — before a task leaves `consistency`, rather than merely no repeats.

## TODO 4: a second `rewrite_exchanges` on the same clue should escalate to `repair`

`rewrite_exchanges` rewrites the CONVERSATION around a remark. It cannot fix a
remark whose own text states the wrong thing — re-weaving just produces a new
exchange faithfully carrying the same wrong claim.

Measured, twice, in this run:

- **g9 `r2.l9`.** `consistency` named it round after round on the `dropped_indices`
  numbering. It was re-woven twice, appeared to clear, and `prove` then returned a
  deterministic 0/3 on `r2.rule`: the remark says the indices "only count among the
  ones we skipped", against the graded INPUT-position rule. The gate was right the
  whole time and the repair was aimed at the wrong layer.
- **g8 `r1.say23`.** Same shape — the remark said `len(b64)/1024**2` where the
  suite grades `get_base64_size`. Caught only by reading the helper's body.

So the rule: **the first `rewrite_exchanges` on a clue is reasonable; a second one
on the SAME clue is evidence the defect is in the remark.** `worker.act` already
records which clue ids each `rewrite_exchanges` named, so it can refuse a repeat
and tell the judge to choose `repair` instead. Cheap to implement, and it converts
the most expensive failure mode in this run — paying to re-weave a sentence that
was never going to become correct — into one paid pass that can actually fix it.

Note this does NOT undo the sampling finding: 15 of 26 conflicts never recurred,
and the repeat-to-be-hard rule took the gate from 3-14 findings to 1 per task. The
two facts sit together — a conflict that vanishes was noise, and one that survives
an aimed rewrite is a remark defect.

## TODO 5: replace `required_names` with the suite's own `sym()` names

`surface.required()` parses graded names out of the requirement PROSE, and the
list it produces is wrong in both directions at once. Measured on these five:

    g7.r1  ['A', 'No', 'TURN_LEDGER_FILENAME', 'TURN_LEDGER_VERSION',
            'TurnLedgerDesyncError', 'exists', 'ledger.sidecar_state',
            'read_sidecar', 'turn_ledger.json', 'write_sidecar']
    g8.r1  ['AttachmentTooLarge', 'MB', 'Prompt', 'TooManyAttachments',
            '_ATTACHMENT_COUNT_LIMIT', '_OPENAI_TOKENS_PER_DOCUMENT',
            'calls', 'count', 'limit', 'size_mb']

Too loose — `A`, `No`, `exists`, `MB`, `Prompt`, `calls`, `count`, `limit` are
ordinary words. Too tight — `verify_sidecar` is missing from g7's list although
`test_r1.py:98` demands it by name through `sym()`.

Three separate costs in this run:

1. **A false BLOCKED.** `cli.py horizon` refused to emit g8's clues arm — "no
   remark says `calls`" — on a 10/10 plant. Emitted with `--force` after checking
   the word is in the corpus and nothing is genuinely unreachable.
2. **A missed real defect.** `verify_sidecar` was in no remark and no gate looked,
   so it cost $10 of `prove` to find as 0/3 plus three correlated failures.
3. **A spurious hard finding** at every plant stage, overridden by the judge each
   time at ~$0.25.

**The fix is already written and calibrated:** `fleet/gates.unreachable_names()`
takes the suite's own `sym("...")` names, subtracts what the ticket prints and
what the corpus says, and returns exactly `['verify_sidecar']` for g7 and `[]` for
the other four. Lift that into `tg/surface.py`, have `cli.py horizon`'s refusal and
`clues.missing_identifiers` read it, and all three failure modes go away together.

The one subtlety worth keeping: a name only has to be in the corpus when the
TICKET does not print it. g11's suite names 18 symbols, 11 are absent from its
corpus, every one is in the ticket, and g11 proves 10/10.

## TODO 6: reversed time spans in the `world-located` map

12 rows across the located arms print a span whose end precedes its start —
`attachment-payload` row 2 `15:31–11:06`, `run-cache-identity` row 40
`12:42–10:34`, `training-step-ledger` row 2 `11:12–11:10`.

`build_located_arm.py:169` takes `sorted(when)[0]` and `[-1]`, which is a correct
min/max. The reversal is that a clue's text was matched on MORE THAN ONE DATE, so
the end timestamp belongs to a different day than the start. Line 221 already
guards for exactly this (`f"{clock}–{ends[11:16]}" if ends[:10] == date else ...`);
lines 214 and 230 do not.

Cosmetic — the row still names the right channel and date, so the arm is
findable — but it is in the answer key of a measured arm, and an agent that spots
an impossible range may distrust the whole map.

**DONE 2026-09-07, for three arms.** `landed()` now scopes a chat carrier's hits
to the carrier's own date before counting them or taking the span — a chat
exchange is written into one channel on one day, so a match anywhere else is a
text collision, and it was inflating counts as well as reversing spans (g7 row 5
read "an exchange of 387 messages"). Mail and wiki are untouched: a mail thread
really can run across days and `row()` already renders that.

Rebuilt and re-pushed: g8, g9 and g11's located arms — 0 reversed rows each.
**g1, g3, g4, g6, g7 and g10's located arms still carry the defect** (g7 2 rows,
g4 2, g6 1). Rebuilding them is a one-line command each and a re-push, but their
measurements stop being comparable, so it wants to be a deliberate batch.

## TODO 6b: a `doc_new` row told the reader to skip half of its own carrier

Same pass, same file. `row()` rendered every wiki-comment carrier as *"an exchange
of N **comments** … **not the page body**"*. For a `doc_comment` that is true —
the comments hang on a page the world already had. For a `doc_new` it is not: the
plant writes the page AND the comments, and BookStack's search reaches the body
and not the comments, so "not the page body" points the reader away from the half
that is findable. 12 of g9's 14 wiki rows were `doc_new`.

Fixed by carrying `carrier["kind"]` through `inject.located()` into the row, which
also stops a scan-order accident deciding the surface: `located()` reads
`comments.jsonl` before `docs/`, so a remark that landed in both was always
reported as a comment.

## TODO 7: `repair` can DEGRADE a correct remark — it needs the fact's assertions

`repair` is shown which remarks a proof blamed. It is not shown what the graded
assertions actually require. On a remark that some earlier gate called
contradictory, its safest-looking move is therefore to say LESS — which is exactly
backwards for a corpus whose only job is to carry a requirement.

Measured on g7 `r1.l8`:

    before repair : "... a first write compares against nothing, so the ledger
                     says created, not verified."          -> r1.scope passing
    after repair  : "... the status that comes back is whatever that check made
                     of it."                               -> r1.scope 1/3

The specific claim was replaced by a vacuous one and the fact fell over. The
mechanism is a two-gate failure worth remembering: `consistency` had flagged `l8`
as a fact_conflict — a FALSE POSITIVE, it confused `scope`'s `created` (a fresh
run's first write) with `failure_behavior`'s `adopted` (the load path) — and
`repair` then "resolved" that conflict by deleting the claim rather than defending
it. A false positive in one gate became real damage through another.

**The fix:** pass the fact's own assertion text (the suite lines `prove` names, or
`surface.required` for that key) into the repair prompt, and forbid a rewrite that
REMOVES a graded value or name the previous wording carried. A repair that makes a
remark vaguer should be rejected the way `stage_tree`'s re-ask rejects a worse
attempt — `reknit` already keeps the better of two attempts for exactly this
reason.

Restored by hand this session; `/tmp/g7-plant-before-l8-restore.json` is the
pre-restore copy.

## TODO 8: nothing audits the generated scaffolding around a planted remark

Found 2026-09-07 from g8's `r2.failure_behavior`, which scored **0.0 on all 12
hosted rollouts** while `prove` scored it **3/3**.

`clue_thread` writes an exchange around a remark. `l16`'s planted text is two of
its seven messages; the other five are invented. Two of those five were:

    15:25 gideon: once per process or once per block? per block would be um, a lot of lines
    15:26 dermot: once. its a config mistake, repeating it doesnt tell anyone anything new

The graded assertion is that the fallback warning fires **every** time. The
scaffolding posed exactly that question as an either-or and settled it the wrong
way, in a room where nobody argues back — and the located arm's row 48 points the
agent straight at it, so that arm fails HARDER than a blind one. Both `lumen`
rollouts shipped a module-level latch and cited it.

The thread prompt already forbids this in as many words
(`logs/clue-thread-g8.r2.l16.prompt.md:53`: *"no quantity, ratio, threshold, field
name or mechanism that is not in the remark above … it actively teaches the wrong
answer"*). Its own `question_style: either-or` knob is what manufactured a binary
that then had to be answered.

Nothing catches it afterwards, and that is the general defect: **`prove`, `settle`
and `claims.json` all read the remark text.** None of them reads the exchange the
remark was written into. A corpus can therefore contradict the answer key on every
arm while every local gate is green.

Cheapest fix: after `reknit`, run each written exchange against its requirement's
assertions and fail on a turn that settles a graded question the requirement
answers differently. That is one judge call per exchange, and it is the only gate
that would see this class at all.

## TODO 9: `settle` grades the words in a remark, not whether it names the object

Found the same day, from g9's `r2.rule` — also **0.0 on all 12 rollouts**, also
**3/3** in `prove`.

`claims.json` records:

    {"key": "g9.r2.rule", "verdict": "stated", "clues": ["g9.r2.l3"],
     "source": "assert EncodingReport.__dataclass_params__.frozen is True",
     "why": "l3 ... closes with \"agreed reports are frozen once built\", so
             immutability is decided out loud."}

The remark does say it. What `settle` could not see is that phase 4 wrote it into
a mail thread titled *"PR 643 review notes — cost fields on the response object"*,
about the per-run report rendered for finance — a different object with the same
noun. `frozen` occurred **once** in 9,809 messages, attached to the wrong thing,
and hedged into an experiment ("not entirely sure yet whether that is best
expressed as frozen dataclass"). The sibling claim `rule#1` (`is_dataclass`) was
graded *implied*, repaired by making `l4` say "dataclass" out loud, and passes.

`settle` should require a remark to NAME the graded type or symbol before it can
call a claim about that type "stated" — the assertion source string already
carries the name (`EncodingReport` here), so the check is available where the
verdict is made.

Re-anchored by hand this session onto the `#engineering` 2025-04-18 thread where
`EncodingReport`'s defaults and `==` are already being settled;
`/tmp/g9-plant-before-frozen.json` is the pre-change copy.

## TODO 10: the suite may grade a field's index when the ticket only says "gains"

g11's `open_feature` scored **0.0** on both `lumen` rollouts, which scored 1.0 on
every hidden fact. The single failure:

    assert stats_fields[-2:] == ["current_batch", "total_batches"]

The ticket says "appended in this order" for `CheckpointInfo` and only "gains" for
`TrainingStats` and `TrainingResult`. Every field is defaulted, so placing the two
beside `current_step`/`total_steps` satisfies the ticket, the record and every
existing construction site. Two of five rollouts did exactly that; the tail was a
coin flip, and one of the two that passed only got there by moving them "to be
safe" afterwards.

Relaxed to "existing fields preserved in order, both new ones present, defaulted,
in that relative order", verified against oracle / naive / pristine on `devbox`:
the discrimination is unchanged.

Worth a `trim`-time check generally: an assertion on a dataclass field's *index*
is only legitimate where the ticket says the field is appended.

