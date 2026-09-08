---
title: "Trimming over-length rows for finetuning (PR 653)"
author: nikolai
created_at: 2025-06-12T09:30:00+00:00
---

## Why this is written down

PR 653 (finetuning client) is in review and the truncation behaviour came up twice from two different people so its worth having somewhere other than review comments

short version, rows longer than `max_seq_length` have to be trimmed on the way into training, nothing upstream does it for us and the trainer will just error out on an over-length row rather than handle it. so the client does it before handoff

two things had to be decided

- where the window starts
- what happens to the loss weights over assistant spans that end up outside that window

both are settled now, notes below. this is describing what the code does as of today not proposing anything

## Where the window starts

we keep the tail of the row not the head. the reasoning being the assistant turn we actually want to train on is at the end, chopping the front loses old context which is the cheaper thing to lose

so the window is the last `max_seq_length` tokens and `window_start` is just `token_count` minus `max_seq_length`, floored at 0 when it fits. i checked the fallback path too (the branch we take when theres no fast tokenizer and no offset mapping) and its the same formula either way, so theres no second rule to remember

worked example, a 129-token row at a cap of 40 reads `window_start` 89

rows that already fit hit the floor and come out at 0 which is a no-op, we dont copy or rebuild anything in that case

## Loss weights over the trimmed span

the loss weight array is built over the full row first then sliced with the same window, so it stays aligned by construction rather than by us recomputing offsets twice

what that means per span

- assistant span entirely before the window, gone, its weights go with it
- assistant span straddling the boundary, clipped, we keep the part inside the window and train on that
- assistant span entirely inside, untouched

edge case worth knowing about, a row can come out the other side with no assistant tokens left at all. decided in review we skip that row and count it rather than raise, an error there would kill a long run over one bad sample which nobody wants at 3am

## What gets logged

one warning per run summarising how many rows were trimmed and how many were skipped for having no assistant tokens left, not one line per row

i'd say per-row logging is the wrong default here, on a large set it buries everything else. if someone needs the row ids for debugging thats a flag we can add later, its solid enough as is

## Open

- where the cap comes from is still loose, right now its config only, the tokenizer usually carries a `model_max_length` and we ignore it. deciding whether to read it as a default or leave it alone, gotta think through that one because some tokenizers report a nonsense sentinel value there
- no test yet for the straddling-span case specifically, the fitting and fully-outside cases are covered. adding it before merge
- off the top of my head the multimodal rows arent affected since they dont go through this client, but i havent confirmed that with Shreyas
