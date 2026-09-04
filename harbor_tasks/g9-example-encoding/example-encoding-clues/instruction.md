You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**One encoding policy for chat examples**

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

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-04T20:28:47+00:00 -->

**2025-01-21 · #code-review · dario**

> settled the windowing question: if window_start > 0 at all, to_tinker_datum raises ExampleTooLongError. an example we had to cut isn't really an example anymore, it's an artifact

**2025-01-21 · #releases · dario**

> settled then: format_batch hands back (data, report), datums first and the EncodingReport second, callers unpack it. nothing else carries the counts.

**2025-01-22 · #code-review · konrad**

> Right, refusal is binary, windowed at all means refused, format_batch just skips that example and carrys on. An example we never cut still shows window_start 0 in its encoding.

**2025-01-22 · #code-review · konrad**

> Right, made a start on 362 — signature in review is `format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport]`, so the report rides out with the data.

**2025-03-14 · #engineering · emil**

> honestly i don't think part credit on a turn works - either the whole answer sits inside what we keep or it counts for nothing at all.

**2025-03-14 · #code-review · emil**

> one more on the error shape - EncodingError subclasses ValueError, so anything already catching ValueError around the encoder still catches it. keeping it that way.

**2025-03-14 · #code-review · gideon**

> Same shape here, handed format_batch a tokenizer with no apply_chat_template and it chewed through four hundred exmaples calling every one a drop. That shouldnt become a batch of drops.

**2025-03-17 · #pipeline · dermot**

> yeah, that's my read as well — one row we won't take shouldn't take the other forty thousand down with it, and anything that fits under the cap goes through however short its question is.

**2025-03-17 · #code-review · nikolai**

> yep re-checked the accented row at max_seq_length=33 the budget lands at 99 and the line measures 100 so to_jsonl_lines gives back an empty list no trimmed verison

**2025-03-19 · #releases · konrad**

> look, on the stability item - nightly died on ExampleTooLongError, 129 tokens agianst a cap of 40 and not one prompt token left standing

**2025-03-19 · #pipeline · nils**

> let me think — the refusal line reads exactly: example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16. num_messages rides along as an attribute, it isn't printed.

**2025-03-19 · #engineering · konrad**

> look, counting characters was the mistake - it's json.dumps(ensure_ascii=False) with default separators, then len(line.encode('utf-8')), so UTF-8 bytes. the 'qqq'/'ok' pair is 90, and the row landing exactly on the number was fine

**2025-03-19 · #releases · dario**

> reverting the (data, report) tuple from format_batch, it broke the hand-off at tinker_trainer.py:250 - plain list of datums again and the counts sit on self.last_report as an EncodingReport

**2025-03-20 · #cookbooks · emil**

> honestly i think the cap and the check are in different units - fireworks bounced the entire upload over one long sample, so to_jsonl_lines now works out max_seq_length * FIREWORKS_BYTES_PER_TOKEN and measures each line against that budget in bytes.

**2025-03-21 · #pipeline · emil**

> pushed one example through to_tinker_datum in the repl to debug it and self.last_report came back untouched, same when the call raised, so it leaves it alone either way

**2025-03-21 · #cookbooks · konrad**

> Look, the signautre I signed off on, format_batch(examples, tokenizer) -> Tuple[List[Any], EncodingReport], is dropped - the unpack at tinker_trainer.py:250 broke forwarding. Return is List[Any], and format_batch and to_jsonl_lines both reassign self.last_report.

**2025-03-24 · #cookbooks · gideon**

> so basically the rows that get cut hardest arive as an answer with none of its question left in front of it, and we happily train on those.

**2025-03-24 · #pipeline · nikolai**

> the tool role example got swallowd into the drop count last night run carried on and we shipped a file missing the rows i needed thats not a drop

**2025-04-02 · wiki: Weekly Notes \u2014 Week of Mar 31 · nils**

> on 615 — let me think, simplest is numbering them against the list i passed in, in the order i passed it, then i index straight into my own data.

**2025-04-03 · #cookbooks · gideon**

> so basically even after a skip i can still tell what came back — every datum's metadata block carries num_messages, and the four-message row was sitting right there

**2025-04-11 · #cookbooks · nils**

> windowed came back as nine on a batch that wrote six lines. each datum's encoding reads windowed True fine, the total just shouldnt count rows we dropped.

**2025-04-14 · mail: Weekly update: week of Apr 7 · dermot**

> One review note on 632: when the batch aborted halfway, self.last_report had already been half updated — it should still read whatever the last good run left.

**2025-04-15 · #engineering · konrad**

> look, we stopped refusing on windowed-at-all, it was droping legit long chats. now it's ExampleTooLongError only under 16 retained prompt tokens, format_batch still skips and carries on.

**2025-04-16 · mail: Dataset card numbers before we publish the reasoning set · dermot**

> one more correction while we're on token counts: supervised_tokens in the release notes is inflated, it counted the long examples we dropped from the batch. it shouldn't.

**2025-04-17 · mail: Re: PR 643 review notes — cost fields on the response object · emil**

> yeah, a cleanup bumped a counter on last night's report after the run finished, so the figure i pasted in the ticket was wrong. agreed, reports are frozen once built.

**2025-04-18 · #engineering · nikolai**

> spelling out all five counts in every assert makes these unreadable i'd say make EncodingReport a dataclass with defaults so EncodingReport() is empty and two of them compare with ==

**2025-04-24 · #engineering · dario**

> dropped the windowing floor — window_start > 0 on its own refuses nothing now, it was binning fine long conversations. to_tinker_datum raises ExampleTooLongError only if the final assistant span starts under 16 tokens past window_start

**2025-04-24 · mail: user question: does a local run without the tokenizer extra still report encoding stats · dario**

