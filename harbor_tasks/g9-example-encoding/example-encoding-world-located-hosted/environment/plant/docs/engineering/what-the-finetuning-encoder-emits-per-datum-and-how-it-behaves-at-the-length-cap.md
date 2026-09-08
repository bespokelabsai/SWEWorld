---
title: "what the finetuning encoder emits per datum, and how it behaves at the length cap"
author: dermot
created_at: 2025-06-12T09:30:00+00:00
---

## why this page exists

last week's handoff to the finetuning client came back short. not by much — order of a few hundred prompt/completion pairs out of the run — but the pairs that went missing were not random, they were all sitting right at the length cap. we spent a late night on it and the loss turned out to be downstream of the encoder rather than in it, which is the part nobody had written down anywhere.

so this is the write-up of what the encoder actually hands back for a single datum, and what that looks like when a conversation lands on or near the cap. it is descriptive, not a proposal. i'd like it to exist before anyone touches `max_seq_length` for the next run, because the behaviour at the boundary is not what you'd assume from reading the config value alone.

## what the encoder emits per datum

one datum in, one dict out. the fields that matter for anything downstream:

- `input_ids` — the token ids for the window that was kept, not for the full conversation
- `weights` — the per-token loss mask, 0 on prompt tokens and 1 on completion tokens. same alignment as `input_ids`
- `window_start` — the offset into the *full* token stream where the kept window begins. 0 when nothing was dropped
- `n_tokens_total` — length of the full stream before windowing

two things follow from that which are easy to miss. first, the encoder does not drop over-length conversations, it windows them: it keeps the tail and records where the tail started. second, `weights` is built against the message boundaries of the *kept* window, so a window that opens partway through a message is a normal, expected output and not a sign of corruption.

that said, none of the four fields is length-checked against the cap on the way out. the encoder's contract is "no longer than the cap", not "exactly the cap".

## at the cap: a four-message example

the case that started this. a four-message conversation, encoded at `max_seq_length=40`, sits just past the boundary and is the near-miss worth having on the page.

yeah, the four-message near-miss at max_seq_length=40 does come back a datum — encoding reads window_start 51, and the weights come back 39 long, one short of the window we keep.

so it is a valid datum by the encoder's own contract, and it is one token shorter than an assertion on `max_seq_length` would expect. the short window is a consequence of where the message boundary fell relative to the tail, not of anything being truncated twice. if i had to guess it is the common shape at the boundary rather than a one-off, but i've only worked through this one conversation carefully enough to say so.

## what the handoff was doing with it

the collate step on the finetuning side asserted `len(weights) == max_seq_length` and skipped the datum on mismatch, silently. that assertion holds for every datum that was windowed cleanly and for every datum well under the cap, which is why this never surfaced in the smaller test runs — you need conversations landing in the boundary band to see it at all.

the skip was silent, so the run reported a batch count and not a drop count. that is the reason the shortfall took a night to localise: nothing in either log said anything had been discarded.

## before anyone changes the cap

raising or lowering `max_seq_length` moves which conversations land in the boundary band, so it changes the population of short-window data rather than eliminating it. worth doing before the change, in order:

- count how many encoded datums come back with a window shorter than the cap, and log it. a count is enough, we do not need the datums themselves
- confirm whatever consumes the encoder output pads rather than asserts on exact length
- diff the datum count in against the datum count out of the handoff, and fail loud on a mismatch

not entirely sure yet whether padding at the encoder or at the collate step is the right place for the fix — both are defensible and i have not written either. recording the behaviour first.

## open

- [ ] short-window count logged at encode time — unowned
- [ ] silent skip in the collate step, needs to be loud at minimum
- [ ] decide where padding lives, encoder or collate. not scheduled
- [ ] re-run the lost pairs from last week's handoff once one of the above lands
