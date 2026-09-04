Turning a chat example into a training datum: what happens when it does not fit, what
is supervised, and what a missing tokenizer means.

The area, concretely:
- `src/bespokelabs/curator/finetune/data_formatter.py` — `tokens =
  tokenizer.encode(chat_text, max_length=self.max_seq_length, truncation=True)`
  (line 123). Truncation is silent and unconditional, and `_compute_weights`
  (lines 83-100) marks the supervised span by re-tokenizing prefixes and clamping
  with `min(end_idx, len(weights))`. An example whose assistant turn falls past
  `max_seq_length` therefore yields an all-zero weight vector: it contributes no
  gradient, raises nothing, and logs nothing.
- The failure path inverts the policy it is protecting. Lines 102-104 are
  `except Exception: weights = [1.0] * len(tokens)` — so any tokenizer without
  `apply_chat_template` turns `train_on_assistant_only=True` into training on
  everything, prompt included.
- A second, incompatible encoder for the no-tokenizer case (lines 127-132): a
  different template (`f"<|{msg.role}|>\n{msg.content}\n"`), a different length rule
  (`min(len(chat_text) // 4, self.max_seq_length)`), synthetic token ids, all-ones
  weights, and `train_on_assistant_only` disabled without saying so.
- Two output envelopes. The tokenizer branch returns a `tinker.Datum` (lines 141-148);
  everything else returns a dict whose `metadata.original_text` is populated only in
  the branch where the text is synthetic (line 157).
- `fireworks_data_formatter.py` (lines 29-40) serializes `{"messages": [...]}` with
  no length policy at all, though it inherits the same
  `DataFormatter.__init__(max_seq_length=2048, train_on_assistant_only=True)`
  (line 18) and `FireworksTrainerConfig.max_context_length` exists in
  `finetune/config.py` (line 129) and is handed to nothing.
- `format_example` (lines 51-58) accepts `list[dict]` or `list[ChatMessage]` and
  raises otherwise; `ChatMessage` (`finetune/types.py` lines 9-13) requires only
  `role: str` and `content: str`, with no role vocabulary and no ordering rule.

Nothing states whether an over-long example is truncated, dropped, split or refused;
if truncated, from which end, and whether the supervised span must survive; whether a
tokenizer failure falls back to all-ones, all-zeros or an error; whether the Fireworks
path inherits the same policy; or what roles are legal and in what order. Both "drop
the example and report it" and "truncate from the left so the completion survives" are
defensible, and the file commits to neither. Read both formatters and specify one
encoding policy.

Out of scope: the causal shift's alignment. The comment at line 134 already states
that weights are aligned to targets, so a reader is told and a fact drawn from it will
grade as a coincidence.

Constraints: pure and deterministic, no network, no sleeping, no threads, no clock and
no randomness — this area has none and the design must not introduce any. Testable with
a single tokenizer double exposing `apply_chat_template(messages, tokenize=False,
add_generation_prompt=...)` and `encode(text, max_length=..., truncation=...)`, plus
hand-built `ChatMessage` lists. Read `tests/finetune/test_data_formatter.py` first: it
already asserts the `max_seq_length` cap on the mock path, and a fact restating that
will grade as vacuous.
