# t1.r2 — Prompt-level response cache keying

## The hidden requirement

- **rule** — `cache_stats()` must read from the same on-disk cache directory the rest of `curator.LLM` uses, honoring `CURATOR_CACHE_DIR` if set, and must never write to or mutate the cache directory itself.
- **scope** — Read-only access to whatever directory the existing caching layer resolves to at call time.
- **failure_behavior** — If the cache directory does not exist yet (no prior run), return zeroed stats rather than raising a file-not-found error.
- **observability** — The returned object must include the resolved cache directory path so users can verify which cache was inspected.

14 of 14 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [L1](L1.md) | yes | dario | #general | S1 |
| [L10](L10.md) | yes | gideon | #general | S4 |
| [L11](L11.md) | yes | dario | page:handover-request-processing-core-and-provider-bac | S4 |
| [L12](L12.md) | yes | emil | #viewer | S4 |
| [L13](L13.md) | yes | gideon | #pipeline | S5 |
| [L14](L14.md) | yes | dermot | page:postmortem-2024-12-10 | S5 |
| [L2](L2.md) | yes | emil | #pipeline | S1 |
| [L3](L3.md) | yes | dermot | page:design-ws-012-bulk-llm-inference | S1 |
| [L4](L4.md) | yes | gideon | #random | S2 |
| [L5](L5.md) | yes | dermot | #help | S2 |
| [L6](L6.md) | yes | emil | page:design-t3-plant | S2 |
| [L7](L7.md) | yes | dario | #code-review | S3 |
| [L8](L8.md) | yes | emil | #releases | S3 |
| [L9](L9.md) | yes | gideon | page:handover-status-tracking-cost-reporting-and-the-v | S3 |
