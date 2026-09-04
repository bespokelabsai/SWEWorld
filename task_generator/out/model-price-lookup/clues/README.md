# Clues for g6 — Unified model price resolution

33 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Consolidate the scattered, inconsistent model-price lookups into one canonical path.

Today that logic is spread across `src/bespokelabs/curator/cost.py` — which mixes external-table and litellm-table logic ad hoc across `external_model_cost()` and four separate `cost()` methods — and across the batch/online status trackers.

### 1. Add a frozen dataclass `ModelPrice`

With these fields:

- `model: str`
- `provider: str | None`
- `completion_window: str`
- `input_cost_per_million: float`
- `output_cost_per_million: float`
- `source: str` ("litellm" or "external")
- `batch: bool`
- `output_price_inferred: bool`
- `max_tokens: int | None`

Plus `input_cost_per_token`/`output_cost_per_token` properties (`round(value, 9)` for per-million figures, `round(per_million/1e6, 15)` for per-token).

### 2. Add `UnpricedModelError(LookupError)`

- A class-level `REASONS` frozenset naming the permitted reason strings.
- A keyword-only `__init__(*, model, provider, completion_window, reason)` that raises `ValueError` for an unrecognized `reason`.
- Otherwise it produces the message `f"{reason}: model={model!r} provider={provider!r} completion_window={completion_window!r}"`.

### 3. Add `resolve_model_price(model, *, provider=None, completion_window=None, batch=False) -> ModelPrice`

The single function that consults `_DEFAULT_COST_MAP`'s external provider tables and `litellm.model_cost`. It:

- Raises `UnpricedModelError` instead of ever returning a `None`-valued price.
- Applies a batch-rate discount to the returned per-million prices where the pricing data calls for it when `batch=True`.
- When a table entry has no explicit output price, copies the input price into the output price and sets `output_price_inferred=True`.

### 4. Add `register_price_with_litellm(price: ModelPrice) -> dict`

- Writes `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` into `litellm.model_cost` via `litellm.register_model`.
- Raises `ValueError` if `price.batch` is `True`.
- Returns that same four-key `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` dict — the entry it just wrote, not `{price.model: {...}}`.

### 5. Add `format_cost_strings(price: ModelPrice | None, *, rich: bool) -> tuple[str, str]`

The sole place display strings like `"$0.045"` (or `"[red]$0.045[/red]"` when `rich`) are built. It:

- Appends `"*"` to the output string when `output_price_inferred` is true.
- Returns `("N/A", "N/A")` (or the `[dim]`-wrapped equivalent) for `price is None`.

### 6. Rewrite `external_model_cost(model, completion_window="*", provider="default") -> dict[str, float]`

As a thin shim over `resolve_model_price(..., batch=False)`.

### 7. Delete `_get_litellm_cost_map`

### 8. Give `BatchStatusTracker`/`OnlineStatusTracker` two new fields and one new method

New fields:

- `price_unavailable_reason: Optional[str]`
- `output_price_inferred: bool`

New method `refresh_model_price(*, price_model: str | None = None) -> Optional[str]`, called from `model_post_init`/`__post_init__` and from the batch request processors' `set_model_cost()`. It:

- Re-resolves and assigns the two per-million prices, `output_price_inferred`, and `input_cost_str`/`output_cost_str` (via `format_cost_strings`).
- Sets `price_unavailable_reason` to `None` on success or to `err.reason` on `UnpricedModelError`.
- Never raises.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-27 | #pipeline | dario | went and looked - settled: the base cost processor halves every source, and klusterai/inference.net multiply their cost() by 2 to cancel it, their tables are already batch-tier | *herring* |
| 2025-01-27 | #engineering | konrad | @Dario discount stays in the base, providers whose table already lists batch prices cancel it with a x2 in their own cost() override, klusterai and inference.net both do this | *herring* |
| 2025-03-14 | #engineering *(new)* | emil | Pasting what i got back: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h") gives unknown_provider, not a word about the model or the window - yup, right call for an unregistered provider. | `exclusions_or_crossover`, `observability` |
| 2025-03-19 | #pipeline | gideon | The batch estimate came in at a quarter of the invoice again, so basically two separate layers each knocking half off the same price. Nobody's disputing that part at this point. | `rule` |
| 2025-03-21 | #pipeline | nils | context on that fix - i burned twenty minutes chasing a window typo when the real problem was that I had misspelled the provider. the error should name the first thing that's wrong. | `exclusions_or_crossover` |
| 2025-03-24 | #engineering | gideon | Ya, thats not theoretical - tracker took the whole online run down last night 4k requests in, on a model litellm has never heard of. Cost display, not the work. | `observability` |
| 2025-03-25 | #pipeline | nils | on the adding side, my batch test pins resolve_model_price(m, provider="klusterai", completion_window="*", batch=True).input_cost_per_million at 4.0, same float as batch=False. same test, source == "litellm" halves input_cost_per_million and output_cost_per_million both. | `observability`, `scope` |
| 2025-03-26 | #pipeline *(new)* | nils | let me think - klusterai's published per-million is already their batch rate, and we went and took another 50% off it in the estimate. | `scope` |
| 2025-04-03 | #cookbooks | konrad | @Emil worth one, yes. A cookbook user put their negotiated input cost straight in the config and the batch run reported half of what they typed. | `exclusions_or_crossover` |
| 2025-04-03 | #pipeline *(new)* | gideon | so basically batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure, tbh one number for both. outside batch mode both hand back 1.0. | `observability`, `rule` |
| 2025-04-07 | #pipeline | dario | while we're on cost numbers - i lost an hour today to a nonetype in the cost sum, the price came back with the input side empty and we summed it anyway | `rule` |
| 2025-04-07 | #engineering | nikolai | for the record the klusterai row in pr 622 is 4.0 per million input straight off their pricing page. no window split on their table at all it just sits under "*" | `observability` |
| 2025-04-08 | thread:new|g6.r2.g6r2-s3-l3 *(new)* | dermot | reading the cost path in 565 — we're picking who gets the batch discount with an if-chain on provider names inside batch_multiplier, that belongs on the class as a flag instead. | `exclusions_or_crossover`, `rule` |
| 2025-04-14 | page:releases/v0-1-22-release-notes.md | dermot | on the 50% line: resolve_model_price has no separate batch row, batch=True scales what batch=False returned. whichever number batch_multiplier() hands the processors, it should be reading that same one. | `rule`, `observability` |
| 2025-04-14 | thread:<178769930038.2250839.2605881431154859866@world.local> | emil | on your cost question — resolve_model_price with provider=klusterai and batch=True came back at half the table rate, and anything we read out of those provider tables should come back exactly as listed. | `scope`, `exclusions_or_crossover` |
| 2025-04-14 | #pipeline | dario | batch stats: two layers each halving is why estimates came in at a quarter of the invoice. batch_multiplier() is the only place that factor lives now, 1.0 on klusterai and inference.net, no cost() override. | `rule`, `scope` |
| 2025-04-15 | #pipeline | dario | while we're on the provider cost paths, i left the same note on the azure cost() override again: why is this dividing by two here when batch_multiplier already ran | `rule` |
| 2025-04-21 | page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md | dermot | if the table has no number for it i would rather the lookup raise UnpricedModelError at the call site than hand back a price with a hole in it. | `rule` |
| 2025-04-21 | thread:<178770212973.2301745.4705747507669611471@world.local> | dario | on WS-054 — for the trackers input_cost_per_million and output_cost_per_million just stay empty and the reason sits on price_unavailable_reason, so we can show why rather than a number. | `observability` |
| 2025-04-22 | page:meetings/weekly-notes-week-of-apr-14.md | dario | re the batch vs online cost question — i had an online run showing batch pricing in the tracker all afternoon. outside batch mode the list price comes through untouched, thats settled at least. | `scope` |
| 2025-05-01 | #code-review | dermot | that said, the pricing gaps part of that page: input_cost_per_million comes through None and the viewer renders it $0.00, which readers read as free. that zero shouldnt be shown. | `observability` |
| 2025-05-02 | #code-review | emil | spent the morning working out which of the two subtracions was the real one. only one place in the tree gets to touch the price for batch, we agreed that much. | `rule` |
| 2025-05-13 | page:engineering/price-lookup-errors-what-each-bad-argument-actually-raises.md *(new)* | gideon | so basically same args but with a provider we do have registered and it comes back unknown_model instead, so the junk window never even gets looked at. | `exclusions_or_crossover`, `observability` |
| 2025-05-27 | page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md | konrad | Related: sometimes the price cant be resolved at all. Every cost() method should be catching that and handing back 0.0 rather than ending a run over an accounting number. | `observability` |
| 2025-06-02 | thread:<178771259923.2429685.8918976446565480852@world.local> | konrad | One note on PR 681: I passed reason='no_pricing_data' and the constructor threw ValueError straight back at me - it checks the arg against UnpricedModelError.REASONS, which is those three strings and nothing else. | `rule` |
| 2025-06-03 | #engineering | konrad | Also scratch my reviewr note about the x2 in the provider's cost() override, those overrides are deleted. Where a table already lists batch prices, batch_multiplier() returns 1.0 and resolve_model_price leaves the external-sourced price as listed. | `rule`, `scope`, `exclusions_or_crossover` |
| 2025-06-10 | page:engineering/cost-estimates-in-batch-mode-where-the-price-numbers-come-from.md *(new)* | nikolai | if the price per million came from the user then thats already the number they pay so batch mode shouldnt be knocking anything off it either | `exclusions_or_crossover` |
| 2025-06-18 | thread:new|g6.r1.l7 *(new)* | nikolai | right that gemini row does exist in litellm.model_cost but input_cost_per_token on it is null and we priced a whole week of runs at zero off the back of it | `exclusions_or_crossover` |
| 2025-06-18 | thread:new|g6.r2.g6r2-s2-l2 *(new)* | nikolai | same story with inference.net the number on their pricing page is already what a batch job costs so theres nothing left to take off it | `scope` |
| 2025-06-25 | #code-review *(new)* | emil | let me think through that - if a model's map has no row for the window you asked for thats unknown_window, we shouldnt be quietly borrowing the "*" tier. | `exclusions_or_crossover`, `observability` |
| 2025-06-25 | page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | emil | On pricing: azure's batch_multiplier() keeps drifting from the base processor's; we agreed identical in and out of batch mode, with cost() just scaling the resolved price by self.batch_multiplier(). | `observability` |
| 2025-06-26 | #pipeline *(new)* | nils | while you're in there - there's no 24h row for that model so the lookup fell through to the star entry, and my batch report came out with online prices again | `exclusions_or_crossover` |
| 2025-07-02 | page:engineering/model-price-lookup-what-a-miss-returns.md *(new)* | dermot | a row in the pricing table with a null input price is no more use to us than no row at all, it should come back exactly the way a missing key does. | `exclusions_or_crossover` |

## g6.r1

**The hidden requirement:**

- **rule** — `resolve_model_price` never returns a `ModelPrice` carrying a `None` price: every failure raises `UnpricedModelError`, and the `reason` it carries is exactly one of the three strings `unknown_provider`, `unknown_model`, `unknown_window`.
- **exclusions_or_crossover** — An unregistered provider is `unknown_provider` even when the model is also absent and the window is also unrecognised, and a missing model key is `unknown_model` even when the window is also unrecognised. A model present in `litellm.model_cost` but carrying a missing or `None` input price is `unknown_model`, and a window that is absent from a model's price map is `unknown_window` rather than a fallback to the wildcard tier.
- **observability** — `resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")` raises with `reason == "unknown_provider"`; the same call with a registered provider raises with `reason == "unknown_model"`; a model that provider does list, asked for an unlisted window, raises with `reason == "unknown_window"`. Every `cost()` method and both trackers catch `UnpricedModelError` and degrade — `cost()` to `0.0`, a tracker to `None` prices and a recorded reason.

**What a reader has to infer along the way:**

- *A lookup that cannot produce both numbers must raise rather than return a price object with an empty field, and the raised error carries a reason drawn from a closed set of exactly three permitted strings.*
  - nobody says: If a half-filled price object is what caused the damage, and the only sanctioned failure channel is an error whose reason string is validated against a fixed list, then there is no other way out of the function.
- *When more than one of provider, model and window is bad at once, the reason names the outermost one: an unregistered provider wins over a missing model, and a missing model wins over an unrecognised window.*
  - nobody says: Two pasted calls that differ only in the provider being real, returning two different reasons, means the checks are ordered and stop at the first failure.
- *A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.*
  - nobody says: Both cases are situations where a lookup currently 'succeeds' with bad data, so each has to be reclassified as one of the failures instead of being papered over.
- *Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.*
  - nobody says: If a run must not die over an accounting number, and the viewer must not show a fabricated zero, then the failure has to be caught at every call site and recorded rather than rendered.

**Names the tests reach for that the ticket withholds:**

- said: `Every`, `unknown_model`, `unknown_provider`, `unknown_window`

> **2 of 21 graded assertions are not stated outright** — 2 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g6.r1.sc1 — A lookup that cannot produce both numbers must raise rather than return a price object with an empty field, and the raised error carries a reason drawn from a closed set of exactly three permitted strings.

*Nobody says:* If a half-filled price object is what caused the damage, and the only sanctioned failure channel is an error whose reason string is validated against a fixed list, then there is no other way out of the function.

*3 remarks — 2 reporting the problem, 1 settling the design.*

#### `g6.r1.l1` — rule

**dario**, 2025-04-07, #pipeline

> while we're on cost numbers - i lost an hour today to a nonetype in the cost sum, the price came back with the input side empty and we summed it anyway

*What a reader should take from it:* the team agrees a price object with a missing number gets into the arithmetic and breaks it

*Step it builds toward:* `g6.r1.sc1` — A lookup that cannot produce both numbers must raise rather than return a price object with an empty field, and the raised error carries a reason drawn from a closed set of exactly three permitted strings.

*Drafted as:* lost an hour to a nonetype in the cost sum today; the price came back with the input side empty and we summed it anyway.

