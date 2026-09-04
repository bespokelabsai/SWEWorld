# Clues for g9 — One encoding policy for chat examples

53 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Give `finetune` a single typed encoding policy for chat training examples, shared by the tinker formatter and the Fireworks formatter.

### New module `src/bespokelabs/curator/finetune/encoding.py`

- `ALLOWED_ROLES: frozenset = frozenset({"system", "user", "assistant"})`.
- `class EncodingError(ValueError)` — base class for every error raised by the encoding policy.
- `class InvalidRoleSequenceError(EncodingError)` with `__init__(self, *, role_sequence: List[str], position: int, reason: str) -> None`; attributes `role_sequence`, `position`, `reason`, all set before `super().__init__()`; `str(e) == f"invalid role sequence at position {position} ({reason}): {role_sequence}"`.
- `class TokenizerCapabilityError(EncodingError)` with `__init__(self, *, missing_method: str) -> None`; attribute `missing_method`; `str(e) == f"tokenizer is missing required method {missing_method!r}"`.
- `def validate_role_sequence(messages: Sequence[Any]) -> None` — accepts a sequence of `ChatMessage`-like objects (`.role`) or of dicts (`"role"` key); returns `None` on success.
- Python 3.10 (`^3.10`, checkout is 3.10.12): use `Optional[...]` / `Tuple[...]` from `typing`, not `X | Y`. Stdlib + existing deps only; `tinker` is not installed and must not be required. Pure and deterministic.

### `validate_role_sequence` rules

Checked in this order; the first violation raises and nothing later is reported.

- empty sequence → `reason="empty"`, `position=0`.
- a role not in `ALLOWED_ROLES` → `reason="unknown_role"`, `position` = index of the first such message.
- a `"system"` message at any index other than `0` → `reason="misplaced_system"`, `position` = index of that message.
- after the optional leading system message the roles must alternate `user, assistant, user, assistant, ...` → `reason="non_alternating"`, `position` = index of the first message whose role is not the expected one.
- the last message must be `"assistant"` → `reason="unterminated"`, `position = len(messages) - 1`.

Examples: `[]` → `("empty", 0)`; `[user, tool, assistant]` → `("unknown_role", 1)`; `[user, system, assistant]` → `("misplaced_system", 1)`; `[system, user, user, assistant]` → `("non_alternating", 2)`; `[system, user, assistant, user]` → `("unterminated", 3)`.

### `DataFormatter` (`data_formatter.py`)

- `__init__(self, max_seq_length: int = 2048, train_on_assistant_only: bool = True) -> None` keeps `self.max_seq_length` and `self.train_on_assistant_only`.
- Replace `_compute_weights` with `_supervised_spans(self, messages: List[ChatMessage], tokenizer: Optional[Any]) -> List[Tuple[int, int]]`: the half-open `[start, end)` token indices of every assistant turn, in message order, over the **untruncated** token sequence.
- `to_tinker_datum(self, example: TrainingExample, tokenizer: Optional[Any] = None) -> Any` calls `validate_role_sequence(example.messages)` first thing.
- When `tokenizer is not None`, `to_tinker_datum` requires `callable(getattr(tokenizer, "apply_chat_template", None))` and otherwise raises `TokenizerCapabilityError(missing_method="apply_chat_template")` — regardless of `train_on_assistant_only`.
- Delete the `try/except Exception: weights = [1.0] * len(tokens)` fallback at `data_formatter.py:102-104`. If `apply_chat_template` or `encode` raises while spans are computed, that exception propagates unchanged; there is no all-ones fallback on the tokenizer path.
- With a tokenizer: encode the chat text with exactly one call, `tokenizer.encode(chat_text, add_special_tokens=False)` — no `max_length`, no `truncation` — then window in the formatter: `window_start = max(0, len(tokens) - self.max_seq_length)`, `windowed_tokens = tokens[window_start:]`. Weights are built over the untruncated sequence and sliced with the identical `[window_start:]`, so the end of the conversation survives and the oldest context is what is lost.
- `train_on_assistant_only=False` means weights are all `1.0`.
- Reuse unchanged: `format_chat_messages`, `format_example`, the prefix-tokenization boundary trick (`apply_chat_template(pre, add_generation_prompt=True)` for the start index, `apply_chat_template(cumulative, add_generation_prompt=False)` for the end index), the causal shift and the `tinker.Datum` construction (`data_formatter.py:134-148`, out of scope).
- `format_batch(self, examples: List[TrainingExample], tokenizer: Optional[Any] = None) -> List[Any]` processes examples in input order; its return type stays a list.

### Dict envelope returned by `to_tinker_datum`

`tinker.Datum` is returned when `TINKER_AVAILABLE` and `tokenizer is not None`; otherwise (the only shape reachable in this checkout) exactly:

```python
{
    "model_input":  List[int],                    # windowed_tokens[:-1]
    "loss_fn_inputs": {
        "target_tokens": List[int],               # windowed_tokens[1:]
        "weights":       List[float],             # windowed_weights[1:], 0.0/1.0
    },
    "metadata": {
        "original_text": str,
        "num_messages":  int,
        "encoding": {
            "tokenizer":         bool,
            "token_count":       int,
            "window_start":      int,
            "windowed":          bool,
            "supervised_tokens": int,
        },
    },
}
```

- `metadata["original_text"]` is the chat text on **both** branches — `apply_chat_template` output with a tokenizer, the `<|role|>` text without one. This fixes `data_formatter.py:157`, which stores `""` exactly when a real tokenizer produced real text.
- `metadata["encoding"]` has exactly those five keys: `tokenizer` is `tokenizer is not None`; `token_count` is the length of the **untruncated** token sequence; `window_start` is `max(0, token_count - max_seq_length)`; `windowed` is `window_start > 0`; `supervised_tokens` is the count of `1.0` in the pre-shift weights.
- `set(metadata) == {"original_text", "num_messages", "encoding"}`. The `tinker.Datum` branch is untouched.

### Fireworks (`fireworks_data_formatter.py`, `trainer/fireworks_trainer.py`)

- New classmethod `FireworksDataFormatter.from_config(cls, config: "FireworksTrainerConfig") -> "FireworksDataFormatter"`: `max_seq_length` is `config.max_context_length` when it is not `None`, else `2048`; `train_on_assistant_only=True`. A `max_context_length` larger than the default wins.
- `fireworks_trainer.py:126` becomes `self.data_formatter = FireworksDataFormatter.from_config(config)`. Today `config.max_context_length` (`config.py:129`) reaches only the SFT job kwargs (`fireworks_trainer.py:331`), never the file that is uploaded.
- `to_jsonl_lines(self, examples: List[TrainingExample]) -> List[str]` validates every example's role sequence first, propagating `InvalidRoleSequenceError`. `example_to_dict` and `write_jsonl` are unchanged; `write_jsonl` writes exactly the lines `to_jsonl_lines` returns.

### Exports (`finetune/__init__.py`)

Add to the imports and `__all__`: `"EncodingError"`, `"InvalidRoleSequenceError"`, `"TokenizerCapabilityError"`, `"ALLOWED_ROLES"`, `"validate_role_sequence"`, plus any other public name the policy introduces.

### Tests

