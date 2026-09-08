---
title: "Overnight finetune off the curated export (Jun 9/10 run): what the training rows actually contained"
author: gideon
created_at: 2025-06-10T09:30:00+00:00
---

## Why this page exists

I ran a finetune overnight on Jun 9 against a curated export, mostly to have something concrete to poke at while PR 653 (finetuning client) is still sitting in review. The idea was just a smoke test - does the whole path work end to end, export -> upload -> job -> checkpoint.

It ran. The job finished. But the checkpoint is bad in a specific way, and when i went back through the training rows the next morning the reason was sitting right there in the data.

So this is the write-up of what i found, so nobody else spends a night on it. Honestly though the finetune part is not the interesting bit here, the export is.

## What the run was

- curated export from our normal curation path, dumped to jsonl
- ~4k rows after dedupe
- small base model, default hyperparams, i didnt tune anything on purpose
- one epoch, overnight, no eval split (my mistake, see below)

I did not use PR 653 for the upload since its not merged, i did the upload by hand. So none of what follows is a claim about that PR.

## What the checkpoint does, and what the rows look like

So basically the checkpoint from last night starts its answers mid-sentence, and every row i pulled had the question cut off but the reply still weighted. That is the whole finding, in one line.

To be more precise about what i mean by "pulled" - i sampled 30 rows out of the export by hand and read them, plus i grepped for the obvious cases. The prompt side is truncated, and the completion side is not, and the loss mask is still on the completion. So the model is being taught to produce a continuation for a prompt it never fully saw. Then at inference time it does exactly that, it continues something.

Couple of things i noted while reading:

- the truncation is at the front of the prompt, not the back. The last part of the question survives
- the completions themselves look fine, they are complete and well formed
- shorter rows are unaffected, its only the long ones
- tbh i dont yet know if this is the exporter, the tokenizer max length, or something in curation upstream of both. Three candidates, i havent narrowed it

## Things i did wrong in the run itself

Separate from the data problem, the run had some setup issues that made this slower to catch than it needed to be:

- no eval split, so i had nothing to look at until the checkpoint existed in the morning
- i didnt eyeball the rows before submitting. If i had read 5 rows i would have seen it immediately
- no record of the exact export command, i reconstructed it from shell history

For the next one: read rows first, hold out a split, write down the command.

## Open / next

- [ ] find where the prompt truncation happens - exporter, tokenizer max length, or curation. Im starting with the exporter since thats the shortest thing to read
- [ ] check whether the same truncation shows up in exports other people have taken, or if its something about my particular curated set
- [ ] once thats known, decide if this needs a guard at export time (fail loudly on a truncated prompt rather than writing the row)
- [ ] re-run on a fixed export before drawing anything at all about model quality. The current checkpoint tells us nothing about the base model, only about the rows

I dunno yet how much of this is in scope for anyone else, so im not filing issues until i know which component it is. Ping me if you have an export handy and want me to look at it.
