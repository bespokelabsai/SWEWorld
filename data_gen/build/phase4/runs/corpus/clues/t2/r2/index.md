# t2.r2 — Structured output schema validation before dispatch

## The hidden requirement

- **rule** — The model-support list used for this check must be the same list maintained for the existing structured-output feature (the one already updated when new models like o3 are added) — this task must not introduce a second, separate list that could drift out of sync with it.
- **scope** — Reuse of the existing model-support list only.

9 of 9 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [l1](l1.md) | yes | dario | #pipeline | sc1 |
| [l2](l2.md) | yes | emil | #incidents | sc1 |
| [l3](l3.md) | yes | gideon | #pipeline | sc1 |
| [l4](l4.md) | yes | emil | #pipeline | sc2 |
| [l5](l5.md) | yes | dermot | #pipeline | sc2 |
| [l6](l6.md) | yes | gideon | #random | sc2 |
| [l7](l7.md) | yes | dario | #code-review | sc2 |
| [l8](l8.md) | yes | emil | #engineering | sc3 |
| [l9](l9.md) | yes | gideon | #engineering | sc3 |
