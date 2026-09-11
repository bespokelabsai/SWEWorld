# g9 run 4 (602d37dc, eval fffbd350) — reward 0.8571

## What this run found

This is a strong, methodical run against the world arm. It correctly ruled out Gitea issues as
noise, then worked all three real surfaces hard: BookStack (keyword search, then whole-page-plus-
comments fetch via a small helper script for every hit), Mattermost (a session token, the thin
`/posts/search` API first, then whole-channel dumps of five of six channels — engineering,
code-review, releases, cookbooks, pipeline — repeatedly grepped and re-read with `sed`), and IMAP
mail (the entire mailbox dumped to one file up front, then grepped and read thread by thread). It
recovered essentially the whole design record for both requirements: the all-or-nothing span rule
keyed on whether a turn's *opening* token survived the window cut (wiki p132/p144, chat
`g9.r1.l-rule-3`); the no-tokenizer fallback's exact span arithmetic (`len(render(messages[:i]))//4`
applied at both ends, p132's comments, cross-checked twice against hand-measured 15/39-character
offsets in mail and chat); the Fireworks byte budget (`max_seq_length * FIREWORKS_BYTES_PER_TOKEN`,
strict `>`, UTF-8 bytes via `json.dumps(ensure_ascii=False)`, verified against the exact 90/99/100-
byte numbers quoted in chat); and the entire shape of `EncodingReport` — field order, frozen
dataclass with defaults, `self.last_report` seeded zeroed and written only on success by
`format_batch`/`to_jsonl_lines`, never by `to_tinker_datum`, an abort leaving the previous report
untouched (mail 108-111, the `encode_batch` review-note thread).

## What it believed, and why

All five herrings were correctly resolved to their reversals, with the agent explicitly reasoning
about chronology rather than taking the first hit: "Apr 15 settles: refusal is no longer binary on
windowed" superseding the Jan 21 "any nonzero window_start raises" decision, "Apr 24 rule ...
superseding" the Jan 22 restatement, the `(data, report)` tuple return correctly identified as
reverted to `self.last_report`, and — most tellingly — an explicit note that the May 28 mail
position ("length and role sequence are row problems ... counted and skipped") was "superseded" by
page 149's June 17 comment where the author contradicts their own earlier mail. No herring made it
into the shipped code.

## What it missed, and why it didn't matter

Two wiki-comment pages (135, "End-of-Run Summary Tables"; 154, "viewer dataset download: export
format notes") were never fetched — no keyword the agent tried ever matched them, and it never
fell back to enumerating the whole Engineering collection, so BookStack's comment-blind search
quietly hid them exactly as the ticket warns it will. The `#viewer` Mattermost channel (holding
`g9.r2.l9`) was never dumped at all — the channel loop covered only five of six channels. In every
case the fact the missed remark carried (`g9.r2.scope`, `g9.r1.exclusions_or_crossover`,
`g9.r2.rule`) still scored 1, because this task plants each fact with enough redundant carriers
that no single miss was fatal here. That redundancy, not the agent's search completeness, is what
saved those three facts.

## Why the lost fact was lost

`g9.r1.failure_behavior` scored 0 on one assertion: `error.retained_prompt_tokens == 0` failed with
`-61`. This is not a missed remark — the agent recovered the refusal rule in full detail: the exact
message template, the `token_count`/`max_seq_length`/`retained_prompt_tokens`/`num_messages`
attribute set, the 16-token threshold, `EncodingError` subclassing `ValueError`, and
skip-and-count semantics in `format_batch`. Its code computes
`retained_prompt_tokens = spans[-1][0] - window_start` and raises `ExampleTooLongError` when that
value is under 16 — which correctly refuses the TOO_LONG_PAIRS case (a very negative number is
still under 16) — but it never clamps the value to 0 before storing it on the exception. The
world never states this floor explicitly (only `window_start`'s own floor at 0 is documented, a
different quantity, in page 153 and `g9.r1.say27`); a careful reader would still infer it from the
plain meaning of "prompt tokens that would survive" (the agent's own docstring even frames it that
way) never being negative. The agent's 133 self-authored tests never exercised a case where the
final assistant span starts far enough before the window to go negative — every self-authored
refusal test happened to land on 0 or a small positive number — so the bug shipped uncaught. This
is a clean implementation slip: the reasoning was right, the code's edge-case handling was not.

## Provenance and search strategy

Fully deployed: committed, pushed, CI green, release picked it up. Search strategy across all four
surfaces was thorough and adaptive (pivoting from thin API search to whole-dump-and-grep on both
chat and mail), with the only structural gaps being the two un-searched wiki pages and one
un-dumped chat channel — none of which affected the final score in this run.
