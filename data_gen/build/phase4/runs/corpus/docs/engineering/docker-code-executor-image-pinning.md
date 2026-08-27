---
title: "Docker code executor image pinning"
author: nikolai
created_at: 2025-04-16T10:24:00+00:00
---

# Docker code executor image pinning

Notes on the current state before we decide anything.

## What floats right now

- The code executor doesn't pin a Docker image version anywhere
- The cookbook examples are in the same position, they just reference whatever floats in
- Nothing enforces a tag on the default path, and nothing enforces one on the caller-supplied path either

## The backend_params shortcut

When a caller passes `backend_params={'image': ...}`, the create call takes a shorter path. The extra kwargs we assemble for our own tag are never added. Nobody designed this in, its just where the code landed.

The consequence is that any tag enforcement we add to the default path is silently bypassed if the caller supplies their own image. I'd say that's the more urgent problem, because it means a caller who knows about the param can get around whatever we do on the default side without any error or warning.

## Custom image request

There's a team asking to pass their own image. The reason is purely about what's pre-installed: they want scipy and their internal client lib already present rather than installing at runtime. They're not asking us to change anything about how the container runs. Workspace still comes in read-only from our side, they said thats fine because they write everything to stdout anyway.

This is the concrete use case that made the backend_params path matter. Before this request it was mostly theoretical.

## Failure preference

If we tighten any of this, the preference is for the first task to blow up at create time rather than proceed silently with the wrong image. Don't let it start and fail midway through, fail early.

## Open questions

- What tag value to pin to (need to see what the sandbox repo actually publishes, i dont have that)
- What to name the override key
- Where the default tag should live in config
- Whether the custom image path gets validated at all, or just trusted

[TODO] check what the sandbox repo publishes before any of the pinning decisions can go forward
