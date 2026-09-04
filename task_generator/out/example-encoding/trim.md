# g9 — the requirement, reduced to what is graded

**860 words → 582** across 7 facts and 65 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g9.r1.rule` | 121 → 84 | 8 | 4 |
| `g9.r1.scope` | 169 → 115 | 9 | 5 |
| `g9.r1.exclusions_or_crossover` | 123 → 86 | 6 | 5 |
| `g9.r1.failure_behavior` | 175 → 126 | 17 | 8 |
| `g9.r2.rule` | 143 → 106 | 15 | 4 |
| `g9.r2.scope` | 51 → 26 | 5 | 2 |
| `g9.r2.failure_behavior` | 78 → 39 | 5 | 3 |

## `g9.r1.rule`

**Now (84 words):**

An assistant span (s, e) contributes weight 1.0 to token indices [s, e) only when s >= window_start. A span that begins before the window boundary is zeroed in full. Observable: DataFormatter(max_seq_length=40) with a one-token-per-character tokenizer over messages [user 'u'*30, assistant 'a'*10, user 'v'*5, assistant 'b'*8] (token_count 91, window_start 51, spans (48, 59) and (82, 91)) gives metadata['encoding']['supervised_tokens'] == 9, sum(loss_fn_inputs['weights']) == 9.0, and [i for i, w in enumerate(weights) if w == 1.0] == [30, 31, 32, 33, 34, 35, 36, 37, 38].

**Dropped, because no assertion checks it:**

- "— a partially retained assistant turn is never supervised, not even its surviving tail —": the same rule said again in different words for emphasis. Assertion #2 still follows from "is zeroed in full".
- "while earlier assistant turns that survive whole are supervised normally": a restatement of the first sentence applied to the whole-turn case. Assertions #6, #7 and #8 (window_start 41, supervised_tokens 20, indices range(6, 17) + range(40, 49)) follow from "contributes weight 1.0 ... only when s >= window_start", which is already general over every span.
- "so multi-turn examples keep every complete turn": a "so" clause stating the consequence. Nothing is asserted about multi-turn examples as such.
- "and ends inside the window": a narrowing sub-case. A span beginning before window_start is zeroed whether or not it ends inside, so the shorter clause covers the graded span (48, 59) and more.

**Kept despite looking like padding:** "sum(loss_fn_inputs['weights']) == 9.0" reads as a duplicate of supervised_tokens == 9, but assertion #3 checks sum(weights) == 9.0 and assertions #1 and #4 read the weights list itself (len 39, values {0.0, 1.0}), so the identifier loss_fn_inputs['weights'] — the name the list must be produced under — had to stay. The literal [30, 31, 32, 33, 34, 35, 36, 37, 38] stays verbatim in its original ordering because assertion #2 compares against exactly it.

## `g9.r1.scope`

**Now (115 words):**

The tokenizer=None branch obeys the same policy instead of its current shortcut: the text stays f'<|{msg.role}|>\n{msg.content}\n' per message and the count stays len(chat_text) // 4, but tokens = list(range(len(chat_text) // 4)) goes through the same windowing, and it honours train_on_assistant_only. Spans come from character offsets: for assistant message i, span = (len_before // 4, len_after // 4) where len_before is the length of the text built from messages[:i] and len_after that of messages[:i+1]. train_on_assistant_only=False still yields all-1.0 weights on both paths. Observable: DataFormatter(max_seq_length=1024), no tokenizer, [user 'Hello', assistant 'Hi there!'] -> token_count 9, window_start 0, span (3, 9), metadata['encoding']['supervised_tokens'] == 6, returned weights == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], metadata['encoding']['tokenizer'] is False.

**Dropped, because no assertion checks it:**

- "it is no longer capped at max_seq_length -" : nothing truncates on the mock path; the example runs at max_seq_length=1024 with 9 tokens, and the only capped case (#9) is the tokenizer path.
- "the same retained-prompt floor and the same span rule" : the floor is never exercised (no truncation in any assertion), and the span rule is stated in full in the very next sentence.
- "so the '<|assistant|>' header is INSIDE the supervised span on this path, unlike the tokenizer path where add_generation_prompt=True puts it before the span" : a consequence clause; the offset formula already forces span (3, 9) and supervised_tokens 6.
- "39-character text," : restates token_count 9, which is asserted directly and stated a few words later in the same example.
- "pre-shift weights [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]," : an intermediate value no assertion reads; #5 checks the returned shifted list, kept verbatim.

**Kept despite looking like padding:** "DataFormatter(max_seq_length=1024), no tokenizer" and "window_start 0" read like fixture scaffolding but are graded: #3 asserts window_start == 0 and #1 asserts tokenizer is False. "on both paths" stays because #7/#8 grade train_on_assistant_only=False on the mock path while #9 grades it on the tokenizer path. The f-string, len(chat_text) // 4 and list(range(...)) stay because #2 (token_count 9) and #6 (model_input [0..7]) turn on those literals.

## `g9.r1.exclusions_or_crossover`

**Now (86 words):**

The Fireworks jsonl path never windows or truncates anything: to_jsonl_lines drops any serialized line whose UTF-8 byte length exceeds self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN, where the module constant FIREWORKS_BYTES_PER_TOKEN is 3 (strict >, not >=). The measurement is len(line.encode('utf-8')) on the json.dumps(..., ensure_ascii=False) output. Observable: FireworksDataFormatter(max_seq_length=30) with [user 'qqq', assistant 'ok'] (90-byte line, budget 90) and [user 'qqqqqq', assistant 'ok'] (93 bytes) → len(to_jsonl_lines([a, b])) == 1; and with max_seq_length=33 (budget 99) [user 'héllo wörld', assistant 'ok'] serializes to 100 bytes and is dropped, so to_jsonl_lines([x]) == [].

**Dropped, because no assertion checks it:**

- "inherits the cap as a byte budget and" — framing of where the budget comes from; the arithmetic self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN states it, and the "budget 90"/"budget 99" annotations still land.
- "; a line whose byte length equals the budget is kept" — restatement of the boundary that "(strict >, not >=)" and the 90-byte/budget-90 example both already pin.
- "— not the character count of the line and not len(chat_text) // 4" — negative crossover exclusions; no assertion reads a character count or a //4 estimate.
- "98 characters but" — the character count of the accented line is not asserted; only its 100 bytes decides the drop.
- "the single example" — filler; to_jsonl_lines([x]) already shows the one-element list.

**Kept despite looking like padding:** "never windows or truncates anything" reads like editorializing but assertion #3 checks exactly that — the kept line must round-trip to the whole two-message document. "ensure_ascii=False" stays because assertion #6 reads the literal "héllo wörld" back out of a kept line, which fails under default escaping. "(strict >, not >=)" stays because #4 turns on the equal-to-budget line being kept. Both worked examples stay: the first carries #2/#3/#4 (90 vs 93 bytes), the second carries #5.

## `g9.r1.failure_behavior`

**Now (126 words):**

A new exception ExampleTooLongError(EncodingError). to_tinker_datum raises it when the example was windowed (window_start > 0) AND s_last - window_start < 16, where s_last is the start index of the FINAL assistant span. __init__(self, *, token_count: int, max_seq_length: int, retained_prompt_tokens: int, num_messages: int), all four set as attributes, with retained_prompt_tokens = max(0, s_last - window_start); str(e) == f'example of {token_count} tokens exceeds max_seq_length={max_seq_length}: {retained_prompt_tokens} prompt tokens would survive, minimum is 16'. format_batch skips a refused example and returns the others. Observable: max_seq_length=40 over [user 'u'*10, assistant 'a'*100] raises with token_count == 129, max_seq_length == 40, retained_prompt_tokens == 0, num_messages == 2, isinstance(e, ValueError); the near-miss pair [user 'u'*30, assistant 'a'*10, user 'v'*5, assistant 'b'*8] returns a datum at max_seq_length=40 and raises with retained_prompt_tokens == 8 at max_seq_length=17.

**Dropped, because no assertion checks it:**

- "refuses over-long examples" — the stated purpose of the class. No assertion checks a reason; the raise rule that follows carries the graded content.
- "MIN_RETAINED_PROMPT_TOKENS, where MIN_RETAINED_PROMPT_TOKENS is a module constant equal to 16" — collapsed to the literal 16 in the rule. No assertion imports or reads the constant by name; the threshold value survives both in the rule and in the 'minimum is 16' message literal.
- "Signature is keyword-only:" — no assertion constructs ExampleTooLongError directly, so keyword-only enforcement is unobservable. The parameter list itself was kept verbatim, since #4–#7 read those four names.
- "before super().__init__()" — assignment ordering relative to the base constructor. #4–#8 read only the finished exception object.
- "and num_messages = len(example.messages)" — the definition is fixed by the surviving observables (num_messages == 2 for the two-message example, == 4 for the four-message pair, and #17's metadata num_messages == 4).
- "An example that was NOT windowed is never refused however short its prompt." — a restatement of the rule's first conjunct, which already says the error is raised only when window_start > 0. #14/#15 (window_start == 0, token_count == 6) follow from the conjunct alone.
- "and a windowed example with 16 or more retained prompt tokens is kept" — the inverse restatement of the same threshold; the near-miss example that stays already pins the kept side.
- "(retained 31)" — an intermediate value for the kept near-miss datum. #9 asserts window_start == 51 on that datum, not the retained count.

**Kept despite looking like padding:** "isinstance(e, ValueError)" reads like a redundant note next to "ExampleTooLongError(EncodingError)", but #3 asserts it directly, so it stays. The full "(window_start > 0)" conjunct looks like a detail of the raise condition but is the only thing keeping unwindowed short examples out of the error path, which #14 and #15 check. The entire f-string is #8 verbatim and was untouched, including "minimum is 16". Both worked examples stay: the first carries #4–#8, the second is the sole source of #9–#13 and #16/#17, so neither is a duplicate of the other.

## `g9.r2.rule`

**Now (106 words):**

encoding.py defines a frozen dataclass EncodingReport with exactly the fields kept: int = 0, dropped: int = 0, windowed: int = 0, dropped_indices: Tuple[int, ...] = (), supervised_tokens: int = 0 (that spelling, that order, those defaults), exported from finetune/__init__.py. Both format_batch and FireworksDataFormatter.to_jsonl_lines reassign self.last_report while still returning a plain list. dropped_indices is the ascending tuple of INPUT positions that were dropped; windowed counts only kept examples whose window_start > 0; supervised_tokens sums the supervised token counts of kept examples only, and is 0 on the Fireworks path along with windowed. Observable: FireworksDataFormatter(max_seq_length=30).to_jsonl_lines([a, b]) leaves last_report == EncodingReport(kept=1, dropped=1, windowed=0, dropped_indices=(1,), supervised_tokens=0) by dataclass equality.

**Dropped, because no assertion checks it:**

- "DataFormatter.__init__ sets self.last_report = EncodingReport(), and" — no assertion reads last_report before a formatting call; the field names and defaults of an argument-less EncodingReport() are still pinned by the first sentence and by assertion #4's own construction.
- "wholesale after a complete pass" — a timing/manner nuance no assertion observes; every assertion reads last_report only after the call returns.
- "(no tuple return, no changed signature)" — restatement of "still returning a plain list", which is what #5 and #14 actually check.
- "after fmt = DataFormatter(max_seq_length=40); fmt.format_batch([good, too_long], tok), fmt.last_report.kept == 1, fmt.last_report.dropped == 1, fmt.last_report.windowed == 1, fmt.last_report.dropped_indices == (1,); and" — the second worked example, demonstrating rules the preceding sentence already pins (dropped_indices as ascending input positions, windowed as kept-with-window_start>0, supervised_tokens over kept only); #7–#11 and #13 follow from those rules applied to their fixtures, and the surviving Fireworks example is the one an assertion (#15) turns on by literal equality.

**Kept despite looking like padding:** "exported from finetune/__init__.py" reads like packaging trivia but stays: every assertion (#1–#4, #15) names EncodingReport directly, so the import path has to be stated for the symbol to exist where the tests reach for it. "(that spelling, that order, those defaults)" also stays, since #3 compares the field-name tuple in order and #4 compares the defaults positionally.

## `g9.r2.scope`

**Now (26 words):**

to_tinker_datum never touches self.last_report — neither on success nor when it raises — and a freshly constructed DataFormatter(max_seq_length=40) has last_report == EncodingReport(kept=0, dropped=0, windowed=0, dropped_indices=(), supervised_tokens=0).

**Dropped, because no assertion checks it:**

- "Only the batch entry points write the report." — a summary of the same rule the next sentence states precisely; no assertion reads batch entry points writing, only that to_tinker_datum leaves the value alone.
- "so a single-example call after a batch leaves the attribute at exactly the value the batch left" — a "so" clause restating the preceding rule as a consequence; assertions #3 and #5 already follow from "never touches self.last_report — neither on success nor when it raises".

**Kept despite looking like padding:** The full five-field literal EncodingReport(kept=0, dropped=0, windowed=0, dropped_indices=(), supervised_tokens=0) reads like ceremony next to \"a fresh formatter's report is empty\", but assertion #1 compares report_tuple to (0, 0, 0, (), 0) positionally, so the field names, their values and their ordering all have to stay verbatim. Likewise \"nor when it raises\" looks like a redundant half of the success clause, but assertion #4 exercises exactly the ExampleTooLongError path and nothing else would pin it.

## `g9.r2.failure_behavior`

**Now (39 words):**

format_batch absorbs only the over-long refusal. InvalidRoleSequenceError and TokenizerCapabilityError propagate out of format_batch and abort the pass — they are neither caught nor counted as drops — and self.last_report still holds the value it had before the aborted call.

**Dropped, because no assertion checks it:**

- "because the report is assigned only after a complete pass," — the mechanism/why behind last_report being unchanged; no assertion checks when the assignment happens, only that report_tuple(formatter.last_report) == before.
- "(no partial report is written)" — restatement of the preceding clause about last_report still holding its pre-call value.
- "Observable: with a third example whose roles are [user, user] appended to the batch, format_batch raises InvalidRoleSequenceError and fmt.last_report is still the pre-call EncodingReport." — a worked example that only re-demonstrates the propagate-and-abort rule and the unchanged-report rule already stated; the assertions are pytest.raises(InvalidRoleSequenceError) and an equality on report_tuple, neither of which turns on the [user, user] literal or on the name fmt.

**Kept despite looking like padding:** "— they are neither caught nor counted as drops —" reads like emphasis on "propagate out of format_batch and abort the pass," but it is the only text fixing the drop accounting, which assertion #1 grades: `assert before[1] == 1` requires exactly one drop counted (the over-long refusal) and none added by the raising errors. Without it, "absorbs" could be implemented as a silent skip that never increments the drop counter. "the over-long refusal" and both exact exception names are kept for the same reason — assertions #1, #2 and #4 read them.
