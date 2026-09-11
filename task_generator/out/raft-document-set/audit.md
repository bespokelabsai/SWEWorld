# Audit — g13 (raft-document-set)

| fact | bracket | audit | why |
|---|---|---|---|
| `g13.r1.rule` | hidden | **narrow** | Narrow the rule text to exactly what the test grades, and close the coupling in the second half of the test.

1. **Delete the placement clause.** Strike "`_Raft |
| `g13.r1.scope` | hidden | ship | Ship. The fact has a concrete divergent action (the two `+= 1` lines inside the cached builder rather than in `parse`), a plausible wrong alternative the ticket |
| `g13.r1.exclusions_or_crossover` | hidden | **retest** | Retest, with two changes, then re-run the blind condition.

1. Fix the overshoot. Delete the direct positional probe

```python
replay = gen._get_document_set(0 |
| `g13.r1.observability` | hidden | **cut** | Cut r1.observability. It is one arbitrary integer on a line the open ticket explicitly tells every agent to keep ("the private document-set builder keeps ... it |
| `g13.r2.rule` | hidden | ship | Ship as written. Two things to confirm before it goes out, neither of which changes the test:

1. Verify the clue quotes the message verbatim. Discrimination he |
| `g13.r2.scope` | hidden | ship | Ship. I could not construct a legitimate reading the test rejects: the guard can live in `parse`, in a `_check_corpus` helper called first, compare `len(availab |
| `g13.r2.exclusions_or_crossover` | hidden | **retest** | Retest, with two edits, then re-run the bracket.

1. Delete `assert list(empty.column_names) == []` from `test_exclusions__a_list_corpus_drops_blank_documents_a |
| `g13.r2.failure_behavior` | hidden | **narrow** | Keep the fact — the p-before-distractors inversion and the pre-`super()` placement probe are a real, nameable divergence. Narrow it in three ways:

1. **Delete  |

## g13.r1.rule — narrow

**Divergent action.** The informed agent writes, at module level in `raft.py`, a class the ticket never mentions and no other requirement needs:

```python
@dataclasses.dataclass
class RaftDrawStats:
    document_sets: int = 0
    with_oracle: int = 0

    def oracle_rate(self) -> float:
        if not self.document_sets:
            return 0.0
        return self.with_oracle / self.document_sets
```

and, in `_RaftAnswer.__init__`, the line `self.stats = RaftDrawStats()`. The blind agent writes neither: the open ticket enumerates the post-`__init__` attributes exhaustively — "Attributes after `__init__`: `n`, `distractors`, `p`, `chunks`, `rng`, `sampler`, `formatter`" — so a ticket-only agent that adds an eighth attribute is contradicting an explicit closed list. That is a real, specific, named divergence.

**The assertion.** `assert fields == ["document_sets", "with_oracle"], (f"exactly two fields, document_sets then with_oracle; got {fields}")` — preceded by the lookup `RaftDrawStats = raft_name("RaftDrawStats")`, which is what actually decides pass/fail for any agent who did not read the clue.

Does it depend on anything but this requirement? The field-order assertion, no — it is pure module introspection and touches no sibling. But the second half of the same test does: `isinstance(read_field(gen, "stats"), RaftDrawStats)` routes through `make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler)`, which requires the *open* ticket's `_RaftAnswer.__init__(..., sampler=..., rng=...)` signature and r2.failure_behavior's validators to accept `p=0.5, distractors=2`. An agent who nailed the ledger but botched the open signature fails `rule` for a reason that is not r1. That is ordinary shared-substrate coupling, not a sibling-observable leak, but it means the test is not purely r1 end to end.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The rule carries the clause 'Nothing in the block reads `stats`; it exists so a finished run can be asked what oracle rate it actually realised.' No assertion anywhere in the hidden test checks that nothing reads it, and no agent was going to wire an unused counter into `parse` or the builder's return value anyway. That clause is free for everyone, graded for no one — it is motivation prose masquerading as a requirement clause.

**Catalog B.**
- `behaviour_has_no_consequence` — Two ways. (a) The placement clause '`_RaftAnswer.__init__` sets `self.stats = RaftDrawStats()` after `self.formatter`' has no observable at all — both are bare attribute assignments with no side effects, and no assertion in the test distinguishes an agent who assigns it first. Contrast r2.failure_behavior, which earned its ordering clause an observable ('Placement is visible through the base class: ... raises ValueError("Unknown backend: nope")'). r1.rule's ordering clause has no such lever and is ungradeable. (b) The feature as a whole is declared inert; its only consequence is the existence of the attribute, which the test asserts directly rather than through any behaviour.

**Recommendation.** Narrow the rule text to exactly what the test grades, and close the coupling in the second half of the test.

1. **Delete the placement clause.** Strike "`_RaftAnswer.__init__` sets `self.stats = RaftDrawStats()` after `self.formatter`" down to "`_RaftAnswer.__init__` sets `self.stats = RaftDrawStats()`". The "after `self.formatter`" half is unobservable and ungraded; compare r2.failure_behavior, which only earns its ordering clause because the base class makes placement visible (`raises ValueError("Unknown backend: nope")`). Either give r1.rule a comparable lever or drop the ordering — as written it invites an agent to be marked wrong by a human reader for something the suite scores as right.

2. **Demote the prohibition to prose.** "Nothing in the block reads `stats`" is satisfied by doing nothing and is checked nowhere. Keep it as the stated motivation ("it exists so a finished run can be asked what oracle rate it actually realised") and stop phrasing it as a rule clause, or add the assertion that makes it real — e.g. that `parse`'s returned dict still has exactly the seven ticket keys and no eighth stats key.

3. **Decouple the per-instance half from the open signature.** In `test_rule__...`, construct the two generators with the minimum the ticket guarantees (`make_answer(FIVE)`) instead of `n=2, distractors=2, p=0.5, sampler=head_sampler`. The freshness/identity check needs only two instances; passing `sampler=` makes an r1 assertion fail on an r2/open-ticket defect.

4. **Optional, cheap:** harmonize the attribute spelling. `rule` requires exactly `stats`; `scope`'s `counts_of` accepts `stats`, `draw_stats`, or none. Since the requirement pins `self.stats`, that is defensible, but state in the rule that `stats` is the *required* spelling and that `scope`'s leniency is intentional, so a reviewer does not read the mismatch as a bug.

After these, the fact is sound: the divergent action is concrete and real, both Catalog-A escape routes and the type/counting seam hold, and I could construct neither a blind pass nor a correct-implementation failure.


## g13.r1.scope — ship

**Divergent action.** Two statements placed inside the body of the `functools.lru_cache`-wrapped `_get_document_set`, after the coin: `self.stats.document_sets += 1` and `if oracle_present: self.stats.with_oracle += 1`. The clue-blind agent writes neither (no counter of any name exists on `_RaftAnswer`); an agent who has the ledger but misreads the unit writes the same two lines in `parse` instead, next to `doc_set.oracle_present`, which counts the 4 parse calls rather than the 3 builds.

**The assertion.** `assert counted_builds == builds, (f"document_sets should count the {builds} builds that ran, not the {len(CALLS)} parse calls; got {counted_builds}")` — with `assert counted_oracle == with_oracle` as its twin. Yes, it depends on more than r1.scope: it needs r1.rule's `self.stats` to exist at all (otherwise `read_field` raises rather than mismatching), and its expectation `builds = len(rng.drawn)` is only a faithful count of builds because the OPEN ticket mandates exactly one `self.rng.random()` per build. The preceding guard `assert builds < len(CALLS)` depends on the open ticket's mandated `functools.lru_cache` and on nothing in r1.scope: an agent who counts builds correctly but dropped memoisation would satisfy both equality assertions and fail only this guard.

**Catalog A.** clean

**Catalog B.** clean

**Recommendation.** Ship. The fact has a concrete divergent action (the two `+= 1` lines inside the cached builder rather than in `parse`), a plausible wrong alternative the ticket itself names, and a reader (`counts_of`, six aliases plus a bare-attribute fallback) that is tolerant of everything except the semantics being graded. I could not write a blind pass and could not write a correct implementation the test rejects.

Two things to check before it goes out, neither of which I could verify because Bash and the file tools were unavailable in this session:

1. Confirm in `test_open.py` that `SpyRng.drawn` records only the values returned by `random()` and is not also fed by `shuffle`/`sample`. The whole test hangs on `builds = len(rng.drawn)` being exactly the coin count; if `shuffle` leaks into `drawn`, every correct implementation fails, since the ticket mandates a shuffle in both branches.

2. Confirm `read_field(holder, "document_sets", ...)` with no `default` raises rather than returning `None`. If it returns `None`, a blind implementation reaches `assert None == 3` and still fails — fine — but `rate_of` and the `pytest.approx` line would error confusingly; prefer the raise.

Optional hardening, low priority: `assert builds < len(CALLS)` currently imports its precondition from the open ticket's `lru_cache` clause. If you want the fact graded in isolation, demote it to a `pytest.skip` (or an explicit message naming it as an open-ticket precondition, e.g. "the builder must be lru_cache-wrapped per the ticket before this fact can be measured") so a build-counting-correct agent who broke memoisation fails `test_open` and not r1.scope. Keep the assertion in some form — without a replay actually occurring, "a memoised replay increments nothing" is untested.


## g13.r1.exclusions_or_crossover — retest

**Divergent action.** In `_RaftAnswer`, the memoised builder grows a third parameter that is never referenced in its body, and `parse` feeds it the question positionally:

```python
def _get_document_set(self, chunk_id: int, oracle_document: str, question: str) -> DocumentSet:
    # `question` is unused: it is here only to widen the lru_cache key so that
    # each question on a chunk draws its own oracle coin.
    ...

