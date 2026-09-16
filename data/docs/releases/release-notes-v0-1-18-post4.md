---
title: "Release notes: v0.1.18.post4"
author: dermot
created_at: 2025-02-07T08:45:00+00:00
---

# Release notes: v0.1.18.post4

Hotfix release, shipped 2025-02-07. This follows the provider-integrations incident on Feb 6.

## What changed

- **GC leak in bulk inference** - memory was not being released correctly after large batch inference calls, causing gradual heap growth over long-running processes. Fixed the cleanup path so GC can collect properly after each batch.
- **Empty response handling** - certain providers were returning empty response bodies in edge cases and the client was throwing instead of surfacing a clean error. Now handled explicitly.
- **inference.net provider support** - inference.net was not wired up correctly as a provider option. Should be functional now (only lightly tested against their sandbox, not a full integration run).

## What is not in this release

No functional changes beyond the three fixes above. No dependency bumps.

## Upgrade

Drop-in replacement for v0.1.18 and v0.1.18.post1 through post3. No config changes needed.

---

If you hit the GC issue in production before upgrading: restarting the process clears it. The leak is slow enough that a nightly restart is a reasonable workaround if you cant upgrade immediately.
