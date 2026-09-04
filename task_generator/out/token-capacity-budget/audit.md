# Audit — g10 (token-capacity-budget)

| fact | bracket | audit | why |
|---|---|---|---|
| `g10.r1.rule` | hidden | **narrow** | Narrow `rule` so it measures the floor and nothing else, and so it stops being a subset of `scope`.

1. Delete the prerequisite `assert t.available_token_capaci |
| `g10.r1.scope` | hidden | **narrow** | Narrow the fact and the test to the one thing that is not a restatement of r1.rule or of the open ticket: the per-axis floor under `seperate`.

In `test_scope__ |
| `g10.r1.exclusions_or_crossover` | hidden | **retest** | Retest, narrowed to the one measurement the fact actually owns.

1. Delete the `released` scenario entirely (`released.free_capacity(used=T(0,0), blocked=T(700, |
| `g10.r1.observability` | hidden | **retest** | Retest — keep the fact, fix the last assertion. (1) Make the second increment come from an unsaturated state instead of a re-clamp: insert `seed_full(sep)` (or  |
| `g10.r2.rule` | hidden | **retest** | Retest — keep the fact, fix the naming asymmetry in the test. The fact discriminates for a real reason (the `+1.0` on the request slot is invisible in the ticke |
| `g10.r2.scope` | hidden | **cut** | Cut r2.scope as a separately graded fact and fold `test_scope__both_failure_exits_refund_while_the_success_exit_settles` into r2.rule's test as its end-to-end a |
| `g10.r2.exclusions_or_crossover` | hidden | **cut** | Cut `r2.exclusions_or_crossover`. It cannot be repaired by re-testing: on the token axis, "refund the whole blocked estimate" and "settle with `used = 0`" are t |
| `g10.r2.observability` | hidden | **retest** | Retest, three concrete changes.

1. **Stop the field borrowing its signal from r2.rule.** Split `test_observability__...` in two. The first test must not mentio |

## g10.r1.rule — narrow

**Divergent action.** In `capacity_budget.py`, a module-level `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25`, and in the tracker a floor applied to the *result* of a settlement rather than a clamp at zero: under `combined`, `self.available_token_capacity = max(new_value, -self.max_tokens_per_minute * CAPACITY_DEBT_FLOOR_FRACTION)` (a `float`), and under `seperate` a per-axis `max(axis_value, math.ceil(-limit_axis * CAPACITY_DEBT_FLOOR_FRACTION))` (an `int`), run at the end of `consume_capacity` and of the release path. The blind agent writes one of exactly two other things: no clamp at all (`self.available_token_capacity += blocked.total - used.total`, landing on `-500.0`) or the reflexive non-negativity clamp `max(0.0, ...)` (landing on `0.0`). Both are named and excluded by the test's own comment: "not -500.0 (no floor), not -1000.0 (floor at -limit), not 0.0 (floor at zero)". No blind agent invents the identifier `CAPACITY_DEBT_FLOOR_FRACTION` or the value 0.25.

**The assertion.** `assert t.available_token_capacity == -250.0` (with `assert fraction == 0.25` as a prerequisite gate). Yes, it depends on more than this requirement: (a) on `consume_capacity`, which the test asserts against separately at `assert t.available_token_capacity == 200.0` — an openly stated, `test_open`-graded behaviour; (b) on the open ticket's settlement direction `blocked - used` under `combined`; (c) on `__post_init__` shape coercion, partially neutralised by `seed_full`. It does NOT depend on r2 (test_rule makes no `available_request_capacity` assertion) — that coupling lives in `test_scope`, whose `assert defaulted.available_request_capacity == 59.0` and `assert sep.available_request_capacity == 59.0` are true only under r2.rule's split of settlement from refund.

**Catalog A.** clean

**Catalog B.**
- `observable_belongs_to_another_fact` — `test_rule` hard-asserts `assert t.available_token_capacity == 200.0` before the settlement. That is `consume_capacity` correctness — an openly stated behaviour the docstring itself says is "graded in `test_open`". The test author neutralised the seeding fact via `seed_full` ("so that an agent who got the debt floor right and the seeding wrong loses one fact rather than two") but then re-introduced the same double-jeopardy one line later for consume. A tree with a perfect floor loses r1.rule if `consume_capacity` deviates at all — e.g. if it calls `update_capacity()` first and the default `capacity_clock=time.time` refills a fraction of a token.
- `no_independent_content` — r1.rule is strictly entailed by r1.scope. `test_scope`'s first block is itself a *combined* tracker: `defaulted.free_capacity(...)` then `assert defaulted.available_token_capacity == -25000.0` on a 100_000 limit. That single assertion already pins the fraction at 0.25, the combined-axis float, and the placement of the floor at the end of the settlement. Any tree that passes `scope` necessarily passes `rule`; only the converse can fail (flooring against the pre-normalisation limit). Given scope, rule adds only `assert fraction == 0.25` — and scope already requires the constant to exist via `require_feature(has_floor_constant(), ...)`.

**A correct build the test rejects:**

```
A tree with a textbook-correct debt floor whose `consume_capacity` refills before spending — the ticket forbids this only for `has_capacity` (\"The check runs **before** `update_capacity()`\"), never for `consume_capacity`:

```python
def consume_capacity(self, token_estimate: _TokenUsage) -> None:
    self.update_capacity()          # refill before spending; the ticket never forbids it
    if self.available_token_capacity is not None:
        if self.token_limit_strategy == TokenLimitStrategy.combined:
            self.available_token_capacity -= token_estimate.total
        else:
            self.available_token_capacity = _TokenUsage(
                input=self.available_token_capacity.input - token_estimate.input,
                output=self.available_token_capacity.output - token_estimate.output,
            )
    if self.available_request_capacity is not None:
        self.available_request_capacity -= 1
    self._apply_debt_floor()        # exactly -CAPACITY_DEBT_FLOOR_FRACTION * limit
```

The floor is right and the settlement lands on exactly `-250.0`, but the bundled prerequisite `assert t.available_token_capacity == 200.0` sees `200.0000031…` because `update_capacity` refilled `1000 * elapsed / 60` against the default `capacity_clock=time.time`, and r1.rule is lost for a reason that belongs to `test_open`. This is conditional on `tracker()` in `test_open.py` not injecting a frozen clock by default — I could not read that helper. If it does inject one this specific route is closed, but the double-jeopardy on `consume_capacity` (any other deviation in it fails r1.rule too) stands regardless.
```

**Recommendation.** Narrow `rule` so it measures the floor and nothing else, and so it stops being a subset of `scope`.

1. Delete the prerequisite `assert t.available_token_capacity == 200.0` from `test_rule`, or replace it with a re-seed (`t.available_token_capacity = 200.0`) in the same spirit as `seed_full`. As written it re-grades `consume_capacity`, which `test_open` owns.

2. Give `rule` content that `scope` does not already imply, or merge the two. `test_scope`'s `defaulted.available_token_capacity == -25000.0` is itself a combined-axis case and already pins the 0.25 fraction, so `rule` is currently free once `scope` passes. Two candidates for genuinely independent content: assert the combined axis is a `float` and the `seperate` axes are `int` (`isinstance(t.available_token_capacity, float)`; `all(isinstance(v, int) for v in (c.input, c.output))`), which no other test checks; and exercise the floor at the end of `consume_capacity` — a consume that alone drives the bucket past the floor — which `scope`, `exclusions` and `observability` never do even though the fact says the floor is "applied at the end of `consume_capacity`".

3. Fix the answer key. The fact says the case ends at `-250.0` "(not `-700.0`, not `0.0`)". `-700` is the delta; the unfloored result is `-500.0`, as the test's own comment says. Correct the fact text and any clue that repeats the number.

4. Move the two r2-owned assertions out of `test_scope`: `assert defaulted.available_request_capacity == 59.0` and `assert sep.available_request_capacity == 59.0` hold only under r2.rule's settlement/refund split, so an agent who found the debt-floor clue but not the release-split clue loses r1.scope for an r2 reason. If `scope` needs to say something about the request bucket, assert only `>= 0` or drop the clause — "never floored" is unobservable anyway, since `has_capacity` gating means the request bucket can never reach a floor.

5. Reword r1.rule's "applied at the end of `consume_capacity` and of both release operations": "both release operations" presupposes r2's two-method split and leaks it, while r1's own test only ever calls `free_capacity`. Say "at the end of `consume_capacity` and of every operation that adds capacity back".


## g10.r1.scope — narrow

**Divergent action.** Under `seperate`, computing each axis's floor from that axis's own normalised limit — `math.ceil(-limit.input * CAPACITY_DEBT_FLOOR_FRACTION)` and `math.ceil(-limit.output * ...)` — rather than one floor from `limit.total` (which would give -375/-375 instead of -250/-125). That is the whole of the divergence. The other half of the fact ("effective, i.e. post-`__post_init__`, limit") names no divergent code at all: at settle time `self.max_tokens_per_minute` IS the effective limit, because `__post_init__` overwrote `0` with `DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED` in place; an agent would have to deliberately stash the constructor argument (`self._raw_limit = max_tokens_per_minute`) to fail it, and nothing in the ticket invites that.

**The assertion.** `assert token_axes(sep.available_token_capacity) == (-250, -125, -375)` — the only assertion whose failure is uniquely scope's. Yes, it depends on other requirements: it cannot pass unless r1.rule's floor exists at all (`CAPACITY_DEBT_FLOOR_FRACTION`, applied in `free_capacity`), and the same test's other assertions depend on the open ticket's `0` → `100_000` defaulting, on the open `None`-axis skip rule, and — via `assert defaulted.available_request_capacity == 59.0` after a `free_capacity` — on r2.rule.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Two of scope's clauses are satisfied by doing nothing extra. "An axis whose limit and capacity are `None` has no floor and stays `None`" is already the open ticket's rule — "An axis whose capacity is `None` is read, skipped and left `None` by all of these" — so the `if limit is None: return` guard the agent already wrote for the open feature satisfies it. "`available_request_capacity` is never floored" likewise requires writing no code: nobody floors a bucket they were never told to floor.
- `ticket_gives_it_away` — Everything in scope except the existence of a floor is stated openly. The ticket already specifies "A limit of `0` … is replaced by the matching `DEFAULT_*` constant axis by axis", the `combined`/`seperate` shape coercion, and "An axis whose capacity is `None` is read, skipped and left `None`". `test_scope` even asserts the open facts directly: `assert defaulted.max_tokens_per_minute == 100_000` and `assert unlimited.available_token_capacity is None`.
- `entailed_by_the_open_feature` — Conditioned on the sibling r1.rule ("each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit`"), the open feature supplies the only limit in existence. Because `__post_init__` mutates `self.max_tokens_per_minute` in place, `-0.25 * self.max_tokens_per_minute` at settle time is necessarily the effective limit — there is no alternative implementation of rule that omits scope, except the `.total`-vs-per-axis slip.
- `obvious_implementation_does_it` — The natural floor helper is `floor = -self.max_tokens_per_minute * CAPACITY_DEBT_FLOOR_FRACTION`. It reads the normalised field because that is the only field there is, and under `seperate` a per-axis loop (`for axis in ('input','output')`) is the obvious shape since the ticket already forces per-axis arithmetic everywhere else ("Under `seperate` the refill increment is `math.floor(limit_axis * elapsed / 60.0)`").

**Catalog B.**
- `observable_belongs_to_another_fact` — Twice. (a) The deciding channel, `available_token_capacity` landing on a fraction of the limit, is r1.rule's own observable — `test_rule` already asserts `t.available_token_capacity == -250.0`. (b) `assert defaulted.available_request_capacity == 59.0` and `assert sep.available_request_capacity == 59.0` are read AFTER a `free_capacity` call, which makes them assertions about r2.rule ("`available_request_capacity` is left exactly as `consume_capacity` left it") and about where the `-1` lives — neither is r1.scope's content.
- `no_independent_content` — Scope is r1.rule evaluated on two more fixtures. Strip the open-ticket assertions and the r2 assertions and what remains is `-25000.0` (= rule's `-0.25 * limit` on a limit the open ticket already fixed at 100_000) and `(-250, -125, -375)` (= rule's `math.ceil(-limit*0.25)` "for each `seperate` axis", verbatim). Only the `.total`-vs-per-axis disambiguation is new.

**A correct build the test rejects:**

```
A tree with a textbook-correct debt floor that fails `test_scope` on where the request slot is spent. r1.scope itself says the request bucket "is only decremented after a successful `has_capacity`", and the open ticket never says `consume_capacity` touches the request axis — it only says `_reserve_capacity` "on `False` … returns `None` having consumed nothing, neither tokens nor the request slot". So this is a legitimate reading:

```python
# tracker
def consume_capacity(self, token_estimate: _TokenUsage) -> None:
    """Spend the token axes; the request slot is spent by the reserver."""
    self._spend_tokens(token_estimate)
    self._apply_debt_floor()          # r1.rule/scope, per axis, effective limit

# processor
def _reserve_capacity(self, status_tracker, messages):
    estimate = self.estimate_total_tokens(messages)
    if not status_tracker.has_capacity(estimate):
        return None
    status_tracker.consume_capacity(estimate)
    if status_tracker.available_request_capacity is not None:
        status_tracker.available_request_capacity -= 1   # only after a successful has_capacity
    return estimate
```

This lands on `-25000.0` and `(-250, -125, -375)` exactly, and still fails `test_scope` at `assert defaulted.available_request_capacity == 59.0` (it is `60.0`, because the test calls `t.consume_capacity(...)` directly and never goes through `_reserve_capacity`). A second variant fails the same line for an r2 reason: an agent who has `free_capacity` return the request slot has a perfect r1 and still reads `60.0`.
```

**Recommendation.** Narrow the fact and the test to the one thing that is not a restatement of r1.rule or of the open ticket: the per-axis floor under `seperate`.

In `test_scope__the_floor_follows_the_normalised_limit_of_each_axis`, delete:
- `assert defaulted.available_request_capacity == 59.0` and `assert sep.available_request_capacity == 59.0` — these grade r2.rule and an unstated choice about whether the `-1` lives in `consume_capacity` or in `_reserve_capacity`, and they fail a correct r1 implementation (see correct_fail);
- the `unlimited = tracker(...)` block — "an axis whose capacity is `None` is read, skipped and left `None` by all of these" is an openly stated ticket fact already graded in `test_open`;
- `assert defaulted.max_tokens_per_minute == 100_000` and `assert defaulted.available_token_capacity == 0.0` — open-ticket normalisation and seeding, likewise already graded.

Keep `defaulted.available_token_capacity == -25000.0` (cheap, and it is the one place "effective limit" is nominally observable) and make `token_axes(sep.available_token_capacity) == (-250, -125, -375)` the deciding assertion, with the fact's wording reduced to: "under `seperate` each axis is floored against its own normalised limit, not against `limit.total`." Also add the discriminator that currently has no test — a `seperate` tracker built with `max_tokens_per_minute=_TokenUsage(input=0, output=500)`, where only the input axis defaults, so the floors are `-25000` and `-125` — otherwise the `.total`-based implementation is the only wrong answer the fact can catch and the fact stays thin. If you are unwilling to add that, cut scope and fold the `seperate` fixture into `test_rule`, which already owns this observable.


## g10.r1.exclusions_or_crossover — retest

**Divergent action.** There is no divergent action unique to this fact against a BLIND agent — the blind agent writes neither `CAPACITY_DEBT_FLOOR_FRACTION` nor `num_capacity_debt_clamps`, so it dies on `require_feature(has_floor_constant() and has_clamp_counter(probe), ...)`, which is r1.rule's and r1.observability's artifacts, not this one's. The only divergence this fact owns is INSIDE the clue-seeing population: an agent who factors clamping as one shared helper — `def _clamp(self, v, lo, hi): c = min(max(v, lo), hi); if c != v: self.num_capacity_debt_clamps += 1; return c` — called from the refill path, the release path and the floor path, versus an agent who increments only in the floor path (`floored = max(new, -limit * CAPACITY_DEBT_FLOOR_FRACTION); if floored != new: self.num_capacity_debt_clamps += 1`) and uses a bare `min(new, limit)` for the ceiling. That is the whole measurable delta, and the sibling-supplied field name "debt clamps" already steers agents away from the shared-helper version.

**The assertion.** `assert clamp_count(refilled) == 0` (after `clock.now = 1060.0; refilled.update_capacity()` caps the bucket at 1000.0). It is the only assertion in the test that is exclusion-specific. Passing or failing it depends on much besides this requirement: on r1.rule (`has_floor_constant()` must be true or the gate fires), on r1.observability (`has_clamp_counter()` must be true, and the counter must exist and start at 0), and on the OPEN ticket's `update_capacity` refill capping at the limit. The other two `clamp_count(...) == 0` assertions are worse — `clamp_count(released) == 0` is preceded by `assert released.available_token_capacity == 1000.0`, which grades an unstated ceiling cap in `free_capacity`, and `clamp_count(settled) == 0` is r1.observability's contrapositive.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — This is the strongest hit. The fact is stated as a must-NOT: 'the refill ... capping an axis at its limit, and a release capping an axis at its limit, leave the clamp counter untouched.' The ceiling caps come from the OPEN ticket ('refill is capped above at the limit') and are written as `min(new, limit)` before any counter exists; the counter is introduced later, bound to the floor. Incrementing on a ceiling cap requires deliberate extra work in a different code path. Doing nothing satisfies the rule, so the test never exercises restraint for the overwhelming majority of implementations.
- `ticket_gives_it_away` — Not the open ticket, but the sibling clue the informed agent necessarily has: r1.observability names the field `num_capacity_debt_clamps` and defines it as 'increments by exactly one per call that clamped at least one axis' in a requirement whose entire subject is the DEBT floor. Anyone with that field name has been told, in the identifier itself, that a ceiling cap is not a debt clamp. The exclusion adds nothing the naming has not already given away.
- `entailed_by_the_open_feature` — r1.rule fixes the structure: the floor 'is applied at the end of `consume_capacity` and of both release operations.' Put the increment where the floor is applied — the only natural place — and the ceiling caps in `update_capacity` and the release, which are separate expressions from a separate (open) requirement, cannot possibly increment it. Once the floor is built as specified, the exclusion is not an additional choice.
- `obvious_implementation_does_it` — The single most natural code is `available = min(available + refill, limit)` for the ceiling (open ticket) and a distinct floor step `if floored != raw: self.num_capacity_debt_clamps += 1` for the debt. Normal engineering instinct — increment the counter next to the thing it is named after — passes all three scenarios without anyone intending the exclusion.

**Catalog B.**
- `state_is_unreachable` — The `released` scenario constructs `released.free_capacity(used=T(0,0), blocked=T(700,100))` on a bucket the tracker seeded full at 1000.0 with no prior `consume_capacity`. In the real flow `_reserve_capacity` always consumes before `handle_single_request_with_retries` settles, and it settles against the very estimate it consumed, so a settlement can never push an axis above its limit. The ceiling-cap-on-release behaviour this half of the fact grades is unreachable through the codebase's own path and exists only under direct construction.
- `contradicts_a_sibling` — Flagging this as a specification conflict rather than a literal unreachable-branch conflict. r2.rule says the refund 'gain[s] the whole `blocked` estimate back (capped above at the limit)' and contrasts it with the settlement, described as 'the token axes gain `blocked - used`' with no cap mentioned. An agent reading both siblings has positive reason to write an UNCAPPED settlement — and then fails this test's `assert released.available_token_capacity == 1000.0`. One sibling's wording steers a correct agent into the other's failure.
- `observable_belongs_to_another_fact` — `num_capacity_debt_clamps` is declared by r1.observability ('A tracker field `num_capacity_debt_clamps: int = 0` increments by exactly one per call that clamped at least one axis'). This fact has no channel of its own; `clamp_count()` is r1.observability's channel, and `require_feature(...has_clamp_counter...)` makes the fact ungradable unless that sibling was implemented. Grading here double-counts observability.
- `no_independent_content` — Scenario three — 'a settlement whose result stays above the floor ... leaves the counter at `0`' — is the exact contrapositive of observability's 'increments by exactly one per call that CLAMPED at least one axis.' No clamp, no increment. It cannot fail without observability failing. Only the refill-ceiling scenario carries content the neighbour does not already assert.

**A correct build the test rejects:**

```
A settlement with a debt floor but no ceiling cap — the reading r2.rule invites by capping the refund and pointedly not capping the settlement:

```python
def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage) -> None:
    self.num_capacity_settlements += 1
    if self.available_token_capacity is None:
        return
    if self.token_limit_strategy == TokenLimitStrategy.combined:
        # a settlement only returns what was reserved and not spent; it has no
        # reason to rise above the limit, so only the debt floor is applied
        new = self.available_token_capacity + float(blocked.total - used.total)
        floor = -float(self.max_tokens_per_minute) * CAPACITY_DEBT_FLOOR_FRACTION
        if new < floor:
            new = floor
            self.num_capacity_debt_clamps += 1
        self.available_token_capacity = new
    else:
        ...  # per-axis, same shape, math.ceil floor, one increment per call
```

This satisfies r1.rule (`-250.0` on the worked case), r1.scope (`-25000.0` defaulted, `(-250, -125, -375)` under `seperate`), r1.observability (one increment per clamping call, two calls -> 2) and the whole open ticket, which never says `free_capacity` caps above. It fails this fact on `assert released.available_token_capacity == 1000.0`, landing on `1800.0` — in a state (`used=0` against a full, never-consumed bucket) the processor cannot produce.
```

**Recommendation.** Retest, narrowed to the one measurement the fact actually owns.

1. Delete the `released` scenario entirely (`released.free_capacity(used=T(0,0), blocked=T(700,100))` and both of its assertions). It grades a ceiling cap on `free_capacity` that appears in no visible ticket, is contradicted by the natural reading of r2.rule, and describes a state the processor flow cannot reach. If you want release-caps-at-ceiling graded, state it in the open ticket next to "refill is capped above at the limit" and assert it in `test_open`, not here.

2. Delete the `settled` scenario. `settled.free_capacity(used=T(700,200), blocked=T(700,100))` -> `100.0`, counter `0` is the contrapositive of r1.observability's "increments by exactly one per call that clamped at least one axis" and cannot fail independently of it.

3. Keep only the refill scenario, and restate the fact to match: "the ceiling cap in `update_capacity` is not a debt clamp — a refill that saturates an axis at its limit leaves `num_capacity_debt_clamps` at `0`." That is the one thing a shared `_clamp(value, lo, hi)` implementation gets wrong.

4. Accept that even so this fact is gated behind r1.rule and r1.observability via `require_feature`, so it can never fail alone and it is a prohibition satisfied by inaction for any agent who puts the increment beside the floor. If the bracket needs facts that discriminate independently, this is the r1 sub-fact to cut rather than the one to keep — cutting it costs r1 nothing, since rule, scope and observability already carry the discriminating content.


## g10.r1.observability — retest

**Divergent action.** The informed agent declares `num_capacity_debt_clamps: int = 0` on `OnlineStatusTracker` and, in the shared floor helper called at the end of `consume_capacity`/`free_capacity`/`refund_capacity`, hoists the increment out of the per-axis loop: `floored_in = max(math.ceil(-lim.input * CAPACITY_DEBT_FLOOR_FRACTION), raw_in); floored_out = max(math.ceil(-lim.output * CAPACITY_DEBT_FLOOR_FRACTION), raw_out); if floored_in != raw_in or floored_out != raw_out: self.num_capacity_debt_clamps += 1` — one `+= 1` guarded by an `or` across axes, rather than an increment inside a `_floor_axis()` helper invoked once per axis. The blind agent writes neither the field nor any floor at all: the ticket's `free_capacity` is specified as "settles the token axes by `blocked - used`" with no lower bound and no counter anywhere in the tracker field list.

**The assertion.** `assert clamp_count(sep) == 1` — after `sep.free_capacity(used=T(input=2000, output=1000), blocked=T(input=700, output=100))` floors both axes in one call. Yes, it depends on more than this fact: it can only reach 1 if r1.rule's floor exists *and* is applied inside `free_capacity`, so an agent who adds a correct per-call counter but applies the floor only in `consume_capacity` reads 0 and fails this fact for a rule-fact error. The coupling is partial rather than total — a floor-at-zero implementation loses `rule` and `scope` yet still yields 1 then 2 here — so the fact does retain independent signal.

**Catalog A.** clean

**Catalog B.**
- `observable_belongs_to_another_fact` — The counter is also the entire content and sole observable of the sibling r1.exclusions_or_crossover — 'leave the clamp counter untouched', 'leaves the counter at `0`' — and `test_exclusions` gates on it: `require_feature(has_floor_constant() and has_clamp_counter(probe), "a capacity debt floor with a clamp counter")`. An agent who implements the debt floor correctly but adds no counter field loses two of r1's four facts on one omission. The test's own docstring concedes the sharing ('`exclusions` and `observability` read the counter') rather than resolving it.

**A correct build the test rejects:**

```
```python
def _apply_debt_floor(self) -> None:
    cap, lim = self.available_token_capacity, self.max_tokens_per_minute
    if cap is None or lim is None:
        return
    was_saturated = self._at_debt_floor          # set at the end of the previous call
    if isinstance(cap, _TokenUsage):
        fin = math.ceil(-lim.input * CAPACITY_DEBT_FLOOR_FRACTION)
        fout = math.ceil(-lim.output * CAPACITY_DEBT_FLOOR_FRACTION)
        now_saturated = cap.input < fin or cap.output < fout
        self.available_token_capacity = _TokenUsage(
            input=max(fin, cap.input), output=max(fout, cap.output)
        )
    else:
        floor = -lim * CAPACITY_DEBT_FLOOR_FRACTION
        now_saturated = cap < floor
        self.available_token_capacity = max(floor, cap)
    # a call "clamped" when it drove an axis into debt saturation; an axis already
    # resting on its floor is not clamped again by a further over-settlement
    if now_saturated and not was_saturated:
        self.num_capacity_debt_clamps += 1
    self._at_debt_floor = now_saturated
```
This satisfies the fact as written — "increments by exactly one per call that clamped at least one axis", one per call and not per axis, and the `seperate` double-floor case yields exactly 1 — and it matches the rule's framing that the floor is what happens when "a settlement discovers an under-estimate". It fails only the final assertion, `assert clamp_count(sep) == 2`, because the second settlement re-clamps axes that were already resting on `(-250, -125)`. Nothing in the fact statement says a re-clamp of an already-floored axis counts; the test grades that unstated semantic, and it is compounded by `blocked=T(input=0, output=0)` — a settlement of a reservation that was never made, a shape no path through `handle_single_request_with_retries` can produce.
```

**Recommendation.** Retest — keep the fact, fix the last assertion. (1) Make the second increment come from an unsaturated state instead of a re-clamp: insert `seed_full(sep)` (or build a second fresh `seperate` tracker) before the final settlement, and give it a real reservation — e.g. `sep.consume_capacity(T(input=700, output=100))` then `sep.free_capacity(used=T(input=5000, output=5000), blocked=T(input=700, output=100))` — so `clamp_count(sep) == 2` tests "a second clamping call is a second increment" without also deciding whether re-clamping an already-floored axis counts and without a `blocked=T(0,0)` settlement. If the intent really is that a re-clamp counts, say so in the fact text and in the clue; do not leave the test to legislate it. (2) Decouple the double-count with r1.exclusions_or_crossover: exclusions is gated on `has_clamp_counter`, so one missing field costs two facts. Either give exclusions an observable of its own (assert the capped values `1000.0` and the untouched `available_request_capacity` as its decider, with the counter as a secondary check) or fold exclusions' counter clauses into this fact. (3) Before shipping, confirm the clue states "one per call, not per axis" explicitly — the natural implementation increments inside the per-axis floor helper and returns 2, so without that wording an informed agent fails this fact on a coin flip.


## g10.r2.rule — retest

**Divergent action.** The informed agent adds a FOURTH tracker capacity operation and a SECOND processor delegate that the ticket's exhaustive API list does not contain:

```python
# OnlineStatusTracker
def refund_capacity(self, blocked: _TokenUsage) -> None:
    self.num_capacity_refunds += 1
    if self.available_request_capacity is not None:
        self.available_request_capacity = min(
            float(self.max_requests_per_minute),
            self.available_request_capacity + 1.0,
        )
    ...  # token axes gain the WHOLE blocked estimate, capped at the limit

# BaseOnlineRequestProcessor
def _refund_capacity(self, status_tracker, blocked_capacity) -> None:
    status_tracker.refund_capacity(blocked_capacity)
```
and calls `self._refund_capacity(status_tracker, token_estimate)` in the `except Exception` branch.

The blind agent writes, in that same branch, `self._free_capacity(status_tracker, _TokenUsage(input=0, output=0), token_estimate)` — full tokens back, `available_request_capacity` left at 59.0 — because the ticket says `free_capacity` "settles the token axes by `blocked - used`" and never mentions the request slot, while already demanding release on all three terminal paths. The concrete divergence is the `+ 1.0` on `available_request_capacity` and the separate method carrying it.

**The assertion.** `assert refunded.available_request_capacity == 60.0` — immediately after `refund_op(refunded)(T(input=600, output=200))`, contrasted against `assert settled.available_request_capacity == 59.0     # NOT 60.0`.

It depends on two things beyond this requirement. (1) The open ticket's `_reserve_capacity`/`consume_capacity` must decrement the request slot by exactly one, which the preceding `assert (refunded.available_request_capacity, refunded.available_token_capacity) == (59.0, 9200.0)` pins — that is open-feature behaviour, correctly a precondition rather than a confound. (2) More seriously, it is unreachable unless `refund_op` finds an attribute named `refund_capacity` or `refund`, since `refund_op` calls `pytest.fail` otherwise. So the gate is a name check first and the arithmetic second. It does not depend on any other HIDDEN requirement — not on r1's floor (no value goes negative), not on r2's counters.

**Catalog A.** clean

**Catalog B.** clean

**A correct build the test rejects:**

```
A fully correct implementation that the test rejects on naming alone — it takes the tracker name `refund_op` explicitly blesses, then names the processor delegate symmetrically:

```python
# OnlineStatusTracker — accepted by refund_op, which tries ("refund_capacity", "refund")
def refund(self, blocked: _TokenUsage) -> None:
    self.num_capacity_refunds += 1
    if self.available_request_capacity is not None:
        self.available_request_capacity = min(
            float(self.max_requests_per_minute), self.available_request_capacity + 1.0
        )
    if self.available_token_capacity is None:
        return
    if self.token_limit_strategy == TokenLimitStrategy.combined:
        self.available_token_capacity = min(
            float(self.max_tokens_per_minute),
            self.available_token_capacity + blocked.total,
        )
    else:
        self.available_token_capacity = _TokenUsage(
            input=min(self.max_tokens_per_minute.input,
                      self.available_token_capacity.input + blocked.input),
            output=min(self.max_tokens_per_minute.output,
                       self.available_token_capacity.output + blocked.output),
        )

# BaseOnlineRequestProcessor — mirrors free_capacity -> _free_capacity
def _refund(self, status_tracker: OnlineStatusTracker, blocked_capacity: _TokenUsage) -> None:
    status_tracker.refund(blocked_capacity)
```

Semantics are exactly the requirement: whole estimate back, capped; slot `+1.0`, capped; settlement untouched; counters separate; `None` axes skipped. `test_rule` passes its first two blocks and then dies with `AttributeError: 'StubProcessor' object has no attribute '_refund_capacity'` on the hardcoded `proc._refund_capacity(delegated, blocked)`. The test concedes on line one of `refund_op` that the exact identifier is not what this fact is about, then contradicts itself four lines later — it punishes the direct consequence of a choice it just permitted.
```

**Recommendation.** Retest — keep the fact, fix the naming asymmetry in the test. The fact discriminates for a real reason (the `+1.0` on the request slot is invisible in the ticket, and the contrary policy is the defensible instinct), and I could not build a blind implementation that passes it.

The single change: add a delegate helper mirroring `refund_op` and use it instead of the hardcoded attribute.

```python
def refund_delegate(proc):
    """The processor's failure release, which r2 names `_refund_capacity`."""
    for name in ("_refund_capacity", "_refund"):
        fn = getattr(proc, name, None)
        if callable(fn):
            return fn
    pytest.fail(
        f"{type(proc).__name__} has no refund delegate; the failure path cannot "
        "reach the tracker's refund"
    )
```

then in `test_rule`, replace `proc._refund_capacity(delegated, blocked)` with `refund_delegate(proc)(delegated, blocked)`. Either tolerate both names on both sides or neither — the current split is what fails a correct agent.

Two things I did not verify and would check before shipping. First, I had no repo access this session (Bash disabled, no file tools), so I could not confirm that nothing in the existing `handle_single_request_with_retries` already restores `available_request_capacity` on a retry; if it does, this fact collapses into `codebase_already_does_it` and becomes a cut. Second, confirm the world clue actually names `refund_capacity`/`_refund_capacity` rather than merely describing "give the slot back" — if it only describes the behaviour, the name gate is unfair even with the helper above, and `refund_op`'s synonym list should widen (`release_capacity`, `return_capacity`).


## g10.r2.scope — cut

**Divergent action.** None attributable to this field. The informed and the blind agent both place a release call at all three terminal sites, because the open ticket instructs it: "the reservation is released exactly once per attempt on **every** terminal path — the success path, the requeued-failure path and the exhausted-failure path — rather than only at line 584." The only code that diverges is which call goes there — `self._refund_capacity(status_tracker, token_estimate)` versus `self._free_capacity(status_tracker, used, token_estimate)` — and that is r2.rule's content, tested directly by `test_rule__a_refund_returns_the_whole_estimate_and_one_request_slot`, which asserts the same `60.0` / `10000.0` on the tracker with no coroutine involved.

**The assertion.** "assert requeued.available_request_capacity == 60.0" (the requeued branch is the only path not already covered by `test_rule` or by the exhausted case). Passing or failing it depends squarely on r2.rule: an agent whose `refund_capacity` returns the whole estimate and exactly 1.0 slot passes it automatically, because the ticket already told them to release on the requeued path; an agent whose release is a settlement fails it regardless of where they put the call. The assertion cannot separate "knew which paths" from "knew what a refund is."

**Catalog A.**
- `model_already_knows_it` — "Release the reservation on every exit path" is textbook cleanup discipline (finally/RAII/acquire-release symmetry). An agent reaches for a release at each `return` in an `except` branch from prior convention, not from a clue — especially once the ticket has enumerated the three paths.
- `ticket_gives_it_away` — Verbatim in the open ticket: "the reservation is released exactly once per attempt on **every** terminal path — the success path, the requeued-failure path and the exhausted-failure path". The fact's placement clause ("both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`). The success `else` path keeps the settlement at its current position") is a restatement of that sentence.
- `entailed_by_the_open_feature` — Given the ticket's every-terminal-path sentence plus r2.rule (the failure release is `_refund_capacity`), the placement in this fact is the only way to write it. A `finally`-based release is excluded because the success path must settle with the reported usage, so the refund cannot be shared; nothing is left for `scope` to decide.
- `obvious_implementation_does_it` — The natural implementation of the ticket sentence is one release statement immediately before each `return` in the `except` branch and the existing one in the `else`. That is exactly what the fact describes, arrived at by normal engineering.

**Catalog B.**
- `observable_belongs_to_another_fact` — The deciding numbers are r2.rule's. `test_rule` already asserts `refunded.available_request_capacity == 60.0` and `refunded.available_token_capacity == 10000.0` straight on the tracker, and asserts the settlement leaves `59.0  # NOT 60.0`. `scope` re-reads the same channel one layer up; an agent who gets rule wrong fails scope, and an agent who gets rule right passes scope for free because the ticket dictated the placement.
- `no_independent_content` — scope = (the ticket's "every terminal path" sentence) + (r2.rule's refund semantics). Subtract those two and nothing remains. There is no implementation that satisfies the ticket and rule yet fails scope, and none that fails rule yet passes scope.

**A blind build that passes anyway:**

```
"# ticket only: `free_capacity` settles token axes by `blocked - used`, and the ticket says\n# to release on every terminal path. The attempt failed, so nothing was spent; and the\n# requeued request goes back to `retry_queue` where the loop at 432-439 will reserve a\n# fresh slot, so hand this one back or we double-count it.\ndef _release_failed_attempt(self, status_tracker, blocked_capacity):\n    self._free_capacity(status_tracker, _TokenUsage(input=0, output=0), blocked_capacity)\n    if status_tracker.available_request_capacity is not None:\n        status_tracker.available_request_capacity = min(\n            float(status_tracker.max_requests_per_minute),\n            status_tracker.available_request_capacity + 1.0,\n        )\n\n# ... in handle_single_request_with_retries:\nexcept Exception as e:\n    status_tracker.num_other_errors += 1\n    if request.attempts_left > 0:\n        request.attempts_left -= 1\n        self._release_failed_attempt(status_tracker, token_estimate)\n        await retry_queue.put(request)\n        return\n    else:\n        logger.error(...)\n        self._release_failed_attempt(status_tracker, token_estimate)\n        await append_generic_response(...)\n        return\nelse:\n    # unchanged success settlement at its current position\n    self._free_capacity(status_tracker, generic_response.token_usage, token_estimate)\n\n# scope test outcome: exhausted -> 60.0 / 10000.0, requeued -> 60.0 / 10000.0,\n# success -> 59.0 / 9200.0. All three assertions pass with no refund_capacity anywhere."
```

**Recommendation.** Cut r2.scope as a separately graded fact and fold `test_scope__both_failure_exits_refund_while_the_success_exit_settles` into r2.rule's test as its end-to-end arm — that is what it actually measures. Two reasons, either sufficient: (1) the open ticket states the fact almost word for word ("released exactly once per attempt on **every** terminal path — the success path, the requeued-failure path and the exhausted-failure path"), so there is no divergent action left for a clue to cause; (2) the `used=_TokenUsage(0, 0)` blind release above passes the whole scope test without ever knowing a refund is a distinct operation, so the free bracket's single blind sample understates the pass rate. If the requirement must keep a `scope` field, it has to assert something the ticket does not already say and rule does not already number — e.g. that the refund fires before `await retry_queue.put(request)` rather than after, observed by a tracker whose `refund_capacity` is instrumented to record the queue depth at call time — and even then check it is not just rule's observable again. Also worth fixing while you are in here: `run_attempt(proc, tracker, blocked, ...)` pins `handle_single_request_with_retries` to receiving the estimate as a parameter; keep that helper in the visible `test_open` so the agent can conform, as it currently is.


## g10.r2.exclusions_or_crossover — cut

**Divergent action.** On the `except Exception` branch of `handle_single_request_with_retries`, the informed agent writes `self._refund_capacity(status_tracker, token_estimate)` and never mentions `generic_response.token_usage`; the blind agent writes `self._free_capacity(status_tracker, generic_response.token_usage, token_estimate)`. But that is the divergent action of the sibling `rule`/`scope`, not of this fact: once `_refund_capacity(self, status_tracker, blocked_capacity)` exists as `rule` specifies, there is no parameter through which usage could be consulted, so "ignores token_usage" names no code of its own. Its own subject — HOW MUCH comes back on the token axis — is written identically by an agent who never saw any clue and passes `used=_TokenUsage()` on the failure path.

**The assertion.** `assert t.available_token_capacity == 10000.0` (the fact's own subject; the companion `assert t.available_request_capacity == 60.0` is rule's and scope's observable). Yes, it depends on more than this requirement: it is satisfied by any release on the failure path whose `used` is zero or absent — i.e. by an implementation that has no refund concept at all — and it also depends on `_reserve_capacity`/`consume_capacity` from the open ticket and on the refund's cap-at-limit from `rule`. The only assertion in this test that fails a plausible wrong implementation is the request-slot one, which belongs to `rule` and `scope`.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The fact is a prohibition — "ignores `generic_response.token_usage` even when the failed response carried one". Honouring it is pure inaction: not reading a field. Reading it is the extra work, and in the `except Exception` branch it is *awkward* extra work, since `generic_response` can be unbound when the exception came from `call_single_request`. The rule never tests restraint; it tests that the agent didn't go out of its way.
- `model_already_knows_it` — Reserve/commit/rollback is a published convention: a rollback returns the reservation, not the observed spend. An agent with no clue at all, asked to release a reservation after a failure, reaches for "give back what I took" from prior knowledge.
- `obvious_implementation_does_it` — The most natural failure-path release is `self._free_capacity(status_tracker, _TokenUsage(input=0, output=0), token_estimate)` — because a raised exception leaves no reliable usage in scope. On the token axis that is arithmetically identical to refunding the estimate: 9000 + 1000 = 10000.0. The obvious implementation passes the assertion this fact is about.

**Catalog B.**
- `observable_belongs_to_another_fact` — The test's decisive assertion is `assert t.available_request_capacity == 60.0`, which is `rule`'s ("59.0 vs 60.0", "assert settled.available_request_capacity == 59.0  # NOT 60.0") and `scope`'s ("either failure path ends at `available_request_capacity == 60.0`") observable, asserted verbatim in both sibling tests. The token assertion this fact owns is passed by any zero-used settlement, so grading this fact really re-grades rule/scope.
- `no_independent_content` — `rule` already fixes the failure release as "`_refund_capacity(self, status_tracker, blocked_capacity)`, which delegates to `status_tracker.refund_capacity(blocked_capacity)`". That signature has no `used`/`token_usage` parameter, so an implementation that satisfies `rule` cannot fail `exclusions`. The fact restates half of its neighbour.

**A blind build that passes anyway:**

```
```python
# BaseOnlineRequestProcessor.handle_single_request_with_retries, ticket-only agent
except Exception as e:
    logger.warning(f"Request {request.task_id} failed: {e}")
    # the attempt blew up; we have no trustworthy usage for it (generic_response
    # may not even be bound here), so nothing was used and the whole
    # reservation goes back
    self._free_capacity(status_tracker, _TokenUsage(input=0, output=0), token_estimate)
    if request.attempts_left > 0:
        request.attempts_left -= 1
        retry_queue.put_nowait(request)
        return
    ...
```
This agent never heard of a refund, never reads `generic_response.token_usage`, and lands on `available_token_capacity == 10000.0` — the assertion this fact is actually about. It fails only `available_request_capacity == 60.0`, which is `rule`/`scope`'s observable, not this fact's.
```

**Recommendation.** Cut `r2.exclusions_or_crossover`. It cannot be repaired by re-testing: on the token axis, "refund the whole blocked estimate" and "settle with `used = 0`" are the same arithmetic for every choice of numbers, so no assertion on `available_token_capacity` can ever separate this fact from an agent who simply had no usage in hand on the `except` path. The only separating axis is `available_request_capacity`, which `rule` and `scope` already assert verbatim, and `rule`'s `_refund_capacity(self, status_tracker, blocked_capacity)` signature already forecloses consulting `token_usage`. Keep `rule`, `scope` and `observability` as the three facts of r2 and let `scope`'s failed responses keep their `token_usage`. If r2 needs a fourth fact, give it its own observable rather than a restatement — e.g. the crossover with r1: a failure whose reported usage would drive an axis below `-CAPACITY_DEBT_FLOOR_FRACTION * limit` leaves `num_capacity_debt_clamps == 0` because the refund never looks at that usage, which no zero-used settlement reproduces.


## g10.r2.observability — retest

**Divergent action.** Two new dataclass fields on `OnlineStatusTracker` — `num_capacity_settlements: int = 0` and `num_capacity_refunds: int = 0` — plus one increment each, placed as the *first* statement of its own method, ahead of the `None` short-circuit:

```python
def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage) -> None:
    self.num_capacity_settlements += 1          # before any `is None` guard
    if self.available_token_capacity is None:
        return
    ...

def refund_capacity(self, blocked: _TokenUsage) -> None:
    self.num_capacity_refunds += 1              # before any `is None` guard
    if self.available_request_capacity is not None:
        self.available_request_capacity = min(...)
    ...
```

The part of that which belongs to *this* field rather than to r2.rule is only the two `int = 0` declarations and the placement of the increments above the guards. Note that the second half of the divergence — `refund_capacity` existing at all — is r2.rule's content, and it is what the blind agent actually misses.

**The assertion.** `assert (settlements(unlimited), refunds(unlimited)) == (1, 1)` — the only assertion that is not implied by 'a rule-correct agent added two counters'. Yes, its pass/fail depends on something other than this field: the preceding `require_feature(has_refund(settled), ...)` and `refund_op(unlimited)` mean the whole test is gated on r2.rule's `refund_capacity` existing, and a ticket-only agent dies there — so the bracket's 'blind fails' is r2.rule's signal, not this field's. The earliest counter assertion, `assert (settlements(settled), refunds(settled)) == (0, 0)`, is likewise reached only after that gate.

**Catalog A.**
- `obvious_implementation_does_it` — Partially, and for the clause that matters. Once a rule-informed agent writes `refund_capacity`, the tracker it lives in is already dense with `num_*` counters (`num_tasks_started`, `num_rate_limit_errors`), and `read_field` accepts the loose aliases `num_settlements`, `num_capacity_frees`, `num_refunds`. More sharply: the distinguishing clause 'both counters still increment when the affected capacity is `None`' is satisfied for free by the single most natural placement — `self.num_capacity_settlements += 1` as the first line of the method. The test cannot distinguish 'read the clue about no-ops' from 'wrote the increment at the top like everyone does'.

**Catalog B.** clean

**A correct build the test rejects:**

```
```python
def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage) -> None:
    if self.available_token_capacity is None:      # unlimited: nothing to settle
        return
    self.num_capacity_settlements += 1
    ...

def refund_capacity(self, blocked: _TokenUsage) -> None:
    if self.available_token_capacity is None and self.available_request_capacity is None:
        return
    self.num_capacity_refunds += 1
    ...
```
An agent that has correctly derived 'settlement and refund are two operations, count them separately' and is also honouring the *open ticket's* rule that 'An axis whose capacity is `None` is read, skipped and left `None` by all of these' guards first and counts second. Every other assertion in the test passes; it dies only on `assert (settlements(unlimited), refunds(unlimited)) == (1, 1)`. Whether this is overshoot turns entirely on whether the clue states the no-op clause — the fact's text does, but the agent only ever sees the clue.
```

**Recommendation.** Retest, three concrete changes.

1. **Stop the field borrowing its signal from r2.rule.** Split `test_observability__...` in two. The first test must not mention the refund at all: construct `tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)`, `consume_capacity`, assert `settlements(t) == 0`, `free_capacity(used=..., blocked=...)`, assert `settlements(t) == 1` — no `require_feature`, no `refund_op`. Move the `require_feature(has_refund(...))` gate and the `(0, 1)` / `(1, 1)` blocks into the second test. Then a rule-correct-but-counter-blind agent fails the first test on the counter itself rather than on the missing method.

2. **Re-run the blind bracket with the right control.** The recorded 'blind fails' does not support this field. Run the bracket against an implementation that has a full, correct `refund_capacity` (r2.rule satisfied) and *no* counters, and confirm `g10.r2.observability` still fails while `g10.r2.rule` passes. Also confirm how `harness.require_feature` scores a missing feature — if it skips and a skip is booked as a fail, this field is inheriting r2.rule's discrimination outright.

3. **Back the no-op clause with the clue, or drop it.** `assert (settlements(unlimited), refunds(unlimited)) == (1, 1)` is the only assertion in the test that a counter-adding agent does not get for free, and it is the one that rejects the guard-then-count implementation quoted in `correct_fail` — an implementation the open ticket's own 'read, skipped and left `None`' sentence encourages. Check that the r2 clue says in so many words that the counter ticks even when the release moves nothing; if it does not, delete the `unlimited` block and accept that the field's remaining content is the `(1, 0)` / `(0, 1)` separation.
