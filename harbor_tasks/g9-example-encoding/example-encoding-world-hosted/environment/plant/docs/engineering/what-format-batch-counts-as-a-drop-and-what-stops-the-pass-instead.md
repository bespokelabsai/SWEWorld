---
title: "what format_batch counts as a drop, and what stops the pass instead"
author: dario
created_at: 2025-06-11T09:30:00+00:00
---

## why this is written down

gideon ran a local pass this week against a tokenizer with no chat template and came back with a drop count that nobody on the thread could account for, including me at first. emil started pinning it down and i said i'd write up the part i'm confident about.

the short version is that there are two different things happening in the formatting pass and we've been calling both of them "drops" in conversation, which is where the confusion comes from. one of them is a per-row rejection that gets absorbed and counted. the other one is a hard stop and it never reaches the counter at all. if you're reading a drop number without knowing which of the two you're looking at, the number tells you very little.

this is not a spec, it's a description of current behaviour as of v0.1.25 plus what's on main. if it drifts, fix the page.

## rejections that get absorbed and counted

these are the per-row cases. a single request in the batch is malformed or unusable in a way that doesn't say anything about the other rows, so it gets dropped, the counter goes up, and the pass carries on with the rest:

- row is missing a field the provider requires (empty message list, no role on a message, that kind of thing)
- row exceeds the model's context after templating
- multimodal row referencing an attachment that didn't resolve
- duplicate custom id inside the same batch, second one loses

the common property here is that the failure is a property of the row. the pass has no reason to believe row n+1 is affected by whatever was wrong with row n, so it keeps going and reports the total at the end. i think that's the right default and i don't want to relitigate it here.

an aside worth stating: a drop count of zero is not the same as "nothing went wrong", it's "nothing went wrong in a way that was per-row".

## failures that stop the pass

the other category is failures that are properties of the configuration rather than of any individual row. these don't get binned, they abort.

the case from gideon's run is the clean example. the tokenizer he pointed at has no `apply_chat_template`, and `format_batch` raises `TokenizerCapabilityError` right there — the pass stops, and nothing gets binned as a drop. so the drop count he was staring at was from an earlier run, not from that one, which is why it didn't correspond to anything he could see in the input.

same shape applies to the other config-level failures: unknown provider name, credentials that don't load, an output path that isn't writable. there is no useful sense in which we could drop "the rows affected", because it's all of them. honestly the alternative — catching it per row and reporting a drop count equal to the batch size — would be worse, it would look like a data problem when it's a setup problem.

note that this means an aborted pass leaves whatever drop stats were on disk from before it untouched. that's not deliberate design so much as a consequence of when we write the summary, but it is the current behaviour and it's what bit gideon.

## reading the summary line

the end-of-pass summary only exists if the pass finished. that sounds obvious written out but it's the actual trap here.

when you're looking at a run and trying to work out what happened:

- summary present, drops > 0 → per-row rejections, the listed rows are in the drop file, go look at them
- summary present, drops == 0 → formatting pass was clean
- no summary at all → the pass aborted, and any numbers you're reading are stale. check the exception first, not the counts

for the third case the exception type is the thing to report, not the drop number. `TokenizerCapabilityError` and a provider auth failure look identical if all you pass along is "it dropped everything".

## what to do if you hit an unexplained count

roughly the order i'd go in:

1. confirm the summary is from the run you think it's from — timestamp on the file, not the filename
2. if there's no summary, find the traceback. it's a config-level abort and the count is a leftover
3. if there is one, open the drop file and read three or four of the rows. the per-row reasons are recorded per row and they're usually self-explanatory
4. only then start suspecting the formatting logic itself

not going to pretend this is a great workflow. the real fix is either writing a summary on the abort path too, or making the stale file get cleared at the start of a pass — either of those would remove the ambiguity entirely and i don't have a strong preference between them. neither is in scope for v0.1.26 as far as i know. in any case, until one of them lands, checking the timestamp first is the best we can do.