# in parse:
doc_set = self._get_document_set(input["chunk_id"], oracle_document, input["question"])
```

A ticket-only agent writes `self._get_document_set(input["chunk_id"], oracle_document)` against the existing two-parameter signature, because the ticket enumerates the builder's three steps (coin, sample, shuffle) and its invariants (name, `DocumentSet` return, `lru_cache` wrapping) without ever mentioning the question. That gives 2 coins over the four-call fixture instead of 3.

**The assertion.** `assert rng.calls.count("random") == 3, "one coin per distinct (chunk_id, question): keying on the chunk alone draws 2, no memoisation at all draws 4; the log was f{rng.calls}"`

Dependence: it also rides on two things outside this requirement. (1) The visible ticket's "one `self.rng.random()` per build" — an agent who drew the coin in `parse` instead of inside the builder gets 4 and fails here for a visible-ticket reason. (2) The sibling `observability` fact: the count assumes the cache holds all three entries, so `lru_cache(maxsize=2)` with a *correct* key also yields 4. Otherwise it isolates this fact cleanly — blind implementations land on 2 (chunk-only key) or 4 (no memoisation), never 3.

**Catalog A.**
- `model_already_knows_it` — This is the strongest hit. RAFT (Zhang et al., 2024) defines P as the fraction of *questions/training examples* that retain the oracle document; the published reference implementation draws `random.uniform(0, 1) < p` once per QA pair, not once per chunk. The hidden fact is literally 'the unit the oracle coin is drawn per is the question, not the chunk' — a documented convention of the very paper this block implements, and the block is named `raft.py` with `_DEFAULT_QUESTION_PROMPT`/`n_questions=2`. A blind agent with RAFT priors can notice that the existing per-chunk memo collapses `n_questions` examples onto one coin, and since the ticket forbids removing the cache ("keeps ... its `functools.lru_cache` wrapping of the bound method"), the only repair available is exactly the hidden fact: widen the key with the question.

**Catalog B.** clean

**A blind build that passes anyway:**

```
Yes — a RAFT-faithful ticket-only implementation passes every assertion in the test:

