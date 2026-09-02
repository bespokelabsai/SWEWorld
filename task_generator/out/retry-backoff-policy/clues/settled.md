# Was every graded thing said, or only implied? — g3

**76 of 97** assertions rest on something a remark says outright.

- `stated` **76** — a reader was told
- `implied` **18** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **3** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 11 remark(s) rewritten, 7 added, 0 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g3.r1.exclusions_or_crossover#1` | stated | `g3.r1.l13`, `g3.r1.l12` | l13 says a bad key gives terminal:abort with "attempts to zero, passes untouched", naming the label, the zeroing and the waiver pass-through outright. |
| `g3.r1.exclusions_or_crossover#2` | stated | `g3.r1.l15`, `g3.r1.rev1`, `g3.r1.l8` | l15 pins "429 at attempts_left=0 with throttle_waivers_left=3 still re-queues and comes back 2" and rev1 makes a 429 free while waivers remain, so retry, the unchanged 0 budget and the waiver decremen |
| `g3.r1.exclusions_or_crossover#3` | stated | `g3.r1.l15`, `g3.r1.rev1`, `g3.r1.l8`, `g3.r1.l17` | l15's "and at 0 it's throttle:exhausted" states the stop and the label verbatim, with rev1/l8 for the charge once passes are spent and l17 for flooring the reported attempts_left at zero. |
| `g3.r1.failure_behavior#1` | **implied** | `g3.r1.l16`, `g3.r1.l2`, `g3.r1.l15` | l2 fixes the contract cost at two and l16 says the cost must be charged before the budget is tested, but nobody says that landing on exactly zero remaining is still a retry — the reader must choose `< |
| `g3.r1.failure_behavior#2` | stated | `g3.r1.l16`, `g3.r1.l2`, `g3.r1.l15`, `g3.r1.l17` | l16 names this exact scenario — a malformed-output failure with one attempt left getting "a retry it can't pay for" — as the bug to fix, l2 sets that cost at two, and l15 supplies the `category:exhaus |
| `g3.r1.failure_behavior#3` | stated | `g3.r1.l17` | nils says the verdict logged attempts_left as -1 and that whatever number is handed back there has to floor at zero, which is exactly the verdict field this asserts on. |
| `g3.r1.failure_behavior#4` | stated | `g3.r1.l19`, `g3.r1.l18` | l19 decides outright that if the verdict isn't a retry the delay should just be 0.0. |
| `g3.r1.failure_behavior#5` | stated | `g3.r1.l19`, `g3.r1.l18` | l19 says explicitly not to read the schedule or pull from the jitter source for a non-retry verdict, after l18 reports drawing jitter for requests already binned. |
| `g3.r1.failure_behavior#6` | **implied** | `g3.r1.l3`, `g3.r1.l15`, `g3.r1.l17`, `g3.r1.l16` | l3 pins the transient cost at one and l15 gives the `exhausted` outcome for the throttle path, but no remark says a transient failure with a spent budget yields `transient:exhausted` with attempts flo |
| `g3.r1.failure_behavior#7` | stated | `g3.r1.l19` | l19's rule is stated for any verdict that isn't a retry, which covers the exhausted transient as much as the exhausted contract. |
| `g3.r1.failure_behavior#8` | stated | `g3.r1.l19`, `g3.r1.l18` | the same l19 decision forbids drawing from the jitter source on any non-retry verdict, so the transient case is told, not inferred. |
| `g3.r1.observability#1` | stated | `g3.r1.l5`, `g3.r1.rev2` | l5 names the constant, the value 6, and that it is the module default living in retry_policy.py. |
| `g3.r1.observability#10` | stated | `g3.r1.l2`, `g3.r1.l1` | l2 states two attempts off for a malformed-output failure and l1 ties finish_reason length to that class, so 3 becomes 1. |
| `g3.r1.observability#11` | stated | `g3.r1.l16`, `g3.r1.l2` | l16 names this exact case — malformed-output failure with one attempt left — and calls the retry it currently gets one it can't pay for. |
| `g3.r1.observability#12` | **implied** | `g3.r1.l15`, `g3.r1.h2`, `g3.r1.l13` | Nobody writes contract:exhausted; the reader must compose it by extending the throttle:exhausted pattern onto the CONTRACT category named only in passing. |
| `g3.r1.observability#13` | stated | `g3.r1.l17` | l17 is a decision made out loud that the verdict's attempts_left floors at zero instead of logging -1. |
| `g3.r1.observability#14` | stated | `g3.r1.l13` | l13 gives the literal string terminal:abort for an invalid api key. |
| `g3.r1.observability#15` | stated | `g3.r1.l13`, `g3.r1.l12` | l13 says attempts go to zero on a bad key, and l12 confirms the attempts on the clock are worth nothing once auth is the problem. |
| `g3.r1.observability#16` | stated | `g3.r1.l13` | l13 says the passes are untouched at six in this exact scenario. |
| `g3.r1.observability#2` | stated | `g3.r1.l5`, `g3.r1.l6`, `g3.r1.l7`, `g3.r1.rev2` | l5 says the constant seeds throttle_waivers_left on every request, l6 says the field hangs off APIRequest, and l7 says each request walks in with its own full set. |
| `g3.r1.observability#3` | stated | `g3.r1.rev1`, `g3.r1.l15` | rev1 states a 429 is free while throttle_waivers_left > 0, so a healthy-budget throttle leaves attempts_left untouched at 3. |
| `g3.r1.observability#4` | stated | `g3.r1.l15`, `g3.r1.l8`, `g3.r1.rev2` | l15 states the waiver decrement by one on a 429 (3 comes back 2) and rev2 says decide reports throttle_waivers_after, so 6 goes to 5 under the same rule. |
| `g3.r1.observability#5` | stated | `g3.r1.l15` | l15 pins this case verbatim: 429 at attempts_left=0 with throttle_waivers_left=3 still re-queues. |
| `g3.r1.observability#6` | stated | `g3.r1.l15` | l15 says it comes back 2, for exactly this input. |
| `g3.r1.observability#7` | stated | `g3.r1.l15`, `g3.r1.rev1`, `g3.r1.l8` | l15's "at 0 it's throttle:exhausted" is a non-retry verdict, and rev1/l8 explain that with waivers gone the 429 charges an attempt there is none of. |
| `g3.r1.observability#8` | stated | `g3.r1.l15` | l15 gives the literal reason string throttle:exhausted. |
| `g3.r1.observability#9` | stated | `g3.r1.l17`, `g3.r1.rev1` | l17 states the decision that the attempts_left handed back in the verdict floors at zero rather than going negative. |
| `g3.r1.rule#1` | stated | `g3.r1.l5`, `g3.r1.rev2` | l5 names the constant, its value 6, and calls it the module default in the same sentence that places the retry machinery in retry_policy.py, and rev2 repeats "DEFAULT_THROTTLE_WAIVERS = 6". |
| `g3.r1.rule#10` | stated | `g3.r1.rev1`, `g3.r1.l8` | rev1 says decide charges 1 once the waivers are gone and l8 says the next 429 costs an attempt like anything else, still retrying rather than aborting. |
| `g3.r1.rule#2` | stated | `g3.r1.l6`, `g3.r1.rev2` | l6 corrects the spelling to throttle_waivers_left and says explicitly that it hangs off APIRequest and not the tracker. |
| `g3.r1.rule#3` | stated | `g3.r1.l5`, `g3.r1.l7` | l5 says DEFAULT_THROTTLE_WAIVERS seeds throttle_waivers_left on every request, and l7 insists each request walks in with its own full set. |
| `g3.r1.rule#4` | stated | `g3.r1.l9`, `g3.r1.rev2` | l9 names attempts_made and attempts_left as what decide already sees and says the remaining passes must go in as a third kwarg; rev2 confirms decide takes throttle_waivers_left. |
| `g3.r1.rule#5` | stated | `g3.r1.l3`, `g3.r1.h2` | l3 decides out loud that timeouts stay at one attempt off the budget per failure. |
| `g3.r1.rule#6` | **implied** | `g3.r1.rev1`, `g3.r1.l13`, `g3.r1.h2` | Remarks say a throttle spends a waiver and a terminal leaves the passes untouched, but nobody states that a transient failure leaves the waiver count alone — the reader must infer that only THROTTLE m |
| `g3.r1.rule#7` | stated | `g3.r1.l2`, `g3.r1.l1` | l2 settles on two attempts off for a malformed-output failure, explicitly rejecting one and rejecting binning outright, answering l1's complaint. |
| `g3.r1.rule#8` | **implied** | `g3.r1.l13`, `g3.r1.l2`, `g3.r1.rev1` | The two-attempt cost is stated but nothing says a CONTRACT failure leaves throttle_waivers_left unchanged; the reader has to generalise from l13's terminal case that only 429s spend passes. |
| `g3.r1.rule#9` | stated | `g3.r1.l15`, `g3.r1.rev1`, `g3.r1.l14` | l15 pins the exact case — a 429 with throttle_waivers_left=3 re-queues and comes back with 2, budget untouched — and rev1 says 429 is free while waivers remain, with l15's "throttle:exhausted" fixing  |
| `g3.r1.scope#1` | stated | `g3.r1.l7`, `g3.r1.rev2`, `g3.r1.l5` | konrad's l7 says a shared per-run counter is wrong and "each request should walk in with its own full set", and rev2/l5 fix that set at six seeded on every request. |
| `g3.r1.scope#2` | stated | `g3.r1.rev1`, `g3.r1.l15`, `g3.r1.l10`, `g3.r1.rev2` | rev1 and l15 commit to a 429 spending one waiver while any remain (3 comes back 2), and l10 names the missing write-back of the pass count onto the request as the bug, so six absorbed 429s leave the f |
| `g3.r1.scope#3` | stated | `g3.r1.rev2`, `g3.r1.l9`, `g3.r1.l15` | rev2 says decide takes throttle_waivers_left and reports throttle_waivers_after, l9 says the remaining passes come in as a third kwarg, and l15 pins the decrement (3 in, 2 back), so 6 in yields 5. |
| `g3.r1.scope#4` | stated | `g3.r1.rev1`, `g3.r1.l15`, `g3.r1.h1` | rev1 states outright that a 429 is free while throttle_waivers_left > 0, so the attempt budget handed in comes back unchanged. |
| `g3.r1.scope#5` | stated | `g3.r1.l6` | gideon's l6 says the count hangs off APIRequest and "the tracker has no buisness knowing about it". |
| `g3.r1.scope#6` | stated | `g3.r1.l6` | same remark rules the tracker out of holding the waiver count at all, which covers instance attributes as well as declared fields. |
| `g3.r1.scope#7` | stated | `g3.r1.l11` | dario's l11 says he'd rather not put a new knob on OnlineRequestProcessorConfig for this and that everything else stays on the request. |
| `g3.r1.scope#8` | stated | `g3.r1.l11` | l11's "max_retries still seeds attempts_left" tells the reader the caller-supplied seeding is unchanged, so the field is left without a default; the literal absence of a default/default_factory is nev |
| `g3.r1.scope#9` | stated | `g3.r1.l11` | l11 says in as many words that max_retries still seeds attempts_left. |
| `g3.r2.exclusions_or_crossover#1` | stated | `g3.r2.s4d` | Nikolai says outright that the knob "stays in config.py even once nothing reads it," which is the decision to leave the field declared. |
| `g3.r2.exclusions_or_crossover#2` | **implied** | `g3.r2.s4a`, `g3.r2.s4d` | The only "ten" in the corpus is gideon's complaint about a ten-second pause, a value attached to the pause and not to this field's default, so the reader is left to connect the two (or simply not touc |
| `g3.r2.exclusions_or_crossover#3` | stated | `g3.r2.s4d` | "A few user configs in the wild still set seconds_to_pause_on_rate_limit" says the field must remain accepted from user config. |
| `g3.r2.exclusions_or_crossover#4` | **implied** | `g3.r2.s4a`, `g3.r2.s4d` | Same gap as #2: the default of 10 on the processor's config is nowhere attached to the field name, only to the old flat pause gideon complained about. |
| `g3.r2.exclusions_or_crossover#5` | stated | `g3.r2.s4c`, `g3.r2.s4a`, `g3.r2.s4b`, `g3.r2.s1c` | Dario names the elapsed-time derivation (`now` minus `time_of_last_rate_limit_error`) as the bug that bit him twice, and gideon/konrad reject the flat knob wait, so both discarded pause sources are re |
| `g3.r2.exclusions_or_crossover#6` | stated | `g3.r2.s1d`, `g3.r2.s1a`, `g3.r2.s1b` | Nils commits to "a tracker nobody has throttled should answer 0.0 however far ahead you ask" and nikolai puts a fresh tracker's window at 0.0, with s1b tying the pause point to that remaining figure. |
| `g3.r2.exclusions_or_crossover#7` | stated | `g3.r2.s1b`, `g3.r2.s4a` | Gideon says the pause point should be asking how much of the window is left, and separately that hammering again while still inside the provider's window is the failure being fixed. |
| `g3.r2.exclusions_or_crossover#8` | stated | `g3.r2.s1d`, `g3.r2.s1c`, `g3.r2.s1b`, `g3.r2.s4b` | The pause-equals-time-remaining rule is spelled out with arithmetic (window 1005.0 gives 3.0 at 1002.0, clamped, three decimals), which is exactly what puts the sleep in the horizon band rather than a |
| `g3.r2.exclusions_or_crossover#9` | stated | `g3.r2.s4d` | "even once nothing reads it" is a direct statement that no code path consults the knob any more. |
| `g3.r2.observability#1` | **implied** | `g3.r2.s2c`, `g3.r2.s4b` | No remark says the first failure's delay is 5.0; s2c attaches 5.0-worth of distance only to the horizon (1000.0 -> 1005.0), so the reader must back out the delay by subtraction and assume the delay ac |
| `g3.r2.observability#10` | stated | `g3.r2.s1d`, `g3.r2.s1a` | s1d says outright that "a tracker nobody has throttled should answer 0.0 however far ahead you ask". |
| `g3.r2.observability#2` | stated | `g3.r2.s2c` | s2c names the attribute, the pinned clock, the jitter and the value: "first 429 sets tracker.throttle_cooldown_until to 1005.0". |
| `g3.r2.observability#3` | stated | `g3.r2.s2d`, `g3.r2.s2c`, `g3.r2.s3b` | s2d says to take one clock reading and use it for time_of_last_rate_limit_error and the window both, and s2c pins that reading at 1000.0 with the window landing at 1005.0. |
| `g3.r2.observability#4` | stated | `g3.r2.rev1`, `g3.r2.rev2`, `g3.r2.s2c` | rev1 and rev2 both spell out `throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds)`, and s2c says a second 429 worth 1.0 has to leave the value at 1005.0. |
| `g3.r2.observability#5` | stated | `g3.r2.s1d`, `g3.r2.s1b`, `g3.r2.s1c` | s1d gives this exact pair — "window at 1005.0 gives 3.0 at 1002.0" — for a helper s1b and s1c both describe as asking how much of the window is left, though nobody spells the helper's name. |
| `g3.r2.observability#6` | stated | `g3.r2.s1d`, `g3.r2.s1c` | s1d states "0.5 at 1004.5" for a window at 1005.0, and s1c's three-decimal rule rules out a float-dust answer. |
| `g3.r2.observability#7` | stated | `g3.r2.s1d` | s1d states "0.0 at 1005.0", fixing the boundary as inclusive rather than leaving it open. |
| `g3.r2.observability#8` | stated | `g3.r2.s1c`, `g3.r2.s1d` | s1c reports the helper returning -3.2 once the window was behind us and says "that should be 0.0 clamped", which is exactly the query at 1099.0. |
| `g3.r2.observability#9` | stated | `g3.r2.s1a` | s1a names throttle_cooldown_until "at 0.0 on a fresh tracker"; the hedge is about field ordering churn, not about the initial value. |
| `g3.r2.rule#1` | stated | `g3.r2.s1a`, `g3.r2.s2c` | s1a lists throttle_cooldown_until among the tracker's fields and s2c writes tracker.throttle_cooldown_until, so the field's existence on the tracker is said outright. |
| `g3.r2.rule#10` | stated | `g3.r2.rev1`, `g3.r2.rev2`, `g3.r2.s2b`, `g3.r2.s2c` | rev1 and rev2 both give the max(...) form by name and explain it as a short throttle no longer pulling in a longer window, and s2c states the second smaller wait 'has to leave it there'. |
| `g3.r2.rule#11` | stated | `g3.r2.s2d` | the stamp being set from the one clock reading on each throttle is stated by s2d, and with the clock pinned that value is the same 500.0. |
| `g3.r2.rule#12` | n/a | `g3.r2.s2c` | 16.0 is the suite's third fixture delay, a precondition owed by the backoff computation rather than by any remark about the cooldown horizon. |
| `g3.r2.rule#13` | stated | `g3.r2.rev1`, `g3.r2.rev2`, `g3.r2.s2b` | a longer later wait moving the window further out is exactly what rev1/rev2's max(...) and s2b's 'that window only ever moves further out' describe. |
| `g3.r2.rule#14` | **implied** | `g3.r2.s1d`, `g3.r2.s1c`, `g3.r2.s1b` | the subtraction and three-decimal rounding are told, but nobody names remaining_cooldown_seconds or says it is a module-level function taking (tracker, now) — s1c only calls it 'the helper'. |
| `g3.r2.rule#15` | **implied** | `g3.r2.s1d`, `g3.r2.s1c` | s1d's worked pairs give window-minus-now for a still-open window, yet the reader must invent the helper's name and signature for this call to resolve at all. |
| `g3.r2.rule#16` | **implied** | `g3.r2.s1c`, `g3.r2.s1d` | s1c asks for three decimals, which collapses a sub-millisecond remainder to 0.0, but the expression under test is a function nobody in the corpus names or gives arguments to. |
| `g3.r2.rule#17` | **implied** | `g3.r2.s1c`, `g3.r2.s1d` | the clamp is stated plainly (-3.2 'should be 0.0 clamped', 0.0 at the window edge), but the reader supplies the helper name and two-argument form that the assertion actually calls. |
| `g3.r2.rule#2` | stated | `g3.r2.s1a` | s1a gives the declaration order explicitly — num_other_errors, then time_of_last_rate_limit_error, then throttle_cooldown_until — which is the adjacency the assertion checks, hedging notwithstanding. |
| `g3.r2.rule#3` | stated | `g3.r2.s1a`, `g3.r2.s1d` | s1a says throttle_cooldown_until is 'at 0.0 on a fresh tracker', naming the field and the default together. |
| `g3.r2.rule#4` | **implied** | `g3.r2.s1a`, `g3.r2.s4d` | nobody forbids a second pause-related tracker field; the reader must infer from s1a's in-flux field snapshot and s4d's 'stays in config.py' that only the horizon is added. |
| `g3.r2.rule#5` | n/a | `g3.r2.s2c` | this is the suite establishing its long-wait fixture delay from the backoff rule, not a claim about the horizon; the corpus's only worked delay (s2c) uses different numbers. |
| `g3.r2.rule#6` | stated | `g3.r2.s2d`, `g3.r2.s3a` | s2d says the handler asking the clock twice was the bug and to 'take one reading', and s3a says only throttles read the clock at all. |
| `g3.r2.rule#7` | stated | `g3.r2.s2d`, `g3.r2.s3b` | s2d says the single clock reading is used for time_of_last_rate_limit_error, so the stamp taking the throttle-time value of now is stated. |
| `g3.r2.rule#8` | stated | `g3.r2.s2c`, `g3.r2.rev1`, `g3.r2.rev2` | rev1/rev2 spell out now + delay_seconds as the horizon expression and s2c works it through concretely (1000.0 plus the wait gives 1005.0). |
| `g3.r2.rule#9` | n/a | `g3.r2.s2c` | the short-wait delay of 4.0 is the suite's own fixture setup governed by the backoff rule, not by anything this corpus says about the horizon. |
| `g3.r2.scope#1` | **implied** | — | s3c says a schema failure's whole job is "the counter" and s1a names num_other_errors in passing, but nobody states which counter each verdict kind increments or that a non-throttle failure bumps exac |
| `g3.r2.scope#10` | stated | — | s2d says the single clock reading is used for time_of_last_rate_limit_error as well as the window, so the stamp is that reading. |
| `g3.r2.scope#11` | **implied** | — | The reader is told a schema failure only touches a counter, but never which counters the following transient/terminal verdicts land in nor that the throttle counter holds at 1. |
| `g3.r2.scope#12` | stated | — | s3a's "only throttles read the clock" covers the non-throttle verdicts that follow a throttle just as much as the ones before it. |
| `g3.r2.scope#13` | stated | — | s3c says a non-throttle path has no reason to be moving windows around, so an already-set horizon of 705.0 stays put. |
| `g3.r2.scope#14` | stated | — | s3b names exactly this bug — a timeout between two 429s dragging the last-rate-limit stamp to itself — and s3c says that path moves no stamps. |
| `g3.r2.scope#15` | stated | — | s2d fixes one reading per throttle handler and s3a fixes zero for everything else, which together say the count over a mixed run equals the number of rate-limit failures. |
| `g3.r2.scope#2` | **implied** | — | That a second, differently-classified failure lands in a *different* counter slot is never said; only s3c's "the counter is the whole job" gestures at per-verdict counting. |
| `g3.r2.scope#3` | **implied** | — | Nobody says two distinct verdict kinds share one counter while a third has its own; the reader has to invent the partition that makes (0,2,1) come out. |
| `g3.r2.scope#4` | stated | — | s3a says outright that a bad payload has no business asking what time it is and that only throttles read the clock. |
| `g3.r2.scope#5` | stated | — | s3c says the schema path has no reason to be moving windows around and s1a gives throttle_cooldown_until as 0.0 on a fresh tracker. |
| `g3.r2.scope#6` | stated | — | s3c says that path should not move stamps, and s3b reports a timeout jumping the last-rate-limit stamp as the bug that was fixed. |
| `g3.r2.scope#7` | **implied** | — | A rate-limit counter is never named or said to increment on a THROTTLE; only s1a's "num_other_errors" hints that a separate rate-limit counter exists alongside it. |
| `g3.r2.scope#8` | stated | — | s2d says the handler must take one reading and use it for both the stamp and the window, i.e. exactly one clock call per throttle. |
| `g3.r2.scope#9` | stated | — | rev1/rev2 give the assignment throttle_cooldown_until = max(throttle_cooldown_until, now + delay_seconds) verbatim, and s2c shows the same arithmetic producing 1005.0 from a clock at 1000.0. |

### `g3.r1.failure_behavior#1` — implied

```python
assert outcome(affordable) == (True, 0, 6, 1, "contract:retry"), "2 - 2 == 0 is affordable, so this one is retried"
```

l2 fixes the contract cost at two and l16 says the cost must be charged before the budget is tested, but nobody says that landing on exactly zero remaining is still a retry — the reader must choose `< 0` over the equally available post-deduction `<= 0`, and l15's zero-attempt re-queue is about the free throttle path, not contract.

### `g3.r1.failure_behavior#6` — implied

```python
assert outcome(empty) == (False, 0, 0, 10, "transient:exhausted")
```

l3 pins the transient cost at one and l15 gives the `exhausted` outcome for the throttle path, but no remark says a transient failure with a spent budget yields `transient:exhausted` with attempts floored to zero — the reader must carry the contract-path rule and the throttle-path label across to transients.

### `g3.r1.observability#12` — implied

```python
assert v_reason(last) == "contract:exhausted"
```

Nobody writes contract:exhausted; the reader must compose it by extending the throttle:exhausted pattern onto the CONTRACT category named only in passing.

### `g3.r1.rule#6` — implied

```python
assert v_waivers(transient) == 4, "a transient failure does not touch the waivers"
```

Remarks say a throttle spends a waiver and a terminal leaves the passes untouched, but nobody states that a transient failure leaves the waiver count alone — the reader must infer that only THROTTLE moves it.

### `g3.r1.rule#8` — implied

```python
assert v_waivers(contract) == 4
```

The two-attempt cost is stated but nothing says a CONTRACT failure leaves throttle_waivers_left unchanged; the reader has to generalise from l13's terminal case that only 429s spend passes.

### `g3.r2.exclusions_or_crossover#2` — implied

```python
assert OnlineRequestProcessorConfig(model="gpt-4o-mini").seconds_to_pause_on_rate_limit == 10
```

The only "ten" in the corpus is gideon's complaint about a ten-second pause, a value attached to the pause and not to this field's default, so the reader is left to connect the two (or simply not touch config.py).

### `g3.r2.exclusions_or_crossover#4` — implied

```python
assert processor.config.seconds_to_pause_on_rate_limit == 10
```

Same gap as #2: the default of 10 on the processor's config is nowhere attached to the field name, only to the old flat pause gideon complained about.

### `g3.r2.observability#1` — implied

```python
assert v_delay(first) == 5.0
```

No remark says the first failure's delay is 5.0; s2c attaches 5.0-worth of distance only to the horizon (1000.0 -> 1005.0), so the reader must back out the delay by subtraction and assume the delay accessor returns it unrounded.

### `g3.r2.rule#14` — implied

```python
assert rp.remaining_cooldown_seconds(horizoned, 500.0) == 8.001
```

the subtraction and three-decimal rounding are told, but nobody names remaining_cooldown_seconds or says it is a module-level function taking (tracker, now) — s1c only calls it 'the helper'.

### `g3.r2.rule#15` — implied

```python
assert rp.remaining_cooldown_seconds(horizoned, 508.0) == 0.001
```

s1d's worked pairs give window-minus-now for a still-open window, yet the reader must invent the helper's name and signature for this call to resolve at all.

### `g3.r2.rule#16` — implied

```python
assert rp.remaining_cooldown_seconds(horizoned, 508.0009) == 0.0
```

s1c asks for three decimals, which collapses a sub-millisecond remainder to 0.0, but the expression under test is a function nobody in the corpus names or gives arguments to.

### `g3.r2.rule#17` — implied

```python
assert rp.remaining_cooldown_seconds(horizoned, 600.0) == 0.0, "the remaining cooldown is never negative"
```

the clamp is stated plainly (-3.2 'should be 0.0 clamped', 0.0 at the window edge), but the reader supplies the helper name and two-argument form that the assertion actually calls.

### `g3.r2.rule#4` — implied

```python
assert about_the_pause == {HORIZON}, f"the tracker gained {sorted(about_the_pause)} for the pause; the requirement allows exactly one field"
```

nobody forbids a second pause-related tracker field; the reader must infer from s1a's in-flux field snapshot and s4d's 'stays in config.py' that only the horizon is added.

### `g3.r2.scope#1` — implied

```python
assert counters(tracker) == (0, 1, 0)
```

s3c says a schema failure's whole job is "the counter" and s1a names num_other_errors in passing, but nobody states which counter each verdict kind increments or that a non-throttle failure bumps exactly one of three counters, so the reader must supply the verdict-to-field mapping the tuple encodes.

### `g3.r2.scope#11` — implied

```python
assert counters(tracker) == (1, 3, 2)
```

The reader is told a schema failure only touches a counter, but never which counters the following transient/terminal verdicts land in nor that the throttle counter holds at 1.

### `g3.r2.scope#2` — implied

```python
assert counters(tracker) == (0, 1, 1)
```

That a second, differently-classified failure lands in a *different* counter slot is never said; only s3c's "the counter is the whole job" gestures at per-verdict counting.

### `g3.r2.scope#3` — implied

```python
assert counters(tracker) == (0, 2, 1)
```

Nobody says two distinct verdict kinds share one counter while a third has its own; the reader has to invent the partition that makes (0,2,1) come out.

### `g3.r2.scope#7` — implied

```python
assert counters(tracker) == (1, 2, 1)
```

A rate-limit counter is never named or said to increment on a THROTTLE; only s1a's "num_other_errors" hints that a separate rate-limit counter exists alongside it.
