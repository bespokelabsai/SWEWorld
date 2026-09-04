# g6 — the requirement, reduced to what is graded

**472 words → 347** across 7 facts and 51 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g6.r1.rule` | 47 → 28 | 5 | 2 |
| `g6.r1.exclusions_or_crossover` | 90 → 68 | 9 | 2 |
| `g6.r1.observability` | 70 → 59 | 7 | 1 |
| `g6.r2.rule` | 56 → 38 | 5 | 2 |
| `g6.r2.scope` | 72 → 56 | 8 | 2 |
| `g6.r2.exclusions_or_crossover` | 66 → 46 | 6 | 2 |
| `g6.r2.observability` | 71 → 52 | 11 | 2 |

## `g6.r1.rule`

**Now (28 words):**

`resolve_model_price` never returns a `ModelPrice` carrying a `None` price: every failure raises `UnpricedModelError`, and the `reason` it carries is exactly one of the three strings `unknown_provider`, `unknown_model`, `unknown_window`.

**Dropped, because no assertion checks it:**

- "decided in that fixed order" — no assertion pins which reason a given lookup produces; #1 compares set(UnpricedModelError.REASONS), which is order-insensitive, and #5 only checks membership in REASON_STRINGS.
- "— the provider is checked first, then the model key, then the completion window" — the spelled-out restatement of that same ordering, ungraded for the same reason; nothing reads a precedence between the three failure cases.

**Kept despite looking like padding:** "never returns a `ModelPrice` carrying a `None` price" reads redundant beside the raise-on-failure clause, but #2 asserts each price field is isinstance(value, (int, float)) and not isinstance(value, bool) — that clause is the only thing left in the text requiring a real number to come back, so it stays. "the three strings" also stays: #1 is a set equality, so the count is graded.

## `g6.r1.exclusions_or_crossover`

**Now (68 words):**

An unregistered provider is `unknown_provider` even when the model is also absent and the window is also unrecognised, and a missing model key is `unknown_model` even when the window is also unrecognised. A model present in `litellm.model_cost` but carrying a missing or `None` input price is `unknown_model`, and a window that is absent from a model's price map is `unknown_window` rather than a fallback to the wildcard tier.

**Dropped, because no assertion checks it:**

- "The reasons never compete: when more than one applies the earlier check wins, so" - the abstract statement of the precedence rule, whose two concrete clauses follow it verbatim and are what #1-#4 actually grade.
- "rather than a success with a `None` price" - a restatement; "is `unknown_model`" already fixes the raised reason that #5 and #6 check.

**Kept despite looking like padding:** "rather than a fallback to the wildcard tier" reads like a contrast clause but is the only text forbidding wildcard fallback for an absent window; without it an implementer could return the wildcard price and fail #8/#9, and #7 (wildcard == 0.045) shows the wildcard tier is separately priced and reachable. "even when the model is also absent and the window is also unrecognised" survives because #1 exercises all three faults at once. `litellm.model_cost` and the exact reason strings `unknown_provider`/`unknown_model`/`unknown_window` are read by #2, #4, #6, #9.

## `g6.r1.observability`

**Now (59 words):**

`resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")` raises with `reason == "unknown_provider"`; the same call with a registered provider raises with `reason == "unknown_model"`; a model that provider does list, asked for an unlisted window, raises with `reason == "unknown_window"`. Every `cost()` method and both trackers catch `UnpricedModelError` and degrade — `cost()` to `0.0`, a tracker to `None` prices and a recorded reason.

**Dropped, because no assertion checks it:**

- 'so the exception never reaches a caller above the lookup' — the consequence/rationale clause. No assertion checks that the error fails to propagate above the lookup; #3, #4 and #7 check the degraded values themselves (0.0 and (None, None)), which the surviving clause already states.

**Kept despite looking like padding:** The three 'raises with reason == ...' clauses read like one rule said three times, but assertion #2 grades their exact ordering ["unknown_provider", "unknown_model", "unknown_window"], so all three stay verbatim and in order. The call literals stay because they are the only statement of which condition yields which reason (unregistered provider vs. registered provider with an unknown model vs. a listed model with an unlisted window). 'and a recorded reason' reads thin, but assertions #5 and #6 read price_unavailable_reason == "unknown_model" off the tracker, so the recording requirement cannot go. 'catch UnpricedModelError' stays as the named exception assertion #1 raises on.

## `g6.r2.rule`

**Now (38 words):**

The batch discount factor is applied by exactly one method, `batch_multiplier()`, on the cost processors; no `cost()` override multiplies or divides its result by anything. `resolve_model_price(..., batch=True)` applies that same fixed factor to the per-million numbers it returns.

**Dropped, because no assertion checks it:**

