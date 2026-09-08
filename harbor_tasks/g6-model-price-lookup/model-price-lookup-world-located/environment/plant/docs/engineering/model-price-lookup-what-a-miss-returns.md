---
title: "model price lookup: what a miss returns"
author: dermot
created_at: 2025-07-02T09:30:00+00:00
---

## why this is written down

on monday the weekly cost report came out with 0.00 against two models. nothing in the reporting code had changed that week, and the arithmetic was fine — the problem was upstream, in the price table. the rows for those two models were present but carried no input number, and `lookup_price` was treating that as a different situation from a model it had never seen.

konrad's note pins down what the lookup hands back for a model it does not know. this page is the same contract written from the caller's side, plus the null-priced rows, so that we stop working it out from first principles every time a number looks wrong.

nothing here is new behaviour except where marked. it is mostly a record of what the lookup already does and what callers are expected to do about it.

## the contract as it stands

`lookup_price(model_id)` has exactly two outcomes.

- a hit returns a `ModelPrice` with `input_per_1k` and `output_per_1k` both populated and both non-null
- a miss returns `None`

things it does not do, and these are the ones people assume:

- it does not raise. a model we have never heard of is an ordinary condition, not an error
- it does not return a zeroed `ModelPrice`. zero is a real price and we have at least one row that legitimately holds it, so zero and unknown cannot share a representation
- it does not fall back to a sibling model or a family default. if the exact `model_id` is not priced, that is a miss

lookup is by exact `model_id` string. no normalisation, no prefix matching. that said, the provider prefixes are inconsistent enough across our sources that if i had to guess we will end up wanting some normalisation layer eventually — it would sit above the lookup, not inside it.

## rows that exist but carry no input number

a handful of rows in the table have a name and an output number and nothing at all for input. they come in that way from the upstream source; it is not something we introduced. these were the two models on monday's report.

a row in the table with no input number is no more use to us than no row at all, so it comes back exactly the way a missing key does — `lookup_price` returns `None`, and the caller takes the same branch it would take for a model that was never listed. same for a row missing the output number. there is no third state and callers do not get to inspect the partial row.

the check is on the loaded row, not on the file, so a row that goes null on a table refresh starts returning `None` on the next lookup without anyone touching code. the row stays in the table — we are not deleting it, we are just not reporting it as priced.

## what callers do with a miss

the rule is that a miss propagates. it does not get filled in with a plausible number somewhere in the middle of the stack.

- **cost reporting** — a miss renders as `unknown`, not `0.00`, and the run summary carries a count of unpriced models. this is the change that would have made monday visible on the day it happened rather than a week later
- **budget checks** — a miss is not treated as "within budget". the check reports that it could not evaluate, and the caller decides
- **anything summing across models** — an unpriced model is excluded from the total and named in the exclusion list. a total that silently drops rows is worse than no total

not entirely sure the budget check behaviour is right for every caller, but it is what it does today and i would rather that be written down than discovered.

## open items

- the null rows themselves are an upstream data problem. we can ask for them to be filled or we can keep absorbing them, and nobody owns that question yet
- no alerting on the unpriced count. it goes in the summary and that is all it does, so it still relies on someone reading the summary
- table refresh cadence is not documented anywhere i can find

none of these are v0.1.26 blockers. flagging them so they are at least in one place.
