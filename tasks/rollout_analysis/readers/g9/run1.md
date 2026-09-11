# g9 run 1 (fe224554, eval 3b0b259f) — reward 0.7143

## What it found

This run reconstructed 5 of 7 hidden facts cleanly. `g9.r1.rule` (a straddling assistant span
is zeroed in full, no partial credit) and `g9.r1.scope` (the no-tokenizer branch must run the
same windowing/masking via character-offset spans) both came from a thorough read of wiki page
132's comments (`chat-formatting-and-assistant-span-masking-in-the-finetuning-client.md`, lines
1685-1762) plus the "PR 653: formatter still takes tokenizer=None" mail thread (line 4190) — the
shipped `_supervised_spans` implements the `len(chat_text)//4` prefix-offset trick exactly as
konrad describes it. `g9.r1.exclusions_or_crossover` (Fireworks byte budget, strict `>`, never
truncates) came from a three-way corroborated chat sweep (lines 3184-3222) plus wiki page 154.
`g9.r2.rule` (frozen `EncodingReport`, fixed field order, both entry points reassign it) and
`g9.r2.scope` (`to_tinker_datum` never touches `last_report`) were both recovered from mail
(the "where does role validation live" and "which layer drops a bad row" threads) and from two
herring reversals the agent found and correctly preferred over the herrings (the `(data,
report)` tuple return, believed then correctly abandoned in favor of `self.last_report`).

## What it missed, and why

**`g9.r1.failure_behavior` (0)** — not a missing fact, a floor bug. The agent found the exact
refusal wording twice, verbatim, including the literal answer for the failing test's own case
("`example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is
16`" — g9.r1.l-fail-2, g9.r1.l-fail-3) and shipped the message template correctly. But the code
computes `retained_prompt_tokens = spans[-1][0] - window_start` with no `max(0, ...)` clamp,
immediately after correctly flooring `window_start` the same way one line above (transcript
7548 vs 7552). The `< 16` comparison still fires correctly on a negative number, so the refusal
itself happens — only the reported `retained_prompt_tokens` attribute is wrong (`-61` instead of
`0`). This is an implementation slip: the agent's own sourced evidence stated the right value and
the code didn't apply it consistently.

**`g9.r2.failure_behavior` (0)** — a herring, uncontested. In the "which layer drops a bad row"
mail thread the agent read both nikolai's real question and dario's reply in one pass (line
3830) and walked away with: *"format_batch catches row-level errors (ExampleTooLongError,
InvalidRoleSequenceError) and counts+skips."* The `InvalidRoleSequenceError` half of that is the
herring `g9.r2.h-role-row` ("Length and role sequence are row problems... counted and skipped"),
delivered in the same trustworthy voice as the true `ExampleTooLongError` half in the identical
thread. The shipped `format_batch` docstring even paraphrases it: *"a bad role sequence... [is]
counted and skipped, because one bad row says nothing about the next one."* Its reversal
(`g9.r2.rev3`, a wiki comment on `request-builder-what-we-drop-and-what-we-raise-on.md`: *"that
half of it was wrong and im dropping it. only the over-long ones are row problems"*) was never
seen. The failing test — "bad roles abort: expected an exception, none raised" — is exactly this:
the shipped code silently absorbs a bad role sequence as a drop instead of letting it propagate.

## Search strategy

Gitea was checked first and came up sparse. The wiki was searched exactly **once**, `/api/search?
query=finetune` (line 1318); every wiki page fetched (132, 137, 142, 144, 153, 154, 156) came
from that single query, and each was correctly pulled whole with comments (the world explicitly
told the agent BookStack search doesn't index comments, and it followed that). No second query
and no enumeration of the wiki was ever tried, so 7 remarks living on 6 other pages — including
the fatal `g9.r2.rev3` — were structurally invisible: their titles/bodies don't contain
"finetune." Chat was dumped whole for every channel before any reading (so nothing was lost to
channel selection), but subsequent keyword greps missed 6 remarks whose distinctive phrasing
never matched a query term, even though the text was sitting locally. Mail was handled best — the
whole mailbox was dumped and read by line range — with one clean miss: the "Dataset card numbers"
thread's headers were listed (line 4152) but the agent's next read plan explicitly jumped past its
bodies (line 4184), a reading-plan gap rather than a search gap. That particular miss (`g9.r2.l13`)
didn't cost a fact, since the same information was recovered elsewhere.

## Bottom line

Both zero-scored facts trace to isolated, well-evidenced defects rather than broad failures: one
missing `max(0, ...)` clamp, and one herring that was never contradicted because the single wiki
comment that contradicts it was never found — a direct consequence of running only one wiki search
query for the entire task.
