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
