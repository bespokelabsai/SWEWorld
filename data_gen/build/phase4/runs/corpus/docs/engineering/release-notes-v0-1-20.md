---
title: "Release notes: v0.1.20"
author: dario
created_at: 2025-02-28T09:42:00+00:00
---

# Release notes: v0.1.20

Four changes in this release. Brief notes on each below.

---

## Claude 3.7 support

Provider integrations now include Claude 3.7. Specify it in your generation params the same way you would any other model, no other changes needed on your side.

## Generation params refactor

The gen params interface has been tidied up for consistency across request types. If you were passing params directly, check your field names still match, the refactor may have renamed things you rely on. Nothing dramatic but worth a quick scan before you ship anything.

## Install command fix

Fixed a bug that caused setup to fail in certain environments during fresh installs. If you hit the broken behavior before this release, try again, it should go cleanly now. If it still fails on your env, open an issue with the error output.

## Hosted-curator session IDs

Session IDs are now included in hosted-curator responses. No action needed, they are just there if you want them.

---

## Code execution backend note

The container the library ships against does not update itself, and nothing in the codebase will tell you when the image is stale. Before you touch the checklist line for that backend, go check what the image status notes actually say. Otherwise you're guessing.
