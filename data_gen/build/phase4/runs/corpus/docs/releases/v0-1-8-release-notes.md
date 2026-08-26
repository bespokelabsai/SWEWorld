---
title: "v0.1.8 release notes"
author: dario
created_at: 2024-11-15T09:21:00+00:00
---

# Millrow v0.1.8 Release Notes

69 changes merged. First tagged release of the request pipeline milestone.

## Batch mode fixes

- File size constraint handling was broken in batch mode, fixed
- Progress bar counting was off (undercounting in at least one case), also fixed
- both of these were quiet bugs so if you were using batch mode and things looked slightly wrong, this is probably why

## New examples

- **vLLM / OpenAIOnlineParallelProcessor** (PR 78) - example showing how to use the online parallel processor with a vLLM backend
- **Text message summarization** (PR 106)
- **teacher.py** (PR 130) - honestly not sure how much of the setup context lives outside this file, so read it top to bottom before running it

## Prompter changes

PR 90 adds a cache-disable argument to Prompter. If you were working around the cache by other means you can probably simplify that now.

## Docs and code quality

- PR 39 covers miscellaneous docstring fixes and general code-quality cleanup, nothing functional
- README links corrected, a few had rotted
- examples directory cleaned up generally

## Open questions

- [ ] changelog for the full 69 PRs is not linked anywhere yet, need to check if thats expected or if someone needs to add it
- [ ] not sure which PRs map to the request pipeline milestone marker specifically vs just being along for the ride in this tag, TBD
