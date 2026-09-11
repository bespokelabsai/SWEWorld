# g9 run 8 (5c4fad06) — reward 0.7143 (5/7 facts)

This run did the research well and shipped a large, mostly-correct `encoding.py` /
`DataFormatter` rewrite that passed all 137 local tests, was merged to `main` and
deployed green. It lost exactly two facts, and both losses are traceable to a
specific moment in the transcript rather than to sloppy search.

## What it found

The agent's method was disciplined: it enumerated all 239 wiki pages by title and
batch-fetched the ten that looked finetune-relevant (with comments — it correctly
understood BookStack search doesn't index comments), dumped every Mattermost
channel to a file and grepped repeatedly for evolving terms, and IMAP-searched mail
for the same. This surfaced the full multi-month evolution of two "settled but
never written" decisions: the `ExampleTooLongError` 16-retained-prompt-token
refusal rule (four herrings/reversals, all correctly resolved — g9.r1.h1/h2/rev1/rev2)
and the `(data, report)` tuple-return design that was reverted in favour of
`self.last_report` (g9.r2.g9-tuple-return-1/2 and their reversals, also correctly
resolved). Both `r1.failure_behavior` and `r2.rule` passed cleanly on this strength,
along with `r1.scope`, `r1.exclusions_or_crossover`, and `r2.scope`.

## What it missed, and why

**`g9.r1.rule` (0)** — the requirement that a supervised span straddling the window
boundary must be zeroed *in full*, not clipped to its surviving tail. The agent
actually found the correct remark: at transcript line 2114 it read Nils Brandt's
wiki comment (page 132) and wrote "a turn straddling the cut is IN if its opening
token survived, OUT if it didn't — no partial state... 132's comment is likely the
newer decision," correctly flagging the conflict with an older wiki page (153) that
describes the pre-ticket clip-and-keep behaviour. But it never followed up on that
flag. Its final Plan before writing code says only "weights sliced identically" —
the mechanism from page 153 (and from the ticket's own prose) — with no mention of
the boundary check. The shipped `_supervised_spans`/`to_tinker_datum` code sets
`weights[i]=1` for every span index unconditionally, then slices by
`window_start`, so the straddling span's surviving tail keeps its weight. Working
the test's own numbers by hand: the agent's output has 16 supervised tokens (7 from
the straddling span's tail plus 9 from the clean span) where the test requires
exactly 9. This is a found-then-lost rule — the agent stated the right answer once
and then implemented the wrong one.

**`g9.r2.failure_behavior` (0)** — the requirement that only the over-long refusal
is absorbed by `format_batch`; a bad role sequence must propagate and abort, not be
counted as a drop. The agent read the herring directly (dario's mail, 2025-05-28:
"Length and role sequence are row problems... those get counted and skipped") and
its Analysis one turn later states this as settled fact with no hedge: "Confirmed
the layering: length and role-sequence failures are row problems." The reversal —
dario's own June 17 wiki comment retracting exactly this ("this is me contradicting
myself... only the over-long ones are row problems") — sits as a comment on wiki
page 149. That page *was* fetched to disk in the same batch-fetch command that got
pages 132, 145, 153, etc., but its content was never actually displayed: the plan
at line 2115 says "cat 137 and 135 and 149 heads," and the following terminal
screen shows only page 137's content before the agent moves on to Mattermost
search. The shipped code's `except (InvalidRoleSequenceError, ExampleTooLongError)`
catches both as row-level drops, exactly matching the herring. The other half of
the same rule — a bad tokenizer must abort, never be counted — was implemented
correctly, sourced from wiki page 155 and the same mail thread, both of which the
agent did read in full.

## Search strategy notes

Mail search used only three fixed IMAP terms (`ExampleTooLongError`,
`EncodingReport`, `last_report`), which found the decisive threads but missed 7 of
13 mail-only remarks whose vocabulary didn't overlap (`token_count 52`, `sft
export`, etc.) — none of these were individually load-bearing since redundant
remarks elsewhere carried the same facts, except for `g9.r1.l-rule-2`, whose loss
removed one of two independent confirmations of the r1.rule boundary condition.
Chat grep was similarly narrow but effective given channel dumps were complete.
The wiki fetch-then-never-read failure on page 149 is the single costliest gap in
the run.

## Bottom line

Both lost facts are `implementation_slip`/`herring_followed`, not infra and not
`grader_overspecifies` — in both cases the correct remark was in the agent's own
terminal output, and in one case in its own stated reasoning, before the wrong
code was written.
