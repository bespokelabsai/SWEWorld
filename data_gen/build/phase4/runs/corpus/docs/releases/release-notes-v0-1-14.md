---
title: "Release notes: v0.1.14"
author: emil
created_at: 2025-01-07T09:14:00+00:00
---

# Release Notes: v0.1.14

## What's in this release

Five things merged. None of them are breaking changes.

---

### Docstring pass

Went through the codebase and added/cleaned up docstrings across the public-facing surface. Coverage was pretty uneven before this, especially on some of the older helpers that never got documented when they were first written.

### Cache directory config (`getCacheDir`)

New `getCacheDir` helper that centralizes how the cache directory is resolved. Previously several places were doing their own path logic, which made it annoying to configure a non-default cache location. Now there's one place to change it.

- reads from config first
- falls back to the default path if nothing is set
- [TODO] not sure if we documented what the config key is anywhere visible, need to check

### Special tokens fix

Bug fix. Special tokens were not being handled correctly in at least one code path, details are in the PR. Worth verifying if you were working around this, you may be able to remove that workaround now.

### Test file movement

Moved some test files around, no logic changed. Just reorganizing so the layout is easier to follow. Should be invisible if you're running the test suite normally.

### GenericRequest test coverage

Added tests for GenericRequest. This was basically untested before. Coverage is better now, though i dont think we hit every edge case yet.

---

## Upgrading

No migration steps needed. Drop in the new version, nothing should break.
