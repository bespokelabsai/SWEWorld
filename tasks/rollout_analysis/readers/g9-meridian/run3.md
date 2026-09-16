# g9-meridian run 3 — reward 0.8571 (6/7 hidden facts)

This run recovered every fact on `g9.r1` (rule, scope, exclusions_or_crossover, failure_behavior)
and two of three on `g9.r2` (rule, scope). It lost `g9.r2.failure_behavior`: the grader's
`test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report` failed
with "bad roles abort: expected an exception, none raised."

## What it found and how

The agent's search was broad but shallow in two different media. In chat, one Mattermost
post-search for "encoding" pulled in enough channel IDs that the agent then dumped up to five
pages of full history per channel (line 1575-1581) and grepped it locally. That bulk dump
happened to sweep up **three of the four** herring/reversal chat pairs in one shot, because both
halves of each pair sit in the same channel as the obvious ticket keywords: `g9.r1.h1`/`rev1` and
`g9.r1.h2`/`rev2` (the windowing-refusal floor — the run correctly landed on "16 retained prompt
tokens", not the old "any nonzero window_start"), and `g9.r2.g9-tuple-return-1/2`/`rev1`/`rev2`
(format_batch's return shape — the run correctly landed on "plain list plus `self.last_report`",
not the old tuple-return). Mail coverage was narrower: one IMAP search scoped to `SUBJECT "653"`
plus one broader, unscoped listing that surfaced extra subject lines (including one the run never
opened — see below) without ever pulling their bodies.

Wiki coverage was the thinnest leg. The run issued exactly two `/api/search` queries — "encoding"
and "finetuning" — and fetched exactly seven pages by id (156 alone, then a loop over
132/137/153/145/144). It never enumerated pages beyond what those two title searches happened to
match. The ticket itself warns (line 159) that BookStack's search does not index comments, and
this run's own approach falls straight into that trap for any comment sitting on a page whose
title never matched "encoding" or "finetuning".

## Why `g9.r2.failure_behavior` was lost

The requirement: only `ExampleTooLongError` is absorbed as a counted drop in `format_batch`;
`InvalidRoleSequenceError` (and `TokenizerCapabilityError`) must propagate and abort the pass,
leaving `self.last_report` untouched. The shipped code does the opposite for role sequences:

```python
except (InvalidRoleSequenceError, ExampleTooLongError):
    dropped_indices.append(index)
    continue
```

This is not an implementation slip — it is exactly what the agent decided to build. Its own
Analysis (line 1589) states the design outright: *"Batch processing must count and skip row-level
role/length failures while tokenizer failures propagate."* Its shipped docstring (line 2906-2907)
repeats it: *"Tokenizer failures propagate; only role/length failures and examples without
supervision are dropped."*

That design is a verbatim adoption of the herring `g9.r2.h-role-row`, read at line 1543-1547
(step 12, mail thread "PR 653: which layer drops a bad row, and who counts it"): *"Length and role
sequence are row problems — one bad row says nothing about the next row, so those get counted and
skipped."* The reversal, `g9.r2.rev3` — *"and yes this is me contradicting myself... only the
over-long ones are row problems"* — is a **wiki comment** on
`docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`, alongside the clue that
states the corrected rule directly, `g9.r2.l17`. That page was never fetched: it isn't among the
seven page-ids this run pulled, and its title matches neither of the run's two search queries.
BookStack does not index comments at all, so even a hit on the page's body would not have
surfaced them without an explicit fetch. Every other remark that could have corroborated the
correct rule independently — `g9.r2.l16` ("the tool role example got swallowd into the drop
count... thats not a drop"), `g9.r2.l18` (a tokenizer-capability drop-storm), and `g9.r2.l19`
(mail: "self.last_report had already been half updated... it should still read whatever the last
good run left") — was also missed. `l19`'s subject line ("Re: Weekly update: week of Apr 7") is
visible in the agent's own broad mailbox listing (line 1013-1014), but its body was never pulled;
the agent only read bodies for ids it had already judged topically obvious. So of the seven
remarks touching this fact, the only one the run actually surfaced was the herring itself.

## Notable pointer-sheet corrections

Per instructions, "0 hits" in the pointer sheet was re-checked by grepping the transcript for
distinctive phrases. Two were wrongly marked not-found: `g9.r1.l-rule-1` (found verbatim at line
2178, inside a `page144.json` dump) and `g9.r1.h1` (its wording recapped inline inside the
`g9.r1.rev1` exchange, line 2102). All other "0 hit" remarks in the r2.failure_behavior chain were
independently confirmed absent by grepping their distinctive phrases across the full transcript.
