# g3 run 6 (0d78fdbb, eval 035777f5) — reward 0.8889

This run scored 8 of 9 declared facts, losing only `g3.r2.rule`. It is a strong run: it dumped
Mattermost, BookStack (including comments) and IMAP mail wholesale, ran repeated targeted greps
plus manual `sed` windows over the chat dump, read every mail thread in full, and self-corrected a
BookStack comments-dump bug mid-run (its first pass recorded only `active`/`archived` state
strings for comments; it noticed and re-fetched `/api/pages/{id}` for every page, which is exactly
the "search does not index comments" trap the world sets — this is how it caught both wiki-comment
clues, `g3.r1.l5` and `g3.r2.s1a`). It found all four herrings and both reversals for each, and
followed every reversal: the shipped `decide()` charges a per-request waiver pool (not flat-free
429s) and `record_on_tracker()` advances `throttle_cooldown_until` with `max(current, horizon)`
(not a plain overwrite) — matching `g3.r1.rev1/rev2` and `g3.r2.rev1/rev2` exactly, never the
herrings they overturn.

**Re-plant check.** v9 rewrote konrad's 2025-06-03 #code-review turn about `finish_reason ==
"length"` from "stops being retryable, fail it out on the first" to "does come good on a retry now
and then, so dont stop retrying it, it just shouldnt get as many goes as a timeout." This run read
the rewritten line verbatim (transcript line 3221) and shipped exactly that: `length` classifies
as `CONTRACT` (via the ticket's own table), is charged 2 attempts (per `g3.r1.l2`), and stays
retryable until the budget runs out — never made terminal. `r1.observability`'s
`length_via_request_path == [1, 1]` check passed, confirming this directly.

**The lost fact.** `g3.r2.rule` failed on one specific assertion:
`remaining_cooldown_seconds` must return `round(max(0.0, horizon - now), 3)`, and the shipped
implementation (`horizon - now`, clamped at 0.0, never rounded) returns `8.000900000000001`
instead of `8.001`. Everything else about r2 was implemented correctly — the tracker gained
exactly one new field in the right position, the monotonic `max()` advance is correct, the clock
is read once per throttle, and the dead config knob survives unread — which is why
`r2.scope`/`r2.exclusions_or_crossover`/`r2.observability` all passed. The cause is `not_found`:
the one remark that states the rounding requirement explicitly, `g3.r2.s1c` (#pipeline,
2025-04-07, "`remaining_cooldown_seconds(tracker, now)` handed back -3.2 ... 4.999999999998 ...
clamp at 0.0, round to three decimals"), never surfaces anywhere in the transcript — grepping the
full transcript for `4.999999999998`, `-3.2`, and `round to three decimals` returns zero hits. The
agent's own consolidated design summary (line 5313) states "remaining_cooldown_seconds clamps at
0.0" with no mention of rounding, matching the gap precisely. The root cause is a search-coverage
gap, not a misread: no grep this run issued against the chat dump ever used `cooldown` or
`remaining_cooldown` as a pattern (that pattern only appears in the wiki- and gitea-issue-directed
greps); the same-day, same-function `#general` thread (`g3.r2.s1d`) was caught by a different
keyword, but nothing ever swept `g3.r2.s1c`'s `#pipeline` slot.

**Other misses.** Six more clues never surfaced (`g3.r2.say23`, `g3.r1.l11`, `g3.r2.s2c`,
`g3.r1.l14`, `g3.r2.s2d`, `g3.r1.l10`), all confirmed absent by direct grep. None of these cost a
graded fact — each is redundant with other remarks that were found (e.g. `g3.r1.l14`'s "a waived
429 at attempts_left=0 still re-queues" is independently carried by `g3.r1.l15`/`rev1`, which the
agent did see and implement). The pattern across all seven misses is the same: the chat search used
head-capped keyword greps followed by ad-hoc `sed` windows around hits that looked interesting,
rather than a systematic per-channel/day sweep, so isolated threads whose wording didn't match any
issued keyword list were simply never read — unlike wiki (fully enumerated, comments recovered) and
mail (all three threads read whole).
