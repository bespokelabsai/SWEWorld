---
title: "Postmortem: Nov 12 revert in distill.py and poem.py"
author: dario
created_at: 2024-11-13T09:42:00+00:00
---

# Postmortem: Nov 12 Revert in distill.py and poem.py

Nov 13, 2024

---

## What happened

Changes to distill.py and poem.py landed as part of ongoing request pipeline work. Shortly after merge, a regression was caught in the affected code paths. Both files were reverted to their prior state. The revert was clean, no data loss.

The specific logic that regressed involves how those two files interact with request parsing. That interaction was not fully exercised by the checks in place at the time of merge, so the regression made it through.

## Impact

- Short window of broken state in the affected code paths (duration: I don't have the exact timestamps, need to pull from git log)
- No downstream data corruption confirmed
- Revert resolved the immediate issue

## Timeline

Honestly this is thin because I'm reconstructing from memory and the commit log. Anyone with more context should add to this.

- Nov 12: changes to distill.py and poem.py merged as part of pipeline work
- Nov 12: regression caught post-merge
- Nov 12: both files reverted to prior state
- Nov 13: this postmortem written

## Root Cause

The changed logic in distill.py and poem.py touches request parsing in ways that weren't fully covered by pre-merge checks. The review process at the time didn't have a specific gate for request parsing edge cases in those files, so the regression wasn't caught before the merge landed.

This isn't about the complexity of the change in isolation. It's that the interaction surface between those two files and the parsing layer is broader than the existing checks account for.

## What went well

- Regression was caught quickly, before any downstream data was affected
- Revert was clean and straightforward
- No cascading failures

## Action Items

- [x] Revert landed (Nov 12)
- [ ] PRs touching distill.py or poem.py now require an explicit second reviewer pass focused on request parsing edge cases (process change, effective now)
- [ ] Move to PR-only process, which closes the gap that let this land without adequate review (in progress, not done yet as of this writing)
- [ ] Re-implement the reverted feature with test coverage before it goes back in, no firm timeline yet

## Open Questions

- What's the actual broken window duration? Need the timestamps from git log, I didn't pull them before writing this.
- Are there other files with the same request parsing interaction that should be flagged for the same reviewer requirement? distill.py and poem.py are the ones we know about, but I don't have a full picture of the pipeline surface.
- Who is picking up the re-implementation? Not assigned as of Nov 13.

---

This postmortem is also the reference point for the 0.1.7 release notes re: this revert.
