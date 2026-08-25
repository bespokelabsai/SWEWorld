---
title: "Weekly sync notes: week of Jan 6 \u2014 v0.1.14 shipped"
author: dermot
created_at: 2025-01-08T09:14:00+00:00
---

# Weekly sync notes: week of Jan 6, v0.1.14 shipped

Jan 8 2025. Notes from today's call. Dermot writing.

---

## What shipped

v0.1.14 is out as of this week. 156 changes merged total across 8 releases now. No hotfixes required after release, which is a good sign given how much landed in this one.

## What's in flight

- batch-mode (Emil), progress made this week, not done
- bulk-llm-inference (me), in flight, more on this below
- multimodal-prompts (Emil), in flight
- progress-and-cli (Gideon), in flight
- provider-integrations, caching-and-resume, curator-viewer, online-request-processing (Dario), all in flight, Dario carrying a lot right now
- local-offline-inference (Emil), in flight; local vLLM is under evaluation for whether it goes into next release, not decided yet

## Open PRs to watch

| PR | Title | Owner |
|----|-------|-------|
| 106 | Add an example for summarizing text messages between two people | Konrad Feltrin |
| 133 | adding an env example file | Otto Brennan |
| 161 | [Curator Usage Example] Prometheus LLM Judge evaluation | Gideon Halloway |
| 163 | [curator-viewer] use getCacheDir helper function, add additional param for cache dir | Gideon Halloway |
| 171 | enhance GenericRequest test coverage | Otto Brennan |
| 173 | Refactor Prompter to support class-based approach | Millrow Refactor Bot |

PR 173 I'm a little unsure about, the author is listed as "Millrow Refactor Bot" which I assume is an automated PR from the refactor tooling, but someone should confirm who is actually owning review on that one.

## Open issues carrying into next week

These did not close this week and are rolling forward:

- issue 48: README documentation on batch
- issue 52: Support multiple samples per request
- issue 88: Add a way to disable caching for curator
- issue 92: [UI] Detail View, better JSON/markdown file extension views
- issue 93: [UI] Display status of the run
- issue 94: metadata.db updates run status (enum), run progress (percentage)
- issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
- issue 105: Distribution graph is skewed for data viewer

Issues 92, 93, 94 are all UI-side and probably best handled together. Not sure if Dario owns all three or if Gideon picks up some of that given his curator-viewer work.

## What's next

Two blocking questions before we can set a v0.1.15 timeline:

1. **Ruff migration**, needs a team decision. Either we finalize it or we roll back. I dont think we can leave it half-done going into next release.
2. **local vLLM stability**, Emil's local-offline-inference work needs a soak period assessment. If we're not confident in it, it waits for v0.1.16 or later.

Once those two are resolved we can set the v0.1.15 timeline. No point in putting a date on it before then.
