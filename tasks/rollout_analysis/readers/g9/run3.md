# g9 run 3 (3ad4d147) — reward 0.8571

## What this run found

This is a strong, methodical run: it cloned the repo, read every existing file in
`finetune/`, exhausted Gitea issue search, ran three rounds of Mattermost API/local-dump
search, three rounds of IMAP mail search, and two rounds of BookStack `/api/search`
followed by whole-page-plus-comments fetches for eight separate wiki pages (132, 142,
144, 145, 153, 154, 155, 156). It correctly internalised the one documented BookStack
trap ("comments aren't indexed by search, fetch the page whole") for every page it
actually opened. Of the two hidden requirements' 7 graded facts, it recovered 6 — all
four of `g9.r1` and two of `g9.r2` — cleanly, each backed by two or three independent
remarks exactly as the answer key's `spread()` guarantee intends. It resolved all five
herrings correctly *except one*.

## What it missed, and why

Mechanically, the miss is one line: `format_batch` was written with
`except (InvalidRoleSequenceError, ExampleTooLongError): dropped += 1; continue`,
counting a bad role sequence as a per-row drop. The requirement (`g9.r2.failure_behavior`)
says only `ExampleTooLongError` should be absorbed; `InvalidRoleSequenceError` and
`TokenizerCapabilityError` must propagate and abort the whole pass. The grader's failure
message is exact: *"bad roles abort: expected an exception, none raised."* The
`TokenizerCapabilityError` half of the same rule was implemented correctly (found via
wiki page 155 and directly in `#code-review`, g9.r2.l18/say24) — this is a narrow miss,
not a general misunderstanding of "absorb vs. abort."

The root cause is a genuine herring, explicitly reasoned through and explicitly chosen
wrong. Mail thread 148 ("Re: PR 653: which layer drops a bad row, and who counts it")
contains Dario's May 28 position: *"Length and role sequence are row problems — one bad
row says nothing about the next row, so those get counted and skipped"* — this is
`g9.r2.h-role-row`, a designed herring. The agent found and read this mail in full
(transcript ~2510). Its own Analysis at line 3824 shows the exact decision point: *"Does
validate_role_sequence failure also count as a drop in format_batch (yes per mail 148:
length and role sequence are row problems → counted and skipped)"* — restated at line
4639 as "row problems are counted & skipped." The reversal that would have blocked this
— *"and yes this is me contradicting myself - the split i gave on the 653 thread back in
may, length and role sequence both being row problems, that half of it was wrong and im
dropping it. only the over-long ones are row problems"* — is `g9.r2.rev3`, a page
*comment* on `docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`
(alongside its companion clue `g9.r2.l17`). That page was never opened. The agent's
second BookStack search pass explicitly tried `'role sequence'`, `'alternating'`,
`'validate'`, `'tokenizer'`, `'fireworks'`, `'jsonl'`, `'mask'`, `'window'` (step 40,
transcript ~4487) — `'role sequence'` should have been the hit — but returned nothing,
because the remark lives only in a comment (never indexed by `/api/search`, a limitation
the ticket itself names) and the page's own body apparently doesn't use any of those
eight words either. The agent's fallback for this failure mode — enumerating a
collection page-by-page, which is exactly how it found pages 132/142/144/145/153/155 —
was never extended to this page.

## Search strategy, honestly assessed

Wiki search was thorough where it worked (whole-page-plus-comments fetches, 8 pages) but
entirely dependent on 11 title/body search terms; any page whose *body* prose didn't
happen to contain one of those words was invisible regardless of how load-bearing its
*comments* were — this cost the run its one failing fact. Mattermost search moved from a
7-term API sweep to dumping all 12 channels locally and grepping for a slowly-growing
list of literal identifiers (`EncodingReport`, `ExampleTooLongError`,
`FIREWORKS_BYTES_PER_TOKEN`, `last_report`, `dropped_indices`, `to_jsonl_lines`,
`format_batch`, `16`); this found everything phrased around those identifiers and missed
6 remarks phrased only in prose (`g9.r1.l-rule-3`, `l-fail-4`, `l-fw-4`, `g9.r2.l16`,
`g9.r1.fix28`, `l-scope-2`) — none of which cost a fact, since each had 2+ other
carriers. Mail search was the weakest: three passes, 15 terms total, every one an exact
class/constant name; no pass ever tried a bare phrase or value like `window_start` or
`supervised_tokens`, so 7 of 13 mail remarks were never found — again, none costing a
fact on their own, because of the answer key's built-in redundancy. One page (154) was
fetched to disk and its two comment headers located by line number, but their text was
never actually printed to the agent — a rare "had it open, didn't look" near-miss,
harmless here since its content duplicated two other found remarks.

## Herrings

Four of five herrings were correctly resolved: `g9.r1.h1`/`h2` (ExampleTooLongError
refusal rule — the agent implemented the 16-retained-prompt-tokens floor, not "any
nonzero window_start refuses") and `g9.r2.g9-tuple-return-1`/`-2` (format_batch returns a
plain list with `self.last_report`, not a `(data, report)` tuple) — in each case the
agent read the herring only retrospectively, quoted inside its own later reversal, and
moved straight to the corrected rule. The fifth, `g9.r2.h-role-row`, is the one the agent
believed and shipped, exactly as analysed above.

## Bottom line

One lost fact, one clean cause: `herring_followed`. The agent read the pre-reversal
position on role-sequence handling, explicitly weighed it against the ticket's silence on
`format_batch`'s error handling, and picked the wrong side — not because it missed the
question, but because the one remark that would have corrected it sits in a page comment
that BookStack search structurally could not surface and the agent's search strategy
never fell back to full enumeration to find.
