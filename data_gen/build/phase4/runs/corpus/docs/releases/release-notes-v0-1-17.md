---
title: "Release notes: v0.1.17"
author: dermot
created_at: 2025-01-28T09:14:00+00:00
---

# Release notes: Millrow v0.1.17

---

## Highlights

- Expanded provider support, several new integrations added via the provider-integrations track
- More robust resume behavior, particularly around interrupted runs and partial cache states
- Progress output and CLI polish pass
- JSON parser fix for curly-brace handling (was silently dropping content in some inputs)

---

## Provider integrations

- Added support for additional providers, TBD which exact ones are documented elsewhere (i need to check the merged PRs before listing them explicitly here, dont want to misattribute)
- Configuration surface for new providers follows the same pattern as existing ones
- Some edge cases in credential resolution fixed, these were showing up when a provider returned unexpected header shapes

## Caching and resume

The resume behavior was the main thing that needed attention in this release. Interrupted runs were not always picking up cleanly from the last good checkpoint, particularly when the cache directory had a partial write from a previous run. That is now handled more defensively.

- Cache invalidation logic tightened
- Resume detection now checks for partial state files explicitly rather than relying on directory presence alone
- Not entirely sure if this covers every edge case for very large runs, should be tested at scale before anyone relies on it heavily

## Curator viewer

- Various small fixes to the viewer interface
- Progress display improvements, output is less noisy on repeated updates

## JSON fix

Curly-brace handling in the JSON parser was producing silent data loss in certain inputs. Fixed. If you were running v0.1.16 or earlier against inputs with nested object literals, worth re-running.

## CI

- Several CI improvements merged, mostly around test reliability
- Nothing user-facing

---

## Numbers

207 changes merged across 12 releases to date (including this one).

---

## Known issues / open questions

- Resume at scale: not yet validated on runs over a certain size (need whoever is running the big integration tests to confirm)
- Provider list: i will update this page once I have gone through the full diff list
