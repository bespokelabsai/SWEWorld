---
title: Storage Layer
author: bob
created_at: 2026-01-17T14:03:00Z
---

One Postgres per service, not one shared database.

## Why

Blast radius. A migration that locks a table should not be able to take down
chat and docs at the same time.
