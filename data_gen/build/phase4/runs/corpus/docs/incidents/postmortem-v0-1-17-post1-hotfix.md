---
title: "Postmortem: v0.1.17.post1 hotfix"
author: nikolai
created_at: 2025-01-31T09:14:00+00:00
---

# Postmortem: v0.1.17.post1 hotfix

## What happened

v0.1.17 shipped with a broken executor interface. The multiprocessing backend calls a public method on the executor to run user functions in a subprocess, and that method had been renamed internally before release. The rename was not caught because nothing in CI exercises that call path end-to-end.

The result: calls to the executor returned None silently instead of raising, and bulk-llm-inference dropped the affected rows downstream without any error surfacing. Silent data loss in the output, no exception, no log entry that would catch your eye without knowing what to look for.

A user reported the problem on 2025-01-31, same day as the release.

## Timeline

```
2025-01-31  v0.1.17 released
2025-01-31  user report comes in describing missing rows in output
2025-01-31  root cause identified: executor method name mismatch
2025-01-31  v0.1.17.post1 shipped with fix
```

## Root cause

An internal rename of the executor's public method was merged without updating the call site in bulk-llm-inference, and without a regression test that would have caught the mismatch. The method signature drift meant the caller was invoking a name that no longer existed on the object, but because of how the multiprocessing backend handles dispatch, this came back as None rather than an AttributeError. The assertion that would have caught a None return was not there.

Two things had to both be true for this to slip through: the rename itself, and the absence of any CI check that runs the executor through its caller. Either one fixed and we probably catch this before release.

## Fix

- Restored the expected method name on the executor (or updated the call site, i need to double-check which direction we went here, TBD)
- Added an assertion at the call site so a None return raises immediately rather than propagating silently

## Impact

- No data lost. Affected runs return no output rows, so they can be identified and re-queued safely
- Scope limited to users running the multiprocessing backend with user functions in v0.1.17, which was live for less than a day
- Not sure how many users were actually affected, need to check if anyone else reported or if it was just the one report we got

## What needs to change

- [ ] Interface contract between the executor and its callers needs a regression test in CI. Right now there is nothing that would catch a method rename before release, and that is the actual gap here
- [ ] The PR that introduced the rename should have included a check that bulk-llm-inference still works against it. I want to make sure we have a policy or at least a checklist note for internal renames on public-ish interfaces

I'm not the right person to spec out the CI pipeline change itself, i'd need to pull in whoever owns the pipeline config to make sure it's wired up correctly. Happy to write the actual test cases.

## Open questions

- Which direction did the fix go, rename restored on executor side or call site updated? The PR should clarify but i dont have it in front of me
- Was it only the one user affected or did others hit this silently and not report? Worth a check before we close this out
