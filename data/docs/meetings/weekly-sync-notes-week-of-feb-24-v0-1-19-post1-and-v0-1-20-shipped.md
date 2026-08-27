---
title: "Weekly sync notes: week of Feb 24 \u2014 v0.1.19.post1 and v0.1.20 shipped"
author: gideon
created_at: 2025-02-26T09:35:00+00:00
---

# Weekly sync notes: week of Feb 24, v0.1.19.post1 and v0.1.20 shipped

## Shipped

### v0.1.19.post1

- curator tag fix (code-execution)
- executor hardening (code-execution)
- sandbox image runs tasks as uid 1000; caller-supplied image runs as uid 0
    - this is expected behavior, documented in release notes
- no breaking API changes, upgrade is `pip install --upgrade`

### v0.1.20

- see release notes for full list, not recapping everything here

## In progress

- PR 546: cost estimation revamp, online processors, first of several
    - feedback still being gathered, not merged yet
- PR 547: README update announcing code execution launch (examples-cookbooks)
    - aiming to merge today
- Nikolai posted release notes for v0.1.19.post1 to the wiki

## Open items

- [ ] PR 546 feedback, waiting on a few more reviewers
- [ ] confirm executor hardening ship status for v0.1.19.post1 (i think this is settled but want it on record somewhere)
