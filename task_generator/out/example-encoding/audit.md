# Audit — g9 (example-encoding)

| fact | bracket | audit | why |
|---|---|---|---|
| `g9.r1.rule` | hidden | **retest** | Do not ship as-is; two concrete changes, then re-bracket.

1. Close the coincidence (Catalog A: `model_already_knows_it` + `obvious_implementation_does_it`). Re |
| `g9.r1.scope` | hidden | **narrow** | Narrow, and invert the discriminator. (1) Flip the offset rule: make the mock-path span EXCLUDE the `<|assistant|>\n` header, matching what the ticket already s |
| `g9.r1.exclusions_or_crossover` | hidden | **retest** | Retest. The rule is real and discriminating; the test grades serialization formatting at zero margin. Three changes:

(1) Pin the serialization where the agent  |
| `g9.r1.failure_behavior` | hidden | **retest** | Keep the fact — the divergent action is concrete and no blind implementation reaches `encoding_names("ExampleTooLongError")` — but fix the test, which currently |
| `g9.r2.rule` | hidden | **retest** | Retest — keep the fact, decouple the test from r1. Three concrete changes to test_rule__both_batch_entry_points_publish_a_frozen_encoding_report: (1) after `for |
| `g9.r2.scope` | hidden | **cut** | Cut r2.scope as a separate graded fact and fold its two assertions into r2.rule's test (the fresh-formatter default check is already r2.rule's `__init__` clause |
| `g9.r2.failure_behavior` | hidden | **cut** | Cut r2.failure_behavior as a separately graded fact and fold its one non-redundant clause into r2.rule.

Reasons, in order of weight: (1) no independent content |

## g9.r1.rule — retest

**Divergent action.** `if start < window_start: continue` (equivalently `if s - window_start < 0: continue`) inside the loop that paints assistant spans into the weight vector — a guard that drops a span whose start precedes the window boundary, in place of the clamping form `s = max(start - window_start, 0)` or of no guard at all. Concretely, the informed agent writes `for start, end in spans: if start < window_start: continue; weights[start:end] = [1.0] * (end - start)` where the blind agent writes `for start, end in spans: weights[start:end] = [1.0] * (end - start)` and then slices `weights[window_start:]`. This is a real, nameable divergence: the ticket's own prescription ("weights are built over the untruncated sequence and sliced with the identical [window_start:]") produces the supervised tail, so the fact is not a coincidence along the instructed path.

**The assertion.** `assert [i for i, w in enumerate(weights) if w == 1.0] == [30, 31, 32, 33, 34, 35, 36, 37, 38], ("the straddling span (48, 59) must contribute nothing, not its surviving tail")` — this is the only assertion the tail-supervised implementation fails (it would produce `[0, 1, 2, 3, 4, 5, 6, 30, ..., 38]`); `sum == 9.0`, `set == {0.0, 1.0}` and `supervised_tokens == 9` are all downstream of it. Passing depends on TWO things beyond this fact: (1) `r1.failure_behavior`'s `s_last` being the final assistant span — under the first-span reading the call raises `ExampleTooLongError` at `max_seq_length=40` and the assertion is never reached; and (2) `FakeTokenizer`'s exact character-per-token template in `test_open`, which fixes 91/48/59/82/91 and hence whether a straddle exists at all.

**Catalog A.**
- `model_already_knows_it` — 'Do not train on a truncated assistant response' is a standard chat-SFT data-prep convention — a surviving tail here is a headless fragment of `'a'*10` with its `<|assistant|>` header and opening tokens cut away, which is obviously bad supervision. A model can supply `if start < window_start: continue` from priors about masking incomplete turns, with no clue at all. This is the strongest Catalog A hit.
- `obvious_implementation_does_it` — Conditional on one design choice the ticket does not force. An engineer who builds the weight vector directly in windowed space (natural — it is the vector that reaches `loss_fn_inputs`) must handle `start - window_start < 0`, and `continue` is as idiomatic there as `max(..., 0)`. Along that path the fact falls out of normal defensive coding. The ticket's untruncated-then-slice sentence disfavours that path, which is why the single blind sample failed, but it does not preclude it.

**Catalog B.** clean

**A blind build that passes anyway:**

```
Ticket-only, no clue. The engineer builds the weight vector in windowed space rather than untruncated space, and guards the negative index by skipping rather than clamping:

```python
def to_tinker_datum(self, example, tokenizer=None):
    validate_role_sequence(example.messages)
    ...
    tokens = tokenizer.encode(chat_text, add_special_tokens=False)
    window_start = max(0, len(tokens) - self.max_seq_length)
    windowed_tokens = tokens[window_start:]

    windowed_weights = [0.0] * len(windowed_tokens)
    if self.train_on_assistant_only:
        for start, end in self._supervised_spans(example.messages, tokenizer):
            s = start - window_start
            if s < 0:
                # this assistant turn was cut by the window; don't train on a fragment
                continue
            for i in range(s, min(end - window_start, len(windowed_weights))):
                windowed_weights[i] = 1.0
    else:
        windowed_weights = [1.0] * len(windowed_tokens)
```

`if s < 0: continue` is written here purely as defensive index handling plus the ordinary SFT instinct that a truncated assistant response is bad supervision — not because anyone read the clue. It produces `supervised_tokens == 9`, `sum(weights) == 9.0`, and the 1.0 indices `[30..38]`, i.e. it passes the rule test in full. The `wide` half is unaffected because both spans start after 41. The bracket's single blind sample happened to follow the ticket's untruncated-then-slice phrasing instead; this variant is equally reasonable and is the sample it did not write.
```

**A correct build the test rejects:**

```
I could not construct one that is legitimate. The candidates all fail on inspection:

