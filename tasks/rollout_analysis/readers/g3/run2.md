# g3 run 2 (c81e9802) — reward 1, all 9 facts passed

## What this run did

Given only the ticket, the agent cloned `curator`, read the four target files and the
`OnlineStatusTracker`, then systematically exhausted every source the world offers: Gitea
issues (dumped all 736 with comments and grepped locally after the search API returned
nothing), BookStack wiki pages, Mattermost chat across all 12 channels, and IMAP mail. It hit
and recovered from the world's two deliberate traps on its own: (1) the admin account isn't a
channel member, so `/users/me/teams/.../channels` came back empty — it switched to the
system/team-wide channel-listing endpoint; (2) its first BookStack dump serialized comments as
bare `"active"`/`"archived"` strings, silently losing their content — it noticed, and re-ran a
dedicated `/api/pages/{id}` pass to recover the real comment bodies. That second catch is what
surfaced both wiki-comment remarks (`g3.r1.l5`, `g3.r2.s1a`), which BookStack's `/api/search`
does not index at all.

From there the strategy was grep-and-read: an escalating series of targeted greps over the
normalized chat dump (`retry_policy|waiver|throttle|classif|verdict|failure_class|cooldown`,
then `retry.after|retry_after`, `time_of_last_rate_limit_error|cool_down|pause`,
`attempts_made|pass count`, `attempts_left`, `reset`), each followed by reading the full
surrounding exchange rather than trusting the single matched line. It consolidated everything
into `/tmp/retry_chat.txt` and read that end to end before writing code. This is why the run
found essentially the entire plant: all 41 clues, all 4 herrings and all 4 reversals surface in
the transcript, most of them read in their full multi-turn context rather than as an isolated
line.

## What it believed, and why

For every herring/reversal pair (`g3.r1.h1`/`rev1`, `g3.r1.h2`/`rev2`, `g3.r2.h1`/`rev1`,
`g3.r2.h2`/`rev2`) the agent read both the original decision and its later reversal in the same
grep pass or the same wide `sed` read, and its synthesis (transcript line 5021) states only the
reversed positions: waivers on `APIRequest` (not a flat ban), and `max()` cooldown-floor
semantics (not plain overwrite). Nothing in the shipped code reflects a herring.

## The rewritten thread (v9)

v9 rewrote konrad's 14:12 turn in the `g3.r1.l1` thread (2025-06-03, #code-review) from "length
stops being retryable, fail it out on the first" to "length does come good on a retry now and
then, so dont stop retrying it, it just shouldnt get as many goes as a timeout." The agent read
this exact exchange in full at chat.txt:2975–2995 (pulled up via "Line 2983 ... interesting,
let's read 2975,2995" — transcript line 3919). It never separately re-quotes konrad's 14:12 line
in its own Analysis, but the fact it needed from the thread — that a truncated-output failure is
still retried, just pricier than a timeout — is exactly what shipped: `classify_failure` sorts
`ValueError` into `CONTRACT` per the ticket's own table, and `_ATTEMPT_COST[CONTRACT] = 2` (set
from the independently-read `g3.r1.l2`, dario 2025-06-26: "a CONTRACT/malformed-output failure
costs TWO attempts off the budget," transcript line 4346). A `finish_reason == "length"` failure
is therefore charged 2 attempts and remains retryable until the budget can't cover another 2 —
never made terminal or non-retryable. This matches the rewritten remark, not the old wording, and
is corroborated by the answer key's own observability table (`attempts_left=3 → 1` on a length
failure).

## Why every fact scored 1

Each of the nine facts traces to multiple independently-read remarks rather than one lucky hit:
`r1.rule` to the waiver-mechanism reversal chain plus the cost-table remarks (l1/l2/l3/l4/l9/l10);
`r1.scope` to l11/l7/l6/l10 (no new config knob, per-request not per-run, lives on `APIRequest`);
`r1.exclusions_or_crossover` to l13/l14/l15/l12 (terminal drains attempts but not waivers; a
zero-cost throttle at `attempts_left==0` still re-queues); `r1.failure_behavior` to
l16/l17/say23/l18/l19/say24/rev1 (charge-then-test ordering, clamp at 0 not negative, no
delay/jitter on non-retry); `r1.observability` to l1/l5/l13/l15/l17 (the wiki comment giving
`DEFAULT_THROTTLE_WAIVERS = 6` literally); `r2.rule` to s1a/s2a/s2b/s2c/say19/s2d/rev1/rev2 (the
other wiki comment giving the exact field name and default, plus the `max()` formula literal);
`r2.scope` to s3a/s3b/s3c/say20/say21/say22 (which counter each class touches, and that only
THROTTLE reads the clock); `r2.exclusions_or_crossover` to say23/s4a/s4b/s4c/s4d (the config knob
stays but goes unread, the wait must come from the failure's own backoff); `r2.observability` to
s1c/s1d/s2c (the exact clamp/round and worked numeric examples). The agent's own mid-run sanity
script reproduced several of these worked examples verbatim (`delay_for(THROTTLE,1)==5.0` at
clock=1000/jitter=0.25; `remaining_cooldown_seconds` giving 3.0/0.0) before wiring the module in,
which is strong evidence it understood the numbers rather than pattern-matching field names.

No facts were lost. `lost_facts` is empty.