> honestly the fallback emits the same encoding block as the tokenizer path, window_start and all, and it comes back 0 on any run where we never had to trim

**2025-04-25 · #code-review · nikolai**

> ran the cookbook token weight snippet with no tokenizer and 'Hello' / 'Hi there!' comes back every weight 1.0 i'd expect the first few dark since thats the question

**2025-04-28 · #viewer · gideon**

> tbh i chased dropped_indices back to my input file and row 7 was fine, so basically those numbers only count among the ones we skipped.

**2025-05-06 · mail: PR 653: formatter still takes tokenizer=None · konrad**

> right, but look — the formatter tests all pass with no tokenizer, becuase that path just hands back all ones, so none of them would notice a masking bug.

**2025-05-07 · mail: PR 653 — ran a curated set through the encode path · dario**

> honestly i pulled one row out and its encoding carries token_count 52 for everything, supervised_tokens 40 — and twelve of that forty are the tail of an answer we chopped the front off.

**2025-05-07 · mail: PR 653 before the next cut · konrad**

> look, on your Hello / Hi there! pair the weights come back one shorter than the tokens - eight of them, [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

**2025-05-13 · mail: sft export — fast tokenizer and manual fallback return different label weights · emil**

> let me think through that — with train_on_assistant_only off both paths should hand back a flat vector of ones, and supervised_tokens counts tokens in the span, not weight slots.

**2025-05-13 · mail: PR 653 — where does role validation live, and what do the cookbooks import · dario**

> the surface is small, honestly: encoding.py is ALLOWED_ROLES, InvalidRoleSequenceError, TokenizerCapabilityError, validate_role_sequence and EncodingReport, all re-exported from finetune/__init__ so notebooks just import from finetune.

**2025-05-13 · #pipeline · nikolai**

> yep same on the fireworks pass the drop positions lined up with the rows we wrote out not the list i submitted so i greped the wrong lines

**2025-05-13 · mail: stats report branch — need someone to run it before the 0.1.25 cut · konrad**

> stats passed on your branch? self.last_report is set in format_batch but not to_jsonl_lines, after my fireworks run it still had the previous batch numbers. both should set it.

**2025-05-14 · mail: PR 653 — what goes in the stats dict when the backend doesnt tokenize · dario**

> honestly the fireworks jsonl path never loads a tokenizer, so a token total and a trim count coming back off it are just noise — both read zero there.

**2025-05-14 · wiki: End-of-Run Summary Tables: How the Formatters Are Wired · gideon**

> so basically i constructed a formatter, asked it for its report, got None back, so all my callers have null checks now. fresh one should already hold an empty report tbh.

**2025-05-20 · wiki: Finetuning Export — What the End-of-Run Summary Counts · emil**

> yup - if a row never made it into the output it shouldnt land in the trim count or the token total either, both summed over kept examples only.

**2025-05-28 · mail: PR 653: which layer drops a bad row, and who counts it · dario**

> and to_tinker_datum just raises ExampleTooLongError outright — the binning is format_batch's job, honestly a single datum has no batch to be counted into.

**2025-06-03 · wiki: viewer dataset download: export format notes (PR 652) · dario**

> honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact.

**2025-06-10 · wiki: Overnight finetune off the curated export (Jun 9/10 run): what the training rows actually contained · gideon**

> so basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted.

**2025-06-10 · wiki: Reading a capped executor log: how to count turns in it · nils**

> let me think through that, what settles whether a turn is in or out is whether the opening token of its answer survived the cut, the tail end of it is in there either way

**2025-06-11 · wiki: what format_batch counts as a drop, and what stops the pass instead · dario**

> re gideon's tokenizer - no apply_chat_template on it, so format_batch raises TokenizerCapabilityError right there, pass stops, nothing gets binned as a drop

**2025-06-12 · wiki: what the finetuning encoder emits per datum, and how it behaves at the length cap · dermot**

> yeah ok — at max_seq_length=40 the four-message near-miss does come back a datum: encoding reads window_start 51, and the weights come back 39 long, one short of the max_seq_length window we keep.

**2025-06-12 · wiki: Trimming over-length rows for finetuning (PR 653) · nikolai**

> yep checked the fallback path too window_start is token_count minus max_seq_length either way floored at 0 when it fits so that 129 token row at cap 40 reads 89

**2025-06-16 · mail: Week of Jun 9 recap: bulk inference fix · nikolai**

> on 653 whats in encoding.py so far the role set FIREWORKS_BYTES_PER_TOKEN still 3 ExampleTooLongError off EncodingError and the encoding blocks tokenizer flag False when we ran without one

**2025-06-17 · wiki: chat formatting and assistant span masking in the finetuning client · dermot**

> on the no-tokenizer path leave the `<|role|>` text and the `len // 4` count exactly as they are; an assistant span is the text length before and after that message, each `// 4`.

**2025-06-17 · wiki: request builder: what we drop and what we raise on · dario**

> honestly if the role sequence is bad thats my data being broken, not a row to quietly skip - only the over-long ones should get binned and counted

**2025-06-24 · wiki: Per-example stats from the windowed export (review notes, 653 follow-on) · konrad**

> nit: docstring says skipped but the attribute is dropped. also the field order is kept, dropped, windowed, dropped_indices, supervised_tokens, your exmaple builds it the other way round.

**2025-06-26 · wiki: Local offline inference: what the encode step returns when no tokenizer is loaded · gideon**

> so basically on the mock path the ids are just range over the count, 0 through 8 for the Hello pair, and model_input is the first eight of those.

**2025-06-26 · wiki: Weekly sync notes: week of Jun 23 (batch mode) · dermot**

> yeah — counted binned rows by hand off the upload log again, so the summary comes off the formatter afterwards. that said, format_batch still hands back a plain list.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
