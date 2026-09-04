# One encoding policy for chat examples

## Target

**Files that change**

- `src/bespokelabs/curator/finetune/encoding.py` — **new**. Constants, exception
  hierarchy, `EncodingReport`, `validate_role_sequence`.
- `src/bespokelabs/curator/finetune/data_formatter.py` — `DataFormatter.__init__`,
  `_compute_weights` (replaced by `_supervised_spans`), `to_tinker_datum`,
  `format_batch`.
- `src/bespokelabs/curator/finetune/fireworks_data_formatter.py` —
  `to_jsonl_lines`, new `from_config`.
- `src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py` line 126 — one
  line, `FireworksDataFormatter()` → `FireworksDataFormatter.from_config(config)`.
- `src/bespokelabs/curator/finetune/__init__.py` — export the new public names.
- `tests/finetune/test_data_formatter.py` — additions only; every existing test in
  that file must still pass unchanged (verified against this design: the mock path
  keeps the `<|role|>\n` template and the `len//4` token count, so
  `test_max_seq_length`'s `len(model_input) <= 50` still holds at 49, and
  `test_to_tinker_datum_with_system_message` still finds `"<|system|>"` in
  `metadata["original_text"]`).

**Machinery that may be REUSED (do not rewrite)**

- `ChatMessage`, `TrainingExample`, `TrainingExample.from_dict_messages`
  (`finetune/types.py:9-24`).
- `DataFormatter.format_chat_messages` and `format_example`
  (`data_formatter.py:28-58`) — unchanged.
- The prefix-tokenization boundary trick already in `_compute_weights`
  (`data_formatter.py:80-96`): `apply_chat_template(pre, add_generation_prompt=True)`
  gives the start index, `apply_chat_template(cumulative,
  add_generation_prompt=False)` gives the end index.
- The causal shift and the `tinker.Datum` construction
  (`data_formatter.py:134-148`) — **out of scope**, keep as is.
- `FireworksDataFormatter.example_to_dict` / `write_jsonl`
  (`fireworks_data_formatter.py:20-29, 42-56`) — unchanged except that
  `write_jsonl` inherits whatever `to_jsonl_lines` now returns.
- `FireworksTrainerConfig` (`finetune/config.py:126-147`), in particular
  `max_context_length` (line 129).

**Machinery that must be BUILT**

- `encoding.py` in full: `MIN_RETAINED_PROMPT_TOKENS`, `FIREWORKS_BYTES_PER_TOKEN`,
  `ALLOWED_ROLES`, `EncodingError`, `ExampleTooLongError`,
  `InvalidRoleSequenceError`, `TokenizerCapabilityError`, `EncodingReport`,
  `validate_role_sequence`.
- `DataFormatter._supervised_spans` (replaces `_compute_weights`).
- Left-window + drop logic in `to_tinker_datum`; drop-and-report logic in
  `format_batch`; `self.last_report`.
- Byte-budget logic in `FireworksDataFormatter.to_jsonl_lines`;
  `FireworksDataFormatter.from_config`.

**Latent bugs in this area that this work fixes** (real, cite them):

- `data_formatter.py:157` — `"original_text": chat_text if tokenizer is None else ""`.
  With a real tokenizer and `tinker` not installed (it is not: `pyproject.toml:39`
  marks it optional and `python >= 3.11`; this checkout is 3.10.12, so
  `TINKER_AVAILABLE is False`), every datum carries an empty `original_text`. P6.
- `data_formatter.py:102-104` — `except Exception: weights = [1.0] * len(tokens)`
  turns `train_on_assistant_only=True` into training on the prompt. P4.
- `data_formatter.py:99` — `min(end_idx, len(weights))` silently clamps a supervised
  span that the truncation at line 123 already removed, producing an all-zero weight
  vector for an over-long example. P1/P2/P3.
- `fireworks_trainer.py:126` — `FireworksDataFormatter()` ignores
  `config.max_context_length`; the value reaches the SFT job
  (`fireworks_trainer.py:331`) but never the file that is uploaded to it. P9.

