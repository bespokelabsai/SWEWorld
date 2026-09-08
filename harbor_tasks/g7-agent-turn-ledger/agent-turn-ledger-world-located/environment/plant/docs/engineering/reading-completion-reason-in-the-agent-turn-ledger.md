---
title: "Reading completion_reason in the agent turn ledger"
author: nils
created_at: 2025-07-02T09:30:00+00:00
---

## Why this page exists

The overnight run on Jun 30 stopped early. It hit the stop marker partway through the queue and shut down cleanly, which is the behaviour we want. What we got in the ledger afterwards was a row saying the run had exhausted its budget.

So for most of Tuesday morning nobody could answer the only question that mattered, which was whether that run had been cut off by us or had finished on its own terms. The turn counts looked plausible either way. We ended up reading the raw executor log to settle it, which is not a thing anyone should have to do to interpret a ledger row.

The underlying bug is fixed (see the last section). But the reason it went unnoticed for as long as it did is that we have never written down what the ledger fields are supposed to mean, and that's worth documenting. This page is that.

## What one ledger row contains

One row per run, written once at teardown. The fields people actually read:

- `run_id` - stable across retries, so a retried run appends rather than overwrites
- `turns_completed` - turns that produced a full agent message and were accounted for. partial turns are not counted here
- `turns_budgeted` - the ceiling the run was started with, not the ceiling it used
- `completion_reason` - why the loop stopped. see below
- `stopped_at` - wall clock at teardown

Note that `turns_completed` and `turns_budgeted` being equal does not by itself tell you the run ran to exhaustion, and it never has. A run can be budgeted 40 turns, finish its work on turn 40, and stop for an entirely different reason. The two fields describe the shape of the run. The reason field describes the ending.

## The values completion_reason can take

There are four, and they are mutually exclusive:

- `budget_exhausted` - the loop consumed its last budgeted turn and had more work queued.
- `agent_signal` - the agent emitted the stop marker and the loop honoured it.
- `error` - teardown after an unhandled failure in the executor.
- `cancelled` - external signal, operator or scheduler.

The distinction between the first two is the one that keeps getting muddled, so let me think through that carefully here. A run that ended on the marker did not run out of anything. The budget was sufficient, and some of it was very likely left over. Which means `completion_reason` on the ledger reads `agent_signal` for those runs, never budget. `budget_exhausted` is reserved for the case where the loop wanted another turn and did not have one available to take, and if there was queued work remaining at teardown that is the signal that distinguishes them.

I think the temptation, when writing the teardown path, is to treat "stopped before the budget was used up" as a budget outcome because the budget is right there in scope. It is not. Maybe a clearer way to hold it is that the budget fields say how much room the run had, and only `budget_exhausted` says the run ran out of it.

## Triaging a run that ended earlier than expected

In order, and you should not need to leave the ledger for the first three:

1. Read `completion_reason`. If it is `agent_signal` the run finished on its own and there is nothing to investigate unless the output is wrong.
2. If it is `budget_exhausted`, compare `turns_completed` against `turns_budgeted`. They should be equal or within one. If `turns_completed` is well under budget, the reason field is lying to you and that is itself the bug to file.
3. If it is `error`, the executor log is the right next stop, and the ledger has done its job by telling you so.
4. Only then go to the raw log.

Step 2 is the check that would have caught Jun 30 in about thirty seconds. Fair enough that nobody ran it, since it was not written down anywhere until now.

## Follow-ups

- The teardown path now sets the reason from the loop exit branch rather than inferring it, so the marker case can no longer fall through to the budget case. Merged Jul 1.
- Rows written before Jul 1 are not backfilled and I do not currently plan to backfill them. If you are reading a June run and the reason says budget, treat it as unreliable and check the turn counts.
- Open question for whoever picks up the ledger next: do we want a fifth value for the case where the marker is emitted *and* the budget is exhausted on the same turn, or do we want to keep four values and declare a precedence order? I lean toward precedence, with `agent_signal` winning, since the agent asked to stop and we honoured it. But that is not settled and I would rather it were decided than assumed.