- Counting `supervised_tokens` over the untruncated weight vector instead of the windowed one — a fair reading of 'the count of 1.0 in the pre-shift weights' — gives the same 9 and 20, because under this rule every 1.0 necessarily lies at or after `window_start`. The two readings provably coincide.
- Snapping `window_start` back to the straddling turn's boundary instead of zeroing it (arguably a more faithful reading of 'multi-turn examples keep every complete turn') would break `window_start == 51` and `len(weights) == 39` — but it contradicts the OPEN ticket's `window_start = max(0, len(tokens) - self.max_seq_length)`, so it is not a legitimate reading.
- Routing a straddling span into `ExampleTooLongError` rather than zeroing it is disambiguated by `failure_behavior`, which fixes the refusal condition to the retained-prompt floor.

The one way a correct-on-this-fact agent fails the test is the sibling coupling in `the_assertion`: a wrong `s_last` in `failure_behavior` aborts the rule test with an unrelated exception. That is a test defect, not an overshoot.
```

**Recommendation.** Do not ship as-is; two concrete changes, then re-bracket.

1. Close the coincidence (Catalog A: `model_already_knows_it` + `obvious_implementation_does_it`). Re-run the blind condition at n=5, not n=1, and include at least one run whose prompt or scaffold nudges toward constructing the weight vector in WINDOWED space (e.g. a blind agent that writes `windowed_weights = [0.0] * len(windowed_tokens)` first). If any blind sample emits `if start < window_start: continue`, the fact is a coincidence and must be cut — the passing blind implementation is quoted in `blind_pass` and is behaviourally identical to golden, so no test change can separate them. If all five fail, the fact survives and the ticket's 'built over the untruncated sequence and sliced with the identical [window_start:]' sentence is doing the anti-coincidence work; keep that sentence verbatim and do not let it drift.

2. Fix the silent sibling coupling in the test. Before the weight assertions, make the premise explicit so a misdefined `s_last` produces a diagnostic instead of an unrelated exception inside the rule test:

```python
# premise, not the fact under test: 31 prompt tokens survive, so the
# retained-prompt floor must not fire here. If this raises, the bug is in
# ExampleTooLongError's s_last (final assistant span), not in the span rule.
try:
    datum = DataFormatter(max_seq_length=40).to_tinker_datum(example(*GOOD_PAIRS), tok)
except encoding_names("ExampleTooLongError") as e:
    pytest.fail(f"GOOD_PAIRS retains 31 prompt tokens and must not be refused; s_last must be the FINAL assistant span, got retained={e.retained_prompt_tokens}")
```

Everything else in the rule test — the 1.0-index list, `sum == 9.0`, `set == {0.0, 1.0}`, `supervised_tokens == 9`, and the `wide` half at `window_start 41` / `supervised_tokens 20` — is exact, arithmetically consistent, and should stay unchanged.


## g9.r1.scope — narrow

**Divergent action.** In `_supervised_spans`, the `tokenizer is None` branch builds the chat text incrementally and records character-offset spans instead of returning `[]` or falling back to all-ones: `start = len(text) // 4; text += f"<|{msg.role}|>\n{msg.content}\n"; if msg.role == "assistant": spans.append((start, len(text) // 4))` — the whole per-message chunk, so `<|assistant|>\n` sits inside the span. The informed agent also deletes the `min(..., self.max_seq_length)` cap so `tokens = list(range(len(chat_text) // 4))`. This is a real, nameable difference — but see catalog A: it is also what an agent writes without the clue.

**The assertion.** `assert weights_of(datum) == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]` (equivalently `assert read_field(encoding, "supervised_tokens") == 6, "the mock path must honour train_on_assistant_only, with the header inside the span"`). Passing it depends on two things beyond this requirement: the dict envelope and the causal shift `windowed_weights[1:]` from the open ticket, and — for the *test as a whole* to be green — `r1.rule`'s `window_start == 51` and `r1.failure_behavior`'s floor declining to refuse `GOOD_PAIRS` at 40, both pulled in by the final line.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The clause "it is no longer capped at max_seq_length" is a deletion, and the test never exercises it: the case is `DataFormatter(max_seq_length=1024)` over a 9-token example, so `min(9, 1024) == 9`. An agent who leaves the existing cap in place passes every assertion here. Inaction on that clause is indistinguishable from compliance.
- `ticket_gives_it_away` — The ticket supplies every ingredient but the offset: `_supervised_spans(self, messages: List[ChatMessage], tokenizer: Optional[Any])` — Optional, with no carve-out for None; `supervised_tokens` is "the count of 1.0 in the pre-shift weights" on a dict envelope the ticket calls "the only shape reachable in this checkout"; `"train_on_assistant_only=False" means weights are all 1.0` (so True must not be); and `metadata["original_text"] ... the `<|role|>` text without one`. That is the whole `tokenizer is False` / `token_count 9` / `window_start 0` / all-ones-when-False half of the observable, handed over openly.
- `entailed_by_the_open_feature` — For the "honours train_on_assistant_only on the mock path" half: given a `_supervised_spans` that takes `Optional[Any]`, a `supervised_tokens` key required on the only reachable branch, and all-1.0 explicitly reserved for `train_on_assistant_only=False`, supervising assistant spans on the None path is the only self-consistent build of the visible feature. Not entailed for the header-inside offset.
- `obvious_implementation_does_it` — This is the fatal one. The natural loop appends the whole `f"<|{msg.role}|>\n{msg.content}\n"` chunk per message and takes `len(before)//4, len(after)//4`; putting the header *outside* the span requires deliberately adding `len(f"<|{msg.role}|>\n")` to the start. The fact's discriminator is the branch the careless write already takes — the clue is graded on a coin whose obvious face it picked. Note also `len("<|user|>\nHello\n") // 4 == 3` equals the cumulative per-message sum `3`, so an agent who sums per-message `len(piece)//4` instead of using true prefix offsets also lands on `(3, 9)`.