*Why there:* That day is entirely a cost-path correctness argument: gideon's 10x resume bug, dario explicitly asking whether ws-050 closes or "we need a broader audit of the cost path first", and gideon admitting at 13:49 he has an observed symptom and no repro. Dario reporting his own hour lost to a nonetype in the cost sum — a price that came back with the input side empty and got summed anyway — lands as the second cost-path thing surfacing that day, distinct from the model-mismatch-on-resume one dario already ruled out of scope. Placing it after gideon's 13:49 keeps dario's 12:59 "no broader audit needed" call intact rather than pre-contradicting it, and it doesn't touch what should be returned instead, which is the arm elsewhere. Dario is the natural speaker: he owns cost accounting, is the one pressing on scope all day, and 2025-03-26's usage-extraction discussion is about missing token counts, not a price object with a missing number, so it isn't redundant with what he said there.

*Still leaves open:* What should happen instead of returning the empty-sided price, and what a caller would receive in its place.

*Goes into the real conversation in #pipeline on 2025-04-07, after 13:49 gideon:*

```
09:00  dermot: - *pr 614*: cancellation fixes are close, expect to flag it for review this morning
- gemini batch changes landed over the weekend and I want to confi
09:44  gideon: What exactly did the Gemini batch changes touch on the cost accounting side?
09:44  gideon: I want to cross-check something I saw with resume
09:44  gideon: Actually, on resume, does the cost counter pull the model from the current config or from whatever the job was originally submitted with?
09:44  gideon: I hit a case where it came out about 10x off
10:02  dermot: I'm around all day if it helps to have another set of eyes on this once it's clearer what the resume path is doing.
10:32  gideon: Appreciated, I'll ping you once I've got more to show.
10:52  dermot: did the job resume on a different model than it was originally submitted with?
11:39  emil: from what I know, the gemini batch fixes are finish reason parsing and cancellation edge cases, neither should touch cost accounting or retry paths. n
11:50  dario: that's the question I want us to actually call before end of day, to be honest
11:50  dario: if gideon's 10x case is a model-mismatch-on-resume thing and unrelated to what the batch fixes touched, does that close ws-050, or do we need a broade
12:18  dermot: not entirely sure I'd call ws-050 closed until we know gideon's case is actually isolated from the batch fix scope.
12:28  emil: not convinced gideon's case is in scope for ws-050, honestly.
12:28  gideon: Ya
12:55  gideon: it did. The cost counter prices everything at whatever model the current config says at resume time, but the responses come back from whatever the job
12:55  gideon: Someone is going to file an issue on that reported cost number and I have nothing good to say about it.
12:59  dario: - *ws-050*: gideon's case is confirmed as a resume path issue, the cost counter pricing off the current config model instead of the original submissio
12:59  dario: so I'd call ws-050 closed
13:09  gideon: I'll file the issue on the resume cost bug this afternoon so it doesn't get lost.
13:40  dario: when you file it, is there a clear repro or is it more of an observed symptom at this point?
13:49  emil: notes-2025-03-31 still isn't in my inbox - whoever owes that should probably get it out before the day closes
13:49  gideon: More observed symptom right now, I hit it once and saw the number, I don't have a minimal repro yet.   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

#### `g6.r1.l2` — rule

**dermot**, 2025-04-21, page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md

> if the table has no number for it i would rather the lookup raise UnpricedModelError at the call site than hand back a price with a hole in it.

*What a reader should take from it:* the team agrees the lookup should fail loudly instead of returning an incomplete price

*Step it builds toward:* `g6.r1.sc1` — A lookup that cannot produce both numbers must raise rather than return a price object with an empty field, and the raised error carries a reason drawn from a closed set of exactly three permitted strings.

*Drafted as:* if the table has no number for it i would rather the lookup blow up at the call site than hand back a price with a hole in it.

*Why there:* That page's out-of-scope section is the only place in this history where a per-model price lookup is actually live: the cost counter prices off the current config model instead of the submission-time model, giving a 10x offset. Emil scopes it out and says it's tracked separately, which leaves open what the lookup should do when the model it's asked about isn't in the table — dermot, who has been carrying the cost-reporting gaps (issue 293, unnormalized usage shapes), is the plausible person to leave the failure preference on record there, the same way the image-pinning notes settle on failing at create time. It doesn't say what the error carries or whether the failure vocabulary is closed, so the sibling remark still has work to do.

*Still leaves open:* What the blow-up has to carry with it, and whether the vocabulary of failures is open or fixed.

*Must appear literally:* `UnpricedModelError`

*Goes as a comment on the real page `engineering/ws-050-batch-mode-50-cost-async-batch-apis.md`, at: ## Out of scope: cost accounting offset on resumed jobs:*

```
# WS-050: Batch Mode (50%-Cost Async Batch APIs)

## Status

Closed.

## What this workstream covered

Sweep across providers to implement and stabilize async batch API support, specifically targeting the 50%-cost tier. Primary focus ended up being Gemini batch processing, which is where both bugs surfaced.

## Bugs fixed

### Finish reason parsing (PR 621)

Gemini batch responses were returning `None` for `finish_reason` on successful completions. Not a failure case, just a silent gap in the parsed response. Fixed in PR 621.

### Batch cancellation (PR 614)

Several edge-case bugs in the cancellation path. I dont have the full list of cases in front of me but the fix is in PR 614 and the sweep confirmed behavior looked correct after.

## Out of scope: cost accounting offset on resumed jobs

During the sweep we identified a 10x cost offset on resumed jobs. The cause is that the cost counter prices off the current config model rather than the model that was set at the time of the original submission. So if the config changes between submission and resume, you get a wrong number, and depending on which direction the price moved it can be badly wrong.

This is confirmed out of scope f
```

#### `g6.r1.l3` — rule

**konrad**, 2025-06-02, thread:<178771259923.2429685.8918976446565480852@world.local>

> One note on PR 681: I passed reason='no_pricing_data' and the constructor threw ValueError straight back at me - it checks the arg against UnpricedModelError.REASONS, which is those three strings and nothing else.

*What a reader should take from it:* the team agrees the reason vocabulary is closed at three values and call sites cannot invent new ones

*Step it builds toward:* `g6.r1.sc1` — A lookup that cannot produce both numbers must raise rather than return a price object with an empty field, and the raised error carries a reason drawn from a closed set of exactly three permitted strings.

*Drafted as:* Tried passing reason='no_pricing_data' and the constructor threw ValueError straight back at me. Three allowed strings apparently, and that isn't one of them.

*Why there:* The May 26 recap is the one room where the pricing-lookup work is already live and owned by konrad himself — he lists "PR 681: If the model is not known, let the cost be None. (me)" as in flight. A one-line aside from the PR's own author about what the constructor accepts for `reason` lands as ordinary status color on his own update, and it settles the closed-vocabulary point without naming the three strings. Nothing earlier in the thread has made this point, and the other candidate mails (Mar/Apr) predate PR 681 entirely, so the remark would arrive from nowhere there.

*Still leaves open:* Which three strings those are, and what each of them means.

*Must appear literally:* `PR 681`, `UnpricedModelError.REASONS`, `ValueError`, `reason='no_pricing_data'`

*Goes as a reply into the real thread "Week of May 26 recap: v0.1.25 shipped":*

```
v0.1.25 is out. 359 changes merged to date across 24 releases.

Still in flight heading into this week:
- PR 653: Shreyas/finetuning client (Nikolai)
- PR 663: fix error when torch isn't installed (Nikolai)
- PR 675: add default app id parameter for curator llm (Nolan)
- PR 681: If the model is not known, let the cost be None. (me)

Next up is v0.1.26, after which we move to maintenance mode. I put the plan for that up on the wiki this morning (Winding down to maintenance mode after v0.1.26) if anyone wants the details on what the dormancy era looks like.

One thing I want to confirm before we cut over: is the download plumbing in the viewer surface actually clean and testable? I am not entirely sure where things stand there. Dario, Gideon, can either of you say whether that path is in good shape or whether there are gaps we should know about before we go quiet?
```

> **Problems:** longer than one remark

### g6.r1.sc2 — When more than one of provider, model and window is bad at once, the reason names the outermost one: an unregistered provider wins over a missing model, and a missing model wins over an unrecognised window.

*Nobody says:* Two pasted calls that differ only in the provider being real, returning two different reasons, means the checks are ordered and stop at the first failure.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g6.r1.l4` — exclusions_or_crossover, observability

**emil**, 2025-03-14, #engineering

> Pasting what i got back: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h") gives unknown_provider, not a word about the model or the window - yup, right call for an unregistered provider.

*What a reader should take from it:* the team agrees an unregistered provider names the failure even when the model and window are also bad

*Step it builds toward:* `g6.r1.sc2` — When more than one of provider, model and window is bad at once, the reason names the outermost one: an unregistered provider wins over a missing model, and a missing model wins over an unrecognised window.

*Drafted as:* Pasting what i got back: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h") gives unknown_provider, not a word about the model or the window.

*Why there:* None of the listed rooms is anywhere near model price lookup. 2025-03-14 is about schema_check validating response_format at construction; 2025-04-16 is cost *streaming* skew in the projected-remaining readout; 2025-04-21 touches unvalidated `backend_params` keys but the question there is whether the provider rejects or ignores them, not the precedence of local lookup errors. The code-review days (03-14 aside) are pure PR-queue traffic — gemini serialization, GCS upload, PR 619's merge state, v0.1.26 gating — and a pasted probe of `resolve_model_price` would change the subject and draw no reply. What's missing is the conversation where someone actually pins down error precedence in the price lookup: it belongs beside Nikolai's cost accounting work (WS-054), a couple of days after the 04-21 sync, with Emil and Dario running probes because the tests need to know which check fires first.

*Still leaves open:* What comes back when the provider is one we do register, so whether provider is genuinely checked first or is just the only check.

*Must appear literally:* `resolve_model_price`, `no-such-model`, `not-a-provider`, `96h`, `unknown_provider`

*A new conversation in #engineering on 2025-03-14:*

```
13:11  dario: was poking at the price lookup with deliberately bad inputs over lunch, wanted to see which complaint falls out
13:12  dario: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")
13:14  konrad: and? what comes back
13:15  dario: pasting what i got back: unknown_provider. thats the whole of it
13:16  emil: and nothing about the model? or the window - both of those are junk in that call too
13:18  dario: nope. not a word about either one, just the provider
13:19  emil: yup, right call for an unregistered provider. nothing on the code side does that today though, someone still has to write it
13:21  dario: that tracks. honestly i half expected it to hand me all three at once
```

#### `g6.r1.l6` — exclusions_or_crossover

**nils**, 2025-03-21, #pipeline

> context on that fix - i burned twenty minutes chasing a window typo when the real problem was that I had misspelled the provider. the error should name the first thing that's wrong.

*What a reader should take from it:* the team agrees the error should point at the outermost broken thing rather than the innermost

*Step it builds toward:* `g6.r1.sc2` — When more than one of provider, model and window is bad at once, the reason names the outermost one: an unregistered provider wins over a missing model, and a missing model wins over an unrecognised window.

*Drafted as:* burned twenty minutes on a window typo when the real problem was that i had misspelled the provider; it should name the first thing that is wrong.

*Why there:* Nils opens 2025-03-21 with "cost lookup fix is in" and then spends the morning on how that path is (barely) tested — the room is already on the cost lookup and has no explanation of what the fix was for. This supplies the motivating bug in his own voice, and it's his fix, so he's the one who would tell the story. Nobody has made this point yet; it doesn't settle which dimension counts as first or what the names become, which leaves room for the sibling remark. The 03-25 thread is entirely Mistral batch/provider coverage and WS-047, so the remark would land there as a subject change with no reaction.

*Still leaves open:* Which dimension counts as first, and what the resulting names are.

*Goes into the real conversation in #pipeline on 2025-03-21, after 09:00 nils:*

```
09:00  nils: cost lookup fix is in, and I have a VCR integration test in flight for the Mistral batch backend. Worth getting a second pair of eyes on the cost chan   <-- THE REMARK GOES HERE
09:03  nils: Is there any existing test coverage for the cost lookup path, or would the VCR cassette be the first thing touching it?
09:15  nils: @Dario, are PR 565 and 566 still actively in flight, or have they stalled out?
10:02  nils: i pulled up WS-047 and there's no page for it on the wiki yet. Is the spec written up somewhere else, or is that still to be done?
10:50  nils: vcrpy docs if anyone wants background on the cassette approach for the batch backend tests: https://vcrpy.readthedocs.io/en/latest/
11:51  emil: so there's no test that specifically targets the cost lookup path today, just things that happen to exercise it incidentally?
```

> **Problems:** longer than one remark

#### `g6.r1.l5` — exclusions_or_crossover, observability

**gideon**, 2025-05-13, page:engineering/price-lookup-errors-what-each-bad-argument-actually-raises.md

> so basically same args but with a provider we do have registered and it comes back unknown_model instead, so the junk window never even gets looked at.

*What a reader should take from it:* the team agrees a missing model key names the failure even when the window is also unrecognised

*Step it builds toward:* `g6.r1.sc2` — When more than one of provider, model and window is bad at once, the reason names the outermost one: an unregistered provider wins over a missing model, and a missing model wins over an unrecognised window.

*Drafted as:* Same args but with a provider we do have registered and it comes back unknown_model instead, so the junk window never even gets looked at.

*Why there:* Every listed place is chewing on something else: batch cancellation and Gemini finish reasons (WS-050, Mar 31 notes), image pinning, the response_format gate, rate-limit issues 207/233, the max_output_tokens//4 estimate, or the cost/cache handover. None of them is discussing the price lookup's error taxonomy — which failure name wins when the model key is missing from the registry and the context window value is also garbage. Dropping an `unknown_model` precedence observation into any of them changes the subject and nobody there would answer it. The kluster.ai postmortem is the nearest neighbour (provider-specific token ceilings) but it is about a silent estimate drift with no error raised at all, so a remark about which error code comes back has nothing to attach to. What should have existed is a short engineering doc written while someone was actually poking at the lookup: gideon owns online-request-processing and cost reporting per the May 1 handover, so he is the one who would have been calling the pricing helper with deliberately broken args and writing down what each combination returns, with Dario weighing in from the viewer side since the viewer renders whatever the lookup hands back.

