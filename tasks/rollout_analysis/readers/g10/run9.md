# g10 run 9 (eval 5b468409, rollout 1aea4bd6) — reward 1

## What this run found

This is a clean success: all 8 declared facts (r1/r2 × rule, scope, exclusions_or_crossover,
observability) scored 1, `open_feature`, `hidden_mean`, `suite_ok` and all three provenance checks
are 1, and the final turn shows the agent pushing to `main` with CI green and the service healthy
(last lines of the transcript). There is no failing-test trace in the pointer sheet to explain.

The agent's search strategy was unusually thorough for the format. After the wiki (BookStack
`/api/search` + full-page-with-comments fetch, line 3438) and an IMAP mail dump (line 3439) both
came back essentially empty for this ticket — correctly, since the answer key says all 46 remarks
for g10 live in chat only, none in wiki or mail — it wrote a Mattermost API script that walked every
channel and dumped the **entire company chat history**, about nine months and 10,300+ lines, into
one file `/tmp/chat_all.txt` (lines 3691-3700). From there it ran broad keyword greps
(`capacity|refund|settlement|debt|reservation|bucket`, then narrower terms like `clamp`,
`CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_debt_clamps`, `refund_capacity`, `attempts_left`,
`haiku`) over the full dump, and read wide context windows around every hit to reconstruct each
thread chronologically before writing any code. This "dump everything, then grep" approach recovered
39 of the 46 remarks (all 4 herrings and all 4 reversals included) without the agent ever explicitly
targeting most of the channels or days they lived in — they simply fell inside the context window of
a targeted hit.

## Herrings — correctly resolved

Both requirements carry a January "settled in review" decision that a later thread (April) explicitly
overturns. The agent found and read all four herring exchanges in full (lines 4157, 4708 for r1's two
January threads; 5011, 5038 for r2's) and all four reversals (4185 ×2 for r1, 4354 and 5265 for r2). Its
own reasoning names the resolution directly: "January plan (single `_free_capacity` for both outcomes)
was later superseded in April" (line 5052) and "chat 1119-1121 (Jan): 0.0 floor — superseded by April
debt design. (April is newer)" from its final pre-push self-audit (line ~9314). The shipped code follows
every reversal, never the herring: `free_capacity` no longer clamps at 0.0 (it carries debt to
`-CAPACITY_DEBT_FLOOR_FRACTION * limit`), and failure/success go through two distinct calls
(`refund_capacity` vs `free_capacity`) rather than one shared `_free_capacity`.

## What it missed, and why it didn't matter

Seven clue-level remarks (all clues, no herrings/reversals) never surfaced anywhere in the transcript:
`g10.r2.s1_l3`, `g10.r1.g10.r1.s2.l1`, `g10.r2.s1_l4`, `g10.r2.s2_l3`, `g10.r1.g10.r1.s2.l3`,
`g10.r2.s2_l1`, `g10.r1.g10.r1.s1.l1`. Each carries a fact that had 2-4 other found leaves, so no fact
was starved despite the gap. The common thread is that these remarks describe the *symptom* in plain
incident language — "split-limit config," "thirty real requests a minute against a sixty ceiling,"
"gemini 503'd on everything," "estimator came in light again" — without ever using the core vocabulary
(`capacity`, `refund`, `settlement`, `debt`, `reservation`, `bucket`, `clamp`) the agent's grep passes
were built around, and the agent never did a plain sequential read of the days/channels they sit in.

One data quality note: the pointer sheet's line pointer for `g10.r2.h1` (transcript line 1573) is wrong
— that line is inside an unrelated early code-reading pass, not the chat exchange. The real herring
text is at transcript line ~5011 (step ~75), inside the full January-21 `#releases` block the agent
actually read; verified by direct grep of the exact quoted text.

## Why each fact passed

- **r1.rule / r1.observability**: the s1 (debt floor + constant) and s3 (per-call counter) leaf
  clusters were read in full — "the tracker should just carry a plain counter starting at 0,"
  "`num_capacity_debt_clamps` went up by two on a single settle... my per-run figure is double,"
  "one call one tick" — plus rev1/rev2, which state the `0.25` fraction and constant name verbatim.
  The shipped `_settle_axis` helper implements exactly this: one `clamped` boolean OR'd across axes,
  one increment per `free_capacity` call.
- **r1.scope / r1.exclusions_or_crossover**: s2 (per-axis, defaulted axis still bounded, `None` axis
  never floored, `available_request_capacity` never floored) and s4 (reaching the *ceiling* is not a
  clamp — refill, release, and any settle that stays above the floor all leave the counter alone) were
  both read as full threads. The final code puts the floor-check only inside `_settle_axis` (called
  from `free_capacity`), never inside `update_capacity`'s refill or `refund_capacity`'s cap-at-ceiling
  path, matching this exactly.
- **r2.rule / r2.scope**: s1/s2 (settle only the gap on success, refund the whole reservation on
  failure) plus rev1 (which gives the exact split: `free_capacity(used, blocked)` on success with the
  slot staying spent, `refund_capacity(blocked)` on failure with the slot going back) and s3
  ("`_refund_capacity` should be firing at the point we give up on a request entirely, and right now
  nothing calls it there") were all read. The final `handle_single_request_with_retries` calls
  `_refund_capacity` on both the requeued and the exhausted branch (verified directly in the transcript
  at the printed 540-610 window), and `_free_capacity` only on success.
- **r2.exclusions_or_crossover**: s4 ("we hand back the token counts the failed response itself
  reported so the bucket finishes the minute holding more capacity than the limit allows," "the length
  ones are worst - `finish_reason` length... 800 output against the 100 output we actually booked") and
  rev2 ("on failure the booking comes back whole, the reported usage doesnt enter into it") were both
  read in full. `refund_capacity`'s signature takes only `blocked` — it has no access to
  `generic_response.token_usage` at all, so it cannot use the reported figure even by mistake.
- **r2.observability**: s5 ("`num_capacity_settlements` as its own counter... `num_capacity_refunds`
  seperate, next to it," "an acquire bumps neither... nothing on the way in touches either one," "we're
  counting the call, not whether it moved a number") was read as a full cluster. Both counters are
  incremented unconditionally at the top of their methods, before any per-axis `None` check, so they
  still tick on an unlimited axis.

## Bottom line

No lost facts. The reward-1 outcome rests on a genuinely strong search (whole-corpus dump + grep +
wide-context reads) rather than luck: every subconclusion cluster for both requirements was read in
full at least once, both herring pairs were correctly resolved via their reversals, and the final
implementation was spot-checked against the ticket and the recovered chat record before the agent
pushed.
