# g3 run 4 (rollout 62797bad, eval 035777f5, v9) — reward 1

## What this run found

This run cleared all nine graded facts. It cloned the repo, then ran a brute-force
dump-and-grep pass across every surface before writing a line of code: all 8 Mattermost
channels, all 228 BookStack wiki pages (fetched whole via `/api/pages/{id}`, comments
included — the correct technique given the ticket's own warning that search does not
index comments), and all 119 mailbox messages (over IMAP). It never wrote a single
narrowly-targeted lookup; instead it iterated through four progressively different chat
keyword passes (a broad identifier grep at L2150, an abandoned 1281-line context sweep
into `/tmp/ctx.txt` at L2374, a narrow `jitter|cooldown` grep at L1979, and a narrow
`throttle_waivers|THROTTLE_WAIVERS` grep into `/tmp/w.txt` at L2458), plus several
manually targeted channel/date-range reads. That combination surfaced 33 of 41 clues and
all 8 herrings/reversals. It found all 3 of the mail remarks it needed (`l8`, `s4d`, and
correctly missed `l12` — see below) and, despite doing the wiki dump correctly, missed
both wiki-comment remarks (`l5`, `s1a`).

The design was assembled into one consolidated synthesis at L5129 ("Design fully
gathered. Settled decisions to implement beyond the ticket...") rather than
remark-by-remark commentary — the agent read broadly, then wrote its understanding once,
correctly. That synthesis states, and the shipped `retry_policy.py` implements exactly:
a per-request `throttle_waivers_left` pool seeded from `DEFAULT_THROTTLE_WAIVERS = 6`
(free while waivers remain, then costs 1 like any other failure), `CONTRACT` costing 2
attempts, `TERMINAL` draining attempts but leaving waivers untouched, a verdict that
carries both `attempts_left` and `throttle_waivers_after` for the caller to write back,
`throttle_cooldown_until` on the tracker updated via `max()` from a single clock read
(never plain assignment), `remaining_cooldown_seconds` clamped to 0.0 and rounded to
three decimals, no jitter draw or schedule read on non-retry verdicts, and
`seconds_to_pause_on_rate_limit` left declared but unread. All four herrings (`g3.r1.h1`,
`g3.r1.h2`, `g3.r2.h1`, `g3.r2.h2`) were seen and correctly rejected in favour of their
reversals — verified directly against the shipped `_ATTEMPT_COST`/`record_on_tracker`
code, which follows none of the herrings' unconditional-zero or plain-overwrite
semantics.

## What it missed and why

Ten of the 49 remarks never surfaced, but none of them cost a fact — every requirement
is carried redundantly across enough sources that this run's gaps were always covered by
a substitute. The misses cluster into three real search-strategy weaknesses:

1. **Keyword-list gaps in chat** (`say23`, `l16`, `s2b`, `s2a`, `s4c`, `s4b`, and
   crucially `l1`): none of these six exchanges contain a literal hit in any of the
   agent's keyword lists (no bare `retry`, no `finish_reason`, no `pause`/`config` terms).
   `g3.r2.s2a` is a striking case — it contains "429" three times and should have been
   swept into the abandoned `/tmp/ctx.txt`, but the agent judged that file "too noisy"
   after reading only its first ~45 lines and never returned to it.
2. **Wiki dump correct, wiki keyword grep incomplete** (`l5`, `s1a`): the agent did the
   right thing — whole-page fetch of all 228 pages with comments — but the subsequent
   `throttle|jitter|backoff|cool_down|cooldown` grep over the dump returned only 8
   candidate pages, and neither meeting-notes page (whose comments, per the answer key,
   contain "backoff" and "throttle") was among them. Neither page was ever opened by ID.
3. **Verb-tense miss in mail** (`l12`): the mail grep looked for `retry|retries`, but the
   one relevant thread only uses "retried" — a form that literally does not contain
   either substring.

## The special check: g3.r1.l1 and the v9 rewrite

This rerun asked specifically whether the run saw the v9-rewritten #code-review
2025-06-03 14:12 thread (konrad's turn now reads "length does come good on a retry now
and then, so dont stop retrying it, it just shouldnt get as many goes as a timeout"
instead of the old terminal-sounding wording). **It did not.** A transcript-wide grep
confirms `world_code-review.txt` was only ever read through 2025-04-24 (L2717); no
command anywhere touches its May/June content. The thread's distinctive phrases
("finish_reason length", "spent four attempts", "shoudn't get that many goes") never
appear in the transcript.

Despite never seeing it, the run shipped the **correct post-v9 behaviour**: a
`ValueError("finish_reason was length")` is classified `CONTRACT` (cost 2, still
retryable, never made terminal). This happened for two independent reasons that made the
missing remark moot: (a) the ticket's own `classify_failure` signal-2 table maps
`ValueError` to `CONTRACT` by exception type alone, regardless of message text; and (b)
`g3.r1.l2` (#pipeline, 2025-06-26, found and explicitly dated in the design summary as
"CONTRACT costs two attempts (settled Jun 26)") plus `rev2`/`l13`/`l15`/`l17` (all found)
independently pin CONTRACT at cost-2-and-retryable from other sources. `g3.r1.l1` turned
out to be fully redundant for this run.

## Lost facts

None — `reward` is 1 and all nine facts scored 1. The run merged to `main` at `4b6bd68`,
CI (`build-test-deploy`) reported `success`, and the deployed service was confirmed
healthy and serving the pushed commit.