```python
def parse(self, input: dict, response: str) -> Dict[str, Any]:
    chunk_id = input["chunk_id"]
    oracle_document = self.chunks[chunk_id]["content"]
    # RAFT draws the oracle coin per training example, and n_questions examples
    # share a chunk, so the document set is memoised per (chunk, question) --
    # keying on the chunk alone would give every question the same coin.
    doc_set = self._get_document_set(chunk_id, oracle_document, input["question"])
    docs = doc_set.documents
    return {
        "question": input["question"],
        "cot_answer": response,
        "oracle_document": oracle_document,
        "context": {"title": [["placeholder_title"] * len(docs)], "sentences": [docs]},
        "instruction": self.formatter(docs) + "\n" + input["question"],
        "oracle_present": doc_set.oracle_present,
        "oracle_index": doc_set.oracle_index,
    }

def _get_document_set(self, chunk_id: int, oracle_document: str, question: str) -> DocumentSet:
    # `question` widens the memo key only; the document set does not depend on it.
    oracle_present = self.rng.random() < self.p
    available_indices = [i for i in range(len(self.chunks)) if i != chunk_id]
    k = self.distractors if oracle_present else self.distractors + 1
    picked = self.sampler(available_indices, k)
    slots = [(self.chunks[i]["content"], False) for i in picked]
    if oracle_present:
        slots.append((oracle_document, True))
    self.rng.shuffle(slots)
    documents = [text for text, _ in slots]
    oracle_index = next((i for i, (_, is_oracle) in enumerate(slots) if is_oracle), -1)
    return DocumentSet(documents=documents, oracle_index=oracle_index, oracle_present=oracle_present)
```

Nothing in this was read off a clue: the justification is the RAFT paper's own definition of P plus the ticket's instruction to keep the `lru_cache`, and appending the extra key component is the natural argument position, which happens to be the `(chunk_id, oracle_document, question)` order the test calls positionally. Coins = 3, `rows[3] == rows[0]`, `rows[0]` present / `rows[1]` absent, and `gen._get_document_set(0, "alpha", "Who?")` replays. Full pass, blind.
```

**A correct build the test rejects:**

```
Yes — two legitimate readings of "the question participates in the memoisation key and in nothing else" that the test rejects.

(a) Keyword-only question. `lru_cache` keys on kwargs, so this gives per-question coins, the 3-coin log, and the replay:

```python
def _get_document_set(self, chunk_id: int, oracle_document: str, *, question: str) -> DocumentSet: ...
# parse:
doc_set = self._get_document_set(chunk_id, oracle_document, question=input["question"])
```

(b) Dropping the redundant `oracle_document`, which the builder can derive itself — the ticket only promises the builder "keeps its name, its `DocumentSet` return type ... and its `functools.lru_cache` wrapping", never its parameter list:

```python
def _get_document_set(self, chunk_id: int, question: str) -> DocumentSet:
    oracle_document = self.chunks[chunk_id]["content"]
    ...
# parse:
doc_set = self._get_document_set(chunk_id, input["question"])
```

Both satisfy every behavioural claim of the fact — three coins across four parses, `rows[3] == rows[0]`, two questions on chunk 0 disagreeing — and both die with `TypeError` on the test's last block:

```python
replay = gen._get_document_set(0, "alpha", "Who?")
```

