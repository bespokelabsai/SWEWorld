# g6 — Unified model price resolution

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries.

| arm | what it is handed |
|---|---|
| `blind` | the ticket |
| `spec` | the ticket + both hidden requirements |
| `clues` | the ticket + all 33 remarks, quoted |
| `world` | the ticket, against `sweworld:0.4.4` where the 33 remarks live in chat, the wiki and mail |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Each is graded as five independent facts, 0.1 each. `open_feature` carries weight 0.0: building the feature scores nothing, only recovering what nobody wrote down does.

### `g6.r1`

- **`rule`** — `resolve_model_price` never returns a `ModelPrice` carrying a `None` price: every failure raises `UnpricedModelError`, and the `reason` it carries is exactly one of the three strings `unknown_provider`, `unknown_model`, `unknown_window`.

- **`exclusions_or_crossover`** — An unregistered provider is `unknown_provider` even when the model is also absent and the window is also unrecognised, and a missing model key is `unknown_model` even when the window is also unrecognised. A model present in `litellm.model_cost` but carrying a missing or `None` input price is `unknown_model`, and a window that is absent from a model's price map is `unknown_window` rather than a fallback to the wildcard tier.

- **`observability`** — `resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")` raises with `reason == "unknown_provider"`; the same call with a registered provider raises with `reason == "unknown_model"`; a model that provider does list, asked for an unlisted window, raises with `reason == "unknown_window"`. Every `cost()` method and both trackers catch `UnpricedModelError` and degrade — `cost()` to `0.0`, a tracker to `None` prices and a recorded reason.

### `g6.r2`

- **`rule`** — The batch discount factor is applied by exactly one method, `batch_multiplier()`, on the cost processors; no `cost()` override multiplies or divides its result by anything. `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

- **`scope`** — `batch_multiplier()` returns the discount factor only where the pricing data is a list price: it returns `1.0` when the processor is not in batch mode, and `1.0` on the klusterai and inference.net processors in every mode. `resolve_model_price` discounts a `source == "litellm"` price and leaves a `source == "external"` price exactly as the table lists it.

- **`exclusions_or_crossover`** — A user-supplied per-million price is never discounted: `batch_multiplier()` returns `1.0` whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount. Which processors are exempt is decided by a class-level flag and by which source answered the lookup.

- **`observability`** — `batch_multiplier()` is the discount factor on the base and Azure processors in batch mode and `1.0` out of it, and `1.0` on the klusterai and inference.net processors even in batch mode. `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` equals the `batch=False` value exactly, while a litellm-sourced model's `batch=True` value is exactly half its `batch=False` value.

> *The decision the team made first and later reversed:* the team once applied the fixed batch discount uniformly to every source inside the base cost processor, then had klusterai/inference.net multiply their own result by 2 to cancel it back out because their tables were already batch-tier prices; that compensating multiply was later dropped in favour of one method that simply declines to discount those two providers

---

## Where the remarks are spread

33 remarks in total — 29 clues, 2 herrings and 2 reversals — across 4 surfaces and 4 chat channels. `clues.spread()` reports on this — at least 2 sources, 3 weeks and 2 rooms per requirement, so no single sitting recovers one. It is advisory, not enforced: read the numbers rather than trusting that something refused a plant without them.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **19** | `#pipeline` 10, `#engineering` 5, `#code-review` 3, `#cookbooks` 1 |
| wiki (BookStack) | **7** | 7 page comments |
| mail (Roundcube/IMAP) | **6** | 6 separate threads |
| wiki page body (BookStack) | **1** | `docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md` |

> **The wiki remarks are page _comments_, not page bodies.** BookStack's `/api/search` does not index comments, so a term that lives only in one returns nothing. `/api/pages/{id}` returns them alongside the body — an agent that searches instead of enumerating never sees these 7.

> A page **body**, by contrast, IS indexed — the 1 above answers a BookStack search, and is the wiki carrier an agent can find rather than stumble onto.

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

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


---

## The ticket — stated openly

**Unified model price resolution**

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


---

## Where every remark is

