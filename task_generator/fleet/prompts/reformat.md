The ticket for `{{task_id}}` is unreadable as laid out. Re-lay it out. Change no
wording and drop nothing.

## What the gate found

{{findings}}

## Why this matters

The ticket is **graded text**. It is what the blind arm is handed, and `emit`
ships it verbatim as `task.json`'s `description`. A single 3,000-character
paragraph is what `split` produces when it compresses a whole specification into
prose, and an agent that misreads it builds the wrong open feature — which shows
up later as a blind arm scoring zero for a reason that has nothing to do with
hidden requirements.

The repo's rule is to fix this at the cut rather than afterwards, because every
later stage measures against the ticket that ships.

## What to do

Work in `{{task_dir}}`. Edit `ticket.md` and the `description` field of
`task.json` so they stay byte-identical to each other.

Re-lay-out into:
- one line stating the goal,
- then a `### ` section per thing to add or change,
- with the specifics as bullets.

Break the long paragraphs at their existing sentence boundaries. Put each
enumerated case, each named field and each signature on its own bullet.

## The invariants

1. **Drop nothing inside backticks.** Every `` `like_this` `` span in the ticket
   now must still be there afterwards, spelled identically. The grader may
   require any of them, and a reformat that loses one loses a graded name while
   looking like a whitespace change. This is checked automatically and a
   difference reverts the whole edit.
2. **Change no wording.** You are re-laying-out sentences, not rewriting them.
   Do not clarify, do not summarise, do not add. If a sentence is ambiguous,
   leave it ambiguous.
3. **Touch nothing else.** Not `hidden.md`, not `hidden_requirements`, not
   `whole.md`, not `tests/`, not `fixtures/`.

Reply with a one-line summary of the new structure.
