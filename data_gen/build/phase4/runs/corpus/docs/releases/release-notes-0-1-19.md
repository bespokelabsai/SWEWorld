---
title: "Release notes: 0.1.19"
author: gideon
created_at: 2025-02-17T09:28:00+00:00
---

# Release notes: Millrow 0.1.19

16th release, 258 changes merged.

## Progress and CLI

- Progress bar revamp: run observability is cleaner, and the cache hit counter is now visible during a run (was buried before, basically unusable)
- Several display fixes to per-row status during generation
  - some edge cases where status would render incorrectly or flicker on certain terminal widths

## Online request handling

Around 12 fixes across the online request layer, mostly edge cases that werent caught earlier:

- retry logic under partial failures, which was silently doing the wrong thing in some provider configurations
- cost tracking improvements across providers, per-request and per-run totals are now more reliable (previously they could drift, especially on retried requests)

## Internal cleanup

Some cleanup across the request layer, nothing user-facing.

## Upgrade

No breaking changes.

```
pip install --upgrade bespokelabs-curator
```

## Known issues

None at this time.