33 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-27 | chat | #pipeline | gideon | [`g6.r2.batch-discount-uniform-then-cancel-1`](#g6r2batch-discount-uniform-then-cancel-1) | 8 | **herring** | — |
| 2025-01-27 | chat | #engineering | dario | [`g6.r2.batch-discount-uniform-then-cancel-2`](#g6r2batch-discount-uniform-then-cancel-2) | 7 | **herring** | — |
| 2025-03-14 | chat | #engineering | dario | [`g6.r1.l4`](#g6r1l4) | 8 | clue | `exclusions_or_crossover`, `observability` |
| 2025-03-19 | chat | #pipeline | emil | [`g6.r2.g6r2-s1-l1`](#g6r2g6r2-s1-l1) | 7 | clue | `rule` |
| 2025-03-21 | chat | #pipeline | dario | [`g6.r1.l6`](#g6r1l6) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-24 | chat | #engineering | nikolai | [`g6.r1.l11`](#g6r1l11) | 8 | clue | `observability` |
| 2025-03-25 | chat | #pipeline | gideon | [`g6.r2.g6r2-s4-l3`](#g6r2g6r2-s4-l3) | 7 | clue | `observability`, `scope` |
| 2025-03-26 | chat | #pipeline | dario | [`g6.r2.g6r2-s2-l1`](#g6r2g6r2-s2-l1) | 7 | clue | `scope` |
| 2025-04-03 | chat | #pipeline | dermot | [`g6.r2.g6r2-s4-l1`](#g6r2g6r2-s4-l1) | 9 | clue | `observability`, `rule` |
| 2025-04-03 | chat | #cookbooks | emil | [`g6.r2.g6r2-s3-l1`](#g6r2g6r2-s3-l1) | 9 | clue | `exclusions_or_crossover` |
| 2025-04-07 | chat | #pipeline | gideon | [`g6.r1.l1`](#g6r1l1) | 9 | clue | `rule` |
| 2025-04-07 | chat | #engineering | dermot | [`g6.r2.fix18`](#g6r2fix18) | 8 | clue | `observability` |
| 2025-04-08 | mail | “PR 565: cost reporting before it lands” | dermot | [`g6.r2.g6r2-s3-l3`](#g6r2g6r2-s3-l3) | 3 | clue | `exclusions_or_crossover`, `rule` |
| 2025-04-14 | mail | “Re: Weekly update: week of Apr 7” | konrad | [`g6.r2.g6r2-s2-l4`](#g6r2g6r2-s2-l4) | 3 | clue | `scope`, `exclusions_or_crossover` |
| 2025-04-14 | wiki comment | docs/releases/v0-1-22-release-notes.md | dermot | [`g6.r2.g6r2-s1-l4`](#g6r2g6r2-s1-l4) | 2 | clue | `rule`, `observability` |
| 2025-04-14 | chat | #pipeline | gideon | [`g6.r2.rev1`](#g6r2rev1) | 9 | **reversal** of `g6.r2.batch-discount-uniform-then-cancel-1` | `rule`, `scope` |
| 2025-04-15 | chat | #pipeline | dermot | [`g6.r2.g6r2-s1-l2`](#g6r2g6r2-s1-l2) | 8 | clue | `rule` |
| 2025-04-21 | wiki comment | docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md | dermot | [`g6.r1.l2`](#g6r1l2) | 2 | clue | `rule` |
| 2025-04-21 | mail | “Re: Weekly update: week of Apr 14” | dario | [`g6.r1.l13`](#g6r1l13) | 4 | clue | `observability` |
| 2025-04-22 | wiki comment | docs/meetings/weekly-notes-week-of-apr-14.md | dario | [`g6.r2.g6r2-s2-l3`](#g6r2g6r2-s2-l3) | 2 | clue | `scope` |
| 2025-05-01 | chat | #code-review | gideon | [`g6.r1.l14`](#g6r1l14) | 7 | clue | `observability` |
| 2025-05-02 | chat | #code-review | dario | [`g6.r2.g6r2-s1-l3`](#g6r2g6r2-s1-l3) | 7 | clue | `rule` |
| 2025-05-13 | wiki comment | docs/engineering/price-lookup-errors-what-each-bad-argument-actually-raises.md | gideon | [`g6.r1.l5`](#g6r1l5) | 2 | clue | `exclusions_or_crossover`, `observability` |
| 2025-05-27 | wiki comment | docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md | konrad | [`g6.r1.l12`](#g6r1l12) | 2 | clue | `observability` |
| 2025-06-02 | mail | “Re: Week of May 26 recap: v0.1.25 shipped” | konrad | [`g6.r1.l3`](#g6r1l3) | 3 | clue | `rule` |
| 2025-06-03 | chat | #engineering | dermot | [`g6.r2.rev2`](#g6r2rev2) | 8 | **reversal** of `g6.r2.batch-discount-uniform-then-cancel-2` | `rule`, `scope`, `exclusions_or_crossover` |
| 2025-06-10 | wiki comment | docs/engineering/cost-estimates-in-batch-mode-where-the-price-numbers-come-from.md | nikolai | [`g6.r2.g6r2-s3-l2`](#g6r2g6r2-s3-l2) | 2 | clue | `exclusions_or_crossover` |
| 2025-06-18 | mail | “Week of Jun 9 rollup: gemini batch runs showing $0.00” | dermot | [`g6.r1.l7`](#g6r1l7) | 3 | clue | `exclusions_or_crossover` |
| 2025-06-18 | mail | “batch cost estimates: the 50% discount is being applied to every processor” | nikolai | [`g6.r2.g6r2-s2-l2`](#g6r2g6r2-s2-l2) | 4 | clue | `scope` |
| 2025-06-25 | wiki page | docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | emil | [`g6.r2.g6r2-s4-l2`](#g6r2g6r2-s4-l2) | 1 | clue | `observability` |
| 2025-06-25 | chat | #code-review | gideon | [`g6.r1.l10`](#g6r1l10) | 6 | clue | `exclusions_or_crossover`, `observability` |
| 2025-06-26 | chat | #pipeline | gideon | [`g6.r1.l9`](#g6r1l9) | 8 | clue | `exclusions_or_crossover` |
| 2025-07-02 | wiki comment | docs/engineering/model-price-lookup-what-a-miss-returns.md | dermot | [`g6.r1.l8`](#g6r1l8) | 2 | clue | `exclusions_or_crossover` |

#### `g6.r2.batch-discount-uniform-then-cancel-1` · **herring**

- **chat** · #pipeline · **gideon** · 2025-01-27 16:36
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> went and looked - settled: the base cost processor halves every source, and klusterai/inference.net multiply their cost() by 2 to cancel it, their tables are already batch-tier

As it appears, spread across the exchange:

```
13:47  gideon    whats the *2 doing in klusterai's cost(). looks wrong to me tbh
13:51  dermot    inference.net has the same multiply, if i'm reading it right
13:56  dario     went and looked. the base cost processor halves every source that goes through it, and those two multiply their cost() by 2 to cancel it back out
14:00  gideon    halves it for what though
14:04  dario     batch pricing. which is exactly why it doesnt fit those two — their tables are already batch tier, so the halving takes it off a second time
14:08  dermot    mhm. so the x2 is undoing a discount that was never meant to land on them
14:12  dario     that tracks, yes. so it comes out of the base processor, not out of their cost() methods. nobody has picked up the actual change yet
14:14  gideon    ya. i read that multiply as a real pricing thing
```

#### `g6.r2.batch-discount-uniform-then-cancel-2` · **herring**

- **chat** · #engineering · **dario** · 2025-01-27 18:30
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Dario discount stays in the base, providers whose table already lists batch prices cancel it with a x2 in their own cost() override, klusterai and inference.net both do this

As it appears, spread across the exchange:

```
14:02  dario     on the batch cost thing — is the discount applied once down in the base cost(), or is each provider meant to do its own?
14:06  konrad    base. the discount stays in there, so nobody has to remember it
14:09  dario     mhm. some of the price tables are already batch numbers though, those would come out low twice over
14:12  konrad    those ones cancel it. x2 in their own cost() override, so the base discount washes out
14:14  dario     klusterai does that? i saw a 2 sitting in there and couldnt make sense of it
14:16  konrad    right, klusterai and inference.net. both of them do it that way, presumably thats all of them off the top of my head
14:19  dermot    yeah ok. i read that override a while back and filed it under someone being clever
```

#### `g6.r1.l4`

- **chat** · #engineering · **dario** · 2025-03-14 13:11
- carries `g6.r1.exclusions_or_crossover`, `g6.r1.observability`
- must be typed literally: `resolve_model_price`, `no-such-model`, `not-a-provider`, `96h`, `unknown_provider`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Pasting what i got back: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h") gives unknown_provider, not a word about the model or the window - yup, right call for an unregistered provider.

As it appears, spread across the exchange:

```
13:11  dario     was poking at the price lookup with deliberately bad inputs over lunch, wanted to see which complaint falls out
13:12  dario     resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")
13:14  konrad    and? what comes back
13:15  dario     pasting what i got back: unknown_provider. thats the whole of it
13:16  emil      and nothing about the model? or the window - both of those are junk in that call too
13:18  dario     nope. not a word about either one, just the provider
13:19  emil      yup, right call for an unregistered provider. nothing on the code side does that today though, someone still has to write it
13:21  dario     that tracks. honestly i half expected it to hand me all three at once
```

#### `g6.r2.g6r2-s1-l1`

- **chat** · #pipeline · **emil** · 2025-03-19 11:44
- carries `g6.r2.rule`
- must be typed literally: `The`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> The batch estimate came in at a quarter of the invoice again, so basically two separate layers each knocking half off the same price. Nobody's disputing that part at this point.

As it appears, spread across the exchange:

```
14:04  emil      batch estimate came in at a quarter of the invoice again. thats twice now
14:06  dermot    mhm. same shape as last month, if i had to guess
14:07  emil      a quarter is the part i keep tripping on. one bad rate wouldnt get you all the way there
14:09  gideon    so basically its two separate layers, each one knocking half off the same price
14:10  gideon    The stacking isnt really in dispute at this point tbh, we all landed there already
14:12  dermot    yeah. nobody's written the fix though
14:13  emil      yup. i'll quit re-running it hoping for a different number
```

#### `g6.r1.l6`

- **chat** · #pipeline · **dario** · 2025-03-21 09:02
- carries `g6.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> context on that fix - i burned twenty minutes chasing a window typo when the real problem was that I had misspelled the provider. the error should name the first thing that's wrong.

As it appears, spread across the exchange:

```
13:06  dario     bit of context on that cost lookup fix while it's fresh - i burned twenty minutes on a miss last week before i found it
13:07  nils      twenty minutes on the lookup itself, or on reading what it told you?
13:08  dario     reading it, honestly. i spent the whole time chasing a window typo
13:09  gideon    and it wasnt the window at all?
13:10  dario     no. i had misspelled the provider. the window was fine, it just looked wrong to me because that's where i was staring
13:11  nils      makes sense. so the error should name the first thing that's wrong rather than whatever it trips over later - that's worth documenting wherever this lands
13:12  dario     mhm. that's exactly the twenty minutes back
13:13  gideon    ya tbh i read the last line of those and nothing else
```

#### `g6.r1.l11`

- **chat** · #engineering · **nikolai** · 2025-03-24 15:25
- carries `g6.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Ya, thats not theoretical - tracker took the whole online run down last night 4k requests in, on a model litellm has never heard of. Cost display, not the work.

As it appears, spread across the exchange:

```
14:02  nikolai   is the tracker blowing up on an unknown model actually happening or are we designing for a maybe
14:03  gideon    Ya, thats not theoretical. it took the whole online run down last night
14:04  nikolai   how far in
14:05  gideon    4k requests. on a model litellm has never heard of
14:06  emil      so the run itself was fine and we lost it to the price lookup?
14:07  gideon    exactly. cost display, not the work
14:07  gideon    so basically the lookup doesnt get to end a run anymore, thats settled on my end
14:09  nikolai   yep. 4k in is the part that stings
```

#### `g6.r2.g6r2-s4-l3`

- **chat** · #pipeline · **gideon** · 2025-03-25 13:14
- carries `g6.r2.observability`, `g6.r2.scope`
- must be typed literally: `"*"`, `4.0`, `batch=False`, `batch=True`, `completion_window`, `completion_window="*"`, `input_cost_per_million`, `klusterai`, `litellm`, `output_cost_per_million`, `provider="klusterai"`, `resolve_model_price`, `source`, `source == "litellm"`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on the adding side, my batch test pins resolve_model_price(m, provider="klusterai", completion_window="*", batch=True).input_cost_per_million at 4.0, same float as batch=False. same test, source == "litellm" halves input_cost_per_million and output_cost_per_million both.

As it appears, spread across the exchange:

```
15:18  gideon    quick one on the price lookup - for klusterai batch, are we asserting a different number than the online path or the same one?
15:22  nils      same one. on the adding side my batch test pins resolve_model_price(m, provider="klusterai", completion_window="*", batch=True).input_cost_per_million at 4.0
15:25  gideon    and with batch=False? same 4.0 or just near it
15:28  nils      same float. not near, identical.
15:33  dario     does that test cover the litellm side too or is that a separate one honestly i lost track
15:36  nils      same test. with source == "litellm" it halves input_cost_per_million and output_cost_per_million, both of them, not just the input leg
15:39  gideon    ah. tbh i was reading the "*" in your snippet as a todo marker, not an actual arg you pass
```

#### `g6.r2.g6r2-s2-l1`

- **chat** · #pipeline · **dario** · 2025-03-26 13:18
- carries `g6.r2.scope`
- must be typed literally: `50%`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - klusterai's published per-million is already their batch rate, and we went and took another 50% off it in the estimate.

As it appears, spread across the exchange:

```
13:18  dario     klusterai in the cost estimate is landing at about half what the invoice says. one of the two is lying
13:21  gideon    we take the batch discount off there tho, thats expected no
13:25  nils      let me think - their published per-million is already the batch rate. there's nothing to take off it.
13:27  dario     ok but that alone doesnt get us to half. the estimate is way under even without that
13:31  nils      that's the rest of it. we went and took another 50% off it in the estimate anyway, so the thing is cut twice. the published number stands, the extra one comes out
13:34  dario     that tracks. so the pricing entry stays as-is and the multiplier goes for them
13:36  gideon    ya tbh i think i copied that multiplier down from the block above when i added them
```

#### `g6.r2.g6r2-s4-l1`

- **chat** · #pipeline · **dermot** · 2025-04-03 14:18
- carries `g6.r2.observability`, `g6.r2.rule`
- must be typed literally: `0.5`, `1.0`, `50%`, `azure`, `batch_multiplier()`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure, tbh one number for both. outside batch mode both hand back 1.0.

As it appears, spread across the exchange:

```
14:18  dermot    costing question while i'm in here - for a batched run, where does the discount get applied? we don't do it in the caller do we
14:21  gideon    so basically the base cost processor has a batch_multiplier(), and in batch mode it comes back 0.5. the 50% is the whole of it, nothing else to apply
14:23  dermot    so on a normal sync run it just doesn't get called at all?
14:24  gideon    no it still gets called, you just get 1.0 back. um, same arithmetic either way which is nice
14:26  dario     what about azure though, i had it in my head their batch discount was a different figure
14:27  gideon    ya i went and looked. azure is 0.5 as well, tbh one number for both, i was expecting to have to carry two
14:29  dermot    and azure outside batch mode, 1.0 the same as the other one
14:30  gideon    exactly, both hand back 1.0 there
14:32  dario     ok, so no per provider special casing. i had half a branch written for that, going to bin it before someone finds it
```

#### `g6.r2.g6r2-s3-l1`

- **chat** · #cookbooks · **emil** · 2025-04-03 16:07
- carries `g6.r2.exclusions_or_crossover`
- must be typed literally: `config`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Emil worth one, yes. A cookbook user put their negotiated input cost straight in the config and the batch run reported half of what they typed.

As it appears, spread across the exchange:

```
15:31  emil      the pricing complaint from the cookbook user - worth its own ticket or just a note on the recipe
15:33  konrad    @Emil worth one, yes. its not a docs thing
15:35  emil      what did they actually do though
15:36  konrad    put their negotiated input cost straight in the config
15:38  nikolai   and it got ignored
15:40  konrad    no it took. the batch run reported half of what they typed
15:41  emil      half. yeah ok thats a ticket
15:43  dario     did they attach the config or did you have to go dig for it
15:45  konrad    attached, thats how i knew what number they typed
```

#### `g6.r1.l1`

- **chat** · #pipeline · **gideon** · 2025-04-07 13:51
- carries `g6.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> while we're on cost numbers - i lost an hour today to a nonetype in the cost sum, the price came back with the input side empty and we summed it anyway

As it appears, spread across the exchange:

```
13:41  gideon    while we're still on cost numbers - i lost an hour today to a nonetype in the cost sum
13:44  dario     was that the lookup handing back something odd, or the sum doing it on its own
13:45  gideon    the lookup. price came back with the input side empty
13:47  dermot    and it still went into the addition, if i had to guess
13:48  gideon    exactly. we summed it anyway, nothing said a word until it blew up
13:52  dario     mhm. empty isn't a zero though, that's the part i want closed - the sum shouldn't ever be handed half a price to add
13:53  dario     i'd rather it never gets that far than we patch around it at the addition, in any case
13:55  dermot    yeah ok. that's a ticket of its own, not sure whose yet
13:57  gideon    honestly though, a full hour. i was staring at the resume path the whole time
```

#### `g6.r2.fix18`

- **chat** · #engineering · **dermot** · 2025-04-07 16:22
- carries `g6.r2.observability`
- must be typed literally: `klusterai`, `4.0`, `"*"`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> for the record the klusterai row in pr 622 is 4.0 per million input straight off their pricing page. no window split on their table at all it just sits under "*"

As it appears, spread across the exchange:

```
15:03  dermot    nikolai, on 622 — the klusterai input number. per million, or already scaled
15:05  nikolai   per million its 4.0 in straight off their pricing page
15:07  emil      short context tier or the blended one? i had it in my head they split above the window
15:08  dermot    yeah thats what i was circling. do we need a second row for the long context case
15:10  nikolai   no window split on their table at all
15:11  nikolai   it just sits under "*" thats the whole entry
15:13  dermot    mhm. one row covers it then
15:15  emil      sounds right. the second row i had half drafted for it can go, that was me copying another providers table anyway
```

#### `g6.r2.g6r2-s3-l3`

- **mail** · “PR 565: cost reporting before it lands” · **dermot** · 2025-04-08 13:12
- to nikolai@world.local, emil@world.local, dario@world.local,
 konrad@world.local, gideon@world.local, priya@world.local, ilse@world.local
- carries `g6.r2.exclusions_or_crossover`, `g6.r2.rule`
- must be typed literally: `batch_multiplier`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> reading the cost path in 565 — we're picking who gets the batch discount with an if-chain on provider names inside batch_multiplier, that belongs on the class as a flag instead.

As it appears, spread across the exchange:

```
13:12  dermot    Subject: the provider if-chain in batch_multiplier  Nikolai,  I spent a good part of a late night going through the cost path in 565, and there is one thing in there I would rather raise now than after it lands, because it will only get more expensive to unpick.  The way we currently decide who gets the batch discount is an if-chain on provider names inside batch_multiplier. The function walks through a sequence of string comparisons against the provider name, returns a discounted multiplier for the ones it recognises, and falls through to full price for everything else. Functionally it produces the right numbers today, so this is not a bug report. The problem is where the knowledge lives. Whether a given provider offers batch pricing at all is a fact about that provider, and at the moment that fact is written down nowhere near the provider — it is buried in the middle of a cost function, expressed as a name match. Adding a provider now means remembering to go and edit an unrelated function, and if you forget, the silent result is that the provider is quietly billed at full price rather than erroring.  What I would like instead is for that eligibility to be a flag on the class, and for batch_multiplier to read the flag rather than the name. The multiplier calculation stays where it is; it just stops making the eligibility decision itself.  If I had to guess, this is a small change in practice, but I did not want to make it inside the review without agreement that it is the right direction.  Dermot
13:44  nikolai   Right, I agree with the direction. I have written that if-chain twice now and both times it felt like the wrong place to be typing provider names.  One thing I want pinned down before anyone touches it. Does the flag sit on the base class with a default, so subclasses only speak up when they differ, or does every provider have to declare it explicitly? Off the top of my head the default is the nicer ergonomics, but it reintroduces the same silent failure you just described, only one level up — a new provider that forgets to set it inherits the default and nobody notices.  The rest of it is solid enough as you have it. I would keep batch_multiplier owning the arithmetic and nothing else.
14:26  dermot    On the default question — I would put it on the base class defaulting to off. The silent failure you are describing is real, but it is not symmetric with the current one. Under the if-chain, the eligibility fact is invisible from the provider entirely, so there is nothing to review; under a flag with a default, it is a missing line in a class where every other pricing attribute is sitting in plain sight, and that is the kind of omission a reader notices. Defaulting to off also means the failure mode is that we overcharge ourselves in an estimate rather than undercharge, which is the direction I would rather be wrong in.  So: flag on the base class, off by default, each provider that actually offers batch pricing sets it true alongside its other rates, and batch_multiplier does a lookup instead of a name comparison. I am not entirely sure whether we want the discount rate itself on the class as well, but that is a separate argument and the current numbers do not force it.  That said, I do not think the if-chain was a mistake when it was written. With two providers in it, it read fine. It stopped reading fine somewhere around the fourth, and none of us were looking at it on the day that happened.
```

#### `g6.r2.g6r2-s2-l4`

- **mail** · “Re: Weekly update: week of Apr 7” · **konrad** · 2025-04-14 09:16
- to dermot@world.local, emil@world.local, dario@world.local,
 gideon@world.local, nikolai@world.local, tomas@world.local
- carries `g6.r2.scope`, `g6.r2.exclusions_or_crossover`
- must be typed literally: `resolve_model_price`, `batch=True`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> on your cost question — resolve_model_price with provider=klusterai and batch=True came back at half the table rate, and anything we read out of those provider tables should come back exactly as listed.

As it appears, spread across the exchange:

```
09:16  konrad    Subject: the klusterai number on the cost sheet looks halved  Emil,  I am putting together the cost estimate for the batch runs we discussed last week, and before I circulate anything I want to be sure I am reading the pricing helper correctly, because one of the numbers does not match what I expected.  The case is klusterai in batch mode. I looked up the per-token figure in the provider table by hand, then asked the helper for the same thing, and the helper came back with exactly half of what the table lists. Half is a suspiciously round factor, so it is presumably deliberate, but I cannot tell from the outside whether it is a batch discount the helper is applying on purpose or whether something is being divided that should not be. The difference matters because the estimate goes out to people who will not check it.  There is a second thing I would like confirmed while you are in there. For the ordinary case, where I am not asking for batch at all and just want the price of a model that sits in one of the provider tables, should I take what comes back as the table value unchanged, or is there any adjustment applied on that path as well? Off the top of my head I assumed unchanged, but I have assumed wrong once already in this mail.  Thanks, Konrad
11:02  emil      Konrad,  On your cost question — both of those are working as intended, and I can tell you exactly where each number comes from, because I went through the resolution path this morning to be sure I was not repeating something I half remembered.  The klusterai case first. What you called is resolve_model_price with provider=klusterai and batch=True, and the half-of-table figure it returned is the correct answer, not a lost digit. Batch pricing for that provider is a fifty percent reduction against the listed rate, and rather than carry a second set of numbers that would drift out of date the moment the provider republishes, the helper takes the listed rate and halves it at lookup time. So the round factor you noticed is the whole of the batch behaviour, and you can put the halved number on the sheet with a clear conscience. If it had come back at anything other than exactly half the table rate, that would have been the thing worth mailing about.  On your second point, your assumption was the right one. Anything we read out of those provider tables comes back exactly as listed — no rounding, no markup, no unit conversion, nothing applied on the way out. The table is the source of truth for the non-batch path, and if the helper and the table ever disagree there, we have a bug rather than a policy. I say this with some emphasis because we need to be intentional here about not accumulating quiet adjustments in the lookup layer; the moment a number changes shape between the table and the caller, nobody can reconcile an invoice again. Batch halving is the one transformation, and it only applies when you ask for it.  So, concretely: halved for the klusterai batch line, as listed everywhere else.  Emil
11:47  konrad    Emil,  That settles it, and it settles it in the direction that costs me the least rework, since the sheet already carries the halved figure and I was preparing to raise it back up.  What threw me was that I had the two behaviours the wrong way round in my head. I had it that the tables held the batch rates already and that the flag was some kind of no-op left over from an earlier design, which would have made the halving a genuine fault. Knowing that the halving is the flag doing its one job, and that the plain lookup is untouched, I can read any of these numbers now without going back to the table to check it by hand. I have corrected the note in my own file that said otherwise, in case anyone else was reading over my shoulder.  Konrad
```

#### `g6.r2.g6r2-s1-l4`

- **wiki comment** · docs/releases/v0-1-22-release-notes.md · **dermot** · 2025-04-14 11:42
- carries `g6.r2.rule`, `g6.r2.observability`
- must be typed literally: `batch=False`, `batch=True`, `batch_multiplier()`, `resolve_model_price`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> on the 50% line: resolve_model_price has no separate batch row, batch=True scales what batch=False returned. whichever number batch_multiplier() hands the processors, it should be reading that same one.

As it appears, spread across the exchange:

```
11:42  dermot    the mistral section is accurate as far as it goes, but the way the 50% line is phrased makes it sound like batch is a second price, and it is not. resolve_model_price has no separate batch row - there is one number per model, and batch=True scales what batch=False returned. the discount is a multiplier applied after the lookup, not a lookup of its own.  noting it here because it has a consequence that is easy to miss if you come to this page to find out what batch costs. whichever number batch_multiplier() hands the processors, it should be reading that same one - the value resolve_model_price already returned for batch=False. if it goes to a constant of its own, or a per-provider table, then the two halves can disagree and nothing in the output will say so, the totals just come out wrong quietly. that said i checked this on a late night and it took me a while to satisfy myself the two paths were looking at the same value, so it is worth writing down rather than rediscovering.
15:26  konrad    Adding to this - the notes say the same 50% for all three providers, and that is true now, but only because the multiplier is one shared value and not a per provider one. so if mistral ever discounts diferently, the wording in this section and batch_multiplier() both have to change together, not one or the other. Anyway that is the only line in the notes where I think the phrasing could send someone looking for a price row that does not exist.
```

#### `g6.r2.rev1` · **reversal**

- **chat** · #pipeline · **gideon** · 2025-04-14 11:52
- carries `g6.r2.rule`, `g6.r2.scope`
- takes back `g6.r2.batch-discount-uniform-then-cancel-1`
- must be typed literally: `batch_multiplier()`, `cost()`, `klusterai`, `inference.net`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> batch stats: two layers each halving is why estimates came in at a quarter of the invoice. batch_multiplier() is the only place that factor lives now, 1.0 on klusterai and inference.net, no cost() override.

As it appears, spread across the exchange:

```
14:06  gideon    batch stats projection from yesterday came out at about a quarter of what the invoice says. um, anyone hit that?
14:10  dario     mhm i chased that this morning actually. its being halved twice - two layers each doing it on their own, so you land on a quarter
14:12  gideon    two layers? i thought klusterai and inference.net cancel the base one out with the x2 in their cost()
14:17  dermot    that was the arrangement as i remember it - base cost processor halves every source, and those two double back in cost() because their tables are already batch tier
14:22  dario     that whole arrangement is gone. the factor lives in batch_multiplier() now and thats the only place it lives, nothing else applies it
14:25  gideon    so what do klusterai and inference.net return then
14:29  dario     1.0, and no cost() override at all. their tables already price the batch tier so theres nothing to cancel out
14:33  dermot    yeah ok. one halving nobody argues with
14:35  gideon    ya. i was half a minute from filing this against the provider backends tbh
```

#### `g6.r2.g6r2-s1-l2`

- **chat** · #pipeline · **dermot** · 2025-04-15 18:30
- carries `g6.r2.rule`
- must be typed literally: `batch_multiplier`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> while we're on the provider cost paths, i left the same note on the azure cost() override again: why is this dividing by two here when batch_multiplier already ran

As it appears, spread across the exchange:

```
15:43  dermot    while we're on the provider cost paths - i left the same note on the azure cost() override again. same note as last week
15:45  gideon    what note
15:46  dermot    why is this dividing by two here. no comment on it, no ticket, nothing
15:49  dario     the halving, ya. thats the bit i stall on every time i read that file honestly. by the time cost() runs, batch_multiplier already ran
15:51  dermot    so which is it - the override is doing it a second time, or the multiplier never touched azure
15:53  dario     the multiplier touches azure fine, i checked it back in march. the override is just older than it. so the divide comes out of cost() and thats that
15:54  dermot    yeah ok. i'd stopped assuming that was safe to remove
15:56  gideon    so basically the override predates the multiplier. tbh that would explain the azure line looking small in the march totals
```

#### `g6.r1.l2`

- **wiki comment** · docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md · **dermot** · 2025-04-21 09:58
- carries `g6.r1.rule`
- must be typed literally: `UnpricedModelError`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> if the table has no number for it i would rather the lookup raise UnpricedModelError at the call site than hand back a price with a hole in it.

As it appears, spread across the exchange:

```
09:58  dermot    the out of scope section here is scoped to the resume offset specifically, and that is the right call for this workstream, but there is a second failure in the same code path that i dont think is written down anywhere yet. the offset case assumes the table has a number and picks the wrong one. the case i keep hitting is the table having no number at all - a model id that was never added, or one the provider renamed under us mid-quarter. the lookup returns nothing usable for those, and the aggregator folds that into the run total as zero, so the total comes back looking complete and is simply short by whatever that model actually cost.  that is worse than the 10x, to my mind. a 10x offset is visible - you look at the number and know something is wrong. a total that is quietly missing one model reads as correct forever. if i had to guess, most of the figures i have refused to trust this quarter are this and not the resume path.  so for whoever picks up the cost accounting work after this closes: if the table has no number for it i would rather the lookup raise UnpricedModelError at the call site than hand back a price with a hole in it. a run that fails loudly at the point of the missing entry is recoverable. one that silently understates is not, and by the time anyone notices, the run is weeks gone.
14:26  dario     makes sense, and honestly it is a bit worse than the page reads, because the discarding is ours. the table does return None for the unknown ids - it is not inventing a zero. the aggregator does `or 0.0` about two frames up, before anything is summed. so we do have the information at the one moment we still know something is wrong, and we throw it away there.  which means the raise dermot is describing is not really a change to the lookup, it is the aggregator having to grow a branch it doesnt have. a batch of 400 requests with one unpriced model in it presumably still needs to report the other 399, so the error cant just take the whole run down. in any case the None survives that far today, which is more than i assumed when i started reading this.
```

#### `g6.r1.l13`

- **mail** · “Re: Weekly update: week of Apr 14” · **dario** · 2025-04-21 13:08
- to emil@world.local, nikolai@world.local, gideon@world.local,
 dermot@world.local, tomas@world.local, tobias@world.local
- carries `g6.r1.observability`
- must be typed literally: `WS-054`, `input_cost_per_million`, `output_cost_per_million`, `price_unavailable_reason`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> on WS-054 — for the trackers input_cost_per_million and output_cost_per_million just stay empty and the reason sits on price_unavailable_reason, so we can show why rather than a number.

As it appears, spread across the exchange:

```
13:08  dario     Subject: what the trackers should report when we have no price for a model (WS-054)  Nikolai, Emil, Dermot,  I have been working through the cost accounting piece on WS-054 and I have hit the question we all knew was coming, which is what a tracker should report for a model whose price we simply do not have. This happens more than I expected: a model that is new enough that the registry has not caught up, a provider that never published per-token numbers in the first place, and the various self-hosted cases where there is no meaningful list price at all.  The tempting option is to put a zero in and move on, and I think that is actually the worst thing we could do, because a zero is a number and a number gets summed, charted and quoted back at us in a monthly total that is quietly wrong. My proposal is the opposite: for those models input_cost_per_million and output_cost_per_million just stay empty on the tracker, and we do not substitute anything for them. Nothing gets invented and nothing gets added up that should not be.  Empty on its own is not very helpful to whoever is reading the output, though, so the second half of the proposal is that the tracker carries price_unavailable_reason alongside those two fields, and that is where the explanation goes - the model is not in the registry, the provider publishes no pricing, self-hosted, whichever applies. The point is that we can show why there is no number rather than showing a number we made up.  Either we do that, or we pick a sentinel value and spend the next year explaining it to people. I would rather have the empty fields and the reason.  Best, Dario
13:44  nikolai   Empty rather than zero is right, and I would have argued for it if you had not. A zero in a cost column is indistinguishable from a genuinely free call, and we have a couple of those.  One blunt question: does anything downstream sum these fields today without checking for empty first? If the aggregation path assumes a number is always there, then leaving input_cost_per_million and output_cost_per_million empty moves the problem rather than solving it, and I would want that checked before we call it settled. Off the top of my head the summary path is the only place that touches both fields.  On price_unavailable_reason, that seems solid enough to me. One field, one string, and the reader gets told what happened.
14:26  emil      Dario, Nikolai,  On the reason field, let me make sure I have understood the shape of it correctly. You are saying that when a price is unknown, price_unavailable_reason is populated on the tracker and the two cost fields are left empty, so the presence of a reason is effectively the signal that the numbers are absent by design rather than by accident. If that is right then I am in agreement, because that is a much better story to tell a user than a silent zero.  We need to be intentional about what actually goes into that string, though. If it ends up as three different phrasings of the same situation depending on which code path filled it in, the display becomes noise. I would keep it to a small set of reasons we can write down now and extend deliberately later, and I would write them in language a user can read, not an internal identifier.  On Nikolai's question about the summing path, I believe the summary only reaches for those fields when it has them, but I would not want to state that as fact without looking.  Emil
15:07  dario     Emil, that is exactly the shape. The reason being present is what tells you the empty cost fields are deliberate, and I agree entirely that the wording should come from a short fixed set rather than being composed at whatever call site happened to notice the gap. I will keep it to the handful we know about and we can add to it when a real case turns up that none of them cover.  Nikolai, on the summing question, I went and read it after your mail. The aggregation skips a tracker that has no cost numbers on it rather than treating them as zero, so the totals come out as a sum over the models we actually priced, which is the honest answer. To be honest that is the part I was least sure of before I checked.  So the settled position on WS-054 is this: two empty cost fields, one populated price_unavailable_reason, and output that says plainly what it does not know instead of quoting a figure nobody can defend. In any case it is the best we can do until the registry catches up with the providers, and I would rather be visibly missing a number than confidently wrong about one.  Best, Dario
```

#### `g6.r2.g6r2-s2-l3`

- **wiki comment** · docs/meetings/weekly-notes-week-of-apr-14.md · **dario** · 2025-04-22 09:47
- carries `g6.r2.scope`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> re the batch vs online cost question — i had an online run showing batch pricing in the tracker all afternoon. outside batch mode the list price comes through untouched, thats settled at least.

As it appears, spread across the exchange:

```
09:47  dario     the "open questions i havent pinned down yet" line under WS-050 is doing a lot of work, so let me pin one of them down here since it keeps coming up. the one i mean is the batch vs online cost question.  half of it is genuinely broken: i had an online run sitting in the tracker for most of tuesday afternoon reporting batch pricing. not a batch run, not resumed from one, just an ordinary online run showing the discounted numbers the whole time.  the other half is fine and i think thats worth writing down so nobody re-opens it. outside batch mode the list price comes through untouched. i went back over it by hand against the price table and the figures match, actually to the cent. so its not that cost is wrong in general, its that batch pricing is reaching runs that never asked for it.  in any case, the non batch path is settled as far as im concerend, and whatever the fix ends up being it shouldnt need to go anywhere near it.
15:12  emil      sounds right, and i can confirm the untouched half from the infra side. the discount is applied in exactly one place on the way in, and the online path never reaches it, so there isnt really a mechanism for the list price to come out modified there. lines up with dario's hand check.  the flagged-as-batch half is the one i'd not describe too confidently yet. Honestly i'm not entirely sure whether the run itself was carrying the wrong mode or the tracker was reading it that way, and those are two fairly different problems wearing the same symptom.
```

#### `g6.r1.l14`

- **chat** · #code-review · **gideon** · 2025-05-01 09:06
- carries `g6.r1.observability`
- must be typed literally: `$0.00`, `None`, `input_cost_per_million`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> that said, the pricing gaps part of that page: input_cost_per_million comes through None and the viewer renders it $0.00, which readers read as free. that zero shouldnt be shown.

As it appears, spread across the exchange:

```
13:58  gideon    did anyone read the handover page against the actual viewer? i want to know what i got wrong in it before more people link to it
14:01  dermot    mostly it holds up. that said, the pricing gaps part of that page is the bit i'd push on. input_cost_per_million comes through None for a chunk of the models
14:02  gideon    ok but thats sort of the point of the section no? the gaps are expected, we say so
14:04  dermot    the gap is fine, yeah. what isnt fine is what happens after - the viewer renders it $0.00
14:05  emil      oh. so readers read that as free
14:06  dermot    they do, and one of them is going to quote it back at us. that zero shouldnt be shown
14:09  gideon    ya ok. i pulled a handful of models this morning and more than one came up $0.00, so its not one weird row somewhere
```

#### `g6.r2.g6r2-s1-l3`

- **chat** · #code-review · **dario** · 2025-05-02 12:26
- carries `g6.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> spent the morning working out which of the two subtracions was the real one. only one place in the tree gets to touch the price for batch, we agreed that much.

As it appears, spread across the exchange:

```
15:04  dario     can someone tell me why the batch discount comes off in two different places? i tripped over the second one this morning
15:06  emil      i spent the morning on exactly that, honestly. working out which of the two subtractions was the real one
15:07  konrad    and? which of them wins
15:09  emil      only one place in the tree gets to touch the price for batch. the other subtraction shouldnt be there at all
15:11  konrad    right, that part nobody argued about
15:12  emil      yup. not written yet though, i havent picked a ticket for it
15:14  dario     that tracks. i'd assumed the second one was deliberate and left it alone back in january
```

#### `g6.r1.l5`

- **wiki comment** · docs/engineering/price-lookup-errors-what-each-bad-argument-actually-raises.md · **gideon** · 2025-05-13 10:42
- carries `g6.r1.exclusions_or_crossover`, `g6.r1.observability`
- must be typed literally: `unknown_model`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> so basically same args but with a provider we do have registered and it comes back unknown_model instead, so the junk window never even gets looked at.

As it appears, spread across the exchange:

```
10:42  gideon    The walkthrough in this section assumes the failure comes out of the stale window on the cached price, and I don't think that is right, at least not for the case I ran into. So basically I used the same arguments as the example above, same model string, same timestamp, and the only thing I changed was the provider, to one we actually do have registered. What comes back is unknown_model. The window is never even looked at, the lookup gives up well before it reaches that check. That makes the paragraph below misleading tbh, because it reads as if a registered provider gets you as far as the freshness comparison and then fails there. It does not get that far, and it fails for a different reason entirely.
14:05  dermot    yeah, this matches what i see. the provider resolves out of the registry without complaint, then the model key gets rebuilt from that provider's own naming, and for the one you tried we never populated an entry under that name, so it raises unknown_model before anything touches the cached window at all. if i had to guess, the example here was written against the older single table lookup, where there genuinely was nothing sitting between the arguments and the window check. so the section is describing behaviour that no longer exists, rather than a fault in the window.
```

#### `g6.r1.l12`

- **wiki comment** · docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md · **konrad** · 2025-05-27 10:42
- carries `g6.r1.observability`
- must be typed literally: `Every`, `cost()`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> Related: sometimes the price cant be resolved at all. Every cost() method should be catching that and handing back 0.0 rather than ending a run over an accounting number.

As it appears, spread across the exchange:

```
10:42  konrad    The out of scope section only covers the case where we price off the wrong model and get a number that is wrong by 10x. There is a neighbouring case that is not written down anywhere on this page and I keep running into it: sometimes the price cannot be resolved at all. The model is not in the pricing table, or the batch response comes back under a name we have no entry for, and there is simply nothing to look up. Right now that propogates all the way up and takes the run down with it, which is presumably nobody's intent, we are throwing away hours of finished work over an accounting number. Every cost() method should be catching that case and handing back 0.0 instead. The run completes, the cost line is obviously not real, and the output survives. Not entirely sure this belongs here given the workstream is closed, but it came out of the same sweep as the offset so I am leaving it here anyway rather than nowhere.
15:20  dermot    yeah, and the page more or less assumes the problem away already - "depending on which direction the price moved" only makes sense if there was a price to move. the unresolvable case sits underneath that one and is the more damaging of the two, since a bad number is at least a number you can go back and correct after the fact. that said, i don't think the 0.0 is as ambiguous as it sounds when you say it out loud. a batch run that genuinely cost nothing is not a thing that occurs, so a zero on the ledger reads as missing to anyone looking at it.
```

#### `g6.r1.l3`

- **mail** · “Re: Week of May 26 recap: v0.1.25 shipped” · **konrad** · 2025-06-02 11:14
- to dario@world.local, emil@world.local, nikolai@world.local,
 nolan@world.local, gideon@world.local
- carries `g6.r1.rule`
- must be typed literally: `PR 681`, `UnpricedModelError.REASONS`, `ValueError`, `reason='no_pricing_data'`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> One note on PR 681: I passed reason='no_pricing_data' and the constructor threw ValueError straight back at me - it checks the arg against UnpricedModelError.REASONS, which is those three strings and nothing else.

As it appears, spread across the exchange:

```
11:14  konrad    Subject: the reason argument on PR 681  Dermot,  I spent part of this morning wiring the unpriced-model path into my branch, and I ran into something on PR 681 that I would like to have written down somewhere, because otherwise it stays inside the review and the next person loses the same ten minutes I did.  At the point where we raise for a model that has no entry in the price table, I passed reason='no_pricing_data' to the constructor. That looked to me like the obvious string for the situation, and I did not think about it any further. The constructor threw ValueError straight back at me. It does not simply record whatever string you hand it. It checks the argument against UnpricedModelError.REASONS first, and that constant is a closed list of three strings and nothing else. My string was not one of the three, so the error I was trying to raise never got as far as being raised, and what the caller saw was a ValueError from inside the error class itself, which is confusing the first time.  Look, I am not arguing against the check. Presumably the intention is that the reason is a fixed vocabulary and not free text, and if that is the intention then rejecting anything outside the three is exactly right. What I want to know is whether the three are meant to stay as they are, or whether adding a fourth is a normal thing to do when a new case turns up. I could not quote all three back to you off the top of my head, but they are enumerated in the class and it is a short list.  Anyway, if the answer is that the list is closed on purpose, I will use one of the existing three and stop trying to invent my own.  Konrad
11:52  dermot    Konrad,  So if I have you right, the complaint is not that the constructor rejected your string, it is that it rejected it by raising a different exception type than the one you were in the middle of constructing, and you had to go and read the class to find out why. That is fair, and it is the part of the design that reads badly from the outside.  The validation is deliberate. The reason field ends up in the summary output and in the aggregation on the viewer side, and both of those group by the exact string, so a typo or a one-off variant would quietly produce a fourth bucket that nobody had accounted for. Checking the argument against UnpricedModelError.REASONS in the constructor is the cheap way to make that impossible. That said, the list is not sacred. Three was what the cases were when it was written, and if a genuinely new case turns up, adding a fourth string is a one-line change plus whatever the viewer needs to display it.  If I had to guess, your case is not a new one. A model with no entry in the price table is the situation the existing reasons were written for, so I would look at those three before adding anything.  Dermot
12:20  konrad    Right, that matches what I found once I read the class properly. One of the three covers my case and I have switched to it, so nothing needs to change in the code.  On the confusing part, I have put a short note on PR 681 saying that the constructor validates the reason against UnpricedModelError.REASONS and raises ValueError if it does not match. That is the sentence I would have wanted to read before I passed reason='no_pricing_data' and spent a while wondering why my exception had turned into a different one.  Konrad
```

#### `g6.r2.rev2` · **reversal**

- **chat** · #engineering · **dermot** · 2025-06-03 18:20
- carries `g6.r2.rule`, `g6.r2.scope`, `g6.r2.exclusions_or_crossover`
- takes back `g6.r2.batch-discount-uniform-then-cancel-2`
- must be typed literally: `batch_multiplier()`, `cost()`, `resolve_model_price`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Also scratch my reviewr note about the x2 in the provider's cost() override, those overrides are deleted. Where a table already lists batch prices, batch_multiplier() returns 1.0 and resolve_model_price leaves the external-sourced price as listed.

As it appears, spread across the exchange:

```
15:04  dermot    konrad - your review note on the kluster pricing pr, the one about the x2. i can't find the override it points at
15:08  konrad    ah. scratch my reviewr note about the x2 in the provider's cost() override, i was reading an old copy. those overrides are deleted
15:11  dario     that x2 was the thing we agreed months back - discount stays in the base, and providers whose table already lists batch prices cancel it with a x2 in their own cost(). klusterai and inference.net both did it that way
15:13  dermot    mhm, that's what i was hunting for. so what cancels it now
15:15  konrad    nothing has to. where a table already lists batch prices, batch_multiplier() returns 1.0. two places doing arithmetic on the same number is what bit us when kluster refreshed their table, the override kept discounting a price that was already batch
15:18  dermot    so the listed price still gets scaled somewhere further down? resolve_model_price i mean
15:21  konrad    no, resolve_model_price leaves the external-sourced price as listed. presumably that is the whole point of it being sourced
15:24  dermot    yeah ok. i was reading the pr against your old note the whole afternoon, no wonder the arithmetic didn't sit right
```

#### `g6.r2.g6r2-s3-l2`

- **wiki comment** · docs/engineering/cost-estimates-in-batch-mode-where-the-price-numbers-come-from.md · **nikolai** · 2025-06-10 10:41
- carries `g6.r2.exclusions_or_crossover`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> if the price per million came from the user then thats already the number they pay so batch mode shouldnt be knocking anything off it either

As it appears, spread across the exchange:

```
10:41  nikolai   the batch section here reads like the 0.5 multiplier gets applied to whatever price we ended up with which isnt right once an override is in play  if the price per million came from the user then thats already the number they pay theres nothing left to knock off it we have no idea how they arrived at it and it may well be a batch rate they negotiated themselves so halving it just invents a cheaper number that nobody is being charged  i'd say the multiplier only belongs on registry prices those we own and we know they are the list rate  off the top of my head thats one branch in the lookup not a rewrite but the page should say which of the two cases it means before someone impelments it straight off this
15:02  dario     makes sense, and i think its actually broader than batch - the cached input multiplier a couple of paragraphs down has exactly the same problem, since both of them get applied after the lookup returns and neither one knows or cares where the number came from.  the distinction worth writing into the page, to be honest, is that a registry entry is a rate card and an override is a price. a discount is something you apply to a rate card. once somebody hands us a number they have already done whatever arithmetic they were going to do, and applying ours on top of theirs is us guessing at their contract  i did check and the override itself is recorded as given, so its only the derived cost thats wrong here, not what we store
```

#### `g6.r1.l7`

- **mail** · “Week of Jun 9 rollup: gemini batch runs showing $0.00” · **dermot** · 2025-06-18 13:12
- to nikolai@world.local, emil@world.local, dario@world.local,
 konrad@world.local, gideon@world.local, priya@world.local, ilse@world.local
- carries `g6.r1.exclusions_or_crossover`
- must be typed literally: `litellm.model_cost`, `input_cost_per_token`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> right that gemini row does exist in litellm.model_cost but input_cost_per_token on it is null and we priced a whole week of runs at zero off the back of it

As it appears, spread across the exchange:

```
13:12  dermot    Subject: the gemini line coming back at zero for the week of the 9th  Nikolai,  I spent part of this morning reconciling the spend report for the week of the 9th and the Gemini line comes back at zero on every single run in the window. It is not a rounding artefact and it is not one bad run — it is 0.00 on the input side across the board, on runs that we know moved a serious volume of tokens.  If I had to guess, we simply never had a pricing entry for that model, the lookup found nothing, and the code fell through to a default of zero instead of raising. That said, I have not read the table itself, so I may have the mechanism wrong and I would rather not go to Priya with a theory. You were closer to the pricing path than I was when it landed. Does that match what you would expect, or is it something else entirely?  Dermot
14:05  nikolai   Dermot,  It is something else, and the something else is worse than a missing entry.  Right, that Gemini row does exist in litellm.model_cost. I pulled it up before writing this because I expected to find what you described and did not. The row is present, it has the model name we look up under, it has an output price on it. What it does not have is a price on the input side: input_cost_per_token on that row is null. So the lookup succeeds. It hands back a row, we read the field, we get a null, and the arithmetic downstream turns that into a zero without raising anything or logging anything.  The consequence is that we priced a whole week of runs at zero off the back of it. Not a fraction of the cost, not a few outlier runs — the entire input side of every run in that window that touched the model. A genuinely absent entry would have been the easy version of this, because we would have got a lookup failure and someone would have seen it the same day.  I would say the reporting side is solid enough otherwise; this is one null in one row propagating quietly. What we do about the general case of a partially populated row is a separate question and I have to think that one through properly.  Nikolai
15:20  dario     Nikolai, Dermot,  That tracks, and it explains something I had put down to my own error. I re-ran the week's totals by hand after reading this, pulling the input price from the provider's own page rather than from our table, and the shape of it is exactly what Nikolai describes — the output side of the Gemini runs is priced correctly, the input side is a clean zero, and the gap between the two numbers is the entire input cost of the week.  Honestly, the part that bothers me is not the null itself but that a null and a real zero are indistinguishable by the time the number reaches the report. A row that is half populated reads to us as a row that is fully populated and happens to be free, and there is no free model in that table.  In any case, the corrected figure for the week comes out at a little over four times what the report showed. That is the number going to finance on Friday, in place of the one they already have.  Dario
```

#### `g6.r2.g6r2-s2-l2`

- **mail** · “batch cost estimates: the 50% discount is being applied to every processor” · **nikolai** · 2025-06-18 13:42
- to dermot@world.local, emil@world.local, dario@world.local,
 konrad@world.local, gideon@world.local, priya@world.local, ilse@world.local
- carries `g6.r2.scope`
- must be typed literally: `inference.net`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> same story with inference.net the number on their pricing page is already what a batch job costs so theres nothing left to take off it

As it appears, spread across the exchange:

```
13:42  nikolai   Subject: the inference.net figure is already the batch price  Dermot, Dario,  I have been going down the provider list finishing off the batch side of the pricing table, and inference.net turns out to be the same story we hit earlier in the week. Their pricing page publishes a single number per model, dollars per million tokens in and out, and that number is what a batch job is actually billed at. There is no second column for batch, no footnote offering a percentage off, and no separate batch price list anywhere else on the site that I could find.  The reason I am writing rather than just filling the cell is that our table is built around the assumption that a provider gives you a standard rate and you take something off it for batch. For inference.net there is nothing left to take off. The published figure is the floor. If we apply the usual reduction on top of it we will be quoting a price below anything the provider will ever charge, and every estimate that comes out of it will read low.  So my position is that inference.net goes in at the page price for both the standard and the batch entry, with a note saying the published number is already the batch price. I would say that is solid enough unless one of you knows of a discount schedule I have not seen.  Nikolai
14:20  dermot    Nikolai,  If I had to guess, what you are describing is that inference.net does not price batch as a discount off an interactive rate at all, and that the single figure on the page is the whole of it — so the reduction we apply elsewhere would be a second discount on a price that has already absorbed one. That is my reading of your mail, and if it is right then I agree with where you land.  The failure mode is worth stating plainly, because it is the quiet kind. Nothing errors. The table fills in, the estimate comes out, and it is simply too low by whatever fraction we shaved off, which nobody notices until an invoice contradicts it. That said, I am not entirely sure the page has always read that way; my memory is of an older version that was less explicit. It does not change the conclusion, since we price against what is published now, but it is the sort of thing that makes me want the note you mention to be in the table itself and not in a commit message.  Dermot
14:41  dario     To be honest, the thing I keep coming back to is that we have now seen this twice, which makes it a shape rather than an exception. A provider that only ever publishes one number is not telling us it has no batch tier — it is telling us the batch tier is the number. Treating a missing batch column as an invitation to compute one is where we get into trouble.  On Dermot's point about the note living in the table: I think that is the right call, and I would go slightly further and have the note say why, not just what. "Published price is already the batch price" is the fact, but the next person to read the row will want to know whether we checked or assumed. In any case, for inference.net specifically I have no objection at all to the page figure going in unchanged.
15:16  nikolai   Dermot, Dario,  Yep, that is the reading. One published number, and it is the batch number, so the row goes in at the page price with no reduction applied on either side.  I have written the note into the table rather than the commit, and worded it the way Dario asked for — that the published figure is the batch price, and that I confirmed it against the pricing page today rather than inferring it from the absence of a batch column. Off the top of my head that is the only provider left in the list where the two entries are deliberately identical, so the note also stops it from looking like a copy-paste mistake to whoever reads it next.  Nikolai
```

#### `g6.r2.g6r2-s4-l2`

- **wiki page** · docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md · **emil** · 2025-06-25 09:28
- carries `g6.r2.observability`
- must be typed literally: `batch_multiplier()`, `cost()`, `self.batch_multiplier()`
- find it: BookStack search finds this one — it is in the page body, not a comment

> On pricing: azure's batch_multiplier() keeps drifting from the base processor's; we agreed identical in and out of batch mode, with cost() just scaling the resolved price by self.batch_multiplier().

#### `g6.r1.l10`

- **chat** · #code-review · **gideon** · 2025-06-25 15:44
- carries `g6.r1.exclusions_or_crossover`, `g6.r1.observability`
- must be typed literally: `unknown_window`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - if a model's map has no row for the window you asked for thats unknown_window, we shouldnt be quietly borrowing the "*" tier.

As it appears, spread across the exchange:

```
15:44  gideon    quick one on the price lookup - model has a window map, nothing in it matches the window we passed. what comes back
15:46  konrad    there is a "*" row sitting on that model though
15:49  emil      let me think through that - if the map has no row for the window you asked for thats unknown_window
15:51  konrad    ok but the star row is right there, presumably it just falls onto that?
15:54  emil      no, thats the bit i dont want. we shouldnt be quietly borrowing the "*" tier. unknown_window is honestly the more truthful answer
15:57  gideon    ya. tbh i hit this on a nightly last week and read the number as real
```

#### `g6.r1.l9`

- **chat** · #pipeline · **gideon** · 2025-06-26 14:03
- carries `g6.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> while you're in there - there's no 24h row for that model so the lookup fell through to the star entry, and my batch report came out with online prices again

As it appears, spread across the exchange:

```
14:03  gideon    nils are you in the price lookup today? small thing while you're in there
14:06  nils      yes, most of the afternoon. what is it
14:07  gideon    my batch report came out with online prices again
14:11  nils      let me think. either the batch numbers are wrong for that model, or the lookup matched nothing at all. i'd lean toward nothing
14:13  gideon    ya nothing. there's no 24h row for that model, i checked the table twice
14:16  dermot    so it's not a plain miss then, it lands on the star entry?
14:19  nils      that's it. falls through to the star entry and takes the online prices off it, which is what gideon's report printed. i'll fold it into the pass i'm already doing rather than open something separate
14:21  dermot    mhm. explains the run i wrote off last month, i assumed i'd passed the wrong flag
```

#### `g6.r1.l8`

- **wiki comment** · docs/engineering/model-price-lookup-what-a-miss-returns.md · **dermot** · 2025-07-02 10:24
- carries `g6.r1.exclusions_or_crossover`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> a row in the pricing table with a null input price is no more use to us than no row at all, it should come back exactly the way a missing key does.

As it appears, spread across the exchange:

```
10:24  dermot    the lookup section above still reads as though the only failure mode is an id that isn't in the pricing table, and that isn't quite the shape of it. we have rows where the id is present and the output price is populated but the input price is null - older entries mostly, from before the import started carrying both columns. for our purposes a row like that is no more use to us than no row at all. every caller reaches straight for the input price and multiplies by token count, so a row with a null there gets you an arithmetic error one frame further down instead of a clean miss.  so what i'd like the page to say, and what i'll implement unless someone objects here: a null input price is a miss. it comes back exactly the way a missing key does - same return value, same branch in the caller, no third "partial row" case and nothing raised. the caller shouldn't be able to tell the difference between the two, and shouldn't have to.  that said, if we ever grow a caller that only cares about the output side, this is the wrong call and the page should be revisited. nothing reads the table that way today.
15:47  konrad    Right, and the null rows are not a rare edge case, if i remmeber the import numbers it was a decent handful of the older ids. Collapsing them into the missing key path is also what the fallback already assumes, so nothing downstream needs to change.  One thing that is easy to get wrong when writing this: null and 0.0 are not the same case. 0.0 is a genuine input price on the free entries, and that row must still come back as a hit.
```

