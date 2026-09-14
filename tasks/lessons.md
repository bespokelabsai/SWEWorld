# Lessons

## Judge the artefact, not its summary

Phase 4's clue gate judged `settles` — phase 3's one-clause condensation — and passed
transcripts that had lost half the remark. Whenever a check compares against a *summary* of
the thing rather than the thing, ask what the summary drops, because that is exactly what
will go missing and the check will report success.

Corollary, same bug in miniature: do not let the model return both the parts and a summary
verdict and then trust the verdict. Asked both ways in one call it answers `present: false`
on an element and `carried: true` overall, because the two questions are about different
texts. Compute the verdict in code from the parts.

## The narrow failure gets the narrow fix

A clue that came out half-said triggered a full channel-day re-simulation, which re-rolls
every other clue in the room that was already right — and in a live run came back thinner
each time. The user's instinct was better: regenerate the turn, not the day. Before reaching
for the expensive retry, ask what the smallest artefact containing the defect is.

## Two prompts about one message must not disagree — and fix it at the narrowest flag

`_bare` ("give ONLY the bare claim, no qualifying clause") and `SAY THIS NOW` (a two-part
point) both applied to the same directed turn. The persona obeyed one and dropped the other
half. The fix was not to suppress either rule but to say how they fit together — in chat the
second half is a second *bubble*.

The correction that followed matters more than the fix. I scoped it to `land_item`, which is
set for ordinary must-raise business too, so every directed turn would have become claim +
reasoning — the LLM over-explaining tell that `_bare` exists to kill. The right flag was
`land_settled`, true only on the turn landing a planted clue: a handful of turns in a run,
and the only ones where the second half is content nothing else in the corpus carries rather
than the model padding. **A rule that exists to suppress a model tell should be relaxed on
the narrowest condition that names the real exception, not the nearest one to hand.**

## Fixtures out of past runs

`build/days/specs/` was overwritten by a re-plant mid-task, but every clue's planted text,
`settles`, `covers` and `verbatim` survived in the review documents at
`build/phase4/runs/*/clues/*.md`. Ten cases with known-right answers, reconstructed for free,
and they are what turned "the judge feels too lenient" into a measurement.

## A pasted rubric loses to the instruction above it

`task_generator`'s prompts include the verifiability rubric verbatim — all 220
lines, Catalog A's "ticket gives it away" and "codebase already does it" among
them. Then, 119 lines above it, my own framing said:

> `description` — **the visible ticket**. One paragraph. It must state the API
> openly, including exact names and signatures, because the grader is allowed to
> require them.

The model obeyed the nearer, more specific instruction, as it should. The cut it
produced printed every internal helper's signature in the ticket, and **9 of 10
hidden facts came back as coincidences** — a build that never saw a requirement
passed them.

Two errors underneath it, both mine. The rubric's §1 "fully specified
input/output contract, exact signatures" constrains **the requirement**, so it can
be graded; I read it as constraining **the ticket**. And where the rubric asks
whether the existing code already does it, I asked the weaker question — name two
plausible alternatives. The alternatives were real. The codebase had already
resolved them: the blind engineer opened the function the ticket pointed at, saw
`"\n".join(...)`, and wrote the separator rule unaided.

Same shape as *Two prompts about one message must not disagree*, one level up:
**do not paste a reference document and then contradict it in your own words.**
Before adding an instruction above a quoted standard, check the standard does not
already answer the question — and if it does, quote it rather than paraphrase.

The corollary is what actually fixed it. A rule that a prompt can drop needs a
gate. `tg/leak.py` is eleven lines of real logic: take the identifiers a fact
quotes, subtract the ones the ticket prints, subtract the ones already in the
source tree, and see what is left. It flagged 8 of the 10 facts before any naive
build existed, and it did not flag the one that measured `hidden` — whose anchor
was an invented exception class. **Prompts are advice; gates are enforcement.**

## A gate that reads the model's own claims is not a gate (2026-08-28)

`coverage()` passed on g1's clues because every fact appeared in some leaf's
`covers` list — a list the model writing the leaves had written. The clues arm then
scored 0.00. Whenever a check consumes a field the generator produced, ask what
independent artifact could be compared instead. Here it was the emitted test suite:
the names it reaches for are what an implementation must literally provide, and
comparing those against the remarks costs nothing and would have caught it before a
single rollout.

Corollary for hidden-requirement work: **a name cannot be inferred, a rule can.**
Evidence, however good, does not hand a reader an identifier nobody typed.

## When every free check is green and the score is not, the check is the wrong shape (2026-08-29)

The clues arm sat at 0.70 against a spec arm at 1.00, bimodal — engage a
requirement and score 0.80–0.90, skip it and score 0.00–0.50. Before designing a
fix I measured the two checks I was about to build against the current plant:
`surface.unsaid` returned `[]`, and by a regex for "does somebody state the
decision", **0 of 9 steps failed**. Both would have shipped green and changed
nothing.

That measurement is the lesson. A new gate is worth taking against the artifact
that is already failing *before* it is built — if it passes there, it was never
going to explain the failure. The five minutes cost nothing and redirected the
whole design.

What the gate had to become: decompose against **the tests, not the prose**. A
requirement's `rule` is a 250-word paragraph and its test makes seventeen
assertions; the assertions are what is scored, are atomic by construction, and
enumerating them is an AST walk. Sixty-nine of them grade g1. Then the question
stops being "is this name present" and becomes "was a reader told, or left to
guess" — and `implied` is the verdict that had been passing as carriage all along.

Corollary, and the third of these now: **a name cannot be inferred, a rule can, and
a decision nobody makes out loud is not a rule.** A remark that reports a symptom
and stops is true, in the right room, in the right voice, and tells nobody to write
anything.

## Two mechanisms that each read the same field will contradict each other (2026-08-29)

`forbidden_terms` lists the words that would give a requirement away. `surface.py`
lists the names a test reads and therefore demands somebody type. They overlap:
fourteen of g1's remarks were flagged for carrying a term they were *required* to
carry. Neither mechanism was wrong; nothing reconciled them, because the check that
would have shown it — `leaf_problems` — was only ever run at plan time, on the
drafted sentence, before placement rewrote it.

Recomputing derived fields belongs in one place that every pass ends at
(`clues.finish`), not copied into each pass with a different hole in it. The three
that existed dropped `gaps`, `spread` and `leaf_problems` between them.

## Rank two failure modes in a prompt and you get the safe one, every time (2026-08-29)

`prompts/trim_fact.md` was asked to cut each hidden requirement down to what its
tests assert. It said dropping a graded claim was "much worse" than keeping padding,
added "when in doubt, keep it", and handed the model the assertion list. The result
went **750 words to 1590** — every fact longer, a 27-word sentence returned as 100
words of bullets saying the identical thing, and a `dropped` list that claimed to
have removed a phrase while quadrupling the length.

Nothing about that is the model being unreasonable. Given a ranked pair of risks and
no budget, it took the one it was told to prefer, and "cover every assertion" with
the assertions in view is a transcription task.

Three changes, and the second is the one that actually holds:

1. **Frame it as deletion, not rewriting.** "Return the same text with material
   removed, surviving sentences in their original wording" — a red pen, not a
   redraft. Plus an explicit word budget, and "unchanged is a correct answer",
   because several of these facts were already at their floor.
2. **Guard it in code.** `trim.shorter()` refuses any result longer than its input
   and keeps the original. Same shape and same reason as `clues.keep_wording`.
   A prompt can be talked out of a length budget; a comparison cannot.
3. **Name the specific failure in the prompt.** "Do not add a worked-example
   section or a bulleted restatement of an assertion" — the generic instruction
   was already there and lost to the ranking above it.

This is the same lesson as `tasks/lessons.md`'s first entry from the other side: a
pasted rubric loses to the instruction above it. Here a length rule lost to a
priority ordering. **Prompts are advice; gates are enforcement.**

## Make a paid pass resumable before running it, not after (2026-08-29)

The re-run of `trim` was killed after all ten model calls and before the write, so
ten paid answers sat in `logs/trim-*.stdout.json` with nothing to show for them.
`agent.run` already logs every prompt beside its reply, so `trim.cached()` keys on
the rendered prompt text and reuses the reply when it matches — eight of ten were
free on the next attempt.

`settle` needed the same thing an hour earlier for the same reason: `--dry-run` then
apply re-judged all ten facts because nothing carried the verdicts forward. Any pass
that is "look at the report, then act on it" needs the acting half to consume what
the looking half produced.

