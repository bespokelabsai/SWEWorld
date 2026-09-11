# The tree

## g9.r1

### g9.r1.sc-rule — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*The leap nobody states:* weights built over the whole sequence and then sliced along with the tokens will keep the tail of a clipped turn unless something explicitly drops that turn.

- **gideon** (2025-06-10, page:engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md): so basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted.
- **dario** (2025-05-07, thread:new|g9.r1.l-rule-2): honestly i pulled one row out and its encoding carries token_count 52 for everything, supervised_tokens 40 — and twelve of that forty are the tail of an answer we chopped the front off.
- **emil** (2025-03-14, #engineering): honestly i don't think part credit on a turn works - either the whole answer sits inside what we keep or it counts for nothing at all.
- **nils** (2025-06-10, page:engineering/reading-a-capped-executor-log-how-to-count-turns-in-it.md): let me think through that, what settles whether a turn is in or out is whether the opening token of its answer survived the cut, the tail end of it is in there either way

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
- **emil** (2025-04-17, thread:new|g9.r2.l3): yeah, a cleanup bumped a counter on last night's report after the run finished, so the figure i pasted in the ticket was wrong. agreed, reports are frozen once built.
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

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled then: format_batch hands back (data, report), datums first and the EncodingReport second, callers unpack it. nothing else carries the counts.
- **konrad** (2025-01-22): Right, made a start on 362 — signature in review is `format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]`, so the report rides out with the data.

