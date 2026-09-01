# What makes a hidden requirement verifiable

Given by the user, reproduced verbatim. The prompts in `prompts/` quote it rather
than paraphrase it, and `tg audit` grades against it clause by clause.

---

This rubric is built from a post-mortem on tasks that looked verifiable but weren't. The
two failure modes observed were: **hidden requirements that didn't actually discriminate**
(agents passed without ever seeing the clue) and **hidden requirements that couldn't be
graded fairly** (correct implementations failed the test). Everything below exists to catch
one of those two failures before you generate task data.

---

## 0. The Core Method: Design Whole, Then Split

Idea: Don't write "a task" and "some hidden requirements" separately. Write one fully-specified
implementation (A + B + C), build and test it end to end, and only *then* decide which part
becomes the visible ticket (A) and which parts become hidden requirements (B, C) discoverable
via clues. Splitting after the fact prevents hidden requirements that were never really
separable from the visible ask in the first place. —> This might affect the diversity of the hidden requirements but I think this will make sure its more verifiable…

---

## 1. Foundational Constraints (apply to every requirement, visible or hidden)

A requirement (and its test) must satisfy **all** of these:

- **Pure/deterministic subsystem.** Not the generation loop, not anything whose "correctness"
is a matter of taste or an LLM's judgment call.
- **No live network calls in the test path.** Mock or fixture the boundary; never depend on a
real provider's live behavior.
- **Fully specified input/output contract.** Exact signatures, exact shapes, super verifiable (not "implement caching.")
- **Outputs checkable by exact/structural assertion.** Hashes, exact values, schema
conformance, exception types, counts, ordering (not "looks reasonable.")
- **Covers correctness and edge/error cases**, not just the happy path.
- **Isolated from unrelated repo machinery.** State exactly what may be reused vs. must be
built.
- **Deterministic across runs.** No timing, unseeded randomness, dict-order, or thread-race
dependence.
- **Has a golden reference implementation and a test suite you wrote and ran green** before
the task is stripped down for the agent.
- **Scoped to a single file or a couple of tightly coupled functions/classes** small enough
that the tests uniquely determine a correct solution, not one of several valid designs.

If a requirement can't meet these on its own, it can't be a hidden requirement and full stop,
regardless of whether it's interesting.

---

## 2. Failure Catalog A: Coincidence Facts

**Definition:** the hidden-requirement test passes whether or not the agent ever saw the clue.
The clue was unnecessary; the "hidden" requirement wasn't actually hidden.

**Diagnostic question for every hidden requirement:** *What does an agent that never saw
this clue do differently from one that did concretely, in the code it writes?* If you can't
name a specific divergent action, it's a coincidence fact.

- **Codebase already does it:** the requirement describes behavior the existing code/library
already provides by default. *Why it fails:* the blind agent inherits it for free by never
touching that path.
- **Prohibition satisfied by inaction:** "must not do X" where X requires deliberate extra
work the agent wasn't going to do anyway. *Why it fails:* doing nothing satisfies the rule;
it never tests restraint.
- **Model already knows it:** the "hidden" fact is a documented public convention (e.g., a
published pricing discount, a well-known API default) that models reproduce from
training/priors. *Why it fails:* the blind run gets it right from prior knowledge, not from
reading the clue.
- **Ticket gives it away:** the visible ticket's wording, examples, or naming already implies
the "hidden" detail. *Why it fails:* there's nothing left for the clue to add.
- **Entailed by the open feature:** once the agent builds the visible feature correctly, the
"hidden" requirement is the *only* way to do it; there's no alternative implementation that
omits it. *Why it fails:* the requirement isn't a separate fact, it's a restatement of what
A necessarily entails.
- **Obvious implementation happens to do it:** the single most natural way to write the code
(normal engineering instinct) satisfies the requirement without anyone intending it. *Why it
fails:* the test can't distinguish "read the clue" from "wrote normal code."

**How to catch it before shipping the task:** run the blind condition (ticket only, no clues)
against your own reference implementation *written naively, without consulting the hidden
requirements list*. If naive-blind passes the hidden-requirement tests then the requirement is a
coincidence fact so we should cut it or make it more specific until a genuinely different (but still
reasonable) blind implementation would fail it.

---

## 3. Failure Catalog B: Unmeasurable Facts

**Definition:** the requirement can't be graded fairly even with the right implementation,
because the test setup itself makes correct behavior look wrong (or can't observe the
behavior at all).

**Diagnostic question:** *What specific, finite, single-process, observable event would
differ between a correct and an incorrect implementation and can the harness actually
watch for it?* If the answer routes through another requirement's test, an unreachable code
path, an infinite time horizon, or an environment you can't build, it's unmeasurable.

