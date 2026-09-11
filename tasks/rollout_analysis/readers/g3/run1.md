# g3 run 1 (c77a4f1b, eval 035777f5, v9) — reward 1

## What it found

This run cleared all nine facts. Its search was thorough and escalating: a few targeted
Mattermost keyword searches first, then a wholesale dump of every channel's full history
(~10k messages across 11 channels) to local files, grepped repeatedly with wide context as
the list of design terms grew (`throttle_waivers`, `throttle_cooldown_until`, `terminal`,
`jitter`, `backoff`, `cooldown`, `attempts_made`, `verdict`...). Critically, it read the
*full thread* around every grep hit rather than trusting the matched line, which is how it
caught both g3.r1 herrings (Feb 6, Mar 12) side by side with their reversals (Apr 9, Mar 20)
and reasoned correctly about which was superseded by date ("Feb 6 decision (throttle free)
was superseded by Mar 20 (waiver pool)", line 3585). Same pattern for g3.r2's
`throttle_cooldown_until` herrings/reversals (line 3031). The wiki was enumerated whole via
`/api/pages/{id}` (228 of ~244 pages, comments included) rather than search alone, exactly
as the ticket warned was necessary — both wiki-comment clues (`g3.r1.l5`, `g3.r2.s1a`) were
caught this way. Mail was read via IMAP; the two most load-bearing threads (revoked-key
incident carrying `g3.r1.l8`, 429-handling carrying `g3.r2.s4d`) were opened in full. Gitea's
736 issues were dumped and correctly ruled out as carrying nothing on this ticket.

The reconstructed `retry_policy.py` (pulled from the raw tool-call JSON, since the
transcript itself only shows truncated heredocs) matches the answer key point for point:
`DEFAULT_THROTTLE_WAIVERS = 6`, `_ATTEMPT_COSTS = {THROTTLE:1, TRANSIENT:1, CONTRACT:2,
TERMINAL:0}` with THROTTLE overridden to 0 while a waiver remains, the budget check
`remaining < 0` evaluated *after* the deduction, `throttle_cooldown_until` placed
immediately after `time_of_last_rate_limit_error` and updated only via `max()`,
`remaining_cooldown_seconds` clamped at `0.0` and rounded to three decimals, both
`attempts_left` and `throttle_waivers_left` written back onto the request, and the three
provider processors' compensating counter decrements removed.

## What it missed, and why it didn't matter

Eight of 49 remarks (16%) were never surfaced at all: `g3.r1.l1`, `g3.r1.l12`, `g3.r1.l16`,
`g3.r2.say21`, `g3.r2.say23`, `g3.r2.s2a`, `g3.r2.s2d`, `g3.r2.s4c`. One herring (`g3.r1.h2`)
was only partially surfaced — a single incidental line from its own thread showed up in a
themed grep, and its real content ("no ceiling on it, THROTTLE never deducts") was obtained
secondhand, through konrad's own recap of it inside the Mar 20 reversal exchange rather than
by reading the herring's thread directly. None of this cost a fact: `spread_problems()`
guarantees every requirement at least 2 sources, 3 weeks and 2 channels, so each fact had
redundant carriers and this run happened to read enough of them. `g3.r1.l12` (a mail thread,
"smoke run timings on the wiki before we cut 0.1.26") is the clearest example — its subject
line was seen in the mailbox index (transcript lines 2023-2030) but its body was never
opened, yet `g3.r1.exclusions_or_crossover` still scored 1 via `l13`/`l14`/`l15`/`rev1`, all
read in full.

## The rerun's specific question: g3.r1.l1 and the finish_reason=="length" thread

This version rewrote konrad's 14:12 turn in the 2025-06-03 `#code-review` thread that seats
`g3.r1.l1` — the thread was never surfaced by this run. Grepping the transcript for every
distinctive phrase from that remark and its surrounding exchange ("four times last night",
"broken payload", "shoudn't get that many goes", "does come good on a retry", "retry log
from last night is odd") returns zero hits, and a direct check confirms the agent's chat
searches never dumped `#code-review` for 2025-06-03 at all — every hit for that date is in
`#general`, `#incidents`, or one unrelated `#viewer` line. So this run saw neither the old
nor the new wording of konrad's turn.

That did not stop it from shipping the right behavior, though for a reason unrelated to
`g3.r1.l1`: the ticket's own `classify_failure` table already routes `ValueError` to
CONTRACT via the exception-type/MRO signal, and `finish_reason was {reason}` is raised as a
`ValueError` elsewhere in the codebase (transcript line 1012) — so the *classification* came
straight from the ticket, not from a hidden requirement. The hidden half — that CONTRACT
costs 2 attempts and stays retryable rather than being made terminal — was reconstructed
independently from `g3.r1.l2` (`#pipeline`, 2025-06-26: "two attempts off for a
malformed-output failure sounds right to me, one is too generous"), which *was* found,
together with `l17`/`say23`/`rev1`/`rev2`/`l15`. The shipped code has no special-casing of
`length`/`finish_reason` as terminal; a `finish_reason=="length"` `ValueError` is classified
CONTRACT, charged 2 attempts, and stays retryable until `attempts_left - 2 < 0` — matching
the answer key's `g3.r1.observability` row (`attempts_left=3 -> 1`; `attempts_left=1 ->`
`contract:exhausted` at `0`, never `-1`) exactly, arrived at without ever reading the remark
the answer key attaches that value to.

## Herrings

All four herring/reversal pairs (`g3.r1.h1`/`rev1`, `g3.r1.h2`/`rev2`, `g3.r2.h1`/`rev1`,
`g3.r2.h2`/`rev2`) were resolved correctly toward the reversal. The shipped code matches the
reversed design in every case (waiver pool with a 6-count cap, and `max()`-only cooldown
extension), never the original herring position.

## End state

Ticket complete: merged to `main` at `7b4b24a`, CI run #3 green, deploy verified through the
release symlinks (`current`/`last-good` -> `20260911154241-7b4b24a`) rather than the health
endpoint, which the agent correctly identified as returning only static status JSON after
briefly appearing to misread a `commit` field from it.