*Still leaves open:* What happens when the provider itself is the unregistered one, and what the failure is called when only the window is wrong.

*Must appear literally:* `unknown_model`

*A new page — **Price Lookup Errors: What Each Bad Argument Actually Raises** in `engineering`, 2025-05-13:*

> **Why this page exists**

> **Date:** 2025-05-13
> 
> A run showed up in the viewer with the cost column empty, and the only thing in the logs was a `PriceLookupError` with a message that honestly told us nothing about which of the three arguments was the broken one. Took me most of a morning to figure out it was the model key and not the provider.
> 
> So basically I sat down and called the price helper with every broken combination of provider, model key and context window i could think of, and wrote down what comes back. This page is that table plus the precedence rule, so next time somebody sees an empty cost cell they can read the error code and know which arg to go look at.
> 
> This is a description of current b

> **The call being described**

> Everything below is about the single entry point:
> 
> ```
> get_model_price(provider, model_key, context_window)
> ```
> 
> It raises `PriceLookupError` on anything it cannot resolve, and the useful part is the `code` attribute on the exception, not the message. The message is the thing that was unhelpful in the first place.
> 
> Validation happens in this order internally: provider registry lookup, then model table lookup within that provider, then the context window tier, then the actual price row. That order matters and it is the whole reason for the precedence section below.

> **One thing wrong at a time**

> Each row here is a call where exactly one argument is bad and the other two are good.
> 
> | what is broken | code you get |
> | --- | --- |
> | provider string is not in the registry at all (typo, or a provider we never added) | `unknown_provider` |
> | provider is fine, model key does not exist under that provider | `unknown_model` |
> | provider and model fine, context window is negative or zero | `invalid_context_window` |
> | provider and model fine, context window is a real number but larger than any tier we have priced | `context_window_out_of_range` |
> | everything resolves but the price table has no row for that tier | `missing_price_entry` |
> 
> Two notes on the last two, because

> **When more than one argument is wrong**

> First failure in the validation order wins, and nothing after it runs. That is the entire rule, but it surprises people so here is a worked pair.
> 
> Call it with a provider that is not registered, a garbage model key and a nonsense context window like `-1`, and you get `unknown_provider`. Fine, that is what you would guess.
> 
> Same args but with a provider we do have registered and it comes back `unknown_model` instead, so the junk window never even gets looked at. Meaning: a green `unknown_model` does not tell you the context window you passed was acceptable. It tells you nothing at all about the window, because that check was never reached.
> 
> The practical consequence is that fixing

> **What to do with each code**

> - `unknown_provider` — caller side. Check spelling against the registry, and check whether the provider was ever registered in this environment. We have had cases where it exists in prod config and not in a local run.
> - `unknown_model` — caller side, usually a stale model key after a provider renames something. Grep the model table before assuming the price data is missing.
> - `invalid_context_window` — caller side, almost always an uninitialised or computed-to-zero value upstream.
> - `context_window_out_of_range` — could be either. If the request genuinely used that window, we need a new tier priced, so file it against the price data.
> - `missing_price_entry` — ours. Price table gap, n

### g6.r1.sc3 — A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.

*Nobody says:* Both cases are situations where a lookup currently 'succeeds' with bad data, so each has to be reclassified as one of the failures instead of being papered over.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g6.r1.l7` — exclusions_or_crossover

**nikolai**, 2025-06-18, thread:new|g6.r1.l7

> right that gemini row does exist in litellm.model_cost but input_cost_per_token on it is null and we priced a whole week of runs at zero off the back of it

*What a reader should take from it:* the team agrees a table row with a missing input price currently passes as a successful lookup and produces zeros

*Step it builds toward:* `g6.r1.sc3` — A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.

*Drafted as:* that gemini row does exist in litellm.model_cost, but input_cost_per_token on it is null, and we priced a week of runs at zero off the back of it.

*Why there:* Neither listed thread is anywhere near model pricing. The Jun 16 recap is a status note about the multimodal Gemini batch fix, PRs 690/691 and the fate of PR 653 — a lookup returning zero cost would change the subject and draw no reply from Dario, Emil, Konrad or Nolan, none of whom have said anything about cost tables there. The Docker image pinning thread is about backend_params, tags and read-only workspaces, a different subsystem entirely. The remark also needs a room that has already agreed on the symptom ("right, that row does exist...") — it's the second beat of a diagnosis, and neither thread has a first beat for it to answer. What should exist is a fresh mail nikolai starts after the zero-cost run report comes back, with dario and emil, where the group works out that a present-but-null row is currently indistinguishable from a good lookup; the sibling remark deciding how such a row gets classified and what the caller sees lands in that same thread.

*Still leaves open:* How such a row should be classified instead, and what the caller should see.

*Must appear literally:* `litellm.model_cost`, `input_cost_per_token`

*A new thread — **Week of Jun 9 rollup: gemini batch runs showing $0.00**, 2025-06-18:*

```
From: None  To: 


From: None  To: 


From: None  To: 


```

#### `g6.r1.l10` — exclusions_or_crossover, observability

**emil**, 2025-06-25, #code-review

> let me think through that - if a model's map has no row for the window you asked for thats unknown_window, we shouldnt be quietly borrowing the "*" tier.

*What a reader should take from it:* the team agrees an absent window is its own named failure rather than a wildcard fallback

*Step it builds toward:* `g6.r1.sc3` — A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.

*Drafted as:* if a model's map has no row for the window you asked for that is unknown_window, we should not be quietly borrowing the "*" tier.

*Why there:* None of the three rooms is anywhere near this. #cookbooks 2026-01-02 is CI wiring for code-execution verifiers and the fine-tuning handoff doc; #pipeline 2025-06-26 is streaming vs auto batch routing and cache invalidation; #viewer 2025-07-10 is whether a version tag renders. Nobody in any of them has mentioned pricing, per-model rate maps, context-window tiers, a "*" wildcard row, or an error taxonomy — so a line naming unknown_window as a distinct failure would change the subject and land with no reply, which is exactly the visible kind of plant. It also presumes a decision already half-made ("we shouldn't be quietly borrowing the * tier"), which needs someone to have proposed the wildcard fallback first. What should exist is the design thread where the price lookup's failure modes get named: dermot writing the per-model price map hits a model whose entry has a "*" catch-all row alongside specific window tiers, asks whether a missing window should just fall through to "*", and emil answers. The sibling remark — the other two failure names and what callers do with them — sits naturally later in that same thread, which none of these three days can host.

*Still leaves open:* What the other two failures are called, and what callers do with any of them.

*Must appear literally:* `unknown_window`

*A new conversation in #code-review on 2025-06-25:*

```
15:44  gideon: quick one on the price lookup - model has a window map, nothing in it matches the window we passed. what comes back
15:46  konrad: there is a "*" row sitting on that model though
15:49  emil: let me think through that - if the map has no row for the window you asked for thats unknown_window
15:51  konrad: ok but the star row is right there, presumably it just falls onto that?
15:54  emil: no, thats the bit i dont want. we shouldnt be quietly borrowing the "*" tier. unknown_window is honestly the more truthful answer
15:57  gideon: ya. tbh i hit this on a nightly last week and read the number as real
```

#### `g6.r1.l9` — exclusions_or_crossover

**nils**, 2025-06-26, #pipeline

> while you're in there - there's no 24h row for that model so the lookup fell through to the star entry, and my batch report came out with online prices again

*What a reader should take from it:* the team agrees falling back to the wildcard tier when a window is absent produces wrong numbers

*Step it builds toward:* `g6.r1.sc3` — A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.

*Drafted as:* the 24h row is missing for that model so we fell through to the star entry, and i shipped online prices in a batch report again.

*Why there:* no candidate location in range for this person

*Still leaves open:* What should happen for an unlisted window instead of the fallback, and what that failure is called.

*A new conversation in #pipeline on 2025-06-26:*

```
14:03  gideon: nils are you in the price lookup today? small thing while you're in there
14:06  nils: yes, most of the afternoon. what is it
14:07  gideon: my batch report came out with online prices again
14:11  nils: let me think. either the batch numbers are wrong for that model, or the lookup matched nothing at all. i'd lean toward nothing
14:13  gideon: ya nothing. there's no 24h row for that model, i checked the table twice
14:16  dermot: so it's not a plain miss then, it lands on the star entry?
14:19  nils: that's it. falls through to the star entry and takes the online prices off it, which is what gideon's report printed. i'll fold it into the pass i'm already doing rather than open something separate
14:21  dermot: mhm. explains the run i wrote off last month, i assumed i'd passed the wrong flag
```

> **Problems:** longer than one remark

#### `g6.r1.l8` — exclusions_or_crossover

**dermot**, 2025-07-02, page:engineering/model-price-lookup-what-a-miss-returns.md

> a row in the pricing table with a null input price is no more use to us than no row at all, it should come back exactly the way a missing key does.

*What a reader should take from it:* the team agrees a null-priced entry should be classified the same as an absent model entry

*Step it builds toward:* `g6.r1.sc3` — A litellm entry whose input price is missing or None counts as the model not being found, and a window absent from a model's price map is its own failure rather than a silent fall back to the wildcard tier.

*Drafted as:* a row with no input number is no more use than no row at all, it should come back exactly the way a missing key does.

*Why there:* Neither listed page is chewing on pricing lookup at all. The Jun 23 sync is batch-mode shipping status plus deferred issues 233 and 207; the Jul 10 page is a PR-by-PR freeze checklist (653, 675, 690, 693) and a review queue. A remark about null input prices in the price table answers nothing either page asks, and under "In-Flight PRs" or "Open items" it would land as a subject change with no one to reply to it. The decision it carries — null-priced row classifies as absent — is behavioural design, which belongs in the doc where the unknown-model path was being specified, alongside the sibling paste of what a missing key actually returns.

*Still leaves open:* What a missing key actually comes back as, which is somebody else's paste.

*A new page — **model price lookup: what a miss returns** in `engineering`, 2025-07-02:*

> **why this is written down**

> on monday the weekly cost report came out with 0.00 against two models. nothing in the reporting code had changed that week, and the arithmetic was fine — the problem was upstream, in the price table. the rows for those two models were present but carried no input number, and `lookup_price` was treating that as a different situation from a model it had never seen.
> 
> konrad's note pins down what the lookup hands back for a model it does not know. this page is the same contract written from the caller's side, plus the null-priced rows, so that we stop working it out from first principles every time a number looks wrong.
> 
> nothing here is new behaviour except where marked. it is mostly a 

> **the contract as it stands**

> `lookup_price(model_id)` has exactly two outcomes.
> 
> - a hit returns a `ModelPrice` with `input_per_1k` and `output_per_1k` both populated and both non-null
> - a miss returns `None`
> 
> things it does not do, and these are the ones people assume:
> 
> - it does not raise. a model we have never heard of is an ordinary condition, not an error
> - it does not return a zeroed `ModelPrice`. zero is a real price and we have at least one row that legitimately holds it, so zero and unknown cannot share a representation
> - it does not fall back to a sibling model or a family default. if the exact `model_id` is not priced, that is a miss
> 
> lookup is by exact `model_id` string. no normalisatio

> **rows that exist but carry no input number**

> a handful of rows in the table have a name and an output number and nothing at all for input. they come in that way from the upstream source; it is not something we introduced. these were the two models on monday's report.
> 
> a row in the table with no input number is no more use to us than no row at all, so it comes back exactly the way a missing key does — `lookup_price` returns `None`, and the caller takes the same branch it would take for a model that was never listed. same for a row missing the output number. there is no third state and callers do not get to inspect the partial row.
> 
> the check is on the loaded row, not on the file, so a row that goes null on a table refresh starts

> **what callers do with a miss**

> the rule is that a miss propagates. it does not get filled in with a plausible number somewhere in the middle of the stack.
> 
> - **cost reporting** — a miss renders as `unknown`, not `0.00`, and the run summary carries a count of unpriced models. this is the change that would have made monday visible on the day it happened rather than a week later
> - **budget checks** — a miss is not treated as "within budget". the check reports that it could not evaluate, and the caller decides
> - **anything summing across models** — an unpriced model is excluded from the total and named in the exclusion list. a total that silently drops rows is worse than no total
> 
> not entirely sure the budget chec

> **open items**

> - the null rows themselves are an upstream data problem. we can ask for them to be filled or we can keep absorbing them, and nobody owns that question yet
> - no alerting on the unpriced count. it goes in the summary and that is all it does, so it still relies on someone reading the summary
> - table refresh cadence is not documented anywhere i can find
> 
> none of these are v0.1.26 blockers. flagging them so they are at least in one place.

> **Problems:** longer than one remark

### g6.r1.sc4 — Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.

*Nobody says:* If a run must not die over an accounting number, and the viewer must not show a fabricated zero, then the failure has to be caught at every call site and recorded rather than rendered.

*4 remarks — 2 reporting the problem, 2 settling the design.*

#### `g6.r1.l11` — observability

**gideon**, 2025-03-24, #engineering

> Ya, thats not theoretical - tracker took the whole online run down last night 4k requests in, on a model litellm has never heard of. Cost display, not the work.

*What a reader should take from it:* the team agrees a pricing failure currently kills a run that was otherwise fine

*Step it builds toward:* `g6.r1.sc4` — Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.

*Drafted as:* Tracker took the whole online run down last night about 4k requests in, on a model litellm has never heard of. Cost display, not the work.

*Why there:* That room is already on the cost/pricing table: Gideon owns the cost estimation revamp, Emil has just argued pricing comes down from litellm weekly and should stay in its own table, and Konrad at 15:23 asks outright whether litellm actually covers all the providers they're adding. A concrete case of a model litellm doesn't know killing a run answers Konrad's doubt and hardens Emil's point about pricing being external and incomplete, without saying what the tracker should do instead. Gideon is the natural reporter — the cost path is his work and he's the one who profiles runs and brings back symptoms elsewhere in the corpus.

*Still leaves open:* What the tracker should do with the failure instead, and what the other call sites should do.

*Goes into the real conversation in #engineering on 2025-03-24, after 15:23 konrad:*

```
09:00  gideon: Cost estimation revamp is mostly shaped up on my end
09:00  gideon: Colab display fixes are wrapped too
09:19  konrad: Sent the weekly update, it should be in everyone's inbox
09:19  konrad: @Gideon on the cost revamp, is the pricing/cost table staying separate from the consolidation work or is that getting pulled in?
09:41  gideon: Pricing/cost table stays separate, it's not part of the consolidation.
09:41  gideon: Anyone have thoughts on the cost estimation revamp direction before I go further with it?
10:00  konrad: Separate works for me on the pricing table. I'll take a look at the cost estimation direction and get back to you this morning
10:00  konrad: Has anyone taken a look at the examples table yet and whether it covers what you'd expect to find there?
10:31  nikolai: haven't looked at it yet
10:48  gideon: Glanced at the examples table, there are some gaps that seem like they'd be easy to miss. Is that expected or are we still filling things in?
10:49  gideon: Cost estimation design is in a good place to walk through
10:49  gideon: Waiting to hear back from Konrad, but I'm free this afternoon if a sync makes more sense
13:04  emil: - *PR 579* (openai/deepseek) is up, touches provider-integrations, asked for eyes in code-review
- *PR 584* (Mistral batch) I'm reviewing this afterno
13:06  konrad: @Gideon what kind of gaps did you notice, anything specific missing or more of a coverage thing across use cases?
13:51  gideon: @Konrad more of a coverage thing, it reads better if you already know what provider you want than if you're trying to discover what's possible.
15:10  emil: Do we have a settled pattern for how new provider examples should be named and structured, or is that still being figured out as we go?
15:10  emil: Pricing comes down from litellm and changes weekly, half of it is per-region.
15:10  emil: Not keen on folding it into the same place either
15:10  emil: Keep the cost table where it is
15:10  emil: If it lives next to capability data someone will start hand-editing prices and we'll have a mess
15:22  konrad: @Gideon yeah that tracks, and it's the thing I still don't have a clean answer on - the table works fine if you already know your provider but doesn't
15:22  konrad: That part's still not resolved
15:22  konrad: I'm around this afternoon if you want to do the cost estimation walkthrough
15:23  konrad: so does litellm actually cover deepseek and the mistral batch stuff too, I'm not totally sure all the providers we're adding are in there   <-- THE REMARK GOES HERE
16:16  nikolai: the batch API specifically, or the regular mistral endpoints too?
16:57  gideon: Cost estimation is ready to walk through, @Konrad, if you've still got a few minutes before end of day
17:41  konrad: @Gideon still here, though I'm a little unsure there's enough time to do it properly now - do we try to fit it in or just pick it up first thing tomor
17:41  gideon: fair
17:42  gideon: let's just pick it up tomorrow
18:29  emil: On the provider example pattern question I raised earlier, are we settling on the same naming convention Dermot used for Mistral, or is that still up 
18:29  emil: Can someone share a link to the examples table?
18:30  emil: I want to look at the structure myself and see if the naming pattern question answers itself
```

#### `g6.r1.l13` — observability

**dario**, 2025-04-21, thread:<178770212973.2301745.4705747507669611471@world.local>

> on WS-054 — for the trackers input_cost_per_million and output_cost_per_million just stay empty and the reason sits on price_unavailable_reason, so we can show why rather than a number.

*What a reader should take from it:* the team agrees a tracker holds no prices and retains the failure reason instead of raising

*Step it builds toward:* `g6.r1.sc4` — Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.

*Drafted as:* on the trackers i want the price fields left empty and the reason kept on the object, so we can show why rather than a number.

*Why there:* Emil's Apr 14 rundown puts WS-054 (cost accounting) explicitly in play — "in progress, not blocked", with PR 643's response object as part of it — and dario is on the thread. Cost accounting is exactly where the question of what a tracker holds when a price lookup fails lives, so a short reply from dario settling the tracker side (empty price fields, reason retained on the object rather than raising) reads as him answering the one open design point in Emil's status rather than introducing a new topic. Nothing in the mail already states this, and it deliberately leaves what the cost calculations return and what the reason strings say for elsewhere.

*Still leaves open:* What the cost calculations themselves return, and what the reason strings can be.

*Must appear literally:* `WS-054`, `input_cost_per_million`, `output_cost_per_million`, `price_unavailable_reason`

*Goes as a reply into the real thread "Weekly update: week of Apr 14":*

```
Hey all,

