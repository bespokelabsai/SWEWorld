# g10 run 6 (eval 5b468409, rollout 1e9edef5) — reward 0.875

## What this run found

The agent's process was solid: it read the source files whole before touching the world, then
dumped **every** Mattermost channel's full history to `/tmp/chat/<channel>.txt` (transcript line
3283) and downloaded **every** wiki page with its comments to `/tmp/wiki/` (line 2530), so nothing
was excluded by a search index gap the task's own notes warn about. From there it worked almost
entirely by `grep -rn '<literal identifier>' /tmp/chat/` for terms it already suspected mattered
(`CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_debt_clamps`, `refund_capacity`, `attempts_left`,
`finish_reason`, `available_request_capacity`/`available_token_capacity`), reading a thread in full
once a hit landed. That got it 33 of 46 remarks and all four herring/reversal pairs.

It correctly recognized both herrings (the "clamp debt at 0.0" design and the "one `_free_capacity`
call for both outcomes" design) as superseded, and shipped code that follows both reversals: a
negative-going, floor-bounded `free_capacity` (`CAPACITY_DEBT_FLOOR_FRACTION = 0.25`, line 3199),
and a separate `refund_capacity` that returns the whole blocked estimate plus the request slot on
failure while `free_capacity` leaves the slot spent on success (line 3802-3803). `r1.rule`,
`r1.scope`, `r1.observability` and all four `r2` facts scored 1 on real remarks, not guesses.

## What it missed, and why

**`g10.r1.exclusions_or_crossover` scored 0** — `test_exclusions__capping_at_the_limit...` fails
on `released.available_token_capacity == 1000.0` (capped) vs. the actual `1800.0`. This is a real
implementation gap: the shipped `free_capacity()` (splice command at message 253) applies
`_apply_debt_floor()` — a **lower**-bound-only clamp — to the settled value, but never applies an
**upper** cap. `update_capacity()`'s refill correctly does `min(available + refill, limit)`; the
settle path never does the equivalent `min(...)`. The agent's own pre-code requirements summary
(line 6033) lists `free_capacity` as "settle with debt floor... counts num_capacity_settlements and
num_capacity_debt_clamps" with no upper cap anywhere in the plan — it never registered that the
ceiling applies to *both* capacity-changing operations, only to refill.

The remark that says this outright — `g10.r1.g10.r1.s4.l3`/`s4.l4`, a #code-review Mar-19 exchange
opening with "what happens when a release hands back a big over-reservation?" and ending "same goes
for the release side then" — was never read whole. The agent's debt/clamp/floor grep sweep (step
84, line 4494) matched only two isolated lines out of the six-line exchange (`code-review.txt:2003`
"no it clamps at max_tokens_per_minute it doesnt add through past it" and `:2004` "does that clamp
get counted anywhere"), missing both the opening line that frames it as being about *release* and
the closing line that ties it to `free_capacity` explicitly. A prior turn explicitly planned "Read
code-review 1998-2012" (line 4595) but the next tool call substituted a keyword grep instead, and
that planned read never happened. Grepped for directly, "hands back a big over-reservation" and
"same goes for the release side" appear nowhere else in the transcript — the framing was genuinely
never seen, not misread.

## The 13 unfound remarks

13 of 46 remarks never matched any grep query the agent ran (confirmed by direct grep for each
one's distinctive phrasing — zero hits) — things like "240 calls into a 200 minute" (`r2.s1_l3`),
"thirty real requests a minute agaisnt a sixty ceiling" (`r2.s2_l3`), and "the row where the caller
passed 0 is A" (`r1.s2.l2`). None of these cost a fact on their own: every subconclusion with a
missing leaf still had another leaf that surfaced and carried the same information (the plant's
redundancy doing its job), except `r1.s4` ("reaching the top of a bucket is not the counted
event"), where the one leaf that named the *release* path specifically was seen only as a
decontextualized fragment.

## Bottom line

This is a well-executed, mostly-successful run undone by one gap: applying the ceiling-cap idea to
the refill path but not the release/settle path, traceable to a planned full-context read that got
replaced by a narrower grep and never came back.
