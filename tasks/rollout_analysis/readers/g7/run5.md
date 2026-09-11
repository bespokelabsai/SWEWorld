# g7 run 5 (world-hosted v5, eval 8deffce4, rollout 8a514932) — reward 0

## What this run found

The agent's chat/wiki/mail exploration was thorough enough to reconstruct **both** hidden
requirements almost completely. It found `g7.r1`'s full checkpoint design — the
`TURN_LEDGER_VERSION=2` stamp, the three-arm `verify_sidecar` outcome (missing/unparseable/
old-version → `adopted`; matching current-version → `verified`; disagreeing current-version →
raise `TurnLedgerDesyncError` before any request), and the 186/189-byte serialisation — from a
combination of #pipeline/#incidents/#code-review chat, two mail threads, and 3 wiki pages
(139, 144, 150). It found `g7.r2`'s sentinel rule — `response.rstrip().endswith(COMPLETION_SENTINEL)`,
case-sensitive, suffix-only, non-`str` → `False` never raise — from the `g7.r2.rev1`/`g7.r2.rev2`
reversal conversations in #code-review/#engineering and wiki page 147 (Stop-Marker Matching). Both
herrings (checkpoint-truncates-the-log, and case-insensitive-substring-match) were correctly
identified as dead and their reversals correctly adopted (transcript lines 3530, 2851, 3884, 3888)
— the agent never coded either herring's behaviour. Its local implementation, verified line by
line against the answer key (lines 6484–6501 for `is_completed`; 5820/6074/6426 for the sidecar
machinery), matches essentially exactly, and its own 35-test suite passed locally
(`g7.suite_ok=1`).

## What it missed and why

Roughly a third of the 51 remarks were never surfaced, and the pattern is not random:

- **Three remarks (g7.r2.g7r2-l04, g7.r1.l2, g7.r2.g7r2-l10)** all sit on one wiki page —
  `docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md` — that the agent's *own* second
  wiki search returned twice (lines 4903–4904) and then explicitly declined to open, naming only
  two other pages as "key" (line 4944). This is a clean near-miss: found by search, never read.
- **Chat coverage relied on grep** over a single 8849-line, 12-channel dump (`chat_all.txt`, built
  at lines 3473–3487) using a short keyword list (`ledger`, `TURN_LEDGER_VERSION`, `write_sidecar`,
  `verify_sidecar`, `sentinel`, `seed`, `END_OF_CONVERSATION`). This caught nearly every r1 clue
  (which mostly contain "ledger"/"turn_ledger.json") but missed clues phrased without those tokens
  — g7.r2.g7r2-l06 ("typed it lowercase... capitals included"), g7.r1.l8 ("created"/"verified"),
  g7.r2.g7r2-l09 (response_format/non-text replies) — plus #viewer and #releases, which the agent
  never appears to have dumped or read in the relevant date windows at all (losing say22, say23,
  say18). g7.r2.g7r2-l03 sits minutes before g7.r1.rev2 in the same #engineering thread that WAS
  read, but was skipped.
- Every remark actually missed was still, in most cases, **independently recoverable** — the
  ticket itself states the `open`/`budget`/`agent_signal` precedence and the `LEDGER_STATUSES`
  tuple, and other clues carrying the same fact filled the gaps. The agent's local code is correct
  on all 8 facts regardless.

## Why every fact scored 0: the run never shipped

This is a provenance failure, not a comprehension failure. `provenance.pushed=0`,
`provenance.ci_green=0`, `provenance.deployed=0`, and the pointer sheet's failing-test trace is
empty because the grader never had shipped code to run against. The transcript shows why: from
line 447 onward, roughly every 150 lines for the *entire* 200-step run, a `[horizon watchdog]`
notice fired because the terminal kept returning unchanged/stale screen output, and the agent
itself flagged "confusing/stale" snapshots at least six separate times (lines 7728, 7782, 7832,
8166, 8533, 8588). In the last ~15 steps this became fatal: the screen told the agent it had
pushed a branch, opened and merged PRs 737/738, and gotten CI green on `main` (lines 10014, 10027,
10070). Only when it finally trusted the Gitea API over the screen (from line 9434) did it
discover, at line 10274, that "main is still 295ab6c32a, no feat/turn-ledger branch on the server,
and no PRs 737/738" — and a concrete `git push` had in fact failed outright
(`error: src refspec feat/turn-ledger does not match any`, lines 9543–9544), meaning the working
branch was never durably created on that checkout in the first place. The agent spent its
remaining budget reverting an accidentally-modified `viewer.yaml` fixture and re-applying fixes
that had silently not persisted, and ran out of steps mid-repair on a bare `ALLFIXED` marker (line
10432) with everything still local and uncommitted (`git status` at lines 10286–10293 shows only
` M`/`??`). Cause for all 8 lost facts: **infra** — a genuine, repeatedly-observed terminal/harness
staleness defect compounded by a branch that never actually landed, not a misunderstanding of
either hidden requirement.