Quick rundown on where things stand heading into this week.

WS-050 (batch-mode bug sweep): working through the main failure cases, got the Gemini job-state check addressed in PR 646. A few more edge cases still to close out, but we're past the worst of it.

WS-054 (cost accounting): in progress, not blocked. The response object work in PR 643 is part of this — should have something reviewable this week.

PR situation: I have PR 468 (n samples), PR 643 (response object), and PR 646 (Gemini job state) all sitting in review. They need a rebase before they can move, which I'll sort out today. PR 632 (Gideon's CLI batch update frequency fix) looks contained and ready to land — needs eyes. PR 650 (DeepSeek json_schema) just came in and is coming to me.

If anyone can spare time for reviews this week, 632 is the quickest one to get through.

Emil
```

#### `g6.r1.l14` — observability

**dermot**, 2025-05-01, #code-review

> that said, the pricing gaps part of that page: input_cost_per_million comes through None and the viewer renders it $0.00, which readers read as free. that zero shouldnt be shown.

*What a reader should take from it:* the team agrees a fabricated zero price in the display is misleading and should not be shown

*Step it builds toward:* `g6.r1.sc4` — Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.

*Drafted as:* pricing gaps page: the viewer prints $0.00 for anything we cannot price, which every reader takes to mean the model is free.

*Why there:* Gideon opens that day by posting the "Handover: Status Tracking, Cost Reporting & the Viewer Surface" page and going out of his way to defend one zero — zero cache hits on a fresh machine — as a correct number to report, and later says he can't vouch for the numbers the viewer is surfacing. Dermot is in the room, already engaged with Gideon, and the natural counterweight is the other zero on that page: a fabricated $0.00 price that isn't correct and shouldn't be shown. Nothing there has made this point yet, and it complicates rather than repeats Gideon's line. The viewer thread on 04-14 is the wrong home — that day's bad cost column is diagnosed as stale provider metadata on resume and handed to Dario, and the cost columns aren't user-facing yet.

*Still leaves open:* What the tracker should carry instead of the zero, and what the compute path should return.

*Must appear literally:* `$0.00`, `None`, `input_cost_per_million`

*Goes into the real conversation in #code-review on 2025-05-01, after 09:04 gideon:*

```
09:00  dermot: PR 658 is ready for review, release-and-ci side
09:00  dermot: not blocking a release but I'd like eyes on it this morning if anyone has a slot
09:04  gideon: Handover: Status Tracking, Cost Reporting & the Viewer Surface is up on the engineering wiki. One thing I wanted to nail down explicitly in there: zer
09:04  gideon: @Dermot what's the part of PR 658 you most want eyes on, release scripts or CI config?   <-- THE REMARK GOES HERE
11:34  dermot: CI config side mainly
12:16  emil: PR 643 could use eyes if anyone has a slot after lunch, response object changes on the online-request-processing side.
12:17  emil: PR 651 is up for review too, multimodal models update on the provider-integrations side.
12:39  dermot: I can take a look at PR 643 this afternoon
12:39  dermot: @Dario, might be worth you weighing in too given the viewer surface
12:41  emil: thanks Dermot
12:41  emil: also, I can look at PR 658 CI config this afternoon if nobody's on it yet
12:41  emil: Tried to pull up WS-055 in the tracker and couldn't find it, Dermot
12:41  emil: Is that written up anywhere yet, or is it still pending?
12:52  gideon: PR 643 is also a blocker for me on the integration side, the viewer is reading response fields that aren't under the stable contract yet, so until tha
12:52  gideon: @Emil are the response object changes in PR 643 additive, or do they rename or remove any existing fields?
13:34  gideon: Is PR 643 still targeting a merge today or has that slipped to tomorrow at this point?
13:51  gideon: Anyone had a chance to look at PR 632 yet?
17:51  emil: Sorry @Gideon, PR 643 is additive only, no fields renamed or dropped
17:52  emil: Not sure if Dermot got through the review yet, might slip to tomorrow
17:52  emil: PR 658 CI config still needs a reviewer too, I didnt end up getting to it this afternoon.
18:00  dermot: just checked, WS-055 isn't in the wiki or the tracker
18:00  dermot: that writeup is mine and I haven't done it yet
18:00  dermot: @Emil is it blocking anything on your side right now?
```

> **Problems:** longer than one remark

#### `g6.r1.l12` — observability

**konrad**, 2025-05-27, page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md

> Related: sometimes the price cant be resolved at all. Every cost() method should be catching that and handing back 0.0 rather than ending a run over an accounting number.

*What a reader should take from it:* the team agrees cost calculations degrade to 0.0 when the price cannot be resolved

*Step it builds toward:* `g6.r1.sc4` — Callers never let the failure escape: every cost calculation degrades to 0.0, and the trackers keep no prices at all plus the reason string for display.

*Drafted as:* Every cost() method should be catching that and handing back 0.0 rather than ending a run over an accounting number.

*Why there:* The page's "Out of scope" section is already about the cost counter producing wrong numbers on resumed jobs (pricing off the current config model), so the room is actively chewing on how much a bad accounting number should be allowed to matter. Konrad owns cost reporting on the online-request-processing side, so him commenting on emil's closed workstream page to pin down the adjacent failure — price not resolvable at all — is natural, and it leaves the tracker-side behavior untouched for the sibling remark.

*Still leaves open:* What the trackers do with it, which is a different call site with different state to keep.

*Must appear literally:* `Every`, `cost()`

*Goes as a comment on the real page `engineering/ws-050-batch-mode-50-cost-async-batch-apis.md`, at: ## Out of scope: cost accounting offset on resumed jobs:*

```
# WS-050: Batch Mode (50%-Cost Async Batch APIs)

## Status

Closed.

## What this workstream covered

Sweep across providers to implement and stabilize async batch API support, specifically targeting the 50%-cost tier. Primary focus ended up being Gemini batch processing, which is where both bugs surfaced.

## Bugs fixed

### Finish reason parsing (PR 621)

Gemini batch responses were returning `None` for `finish_reason` on successful completions. Not a failure case, just a silent gap in the parsed response. Fixed in PR 621.

### Batch cancellation (PR 614)

Several edge-case bugs in the cancellation path. I dont have the full list of cases in front of me but the fix is in PR 614 and the sweep confirmed behavior looked correct after.

## Out of scope: cost accounting offset on resumed jobs

During the sweep we identified a 10x cost offset on resumed jobs. The cause is that the cost counter prices off the current config model rather than the model that was set at the time of the original submission. So if the config changes between submission and resume, you get a wrong number, and depending on which direction the price moved it can be badly wrong.

This is confirmed out of scope f
```

> **Problems:** longer than one remark


## g6.r2

**The hidden requirement:**

- **rule** — The batch discount factor is applied by exactly one method, `batch_multiplier()`, on the cost processors; no `cost()` override multiplies or divides its result by anything. `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.
- **scope** — `batch_multiplier()` returns the discount factor only where the pricing data is a list price: it returns `1.0` when the processor is not in batch mode, and `1.0` on the klusterai and inference.net processors in every mode. `resolve_model_price` discounts a `source == "litellm"` price and leaves a `source == "external"` price exactly as the table lists it.
- **exclusions_or_crossover** — A user-supplied per-million price is never discounted: `batch_multiplier()` returns `1.0` whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount. Which processors are exempt is decided by a class-level flag and by which source answered the lookup.
- **observability** — `batch_multiplier()` is the discount factor on the base and Azure processors in batch mode and `1.0` out of it, and `1.0` on the klusterai and inference.net processors even in batch mode. `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` equals the `batch=False` value exactly, while a litellm-sourced model's `batch=True` value is exactly half its `batch=False` value.

**Reversed earlier:** the team once applied the fixed batch discount uniformly to every source inside the base cost processor, then had klusterai/inference.net multiply their own result by 2 to cancel it back out because their tables were already batch-tier prices; that compensating multiply was later dropped in favour of one method that simply declines to discount those two providers

**What a reader has to infer along the way:**

- *The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.*
  - nobody says: If two layers each take a cut off the same price the answer depends on which of them ran, so the factor has to have a single owner that everything else calls.
- *The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.*
  - nobody says: A table that already quotes the batch tier has had the discount taken once; taking it again is not a discount, it is an error, so the discount belongs only to list prices.
- *A price the user supplied themselves is never discounted: `batch_multiplier()` returns 1.0 whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount, and which processors are exempt is decided by a class-level flag and by which source answered the lookup.*
  - nobody says: A number a user typed in is the number they were quoted, not a list price we are entitled to mark down; and the exemption has to be a property of the processor rather than a string check buried in the arithmetic.
- *The factor is a fixed one half, observable as `batch_multiplier()` on the base and Azure processors in batch mode and 1.0 out of it, 1.0 on klusterai and inference.net even in batch mode, and as `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` matching its `batch=False` value while a litellm-sourced model's halves.*
  - nobody says: If both the processor method and the resolver are meant to use one factor, the way you show they do is to compare the two prices they hand back for the same model.

**Names the tests reach for that the ticket withholds:**

- said: `The`, `batch_multiplier`, `config`, `inference.net`

> **Spread:** g6.r2.g6r2-s4: two remarks in #pipeline within 9 days

> **Said outright:** every one of the 30 assertions grading this requirement rests on a remark that states it (`settled.md`).

### The remarks, by the step they build

### g6.r2.g6r2-s1 — The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

