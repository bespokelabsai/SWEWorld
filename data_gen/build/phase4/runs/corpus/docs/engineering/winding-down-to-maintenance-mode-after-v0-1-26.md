---
title: "Winding Down to Maintenance Mode After v0.1.26"
author: konrad
created_at: 2025-07-10T10:10:00+00:00
---

# Winding Down to Maintenance Mode After v0.1.26

After v0.1.26 ships, Millrow enters dormancy. Maintenance mode means critical bug fixes and dependency updates only. No new features will be merged.

## In-Flight PRs

These need to be resolved before the freeze. Current state as of this morning:

- PR 696 (version tag in lib) - merged and confirmed correct
- PR 653 (finetuning client, Nikolai Berresford) - state is unclear, awaiting clarification from Nikolai
- PR 675 (default app id for curator llm, Nolan Whitfield) - status pending, need update from Nolan
- PR 690 (multimodal Gemini batch fix, Emil Brandvold) - update expected this afternoon
- PR 693 (OpenAI streaming, Emil Brandvold) - also Emil, also expected this afternoon

So 696 is done. Everything else is still open. Emil's two PRs should be clearer by end of day. The two that concern me most are 653 and 675 because I dont have a timeline on either of them.

## My Reviews

- finetuning - reviewed this morning, ready for maintenance mode
- code-execution - pending
- examples-cookbooks - pending

I will try to get code-execution and examples-cookbooks done today or tomorrow, before we lock.

## Open Questions

- What is the state of PR 653? Nikolai needs to respond.
- PR 675, Nolan - is this mergeable or is it being held for a reason?
- Do we have a hard cutoff date for the freeze, or are we waiting until the last in-flight PR lands? I dont have a confirmed date for this.