**Catalog B.**
- `observable_belongs_to_another_fact` — The test's closing assertion — `weights_of(DataFormatter(max_seq_length=40, train_on_assistant_only=False).to_tinker_datum(example(*GOOD_PAIRS), FakeTokenizer())) == [1.0] * 39` — is on the tokenizer path and its length 39 encodes `window_start == 51`, which is `r1.rule`'s observable, while its non-refusal is `r1.failure_behavior`'s. The docstring asserts "`scope` stays on the mock path"; this line leaves it.

**A blind build that passes anyway:**

```
def _supervised_spans(self, messages: List[ChatMessage], tokenizer: Optional[Any]) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    if tokenizer is None:
        # No real tokenizer: the mock path counts one token per four characters,
        # so map each assistant message's character offsets the same way.
        text = ""
        for msg in messages:
            start = len(text) // 4
            text += f"<|{msg.role}|>\n{msg.content}\n"
            if msg.role == "assistant":
                spans.append((start, len(text) // 4))
        return spans
    ...  # existing prefix-tokenization boundary trick
# Ticket-only reasoning that gets here: _supervised_spans is typed
# `tokenizer: Optional[Any]` with no exception for None; metadata["encoding"]
# requires a real `supervised_tokens` on the branch the ticket calls "the only
# shape reachable in this checkout"; and all-1.0 is reserved by the ticket for
# train_on_assistant_only=False. Nothing about the header is considered — the
# whole per-message chunk is appended, which is precisely the graded answer.
# With max_seq_length=1024 the retained `min(..., self.max_seq_length)` cap
# never binds, so leaving it in place also passes.
```

**A correct build the test rejects:**

```
def _supervised_spans(self, messages, tokenizer):
    if tokenizer is None:
        spans = []
        text = ""
        for msg in messages:
            header = f"<|{msg.role}|>\n"
            if msg.role == "assistant":
                # mirror the tokenizer path: apply_chat_template(pre,
                # add_generation_prompt=True) puts the assistant header BEFORE
                # the span, so the header is prompt, not supervised output.
                spans.append(((len(text) + len(header)) // 4,
                              (len(text) + len(header) + len(msg.content) + 1) // 4))
            text += header + f"{msg.content}\n"
        return spans
# Span (7, 9) -> supervised_tokens 2, weights [0,0,0,0,0,0,1,1]. This agent read
# "obeys the same policy" as "the header is excluded on both paths", which is the
# more faithful reading of the ticket's own description of the tokenizer path
# ("add_generation_prompt=True for the start index"). The test rejects it.
```

**Recommendation.** Narrow, and invert the discriminator. (1) Flip the offset rule: make the mock-path span EXCLUDE the `<|assistant|>\n` header, matching what the ticket already says the tokenizer path does with `add_generation_prompt=True`. As written, the graded answer (header inside) is what the obvious loop produces, so the clue buys nothing; header-outside costs a deliberate `+ len(header)` that only a clue-reader writes, and the `correct_fail` implementation above becomes the golden while the `blind_pass` one fails. Restate the fact's observable as span (7, 9), supervised_tokens 2, weights [0,0,0,0,0,0,1,1]. (2) Drop from the fact the clauses the ticket already gives — `<|role|>` template, `len // 4`, `tokenizer is False`, `token_count`, `window_start`, all-ones-when-False — and leave scope as the offset rule alone. (3) Delete the final assertion (`max_seq_length=40, train_on_assistant_only=False`, `FakeTokenizer`, `[1.0] * 39`): it is on the tokenizer path, encodes `r1.rule`'s `window_start == 51`, and depends on `r1.failure_behavior`'s floor not firing, contradicting the docstring's "`scope` stays on the mock path". Cover all-ones-when-False on the mock path instead: `weights_of(DataFormatter(max_seq_length=1024, train_on_assistant_only=False).to_tinker_datum(plain)) == [1.0] * 8`, which is already there. (4) Either test the un-capping or cut it: at `max_seq_length=1024` over 9 tokens the retained `min(..., max_seq_length)` cap never binds, so add a binding mock-path case (e.g. `DataFormatter(max_seq_length=5)` on the same example → `token_count == 9`, `window_start == 4`, `windowed is True`) or remove "no longer capped at max_seq_length" from the fact. (5) Use a multi-turn mock example so header-in/header-out cannot coincide with a per-message-sum shortcut, and re-run the blind condition against several samples after the inversion — the current bracket's single blind sample took a third path (the all-ones shortcut) and tells you nothing about the two paths that matter here.


## g9.r1.exclusions_or_crossover — retest

**Divergent action.** Two things a blind agent does not write: (1) a module-level `FIREWORKS_BYTES_PER_TOKEN = 3` in `encoding.py`, and (2) inside `FireworksDataFormatter.to_jsonl_lines`, a drop branch keyed on the serialized line's UTF-8 length — `if len(line.encode("utf-8")) > self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN: continue`. A blind `to_jsonl_lines` returns exactly one line per input example (the ticket says only "validates every example's role sequence first"), so `len(to_jsonl_lines([fits, over])) == 2` and `to_jsonl_lines([accented]) == [accented_line]`. That is a real, nameable divergence.

