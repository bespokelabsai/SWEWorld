# g10 — the requirement, reduced to what is graded

**533 words → 376** across 8 facts and 52 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g10.r1.rule` | 93 → 59 | 3 | 4 |
| `g10.r1.scope` | 73 → 50 | 9 | 2 |
| `g10.r1.exclusions_or_crossover` | 62 → 52 | 7 | 1 |
| `g10.r1.observability` | 43 → 19 | 4 | 3 |
| `g10.r2.rule` | 76 → 53 | 10 | 4 |
| `g10.r2.scope` | 81 → 66 | 8 | 2 |
| `g10.r2.exclusions_or_crossover` | 43 → 32 | 4 | 2 |
| `g10.r2.observability` | 62 → 45 | 7 | 1 |

## `g10.r1.rule`

**Now (59 words):**

Token capacity may go negative, but each axis is floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` with `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25` exported from the capacity-budget module. The floor is `-limit * 0.25` as a `float` for the `combined` axis. Worked case: a tracker with `max_tokens_per_minute=1_000`, after `consume_capacity(_TokenUsage(input=700, output=100))` and then settling `used=_TokenUsage(input=1000, output=500)` against `blocked=_TokenUsage(input=700, output=100)`, ends at `available_token_capacity == -250.0`.

**Dropped, because no assertion checks it:**

- "when a settlement discovers an under-estimate" — the why behind going negative. No assertion reads it, and "settling" survives inside the worked case anyway.
- "and `math.ceil(-limit * 0.25)` (an `int`) for each `seperate` axis" — all three assertions read the combined axis (`available_token_capacity`, values `200.0` and `-250.0`); nothing checks a separate axis or its int rounding.
- ", and it is applied at the end of `consume_capacity` and of both release operations" — placement restated in prose. The worked case already pins the settlement path, and the `200.0` result never reaches a floor, so no assertion turns on the consume-side or second-release application.
- "(not `-700.0`, not `0.0`)" — the same rule said again by negation; the `-250.0` literal already carries it.

**Kept despite looking like padding:** The whole worked case reads like padding but stays verbatim. `max_tokens_per_minute=1_000` with `consume_capacity(_TokenUsage(input=700, output=100))` is the only thing that makes assertion #2's `200.0` derivable, and the exact `used=`/`blocked=` literals plus `-250.0` are what assertion #3 turns on. `CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25` and its export are held by assertion #1; `-limit * 0.25` as a `float` for `combined` is held by the float-valued results in #2 and #3.

## `g10.r1.scope`

**Now (50 words):**

A tracker constructed with `max_tokens_per_minute=0` (defaulted to 100_000) floors at `-25000.0`, and under `seperate` each axis floors against its own limit: with `_TokenUsage(input=1_000, output=500)` an over-settled tracker lands on `_TokenUsage(input=-250, output=-125, total=-375)`. An axis whose limit and capacity are `None` has no floor and stays `None`. `available_request_capacity` is never floored.

**Dropped, because no assertion checks it:**

- The opening mechanism clause: 'The floor is computed from the tracker's *effective* per-minute limit after `__post_init__` normalisation, so' — it says why the floor lands where it does. No assertion checks the derivation: #1 checks `max_tokens_per_minute == 100_000` and #3 checks the literal `-25000.0`, and both still appear verbatim in the surviving text.
- The trailing reason clause: 'because it is only decremented after a successful `has_capacity`' — why the request bucket has no floor. #8 and #9 assert only `available_request_capacity == 59.0`; the rule ('is never floored') survives, its justification does not.

