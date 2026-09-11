# g2 run 9 (4ba13ac7) — eval 9f2db992 — reward 0.8889

## What this run found

This is one of the strongest g2 rollouts: 8 of 9 hidden facts scored, `provenance` all
green, and — unusually — all four herrings were correctly identified and rejected. The
agent's search discipline is the reason: rather than reading isolated search snippets, it
built three small scripts early (`/tmp/cm.py` for BookStack comment trees, `/tmp/imf.py`
for full IMAP thread fetches, `/tmp/mmd.py` for full Mattermost channel-window dumps) and
used them to pull *entire exchanges*, not just the message that matched a keyword. That is
what surfaced both wiki-comment-only clues (`g2.r2.l-cross-1`, `g2.r2.l-rule-4`, lines
1197-1240) — BookStack search does not index comments, and a search-only agent would have
missed them — and it is what caught all four herrings and both r1 reversals in one pair of
full-window dumps (transcript lines 2397-2533, 2412-2470): the agent's Jan-2025 pipeline and
viewer dumps returned complete six-to-eight-message exchanges, so the reversal that followed
each herring a few weeks later was never read in isolation from the belief it corrected.
Mail was read unusually thoroughly — five separate threads, all fetched to completion
(lines 1493-1817) — and ended up being the primary carrier for `g2.r2.scope` and half of
`g2.r1.rule` (the 3:1 head/tail ratio came from mail, `g2.r1.l-rule-2`/`l-seam-dario`, not
chat).

## What it missed, and why

Thirteen of 46 remarks were never surfaced by any search or dump in the transcript. Twelve
of those turned out to be pure redundancy — the same fact was independently recovered from
a different remark, often the mail thread the agent had already read closely (e.g.
`g2.r2.l-scope-1`/`l-rule-1` were never found, but `g2.r2.l-scope-3` and `l-rule-2`, both
mail, carried the same information and were found). The thirteenth, `g2.r1.l-log-konrad`,
was not redundant, and its absence is the entire reason this run isn't a perfect 1.0.

`g2.r1.l-log-konrad` (#cookbooks, 2025-05-01 10:41–10:54) is the **only** remark in the
answer key stating that "the except handler's salvage cap logs nothing, we log where we
cut." The agent dumped the sibling #pipeline channel for the *exact same timestamp window*
one message earlier (transcript line 2214, `mr6zzi... 1746094000000 1746099000000`, chasing
`g2.r1.l-log-emil`'s wording of `TRUNCATION_LOG_TEMPLATE`) but never dumped `#cookbooks`
(channel id `tzfbbu`) for that window. The only trace of that exchange anywhere in the
transcript is one incidental line (2613) picked up by an unrelated `'floor'` keyword search
— dario's last message in the thread ("...how much we actually dropped on the floor"),
never konrad's actual determination. The agent's own Analysis at line 2543 explicitly lists
"log level of TRUNCATION_LOG_TEMPLATE" as a remaining unknown right before it starts writing
`output_cap.py`, and that unknown was resolved by inference rather than evidence: it built
one shared `_cap_output()` helper (line 3430) that logs on any capping, and wired it into
**all four** `CodeExecutionOutput` construction sites, including the `except Exception`
salvage branch (diff lines 4301, 4345). That is the architecturally natural choice absent
the corpus fact, and it is wrong: in the graded fixture (`exit_code=0`, oversized stdout,
then `Sandbox.__exit__` raising `RuntimeError("boom")` on the way out of a successful `with`
block), the try-body already caps-and-logs the stdout before the exception fires, and the
`except` branch then re-caps the *same* raw `result.stdout` via the identical helper,
logging the identical warning a second time. The test wants exactly one line; the shipped
code produces two. This is a clean `not_found` case, not a `implementation_slip` — nothing
the agent actually read contradicts what it shipped; the fact it needed was simply never in
view.

## Herrings

All four herrings (`g2.r1.herring-marker-inside-budget-dario`, `g2.r1.herring-dropped-count-
gideon`, `g2.r2.h1`, `g2.r2.h2`) were read in full alongside their reversals and correctly
resolved: the shipped code computes `dropped = original_bytes - kept_bytes` (not `original -
max_output_bytes`), keeps the marker outside the budget (not sliced out of the head), keeps
`error_truncated` on `CodeExecutionOutput` only (never mirrored onto `CodeExecutionResult` or
folded into `truncated_streams` as a third entry). None of the four herrings influenced the
final implementation in any way.

## Verification discipline

Before committing, the agent ran the full existing test suite and hit one pre-existing
failure (`test_simple_code_execution_local`); rather than assuming it was caused by the
change, it `git stash`ed, re-ran against clean `main`, confirmed the failure was pre-existing
(no sandbox available in this environment), and popped the stash back (lines 3658-3687) —
solid practice that avoided a false alarm. It then hand-verified the cap arithmetic against
the record's own numbers (64-byte budget over 80 bytes → 93 back, line 3743) before writing
tests, and added its own `test_output_cap.py` plus sandbox-backend tests through the fake
seam, all passing (32 passed, line 4599), before pushing to `main` and confirming CI green
and the service healthy (lines 4612-4633).

## Summary of the one lost fact

`g2.r1.observability` lost to one bundled pytest assertion: the except-path salvage cap logs
a duplicate warning line instead of staying silent. Cause: `not_found` — the sole carrying
remark (`g2.r1.l-log-konrad`) was never fetched, despite the agent dumping the sibling
channel for the identical timestamp window one step earlier.
