# g9 run 2 (f7cf25ff) — reward 0.8571

## What this run found

The run was thorough and disciplined. It cloned the repo, read every relevant source file, then
ran three separate investigations in parallel style: a Mattermost sweep (first API keyword search,
then a full local dump of every channel — code-review 3233 lines, engineering 2484, pipeline 1990,
cookbooks 776, releases 685 — grepped locally with context), a BookStack sweep (`/api/search` then
full page+comment fetches for every promising hit — pages 132, 142, 144, 145, 149, 153, 156), and a
very thorough IMAP sweep (subject/body keyword search, then full-thread fetches reaching 20+
transcript hits on several threads: `l-scope-1` 26, `l-rule-2` 23, `l-scope-4` 20, `l19` 24). By
transcript line 4910 it had assembled an accurate composite record — the encoding.py surface, the
`ExampleTooLongError` 16-retained-prompt-token floor, `EncodingReport`'s frozen dataclass and field
order, and the abort/skip semantics of `format_batch` — and shipped code that passed 7 of 8 grader
tests: `open_feature`, all three `r1` facts except `failure_behavior`, and both `r2` facts.

## What it missed and why

Exactly one fact was lost: `g9.r1.failure_behavior`. The grader's assertion
`assert error.num_messages == 2` failed with `None` (junit trace: "over-long refusal:
num_messages: None != 2", `test_r1.py:161`). The agent's shipped `ExampleTooLongError` raise call
(rollout JSON message 228) passes `token_count`, `max_seq_length`, `window_start`, and
`retained_prompt_tokens` — never `num_messages`. Of the 57 planted remarks, exactly **one** states
that the exception carries `num_messages` as a constructor attribute and quotes the exact required
message string: `g9.r1.l-fail-3` (#pipeline, 2025-03-19, "num_messages rides along as an attribute,
not printed"). It was never surfaced by any search the agent ran — confirmed independently by
grepping the full transcript for "num_messages" near `ExampleTooLongError`, and for the exact
required message text ("prompt tokens would survive", "minimum is 16"), both zero hits. Its sibling
`g9.r1.l-fail-2` (#releases, same date, quoting the literal string with the 129/40/0/16 example) was
only glimpsed as a one-line grep fragment ("stopped. ExampleTooLongError, and the traceback right
after it", line 3654) that the agent never expanded into full channel context. The agent's own
shipped message text ("example too long: {N} tokens against a limit of {M} leaves only {K} prompt
tokens past window_start") is a self-invented template, confirming neither remark's literal wording
was ever recovered.

This was not a believed-herring failure — the agent correctly reasoned through both herring/reversal
pairs for this requirement (`h1`→`rev1`, `h2`→`rev2`): it explicitly concluded "window_start > 0
refuses nothing now... keyed on where the final assistant span starts relative to window_start...
under 16 tokens" (line 4498), and the shipped threshold logic is correct (three of the four exception
attributes and the skip-and-continue batch behavior all passed their assertions). The miss is narrow
and specific: one constructor field, gated behind one remark that a reactive, proper-noun-driven
keyword search never queried for, despite the full #pipeline channel sitting locally dumped on disk.

## What it believed, and why

Both herring pairs (r1's refuse-all-windowed position, r2's tuple-return signature) were correctly
identified as superseded: the agent read the reversal chat exchanges in full and its own final
summary states the corrected rules verbatim ("being windowed alone refuses nothing... format_batch
skips-and-counts over-long rows... self.last_report... never written on abort", line 8036). The
`g9.r2.h-role-row` herring (treating a bad role sequence as a skippable row problem) was likewise
caught and correctly reversed via `docs/engineering/request-builder-what-we-drop-and-what-we-raise-
on.md` (`l17`/`rev3`, line 5033), matching the ticket's own explicit statement that
`InvalidRoleSequenceError` propagates. No herring was shipped into the final code.

## Other search gaps (no fact impact)

Roughly 20 other clues were never surfaced, but every affected fact still had 3+ independent
carriers found elsewhere, so none of these changed a grade: nine plain-language #chat remarks
(`l-rule-3`, `say20`, `l-fail-1/4`, `l18`, `l16`, `say22`, `l-fw-4`, `l-scope-2`) sat in the locally
dumped channel files but were never grepped for; six wiki-comment remarks were missed because their
pages were never fetched — notably `docs/meetings/*` pages (`l11`, `l5`) were never enumerated at
all, distinct from the `docs/engineering/*` pages the agent's searches favored; two mail threads
(`l13`, `say25`) were found only as subject-line hits and never opened. One remark (`g9.r1.l-rule-1`)
surfaced as page BODY text in this served world rather than as the page COMMENT the answer key
describes it as — a corpus/key discrepancy worth flagging, though it did not change any grade since
`r1.rule` passed via other remarks regardless.