- **State is unreachable** - the requirement names a feature combination the system itself
refuses to construct (e.g., "X must not get behavior Y" when the code raises before X and Y
can ever coexist). *Why it fails:* never happening and being correctly excluded are
indistinguishable - the test can't tell them apart.
- **Contradicts a sibling** - one requirement's rule guarantees a precondition that another
requirement's "failure behavior" needs to be false in order to test. *Why it fails:*
satisfying the rule makes the failure branch unreachable; the "test" trivially passes
because the rule works, not because the failure-handling works.
- **Behaviour has no consequence** - the requirement describes graceful/careful handling of
something that's fatal one layer down anyway (the run dies either way). *Why it fails:*
passing or failing the requirement produces the same end state - there's no differentiating
outcome to grade.
- **Only observable belongs to a different fact** - the one channel available to check
requirement X is really the channel for requirement Y (e.g., you can only confirm "computed
from a sample" via the same log line that already tests "reports that it sampled"). *Why it
fails:* grading X through Y's observable double-counts Y and can fail a correct X that just
doesn't expose it the same way.
- **No independent content** - the requirement restates half of a neighboring requirement, and
the only test available is already that neighbor's test. *Why it fails:* there's no way to
fail this requirement without also failing (or passing) the neighbor - it adds no
information.
- **Unbounded in time** - phrased with "forever," "never," "always," "rather than stalling
indefinitely." *Why it fails:* a test can only watch a finite window; a timeout can't
distinguish "will never happen" from "hasn't happened yet in N seconds," so a slow-but-correct
implementation looks broken.
- **Needs an environment the harness can't build** - per-process state, restart survival,
signal handling, cross-worker concurrency, multi-interpreter behavior. *Why it fails:* honest
testing requires infrastructure (second process, real restart, real signal) the grading
harness doesn't have; anything less tests a proxy, not the requirement.
- **The fake defines what's being graded** - a mock/stub controls the exact trigger condition
the requirement is supposedly testing (e.g., testing "how the system reacts under load" when
your test double decides when load happens). *Why it fails:* this is fine if the requirement
is about *the reaction*, but broken if it's about *when or how often the trigger fires*,
because the test authored the answer to its own question.

**How to catch it before shipping the task:** for each requirement, write down the one
concrete assertion your test makes, then ask "does passing/failing this assertion depend on
anything other than the agent's implementation of *this* requirement?" If yes, redesign the
test or drop the requirement.

---

## 4. Solvability & Difficulty Calibration

Beyond correctness of the individual tests, the task as a whole needs to satisfy:

- **Clues imply the hidden requirements.** Given the clue, a competent agent should be able
to derive the requirement - not just get lucky matching it.
- **Clues are discoverable from the given context** (e.g., Slack) through the normal
exploration process you expect the agent to use - not buried in a way that requires knowing
what to search for in advance.
- **The task is not solvable without the context.** If the blind condition (ticket only)
already passes the full hidden-requirement suite, the task provides no signal - see
Catalog A.
- **The task is not trivially solvable with the context either.** It should still require real
implementation work once the requirements are known - the difficulty should be calibrated
to the agents you're evaluating, not just "does it work at all."

---

## 5. Validation Protocol: Run Before Any Task Ships

Test each task under four conditions and check the expected outcome. A mismatch tells you
exactly which failure mode you have.

- **1. Blind:** input: ticket only (no hidden requirements, no clues). Expected: fails the
hidden-requirement tests. If it *passes* instead → coincidence fact (Catalog A); diagnose
which pattern and cut/rewrite.
- **2. Full spec (oracle check):** input: ticket + hidden requirements stated explicitly.
Expected: passes all tests. If it *fails* instead → your reference implementation or test is
broken, or the requirement is unmeasurable (Catalog B); fix before going further.
- **3. Ticket + clues:** input: ticket + the clues meant to lead to the hidden requirements
(no explicit hidden-requirement statement). Expected: passes the hidden-requirement tests.
If it *fails* instead → the clue doesn't sufficiently imply the requirement, or isn't
discoverable the way you assumed; rewrite the clue, not the test.
- **4. Reconstruction from clues only:** input: clues only, no ticket. Expected: the agent's
reconstructed understanding matches the actual hidden requirements. If it *diverges* instead
→ the clues underspecify or point somewhere else; this tests the clue set's completeness
independent of the ticket.

Additionally, **loop the test suite against multiple candidate implementations** (not just
your one golden solution) to catch:

- **Overshooting:** the test is so strict it rejects other valid, reasonable implementations
(false negative for a correct agent).
- **Undershooting:** the test is loose enough that a wrong or incomplete implementation still
passes (false positive that masks a broken hidden requirement).

A requirement only ships once conditions 1-4 all land where expected *and* the test survives
being run against a few deliberately-varied correct and deliberately-varied incorrect
implementations.

---

## 6. Pre-Flight Checklist (per hidden requirement)

Before generating clue data for a hidden requirement, confirm every box:

- [ ]  I can name a concrete code difference between an agent that saw the clue and one that
didn't.
- [ ]  I ran a naive blind implementation and it fails this requirement's test.
- [ ]  The test asserts something exact/structural, not judgment-based.
- [ ]  The test doesn't route through another requirement's only observable.
- [ ]  The behavior this requirement describes has an observable consequence if violated.
- [ ]  Nothing in the requirement is phrased as unbounded-in-time ("always," "never,"
"forever").
- [ ]  The state/feature-combination this requirement describes is actually reachable in the
codebase.
- [ ]  This requirement doesn't contradict a precondition required by a sibling requirement's
failure-mode test.
- [ ]  If a mock/fake is involved, it controls only the reaction being tested, not the trigger
condition the requirement is about.
- [ ]  The clue that reveals this requirement is discoverable through normal exploration of
the given context, and plausibly implies the requirement rather than merely mentioning
it in passing.
- [ ]  I ran the four-condition validation protocol (Section 5) and got the expected result in
all four.

If any box is unchecked, the requirement isn't ready - fix it before it's built into task
data, since these issues are exactly the ones that are cheap to catch by inspection now and
expensive to catch only after running the agent.
