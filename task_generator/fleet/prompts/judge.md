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

## The plant — rules for `clues`, `settle`, `reverse`, `reorder`, `reknit`, `consistency`, `prove`

These stages hide the requirements as remarks scattered through the company's
chat, wiki and mail. They all rewrite one file, `clues/plant.json`, and they all
report through the same findings. Three repairs answer them and they are not
interchangeable:

- **`repair`** — a *measured build* blamed specific remarks. Only meaningful
  after `prove`, which writes `clues/proof.json` naming the failing assertion.
  It rewrites just those remarks and leaves the rest, because placement — which
  conversation each remark sits in and what it answers — is the expensive half
  and the proof just showed the others working.
- **`replace`** — the wording is right and the *placement* is wrong: a remark in
  a room where nobody would say it, a date before the problem it answers, a
  source the holder never uses. Re-places every remark without re-wording any.
- **`reclues`** — the *tree* is wrong. Reach for this only when the requirement
  is not decomposed into recoverable pieces at all: a graded name appears in no
  remark and no rewrite can add it without inventing a new leaf, or a
  subconclusion rests on one remark so nothing can be inferred. It throws away
  every placement, so it is the most expensive answer by a wide margin.

Rules, all measured:

1. **A fresh plant reporting `fact_conflicts: never run` is not a defect.** The
   `consistency` stage has not run yet and the plan runs it three steps later.
   Judge the other findings.
2. **A name cannot be inferred; a rule can.** If `missing_identifiers` names a
   symbol, the tests read it by position — an attribute, a dict key — and that
   fact scores zero however well the corpus reads. Some entries are noise
   (`A`, `The`, `MB`, `HIGH`): a remark will contain them by accident, so check
   whether the name is a real identifier before spending a re-plant on it.
3. **Correlated failures in `prove` are ONE defect in ONE remark.** Read the
   grid in `clues/proof.md`: facts that fail on the same runs and pass on the
   same run share a cause. Find the sentence before asking for more samples.
   Five facts failing together is not five problems.
4. **`out_of_order` and `unreversed` are chronology, and a reader goes in date
   order.** A decision dated before the complaint it answers, or a herring
   nothing ever retracts, leaves the wrong remark as the last word — which is
   the one a reader believes.
5. **A corpus that argues with itself is unsolvable, not hard.** An invented
   quantity in an exchange that no remark states cost one task four facts: the
   agent read the most recent number and behaved correctly on it.
6. **Hedged substance is not realism.** "The shape isn't settled", "don't write
   anything against it yet" — six consecutive rollouts quoted that back as their
   reason to skip a requirement. Hedging the *schedule* is the truth of this
   corpus and stays; hedging the *substance* means there is nothing to recover.
7. **Wordiness and stock closings are reported, never fatal.** A task shipped at
   8.4× inflation and scored 1.00 on its clues arm. Do not spend a paid pass on
   `too_wordy` or `stock_phrasing` alone.

### Which stage owns which defect — do not repair what the next stage fixes

The plant chain runs in this order, and each stage exists to fix a specific
class of finding **that the stages before it are expected to leave behind**:

```
clues → settle → reverse → reorder → reknit → consistency → prove
```

| finding | owned by | so before that stage runs it is |
|---|---|---|
| `fact_conflicts: never run` | `consistency` | **expected**, not a defect |
| `out_of_order` — answers dated before their questions | `reorder` | **expected** |
| `unreversed` — a herring nothing retracts | `reverse` | **expected** |
| `unknit` — no exchange, or an exchange whose wording is stale against the remark | `reknit` | **expected** |
| `unstated: implied` | `settle` | **expected** |

**`settle` rewrites remarks, and the exchanges woven around them during `clues`
are stale the moment it does.** That is normal and `reknit` is the stage that
repairs it — it rewrites each exchange to say the remark as the plant now words
it. Do not answer stale exchanges with `replace`: re-placing chooses new
carriers with the SAME wording, so it does not fix a stale exchange at all, and
it costs a placement call per remark.

So: before reaching a stage, its findings are **owed**, and the answer is
`proceed`. Reach for a repair only when a stage that owns a finding has already
run and the finding is still there — that is the case the repairs exist for.

### `rewrite_exchanges` — when the conversation says the wrong thing

`fact_conflicts` and `unknit` are defects in the woven **exchange**, not in the
remark or where it sits: a thread whose last turn asserts the opposite of the
graded decision, or one that drops a claim the remark carries. A reader believes
the last word, so this is the shape that cost one task four facts.

Neither `replace` nor `reclues` touches it — the first re-places with identical
wording, the second throws away placement to fix a tree that is fine. Use
`rewrite_exchanges`: it re-weaves **only** the exchanges the findings name, via
`reknit --only <ids> --redo`, and leaves everything else alone. It is the
cheapest repair on the menu, roughly two calls per named exchange.

### Before you accept a `fact_conflicts` finding, look in the other sources

A conflict is only a conflict if **nothing later puts it right, anywhere**. The
resolving remark is often not where you expect:

- it may be filed under a **sibling fact** — `covers` is the tree's own claim and
  is truncated to two entries, so it is not a reliable index of what a remark
  carries;
- it may live in **mail or the wiki** rather than in chat, and a finding quoted
  from a chat exchange gives no hint that it exists;
- it may be a **reversal**, which exists precisely to retract an earlier
  decision and is filed as `kind: reversal`.

So read `clues/README.md` — which lists every remark in date order with its
source and carrier — before deciding. One conflict reported here was not one:
the remark that settled it was an email, and nothing in the finding said so.

The rule stands as the gate states it: a wrong statement is fine if a later
remark plainly overturns it, and a defect only when it is **the last word**. Your
job is to check whether it really is the last word, across every source.
