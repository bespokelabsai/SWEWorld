# g7 run 7 (9bd32b81) — eval 8deffce4 — reward 0.5

## What this run found

r2 (the sentinel-ends-a-turn requirement) is fully solved: all four facts (rule, scope,
failure_behavior, observability) score 1. The decisive source was `g7.r2.h1-sentinel-substring-ci`'s
reversal (`g7.r2.rev1`), which the agent pulled as one complete, contiguous `awk` range over the
#code-review channel (transcript lines 4207–4230) rather than as a search snippet — the only time in
this run it read a whole multi-turn exchange in one shot. That gave it, verbatim, `is_completed is
response.rstrip().endswith(COMPLETION_SENTINEL), nothing else` and `gone too. case sensitive now`,
and the shipped `Agent.is_completed` matches it exactly (`str(content).rstrip().endswith(tl.COMPLETION_SENTINEL)`,
rollout tool call index 6491). Three more found remarks (g7r2-l09, l11, l12, l13, l14) rounded out
scope/failure_behavior/observability with no contradiction anywhere.

r1 (the checkpoint sidecar) is a different story: all four facts score 0, but the shipped code got
almost everything about it right. `sidecar_state()`'s eight keys, the `sort_keys, indent=2,
trailing-newline` serialization (186 bytes mid-run, 189 at the end — both byte-exact assertions
pass), `TurnLedgerDesyncError`'s exact message format and `.log_responses`/`.recorded_responses`/
`.log_last_author`/`.recorded_last_author` attributes, and the "raise before any call" timing are
all correctly implemented, informed by remarks the agent genuinely read and applied (l3, l4, l12,
l13, l14, fix28, say21). The whole 0.0 on r1 comes down to two narrow, surgical bugs.

## What it missed and why

**Bug 1 — wrong constant name (kills `r1.rule`).** The shipped module defines `SIDECAR_FILENAME`,
not `TURN_LEDGER_FILENAME`; the grading probe fails on its very first line (`sym('TURN_LEDGER_FILENAME')`).
The literal identifier `TURN_LEDGER_FILENAME` appears exactly once in the entire 51-remark corpus —
a comment on `docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md` (`g7.r1.l2`) — and that
page was never opened by any route (zero grep hits for "weekly-sync"/"jun-2" across the whole
8208-line transcript). Every other sidecar remark talks about "the sidecar"/"turn_ledger.json" but
never states the Python constant's name, so the agent invented one.

**Bug 2 — `verify_sidecar` returns `"created"` instead of `"adopted"` for a missing sidecar file**
(kills `r1.scope`, `r1.failure_behavior`, and the last section of `r1.observability`, whose earlier
byte-exact checks all pass). This is the more interesting failure because it is a genuine misread,
not a corpus gap. At transcript line 5040 the agent states: *"verify_sidecar returns 'created' when
no sidecar on disk, 'adopted' when present but unusable."* Immediately before writing that, at lines
4995–5034, it had read `g7.r1.fix27` in full: *"...you ran that first pass with turn_ledger.json
deleted"* → *"yup, that one first. then again with nils' old record sitting there"* → *"version 1.
came back **adopted both times**, not verified."* Both the deleted-file case and the old-version case
are stated, together, to return `"adopted"` — directly contradicting the rule the agent wrote one
screen later. It appears to have conflated that exchange's earlier, unrelated line ("a freshly built
ledger" — a brand-new in-memory object before any load happens, the genuine `"created"` case) with
the deleted-file/resume scenario. Two more remarks state the same "missing → adopted" rule in plain
language and were never fully seen: `g7.r1.l9` (mail: *"Missing file is benign - we adopt the log"*)
was never opened because its vocabulary is "checkpoint"/"metadata json", and none of the agent's
fixed IMAP search terms (`ledger`, `sidecar`, `sentinel`, `marker`) appear anywhere in that thread;
`g7.r1.rev2` (chat) was read only as a search-snippet dump that is cut exactly one line before its
resolving sentence, *"missing, or below 2, gets status adopted and we keep going"* — confirmed absent
from the transcript by direct grep.

## What it believed and why

Both r1 herrings (checkpoint-authoritative-truncation) were correctly rejected — no truncation logic
exists anywhere in the shipped `turn_ledger.py` — though the agent never saw either herring's or
reversal's resolving lines cleanly; it treated the topic as open ("need much more chat context") and
arrived independently, via later remarks (l12, fix28), at the correct desync-and-raise design. Both
r2 herrings were also correctly rejected, with `g7.r2.h1-sentinel-substring-ci`'s full reversal read
whole and never doubted afterward.

## Why each lost fact was lost

- **r1.rule** — `not_found`: the sole carrier of `TURN_LEDGER_FILENAME` sits in a never-visited wiki
  comment.
- **r1.scope / r1.failure_behavior / r1.observability (final section)** — `found_misread`: the same
  status-label bug (`"created"` vs `"adopted"` for a missing sidecar) sinks all three, despite direct
  contradicting evidence (`fix27`) sitting in the agent's own immediately-preceding tool output, and
  despite two other remarks (`l9`, `rev2`) that would have settled it independently but were missed
  for narrower reasons (keyword-search gap; snippet truncation).

## Search strategy

Chat was searched mostly through a helper (`/tmp/mm.py`) that returns 1–2 line snippets per keyword
hit — this is the direct mechanism behind the rev2 truncation. The one time the agent instead pulled
a full contiguous line range (`awk 'NR>=4060 && NR<=4100'`), it got a complete, unambiguous answer
(r2.rev1) and never wavered. Wiki pages that were opened were fetched whole via the BookStack API
(comments included, per the ticket's own advice), which is why several wiki-comment clues were found
— but `weekly-sync-notes-week-of-jun-2-release-ci.md` was never discovered at all, despite carrying
an indexed, search-findable page-body clue (`g7r2-l04`) that should have led the agent to fetch it
whole and pick up `l2`'s comment in the same request. Mail was searched over IMAP `TEXT` for a fixed
term list that happened not to intersect the two threads (`l9`, `g7r2-l08`) written in different
vocabulary ("checkpoint"/"metadata json" rather than "ledger"/"sidecar").
