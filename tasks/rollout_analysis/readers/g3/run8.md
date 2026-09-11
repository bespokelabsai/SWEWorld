# g3 run 8 (rollout cd046ece, eval ce846459, world-hosted v7) -- reward 0.8889

## What this run found

The agent read all three surfaces, not just chat: it dumped the full Mattermost history over a
scripted channel export (11,031 lines to `/tmp/chat.txt`), pulled every mail message over IMAP as
`worldadmin@world.local`, and -- correctly, per the ticket's own warning that `/api/search` does
not index comments -- enumerated *every* BookStack page via `/api/pages?count=500` and fetched
each one's full body **and comments** via `/api/pages/{id}`. That enumeration is exactly why both
wiki-comment remarks (`g3.r1.l5`, `g3.r2.s1a`) were found even though a search-only agent would
have missed them.

Chat, however, was swept with a single capped call --
`grep -n -i -E 'throttle|transient|classif|failure class|jitter|retry policy|free pass|cooldown|
backoff' /tmp/chat.txt | head -60` (transcript line 2628) -- then explored outward from those 60
hits with targeted `sed -n` ranges. Because the regex also matches ordinary engineering chatter (PR
review threads using "classif[y]", an aside about running "at full throttle", etc.), the cap
silently displaced some on-topic hits.

