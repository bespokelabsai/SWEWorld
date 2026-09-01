You are cutting one fully-specified implementation into a **visible ticket** and
**hidden requirements**, for an agent evaluation.

The specification is already written and already built. Your job is only the cut.

## The whole specification

{{whole}}

## What the cut has to achieve

The visible ticket states the feature openly — enough that an agent knows what to
build and what to call it. The hidden requirements are the parts nobody wrote
down: an agent has to recover them from remarks scattered through a company's
chat, wiki and mail, or fail them.

So the test of a good cut is: **for each hidden fact, can you name the concrete,
different code a blind agent writes?** If you cannot, that fact does not belong
in the hidden set.

## The shape you must return

JSON matching the schema you have been given. Field by field:

- `title` — short noun phrase.
- `description` — **the visible ticket**. One paragraph. It states the API the
  OPEN feature needs — exact names and signatures for those, because the grader is
  allowed to require them — and nothing more. It must NOT hint at which
  alternative any hidden part chose, and see the naming rule below, which is the
  one that has actually gone wrong.
- `hidden_requirements` — exactly **two** requirements. Each has a `requirement`
  object drawn from these five fields, and each requirement should declare
  **three to five** of them:
  - `rule` — the core behaviour. Required.
  - `scope` — where it applies, and where it does not.
  - `exclusions_or_crossover` — the neighbouring case that must NOT get this
    behaviour, or must get it identically.
  - `failure_behavior` — what happens on the bad input, exactly.
  - `observability` — what a caller can see that proves it, exactly.
- `fact_sources` — for every field you declared, which part of the spec (`P3`)
  it came from and, in one clause, the alternative a blind agent would pick
  instead.

## Rules, and each one is a way tasks have failed before

**Name in the ticket only what the open feature needs.** Every helper you name in
`description` is a helper a blind agent will now write — and if one of your hidden
facts is a statement about what that helper does *inside*, you have handed the
fact over in the ticket. Take each name you put in the ticket and ask: is any
hidden fact a claim about this function's body? If yes, drop the name and re-state
the fact as behaviour observable through a name you kept. Concretely: if a fact
says "the size helper counts the separators between lines", do not name the size
helper — say the planner must respect a byte limit, and let the fact be graded by
where the planner puts the boundary.

This is the way this step has actually failed. A ticket that spelled out every
internal helper's signature let a ticket-only build reproduce four hidden facts
from the ticket alone, and the bracket scored them all as coincidences.

**Do not list, as "reused", the existing function a hidden fact tells the agent to
call.** The reuse list is written to be helpful and reads as an instruction. If the
fact is "measure the provider-specific request, not the generic one", then naming
the provider-specific builder as available machinery *is* the answer.

**Do not declare a fact whose alternatives you cannot name.** The spec gave every
part its alternatives. A fact whose part had none is entailed by the feature and a
blind agent gets it for free.

**And naming alternatives is not enough — this is the rule that was learned the
hard way.** A measured run declared ten facts, every one with two plausible
alternatives written out, and **nine came back as coincidences.** The alternatives
were real; they were just already resolved by the code. A blind engineer who reads
the function the ticket points at finds `"\n".join(...)` there and writes the
separator rule; finds `<=` natural and writes the inclusive limit; finds the
existing column check and copies it; returns the list they just built. Every one of
those was declared hidden and every one was free.

So apply this test to each candidate fact, and it is stricter than the
alternatives test:

> Could a competent engineer, with the ticket and the surrounding source, arrive
> at this by reading? If yes it is not hidden, however many alternatives exist.

What survives that test is content the codebase does not already imply:

- **an invented name** — a class, field or attribute nobody could guess, whose
  exact spelling and shape the grader can require;
- **a chosen value** — a threshold, a cap, a window, where nothing in the code
  says which number;
- **a policy with no local evidence** — of several behaviours the code is silent
  about, the one the team settled on;
- **a deliberate departure** — behaviour that contradicts what the surrounding
  code plainly does, so reading it leads you the wrong way.

In the measured run exactly one fact survived, and it was of the first kind: a new
exception subclass with a specific extra attribute, raised at a specific moment.
Nothing in the repository suggested it, so nothing in the repository gave it away.

**Prefer four facts of those kinds to ten of any kind.** The grader divides by the
number declared, so a fact you do not declare costs nothing, and a fact that does
not discriminate costs the whole reading of the blind arm.

**Do not declare a prohibition that inaction satisfies.** "Must not add a public
knob", "must not special-case per provider" — an agent who writes nothing passes
those. If the restraint is real, phrase the fact so it is only reachable once the
feature exists, and say in `fact_sources` what makes it so.

**Do not declare a fact the ticket gives away.** After you write `description`,
re-read it against every fact and cut any fact the ticket implies. Prefer cutting
the fact to weakening the ticket: the ticket has to be a real, buildable
instruction.

**Do not declare a public convention.** If the fact is a documented default, a
published price, a well-known API behaviour — a model reproduces it from priors,
not from a clue.

**Do not declare two facts that share one observable.** If the only way to check
fact X is the assertion that already checks fact Y, X adds no information and one
of them will fail a correct implementation.

**Nothing unbounded in time.** No "always", "never", "forever", "rather than
stalling indefinitely". A grader watches a finite window.

**Fewer, sharper facts beat more, softer ones.** The grader divides by the number
of facts declared, so an undeclared field costs nothing. Six facts that all
discriminate is a better task than ten of which four are free.

{{feedback}}

## The rubric

{{rubric}}
