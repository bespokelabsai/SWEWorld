# g3 run 10 (eval 035777f5, rollout 6880e992) — reward 0.7778

## What this run found

This run abandoned targeted search almost immediately in favor of full enumeration: after
one `'retry'` term-search on Mattermost (step 30), it wrote scripts that dumped the *entire*
corpus — every channel via the Mattermost v4 API into `/tmp/chat_all.txt` (11,031 lines,
step 32), every BookStack page **with its comments** into `/tmp/wiki_all.txt` (9,024 lines),
and the full IMAP mailbox into `/tmp/mail_all.txt` (1,424 lines) — then grepped those dumps in
widening waves (`waiver|throttle`, then `CONTRACT|TRANSIENT|TERMINAL|verdict|decide(`, and for
wiki `jitter|backoff|exhausted|abort|num_api_errors|num_other_errors|num_rate_limit|cooldown|
cool down|retry_policy`). This enumeration strategy is exactly why it caught the two
comment-only wiki remarks for g3.r1 and g3.r2 that BookStack search would have missed on its
own, and both mail threads for g3.r1 plus one of the two for g3.r2.

**All five g3.r1 facts passed.** The shipped `decide()` almost paraphrases the reversed chat
threads verbatim: "the waiver comes off on every 429 regardless; the charging only starts once
the pool is empty" (transcript L5530-5531) mirrors `g3.r1.rev1` exactly; "a contract failure
costs two attempts, because a model handing back garbage tends to keep doing so" mirrors
`g3.r1.l2`/`l9`; the deduct-then-check-strictly-negative ordering mirrors `g3.r1.l16/l17/say23`.
Notably, this run's world had the v9-rewritten `konrad` 14:12 turn in the `g3.r1.l1` thread
(2025-06-03, #code-review) — "length does come good on a retry now and then, so dont stop
retrying it" instead of the older "stops being retryable, fail it out on the first." The agent
read the *new* wording (transcript L3553) and concluded "CONTRACT costing two attempts is
corroborated" (L3584); it shipped `finish_reason=="length"` as a retryable CONTRACT failure
costing 2 attempts, matching the answer key's observability row exactly — it never made it
terminal.

`g3.r2.scope` and `g3.r2.exclusions_or_crossover` also passed cleanly: the record-keeping split
(only `THROTTLE` reads the clock and extends the horizon; `TRANSIENT`/`TERMINAL` share
`num_api_errors`; `CONTRACT` bumps `num_other_errors`) and the dead `seconds_to_pause_on_rate_limit`
knob both shipped correctly, off `g3.r2.s3a/s3b/s3c`, `say19-22`, `s2d`, `s4a/s4b`, and the
`s4d` mail thread.

## What it missed, and why

Both lost facts — `g3.r2.rule` and `g3.r2.observability` — fail on the **same line**: the judge
reads `OnlineStatusTracker().throttle_cooldown_until` off a freshly constructed tracker and
asserts it equals `0.0`. The shipped field is
`throttle_cooldown_until: float | None = field(default=None)` (raw tool call, patch4.py),
so this reads `None`, not `0.0`, and both facts fail on their very first assertion.

The agent *understood* the effective behaviour — its own docstring for `remaining_cooldown_seconds`
says "the answer is `0.0` however far ahead you ask" (L5624-5625), lifted almost verbatim from
`g3.r2.s1d`, which it did find and read in full (L2759). But it shipped the *raw field default*
as `None`, because it took at face value one line buried in the `g3.r2.h2` herring exchange that
nobody in the corpus ever explicitly reversed: "no thats its own reset, sets it to none" (L2587,
the herring exchange's own tail, about a clear-on-success path). Its planning notes explicitly
carry this forward as "clear-on-success reset" (L5016, L6006), and it built a `clear_cooldown()`
helper and a `None` `__init__` default around it — a behaviour the answer key never asks for.

The two remarks that would have stopped this never surfaced: `g3.r2.s1a` (wiki comment,
"0.0 on a fresh tracker... nothing else added for the pause" — stating both the literal default
*and* that nothing extra like a reset belongs) and `g3.r2.s1c` (chat, "-3.2... and
4.999999999998 before that — clamp at 0.0, round to three decimals"). Both are near-misses
rather than dead ends: a wiki grep that *did* include `cooldown` was actually executed (raw
tool call), but the terminal-screen snapshot shown to the model was the truncated tail of a
`| head -40` pipe that scrolled past `s1a`'s comment; and a chat grep for `cooldown` was
explicitly planned three times (L2534, L2626, L2931) but the command actually run each time
used a narrower term list that dropped it, so `g3.r2.s1c` was never seen at all (confirmed by a
full-text grep of the transcript for "4.999999999998", "-3.2", "round to three decimals" — zero
hits). A latent second bug compounds this: `remaining_cooldown_seconds` ships without
`round(..., 3)` at all (L5638), which independently breaks the `508.0009` boundary case in
`g3.r2.rule`'s table; the agent only rounded where the *ticket itself* spelled out the formula
(`delay_for`'s jitter, L137).

## Herrings

All four herrings (`g3.r1.h1/h2`, `g3.r2.h1/h2`) were found and correctly abandoned in favor of
their reversals — the shipped waiver-pool and `max()`-horizon logic match the reversals exactly.
The one exception is the unreversed detail buried inside `g3.r2.h2`'s own exchange (the
"reset to none" tail) discussed above, which the agent could not have known was scaffolding
rather than a settled decision, since nothing in the corpus ever explicitly retracted it.
