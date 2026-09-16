# g9-meridian run 10 (43076a77) — eval de47e209 — reward 1.0

A clean perfect run. The agent scored 1 on every graded fact: `open_feature`
(weight 0), `r1.rule`, `r1.scope`, `r1.exclusions_or_crossover`,
`r1.failure_behavior`, `r2.rule`, `r2.scope`, `r2.failure_behavior`. It cloned
the repo, read the ticket's fully-specified "open feature" (the error
hierarchy, `DataFormatter` signature, the dict envelope), then spent ~40 of its
56 steps pulling a bulk Mattermost channel dump, IMAP mail dump and BookStack
wiki pages into `/tmp` and grepping them with progressively refined keyword
lists, before implementing and pushing `92c8a9a` (all 113 finetune tests
green, CI run 14 green, deployed).

**r1 (all-or-nothing span boundary, byte-budget Fireworks path, 16-token
floor)** was solved cleanly and with good remark coverage. The all-or-nothing
rule came from `g9.r1.l-rule-3` ("the whole answer has to sit inside what we
keep...it counts for nothing at all") and was independently confirmed later by
`g9.r1.l-rule-1`'s wiki-comment restatement. Scope (no-tokenizer branch
sharing the same masking) traced to the `g9.r1.l-scope-1` mail thread arguing
against a second implementation, with `say23`/`fix28` supplying the exact
numeric weights and character offsets. The byte-budget exclusion came from
`l-fw-1`/`l-fw-4`/`say26`, and the 16-token floor plus `ExampleTooLongError`
message from `l-fail-2`/`l-fail-3` plus the reversal of the `h1` herring
(`rev1`) — the agent explicitly registered the herring ("any nonzero
window_start...raises") then read its own reversal in the same channel dump
and built the 16-retained-token floor, never the windowed-at-all rule.

**r2 (EncodingReport, self.last_report, only-ExampleTooLongError-drops)** is
where the run gets interesting, because the fact the prompt asked me to
settle — `g9.r2.failure_behavior` — was scored 1 despite the four remarks
that state or reverse it directly (`l16`, `l17`, `say24`, `rev3`) never
surfacing at all (confirmed absent by direct grep, matching the mechanical
pre-pass). The only remark in this family the agent actually saw was the
herring itself, `g9.r2.h-role-row` ("Length and role sequence are row
problems...counted and skipped"), at transcript line 1350 — and it saw it
inside the very same email as the correct scope clue `g9.r2.say23`. The
agent's next Analysis (line 1412) discusses only the atomicity requirement
and the too-long error message; it never repeats, endorses, or contradicts the
herring's role-sequence claim in words. It got the fact right anyway, by
construction: `g9.r2.l19`'s mail (lines 1336–1339, "accumulating into locals
and constructing the EncodingReport at the end...If the loop raises, no write
ever happens") gave it the accumulate-then-assign-once pattern, and the r1
herring/reversal thread (`h1`/`rev1`) gave it the narrow
`except ExampleTooLongError:` shape as the specific skip-and-continue
mechanism for length refusals. Composed together, any other exception raised
inside `to_tinker_datum` — `InvalidRoleSequenceError` from
`validate_role_sequence`, or `TokenizerCapabilityError` — necessarily
propagates out of `format_batch` before the single `self.last_report =
EncodingReport(...)` assignment runs, which is exactly the graded behavior.
This was not an accident: the agent wrote
`test_policy_reports_are_frozen_and_atomic`, which explicitly asserts
`pytest.raises(InvalidRoleSequenceError): formatter.format_batch(...)`
followed by `formatter.last_report is previous`. No corresponding test
exercises `TokenizerCapabilityError` through `format_batch` itself (only
through `to_tinker_datum` directly), so that half of the fact is correct by
the same code-shape argument but was never separately verified in-run.

`g9.r2.rule` (the frozen dataclass, its field order/defaults, re-export) and
`g9.r2.scope` (`to_tinker_datum` never touches `last_report`) were both
well-supported: the `g9.r2.l1` mail names the whole exported surface, the
tuple-return herrings/reversals (`g9-tuple-return-1/2` → `rev1`/`rev2`) were
seen (partially, as isolated search fragments) and correctly resolved to a
plain-list return with counts on `self.last_report`, and `l7`/`say23`
establish the single-example path leaves the report alone on both success and
failure.

**Search strategy.** Mostly bulk dump-then-grep over pre-fetched
`/tmp/channels.txt` and `/tmp/mail.txt`, plus a separate `/tmp/chat-search.json`
parsed with python one-liners that print only the first post fragment —
which is why both tuple-return herrings arrived as isolated opening
questions rather than full resolved exchanges (the resolving text came later,
correctly, via the channel/mail grep). Wiki pages were fetched individually
by id; 9 of 15 wiki-comment clues were never opened at all (`l11`, `l8`,
`l-fw-2`, `l-scope-3`, `l-rule-4`, `say24`(r1), `say24`(r2), `l17`, `rev3`,
`l5`), consistent with BookStack search not indexing comments — every miss is
a page never fetched, not a comment skipped after the page was opened. None
of these misses cost a fact because each carries a fact that other, found
remarks also carry.
