---
title: "Weekly sync notes: week of Feb 10 \u2014 pickler regression"
author: emil
created_at: 2025-02-12T09:21:00+00:00
---

# Weekly sync notes: week of Feb 10, pickler regression

## Pickler revert

Revert went in Monday Feb 10 after cache invalidation issues surfaced in prod. I dont have the full error text in front of me but the symptom was stale cache entries surviving across what should have been a clean invalidation boundary. The decision to revert was straightforward once we saw it reproducing reliably, no argument there.

- v0.1.18.post4 shipped as the hotfix release
- need to confirm with whoever owns the pickler work what the path forward looks like before we re-land it
- `[TODO]` get the original regression issue linked here

## Hotfix release (v0.1.18.post4)

Went out this week. As far as I know it is just the pickler revert, nothing else bundled in. Someone should double-check the release notes to make sure nothing snuck in.

## Cost-map config work

Changes landed across two services: provider-integrations and online-request-processing. Both look like they made it in cleanly.

- PR 481 (cost-map) is still open, pending final safety review of the fallback logic
  - I think the fallback behavior is the right thing to hold on, especially if a provider returns something unexpected mid-request
  - not blocking next release yet but it will be if we dont close the review out by end of week
- works for me to merge 481 once whoever is doing the safety review signs off, I dont want to rush that

## Multimodal prompt surface

Updated this week. I dont have details on exactly what changed, need to check with whoever owns that surface area.

- open question: is this stable enough to carry into next week without another look, or do we want someone to do a quick sanity pass before the next release?

## Open items

- [ ] confirm multimodal changes are stable (see above)
- [ ] confirm cost-map (provider-integrations + online-request-processing) stable for next release
- [ ] PR 481 safety review on fallback logic, needs a reviewer to actually close it
- [ ] PR 468 (n samples) still under discussion, no resolution this week, lets circle back on that next sync
- [ ] link the original pickler regression issue to these notes once someone digs it up

## Questions

- Who is picking up the pickler re-land? Is there a plan or are we waiting on the regression root cause first?
- PR 468, is the n samples discussion blocked on something specific or just not prioritized yet? I dont know enough about where that landed to say.
