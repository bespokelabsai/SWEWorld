# Was every graded thing said, or only implied? — g6

**46 of 51** assertions rest on something a remark says outright.

- `stated` **46** — a reader was told
- `implied` **1** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g6.r1.exclusions_or_crossover#1` | stated | `g6.r1.l4`, `g6.r1.l2`, `g6.r1.l3` | l4 names the exact triple-bad call (bad model, bad provider, unrecognised window) as a failing lookup, and l2/l3 commit out loud that a failing lookup raises UnpricedModelError carrying a reason. |
| `g6.r1.exclusions_or_crossover#2` | stated | `g6.r1.l4`, `g6.r1.l6` | l4 gives that literal call and says it yields unknown_provider with 'not a word about the model or the window', and l6 confirms the first-wrong-thing ordering rule. |
| `g6.r1.exclusions_or_crossover#3` | stated | `g6.r1.l5`, `g6.r1.l2` | l5 describes the same args with a registered provider as still an error case, and l2 states such a lookup raises UnpricedModelError. |
| `g6.r1.exclusions_or_crossover#4` | stated | `g6.r1.l5` | l5 says verbatim that with a registered provider it comes back unknown_model and the junk window never even gets looked at. |
| `g6.r1.exclusions_or_crossover#5` | stated | `g6.r1.l2`, `g6.r1.l7`, `g6.r1.l8` | l2 says that when the table has no number the lookup should raise UnpricedModelError rather than return a price with a hole, and l7/l8 identify the null-input-price row as exactly that case. |
| `g6.r1.exclusions_or_crossover#6` | stated | `g6.r1.l8`, `g6.r1.l7`, `g6.r1.l5` | l8 rules that a null input price 'should come back exactly the way a missing key does' and l5 fixes the missing-key reason as unknown_model, so the reason string for these rows is decided out loud. |
| `g6.r1.exclusions_or_crossover#7` | n/a | — | 0.045 is the suite's own wildcard-tier fixture price, asserted only to show the '*' row exists and was not borrowed; no remark owes this number. |
| `g6.r1.exclusions_or_crossover#8` | stated | `g6.r1.l10`, `g6.r1.l2` | l10 says a model map with no row for the requested window is an unknown_window failure, and l2/l3 establish that such failures surface as a raised UnpricedModelError. |
| `g6.r1.exclusions_or_crossover#9` | stated | `g6.r1.l10`, `g6.r1.l9` | l10 states the reason string and forbids silently borrowing the '*' tier, with l9 reporting the wildcard fallthrough as the bug being fixed. |
| `g6.r1.observability#1` | stated | `g6.r1.l2`, `g6.r1.l3`, `g6.r1.l4` | l2 says outright that when the table has no number the lookup should raise UnpricedModelError at the call site rather than return a holed price, and l3 refers to its constructor and REASONS, so the ex |
| `g6.r1.observability#2` | stated | `g6.r1.l4`, `g6.r1.l5`, `g6.r1.l10`, `g6.r1.l6`, `g6.r1.l3` | l4 gives the exact call and the exact string "unknown_provider", l5 gives "unknown_model" for the same args with a registered provider and says the junk window is never reached, l10 gives "unknown_win |
| `g6.r1.observability#3` | stated | `g6.r1.l12`, `g6.r1.l11` | l12 states the rule directly — every cost() method should catch the unresolvable-price error and hand back 0.0 rather than end a run over an accounting number — with l11 supplying the incident that mo |
| `g6.r1.observability#4` | stated | `g6.r1.l13`, `g6.r1.l1`, `g6.r1.l14` | l13 names both tracker attributes by their exact spelling and says they just stay empty when the price can't be resolved, and l14/l1 establish that "empty" here means None and specifically not a displ |
| `g6.r1.observability#5` | stated | `g6.r1.l13`, `g6.r1.l5`, `g6.r1.l11` | l13 says the reason sits on the field named `price_unavailable_reason` on the trackers, and l5 fixes the reason string for a registered provider that doesn't list the model as "unknown_model". |
| `g6.r1.observability#6` | stated | `g6.r1.l13`, `g6.r1.l5`, `g6.r1.l11` | Same as #5 for the second tracker — l13 speaks of "the trackers" in the plural and puts the reason on `price_unavailable_reason`, and l5 supplies "unknown_model" for that scenario. |
| `g6.r1.observability#7` | stated | `g6.r1.l13`, `g6.r1.l1`, `g6.r1.l14` | Same as #4 for the second tracker: l13 names both cost-per-million attributes and says they stay empty rather than carrying a number. |
| `g6.r1.rule#1` | stated | `g6.r1.l3`, `g6.r1.l4`, `g6.r1.l5`, `g6.r1.l10` | l3 names the attribute outright (`UnpricedModelError.REASONS`), says the constructor validates against it and that it is "those three strings and nothing else", and l4/l5/l10 each speak one of the thr |
| `g6.r1.rule#2` | stated | `g6.r1.l2`, `g6.r1.l8`, `g6.r1.l7`, `g6.r1.l1` | l2 says the lookup should raise rather than "hand back a price with a hole in it" and l8 says a row whose input price is null "should come back exactly the way a missing key does", so a successfully r |
| `g6.r1.rule#3` | n/a | — | This guards the suite's own iteration over its price-table fixture — that something was actually measured — and is not a claim about the implementation at all. |
| `g6.r1.rule#4` | stated | `g6.r1.l2`, `g6.r1.l3`, `g6.r1.l4`, `g6.r1.l5` | l2 names the exception type and the behaviour together — "i would rather the lookup raise UnpricedModelError at the call site" — and l3 confirms it is a constructed exception class with a validated re |
| `g6.r1.rule#5` | stated | `g6.r1.l3`, `g6.r1.l4`, `g6.r1.l5`, `g6.r1.l10` | l3 says the constructor rejects a reason outside `UnpricedModelError.REASONS` with ValueError, so every raised instance carries a reason drawn from that set, and l4/l5/l10 name the members it is drawn |
| `g6.r2.exclusions_or_crossover#1` | stated | `g6.r2.g6r2-s3-l2`, `g6.r2.g6r2-s3-l1`, `g6.r2.rev1`, `g6.r2.g6r2-s4-l2` | Nikolai's wiki page decides it outright — a per-million price that came from the user is already what they pay, so "batch mode shouldnt be knocking anything off it either" — and rev1/s4-l2 fix batch_m |
| `g6.r2.exclusions_or_crossover#2` | stated | `g6.r2.g6r2-s4-l2`, `g6.r2.g6r2-s3-l1`, `g6.r2.g6r2-s3-l2` | Emil states the shape of cost() ("just scaling the resolved price by self.batch_multiplier()") and konrad states the bug as a batch run reporting "half of what they typed", so the reader is told cost( |
| `g6.r2.exclusions_or_crossover#3` | stated | `g6.r2.rev1`, `g6.r2.rev2`, `g6.r2.g6r2-s3-l3` | Rev1 says batch_multiplier() is "1.0 on klusterai and inference.net" and rev2 generalises it to "where a table already lists batch prices, batch_multiplier() returns 1.0", with dermot putting the who- |
| `g6.r2.exclusions_or_crossover#4` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.g6r2-s4-l2` | Gideon pins the number and the call by name: "batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure ... outside batch mode both hand back 1.0." |
| `g6.r2.exclusions_or_crossover#5` | stated | `g6.r2.g6r2-s4-l3` | Nils writes the field and its value into a resolve_model_price test in the same breath — "same test, source == \"litellm\"" — so both the attribute name and the string a litellm-answered lookup report |
| `g6.r2.exclusions_or_crossover#6` | stated | `g6.r2.g6r2-s4-l3`, `g6.r2.g6r2-s1-l4`, `g6.r2.g6r2-s4-l1` | Nils says a litellm-sourced resolve_model_price "halves input_cost_per_million and output_cost_per_million both", dermot says batch=True scales what batch=False returned using the same number batch_mu |
| `g6.r2.observability#1` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.rev1` | Gideon names the function and the value outright: "batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure". |
| `g6.r2.observability#10` | stated | `g6.r2.g6r2-s4-l3`, `g6.r2.g6r2-s1-l4` | Nils writes that for source == "litellm" the same test halves input_cost_per_million, naming the function, the flag and the field. |
| `g6.r2.observability#11` | stated | `g6.r2.g6r2-s4-l3` | The same sentence names output_cost_per_million as halved too ("input_cost_per_million and output_cost_per_million both"), with 4.0 being half the fixture's listed output price. |
| `g6.r2.observability#2` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.g6r2-s4-l2` | Same remark closes with "outside batch mode both hand back 1.0", and Emil repeats that azure and the base processor are identical in and out of batch mode. |
| `g6.r2.observability#3` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.g6r2-s4-l2` | "0.5 on azure ... one number for both" is the decision said out loud, reinforced by Emil's "we agreed identical". |
| `g6.r2.observability#4` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.g6r2-s4-l2` | "outside batch mode both hand back 1.0" covers azure explicitly, since "both" is base plus azure. |
| `g6.r2.observability#5` | stated | `g6.r2.rev1`, `g6.r2.rev2` | Dario's revision states "batch_multiplier() is the only place that factor lives now, 1.0 on klusterai and inference.net, no cost() override", overriding the January cancel-with-x2 line. |
| `g6.r2.observability#6` | stated | `g6.r2.rev1`, `g6.r2.g6r2-s2-l2`, `g6.r2.rev2` | The same revision names inference.net alongside klusterai at 1.0, and Nikolai confirms its published number is already the batch price. |
| `g6.r2.observability#7` | stated | `g6.r2.g6r2-s4-l3`, `g6.r2.g6r2-s2-l4`, `g6.r2.rev2`, `g6.r2.g6r2-s2-l3` | Nils pins the batch=True resolve at "same float as batch=False", Emil says table-sourced prices come back exactly as listed, and Dario says the out-of-batch list price comes through untouched — the th |
| `g6.r2.observability#8` | stated | `g6.r2.rev2`, `g6.r2.g6r2-s2-l4`, `g6.r2.g6r2-s4-l3` | The listed == batched equality for an externally-sourced table price is stated by Konrad and Emil; the literal 3.0 is the suite's own fixture value and the corpus owes it nothing. |
| `g6.r2.observability#9` | stated | `g6.r2.g6r2-s2-l3`, `g6.r2.g6r2-s1-l4` | Dario settles that outside batch mode the list price comes through untouched and Dermot says batch=True scales what batch=False returned, so batch=False returning the raw fixture number is told; the 2 |
| `g6.r2.rule#1` | stated | `g6.r2.g6r2-s4-l2`, `g6.r2.rev1`, `g6.r2.g6r2-s4-l1`, `g6.r2.rev2` | Emil spells out the shape of cost() outright -- "cost() just scaling the resolved price by self.batch_multiplier()" -- and rev1/rev2 confirm the factor lives only there with the cancelling overrides d |
| `g6.r2.rule#2` | n/a | `g6.r2.g6r2-s4-l1` | This is the suite guarding its own arithmetic before dividing by the factor it just read; the corpus owes nothing to a non-zero precondition (and s4-l1's 0.5/1.0 values would satisfy it anyway). |
| `g6.r2.rule#3` | n/a | — | A fixture sanity check that the baseline price is non-zero so the substitution has something to move, not a behavioural claim about the product. |
| `g6.r2.rule#4` | stated | `g6.r2.rev1`, `g6.r2.g6r2-s1-l3`, `g6.r2.g6r2-s4-l2`, `g6.r2.g6r2-s1-l2`, `g6.r2.rev2` | "only one place in the tree gets to touch the price for batch" plus rev1's "batch_multiplier() is the only place that factor lives now ... no cost() override" and Emil's cost()-scales-by-self.batch_mu |
| `g6.r2.rule#5` | stated | `g6.r2.g6r2-s1-l4`, `g6.r2.g6r2-s4-l3`, `g6.r2.g6r2-s4-l1` | Dermot says resolve_model_price has no separate batch row and batch=True scales what batch=False returned by the same number batch_multiplier() hands the processors, and Nils pins the concrete consequ |
| `g6.r2.scope#1` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.rev1`, `g6.r2.g6r2-s1-l1` | Gideon says batch_multiplier() "comes back 0.5 on the base cost processor", a concrete factor strictly between 0 and 1, and Dario/rev1 confirms that single halving factor now lives only in batch_multi |
| `g6.r2.scope#2` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.g6r2-s2-l3` | Gideon states outright that "outside batch mode both hand back 1.0", and Dario confirms the list price comes through untouched outside batch mode. |
| `g6.r2.scope#3` | stated | `g6.r2.g6r2-s4-l1`, `g6.r2.g6r2-s4-l2`, `g6.r2.g6r2-s1-l2` | Gideon pins azure's batch_multiplier() at the same 0.5 as the base processor ("one number for both") and Emil restates the agreement that azure's is identical to the base processor's in and out of bat |
| `g6.r2.scope#4` | stated | `g6.r2.rev1`, `g6.r2.rev2`, `g6.r2.g6r2-s4-l1` | Dario's revision says batch_multiplier() is "1.0 on klusterai and inference.net" with no cost() override, Konrad repeats that where a table already lists batch prices batch_multiplier() returns 1.0, a |
| `g6.r2.scope#5` | **implied** | `g6.r2.rev2`, `g6.r2.g6r2-s4-l3`, `g6.r2.g6r2-s2-l4` | Konrad names an "external-sourced price" and Nils names a field called `source` whose value can be "litellm", but nobody puts the two together to say the returned record carries `source == "external"` |
| `g6.r2.scope#6` | stated | `g6.r2.g6r2-s4-l3`, `g6.r2.rev2`, `g6.r2.g6r2-s2-l4` | Nils pins resolve_model_price(..., batch=True).input_cost_per_million at "the same float as batch=False" for a table-listed provider, and Konrad and Emil both say table-sourced prices come back exactl |
| `g6.r2.scope#7` | stated | `g6.r2.g6r2-s4-l3` | Nils writes the discriminator literally — 'same test, source == "litellm" halves input_cost_per_million and output_cost_per_million both'. |
| `g6.r2.scope#8` | stated | `g6.r2.g6r2-s4-l3`, `g6.r2.g6r2-s1-l4`, `g6.r2.g6r2-s4-l1` | Nils says litellm-sourced prices halve both cost fields under batch=True, and Dermot ties resolve_model_price's batch scaling to the very number batch_multiplier() hands the processors, which Gideon f |

### `g6.r2.scope#5` — implied

```python
assert read_field(batched, "source") == "external"
```

Konrad names an "external-sourced price" and Nils names a field called `source` whose value can be "litellm", but nobody puts the two together to say the returned record carries `source == "external"` — the reader must supply that the adjective is that field's literal value.