**Python / deps.** Python 3.10 (`pyproject.toml:22`, `^3.10`); this checkout runs
3.10.12, so use `Optional[...]`/`Tuple[...]` from `typing`, not `X | Y`. Stdlib
`json`, `dataclasses`, `typing`; `pydantic` v2 (already a dependency). `tinker` is
NOT installed and must not be required. `pytest` for tests. No new dependencies.
Pure, deterministic, no I/O other than the existing `write_jsonl`.

## The API

```python
# src/bespokelabs/curator/finetune/encoding.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

MIN_RETAINED_PROMPT_TOKENS: int = 16
FIREWORKS_BYTES_PER_TOKEN: int = 3
ALLOWED_ROLES: frozenset = frozenset({"system", "user", "assistant"})


class EncodingError(ValueError):
    """Base class for every error raised by the encoding policy."""


class ExampleTooLongError(EncodingError):
    def __init__(
        self,
        *,
        token_count: int,
        max_seq_length: int,
        retained_prompt_tokens: int,
        num_messages: int,
    ) -> None: ...

    # attributes, all set before super().__init__():
    #   token_count: int            length of the UNtruncated token sequence
    #   max_seq_length: int         the formatter's cap
    #   retained_prompt_tokens: int max(0, start_of_final_assistant - window_start)
    #   num_messages: int           len(example.messages)
    # str(e) == (
    #     f"example of {token_count} tokens exceeds max_seq_length={max_seq_length}: "
    #     f"{retained_prompt_tokens} prompt tokens would survive, "
    #     f"minimum is {MIN_RETAINED_PROMPT_TOKENS}"
    # )


class InvalidRoleSequenceError(EncodingError):
    def __init__(self, *, role_sequence: List[str], position: int, reason: str) -> None: ...

    # attributes:
    #   role_sequence: List[str]  the roles as given, in order
    #   position: int             index of the offending message
    #   reason: str               one of "empty" | "unknown_role" | "misplaced_system"
    #                                    | "non_alternating" | "unterminated"
    # str(e) == f"invalid role sequence at position {position} ({reason}): {role_sequence}"


class TokenizerCapabilityError(EncodingError):
    def __init__(self, *, missing_method: str) -> None: ...

    # attributes:
    #   missing_method: str   e.g. "apply_chat_template"
    # str(e) == f"tokenizer is missing required method {missing_method!r}"


@dataclass(frozen=True)
class EncodingReport:
    kept: int = 0
    dropped: int = 0
    windowed: int = 0
    dropped_indices: Tuple[int, ...] = ()
    supervised_tokens: int = 0


def validate_role_sequence(messages: Sequence[Any]) -> None:
    """Raise InvalidRoleSequenceError if the roles are not a legal conversation.

    `messages` is a sequence of objects with a `.role` attribute (ChatMessage) or
    of dicts with a "role" key; both are accepted. Returns None on success.
    """
```

```python
# src/bespokelabs/curator/finetune/data_formatter.py
class DataFormatter:
    def __init__(self, max_seq_length: int = 2048, train_on_assistant_only: bool = True) -> None:
        self.max_seq_length: int = max_seq_length
        self.train_on_assistant_only: bool = train_on_assistant_only
        self.last_report: EncodingReport = EncodingReport()   # NEW

    def _supervised_spans(
        self, messages: List[ChatMessage], tokenizer: Optional[Any]
    ) -> List[Tuple[int, int]]:
        """Half-open [start, end) token index of every assistant turn, in message
        order, over the UNtruncated token sequence. Never swallows exceptions."""

    def to_tinker_datum(self, example: TrainingExample, tokenizer: Optional[Any] = None) -> Any:
        """Returns tinker.Datum when TINKER_AVAILABLE and tokenizer is not None,
        else the dict below. Raises InvalidRoleSequenceError,
        TokenizerCapabilityError, ExampleTooLongError. Does not touch last_report."""

    def format_batch(self, examples: List[TrainingExample], tokenizer: Optional[Any] = None) -> List[Any]:
        """Drops examples that raise ExampleTooLongError; sets self.last_report.
        Lets every other EncodingError propagate."""
```

Dict return shape of `to_tinker_datum` (the only shape reachable without `tinker`):

