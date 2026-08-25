---
title: "Postmortem: release-and-ci revert on Jan 10"
author: dario
created_at: 2025-01-13T09:28:00+00:00
---

# Postmortem: release-and-ci revert, Jan 10

CI was broken for some portion of Jan 10 after a change to the release and CI configuration was merged to main. Merges on the main development path were blocked until a revert restored the working state. No data loss. This document records what we know so far and what changes as a result.

## Timeline

```
Jan 10  release-and-ci change merged to main
Jan 10  CI pipeline failures observed
Jan 10  revert executed, pipeline restored
```

The exact times between those three events are not captured here yet. Dermot Callaghan's workstream (WS-014) should be able to pull them from the CI logs.

## Impact

- Main development path blocked for merge during the window between merge and revert
- CI pipeline disrupted for the same window
- No data loss; revert restored full functionality

We don't have an exact count of how many merges were queued or delayed during that window.

## Root cause

Still under investigation as part of WS-014 (Release Engineering, CI & Test Suite), which Dermot is leading. The specific configuration change that triggered the failure hasn't been fully pinned down yet. Once WS-014 documents it I'll update this page.

Honestly, until we have the full failure trace I'm reluctant to write more here. A plausible explanation isn't the same as a documented one.

## What went well

The revert happened on the same day. Nobody waited until the next morning to escalate, and the pipeline was back to a working state without the failure spreading further.

## Action items

- [ ] WS-014 to document the exact configuration that failed and add a regression guard
- [ ] CI changes going forward to be staged or validated in a branch before merging to main (need to agree on what "validated" means here, could just mean a manual run, TBD)
- [ ] Postmortem findings to be reviewed in the next engineering sync
- [ ] Pull exact timestamps from CI logs and fill the gap in the timeline above

## Open questions

- Were there signals in the pipeline logs that would have caught this before the merge landed? Need someone with access to the CI dashboard to check.
- Should release-and-ci changes require an additional review step or a separate approval gate? I think probably yes but this should be a conversation in the engineering sync rather than me deciding it unilaterally.
