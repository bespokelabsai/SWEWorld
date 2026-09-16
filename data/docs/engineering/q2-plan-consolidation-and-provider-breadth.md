---
title: "Q2 Plan: Consolidation and Provider Breadth"
author: konrad
created_at: 2025-03-03T08:46:00+00:00
---

# Q2 Plan: Consolidation and Provider Breadth

## Where we are

281 changes merged, 18 releases out. Q1 moved fast and we have real surface area to show for it. The risk now is that we keep moving at that pace and something quietly breaks underneath us before anyone notices. Q2 is about slowing down deliberately, not because we ran out of things to do.

## Priorities

### 1. Prune and stabilize

The sprint pace left some design questions open. Q2 closes them.

- PR 574 (make process_response mandatory) and PR 571 (RAFT block shape) are the clearest examples, both close things that were left loose in Q1
- blocks-and-recipes API still shifting, need to get it to a shape we can hold
- do a pass on what we shipped Q1 and make sure it works end-to-end, not just in the happy path, that audit hasnt happened yet
- anything that isn't pulling weight in terms of usage or maintenance burden is a candidate to cut, I'd rather drop it cleanly than carry it

I think the instinct in Q1 was to keep adding surface rather than finishing what was half-done. That changes in Q2.

### 2. Provider breadth

The headline additions are already in flight:

- PR 565, OpenAI client backend
- PR 566, DeepSeek API
- rate-limit detection, issues 207 and 233, this one sits just behind the above two but its actually more important for multi-provider runs, without it those runs are fragile
- batch mode (cost-sensitive use case)
- local offline inference (air-gapped use case)

These arent new directions. They're the breadth pass the core always needed. Provider work should be mostly wrapped before we start pulling on the open questions below.

### 3. Sustainable pace

We will not ship a release every week in Q2. The goal is fewer PRs open at once, faster turnaround on what is open, and postmortems that get written before the next incident lands.

- Dermot is picking up release cutting, so that's no longer sitting on a single engineer as a blocker
- Mar 1 incident is the first test of the postmortem discipline, that needs to be written and closed properly before we move on
- [ ] postmortem for Mar 1 incident (owner TBD, should not wait)
- [ ] agree on max concurrent open PRs target (my instinct is somewhere around 8-10 but haven't talked to the team about it yet)

## Open questions not resolved this quarter

These stay open but should have room to land once provider work is stable:

- issue 52, multiple samples per request
- issues 102 and 121, Pydantic-to-dict handling (these two are probably related, need to check)
- issue 105, distribution graph skew in curator-viewer

I dont want to commit Q2 scope to these before the provider breadth is in a stable place. Pulling on them earlier risks the same problem we're trying to fix, too much in flight at once.

## Questions

- Who is doing the Q1 end-to-end audit? I can coordinate but someone needs to own the actual pass through the test coverage gaps.
- Is there a decision on whether batch mode lands before or after rate-limit detection? My preference is rate-limit first but I dont know what the dependency looks like on the provider side.
- curator-viewer issue 105, does anyone actually know what's causing the graph skew? Last I checked it was undiagnosed.