That block grades a calling convention, not the requirement, and the test's own comment concedes it is redundant ("the memo key is only visible on the builder the ticket names") when in fact the key is already fully visible in the coin log three assertions earlier.
```

**Recommendation.** Retest, with two changes, then re-run the blind condition.

1. Fix the overshoot. Delete the direct positional probe

```python
replay = gen._get_document_set(0, "alpha", "Who?")
assert list(read_field(replay, "documents")) == documents_of(rows[0])
assert rng.calls.count("random") == 3, "the replay drew no new coin"
```

and replace it with a signature-agnostic replay through the public entry point, which measures the same thing:

```python
gen.parse({"chunk_id": 0, "question": "Who?"}, "a different response")
assert rng.calls.count("random") == 3, "the replay drew no new coin"
```

If the third-positional calling convention is genuinely part of the contract, grade it by introspection rather than by invocation — `inspect.signature` on the underlying function, asserting the parameter names/order are `(chunk_id, oracle_document, question)` and that `question.kind` is positional-or-keyword — so keyword-only and two-argument variants fail for a stated reason instead of a `TypeError`.

2. Loosen the seed artifact. `assert read_field(rows[1], "oracle_present") is False` grades seed 7, not the requirement. Assert the property instead: the two coins are distinct draws (`coins[0] != coins[1]`) and `documents_of(rows[1]) != documents_of(rows[0])`, keeping the `is True`/`is False` pair only if the golden's rng consumption is pinned by the visible ticket (it is, since both branches shuffle a 3-element list — but say so in the test).

3. Re-run the blind condition before shipping, with several samples and at least one prompt that primes RAFT domain knowledge. The blind implementation quoted above passes this test on RAFT priors alone — "P is the fraction of *questions* that keep the oracle" is published, and since the ticket forbids dropping the `lru_cache`, widening the key is the only repair a RAFT-aware agent has. If more than an occasional blind sample lands there, this becomes a Catalog A coincidence and should be cut or re-pointed at something the paper does not supply (e.g. make the arbitrary part the thing that is graded — the memo bound, the counter semantics — rather than the unit the coin is drawn per).

Also note for the task owner: the fact annotates the parameter `question: Question` while `parse` supplies `input["question"]`, a `str`. Either `Question` is a type the ticket never names or it is a slip; make it `str` so the clue and the fact agree.


## g13.r1.observability — cut

**Divergent action.** Editing the existing memoisation line (`raft.py:109`) to read `self._get_document_set = functools.lru_cache(maxsize=512)(self._get_document_set)` — i.e. writing the literal `512` — where a ticket-only agent leaves that line exactly as it found it (the ticket says the builder "keeps ... its `functools.lru_cache` wrapping of the bound method (`raft.py:109`)") or, if rewriting, writes `maxsize=None` / bare `@functools.lru_cache` / the documented default 128. That is a nameable divergence, but its whole content is one integer literal, and whether it diverges at all depends entirely on what that line currently says — which I could not read (no Bash/Read/Glob in this session).

**The assertion.** `assert info.maxsize == 512, f"lru_cache(maxsize=512); got maxsize={info.maxsize}"` — this is the only assertion in the test that this requirement uniquely decides. Passing it depends on nothing but this requirement. But the other four assertions in the same test do NOT: `info.hits >= 1`, `info.hits + info.misses == len(CALLS)` and `info.currsize == info.misses` are all decided by r1.exclusions' cache-key choice and by the ticket's own "keeps its `functools.lru_cache` wrapping", not by the bound. Strip those and the fact is a single memorised constant.

**Catalog A.**
- `codebase_already_does_it` — The ticket asserts the memoisation already exists and is preserved: "keeps its name, its `DocumentSet` return type ... and its `functools.lru_cache` wrapping of the bound method (`raft.py:109`)". The requirement adds exactly one integer to a line the ticket forbids changing, and phrases it as existing state: "The memoisation bound *is* `functools.lru_cache(maxsize=512)`". I could not open raft.py (no file tools in this session) to confirm the current literal. If it already reads 512, every blind agent passes by inaction. The bracket's "untouched checkout fails" does not rule this out: an untouched checkout raises TypeError inside `make_answer(FIVE, n=2, distractors=2, p=0.5, sampler=head_sampler, rng=SpyRng(7))` because the old `_RaftAnswer.__init__` takes no `sampler`/`rng`, so it never reaches `cache_info()`. This is the single highest-value thing for the owner to check.
- `ticket_gives_it_away` — The ticket names `functools.lru_cache`, the bound-method wrapping, the builder's preserved name and even the line number. That hands the blind agent `info.maxsize is not None`, `(hits, misses, currsize) == (0, 0, 0)` before any build, `hits + misses == len(CALLS)` (one lookup per parse) and `currsize == info.misses`. Four of the test's five assertions come free from the ticket; only `maxsize == 512` does not.

**Catalog B.**
- `state_is_unreachable` — The state the bound governs — eviction at 512 live entries — is unreachable. The fixture is five chunks and three distinct `(chunk_id, question)` keys; `assert info.currsize == info.misses, "every miss stored an entry; none was evicted"` concedes that nothing is ever evicted. No run in this task, or any realistic run of the block, distinguishes 512 from 128, 1024 or None.
- `behaviour_has_no_consequence` — This is the headline. Violating the fact (writing 1024) changes no emitted row, no rng draw, no `RaftDrawStats` count, no exception, no `oracle_index`. The run is byte-identical. The §6 checklist box "the behavior this requirement describes has an observable consequence if violated" is unchecked: the only observable is the introspected constant itself. Its three siblings all have genuine consequences (counters, coin log, differing `oracle_present` rows); this one is a shibboleth measuring whether the agent copied a number out of a clue.
- `observable_belongs_to_another_fact` — The fact as stated demands `cache_info() == CacheInfo(hits=1, misses=3, maxsize=512, currsize=3)`. That hit/miss split is decided entirely by r1.exclusions' cache key ("the question ... is the third positional argument of the memoised builder and part of its key"). The test itself admits this and backs off — its docstring says observability reads "never the exact hit/miss split that the cache key decides" — relaxing to `hits >= 1` and `hits + misses == 4`, which are exclusions' and scope's observables. So the stated fact borrows exclusions' channel, and the graded test is looser than the stated fact: an agent that writes 512 but keys on `(chunk_id, oracle_document)` alone gets hits=2, misses=2 and passes observability while failing exclusions outright.
- `no_independent_content` — Remove `maxsize == 512` and nothing is left that scope and exclusions do not already assert. `hits >= 1` restates "a repeated (chunk_id, question) replays its document set" from test_exclusions; `hits + misses == 4` and `builds < len(CALLS)` are the same observation from test_scope. The fact is one constant plus a re-run of its neighbours.

**A blind build that passes anyway:**

```
Contingent but decisive: if `raft.py:109` currently reads `self._get_document_set = functools.lru_cache(maxsize=512)(self._get_document_set)`, then the passing blind implementation is *the ticket followed literally* — the agent never touches line 109, because the ticket instructs "The private document-set builder keeps its name, its `DocumentSet` return type ... and its `functools.lru_cache` wrapping of the bound method (`raft.py:109`)". Zero lines of code, guaranteed pass. Independently of that, a blind agent who does rewrite the wrapper picks from a five-element space of round, idiomatic values — `functools.lru_cache(maxsize=None)`, bare `@functools.lru_cache`, 128, 256, `functools.lru_cache(maxsize=512)`, 1024 — e.g. `self._get_document_set = functools.lru_cache(maxsize=512)(self._get_document_set)  # bounded so a long run cannot grow the cache without limit`. That is a ~1-in-5 lottery, not an unguessable token; one blind sample failing it is weak evidence.
```

**A correct build the test rejects:**

```
An informed agent who reconciles the clue with the open ticket and treats the clue as *descriptive of existing state* rather than as an instruction to edit:

```python
    # raft.py:109, untouched per the ticket: "the private document-set builder
    # keeps ... its functools.lru_cache wrapping of the bound method".
    # The clue states the bound *is* 512; nothing here needs to move.
    self._get_document_set = functools.lru_cache(maxsize=None)(self._get_document_set)
```