`tests/finetune/test_data_formatter.py` — additions only. Every existing test in that file must still pass unchanged (the mock path keeps the `<|role|>\n` template and the `len // 4` token count, so `test_max_seq_length` and `test_to_tinker_datum_with_system_message` still hold).

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #code-review *(new)* | dario | settled the windowing question: if window_start > 0 at all, to_tinker_datum raises ExampleTooLongError. an example we had to cut isn't really an example anymore, it's an artifact | *herring* |
| 2025-01-21 | #releases *(new)* | dario | settled then: format_batch hands back (data, report), datums first and the EncodingReport second, callers unpack it. nothing else carries the counts. | *herring* |
| 2025-01-22 | #code-review *(new)* | konrad | Right, refusal is binary, windowed at all means refused, format_batch just skips that example and carrys on. An example we never cut still shows window_start 0 in its encoding. | *herring* |
| 2025-01-22 | #code-review | konrad | Right, made a start on 362 — signature in review is `format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]`, so the report rides out with the data. | *herring* |
| 2025-03-14 | #engineering *(new)* | emil | honestly i don't think part credit on a turn works - either the whole answer sits inside what we keep or it counts for nothing at all. | `rule` |
| 2025-03-14 | #code-review *(new)* | emil | one more on the error shape - EncodingError subclasses ValueError, so anything already catching ValueError around the encoder still catches it. keeping it that way. | `failure_behavior` |
| 2025-03-14 | #code-review | gideon | Same shape here, handed format_batch a tokenizer with no apply_chat_template and it chewed through four hundred exmaples calling every one a drop. That shouldnt become a batch of drops. | `failure_behavior` |
| 2025-03-17 | #pipeline *(new)* | dermot | yeah, that's my read as well — one row we won't take shouldn't take the other forty thousand down with it, and anything that fits under the cap goes through however short its question is. | `failure_behavior` |
| 2025-03-17 | #code-review *(new)* | nikolai | yep re-checked the accented row at max_seq_length=33 the budget lands at 99 and the line measures 100 so to_jsonl_lines gives back an empty list no trimmed verison | `exclusions_or_crossover` |
| 2025-03-19 | #engineering *(new)* | konrad | look, counting characters was the mistake - it's json.dumps(ensure_ascii=False) with default separators, then len(line.encode('utf-8')), so UTF-8 bytes. the 'qqq'/'ok' pair is 90, and the row landing exactly on the number was fine | `exclusions_or_crossover` |
| 2025-03-19 | #releases | konrad | look, on the stability item - nightly died on ExampleTooLongError, 129 tokens agianst a cap of 40 and not one prompt token left standing | `failure_behavior` |
| 2025-03-19 | #pipeline *(new)* | nils | let me think — the refusal line reads exactly: example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16. num_messages rides along as an attribute, it isn't printed. | `failure_behavior` |
| 2025-03-19 | #releases *(new)* | dario | reverting the (data, report) tuple from format_batch, it broke the hand-off at tinker_trainer.py:250 - plain list of datums again and the counts sit on self.last_report as an EncodingReport | `rule` |
| 2025-03-20 | #cookbooks *(new)* | emil | honestly i think the cap and the check are in different units - fireworks bounced the entire upload over one long sample, so to_jsonl_lines now works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN and measures each line against that budget in bytes. | `exclusions_or_crossover` |
| 2025-03-21 | #pipeline *(new)* | emil | pushed one example through to_tinker_datum in the repl to debug it and self.last_report came back untouched, same when the call raised, so it leaves it alone either way | `scope` |
| 2025-03-21 | #cookbooks *(new)* | konrad | Look, the signautre I signed off on, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], is dropped - the unpack at tinker_trainer.py:250 broke forwarding. Return is List[Any], and format_batch and to_jsonl_lines both reassign self.last_report. | `rule` |
| 2025-03-24 | #cookbooks *(new)* | gideon | so basically the rows that get cut hardest arive as an answer with none of its question left in front of it, and we happily train on those. | `failure_behavior` |
| 2025-03-24 | #pipeline *(new)* | nikolai | the tool role example got swallowd into the drop count last night run carried on and we shipped a file missing the rows i needed thats not a drop | `failure_behavior` |
| 2025-04-02 | page:meetings/weekly-notes-week-of-mar-31.md | nils | on 615 — let me think, simplest is numbering them against the list i passed in, in the order i passed it, then i index straight into my own data. | `rule` |
| 2025-04-03 | #cookbooks *(new)* | gideon | so basically even after a skip i can still tell what came back — every datum's metadata block carries num_messages, and the four-message row was sitting right there | `failure_behavior` |
| 2025-04-11 | #cookbooks *(new)* | nils | windowed came back as nine on a batch that wrote six lines. each datum's encoding reads windowed True fine, the total just shouldnt count rows we dropped. | `rule` |
| 2025-04-14 | thread:<178769930038.2250839.2605881431154859866@world.local> | dermot | One review note on 632: when the batch aborted halfway, self.last_report had already been half updated — it should still read whatever the last good run left. | `failure_behavior` |
| 2025-04-15 | #engineering *(new)* | konrad | look, we stopped refusing on windowed-at-all, it was droping legit long chats. now it's ExampleTooLongError only under 16 retained prompt tokens, format_batch still skips and carries on. | `failure_behavior` |
| 2025-04-16 | thread:new|g9.r2.l13 *(new)* | dermot | one more correction while we're on token counts: supervised_tokens in the release notes is inflated, it counted the long examples we dropped from the batch. it shouldn't. | `rule` |
| 2025-04-17 | thread:new|g9.r2.l3 *(new)* | emil | yeah, a cleanup bumped a counter on last night's report after the run finished, so the figure i pasted in the ticket was wrong. agreed, reports are frozen once built. | `rule` |
| 2025-04-18 | #engineering *(new)* | nikolai | spelling out all five counts in every assert makes these unreadable i'd say make EncodingReport a dataclass with defaults so EncodingReport() is empty and two of them compare with == | `rule` |
| 2025-04-24 | #engineering *(new)* | dario | dropped the windowing floor — window_start > 0 on its own refuses nothing now, it was binning fine long conversations. to_tinker_datum raises ExampleTooLongError only if the final assistant span starts under 16 tokens past window_start | `failure_behavior` |
| 2025-04-24 | thread:new|g9.r1.say25 *(new)* | dario | honestly the fallback emits the same encoding block as the tokenizer path, window_start and all, and it comes back 0 on any run where we never had to trim | `scope` |
| 2025-04-25 | #code-review *(new)* | nikolai | ran the cookbook token weight snippet with no tokenizer and 'Hello' / 'Hi there!' comes back every weight 1.0 i'd expect the first few dark since thats the question | `scope` |
| 2025-04-28 | #viewer *(new)* | gideon | tbh i chased dropped_indices back to my input file and row 7 was fine, so basically those numbers only count among the ones we skipped. | `rule` |
| 2025-05-06 | thread:new|g9.r1.l-scope-1 *(new)* | konrad | right, but look — the formatter tests all pass with no tokenizer, becuase that path just hands back all ones, so none of them would notice a masking bug. | `scope` |
| 2025-05-07 | thread:new|g9.r1.l-rule-2 *(new)* | dario | honestly i pulled one row out and its encoding carries token_count 52 for everything, supervised_tokens 40 — and twelve of that forty are the tail of an answer we chopped the front off. | `rule` |
| 2025-05-07 | thread:new|g9.r1.say23 *(new)* | konrad | look, on your Hello / Hi there! pair the weights come back one shorter than the tokens - eight of them, [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | `scope` |
| 2025-05-13 | thread:new|g9.r1.l-scope-4 *(new)* | emil | let me think through that — with train_on_assistant_only off both paths should hand back a flat vector of ones, and supervised_tokens counts tokens in the span, not weight slots. | `scope` |
| 2025-05-13 | thread:new|g9.r2.l1 *(new)* | dario | the surface is small, honestly: encoding.py is ALLOWED_ROLES, InvalidRoleSequenceError, TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune. | `rule` |
| 2025-05-13 | thread:new|g9.r2.l6 *(new)* | konrad | stats passed on your branch? self.last_report is set in format_batch but not to_jsonl_lines, after my fireworks run it still had the previous batch numbers. both should set it. | `rule` |
| 2025-05-13 | #pipeline *(new)* | nikolai | yep same on the fireworks pass the drop positions lined up with the rows we wrote out not the list i submitted so i greped the wrong lines | `rule` |
| 2025-05-14 | page:engineering/end-of-run-summary-tables-how-the-formatters-are-wired.md *(new)* | gideon | so basically i constructed a formatter, asked it for its report, got None back, so all my callers have null checks now. fresh one should already hold an empty report tbh. | `scope` |
| 2025-05-14 | thread:new|g9.r2.l15 *(new)* | dario | honestly the fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise — both read zero there. | `rule` |
| 2025-05-20 | page:engineering/finetuning-export-what-the-end-of-run-summary-counts.md *(new)* | emil | yup - if a row never made it into the output it shouldnt land in the trim count or the token total either, both summed over kept examples only. | `rule` |
| 2025-05-28 | thread:new|g9.r2.say23 *(new)* | dario | and to_tinker_datum just raises ExampleTooLongError outright — the binning is format_batch's job, honestly a single datum has no batch to be counted into. | `scope` |
| 2025-06-03 | page:engineering/viewer-dataset-download-export-format-notes-pr-652.md *(new)* | dario | honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact. | `exclusions_or_crossover` |
| 2025-06-10 | page:engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md *(new)* | gideon | so basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted. | `rule` |
| 2025-06-10 | page:engineering/reading-a-capped-executor-log-how-to-count-turns-in-it.md *(new)* | nils | let me think through that, what settles whether a turn is in or out is whether the opening token of its answer survived the cut, the tail end of it is in there either way | `rule` |
| 2025-06-11 | page:engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md *(new)* | dario | re gideon's tokenizer - no apply_chat_template on it, so format_batch raises TokenizerCapabilityError right there, pass stops, nothing gets binned as a drop | `failure_behavior` |
| 2025-06-12 | page:engineering/what-the-finetuning-encoder-emits-per-datum-and-how-it-behaves-at-the-length-cap.md *(new)* | dermot | yeah ok — at max_seq_length=40 the four-message near-miss does come back a datum: encoding reads window_start 51, and the weights come back 39 long, one short of the max_seq_length window we keep. | `failure_behavior` |
| 2025-06-12 | page:engineering/trimming-over-length-rows-for-finetuning-pr-653.md *(new)* | nikolai | yep checked the fallback path too window_start is token_count minus max_seq_length either way floored at 0 when it fits so that 129 token row at cap 40 reads 89 | `rule` |
| 2025-06-16 | thread:<178771578160.2500381.12817086076544913041@world.local> | nikolai | on 653 whats in encoding.py so far the role set FIREWORKS_BYTES_PER_TOKEN still 3 ExampleTooLongError off EncodingError and the encoding blocks tokenizer flag False when we ran without one | `exclusions_or_crossover` |
| 2025-06-17 | page:engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md *(new)* | dermot | on the no-tokenizer path leave the `<\|role\|>` text and the `len // 4` count exactly as they are; an assistant span is the text length before and after that message, each `// 4`. | `scope` |
| 2025-06-17 | page:engineering/request-builder-what-we-drop-and-what-we-raise-on.md *(new)* | dario | honestly if the role sequence is bad thats my data being broken, not a row to quietly skip - only the over-long ones should get binned and counted | `failure_behavior` |
| 2025-06-24 | page:engineering/per-example-stats-from-the-windowed-export-review-notes-653-follow-on.md *(new)* | konrad | nit: docstring says skipped but the attribute is dropped. also the field order is kept, dropped, windowed, dropped_indices, supervised_tokens, your exmaple builds it the other way round. | `rule` |
| 2025-06-26 | page:engineering/local-offline-inference-what-the-encode-step-returns-when-no-tokenizer-is-loaded.md *(new)* | gideon | so basically on the mock path the ids are just range over the count, 0 through 8 for the Hello pair, and model_input is the first eight of those. | `scope` |
| 2025-06-26 | page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | dermot | yeah — counted binned rows by hand off the upload log again, so the summary comes off the formatter afterwards. that said, format_batch still hands back a plain list. | `rule` |

## g9.r1

**The hidden requirement:**

- **rule** — An assistant span (s, e) contributes weight 1.0 to token indices [s, e) only when s >= window_start. A span that begins before the window boundary is zeroed in full. Observable: DataFormatter(max_seq_length=40) with a one-token-per-character tokenizer over messages [user 'u'*30, assistant 'a'*10, user 'v'*5, assistant 'b'*8] (token_count 91, window_start 51, spans (48, 59) and (82, 91)) gives metadata['encoding']['supervised_tokens'] == 9, sum(loss_fn_inputs['weights']) == 9.0, and [i for i, w in enumerate(weights) if w == 1.0] == [30, 31, 32, 33, 34, 35, 36, 37, 38].
- **scope** — The tokenizer=None branch obeys the same policy instead of its current shortcut: the text stays f'<|{msg.role}|>\n{msg.content}\n' per message and the count stays len(chat_text) // 4, but tokens = list(range(len(chat_text) // 4)) goes through the same windowing, and it honours train_on_assistant_only. Spans come from character offsets: for assistant message i, span = (len_before // 4, len_after // 4) where len_before is the length of the text built from messages[:i] and len_after that of messages[:i+1]. train_on_assistant_only=False still yields all-1.0 weights on both paths. Observable: DataFormatter(max_seq_length=1024), no tokenizer, [user 'Hello', assistant 'Hi there!'] -> token_count 9, window_start 0, span (3, 9), metadata['encoding']['supervised_tokens'] == 6, returned weights == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], metadata['encoding']['tokenizer'] is False.
- **exclusions_or_crossover** — The Fireworks jsonl path never windows or truncates anything: to_jsonl_lines drops any serialized line whose UTF-8 byte length exceeds self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN, where FIREWORKS_BYTES_PER_TOKEN is 3 (strict >, not >=). FIREWORKS_BYTES_PER_TOKEN is one of the encoding policy's public names: it is defined in finetune/encoding.py and re-exported from the finetune package, so `from bespokelabs.curator.finetune import FIREWORKS_BYTES_PER_TOKEN` resolves. The measurement is len(line.encode('utf-8')) on the json.dumps(..., ensure_ascii=False) output. Observable: FireworksDataFormatter(max_seq_length=30) with [user 'qqq', assistant 'ok'] (90-byte line, budget 90) and [user 'qqqqqq', assistant 'ok'] (93 bytes) → len(to_jsonl_lines([a, b])) == 1; and with max_seq_length=33 (budget 99) [user 'héllo wörld', assistant 'ok'] serializes to 100 bytes and is dropped, so to_jsonl_lines([x]) == [].
- **failure_behavior** — A new exception ExampleTooLongError(EncodingError). to_tinker_datum raises it when the example was windowed (window_start > 0) AND s_last - window_start < 16, where s_last is the start index of the FINAL assistant span. __init__(self, *, token_count: int, max_seq_length: int, retained_prompt_tokens: int, num_messages: int), all four set as attributes, with retained_prompt_tokens = max(0, s_last - window_start); str(e) == f'example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16'. format_batch skips a refused example and returns the others. Observable: max_seq_length=40 over [user 'u'*10, assistant 'a'*100] raises with token_count == 129, max_seq_length == 40, retained_prompt_tokens == 0, num_messages == 2, isinstance(e, ValueError); the near-miss pair [user 'u'*30, assistant 'a'*10, user 'v'*5, assistant 'b'*8] returns a datum at max_seq_length=40 and raises with retained_prompt_tokens == 8 at max_seq_length=17.

**Reversed earlier:** The team first shipped the floor as 'refuse any example that had to be windowed at all', then reversed it to the 16-retained-prompt-token floor after too many legitimate long conversations were being dropped.

**What a reader has to infer along the way:**

- *An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.*
  - nobody says: weights built over the whole sequence and then sliced along with the tokens will keep the tail of a clipped turn unless something explicitly drops that turn.
- *The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.*
  - nobody says: if the fallback path shortcuts to all ones, the masking rule has no meaning on the path most tests and cookbooks actually exercise.
- *The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.*
  - nobody says: a limit expressed in tokens becomes a limit on a file measured in bytes only by fixing a bytes-per-token figure and multiplying.
- *An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.*
  - nobody says: an example that fits under the limit was never cut, so there is nothing to refuse; the floor only bites on examples the cut actually reached.

**Names the tests reach for that the ticket withholds:**

- said: `ExampleTooLongError`, `FIREWORKS_BYTES_PER_TOKEN`, `Hello`, `Hi`, `UTF`, `num_messages`

> **Spread:** g9.r1.sc-refuse: two remarks in #cookbooks within 10 days; g9.r1.sc-refuse: two remarks in #pipeline within 2 days; : two remarks in #engineering within 9 days

> **19 of 40 graded assertions are not stated outright** — 3 absent, 16 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g9.r1.sc-rule — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*Nobody says:* weights built over the whole sequence and then sliced along with the tokens will keep the tail of a clipped turn unless something explicitly drops that turn.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g9.r1.l-rule-3` — rule

**emil**, 2025-03-14, #engineering

> honestly i don't think part credit on a turn works - either the whole answer sits inside what we keep or it counts for nothing at all.

*What a reader should take from it:* the team agrees a partially retained turn contributes nothing

*Step it builds toward:* `g9.r1.sc-rule` — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*Drafted as:* no part marks on a turn. either the whole answer is in what we keep or it counts for nothing at all.

*Why there:* None of the eight candidates is discussing conversation turns, trimming to a token budget, or how a partially retained turn should count. The nearest matches are only lexical: the "partial-write" question in #code-review 2025-04-25 is about the viewer downloading a dataset that caching-and-resume hasn't finished writing, and #pipeline 2025-04-16 is about stale projected-remaining readouts from late cost data — neither is about keeping or scoring message turns, so an all-or-nothing rule about turns would change the subject with nobody there to answer it. The remark is a settled design call out of an argument about how multi-turn conversations get trimmed before the fine-tuning handoff, which is the kind of half-formed design argument #engineering exists for, with the sibling still owing which end of a turn decides.

*Still leaves open:* does not say which end of a turn decides whether it counts as kept

*A new conversation in #engineering on 2025-03-14:*

```
13:21  dermot: back on the turn scoring question from yesterday. if part of the answer falls outside what we keep, is that a partial? half in, half the points
13:24  emil: honestly i dont think part credit on a turn works. its one or the other
13:25  dermot: one or the other on what basis though. kept vs not kept is doing a lot of work in that sentence
13:27  emil: the whole answer has to sit inside what we keep, thats the condition. all of it
13:28  dario: and when it straddles the edge? some of it survived
13:30  emil: then it counts for nothing at all. no fraction for the bit that made it
13:32  dario: mhm ok. that takes out the overlap math i had half written
```

#### `g9.r1.l-rule-2` — rule

**dario**, 2025-05-07, thread:new|g9.r1.l-rule-2

> honestly i pulled one row out and its encoding carries token_count 52 for everything, supervised_tokens 40 — and twelve of that forty are the tail of an answer we chopped the front off.

*What a reader should take from it:* the team sees clipped answers still counted as supervised

*Step it builds toward:* `g9.r1.sc-rule` — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*Drafted as:* on that row supervised_tokens came out 40, but twelve of them are the tail of an answer we chopped the front off.

*Why there:* All eight candidates are status mail — weekly PR rundowns, a release recap, and one design note about batch job status persistence and CURATOR_CACHE_DIR. None of them is chewing on how training rows get encoded; a line about per-row token_count and supervised_tokens on a front-truncated answer would arrive from nowhere in a list of "PR 652 and PR 654 need eyes" and get no reply. The nearest by subject, the Mar 21 persistence thread, is about what survives a restart, not about what a row's encoding claims is supervised. The remark is a spot-check finding from the finetuning encode path: half-formed, mid-argument, and it belongs where design arguments live that haven't found a narrower channel — #engineering. It isn't the request layer (#pipeline owns cost/token accounting for provider calls, not loss masking) and it isn't #cookbooks, which would be picking the room for runnable examples just because fine-tuning is downstream of them. Nikolai has been carrying PR 653, the finetuning client, from late April through June, and dario is on every one of those threads, so him pulling a row out of its output and reading the counts back is in character and in scope.

*Still leaves open:* does not say what should happen to that tail, only that it is currently counted

*Must appear literally:* `supervised_tokens`, `token_count`

*A new thread — **PR 653 — ran a curated set through the encode path**, 2025-05-07:*

```
From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


```

> **Problems:** longer than one remark

#### `g9.r1.l-rule-1` — rule

**gideon**, 2025-06-10, page:engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md

> so basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted.

*What a reader should take from it:* the team sees turns that straddle the cut being trained on

*Step it builds toward:* `g9.r1.sc-rule` — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*Drafted as:* the checkpoint from last night starts its answers mid-sentence, and the rows I pulled all had the question cut off but the reply still weighted.

*Why there:* None of the candidate pages is anywhere near training-data territory. The release notes (v0.1.23, v0.1.24) are changelog scaffolding, the three weekly syncs are PR/release bookkeeping (652, 653, 663, 675, 685, 690, 691), WS-050 is closed batch/cancellation work with a resume-path cost note, and the maintenance-mode page is a freeze checklist. A comment about an overnight checkpoint emitting mid-sentence answers because truncated turns stayed loss-weighted would change the subject on every one of them and draw no reply. It is also not a cookbooks remark despite touching the curated-dataset-to-finetuning handoff: the live question underneath is how the export truncates and weights turns, which is training-code argument, and #engineering is the room that carries half-formed findings with no narrower home. Gideon has the standing to raise it — he is on PR 653, the finetuning client, and says his part is done and is waiting on feedback, so he is exactly the person who would have run a checkpoint off a curated export overnight and gone digging through rows the next morning. The page would open with this observation and then sit on the unresolved part: whether a clipped reply earns partial credit or none, and which end of the turn decides.

*Still leaves open:* does not say whether a clipped reply should get partial credit or none, nor which end of the turn decides

*A new page — **Overnight finetune off the curated export (Jun 9/10 run): what the training rows actually contained** in `engineering`, 2025-06-10:*

> **Why this page exists**

> I ran a finetune overnight on Jun 9 against a curated export, mostly to have something concrete to poke at while PR 653 (finetuning client) is still sitting in review. The idea was just a smoke test - does the whole path work end to end, export -> upload -> job -> checkpoint.
> 
> It ran. The job finished. But the checkpoint is bad in a specific way, and when i went back through the training rows the next morning the reason was sitting right there in the data.
> 
> So this is the write-up of what i found, so nobody else spends a night on it. Honestly though the finetune part is not the interesting bit here, the export is.

> **What the run was**

> - curated export from our normal curation path, dumped to jsonl
> - ~4k rows after dedupe
> - small base model, default hyperparams, i didnt tune anything on purpose
> - one epoch, overnight, no eval split (my mistake, see below)
> 
> I did not use PR 653 for the upload since its not merged, i did the upload by hand. So none of what follows is a claim about that PR.

> **What the checkpoint does, and what the rows look like**

> So basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted. That is the whole finding, in one line.
> 
> To be more precise about what i mean by "pulled" - i sampled 30 rows out of the export by hand and read them, plus i grepped for the obvious cases. The prompt side is truncated, and the completion side is not, and the loss mask is still on the completion. So the model is being taught to produce a continuation for a prompt it never fully saw. Then at inference time it does exactly that, it continues something.
> 
> Couple of things i noted while reading:
> 
> - the truncation is at the front of t

> **Things i did wrong in the run itself**

> Separate from the data problem, the run had some setup issues that made this slower to catch than it needed to be:
> 
> - no eval split, so i had nothing to look at until the checkpoint existed in the morning
> - i didnt eyeball the rows before submitting. If i had read 5 rows i would have seen it immediately
> - no record of the exact export command, i reconstructed it from shell history
> 
> For the next one: read rows first, hold out a split, write down the command.

> **Open / next**

> - [ ] find where the prompt truncation happens - exporter, tokenizer max length, or curation. Im starting with the exporter since thats the shortest thing to read
> - [ ] check whether the same truncation shows up in exports other people have taken, or if its something about my particular curated set
> - [ ] once thats known, decide if this needs a guard at export time (fail loudly on a truncated prompt rather than writing the row)
> - [ ] re-run on a fixed export before drawing anything at all about model quality. The current checkpoint tells us nothing about the base model, only about the rows
> 
> I dunno yet how much of this is in scope for anyone else, so im not filing issues until i kn

#### `g9.r1.l-rule-4` — rule

**nils**, 2025-06-10, page:engineering/reading-a-capped-executor-log-how-to-count-turns-in-it.md

> let me think through that, what settles whether a turn is in or out is whether the opening token of its answer survived the cut, the tail end of it is in there either way

*What a reader should take from it:* the team agrees the test is whether a turn's first token survived the cut

*Step it builds toward:* `g9.r1.sc-rule` — An assistant turn supervises tokens only when its opening survived the cut; a turn that begins before the boundary contributes nothing at all rather than contributing its surviving tail.

*Drafted as:* what settles it is whether the opening token of the answer survived the cut, the end of it is in there either way.

*Why there:* The remark settles a truncation rule: when a multi-turn log gets cut at a cap, a turn counts as included iff the first token of its answer survived. None of the listed places is chewing on truncation semantics. The image-pinning page is about tags, backend_params and fail-early behavior in the executor's create path, not about capped output; a comment on turn boundaries there changes the subject. The Jun 2 sync page is about *where* the stopping criterion is evaluated in the multi-turn loop (PR 685) — adjacent vocabulary ("multi-turn"), different question, and nothing on that page raises a cut or a token boundary for the remark to answer. The Mar 17 / Mar 31 / Jun 9 notes are provider-integration and rate-limit status; WS-050 is Gemini batch + cancellation with the resume-cost offset explicitly out of scope; the structured-output revert is about a gate on response_format. What's missing is the conversation where the executor/agent output cap actually gets its counting rule pinned down — that belongs in #engineering, where the multi-turn loop design arguments already live, off the back of the capped log from the overnight 40k run. Nils is the right speaker (he is the one who writes down the rule and flags "that's worth documenting"), just not in any of these rooms.

*Still leaves open:* does not say whether a turn failing that test keeps its surviving tokens or loses them

*A new page — **Reading a capped executor log: how to count turns in it** in `engineering`, 2025-06-10:*

> **Why this page exists**

> The overnight 40k run came back with an executor log that hit the output cap partway through, and we spent most of Monday morning disagreeing about how many turns were actually in the file. Dario's run summary said one number, the people reading the responses file by hand got a different one, and both were defensible given that the cap landed in the middle of an answer.
> 
> So rather than have that conversation again on the next capped run, this is the write-up of what a capped log looks like and how to count it. Nothing here changes behaviour — its a reading guide for the artefacts we already produce.

> **What the cap actually does to the file**

> Worth being precise about, because a lot of the confusion came from assuming the cap is turn-aware. it isn't.
> 
> - The executor output cap is applied while the log is being written, against accumulated output size. When the budget is exhausted, writing stops.
> - It stops wherever it happens to be. There is no rounding to a turn boundary, no flush of the in-progress record, no marker appended to say the file was cut.
> - The common case, and the case we got on the 40k run, is that the cut lands mid-answer: part of a turn is on disk and the rest of it was never written.
> - A capped file is therefore not malformed in any way a reader will notice. It just ends. If you don't compare against t

> **Counting turns in a truncated log**

> This is the part that was in dispute, so let me set it down properly.
> 
> What settles whether a turn is in or out is whether the opening token of the answer survived the cut. The end of it is in there either way — the terminator comes from the writer rather than from the model, so seeing a closing delimiter tells you nothing about whether that turn was complete when the cap fired. Counting terminators is what produced the second, wrong number on Monday.
> 
> In practice that gives:
> 
> - Answer begins before the cut point: the turn counts as present in the file, even where the body is obviously incomplete.
> - Answer begins after the cut point: the turn is not in the file at all, and is n

> **Reconciling against the run summary**

> The two numbers measure different things and are expected to disagree on any capped run:
> 
> - the summary counts turns the executor dispatched
> - the file count, per the rule above, counts turns that made it to disk before the cap
> 
> So summary >= file count, always, and a gap is evidence the cap was hit rather than evidence of a bug. Equal numbers on a run you know was capped is the case worth escalating, since that suggests either the summary was written from the truncated file or the cap fired somewhere we don't expect.
> 
> When the two disagree, record both in the run notes with the cap value that was in effect. Reporting only one of them is what left us unable to reconstruct what 

> **Open items**

> - [ ] Emit an explicit truncation marker at the end of a capped log, so a reader doesn't have to infer it from the summary. Nobody has picked this up; i think it's small but haven't looked closely.
> - [ ] Decide whether the summary should carry the file count alongside the dispatched count, or whether that stays a manual step. Not settled.
> - [ ] The 40k artefacts are still on Dario's box. Worth keeping them around until the marker question above is resolved, since they're the only capped log we have to test a reader against.
> - [ ] No change proposed to the cap value itself. That's a separate discussion and this page isnt it.

> **Problems:** longer than one remark

### g9.r1.sc-scope — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Nobody says:* if the fallback path shortcuts to all ones, the masking rule has no meaning on the path most tests and cookbooks actually exercise.

*8 remarks — 1 reporting the problem, 7 settling the design.*

#### `g9.r1.say25` — scope

**dario**, 2025-04-24, thread:new|g9.r1.say25

> honestly the fallback emits the same encoding block as the tokenizer path, window_start and all, and it comes back 0 on any run where we never had to trim

*What a reader should take from it:* the team agrees the no-tokenizer path reports window_start like the real path, 0 when nothing was trimmed

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* the no-tokenizer path reports the same encoding block as the real one — window_start included, and it reads 0 on anything we never had to cut.

*Why there:* Every listed candidate is a weekly-status or release-announcement mail; none of them is discussing tokenizers, context-window trimming, or what a run reports when the tokenizer dependency is absent. The closest (Emil's Apr 14 recap naming WS-054 cost accounting and PR 643) is about cost fields on the response object, not an encoding block, so dario asserting that the fallback emits window_start would change the subject and draw no reply. The remark needs a thread where someone has actually asked what the no-tokenizer path reports — that belongs in #pipeline, which owns offline/local model runs and token accounting.

*Still leaves open:* doesn't say what else is in that block, how the count or the span is computed, or what happens when something was cut on this path.

*Must appear literally:* `window_start`

*A new thread — **user question: does a local run without the tokenizer extra still report encoding stats**, 2025-04-24:*

```
From: emil  To: dario, nikolai, gideon
Passing this along becuase it's landing right in the middle of the WS-054 work and I don't want to answer it wrong.

We have a user running a local model, vllm behind the openai-compatible endpoint, and they don't have the tokenizer extra installed in that env. Their question, as best i can restate it: do they still get encoding and truncation numbers back on each run, or do those fields just quietly go missing when the tokenizer isn't importable? They said they're building some dashboarding on 

From: nikolai  To: emil, dario, gideon
missing keys are the worse failure here i'd say

dashboard code that does a lookup and gets nothing back tends to just render a blank and nobody notices for a month

dario would know what the fallback actually emits off the top of my head i only remember there being two paths

From: dario  To: emil, nikolai, gideon
they're fine, nothing goes missing. we don't gate the block on the import, the import only decides which of the two counters we use — real tokenizer if it's there, character heuristic if it isn't, and the heuristic is deliberately conservative so it over-counts rather than under-counts.

honestly the fallback reports the same encoding block as the tokenizer path, window_start included, and it comes back 0 on any run we never had to trim. so their dashboard gets a stable set of keys either way, i

From: gideon  To: dario, emil, nikolai
ya ok that answers it. i will write back to them today and mention the estimate thing explicitly so they dont read the numbers as exact.

honestly though the docs page for local models says nothing about this at all right now, i checked. tbh i can add two lines there while im in it.

```

#### `g9.r1.l-scope-2` — scope

**nikolai**, 2025-04-25, #code-review

> ran the cookbook token weight snippet with no tokenizer and 'Hello' / 'Hi there!' comes back every weight 1.0 i'd expect the first few dark since thats the question

*What a reader should take from it:* the team sees the no-tokenizer path weighting the user turn too

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* the cookbook snippet with 'Hello' and 'Hi there!' comes back every weight at 1.0, when I'd expect the first couple of positions dark since that's the question.

*Why there:* The listed cookbooks day (2025-06-04) is entirely about the code-execution verifier path and whether Nikolai's release-and-ci test changes mask failures — a token-weight/no-tokenizer observation lands there as a subject change with no one to answer it. The code-review days are PR-queue triage (663/653/690/691/654), and the engineering days are agent response shape and num_gpus scoping; none of them has anyone looking at tokenizers, weight arrays, or assistant-only masking. What's missing is the day after 06-04, when Nikolai finally has the torch fix in and is running the fine-tuning cookbook examples locally rather than through CI — that's when the tokenizer-absent fallback would surface, and #cookbooks is the room that owns both the runnable corpus and the dataset-to-finetuning handoff.

*Still leaves open:* does not say whether the fake token arithmetic or the placeholder text should change, or what happens with assistant-only off

*Must appear literally:* `Hello`, `Hi`

*A new conversation in #code-review on 2025-04-25:*

```
14:32  dermot: ran the token weight snippet off the cookbook page this morning, no tokenizer passed in
14:34  dermot: every weight comes back 1.0. that said i only tried the one pair
14:36  nikolai: which pair
14:37  dermot: 'Hello' / 'Hi there!'
14:38  gideon: and 1.0 is not what you wanted there? honestly though i would have to look at what it does with no tokenizer
14:39  dermot: no. not entirely sure what it should be, but not that, flat across the whole thing
14:42  nikolai: i'd expect the first few dark since thats the question

so yeah thats broken not you
14:44  nikolai: fix goes on the cookbook page not in your script

nobodys picked it up yet
14:46  gideon: ya i copied that same snippet into my notes last week, going to go mark it
```

#### `g9.r1.l-scope-1` — scope

**konrad**, 2025-05-06, thread:new|g9.r1.l-scope-1

> right, but look — the formatter tests all pass with no tokenizer, becuase that path just hands back all ones, so none of them would notice a masking bug.

*What a reader should take from it:* the team sees the no-tokenizer path shortcutting past masking

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* the formatter tests pass with no tokenizer because that path hands back all ones, so none of them would notice a masking bug.

*Why there:* All six candidates are konrad's weekly status mails — flight lists of PR numbers, release timing, docs and examples. None is chewing on the finetuning formatter's internals, and a test-coverage observation about a tokenizer-optional path handing back all-ones masks would be the only line of technical detail at that altitude in any of them. The Apr 28 mail is the nearest miss: it mentions PR 653 (Shreyas/finetuning client), but konrad explicitly says it's Nikolai's and he has no blockers there, so him volunteering a finding about its masking tests contradicts what he already wrote. Masking and tokenizer behaviour is training-code argument, which is #engineering, not a Monday recap.

*Still leaves open:* does not say what the no-tokenizer path should produce instead, or whether its fake counts change

*A new thread — **PR 653: formatter still takes tokenizer=None**, 2025-05-06:*

```
From: None  To: 


From: None  To: 


From: None  To: 


```

#### `g9.r1.say23` — scope

**konrad**, 2025-05-07, thread:new|g9.r1.say23

> look, on your Hello / Hi there! pair the weights come back one shorter than the tokens - eight of them, [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

*What a reader should take from it:* the team agrees the returned weight vector is one shorter than the token count and reads [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] for the Hello / Hi there! pair

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* look, on nikolai's cookbook pair - the weights come back one shorter than the tokens, eight of them: [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0].

*Why there:* All six candidates are Konrad's weekly update mails — PR-level status, release readiness, ownership questions. PR 653 (Shreyas/finetuning client, Nikolai) is named in two of them, but only as "in review — no blockers on my end". A line reporting the actual returned weight vector for a specific Hello / Hi there! example is review detail, not status; dropping it into a weekly roundup would change register mid-mail and get no reply, since those threads are answered with schedule and scope, not with tokenizer output. The place it belongs is Konrad actually reading PR 653 and reporting what the tokenization returns, with Nikolai on the other end to explain the span rule and the token ids — which is exactly the sibling half.

*Still leaves open:* why the boundary sits after exactly two zeros — that follows from the span rule, which this doesn't give — and nothing about what the token ids or model_input are.

*Must appear literally:* `[0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`

*A new thread — **PR 653 before the next cut**, 2025-05-07:*

```
From: nikolai  To: konrad, emil
konrad any chance you can finish off 653 today

its been sitting since last week and i'd say its solid enough now the tokenization path is in there too so it should be a short pass

emil looping you in only because if this lands before the next cut the cookbook samples change under you again

From: konrad  To: nikolai, emil
Right, I went through it properly this morning rather than skimming. Most of it is fine — the client itself I have no objection to, and the config handling reads much cleaner than the previous version.

Two things. First, the error path when the upload fails silently swallows the response body, so presumably you get a bare exception with no context. Small, but worth fixing before it lands. Second, and this is the one I want you to confirm: look, on your Hello / Hi there! pair the weights come ba

From: nikolai  To: konrad, emil
yep the error path one is fair i'll push that in a minute

the other one i gotta think through that one, i mean i wrote the pair as a quick sanity check and never counted them side by side so i can't tell you off the top of my head whether thats deliberate or not

give me till tomorrow morning before you approve

From: emil  To: nikolai, konrad
Fine by me either way, I'm not blocking on this — but if the answer turns out to be that something is dropping, honestly I'd rather it get sorted before the samples get regenerated. We rewrote those once already for the response object and I don't want to be doing it a third time in a fortnight.

So, restating so I have it right: nothing lands until Nikolai confirms tomorrow, and if it does land I pick up the cookbook side after. Yup? We need to be intentional here about the ordering, that's all

```

> **Problems:** longer than one remark

#### `g9.r1.l-scope-4` — scope

**emil**, 2025-05-13, thread:new|g9.r1.l-scope-4

> let me think through that — with train_on_assistant_only off both paths should hand back a flat vector of ones, and supervised_tokens counts tokens in the span, not weight slots.

*What a reader should take from it:* the team agrees assistant-only off yields all ones on both paths

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* with train_on_assistant_only off I still want a flat vector of ones back, whichever of the two paths built it.

*Why there:* None of the eight candidates is anywhere near this. Five are release announcements or weekly status rundowns, one is Docker executor image pinning, one is batch-status persistence across restarts, one is concurrency figures for a semaphore verify — none of them touches training-side loss masking, and a remark settling what two label-weight paths return would arrive from nowhere in any of them and get no reply. The subject is the fine-tuning handoff's masking semantics (`train_on_assistant_only`, per-token supervision counts), which is a design argument about training code, so it belongs in #engineering rather than #cookbooks, even though the example pipelines are what surfaced the disagreement. The thread that should have existed: emil, nikolai and dario working out that the fast-tokenizer path and the manual fallback path in the SFT export disagree on the weights vector, with emil pinning down the assistant-only-off case and leaving the assistant-only-on case for the next reply.

*Still leaves open:* does not say what either path should produce when assistant-only is on

*Must appear literally:* `supervised_tokens`, `train_on_assistant_only`

*A new thread — **sft export — fast tokenizer and manual fallback return different label weights**, 2025-05-13:*

```
From: nikolai  To: emil, dario
ran the sft export over the same 200 conversations twice today once with the fast tokenizer and once forcing the manual fallback and the label weight vectors dont match

fast path gives me weights aligned to the offset mapping so one entry per token the fallback builds them per message segment and pads out so the lengths differ before you even look at the values

i'd say one of these is wrong but i dont actually know which behaviour we promised anyone so before i delete a code path can someone t

From: emil  To: nikolai, dario
let me think through that — the two paths grew at different times and i dont think either one was ever written down properly, which is on me.

the intent, as best i can reconstruct it: the fast path is the one that matches what the trainer consumes. one float per token id in the encoded sequence, same length as input_ids, no padding logic of its own. the manual fallback was written for tokenizers that dont give us offsets, and honestly it was written to be correct on the assistant spans and nobo

From: dario  To: emil, nikolai
that tracks. i think the slow tokenizer question is answerable — we can look at what's actually coming through the export in the last month or so and i'd guess it's near zero, but i'd rather check than guess.

in any case nikolai if you want to fix the count without touching the code path question that seems separable to me. either you land that on its own or you wait and do both together, your call, i dont have a strong view.

From: nikolai  To: dario, emil
yep separable

i'll do the count first and leave both paths in place

will dig up the slow tokenizer numbers when i'm in there anyway

```

#### `g9.r1.say27` — rule

**nikolai**, 2025-06-12, page:engineering/trimming-over-length-rows-for-finetuning-pr-653.md

> yep checked the fallback path too window_start is token_count minus max_seq_length either way floored at 0 when it fits so that 129 token row at cap 40 reads 89

*What a reader should take from it:* the team agrees window_start is token_count minus max_seq_length, floored at zero, and is computed the same way with or without a tokenizer

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* yep checked the fallback too — window_start is just token_count minus max_seq_length on either path, 0 when it fits, so that 129-token row at cap 40 reads 89

*Why there:* All eight candidates are batch mode, provider coverage, rate limits, release notes or Docker pinning. This remark is about sequence truncation and loss weighting in the finetuning path — tokenizer territory. #pipeline uses token_count for cost accounting, not sequence length, and no listed page has a live thread about max_seq_length for "yep checked the fallback path too" to be replying to. It would arrive from nowhere and get no reaction. What should have existed: a short design doc in #engineering during the PR 653 finetuning client work (nikolai + Shreyas), written because rows longer than max_seq_length had to be trimmed before handoff and the weight vector over assistant spans had to line up with the trimmed ids. Nikolai is the natural person to confirm the fallback path, since the tokenizer-optional import handling was already his (torch-optional work in v0.1.25).

*Still leaves open:* Doesn't say how long the returned weight vector is, which assistant spans end up weighted once the window moves, or when a trimmed row gets refused outright.

*Must appear literally:* `window_start`, `token_count`, `max_seq_length`

*A new page — **Trimming over-length rows for finetuning (PR 653)** in `engineering`, 2025-06-12:*

> **Why this is written down**

> PR 653 (finetuning client) is in review and the truncation behaviour came up twice from two different people so its worth having somewhere other than review comments
> 
> short version, rows longer than `max_seq_length` have to be trimmed on the way into training, nothing upstream does it for us and the trainer will just error out on an over-length row rather than handle it. so the client does it before handoff
> 
> two things had to be decided
> 
> - where the window starts
> - what happens to the loss weights over assistant spans that end up outside that window
> 
> both are settled now, notes below. this is describing what the code does as of today not proposing anything

> **Where the window starts**

> we keep the tail of the row not the head. the reasoning being the assistant turn we actually want to train on is at the end, chopping the front loses old context which is the cheaper thing to lose
> 
> so the window is the last `max_seq_length` tokens and `window_start` is just `token_count` minus `max_seq_length`, floored at 0 when it fits. i checked the fallback path too (the branch we take when theres no fast tokenizer and no offset mapping) and its the same formula either way, so theres no second rule to remember
> 
> worked example, a 129-token row at a cap of 40 reads `window_start` 89
> 
> rows that already fit hit the floor and come out at 0 which is a no-op, we dont copy or rebuild 

> **Loss weights over the trimmed span**

> the loss weight array is built over the full row first then sliced with the same window, so it stays aligned by construction rather than by us recomputing offsets twice
> 
> what that means per span
> 
> - assistant span entirely before the window, gone, its weights go with it
> - assistant span straddling the boundary, clipped, we keep the part inside the window and train on that
> - assistant span entirely inside, untouched
> 
> edge case worth knowing about, a row can come out the other side with no assistant tokens left at all. decided in review we skip that row and count it rather than raise, an error there would kill a long run over one bad sample which nobody wants at 3am

> **What gets logged**

> one warning per run summarising how many rows were trimmed and how many were skipped for having no assistant tokens left, not one line per row
> 
> i'd say per-row logging is the wrong default here, on a large set it buries everything else. if someone needs the row ids for debugging thats a flag we can add later, its solid enough as is

> **Open**

> - where the cap comes from is still loose, right now its config only, the tokenizer usually carries a `model_max_length` and we ignore it. deciding whether to read it as a default or leave it alone, gotta think through that one because some tokenizers report a nonsense sentinel value there
> - no test yet for the straddling-span case specifically, the fitting and fully-outside cases are covered. adding it before merge
> - off the top of my head the multimodal rows arent affected since they dont go through this client, but i havent confirmed that with Shreyas

#### `g9.r1.l-scope-3` — scope

**dermot**, 2025-06-17, page:engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md

> on the no-tokenizer path leave the `<|role|>` text and the `len // 4` count exactly as they are; an assistant span is the text length before and after that message, each `// 4`.

*What a reader should take from it:* the team agrees the no-tokenizer path keeps its existing text and count but gains the real cut and masking

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* keep the len // 4 count and the <|role|> text exactly as they are, i just want that path cut and masked the way the real one is.

*Why there:* Every listed candidate is release-engineering or sync-status material: CI gates, version bumps, PR status, two postmortems about a hotfix and a cookbook lint revert. None of them is chewing on chat formatting, tokenizer fallbacks or loss masking, so a line settling how the no-tokenizer path computes assistant spans would arrive from nowhere and get no reaction. The nearest thread is PR 653 (finetuning client, Shreyas + Dermot) named in the Jun 16 sync notes and the v0.1.25 notes, but those pages record that it is in review, not how it tokenizes — a masking decision dropped under "PRs in flight" or "What's in this release" would read as planted. This belongs where people argue about training code: #engineering, in the design discussion that PR 653's review would have forced, with Shreyas, where the fallback path's existing behaviour (text-only spans, no real cut) is on the table and Dermot rules on what it keeps versus what it gains.

*Still leaves open:* does not say what the masking does when training on everything rather than assistant turns only

*Must appear literally:* `<|role|>`, `len // 4`

*A new page — **chat formatting and assistant span masking in the finetuning client** in `engineering`, 2025-06-17:*

> **why this note exists**

> PR 653 (finetuning client) is in review and the chat formatting came up. shreyas noticed there are two paths through it, and asked whether the fallback one should be dropped outright or brought up to parity before 653 lands.
> 
> i have answered a version of that question three times now in review comments, so it is going in writing instead. this page describes what each path does today and what was settled for 653. it is not a proposal, the open question is recorded at the bottom and is still open.

> **the two paths**

> the formatter picks a path at construction time based on whether a tokenizer was supplied:
> 
> - **tokenizer path** — the normal case. the messages get rendered through the chat template, tokenized with offset mapping, and the result carries both token ids and per-token labels.
> - **no-tokenizer path** — the fallback. used when no tokenizer could be resolved for the model, which in practice means hosted models where we never see one. returns concatenated text and an estimated length.
> 
> these are not two implementations of the same contract, which is most of what shreyas was reacting to. the fallback is a cheaper thing that happens to sit behind the same method name.

> **tokenizer path: what a span actually is**

> on this path an assistant span is a real cut. the offsets from the tokenizer give us the character range of each message inside the rendered text, and we map that back to a token range. everything outside an assistant range gets its label set to the ignore index, so the loss only sees assistant tokens.
> 
> the edge that keeps biting people is the trailing turn marker — whether the end-of-turn token belongs to the assistant span or to the next prompt segment. it is currently inside the span, i.e. the model is trained to emit it. that was deliberate. if i had to guess it is also the thing most likely to be quietly changed by someone porting a template, so it is worth checking in review.

> **no-tokenizer path: shape is fixed for 653**

> the fallback returns concatenated text. there is no real span cut and no masking at all — the estimate is a length, not a label vector, and callers that ask it for labels get nothing meaningful back. that is the current state and 653 does not change it.
> 
> what was settled for 653: on the no-tokenizer path keep the `len // 4` count and the `<|role|>` text exactly as they are; an assistant span is the text length before and after that message, each `// 4`. so the span is derived from the two surrounding text lengths rather than from any tokenization, and the `<|role|>` markers stay verbatim in the concatenated output — downstream length accounting and a couple of the fixtures both key off t

> **still open**

> - whether the no-tokenizer fallback gets dropped or brought to parity. shreyas raised it on 653, no owner and no decision. not entirely sure it needs to be resolved before 653 lands — it is pre-existing behaviour either way — but it should not sit in a review thread indefinitely.
> - if it goes to parity, the question underneath is where a token count would come from for hosted models at all. nobody has costed that.
> - the fixtures for the fallback path are thin. two cases, both ascii.

> **review checklist for changes in here**

> for anything touching the formatter:
> 
> - did the labels change shape, or only their values? shape changes break the collator silently.
> - is the end-of-turn marker still inside the assistant span.
> - did the rendered text change at all on the fallback path, including whitespace.
> - multi-turn fixture, not just single-turn. most of the span bugs we have had only show up on the second assistant message.
> - system-message-only input, which is a legitimate input and used to raise.
> 
> none of these are new, i have just been checking them from memory during late night review passes and would rather they were written down.

> **Problems:** longer than one remark

#### `g9.r1.say24` — scope

**gideon**, 2025-06-26, page:engineering/local-offline-inference-what-the-encode-step-returns-when-no-tokenizer-is-loaded.md

> so basically on the mock path the ids are just range over the count, 0 through 8 for the Hello pair, and model_input is the first eight of those.

*What a reader should take from it:* the team agrees the no-tokenizer path's token ids are range over the count and model_input drops the last one

*Step it builds toward:* `g9.r1.sc-scope` — The branch that runs without a tokenizer keeps its existing text and its existing character-derived token count, but goes through the same cut and the same assistant-only masking as the real path, including returning a flat vector of ones when assistant-only is off.

*Drafted as:* so basically on the mock path the ids are just range over that count - 0 through 8 for the Hello pair - and model_input is the first eight of them.

*Why there:* None of the listed pages is anywhere near tokenization or the offline/local encoding path. They're about Docker image pinning, batch/cancellation bugs, release gates, structured output, and meeting status — the closest, the Jun 23 sync, mentions "local offline inference, same ownership" in one line and then drops it, so a comment there about token ids and model_input on the mock path would arrive from nowhere under a heading about batch mode deferrals. The remark is a settled reading of what the no-tokenizer path emits, which belongs in #pipeline, the room that owns offline/local model runs and token accounting. What should have existed: a short engineering page written up right after the Jun 23 sync flagged offline inference as moving — someone (Dario, who owns that work) writing down what the offline encode step returns when no tokenizer is loaded, using the two-row "Hello" example everyone was pasting, with gideon reading it back to confirm the ids and the model_input slice while the questions of weighting, how the count is derived, and what the encoding block reports stay open on the page.

*Still leaves open:* says nothing about which of those positions get weighted, how the count itself is arrived at, or what the encoding block reports.

*Must appear literally:* `model_input`

*A new page — **Local offline inference: what the encode step returns when no tokenizer is loaded** in `engineering`, 2025-06-26:*

> **Why im writing this down**

> At the Jun 23 sync we said local offline inference is moving, same ownership, and thats about all that got recorded. Fine for a sync note. But the part nobody wrote down anywhere is what the encode step actually gives you back when there is no tokenizer loaded.
> 
> So basically every couple of days somebody pastes the same two-row Hello output into #pipeline and asks what the numbers mean. Same two rows, every time. Honestly though thats on us for never writing it down, so here it is.
> 
> This page is only about the encode step on the offline path. Not about the batch stuff, not about v0.1.26.

> **The two paths through encode**

> Encode has two paths and which one you get depends on whether a tokenizer got loaded, nothing else.
> 
> - **Real tokenizer path** - a tokenizer is present, we call it, you get real vocab ids back. These are the ids you would expect from the model, they map to actual tokens, they are not sequential.
> - **Mock path** - no tokenizer was loaded (no model dir, or you are running the offline path in a test, or the load quietly didnt happen). Encode still returns something with the right shape so the rest of the pipeline keeps running. It does not fail.
> 
> The important thing is that the mock path is not an error state. It returns a well formed record and the downstream steps are happy with it.

> **The two-row Hello example, read out** **← carries the remark**

> This is the output people keep pasting. Its a pair of rows for the Hello prompt, run with no tokenizer.
> 
> So basically on the mock path the ids are just range over that count, 0 through 8 for the Hello pair, and `model_input` is the first eight of them. Thats the whole rule. There is no vocab lookup happening, the count comes from the record and the ids are generated off it, so row two looks like row one shifted only because the counts differ.
> 
> A couple of things that follow from that and are worth stating plainly:
> 
> - the ids carry no information about the text. Two completely different prompts with the same count give you identical ids.
> - `model_input` being one shorter than th

> **What not to read into a mock run**

> Since the output looks legitimate, people have been drawing conclusions from it that dont hold. tbh i have done this myself once.
> 
> - dont benchmark against it. Nothing tokenizer shaped is being executed, so the timings mean nothing.
> - dont file bugs about ids not being in vocab range. They are not vocab ids at all.
> - dont diff mock output against real tokenizer output and expect anything. The only thing thats comparable between the two is the shape.
> - if you are checking that the pipeline plumbing works end to end, mock output is fine and thats what its for.

> **Still open**

> Not settled as of today, just recording so it doesnt get lost:
> 
> - should the mock path log a warning when it kicks in? i lean yes, one line at startup, but it would be noisy in tests so i dunno. Nobody has decided.
> - who owns this file after v0.1.26 given the freeze. This is a behaviour question not a bug, so probably it just stays as is.
> 
> If someone asks in #pipeline again please link here instead of re-explaining it, and if the answer above turns out to be wrong somewhere, edit the page rather than correcting it in the thread.

### g9.r1.sc-fireworks — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*Nobody says:* a limit expressed in tokens becomes a limit on a file measured in bytes only by fixing a bytes-per-token figure and multiplying.

*5 remarks — 0 reporting the problem, 5 settling the design.*

#### `g9.r1.say26` — exclusions_or_crossover

**nikolai**, 2025-03-17, #code-review

> yep re-checked the accented row at max_seq_length=33 the budget lands at 99 and the line measures 100 so to_jsonl_lines gives back an empty list no trimmed verison

*What a reader should take from it:* the team agrees a line one byte over the budget is left out entirely, so a single over-budget example yields an empty list

*Step it builds toward:* `g9.r1.sc-fireworks` — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*Drafted as:* re-checked the accented row at max_seq_length=33 - budget's 99 bytes, the line is 100, so to_jsonl_lines gives back an empty list. no trimmed version, nothing.

*Why there:* None of the eight candidate conversations is anywhere near this. They're about docker image pinning and resume-ignoring-model (#cookbooks 04-16), PR queue hygiene and the container user arg (#code-review 05-06 and 05-30), SimpleStrat/RAFT shape (#cookbooks 04-03), agent response shape being a plain dict (#engineering 05-21), model-name lists disagreeing (#random 04-25), dormancy logistics (#general 06-02), and Claude 4.x identifiers in PR 704 (#code-review 2026-01-23). A byte-budget cutoff inside to_jsonl_lines on the finetuning export path answers nothing live in any of them and would land as a subject change with no reply. The right home is #engineering: that's where design arguments about subsystem behavior get settled, and Konrad's finetuning work plus Nikolai's client work were both live there in late May 2025. The sibling pieces — Emil on how the line gets serialized to measure 100 bytes, Konrad on the token-cap times bytes-per-token that yields 99 — sit with the same two people who were in the 05-21 thread, so this reads as the next day's continuation rather than a new topic.

*Still leaves open:* Where the 99 comes from (the token-cap times the bytes-per-token constant) and how the line is serialized to be measured at 100 bytes -- both sit with emil and konrad.

*Must appear literally:* `max_seq_length=33`, `to_jsonl_lines`, `99`, `100`

*A new conversation in #code-review on 2025-03-17:*

```
14:02  emil: did we ever get to the bottom of the accented rows coming back empty out of to_jsonl_lines
14:04  nikolai: yep re-checked one of them this morning  that run was max_seq_length=33
14:05  emil: and the budget off that
14:06  nikolai: lands at 99  its three times the seq length so 33 gets you there
14:08  emil: so if im reading you right the accented line comes in just past that
14:09  nikolai: the line measures 100  one over
14:11  konrad: and then? it hands back a shortened one, or nothing
14:12  nikolai: nothing  to_jsonl_lines gives back an empty list  theres no trimmed verison of the row anywhere
14:14  emil: yup thats the shape i was seeing in the counts, honestly couldnt tell if it was dropping or trimming
```

#### `g9.r1.l-fw-4` — exclusions_or_crossover

**konrad**, 2025-03-19, #engineering

> look, counting characters was the mistake - it's json.dumps(ensure_ascii=False) with default separators, then len(line.encode('utf-8')), so UTF-8 bytes. the 'qqq'/'ok' pair is 90, and the row landing exactly on the number was fine

*What a reader should take from it:* the team agrees the measurement is the encoded byte length and that landing exactly on the limit is acceptable

*Step it builds toward:* `g9.r1.sc-fireworks` — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*Drafted as:* counting characters was the mistake, 'héllo wörld' is two bigger once you encode it UTF-8. the row that landed exactly on the number was fine, by the way.

*Why there:* None of the eight candidates is chewing on serialization or an output size cap. They're all PR-status logistics (653/661/704/605/606), sandbox guarantees, dormancy planning, factory-cleanup ownership, and a post1 release announcement — a byte-vs-character measurement ruling would arrive from nowhere in every one of them and get no reply. The nearest thematic neighbour, 2025-05-06, is about the docker user arg, not about how a jsonl line is measured. The live thing this belongs to is the executor output cap: someone capping per-row output in the responses jsonl, a test row landing exactly on the limit, and a disagreement about whether the count is characters or encoded bytes. That's a design argument about code-execution's behaviour with no narrower room — #engineering is where nikolai (who owns code-execution's create-time behaviour) and dermot already argue this kind of thing out, and konrad is the one who'd have gone and actually measured the pair.

*Still leaves open:* does not say what the number it is measured against is built from, or what happens to a row over it

*Must appear literally:* `'qqq'/'ok'`, `90`, `UTF`, `json.dumps(ensure_ascii=False)`, `len(line.encode('utf-8'))`

*A new conversation in #engineering on 2025-03-19:*

```
14:03  gideon: my sanity check on the jsonl rows disagrees with what the code decides, every time. so basically i measured the line myself and got something smaller
14:05  dermot: if i'm reading that right you measured the string length? characters, not what actually goes out
14:06  gideon: ya, len of the line
14:08  konrad: look, counting characters was the mistake. it is len(line.encode('utf-8')) that we go on, so bytes
14:09  gideon: UTF-8 bytes of what though, the row as we built it or the serialized thing
14:11  konrad: the serialized one. json.dumps(ensure_ascii=False) with the default separators, and that line is what gets measured
14:12  gideon: ok that explains my gap. and the 'qqq'/'ok' pair, what does that land at
14:14  konrad: 90. and the row that came out exactly on the number was fine, that one was never the failure
14:16  dermot: mhm, that tracks with the two rows i pulled last night
```

> **Problems:** longer than one remark

#### `g9.r1.l-fw-1` — exclusions_or_crossover

**emil**, 2025-03-20, #cookbooks

> honestly i think the cap and the check are in different units - fireworks bounced the entire upload over one long sample, so to_jsonl_lines now works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN and measures each line against that budget in bytes.

*What a reader should take from it:* the team sees one long sample failing an entire upload, with the cap and the check in different units

*Step it builds toward:* `g9.r1.sc-fireworks` — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*Drafted as:* fireworks bounced the whole upload over one oversized sample. our cap is counted in tokens and the thing they measure is the file, in bytes.

*Why there:* No listed day is about the dataset-to-finetuning export path. The three #code-review days are review-queue and PR-ordering threads (PR 653 appears only as an unclaimed review, never discussed on its merits); #releases 2025-05-06 is notes logistics; #viewer 2025-03-27 is local-viewer removal; #engineering 2025-03-19 is throttle/cost-estimation on v0.1.21; #engineering 2025-06-03 touches finetuning only through the pricing-lookup cost guard, a different subsystem from upload payloads. #pipeline 2025-04-23 is the nearest in spirit but that room is the request layer and that day is fixed on cache fingerprints and the pending job record. The remark needs the room that owns the curated-dataset-into-fine-tuning handoff, which is #cookbooks.

*Still leaves open:* does not say what to do with an oversized line, nor how many bytes a token is worth

*Must appear literally:* `FIREWORKS_BYTES_PER_TOKEN`, `max_seq_length`, `to_jsonl_lines`

*A new conversation in #cookbooks on 2025-03-20:*

```
13:04  dario: what happened with the fireworks upload yesterday, it came back rejected whole?
13:06  emil: yup. one long sample and they bounced the entire upload over it, not just that record
13:08  dario: but our own check passed the file first? so either the check is wrong or their limit is not what we think it is
13:09  emil: honestly i think the cap and the check are just in different units
13:11  dermot: mhm. so if i'm reading that right the cap we have is in tokens and the thing we were comparing it against was never tokens
13:13  emil: right. so to_jsonl_lines works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN, and thats the budget every line gets measured against, in bytes
13:14  dermot: yeah ok. that would explain why nothing local ever fired on that file
```

> **Problems:** longer than one remark

#### `g9.r1.l-fw-2` — exclusions_or_crossover

**dario**, 2025-06-03, page:engineering/viewer-dataset-download-export-format-notes-pr-652.md

> honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact.

*What a reader should take from it:* the team agrees the jsonl path leaves lines out rather than shortening them

*Step it builds toward:* `g9.r1.sc-fireworks` — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*Drafted as:* i'd sooner ship one example fewer than a conversation with its opening sawn off, so nothing in the jsonl gets shortened, ever.

*Why there:* The remark settles a serialization policy — the jsonl export drops whole rows rather than truncating them, and anything under budget round-trips byte-identical including non-ASCII. None of the eight candidates has that thread. The pinning page is about Docker tags, the persistence page is about which store a restart reads, the release notes touch jsonl only as a correctness bugfix, and the four meeting pages are status/PR triage where a serialization decision would change the subject and draw no reply. It belongs against the viewer dataset download work (PR 652), which is exactly the path that writes a dataset out to jsonl and reads it back; a design page written while 652 was in review, with dario and emil on it, would already be arguing about oversize rows and encoding, and the sibling question of how the budget is computed sits naturally next to it unanswered.

*Still leaves open:* does not say how you decide which lines are too big to ship

*Must appear literally:* `héllo wörld`

*A new page — **viewer dataset download: export format notes (PR 652)** in `engineering`, 2025-06-03:*

> **why this page exists**

> PR 652 (feat: add support to download dataset from viewer) has been open since the start of may and finally got a reviewer this week, which is 33 days of nobody looking at it, so a fair amount of the behaviour in there was never written down anywhere.
> 
> i went through it properly on 2025-06-03. most of the diff is fine and does what the title says. two things came out of the review that arent really review comments so much as missing spec: what the download path does with an example that is too large for the row budget, and what happens to non-ascii content when a dataset goes out and comes back in. neither had an answer in the code or in the PR description.
> 
> this page is the answer t

> **what the download path actually does today**

> the shape of it, as merged-ish:
> 
> - the viewer holds the dataset as rows, the download endpoint walks them in order and writes one jsonl line per example
> - one example, one line, no wrapping envelope and no manifest alongside it. the file is the dataset
> - ordering is preserved. this matters more than it sounds like it does, because a couple of the curation recipes are positional and a reordered download is a silently wrong download
> - there is a per-row size budget applied at serialization time. the number itself lives in the config and i dont think it should be quoted here since it has already moved once
> 
> things the path does *not* do: no compression, no chunking across lines, n

> **rows over the size budget**

> the decision here is drop, not truncate. an example that exceeds the per-row budget is omitted from the download entirely and counted in the summary; it is never written out in a shortened form.
> 
> dario's reasoning on the review, recorded because it's the actual rationale and not just a preference: honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact.
> 
> the practical consequence is that a downloaded file is a subset of the dataset but every line in it is a faithful example. a truncated multi-turn conversation looks like a valid conversation to everything downstream, 

> **encoding on the round trip**

> utf-8 end to end, and no ascii escaping on the way out. the serializer writes the codepoints directly rather than \uXXXX sequences, so the file is readable and, more to the point, byte-identical content comes back when you load it.
> 
> checked on the review with a few of the multilingual rows in the curator-viewer test set — cjk, combining diacritics, and one row with emoji in the assistant turn. all round-tripped clean. to be honest i expected the combining-character row to be the one that broke and it didnt, so either python's json module is doing the right thing or we got lucky in a way i havent found yet.
> 
> the one caveat is that nothing normalizes unicode forms. if a row goes in as 

> **open items before this merges**

> - [ ] dropped-row count needs to be surfaced in the viewer ui, not just the response body. right now you have to go looking for it
> - [ ] the per-row budget should be documented wherever the viewer config is documented, since it's now load-bearing for correctness and not just a memory guard
> - [ ] no test covers the drop path. there's a test that a large row doesnt crash the serializer, which is not the same claim at all
> - [ ] issue 290 (ModuleNotFoundError: 'resource') is unrelated but touches the same module on import, worth checking they dont conflict once both land
> 
> nothing here is blocking in the sense of "this is wrong", its more that the behaviour is deliberate and currently u

#### `g9.r1.l-fw-3` — exclusions_or_crossover

**nikolai**, 2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>

> on 653 whats in encoding.py so far the role set FIREWORKS_BYTES_PER_TOKEN still 3 ExampleTooLongError off EncodingError and the encoding blocks tokenizer flag False when we ran without one

*What a reader should take from it:* the team fixes the bytes-per-token figure at 3 and puts it in the encoding module's public surface

*Step it builds toward:* `g9.r1.sc-fireworks` — The jsonl written for Fireworks cuts nothing; a line is either shipped whole or left out entirely, and it is left out when its encoded byte size is over a budget of three bytes for each token of the sequence limit, with a line landing exactly on the budget kept.

*Drafted as:* encoding.py so far: the role set, the error types, and FIREWORKS_BYTES_PER_TOKEN, which is 3 until somebody measures a real tokenizer. all of it imports from finetune.

*Why there:* Nikolai's own recap already puts PR 653 — the finetuning client he inherited from Shreyas — on the table with a blunt question: does it need to land or should it be closed. The one thing missing from that ask is what's actually in the branch, so an inventory of encoding.py is exactly what the thread is waiting on, and Nikolai is the person carrying it. It also fixes the bytes-per-token figure at 3 on the module's public surface without saying what it's multiplied against, which is the part the finetuning-side discussion still owes.

*Still leaves open:* does not say what the constant multiplies or what the resulting number is compared against

*Must appear literally:* `EncodingError`, `ExampleTooLongError`, `FIREWORKS_BYTES_PER_TOKEN`, `False`, `encoding.py`, `tokenizer`

*Goes as a reply into the real thread "Week of Jun 9 recap: bulk inference fix":*

```
Quick recap from last week. Dario's fix in bulk-llm-inference for multimodal Gemini batch request creation is the main thing worth knowing about — it's non-trivial and the two batch-related PRs (690 and 691) are close enough in scope that whoever reviews them will want to look at both at once.

One thing I want an answer on: PR 653, the finetuning client Shreyas originally opened, has been sitting with me. I've merged main in and there's still work to do. But if we're heading into maintenance mode after 0.1.26, does this PR actually need to land, or should it just be closed? Don't want to keep carrying it if the answer is abandon.
```

### g9.r1.sc-refuse — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Nobody says:* an example that fits under the limit was never cut, so there is nothing to refuse; the floor only bites on examples the cut actually reached.

*7 remarks — 0 reporting the problem, 7 settling the design.*

#### `g9.r1.say20` — failure_behavior

**emil**, 2025-03-14, #code-review

> one more on the error shape - EncodingError subclasses ValueError, so anything already catching ValueError around the encoder still catches it. keeping it that way.

*What a reader should take from it:* the team agrees EncodingError derives from the builtin ValueError

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* one more on the error shape — EncodingError extends ValueError, so anything catching ValueError round the encoder still catches it. keeping it that way.

*Why there:* None of the eight candidates is anywhere near this subject. The two #code-review days are pure PR-queue triage (683/681/653/675), #engineering 2025-03-14 is semaphore gating and OOM, #engineering 2025-04-18 and #viewer are cache keys and log noise, #pipeline 2025-03-31 is Mistral auth and rate-limit headers, #cookbooks 2026-01-02 is CI wiring for code-execution verifiers. The nearest thematic neighbour is #general 2025-04-29 (raise vs warn on the structured-output override key), but that thread is about a docker-backend config key and a fallback-vs-abort argument — dropping an exception-hierarchy decision about the encoder in there changes the subject and lands on a day where nikolai is already the one steering error behaviour. This remark answers "what does the encoder raise and do callers need new except clauses", which needs a thread where the example-encoding path is actually being designed. That belongs in #engineering, the room for design arguments that haven't found a narrower channel, alongside nikolai's inventory of encoding.py that supplies ExampleTooLongError.

*Still leaves open:* Doesn't say ExampleTooLongError is itself an EncodingError — that comes from nikolai's inventory of encoding.py — nor what the refusal reports or when it fires.

*Must appear literally:* `EncodingError`, `ValueError`

*A new conversation in #code-review on 2025-03-14:*

```
13:43  gideon: quick thing on the encoder before i forget - it raises its own error type now right? does that break people catching around it
13:45  emil: shouldnt. EncodingError isnt a fresh branch off on its own, it sits under ValueError
13:46  gideon: hm ok but the existing call sites catch ValueError, not the new name. so what happens there
13:47  dario: thats the bit i wasnt sure about either honestly
13:49  emil: thats the whole reason for the shape - anything already catching ValueError around the encoder still catches it. no edits at those sites
13:50  emil: and we're keeping it that way, i dont want somebody making it standalone in six months and quietly breaking every handler. still needs writing, but thats the shape it gets written to
13:52  gideon: ya ok. i had half a rewrite of those try/excepts in my head, binning that
```

> **Problems:** contains its own forbidden term 'subclass'

#### `g9.r1.l-fail-4` — failure_behavior

**dermot**, 2025-03-17, #pipeline

> yeah, that's my read as well — one row we won't take shouldn't take the other forty thousand down with it, and anything that fits under the cap goes through however short its question is.

*What a reader should take from it:* the team agrees a batch skips a refused example and keeps the rest, and that examples that were never cut are never refused

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* one row we won't take shouldn't take the other forty thousand down with it. and anything that fits under the cap goes through, however short its question.

*Why there:* The remark settles two things about per-row behaviour under a payload/length cap in a batch submission: a refused row is skipped rather than failing the submission, and a row that was never truncated is never refused. None of the candidate threads is chewing on caps, truncation, or row-level refusal. The two #pipeline days are about validating provider backend changes on the batch submission path (04-09) and streaming vs. auto batch routing and cache behaviour (06-26); #cookbooks 04-16 is docker image pinning and resume locking the model; both #code-review days are PR logistics (container user arg, viewer download partial writes); #engineering 04-02 is batch cancellation and release readiness; 03-17 is the capability table keys. The nearest thematic neighbour is #help 03-26 (fail-open vs fail-closed on unknown capability), but that is a whole-run capability gate, not a per-row skip inside a 40k batch, and dropping this there would answer a question nobody asked. It belongs in #pipeline, which owns async batch submissions and what happens to a request the backend won't take — but in a thread about the cap, which doesn't exist yet.

*Still leaves open:* does not say how short the surviving question can get before a row is refused

*A new conversation in #pipeline on 2025-03-17:*

```
13:36  dario: nightly came back empty. one row over the cap and the whole submission got rejected
13:38  emil: yup, chased that this morning. one row we wont take shouldnt take the other forty thousand down with it
13:41  dario: so skip that one and send the rest. writer is all or nothing today, nothing in it survives a bad row
13:44  emil: right. it just gives up
13:46  dario: and the other end — we still bounce the very short prompts before the cap ever comes into it. keeping that or dropping it
13:49  dermot: yeah, thats my read as well. no floor worth defending — anything that fits under the cap goes through however short its question is
13:51  dario: mhm. the tiny ones are mostly retry stubs anyway
```

> **Problems:** longer than one remark

#### `g9.r1.l-fail-2` — failure_behavior

**konrad**, 2025-03-19, #releases

> look, on the stability item - nightly died on ExampleTooLongError, 129 tokens agianst a cap of 40 and not one prompt token left standing

*What a reader should take from it:* the team has a dedicated error for an example the cut leaves unusable

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* nightly died on ExampleTooLongError, 129 tokens against a cap of 40 and not one prompt token left standing.

*Why there:* Dermot has just quoted the weekly-notes line for v0.1.21 ("confirm contents and stability") and asked Emil whether CI passing on the two fixes closes that item. Konrad has been the one pressing all morning on what is and isn't in the cut, so him coming back with a nightly failure is exactly the counterweight to "CI came through clean" — and the release already contains the token count wrap fix on long responses, so a length/cap failure is in scope for that item rather than arriving from nowhere. It tells the room a dedicated ExampleTooLongError exists without saying how much surviving prompt would be acceptable or whether one bad row should sink the whole run, which is the open question Dermot's "is there more expected" invites.

*Still leaves open:* does not say how much surviving prompt would have been enough, nor whether one bad row should take the run with it

*Must appear literally:* `ExampleTooLongError`

*Goes into the real conversation in #releases on 2025-03-19, after 11:49 dermot:*

```
09:00  dermot: v0.1.21 release notes are up on the wiki
09:00  dermot: two fixes covered: the gemini unicode corruption in batch output and the token count wrap on long responses
09:12  konrad: Before we push the announcement, are PR 581 and 583 making it into this release or are we just cutting now and those slip to next?
09:34  dermot: announcement is out.
09:34  dermot: PR 581 and 583 are still open so they slip to next, I've cut with just the two bugfixes
10:09  konrad: The notes don't call out that 581 and 583 are coming next, or is it just the two fixes and nothing else?
10:50  dermot: I'm not sure the release notes are the right place for that, they document what's in, not what missed the cut.
11:33  emil: CI came through clean on both fixes
11:33  emil: PR 581 and 583 are queued and should be first in line for the next cut
11:48  dermot: I pulled up the weekly notes earlier, the v0.1.21 section just flags "confirm contents and stability", nothing more
11:49  dermot: @Emil, is CI passing on both fixes enough to close that item, or is there more expected?   <-- THE REMARK GOES HERE
```

#### `g9.r1.l-fail-3` — failure_behavior

**nils**, 2025-03-19, #pipeline

> let me think — the refusal line reads exactly: example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16. num_messages rides along as an attribute, it isn't printed.

*What a reader should take from it:* the team sets the floor at sixteen surviving prompt tokens and records the counts on refusal

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* refusal lines print the token count, the cap, how much prompt survived and num_messages. sixteen surviving tokens is about the least that still reads as a question.

*Why there:* Neither candidate is chewing on sequence-length truncation. The 2025-03-17 #pipeline day is about the *shape* of Mistral batch usage dicts (prompt_tokens/completion_tokens/total_tokens) feeding cost accounting — token counting for billing, not a tokenizer refusing an over-long example against max_seq_length; dropping a truncation error message there would change the subject mid-block and leave PR 584's blocker untouched. The 2025-03-24 #code-review day is pure review logistics (who has 583, who has 584, CI green), and nobody there is discussing error text. The remark is about the offline/local tokenization path deciding when an example can't be cut down far enough, which is #pipeline's territory (offline/local model runs, token accounting) — it just needs a day where that path is actually under discussion. Invented as a #pipeline thread where a long multi-turn example gets truncated to nothing in an offline run and Nils, who owns the guard, reports the exact wording; Emil is the natural other voice since he keeps asking what shape counts arrive in, and Dario asks the follow-up about what a refusal does to the run, which is where the sibling remark lands.

*Still leaves open:* does not say whether a refusal stops the run or whether uncut examples are subject to it

*Must appear literally:* `example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16`, `max_seq_length`, `num_messages`, `retained_prompt_tokens`, `token_count`

*A new conversation in #pipeline on 2025-03-19:*

```
14:03  gideon: quick one before i forget. when an example is too long to fit, what does the refusal actually say? my logs just show a skip and a number
14:05  nils: it puts the example's token_count next to the max_seq_length it went past. those two are in there for certain
14:06  gideon: ya but thats the part i already have. what i want is how much of the prompt would still be left, otherwise i cant tell if reshaping the example is worth it or i just drop it
14:10  nils: fair enough. let me think — the refusal line reads exactly: example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16
14:12  dermot: so if i'm reading that right, the text says nothing about how many messages the example had
14:13  nils: correct. num_messages rides along as an attribute, it isn't printed.
14:15  dermot: yeah ok. that said none of this is on a branch yet is it, i went looking earlier
14:16  nils: not yet, someone still has to write it. maybe it goes on the batch ticket, i don't much mind which
14:17  gideon: so my alert is matching the old wording then. explains the silence
```

> **Problems:** longer than one remark

#### `g9.r1.l-fail-1` — failure_behavior

**gideon**, 2025-03-24, #cookbooks

> so basically the rows that get cut hardest arive as an answer with none of its question left in front of it, and we happily train on those.

*What a reader should take from it:* the team sees examples kept whose prompt did not survive the cut

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* the rows that get cut hardest arrive as an answer with none of its question left in front of it, and we happily train on those.

*Why there:* None of the candidate threads is about dataset curation or the fine-tuning handoff. #code-review 05-06, 03-17, 03-27, 04-01 and 04-16 are PR-triage days (container user arg, auth flow, gemini parts key, response-path overlap); #random 04-25 is the duplicate model-name lists; #incidents 04-11 is the post1 announcement; #pipeline 04-29 is the scope of Nikolai's stdout removal and whether the structured output override is provider-agnostic — all request-layer, none of them about what a length cut does to rows we then train on. The remark is about the curated corpus losing prompts to that cut while the examples still go into the fine-tune, which is #cookbooks' beat (the reasoning-dataset pipelines and the handoff from a curated dataset into fine-tuning). Dropped into any of the listed days it changes the subject and nobody present could answer it.

*Still leaves open:* does not say where the line is drawn or what should happen to such a row

*A new conversation in #cookbooks on 2025-03-24:*

```
15:11  emil: pulled a handful of rows out of the export and a few of them just start mid answer. not entirely sure if thats us or the viewer
15:13  gideon: its us. the rows that get cut hardest are the ones youre looking at
15:14  emil: cut hardest as in the longest ones. and the cut eats forward from the front of the row, i take it
15:16  gideon: ya. so basically what arives is an answer with none of its question left in front of it
15:17  konrad: and something drops those before training, presumably
15:18  gideon: thats the thing, no. we happily train on those
15:19  gideon: honestly though thats not defensible. no question left, the row doesnt go in. i dunno which ticket it lands on but thats what were doing
15:20  konrad: mhm. i had been putting those down to the preview rendering badly
```

#### `g9.r1.say22` — failure_behavior

**gideon**, 2025-04-03, #cookbooks

> so basically even after a skip i can still tell what came back — every datum's metadata block carries num_messages, and the four-message row was sitting right there

*What a reader should take from it:* the team agrees each returned datum's metadata block carries num_messages

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* so basically after a skip i can still tell what came back — every datum's metadata block carries num_messages, and the four-message row was sitting right there.

*Why there:* None of the listed rooms is chewing on skipped/refused examples or on the shape of what a generation run hands back per row. The closest by vocabulary is #viewer 2025-04-28, but that thread's "metadata panel" is the executor report object and the whole live question there is the *inspected directory* field — a remark about per-datum num_messages after a refusal skip would change the subject and get no reaction, and it would also collide with Dario's settled point that the panel only shows what the executor reports. #code-review 2025-04-04/04-08 are PR-state triage, #engineering 2025-04-16 is cost-streaming skew, #help 2025-03-26 and #code-review 2025-03-14 are the capability/schema_check hard-block. The remark belongs where someone is actually reading the output rows of a reasoning-dataset run: #cookbooks, where the published pipelines and their per-row contents live, and where a skip in the middle of a run is a normal thing to have to account for.

*Still leaves open:* Doesn't say which examples get skipped, why, or what the refusal itself reports.

*Must appear literally:* `num_messages`

*A new conversation in #cookbooks on 2025-04-03:*

```
11:31  konrad: the run skipped a chunk of rows this morning and now i cant tell what actually came back for each one
11:32  konrad: do i have to re-run the whole thing to find out, off the top of my head there is nothing in the output
11:35  gideon: no, um, you dont need to re-run. every datum carries its own metadata block and num_messages is in there
11:36  konrad: right but does that survive a skip. thats the part im not sure about
11:38  gideon: ya it does, so basically even after a skip i can still tell what came back — i opened your file and the four message row was sitting right there
11:41  emil: so if i'm reading that right, the count is per datum, not something the run has to report back to us
11:41  konrad: mhm. so the check reads num_messages off the block then, no log parsing. nobody has written that yet
11:43  gideon: exactly. honestly though i lost the morning re-running for a number that was already sitting in the file
```

#### `g9.r1.say21` — failure_behavior

**dermot**, 2025-06-12, page:engineering/what-the-finetuning-encoder-emits-per-datum-and-how-it-behaves-at-the-length-cap.md

> yeah ok — at max_seq_length=40 the four-message near-miss does come back a datum: encoding reads window_start 51, and the weights come back 39 long, one short of the max_seq_length window we keep.

*What a reader should take from it:* the team agrees the surviving near-miss datum's encoding reports window_start 51

*Step it builds toward:* `g9.r1.sc-refuse` — An example is refused with its own error type when the cut leaves fewer than sixteen tokens of prompt in front of the final assistant turn, and refusing one example does not stop the rest of the batch from being produced.

*Drafted as:* on the four-message near-miss at max_seq_length=40: it comes back a datum, and its encoding reads window_start 51, so we trimmed it and kept it anyway.

*Why there:* Every listed page sits in a different subsystem — batch metadata db vs responses file, provider cost/usage normalization, supports_structured_output(), CI gating and release cuts, PR-age weeklies. None of them has anything above it about encoding examples into token windows, so a line about max_seq_length, window_start and a short weights array would arrive from nowhere and get no reaction. The remark's sibling ("rev1 and konrad's line", the retained prompt count and the floor) implies a working doc that goes through revisions with konrad commenting, which is what should have existed: an engineering page where the example encoder's window boundaries get pinned down after a fine-tuning handoff dropped pairs sitting right at the cap. dermot is the right voice for it — he already writes the "recording this while I have the code open" documents — but it needed its own page, not a comment bolted onto the release-engineering or batch-persistence one.

*Still leaves open:* Doesn't give the retained prompt count, the floor, or what happens to the same pair at a smaller cap — that's rev1 and konrad's line.

*Must appear literally:* `max_seq_length`, `max_seq_length=40`, `window_start`

*A new page — **what the finetuning encoder emits per datum, and how it behaves at the length cap** in `engineering`, 2025-06-12:*

> **why this page exists**

> last week's handoff to the finetuning client came back short. not by much — order of a few hundred prompt/completion pairs out of the run — but the pairs that went missing were not random, they were all sitting right at the length cap. we spent a late night on it and the loss turned out to be downstream of the encoder rather than in it, which is the part nobody had written down anywhere.
> 
> so this is the write-up of what the encoder actually hands back for a single datum, and what that looks like when a conversation lands on or near the cap. it is descriptive, not a proposal. i'd like it to exist before anyone touches `max_seq_length` for the next run, because the behaviour at the boundar

> **what the encoder emits per datum**

> one datum in, one dict out. the fields that matter for anything downstream:
> 
> - `input_ids` — the token ids for the window that was kept, not for the full conversation
> - `weights` — the per-token loss mask, 0 on prompt tokens and 1 on completion tokens. same alignment as `input_ids`
> - `window_start` — the offset into the *full* token stream where the kept window begins. 0 when nothing was dropped
> - `n_tokens_total` — length of the full stream before windowing
> 
> two things follow from that which are easy to miss. first, the encoder does not drop over-length conversations, it windows them: it keeps the tail and records where the tail started. second, `weights` is built against the 

> **at the cap: a four-message example**

> the case that started this. a four-message conversation, encoded at `max_seq_length=40`, sits just past the boundary and is the near-miss worth having on the page.
> 
> yeah, the four-message near-miss at max_seq_length=40 does come back a datum — encoding reads window_start 51, and the weights come back 39 long, one short of the window we keep.
> 
> so it is a valid datum by the encoder's own contract, and it is one token shorter than an assertion on `max_seq_length` would expect. the short window is a consequence of where the message boundary fell relative to the tail, not of anything being truncated twice. if i had to guess it is the common shape at the boundary rather than a one-off, but

> **what the handoff was doing with it**

> the collate step on the finetuning side asserted `len(weights) == max_seq_length` and skipped the datum on mismatch, silently. that assertion holds for every datum that was windowed cleanly and for every datum well under the cap, which is why this never surfaced in the smaller test runs — you need conversations landing in the boundary band to see it at all.
> 
> the skip was silent, so the run reported a batch count and not a drop count. that is the reason the shortfall took a night to localise: nothing in either log said anything had been discarded.

> **before anyone changes the cap**

> raising or lowering `max_seq_length` moves which conversations land in the boundary band, so it changes the population of short-window data rather than eliminating it. worth doing before the change, in order:
> 
> - count how many encoded datums come back with a window shorter than the cap, and log it. a count is enough, we do not need the datums themselves
> - confirm whatever consumes the encoder output pads rather than asserts on exact length
> - diff the datum count in against the datum count out of the handoff, and fail loud on a mismatch
> 
> not entirely sure yet whether padding at the encoder or at the collate step is the right place for the fix — both are defensible and i have not w

> **open**

> - [ ] short-window count logged at encode time — unowned
> - [ ] silent skip in the collate step, needs to be loud at minimum
> - [ ] decide where padding lives, encoder or collate. not scheduled
> - [ ] re-run the lost pairs from last week's handoff once one of the above lands

> **Problems:** longer than one remark

### Herrings — believed at the time, overturned later

#### `g9.r1.h1` — herring

**dario**, 2025-01-21, #code-review

> settled the windowing question: if window_start > 0 at all, to_tinker_datum raises ExampleTooLongError. an example we had to cut isn't really an example anymore, it's an artifact

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled on the windowing floor: if window_start > 0 at all, to_tinker_datum raises ExampleTooLongError. an example we had to cut isn't an example, it's an artifact.

*Why there:* Subject-wise this belongs to the curated-dataset → fine-tuning handoff, which is #cookbooks' stated territory, but none of the listed threads is chewing on example length, truncation or the conversion layer. The 2025-03-10 #cookbooks thread is about PR 571's schema shape and where the finetuning example should start; dario appears there once, about onboarding mail. Dropping a settled decision about to_tinker_datum and ExampleTooLongError into it changes the subject and answers a question nobody in that room had asked — "settled the windowing question" only reads as natural if the windowing question was actually open somewhere first. The other candidates are cache stats, cost maps, PR ordering and throughput, all further away. What should exist is a short #cookbooks thread a couple of days after the PR 571 discussion, once the handoff path in the finetuning example starts meeting examples longer than the target model's context: emil or konrad asking whether to_tinker_datum should window them down or refuse them, dario weighing truncate-and-keep against drop-and-log, and landing on the strict version.

*A new conversation in #code-review on 2025-01-21:*

```
14:03  nikolai: what is to_tinker_datum supposed to do when window_start comes back nonzero
14:06  konrad: it raises. ExampleTooLongError
14:07  nikolai: even if its off by a token or two
14:09  konrad: presumably yes but off the top of my head i am not entirely sure if we said any nonzero or there is some slack
14:16  dario: any nonzero. if window_start > 0 at all it raises, no slack — honestly an example we had to cut isnt really an example anymore, its an artifact
14:16  nikolai: right thats gonna take out a chunk of the long ones
14:18  konrad: mhm. i had it the other way round in my head, that it would just hand back the shortened one. good that i asked before writing it
```

#### `g9.r1.h2` — herring

**konrad**, 2025-01-22, #code-review

> Right, refusal is binary, windowed at all means refused, format_batch just skips that example and carrys on. An example we never cut still shows window_start 0 in its encoding.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Confirming for the review: the refusal is binary. Windowed at all means refused, format_batch skips it and carries on with the rest.

*Why there:* None of the candidate rooms is chewing on batch payload construction or long-prompt windowing. The two #code-review days closest in subject (Jan 27's PR 403 batch processor, Feb 5's PR 443 generation_params) are about parameter passing and cost-map validation, not about what `format_batch` does with an example whose encoding had to be windowed; the rest are review scheduling, viewer cost model, RAFT cookbook API, onboarding. Dropped into any of them this changes the subject and draws no reaction. What the batch submission path skips before a payload goes out, and what the encoding carries, is squarely #pipeline's remit (async batch submissions, token accounting), and konrad already owns batch-processor questions.

*Must appear literally:* `format_batch`, `window_start`

*A new conversation in #code-review on 2025-01-22:*

```
15:04  emil: quick one on the refusal flag - if we only windowed part of an example, is that a partial refusal or does it count as the whole thing
15:06  konrad: the whole thing. its binary, windowed at all means refused. there is no half state
15:08  emil: ok. so what happens to it downstream, does it still go out with some marker on it
15:10  konrad: no. format_batch just skips that example and carrys on

nobody has written that yet though, off the top of my head its two lines
15:13  dermot: so if i'm restating that right, the examples we never cut still carry the window fields anyway
15:15  konrad: mhm. one we never cut still shows window_start 0 in its encoding, thats just the default sitting there
```

#### `g9.r1.rev1` — failure_behavior

**dario**, 2025-04-24, #engineering

> dropped the windowing floor — window_start > 0 on its own refuses nothing now, it was binning fine long conversations. to_tinker_datum raises ExampleTooLongError only if the final assistant span starts under 16 tokens past window_start

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the windowing floor is gone — window_start > 0 on its own no longer refuses anything, it was binning perfectly good long conversations. to_tinker_datum raises ExampleTooLongError only when the final assistant span starts less than 16 tokens past window_start.

*Why there:* Nothing in the listed rooms is about training-data conversion or conversation windowing. The closest by domain is #engineering 2025-04-29, but that thread is nikolai's num_gpus scope, the structured-output override, and stdout removal from the code-execution path — dario is there asking clarifying questions about nikolai's commits, not announcing a settled change to a tokenization floor. Dropping "the windowing floor is gone" in would change the subject and draw no reaction; ExampleTooLongError, to_tinker_datum and window_start appear nowhere in any of these conversations, so the term arrives cold. The other candidates are cache fingerprinting, Mistral batch usage extraction, the capability table, and PR triage — all further away. What should have existed is a short #engineering thread with dario and nikolai on the finetuning side, prompted by someone noticing a chunk of long conversations silently missing from a converted dataset: nikolai asking how many examples got dropped and on what basis, dario tracing it to the length check in to_tinker_datum, and this line landing as the decision about what the refusal condition now is.

*Must appear literally:* `window_start`, `to_tinker_datum`, `ExampleTooLongError`, `16`

*A new conversation in #engineering on 2025-04-24:*

```
14:06  emil: quick one on to_tinker_datum — are we still refusing anything where window_start came back above zero?
14:08  dermot: that was the call yes. any nonzero window_start and it raises ExampleTooLongError. the reasoning being that an example we had to cut isnt really an example anymore, its an artifact
14:09  emil: i remember the framing. it isnt holding up though, the bin i pulled is mostly long support threads that were completely fine
14:13  dario: mhm we dropped that one. window_start > 0 on its own refuses nothing now, honestly it was just binning good long conversations
14:16  dermot: so what trips it instead. if i had to guess something about how much of the tail survives the cut
14:18  dario: close. to_tinker_datum still raises ExampleTooLongError but its keyed on where the final assistant span starts relative to window_start. if theres near nothing of the answer left past the cut, refuse. otherwise its just a long chat and we keep it
14:19  dermot: near nothing being defined how
14:20  dario: if it starts under 16 tokens past window_start
14:23  emil: yup, that reads better. i can stop subtracting that bin out of my totals then, been doing it since febuary
```

> **Problems:** longer than one remark

#### `g9.r1.rev2` — failure_behavior

**konrad**, 2025-04-15, #engineering

> look, we stopped refusing on windowed-at-all, it was droping legit long chats. now it's ExampleTooLongError only under 16 retained prompt tokens, format_batch still skips and carries on.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* look, the refusal isn't binary anymore — we stopped refusing on windowed-at-all, it was dropping legit long chats. now it's ExampleTooLongError only if fewer than 16 prompt tokens survive the cut; format_batch still skips and carries on.

*Why there:* None of the eight rooms is chewing on token windowing, truncation, or the batch formatting path. The two #code-review days closest in kind are about PR triage and merge/defer calls (PR 604's prompt()/parse() input shape mismatch is the nearest neighbour and still a different subsystem), 2025-06-06 is the multiturn stopping criterion refactor, and the rest are release notes, docker user args, cookbook freshness, and CI wiring. Dropping a settled decision about ExampleTooLongError and a 16-token floor into any of them changes the subject and would draw no reply — nobody in those rooms has asked anything it answers. What's missing is the thread where the over-eager refusal got reported and Konrad reported back what the new rule is: someone hitting legitimate long multi-turn chats being refused outright, Dario confirming it on the online request path, and Konrad landing the windowed-vs-refused distinction plus what format_batch does with a refused example. That belongs in #engineering in the weeks after the v0.1.22 cut, not retrofitted into a PR-status standup.

*Must appear literally:* `ExampleTooLongError`, `16`, `format_batch`

*A new conversation in #engineering on 2025-04-15:*

```
15:02  nikolai: konrad whats the refusal rule on length now

a run today kept two chats i was sure we would drop
15:04  konrad: right, that one is gone. it was binary before — windowed at all meant refused, and format_batch just skips that example and carrys on. we were droping legit long chats that way
15:08  emil: so if i'm reading that right nothing refuses on length at all anymore? that doesn't sound like what we'd want
15:10  konrad: no, ExampleTooLongError still fires. just only under 16 retained prompt tokens now
15:13  nikolai: and when it does fire what happens downstream
15:15  konrad: same as it was, format_batch skips it and carrys on. that part nobody touched
15:19  emil: yup ok. i was going to count how many we lost under the old rule by grepping encodings for window_start, but every example comes back 0 there, even ones we never cut
```


## g9.r2

**The hidden requirement:**

- **rule** — encoding.py defines a frozen dataclass EncodingReport with exactly the fields kept: int = 0, dropped: int = 0, windowed: int = 0, dropped_indices: Tuple[int, ...] = (), supervised_tokens: int = 0 (that spelling, that order, those defaults), exported from finetune/__init__.py. Both format_batch and FireworksDataFormatter.to_jsonl_lines reassign self.last_report while still returning a plain list. dropped_indices is the ascending tuple of INPUT positions that were dropped; windowed counts only kept examples whose window_start > 0; supervised_tokens sums the supervised token counts of kept examples only, and is 0 on the Fireworks path along with windowed. Observable: FireworksDataFormatter(max_seq_length=30).to_jsonl_lines([a, b]) leaves last_report == EncodingReport(kept=1, dropped=1, windowed=0, dropped_indices=(1,), supervised_tokens=0) by dataclass equality.
- **scope** — to_tinker_datum never touches self.last_report — neither on success nor when it raises — and a freshly constructed DataFormatter(max_seq_length=40) has last_report == EncodingReport(kept=0, dropped=0, windowed=0, dropped_indices=(), supervised_tokens=0).
- **failure_behavior** — format_batch absorbs only the over-long refusal. InvalidRoleSequenceError and TokenizerCapabilityError propagate out of format_batch and abort the pass — they are neither caught nor counted as drops — and self.last_report still holds the value it had before the aborted call.

**Reversed earlier:** format_batch first returned a (data, report) tuple; that was reversed when it broke the direct forwarding at tinker_trainer.py:250, and the report moved onto the formatter instance.

**What a reader has to infer along the way:**

- *The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.*
  - nobody says: a number people paste into tickets and assert on in tests has to be fixed once written and comparable as a whole object.
- *The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.*
  - nobody says: if callers ask the object itself for the last batch's summary, only calls that actually process a batch have any business changing what it says.
- *dropped_indices holds the positions the dropped examples occupied in the list the caller passed in, in that order.*
  - nobody says: a position is only useful to the person holding the input if it is numbered against the input they handed over.
- *windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.*
  - nobody says: a count about tokens or about trimming can only describe work that really happened on rows that really shipped.
- *Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.*
  - nobody says: an error that says the caller's data or setup is wrong is not a row you can skip on their behalf and keep going.

**Names the tests reach for that the ticket withholds:**

- said: `EncodingReport`, `dropped`, `dropped_indices`, `kept`, `self.last_report`, `windowed`

> **5 of 25 graded assertions are not stated outright** — 2 absent, 3 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g9.r2.sc1 — The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.

*Nobody says:* a number people paste into tickets and assert on in tests has to be fixed once written and comparable as a whole object.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g9.r2.l3` — rule

**emil**, 2025-04-17, thread:new|g9.r2.l3

> yeah, a cleanup bumped a counter on last night's report after the run finished, so the figure i pasted in the ticket was wrong. agreed, reports are frozen once built.

*What a reader should take from it:* the team agrees the report cannot be modified after it is built

*Step it builds toward:* `g9.r2.sc1` — The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.

*Drafted as:* someone's cleanup incremented a counter on last night's report after the run had finished, so the number i pasted into the ticket was wrong. that should not be possible.

*Why there:* None of the eight candidates is chewing on run-report immutability. Six are release announcements or weekly status mails — one-way broadcasts where a reply reporting a mutated counter on last night's report would arrive from nowhere — and the concurrency/OOM thread with dermot is about semaphores under concurrent row creation, not report objects. The v0.1.21 mail mentions "cost accounting to report wrong numbers", but that's a token-wrapping bug in a shipped release, not a design decision about whether a built report can still be written to; landing this there would read as vocabulary matching. The remark is a reply inside a live design argument about a run report and its counters (the sibling supplies the counter names, defaults, and which calls may emit one), which is request-layer work — the report is assembled from the run's request accounting and then a cleanup path incremented it afterwards. That belongs in #pipeline, in the WS-054 cost-accounting window where Emil is already carrying PR 643 (response object in curator), and Emil is exactly the person to bring the concrete burn: he pasted a number into a ticket and it was wrong by the time anyone read it.

*Still leaves open:* what the counters are called, what they default to, and which calls are allowed to produce one

*A new thread — **Re: PR 643 review notes — cost fields on the response object**, 2025-04-17:*

```
From: nikolai  To: emil, dermot, gideon
went through PR 643 this morning before standup so notes while theyre fresh

the cost fields on the response object are assembled in two places right now one in the constructor and one later when the tracker flushes i'd say pick one. off the top of my head the constructor is the only place that has everything it needs

also the totals field is typed float but the token counts feeding it are ints coming back from the provider payload. probably fine but somebody should say so on purpose rather tha

From: dermot  To: emil, nikolai, gideon
mhm, agree on collapsing to one assembly point.

one thing to add from the reporting side, since it lands on the same object: the per-run report we render for finance reads these fields directly, and it reads them whenever the ticket gets opened, not when the run ends. so whatever shape we settle on has to survive being read hours later.

if i had to guess that is fine today because nothing rewrites the object. but nothing stops it either, which is a different statement.

From: emil  To: dermot, nikolai, gideon
Let me think through that, because i think dermot's point and nikolai's first point are actually the same point wearing two hats.

On assembly: yup, constructor. i had it split because the tracker flush was where the retry counts arrived, but i've since moved retry accounting earlier so the constructor genuinely has everything now. Will fold it in PR 643 today. On float vs int — i believe we want the counts to stay int all the way through and only widen at the final currency multiply, i'll write

From: gideon  To: emil, dermot, nikolai
ya the frozen version, try it. tbh if it gets loud that is information too, means somebody somewhere is writing to it and we want to know who.

so basically i can take the finance render side once you land, it is like twenty lines and i already have that file open for something else

```

#### `g9.r2.l4` — rule

**nikolai**, 2025-04-18, #engineering

> spelling out all five counts in every assert makes these unreadable i'd say make EncodingReport a dataclass with defaults so EncodingReport() is empty and two of them compare with ==

*What a reader should take from it:* the team agrees every field has an empty default and two reports compare by value

*Step it builds toward:* `g9.r2.sc1` — The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.

*Drafted as:* spelling out all five counts in every assertion makes the tests unreadable. i want EncodingReport() to come out empty and compare equal with ==.

*Why there:* None of the eight candidates is chewing on encoding results or a report object at all. The two #code-review threads (05-08, 06-16) are queue management — who reviews PR 653/654/690, what's blocking a release — not line-level feedback on anyone's diff, so a design note about a report type's fields and equality would arrive from nowhere and get no reaction. The nearest topical neighbour is the 05-21 response-shape argument, but there Nikolai is arguing against wrapping row output in anything heavier than a plain dict, so having him propose a dataclass in that same thread reads as him contradicting himself, and it's about the agent response, not encoding counts. The 06-13 Pydantic/Arrow thread is about whether the fix touches Dario's services, not about a new type's shape. This is review feedback on a specific PR's tests, which is exactly what #code-review is for — it just needs the PR that introduces EncodingReport to be on the table, which no existing thread puts there.

*Still leaves open:* what the five counts are called, what each one counts, and where a filled-in one comes from

*Must appear literally:* `==`, `EncodingReport`

*A new conversation in #engineering on 2025-04-18:*

```
15:21  gideon: the encoding tests are killing me, every assert spells out all five counts even when four of them are zero. honestly though it's unreadable
15:23  nikolai: yep i'd say make EncodingReport a dataclass with defualts
15:24  gideon: ok but i still have to name all five in the assert, no? um that's the part that's noisy
15:25  dario: i think thats the bit gideon is stuck on, defaults on the constructor dont do anything for the assert side
15:27  nikolai: you stop naming them EncodingReport() is empty on its own so thats what the no-op cases go against and two of them compare with ==
15:28  gideon: ahh ya. one line each then
15:29  dario: mhm. keeping the name as is i assume
15:30  nikolai: yep no reason to rename it
```

#### `g9.r2.l1` — rule

**dario**, 2025-05-13, thread:new|g9.r2.l1

> the surface is small, honestly: encoding.py is ALLOWED_ROLES, InvalidRoleSequenceError, TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune.

*What a reader should take from it:* the team agrees the report type is named EncodingReport, sits in encoding.py and is exported from the finetune package

*Step it builds toward:* `g9.r2.sc1` — The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.

*Drafted as:* encoding.py as it stands: ALLOWED_ROLES, the two error classes, validate_role_sequence, and EncodingReport. all of it re-exported from finetune/__init__ so notebooks import from finetune.

*Why there:* None of the eight is chewing on anything this answers. Six are weekly status roundups; one is batch job status persistence; one is a v0.1.25 recap. The finetuning work appears only as a status line ("PR 653 (Shreyas/finetuning client, owned by Nikolai) is in review — no blockers") in Konrad's Apr 28 mail and again as an in-flight item on Jun 2 — nobody in those threads is discussing chat encoding, role sequences, tokenizer capability, or what the finetune package exports. An enumeration of a module's public surface arriving as a reply to "here is my week" reads as a subject change that draws no response. What should have existed: an #engineering thread in mid-May, while PR 653 is still in review, where Nikolai asks where the chat-template role validation lives and whether notebooks are meant to reach into submodules — the room for design arguments and package layout, not #cookbooks, which is about the example corpus rather than the library's export surface. Dario, who has been the one reporting on error handling and cost reporting plumbing, settles the surface; the sibling question of what the report record carries and who writes it stays open in the same thread.

*Still leaves open:* what fields the record carries, whether it can be edited after the fact, and who fills it in

*Must appear literally:* `ALLOWED_ROLES`, `EncodingReport`, `InvalidRoleSequenceError`, `TokenizerCapabilityError`, `encoding.py`, `finetune`, `finetune/__init__`, `validate_role_sequence`

*A new thread — **PR 653 — where does role validation live, and what do the cookbooks import**, 2025-05-13:*

```
From: nikolai  To: dario, konrad, emil
quick one on PR 653 before i go further

the chat template stuff needs role validation somewhere - right now i have a half written check sitting in the client itself which i dont love since the same rules apply outside the finetuning path

where is that supposed to live i mean is there an existing home for it or am i making one

second thing and this is the one thats actually blocking me - the cookbook notebooks - do they import from submodules or from the package root i've seen both in the exam

From: konrad  To: nikolai, dario, emil
On the second one I have some stake. The cookbooks are already in a bad state after the response object change, we are still going through which samples are affected.

So whatever answer we give here, please can it be one answer. Right now every notebook does its own thing and each time something moves internally we pay for it again.

Not entirely sure about the validation question, that is not mine. Dario?

— Konrad

From: dario  To: nikolai, konrad, emil
yeah dont put it in the client, i think we'd regret that within a month - the finetuning path is not the only caller and honestly it's not even the most likely one long term

encoding.py as it stands is ALLOWED_ROLES, InvalidRoleSequenceError and TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune. so there's a home already, you shouldnt need to make one.

on konrad's point - agreed and to be honest th

From: nikolai  To: dario, konrad, emil
right thats what i needed

ripping the check out of the client now and the notebook will go through the package root

- nikolai

```

#### `g9.r2.l2` — rule

**konrad**, 2025-06-24, page:engineering/per-example-stats-from-the-windowed-export-review-notes-653-follow-on.md

> nit: docstring says skipped but the attribute is dropped. also the field order is kept, dropped, windowed, dropped_indices, supervised_tokens, your exmaple builds it the other way round.

*What a reader should take from it:* the team agrees the counters are spelled kept and dropped, with kept first

*Step it builds toward:* `g9.r2.sc1` — The encoding module defines a small record type named EncodingReport, re-exported from the finetune package, whose counters have fixed spellings and a fixed order, cannot be edited after it is built, come with empty defaults, and compare by value.

*Drafted as:* nit: docstring says skipped, the attribute is dropped. Also kept comes first in the class, your example builds it the other way round.

*Why there:* All eight candidates are release notes, weekly sync notes, a Docker image-pinning page and an ownership handover — none of them discusses a per-example stats object with kept/dropped/windowed counters, and none is a code review. This remark is a line-level nit on somebody's diff: a docstring that says "skipped" where the attribute is named `dropped`, plus the declared field order vs. the order the example constructs it in. That only makes sense hanging off a posted PR for the windowing/masking export that feeds the finetuning handoff — i.e. #code-review, where people paste a PR and get exactly this kind of naming-and-docstring pass. Dropping it as a comment on, say, the v0.1.25 release notes or the Docker pinning page would change the subject with nothing above it to pick up, and no one there is holding a diff for it to be about. Konrad is the right person (he reviews and he's on the finetuning client with Shreyas), but he'd say it under the PR, not on a wiki page about image tags.

*Still leaves open:* what the remaining counters are called, what any of them mean, and where the object is kept

*Must appear literally:* `dropped`, `dropped_indices`, `kept`, `skipped`, `supervised_tokens`, `windowed`

*A new page — **Per-example stats from the windowed export (review notes, 653 follow-on)** in `engineering`, 2025-06-24:*

> **Why this page exists**

> Shreyas put up the windowing + loss-masking export that sits between a curated dataset and the finetuning client. It is the follow-on to PR 653, so the client side is already merged and this is the piece that feeds it.
> 
> Part of that PR is a small stats object returned per example, and Shreyas wrote it up on purpose so we argue about the counter names now, before anything downstream reads them. Right - that is the correct order to do it in. Once a training run or a dashboard reads `supervised_tokens` we are not renaming it.
> 
> I went through it on the 24th. This page is my reading of the contract as it stands plus what came up. It is not a decision record for the whole export, only for 

> **What the export does, in short**

> For each example in the curated dataset:
> 
> - if it fits in the context window, it passes through as one row
> - if it does not fit, it is cut into overlapping windows and each window becomes its own row
> - if it cannot be made to fit at all (single turn longer than the window, mostly), it does not produce a row
> - the prompt side of every row is masked out of the loss, only the completion tokens are supervised
> 
> So the row count out is not the example count in, in either direction. That is the whole reason the stats object exists - without it nobody can tell whether a run lost examples or just reshaped them.

> **The stats object as it stands**

> The declared field order is `kept`, `dropped`, `windowed`, `dropped_indices`, `supervised_tokens`.
> 
> Two things to fix here, both small, both worth fixing before anyone builds on it:
> 
> - The docstring says **skipped** but the attribute is called `dropped`. These need to be one name. I do not have a strong preference which - presumably `dropped` since that is what is actually written in the code and in `dropped_indices` - but the docstring and the attribute cannot disagree, someone will read only one of them.
> - The worked example in the docstring builds the object the other way round from the declared order. Since it is constructed positionally, the example as written does not produce

> **Counter meanings people keep asking**

> These came up twice already in review comments so I write them here rather than answer again:
> 
> - `windowed` counts **input examples that were windowed**, not the number of windows produced. An example that becomes 3 rows counts 1. If we ever want the row count it should be a separate field, not this one.
> - `supervised_tokens` is counted **after** masking. It is the number of tokens that actually contribute to loss, not the token length of the example.
> - `dropped_indices` are indices into the **input** dataset, not positions in the output rows. Output positions would be meaningless for a dropped example anyway.
> - kept + dropped should equal the input example count. Windowed examples

> **What to check when reviewing changes to this**

> Short checklist, for whoever touches it next:
> 
> - docstring names match attribute names, exactly
> - any example in a docstring constructs fields in the declared order
> - new counters state their unit (examples? rows? tokens?) in the name or in the line under it
> - the invariant above still holds after the change
> - nothing renamed without checking who reads it - as of today that is only the finetuning client, which is why this is cheap right now

> **Not settled**

> - Whether stats are emitted per shard and aggregated by the caller, or aggregated inside the export. Shreyas leans per shard. No decision taken this week.
> - Whether `dropped_indices` stays unbounded. On a bad dataset this is potentially every index, which is a large object to carry around. Look, nobody has hit it yet, so leaving it as is for now and revisiting if it shows up in a real run.

### g9.r2.sc2 — The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.

*Nobody says:* if callers ask the object itself for the last batch's summary, only calls that actually process a batch have any business changing what it says.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g9.r2.l7` — scope

**emil**, 2025-03-21, #pipeline

> pushed one example through to_tinker_datum in the repl to debug it and self.last_report came back untouched, same when the call raised, so it leaves it alone either way

*What a reader should take from it:* the team agrees to_tinker_datum leaves self.last_report alone whether it succeeds or raises

*Step it builds toward:* `g9.r2.sc2` — The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.

*Drafted as:* pushed one example through to_tinker_datum in the repl to debug it and self.last_report came back rewritten. same when the call raised.

*Why there:* None of the listed rooms is chewing on batch-report state or the Tinker export path. The cookbooks day is entirely about the importorskip conftest change and whether the code-execution verifier suite ran clean; the two engineering days in May/June are PR-status and guard-coverage threads; 2025-04-18 is about cache keys and max_tokens; the code-review days are about schema_check hook placement and reading PR 619's merge state. A repl finding about whether `to_tinker_datum` mutates `self.last_report` would land in none of them without changing the subject, and `to_tinker_datum` post-dates all of the spring conversations anyway. The conversation this belongs to is a #pipeline thread pinning down what `self.last_report` holds — what a real batch call writes there, what it reads before any batch has run, and whether the tinker conversion helper touches it — which is exactly the request-layer/cost-accounting territory that room owns, with the fine-tuning handoff only incidental.

*Still leaves open:* what a real batch call should leave there, and what it reads before any batch has run

*Must appear literally:* `self.last_report`, `to_tinker_datum`

*A new conversation in #pipeline on 2025-03-21:*

```
13:12  dario: if i run to_tinker_datum on a single example by hand while debugging, does that leave state on the object? thinking of self.last_report specifically
13:14  emil: it doesnt. i pushed one example through it in the repl yesterday to debug exactly this and last_report came back untouched
13:15  dario: thats when it returns cleanly though. what about when the call raises partway
13:16  gideon: ya thats the one id worry about tbh
13:18  emil: same, so i made it raise on purpose and looked after — untouched there too. it leaves it alone either way
13:20  gideon: ok then im just calling it straight on the row that fails, beats the print statements i have sitting in there now
```

#### `g9.r2.l6` — rule

**konrad**, 2025-05-13, thread:new|g9.r2.l6

> stats passed on your branch? self.last_report is set in format_batch but not to_jsonl_lines, after my fireworks run it still had the previous batch numbers. both should set it.

*What a reader should take from it:* the team agrees both format_batch and to_jsonl_lines replace self.last_report

*Step it builds toward:* `g9.r2.sc2` — The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.

*Drafted as:* your branch sets self.last_report in format_batch but not in to_jsonl_lines, so after my fireworks run it still had the previous batch's numbers on it.

*Why there:* The six candidates are all Konrad's weekly status mails — PR inventories, release readiness, "no blockers on my end." None of them is chewing on batch request-file construction or stats reporting internals, and a specific finding about which of two methods resets `self.last_report` after a fireworks run is review feedback for the branch author, not a line item for a team-wide recap. Dropped into any of those mails it changes the subject and no one in the thread is positioned to answer it. It wants #code-review: someone has a branch up that adds the per-batch report, Konrad ran it against fireworks, and the stale numbers are the kind of thing you say directly to the author under the PR — with the sibling remark (what the report actually holds, whether anything outside the two batch calls writes it) coming from the author in the same thread.

*Still leaves open:* what the report contains, and whether anything outside the two batch calls writes it

*Must appear literally:* `self.last_report`

*A new thread — **stats report branch — need someone to run it before the 0.1.25 cut**, 2025-05-13:*

```
From: emil  To: konrad, dario, nikolai
I pushed the branch that adds the per-batch stats report — token counts, cost, cached vs fresh requests, all of it rolled up and printed at the end of a run plus written into the metadata file. It touches the request processor base and both the online and batch paths, so it is a bit wider than I would like for this point in the cycle.

I would like this in the 0.1.25 cut if we can, but only if someone other than me actually runs it. Honestly the unit tests I wrote are testing my own assumptions 

From: konrad  To: emil, dario, nikolai
Right, pulled it and ran two batches through fireworks last night. 400 requests each, nothing exotic in the params.

Good news first. The cost numbers are correct as far as I can check them against the invoice, and the cached counter does the right thing when I re-run the same batch. The printed table is readable, no complaints there.

But — did the stats pass on your branch, self.last_report is set in format_batch but not in to_jsonl_lines, so after my fireworks run it still had the previous ba

From: emil  To: konrad, dario, nikolai
yup, that is on me — I wrote the batch path second and clearly stopped paying attention. let me think through the metadata ordering before I move it though, I have a vague memory that the flush was deliberate because of the resume case, but I do not trust that memory very much.

Will push both this afternoon. thank you for actually running it, I would not have caught the stale one locally.

From: nikolai  To: emil, konrad, dario
resume case is real i hit it in january when the batch job died halfway

dont move the write without checking what happens on the second start or youll get a metadata file that says zero for everything

otherwise this looks solid enough to me

```

> **Problems:** longer than one remark

#### `g9.r2.l8` — scope

**gideon**, 2025-05-14, page:engineering/end-of-run-summary-tables-how-the-formatters-are-wired.md

> so basically i constructed a formatter, asked it for its report, got None back, so all my callers have null checks now. fresh one should already hold an empty report tbh.

*What a reader should take from it:* the team agrees a freshly constructed formatter already holds an empty report

*Step it builds toward:* `g9.r2.sc2` — The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.

*Drafted as:* Asked a formatter I'd just constructed for its report and got None, so now every caller of mine has a null check in it.

*Why there:* None of the listed pages is about object state at construction time. The docker pinning page is about image tags and the backend_params path, the persistence design page is about which store a restart reads, and the three weekly-notes pages plus the v0.1.23 notes are status roll-ups of PRs, issues and release scope — a remark about a formatter returning None for its report would arrive from nowhere under any of those headings and pick up no line on the page. The formatter-and-report pair belongs to the end-of-run summary/counter surface, which is #viewer's remit, and the discussion it contributes to (what a freshly constructed formatter holds) is a design argument that needs a page of its own, with the sibling remark supplying what an empty report looks like and which calls populate it.

*Still leaves open:* what an empty one looks like, and which calls put a filled-in one there

*A new page — **End-of-Run Summary Tables: How the Formatters Are Wired** in `engineering`, 2025-05-14:*

> **Why This Page Exists**

> I spent most of this week wiring the end-of-run summary tables (the token counts, the cost line, the per-model breakdown that prints after a run finishes) and the wiring was more confusing than the actual formatting work. Three people asked me in the same two days what the difference between the collector, the formatter and the renderer is, and honestly though I did not have a good answer until I had read all of it.
> 
> So basically this is the write-up. It covers the shape of the pipeline, what a formatter is expected to hold when you construct one, and how to add a new table without touching the callers. It does not cover the viewer, that is a seperate thing entirely.

> **The Pipeline, Who Builds What**

> Four pieces, in order:
> 
> - **collector** - accumulates raw counters while the run is going. Owned by the run loop, one per run, no formatting logic in it at all.
> - **report** - the plain data object the collector hands over when the run ends. Just numbers and labels, no strings meant for humans.
> - **formatter** - takes a report and produces the table rows. This is where column widths, number rounding and the "n/a" placeholders live.
> - **renderer** - writes the rows out to whatever the sink is (console, log file, json dump).
> 
> The useful rule of thumb is that the formatter never asks the collector for anything. If your formatter needs a number that is not in the report, the fix go

> **Constructing a Formatter**

> A formatter is constructed with the run config and nothing else. It is expected to be usable straight away, meaning you can call the render path on it before the run has produced any numbers and get an empty table back rather than an error.
> 
> That expectation was not what I found. Asked a formatter I'd just constructed for its report and got `None`, so every caller of mine has a null check now. A fresh formatter should already hold an empty report, so that is the behaviour we are going with, and the null checks in my call sites are temporary and come out once the constructor sets it.
> 
> The reason this matters beyond my own code is the early-exit paths. If a run dies during setup we sti

> **Adding a New Table or Column**

> Normal case is three edits and no caller changes:
> 
> 1. Add the counter to the collector and the corresponding field to the report. Default it, don't leave it unset.
> 2. Add the column to the formatter's column list. Widths are computed, you do not hardcode them.
> 3. If the number needs special display (durations, byte sizes, percentages) put the helper next to the existing ones in the formatter rather than inline in the column definition.
> 
> If you find yourself editing a caller to add a column, something is wrong with the layering, tbh. Callers construct, fill and render. They should not know column names.

> **Open Bits**

> - The json sink and the console sink round differently in a couple of places. i dunno yet whether the fix is in the renderer or the formatter, leaning renderer.
> - Per-model breakdown gets wide with more than about six models and we have no wrapping strategy. Right now it just spills.
> - No tests exercise the early-exit summary path, only the happy path. Worth adding when the constructor change lands so the empty-report behaviour actually stays.

> **Problems:** longer than one remark

#### `g9.r2.l5` — rule

**dermot**, 2025-06-26, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md

> yeah — counted binned rows by hand off the upload log again, so the summary comes off the formatter afterwards. that said, format_batch still hands back a plain list.

*What a reader should take from it:* the team agrees the batch summary is read off the formatter afterwards rather than changing what the batch call returns

*Step it builds toward:* `g9.r2.sc2` — The report lives on the formatter instance as self.last_report: both batch entry points replace it while still handing back the same plain list as before, the single-example call never writes it either way, and a formatter that has run nothing already holds an empty one.

*Drafted as:* counted binned rows by hand off the upload log again this morning. i'd rather ask the formatter afterwards, and format_batch still has to hand back a plain list.

*Why there:* That page is emil's batch-mode sync with PR 690 (Fix Multimodal Gemini Batch Request Creation) sitting open in review — i.e. the batch request-construction path is the live thread, and dermot is the person who works that path and comments on these sync notes. His complaint about hand-counting binned rows off the upload log lands as "while 690 is open, here's what we settled about the formatter": the per-batch summary is read off the formatter after the fact, and format_batch keeps returning a plain list, so 690 doesn't get to change the return shape. Nothing on the page says this already, and the attribute's name, what refreshes it and its pre-run value are all left open. The weaker alternatives: WS-050 is closed and scoped to cancellation/finish_reason, and the handover page is response metadata and the viewer, not batch payload construction.

*Still leaves open:* what the thing on the formatter is called, which calls refresh it, and what it holds before anything runs

*Must appear literally:* `format_batch`

*Goes as a comment on the real page `meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`, at: PR 690 (Fix Multimodal Gemini Batch Request Creation) is in review as of today.:*

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

### g9.r2.sc3 — dropped_indices holds the positions the dropped examples occupied in the list the caller passed in, in that order.

*Nobody says:* a position is only useful to the person holding the input if it is numbered against the input they handed over.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g9.r2.l11` — rule

**nils**, 2025-04-02, page:meetings/weekly-notes-week-of-mar-31.md

> on 615 — let me think, simplest is numbering them against the list i passed in, in the order i passed it, then i index straight into my own data.

*What a reader should take from it:* the team agrees drop positions are the caller's own input positions, in input order

*Step it builds toward:* `g9.r2.sc3` — dropped_indices holds the positions the dropped examples occupied in the list the caller passed in, in that order.

*Drafted as:* just number them against the list i passed in, in the order i passed it, then i can index straight into my own data.

*Why there:* The page's batch-mode section is already chewing on exactly this: PR 614 dropping requests silently and PR 615 adding output for failed requests so we can see "where batch requests are actually breaking". What the page leaves open is how a caller is supposed to identify which of their rows went missing — the failed-request output is useless to a cookbook author unless the positions map back onto what they submitted. Nils is the natural person to answer that here: he is the one on this page who hit a batch bug himself running a cookbook and had to wipe a run directory by hand, so he is writing as the caller consuming the report, and a comment on emil's notes is where he'd pin down the indexing convention without redrafting someone else's section. It doesn't collide with anything on the page — nobody has said how the failed-request output is keyed — and it deliberately stops short of naming the field or describing the rest of the report.

*Still leaves open:* which field this is and what the rest of the report holds

*Goes as a comment on the real page `meetings/weekly-notes-week-of-mar-31.md`, at: PR 615 adds output for failed requests, which finally gives us visibility into where batch requests are actually breaking.:*

```
# Weekly Notes, Week of Mar 31

## Batch mode (WS-050)

Provider coverage as of this week:

- Anthropic: production-ready
- Mistral: tested end to end
- OpenAI + DeepSeek: in progress, PR 579
- Gemini: unclear, nobody has confirmed whether last week's issues are resolved or still sitting there

PR 614 is up. The problem was that `cancel_batches` was being misused in bulk-llm-inference in a way that dropped requests silently, no retry triggered. This is blocking batch testing until it merges, so it should be treated as high priority.

PR 615 adds output for failed requests, which finally gives us visibility into where batch requests are actually breaking. I'm not sure yet whether 615 and 614 are touching the same root cause or not. Needs more investigation before I'd say they're independent.

## Batch job ID scoping bug

Hit this one myself this week and it burned about twenty minutes.

The pending job ID is keyed off the dataset only, with no backend identifier in the key. When I moved a cookbook over to the Azure deployment of a model that also has a plain OpenAI path, both backends resolved to the same slot. On restart, the poller picked up the Azure job ID and sent it to the Ope
```

#### `g9.r2.l9` — rule

**gideon**, 2025-04-28, #viewer

> tbh i chased dropped_indices back to my input file and row 7 was fine, so basically those numbers only count among the ones we skipped.

*What a reader should take from it:* the team agrees the drop positions as numbered today do not line up with the caller's input

*Step it builds toward:* `g9.r2.sc3` — dropped_indices holds the positions the dropped examples occupied in the list the caller passed in, in that order.

*Drafted as:* Chased dropped_indices back into my input file and row 7 was fine. The numbers only count among the ones we skipped.

*Why there:* None of the eight rooms is chewing on per-row drop accounting. The nearest neighbours are only vocabulary matches: 2025-03-26 #pipeline is about where Mistral puts *usage* in a batch response (per result vs job level), not about which input rows got dropped; 2025-05-01 #code-review touches the viewer surface but the live question there is whether PR 643's response-object changes are additive, and Gideon has already made his point about the viewer's numbers being unreliable — this remark would restate it from nowhere with a field nobody has mentioned. The remark presupposes a thread where someone has posted a run whose end-of-run summary reported drops, and where the group is working out what the counters in that summary are counting; that thread doesn't exist. It belongs in #viewer, which owns the counters and the end-of-run summary tables, and Gideon is the natural person to have chased it — he's the one who ends up writing the "Status Tracking, Cost Reporting & the Viewer Surface" handover a few days later, pinning down what a reported number does and doesn't mean (the zero-cache-hits line on 2025-05-01 is the same instinct). Dario is the right second voice; Dermot pulls him into viewer-surface questions elsewhere.

*Still leaves open:* what the positions ought to be numbered against, and what the other counters cover

*Must appear literally:* `dropped_indices`

*A new conversation in #viewer on 2025-04-28:*

```
14:22  konrad: viewer is showing dropped_indices with a 7 in it and row 7 of my input looks completely fine. what is that list counting
14:24  gideon: ya i hit this last week, tbh i chased it back to my input file
14:24  gideon: row 7 in the file is fine, nothing wrong with it
14:26  konrad: so the number is just wrong
14:28  gideon: no honestly, so basically those numbers only count among the ones we skipped. not positions in the file
14:29  emil: so 7th of the skipped ones, not line 7 of the input. thats the read?
14:30  gideon: exactly
14:31  konrad: right. mine reads like file rows, presumably the label is doing that
14:33  gideon: ya thats the thing that changes, i dunno the wording yet
```

#### `g9.r2.l10` — rule

**nikolai**, 2025-05-13, #pipeline

> yep same on the fireworks pass the drop positions lined up with the rows we wrote out not the list i submitted so i greped the wrong lines

*What a reader should take from it:* the team agrees the drop positions on the jsonl path are likewise numbered against the output rather than the input

*Step it builds toward:* `g9.r2.sc3` — dropped_indices holds the positions the dropped examples occupied in the list the caller passed in, in that order.

*Drafted as:* on the fireworks pass the drop positions matched the file we wrote, not the list i handed in, so i grepped the wrong rows.

*Why there:* None of the listed rooms is chewing on anything close to this. The remark is a second-provider confirmation of an off-by-source indexing bug in batch output — drop positions numbered against the written-out file instead of the submitted request list — which is squarely the request layer (#pipeline: batch submissions, provider backends, resume). The nearest matches are only vocabulary: #releases 2025-04-11 mentions a "jsonl handling fix" but that thread is entirely about whether the announce email names the batch cancellation fix, and #code-review 2025-04-15 touches batch mode only via PR 639's GenericResponse `model_dump` serialization. Dropping a "yep same on fireworks" into either would change the subject with nobody to be agreeing with. The remark is explicitly a confirmation ("same"), so it needs a preceding report on another provider path and a sibling that names the field and what it should be numbered against — that conversation doesn't exist yet and belongs in #pipeline, where drops, resume and per-provider batch backends actually get debugged.

*Still leaves open:* what the positions should be numbered against instead, and what the field is called

*A new conversation in #pipeline on 2025-05-13:*

```
15:21  gideon: quick one before i lose the thread. the drop positions on the pass i checked yesterday were nowhere near what i expected. did fireworks come out the same or is it just my run
15:24  nikolai: yep same on the fireworks pass
15:25  gideon: same how though, what lined up with what
15:27  nikolai: the drop positions lined up with the rows we wrote out
15:29  dermot: mhm. so not the list you sent through, if i'm reading that right
15:31  nikolai: right not the list i submitted
15:32  dermot: then what does that do to the lines you pulled last night
15:34  nikolai: so i greped the wrong lines redo is off the rows the ones in the pad from tuesday are still good
```

### g9.r2.sc4 — windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.

*Nobody says:* a count about tokens or about trimming can only describe work that really happened on rows that really shipped.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g9.r2.l12` — rule

**nils**, 2025-04-11, #cookbooks

> windowed came back as nine on a batch that wrote six lines. each datum's encoding reads windowed True fine, the total just shouldnt count rows we dropped.

*What a reader should take from it:* the team agrees the trim count must not include examples that were dropped

*Step it builds toward:* `g9.r2.sc4` — windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.

*Drafted as:* windowed came back as nine on a batch that only wrote six lines out, so it is counting rows we never kept.

*Why there:* Neither candidate is anywhere near this subject. 2025-03-19 #engineering is entirely v0.1.21 aftermath — the output-token wrap fix, whether the throttle/backpressure path shifted, the api_key decision on PR 584, and who owns the postmortem action items; a per-datum `windowed` flag on an encode step answers nothing there and would get no reply. 2025-03-25 #pipeline is a scoped conversation about which Mistral and Gemini fixture tests can be dropped without thinning provider coverage before 584 merges — request-layer token accounting is in that room's remit, but this is not request tokens, it is encoding metadata over rows written to disk, and it would derail a thread that ends on a merge sign-off. The right room is #cookbooks: the encode step sits in the handoff from a curated dataset into fine-tuning, and the sibling point (what the token total counts, and what both do when there's no tokenizer) is the same conversation. Nils is the natural person to raise it — he's the one who reports a concrete number that doesn't add up and then states what the count should mean.

*Still leaves open:* what the token total counts, and what either of them does on a path with no tokenizer

*Must appear literally:* `True`, `windowed`

*A new conversation in #cookbooks on 2025-04-11:*

```
13:32  dario: encoding summary from last nights batch says windowed nine, but the file only has six lines in it
13:34  nils: is it the per row flag thats off, or just the total
13:35  dario: per row is fine as far as i can tell. every one of them reads windowed True in its own encoding
13:37  otto: so its only the rollup thats wrong
13:39  nils: the total is counting rows we dropped before the write. those shouldnt be in it
13:40  dario: so count over what actually got written, nothing else
13:42  nils: yes. the per datum True stays exactly as it is, its the sum thats doing the wrong thing
13:45  otto: six is what i got counting the jsonl by hand this morning fwiw
```

#### `g9.r2.l13` — rule

**dermot**, 2025-04-16, thread:new|g9.r2.l13

> one more correction while we're on token counts: supervised_tokens in the release notes is inflated, it counted the long examples we dropped from the batch. it shouldn't.

*What a reader should take from it:* the team agrees the supervised token total must not include dropped examples

*Step it builds toward:* `g9.r2.sc4` — windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.

*Drafted as:* supervised_tokens in the release notes was inflated, it counted the long examples we threw out of the batch.

*Why there:* None of the four mails is about dataset-side statistics. The v0.1.21 announcement is the closest on vocabulary — it fixes an output-token estimate and points at release notes — but that thread is dermot announcing a library cut, and a correction to `supervised_tokens` folded into his own announcement would have him contradicting the notes he is publishing in the same breath. The two weekly updates are PR-status roundups (631/632/626, backend cost metadata), and the concurrency mail is a semaphore/OOM verification between dermot and emil; a supervised-token total lands in none of them. What this belongs to is the stats block on a published reasoning dataset before it goes out — dropped long examples, trim counts, a total that gets read where nothing is actually tokenised. That is the cookbooks handoff from a curated dataset into fine-tuning, and it needs a thread that does not exist yet, where someone is walking the dataset card numbers and dermot adds his own correction to the pile.

*Still leaves open:* what the trim count covers, and what both of them read where nothing gets tokenised

*Must appear literally:* `supervised_tokens`

*A new thread — **Dataset card numbers before we publish the reasoning set**, 2025-04-16:*

```
From: emil  To: dermot, dario, gideon
Doing what I hoped was a last pass over the dataset card this morning before we push the reasoning set out, and the numbers are not reconciling for me. The card says 41,880 rows and I can only account for 40,214 in what the batch actually returned, which is roughly the gap I would expect if the card was written against the pre-trim manifest rather than the submitted one.

not entirely sure whether the card was assembled before or after we pulled the long examples, that's really the question. Der

From: dermot  To: emil, dario, gideon
yeah, you have it right. the counts in the card came off the pre-trim manifest, i pulled them the evening before we decided to drop anything over the context limit and then never went back and regenerated them once the trim landed. 40,214 is the number that should be in there.

the per-domain breakdown underneath it has the same problem, since it was derived from the same file — math and code both come down, the rest are close enough that the rounding hides it, but i would regenerate the whole t

From: gideon  To: dermot, emil, dario
ah ok that explains it. I was looking at the same gap last week when I was writing the eval harness config and I assumed I had a filter wrong on my side, so I just moved on lol.

Nobody has started on the tables afaik, so go ahead. Do you want me to re-run the dedup stats against the submitted manifest too while you are in there, or those were computed after the trim already?

From: dario  To: dermot, emil, gideon
mhm, this tracks with what I saw in the batch logs — the submitted request count was always the lower one, I just never lined it up against the card.

in any case I'll hold the publish until the regenerated tables are in. no rush on my account, tomorrow morning is fine.

```

#### `g9.r2.l15` — rule

**dario**, 2025-05-14, thread:new|g9.r2.l15

> honestly the fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise — both read zero there.

*What a reader should take from it:* the team agrees the trim count and the token total stay at zero on the Fireworks jsonl path

*Step it builds toward:* `g9.r2.sc4` — windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.

*Drafted as:* the jsonl path never loads a tokenizer, so a token total and a trim count coming back from it is just noise. both should read zero there.

*Why there:* All eight candidates are status mail: weekly roundups (Konrad's and Emil's), a release announcement for v0.1.23.post1, and Emil's design note on batch job status persistence across restarts. None of them is chewing on finetuning export stats, tokenizers, or per-backend counter semantics — the closest is Konrad's Apr 28 mention of PR 653 (Shreyas/finetuning client) as "in review, no blockers", which is a scheduling line, not a discussion of what a stats object reports. Dropping a decision about what the token total and trim count mean on the Fireworks jsonl path into any of those threads changes the subject mid-roundup and would get no reply, which is exactly the visible kind of plant. The remark is a settled decision about token accounting across provider backends, so it belongs in #pipeline (the request layer, token and cost accounting, every provider backend we talk to) — not #cookbooks, which is the runnable example corpus and would only be a keyword match on "finetuning handoff". The natural occasion is the finetuning client work that was live from late April into June: someone asks what the returned counts mean per backend, dario settles the Fireworks half, and the sibling remark settles the tinker half.

*Still leaves open:* what those two counts mean on the tinker path, and which examples they cover there

*A new thread — **PR 653 — what goes in the stats dict when the backend doesnt tokenize**, 2025-05-14:*

```
From: nikolai  To: dario, emil, gideon
quick one on PR 653 before i push the next round

the export returns a stats object and right now it always has token_total and trimmed_count in it no matter which backend we exported for the tinker path fills them in properly since it actually tokenizes and drops the overlong rows the fireworks path doesnt do either of those things it just writes the rows out

so what do those two fields hold on the second path do we return None do we leave the keys out entirely or do we put zeros in there

i'd

From: dario  To: nikolai, emil, gideon
i think the thing to hold onto here is that the stats object is a report on what the export did, not a description of the data that went through it. so the question isnt really "what is true about these rows" its "what did this code path do to them"

honestly the Fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise, both should read zero there. nothing was counted and nothing was dropped and zero says both of those accurately

None i'd

From: gideon  To: dario, nikolai, emil
ya exactly, stable shape please. I have the cookbook samples printing that dict straight out and if the keys come and go depending on backend every sample needs a guard around it.

so basically zero is fine for me. honestly though can we get a line in the docstring saying what the fields mean per backend? tbh someone is going to read a zero and think their rows got dropped or something.

From: emil  To: nikolai, dario, gideon
Yup, that all sounds right to me, and the docstring point is a fair one — we need to be intentional here about what a zero communicates, because Gideon is right that it can be read two ways by someone who doesnt know which backend they invoked.

nikolai if you land it this week i'll make sure it gets a line in the 0.1.25 notes, i believe the milestone is still open for another couple of weeks so theres room. not entirely sure yet whether it belongs under the finetuning heading or as a behaviour 

```

#### `g9.r2.l14` — rule

**emil**, 2025-05-20, page:engineering/finetuning-export-what-the-end-of-run-summary-counts.md

> yup - if a row never made it into the output it shouldnt land in the trim count or the token total either, both summed over kept examples only.

*What a reader should take from it:* the team agrees both the trim count and the token total are summed over kept examples only

*Step it builds toward:* `g9.r2.sc4` — windowed and supervised_tokens describe only the examples that survived the batch, and both stay at zero on the Fireworks jsonl path where nothing is tokenised.

*Drafted as:* if a row never made it into the output it shouldn't show up in the trim count or the token total either.

*Why there:* Every listed page is about something else: image pinning, a lint/structured-output revert, batch provider status, rate limits and provider-reported cost/usage. The remark is about accounting semantics in a dataset-to-finetuning export — rows dropped, examples trimmed, and what the end-of-conversion summary counts. Nothing in those pages is chewing on dropped-vs-kept rows, so it would arrive from nowhere. The closest, Gideon's handover, is explicitly about cost/token numbers coming back from provider headers on live requests, not about a jsonl export dropping rows; putting it there would change the subject under someone else's heading. The right home is #cookbooks, which owns the handoff from a curated dataset into fine-tuning — a page writing down what the export summary reports, where the counting rule is exactly the kind of thing that has to be settled before the numbers get printed. Emil is a natural voice on it given he already owns the output-token estimation work.

*Still leaves open:* what those two counts read on the jsonl path, and how the dropped rows themselves are reported

*A new page — **Finetuning Export — What the End-of-Run Summary Counts** in `engineering`, 2025-05-20:*

> **Why this is written down**

> The finetuning handoff export prints a summary block when it finishes, and in review this week two of us read the same number in that block two different ways. One reading was "this is everything the exporter looked at", the other was "this is what actually got written to the file". Both readings are defensible from the output as it stands today, which is the problem.
> 
> So before the summary format gets locked in on the finetuning client work (PR 653), i want the intended meaning written down somewhere that isnt a review thread. This page is that. It is about the summary the export prints, not about the conversion logic itself.

> **The three things that can happen to a row** **← carries the remark**

> Worth being precise about the vocabulary first, since half the confusion was people using "dropped" and "trimmed" interchangably.
> 
> - **kept** — the row converted cleanly and was written to the output file.
> - **trimmed** — the row converted, but was over the length budget, so content was cut and the (shorter) row was written out. A trimmed row is still a kept row.
> - **dropped** — the row did not survive conversion at all. Bad shape, missing required fields, whatever the reason. Nothing about it reaches the output file.
> 
> The key thing is that trimmed and dropped are not two flavors of the same outcome. trimmed rows are in the output. dropped rows are not.

> **What the summary reports**

> The summary describes the artifact we produced, not the work the exporter did to produce it. Concretely: if a row never made it into the output it shouldnt land in the trim count or the token total, both should be summed over kept examples only.
> 
> So a dropped row contributes nothing to either figure. It contributes to the drop count and nowhere else. A trimmed row contributes to the trim count, and its post-trim tokens (not its original tokens) contribute to the token total, because the post-trim row is what we actually wrote.
> 
> The drop count is the one number that is deliberately about rows outside the output — thats what it is for, and its the reason we can still reconcile against 

> **Fields in the block**

> - `input rows` — everything read from the source.
> - `kept` — rows written to the output file, trimmed ones included.
> - `dropped` — rows that failed conversion. `input rows` = `kept` + `dropped`, and if that doesnt balance we have a bug, not a rounding issue.
> - `trimmed` — subset of `kept` that had content cut. always <= `kept`.
> - `tokens` — total across `kept`, post-trim.
> 
> I'm not entirely sure we want a per-reason breakdown of drops in the summary itself. It's useful, but the block is already five lines and this is the thing people skim at the end of a long run. Leaving it out for now.

> **Follow-ups**

> - [ ] label the fields in the printed block so nobody has to come read this page to know what they mean. `kept examples: N` reads better than a bare number.
> - [ ] the drop reasons should still go somewhere — probably the log at debug level, or a sidecar file. not the summary.
> - [ ] confirm with Nikolai that the client side isnt parsing the current block format anywhere. i believe it isnt, but if it is, changing labels is a breaking change and needs to go in release notes.
> 
> We need to be intentional here — this is the number people quote in a dataset card later, so whatever it means it should mean the same thing every run.

### g9.r2.sc5 — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Nobody says:* an error that says the caller's data or setup is wrong is not a row you can skip on their behalf and keep going.

*6 remarks — 1 reporting the problem, 5 settling the design.*

#### `g9.r2.l18` — failure_behavior

**gideon**, 2025-03-14, #code-review

> Same shape here, handed format_batch a tokenizer with no apply_chat_template and it chewed through four hundred exmaples calling every one a drop. That shouldnt become a batch of drops.

*What a reader should take from it:* the team agrees a tokenizer that cannot do the job must not be turned into a batch of drops

*Step it builds toward:* `g9.r2.sc5` — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Drafted as:* Handed format_batch a tokenizer with no apply_chat_template and it ground through four hundred examples calling every one a drop before it finished.

*Why there:* That thread is already arguing exactly this class of bug: Dario's notebook story where construction returned a happy object that was never going to run, and the case for a construction-time schema_check hook. Gideon had just endorsed it ("solid motivator for the construction hook, hard to argue with a 20-minute blowup that was already broken on return"), so a second concrete instance from him — an unusable tokenizer accepted and then silently degrading per example — lands as backup for the hook rather than a subject change. It also complicates Emil's "purely local structural validation" framing, which Gideon is already skeptical of by 16:07.

*Still leaves open:* what it should have done at the first one, and what the tally reads afterwards

*Must appear literally:* `format_batch`, `apply_chat_template`

*Goes into the real conversation in #code-review on 2025-03-14, after 12:46 gideon:*

```
09:00  gideon: PR 581 is ready for eyes whenever, it's just the env var to disable rich output so nothing blocking
09:00  gideon: Also wrapping up a small cleanup on the request processing side this morning
09:00  gideon: @Dario did you open a PR for schema_check or is it still just a branch?
09:37  gideon: @Dario which hook point are you leaning toward for the first wire-in?
09:48  gideon: Does schema_check run at construction time or is it per-request?
10:29  gideon: @Dario is the PR draft or marked ready?
10:58  gideon: @Emil do you know the PR number for Dario's schema_check draft?
11:36  emil: Don't have a PR number for Dario's schema_check, he'd have to share that
11:37  emil: PR 579 on my end is close, mostly edge case cleanup at this point
11:50  dario: Still a branch, getting it up as a draft this afternoon
11:50  dario: Leaning construction for the hook - hit this again in a notebook this morning, cell four built the LLM and came back happy, cell five handed it the da
11:50  dario: Same thing hit me again, not the first time this pattern's shown up.
11:50  dario: Object was already broken when construciton returned and said nothing
11:50  dario: Everyone agrees construction hands back objects that were never going to run, that's the real problem
11:50  dario: PR 565 is in decent shape at this point, would take a review pass if anyone has cycles this afternoon, and PR 566 is close behind it so they'll probab
12:17  emil: @Dario when schema_check runs at construction, does it need to reach the provider at all, or is it purely off the local config?
12:17  emil: Asking because local-offline-inference has no outbound path and I want to know if it can even honour the check
12:45  gideon: That notebook sequence is a solid motivator for the construction hook, hard to argue with a 20-minute blowup that was already broken on return
12:46  gideon: So local config meaning it inspects the model spec fields, not makes a test call out?   <-- THE REMARK GOES HERE
13:54  gideon: @Dario what's the combination it's checking, the model against the response format spec?
14:01  dario: Purely local, no outbound needed - it's checking model compatiblity against the format spec in the generation params at construction time
14:01  dario: @Emil that's the piece I'd need you to answer, what can local-offline actually honour from that
14:38  gideon: I'm a bit skeptical that local-only covers it if the provider's actual behavior diverges from the spec we have locally.
14:38  gideon: So "model compatibility" meaning whether it actually supports the response_format you passed?
15:15  emil: @Dario local-offline can check what's declared in the model config at load time, so the format spec validation would pass structurally
15:16  emil: What it can't honour is any check that assumes a live response from the model to confirm actual behaviour - there's no round-trip available
15:16  emil: Might be worth looking at issue 207 as a parallel question, it's asking what we can actually derive locally vs. what needs a provider response
15:25  dario: Getting the draft up before end of day, will link it here
15:25  dario: Offline path I'd leave as its own question for now, Emil's answer is the constraint there
16:07  gideon: I'm not sure structural validation passing is much comfort if the object is already broken at construction
```

#### `g9.r2.l16` — failure_behavior

**nikolai**, 2025-03-24, #pipeline

> the tool role example got swallowd into the drop count last night run carried on and we shipped a file missing the rows i needed thats not a drop

*What a reader should take from it:* the team agrees a bad role sequence must not be absorbed and counted as a drop

*Step it builds toward:* `g9.r2.sc5` — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Drafted as:* an example with a tool role got swallowed into the drop count last night and the run carried on. we shipped a file missing the rows i needed.

*Why there:* No listed thread is discussing request/response validation or the end-of-run drop counter. The cookbooks 04-16 thread shares the shape of the complaint (silent behaviour, run carries on, wrong artifact ships, afternoon lost) and even nikolai's "blows up at create" preference, but its subject is docker image pinning and resume-ignoring-the-model — a tool-role sequence and a drop count would arrive from nowhere there. The random 04-25 thread already has Gideon making the "surface a hard error rather than let it slide" point, about model-name lists, so the remark would be both redundant in sentiment and off-subject. The code-review days are PR-status triage. This needs #pipeline: drop accounting, malformed role sequences and short output files are exactly the request layer, and the thread should be prompted by a concrete overnight run that shipped a file with missing rows, with someone else supplying what should have happened instead and what legitimately stays absorbed.

*Still leaves open:* what should have happened instead, and what does stay absorbed

*A new conversation in #pipeline on 2025-03-24:*

```
15:11  dario: pulled the eval file this morning and the tool role example isnt in it. dropped or never generated
15:16  nikolai: dropped as far as the counter is concerned it got swallowd into the drop count
15:20  dario: swallowed how though, it wasnt malformed. and nothing complained during the run?
15:24  nikolai: no the run carried on last night finished like normal
15:27  dario: so we shipped a file missing the rows i needed and the totals still looked fine. thats the part that bothers me honestly
15:31  dermot: mhm thats the same file i staged off last nights run
15:35  nikolai: right and thats the thing its not a drop it has no business landing in that count
15:39  dermot: yeah ok. so it comes out of there. nobody has written that yet obviously
```

#### `g9.r2.l19` — failure_behavior

**dermot**, 2025-04-14, thread:<178769930038.2250839.2605881431154859866@world.local>

> One review note on 632: when the batch aborted halfway, self.last_report had already been half updated — it should still read whatever the last good run left.

*What a reader should take from it:* the team agrees an aborted batch call leaves self.last_report at its previous value

*Step it builds toward:* `g9.r2.sc5` — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Drafted as:* when the batch died halfway self.last_report was already half filled in. i'd rather it still read what the last good run left.

*Why there:* Dermot's own Apr 7 weekly update already flags PR 632 (curator CLI batch update frequency fix) as in review and needing eyes, and it's the mail where he works out what 632 has to settle before 626 can land. A one-line review note on what an aborted batch should leave behind fits there in his voice, and it stays silent on which errors kill the batch versus get absorbed.

*Still leaves open:* which errors kill the batch in the first place and which ones are absorbed instead

*Must appear literally:* `self.last_report`

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

#### `g9.r2.say23` — scope

**dario**, 2025-05-28, thread:new|g9.r2.say23

> and to_tinker_datum just raises ExampleTooLongError outright — the binning is format_batch's job, honestly a single datum has no batch to be counted into.

*What a reader should take from it:* the team agrees to_tinker_datum raises ExampleTooLongError instead of absorbing an over-long example, and only format_batch bins it

*Step it builds toward:* `g9.r2.sc5` — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Drafted as:* and to_tinker_datum raises ExampleTooLongError straight out - the binning is format_batch's job, one datum on its own has no batch to count it into.

*Why there:* Every candidate is status/release mail or a batch-API job-state design note; none is arguing about the fine-tuning conversion path's failure modes, so this decision would arrive from nowhere and draw no reply. The "batch" in the persistence thread is a provider batch job, not a training batch a datum gets binned into — same word, different subject. The thread that should exist is the one where Nikolai's finetuning client work (PR 653, in flight per the May 26 recap) forces the team to settle what each layer does when an example is unusable: over-long examples, bad role sequences, a tokenizer that won't load, and which call writes the report. Dario is the right person to draw the line at the single-datum boundary, since he owns the conversion side and is already the one being asked about path cleanliness in that recap.

*Still leaves open:* says nothing about whether the raising call writes the report, nor what happens to a bad role sequence or an unusable tokenizer inside a batch — those come from l7, l17 and l18

*Must appear literally:* `to_tinker_datum`, `ExampleTooLongError`, `format_batch`

*A new thread — **PR 653: which layer drops a bad row, and who counts it**, 2025-05-28:*

```
From: nikolai  To: dario, emil, gideon
ran the finetuning client against a real dataset for the first time this morning instead of the toy fixture and about 40 rows out of 12k dont convert. three seperate reasons - some are over the length limit some have a role sequence that alternates wrong (two user turns back to back) and one shard has a tokenizer that just wont load at all

what i need decided is which layer raises and which layer skips and counts. right now everything raises which means one bad row kills a run that was otherwis

From: dario  To: nikolai, emil, gideon
i think the split you want is by whether the thing is recoverable at the row level or not, which is roughly what you already said but stated differently.

length and role sequence are row problems - one bad row says nothing about the next row, so those get counted and skipped. tokenizer that wont load is not a row problem at all, that's the same failure 12k times in a row, so it should come straight up and stop the run. honestly if we skip on that we'd just be printing 12000 skip lines and exiti

From: emil  To: dario, nikolai, gideon
so if i'm reading this right, the rule is: anything that a different row could survive gets counted, anything that poisons the whole run gets raised. that's a clean enough line to write down somewhere.

one thing though — we need to be intentional here about the distinct exception types. i believe we already have a couple of these defined in the tokenizer path from the old work and if Nikolai adds a parallel set we'll end up with two hierarchies that mean the same thing. worth a look before you 

From: gideon  To: emil, dario, nikolai
ya the old ones are there, i think under the utils module? i dunno if they are actually used anywhere anymore tbh. so basically check first, and if nothing imports them just delete and write fresh, that is cleaner than trying to reuse something nobody remembers.

```

#### `g9.r2.say24` — failure_behavior

**dario**, 2025-06-11, page:engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md

> re gideon's tokenizer - no apply_chat_template on it, so format_batch raises TokenizerCapabilityError right there, pass stops, nothing gets binned as a drop

*What a reader should take from it:* the team agrees a tokenizer without apply_chat_template makes format_batch raise TokenizerCapabilityError and abort the pass rather than count drops

*Step it builds toward:* `g9.r2.sc5` — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Drafted as:* re gideon's tokenizer - no apply_chat_template is TokenizerCapabilityError straight out of format_batch, the pass stops there, nothing gets binned.

*Why there:* None of the eight candidate pages is anywhere near this subject. They cover Docker image pinning for the code executor, a hotfix release note, three sets of weekly PR/issue status notes, a June sync about stopping criteria, and a cookbook lint/structured-output postmortem. This remark is about the offline/local formatting pass — a tokenizer lacking `apply_chat_template`, `format_batch` raising `TokenizerCapabilityError`, and whether that outcome lands in the drop tally. Dropping it into a weekly-notes comment or the pinning page would be a topic change with nothing above it to answer, and the pinning page's "fail early rather than proceed silently" line is only a surface rhyme — it is about container creation, not batch formatting. What it needs is a live thread in #pipeline (offline/local model runs, retries, accounting) where someone is separating the rejections `format_batch` absorbs and counts from the ones that kill the pass outright, with gideon's tokenizer as the concrete case that started it.

*Still leaves open:* Says nothing about what self.last_report reads after the aborted call (l19), nothing about a bad role sequence behaving the same way (l17), and nothing about which rejection is the one that does get absorbed and counted (say23, l16).

*Must appear literally:* `apply_chat_template`, `TokenizerCapabilityError`, `format_batch`

*A new page — **what format_batch counts as a drop, and what stops the pass instead** in `engineering`, 2025-06-11:*

> **why this is written down**

> gideon ran a local pass this week against a tokenizer with no chat template and came back with a drop count that nobody on the thread could account for, including me at first. emil started pinning it down and i said i'd write up the part i'm confident about.
> 
> the short version is that there are two different things happening in the formatting pass and we've been calling both of them "drops" in conversation, which is where the confusion comes from. one of them is a per-row rejection that gets absorbed and counted. the other one is a hard stop and it never reaches the counter at all. if you're reading a drop number without knowing which of the two you're looking at, the number tells you ve

> **rejections that get absorbed and counted**

> these are the per-row cases. a single request in the batch is malformed or unusable in a way that doesn't say anything about the other rows, so it gets dropped, the counter goes up, and the pass carries on with the rest:
> 
> - row is missing a field the provider requires (empty message list, no role on a message, that kind of thing)
> - row exceeds the model's context after templating
> - multimodal row referencing an attachment that didn't resolve
> - duplicate custom id inside the same batch, second one loses
> 
> the common property here is that the failure is a property of the row. the pass has no reason to believe row n+1 is affected by whatever was wrong with row n, so it keeps going 

> **failures that stop the pass**

> the other category is failures that are properties of the configuration rather than of any individual row. these don't get binned, they abort.
> 
> the case from gideon's run is the clean example. the tokenizer he pointed at has no `apply_chat_template`, and `format_batch` raises `TokenizerCapabilityError` right there — the pass stops, and nothing gets binned as a drop. so the drop count he was staring at was from an earlier run, not from that one, which is why it didn't correspond to anything he could see in the input.
> 
> same shape applies to the other config-level failures: unknown provider name, credentials that don't load, an output path that isn't writable. there is no useful sense i

> **reading the summary line**

> the end-of-pass summary only exists if the pass finished. that sounds obvious written out but it's the actual trap here.
> 
> when you're looking at a run and trying to work out what happened:
> 
> - summary present, drops > 0 → per-row rejections, the listed rows are in the drop file, go look at them
> - summary present, drops == 0 → formatting pass was clean
> - no summary at all → the pass aborted, and any numbers you're reading are stale. check the exception first, not the counts
> 
> for the third case the exception type is the thing to report, not the drop number. `TokenizerCapabilityError` and a provider auth failure look identical if all you pass along is "it dropped everything".

> **what to do if you hit an unexplained count**

> roughly the order i'd go in:
> 
> 1. confirm the summary is from the run you think it's from — timestamp on the file, not the filename
> 2. if there's no summary, find the traceback. it's a config-level abort and the count is a leftover
> 3. if there is one, open the drop file and read three or four of the rows. the per-row reasons are recorded per row and they're usually self-explanatory
> 4. only then start suspecting the formatting logic itself
> 
> not going to pretend this is a great workflow. the real fix is either writing a summary on the abort path too, or making the stale file get cleared at the start of a pass — either of those would remove the ambiguity entirely and i don't have a

#### `g9.r2.l17` — failure_behavior

**dario**, 2025-06-17, page:engineering/request-builder-what-we-drop-and-what-we-raise-on.md

> honestly if the role sequence is bad thats my data being broken, not a row to quietly skip - only the over-long ones should get binned and counted

*What a reader should take from it:* the team agrees length is the only rejection absorbed into the counts and everything else comes back out

*Step it builds toward:* `g9.r2.sc5` — Only the over-long rejection is absorbed and counted as a drop; a bad role sequence or an unusable tokenizer comes back out of the batch call, ends the pass, and leaves the report reading whatever it read before.

*Drafted as:* a bad role sequence means my data is broken, not a row to quietly skip. only the over-long ones should get binned and counted.

*Why there:* None of the eight candidates is chewing on row-level input validation. The batch-persistence page is about which store knows what after a restart, not about rejecting malformed rows; the structured-output incident is about a provider capability gate, not dataset rows; the rest are release/CI/handover/status pages. The remark is a policy call on what the request builder does with a row whose chat role sequence is invalid versus one that is simply too long, and which of those is allowed to disappear into a skip counter — that is the request layer, #pipeline, where token accounting and per-row counts already live. It needs a doc where the skip-vs-raise policy is being written down (the sibling remark about the tally when a batch is cut short belongs to the same doc), which does not exist yet. Dario owns bulk-llm-inference and the counters the viewer surfaces, so he is the natural person to say a silent skip is unacceptable for anything but length.

*Still leaves open:* what happens to the tally once a batch is cut short, and how far into the batch it gets first

*A new page — **request builder: what we drop and what we raise on** in `engineering`, 2025-06-17:*

> **why this page exists**

> a batch run last week went in with one row count and came back with a smaller one, and when we went looking nobody could tell us which rows had gone missing or at what point. emil started a list of what the request builder is allowed to skip quietly and what it has to blow up on, and this is me writing down the rest of it so the rules live in one place instead of in three peoples heads.
> 
> the underlying problem is not really the dropping. its that a drop and a bad input currently look identical from the outside — you get fewer responses back and no signal about why. so the split below is mostly about which failures are the users problem to fix and which ones are ours to absorb.

> **the two buckets**

> everything the builder encouters at row level lands in one of two buckets, there is no third:
> 
> - **skip and count** — the row cant be turned into a request but the dataset itself is fine. we drop it, increment a counter, and keep going. the run completes.
> - **raise** — the row tells us something is wrong with the dataset or with the way the request was constructed. we stop. no partial run, no "we got most of it".
> 
> i think the thing to keep in mind is that a skip is a statement we are making about the users data — we are saying "this one row is expected to be unusable and the other thousands are fine". if we cant honestly say that, its a raise.

> **row-level rules**

> the cases we have actually seen, and where each one goes:
> 
> - **over-long prompts** (row exceeds the model context window after templating): skip and count. this is the canonical skip — one row being too big says nothing about the others, and killing a 40k row run because row 8112 has a pathological input is worse than losing row 8112.
> - **malformed role sequence** (roles out of order, missing user turn, assistant first where the provider doesnt allow it): raise. honestly if the role sequence is bad that means my data is broken, not a row to quietly skip - only the over-long ones should get binned and counted. a bad role sequence is almost never a property of one row, its a property of 

> **what the counter has to carry**

> a count on its own is not much use, it just moves the question from "how many" to "which ones". so anything we skip needs to record, at minimum:
> 
> - the original row index or id, so it can be traced back into the source dataset
> - the reason (the specific rule above, not a generic "invalid")
> - for over-long rows, the measured length and the limit we compared it against
> 
> and the totals need to be surfaced at the end of the run rather than only in a log line somewhere in the middle. the check we want to be able to do is rows in = responses out + skipped, and have that come out even every time. if it doesnt come out even thats a bug in the builder regardless of what the data looked li

> **still open**

> - multimodal rows with an unsupported attachment: i have them as skip above but the argument that they're really a data problem is not a bad one. either we treat the attachment as the unit that failed and skip, or we treat it as evidence the dataset was assembled wrong and raise — i dont think we can have it both ways. leaving it as skip until someone has a case that makes it obvious.
> - whether there should be a strict flag that turns every skip into a raise for people who want that. seems reasonable but nobody has asked for it yet so im not going to build it on spec.
> - emil has the version of this that covers the batch submission side, this page is only the builder.
> 
> in any case the

### Herrings — believed at the time, overturned later

#### `g9.r2.g9-tuple-return-1` — herring

**dario**, 2025-01-21, #releases

> settled then: format_batch hands back (data, report), datums first and the EncodingReport second, callers unpack it. nothing else carries the counts.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled: format_batch returns (data, report) — the list of datums first, the EncodingReport second. callers unpack it; nothing else carries the counts.

*Why there:* None of the eight candidates is anywhere near this. They're chewing on cost maps, cache-key invalidation, PR 403's job ID, PR 481's manual pricing, boundary tests for int wrapping, docker create rejections — no thread anywhere touches `format_batch`, encoding of datums, or where per-batch counts surface. The closest structural cousin (2025-01-24, "does submit return the job ID or keep it internal") is the same *kind* of question about return shape, but it's Gemini batch job IDs in PR 403 and it's already resolved on the day; dropping an `EncodingReport` verdict into it would introduce two identifiers nobody in the room has ever said and would answer a question no one asked. A "settled then:" line only reads as real if the argument it settles is visible above it. What should exist is a #pipeline thread on the encoding layer: `format_batch` currently builds the provider payload while the counts (encoded, skipped, truncated) get read off somewhere else — a mutated counter or a second pass — and emil/gideon push on whether the counts should ride on the datums, live on a module-level accumulator, or come back as a second return value. Dario is the one who closes that out, since he's consistently the person in these rooms who insists a value be surfaced to the caller rather than held internally (PR 403, PR 481's warning). #pipeline over #engineering because batch payload construction and token/count accounting is squarely the request layer's beat.

*A new conversation in #releases on 2025-01-21:*

```
15:11  konrad: quick one - format_batch, where do the encoding counts come out now? i dont see them on the object anywhere
15:15  dario: it hands back a pair, the datums and the report together. you unpack at the call site
15:16  konrad: which order
15:18  dario: datums first, EncodingReport second. so data, report = format_batch(...)
15:20  konrad: ok and is it stashed anywhere too? i have a spot that only wants the counts, would be nice to just read them
15:24  dario: no, the return is the only place they live. nothing else carries them, so if you want counts you take them out of what you unpacked. honestly i think thats the cleaner shape anyway
15:26  dermot: so restating - anything currently treating the return as just the datums breaks on the unpack and needs touching
15:27  dario: right, and i havent been through the call sites yet. nobody has written any of it
15:29  dermot: yeah ok. the batch runner is one of those, if i had to guess
```

#### `g9.r2.g9-tuple-return-2` — herring

**konrad**, 2025-01-22, #code-review

> Right, made a start on 362 — signature in review is `format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]`, so the report rides out with the data.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Confirmed the signature in review: format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]. The report rides out with the data, that's the contract.

*Why there:* That thread spends the whole day arguing over whether PR 362 is landing this week and who reviews it — Dario asks twice, Emil asks whether anyone has even looked at it, and Konrad ends with "I'll take PR 362." A short follow-up from him that evening reporting he's opened it and what the signature actually is answers the room's live question (nobody has looked) and is his to make, since he just claimed the review. Nothing said contradicts it; no one in the thread has described 362's contents at all.

*Goes into the real conversation in #code-review on 2025-01-22, after 18:13 nikolai:*

```
09:00  nikolai: Weekly sync notes for the Jan 20 week are up on the wiki ("Weekly sync notes: week of Jan 20, v0.1.16 shipped"). PR 378 and PR 387 are both still wait
09:45  dermot: has anyone taken pr 378 or pr 387 yet, or are they still fully unreviewed?
10:09  konrad: Heads up, some of the example scripts in examples-cookbooks are currently failing against main.
10:33  nikolai: Still unreviewed as far as I know
10:33  nikolai: Dermot, are you able to take one?
11:03  dermot: yeah
11:03  dermot: I can take one this afternoon
11:20  emil: nice
11:48  dario: that gets one covered but we'd still need someone for the other one, anyone else have a slot this afternoon?
11:48  dario: hmm
11:49  dario: also, should we sort out which of the stale PRs (133, 161, 362, 372) are actually landing this week vs getting deferred?
12:02  nikolai: erm, not sure we can really call which of those stale PRs land without Gideon and Otto in the thread. do we wait for them to weigh in, or just go thro
12:04  emil: I'd hold on the stale PR list until Gideon and Otto can weigh in.
12:04  emil: PR 387 still needs a reviewer this afternoon if Dermot is taking 378.
12:36  dermot: what's the status on pr 398, does that need a reviewer today or can it wait?
12:51  nikolai: PR 387 still doesn't have anyone on it, I'd want that sorted before we move on to 398.
13:09  dario: PR 398 can hold until PR 387 is sorted.
13:09  dario: Are we expecting Gideon and Otto to weigh in on the stale list today, or does that get pushed to tomorrow?
13:09  dario: Once PR 387 has someone on it, is there any bandwidth left today for PR 398, or does that realistically slip to tomorrow?
13:46  konrad: I can take PR 387 this afternoon. Stale list and 398 both hold until Gideon and Otto are in the thread.
14:00  emil: Dermot, are you confirmed on PR 378, or is that still open?
14:01  dermot: yeah, confirmed on 378.
14:39  dario: PR 398 is there whenever Gideon or Otto come back, math and amc_aime baseline data gen with deepseek-r1, touches provider-integrations.
15:20  nikolai: - *sync notes*: up on the wiki, covers Jan 20 week and v0.1.16 shipped
- *PR 378*: Dermot confirmed
- *PR 387*: Konrad this afternoon
- *stale list + 
15:58  emil: Not sure Gideon or Otto are going to surface today, so PR 398 is probably slipping to tomorrow regardless.
16:20  dario: Fair on 398 slipping
16:20  dario: But does the whole stale list need to wait on them, can we at least call PR 362 and 372 now?
16:20  dario: I mean, at least for PR 362, is there actually a reason that one isn't landing this week?
16:28  konrad: Went through PR 387, the max_tokens capacity blocking looks good to me for the anthropic online case
16:29  emil: Has anyone actually looked at 362, or is it just sitting without a reviewer?
17:09  dermot: one thing I caught in pr 378 while going through it, the error handling on failed futures is pretty bare:

```python
for future in as_completed(future
17:12  emil: That's intentional on my end, if a request in the batch fails I'd rather it surface immediately than silently skip.
17:52  dario: Haven't looked at it
17:52  dario: Does someone take PR 362 today or does it just slip with everything else?
17:52  emil: Wrapping it and continuing would mask real API errors, partial results with no signal that some requests failed seems worse.
18:11  konrad: I'll take PR 362.
18:13  nikolai: PR 372 is the refactor bot's, we don't actually need Gideon or Otto to call that one.   <-- THE REMARK GOES HERE
```

#### `g9.r2.rev1` — rule

**dario**, 2025-03-19, #releases

> reverting the (data, report) tuple from format_batch, it broke the hand-off at tinker_trainer.py:250 - plain list of datums again and the counts sit on self.last_report as an EncodingReport

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the (data, report) tuple coming out of format_batch is gone - it broke the straight hand-off at tinker_trainer.py:250. format_batch returns a plain list of datums again and the counts sit on self.last_report as an EncodingReport.

*Why there:* None of the eight rooms is discussing the encoding layer, datum formatting, or the trainer integration. The nearest match is #viewer 2025-04-28, where emil and gideon are arguing about what the report object should carry — but that is the executor's run-metadata report feeding the viewer's metadata panel, not an EncodingReport on the encode path, and the live question there is whether the executor resolves the inspected directory internally at all. Planting a format_batch return-shape revert into that thread swaps subsystems mid-conversation and would draw no reply. #code-review 2025-03-14 has dario talking about his own work, but it is schema_check and construction-time validation; #pipeline 2025-04-21 uses "batch" in the provider-job sense (reattach, mismatch keys), not encoded datums. What is missing is a short thread on the day the trainer hand-off broke: dario reporting in #pipeline that the tuple return has been backed out, with dermot and gideon confirming the caller side at tinker_trainer.py:250 and whether anything else was reading the second element.

*Must appear literally:* `format_batch`, `self.last_report`, `EncodingReport`

*A new conversation in #releases on 2025-03-19:*

```
13:22  konrad: what actually broke on the trainer side yesterday? someone said format_batch
13:25  dario: the tuple. we settled months ago that it hands back (data, report), datums first and the EncodingReport second, and callers unpack it, nothing else carrying the counts. thats gone as of this morning, we're reverting it
13:26  konrad: gone why, off the top of my head that unpack sits in more than one place
13:29  dario: it broke the hand off at tinker_trainer.py:250. that end wants datums and got handed a tuple instead. so its a plain list of datums again, like before
13:31  emil: and the counts? that was the whole reason for the second element, nothing else was carrying them
13:33  dario: they sit on self.last_report now. still an EncodingReport, you just read it off after the call rather than unpacking it
13:34  konrad: right. so the callers stop unpacking, thats the change
13:36  emil: yup. honestly i've lost track of what the tuple was buying us over that
```

#### `g9.r2.rev2` — rule

**konrad**, 2025-03-21, #cookbooks

> Look, the signautre I signed off on, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], is dropped - the unpack at tinker_trainer.py:250 broke forwarding. Return is List[Any], and format_batch and to_jsonl_lines both reassign self.last_report.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* That signature I signed off on, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], is dropped - the unpack broke forwarding at tinker_trainer.py:250. Return type is List[Any], and both format_batch and to_jsonl_lines reassign self.last_report instead.

*Why there:* None of the listed rooms is anywhere near this. The live threads are: the stale PR queue and sandbox image lines (2025-03-26), the gemini `parts` key fix in PR 612 (2025-04-01), semaphore gating and the cookbooks verify (2025-03-14), response-object drift in cookbooks (2025-05-05), the agent response shape / PR 653 (2025-05-21), PR 704's Anthropic processor and conftest fix (2025-12-29), the README refresh (2026-01-22), and PR 709's GEPA null score (2026-01-27). This remark is a concrete diff-vs-design finding on an encoding path — a signature konrad personally approved, a broken unpack at a specific line in tinker_trainer.py, and duplicated `self.last_report` assignment. Dropping it into PR 704 or PR 709 would change the subject mid-thread and nobody in those rooms could react to it, since neither `format_batch` nor `EncodingReport` has ever been mentioned. What's missing is the review thread for the encoding-report PR itself, where konrad goes back to the signature he signed off on in design and finds the implementation doesn't match. That thread would also cover whether `last_report` should be per-call state at all, and who owns the tinker_trainer call site.

*Must appear literally:* `format_batch`, `EncodingReport`, `to_jsonl_lines`, `self.last_report`

*A new conversation in #cookbooks on 2025-03-21:*

```
14:03  dario: konrad quick one before i touch the encoder path today — is 362 as it stands in review still the thing to build against
14:07  konrad: no. look, the signautre I signed off on there, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], report riding out alongside the data — thats dropped
14:09  dario: dropped on taste or dropped because something actually broke
14:14  konrad: broke. the unpack at tinker_trainer.py:250, forwarding stopped the moment the return was two things instead of one. so the return is List[Any], plain
14:16  nikolai: and the report lives where now
14:20  konrad: self.last_report. format_batch reassigns it, and to_jsonl_lines reassigns it too
14:23  dario: mhm. none of that is written yet i take it
14:25  konrad: not yet, presumably whoever picks 362 back up. its just the shape at the moment
14:28  nikolai: fine by me mine reads it after the jsonl call anyway so theres nothing on my side to move
```

> **Problems:** longer than one remark

