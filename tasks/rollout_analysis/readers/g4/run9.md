# g4 run 9 (e157d675, eval 0ebb2b86) — reward 0

## What happened

This is a **provenance failure, not a comprehension failure**. The agent implemented an unusually
complete and correct version of both hidden requirements from real chat archaeology, then ran out
of its 200-step budget before it could get any of that work onto `main`.

The transcript ends (l.11178-11185) one tool call after the agent's *first genuinely real* local
commit — `2825c31 feat: versioned run identity for the curator cache`, 10 files changed including
`src/bespokelabs/curator/run_identity.py`. There is no push, no PR, no merge after it. The pointer
sheet's `provenance.pushed=0 / ci_green=0 / deployed=0` all confirm nothing reached Gitea `main`,
so the grading snapshot's `bespokelabs.curator.__init__` never exported `run_identity`, and every
r1/r2 test fails at the shared `importable()` guard before any content assertion runs — hence all
8 declared facts read 0 regardless of whether the underlying code was right.

**Why it never pushed:** starting around l.9682, the agent's terminal repeatedly echoed stale or
outright fabricated output. It believed several times that it had already added tests, committed,
pushed, opened a PR, and merged — then discovered each belief was false by re-deriving ground
truth from fresh commands ("the earlier commit screens were fabricated/stale" l.10823, "Terminal
output has repeatedly shown stale/fabricated content" l.11085, "Earlier commit/push/PR/merge
outputs were not real" l.11136). This loop consumed roughly the back half of the run's step
budget. `[horizon watchdog]` messages fired repeatedly telling it to stop polling and try a
different approach.

## What it found

Using only Mattermost (the answer key confirms g4 has no wiki/mail carriers), the agent dumped the
full chat export (11,045 lines, l.2380-2440) and ran a widening sequence of greps — from the
obvious `run_identity|identity_version|...` (l.2411) out to thematic passes on `digest`,
`disable_cache`, `uuid4`, `backend_params`, `base_url`, `column`, `twelve`. It read generous
context windows around hits rather than single lines, which is how it recovered remarks whose
literal keywords weren't in its grep list. By its own running summary at l.6524 it had correctly
reconstructed: the 12-key alphabetical `IDENTITY_COMPONENT_KEYS` tuple (including the
`parse_func_hash`/`prompt_func_hash` naming nuance it initially got wrong at l.3998 and
self-corrected at l.4756 after reading the relevant #engineering exchange), the
`batch_mode`-above-`backend` ordering nit, `IDENTITY_BACKEND_PARAM_KEYS = {base_url,
azure_deployment, batch_size, completion_window}` excluding `api_key`/`max_retries`/
`request_timeout`, `response_format` as sorted compact JSON or `"text"`, resolved `backend` and
copy-semantics `backend_params` properties, `run_id` keyword-only threaded from `__call__` with a
`CURATOR_RUN_ID`-then-`uuid4` default, both `RunIdentityError` refusals (cached+run_id,
disabled+empty/None), and the `v3-nocache-` prefix with no timestamp segment. All of this was
actually written into `run_identity.py` and wired through `llm.py`/`db.py`/`curator_response.py`/
`base_request_processor.py`.

## Herrings — all three resolved correctly

The corpus plants two flavors of herring for each requirement (whole-dict `backend_params`
hashing for r1; `uuid4`-mint and isoformat-segment for r2), each with a later reversal. The agent
saw every herring, initially adopted each one as a "settled decision" in its running notes, then
read the reversal and updated its position before writing code — in every case landing on the
reversal, never the herring, in what it actually shipped (`IDENTITY_BACKEND_PARAM_KEYS` filter,
caller-supplied `run_id`, no-timestamp `v3-nocache-` hash).

## What it missed

8 of 48 remarks were never surfaced by the agent's grep vocabulary (`l-retries-fork`,
`l-window-reuse`, `g4.r2.l1`, `g4.r2.l2`, `l-backend-resolved`, `l-genparams-empty`,
`l-genparams-fix`, `l-system-prompt`) — mostly because its keyword list never included plain terms
like `max_retries`, `completion_window` alone, `flake hunt`, or `system_prompt`. Every one of
these facts, however, is redundant with a remark the agent *did* find and act on, so no unique
requirement content was actually lost — it's a search-coverage gap with zero net cost to the
final design.

## Why each declared fact was lost

All 8 (`g4.r1.rule/scope/exclusions_or_crossover/observability`,
`g4.r2.rule/scope/failure_behavior/observability`) fail for the identical reason: the graded
submission's `bespokelabs.curator` package does not export `run_identity`, because nothing was
ever pushed to `main`. Cause = **infra** for all eight — this is "nothing pushed because the run
died" (the reader instructions' own canonical example of an infra cause), not a corpus
contradiction, a herring followed, or a misread remark. The irony is that had the run gotten even
~10 more turns to actually execute `git push` / open and merge a PR, this rollout likely would
have scored close to the `clues`-arm ceiling on content alone.
