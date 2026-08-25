---
title: "v0.1.23.post1 Release Notes"
author: emil
created_at: 2025-04-11T10:10:00+00:00
---

# v0.1.23.post1 Release Notes

Same-day hotfix on top of v0.1.23. No API changes, drop-in replacement.

## What changed

- Failed-requests jsonl handling: fixed an issue where failed request records were not being written/read correctly
- Batch cancellation: fix for a case where cancellation was not propagating as expected
- Dead code removal: conftest and viewer cleanup, nothing that affected runtime behavior

## Should I upgrade?

If you are hitting either of the two bugs above: yes, pull this now.

If not: not strictly mandatory, but I'd recommend grabbing it before the weekend rather than leaving v0.1.23 in place.

If you are coming from anything older than v0.1.23: skip straight to post1, dont bother with the intermediate release.

## API compatibility

No public API changes. Existing integrations dont need to be updated.
