# g7 run 4 (da2368bd) — reward 0.625

## What this run found

The agent read every source file whole before touching the world (lines 390-1097),
then worked chat, wiki and mail in that order. Its wiki strategy was exactly right
for this task: it fetched `/api/pages/{id}` (body + comments) for every page it
identified rather than trusting BookStack's search, which does not index comments
(the ticket itself warns of this at line 143). Result: **9 of 9** wiki-surface
remarks were found — all 8 page comments and the 1 indexed page body.

Chat and mail were both worked by keyword search rather than date-range channel
dumps. In Mattermost (`mm.py`, a wrapper on `/api/v4/.../posts/search`) the agent
escalated through an identifier-heavy term list — `sentinel`, `turn_ledger`,
`TURN_LEDGER_FILENAME`, `COMPLETION_SENTINEL`, `next_speaker`, `adopt_ledger`,
`seed`, `sidecar`, `TurnLedgerDesyncError`, `interleave_faults`, `read_sidecar`,
`write_sidecar`, `ledger` — each returning single-line snippets across all
channels, with promising snippets then re-fetched as full timestamped windows
(`mmch.py`). This found all 4 reversals and 19 of 26 non-herring/reversal chat
clues (lines 2176-3121 and after). It systematically missed messages phrased in
plain English before the matching code/identifier existed in the world's own
timeline: neither herring's original wording was ever found directly (`checkpoint
wins on the mismatch`, `is_completed is a case insensitive substring scan`), nor
were `l1`, `l8`, `g7r2-l01/l02/l03/l06/l09`, `say23`, `say18`, `g7r2-l12`, `fix26`
— none of these contain any of the searched identifiers. No channel (`#releases`,
`#cookbooks` especially) was ever dumped end-to-end independent of a keyword hit.

Mail was searched even more narrowly: `mail.py` was run with only 9 terms across
the whole run (`turn_ledger`, `ledger`, `next_speaker`, `adopt_ledger`,
`num_cached`, `COMPLETION_SENTINEL`, `sidecar`, `seed message`, `multi-turn`),
never with plain terms like `resume`, `stop`, `sentinel` or `marker`. This is
exactly why the 3 mail threads whose *subjects* use those words — `l9` ("resume
when the metadata json isn't on disk"), `r2-l08` ("stop condition in the turn
loop — does it assume string content?"), `r2-l05` ("stop sequences: what should
count as a stop...") — were never surfaced, while the other 5 of 8 mail threads
were found and read in full (lines 3126-3559).

## What it believed, and why

The agent found full copies of **all four reversals** (`g7.r1.rev1`, `g7.r1.rev2`,
`g7.r2.rev1`, `g7.r2.rev2`) and, for two of the four herrings, only isolated
one-line fragments via the broad `ledger`/`sentinel` snippet searches — never the
herrings' own full threads. Despite that, the shipped code matches the *reversed*
design in every case: `verify_sidecar`/`run()` contain no truncation logic
anywhere, and `Agent.is_completed` is exactly `not isinstance(response, str)` then
`False`, else `response.rstrip().endswith(COMPLETION_SENTINEL)` — case-sensitive,
suffix-only (transcript lines 4367-4379). Because the reversals restate their
herrings' wrongness explicitly and give the corrected rule as executable-sounding
prose, finding the reversal alone was sufficient; none of the four herrings
diverted the implementation.

## Why each lost fact was lost

**g7.r1.rule (0):** a pure implementation slip, not a research failure. The
ticket itself states `write_sidecar | (working_dir, ledger) -> str` (task
description line 57). The agent instead wrote
`def write_sidecar(ledger: TurnLedger, working_dir: str) -> str` (line 4103) and
called it consistently as `write_sidecar(ledger, working_dir)` in `run()` (lines
4960, 4982, 6331) and in its own test suite (lines 5201, 5214) — so its own tests
reinforced the bug rather than catching it. The grader's held-out test calls it in
the ticket's documented order and gets `TypeError: expected str, bytes or
os.PathLike object, not TurnLedger`. No remark could have prevented this; the
ticket already said the right thing and the agent's code disagreed with it.

**g7.r1.scope (0) and g7.r1.observability (0):** one shared root cause.
`_derive_ledger(self, records, *, status: str = "verified")` (line 4864) is
called after every append in `run()` without ever overriding `status` (lines
4959, 4981), so the ledger's `status` is silently reset to `"verified"` on every
turn — even the very first, and even after a resume that correctly determined
`"adopted"`. The agent partially recognised that a fresh ledger should read
`"created"`: it special-cased `load_ledger` for a *completely empty* directory
(line 4657, reasoning explicitly from `g7.r1.fix30`, "clean work dir ... verify
never fired") but never carried that status through the *seed-derivation* step
that immediately follows, nor preserved a resumed run's `"adopted"` status across
its own subsequent appends. The one remark that states the missing rule in so
many words — `g7.r1.l8` (chat #pipeline, emil, 2025-03-24 18:30: "per-run, yeah -
... first write carries created, verified is only a load where both matched") —
was never found, because no chat search in this run ever used the terms
`created` or `per-run`. Even had it been found, catching the `_derive_ledger`
default-parameter bug required generalising status from "a value produced by
verification" to "a property that persists for the life of the run", which is
closer to inference than direct recall — the requirement's own stated "leap."

## A note on g7.r1.l12

The answer key's current text for `g7.r1.l12` has nikolai's 16:15 reply reading
"no, both sides" — but that phrasing was edited into the answer key locally after
this world (v4) was built, and was never pushed into the corpus. The transcript
this rollout actually read (lines 3288-3301, matching lines 3465-3499 on its
second pass) carries the pre-edit text: "yes, the log side only ... deliberate
... `.log_responses` is the count and `.log_last_author` is the name." Judged
against what the agent actually saw, its implementation is correct and
consistent: `.log_responses`/`.log_last_author` are log-side-only attributes
exactly as the world told it, and `.recorded_responses`/`.recorded_last_author`
(the ledger side) were separately and correctly sourced from `g7.r1.l16`. This
mismatch cost nothing.

## Summary

r2 (the sentinel/stop-condition requirement) scored a perfect 1.0 across all four
facts despite the agent missing 9 of its 13 non-wiki supporting clues, because the
two reversals alone restate rule, scope and failure_behavior as near-literal code,
and 3 wiki comments plus 1 chat remark covered observability. r1 (the checkpoint
ledger) scored only 0.25 mean across its four facts despite the agent finding 25
of 30 non-herring/reversal r1 clues and reproducing byte-exact serialization
(186/189 bytes), because its two zeroed facts both trace to a status-tracking
design gap that no amount of additional remark-reading alone would have closed,
compounded by one clean, remark-independent implementation slip (the
`write_sidecar` argument swap) that its own test suite was blind to by
construction.
