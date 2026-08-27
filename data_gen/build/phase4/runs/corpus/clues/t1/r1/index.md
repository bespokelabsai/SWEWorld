# t1.r1 — Prompt-level response cache keying

## The hidden requirement

- **rule** — The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone.
- **scope** — Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes.
- **exclusions_or_crossover** — Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses.
- **failure_behavior** — If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising.
- **observability** — `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows.

22 of 22 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [h1](h1.md) | yes | dermot | #engineering |  |
| [h2](h2.md) | yes | dario | #code-review |  |
| [l_model_1](l_model_1.md) | yes | gideon | #random | sc_model |
| [l_model_2](l_model_2.md) | yes | dermot | #incidents | sc_model |
| [l_params_1](l_params_1.md) | yes | gideon | #help | sc_params |
| [l_params_2](l_params_2.md) | yes | emil | #engineering | sc_params |
| [l_params_3](l_params_3.md) | yes | dario | page:design-t1-plant | sc_params |
| [l_prompt_1](l_prompt_1.md) | yes | dermot | #engineering | sc_prompt |
| [l_prompt_2](l_prompt_2.md) | yes | dario | page:runbook-bulk-llm-inference | sc_prompt |
| [l_prompt_3](l_prompt_3.md) | yes | emil | #engineering | sc_prompt |
| [l_schema_1](l_schema_1.md) | yes | emil | #engineering | sc_schema |
| [l_schema_2](l_schema_2.md) | yes | dario | page:design-t2-plant | sc_schema |
| [l_schema_3](l_schema_3.md) | yes | gideon | #incidents | sc_schema |
| [l_scope_1](l_scope_1.md) | yes | emil | #engineering | sc_scope |
| [l_scope_2](l_scope_2.md) | yes | gideon | #pipeline | sc_scope |
| [l_scope_3](l_scope_3.md) | yes | dermot | page:postmortem-2025-01-13 | sc_scope |
| [l_stats_1](l_stats_1.md) | yes | gideon | #viewer | sc_stats |
| [l_stats_2](l_stats_2.md) | yes | emil | comment:handover-status-tracking-cost-reporting-and-the-v-c0 | sc_stats |
| [l_stats_3](l_stats_3.md) | yes | dario | #cookbooks | sc_stats |
| [l_unhash_1](l_unhash_1.md) | yes | emil | #cookbooks | sc_unhashable |
| [l_unhash_2](l_unhash_2.md) | yes | dermot | #help | sc_unhashable |
| [l_unhash_3](l_unhash_3.md) | yes | gideon | #pipeline | sc_unhashable |
