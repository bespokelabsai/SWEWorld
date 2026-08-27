---
title: "Weekly sync notes: week of Feb 3 \u2014 v0.1.18 and v0.1.18.post4 shipped"
author: emil
created_at: 2025-02-05T09:14:00+00:00
---

# Weekly sync notes: week of Feb 3 - v0.1.18 and v0.1.18.post4 shipped

## Shipped

- v0.1.18 - out early in the week
- v0.1.18.post4 - patched same week
  - two post-releases against v0.1.18 is a lot for one week; both driven by litellm version pinning issues that surfaced after the initial cut
  - if i had to guess, the pinning stuff will keep biting us until we nail down a cleaner bump process (see PR 449 below)

## In flight

- **PR 445** - multimodal litellm support
  - targeting merge before next cut
  - sign-off on surface coverage still open (see questions below)
- **PR 443** - generation_params per row
  - blocked on design decision around merge vs. override semantics, not landing until that's resolved
  - there's an issue tied to this one that needs whoever owns the API surface to weigh in
- **PR 449** - litellm version bump
  - also targeting merge before next cut
  - directly related to why we had to push post4; want this in before we cut again
- **PR 362** - fix_json curly braces
  - still in flight, didn't come up much this week
- **PR 430** - OpenRouter reasoning examples
  - in review, no blockers flagged today

## Patch cadence note

Two post-releases in one week is worth flagging. Both were reactive to litellm pinning issues we didn't catch before the v0.1.18 cut. PR 449 is supposed to get us ahead of this, but I'd want to check with whoever owns the release checklist whether we have a step for validating dependency pins before tagging. We probably should.

## Open questions

- Per-row params (PR 443): merge behavior vs. full override when generation_params are specified at the row level. This needs a decision before we can land it, not just a review pass.
- Multimodal surface coverage (PR 445): who is signing off that we've covered the right input types? Not clear to me that's been formally assigned.

## Next week

- [ ] PR 445 and PR 449 merge before next cut
- [ ] PR 443: get design sign-off on override semantics, then re-evaluate
- [ ] PR 362 and PR 430: status TBD, didn't get to these today
