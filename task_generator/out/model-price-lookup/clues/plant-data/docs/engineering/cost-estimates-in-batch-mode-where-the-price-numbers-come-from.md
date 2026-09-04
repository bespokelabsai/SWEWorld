---
title: "Cost estimates in batch mode: where the price numbers come from"
author: nikolai
created_at: 2025-06-10T09:30:00+00:00
---

## why this page exists

2025-06-10

A user reported their batch cost estimate came back at exactly half the per million price they had configured themselves and asked if that was a bug

I went looking for something to point them at and there is nothing written down anywhere about how a price gets picked so this is that page

This is not a spec it is what the code does today on v0 1 25 - if we change the behaviour later this page needs to change with it

## the two paths a price can come from

There are exactly two ways a per million price ends up in an estimate

- **lookup path** - we hand the model id to the pricing map and get back `input_cost_per_million` and `output_cost_per_million` - these are published list prices for the hosted providers
- **caller supplied path** - the user passes the prices in directly - usualy because the model is self hosted or the map is stale for a new model or they have negotiated pricing that is not public

The lookup only runs when nothing was supplied - caller supplied always wins and we never merge the two or fall back from one to the other

If the lookup misses and nothing was supplied there is no estimate at all - we skip it rather than guess - that part is solid enough and i'd leave it alone

## the batch discount

Batch mode applies a 0 5 multiplier to prices that came out of the lookup path

The reason is that the map holds the synchronous list price and openai and anthropic both bill batch work at half of that so halving the looked up number gets the estimate close to what the invoice actualy says

The multiplier does not apply to caller supplied prices - if the number came from the user it is already the number they pay so nothing should come off it in batch mode either - we have no way of knowing whether they typed in a list price or their negotiated batch rate and halving it would be us inventing a discount on top of one they may have already accounted for

So the 0 5 belongs to the lookup path not to batch mode generally - that is the distinction the user in the report was running into

## checking a number that looks wrong

In order

1. confirm which path the price came from - was anything passed in by the caller or did we look it up
2. if it was looked up check the raw map entry for that model id - compare against the providers public page since the map goes stale
3. if it was looked up and we are in batch mode expect half the list price - that is working as intended not a bug
4. if it was caller supplied expect the number back unchanged in both sync and batch
5. only then look at token counts - most of the reports that come in as pricing bugs are actualy estimated token counts being off not the per million rate

## open / rough edges

- the 0 5 is hardcoded - it is right for the two big providers right now but it is not a universal batch rate and we will hit a provider where it is wrong
- nothing in the output says which path a price came from - if the estimate printed that it would have answered the users question without anyone reading the code - i mean this is probably the cheapest fix on the list
- no idea off the top of my head what we do for a model that is in the map with only an input price and no output price - gotta think through that one and write it down here when i know
