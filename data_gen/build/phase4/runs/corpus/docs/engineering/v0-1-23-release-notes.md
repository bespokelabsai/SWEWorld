---
title: "v0.1.23 Release Notes"
author: emil
created_at: 2025-04-11T09:28:00+00:00
---

# v0.1.23 Release Notes

22nd release. 323 changes merged to date.

## What's in this release

- **Metadata schema now includes cost fields** (PR 626)
  - fields added to track per-request cost data in the metadata output
- **n-samples support in generation params** (PR 468, in progress)
  - not fully landed yet, more coming
- **Param to disable the metadata db** (PR 583, in progress)
  - same, still moving
- Ongoing provider and integration work across:
  - batch-mode
  - local-offline-inference
  - multimodal-prompts
  - blocks-and-recipes

## Upgrading

No breaking public API changes. Drop-in upgrade.

---

## v0.1.23.post1

Same-day hotfix on top of v0.1.23.

### What it fixes

- Failed-requests jsonl handling
- Batch cancellation fix
- Dead viewer code removed (conftest and viewer cleanup)

### Should you upgrade now?

Not mandatory. If you're not hitting failed-request handling or batch cancellation issues you can wait. That said, worth pulling before the weekend.

No public API changes.
