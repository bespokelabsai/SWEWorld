---
title: "Release notes: v0.1.15.post1"
author: dermot
created_at: 2025-01-15T09:28:00+00:00
---

# Release notes: v0.1.15.post1

Hotfix release. Safe to upgrade directly from v0.1.15, no migration needed.

---

## What changed

- **Cost calculation fix** (bug, regression)
    - The cost-per-minute calculation was dividing by number of requests instead of elapsed minutes, so longer-running jobs were being overcharged.
    - The divisor is now corrected. The formula was right before the recent refactor and got broken during it.
    - No API surface change. No schema change.

- **Typo in opening docs example**
    - Caught during release review. Fixed inline.
    - No logic change.

- **README example updated for LLM interface**
    - The README example was out of date after the LLM class refactor. Updated to match the current interface.
    - No functional change to the library itself.

---

## Upgrading

Drop in over v0.1.15. No schema changes, no migration, no breaking changes to the API surface. All three changes are isolated from each other.
