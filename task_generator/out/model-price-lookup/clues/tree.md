# The tree

## g6.r1

### g6.r1.sc1 — A lookup that cannot produce both numbers must raise rather than return a price object with an empty field, and the raised error carries a reason drawn from a closed set of exactly three permitted strings.

*The leap nobody states:* If a half-filled price object is what caused the damage, and the only sanctioned failure channel is an error whose reason string is validated against a fixed list, then there is no other way out of the function.

- **dario** (2025-04-07, #pipeline): while we're on cost numbers - i lost an hour today to a nonetype in the cost sum, the price came back with the input side empty and we summed it anyway
- **dermot** (2025-04-21, page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md): if the table has no number for it i would rather the lookup raise UnpricedModelError at the call site than hand back a price with a hole in it.
- **konrad** (2025-06-02, thread:<178771259923.2429685.8918976446565480852@world.local>): One note on PR 681: I passed reason='no_pricing_data' and the constructor threw ValueError straight back at me - it checks the arg against UnpricedModelError.REASONS, which is those three strings and nothing else.

### g6.r1.sc2 — When more than one of provider, model and window is bad at once, the reason names the outermost one: an unregistered provider wins over a missing model, and a missing model wins over an unrecognised window.

*The leap nobody states:* Two pasted calls that differ only in the provider being real, returning two different reasons, means the checks are ordered and stop at the first failure.

- **emil** (2025-03-14, #engineering): Pasting what i got back: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h") gives unknown_provider, not a word about the model or the window - yup, right call for an unregistered provider.
- **gideon** (2025-05-13, page:engineering/price-lookup-errors-what-each-bad-argument-actually-raises.md): so basically same args but with a provider we do have registered and it comes back unknown_model instead, so the junk window never even gets looked at.
- **nils** (2025-03-21, #pipeline): context on that fix - i burned twenty minutes chasing a window typo when the real problem was that I had misspelled the provider. the error should name the first thing that's wrong.

### g6.r1.sc3 — A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.

*The leap nobody states:* Both cases are situations where a lookup currently 'succeeds' with bad data, so each has to be reclassified as one of the failures instead of being papered over.

- **nikolai** (2025-06-18, thread:new|g6.r1.l7): right that gemini row does exist in litellm.model_cost but input_cost_per_token on it is null and we priced a whole week of runs at zero off the back of it
- **dermot** (2025-07-02, page:engineering/model-price-lookup-what-a-miss-returns.md): a row in the pricing table with a null input price is no more use to us than no row at all, it should come back exactly the way a missing key does.
- **nils** (2025-06-26, #pipeline): while you're in there - there's no 24h row for that model so the lookup fell through to the star entry, and my batch report came out with online prices again
- **emil** (2025-06-25, #code-review): let me think through that - if a model's map has no row for the window you asked for thats unknown_window, we shouldnt be quietly borrowing the "*" tier.

### g6.r1.sc4 — Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.

*The leap nobody states:* If a run must not die over an accounting number, and the viewer must not show a fabricated zero, then the failure has to be caught at every call site and recorded rather than rendered.

- **gideon** (2025-03-24, #engineering): Ya, thats not theoretical - tracker took the whole online run down last night 4k requests in, on a model litellm has never heard of. Cost display, not the work.
- **konrad** (2025-05-27, page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md): Related: sometimes the price cant be resolved at all. Every cost() method should be catching that and handing back 0.0 rather than ending a run over an accounting number.
- **dario** (2025-04-21, thread:<178770212973.2301745.4705747507669611471@world.local>): on WS-054 — for the trackers input_cost_per_million and output_cost_per_million just stay empty and the reason sits on price_unavailable_reason, so we can show why rather than a number.
- **dermot** (2025-05-01, #code-review): that said, the pricing gaps part of that page: input_cost_per_million comes through None and the viewer renders it $0.00, which readers read as free. that zero shouldnt be shown.

## g6.r2

### g6.r2.g6r2-s1 — The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

*The leap nobody states:* If two layers each take a cut off the same price the answer depends on which of them ran, so the factor has to have a single owner that everything else calls.

- **gideon** (2025-03-19, #pipeline): The batch estimate came in at a quarter of the invoice again, so basically two separate layers each knocking half off the same price. Nobody's disputing that part at this point.
- **dario** (2025-04-15, #pipeline): while we're on the provider cost paths, i left the same note on the azure cost() override again: why is this dividing by two here when batch_multiplier already ran
- **emil** (2025-05-02, #code-review): spent the morning working out which of the two subtracions was the real one. only one place in the tree gets to touch the price for batch, we agreed that much.
- **dermot** (2025-04-14, page:releases/v0-1-22-release-notes.md): on the 50% line: resolve_model_price has no separate batch row, batch=True scales what batch=False returned. whichever number batch_multiplier() hands the processors, it should be reading that same one.

### g6.r2.g6r2-s2 — The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.

*The leap nobody states:* A table that already quotes the batch tier has had the discount taken once; taking it again is not a discount, it is an error, so the discount belongs only to list prices.

- **nils** (2025-03-26, #pipeline): let me think - klusterai's published per-million is already their batch rate, and we went and took another 50% off it in the estimate.
- **nikolai** (2025-06-18, thread:new|g6.r2.g6r2-s2-l2): same story with inference.net the number on their pricing page is already what a batch job costs so theres nothing left to take off it
- **dario** (2025-04-22, page:meetings/weekly-notes-week-of-apr-14.md): re the batch vs online cost question — i had an online run showing batch pricing in the tracker all afternoon. outside batch mode the list price comes through untouched, thats settled at least.
- **emil** (2025-04-14, thread:<178769930038.2250839.2605881431154859866@world.local>): on your cost question — resolve_model_price with provider=klusterai and batch=True came back at half the table rate, and anything we read out of those provider tables should come back exactly as listed.

### g6.r2.g6r2-s3 — A price the user supplied themselves is never discounted: `batch_multiplier()` returns 1.0 whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount, and which processors are exempt is decided by a class-level flag and by which source answered the lookup.

*The leap nobody states:* A number a user typed in is the number they were quoted, not a list price we are entitled to mark down; and the exemption has to be a property of the processor rather than a string check buried in the arithmetic.

- **konrad** (2025-04-03, #cookbooks): @Emil worth one, yes. A cookbook user put their negotiated input cost straight in the config and the batch run reported half of what they typed.
- **nikolai** (2025-06-10, page:engineering/cost-estimates-in-batch-mode-where-the-price-numbers-come-from.md): if the price per million came from the user then thats already the number they pay so batch mode shouldnt be knocking anything off it either
- **dermot** (2025-04-08, thread:new|g6.r2.g6r2-s3-l3): reading the cost path in 565 — we're picking who gets the batch discount with an if-chain on provider names inside batch_multiplier, that belongs on the class as a flag instead.

### g6.r2.g6r2-s4 — The factor is a fixed one half, observable as `batch_multiplier()` on the base and Azure processors in batch mode and 1.0 out of it, 1.0 on klusterai and inference.net even in batch mode, and as `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` matching its `batch=False` value while a litellm-sourced model's halves.

*The leap nobody states:* If both the processor method and the resolver are meant to use one factor, the way you show they do is to compare the two prices they hand back for the same model.

- **gideon** (2025-04-03, #pipeline): so basically batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure, tbh one number for both. outside batch mode both hand back 1.0.
- **emil** (2025-06-25, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md): On pricing: azure's batch_multiplier() keeps drifting from the base processor's; we agreed identical in and out of batch mode, with cost() just scaling the resolved price by self.batch_multiplier().
- **nils** (2025-03-25, #pipeline): on the adding side, my batch test pins resolve_model_price(m, provider="klusterai", completion_window="*", batch=True).input_cost_per_million at 4.0, same float as batch=False. same test, source == "litellm" halves input_cost_per_million and output_cost_per_million both.

### herrings — believed at the time, reversed later

- **dario** (2025-01-27): went and looked - settled: the base cost processor halves every source, and klusterai/inference.net multiply their cost() by 2 to cancel it, their tables are already batch-tier
- **konrad** (2025-01-27): @Dario discount stays in the base, providers whose table already lists batch prices cancel it with a x2 in their own cost() override, klusterai and inference.net both do this

