# Audit — g7 (agent-turn-ledger)

| fact | bracket | audit | why |
|---|---|---|---|
| `g7.r1.rule` | hidden | **retest** | Keep the fact — it discriminates, and I could not construct a blind implementation that passes — but fix the test, which currently measures the artifact and not |
| `g7.r1.scope` | hidden | **narrow** | Narrow the fact to the one thing it uniquely owns — status provenance — and fix the two defects.

1. Delete from r1.scope everything already owned elsewhere: "w |
| `g7.r1.failure_behavior` | hidden | **retest** | Retest, with three concrete edits. (1) Replace the byte-exact prose check with a structural one unless you can point at a clue that quotes the f-string verbatim |
| `g7.r1.observability` | hidden | **narrow** | Narrow the fact and the test to the one thing only it can see — the literal bytes — and delete the parts that re-measure siblings. Concretely:

1. Cut from the  |
| `g7.r2.rule` | hidden | **narrow** | Narrow the fact, then re-run blind with instrumentation.

1. Rewrite `r2.rule` to its unique residue only: "`COMPLETION_SENTINEL` is exactly the string `\"<<END |
| `g7.r2.scope` | hidden | **cut** | Cut r2.scope as a separately graded fact and fold its two live assertions into `test_rule`, which is where they belong: r2.rule already specifies the exact expr |
| `g7.r2.failure_behavior` | hidden | **cut** | Cut `r2.failure_behavior`. It fails four Catalog A patterns and four Catalog B patterns, and the test's own comment concedes the problem ("An untouched Agent re |
| `g7.r2.observability` | hidden | **cut** | Cut `observability` as a scored field on r2. It fires four Catalog A patterns (ticket_gives_it_away, entailed_by_the_open_feature, obvious_implementation_does_i |

## g7.r1.rule — retest

**Divergent action.** The informed agent writes, in turn_ledger.py: `TURN_LEDGER_FILENAME: str = "turn_ledger.json"`, `TURN_LEDGER_VERSION: int = 2`, a `TurnLedger.sidecar_state()` returning exactly `{"version": TURN_LEDGER_VERSION, "responses": ..., "turns": ..., "last_author": ..., "next_speaker": ..., "interleave_faults": ..., "completed": ..., "completion_reason": ...}`, and `write_sidecar(working_dir, ledger)` doing `handle.write(json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n")`; and in processor.run(), a `write_sidecar(working_dir, self.ledger)` call on the line after the seed's `append_response()` and again on the line after each response's `append_response()`. The blind agent writes no second file at all: the open ticket's `load_ledger` "loads the ledger for a working directory and never writes to disk" and derives every field from `responses_0.jsonl`, so a ticket-only agent produces a module with `RESPONSES_FILENAME` and no checkpoint whatsoever — `sym("TURN_LEDGER_FILENAME")` fails on the test's first line.

**The assertion.** `assert os.path.exists(path), "no checkpoint was written before the run failed"` — gated by the three symbol lookups above it (`assert sym("TURN_LEDGER_FILENAME") == "turn_ledger.json"`, `assert sym("TURN_LEDGER_VERSION") == 2`, `sym("read_sidecar"/"write_sidecar"/"verify_sidecar")`), which is where a blind agent actually dies. Passing depends on more than this requirement: the test cannot reach it unless the open ticket's seed-as-turn write, `next_speaker` alternation, the `while ledger.responses < max_length` loop and the append-nothing-on-failure path are all already correct, since `assert authors(tmp_path) == [SEEDER, PARTNER, SEEDER]` precedes it. Those are open-feature dependencies rather than another hidden fact's, but they mean a `rule` failure does not localise to r1.

**Catalog A.** clean

**Catalog B.**
- `contradicts_a_sibling` — `rule` guarantees the checkpoint is rewritten 'after **every** appended response', which guarantees sidecar == log — exactly the precondition sibling `failure_behavior` needs to be FALSE to reach arm (c). The desync state is therefore unreachable through the system's own operation and only exists because the test performs file surgery (`put_sidecar(tmp_path, full_state(responses=1))`, and `(done/"responses_0.jsonl").write_text("".join(lines[:3]))`). Worse, the one way the implementation itself can produce a desync is a crash in the window between `append_response()` and `write_sidecar()`, which leaves recorded_responses < log_responses and makes the next resume a hard error — i.e. the rule's own cadence manufactures the failure it then treats as fatal.
- `observable_belongs_to_another_fact` — The test docstring asserts the division 'observability is the only one that spells the file out literally', yet `test_rule` reads the same file and asserts all eight key/value pairs (`state["responses"] == 2`, `state["next_speaker"] == PARTNER`, `state["completion_reason"] == "open"`, ...). That is observability's channel with the byte count removed. `rule`'s genuinely own observable is only the symbol table plus `os.path.exists`.
- `no_independent_content` — You cannot fail `rule` without failing `observability`: any implementation producing the exact 186-byte text and the exact `read_sidecar(str(done))` dict necessarily has the filename, version 2, the eight keys and their values. What remains uniquely `rule`'s is naming — the two constant names, `sidecar_state()` being a method, `write_sidecar` returning an absolute path, `verify_sidecar` existing as a symbol. r1 is one artifact measured four times, not four measurements.
- `fake_defines_the_trigger` — The graded question is *when* the write happens ('never batched to the end'), and `Conversation(raise_on=(3,))` is what defines when 'the end' arrives — the fake authors the only condition that could separate per-append writing from a single deferred write, and it separates them so weakly that a `finally` write is indistinguishable. In `test_observability` the same fake also supplies `is_completed=stops`, deciding when the conversation ends and hence when the last write occurs.

**A correct build the test rejects:**

```
A ticket-plus-clue agent that takes the sibling's own definition literally — "`load_ledger` is `read_log` + `build_ledger` + `verify_sidecar`" — and uses that single public entry point to refresh the mid-run ledger:

```python
async def run(self, working_dir: str):
    ledger = self.load_cache(working_dir)          # read_log + build_ledger + verify_sidecar
    self.status_tracker.adopt_ledger(cached_responses=ledger.responses)
    if not ledger.entries:
        await self.append_response(self._seed_record(), working_dir)
        ledger = self.load_cache(working_dir)      # <-- desyncs against the stale file
        write_sidecar(working_dir, ledger)
    ...
    while ledger.responses < self.max_length:
        ...
        await self.append_response(response, working_dir)
        ledger = self.load_cache(working_dir)      # <-- one append stale again
        write_sidecar(working_dir, ledger)
```

This is a legitimate reading: r1 never says the mid-run rebuild must use `build_ledger` directly rather than `load_ledger`, and never fixes the order of rebuild-vs-write. It raises `TurnLedgerDesyncError` against a log it wrote itself one line earlier, so `test_rule` fails at `with pytest.raises(Boom)` with a desync instead. The same agent writing `write_sidecar(...)` *before* the rebuild passes — an ordering the requirement leaves unstated.
```

**Recommendation.** Keep the fact — it discriminates, and I could not construct a blind implementation that passes — but fix the test, which currently measures the artifact and not the cadence it names.

1. Actually measure "after every appended response, never batched to the end." Have the fake capture the checkpoint at the top of each `call_single_request` and assert the sequence, so a single deferred write cannot pass:
   `assert conversation.sidecars == [{"responses": 0, "turns": 1, "last_author": SEEDER, ...}, {"responses": 1, "turns": 2, "last_author": PARTNER, ...}, {"responses": 2, "turns": 3, "last_author": SEEDER, ...}]`
   As written, an implementation that writes the sidecar once inside `try: ... finally: write_sidecar(working_dir, self.ledger)` around the whole loop passes every assertion in `test_rule`. This needs `Conversation` in test_open.py to expose an observer hook (it already knows `working_dir`); that is the only harness change required.

2. Close the ordering hole that fails a correct agent: add to the rule "the checkpoint is written before the ledger is next re-derived, so a mid-run `load_ledger` never verifies against a stale file" — or state that the mid-run rebuild uses `build_ledger`, not `load_ledger`. Without one of these, the `load_ledger`-based implementation quoted in correct_fail is rejected for an ordering the spec does not state.

3. De-duplicate `rule` against `observability`. Drop the eight value assertions (`state["responses"] == 2` ... `state["completion_reason"] == "open"`) from `test_rule` and leave the literal file spelling to `observability`; keep `rule` on the symbol table (`TURN_LEDGER_FILENAME`, `TURN_LEDGER_VERSION`, `sidecar_state()`, `write_sidecar`'s absolute return, `verify_sidecar`) plus the new cadence sequence. That makes the two fields separately failable instead of mutually implied.

4. Optional, for `failure_behavior` rather than `rule`: note in the requirement that a desync is reachable in production only through the append/write crash window, so the sibling's arm (c) is exercised solely by test file surgery.


## g7.r1.scope — narrow

**Divergent action.** Two lines, only one of which is scope's own. (1) Scope-unique: stamping the provenance on the fresh run's first ledger and keeping it — `self.ledger = build_ledger(read_log(working_dir), seeder_name=..., partner_name=..., max_responses=self.max_length, is_completed=..., status="created")` (or `dataclasses.replace(ledger, status="created")`) executed on the ledger built right after `append_response(build_seed_record(...))` and *not* re-derived afterwards. Nothing else in r1 or r2 mentions `"created"` at all. (2) Not scope's own: `if recorded.get("responses") != ledger.responses or recorded.get("last_author") != ledger.last_author: raise TurnLedgerDesyncError(...)` instead of `if recorded != ledger.sidecar_state(): ...` — that two-key comparison is already spelled out in r1.failure_behavior arms (b)/(c), so an agent who saw only failure_behavior writes it.

**The assertion.** `assert read_field(adopted, "status") == "adopted"` — the first status assertion, and the one every blind implementation dies on (a blind `load_ledger` returns `build_ledger`'s ticket-given default `"verified"`). Yes, it depends on other requirements: it is r1.failure_behavior arm (a) — "The file is absent ... → status = 'adopted'" — asserted byte-for-byte in that fact's own test on the same fixture, and it presupposes r1.rule's existence of `turn_ledger.json`. The only assertion that depends on r1.scope alone is `assert read_field(processor.ledger, "status") == "created"`.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Most of the fact is a prohibition: "load_ledger ... writes nothing" and "no log line is ever truncated, ignored, re-ordered or rewritten to agree with the checkpoint". The test grades those by `assert sorted(os.listdir(str(tmp_path))) == listing`, `assert open(path, "rb").read() == recorded`, `assert open(before, "rb").read() == log_bytes`, `assert authors(tmp_path) == [SEEDER, PARTNER, SEEDER]`. No engineer, informed or blind, writes a loader that rewrites the log to match a JSON file; every one of those four passes by nobody doing anything.
- `model_already_knows_it` — "The log is the authority in every direction" is the standard WAL/checkpoint convention (SQLite WAL, Kafka offsets, any journal + snapshot design): the append-only log is truth, the snapshot is an advisory index rebuilt from it. Any model that is told to put a checkpoint beside a log defaults to this without being told.
- `ticket_gives_it_away` — The headline clause is verbatim in the visible ticket: `load_ledger(working_dir, *, ...)` — "loads the ledger for a working directory and never writes to disk". The ticket also supplies `LEDGER_STATUSES: tuple[str, ...] = ("created", "adopted", "verified")` and `build_ledger(..., status: str = "verified")`. The test's first assertion, `assert set(statuses) == {"created", "adopted", "verified"}`, and its writes-nothing assertion are both pure ticket text.
- `entailed_by_the_open_feature` — "None of its six lies reach the ledger" cannot fail for anyone who built the open feature plus r1.rule: `build_ledger(records, ...)` receives only records, the ticket defines turns/next_speaker/interleave_faults/completed/completion_reason as log-derived, and r1.rule's `verify_sidecar(working_dir, ledger) -> TurnLedger` takes an already-built frozen ledger, so the only field it can possibly alter is `status`. `assert read_field(ledger, "turns") == 3` and its four neighbours are unfailable.
- `obvious_implementation_does_it` — The obvious shape of `load_ledger` given r1.rule alone — `records = read_log(d); ledger = build_ledger(records, ...); return verify_sidecar(d, ledger)` — satisfies every assertion in this test except `read_field(processor.ledger, "status") == "created"`. An agent who saw r1.rule and r1.failure_behavior and never saw r1.scope passes ~14 of the 15 assertions.

**Catalog B.**
- `behaviour_has_no_consequence` — Partly. For the truncate/re-order/rewrite clause there is no differentiating outcome: a correct and an incorrect implementation both leave `responses_0.jsonl` byte-identical, because neither contains code that would rewrite it. `assert open(before, "rb").read() == log_bytes` cannot distinguish the two.
- `observable_belongs_to_another_fact` — The two status observables scope leans on are failure_behavior's. Scope asserts `read_field(adopted, "status") == "adopted"` for a log with no checkpoint; failure_behavior's test asserts the same thing on the same fixture — `# (a) absent...` / `assert read_field(load(tmp_path), "status") == "adopted"`. Likewise `"verified"` for an agreeing file is arm (b). A broken arm (a) fails both facts; that double-counts failure_behavior.
- `no_independent_content` — Decompose the fact: "writes nothing" = ticket text; "'adopted' or 'verified' after a load" = failure_behavior arms (a)/(b); "only two of the eight recorded keys are compared" = failure_behavior's "both 'responses' and 'last_author' equal the log-derived values"; "the log is the authority" = entailed by build_ledger's signature. The only residue is "'created' for a ledger built for a fresh run's first write" — one clause, one assertion.
- `unbounded_in_time` — "The log is the authority in every direction: no log line is ever truncated, ignored, re-ordered or rewritten" — universal quantification over all directions and all time, checked at exactly one finite instant on a 3-line log.

**A correct build the test rejects:**

```
```python
# processor.run(), a reading that takes "the log is the authority in every
# direction" and "load_ledger is read_log + build_ledger + verify_sidecar"
# literally: after every write to the log, the ledger is re-derived from the log.
async def run(self, working_dir: str):
    ledger = self.load_cache(working_dir)
    self.status_tracker.adopt_ledger(cached_responses=ledger.responses)
    if not ledger.entries:
        seed = build_seed_record(
            seeder_name=self.seeder.name, seed_message=self.seed_message,
            model_name=self.seeder.model_name, now=self.now_fn(),
        )
        await self.append_response(seed, working_dir)
        write_sidecar(working_dir, build_ledger(  # the fresh run's first write
            read_log(working_dir), seeder_name=..., partner_name=...,
            max_responses=self.max_length, is_completed=..., status="created",
        ))
        ledger = self.load_cache(working_dir)   # the log is the authority
        self.ledger = ledger                    # -> status == "verified"
    ...
```
The fact says only that `"created"` is the status of "a ledger built for a fresh run's first write" — which this does — and that `"adopted"` or `"verified"` follow "after a load", which is exactly what the reload produces. Nothing in r1.scope, r1.rule or the ticket says the `"created"` stamp must survive onto `self.ledger`, or that a status is assigned once and never re-derived; the ticket only says "the processor keeps the last ledger it built on `self.ledger`", and under this reading the last one built is the reloaded, verified one. The test rejects it at `assert read_field(processor.ledger, "status") == "created"`. (The same implementation also fails r1.observability's `assert read_field(second.ledger, "status") == "adopted"`, since after the resumed run's append-and-rewrite the reload verifies — so the overshoot is systemic, not a one-line fluke.)
```

**Recommendation.** Narrow the fact to the one thing it uniquely owns — status provenance — and fix the two defects.

1. Delete from r1.scope everything already owned elsewhere: "writes nothing" (verbatim in the visible ticket), "only two of the eight recorded keys are compared on load" (that is r1.failure_behavior's arms (b)/(c)), and "no log line is ever truncated, ignored, re-ordered or rewritten" (unfalsifiable by inaction; entailed by `build_ledger(records, ...)` + `verify_sidecar(working_dir, ledger) -> TurnLedger`).

2. Restate it as: "A ledger carries where it came from, stamped once and never re-derived: `\"created\"` on the ledger the processor builds for a fresh run's first sidecar write, `\"adopted\"` or `\"verified\"` on one produced by a load; `self.ledger` keeps that stamp for the life of the run even though the sidecar is rewritten after every append." The added clause "stamped once and never re-derived" is what closes the overshoot in section 6 — without it, a reload-after-every-append implementation is a legitimate reading that both this test and r1.observability reject.

3. In the test, remove `assert read_field(adopted, "status") == "adopted"` for the no-checkpoint case — it is byte-identical to r1.failure_behavior's arm-(a) assertion on the same fixture, and it is what a blind agent dies on, which means scope currently borrows its discrimination from r1.rule/failure_behavior. Replace the decisive assertions with the two that only scope determines: (a) `processor.ledger.status == "created"` on the fresh run, and (b) that the stamp survives an append — run two turns and assert `processor.ledger.status == "created"` still, and on a resume-with-agreeing-checkpoint assert it stays `"verified"` after a further appended response rather than flipping.

4. Keep the six-lie checkpoint case (`full_state(turns=99, next_speaker="nobody", ...)` → still `"verified"`), but move it to r1.failure_behavior, whose arm (b)/(c) text is what it actually grades; that test today only ever writes self-consistent or one-key-off states, so it cannot catch a `recorded != ledger.sidecar_state()` full-dict comparer.

5. Unrelated but blocking: verify that `test_open.py` — which the grading test imports `SIDECAR` from — is not visible to the agent. If it is, `turn_ledger.json` is named in open material and all of r1 is a coincidence fact, not just this one. I could not check; file tools are disabled in this session.


## g7.r1.failure_behavior — retest

**Divergent action.** In `verify_sidecar`, the third arm — raising instead of self-healing: `if recorded.get("version") != TURN_LEDGER_VERSION: return dataclasses.replace(ledger, status="adopted")` followed by `if recorded["responses"] != ledger.responses or recorded["last_author"] != ledger.last_author: raise TurnLedgerDesyncError(path, ledger.responses, recorded["responses"], ledger.last_author, recorded["last_author"])`, with that call reached from `load_ledger` (hence from `run()`) before the first `call_single_request`. An agent who never saw the clue writes no sidecar at all; an agent who saw the clue but read only its "the log is the authority in every direction" half writes `return dataclasses.replace(ledger, status="adopted")` on mismatch and rewrites the file from the log — a stale checkpoint is silently repaired and the run continues. The `or` on `last_author` (not just `responses`) and the abort-before-append placement are the concrete divergences.

**The assertion.** `assert str(error) == (f"{error.path} records 1 response(s) last authored by {SEEDER!r}, " f"the log holds 2 last authored by {SEEDER!r}")` — the only assertion in this test that no sibling test also makes (with the near-unique `put_sidecar(tmp_path, full_state(last_author=PARTNER))` block that proves the comparison is an OR over both keys). Passing it depends on more than this requirement: the whole open-ticket module must import and work (`load_ledger`, `read_log`, `build_ledger`, `TurnLedger.status`), the shared `write_log`/`read_field`/`SIDECAR` harness must agree with the agent's filename, and — critically — it grades reproduction of an arbitrary English sentence, including the `"response(s)"` pluralization and the `!r` quoting, which is content that lives in the clue corpus rather than in the agent's engineering judgment.

**Catalog A.**
- `model_already_knows_it` — Scoped to arm (a)'s version branch: "its `"version"` is not `TURN_LEDGER_VERSION` -> `status = "adopted"`, no error raised" is the standard schema-migration convention (unknown version => treat as absent, rewrite). Any competent agent told there is a `TURN_LEDGER_VERSION: int = 2` (given in the sibling `rule`, same clue bundle) writes that branch from priors. `put_sidecar(tmp_path, {"version": 1, ...})` -> "adopted" therefore discriminates almost nothing beyond `rule`.
- `ticket_gives_it_away` — The open ticket already ships `LEDGER_STATUSES: tuple[str, ...] = ("created", "adopted", "verified")`, `build_ledger(..., status: str = "verified")`, and `load_ledger(...) -- loads the ledger for a working directory and never writes to disk`. Three status words that only make sense against something on disk, plus a gratuitous promise not to write to disk, telegraph that loading verifies against a persisted record. It does not give away the filename, version 2, the exception, or the message — so it is a discovery hint, not a pass — but it is why `test_scope`'s "created"/"adopted"/"verified" checks carry little weight.
- `obvious_implementation_does_it` — Scoped to arm (a)'s absent/unreadable branches, and only once the sibling `rule` is known: the obvious `read_sidecar(working_dir) -> t.Optional[dict]` is `try: return json.load(open(path)) except (OSError, json.JSONDecodeError): return None`, and the obvious caller does `if recorded is None: return replace(ledger, status="adopted")`. That makes `write handle.write("{not json at all")` -> "adopted" free. Two of arm (a)'s three triggers cost the agent no extra thought; only arm (c) is a real decision.

**Catalog B.**
- `observable_belongs_to_another_fact` — Two ways. (i) Arm (a) asserts "the file is rewritten from the log on the next append" — this test never checks that; its only observable is r1.rule's `test_rule__a_versioned_checkpoint_rewritten_after_every_appended_response`. (ii) The five DesyncError attributes are re-asserted verbatim by observability: `caught.value.log_responses == 2`, `.recorded_responses == 3`, `.log_last_author == SEEDER`, `.recorded_last_author == PARTNER`, plus `stale.calls == []` and `len(log_lines(done)) == 3` — the same abort-before-append observable this fact claims as its own.
- `no_independent_content` — Cross-tabulating: absent->adopted is in `test_scope` (`adopted = load(tmp_path)`) and in observability (`sidecar.unlink()`); `{"version": 1, "responses": 2, "last_author": SEEDER}`->adopted is duplicated word-for-word as observability's last block; agreeing->verified is in `test_scope`; the five attributes and the zero-calls/3-lines abort are in observability. The only implementations that fail this test but pass its siblings are ones that (a) treat unreadable JSON as fatal, (b) compare `responses` only and not `last_author`, or (c) word the message differently. Most of this fact is one bit — "did you build the sidecar?" — reported a second time.

**A correct build the test rejects:**

```
A clue-following agent that gets every graded behaviour right and still fails, on prose alone:

```python
class TurnLedgerDesyncError(TurnLedgerError):
    def __init__(self, path, log_responses, recorded_responses, log_last_author, recorded_last_author):
        self.path = path
        self.log_responses = log_responses
        self.recorded_responses = recorded_responses
        self.log_last_author = log_last_author
        self.recorded_last_author = recorded_last_author
        super().__init__(
            f"{path}: checkpoint records {recorded_responses} responses "
            f"last authored by {recorded_last_author!r}, but the log holds "
            f"{log_responses} last authored by {log_last_author!r}"
        )
```

Right class, right base, right five attribute names, right values, raised from `verify_sidecar` on the load path before any append. It fails `assert str(error) == ...` on a colon, the missing `"(s)"`, and the word "but". A second legitimate variant that fails the same assertion builds the message lazily in `__str__` from the attributes with the counts leading (`f"log holds {log_responses} ... {path} records {recorded_responses}"`) — a natural choice given the requirement's own emphasis that "the log is the authority".
```

**Recommendation.** Retest, with three concrete edits. (1) Replace the byte-exact prose check with a structural one unless you can point at a clue that quotes the f-string verbatim — I could not check the corpus (Bash disabled in this session), so verify it; if the literal message is not in the discoverable context, this assertion is a condition-3 false negative waiting to happen. Substitute: `msg = str(error); assert error.path in msg and "1" in msg and "2" in msg and repr(SEEDER) in msg` plus `assert isinstance(error, base)`. If the clue does quote it verbatim, keep the assertion and record that in the fact so the grader is defensible. (2) Delete the clause "and the file is rewritten from the log on the next append" from arm (a) of the fact text — it is graded only by r1.rule's after-every-append test, not here. (3) De-duplicate against observability: move the `{"version": 1, ...} -> "adopted"` block and the `stale.calls == []` / `len(log_lines(done)) == 3` abort-before-append block out of `test_observability` (leave it the byte counts, the literal file text, and the five attribute values, which is what its docstring already claims), and let this test own the three arms outright — including the currently-unique `last_author`-only mismatch, which is the assertion that actually proves the comparison is an OR over both compared keys. After those edits the fact measures something no sibling measures and stops grading English.


## g7.r1.observability — narrow

**Divergent action.** Inside `run()`, immediately after `await self.append_response(seed_record, working_dir)` and before the first `call_single_request`, a call to `write_sidecar(working_dir, ledger)` whose body is `handle.write(json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n")` — i.e. an eager, byte-exact rewrite of `turn_ledger.json` at seed time. Caveat that decides this audit: the *file* is r1.rule's divergent action (the informed agent writes a sidecar at all, the blind one writes none); the increment this field adds over rule is only the spelling `sort_keys=True` plus the trailing `"\n"`, and that spelling is handed to the agent verbatim by rule's own sentence "serialized as `json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n"`". So the divergent action for `observability` alone is not separable from rule's.

**The assertion.** `assert path.read_text() == ("{\n" '  \"completed\": false,\n' '  \"completion_reason\": \"open\",\n' '  \"interleave_faults\": 0,\n' '  \"last_author\": \"client\",\n' '  \"next_speaker\": \"advisor\",\n' '  \"responses\": 0,\n' '  \"turns\": 1,\n' '  \"version\": 2\n' "}\n")` (with `assert path.stat().st_size == 186` as its redundant restatement). Yes, it depends on things other than this fact: on r1.rule's serialization formula and eight-key `sidecar_state()`, on r1.rule's "rewrite immediately after the seed line", on the open ticket's "the seed is written before the first request is built", and on the harness fixture's agent names — `"client"`/`"advisor"` are what make the total 186 rather than any other number.

**Catalog A.**
- `ticket_gives_it_away` — Partially, and precisely on this fact's last two clauses. The open ticket already contains `LEDGER_STATUSES: tuple[str, ...] = ("created", "adopted", "verified")` and `build_ledger(..., status: str = "verified")`, and says `load_ledger` 'loads the ledger for a working directory and never writes to disk'. A blind agent choosing `"adopted"` for a ledger loaded off disk is an unremarkable guess, so `read_field(load(older), "status") == "adopted"` and `read_field(second.ledger, "status") == "adopted"` carry no hidden-requirement signal of their own.

**Catalog B.**
- `observable_belongs_to_another_fact` — Two of this fact's three blocks are `failure_behavior`'s channel. Its desync block asserts `caught.value.log_responses == 2`, `.recorded_responses == 3`, `.log_last_author`, `.recorded_last_author`, `stale.calls == []`, `len(log_lines(done)) == 3` — `failure_behavior`'s test asserts the same five attributes and the same `conversation.calls == []` / `len(log_lines(tmp_path)) == 3`. Its final block, `put_sidecar(older, {"version": 1, "responses": 2, "last_author": SEEDER}); assert read_field(load(older), "status") == "adopted"`, is character-for-character `failure_behavior` arm (a). The docstring's claim that '`failure_behavior` never reads a byte count, and `observability` is the only one that spells the file out literally' is true only of the first block.
- `no_independent_content` — After removing what rule/scope/failure_behavior already assert, the residue is the literals 186 and 189 — and both are a mechanical evaluation of the formula `rule` itself states: 'serialized as `json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n"`'. `rule`'s test already asserts all eight keys and all eight mid-run values on the same `raise_on` fixture; this fact re-asserts them with a ruler. There is no implementation that satisfies `rule` and fails the 186-byte check, and none that fails `rule` and passes it.

**A correct build the test rejects:**

```
A ticket+clue-informed implementation that treats "the log is the authority" and "the processor keeps the last ledger it built" literally, rebuilding after each append:

```python
async def _append(self, working_dir, response):
    await self.append_response(response, working_dir)          # reused verbatim
    write_sidecar(working_dir, self.ledger)                    # rule: after EVERY append
    # the log is the authority in every direction -- re-derive, never patch in place
    self.ledger = load_ledger(
        working_dir,
        seeder_name=self.seeder.name,
        partner_name=self.partner.name,
        max_responses=self.max_length,
        is_completed=self.seeder.is_completed,
    )
    self.conversation_history = self.ledger.messages()
    return self.ledger
```

This satisfies rule (a rewrite after every append), scope (load_ledger writes nothing; the log outranks the file) and failure_behavior (verify_sidecar's three arms) — but the checkpoint it just wrote now agrees with the log, so the re-derived ledger carries `status == "verified"`. The test's `assert read_field(second.ledger, "status") == "adopted"` rejects it. Nothing in r1 says `status` is sticky for the lifetime of a `run()`; "adopted" is stated as what the *load* yields, and this implementation's last load is post-append.
```

**Recommendation.** Narrow the fact and the test to the one thing only it can see — the literal bytes — and delete the parts that re-measure siblings. Concretely:

1. Cut from the fact text and from `test_observability__...` the truncated-log desync block (`caught.value.log_responses == 2` … `len(log_lines(done)) == 3`): it re-asserts `failure_behavior` arm (c)'s five attributes and its "nothing asked, nothing appended" on a second fixture.
2. Cut the final block entirely — `put_sidecar(older, {"version": 1, "responses": 2, "last_author": SEEDER})` … `== "adopted"` is verbatim `failure_behavior` arm (a), same helper, same `THREE_LINES` log.
3. Replace `assert read_field(second.ledger, "status") == "adopted"` with status-free evidence of the same resume — keep `assert resumed.calls == [(PARTNER, 2)]` and `assert len(log_lines(done)) == 4` — or, if the author wants the status asserted, first fix r1's text to say whether `status` is fixed at load time or re-derived after each append. As written it rejects the re-derive reading (see correct_fail).
4. Give the fact content the siblings genuinely lack, in place of the deleted blocks: (a) assert the end-of-run file's exact 10-line text rather than only `st_size == 189` plus a `read_sidecar` dict — `rule` already covers dict equality, so the literal end-of-run spelling is new; and (b) assert the rewrite truncates rather than appends, e.g. after the 4-line run `open(sidecar).read().count("\"version\"") == 1` and `path.stat().st_size == 189` — an implementation opening with mode `"a"` is the one realistic wrong-but-plausible variant that only a byte-level check catches.

With 1–4 the fact stops double-counting `failure_behavior` and stops overshooting on `status`, but it still measures a formula `rule` spells out. If the author wants a fact that discriminates on its own, this field is the weakest of r1's four and folding it into `rule` (one byte-exact assertion inside `rule`'s test) costs almost nothing.


## g7.r2.rule — narrow

**Divergent action.** Writing the exact literal on the constant: `COMPLETION_SENTINEL: str = "<<END_OF_CONVERSATION>>"` in `turn_ledger.py` — the double-angle-bracket delimiters plus that exact uppercase phrase — instead of an invented token (`"TERMINATE"`, `"<END_OF_CONVERSATION>"`, `"[[DONE]]"`, `"<<END>>"`, `"CONVERSATION_COMPLETE"`, `"<|end_of_conversation|>"`). Nothing else in this fact diverges: the body `return isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)` is what an agent writes from the ticket alone, because the ticket names the constant and orders `is_completed` to be implemented "in terms of COMPLETION_SENTINEL".

**The assertion.** `assert sym("COMPLETION_SENTINEL") == SENTINEL` — the other three lines in `test_rule__...` (`is_completed(f"all set {SENTINEL}") is True`, `is_completed(SENTINEL) is True`, `is_completed("all set") is False`) all pass for any implementation that has the right literal, including wrong readings like `SENTINEL in response`, so they decide nothing. Dependency: it also requires the open feature's module `turn_ledger.py` to exist and import cleanly (that is where the ticket places the constant), so an agent who botched requirement A fails this line for a reason unrelated to r2. Beyond that coupling it is decided by this requirement alone.

**Catalog A.**
- `model_already_knows_it` — Two layers. (a) The matching idiom is a published convention: AutoGen's documented default is `is_termination_msg=lambda x: x.get("content","").rstrip().endswith("TERMINATE")` — the rule's `response.rstrip().endswith(COMPLETION_SENTINEL)` is that line verbatim with the token swapped, so models reproduce it from priors. (b) The token itself is drawn from a small, high-prior set: `<<UPPER_SNAKE>>` is the standard prompt-sentinel style and END_OF_CONVERSATION is close to the most obvious phrase for a module docstringed "The durable record of a multi-turn agent conversation." This is the crux: one blind sample cannot bound a several-percent exact-match rate.
- `ticket_gives_it_away` — For the behavioural half, fully. The ticket lists `COMPLETION_SENTINEL: str` as a module constant, lists `COMPLETION_REASONS = ("open", "budget", "agent_signal")`, and says "Give it a real default implementation in terms of COMPLETION_SENTINEL." A word meaning *sentinel* plus "in terms of" leaves only "compare the reply against it". The ticket withholds only the literal string.
- `entailed_by_the_open_feature` — Again the behavioural half only. Ledger semantics fix `completion_reason == "agent_signal"` off `is_completed` on the last entry's content, and the ticket forbids the current dead `return False`; given any constant named COMPLETION_SENTINEL there is no second sane design for the base method. The literal value is not entailed by anything in A.
- `obvious_implementation_does_it` — `isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)` is the one-liner normal engineering instinct produces — it simultaneously satisfies rule's body, scope's whitespace/suffix/case discipline and failure_behavior's non-str guard, with no intent. Only the string is a real choice.

**Catalog B.**
- `no_independent_content` — `rule` as written = literal + scope + failure_behavior. Its clause `response.rstrip().endswith(...)` is precisely scope's "suffix-only, and insensitive to trailing whitespace", and its clause `isinstance(response, str)` is precisely failure_behavior's "A non-`str` response_message ... returns False rather than raising". Strip the two restatements and the unique residue is a single token value.

**A blind build that passes anyway:**

```
"""agent/turn_ledger.py — ticket only, no clue seen.

The ticket says the constant exists and that `Agent.is_completed` must be
"a real default implementation in terms of COMPLETION_SENTINEL", so I pick a
token an LLM will not emit by accident and match it as a suffix.
"""
COMPLETION_SENTINEL: str = "<<END_OF_CONVERSATION>>"

# agent/agent.py
def is_completed(self, response: t.Any) -> bool:
    """True when the agent signalled the end of the conversation."""
    return isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)

# This is a plausible blind draw, not a contrived one. The module docstring is
# "The durable record of a multi-turn agent conversation.", the sibling reason
# is "agent_signal", and `<<SHOUTING_SNAKE>>` is the house style for prompt
# sentinels; "END_OF_CONVERSATION" is close to the highest-prior phrase for it.
# The rstrip().endswith() body is AutoGen's documented default termination check
# with the token swapped, so it costs the blind agent nothing.
```

**Recommendation.** Narrow the fact, then re-run blind with instrumentation.

1. Rewrite `r2.rule` to its unique residue only: "`COMPLETION_SENTINEL` is exactly the string `\"<<END_OF_CONVERSATION>>\"`." Delete the `isinstance(response, str) and response.rstrip().endswith(...)` clause from the rule field — `scope` already owns suffix-only/case-sensitive/whitespace-blind, `failure_behavior` already owns the non-`str` guard, and that clause is handed over by the ticket's own "a real default implementation in terms of COMPLETION_SENTINEL" plus AutoGen's published `rstrip().endswith()` idiom. As written the fact takes credit for behaviour it does not gate.

2. No change needed to `test_rule__the_sentinel_is_the_end_of_conversation_token` — `assert sym(\"COMPLETION_SENTINEL\") == SENTINEL` is already the only line that decides it, and the three behavioural asserts are harmless (they pass under any reading that has the literal). Keep them as smoke.

3. Fix the real risk, which the narrowing exposes: discrimination now rests entirely on guessing one token from a small high-prior set. Re-run the blind condition at least 5 times and log the *value* each run assigns to `COMPLETION_SENTINEL`, not just pass/fail. If any run lands on `<<END_OF_CONVERSATION>>`, re-plant the token in the world corpus and in the tests as something no prior emits (e.g. `<<END_OF_CONVERSATION::v2>>` or a project-flavoured spelling) — the clue can name any string at zero cost, so there is no reason to bet the fact on the most guessable one.

4. Close the check I could not run (Bash/file tools disabled this session): grep the repo, docs, examples and the whole world corpus for `<<END_OF_CONVERSATION>>` and confirm the clue is its only occurrence. If it appears in any ticket-visible or ambient-context file, cut the fact instead of narrowing it.


## g7.r2.scope — cut

**Divergent action.** Inserting `.rstrip()` before the suffix test, and choosing a suffix test at all: `return isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)` instead of either `response.endswith(COMPLETION_SENTINEL)` (no strip) or `COMPLETION_SENTINEL in response` (containment). That is a nameable difference, so this is not a pure coincidence fact — but it is not a *reliable* one: the two variants that fail are no more likely, blind, than the variant that passes, and the case-sensitivity and "all set" clauses of the fact contribute no divergence whatsoever.

**The assertion.** `assert agent.is_completed(f"all set {SENTINEL}  \n") is True` — the only assertion whose outcome is not already handed over by Python's `endswith` defaults, by the word "sentinel" in the ticket, or by a line copied out of `test_rule`. (`assert agent.is_completed(f"{SENTINEL} but wait") is False` is the secondary one, catching containment.) Yes, it depends on more than this requirement: it is gated on `require_feature(agent.is_completed(f"all set {SENTINEL}") is True, ...)` and built from the test's hardcoded `SENTINEL` literal, so it cannot be reached at all unless the agent got r2.rule's exact token string right.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Two of the fact's three clauses are Python defaults you must take deliberate extra action to violate. `str.endswith` is case-sensitive, so `assert agent.is_completed("all set <<end_of_conversation>>") is False` passes unless the agent went out of its way to write `.lower()` or `re.IGNORECASE`. Likewise `endswith` is anchored, so "suffix-only" is satisfied by simply not reaching for `in`. The fact's wording — "case-sensitive and suffix-only" — is a description of doing nothing special.
- `model_already_knows_it` — "Strip the model's output before matching a terminator" is a well-worn idiom, not a hidden fact: provider replies routinely carry trailing `\n`, and `.strip().endswith(marker)` is the standard shape. The whitespace-tolerance clause — the only clause with real content — is exactly the piece prior habit supplies.
- `ticket_gives_it_away` — The ticket says: "Give it a real default implementation in terms of `COMPLETION_SENTINEL`", and the constant is named a *sentinel* for *completion*. A sentinel that marks the end of a reply implies a terminal/suffix check; that hands over the "suffix-only" clause (and with it the `"<<END_OF_CONVERSATION>> but wait" is False` assertion) before any clue is read. It does not hand over `rstrip()`.
- `obvious_implementation_does_it` — This is the headline finding. The single most natural expression for "a sentinel that terminates a reply" is `isinstance(response, str) and response.strip().endswith(COMPLETION_SENTINEL)`, and it satisfies all five scope assertions. `.strip()` and the specified `.rstrip()` are indistinguishable under `endswith` — leading whitespace cannot change a suffix — so the test cannot tell the clue-reader from the engineer who stripped out of habit.

**Catalog B.**
- `observable_belongs_to_another_fact` — Every scope assertion sits behind `require_feature(agent.is_completed(f"all set {SENTINEL}") is True, "Agent.is_completed's default sentinel match")`, which is verbatim r2.rule's assertion and turns on the *value* of `COMPLETION_SENTINEL` — rule's content, not scope's. The probes are also built from the test file's own `SENTINEL = "<<END_OF_CONVERSATION>>"` literal rather than from the agent's constant. So an agent with perfect rstrip/endswith discipline that guessed `"TERMINATE"` or `"<<DONE>>"` is graded on rule's token. I could not open harness.py to confirm whether require_feature skips or fails; if it fails, the bracket's "blind fails r2.scope" result is very likely measuring the token guess and not the matching discipline. Additionally `assert agent.is_completed("all set") is False` is lifted verbatim from test_rule.
- `no_independent_content` — r2.rule already publishes the exact expression: "returns `True` iff `response` is a `str` whose right-stripped form ends with it (`isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)`)". Case-sensitivity, suffix anchoring and trailing-whitespace tolerance are all just properties of that one expression restated as prose. An agent holding rule has no scope decision left to make; scope is rule's docstring.

**A blind build that passes anyway:**

```
```python
# src/bespokelabs/curator/agent/agent.py  — ticket only, no clues
def is_completed(self, response: t.Any) -> bool:
    """True once the agent has signalled the end of the conversation."""
    if not isinstance(response, str):
        return False
    return response.strip().endswith(COMPLETION_SENTINEL)
```
Written by an engineer who read only "Give it a real default implementation in terms of `COMPLETION_SENTINEL`": a *sentinel* for *completion* marks the end of a reply, so `endswith`; and provider replies carry trailing newlines, so `.strip()` first. This passes all five scope assertions. `.strip()` and the specified `.rstrip()` are behaviourally identical under `endswith`. The remaining barrier is guessing `COMPLETION_SENTINEL = "<<END_OF_CONVERSATION>>"` to clear the require_feature gate — but that is r2.rule's content, not this fact's, which is precisely the confound.
```

**A correct build the test rejects:**

```
I could not write a convincing one; the test does not overshoot. The nearest candidate is an agent reading "insensitive to trailing whitespace" against the fact's own examples (`"all set <<END_OF_CONVERSATION>>  \n"`, spaces and newline only) and writing `response.rstrip(" \n").endswith(COMPLETION_SENTINEL)`, which the test rejects via its extra `assert agent.is_completed(f"all set {SENTINEL}\t") is True`. I regard that as strained rather than legitimate — bare `.rstrip()` is the obvious idiom and the fact says "whitespace", not "spaces and newlines" — so I am not counting it as a real overshoot. The flaw here is on the discrimination side, not the fairness side.
```

**Recommendation.** Cut r2.scope as a separately graded fact and fold its two live assertions into `test_rule`, which is where they belong: r2.rule already specifies the exact expression `isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)`, so `is_completed(f"all set {SENTINEL}  \n") is True` and `is_completed(f"{SENTINEL} but wait") is False` are just rule's test written properly. Drop `is_completed("all set <<end_of_conversation>>") is False` (satisfied by inaction — `endswith` is case-sensitive) and `is_completed("all set") is False` (already asserted verbatim in `test_rule`).

If you keep the fact instead of cutting it, the minimum repair is to decouple it from its sibling: build the probes from the agent's own constant, `s = sym("COMPLETION_SENTINEL")`, and gate on `require_feature(agent.is_completed(f"all set {s}") is True, ...)` rather than on the hardcoded `SENTINEL` literal, so scope grades matching discipline independently of whether the agent guessed the token. Also confirm whether `require_feature` skips or fails — if it fails, re-run the blind bracket after the repair, because the current "blind fails" signal is probably the token guess. Be aware that the repair fixes the confound but not the coincidence: `.strip().endswith(COMPLETION_SENTINEL)` still passes blind, which is why my verdict is cut rather than retest.


## g7.r2.failure_behavior — cut

**Divergent action.** None that belongs to this fact. The only code an informed agent writes that a blind one does not is `COMPLETION_SENTINEL: str = "<<END_OF_CONVERSATION>>"` — and that is r2.rule's content, which this test re-runs as a `require_feature` gate. The residue this fact owns is the type guard, i.e. the `isinstance(response, str) and` prefix (or `str(response)`, or `try/except AttributeError`) in `return isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)`. That guard is written by an agent who read nothing but the ticket's own signature `is_completed(self, response: t.Any) -> bool`, so it is not a divergent action; it is the default response to an `Any`-typed parameter.

**The assertion.** `assert agent.is_completed({\"text\": SENTINEL}) is False` (with `assert agent.is_completed(None) is False` as its twin). Passing or failing it depends on much more than this requirement: it is preceded by `require_feature(agent.is_completed(f\"all set {SENTINEL}\") is True, ...)`, so the test cannot even be entered unless r2.rule's hidden sentinel string is already correct — and once it is, the assertion is satisfied by the guard clause that r2.rule's own stated implementation (`isinstance(response, str) and ...`) already contains. It is also satisfied by the untouched checkout, whose `is_completed` returns `False` unconditionally.

**Catalog A.**
- `codebase_already_does_it` — The ticket states the starting point openly: "Agent.is_completed(self, response: t.Any) -> bool currently returns False unconditionally". So the checkout as shipped already satisfies every literal assertion of this fact — `is_completed({"text": SENTINEL}) is False`, `is_completed(None) is False`, no AttributeError, no TypeError. The test's own comment admits it: "An untouched Agent returns False for everything, so this constraint only means something once the sentinel match exists at all." The fact is inherited for free by not touching the path; only failing a *different* fact (r2.rule) can make it fail.
- `prohibition_satisfied_by_inaction` — The fact is phrased as a prohibition — "with no `AttributeError` or `TypeError` escaping". Not raising requires no deliberate work; it is the state of the method today and the state of every implementation that spells the match with `isinstance(...)` or `str(...)`. Deliberate extra work is required to *violate* it (dropping the guard on an `Any`-annotated parameter).
- `model_already_knows_it` — "Guard an `Any`-typed parameter with `isinstance` before calling a str method" is ordinary defensive-Python instinct, not a hidden convention. It is also the local house idiom the ticket itself publishes for the same value: TurnEntry's `content` is "`response_message` coerced with `str()` when it is not already a `str`". An agent mirroring the surrounding code reaches the same behaviour from priors.
- `ticket_gives_it_away` — The ticket prints the exact signature — `Agent.is_completed(self, response: t.Any) -> bool` — which announces both halves of this fact: non-`str` inputs are in-domain (`t.Any`) and the answer is a `bool`, never an exception (`-> bool`). Everything this fact adds beyond the ticket is the sentinel string, which is r2.rule.
- `obvious_implementation_does_it` — Both of the two most natural spellings pass all four assertions. `isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)` passes by construction. `str(response).rstrip().endswith(COMPLETION_SENTINEL)` also passes: `str(None)` is `'None'`, `str({"text": "<<END_OF_CONVERSATION>>"})` ends with `'}`, `str([SENTINEL])` ends with `']`, `str(42)` is `'42'` — four Falses and no exception. The test cannot distinguish "read the clue" from "wrote normal code"; it can only distinguish "knew the sentinel string".

**Catalog B.**
- `state_is_unreachable` — In the product, `is_completed` is reached only through `build_ledger`, which per the ticket checks "the **last** entry's author's `is_completed` ... for its content" — and `TurnEntry.content` is `response_message` "coerced with `str()` when it is not already a `str`". A dict or `None` therefore cannot reach `is_completed` on any live path; the ledger has already coerced it. The test reaches the state only by constructing a bare `Agent` and calling the method directly.
- `behaviour_has_no_consequence` — Because of the coercion above, an implementation that raises `AttributeError` on a dict and one that returns `False` produce identical end-to-end behaviour in every scenario the task describes — including r2.observability's 3-call run and r1's sidecar runs. There is no differentiating outcome anywhere except a direct unit call on the method. Violating this fact costs the system nothing.
- `observable_belongs_to_another_fact` — The only channel that makes these assertions non-trivial is `require_feature(agent.is_completed(f"all set {SENTINEL}") is True, "Agent.is_completed's default sentinel match")` — verbatim the assertion of r2.rule (`test_rule__the_sentinel_is_the_end_of_conversation_token`) and the same gate r2.scope and r2.observability use. This fact is graded through r2.rule's observable; blind failure here is r2.rule failing, not this fact failing.
- `no_independent_content` — Subtract r2.rule and nothing measurable is left: r2.rule already spells the implementation in full — "`isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)`". The `isinstance` guard that this fact is about is a clause of the sibling's own stated rule. There is no way to fail this fact without either failing r2.rule (gate) or having deliberately dropped a clause r2.rule already dictates.

**A blind build that passes anyway:**

```
def is_completed(self, response: t.Any) -> bool:\n    \"\"\"True when the agent's reply ends with the completion sentinel.\"\"\"\n    return str(response).rstrip().endswith(COMPLETION_SENTINEL)\n\n# and the even more common spelling:\ndef is_completed(self, response: t.Any) -> bool:\n    return isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)\n\n# Written by an engineer who saw only the ticket line \"Give it a real default\n# implementation in terms of COMPLETION_SENTINEL\", the signature `response: t.Any`,\n# and the ticket's own coercion idiom for TurnEntry.content. Neither author ever\n# considered a structured-output dict. Both pass all four assertions:\n#   str(None) -> 'None'; str({'text': S}) -> \"{'text': '<<END_OF_CONVERSATION>>'}\";\n#   str([S]) -> \"['<<END_OF_CONVERSATION>>']\"; str(42) -> '42'  -> four Falses, no raise.\n# Conditional on knowing the sentinel (r2.rule's content, supplied by r2.rule's clue),\n# this fact adds zero discriminating power. The bracket's blind sample failed the\n# require_feature gate, not this fact.
```

**A correct build the test rejects:**

```
def is_completed(self, response: t.Any) -> bool:\n    \"\"\"True when the reply ends with the sentinel; structured replies are unwrapped.\"\"\"\n    if isinstance(response, dict):\n        response = response.get(\"text\") or response.get(\"content\") or \"\"\n    return isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)\n\n# This satisfies the fact as *stated in prose* -- \"returns False rather than raising ...\n# with no AttributeError or TypeError escaping\": nothing escapes, ever. It is a\n# legitimate reading of \"the structured-output `dict`\": the fact singles out a dict\n# carrying the sentinel under a \"text\" key, which reads as an invitation to look inside\n# rather than to ignore it -- and a partner agent that genuinely signalled completion\n# through structured output arguably *should* stop the conversation. The test rejects it\n# on `assert agent.is_completed({\"text\": SENTINEL}) is False`. An agent working from a\n# clue rather than from this fact's exact wording lands here easily.
```

**Recommendation.** Cut `r2.failure_behavior`. It fails four Catalog A patterns and four Catalog B patterns, and the test's own comment concedes the problem ("An untouched Agent returns False for everything, so this constraint only means something once the sentinel match exists at all"). The untouched checkout passes it; the obvious implementation passes it; violating it changes no observable in any run the task describes, because the ticket already mandates that `TurnEntry.content` is `str()`-coerced before `is_completed` ever sees it. Its apparent discrimination in the free bracket is r2.rule's discrimination, re-measured through r2.rule's own `require_feature` gate. Keep `test_failure_behavior__...` in the file as a regression guard if you like, but stop scoring it as a distinct hidden fact.

If you want r2 to keep a failure-behavior fact, it must be made consequential rather than narrowed — retest it end to end on a path that actually carries a non-`str`. Concretely: change the ledger so the stop check runs on the raw `response_message` (before the `str()` coercion into `TurnEntry.content`), then grade a run, not a unit call: `Conversation(replies=["a", "b", {"text": f"done {SENTINEL}"}, "d"], ...)` with `max_length=6` must reach 4 calls without raising, `ledger.completion_reason == "open"` after the dict turn, the dict turn still logged and counted, and `str(row["content"])` in the dataset. That version has a divergent action (the guard is load-bearing), an in-product consequence, and an observable that is not r2.rule's gate. Also drop the `[SENTINEL]` and `42` assertions — they are not in the fact and buy nothing.

One check I could not run: every file tool was disabled this session, so I could not grep the checkout for the literal `<<END_OF_CONVERSATION>>`. Before shipping any of r2, confirm the string appears nowhere in the repo (examples, default system prompts, docs, tests, README) — if it does, a blind agent greps it, the `require_feature` gate opens, and by the analysis above every fact in r2 collapses at once, not just this one.


## g7.r2.observability — cut

**Divergent action.** None. I cannot name any code an agent who saw r2.observability writes that an agent who saw only (a) the open ticket and (b) sibling r2.rule does not. The only clue-dependent expression anywhere in this test's pass/fail path is `COMPLETION_SENTINEL = "<<END_OF_CONVERSATION>>"` plus the `isinstance(response, str) and response.rstrip().endswith(COMPLETION_SENTINEL)` body — and both belong to r2.rule, which asserts them directly. The "append it / count it / put it in the dataset / stop after it" behaviour is written by the open ticket's own text, not by this clue. By the rubric's diagnostic ("If you can't name a specific divergent action, it's a coincidence fact"), this fact is a coincidence riding on r2.rule's discrimination.

**The assertion.** `assert len(conversation.calls) == 3, conversation.calls` — the only assertion expressing anything beyond bookkeeping ("the conversation stops after it"). It depends on much besides this requirement: (1) on sibling r2.rule, since a wrong `COMPLETION_SENTINEL` trips `require_feature(...)` before this line is ever reached; (2) on the open ticket's "`run()` short-circuits on `ledger.completed`" and "The loop condition is `while ledger.responses < self.max_length`"; (3) on the fake, which supplies exactly three scripted replies. Strictly, the assertion that carries all the hidden-requirement signal is the gate itself, `require_feature(probe.is_completed(f"all set {SENTINEL}") is True, ...)`, which is r2.rule's assertion verbatim.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The fact's whole framing is a prohibition: the message is "a real turn, not a discarded control signal". Discarding it requires deliberate extra code — an explicit branch that detects the sentinel and swallows the record before `append_response()`. No engineer writes that swallow-branch unprompted. Doing nothing satisfies the rule, so it never tests restraint.
- `ticket_gives_it_away` — Every assertion is quoted spec. `completion_reason == "agent_signal"` <- "`completion_reason` is `"agent_signal"` when the **last** entry's author's `is_completed` returns true for its content". `ledger.responses == 3` <- "`responses == len(entries) - 1`". `len(log_lines) == 4` <- "leaves `max_length + 1` log lines" + the seed-is-a-durable-turn section. 4 dataset rows with `content`/`role` <- "`create_dataset_file(working_dir)` writes one row per log line with exactly four fields". `len(calls) == 3` <- "`run()` short-circuits on `ledger.completed`". `num_responses == 3` <- the `update_turn`/`adopt_ledger` spec. Nothing is left for the clue to add.
- `entailed_by_the_open_feature` — Decisive. The ticket defines `completion_reason` as a function of the LAST LOG ENTRY's content, and the ledger is built from the log (`load_ledger` is `read_log` + `build_ledger`). An implementation that discards the sentinel message therefore has no last entry to compute `"agent_signal"` from — it is architecturally impossible to satisfy the open ticket while violating this fact. This is the rubric's "once the agent builds the visible feature correctly, the hidden requirement is the *only* way to do it".
- `obvious_implementation_does_it` — The natural loop — `while ledger.responses < self.max_length:` / call the agent / `append_response(...)` / rebuild ledger / `if ledger.completed: break` — appends, counts, stops, and writes the dataset from the log, with no intent to satisfy anything. The test cannot distinguish "read the clue" from "wrote normal code".

**Catalog B.**
- `state_is_unreachable` — The failure this fact excludes cannot be constructed. To have a "discarded control signal" you would need `completion_reason == "agent_signal"` with the message absent from the log — but the ticket derives completion from `entries[-1].content` and derives `entries` from the log. Never-happening and being-correctly-excluded are indistinguishable here, which is exactly the rubric's failure mode.
- `observable_belongs_to_another_fact` — Two ways. (1) The clue-bearing channel is `require_feature(probe.is_completed(f"all set {SENTINEL}") is True, "Agent.is_completed's default sentinel match")` — verbatim r2.rule's assertion, re-run as a gate; all hidden-requirement signal enters through it. (2) The end-state channel is already r1.observability's: that fact independently asserts "After a completed 4-line run" with `"completion_reason": "agent_signal"`, `"responses": 3`, `"turns": 4`. Grading r2 through those observables double-counts r1 and the open ticket.
- `no_independent_content` — The test cannot fail while r2.rule passes, except by failing the open ticket. A wrong sentinel trips the `require_feature` gate (that is rule's discrimination). A right sentinel plus a competent ticket implementation passes every remaining assertion, because every remaining assertion is quoted from the ticket. There is no way to fail this fact without failing the neighbour or failing the visible ask — it adds no information.

**A blind build that passes anyway:**

```
Ticket-only, no clue seen. The engineer reads "Constants: ... `COMPLETION_SENTINEL: str`" and "Give it a real default implementation in terms of `COMPLETION_SENTINEL`", picks the most literal name for the concept in a module about conversations, and writes the one-line matcher any engineer writes:

```python
# src/bespokelabs/curator/agent/turn_ledger.py
COMPLETION_SENTINEL: str = "<<END_OF_CONVERSATION>>"

# src/bespokelabs/curator/agent/agent.py
def is_completed(self, response: t.Any) -> bool:
    """True when the reply ends with the completion sentinel."""
    if not isinstance(response, str):
        return False
    return response.rstrip().endswith(COMPLETION_SENTINEL)

# src/bespokelabs/curator/agent/processor.py, inside run()
ledger = self.load_cache(working_dir)
self.status_tracker.adopt_ledger(cached_responses=ledger.responses)
if not ledger.entries:
    self.append_response(build_seed_record(
        seeder_name=self.seeder.name, seed_message=self.seed_message,
        model_name=self.seeder.model_name, now=self.now_fn()), working_dir)
    ledger = self.load_cache(working_dir)
while ledger.responses < self.max_length:
    if ledger.completed:
        break
    agent = self._agent_for(ledger.next_speaker)
    response = await self.call_single_request(
        APIRequest(task_id=ledger.responses, ...), ...)
    self.append_response(response, working_dir)
    ledger = self.load_cache(working_dir)
    self.conversation_history = ledger.messages()
    self.status_tracker.update_turn(agent, response_success=True, ...)
```

This passes `test_observability__...` in full — 3 calls, 4 log lines, `num_responses == 3`, `responses == 3`, `"agent_signal"`, 4 rows, last row `content`/`role` correct — with the only gamble being the sentinel string, which is r2.rule's gamble and a strong blind attractor (`<<SYS>>`/`<<EOT>>` convention + the most literal phrase). The bracket's single blind sample landing on a different sentinel is thin evidence that this is unreachable blind.
```

**A correct build the test rejects:**

```
A literal reading of the ticket's own two sentences — "The loop condition is `while ledger.responses < self.max_length`" and "`run()` calls `status_tracker.adopt_ledger(...)` exactly once, immediately after the ledger is loaded and **before** the `ledger.completed` short-circuit" — yields a load-time-only short-circuit:

```python
ledger = self.load_cache(working_dir)
self.status_tracker.adopt_ledger(cached_responses=ledger.responses)
if ledger.completed:                     # the short-circuit the ticket sites here
    return self.create_dataset_file(working_dir)
while ledger.responses < self.max_length:   # the loop condition, verbatim
    ...
```

With `max_length = 6` this makes six calls against a three-reply fake and dies at `assert len(conversation.calls) == 3`. The ticket never says the `completed` check is re-evaluated inside the loop; it spells out the loop condition explicitly and separately, and places the only named short-circuit at load time. I judge this a misreading rather than a correct alternative — but it is textually defensible, and note what it means: this test's realistic failure mode is open-ticket loop plumbing, not the hidden sentinel. That is the wrong axis for a hidden-requirement test even when the rejection is arguably fair.
```

**Recommendation.** Cut `observability` as a scored field on r2. It fires four Catalog A patterns (ticket_gives_it_away, entailed_by_the_open_feature, obvious_implementation_does_it, prohibition_satisfied_by_inaction) and four Catalog B patterns (state_is_unreachable, observable_belongs_to_another_fact, no_independent_content), and I could name no divergent action for it. Its `hidden` bracket result is real but wholly inherited from r2.rule via the `require_feature` gate.

Concretely:
1. Move the body of `test_observability__the_message_that_ends_the_talk_is_still_a_turn` into `test_rule__the_sentinel_is_the_end_of_conversation_token` as a corroborating end-to-end. It does usefully prove the sentinel wires through a live run; it just is not a separate fact. Drop the `require_feature` gate there, since rule's own assertions already establish the precondition.
2. Relocate the `len(log_lines) == 4`, `ledger.responses == 3`, `num_responses == 3` and 4-row dataset assertions to the open-ticket suite, where failing them correctly reads as "failed the visible ask."
3. Do not try to narrow r2 to a fourth field. I attempted to construct one and could not: the ticket settles the entire completion path (`completion_reason` from the last entry, `responses == len(entries) - 1`, one dataset row per log line), so any remaining candidate is either restatement or a prohibition satisfied by inaction.
4. Separately, re-sample the blind condition against r2.rule alone with several agents. `"<<END_OF_CONVERSATION>>"` is a strong prior and one blind sample is not enough to call that string hidden.
5. Also worth fixing regardless of this verdict: the ticket should state that `ledger.completed` is re-checked each iteration, not only after load. As written it invites the six-call implementation quoted in `correct_fail`.
