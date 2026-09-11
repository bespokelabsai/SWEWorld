# g7 (agent-turn-ledger) — world-hosted v5, eval 8deffce4, run 2, rollout c22e6a99

**Reward: 0.875 (7/8 declared facts).** Pushed, CI green, deployed, suite_ok. The only miss is
`g7.r1.observability`.

## What this run found

Search strategy was exhaustive rather than clever: at step 31 (line 2671) the agent enumerated all
12 Mattermost channels via the API and bulk-dumped every post to local files instead of searching
piecemeal, then grepped repeatedly as its model of the requirement grew. For the wiki, it correctly
learned (line 143) that BookStack search does not index comments and switched to fetching whole
pages by id (`/api/pages/{id}` for 139, 143, 144, 150, 152, 211, 85) — this is exactly the discipline
the task rewards, and it is why **all 8 wiki-comment clues plus the 1 wiki-page-body clue were
found**. For mail it ran one IMAP `SEARCH` pass with the keyword list `{ledger, sidecar, sentinel,
turn_ledger, next_speaker, seed}` and fetched the union (22 message ids) in one shot — it never
widened the term list, which is the run's one real search-strategy gap (see below).

By the end the agent had correctly reconstructed both requirements almost completely: the three-arm
`verify_sidecar` (absent/unparseable/old-version → adopted; matching → verified; current-version
mismatch → raise `TurnLedgerDesyncError` before any request), the exact 186/189-byte sidecar
spellings, the `sidecar_state()` eight keys, and — for r2 — `COMPLETION_SENTINEL =
"<<END_OF_CONVERSATION>>"` matched by `response.rstrip().endswith(...)`, case-sensitive,
non-`str` → `False`. All four herrings were correctly abandoned for their reversals (see below).

## What it missed and why

Fourteen of 51 remarks never surfaced. Three are mail threads whose wording (`"metadata json isn't
on disk"`, `"stop condition"`, `"stop sequences"`) doesn't contain any of the five IMAP search
terms — the `sentinel` search itself returned 0 hits, so those message ids were never in the fetch
list at all. Several more are chat clues in `#cookbooks`, `#viewer` and `#releases` — channels that
were dumped in full alongside every other channel but were comparatively under-grepped (0 misses in
`#code-review`/`#pipeline`/`#engineering`/`#incidents` versus 4 of the 14 total misses living in
these three). One miss, `g7.r2.g7r2-l12` (the exact dataset row content/role), cost nothing because
the open ticket's own stated dataset schema already supplied that detail publicly.

## What it believed, and why

All four herrings were seen only through their reversals or side-by-side with them, and the agent
believed the reversal in every case. Two herrings (`g7.r1.g7-h2-truncate-is-the-pattern`,
`g7.r2.h2-sentinel-placement-free`) were never encountered in their original form at all — the
agent only ever saw them paraphrased inside the reversal exchange itself (lines 3626 and
3040/3186) — which was still sufficient to avoid shipping them. The shipped code matches the
reversed (correct) design throughout: log-wins-on-resume, case-sensitive suffix match.

## Why `g7.r1.observability` was lost — the one fact that scored 0

The failing check (first failure in `judge_r1_observability`, everything before it passed) is
`eq(o["nockpt_status"], "adopted", "no checkpoint -> adopted")` — a resumed run whose sidecar file
was deleted (but whose log already has content) must come back with `ledger.status == "adopted"`.
The agent's code got `"created"` instead.

This is a genuine **implementation slip**, and an unusually legible one because the agent narrated
it into existence. `verify_sidecar()` itself is correct: it returns `status="adopted"` whenever
`read_sidecar()` is `None`. The bug is that `processor.run()`'s turn loop never keeps that status:
after computing `ledger = self.load_cache(working_dir)` once at the top of `run()`, every
subsequent appended response re-derives the ledger via `self._ledger_from(records)` — and
`_ledger_from`'s signature hardcodes a status default (originally `"verified"`, later `"created"`)
that overwrites whatever `load_cache`/`verify_sidecar` had just computed, on every turn.

Late in the run (transcript line 8703), the agent read remark `g7.r1.fix30` (`#pipeline`,
2025-12-30: *"clean work dir, ran it end to end — nothing to load so verify_sidecar never fired,
and the ledger came back still carrying the status it was built with"*) and correctly diagnosed
that a truly fresh work dir should keep `"created"`. But its fix — gating `load_ledger` on
`if not records: return ledger` and flipping `_ledger_from`'s default to `"created"` — only patches
the symptom for the *empty-log* case; it does not address that the loop always overwrites status
with a fixed default regardless of provenance. So a resume with an existing (non-empty) log and a
deleted sidecar still goes through the loop and gets stamped `"created"` instead of the `"adopted"`
that `verify_sidecar` had correctly produced moments earlier. The agent then wrote new unit tests
only for the fresh-run case (line 8760-8776) and never re-tested the delete-the-sidecar resume path
that its own earlier reading (`g7.r1.l9`, `g7.r1.l16`, `g7.r1.rev1`) had established — a
self-inflicted regression from a clue it read correctly but fixed too narrowly.

## Facts

| fact | score | relied on |
|---|---|---|
| g7.r1.rule | 1 | g7.r1.l2, g7.r1.rev1, g7.r1.l4 |
| g7.r1.scope | 1 | g7.r1.l5, g7.r1.l6, g7.r1.l8 |
| g7.r1.failure_behavior | 1 | g7.r1.l16, g7.r1.fix28 |
| g7.r1.observability | **0** | implementation_slip — see above |
| g7.r2.rule | 1 | g7.r2.rev1, g7.r2.g7r2-l03 |
| g7.r2.scope | 1 | g7.r2.rev1, g7.r2.g7r2-l07 |
| g7.r2.failure_behavior | 1 | g7.r2.rev2 (sole carrier found) |
| g7.r2.observability | 1 | g7.r2.g7r2-l13, g7.r2.g7r2-l14 |
