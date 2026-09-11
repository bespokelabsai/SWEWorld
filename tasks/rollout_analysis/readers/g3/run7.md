# g3 run 7 (eval ce846459, rollout 3111b210) — reward 0.8889

## What this run found

The agent's method was dump-then-grep: it pulled the *entire* Mattermost history into
`/tmp/chat.txt` in one shot (`Analysis: Chat dumped (10285 lines).`, line 3006), the whole
mailbox into another file (`119 mails dumped`, line 2446), and enumerated BookStack pages,
fetching `/api/pages/{id}` for each so page **comments** were visible too — it explicitly
noted the search-doesn't-index-comments trap while chasing a duplicate-page-ID mystery
(line 4580). Against the chat dump it then ran a sequence of multi-term `grep -n -i
'a\|b\|c...'` sweeps (`jitter|backoff`; `THROTTLE|TRANSIENT|CONTRACT|TERMINAL`;
`retry_after|retry-after|decide(|verdict|throttle_cooldown|DEFAULT_THROTTLE|waiver`;
`time_of_last_rate_limit_error|cooldown_until|two fields|one field`), each capped with
`head -N`, and `sed`-range-read the promising hits. This recovered 41 of 49 remarks —
all 4 herrings, all 4 reversals, both wiki comments, and all 3 mail threads.

By transcript line 3157 (`Analysis: Chronology matters: March says THROTTLE never deducts
and no ceiling; April introduces waivers. Need later messages.`) the agent had explicitly
worked out the herring/reversal structure for both requirements before writing any code, and
the shipped design (message ~9260) matches every reversal, not any herring: per-request
`DEFAULT_THROTTLE_WAIVERS = 6` on `APIRequest`, `TERMINAL` draining `attempts_left` to 0 while
leaving waivers untouched, exhaustion tested strictly-negative *after* deduction, and
`throttle_cooldown_until` written as `max(existing, now + delay)` off one clock read. All 5
`g3.r1` facts and 3 of 4 `g3.r2` facts scored 1.

## What it missed, and why

The one lost fact is `g3.r2.rule`, and it traces to exactly one remark. The shipped
`remaining_cooldown_seconds` is:

```python
def remaining_cooldown_seconds(tracker, now: float) -> float:
    cooldown_until = getattr(tracker, "throttle_cooldown_until", 0.0) or 0.0
    return max(0.0, cooldown_until - now)
```

Correctly clamped at zero, but **never rounded**. The grader's rule test asks for
`remaining_cooldown_seconds(horizoned, 500.0) == 8.001` where the raw subtraction is
`508.0009 - 500.0 = 8.000900000000001` — round to 3 decimals and it's `8.001`; skip the
round and the assertion fails on the un-rounded float. `g3.r2.observability` still passed,
because that test's worked table (1002.0→3.0, 1004.5→0.5, 1005.0→0.0) is all exact numbers
that never expose a missing `round()`.

The rounding requirement lives in exactly one remark, `g3.r2.s1c` (gideon, #pipeline,
2025-04-07 10:54): *"remaining_cooldown_seconds(tracker, now) handed back -3.2 once the
window was behind us, and 4.999999999998 before that — clamp at 0.0, round to three
decimals."* Grepping the transcript for its literal identifiers (`4.999999999998`,
`remaining_cooldown_seconds(tracker, now)`, "round to three") turns up nothing — none of
the agent's grep patterns contained "round", "clamp", or "remaining_cooldown_seconds"
itself, so a remark carrying exactly that text, already sitting in the locally-dumped
`/tmp/chat.txt`, was never read. What the agent *did* read is a same-day, different-channel
conversation — `g3.r2.s1d` (#general, 14:02, line 4847) — that discusses the same function
name but only with exact-valued examples, so it registered as "requirement" and got
implemented, but it could not have taught the agent to round, because its own worked
examples never needed rounding. This is a genuine near-duplicate-coverage gap: the agent
believed it had fully specified `remaining_cooldown_seconds` because it found *a* remark
about it, and the one remark that actually carried the missing half was never surfaced.

Seven other chat remarks were likewise never found (`g3.r2.say23`, `g3.r1.l16`,
`g3.r2.s1b`, `g3.r2.s3a`, `g3.r1.l18`, `g3.r1.l1`, `g3.r1.l4`) for the same reason — grep
vocabulary miss against an already-fetched file — but each is redundantly carried by other
remarks the agent did find, so no other fact was lost.

## Herrings

All four herrings (`g3.r1.h1`, `g3.r1.h2`, `g3.r2.h1`, `g3.r2.h2`) were seen, their
reversals were also seen, and the agent explicitly reasoned about the chronology (line
3157 for r1, line 3106 for r2) before committing to code. None was followed: the shipped
code has the six-waiver system (not "THROTTLE always free") and the monotonic `max()`
horizon (not plain overwrite / last-write-wins).

## Coordinator check: is `finish_reason == "length"` shipped as terminal?

**No.** `classify_failure()` (full rollout JSON message index 225) sorts a caught exception
by HTTP status, then by exception *type* via the MRO, then by message-substring markers,
then defaults to `TRANSIENT`. `_TYPE_NAME_CLASSES` (message index 223) maps `"ValueError"`
unconditionally to `FailureClass.CONTRACT`. The raise site is untouched —
`raise ValueError(f"finish_reason was {generic_response.finish_reason}")` (transcript lines
829, 6548) — so a length failure is still a plain `ValueError`. No new exception class was
introduced, `"length"` appears nowhere in `_MESSAGE_MARKERS`, and there is no `TERMINAL`
branch for it: it is `CONTRACT`, charged `CONTRACT_ATTEMPT_COST = 2`, exactly matching the
answer key's `g3.r1.rule`.

The remark that could have argued the other way — `g3.r1.l1` (#code-review, 2025-06-03),
which ends with konrad's turn *"and length wont fix itself on a retry anyway, so it stops
being retryable, fail it out on the first"* (answer key line 1432) — was never surfaced by
this agent; `"fail it out on the first"` and `"wont fix itself"` appear nowhere in the
transcript or the full rollout JSON, so the agent never quoted it. The shipped code is
correct here **by omission, not by weighing and rejecting** konrad's line — the same grep-
vocabulary gap documented above for `g3.r2.s1c` also swallowed this remark.

## Bottom line

Reward 0.8889 (8/9). The only lost fact, `g3.r2.rule`, failed because
`remaining_cooldown_seconds` was never rounded to three decimals — a sub-element carried
by a single unsurfaced remark (`g3.r2.s1c`) whose exact wording never matched the agent's
grep vocabulary, compounded by the agent finding a same-topic remark elsewhere that gave
false confidence the function was fully specified. This is a search-strategy miss
(`not_found`), not an infra failure, a herring, or a task defect — CI was green and the
feature was deployed.
