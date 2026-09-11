# g3 run 4 (34a87e12, eval ce846459) — reward 1, all 9 facts scored 1

## What this run found

The agent built a comprehensive model of both hidden requirements *before* writing any code.
After cloning the repo and reading `base_online_request_processor.py`, it dumped the full
Mattermost corpus twice (`/tmp/chat.txt`, 11019 lines, all channels, no timestamps; then
`/tmp/chat_ts.txt`, timestamped), read all three mail threads over IMAP, and correctly fetched
both wiki pages via `/api/pages/{id}` — pulling the `comments` field rather than relying on
`/api/search` (which the ticket itself warns does not index comments). That got it both
comment-only clues (`g3.r1.l5`, `g3.r2.s1a`) cleanly (transcript lines 2435, 2445).

For chat it ran three successive keyword-grep passes rather than reading any channel start to
finish: `waiver|throttle_cooldown|retry_policy|...`, then `verdict|delay_seconds|should_retry|
attempts_made|reason_code|DEFAULT_THROTTLE`, then a broad case-sensitive sweep (`THROTTLE|
TRANSIENT|CONTRACT|TERMINAL|waiver|classif|verdict|decide|delay|jitter|exhaust|attempts_|
retry_polic|cooldown|...`) funneled into a 223-line `/tmp/design.txt` that it read almost
end-to-end. This caught 39 of the 49 planted remarks, including all four herrings and all four
reversals, both wiki comments, and all three mail threads (line 5275 is the agent's own
consolidated design summary, written before it touched `retry_policy.py`, and it is a
near-verbatim restatement of the full rule/scope/exclusions/failure_behavior/observability set
for both requirements).

## What it missed, and why it didn't matter

Ten clues never surfaced: `g3.r2.say23`, `g3.r1.l16`, `g3.r2.s2b`, `g3.r2.s1b`, `g3.r2.s2a`,
`g3.r2.s3a`, `g3.r2.s4c`, `g3.r1.l14`, `g3.r1.l7`, `g3.r2.s4b`. Nine of these are genuine
keyword-list misses — their wording ("budget"/"deduct", "shared counter", "a new wait lands
earlier", "fake clock", "retry_after to 45", lowercase "throttle" against a case-sensitive
`THROTTLE` grep) matches none of the three searched term lists, so no amount of re-reading the
same greps would have caught them; the agent simply never read those channel windows in full.
The tenth, `g3.r1.l14`, plausibly *would* have matched the design.txt filter (it contains
`attempts_left`) but sits chronologically inside a genuinely truncated tool result — the
design.txt read at step 57 was cut mid-stream by the harness itself
(`[... output limited to 10000 bytes; 626 interior bytes omitted ...]`, right after `g3.r2.rev1`
and before the next #pipeline entry, spanning exactly the 04-08→04-24 window that `l14` (04-10)
falls in).

None of the ten misses cost a fact. Each carries a fact that at least one other, found, remark
also carries — `g3.r2.exclusions_or_crossover` alone is carried by four remarks (`say23`, `s4c`,
`s4a`, `s4b`, `s4d`), and the agent found two of them (`s4a`, `s4d`, including the mail thread).
This is exactly what `spread_problems()`'s ≥2-source/≥3-week/≥2-channel gate is for.

## Herrings: all four seen, all four correctly superseded

The agent read every herring in the same grep passes that found its reversal, generally within
a few transcript lines of each other (e.g. `g3.r1.h2` at line 3116 and its reversal `g3.r1.rev2`
at line 2718, both from the same `waiver|throttle_cooldown|...` grep). Its running design notes
never adopted a herring's claim: the shipped `decide()` charges a THROTTLE failure once
`throttle_waivers_left` reaches 0 (not "never," per `g3.r1.h1`), and `record_verdict` writes
`throttle_cooldown_until = max(current, horizon)` (not a plain overwrite, per `g3.r2.h1`/`h2`).
`believed = "reversal"` for all four, and shipped code contradicts all four herrings.

## The coordinator's finish_reason check

**No** — the shipped code does not treat `finish_reason == "length"` as terminal. The
`raise ValueError(f"finish_reason was {generic_response.finish_reason}")` call site is byte-for-
byte unchanged from the original (transcript line 878 pre-edit, line 6147 post-edit sanity
check) — no new exception class, no call-site reclassification. In `classify_failure`,
`ValueError` is matched by the exception-type signal (2), which returns `CONTRACT`
*before* the message-marker signal (3) is ever consulted — so this is structurally guaranteed
CONTRACT, not an accident of what the message string happens to say. `_ATTEMPT_COSTS[CONTRACT]
= 2` and CONTRACT stays retryable, matching the answer key.

Konrad's misleading 2025-06-03 turn — "and length wont fix itself on a retry anyway, so it stops
being retryable, fail it out on the first" — was **never shown to the agent**. Its only view of
that `#code-review` thread came from a `grep` on the bare substring `reason`, which matched only
the exchange's opening line (nikolai, "finish_reason length every time...") and closing line
(nikolai, "log line should say which reason it was too") — the three turns in between, including
Konrad's line, contain no occurrence of "reason" and were skipped entirely. A direct substring
search across the whole transcript for "fail it out", "wont fix itself on a retry", and
"shoudn't get that many goes" confirms none of that text ever appears. The agent's correct
CONTRACT/two-attempts conclusion instead came from the companion remark `g3.r1.l2` (2025-06-26,
found and read in full at line 3711: "two attempts off for a malformed-output failure ...
doesn't spend a throttle_waivers_left pass though, thats for 429s").

## End state

Normal, complete run. Module written to spec, wired into the base processor exactly as the
ticket and the record required, double-counting removed from the three provider processors, 59
new unit tests passing, commit `beb7d6d` pushed to `main`, CI green (`ci / build-test-deploy —
Successful`), deploy confirmed live at `curator.world.local`, and a final import check confirms
both the tracker's `throttle_cooldown_until` field and `APIRequest`'s new fields exist exactly as
specified.
