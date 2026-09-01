You are auditing ONE hidden requirement in an agent-evaluation task, adversarially.
Your job is to find the reason it should not ship. Assume it is flawed and look
for the flaw. Saying "this is fine" is only useful once you have genuinely tried.

## The task the agent is told openly

{{ticket}}

## The one fact you are auditing

Requirement **r{{req}}**, field **{{field}}**:

> {{fact}}

Its siblings in the same requirement, for the "shares an observable" and
"contradicts a sibling" checks:

{{siblings}}

The other requirement's facts, for the same reason:

{{others}}

## The test that grades it

{{test_source}}

## What the free bracket already measured

{{bracket}}

`hidden` there means the golden tree passes this fact and both an untouched
checkout and a blind implementation fail it. That is evidence, not proof: the
blind implementation is one sample of one blind agent. Your job is to find the
blind implementation it did not write.

## Answer these, in the schema you were given

1. **The divergent action.** Name the concrete, specific code an agent who saw
   the clue writes and an agent who did not does not. Not "handles the edge case
   correctly" — the actual expression, call, or branch. If you cannot name one,
   this fact is a coincidence and you must say so.

2. **Catalog A.** For each of the six patterns, does it apply? Quote what makes
   you think so.
   - codebase already does it
   - prohibition satisfied by inaction
   - model already knows it (a documented default, a published convention)
   - the ticket gives it away
   - entailed by the open feature (once A is built correctly, this is the only way)
   - the obvious implementation happens to do it

3. **Catalog B.** For each, does it apply?
   - the state it describes is unreachable in this codebase
   - it contradicts a precondition a sibling's failure test needs
   - the behaviour has no consequence (fatal one layer down either way)
   - its only observable really belongs to a different fact
   - no independent content — it restates half of a neighbour
   - unbounded in time ("always", "never", "forever")
   - needs an environment the harness cannot build
   - a fake defines the trigger the fact is about, not just the reaction

4. **The one assertion.** Quote the single assertion in the test that decides
   this fact. Then answer: does passing or failing it depend on anything other
   than this requirement's implementation?

5. **The blind implementation that passes.** Try to write one: a reasonable
   engineer, ticket only, who happens to satisfy this fact. If you can, quote it
   — that is a coincidence the bracket's one sample missed, and it is the most
   valuable thing you can find.

6. **The correct implementation that fails.** Try to write one: a different but
   legitimate reading of the requirement that this test rejects. If you can,
   quote it — the test is overshooting and will fail a correct agent.

## Verdict

`ship` only if you found nothing in 2, 3, 5 or 6 and you named a real divergent
action in 1. Otherwise `cut` (the fact cannot be saved), `narrow` (the fact is
real but too broad — say what to narrow it to), or `retest` (the fact is real and
the test is wrong — say what the test should assert instead).

## The rubric

{{rubric}}
