---
title: "Postmortem: v0.1.18.post4 hotfix"
author: emil
created_at: 2025-02-10T09:56:00+00:00
---

# Postmortem: v0.1.18.post4 hotfix

v0.1.18 shipped with a cloudpickle-based serialization approach in online-request-processing that failed silently under real workload. The fix was a revert, not a repair. v0.1.18.post4 went out over the weekend.

## Impact

The failure mode was a silent drop: rows that hit the serialization error were discarded rather than raising. That means any run that touched the affected code path between v0.1.18 shipping and post4 going out should be treated as suspect. I don't have a count of affected rows, and I don't know yet who would have that number. If your team ran anything against v0.1.18 before the hotfix, lets circle back on whether you need to rerun.

No crash, no alert, no loud failure. The problem was found by observing results, not by the system telling us something was wrong.

## Timeline

```
v0.1.18 ships
  |
Serialization failures observed in online-request-processing during a run
  |
Root cause identified: cloudpickle failing on import-path-sensitive class
  |
Decision to revert rather than fix under time pressure
  |
v0.1.18.post4 issued (4 commits: revert, test update, version bump, changelog)
```

The whole thing ran over a weekend. I don't have exact timestamps for each step.

## Root cause

cloudpickle resolves class identity by import path at serialization time. The custom class in question was being imported differently at the producer and consumer sides of the process boundary, so cloudpickle could not deserialize on the consumer end.

That failure was then caught too broadly in the request handling layer. Instead of propagating up or logging visibly, the row was dropped and processing continued. The broad catch is what turned a serialization bug into a silent data loss bug. Those are two separate problems, and only one of them is fixed in post4.

The pickler approach worked in testing because the import path was consistent in the test environment. Under real workload it wasn't, and we didn't have a test that crossed an actual process boundary.

## What we changed

Reverted to passing raw dicts across the process boundary. This is what the code did before the v0.1.18 pickler work, and it's safe. The trade-off is that the caller is now responsible for converting back to the expected type, which is a bit of extra burden but not a correctness risk.

The revert is four commits: the revert itself, a test update, version bump, changelog.

## What went well

Once the root cause was identified, the path forward was clear and the revert was straightforward. The decision to revert rather than attempt a repair under time pressure was the right call.

## Action items

- [ ] Tighten the broad exception catch in the request handling layer. This is the thing that turned a serialization error into a silent drop. Not in post4, needs its own fix.
- [ ] Address the silent drop behavior regardless of which serialization path we land on. Even if the catch is tightened, we should be explicit about what happens to a row that cannot be processed.
- [ ] Anyone who ran against v0.1.18 before the hotfix should audit their results. Need to figure out who that is.
- [ ] If we want to revisit cloudpickle-based serialization later: pin class identity by fully-qualified name, and add a test that explicitly crosses a process boundary. No decision made yet on whether to do this at all.

## Open questions

- How many rows were dropped across all runs on v0.1.18? Whoever owns the run output dashboard would know, but I haven't pulled that yet.
- Is there a way to detect the affected runs after the fact, or do they need to be fully rerun?