## A gate that is enforced at write time is not enforced at read time

`clue_herrings.md` forbids the herring from hinting at its own reversal, and
placement dates every herring before the earliest clue. Both rules are correct and
both are about *writing*. Neither produces the thing a *reader* needs: something
that says the reversal happened. Four herrings sat in a measured corpus never
retracted, and the plant passed every gate it had.

**Rule for myself:** when a property is "the reader can tell X", check it by reading
the rendered artifact, not by confirming the constraints that were supposed to
produce it. `render_remarks()` output is the corpus. Grep it.

## Ask which field a reader actually sees before calling a divergence a bug

Found `clue["text"]` and `placement.adapted` disagreeing on 7 remarks after `settle`
and called it a bug in my own code. It was not: `as_row` sets the ledger's `text` to
`leaf.get("adapted") or leaf["text"]`, so `text` IS the reader-visible string and
`placement.adapted` is superseded provenance. The judge, `render_remarks` and
`finish` all read `text`, so the measurement stood.

**Rule for myself:** before reporting a data inconsistency, find the one function
that renders the artifact and see which field it reads. One grep separates "the
measurement is wrong" from "a provenance field is stale".

## The local bracket beats the hosted one for anything but a headline number

Horizon's cipher-omni completion rate (2/6 on spec) confounds every arm: a 0.33
average is one completion rate and one recovery rate multiplied together, and five
rollouts cannot separate them. The same three arms on Harbor with one model gave
1.00 / 1.00 / 0.00 with n=1 each and no ambiguity at all.

**Rule for myself:** measure the bracket locally first, where the only variable is
the instruction. Spend hosted rollouts on the question the local run cannot answer.

## Correlated failures are one cause; read the assertion, not the fact name

Three facts (`g1.r1.rule`, `scope`, `observability`) failed together on 3 of 5
rollouts with byte-identical assertion errors while the other seven passed 5/5. I
first called it variance, then called it damage from a change I had just made. It was
neither: one remark said "the string `plan_fingerprint` hashed was …", which reads as
the string the function *returns*, and three rollouts implemented it that way.

**Rules for myself:**
- Perfectly correlated per-fact failures are ONE defect. Find it before sampling more.
- Read the failing assertion's two sides and name what each evaluates to. Pytest
  prints left-then-right in source order; I read it backwards once and blamed the
  wrong half of the program.
- An LLM judge asked "is this stated?" will accept a value appearing anywhere in the
  corpus as stating a claim about the expression that must produce it. That leniency
  needs naming in the prompt, and even then it may not catch a specific case — at
  which point fix the data directly and record why on the record itself.

## The artifact nothing reads is the one that drifts (2026-08-31)

The plant's invented conversations — the actual prose that would become the corpus —
had drifted from the remarks they were built around. Thirty-three of thirty-five. One
still carried the exact `l6` phrasing a measurement had already blamed for three
failed builds in five.

Nothing was wrong with any individual pass. `settle` rewrites `text`; `reverse`
appends to `text`; `finish` recomputes every derived field over `text`; the digest
renders `text`; the judge marks `text`. The conversation is the only thing in the
plant that no check has ever opened, so it is the only thing that could quietly stop
matching. It was also the thing the world was going to be built out of.

The user asked the right question before any of this shipped — *"i'm not sure if the
plant is stale"* — and it took one substring test to answer. I had been about to
insert those conversations on the strength of having generated them.

**Rule for myself:** when a pipeline has several passes and one artifact, list which
passes READ each field. A field that only ever gets written is not maintained, it is
just old. Check it before it becomes the deliverable.

Corollary on the fix: the guard is `anchor()`, which forces the holder's message to
be the remark, byte for byte, after the model has finished. **Six of thirty-five
still needed it** — the prompt says "reproduce it character for character", twice,
and the model paraphrased anyway. Prompts are advice; gates are enforcement, and this
one is a substring comparison.

## Context handed to a model is material it will use (2026-08-31)

The re-knit prompt showed each conversation the real messages from that channel-day,
so the new thread could be written around what the room was already discussing.
Three of thirty-five came back with a dozen of those real messages copied INTO the
invented thread. `g1.r2.l4` was 20 messages, most of them the room's own traffic,
which would have written a real conversation into the corpus a second time.

Nothing about that is unreasonable behaviour. I put text under a heading in the
middle of a prompt that mostly consisted of a thread to rewrite, and asked for a
thread back.

**Rule for myself:** reference material in a prompt needs a fence in code, not just a
label. The label went in ("this is NOT part of this conversation"); what actually
fixed it was dropping any returned message whose text already exists in that
channel-day. Same shape as `keep_wording` and `trim.shorter`, for the same reason.

## A gate that reads bytes is not reading the artifact (2026-08-31)

The injection gate — every remark must come back out of the corpus — reported six of
fifty missing from a corpus that had all fifty. Mail bodies are quoted-printable, so
a remark comes back as `next to the request=\ns,`; chat is JSON-escaped, so
`{"num_jobs": n}` is on disk as `{\"num_jobs\": n}`. Both files were correct.

This is the same error as judging `settles` instead of the remark: comparing against
a *representation* of the thing rather than the thing. It failed safe — it cried
missing rather than present — and it still would have sent me editing a plant that
was right.

**Rule for myself:** a read-back check decodes to whatever a reader sees. If the
check would give a different answer than a person looking at the page, it is checking
the storage format.

## Widening a guard's scope spends the headroom it was set with (2026-08-31)

`_loop/run.sh` counted `jobs/spec-* jobs/blind-*` against a cap of 55, so the clues
and world arms were invisible to the spend guard. Correct to fix. But the narrow glob
matched 40 of 89 existing job directories and the wide one matches all 89, so the fix
alone refused the next trial: `89 trials already run, cap is 55`.

The cap was calibrated against what it was counting. Changing what a threshold counts
changes the threshold, whether or not you edit the number.

**Rule for myself:** when a check's scope widens, rebase its threshold by the amount
newly in scope, and write the arithmetic down where the number lives. Anything else
either silently spends someone's budget or silently grants them more.

## A guard that guarantees the information can guarantee the tell (2026-08-31)

`anchor()` forced each planted remark into one chat message, byte for byte, and a
substring test proved it was there. It worked: every remark carried, every
identifier typed, gate green. It also produced a corpus in which fifty people each
say one complete, self-contained, faintly over-specified sentence — and twelve of
them say it as a reply to a question about something else, because the remark was
inserted into a conversation that had already happened.

The user read the corpus and said it did not sound like people. That is not a
defect any check I had could see, because every check was asking *is the
information present* and the answer was yes.

What was wrong is that **the strongest possible guarantee of presence is also the
strongest possible tell.** A sentence that survives intact into a chat log did not
come from a chat.

The replacement inverts the guard: a turn containing the whole remark is now a
finding, the information is spread across an exchange that exists *because* the
team was working it out, and carriage is judged claim by claim by a call that is
shown the remark and the thread — never the writer's own list of where it put
things.

**Rule for myself:** when a check can only be satisfied one way, ask what that one
way looks like fifty times over. A gate with a single passing shape stamps that
shape on everything it guards.

Second, smaller: the remark must read as a decision **not yet carried out**. The
agent is the one implementing it. A corpus where somebody quotes output from the
finished feature is a corpus that contradicts the ticket.

## One producer, four consumers, four private guesses (2026-09-01)

Changing a remark from "one message" to "an exchange" broke four things, one at a
time, over about an hour:

- the **mail writer** read `sender`/`body` while the stage that writes exchanges
  speaks chat (`author`/`text`), so four threads went out from `None@world.local`
  with empty bodies;
- the **mail-reply writer** wrote the bare remark and ignored the exchange entirely;
- the **read-back gate** searched for the remark as one string, which by design now
  appears nowhere;
- the **answer key** did the same and emitted fifty rows of `?`, which reads as a
  rendering quirk rather than as "this renderer no longer understands the plant".

Four bugs, one cause: every consumer had its own idea of a turn's field names and
its own idea of what the corpus should contain, and none of them was written down
anywhere both could see. Each fix I made was correct and none of them prevented the
next one, because I was fixing sites instead of the seam.

What actually closed it: `who_said`, `what_said`, `turns` and `must_appear` in
`tg/inject.py`, and a grep proving the raw field names appear in exactly two places
— the two seam functions. Plus `located()` now REFUSES rather than rendering `?`,
because a document full of question marks is worse than no document.

**Rule for myself:** when a data shape changes, do not go and fix the readers. Count
them first. If there is more than one, the fix is a function they all call, and the
count is the test that it worked.

