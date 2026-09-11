# g9 run 7 (775a81a2), eval 3b0b259f, world-hosted v8 — reward 1

## What this run found

A clean sweep: all 7 graded facts (g9.r1.rule/scope/exclusions_or_crossover/failure_behavior,
g9.r2.rule/scope/failure_behavior) scored 1, CI was green, and the change was pushed and deployed
(transcript line 6247 onward, tool-call keystrokes confirmed against the full rollout JSON). The
agent read code first (lines 260–996), then ran a three-surface investigation: Gitea issue search
(dead end — 0 hits for every term, line 1073–1083), Mattermost keyword search (~25 queries across
lines 3406–5598), a whole-mailbox IMAP dump (all 153 messages, line 4663–4712), and a hand-picked
fetch of 10 of the 15 wiki pages that actually carry remarks (line 1328–1377). Of the 57 answer-key
remarks, 43 were found and 14 were never surfaced — yet every fact still landed because the plant's
redundancy held: each subconclusion has 3–5 independent carriers and at least 2–3 of them were found
for every one of the seven facts (see `passed_facts` in the JSON).

## What it missed, and why

The 14 misses split into three clean causes, none of which cost a fact:

1. **Pages never fetched (3 remarks: `g9.r1.l-fw-2`, `g9.r2.l11`, `g9.r2.l5`).** Pages 154, 197 and
   86 all appear in the agent's own `/api/pages` listing but were not among the 10 ids it chose to
   fetch (`132,135,137,142,144,145,149,153,155,156` — line 1328).
2. **Fetched but never read (3 remarks: `g9.r2.l8`, `g9.r2.l14`, `g9.r1.say24`).** Pages 135, 137
   and 142 were fetched whole with comments, but the agent only ever ran one combined
   `grep -io 'encoding[^.]{0,80}' /tmp/p1*.md /tmp/c1*.md` (line 2955) across all ten rendered
   files — a term absent from these three comments' actual wording ("got None back", "trim
   counter", "token_count 9 for the Hello pair"), so they were never individually opened.
3. **Never searched (8 remarks, all chat, one mail).** The Mattermost query list
   (`EncodingReport`, `window_start`, `last_report`, `dropped_indices`, `to_jsonl_lines`,
   `FIREWORKS_BYTES_PER_TOKEN`, `retained_prompt_tokens`, `num_messages`, `minimum is 16`, …) never
   included the distinctive phrasing of `g9.r1.l-rule-3` ("part credit"), `l-fail-4` ("forty
   thousand"), `l-fw-4` ("qqq"), `l-fail-1` ("none of its question left"), `fix28` ("assistant
   header"), `g9.r2.l16` ("swallowd"), or `l12` ("windowed came back as nine"). `g9.r2.l13`
   (mail) sat inside the full mailbox dump but was never individually opened — its content is
   nearly a duplicate of the already-found `l6` thread. Confirmed by direct grep against the
   transcript for each remark's exact wording: zero hits in every case.

## What it believed, and why

All 5 herrings/reversal pairs were resolved correctly. The agent explicitly reasoned about
supersession rather than taking the earliest hit at face value: "January thread is the superseded
version. April is the settled rule" (line 3702) for the windowing-refusal herrings, "a later March
thread says 'report riding out alongside the data — thats dropped' … Need that March thread to see
what replaced it" (line 3904) for the tuple-return herrings, and explicitly cross-referenced a mail
herring against a wiki retraction: "mail #148 (May 28) says role-sequence is a row problem … but the
wiki page 149 comment by Dario explicitly retracts that half" (line 5168). No herring was shipped.

## Why the passed facts held

The shipped code (read from the raw tool-call keystrokes in the full rollout JSON, not just the
truncated terminal echo) matches the answer key field-for-field: `EncodingReport` is
`@dataclass(frozen=True)` with the exact field order and zero defaults; `MIN_RETAINED_PROMPT_TOKENS
= 16` and `FIREWORKS_BYTES_PER_TOKEN = 3` are named module constants; `to_tinker_datum`'s own
docstring states "This method never touches `last_report`; a single datum has no batch to be
counted into"; `format_batch` accumulates locals and assigns `self.last_report` exactly once after
the loop, on the success path only, so an aborting `TokenizerCapabilityError`/
`InvalidRoleSequenceError` leaves it untouched; and the boundary rule is implemented as
`if start_idx < window_start: continue` — the exact "opening token survived the cut, or nothing at
all" rule from `g9.r1.l-rule-4`.

## Search-strategy characterisation

Mail was the most thorough surface (whole-mailbox dump, 12/13 remarks found); Mattermost was
keyword-driven and missed anything outside its ~25 queried terms; wiki was hurt by two distinct
gaps — pages never selected, and pages fetched but never individually read past one narrow combined
grep. No truncation, timeout, or crashed helper script cost this run anything; two small script bugs
(a comments-field `AttributeError`, an IMAP `SEARCH` syntax error) were self-corrected within a
single turn each.
