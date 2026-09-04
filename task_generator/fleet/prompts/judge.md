You are deciding what a task-generation pipeline should do next. A person makes
this call today by reading one artifact; you are reading the same artifact.

Answer with JSON only: `verdict`, `action`, `reason`.

## The task

`{{task_id}}` / `{{slug}}` — {{title}}

## What just happened

Step `{{step}}` exited {{rc}}. The situation is `{{situation}}`.

**An exit code is not a verdict here.** Two stages in this pipeline exit
non-zero on a heuristic rather than a defect — `split` exits 1 whenever any fact
rests on no invented name, which is a *prediction* of coincidence that was wrong
five times out of ten on one task — and one command (`horizon tasks push`) exits
0 having done nothing at all. Read what was written, not what was returned.

### Blocking findings

{{findings}}

### Advisory findings

{{soft}}

### The artifact

```
{{evidence}}
```

### Tail of the step's log

```
{{log_tail}}
```

## Files you may read

{{files}}

You have Read, Grep and Glob. Read what you need. Do not write anything.

## What you may choose

{{actions}}

## The rules that decide most of these

These are measured, not opinions. Each one cost real money to learn.

1. **A coincidence is a fact about the specification, not about the cut.** When
   the bracket says a hidden fact passed on the `naive` build, the instinct is
   to re-cut and hide different facts. That does not work: three further `split`
   calls on one task moved the anchor count 2 → 4 → 2 and changed nothing,
   because re-cutting only chooses *which* parts to hide and every part was
   derivable from the surrounding source. One `author --extend` — which keeps
   the parts and the oracle and only adds parts carrying content the codebase
   cannot supply — took `naive` from 5/10 to 1/10. So: **coincidence ⇒
   `author_extend`, never `resplit`.**

2. **`resplit` is for a LEAK, and almost nothing else.** Re-cut when the ticket
   printed an identifier its own hidden facts need. `split` already detects that
   case and re-cuts itself once without being asked, so if you are reaching for
   `resplit` a second time, ask what makes this different.

3. **`broken` and `unreachable` are real defects; stop.** `broken` means the
   oracle itself fails the test. `unreachable` means a build given the ticket
   *and* every hidden requirement still fails — the requirement's wording does
   not say what the suite grades, and no amount of re-cutting helps.

4. **The healthy naive shape is: passes `open_feature`, fails everything else.**
   Failing everything including `open_feature` is *not* a better result. It
   means the suite grades something the ticket never states, so a blind score of
   0.00 cannot be told apart from an agent that built nothing — which is the
   whole reason that number is reported. The repair is `amend_ticket`: state the
   missing detail in the ticket, leave `hidden_requirements` byte-identical, and
   rebuild. It is never another `split`, which would re-roll which facts are
   hidden and throw away verdicts already in hand.

5. **Perfectly correlated failures are ONE defect, not variance.** If several
   facts fail together on the same runs with the same assertion text, find the
   single sentence behind them before sampling more.

6. **`hand_cut` is a real answer.** One task's `split` gate came back 0-of-8 and
   a person re-cut it by hand to 8-of-8 for $0, because the oracle is
   cut-independent and nothing had to be rebuilt. If the fix is small, specific
   and you can say exactly what it is, say so in `reason` and choose `hand_cut`.

7. **When in doubt, `stop`.** Parking a task costs a message. Spending forward
   into a defect costs the stage, and every stage after it.

## Learnings recorded during this run

These come from the person running the fleet, mid-flight. They override the
general rules above where they conflict.

{{notes}}