## A realistic corpus plus an incomplete instruction reads exactly like a corpus defect (2026-09-01)

g1's world arm scored `r1` at 0/5 on three runs out of three. The plant carried
deferral language at 3.77% of turns against an authentic-corpus baseline of 0.96%
— four times over — and concentrated on `r1`: 29% of its exchanges against 16% of
`r2`'s. The numbers lined up with the outcome perfectly, so I concluded the corpus
was defective and planned to strip the hedging out.

Then I read what the agents actually said. All three **found `r1` and declined it**:

> "All of it is tagged 'when we get to it' and none of it is in the ticket's API,
> so I built neither."
> "separate work, shapes still moving per the page-7 comments"

The corpus was right. Real teams settle a design and then do not get to it — that
is *why* there is a ticket now. What was missing was a sentence in the instruction
saying that carrying out a parked decision is part of the job. Stripping the
deferral would have bought a higher score by making the world less like a company,
which is the opposite of the point.

Two things I would have got wrong without the transcripts:

- **A correlation between a corpus property and a score is not a diagnosis.** The
  4× hedging rate was real, concentrated on the failing requirement, and not the
  cause. The cause was legible only in what the agent said about why it stopped.
- **"The world arm is hard" and "the world arm is unfair" produce the same number.**
  Difficulty from *the agent could not find it* is the measurement. Difficulty from
  *the agent was penalised for correctly reading what it was given* is a bug. The
  transcripts separate them; the score never will.

**Rule for myself:** before changing a corpus because an arm scored badly, count the
rollouts that declined a requirement on scope grounds. If that number is non-zero,
the instruction is the suspect and the corpus is a witness.

## A check with no reader is not a gate, however carefully it is computed (2026-09-01)

`finish()` was written to cure exactly this and cured half of it. Its docstring says
so: four herrings sat unretracted through a whole measured corpus because
`unreversed` was wired only to `reverse` and `out_of_order` only to `reorder`. The
fix computed all of them on every pass — and stored them on the plant, where
`stock_phrasing` and `unstated` were read by **nothing at all**, in either the
package or the CLI. `settle`, `replace` and `repair` each returned 0 over a plant
another pass had broken.

Three shapes of the same disease, all present at once:

- computed and never read (`stock_phrasing`, `unstated`);
- read only by the command that could have caused it (`unreversed`, `unknit`);
- gated, but on a stage `make` skips by default (`out_of_order`, behind
  `reorder`'s `optional=True`) — which is how g1 shipped eight chronology
  inversions that were visible the moment anything printed them.

**Rule for myself:** after writing a check, name its reader in the same commit. If
the reader is a JSON field, it has none. `grep` for the field name — if the only hit
is the line that assigns it, the check does not exist yet.

## Measure a detector against the artifact before trusting it as a gate (2026-09-01)

Writing the already-built detector, I matched on tense: `already has`, `it's
written`, `is already there`. Ten exchanges flagged. Reading them, **nine were
fine** — "the sizer already had the answer on tuesday night" (a past run), "the
directory is already there, the sizing pass mkdirs up front" (a directory that
does exist), "the same numbers we already write into metadata_0.json" (files that
do exist). Engineers talk about what exists constantly, and most of what exists
really does.

Requiring a graded identifier in the same message cut it to seven. Five were still
fine, because in every false positive the phrase has its own object and the
identifier merely sits nearby. Which noun "already" attaches to is a parse, not a
regex.

So it prints and does not fail, and the precise half (`UNSETTLED`, one finding, the
true one) is what gates. A gate wrong five times in seven is a gate people learn to
skip, and then it protects nothing.

This is the same error as the first `stock_phrasing`, which flagged "the auto sizing
branch" — topic vocabulary — as a tell. Both times the fix was to run the detector
over the real artifact and read every hit before wiring it to an exit code.

**Rule for myself:** a new detector's first run is a measurement, not a result. Read
every finding. Ship it as a gate only if the false-positive rate is near zero;
otherwise ship it as a report and gate the part that is precise.

## The bracket runs where the assumption is true

g3's suite read `/opt/world-state/input/curator/...` to prove the agent had added
exactly one field to `OnlineStatusTracker`. That is SWEWorld's pristine checkout.
It exists in the `devbox` the bracket runs in, so the bracket scored oracle 10 of
10 and every fact `hidden`. It exists in no `apex_arena` image, so hosted
validation came back 0.8889 on a bare `FileNotFoundError` — after a push and a
six-minute Cloud Batch round trip.

The bracket could not have caught it. It is not a weak check; it runs inside the
container that makes the path true. Two environments, and only one of them was
ever exercised before spending.

`prompts/write_tests.md` was the cause, not the symptom: it listed `BASELINE`
among the things a test may import, so the suite did exactly as instructed. The
prompt now offers `harness.baseline_text()` instead, which tries `BASELINE`,
falls back to the vendored tarball at `/tests/curator-src.tar.gz` (root-owned
0700, so a baseline the grader can read and the agent cannot), and returns `None`
rather than raising.

But a prompt is advice, so `horizon.emit()` gained `unhosted_paths()`: it refuses
to emit an arm whose `test_*.py` name a path outside `/workdir`, `/tests`, `/tmp`
and ordinary Linux, or import `BASELINE` at all. `harness.py` is exempt — it is
the one place allowed to know where a baseline lives, and it guards what it
knows. Written against the regression in both shapes it takes: the import (g3)
and a hardcoded literal (`t3_shared_limiter`, `t4_deepseek_empty`, which define
their own `BASELINE` and so are not reached by the harness fallback at all).

Its first run flagged `/dev/null` in `test_open.py` — the false positive the
lesson above predicts — which is why the allow-list names ordinary Linux
explicitly rather than only the three hosted roots.

**Rule for myself:** when a suite is authored in one environment and graded in
another, list what differs between them BEFORE the first push, and gate on it.
A green check is only evidence about the environment it ran in, and the cost of
learning that hosted is a round trip that reports a path problem as a score.

## A metric that is reported but not gated is where a bad suite hides (2026-09-02)

`bracket.ships()` gates on the hidden facts. `score.py` sets
`reward = hidden_mean`, and `hidden_mean` explicitly excludes `open_feature`. So
`open_feature` is computed, printed in every table, quoted in every write-up as
"the load-bearing part of that zero" — and enforced by nothing. g4's suite graded
`RunDirectoryCheck.previous_version`, which `whole.md` specifies in full, the
ticket names only inside a constructor signature, and the hidden requirements never
mention. No arm stated it. The bracket still read `Ships: yes`.

Nothing was wrong with the score. What was at risk was the only thing that makes
the score mean anything: a blind 0.00 with `open_feature` 0 cannot be told apart
from an agent that built nothing.

It is the g3 defect one level up. g3: the suite graded what the *hidden
requirement* failed to state, and the spec arm capped at 0.44. g4: the suite graded
what the *ticket* failed to state, and both the naive and spec trees failed it.
`split` compresses a specification into a ticket, and compression loses precisely
the small enumerated values — four status strings, four return codes — that a test
then asserts one at a time.

**Rules for myself:**
- When a number is reported everywhere and gated nowhere, read it by hand at every
  stage that produces it. Ask of each printed metric: what refuses if this is
  wrong? If the answer is nothing, I am the gate.
- The healthy naive tree is `failed: 8, passed: 1` — passing `open_feature` and
  nothing else. `failed: 9` is not "even better", it is a suite that no blind agent
  can reach.
- Two independently built trees failing on the *same assertion string* is one
  defect. Read the assertion before spending anything on another sample.
- Repair the artifact the defect is in, not the stage upstream of it. Amending the
  ticket cost $3.93 of rebuilds; re-running `split` would have re-rolled a measured
  8-of-8. Snapshot the cut, then assert `hidden_requirements` is byte-identical
  before and after, so the repair provably cannot soften a hidden verdict.

## `failed` in a running evaluation's status table is not a failure (2026-09-02)

g4's first hosted evaluation showed all 20 rollouts as `failed` with no score,
about ten minutes in. It read as total collapse and I cancelled on that reading.
It was not collapse. `horizon evaluations status --json` says what the table
cannot:

    error_message : "Cancelled by user"
    rollouts      : {'total': 0, 'successful': 0, 'passed': 0, 'errored': 0}

