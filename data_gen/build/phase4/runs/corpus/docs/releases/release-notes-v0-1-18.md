---
title: "Release notes: v0.1.18"
author: emil
created_at: 2025-02-06T09:14:00+00:00
---

# Release notes: Millrow v0.1.18 (Stratos Crunch)

## What shipped

- **Multimodal image support**, multimodal-prompts now handles image inputs end-to-end
    - covers prompt construction, provider passthrough, and output handling for image-bearing rows
    - if you were working around this with manual preprocessing, you should be able to drop that now
- **Batch stability fixes**, batch-mode got a round of stability work
    - reduced failure rates on large jobs
    - improved error surface when a provider returns garbage mid-run (previously these could stall silently or produce confusing output)
- **Rich progress bar / error log overlap fix** (PR 457), the Rich-rendered progress bar was stomping over error log lines; errors now display cleanly above the bar
- **Generation params per row** (PR 443), `generation_params` can now be specified per row, not just globally
- **HuggingFace card template** (PR 456), `curator` tag added to hf_card_template
- **pyproject.toml / litellm version bump** (PR 449), litellm pinned to a known-good version; dependency alignment only, no behavior changes expected

## What did NOT ship

The prompt formatter fix (PR 461) was merged but reverted before the tag was cut. It is not in v0.1.18. Root cause is still being investigated. A corrected version will land in a future patch.

## Known issues / next patch targets

- Prompt formatter root cause resolution is the top priority for the next patch
- PR 362 (Fix_json curly braces) and PR 430 (Reasoning with OpenRouter examples) are under review and targeting the next release
