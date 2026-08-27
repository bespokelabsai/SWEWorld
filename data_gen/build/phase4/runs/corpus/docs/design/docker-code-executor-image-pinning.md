---
title: "Docker code executor image pinning"
author: nikolai
created_at: 2025-04-16T09:14:00+00:00
---

# Docker code executor image pinning

## Problem

The Docker backend pulls an image at runtime with no pinned tag or digest. That means any silent upstream change to the image changes the execution environment, and two callers hitting the backend on different days can get different behaviour from code that is nominally identical. There is no versioning, no audit trail, nothing.

The override path is broken too. When a caller passes `backend_params={'image': ...}`, the create call takes a shorter code path than the default one, and the extra kwargs the default path assembles for the internal tag never reach it. Nobody designed that, it is just where things ended up after a few iterations.

## What needs to change

Two things, both required:

- **Pin the default image.** One canonical constant in the codebase, set to a deterministic tag or digest. Not inferred at runtime, not assembled from parts at call time. The value lives in one place and changing it is a deliberate act.
- **Fix the override path.** When a caller supplies their own image via `backend_params`, that image has to go through the same setup the default path does, including whatever image-specific prep currently only happens on the default branch. Right now it does not.

## Failure behaviour preference

If the image is bad or missing, the error should surface at `create` time, not at execution time. A `create`-time failure is loud and cheap to diagnose. A wrong environment that silently runs to completion is expensive to catch and hard to trace back. This is worth designing for explicitly, not leaving to whatever happens naturally.

## Known caller use case

One team (I dont know who owns the ticket, need to check) wants to supply an image with scipy and an internal client library pre-installed. They are not asking to change how the container runs. The workspace still mounts read-only from our side and they confirmed that is fine, they write everything to stdout.

This is a solid enough use case to design the override path against. If their image works end-to-end then the override is working.

## Open questions

- What is the actual pinned tag? Need to check what the sandbox repo publishes and on what cadence. I dont want to invent a value here.
- What should the key be called in `backend_params`? `image` is already used informally but it is not formally documented anywhere I can find. Gotta think through that one before we commit to it in the API surface.
- Where does the default constant live? A module-level constant in the backend file is the obvious answer but I want to know if there is already a config layer that should own it instead.

Resolution on all three belongs in the follow-up once the sandbox publish cadence is confirmed.
