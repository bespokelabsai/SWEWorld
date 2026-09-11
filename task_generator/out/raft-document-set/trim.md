# g13 — the requirement, reduced to what is graded

**678 words → 456** across 8 facts and 58 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g13.r1.rule` | 83 → 44 | 12 | 6 |
| `g13.r1.scope` | 79 → 64 | 5 | 2 |
| `g13.r1.exclusions_or_crossover` | 105 → 73 | 7 | 3 |
| `g13.r1.observability` | 24 → 16 | 6 | 2 |
| `g13.r2.rule` | 68 → 53 | 6 | 2 |
| `g13.r2.scope` | 97 → 58 | 4 | 2 |
| `g13.r2.exclusions_or_crossover` | 89 → 66 | 7 | 5 |
| `g13.r2.failure_behavior` | 133 → 82 | 11 | 7 |

## `g13.r1.rule`

**Now (44 words):**

A new module-level mutable `@dataclass class RaftDrawStats` with exactly two fields in this order, `document_sets: int = 0` and `with_oracle: int = 0`, plus one method `oracle_rate(self) -> float` returning `self.with_oracle / self.document_sets` (and `0.0` when `document_sets == 0`). `_RaftAnswer.__init__` sets `self.stats = RaftDrawStats()`.

**Dropped, because no assertion checks it:**

- " after `self.formatter`" — the placement of the assignment relative to the formatter line; no assertion reads where in `__init__` `stats` is set, only that it exists, equals a zeroed RaftDrawStats, and is per-instance.
- "Nothing in the block reads `stats`." — a negative claim about the rest of the block; nothing checks that no other code touches it.
- "it exists so a finished run can be asked what oracle rate it actually realised" — the reason the field exists. A rationale is never asserted.
- "Checkable: `[f.name for f in dataclasses.fields(RaftDrawStats)] == [\"document_sets\", \"with_oracle\"]`" — a restatement of the field names and order already fixed by the opening sentence (assertion #2).
- "`RaftDrawStats() == RaftDrawStats(document_sets=0, with_oracle=0)`" — a restatement of the `= 0` defaults already written into the field declarations (assertions #3, #4, #5).
- "`RaftDrawStats().oracle_rate() == 0.0`" — a worked example of the zero guard that the parenthetical "(and `0.0` when `document_sets == 0`)" already pins (assertion #6).

**Kept despite looking like padding:** "mutable" reads like an adjective for flavour, but assertion #9 asserts `rate_of(fresh) == 0.5` on the same `fresh` object that assertion #6 saw at `0.0`, so the test mutates the fields in place; a `frozen=True` dataclass would fail there. It stays. "module-level" also stays because every assertion constructs `RaftDrawStats` by bare name, so it must be importable from the module rather than nested.

## `g13.r1.scope`

**Now (64 words):**

The counters follow document-set builds, not emitted rows: exactly one increment of `document_sets` per build that actually runs, plus one of `with_oracle` when that build's coin said the oracle is present. A memoised replay increments nothing. On the five-chunk fixture parsed with `(0,"Who?")`, `(0,"What?")`, `(2,"Who?")`, `(0,"Who?")` — four `parse` calls, one of them a repeat — `gen.stats == RaftDrawStats(document_sets=3, with_oracle=2)` and `gen.stats.oracle_rate() == 0.6666666666666666`.

**Dropped, because no assertion checks it:**

- The fixture-construction parenthetical: "(`["alpha","bravo","charlie","delta","echo"]`, `distractors=2`, `p=0.5`, `sampler=lambda pop, k: list(pop)[:k]`, `rng=random.Random(7)`)" — the harness constructs the generator, no assertion reads the chunk list, distractor count, p, sampler or seed, and fixture guards are excluded from grading.
- The closing counter-example sentence: "Counting `parse` calls instead gives `RaftDrawStats(document_sets=4, with_oracle=3)`." — the "builds, not parse calls" rule restated as its negation; it is already pinned by the opening sentence and the retained example, and nothing asserts the values 4 and 3.

**Kept despite looking like padding:** The worked example ("On the five-chunk fixture parsed with ... four `parse` calls, one of them a repeat ... `RaftDrawStats(document_sets=3, with_oracle=2)` ... `oracle_rate() == 0.6666666666666666`") reads like padding beside the rule sentence, but it stays: #1 needs one row per parse call across four calls, #2 turns on one call being a repeat that replays rather than redraws, #3 and #4 read the `document_sets` and `with_oracle` field names off `gen.stats`, and #5 calls the `oracle_rate()` accessor, whose name appears nowhere else in the text.

## `g13.r1.exclusions_or_crossover`

**Now (73 words):**

The document-set builder takes a third positional parameter `question: Question` which participates in the memoisation key, and `parse` passes `(chunk_id, oracle_document, question)` positionally in that order. A repeat of the same `(chunk_id, question)` replays the memoised `DocumentSet` and consumes no rng. On the fixture above, a spy rng records exactly three `"random"` calls across the four `parse` calls, and `rows[3] == rows[0]` while `rows[1]` (`oracle_present=False`) differs from `rows[0]` (`oracle_present=True`) on the same chunk.

**Dropped, because no assertion checks it:**

- "The unit the oracle coin is drawn per is the question, not the chunk:" — framing restatement of the memoisation-key rule; no assertion reads the coin's "unit", only the call count.
- "and in nothing else" — a negative scope limit on the `question` parameter; nothing checks that `question` fails to influence anything besides the memoisation key.
- "; two different questions on one chunk get independent coins and can differ in `oracle_present`" — the abstract second statement of a rule the fixture sentence already pins with the exact literals (`rows[0]` True, `rows[1]` False, same chunk) that assertions #3, #4 and #5 read.

**Kept despite looking like padding:** "and consumes no rng" reads like a restatement of "replays the memoised `DocumentSet`", but assertion #7 (`rng.calls.count("random") == 3`, "the replay drew no new coin") grades exactly that, separately from #2 and #6 which grade the replayed value. Likewise "across the four `parse` calls" looks like scene-setting, but assertion #1 counts three `"random"` calls against four `parse` calls and names the wrong answers (2 for chunk-only keying, 4 for none), so both counts have to be stated.

## `g13.r1.observability`

**Now (16 words):**

The memoisation bound is `functools.lru_cache(maxsize=512)`: `gen._get_document_set.cache_info()` on the four-call fixture above `== CacheInfo(hits=1, misses=3, maxsize=512, currsize=3)`.

**Dropped, because no assertion checks it:**

- "on any constructed `_RaftAnswer`," — a second staging site for a claim the decorator already makes. Assertion #2's fresh (0, 0, 0) is what lru_cache returns before the first call, not a design decision the sentence has to pin.
- "`.cache_info().maxsize == 512`, and" — restatement of the `maxsize=512` already written inside `functools.lru_cache(maxsize=512)`; assertions #1 and #3 both follow from the decorator argument alone. The `.cache_info()` call itself was kept and spliced onto the surviving fixture clause.

**Kept despite looking like padding:** "on the four-call fixture above" plus the whole `CacheInfo(hits=1, misses=3, maxsize=512, currsize=3)` literal reads like a worked example, but #4 (hits + misses == len(CALLS)), #5 (currsize == misses) and #6 (hits >= 1) all turn on those exact numbers and on the fixture they are measured over, so the example is the specification. `gen._get_document_set` stays because the assertions read cache_info() off that name; `maxsize=512` appears twice because #1 and #3 grade it in both the decorator and the reported CacheInfo.

## `g13.r2.rule`

**Now (53 words):**

A new module-level `InsufficientDistractorsError(ValueError)` raised by the document-set builder when the corpus cannot supply the distractors. It is constructed `InsufficientDistractorsError(chunk_id=chunk_id, requested=requested, available=available)` and carries exactly those three attributes. On chunks `["a","b","c","d"]` with `distractors=3` and `chunk_id=2`: `(exc.chunk_id, exc.requested, exc.available) == (2, 4, 3)` and `str(exc) == "chunk 2: requested 4 distractors, only 3 available"`.

**Dropped, because no assertion checks it:**

- ", and `str(exc)` is exactly `f"chunk {chunk_id}: requested {requested} distractors, only {available} available"`" - the general message template, said a second time as a literal by the worked example, which is the form assertions #3 and #6 actually check.
- "`isinstance(exc, ValueError)` is `True`," - restates the `(ValueError)` base already declared in the opening sentence, which is what assertion #1 reads.

**Kept despite looking like padding:** "raised by the document-set builder when the corpus cannot supply the distractors" reads like background but is the raise condition assertion #4 exercises through `pytest.raises`, with #5 and #6 reading the instance that escapes that call. The full keyword constructor signature stays because the test constructs `built` with those exact keywords before #2 and #3 inspect it. The worked example's inputs (`["a","b","c","d"]`, `distractors=3`, `chunk_id=2`) stay because they pin how `requested == 4` is derived, which #2 checks.

## `g13.r2.scope`

**Now (58 words):**

The check is the builder's first statement and consumes no randomness: `available = len(self.chunks) - 1`, `requested = self.distractors + 1` — the oracle-absent worst case, regardless of how the coin would land — and it raises when `available < requested`. With `p=1.0`, `parse({"chunk_id": 2, "question": "Q"}, "resp")` still raises, and a spy rng records `rng.calls == []`.

**Dropped, because no assertion checks it:**

- "So a corpus with `len(chunks) - 1 == distractors` fails on every chunk deterministically instead of only on the chunks that happen to draw the absent branch:" — a "so" consequence restating the raise rule already pinned by `available < requested`; no assertion checks per-chunk determinism or the absent branch.
- "(where the present branch would need only 3 of the 3 available)" — parenthetical rationale for why `p=1.0` is the interesting setting; no assertion reads the present-branch arithmetic.

**Kept despite looking like padding:** The `p=1.0` clause plus `parse({"chunk_id": 2, "question": "Q"}, "resp")` reads like a second demonstration of "regardless of how the coin would land", but it is the one worked example carrying literals and it is what forces #1 (`pytest.raises(ValueError)`) to hold on the coin setting that would otherwise succeed. `rng.calls == []` is quoted verbatim by #2, and "the builder's first statement and consumes no randomness" is the rule #2's failure message states ("the availability check runs before any draw").

## `g13.r2.exclusions_or_crossover`

**Now (66 words):**

In `Raft.__call__`'s list branch only, entries whose `str.strip()` is empty are dropped and the survivors are renumbered contiguously from `0`. With kwarg-recording stubs, `Raft(model="m", ...)(["alpha", "", "  ", "\n", " bravo "])` gives `len(StubA.kw["chunks"]) == 2`, `StubA.kw["chunks"]["content"] == ["alpha", " bravo "]`, `StubA.kw["chunks"]["chunk_id"] == [0, 1]`; `(["", "   ", "\t\n"])` gives `len(...) == 0` with `column_names == []`; `("abcdefghij")` gives `content == ["abcdefghij"]`, `chunk_id == [0]`.

**Dropped, because no assertion checks it:**

- "before chunk ids are assigned" — ordering narration; the example's `chunk_id == [0, 1]` is what is graded.
- "; surviving text is stored verbatim, surrounding whitespace kept" — restatement of the literal `["alpha", " bravo "]`, which assertion #2 reads directly.
- "The `str` branch is untouched." — restatement of the third example, whose `content == ["abcdefghij"]` / `chunk_id == [0]` are what assertions #6 and #7 read.
- "and raises nothing here" — no assertion checks for an exception.
- "still" — filler adverb in the str-branch example.

**Kept despite looking like padding:** All three worked examples stay: they are not repetitions of one rule. The five-entry list pins #1–#3, the all-blank list pins #4 and #5 (`column_names == []` is a separate decision no rule sentence implies), and `("abcdefghij")` pins #6 and #7. "With kwarg-recording stubs" stays because the asserted values are read off `StubA.kw["chunks"]`, so the observation point is part of the spec.

## `g13.r2.failure_behavior`

**Now (82 words):**

`_RaftAnswer.__init__` validates its two numeric knobs before `super().__init__(*args, **kwargs)` runs, `p` before `distractors`, raising plain `ValueError` (never `InsufficientDistractorsError`): `p` outside the closed interval gives `"p must be in [0.0, 1.0], got 1.5"`, and `distractors < 1` gives `"distractors must be >= 1, got 0"`. `p=0.0`, `p=1.0` and `distractors=1` all construct. `_RaftAnswer(chunks=..., model_name="gpt-4o-mini", backend="nope")` raises `ValueError("Unknown backend: nope")`, while adding `p=1.5` to that same call raises `"p must be in [0.0, 1.0], got 1.5"`. `Raft` itself does not re-check, so `Raft(model="m", p=1.5)` constructs.

**Dropped, because no assertion checks it:**

- "as its first statements," - restatement of the ordering already given by "before `super().__init__(*args, **kwargs)` runs"; assertion #10 turns only on the before-super ordering.
- ", which is reserved for the corpus-size failure" - the reason that class is off-limits. Assertion #3 checks only `not isinstance(caught.value, error_cls)`.
- " / \"p must be in [0.0, 1.0], got -0.1\"" - second worked example of a message template already pinned by the `got 1.5` literal plus "outside the closed interval".
- " / \"distractors must be >= 1, got -2\"" - second worked example of a message template already pinned by the `got 0` literal plus `distractors < 1`.
- "`p=1.5, distractors=0` together give the `p` message." - worked example restating the `p` before `distractors` ordering stated in the opening sentence.
- "Placement is visible through the base class:" - framing clause saying why the backend example follows; the example itself is kept verbatim for assertions #7-#10.
- " and fails only when `__call__` builds the answer generator" - downstream behaviour no assertion reaches; #11 only checks `Raft(model="m", p=1.5).p == 1.5`.

**Kept despite looking like padding:** "(never `InsufficientDistractorsError`)" reads like an aside about a class this rule never raises, but assertion #3 asserts `not isinstance(caught.value, error_cls)`, so the name has to be stated. "`p` before `distractors`" likewise looks like a redundant ordering note, but it is the only thing telling an implementer which message wins when both knobs are bad, which assertion #2's parametrized message comparison can turn on.