*Nobody says:* If two layers each take a cut off the same price the answer depends on which of them ran, so the factor has to have a single owner that everything else calls.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g6.r2.g6r2-s1-l1` — rule

**gideon**, 2025-03-19, #pipeline

> The batch estimate came in at a quarter of the invoice again, so basically two separate layers each knocking half off the same price. Nobody's disputing that part at this point.

*What a reader should take from it:* the team agrees the discount is currently being applied more than once

*Step it builds toward:* `g6.r2.g6r2-s1` — The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

*Drafted as:* The batch estimate came in at a quarter of the invoice again, like two separate layers each knocked half off the same price.

*Why there:* On 03-19 the room is working through the postmortem's open action item to audit the batch-mode estimation path, and Gideon has just made the point that the postmortem blames more than the cost accounting. A concrete symptom — the batch estimate landing at a quarter of the invoice, as if the discount gets applied twice — is exactly the kind of thing he'd add to his own burst there, and it gives the estimation-path audit something specific to chase. It doesn't resolve which layers do it or what the resolver should do with batch=True.

*Still leaves open:* Which two layers, which one is supposed to keep doing it, and what the resolver is meant to do with batch=True.

*Must appear literally:* `The`

*Goes into the real conversation in #pipeline on 2025-03-19, after 11:42 gideon:*

```
09:00  nils: put the weekly notes for week of Mar 17 on the wiki (engineering/weekly-notes-week-of-mar-17). Covers provider and batch-mode status, the PR 584 block
10:43  dermot: read through Nils's weekly notes
10:43  dermot: gemini unicode fix is showing no regressions so far, which is good, but the backpressure question from the output-token change is still marked open th
11:05  emil: Gemini batch side looks clean from what I can see too
11:05  emil: Mistral is still stuck on the api_key config for PR 584, haven't found a clean path forward on that yet
11:22  nils: yeah
11:22  nils: PR 584 is stuck on that exactly
11:22  nils: need a decision on how the api_key gets passed for Mistral batch before I can move it forward
11:29  gideon: so the backpressure question is still open on both sides
11:41  gideon: Read through the postmortem, and it explicitly says the rate limiter was miscalculating headroom, not just the cost accounting
11:42  gideon: Has anyone actually run a check on the throttle path since the wrapping fix landed, or are we calling it clean without one?   <-- THE REMARK GOES HERE
12:19  emil: @Nils, you getting any traction on the api_key question or still waiting on someone to make the call?
12:34  dermot: @Gideon I haven't seen a proper check done
12:34  dermot: that path is in online-request-processing, @Dario, are you in a position to run one this afternoon?
13:09  nils: went with the env-variable pattern, same as the other providers. no separate config path needed, so PR 584 is unblocked
13:52  gideon: I can run that check, online-request-processing is mine
13:52  gideon: @Konrad, do you want an explicit throttle validation before we close out the postmortem action item, or are we ok proceeding on no observed regression
14:02  gideon: The batch-mode estimation path is getting checked this afternoon but has anyone looked at the throttle path in online-request-processing specifically?
14:02  gideon: I offered to run that check but I'm still waiting on a call on whether it's needed
14:41  dermot: good news on PR 584
15:10  gideon: Read through the postmortem - it has an open action item to audit the batch-mode estimation path, but doesn't call out the throttle path in online-req
15:10  gideon: Does Emil's check this afternoon cover that too, or is that still pending?
15:27  emil: My check is the batch-mode estimation path
15:27  emil: The throttle path in online-request-processing is separate and still pending
15:27  gideon: So that one's still on me to run?
15:34  emil: Looks like it. I'll finish the batch-mode side, you cover the throttle path, and we should have both closed out by end of day.
16:07  dermot: will you both post results here when done?
16:32  nils: PR 584 is in progress, the api_key change itself is fairly straightforward so should be up for review tomorrow morning
16:41  dermot: gemini unicode fix is confirmed clean, mistral api_key is sorted, good place to end the day.
16:41  gideon: by end of day today, so I'm running it now?
17:04  nils: solid
18:14  gideon: Running it now, will post results
18:29  emil: Batch-mode estimation check is done, came back clean.
18:29  gideon: Throttle path check is running, should have results in a few minutes
18:29  gideon: Throttle check came back clean, no regressions.
```

> **Problems:** longer than one remark

#### `g6.r2.g6r2-s1-l4` — rule, observability

**dermot**, 2025-04-14, page:releases/v0-1-22-release-notes.md

> on the 50% line: resolve_model_price has no separate batch row, batch=True scales what batch=False returned. whichever number batch_multiplier() hands the processors, it should be reading that same one.

*What a reader should take from it:* the team agrees resolve_model_price applies the same fixed factor the processors do

*Step it builds toward:* `g6.r2.g6r2-s1` — The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

*Drafted as:* the resolver's batch=True price and the tracker's batch price differed by half; whichever factor the processors use, resolve_model_price should be using the same one.

*Why there:* This is the page that puts the batch discount on the record — "the same 50%-cost discount the other two providers offer" — and it's the release that made Mistral a first-class batch provider, so batch pricing is exactly what the room is chewing on. A comment from dermot picking up that line to say two code paths disagreed by precisely that factor reads as somebody correcting/completing what the notes assert, which is what release-notes comments are for. Emil wrote the page and owns the batch story; dermot is the one who reads through and flags inconsistencies (he does the same on the weekly notes pages). The page nowhere mentions the resolver or the tracker, so nothing here is redundant, and stating that resolve_model_price should use the processors' factor is a decision the notes leave open. It stops short of naming the constant or scoping which providers it applies to.

*Still leaves open:* What the factor is, and which models or providers it is allowed to touch.

*Must appear literally:* `batch=False`, `batch=True`, `batch_multiplier()`, `resolve_model_price`

*Goes as a comment on the real page `releases/v0-1-22-release-notes.md`, at: ## Mistral batch support:*

```
# v0.1.22 Release Notes

## Breaking change: authentication required everywhere

Auth is now enforced on every provider backend. If API keys are not configured before running, the client will raise, it will not fall through silently. This was optional in some code paths before this release. It is not anymore.

If you are upgrading from an earlier version, configure credentials first. Do not assume the old silent-fallback behavior is still there.

## Mistral batch support

Mistral is now a first-class batch provider alongside Anthropic and OpenAI. You can submit async batch jobs to Mistral at the same 50%-cost discount the other two providers offer.

The design and failure model for batch mode are documented in WS-050 on the wiki (Batch Mode, 50%-Cost Async Batch APIs). Worth reading if you are new to batch, the failure model in particular has a few details worth knowing before you rely on it in production.

## Examples refreshed

All examples have been updated for the current API, including Mistral batch authentication. If you have been working from an older example, pull the latest before you go any further. Some of the auth usage in older examples is wrong now given the breaking
```

#### `g6.r2.g6r2-s1-l2` — rule

**dario**, 2025-04-15, #pipeline

> while we're on the provider cost paths, i left the same note on the azure cost() override again: why is this dividing by two here when batch_multiplier already ran

*What a reader should take from it:* the team agrees a cost() override is scaling the result after the multiplier has already been applied

*Step it builds toward:* `g6.r2.g6r2-s1` — The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

*Drafted as:* left this on the azure cost() override again: "why is this dividing by two here when batch_multiplier already ran"

*Why there:* The room spent the day on the cost accounting path per provider — gideon asking twice whether GPT-4.1 structured output needs its own handling or maps onto existing OpenAI provider logic, and dario answering at 18:28 that he can't confirm the cost accounting integration until he knows what PR 640 does to the provider mapping. A second, concrete instance of a per-provider cost path being wrong (azure's cost() override scaling again after batch_multiplier) lands directly on that thread: it's evidence that the provider-specific cost overrides are already untrustworthy, which complicates "does it map cleanly onto existing provider logic." Dario is the one holding the cost accounting/provider mapping question that day, and nobody has raised the double-scaling yet, so it isn't redundant. It also stops short of who owns the fix, leaving the override-vs-method question open.

*Still leaves open:* Whether the override or the method should be the one to go, and whether anything outside the processors applies the factor at all.

*Must appear literally:* `batch_multiplier`

*Goes into the real conversation in #pipeline on 2025-04-15, after 18:28 dario:*

```
09:00  gideon: Cost streaming is looking cleaner after the schema updates landed, stil trying to pin down whether the batch mode response-shape issues are Gemini-spe
09:50  gideon: Has anyone confirmed whether the batch mode response-shape issues are isolated to Gemini, or are they turning up on other providers too?
10:12  gideon: Does the GPT-4.1 structured output format need its own handling in the cost accounting path, or does it map cleanly onto the existing OpenAI provider 
10:56  gideon: Has anyone checked whether cost streaming could deadlock against the rate limiter if the buffer backs up?
12:44  emil: From what I've seen so far the response-shape bugs are turning up on Gemini and not other providers, but I haven't ruled out it being something in how
13:23  gideon: Is the shape mismatch showing up in the raw response, or after the request layer has touched it?
13:51  dario: Tangentially related to the batch mode stuff, but I finally traced why one of my runs was asking for root: the entrypoint does an apt-get at container
13:51  dario: Batch completed fine, numbers looked normal, and I only figured it out days later when I opened the Dockerfile for something unrelated
13:51  dario: Nothing in the output or logs flagged that the run had been any different
14:20  emil: It's showing up after the request layer, not in the raw response. Something like this:

```python
result = response.model_dump()
# result["structured_
14:36  gideon: GPT-4.1 structured output mapping, still no answer on whether it conflicts with the Gemini or Anthropic provider paths
14:36  gideon: Anyone confirmed it integrates into cost accounting cleanly?
15:22  emil: Schema updates landing cleanly really simplified the cost streaming path.
15:22  emil: Ran it this afternoon and it looks fine against the rate limiter, buffer drains before anything backs up enough to deadlock.
15:23  emil: WS-050 doesn't exist anywhere I can find - is that spec filed somewhere other than the issue tracker, or has it just not been written yet?
16:50  gideon: Tuesdays always end up being the real work day, Mondays are just warmup
18:28  dario: Can't confirm GPT-4.1 cost accounting integration on my end until I know what PR 640 does to the provider mapping, so that piece is still open   <-- THE REMARK GOES HERE
18:29  dario: So it just hasn't been filed yet?
18:29  emil: Yeah
18:29  emil: just hasn't been filed - that's my gap
18:29  emil: Nice call on cost accounting though, good to have that unblocked
```

#### `g6.r2.g6r2-s1-l3` — rule

**emil**, 2025-05-02, #code-review

> spent the morning working out which of the two subtracions was the real one. only one place in the tree gets to touch the price for batch, we agreed that much.

*What a reader should take from it:* the team agrees only one place may adjust the price for batch

*Step it builds toward:* `g6.r2.g6r2-s1` — The batch discount factor comes from exactly one method on the cost processors, `batch_multiplier()`, and no `cost()` override adjusts its own result; `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

*Drafted as:* spent the morning working out which of the two subtractions was the real one, there should only be one place in the tree that touches that number.

*Why there:* On 2025-05-02 emil is already the one doing price math in that room — he's chewing on the cookbook cost estimate, complaining about "a percentage I have to invert" and wanting to multiply misses by price per row to put a dollar figure in front of someone. A batch discount applied as a percentage is exactly the kind of thing that gets subtracted twice, so him reporting a morning spent chasing which of the two subtractions was real, and stating that only one place in the tree may touch the batch price, reads as the same person continuing the same work rather than opening a new subject. Nothing already said covers double-adjustment, and it leaves open where that single place is and whether the price resolver sits inside it.

*Still leaves open:* Where that one place is, and whether the price resolver counts as inside or outside it.

*Goes into the real conversation in #code-review on 2025-05-02, after 12:24 emil:*

```
09:00  konrad: PR 656 and 659 both merged this morning, finetuning side is clean
09:00  konrad: Six older PRs still need eyes on blockers before end of day
09:27  gideon: PR 632 needs eyes too, it touches progress-and-cli and the batch update-freq logic
09:27  gideon: Not release-blocking but hte queue is getting long
10:04  konrad: My side is clear now that 656 and 659 are in
10:28  gideon: PR 632 is one of those six, does it actually get eyes today or is it rolling to next week?
10:55  konrad: Fair question.
11:30  emil: does PR 632 need someone with batch context to review it, or is it just waiting on general eyes?
11:39  gideon: It's mostly general eyes, the batch logic is pretty self-contained.
11:39  gideon: Still five or six PRs in that queue that need someone to claim them beofre end of day.
12:24  emil: which of those five or six PRs still don't have anybody on them?   <-- THE REMARK GOES HERE
12:41  emil: on the cookbook cost estimate, I don't want a percentage I have to invert. misses needs to be a plain int.
12:41  emil: that way I can multiply by price per row and put an actual dollar figure in front of someone before they hit go
13:48  emil: has anyone actually written the handover page for status tracking, cost reporting and the viewer surface?
13:48  emil: I've been trying to find it and it doesn't exist anywhere
14:06  konrad: PR 656 and 659 are confirmed merged, finetuning is clear. PR 632 still needs an owner and from what Gideon said there are at least a few more in the q
15:51  emil: are we actually triaging the rest of that queue today, or is this rolling to Monday?
16:06  emil: v0.1.23 release notes still don't exist - should those get written before v0.1.24 cuts?
16:51  gideon: PR 632 is ready on my end, just needs someone to claim the review.
16:51  gideon: If nobody picks up PR 632 by end of day, it rolls to Monday.
17:28  emil: I added myself to PR 632 earlier - honestly not sure it makes sense to rush a review in the last half hour
17:28  emil: does it matter if it goes to Monday?
17:50  gideon: Monday is fine, it's not blocking anything.
17:51  gideon: - *PR 632*: ready, Emil is on it, reviewing Monday
- *656 / 659*: confirmed merged
18:28  emil: so the remaining queue rolls to Monday - I'll start with PR 632.
18:28  emil: WS-055 on the wiki has the CI gating rules for PRs, in case that's a useful reference.
```

> **Problems:** longer than one remark

### g6.r2.g6r2-s2 — The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.

*Nobody says:* A table that already quotes the batch tier has had the discount taken once; taking it again is not a discount, it is an error, so the discount belongs only to list prices.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g6.r2.g6r2-s2-l1` — scope

**nils**, 2025-03-26, #pipeline

> let me think - klusterai's published per-million is already their batch rate, and we went and took another 50% off it in the estimate.

*What a reader should take from it:* the team agrees the klusterai table is already a batch-tier price and must not be discounted again

*Step it builds toward:* `g6.r2.g6r2-s2` — The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.

*Drafted as:* klusterai's published per-million is already their batch rate, and we went and took another 50% off it in the estimate.