```python
{
    "model_input":  List[int],                    # windowed_tokens[:-1]
    "loss_fn_inputs": {
        "target_tokens": List[int],               # windowed_tokens[1:]
        "weights":       List[float],             # windowed_weights[1:], 0.0/1.0
    },
    "metadata": {
        "original_text": str,                     # ALWAYS the chat text, both branches
        "num_messages":  int,                     # len(example.messages)
        "encoding": {                             # NEW, exactly these five keys
            "tokenizer":         bool,            # tokenizer is not None
            "token_count":       int,             # len of UNtruncated tokens
            "window_start":      int,             # max(0, token_count - max_seq_length)
            "windowed":          bool,            # window_start > 0
            "supervised_tokens": int,             # count of 1.0 in PRE-shift weights
        },
    },
}
```

```python
# src/bespokelabs/curator/finetune/fireworks_data_formatter.py
class FireworksDataFormatter(DataFormatter):
    @classmethod
    def from_config(cls, config: "FireworksTrainerConfig") -> "FireworksDataFormatter": ...

    def to_jsonl_lines(self, examples: List[TrainingExample]) -> List[str]:
        """Validates roles, drops over-budget lines, sets self.last_report."""
```

```python
# src/bespokelabs/curator/finetune/__init__.py  — added to the imports and __all__
"EncodingError", "ExampleTooLongError", "InvalidRoleSequenceError",
"TokenizerCapabilityError", "EncodingReport", "MIN_RETAINED_PROMPT_TOKENS",
"FIREWORKS_BYTES_PER_TOKEN", "ALLOWED_ROLES", "validate_role_sequence",
```

The tokenizer double the whole spec is testable with:

```python
class FakeTokenizer:
    def __init__(self) -> None:
        self.encode_calls: List[Tuple[str, Dict[str, Any]]] = []

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False) -> str:
        text = "".join(f"[{m['role']}]{m['content']}\n" for m in messages)
        return text + "[assistant]" if add_generation_prompt else text

    def encode(self, text, **kwargs):
        self.encode_calls.append((text, kwargs))
        return [ord(c) for c in text]        # one token per character
```

## Parts

### P1 — Left window, computed by the formatter, not by the tokenizer

**Behaviour.** `to_tinker_datum` encodes the full chat text with exactly one call,
`tokenizer.encode(chat_text, add_special_tokens=False)` — no `max_length`, no
`truncation` — and then keeps the **last** `max_seq_length` tokens itself:
`window_start = max(0, len(tokens) - self.max_seq_length)`,
`windowed = tokens[window_start:]`. Weights are computed over the untruncated
sequence and sliced with the identical `[window_start:]`, so the completion at the
end of the conversation always survives and the oldest context is what is lost.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep line 123 as it is: `tokenizer.encode(chat_text, max_length=self.max_seq_length,
   truncation=True)`, i.e. right truncation performed by the tokenizer. This is what
   the file does today, it is the HF default (`truncation_side="right"`), and it is
   the single most likely thing a reader writes.
2. Encode fully and keep the **first** `max_seq_length` tokens (`tokens[:max_seq_length]`),
   which reads as "the same thing, just done by hand", preserving the system prompt
   instead of the answer.
3. Middle-out: keep the first `max_seq_length // 2` and the last `max_seq_length // 2`
   tokens joined, a common long-context trick.

**The observable.** With `FakeTokenizer` (one token per character) and
`DataFormatter(max_seq_length=40)` over the four messages of the End-to-end section
(`token_count == 91`): `datum["loss_fn_inputs"]["target_tokens"][0] == 97` (`'a'`,
i.e. `tokens[52]`) and `len(datum["model_input"]) == 39`, whereas all three
alternatives keep `tokens[0..]` and so give `target_tokens[0] == 117` (`'u'`, i.e.
`tokens[1]`), and `model_input[19] == 10` here (`tokens[70]`, the newline before
the final turn) against `117` (`tokens[19]`) for all three. Additionally
`tokenizer.encode_calls[-1][1] == {"add_special_tokens": False}` — no call anywhere
in the run carries a `truncation` or `max_length` key
(`assert all("truncation" not in kw and "max_length" not in kw for _, kw in
tokenizer.encode_calls)`).

**Arbitrary:** policy with no local evidence + deliberate departure — line 123
plainly does right truncation through the tokenizer, and reading it leads you the
wrong way.

### P2 — `ExampleTooLongError` and the 16-token prompt floor

