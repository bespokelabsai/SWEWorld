# g10 run 1 (eval 5b468409, rollout f29b27b5) — reward 1

## What this run found

The agent cloned the repo, checked Gitea's closed/parked issues (finding #401, the parked
capacity-seeding design), pulled the whole wiki in the background, then authenticated to
Mattermost and ran the team's own chat-search endpoint with a first pass of generic terms
— `capacity, rate limit, tpm, budget` (step 34, transcript lines 2850-3050). That single pass
was disproportionately productive: because all four herrings, all four reversals, and most of
the `say*`/`s5_*` observability clues happen to use the literal word "capacity", it surfaced
30 of the corpus's 46 remarks in one shot, including the two remarks that do almost all the
work — `g10.r1.rev1` (line 2879: the 0.0 clamp is gone, floor at `-CAPACITY_DEBT_FLOOR_FRACTION
* limit`, 0.25) and `g10.r2.rev1` (line 2867: success settles via `free_capacity(used, blocked)`
with the slot staying spent, failure refunds via `refund_capacity(blocked)` plus the 1.0 slot).
The agent then iterated with identifier-name searches — `CAPACITY_DEBT_FLOOR_FRACTION` (step 46),
a batch of `num_capacity_*`/`limit_origin`/`capacity_clock`/`exceeds`/`unlimited`/`reservation`
(step 49), then `has_capacity`/`consume_capacity`/`available_token_capacity`/etc (step 71) —
dumping whole channel files to `/tmp/mm/*.txt` and printing wide context around each hit. By
step 92 (line 5418) it had assembled a synthesis (line 5518, restated at 6175) that states
essentially the full content of both hidden requirements: the free/refund split with exact
signatures, the debt-floor constant and its herring's supersession, and all three counters with
call-not-axis, counts-even-on-unlimited-axes semantics.

## What it missed and why

16 of the 46 remarks never surfaced — I grepped the transcript directly for each one's
distinctive wording (`quarter of the minute's alowance`, `240 calls`, `split limit config`,
`haiku`, `503`, `attemtp`, `settle threw doing arithmetic on a None`, `minute two should open
owing`, etc.) and confirmed genuine absence, not truncation. The pattern is consistent: every
missed remark is phrased without the word "capacity" and without any of the later
identifier-name search terms the agent actually used — e.g. `g10.r2.s1_l1` ("estimator books
1k output tokens on every haiku call, actual comes back under 150") and `g10.r2.s2_l1`
("gemini 503'd on everything last night ... down to one request every few seconds with zero
successes") describe the same facts in plain incident language that a keyword search for
"capacity"/"reservation"/identifier names would never catch. This is a real, if narrow, search
gap — a channel-by-channel full read (rather than global keyword search) would likely have
caught them. It cost nothing here because the plant's redundancy meant every one of the 8 graded
facts had 2-6 *other* found carriers, several of them reversal messages that restate the whole
settled design in one turn.

## What it believed, and why

All four herrings were correctly identified as superseded. Two (`g10.r1.clamp-at-zero-decision`,
`g10.r1.clamp-at-zero-rationale`) were read directly (lines 3336, 3489) alongside their
reversals in the same wide chat dump, and the agent's own Analysis at line 3351 states the
"two eras of decisions" framing explicitly before implementing the later one. The third
(`g10.r2.h1`) was read via its reversal's restatement (line 2873, inside `g10.r2.rev1`'s
opening line "we settled this months ago, one `_free_capacity`..."). The fourth (`g10.r2.h2`)
was **never independently fetched** — the agent only ever saw its content because
`g10.r2.rev2` (line 3991) quotes it verbatim before overturning it ("thats the old plan and its
dead ... the code does neither half"). In all four cases the agent believed the reversal, not
the herring, and the shipped code implements the reversed design throughout (`free_capacity`
returns only the gap and keeps the slot spent; `refund_capacity` is a separate operation
returning the whole booking plus the slot, clamped).

## Why each lost fact was lost

None — all 8 graded facts scored 1 and `suite_ok`/both provenance checks are green
(PR #737 merged, CI green, release `ea497c3` deployed and health-checked, lines 10238/10289).
The agent's final self-summary (lines 10230-10291) independently restates the debt floor,
the counter semantics, and the free/refund split closely enough to explain the clean pass —
and its step-9505 pre-push checklist explicitly re-verifies three specific remarks by name
against the diff before marking the task complete, which is unusually disciplined
self-verification for this task.