*Why there:* Both listed rooms are one continuous thread about PR 584 (Mistral batch processor), which fixture tests were removed, provider test coverage, and the unwritten WS-047 spec. Neither mentions pricing, per-million rates, cost estimates, or klusterai anywhere across two days. The remark corrects an error in a price estimate — there is no live discussion it answers or complicates, so it would land mid-thread as a subject change and get no reaction. Nils is the right speaker for it, but not in those threads on those days. It needs a room where someone has actually put the estimator's numbers next to the published provider tables.

*Still leaves open:* Whether the same holds for the other external providers, and what the resolver should return for them.

*Must appear literally:* `50%`

*A new conversation in #pipeline on 2025-03-26:*

```
13:18  dario: klusterai in the cost estimate is landing at about half what the invoice says. one of the two is lying
13:21  gideon: we take the batch discount off there tho, thats expected no
13:25  nils: let me think - their published per-million is already the batch rate. there's nothing to take off it.
13:27  dario: ok but that alone doesnt get us to half. the estimate is way under even without that
13:31  nils: that's the rest of it. we went and took another 50% off it in the estimate anyway, so the thing is cut twice. the published number stands, the extra one comes out
13:34  dario: that tracks. so the pricing entry stays as-is and the multiplier goes for them
13:36  gideon: ya tbh i think i copied that multiplier down from the block above when i added them
```

#### `g6.r2.g6r2-s2-l4` — scope, exclusions_or_crossover

**emil**, 2025-04-14, thread:<178769930038.2250839.2605881431154859866@world.local>

> on your cost question — resolve_model_price with provider=klusterai and batch=True came back at half the table rate, and anything we read out of those provider tables should come back exactly as listed.

*What a reader should take from it:* the team agrees resolve_model_price returns external-table prices unmodified

*Step it builds toward:* `g6.r2.g6r2-s2` — The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.

*Drafted as:* resolve_model_price for provider=klusterai with batch=True came back at half the table, but anything we read out of those provider tables should come back exactly as listed.

*Why there:* Dermot's Apr 14 weekly update ends with an explicit open question — "is cost metadata coming back consistently from provider backends, or are there gaps depending on which one you hit? This matters before PR 626 lands. If you've run against multiple backends recently please shout." Emil owns PR 626 (metadata schema update with cost fields) and is the person most blocked by the answer, so he's exactly who replies with a concrete gap he hit. The klusterai batch=True halving is the kind of per-backend inconsistency Dermot was fishing for, and it lands the settled expectation (external provider tables come back unmodified) without touching the litellm-priced case.

*Still leaves open:* What the resolver should do for a model it priced out of litellm instead.

*Must appear literally:* `resolve_model_price`, `batch=True`

*Goes as a reply into the real thread "Weekly update: week of Apr 7":*

```
Hi all,

Quick summary of where things stand coming into this week.

What shipped last week: v0.1.23 is out, and we cut v0.1.23.post1 shortly after to address a post-release regression. Postmortem is in the wiki under the postmortems collection.

In flight right now:
- PR 631: projected-total and projected-remaining readout improvements (in review)
- PR 632: curator CLI batch update frequency fix (in review, needs eyes)
- PR 626: metadata schema update with cost fields (Emil, waiting on 632 to land first, or possibly can proceed in parallel — see below)
- PR 634: OpenAI/DeepSeek provider support (Tomas)
- PR 583: param to disable metadata db (Nikolai)
- PR 468: n samples in generation params (Emil)

Merge ordering to sort: PR 632 should ideally land before PR 626, but I'm not sure that's a hard dependency. Worth clarifying so Emil isn't blocked unnecessarily.

Open question I'd like input on: is cost metadata coming back consistently from provider backends, or are there gaps depending on which one you hit? This matters before PR 626 lands. If you've run against multiple backends recently please shout.

Dermot
```

> **Problems:** longer than one remark

#### `g6.r2.g6r2-s2-l3` — scope

**dario**, 2025-04-22, page:meetings/weekly-notes-week-of-apr-14.md

> re the batch vs online cost question — i had an online run showing batch pricing in the tracker all afternoon. outside batch mode the list price comes through untouched, thats settled at least.

*What a reader should take from it:* the team agrees no discount is applied when the processor is not in batch mode

*Step it builds toward:* `g6.r2.g6r2-s2` — The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.

*Drafted as:* an online run was showing batch pricing in the tracker all afternoon; outside batch mode the list price should come through untouched.

*Why there:* The page ends with an explicit open question — "Batch vs online cost representation: how do we align the cost number the user sees in batch mode with what they'd see in online mode?" — and flags that nobody knows if the difference is documented as intentional. Dario owns the viewer/cost-surfacing integration and the tracker readout, so he is the natural person to answer half of that question with a concrete sighting and the settled half of the rule, while leaving the in-batch behaviour (and provider exemptions) still open, which is what the page's other open question is about anyway.

*Still leaves open:* What happens inside batch mode, and which providers are exempt there.

*Goes as a comment on the real page `meetings/weekly-notes-week-of-apr-14.md`, at: ## Open Questions:*

```
# Weekly Notes, Week of Apr 14

## Merged

- PR 632, CLI batch update frequency fix, merged earlier this week
  - was blocking some local testing so glad thats out

## In Flight

- PR 640, OpenAI and DeepSeek API support
  - still open, needs review
- PR 642, GPT-4.1 structured output
  - tied somewhat to 640 in terms of ordering, not a hard dependency but makes sense to sequence them
- PR 643, CuratorResponse object
  - early but moving

## WS-050 Batch Mode (with Emil)

Ongoing work here. Emil is taking the lead on some of the infrastructure side, I'm handling the API layer and how cost gets surfaced. Not blocked but there are open questions I havent pinned down yet (see below).

## Gemini 2.0 / 2.5 API Incompatibility

Triaged this. The short version is that there's a breaking difference in how the Gemini 2.0 and 2.5 APIs behave compared to what we currently expect, but it doesnt block anything in the current sprint. Moved to backlog as non-blocking. We'll need to come back to it before doing a serious Gemini push.

## Cost-Streaming Pattern, Needs Docs Before Next Sprint

I want to flag this before we get into next sprint's provider work. The cost-streaming pattern we're using
```

> **Problems:** longer than one remark

#### `g6.r2.g6r2-s2-l2` — scope

**nikolai**, 2025-06-18, thread:new|g6.r2.g6r2-s2-l2

> same story with inference.net the number on their pricing page is already what a batch job costs so theres nothing left to take off it

*What a reader should take from it:* the team agrees the inference.net processor never discounts either

*Step it builds toward:* `g6.r2.g6r2-s2` — The factor is only returned where the pricing data is a list price: `batch_multiplier()` gives 1.0 outside batch mode and 1.0 on the klusterai and inference.net processors in every mode, and `resolve_model_price` discounts a `source == "litellm"` price while returning a `source == "external"` price exactly as the table lists it.

*Drafted as:* same story with inference.net: the number on their pricing page is what a batch job costs, there is nothing left to take off it.

*Why there:* Neither thread is about pricing. The Jun 9 recap is a status note on Dario's multimodal Gemini batch *request creation* fix and whether PR 653 should be closed heading into maintenance mode — nobody there has raised cost, discounts, or a price table, so "same story with inference.net" would be answering a question that room never asked, and the "same story" would have no antecedent. The Docker image pinning thread is further off still: it is about backend_params={'image': ...}, failure behaviour at create, and read-only workspace mounts. The remark needs a room where somebody has just said that one processor's batch price equals its list price and the code is nonetheless applying a discount to it; that conversation does not exist in the corpus yet.

*Still leaves open:* What should happen for models priced out of litellm, and how the code tells the two cases apart.

*Must appear literally:* `inference.net`

*A new thread — **batch cost estimates: the 50% discount is being applied to every processor**, 2025-06-18:*

```
From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


```

### g6.r2.g6r2-s3 — A price the user supplied themselves is never discounted: `batch_multiplier()` returns 1.0 whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount, and which processors are exempt is decided by a class-level flag and by which source answered the lookup.

