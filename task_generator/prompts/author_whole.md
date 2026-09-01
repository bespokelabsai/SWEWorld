You are designing ONE implementation task for an agent evaluation, against a real
Python library. This step writes the **whole specification** — every part of it,
openly. Nothing is hidden yet. Splitting happens later and is not your concern.

## The library

`{{repo}}/curator` — `bespokelabs/curator`, a batch/online LLM inference library,
version 0.1.29, src-layout under `curator/src/bespokelabs/curator/`. Read it. It
is checked out and you have it.

## The area you are designing in

{{brief}}

## What you must produce

Write `whole.md` in your working directory. Nothing else. Structure it exactly:

```
# <title: a short noun phrase naming the feature>

## Target
- files that change, with paths
- what existing machinery may be REUSED (name it)
- what must be BUILT (name it)
- python version, dependencies available

## The API
Exact signatures. Exact types. Exact return shapes, field by field, with types.
No prose where a signature will do.

## Parts

### P1 — <short name>
**Behaviour.** What it does, in one or two sentences, precisely enough that two
engineers implementing from this sentence alone would produce the same observable
result.

**Alternatives a competent engineer would plausibly choose instead.** At least
two, each a real design an experienced person might pick if nobody told them
otherwise. Write them out.

**The observable.** The single, finite, exact assertion that separates this
behaviour from EVERY alternative above. An integer, a count, a byte length, an
exception type, a structural shape. Name the values.

### P2 — ...
(as many parts as the feature honestly has; aim for 6 to 10)

## End to end
One worked example. Concrete inputs. The exact expected outputs, as literals.
```

## The three rules that decide whether this task is any good

**1. Every part must name real alternatives — AND the code must not already
resolve them.** A part whose behaviour is the only sensible way to write the code
is not a part; it is entailed by the feature, and later it becomes a "hidden
requirement" a blind agent passes for free.

Naming alternatives is necessary and it is not sufficient. This was measured: a
specification of ten parts, every one with two plausible alternatives written out,
produced ten candidate hidden requirements of which **nine were passed by a build
that never saw them.** The alternatives were real. They were simply already
resolved by the surrounding source - the engineer read the function the ticket
pointed at, saw `"\n".join(...)`, and wrote the separator rule; wrote `<=` because
it is natural; copied the existing column check; returned the list they had just
built.

So for every part, ask the harder question:

> Could a competent engineer, reading this codebase, arrive at my chosen
> behaviour rather than an alternative? If yes, the part is not hidden material.

**At least half your parts must carry content this codebase cannot supply.** Four
kinds qualify:

- **an invented name** - a class, exception, field or attribute nobody could guess,
  whose exact spelling and shape a grader can require;
- **a chosen value** - a threshold, cap, window or margin where nothing in the code
  says which number;
- **a policy with no local evidence** - of several behaviours the code is silent
  about, the one this team settled on;
- **a deliberate departure** - behaviour that contradicts what the surrounding code
  plainly does, so reading the code leads you the wrong way.

In the measured run exactly one part survived, and it was of the first kind: a new
exception subclass carrying a specific extra attribute, raised at a specific
moment. Nothing in the repository suggested it, so nothing gave it away. Design for
that on purpose.

Mark each part `**Arbitrary:**` with which of the four kinds it is, or
`**Arbitrary:** none - derivable from <file>` when it honestly is derivable. Being
straight about a derivable part is useful: the split step needs to know which is
which, and a specification of ten parts that claims ten arbitrary ones is worse
than useless.

**2. Every part must have a finite, exact observable.** Not "the log should
mention it". A count, a length, a type, a shape, with values. If the only way to
tell right from wrong is how long something took, or whether something *never*
happens, the part is unmeasurable — cut it.

**3. The whole thing must be pure and deterministic.** No network. No sleeping.
No timing. No unseeded randomness. No dict-ordering dependence. No second
process, no signals, no threads. If the area you were given cannot be specified
this way, say so plainly in `whole.md` under a heading `## Cannot be specified`
and explain what stopped you — that is a useful answer, not a failure.

{{feedback}}

## Grounding

Read the actual code before you write a signature. Name real files, real
existing functions, real fields. If the library already has a latent bug in this
area, say where it is, with a file and line — a part that fixes something real is
worth more than a part that invents something.

## The rubric this will be graded against

{{rubric}}