- "appears in exactly one place in the pricing path and" — a restatement of the one-owner rule that the surviving "no `cost()` override multiplies or divides its result by anything" already states; #4 establishes the single owner by substituting the multiplier, not by counting places in the path.
- "and only when the price came from `litellm.model_cost`" — no assertion checks where the price was sourced from; #5 only compares `discounted` to `listed * factor`, so the negative case (a price from any other source going undiscounted) is never exercised.

**Kept despite looking like padding:** "no `cost()` override multiplies or divides its result by anything" reads like emphasis on the clause before it, but it is the only surviving statement of what #4 checks: with `batch_multiplier()` patched to 3.0, `after == before / factor_before * 3.0`, i.e. nothing else scales the result on the way out. #1 pins `cost == completion_cost * batch_multiplier()` but not the absence of other factors, so cutting this clause would leave #4 ungrounded.

## `g6.r2.scope`

**Now (56 words):**

`batch_multiplier()` returns the discount factor only where the pricing data is a list price: it returns `1.0` when the processor is not in batch mode, and `1.0` on the klusterai and inference.net processors in every mode. `resolve_model_price` discounts a `source == "litellm"` price and leaves a `source == "external"` price exactly as the table lists it.

**Dropped, because no assertion checks it:**

- "because the per-window numbers in the external rate table are already those providers' batch tiers" — the reason klusterai and inference.net are exempt. No assertion reads the rate table's provenance; #4 only checks that 1.0 comes back for both batch values.
- "Symmetrically" — a rhetorical link announcing that the resolve_model_price sentence parallels the batch_multiplier one. Nothing is asserted about the parallel; #5–#8 read only the source strings and the field arithmetic.

**Kept despite looking like padding:** "only where the pricing data is a list price" reads like a preamble to the exceptions that follow it, but it is the only statement that a list-priced processor gets the factor rather than 1.0 — assertion #3 (`multiplier(azure_cls(config=config, batch=True)) == factor`) has no other source for that. "discount factor" likewise carries #1 (`0.0 < factor < 1.0`). "exactly as the table lists it" carries #6, which compares every field of the batched external price against the listed one; "leaves" on its own would not pin field-level equality.

## `g6.r2.exclusions_or_crossover`

**Now (46 words):**

A user-supplied per-million price is never discounted: `batch_multiplier()` returns `1.0` whenever the config carries an explicit input cost, even in batch mode on a processor that would otherwise discount. Which processors are exempt is decided by a class-level flag and by which source answered the lookup.

**Dropped, because no assertion checks it:**

- "taken as given and" — restatement of the rule that follows it; "is never discounted" already carries the whole claim, and no assertion can tell the two phrasings apart.
- ", never by matching the provider string against a hardcoded list at the point of use" — a prohibition on implementation style. Every assertion reads a returned multiplier, a cost, or a field value; none inspects how the exemption is resolved, so no test can distinguish a hardcoded provider list from a class-level flag.

**Kept despite looking like padding:** "even in batch mode on a processor that would otherwise discount" reads like emphasis on the first clause, but it is what pins #3 and #4 together: `exempt(config=config, batch=True)` must give `1.0` while `discounting(config=config, batch=True)` must give `factor`, so the exemption has to survive batch mode on a processor whose sibling still discounts. "by which source answered the lookup" stays as the only mention of a source, which #5 reads via `read_field(listed, "source")`.

## `g6.r2.observability`

**Now (52 words):**

`batch_multiplier()` is the discount factor on the base and Azure processors in batch mode and `1.0` out of it, and `1.0` on the klusterai and inference.net processors even in batch mode. `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` equals the `batch=False` value exactly, while a litellm-sourced model's `batch=True` value is exactly half its `batch=False` value.

**Dropped, because no assertion checks it:**

- '; a klusterai `cost()` in batch mode therefore returns the same number as out of it' — a 'therefore' consequence, not a rule of its own. #7 (in_batch == out_of_batch == pytest.approx(raw)) still follows: cost scales by the multiplier, and the surviving text pins klusterai's multiplier at `1.0` in batch mode.
- 'With a litellm-priced model,' — scene-setting preamble. Assertions #1-#6 build processors from `config` alone and never vary the pricing source, and the surviving final clause still says 'a litellm-sourced model's' at the one place the halving is graded (#9-#11).

**Kept despite looking like padding:** 'the discount factor' reads vague but cannot be cut: deleting it breaks the sentence, and it is the only carrier of the 0.5 that #1 and #3 check — the value is anchored by the surviving 'is exactly half its `batch=False` value'. 'and `1.0` out of it' looks like a mirror of the batch clause but is separately graded by #2 and #4. The whole `resolve_model_price(...)` call signature stays verbatim because #8 grades that path independently of the multiplier, and identifiers are never paraphrased.