*Nobody says:* A number a user typed in is the number they were quoted, not a list price we are entitled to mark down; and the exemption has to be a property of the processor rather than a string check buried in the arithmetic.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g6.r2.g6r2-s3-l1` — exclusions_or_crossover

**konrad**, 2025-04-03, #cookbooks

> @Emil worth one, yes. A cookbook user put their negotiated input cost straight in the config and the batch run reported half of what they typed.

*What a reader should take from it:* the team agrees an explicit user-supplied input cost is currently being discounted in batch mode

*Step it builds toward:* `g6.r2.g6r2-s3` — A price the user supplied themselves is never discounted: `batch_multiplier()` returns 1.0 whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount, and which processors are exempt is decided by a class-level flag and by which source answered the lookup.

*Drafted as:* a cookbook user put their negotiated input cost straight in the config and the batch run reported half of what they typed.

*Why there:* At 16:05 Emil asks whether a cookbook example for batch mode is planned or out of scope for the milestone, and nobody answers him — the thread just drifts to CI and the SimpleStrat run. Konrad owns the cookbooks pass and is the one fielding user reports on the examples, so him answering Emil with a concrete thing a cookbook user hit in batch mode is exactly the reply that question was waiting for. It also sits naturally beside Dario's earlier "user pointed the executor at a custom image and lost the CSV" report — this channel already trades in user-hit-a-sharp-edge anecdotes. Nothing said that day covers cost estimation, so it isn't redundant, and it stops short of saying what the estimate should have shown or how the code should detect an explicit cost.

*Still leaves open:* What the estimate should have shown, and how the code knows to leave that number alone.

*Must appear literally:* `config`

*Goes into the real conversation in #cookbooks on 2025-04-03, after 16:05 emil:*

```
09:00  konrad: SimpleStrat recipe merged, so I want to make sure the example actually runs end to end and that the shape lines up with RAFT before we cut the next re
09:00  konrad: Haven't confirmed CI is exercising it yet either
09:37  nikolai: I'm on the CI side of this, haven't confirmed the recipe gets exercised yet but I'm looking at it this morning.
09:37  nikolai: Looked for WS-047 in the wiki and there's no page for it yet. @Nils, has that spec been written up anywhere?
10:09  konrad: @Nikolai if it's not covered, could you open a PR to add it?
10:09  konrad: I'll handle the end-to-end run on the example itself and confirm the shape is right
10:46  nikolai: sounds good, I'll open one
12:52  emil: @Konrad when you say the shape lines up with RAFT, are you checking against the distractor format specifically or just the overall generation structur
13:14  konrad: I was checking overall generation structure, but if there's a distractor format spec somewhere I should be checking against that too, do you have it h
14:54  dario: Pointed CodeExecutor at a custom image to stop pip installing pandas per task, and the generated solution just rewrote the input CSV sitting in the mo
14:54  dario: Lost the whole afternoon to it.
14:54  dario: Original CSV's gone too, no backup.
14:54  dario: Same script errors on write with the stock image
14:58  emil: Has the SimpleStrat example been confirmed runnable yet, or is that still on Konrad's list for this afternoon?
15:22  nikolai: The workspace mount write behavior Dario described is consistent with how CodeExecutor works, writable with a custom image, errors with the stock one
15:22  nikolai: I'll get the CI PR up before end of day
16:05  emil: Pulled up WS-050 - it covers the batch mode design pretty thoroughly, the submit/poll/fetch cycle and where state needs to be written. Is there a cook   <-- THE REMARK GOES HERE
16:13  dario: Around for the rest of the afternoon if anything comes up.
16:24  dario: Did Konrad get back on the SimpleStrat run yet, or is that still coming?
16:50  dario: Has the CI PR gone up yet?
17:32  konrad: Example runs clean end to end
17:32  konrad: For the distractor format question I was asking about earlier, I ended up cross-checking against the original RAFT paper (the domain-specific RAG one,
18:04  nikolai: CI PR isn't up yet, still on it
18:13  dario: @Nikolai any chance that goes up tonight or is it a tomorrow thing?
18:21  nikolai: Tonight.
```

#### `g6.r2.g6r2-s3-l3` — exclusions_or_crossover, rule

**dermot**, 2025-04-08, thread:new|g6.r2.g6r2-s3-l3

> reading the cost path in 565 — we're picking who gets the batch discount with an if-chain on provider names inside batch_multiplier, that belongs on the class as a flag instead.

*What a reader should take from it:* the team agrees the exemption is carried by a class-level flag on the processor

*Step it builds toward:* `g6.r2.g6r2-s3` — A price the user supplied themselves is never discounted: `batch_multiplier()` returns 1.0 whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount, and which processors are exempt is decided by a class-level flag and by which source answered the lookup.

*Drafted as:* we're picking who discounts with an if-chain on provider names inside batch_multiplier, that belongs on the class as a flag instead.

*Why there:* None of the three rooms is discussing batch pricing. The concurrency mail is a two-person OOM repro thread; the v0.1.21 mail is dermot's own release announcement about unicode and token-count wrapping, where a design decision would be alien; dario's weekly recap is a status roll-up, and dermot answering it with a review finding on someone else's method inverts the direction of that thread. The remark is a review comment that settles where the exemption lives, so it needs the review itself. Dario's recap says PR 565's remaining edge cases are "error handling and cost reporting" — the thread that should exist is dermot's review of that cost path the next day, with dario and emil (who owns the gemini batch side, ws-050) on it, covering where the discount applies relative to token estimation and what a new processor defaults to.

*Still leaves open:* Which providers set the flag, and what the method returns for the ones that do.

*Must appear literally:* `batch_multiplier`

*A new thread — **PR 565: cost reporting before it lands**, 2025-04-08:*

```
From: None  To: 


From: None  To: 


From: None  To: 


```

> **Problems:** longer than one remark

#### `g6.r2.g6r2-s3-l2` — exclusions_or_crossover

**nikolai**, 2025-06-10, page:engineering/cost-estimates-in-batch-mode-where-the-price-numbers-come-from.md

> if the price per million came from the user then thats already the number they pay so batch mode shouldnt be knocking anything off it either

*What a reader should take from it:* the team agrees a user-supplied per-million price is passed through unchanged even in batch mode

*Step it builds toward:* `g6.r2.g6r2-s3` — A price the user supplied themselves is never discounted: `batch_multiplier()` returns 1.0 whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount, and which processors are exempt is decided by a class-level flag and by which source answered the lookup.

*Drafted as:* if the number came from the user it is already the number they pay, so nothing should come off it in batch mode either.

*Why there:* None of the eight rooms is chewing on pricing at all. The closest is the cost-reporting section of the handover, but that page is explicitly about numbers coming back from provider headers and bodies (issue 293, issue 207) — a user-supplied per-million price and a batch discount are never raised there, and batch mode isn't Nikolai's surface on that page. The Jun 23 batch sync is the right room for "batch mode" but is entirely rate limits, PR 690 and v0.1.26 readiness; a pricing ruling would change the subject and draw no reply. The remark is a settled decision out of a design discussion about the price lookup and where the batch discount gets applied, and that discussion doesn't exist yet in the corpus. It should have been a short engineering page once someone noticed a batch estimate coming in at half the price the caller configured, with Nikolai (online-request-processing, cost reporting) and Emil (batch-mode) on it, covering the discount table, which providers never discount, and what happens to an explicit override.

*Still leaves open:* Where that check lives, and how it interacts with the providers that already never discount.

*A new page — **Cost estimates in batch mode: where the price numbers come from** in `engineering`, 2025-06-10:*

> **why this page exists**

> 2025-06-10
> 
> A user reported their batch cost estimate came back at exactly half the per million price they had configured themselves and asked if that was a bug
> 
> I went looking for something to point them at and there is nothing written down anywhere about how a price gets picked so this is that page
> 
> This is not a spec it is what the code does today on v0 1 25 - if we change the behaviour later this page needs to change with it

> **the two paths a price can come from**

> There are exactly two ways a per million price ends up in an estimate
> 
> - **lookup path** - we hand the model id to the pricing map and get back `input_cost_per_million` and `output_cost_per_million` - these are published list prices for the hosted providers
> - **caller supplied path** - the user passes the prices in directly - usualy because the model is self hosted or the map is stale for a new model or they have negotiated pricing that is not public
> 
> The lookup only runs when nothing was supplied - caller supplied always wins and we never merge the two or fall back from one to the other
> 
> If the lookup misses and nothing was supplied there is no estimate at all - we skip it rat

> **the batch discount** **← carries the remark**

> Batch mode applies a 0 5 multiplier to prices that came out of the lookup path
> 
> The reason is that the map holds the synchronous list price and openai and anthropic both bill batch work at half of that so halving the looked up number gets the estimate close to what the invoice actualy says
> 
> The multiplier does not apply to caller supplied prices - if the number came from the user it is already the number they pay so nothing should come off it in batch mode either - we have no way of knowing whether they typed in a list price or their negotiated batch rate and halving it would be us inventing a discount on top of one they may have already accounted for
> 
> So the 0 5 belongs to the l

> **checking a number that looks wrong**

> In order
> 
> 1. confirm which path the price came from - was anything passed in by the caller or did we look it up
> 2. if it was looked up check the raw map entry for that model id - compare against the providers public page since the map goes stale
> 3. if it was looked up and we are in batch mode expect half the list price - that is working as intended not a bug
> 4. if it was caller supplied expect the number back unchanged in both sync and batch
> 5. only then look at token counts - most of the reports that come in as pricing bugs are actualy estimated token counts being off not the per million rate

> **open / rough edges**

> - the 0 5 is hardcoded - it is right for the two big providers right now but it is not a universal batch rate and we will hit a provider where it is wrong
> - nothing in the output says which path a price came from - if the estimate printed that it would have answered the users question without anyone reading the code - i mean this is probably the cheapest fix on the list
> - no idea off the top of my head what we do for a model that is in the map with only an input price and no output price - gotta think through that one and write it down here when i know

### g6.r2.g6r2-s4 — The factor is a fixed one half, observable as `batch_multiplier()` on the base and Azure processors in batch mode and 1.0 out of it, 1.0 on klusterai and inference.net even in batch mode, and as `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` matching its `batch=False` value while a litellm-sourced model's halves.

*Nobody says:* If both the processor method and the resolver are meant to use one factor, the way you show they do is to compare the two prices they hand back for the same model.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g6.r2.g6r2-s4-l3` — observability, scope

**nils**, 2025-03-25, #pipeline

> on the adding side, my batch test pins resolve_model_price(m, provider="klusterai", completion_window="*", batch=True).input_cost_per_million at 4.0, same float as batch=False. same test, source == "litellm" halves input_cost_per_million and output_cost_per_million both.

*What a reader should take from it:* the team agrees the resolver's batch prices are checked against the non-batch ones per source

*Step it builds toward:* `g6.r2.g6r2-s4` — The factor is a fixed one half, observable as `batch_multiplier()` on the base and Azure processors in batch mode and 1.0 out of it, 1.0 on klusterai and inference.net even in batch mode, and as `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` matching its `batch=False` value while a litellm-sourced model's halves.

*Drafted as:* putting an assert in the tests: klusterai's per-million with batch=True equals the batch=False one, and a litellm-priced model comes back exactly half.

*Why there:* That thread is nils accounting for what's in and out of the batch test suite — he asked at 10:53 whether batch tests are generic or provider-specific, and at 13:12 he's showing the fixture tests he plans to drop. A line naming the assert he's adding on the batch-price side lands as the other half of that ledger, from the person who owns the batch PR, and it leaves open why the two models diverge and where else the comparison lives.

*Still leaves open:* Why those two models differ, and where in the processors the same comparison shows up.

*Must appear literally:* `"*"`, `4.0`, `batch=False`, `batch=True`, `completion_window`, `completion_window="*"`, `input_cost_per_million`, `klusterai`, `litellm`, `output_cost_per_million`, `provider="klusterai"`, `resolve_model_price`, `source`, `source == "litellm"`

*Goes into the real conversation in #pipeline on 2025-03-25, after 13:12 nils:*

```
09:00  nils: Mistral batch processor is up in PR 584. I did pull out some of the Mistral-specific tests as part of the refactor, and I want to make sure we're not 
09:39  nils: Does anyone know what tests actually got removed in the Gemini example refactor? I want to make sure we're not already thin on provider coverage beofr
10:19  nils: what does PR 585 actually change on the retry side - does it cover batch submissions or just online requests?
10:53  nils: does the batch test suite cover providers generically or is each test provider-specific?
12:42  emil: I went through the Gemini example refactor and the tests that got pulled were tied to the example setup, not the core provider path, so coverage shoul
12:56  emil: I pulled up WS-047 and it doesn't seem to exist yet as an issue
12:56  emil: Is that still on Nils to open, or did it land somewhere else?
13:12  nils: good to know on Gemini. the Mistral tests I'm planning to drop look like this - all fixture-based, nothing hitting a real endpoint:

```python
def tes   <-- THE REMARK GOES HERE
14:10  dario: fair enough
14:48  emil: WS-047 doesn't show up anywhere in the issues
14:48  emil: @Nils, is that still getting written, or has it stalled?
15:09  nils: hasn't stalled, I just have no scope to work from. I'll write it up from scratch this afternoon, but someone should shout if it needs to match somethi
15:52  emil: Does anyone actually know what it was originally supposed to cover, or is Nils genuinely starting from a blank slate here?
16:08  dario: Provider-integrations test coverage is still solid after those fixture removals, nothing hitting a real endpoint got pulled.
16:44  nils: good on the coverage - I'll go ahead and drop the Mistral fixture tests from provider-integrations
16:44  nils: That's the last open question on my side for this PR
16:49  emil: Is fixture coverage enough to sign off on 584, or does anyone want an integration pass before it merges?
16:54  dario: makes sense
17:29  emil: @Nils, do you want someone to review 584 before end of day, or is it ready to merge once the fixture tests are dropped?
17:31  nils: review before merge, yes - implementation hasn't had eyes yet
17:32  nils: anyone able to take a look at PR 584 first thing tomorrow?
17:45  dario: I can take a look at 584 tomorrow, it's in my area anyway.
18:20  emil: Are we all in agreement that provider test coverage is still solid after the Gemini example cleanup and now the Mistral fixture removals?
18:20  emil: Actually, Dario already confirmed coverage is solid earlier in this thread
18:20  emil: Is that enough to green-light 584 once the fixture tests are out, or do we want a second opinion first?
```

> **Problems:** longer than one remark

#### `g6.r2.g6r2-s4-l1` — observability, rule

**gideon**, 2025-04-03, #pipeline

> so basically batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure, tbh one number for both. outside batch mode both hand back 1.0.

*What a reader should take from it:* the team agrees the discount factor is a single fixed one half shared by the base and Azure processors

*Step it builds toward:* `g6.r2.g6r2-s4` — The factor is a fixed one half, observable as `batch_multiplier()` on the base and Azure processors in batch mode and 1.0 out of it, 1.0 on klusterai and inference.net even in batch mode, and as `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` matching its `batch=False` value while a litellm-sourced model's halves.

*Drafted as:* Batch is 50% off list on openai and on azure alike, there is one number in this and it isn't per-provider.

*Why there:* No listed room is working the batch pricing path. The nearest, code-review 2025-03-18, has Gideon on a cost-estimation blindspot, but that thread is about the output-token cap and the undefined batch processor interface — a fixed discount constant answers nothing anyone there asked and would get no reaction. pipeline 2025-04-21 mentions cost only as rhetoric ("a duplicate batch is a few dollars") and is settled on mismatch keys. The remark needs a thread where the batch cost calculation is being wired, with a sibling deciding which processors and sources qualify; that thread doesn't exist yet. It follows naturally from Gideon's 2025-04-01 "starting to look at what I need from the batch side" and the postmortem's still-open batch-mode cost audit.

*Still leaves open:* Which processors and which sources are entitled to that 50% at all.

*Must appear literally:* `0.5`, `1.0`, `50%`, `azure`, `batch_multiplier()`

*A new conversation in #pipeline on 2025-04-03:*

```
14:18  dermot: costing question while i'm in here - for a batched run, where does the discount get applied? we don't do it in the caller do we
14:21  gideon: so basically the base cost processor has a batch_multiplier(), and in batch mode it comes back 0.5. the 50% is the whole of it, nothing else to apply
14:23  dermot: so on a normal sync run it just doesn't get called at all?
14:24  gideon: no it still gets called, you just get 1.0 back. um, same arithmetic either way which is nice
14:26  dario: what about azure though, i had it in my head their batch discount was a different figure
14:27  gideon: ya i went and looked. azure is 0.5 as well, tbh one number for both, i was expecting to have to carry two
14:29  dermot: and azure outside batch mode, 1.0 the same as the other one
14:30  gideon: exactly, both hand back 1.0 there
14:32  dario: ok, so no per provider special casing. i had half a branch written for that, going to bin it before someone finds it
```

> **Problems:** longer than one remark; claims verbatim '50%' but does not contain it

#### `g6.r2.g6r2-s4-l2` — observability

**emil**, 2025-06-25, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md

> On pricing: azure's batch_multiplier() keeps drifting from the base processor's; we agreed identical in and out of batch mode, with cost() just scaling the resolved price by self.batch_multiplier().

*What a reader should take from it:* the team agrees the Azure processor reports the same factor as the base processor in and out of batch mode

*Step it builds toward:* `g6.r2.g6r2-s4` — The factor is a fixed one half, observable as `batch_multiplier()` on the base and Azure processors in batch mode and 1.0 out of it, 1.0 on klusterai and inference.net even in batch mode, and as `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` matching its `batch=False` value while a litellm-sourced model's halves.

*Drafted as:* azure keeps drifting from the base processor whenever someone edits one of them, they should be reporting the identical factor in batch mode and the identical one outside it.

*Why there:* This is emil's own batch-mode sync, written the week auto batch mode (PR 691) is declared ready for v0.1.26. Auto batch mode is exactly the feature that has to compare batch vs non-batch cost, so the state of the per-provider factors is live in that room, and emil owns the batch processors. The page currently says "no blockers" and lists deferred items, so a short note recording a settled point about the azure processor tracking the base processor sits naturally under Status without changing the subject. It stops short of naming the factor or the two providers with their own tables, which the sibling remark supplies.

*Still leaves open:* What that factor is, and what the two providers with their own tables report.

*Must appear literally:* `batch_multiplier()`, `cost()`, `self.batch_multiplier()`

*Goes as a section in the real page `meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`, at: ## Status:*

```
# Weekly sync notes: week of Jun 23 (batch mode)

## Status

Auto batch mode is ready to ship in v0.1.26. No blockers.

PR 690 (Fix Multimodal Gemini Batch Request Creation) is in review as of today. Nothing holding it up that I'm aware of, just needs eyes.

## Open items (deferred past v0.1.26)

- Issue 233 (rate limit detection): still unresolved, punting past this release
    - we talked about this last week too, not sure there's a clean answer yet
- Issue 207 (has_capacity implementation): same situation, deferred
    - TBD on who picks these up and when, lets circle back once 0.1.26 is out

## Also in flight

Local offline inference, same ownership. Didnt get deep into it this sync but its moving.

## Questions

- Is anyone tracking 233 and 207 for the next milestone or are they just sitting in the backlog?
```

### Herrings — believed at the time, overturned later

#### `g6.r2.batch-discount-uniform-then-cancel-1` — herring

**dario**, 2025-01-27, #pipeline

> went and looked - settled: the base cost processor halves every source, and klusterai/inference.net multiply their cost() by 2 to cancel it, their tables are already batch-tier

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* settled: the base cost processor halves every source, and klusterai/inference.net multiply their cost() by 2 to cancel it, since their tables are already batch-tier.

*Why there:* That thread is already on exactly this: emil flags at 16:19 that "the cost calc only accounts for OpenAI batch right now, not Gemini," and dario's own 16:34 question is whether other batch backends have the same gap. The remark is dario coming back with the answer to his own question — where the batch discount actually lives (uniformly in the base cost processor) and which providers have to undo it. Dario answering his own open question later in the day is a pattern he already shows on 2025-02-17. Nobody in the thread has made this point yet, so it isn't redundant, and it doesn't resolve emil's separate generation-params question.

*Goes into the real conversation in #pipeline on 2025-01-27, after 16:34 dario:*

```
09:00  emil: PR 403 is mostly through, the Gemini batch processor itself is wired up, but generation params aren't making it into the batch path yet
11:19  dario: Where's it breaking, is the params not getting passed into the batch request at all, or are they going in and just getting dropped before the actual c
11:19  dario: Actually, in the Gemini batch path, when are the generation params supposed to get serialized into each batch entry, at submission time or when PR 403
16:19  emil: Good question, I haven't gotten far enough in to answer that yet. Will dig into it tomorrow morning.
16:19  emil: Also, if we're touching the batch path anyway, I'm pretty sure the cost calc only accounts for OpenAI batch right now, not Gemini.
16:34  dario: Read Konrad's weekly just now, it's got both the param-passing block and the cost calc gap already flagged
16:34  dario: On the cost calc thing Emil mentioned, is it just Gemini that's unaccounted for or are there other batch backends with the same gap?   <-- THE REMARK GOES HERE
```

#### `g6.r2.batch-discount-uniform-then-cancel-2` — herring

**konrad**, 2025-01-27, #engineering

> @Dario discount stays in the base, providers whose table already lists batch prices cancel it with a x2 in their own cost() override, klusterai and inference.net both do this

*A herring: stated as settled at the time, overturned later (from 2025-03-19).*

*Drafted as:* Reminder for reviewers: if a provider table already lists batch prices, the fix is the x2 in that provider's cost() override. The discount itself stays in the base.

*Why there:* Konrad opened this exact question at 10:21 — whether batch cost calc is one shared formula or per-backend estimates — and Dario reposts it unanswered at 18:28 alongside the PR 403 batch path work Konrad flagged at 09:00. The remark is the answer nobody had given: the discount lives in the base, providers whose tables already list batch prices cancel it in their own cost() override. Nothing in the day makes it redundant, and Konrad closing out a thread he started matches how he behaves elsewhere.

*Goes into the real conversation in #engineering on 2025-01-27, after 18:28 dario:*

```
09:00  konrad: Weekly update for the week of Jan 20 just went out to the team
09:00  konrad: v0.1.16 shipped, but PR 403 is still stuck, params aren't routing through the Gemini batch path and cost calc doesn't cover all batch backends yet
09:13  konrad: @Emil for PR 403, are the generation params supposed to pass through as part of the request body on each batch item, or do they get set once at the jo
10:21  konrad: Does anyone know if the cost calc for batch is supposed to handle all backends with a single formula, or is each backend expected to provide its own c
11:13  konrad: @Emil did anyone validate PR 406 after it merged, or did it go in without a post-merge check?
16:38  dario: Params are going out from provider-integrations fine, they're just not making it into the batch entries in PR 403.
18:28  emil: gotcha
18:28  dario: Read the weekly, it flags the param routing as needing eyes from my side but doesn't go further on cost calc scope
18:28  dario: Is each batch backend expected to provide its own cost estimate, or is there supposed to be one shared formula?   <-- THE REMARK GOES HERE
```

#### `g6.r2.rev1` — rule, scope

**dario**, 2025-04-14, #pipeline

> batch stats: two layers each halving is why estimates came in at a quarter of the invoice. batch_multiplier() is the only place that factor lives now, 1.0 on klusterai and inference.net, no cost() override.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the halve-every-source-then-multiply-back-by-2 setup is gone — two layers each taking 50% is why batch estimates came in at a quarter of the invoice. batch_multiplier() is the only place the factor lives now, and it returns 1.0 on klusterai and inference.net; no cost() override multiplies anything.

*Why there:* That room is already on cost metadata and the projected-total / projected-remaining readouts, with batch statistics flagged as checkpointed but not validated; dario explicitly takes batch stats for the afternoon at 11:50 and owns the request layer where the cost math lives. A double-applied batch discount that makes estimates land at a quarter of the invoice is exactly what "validate batch stats" turns up, and nobody there has made this point yet — gideon's earlier question is about whether providers return cost data at all, not about how the discount is applied. The 03-26 thread is the nearer topic but everything there is deferred and unresolved, so a settled "this is fixed" report would land as a subject change.

*Must appear literally:* `batch_multiplier()`, `cost()`, `klusterai`, `inference.net`

*Goes into the real conversation in #pipeline on 2025-04-14, after 11:50 dario:*

```
09:00  gideon: Projected-total and projected-remaining readouts are in good shape after the last two commits, I think they're ready for someone to poke at
09:00  gideon: Batch statistics account is checkpointed too if anyone wants to validate that side
09:38  dermot: bulk-llm-inference is stable on my end
09:50  gideon: Is cost metadata coming back consistently from the provider backends, or are there gaps depending on which one you're hitting?
09:50  gideon: @Dermot, weekly notes for this week - are those going up today?
10:20  dermot: weekly notes are up in the engineering section of the wiki
10:21  dermot: the cost metadata question is the open one I put in there, @Dario, that one's probably yours to answer given where the request layer lives
10:40  gideon: thanks Dermot
10:53  dario: Depends which angle you're asking from - are you asking whether the providers actually return cost data at all (some don't, or return it inconsistentl
10:54  dario: @Gideon, you free this afternoon to go through the cost metadata question?
11:23  gideon: Yeah, this afternoon works. Both angles honestly, but the handoff side is the more pressing one for me right now
11:26  emil: PR 626 metadata schema is merged-ready on my side, just waiting on PR 632 to land first so the ordering doesn't bite us.
11:29  gideon: Pulled up the weekly notes, batch statistics account is flagged there as checkpointed but not validated
11:29  gideon: @Dario, is that on your plate for this afternoon or does someone else need to pick it up?
11:50  dario: Yeah I can take batch stats this afternoon.
11:50  dario: Provider integrations side for cost work is still the open piece - I want to get to that in our sync too, not sure we'll land it today but it shouldn'   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

#### `g6.r2.rev2` — rule, scope, exclusions_or_crossover

**konrad**, 2025-06-03, #engineering

> Also scratch my reviewr note about the x2 in the provider's cost() override, those overrides are deleted. Where a table already lists batch prices, batch_multiplier() returns 1.0 and resolve_model_price leaves the external-sourced price as listed.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* Scratch my old reviewer note about fixing this with the x2 in the provider's cost() override — those overrides are deleted. If a table already lists batch prices, batch_multiplier() returns 1.0 there, and resolve_model_price leaves an external-sourced price exactly as listed.

*Why there:* That day's thread is the one place pricing is live: konrad opens with his cost-safety fix, the room asks at 13:33 whether guarding at the pricing lookup is enough, and at 18:18 he reports the guard on the pricing lookup is in and unknown models return None cleanly. A retraction of his own earlier reviewer note about handling batch pricing with an x2 in the provider cost() override slots into that same burst — it's his subsystem, his note, and nobody else has said where batch pricing gets handled.

*Must appear literally:* `batch_multiplier()`, `cost()`, `resolve_model_price`

*Goes into the real conversation in #engineering on 2025-06-03, after 18:18 konrad:*

```
09:00  konrad: Cost-safety fix on the finetuning side is in, and I want to make sure we're aligned on the safeguard approach before anything else moves forward today
09:00  konrad: Happy to walk through it with whoever has eyes on the broader dormancy plan
09:18  nikolai: PR 663 is my piece of that picture on the code-execution side, torch safety fix, and I want it in before we call dormancy locked
09:49  konrad: Nikolai, what does the fix actually do when torch isn't present, does it fall back cleanly or just skip the import?
10:08  nikolai: Around this morning if you want to walk through it together rather than back-and-forth in comments
10:34  konrad: Quick call or just a thread where we can drop code?
11:03  nikolai: call works
12:10  emil: Does PR 663 guard just the import, or does it also cover any torch calls further down the stack?
12:50  emil: PR 683's litellm structured-output detection hasn't been validated against actual provider responses, and it's sitting without a reviewer.
13:17  konrad: @Emil, for PR 683, what would a validation against actual provider responses actually look like?
13:18  konrad: Is there a test setup already or would someone need to wire one up?
13:33  konrad: Are we aligned that guarding at the pricing lookup is enough, or does the viewer need its own layer on top?
14:02  konrad: Nikolai, did anything come up from the call that changes the picture on PR 663?
14:18  nikolai: That provider-validation gap in PR 683 is a real find, @Emil, that's exactly the kind of thing that bites you on a provider you haven't tested against
15:01  emil: Which providers are you thinking, the ones litellm supports but we haven't actually run against, or something more specific?
15:09  emil: Has anyone actually run the litellm structured-output detection in PR 683 against a real provider response, or is it untested so far?
15:37  nikolai: The guard in PR 663 only covers the import
15:52  emil: @Dario, you own code-execution, worth a look at whether the torch guard in PR 663 needs to extend past the import before it merges.
16:22  emil: Anyone know why the litellm structured-output check in PR 683 would return inconsistent results on the same provider across runs?
16:49  nikolai: That's my subsystem, not Dario's - I already surfaced the guard gap on 663 and I'm extending it past the import now
17:13  konrad: With 663's guard getting extended and 683 still unresolved, are we actually able to call all three fixes safe today, or is that slipping?
17:48  nikolai: Guard extension on PR 663 is done and I've pushed the update, so that one's ready for eyes when someone has a chance.
18:09  emil: If PR 683 isn't getting reviewed today, we could at least mark it explicitly as post-dormancy so it's not just floating.
18:09  emil: PR 683 is open and unreviewed, calling it explicitly post-dormancy for now, will pick it back up after the milestone.
18:18  konrad: Cost fix on my end is solid, the guard on the pricing lookup is in and unknown models return None cleanly   <-- THE REMARK GOES HERE
18:19  konrad: With 663's guard now extended and 683 explicitly deferred, the two active fixes look sound to me
18:19  nikolai: 663 is updated but nobody's actually reviewed the extension yet, dunno if "sound" is quite the right word before that happens.
18:19  emil: Right, "sound" and "reviewed" are two different things.
18:19  emil: Someone should take a look at the updated PR 663 before we call torch safety confirmed, Nikolai pushed the guard extension and it needs actual eyes on
```

> **Problems:** longer than one remark

### the klusterai provider table carries one input rate of 4.0 per million, filed under completion_window "*" — *(no such subconclusion)*

#### `g6.r2.fix18` — observability

**nikolai**, 2025-04-07, #engineering

> for the record the klusterai row in pr 622 is 4.0 per million input straight off their pricing page. no window split on their table at all it just sits under "*"

*What a reader should take from it:* the team agrees klusterai's table lists 4.0 per million input under a single wildcard completion_window entry

*Drafted as:* for the record the klusterai row we test against is 4.0 per million input, straight off their pricing page — theres no window split on their table, it all sits under "*".

*Why there:* That day nikolai owns PR 622, which is exactly the klusterai model list update, and the room is closing out ws-050 — the 50%-cost async batch workstream Emil just wrote the wiki page for. A note about what klusterai's own table actually lists (a single "*" completion_window row at 4.0 per million input) lands right where the batch-discount question is live: it pins what the source data says without touching what the resolver does with it under the batch flag. Nikolai is the natural author since 622 is his and he's been the one nudging for the ws-050 page before calling it closed. Slight stretch in that pricing rows hadn't been named explicitly yet in the thread, but they sit inside the model list change he's landing.

*Still leaves open:* what the resolver does with that row when the batch flag is set — whether 4.0 survives it, or gets scaled — which only nils's test pins down

*Must appear literally:* `klusterai`, `4.0`, `"*"`

*Goes into the real conversation in #engineering on 2025-04-07, after 16:20 emil:*

```
09:00  nikolai: Ws-053 is done on my end, PR 622 merges cleanly
09:00  nikolai: klusterai model list update and the llama4 additions are ready to land
09:44  dermot: ws-055 design is on the wiki now (WS-055: Release Engineering, CI & Test Suite). before I lock the integration test scope in it, is ws-050 fully close
10:37  dermot: so are we set to kick off ws-055 tomorrow?
10:46  dario: PR 565 is in decent shape, openai backend mostly there and I'm working through a couple of edge cases this morning
10:46  dario: on ws-050, I'd want to hear from Emil before saying it's closed, I'm not sure myself if there's still a third gemini bug in play
11:33  emil: nice on 053
11:53  emil: from my end ws-050 is the finish reason fix (PR 621) and the cancellation bugs in 614, I don't have a third thing in my queue
11:53  emil: I tried to pull up the ws-050 wiki page and it doesn't exist yet, so I honestly can't say with full confidence we've captured everything - not ready t
12:28  dermot: fair.
12:29  dermot: read the weekly update, ws-050 is still flagged as open in it. are we settling that today or leaving it?
13:06  emil: PR 621 is pretty targeted, just this in the gemini batch path:
```
"finish_reason": candidate.get("finishReason", "STOP").lower()
```
if that's the fu
13:47  dario: if that's the scope, I'd say merge PR 621, let PR 614 land when dermot flags it, and close ws-050. PR 622 can follow once those are clear.
14:31  emil: sounds right. does ws-055 still kick off tomorrow now that the design's on the wiki?
14:54  dario: design's on the wiki so tomorrow should be on, but dermot would know if anything's still gating it on his end.
15:34  emil: WS-050 doesn't have a wiki page - tried to pull it up and it's not there.
15:34  emil: is that on someone's list, or does it get written when the workstream formally closes?
15:37  dermot: nice, that fix is clean. ws-055 is on for tomorrow, nothing gating on my end. the design also records the cache layout: the run fingerprint hashes the
15:38  dermot: read the weekly update, ws-055 is in there and my part looks covered. is ws-047 also wrapping this week or still in flight?
15:59  nikolai: @Emil can you write the ws-050 wiki page before we call it closed
15:59  nikolai: pr 622 is ready whenever 621 and 614 land
16:20  emil: wrote the ws-050 wiki page, it's up in engineering now (WS-050: Batch Mode (50%-Cost Async Batch APIs))
16:20  emil: PR 621 and 614 still need to land to fully call it done   <-- THE REMARK GOES HERE
16:54  dario: PR 565 is nearly there, finishing up the last bits on error handling this afternoon and I expect it ready for review tomorrow
```

> **Problems:** longer than one remark; names no known subconclusion

