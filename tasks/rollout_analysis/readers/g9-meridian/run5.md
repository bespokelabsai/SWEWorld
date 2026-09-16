# g9-meridian run 5 (1a76c237) — reward 0.8571

## What this run found

The run is a near-clean sweep: 6 of 7 hidden facts, all of `g9.r1` (rule, scope,
exclusions_or_crossover, failure_behavior) and two of three `g9.r2` facts (rule,
scope). Only `g9.r2.failure_behavior` scored 0.

For `r1`, the agent correctly threaded the herring/reversal pair on the refusal
threshold: it read both `g9.r1.h1`/`h2` ("any nonzero window_start refuses",
"binary, windowed at all means refused") and their reversals `g9.r1.rev1`/`rev2`
("only under 16 retained prompt tokens"), and shipped the reversed rule verbatim,
including the exact error string. It also correctly derived the all-or-nothing
span rule (`g9.r1.l-rule-2`, `l-rule-1`, `l-rule-4`: a straddling span keeps
*none* of its weight, not its surviving tail) and the character-offset mock-path
spans (`l-scope-3`, `l-scope-4`, `say23`, `fix28`).

For `r2`, the agent likewise navigated the `(data, report)`-tuple herrings
(`g9-tuple-return-1`/`-2`) and their reversals correctly, shipping
`EncodingReport` as a frozen dataclass on `self.last_report`, reassigned by both
`format_batch` and `to_jsonl_lines`, with `to_tinker_datum` never touching it
(`g9.r2.say23` — the one remark the passing `r2.scope` fact actually rests on).

## What it missed, and why

`g9.r2.failure_behavior` requires that only `ExampleTooLongError` be absorbed as
a drop inside `format_batch`; `InvalidRoleSequenceError` and
`TokenizerCapabilityError` must propagate and abort the pass untouched. The
shipped code (transcript line 2183, unchanged through the final diff at line
2675) reads:

```python
except (InvalidRoleSequenceError, ExampleTooLongError):
    dropped_indices.append(index)
    continue
```

— it silently drops bad-role rows instead of raising, which is exactly what the
grader caught: `bad roles abort: expected an exception, none raised`.

This is a herring the agent followed, not a fact it never found. At transcript
lines 2089–2118 a single `sed` dump of the mail archive surfaces *both* the real
requirement `g9.r2.say23` ("to_tinker_datum just raises ExampleTooLongError
outright — the binning is format_batch's job") *and* the herring
`g9.r2.h-role-row` in the same reply thread: "Length and role sequence are row
problems — one bad row says nothing about the next row, so those get counted
and skipped." The agent's very next Analysis (line 2123–2126) reads: "The record
adds frozen EncodingReport, ExampleTooLongError, whole-turn masking, **selective
batch skipping**, and Fireworks byte filtering" — folding role-sequence errors
into the same "skip and count" bucket as over-long examples — and its very next
command (line 2167) writes the code above.

**Did it see the reversal?** No. `g9.r2.rev3` — dario's own wiki-comment
retraction six weeks later ("this is me contradicting myself... only the
over-long ones are row problems") — sits, together with the independent clue
`g9.r2.l17` ("only the over-long ones should get binned and counted"), on
`docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`. That
page was never fetched. **Did it fetch wiki comments at all?** Yes, routinely —
6 pages (156, 137, 132, 153, 145, 144) were pulled whole, body plus comments,
via `/api/pages/{id}`, and several passing facts (`say21`, `l-scope-3`,
`l-rule-4`, `l-rule-1`, `say27`, `l2`) rest on comments the agent read exactly
that way. The gap is upstream of fetching: the agent ran only three BookStack
`/api/search` queries the whole run — `encoding`, `finetuning`, `Fireworks` (the
last returned zero hits) — and never tried `drop`, `raise`, `role`, or `batch`.
The request-builder page's title matches none of the three terms tried, so it
was never in a result list to begin with. (A second page carrying the same
correction, `what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md`,
was equally unreachable for the same reason.)

A second contributing factor: the agent's own regression test only asserts
`InvalidRoleSequenceError` propagation on the Fireworks `to_jsonl_lines` path
(line 2390); it never wrote an equivalent test for `format_batch`, so its local
"121 passed" run (line 3069) never caught the mismatch between its own belief
and its own code.

## Search strategy

Chat: Mattermost REST search across three escalating keyword rounds, expanded to
whole-channel dumps (200 posts/channel) and ±8–12-post context windows, all
grepped locally — thorough enough to recover both requirements' rule/scope with
redundancy, but blind to any remark whose exact wording never matched a chosen
grep term. Mail: one IMAP `ALL` fetch of the entire mailbox up front (nothing
structurally unreachable), read afterward only through targeted `sed` ranges,
leaving several full threads (`say25`, `l-scope-1`, `l13`, `l19`) unread on disk.
Wiki: only 3 whole-word searches, 6 pages fully fetched (body + comments); no
search ever touched the vocabulary of the missed pages, and one page returned by
the very first search (154, PR 652) was never opened at all. A combined 3-page
body+comment dump also overflowed the terminal screen, likely costing the agent
`g9.r2.l14`'s comment on page 137 even though the command that produced it ran
successfully.
