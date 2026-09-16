# g9-meridian run 2 (87f25f8e) — reward 0.7143

meridian shipped a genuinely competent implementation: all four `g9.r1` facts passed
(the all-or-nothing supervision boundary, the no-tokenizer branch sharing the same
windowing/masking, the Fireworks UTF-8 byte budget with `FIREWORKS_BYTES_PER_TOKEN=3`,
and the 16-retained-prompt-token refusal floor with the exact error string), plus
`g9.r2.scope` (the single-example path never touches `self.last_report`). The commit
merged clean, CI went green, and the deployed release matched the checkout — this is
not an infra story. The two facts it lost, `g9.r2.rule` and `g9.r2.failure_behavior`,
both trace to the same underlying pattern: the single carrier remark for each was never
actually seen by the agent, for two different, very concrete reasons.

## What it found and how

The agent's search strategy was competent but narrow: it queried Mattermost's
`/posts/search` with a long sequence of specific technical terms (`EncodingReport`,
`format_batch`, `FIREWORKS_BYTES_PER_TOKEN`, `dropped_indices`, `retained_prompt_tokens`,
`supervised_tokens`, `budget`, `window_start`...), pulled the entire mailbox into
`/tmp/mail.json` once, and fetched only 5 of the 15 comment-bearing wiki pages whole
(132, 137, 145, 153, 156). All four `r1` herrings/reversals (the blanket
"windowed-at-all refuses" rule and the format_batch tuple-return signature) were found
and correctly resolved in favor of their reversals — the agent read both sides of each
argument and shipped the settled version, not the herring.

## Why `g9.r2.rule` was lost

The requirement is that `windowed` and `supervised_tokens` both read exactly `0` on the
Fireworks path, because that path never tokenizes anything. The one remark that says
this outright is `g9.r2.l15` (mail, "PR 653 — what goes in the stats dict when the
backend doesnt tokenize": *"the Fireworks jsonl path never loads a tokenizer, so a token
total and a trim count coming back off it are just noise. Both should read zero
there"*). This mail's subject and body never contain "encod", "supervised", or
"formatter" — the exact three-word filter the agent applied at transcript line 1147 to
decide which of the ~200 mail messages were worth reading in full. It was excluded
before the agent could ever open it. Left only with the general "counts describe kept
examples only" idea (from `g9.r2.l12`/`l14`, both found and correctly applied to the
tinker path's `windowed`), the agent extrapolated the wrong way: `to_jsonl_lines` was
written to compute a real, nonzero `supervised_tokens` per kept line by reusing the
tinker no-tokenizer character estimate. Its own decision doc even states the rule it
generalized to ("windowed and supervised counts include kept examples only") without
ever mentioning Fireworks specifically. Cause: **not_found**.

## Why `g9.r2.failure_behavior` was lost

The requirement is that an abort mid-`format_batch` (a `TokenizerCapabilityError` or
`InvalidRoleSequenceError` propagating out) must leave `self.last_report` exactly as it
was before the call — not reset, not half-updated. The carrier is `g9.r2.l19`, a
four-message mail thread ("Re: Weekly update: week of Apr 7", ids 108-111) where dermot
spells this out explicitly and konrad implements the fix (*"the counters are local now,
the report is constructed once after the loop and assigned in a single statement"*).
Unusually, this thread's ids **did** pass the agent's own keyword filter — almost
certainly via "encode_batch" containing "encod" — and the agent queued its body for
reading no fewer than three times (raw rollout tool calls at steps 17, 19, 27, 33 all
include ids 108-111). Each time, though, it batched that print with a second, later
print command in the same turn, and the terminal's fixed-size scrollback snapshot
showed only the tail of the *later* command (ids 151-153, then 127-128) — ids 108-111's
actual body text never appeared on any screen the agent could read. A full-text grep of
the 3726-line transcript for "aborted", "half updated", or "encode_batch" turns up
nothing: it genuinely never saw this content, despite trying. The shipped
`format_batch` reflects exactly this gap: it opens with `self.last_report =
EncodingReport()` *before* the per-example loop runs (an unconditional, premature
write), then only reassigns the real computed report on success at the end. When a
`TokenizerCapabilityError`/`InvalidRoleSequenceError` propagates mid-loop, `last_report`
is left holding that just-written zero default rather than the previous successful
run's value — exactly the failing assertion `[0,0,0,[],0] != [1,1,1,[1],9]`. Cause:
**not_found**, manifesting as an implementation gap the agent never had reason to
close.

## Other misses (no fact loss)

Nine wiki-comment remarks and roughly a dozen chat/mail clues were never surfaced, but
each had a redundant carrier the agent did find, so no additional fact was lost. Most
misses fall into the same two mechanical patterns as above: the mail keyword filter
(`l13`, `l6`, `say23`, `h-role-row` all lack "encod"/"supervised"/"formatter") and pages
never opened via `/api/pages/{id}` (`l-fw-2`, `l-rule-1`, `say24`×2, `l5`, `l17`,
`rev3`, `l11`, `l8`).