**Behaviour.** Let `(s_last, e_last)` be the span of the **final** assistant message.
If the example was windowed (`window_start > 0`) and
`s_last - window_start < MIN_RETAINED_PROMPT_TOKENS` (= 16), the example is refused:
`to_tinker_datum` raises `ExampleTooLongError(token_count=len(tokens),
max_seq_length=self.max_seq_length, retained_prompt_tokens=max(0, s_last -
window_start), num_messages=len(example.messages))`. An example that is not windowed
is never refused, however short its prompt. A supervised span that is retained with
16 or more prompt tokens ahead of it is kept, not refused.

**Alternatives a competent engineer would plausibly choose instead.**
1. No floor at all: window and keep, as long as at least one supervised token
   survives (`s_last >= window_start`).
2. Refuse any example that had to be windowed at all — "if it does not fit, drop it"
   is the other defensible half of the brief.
3. Keep everything and let the caller notice: return the datum with an all-zero
   weight vector and a `metadata["truncated"] = True` flag, which is the smallest
   change from today's behaviour.

**The observable.** `DataFormatter(max_seq_length=40)`, `FakeTokenizer`, messages
`[user "u"*10, assistant "a"*100]` → `token_count == 129`, `window_start == 89`,
`s_last == 28`. `pytest.raises(ExampleTooLongError)` and the caught exception has
`e.token_count == 129`, `e.max_seq_length == 40`, `e.retained_prompt_tokens == 0`,
`e.num_messages == 2`, `isinstance(e, ValueError) is True`. And the near-miss pair
that separates the floor from alternative 1: with `max_seq_length=40` and messages
`[user "u"*30, assistant "a"*10, user "v"*5, assistant "b"*8]`
(`window_start == 51`, `s_last == 82`, retained prompt `31`) no exception is raised;
shrink to `max_seq_length=17` (`window_start == 74`, retained prompt `8`) and
`ExampleTooLongError` is raised with `retained_prompt_tokens == 8` — alternative 1
returns a datum there.

**Arbitrary:** invented name + chosen value (nothing in the repository suggests 16,
or that the floor applies only to windowed examples).

### P3 — A partially windowed assistant span is unsupervised in full

**Behaviour.** An assistant span `(s, e)` contributes weight `1.0` to indices
`[s, e)` **only if `s >= window_start`**. A span that begins before the window and
ends inside it is zeroed entirely — no half-turn is ever supervised. Spans of
earlier assistant turns that survive whole are supervised normally, so multi-turn
examples keep every complete turn.

**Alternatives a competent engineer would plausibly choose instead.**
1. Supervise the surviving tail: weights `1.0` on `[max(s, window_start), e)`. This
   is what today's clamping idiom at line 99 (`min(end_idx, len(weights))`) does at
   the other end, and it is the natural thing to write when slicing.
2. Refuse the example: if any assistant span is cut, raise rather than silently
   dropping supervision from a turn.

**The observable.** The End-to-end example: two assistant spans, `(48, 59)` and
`(82, 91)`, `window_start == 51`. `datum["metadata"]["encoding"]["supervised_tokens"]
== 9` and `sum(datum["loss_fn_inputs"]["weights"]) == 9.0` with the ones exactly at
shifted indices 30..38 inclusive
(`[i for i, w in enumerate(datum["loss_fn_inputs"]["weights"]) if w == 1.0]
== [30, 31, 32, 33, 34, 35, 36, 37, 38]`). Alternative 1 yields
`supervised_tokens == 17` with ones also at shifted indices 0..6; alternative 2
raises.

**Arbitrary:** policy with no local evidence (the file's own clamping idiom argues
for the alternative).

### P4 — `TokenizerCapabilityError`, and boundary failures propagate

**Behaviour.** Before any encoding, `to_tinker_datum` checks
`callable(getattr(tokenizer, "apply_chat_template", None))` when `tokenizer is not
None`; if it is not callable it raises
`TokenizerCapabilityError(missing_method="apply_chat_template")` — regardless of
`train_on_assistant_only`. The `try/except Exception` at lines 102-104 is deleted:
if `apply_chat_template` or `encode` raises while spans are being computed, that
exception propagates unchanged. There is no all-ones fallback anywhere on the
tokenizer path.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep lines 102-104 verbatim — fall back to `[1.0] * len(tokens)`, which is what
   the code says and what the comment defends.
