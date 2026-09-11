# g9 — One encoding policy for chat examples

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries; `located` gets the same world as `world` plus a map of where each remark sits, but never a quote, never which requirement a conversation serves, and never which are herrings.

| arm | what it is handed | measured |
|---|---|---|
| `blind` | the ticket | — |
| `spec` | the ticket + both hidden requirements | — |
| `clues` | the ticket + all 57 remarks, quoted | **1.00** |
| `world` | the ticket, against `sweworld:0.4.4` where the 57 remarks live in chat, the wiki and mail | — |
| `located` | the `world` arm plus a map naming each remark's channel, day, minute and length (or its page, or its mail subject) — the search removed, the inference left | **1.00** |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Two requirements, `g9.r1` and `g9.r2`. Neither is written down anywhere an agent
can read: they have to be reassembled from remarks scattered across the world.

**Seven facts, not ten.** `g9.r1` declares four — no `observability`; `g9.r2`
declares three — no `exclusions_or_crossover` and no `observability`. `score.py`
takes its keys from `tasks.json` rather than from a fixed list of five, precisely
so an absent fact is not invented and does not divide the mean by the wrong
number, so each of the seven is worth one seventh. `open_feature` (did the agent
build the feature at all?) carries weight **0.0**: building the feature scores
nothing, only recovering what nobody wrote down does.

Note that the exact values are not gathered under an `observability` fact here —
neither requirement declares one. They sit inside the fact they belong to, marked
**Observable** below, and they are graded as part of it.

The facts, and the question each one answers:

| fact | the question it answers |
|---|---|
| `rule` | what exactly has to exist |
| `scope` | where it applies, and where it must not |
| `exclusions_or_crossover` | what has to stay untouched |
| `failure_behavior` | what happens when it goes wrong |
| `observability` | the exact values a test can read back |

---

### `g9.r1` — a span that starts before the window is zeroed in full

**In one sentence:** loss weight is granted to an assistant span only if the span
*begins* inside the window — a span straddling the boundary earns nothing at all,
not a partial credit — and the no-tokenizer path follows the same policy instead
of its shortcut.

#### `rule` — all-or-nothing at the boundary

An assistant span `(s, e)` contributes weight `1.0` to token indices `[s, e)`
**only when `s >= window_start`**. A span that begins before the window boundary
is **zeroed in full**.

**Observable.** `DataFormatter(max_seq_length=40)` with a one-token-per-character
tokenizer over `[user 'u'*30, assistant 'a'*10, user 'v'*5, assistant 'b'*8]`
(`token_count` 91, `window_start` 51, spans `(48, 59)` and `(82, 91)`):

```python
metadata['encoding']['supervised_tokens'] == 9
sum(loss_fn_inputs['weights']) == 9.0
[i for i, w in enumerate(weights) if w == 1.0] == [30, 31, 32, 33, 34, 35, 36, 37, 38]
```

#### `scope` — the `tokenizer=None` branch obeys the same policy

Its current shortcut goes. What stays:

- the text is still `f'<|{msg.role}|>\n{msg.content}\n'` per message
- the count is still `len(chat_text) // 4`

What changes: `tokens = list(range(len(chat_text) // 4))` goes through the **same
windowing**, and it honours `train_on_assistant_only`.

Spans come from character offsets — for assistant message `i`,
`span = (len_before // 4, len_after // 4)`, where `len_before` is the length of the
text built from `messages[:i]` and `len_after` that of `messages[:i+1]`.

`train_on_assistant_only=False` still yields all-`1.0` weights on **both** paths.

**Observable.** `DataFormatter(max_seq_length=1024)`, no tokenizer,
`[user 'Hello', assistant 'Hi there!']` → `token_count` 9, `window_start` 0, span
`(3, 9)`:

```python
metadata['encoding']['supervised_tokens'] == 6
weights == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
metadata['encoding']['tokenizer'] is False
```

#### `exclusions_or_crossover` — the Fireworks path never windows

`to_jsonl_lines` windows and truncates **nothing**. It drops any serialized line
whose UTF-8 byte length exceeds `self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN`,
where `FIREWORKS_BYTES_PER_TOKEN` is `3` — **strict `>`, not `>=`**.

`FIREWORKS_BYTES_PER_TOKEN` is one of the encoding policy's public names: defined
in `finetune/encoding.py` and re-exported from the `finetune` package, so
`from bespokelabs.curator.finetune import FIREWORKS_BYTES_PER_TOKEN` resolves.

The measurement is `len(line.encode('utf-8'))` on the
`json.dumps(..., ensure_ascii=False)` output.

**Observable.**

| formatter | example | bytes | budget | outcome |
|---|---|---|---|---|
| `FireworksDataFormatter(max_seq_length=30)` | `[user 'qqq', assistant 'ok']` | 90 | 90 | kept |
| same | `[user 'qqqqqq', assistant 'ok']` | 93 | 90 | dropped |
| `max_seq_length=33` | `[user 'héllo wörld', assistant 'ok']` | 100 | 99 | dropped |

so `len(to_jsonl_lines([a, b])) == 1` and `to_jsonl_lines([x]) == []`.

#### `failure_behavior` — the retained-prompt floor

A new exception `ExampleTooLongError(EncodingError)`. `to_tinker_datum` raises it
when the example was windowed (`window_start > 0`) **AND**
`s_last - window_start < 16`, where `s_last` is the start index of the **final**
assistant span.

```python
__init__(self, *, token_count: int, max_seq_length: int,
         retained_prompt_tokens: int, num_messages: int)
```

All four are set as attributes, with
`retained_prompt_tokens = max(0, s_last - window_start)`, and:

```python
str(e) == f'example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16'
```

`format_batch` **skips** a refused example and returns the others.

**Observable.**

| input | at | result |
|---|---|---|
| `[user 'u'*10, assistant 'a'*100]` | `max_seq_length=40` | raises: `token_count == 129`, `max_seq_length == 40`, `retained_prompt_tokens == 0`, `num_messages == 2`, `isinstance(e, ValueError)` |
| `[user 'u'*30, assistant 'a'*10, user 'v'*5, assistant 'b'*8]` | `max_seq_length=40` | returns a datum |
| the same near-miss pair | `max_seq_length=17` | raises with `retained_prompt_tokens == 8` |

#### `observability` — not declared

This requirement has no separate `observability` fact; its exact values are graded
inside the facts above.

> **The herring** — what the team decided first and later reversed: the team first
> shipped the floor as "refuse any example that had to be windowed at all", then
> reversed it to the 16-retained-prompt-token floor after too many legitimate long
> conversations were being dropped.

---

### `g9.r2` — one report on the formatter, reassigned, never returned

**In one sentence:** the batch result is still a plain list, and what happened to
it is recorded on `self.last_report` — which the single-example path never touches,
and which an abort leaves exactly as it was.

#### `rule` — what has to exist

`encoding.py` defines a **frozen** dataclass `EncodingReport` with exactly these
fields, in this order, with these defaults and that spelling:

```python
kept: int = 0
dropped: int = 0
windowed: int = 0
dropped_indices: Tuple[int, ...] = ()
supervised_tokens: int = 0
```

exported from `finetune/__init__.py`.

Both `format_batch` and `FireworksDataFormatter.to_jsonl_lines` **reassign
`self.last_report`** while still returning a plain list.

| field | what it counts |
|---|---|
| `dropped_indices` | the **ascending** tuple of INPUT positions that were dropped |
| `windowed` | only kept examples whose `window_start > 0` |
| `supervised_tokens` | the supervised token counts of **kept examples only** |

`supervised_tokens` and `windowed` are both `0` on the Fireworks path.

**Observable.** `FireworksDataFormatter(max_seq_length=30).to_jsonl_lines([a, b])`
leaves, by dataclass equality:

```python
last_report == EncodingReport(kept=1, dropped=1, windowed=0,
                              dropped_indices=(1,), supervised_tokens=0)
```

#### `scope` — the single-example path never writes it

`to_tinker_datum` never touches `self.last_report` — neither on success nor when it
raises. And a freshly constructed `DataFormatter(max_seq_length=40)` has:

```python
last_report == EncodingReport(kept=0, dropped=0, windowed=0,
                              dropped_indices=(), supervised_tokens=0)
```

#### `exclusions_or_crossover` — not declared

This requirement has no `exclusions_or_crossover` fact. Nothing to implement, and
nothing scored here.

#### `failure_behavior` — only the over-long refusal is absorbed

`format_batch` absorbs **only** `ExampleTooLongError`.

`InvalidRoleSequenceError` and `TokenizerCapabilityError` propagate out of
`format_batch` and abort the pass — they are neither caught nor counted as drops —
and `self.last_report` still holds the value it had **before** the aborted call.

#### `observability` — not declared

This requirement has no separate `observability` fact; its exact values are graded
inside the facts above.

> **The herring** — what the team decided first and later reversed: `format_batch`
> first returned a `(data, report)` tuple; that was reversed when it broke the
> direct forwarding at `tinker_trainer.py:250`, and the report moved onto the
> formatter instance.

---

## Where the remarks are spread

57 remarks in total — 47 clues, 5 herrings and 5 reversals — across 3 surfaces and 6 chat channels. `clues.spread()` reports on this — at least 2 sources, 3 weeks and 2 rooms per requirement, so no single sitting recovers one. It is advisory, not enforced: read the numbers rather than trusting that something refused a plant without them.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **29** | `#code-review` 7, `#engineering` 7, `#pipeline` 6, `#cookbooks` 5, `#releases` 3, `#viewer` 1 |
| wiki (BookStack) | **15** | 15 page comments |
| mail (Roundcube/IMAP) | **13** | 13 separate threads |

> **The wiki remarks are page _comments_, not page bodies.** BookStack's `/api/search` does not index comments, so a term that lives only in one returns nothing. `/api/pages/{id}` returns them alongside the body — an agent that searches instead of enumerating never sees these 15.

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

## g9.r1

### g9.r1.sc-rule — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*The leap nobody states:* weights built over the whole sequence and then sliced along with the tokens will keep the tail of a clipped turn unless something explicitly drops that turn.