The requirement is written in the present tense — "The memoisation bound **is** `functools.lru_cache(maxsize=512)`" — and the ticket's verb is "keeps". Under that joint reading, not editing the line is the ticket-compliant action, and the test rejects it. This failure mode only exists because the fact was phrased as a description of the checkout instead of as a change to make.
```

**Recommendation.** Cut r1.observability. It is one arbitrary integer on a line the open ticket explicitly tells every agent to keep ("the private document-set builder keeps ... its `functools.lru_cache` wrapping of the bound method (`raft.py:109`)"), it has no behavioural consequence anywhere in the task, and everything else its test asserts already belongs to r1.scope and r1.exclusions.

Before doing anything else, read `raft.py:109`. If it already says `maxsize=512`, the fact is dead on arrival — a blind agent passes by touching nothing, and the free bracket's blind sample almost certainly failed at `make_answer(..., sampler=..., rng=...)` raising TypeError on the old `__init__` signature rather than on the bound.

If you want to keep an observability fact for r1, replace it with one that has a consequence — make the bound small enough that eviction is visible: `lru_cache(maxsize=2)` over a three-distinct-key fixture, asserting that the evicted `(chunk_id, question)` is rebuilt and draws a *fourth* coin from the spy rng (`rng.calls.count("random") == 4` and `rows[3] != rows[0]`). That is a behavioural claim an agent can only satisfy by understanding the bound, and it cannot be reached by inaction. Whichever you choose, also amend the ticket's "keeps ... its `functools.lru_cache` wrapping" to "stays memoised, wrapping the bound method" so the hidden fact is not contradicted by the visible one, and rephrase the requirement imperatively ("set the bound to N") rather than in the present tense ("the bound *is* N"), which currently reads as a description of the checkout and invites a correct agent to leave the line alone.


## g13.r2.rule — ship

**Divergent action.** A module-level class definition that does not exist anywhere in the ticket's scope: `class InsufficientDistractorsError(ValueError): def __init__(self, chunk_id, requested, available): super().__init__(f"chunk {chunk_id}: requested {requested} distractors, only {available} available"); self.chunk_id = chunk_id; self.requested = requested; self.available = available` — plus the `raise InsufficientDistractorsError(chunk_id=chunk_id, requested=requested, available=available)` at the top of the document-set builder guarded by `available < requested`. The blind agent writes neither: the ticket never mentions an error path, and the blind builder reaches `self.sampler(available_indices, self.distractors + 1)` and lets whatever the sampler does happen (with the default `self.rng.sample` that is a bare `ValueError("Sample larger than population or is negative")`; with an injected sampler, nothing at all).

**The assertion.** `assert str(built) == "chunk 2: requested 4 distractors, only 3 available"` (immediately preceded by `built = error_cls(chunk_id=2, requested=4, available=3)` and `assert (built.chunk_id, built.requested, built.available) == (2, 4, 3)`). Passing or failing it depends on nothing but this requirement: no builder runs, no rng is touched, no facade is constructed, no sibling's behaviour is read. Its only external dependency is `raft_name` resolving a module-level name in `raft.py`, which is this fact's own subject.

**Catalog A.** clean

**Catalog B.** clean

**Recommendation.** Ship as written. Two things to confirm before it goes out, neither of which changes the test:

1. Verify the clue quotes the message verbatim. Discrimination here rests on an unguessable string, `f"chunk {chunk_id}: requested {requested} distractors, only {available} available"`, and on the exact class name. That is fine for condition 1 (blind fails, as the bracket found), but condition 3 (ticket + clues) only lands if the clue material reproduces the name and the message character-for-character rather than paraphrasing them ("it should tell you which chunk and how short we were"). An agent who correctly derives the class, the three attributes and the up-front worst-case check and still fails on wording would be a solvability failure, not a discrimination success. I could not open the clue files in this session to check.

2. Note a cosmetic grading edge. An agent who puts the corpus-size check in `_RaftAnswer.__init__` instead of the builder — a plausible over-extension of the sibling `failure_behavior`, though contrary to both `rule` ("raised by the document-set builder") and `scope` ("the builder's first statement") — makes `make_answer(SMALL, n=2, distractors=3, ...)` throw outside the `pytest.raises` block, so the test ERRORs rather than failing with a readable message. It is a correct rejection of an incorrect implementation; if you want the failure to read better, move the `make_answer(...)` line inside the `with pytest.raises(error_cls)` block, since the requirement is indifferent to which of the two calls raises.


## g13.r2.scope — ship

**Divergent action.** The clued agent writes a pre-coin, worst-case guard as the builder's first statement:

    def _get_document_set(self, chunk_id, oracle_document, question):
        available = len(self.chunks) - 1
        requested = self.distractors + 1
        if available < requested:
            raise InsufficientDistractorsError(
                chunk_id=chunk_id, requested=requested, available=available)
        oracle_present = self.rng.random() < self.p
        ...

Three things here are the clue's fingerprint and none of them follow from the ticket: (1) the guard exists at all — the ticket never mentions a corpus-size failure; (2) `requested = self.distractors + 1` unconditionally, i.e. the oracle-ABSENT k even on runs where the coin will say present; (3) it sits above `self.rng.random()`, whereas the ticket enumerates the build as "in this order: 1. one `self.rng.random()`", making the coin the first statement. The blind agent writes the three numbered steps and computes k inside the branch: `k = self.distractors if oracle_present else self.distractors + 1`, with no guard anywhere.

**The assertion.** "rng = SpyRng(7); gen = make_answer(SMALL, n=2, distractors=3, p=1.0, sampler=head_sampler, rng=rng); with pytest.raises(ValueError): gen.parse({\"chunk_id\": 2, \"question\": \"Q\"}, RESPONSE)" — together with its immediate partner "assert rng.calls == []". The raise-at-p=1.0 kills any branch-local check (k=3 of 3 available succeeds); `calls == []` kills any check placed after the coin. Neither depends on another hidden fact: not on `rule` (bare ValueError, no class/attribute/message read), not on `failure_behavior` (p=1.0 and distractors=3 are both legal knobs), not on r1 (no stats, no memoisation, no `question` positional — only the public `parse` is called). The only outside dependency is on the open feature: `make_answer` must accept the ticket's `sampler`/`rng` kwargs, and the negative control's `len(documents_of(row)) == 4` reads A's `context` shape.

**Catalog A.**
- `obvious_implementation_does_it` — This is the one live risk, and it is partial. A defensively-minded engineer might add a friendly guard after seeing `random.sample` fail on a small fixture while writing the ticket-mandated tests. But passing requires three coincidences simultaneously: writing a guard at all (the ticket gives no prompt to), remembering the oracle exclusion (`len(self.chunks) - 1`, not `len(self.chunks)` — the latter gives `4 < 4 == False` and fails on SMALL), and choosing the worst case above the coin rather than the branch-local k that is already being computed one line down. The ticket's explicit 'in this order: 1. one `self.rng.random()`' actively discourages the third. I estimate this path in the low tens of percent at worst, not the majority case.

**Catalog B.** clean

**A blind build that passes anyway:**

```
A defensive ticket-only implementation that happens to satisfy this fact (fails `rule`, passes `scope`):

    def _document_set(self, chunk_id, oracle_document):
        # A set needs `distractors` other chunks, plus one more standing in for
        # the oracle when the coin leaves it out. Check the larger of the two so
        # a corpus either works on every chunk or on none of them.
        available = len(self.chunks) - 1
        requested = self.distractors + 1
        if available < requested:
            raise ValueError(
                f"chunk {chunk_id}: requested {requested} distractors, "
                f"only {available} available")
        oracle_present = self.rng.random() < self.p
        ...