**Kept despite looking like padding:** Both worked examples stayed — they are not one rule restated. The `max_tokens_per_minute=0` example is the only source of `100_000` (#1) and `-25000.0` (#3); the `_TokenUsage(input=1_000, output=500)` example is the only source of `(-250, -125, -375)` (#5) and carries the misspelled mode name `seperate`, which an implementer needs verbatim to build the `sep` tracker read by #4, #5 and #9. The `None`-axis sentence reads like a footnote but is the sole basis for #6 and #7.

## `g10.r1.exclusions_or_crossover`

**Now (52 words):**

The refill in `update_capacity` capping an axis at its limit, and a release capping an axis at its limit, leave the clamp counter untouched. Only the lower debt floor counts — a settlement whose result stays above the floor (e.g. `available_token_capacity == 100.0` on a 1_000-token tracker) leaves the counter at `0`.

**Dropped, because no assertion checks it:**

- The upper cap is not a clamp for counting purposes: — an abstract restatement of the concrete rule that follows the colon. The surviving clause already says refill-at-limit and release-at-limit leave the clamp counter untouched, which is what assertions #3 and #5 grade; no assertion reads the general phrasing.

**Kept despite looking like padding:** 'and a release capping an axis at its limit' reads like a second example of the refill rule, but assertion #5 (clamp_count(released) == 0) grades release as a path separate from refill's #3, so it stays. 'Only the lower debt floor counts' sits close to the deleted preamble, but it is the only introduction of 'the floor' that the settlement clause refers back to, and assertion #7 turns on that floor rule. The parenthetical `available_token_capacity == 100.0` on a 1_000-token tracker is the one worked example whose literal an assertion reads (#6).

## `g10.r1.observability`

**Now (19 words):**

A tracker field `num_capacity_debt_clamps: int = 0` increments by exactly one per call that clamped at least one axis.

**Dropped, because no assertion checks it:**

- "one increment per call, not per axis" — a restatement of the preceding clause "increments by exactly one per call that clamped at least one axis" in different words for emphasis; the surviving clause already fixes the per-call granularity that makes assertion #3 yield 1.
- "so the `seperate` case above yields `num_capacity_debt_clamps == 1`" — a "so" clause carrying a worked example that demonstrates the already-stated rule; no assertion turns on a literal here, it just re-reads the counter the rule defines.
- "even though both axes hit their floors" — the justification for that example, explaining why the count is 1 rather than 2. A reason is never asserted.

**Kept despite looking like padding:** `num_capacity_debt_clamps: int = 0` is kept verbatim, including the `= 0` default, because assertions #1 and #2 both check `clamp_count(sep) == 0` before anything clamps — the starting value is graded, not decoration. \"exactly one per call that clamped at least one axis\" reads like it could collapse to \"increments per clamping call\", but assertion #3 (`== 1`) is only distinguishable from a per-axis counter by the words \"exactly one per call\" and \"at least one axis\", and assertion #4 (`== 2`) needs the increment to be repeatable across calls.

## `g10.r2.rule`

**Now (53 words):**

`free_capacity(used, blocked)`: the token axes gain `blocked - used` and `available_request_capacity` is left exactly as `consume_capacity` left it. `refund_capacity(blocked: _TokenUsage) -> None`: the token axes gain the whole `blocked` estimate back (capped above at the limit) and `available_request_capacity` gains exactly `1.0`, capped above at `max_requests_per_minute`. The processor's `_refund_capacity(self, status_tracker, blocked_capacity)` delegates to `status_tracker.refund_capacity(blocked_capacity)`.

**Dropped, because no assertion checks it:**

- Opening framing sentence: "Releasing a reservation is two distinct tracker operations, not one." - a restatement of the fact that two separately specified methods follow; nothing asserts the count or the distinctness.
- The label "is a *settlement*" on free_capacity - a name for the behavior, not the behavior; only the clause after the colon is graded (#6, #7).
- "A second method" and the label "is a *refund*" on refund_capacity - ordering commentary plus another behavior label; no assertion turns on either.
- "failure release is" and the connective "which" in the last sentence - this states the occasion on which the processor calls the method; the assertions call it directly and only check that it delegates (#8-#10).

**Kept despite looking like padding:** "is left exactly as `consume_capacity` left it" reads like prose but is the only thing forcing #7 (settled.available_request_capacity == 59.0, NOT 60.0). The two caps - "(capped above at the limit)" and "capped above at `max_requests_per_minute`" - look like caveats but are exactly what #3/#5 (10000.0) and #2/#4 (60.0) grade. The full parameter list in `_refund_capacity(self, status_tracker, blocked_capacity)` and the exact delegated call `status_tracker.refund_capacity(blocked_capacity)` are held by #8-#10, so neither can be shortened to a description.

## `g10.r2.scope`

**Now (66 words):**

Every terminal path through the `except Exception` branch of `handle_single_request_with_retries` calls the refund — both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`). On a tracker with `max_requests_per_minute=60`, `max_tokens_per_minute=10_000` and a reservation of `_TokenUsage(input=700, output=300)`, either failure path ends at `available_request_capacity == 60.0` and `available_token_capacity == 10000.0`, while the success path with reported usage `_TokenUsage(input=700, output=100)` ends at `59.0` / `9200.0`.

**Dropped, because no assertion checks it:**

- "immediately before its `return`" — statement-placement detail inside the branch. No assertion reads where in the branch the refund sits, only the end-state capacities 60.0 / 10000.0 that both failure paths finish at.
- "The success `else` path keeps the settlement at its current position." — a restatement of success behaviour the worked example already pins numerically. Assertions #7 and #8 turn on the literals `59.0` and `9200.0`, which the surviving example still states together with the reservation `_TokenUsage(input=700, output=300)` and reported usage `_TokenUsage(input=700, output=100)` they follow from.

**Kept despite looking like padding:** The em-dash enumeration "both the requeued case (`attempts_left > 0`) and the exhausted case (`attempts_left == 0`)" reads as elaboration on "every terminal path", but it had to stay: #4 reads `attempts_left` by name and value, and #2/#3 (exhausted) versus #5/#6 (requeued) grade the two failure branches separately, so "either failure path" in the example needs both branches named to be unambiguous. The limits `max_requests_per_minute=60` / `max_tokens_per_minute=10_000` and the reservation also look like scene-setting, but they are what makes #1's `(59.0, 9000.0)` reachable.

## `g10.r2.exclusions_or_crossover`

**Now (32 words):**

The failure refund uses the full blocked estimate and ignores `generic_response.token_usage` — e.g. a response with `finish_reason="length"` (in `config.invalid_finish_reasons`) reporting `_TokenUsage(input=900, output=800)` against a blocked estimate of `_TokenUsage(input=900, output=100)` returns the estimate.

**Dropped, because no assertion checks it:**

- "even when the failed response carried one" — a restatement of "ignores `generic_response.token_usage`". No assertion reads whether the failed response carried a usage; #3 and #4 only check that the estimate comes back whole (10000.0, 60.0).
- ", not the reported spend" — the same rule a third time for emphasis. The example already ends with "returns the estimate", and nothing checks the negative form.

**Kept despite looking like padding:** "(in `config.invalid_finish_reasons`)" reads like a gloss but is the mechanism that makes `finish_reason=\"length\"` a failure at all — assertions #3 and #4 fire only on the failure path, so an implementer who does not treat invalid finish reasons as failures never refunds and lands on 8300.0/59.0 instead of 10000.0/60.0. The `_TokenUsage(input=900, output=800)` clause also had to stay: it is the single worked example, and its 900+800 is the 1700 that assertion #3's comment contrasts against. `_TokenUsage(input=900, output=100)` is read directly by assertion #1 as (900, 100, 1000).

## `g10.r2.observability`

**Now (45 words):**

Two tracker counters, `num_capacity_settlements: int = 0` and `num_capacity_refunds: int = 0`, each incremented by exactly one by its own operation and by neither the other's. Both counters still increment when the affected capacity is `None` and the operation is a no-op on every axis.

**Dropped, because no assertion checks it:**

- The worked example restating the increment rule in different words: "— a failed attempt gives `num_capacity_refunds == 1`, `num_capacity_settlements == 0`, and a successful one the reverse". The clause before it — "each incremented by exactly one by its own operation and by neither the other's" — already pins assertion #3 (1, 0) and assertion #4 (0, 1); the example only says the same rule twice more, once per direction.

**Kept despite looking like padding:** "and the operation is a no-op on every axis" reads like colour on the `None` case, but assertions #6 and #7 read `unlimited.available_token_capacity is None` and `unlimited.available_request_capacity is None` after both operations have run, so that clause is what stops an implementer mutating one of the two axes. `int = 0` on both names stays for assertions #1 and #2, which read the counters at (0, 0).