`errored: 0` with `total: 0` means **nothing had errored and nothing had
finished** — every run was still in flight, and the table renders an unfinished
run as `failed`. The runs were healthy: 64 to 237 messages each, and Horizon's own
rollout insight for run 10 read "running successfully through multiple
conversation turns (turns 83-88), with code execution completing without errors".
The cancel is what failed them, and cancelling carries no refund: $17.03 over 906
requests, gone, for a measurement that no longer exists.

The hosted validations had already passed on both arms — oracle 1, noop 0 — so
there was positive evidence the image and suite were fine, and I discarded it in
favour of a status column.

**Rules for myself:**
- Read `rollouts.errored` and `rollouts.total`, never the per-run status column,
  to decide whether a running evaluation is in trouble. The column has no state
  for "in progress" that differs from failure.
- A cancel is destructive and unrefunded. Before cancelling anything that is
  spending, spend one command establishing that it is actually broken.
- Sanity-check the clock against a task that worked: g3's rollouts finished in
  ~8 minutes, g4's ticket is 3829 characters across 11 parts, so 13 minutes with
  agents at turn 88 is a long task in progress, not a hung one.
- "Everything is failing" from a person is a report of what a screen said. Verify
  the screen before acting on it, especially when the action is irreversible.

## `test_open` sets a floor under the ticket, and that floor can eat the hidden half (2026-09-03)

g5 (`response-ledger`) bracketed at `naive: {'failed': 1, 'passed': 8}` — the
inverse of the healthy shape. Seven of eight facts came back `coincidence`.

`split` had exited 1 and said so precisely: 0 of 8 facts rested on an invented
anchor, and it named five facts whose identifiers the ticket printed. I overrode
it on the reasoning that both hidden requirements rested on *policies the code is
silent about* — duplicate folding by status precedence, and `EMPTY` completing
while `UNPARSEABLE` retries — which the leak audit cannot see. That reasoning was
right about the audit's blind spot and wrong about the outcome, and the $10 of
`naive` + `spec` builds is what it cost to find out.

The cause was upstream of the cut. `test_open` graded the whole predicate table of
`classify_record`, `LedgerIntegrityError`'s two attributes, `ledger_line`'s
normalisation rules and `read_resume_state`'s `completed_row_indices`. Since
`ships()` now requires `open_feature` to pass on `naive`, the ticket is *obliged*
to state everything `test_open` grades. That obligation set a floor, the floor
covered most of the specification, and the two hidden requirements were left
holding a residue that the ticket's own API listing entails. No re-cut could have
fixed it: whatever `split` hid, `test_open` still graded openly.

The area made this easy to walk into. g1–g4 each had a behavioural core — how big
a batch is, what a cap keeps, what a retry costs, what makes two runs the same —
where the API can be named openly and the behaviour still hidden. g5's core is
mostly definitional: the feature IS a named surface, and once the surface is
named the policies follow from it.

**Rules for myself:**
- `split`'s exit code and `leak.audit` are cheap; `naive` is $5. When the audit
  says 0 of N anchored AND names identifiers the ticket printed, treat that as the
  verdict unless I can point to a fact whose content is a *chosen value* or an
  *invented specific* — not a policy that hangs off a name the ticket must print.
  "It rests on a policy" is only a defence when the policy is separable from the
  API, and here it was not.
- Read `test_open.py` before building `naive`. It is free, and it says what the
  ticket is obliged to contain. If `test_open` grades a fact's substance, that
  fact cannot be hidden, whatever `split` did with it.
- Prefer an area with a behavioural core over a definitional one. Ask of a
  candidate brief: could the ticket name every symbol this feature needs and still
  leave the behaviour unguessable? If naming the surface settles the behaviour,
  the area will bracket badly however well the pipeline runs.

## A failing split gate has a third answer: re-cut it by hand (2026-09-03)

g6 (`model-price-lookup`) split to **0 of 8 anchored** — g5's exact number, on an
area chosen specifically to avoid g5's failure. The reflex was the one g5's lesson
installed: 0-of-N is the verdict, stop. That reflex would have been wrong here, and
so would overriding it.

Reading the cut is free, and it showed the cut was bad rather than the area. The
model had hidden P2 and P5's *policies* — "external wins, no fallback", "the
discount is only for litellm-sourced prices" — and left every invented name in the
open ticket: `REASONS = {"unknown_provider", "unknown_model", "unknown_window"}`,
`output_price_inferred`, the `None`/`""` → `"*"` window normalisation. So a blind
engineer was handed the vocabulary for free and asked to guess the policy, which is
the inverse of the arrangement that works.

Re-cutting onto the invented names — P3's three reason spellings, P5's
`batch_multiplier` — took it to **8 of 8**, and cost **$0**: `build --role oracle`
implements all of `whole.md`, so which parts are hidden is a property of the cut
alone. Two clauses came out of the ticket; nothing was rebuilt.

**Rules for myself:**
- `leak.audit` is lexical (`tg/leak.py:99` — backticked identifiers, no model call).
  It measures whether a fact quotes a name the ticket withheld, NOT whether the
  ticket entails the fact. A 0-of-N reading is a fact about the *cut*, and the cut
  is the cheapest thing in the pipeline to change.
- Before accepting or overriding a failing split, read `ticket.md` and
  `fact_sources.json` and ask which of the two failed: the area (no invented names
  exist anywhere in `whole.md` — g5) or the cut (they exist but the ticket printed
  them — g6). Only the first is a reason to stop.
- Re-cutting is free because the oracle is cut-independent. `steps.split` only
  re-cuts twice and both cuts are one prompt, so when it converges on a bad shape,
  hand-editing `task.json` + regenerating through `steps.render_hidden` and
  re-running `leak.audit` is the cheap fix — not another paid stage.
- Check the new anchors are in `fixtures/oracle.patch` before moving on. A fact
  resting on a name the oracle never implements is unscoreable, which the bracket
  reports as `broken` after the builds are paid for.
- The `test_open` read has a repair, not just a verdict. g6's graded the hidden
  vocabulary by constructing `UnpricedModelError(reason="unknown_model")` and
  requiring it to be accepted — a naive build spelling it `model_not_found` fails
  `open_feature`, and `ships()` refuses that outright. Drawing the reason from
  `UnpricedModelError.REASONS` grades the message format the ticket states and
  nothing it doesn't. Then re-run the suite on the persistent `.trees/<slug>/oracle`
  via `bracket.measure(task, roles=['oracle'])` — free, no LLM, and it proves the
  edit did not break the tree the suite is written against.

## A pass that writes once loses everything it paid for (2026-09-03)

`repair` died four calls in and `reknit` fourteen exchanges in, both to the same
ten-minute harness timeout, on the same afternoon. $1.64 of model time for
nothing — and the failure left no trace, because `plant.json` was untouched both
times and read exactly as it had before the money was spent.

The cause was mine and it was an inconsistency, not bad luck: 11 of g4's 18 stages
run longer than ten minutes, and the ones that survived were the ones I happened
to launch with a three- or four-hour timeout. Same stages, same durations; the
only variable was the number I typed.

Two fixes, because either alone is not enough:

- **Launch long paid stages with `setsid nohup … & disown`.** Own session, no
  controlling terminal, outside the harness lifecycle entirely. This does not
  depend on remembering a magic number, which the timeout approach does.
- **Checkpoint the ledger.** Every pass that edits a finished plant mutates
  `ledger` in place and writes ONCE through `finish()`, so the ledger *is* the
  state and a checkpoint is just the ledger. `clues.resume(task, stamp)` reads
  `.{stamp}.partial.json` if a previous pass was interrupted, `checkpoint()`
  writes it after each item, and `finish()` deletes it once the real artifact is
  on disk. A kill now costs one call instead of forty.

**Rules for myself:**
- Before launching anything that spends per item, ask what is on disk if it dies
  halfway. If the answer is "nothing", fix that first — it is cheaper than the
  first interruption.
- A harness timeout is a property of the harness, not of the work. Detach rather
  than tune the number.
- An interrupted pass that leaves the artifact unchanged is worse than one that
  crashes loudly: nothing downstream can tell the difference between "not run"
  and "ran and lost".

## The horizon CLI's push path has three undocumented edges (2026-09-03)

Pushing g6's two arms cost four failed or wasted commands before anything uploaded,
all of them avoidable.

- **`horizon tasks push` prompts for the task name even when `MINI_BATCH_ID` is set.**
  It reads the batch from the environment and then blocks on the name, so a
  non-interactive shell gets `Error uploading task: EOF when reading a line` and exits
  **0**. Pipe it: `printf 'g6-model-price-lookup\n\n\n' | horizon tasks push <dir>`.
  The README's recipe shows only the bare command.