2. Invert the fallback but stay soft: on failure return all-zero weights, so the
   example simply contributes nothing rather than training on the prompt.
3. Degrade to the no-tokenizer path when the tokenizer lacks a chat template — i.e.
   treat a template-less tokenizer as `tokenizer=None` and build the `<|role|>`
   text instead.

**The observable.** A double exposing only `encode` (no `apply_chat_template`):
`pytest.raises(TokenizerCapabilityError)` from
`formatter.to_tinker_datum(example, tok)` with `e.missing_method ==
"apply_chat_template"` and `str(e) == "tokenizer is missing required method
'apply_chat_template'"`; the same holds for `DataFormatter(train_on_assistant_only=
False)`. Separately, a double whose `apply_chat_template` raises
`RuntimeError("template boom")` only when `add_generation_prompt=True`: the call
raises `RuntimeError` with `str(e) == "template boom"`, where alternative 1 returns
a datum whose `weights` are all `1.0` and alternative 2 one whose `weights` are all
`0.0`.

**Arbitrary:** invented name + deliberate departure (the surrounding code plainly
does the opposite, with a comment explaining why).

### P5 — Role vocabulary and ordering

**Behaviour.** `validate_role_sequence` is called first thing in `to_tinker_datum`
and in `FireworksDataFormatter.to_jsonl_lines`, and raises
`InvalidRoleSequenceError` on the first violation found, testing the rules in this
order: (a) empty list → `reason="empty"`, `position=0`; (b) any role not in
`ALLOWED_ROLES` = `{"system", "user", "assistant"}` → `reason="unknown_role"`,
`position` = index of the first such message; (c) a `"system"` message anywhere but
index 0 → `reason="misplaced_system"`, `position` = index of that message; (d) after
the optional leading system message the roles must alternate `user, assistant, user,
assistant, ...` → `reason="non_alternating"`, `position` = index of the first message
whose role is not the expected one; (e) the last message must be `"assistant"` →
`reason="unterminated"`, `position = len(messages) - 1`.

**Alternatives a competent engineer would plausibly choose instead.**
1. No validation at all — `ChatMessage` (`types.py:9-13`) takes any `role: str`, the
   formatter passes roles through to the template, and nothing today objects.
2. Validate the vocabulary but accept `"tool"` and `"function"` as well (OpenAI's
   set), and allow repeated same-role turns, since chat templates handle them.
