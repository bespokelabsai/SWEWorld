# g3 run 3 (world-hosted v7, eval ce846459, rollout dbcedd39) — reward 1.0

## What this run found

This is a clean sweep: all nine graded facts (`g3.r1.rule/scope/exclusions_or_crossover/failure_behavior/observability`,
`g3.r2.rule/scope/exclusions_or_crossover/observability`) scored 1, CI was green for both commits
it pushed, and the release deployed. The agent's search infrastructure explains most of it: it read
the actual code first (base processor, all three provider processors, status tracker, config),
then **bulk-enumerated** rather than point-searched every external source — all 228 BookStack pages
with their comments (line 1656-2046), all 12 Mattermost channels' full history (line 2356-2431),
and all 119 mail messages (line 3391-3405) — before grepping locally and reading wide context
windows around every hit. That enumeration is exactly the workaround the answer key calls
necessary: it caught both comment-only wiki clues (`g3.r1.l5` and `g3.r2.s1a`, line 1787-2200,
which BookStack's own `/api/search` cannot index) and recovered 35 of 44 chat remarks and both
mail threads that mattered (`g3.r1.l8`, `g3.r2.s4d`) through a long, patient sequence of targeted
greps (waiver, verdict, throttle_cooldown, clamp/negative, jitter/ceiling, cool-down formulas) with
a final "June onward" pass that caught two late-breaking remarks (`g3.r1.l1`, `g3.r1.l4`, line
7206-7242).

## What it missed, and why it didn't matter

Of 49 answer-key remarks, 9 were never opened by the agent (`g3.r2.say23`, `s2a`, `s3a`, `s2c`,
`s4c`, `g3.r1.l7`, `l11`, `l12`(mail), `g3.r2.s2d`). Every one of these had its carried fact
independently delivered by at least one other remark the agent *did* find and read (e.g. the
max()-floor semantics for `g3.r2.rule` is stated four separate times across `s2b`/`rev1`/`rev2`/
`s1b`, so missing `s2a` cost nothing), by the ticket's own text (`g3.r1.l11`'s "no new config knob"
claim is literally already in the ticket: "attempts_left keeps its name and its seeding from
config.max_retries"), or by the agent's own correct code-reading (`g3.r2.s4c`'s "pause must not
derive from elapsed time since time_of_last_rate_limit_error" was satisfied because the agent
independently spotted and replaced the existing buggy `cool_down_if_rate_limit_error`, line
6676). The mail miss (`g3.r1.l12`) is a pure keyword-matching artifact: the agent downloaded all
119 mails but grepped for literal "retry"/"429"-style terms, and that mail's own wording
("retried five more times") doesn't substring-match "retry" — the same underlying fact (auth
failures should drain the attempt budget) was recovered instead from `g3.r1.l13` and the
"revoked key" mail thread it did find.

## What it believed, and why

All four herrings (`g3.r2.h1`/`h2`, `g3.r1.h1`/`h2`) were seen alongside their reversals — mostly
in the same grep sweep — and the agent correctly treated every herring as superseded. Its final
design implements the reversed positions exactly: `DEFAULT_THROTTLE_WAIVERS = 6` on `APIRequest`
(not "THROTTLE never deducts"), and `throttle_cooldown_until = max(existing, now + delay_seconds)`
(not a plain overwrite). Nothing in the shipped code reflects a herring position.

## One real deviation the grader didn't catch

The one substantive finding worth flagging: around line 7256-7368 the agent's final "June onward"
sweep surfaced `g3.r1.l1` (four attempts spent on a `finish_reason: length` failure), but the
*invented dialogue* around that remark in the world also has konrad conclude "it stops being
retryable, fail it out on the first" (line 7276) — which the agent took literally, adding a new
`InvalidFinishReasonError` mapped to `TERMINAL` (commit `d7a287b`, line 8406-8412) so that a
truncated-output failure now aborts immediately with attempts drained to zero. This contradicts the
answer key's own `g3.r1` observability table, which requires this exact case to classify as
`CONTRACT` (cost 2 attempts: `attempts_left=3 -> 1`, `attempts_left=1 -> 0, contract:exhausted`).
It cost nothing here only because `test_r1.py`'s finish_reason assertions construct a raw
`ValueError("finish_reason was length")` directly against `policy.decide()`, which still resolves
to `CONTRACT` through the ticket's own exception-type table — untouched by the agent's new,
grader-unreached exception class. This is the "invented scaffolding argues the opposite of the
golden answer" shape the reading instructions call out, and it happened not to be probed by this
particular test suite.

## Lost facts

None — reward 1.0 across all nine facts.
