---
title: "Weekly sync notes: week of Jan 27 \u2014 v0.1.17 and v0.1.17.post1 shipped"
author: nikolai
created_at: 2025-01-29T09:14:00+00:00
---

# Weekly sync notes: week of Jan 27, v0.1.17 and v0.1.17.post1 shipped

## Shipped this week

- v0.1.17
- v0.1.17.post1 (quick follow-up, same week)

209 changes merged to date, 12 releases total.

## PRs in flight

- **PR 411**, ci: cache (Emil), not merged yet, need to check if it's blocking anything downstream
- **PR 418**, pass generation params in gemini batch (Emil)
- **PR 407**, verifiers for Code (Dario)
- **PR 362**, fix_json adds curly braces (Ilse)
- **PR 161**, Curator Usage Example: Prometheus LLM Judge evaluation (Gideon), this one has been open a while, i want to make sure we follow up with Gideon and not let it stall
- **PR 133**, adding an env example file (Otto), should be straightforward honestly, not sure why it's still open

## Merged this week

- **PR 420**, push_to_hub override, merged

## Open issues (still pending)

- issue 52, multiple samples per request
- issue 92, 93, 94, UI and metadata.db (these three feel related, hold on to see if anyone picks them up together)
- issue 102, return dictionary without Pydantic objects
- issue 105, distribution graph skew
- issue 121, pydantic to dict handling (possibly overlaps with 102? i havent looked closely enough to say for sure)
- issue 124, inspect cache invalidation

None of these moved this week as far as I can tell.

## Questions / things i'm not sure about

- PR 161 and 133 are both old enough that we should probably decide: are we still expecting them to merge, or do we close and re-open if the contributor comes back? I dont want to just leave them indefinitely.
- Issues 92/93/94, are these being tracked somewhere together, or handled separately? Someone should own the UI+metadata.db work explicitly.