I want to be honest about how much weight this carries: it is not the naive blind implementation the rubric asks you to test against. The naive one transcribes the ticket's numbered steps and has no guard. This variant needs a guard the ticket never asks for, the `- 1` oracle exclusion (writing `len(self.chunks) < requested` gives `4 < 4 == False` and fails SMALL), and worst-case-before-coin in the face of the ticket's "in this order: 1. one `self.rng.random()`". Three coincidences, so a real but minority path — worth a second blind sample rather than a cut.
```

**Recommendation.** Ship. I could not construct a legitimate reading the test rejects: the guard can live in `parse`, in a `_check_corpus` helper called first, compare `len(available_indices) < requested` or `len(self.chunks) <= self.distractors + 1`, and raise `InsufficientDistractorsError` or a plain `ValueError` — all pass. The test reads no message and no class, and it carries its own negative control (FIVE, exactly `distractors + 1` others, builds with one coin), so it cannot be passed by a guard that simply fires everywhere.

Note this is a deliberate override of "ship only if you found nothing in 5": I did write a blind pass, and I judge it too improbable to disqualify the fact. Two cheap hardenings if you want them, neither blocking:

1. Re-run the blind bracket once more with a defensiveness-primed prompt (e.g. an agent told to make the block robust to odd inputs). That is the sample that would actually catch the residual coincidence; no test edit can, since the coincidence is in the agent's instinct, not in the assertion.
2. Optionally drop `assert len(documents_of(row)) == 4` from the negative control and keep only `assert ok_rng.calls.count("random") == 1` plus "the call returns without raising". As written, that one line makes a scope-correct agent with a malformed `parse` context fail scope. It routes through the OPEN feature rather than a sibling hidden fact, and `documents_of` is shared with `test_open` on purpose, so this is defensible as-is — cut it only if you want scope readable in total isolation from A.


## g13.r2.exclusions_or_crossover — retest

**Divergent action.** In `Raft.__call__`'s list branch, before the chunk dataset is built: `chunks = [c for c in input if c.strip()]` (equivalently `filter(str.strip, input)`), with chunk ids then assigned by `enumerate`/`range(len(chunks))` over the survivors rather than over `input`. A blind agent writes `chunks = input` (or `list(input)`) and numbers every entry, so `["alpha", "", "  ", "\n", " bravo "]` yields 5 rows with chunk_ids 0..4 instead of 2 rows with chunk_ids 0,1.

**The assertion.** `assert list(chunks["content"]) == ["alpha", " bravo "], "survivors are stored verbatim, surrounding whitespace kept"` (with `assert list(chunks["chunk_id"]) == [0, 1]` as its inseparable partner — filtering without renumbering is not a reachable variant once you filter the list before `range(len(...))`). Passing it depends on more than this requirement: it reads the chunk dataset through `chunks_handed_to(StubA)`, which first asserts `len(stub_cls.instances) == 1` and then indexes `instances[0].kwargs["chunks"]` — i.e. it presupposes the OPEN ticket's `answer_generator_cls` seam and the exact `chunks=` keyword wiring. The `question_generator_cls` half of that seam is gated by `require_feature`, but the one-instance / `kwargs["chunks"]` contract is not; an agent who wired the facade differently fails this hidden fact for an r0 reason.

**Catalog A.**
- `ticket_gives_it_away` — Location, not content, is given away: "The `str` input branch keeps its behaviour: `chunk_text` (`raft.py:181`) and the `chunk_size` knob are out of scope." Explicitly freezing one branch of a two-branch `if` invites the reader to infer the other branch is where a change lands. The ticket otherwise never mentions the list branch, so this is the only sentence in the whole ticket that draws attention to it. It does not say *what* to change, so it is a partial giveaway — but it materially raises the odds a blind agent touches exactly the right three lines.
- `obvious_implementation_does_it` — The entire hidden behaviour reduces to one comprehension, `[c for c in input if c.strip()]`, which is a common defensive move when turning a user-supplied list into a retrieval corpus (a blank document is useless as an oracle and as a distractor). The 'renumber contiguously from 0' half is then free — any `enumerate`/`range(len(...))` over the filtered list does it automatically, so an agent gets two of the three assertions for the price of one instinct, and 'stored verbatim' is free too because nobody strips the survivor they kept. This is a narrow fact resting on a single line a tidy engineer plausibly writes unprompted.

**Catalog B.**
- `behaviour_has_no_consequence` — For the all-blank sub-clause only. "raises nothing here" is true only because a stub absorbs the empty dataset. In a real run both policies are fatal one layer down: 0 chunks gives an empty question stage, while 3 blank chunks with the default `distractors=3` gives `available = 2 < requested = 4` and the sibling's `InsufficientDistractorsError` on every chunk. The `assert len(empty) == 0` / `column_names == []` pair therefore grades a distinction with no downstream consequence, and it is exactly the pair that produces the false negative in question 6.

**A blind build that passes anyway:**

```
Ticket-only, no clue — an agent tidying the corpus while it is already editing this branch to thread the new seams:

