# t2.r1 — Structured output schema validation before dispatch

## The hidden requirement

- **rule** — Compatibility must be checked against a maintained list of model name patterns known to support structured outputs (e.g. gpt-4o family, o3 family per the existing model-support list), and the check must happen once at `LLM.__init__` time, not per-row at request time.
- **scope** — `LLM.__init__` only.
- **failure_behavior** — An unsupported model + response_format combination must raise `ValueError` immediately at construction, before `__call__` ever touches the dataset, so failures show up before any API spend.

12 of 12 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [L1](L1.md) | yes | dario | page:notes-2024-12-30 | S1 |
| [L10](L10.md) | yes | dario | comment:postmortem-2025-03-01-c0 | S3 |
| [L2](L2.md) | yes | gideon | #engineering | S1 |
| [L3](L3.md) | yes | emil | #releases | S1 |
| [L4](L4.md) | yes | dermot | page:postmortem-2025-05-06 | S1 |
| [L5](L5.md) | yes | gideon | #help | S2 |
| [L6](L6.md) | yes | dario | #code-review | S2 |
| [L7](L7.md) | yes | emil | comment:handover-request-processing-core-and-provider-bac-c0 | S2 |
| [L8](L8.md) | yes | dermot | #pipeline | S3 |
| [L9](L9.md) | yes | emil | #releases | S3 |
| [h1](h1.md) | yes | dermot | #pipeline |  |
| [h2](h2.md) | yes | dario | #code-review |  |
