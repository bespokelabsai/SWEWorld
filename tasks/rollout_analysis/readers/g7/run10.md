# g7 run 10 (41f9c9fd, eval 8deffce4) — reward 0.625

## What it found

The agent read essentially all of the ticket's hidden material for **g7.r2** (the
sentinel/`is_completed` requirement): all four r2 facts scored 1. It recovered the
`response.rstrip().endswith(COMPLETION_SENTINEL)` rule from the code-review reversal
thread (`g7.r2.rev1`, line 3436) and cross-checked it against wiki page 147; the
suffix-only/case-sensitive/whitespace-tolerant scope from a mail thread (`g7r2-l05`)
and a wiki comment (`g7r2-l07`); the non-string-returns-False failure behaviour from a
mail thread (`g7r2-l08`) and the `rev2` chat reversal; and the exact observability
numbers (four `responses_0.jsonl` lines for three responses, `completion_reason ==
"agent_signal"`) from two wiki comments (`g7r2-l13`, `g7r2-l14`). Both r2 herrings were
seen, both correctly recognized as dead, and the shipped `Agent.is_completed`
implements the reversal, not the herring, in every respect.

For **g7.r1** it recovered `g7.r1.failure_behavior` cleanly (all three verify_sidecar
arms: adopted/verified/raise, with the exact `TurnLedgerDesyncError` message and
attributes), built mostly from mail threads read in one early bulk pass (steps 32-46)
plus a chat exchange confirming `TurnLedgerDesyncError` is the module's only raise
(`fix28`).

## What it missed, and why

Three of `g7.r1`'s four facts scored 0 — but **not** because the agent failed to
recover the requirement. Its own reasoning states the created/adopted/verified
three-status design correctly (e.g. "load_ledger = read log, rebuild in memory,
verify_sidecar, nothing written," line 3979) and even confidently names
`TURN_LEDGER_FILENAME` as a settled fact eight separate times from step 66 onward. The
actual grader failures are implementation bugs against that correct understanding:

- **`rule`** failed because the shipped constant is literally named `SIDECAR_FILENAME`,
  not `TURN_LEDGER_FILENAME` — despite the agent stating the latter as fact repeatedly.
  Grepping the whole 10,268-line transcript for `TURN_LEDGER_FILENAME` turns up zero
  hits: the agent never actually read it anywhere. The one remark that names it
  (`g7.r1.l2`, a wiki *comment*) sits on
  `docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md`, a page the agent never
  opened, searched for, or listed in the entire 183-step run. The name it "recalled" was
  a confabulation off the sibling constant `TURN_LEDGER_VERSION` (which the corpus does
  attest, repeatedly) — and then, in the moment of writing code, it typed a third, still
  different name. Cause: `implementation_slip` (plus a genuine `not_found` on the one
  remark that would have prevented it).
- **`scope`** and **`observability`** both failed on the same bug: `build_ledger()`'s
  default parameter `status: str = "verified"` is inherited by `processor._derive_ledger()`,
  and the `run()` loop calls `_derive_ledger(records)` with no explicit status at the two
  places where it matters — the seed's first write (should be `"created"`) and every
  post-resume re-derivation (should preserve `"adopted"`). Both silently collapse to
  `"verified"`. The agent's reasoning about `created`/`adopted`/`verified` (built from
  `l5`, `l6`, `fix27`, `fix30`, `say20`) is correct; the wiring at those two call sites is
  not. Cause: `implementation_slip`.

The same never-opened weekly-sync-notes page also cost two `g7.r2` remarks
(`g7r2-l04`, `g7r2-l10`), but both were redundant — other remarks (`g7r2-l08/l09/l12`,
`rev1`, `l07`) already carried those facts, so `g7.r2` lost nothing from the gap.

## Search strategy

Mail was read in full, in order, very early — this alone supplied most of r1's
`failure_behavior` and several `rule`/`scope` clues almost for free. Chat was searched
with a fixed, self-chosen keyword list (`sentinel`, `sidecar`, `next_speaker`,
`desync`, `load_ledger`, …) through a single-line-snippet search tool, so remarks
worded without any of those literal terms (`"negotiation demo"`, `"nobody
subclassed"`, `"typed it lowercase"`, TurnLedgerError's trailing full stop) were never
found regardless of channel. `#cookbooks` — home to five remarks across both
requirements — was visited exactly once, incidentally, via an unrelated `ledger`
keyword hit. Wiki comments were missed for the first ~60 steps until the agent
debugged its own page-dumping script to surface `comments.active[].comment.html`;
after that it recovered comment-carried clues systematically on every page it actually
opened — the failure mode there is entirely about which pages it opened, not how it
read them once open.

## Bottom line

`reward = 5/8` hidden facts. Lost: `g7.r1.rule` (probe: `no module ... exports
'TURN_LEDGER_FILENAME'`, implementation_slip), `g7.r1.scope` (`'verified' !=
'created'`, implementation_slip), `g7.r1.observability` (`'verified' != 'adopted'`,
implementation_slip). All three trace to the shipped code diverging from the agent's
own correctly-stated understanding, not to unrecovered corpus content — except for the
one literal identifier (`TURN_LEDGER_FILENAME`) that lived solely on a page the agent
never visited.
