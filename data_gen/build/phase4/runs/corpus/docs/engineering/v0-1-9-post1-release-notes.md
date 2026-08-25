---
title: "v0.1.9.post1 release notes"
author: dario
created_at: 2024-11-19T09:14:00+00:00
---

# v0.1.9.post1 Release Notes

Hotfix on top of v0.1.9. No API changes, no new features, safe to upgrade.

## What changed

- Fixed an edge case in the caching-and-resume path where cached results were not being matched correctly under certain prompt configurations
  - when this hit, the cache lookup would fall through and the pipeline would re-request from the provider unnecessarily
  - no incorrect results were returned, just redundant provider calls (and the cost/latency that comes with that)

## Who should upgrade

Anyone on v0.1.9. If you are seeing more provider calls than you expect, or higher costs than the cache hit rate would suggest, this is likely the fix.

If you are not on v0.1.9 this does not apply.

## What is not changing

- No interface or API changes
- No behaviour changes other than the cache matching fix
- Drop-in replacement for v0.1.9
