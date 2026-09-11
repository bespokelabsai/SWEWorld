# g10 run 8 (world-hosted v5, eval 5b468409, rollout b2357bac) — reward 0

## What happened

The reward is 0, but not because the agent failed to find or understand the hidden requirements — it
found and correctly reconstructed almost all of both `g10.r1` (the -25% debt floor) and `g10.r2`
(settle vs. refund) well before it started writing code, and then *implemented them correctly*. The
run failed because **it never committed or pushed anything**. A grep of the entire 200-step transcript
for `git commit`, `git add` and `git push` returns zero hits. `provenance.pushed=0`,
`ci_green=0`, `deployed=0` are literal: the graded submission is byte-identical to the untouched repo,
which is exactly why every failing test bottoms out at the same two boundaries — `test_open.py` and
`test_r1.py` fail because `bespokelabs.curator.status_tracker.capacity_budget` does not import at all
(the module file was never in the submission), and `test_r2.py` fails one step later because
`OnlineStatusTracker.__init__()` has no `capacity_clock` keyword (the tracker rewrite was never in the
submission either).

## The search

The agent's search was thorough in coverage but read by keyword window rather than exhaustively:
it cloned the repo and read the existing tracker/processor code in full (steps 1-25), checked Gitea
issues/PRs (nothing relevant), pulled every BookStack wiki page via the REST API *including comments*
(steps 31-40 — correctly unproductive, since none of this task's 46 remarks live in the wiki), dumped
every Mattermost channel to files and grepped for `capacity_budget`, `refund`, `debt`, `floor`, `clamp`,
`CAPACITY_DEBT_FLOOR_FRACTION`, `num_capacity_*`, etc., reading fixed line windows around each hit, and
pulled all mail over IMAP (also correctly unproductive). Two synthesis passes — step 64 (line 3543) and
step 125 (line 6659) — assembled the full picture: the 0.0-clamp herring reversed into a per-axis debt
floor at `-CAPACITY_DEBT_FLOOR_FRACTION * limit` counted once per call regardless of how many axes
clamped, and the merged-`_free_capacity` herring reversed into distinct `free_capacity`/`refund_capacity`
operations with independent `num_capacity_settlements`/`num_capacity_refunds` counters, both terminal
failure paths (requeued and exhausted) refunding. Both herring/reversal pairs were correctly resolved in
favour of the reversal, with no sign the agent ever considered building to the herring.

13 of 46 remarks (28%) were never surfaced — confirmed by grepping the transcript for each remark's
distinctive wording, not just trusting the pointer sheet. They cluster in `#pipeline` (12 remarks total,
the densest channel) and `#engineering`/`#general`/`#help`; `#help` (carrying `g10.r2.s1_l1`, "estimator
books 1k output tokens on every haiku call") was never dumped or searched at all. This had no effect on
the outcome: every subconclusion had 3-4 redundant clues, and enough survived in each case for both
syntheses to land on the right rule, scope, exclusions and observability for every fact.

## What it built, and why it doesn't matter

Starting at step 126 (line 6713) the agent wrote `capacity_budget.py` from scratch, then rewrote
`OnlineStatusTracker` (the `capacity_clock` field, per-axis `_debt_floor`, `free_capacity` gone-negative
settlement, `refund_capacity`, `num_capacity_debt_clamps`/`num_capacity_settlements`/`num_capacity_refunds`)
and `BaseOnlineRequestProcessor` (`_reserve_capacity`, `_free_capacity`, `_refund_capacity`, both retry-path
release call sites). A smoke test it ran itself (line 7902-7912) shows this working: `"after settle -10.0
1"` — a tracker seeded to floor at -25%, correctly gone negative, with the clamp counter at exactly 1.
This is real, behaviourally-verified, correct work. None of it reached Gitea.

Instead of committing once the implementation was smoke-tested (around step 166), the agent spent its
remaining budget (steps 183-200) writing its own unit-test file in tiny single-line-redirect increments,
fighting the sandbox's own JSON/heredoc escaping the whole way — 61 of 200 steps produced "Extra text
detected after JSON object" warnings and 65 produced terminal-idle watchdog warnings. The transcript ends
mid test-append at step 200 (line 10474), having created a branch (`feat/capacity-budget`, step 125) it
never committed to.

## Why every fact reads "infra"

All eight declared facts (`r1`/`r2` × `rule`/`scope`/`exclusions_or_crossover`/`observability`) are
scored `lost_facts` with cause `infra`: the assertions that fail are not about the *content* of the
implementation (which matched the answer key's rule/scope/exclusions/observability on inspection of the
diffs) but about whether the module and the constructor keyword exist in the graded submission at all —
and they don't, because the run never pushed. Per the reader instructions this is the textbook case of
"nothing pushed because the run died": here "died" means it ran out of its 200-step budget while doing
unrequired, low-value work (its own tests) after the requested change was already complete and verified,
rather than banking the win with a commit and push first.
