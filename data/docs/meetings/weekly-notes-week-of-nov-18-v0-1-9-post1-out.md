---
title: "Weekly notes: week of Nov 18 - v0.1.9.post1 out"
author: gideon
created_at: 2024-11-20T09:00:00+00:00
---

# Weekly notes: week of Nov 18 - v0.1.9.post1 out

## Release

v0.1.9.post1 shipped as a hotfix on Nov 19. Three releases total through end of this week. See the postmortem for the full account of what happened and why it needed a patch release this quickly.

## What landed

79 merged changes through today (Nov 20).

- Time logging added to the request pipeline (PR 159 in progress, this is related)
- aiohttp security bump (PR 156, waiting on final CI green before merge)
- Env example file (PR 133, still in review)
- vLLM example for online parallel processor (PR 78, still in review)

Honestly the list of things that fully cleared this week is shorter than I would have liked given where we started Monday, mostly because a few PRs are blocked on their owners getting back to us.

## PRs in flight

| PR | Owner | Status |
|----|-------|--------|
| 39 | Konrad | Minor code/docstring fixes. No re-pitch, holding. |
| 78 | Dario | vLLM example. Waiting on owner. |
| 90 | Dario | Disable-cache arg for Prompter. Waiting on owner. |
| 106 | Konrad | Text message summarization example. Waiting on owner. |
| 130 | Dermot | teacher.py example. Fate undecided, deferred to next week. |
| 133 | Otto | Env example file. In review. |
| 156 | - | aiohttp security bump. Lands when CI passes. |
| 159 | Gideon | Cost/token logging. Targeting to land this week. |

PRs 39, 78, 90, and 106 are all sitting and waiting on their owners to re-pitch or rework. No action taken on any of them this week. PR 130 (Dermot's teacher.py example) is a different situation, the fate question is one we deliberately deferred rather than stalled on, but we need a call on that next week.

## Open questions going into next week

None of these had any resolution this week.

- issue 33: cache check for batch completions
- issue 47: cancel submitted batches
- issue 48: README docs on batch
- issue 50: vary batch size by request count
- issue 52: multiple samples per request
- issue 55: loudness when request/response counts mismatch
- issue 57: expose more raw_response metrics to cache
- issue 62: generation configuration for LLM

Issues 47, 48, 50 feel related (all batch-adjacent) but I have not looked at them together in any systematic way yet so I am not sure if they can be grouped into one body of work.

## Next week

- [ ] PR 130 (Dermot): need a decision, not another deferral
- [ ] PR 159: get this landed, CI green by Monday if possible
- [ ] Revisit 39, 78, 90, 106, if owners dont respond we should decide whether to close or take them over
- [ ] TBD: someone should look at issues 47/48/50 together and say whether they are one project or three
