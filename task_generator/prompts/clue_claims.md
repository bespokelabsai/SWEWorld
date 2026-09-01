An engineer is going to read this company's chat, wiki and mail — and nothing else —
and from that alone write the code these tests grade. You are deciding, assertion by
assertion, whether the corpus actually told them, or whether they would have had to
guess and happen to guess right.

## The requirement being graded — {{key}}

{{fact}}

The engineer never sees this text. It is here so you know what the assertions below
are assertions *about*.

## What the tests check

Each of these is one assertion from the graded test, with the comment the suite
wrote above it. It is the literal thing an implementation has to get right, and it
is worth a fraction of this task's score.

{{claims}}

## Everything the corpus says about this requirement

Every planted remark in {{req_id}}, in date order, the way a reader meets them.
There is nothing else — no specification, no design doc, no comments in the code.
Some of these were later overturned by other remarks and the reader is not told
which.

{{remarks}}

## The judgement

For each claim, exactly one verdict:

- **`stated`** — somebody says it. A reader who has read these and is now writing the
  code puts this in *because they were told to*. The wording may be nothing like the
  assertion; a name may be spelled in passing, a number dropped into a complaint. What
  matters is that the decision was made out loud by somebody.
- **`implied`** — the reader could get there, but nobody said it. Somebody reports a
  symptom and leaves what to do about it open. Somebody names a thing without saying
  what it does. Two remarks together point at it and neither commits. **A reader who
  works it out is not the same as a reader who was told**, and this is the verdict for
  anything a competent engineer might reasonably read and then not do.
- **`absent`** — nothing in the corpus bears on it at all.
- **`not_required`** — the assertion is checking the suite's own fixture, or a detail
  the feature request already fixes. The corpus owes it nothing.

### An assertion is about one expression, not about a value in the air

Read what the assertion actually evaluates. `assert module.plan_fingerprint([]) ==
"e3b0c44298fc"` is a claim about **what that function returns**. A remark saying
"plan_id comes out e3b0c44298fc" states a claim about `plan_id`; it does not state
this one, because a reader can satisfy it by computing the digest at the call site
and leaving `plan_fingerprint` returning the string it hashed. Three rollouts in five
did exactly that, and the judge had marked the assertion `stated` on the strength of
that value appearing somewhere in the corpus.

So, for every assertion: name the expression on each side, and ask whether a remark
says what **that** expression is. A value that appears in the corpus attached to a
different name is `implied` at best. The same goes for a function whose arguments
nobody describes, an attribute nobody says is an attribute, and a constant nobody
attaches to the name that must hold it.

Be hard about the line between `stated` and `implied`. This exact corpus scores 1.00
when the requirement is handed over outright and 0.70 when it is planted as these
remarks, so the gap is made of assertions that a generous reading calls carried. If
you find yourself explaining how a reader would infer it, that is `implied`.

Judge what the remarks say, not what the requirement says. You have read the
requirement and the engineer has not; the question is only ever whether *these
sentences* would put it in their head.

`clues` names the remark ids the verdict rests on — which ones say it for `stated`,
which ones come closest for `implied`.