3. Raise the existing `ValueError` with a message (the file's own idiom at line 58)
   instead of a typed exception carrying a position.

**The observable.** Exact `(reason, position)` for five inputs, all with
`ALLOWED_ROLES`-shaped construction:
`[]` → `("empty", 0)`;
`[user, tool, assistant]` → `("unknown_role", 1)`;
`[user, system, assistant]` → `("misplaced_system", 1)`;
`[system, user, user, assistant]` → `("non_alternating", 2)`;
`[system, user, assistant, user]` → `("unterminated", 3)`.
Plus `e.role_sequence == ["system", "user", "user", "assistant"]` for the fourth and
`isinstance(e, EncodingError) and isinstance(e, ValueError)`.

**Arbitrary:** invented name + policy with no local evidence + chosen ordering of
checks (the `misplaced_system`-before-`non_alternating` order is what makes
`[user, system, assistant]` report position 1 with `"misplaced_system"` rather than
`"non_alternating"`).

### P6 — One envelope: `metadata["original_text"]` always populated, plus `metadata["encoding"]`

**Behaviour.** The dict envelope's `metadata["original_text"]` is the chat text on
**both** branches — the tokenizer's `apply_chat_template` output when a tokenizer is
given, the `<|role|>` text when it is not — fixing `data_formatter.py:157`, which
today stores `""` exactly when the text is real. `metadata` gains an `"encoding"`
sub-dict with exactly the five keys `{"tokenizer", "token_count", "window_start",
"windowed", "supervised_tokens"}` and the types given in The API. `num_messages`
stays. The `tinker.Datum` branch is untouched.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave line 157 alone (it looks deliberate — "don't carry the big string when the
   tokenizer already has it") and add the new counters as top-level keys of the
   returned dict, next to `model_input`.
2. Flatten: `metadata["truncated"]`, `metadata["window_start"]`,
   `metadata["supervised_tokens"]` directly on `metadata`, no nesting.
3. Report the post-window length as `token_count`, i.e. `len(windowed)`, since that
   is the datum's actual size.

**The observable.** For the End-to-end example:
`datum["metadata"]["encoding"] == {"tokenizer": True, "token_count": 91,
"window_start": 51, "windowed": True, "supervised_tokens": 9}` (exact dict equality,
so extra or renamed keys fail), `datum["metadata"]["original_text"] ==
"[user]" + "u"*30 + "\n[assistant]" + "a"*10 + "\n[user]vvvvv\n[assistant]bbbbbbbb\n"`
(91 characters), and `set(datum["metadata"]) == {"original_text", "num_messages",
"encoding"}`. Alternative 3 gives `token_count == 40`.

**Arbitrary:** invented field names + a fix to a real bug at `data_formatter.py:157`
that reading the line argues against.

### P7 — `format_batch` drops, counts, and reports; other errors propagate

**Behaviour.** `format_batch` calls `to_tinker_datum` per example in input order.
An `ExampleTooLongError` means the example is **dropped** from the returned list and
recorded; `InvalidRoleSequenceError` and `TokenizerCapabilityError` propagate out of
`format_batch` and abort it (bad data is a bug, an over-long example is a fact of
life). After a complete pass it assigns `self.last_report = EncodingReport(kept=<len
of returned list>, dropped=<number dropped>, windowed=<kept examples whose
window_start > 0>, dropped_indices=<tuple of input indices dropped, ascending>,
supervised_tokens=<sum of encoding.supervised_tokens over kept examples>)`.
`to_tinker_datum` never writes `last_report`; a fresh `DataFormatter` has
`last_report == EncodingReport()`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Let `ExampleTooLongError` propagate too — one bad row fails the batch — which is
   the simplest and most honest-looking thing to do once P2 exists.
2. Keep the offending example in place as `None` so indices line up with the input,
   and let the trainer filter.
3. Return `(data, report)` as a tuple from `format_batch`, rather than parking the
   report on the instance; `tinker_trainer.py:250` returns the result of
   `format_batch` directly, so an instance attribute is the non-obvious choice.

**The observable.** The two-example batch of the End-to-end section:
`len(batch) == 1` and `formatter.last_report == EncodingReport(kept=1, dropped=1,
windowed=1, dropped_indices=(1,), supervised_tokens=9)` (dataclass equality).
Immediately before the call, `DataFormatter(max_seq_length=40).last_report ==
EncodingReport(kept=0, dropped=0, windowed=0, dropped_indices=(), supervised_tokens=
0)`. With a third example whose roles are `[user, user]`, `format_batch` raises
`InvalidRoleSequenceError` and `last_report` is still the pre-call value.

**Arbitrary:** invented name + policy with no local evidence (which error class
drops and which aborts; the report living on `self`).

### P8 — Fireworks inherits the policy as a byte budget

**Behaviour.** `to_jsonl_lines` validates roles for every example (propagating
`InvalidRoleSequenceError`), serializes each with the existing
`json.dumps(..., ensure_ascii=False)`, and drops any line whose **UTF-8 byte length**
exceeds `self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN` (= `max_seq_length * 3`);
a line whose byte length equals the budget is kept. Nothing is ever truncated on
this path. It then sets `self.last_report = EncodingReport(kept=..., dropped=...,
windowed=0, dropped_indices=..., supervised_tokens=0)`. `write_jsonl` writes exactly
the lines `to_jsonl_lines` returned, so drops reach the file.

**Alternatives a competent engineer would plausibly choose instead.**
1. No length policy at all — the current behaviour; Fireworks is a hosted service and
   will do its own truncation.
2. Reuse the mock path's ratio, `len(chat_text) // 4 <= max_seq_length`, i.e. 4
   characters per token measured on the message text — `data_formatter.py:130` is
   right there and says 4.
3. Measure `len(line)` in characters rather than UTF-8 bytes (identical for ASCII,
   so it survives a careless test).

**The observable.** `FireworksDataFormatter(max_seq_length=30)` and the examples
`[user "qqq", assistant "ok"]` (line = 90 bytes = budget) and
`[user "qqqqqq", assistant "ok"]` (93 bytes) → `len(to_jsonl_lines([a, b])) == 1`
and `last_report == EncodingReport(kept=1, dropped=1, windowed=0,
dropped_indices=(1,), supervised_tokens=0)`. For bytes-vs-characters: with
`max_seq_length=33` (budget 99) the single example
`[user "héllo wörld", assistant "ok"]` serializes to 98 characters / 100 bytes and
is **dropped** — `to_jsonl_lines([x]) == []`, `last_report.dropped == 1` —
where alternative 3 keeps it; alternatives 1 and 2 keep every case above.

**Arbitrary:** chosen value (3 bytes/token, and `>` rather than `>=` at the
boundary) + policy with no local evidence (bytes of the serialized line, not
characters of the chat text).

### P9 — `FireworksDataFormatter.from_config`

**Behaviour.** `from_config(config)` returns
`cls(max_seq_length=config.max_context_length if config.max_context_length is not
None else 2048, train_on_assistant_only=True)`, and `fireworks_trainer.py:126`
becomes `self.data_formatter = FireworksDataFormatter.from_config(config)`. This is
the only place `FireworksTrainerConfig.max_context_length` (`config.py:129`) reaches
the data that is written; today it reaches only the SFT job kwargs
(`fireworks_trainer.py:331`).

**Alternatives a competent engineer would plausibly choose instead.**
1. Pass it inline at the call site: `FireworksDataFormatter(max_seq_length=
   config.max_context_length or 2048)` — no classmethod, nothing importable to test.
2. Fall back to `config.batch_size`-style "leave it None and let the server decide":
   keep the formatter's own default and never wire `max_context_length` at all
   (today's behaviour).
3. Treat `max_context_length` as a hard cap and take
   `min(max_context_length, 2048)`, so the default never grows.

**The observable.** `FireworksDataFormatter.from_config(FireworksTrainerConfig(
base_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
max_context_length=100)).max_seq_length == 100`;
`FireworksDataFormatter.from_config(FireworksTrainerConfig(base_model=<same>)
).max_seq_length == 2048`; and
`from_config(FireworksTrainerConfig(base_model=<same>, max_context_length=4096)
).max_seq_length == 4096` (alternative 3 gives 2048). The returned object satisfies
`isinstance(x, FireworksDataFormatter)` and `x.train_on_assistant_only is True`.

**Arbitrary:** invented name + chosen value (the 2048 fallback, and that a larger
`max_context_length` wins).

### P10 — The no-tokenizer path obeys `train_on_assistant_only`

**Behaviour.** With `tokenizer=None` the text stays exactly what
`data_formatter.py:127-129` builds (`f"<|{msg.role}|>\n{msg.content}\n"` per
message) and the token count stays `len(chat_text) // 4` — but it is **no longer
capped** at `max_seq_length` there; instead `tokens = list(range(len(chat_text) //
4))` goes through the same P1 window, the same P2 floor and the same P3 span rule as
the tokenizer path. Spans are derived from character offsets: for assistant message
`i`, `span = (len_before // 4, len_after // 4)` where `len_before` is the length of
the text built from `messages[:i]` and `len_after` that of `messages[:i+1]` — i.e.
the `<|assistant|>\n` header is inside the supervised span on this path, unlike the
tokenizer path where `add_generation_prompt=True` puts it before the span. When
`train_on_assistant_only` is `False`, weights are all `1.0`, on both paths.
`metadata["encoding"]["tokenizer"]` is `False`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep lines 130-132 as they are — cap at `max_seq_length`, all-ones weights — on
   the grounds that synthetic ids cannot be trained on anyway, so supervision is
   meaningless there.
2. Honour `train_on_assistant_only` but exclude the header, mirroring
   `add_generation_prompt=True`: `span = ((len_before + len(f"<|assistant|>\n")) //
   4, len_after // 4)`.
3. Refuse the path outright: raise `TokenizerCapabilityError(missing_method=
   "encode")` when `tokenizer is None`, since a datum of synthetic ids is not a
   training datum.

**The observable.** `DataFormatter(max_seq_length=1024)`, no tokenizer, messages
`[user "Hello", assistant "Hi there!"]`. Text is
`"<|user|>\nHello\n<|assistant|>\nHi there!\n"` — 39 characters, `token_count == 9`,
`window_start == 0`, `len_before == 15`, `len_after == 39`, so the span is `(3, 9)`
and `metadata["encoding"]["supervised_tokens"] == 6` with pre-shift weights
`[0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`, hence
`datum["loss_fn_inputs"]["weights"] == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`
(8 entries, `sum == 6.0`). Alternative 1 gives eight `1.0`s and
`supervised_tokens == 9`; alternative 2 gives `supervised_tokens == 2`
(span `(7, 9)`, since `(15 + 14) // 4 == 7`); alternative 3 raises.
`datum["metadata"]["encoding"]["tokenizer"] is False`.

**Arbitrary:** deliberate departure (line 132 is literally `[1.0] * len(tokens)`) +
policy (the header is inside the span here and outside it there).

## End to end

**Setup.**

```python
tok = FakeTokenizer()                       # as defined in The API
fmt = DataFormatter(max_seq_length=40, train_on_assistant_only=True)

good = TrainingExample.from_dict_messages([
    {"role": "user",      "content": "u" * 30},
    {"role": "assistant", "content": "a" * 10},
    {"role": "user",      "content": "v" * 5},
    {"role": "assistant", "content": "b" * 8},
])
too_long = TrainingExample.from_dict_messages([
    {"role": "user",      "content": "u" * 10},
    {"role": "assistant", "content": "a" * 100},
])

batch = fmt.format_batch([good, too_long], tok)
```

**Derivation.** `chat_text(good)` is 91 characters, so `token_count == 91` and
`window_start == max(0, 91 - 40) == 51`. Assistant spans: the first is `(48, 59)`
(48 = `len("[user]" + "u"*30 + "\n" + "[assistant]")`), the second is `(82, 91)`.
`48 < 51`, so the first span is dropped whole (P3); `82 >= 51`, so the second is
supervised, with `82 - 51 == 31 >= 16` prompt tokens ahead of it (P2). `too_long`
has `token_count == 129`, `window_start == 89`, final span `(28, 129)`, so
`retained_prompt_tokens == max(0, 28 - 89) == 0 < 16` and it is refused and dropped.

**Exact outputs.**

```python
len(batch) == 1

batch[0] == {
    "model_input": [
        97, 97, 97, 97, 97, 97, 97, 10, 91, 117, 115, 101, 114, 93, 118, 118, 118,
        118, 118, 10, 91, 97, 115, 115, 105, 115, 116, 97, 110, 116, 93, 98, 98, 98,
        98, 98, 98, 98, 98,
    ],                                                     # 39 ints
    "loss_fn_inputs": {
        "target_tokens": [
            97, 97, 97, 97, 97, 97, 10, 91, 117, 115, 101, 114, 93, 118, 118, 118,
            118, 118, 10, 91, 97, 115, 115, 105, 115, 116, 97, 110, 116, 93, 98, 98,
            98, 98, 98, 98, 98, 98, 10,
        ],                                                 # 39 ints
        "weights": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        ],                                                 # 39 floats, sum == 9.0
    },
    "metadata": {
        "original_text": (
            "[user]uuuuuuuuuuuuuuuuuuuuuuuuuuuuuu\n"
            "[assistant]aaaaaaaaaa\n"
            "[user]vvvvv\n"
            "[assistant]bbbbbbbb\n"
        ),                                                 # 91 characters
        "num_messages": 4,
        "encoding": {
            "tokenizer": True,
            "token_count": 91,
            "window_start": 51,
            "windowed": True,
            "supervised_tokens": 9,
        },
    },
}

fmt.last_report == EncodingReport(
    kept=1, dropped=1, windowed=1, dropped_indices=(1,), supervised_tokens=9
)
```

And, for the same `fmt` and `tok`, the single-example call on the refused row:

```python
with pytest.raises(ExampleTooLongError) as excinfo:
    fmt.to_tinker_datum(too_long, tok)

excinfo.value.token_count == 129
excinfo.value.max_seq_length == 40
excinfo.value.retained_prompt_tokens == 0
excinfo.value.num_messages == 2
str(excinfo.value) == (
    "example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would "
    "survive, minimum is 16"
)
fmt.last_report == EncodingReport(                  # unchanged by to_tinker_datum
    kept=1, dropped=1, windowed=1, dropped_indices=(1,), supervised_tokens=9
)
```
