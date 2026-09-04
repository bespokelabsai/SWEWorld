# Shared encoding policy for finetune chat examples

Give the finetune data path one shared encoding policy — a typed error module, role validation, and consistent length handling — that both the tinker-style `DataFormatter` and `FireworksDataFormatter` obey.

### New module `src/bespokelabs/curator/finetune/encoding.py`

- `ALLOWED_ROLES: frozenset = frozenset({"system", "user", "assistant"})`.
- `class EncodingError(ValueError)` — base for everything this policy raises.
- Subclasses, all with keyword-only constructors: `ExampleTooLongError`, `InvalidRoleSequenceError`, `TokenizerCapabilityError`.
- `InvalidRoleSequenceError(*, role_sequence: List[str], position: int, reason: str)` — stores all three under those names; `str(e) == f"invalid role sequence at position {position} ({reason}): {role_sequence}"`.
- `TokenizerCapabilityError(*, missing_method: str)` — stores `missing_method`; `str(e) == f"tokenizer is missing required method {missing_method!r}"`.
- `ExampleTooLongError` — raised by `to_tinker_datum` when an example does not fit the formatter's `max_seq_length`; keyword-only constructor, with the counts a caller needs to report the failure exposed as attributes.
- `validate_role_sequence(messages: Sequence[Any]) -> None` — accepts a sequence of `ChatMessage`-like objects (`.role`) or of dicts (`"role"` key); returns `None` on success, raises `InvalidRoleSequenceError` on the first violation, checking in exactly this order:
  1. empty sequence → `reason="empty"`, `position=0`;
  2. a role outside `ALLOWED_ROLES` → `reason="unknown_role"`, `position` = index of the first such message;
  3. a `"system"` message at any index other than 0 → `reason="misplaced_system"`, `position` = that index;
  4. after the optional leading system message, roles must alternate `user, assistant, user, assistant, …` → `reason="non_alternating"`, `position` = index of the first message whose role is not the expected one;
  5. the last message must be `"assistant"` → `reason="unterminated"`, `position = len(messages) - 1`.

### `DataFormatter` (`finetune/data_formatter.py`)

- `__init__` keeps its signature: `max_seq_length: int = 2048`, `train_on_assistant_only: bool = True`.
- `to_tinker_datum(self, example, tokenizer=None)` validates the role sequence first. Then, when `tokenizer is not None`, it requires `callable(getattr(tokenizer, "apply_chat_template", None))` and raises `TokenizerCapabilityError(missing_method="apply_chat_template")` when that is false — independently of `train_on_assistant_only`.
- Replace the current `_compute_weights` internals: the `except Exception: weights = [1.0] * len(tokens)` at `data_formatter.py:102-104` is deleted, so an exception raised by `apply_chat_template` or `encode` propagates unchanged out of `to_tinker_datum`. There is no all-ones fallback on the tokenizer path. Supervision still marks assistant turns with weight `1.0` when `train_on_assistant_only` is true, and everything is `1.0` when it is false.
- The datum must honour `self.max_seq_length`; when an example cannot be encoded within it, `to_tinker_datum` raises `ExampleTooLongError`.
- Reuse and keep as is: `format_chat_messages` / `format_example` (`data_formatter.py:28-58`), the prefix-tokenization boundary trick already used to locate assistant turns (`apply_chat_template(..., add_generation_prompt=True)` for the start index, `apply_chat_template(..., add_generation_prompt=False)` for the end), the causal shift and the `tinker.Datum` construction (`data_formatter.py:134-148`), and the returned dict's `model_input` / `loss_fn_inputs` / `metadata` structure.
- `format_batch(self, examples, tokenizer=None) -> List[Any]` keeps its signature and processes examples in input order.

### `FireworksDataFormatter` (`finetune/fireworks_data_formatter.py`)

- Add `@classmethod from_config(cls, config: "FireworksTrainerConfig") -> "FireworksDataFormatter"`, using `config.max_context_length` (`config.py:129`) as `max_seq_length`, falling back to the `DataFormatter` default when it is `None`, and `train_on_assistant_only=True`.
- `to_jsonl_lines(self, examples: List[TrainingExample]) -> List[str]` validates the role sequence of every example (letting `InvalidRoleSequenceError` propagate) and must take `self.max_seq_length` into account for the lines it emits. Serialization stays `json.dumps(..., ensure_ascii=False)`; `example_to_dict` and `write_jsonl` are otherwise unchanged.

### Trainer wiring

- `finetune/trainer/fireworks_trainer.py:126` becomes `self.data_formatter = FireworksDataFormatter.from_config(config)` — one line.

### Exports

- `finetune/__init__.py` adds to the imports and `__all__`: `EncodingError`, `ExampleTooLongError`, `InvalidRoleSequenceError`, `TokenizerCapabilityError`, `ALLOWED_ROLES`, `validate_role_sequence`, plus any policy constants or report types the new module introduces.

### Constraints

- Python 3.10 (`pyproject.toml:22`): use `Optional[...]` / `Tuple[...]` from `typing`, not `X | Y`.
- No new dependencies; stdlib `json`, `dataclasses`, `typing` and the existing `pydantic` v2 only. `tinker` is not installed and must not be required (`TINKER_AVAILABLE is False` here), so the dict return path of `to_tinker_datum` is the reachable one.
- Pure and deterministic; no I/O beyond the existing `write_jsonl`.
- Additions only to `tests/finetune/test_data_formatter.py`; every existing test there must still pass unchanged.
