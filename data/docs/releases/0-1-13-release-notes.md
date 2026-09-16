---
title: "0.1.13 release notes"
author: konrad
created_at: 2025-01-07T14:30:14+00:00
---

# Millrow v0.1.13 Release Notes

141 changes across 7 releases, no breaking changes in this one.

---

## o1 model support

Provider integrations now handle o1-series models. If you are already using the provider config you have, this should just work, nothing to reconfigure.

- o1 and o1-mini both covered
- reasoning token handling is included (o1 uses those instead of normal completion tokens, the accounting is different)
- I'd double-check your token budget estimates if you're running evals that are cost-sensitive, the per-run numbers will look higher than you'd expect coming from gpt-4o

## Batch mode improvements

A few rough edges smoothed out. Nothing dramatic, mostly reliability and handling of edge cases that were showing up in longer runs.

TBD - need to pull the specific issues from the milestone before I publish this, want to be accurate about what actually changed vs what was planned

## curator-viewer: cache dir helper

curator-viewer now exposes a helper for locating the cache directory. Useful if you're scripting around the viewer or trying to clean up between runs without hunting for the path manually.

- returns the resolved path, not a relative one
- works on the platforms we actually test (linux, mac), not sure about windows (need to check with whoever handles the windows build)

## Prompter: `, no-cache` argument

You can now pass `, no-cache` to Prompter to disable caching entirely for a run. Handy when you're iterating on a prompt and want to be sure you're not hitting a stale result.

- does what it says, skips both read and write
- no config file change needed, argument only

---

No breaking changes. Upgrade from any 0.1.x should be straightforward.