- **`horizon tasks list` is broken** — `Error fetching tasks: 0` — and **nothing lists
  mini-batches**; `horizon docs` says to read the id off the web UI's My Work tab. So a
  batch name like "nidhi-test" cannot be resolved to an id from this box at all. The
  `.horizon/metadata.json` files under each pushed arm are the only on-box record.
  Grep them before guessing: `b52ead5c` is nidhi-test (apex blind/spec/clues arms),
  `fde8a4a1` is sweworld (the harbor world arms). `horizon projects list` gives project
  names and ids but a project id is NOT a mini-batch id.
- **`validate --mode hosted` is asynchronous.** It triggers a build, prints a Build ID
  and returns 0 immediately — it does not wait and it does not report a score. The
  result only arrives through `horizon tasks validate-logs -a <agent>`, which says
  `Validation status: running` until it does not. Trigger all four (oracle and noop on
  each arm) and then poll, rather than serialising them.

**Rule for myself:** the push is free but not instant, and a command that exits 0 here
has told you nothing about whether it worked. Read the artifact — `.horizon/metadata.json`
after a push, `validate-logs` after a validate — never the exit code.

## An exhausted budget looks exactly like a broken task (2026-09-03)

g6's first hosted evaluation errored 6/6 in four minutes. Two more controls errored
1/1 each. Every transcript was byte-identical — one `[user]` section, zero assistant
turns — and `horizon evaluations cost` said `$0.00 over 0 requests`.

The cause was `horizon whoami --json` -> `budget: 0.0` against `total_spend: 1040.18`.
Nothing in the evaluation API says so: `submit` accepts the job, `status` returns
`error_message: None` and `rollout_error_insights: {}`, and the only signal is
`steps: [{provision: pending}, {evaluate: failed}]`.

What made it slow to find is that everything task-shaped looked healthy, and correctly
so: hosted validation returned oracle 1.00 / noop 0.00 on both arms **because
validation runs `solution.sh` and the noop deterministically and spends no model
budget**. A task can validate perfectly and still not be runnable.

I burned two wrong hypotheses first. `--machine-type e2-custom-8-16384` was mine — the
one thing I had changed from g4's working config — and a control with the flag omitted
failed identically. Then I read a 46-byte `workdir.tar.gz` in the artifacts as proof
`/workdir` was empty, which it is not: a snapshot of an agent that never ran is empty
whatever `/workdir` held.

**Rules for myself:**
- Rollouts erroring with **zero spend and zero requests** is an account-level problem
  until proven otherwise. Run `horizon whoami --json` FIRST — before controls, before
  reading artifacts. It is one free command and it would have ended this in a minute.
- Zero assistant turns is categorically different from a low score. g4's cipher-omni
  runs produced 33-254 sections and scored 0; that was a model wall. Zero sections is
  never a model wall — the model was never called.
- Hosted validation passing says the image builds and the suite grades. It says nothing
  about whether an agent can run, because it spends no model budget.
- `horizon whoami --json` prints the account API key in plaintext. Never paste that
  output anywhere, and do not echo it into a transcript.

## The ticket is graded text, so format it at the cut, not afterwards (2026-09-03)

g6's ticket shipped as a single 3271-character sentence carrying sixty backticked
names — unreadable, and `prompts/split.md` was the cause: it said `description` is
"One paragraph".

Reformatting it by hand was safe only because of one mechanical invariant: **zero
backticked spans dropped**. `leak.audit` reads anchors from backticked spans and
`test_open` grades what the ticket STATES, so a rewrite that loses one clause makes a
fact no blind build can reach — the `ships()` failure that costs two paid builds to
discover. The reformat preserved all 60 spans, kept the leak audit at 7 of 7, and
re-bracketed identically.

**The choice, and why.** Three ways to make this automatic:
- A post-hoc LLM reformat pass. Rejected: a paid call per task AND a new way to break
  a task, because a model rewriting graded text can silently drop a clause.
- A deterministic formatter. Rejected: sectioning a run-on English sentence needs to
  understand it.
- Ask for the shape at the cut. Chosen — the ticket is authored there anyway, so
  structure costs nothing and no transformation step exists to lose anything.

Prompting alone is not enough (lesson 5: prompts are advice, gates are enforcement —
`split.md` already asked for things it did not get). So `steps.unstructured()` folds
into the **re-cut loop `split` already runs for `leak.audit`**: same retry, same
feedback channel, no new stage and no extra call unless the first cut ignores it.

**Rules for myself:**
- Before touching ticket text, snapshot it and diff the set of backticked spans. Zero
  dropped is the invariant; prose case and verb form are free to change. Case-sensitive
  word diffing just reports `add` -> `Add` and buries the real signal.
- A checker earns its place by discriminating on real data. `unstructured()` passes
  reformatted g6 and fails g1-g5, which is what says it fires on the actual defect
  rather than on noise.
- Re-run `bracket` after any ticket edit, even a cosmetic one. It is free and it is the
  only thing that proves the task did not move.

---

## A name check is not a grading defect until the bracket says so

**What I got wrong.** g6's four `r2` facts all die on one line —
`getattr(processor, "batch_multiplier", None)`, `pytest.fail` if absent — and a
world-arm run that had the discount policy exactly right scored 0 on all four for
writing `_LITELLM_BATCH_MULTIPLIER = 0.5` as a module constant. I called that a
grading defect and rerouted `scope`, `exclusions` and `observability` onto the ratio
`cost()` shows.

`cli bracket` refused it: `naive` — the blind, ticket-only build — then **passed**
`r2.scope` and `r2.observability`, so both read `coincidence` and the task stopped
shipping. `naive.patch` already writes `_BATCH_DISCOUNT = 0.5`, discounts litellm and
leaves the external tables alone. The ticket implies the whole policy. The only hidden
thing in `r2` is the *ownership* — one named method, nothing multiplying downstream —
so the name check IS the requirement, and the correct verdict on that run was 0.

**The rule.** Before removing an assertion because a run "clearly had it right", ask
what `naive` scores without it. A fact is hidden only relative to a blind build, and
the free gate answers that in about a minute. The run I was defending had produced
*the same shape as the blind build* after reading and quoting the wiki page that names
the method — which makes it a measurement, not a miss.

**The general form:** when a run fails on a name it demonstrably read, the question is
not "is the name check unfair" but "does anything survive if I drop it". Run the
bracket first and let it answer. It cost a minute here and would have cost a paid
world arm measuring nothing.

## A herring nobody registered is invisible to every gate

g6's `r1` requires three reason strings. `place()` had nowhere to put one remark, so
`clue_document.md` invented a page to carry it, and around the remark it wrote a
five-row table of error codes for a plausible neighbouring helper — two real names and
three invented on the spot. Eight of eleven scored rollouts shipped those five.

Every existing check reads the **remark**: `carried`, `giveaways`, `spread_problems`,
`not_fragmented`, `unreversed`. This was the **filler around** it, so nothing looked.
`prove` and the hosted `clues` arm cannot see it either — both build from
`render_remarks()`, the digest, which never contains a page body. I confirmed that by
diffing the clues-arm instruction before and after the fix: byte-identical.

