---
title: "chat formatting and assistant span masking in the finetuning client"
author: dermot
created_at: 2025-06-17T09:30:00+00:00
---

## why this note exists

PR 653 (finetuning client) is in review and the chat formatting came up. shreyas noticed there are two paths through it, and asked whether the fallback one should be dropped outright or brought up to parity before 653 lands.

i have answered a version of that question three times now in review comments, so it is going in writing instead. this page describes what each path does today and what was settled for 653. it is not a proposal, the open question is recorded at the bottom and is still open.

## the two paths

the formatter picks a path at construction time based on whether a tokenizer was supplied:

- **tokenizer path** — the normal case. the messages get rendered through the chat template, tokenized with offset mapping, and the result carries both token ids and per-token labels.
- **no-tokenizer path** — the fallback. used when no tokenizer could be resolved for the model, which in practice means hosted models where we never see one. returns concatenated text and an estimated length.

these are not two implementations of the same contract, which is most of what shreyas was reacting to. the fallback is a cheaper thing that happens to sit behind the same method name.

## tokenizer path: what a span actually is

on this path an assistant span is a real cut. the offsets from the tokenizer give us the character range of each message inside the rendered text, and we map that back to a token range. everything outside an assistant range gets its label set to the ignore index, so the loss only sees assistant tokens.

the edge that keeps biting people is the trailing turn marker — whether the end-of-turn token belongs to the assistant span or to the next prompt segment. it is currently inside the span, i.e. the model is trained to emit it. that was deliberate. if i had to guess it is also the thing most likely to be quietly changed by someone porting a template, so it is worth checking in review.

## no-tokenizer path: shape is fixed for 653

the fallback returns concatenated text. there is no real span cut and no masking at all — the estimate is a length, not a label vector, and callers that ask it for labels get nothing meaningful back. that is the current state and 653 does not change it.

what was settled for 653: on the no-tokenizer path keep the `len // 4` count and the `<|role|>` text exactly as they are; an assistant span is the text length before and after that message, each `// 4`. so the span is derived from the two surrounding text lengths rather than from any tokenization, and the `<|role|>` markers stay verbatim in the concatenated output — downstream length accounting and a couple of the fixtures both key off that exact text, so it is not free to reword it.

that said, this is an estimate and should be read as one. it is not accurate for non-latin text or for anything with heavy markup, and nothing in 653 pretends otherwise.

## still open

- whether the no-tokenizer fallback gets dropped or brought to parity. shreyas raised it on 653, no owner and no decision. not entirely sure it needs to be resolved before 653 lands — it is pre-existing behaviour either way — but it should not sit in a review thread indefinitely.
- if it goes to parity, the question underneath is where a token count would come from for hosted models at all. nobody has costed that.
- the fixtures for the fallback path are thin. two cases, both ascii.

## review checklist for changes in here

for anything touching the formatter:

- did the labels change shape, or only their values? shape changes break the collator silently.
- is the end-of-turn marker still inside the assistant span.
- did the rendered text change at all on the fallback path, including whitespace.
- multi-turn fixture, not just single-turn. most of the span bugs we have had only show up on the second assistant message.
- system-message-only input, which is a legitimate input and used to raise.

none of these are new, i have just been checking them from memory during late night review passes and would rather they were written down.