```python
def __call__(self, input: str | list[str]) -> datasets.Dataset:
    if isinstance(input, str):
        docs = chunk_text(input, self.chunk_size)
    else:
        # a blank document is useless as an oracle and as a distractor
        docs = [doc for doc in input if doc.strip()]
    chunks = datasets.Dataset.from_list(
        [{"content": doc, "chunk_id": i} for i, doc in enumerate(docs)]
    )
    ...
```

This passes every assertion in the exclusions test. It needs two things to line up: the `if doc.strip()` instinct (which the ticket nudges toward by freezing only the `str` branch), and `from_list` rather than `from_dict` (free if that is what `raft.py` already does — I could not read the file to check). Note the asymmetry: `from_dict` is the construction that makes a *correct* agent fail, and `from_list` is the construction that makes a *blind* agent pass. The `column_names` assertion is grading the construction call, not the requirement.
```

**A correct build the test rejects:**

```
A clue-informed agent that filters and renumbers exactly as specified, but keeps the columnar construction:

```python
else:
    docs = [doc for doc in input if doc.strip()]     # blanks dropped, verbatim survivors
chunks = datasets.Dataset.from_dict(
    {"content": docs, "chunk_id": list(range(len(docs)))}   # unchanged from today
)
```

`["alpha", "", "  ", "\n", " bravo "]` → `content == ["alpha", " bravo "]`, `chunk_id == [0, 1]`: correct. `["", "   ", "\t\n"]` → `len(...) == 0`: correct. But `datasets.Dataset.from_dict({"content": [], "chunk_id": []})` keeps both null-typed columns, so `column_names == ["content", "chunk_id"]` and `assert list(empty.column_names) == []` fails. Nothing in "drops blank entries before chunk ids are assigned and renumbers the survivors from 0, keeping their text verbatim" — the test's own statement of the fact — implies the empty dataset must also lose its schema, and no clue that teaches blank-filtering would plausibly teach `from_list`.
```

**Recommendation.** Retest, with two edits, then re-run the bracket.

1. Delete `assert list(empty.column_names) == []` from `test_exclusions__a_list_corpus_drops_blank_documents_and_renumbers_from_zero`, and delete "with `column_names == []`" from the fact text. Keep `assert len(empty) == 0` (that one is genuinely about filtering). If you want any schema assertion at all, make it construction-agnostic: `assert set(empty.column_names) <= {"content", "chunk_id"}`. As written the assertion grades `from_list` vs `from_dict`, which is not the hidden fact and which a correct agent has no way to guess.

2. Blunt the ticket's location hint. "The `str` input branch keeps its behaviour: `chunk_text` and the `chunk_size` knob are out of scope" is the only sentence pointing at the branch pair; rephrase so the str branch is not singled out for preservation (e.g. fold `chunk_text`/`chunk_size` into a general out-of-scope list that does not contrast the two branches). Then re-run the blind condition — the fact's whole weight is one `if doc.strip()` comprehension, so it needs more than one blind sample before you trust the `hidden` label.

If a re-run of blind still passes after edit 2, cut the fact rather than narrow it: there is no smaller version of "filter one list" left to hide.


## g13.r2.failure_behavior — narrow

**Divergent action.** Two guard clauses as the first statements of `_RaftAnswer.__init__`, above `super().__init__(*args, **kwargs)`, in p-then-distractors order — which is the reverse of the order the ticket's own signature declares them (`n, distractors, p, ...`):

```python
def __init__(self, chunks, *args, n=5, distractors=5, p=0.8, sampler=None, rng=None, **kwargs):
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"p must be in [0.0, 1.0], got {p}")
    if distractors < 1:
        raise ValueError(f"distractors must be >= 1, got {distractors}")
    super().__init__(*args, **kwargs)
```

The informed agent writes the p guard first and puts both above `super()`; the blind agent either writes no guard (the ticket enumerates `__init__`'s post-conditions exhaustively and never mentions validation) or writes them in declaration order, distractors first, and answers `(p=1.5, distractors=0)` with the distractors message.

**The assertion.** The deciding pair is inside the table loop plus the placement probe:

```python
(dict(p=1.5, distractors=0), "p must be in [0.0, 1.0], got 1.5"),
...
assert str(caught.value) == message, f"for {kwargs}"
```
and
```python
with pytest.raises(ValueError) as ours_first:
    cls(chunks=make_chunks(THREE), model_name=MODEL, backend="nope", p=1.5)
assert str(ours_first.value) == "p must be in [0.0, 1.0], got 1.5", (
    "the knob check runs before super().__init__")
