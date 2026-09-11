# g3 run 1 (eval ce846459, rollout ccc381f3) — reward 1

## What this run found

This is a clean success: all nine graded facts (`g3.r1.{rule,scope,exclusions_or_crossover,failure_behavior,observability}`,
`g3.r2.{rule,scope,exclusions_or_crossover,observability}`) scored 1. The agent cloned the repo,
pulled all 736 Gitea issues with comments into a local file, dumped the full Mattermost chat
(10,297 lines) and all 119 mail messages via IMAP, and — after discovering BookStack's `/api/search`
doesn't index page comments — wrote a paginated `/api/pages` dump that recursively walks each page's
nested comment tree (fixing two real bugs along the way: comments first came back as an empty dict,
then were found to live in a `{comment, children}` tree that needed recursive extraction, lines
2616–4632). It grepped all three corpora for uppercase design tokens (`THROTTLE`,
`DEFAULT_THROTTLE_WAIVERS`, `decide`, `attempts_made`, …) and read the surrounding exchanges in full,
explicitly tracking chronology to separate a herring from its reversal: *"Jan discussion said plain
assignment, but the Mar 24 and Apr 8 discussions explicitly changed it to max(). Latest wins: max()."*
(line 4132). Both `g3.r1`'s herrings (Feb 6 "THROTTLE costs 0, no ceiling", Mar 12 "no ceiling on it")
and both `g3.r2`'s herrings (Jan 21/22 "plain assignment") were seen, correctly recognized as
superseded, and never followed in code.

The shipped `retry_policy.py` matches the answer key near-verbatim: `DEFAULT_THROTTLE_WAIVERS = 6`,
`APIRequest.throttle_waivers_left`, `decide()` taking `throttle_waivers_left` as a third keyword and
returning `attempts_left_after`/`throttle_waivers_after`, a waived-THROTTLE branch that ignores
`attempts_left` entirely (so a 429 at `attempts_left=0` with waivers left still retries), a TERMINAL
branch that drains `attempts_left` to 0 while leaving waivers untouched, `record_verdict()` reading
the clock exactly once and writing `tracker.throttle_cooldown_until = max(current, horizon)`, and
`remaining_cooldown_seconds()` clamped at 0.0 and rounded to three decimals at the source. 63 new unit
tests pass, ruff was matched against CI's exact pinned version (0.8.6, after a false start with a
newer local binary that flagged 142 spurious errors — lines 7241–7398), the change merged to main as
`a2d6a41`, and before marking the task complete the agent independently found the deployed release
directory on the host filesystem and confirmed `retry_policy.py` was actually there, rather than
trusting CI's "green" status alone.

## What it missed, and why it didn't matter

Of the 49 planted remarks, 14 clues never surfaced anywhere in the transcript (verified by direct
grep against the transcript, not just trusting the pointer sheet). Twelve of these share one
mechanical cause: the agent's grep passes were tuned to uppercase design tokens, and these remarks
are phrased in ordinary lowercase prose with no unique searchable token — e.g. `g3.r1.l7`'s "one
shared counter for the run... free passes" (#engineering, Apr 15) was never read, even though the
agent *did* read the phrase "free passes" elsewhere — it belongs to `g3.r1.l8`, a different remark, in
the mail thread. The channel/day for each of these 12 was simply never opened by any other route.

The other two misses are the wiki page comments, `g3.r1.l5` and `g3.r2.s1a`. These are more
interesting: the agent's final wiki-dump script (`wiki3.py`) does paginate every page via
`/api/pages?count=100&offset=...` and does recursively walk comments — a genuinely thorough,
comment-aware pass — but it dedupes pages by display **name** (`if p["name"] in seen: continue`)
rather than by id. The transcript's own page listings show the corpus serving duplicate-titled pages
under two different ids ("Weekly Notes — Week of Mar 31" at both id 66 and 186, "Handover:
Request-Processing Core and Provider Backends" at both 17 and 137, and others, lines 1716–1745),
which is consistent with this task having run against the pre-deduplication `sweworld:0.4.4` image.
If the two "meetings/" pages carrying these comments have same-titled twins, the name-based dedup
would silently keep one copy and drop the other. The final comment dump surfaced only 17 comments
sitewide, none about the retry policy — a suspiciously clean miss for an otherwise careful pass.

Neither miss cost a fact. `spread_problems()` guarantees every requirement at least two sources and
two channels, and in this run every fact that these 14 remarks carried had a redundant carrier the
agent *did* find: `g3.r1.l5`'s `DEFAULT_THROTTLE_WAIVERS=6` was independently carried by `g3.r1.rev2`,
`l6`, `l8`, `l9`; `g3.r2.s1a`'s field-placement rule was carried by `g3.r2.s1b/s1c/s1d`. The agent's
own three design-synthesis passes (lines 2817, 5236, 8861/8906) show it converging on the same
complete picture each time regardless of which individual remarks it had or hadn't seen.

## Believed vs. followed

For all four herring/reversal pairs the agent registered the reversal as the final decision and
shipped code that matches it, never the earlier herring — confirmed both by its own Analysis text
(lines 2817, 3981, 4132) and by reading the shipped `decide()`/`record_verdict()` code directly. No
fact was lost to a herring being followed, to a misread remark, or to a corpus contradiction; this is
a full, correctly-reconstructed pass against the answer key.
