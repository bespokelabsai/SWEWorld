You are **extending** an implementation specification you already wrote, because a
measurement found most of it does not do the job it was written for.

## What was measured

{{feedback}}

## Your specification, as it stands

{{whole}}

## What went wrong, and what to do about it

Every part you wrote named plausible alternatives, and that was not enough. A
competent engineer reading this codebase resolves most of those alternatives by
reading — the existing function shows them `"\n".join(...)`, or `<=` is simply the
natural choice, or the surrounding code already contains the check. A part whose
behaviour is *derivable* cannot be a hidden requirement, however many alternatives
exist on paper.

Do not delete or rewrite the parts you have. They are correct and an
implementation of them exists. **Add parts** whose content this codebase cannot
supply, of these kinds:

- **an invented name** — a class, exception, field, attribute or key nobody could
  guess, whose exact spelling and shape a grader can require;
- **a chosen value** — a threshold, cap, window, margin or retry count where
  nothing in the code says which number;
- **a policy with no local evidence** — of several behaviours the code is silent
  about, the one this team settled on;
- **a deliberate departure** — behaviour that contradicts what the surrounding code
  plainly does, so reading the code leads a blind engineer the wrong way.

Note which kind of the surviving part was, and design more like it.

## Constraints on what you add

- **Consistent with everything already specified.** The new parts extend the same
  feature; they must not contradict an existing part or change an existing
  signature. Additive only: new fields on existing shapes, new names, new
  behaviours at moments the spec did not previously pin down.
- **Same purity rules.** Pure, deterministic, no network, no sleeping, no timing,
  no threads, no second process, no unseeded randomness.
- **Same exactness.** Every new part needs its alternatives written out AND a
  finite exact observable with literal values. Verify each literal by running it —
  do not guess a byte count or a repr.
- **Plausible as something a real team decided.** An invented name has to be one
  an engineer would actually have chosen, and a chosen value has to have a reason
  someone could have had. A fact that reads as arbitrary *to the agent* reads as
  arbitrary to a reader of the corpus too, and the whole point is that it looks
  like a decision.
- **Aim for four to six new parts.** Enough that the split step can build two
  requirements out of arbitrary content alone.

## How to write them

Append to `whole.md`, continuing the part numbering, in the same format — including
the `**Arbitrary:**` line naming which of the four kinds each part is. Then update
the `## End to end` section so the worked example reflects the additions, with
exact literal values. Change nothing else.

## Running things

You can execute against the checkout:

```
{{exec_cmd}} --cmd 'python3 -c "from bespokelabs.curator... ; print(...)"'
```

That runs in a container where curator's dependencies exist, with
`PYTHONPATH=<tree>/src`. Use it for every literal value you write down.

## The rubric

{{rubric}}