The agent correctly read and reversed all four herrings. `g3.r1.h1` ("THROTTLE costs 0 attempts,
no cap") is overturned by `g3.r1.rev1`; `g3.r1.h2` ("no ceiling on it") by `g3.r1.rev2`; `g3.r2.h1`
("plain assignment, most recent wins") by `g3.r2.rev1`; `g3.r2.h2` ("last THROTTLE wins, no
comparison") by `g3.r2.rev2`. Its shipped `record_verdict()` implements exactly the reversal's
formula -- `throttle_cooldown_until = max(getattr(tracker, "throttle_cooldown_until", 0.0) or 0.0,
horizon)` -- and its `decide()` spends a `throttle_waivers_left` pool of 6 before charging an
attempt, matching `g3.r1.rev2`, not either herring.

## What it missed, and why

Eight of nine facts passed. The one it lost, **`g3.r2.rule`**, fails on the very last assertion of
`test_rule__the_cooldown_horizon_is_one_new_tracker_field_that_only_ever_moves_forward`: the field
placement, the `0.0` default, and the `max()`-not-overwrite semantics all passed, but
`remaining_cooldown_seconds(horizoned, 500.0)` returned `8.000900000000001` where the test expects
`8.001`. The shipped implementation (raw tool call, full rollout JSON message index 145) is:

```python
def remaining_cooldown_seconds(tracker, now: float) -> float:
    horizon = getattr(tracker, "throttle_cooldown_until", 0.0) or 0.0
    return max(0.0, horizon - now)
```

No `round()`. The answer key's `g3.r2.sc1` states the wait is "floored at zero and rounded to three
decimals," but that specific instruction lives in exactly one remark across all 49: `g3.r2.s1c`
(gideon, #pipeline, 2025-04-07 13:41-13:53 -- "`remaining_cooldown_seconds(tracker, now)` handed
back `-3.2`... and `4.999999999998` before that -- clamp at `0.0`, round to three decimals"). I
grepped the full transcript for its distinctive text (`4.999999999998`, `-3.2`, "round to three
decimals") and got zero hits, confirming the pointer sheet's "0 hits" mark. The agent's own
settled-record Analysis (transcript lines 4705, 4907, 8420) states "`remaining_cooldown_seconds`
clamps at `0.0`" and never mentions rounding at any point -- so this is not a reasoning-vs-code
slip, it is that the fact never entered the agent's reasoning at all. `g3.r2.s1c`'s own text
contains "cooldown" (via `remaining_cooldown_seconds`) and should have matched the capped chat
regex; the same-day #general exchange one channel over (`g3.r2.s1d`, carrying an overlapping but
rounding-free numeric example) *was* read, which suggests the #pipeline exchange simply fell
outside whatever sed range the agent chose to follow up with, rather than the regex itself
excluding it.

Nine other remarks were likewise never surfaced (`g3.r2.say23`, `s1b`, `s2a`, `s2c`, `s3b`, `s4c`,
`g3.r1.say23`, `g3.r1.l11`), but none of them cost a fact: each is one of several independent
carriers for a fact that passed via a different remark the agent did read (e.g. `g3.r2.exclusions_
or_crossover` passed via `s4a`/`s4b`/mail `s4d` even though `say23` and `s4c` were both missed).
`g3.r2.rule` is the one requirement where the missing sub-detail (rounding) had only a single
carrier in the entire plant -- a single point of failure in the plant's spread for that one detail,
not a broader comprehension gap.

## Coordinator check: does finish_reason=="length" ship as terminal/non-retryable?

**Yes**, but not through `classify_failure()`. `_TYPE_NAME_CLASSES['ValueError'] = CONTRACT` is
unchanged and matches the ticket's own type table, so `policy.decide(ValueError("finish_reason was
length"))` called directly still returns CONTRACT and would cost 2 attempts -- which is exactly what
`test_r1.py` calls (lines 221, 224), so `g3.r1.rule` scored 1 legitimately at the policy level.

But the agent separately patched the *call site*, `base_online_request_processor.py` (raw rollout
JSON message index 257, script `/tmp/edit9.py`), to set `request.attempts_left = 0` immediately
before raising `ValueError(f"finish_reason was {generic_response.finish_reason}")` for any reason in
`config.invalid_finish_reasons` (default `["content_filter", "length"]`). In the actually-shipped
request path, a length or content_filter failure is therefore forced to `contract:exhausted` on the
very first attempt, not charged 2 attempts as the hidden rule requires -- invisible to the grader
purely because `test_r1.py` never exercises the online processor's except block, only
`policy.decide()` in isolation. This is not a stray, reverted experiment: it shipped as its own PR,
**#738**, explicitly titled *"feat: contract failures cost two attempts; invalid finish_reasons fail
out on the first"* (transcript line 8248, commit `219acbb`), merged and CI-green as part of the final
deployed state (transcript lines 8397-8420).

The agent did quote konrad's line. Transcript lines 7772 and 7789 quote it while first reading the
thread ("and length wont fix itself on a retry anyway, so it stops being retryable, fail it out on
the first"), and lines 7822/7873/7875 elevate it to a second settled decision alongside the real
CONTRACT-costs-2-attempts rule: *"Two settled-but-unimplemented decisions found: (a) CONTRACT costs
two attempts (done), and (b) Jun 3: an invalid finish_reason such as `length` won't fix itself on a
retry, so it stops being retryable and fails out on the first attempt"*. The shipped code comment
paraphrases both konrad's line and an unrelated mail remark (`g3.r1.l12`, "attempts still on the
clock are worth nothing") together to justify the zeroing.

Checked against `task_generator/out/retry-backoff-policy/clues/plant.json` (`g3.r1.l1`): konrad's
"fail it out on the first" line lives only in the remark's **invented scaffolding dialogue**. The
remark's actual `settles` field is "the team agrees a contract failure should be charged more than
one attempt," and its `forbidden_terms` list deliberately excludes "cost" and "two attempts" --
withholding the exact charge for a different remark (`g3.r1.l2`, 2025-06-26) to carry. This is a
clean scaffolding-outvotes-the-plant case: invented filler dialogue that reads as a real decision led
the agent to ship a genuine deviation from `g3.r1.rule`, currently undetected only because the
grader's coverage of that fact does not reach the call site the agent modified.

## Summary

**Lost fact: `g3.r2.rule`** -- cause `not_found`. The sole remark stating "round to three decimals"
(`g3.r2.s1c`) was never surfaced by the agent's capped chat search; its own settled-record reasoning
never acquired the requirement, and its shipped `remaining_cooldown_seconds()` correctly implements
everything else about the rule (one field, right position, `max()` semantics) but omits the
rounding, failing the test's boundary-precision assertion by a fraction of a millisecond
(`8.0009000...` vs `8.001`).

**Additional risk found on request (does not affect the 0.8889 score):** the shipped code makes
`finish_reason=="length"`/`"content_filter"` fail out on the first attempt (`attempts_left = 0`
before raising) rather than costing 2 attempts as `g3.r1.rule` actually specifies. The agent based
this on konrad's "fail it out on the first" line, which the plant record shows is invented scaffolding
dialogue, not part of the remark's real settled content. `test_r1.py` never exercises the call site
that carries this bug, so it ships undetected.
