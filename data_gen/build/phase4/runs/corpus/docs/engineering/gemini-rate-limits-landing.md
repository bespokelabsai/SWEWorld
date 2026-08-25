---
title: "Gemini Rate Limits Landing"
author: emil
created_at: 2025-03-06T09:35:00+00:00
---

# Gemini Rate Limits Landing

PR 578 is merged and this workstream is closed. Three pieces landed as part of this:

- **PR 578** - core rate limit handling for Gemini. Retries, backoff, the works. This is the main thing.
- **failed-count fix** - caught during review, fixed before merge. The counter was incrementing on rate limit retries, which meant a request that eventually succeeded could still show up as failed in reporting. Small fix but would have been annoying to debug later.
- **batch example** - added as the reference implementation for anyone integrating with Gemini going forward. If someone is wiring up a new Gemini integration, this is where they should start.

The batch example in particular is worth pointing people at proactively. We've had a couple of situations where integrations got the retry logic subtly wrong, and having a concrete working example they can just follow should reduce that.

Open question I don't have an answer to: is the batch example linked anywhere in the onboarding docs or the engineering wiki? If not, let's circle back on that before it gets buried.