**The assertion.** `assert len(lines) == 1, f"expected the 90-byte line and not the 93-byte one, got {lines}"` — with its companion `assert len(lines[0].encode("utf-8")) == 90`. Passing depends on more than this requirement: the second assertion is purely about `json.dumps` separator style and `ensure_ascii`, not about the byte budget, and the first sits at an exact 90-vs-90 boundary that any serialization difference (compact separators, `sort_keys`, an added key) flips. I could not read the checkout's current `to_jsonl_lines`, so I also cannot rule out that the `max_seq_length=34` assertion silently requires the agent to *add* `ensure_ascii=False` — a change no clause of the ticket or the fact asks for.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Half the fact is "never windows or truncates anything", graded by `json.loads(lines[0]) == {...}` with the message "the kept line must be whole: nothing on this path is truncated". No agent, blind or informed, was ever going to truncate a JSON line mid-string; this clause passes for free and tests no restraint. Only the drop-by-byte-budget half carries signal.

**Catalog B.**
- `fake_defines_the_trigger` — No mock is involved, but the *trigger threshold* is authored by a formatting detail the requirement never pins. The line is 90 bytes only because `json.dumps` defaults to `", "`/`": "` separators; those eight spaces are the entire margin against a 90-byte budget. With `separators=(",", ":")` the same example serializes to 82 bytes and the 93-byte one to 85, so both fit. The fact pins `ensure_ascii=False` and stays silent on separators, so the harness — not the requirement — decided when the trigger fires.

**A correct build the test rejects:**

```
FIREWORKS_BYTES_PER_TOKEN = 3  # in encoding.py

def to_jsonl_lines(self, examples: List[TrainingExample]) -> List[str]:
    for ex in examples:
        validate_role_sequence(ex.messages)
    budget = self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN
    lines: List[str] = []
    for ex in examples:
        # compact separators: this is a jsonl file, not a document
        line = json.dumps(self.example_to_dict(ex), ensure_ascii=False, separators=(",", ":"))
        if len(line.encode("utf-8")) > budget:
            continue
        lines.append(line)
    return lines

# Satisfies every stated clause — constant 3, budget = max_seq_length * 3, strict >,
# len(line.encode("utf-8")), ensure_ascii=False, nothing truncated — and still fails:
#   len(lines) == 1            -> 82 and 85 bytes both fit a 90-byte budget, gets 2
#   len(lines[0].encode()) == 90 -> gets 82
#   to_jsonl_lines([accented]) == [] -> 92 bytes fits the 99-byte budget, gets 1 line
```

**Recommendation.** Retest. The rule is real and discriminating; the test grades serialization formatting at zero margin. Three changes:

(1) Pin the serialization where the agent can see it. Add to the visible ticket's Fireworks bullet: "`to_jsonl_lines` keeps its existing `json.dumps(self.example_to_dict(ex), ensure_ascii=False)` — default separators, no `sort_keys`." First confirm the checkout already passes `ensure_ascii=False`; if it does not, the ticket must say to add it, because the `max_seq_length=34` assertion depends on it.