So the corpus could contradict the answer key with nothing in the free gate set able
to notice. `inject.rival_vocabulary()` is now the check that reads what was written
rather than what was planted, and it blocks. Its three narrowing conditions are the
lesson: backticked spans only (a rival is something somebody quoted, which is also
what separates it from the neighbouring helper's own parameters); two or more graded
names in one artifact (spread pushes them apart, so two together means that artifact
is enumerating the vocabulary); and same shape as the names it sits beside (a rival to
three snake_case strings is another snake_case string, not a CamelCase exception).

**Rules for myself:**
- A wrong decision in the corpus is fine — that is a herring. An *unregistered* one is
  a bug, because `reverse` only retracts what `plan()` knows is a herring.
- When a plant stage invents prose to host a remark, the prose is corpus too. Check
  what it minted, not just whether the remark landed.
- A checker earns its place by discriminating on real data: this one fires on the
  pre-fix page naming exactly the three strings, and is clean on all four plants on
  disk.

## Agent type follows the task FORMAT, not the model (2026-09-05)

Submitting the g2 world-hosted arm with `--agent-type meteor` failed the evaluation
in three minutes: `status: failed`, `rollouts.total: 0`, no spend, and
`steps: [{provision: pending}, {evaluate: failed}]`.

`meteor` comes from the g1/g4 notes, and it is correct — for the **apex-format**
blind/spec/clues arms those notes were about. The `-world*` arms in `harbor_tasks/`
are `"format": "harbor"` (it says so in `.horizon/metadata.json`), and harbor
accepts a different roster: claude-code, terminus-2, codex, gemini-cli, openhands,
mini-swe-agent, goose, aider. Their rollouts have always run on **`typhoon`**.

What made it slow to see is that the failure is byte-identical to the exhausted-budget
signature in the lesson above — zero rollouts, zero requests, provision pending — so
the documented first move (`horizon whoami --json`) returns a healthy $400 and
tells you nothing.

**Rules for myself:**
- Read `agent_type` out of the previous version's rollout JSON before submitting.
  `.rollouts/v<N>/*.json` carries it, and it is one `python3 -c` away.
- `rollout_error_insights` is generated text, but it named this exactly ("the harbor
  format only supports specific agents") while `error_message` said only "exit code
  1". Read the insight first; verify it against the rollouts, don't dismiss it.
- Zero-rollout failures have at least two causes now. Check the task format and the
  budget together, not budget alone.

## The model gate counts rollouts per TASK ID, not per task (2026-09-07)

`evaluations submit --model lumen` on g9's `example-encoding-world-hosted` returned

    403 Forbidden: This task is gated to cipher-omni (GLM 5.2) or cheaper:
    run 10+ cipher-omni rollouts below a 0.4 pass rate to unlock pricier models.

The same submit on g8's `attachment-payload-world-hosted`, sent in the same command
seconds earlier, was accepted — and a two-task submit is refused wholesale if either
half is gated, so the first attempt looked like both were blocked.

The difference is not the task, the arm or the version. `tasks.rollouts(<id>)`
returns a `stats` list keyed by model:

    g8 attachment-payload-world-hosted   cipher-omni, 10 rollouts, pass_rate 0.0
    g9 example-encoding-world-hosted     no rollouts at all
    g9 example-encoding-world-LOCATED-hosted   cipher-omni, 10 + 8 more

g9 *had* run 12 hosted rollouts — on its located twin, which is a different task id.
Nothing about a sibling arm, an earlier version, or the same requirement under
another name counts toward the gate. A brand-new arm starts at zero every time,
so the ~$16-36 gating run is a per-arm cost, not a per-task one.

**Rules for myself:**
- Before pricing a hosted run, read the gate itself:
  `GET /api/v1/evaluations/config?task_id=<id>` returns `gate.unlocked` along with
  `graded_count`, `pass_rate`, `threshold` and `min_rollouts`. That is the server's
  own verdict, free, and it beats inferring one from `tasks.rollouts(<id>).stats` --
  stats count `total_rollouts` per (model, agent_type), and only GRADED ones on the
  right agent count, so g1 (12 cipher-omni on cascade) and g3 (21 on typhoon, 11
  errored) both read ambiguous there and unambiguous here. Note the SDK parses this
  field as `gate`, not `model_gate`; `EvalConfig.model_gate` is always None.
- Submit gated and ungated tasks separately. One comma-separated submit with a
  gated member spends nothing and grades nothing, and the 403 names no task id.
- Budget the gate as part of standing up an arm. Two new arms is two gating runs.

## A remark that names an invariant without naming the mechanism is read as "raise" (2026-09-08)

g11's located arm lost `r1.rule` in 3 of 4 completed opus-5 rollouts and lost nothing
else. All three implemented `canonical_reasons` to raise `StepLedgerError` on a
repeated label, where the suite asserts it collapses one. All three had quoted the
same corpus line into their own notes:

    2025-03-24 14:16 konrad: that goes too, a label shows up once in a record or the
    record is not accepted

The answer key says the function deduplicates. The corpus said refuse. That half was
already repaired -- the line now reads "not by refusing the write though - the record
just carries the label once, a second mention folds into the first" -- but the repair
landed at 20:03 on 2026-09-07, two hours AFTER the rollouts, and reading the failure
without checking that timestamp would have re-fixed a fixed bug. **Compare the
rollout's `created_at` against the mtime of what it is failing on before diagnosing.**

The residual defect is the one worth remembering. Even repaired, the folding was
attached to *the record*, while the graded call is `canonical_reasons`, and the one
thread that enumerates what that function does and does not raise on (2025-04-09
`#code-review`) never mentioned duplicates -- next to `anything not in
CHECKPOINT_REASONS raises`, "the record carries it once" reads as one more thing the
writer enforces by refusing. An invariant stated as a property ("no repeats within a
record") does not tell a reader which function upholds it, and in a module that
already raises, the default guess is that it raises. **State the mechanism in the room
where the function is described, not only the invariant in the room where the symptom
was found.**

## Rewriting corpus text silently breaks the plant, and a cache hides it (2026-09-08)

Rewriting g1's four planted mail threads to read like mail cost nothing at the time
and broke `build_located_arm.py` for two commits without a single error appearing.

`inject.located()` finds a remark by substring-searching the corpus for **the
plant's own words** (`must_appear(c)[0]`), and it raises rather than degrading. Edit
a body for how it READS and the plant becomes a record of something nobody says any
more:

    clues.hedged-v1  FAIL: cannot locate 4 of 50 remark(s) in data:
                     g1.r1.l10, g1.r1.l12, g1.r1.l14, g1.r2.l6

Exactly the four mail carriers. It went unnoticed because `locate()` falls back
through every `clues.*` snapshot and, failing those, the arm still built off
`harbor_tasks/.located-corpora/sweworld_0.4.4/` — a cache still holding the old
bodies. **The artifact looked healthy while the tool that makes it did not work.**
`cli.py resync` is the repair, and it calls `located()` itself afterwards so a
resync that fixed nothing says so now rather than three commands later.

- **Any corpus edit needs the plant resynced in the same change.** Corpus and plant
  are coupled by substring search, not by id.
- **Clear the cache before you believe a rebuild.** A generator that passes on a
  stale cache proves nothing about the corpus you just changed.

Two more things the same change turned up:

**Build the located map from the IMAGE, never from `data/`.** `data/` has four chat
and wiki exchanges a message shorter than `sweworld:0.4.x` does, so a map rebuilt
from it turns four `an exchange of 7 messages` into `6` and sends a reader looking
for a turn that is there. The mail rows are identical either way, which is what makes
this easy to miss.

**A body rewrite is safe everywhere else, and that is worth knowing so you do not
regenerate half the repo.** The `-clues` and `-spec` instructions render
`clue["text"]` and the requirement fields, never message bodies. No grader reads mail
at all — the suites only read `/opt/world-state/input/curator`. Message counts,
subjects and timestamps are untouched, so the located map's own numbers do not move.

## `horizon artifacts environment push` builds from the repo root (2026-09-08)

Publishing a world image failed with

    failed to compute cache key: "/task-entrypoint.sh": not found

which reads as a missing file and is a wrong build context. The CLI builds from
`git archive HEAD` — a clean checkout of the repo ROOT — with `--dockerfile` overlaid
on top, so a task's own `environment/Dockerfile` cannot resolve its `COPY setup.sh`.

Nothing task-specific belongs in the published image anyway: it is the company, and
every hosted arm does `FROM <it, by digest>` and adds its own setup, entrypoint and
`plant/`. `harbor_tasks/_env/world-registry.Dockerfile` is what gets published and it
copies nothing from the context. The push prints `image_reference`; that digest goes
into the pinning arm's `FROM` by hand.

Also: it stages an uncompressed OCI tar **and** its gzip under `/tmp`, on the same
filesystem. A ~7GB world took the box from 9.7GB free to 4.7GB before recovering.
Check free space before starting, not after it fails.

## An absent fact is not a missing fact (2026-09-08)

Every answer key says "Each is graded as five independent facts, 0.1 each". For g2
that is simply false: `g2.r2` declares no `failure_behavior`, its grader has four
tests rather than five, and the task is scored on **nine** facts at one ninth each —
which is why 8/9 shows up as 0.889 in the results and not as some rounding artifact.
`score.py` says so at the top: keys come from `tasks.json`, because "inventing keys
for absent facts would quietly divide every mean by the wrong number."

Five of the ten requirements across g2/g3/g4/g6 have no `failure_behavior`, and
g6.r1 has only three of the five. **Read the suite's test count, not the key's
boilerplate, before reasoning about what a score means.**

## A backtick guard that cannot see a fence parks healthy tasks

`fleet/worker.py:reformat_ticket` protects a real invariant — a reformat must not
drop a backticked span, because any of them may be a graded identifier. It checked
it with `re.findall(r"`[^`]+`", text)`, which pairs backticks left to right and has
no idea what a fenced code block is. A ticket containing ```` ```python ```` throws
the pairing off by three, so every "span" after the fence is the PROSE BETWEEN two
identifiers rather than an identifier.

g13 parked on exactly this: six "dropped spans" reading `` ` does not read it. ` ``
and `` `). Use ` ``. None was a name. The cut underneath was healthy — the judge had
already said "No leak and no defect" — and the run stopped anyway.

Measured before trusting the fix, which is this repo's rule for any detector: on the
nine tickets with no fence, old and new span extraction are byte-identical (209/209,
196/196, 74/74, …), so the change is a strict no-op on everything that shipped. On
the three fenced tickets the junk collapses — 39→2, 33→6, 23→7.

The fix strips fenced blocks before extracting inline spans, and then checks the
fenced blocks in their own right, because their content is graded text too and
excluding them from the first check must not make dropping one invisible.

**The general form:** a guard that reports a violation nobody can act on is worse
than no guard, because it stops good work. When a guard fires, read the thing it
claims was lost. If it is prose, the guard is broken, not the artifact.

## A tight bullet list is not a wall of text

`steps.unstructured()` flags a ticket whose longest paragraph runs past 600
characters, splitting on `\n\s*\n`. A markdown bullet list with no blank lines
between items is ONE paragraph to that regex. g13's flagged "940-character
paragraph" was four bullet lines; g12's "1463" was the same shape. Both tickets
carried 33 and 28 heading/bullet lines respectively — they were already the
structured markdown the message asks for.

It is advisory feedback, not a gate, and g12's judge read it correctly and carried
on. g13's judge acted on it, and the reformat it ordered is what tripped the broken
guard above. Two false positives stacked into a park.

Before acting on `unstructured()`, print the block it is complaining about. If it is
bullets, there is nothing to fix.

## A ticket that promises what the image does not deliver (2026-09-09)

Triaging two 0.07 rollouts in a g6 evaluation of ten turned up three defects, and
all three are the same defect: `instruction.md` states something the environment
does not provide, and nothing checks the two against each other.

- *"Nothing is checked out for you. Clone it."* — and `useradd -m ubuntu` leaves a
  bare home, so the agent's first `git commit` is `Author identity unknown`.
- *"installed in the virtualenv at `$CURATOR_VENV`"* — and both world arms reach
  that virtualenv through `COPY --from=...`, which copies **files, not the source
  image's ENV**. The variable is empty and `$CURATOR_VENV/bin/python` expands to
  `/bin/python`.
- *"`$CURATOR_VENV/bin/pytest` will run the library and its tests"* — and curator's
  `tests/conftest.py` imports `vcr` at module scope, which the venv does not have,
  so the whole tree dies at collection.

Each is survivable and nine of ten runs did survive them. What makes them worth
fixing is **where** the cost lands: the git one is spent at the END, because
committing is the last thing an agent does. Run 1 wrote the entire change, 18
passing tests included, and hit the identity error at message 389 of a 401-message
cap. `run_suites.py` grades a clean clone of pushed `main`, so a commit that never
happens scores zero on the requirements too, not just on provenance. **Friction near
a turn limit is not a small tax on the score, it is a coin flip on the whole run.**

The `COPY --from` one is the one to remember mechanically: it is invisible in the
Dockerfile, invisible in the ticket, and the arms it breaks are exactly the arms it
does not appear in.

**Check the plant before blaming it, and check the controls before blaming the
suite.** `r2.exclusions_or_crossover` failed 6 of 8 pushed runs, which looks exactly
like an over-specified test — and it is 1.00 in `spec`, in both `clues` runs and in
`located`. The fact is recoverable and the test is fair; the spread is the search,
which is what a world arm exists to measure. The controls are already paid for and
they answer this in one command.

Corollary that cost nothing here and could have cost a lot: regenerating `setup.sh`
from the template pulled in four leak fixes the pushed g6 arm predated — the
Mattermost import zip, the maddy store, `/opt/task-plant`, the plant log. Before
believing the earlier numbers, grep the transcripts for those paths. None of the ten
runs touched them, so the evaluation stands. **An arm pushed before a fix keeps
running without it, silently; the emitted directory is the artifact, not the
template.**

## Dropping root did not stop the forgery it was reported for (2026-09-09)

The report was exact: `run_suites.py` put the submission first on `PYTHONPATH`
and spawned pytest as root, so a pushed `src/sitecustomize.py` ran as uid 0,
rewrote `/tests/score.py`, and returned `reward.json` all 1.0 from a pristine
tree. Reproduced before touching anything, which is the only reason the rest of
this is measurable.

The fix — drop to `nobody`, open `/tests` to the drop group read-only, take the
submission off `PYTHONPATH` — killed that payload outright and left the oracle at
1.00. Then the same pristine tree scored **1.0 again**, by a different route:

    # bespokelabs/curator/__init__.py, which the grader MUST import
    args = Path("/proc/self/cmdline").read_bytes().decode().split("\0")
    out  = [a.split("=",1)[1] for a in args if a.startswith("--junit-xml=")]
    ...rewrite it from an atexit hook with the real node ids read out of /tests

Nine forged `<testcase>` elements, `reward: 1.0`. **A uid cannot fix this**, and
the first version of my own summary said the drop "closes the reported forgery",
which was wrong and would have been believed. The process that imports agent code
is the process that writes the report; no permission bit separates them.

Three things worth keeping:

- **Verify the fix against the original exploit, then against a variant.** The
  first payload dying proves the patch does what it says, not that the hole is
  shut. The second payload is the one that tells you what you actually bought.
- **A naive probe failing is not evidence.** My first forgery scored 0.0 — but
  only because its fake `name=` did not match `score.py`'s `FUNC` regex, and an
  earlier one had a shell-escaping SyntaxError so it never ran at all. Both
  looked exactly like "the harness defended itself". Read the payload's own
  marker file before believing a zero.
- **State the boundary as what an attacker gains, not as what you changed.**
  "Runs unprivileged" is not a security property. What the drop actually bought:
  no root execution, no reading the planted corpus at `/opt/world-state`, no
  persistence past the run, and `provenance.py` still unforgeable because it is a
  separate root process reading Gitea and an `svc`-owned symlink. What it did not
  buy: the score.

## The score forgery closes with a worker/judge split, and the bracket proves it did no harm (2026-09-10)

The gap the drop left — a `junit.xml` forged by the process that imports the
submission — closes only by separating the two: `probe.py` (worker, nobody,
imports curator, writes VALUES to observations.json) and `judge.py` (root, stdlib
only, never imports curator, applies the assertions and writes junit STRAIGHT to
root-owned /logs). A forged atexit/junit then has nothing to rewrite in the
reporting process. g11 done; opt-in in `run_suites.py` on the suite shipping both
files, so every other task is byte-identical.

Two things made this safe rather than a rewrite of the grader's meaning:

- **The judge emits the same `classname`/`name` as the old tests**, so `score.fold`
  maps to the identical fact keys and `score.py`/`test.sh` need no change. The
  "task" is the set of verdicts, and the invariant to protect is those verdicts —
  not the test bodies. Proven by re-running the bracket through the new path:
  pristine 0/10, naive open=1 rest 0, oracle 10/10, every hidden fact still
  `hidden`. Byte-for-byte the pytest baseline.

- **The proof needs BOTH directions.** Invariance alone (bracket unchanged) does
  not show the hole is shut; a forge fixture (pristine tree + sitecustomize +
  atexit junit-rewrite, implementing nothing) is what does — 1.0 under the old
  pytest grader, 0.0 under the split, same tree. Run it before believing the fix,
  exactly as the drop lesson above says.

**Rule for myself:** to close an in-process forgery, move the verdict to a process
that never imports the code — a uid cannot do it. To prove a grading change is
verdict-preserving, replay the whole bracket through it and diff per fact; to prove
it closed the hole, keep the exploit fixture and watch it drop to zero. Floats
cross the observations JSON exactly (json uses repr), so `approx(rel=1e-12)` still
means what it meant in-process.

Kept `test_*.py` (unused by the split) for the fact↔test bijection and as the
assertions' source of truth; probe/judge travel together in `_suites/`, so a
rebuild can't ship one without the other and silently reopen the pytest fallback.

## Rollout analysis is reading transcripts against the answer key (2026-09-11)

Asked to analyze g1-g11 lumen rollouts, I planned per-fact subscore tables plus a
shingle matcher computing "seen" rates. Rejected: "look at the transcripts and cross
check what clues it was able to find with the answer key ... and see what its
reasoning was".

**Rules for myself:**
- The unit is (transcript x answer-key remark): found? how? what did the agent's
  `analysis`/`plan` say about it? did the code follow it? Same for every herring and
  its reversal.
- A subscore says a fact failed; a string match says text scrolled past. Neither says
  whether the agent registered, dismissed or overrode the remark. Mechanical passes
  aim the reading; they never stand in for it.

## A herring that works is not a defect (2026-09-11)

I registered g9's mail herring as "task defect G9-H" because its only reversal sits in
wiki comments that search does not index, and 6/10 runs believed it. Nidhi: "Remove g9
... they are fine", then "for g9 though remove it".

**Rules for myself:**
- Hidden and hard to reach is the task's design. A defect is the world arguing AGAINST
  the answer key (scaffolding that contradicts `settles`), a clause that never rendered,
  or a grader that measures something other than the requirement.
- A herring whose reversal exists and is reachable by reading the corpus is working.
  Report its capture rate as a measurement, not as something to fix.

## Fixed defects leave the analysis (2026-09-11)

Three times Nidhi removed a defect I kept listing after it stopped being one: G9-H (by
design), G7-A ("g7 was fixed and re evaled so it shouldnt be counted in the artifact"),
then G7-D once its grader fix was in ("remove g7d from the artifact and .md file").

**Rules for myself:**
- The report's defect lists, fix lists and register are for OPEN problems. When one is
  fixed, remove its entries rather than badging them "fixed".
- Remove the label, never the measurement: the runs still lost what they lost in that
  eval, so rewards and loss counts stay as measured and are described plainly.

## A split grader still fails if the worker can KNOW the answers (2026-09-14)

argus on g1: pristine `main` plus an import-time `atexit` hook that overwrites
`observations.json` scored **reward 1.0 on all eleven facts**. I reproduced it
against the unchanged grader before touching anything, and it was worse than the
report said — about **thirty of g1's ninety assertions were booleans the worker
computed** (`swept_proof`, `unchanged`, `keepers_intact`, eight `doc_*_eq`), and a
**1.2 KB file of `true`** passes `r1.scope` and `r2.exclusions` knowing no answer
at all. `keepers_intact: {}` passed because the judge iterated the worker's own
dict.

Three rounds of jailing had all been aimed at what the worker can READ. None of
them touched what it can WRITE, and reading was never the point: the expected
values are the planted requirement, published in the corpus the world arm tells
the agent to read, and `probe_support.py` (necessarily in the jail) named the
exact inputs. The forger did not need `/tests` at all.

What actually closed it, and the order matters — each covers what the others miss:

- **Re-draw the inputs every run.** Root picks a seed, `run_split` hands it to
  worker and judge, `fixture_spec.derive` turns it into prompts, counts and
  limits. Nothing about the run is knowable in advance.
- **Entropy has to reach the GRADED value, not just the input.** My first draft
  re-drew the prompt token at a fixed width, so every row serialised to the same
  number of bytes and a plan captured from one run fitted the next: the replay
  forgery passed 3 of 10 facts. Varying the token's WIDTH moved the byte counts
  and the digests with it. **Randomising an input that does not change the answer
  is decoration.**
- **The judge reads the directories.** "The sweep ran", "the failed run left the
  place alone" are now root opening the working directory and diffing it against
  the inputs it planted — not a word the worker chose.
- **Seed-independent facts stay forgeable even so.** `r1.scope` was graded on an
  empty plan's document, which is identical every run; the replay forgery passed
  that one fact and no other. Grading it on the run's own sidecar closed it.
  **Check every fact for whether ANY of its assertions move with the seed.**
- **Constants that cannot be re-drawn get read out of the source.** The 512 cap,
  `PLAN_FILE_NAME`, the format version: AST over `SUBMISSION_SRC`, so reporting
  the right number without defining it fails.

`os._exit` bound before the submission import kills the exact `atexit` vector —
and it is a trap to stop there. It made the first two forge fixtures score 0.0
with their payloads never running, which reads exactly like a fix. The fixture
that proves anything intercepts the write itself (`json.dump` patched at import)
and **writes a marker file you check**; lessons.md 2026-09-09 says read the
marker before believing a zero, and it was right again.

**Rule for myself:** to close a forged-value channel, ask what the forger would
have to KNOW, not what it can reach. If the answer is knowable — from a previous
run, from the corpus, or because the fact is the same every time — no permission
bit, uid or jail closes it; only moving the answer out of reach of prediction
does. And prove it with a payload that survives the mitigation you are proudest
of.

## 2026-09-14 — "use the correct scores" asked for a check, not new content

Asked to update the rollout-audit artifact "with the correct scores", I verified
every reward against the pulled subscores (all matched) and then added a whole
scoring section plus Horizon-score markers nobody asked for. The user only cared
that `reward` was right. Rule: when a request is to make numbers correct, verify
them first and report the verdict; if they are already right, change nothing and
say so. Adding explanatory material is a separate request the user makes.

## A probe reaching for an attribute is a dependency between facts (2026-09-14)

argus, second pass on g1. `probe.py` opened three of its eleven nodes with
`module.PLAN_FILE_NAME` — r1.rule's constant. A submission that hardcodes
`"batch_plan.json"` and exports no constant makes that raise; `probe.main` catches
per node, the judge says "probe error", `score.py` folds the fact to 0. r1.scope,
r2.failure_behavior and r2.observability all died on a naming detail that only
r1.rule owns, and because the access was each node's FIRST statement, nothing
those facts could have reported survived. Measured on a fixture of argus's own
rollout: **hidden_mean 0.6, where the same tree deserves 0.9**.

`test_r2.py:14-16` had promised the opposite in as many words — "an implementation
that sweeps without writing a sidecar passes r2 in full" — and the human reference
honours it with a literal. The probe invented the coupling. Half of it was mine:
v15 planted the stale bystander under a module-level literal, I deleted that
literal to keep answers out of the worker's jail (correct) and reached for the
module's constant instead (not correct). **Removing an answer from the jail is not
a licence to depend on the submission for it.**

What the fix looks like, and it is not `getattr(module, "X", <the answer>)`:

- **`getattr(..., None)`, then grade what you can.** The r2 probes plant the stale
  sidecar only when there is a name to plant under; the judge adds it to the
  expected directory only when it was planted. r2 keeps every bit of evidence it
  is entitled to and none it is not. A literal default would have put r1.rule's
  answer back in the jail — the thing v16 spent a day removing.
- **Let the judge own the spelling.** r1.scope used to ask the worker "is
  <name> in this directory yet?". It now records the directory and the judge
  asserts the name — no dependency, and strictly stronger, because the worker no
  longer chooses what to look for.
- **A missing field should fail the fact, not kill the node.**
  `read_field(..., default=None)` turns a probe error into the judge's own
  message: "BatchLimits.max_batches_per_plan default: None != 512".

**Rule for myself:** grep every probe for attribute access on the submission and
ask which fact owns each one. If the answer is "a different fact", the node has a
silent dependency whose failure mode is the worst available — a zero that reads
as "not implemented" about behaviour nobody looked at. Two fixtures make it
visible and belong in the bracket for good: one that implements everything but
the naming detail, and one that implements the other requirement and nothing of
this one.

### Postscript: the verification driver deleted its own container (2026-09-14)

Mid-verification, `docker exec` started answering `exec: "bash": executable file
not found`. The twin was healthy; its root filesystem was empty. Cause, in the
scratchpad `driver.sh` inherited from the 2026-09-10 session:

```bash
git clone -q "$URL" /tmp/push      # failed, silently — the script had `set -uo pipefail`, not -e
cd /tmp/push                       # failed too; cwd stayed /
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +   # deleted /
```

Nothing outside the container was touched (it runs through `docker exec`, and the
host repo was clean), and the measurements taken before it died stand — but the
twin had to be rebuilt and a fixture re-run. Now: `set -euo pipefail`, the clone
is asserted (`test -d "$WORK/.git"`), and every path in the script is absolute —
`find "$WORK" …`, `git -C "$WORK" …`. There is also a `setup_twin.sh` that
rebuilds the whole thing from scratch, because a verification harness that cannot
be recreated in one command is a harness you will be tempted not to re-run.

**Rule for myself:** a recursive delete never runs on a relative path. Either the
path is absolute, or the `cd` that established it was checked — and a helper
script that deletes anything gets `set -e` before it gets anything else.
