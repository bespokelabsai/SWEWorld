Colleagues worked on this area for months, and an engineer is going to rebuild it
from what they said to each other. Some of what the team decided never actually got
said out loud — it sits in the record as a symptom somebody hit, or a name somebody
dropped, and a reader is left to supply the decision themselves.

You are fixing that, without turning the record into a specification.

## What the team settled — {{key}}

{{fact}}

## What nobody said

Each of these is something the code has to get right that the remarks below do not
put in a reader's head. `implied` means somebody gestured at it and stopped;
`absent` means nobody touched it.

{{missing}}

## What the remarks say now

{{remarks}}

## The steps these remarks build

{{steps}}

## What to write

Rewrites of the remarks above, and new remarks where no rewrite can carry a missing
piece.

**Somebody has to state the decision.** Not hint at it, not report the symptom that
motivated it — say it, the way a person says a thing that has already been settled:
*"we write X before Y"*, *"the cap is N and it lives on the limits dataclass"*,
*"that one stays as it is"*. Every missing piece above is somewhere the guessing
already happened, and the engineer guessed something else.

**Keep one person still complaining, per step.** Each step above lists its remarks
as `problem` or `decision`. Do not convert a step's last `problem` into a decision.
Someone hits a thing and someone else settles it is what makes this read as a
company rather than a specification cut into pieces — and the complaint is what
makes anybody care that a decision was needed.

A **new** remark that settles something is dated where it is placed, and a decision
that lands before the complaint it answers is thrown back and re-placed. So a new
decision belongs to a step that already has somebody complaining; if the step has
none, write the complaint rather than the answer.

**One missing piece per remark.** A message carrying three decisions is a message
written for a grader. Spread them: different people, different steps, and prefer
whoever already owns that ground in the remarks above.

**Everything that made these remarks work has to survive:**

- One or two sentences, under thirty words, in that person's own voice. Copy the
  voice off how they already write above — the typos, the lowercase, the way they
  open. A rewrite in clean prose is more visible than the vagueness it replaced.
- A rewrite stays where it is. Each remark above already sits in a real conversation
  and answers something; the new wording has to still work as that reply.
- Identifiers appear literally, character for character, and go in `verbatim`. A
  rewrite that drops one is thrown away and the vague original is kept instead.
- **Never restate the whole requirement in one remark.** Stating ONE settled
  decision is what a remark is for; stating all of them is the arm we are measuring
  against.
- **Never contradict something another remark already settles.** A remark dated
  later overwrites an earlier one in a reader's head — that is how a plant that had
  a fact right lost it again.

A new remark needs a `holder` from the roster below, a `source` they can appear in,
and the `subconclusion` id of the step it belongs to:

{{roster}}