(2) Make the test self-calibrating instead of hard-coding 90. Measure the formatter's own output, then place the budget on either side of it:
    n = len(FireworksDataFormatter(max_seq_length=10**6).to_jsonl_lines([fits])[0].encode("utf-8"))
    assert n % 3 == 0  # or ceil to the next multiple
    assert len(FireworksDataFormatter(max_seq_length=n // 3).to_jsonl_lines([fits])) == 1      # strict >
    assert FireworksDataFormatter(max_seq_length=(n // 3) - 1).to_jsonl_lines([fits]) == []
This tests strict-`>` and the ×3 budget without grading separator style. Delete `assert len(lines[0].encode("utf-8")) == 90`.

(3) Keep the accented case — bytes-not-characters is the substance of the fact — but calibrate it the same way: measure the emitted line, assert `len(line.encode("utf-8")) > len(line)`, then set the cap so the budget falls between the character count and the byte count.

Also: drop "never windows or truncates anything" as a graded clause (satisfied by inaction), and give r2.rule its own fixture rather than reusing `[a, b]` at `max_seq_length=30`, so a single miss here is not counted twice.


## g9.r1.failure_behavior — retest

**Divergent action.** In `to_tinker_datum`, after windowing and span computation, before building the datum:

```python
MIN_RETAINED_PROMPT_TOKENS = 16   # module constant in encoding.py

s_last = spans[-1][0]
if window_start > 0 and s_last - window_start < MIN_RETAINED_PROMPT_TOKENS:
    raise ExampleTooLongError(
        token_count=len(tokens),
        max_seq_length=self.max_seq_length,
        retained_prompt_tokens=max(0, s_last - window_start),
        num_messages=len(example.messages),
    )
```
plus `class ExampleTooLongError(EncodingError)` with the four keyword-only attributes and the exact `__str__`, and `except ExampleTooLongError: continue` in `format_batch`. A ticket-only agent writes none of this: the ticket resolves over-length purely by windowing ("the end of the conversation survives and the oldest context is what is lost") and gives `to_tinker_datum` no failure mode beyond `InvalidRoleSequenceError` / `TokenizerCapabilityError`. It returns a datum for every valid example.

**The assertion.** `assert str(error) == ("example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16")`, guarded by `with pytest.raises(ExampleTooLongError) as excinfo: formatter.to_tinker_datum(too_long, tok)`. Passing depends on more than this requirement: the numbers 129 and 0 are produced by the open ticket's untruncated `token_count` and `window_start = max(0, token_count - max_seq_length)`, and by the reused prefix-tokenization boundary trick that fixes `s_last = 28`. A correct floor on top of a mis-built `token_count` fails this assertion; that coupling is acceptable (the open feature is graded elsewhere too) but it means this block is not a clean single-fact probe.

**Catalog A.** clean

**Catalog B.** clean

**A correct build the test rejects:**

```
Two, one certain and one conditional.

CERTAIN (the reverse problem — the test accepts a wrong floor rather than rejecting a right one, which is the same defect seen from the other side). The fact's central claim is `MIN_RETAINED_PROMPT_TOKENS == 16` with strict `<`. The test's three graded points are retained 0 (refuse), 8 (refuse), 31 (keep). So this passes every assertion:

```python
MIN_RETAINED_PROMPT_TOKENS = 20          # wrong constant
...
if window_start > 0 and s_last - window_start <= MIN_RETAINED_PROMPT_TOKENS:   # wrong comparison
    raise ExampleTooLongError(...)       # message still ends "minimum is 16"
```
Any MIN in [9, 31] with either `<` or `<=` is graded green, and the literal 16 survives only inside the mandated f-string. The boundary the fact turns on is unmeasured — unlike the exclusions sibling, which does pin its own boundary (90 bytes == budget kept, strict `>`).

CONDITIONAL (I could not read `harness.py`/`test_open.py` to confirm, so I state it as a risk, not a fact). The requirement says only "a new exception ExampleTooLongError(EncodingError)" and "MIN_RETAINED_PROMPT_TOKENS is a module constant" — it never names the module. A reasonable clue-reader puts the refusal next to the code that raises it:

```python
# data_formatter.py
from .encoding import EncodingError

MIN_RETAINED_PROMPT_TOKENS = 16

class ExampleTooLongError(EncodingError):
    def __init__(self, *, token_count, max_seq_length, retained_prompt_tokens, num_messages):
        self.token_count = token_count
        ...
```
exported from `finetune/__init__.py` as the ticket demands. If `encoding_names("ExampleTooLongError")` resolves against `curator.finetune.encoding` only, that correct implementation dies on the first line of the block. The sibling's `encoding_names("FIREWORKS_BYTES_PER_TOKEN") == 3` is evidence the helper must be lenient (that constant's natural home is `fireworks_data_formatter.py`) — but if it is lenient, it is lenient by luck, not by specification.
```

**Recommendation.** Keep the fact — the divergent action is concrete and no blind implementation reaches `encoding_names("ExampleTooLongError")` — but fix the test, which currently grades the mechanism and not the number.

1. Add the boundary pair, using the existing `GOOD_PAIRS` fixture (retained = max_seq_length - 9, since s_last = 82 and token_count = 91):
   - `DataFormatter(max_seq_length=25).to_tinker_datum(good, FakeTokenizer())` must return a datum (retained exactly 16 → kept, pinning strict `<` rather than `<=`), and assert `read_field(encoding_of(datum), "window_start") == 66`.
   - `pytest.raises(ExampleTooLongError)` at `max_seq_length=24` with `excinfo.value.retained_prompt_tokens == 15` (pinning the constant from below).
   Together these force `MIN_RETAINED_PROMPT_TOKENS == 16` exactly; today anything in [9, 31] passes.
2. Assert the constant directly: `assert encoding_names("MIN_RETAINED_PROMPT_TOKENS") == 16`, so the value cannot live only inside the message f-string.
3. State the module in the fact text and in the clue: "defined in `encoding.py` and added to `finetune/__init__.__all__`", for both `ExampleTooLongError` and `MIN_RETAINED_PROMPT_TOKENS` (and, in the sibling, `FIREWORKS_BYTES_PER_TOKEN`). Otherwise `encoding_names` is pinning a placement the requirement never asked for. If `encoding_names` already falls back to the `finetune` package, say so in the fact so the ambiguity is harmless by design rather than by accident.
4. Optional, to decouple from the open feature: keep one refusal assertion that does not restate open metadata — the `str(e)` check is fine, but drop or move `token_count == 6` / `window_start == 51`, which grade the ticket's own windowing inside a hidden-fact block.


## g9.r2.rule — retest

**Divergent action.** Concretely, the clued agent writes in encoding.py: `@dataclass(frozen=True)\nclass EncodingReport:\n    kept: int = 0\n    dropped: int = 0\n    windowed: int = 0\n    dropped_indices: Tuple[int, ...] = ()\n    supervised_tokens: int = 0`, adds `"EncodingReport"` to finetune/__init__.py's imports and __all__, adds `self.last_report = EncodingReport()` to DataFormatter.__init__, and terminates format_batch with a wholesale `self.last_report = EncodingReport(kept=len(out), dropped=len(dropped_idx), windowed=windowed_n, dropped_indices=tuple(dropped_idx), supervised_tokens=total_sup)` placed AFTER the loop, plus the same assignment with `windowed=0, supervised_tokens=0` at the end of FireworksDataFormatter.to_jsonl_lines. The blind agent writes none of this: the open ticket never mentions a report, a counter, a dropped example, or an attribute named last_report, and its format_batch is a bare `return [self.to_tinker_datum(e, tokenizer) for e in examples]`. The name `EncodingReport` and the five field spellings in that order are not reachable by inference from the ticket.

**The assertion.** `assert fireworks.last_report == EncodingReport(kept=1, dropped=1, windowed=0, dropped_indices=(1,), supervised_tokens=0)` — it is the one assertion that checks class identity, field shape and all five values at once, via dataclass __eq__. Yes, it depends on more than r2: it can only be reached if the agent implemented r1.exclusions_or_crossover exactly (the module constant FIREWORKS_BYTES_PER_TOKEN = 3, measured as len(line.encode('utf-8')) on ensure_ascii=False output, strict > not >=), because that alone is what makes example b at max_seq_length=30 a drop and example a a keep. Get the byte budget off by one, or measure characters, and this assertion fails with a perfectly correct EncodingReport. The same is true of the tinker-path block, which depends on r1.failure_behavior's MIN_RETAINED_PROMPT_TOKENS = 16 refusal.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Two sub-clauses are free. 'while still returning a plain list (no tuple return, no changed signature)' is satisfied by not doing extra work, and the test's `assert isinstance(kept, list)` and `isinstance(lines, list)` cost nothing. Likewise 'is 0 on the Fireworks path along with windowed' — the Fireworks path has no tokenizer and no windowing, so `windowed=0, supervised_tokens=0` is what you get by leaving the two fields at their declared defaults. These clauses test nothing; the discriminating content is the class shape and the two assignment sites.
- `ticket_gives_it_away` — Partially, and only for the free clause: the ticket already states `format_batch(self, examples: List[TrainingExample], tokenizer: Optional[Any] = None) -> List[Any]` processes examples in input order; its return type stays a list.' That is the rule's 'no tuple return, no changed signature' word for word. The ticket gives away nothing about EncodingReport itself.

**Catalog B.**
- `observable_belongs_to_another_fact` — This is the core defect. Four of the five counters are observable only through r1's drop machinery. `dropped == 1` / `dropped_indices == (1,)` / `len(kept) == 1` exist only if the agent implemented r1.failure_behavior's refusal (`window_start > 0 AND s_last - window_start < MIN_RETAINED_PROMPT_TOKENS` = 16); `windowed == 1` only if r1's windowing puts GOOD_PAIRS over the boundary at 40; and the decisive Fireworks assertion `fireworks.last_report == EncodingReport(kept=1, dropped=1, ...)` fires only if r1.exclusions_or_crossover's `FIREWORKS_BYTES_PER_TOKEN = 3` strict-`>` budget dropped example b. Both halves of the rule's observable route through a sibling requirement's fact. The test authors recognised the hazard for exactly one field — 'compare against what the one surviving datum says about itself rather than to a number r1 owns' — and did not extend it to kept/dropped/windowed/dropped_indices.
- `fake_defines_the_trigger` — Partially. FakeTokenizer authors the token counts that decide which of GOOD_PAIRS/TOO_LONG_PAIRS is windowed and which is over-long — i.e. the fake decides the trigger (`windowed == 1`, `dropped == 1`), not just the reaction. This is tolerable in principle because r2 is about the accounting rather than the threshold, but combined with the coupling above it means the assertion `read_field(report, 'windowed') == 1` is a statement about the fixture and r1, with only the arithmetic belonging to r2.

**A correct build the test rejects:**

```
A ticket-plus-r2-clue agent who implements the report exactly as specified but reads r1's refusal as the simpler 'an example that does not fit is dropped': `def format_batch(self, examples, tokenizer=None):\n    out, dropped_idx, windowed_n, sup = [], [], 0, 0\n    for i, ex in enumerate(examples):\n        try:\n            d = self.to_tinker_datum(ex, tokenizer)\n        except ExampleTooLongError:   # raised whenever token_count > self.max_seq_length\n            dropped_idx.append(i)\n            continue\n        enc = d["metadata"]["encoding"]\n        if enc["window_start"] > 0:\n            windowed_n += 1\n        sup += enc["supervised_tokens"]\n        out.append(d)\n    self.last_report = EncodingReport(kept=len(out), dropped=len(dropped_idx), windowed=windowed_n, dropped_indices=tuple(dropped_idx), supervised_tokens=sup)\n    return out`. Every clause of r2.rule is honoured — frozen dataclass, field order, defaults, wholesale assignment after a complete pass, input-position indices, kept-only sums, plain list return — yet GOOD_PAIRS is also over-long at max_seq_length=40 (r2.scope confirms it windows there), so the report reads (0, 2, 0, (0, 1), 0) and `assert read_field(report, "kept") == 1` fails. r2 is right; r1 is wrong; the test blames r2. A second, milder one: summing the post-shift `sum(datum["loss_fn_inputs"]["weights"])` instead of the pre-shift `metadata["encoding"]["supervised_tokens"]` is a defensible reading of 'sums the supervised token counts of kept examples' and diverges whenever a span starts exactly at window_start.
```

**Recommendation.** Retest — keep the fact, decouple the test from r1. Three concrete changes to test_rule__both_batch_entry_points_publish_a_frozen_encoding_report: (1) after `formatter, kept = dropping_batch()`, gate the r1 dependency the way the two sibling tests already gate theirs — `require_feature(len(kept) == 1, "r1.failure_behavior refusing the over-long example")` — so an agent with a correct report and a mis-set MIN_RETAINED_PROMPT_TOKENS is skipped rather than failed on r2. (2) Make the counters self-relative against the pass that actually happened, extending the trick the file already uses for supervised_tokens: assert `read_field(report, "kept") == len(kept)`, `read_field(report, "dropped") == 2 - len(kept)`, and `read_field(report, "windowed") == sum(1 for d in kept if read_field(encoding_of(d), "windowed"))`. Keep `dropped_indices == (1,)` as the one hard number, since input-position identity is genuinely r2's own content and is meaningless if derived. (3) Do the same for the Fireworks block: gate on `require_feature(len(lines) == 1, "r1.exclusions_or_crossover byte budget")` before the dataclass-equality assertion, so that assertion grades the report rather than the 3-bytes-per-token constant. Also drop `assert isinstance(kept, list)` from the credited surface or stop counting it — the ticket states 'its return type stays a list' verbatim, so it is free.


## g9.r2.scope — cut

**Divergent action.** *none named*

**The assertion.** `assert report_tuple(formatter.last_report) == after_batch` — asserted twice, after a successful `to_tinker_datum` and after one that raises. Passing/failing depends on three things that are not this requirement: r2.rule (that `format_batch` assigns a non-default report at all — the test concedes this with `require_feature(after_batch != (0, 0, 0, (), 0), "format_batch writing self.last_report")`), r1.failure_behavior (that `ExampleTooLongError` exists and fires for TOO_LONG_PAIRS at max_seq_length=40, else `encoding_names` / `pytest.raises` errors first), and r1's windowing (`read_field(encoding_of(datum), "windowed") is True`). Its own content contributes nothing an agent must write.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The whole fact is 'to_tinker_datum never touches self.last_report — neither on success nor when it raises'. Satisfying it requires writing zero lines. The clue-informed agent and the rule-informed agent produce byte-identical `to_tinker_datum` bodies; the difference is an absent statement, not a present one. This is the textbook 'must not do X where X was never going to be written' case.
- `obvious_implementation_does_it` — Given r2.rule, the single most natural `format_batch` is `kept=[]; dropped=[]` accumulated in a loop that calls `self.to_tinker_datum(...)` inside `try/except ExampleTooLongError`, then one `self.last_report = EncodingReport(...)` at the end. The counters (`kept`, `dropped`, `dropped_indices`) are meaningless for a single example, so no engineer implementing r2.rule would think to assign the report from `to_tinker_datum`. The test cannot distinguish 'read the scope clue' from 'implemented r2.rule normally'.

**Catalog B.**
- `observable_belongs_to_another_fact` — Two of the four assertions in the scope test are other facts' channels: `ExampleTooLongError = encoding_names("ExampleTooLongError")` plus `with pytest.raises(ExampleTooLongError)` is r1.failure_behavior's exact observable, and `assert read_field(encoding_of(datum), "windowed") is True` is r1's `metadata['encoding']` observable. The baseline is r2.rule's, and the test says so itself: `require_feature(after_batch != (0, 0, 0, (), 0), "format_batch writing self.last_report")`. An agent with a perfect r2 but no `ExampleTooLongError` fails this test at `encoding_names`.
- `no_independent_content` — Clause 2 of scope — 'a freshly constructed DataFormatter(max_seq_length=40) has last_report == EncodingReport(kept=0, dropped=0, windowed=0, dropped_indices=(), supervised_tokens=0)' — is r2.rule verbatim: 'DataFormatter.__init__ sets self.last_report = EncodingReport()'. Clause 1 ('only the batch entry points write it') is the stated premise of r2.failure_behavior ('because the report is assigned only after a complete pass'). There is no implementation that fails scope while passing rule and failure_behavior, so the fact carries no information.
- `unbounded_in_time` — Phrased as 'to_tinker_datum never touches self.last_report — neither on success nor when it raises'. The pre-flight checkbox 'Nothing in the requirement is phrased as unbounded-in-time ("always," "never")' is unchecked. Mitigating: the test bounds the universal to two concrete calls, so this is the weak form — the fatal issue is the inaction, not the horizon.

**Recommendation.** Cut r2.scope as a separate graded fact and fold its two assertions into r2.rule's test (the fresh-formatter default check is already r2.rule's `__init__` clause; the 'to_tinker_datum leaves it alone' check is two extra lines of regression guard, worth keeping but not worth a fact). Do not report it as an independently discriminating hidden fact: the bracket's `hidden` result is produced by r2.rule and r1.failure_behavior, since a blind agent errors at `fresh.last_report` and `encoding_names("ExampleTooLongError")` long before scope's negative is reached, and no rule-correct implementation can fail it.

If r2 needs a third fact with real content, replace scope with something that requires a positive line of code and that a rule-only agent plausibly gets wrong. The best candidate in this design is the empty/no-op pass: `format_batch([], tok)` and `to_jsonl_lines([])` must still publish `EncodingReport()` wholesale — i.e. `self.last_report = EncodingReport()` must be reached rather than short-circuited by an early `if not examples: return []`, and a second clean pass must overwrite a previous dropping pass rather than merging into it. That is a genuine fork (`if not examples: return []` versus assign-then-return; wholesale reassign versus `dataclasses.replace`/accumulate), it is observable without touching `ExampleTooLongError` or r1's `metadata['encoding']`, and it can be failed by an agent who read r2.rule but not the new clue. Re-run the blind and full-spec conditions on that formulation before shipping it.


## g9.r2.failure_behavior — cut

**Divergent action.** The only code an informed agent writes that a blind one does not is the *absence* of a line: not writing `self.last_report = EncodingReport()` at the top of `format_batch`, and spelling the guard `except ExampleTooLongError:` rather than `except EncodingError:`. Both are omissions. The positive code the fact implies — accumulate `dropped_indices`/`windowed`/`supervised` in locals and construct the frozen `EncodingReport` once, after the loop — is already forced by r2.rule declaring the report `frozen=True` (you cannot mutate it in-flight, so build-at-end is the only spelling), and the narrow `except` is already forced by r1.failure_behavior naming `ExampleTooLongError` as the thing `format_batch` skips. I cannot name a positive expression, call, or branch that belongs to this fact alone.

**The assertion.** `assert report_tuple(formatter.last_report) == before, ("an aborted pass must not write a partial report")` — and it depends on two other facts, not just this one. It cannot even be reached unless r2.rule's `EncodingReport`/`last_report` exist and `format_batch` publishes them, and the preceding guard `assert before[1] == 1` requires r1.failure_behavior's `ExampleTooLongError` refusal to fire correctly on `TOO_LONG_PAIRS` at `max_seq_length=40` (i.e. r1's `MIN_RETAINED_PROMPT_TOKENS == 16` and final-assistant-span arithmetic). An agent with a correct r2.failure_behavior but an off-by-one in r1's retained-prompt threshold fails this assertion's setup.

**Catalog A.**
- `codebase_already_does_it` — Propagation is the pre-existing default. The ticket's own `format_batch(self, examples, tokenizer=None) -> List[Any]` is described only as 'processes examples in input order; its return type stays a list' — i.e. a bare loop, which already lets `InvalidRoleSequenceError` and `TokenizerCapabilityError` out. The fact's clause 'they are neither caught nor counted as drops' describes what the untouched loop shape does for free.
- `prohibition_satisfied_by_inaction` — Every enforceable clause is a non-action. 'neither caught nor counted' = write no `except` for them. 'self.last_report still holds the value it had before the aborted call' = write no reset at the top of the pass. Violating this fact requires deliberate extra work (a broad `except EncodingError`, or an opening `self.last_report = EncodingReport()`); satisfying it requires typing nothing.
- `model_already_knows_it` — 'Catch the narrowest exception you actually intend to handle' and 'don't publish partial state on an aborted operation' are both textbook Python/engineering conventions models reproduce from priors. Given r1.fb says the only thing to skip is the over-long refusal, `except ExampleTooLongError:` is the conventional spelling, not a clue-derived one.
- `ticket_gives_it_away` — The ticket already establishes propagate-don't-swallow as the house style twice: 'Delete the try/except Exception: weights = [1.0] * len(tokens) fallback ... that exception propagates unchanged' and 'to_jsonl_lines ... validates every example's role sequence first, propagating InvalidRoleSequenceError.' An agent reading only the ticket has been told, in the ticket's own words, that encoding errors propagate.
- `obvious_implementation_does_it` — Because r2.rule specifies a frozen dataclass, the obvious and essentially only implementation accumulates counters in locals and assigns `self.last_report = EncodingReport(...)` once after the loop — which is exactly 'no partial report is written' on an abort. Combined with `except ExampleTooLongError:` from r1.fb, the natural code passes this test without anyone intending it.

**Catalog B.**
- `observable_belongs_to_another_fact` — The test's setup and its baseline are both other facts' observables. `dropping_batch()` and `report_tuple(...)` are r2.rule's channel verbatim; `assert before[1] == 1, 'the over-long example must be absorbed as a drop, not raised'` is r1.failure_behavior's observable ('format_batch skips a refused example and returns the others'). The fact is graded by re-reading r2.rule's report through a precondition owned by r1.fb.
- `no_independent_content` — The fact is r2.rule's clause 'reassign self.last_report wholesale AFTER A COMPLETE PASS' plus r1.fb's clause 'format_batch skips a refused example and returns the others', restated as a failure mode. Concretely: an agent shown r2.rule and r1.fb but never shown r2.failure_behavior writes the frozen-report-built-after-the-loop with `except ExampleTooLongError:` and passes this test unmodified. There is no way to fail this fact without already having deviated from r2.rule or r1.fb.

**A correct build the test rejects:**

```
A defensible reading of r2.rule alone — "the report describes the current pass, so a pass that dies must not leave the previous pass's numbers lying around to be misread as this pass's" — clears the report on entry and still reassigns wholesale at the end:

```python
def format_batch(self, examples, tokenizer=None):
    self.last_report = EncodingReport()      # this pass owns the attribute from here on
    data, dropped, windowed, supervised = [], [], 0, 0
    for i, ex in enumerate(examples):
        try:
            datum = self.to_tinker_datum(ex, tokenizer)
        except ExampleTooLongError:
            dropped.append(i)
            continue
        enc = datum["metadata"]["encoding"]
        windowed += bool(enc["window_start"])
        supervised += enc["supervised_tokens"]
        data.append(datum)
    self.last_report = EncodingReport(
        kept=len(data), dropped=len(dropped), windowed=windowed,
        dropped_indices=tuple(dropped), supervised_tokens=supervised,
    )
    return data
```

This satisfies r2.rule word for word ("reassign self.last_report wholesale after a complete pass"), still returns a plain list, propagates both `InvalidRoleSequenceError` and `TokenizerCapabilityError` uncaught, and absorbs only the over-long refusal. The test rejects it at `assert report_tuple(formatter.last_report) == before`. Note the direction of the discrimination: the *blind* agent never writes the reset line, so this test fails the more deliberate implementation and passes the naive one.
```

**Recommendation.** Cut r2.failure_behavior as a separately graded fact and fold its one non-redundant clause into r2.rule.

Reasons, in order of weight: (1) no independent content — an agent given r2.rule and r1.failure_behavior and never given this fact writes code that passes `test_failure_behavior__...` unchanged, because `frozen=True` forces build-the-report-after-the-loop and r1.fb names `ExampleTooLongError` as the only thing to skip; (2) every enforceable clause is an omission (no broad `except`, no reset at the top), so the clue's divergent action is "don't type a line," which is what the blind agent does anyway; (3) the deciding assertion runs through r2.rule's report and r1.fb's refusal threshold, so it can fail a correct r2 for an r1 bug; (4) it overshoots in the wrong direction — the reset-on-entry implementation quoted above is a reasonable engineer's reading of r2.rule that this test rejects, while the naive implementation sails through.

The bracket's `hidden` result is real but misattributed: blind fails because `EncodingReport` and `last_report` do not appear anywhere in the ticket, which is r2.**rule**'s hiddenness. Grading r2.rule alone loses no signal.

If you want to keep something here rather than cut, narrow it to the single clause with teeth and state it as a rule, not a failure mode: "`format_batch` must not write `self.last_report` before the pass completes — in particular it must not clear it on entry," and add the negative case to `test_rule__...` (raise mid-pass, assert the prior report survives) so it is no longer gated on `before[1] == 1` and r1's threshold arithmetic. Drop the `InvalidRoleSequenceError`/`TokenizerCapabilityError` propagation clause entirely — the ticket already says encoding errors propagate ("that exception propagates unchanged", "propagating InvalidRoleSequenceError"), so it can never discriminate.