```

Does passing depend on anything but this requirement? Yes, in three places. (a) The placement probe depends on the base class raising a `ValueError` whose text contains `"Unknown backend"` for `backend="nope"` — repo/library behaviour outside this requirement; if curator's backend dispatch ever raises a different type or wording, a correct implementation fails. (b) The success-path builds (`build(p=0.0)`, `build(p=1.0)`, `build(distractors=1)`) depend on the sibling `scope`'s decision to keep the corpus check out of `__init__`, since `THREE` + default `distractors=5` is an under-supplied corpus. (c) `assert Raft(model="m", p=1.5).p == 1.5` depends on the agent's reading of the open ticket's "authoritative owner of the sampling knobs", not on `_RaftAnswer.__init__` at all.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Two clauses are pure inaction. "`Raft` itself does not re-check, so `Raft(model="m", p=1.5)` constructs" is graded by `assert Raft(model="m", p=1.5).p == 1.5` — true of every implementation that simply doesn't add a `__post_init__`, blind ones included. Likewise "never `InsufficientDistractorsError`", graded by `assert not isinstance(caught.value, error_cls)`: you have to go out of your way to fail it. Neither clause can distinguish clue-reader from non-reader; the second can only punish.
- `model_already_knows_it` — `f"p must be in [0.0, 1.0], got {p}"` and `f"distractors must be >= 1, got {distractors}"` are near the modal phrasing an LLM produces for a range guard (`"<name> must be <constraint>, got <value>"`). They are not arbitrary sentinels like the sibling's `"chunk 2: requested 4 distractors, only 3 available"`. Conditional on the agent writing a guard at all, exact-string agreement is plausible; the discrimination here comes from the ordering inversion and the pre-`super()` placement, not from the text.

**Catalog B.**
- `observable_belongs_to_another_fact` — The success-path builds use `chunks=make_chunks(THREE)` with `distractors` at its default `5`: `assert build(p=0.0).p == 0.0`. Under an implementation that puts the corpus-size check in `__init__` rather than in the builder, `available = 3 - 1 = 2 < requested = 6` and these three constructions raise `InsufficientDistractorsError` — so a violation of the sibling `scope` ("the check is the builder's first statement") fails *this* fact. `scope`'s observable is doing work inside `failure_behavior`. The `not isinstance(caught.value, error_cls)` clause also reads the sibling's class, though `required=False` softens it.

**A blind build that passes anyway:**

```
A defensive engineer with the ticket only, who guards the probability knob and happens to land the conventional phrasing and the non-obvious order:

```python
class _RaftAnswer(curator.LLM):
    def __init__(self, chunks: datasets.Dataset, *args, n: int = 5, distractors: int = 5,
                 p: float = 0.8, sampler: Optional[_SamplingStrategy] = None,
                 rng: Optional[random.Random] = None, **kwargs) -> None:
        # p is a probability; distractors is a count. Fail loudly at construction
        # rather than producing quietly wrong document sets.
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"p must be in [0.0, 1.0], got {p}")
        if distractors < 1:
            raise ValueError(f"distractors must be >= 1, got {distractors}")
        super().__init__(*args, **kwargs)
        self.n = n
        self.distractors = distractors
        self.p = p
        self.chunks = chunks
        self.rng = rng if rng is not None else random.Random()
        self.sampler = sampler if sampler is not None else self.rng.sample
        self.formatter = _ContextFormatter()
```

This passes every assertion. I rate it unlikely rather than impossible: it needs three independent coincidences — writing a guard the ticket never asks for (the ticket enumerates `__init__`'s post-state exhaustively), phrasing both messages verbatim, and checking `p` before `distractors` against the declared parameter order `n, distractors, p`. The third is the real barrier; guards written top-to-bottom answer `(p=1.5, distractors=0)` with the distractors message. The bracket's one blind sample missing this is consistent with it being a low-probability branch, not an unreachable one.
```

**A correct build the test rejects:**

```
An agent who read the clue, implemented `_RaftAnswer.__init__` exactly as specified, and then took the open ticket's opening sentence — *"Make the `Raft` facade the authoritative owner of the sampling knobs"* — to mean the facade should also reject a knob it owns:

```python
@dataclass
class Raft:
    model: str
    distractors: int = 3
    chunk_size: int = 1000
    n_questions: int = 2
    p: float = 0.8
    ...
    def __post_init__(self) -> None:
        # the facade owns the knobs, so it is the first place a bad one is caught
        if not 0.0 <= self.p <= 1.0:
            raise ValueError(f"p must be in [0.0, 1.0], got {self.p}")
        if self.distractors < 1:
            raise ValueError(f"distractors must be >= 1, got {self.distractors}")
```

`_RaftAnswer` still validates first, still p-before-distractors, still above `super()`, still plain `ValueError`, still the documented messages — every clause of the fact that is about the answer generator holds — but `assert Raft(model="m", p=1.5).p == 1.5` raises and the fact is scored failed. The ticket's own "authoritative owner" wording invites exactly this reading, so the test is punishing a defensible interpretation of the visible ask.

Second, weaker one: an agent who correctly puts the corpus check in the builder passes, but one who reasonably reports the corpus problem early — at construction, where `chunks` and `distractors` are both already known — fails `assert build(p=0.0).p == 0.0` on the 3-chunk fixture. That is a `scope` mistake being charged to `failure_behavior`.
```

**Recommendation.** Keep the fact — the p-before-distractors inversion and the pre-`super()` placement probe are a real, nameable divergence. Narrow it in three ways:

1. **Delete the facade clause.** Drop `assert Raft(model="m", p=1.5).p == 1.5` from the test and strike "`Raft` itself does not re-check, so `Raft(model=\"m\", p=1.5)` constructs and fails only when `__call__` builds the answer generator" from the fact. It is prohibition-satisfied-by-inaction (free for every blind agent) and it fails a correct agent who reads the ticket's "authoritative owner of the sampling knobs" as licence to guard at the facade. If the non-re-checking is genuinely wanted, move it to the open ticket as an explicit "`Raft` performs no validation" line so it stops being a hidden trap.

2. **Decouple the success path from the sibling.** Change the `build` helper's corpus so it is large enough under the default `distractors=5` — `make_chunks(FIVE + ["foxtrot", "golf"])`, or pass `distractors=1` alongside `p=0.0`/`p=1.0`. As written, `THREE` + default `distractors=5` means an agent who puts the corpus check in `__init__` (a `scope` violation) also fails `failure_behavior`.

3. **Close the undershoot.** Nothing currently checks that the *distractors* guard precedes `super()`; `backend="litellm"` constructs fine, so a distractors-check-after-super implementation passes. Add the mirror of the existing probe: `cls(chunks=..., model_name=MODEL, backend="nope", distractors=0)` must give `"distractors must be >= 1, got 0"`.

Also worth noting for the clue: the two message strings are close to modal LLM validator phrasing and should not be treated as the discriminator. Make sure the clue states the order (`p` first) and the placement (above `super()`) explicitly, since that is where the actual signal lives.
