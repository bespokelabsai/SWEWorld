The suite for `{{task_id}}` grades something the ticket does not state. Fix the
ticket. Change nothing else.

## What the gate found

{{findings}}

## Why this and not another `split`

`test_open` sets a floor under the ticket: it grades the *open* feature, the
half stated openly, and every arm is supposed to be able to build it. When it
fails on the `naive` build — an agent given only `ticket.md` — the suite is
grading a detail the ticket never states. The damage is not the score. It is
that a blind arm scoring 0.00 can then no longer be told apart from an agent
that built nothing at all, which is the entire reason that number is reported.

Re-running `split` would fix it by re-rolling *which* facts are hidden, throwing
away bracket verdicts already measured and paid for. So: amend the ticket.

## What to do

Work in `{{task_dir}}`.

1. Read `tests/test_open.py` and find every name, value and behaviour it reaches
   for. Read `ticket.md` and `task.json`'s `description`.
2. For each thing the test grades that the ticket does not state, add it to the
   ticket. Add the minimum: the name, the value, the enumerated cases — enough
   that a competent engineer with only the ticket would build it.
3. Make the identical edit in **both** places. `ticket.md` is what the local
   builds read; `task.json`'s `description` is the field `emit` ships to the
   hosted arms. A ticket fixed in one and not the other is two different tasks.
4. Keep the existing structure: one line stating the goal, then a `### ` section
   per thing to add or change, specifics as bullets.

## The one thing you must not do

**Do not touch `hidden_requirements` in `task.json`.** Not a word, not a
whitespace change. It is compared byte-for-byte before and after this step and a
difference reverts the whole edit, because softening a hidden requirement is
exactly how this repair would turn a hidden fact into a passing one and look
like a fix.

Likewise do not edit `tests/`, `whole.md`, or anything under `fixtures/`. If you
believe the test is wrong rather than the ticket, change nothing and say so.

When you are done, reply with a short summary of what you added to the ticket.
