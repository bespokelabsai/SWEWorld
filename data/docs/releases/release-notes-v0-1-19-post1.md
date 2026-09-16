---
title: "Release notes: v0.1.19.post1"
author: nikolai
created_at: 2025-02-26T08:50:00+00:00
---

# Release notes: v0.1.19.post1 (Stratos Crunch)

Two fixes shipped as a post-release on top of v0.1.19. No API changes, no migration steps beyond the upgrade itself.

---

## Upgrade

```
pip install --upgrade bespokelabs-curator==0.1.19.post1
```

---

## What changed

### Curator tag resolution fix

During a hosted curator viewer resume flow, curator version tags were not being resolved correctly. The effect was that the wrong tag could be picked up on resume, which could cause the resumed run to behave differently from the original.

This is now fixed. Tag resolution happens against the correct ref at resume time.

### Executor hardening (code-execution Docker backend)

Two things here, and i want to make sure the second one is clearly documented so nobody files a bug about it.

- The shipped sandbox image now runs tasks as uid 1000 (non-root). This is intentional, a deliberate tightening of the Docker backend.
- If you supply your own image, the executor runs as uid 0. That is also expected. We dont override the user in caller-supplied images because we cant make assumptions about what the image needs.

Both changes are in the code-execution service only.

---

## What has not changed

- Public API: no changes
- Wire format: no changes
- Hosted viewer: no schema changes

---

## Known issues / open questions

- I dont have a full list of which resume-flow edge cases were tested for the tag fix. If you hit a resume failure that looks tag-related, please open an issue with the curator version string from the original run.
