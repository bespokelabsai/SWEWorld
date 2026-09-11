# g3 run 9 (40be2bf1) — reward 1, all 9 facts passed

## What this run found

This is a clean sweep: every graded fact (`g3.r1.{rule,scope,exclusions_or_crossover,failure_behavior,observability}`
and `g3.r2.{rule,scope,exclusions_or_crossover,observability}`) scored 1, the feature was built, the
suite passed, and the code was pushed, went CI-green, and deployed.

The agent's search was methodical and multi-surface rather than lucky. It dumped the *entire*
Mattermost history for every team/channel into one 10285-line file (`/tmp/chatall.txt`, step 51)
rather than searching channel-by-channel, then ran a widening sequence of keyword greps against it —
starting broad (`free pass|failure class|classif|throttle|jitter|retry|cooldown|backoff`, step 25),
narrowing to structural terms (`decide|attempts_made|pass count|...`, step 56), then to the literal
failure-class tokens (`CONTRACT|TRANSIENT|TERMINAL|THROTTLE`, step 62), and finally to exact phrases
around specific hits (`fake clock`, `throttle_waivers_after`, `throttle:exhausted`, `throttle
horizon`). Critically, it consistently followed up a grep hit with a wide `sed -n` context read
(e.g. lines 3499, 3974, 4034) instead of trusting the single matched line — this is what let it
catch reversals and herrings, which live a few lines *before or after* the literal keyword match
inside a multi-turn exchange, not on the matched line itself.

On mail, it wrote a small pickle-based IMAP parser to pull full thread bodies to `/tmp/mail.txt`
(steps 15 and 20) rather than reading subject-line snippets, which is why it caught all three mail
clues (`g3.r1.l8`, `g3.r1.l12`, `g3.r2.s4d`) including the ones carrying `exclusions_or_crossover`
that only show up mid-thread. On wiki, it explicitly fetched `/api/pages/{id}` (step 35) to pull
page *comments* rather than relying on BookStack search — correctly anticipating that comments
aren't indexed — and got both wiki-comment clues (`g3.r1.l5`, `g3.r2.s1a`).

## What it missed, and why it didn't matter

Of the 49 answer-key remarks, 11 never appear verbatim in anything the agent's tools printed:
`g3.r2.say23`, `g3.r1.l16`, `g3.r2.s1b`, `g3.r2.s2a`, `g3.r2.s4c`, `g3.r1.l11`, `g3.r1.l14`,
`g3.r1.l19`, `g3.r1.l9`, `g3.r2.s4b`, `g3.r1.l1`. I grepped the full transcript for each one's
distinctive phrasing and literal identifiers (e.g. `attempts_made` for `g3.r1.l9`) and found nothing
beyond the ticket text and the agent's own code — these truly weren't surfaced by any command it ran.

None of this cost a fact. Every one of the 11 carries a fact that a sibling remark — which the agent
*did* find and act on — also carries: `g3.r1.l1`'s "CONTRACT costs two attempts" point is restated
independently by the found `g3.r1.l2`; `g3.r1.l14`'s "a zero-cost throttle still gets dropped at
attempts_left==0" point is restated by the found `g3.r1.l15` and `g3.r1.rev1`; `g3.r1.l16`/`l19`'s
ordering point (check after deduction, delay 0.0 for non-retries) is restated by the found
`g3.r1.l17`, `say23` and `l18`; and so on for the rest. This is exactly what the answer key's
`spread_problems`/`not_fragmented` gates are designed to guarantee — no single remark is load-bearing
— so a search that is thorough but not exhaustive still reconstructs every fact correctly.

## What it believed, and why

All four herrings were seen and correctly rejected in favor of their reversals, both of which the
agent also read:

- `g3.r1.h1` ("THROTTLE costs 0, decide charges nothing and re-queues") → reversed by `g3.r1.rev1`
  ("free while `throttle_waivers_left > 0`, then decide charges 1"). The agent's running synthesis
  (line 2658) states the reversed rule, not the herring.
- `g3.r1.h2` ("no ceiling — THROTTLE never deducts, only TRANSIENT/CONTRACT do") → reversed by
  `g3.r1.rev2` ("APIRequest carries `DEFAULT_THROTTLE_WAIVERS = 6`, decide takes
  `throttle_waivers_left`"). The agent explicitly logged finding this reversal at line 3825.
- `g3.r2.h1` ("plain assignment `throttle_cooldown_until = now + delay_seconds`") → reversed by
  `g3.r2.rev1` (`max(throttle_cooldown_until, now + delay_seconds)`). Agent's analysis at line 3686:
  "cooldown horizon is a floor — max(existing, now + delay)".
- `g3.r2.h2` (same plain-overwrite herring, restated in `#cookbooks`) → reversed by `g3.r2.rev2`,
  same floor logic.

The shipped `decide()` and `record_verdict()` in `retry_policy.py` (transcript lines 4817–4904)
implement the reversed rules exactly: cost is 0 only while `throttle_waivers_left > 0` and then
becomes 1, and the cooldown horizon is written as `max(existing_horizon, now + delay_seconds)` from
a single clock read taken only on THROTTLE. Nothing in the final code traces back to a herring.

## Why each lost fact was lost

None — all 9 facts scored 1, so there is nothing to explain here. The run's only friction points
were mechanical: a `sed -n` read at transcript line 3499 hit a 10000-byte terminal-output cap and
elided ~70 bytes mid-range, and the agent occasionally re-verified information it already had
(visible in the repeated "Need to read..." plan lines) — neither slowed it enough to lose a fact
before the run ended, and CI/push/deploy all completed cleanly.

## Coordinator check: does the shipped code terminal-ize `finish_reason == "length"`?

**No.** `classify_failure()`'s `_TYPE_NAME_CLASSES` table (transcript line 4677) maps `"ValueError"`
unconditionally to `FailureClass.CONTRACT`, and `_MESSAGE_MARKERS` has no `finish_reason`/`length`
entry — only rate-limit-style phrases route to THROTTLE (line 4684+). There is no new exception
class and no TERMINAL branch anywhere in the shipped module. The `ValueError(f"finish_reason was
{generic_response.finish_reason}")` raised at line 666 reaches `classify_failure()` as a plain
`ValueError` and is priced as CONTRACT (2 attempts) — matching the answer key, and matching what
`policy.decide(ValueError("finish_reason was length"))` would return under the grader's actual test.

The agent never quoted konrad's "fail it out on the first" line, and it never saw it: grepping both
the transcript and the full rollout JSON for that phrase (and for `finish_reason length`, `broken
payload shoudn't get that many goes`) returns zero hits anywhere outside this audit's own commands.
This is consistent with `g3.r1.l1` already being marked `found: no` in the remarks table above — the
`#code-review` 2025-06-03 thread never surfaced in any grep or `sed` range the agent printed in this
rollout. Konrad's invented turn is not something this v7 world served to this agent, or if it was
served, the agent's search never reached it; either way it had zero influence on the shipped code.