- **gideon** (2025-06-10, page:engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md): so basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted.
- **dario** (2025-05-07, thread:new|g9.r1.l-rule-2): honestly i pulled one row out and its encoding carries token_count 52 for everything, supervised_tokens 40 — and twelve of that forty are the tail of an answer we chopped the front off.
- **emil** (2025-03-14, #engineering): honestly i don't think part credit on a turn works - either the whole answer sits inside what we keep or it counts for nothing at all.
- **nils** (2025-06-17, page:engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md): let me think through that, what settles whether a turn is in or out is whether the opening token of its answer survived the cut, the tail end of it is in there either way

### g9.r1.sc-scope — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*The leap nobody states:* if the fallback path shortcuts to all ones, the masking rule has no meaning on the path most tests and cookbooks actually exercise.

- **konrad** (2025-05-06, thread:new|g9.r1.l-scope-1): right, but look — the formatter tests all pass with no tokenizer, becuase that path just hands back all ones, so none of them would notice a masking bug.
- **nikolai** (2025-04-25, #code-review): ran the cookbook token weight snippet with no tokenizer and 'Hello' / 'Hi there!' comes back every weight 1.0 i'd expect the first few dark since thats the question
- **dermot** (2025-06-17, page:engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md): on the no-tokenizer path leave the `<|role|>` text and `len(chat_text) // 4` as they are; a span's ends are that count over messages[:i], then over messages[:i+1].
- **emil** (2025-05-13, thread:new|g9.r1.l-scope-4): let me think through that — with train_on_assistant_only off both paths hand back a flat vector of ones, and the span is the whole example rather than the answer, so supervised_tokens is the token count itself. on the Hello / Hi there! pair thats 9, against 8 weight slots — its the span's end minus its start, never the number of weights.
- **konrad** (2025-05-07, thread:new|g9.r1.say23): look, on your Hello / Hi there! pair the weights come back one shorter than the tokens - eight of them, [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
- **gideon** (2025-06-26, page:engineering/local-offline-inference-what-the-encode-step-returns-when-no-tokenizer-is-loaded.md): so basically on the mock path the encoding reads token_count 9 for the Hello pair, the whole chat_text in one go, ids 0 through 8, model_input the first eight.
- **dario** (2025-04-24, thread:new|g9.r1.say25): honestly the fallback emits the same encoding block as the tokenizer path, window_start and all, and it comes back 0 on any run where we never had to trim
- **nikolai** (2025-06-12, page:engineering/trimming-over-length-rows-for-finetuning-pr-653.md): yep checked the fallback path too window_start is token_count minus max_seq_length either way floored at 0 when it fits so that 129 token row at cap 40 reads 89

### g9.r1.sc-fireworks — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*The leap nobody states:* a limit expressed in tokens becomes a limit on a file measured in bytes only by fixing a bytes-per-token figure and multiplying.

- **emil** (2025-03-20, #cookbooks): honestly i think the cap and the check are in different units - fireworks bounced the entire upload over one long sample, so to_jsonl_lines now works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN and measures each line against that budget in bytes.
- **dario** (2025-06-03, page:engineering/viewer-dataset-download-export-format-notes-pr-652.md): honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact.
- **nikolai** (2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>): on 653 whats in encoding.py so far the role set FIREWORKS_BYTES_PER_TOKEN still 3 ExampleTooLongError off EncodingError and the encoding blocks tokenizer flag False when we ran without one
- **konrad** (2025-03-19, #engineering): look, counting characters was the mistake - it's json.dumps(ensure_ascii=False) with default separators, then len(line.encode('utf-8')), so UTF-8 bytes. the 'qqq'/'ok' pair is 90, and the row landing exactly on the number was fine
- **nikolai** (2025-03-17, #code-review): yep re-checked the accented row at max_seq_length=33 the budget lands at 99 and the line measures 100 so to_jsonl_lines gives back an empty list no trimmed verison

### g9.r1.sc-refuse — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*The leap nobody states:* an example that fits under the limit was never cut, so there is nothing to refuse; the floor only bites on examples the cut actually reached.

- **gideon** (2025-03-24, #cookbooks): so basically the rows that get cut hardest arive as an answer with none of its question left in front of it, and we happily train on those.
- **konrad** (2025-03-19, #releases): look, on the stability item - nightly died on `ExampleTooLongError: example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16`, traceback right after.
- **nils** (2025-03-19, #pipeline): let me think — the line is `example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16`, and num_messages rides along as an attribute, not printed.
- **dermot** (2025-03-17, #pipeline): yeah, that's my read as well — one row we won't take shouldn't take the other forty thousand down with it, and anything that fits under the cap goes through however short its question is.
- **emil** (2025-03-14, #code-review): one more on the error shape - EncodingError subclasses ValueError, so anything already catching ValueError around the encoder still catches it. keeping it that way.
- **dermot** (2025-06-12, page:engineering/what-the-finetuning-encoder-emits-per-datum-and-how-it-behaves-at-the-length-cap.md): yeah ok — at max_seq_length=40 the four-message near-miss does come back a datum: encoding reads window_start 51, and the weights come back 39 long, one short of the max_seq_length window we keep.
- **gideon** (2025-04-03, #cookbooks): so basically even after a skip i can still tell what came back — every datum's metadata block carries num_messages, and the four-message row was sitting right there

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled the windowing question: if window_start > 0 at all, to_tinker_datum raises ExampleTooLongError. an example we had to cut isn't really an example anymore, it's an artifact
- **konrad** (2025-01-22): Right, refusal is binary, windowed at all means refused, format_batch just skips that example and carrys on. An example we never cut still shows window_start 0 in its encoding.

## g9.r2

### g9.r2.sc1 — The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.

*The leap nobody states:* a number people paste into tickets and assert on in tests has to be fixed once written and comparable as a whole object.

- **dario** (2025-05-13, thread:new|g9.r2.l1): the surface is small, honestly: encoding.py is ALLOWED_ROLES, InvalidRoleSequenceError, TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune.
- **konrad** (2025-06-24, page:engineering/per-example-stats-from-the-windowed-export-review-notes-653-follow-on.md): nit: docstring says skipped but the attribute is dropped. also the field order is kept, dropped, windowed, dropped_indices, supervised_tokens, your exmaple builds it the other way round.
- **emil** (2025-04-18, #engineering): related - a cleanup bumped a counter on an EncodingReport after the batch had finished, so the figure i pasted in the ticket was wrong. frozen=True on it, its finished when format_batch hands it back
- **nikolai** (2025-04-18, #engineering): spelling out all five counts in every assert makes these unreadable i'd say make EncodingReport a dataclass with defaults so EncodingReport() is empty and two of them compare with ==

### g9.r2.sc2 — The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.

*The leap nobody states:* if callers ask the object itself for the last batch's summary, only calls that actually process a batch have any business changing what it says.

- **dermot** (2025-06-26, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md): yeah — counted binned rows by hand off the upload log again, so the summary comes off the formatter afterwards. that said, format_batch still hands back a plain list.
- **konrad** (2025-05-13, thread:new|g9.r2.l6): stats passed on your branch? self.last_report is set in format_batch but not to_jsonl_lines, after my fireworks run it still had the previous batch numbers. both should set it.
- **emil** (2025-03-21, #pipeline): pushed one example through to_tinker_datum in the repl to debug it and self.last_report came back untouched, same when the call raised, so it leaves it alone either way
- **gideon** (2025-05-14, page:engineering/end-of-run-summary-tables-how-the-formatters-are-wired.md): so basically i constructed a formatter, asked it for its report, got None back, so all my callers have null checks now. fresh one should already hold an empty report tbh.

### g9.r2.sc3 — dropped_indices holds the positions the dropped examples occupied in the list the caller passed in, in that order.

*The leap nobody states:* a position is only useful to the person holding the input if it is numbered against the input they handed over.

- **gideon** (2025-04-28, #viewer): tbh i chased dropped_indices back to my input file — came back (0, 1) when the rows i binned were 3 and 7. numbered among the ones we skipped.
- **nikolai** (2025-05-13, #pipeline): yep same on the fireworks pass — to_jsonl_lines numbered dropped_indices against the rows we wrote out, not the list i submitted, so i greped the wrong lines.
- **nils** (2025-04-02, page:meetings/weekly-notes-week-of-mar-31.md): on 615 — let me think, simplest is dropped_indices numbered against the list i handed in, in that order, so i index straight back into my own examples.

### g9.r2.sc4 — windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.

*The leap nobody states:* a count about tokens or about trimming can only describe work that really happened on rows that really shipped.

- **nils** (2025-04-11, #cookbooks): windowed came back as nine on a batch that wrote six lines. each datum's encoding reads windowed True fine, the total just shouldnt count rows we dropped.
- **dermot** (2025-04-16, thread:new|g9.r2.l13): one more correction while we're on token counts: supervised_tokens in the release notes is inflated, it counted the long examples we dropped from the batch. it shouldn't.
- **emil** (2025-05-20, page:engineering/finetuning-export-what-the-end-of-run-summary-counts.md): yup - if a row never made it into the output it shouldnt land in the trim count or the token total either, both summed over kept examples only.
- **dario** (2025-05-14, thread:new|g9.r2.l15): honestly the fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise — both read zero there.

### g9.r2.sc5 — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*The leap nobody states:* an error that says the caller's data or setup is wrong is not a row you can skip on their behalf and keep going.

- **nikolai** (2025-03-24, #pipeline): the tool role example got swallowd into the drop count last night run carried on and we shipped a file missing the rows i needed thats not a drop
- **dario** (2025-06-17, page:engineering/request-builder-what-we-drop-and-what-we-raise-on.md): honestly if the role sequence is bad thats my data being broken, not a row to quietly skip - only the over-long ones should get binned and counted
- **gideon** (2025-03-14, #code-review): Same shape here, handed format_batch a tokenizer with no apply_chat_template and it chewed through four hundred exmaples calling every one a drop. That shouldnt become a batch of drops.
- **dermot** (2025-04-14, thread:<178769930038.2250839.2605881431154859866@world.local>): One review note on 632: when the batch aborted halfway, self.last_report had already been half updated — it should still read whatever the last good run left.
- **dario** (2025-05-28, thread:new|g9.r2.say23): and to_tinker_datum just raises ExampleTooLongError outright — the binning is format_batch's job, honestly a single datum has no batch to be counted into.
- **dario** (2025-06-11, page:engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md): re gideon's tokenizer - no apply_chat_template on it, so format_batch raises TokenizerCapabilityError right there, pass stops, nothing gets binned as a drop
- **dario** (2025-05-28, thread:new|g9.r2.say23): Length and role sequence are row problems — one bad row says nothing about the next row, so those get counted and skipped
- **dario** (2025-06-17, page:engineering/request-builder-what-we-drop-and-what-we-raise-on.md): and yes this is me contradicting myself - the split i gave on the 653 thread back in may, length and role sequence both being row problems, that half of it was wrong and im dropping it. only the over-long ones are row problems.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled then: format_batch hands back (data, report), datums first and the EncodingReport second, callers unpack it. nothing else carries the counts.
- **konrad** (2025-01-22): Right, made a start on 362 — signature in review is `format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]`, so the report rides out with the data.


---


## Where every remark is

57 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-21 | chat | #code-review | nikolai | [`g9.r1.h1`](#g9r1h1) | 7 | **herring** | — |
| 2025-01-21 | chat | #releases | konrad | [`g9.r2.g9-tuple-return-1`](#g9r2g9-tuple-return-1) | 9 | **herring** | — |
| 2025-01-22 | chat | #code-review | dermot | [`g9.r1.h2`](#g9r1h2) | 7 | **herring** | — |
| 2025-01-22 | chat | #code-review | dermot | [`g9.r2.g9-tuple-return-2`](#g9r2g9-tuple-return-2) | 8 | **herring** | — |
| 2025-03-14 | chat | #code-review | emil | [`g9.r2.l18`](#g9r2l18) | 7 | clue | `failure_behavior` |
| 2025-03-14 | chat | #engineering | dermot | [`g9.r1.l-rule-3`](#g9r1l-rule-3) | 7 | clue | `rule` |
| 2025-03-14 | chat | #code-review | gideon | [`g9.r1.say20`](#g9r1say20) | 7 | clue | `failure_behavior` |
| 2025-03-17 | chat | #pipeline | dario | [`g9.r1.l-fail-4`](#g9r1l-fail-4) | 7 | clue | `failure_behavior` |
| 2025-03-17 | chat | #code-review | emil | [`g9.r1.say26`](#g9r1say26) | 9 | clue | `exclusions_or_crossover` |
| 2025-03-19 | chat | #releases | dermot | [`g9.r1.l-fail-2`](#g9r1l-fail-2) | 9 | clue | `failure_behavior` |
| 2025-03-19 | chat | #releases | konrad | [`g9.r2.rev1`](#g9r2rev1) | 8 | **reversal** of `g9.r2.g9-tuple-return-1` | `rule` |
| 2025-03-19 | chat | #pipeline | gideon | [`g9.r1.l-fail-3`](#g9r1l-fail-3) | 9 | clue | `failure_behavior` |
| 2025-03-19 | chat | #engineering | gideon | [`g9.r1.l-fw-4`](#g9r1l-fw-4) | 9 | clue | `exclusions_or_crossover` |
| 2025-03-20 | chat | #cookbooks | dario | [`g9.r1.l-fw-1`](#g9r1l-fw-1) | 7 | clue | `exclusions_or_crossover` |
| 2025-03-21 | chat | #pipeline | dario | [`g9.r2.l7`](#g9r2l7) | 6 | clue | `scope` |
| 2025-03-21 | chat | #cookbooks | dario | [`g9.r2.rev2`](#g9r2rev2) | 9 | **reversal** of `g9.r2.g9-tuple-return-2` | `rule` |
| 2025-03-24 | chat | #cookbooks | emil | [`g9.r1.l-fail-1`](#g9r1l-fail-1) | 8 | clue | `failure_behavior` |
| 2025-03-24 | chat | #pipeline | dario | [`g9.r2.l16`](#g9r2l16) | 8 | clue | `failure_behavior` |
| 2025-04-02 | wiki comment | docs/meetings/weekly-notes-week-of-mar-31.md | nils | [`g9.r2.l11`](#g9r2l11) | 2 | clue | `rule` |
| 2025-04-03 | chat | #cookbooks | konrad | [`g9.r1.say22`](#g9r1say22) | 8 | clue | `failure_behavior` |
| 2025-04-11 | chat | #cookbooks | dario | [`g9.r2.l12`](#g9r2l12) | 8 | clue | `rule` |
| 2025-04-14 | mail | “Re: Weekly update: week of Apr 7” | dermot | [`g9.r2.l19`](#g9r2l19) | 4 | clue | `failure_behavior` |
| 2025-04-15 | chat | #engineering | nikolai | [`g9.r1.rev2`](#g9r1rev2) | 8 | **reversal** of `g9.r1.h2` | `failure_behavior` |
| 2025-04-16 | mail | “Dataset card numbers before we publish the reasoning set” | emil | [`g9.r2.l13`](#g9r2l13) | 4 | clue | `rule` |
| 2025-04-18 | chat | #engineering | gideon | [`g9.r2.l4`](#g9r2l4) | 8 | clue | `rule` |
| 2025-04-18 | chat | #engineering | emil | [`g9.r2.l3`](#g9r2l3) | 2 | clue | `rule` |
| 2025-04-24 | mail | “user question: does a local run without the tokenizer extra still report encoding stats” | dario | [`g9.r1.say25`](#g9r1say25) | 3 | clue | `scope` |
| 2025-04-24 | chat | #engineering | emil | [`g9.r1.rev1`](#g9r1rev1) | 9 | **reversal** of `g9.r1.h1` | `failure_behavior` |
| 2025-04-25 | chat | #code-review | gideon | [`g9.r1.l-scope-2`](#g9r1l-scope-2) | 8 | clue | `scope` |
| 2025-04-28 | chat | #viewer | gideon | [`g9.r2.l9`](#g9r2l9) | 7 | clue | `rule` |
| 2025-05-06 | mail | “PR 653: formatter still takes tokenizer=None” | dermot | [`g9.r1.l-scope-1`](#g9r1l-scope-1) | 4 | clue | `scope` |
| 2025-05-07 | mail | “PR 653 before the next cut” | nikolai | [`g9.r1.say23`](#g9r1say23) | 4 | clue | `scope` |
| 2025-05-07 | mail | “PR 653 — ran a curated set through the encode path” | dario | [`g9.r1.l-rule-2`](#g9r1l-rule-2) | 4 | clue | `rule` |
| 2025-05-13 | mail | “PR 653 — where does role validation live, and what do the cookbooks import” | nikolai | [`g9.r2.l1`](#g9r2l1) | 4 | clue | `rule` |
| 2025-05-13 | mail | “stats report branch — need someone to run it before the 0.1.25 cut” | emil | [`g9.r2.l6`](#g9r2l6) | 4 | clue | `rule` |
| 2025-05-13 | mail | “sft export — fast tokenizer and manual fallback return different label weights” | konrad | [`g9.r1.l-scope-4`](#g9r1l-scope-4) | 4 | clue | `scope` |
| 2025-05-13 | chat | #pipeline | gideon | [`g9.r2.l10`](#g9r2l10) | 7 | clue | `rule` |
| 2025-05-14 | mail | “PR 653 — what goes in the stats dict when the backend doesnt tokenize” | nikolai | [`g9.r2.l15`](#g9r2l15) | 4 | clue | `rule` |
| 2025-05-14 | wiki comment | docs/engineering/end-of-run-summary-tables-how-the-formatters-are-wired.md | gideon | [`g9.r2.l8`](#g9r2l8) | 2 | clue | `scope` |
| 2025-05-20 | wiki comment | docs/engineering/finetuning-export-what-the-end-of-run-summary-counts.md | emil | [`g9.r2.l14`](#g9r2l14) | 2 | clue | `rule` |
| 2025-05-28 | mail | “PR 653: which layer drops a bad row, and who counts it” | nikolai | [`g9.r2.say23`](#g9r2say23) | 4 | clue | `scope` |
| 2025-05-28 | mail | “Re: PR 653: which layer drops a bad row, and who counts it” | dario | [`g9.r2.h-role-row`](#g9r2h-role-row) | 1 | **herring** | — |
| 2025-06-03 | wiki comment | docs/engineering/viewer-dataset-download-export-format-notes-pr-652.md | dario | [`g9.r1.l-fw-2`](#g9r1l-fw-2) | 2 | clue | `exclusions_or_crossover` |
| 2025-06-10 | wiki comment | docs/engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md | gideon | [`g9.r1.l-rule-1`](#g9r1l-rule-1) | 3 | clue | `rule` |
| 2025-06-11 | chat | #engineering | nikolai | [`g9.r1.fix28`](#g9r1fix28) | 6 | clue | `scope` |
| 2025-06-11 | wiki comment | docs/engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md | dario | [`g9.r2.say24`](#g9r2say24) | 2 | clue | `failure_behavior` |
| 2025-06-12 | wiki comment | docs/engineering/what-the-finetuning-encoder-emits-per-datum-and-how-it-behaves-at-the-length-cap.md | dermot | [`g9.r1.say21`](#g9r1say21) | 2 | clue | `failure_behavior` |
| 2025-06-12 | wiki comment | docs/engineering/trimming-over-length-rows-for-finetuning-pr-653.md | nikolai | [`g9.r1.say27`](#g9r1say27) | 2 | clue | `rule` |
| 2025-06-16 | mail | “Re: Week of Jun 9 recap: bulk inference fix” | nikolai | [`g9.r1.l-fw-3`](#g9r1l-fw-3) | 3 | clue | `exclusions_or_crossover` |
| 2025-06-17 | wiki comment | docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md | dario | [`g9.r2.l17`](#g9r2l17) | 2 | clue | `failure_behavior` |
| 2025-06-17 | wiki comment | docs/engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md | dermot | [`g9.r1.l-scope-3`](#g9r1l-scope-3) | 2 | clue | `scope` |
| 2025-06-17 | wiki comment | docs/engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md | nils | [`g9.r1.l-rule-4`](#g9r1l-rule-4) | 2 | clue | `rule` |
| 2025-06-17 | wiki comment | docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md | dario | [`g9.r2.rev3`](#g9r2rev3) | 1 | **reversal** of `g9.r2.h-role-row` | `failure_behavior` |
| 2025-06-24 | wiki comment | docs/engineering/per-example-stats-from-the-windowed-export-review-notes-653-follow-on.md | konrad | [`g9.r2.l2`](#g9r2l2) | 2 | clue | `rule` |
| 2025-06-26 | wiki comment | docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | dermot | [`g9.r2.l5`](#g9r2l5) | 2 | clue | `rule` |
| 2025-06-26 | wiki comment | docs/engineering/local-offline-inference-what-the-encode-step-returns-when-no-tokenizer-is-loaded.md | gideon | [`g9.r1.say24`](#g9r1say24) | 2 | clue | `scope` |
| 2025-07-10 | chat | #pipeline | gideon | [`g9.r2.fix25`](#g9r2fix25) | 8 | clue | `rule` |

#### `g9.r1.h1` · **herring**

- **chat** · #code-review · **nikolai** · 2025-01-21 14:03
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> settled the windowing question: if window_start > 0 at all, to_tinker_datum raises ExampleTooLongError. an example we had to cut isn't really an example anymore, it's an artifact

As it appears, spread across the exchange:

```
14:03  nikolai   what is to_tinker_datum supposed to do when window_start comes back nonzero
14:06  konrad    it raises. ExampleTooLongError
14:07  nikolai   even if its off by a token or two
14:09  konrad    presumably yes but off the top of my head i am not entirely sure if we said any nonzero or there is some slack
14:16  dario     any nonzero. if window_start > 0 at all it raises, no slack — honestly an example we had to cut isnt really an example anymore, its an artifact
14:16  nikolai   right thats gonna take out a chunk of the long ones
14:18  konrad    mhm. i had it the other way round in my head, that it would just hand back the shortened one. good that i asked before writing it
```

#### `g9.r2.g9-tuple-return-1` · **herring**

- **chat** · #releases · **konrad** · 2025-01-21 15:11
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> settled then: format_batch hands back (data, report), datums first and the EncodingReport second, callers unpack it. nothing else carries the counts.

As it appears, spread across the exchange:

```
15:11  konrad    quick one - format_batch, where do the encoding counts come out now? i dont see them on the object anywhere
15:15  dario     it hands back a pair, the datums and the report together. you unpack at the call site
15:16  konrad    which order
15:18  dario     datums first, EncodingReport second. so data, report = format_batch(...)
15:20  konrad    ok and is it stashed anywhere too? i have a spot that only wants the counts, would be nice to just read them
15:24  dario     no, the return is the only place they live. nothing else carries them, so if you want counts you take them out of what you unpacked. honestly i think thats the cleaner shape anyway
15:26  dermot    so restating - anything currently treating the return as just the datums breaks on the unpack and needs touching
15:27  dario     right, and i havent been through the call sites yet. nobody has written any of it
15:29  dermot    yeah ok. the batch runner is one of those, if i had to guess
```

#### `g9.r1.h2` · **herring**

- **chat** · #code-review · **dermot** · 2025-01-22 15:11
- carries nothing — it is here to be wrong
- must be typed literally: `format_batch`, `window_start`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Right, refusal is binary, windowed at all means refused, format_batch just skips that example and carrys on. An example we never cut still shows window_start 0 in its encoding.

As it appears, spread across the exchange:

```
15:11  dermot    quick one on the windowing while i have it open — if an example gets cut at all, is that a partial refusal or is the whole thing refused
15:14  nikolai   binary windowed at all means refused theres no half state
15:17  dermot    yeah ok. so the refused one just never lands in the batch, or does something downstream have to look at a flag
15:20  konrad    no flag. format_batch skips that example and carrys on
15:22  dermot    that leaves the bit i keep tripping over then. an example we never cut still shows window_start 0 in its encoding
15:25  konrad    right but thats a measured 0, not an empty field. the windowing runs either way, so it comes back saying the window starts at the front. nothing is being left unset there
15:28  nikolai   huh yep thats not how i had it in my head i had that 0 down as nobody having filled the field in
```

#### `g9.r2.g9-tuple-return-2` · **herring**

- **chat** · #code-review · **dermot** · 2025-01-22 18:15
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Right, made a start on 362 — signature in review is `format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]`, so the report rides out with the data.

As it appears, spread across the exchange:

```
15:02  dermot    362 still has nobodys name on it as far as i can tell
15:04  konrad    i made a start on it this morning. only a start
15:06  dermot    ok. whats format_batch taking now, if i had to guess still just the examples
15:08  konrad    examples and the tokenizer. thats whats in review — format_batch(examples, tokenizer)
15:10  emil      and it hands back the encoded list same as before i believe? or is something else coming out of it
15:12  konrad    -> Tuple[List[Any], EncodingReport]. the list, and the report next to it
15:14  emil      hm. so the report comes out of the call itself, not read off somewhere after
15:16  konrad    right, it rides out with the data. anyway the body isnt written yet, just the signature
```

#### `g9.r2.l18`

- **chat** · #code-review · **emil** · 2025-03-14 12:48
- carries `g9.r2.failure_behavior`
- must be typed literally: `format_batch`, `apply_chat_template`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Same shape here, handed format_batch a tokenizer with no apply_chat_template and it chewed through four hundred exmaples calling every one a drop. That shouldnt become a batch of drops.

As it appears, spread across the exchange:

```
13:19  emil      same shape as your notebook thing this morning i think. i handed format_batch a tokenizer that has no apply_chat_template on it
13:21  dario     and did it raise there or did it just carry on
13:23  emil      carried on. chewed through four hundred exmaples and called every one of them a drop
13:25  gideon    wait the whole file came back drops? um. thats not really a batch then
13:26  emil      yup. a drop is supposed to be the odd row that didnt fit, not the entire input
13:28  gideon    exactly, so basically that shouldnt become a batch of drops. if the tokenizer cant do apply_chat_template then format_batch stops there, honestly though its one broken tokenizer, not four hundred broken rows
13:33  dario     mhm. same as construciton handing back a dead object, just three calls further down
```

#### `g9.r1.l-rule-3`

- **chat** · #engineering · **dermot** · 2025-03-14 13:21
- carries `g9.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly i don't think part credit on a turn works - either the whole answer sits inside what we keep or it counts for nothing at all.

As it appears, spread across the exchange:

```
13:21  dermot    back on the turn scoring question from yesterday. if part of the answer falls outside what we keep, is that a partial? half in, half the points
13:24  emil      honestly i dont think part credit on a turn works. its one or the other
13:25  dermot    one or the other on what basis though. kept vs not kept is doing a lot of work in that sentence
13:27  emil      the whole answer has to sit inside what we keep, thats the condition. all of it
13:28  dario     and when it straddles the edge? some of it survived
13:30  emil      then it counts for nothing at all. no fraction for the bit that made it
13:32  dario     mhm ok. that takes out the overlap math i had half written
```

#### `g9.r1.say20`

- **chat** · #code-review · **gideon** · 2025-03-14 13:43
- carries `g9.r1.failure_behavior`
- must be typed literally: `EncodingError`, `ValueError`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one more on the error shape - EncodingError subclasses ValueError, so anything already catching ValueError around the encoder still catches it. keeping it that way.

As it appears, spread across the exchange:

```
13:43  gideon    quick thing on the encoder before i forget - it raises its own error type now right? does that break people catching around it
13:45  emil      shouldnt. EncodingError isnt a fresh branch off on its own, it sits under ValueError
13:46  gideon    hm ok but the existing call sites catch ValueError, not the new name. so what happens there
13:47  dario     thats the bit i wasnt sure about either honestly
13:49  emil      thats the whole reason for the shape - anything already catching ValueError around the encoder still catches it. no edits at those sites
13:50  emil      and we're keeping it that way, i dont want somebody making it standalone in six months and quietly breaking every handler. still needs writing, but thats the shape it gets written to
13:52  gideon    ya ok. i had half a rewrite of those try/excepts in my head, binning that
```

#### `g9.r1.l-fail-4`

- **chat** · #pipeline · **dario** · 2025-03-17 13:36
- carries `g9.r1.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah, that's my read as well — one row we won't take shouldn't take the other forty thousand down with it, and anything that fits under the cap goes through however short its question is.

As it appears, spread across the exchange:

```
13:36  dario     nightly came back empty. one row over the cap and the whole submission got rejected
13:38  emil      yup, chased that this morning. one row we wont take shouldnt take the other forty thousand down with it
13:41  dario     so skip that one and send the rest. writer is all or nothing today, nothing in it survives a bad row
13:44  emil      right. it just gives up
13:46  dario     and the other end — we still bounce the very short prompts before the cap ever comes into it. keeping that or dropping it
13:49  dermot    yeah, thats my read as well. no floor worth defending — anything that fits under the cap goes through however short its question is
13:51  dario     mhm. the tiny ones are mostly retry stubs anyway
```

#### `g9.r1.say26`

- **chat** · #code-review · **emil** · 2025-03-17 14:02
- carries `g9.r1.exclusions_or_crossover`
- must be typed literally: `max_seq_length=33`, `to_jsonl_lines`, `99`, `100`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yep re-checked the accented row at max_seq_length=33 the budget lands at 99 and the line measures 100 so to_jsonl_lines gives back an empty list no trimmed verison

As it appears, spread across the exchange:

```
14:02  emil      did we ever get to the bottom of the accented rows coming back empty out of to_jsonl_lines
14:04  nikolai   yep re-checked one of them this morning  that run was max_seq_length=33
14:05  emil      and the budget off that
14:06  nikolai   lands at 99  its three times the seq length so 33 gets you there
14:08  emil      so if im reading you right the accented line comes in just past that
14:09  nikolai   the line measures 100  one over
14:11  konrad    and then? it hands back a shortened one, or nothing
14:12  nikolai   nothing  to_jsonl_lines gives back an empty list  theres no trimmed verison of the row anywhere
14:14  emil      yup thats the shape i was seeing in the counts, honestly couldnt tell if it was dropping or trimming
```

#### `g9.r1.l-fail-2`

- **chat** · #releases · **dermot** · 2025-03-19 11:51
- carries `g9.r1.failure_behavior`
- must be typed literally: `ExampleTooLongError`, `example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, on the stability item - nightly died on `ExampleTooLongError: example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16`, traceback right after.

As it appears, spread across the exchange:

```
12:02  dermot    emil hasnt come back on the stability item yet. if i had to guess the two green CI runs is what closes it
12:04  konrad    look, that item is not clean. nightly died last night
12:05  dermot    died as in flaky, or died as in it stopped
12:07  konrad    stopped. ExampleTooLongError, and the traceback right after it
12:09  emil      which limit did it trip though, i believe we have a couple of them in there
12:12  konrad    "example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16" - thats the whole line
12:14  dermot    mhm. zero surviving, so theres nothing left to trim down to
12:16  konrad    right. so green CI is not enough for that item, it stays open and it doesnt go in this cut
12:18  dermot    yeah ok. i had that line half crossed off in the weekly notes, putting it back
```

#### `g9.r2.rev1` · **reversal**

- **chat** · #releases · **konrad** · 2025-03-19 13:22
- carries `g9.r2.rule`
- takes back `g9.r2.g9-tuple-return-1`
- must be typed literally: `format_batch`, `self.last_report`, `EncodingReport`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> reverting the (data, report) tuple from format_batch, it broke the hand-off at tinker_trainer.py:250 - plain list of datums again and the counts sit on self.last_report as an EncodingReport

As it appears, spread across the exchange:

```
13:22  konrad    what actually broke on the trainer side yesterday? someone said format_batch
13:25  dario     the tuple. we settled months ago that it hands back (data, report), datums first and the EncodingReport second, and callers unpack it, nothing else carrying the counts. thats gone as of this morning, we're reverting it
13:26  konrad    gone why, off the top of my head that unpack sits in more than one place
13:29  dario     it broke the hand off at tinker_trainer.py:250. that end wants datums and got handed a tuple instead. so its a plain list of datums again, like before
13:31  emil      and the counts? that was the whole reason for the second element, nothing else was carrying them
13:33  dario     they sit on self.last_report now. still an EncodingReport, you just read it off after the call rather than unpacking it
13:34  konrad    right. so the callers stop unpacking, thats the change
13:36  emil      yup. honestly i've lost track of what the tuple was buying us over that
```

#### `g9.r1.l-fail-3`

- **chat** · #pipeline · **gideon** · 2025-03-19 14:03
- carries `g9.r1.failure_behavior`
- must be typed literally: `example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16`, `max_seq_length`, `num_messages`, `retained_prompt_tokens`, `token_count`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think — the line is `example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16`, and num_messages rides along as an attribute, not printed.

As it appears, spread across the exchange:

```
14:03  gideon    quick one before i forget. when an example is too long to fit, what does the refusal actually say? my logs just show a skip and a number
14:05  nils      it puts the example's token_count next to the max_seq_length it went past. those two are in there for certain
14:06  gideon    ya but thats the part i already have. what i want is how much of the prompt would still be left, otherwise i cant tell if reshaping the example is worth it or i just drop it
14:10  nils      fair enough. let me think — the refusal line reads exactly: example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16
14:12  dermot    so if i'm reading that right, the text says nothing about how many messages the example had
14:13  nils      correct. num_messages rides along as an attribute, it isn't printed.
14:15  dermot    yeah ok. that said none of this is on a branch yet is it, i went looking earlier
14:16  nils      not yet, someone still has to write it. maybe it goes on the batch ticket, i don't much mind which
14:17  gideon    so my alert is matching the old wording then. explains the silence
```

#### `g9.r1.l-fw-4`

- **chat** · #engineering · **gideon** · 2025-03-19 14:03
- carries `g9.r1.exclusions_or_crossover`
- must be typed literally: `'qqq'/'ok'`, `90`, `UTF`, `json.dumps(ensure_ascii=False)`, `len(line.encode('utf-8'))`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, counting characters was the mistake - it's json.dumps(ensure_ascii=False) with default separators, then len(line.encode('utf-8')), so UTF-8 bytes. the 'qqq'/'ok' pair is 90, and the row landing exactly on the number was fine

As it appears, spread across the exchange:

```
14:03  gideon    my sanity check on the jsonl rows disagrees with what the code decides, every time. so basically i measured the line myself and got something smaller
14:05  dermot    if i'm reading that right you measured the string length? characters, not what actually goes out
14:06  gideon    ya, len of the line
14:08  konrad    look, counting characters was the mistake. it is len(line.encode('utf-8')) that we go on, so bytes
14:09  gideon    UTF-8 bytes of what though, the row as we built it or the serialized thing
14:11  konrad    the serialized one. json.dumps(ensure_ascii=False) with the default separators, and that line is what gets measured
14:12  gideon    ok that explains my gap. and the 'qqq'/'ok' pair, what does that land at
14:14  konrad    90. and the row that came out exactly on the number was fine, that one was never the failure
14:16  dermot    mhm, that tracks with the two rows i pulled last night
```

#### `g9.r1.l-fw-1`

- **chat** · #cookbooks · **dario** · 2025-03-20 13:04
- carries `g9.r1.exclusions_or_crossover`
- must be typed literally: `FIREWORKS_BYTES_PER_TOKEN`, `max_seq_length`, `to_jsonl_lines`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly i think the cap and the check are in different units - fireworks bounced the entire upload over one long sample, so to_jsonl_lines now works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN and measures each line against that budget in bytes.

As it appears, spread across the exchange:

```
13:04  dario     what happened with the fireworks upload yesterday, it came back rejected whole?
13:06  emil      yup. one long sample and they bounced the entire upload over it, not just that record
13:08  dario     but our own check passed the file first? so either the check is wrong or their limit is not what we think it is
13:09  emil      honestly i think the cap and the check are just in different units
13:11  dermot    mhm. so if i'm reading that right the cap we have is in tokens and the thing we were comparing it against was never tokens
13:13  emil      right. so to_jsonl_lines works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN, and thats the budget every line gets measured against, in bytes
13:14  dermot    yeah ok. that would explain why nothing local ever fired on that file
```

#### `g9.r2.l7`

- **chat** · #pipeline · **dario** · 2025-03-21 13:12
- carries `g9.r2.scope`
- must be typed literally: `self.last_report`, `to_tinker_datum`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> pushed one example through to_tinker_datum in the repl to debug it and self.last_report came back untouched, same when the call raised, so it leaves it alone either way

As it appears, spread across the exchange:

```
13:12  dario     if i run to_tinker_datum on a single example by hand while debugging, does that leave state on the object? thinking of self.last_report specifically
13:14  emil      it doesnt. i pushed one example through it in the repl yesterday to debug exactly this and last_report came back untouched
13:15  dario     thats when it returns cleanly though. what about when the call raises partway
13:16  gideon    ya thats the one id worry about tbh
13:18  emil      same, so i made it raise on purpose and looked after — untouched there too. it leaves it alone either way
13:20  gideon    ok then im just calling it straight on the row that fails, beats the print statements i have sitting in there now
```

#### `g9.r2.rev2` · **reversal**

- **chat** · #cookbooks · **dario** · 2025-03-21 14:03
- carries `g9.r2.rule`
- takes back `g9.r2.g9-tuple-return-2`
- must be typed literally: `format_batch`, `EncodingReport`, `to_jsonl_lines`, `self.last_report`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, the signautre I signed off on, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], is dropped - the unpack at tinker_trainer.py:250 broke forwarding. Return is List[Any], and format_batch and to_jsonl_lines both reassign self.last_report.

As it appears, spread across the exchange:

```
14:03  dario     konrad quick one before i touch the encoder path today — is 362 as it stands in review still the thing to build against
14:07  konrad    no. look, the signautre I signed off on there, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], report riding out alongside the data — thats dropped
14:09  dario     dropped on taste or dropped because something actually broke
14:14  konrad    broke. the unpack at tinker_trainer.py:250, forwarding stopped the moment the return was two things instead of one. so the return is List[Any], plain
14:16  nikolai   and the report lives where now
14:20  konrad    self.last_report. format_batch reassigns it, and to_jsonl_lines reassigns it too
14:23  dario     mhm. none of that is written yet i take it
14:25  konrad    not yet, presumably whoever picks 362 back up. its just the shape at the moment
14:28  nikolai   fine by me mine reads it after the jsonl call anyway so theres nothing on my side to move
```

#### `g9.r1.l-fail-1`

- **chat** · #cookbooks · **emil** · 2025-03-24 15:11
- carries `g9.r1.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically the rows that get cut hardest arive as an answer with none of its question left in front of it, and we happily train on those.

As it appears, spread across the exchange:

```
15:11  emil      pulled a handful of rows out of the export and a few of them just start mid answer. not entirely sure if thats us or the viewer
15:13  gideon    its us. the rows that get cut hardest are the ones youre looking at
15:14  emil      cut hardest as in the longest ones. and the cut eats forward from the front of the row, i take it
15:16  gideon    ya. so basically what arives is an answer with none of its question left in front of it
15:17  konrad    and something drops those before training, presumably
15:18  gideon    thats the thing, no. we happily train on those
15:19  gideon    honestly though thats not defensible. no question left, the row doesnt go in. i dunno which ticket it lands on but thats what were doing
15:20  konrad    mhm. i had been putting those down to the preview rendering badly
```

#### `g9.r2.l16`

- **chat** · #pipeline · **dario** · 2025-03-24 15:11
- carries `g9.r2.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the tool role example got swallowd into the drop count last night run carried on and we shipped a file missing the rows i needed thats not a drop

As it appears, spread across the exchange:

```
15:11  dario     pulled the eval file this morning and the tool role example isnt in it. dropped or never generated
15:16  nikolai   dropped as far as the counter is concerned it got swallowd into the drop count
15:20  dario     swallowed how though, it wasnt malformed. and nothing complained during the run?
15:24  nikolai   no the run carried on last night finished like normal
15:27  dario     so we shipped a file missing the rows i needed and the totals still looked fine. thats the part that bothers me honestly
15:31  dermot    mhm thats the same file i staged off last nights run
15:35  nikolai   right and thats the thing its not a drop it has no business landing in that count
15:39  dermot    yeah ok. so it comes out of there. nobody has written that yet obviously
```

#### `g9.r2.l11`

- **wiki comment** · docs/meetings/weekly-notes-week-of-mar-31.md · **nils** · 2025-04-02 10:42
- carries `g9.r2.rule`
- must be typed literally: `dropped_indices`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> on 615 — let me think, simplest is dropped_indices numbered against the list i handed in, in that order, so i index straight back into my own examples.

As it appears, spread across the exchange:

```
10:42  nils      the 615 line above says it finally gives us visibility into where batch requests are breaking, which is true as far as it goes, but it does not say what that output is keyed against, and that is the part i had to decide while writing the failed-request path. let me think through it here so it is at least written down somewhere.  simplest option, and the one i've gone with: `dropped_indices`, numbered against the request list as it was handed in, in that order. not the provider's ordering, not the order things happen to come back in. so if i submit two thousand examples and get back dropped_indices [17, 903], i index straight back into my own examples at 17 and 903 and i have the two that failed in front of me, with no correlating of custom ids by hand.  the other option was to hand back the provider's own request ids and let the caller do the mapping, which is more faithful to what we actually receive, but then every caller writes the same twelve lines of mapping code and gets it subtly wrong. That's worth documenting either way, because the ordering guarantee is the entire contract — the numbers mean nothing if anything reorders between the list you handed in and the submit call.
15:08  dario     the ordering caveat is the bit i'd underline, because we already have one path where the list handed in is not the list on disk — the cookbook helper dedupes exact duplicate prompts before submit. so someone reading dropped_indices as offsets into their input file would be off by however many dupes got dropped, and silently, which is the worst version of that.  i think that's still fine, as long as the docstring says handed in rather than input, since the caller does have the post-filter list sitting right there at the point they get the response back. and honestly returning provider ids doesn't fix it, it just moves the same mismatch somewhere less visible.  in any case the numbering is only ever as good as the list you kept a reference to, and that is a much cheaper thing to get right than a mapping table in every caller.
```

#### `g9.r1.say22`

- **chat** · #cookbooks · **konrad** · 2025-04-03 11:31
- carries `g9.r1.failure_behavior`
- must be typed literally: `num_messages`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically even after a skip i can still tell what came back — every datum's metadata block carries num_messages, and the four-message row was sitting right there

As it appears, spread across the exchange:

```
11:31  konrad    the run skipped a chunk of rows this morning and now i cant tell what actually came back for each one
11:32  konrad    do i have to re-run the whole thing to find out, off the top of my head there is nothing in the output
11:35  gideon    no, um, you dont need to re-run. every datum carries its own metadata block and num_messages is in there
11:36  konrad    right but does that survive a skip. thats the part im not sure about
11:38  gideon    ya it does, so basically even after a skip i can still tell what came back — i opened your file and the four message row was sitting right there
11:41  emil      so if i'm reading that right, the count is per datum, not something the run has to report back to us
11:41  konrad    mhm. so the check reads num_messages off the block then, no log parsing. nobody has written that yet
11:43  gideon    exactly. honestly though i lost the morning re-running for a number that was already sitting in the file
```

#### `g9.r2.l12`

- **chat** · #cookbooks · **dario** · 2025-04-11 13:32
- carries `g9.r2.rule`
- must be typed literally: `True`, `windowed`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> windowed came back as nine on a batch that wrote six lines. each datum's encoding reads windowed True fine, the total just shouldnt count rows we dropped.

As it appears, spread across the exchange:

```
13:32  dario     encoding summary from last nights batch says windowed nine, but the file only has six lines in it
13:34  nils      is it the per row flag thats off, or just the total
13:35  dario     per row is fine as far as i can tell. every one of them reads windowed True in its own encoding
13:37  otto      so its only the rollup thats wrong
13:39  nils      the total is counting rows we dropped before the write. those shouldnt be in it
13:40  dario     so count over what actually got written, nothing else
13:42  nils      yes. the per datum True stays exactly as it is, its the sum thats doing the wrong thing
13:45  otto      six is what i got counting the jsonl by hand this morning fwiw
```

#### `g9.r2.l19`

- **mail** · “Re: Weekly update: week of Apr 7” · **dermot** · 2025-04-14 11:41
- to emil@world.local, dario@world.local, gideon@world.local, nikolai@world.local, tomas@world.local
- carries `g9.r2.failure_behavior`
- must be typed literally: `self.last_report`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> One review note on 632: when the batch aborted halfway, self.last_report had already been half updated — it should still read whatever the last good run left.

As it appears, spread across the thread:

```
From: dermot@world.local
Sent: 11:41

Konrad,

I went through 632 properly late last night, and there is only one note I would hold the merge for. Everything else in it I am happy with, so please read this as a single review note rather than a list.

The issue is in encode_batch. As the loop walks the examples it updates the counters on self.last_report in place: kept incremented for each example that survives, the index appended to dropped_indices when one does not, supervised_tokens accumulated as it goes. That is fine as long as the batch runs to completion, because by the time the method returns the attribute describes exactly the run that just finished. The problem is the abort path. When something raises partway through the loop, and the tokenizer raising on a pathological example is the case I actually hit, the exception propagates out of encode_batch and the attribute is left half updated. It then describes neither the run that just died nor the run before it. It is a tally of the first n examples of a batch that never completed, which is the one thing it should never be, because nothing in the object tells the caller that is what they are looking at.

What I want out of it is easy to state: when a batch aborts halfway, self.last_report should still read whatever the last good run left. If a caller encoded a batch successfully at ten past, then tried another one that blew up at half past, the attribute should still be the ten past numbers, untouched. Mechanically that means accumulating into locals and constructing the EncodingReport at the end, then assigning it to the attribute once, on the success path after the loop has finished. If the loop raises, no write ever happens and the previous value survives by construction rather than by us remembering to put it back.

If I had to guess this was never a decision so much as the counters having grown outward from a local variable that was already there, so I am not asking you to defend it. That said, I do think it has to be fixed before this goes in, because a half written report is the sort of thing that gets read into a dashboard and believed.

Regards,
Dermot

--------------------------------------------------------------

From: konrad@world.local
Sent: 12:20

Dermot,

Right, I see it, and I agree it is a bug and not a preference. I had been thinking of the attribute as a running counter and you are describing it as a record of one completed run, and yours is the reading that matches what the name promises. Building the EncodingReport at the end and assigning once is straightforward here, since all five fields are already local except dropped_indices, which I can collect in a list and freeze into the tuple at the same point.

One question before I push anything. What is it supposed to read when nothing good has ever run? A formatter that was constructed and then had its very first batch abort halfway has no last good run behind it, so "whatever the last good run left" does not obviously say anything about that case. Presumably I should leave whatever is there alone, but I am not entirely sure what you expect a caller to find, and I would rather write the test to your answer than to my guess.

Konrad

--------------------------------------------------------------

From: dermot@world.local
Sent: 14:05

On the never-ran case: leave it exactly alone, and there is nothing to invent, because the constructor has already put something there. DataFormatter(max_seq_length=40) seeds the attribute with EncodingReport(kept=0, dropped=0, windowed=0, dropped_indices=(), supervised_tokens=0) before any batch is encoded, so a freshly constructed formatter holds a zeroed report, not None. That is deliberate and I would not change it as part of 632 — callers can read the field and unpack the fields without a null check from the moment they have an object.

So the rule you are implementing is narrower than the sentence I wrote, and it is worth being precise about it since you are writing the test. It is a rule about the abort path only: on an abort, do not write. Whatever the attribute held going into the failed batch is what it holds coming out. For a formatter that had a good run behind it, that is the last good run's report. For one that has never completed a batch, that is the zeroed report the constructor left, which is the correct answer for the same reason — nothing has been counted, so nothing is reported. I am not making a general claim about the initial value beyond that; the constructor decides the initial value, and the abort path simply does not get a vote.

While you are in there, the second write is in encode_batch's early return for the empty input case, and that one should assign a complete report too rather than touching fields. Otherwise it is the same shape of bug waiting for the next person.

Dermot

--------------------------------------------------------------

From: konrad@world.local
Sent: 15:12

That is clear, thank you. Pushed to the branch on 632. The counters are local now, the report is constructed once after the loop and assigned in a single statement, and the empty input path assigns a full zeroed report instead of poking at fields.

The test encodes a batch that succeeds, keeps a copy of the report, then encodes a second batch where the third example makes the tokenizer raise, catches the exception and asserts the attribute is still equal to the copy — kept, dropped, windowed, dropped_indices and supervised_tokens, all five, since the old code would have moved three of them. I did not add a separate case for the freshly constructed formatter because there is already one asserting the zeroed report at construction, and between the two of them the behaviour you described is covered.

One thing I noticed on the way through: the old in place update was the reason the retry helper looked correct in the log, because it read the attribute after the failure and reported the partial count as progress. That is gone now too.

Konrad
```

#### `g9.r1.rev2` · **reversal**

- **chat** · #engineering · **nikolai** · 2025-04-15 14:31
- carries `g9.r1.failure_behavior`
- takes back `g9.r1.h2`
- must be typed literally: `ExampleTooLongError`, `16`, `format_batch`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, we stopped refusing on windowed-at-all, it was droping legit long chats. now it's ExampleTooLongError only under 16 retained prompt tokens, format_batch still skips and carries on.

As it appears, spread across the exchange:

```
14:31  nikolai   whats the refusal rule on long prompts now i lost track
14:34  konrad    not the old one anyway. we had it as refusal is binary, windowed at all means refused, and format_batch just skips that example and carrys on
14:36  nikolai   right thats the one i remember plus an example we never cut still shows window_start 0 in its encoding
14:38  gideon    ya and honestly that was droping legit long chats. anything a bit chatty came back refused
14:41  konrad    so we stopped refusing on windowed-at-all. look, it is ExampleTooLongError now and only under 16 retained prompt tokens
14:43  nikolai   and the skip behaviour
14:46  konrad    skip stays. format_batch skips it and carrys on, same as before. nobody has written it yet, presumably it goes on whatever ticket dermot has open
14:49  gideon    so basically the window_start 0 thing stops meaning anything to us
```

#### `g9.r2.l13`

- **mail** · “Dataset card numbers before we publish the reasoning set” · **emil** · 2025-04-16 09:14
- to dermot@world.local, dario@world.local, gideon@world.local
- carries `g9.r2.rule`
- must be typed literally: `supervised_tokens`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> one more correction while we're on token counts: supervised_tokens in the release notes is inflated, it counted the long examples we dropped from the batch. it shouldn't.

As it appears, spread across the thread:

```
From: emil@world.local
Sent: 09:14

Doing what I hoped was a last pass over the dataset card this morning before we push the reasoning set out, and the numbers are not reconciling for me. The card says 41,880 rows and I can only account for 40,214 in what the batch actually returned, which is roughly the gap I would expect if the card was written against the pre-trim manifest rather than the submitted one.

not entirely sure whether the card was assembled before or after we pulled the long examples, that's really the question. Dermot I believe you put the original counts together — do you remember which manifest you were reading off?

I would rather we be intentional here and fix it now than publish something we quietly correct in a week.

--------------------------------------------------------------

From: dermot@world.local
Sent: 11:38

Emil,

You have it right. The counts in the card came off the pre-trim manifest — i pulled them the evening before we decided to drop anything over the context limit, and then never went back and regenerated them once the trim landed. 40,214 is the number that should be in there.

The per-domain breakdown underneath it has the same problem, since it was derived from the same file. Math and code both come down; the rest are close enough that the rounding hides it, but i would regenerate the whole table rather than patch two rows.

One more correction while we're on token counts: supervised_tokens in the release notes was inflated, it counted the long examples we threw out of the batch. That said, none of this changes the license or provenance sections, so the rest of the card can stand as written.

I can regenerate both tables from the submitted manifest this afternoon if nobody has started already.

Dermot

--------------------------------------------------------------

From: gideon@world.local
Sent: 12:06

Ah ok, that explains it. I was looking at the same gap last week when I was writing the eval harness config and I assumed I had a filter wrong on my side, so I just moved on lol.

Nobody has started on the tables afaik, so go ahead. Do you want me to re-run the dedup stats against the submitted manifest too while you are in there, or were those computed after the trim already?

Gideon

--------------------------------------------------------------

From: dario@world.local
Sent: 13:41

Mhm, this tracks with what I saw in the batch logs — the submitted request count was always the lower one, I just never lined it up against the card.

In any case i'll hold the publish until the regenerated tables are in. No rush on my account, tomorrow morning is fine.

Dario
```

#### `g9.r2.l4`

- **chat** · #engineering · **gideon** · 2025-04-18 15:21
- carries `g9.r2.rule`
- must be typed literally: `==`, `EncodingReport`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> spelling out all five counts in every assert makes these unreadable i'd say make EncodingReport a dataclass with defaults so EncodingReport() is empty and two of them compare with ==

As it appears, spread across the exchange:

```
15:21  gideon    the encoding tests are killing me, every assert spells out all five counts even when four of them are zero. honestly though it's unreadable
15:23  nikolai   yep i'd say make EncodingReport a dataclass with defualts
15:24  gideon    ok but i still have to name all five in the assert, no? um that's the part that's noisy
15:25  dario     i think thats the bit gideon is stuck on, defaults on the constructor dont do anything for the assert side
15:27  nikolai   you stop naming them EncodingReport() is empty on its own so thats what the no-op cases go against and two of them compare with ==
15:28  gideon    ahh ya. one line each then
15:29  dario     mhm. keeping the name as is i assume
15:30  nikolai   yep no reason to rename it
```

#### `g9.r2.l3`

- **chat** · #engineering · **emil** · 2025-04-18 15:32
- carries `g9.r2.rule`
- must be typed literally: `EncodingReport`, `frozen`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> related - a cleanup bumped a counter on an EncodingReport after the batch had finished, so the figure i pasted in the ticket was wrong. frozen=True on it, its finished when format_batch hands it back

As it appears, spread across the exchange:

```
15:32  emil      one more while were on it - a cleanup bumped a counter on an EncodingReport after the batch had finished and the figure i pasted in the ticket was wrong. frozen=True on it, its finished when format_batch hands it back
15:33  nikolai   ya frozen. if it gets loud thats information too, means somebody is writing to one after the fact and we want to know who
```

#### `g9.r1.say25`

- **mail** · “user question: does a local run without the tokenizer extra still report encoding stats” · **dario** · 2025-04-24 13:42
- to gideon@world.local, emil@world.local, dermot@world.local, konrad@world.local, nikolai@world.local, priya@world.local, ilse@world.local
- carries `g9.r1.scope`
- must be typed literally: `window_start`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> honestly the fallback emits the same encoding block as the tokenizer path, window_start and all, and it comes back 0 on any run where we never had to trim

As it appears, spread across the thread:

```
From: dario@world.local
Sent: 13:42

Dermot, Emil,

Some context first, since neither of you was on the thread where this came up and it will read as nonsense otherwise. When the tokenizer is not available on a run — nothing loadable on the box, or we are pointed at a model we cannot open — the counting quietly drops to a character-length estimate instead of failing the run outright. That much I think everyone knows. The part that has been confusing people is what that fallback writes out afterwards, because it is not a reduced or partial record. It emits the same encoding block the real tokenizer path emits, the same keys in the same order, window_start and all, for the straightforward reason that it is the same code doing the writing at the tail of both branches.

The consequence is what I actually want on the record. window_start comes back 0 on any run where we never had to trim, and that is true whichever counter produced the numbers. It is not a placeholder and it is not the fallback declining to fill the field in. It is a measured zero: the window opened at the start of the sequence because nothing needed to be dropped. So reading a 0 there and concluding the estimate path must have been in play is backwards — you get exactly the same 0 out of a clean tokenizer run over a corpus that fits comfortably.

To be honest, keeping the shape identical across the two branches is the best we can do given how much downstream code indexes into that block, so I am not proposing we change the writer. I would only like us to stop treating that zero as evidence of anything.

Dario

--------------------------------------------------------------

From: dermot@world.local
Sent: 14:31

Dario,

Let me restate this to be sure I have the shape of it, because I have been reasoning from the opposite assumption for about a week.

Your position as I read it: both branches terminate in the same writer, so the encoding block is structurally identical between them, and window_start is a real measurement rather than a default, landing on 0 whenever no trimming occurred. Fine, that follows. If I had to guess where it leaves us, though, the block is then identical either way and tells you nothing at all about which counter produced the count, so a record from a run with no tokenizer is simply indistinguishable from a record where the tokenizer ran and the input happened to fit inside the window. Is that the position you are taking, or is there something still in the block that separates the two cases?

I ask because I spent a late night last week reconciling counts across two runs on the assumption that each record announced its own provenance somewhere, and if it does not, I would rather know now than rediscover it.

--------------------------------------------------------------

From: dario@world.local
Sent: 15:14

Your restatement of the window is right and the guess you appended to it is not, and the two are worth pulling apart, because it is the second half that would cost you another night.

Structurally identical, yes — same fields, same order, same code writing them, and window_start carries the same meaning in both branches. But the block is not silent about where the number came from. It carries metadata['encoding']['tokenizer'], and that boolean is False precisely on the runs where we fell back to the character estimate, and True where a real tokenizer produced the count. So the record does say which counter ran. That single key is what separates the two cases, and it is sitting in every record you already have, including the ones from the runs you were reconciling.

What the block genuinely cannot tell you is anything about trimming, and that is where I think the confusion started. A 0 in window_start is a 0 in either branch whenever nothing was dropped, so it discriminates nothing on its own. One field there is a measurement and the other is a declaration; the zero is the measurement, and the declaration is the one you want when the question is which path ran. In any case, nothing needs to change in the writer for that to hold.

Dario
```

#### `g9.r1.rev1` · **reversal**

- **chat** · #engineering · **emil** · 2025-04-24 14:06
- carries `g9.r1.failure_behavior`
- takes back `g9.r1.h1`
- must be typed literally: `window_start`, `to_tinker_datum`, `ExampleTooLongError`, `16`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> dropped the windowing floor — window_start > 0 on its own refuses nothing now, it was binning fine long conversations. to_tinker_datum raises ExampleTooLongError only if the final assistant span starts under 16 tokens past window_start

As it appears, spread across the exchange:

```
14:06  emil      quick one on to_tinker_datum — are we still refusing anything where window_start came back above zero?
14:08  dermot    that was the call yes. any nonzero window_start and it raises ExampleTooLongError. the reasoning being that an example we had to cut isnt really an example anymore, its an artifact
14:09  emil      i remember the framing. it isnt holding up though, the bin i pulled is mostly long support threads that were completely fine
14:13  dario     mhm we dropped that one. window_start > 0 on its own refuses nothing now, honestly it was just binning good long conversations
14:16  dermot    so what trips it instead. if i had to guess something about how much of the tail survives the cut
14:18  dario     close. to_tinker_datum still raises ExampleTooLongError but its keyed on where the final assistant span starts relative to window_start. if theres near nothing of the answer left past the cut, refuse. otherwise its just a long chat and we keep it
14:19  dermot    near nothing being defined how
14:20  dario     if it starts under 16 tokens past window_start
14:23  emil      yup, that reads better. i can stop subtracting that bin out of my totals then, been doing it since febuary
```

#### `g9.r1.l-scope-2`

- **chat** · #code-review · **gideon** · 2025-04-25 14:12
- carries `g9.r1.scope`
- must be typed literally: `Hello`, `Hi`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the cookbook token weight snippet with no tokenizer and 'Hello' / 'Hi there!' comes back every weight 1.0 i'd expect the first few dark since thats the question

As it appears, spread across the exchange:

```
14:12  gideon    ran the cookbook token weight snippet with no tokenizer and the vector came back flat
14:15  dermot    flat as in every weight 1.0? on what pair
14:17  gideon    ya, every one 1.0. 'Hello' then 'Hi there!'
14:21  gideon    i'd expect the first few dark since thats the question, no?
14:26  nikolai   right thats the bug that branch just hands back ones it isnt masking anything today
14:30  dermot    so if i'm following, the fix goes in the no-tokenizer branch itself, not a note on the page
14:33  nikolai   yep in the branch it should come out the same shape the tokenizer path gives you question dark answer weighted nobodys written it yet
14:36  gideon    honestly though i had been reading that flat vector as the tokenizer just being optional
```

#### `g9.r2.l9`

- **chat** · #viewer · **gideon** · 2025-04-28 14:12
- carries `g9.r2.rule`
- must be typed literally: `dropped_indices`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> tbh i chased dropped_indices back to my input file — came back (0, 1) when the rows i binned were 3 and 7. numbered among the ones we skipped.

As it appears, spread across the exchange:

```
14:12  gideon    viewer handed me a dropped_indices tuple this morning, so i went and pulled row 7 out of my input file and tbh it was fine. clean row, nothing wrong with it
14:13  gideon    so what is that number even pointing at
14:19  dario     i think you counted entries. nothing gets written in there for the rows that came through ok
14:23  gideon    ok but the values themselves. um, are they positions in my file or just an ordering
14:27  emil      the input row each skip landed on, i believe. ascending. one drop at row 1 gives you 1, not 0
14:33  gideon    ya, exactly. so basically those numbers only count among the ones we skipped, 7 was never listed at all, i chased it back off the count
14:38  dario     honestly the panel copy is what misled you there, it reads like one slot per row. needs a pass
```

#### `g9.r1.l-scope-1`

- **mail** · “PR 653: formatter still takes tokenizer=None” · **dermot** · 2025-05-06 13:12
- to konrad@world.local, emil@world.local, dario@world.local, gideon@world.local, nikolai@world.local, priya@world.local, ilse@world.local
- carries `g9.r1.scope`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> right, but look — the formatter tests all pass with no tokenizer, becuase that path just hands back all ones, so none of them would notice a masking bug.

As it appears, spread across the thread:

```
From: dermot@world.local
Sent: 13:12

Konrad, Dario,

The supervised run from Sunday night was configured with train_on_assistant_only set to true, and the loss curve does not have the shape any of the earlier assistant-only runs had. It comes down too smoothly and it starts far too low. I pulled a batch straight off the loader this morning and dumped the loss mask alongside the decoded text, and the mask is all ones from the first position to the last: system preamble, user turns, everything. Nothing is being excluded.

The reason I did not start looking in the formatter is that the formatter suite is green and has been green for weeks, and it does contain cases that assert on the mask for multi-turn conversations, including at least one that I wrote myself. So my working assumption was that the flag is being dropped somewhere between the config object and the formatter constructor, or else the collator is rebuilding the mask from scratch after the fact and throwing away what the formatter handed it. If I had to guess I would say the collator, since it is the newer code, but I am not entirely sure and I have not read it closely yet.

Before I spend a late night in the collator, does either of you have a concrete reason to think the formatter itself could be at fault here? I would like to rule it out properly rather than on the strength of a passing test suite.

Dermot

--------------------------------------------------------------

From: konrad@world.local
Sent: 13:58

Dermot,

Right, but look — the formatter is exactly where I would look, and the passing suite is not evidence of anything on this point. The mask construction has two branches. When the formatter is built with a tokenizer, we ask it for the token span of each rendered segment, and we zero out everything that does not fall inside a span belonging to an assistant turn. When the formatter is built without one, we do not have spans, so that branch simply returns a vector of 1.0 with the length of the rendered text and returns it. It never reads train_on_assistant_only. The flag is not dropped on the way in; on that path it is not consulted at all.

The formatter tests all construct the formatter with no tokenizer, because that is what makes them fast and independent of which model we are pointed at. So every one of those mask assertions is running against the branch that hands back all ones, and every one of them passes, and none of them would notice a masking bug even if the assistant-only logic were deleted entirely. Your own case included, presumably. I checked the fixture this morning and there is no tokenizer anywhere in it.

What I would like us to agree is that the no-tokenizer branch has to honour the flag rather than ignore it, and that we do not do this by writing a second masking implementation inside that branch. We already know where each segment begins and ends in the rendered string, because we accumulate the length of the prefix as we build it, so we can produce the assistant spans in character units and pass them to the same masking function the tokenized path calls. That includes the trimming step that clips a long example down to the maximum length, so that a conversation which gets cut is masked the same way whichever branch produced it. One code path, one place where the flag is read.

Off the top of my head that is a small change, but it will make several of those green tests turn red, which is the point of it.

Konrad

--------------------------------------------------------------

From: dario@world.local
Sent: 14:26

That tracks, and it explains the shape of the curve better than the collator theory does, because a mask of all ones is exactly a run that is training on everything and therefore converging on the easy tokens too.

On the question of how to fix it: I had been assuming the choice was either to leave the no-tokenizer branch as its own small per-segment implementation and make it correct on its own terms, or to fold it onto the tokenized path. Having read your description I think folding is the only version that survives contact with us six months from now. Two implementations of the same masking rule is two things to keep in agreement, and honestly the truncation behaviour is where they would drift first — the tokenized path trims after it has spans, and anything written separately would end up trimming before, and then the two would disagree only on long conversations, which is the case nobody inspects by hand. So derive the spans from the prefix lengths, hand them to the existing function, let the trimming happen in the one place it already happens.

The other half of this, which I think matters as much as the fix, is that the fixture cannot stay the only caller. In any case a suite that is structurally incapable of failing on the thing it claims to test is worse than no suite, because it bought us weeks of confidence we had not earned. At minimum the assistant-only cases need to run in both configurations, with a real tokenizer and without, and assert the same mask out of both.

Dario

--------------------------------------------------------------

From: konrad@world.local
Sent: 14:41

Mhm, agreed on both, and the point about truncation being where two implementations would drift is a better argument than the one I gave.

Anyway, the thing I would like written into the commit message is that the all-ones branch was never a decision anyone made. Nobody sat down and decided that a formatter without a tokenizer should train on the user turns. It is the shape the fixture happened to take when the flag did not exist yet, and the suite has been quietly agreeing with it ever since.
```

#### `g9.r1.say23`

- **mail** · “PR 653 before the next cut” · **nikolai** · 2025-05-07 09:04
- to konrad@world.local, emil@world.local
- carries `g9.r1.scope`
- must be typed literally: `[0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> look, on your Hello / Hi there! pair the weights come back one shorter than the tokens - eight of them, [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

As it appears, spread across the thread:

```
From: nikolai@world.local
Sent: 09:04

Konrad,

Any chance you can finish off 653 today? It's been sitting since last week and I'd say its solid enough now, the tokenization path is in there too, so it should be a short pass.

Emil, looping you in only because if this lands before the next cut the cookbook samples change under you again.

Nikolai

--------------------------------------------------------------

From: konrad@world.local
Sent: 11:26

Right, I went through it properly this morning rather than skimming. Most of it is fine — the client itself I have no objection to, and the config handling reads much cleaner than the previous version.

Two things. First, the error path when the upload fails silently swallows the response body, so presumably you get a bare exception with no context. Small, but worth fixing before it lands. Second, and this is the one I want you to confirm: look, on your Hello / Hi there! pair the weights come back one shorter than the tokens - eight of them, [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]. I am not entirely sure if that is intentional (shifted for the next-token prediction, maybe?) or if something is dropping off the end. Off the top of my head I could not tell from the code alone.

If it is intended I will approve today. Anyway the rest is fine from my side.

— Konrad

--------------------------------------------------------------

From: nikolai@world.local
Sent: 13:47

Yep, the error path one is fair, i'll push that in a minute.

The other one I gotta think through. I mean I wrote the pair as a quick sanity check and never counted them side by side, so i can't tell you off the top of my head whether thats deliberate or not.

Give me till tomorrow morning before you approve.

Nikolai

--------------------------------------------------------------

From: emil@world.local
Sent: 15:12

Fine by me either way, I'm not blocking on this — but if the answer turns out to be that something is dropping, honestly I'd rather it get sorted before the samples get regenerated. We rewrote those once already for the response object and I don't want to be doing it a third time in a fortnight.

So, restating so I have it right: nothing lands until Nikolai confirms tomorrow, and if it does land I pick up the cookbook side after. Yup? We need to be intentional here about the ordering, that's all.
```

#### `g9.r1.l-rule-2`

- **mail** · “PR 653 — ran a curated set through the encode path” · **dario** · 2025-05-07 11:04
- to nikolai@world.local, dermot@world.local, emil@world.local, konrad@world.local, gideon@world.local, priya@world.local, ilse@world.local
- carries `g9.r1.rule`
- must be typed literally: `supervised_tokens`, `token_count`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> honestly i pulled one row out and its encoding carries token_count 52 for everything, supervised_tokens 40 — and twelve of that forty are the tail of an answer we chopped the front off.

As it appears, spread across the thread:

```
From: dario@world.local
Sent: 11:04

Nikolai, Dermot,

Before 653 goes any further I spent the first part of this morning in the encoding path rather than the client surface, because the coverage figure we quote in the eval summary has looked too steady to me for several weeks now. Honestly, rather than trust the aggregate I pulled one row out of the encoded set and read the fields on it by hand, and what came back does not support the reading we have been giving that figure.

The row carries token_count 52. So does the row after it, and the one after that — 52 is what every row carries, which tells me the field is being written from the padded length and not from anything the tokenizer actually produced for that example. Against that constant, supervised_tokens on the row is 40. That is where the 40 out of 52 we have been reporting comes from, and since both halves of it are fixed by construction, the number has never measured the thing we describe it as measuring. It is arithmetic on the padding.

The worse half of this is the 40 itself. Twelve of those forty positions are the tail of an answer whose front we chopped off — the example ran long, the head of the answer went, and the remainder stayed in the sequence and stayed marked as supervised. So we are training on the back half of an answer with no beginning attached to it, and counting those twelve positions as legitimate supervision while we do it.

As I see it there are two ways to go: either we correct token_count to report the real tokenized length and leave the mask alone for the moment, or we treat the two as a single change and stop marking a chopped answer as supervised at all. I lean to the second, but I would rather not settle it by myself. In any case, I do not think 653 should land while the summary still describes 40 over 52 as coverage.

Best,
Dario

--------------------------------------------------------------

From: nikolai@world.local
Sent: 11:33

Dario,

On the 52: that is the pad length, and I would say it has been since the encoder was written. Nobody put a real length in that field, so nothing was ever going to vary. Blunt question, because it decides how much of the set is affected — did you find a single row anywhere where token_count is not 52, or is it 52 across the whole file?

The twelve is the part that bothers me more than the constant. A constant that lies in the summary is embarrassing. Supervising a fragment that begins mid-sentence is a training signal we did not intend to give and cannot see in any metric we currently print, since supervised_tokens counts those twelve exactly like the other twenty-eight.

Your second option, for my part. Splitting them means we ship a corrected count that still sits on top of a mask we know is wrong, and then the number looks trustworthy while the data underneath it is not. That is worse than the current state, which at least nobody believes.

Nikolai

--------------------------------------------------------------

From: dermot@world.local
Sent: 12:40

I came to this after the fact and had to read the encoder to follow it, so let me restate what I take the finding to be and you can correct me. The length field is populated after padding, hence 52 everywhere; the supervision mask is applied to the answer span before truncation is applied to the sequence; truncation then removes the head of the answer but the mask that was computed over the full span survives on whatever remains. If I had to guess, that ordering is also why the ratio has been suspiciously flat in every report since we moved to the fixed-length encoder.

That said, I would put one refinement on the remedy. A truncated answer is not merely an unsupervised example — it is an example we should be able to detect and count, otherwise we will lose the signal about how often our sequences are too short for the material. If we drop those twelve positions from supervision and say nothing else, supervised_tokens quietly falls and we will have no way to tell a genuinely short answer from one we mutilated. I would like a per-row marker for the truncated case so that the loss of supervision is visible as such.

On the wider question, I agree with Nikolai that the two changes belong together.

Dermot

--------------------------------------------------------------

From: dario@world.local
Sent: 13:15

Your restatement is right, and the refinement is a genuine improvement on what I proposed, so let me write down what we have settled and treat it as settled.

On Nikolai's question first: it is 52 on every row I looked at, and I looked at rather more than the one after I sent that mail. There is no partial exposure here to scope — the field is uniform across the file, so the correction touches everything and the historical numbers in the summaries are all of them the same fiction.

So: token_count is written from the tokenizer output for the actual example, not from the padded length. An answer whose head was removed by truncation is not supervised — the remaining positions come out of the mask rather than being counted as the twelve currently are — and the row carries a marker saying that is why, so that a shrinking supervised_tokens can be read as truncation rather than as short answers. The eval summary stops quoting a ratio at all until it is quoting one built on real lengths.

I will not pretend this recovers the runs we have already reported on; those were measuring padding against a mask that included mutilated spans, and no correction applied downstream makes them mean anything. Re-encoding and re-running is the best we can do there, and I would rather we say so plainly in the summary than quietly publish a new number next to the old ones as though they were comparable.

Dario
```

#### `g9.r2.l1`

- **mail** · “PR 653 — where does role validation live, and what do the cookbooks import” · **nikolai** · 2025-05-13 09:12
- to dario@world.local, konrad@world.local, emil@world.local
- carries `g9.r2.rule`
- must be typed literally: `ALLOWED_ROLES`, `EncodingReport`, `InvalidRoleSequenceError`, `TokenizerCapabilityError`, `encoding.py`, `finetune`, `finetune/__init__`, `validate_role_sequence`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> the surface is small, honestly: encoding.py is ALLOWED_ROLES, InvalidRoleSequenceError, TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune.

As it appears, spread across the thread:

```
From: nikolai@world.local
Sent: 09:12

Konrad, Dario,

Quick one on PR 653 before I go further.

The chat template stuff needs role validation somewhere. Right now I have a half written check sitting in the client itself, which I dont love since the same rules apply outside the finetuning path. Where is that supposed to live — is there an existing home for it, or am I making one?

Second thing, and this is the one thats actually blocking me: the cookbook notebooks. Do they import from submodules or from the package root? I've seen both in the examples dir and I dont want to write a notebook that goes stale in a week.

Nikolai

--------------------------------------------------------------

From: konrad@world.local
Sent: 09:48

On the second one I have some stake. The cookbooks are already in a bad state after the response object change, we are still going through which samples are affected.

So whatever answer we give here, please can it be one answer. Right now every notebook does its own thing and each time something moves internally we pay for it again.

Not entirely sure about the validation question, that is not mine. Dario?

— Konrad

--------------------------------------------------------------

From: dario@world.local
Sent: 11:26

Dont put it in the client — I think we'd regret that within a month. The finetuning path is not the only caller and honestly it's not even the most likely one long term.

encoding.py as it stands is ALLOWED_ROLES, InvalidRoleSequenceError and TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune. So there's a home already, you shouldnt need to make one.

On konrad's point — agreed, and to be honest that's most of the reason the re-exports exist in the first place. Notebooks reaching into submodules is how we end up rewriting eight of them every time somebody moves a file around. Package root only, and if something you need isnt reachable that way, tell me and i'll widen it rather than you working around it.

In any case, for 653 i'd rather you didnt block on this. The surface is stable enough to write against today.

Dario

--------------------------------------------------------------

From: nikolai@world.local
Sent: 12:03

Right, thats what I needed.

Ripping the check out of the client now, and the notebook will go through the package root.

Nikolai
```

#### `g9.r2.l6`

- **mail** · “stats report branch — need someone to run it before the 0.1.25 cut” · **emil** · 2025-05-13 09:14
- to konrad@world.local, dario@world.local, nikolai@world.local
- carries `g9.r2.rule`
- must be typed literally: `self.last_report`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> stats passed on your branch? self.last_report is set in format_batch but not to_jsonl_lines, after my fireworks run it still had the previous batch numbers. both should set it.

As it appears, spread across the thread:

```
From: emil@world.local
Sent: 09:14

Doing what I hoped was a last pass over the dataset card this morning before we push the reasoning set out, and the numbers are not reconciling for me. The card says 41,880 rows and I can only account for 40,214 in what the batch actually returned, which is roughly the gap I would expect if the card was written against the pre-trim manifest rather than the submitted one.

not entirely sure whether the card was assembled before or after we pulled the long examples, that's really the question. Dermot I believe you put the original counts together — do you remember which manifest you were reading off?

I would rather we be intentional here and fix it now than publish something we quietly correct in a week.

--------------------------------------------------------------

From: konrad@world.local
Sent: 11:52

Right, pulled it and ran two batches through fireworks last night. 400 requests each, nothing exotic in the params.

Good news first. The cost numbers are correct as far as I can check them against the invoice, and the cached counter does the right thing when I re-run the same batch. The printed table is readable, no complaints there.

But — did the stats pass on your branch, self.last_report is set in format_batch but not in to_jsonl_lines, so after my fireworks run it still had the previous batch's numbers. Both should set it. Took me a while to belive it because the first batch looked fine, obviously, there was no previous batch to be stale from.

Also the metadata write happens before the final flush in the batch path, presumably that is intentional? I did not want to move it myself without asking. Off the top of my head that is the only other thing.

Anyway, with those two sorted I think it is fine for 0.1.25.

— Konrad

--------------------------------------------------------------

From: emil@world.local
Sent: 13:40

Yup, that is on me — I wrote the batch path second and clearly stopped paying attention.

Let me think through the metadata ordering before I move it though. I have a vague memory that the flush was deliberate because of the resume case, but I do not trust that memory very much.

Will push both this afternoon. Thank you for actually running it, I would not have caught the stale one locally.

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 16:03

Resume case is real, i hit it in january when the batch job died halfway.

Dont move the write without checking what happens on the second start, or youll get a metadata file that says zero for everything.

Otherwise this looks solid enough to me.

Nikolai
```

#### `g9.r1.l-scope-4`

- **mail** · “sft export — fast tokenizer and manual fallback return different label weights” · **konrad** · 2025-05-13 09:38
- to emil@world.local, dermot@world.local, dario@world.local, gideon@world.local, nikolai@world.local, priya@world.local, ilse@world.local
- carries `g9.r1.scope`
- must be typed literally: `supervised_tokens`, `train_on_assistant_only`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> let me think through that — with train_on_assistant_only off both paths hand back a flat vector of ones, and the span is the whole example rather than the answer, so supervised_tokens is the token count itself. on the Hello / Hi there! pair thats 9, against 8 weight slots — its the span's end minus its start, never the number of weights.

As it appears, spread across the thread:

```
From: konrad@world.local
Sent: 09:38

Emil, Dermot,

I was checking the smoke fixture we use for the loader — the one with the single "Hello" prompt and the "Hi there!" response — and the counter reports a value I cannot reconcile with what the batch actually contains. The example comes back with eight weight entries, one per token, but the record we log alongside it says nine. Both numbers are stable across runs, so this is not a flake.

I checked whether the fixture was configured with assistant-only supervision and it is not, so presumably every token is being counted rather than only the response. That still does not explain the extra one. Maybe I am reading the wrong field, or maybe the counter is computed somewhere other than where I assume it is. Off the top of my head I cannot see where the ninth would come from.

Anyway, before I go further into it: do either of you know what that field is actually counting?

Konrad

--------------------------------------------------------------

From: emil@world.local
Sent: 10:34

Konrad,

Let me think through that, because I have been in the same file this week and the answer is less interesting than it looks, though it is worth writing down properly so nobody rediscovers it in a month.

Start with the configuration. With train_on_assistant_only off, neither branch does any selective work — both paths hand back a flat vector of ones, one entry per token, and the span that gets recorded is the whole example rather than just the answer portion. So the two things you are comparing are not really two views of the same quantity. The weight vector is per-token and comes out of the tokenised sequence directly; the logged figure comes out of the span. In that configuration supervised_tokens is the token count itself, which is exactly why it looks like it ought to agree with the length of the weight vector and mostly does.

On the fixture specifically: for the "Hello" / "Hi there!" pair the recorded value is 9, and there are 8 weight slots. I am not entirely sure the two were ever meant to be read against each other, but people clearly are reading them that way, so we need to be intentional here about which one we treat as the length of the example. The weight vector is the one that matches what the model sees.

Emil

--------------------------------------------------------------

From: dermot@world.local
Sent: 11:22

If I am restating your explanation correctly, the logged figure is never derived from the weights at all — it is arithmetic on the span boundaries, and the weight vector is a separate artefact that happens to line up in most configurations. That would make the discrepancy a property of how the span is measured rather than anything to do with supervision at all, which fits: Konrad's fixture has no assistant-only behaviour in play and the gap is still there.

If I had to guess at the source of the extra one, it is the boundary convention on the span itself rather than an extra token appearing from anywhere. I spent a late night on the truncation path a while back and the spans in that region were half-open in some places and inclusive in others, so a one-token disagreement between a span width and a sequence length is a familiar shape.

That said, I would rather have it stated than guessed at. Emil, is the field computed off the boundaries and nothing else?

Dermot

--------------------------------------------------------------

From: emil@world.local
Sent: 13:24

Dermot, your restatement is right, and I can be exact about it.

The field is the span's end minus its start, never the number of weights. There is no code path in which the weight vector is consulted to produce it, in this configuration or any other. So on the fixture it reports 9 because that is what the boundary subtraction yields for an example whose span covers the entire sequence, and the 8 slots are simply the tokenised length, arriving by a different route. Your reading of it as a boundary convention rather than a stray token is what I believe is happening as well.

Honestly the practical consequence is small but worth holding onto: supervised_tokens answers the question "how wide is the supervised region" and not "how many tokens carry weight", and those questions only give the same answer when the convention happens to line up. Konrad, for what you were doing, the eight is the number you want.

Emil
```

#### `g9.r2.l10`

- **chat** · #pipeline · **gideon** · 2025-05-13 15:12
- carries `g9.r2.rule`
- must be typed literally: `dropped_indices`, `to_jsonl_lines`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yep same on the fireworks pass — to_jsonl_lines numbered dropped_indices against the rows we wrote out, not the list i submitted, so i greped the wrong lines.

As it appears, spread across the exchange:

```
15:12  gideon    pulled the rows dropped_indices pointed me at and none of them are the ones that blew up. so basically i greped the wrong lines
15:15  nikolai   those arent offsets into the list you submitted to_jsonl_lines numbers them against the rows we wrote out
15:17  gideon    wait so anything dropped before that point just shifts everything after it? um then my whole triage doc is off
15:19  nikolai   right off by however many never made it into the file
15:23  dermot    yep same on the fireworks pass. i read them as my submitted list, lined up for the first handful then went sideways
15:26  nikolai   they should be numbered against what went in not what came out thats the list people are actually holding nobody has written it yet though
15:29  gideon    ya ok. redoing the grep off my submitted list, the counts were junk either way
```

#### `g9.r2.l15`

- **mail** · “PR 653 — what goes in the stats dict when the backend doesnt tokenize” · **nikolai** · 2025-05-14 09:41
- to dario@world.local, emil@world.local, gideon@world.local
- carries `g9.r2.rule`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> honestly the fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise — both read zero there.

As it appears, spread across the thread:

```
From: nikolai@world.local
Sent: 09:41

Dario, Emil,

Ran the finetuning client against a real dataset for the first time this morning instead of the toy fixture, and about 40 rows out of 12k dont convert. Three seperate reasons — some are over the length limit, some have a role sequence that alternates wrong (two user turns back to back), and one shard has a tokenizer that just wont load at all.

What I need decided is which layer raises and which layer skips and counts. Right now everything raises, which means one bad row kills a run that was otherwise fine, and thats clearly not what we want. But I dont want to swallow the tokenizer failure either, since thats not a data problem, thats a config problem.

Also, where does the per run report of dropped examples get writen? Is that going in the run dir next to the artifacts or somehwere else?

Not blocking me today, but its blocking me from calling this done.

Nikolai

--------------------------------------------------------------

From: dario@world.local
Sent: 11:02

I think the thing to hold onto here is that the stats object is a report on what the export did, not a description of the data that went through it. So the question isnt really "what is true about these rows", its "what did this code path do to them".

Honestly the Fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise. Both should read zero there — nothing was counted and nothing was dropped, and zero says both of those accurately.

None i'd push back on. It reads like the number went missing rather than the work not happening, and then every caller has to decide what None means to them. And dropping the keys just moves the branch from us to whoever consumes it, which is worse — we'd be handing out a return shape that changes under people.

In any case keep the shape stable across backends. Its not a perfect signal but its the best we can do without making the caller know which backend ran.

Dario

--------------------------------------------------------------

From: gideon@world.local
Sent: 11:48

Ya exactly, stable shape please. I have the cookbook samples printing that dict straight out, and if the keys come and go depending on backend then every sample needs a guard around it.

So basically zero is fine for me. Honestly though, can we get a line in the docstring saying what the fields mean per backend? Tbh someone is going to read a zero and think their rows got dropped or something.

Gideon

--------------------------------------------------------------

From: emil@world.local
Sent: 14:15

Yup, that all sounds right to me, and the docstring point is a fair one — we need to be intentional here about what a zero communicates, because Gideon is right that it can be read two ways by someone who doesnt know which backend they invoked.

nikolai if you land it this week i'll make sure it gets a line in the 0.1.25 notes, i believe the milestone is still open for another couple of weeks so theres room. not entirely sure yet whether it belongs under the finetuning heading or as a behaviour note, i'll figure that out when i draft.
```

#### `g9.r2.l8`

- **wiki comment** · docs/engineering/end-of-run-summary-tables-how-the-formatters-are-wired.md · **gideon** · 2025-05-14 09:42
- carries `g9.r2.scope`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> so basically i constructed a formatter, asked it for its report, got None back, so all my callers have null checks now. fresh one should already hold an empty report tbh.

As it appears, spread across the exchange:

```
09:42  gideon    The lifecycle section here still says the report is populated at construction time, and that is not what actually happens. So basically I constucted a formatter, did nothing else with it at all, asked it for its report and got None back. Not an empty report, None.  Which means every caller I have written this week now carries a null check before it touches anything on the report, and those checks are spreading, because once one call site can see None they all have to assume it. Thats a lot of noise for a field the page describes as always being there.  honestly though the fix i want is not to document the None. A freshly constructed formatter should already hold an empty report tbh, then the null checks all go away and this section is true as written instead of needing a warning box under it.
15:20  dermot    the section was written against the older constructor, which took the report in as an argument, so at that time it really was populated before anyone could observe the object. the field became lazy when config resolution moved out of __init__ and nobody came back here afterwards.  that said the page is worse than merely stale. the example three paragraphs down calls .report.render() on a fresh instance with no guard, so anyone working from it writes the exact bug you hit, and it reads as sanctioned because it is in the docs. if i had to guess, defaulting to an empty report is a two line change in the constructor, and the only thing it can plausibly break is code that currently branches on None being meaningful — your null checks, and the two tests that assert on the lazy behaviour. that is a smaller surface than the prose fix, which would have to explain a distinction that shouldnt exist.
```

#### `g9.r2.l14`

- **wiki comment** · docs/engineering/finetuning-export-what-the-end-of-run-summary-counts.md · **emil** · 2025-05-20 10:42
- carries `g9.r2.rule`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> yup - if a row never made it into the output it shouldnt land in the trim count or the token total either, both summed over kept examples only.

As it appears, spread across the exchange:

```
10:42  emil      the stats section here still reads as though the trim counter and the token total are computed over every row the loader touched, and i dont think thats what we actually want. if a row gets dropped before it reaches the output — length filter, dedupe, whatever else we bolt on later — it never becomes an example that anyone trains on. counting the tokens it would have contributed is just noise in the token total, and counting it as a trim is worse, becaue that trim rate is the one number people look at when they're deciding whether the max length is set too aggresively. So both of those should be summed over kept examples only. i beleive the wording as it stands lets someone implement it either way, which is honestly probably how we ended up with two differnt trim rates quoted for the same run last month. we need to be intentional here rather than leaving it to whoever writes the next loader.
15:17  dermot    agreed, and the ordering is what makes it bite: the trim runs before the filter in the current pass, so a row can be trimmed and then discarded, and that lands in the counter as a trim with no surviving example behind it. incrementing both accumulators at the point where we append to the output list makes the two agree by construction instead of by discipline, which is the version i'd want documented on the page. that said, the worked example further up was written against the old behaviour, so the 4.1% figure quoted there will not reproduce once this is corrected — i've struck it rather than recomputing it from memory, since i no longer have the run it came from.
```

#### `g9.r2.say23`

- **mail** · “PR 653: which layer drops a bad row, and who counts it” · **nikolai** · 2025-05-28 09:41
- to dario@world.local, emil@world.local, gideon@world.local
- carries `g9.r2.scope`
- must be typed literally: `to_tinker_datum`, `ExampleTooLongError`, `format_batch`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> and to_tinker_datum just raises ExampleTooLongError outright — the binning is format_batch's job, honestly a single datum has no batch to be counted into.

As it appears, spread across the thread:

```
From: nikolai@world.local
Sent: 09:41

Dario, Emil,

Ran the finetuning client against a real dataset for the first time this morning instead of the toy fixture, and about 40 rows out of 12k dont convert. Three seperate reasons — some are over the length limit, some have a role sequence that alternates wrong (two user turns back to back), and one shard has a tokenizer that just wont load at all.

What I need decided is which layer raises and which layer skips and counts. Right now everything raises, which means one bad row kills a run that was otherwise fine, and thats clearly not what we want. But I dont want to swallow the tokenizer failure either, since thats not a data problem, thats a config problem.

Also, where does the per run report of dropped examples get writen? Is that going in the run dir next to the artifacts or somehwere else?

Not blocking me today, but its blocking me from calling this done.

Nikolai

--------------------------------------------------------------

From: dario@world.local
Sent: 11:06

I think the split you want is by whether the thing is recoverable at the row level or not, which is roughly what you already said but stated differently.

Length and role sequence are row problems — one bad row says nothing about the next row, so those get counted and skipped. A tokenizer that wont load is not a row problem at all, thats the same failure 12k times in a row, so it should come straight up and stop the run. Honestly if we skip on that we'd just be printing 12000 skip lines and exiting with an empty dataset, which is worse than the traceback.

As for who does the counting: to_tinker_datum just raises ExampleTooLongError straight out — the binning is format_batch's job, a single datum has no batch to be counted into. So the caller catches, increments the right bucket, and moves on. Keep the exception types distinct per reason or the report is useless; dont collapse them into one ConversionError.

On the report — either the run dir next to the artifacts, or nothing at all for now and we just log the counts at the end. I'd lean run dir since you already have the path plumbed through, but to be honest with 40 out of 12k the log line is probably fine for this milestone. Best we can do without knowing if anyone actually reads these files.

Dario

--------------------------------------------------------------

From: emil@world.local
Sent: 13:22

So if I'm reading this right, the rule is: anything that a different row could survive gets counted, anything that poisons the whole run gets raised. That's a clean enough line to write down somewhere.

One thing though — we need to be intentional here about the distinct exception types. I believe we already have a couple of these defined in the tokenizer path from the old work, and if Nikolai adds a parallel set we'll end up with two hierarchies that mean the same thing. Worth a look before you write new ones.

Emil

--------------------------------------------------------------

From: gideon@world.local
Sent: 13:58

Ya, the old ones are there, I think under the utils module? I dunno if they are actually used anywhere anymore tbh.

So basically check first, and if nothing imports them just delete and write fresh — that is cleaner than trying to reuse something nobody remembers.

Gideon
```

#### `g9.r2.h-role-row` · **herring**

- **mail** · “Re: PR 653: which layer drops a bad row, and who counts it” · **dario** · 2025-05-28 11:06
- to nikolai@world.local, emil@world.local, gideon@world.local
- carries nothing — it is here to be wrong
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

> Length and role sequence are row problems — one bad row says nothing about the next row, so those get counted and skipped


#### `g9.r1.l-fw-2`

- **wiki comment** · docs/engineering/viewer-dataset-download-export-format-notes-pr-652.md · **dario** · 2025-06-03 11:26
- carries `g9.r1.exclusions_or_crossover`
- must be typed literally: `héllo wörld`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact.

As it appears, spread across the exchange:

```
11:26  dario     the paragraph under the oversized rows heading still reads as though we shorten things to make them fit, and i think that wants correcting before anyone builds on it. nothing gets shortened anywhere in this path. a row that comes in over the limit is dropped entire, and a row that comes in under it comes back exactly as it was written - 'héllo wörld' goes in and 'héllo wörld' comes out, same bytes, same first character, no quiet reencoding on the way through.  honestly i'd sooner drop an example than ship a conversation with its opening sawn off. a half conversation isn't a smaller version of the same conversation, it's a different one, and it reads as if the speaker walked in mid sentence - nothing downstream can tell the differnce between that and a genuinely odd example, which is exactly the failure you don't want in a training set. a dropped row at least shows up in the counts where somebody can see it.  in any case that's the behaviour as it actually stands today, and i'd rather the page said so plainly than leave the word truncate sitting there as though it were an option still on the table.
15:53  emil      came here for the loader notes and read this on the way past. the guess i'd make from your comment is that the drop is all or nothing per row - there is no middle state where we keep the first few turns and mark the thing partial. if thats right then the dropped count is the only number anyone has to reason about, which is a good deal easier to explain to someone new than any shortening rule i've ever written down.  changed the wording above from shortened to dropped on the strength of that, and left the accented example sitting right next to it, since the round trip of an under-budget row is the part people assume is where things get lost.
```

#### `g9.r1.l-rule-1`

- **wiki comment** · docs/engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md · **gideon** · 2025-06-10 09:41
- carries `g9.r1.rule`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> so basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted.

As it appears, spread across the exchange:

```
09:41  gideon    so basically the truncation part of this page still reads like the only thing that happens is the text starts later, and i dont think that covers what i am looking at. the checkpoint from last night starts its answers mid-sentence — you ask it anything and the first token out is the middle of a clause, there is no opening at all, it just continues something that was never said.  so i went and pulled rows from the shard to see where it learned that. every row i pulled had the question cut off, the front of the exchange is simply not in the row, and in most of them the reply itself also begins partway in, but the reply was still weighted. so the model is being taught to produce a continuation with nothing in front of it, which is exactly the behaviour i am seeing.  honestly though i am not sure what i am holding. tbh the file i pulled from was one sitting in my scratch dir since a while, i did not rebuild it. what is the rule supposed to be when the opening tokens of a turn land outside the window — does the rest of that turn keep its weight or not?
11:26  dermot    the rows are real, the shard is not current. that file is from before the masking change in early may, and the page section you are reading was written after it, which is why they do not line up.  the rule as it stands: if a turn's opening tokens fall outside the front edge of the window, that turn is not supervised at all. not the surviving tail, not the last sentence of it, nothing — the entire remainder of that turn carries no weight. a head-removed answer is treated as not an answer. so a row where the reply begins partway in and still shows 1.0 on its tail cannot come out of the builder as it exists now. it could only come out of a build older than may, which is what you have.  that said, your checkpoint is still a real data problem, just a stale one - it trained on the old shard, so the mid-sentence starts are exactly what you would expect from it. if i had to guess the checkpoint was cut from a snapshot that never got rebuilt after the mask change, rather than anything wrong in the current path.
15:12  gideon    ya, rebuilt it and it lines up. the row i had been staring at, the answer that used to run 48 to 59 and lost its first three tokens to the cut, now contributes nothing — supervised count on that row is 9 where before it was 17, and the first 1.0 anywhere in the row is at index 30, which is the next answer that is fully inside. so the eight surviving tokens are carrying no weight at all, exactly as described above.  so the checkpoint is the throwaway here, not the masking code. adding this as a comment rather than editing the section, since the section is already correct — it was my shard that was a month behind it.
```

#### `g9.r1.fix28`

- **chat** · #engineering · **nikolai** · 2025-06-11 10:07
- carries `g9.r1.scope`
- must be typed literally: `Hello`, `Hi there!`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, I measured the Hello / Hi there! case by hand - 15 charcters up to where the assistant header starts, 39 with that whole turn on the end.

As it appears, spread across the exchange:

```
10:07  nikolai   for the finetuning masking are you pulling the assistant spans out of the tokenizer or computing them yourself
10:09  konrad    computing them. the tokenizer offsets did not line up with what the chat template actually renders so i went back to charcter offsets on the rendered string
10:10  konrad    look, i measured the Hello / Hi there! text by hand - 15 characters up to where the assistant header starts, 39 with that whole turn on the end. right now the test just asserts those two numbers
10:14  emil      let me think through that... the thing that worries me a little is the template can shift under you on a tokenizer bump and then your 15 and 39 are quietly wrong, nothing fails loudly. not entirely sure what the catch for that looks like honestly
10:16  konrad    mhm, presumably we derive them from the template in the test instead of hardcoding. anyway that is after i get the masking itself correct
10:18  nikolai   solid enough for now i'd say gotta think through that one properly when the other template lands
```

#### `g9.r2.say24`

- **wiki comment** · docs/engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md · **dario** · 2025-06-11 11:24
- carries `g9.r2.failure_behavior`
- must be typed literally: `apply_chat_template`, `TokenizerCapabilityError`, `format_batch`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> re gideon's tokenizer - no apply_chat_template on it, so format_batch raises TokenizerCapabilityError right there, pass stops, nothing gets binned as a drop

As it appears, spread across the exchange:

```
11:24  dario     the paragraph above about the drop tally holds only for tokenizers that get far enough to produce a drop, and i think thats worth spelling out because gideon's doesnt. there is no apply_chat_template on it at all, so format_batch raises TokenizerCapabilityError on the first message it tries to render and the pass stops right there. nothing from that run gets binned as a drop. not zero drops - no drop accountign happened, the code never reached the part of the loop that does the binning.  so if you came to this page because a run showed an empty drop column and you were trying to work out what got thrown away, honestly the answer may be nothing was, and the numbers on this page only describe tokenizers that have the method. in any case the distinction the page is missing is between a pass that dropped nothing and a pass that never ran.
15:52  dermot    yeah, and the reason it reads as zero rather than absent is that the summary is rendered off the same counter dict regardless of whether the pass completed, so an untouched counter and a completed pass with no drops are indistinguishable downstream of that.  that said, i have reworded the second paragraph above to say "tokenizers exposing apply_chat_template" instead of "all configured tokenizers", and put the raise case in its own sentence underneath, so the page no longer claims coverage it does not have.
```

#### `g9.r1.say21`

- **wiki comment** · docs/engineering/what-the-finetuning-encoder-emits-per-datum-and-how-it-behaves-at-the-length-cap.md · **dermot** · 2025-06-12 10:42
- carries `g9.r1.failure_behavior`
- must be typed literally: `max_seq_length`, `max_seq_length=40`, `window_start`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> yeah ok — at max_seq_length=40 the four-message near-miss does come back a datum: encoding reads window_start 51, and the weights come back 39 long, one short of the max_seq_length window we keep.

As it appears, spread across the exchange:

```
10:42  dermot    the line in this section about near-misses being dropped once the window gets short is not right, or at least it is not right for the case i went and checked late last night. yeah ok — at max_seq_length=40 the four-message near-miss does come back a datum. it is not dropped, it comes back short. encoding reads window_start 51 for it, and the weights come back 39 long, one short of the max_seq_length window we keep.  so what is actually on disk is a real example carrying a 39-length weight vector against a 40-wide window, which is a different failure from the one the page describes. if i had to guess this section was written from a narrower window where the same example genuinely does fall out, and the wording got carried up. that said, anyone reading here to decide whether a near-miss survives at 40 will take the wrong answer away. the discrepancy is a length, not a missing row.
14:05  konrad    Right, 39 is what I get as well. Off the top of my head the two counts are not measuring the same thing — the window is counted from window_start inclusive and the weights are written for the transitions, so a 40-wide window gives you 39 of them. Nothing truncated it, that is just the arithmetic.  Anyway I agree the sentence should say short and not dropped. But the more useful thing to put next to it is the one line of subtraction, because a reader who sees 39 where they expected max_seq_length will assume something ate a token, and there is no missing token to go looking for.
```

#### `g9.r1.say27`

- **wiki comment** · docs/engineering/trimming-over-length-rows-for-finetuning-pr-653.md · **nikolai** · 2025-06-12 11:24
- carries `g9.r1.rule`
- must be typed literally: `window_start`, `token_count`, `max_seq_length`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> yep checked the fallback path too window_start is token_count minus max_seq_length either way floored at 0 when it fits so that 129 token row at cap 40 reads 89

As it appears, spread across the exchange:

```
11:24  nikolai   the note under this section still says the offset math is only documented for the main path and to treat the fallback as unknown but i went and read the fallback too and its the same arithmetic  window_start is token_count minus max_seq_length in both branches and its floored at 0 so a row that fits under the cap starts at 0 rather than going negative  worked it agaisnt a real row to be sure a 129 token row with max_seq_length at 40 reads 89 either way which is exactly the subtracion and nothing else so i'd say the caveat can come out
16:47  dermot    the fallback branch went in late night alongside the batching change, which is most likely why it never got written up here in the first place.  reading your numbers back to check i have it: the floor is only doing work for the short rows, anything at or above the cap just takes the difference, so 129 against a cap of 40 lands on 89 no matter which branch produced it. that matches what i get.  i've struck the caveat and rewritten the paragraph so it covers both branches, with the 129/40 case in as the worked example.
```

#### `g9.r1.l-fw-3`

- **mail** · “Re: Week of Jun 9 recap: bulk inference fix” · **nikolai** · 2025-06-16 14:20
- to dario@world.local, emil@world.local, konrad@world.local, nolan@world.local
- carries `g9.r1.exclusions_or_crossover`
- must be typed literally: `EncodingError`, `ExampleTooLongError`, `FIREWORKS_BYTES_PER_TOKEN`, `False`, `encoding.py`, `tokenizer`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> on 653 whats in encoding.py so far the role set FIREWORKS_BYTES_PER_TOKEN still 3 ExampleTooLongError off EncodingError and the encoding blocks tokenizer flag False when we ran without one

As it appears, spread across the thread:

```
From: nikolai@world.local
Sent: 14:20

Dermot,

Nobody has been willing to say whether 653 needs to land for 0.1.26, and I think that is partly because nobody outside the PR knows what is in it. I merged main in this morning and worked through the conflicts far enough to see the shape of the file, so rather than keep answering this one comment at a time in review, here is the whole inventory. Read it as a description of what exists today, not as a proposal for anything.

encoding.py is four things and nothing else. The first is the role set, the fixed set of roles a message is allowed to declare, which is what the rest of the validation in the file hangs off. The second is FIREWORKS_BYTES_PER_TOKEN, which is still 3. It was 3 before the merge and it is 3 after; I did not touch it and nobody has given me a reason to. The third is the error hierarchy, which is small: ExampleTooLongError comes off EncodingError, so a caller that catches the base type gets the too-long case along with everything else, whether or not it wanted it. The fourth is the encoding blocks themselves.

The blocks are the part I would want a second pair of eyes on. They carry a tokenizer flag, and when we ran the thing without a tokenizer configured that flag came through as False rather than the run failing outright. Off the top of my head that is defensible, since the alternative is refusing to encode at all in a setup that has no tokenizer to hand, but it does mean the flag is describing what was available at the time rather than anything the caller asked for. I'd say the rest of the file is solid enough. That one I have gotta think through.

Nikolai

--------------------------------------------------------------

From: dermot@world.local
Sent: 15:02

Nikolai,

Thank you for writing it out; this is the first description of 653 I have been able to read without opening the diff.

Let me make sure I have the last point right, because I think it is the only thing in your list that is a decision rather than an inventory item. Your reading is that the tokenizer flag on the encoding blocks is derived rather than supplied, so the run we did without a tokenizer produced False on that flag and carried on, instead of raising. If that is right then the flag is a record of the environment rather than an instruction, and the two are easy to confuse later when somebody reads False and concludes we chose it.

On the error hierarchy, I would rather have it the way you describe it than the alternative. ExampleTooLongError deriving from EncodingError is the arrangement I would expect, and if a caller is catching the base and swallowing a length failure, that is the caller's problem and not the file's. That said, it is worth someone knowing it, since a length failure is the one case where the caller can usually do something about the input.

FIREWORKS_BYTES_PER_TOKEN at 3 matches what I remembered, and I am glad the merge did not quietly move it.

Dermot

--------------------------------------------------------------

From: nikolai@world.local
Sent: 15:26

Right on both counts. The flag is derived, not passed in, and False is what came back on the run without a tokenizer. Nothing decided it; it is a report of what was there.

And yep, the constant survived the merge intact. That is the point I was mostly trying to make by listing all four together: the role set, FIREWORKS_BYTES_PER_TOKEN at 3, ExampleTooLongError off EncodingError, and the encoding blocks with that flag. None of it is new behaviour introduced by 653. What is in the PR is conflicts and the file above, which means the question of whether it lands is a scheduling question and not a design one, and I no longer think it needs the review it has been waiting on.

Nikolai
```

#### `g9.r2.l17`

- **wiki comment** · docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md · **dario** · 2025-06-17 09:47
- carries `g9.r2.failure_behavior`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> honestly if the role sequence is bad thats my data being broken, not a row to quietly skip - only the over-long ones should get binned and counted

As it appears, spread across the exchange:

```
09:47  dario     the malformed input section still has both cases sitting under the same bullet ("rows that fail validation are skipped") and i think thats wrong, or at least its wrong for half of it.  if a conversation comes through with a role sequence that doesnt make sense - two user turns back to back, assistant leading, whatever the shape is - honestly that is my data being broken somewhere upstream, its not a row we should be quietly skipping. skipping it means nobody finds out until the counts dont add up three weeks later, if they even notice then. i would much rather it just fails loudly at that point so whoever built the file gets told what they built.  the over-long ones are a different animal and i have no argument with dropping those, they genuinely cant be used. but they should be binned and counted, so there is an actual number somewhere to look at instead of infering it from the fact that the output file came out shorter than the input. in any case the two things shouldnt be described as one behaviour on this page, they are not the same behaviour.
15:12  dermot    for whoever reads this later - the sequence check and the length check are the same guard in the loader, which is presumably how they came to be one bullet here in the first place. separating them the way described above means the sequence case raises and the length case increments, so they cannot stay in one branch, thats a real change and not just a wording fix on the page.  that said, the counter as it exists today covers both together, so the dropped figure in the table above is not measuring what its caption claims. i went back through last month's run and a bit over two thirds of what it counted were sequence failures rather than length.
```

#### `g9.r2.rev3` · **reversal**

- **wiki comment** · docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md · **dario** · 2025-06-17 09:47
- carries `g9.r2.failure_behavior`
- takes back `g9.r2.h-role-row`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

> and yes this is me contradicting myself - the split i gave on the 653 thread back in may, length and role sequence both being row problems, that half of it was wrong and im dropping it. only the over-long ones are row problems.


#### `g9.r1.l-scope-3`

- **wiki comment** · docs/engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md · **dermot** · 2025-06-17 10:42
- carries `g9.r1.scope`
- must be typed literally: `<|role|>`, `len // 4`, `len(chat_text) // 4`, `messages[:i+1]`, `messages[:i]`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> on the no-tokenizer path leave the `<|role|>` text and `len(chat_text) // 4` as they are; a span's ends are that count over messages[:i], then over messages[:i+1].

As it appears, spread across the exchange:

```
10:42  dermot    the fallback section still reads as though the `<|role|>` markers and the character estimate are placeholders sitting there until someone wires in a real tokenizer. that got decided the other way and the page should stop implying otherwise. on the no-tokenizer path the rendered text keeps the `<|role|>` form as it is, and the length stays `len(chat_text) // 4`. neither is getting swapped for a tokenizer call later.  the part that actually caused the confusion is the span arithmetic, which as far as i can tell is not written down anywhere on this page. a span's two ends are the same `len // 4` count applied twice, over prefixes of the message list: the start is that count taken over `messages[:i]`, the end is that count taken over `messages[:i+1]`. so both offsets come out of one estimator and the width of the span is just whatever the i-th message adds to the rendered text.  if i had to guess, that is why the numbers looked internally consistent to me but never lined up with anything a tokenizer would have produced. they were not meant to. that said, the thing worth stating explicitly for whoever reads this section next is that the estimate does not need to be accurate, it needs to be the same function at both ends. compute the two ends by different routes and the spans stop nesting, and everything downstream that assumes containment goes quietly wrong.
16:05  konrad    The case i would add to the section is the empty one, becuase it looks like a bug the first time you hit it. For the first message the slice `messages[:i]` is empty, so the prefix renders to nothing and the start comes out 0. That is a real start value, not a missing one. I had a guard in my own check treating 0 as unset, and that is why my offsets sat one message off for two weeks.  Also worth putting in the text, now that `<|role|>` stays literal: the count includes those markers, so a span start lands a few characters ahead of where the visible message content begins. That is fine when you compare against the rendered string. Not fine when you compare against the raw message, which off the top of my head is exactly what i was doing.
```

#### `g9.r1.l-rule-4`

- **wiki comment** · docs/engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md · **nils** · 2025-06-17 11:20
- carries `g9.r1.rule`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> let me think through that, what settles whether a turn is in or out is whether the opening token of its answer survived the cut, the tail end of it is in there either way

As it appears, spread across the exchange:

```
11:20  nils      The checklist above doesn't cover the boundary one, and the span section reads as though every assistant span sits whole inside what we keep. On a windowed row the first one often doesn't — rather than rewrite someone else's section I will leave the reasoning here.  let me think through that properly. the windowing takes material off the front, never off the back. So for any turn that straddles the cut, the tail end of its answer is inside the window either way — that end of it is simply never the thing in question, and no amount of looking at it will tell you anything. What actually varies across the boundary is one thing only: whether the opening token of that turn's answer survived the cut. if it did, the turn is in. if it didn't, the turn is out.  So there is no third state to describe. "partially present" reads as if there were a middle case that needs its own handling, and that is what sends people off writing coverage ratios for turns that don't need them. that's worth documenting plainly, because the rule fits in a sentence.
15:12  dermot    mhm. so if i'm restating that correctly, the predicate is on the start offset of the answer and nothing ever reads the end offset, because the end offset is trivially inside the window by construction. that matches what the masking path does — it compares the answer's first token position against the cut and returns a boolean, there's no partial branch in there at all.  that said, the fixtures further down are already consistent with what nils wrote, they just aren't labelled that way. so the examples are fine and it's only the sentence above them that's wrong.
```

#### `g9.r2.l2`

- **wiki comment** · docs/engineering/per-example-stats-from-the-windowed-export-review-notes-653-follow-on.md · **konrad** · 2025-06-24 10:41
- carries `g9.r2.rule`
- must be typed literally: `dropped`, `dropped_indices`, `kept`, `skipped`, `supervised_tokens`, `windowed`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> nit: docstring says skipped but the attribute is dropped. also the field order is kept, dropped, windowed, dropped_indices, supervised_tokens, your exmaple builds it the other way round.

As it appears, spread across the exchange:

```
10:41  konrad    Two things about the section above, both small but they will bite someone.  The docstring quoted on this page says the count of skipped rows, but there is no attribute called skipped anywhere in the class. It is dropped. Presumably the wording is older than the rename, anyway a reader who greps for skipped after reading this finds nothing, and there is also dropped_indices sitting right next to it which makes the wrong name more confusing not less.  The other one is the field order. In the dataclass it is kept, dropped, windowed, dropped_indices, supervised_tokens. The exmaple on this page builds it the other way round, reversed. So if somebody copies it as positional arguments, dropped_indices lands where dropped is expected and that one at least blows up, but kept and supervised_tokens swap silently, both are ints. I am not entirely sure which of the two is the intended order, look, whichever it is the page should say the same thing in both places.
14:26  dermot    yeah, skipped is the pre-rename wording. the field held the filtered rows themselves at one point and was renamed to dropped when it became a count, the docstring just never followed. i've corrected it in place above so this comment is now describing text that isn't there anymore.  the reversal in the example was my transcription and not some other convention, there is only one order and it is the dataclass one, kept, dropped, windowed, dropped_indices, supervised_tokens. rather than flip the example back i rewrote it to construct with keywords, since the order stops mattering to anyone copying off the page that way. your point about kept and supervised_tokens is the reason i went that direction — a positional copy that fails on dropped_indices is a nuisance, one that quietly reports the wrong token count is not.
```

#### `g9.r2.l5`

- **wiki comment** · docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md · **dermot** · 2025-06-26 09:14
- carries `g9.r2.rule`
- must be typed literally: `format_batch`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> yeah — counted binned rows by hand off the upload log again, so the summary comes off the formatter afterwards. that said, format_batch still hands back a plain list.

As it appears, spread across the exchange:

```
09:14  dermot    yeah — the status section reads as if the per-batch counts in it fall out of the pipeline. they don't, or at least they didn't this week. i counted the binned rows by hand off the upload log again, late night before the sync, same as i did for the last two.  the reason is worth writing down somewhere less transient than this page: format_batch still hands back a plain list. no counts on it, no bin labels, nothing you could summarise from. so the summary has to come off the formatter afterwards, out of the log, which is where the hand counting comes in.  not entirely sure that needs fixing before 0.1.26 since it isn't blocking anything. but whoever reads "no blockers" here later should read it as "no blockers, and the numbers underneath it have a person in the loop".
11:02  konrad    This matches what I hit last week. I went looking for the counts in what format_batch returns, so I could put them in the release note, found nothing, and assumed I was calling it wrong. Apparently I was not calling it wrong.  Anyway, presumably the local offline inference line further down has the same caveat, since as far as I know those numbers are produced the same way, but I have not checked that myself so I am not going to claim it here. For the release note I have already reworded it to say the counts are manual, so at least that text is not claiming to be measured when it is not.
```

#### `g9.r1.say24`

- **wiki comment** · docs/engineering/local-offline-inference-what-the-encode-step-returns-when-no-tokenizer-is-loaded.md · **gideon** · 2025-06-26 10:42
- carries `g9.r1.scope`
- must be typed literally: `Hello`, `chat_text`, `model_input`, `token_count`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> so basically on the mock path the encoding reads token_count 9 for the Hello pair, the whole chat_text in one go, ids 0 through 8, model_input the first eight.

As it appears, spread across the exchange:

```
10:42  gideon    the section above still says the mock tokenizer gets called once per message, and that is not what happens when i actually run it. on the mock path the encode gets the whole chat_text in one go, single call, the entire rendered string, not the user turn and then the assistant turn seperately. and for the Hello pair what comes back is token_count 9, with ids 0 through 8, so the ids are just a range as long as the count, nothing to do with the actual text. model_input is then the first eight of those, 0 through 7, the last id is not in it. honestly though i lost an hour to this becuase i assumed the 9 vs 8 was my own slicing being off by one somewhere, and it is not, that is the shape it is supposed to have. tbh the table in that section should just print those four things directly, otherwise everyone reading it spends the same hour.
15:58  emil      Yup, that lines up with what i see. one thing worth putting next to it for whoever reads the page later: because the ids come out as 0 through 8 in order, they carry no information about the text at all. you can't use them to check the pair got rendered in the right order, since 0..8 comes back the same whichever way round the two turns go. on the mock path the count and the length of model_input are the only parts of that output that mean anything. i had been treating a clean sequential range as a sign the encode did the right thing, and it isn't, it's only a sign it ran.
```

#### `g9.r2.fix25`

- **chat** · #pipeline · **gideon** · 2025-07-10 13:02
- carries `g9.r2.rule`
- must be typed literally: `format_batch`, `to_jsonl_lines`, `dropped_indices`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Reran both over the same input list now that the renumber landed — format_batch and to_jsonl_lines come back with identcial dropped_indices. anyway, no more guessing which one I'm reading.

As it appears, spread across the exchange:

```
13:02  gideon    the drop list coming out of format_batch — is that the same thing to_jsonl_lines reports back, or not? i had both open yesterday and they did not agree
13:05  dario     yesterday, probably not. the renumber only went in after that
13:07  gideon    ok so basically nothing from before is worth comparing. did anyone push the same thing through both since
13:10  konrad    yes. i took the same input list and reran both, now that the renumber landed
13:11  gideon    and?
13:13  konrad    dropped_indices comes back identcial. same out of format_batch, same out of to_jsonl_lines
13:14  konrad    anyway, no more guessing which one i am reading
13:17  gideon    ya thats the bit that kept biting me, i was reading whichever one came up first and assuming
```

