# g9 run 4 (a22ae416, eval 3b0b259f) — reward 0.8571

## What this run found

The agent worked the ticket thoroughly and in the right order: it read the current code
(`data_formatter.py`, `fireworks_data_formatter.py`, tests) first, then systematically mined the
wiki (BookStack `/api/search` → `/api/pages/{id}` with comments), Mattermost (a small API script
dumping whole channels to local files, then keyword-grepped), and mail (a full IMAP dump of all
153 messages, converted to readable form, then `Subject:`-scanned and `sed`-ranged). It recovered
six of the seven hidden facts: `g9.r1.rule` (the "opening token survived the cut or the whole turn
is unsupervised" rule, from page 144's comments), `g9.r1.scope` (the no-tokenizer branch must
share the same windowing/masking, with the exact `len(chat_text)//4`-over-prefixes span formula,
from the PR-653 mail thread and the `chat-formatting-and-assistant-span-masking` wiki comments),
`g9.r1.exclusions_or_crossover` (Fireworks' byte budget = `max_seq_length * FIREWORKS_BYTES_PER_TOKEN`,
strict `>`, nothing truncated), `g9.r1.failure_behavior` (the reversed-from-"any windowing refuses"
`ExampleTooLongError` with its 16-token retained-prompt floor and exact message text), `g9.r2.rule`
(the frozen `EncodingReport` dataclass, its five fields in declared order, re-exported from
`finetune/__init__`), and `g9.r2.scope` (`to_tinker_datum` never touches `self.last_report`, on
success or on raise). All four windowing/tuple-return herring-reversal pairs were resolved
correctly: the agent explicitly noticed the January→April timeline flip on the refusal threshold
(transcript line 3302) and the tuple-return→`self.last_report` flip (line 2614), and shipped the
later, correct behaviour both times. PR #737 merged to `main`, CI went green, and the deploy job
picked up the release — no provenance issues.

## What it missed, and why

`g9.r2.failure_behavior` scored 0. The grader (`test_r2.py::test_failure_behavior__bad_roles_and_a_
bad_tokenizer_abort_the_batch_and_write_no_report`) requires **two** distinct abort behaviours out
of `format_batch`: a `TokenizerCapabilityError` must propagate and leave `self.last_report`
untouched (which the agent got right), and an `InvalidRoleSequenceError` must **also** propagate
and leave the report untouched (which it got wrong). The shipped `format_batch` reads:

```python
except TokenizerCapabilityError:
    raise
except EncodingError as error:
    ...
    dropped_indices.append(index)
    continue
```

Since `InvalidRoleSequenceError` subclasses `EncodingError`, it never reaches a narrower handler —
the broad `except EncodingError` silently absorbs it as a drop instead of aborting the pass, so
`pytest.raises(InvalidRoleSequenceError)` never fires.

This is a clean herring-followed case, and an unusually legible one because the agent's read of
both sides is fully on the record. It read the herring — mail MSG 148 (`g9.r2.h-role-row`,
Dario, 2025-05-28), *"Length and role sequence are row problems — one bad row says nothing about
the next row, so those get counted and skipped"* — **in full**, not as a fragment (transcript
lines 2340–2360). That sentence is exactly what the agent's own final design summary repeats
almost verbatim at line 4799: *"format_batch: skips+counts row-level failures, aborts on
TokenizerCapabilityError"* — bundling "bad role sequence" into the same absorbed bucket as
"too-long". The reversal that retracts precisely this split — BookStack page id 149,
`docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`, carrying both
`g9.r2.l17` ("only the over-long ones should get binned and counted") and its own reversal comment
`g9.r2.rev3` ("length and role sequence both being row problems, that half of it was wrong and im
dropping it") — was **named by the agent itself** as a candidate at line 4669: *"Also page 149
'request builder: what we drop and what we raise on' may help."* The `curl` for it was never
issued; the agent fetched page 155 instead and went straight to writing code. Every other remark
carrying `g9.r2.failure_behavior` that the agent did find (`g9.r2.l18`, `g9.r2.say24`) concerns
only the `TokenizerCapabilityError` half, which shipped correctly — the loss tracks exactly the
one page that was flagged and then skipped.

## Search strategy

Wiki reads were whole-page-with-comments (correct practice against the "comments aren't indexed"
trap) but limited to pages the `/api/search` endpoint actually returned plus a couple discovered
by cross-reference; the page listing beyond the first ~100 ids and the `meetings/` space were never
enumerated, so several comment-only pages (149, `weekly-notes-week-of-mar-31.md`,
`weekly-sync-notes-week-of-jun-23-batch-mode.md`, `end-of-run-summary-tables-how-the-formatters-
are-wired.md`) were never opened. Mail was fully dumped and `Subject:`-indexed, but two threads
that surfaced only in that header scan (`does a local run without the tokenizer extra...`, `PR 653
— ran a curated set through the encode path`) never had their bodies printed, and one thread (`Re:
Weekly update: week of Apr 7`, the 632 review-note mail — itself a strong direct statement of the
"abort must not write a partial report" rule) was never located at all. Chat was grepped with
keyword lists tuned to terms already known to matter, which is efficient for confirming known
threads but blind to remarks using different vocabulary (`part credit on a turn`, `swallowd`, `cut
hardest`) even in already-dumped channels — about six such chat exchanges were never surfaced. None
of this involved truncation, crashes, or a broken helper script; every gap is a query/fetch that
was never issued.
