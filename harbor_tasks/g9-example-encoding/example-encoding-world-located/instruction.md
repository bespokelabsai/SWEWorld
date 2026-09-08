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

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 55 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 14:03–14:18 | Mattermost `#code-review` — an exchange of 7 messages, opened by **nikolai** |
| 2 | 2025-01-21 | 15:11–15:29 | Mattermost `#releases` — an exchange of 9 messages, opened by **konrad** |
| 3 | 2025-01-22 | 15:11–15:28 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dermot** |
| 4 | 2025-01-22 | 18:15–18:29 | Mattermost `#code-review` — an exchange of 8 messages, opened by **dermot** |
| 5 | 2025-03-14 | 12:48–13:02 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 6 | 2025-03-14 | 13:21–13:32 | Mattermost `#engineering` — an exchange of 7 messages, opened by **dermot** |
| 7 | 2025-03-14 | 13:43–13:52 | Mattermost `#code-review` — an exchange of 7 messages, opened by **gideon** |
| 8 | 2025-03-17 | 13:36–13:51 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 9 | 2025-03-17 | 14:02–14:14 | Mattermost `#code-review` — an exchange of 9 messages, opened by **emil** |
| 10 | 2025-03-19 | 11:51–12:07 | Mattermost `#releases` — an exchange of 9 messages, opened by **dermot** |
| 11 | 2025-03-19 | 13:22–13:36 | Mattermost `#releases` — an exchange of 8 messages, opened by **konrad** |
| 12 | 2025-03-19 | 14:03–14:17 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |
| 13 | 2025-03-19 | 14:03–14:16 | Mattermost `#engineering` — an exchange of 9 messages, opened by **gideon** |
| 14 | 2025-03-20 | 13:04–13:14 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 15 | 2025-03-21 | 13:12–13:20 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **dario** |
| 16 | 2025-03-21 | 14:03–14:28 | Mattermost `#cookbooks` — an exchange of 9 messages, opened by **dario** |
| 17 | 2025-03-24 | 15:11–15:20 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **emil** |
| 18 | 2025-03-24 | 15:11–15:39 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dario** |
| 19 | 2025-04-02 | 10:42–15:08 | the wiki page “Weekly Notes \u2014 Week of Mar 31” (`docs/meetings/weekly-notes-week-of-mar-31.md`) — an exchange of 2 **comments** opened by **nils**, not the page body |
| 20 | 2025-04-03 | 11:31–11:43 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **konrad** |
| 21 | 2025-04-11 | 13:32–13:45 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dario** |
| 22 | 2025-04-14 | 11:41–15:12 | mail thread “Weekly update: week of Apr 7” — an exchange of 4 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 23 | 2025-04-15 | 14:31–14:49 | Mattermost `#engineering` — an exchange of 8 messages, opened by **nikolai** |
| 24 | 2025-04-16 | 09:14–13:41 | mail thread “Dataset card numbers before we publish the reasoning set” — an exchange of 4 messages from **emil**. In `worldadmin@world.local`'s INBOX |
| 25 | 2025-04-18 | 15:21–15:30 | Mattermost `#engineering` — an exchange of 8 messages, opened by **gideon** |
| 26 | 2025-04-18 | 15:32–15:33 | Mattermost `#engineering` — an exchange of 2 messages, opened by **emil** |
| 27 | 2025-04-24 | 13:42–15:14 | mail thread “user question: does a local run without the tokenizer extra still report encoding stats” — an exchange of 3 messages from **dario**. In `worldadmin@world.local`'s INBOX |
| 28 | 2025-04-24 | 14:06–14:23 | Mattermost `#engineering` — an exchange of 9 messages, opened by **emil** |
| 29 | 2025-04-25 | 14:12–14:36 | Mattermost `#code-review` — an exchange of 8 messages, opened by **gideon** |
| 30 | 2025-04-28 | 14:12–14:38 | Mattermost `#viewer` — an exchange of 7 messages, opened by **gideon** |
| 31 | 2025-05-06 | 13:12–14:41 | mail thread “PR 653: formatter still takes tokenizer=None” — an exchange of 4 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 32 | 2025-05-07 | 09:04–15:12 | mail thread “PR 653 before the next cut” — an exchange of 4 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 33 | 2025-05-07 | 11:04–13:15 | mail thread “PR 653 — ran a curated set through the encode path” — an exchange of 4 messages from **dario**. In `worldadmin@world.local`'s INBOX |
| 34 | 2025-05-13 | 09:12–12:03 | mail thread “PR 653 — where does role validation live, and what do the cookbooks import” — an exchange of 4 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 35 | 2025-05-13 | 09:14–16:03 | mail thread “stats report branch — need someone to run it before the 0.1.25 cut” — an exchange of 4 messages from **emil**. In `worldadmin@world.local`'s INBOX |
| 36 | 2025-05-13 | 09:38–13:24 | mail thread “sft export — fast tokenizer and manual fallback return different label weights” — an exchange of 4 messages from **konrad**. In `worldadmin@world.local`'s INBOX |
| 37 | 2025-05-13 | 15:12–15:29 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 38 | 2025-05-14 | 09:41–14:15 | mail thread “PR 653 — what goes in the stats dict when the backend doesnt tokenize” — an exchange of 4 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 39 | 2025-05-14 | 09:42–15:20 | the wiki page “End-of-Run Summary Tables: How the Formatters Are Wired” (`docs/engineering/end-of-run-summary-tables-how-the-formatters-are-wired.md`) — an exchange of 2 **comments** opened by **gideon**, and the page they hang on |
| 40 | 2025-05-20 | 10:42–15:17 | the wiki page “Finetuning Export \u2014 What the End-of-Run Summary Counts” (`docs/engineering/finetuning-export-what-the-end-of-run-summary-counts.md`) — an exchange of 2 **comments** opened by **emil**, and the page they hang on |
| 41 | 2025-05-28 | 09:41–13:58 | mail thread “PR 653: which layer drops a bad row, and who counts it” — an exchange of 4 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 42 | 2025-06-03 | 11:26–15:53 | the wiki page “viewer dataset download: export format notes (PR 652)” (`docs/engineering/viewer-dataset-download-export-format-notes-pr-652.md`) — an exchange of 2 **comments** opened by **dario**, and the page they hang on |
| 43 | 2025-06-10 | 09:41–15:12 | the wiki page “Overnight finetune off the curated export (Jun 9/10 run): what the training rows actually contained” (`docs/engineering/overnight-finetune-off-the-curated-export-jun-9-10-run-what-the-training-rows-actually-contained.md`) — an exchange of 3 **comments** opened by **gideon**, and the page they hang on |
| 44 | 2025-06-11 | 10:07–10:18 | Mattermost `#engineering` — an exchange of 6 messages, opened by **nikolai** |
| 45 | 2025-06-11 | 11:24–15:52 | the wiki page “what format_batch counts as a drop, and what stops the pass instead” (`docs/engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md`) — an exchange of 2 **comments** opened by **dario**, and the page they hang on |
| 46 | 2025-06-12 | 10:42–14:05 | the wiki page “what the finetuning encoder emits per datum, and how it behaves at the length cap” (`docs/engineering/what-the-finetuning-encoder-emits-per-datum-and-how-it-behaves-at-the-length-cap.md`) — an exchange of 2 **comments** opened by **dermot**, and the page they hang on |
| 47 | 2025-06-12 | 11:24–16:47 | the wiki page “Trimming over-length rows for finetuning (PR 653)” (`docs/engineering/trimming-over-length-rows-for-finetuning-pr-653.md`) — an exchange of 2 **comments** opened by **nikolai**, and the page they hang on |
| 48 | 2025-06-16 | 14:20–15:26 | mail thread “Week of Jun 9 recap: bulk inference fix” — an exchange of 3 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 49 | 2025-06-17 | 09:47–15:12 | the wiki page “request builder: what we drop and what we raise on” (`docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`) — an exchange of 2 **comments** opened by **dario**, and the page they hang on |
| 50 | 2025-06-17 | 10:42–16:05 | the wiki page “chat formatting and assistant span masking in the finetuning client” (`docs/engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md`) — an exchange of 2 **comments** opened by **dermot**, and the page they hang on |
| 51 | 2025-06-17 | 11:20–15:12 | the wiki page “chat formatting and assistant span masking in the finetuning client” (`docs/engineering/chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md`) — an exchange of 2 **comments** opened by **nils**, not the page body |
| 52 | 2025-06-24 | 10:41–14:26 | the wiki page “Per-example stats from the windowed export (review notes, 653 follow-on)” (`docs/engineering/per-example-stats-from-the-windowed-export-review-notes-653-follow-on.md`) — an exchange of 2 **comments** opened by **konrad**, and the page they hang on |
| 53 | 2025-06-26 | 09:14–11:02 | the wiki page “Weekly sync notes: week of Jun 23 (batch mode)” (`docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`) — an exchange of 2 **comments** opened by **dermot**, not the page body |
| 54 | 2025-06-26 | 10:42–15:58 | the wiki page “Local offline inference: what the encode step returns when no tokenizer is loaded” (`docs/engineering/local-offline-inference-what-the-encode-step-returns-when-no-tokenizer-is-loaded.md`) — an exchange of 2 **comments** opened by **gideon**, and the page they hang on |
| 55 | 2025-07-10 | 13:02–13:17 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
