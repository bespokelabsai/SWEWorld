# Was every graded thing said, or only implied? — g9

**38 of 65** assertions rest on something a remark says outright.

- `stated` **38** — a reader was told
- `implied` **19** — a reader has to work it out, and may not
- `absent` **5** — nothing in the corpus bears on it
- `not_required` **3** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 15 remark(s) rewritten, 10 added, 1 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g9.r1.exclusions_or_crossover#1` | stated | `g9.r1.l-fw-3` | nikolai names FIREWORKS_BYTES_PER_TOKEN, gives its value as 3, places it in encoding.py and says all of it imports from finetune — the name, the number and the public location are all said out loud. |
| `g9.r1.exclusions_or_crossover#2` | **implied** | `g9.r1.l-fw-1`, `g9.r1.l-fw-3`, `g9.r1.l-fw-4`, `g9.r1.l-fw-2` | the reader must themselves multiply max_seq_length by the 3-bytes-per-token constant to get the per-line byte budget — l-fw-1 only reports that our cap is in tokens while Fireworks measures bytes, and |
| `g9.r1.exclusions_or_crossover#3` | stated | `g9.r1.l-fw-2` | dario decides outright that nothing in the jsonl gets shortened ever, preferring to ship one example fewer, which is exactly the kept-line-must-be-whole decision this assertion grades. |
| `g9.r1.exclusions_or_crossover#4` | **implied** | `g9.r1.l-fw-4` | l-fw-4 fixes the measurement as UTF-8 encoded length rather than characters, but nobody states the serialization that makes this pair come out at exactly 90 bytes — the reader has to supply json.dumps |
| `g9.r1.exclusions_or_crossover#5` | **implied** | `g9.r1.l-fw-4`, `g9.r1.l-fw-2`, `g9.r1.l-fw-3` | the accented row and the UTF-8 overshoot are described as a past mistake, but the reader must derive the 99-byte budget from max_seq_length=33 and the constant, and conclude the over-budget row leaves |
| `g9.r1.exclusions_or_crossover#6` | **implied** | `g9.r1.l-fw-4`, `g9.r1.l-fw-2`, `g9.r1.l-fail-4` | that the same accented row survives intact under a larger budget rests on the reader computing the byte budget themselves; l-fw-4 only says the row that landed exactly on the number was fine and l-fw- |
| `g9.r1.failure_behavior#1` | **implied** | `g9.r1.l-fw-3`, `g9.r1.rev1` | Nobody names EncodingError or says the new exception derives from it; l-fw-3 only mentions that "the error types" already live in encoding.py, leaving the reader to supply the inheritance. |
| `g9.r1.failure_behavior#10` | stated | `g9.r1.rev2`, `g9.r1.rev1`, `g9.r1.l-fail-3` | rev2 and rev1 both commit to raising ExampleTooLongError exactly when fewer than 16 prompt tokens survive past window_start. |
| `g9.r1.failure_behavior#11` | stated | `g9.r1.rev1`, `g9.r1.l-fail-3`, `g9.r1.rev2` | rev1 defines the retained quantity as how far the final assistant span starts past window_start and l-fail-3 says the refusal reports how much prompt survived, so the value falls out of the fixture. |
| `g9.r1.failure_behavior#12` | stated | `g9.r1.l-fail-3`, `g9.r1.l-fail-2` | The error carrying the example's full token count is said out loud in l-fail-3 and demonstrated by 129-against-cap-40 in l-fail-2; 91 is that same field on a different fixture. |
| `g9.r1.failure_behavior#13` | stated | `g9.r1.l-fail-3` | num_messages is named as one of the reported fields; 4 is simply the fixture's message count. |
| `g9.r1.failure_behavior#14` | **implied** | `g9.r1.rev1`, `g9.r1.h1`, `g9.r1.l-fail-4` | window_start is named and "window_start > 0" implies 0 means untrimmed, but nobody says the encoding of a short example exposes window_start == 0. |
| `g9.r1.failure_behavior#15` | **absent** | `g9.r1.l-rule-2` | No remark says the encoding itself carries a token_count field; the only counts discussed are on the refusal, and l-rule-2's metadata field is supervised_tokens. |
| `g9.r1.failure_behavior#16` | stated | `g9.r1.rev2`, `g9.r1.h2`, `g9.r1.l-fail-4` | h2 and rev2 both say format_batch skips the refused example and carries on with the rest, and l-fail-4 restates it. |
| `g9.r1.failure_behavior#17` | **implied** | `g9.r1.l-fail-3`, `g9.r1.rev2` | That the kept example survives the batch is stated, but nobody says the datum's metadata block carries a num_messages field to identify it by. |
| `g9.r1.failure_behavior#2` | stated | `g9.r1.rev1`, `g9.r1.rev2`, `g9.r1.l-fail-2` | rev1 says to_tinker_datum raises ExampleTooLongError when the final assistant span starts under 16 tokens past window_start, and l-fail-2 gives exactly this 129-vs-40 no-prompt-left case. |
| `g9.r1.failure_behavior#3` | **absent** | — | ValueError is never mentioned, and nothing in the corpus says the error hierarchy bottoms out in a builtin. |
| `g9.r1.failure_behavior#4` | stated | `g9.r1.l-fail-2`, `g9.r1.l-fail-3` | l-fail-2 attaches 129 tokens to an ExampleTooLongError refusal and l-fail-3 says the refusal carries the token count. |
| `g9.r1.failure_behavior#5` | stated | `g9.r1.l-fail-2`, `g9.r1.l-fail-3` | "129 tokens agianst a cap of 40" plus l-fail-3's "the cap" among the reported fields fixes the cap value the error carries. |
| `g9.r1.failure_behavior#6` | stated | `g9.r1.l-fail-2`, `g9.r1.l-fail-3` | "not one prompt token left standing" is zero surviving prompt tokens, and l-fail-3 says how much prompt survived is one of the reported quantities. |
| `g9.r1.failure_behavior#7` | stated | `g9.r1.l-fail-3` | l-fail-3 names num_messages literally as part of what a refusal reports; the value 2 is just the fixture's message count. |
| `g9.r1.failure_behavior#8` | **implied** | `g9.r1.l-fail-3`, `g9.r1.l-fail-2` | The corpus lists which quantities a refusal reports but never the wording, ordering, or the "minimum is 16" tail, and the required string omits num_messages that l-fail-3 says is printed. |
| `g9.r1.failure_behavior#9` | **implied** | `g9.r1.rev1`, `g9.r1.rev2`, `g9.r1.l-fail-4` | That a windowed example with enough retained prompt is returned rather than refused is stated, but the surviving datum's window_start of 51 is arithmetic nobody writes down. |
| `g9.r1.rule#1` | **implied** | `g9.r1.l-fail-2`, `g9.r1.l-fw-1`, `g9.r1.l-fail-1` | The corpus fixes a token cap ("129 tokens against a cap of 40") and that trimming keeps the tail, but nobody says how long the returned weight vector is, so the reader must supply the off-by-one that  |
| `g9.r1.rule#2` | stated | `g9.r1.l-rule-4`, `g9.r1.l-rule-3`, `g9.r1.l-rule-2`, `g9.r1.l-rule-1` | l-rule-4 says what settles a turn being in or out is whether the opening token of the answer survived the cut, and l-rule-3 says there are no part marks on a turn — the straddling span's surviving tai |
| `g9.r1.rule#3` | stated | `g9.r1.l-rule-3`, `g9.r1.l-rule-4`, `g9.r1.l-scope-2` | The all-or-nothing rule plus the one-per-supervised-token weighting is stated, so the surviving nine-token span summing to 9.0 is what the reader was told to produce. |
| `g9.r1.rule#4` | stated | `g9.r1.l-scope-2`, `g9.r1.l-scope-4`, `g9.r1.l-rule-3` | l-scope-2 reports weights coming back at 1.0 and says the question positions should instead be dark, and l-rule-3 rules out partial credit, so the vector being only 0.0 and 1.0 is said. |
| `g9.r1.rule#5` | stated | `g9.r1.l-rule-2`, `g9.r1.l-rule-3`, `g9.r1.l-rule-4` | l-rule-2 names supervised_tokens by that name and complains that twelve of its count are the tail of a front-chopped answer, which is exactly the field and the exclusion being graded. |
| `g9.r1.rule#6` | **implied** | `g9.r1.rev1`, `g9.r1.h1`, `g9.r1.l-fail-1` | The name window_start is used out loud in h1 and rev1, but nobody says how it is computed from token_count and the cap, so the reader has to derive the value 41 themselves from remarks that only repor |
| `g9.r1.rule#7` | stated | `g9.r1.l-rule-2`, `g9.r1.l-rule-3`, `g9.r1.l-rule-4` | supervised_tokens is named and its meaning fixed by l-rule-2, and the retained-span rule that makes both wide spans count in full is stated by l-rule-3 and l-rule-4. |
| `g9.r1.rule#8` | stated | `g9.r1.l-rule-4`, `g9.r1.l-rule-3`, `g9.r1.l-scope-2` | That a turn whose opening token survived is weighted end to end is stated by l-rule-4 and l-rule-3, which is what makes both wide spans light up in full rather than partially. |
| `g9.r1.scope#1` | **absent** | `g9.r1.l-fw-3`, `g9.r1.l-scope-3` | No remark names an encoding metadata field called "tokenizer" or says the no-tokenizer path flags itself as False in metadata; l-fw-3's inventory of encoding.py lists the role set, error types and FIR |
| `g9.r1.scope#2` | stated | `g9.r1.l-scope-3` | l-scope-3 makes the decision out loud about this exact expression — on the no-tokenizer path keep the len // 4 count and the <\|role\|> text exactly as they are — so the reader is told not to re-deriv |
| `g9.r1.scope#3` | **implied** | `g9.r1.rev1`, `g9.r1.h1` | h1 and rev1 use the name window_start and treat window_start > 0 as meaning "we cut something", so a reader can infer 0 for a 9-token example under a 1024 cap, but nobody says the mock path reports wi |
| `g9.r1.scope#4` | **implied** | `g9.r1.l-scope-3`, `g9.r1.l-scope-1`, `g9.r1.l-scope-2` | l-scope-3, l-scope-1 and l-scope-2 do say the no-tokenizer path must be masked like the real one, but nobody says how the mock path locates a span — the character-offset //4 rule and whether the <\|as |
| `g9.r1.scope#5` | **implied** | `g9.r1.l-scope-2`, `g9.r1.l-scope-3`, `g9.r1.l-scope-1` | l-scope-2 asks for "the first couple positions dark" on precisely this pair, which gestures at the shape, but the length-8 vector (the shift off a 9-token count) and the exact boundary after two zeros |
| `g9.r1.scope#6` | **implied** | `g9.r1.l-scope-3` | Only l-scope-3's "keep ... exactly as they are" bears on the mock path's outputs; that the token ids are literally range(count) and that model_input is the first eight of nine is nowhere written down. |
| `g9.r1.scope#7` | stated | `g9.r1.l-scope-4`, `g9.r1.l-scope-1` | l-scope-4 makes exactly this call — train_on_assistant_only off yields a flat vector of ones, "whichever of the two paths built it" — and l-scope-1 confirms the no-tokenizer path is one of those two. |
| `g9.r1.scope#8` | **implied** | `g9.r1.l-rule-2`, `g9.r1.l-scope-4` | l-rule-2 names supervised_tokens as a reported field and l-scope-4 gives all-ones weights, but nobody says supervised_tokens counts tokens rather than weight positions, so a reader summing the weights |
| `g9.r1.scope#9` | stated | `g9.r1.l-scope-4` | l-scope-4 explicitly covers the real-tokenizer path too — flag off means a flat vector of ones back regardless of which path built it — so the reader puts this in because they were told to, the 39 bei |
| `g9.r2.failure_behavior#1` | stated | `g9.r2.l17`, `g9.r2.l13` | dario decides out loud in l17 that "only the over-long ones should get binned and counted", and l13 confirms long examples are thrown out of the batch, so absorbing the over-long row as a counted drop |
| `g9.r2.failure_behavior#2` | stated | `g9.r2.l17`, `g9.r2.l16`, `g9.r2.l1` | l17 rules bad role sequences out of the drop path ("not a row to quietly skip") and l16 complains that the run carried on and shipped a file missing rows, so stopping the pass on a role-sequence error |
| `g9.r2.failure_behavior#3` | stated | `g9.r2.l19`, `g9.r2.l7` | l19 says that when the batch died halfway self.last_report was half filled in and "i'd rather it still read what the last good run left", which is exactly the no-partial-report-on-abort rule. |
| `g9.r2.failure_behavior#4` | **implied** | `g9.r2.l18`, `g9.r2.l1` | l18 only reports that a tokenizer with no apply_chat_template turned four hundred examples into drops and that "shouldnt become a batch of drops" — the reader must supply on their own that the alterna |
| `g9.r2.failure_behavior#5` | stated | `g9.r2.l19`, `g9.r2.l7` | the same rule as #3 is stated by l19 — an aborted batch must leave self.last_report reading what the last good run left — and l19 speaks of the batch dying generally, not of one particular error. |
| `g9.r2.rule#1` | **implied** | `g9.r2.l3`, `g9.r2.l4`, `g9.r2.l2`, `g9.r2.l1` | The word "dataclass" is never said; the reader must supply that "frozen" (l3) plus "compare equal with ==" (l4) plus a fixed field order (l2) means @dataclass rather than NamedTuple, which satisfies e |
| `g9.r2.rule#10` | stated | `g9.r2.l11`, `g9.r2.l10`, `g9.r2.l9` | l11 settles on numbering "against the list i passed in, in the order i passed it" and l10 reports the bug of positions matching the written file instead, giving both input-relative and ascending. |
| `g9.r2.rule#11` | stated | `g9.r2.l14`, `g9.r2.l13` | l13 names supervised_tokens as inflated by counting thrown-out examples and l14 says the token total should be "summed over kept examples only". |
| `g9.r2.rule#12` | n/a | — | Pure fixture check that the two short examples both survive the clean batch. |
| `g9.r2.rule#13` | stated | `g9.r2.l14`, `g9.r2.l12`, `g9.r2.l6`, `g9.r2.l4` | Every component is spoken: l6 has format_batch setting self.last_report, l14 sums tokens over kept only, l12 keeps non-kept rows out of windowed, and with nothing dropped the zero counters and empty i |
| `g9.r2.rule#14` | n/a | `g9.r2.rev2`, `g9.r2.l5` | The jsonl list-of-lines return is pre-existing shape the change must merely leave alone, and the length is the suite's fixture. |
| `g9.r2.rule#15` | stated | `g9.r2.l6`, `g9.r2.rev2`, `g9.r2.l15`, `g9.r2.l4`, `g9.r2.l11` | l6 and rev2 make to_jsonl_lines reassign self.last_report, l15 says the token total and trim count "should read zero there" on the tokenizer-less Fireworks path, l11 gives the input-relative index, an |
| `g9.r2.rule#2` | stated | `g9.r2.l3` | l3 reports a counter being incremented on a finished report and closes with "agreed reports are frozen once built", so immutability is decided out loud. |
| `g9.r2.rule#3` | **implied** | `g9.r2.l2`, `g9.r2.l4`, `g9.r2.l9`, `g9.r2.l12`, `g9.r2.l13` | All five names are spoken somewhere and l4 fixes the count at five, but only l2 pins a position ("kept comes first") — the reader has to invent the order of dropped/windowed/dropped_indices/supervised |
| `g9.r2.rule#4` | stated | `g9.r2.l4`, `g9.r2.l8` | l4 asks for "EncodingReport() to come out empty" and l8 says a freshly constructed formatter should already hold an empty report, which is the argument-less all-zero instance. |
| `g9.r2.rule#5` | stated | `g9.r2.rev1`, `g9.r2.rev2`, `g9.r2.l5` | rev1 reverts the tuple to a "plain list of datums", rev2 says "Return is List[Any]", and l5 repeats that format_batch "still has to hand back a plain list". |
| `g9.r2.rule#6` | n/a | `g9.r2.l17` | This is the suite's own fixture — one over-long example of two — resting on the drop behaviour l17 restates rather than on anything this report requirement owes. |
| `g9.r2.rule#7` | stated | `g9.r2.l2`, `g9.r2.l14`, `g9.r2.l4` | l2 places kept as an attribute of the class and l14 defines "kept examples" as the rows that made it into the output, so the counter named kept holding that number is a decision made aloud. |
| `g9.r2.rule#8` | stated | `g9.r2.l17`, `g9.r2.l5`, `g9.r2.l2` | l17 says the over-long ones "get binned and counted" and l5 says the binned-row count should be asked of the formatter afterwards; l2 fixes the attribute spelling as dropped, not skipped. |
| `g9.r2.rule#9` | stated | `g9.r2.l12`, `g9.r2.l14` | l12 complains windowed read nine on a batch that wrote six lines and says "dropped examples should not be in that number", and l14 backs it for the trim count, which is exactly the discriminating beha |
| `g9.r2.scope#1` | stated | `g9.r2.l8`, `g9.r2.l4`, `g9.r2.rev1` | l8 says outright that a just-constructed formatter returning None is wrong and "fresh one should already hold an empty report", and l4 fixes what empty means (EncodingReport() comes out empty and comp |
| `g9.r2.scope#2` | **absent** | `g9.r2.l12`, `g9.r2.l15` | Every mention of "windowed" in the corpus is a per-batch counter on the report (l12, l15); nothing says a returned datum carries a windowed field, let alone that it reads True for a windowed example. |
| `g9.r2.scope#3` | stated | `g9.r2.l7`, `g9.r2.rev2`, `g9.r2.l6` | l7 reports that a single call through to_tinker_datum came back with self.last_report rewritten, and rev2/l6 name the complete set of methods that are supposed to reassign it (format_batch and to_json |
| `g9.r2.scope#4` | **absent** | `g9.r2.l1`, `g9.r2.l17` | l1 mentions "the two error classes" without naming either and l17 talks about over-long rows being binned in a batch, not about any call raising, so the name ExampleTooLongError and the fact that to_t |
| `g9.r2.scope#5` | stated | `g9.r2.l7`, `g9.r2.rev2` | l7 covers the failing branch explicitly — "same when the call raised" — so the reader is told the raise path must leave last_report as the last batch left it, not half-written. |

### `g9.r1.exclusions_or_crossover#2` — implied

```python
assert len(lines) == 1, f"expected the 90-byte line and not the 93-byte one, got {lines}"
```

the reader must themselves multiply max_seq_length by the 3-bytes-per-token constant to get the per-line byte budget — l-fw-1 only reports that our cap is in tokens while Fireworks measures bytes, and nobody says the jsonl writer computes or applies that product.

### `g9.r1.exclusions_or_crossover#4` — implied

```python
assert len(lines[0].encode("utf-8")) == 90
```

l-fw-4 fixes the measurement as UTF-8 encoded length rather than characters, but nobody states the serialization that makes this pair come out at exactly 90 bytes — the reader has to supply json.dumps with default separators and ensure_ascii=False.

### `g9.r1.exclusions_or_crossover#5` — implied

```python
assert FireworksDataFormatter(max_seq_length=33).to_jsonl_lines([accented]) == []
```

the accented row and the UTF-8 overshoot are described as a past mistake, but the reader must derive the 99-byte budget from max_seq_length=33 and the constant, and conclude the over-budget row leaves an empty list rather than a trimmed one.

### `g9.r1.exclusions_or_crossover#6` — implied

```python
assert len(kept) == 1 and json.loads(kept[0])["messages"][0]["content"] == "héllo wörld"
```

that the same accented row survives intact under a larger budget rests on the reader computing the byte budget themselves; l-fw-4 only says the row that landed exactly on the number was fine and l-fw-2 only forbids shortening.

### `g9.r1.failure_behavior#1` — implied

```python
assert issubclass(ExampleTooLongError, EncodingError)
```

Nobody names EncodingError or says the new exception derives from it; l-fw-3 only mentions that "the error types" already live in encoding.py, leaving the reader to supply the inheritance.

### `g9.r1.failure_behavior#14` — implied

```python
assert read_field(encoding_of(unwindowed), "window_start") == 0
```

window_start is named and "window_start > 0" implies 0 means untrimmed, but nobody says the encoding of a short example exposes window_start == 0.

### `g9.r1.failure_behavior#15` — absent

```python
assert read_field(encoding_of(unwindowed), "token_count") == 6
```

No remark says the encoding itself carries a token_count field; the only counts discussed are on the refusal, and l-rule-2's metadata field is supervised_tokens.

### `g9.r1.failure_behavior#17` — implied

```python
assert read_field(datum_part(batch[0], "metadata"), "num_messages") == 4
```

That the kept example survives the batch is stated, but nobody says the datum's metadata block carries a num_messages field to identify it by.

### `g9.r1.failure_behavior#3` — absent

```python
assert isinstance(error, ValueError)
```

ValueError is never mentioned, and nothing in the corpus says the error hierarchy bottoms out in a builtin.

### `g9.r1.failure_behavior#8` — implied

```python
assert str(error) == (
        "example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would "
        "survive, minimum is 16"
    )
```

The corpus lists which quantities a refusal reports but never the wording, ordering, or the "minimum is 16" tail, and the required string omits num_messages that l-fail-3 says is printed.

### `g9.r1.failure_behavior#9` — implied

```python
assert read_field(encoding_of(datum), "window_start") == 51
```

That a windowed example with enough retained prompt is returned rather than refused is stated, but the surviving datum's window_start of 51 is arithmetic nobody writes down.

### `g9.r1.rule#1` — implied

```python
assert len(weights) == 39
```

The corpus fixes a token cap ("129 tokens against a cap of 40") and that trimming keeps the tail, but nobody says how long the returned weight vector is, so the reader must supply the off-by-one that makes it 39 rather than 40.

### `g9.r1.rule#6` — implied

```python
assert read_field(encoding_of(wide), "window_start") == 41
```

The name window_start is used out loud in h1 and rev1, but nobody says how it is computed from token_count and the cap, so the reader has to derive the value 41 themselves from remarks that only report that the front gets cut.

### `g9.r1.scope#1` — absent

```python
assert read_field(encoding, "tokenizer") is False
```

No remark names an encoding metadata field called "tokenizer" or says the no-tokenizer path flags itself as False in metadata; l-fw-3's inventory of encoding.py lists the role set, error types and FIREWORKS_BYTES_PER_TOKEN and nothing like this.

### `g9.r1.scope#3` — implied

```python
assert read_field(encoding, "window_start") == 0
```

h1 and rev1 use the name window_start and treat window_start > 0 as meaning "we cut something", so a reader can infer 0 for a 9-token example under a 1024 cap, but nobody says the mock path reports window_start at all, let alone 0 when nothing is trimmed.

### `g9.r1.scope#4` — implied

```python
assert read_field(encoding, "supervised_tokens") == 6, (
        "the mock path must honour train_on_assistant_only, with the header inside the span"
    )
```

l-scope-3, l-scope-1 and l-scope-2 do say the no-tokenizer path must be masked like the real one, but nobody says how the mock path locates a span — the character-offset //4 rule and whether the <|assistant|> header falls inside the span are left for the reader to invent, and 6 depends entirely on both.

### `g9.r1.scope#5` — implied

```python
assert weights_of(datum) == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
```

l-scope-2 asks for "the first couple positions dark" on precisely this pair, which gestures at the shape, but the length-8 vector (the shift off a 9-token count) and the exact boundary after two zeros are never said by anyone.

### `g9.r1.scope#6` — implied

```python
assert list(datum_part(datum, "model_input")) == [0, 1, 2, 3, 4, 5, 6, 7]
```

Only l-scope-3's "keep ... exactly as they are" bears on the mock path's outputs; that the token ids are literally range(count) and that model_input is the first eight of nine is nowhere written down.

### `g9.r1.scope#8` — implied

```python
assert read_field(encoding_of(everything.to_tinker_datum(plain)), "supervised_tokens") == 9
```

l-rule-2 names supervised_tokens as a reported field and l-scope-4 gives all-ones weights, but nobody says supervised_tokens counts tokens rather than weight positions, so a reader summing the weights lands on 8, not 9.

### `g9.r2.failure_behavior#4` — implied

```python
with pytest.raises(TokenizerCapabilityError):
```

l18 only reports that a tokenizer with no apply_chat_template turned four hundred examples into drops and that "shouldnt become a batch of drops" — the reader must supply on their own that the alternative is a capability error propagating out of format_batch and aborting, and must supply the class name, since nobody here says either.

### `g9.r2.rule#1` — implied

```python
# The declared shape: exactly these fields, in this order, with these defaults.
    assert dataclasses.is_dataclass(EncodingReport)
```

The word "dataclass" is never said; the reader must supply that "frozen" (l3) plus "compare equal with ==" (l4) plus a fixed field order (l2) means @dataclass rather than NamedTuple, which satisfies every remark and fails this assertion.

### `g9.r2.rule#3` — implied

```python
assert tuple(f.name for f in dataclasses.fields(EncodingReport)) == FIELDS
```

All five names are spoken somewhere and l4 fixes the count at five, but only l2 pins a position ("kept comes first") — the reader has to invent the order of dropped/windowed/dropped_indices/supervised_tokens.

### `g9.r2.scope#2` — absent

```python
assert read_field(encoding_of(datum), "windowed") is True
```

Every mention of "windowed" in the corpus is a per-batch counter on the report (l12, l15); nothing says a returned datum carries a windowed field, let alone that it reads True for a windowed example.

### `g9.r2.scope#4` — absent

```python
# ... and neither does one that raises.
    with pytest.raises(ExampleTooLongError):
```

l1 mentions "the two error classes" without naming either and l17 talks about over-long rows being binned in a batch, not about any call raising, so the name ExampleTooLongError and the fact that to_tinker_datum raises it are nowhere on the page.
