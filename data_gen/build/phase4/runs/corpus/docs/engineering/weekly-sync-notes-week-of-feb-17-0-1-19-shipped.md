---
title: "Weekly sync notes: week of Feb 17 \u2014 0.1.19 shipped"
author: gideon
created_at: 2025-02-19T09:14:00+00:00
---

# Weekly sync notes: week of Feb 17, 0.1.19 shipped

**Date:** Feb 19, 2025
**Attendees:** Gideon Halloway, Emil Brandvold, Nikolai Berresford, Dario Kestrel

---

## Shipped

0.1.19 out. No blockers on the release, went cleanly.

## In-flight PRs

- PR 468, n samples
- PR 495, code executor enhancements, in review
- PR 502, telemetry config
- PR 509, litellm update
- PR 516, rich hyperlink, in review, CHANGES_REQUESTED
- PR 518, logger, in review

516 got changes requested so someone needs to go back to that before it moves. 518 and 495 are both sitting in review, no blockers as of today.

## Open issues

- issue 52, multiple samples
- issue 93, run status display
- issue 94, metadata.db run status
- issue 124, inspect cache invalidation

93 and 94 are probably related, i think we talked about that briefly but didnt land anywhere definitive. need to check with Nikolai on whether 94 is blocking anything for the next milestone.

## Next steps

- [ ] whoever owns 516 to address CHANGES_REQUESTED
- [ ] keep pushing on next milestone work, no blockers declared
- [ ] TBD on 93/94, are they actually the same root cause or just similar symptoms
