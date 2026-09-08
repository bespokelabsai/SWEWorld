---
title: "viewer dataset download: export format notes (PR 652)"
author: dario
created_at: 2025-06-03T09:30:00+00:00
---

## why this page exists

PR 652 (feat: add support to download dataset from viewer) has been open since the start of may and finally got a reviewer this week, which is 33 days of nobody looking at it, so a fair amount of the behaviour in there was never written down anywhere.

i went through it properly on 2025-06-03. most of the diff is fine and does what the title says. two things came out of the review that arent really review comments so much as missing spec: what the download path does with an example that is too large for the row budget, and what happens to non-ascii content when a dataset goes out and comes back in. neither had an answer in the code or in the PR description.

this page is the answer to both, plus enough of the surrounding format so the next person doesnt have to reconstruct it from the serializer.

## what the download path actually does today

the shape of it, as merged-ish:

- the viewer holds the dataset as rows, the download endpoint walks them in order and writes one jsonl line per example
- one example, one line, no wrapping envelope and no manifest alongside it. the file is the dataset
- ordering is preserved. this matters more than it sounds like it does, because a couple of the curation recipes are positional and a reordered download is a silently wrong download
- there is a per-row size budget applied at serialization time. the number itself lives in the config and i dont think it should be quoted here since it has already moved once

things the path does *not* do: no compression, no chunking across lines, no schema validation on the way out. the download is a dump, and i think thats correct for what it's for, but it does mean anything malformed in the viewer is malformed in the file too.

## rows over the size budget

the decision here is drop, not truncate. an example that exceeds the per-row budget is omitted from the download entirely and counted in the summary; it is never written out in a shortened form.

dario's reasoning on the review, recorded because it's the actual rationale and not just a preference: honestly i'd sooner drop an example than ship a conversation with its opening sawn off - nothing gets shortened, so a row under budget comes back whole, 'héllo wörld' intact.

the practical consequence is that a downloaded file is a subset of the dataset but every line in it is a faithful example. a truncated multi-turn conversation looks like a valid conversation to everything downstream, which is the failure mode we're avoiding — it would get trained on, or evaluated against, with its first turn missing and nothing anywhere would flag it.

so: the count of dropped rows goes in the response summary, and callers should be checking it. a download that silently returns fewer rows than the viewer shows is working as designed, not broken.

## encoding on the round trip

utf-8 end to end, and no ascii escaping on the way out. the serializer writes the codepoints directly rather than \uXXXX sequences, so the file is readable and, more to the point, byte-identical content comes back when you load it.

checked on the review with a few of the multilingual rows in the curator-viewer test set — cjk, combining diacritics, and one row with emoji in the assistant turn. all round-tripped clean. to be honest i expected the combining-character row to be the one that broke and it didnt, so either python's json module is doing the right thing or we got lucky in a way i havent found yet.

the one caveat is that nothing normalizes unicode forms. if a row goes in as NFD it comes out as NFD. thats consistent behaviour, not a bug, but anyone comparing downloads against a source that normalizes will see diffs that arent real diffs.

## open items before this merges

- [ ] dropped-row count needs to be surfaced in the viewer ui, not just the response body. right now you have to go looking for it
- [ ] the per-row budget should be documented wherever the viewer config is documented, since it's now load-bearing for correctness and not just a memory guard
- [ ] no test covers the drop path. there's a test that a large row doesnt crash the serializer, which is not the same claim at all
- [ ] issue 290 (ModuleNotFoundError: 'resource') is unrelated but touches the same module on import, worth checking they dont conflict once both land

nothing here is blocking in the sense of "this is wrong", its more that the behaviour is deliberate and currently undiscoverable. in any case the first two are small and i'd rather they went in with the PR than after it.
